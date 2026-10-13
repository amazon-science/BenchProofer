import Mathlib
-- imports-end

/-!
Removing a batch of collected records and reporting how many were removed.

The records to remove are organized into groups (one group per kind of record);
each record carries a single observable field: its primary-key identity, which is
either present (the record currently lives in the store under that key) or absent
(the record has no key, i.e. it does not correspond to any stored row).

Removal has TWO observable outcomes:

  * a count of how many rows were removed, and
  * a side effect on every removed record: once a record has been removed, it no
    longer corresponds to any stored row, so its primary-key identity must be
    cleared (made absent). This must hold for EVERY removed record, in every
    group — there is no record that is removed yet keeps a stale key.

There is a fast path for the smallest possible job — a single group holding a
single record that has no dependents and so can be removed by one direct
operation — and a general path for everything else. The reported count differs
between the two paths (each path tallies removals its own way), but the
key-clearing outcome is identical: after removal, no removed record retains a
key.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Whether the smallest job
-- qualifies for the direct single-record removal is an unchanged decision left
-- as the universally-quantified predicate `directlyDeletable` (the spec holds
-- for every such predicate). The two removal tallies are likewise the unchanged
-- counting machinery, taken as the parameters `directCount` / `generalTotal`.
-- The key-clearing side effect (the modeled behavior) is spelled out structurally
-- by `clearAllPks`, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A removed record, restricted to its single touched field: the primary-key
identity, `some v` when a key value `v` is present and `none` when absent. -/
structure Instance where
  pk : Option Int
deriving DecidableEq

/-- A group label (one per kind of record). Identity only; never compared. -/
abbrev Label := Nat

/-- One group: a label paired with the list of records collected under it. -/
abbrev RecGroup := Label × List Instance

/-- Clear the primary-key identity of every record in every group: each removed
record's key is made absent, every group's label and shape preserved. -/
def clearAllPks (data : List RecGroup) : List RecGroup :=
  data.map (fun g => (g.1, g.2.map (fun i => { i with pk := none })))

/-- Whether the job is the smallest possible one eligible for the direct
single-record removal: exactly one group holding exactly one record, and that
record qualifies for direct removal. -/
def isSingleFast (data : List RecGroup) (directlyDeletable : Instance → Bool) : Bool :=
  match data with
  | [(_, [inst])] => directlyDeletable inst
  | _ => false
-- pure-end

-- post-conditions-start
/-- The outcome is fully pinned to the inputs:

  * the record groups are exactly the input groups with every record's key
    cleared (`clearAllPks data`) — identical whether the fast path or the general
    path was taken, so no removed record keeps a key; and
  * the reported count is the direct tally on the fast path and the general tally
    otherwise.

No output component is left free: the group structure is pinned to
`clearAllPks data`, and the count is pinned to the branch-selected tally. -/
def problem_spec_delete
    (data : List RecGroup) (directlyDeletable : Instance → Bool)
    (directCount generalTotal : Int)
    (result : (List RecGroup) × Int) : Prop :=
  result.1 = clearAllPks data ∧
  result.2 = (if isSingleFast data directlyDeletable then directCount else generalTotal)
-- post-conditions-end

-- impl-start
def implementation_delete
    (data : List RecGroup) (directlyDeletable : Instance → Bool)
    (directCount generalTotal : Int) : (List RecGroup) × Int := Id.run do
  -- Optimize for the case with a single collected record and no dependents.
  match data with
  | [(label, [inst])] =>
    if directlyDeletable inst then
      -- Remove the one record directly, clear its now-stale key, and return early.
      return ([(label, [{ inst with pk := none }])], directCount)
  | _ => pure ()
  -- General path: after removal, clear every collected record's key.
  return (clearAllPks data, generalTotal)
-- impl-end

-- proof-start
theorem correct_delete :
    ∀ (data : List RecGroup) (directlyDeletable : Instance → Bool)
      (directCount generalTotal : Int),
      problem_spec_delete data directlyDeletable directCount generalTotal
        (implementation_delete data directlyDeletable directCount generalTotal) := by
  intro data directlyDeletable directCount generalTotal
  unfold implementation_delete problem_spec_delete isSingleFast
  match data with
  | [(label, [inst])] =>
    by_cases h : directlyDeletable inst <;> simp [clearAllPks, h]
  | [] => simp [clearAllPks]
  | (label, []) :: rest => simp [clearAllPks]
  | (label, inst1 :: inst2 :: more) :: rest => simp [clearAllPks]
  | g1 :: g2 :: rest => simp [clearAllPks]
-- proof-end
