# Requirements: Reduce Add/Remove index migration operations

## Introduction

Django's migration framework contains an optimizer that shortens a sequence of
migration operations by repeatedly asking each operation whether it can be
*reduced* against the operation that immediately follows it. Each operation
exposes a `reduce(operation, app_label)` method (defined on the base
`Operation` class in `django/db/migrations/operations/base.py`) that returns
either a list of operations to replace the pair with, or a value indicating the
two operations cannot be optimized across each other.

Index operations live in `django/db/migrations/operations/models.py`:
`AddIndex` (which carries an `index` whose `name` identifies the index it
creates) and `RemoveIndex` (which carries the `model_name` and the `name` of
the index it drops). Prior to this change, an `AddIndex` followed by a
`RemoveIndex` of the very same index was left untouched by the optimizer, even
though the two operations cancel each other out and produce no net schema
change.

The goal is to teach the optimizer that adding an index and then removing that
same index is a no-op, so the pair collapses to nothing — while leaving every
other optimization behavior of the migration optimizer unchanged.

## Requirement 1: Cancel an AddIndex against a following matching RemoveIndex

**User story:** As a developer squashing/optimizing migrations, I want an
`AddIndex` immediately followed by a `RemoveIndex` of the same index to be
eliminated, so that redundant index creation/deletion is not emitted into the
optimized migration.

**Acceptance criteria**

1. WHEN the migration optimizer reduces an `AddIndex` operation against a
   following `RemoveIndex` operation whose target index name equals the name of
   the index the `AddIndex` creates, THEN the reduction SHALL return an empty
   list of operations, so that the pair is removed entirely from the optimized
   sequence.
2. WHEN the optimizer is given a sequence consisting solely of an `AddIndex`
   creating an index and a subsequent `RemoveIndex` naming that same index (on
   the same model), THEN the optimizer SHALL produce an empty result sequence.
3. The comparison that decides cancellation SHALL match the index name created
   by the `AddIndex` operation against the index name carried by the
   `RemoveIndex` operation, using exact (case-sensitive) string equality.

## Requirement 2: Do not cancel when the following operation does not match

**User story:** As a developer, I want the optimizer to only collapse an
`AddIndex`/`RemoveIndex` pair when they truly refer to the same index, so that
unrelated operations are preserved.

**Acceptance criteria**

1. IF the operation following an `AddIndex` is a `RemoveIndex` whose target
   index name is different from the name of the index created by the
   `AddIndex`, THEN the `AddIndex` reduction SHALL NOT return an empty list and
   SHALL instead defer to the generic base-class reduction behavior.
2. IF the operation following an `AddIndex` is not a `RemoveIndex`, THEN the
   `AddIndex` reduction SHALL defer to the generic base-class reduction
   behavior and SHALL return exactly what that generic reduction yields for the
   same two operations and application label.
3. The system SHALL leave the outcome for any non-cancelling case identical to
   the behavior that existed before this change (i.e. the inherited
   `Operation.reduce` result), introducing no new reduction outcome other than
   the empty-list cancellation of Requirement 1.

## Requirement 3: Preserve all existing optimizer behavior

**User story:** As a maintainer, I want the new cancellation to be additive, so
that every other migration-operation optimization continues to work exactly as
before.

**Acceptance criteria**

1. The system SHALL continue to collapse a `CreateModel` immediately followed
   by a matching `DeleteModel` into no operations.
2. The system SHALL continue to optimize `AddField`, `AlterField`,
   `RemoveField`, and `RenameField` operations into a preceding `CreateModel`
   (or across each other) exactly as before.
3. The system SHALL continue to optimize adjacent `AlterField` operations,
   and to let a `RemoveField` absorb a preceding `AlterField`, unchanged.
4. The system SHALL continue to optimize model-option operations
   (`AlterModelOptions`, `AlterModelManagers`, `AlterUniqueTogether`,
   `AlterIndexTogether`/index alterations, `AlterModelTable`) relative to a
   preceding `CreateModel` or across each other, unchanged.
5. The system SHALL continue to optimize `RenameIndex` operations as before,
   with the addition in Requirement 1 not altering rename-index handling.
6. WHEN the optimizer is given a single operation, THEN it SHALL leave that
   operation unchanged.
7. The system SHALL continue to optimize across any operation that is elidable,
   and SHALL treat an `app_label` of `None` in the reduction the same as
   before.
8. The system SHALL keep the reduction total and deterministic: for identical
   inputs the reduction SHALL always yield the same outcome, and every
   non-cancelling case SHALL yield a well-defined result rather than an error.
