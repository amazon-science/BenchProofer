import Mathlib
-- imports-end

/-!
Wrapping a transformer's output into a tabular ("DataFrame") container.

When a transformer produces output that downstream code wants as a labelled
table, the output is wrapped into a container with column labels and a row index.
The wrapping reads three things: the produced data, an optional set of column
labels, and an optional caller-supplied row index.

The wrapping rule is:

  * if the data cannot be represented as a dense table (a sparse payload), the
    request is rejected with an error;
  * if the data is ALREADY a table, it is returned as that same table — its
    column labels replaced by the supplied labels when those are given, but its
    OWN row index always kept (a caller-supplied row index does not apply
    to data that already carries its own index);
  * otherwise a fresh table is built from the data, using the supplied column
    labels when given (else positional labels) and the supplied row index when
    given (else a positional `0,1,2,…` index).

In particular, when the data is already a table, the resulting container keeps
the data's own row index regardless of any caller-supplied index — so a
transformer that re-labels its rows (e.g. by aggregating) is not silently forced
back onto the caller's index.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The wrapping
-- rule is modeled structurally over the observable parts of the inputs (the
-- data's runtime category, its own column/index/payload when it is already a
-- table, the optional supplied column labels, the optional supplied row index),
-- so no `opaque`/`axiom` callee contract is needed. (`check_pandas_support`
-- merely makes the table library available and has no effect on the produced
-- value; it is not modeled.)
-- axioms-end

-- pure-start
/-- A tabular container, projected to the three parts the wrapping observes:
`cols` (column labels, in order), `idx` (row index labels, in order), and `data`
(the cell payload, one inner list per row). -/
structure DataFrame where
  cols : List String
  idx : List Int
  data : List (List Int)
deriving DecidableEq, Repr

/-- The data to wrap, by runtime category:
* `sparse` — a sparse payload that cannot be densely tabulated;
* `dataframe df` — data that is already a table `df`;
* `ndarray values` — a plain dense array-like payload (rows of cells). -/
inductive InputData where
  | sparse
  | dataframe (df : DataFrame)
  | ndarray (values : List (List Int))
deriving Repr

/-- Positional column labels `"0","1",…` for a fresh table built from `values`
(one label per column of the first row). -/
def ndColumns (values : List (List Int)) : List String :=
  (List.range (values.headD []).length).map (fun i => toString i)

/-- Positional row index `0,1,…` for a fresh table built from `values` (one entry
per row). -/
def ndIndex (values : List (List Int)) : List Int :=
  (List.range values.length).map (fun i => (i : Int))

/-- The container produced by the wrapping rule. -/
def containerResult (input : InputData) (columns : Option (List String))
    (index : Option (List Int)) : Except String DataFrame :=
  match input with
  | .sparse => Except.error "Pandas output does not support sparse data."
  | .dataframe df =>
      -- already a table: replace columns when supplied; keep the table's own
      -- row index (the supplied index does not apply).
      let cols := match columns with | some c => c | none => df.cols
      Except.ok { df with cols := cols }
  | .ndarray values =>
      let cols := match columns with | some c => c | none => ndColumns values
      let idx := match index with | some i => i | none => ndIndex values
      Except.ok { cols := cols, idx := idx, data := values }
-- pure-end

-- post-conditions-start
/-- The produced container is exactly the one the wrapping rule selects. When the
input is already a table, its own row index is preserved (the caller-supplied
`index` is not applied); only its column labels may change. -/
def problem_spec_buildOutputContainer
    (input : InputData) (columns : Option (List String)) (index : Option (List Int))
    (result : Except String DataFrame) : Prop :=
  result = containerResult input columns index
-- post-conditions-end

-- impl-start
def implementation_buildOutputContainer
    (input : InputData) (columns : Option (List String)) (index : Option (List Int)) :
    Except String DataFrame := Id.run do
  match input with
  | .sparse =>
      return Except.error "Pandas output does not support sparse data."
  | .dataframe df =>
      let mut out := df
      if let some c := columns then
        out := { out with cols := c }
      return Except.ok out
  | .ndarray values =>
      let cols := match columns with | some c => c | none => ndColumns values
      let idx := match index with | some i => i | none => ndIndex values
      return Except.ok { cols := cols, idx := idx, data := values }
-- impl-end

-- proof-start
theorem correct_buildOutputContainer :
    ∀ (input : InputData) (columns : Option (List String)) (index : Option (List Int)),
      problem_spec_buildOutputContainer input columns index
        (implementation_buildOutputContainer input columns index) := by
  intro input columns index
  unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
  cases input with
  | sparse => rfl
  | dataframe df =>
      cases columns with
      | none => rfl
      | some c => rfl
  | ndarray values => rfl
-- proof-end
