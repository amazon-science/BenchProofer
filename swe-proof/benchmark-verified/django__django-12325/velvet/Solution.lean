import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure data-flow that scans a record's own one-to-one identity references and
   keeps, per referenced target, only those references explicitly marked as the
   record's identity link. Every observable is computed from the read-only input
   list `refs`; nothing is borrowed from a foreign oracle. There is therefore no
   consumed axiom and no deep-model reference (mapping.md §3). -/
-- axioms-end

-- pure-start
/- One one-to-one identity reference a record declares to an ancestor. `target`
   is the identity of the referenced ancestor (distinct ancestors get distinct
   `target`s); `isLink` flags whether this reference is explicitly declared to be
   the record's identity link to that ancestor; `fid` is the reference's own
   identity, so two references to the same ancestor remain distinguishable. -/
structure Ref where
  target : Nat
  isLink : Bool
  fid : Nat
deriving DecidableEq, Inhabited, Repr

/- A per-target selection of identity links: for each ancestor identity, the
   reference (if any) chosen as the record's identity link to that ancestor.
   `none` means no identity link to that ancestor has been selected. -/
abbrev LinkMap := Nat → Option Ref

/- Fold one reference into the selection. A reference that is NOT an explicit
   identity link is ignored — it must never be selected as an identity link. An
   explicit identity link is recorded under its target ancestor, overwriting any
   link already held for that same target (later declarations win, the
   last-writer-wins map semantics). -/
def selectRef (m : LinkMap) (f : Ref) : LinkMap :=
  if f.isLink then (fun k => if k = f.target then some f else m k) else m

/- The selection after scanning the whole reference list left to right. -/
def collectLinks (refs : List Ref) : LinkMap :=
  refs.foldl selectRef (fun _ => none)

/- The key structural fact, generalized over an arbitrary starting selection so
   it folds by induction: anything the scan selects under key `k` is either an
   explicit identity link that targets exactly `k` and is one of the references
   scanned, or it was already present in the starting selection. -/
lemma foldl_selectRef_props (refs : List Ref) (m : LinkMap) :
    ∀ k g, refs.foldl selectRef m k = some g →
      (g.isLink = true ∧ g.target = k ∧ g ∈ refs) ∨ m k = some g := by
  induction refs generalizing m with
  | nil => intro k g h; right; simpa using h
  | cons hd tl ih =>
    intro k g h
    rw [List.foldl_cons] at h
    rcases ih (selectRef m hd) k g h with hL | hR
    · exact Or.inl ⟨hL.1, hL.2.1, by simp [hL.2.2]⟩
    · unfold selectRef at hR
      by_cases hf : hd.isLink
      · simp only [hf, if_true] at hR
        by_cases hk : k = hd.target
        · simp only [hk, if_true] at hR
          have hg := Option.some_inj.mp hR
          subst hg
          exact Or.inl ⟨hf, hk.symm, by simp⟩
        · simp only [hk, if_false] at hR
          exact Or.inr hR
      · simp only [hf] at hR
        exact Or.inr hR

/- The whole-list selection: any selected entry is an explicit identity link,
   targets exactly its key, and is one of the declared references. This is the
   property that pins the behavior — a selected reference is necessarily one the
   record declared as its identity link, so no non-link reference can hijack the
   identity-link slot for an ancestor. -/
lemma collectLinks_props (refs : List Ref) :
    ∀ k g, collectLinks refs k = some g →
      g.isLink = true ∧ g.target = k ∧ g ∈ refs := by
  intro k g h
  rcases foldl_selectRef_props refs (fun _ => none) k g h with hL | hR
  · exact hL
  · simp at hR

/- Forward-fold step: extending the consumed prefix by one reference folds that
   reference into the selection built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the Velvet forward-fold pattern). -/
lemma collectLinks_take_step (refs : List Ref) (i : Nat) (hi : i < refs.length) :
    (refs.take (i + 1)).foldl selectRef (fun _ => none)
      = selectRef ((refs.take i).foldl selectRef (fun _ => none)) refs[i]! := by
  have hcons : refs.take (i + 1) = refs.take i ++ [refs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select, per ancestor, the record's identity link among its declared one-to-one
   references. Scanning the references in declaration order, a reference is chosen
   as the identity link to its target ancestor ONLY when it is explicitly marked
   as such; a plain one-to-one reference to an ancestor must NOT be treated as an
   identity link, so that declaring such a reference (in any order, alongside or
   without an explicit identity link) never misidentifies the record's identity
   link. The post-state pins the selection to the input references: any selected
   entry is one of the declared references, it is an explicit identity link, and
   it is filed under exactly the ancestor it references.

   `refs` is read-only: the method builds and returns a fresh selection and never
   mutates its input. -/
method collectParentLinks (refs : List Ref) return (out : LinkMap)
  ensures ∀ k, out k = collectLinks refs k
  ensures ∀ k g, out k = some g → g.isLink = true
  ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs
  do
    -- impl-start
    let mut result : LinkMap := (fun _ => none)
    let mut i := 0
    while i < refs.length
      invariant i ≤ refs.length
      invariant result = (refs.take i).foldl selectRef (fun _ => none)
      done_with i = refs.length
      decreasing refs.length - i
    do
      let f := refs[i]!
      result := selectRef result f
      i := i + 1
    return result
    -- impl-end

prove_correct collectParentLinks by
  loom_solve
  case «invariant_2: result = (refs.take i).foldl selectRef (fun _ => none)» =>
    have hi : i < refs.length := by omega
    rw [invariant_2, collectLinks_take_step refs i hi]
  case «ensures_2: ∀ k g, out k = some g → g.isLink = true» =>
    intro k g h
    cases i_2
    have hlen : i = refs.length := by omega
    rw [invariant_2, hlen, List.take_length] at h
    exact (collectLinks_props refs k g h).1
  case «ensures_1: ∀ k g, out k = some g → g.target = k ∧ g ∈ refs» =>
    intro k g h
    cases i_2
    have hlen : i = refs.length := by omega
    rw [invariant_2, hlen, List.take_length] at h
    exact (collectLinks_props refs k g h).2
  all_goals simp_all [collectLinks]
