import Mathlib
-- imports-end

/-!
Interpreting a textual duration into a single signed quantity of microseconds.

A duration may be written in one of several textual notations. This file pins
the behavior of the PRIMARY clock notation, of the shape

    [<days> ]<clock>

where the optional leading `<days> ` part is an integer day count followed by a
space (optionally followed by a word for the unit) and `<clock>` is a
colon-separated clock quantity `H:M:S`, `M:S`, or `S`, with an optional
fractional second `.f`. A single optional leading minus sign in front of the
clock negates the WHOLE clock quantity at once; the day count carries its own
independent sign. Each individual clock field (hours, minutes, seconds, and the
fractional digits) is a NON-negative integer — a minus sign attached to an
inner clock field is not part of this notation, so such input is not accepted by
the primary notation. The whole-text match runs to the end of the text or to just
before ONE final newline, so a single trailing newline is tolerated.

When the text does not match the primary notation, the value is interpreted by a
secondary notation (the unchanged alternative interpreter, modeled abstractly as
`fallbackFormatMicros`); the overall result is the primary interpretation when it
applies and otherwise the secondary one. The result is a quantity of
microseconds (two textual durations denote the same duration exactly when their
total microseconds agree), or "no interpretation" when neither notation applies.

DOMAIN OF THE MODEL. Two side conditions delimit the text this file speaks
about. Outside them the interpreter being modeled does something this value type
cannot denote, so no claim is made there rather than a false one:

  1. ASCII TEXT (`asciiText`). The digit class of the primary notation here is
     the ASCII run `0`-`9`. The real interpreter's digit class is the host's
     whole Unicode decimal-digit repertoire: to it `"٥"` (U+0665, Arabic-Indic
     digit five) is a digit denoting five, and `"٥"` therefore names a duration
     of five seconds. That repertoire is a host character table of some 650
     ranges, not a property of this notation, and this file does not re-derive
     it — so the claim below is made only for text all of whose code points are
     below 128, exactly where the two digit classes coincide.

  2. REPRESENTABLE MAGNITUDE (`primaryInRange`). A duration value here is a
     bounded quantity: `-999999999 days` at the bottom and
     `999999999 days, 23:59:59.999999` at the top, and the day part, the signed
     clock part and their sum must each land inside it. Where the primary
     notation names a larger magnitude the real interpreter signals an
     out-of-range condition instead of returning a duration, and an
     out-of-range condition is not a value of `Option Int` — so the claim below
     is made only inside the range.
-/

-- axioms-start
-- The secondary interpreter (the alternative textual notations other than the
-- primary clock notation) is declared as an opaque reference. Its behavior is
-- not re-derived here; it is validated against the real alternative interpreter
-- by G-CONF (A-reference). The proof agent may add a `_prop` axiom about it only
-- if a proof step requires one — the primary-notation proof obligations below do
-- not.
opaque fallbackFormatMicros : List Char → Option Int
-- axioms-end

-- pure-start
/-- A character is a decimal digit `0`–`9`. -/
def isDigitC (c : Char) : Bool := 48 ≤ c.toNat && c.toNat ≤ 57

/-- A character inside the ASCII range. -/
def isAsciiC (c : Char) : Bool := c.toNat < 128

/-- Side condition 1 of the model's domain: the text is entirely ASCII, which is
where this file's digit class agrees with the real interpreter's. -/
def asciiText (v : List Char) : Bool := v.all isAsciiC

/-- Decode a NON-empty run of decimal digits into its value; `none` if the input
is empty or contains a non-digit. -/
def digitsToNat? (cs : List Char) : Option Nat :=
  if cs.isEmpty then none
  else if cs.all isDigitC then
    some (cs.foldl (fun n c => n * 10 + (c.toNat - 48)) 0)
  else none

/-- Split a character list into fields separated by `sep` (like a string split):
the result always has one more field than the count of separators. -/
def splitOnChar (sep : Char) : List Char → List (List Char)
  | [] => [[]]
  | c :: cs =>
      match splitOnChar sep cs with
      | [] => [[]]                       -- unreachable: split is never empty
      | f :: fs => if c = sep then [] :: f :: fs else (c :: f) :: fs

/-- Split a list at its FIRST occurrence of a space into the part before and the
part after; `none` if there is no space. -/
def splitFirstSpace : List Char → Option (List Char × List Char)
  | [] => none
  | c :: t =>
      if c = ' ' then some ([], t)
      else match splitFirstSpace t with
        | some (b, a) => some (c :: b, a)
        | none => none

