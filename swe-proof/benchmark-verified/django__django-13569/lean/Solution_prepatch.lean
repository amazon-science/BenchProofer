import Mathlib
-- imports-end

/-!
Grouping columns contributed by a non-deterministic ordering expression.

When an aggregated result set is also ordered, each ordering term is asked which
underlying stored columns it adds to the grouping of the result. A plain column
reference contributes that column; an aggregate contributes the columns of its
operands. But an ordering term that is a non-deterministic value generator — a
random-value function with arity zero and therefore no underlying stored column —
has nothing to group on. Asking such a term for its grouping columns must yield
the empty collection, so that ordering a result randomly never alters how the
aggregated rows are grouped.

This file models that single query: given such a non-deterministic ordering
expression (and an optional output outAlias), the list of grouping columns it
contributes is empty.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The behavior
-- being modeled — the grouping-column contribution of a non-deterministic
-- ordering expression — is a leaf computation that always returns an empty
-- collection regardless of its inputs, so there is no `opaque`/`axiom` callee
-- whose contract the proof consumes.
-- axioms-end

-- pure-start
/-- A column that participates in the grouping of an aggregated result set,
identified by the SQL fragment it compiles to. -/
abbrev GroupByCol := String

/-- A scalar expression that can appear as an ordering term, identified by the
SQL function it emits (e.g. the non-deterministic random-value generator). Such a
generator has arity zero — no operand expressions and so no underlying stored
column. -/
structure OrderingExpr where
  /-- the SQL function this ordering expression emits. -/
  function : String
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The grouping-column contribution of a non-deterministic ordering expression
is empty: such a term adds no columns to the grouping of an aggregated result set,
for any expression and any output `outAlias`. The result is pinned exactly to the
empty collection (directive 5: the sole output component is fully determined),
grounded structurally rather than by any oracle. -/
def problem_spec_randomGroupingColumns
    (self : OrderingExpr) (outAlias : Option String)
    (result : List GroupByCol) : Prop :=
  result = []
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton. The generic default contribution for a
-- non-aggregate expression is the expression itself, compiled to a single
-- grouping column (its emitted SQL function). For a non-deterministic ordering
-- term this wrongly injects that term into the grouping of the aggregated
-- result set — the defect in the issue.
def randomGroupingColumns
    (self : OrderingExpr) (outAlias : Option String) : List GroupByCol :=
  Id.run do
    return [self.function]
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- buggy impl it cannot close: the result is `[self.function]`, a one-element
-- list, but the spec requires the empty collection, so the final reduction does
-- not hold.
theorem correct_randomGroupingColumns :
    ∀ (self : OrderingExpr) (outAlias : Option String),
      problem_spec_randomGroupingColumns self outAlias
        (randomGroupingColumns self outAlias) := by
  intro self outAlias
  unfold problem_spec_randomGroupingColumns randomGroupingColumns
  rfl
-- proof-end
