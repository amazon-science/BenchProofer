import Mathlib
-- imports-end

/-!
Selecting and cleaning the submitted value of each field on a bound form.

A form has an ordered collection of fields. Cleaning the form produces, for each
field and in field order, the value that field contributes to the form's cleaned
data. For each field the value is chosen as follows:

* an *editable* field takes the value submitted for it (the data extracted from
  the form's payload for that field);
* a *disabled* field ignores any submitted payload and instead takes its own
  preset initial value — specifically the initial value exactly as the field
  itself would present it. A field presents a temporal initial value (a date or
  time) only at the precision its display can represent: if the field's display
  cannot represent sub-second precision, any sub-second component of the initial
  value is dropped before it is used. Non-temporal initial values, and temporal
  values on fields whose display does support sub-second precision, are presented
  unchanged.

The selected value is then cleaned. In the success case modeled here cleaning
preserves the selected value, so the cleaned value for each field equals the
value selected by the rule above. The cleaned data therefore has one entry per
field, in field order, with no field's entry left unconstrained.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The two outside
-- operations used per field — obtaining the field's preset initial value and
-- obtaining the value submitted for the field — have their results supplied as
-- inputs (`rawInitial`, `data`). The presentation-normalization of a temporal
-- value and the field-order traversal are spelled out concretely below.
-- axioms-end

-- pure-start
/-- A field value. `ts whole sub` is a temporal value split into its
whole-second-and-coarser component (`whole`) and its sub-second component
(`sub`, a microsecond count `0..999999`). `other n` stands in for any
non-temporal value. -/
inductive FieldValue where
  | ts (whole : Int) (sub : Nat)
  | other (n : Int)
deriving DecidableEq

/-- One field of the form together with its bound state.
* `disabled`      — whether the field is disabled;
* `supportsMicro` — whether the field's display can represent sub-second precision;
* `rawInitial`    — the field's preset initial value (already evaluated);
* `data`          — the value submitted for the field. -/
structure FieldModel where
  disabled : Bool
  supportsMicro : Bool
  rawInitial : FieldValue
  data : FieldValue
deriving DecidableEq

/-- The initial value of a field exactly as the field presents it: a temporal
value loses its sub-second component when the field's display cannot represent
sub-second precision; every other value is presented unchanged. -/
def boundInitial (f : FieldModel) : FieldValue :=
  match f.rawInitial with
  | FieldValue.ts whole sub => if f.supportsMicro then FieldValue.ts whole sub else FieldValue.ts whole 0
  | FieldValue.other n => FieldValue.other n

/-- The cleaned value contributed by one field: a disabled field uses its
presented initial value; an editable field uses its submitted value. -/
def cleanedValue (f : FieldModel) : FieldValue :=
  if f.disabled then boundInitial f else f.data
-- pure-end

-- post-conditions-start
def problem_spec_cleanFields (fields : List FieldModel) (result : List FieldValue) : Prop :=
  result = fields.map cleanedValue
-- post-conditions-end

-- impl-start
-- PRE-PATCH skeleton: a disabled field's value is taken from its preset initial
-- value as-is, WITHOUT presenting it at the field's display precision. On a
-- disabled field whose display cannot represent sub-second precision and whose
-- initial value carries a non-zero sub-second component, this yields the raw
-- value (sub-second component retained) instead of the presented value
-- (sub-second component dropped), contradicting the postcondition.
def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
  let mut cleaned : List FieldValue := []
  for f in fields do
    let value := if f.disabled then f.rawInitial else f.data
    cleaned := cleaned ++ [value]
  return cleaned
-- impl-end

-- proof-start
theorem correct_cleanFields :
    ∀ (fields : List FieldModel),
      problem_spec_cleanFields fields (implementation_cleanFields fields) := by
  sorry
-- proof-end
