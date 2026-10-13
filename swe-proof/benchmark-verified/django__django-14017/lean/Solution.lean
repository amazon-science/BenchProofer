import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is consumed by the modeled behavior. The decision the
-- modeled procedure makes (whether an operand may be merged, and which branch is
-- taken) is determined entirely by observable attributes of the two operands,
-- which are carried as fields of the input carriers below and modeled deeply.
-- Hence there is no `opaque` callee and no consumed `_prop` axiom.
-- axioms-end

-- pure-start
/-- A logical connector used to merge two filter conditions. -/
inductive Connector
  | and_
  | or_
  deriving DecidableEq, Repr

/-- The left-hand operand: a filter node. The only behaviourally relevant
attribute here is whether it is *empty* (carries no sub-conditions). -/
structure FilterNode where
  /-- `true` iff this filter node carries no sub-conditions. -/
  empty : Bool
  deriving DecidableEq, Repr

/-- The right-hand operand of a merge. Three observable attributes drive the
behaviour:
* `isFilter` — whether the operand is itself a filter node;
* `boolValued` — whether the operand is a standalone boolean-valued condition
  (i.e. usable on its own as a filter), exactly the property the merge inspects;
* `empty` — whether the operand is itself trivial (carries no content), which is
  observed uniformly for any accepted operand. -/
structure Operand where
  isFilter : Bool
  boolValued : Bool
  empty : Bool
  deriving DecidableEq, Repr

/-- Outcome of attempting to merge the left filter node with the operand under a
connector. -/
inductive MergeResult
  | /-- the operand is not a valid thing to merge: the merge is rejected. -/
    rejected
  | /-- the operand contributes nothing: the result is (a copy of) the left node. -/
    keepLeft
  | /-- the left node contributes nothing: the result is (a copy of) the operand. -/
    keepRight
  | /-- a fresh combined node is built, joining both operands under `conn`. -/
    merged (conn : Connector)
  deriving DecidableEq, Repr

/-- The mergeability test: an operand may be merged iff it is itself a filter
node, or it is a standalone boolean-valued condition. -/
def mergeable (other : Operand) : Bool :=
  other.isFilter || other.boolValued
-- pure-end

-- post-conditions-start
/-- Merging the left filter node `self` with `other` under connector `conn`:
* if `other` is neither a filter node nor a standalone boolean condition, the
  merge is rejected;
* otherwise the outcome is fully determined: an empty operand contributes
  nothing (the left node is kept), failing that an empty left node contributes
  nothing (the operand is kept), and otherwise a fresh node merging both under
  `conn` is produced. -/
def problem_spec_mergeFilters
    (self : FilterNode) (other : Operand) (conn : Connector)
    (result : MergeResult) : Prop :=
  (mergeable other = false ↔ result = MergeResult.rejected)
  ∧ (mergeable other = true →
      result =
        (if other.empty then MergeResult.keepLeft
         else if self.empty then MergeResult.keepRight
         else MergeResult.merged conn))
-- post-conditions-end

-- impl-start
def implementation_mergeFilters
    (self : FilterNode) (other : Operand) (conn : Connector) : MergeResult := Id.run do
  if !(other.isFilter || other.boolValued) then
    return MergeResult.rejected
  if other.empty then
    return MergeResult.keepLeft
  if self.empty then
    return MergeResult.keepRight
  return MergeResult.merged conn
-- impl-end

-- proof-start
theorem correct_mergeFilters :
    ∀ (self : FilterNode) (other : Operand) (conn : Connector),
      problem_spec_mergeFilters self other conn
        (implementation_mergeFilters self other conn) := by
  intro self other conn
  unfold problem_spec_mergeFilters implementation_mergeFilters mergeable
  obtain ⟨se⟩ := self
  obtain ⟨of, ob, oe⟩ := other
  cases conn <;> cases se <;> cases of <;> cases ob <;> cases oe <;> decide
-- proof-end
