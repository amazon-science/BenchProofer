import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Both modeled operations are unchanged library callees
-- modeled DEEPLY as concrete data transforms (A-reference), validated
-- == the real callee by axiom_check.py (G-AX); see mapping.md §3.
-- axioms-end

-- pure-start
/- The "released" image of a registry of resource-handles: every handle in the
   sequence is left in the released (inactive) state, regardless of its prior
   state. Front-recursive so a single unfold is available per loop step (the
   backward-fold pattern). A handle is modeled by a `Bool` recording whether it
   is currently active. -/
def releasedSeq : List Bool → List Bool
  | []      => []
  | _ :: cs => false :: releasedSeq cs

@[grind] lemma releasedSeq_nil : releasedSeq [] = [] := rfl
@[grind] lemma releasedSeq_cons (b : Bool) (cs : List Bool) :
    releasedSeq (b :: cs) = false :: releasedSeq cs := rfl

/- After releasing, every entry is inactive. -/
@[grind] lemma releasedSeq_all_false (cs : List Bool) :
    ∀ b ∈ releasedSeq cs, b = false := by
  induction cs with
  | nil => simp [releasedSeq]
  | cons c cs ih =>
      intro b hb
      simp [releasedSeq_cons] at hb
      rcases hb with h | h
      · exact h
      · exact ih b h

@[grind] lemma releasedSeq_length (cs : List Bool) :
    (releasedSeq cs).length = cs.length := by
  induction cs with
  | nil => rfl
  | cons c cs ih => simp [releasedSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Install a set of preferred bindings over an existing keyed registry.

   `registry` is a keyed collection (alias ↦ handle id), modeled as an
   association list with first-match lookup. `preferred` is the set of bindings
   that must take precedence: after installation, every alias present in
   `preferred` resolves to the preferred handle, and aliases absent from
   `preferred` keep their prior binding. Modeled as prepending the preferred
   bindings, so first-match lookup yields preferred precedence (mapping.md §2).

   This is the behavior an isolated worker needs: it must operate against the
   handles handed to it, not against freshly-created handles for the same
   aliases. -/
method installPreferred
    (preferred : List (String × Int)) (registry : List (String × Int))
    return (out : List (String × Int))
  ensures out = preferred ++ registry
  ensures out.length = preferred.length + registry.length
  ensures ∀ p, p ∈ preferred → p ∈ out
  do
    -- impl-start
    -- Pre-image skeleton: the worker does NOT install the preferred bindings;
    -- it operates against the registry as-is. The frozen spec requires the
    -- preferred bindings to take precedence (out = preferred ++ registry), so
    -- prove_correct MUST fail whenever `preferred` is non-empty.
    let result : List (String × Int) := registry
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the binding at
   `i-1` on the front, and `++` distributes through the resulting cons. The one
   goal `loom_solve` leaves for the loop body. -/
lemma overlay_drop_step (preferred registry : List (String × Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ preferred.length) :
    preferred.drop (i - 1) ++ registry
      = preferred[i - 1]! :: (preferred.drop i ++ registry) := by
  have hlt : i - 1 < preferred.length := by omega
  have hcons : preferred.drop (i - 1) = preferred[i - 1]! :: preferred.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, List.cons_append]

prove_correct installPreferred by
  loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Release every resource-handle held by a worker before it is recycled. The
   handles are modeled by their active/inactive flags; after this operation no
   handle remains active, so a later teardown observes no still-held resources.
   This is the per-handle release the worker must perform at the end of each
   unit of work (mapping.md §2). -/
method releaseAll (handles : List Bool) return (out : List Bool)
  ensures out = releasedSeq handles
  ensures out.length = handles.length
  ensures ∀ b ∈ out, b = false
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := handles.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ handles.length
      invariant result = releasedSeq (handles.drop i)
      done_with i = 0
      decreasing i
    do
      result := false :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for release: dropping one fewer element exposes one
   more handle on the front, and `releasedSeq` peels one inactive entry (the
   prior state of that handle is irrelevant). -/
lemma released_drop_step (handles : List Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ handles.length) :
    releasedSeq (handles.drop (i - 1)) = false :: releasedSeq (handles.drop i) := by
  have hlt : i - 1 < handles.length := by omega
  have hcons : handles.drop (i - 1) = handles[i - 1]! :: handles.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, releasedSeq_cons]

prove_correct releaseAll by
  loom_solve
  rw [released_drop_step handles i (by omega) (by omega)]
  simp_all
