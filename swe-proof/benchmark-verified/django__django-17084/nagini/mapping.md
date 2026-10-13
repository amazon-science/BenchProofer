# mapping.md — django__django-17084

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f8c43aca467b7b0c4bb0a7fa41362f90b610b8df`, states the type
abstraction, and gives the provenance of each axiomatized / deep-modeled callee.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `requires_subquery_wrap(...)` | `Query.get_aggregation(self, using, aggregate_exprs)` — `django/db/models/sql/query.py:397` (decision block body lines 405-457) | the modeled changed function: computes whether the aggregation must be evaluated inside a wrapping subquery |
| `any_referenced_is_window(window_flags)` (deep model, pure region) | the new `refs_window |= any(getattr(self.annotations[ref], "contains_over_clause", True) for ref in aggregate.get_refs())` accumulation — `query.py:423-426` (post-patch) | pure spec: disjunction over every referenced annotation of its `contains_over_clause` flag |
| `any_referenced_is_subquery(subquery_flags)` (deep model, pure region) | the existing `refs_subquery |= any(getattr(self.annotations[ref], "subquery", False) for ref in aggregate.get_refs())` accumulation — `query.py:418-421` | pure spec: disjunction over every referenced annotation of its `subquery` flag (unchanged term, modeled to keep the decision faithful) |
| parameter `window_flags: List[bool]` | for every `ref` in every `aggregate.get_refs()`, the value `getattr(self.annotations[ref], "contains_over_clause", True)` | the per-referenced-annotation window flag; see §2 / §3 |
| parameter `subquery_flags: List[bool]` | for every `ref` in every `aggregate.get_refs()`, the value `getattr(self.annotations[ref], "subquery", False)` | the per-referenced-annotation subquery flag |
| parameter `other_forces_wrap: bool` | `isinstance(self.group_by, tuple) or self.is_sliced or has_existing_aggregation or qualify or self.distinct or self.combinator` — `query.py:449-457` (the unchanged disjuncts of the wrap predicate) | the OR of every wrap-forcing condition OTHER than `refs_subquery`/`refs_window` |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `aggregate_exprs` dict + each aggregate's `get_refs()` set + the `self.annotations[ref]` lookups | a flat `List[bool]` `window_flags` (one entry per `(aggregate, ref)` pair) plus a parallel `List[bool]` `subquery_flags` | the nested `for aggregate ... for ref in aggregate.get_refs()` iteration flattens to one list traversal; `window_flags[k]` ↔ `getattr(self.annotations[ref_k], "contains_over_clause", True)`; `subquery_flags[k]` ↔ `getattr(self.annotations[ref_k], "subquery", False)`. Order is irrelevant — both `refs_window` and `refs_subquery` are order-independent `any(...)` reductions, so the flattened-list disjunction equals the repo's `|=` accumulation. |
| each `getattr(annotation, "contains_over_clause", True)` / `getattr(annotation, "subquery", False)` | the corresponding `bool` element | the model carries the resolved boolean directly; the `getattr` default (True / False) is the value used when the attribute is absent and is folded into the element value at the binding boundary (see §3) |
| the scalar disjuncts `isinstance(self.group_by, tuple)`, `self.is_sliced`, `has_existing_aggregation`, `qualify`, `self.distinct`, `self.combinator` | one collapsed `bool` `other_forces_wrap` | `or` over the six unchanged repo conditions ↔ a single boolean; none of them is touched by the patch, so collapsing them loses no tested distinction |
| the wrap branch `if (...) :` taken vs. not taken | `Result()` of `requires_subquery_wrap` (`bool`) | `Result() == True` ↔ control enters the `AggregateQuery`/inner-subquery branch (`query.py:458`); `Result() == False` ↔ the aggregation is evaluated in place |

The `List[bool]` parameters are genuinely read-only (the decision only *reads*
the flags), so they are required AND ensured at `Acc(list_pred(x), 1/2)`
(directive 5).

The spec also carries `Requires(MustTerminate(2))`: the repo's wrap decision is
bounded work (a finite `|=`-accumulation over the `(aggregate, ref)` pairs plus
a scalar disjunction) that always returns its verdict to the aggregation
pipeline. Nagini is a partial-correctness verifier by default, so the totality
obligation is required to exclude same-spec implementations that diverge before
returning (which would satisfy the value postconditions only vacuously, while
their faithful patch hangs every `aggregate()` call and resolves nothing). The
model's loops discharge it with the strictly decreasing measures `i` / `j`.

## 3. Callee / attribute provenance (kind A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**: the changed operation is the
`any(...)` disjunction itself, which is modeled DEEPLY (the front-recursive
`@Pure` OR-folds `any_referenced_is_window` / `any_referenced_is_subquery`),
not hidden behind an axiom. The deep models are validated against the real
Python semantics by `axiom_check.py` (G-AX, A-reference).

### 3.1 `contains_over_clause` — the window flag
**Source:** `django/db/models/expressions.py`.
- `Window.contains_over_clause = True` (class attribute, `expressions.py:1703`):
  a `Window(...)` expression contains an OVER clause.
- `BaseExpression.contains_over_clause` (`expressions.py:246-250`) is
  `any(expr and expr.contains_over_clause for expr in self.get_source_expressions())`
  — so a composite annotation such as `Coalesce(Window(...), 0.0)` is `True`
  because one of its source expressions is a `Window`.
- The accumulation uses `getattr(self.annotations[ref], "contains_over_clause", True)`:
  the default is **`True`** (conservative — an annotation lacking the attribute
  is assumed to contain a window, forcing the safe subquery wrap). The model's
  `window_flags[k]` is exactly this resolved boolean.

The single behavioural change: an aggregate that references an annotation whose
`contains_over_clause` is `True` (e.g. `Sum("cumul_DJR")` over a
`Coalesce(Window(...), 0.0)` annotation) must force the wrapping subquery, so
the aggregate is computed over the window result rather than emitting an
illegal `aggregate(window())` SQL fragment.

### 3.2 `subquery` — the subquery flag (unchanged term)
**Source:** `django/db/models/expressions.py`.
- `Subquery.subquery = True` (`expressions.py:1544`).
- `getattr(self.annotations[ref], "subquery", False)`: default `False`.
The model's `subquery_flags[k]` is exactly this resolved boolean. This disjunct
is **unchanged** by the patch; it is modeled only so the wrap decision the spec
pins is the *complete* decision (a faithful skeleton), not a partial one.

### 3.3 `get_refs` / `any(...)` reduction
**Source:** `django/db/models/expressions.py:409-413` (`get_refs` unions the
refs of all source expressions) and CPython `any()` (short-circuit OR over a
boolean iterable). G-AX validates that the model's front-recursive OR-fold
equals Python's `any(...)` over the flattened flag list on boundary + fuzz
inputs (empty list, all-False, single-True at every position, all-True, mixed).
