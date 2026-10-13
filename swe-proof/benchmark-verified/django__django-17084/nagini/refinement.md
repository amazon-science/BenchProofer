# refinement.md — django__django-17084

The operation-by-operation correspondence between `model.py`'s implementation
(the `requires_subquery_wrap` impl region and the deep `any_referenced_flag`
fold) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee/semantics by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change — `Query.get_aggregation` (`django/db/models/sql/query.py:397`)

Gold hunks:
```
  refs_subquery = False
+ refs_window = False
  ...
+ refs_window |= any(
+     getattr(self.annotations[ref], "contains_over_clause", True)
+     for ref in aggregate.get_refs()
+ )
  ...
  or refs_subquery
+ or refs_window
  or qualify
```

The patch (1) introduces an accumulator `refs_window`, (2) for each aggregate
ORs in whether any referenced annotation `contains_over_clause`, and (3) adds
`refs_window` as a disjunct of the subquery-wrap predicate. The model spells
this out: the `window_flags` loop computes `refs_window`, and the return ORs it
into the wrap decision.

| # | model.py impl op (`requires_subquery_wrap`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `window_flags: List[bool]` | the per-`(aggregate, ref)` values `getattr(self.annotations[ref], "contains_over_clause", True)` collected across the `for alias, aggregate_expr in aggregate_exprs.items()` / `for ref in aggregate.get_refs()` iteration | R | the nested dict+set iteration flattens to one boolean list; order is irrelevant because the reduction is `any(...)` (order-independent). The `getattr` default `True` is folded into each element at the binding boundary (mapping.md §2, §3.1). |
| A2 | parameter `subquery_flags: List[bool]` | the parallel `getattr(self.annotations[ref], "subquery", False)` values (the **unchanged** `refs_subquery` term) | R | same flattening; default `False` folded in (mapping.md §3.2). Modeled so the wrap decision the spec pins is complete, not partial. |
| A3 | parameter `other_forces_wrap: bool` | `isinstance(self.group_by, tuple) or self.is_sliced or has_existing_aggregation or qualify or self.distinct or self.combinator` (the six unchanged disjuncts, `query.py:449-457`) | R | the OR of six untouched conditions collapses to one boolean; the patch changes none of them, so collapsing loses no tested distinction (mapping.md §2). |
| A4 | `refs_window = False` then the `while i > 0` loop accumulating `refs_window = window_flags[i-1] or refs_window` | `refs_window = False` then `refs_window |= any(getattr(self.annotations[ref], "contains_over_clause", True) for ref in aggregate.get_refs())` accumulated over aggregates | A-reference + I | the OR-reduction is modelled **deeply** by the front-recursive `@Pure` fold `any_referenced_flag` and the verified loop; there is no consumed axiom. The deep fold is validated `any_referenced_flag == Python any(...)` and the element values == Django's `contains_over_clause` resolution by axiom_check.py / G-AX (mapping.md §3). `|=` over the flattened list ≡ a single `any(...)` over it (idempotent, order-independent OR). |
| A5 | `refs_subquery = False` then the `while j > 0` loop accumulating `refs_subquery = subquery_flags[j-1] or refs_subquery` | the existing `refs_subquery |= any(getattr(self.annotations[ref], "subquery", False) ...)` | A-reference + I | identical reduction structure to A4 on the **unchanged** subquery term; same G-AX validation of the fold. |
| A6 | `return other_forces_wrap or refs_subquery or refs_window` | the `if (... or refs_subquery or refs_window or ...)` branch guard | I + R | the disjunction is the literal wrap predicate; `Result() == True` ↔ the patched code enters the inner-subquery (`AggregateQuery`) branch (`query.py:458`), `False` ↔ in-place aggregation (mapping.md §2). |

**Totality.** The spec carries `Requires(MustTerminate(2))`: deciding the wrap
is bounded straight-line + finite-loop work in the real `get_aggregation`
(one read per `(aggregate, ref)` flag), and the decision must actually be
DELIVERED to the aggregation pipeline. Nagini verifies partial correctness by
default, so without this obligation a same-spec implementation that diverges
before returning (an unbounded loop ahead of the gold body) satisfies the value
postconditions vacuously while its faithful real patch hangs every
`aggregate()` call — the F2P harness times out and it does NOT resolve. Both
verified loops discharge the obligation with the strictly decreasing,
bounded-below measures `i` / `j` (`Invariant(MustTerminate(i + 1))` /
`Invariant(MustTerminate(j + 1))`), matching the real loops' bounded iteration
over the finite flag lists.

The discriminating content of the change — including `refs_window` in the
disjunction — lives in the postcondition
`Result() == (any_referenced_flag(window_flags) or any_referenced_flag(subquery_flags) or other_forces_wrap)`
and the consequence `Implies(any_referenced_flag(window_flags), Result())`.
`model_prepatch.py` reproduces the pre-patch skeleton (no `refs_window` term,
`return other_forces_wrap or refs_subquery`) and **fails** that postcondition on
any input with a True window flag and all other terms False — exactly the spec
sensing the change (G-DIFF). This is the behaviour the F2P test
`test_referenced_window_requires_wrapping` observes: an aggregate over a
`Coalesce(Window(...), 0.0)` annotation must be wrapped (`sql.count("select") == 2`),
whereas pre-patch it was not, yielding illegal `aggregate(window())` SQL.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding the `any(... contains_over_clause ...)` disjunct to the wrap
predicate — is modelled **deeply** (the spelled-out front-recursive fold
`any_referenced_flag` consumed in the window loop, step A4, an **A-reference**),
not hidden behind an axiom about the function under change. There is **no
consumed `@ContractOnly` axiom** (the axioms region is empty). The fold and the
element semantics are the **A-reference** that G-AX validates against Python's
`any(...)` and Django's `contains_over_clause`/`subquery` attribute resolution.

## C. verify(model) ⇒ resolved

`requires_subquery_wrap` verifies only if its result equals the full three-term
disjunction **including** the window term (A4/A6) and only if a single True
window flag forces the wrap (the `Implies` clause). By R (the flattening of the
dict/set iteration into boolean lists, the collapse of the six untouched
disjuncts, and the branch ↔ `Result()` correspondence) the verified decision
equals the gold patch's `if (...)` guard on the tested query. By G-AX the deep
fold `any_referenced_flag` equals Python's `any(...)` and the flag elements
equal `getattr(annotation, "contains_over_clause"/"subquery", default)`
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited semantics — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
the A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
