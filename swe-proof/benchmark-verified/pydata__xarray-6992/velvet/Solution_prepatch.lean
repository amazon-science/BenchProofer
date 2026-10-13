import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- This bundle models the name-set bookkeeping of the operation that removes one
   (multi-)index from a labelled-array container and recomputes the container's
   variable / coordinate / index name-sets. A labelled-array container carries
   three name-sets that must obey one structural invariant: every coordinate
   name is also a variable name (`coords ⊆ vars`). The modeled operation must
   keep that invariant intact for every input. The carrier is `List String`
   (names are opaque string identifiers); the index being removed is described
   abstractly by its dimension name `dim`, whether it is a multi-level index,
   and (for a multi-level index) its level coordinate names `levels`. The full
   coordinate footprint of the index is `{dim} ∪ levels` — the property an
   unchanged neighbouring helper supplies (validated in axiom_check.py / G-AX).
   Duplicate-freeness of the carriers is irrelevant to the name-sets, so plain
   `List String` with membership/`filter` semantics is the faithful model. -/

-- axioms-start
-- (No consumed axioms. The operation under change is modeled DEEPLY as concrete
--  list bookkeeping over `List String`, spelled out in the `pure` region; no
--  library callee's `ensures` is consumed by the proof. The single UNCHANGED
--  neighbouring callee the model relies on — the index-footprint helper that
--  reports a (multi-)index's full coordinate set as `{dim} ∪ levels` — is an
--  A-reference, validated == its real counterpart by axiom_check.py (G-AX). The
--  changed bookkeeping itself (including the single-level-reduction renaming of a
--  kept level coordinate to the dimension name) is part of this deep model and is
--  refuted against the real operation by conformance_check.py (G-CONF), not an
--  axiom.)
-- axioms-end

-- pure-start
/- Remove from a name list, in order, every name that occurs in `drop`. Empty
   `drop` removes nothing. Front-recursive so a single unfold is available. -/
def filterOut (drop : List String) : List String → List String
  | []      => []
  | x :: xs => (if drop.contains x then [] else [x]) ++ filterOut drop xs

@[grind] lemma filterOut_nil (d : List String) : filterOut d [] = [] := rfl
@[grind] lemma filterOut_cons (d : List String) (x : String) (xs : List String) :
    filterOut d (x :: xs) = (if d.contains x then [] else [x]) ++ filterOut d xs := rfl

/- Membership characterisation: a name survives `filterOut` iff it was present
   and is not among the dropped names. -/
lemma mem_filterOut (d : List String) (xs : List String) (k : String) :
    k ∈ filterOut d xs ↔ (k ∈ xs ∧ d.contains k = false) := by
  induction xs with
  | nil => simp [filterOut]
  | cons x xs ih =>
    rw [filterOut_cons]
    by_cases hc : d.contains x = true
    · rw [if_pos hc]; simp only [List.nil_append, ih, List.mem_cons]
      constructor
      · rintro ⟨hmem, hcon⟩; exact ⟨Or.inr hmem, hcon⟩
      · rintro ⟨h, hcon⟩; rcases h with h | h
        · subst h; rw [hc] at hcon; exact absurd hcon (by simp)
        · exact ⟨h, hcon⟩
    · rw [if_neg hc]; simp only [List.singleton_append, List.mem_cons, ih]
      simp only [Bool.not_eq_true] at hc
      constructor
      · rintro (h | ⟨hmem, hcon⟩)
        · subst h; exact ⟨Or.inl rfl, hc⟩
        · exact ⟨Or.inr hmem, hcon⟩
      · rintro ⟨h, hcon⟩; rcases h with h | h
        · exact Or.inl h
        · exact Or.inr ⟨h, hcon⟩

/- The three recomputed name-sets of the container after the index is removed. -/
structure NameSets where
  vars : List String
  coords : List String
  idxs : List String
deriving DecidableEq

/- The recomputed (variables, coordinate-names, index-keys) after removing the
   index whose dimension is `dim`. `R` is the set of requested names to reset.
   `V`/`C` are the prior variable / coordinate name-sets. `dropF` selects "drop"
   (discard the de-indexed coordinates) versus "convert" (retain them as plain
   variables). Written as one nested-if mirroring the operation's control flow:

   * non-multi index: its single coordinate `dim` is dropped (`dropF`) or
     retained as a plain variable (else); no index remains.
   * multi-level index, with at least one kept level and the dimension itself
     not requested: the index is rebuilt on the kept levels.
       - exactly one kept level: it reduces to a single index whose coordinate
         is renamed to `dim`; the old kept-level name is removed; the reset
         levels are dropped/converted.
       - more than one kept level: the multi-index is rebuilt on the kept levels
         (names unchanged) and the reset levels are dropped/converted.
   * multi-level index otherwise (dimension requested, or no level kept): the
     whole index goes; the dimension variable is always removed and the levels
     are dropped/converted.

   In every branch the SAME drop-set `dv` is subtracted from BOTH `V` and `C`,
   which is exactly what keeps `coords ⊆ vars` intact (see `subsetPreserved`). -/
