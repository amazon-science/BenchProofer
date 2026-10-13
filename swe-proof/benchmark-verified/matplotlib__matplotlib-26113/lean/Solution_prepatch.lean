import Mathlib
-- imports-end

/-!
Reducing per-cell value collections to a binned grid.

A 2-D plotting routine groups input points into grid cells. When an auxiliary
value array is supplied, every grid cell accumulates the values of the points
that fall into it, and each cell is summarised to a single number by a
user-supplied reduction function. A cell that does not hold enough contributing
points is left empty (marked with the empty/absent sentinel) instead of being
summarised.

The threshold is a single count parameter shared by the whole grid. The desired
rule is:

  * a cell is summarised (its reduction value is produced) exactly when the
    number of points it holds is AT LEAST the threshold;
  * otherwise the cell is left empty.

In particular, with a threshold of `1`, every cell that holds one or more points
is summarised; with a threshold of `0`, every cell — including empty ones — is
summarised. The threshold counts points the same way whether or not auxiliary
values are present: a cell holding exactly the threshold number of points is
summarised, not skipped.
-/

-- axioms-start
-- The per-cell reduction is an UNCHANGED, user-supplied callee: it maps a cell's
-- collection of contributing values to a single summary number. It is applied
-- identically in the specification and the implementation and the result pins no
-- output component on its own, so no property of it is asserted (no `_prop`
-- axiom); only its signature is declared so it can appear in the executable impl.
opaque reduceC : List Float → Float
-- axioms-end

-- pure-start
/-- The summary of one grid cell. `cells` lists, per grid cell, the collection of
contributing values; `mincnt` is the shared count threshold. A cell is summarised
(its reduction value, wrapped in `some`) exactly when it holds at least `mincnt`
points; otherwise it is left empty (`none`). -/
def cellSummary (mincnt : Int) (acc : List Float) : Option Float :=
  if (acc.length : Int) ≥ mincnt then some (reduceC acc) else none
-- pure-end

-- post-conditions-start
/-- The binned grid is, cell by cell, the summary of that cell's collection under
the shared threshold: every cell is summarised iff it holds at least `mincnt`
points, and the grid preserves the order and count of the input cells. -/
def problem_spec_hexbinAccum
    (cells : List (List Float)) (mincnt : Int) (result : List (Option Float)) : Prop :=
  result = cells.map (cellSummary mincnt)
-- post-conditions-end

-- impl-start
def implementation_hexbinAccum
    (cells : List (List Float)) (mincnt : Int) : List (Option Float) := Id.run do
  let mut accum : List (Option Float) := []
  for acc in cells do
    -- a cell is summarised only when it holds STRICTLY MORE than the threshold
    -- number of points, so a cell holding exactly the threshold is left empty
    if (acc.length : Int) > mincnt then
      accum := accum ++ [some (reduceC acc)]
    else
      accum := accum ++ [none]
  return accum
-- impl-end

-- proof-start
theorem correct_hexbinAccum :
    ∀ (cells : List (List Float)) (mincnt : Int),
      problem_spec_hexbinAccum cells mincnt
        (implementation_hexbinAccum cells mincnt) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
