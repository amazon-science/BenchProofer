import Mathlib
-- imports-end

/-!
Selecting which interior/boundary separator segments are drawn between adjacent
color bands of a one-dimensional color strip.

The strip carries a list of candidate separator rows, one per band boundary in
order from the lower end to the upper end. Three boolean settings govern the
selection:

* whether boundary separators are drawn at all;
* whether the lower end of the strip is open (so its terminal separator is a
  genuine boundary that must be kept);
* whether the upper end of the strip is open (likewise for the upper terminal
  separator).

When separators are disabled the selection is empty. When enabled, every
separator is kept except those terminal separators sitting at a *closed* end.
-/

-- axioms-start
-- No unchanged callee is invoked as an opaque operation inside the model: the
-- two end-openness settings are passed in as boolean inputs, and the segment
-- carrier is the input list. Hence no `opaque` decls and no consumed axioms.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- `drawEdges` enables separators; `openLower`/`openUpper` say whether the
respective end of the strip is open. `segs` are the candidate separator rows in
order. The kept selection drops a terminal separator only at a *closed* end:
the front separator is dropped iff the lower end is closed, and the back
separator is dropped iff the upper end is closed; if separators are disabled the
selection is empty. -/
def problem_spec_colorbarEdgeSegments {α : Type}
    (drawEdges openLower openUpper : Bool) (segs : List α) (result : List α) : Prop :=
  result =
    (if drawEdges then
        (segs.take (if openUpper then segs.length else segs.length - 1)).drop
          (if openLower then 0 else 1)
      else [])
-- post-conditions-end

-- impl-start
def implementation_colorbarEdgeSegments {α : Type}
    (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
  if !drawEdges then
    return []
  let startIdx := if openLower then 0 else 1
  let endIdx := if openUpper then segs.length else segs.length - 1
  return (segs.take endIdx).drop startIdx
-- impl-end

-- proof-start
theorem correct_colorbarEdgeSegments :
    ∀ {α : Type} (drawEdges openLower openUpper : Bool) (segs : List α),
      problem_spec_colorbarEdgeSegments drawEdges openLower openUpper segs
        (implementation_colorbarEdgeSegments drawEdges openLower openUpper segs) := by
  intro α drawEdges openLower openUpper segs
  unfold problem_spec_colorbarEdgeSegments implementation_colorbarEdgeSegments
  cases drawEdges <;> rfl
-- proof-end
