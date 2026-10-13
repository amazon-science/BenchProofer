# Requirements: CountVectorizer.get_feature_names with a provided vocabulary

## Introduction

`CountVectorizer` (in `sklearn.feature_extraction.text`) can be constructed with
an explicit `vocabulary` parameter — an ordered iterable of terms (or a mapping
of term to index) — instead of learning its vocabulary from a corpus. When a
vocabulary is supplied at construction time, the vectorizer can already map
terms to feature indices without any prior `fit`; indeed `transform` works
without fitting because it establishes the internal vocabulary on demand.

However, `get_feature_names` did not do this: on a vectorizer that was
constructed with a `vocabulary` but never fitted, it raised a
"not fitted" error instead of returning the feature names implied by that
vocabulary. This is inconsistent with `transform`, which succeeds on the same
object.

This document specifies the corrected behavior of
`CountVectorizer.get_feature_names`, the vocabulary-establishment step it must
perform, and the pre-existing behaviors that must be preserved. The relevant
code is the `get_feature_names` method and the internal vocabulary handling
(`_validate_vocabulary`, `_check_vocabulary`, and the `vocabulary_` and
`fixed_vocabulary_` attributes) of the vectorizers in
`sklearn/feature_extraction/text.py`.

## Requirement 1: Return feature names for a provided-but-unfitted vocabulary

**User story:** As a user who constructs a `CountVectorizer` with an explicit
`vocabulary`, I want `get_feature_names` to return the feature names without
first fitting on a corpus, so that querying feature names is as convenient as
calling `transform`.

**Acceptance criteria**

1. WHEN `get_feature_names` is called on a vectorizer that was constructed with
   a non-empty `vocabulary` and has not been fitted (its learned-vocabulary
   attribute `vocabulary_` is not yet present), THEN the method SHALL establish
   the internal vocabulary from the provided `vocabulary` and return the list of
   feature names, rather than raising an error.
2. WHEN the provided `vocabulary` is an ordered list of terms and
   `get_feature_names` is called before fitting, THEN the method SHALL return
   the terms in feature-index order, i.e. in the order the terms occupy in the
   provided list, with each term appearing at the position equal to its
   0-based index.
3. WHEN `get_feature_names` returns for a provided vocabulary, THEN for every
   returned name the vectorizer's term-to-index mapping (`vocabulary_`) SHALL
   map that name to its position in the returned list.
4. IF the same vectorizer is later fitted or transformed, THEN
   `get_feature_names` SHALL continue to return names consistent with the
   established `vocabulary_` mapping.

## Requirement 2: Establish provided-vocabulary state on first access

**User story:** As a developer relying on the vectorizer's public attributes, I
want accessing feature names on a provided-vocabulary vectorizer to leave the
object in the same fitted state that `transform` would, so that state is
consistent regardless of which accessor triggered it.

**Acceptance criteria**

1. WHEN `get_feature_names` establishes the vocabulary from a provided
   `vocabulary` parameter, THEN the vectorizer's `fixed_vocabulary_` attribute
   SHALL be True.
2. WHEN the vocabulary is established from a provided `vocabulary`, THEN the
   validation applied SHALL be the same as that used by `transform`/`fit` for a
   provided vocabulary: an ordered iterable of terms is turned into a
   term-to-index mapping following the terms' positions.
3. IF the provided `vocabulary` contains a term more than once, THEN
   `get_feature_names` SHALL raise a `ValueError` reporting a duplicate term.
4. IF the provided `vocabulary` is a mapping whose indices are repeated or do
   not cover every position from 0 up to its size minus one, THEN establishing
   the vocabulary SHALL raise a `ValueError`.
5. IF the provided `vocabulary` is empty, THEN establishing the vocabulary
   SHALL raise a `ValueError` indicating an empty vocabulary.

## Requirement 3: Preserve the not-fitted behavior when no vocabulary is provided

**User story:** As a user who neither supplies a vocabulary nor fits the
vectorizer, I want a clear error from `get_feature_names`, so that misuse is
still reported rather than silently returning empty results.

**Acceptance criteria**

1. WHEN `get_feature_names` is called on a vectorizer that was constructed
   without a `vocabulary` and has not been fitted, THEN the method SHALL raise a
   `ValueError` (the not-fitted error), as before.
2. WHILE a vectorizer constructed without a `vocabulary` has not been fitted,
   its `fixed_vocabulary_` attribute — once available — SHALL be False.
3. The system SHALL NOT establish or mutate a learned vocabulary when no
   `vocabulary` parameter was provided and the vectorizer has not been fitted.

## Requirement 4: Preserve feature-name behavior after fitting

**User story:** As a user who fits the vectorizer on a corpus, I want
`get_feature_names` to keep returning the learned feature names in index order,
so that existing workflows are unaffected by this change.

**Acceptance criteria**

1. WHEN a vectorizer is fitted on a corpus and `get_feature_names` is called,
   THEN the method SHALL return the learned terms in ascending feature-index
   order.
2. WHEN a vectorizer has been fitted, THEN the number of names returned by
   `get_feature_names` SHALL equal the number of features (the size of
   `vocabulary_`).
3. WHEN a vectorizer has been fitted, THEN for each name at position `idx` in
   the returned list, the term-to-index mapping SHALL map that name to `idx`.
4. The system SHALL keep the existing behavior of `transform`, which establishes
   the vocabulary from a provided `vocabulary` parameter on demand and succeeds
   without a prior fit.
