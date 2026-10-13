# Requirements — Stratified k-fold shuffling honors the random seed

## Introduction

`StratifiedKFold` (in `sklearn/model_selection/_split.py`) produces stratified
cross-validation splits: for each target class it lays that class's samples out
and deals them into folds so every fold preserves the class balance. When the
`shuffle` option is enabled, the intent — as documented for the `shuffle`
parameter — is that each class's own samples are shuffled before being dealt
into folds, with the arrangement controlled by `random_state`.

In the affected version the shuffling done inside
`StratifiedKFold._make_test_folds` does not actually vary with the seed: every
class ends up arranged the same way and two different `random_state` values
yield the same test folds (only the order in which folds are emitted differs,
which does not change cross-validation results). The goal of this change is to
make `shuffle=True` genuinely seed-dependent — each class shuffled from a single
seeded source of randomness that is threaded across the classes — while leaving
the unshuffled behavior, the class-balance guarantees, and the reproducibility
of a fixed seed completely unchanged.

The relevant code is `StratifiedKFold._make_test_folds` and its use of the
`random_state` attribute, together with the shared helper `check_random_state`
(in `sklearn/utils/validation.py`) and the per-class fold splitter (`KFold`)
that consumes the resulting generator.

## Requirement 1: Seed-dependent shuffling of stratified folds

**User story:** As a user running stratified cross-validation with shuffling
enabled, I want the produced folds to genuinely depend on `random_state`, so
that different seeds give me different partitions of my data and shuffling is
actually meaningful.

**Acceptance criteria**
1. WHEN `StratifiedKFold` is constructed with `shuffle=True` and `split` is
   called on the same data with two different integer `random_state` values,
   THEN the splitter SHALL, in general, produce different collections of test
   folds for the two seeds (the set of test-index groups produced under one seed
   SHALL NOT be forced to equal that produced under the other).
2. WHEN `shuffle=True`, THEN `StratifiedKFold` SHALL derive the randomness used
   to shuffle the classes from a single random generator obtained from
   `random_state`, rather than re-deriving an identical generator independently
   for each class.
3. WHILE `shuffle=True` and more than one class is present, the splitter SHALL
   consume that single generator once per class in class order, advancing its
   state from each class to the next, so that distinct classes are generally
   arranged differently rather than all classes receiving an identical
   arrangement.
4. The system SHALL confine this behavioral change to how the per-class
   shuffling generator is obtained inside `StratifiedKFold._make_test_folds`;
   it SHALL NOT change the sample-to-fold assignment logic used once the
   per-class orders are fixed.

## Requirement 2: Interpretation of the `random_state` argument

**User story:** As a user, I want `random_state` to be interpreted consistently
however I pass it, so that seeding behaves predictably.

**Acceptance criteria**
1. WHEN `random_state` is an integer, THEN `StratifiedKFold` SHALL treat it as a
   seed for a freshly created pseudo-random generator used for shuffling.
2. WHEN `random_state` is `None`, THEN `StratifiedKFold` SHALL use the shared
   global pseudo-random generator.
3. WHEN `random_state` is already a pseudo-random generator instance, THEN
   `StratifiedKFold` SHALL use that instance directly for shuffling.
4. IF `random_state` is none of the above accepted forms, THEN the system SHALL
   raise a `ValueError`.

## Requirement 3: Reproducibility for a fixed seed

**User story:** As a user, I want a fixed seed to reproduce the same splits
exactly, so that my experiments remain deterministic and comparable.

**Acceptance criteria**
1. WHEN `StratifiedKFold` is constructed with `shuffle=True` and a fixed integer
   `random_state`, THEN calling `split` on the same data SHALL yield the same
   train/test index partitions on every invocation.
2. WHEN two `StratifiedKFold` instances are built with the same `shuffle=True`
   and the same integer `random_state`, THEN they SHALL produce identical splits
   for identical input data.

## Requirement 4: Unshuffled behavior is preserved

**User story:** As a user relying on the default behavior, I want disabling
shuffle to keep the previous, seed-independent ordering, so that existing code
is unaffected.

**Acceptance criteria**
1. WHEN `shuffle=False`, THEN `StratifiedKFold` SHALL keep each class's samples
   in their natural (ascending index) order before dealing them into folds.
2. WHILE `shuffle=False`, the value of `random_state` SHALL NOT affect the
   produced splits.

## Requirement 5: Stratification and coverage guarantees are kept

**User story:** As a user, I want the class-balance and coverage properties of
stratified splitting to remain intact regardless of shuffling, so that folds
stay valid for evaluation.

**Acceptance criteria**
1. The system SHALL keep the number of splits equal to the requested
   `n_splits`.
2. The system SHALL keep each fold's class proportions approximately equal to
   the class proportions of the whole dataset, for both `shuffle=True` and
   `shuffle=False`.
3. WHEN `split` is called, THEN across all folds the test indices SHALL together
   cover every sample exactly once, and each sample's train set SHALL be the
   complement of its test fold.
4. IF `n_splits` exceeds the number of members in every class, THEN the system
   SHALL raise a `ValueError`; and IF the least populated class has fewer
   members than `n_splits`, THEN the system SHALL emit a warning while still
   producing splits.
5. The system SHALL continue to accept only the supported target types for
   stratification and SHALL raise a `ValueError` for unsupported target types.
