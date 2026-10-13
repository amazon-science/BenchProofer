# Requirements: Collapse redundant AlterUniqueTogether / AlterIndexTogether operations

## Introduction

Django's migration framework represents changes to a model's grouped column
options with two operation types: `AlterUniqueTogether` (option
`unique_together`) and `AlterIndexTogether` (option `index_together`), both
subclasses of `AlterTogetherOptionOperation` in
`django/db/migrations/operations/models.py`.

To let field alterations run safely, the autodetector emits these option
changes as a *clear-then-set* pair: first an operation that empties the option
(`unique_together=set()` / `index_together=set()`), then a later operation that
installs the new value. When both `unique_together` and `index_together` change
for the same model, this produces four operations — two clears followed by two
sets — where two would suffice.

The `MigrationOptimizer` (`django/db/migrations/optimizer.py`) merges adjacent
operations by asking each operation, via its `reduce(operation, app_label)`
method, whether it can be combined with, or reordered across, a following
operation. Today an alter-together operation refuses to be optimized across any
later operation that references the same model, so the clear of one option and
the set of that option are never brought together across the intervening
change to the *other* option, and the redundant pair survives.

The goal is to make the optimizer collapse such a redundant clear-then-set of a
model's `unique_together` and `index_together` into a single operation per
option, while preserving all other ordering guarantees the optimizer already
provides (field additions before use, renames before use, removals after use,
and no reordering across unrelated model-referencing operations).

The affected behavior lives in `AlterTogetherOptionOperation` (and its
subclasses `AlterUniqueTogether` and `AlterIndexTogether`) and is observed
through `MigrationOptimizer.optimize(operations, app_label)` and the migration
autodetector that feeds it.

## Requirement 1: Optimize an alter-together operation across an alter-together change of the other option

**User story:** As a Django developer generating migrations, I want an
`AlterUniqueTogether` change to be optimizable across a following
`AlterIndexTogether` change (and vice versa) on the same model, so that the
optimizer can bring together the two operations that touch the *same* option
and merge them.

**Acceptance criteria**

1. WHEN an `AlterUniqueTogether` operation is asked, via its
   `reduce` method, whether it can be optimized across a later
   `AlterIndexTogether` operation on the same model, THEN the operation SHALL
   report that it can be optimized across that later operation.
2. WHEN an `AlterIndexTogether` operation is asked, via its `reduce` method,
   whether it can be optimized across a later `AlterUniqueTogether` operation
   on the same model, THEN the operation SHALL report that it can be optimized
   across that later operation.
3. The system SHALL treat `unique_together` and `index_together` as independent
   option groups, so that an operation altering one option may always be
   reordered relative to an operation altering the other option on the same
   model.
4. IF the later operation is an alter-together operation of the *same* option
   type on the same model, THEN the two operations SHALL still be combined into
   a single operation carrying the later operation's value (the pre-existing
   merge behavior SHALL be preserved).

## Requirement 2: Collapse a redundant clear-then-set of grouped options into one operation per option

**User story:** As a Django developer, I want a migration that clears and then
re-sets both `unique_together` and `index_together` for a single model to be
reduced to one operation per option, so that each constraint group is altered
exactly once instead of twice.

**Acceptance criteria**

1. WHEN `MigrationOptimizer.optimize` is given, for a single model, an
   `AlterUniqueTogether` to the empty set followed by an `AlterIndexTogether`
   to the empty set followed by an `AlterUniqueTogether` to a non-empty value
   followed by an `AlterIndexTogether` to a non-empty value, THEN it SHALL
   return exactly one `AlterUniqueTogether` and one `AlterIndexTogether` for
   that model.
2. WHEN such a sequence is optimized, THEN the surviving `AlterUniqueTogether`
   SHALL carry the final `unique_together` value and the surviving
   `AlterIndexTogether` SHALL carry the final `index_together` value; neither
   an empty-set clear nor its later set SHALL remain as a separate operation.
3. The system SHALL preserve this collapse regardless of whether the option
   change was triggered by a new value, by removing all entries (an empty
   target), or by a change only in the ordering of the grouped columns.
4. WHILE optimizing, the system SHALL leave the relative order of the surviving
   `AlterUniqueTogether` and `AlterIndexTogether` operations well-defined and
   SHALL not increase the total number of operations.

## Requirement 3: Preserve existing ordering guarantees around field operations

**User story:** As a Django developer, I want the collapse of alter-together
operations to keep working correctly alongside field additions, removals, and
renames, so that the optimized migration still applies in a valid order.

**Acceptance criteria**

1. IF a field must be added before it is referenced by a grouped-option value,
   THEN the optimizer SHALL keep the field-adding operation before the
   alter-together operation that references that field (an alter-together
   operation SHALL NOT be optimized across an add-field operation on the same
   model).
2. IF a field is removed after the grouped options are updated, THEN the
   optimizer SHALL keep the field-removing operation after the collapsed
   alter-together operations for that model (an alter-together operation SHALL
   NOT be optimized across a remove-field operation on the same model).
3. IF a field is renamed before the grouped options are updated, THEN the
   optimizer SHALL keep the field-renaming operation before the collapsed
   alter-together operations for that model (an alter-together operation SHALL
   NOT be optimized across a rename-field operation on the same model).
4. The system SHALL continue to allow an alter-together operation to be
   optimized across any later operation that does not reference the same model,
   exactly as before this change.
5. WHEN a sequence contains both a redundant clear-then-set of the grouped
   options and a field removal for the same model, THEN the optimizer SHALL
   return the collapsed single `AlterUniqueTogether` and single
   `AlterIndexTogether` followed by the field-removal operation.
6. WHEN a sequence contains a field rename for a model followed by a redundant
   clear-then-set of that model's grouped options, THEN the optimizer SHALL
   return the field-rename operation followed by the collapsed single
   `AlterUniqueTogether` and single `AlterIndexTogether`.
