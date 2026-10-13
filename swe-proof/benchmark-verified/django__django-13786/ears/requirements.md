# Requirements: Clearing model options when squashing CreateModel with a Meta-options change

## Introduction

Django's migration optimizer collapses consecutive migration operations into
fewer operations. When a model is created and then its Meta options are changed
in a later operation, the optimizer can fold the options change directly into
the original model-creation operation, producing a single model-creation
operation that already carries the final set of options.

This behavior lives in the migration operations module
`django/db/migrations/operations/models.py`, specifically in the
`CreateModel.reduce()` method, in the branch that handles reducing a
`CreateModel` operation together with a following `AlterModelOptions` operation
that targets the same model.

The defect being addressed: when the two operations are combined, the resulting
model-creation operation only ever *overlays* the change operation's options on
top of the creation operation's options. It never *removes* options that the
change operation intends to unset. This diverges from how an
`AlterModelOptions` operation applies to model state on its own (its
`state_forwards()` treats the operation's options as authoritative for a fixed
family of Meta option keys), so a squashed migration ends up retaining options
that a non-squashed run of the same migrations would have cleared. The goal is
to make the folded result carry exactly the options that applying the change
operation to the created model would yield.

Throughout, "creation operation" means the `CreateModel` operation, "change
operation" means the `AlterModelOptions` operation, and "managed option keys"
means the fixed family of Meta option keys that `AlterModelOptions` treats as
owned by the change operation (the same set used by
`AlterModelOptions.state_forwards()`).

## Requirement 1: Fold an options change into model creation with correct clearing semantics

**User story:** As a developer squashing migrations, I want a model-creation
step followed by a Meta-options change on the same model to optimize into a
single model-creation step whose options exactly match the end state, so that
squashed migrations produce the same model configuration as the original,
unsquashed sequence.

**Acceptance criteria**

1. WHEN `CreateModel.reduce()` is asked to reduce its operation together with an
   `AlterModelOptions` operation whose target model name matches the created
   model (case-insensitively), THEN `reduce()` SHALL return a single
   replacement `CreateModel` operation for that model.

2. The replacement operation SHALL preserve the created model's identity
   unchanged, carrying the same model name, the same fields, the same bases, and
   the same managers as the original creation operation.

3. WHEN the replacement operation's options are computed, THEN `reduce()` SHALL
   start from the union of the creation operation's options and the change
   operation's options, with the change operation's value taking precedence for
   any option key present in both.

4. IF an option key belongs to the managed option keys AND that key is NOT
   present in the change operation's options, THEN `reduce()` SHALL remove that
   key from the replacement operation's options, even when the creation
   operation had set it.

5. WHEN the change operation's options is empty, THEN the replacement
   operation's options SHALL contain none of the managed option keys that the
   creation operation had set (i.e. all such creation-supplied managed options
   SHALL be cleared).

6. IF an option key is present in the change operation's options, THEN the
   replacement operation's options SHALL retain that key with the change
   operation's value, regardless of whether the key is a managed option key.

7. IF an option key is NOT one of the managed option keys AND is present only in
   the creation operation's options, THEN the replacement operation's options
   SHALL retain that key with the creation operation's value.

## Requirement 2: Preserve existing overlay behavior for changed and added options

**User story:** As a developer relying on the optimizer, I want the folding of a
Meta-options change into model creation to keep working for options that are
added or overridden, so that this fix does not regress the previously supported
optimization.

**Acceptance criteria**

1. WHEN the change operation sets an option key that the creation operation did
   not set, THEN the replacement operation's options SHALL include that key with
   the change operation's value.

2. WHEN the change operation sets an option key to a new value that the creation
   operation had set to a different value, THEN the replacement operation's
   options SHALL hold the change operation's value for that key.

3. The replacement operation's options SHALL contain no option key that is
   absent from both the creation operation's options and the change operation's
   options.

## Requirement 3: Do not disturb reduction of other operation combinations

**User story:** As a maintainer, I want this change confined to the
create-then-alter-options case, so that all other optimizer reductions behave
exactly as before.

**Acceptance criteria**

1. The clearing behavior for managed option keys SHALL apply only when reducing a
   `CreateModel` together with an `AlterModelOptions` operation; the system
   SHALL NOT alter the options produced when reducing a `CreateModel` together
   with any other operation kind (for example renaming the model, altering
   together-options, altering order-with-respect-to, or field operations).

2. WHEN `reduce()` is given an operation whose target model name does not match
   the created model, THEN `reduce()` SHALL NOT fold that operation into the
   creation operation.
