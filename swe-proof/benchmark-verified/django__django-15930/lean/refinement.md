# refinement.md — django__django-15930

Maps every operation in `implementation_resolveBranchCondition` to its
`patch.diff` counterpart in `When.as_sql`
(`django/db/models/expressions.py`, the guard-fragment selection step).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch guard-fragment selection)
```python
condition_sql, condition_params = compiler.compile(self.condition)
# Filters that match everything are handled as empty strings in the
# WHERE clause, but in a CASE WHEN expression they must use a predicate
# that's always True.
if condition_sql == "":
    condition_sql, condition_params = compiler.compile(Value(True))
template_params["condition"] = condition_sql
sql_params.extend(condition_params)
```
The modeled value is the `(condition_sql, condition_params)` pair as it stands
*after* this block — the guard fragment (and its bound parameters) that the branch
then splices into its `"WHEN %(condition)s THEN %(result)s"` template.

## Operation correspondence
| # | Lean op (`implementation_resolveBranchCondition`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut condSql := conditionSql` | `condition_sql` from `compiler.compile(self.condition)` (the input) | I | the guard-fragment accumulator starts at the rendered branch-predicate fragment. The compile step itself is upstream; its result enters as the input `conditionSql` (mapping.md). |
| 2 | `let mut condParams := conditionParams` | `condition_params` from `compiler.compile(self.condition)` (the input) | I | the parameter accumulator starts at the rendered branch-predicate parameters; enters as input `conditionParams`. |
| 3 | `if condSql == "" then` | `if condition_sql == "":` | R | Python `str` empty-string test ↔ Lean `String` `== ""`. Type bijection in mapping.md (`condition_sql : str` ↔ `conditionSql : String`). |
| 4 | `condSql := trueSql` | `condition_sql, _ = compiler.compile(Value(True))` (first component) | R | wholesale replacement of the guard fragment by the rendered always-satisfied stand-in fragment. The compile of `Value(True)` is upstream; its first result enters as input `trueSql` (mapping.md). |
| 5 | `condParams := trueParams` | `_, condition_params = compiler.compile(Value(True))` (second component) | R | wholesale replacement of the bound parameters by the stand-in fragment's parameters; enters as input `trueParams`. |
| 6 | `return (condSql, condParams)` | the `(condition_sql, condition_params)` pair as used by the subsequent `template_params["condition"] = condition_sql` / `sql_params.extend(condition_params)` | I | return the chosen guard pair (what the template formatting consumes). |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of an
unchanged callee — `compiler.compile(self.condition)` and
`compiler.compile(Value(True))` enter as DATA per mapping.md). Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the block is simply
`condition_sql, condition_params = compiler.compile(self.condition)` with NO
emptiness check — the empty guard fragment is spliced directly into the template,
producing `... WHEN  THEN ...` (a malformed predicate), which is the
`ProgrammingError: syntax error at or near "THEN"` in the issue. The prepatch impl
(`implementation_resolveBranchCondition := return (conditionSql, conditionParams)`,
never substituting) is exactly this: it returns the original pair unconditionally,
never replacing the empty guard with the always-true stand-in. It therefore cannot
satisfy `problem_spec_resolveBranchCondition` on the discriminating clause
(`conditionSql = "" → result = (trueSql, trueParams)`) whenever
`(trueSql, trueParams) ≠ ("", conditionParams)` — e.g. with a non-empty stand-in
fragment (`trueSql = "%s"`) while the original guard fragment is empty, so the
clause is violated. This is precisely the case the
FAIL_TO_PASS test `test_annotate_with_full_when` exercises (a `When(~Q(pk__in=[]),
…)` whose guard compiles to the empty string). The carried gold proof fails to
typecheck against the buggy impl (G-DIFF).
