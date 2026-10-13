import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. Two operations are modeled here; the operation that the
-- desired behavior changes (how a comparison target is rebound while building a
-- negated subquery) is modeled IDENTICALLY (`rebind`) and the surrounding
-- classification of a target is a structural type refinement. The one unchanged
-- downstream step — how a rebound target is consulted from inside the subquery —
-- is modeled DEEPLY (`resolveInSubquery`) and validated `== the real callee` by
-- axiom_check.py (G-AX) as an A-reference, NOT consumed as an axiom. There is no
-- opaque callee whose contract the proof assumes (mapping.md §3).
-- axioms-end

-- pure-start
/- The kind of value compared against in a lookup ("the comparison target"):
   * `outerRef`     — a reference to a value of the enclosing (outer) query;
   * `localRef`     — a reference to a field of the query under construction;
   * `directValue`  — a plain value supplied directly (a literal/instance). -/
inductive Target where
  | outerRef
  | localRef
  | directValue
  deriving DecidableEq, Inhabited, Repr

/- A target is a query *expression* (it is consulted/resolved when the query is
   built) exactly when it is not a plain directly-supplied value. A plain value
   carries no resolution step. -/
def isExpression : Target → Bool
  | .directValue => false
  | _            => true

/- Whether a comparison target is treated as a direct value to be normalized
   into the related field's value domain. This happens only for a single-column
   relation (the left side does not span multiple columns) AND only when the
   target is a plain value — a query expression must be left untouched so it can
   be resolved later, not coerced into a value. -/
def normalizesAsValue (lhsSpansMultipleColumns : Bool) (t : Target) : Bool :=
  (!lhsSpansMultipleColumns) && (!isExpression t)

/- How a comparison target is rebound when an exclusion is turned into a nested
   subquery. A reference to the outer query must be rebound so that it KEEPS
   denoting the outer query across the extra layer of nesting the subquery adds;
   a reference to a field of the (now inner) query is rebound to an outer
   reference by name; a plain value is carried through unchanged. -/
inductive Rebound where
  | outerKeepingDepth   -- the outer reference is re-wrapped to survive one nesting level
  | outerByName         -- rebound to an outer reference of the field's name
  | unchanged           -- a plain value, carried through
  deriving DecidableEq, Inhabited, Repr

def rebind : Target → Rebound
  | .outerRef    => .outerKeepingDepth
  | .localRef    => .outerByName
  | .directValue => .unchanged

/- How a rebound target resolves when consulted from inside the subquery — the
   observable that decides whether the subquery is usable. This step is UNCHANGED
   by the desired behavior; it is the constant resolution semantics of the rebound
   target (A-reference, validated `== the real callee` by axiom_check.py):
   * a re-wrapped outer reference STAYS an outer reference (one nesting level is
     peeled, leaving it still bound to the outer query — the usable case);
   * an outer reference of a name resolves to a concrete reference at THIS level;
   * a plain value stays a plain value. -/
inductive Resolution where
  | staysOuter        -- still bound to the outer query (usable inside the subquery)
  | resolvesLocally   -- resolved at this query level
  | plainValue
  deriving DecidableEq, Inhabited, Repr

def resolveInSubquery : Rebound → Resolution
  | .outerKeepingDepth => .staysOuter
  | .outerByName       => .resolvesLocally
  | .unchanged         => .plainValue
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Whether a comparison target is taken to be a direct value to normalize. A
   query expression (e.g. an outer-query reference) must NOT be classified as a
   direct value, even for a single-column relation — otherwise it is coerced
   into a value instead of being resolved as a reference. -/
method comparisonNormalizesAsValue (lhsSpansMultipleColumns : Bool) (t : Target)
    return (out : Bool)
  ensures out = normalizesAsValue lhsSpansMultipleColumns t
  do
    -- impl-start
    -- PRE-PATCH BUG (site 1): the target is taken as a "direct value" whenever
    -- it is not directly SQL-renderable. An outer-query reference is not
    -- renderable, so it is WRONGLY classified as a direct value (treated like a
    -- localRef here) and coerced — the frozen spec keeps it an expression, so
    -- `prove_correct` MUST fail.
    let targetIsDirectlyRenderable : Bool := false
    pure ((!lhsSpansMultipleColumns) && (!targetIsDirectlyRenderable))
    -- impl-end

prove_correct comparisonNormalizesAsValue by
  loom_solve <;> simp_all [normalizesAsValue, isExpression]

/- The resolution outcome of a comparison target after an exclusion is rebuilt
   as a nested subquery. An outer-query reference must end up STILL bound to the
   outer query (so the subquery is usable); the previous behavior, which rebound
   it the same way as a plain field reference, would instead resolve it at this
   level and make the subquery unusable. -/
method subqueryTargetResolution (t : Target) return (out : Resolution)
  ensures out = resolveInSubquery (rebind t)
  do
    -- impl-start
    -- This site is modeled faithfully here; the discriminating bug in THIS
    -- prepatch is at the first method (site 1). The rebind is the correct one.
    let b : Rebound :=
      match t with
      | .outerRef    => .outerKeepingDepth
      | .localRef    => .outerByName
      | .directValue => .unchanged
    let r : Resolution :=
      match b with
      | .outerKeepingDepth => .staysOuter
      | .outerByName       => .resolvesLocally
      | .unchanged         => .plainValue
    pure r
    -- impl-end

prove_correct subqueryTargetResolution by
  loom_solve <;> simp_all [resolveInSubquery, rebind]
