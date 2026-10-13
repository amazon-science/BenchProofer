import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- This bundle models the coordinate-name bookkeeping of the reshaping operation
   that splits a labelled-array dimension into a pair of new dimensions. A
   labelled-array container carries a set of variable names, some of which are
   distinguished as coordinate names. The reshaping rebuilds every variable under
   the new dimension layout and then re-selects which of the rebuilt names are
   coordinates. The behaviour under specification is exactly that re-selection:
   which names end up as coordinates afterwards.

   The desired guarantee is that the coordinate-name set is invariant across the
   reshaping — every name that was a coordinate beforehand is still a coordinate
   afterwards, and no new name becomes one. Names are opaque string identifiers,
   so the faithful carrier is `List String` with membership semantics; duplicate
   structure is irrelevant because only the resulting set of names is observed.
   `requestedDims` are the names of the dimensions being reshaped and `coordNames`
   the prior coordinate names. -/

-- axioms-start
-- (No consumed axioms. The re-selection is concrete set bookkeeping over
--  `List String`, spelled out in the `pure`/`impl` regions. The one neighbouring
--  callee the operation relies on — the routine that installs a chosen name-set
--  as the container's coordinates on an otherwise coordinate-free rebuild — is an
--  UNCHANGED identity on names (the resulting coordinate names equal the chosen
--  set), validated end-to-end by conformance_check.py (G-CONF) against the real
--  callee, not consumed as an axiom. Hence no library callee's `ensures` is used
--  by the proof.)
-- axioms-end

-- pure-start
/- The chosen coordinate name-set for the rebuilt container: the names common to
   the reshaped dimensions and the prior coordinates, together with all the prior
   coordinate names. Written front-recursively via `filter`/`++` so a single
   unfold is available; only membership in the result is observed. -/
def keptCoordNames (requestedDims coordNames : List String) : List String :=
  requestedDims.filter (fun k => coordNames.contains k) ++ coordNames

/- Membership characterisation: a name is among the chosen coordinates iff it was
   a prior coordinate. The common-names component is a subset of the prior
   coordinates, so unioning it back in changes nothing — the chosen set is exactly
   the prior coordinate-name set. This is the structural fact that makes the
   coordinate-name set invariant across the reshaping. -/
@[grind] lemma mem_keptCoordNames (requestedDims coordNames : List String) (k : String) :
    k ∈ keptCoordNames requestedDims coordNames ↔ k ∈ coordNames := by
  simp only [keptCoordNames, List.mem_append, List.mem_filter,
             List.contains_eq_mem, decide_eq_true_eq]
  constructor
  · rintro (⟨_, h⟩ | h) <;> exact h
  · intro h; exact Or.inr h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Re-select the coordinate names of the rebuilt container. The result must be
   exactly the prior coordinate-name set (membership-wise): every name that was a
   coordinate before is one after, and no other name is introduced. Both inputs
   describe the prior state and the request and are read-only — the operation
   builds a fresh name-set and mutates neither (directive 5). -/
method coordsToKeep (requestedDims : List String) (coordNames : List String)
    return (out : List String)
  ensures ∀ k, (k ∈ out) ↔ (k ∈ coordNames)
  do
    -- impl-start
    let common := requestedDims.filter (fun k => coordNames.contains k)
    let result := common ++ coordNames
    return result
    -- impl-end

prove_correct coordsToKeep by
  loom_solve
