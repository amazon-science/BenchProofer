# Requirements: Migration optimizer reduces consecutive AlterField operations

## Introduction

Django's migration optimizer collapses redundant migration operations by
repeatedly asking each operation to `reduce` against the operation that
immediately follows it. The operation of interest is `AlterField`
(`django/db/migrations/operations/fields.py`), whose `reduce(self, operation,
app_label)` method decides whether the receiver `AlterField` and the following
`operation` can be combined.

Currently, when an `AddField` for a column is immediately followed by one or
more `AlterField` operations on that same column, the optimizer collapses them
into the `AddField`. But when the `AddField` is absent — for example the field
is added in an earlier, separate (non-squashed or non-elidable) migration — a
run of successive `AlterField` operations on the *same* field is left
un-reduced: `AlterField.reduce` never recognizes that the following operation is
itself an `AlterField` on the same field, so each `AlterField` survives.

The goal is to make `AlterField.reduce` recognize the case where the following
operation is an `AlterField` targeting the same field, so that the earlier
`AlterField` is superseded by the later one and the pair collapses into just the
later operation — mirroring how consecutive `AlterModelTable`,
`AlterUniqueTogether`, `AlterIndexTogether`, and `AlterOrderWithRespectTo`
operations already collapse into the second. All other existing reduction
behavior of `AlterField` (against `RemoveField`, `RenameField`, `AddField`,
`CreateModel`, and unrelated operations) must be preserved.

This behavior is localized to `AlterField.reduce` and the same-field matching
performed by `FieldOperation.is_same_field_operation`.

## Requirement 1: Collapse consecutive AlterField operations on the same field

**User story:** As a developer squashing or optimizing migrations, I want two
successive alterations of the same field to reduce to the final alteration, so
that redundant intermediate `AlterField` operations do not accumulate when the
originating `AddField` is not present in the same operation list.

**Acceptance criteria**
1. WHEN `AlterField.reduce` is called and the following `operation` is an
   `AlterField` targeting the same field on the same model as the receiver,
   THEN `reduce` SHALL return a list containing only that following `operation`.
2. WHEN the migration optimizer is given a list of two or more consecutive
   `AlterField` operations that all target the same field on the same model,
   THEN it SHALL reduce them to a single `AlterField` operation whose field
   definition is that of the last `AlterField` in the run.
3. The system SHALL treat the field definition carried by the later
   `AlterField` (including attributes such as `max_length`, `null`, `help_text`,
   and `default`) as the surviving definition after the collapse, discarding the
   earlier `AlterField`'s field definition.
4. WHEN a list consists solely of successive same-field `AlterField` operations
   with no preceding `AddField`, THEN the optimizer SHALL still reduce that list
   (its length after optimization SHALL be less than its length before, down to
   a single operation for a same-field run).

## Requirement 2: Restrict the collapse to same-model, same-field operations

**User story:** As a developer, I want the optimizer to only merge alterations
that genuinely target the same field, so that unrelated field alterations are
never incorrectly discarded.

**Acceptance criteria**
1. Two operations SHALL be considered the same-field operation only when they
   reference the same model name and the same field name, each compared
   case-insensitively.
2. IF the following `operation` is an `AlterField` whose model name or field
   name differs from the receiver's (case-insensitively), THEN `AlterField.reduce`
   SHALL NOT collapse the two into the following operation.
3. WHEN two same-field `AlterField` operations differ only in the letter case of
   their model name or field name, THEN they SHALL still be recognized as
   targeting the same field and be eligible for the collapse in Requirement 1.

## Requirement 3: Preserve the existing AlterField-then-RemoveField reduction

**User story:** As a maintainer, I want removing a field after altering it to
keep collapsing to the removal, so that this change adds the new behavior
without regressing the existing one.

**Acceptance criteria**
1. WHEN `AlterField.reduce` is called and the following `operation` is a
   `RemoveField` targeting the same field on the same model, THEN `reduce` SHALL
   return a list containing only that `RemoveField` operation.

## Requirement 4: Preserve the existing AlterField-then-RenameField reduction

**User story:** As a maintainer, I want an alteration followed by a rename of the
same field to keep producing the rename plus a re-expressed alteration under the
new name, so that rename optimization is unaffected.

**Acceptance criteria**
1. WHEN `AlterField.reduce` is called, the following `operation` is a
   `RenameField` targeting the same field on the same model, and the receiver's
   field defines no explicit database column, THEN `reduce` SHALL return a list
   containing the `RenameField` followed by an `AlterField` that targets the
   renamed field (the rename's new name) and carries the receiver's field
   definition.
2. The system SHALL leave the ordering and content of this rename reduction
   unchanged from prior behavior.

## Requirement 5: Preserve reduction of AlterField into AddField and CreateModel

**User story:** As a developer, I want an alteration that immediately follows the
addition or creation of its field to keep folding into that addition/creation,
so that the common squash case is unaffected.

**Acceptance criteria**
1. WHEN a field is added by an `AddField` and then altered by an `AlterField`
   for the same field, THEN the optimizer SHALL collapse the two so that only
   the `AddField` (carrying the altered field definition) remains.
2. WHEN a model is created by a `CreateModel` that includes a field, and that
   field is subsequently altered by an `AlterField`, THEN the optimizer SHALL
   fold the alteration into the `CreateModel`.

## Requirement 6: Preserve behavior for unrelated following operations

**User story:** As a maintainer, I want alterations to remain un-reduced against
operations that do not target the same field, so that the optimizer never merges
across unrelated changes.

**Acceptance criteria**
1. IF the following `operation` does not target the same field and does not
   reference the receiver's field, THEN `AlterField.reduce` SHALL allow the two
   operations to commute rather than collapsing them.
2. WHEN the optimizer is given a single operation, THEN it SHALL leave that
   operation unchanged.
3. The system SHALL continue to collapse consecutive same-target
   `AlterModelTable`, `AlterUniqueTogether`, `AlterIndexTogether`, and
   `AlterOrderWithRespectTo` operations into the later one, unaffected by this
   change.
