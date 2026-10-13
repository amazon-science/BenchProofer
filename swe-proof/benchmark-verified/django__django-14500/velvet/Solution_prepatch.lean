import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A migration's identity for recording purposes. Only the fields the recording
   step observes are modeled: the application label and migration name form the
   migration's own key, and `replaces` is the list of older migration keys a
   squashed migration stands in for (empty for an ordinary migration). -/
structure Migration where
  replaces : List (String × String)
  appLabel : String
  name     : String

/- Backward-scan step: dropping one fewer element of a list exposes the element
   at that index on the front. The single rewrite each loop iteration needs. -/
lemma drop_step {α : Type} [Inhabited α] (xs : List α) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
  have hlt : i - 1 < xs.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The keys recorded as unapplied when reversing a migration: every key the
   migration replaces, in order, followed by the migration's own key. For an
   ordinary migration (no replaced keys) this is just its own key. -/
method recordUnappliedKeys (m : Migration)
    return (out : List (String × String))
  ensures out = m.replaces ++ [(m.appLabel, m.name)]
  do
    -- impl-start
    -- Pre-image skeleton: when the migration stands in for replaced keys, only
    -- those replaced keys are recorded and the migration's own key is recorded
    -- ONLY in the complementary branch (no replaced keys). The frozen spec
    -- requires the own key to follow the replaced keys in every case, so
    -- prove_correct MUST fail on a migration with a non-empty replaced set.
    let mut result : List (String × String) := []
    let e : List (String × String) :=
      if m.replaces = [] then [(m.appLabel, m.name)] else []
    result := e
    let mut i := m.replaces.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ m.replaces.length
      invariant result = m.replaces.drop i ++ e
      done_with i = 0
      decreasing i
    do
      let k := m.replaces[i - 1]!
      result := k :: result
      i := i - 1
    return result
    -- impl-end

prove_correct recordUnappliedKeys by
  loom_solve
  rw [drop_step m.replaces i (by omega) (by omega)]
  simp_all
