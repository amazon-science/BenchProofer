import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A polynomial is modelled as an opaque identity `Int`, a value DISTINCT from
   the factor list it must produce; a factorisation is a `List Int` of factor
   identities. The operations below are the unchanged library routines the
   function invokes, plus the two shape tests it consults about its input; each
   is axiomatised by the weakest behaviour the proof needs and its soundness is
   validated executably against the real callees (mapping.md / axiom_check.py,
   G-AX). -/

/- `factorList p` — the complete factorisation of a polynomial `p`: a determinate
   sequence depending ONLY on its argument. Weakest behaviour the proof needs:
   SOME determinate sequence as a function of `p` (nothing relates the lists of
   two DIFFERENT arguments, so applying it to a different polynomial yields, in
   general, a different list). Provenance + soundness: mapping.md /
   axiom_check.py (G-AX). -/
axiom factorList : Int → List Int

/- `otherPoly p` — an auxiliary identity computed from `p`. The weakest behaviour
   the proof needs: it returns SOME identity, about which NOTHING is promised — in
   particular nothing relates its value to `p`. Provenance / soundness: mapping.md
   / axiom_check.py. -/
axiom otherPoly : Int → Int

/- `lone p` — a determinate one-element factorisation depending only on `p` (the
   legitimate non-splitting case); nothing further is promised. Provenance /
   soundness: mapping.md / axiom_check.py. -/
axiom lone : Int → List Int
axiom loneLen : ∀ p : Int, (lone p).length = 1

/- `isConstant p` — the shape test the operation makes on its argument before any
   factoring is attempted: `true` exactly when `p` carries no positive degree in
   any generator (a constant of the coefficient field). A determinate Boolean
   function of `p`; nothing else is promised. Provenance / soundness: mapping.md
   / axiom_check.py. -/
axiom isConstant : Int → Bool

/- `noRepeatedFactor p` — `true` exactly when no irreducible factor occurs in `p`
   more than once. A determinate Boolean function of `p`; nothing else is
   promised. It is a property of the ARGUMENT AS GIVEN and of nothing else: NOT of
   any intermediate value the operation derives from `p`, and in particular NOT of
   the successive images its factor recovery steps through — such an image may
   carry a repeated factor even when `p` does not, which is precisely why the
   recovery can need several steps on an argument that IS in the domain, so the
   recovery's own per-step test is a DIFFERENT predicate from this one. Together
   with `hasMainDegree` it delimits the arguments on which the operation is
   DEFINED (see the `require`s). Provenance / soundness: mapping.md /
   axiom_check.py. -/
axiom noRepeatedFactor : Int → Bool

/- `hasMainDegree p` — the second shape test the operation's factor recovery
   depends on: `true` exactly when `p` carries positive degree in the FIRST
   (main) generator of the dense representation it is given. Again a property of
   the ARGUMENT AS GIVEN, not of any value the operation derives from it. A
   determinate Boolean function of `p`; nothing else is promised. Together with
   `noRepeatedFactor` it delimits the arguments on which the operation is
   DEFINED (see the `require`s). Provenance / soundness: mapping.md /
   axiom_check.py. -/
axiom hasMainDegree : Int → Bool
-- axioms-end

-- pure-start
/- The complete factorisation the contract demands of the input `poly`. A
   CONSTANT input carries no factor content, so the demanded result is the EMPTY
   sequence — the operation reports nothing for it. Otherwise: when the
   input-driven factoring splits into ≥ 2 elements the demanded result is
   precisely that factor list, and when it does not it is the single-element
   fallback `lone poly` (the legitimate non-splitting case). Expressed purely
   STRUCTURALLY over `isConstant poly` and `factorList poly` (sequence equality
   and length only — no answer-key lookup), so the obligation stays inside the
   decidable fragment. Front-recursive selection so a single reduction is
   available (the Velvet pattern). -/
noncomputable def expectedFactors (poly : Int) : List Int :=
  if isConstant poly then []
  else if (factorList poly).length ≥ 2 then factorList poly else lone poly

@[grind] lemma expectedFactors_const (poly : Int)
    (h : isConstant poly = true) : expectedFactors poly = [] := by
  unfold expectedFactors; simp [h]

@[grind] lemma expectedFactors_split (poly : Int) (hc : isConstant poly = false)
    (h : (factorList poly).length ≥ 2) : expectedFactors poly = factorList poly := by
  unfold expectedFactors; simp [hc, h]

