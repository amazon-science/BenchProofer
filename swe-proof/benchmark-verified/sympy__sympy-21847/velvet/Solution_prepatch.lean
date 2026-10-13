import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The surrounding machinery the selection consults —
--  the enumerator that produces the bounded candidate exponent vectors and the
--  product constructor that turns a kept vector back into a term — is UNCHANGED
--  and is folded into the free input `candidates : List (List Nat)` (one entry
--  per enumerated candidate, holding its per-component multiplicities). The spec
--  makes no behavioural claim about that machinery and holds for EVERY candidate
--  list, so there is nothing to validate against a real callee — hence no G-AX.
--  See mapping.md §3 / refinement.md §C.)
-- axioms-end

-- pure-start
/- The total degree of one candidate: the sum of its per-component
   multiplicities. For a candidate whose components count how many times each
   generator occurs, this is the documented size measure — the quantity the
   public contract compares against the lower bound
   (`min_degree <= total_degree(...) <= max_degree`). -/
def totalDegree (p : List Nat) : Nat := p.sum

/- Retain, in their original order, exactly the candidates whose total degree
   is at least the supplied lower bound `minDeg`. Front-recursive (one unfold
   per element) so a single drop-step is available to the backward loop below
   (the Velvet fold pattern, plan §5.4). -/
def selectByDegree (minDeg : Nat) : List (List Nat) → List (List Nat)
  | []      => []
  | p :: ps => (if minDeg ≤ totalDegree p then [p] else []) ++ selectByDegree minDeg ps

@[grind] lemma selectByDegree_nil (minDeg : Nat) : selectByDegree minDeg [] = [] := rfl
@[grind] lemma selectByDegree_cons (minDeg : Nat) (p : List Nat) (ps : List (List Nat)) :
    selectByDegree minDeg (p :: ps)
      = (if minDeg ≤ totalDegree p then [p] else []) ++ selectByDegree minDeg ps := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- From a list of enumerated candidates (each given by its per-component
   multiplicities) and a lower bound `minDeg`, keep exactly those candidates
   whose total degree is at least `minDeg`, preserving their enumeration order.
   `candidates` and `minDeg` are read-only (not `mut`): the scan threads a fresh
   accumulator and never mutates anything it is handed (directive 5). -/
method selectMonomials (candidates : List (List Nat)) (minDeg : Nat) return (out : List (List Nat))
  ensures out = selectByDegree minDeg candidates
  do
    -- impl-start
    -- Pre-image skeleton: the per-candidate threshold compares the LARGEST single
    -- component multiplicity (`List.foldr max 0`) against the lower bound, NOT the
    -- total degree (the sum). The frozen spec requires selectByDegree (which uses
    -- the sum), so prove_correct MUST fail on any candidate whose largest single
    -- multiplicity is below the bound while its total degree meets it.
    let mut result : List (List Nat) := []
    let mut i := candidates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ candidates.length
      invariant result = selectByDegree minDeg (candidates.drop i)
      done_with i = 0
      decreasing i
    do
      let p := candidates[i - 1]!
      let largest := p.foldr Nat.max 0
      result := (if minDeg ≤ largest then [p] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the candidate at
   `i-1` on the front, so `selectByDegree` peels one decision. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selectByDegree_drop_step (minDeg : Nat) (candidates : List (List Nat)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ candidates.length) :
    selectByDegree minDeg (candidates.drop (i - 1))
      = (if minDeg ≤ totalDegree candidates[i - 1]! then [candidates[i - 1]!] else [])
        ++ selectByDegree minDeg (candidates.drop i) := by
  have hlt : i - 1 < candidates.length := by omega
  have hcons : candidates.drop (i - 1) = candidates[i - 1]! :: candidates.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectByDegree_cons]

prove_correct selectMonomials by
  loom_solve
  rw [selectByDegree_drop_step minDeg candidates i (by omega) (by omega)]
  simp_all
