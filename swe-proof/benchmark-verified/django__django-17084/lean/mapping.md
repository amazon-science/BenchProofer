# mapping.md — symbol binding & type bijection (django__django-17084)

## Modeled function
- **Lean** `implementation_requiresSubqueryWrap : List AggregateExpr → Bool → Bool`
- **Python** `Query.get_aggregation(self, using, aggregate_exprs)` —
  `django/db/models/sql/query.py:397-456 @ base_commit`.

`get_aggregation` resolves the requested aggregate expressions, then decides
whether the aggregation must be evaluated inside a wrapping subquery (the
`if (... ) :` at line 449-457). The modeled behavior is exactly that boolean
decision. The patch adds a new contributing disjunct.

### The decision (post-patch), line 449-457
```python
if (
    isinstance(self.group_by, tuple)     # ─┐
    or self.is_sliced                    #  │  pre-existing structural conditions
    or has_existing_aggregation          #  │  (modeled jointly as otherConditions)
    or refs_subquery                     #  │
    or refs_window          # <-- ADDED by the patch
    or qualify                           #  │
    or self.distinct                     #  │
    or self.combinator                   # ─┘
):
```

### The two reference flags, computed in the resolve loop (line 408-424)
```python
refs_subquery |= any(
    getattr(self.annotations[ref], "subquery", False)
    for ref in aggregate.get_refs()
)
refs_window |= any(                                       # <-- ADDED
    getattr(self.annotations[ref], "contains_over_clause", True)
    for ref in aggregate.get_refs()
)
```
Both flags start `False` and are OR-accumulated over every requested aggregate
and every annotation it references. `refs_window` is the new accumulator.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `aggregate_exprs` (ordered dict alias→aggregate) | `aggregates : List AggregateExpr` | only the `get_refs()` list matters; alias keys are irrelevant to the decision |
| one resolved `aggregate` and its `aggregate.get_refs()` | `AggregateExpr.refs : List RefAnnotation` | the list of referenced annotations |
| `getattr(self.annotations[ref], "subquery", False)` | `RefAnnotation.isSubqueryExpr : Bool` | per-reference subquery flag (default `False`) |
| `getattr(self.annotations[ref], "contains_over_clause", True)` | `RefAnnotation.isWindowExpr : Bool` | per-reference window/over-clause flag (default `True`) |
| `isinstance(group_by, tuple) or is_sliced or has_existing_aggregation or qualify or distinct or combinator` | `otherConditions : Bool` | the pre-existing disjuncts, collapsed into one boolean (their internal computation is unchanged by the patch and out of model scope) |
| the `if (...)` truth value (whether to build `AggregateQuery`/wrap) | result `Bool` | `True` ⇔ a wrapping subquery is used |

The `refs_subquery` accumulation is **unchanged** by the patch but is part of the
decision; it is modeled deeply (`anyRefSubquery`) and folded into the spec so the
frame is fully pinned (directive 5), not left as an unconstrained input.

## Default-value note (`contains_over_clause` default `True`)
The patched `getattr` defaults to `True`: a referenced annotation lacking the
attribute is treated conservatively as a window expression (forcing the wrap).
In the model each `RefAnnotation` carries `isWindowExpr` explicitly, so the
default is already resolved into the boolean. G-CONF fuzzes both flag values
(including the all-True bias that exercises the default).

## Callee provenance
- `aggregate.get_refs()` — returns the referenced annotation aliases. UNCHANGED;
  its result is the carrier `AggregateExpr.refs`. No axiom consumed.
- `getattr(..., "subquery", False)` / `getattr(..., "contains_over_clause", True)`
  — attribute reads on resolved annotations. UNCHANGED reads; reproduced as the
  boolean fields `isSubqueryExpr` / `isWindowExpr` (I/R), not axiomatized.
- `self.where.split_having_qualify()`, `append_annotation_mask`, etc. — feed the
  pre-existing disjuncts; their computation is unchanged and collapsed into
  `otherConditions`. Out of model scope.
- No UNCHANGED callee *property* is consumed: the axioms region is empty; G-AX is
  a skip stub.

## Flag dependency
The new disjunct fires when some referenced annotation is a window/over-clause
expression (`isWindowExpr = True`). G-CONF fuzzes both reference flags and
`otherConditions` independently.

## Scope note
Only the boolean wrapping *decision* is modeled — not the subsequent
`AggregateQuery` construction (line 458+), which is unchanged and orthogonal. The
F2P test (`test_referenced_window_requires_wrapping`) asserts the query is
wrapped (`select` count) when an aggregate references a `Window` annotation; that
is precisely `result = True` when `anyRefWindow aggregates` holds and the other
disjuncts are false.

## G-CONF fuzz seed
Pinned seed: **17084**. ≥10^5 fuzzed inputs over random aggregate/reference
lists and `otherConditions`.
