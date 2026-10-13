import Mathlib
-- imports-end

/-!
Building the SQL expression that presents a stored datetime column in a target
time zone, for a backend that keeps datetimes as naive local values.

The builder is given:

  * a flag saying whether time-zone–aware processing is active at all;
  * the name of the time zone the stored values are recorded in (the source
    time zone of the connection);
  * the name of the target time zone the caller wants the value expressed in;
  * the SQL expression naming the column.

When time-zone–aware processing is active AND the source and target time zones
differ, the column expression is wrapped in a conversion from the source time
zone to the target time zone, producing
`CONVERT_TZ(<column>, '<source>', '<target>')`.

In every other case — time-zone processing inactive, or the source and target
time zones coinciding — the column expression is returned unchanged (no
conversion is emitted, so the value is presented in the time zone it is already
recorded in).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the time-zone flag and the source /
-- target time-zone names enter as plain data, and the only operation performed
-- is the construction of the SQL conversion fragment, modeled directly as string
-- concatenation. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The conversion fragment that re-expresses a column from a source time zone in
a target time zone: `CONVERT_TZ(<column>, '<source>', '<target>')`. -/
def convertTzFragment (fieldName srcTz dstTz : String) : String :=
  "CONVERT_TZ(" ++ fieldName ++ ", '" ++ srcTz ++ "', '" ++ dstTz ++ "')"
-- pure-end

-- post-conditions-start
/-- The produced SQL expression is fully pinned to the inputs:

  * when time-zone processing is active and the source and target time zones
    differ, it is exactly the conversion fragment from the source to the target
    time zone wrapping the original column expression;
  * otherwise it is exactly the original column expression, unchanged.

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_tzConvertSql
    (useTz : Bool) (connTz tzname fieldName : String) (result : String) : Prop :=
  (useTz = true ∧ connTz ≠ tzname →
      result = convertTzFragment fieldName connTz tzname) ∧
  (¬ (useTz = true ∧ connTz ≠ tzname) →
      result = fieldName)
-- post-conditions-end

-- impl-start
def implementation_tzConvertSql
    (useTz : Bool) (connTz tzname fieldName : String) : String := Id.run do
  let mut field := fieldName
  if useTz then
    field := convertTzFragment field "UTC" tzname
  return field
-- impl-end

-- proof-start
theorem impl_eq (useTz : Bool) (connTz tzname fieldName : String) :
    implementation_tzConvertSql useTz connTz tzname fieldName
      = if useTz && connTz != tzname then convertTzFragment fieldName connTz tzname
        else fieldName := by
  unfold implementation_tzConvertSql
  simp only [Id.run, bind, pure]

theorem correct_tzConvertSql :
    ∀ (useTz : Bool) (connTz tzname fieldName : String),
      problem_spec_tzConvertSql useTz connTz tzname fieldName
        (implementation_tzConvertSql useTz connTz tzname fieldName) := by
  intro useTz connTz tzname fieldName
  have hcond : (useTz && connTz != tzname) = true ↔ (useTz = true ∧ connTz ≠ tzname) := by
    rw [Bool.and_eq_true, bne_iff_ne]
  unfold problem_spec_tzConvertSql
  rw [impl_eq]
  by_cases h : useTz && connTz != tzname
  · rw [if_pos h]
    exact ⟨fun _ => rfl, fun hneg => absurd (hcond.mp h) hneg⟩
  · rw [if_neg h]
    exact ⟨fun hpos => absurd (hcond.mpr hpos) h, fun _ => rfl⟩
-- proof-end
