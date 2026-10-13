# refinement.md — django__django-14122

Maps every operation in `implementation_getGroupBy` to its `patch.diff`
counterpart in `SQLCompiler.get_group_by` (`django/db/models/sql/compiler.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch `get_group_by`, the modeled accumulation phases)
```python
def get_group_by(self, select, order_by):
    if self.query.group_by is None:
        return []
    expressions = []
    if self.query.group_by is not True:
        for expr in self.query.group_by:
            if not hasattr(expr, 'as_sql'):
                expressions.append(self.query.resolve_ref(expr))
            else:
                expressions.append(expr)
    ref_sources = {expr.source for expr in expressions if isinstance(expr, Ref)}
    for expr, _, _ in select:
        if expr in ref_sources:
            continue
        cols = expr.get_group_by_cols()
        for col in cols:
            expressions.append(col)
    if not self._meta_ordering:                       # <-- the gold's new guard
        for expr, (sql, params, is_ref) in order_by:
            if not is_ref:
                expressions.extend(expr.get_group_by_cols())
    having_group_by = self.having.get_group_by_cols() if self.having else ()
    for expr in having_group_by:
        expressions.append(expr)
    # ... collapse_group_by + compile/dedup pass (unchanged, NOT modeled) ...
```
The single behavioral change is the new `if not self._meta_ordering:` guard
wrapping the ORDER BY → `expressions` loop. Everything else in the accumulation
is verbatim-unchanged.

## Operation correspondence (`implementation_getGroupBy`)
| # | Lean op (`implementation_getGroupBy`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut expressions : List Col := []` | `expressions = []` | I | accumulator starts empty. |
| 2 | `match gb with \| GroupBy.isNone => return []` | `if self.query.group_by is None: return []` | R | `self.query.group_by ∈ {None, True, list}` ↔ `GroupBy`; the `None` case early-returns the empty list. |
| 3 | `\| GroupBy.allFields => pure ()` | `if self.query.group_by is not True: … (skipped when True)` | R | when grouping by all selected fields there is no explicit seed list, so nothing is appended in this phase. |
| 4 | `\| GroupBy.explicit cols => for c in cols do expressions := expressions ++ [c]` | `for expr in self.query.group_by: … expressions.append(…)` | R | the resolved explicit grouping columns ↔ `cols : List Col` (each entry's contributed group-by column identity, via `resolve_ref`/`as_sql`, mapping.md); appended in order. |
| 5 | `for entry in select do if entry.1 then continue; for col in entry.2 do expressions := expressions ++ [col]` | `for expr, _, _ in select: if expr in ref_sources: continue; for col in expr.get_group_by_cols(): expressions.append(col)` | R | per `select` entry: `expr in ref_sources` ↔ `entry.1`; `expr.get_group_by_cols()` ↔ `entry.2` (data, mapping.md); skip-if-covered ↔ `continue`; append each column in order. |
| 6 | `if !metaOrdering then for entry in orderBy do if !entry.1 then for col in entry.2 do expressions := expressions ++ [col]` | `if not self._meta_ordering: for expr, (sql, params, is_ref) in order_by: if not is_ref: expressions.extend(expr.get_group_by_cols())` | R | **THE changed line(s).** `bool(self._meta_ordering)` ↔ `metaOrdering`; `is_ref` ↔ `entry.1`; `expr.get_group_by_cols()` ↔ `entry.2` (data); `extend` ↔ appending each column in order. The new outer guard `not self._meta_ordering` ↔ `!metaOrdering`. |
| 7 | `for col in having do expressions := expressions ++ [col]` | `for expr in having_group_by: expressions.append(expr)` | R | `self.having.get_group_by_cols()` ↔ `having : List Col` (data, mapping.md); appended in order. |
| 8 | `return expressions` | (the accumulated `expressions`, fed to `collapse_group_by`/dedup) | I | return the ordered accumulation (the pre-collapse value the patch produces differently; see mapping.md "downstream unchanged"). |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee — the `get_group_by_cols()` outputs and the
`ref_sources`/`is_ref` membership enter as data per mapping.md). Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the ORDER BY loop is unconditional — it has no
`if not self._meta_ordering:` guard:
```python
for expr, (sql, params, is_ref) in order_by:
    if not is_ref:
        expressions.extend(expr.get_group_by_cols())
```
The prepatch impl (`implementation_getGroupBy`, identical otherwise) drops the
`if !metaOrdering then` guard and always runs the ORDER BY phase. It therefore
cannot satisfy `problem_spec_getGroupBy` (which omits the ORDER BY columns when
`metaOrdering = true`) whenever the ordering is the model's implicit default and
contributes at least one non-reference column — precisely the case the
FAIL_TO_PASS test `test_default_ordering_does_not_affect_group_by` exercises: a
model with `Meta.ordering` is aggregated with `.values('author').annotate(Count(
'author'))`, and the implicit ordering field must NOT widen the GROUP BY (else
the counts are wrong). The carried gold proof fails to typecheck against the
buggy impl (G-DIFF).
