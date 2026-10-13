import Mathlib
-- imports-end

/-!
Rendering the outline of a filled shape with a dashed stroke style.

A dashed stroke style is described by two pieces of data carried together: a
non-negative *offset* (how far into the dash cycle the very first segment
begins) and an *on/off sequence* (the alternating lengths of drawn and blank
ink). When the shape is actually rendered, the stroke style that is handed to
the renderer must reproduce BOTH pieces of data exactly as they were configured
on the shape: the offset and the on/off sequence applied at render time are the
ones the user supplied.

There is one short-circuit: if the shape is not visible, nothing is rendered at
all and no stroke style is produced.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a logical contract: the rendered
-- stroke style is the configured offset/on-off data carried through verbatim,
-- spelled out concretely below. The visibility short-circuit is a plain guard.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The stroke style produced when rendering:

* if the shape is not visible, nothing is produced (`none`);
* if it is visible, the produced style carries BOTH the configured `offset` and
  the configured on/off sequence `dashes`, unchanged — i.e. exactly
  `some (offset, dashes)`. In particular the offset is preserved, not discarded. -/
def problem_spec_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int))
    (result : Option (Int × Option (List Int))) : Prop :=
  (visible = false → result = none) ∧
  (visible = true → result = some (offset, dashes))
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: while rendering, the configured offset is replaced
-- by the constant `0` before the stroke style is applied, so a non-zero offset
-- has no effect on the rendered dash pattern.
def implementation_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int)) :
    Option (Int × Option (List Int)) := Id.run do
  if !visible then
    return none
  let used : Int × Option (List Int) := (0, dashes)
  return some used
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (the
-- `visible = true → result = some (offset, dashes)` clause is violated whenever
-- `offset ≠ 0`, since the buggy impl yields `some (0, dashes)`).
theorem correct_dashRender :
    ∀ (visible : Bool) (offset : Int) (dashes : Option (List Int)),
      problem_spec_dashRender visible offset dashes
        (implementation_dashRender visible offset dashes) := by
  sorry
-- proof-end
