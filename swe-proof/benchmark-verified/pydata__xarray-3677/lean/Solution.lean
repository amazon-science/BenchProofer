import Mathlib
-- imports-end

/-!
Merging a second argument into a dataset.

The second argument may itself already be a dataset, or it may be a single
named array. The desired outcome is stated abstractly as an input→output
relation, in two stages:

* READING the second argument as a dataset. A dataset is used unchanged, and
  this always succeeds. A single named array is read as its equivalent
  one-variable dataset — a reading that is itself PARTIAL: an array the
  one-variable-dataset reading does not apply to raises, and that raised error
  is the whole outcome of the operation, with no merge attempted.
* MERGING, when and only when the reading succeeded: the result is *exactly*
  what the underlying dataset-to-dataset merge produces for the first dataset
  and the dataset just read — the merged dataset, or the error that merge
  raises.

The result carries no freedom beyond that composition: it is fully determined by
the two operands, and both stages' error channels are propagated verbatim, error
payload included.

The behavior is stated as a logical predicate; the implementation and its
correctness proof are supplied separately.
-/

-- axioms-start
-- The unchanged dependency callees this operation uses, declared here only by
-- signature (`opaque`) — the contract is stated directly over them and
-- discharged by case analysis on the shape of the second argument, so no
-- property axiom about either callee is consumed.

/-- An error this operation raises, carrying an opaque reason. Either stage can
raise one: reading the second argument as a dataset, or the merge itself. -/
structure OpErr where
  reason : String
deriving DecidableEq, Repr, Inhabited

/-- A dataset value. -/
opaque DatasetRep : NonemptyType.{0}
def Dataset : Type := DatasetRep.type
instance : Nonempty Dataset := DatasetRep.property

/-- A single (named) array value. -/
opaque DataArrayRep : NonemptyType.{0}
def DataArray : Type := DataArrayRep.type
instance : Nonempty DataArray := DataArrayRep.property

/-- Reading a single named array as its equivalent one-variable dataset — the
canonical interpretation of an array as a dataset of exactly one variable. A
PARTIAL reading: it yields that dataset, or the error it raises on an array the
reading does not apply to. -/
opaque datasetOfArray : DataArray → Except OpErr Dataset

/-- The underlying dataset-to-dataset merge: given two datasets it yields the
merged dataset, or the error the merge raises when they conflict or cannot be
combined. -/
opaque mergeDatasets : Dataset → Dataset → Except OpErr Dataset
-- axioms-end

-- pure-start
/-- The second operand of the merge: either a dataset or a single named array. -/
inductive MergeOther where
  | ds : Dataset → MergeOther
  | da : DataArray → MergeOther

/-- Read the second operand as a dataset: a dataset is used unchanged and always
succeeds; a single named array is read as its equivalent one-variable dataset,
which may instead raise. -/
def asDataset : MergeOther → Except OpErr Dataset
  | .ds d => Except.ok d
  | .da a => datasetOfArray a
-- pure-end

-- post-conditions-start
/-- The merge method's contract: read the second operand as a dataset, and if
that raises, that error IS the result and no merge happens; otherwise the result
is *exactly* the underlying dataset-to-dataset merge of the first dataset with
the dataset just read — value or error, propagated verbatim. -/
def problem_spec_merge (self : Dataset) (other : MergeOther)
    (result : Except OpErr Dataset) : Prop :=
  result = (asDataset other).bind (mergeDatasets self)
-- post-conditions-end

-- impl-start
noncomputable def implementation_merge (self : Dataset) (other : MergeOther) :
    Except OpErr Dataset := Id.run do
  -- Read the second operand as a dataset: a single named array is read as its
  -- equivalent one-variable dataset (a reading that may raise); a dataset is
  -- used unchanged.
  let read : Except OpErr Dataset :=
    match other with
    | .ds d => Except.ok d
    | .da a => datasetOfArray a
  -- Delegate to the underlying dataset-to-dataset merge only where the reading
  -- succeeded; a reading error is the whole outcome.
  return read.bind (mergeDatasets self)
-- impl-end

-- proof-start
theorem correct_merge :
    ∀ (self : Dataset) (other : MergeOther),
      problem_spec_merge self other (implementation_merge self other) := by
  intro self other
  unfold problem_spec_merge implementation_merge asDataset
  cases other <;> rfl
-- proof-end
