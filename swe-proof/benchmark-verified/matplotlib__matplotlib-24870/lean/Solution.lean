import Mathlib
-- imports-end

/-!
Choosing the level specification for a contour plot.

A contour routine must decide, from the caller's request and the nature of the
data being contoured, *what set of levels* to draw. The decision has three
ingredients:

* an optional explicit level specification provided by the caller (a preset count
  of automatically chosen levels, or a concrete list of level values);
* an optional positional level argument supplied alongside the data;
* the nature of the data itself — in particular whether the data is
  boolean-valued — together with whether the plot is filled (regions between
  levels are shaded) or unfilled (only the level curves are drawn).

The decision is resolved in priority order. A caller-provided explicit
specification always wins. Failing that, a positional level argument, if present,
is used directly. Failing both, the choice depends on the data: for
boolean-valued data the only meaningful boundary sits midway between the two
values, so an unfilled plot draws the single mid-level and a filled plot uses the
three values that bracket and separate the two regions; for all other data a
preset default count of automatically chosen levels is used.

The behaviour is stated abstractly here as an input→output relation; the
implementation and correctness proof are supplied separately. The value `1/2`
denotes the midpoint between the two boolean values `0` and `1`.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract here: the level-specification
-- decision is modeled value-exactly (a count, or a concrete list of exact
-- rationals). The downstream routine that expands a count into concrete
-- automatic levels is invoked only AFTER this decision and is outside the
-- modeled function (validated against the real routine by the differential
-- conformance check, not assumed as an axiom).
-- axioms-end

-- pure-start
/-- A level specification: either a count `n` of levels to be chosen
automatically downstream, or an explicit list of level values. -/
inductive LevelsArg where
  | count    (n : Nat)
  | explicit (xs : List Rat)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The chosen level specification, resolved in priority order from the caller's
request and the data characteristics.

* If the caller gave an explicit specification (`userLevels = some lv`), the
  result is exactly that specification.
* Otherwise, if a positional level argument is present, the result is its first
  element.
* Otherwise the result depends on the data: for boolean-valued data the result
  is the three bracketing values `[0, 1/2, 1]` for a filled plot and the single
  mid-value `[1/2]` for an unfilled plot; for non-boolean data the result is the
  preset default count `7`. -/
def problem_spec_chooseLevels
    (userLevels : Option LevelsArg) (args : List LevelsArg)
    (zIsBool filled : Bool) (result : LevelsArg) : Prop :=
  match userLevels with
  | some lv => result = lv
  | none =>
    match args with
    | a :: _ => result = a
    | [] =>
      if zIsBool then
        (filled = true  → result = LevelsArg.explicit [0, 1/2, 1]) ∧
        (filled = false → result = LevelsArg.explicit [1/2])
      else
        result = LevelsArg.count 7
-- post-conditions-end

-- impl-start
def implementation_chooseLevels
    (userLevels : Option LevelsArg) (args : List LevelsArg)
    (zIsBool filled : Bool) : LevelsArg := Id.run do
  match userLevels with
  | some lv => return lv
  | none =>
    match args with
    | a :: _ => return a
    | [] =>
      if zIsBool then
        if filled then
          return LevelsArg.explicit [0, 1/2, 1]
        else
          return LevelsArg.explicit [1/2]
      else
        return LevelsArg.count 7
-- impl-end

-- proof-start
theorem correct_chooseLevels :
    ∀ (userLevels : Option LevelsArg) (args : List LevelsArg) (zIsBool filled : Bool),
      problem_spec_chooseLevels userLevels args zIsBool filled
        (implementation_chooseLevels userLevels args zIsBool filled) := by
  intro userLevels args zIsBool filled
  unfold problem_spec_chooseLevels implementation_chooseLevels
  cases userLevels with
  | some lv => rfl
  | none =>
    cases args with
    | cons a as => rfl
    | nil =>
      cases zIsBool with
      | false => rfl
      | true =>
        cases filled <;>
          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
            first | rfl | simp_all
-- proof-end
