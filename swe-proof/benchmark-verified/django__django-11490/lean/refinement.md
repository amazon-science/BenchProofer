# refinement.md — django__django-11490

Maps every operation in `implementation_propagateColumns` to its `patch.diff`
counterpart in the per-part column-propagation loop of
`SQLCompiler.get_combinator_sql` (compiler.py:422-433). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference** op left
as the real repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch propagation loop)
```python
for compiler in compilers:
    ...
    # If the columns list is limited, then all combined queries
    # must have the same columns list. Set the selects defined on
    # the query on all combined queries, if not already set.
    if not compiler.query.values_select and self.query.values_select:
        compiler.query = compiler.query.clone()           # <-- the fix
        compiler.query.set_values((
            *self.query.extra_select,
            *self.query.values_select,
            *self.query.annotation_select,
        ))
    part_sql, part_args = compiler.as_sql()
    ...
```

The single changed line is `compiler.query = compiler.query.clone()`: it
re-points `compiler.query` at a fresh copy BEFORE `set_values` mutates it, so the
part's shared underlying `Query` is never altered. Pre-patch, `set_values`
mutated the shared object directly.

## Modeling decision
The behavior the fix governs is the relationship between two quantities the
shared mutation conflated:

- the query USED to build this part's SQL this evaluation (it must adopt the
  composed column list), and
- the part DEFINITION carried forward to any later evaluation (it must remain the
  original part, so a later evaluation can pick a different column list).

These are modeled as the `.fst` and `.snd` of each result entry (mapping.md). A
query part is observed solely by its projected column list (`QueryPart.columns`).
`set_values`/`clone` are not modeled as callees: their only observable
contribution is the resulting query's column list, captured directly. Hence no
`opaque`/`axiom`.

## Operation correspondence
| # | Lean op (`implementation_propagateColumns`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut out := []` | initialize the accumulation of per-part results (the loop builds `parts`/`compilers` into the SQL parts) | I | empty accumulator. |
| 2 | `for part in parts do` | `for compiler in compilers:` | I | iterate the combined-query parts in order. |
| 3 | `if part.columns = [] ∧ composedColumns ≠ []` | `if not compiler.query.values_select and self.query.values_select:` | R | `part.columns : List String ↔ compiler.query.values_select`; `composedColumns ↔ self.query.values_select`. Emptiness ↔ falsiness of the tuple. |
| 4 | `let derived := { part with columns := composedColumns }` | `compiler.query = compiler.query.clone()` then `compiler.query.set_values((*extra_select, *values_select, *annotation_select))` | R | the query used this evaluation is a FRESH copy carrying the composed column list. `clone()` (the fix) is what makes this a distinct object from the part; modeled as a fresh record value with `columns := composedColumns`. |
| 5 | `out := out ++ [(derived, part)]` | the cloned query is what `compiler.as_sql()` runs (`.fst`); the part's shared `Query` is left untouched (`.snd`) | R | `.fst` = used query (adopts composed list); `.snd` = part carried forward (unchanged) — the two are distinct precisely because of `clone()`. |
| 6 | `else out := out ++ [(part, part)]` | a part that already fixes its own columns (or no composed list requested) is used as-is; its query is unchanged | I | both components are the part as-given. |
| 7 | `return out` | the loop result (one built part per compiler) | I | one entry per part, order preserved. |

## R/I legs ⇒ G-CONF
Every op is R or I (ops 3-5 are R, the rest I); there is no A leg. `conf_skip =
false`: the impl region is genuine R/I content (the conditional adopt-or-keep +
the distinctness of the used query from the carried part), so
`conformance_check.py` differential-tests the shadow against the REAL patched
propagation over ≥10^5 fuzzed inputs, observing per part
`(used_query_columns, carried_forward_part_columns)`.

## No A row
No unchanged callee property is consumed and nothing is deep-modeled (`set_values`
and `clone` contribute only the resulting column list, captured directly as
`QueryPart.columns`), so `meta.json axioms = []`, `deep_model_references = []`,
and `axiom_check.py` is a skip stub.

## F2P alignment
`test_union_with_values` evaluates `qs1.union(qs1).values_list('name', 'order')`
(composed list `('name','order')`) and then `qs1.union(qs1).values_list('order')`
(composed list `('order',)`) — and the second evaluation must actually project
`('order',)`. Pre-patch, the first `set_values` mutated the shared part `Query`,
so on the second evaluation the part already had `values_select` set and kept the
stale `('name','order')` list. The discriminating clause `problem_spec` pins is
`.snd = parts` (the carried-forward part is never altered): the prepatch impl
carries the ALTERED part forward (`(derived, derived)`), so this clause is false
and the carried gold proof cannot close — `Solution_prepatch.lean` fails
G-VERIFY. `patch.diff` (gold verbatim) makes the harness resolve.
