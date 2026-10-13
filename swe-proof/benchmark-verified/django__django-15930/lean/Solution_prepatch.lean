import Mathlib
-- imports-end

/-!
Rendering a single branch of a searched conditional expression.

A searched conditional expression is built from a sequence of branches, each
pairing a guard predicate with a result. When one branch is turned into its
textual form, two fragments are produced and combined into a constant template
`"WHEN <guard> THEN <result>"`: the guard fragment, obtained by rendering the
branch's predicate, and the result fragment.

A predicate that is satisfied by every row has an empty rendered guard fragment
in some contexts (a top-level filter simply drops the predicate). Spliced into a
branch template, an empty guard fragment would leave the template malformed —
the `WHEN` keyword would be immediately followed by `THEN` with no predicate
between them. The desired behavior is therefore: when the rendered guard fragment
is empty, substitute the fragment of an always-satisfied predicate (a stand-in
that renders to a non-empty, unconditionally-true fragment together with its
bound parameters); otherwise keep the rendered guard fragment and its parameters
unchanged.

The choice is governed by:

  * `conditionSql` — the rendered guard fragment for this branch;
  * `conditionParams` — the parameters bound by that guard fragment;
  * `trueSql` — the rendered fragment of an always-satisfied stand-in predicate;
  * `trueParams` — the parameters bound by that stand-in fragment.

The modeled value is the `(guard fragment, guard parameters)` pair that the
branch ultimately splices into its template.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Rendering the
-- branch predicate and rendering the always-satisfied stand-in predicate are
-- performed elsewhere; their observable results (a fragment string paired with
-- its bound parameters) enter here as plain data. The only operation modeled is
-- the emptiness test on the guard fragment and the wholesale substitution of the
-- stand-in pair. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- (No shared pure helper needed: the decision is a single conditional on the
-- guard fragment's emptiness.)
-- pure-end

-- post-conditions-start
/-- The rendered guard pair is fully pinned to the inputs:

  * when the rendered guard fragment is empty, the result is exactly the
    always-satisfied stand-in pair `(trueSql, trueParams)`;
  * otherwise the result is exactly the original guard pair
    `(conditionSql, conditionParams)`, unchanged.

Both cases together determine the result for every input, so neither component of
the output is left free. -/
def problem_spec_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α)
    (result : String × List α) : Prop :=
  (conditionSql = "" → result = (trueSql, trueParams)) ∧
  (conditionSql ≠ "" → result = (conditionSql, conditionParams))
-- post-conditions-end

-- impl-start
def implementation_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α) : String × List α := Id.run do
  let mut condSql := conditionSql
  let mut condParams := conditionParams
  return (condSql, condParams)
-- impl-end

-- proof-start
theorem correct_resolveBranchCondition {α : Type}
    (conditionSql : String) (conditionParams : List α)
    (trueSql : String) (trueParams : List α) :
    problem_spec_resolveBranchCondition conditionSql conditionParams trueSql trueParams
      (implementation_resolveBranchCondition conditionSql conditionParams trueSql trueParams) := by
  sorry
-- proof-end
