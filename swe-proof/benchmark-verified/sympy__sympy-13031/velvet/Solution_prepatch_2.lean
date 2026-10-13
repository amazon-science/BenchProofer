import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Stacking two sparse rectangular blocks edge-to-edge.

   A block has a row count, a column count, and a sparse set of stored entries
   (an entry pins one (row, column) cell to a value; absent cells are zero).

   Horizontal stacking places the second block immediately to the RIGHT of the
   first: the combined block is as tall as the operands and as wide as the SUM
   of their widths, with the second block's stored cells shifted right by the
   first block's width. Vertical stacking is the transpose situation: the second
   block goes BELOW the first, the combined height is the SUM of the heights, and
   the second block's cells shift down by the first block's height.

   A degenerate block — one whose width (for horizontal stacking) or height (for
   vertical stacking) is zero — contributes no cells but STILL contributes its
   measured extent: stacking such a block must accumulate the running width/height
   exactly as a non-degenerate block would, never collapse the result to the shape
   of the other operand alone. This is the property the model pins. -/

-- axioms-start
/- No callee is axiomatized. The stacking behavior is pure shape-and-cell
   arithmetic computed entirely from the two operand blocks (extent addition plus
   a coordinate shift of the second block's stored cells); there is no unchanged
   repository callee whose contract the proof must assume. Both legs of the result
   construction are concrete (refinement.md: every row R or I). Soundness of the
   shape arithmetic is exercised executably against the real callees by
   conformance_check.py. -/
-- axioms-end

-- pure-start
/- A rectangular block: `rows` × `cols`, with `entries` the stored (nonzero)
   cells as `((i, j), v)`. The carrier abstracts over storage form — a value is
   recorded the same way whether the real object stores it densely or sparsely. -/
structure Block where
  rows : Nat
  cols : Nat
  entries : List ((Nat × Nat) × Int)
  deriving DecidableEq, Inhabited, Repr

/- Shift a stored cell to the right by `n` columns (used when a block is placed
   to the right of another of width `n`). -/
def shiftRight (n : Nat) (e : (Nat × Nat) × Int) : (Nat × Nat) × Int :=
  ((e.1.1, e.1.2 + n), e.2)

/- Shift a stored cell down by `n` rows (used when a block is placed below
   another of height `n`). -/
def shiftDown (n : Nat) (e : (Nat × Nat) × Int) : (Nat × Nat) × Int :=
  ((e.1.1 + n, e.1.2), e.2)

/- The block obtained by placing `B` immediately to the right of `A`. Width is
   the SUM of the two widths (so a zero-width `A` still contributes its — zero —
   width and the running total is preserved, never replaced by `B`'s width
   alone). Height is `A`'s, except a zero-width `A` carries no height of its own
   and adopts `B`'s. `B`'s cells move right by `A`'s width. -/
def hstackBlock (A B : Block) : Block :=
  { rows := if A.cols = 0 then B.rows else A.rows,
    cols := A.cols + B.cols,
    entries := A.entries ++ B.entries.map (shiftRight A.cols) }

/- The block obtained by placing `B` immediately below `A`. Height is the SUM of
   the two heights; width is `A`'s, except a zero-height `A` adopts `B`'s width.
   `B`'s cells move down by `A`'s height. -/
def vstackBlock (A B : Block) : Block :=
  { rows := A.rows + B.rows,
    cols := if A.rows = 0 then B.cols else A.cols,
    entries := A.entries ++ B.entries.map (shiftDown A.rows) }

@[grind] lemma hstackBlock_eq (A B : Block) :
    hstackBlock A B =
      { rows := if A.cols = 0 then B.rows else A.rows,
        cols := A.cols + B.cols,
        entries := A.entries ++ B.entries.map (shiftRight A.cols) } := rfl

@[grind] lemma vstackBlock_eq (A B : Block) :
    vstackBlock A B =
      { rows := A.rows + B.rows,
        cols := if A.rows = 0 then B.cols else A.cols,
        entries := A.entries ++ B.entries.map (shiftDown A.rows) } := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Place block `B` immediately to the right of block `A`. `A` and `B` are
   read-only operands (neither is `mut`; the result is a fresh block and the
   inputs are unchanged). The operands are compatible when their heights match,
   OR when `A` is degenerate in width — a zero-width block can be stacked beside
   any block, taking on that block's height. The result must have width equal to
   the SUM of the two widths in every admissible case, so a zero-width `A` never
   collapses the result to `B`'s width alone. -/
method stackHorizontally (A : Block) (B : Block) return (out : Block)
  require A.cols = 0 ∨ A.rows = B.rows
  ensures out = hstackBlock A B
  do
    -- impl-start
    -- When `A` is width-zero and the heights disagree, `A` is first re-measured
    -- to `B`'s height (it has no cells to carry), then stacked — yielding `B`'s
    -- content at the full summed width.  Otherwise the heights already line up
    -- and `B`'s columns are appended after `A`'s.  Both legs accumulate the
    -- width as the SUM `A.cols + B.cols`.
    if A.cols = 0 ∧ A.rows ≠ B.rows then
      return { rows := B.rows, cols := A.cols + B.cols,
               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
    else
      return { rows := A.rows, cols := A.cols + B.cols,
               entries := A.entries ++ B.entries.map (shiftRight A.cols) }
    -- impl-end

prove_correct stackHorizontally by
  loom_solve

/- Place block `B` immediately below block `A`. `A` and `B` are read-only
   operands (neither is `mut`). The operands are compatible when their widths
   match, OR when `A` is degenerate in height. The result must have height equal
   to the SUM of the two heights in every admissible case, so a zero-height `A`
   never collapses the result to `B`'s height alone. -/
method stackVertically (A : Block) (B : Block) return (out : Block)
  require A.rows = 0 ∨ A.cols = B.cols
  ensures out = vstackBlock A B
  do
    -- impl-start
    -- Pre-patch skeleton (buggy): ANY measure-zero `A` (zero height OR zero
    -- width) short-circuits and the result is taken to be `B` alone. When `A`
    -- has zero width but nonzero height this DROPS `A`'s height: the result
    -- keeps only `B`'s height instead of the summed height.  The frozen spec
    -- requires the summed height (vstackBlock), so prove_correct MUST fail.
    if A.rows = 0 ∨ A.cols = 0 then
      return { rows := B.rows, cols := B.cols, entries := B.entries }
    else
      return { rows := A.rows + B.rows, cols := A.cols,
               entries := A.entries ++ B.entries.map (shiftDown A.rows) }
    -- impl-end

prove_correct stackVertically by
  loom_solve
