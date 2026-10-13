import Mathlib
-- imports-end

/-!
Converting a single labelled level of a composite index wrapper into a plain
numeric array, while preserving the element data type the wrapper was built to
carry.

The wrapper stores an *original* element data type (`selfDtype`) — the data type
of the values it was constructed from. Reading one labelled level out of the
underlying composite index yields a raw value array (`rawArray`) whose own data
type may have been widened by the underlying machinery, even though the values
themselves are unchanged.

The array-conversion entry point takes an optional requested data type
(`dtypeArg`). Its contract:

  * The EFFECTIVE data type is the requested one when given, and otherwise the
    wrapper's stored original data type.
  * When a labelled level is selected, the result is the raw level values
    re-presented with the EFFECTIVE data type — same element values, but the
    effective data type rather than the raw array's (possibly widened) one.
  * When no level is selected, the result is whatever the underlying (non-level)
    conversion produces for the effective data type.

Stated as an input→output relation; the implementation and its correctness proof
are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract. Reading a level's
-- raw value array, and the non-level conversion, are taken as modeled inputs
-- (`rawArray` and `superArray`); their production by the underlying machinery is
-- unchanged by this behavior and is exercised end-to-end by the differential
-- check. There is therefore no `axiom <callee>_prop` for the proof to consume.

/-- An element data type, abstracted to the only property observed here:
identity (equality). Distinct concrete data types ↔ distinct `Nat`s. -/
abbrev Dtype := Nat

/-- A labelled level identity. Only "selected vs not selected" and its identity
are observed. -/
abbrev Level := Nat

/-- A plain numeric array, restricted to the two observed components:
* `dtype` — the array's element data type;
* `data`  — the element values (a widening/narrowing of the data type preserves
  the in-range integer values, so the values are modeled as a `List Int`). -/
structure NpArray where
  dtype : Dtype
  data : List Int
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Re-present a list of element values as an array carrying a given data type
(the value-level conversion to a requested data type): the data type is set to
`d` and the in-range element values are carried through unchanged. -/
def castArray (d : Dtype) (data : List Int) : NpArray :=
  { dtype := d, data := data }

/-- The effective data type: the requested one if supplied, otherwise the
wrapper's stored original data type. -/
def effectiveDtype (selfDtype : Dtype) (dtypeArg : Option Dtype) : Dtype :=
  dtypeArg.getD selfDtype
-- pure-end

-- post-conditions-start
/-- The array-conversion result as a function of the inputs:

* the effective data type is `dtypeArg` when supplied, else `selfDtype`;
* a selected level (`level = some _`) yields the raw level values carried at the
  effective data type — i.e. the effective data type, NOT the raw array's;
* an unselected level (`level = none`) yields the underlying non-level
  conversion at the effective data type. -/
def problem_spec_arrayConvert
    (selfDtype : Dtype) (dtypeArg : Option Dtype)
    (level : Option Level) (rawArray : NpArray)
    (superArray : Dtype → NpArray)
    (result : NpArray) : Prop :=
  result =
    (match level with
     | some _ => castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
     | none   => superArray (effectiveDtype selfDtype dtypeArg))
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: a selected level returns the raw level value array
-- VERBATIM — carrying the raw array's (possibly widened) data type — instead of
-- re-presenting the values at the effective data type. When the raw array's data
-- type differs from the effective one, the result advertises the wrong type.
def implementation_arrayConvert
    (selfDtype : Dtype) (dtypeArg : Option Dtype)
    (level : Option Level) (rawArray : NpArray)
    (superArray : Dtype → NpArray) : NpArray := Id.run do
  match level with
  | some _ =>
      return rawArray
  | none   =>
      return superArray (effectiveDtype selfDtype dtypeArg)
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl: when a
-- level is selected and the raw array's data type differs from the effective
-- data type, the spec demands `castArray (effectiveDtype …) rawArray.data` but
-- the buggy impl returns `rawArray` (with its raw data type).
theorem correct_arrayConvert :
    ∀ (selfDtype : Dtype) (dtypeArg : Option Dtype)
      (level : Option Level) (rawArray : NpArray)
      (superArray : Dtype → NpArray),
      problem_spec_arrayConvert selfDtype dtypeArg level rawArray superArray
        (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
  intro selfDtype dtypeArg level rawArray superArray
  unfold problem_spec_arrayConvert implementation_arrayConvert
  cases level with
  | some l => simp [castArray, effectiveDtype]
  | none => simp [effectiveDtype]
-- proof-end
