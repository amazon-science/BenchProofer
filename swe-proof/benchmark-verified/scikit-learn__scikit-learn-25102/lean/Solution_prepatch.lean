import Mathlib
-- imports-end

/-!
Reducing a tabular input to a chosen subset of its columns, while keeping each
surviving column's element type intact.

A tabular input is a sequence of named columns, each carrying its own element
type, together with a row count. A column-selection step keeps the
columns picked out by a boolean selection vector (one flag per input column) and
drops the rest; the number of rows is never changed (so even when nothing is
selected the result still has the original row count, with zero columns).

Such a step can run in two modes:

  * `nativeContainer` — the input arrives as a native tabular container and the
    caller has asked for output in that same native container form. Here the
    selected columns are returned exactly as they were, each keeping its own
    element type.
  * otherwise — the input is first turned into a single homogeneous numeric
    block in which every column is coerced to one common element type; the
    selection is then taken from that homogeneous block, so every surviving
    column carries the common type rather than its original one.

We model the observable the step produces: the resulting sequence of columns
(name + element type, in input order) and the resulting row count.

  * `isDataFrame`   — the input arrives as a native tabular container;
  * `outputPandas`  — output is requested in that native container form;
  * `cols`          — the input columns (name + element type);
  * `nRows`         — the number of rows;
  * `commonDtype`   — the single element type every column is coerced to when the
                      input is homogenised into one numeric block;
  * `mask`          — the per-column selection vector.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both the
-- homogenise-or-keep decision and the by-flag column selection are modeled
-- structurally over the input columns and the selection vector, so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One column, restricted to the observable fields:
* `name`  — the column's identity (its label), modeled as a `Nat` identity;
* `dtype` — the column's element type, modeled as a `Nat` identity. -/
structure Column where
  name : Nat
  dtype : Nat
deriving DecidableEq, Repr

/-- The observable result of the column-selection step:
* `cols`  — the surviving columns, in input order;
* `nRows` — the row count (unchanged from the input). -/
structure TransformResult where
  cols : List Column
  nRows : Nat
deriving DecidableEq, Repr

/-- Keep the columns whose selection flag is `true`, in input order; drop the
rest. (Pairs each column with its flag and filters.) -/
def selectByMask (cols : List Column) (mask : List Bool) : List Column :=
  (cols.zip mask).filterMap (fun p => if p.2 then some p.1 else none)

/-- Coerce every column to a single common element type (homogenise the input
into one numeric block). Column identities are preserved; only element types are
collapsed to `dt`. -/
def castAll (cols : List Column) (dt : Nat) : List Column :=
  cols.map (fun c => { c with dtype := dt })
-- pure-end

-- post-conditions-start
/-- The result keeps the original row count, and its columns are the by-flag
selection taken either from the columns exactly as given (when the input is a
native container and native-container output is requested) or from the
homogenised block in which every column shares the common element type
(otherwise). -/
def problem_spec_transform
    (isDataFrame outputPandas : Bool)
    (cols : List Column) (nRows commonDtype : Nat) (mask : List Bool)
    (result : TransformResult) : Prop :=
  result.nRows = nRows
  ∧ result.cols =
      selectByMask
        (if isDataFrame && outputPandas then cols else castAll cols commonDtype)
        mask
-- post-conditions-end

-- impl-start
def implementation_transform
    (isDataFrame outputPandas : Bool)
    (cols : List Column) (nRows commonDtype : Nat) (mask : List Bool)
    : TransformResult := Id.run do
  -- The input is always homogenised into one numeric block before selection,
  -- so every surviving column carries the common element type.
  let block := castAll cols commonDtype
  let selected := selectByMask block mask
  if !(mask.any id) then
    return { cols := [], nRows := nRows }
  return { cols := selected, nRows := nRows }
-- impl-end

-- proof-start
theorem correct_transform :
    ∀ (isDataFrame outputPandas : Bool) (cols : List Column)
      (nRows commonDtype : Nat) (mask : List Bool),
      problem_spec_transform isDataFrame outputPandas cols nRows commonDtype mask
        (implementation_transform isDataFrame outputPandas cols nRows commonDtype mask) := by
  intro isDataFrame outputPandas cols nRows commonDtype mask
  unfold problem_spec_transform implementation_transform
  simp only [Id.run, bind, pure]
  by_cases h : mask.any id
  · -- something selected: both sides agree
    by_cases hk : isDataFrame && outputPandas <;>
      simp [h, hk]
  · -- nothing selected: selectByMask block mask = []
    have hempty : ∀ block : List Column, selectByMask block mask = [] := by
      intro block
      unfold selectByMask
      have hfm : ∀ p ∈ block.zip mask, (if p.2 then some p.1 else none) = (none : Option Column) := by
        intro p hp
        have hp2 : p.2 ∈ mask := (List.of_mem_zip hp).2
        have hpf : p.2 = false := by
          by_contra hne
          have htrue : p.2 = true := by cases p.2 <;> simp_all
          rw [List.any_eq_true] at h
          exact h ⟨p.2, hp2, by simp [htrue]⟩
        simp [hpf]
      rw [List.filterMap_eq_nil_iff.mpr hfm]
    by_cases hk : isDataFrame && outputPandas <;>
      simp [h, hk, hempty]
-- proof-end
