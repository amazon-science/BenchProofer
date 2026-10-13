# mapping.md — django__django-12050

## Symbol binding (file:line @ base_commit b93a0e34d9b9b99d41103782b7e7aeabf47517e3)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_resolveLookupValue` / `problem_spec_resolveLookupValue` | `django.db.models.sql.query.Query.resolve_lookup_value` | `django/db/models/sql/query.py:1053-1077` |
| `LV` (pure helper, inductive) | the `value` argument and its recursive structure (an expression-bearing object, a scalar, a `list`, or a `tuple`) | `query.py:1053` (the `value` parameter) |
| `resolveExpression` (`opaque` callee) | `value.resolve_expression(self, reuse=…, allow_joins=…[, simple_col=…])` | `query.py:1054-1058` / `django/db/models/expressions.py:228,…` |
| `resolveSpec` (pure helper) | the recursive resolution of `value` (the structural "what" the function computes) | `query.py:1053-1077` |

The modeled function is `Query.resolve_lookup_value`. It is the only function the
patch changes and the only behavior the FAIL_TO_PASS test
(`test_iterable_lookup_value`) observes.

### What the function does (base_commit)

```python
def resolve_lookup_value(self, value, can_reuse, allow_joins, simple_col):
    if hasattr(value, 'resolve_expression'):
        kwargs = {'reuse': can_reuse, 'allow_joins': allow_joins}
        if isinstance(value, F):
            kwargs['simple_col'] = simple_col
        value = value.resolve_expression(self, **kwargs)
    elif isinstance(value, (list, tuple)):
        # The items of the iterable may be expressions and therefore need
        # to be resolved independently.
        resolved_values = []
        for sub_value in value:
            if hasattr(sub_value, 'resolve_expression'):
                if isinstance(sub_value, F):
                    resolved_values.append(sub_value.resolve_expression(
                        self, reuse=can_reuse, allow_joins=allow_joins,
                        simple_col=simple_col,
                    ))
                else:
                    resolved_values.append(sub_value.resolve_expression(
                        self, reuse=can_reuse, allow_joins=allow_joins,
                    ))
            else:
                resolved_values.append(sub_value)
        value = tuple(resolved_values)          # <-- pre-fix: ALWAYS a tuple
    return value
```

The function classifies `value`:
1. **expression** (`hasattr(value, 'resolve_expression')`) — resolve it via
   `value.resolve_expression(...)` and return the resolved expression.
2. **iterable** (`isinstance(value, (list, tuple))`) — resolve each element and
   return the collection of resolved elements.
3. **anything else** — return `value` unchanged.

The dispatch is the heart of the function: an element of an iterable may itself
be an expression (the in-code comment), so each element must go through the same
resolution.

### The base_commit (pre-fix) behavior vs the post-fix behavior

* **Pre-fix iterable branch** builds `resolved_values` with a single, NON-recursive
  pass: each element is resolved if it is an expression, otherwise kept verbatim;
  it never re-enters the list/tuple branch for a nested iterable. It then wraps
  the result with `tuple(resolved_values)` — so the returned container is ALWAYS a
  `tuple`, regardless of whether the input was a `list` or a `tuple`.
* **Post-fix iterable branch** is `return type(value)(resolve_lookup_value(sub)
  for sub in value)`: it (a) reconstructs the SAME container type as the input
  (`type(value)` — a `list` stays a `list`, a `tuple` stays a `tuple`), and (b)
  resolves each element by RECURSING through the full dispatch, so a nested
  `list`/`tuple` keeps its own type too.

The observable defect the issue reports: a `list` input is returned as a `tuple`.
Field types whose lookups compare against the input container type (e.g. an
exact match whose right-hand side is rendered from the value) then break, because
`['a', 'b']` is rendered/compared as a `tuple` `('a', 'b')` instead of the list.
The FAIL_TO_PASS assertion pins exactly this: `Query(Item).build_where(Q(name=['a',
'b']))` must keep the right-hand side as `"['a', 'b']"` (list bracket repr), not
`"('a', 'b')"`.

## `LV` constructor ↔ Python value bijection