/-- Drop ONE final newline if the text has one: the whole-text match of the
primary notation runs to the end of the text or to just before a single final
newline, and no other character of the notation is a newline. -/
def dropFinalNewline (v : List Char) : List Char :=
  if v.getLast? = some '\n' then v.dropLast else v

/-- Decode an OPTIONALLY-signed integer (`-?` then a non-empty digit run). -/
def signedIntToInt? (cs : List Char) : Option Int :=
  match cs with
  | '-' :: ds =>
      match digitsToNat? ds with
      | some n => some (-(n : Int))
      | none => none
  | _ =>
      match digitsToNat? cs with
      | some n => some (n : Int)
      | none => none

/-- Drop a leading day-unit word (`days, ` or `day, `) if present. -/
def stripUnit (cs : List Char) : List Char :=
  if "days, ".toList.isPrefixOf cs then cs.drop 6
  else if "day, ".toList.isPrefixOf cs then cs.drop 5
  else cs

/-- Microseconds contributed by a non-negative clock `H:M:S.f`. -/
def clockUs (h m s us : Nat) : Int :=
  ((h * 3600 * 1000000 + m * 60 * 1000000 + s * 1000000 + us : Nat) : Int)

/-- Apply a leading minus (if `neg`) to the whole clock quantity. -/
def applySign (neg : Bool) (x : Int) : Int := if neg then -x else x

/-- Bottom of the range a duration value can hold, in microseconds:
`-999999999 days`. -/
def usMin : Int := -(999999999 * 86400 * 1000000)

/-- Top of the range a duration value can hold, in microseconds:
`999999999 days, 23:59:59.999999`. -/
def usMax : Int := (999999999 * 86400 + 86399) * 1000000 + 999999

/-- A microsecond quantity a duration value can hold. -/
def inUsRange (x : Int) : Bool := decide (usMin ≤ x ∧ x ≤ usMax)

/-- Decode the final clock field: a non-negative seconds count with an optional
fractional part `.f`. The fractional part must be 1–12 digits; its first up to
six digits, right-padded to six, give the microseconds; surplus digits are
dropped. Returns the seconds count and the microseconds, or `none`. -/
def parseSecMicro? (cs : List Char) : Option (Nat × Nat) :=
  match splitOnChar '.' cs with
  | [secs] =>
      match digitsToNat? secs with
      | some s => some (s, 0)
      | none => none
  | [secs, frac] =>
      if frac.isEmpty || frac.length > 12 || !frac.all isDigitC then none
      else
        let micro6 := (frac.take 6) ++ List.replicate (6 - min 6 frac.length) '0'
        match digitsToNat? secs, digitsToNat? micro6 with
        | some s, some us => some (s, us)
        | _, _ => none
  | _ => none

/-- Decode the clock portion (after any day prefix has been stripped): an
optional single leading minus negating the whole quantity, then 1–3
colon-separated NON-negative fields. -/
def parseClockMicros? (rest : List Char) : Option Int :=
  let (neg, body) :=
    match rest with
    | '-' :: t => (true, t)
    | _ => (false, rest)
  match splitOnChar ':' body with
  | [a] =>
      match parseSecMicro? a with
      | some (s, us) => some (applySign neg (clockUs 0 0 s us))
      | none => none
  | [m, a] =>
      match digitsToNat? m, parseSecMicro? a with
      | some mm, some (s, us) => some (applySign neg (clockUs 0 mm s us))
      | _, _ => none
  | [h, m, a] =>
      match digitsToNat? h, digitsToNat? m, parseSecMicro? a with
      | some hh, some mm, some (s, us) => some (applySign neg (clockUs hh mm s us))
      | _, _, _ => none
  | _ => none

/-- The two microsecond quantities the PRIMARY clock notation builds, or `none`
if the text is not in that notation: the day part (carrying its own sign) and the
clock part (carrying the single leading minus). An optional integer day count
followed by a space (and optional unit word) prefixes the clock quantity; one
final newline is tolerated by the whole-text match. -/
def primaryParts? (v : List Char) : Option (Int × Int) :=
  let w := dropFinalNewline v
  match splitFirstSpace w with
  | some (before, after) =>
      match signedIntToInt? before with
      | some d =>
          match parseClockMicros? (stripUnit after) with
          | some t => some (d * 86400 * 1000000, t)
          | none => none
      | none =>
          match parseClockMicros? w with   -- the space is not a day separator
          | some t => some (0, t)
          | none => none
  | none =>
      match parseClockMicros? w with
      | some t => some (0, t)
      | none => none

