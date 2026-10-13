# mapping.md — django__django-11239

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d87bd29c4f8dfcdf3f4a4eb8340e6770a2416fe3`, states the type
abstraction, and gives the provenance for the deep-model A-reference.

Repo file under change: `django/db/backends/postgresql/client.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_pg_env(conn_params)` | the PostgreSQL-environment-building portion of `DatabaseClient.runshell_db(cls, conn_params)` — `django/db/backends/postgresql/client.py:12` (env construction lines 19, 30-32 pre-patch) | the modeled changed function: builds the `subprocess_env` PG* variables from `conn_params` |
| `setting_password()` = 0 | the `conn_params.get('password', '')` key `'password'` (line 19) | input setting-name token |
| `setting_sslmode()` = 1 | `conn_params.get('sslmode', '')` key `'sslmode'` (added by patch) | input setting-name token |
| `setting_sslrootcert()` = 2 | `conn_params.get('sslrootcert', '')` key `'sslrootcert'` (added by patch) | input setting-name token |
| `setting_sslcert()` = 3 | `conn_params.get('sslcert', '')` key `'sslcert'` (added by patch) | input setting-name token |
| `setting_sslkey()` = 4 | `conn_params.get('sslkey', '')` key `'sslkey'` (added by patch) | input setting-name token |
| `envvar_password()` = 100 | the environment-variable name `'PGPASSWORD'` (line 32 / patch) | output env-var-name token |
| `envvar_sslmode()` = 101 | `'PGSSLMODE'` (patch) | output env-var-name token |
| `envvar_sslrootcert()` = 102 | `'PGSSLROOTCERT'` (patch) | output env-var-name token |
| `envvar_sslcert()` = 103 | `'PGSSLCERT'` (patch) | output env-var-name token |
| `envvar_sslkey()` = 104 | `'PGSSLKEY'` (patch) | output env-var-name token |

The pre-patch repo computed only the `PGPASSWORD` entry (`if passwd:
subprocess_env['PGPASSWORD'] = str(passwd)`); the four `sslmode/sslrootcert/
sslcert/sslkey` settings were never read and never published.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `conn_params` (a `dict` of `str -> str`, the connection settings) | `Dict[int, int]` of setting-name token -> value token | a string key `'password'/'sslmode'/...` ↔ its token `0..4`; a string value ↔ an `int` value token. Only membership / per-key value / which names are present are observed by the F2P test, so integer identity is faithful. |
| `conn_params.get(k, '')` returning a non-empty string, then the `if value:` guard | the key `k`'s token being **present** in the `Dict[int,int]` | `.get(k,'') ` is `''` (falsy, skipped) exactly when `k` is absent or maps to `''`; the F2P test never supplies an explicit empty value, so "supplied non-empty value" ↔ "token present in the model dict". Absent-or-empty both leave the variable unset, modelled identically by token absence. |
| `subprocess_env` (the launched shell's environment `dict`, `str -> str`), restricted to the PG* credential / transport-security variables | `Dict[int, int]` of env-var-name token -> value token (the `Result()`) | the PG* keys `'PGPASSWORD'/'PGSSLMODE'/...` ↔ tokens `100..104`; values carried verbatim. The F2P test inspects exactly `{k: env[k] for k in env if k.startswith('PG')}`. |
| `str(value)` coercion when publishing (`subprocess_env['PGX'] = str(value)`) | identity on the value token | the F2P inputs are already `str`; `str()` is observationally the identity for them. |
| `os.environ.copy()` inherited entries (non-PG variables, plus any pre-existing PG variable) | omitted from the model | the F2P test observes only the PG* keys the publication writes; inherited non-PG entries are not part of the modeled behaviour. The test environment supplies no pre-existing `PG*` variable. |

`str` indexing/iteration is banned in Nagini, so settings and values are modelled
as `int` tokens; only membership/value/emptiness of the mappings are observed.

## 3. Callee provenance

This bundle has **no consumed axiom** (no `@ContractOnly`): the connection-setting
publication is the operation under change and is modelled **deeply** (the
per-setting conditional writes spelled out in `build_pg_env`'s impl region).

### 3.1 `build_pg_env` deep model ↔ the real `runshell_db` PG* publication (A-reference)
**Operation:** `DatabaseClient.runshell_db`'s construction of the PostgreSQL
process-environment variables (`django/db/backends/postgresql/client.py`,
post-patch lines reading `password/sslmode/sslrootcert/sslcert/sslkey` and
publishing `PGPASSWORD/PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY`). The changed
operation is modelled deeply by the verified `build_pg_env`; there is **no
publication axiom** the proof consumes. The deep model is validated equal to the
real operation out-of-band by `axiom_check.py` (G-AX), which runs the real
`runshell_db` (with `subprocess.run` intercepted, exactly as the repo's own
`tests/dbshell/test_postgresql.py` does) and asserts the published PG* mapping
equals the deep model on boundary + fuzz connection-parameter mappings.

The publication contract the deep model encodes, per setting:

  `password    -> PGPASSWORD`, `sslmode -> PGSSLMODE`,
  `sslrootcert -> PGSSLROOTCERT`, `sslcert -> PGSSLCERT`, `sslkey -> PGSSLKEY`,

each variable present (with the value verbatim) iff its setting is supplied
non-empty, and no other credential / transport-security variable published.

**Soundness check (G-AX):** `axiom_check.py` imports only the standard library
plus the repository package under evaluation (the very module the gold patch
edits). Each PG* variable corresponds to a single PostgreSQL libpq environment
variable (PostgreSQL docs: `PGPASSWORD`, `PGSSLMODE`, `PGSSLROOTCERT`,
`PGSSLCERT`, `PGSSLKEY` — https://www.postgresql.org/docs/current/libpq-envars.html);
the value is published verbatim via `str(value)`. Exit 0 iff every observation
matches the deep model.
