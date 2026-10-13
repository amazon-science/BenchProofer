import Mathlib
-- imports-end

/-!
Rendering the stored value of a JSON-valued model field for read-only display.

The routine is given the value held by the field and the placeholder text shown
for an absent value. It decides what text to display:

* if the value is absent (null), the placeholder text is shown;
* if the value is present and non-empty, it is shown as its standard JSON text;
* if a present, non-empty value cannot be represented as JSON, a generic textual
  rendering of the value is shown instead;
* a value that is present but empty (for example an empty object, empty list,
  empty string, the integer zero, or the boolean false) is shown using the
  generic textual rendering.

The standard JSON rendering and the generic textual rendering are pre-existing
operations the routine merely selects between; their behavior is described by
their signatures and is exercised directly by the differential checks. The
distinguishing behavior modeled here is *which* rendering is selected for each
class of value.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- pure-start
/-- A value that may be stored in a JSON-valued field. Rich enough to express
the presence/emptiness distinctions that drive the display choice, and to carry
values that are not representable as JSON (e.g. a mapping keyed by a tuple). -/
inductive PyVal where
  | null
  | bool (b : Bool)
  | int (n : Int)
  | num (q : Rat)
  | str (s : String)
  | list (xs : List PyVal)
  | tuple (xs : List PyVal)
  | dict (kvs : List (PyVal × PyVal))

/-- Whether the value is absent. -/
def isNull : PyVal → Bool
  | .null => true
  | _ => false

/-- Whether the value is "present and non-empty" — the presence test that gates
the JSON rendering. Mirrors the standard emptiness convention: the absent value,
the boolean false, a zero number, the empty string, and empty containers are
all treated as empty; everything else is non-empty. -/
def truthy : PyVal → Bool
  | .null => false
  | .bool b => b
  | .int n => n != 0
  | .num q => q != 0
  | .str s => !s.isEmpty
  | .list xs => !xs.isEmpty
  | .tuple xs => !xs.isEmpty
  | .dict kvs => !kvs.isEmpty
-- pure-end

-- axioms-start
/-- The standard JSON text of a value, or a failure signal (`Except.error`) when
the value's structure is not representable as JSON (the one failure mode the
caller recovers from; any other failure propagates and is out of scope). An
unchanged pre-existing operation; only its result is consumed here. -/
opaque jsonSerialize : PyVal → Except Unit String

/-- The generic textual rendering of a value, given the placeholder text for an
absent value. An unchanged pre-existing operation; only its result is consumed
here. -/
opaque genericDisplay : PyVal → String → String
-- axioms-end

-- post-conditions-start
/-- Input→output relation for rendering a JSON-valued field's value.

Inputs:
* `value` — the value held by the field;
* `empty` — the placeholder text shown for an absent value.

The result is pinned in every case, and the three cases partition the inputs:
absent, present-and-non-empty, and present-but-empty. -/
def problem_spec_displayForField (value : PyVal) (empty : String) (result : String) : Prop :=
  (isNull value = true → result = empty) ∧
  (isNull value = false → truthy value = true →
      result = (match jsonSerialize value with
                | .ok s => s
                | .error _ => genericDisplay value empty)) ∧
  (isNull value = false → truthy value = false →
      result = genericDisplay value empty)
-- post-conditions-end

-- impl-start
def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
  -- An absent value shows the placeholder.
  if isNull value then
    return empty
  -- A present, non-empty value is rendered as JSON; if it cannot be represented
  -- as JSON, fall back to the generic rendering.
  if truthy value then
    match jsonSerialize value with
    | .ok s => return s
    | .error _ => return genericDisplay value empty
  -- A present but empty value uses the generic rendering.
  return genericDisplay value empty
-- impl-end


-- proof-start
theorem correct_displayForField :
    ∀ (value : PyVal) (empty : String),
      problem_spec_displayForField value empty
        (implementation_displayForField value empty) := by
  intro value empty
  refine ⟨fun h => ?_, fun h1 h2 => ?_, fun h1 h2 => ?_⟩ <;>
    simp only [implementation_displayForField, Id.run] <;>
    simp_all [pure] <;> cases jsonSerialize value <;> rfl

-- proof-end
