import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constraint that narrows the candidate collection
--  is applied via a presence check on each candidate's matching-witness count;
--  the collection-building primitive it relies on is modeled DEEPLY as the
--  per-candidate selection below, not consumed as an outside contract. There is
--  no `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One candidate item considered for inclusion in a constrained collection. It
   carries only the two fields the operation observes: a stable identity `id`
   and `witnesses` — the number of distinct ways this item satisfies the
   constraint (e.g. how many related records make it eligible). A candidate is
   *eligible* exactly when it has at least one witness. -/
structure Candidate where
  id : Int
  witnesses : Nat
deriving Inhabited, DecidableEq

/- The per-candidate contribution to the constrained collection: an eligible
   candidate contributes its identity ONCE; an ineligible one contributes
   nothing. The contribution does NOT depend on HOW MANY witnesses an eligible
   candidate has — one is enough, and more do not multiply it. -/
def keep (c : Candidate) : List Int :=
  if c.witnesses > 0 then [c.id] else []

/- The constrained collection over a whole candidate sequence: concatenate the
   per-candidate contributions, in order. Front-recursive so a single unfold is
   available per loop step (the backward-fold pattern). Because each eligible
   candidate contributes exactly one identity, the result lists every eligible
   identity once — never duplicated by a candidate's witness multiplicity. -/
def keepMatching : List Candidate → List Int
  | []      => []
  | c :: cs => keep c ++ keepMatching cs

@[grind] lemma keepMatching_nil : keepMatching [] = [] := rfl
@[grind] lemma keepMatching_cons (c : Candidate) (cs : List Candidate) :
    keepMatching (c :: cs) = keep c ++ keepMatching cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectEligible (rows : List Candidate) return (out : List Int)
  ensures out = keepMatching rows
  do
    -- impl-start
    -- Pre-image skeleton: the constrained collection is built by an inner-join
    -- expansion — each candidate is emitted ONCE PER witness (`List.replicate
    -- c.witnesses c.id`), so a candidate with several witnesses appears several
    -- times. The frozen spec requires `keepMatching` (each eligible candidate
    -- ONCE), so prove_correct MUST fail on any candidate with witnesses ≥ 2.
    let mut result : List Int := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      done_with i = 0
      decreasing i
    do
      let c := rows[i - 1]!
      result := List.replicate c.witnesses c.id ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the candidate at
   `i-1` on the front, so `keepMatching` peels one `keep`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keepMatching_drop_step (rows : List Candidate) (i : Nat)
    (hi : 0 < i) (hle : i ≤ rows.length) :
    keepMatching (rows.drop (i - 1)) = keep rows[i - 1]! ++ keepMatching (rows.drop i) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepMatching_cons]

prove_correct selectEligible by
  loom_solve
  rw [keepMatching_drop_step rows i (by omega) (by omega)]
  simp_all
