import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- Separator-line selection for a colour scale rendered as a strip of coloured
   cells with optional dividing lines between adjacent cells.

   The full list of candidate dividers has one entry per internal cell
   boundary of the assembled strip, in order from one end to the other. When
   dividing lines are disabled the selection is empty. When enabled, the
   selection is the contiguous run of boundaries that lie strictly between the
   two outermost cells UNLESS an end is "open" (the scale continues past that
   end with a pointed/extended cap), in which case the boundary touching that
   open end is also kept. So an open lower end keeps the first boundary, and an
   open upper end keeps the last boundary; a closed end drops the boundary
   adjacent to it.

   The model below performs that selection abstractly as a positional slice of
   the candidate list; no callee is axiomatized because the selection is the
   only computation (the open-end flags are plain booleans supplied by the
   caller). -/

-- axioms-start
-- axioms-end

-- pure-start
/- A single candidate divider, modelled by its flattened coordinate entries
   (the operation is purely positional, so the segment's content is opaque to
   the selection). -/
abbrev Seg := List Float

/- The lower start index: 0 when the lower end is open (keep the first
   boundary), 1 when it is closed (drop the boundary adjacent to the closed
   lower end). -/
def startIdx (extLow : Bool) : Nat := if extLow then 0 else 1

/- The upper end index (exclusive): the full length when the upper end is open
   (keep the last boundary), one less when it is closed (drop the boundary
   adjacent to the closed upper end). -/
def endIdx (extUp : Bool) (n : Nat) : Nat := if extUp then n else n - 1

/- The selected dividers: empty when dividing lines are disabled; otherwise the
   contiguous sub-run of the candidate list from `startIdx` (inclusive) to
   `endIdx` (exclusive). Expressed as drop-then-take so it is a faithful
   positional slice over a `List`. -/
def selectSeg (segs : List Seg) (drawEdges : Bool) (extLow : Bool) (extUp : Bool) :
    List Seg :=
  if drawEdges then
    (segs.drop (startIdx extLow)).take (endIdx extUp segs.length - startIdx extLow)
  else
    []

@[grind] lemma selectSeg_eq (segs : List Seg) (drawEdges extLow extUp : Bool) :
    selectSeg segs drawEdges extLow extUp =
      (if drawEdges then
        (segs.drop (startIdx extLow)).take (endIdx extUp segs.length - startIdx extLow)
      else []) := rfl
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose which dividing lines between adjacent colour cells are drawn.
   `segs` is the ordered list of candidate dividers (one per internal boundary
   of the assembled strip); `drawEdges` enables the lines at all; `extLow` /
   `extUp` say whether the lower / upper end of the scale is open (extended past
   the outermost cell with a pointed/rectangular cap). The result is the subset
   of candidates that are actually drawn. -/
method selectSegM (segs : List Seg) (drawEdges : Bool) (extLow : Bool) (extUp : Bool)
    return (out : List Seg)
  ensures out = selectSeg segs drawEdges extLow extUp
  do
    -- impl-start
    -- Lower bound of the kept run: keep the boundary at the open lower end,
    -- otherwise start one in (drop the boundary touching a closed lower end).
    let s : Nat := if extLow then 0 else 1
    -- Upper bound (exclusive): keep through the boundary at the open upper end,
    -- otherwise stop one short (drop the boundary touching a closed upper end).
    let e : Nat := if extUp then segs.length else segs.length - 1
    -- The contiguous slice [s, e) of the candidate list.
    let selected : List Seg := (segs.drop s).take (e - s)
    let out : List Seg := if drawEdges then selected else []
    return out
    -- impl-end

prove_correct selectSegM by
  loom_solve
  simp [selectSeg, startIdx, endIdx]
