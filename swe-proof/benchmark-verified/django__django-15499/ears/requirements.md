# Requirements: Optimize a model-creation step followed by a manager reconfiguration

## Introduction

Django's migration optimizer (`django/db/migrations/optimizer.py`) repeatedly
inspects each operation together with the operation that immediately follows it
and, where the two describe a single net effect, fuses them into one operation.
The fusing decision for a model-creation step lives in
`CreateModel.reduce(self, operation, app_label)` in
`django/db/migrations/operations/models.py`, which contains a chain of cases:
one per kind of following operation it can absorb (a deletion, a rename, a
change of Meta options, a change of the `unique_together` / `index_together`
family, a change of `order_with_respect_to`, and the field-level operations).

A `CreateModel` operation records, for one model, five components: its name, its
fields, its options, its bases, and its managers. The optimizer already collapses
a `CreateModel` immediately followed by an `AlterModelOptions` for the *same*
model into a single `CreateModel` that carries the altered options. As the issue
notes, the analogous fusion is missing for `AlterModelManagers`: a
`CreateModel` immediately followed by an `AlterModelManagers` for the same model
can likewise become a single `CreateModel` that already carries the reconfigured
managers.

The goal is to add that missing reduction while leaving every existing reduction
of `CreateModel.reduce` unchanged. The affected module is
`django/db/migrations/operations/models.py`; the behavior is observed through
the result the optimizer produces for a sequence of migration operations.

## Requirement 1: Fuse a model creation with a following manager reconfiguration

**User story:** As a developer running migration optimization, I want a model
creation immediately followed by a reconfiguration of that model's managers to
collapse into a single model-creation step, so that the resulting migration is
minimal and carries the intended managers.

**Acceptance criteria**

1. WHEN a `CreateModel` operation is reduced against a following
   `AlterModelManagers` operation that targets the same model, THEN the
   optimizer SHALL replace the pair with exactly one `CreateModel` operation
   (a single-element result).
2. WHEN that fusion occurs, THEN the resulting `CreateModel` SHALL carry the
   managers taken from the `AlterModelManagers` operation, fully replacing the
   managers the original `CreateModel` had.
3. WHEN that fusion occurs, THEN the resulting `CreateModel` SHALL preserve the
   original `CreateModel`'s name, fields, options, and bases unchanged.
4. WHEN a model creation with no managers is followed by a manager
   reconfiguration for the same model, THEN the resulting single `CreateModel`
   SHALL carry exactly the reconfigured managers (including when several
   managers are supplied), in the order given by the reconfiguration.
5. WHEN the two fused operations are re-run through the optimizer, THEN the
   overall sequence of operations SHALL be reduced (the optimizer SHALL report
   that a reduction took place for this pair rather than leaving both
   operations in place).

## Requirement 2: Fuse only when the two operations target the same model

**User story:** As a developer, I want the manager-reconfiguration fusion to
apply only to the model that was just created, so that unrelated operations are
never incorrectly merged.

**Acceptance criteria**

1. The optimizer SHALL treat a `CreateModel` and a following
   `AlterModelManagers` as referring to the same model when their model names
   match case-insensitively.
2. IF a `CreateModel` is followed by an `AlterModelManagers` whose target model
   name does not match the created model's name (case-insensitively), THEN the
   optimizer SHALL NOT collapse them into a single `CreateModel`.
3. WHEN the manager reconfiguration targets a different model than the one just
   created, THEN both the `CreateModel` operation and the `AlterModelManagers`
   operation SHALL remain in the optimized output.

## Requirement 3: Preserve all existing model-creation reductions

**User story:** As a maintainer, I want the existing reductions of
`CreateModel.reduce` to keep working exactly as before, so that adding the new
manager fusion introduces no regression.

**Acceptance criteria**

1. WHEN a `CreateModel` is immediately followed by an `AlterModelOptions` for
   the same model, THEN the optimizer SHALL continue to collapse them into a
   single `CreateModel` carrying the altered options, dropping any previously
   set option keys that the alteration omits.
2. WHEN a `CreateModel` is immediately followed by a change to the same model's
   `unique_together` or `index_together`, THEN the optimizer SHALL continue to
   collapse them into a single `CreateModel` carrying that option value.
3. WHEN a `CreateModel` is immediately followed by a change to the same model's
   `order_with_respect_to`, THEN the optimizer SHALL continue to collapse them
   into a single `CreateModel` carrying that setting.
4. WHEN a `CreateModel` is immediately followed by a `DeleteModel` for the same
   non-proxy model, THEN the optimizer SHALL continue to reduce the pair to no
   operations.
5. WHEN a `CreateModel` is immediately followed by a `RenameModel` of that
   model, THEN the optimizer SHALL continue to produce a single `CreateModel`
   under the new name, preserving fields, options, bases, and managers.
6. WHEN a `CreateModel` is immediately followed by a field-level operation
   (adding, altering, removing, or renaming a field) on the same model, THEN
   the optimizer SHALL continue to fold that field change into the
   `CreateModel` as it did before.
7. The optimizer SHALL continue to return its existing result for every
   operation pairing it already reduced, so that no previously optimized
   sequence changes its outcome.
