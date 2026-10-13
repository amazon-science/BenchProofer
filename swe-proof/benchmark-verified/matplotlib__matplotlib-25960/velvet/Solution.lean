import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The grid-position arithmetic is modeled DEEPLY in
--  the `pure` region — `cellSize`/`cellPitch`/`axisExtents` ARE the layout
--  computation, an A-reference validated == the real grid-position routine by
--  axiom_check.py (G-AX). No consumed axiom borrows soundness from it.)
-- axioms-end

-- pure-start
/- A row (or column) of `n` equally-sized cells is laid out along the unit
   interval `[0, 1]`, leaving a uniform gap between adjacent cells. The gap is
   expressed as a fraction `s` of a single cell's size: between every pair of
   neighbouring cells a separation of `s` times the cell size is inserted.

   With `n` cells and `n - 1` such gaps the interval must accommodate a total
   length of `n + s·(n-1)` cell-sizes, so each cell occupies a fraction

       cellSize n s = 1 / (n + s·(n-1)).

   For `n ≥ 1` the denominator is at least `1`, so the size is well defined and
   strictly positive. With no gap (`s = 0`) this is the even split `1 / n`. -/
def cellSize (n : Nat) (s : Rat) : Rat :=
  1 / ((n : Rat) + s * ((n : Rat) - 1))

/- The centre-to-centre stride from one cell's low edge to the next: a full
   cell plus the separation that follows it, i.e. `cellSize · (1 + s)`. When the
   gap fraction is zero this collapses to the cell size itself (cells abut). -/
def cellPitch (n : Nat) (s : Rat) : Rat :=
  cellSize n s * (1 + s)

/- The closed extents `(low, high)` of every cell of the axis, in order from the
   low end. Cell `i` starts at `i` strides in and spans one cell size:

       low i  = i · cellPitch n s,
       high i = low i + cellSize n s.

   The result is the per-cell expansion of the index range `0 .. n-1`: exactly
   `n` extents, the `i`-th being the interval reserved for cell `i`. -/
def axisExtents (n : Nat) (s : Rat) : List (Rat × Rat) :=
  (List.range n).map
    (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Lay out `n` equally-sized cells along the unit axis with a uniform gap of
   fraction `s` between neighbours, and return each cell's `(low, high)` extent
   in order from the low end.

   The guarantees pin the behaviour the issue demands — that the requested gap
   actually reserves space between cells, instead of being silently dropped so
   the cells abut:

   - there are exactly `n` extents, one per cell (`out.length = n`);
   - the `i`-th extent is exactly `(i · cellPitch n s, i · cellPitch n s +
     cellSize n s)`. Because the pitch carries the `(1 + s)` factor, a non-zero
     gap genuinely separates consecutive cells — `high` of cell `i` is strictly
     below `low` of cell `i+1` whenever `s > 0`. An even split that ignores `s`
     cannot satisfy this for any positive gap.

   `n` and `s` are read-only inputs (not `mut`); the operation derives the
   extent list and mutates nothing (directive 5). The extents are modeled as
   exact rationals (`Rat`): the discriminating behaviour is the proportional
   placement of cell edges, an exact ratio computation that is
   precision-independent (the gap fraction multiplies, it never accumulates
   round-off across cells), so an exact ordered carrier is faithful. -/
method axisCellExtents (n : Nat) (s : Rat) return (out : List (Rat × Rat))
  require n ≥ 1
  require s ≥ 0
  ensures out.length = n
  ensures out = axisExtents n s
  do
    -- impl-start
    let extents := (List.range n).map
      (fun (i : Nat) => ((i : Rat) * cellPitch n s, (i : Rat) * cellPitch n s + cellSize n s))
    return extents
    -- impl-end

prove_correct axisCellExtents by
  loom_solve
  simp [axisExtents]
