import Mathlib
-- imports-end

/-!
Converting an array's values to plain floating-point numbers for numeric
computation (the coercion a polynomial-evaluation routine applies to its
coordinate before doing arithmetic).

An array is described by the *kind* of its values and the two value views the
coercion can read:

* a **datetime** array — instants in time — is made numeric by the standard
  datetime-to-number reduction relative to a constant epoch (the result is the
  number of nanoseconds since that epoch, as a float);
* a **duration** array — time spans / elapsed-time values — is made numeric by
  reinterpreting its underlying integer nanosecond counts directly as floats;
* an array that is **already numeric** is returned with its values unchanged.

The desired rule is therefore branch-specific:

  * datetime values  → the epoch-relative datetime-to-number reduction;
  * duration values  → the underlying integer counts cast to float;
  * any other values → the values, unchanged.

In particular a duration array follows its OWN rule — its integer counts cast to
float — and is not put through the datetime epoch reduction; the two
time-related kinds are coerced by different rules even though both originate
from time values.
-/

-- axioms-start
/-- The unchanged datetime-to-number reduction used for datetime-valued arrays:
it maps the underlying integer nanosecond counts to floats relative to a
constant epoch (with the not-a-time sentinel mapped to a not-a-number float). It is an
unchanged upstream callee, declared by signature only and used identically by
the specification and the implementation, so no separate property of it is
consumed. -/
opaque datetimeToFloat : List Int → List Float
-- axioms-end

-- pure-start
/-- The kind of values an array holds, as far as the coercion is concerned. -/
inductive ValKind where
  | datetime
  | duration
  | numeric
deriving DecidableEq, Repr

/-- An array, described by the observations the coercion reads:

* `kind` — whether the values are datetimes, durations, or already numeric;
* `raw` — the underlying integer nanosecond counts (read by the datetime and
  duration branches);
* `data` — the array's values seen as floats (returned by the numeric branch). -/
structure ArrayView where
  kind : ValKind
  raw : List Int
  data : List Float

/-- The float values produced by coercing an array, by the rule described above. -/
def coerceResult (x : ArrayView) : List Float :=
  match x.kind with
  | ValKind.datetime => datetimeToFloat x.raw
  | ValKind.duration => x.raw.map Float.ofInt
  | ValKind.numeric  => x.data
-- pure-end

-- post-conditions-start
/-- The coercion yields exactly the float values dictated by the array's kind:
the epoch-relative datetime reduction for datetimes, the underlying integer
counts cast to float for durations, and the unchanged values for numeric
arrays. -/
def problem_spec_coerceToFloat (x : ArrayView) (result : List Float) : Prop :=
  result = coerceResult x
-- post-conditions-end

-- impl-start
def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do
  -- Pre-patch: datetime AND duration arrays are both routed through the
  -- datetime epoch reduction; duration arrays never reach their own cast rule.
  if x.kind = ValKind.datetime ∨ x.kind = ValKind.duration then
    return datetimeToFloat x.raw
  else
    return x.data
-- impl-end

-- proof-start
theorem correct_coerceToFloat :
    ∀ (x : ArrayView),
      problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
  intro x
  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
  cases x.kind <;> simp
-- proof-end
