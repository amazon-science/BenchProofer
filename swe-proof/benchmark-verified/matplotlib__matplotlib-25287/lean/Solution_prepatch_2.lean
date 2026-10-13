import Mathlib
-- imports-end

/-!
Choosing the color of an axis's offset text (the small exponent / multiplier
label drawn at the end of a numeric axis).

An axis carries two independent color settings that can govern its annotations:

  * a tick-mark color — the color used for the tick marks themselves;
  * a label-color setting — the color used for the tick *labels*. This setting
    may instead hold a distinguished sentinel value meaning "I have no opinion;
    defer to the tick-mark color." We model that sentinel as the absence of a
    value (`none`); an explicit choice is `some c`.

The offset text is a tick label, so its color must follow the label-color
setting, not the tick-mark color. The desired behavior: when the label-color
setting holds an explicit color, the offset text takes that color; when the
label-color setting is at its defer-to-ticks sentinel, the offset text falls
back to the tick-mark color. In particular, when an explicit label color is set
the offset text must NOT be left at the tick-mark color.

Two coordinate axes (the horizontal and the vertical one) carry independent
copies of these two settings and resolve the offset-text color the same way, so
each direction is modeled by its own function with the identical contract.

A color is an opaque token: its internal structure is irrelevant here — what
matters is solely WHICH of the two input colors ends up on the offset text.
-/

-- axioms-start
/-- An opaque color token. Only the IDENTITY of the chosen color matters to the
behavior modeled here (which of the two candidate colors the offset text ends up
with), never how a color is represented or rendered. -/
opaque Color : Type
-- axioms-end

-- pure-start
-- No additional pure helpers are required: each modeled behavior is the single
-- choice between the explicit label color and the tick-mark fallback.
-- pure-end

-- post-conditions-start
/-- Resolving the offset-text color for the horizontal axis. The result is fully
pinned to the two inputs: it equals the explicit label color when one is set
(`labelColor = some c` ⇒ result `= c`), and falls back to the tick-mark color
when the label-color setting is at its defer-to-ticks sentinel
(`labelColor = none` ⇒ result `= tickColor`). No part of the result is left
free, and no color outside the two inputs may appear. -/
def problem_spec_horizOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) (result : Color) : Prop :=
  result = labelColor.getD tickColor
-- post-conditions-end

-- impl-start
def implementation_horizOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
  -- Decide the offset text's color from the label-color setting, falling back
  -- to the tick-mark color only when that setting defers to the ticks.
  let mut chosen := tickColor
  match labelColor with
  | none   => chosen := tickColor
  | some c => chosen := c
  return chosen
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against the
-- buggy impl it cannot close: when an explicit label color is set
-- (`labelColor = some c`), the impl returns `tickColor` while the spec requires
-- the inherited value `c = labelColor.getD tickColor`.
theorem correct_horizOffsetTextColor :
    ∀ (tickColor : Color) (labelColor : Option Color),
      problem_spec_horizOffsetTextColor tickColor labelColor
        (implementation_horizOffsetTextColor tickColor labelColor) := by
  intro tickColor labelColor
  unfold problem_spec_horizOffsetTextColor implementation_horizOffsetTextColor
  cases labelColor with
  | none => rfl
  | some c => rfl
-- proof-end

-- post-conditions-start
/-- Resolving the offset-text color for the vertical axis. Symmetric to the
horizontal case: the result equals the explicit label color when one is set, and
falls back to the tick-mark color when the label-color setting is at its
defer-to-ticks sentinel — the result is fully pinned to the two inputs. -/
def problem_spec_vertOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) (result : Color) : Prop :=
  result = labelColor.getD tickColor
-- post-conditions-end

-- impl-start
def implementation_vertOffsetTextColor
    (tickColor : Color) (labelColor : Option Color) : Color := Id.run do
  -- The offset text is colored from the tick-mark color directly, ignoring the
  -- label-color setting entirely.
  let mut chosen := tickColor
  return chosen
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against the
-- buggy impl it cannot close: when an explicit label color is set
-- (`labelColor = some c`), the impl returns `tickColor` while the spec requires
-- the inherited value `c = labelColor.getD tickColor`.
theorem correct_vertOffsetTextColor :
    ∀ (tickColor : Color) (labelColor : Option Color),
      problem_spec_vertOffsetTextColor tickColor labelColor
        (implementation_vertOffsetTextColor tickColor labelColor) := by
  intro tickColor labelColor
  unfold problem_spec_vertOffsetTextColor implementation_vertOffsetTextColor
  cases labelColor with
  | none => rfl
  | some c => rfl
-- proof-end
