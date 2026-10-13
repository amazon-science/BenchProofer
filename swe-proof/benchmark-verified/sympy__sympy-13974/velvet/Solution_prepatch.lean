import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An opaque binary primitive on symbolic factors: forming the power of a factor
   by a shared exponent. It is the repository's exponentiation constructor, taken
   as UNINTERPRETED — the specification assumes NO algebraic facts about it, so it
   carries no soundness obligation (no `ensures` is consumed; it is not a kind-A
   axiom). The factor↔value bijection and provenance live in mapping.md; an
   executable differential check is conformance_check.py (G-CONF). -/
abbrev Factor := Nat
opaque powF : Factor → Factor → Factor
-- axioms-end

-- pure-start
/- Distribute one shared exponent across a sequence of factors: each factor is
   raised, position-wise, to that exponent. Front-recursive so a single unfold is
   available per loop step (the verified-fold pattern). -/
def powAll (n : Factor) : List Factor → List Factor
  | []      => []
  | b :: bs => powF b n :: powAll n bs

@[grind] lemma powAll_nil (n : Factor) : powAll n [] = [] := rfl
@[grind] lemma powAll_cons (n b : Factor) (bs : List Factor) :
    powAll n (b :: bs) = powF b n :: powAll n bs := rfl

/- One factor position of a product whose factor carries its own aggregate: that
   aggregate's positions contribute either each raised to the shared exponent
   (when the factor is a power of the aggregate) or untouched (when the factor is
   the bare aggregate itself). The routing is decided by that single flag and by
   nothing else — in particular not by the number of positions, not by the
   exponent's value, and not by which position is being examined. -/
def factorImage (isPowOfAggregate : Bool) (n : Factor) (factors : List Factor) :
    List Factor :=
  if isPowOfAggregate then powAll n factors else factors
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method distributePow (factors : List Factor) (n : Factor) return (out : List Factor)
  ensures out = powAll n factors
  do
    -- impl-start
    -- Pre-image skeleton: the shared exponent is applied to the aggregate as a
    -- whole, leaving the factor sequence UNCHANGED (the per-position raise is
    -- never performed). The frozen spec requires `powAll n factors` (each factor
    -- raised), so prove_correct MUST fail.
    let mut result : List Factor := []
    let mut i := factors.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ factors.length
      invariant result = powAll n (factors.drop i)
      done_with i = 0
      decreasing i
    do
      let b := factors[i - 1]!
      result := b :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer factor exposes the factor at `i-1`
   on the front, so `powAll` peels one `powF`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma powAll_drop_step (factors : List Factor) (n : Factor) (i : Nat)
    (hi : 0 < i) (hle : i ≤ factors.length) :
    powAll n (factors.drop (i - 1)) = powF factors[i - 1]! n :: powAll n (factors.drop i) := by
  have hlt : i - 1 < factors.length := by omega
  have hcons : factors.drop (i - 1) = factors[i - 1]! :: factors.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, powAll_cons]

prove_correct distributePow by
  loom_solve
  rw [powAll_drop_step factors n i (by omega) (by omega)]
  simp_all

/- The factor-position operation. `isPowOfAggregate` says whether the examined
   factor is a power of the aggregate whose positions are `factors` (then `n` is
   that power's exponent) or the bare aggregate itself. Desired behaviour: a
   power-of-aggregate factor contributes the per-position raise; a bare-aggregate
   factor contributes its positions unchanged. This is the operation every place
   a factor of a product is examined must perform, so that the per-position raise
   is reached for a power of an aggregate occurring as ONE factor of a product and
   not only as a whole expression. -/
method simplifyFactor (isPowOfAggregate : Bool) (factors : List Factor) (n : Factor)
    return (out : List Factor)
  ensures out = factorImage isPowOfAggregate n factors
  ensures isPowOfAggregate = true → out = powAll n factors
  ensures isPowOfAggregate = false → out = factors
  do
    -- impl-start
    -- Pre-image skeleton: a factor of a product that is a power of an aggregate
    -- is left alone — the examined factor's positions are handed back untouched
    -- whatever the flag says, so the per-position raise is never reached from a
    -- factor position. The frozen spec requires the per-position raise when the
    -- flag is set, so prove_correct MUST fail.
    return factors
    -- impl-end

prove_correct simplifyFactor by
  loom_solve
  all_goals simp_all [factorImage]