/-- Decode the PRIMARY clock notation into microseconds, or `none` if the text
is not in that notation. The day count's microseconds are added to the
(independently signed) clock microseconds. -/
def primaryFormatMicros (v : List Char) : Option Int :=
  match primaryParts? v with
  | some (dus, tus) => some (dus + tus)
  | none => none

/-- Side condition 2 of the model's domain: every microsecond quantity the
primary notation builds — the day part, the signed clock part, and their sum —
lands inside the range a duration value can hold. Text whose primary notation
does not apply is unconstrained by this condition. -/
def primaryInRange (v : List Char) : Bool :=
  match primaryParts? v with
  | some (dus, tus) => inUsRange dus && inUsRange tus && inUsRange (dus + tus)
  | none => true
-- pure-end

-- post-conditions-start
/-- The interpreted duration is fully pinned to the input text: it is the PRIMARY
notation's microseconds when that notation applies, and otherwise the secondary
notation's interpretation. No output component is left free. Asserted on the
model's domain — ASCII text whose primary quantities are representable (the two
side conditions stated in the header). -/
def problem_spec_durationFromText (v : List Char) (result : Option Int) : Prop :=
  asciiText v = true →
  primaryInRange v = true →
  result =
    (match primaryFormatMicros v with
     | some us => some us
     | none => fallbackFormatMicros v)
-- post-conditions-end

-- impl-start
/-- Decode an OPTIONALLY-signed seconds field with optional `.f`; the fractional
microseconds inherit the seconds field's sign (pre-fix behavior). -/
def parseSecMicroBug? (cs : List Char) : Option (Int × Int) :=
  match splitOnChar '.' cs with
  | [secs] =>
      match signedIntToInt? secs with
      | some s => some (s, 0)
      | none => none
  | [secs, frac] =>
      if frac.isEmpty || frac.length > 12 || !frac.all isDigitC then none
      else
        let micro6 := (frac.take 6) ++ List.replicate (6 - min 6 frac.length) '0'
        match signedIntToInt? secs, digitsToNat? micro6 with
        | some s, some us =>
            let neg := "-".toList.isPrefixOf secs
            some (s, if neg then -(us : Int) else (us : Int))
        | _, _ => none
  | _ => none

/-- Pre-fix clock decoder: NO single leading sign; every field is independently
signed and contributes with its own sign (the bug). -/
def parseClockMicrosBug? (body : List Char) : Option Int :=
  match splitOnChar ':' body with
  | [a] =>
      match parseSecMicroBug? a with
      | some (s, us) => some (s * 1000000 + us)
      | none => none
  | [m, a] =>
      match signedIntToInt? m, parseSecMicroBug? a with
      | some mm, some (s, us) => some (mm * 60 * 1000000 + s * 1000000 + us)
      | _, _ => none
  | [h, m, a] =>
      match signedIntToInt? h, signedIntToInt? m, parseSecMicroBug? a with
      | some hh, some mm, some (s, us) =>
          some (hh * 3600 * 1000000 + mm * 60 * 1000000 + s * 1000000 + us)
      | _, _, _ => none
  | _ => none

def primaryFormatMicrosBug (v : List Char) : Option Int :=
  match splitFirstSpace v with
  | some (before, after) =>
      match signedIntToInt? before with
      | some d =>
          match parseClockMicrosBug? (stripUnit after) with
          | some t => some (d * 86400 * 1000000 + t)
          | none => none
      | none => parseClockMicrosBug? v
  | none => parseClockMicrosBug? v

def implementation_durationFromText (v : List Char) : Option Int := Id.run do
  -- PRE-FIX skeleton: the primary notation allows per-field signs and has no
  -- single leading sign, so a leading minus does not negate the whole clock.
  match primaryFormatMicrosBug v with
  | some us => return some us
  | none => return fallbackFormatMicros v
-- impl-end

-- proof-start
theorem correct_durationFromText : ∀ (v : List Char),
    problem_spec_durationFromText v (implementation_durationFromText v) := by
  intro v
  unfold problem_spec_durationFromText implementation_durationFromText
  intro _ _
  simp only [Id.run]
  cases primaryFormatMicros v <;> rfl   -- gold proof body; UNCLOSABLE vs the pre-fix impl (G-DIFF)
-- proof-end
