import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model reference of an outside callee. The
--  operation modeled here — taking an ordered slice of each independent group of
--  related rows — is spelled out directly by `groupSlice`/`slicedGroups` over
--  the already-ordered groups. The machinery that resolves the ordering of each
--  group is unchanged and shared by both the old and new behaviour, so the
--  resolved order enters as an abstracted input (the already-ordered `groups`),
--  not as a consumed contract. See mapping.md §3. -/
-- axioms-end

-- pure-start
/- A requested slice is a half-open range of positions: a start offset `low`
   (number of leading rows to skip) and an optional stop `high` (`none` means
   "to the end"). Positions are 0-based. -/

/- The slice of ONE ordered group: skip the first `low` rows, then keep up to
   the stop. With an open-ended stop, keep everything after the offset; with a
   concrete stop `h`, keep the rows whose position is in `[low, h)`. This is the
   per-group analogue of an ordinary sequence slice `g[low:high]`. -/
def groupSlice (low : Nat) (high : Option Nat) (g : List Int) : List Int :=
  match high with
  | none   => g.drop low
  | some h => (g.drop low).take (h - low)

/- The result over many independent groups: each group is sliced ON ITS OWN
   (the offset/stop are measured from the start of that group, not across the
   combined sequence), and the per-group slices are concatenated in group order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def slicedGroups (low : Nat) (high : Option Nat) : List (List Int) → List Int
  | []      => []
  | g :: gs => groupSlice low high g ++ slicedGroups low high gs

@[grind] lemma slicedGroups_nil (low : Nat) (high : Option Nat) :
    slicedGroups low high [] = [] := rfl
@[grind] lemma slicedGroups_cons (low : Nat) (high : Option Nat)
    (g : List Int) (gs : List (List Int)) :
    slicedGroups low high (g :: gs) = groupSlice low high g ++ slicedGroups low high gs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method perGroupSlice (groups : List (List Int)) (low : Nat) (high : Option Nat)
    return (out : List Int)
  ensures out = slicedGroups low high groups
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := groups.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ groups.length
      invariant result = slicedGroups low high (groups.drop i)
      done_with i = 0
      decreasing i
    do
      let g := groups[i - 1]!
      result := groupSlice low high g ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer group exposes the group at `i-1`
   on the front, so `slicedGroups` peels one `groupSlice`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma slicedGroups_drop_step (low : Nat) (high : Option Nat)
    (groups : List (List Int)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ groups.length) :
    slicedGroups low high (groups.drop (i - 1))
      = groupSlice low high groups[i - 1]! ++ slicedGroups low high (groups.drop i) := by
  have hlt : i - 1 < groups.length := by omega
  have hcons : groups.drop (i - 1) = groups[i - 1]! :: groups.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, slicedGroups_cons]

prove_correct perGroupSlice by
  loom_solve
  rw [slicedGroups_drop_step low high groups i (by omega) (by omega)]
  simp_all
