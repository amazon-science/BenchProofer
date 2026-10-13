# mapping.md — django__django-13346

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9c92924cd5d164701e2514e1c2d6574126bd7cc2`, states the type
abstraction, and gives the provenance of the modeled behaviour.

Repo file under change: `django/db/models/fields/json.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `process_membership_rhs(num_values)` | the new `KeyTransformIn.process_rhs(self, compiler, connection)` — `django/db/models/fields/json.py` (gold adds it after line 380, registered at line 482 via `KeyTransform.register_lookup(KeyTransformIn)`) | the modeled changed function: the membership-lookup right-hand-side comparison-string production on a non-native-JSON backend |
| `slots_sql(n)` *(deep model — A-reference)* | the per-slot expansion `rhs % func` with `func = ("JSON_EXTRACT(%s, '$')",) * len(rhs_params)` (the `elif connection.vendor in {'sqlite', 'mysql'}` branch of `KeyTransformIn.process_rhs`) | pure spec: the comparison string is the wrapped per-value slot, validated `slots_sql == real slot-wrapping` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `wrapped_slot()` | the literal SQL wrapper `"JSON_EXTRACT(%s, '$')"` | pure spec: one value compared against the extracted document scalar |
| `bare_slot()` | the pre-fix base-class slot `"%s"` (what `In.process_rhs` returns unmodified — `django/db/models/lookups.py:383-385`) | pure spec: the un-wrapped slot (the bug) — used only in `model_prepatch.py`'s impl |
| `sep()` | the `', '` join separator inside the base-class placeholder `'(' + ', '.join(sqls) + ')'` (`django/db/models/lookups.py:384`) | pure spec: separator between slots |

The base-class `In.process_rhs` (`django/db/models/lookups.py:362-390`) is the
UNCHANGED producer of the bare placeholder string `'(' + ', '.join(['%s']*n) +
')'`; the fix wraps each `%s` via `rhs % func`. The outer parentheses and the
comma-space joins are produced identically pre- and post-fix; only the per-slot
content changes (`%s` → `JSON_EXTRACT(%s, '$')`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the comparison `str` produced by `process_rhs` (`rhs`) | `List[int]` of code points; specification over `PSeq[int]` | `s[k]` ↔ `result[k] == ord(s[k])`; `len(s)` ↔ `len(result)`; `str` concatenation ↔ list `+`; an empty `str` ↔ `[]` |
| the count of right-hand-side values `len(rhs_params)` | `int` `num_values` (`>= 1`) | one value slot per right-hand-side value; the membership set is non-empty when comparison-string production is reached (`In.process_rhs` raises `EmptyResultSet` for an empty rhs at `django/db/models/lookups.py:378-379`, so `num_values >= 1`) |
| the outer parentheses `'(' ... ')'` of the base placeholder | omitted (identical pre/post-fix) | the parens are produced by the unchanged base class and unchanged by the fix; the discriminating content is the inner per-slot expansion, which is what `slots_sql` models. axiom_check.py reproduces the FULL real string `rhs % func` and strips the identical parens before comparing. |
| the bind parameters `rhs_params` | omitted (unchanged by the modeled branch) | on the sqlite/mysql branch the fix touches only `rhs` (the placeholder string); `rhs_params` passes through unchanged, so it is not part of the modeled output |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Provenance of the modeled behaviour (checked by G-AX / axiom_check.py)

### 3.1 `slots_sql` deep model ↔ the real slot-wrapping (A-reference)
**Modeled operation:** `KeyTransformIn.process_rhs`'s slot-wrapping on a
backend without a native JSON type. The gold hunk:

```python
class KeyTransformIn(lookups.In):
    def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        if not connection.features.has_native_json_field:
            func = ()
            ...
            elif connection.vendor in {'sqlite', 'mysql'}:
                func = ("JSON_EXTRACT(%s, '$')",) * len(rhs_params)
            rhs = rhs % func
        return rhs, rhs_params
```

The base `rhs` (from `In.process_rhs`, `django/db/models/lookups.py:383-385`)
is `'(' + ', '.join(['%s'] * n) + ')'`. With `func` a tuple of `n` copies of
`"JSON_EXTRACT(%s, '$')"`, the `%`-substitution replaces each `%s` slot by the
wrapper, giving inner content
`"JSON_EXTRACT(%s, '$'), JSON_EXTRACT(%s, '$'), ..."` — exactly `slots_sql(n)`.

This is the changed string operation, modeled **deeply** by the `@Pure` fold
`slots_sql` (with `wrapped_slot`/`sep`) in the `pure` region; there is **no
`process_rhs` axiom** the proof consumes. The deep model is validated equal to
the real operation out-of-band by axiom_check.py (G-AX), which reproduces
`rhs % func` exactly and asserts `slots_sql(n) == that inner expansion` on
boundary (`n = 1, 2, 3, 4, 5, 10, 32, 100`, the single-element case the issue is
specifically about included) and 5000 fuzzed counts.

**Flag/branch dependency (recorded for G-AX):** the wrapper `JSON_EXTRACT(%s,
'$')` is the SQLite/MySQL branch (`connection.vendor in {'sqlite', 'mysql'}`),
which the FAIL_TO_PASS test (`test_key_in`, run on SQLite in the harness image)
exercises. The MariaDB branch wraps with `JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))`
and the Oracle branch builds `JSON_QUERY`/`JSON_VALUE` per value; those branches
are not on the tested SQLite path. The PostgreSQL path
(`has_native_json_field` true) is unchanged and short-circuits before any
wrapping — the bug never manifested there. The harness resolves `test_key_in`
on SQLite, so the modeled branch is the tested one.

No standard-library or repo callee behaviour is *axiomatized*: the wrapper is a
fixed SQL string constant and the `%`-substitution is a plain Python string
operation, both spelled out. axiom_check.py imports nothing repo-specific.
