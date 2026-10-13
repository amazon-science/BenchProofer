# Requirements: Pipeline length support

## Introduction

The scikit-learn `Pipeline` class (in `sklearn.pipeline`) is a sequential
container that holds an ordered list of named estimator steps in its `steps`
attribute. `Pipeline` already supports integer/slice indexing (`pipe[i]`,
`pipe[:k]`) and name-based lookup (`pipe['name']`) via its `__getitem__`
method, but it does not report how many steps it contains: calling the built-in
`len()` on a pipeline raises `TypeError`. This also makes the natural idiom
`pipe[:len(pipe)]` fail.

The goal is to make a `Pipeline` report its number of steps through the
standard Python length protocol, so that `len(pipe)` returns the step count and
length-based slicing works, while all existing indexing, slicing, and
name-lookup behavior is preserved.

## Requirement 1: Pipeline reports its number of steps

**User story:** As a user of scikit-learn pipelines, I want `len(pipe)` to
return the number of steps in the pipeline, so that I can query the pipeline's
size and use length-based indexing idioms.

**Acceptance criteria**

1. WHEN the built-in `len()` is applied to a `Pipeline` instance, THEN the
   `Pipeline` SHALL return an integer equal to the number of entries in its
   ordered `steps` list.
2. WHEN `len()` is applied to a `Pipeline` constructed with N step entries,
   THEN the returned value SHALL equal N, counting every entry in `steps`
   regardless of the estimator each entry holds (including entries whose
   estimator is `None` or the string `'passthrough'`).
3. The system SHALL report the count as the exact length of the `steps` list
   as provided at construction, without adding, dropping, or deduplicating any
   entry.
4. The system SHALL make `len(pipe)` return the same integer as
   `len(pipe.steps)` for the same pipeline.
5. WHEN `len()` is applied to a `Pipeline`, THEN the operation SHALL succeed
   without raising `TypeError`.

## Requirement 2: Length-based slicing works

**User story:** As a user, I want `pipe[:len(pipe)]` to work, so that I can
slice a pipeline using its own length as a bound.

**Acceptance criteria**

1. WHEN a `Pipeline` is sliced using its own length as the stop bound (for
   example `pipe[:len(pipe)]`), THEN the operation SHALL succeed and return a
   `Pipeline` instance containing all of the original steps.
2. WHEN a `Pipeline` is sliced with any valid slice whose bounds are derived
   from `len(pipe)`, THEN the returned object SHALL be a `Pipeline` whose
   `steps` equal the corresponding slice of the original `steps` list.

## Requirement 3: Existing indexing and lookup behavior is preserved

**User story:** As a maintainer, I want the new length support to leave all
existing pipeline access behavior unchanged, so that no regressions are
introduced.

**Acceptance criteria**

1. WHEN a `Pipeline` is indexed with an integer position, THEN the `Pipeline`
   SHALL return the estimator object stored at that position in `steps`,
   supporting negative indices in the usual Python manner.
2. WHEN a `Pipeline` is indexed with a step name string, THEN the `Pipeline`
   SHALL return the estimator registered under that name.
3. WHEN a `Pipeline` is sliced with a slice object, THEN the `Pipeline` SHALL
   return a new `Pipeline` instance whose `steps` are the corresponding slice
   of the original `steps`.
4. IF a `Pipeline` is sliced with a step other than 1 (for example a reversed
   slice), THEN the `Pipeline` SHALL raise `ValueError`.
5. IF a `Pipeline` is indexed with an integer position outside the range of
   `steps`, THEN the `Pipeline` SHALL raise `IndexError`.
6. IF a `Pipeline` is indexed with a name that is not present among the steps,
   THEN the `Pipeline` SHALL raise `KeyError`.
7. The system SHALL keep the `named_steps`, construction, and step-validation
   behavior of `Pipeline` unchanged, including the number of accessible named
   steps for any given pipeline.
