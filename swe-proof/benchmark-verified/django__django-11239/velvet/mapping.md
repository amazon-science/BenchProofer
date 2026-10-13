# mapping.md — django__django-11239

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d87bd29c4f8dfcdf3f4a4eb8340e6770a2416fe3`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms** in this bundle (the changed region
calls no library function whose behaviour the proof must assume); every step is
**R** (type refinement) or **I** (identical concrete op).

Repo file under change:
`django/db/backends/postgresql/client.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `clientEnv (password sslmode sslrootcert sslcert sslkey : List Char)` | the connection-environment construction inside `DatabaseClient.runshell_db(cls, conn_params)` — `django/db/backends/postgresql/client.py:12` (env block lines 19, 30–32 pre-patch) | the modeled changed function: builds the set of connection options forwarded to the spawned client process |
| `forwardedEnv` *(pure, deep model)* | the same env-construction logic, post-patch (lines 19, 23–26 and 31–47 of the patched file) | pure spec: which options are forwarded, given their values |
| `optKey` *(pure)* | the literal option keys read from `conn_params` (`'password'`, `'sslmode'`, `'sslrootcert'`, `'sslcert'`, `'sslkey'`) | the canonical option-name carried as the forwarded entry's key |

The five forwarded options correspond to these `conn_params` reads in
`runshell_db` (all `conn_params.get(<key>, '')`):

| option (model key, public) | `conn_params` key | repo line @ base_commit | added by patch? |
|---|---|---|---|
| `password` | `'password'` | client.py:19 (read), :31–32 (forward) | no — pre-existing, unchanged |
| `sslmode` | `'sslmode'` | added at client.py:20 (read), :37–38 (forward) | **yes** |
| `sslrootcert` | `'sslrootcert'` | added at client.py:21 (read), :39–40 (forward) | **yes** |
| `sslcert` | `'sslcert'` | added at client.py:22 (read), :41–42 (forward) | **yes** |
| `sslkey` | `'sslkey'` | added at client.py:23 (read), :43–44 (forward) | **yes** |

The four `ssl*` option keys are the public names quoted verbatim in the issue's
`OPTIONS` block (`problem_statement`); `password` is the pre-existing,
issue-independent option whose handling the patch leaves untouched (modeled to
pin the unchanged frame — directive 5).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an option value `str` (e.g. `conn_params.get('sslmode','')`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; empty/absent option (`''`, the `get` default) ↔ `[]` |
| `if <opt>:` truthiness test | `<opt> ≠ []` | a Python `str` is falsy iff empty; absent key defaults to `''` → falsy. So "option is set" ↔ the `List Char` is non-empty. |
| `str(<opt>)` coercion in the forward (`str(sslmode)` …) | identity on the `List Char` | the option values the F2P/P2P tests pass are already `str`; `str()` is observationally the identity on them (cf. 11951 `bulk_batch_size` floor / 11276 `mark_safe`). |
| the **forwarded entry's key** — repo writes the OS-environment variable name (`PGPASSWORD`, `PGSSLMODE`, `PGSSLROOTCERT`, `PGSSLCERT`, `PGSSLKEY`) | the model uses the **option name** (`"password"`, `"sslmode"`, `"sslrootcert"`, `"sslcert"`, `"sslkey"`) | a fixed bijection between the two name sets (see table below). The forwarding *mechanism* (an environment variable on the client subprocess) is an implementation detail not observed at the option level; G-CONF re-applies this bijection to compare the model's option-keyed map against the real per-process environment. |
| the forwarded set (repo: the `PG*` entries of the child process environment, the F2P test's observed `dict`) | `List (String × List Char)` of `(optionName, value)` pairs, source order | order-preserving; the test compares the forwarded mapping as a set/dict, so order is immaterial but the model emits the deterministic source order (password, then the four ssl options) |

### Option-name ↔ environment-variable bijection (used by G-CONF only)

| model key (public option name) | repo environment variable |
|---|---|
| `"password"` | `PGPASSWORD` |
| `"sslmode"` | `PGSSLMODE` |
| `"sslrootcert"` | `PGSSLROOTCERT` |
| `"sslcert"` | `PGSSLCERT` |
| `"sslkey"` | `PGSSLKEY` |

This bijection is the single R-refinement of the entry key. It lives here (not in
the consumer-visible `Solution.lean`) because the environment-variable names are
NOT in the public `problem_statement` and naming them in the spec view would leak
the fix mechanism (directive 6).

## 3. Callee provenance

**None consumed.** The changed region calls no library function whose result the
proof must assume: the construction is a closed function of the five option
values (`dict.get` with a default, a truthiness test, and a string-keyed
assignment — all transliterated I/R ops). `os.environ.copy()`, `signal.*`, and
`subprocess.run` are unchanged by the patch, are not part of the forwarded-option
behaviour the F2P test observes, and are abstracted away (the test mocks
`subprocess.run`). Hence there is **no `axiom`, no deep-model A-reference, and no
`axiom_check.py`** (G-AX = skip). All refinement legs are R/I, fully covered by
G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11239`** so the
consumer-side verdict is reproducible. The ORACLE runs the **real patched**
`DatabaseClient.runshell_db` in-container (mocking `subprocess.run`, exactly as
the repo's own `tests/dbshell/test_postgresql.py::_run_it` does) and captures the
`PG*` subset of the child-process environment. The SHADOW transliterates
`forwardedEnv` (R/I ops) to Python over the real `str` type and re-keys it
through the §2 option→environment-variable bijection. They must agree on every
fuzzed `conn_params`.
