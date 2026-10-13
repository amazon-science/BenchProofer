import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. Both modeled procedures
-- assemble their result text directly from already-rendered fragments by
-- straight-line code; the per-element rendering recursion supplies the inputs
-- and is not part of the modeled joining behavior, so no callee contract is
-- consumed. The proof agent may add `_prop` axioms only if a proof obligation
-- needs one.
-- axioms-end

-- pure-start
/-- The shape of a subscription index as seen by the text renderer.

* `elementTuple elts` — the index is a multi-component grouping, carrying the
  already-rendered text of each component (`elts`); by construction it is
  non-empty and carries no spread component.
* `plain rendered` — any other index, carrying its own already-rendered text. -/
inductive IndexForm where
  | elementTuple (elts : List (List Char))
  | plain (rendered : List Char)
-- pure-end

-- post-conditions-start
/-- Specification of rendering a comma-separated display of a sequence of
already-rendered component texts (`elts`).

A non-empty sequence is shown as its components joined by `", "` and enclosed in
a matching pair of round brackets, so that the display is a single grouped unit.
An empty sequence is shown as the empty grouping `"()"`. The whole result is
determined by `elts` alone. -/
def problem_spec_tupleDisplay
    (elts : List (List Char)) (result : List Char) : Prop :=
  result =
    (if elts = [] then ['(', ')']
     else ['('] ++ List.intercalate [',', ' '] elts ++ [')'])
-- post-conditions-end

-- impl-start
def implementation_tupleDisplay
    (elts : List (List Char)) : List Char := Id.run do
  if elts ≠ [] then
    return ['('] ++ List.intercalate [',', ' '] elts ++ [')']
  else
    return ['(', ')']
-- impl-end

-- proof-start
theorem correct_tupleDisplay : ∀ (elts : List (List Char)),
    problem_spec_tupleDisplay elts (implementation_tupleDisplay elts) := by
  intro elts
  unfold problem_spec_tupleDisplay implementation_tupleDisplay
  by_cases h : elts = []
  · simp [h, Id.run, pure]
  · simp [h, Id.run, pure]
-- proof-end

-- post-conditions-start
/-- Specification of rendering a subscription `value[index]` to text.

`valueStr` is the already-rendered text of the subscripted value and `idx` is
the index. The result is `valueStr`, then `'['`, then the index text, then `']'`.
When the index is a multi-component grouping, its components are listed directly
between the brackets — joined by `", "`, with no extra surrounding grouping —
so each component is a separate subscript argument. Any other index contributes
its own rendered text unchanged. -/
def problem_spec_subscription
    (valueStr : List Char) (idx : IndexForm) (result : List Char) : Prop :=
  result =
    valueStr ++ ['['] ++
      (match idx with
       | .elementTuple elts => List.intercalate [',', ' '] elts
       | .plain rendered => rendered)
    ++ [']']
-- post-conditions-end

-- impl-start
def implementation_subscription
    (valueStr : List Char) (idx : IndexForm) : List Char := Id.run do
  match idx with
  | .elementTuple elts =>
      let inner := List.intercalate [',', ' '] elts
      return valueStr ++ ['['] ++ inner ++ [']']
  | .plain rendered =>
      return valueStr ++ ['['] ++ rendered ++ [']']
-- impl-end

-- proof-start
theorem correct_subscription : ∀ (valueStr : List Char) (idx : IndexForm),
    problem_spec_subscription valueStr idx
      (implementation_subscription valueStr idx) := by
  intro valueStr idx
  unfold problem_spec_subscription implementation_subscription
  cases idx with
  | elementTuple elts => simp [Id.run, pure]
  | plain rendered => simp [Id.run, pure]
-- proof-end
