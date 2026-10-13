import Mathlib
-- imports-end

/-!
Rendering a (possibly negated) existence test over a subquery into an SQL
fragment together with its bind parameters.

An existence test asks whether a subquery matches at least one row; it can also
be used in negated form (whether the subquery matches NO row). Rendering it
delegates to a generic subquery renderer, which produces an SQL fragment and a
list of bind parameters — but that renderer may instead signal that the subquery
is statically known to match no rows at all (an "empty-result" signal).

The desired behavior:

* When the inner renderer succeeds with a fragment `sql` and parameters
  `params`, the rendered predicate is `sql` (parameters unchanged) when the test
  is not negated, and the negation of that fragment (its textual `NOT`-prefix)
  with the SAME parameters when it is negated.
* When the inner renderer signals that the subquery matches no rows, a non-negated
  existence test is itself unsatisfiable, so the empty-result signal must
  propagate. A negated existence test, however, is then trivially satisfied by
  every row, so it must render as the empty fragment with no parameters — a
  no-op contribution that leaves the surrounding predicate intact rather than
  discarding it.

`negated` says whether the test is in its negated form. `inner` is the outcome of
the inner subquery renderer: either a successful `(sql, params)` pair, or the
empty-result signal. The result is the rendered `(sql, params)` pair, or the
empty-result signal propagated.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The generic subquery
-- renderer that produces the inner fragment (or fails) is NOT modeled as an
-- opaque callee: its outcome is taken as the boundary input
-- `inner : Except RenderFailure (String × List String)` (`.ok (sql, params)` for
-- a successful render; `.error .emptyResult` for the dedicated empty-result
-- signal; `.error .other` for any other failure). The modeled function is the
-- pure dispatch over `(negated, inner)`, so no callee contract is required and no
-- `axiom _prop` is consumed.
-- axioms-end

-- pure-start
/-- The ways the inner subquery renderer can fail.
  * `emptyResult` — it signals the subquery is statically known to match no rows;
  * `other`       — any other failure (kept distinct: it is never special-cased). -/
inductive RenderFailure where
  | emptyResult
  | other
  deriving DecidableEq, Repr

-- The rendered SQL is modeled as a `String`; its bind parameters as a
-- `List String` of opaque parameter tokens (the dispatch never inspects them, it
-- only passes them through unchanged or replaces them by the empty list).
-- pure-end

-- post-conditions-start
/-- The rendered predicate is fully determined by `negated` and the inner
renderer outcome `inner`:
  * inner success `(sql, params)` → `.ok` of `(sql, params)` unchanged when not
    negated, and `("NOT " ++ sql, params)` (same parameters) when negated;
  * inner empty-result signal → the empty fragment with no parameters
    (`.ok ("", [])`) when negated, and the SAME signal propagated
    (`.error .emptyResult`) when not negated;
  * any other inner failure → propagated unchanged (`.error .other`), regardless
    of `negated` — only the empty-result signal is ever special-cased. -/
def problem_spec_compileExistenceCheck
    (negated : Bool) (inner : Except RenderFailure (String × List String))
    (result : Except RenderFailure (String × List String)) : Prop :=
  match inner with
  | .error .emptyResult =>
      result = (if negated then .ok ("", []) else .error .emptyResult)
  | .error .other =>
      result = .error .other
  | .ok (sql, params) =>
      result = .ok ((if negated then "NOT " ++ sql else sql), params)
-- post-conditions-end

-- impl-start
def implementation_compileExistenceCheck
    (negated : Bool) (inner : Except RenderFailure (String × List String)) :
    Except RenderFailure (String × List String) := Id.run do
  match inner with
  | .error .emptyResult =>
      if negated then
        return .ok ("", [])
      else
        return .error .emptyResult
  | .error .other =>
      return .error .other
  | .ok (sql, params) =>
      let mut sql := sql
      if negated then
        sql := "NOT " ++ sql
      return .ok (sql, params)
-- impl-end

-- proof-start
theorem correct_compileExistenceCheck :
    ∀ (negated : Bool) (inner : Except RenderFailure (String × List String)),
      problem_spec_compileExistenceCheck negated inner
        (implementation_compileExistenceCheck negated inner) := by
  intro negated inner
  unfold problem_spec_compileExistenceCheck implementation_compileExistenceCheck
  match inner with
  | .error .emptyResult => cases negated <;> rfl
  | .error .other => rfl
  | .ok (sql, params) => cases negated <;> rfl
-- proof-end
