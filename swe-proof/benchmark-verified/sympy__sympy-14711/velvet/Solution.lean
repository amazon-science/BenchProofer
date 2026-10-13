import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A vector value, abstracted to an opaque handle. The behaviour under spec
   observes a vector value in only two ways: by identity (returning the very
   same vector unchanged), and through the unchanged binary combination of two
   vectors (`combine` below). The internal component representation is never
   inspected by this behaviour, so it is abstracted away. Provenance + executable
   soundness check: mapping.md §1 / axiom_check.py (G-AX). -/
structure VecVal where
  handle : Int
  deriving DecidableEq, Inhabited

/- The right operand of the combination, classified into the three shapes the
   behaviour distinguishes:

     * `zero`    — the additive identity (a non-vector value that compares equal
                   to the additive identity, e.g. the neutral element a running
                   total is seeded with). It is NOT itself a vector.
     * `vec v`   — a genuine, non-identity vector value.
     * `foreign` — any other value that is neither a vector nor the additive
                   identity.

   These are exactly the classes the desired behaviour treats differently
   (mapping.md §2). -/
inductive Operand where
  | zero
  | vec (v : VecVal)
  | foreign
  deriving DecidableEq

/- The single distinguished failure outcome: the operand could not be brought
   into vector form (the type error a downstream coercion raises when handed a
   value that is not a vector). -/
inductive AddErr where
  | notAVector
  deriving DecidableEq

/- The UNCHANGED operand-coercion callee, modeled DEEPLY: it accepts a genuine
   vector unchanged, and rejects everything else (the additive identity and any
   foreign value) with the type-error outcome. This callee is invoked, never
   redefined, by the behaviour under spec; spelling it out makes it an
   A-reference validated == the real callee by G-AX. Provenance: mapping.md §3.1
   / axiom_check.py. -/
def asVector : Operand → Except AddErr VecVal
  | .vec v   => Except.ok v
  | .zero    => Except.error .notAVector
  | .foreign => Except.error .notAVector

/- The UNCHANGED binary combination of two genuine vector values (the
   constructor that builds the combined vector). Its concrete result is
   orthogonal to the behaviour under spec — only that it combines two vectors
   into a vector matters — so it is modeled `opaque` with NO
   asserted `ensures` (it is the same function in the spec and in the impl, so it
   is grounded, not an oracle). Provenance + executable soundness check:
   mapping.md §3.2 / axiom_check.py (G-AX). -/
opaque combine : VecVal → VecVal → VecVal
-- axioms-end

-- pure-start
/- Whether the right operand is the additive identity — the value that compares
   equal to the neutral element of addition. True for the identity, False for a
   genuine vector and for any foreign value. -/
def isZeroOperand : Operand → Bool
  | .zero    => true
  | .vec _   => false
  | .foreign => false

/- The desired result of combining a vector `self` with a right operand:

     * if the operand is the additive identity, the combination ABSORBS it and
       yields `self` unchanged — no coercion is attempted, so no type error can
       arise from the identity;
     * otherwise the operand is coerced to vector form (a genuine vector passes;
       anything else is rejected with the type-error outcome) and, on success,
       the two vectors are combined.

   The absorbing case is the behaviour the public report asks for: seeding a
   running total with the additive identity and adding a vector must succeed,
   returning the vector, rather than failing the coercion. -/
def addSpec (self : VecVal) (other : Operand) : Except AddErr VecVal :=
  if isZeroOperand other then Except.ok self
  else match asVector other with
    | Except.ok v    => Except.ok (combine self v)
    | Except.error e => Except.error e
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine a vector `self` with a right operand `other`, taking care of the
   additive identity.

   Desired behaviour: when `other` is the additive identity, the combination
   absorbs it and returns `self` unchanged (the missing behaviour the public
   report exhibits — seeding a running total with the identity and adding a
   vector must not fail). Otherwise the operand is coerced to vector form: a
   genuine vector is accepted and the two are combined; any other value is
   rejected with the type-error outcome.

   Both `self` and `other` are read-only (not `mut`): the combination computes a
   fresh result and mutates neither operand (directive 5). A vector value is
   modeled as an opaque handle; the only observations are identity and the
   unchanged binary combination (mapping.md §1-2). -/
method vectorAdd (self : VecVal) (other : Operand)
    return (out : Except AddErr VecVal)
  ensures out = addSpec self other
  do
    -- impl-start
    -- Absorb the additive identity BEFORE attempting any coercion, so the
    -- identity yields `self` instead of being rejected; otherwise coerce the
    -- operand to vector form and combine, propagating the rejection unchanged.
    let result : Except AddErr VecVal :=
      if isZeroOperand other then Except.ok self
      else match asVector other with
        | Except.ok v    => Except.ok (combine self v)
        | Except.error e => Except.error e
    return result
    -- impl-end

prove_correct vectorAdd by
  loom_solve
  simp_all [addSpec]