`LV` models the `value` argument as a finite tree of the four cases the dispatch
distinguishes:

| `LV` constructor | Python meaning | notes |
|---|---|---|
| `LV.expr e` | a `value` for which `hasattr(value, 'resolve_expression')` is true (any expression object, `F` or otherwise) | `e : Nat` is an injective identity tag for the expression object; only its identity (which resolution it triggers) is observed. |
| `LV.plain n` | a `value` that is neither an expression nor a `list`/`tuple` (a scalar leaf — `int`, `str`, etc.) | `n : Nat` is an opaque identity for the scalar; it is returned verbatim. |
| `LV.lst xs` | a Python `list` whose elements are themselves modeled `LV` values | preserves order and arity. |
| `LV.tup xs` | a Python `tuple` whose elements are themselves modeled `LV` values | preserves order and arity. |

The `can_reuse`, `allow_joins`, `simple_col` arguments influence ONLY the keyword
arguments passed to `resolve_expression`; they do not affect the dispatch or the
container reconstruction, which is the behavior the patch changes. They are
therefore folded into the opaque `resolveExpression` callee (below) and not
surfaced as separate Lean inputs.

## `resolveExpression` opaque callee — provenance + flag dependency

* **Real callee:** `value.resolve_expression(self, reuse=can_reuse,
  allow_joins=allow_joins[, simple_col=simple_col])`
  (`django/db/models/expressions.py`). It is UNCHANGED by the patch.
* **Why opaque, no consumed property.** `resolve_lookup_value` does not inspect
  the resolved expression; it returns it (top level) or stores it as an element
  (iterable branch). The proof needs no property of the resolved value beyond
  "resolution is a deterministic function of the expression object", so
  `resolveExpression : Nat → LV` is declared `opaque` and NO `axiom
  resolveExpression_prop` is consumed. It is an **A-reference**: the spec and the
  impl call it identically, so it cancels in the correctness argument.
* **Flag dependency (`F` vs non-`F`).** The real code passes `simple_col` only
  when `isinstance(value, F)`. This selects WHICH keyword arguments the unchanged
  callee receives; the patch preserves this branching identically (the recursive
  `resolve_lookup_value(sub_value, …, simple_col)` re-derives the same `F`/non-`F`
  split inside the recursive call). Since both pre- and post-fix resolve an
  expression element to the same value, the `F`/`simple_col` split does not
  distinguish the bug and is absorbed into the single opaque `resolveExpression`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `value` (expression / scalar / `list` / `tuple`, recursively) | `LV` | `expr ↔` resolve-expression-bearing object; `plain ↔` scalar leaf; `lst ↔ list`; `tup ↔ tuple`; nesting is structural. |
| `value.resolve_expression(...)` | `resolveExpression e` | the unchanged resolution callee; opaque deterministic function of the expression identity. |
| `type(value)(... for sub in value)` for a `list` input | `LV.lst (xs.map resolveSpec)` | same-type reconstruction + element-wise recursion. |
| `type(value)(... for sub in value)` for a `tuple` input | `LV.tup (xs.map resolveSpec)` | same-type reconstruction + element-wise recursion. |
| return value unchanged (scalar) | `LV.plain n` | identity. |

The result is itself an `LV`, modeling the returned `value` after resolution.

## G-CONF fuzz seed

Pinned LCG seed: **12050** (see `conformance_check.py` `SEED`). Corpus: randomly
generated `LV` trees (bounded depth 0–4, each node an `expr`/`plain`/`lst`/`tup`
with 0–4 children), with `expr` leaves carrying an opaque identity resolved
IDENTICALLY in both legs. The R/I shadow of `implementation_resolveLookupValue`
is diffed against an in-process replica of the POST-PATCH
`resolve_lookup_value` (`type(value)(resolve_lookup_value(sub) for sub in value)`)
over ≥1e5 fuzzed trees plus hand-picked edge cases (top-level list, top-level
tuple, nested list-in-tuple and tuple-in-list, list/tuple of expressions, empty
list, empty tuple, bare scalar). They must agree on every input — in particular
the top-level `list` case (`Q(name=['a','b'])`) that the patch fixes.
