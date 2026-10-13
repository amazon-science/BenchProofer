# refinement.md — django__django-14376

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_db_arg` impl region and the deep `select_name` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The client-argument selection — `settings_to_cmd_args_env` (`django/db/backends/mysql/client.py:7`)

Gold hunk 1 (`client.py:11`):
```
- db = settings_dict['OPTIONS'].get('db', settings_dict['NAME'])
+ database = settings_dict['OPTIONS'].get(
+     'database',
+     settings_dict['OPTIONS'].get('db', settings_dict['NAME']),
+ )
```
Gold hunk 2 (`client.py:54-55`):
```
- if db:
-     args += [db]
+ if database:
+     args += [database]
```

| # | model.py impl op (`resolve_db_arg`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `opt_database, opt_db: Optional[List[int]]`, `settings_name: List[int]` | `settings_dict['OPTIONS'].get('database', …)`, `…get('db', …)`, `settings_dict['NAME']` | R | `OPTIONS.get(k, fb)` present/absent ↔ `Optional[List[int]]` (`None` = absent); database-name `str` ↔ `List[int]` of code points (mapping.md §2). |
| A2 | the branch `if opt_database is not None: chosen = opt_database; elif opt_db is not None: chosen = opt_db; else: chosen = settings_name`, captured purely by `select_name` | the nested `OPTIONS.get('database', OPTIONS.get('db', NAME))` | A-reference | the changed selection is modeled **deeply**: `select_name` (the spelled-out three-level precedence in the `pure` region) and the impl branch ARE the selection. There is no consumed selection axiom — the proof never depends on one. Instead the deep model is validated **== the real gold-patched callee** out-of-band: G-AX (axiom_check.py) runs the real `settings_to_cmd_args_env` over all option combinations + fuzz and asserts the trailing database argument == `select_name` (mapping.md §3.1). A present `OPTIONS` key short-circuits the fallback even when its value is empty, matching `dict.get`. |
| A3 | `appended = len(database) > 0`; result reports `(appended, database)` | `if database: args += [database]` | R + I | the truthiness test `if database:` on a `str` ↔ `len(...) > 0` on the code-point list (empty string falsy; mapping.md §2). The conditional append is I (identical control flow); whether the name is appended is reported by `appended` and pinned by `Result()[0] == (len(Result()[1]) > 0)`. |
| A4 | the selected name copied code-point-by-code-point into a freshly-owned `List[int]` (`Result()[1]`) | the `str` value placed into the argument list as a trailing positional argument | R | `str` value ↔ its code-point list; the copy makes the returned argument value genuinely owned at full permission, independent of the read-only inputs (directive 5). Content is preserved: `ToSeq(Result()[1]) == select_name(...)`. |

The discriminating content of the change — the non-deprecated `database` option
taking precedence over the legacy `db` option — lives in the FIRST branch of
`select_name`/`resolve_db_arg` (`if opt_database is not None: chosen =
opt_database`) ⇔ the OUTER `.get('database', …)` of the gold expression. The
pre-patch code consulted only `.get('db', NAME)`; `model_prepatch.py` reproduces
that (drops the `opt_database` branch, selecting `opt_db` then `settings_name`)
and **fails** the postcondition `ToSeq(Result()[1]) == select_name(opt_database,
opt_db, ToSeq(settings_name))`, which is exactly the spec sensing the change
(G-DIFF). This is the behaviour the F2P test
`test_options_non_deprecated_keys_preferred` observes (both `database` and `db`
present ⇒ the `database` value must be chosen), and the changed precedence in
`test_options_override_settings_proper_values` / `test_parameters`.

## B. The connection-keyword hunk (`base.py`) — kind-I, not differentially observable

Gold hunk 3 (`django/db/backends/mysql/base.py:203-205`):
```
- kwargs['db'] = settings_dict['NAME']
+ kwargs['database'] = settings_dict['NAME']
- kwargs['passwd'] = settings_dict['PASSWORD']
+ kwargs['password'] = settings_dict['PASSWORD']
```

This is a pure connection-keyword rename consumed by `mysqlclient`'s
`Database.connect(**kwargs)`. It is **not exercised by any FAIL_TO_PASS or
PASS_TO_PASS test** (all of which are in `tests/dbshell/test_mysql.py` and call
only the client of site A); observing it would require a live mysqlclient
connection. It is shipped verbatim in `patch.diff` (the real patch is the gold)
but produces no model-sensible differential on the tested inputs, so it is not
modeled and has no `model_prepatch` variant (mapping.md §4). It is a kind-I
rename of dict keys at the call boundary, not a changed algorithm.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* and is F2P-observable — the database-name selection precedence — is
modeled **deeply** (the spelled-out three-level `select_name` consumed in
`resolve_db_arg`, step A2, an **A-reference**), not hidden behind an axiom about
the function under change: there is no consumed selection axiom. There are no
A-consumed axioms in this bundle (no unchanged opaque callee is relied upon
inside an `Ensures`).

## D. verify(model) ⇒ resolved

`resolve_db_arg` verifies only if its selected name equals the three-level
precedence selection with the non-deprecated option preferred (A2) and only if
the trailing argument is appended exactly when non-empty (A3). By R (str ↔
List[int], `dict.get` ↔ `Optional`, truthiness ↔ `len>0`) the verified
selection equals `OPTIONS.get('database', OPTIONS.get('db', NAME))` and the
gold append on the tested `str` inputs; by G-AX the deep model `select_name`
equals the real gold-patched `settings_to_cmd_args_env` selection (A-reference).
The `base.py` rename (B) is shipped verbatim and is correctness-neutral on the
tested inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The one trust point is refinement fidelity (this document, G-EQ)
plus the G-AX validation of the deep model against the real callee.
