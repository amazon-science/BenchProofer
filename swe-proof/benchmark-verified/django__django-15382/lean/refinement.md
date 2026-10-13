# refinement.md — django__django-15382

Maps every operation in `implementation_compileExistenceCheck` to its
`patch.diff` counterpart (`Exists.as_sql`,
`django/db/models/expressions.py:1212-1224`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed/used
op validated == real callee, **I** identical concrete op.

## Patch (post-patch `Exists.as_sql`)
```python
def as_sql(self, compiler, connection, template=None, **extra_context):
    query = self.query.exists(using=connection.alias)
    try:
        sql, params = super().as_sql(
            compiler, connection, template=template, query=query, **extra_context,
        )
    except EmptyResultSet:
        if self.negated:
            return '', ()
        raise
    if self.negated:
        sql = 'NOT {}'.format(sql)
    return sql, params
```

## Operation correspondence
| # | Lean op (`implementation_compileExistenceCheck`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `match inner with` (case on `.ok`/`.error .emptyResult`/`.error .other`) | `try: … except EmptyResultSet:` around `super().as_sql(...)` | R | The outcome of the unchanged `super().as_sql` call (`query=self.query.exists(...)` precomputed) is refined to `inner : Except RenderFailure (String × List String)`: a normal return `(sql, params)` ↦ `.ok (sql, params)`; an `EmptyResultSet` raise ↦ `.error .emptyResult`; any OTHER raise ↦ `.error .other`. The `try/except EmptyResultSet` control split — which catches only `EmptyResultSet` and lets other exceptions propagate — ↦ the three-way `match`. |
| 2 | `.error .emptyResult → if negated then return .ok ("", [])` | `except EmptyResultSet: if self.negated: return '', ()` | I | The negated empty-result branch returns the empty fragment with no parameters. `('', ())` ↦ `("", [])`. |
| 3 | `.error .emptyResult → else return .error .emptyResult` | `except EmptyResultSet: … raise` | I | A non-negated empty-result re-raises `EmptyResultSet`, propagated unchanged as `.error .emptyResult`. |
| 4 | `.error .other → return .error .other` | (no `except` clause matches; exception propagates) | I | Any non-`EmptyResultSet` failure is NOT caught by the `try/except EmptyResultSet`, so it propagates unchanged regardless of `negated`; modeled as the distinct `.other` channel re-raised verbatim. |
| 5 | `.ok (sql, params) → let mut sql := sql` | bind `sql, params = super().as_sql(...)` | I | the success fragment + parameters from the inner render. |
| 6 | `if negated then sql := "NOT " ++ sql` | `if self.negated: sql = 'NOT {}'.format(sql)` | I | textual negation prefix on the success fragment; `'NOT {}'.format(sql)` ↦ `"NOT " ++ sql`. |
| 7 | `return .ok (sql, params)` | `return sql, params` | I | success result; parameters passed through unchanged in every success branch. |

Every op is **R** (the single `try/except`→`Except`/`match` boundary refinement,
op 1) or **I** (the concrete dispatch arms). There is **no A-consumed row** (no
opaque-axiom contract is consumed) and **no A-reference** (no callee is modeled
deeply): the unchanged callee `super().as_sql` is not modeled at all — its outcome
is the boundary input `inner`. Hence `meta.json axioms = []`,
`deep_model_references = []`, `conf_skip = false`. The whole impl region is
R/I, so its behavioral conformance is mechanically refuted by **G-CONF**
(`conformance_check.py`) over fuzzed `(negated, inner)`; `axiom_check.py` (G-AX)
is a skip stub (no callee contract to validate).

## Prepatch = the real bug
Pre-patch, `super().as_sql(...)` is called WITHOUT the `try/except`, so an
`EmptyResultSet` raised by an empty subquery propagates out of `Exists.as_sql`
unconditionally — including for a NEGATED `Exists`. The prepatch impl models this
as: in the `.error e` case, `return .error e` regardless of `negated` (any
failure, the empty-result signal included, propagates unchanged). It therefore
cannot satisfy `problem_spec_compileExistenceCheck` in the discriminating case
`negated = true ∧ inner = .error .emptyResult`: the spec requires `.ok ("", [])`
(the empty fragment) but the prepatch yields `.error .emptyResult`. The carried
gold proof closes the `.ok` arms, the `.error .other` arm, and the non-negated
`.error .emptyResult` arm, but the `error.emptyResult.true` case reduces to
the goal `False` (empty fragment ≠ propagated signal), so the prepatch FAILS
G-VERIFY — exactly the behavior the FAIL_TO_PASS test
`test_negated_empty_exists` exercises (a `~Exists(Manager.objects.none())`
combined with `Q(pk=…)` must keep the `WHERE` block and return the manager,
instead of `EmptyResultSet` dropping the whole predicate). Confirmed by
`lean_verify` exit 1 on `Solution_prepatch.lean`.
