import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee is consumed: the cluster centers are an INPUT to the
-- modeled computation (produced upstream by a clustering routine that this
-- behavior does not change). The bin-edge construction is modeled deeply below.
-- axioms-end

-- pure-start
/-- Consecutive pairwise midpoints of a list:
`midpoints [c₀, c₁, …, cₙ] = [(c₀+c₁)/2, (c₁+c₂)/2, …]`.
Models the elementwise average of a sequence with its tail. -/
def midpoints : List Rat → List Rat
  | a :: b :: rest => (a + b) / 2 :: midpoints (b :: rest)
  | _ => []
-- pure-end

-- post-conditions-start
/-- The interior bin boundaries are the consecutive midpoints of the cluster
centers taken in ascending order, bracketed by the column minimum and maximum.
The result must be realizable as a reordering of the centers into ascending
order: there exists a sorted permutation `cs` of `centers` whose consecutive
midpoints, bracketed by `colMin`/`colMax`, equal the result. This forces the
boundaries to be derived from order-normalized centers, the property the
downstream digitization step requires. -/
def problem_spec_binEdges (colMin colMax : Rat) (centers result : List Rat) : Prop :=
  ∃ cs : List Rat,
    cs.Perm centers ∧ List.Sorted (· ≤ ·) cs ∧
    result = colMin :: (midpoints cs ++ [colMax])
-- post-conditions-end

-- impl-start
def implementation_binEdges (colMin colMax : Rat) (centers : List Rat) : List Rat :=
  Id.run do
    let mut cs := centers
    return colMin :: (midpoints cs ++ [colMax])
-- impl-end

-- proof-start
theorem correct_binEdges :
    ∀ (colMin colMax : Rat) (centers : List Rat),
      problem_spec_binEdges colMin colMax centers
        (implementation_binEdges colMin colMax centers) := by
  sorry
-- proof-end
