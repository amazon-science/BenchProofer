import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The configuration that
-- precedes the modeled decision (the surrounding serialization that produces the
-- other recorded entries) is orthogonal to which storage reference is recorded,
-- and the identity comparison itself is modeled DEEPLY below rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- When a field's configuration is serialized into a reconstructable form, the
storage reference that gets recorded is the *original* storage specification: the
caller-supplied callable when one was supplied, otherwise the configured storage
instance. That reference is recorded only when it differs from the default
storage; when it coincides with the default it is left out entirely.

Storage objects are compared by identity, modeled here as a numeric identity
(`Nat`); `none` means no storage reference is recorded, `some s` means the
reference `s` is recorded. Every component of the decision is pinned to the
inputs: the recorded reference, and whether one is recorded at all, are fully
determined by the original specification and the default identity. -/
def problem_spec_recordedStorage
    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat)
    (result : Option Nat) : Prop :=
  result =
    (let storage := originalCallable.getD evaluatedStorage
     if storage = defaultStorage then none else some storage)
-- post-conditions-end

-- impl-start
def implementation_recordedStorage
    (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat) :
    Option Nat := Id.run do
  -- Pre-patch (buggy): the "differs from default" test is made against the
  -- already-evaluated storage instance rather than the original specification, so
  -- an original reference that evaluates to the default is dropped instead of
  -- being recorded.
  let storage := originalCallable.getD evaluatedStorage
  let mut result : Option Nat := none
  if evaluatedStorage ≠ defaultStorage then
    result := some storage
  return result
-- impl-end

-- proof-start
theorem correct_recordedStorage :
    ∀ (originalCallable : Option Nat) (evaluatedStorage : Nat) (defaultStorage : Nat),
    problem_spec_recordedStorage originalCallable evaluatedStorage defaultStorage
      (implementation_recordedStorage originalCallable evaluatedStorage defaultStorage) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
