# refinement.md — django__django-11239

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_pg_env` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**, the
proof uses the axiom's `Ensures`; **A-reference**, a deep model validated == the
real operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

## A. The PG-environment publication — `runshell_db` (`postgresql/client.py`)

Gold hunks (`DatabaseClient.runshell_db`): read the four new settings and
publish them under their dedicated PG* environment variables, alongside the
pre-existing password publication.
```
+        sslmode = conn_params.get('sslmode', '')
+        sslrootcert = conn_params.get('sslrootcert', '')
+        sslcert = conn_params.get('sslcert', '')
+        sslkey = conn_params.get('sslkey', '')
         ...
         if passwd:
             subprocess_env['PGPASSWORD'] = str(passwd)
+        if sslmode:
+            subprocess_env['PGSSLMODE'] = str(sslmode)
+        if sslrootcert:
+            subprocess_env['PGSSLROOTCERT'] = str(sslrootcert)
+        if sslcert:
+            subprocess_env['PGSSLCERT'] = str(sslcert)
+        if sslkey:
+            subprocess_env['PGSSLKEY'] = str(sslkey)
```

Model function: `build_pg_env(conn_params)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `conn_params: Dict[int, int]` | the `conn_params` `dict` (str→str) argument | R | connection-settings `dict` ↔ `Dict[int,int]` of setting/value tokens (mapping.md §2); only membership/value/which-names-present are observed. |
| A2 | `if setting_password() in conn_params: env[envvar_password()] = conn_params[setting_password()]` | `passwd = conn_params.get('password','')`; `if passwd: subprocess_env['PGPASSWORD'] = str(passwd)` | R + I | `.get(k,'')` then `if value:` is "supplied non-empty" ↔ key-token present (mapping.md §2); the conditional write is identical; `str()` is identity on the value token (mapping.md §2); `'password'`↔`0`, `'PGPASSWORD'`↔`100`. |
| A3 | `if setting_sslmode() in conn_params: env[envvar_sslmode()] = conn_params[setting_sslmode()]` | `sslmode = conn_params.get('sslmode','')`; `if sslmode: subprocess_env['PGSSLMODE'] = str(sslmode)` | R + I | as A2; `'sslmode'`↔`1`, `'PGSSLMODE'`↔`101`. |
| A4 | `if setting_sslrootcert() in conn_params: env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]` | `sslrootcert = conn_params.get('sslrootcert','')`; `if sslrootcert: subprocess_env['PGSSLROOTCERT'] = str(sslrootcert)` | R + I | as A2; `'sslrootcert'`↔`2`, `'PGSSLROOTCERT'`↔`102`. |
| A5 | `if setting_sslcert() in conn_params: env[envvar_sslcert()] = conn_params[setting_sslcert()]` | `sslcert = conn_params.get('sslcert','')`; `if sslcert: subprocess_env['PGSSLCERT'] = str(sslcert)` | R + I | as A2; `'sslcert'`↔`3`, `'PGSSLCERT'`↔`103`. |
| A6 | `if setting_sslkey() in conn_params: env[envvar_sslkey()] = conn_params[setting_sslkey()]` | `sslkey = conn_params.get('sslkey','')`; `if sslkey: subprocess_env['PGSSLKEY'] = str(sslkey)` | R + I | as A2; `'sslkey'`↔`4`, `'PGSSLKEY'`↔`104`. |
| A7 | `return env` (the published mapping) | `subprocess_env` handed to `subprocess.run(args, ..., env=subprocess_env)` | R | the model's `Result()` is the PG* restriction of the launched shell's environment (mapping.md §2); the F2P test inspects exactly `{k: env[k] for k in env if k.startswith('PG')}`. Inherited non-PG entries (from `os.environ.copy()`) are outside the modeled behaviour. |

The whole publication is also validated **as one A-reference**: G-AX
(`axiom_check.py`) runs the real `runshell_db` and asserts the published PG*
mapping equals the deep model `build_pg_env` on boundary + fuzz inputs
(mapping.md §3.1). No consumed axiom is involved.

The discriminating content of the change — the four TLS settings each reach the
launched shell under their dedicated PG* variable — lives in the SSL
biconditionals A3–A6 (model) ⇔ the four added `if ...: subprocess_env['PGSSL*']
= str(...)` writes (real). The pre-patch code published only `PGPASSWORD`;
`model_prepatch.py` reproduces that (the impl writes only the password entry)
and **fails** the postcondition
`(envvar_sslmode() in Result()) == (setting_sslmode() in conn_params)`
(the first SSL biconditional Z3 reaches), which is exactly the spec sensing the
change (G-DIFF). The F2P `test_ssl_certificate` is the matching observation: a
TLS-configured connection must yield `{PGSSLMODE, PGSSLROOTCERT, PGSSLCERT,
PGSSLKEY}` in the published environment.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely **changed** — the
per-setting publication of the four TLS settings — is modelled **deeply** (the
spelled-out conditional writes in `build_pg_env`'s impl region; an
**A-reference**, validated == the real `runshell_db` PG* publication by G-AX),
not hidden behind an axiom about the function under change. There is **no
consumed axiom** (no `@ContractOnly`): the bundle ships zero dead axioms.

## C. verify(model) ⇒ resolved

`build_pg_env` verifies only if, for each of the five settings, the dedicated PG*
variable is present in the result exactly when that setting is supplied and then
carries its value (the five biconditionals + value clauses), and only if the
result publishes no variable outside the five dedicated names (the no-spurious
clause). By R (`dict` str/str ↔ `Dict[int,int]`, `.get(k,'')`+`if value:` ↔
key-token presence, `str()` identity) the verified publication equals the gold
patch's conditional `subprocess_env['PG*'] = str(...)` writes on the tested
connection parameters; by G-AX the deep model equals the real `runshell_db` PG*
publication (A-reference). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The one trust point is refinement fidelity (this document, G-EQ),
plus the A-reference soundness check (G-AX); there is no consumed-axiom trust
point.
