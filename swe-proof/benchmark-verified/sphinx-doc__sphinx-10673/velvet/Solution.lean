import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model references. The decision modeled here is
-- pure list/membership logic over FREE INPUTS: the sequence of table-of-contents
-- entry names requested in a document, the set of document names that have a
-- backing source file, and the set of reference targets the project provides
-- automatically (the index / module-index / search pages). The directive only
-- READS these collections to decide which entries name a targetExists target; it
-- never reshapes the collections themselves, so there is no callee contract to
-- assume and nothing for G-AX.
-- axioms-end

-- pure-start
/- Whether a requested entry names a targetExists target: it does when the name
   belongs to the documents that have a backing source file, OR to the reference
   targets the project provides automatically (the index, module-index and
   search pages). The two collections are read-only carriers of membership. -/
def targetExists (sourceDocs autoTargets : List String) (name : String) : Bool :=
  sourceDocs.contains name || autoTargets.contains name

@[grind] lemma targetExists_def (sourceDocs autoTargets : List String) (name : String) :
    targetExists sourceDocs autoTargets name
      = (sourceDocs.contains name || autoTargets.contains name) := rfl

/- The entries retained for the table of contents: every requested entry that
   names a targetExists target, in request order. Written front-recursively (one
   structural unfold exposed per element) so the backward `while` fold below
   discharges with a single drop-step rewrite. An entry that is absent is
   omitted (the directive emits a diagnostic for it; only the retained sequence
   is observed here). -/
def retainedEntries (sourceDocs autoTargets : List String) :
    List String → List String
  | []          => []
  | e :: rest =>
    (if targetExists sourceDocs autoTargets e then [e] else [])
      ++ retainedEntries sourceDocs autoTargets rest

@[grind] lemma retainedEntries_nil (sourceDocs autoTargets : List String) :
    retainedEntries sourceDocs autoTargets [] = [] := rfl

@[grind] lemma retainedEntries_cons
    (sourceDocs autoTargets : List String) (e : String) (rest : List String) :
    retainedEntries sourceDocs autoTargets (e :: rest)
      = (if targetExists sourceDocs autoTargets e then [e] else [])
          ++ retainedEntries sourceDocs autoTargets rest := rfl

/- Characterisation: an entry is retained exactly when it was requested AND it
   exists. Gives the membership postconditions to `loom_solve`/`grind`. -/
@[grind] lemma mem_retainedEntries
    (sourceDocs autoTargets : List String) (requested : List String) (e : String) :
    e ∈ retainedEntries sourceDocs autoTargets requested
      ↔ e ∈ requested ∧ targetExists sourceDocs autoTargets e = true := by
  induction requested with
  | nil => simp [retainedEntries]
  | cons h t ih =>
    rw [retainedEntries_cons]
    by_cases hp : targetExists sourceDocs autoTargets h = true
    · rw [if_pos hp, List.singleton_append, List.mem_cons, List.mem_cons, ih]
      constructor
      · rintro (rfl | ⟨hmem, hr⟩)
        · exact ⟨Or.inl rfl, hp⟩
        · exact ⟨Or.inr hmem, hr⟩
      · rintro ⟨rfl | hmem, hr⟩
        · exact Or.inl rfl
        · exact Or.inr ⟨hmem, hr⟩
    · rw [if_neg hp, List.nil_append, List.mem_cons, ih]
      constructor
      · rintro ⟨hmem, hr⟩
        exact ⟨Or.inr hmem, hr⟩
      · rintro ⟨rfl | hmem, hr⟩
        · exact absurd hr hp
        · exact ⟨hmem, hr⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the table-of-contents entries to retain for a document. A requested
   entry is retained when it names a target that exists — one with a backing
   source file, OR one of the reference targets the project provides
   automatically (the index, module-index and search pages). Entries that do not
   exist are omitted (a diagnostic is emitted for them; only the retained
   sequence is observed). The three input collections are read-only. -/
method selectToctreeEntries
    (requested : List String) (sourceDocs : List String) (autoTargets : List String)
    return (out : List String)
  ensures out = retainedEntries sourceDocs autoTargets requested
  ensures ∀ e, e ∈ out → e ∈ requested ∧ targetExists sourceDocs autoTargets e = true
  ensures ∀ e, e ∈ requested → autoTargets.contains e = true → e ∈ out
  ensures ∀ e, e ∈ requested → targetExists sourceDocs autoTargets e = true → e ∈ out
  do
    -- impl-start
    let mut out : List String := []
    let mut i := requested.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ requested.length
      invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
      done_with i = 0
      decreasing i
    do
      let e := requested[i - 1]!
      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
      i := i - 1
    return out
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `retainedEntries` peels one contribution. The single
   goal `loom_solve` leaves for the loop body. -/
lemma retainedEntries_drop_step
    (sourceDocs autoTargets requested : List String) (i : Nat)
    (hi : 0 < i) (hle : i ≤ requested.length) :
    retainedEntries sourceDocs autoTargets (requested.drop (i - 1))
      = (if targetExists sourceDocs autoTargets requested[i - 1]!
          then [requested[i - 1]!] else [])
        ++ retainedEntries sourceDocs autoTargets (requested.drop i) := by
  have hlt : i - 1 < requested.length := by omega
  have hcons : requested.drop (i - 1) = requested[i - 1]! :: requested.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, retainedEntries_cons]

prove_correct selectToctreeEntries by
  loom_solve
  rw [retainedEntries_drop_step sourceDocs autoTargets requested i (by omega) (by omega)]
  simp_all
