import Mathlib
-- imports-end

/-!
Validating that a freshly combined N-dimensional object has monotonic global
indexes.

When several datasets are merged into one by aligning them along their shared
coordinates, some dimensions are *combined across* the inputs (their coordinate
values differ between datasets, so the inputs are stacked along them) while other
coordinate dimensions are mere *bystanders* — identical in every input, and so
carried through unchanged rather than concatenated.

After the combine, the result is checked: along every dimension that was combined
across the inputs, the resulting global index must be monotonic (either
increasing or decreasing throughout); otherwise the combine is rejected with an
error naming the offending dimension.

A bystander coordinate dimension — one that does not vary between the inputs — is
NOT subjected to this requirement: its values are taken verbatim from the inputs
and may legitimately be in any order, so it must never cause the combine to be
rejected. Only dimensions actually combined across the inputs are validated.

The check scans the dimensions in order and reports the FIRST combined dimension
whose global index fails to be monotonic; if every combined dimension is
monotonic, the combine succeeds. The result is success, or the name of that first
offending dimension.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a given
-- dimension's global index is monotonic, and whether that dimension was combined
-- across the inputs, are upstream observations carried as plain data on each
-- dimension record; the decision the specification pins — which dimensions are
-- subjected to the monotonicity requirement, and which offending one is reported
-- first — is modeled deeply over those observations, so no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
/-- One dimension of a combined object, together with the observations the
validation reads about it.

* `name` — the dimension's label (reported when the dimension is the offender);
* `isCoordDim` — the dimension carries a coordinate index;
* `variesBetweenInputs` — the dimension's coordinate values differ between the
  input datasets, i.e. the inputs were combined across this dimension (as opposed
  to a bystander dimension identical in every input);
* `isMonotonic` — the dimension's global index is monotonic (increasing OR
  decreasing) throughout. -/
structure Dim where
  name : String
  isCoordDim : Bool
  variesBetweenInputs : Bool
  isMonotonic : Bool
deriving DecidableEq, Repr

/-- The label of the first dimension, in order, that was combined across the
inputs yet whose global index is not monotonic — `none` if there is no such
dimension. Bystander dimensions (those that do not vary between the inputs) are
skipped regardless of their monotonicity. -/
def firstNonMonotonicVarying (dims : List Dim) : Option String :=
  match dims with
  | [] => none
  | d :: rest =>
      if d.variesBetweenInputs && !d.isMonotonic then
        some d.name
      else
        firstNonMonotonicVarying rest
-- pure-end

-- post-conditions-start
/-- The validation succeeds (`Except.ok ()`) iff every dimension combined across
the inputs has a monotonic global index; otherwise it fails with the name of the
first such offending dimension in iteration order. A bystander dimension that
does not vary between the inputs never affects the outcome. -/
def problem_spec_monotonicCheck
    (dims : List Dim) (result : Except String Unit) : Prop :=
  result = (match firstNonMonotonicVarying dims with
            | some n => Except.error n
            | none => Except.ok ())
-- post-conditions-end

-- impl-start
def implementation_monotonicCheck (dims : List Dim) : Except String Unit := Id.run do
  -- Pre-patch bug: the monotonicity requirement is applied to EVERY coordinate
  -- dimension, not only the ones combined across the inputs. A bystander
  -- coordinate (identical in every input, hence not combined along) whose values
  -- happen to be non-monotonic wrongly triggers the rejection.
  for d in dims do
    if d.isCoordDim && !d.isMonotonic then
      return Except.error d.name
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_monotonicCheck :
    ∀ (dims : List Dim),
      problem_spec_monotonicCheck dims (implementation_monotonicCheck dims) := by
  intro dims
  unfold problem_spec_monotonicCheck implementation_monotonicCheck firstNonMonotonicVarying
  induction dims with
  | nil => rfl
  | cons d rest ih =>
    simp only [List.forIn_cons]
    by_cases h : d.variesBetweenInputs && !d.isMonotonic
    · simp [h]
    · simp [h, ih]
-- proof-end
