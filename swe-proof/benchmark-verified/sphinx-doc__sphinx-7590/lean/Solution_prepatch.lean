import Mathlib
-- imports-end

/-!
Computing the mangled identifier of a parsed C++ numeric literal.

A C++ literal may be written bare (e.g. `5`, `6.62607015e-34`), with a standard
numeric type suffix (e.g. `5ul`, `5.0f`), or as a *user-defined literal*: the
bare literal immediately followed by an identifier, e.g. `6.62607015e-34q_J` or
`5_udl`. The desired behaviour is that all three forms are recognised and given
a mangled identifier:

* a bare numeric literal whose source text is `data` mangles to `"L" data "E"`;
* a literal carrying a standard numeric suffix keeps the suffix as part of its
  source text, so `data` includes the suffix and the mangling is again
  `"L" data "E"`;
* a user-defined literal — a bare literal (with NO standard suffix) directly
  followed by an identifier `ident` — mangles as if it were a call of the
  identifier on the literal: `"clL_Zli" (id ident) "E" (inner) "E"`, where
  `inner` is the mangling of the underlying bare literal and `(id ident)` is the
  identifier's own mangling: the reserved namespace name `std` mangles to its
  standard abbreviation `"St"`, any other identifier to its length in decimal
  followed by its text.

A standard suffix takes precedence over a user-defined identifier: a literal that
is immediately followed by a recognised suffix is a plain suffixed literal, never
a user-defined literal. The float forms are recognised before the integer forms,
and among integer forms the binary, hexadecimal, decimal and octal shapes are
tried in that order.
-/

-- axioms-start
-- The lexical recognisers below are primitive pattern matchers over the head of
-- the input: each returns the LENGTH of the prefix it consumes (0 = no match).
-- They are modeled as opaque callees so that they appear identically in the
-- specification and the implementation; the behaviour of interest is the CONTROL
-- FLOW that combines them (when a trailing identifier is folded into a
-- user-defined literal), not the internals of any single recogniser. No property
-- of any recogniser is consumed by the proof, so no `axiom … _prop` is declared.

/-- Length of a leading floating-point literal (0 if none). -/
opaque floatMatch : List Char → Nat
/-- Length of a leading standard float type suffix following a float literal. -/
opaque floatSuffixMatch : List Char → Nat
/-- Length of a leading binary integer literal. -/
opaque binMatch : List Char → Nat
/-- Length of a leading hexadecimal integer literal. -/
opaque hexMatch : List Char → Nat
/-- Length of a leading decimal integer literal. -/
opaque decMatch : List Char → Nat
/-- Length of a leading octal integer literal. -/
opaque octMatch : List Char → Nat
/-- Length of a leading standard integer type suffix following an integer literal. -/
opaque intSuffixMatch : List Char → Nat
/-- Length of a leading user-defined-literal identifier (0 if none). -/
opaque udlMatch : List Char → Nat
-- axioms-end

-- pure-start
/-- Mangling of a bare literal whose source text is `data`. -/
def numId (data : List Char) : String := "L" ++ String.mk data ++ "E"

/-- Mangling fragment of an identifier: the reserved namespace name `std`
mangles to its standard abbreviation `"St"`; any other identifier mangles as
its length in decimal followed by its text. -/
def identId (ident : List Char) : String :=
  if ident = "std".toList then "St"
  else toString ident.length ++ String.mk ident

/-- Mangling of a user-defined literal wrapping `inner` with identifier `ident`. -/
def udlId (ident : List Char) (inner : String) : String :=
  "clL_Zli" ++ identId ident ++ "E" ++ inner ++ "E"

/-- Given a base literal occupying the first `baseLen` chars of `s` and the
suffix recogniser `suffixMatch` for that literal class, produce the mangled id:
keep a standard suffix as part of the literal's text, otherwise try to fold a
trailing identifier into a user-defined literal, otherwise emit the bare id. -/
def finishLiteral (baseLen : Nat) (s : List Char)
    (suffixMatch : List Char → Nat) : String :=
  let rest := s.drop baseLen
  let sfx := suffixMatch rest
  if sfx > 0 then
    numId (s.take (baseLen + sfx))
  else
    let baseId := numId (s.take baseLen)
    let u := udlMatch rest
    if u > 0 then udlId (rest.take u) baseId else baseId

/-- First matching integer-literal length, trying binary, hex, decimal, octal. -/
def intMatchLen (s : List Char) : Option Nat :=
  let bs := binMatch s
  if bs > 0 then some bs else
  let hs := hexMatch s
  if hs > 0 then some hs else
  let ds := decMatch s
  if ds > 0 then some ds else
  let os := octMatch s
  if os > 0 then some os else none
-- pure-end

-- post-conditions-start
/-- The mangled id of the literal at the head of `s`: a float literal (with
optional suffix or trailing user-defined identifier) if one is present, else the
first matching integer literal (likewise), else none. -/
def problem_spec_literalId (s : List Char) (result : Option String) : Prop :=
  result =
    (let fl := floatMatch s
     if fl > 0 then some (finishLiteral fl s floatSuffixMatch)
     else match intMatchLen s with
          | some il => some (finishLiteral il s intSuffixMatch)
          | none => none)
-- post-conditions-end

-- impl-start
def implementation_literalId (s : List Char) : Option String := Id.run do
  -- Pre-patch bug: literals are recognised but a trailing user-defined-literal
  -- identifier is never folded in — only standard numeric suffixes are kept, so
  -- `6.62607015e-34q_J` is parsed as the bare float and the `q_J` is dropped.
  let fl := floatMatch s
  if fl > 0 then
    let sfx := floatSuffixMatch (s.drop fl)
    return some (numId (s.take (fl + sfx)))
  for m in [binMatch, hexMatch, decMatch, octMatch] do
    let il := m s
    if il > 0 then
      let sfx := intSuffixMatch (s.drop il)
      return some (numId (s.take (il + sfx)))
  return none
-- impl-end

-- proof-start
theorem correct_literalId :
    ∀ (s : List Char),
      problem_spec_literalId s (implementation_literalId s) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