@[grind] lemma expectedFactors_lone (poly : Int) (hc : isConstant poly = false)
    (h : ¬ (factorList poly).length ≥ 2) : expectedFactors poly = lone poly := by
  unfold expectedFactors; simp [hc, h]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `extFactor lc poly` — factor a multivariate polynomial over an algebraic
   number field. `poly` is the opaque input polynomial identity; `lc` the leading
   coefficient passed through unchanged. The contract pins the result to the
   COMPLETE factorisation OF THE INPUT: a constant input is reported with the
   EMPTY factorisation; otherwise, when the factoring splits into ≥ 2 elements
   the result is exactly `factorList poly`, and when it does not it is the
   one-element `lone poly`. On every non-constant input the result must equal the
   factorisation OF THE INPUT itself. -/
noncomputable section
method extFactor (lc : Int) (poly : Int) return (out : List Int)
  -- pre-conditions-start
  /- DOMAIN, first half. The operation is DEFINED only on arguments in which no
     irreducible factor occurs more than once — a condition on the ARGUMENT
     ITSELF. Its factor recovery reaches a reportable image by stepping through
     successive images of the argument taken over the ground domain: an argument
     with no repeated factor is guaranteed to reach one after FINITELY MANY steps,
     though not necessarily at the first, since an early image may still carry a
     repeated factor — so the recovery's own per-step test is NOT this condition
     and must not be mistaken for it. An argument in which some irreducible factor
     recurs reaches no reportable image at all, so there no result — and in
     particular no termination — is promised. The condition is decidable and
     publicly observable on the real carrier, and it is satisfied VACUOUSLY by a
     constant (a unit has no irreducible factor at all). -/
  require noRepeatedFactor poly = true
  /- DOMAIN, second half. A NON-CONSTANT argument must additionally carry
     positive degree in the main generator. The operation reduces its argument
     with respect to the main generator alone and then reads multiplicities off
     the original by repeated division by the resulting factors; an argument with
     no main-generator degree reduces to a unit, and dividing by a unit never
     makes progress, so again no result and no termination is promised there. A
     CONSTANT argument is exempt because the operation reports it (with the empty
     factorisation) before any of that begins, so the empty-factorisation clause
     below lies inside the domain. Both halves are decidable and publicly
     observable on the real carrier and both are satisfied by every input the
     graded tests drive through this operation (mapping.md §3). -/
  require isConstant poly = false → hasMainDegree poly = true
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = expectedFactors poly
  ensures isConstant poly = true → out = []
  ensures isConstant poly = false → (factorList poly).length ≥ 2 → out = factorList poly
  ensures isConstant poly = false → ¬ (factorList poly).length ≥ 2 → out = lone poly
  -- post-conditions-end
  do
    -- impl-start
    -- PRE-PATCH BUG: the recovery is applied to the RELATED polynomial
    -- `otherPoly poly` (the square-free part, `dmp_sqf_norm(f, …)`), NOT the
    -- original `F`. `otherPoly`'s contract promises nothing about its factor
    -- content, so the materialised list is `factorList (otherPoly poly)`, which
    -- the proof cannot equate to the required `factorList poly` — the
    -- completeness clause fails (G-DIFF).
    let other := otherPoly poly
    if isConstant poly then
      -- constant argument: reported with no factors at all (`return lc, []`).
      return ([] : List Int)
    else
      let images := factorList other
      let mut result : List Int := []
      if images.length ≥ 2 then
        -- two or more elements: the complete factor list of the input.
        let mut i := images.length
        while i > 0
          invariant 0 ≤ i ∧ i ≤ images.length
          invariant result = images.drop i
          done_with i = 0
          decreasing i
        do
          result := images[i - 1]! :: result
          i := i - 1
      else
        -- single element: the one-element fallback `lone poly`.
        let blob := lone poly
        let mut i := blob.length
        while i > 0
          invariant 0 ≤ i ∧ i ≤ blob.length
          invariant result = blob.drop i
          done_with i = 0
          decreasing i
        do
          result := blob[i - 1]! :: result
          i := i - 1
      return result
    -- impl-end
end

/- Backward-fold step: dropping one fewer element exposes the element at `i-1`
   on the front, so the materialised prefix grows by one. The single goal
   `loom_solve` leaves for each loop body. -/
lemma drop_step (xs : List Int) (i : Nat) (hi : 0 < i) (hle : i ≤ xs.length) :
    xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
  have hlt : i - 1 < xs.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct extFactor by
  loom_solve
  -- The loop-body fold steps close, but the postcondition goals
  --   `out = factorList poly` / `out = expectedFactors poly`
  -- are UNPROVABLE: the impl materialises `factorList (otherPoly poly)`, and
  -- `otherPoly`'s contract relates nothing to `poly`'s factor content, so the
  -- completeness clause cannot be discharged. This is the intended G-DIFF
  -- failure (the dropped-factor bug).
  all_goals
    try (first
      | (rw [drop_step (factorList (otherPoly poly)) i (by omega) (by omega)]; simp_all)
      | (rw [drop_step (lone poly) i (by omega) (by omega)]; simp_all))
