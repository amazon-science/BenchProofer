# mapping.md — django__django-14122

## Symbol binding (file:line @ base_commit bc04941bf811d1ea2c79fb7fc20457ed2c7e3410)
Modeled function: `SQLCompiler.get_group_by(self, select, order_by)`,
`django/db/models/sql/compiler.py:63-148` @ base_commit. The gold patch changes
the single phase that contributes the ORDER BY expressions to the accumulated
`expressions` list: the loop

```python
for expr, (sql, params, is_ref) in order_by:
    if not is_ref:
        expressions.extend(expr.get_group_by_cols())
```
becomes guarded by the implicit-default-ordering flag:
```python
if not self._meta_ordering:
    for expr, (sql, params, is_ref) in order_by:
        if not is_ref:
            expressions.extend(expr.get_group_by_cols())
```

`self._meta_ordering` is set (to a truthy list) by `get_order_by` exactly when
the query's ordering comes from the model's default ordering
(`Meta.ordering`) rather than from an explicit request
(`compiler.py:285-287`); otherwise it stays `None`.

The observable fixed behavior: when the ordering is the model's implicit default
ordering, its expressions are NOT added to the grouping; when the ordering is
explicit (or absent), they are still added (unchanged behavior). Every other
phase that builds `expressions` (the explicit `group_by` entries, the SELECT
columns, the HAVING columns) is unchanged.

Lean modeled function name: `getGroupBy`.

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `getGroupBy` (modeled accumulation) | `SQLCompiler.get_group_by`, building the `expressions` local, `compiler.py:101-138` |
| `metaOrdering` | truthiness of `self._meta_ordering` (`if not self._meta_ordering:` post-patch), `compiler.py:286-287` (set), `:128` (read post-patch) |
| `gb : GroupBy` | `self.query.group_by`: `None` (`GroupBy.isNone`), `True` (`GroupBy.allFields`), or a list (`GroupBy.explicit cols`), `compiler.py:101-114` |
| `gb.explicitList` | the resolved expressions appended when `group_by` is a list, `compiler.py:108-114` (each entry's contributed group-by column identity) |
| `select : List (Bool × List Col)` | the `select` argument; per entry `(expr in ref_sources, expr.get_group_by_cols())`, `compiler.py:116-124` |
| `orderBy : List (Bool × List Col)` | the `order_by` argument; per entry `(is_ref, expr.get_group_by_cols())`, `compiler.py:125-129` |
| `having : List Col` | `self.having.get_group_by_cols()` column identities, `compiler.py:130-132` |
| `Col` | the identity of a group-by column expression appended to `expressions` |
| result | the accumulated `expressions` list (pre-`collapse_group_by`/dedup), in order |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `bool(self._meta_ordering)` (ordering came from `Meta.ordering`) | `metaOrdering : Bool` |
| `self.query.group_by` ∈ {`None`, `True`, list} | `GroupBy` (`isNone` / `allFields` / `explicit (List Col)`) |
| `expr.get_group_by_cols()` (an ordered list of group-by columns) | `List Col` (`Col := Nat`, a column identity) |
| `expr in ref_sources` (SELECT entry already covered by reference) | the `Bool` of a `select` entry |
| `is_ref` (ORDER BY entry references the SELECT clause) | the `Bool` of an `orderBy` entry |
| `self.having.get_group_by_cols()` | `having : List Col` |
| the accumulated `expressions` list (in order) | `result : List Col` |

### Modeling note — `get_group_by_cols()` outcomes as data
`expr.get_group_by_cols()` (and `resolve_ref`) are unchanged callees. Each
expression's contributed list of group-by columns enters as the `List Col`
carried by the corresponding `select` / `orderBy` entry (or `having`). They are
NOT axiomatized: the loop consumes their results as data, and the accumulation /
gating logic that uses them is modeled deeply (R/I), so there is no consumed
callee axiom and no A-reference.

### Modeling note — downstream `collapse_group_by` + dedup are unchanged
After the `expressions` list is built, `get_group_by` runs
`collapse_group_by(expressions, having)` and a `compile`/dedup pass
(`compiler.py:133-148`). These are byte-identical pre/post patch and operate on
the already-built `expressions`. The patch changes ONLY which columns enter
`expressions`; an erroneously-added implicit-ordering column is a distinct
column that the dedup pass does not remove, so it would still reach the final
GROUP BY. The modeled value is therefore the pre-collapse `expressions` list —
exactly the value the patch produces differently — and the unchanged downstream
transform is outside the modeled function.

## Callee provenance + flag deps
- No unchanged callee is consumed as an axiom; none is an A-reference. The
  `get_group_by_cols()` outputs and the `ref_sources`/`is_ref` membership enter
  as data; the accumulation + gating logic is modeled deeply. `axiom_check.py`
  is a skip stub.
- Flag dependency: the ORDER BY contribution fires only when
  `not self._meta_ordering` (`metaOrdering = false`). When `metaOrdering = true`
  (ordering is the model's implicit default), the ORDER BY phase is skipped
  entirely; all other phases are unchanged.

## G-LEAK
The solver-visible `problem_statement` itself states the desired behavior
verbatim — "Meta.ordering fields must not be included in GROUP BY clause" — and
names `Meta.ordering` and `GROUP BY`. These are public vocabulary; `metaOrdering`
echoes the public `Meta.ordering`, `getGroupBy`/`GROUP BY` is public. The spec
view describes the abstract behavior (the accumulation of grouping columns, and
that an implicit default ordering does not contribute) and does not quote any
gold-diff line, name the patched flag symbol (`_meta_ordering`), nor narrate the
bug→fix mechanism.

## Pinned G-CONF fuzz seed
`14122`.
