import Mathlib
-- imports-end

/-!
Collecting the scale factor and dimension of a function application.

A physical expression carries a scale factor together with a dimension. When the
expression is a function applied to one or more arguments, each argument has
already been reduced to its own scale factor and dimension. The combined result
reports:

  * a scale factor equal to the function applied to the arguments' scale factors;
  * for each argument, a dimension equal to the unit dimension `Dimension(1)`
    whenever the dimension system regards that argument's dimension as
    dimensionless, and equal to the argument's dimension otherwise.

The canonicalisation of every dimensionless argument dimension to the single unit
dimension is what lets a later same-dimension comparison recognise two
dimensionless quantities as compatible, even when their dimensions are written in
different but equivalent symbolic forms.
-/

-- axioms-start
-- Two UNCHANGED outside operations are used identically by the specification and
-- the implementation, so each is carried as an opaque callee and NO property of
-- either is consumed (G-AX skips):
--
--   * `isDimensionless` — the dimension system's query deciding whether a
--     dimension reduces to no net dimension. Modelled as an opaque predicate; its
--     internal dependency resolution is out of scope here.
--   * `applyFunc` — rebuilding the function applied to the arguments' scale
--     factors. Unchanged by the modelled behavior; carried opaquely so the scale
--     factor component is pinned to its inputs.
--
-- The argument scale/dimension pairs `fds` are themselves produced by the
-- (unchanged) recursive collection and are carried as grounded inputs, not
-- axiomatised.
abbrev Dim := Nat
abbrev Factor := Nat
abbrev Func := Nat
opaque dimOne : Dim
opaque isDimensionless : Dim → Bool
opaque applyFunc : Func → List Factor → Factor
-- axioms-end

-- pure-start
/-- The collected result of a function application: the rebuilt scale factor and
the per-argument list of (canonicalised) dimensions. -/
structure FunctionResult where
  factor : Factor
  dims : List Dim
deriving DecidableEq, Repr

/-- Canonicalise a single argument's dimension: report the unit dimension when
the dimension system regards it as dimensionless, otherwise report it unchanged. -/
def canonDim (d : Dim) : Dim :=
  if isDimensionless d then dimOne else d
-- pure-end

-- post-conditions-start
/-- The result of collecting a function application: the scale factor is the
function applied to the arguments' scale factors, and the dimension list is the
element-wise canonicalisation of the arguments' dimensions (each dimensionless
dimension reported as the unit dimension, every other dimension unchanged). -/
def problem_spec_collectFunction
    (func : Func) (fds : List (Factor × Dim)) (result : FunctionResult) : Prop :=
  result.factor = applyFunc func (fds.map Prod.fst) ∧
  result.dims = fds.map (fun fd => canonDim fd.2)
-- post-conditions-end

-- impl-start
def implementation_collectFunction
    (func : Func) (fds : List (Factor × Dim)) : FunctionResult := Id.run do
  let mut dims : List Dim := []
  for fd in fds do
    if isDimensionless fd.2 then
      dims := dims ++ [dimOne]
    else
      dims := dims ++ [fd.2]
  return { factor := applyFunc func (fds.map Prod.fst), dims := dims }
-- impl-end

-- proof-start
theorem correct_collectFunction :
    ∀ (func : Func) (fds : List (Factor × Dim)),
      problem_spec_collectFunction func fds
        (implementation_collectFunction func fds) := by
  have helper : ∀ (fds : List (Factor × Dim)) (init : List Dim),
      Id.run (forIn fds init (fun (fd : Factor × Dim) r =>
        (if isDimensionless fd.2 = true then do
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [dimOne]))
          else do
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))
        = init ++ fds.map (fun fd => canonDim fd.2) := by
    intro fds
    induction fds with
    | nil => intro init; simp only [List.forIn_nil, Id.run, pure, List.map_nil, List.append_nil]
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind, canonDim] at ih ⊢
      by_cases h : isDimensionless a.2 = true <;>
        simp [h, ih, List.append_assoc]
  intro func fds
  unfold problem_spec_collectFunction implementation_collectFunction
  refine ⟨rfl, ?_⟩
  show (Id.run (forIn fds ([] : List Dim) (fun (fd : Factor × Dim) r =>
        (if isDimensionless fd.2 = true then do
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [dimOne]))
          else do
            pure PUnit.unit
            pure (ForInStep.yield (r ++ [fd.2]))) : Id _))) = _
  rw [helper]
  simp
-- proof-end
