import Mathlib
-- imports-end

/-!
Deciding whether a value is admissible on the left/right-hand side of a
relational *filter clause*.

The subject is a single procedure that inspects a candidate value and decides
whether that value must be **rejected** from a filter clause (the rejection that,
in the host system, surfaces as a "disallowed in the filter clause" error).

A candidate value is described by three observable facets:

  * whether it is a genuine *query expression* — a first-class expression object
    that participates in the system's expression-resolution protocol, as opposed
    to a plain stored value that merely happens to carry like-named attributes;
  * whether it is marked as admissible in a filter clause (its `filterable`
    flag); a value that does not carry the flag at all counts as admissible;
  * its nested *source sub-expressions* — the component expressions it is built
    from (a plain value has none).

Desired behavior: a candidate is rejected exactly when it — or, recursively, any
of its nested source sub-expressions — is a genuine query expression that is
marked non-admissible. A value that is not a query expression is never rejected
on its own account, no matter how its `filterable` flag reads; but it is still
rejected if one of its nested source sub-expressions independently warrants
rejection.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- is modeled structurally over the candidate value's three observable facets
-- (query-expression status, admissibility flag, nested sub-expressions), so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A candidate value inspected for filter-clause admissibility, restricted to
the touched facets:
* `isQueryExpr` — whether the value is a genuine query expression participating
  in the expression-resolution protocol;
* `filterable`  — whether the value is marked admissible in a filter clause
  (absence of the marking is modeled as `true`);
* `children`    — its nested source sub-expressions. -/
inductive Expr where
  | mk (isQueryExpr : Bool) (filterable : Bool) (children : List Expr)

namespace Expr
def isQueryExpr : Expr → Bool | .mk q _ _ => q
def filterable  : Expr → Bool | .mk _ f _ => f
def children    : Expr → List Expr | .mk _ _ c => c
end Expr

/- The reference decision, as a structural fold over the candidate value.
A node forces rejection on its own account only when it is a query expression
(`q`) AND is marked non-admissible (`!f`); rejection otherwise propagates from
any nested sub-expression that independently warrants it. -/
mutual
def raises : Expr → Bool
  | .mk q f children => (q && !f) || raisesAny children
def raisesAny : List Expr → Bool
  | [] => false
  | c :: cs => raises c || raisesAny cs
end
-- pure-end

-- post-conditions-start
/-- The decision is pinned exactly to the structural reference fold over the
candidate value: the result is `true` iff the value (or one of its nested source
sub-expressions, transitively) is a query expression marked non-admissible. -/
def problem_spec_checkFilterable (e : Expr) (result : Bool) : Prop :=
  result = raises e
-- post-conditions-end

-- impl-start
/- Imperative skeleton of the procedure: inspect the value; if it is a query
expression marked non-admissible, reject immediately (early return); otherwise
recurse over the nested source sub-expressions, rejecting if any of them does. -/
mutual
def implementation_checkFilterable : Expr → Bool
  | .mk _q f children => Id.run do
    if !f then
      return true
    return implementation_checkFilterableAny children
def implementation_checkFilterableAny : List Expr → Bool
  | [] => false
  | c :: cs => implementation_checkFilterable c || implementation_checkFilterableAny cs
end
-- impl-end

-- proof-start
theorem correct_checkFilterable :
    ∀ e : Expr,
      problem_spec_checkFilterable e (implementation_checkFilterable e) := by
  sorry
-- proof-end
