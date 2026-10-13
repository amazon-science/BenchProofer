import Mathlib
-- imports-end

/-!
Resolving the numeric permission mode that newly uploaded files are given by the
filesystem-backed storage.

The effective mode is decided in three layers, most specific first:

  * a per-storage-instance override (the mode passed when the storage object was
    constructed): if it carries a concrete mode, that mode wins outright;
  * otherwise the project-wide configured mode is consulted. The project may
    leave this unconfigured, in which case the framework's built-in default
    applies; or it may pin it to a concrete choice (which itself may be a
    definite mode or the explicit "no special mode" choice);
  * the framework's built-in default mode, used when nothing more specific was
    supplied.

A mode of "absent" (no concrete number) means the storage performs no explicit
permission adjustment and the surrounding operating-system behavior is left in
effect; a concrete number is the octal mode to apply.

The built-in default is a concrete, predictable mode (`0o644`) so that uploaded
files receive consistent permissions regardless of how the upload was buffered.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The per-instance override, the
-- project-configured mode, and the built-in default all enter as plain data
-- (modeled as `Option`), and the only operation performed is the most-specific
-- wins selection, modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The framework's built-in default permission mode: a concrete octal mode
(`0o644`). `Option Nat` carries a permission mode, with `none` meaning "no
explicit mode" and `some m` the octal number `m`. -/
def defaultUploadMode : Option Nat := some 0o644
-- pure-end

-- post-conditions-start
/-- The resolved permission mode is fully pinned to the inputs:

  * if the per-storage override carries a concrete mode `m`, the result is
    exactly `some m` (the override wins, whatever the project setting);
  * if there is no per-storage override, the result is exactly the
    project-configured mode when one is configured, and otherwise the built-in
    default mode.

Both layers together determine the result for every input, so no output is left
free. -/
def problem_spec_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat))
    (result : Option Nat) : Prop :=
  (∀ m, storageOverride = some m → result = some m) ∧
  (storageOverride = none →
      result = (match projectSetting with
                | some v => v
                | none   => defaultUploadMode))
-- post-conditions-end

-- impl-start
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := none
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting
-- impl-end

-- proof-start
theorem correct_effectiveFilePermissionsMode :
    ∀ (storageOverride : Option Nat) (projectSetting : Option (Option Nat)),
      problem_spec_effectiveFilePermissionsMode storageOverride projectSetting
        (implementation_effectiveFilePermissionsMode storageOverride projectSetting) := by
  intro storageOverride projectSetting
  unfold problem_spec_effectiveFilePermissionsMode implementation_effectiveFilePermissionsMode
  constructor
  · intro m hm
    subst hm
    cases projectSetting <;> rfl
  · intro h
    subst h
    cases projectSetting <;> rfl
-- proof-end
