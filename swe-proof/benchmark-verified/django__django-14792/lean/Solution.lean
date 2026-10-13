import Mathlib
-- imports-end

/-!
Choosing the display name of a time zone.

A time zone exposes two pieces of textual information about itself:

  * a short self-reported label (for example a constant UTC-offset designation),
    which may be absent altogether or be the empty string when the zone does not
    advertise one; and
  * a full textual form that is always available.

The display name is the short label whenever it is present and non-empty;
otherwise it is the full textual form. This makes constant-offset zones present
themselves by their offset designation while named zones fall back to their full
textual form.
-/

-- axioms-start
-- No unchanged outside callee is consumed: the short self-reported label and the
-- full textual form of the time zone enter as plain data (an optional string and
-- a string), and the only operation performed is choosing between them by
-- truthiness. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (no auxiliary helpers needed)
-- pure-end

-- post-conditions-start
/-- The display name is fully pinned to the inputs:

  * when the short self-reported label is present and non-empty, the result is
    exactly that label;
  * otherwise (the label is absent or empty) the result is exactly the full
    textual form.

Both cases together determine the result for every input, so no output component
is left free. -/
def problem_spec_getTimezoneName
    (tzLabel : Option String) (tzStr : String) (result : String) : Prop :=
  (∀ s, tzLabel = some s → s ≠ "" → result = s) ∧
  ((tzLabel = none ∨ tzLabel = some "") → result = tzStr)
-- post-conditions-end

-- impl-start
def implementation_getTimezoneName
    (tzLabel : Option String) (tzStr : String) : String := Id.run do
  let mut name := tzStr
  match tzLabel with
  | some s => if s ≠ "" then name := s
  | none => pure ()
  return name
-- impl-end

-- proof-start
theorem correct_getTimezoneName :
    ∀ (tzLabel : Option String) (tzStr : String),
      problem_spec_getTimezoneName tzLabel tzStr
        (implementation_getTimezoneName tzLabel tzStr) := by
  intro tzLabel tzStr
  unfold problem_spec_getTimezoneName implementation_getTimezoneName
  constructor
  · intro s hs hne
    subst hs
    simp only [Id.run, if_pos hne]
    rfl
  · rintro (h | h) <;> subst h <;> rfl
-- proof-end
