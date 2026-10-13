# mapping.md — django__django-15930

## Symbol binding (file:line @ base_commit 63884829acd207404f2a5c3cc1d6b4cd0a822b70)

Modeled function: the predicate-fragment selection performed when a single branch
of a searched conditional SQL expression is rendered, in
`When.as_sql`, `django/db/models/expressions.py:1297-1308` (the
`condition_sql, condition_params = compiler.compile(self.condition)` step and the
slot it fills in the `"WHEN %(condition)s THEN %(result)s"` template).

The gold patch inserts, immediately after the guard is compiled, a check: if the
compiled guard SQL fragment is the empty string, the guard SQL and its bound
parameters are replaced by the compilation of an unconditionally-true value
(`Value(True)`). This is the entire modeled change; everything downstream
(storing the fragment into the template params, extending the parameter list with
the result fragment, the `template % template_params` formatting) is unchanged by
the patch and is therefore outside the modeled behavior.

Lean modeled function name: `resolveBranchCondition` (deliberately neutral — it
names the *behavior* "decide the guard fragment for one conditional branch", not
the patched method/class; see G-LEAK note below).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `resolveBranchCondition` (modeled decision) | `When.as_sql` guard-fragment selection, `expressions.py:1297` → patched `:1299-1304` |
| `conditionSql` | `condition_sql` = first element of `compiler.compile(self.condition)`, `expressions.py:1299` |
| `conditionParams` | `condition_params` = second element of `compiler.compile(self.condition)`, `expressions.py:1299` |
| `trueSql` | first element of `compiler.compile(Value(True))` — the SQL fragment of an unconditionally-true value, post-patch `:1303` |
| `trueParams` | second element of `compiler.compile(Value(True))` — the bound parameters of that value, post-patch `:1303` |
| result `(.1, .2)` | the `(condition_sql, condition_params)` pair that is stored into `template_params["condition"]` and extended into `sql_params`, `expressions.py:1305-1306` |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `condition_sql : str` (compiled guard fragment) | `conditionSql : String` |
| `condition_params : list` (bound params; arbitrary Python objects) | `conditionParams : List α` (opaque payloads, carried/replaced wholesale) |
| `compiler.compile(Value(True))[0] : str` | `trueSql : String` |
| `compiler.compile(Value(True))[1] : list` | `trueParams : List α` |
| `condition_sql == ""` (empty-string test) | `conditionSql = ""` (`String` equality; impl uses `== ""`) |
| resulting `(condition_sql, condition_params)` pair | `result : String × List α` |

### Parameter-payload modeling note
`condition_params` is a Python `list` of opaque parameter values (ints, strings,
booleans — whatever the compiled fragment binds). The patch never inspects an
individual parameter; it either keeps the pair `(condition_sql, condition_params)`
or replaces it wholesale with `(true_sql, true_params)`. We therefore model the
parameter list as `List α` over an arbitrary element type `α`: the elements are
never compared or decomposed, only carried or replaced as a unit. G-CONF bridges
this with concrete string payloads (the element type is irrelevant to the
decision, which branches only on `condition_sql == ""`).

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `compiler.compile(self.condition)`
  and `compiler.compile(Value(True))` enter as DATA: their observable outputs (the
  `(sql, params)` pairs) are supplied as the inputs `(conditionSql, conditionParams)`
  and `(trueSql, trueParams)`. The only operation modeled is the empty-string test
  and the wholesale substitution — an I/R op, not an axiom. Hence `axioms = []`,
  `deep_model_references = []`, `axiom_check.py` is a skip stub.
- Real-world fact (NOT needed as a precondition): `compiler.compile(Value(True))`
  yields a non-empty SQL fragment (a placeholder `"%s"` bound to the truthy value,
  or a backend literal). The substitution is only *meaningful* in practice because
  the stand-in fragment is non-empty, but the spec/theorem hold for every
  `trueSql` (the impl mirrors the spec branch-for-branch for all inputs), so the
  `correct_*` theorem carries no `trueSql ≠ ""` hypothesis — keeping the verified
  statement maximally strong.
- No flag dependency: the substitution fires purely on `condition_sql == ""`.

## G-LEAK
The solver-visible `problem_statement` mentions `Case`, `When`, `Q`, `Value(True)`,
`annotate`, `THEN`, `True`, and "match"/"all rows match". The spec view uses only
neutral behavioral vocabulary ("conditional expression branch", "guard",
"predicate fragment", "always-satisfied predicate"). The modeled-function
identifier `resolveBranchCondition` shares no patched def/class name (`When`,
`Case`, `as_sql`, `Value`, `compile`, `condition_sql`) as a substring. No diff line
is quoted; the bug→fix mechanism (empty-string handling differences between query
contexts) is not narrated.

## Pinned G-CONF fuzz seed
`15930`.
