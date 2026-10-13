import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No unchanged dependency callee is CONSUMED by this specification. The
-- registration step is modeled structurally below as a single-name update on a
-- class namespace, so there is no `axiom`/stub callee to declare. The accessor
-- that would be generated is taken as an abstract token (`gen`): the step never
-- inspects its value, only whether the target name is already bound.
-- axioms-end

-- pure-start
/- A class namespace, viewed as the partial map from an accessor name to the
   identity of the attribute bound there: `some t` when the name is bound to an
   attribute of identity-kind `t`, `none` when the name is free. -/
abbrev Namespace := String → Option Nat

/- Install the generated accessor `gen` at name `key`, but only when that name is
   currently free. When the name is already bound, the namespace is returned
   unchanged, so whatever was bound there stays in force; every other name is
   left untouched in both cases. -/
def registerDisplay (lookup : Namespace) (key : String) (gen : Nat) : Namespace :=
  if (lookup key).isNone then
    (fun n => if n = key then some gen else lookup n)
  else
    lookup
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method registerAccessor (lookup : Namespace) (key : String) (gen : Nat)
  return (out : Namespace)
  ensures out = registerDisplay lookup key gen
  do
    -- impl-start
    -- Pre-image skeleton: the generated accessor is installed at `key`
    -- unconditionally, displacing whatever was already bound there. The frozen
    -- spec requires the set-if-absent `registerDisplay`, so prove_correct MUST
    -- fail whenever `key` is already bound.
    let mut result := lookup
    result := (fun n => if n = key then some gen else lookup n)
    return result
    -- impl-end

prove_correct registerAccessor by
  loom_solve <;> simp_all [registerDisplay]
