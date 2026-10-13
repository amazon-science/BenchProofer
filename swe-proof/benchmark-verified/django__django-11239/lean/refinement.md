# refinement.md — django__django-11239

Maps every operation in `implementation_runShell` to its `patch.diff`
counterpart (`DatabaseClient.runshell_db`,
`django/db/backends/postgresql/client.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed/used
op validated == real callee, **I** identical concrete op.

## Patch (the added behavior)
```python
sslmode     = conn_params.get('sslmode', '')
sslrootcert = conn_params.get('sslrootcert', '')
sslcert     = conn_params.get('sslcert', '')
sslkey      = conn_params.get('sslkey', '')
...
if sslmode:     subprocess_env['PGSSLMODE']     = str(sslmode)
if sslrootcert: subprocess_env['PGSSLROOTCERT'] = str(sslrootcert)
if sslcert:     subprocess_env['PGSSLCERT']     = str(sslcert)
if sslkey:      subprocess_env['PGSSLKEY']      = str(sslkey)
```
(The pre-existing user/host/port → `args` and `passwd` → `PGPASSWORD` lines are
unchanged by the patch but are part of the modeled function's observable output,
so they are modeled too — all I/R.)

## Operation correspondence
| # | Lean op (`implementation_runShell`) | patch.diff / base op | tag | note |
|---|---|---|---|---|
| 1 | `let mut args := ["psql"]` | `args = [cls.executable_name]` | I | `cls.executable_name == 'psql'` (class attribute, unchanged). |
| 2 | `if cp.user ≠ "" then args := args ++ ["-U", cp.user]` | `if user: args += ['-U', user]` | R | string truthiness ⇔ `≠ ""` (`.get(k,'')` yields a real string or the `''` default); `list +=` ⇔ `++`. |
| 3 | `if cp.host ≠ "" then args := args ++ ["-h", cp.host]` | `if host: args += ['-h', host]` | R | as #2. |
| 4 | `if cp.port ≠ "" then args := args ++ ["-p", cp.port]` | `if port: args += ['-p', str(port)]` | R | `str(port)` ⇔ identity (port modeled as `String`). |
| 5 | `args := args ++ [cp.dbname]` | `args += [dbname]` | I | database name always appended last. |
| 6 | `if cp.password ≠ "" then pgEnv := pgEnv ++ [("PGPASSWORD", cp.password)]` | `if passwd: subprocess_env['PGPASSWORD'] = str(passwd)` | R | dict assignment of a fresh `PG`-key ⇔ appending a `(name,value)` pair; `str(passwd)` ⇔ identity. |
| 7 | `if cp.sslmode ≠ "" then pgEnv := pgEnv ++ [("PGSSLMODE", cp.sslmode)]` | `if sslmode: subprocess_env['PGSSLMODE'] = str(sslmode)` (ADDED) | R | as #6. |
| 8 | `if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLROOTCERT", cp.sslrootcert)]` | `if sslrootcert: subprocess_env['PGSSLROOTCERT'] = str(sslrootcert)` (ADDED) | R | as #6. |
| 9 | `if cp.sslcert ≠ "" then pgEnv := pgEnv ++ [("PGSSLCERT", cp.sslcert)]` | `if sslcert: subprocess_env['PGSSLCERT'] = str(sslcert)` (ADDED) | R | as #6. |
| 10 | `if cp.sslkey ≠ "" then pgEnv := pgEnv ++ [("PGSSLKEY", cp.sslkey)]` | `if sslkey: subprocess_env['PGSSLKEY'] = str(sslkey)` (ADDED) | R | as #6. |
| 11 | `return { args, pgEnv }` | `subprocess.run(args, env=subprocess_env)` | R | the observable is `(args, PG*-projection of subprocess_env)`; see the `os.environ.copy()` projection note in mapping.md. |

Every op is **I** or **R** (a type refinement of a string/list primitive). There
is **no A-consumed row** (no opaque-axiom contract is consumed) and **no
A-reference row** (no external callee is deeply modeled). Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
`status=skip` stub. The R/I behavior is differential-tested against the real
post-patch `runshell_db` by `conformance_check.py` (G-CONF, `conf_skip=false`).

### `os.environ.copy()` projection (op #11) — why R is sound
The real `subprocess_env` is the full process environment with `PG*` keys added.
The official tests observe only `{k: env[k] for k in env if k.startswith('PG')}`.
The method sets exactly the `PG*` keys modeled (and only when the source param is
non-empty), never sets a non-`PG` key, and never overwrites a key, so the
`PG*`-projection of the real environment equals the modeled `pgEnv` list (as a
set of pairs). G-CONF compares the two as dicts (order-insensitive), matching the
test observation.

## Prepatch = the real bug
Pre-patch, `runshell_db` reads only `host/port/database/user/password` and injects
only `PGPASSWORD`; the four SSL parameters are never read and never propagated to
their libpq environment variables. The prepatch impl
(`implementation_runShell` with only the `PGPASSWORD` arm and no SSL arms) is
exactly this inherited behavior. It cannot satisfy `problem_spec_runShell`
whenever any SSL parameter is supplied — precisely the bug case: with
`sslmode/sslrootcert/sslcert/sslkey` set, `result.pgEnv` must contain
`PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY`, but the prepatch produces only
`PGPASSWORD` (or nothing), so `result.pgEnv ≠ specPgEnv cp`. This is the behavior
the FAIL_TO_PASS test `test_ssl_certificate` exercises (the four SSL params in,
the four `PGSSL*` env vars expected out). The carried gold-style proof body
(`simp [implementation_runShell, specPgEnv]`) fails to typecheck against the buggy
impl (G-DIFF), confirmed by `lean_verify` exit 1 (unsolved `pgEnv` goal).
