import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The producer of candidate relations is an
--  unchanged enumerator whose only relevant effect is the SEQUENCE of
--  (table, column) relations it yields; that sequence is the read-only input
--  `relations` here. The combining transformation under spec is modeled DEEPLY
--  below — every observable is computed from `relations`, nothing is borrowed
--  from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- One candidate relation feeding the fast-delete pass: a target table (`fst`)
   paired with the single column (`snd`) on that table that references the rows
   being deleted. Tables and columns are carried by stable integer identities. -/
abbrev Relation := Int × Int

/- One combined fast-delete group: a target table (`fst`) paired with the list
   of columns (`snd`) on that table to be matched, in first-encounter order. A
   single group is emitted as ONE query of the shape "delete the rows of this
   table where any of these columns matches". -/
abbrev TableGroup := Int × List Int

/- Insertion-ordered grouping: record that column `f` of table `m` must be
   matched.
   - a table never seen before is appended at the end, keeping the order in
     which tables were first encountered, carrying just `[f]`;
   - a table already present keeps its original position and APPENDS `f` to its
     column list (so all columns of one table accumulate into one group).
   This is the exact semantics of `groups[m].append(f)` on an order-preserving
   table→columns mapping then reading it back in table order. -/
def combineInto (gs : List TableGroup) (m : Int) (f : Int) : List TableGroup :=
  match gs with
  | []            => [(m, [f])]
  | (m', fs') :: r => if m' = m then (m, fs' ++ [f]) :: r else (m', fs') :: combineInto r m f

/- Fold one relation into the accumulating grouping. -/
def combineStep (gs : List TableGroup) (e : Relation) : List TableGroup := combineInto gs e.1 e.2

/- The combined fast-delete plan built from a whole sequence of candidate
   relations: each relation is grouped under its table; the plan is that mapping
   read out in table order. Net effect: every distinct table appears EXACTLY
   ONCE (one combined query per table), in first-encounter order, carrying every
   column that referenced it — so N relations on the same table collapse to a
   single group instead of N separate ones. -/
def combined (relations : List Relation) : List TableGroup := relations.foldl combineStep []

/- Tables of a grouping step: an already-present table leaves the table list
   unchanged; a fresh table is appended. (The column accumulation does not touch
   the key projection.) -/
@[grind] lemma keys_combineInto (gs : List TableGroup) (m f : Int) :
    (combineInto gs m f).map Prod.fst
      = if m ∈ gs.map Prod.fst then gs.map Prod.fst else gs.map Prod.fst ++ [m] := by
  induction gs with
  | nil => simp [combineInto]
  | cons hd tl ih =>
    obtain ⟨m', fs'⟩ := hd
    by_cases hmm : m' = m
    · subst hmm; simp [combineInto]
    · simp only [combineInto, hmm, if_false, List.map_cons]
      by_cases hmem : m ∈ tl.map Prod.fst
      · simp [ih, hmem, List.mem_cons, Ne.symm hmm]
      · have : m ∉ (m', fs').1 :: tl.map Prod.fst := by
          simp [List.mem_cons, Ne.symm hmm, hmem]
        simp [ih, hmem, List.mem_cons, Ne.symm hmm]

/- Grouping preserves table-uniqueness. -/
@[grind] lemma nodup_combineInto (gs : List TableGroup) (m f : Int)
    (h : (gs.map Prod.fst).Nodup) : ((combineInto gs m f).map Prod.fst).Nodup := by
  rw [keys_combineInto]
  by_cases hmem : m ∈ gs.map Prod.fst
  · simp [hmem, h]
  · simp only [hmem, if_false]
    exact h.append (by simp) (by simp [hmem])

/- The accumulator's tables stay unique through any fold, starting from any
   table-unique seed. -/
lemma nodup_foldl (relations : List Relation) :
    ∀ gs, (gs.map Prod.fst).Nodup → ((relations.foldl combineStep gs).map Prod.fst).Nodup := by
  induction relations with
  | nil => intro gs h; simpa using h
  | cons e es ih =>
    intro gs h
    exact ih (combineStep gs e) (by simpa [combineStep] using nodup_combineInto gs e.1 e.2 h)

/- The plan never lists a table twice: each target table is queried with a single
   combined query, regardless of how many candidate relations reference it. -/
@[grind] lemma combined_nodup (relations : List Relation) :
    ((combined relations).map Prod.fst).Nodup :=
  nodup_foldl relations [] (by simp)

/- Forward-fold step: extending the consumed prefix by one relation groups that
   relation into the plan built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body. -/
lemma combined_take_step (relations : List Relation) (i : Nat) (hi : i < relations.length) :
    (relations.take (i + 1)).foldl combineStep []
      = combineStep ((relations.take i).foldl combineStep []) relations[i]! := by
  have hcons : relations.take (i + 1) = relations.take i ++ [relations[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the combined fast-delete plan from the full sequence of candidate
   `relations`.
   The result is exactly the order-preserving group-by-table collapse of the
   sequence: every distinct table appears once (no table is queried twice), in
   first-encounter order, carrying every referencing column. `relations` is
   read-only (not `mut`): the loop builds a fresh result and never mutates its
   input. -/
method combineByTable (relations : List Relation) return (out : List TableGroup)
  ensures out = combined relations
  ensures (out.map Prod.fst).Nodup
  do
    -- impl-start
    -- Pre-image skeleton: every candidate relation is emitted as its OWN group
    -- as it is seen (a raw append per relation), with NO grouping by table. Two
    -- relations on the same table therefore yield two separate groups, so the
    -- result is the raw relation sequence (each as a singleton-column group) —
    -- not `combined relations` — and its tables are not unique. prove_correct
    -- MUST fail (both `ensures` clauses).
    let mut result : List TableGroup := []
    let mut i := 0
    while i < relations.length
      invariant i ≤ relations.length
      invariant result = (relations.take i).map (fun e => (e.1, [e.2]))
      done_with i = relations.length
      decreasing relations.length - i
    do
      let e := relations[i]!
      result := result ++ [(e.1, [e.2])]
      i := i + 1
    return result
    -- impl-end

prove_correct combineByTable by
  -- Honest attempt with the SAME tactic shape as Solution.lean. It cannot close:
  -- the raw per-relation emission satisfies neither `out = combined relations`
  -- (the grouped collapse) nor `(out.map Prod.fst).Nodup` once any table is
  -- referenced twice, so `loom_solve` is left with unsolvable goals (G-DIFF).
  loom_solve
  case «invariant_2: result = (relations.take i).map (fun e => (e.1, [e.2]))» =>
    have hi : i < relations.length := by omega
    rw [invariant_2, List.take_succ, List.map_append, List.getElem?_eq_getElem hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  -- The discriminating clause `ensures_2: out = combined relations` is left
  -- UNSOLVED here: the raw singleton-group list differs from the table-grouped
  -- collapse on any input referencing one table twice. This honest attempt
  -- cannot close it, so `prove_correct` fails and G-DIFF (exit ≠ 0) holds.
  all_goals
    simp_all [combined]
