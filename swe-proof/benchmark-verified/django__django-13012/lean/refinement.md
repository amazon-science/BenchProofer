# refinement.md — django__django-13012

Operation correspondence between `implementation_wrapperGroupByCols` (Solution.lean,
impl region) and `patch.diff`. Every step is tagged R / A-consumed / A-reference / I.

## patch.diff (gold)
The patch adds one method to `ExpressionWrapper`:

```python
def get_group_by_cols(self, alias=None):
    return self.expression.get_group_by_cols(alias=alias)
```

This makes the wrapping expression contribute exactly the grouping columns of the
expression it wraps, instead of inheriting `BaseExpression.get_group_by_cols`
(which returns `[self]` for a non-aggregate wrapper, wrongly forcing a wrapped
constant into the GROUP BY clause).

## Impl ↔ patch op map

| # | `implementation_wrapperGroupByCols` op | `patch.diff` counterpart | tag |
|---|---|---|---|
| 1 | `return e.innerCols` | `return self.expression.get_group_by_cols(alias=alias)` — the new method forwards the group-by columns of the wrapped (inner) expression | **A-reference** |

### Tag justification
- **Op 1 — A-reference.** The patched method delegates verbatim to the wrapped
  expression's own `get_group_by_cols`. That callee is NOT changed by the patch;
  its result is modeled deeply as the input field `e.innerCols` (the columns the
  inner expression contributes). The impl forwards exactly this value, mirroring
  the delegation. No property of the inner callee is consumed by the proof
  (the spec equates the result to `e.innerCols` directly), so this is a deep
  model reference, not a consumed axiom. The model–vs–real-callee fidelity is
  validated against the actual `self.expression.get_group_by_cols` by G-AX/G-CONF
  semantics; here there is no standalone R/I transformation to differential-test.

## conf_skip
The impl region is composed entirely of the single A-reference op (a pure
forward of the inner expression's already-computed contribution). There is no
standalone R/I data transformation whose Python shadow could be built without
re-implementing the real inner callee. Hence `meta.json conf_skip = true` and
`conformance_check.py` is a skip stub.

## No changed-inexpressible op
Every op of the fix is expressed: the delegation is modeled as forwarding the
inner expression's contribution `e.innerCols`. The discriminating behavior (a
wrapped constant — `innerCols = []`, `innerContainsAggregate = false` — must
contribute `[]`, not the wrapper `[e.selfCol]`) is pinned by the spec and is
exactly what the prepatch impl violates (G-DIFF).
