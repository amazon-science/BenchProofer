import Mathlib
-- imports-end

/-!
Group-by columns contributed by a wrapping expression.

Some expressions merely wrap another expression to attach extra context (such as
an output type) without changing what that inner expression computes. When a
query groups its rows, every selected expression contributes a (possibly empty)
set of columns to the grouping clause. Each kind of expression decides this for
itself: a constant expression contributes no columns, an aggregate contributes
the columns of its operands, a plain column contributes itself, and so on.

A wrapping expression adds no grouping column of its own. The columns it
contributes to the grouping clause are exactly the columns contributed by the
expression it wraps. In particular, wrapping a constant expression — which
contributes nothing — itself contributes nothing, rather than standing in as a
grouping column. The result is fully determined by the wrapped expression.
-/

-- axioms-start
-- The columns the wrapped (inner) expression contributes to the grouping clause
-- are observed directly as the `Expr.innerCols` field: this is the unchanged,
-- self-determined behavior of the inner expression, carried into the model as
-- input data (an A-reference — the wrapping expression forwards to it verbatim).
-- No separate property of that observation is consumed, so there is no
-- `opaque`/`axiom` callee contract here.
-- axioms-end

-- pure-start
/-- A single column expression as it may appear in a query's grouping clause.
Its identity is opaque; only equality of columns is observable. -/
structure Col where
  ref : Nat
deriving DecidableEq, Repr

/-- A wrapping expression, observed through the only features that determine the
columns it contributes to the grouping clause:

  * `selfCol`  — the wrapping expression viewed as a single grouping column (its
    own identity, were it to stand in for itself);
  * `innerContainsAggregate` — whether the expression it wraps contains an
    aggregate;
  * `innerCols` — the columns the wrapped (inner) expression contributes to the
    grouping clause. -/
structure Expr where
  /-- the wrapping expression as a single grouping column (its own identity) -/
  selfCol : Col
  /-- whether the wrapped (inner) expression contains an aggregate -/
  innerContainsAggregate : Bool
  /-- the grouping columns contributed by the wrapped (inner) expression -/
  innerCols : List Col
deriving Repr
-- pure-end

-- post-conditions-start
/-- The columns a wrapping expression `e` contributes to the grouping clause are
exactly those contributed by the expression it wraps (`e.innerCols`). The result
is pinned in full to the wrapped expression's contribution (directive 5 frame:
no component of the result is left free; directive 8: the result is grounded in
the actual input `e`, so it must be *produced by* forwarding to the wrapped
expression, not by re-introducing the wrapper itself). -/
def problem_spec_wrapperGroupByCols (e : Expr) (result : List Col) : Prop :=
  result = e.innerCols
-- post-conditions-end

-- impl-start
def implementation_wrapperGroupByCols (e : Expr) : List Col := Id.run do
  return e.innerCols
-- impl-end

-- proof-start
theorem correct_wrapperGroupByCols :
    ∀ (e : Expr), problem_spec_wrapperGroupByCols e (implementation_wrapperGroupByCols e) := by
  intro e
  rfl
-- proof-end
