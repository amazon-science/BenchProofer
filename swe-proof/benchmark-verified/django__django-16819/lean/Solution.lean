import Mathlib
-- imports-end

/-!
Optimizing a migration plan: cancelling an add-index against a later
remove-index.

A migration plan is optimized by repeatedly asking each operation whether it can
be *reduced* against the operation that follows it. The reduction either returns
a concrete list of operations that should replace the pair, or a sentinel
meaning "these two cannot be optimized across each other".

This bundle models the reduction decision for an *add-index* operation. An
add-index operation carries the name of the index it creates. The desired
behavior is:

  * when the following operation is a remove-index operation that targets an
    index with the SAME name, the add and the remove annihilate, so the pair is
    replaced by NO operations (the empty list); otherwise

  * the reduction falls back to the generic operation-reduction behavior shared
    by all operations (which decides, from the two operations alone, whether one
    may be optimized across the other).

Only the first bullet is specific to add-index; the fallback is the unchanged
shared behavior, modeled here as an opaque reference (its result is whatever the
generic reducer yields for the same two operations).
-/

-- axioms-start
/-- A migration operation, modeled by the attributes the add-index reduction
observes about it: whether it is a remove-index operation, the index name it
targets (meaningful only for a remove-index), and whether it is elidable (the
only attribute the generic fallback reducer inspects about the other operation).
-/
structure OpArg where
  /-- Whether this operation removes an index. -/
  isRemoveIndex : Bool
  /-- The index name this operation targets (used only when `isRemoveIndex`). -/
  name : String
  /-- Whether this operation may be elided (consumed only by the generic
  fallback reducer). -/
  elidable : Bool
deriving DecidableEq, Repr

/-- The outcome of a reduction: either a concrete list of operations that should
replace the pair, or the sentinel meaning the two operations cannot be optimized
across each other. The empty list is a genuine outcome distinct from the
sentinel — it means the pair annihilates. -/
inductive ReduceResult where
  /-- Replace the pair by this concrete list of operations. -/
  | replace (ops : List OpArg)
  /-- The two operations cannot be optimized across each other. -/
  | cannot
deriving DecidableEq, Repr

instance : Inhabited ReduceResult := ⟨.cannot⟩

/-- The generic, shared reduction behavior used by every operation (the
fallback). It decides, from the add-index operation's own index name, the other
operation, and the application label, what the reduction yields when the
add-index–specific cancellation does not apply. It is referenced opaquely: the
specification does not pin its value, only that the fallback defers to it. -/
opaque baseReduce (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled decision is a single
-- guard over the observed attributes of the two operations.
-- pure-end

-- post-conditions-start
/-- The reduction of an add-index operation (whose created index is named
`selfName`) against a following operation `op` under application label
`appLabel`. The result is fully determined: if `op` removes an index of the same
name, the pair annihilates to the empty replacement list; otherwise the result
is exactly the generic fallback reduction for the same two operations. No
component of the result is left unconstrained. -/
def problem_spec_reduceAddIndex
    (selfName : String) (op : OpArg) (appLabel : String) (result : ReduceResult) : Prop :=
  result =
    (if op.isRemoveIndex && selfName == op.name then
        ReduceResult.replace []
      else
        baseReduce selfName op appLabel)
-- post-conditions-end

-- impl-start
def implementation_reduceAddIndex
    (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
  if op.isRemoveIndex && selfName == op.name then
    return ReduceResult.replace []
  return baseReduce selfName op appLabel
-- impl-end

-- proof-start
theorem correct_reduceAddIndex :
    ∀ (selfName : String) (op : OpArg) (appLabel : String),
      problem_spec_reduceAddIndex selfName op appLabel
        (implementation_reduceAddIndex selfName op appLabel) := by
  intro selfName op appLabel
  unfold problem_spec_reduceAddIndex implementation_reduceAddIndex
  by_cases h : op.isRemoveIndex && selfName == op.name <;>
    simp only [h, Id.run, bind, if_true, pure]
-- proof-end