def computeNameSets (isMulti : Bool) (dim : String) (levels R V C : List String)
    (dropF : Bool) : NameSets :=
  let mk := fun (dv nv ni : List String) =>
    ({ vars := filterOut dv V ++ nv, coords := filterOut dv C, idxs := ni } : NameSets)
  if isMulti then
    let keepLevels := levels.filter (fun k => !R.contains k)
    if (!R.contains dim) && !keepLevels.isEmpty then
      let resetLevels := levels.filter (fun k => R.contains k)
      if keepLevels.length == 1 then
        if dropF then mk (keepLevels ++ resetLevels) [dim] [dim]
                 else mk keepLevels ([dim] ++ resetLevels) [dim]
      else
        if dropF then mk resetLevels keepLevels (keepLevels ++ [dim])
                 else mk [] (keepLevels ++ resetLevels) (keepLevels ++ [dim])
    else
      if dropF then mk (dim :: levels) [] []
               else mk [dim] levels []
  else
    if dropF then mk [dim] [] []
             else mk [] [dim] []

/- The structural guarantee the operation must preserve: if every coordinate
   name was a variable name beforehand (`coords ⊆ vars`), then every recomputed
   coordinate name is a recomputed variable name. This is the invariant whose
   violation by a defective bookkeeping makes a downstream length computation
   negative; the deep model restores it for ALL inputs. Proved once, branch by
   branch, from `mem_filterOut` and the fact that the same drop-set is removed
   from both name-sets. -/
theorem subsetPreserved (isMulti : Bool) (dim : String) (levels R V C : List String)
    (dropF : Bool) (hCV : ∀ k, k ∈ C → k ∈ V) :
    ∀ k, k ∈ (computeNameSets isMulti dim levels R V C dropF).coords →
         k ∈ (computeNameSets isMulti dim levels R V C dropF).vars := by
  have key : ∀ (dv nv : List String) (k : String),
      k ∈ filterOut dv C → k ∈ filterOut dv V ++ nv := by
    intro dv nv k hk
    rw [mem_filterOut] at hk
    apply List.mem_append_left
    rw [mem_filterOut]
    exact ⟨hCV k hk.1, hk.2⟩
  simp only [computeNameSets]
  split_ifs <;> intro k hk <;> exact key _ _ _ hk
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Recompute the variable / coordinate / index name-sets of the container after
   removing the index on dimension `dim`. The result must equal the name-set
   bookkeeping `computeNameSets` describes — in particular every dropped name is
   subtracted from BOTH the variable set and the coordinate set, so that the
   structural invariant `coords ⊆ vars` is preserved (`subsetPreserved`).

   All inputs (`isMulti`, `dim`, `levels`, `R`, `V`, `C`, `dropF`) are read-only
   descriptions of the prior state and the request; the operation builds fresh
   name-sets and mutates none of them (directive 5). -/
method dropIndexNameSets (isMulti : Bool) (dim : String) (levels : List String)
    (R : List String) (V : List String) (C : List String) (dropF : Bool)
    return (out : NameSets)
  ensures out = computeNameSets isMulti dim levels R V C dropF
  do
    -- impl-start
    -- Pre-patch (buggy) skeleton: the de-indexed coordinate names are NOT
    -- subtracted from the coordinate set (`coord2 := C ++ newVars`, never
    -- shrinking), only the explicitly-requested names are removed from the
    -- variable set when dropping, and a reduced single level keeps its own
    -- name (no rename to the dimension). This is the skeleton that lets the
    -- coordinate set outgrow the variable set.
    let mut dropVars : List String := []
    let mut newVars : List String := []
    let mut newIdx : List String := []
    if isMulti then
      let keepLevels := levels.filter (fun k => !R.contains k)
      let resetLevels := levels.filter (fun k => R.contains k)
      if (!resetLevels.isEmpty) && !keepLevels.isEmpty then
        newVars := keepLevels
        newIdx := keepLevels
      else
        newIdx := []
    else
      newIdx := []
    if dropF then
      dropVars := R
    else
      dropVars := []
    let variables2 := filterOut dropVars V ++ newVars
    let coord2 := C ++ newVars
    return { vars := variables2, coords := coord2, idxs := newIdx }
    -- impl-end

prove_correct dropIndexNameSets by
  loom_solve <;> simp_all [computeNameSets]
