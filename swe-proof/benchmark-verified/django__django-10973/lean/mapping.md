# mapping.md — django__django-10973

## Symbol binding (file:line @ base_commit ddb293685235)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_dbShellCommand` | `DatabaseClient.runshell_db(cls, conn_params)` | `django/db/backends/postgresql/client.py:19-68` |
| input `host`  | `conn_params.get('host', '')`     | client.py:23 |
| input `port`  | `conn_params.get('port', '')`     | client.py:24 |
| input `dbname`| `conn_params.get('database', '')` | client.py:25 |
| input `user`  | `conn_params.get('user', '')`     | client.py:26 |
| input `passwd`| `conn_params.get('password', '')` | client.py:27 |
| result `.1` (`List String`) | the `args` list passed to the subprocess invocation | client.py:21-35 |
| result `.2` (`Option String`) | the `PGPASSWORD` entry of the subprocess environment (post-fix) | client.py (gold patch) |

## Lean ↔ Python type bijection (used by G-CONF, G-AX)

- Python `str` connection-parameter values ↔ Lean `String`. Each of
  host/port/dbname/user/passwd arrives from `conn_params.get(k, '')`, so the
  default is the empty string `''` ↔ Lean `""`.
- `port`: Python does `str(port)`; in the conn_params dict the value is already a
  string (e.g. `'444'`), so the bijection is `port : String` with `str(port) = port`.
  The Python truthiness test `if port:` ↔ `port ≠ ""`. Likewise `if user:`,
  `if host:`. `str(passwd)` ↔ `passwd` (already a `String`).
- The command line `args : list[str]` ↔ `List String`. The executable name
  `cls.executable_name = 'psql'` ↔ the literal head `"psql"`.
- The subprocess environment's password entry ↔ `Option String`: it is **set** to
  the raw password value exactly when `passwd` is truthy, and **absent**
  otherwise. `env.get('PGPASSWORD')` returning the value ↔ `some passwd`;
  returning `None` (entry never set) ↔ `none`. (This is precisely the 2-tuple the
  F2P tests' mock observes: `(self.subprocess_args, env.get('PGPASSWORD'))`.)

## Scoping assumption (ambient environment)

The post-patch code does `subprocess_env = os.environ.copy()` and then sets
`PGPASSWORD` only when `passwd` is truthy. Strictly, if the PARENT process already
exported `PGPASSWORD`, then for an empty `passwd` the child would inherit that
ambient value rather than nothing. The observable contract modeled here — and the
one the FAIL_TO_PASS harness checks (`env.get('PGPASSWORD')` with `test_nopass`
expecting `None`) — is evaluated under a clean ambient environment with no
pre-existing `PGPASSWORD`. The `Option String` second component therefore models
the password **the function itself provisions** for the child: `some passwd` iff
`passwd ≠ ""`, else `none`. `conformance_check.py` clears any ambient
`PGPASSWORD` before driving the real code, matching this harness condition, so the
R/I differential is exact. Effects outside this observable pair (the SIGINT
save/restore, the temp-file side channel removed by the fix, other env entries)
are out of model scope.

## Callee provenance + flag deps

- No UNCHANGED callee requires an `opaque` signature. The command-line assembly
  and the password-environment computation are both modeled concretely
  (literal-driven list construction + a single conditional), so the axioms region
  is empty. The subprocess invocation itself (process spawn) is an effect outside
  the observable contract and is not modeled — only the `(args, PGPASSWORD)`
  inputs handed to it are, which is exactly what the harness observes.
- No flag-dependent callee.

## G-CONF fuzz seed

Pinned seed: `10973` (see `conformance_check.py`, `SEED = 10973`).
