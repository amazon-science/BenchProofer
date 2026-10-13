# Requirements: Correctly strip accents from already-decomposed Unicode strings

## Introduction

`strip_accents_unicode(s)` in `sklearn/feature_extraction/text.py` is the
Unicode accent-stripping routine used by the text feature extractors
(`CountVectorizer`, `TfidfVectorizer`, `HashingVectorizer` and their shared
preprocessing machinery) when the `strip_accents="unicode"` option is selected.
It is a sibling of `strip_accents_ascii` and both are exposed as module-level
helpers.

The function is meant to remove accent/diacritic marks from text while leaving
the underlying base characters intact. It does this by taking the canonical
(NFKD) decomposition of the string and discarding the standalone combining
marks.

The defect: the function decides whether to do any work by comparing the string
to its own NFKD decomposition and returning the string unchanged when they are
equal. A string that is *already supplied in decomposed form* (a base letter
followed by separate combining-mark code points) equals its own NFKD form, so
the function returns it verbatim and the accent is never removed. Two visually
identical inputs — one pre-composed (e.g. a single "n with tilde" code point)
and one decomposed (an "n" followed by a "combining tilde" code point) — then
produce different results, which is wrong.

The goal is to make the decision to strip depend on whether the text actually
contains any non-ASCII code point, not on whether it happens to already be in
decomposed form, while preserving all existing correct behavior and the behavior
of the neighbouring helpers and vectorizers.

## Requirement 1: Strip accents from already-decomposed input

**User story:** As a user vectorizing text with `strip_accents="unicode"`, I
want accents removed regardless of whether the input glyphs are pre-composed or
already decomposed, so that visually identical strings map to the same
accent-free tokens.

**Acceptance criteria**

1. WHEN `strip_accents_unicode` is called with a string that contains a base
   character immediately followed by one or more standalone combining marks,
   THEN the function SHALL return the base character(s) with every combining
   mark removed.
2. WHEN `strip_accents_unicode` is given the pre-composed form of a glyph and,
   separately, the equivalent decomposed form (base character plus combining
   mark) of the same glyph, THEN the function SHALL return the same result for
   both inputs.
3. WHEN `strip_accents_unicode` is called with a string consisting solely of
   combining-mark code points and no base characters, THEN the function SHALL
   return the empty string.
4. WHEN `strip_accents_unicode` is called with a single base character carrying
   more than one combining mark, THEN the function SHALL return only that base
   character with all of its combining marks removed.

## Requirement 2: Preserve accent-stripping for pre-composed accented input

**User story:** As a user, I want existing accented text to continue to be
normalized to its unaccented base letters, so that the fix introduces no
regression for the already-working case.

**Acceptance criteria**

1. WHEN `strip_accents_unicode` is called with a string containing pre-composed
   accented characters (single code points that decompose into a base letter
   plus a combining mark), THEN the function SHALL return the corresponding base
   letters with the accents removed.
2. The function SHALL, for any input that contains at least one non-ASCII code
   point, produce the canonical (NFKD) decomposition of the input with every
   combining mark discarded and the remaining characters preserved in their
   original order.

## Requirement 3: Leave pure-ASCII input unchanged

**User story:** As a user processing plain ASCII text, I want it returned
untouched and cheaply, so that no unnecessary transformation is applied to
strings that cannot contain accents.

**Acceptance criteria**

1. IF the input string consists entirely of ASCII code points (every code point
   below 128), THEN `strip_accents_unicode` SHALL return the input string
   unchanged.
2. WHEN the input contains no non-ASCII code point, THEN the function SHALL NOT
   remove or alter any character of the input, including any ASCII characters
   that are not letters.

## Requirement 4: Preserve neighbouring and dependent behavior

**User story:** As a maintainer, I want the change confined to the Unicode
accent-stripping decision, so that related helpers and the text vectorizers keep
behaving as before.

**Acceptance criteria**

1. The system SHALL keep `strip_accents_ascii` behaving as before, transliterating
   accented Unicode symbols to their ASCII counterparts (or dropping them) and
   returning an ASCII string.
2. The system SHALL keep the analyzers and preprocessors of `CountVectorizer`,
   `TfidfVectorizer`, and `HashingVectorizer` — including tokenization, n-gram
   generation, stop-word handling, vocabulary handling, and term weighting —
   unchanged by this fix.
3. WHEN a vectorizer is configured with `strip_accents="unicode"`, THEN accent
   stripping applied during preprocessing SHALL follow the behavior specified in
   Requirements 1–3.
4. The system SHALL continue to accept any Python string as input to
   `strip_accents_unicode` and SHALL always return a string.
