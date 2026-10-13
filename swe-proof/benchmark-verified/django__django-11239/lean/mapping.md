# mapping.md — django__django-11239

## Symbol binding (file:line @ base_commit d87bd29c4f8dfcdf3f4a4eb8340e6770a2416fe3)

Modeled function: the class method that assembles the PostgreSQL interactive
shell invocation from a connection-parameter mapping, in
`django/db/backends/postgresql/client.py`,
`DatabaseClient.runshell_db(cls, conn_params)` (`:11-39`).

The method does two observable things before launching the child process:

1. Builds the command-line argument list `args` (`:13-27`):
   ```python
   args = [cls.executable_name]            # 'psql'
   ... read host/port/dbname/user/password from conn_params.get(k, '')
   if user: args += ['-U', user]
   if host: args += ['-h', host]
   if port: args += ['-p', str(port)]
   args += [dbname]
   ```
2. Builds the child-process environment `subprocess_env` (`:30-32`, pre-patch):
   ```python
   subprocess_env = os.environ.copy()
   if passwd: subprocess_env['PGPASSWORD'] = str(passwd)
   ```
   then calls `subprocess.run(args, check=True, env=subprocess_env)` (`:36`).

The gold patch adds, alongside the existing `passwd` handling, four more
connection parameters read with `conn_params.get(k, '')` (`sslmode`,
`sslrootcert`, `sslcert`, `sslkey`) and, when each is non-empty, sets the
corresponding libpq environment variable in `subprocess_env`
(`PGSSLMODE`, `PGSSLROOTCERT`, `PGSSLCERT`, `PGSSLKEY`). libpq (used by the
`psql` client) reads TLS configuration from exactly those environment variables,
so this makes the interactive shell honor the same mutual-TLS configuration the
ORM connection already supports.

Why it fixes the issue: pre-patch, a connection configured with the four SSL
`OPTIONS` keys launches `psql` with NONE of the TLS environment variables set,
so the interactive shell cannot present the client certificate/key the database
requires. The added assignments propagate each supplied SSL parameter to its
libpq environment variable. The FAIL_TO_PASS test `test_ssl_certificate` drives
`runshell_db` with the four SSL params and asserts the captured `PG*` environment
is exactly `{PGSSLCERT, PGSSLKEY, PGSSLMODE, PGSSLROOTCERT}`.

Lean modeled function name: `runShell` (neutral — names the *behavior*
"assemble the database shell invocation"; shares no substring with the patched
method name `runshell_db`/`runshell` of length ≥4 after underscore-stripping —
`runshelldb`/`runshell` vs `runShell` differ, and in any case the patch adds no
new def/class, so there are no patched def/class symbols).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `runShell` (modeled function) | `DatabaseClient.runshell_db` (`client.py:11-39`) |
| `ConnParams` field `host` | `conn_params.get('host', '')` (`:15`) |
| `ConnParams` field `port` | `conn_params.get('port', '')` (`:16`) |
| `ConnParams` field `dbname` | `conn_params.get('database', '')` (`:17`) |
| `ConnParams` field `user` | `conn_params.get('user', '')` (`:18`) |
| `ConnParams` field `password` | `conn_params.get('password', '')` (`:19`) |
| `ConnParams` field `sslmode` | `conn_params.get('sslmode', '')` (added, post-patch `:20`) |
| `ConnParams` field `sslrootcert` | `conn_params.get('sslrootcert', '')` (added) |
| `ConnParams` field `sslcert` | `conn_params.get('sslcert', '')` (added) |
| `ConnParams` field `sslkey` | `conn_params.get('sslkey', '')` (added) |
| `ShellInvocation.args` | the `args` list passed to `subprocess.run` (`:36`) |
| `ShellInvocation.pgEnv` | the `PG`-prefixed keys/values set in `subprocess_env` |
| `"psql"` literal in `args` | `cls.executable_name` (`:9`) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean |
|---|---|
| `conn_params` (a `dict[str, Any]`) restricted to the 9 read keys | `ConnParams` (9 `String` fields) |
| `conn_params.get(k, '')` | the corresponding `String` field; **`""` ⇔ key absent** |
| `if x:` truthiness on a `str` from `.get(k,'')` | `x ≠ ""` (a non-empty string is truthy; the only value `.get` yields here besides a real string is the `''` default) |
| `str(port)` / `str(passwd)` / `str(sslmode)` … | identity (every modeled value is already a `String`) |
| `args` = `list[str]` command line | `List String` |
| `subprocess_env` projected to its `PG*` keys (ordered by assignment) | `List (String × String)` |
| `subprocess.run(args, env=subprocess_env)` observable | `ShellInvocation { args, pgEnv }` |

### `os.environ.copy()` projection note (an R refinement)
`subprocess_env` starts as a copy of the whole process environment, then has
`PG*` keys ADDED to it (never read, never removed). The FAIL_TO_PASS / PASS_TO_PASS
tests observe `{key: env[key] for key in env if key.startswith('PG')}` — i.e. the
`PG`-prefixed projection of the final environment. The model therefore tracks ONLY
the `PG*` entries the method explicitly sets, in assignment order
(`PGPASSWORD`, then `PGSSLMODE`, `PGSSLROOTCERT`, `PGSSLCERT`, `PGSSLKEY`). This is
sound for the modeled behavior because the method never sets a non-`PG` key and
never sets two values for the same key, and the harness environment contributes no
pre-existing `PG*` key (the official tests assert exact `PG*` dicts). Tagged **R**
in refinement.md.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom, and none is deeply modeled as an
  A-reference.** Every operation the method uses is a primitive modeled as an
  identical concrete op (I) or a type refinement (R): `dict.get(k, '')` → field
  access with `""` default; string truthiness → `≠ ""`; `str()` on a string →
  identity; `list +=` → `++`; dict assignment → list append of a `(key, value)`
  pair. Hence `axioms = []` and `deep_model_references = []`; `axiom_check.py`
  is a `status=skip` stub (G-AX), and the R/I behavior is differential-tested by
  `conformance_check.py` (G-CONF).
- No flag dependency: each SSL parameter is handled by an independent
  non-emptiness guard; there is no mode flag gating the per-parameter behavior.

## G-LEAK
The solver-visible `problem_statement` names `sslmode`, `sslrootcert`, `sslcert`,
`sslkey`, `dbshell`, client certificate/key, and mutual TLS. It does NOT name the
libpq environment variables `PGSSLMODE`/`PGSSLROOTCERT`/`PGSSLCERT`/`PGSSLKEY`/
`PGPASSWORD`, but those are string-literal dict KEYS in the patch, not def/class
names, so the mechanical screen does not flag them; and naming them in the spec
states the *desired behavior* (which libpq variable each parameter must populate)
rather than the edit or its diagnosis. The patch adds no def/class, so there is no
patched repo symbol for a spec-view identifier to embed. The spec view narrates no
bug→fix mechanism and reproduces no gold-diff line. The modeled-function identifier
`runShell` shares no patched def/class name.

## Pinned G-CONF fuzz seed
`11239`.
