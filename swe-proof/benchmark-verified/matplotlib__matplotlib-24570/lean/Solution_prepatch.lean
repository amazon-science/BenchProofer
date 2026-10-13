import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only outside helper
-- the modeled branch uses is a maximum over a non-empty list of rationals, which
-- is reproduced concretely below (`maxList`); the anchor-membership validation is
-- carried as a binder precondition (`validAlign`). The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Maximum of a list of rationals (the empty list yields `0`; callers always
pass a non-empty list). Reproduces the `max(… for … in …)` reduction used to
resolve the packing extent. -/
def maxList : List Rat → Rat
  | []      => 0
  | x :: xs => xs.foldl max x

/-- The set of anchor keywords accepted by the alignment helper. Used as the
binder precondition (the real code validates the keyword and rejects others). -/
def validAlign (align : String) : Prop :=
  align = "baseline" ∨ align = "left" ∨ align = "top" ∨
  align = "right" ∨ align = "bottom" ∨ align = "center"
-- pure-end

-- post-conditions-start
/-- Aligns boxes given by their `(height, descent)` pairs within an intended total
`height`, returning `(resolvedHeight, descent, offsets)` along the alignment axis.
Each anchor selects one offset rule and is pinned completely:

* `baseline` — the total is recomputed from the per-box extents, the descent is
  the maximal box descent, and every offset is zero;
* `left`/`bottom` — descent zero, each offset is that box's own descent;
* `right`/`top` — descent zero, each offset places the box flush against the far
  edge (`height - boxHeight + descent`);
* `center` — descent zero, each offset centers the box (`(height - boxHeight)/2 +
  descent`).

The resolved height equals the input `height` for every anchor except `baseline`;
the offsets list has the same length and order as the input. -/
def problem_spec_alignedOffsets
    (hdList : List (Rat × Rat)) (height : Rat) (align : String)
    (result : Rat × Rat × List Rat) : Prop :=
  (align = "baseline" →
      result.1 = maxList (hdList.map (fun hd => hd.1 - hd.2))
                   + maxList (hdList.map (fun hd => hd.2))
    ∧ result.2.1 = maxList (hdList.map (fun hd => hd.2))
    ∧ result.2.2 = hdList.map (fun _ => (0 : Rat)))
  ∧ (align = "left" ∨ align = "bottom" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => hd.2))
  ∧ (align = "right" ∨ align = "top" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => height - hd.1 + hd.2))
  ∧ (align = "center" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
-- post-conditions-end

-- impl-start
def implementation_alignedOffsets
    (hdList : List (Rat × Rat)) (height : Rat) (align : String) :
    Rat × Rat × List Rat := Id.run do
  -- Pre-patch (buggy): the "top" anchor selects the own-descent rule and the
  -- "bottom" anchor selects the far-edge rule, the reverse of the intended
  -- vertical alignment.
  if align == "baseline" then
    let heightDescent := maxList (hdList.map (fun hd => hd.1 - hd.2))
    let descent := maxList (hdList.map (fun hd => hd.2))
    let h := heightDescent + descent
    return (h, descent, hdList.map (fun _ => (0 : Rat)))
  else if align == "left" || align == "top" then
    return (height, 0, hdList.map (fun hd => hd.2))
  else if align == "right" || align == "bottom" then
    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
  else
    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
-- impl-end

-- proof-start
theorem correct_alignedOffsets :
    ∀ (hdList : List (Rat × Rat)) (height : Rat) (align : String),
    validAlign align →
    problem_spec_alignedOffsets hdList height align
      (implementation_alignedOffsets hdList height align) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
