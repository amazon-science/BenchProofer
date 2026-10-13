import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The fallback routing policy's chosen target is taken
--  as a free input alias `routed`: the operation under spec does NOT determine
--  how that policy decides, and an explicit named target supersedes it whenever
--  one is given. Its only relied-on property — the policy may name a store
--  different from the explicit one — is validated against the real routing
--  machinery by axiom_check.py (G-AX), an A-reference, not a consumed contract.)
-- axioms-end

-- pure-start
/- Two store handles denote the same data store iff their code-point sequences
   are equal. A store handle is carried as its `List Char` of code points; this
   is the alias equality the resolution must respect. -/
def aliasEq (a b : List Char) : Prop := a = b
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A persistence step is handed two things: an explicitly named target data
   store (a handle that is always present here) and the handle a separate,
   independent write-routing policy would otherwise pick. The write must land in
   the EXPLICITLY NAMED store, so the resolved target equals the named handle no
   matter which store the routing policy would have chosen. The routing policy
   is only a fallback, reached when no explicit store is named at all.

   `db` is the explicitly named target handle and is always present (non-empty);
   `routed` is the handle the routing policy would otherwise pick — an arbitrary
   present handle, unconstrained to equal `db`. Both are read-only (neither is
   `mut`; the resolution mutates nothing — directive 5). The result is a freshly
   built handle whose code points equal the explicitly named store's, so a
   resolution cannot satisfy the postcondition by echoing `routed`. -/
method resolveTarget (db : List Char) (routed : List Char) return (out : List Char)
  require db.length > 0
  require routed.length > 0
  ensures aliasEq out db
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: NO explicit handle is supplied to the write,
    -- so the resolution always falls through to the routing-policy fallback and
    -- the target is `routed` rather than the explicitly named store. The frozen
    -- spec requires the result to equal `db` for an arbitrary `routed`, so
    -- prove_correct MUST fail.
    let src : List Char := routed
    let mut result : List Char := []
    let mut i := src.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ src.length
      invariant result = src.drop i
      done_with i = 0
      decreasing i
    do
      let c := src[i - 1]!
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-copy step: dropping one fewer element exposes the element at
   `i-1` on the front, so the suffix peels one code point. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma drop_copy_step (src : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ src.length) :
    src.drop (i - 1) = src[i - 1]! :: src.drop i := by
  have hlt : i - 1 < src.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct resolveTarget by
  loom_solve
  · simp only [require_2, if_true] at *
    rw [drop_copy_step routed i (by omega) (by omega), invariant_2]
  · simp only [require_2, if_true, aliasEq] at *
    simp_all
