# refinement.md — django__django-11239

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`clientEnv` `do` block and the deep `forwardedEnv`/`forwardOne` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
bijection stated), **A** (axiomatized callee — none here), or **I** (identical
concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); this narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The forwarded-options site — the connection-environment block

Gold hunks (`django/db/backends/postgresql/client.py`): four new reads of ssl
options from `conn_params`, and four new conditional forwards of them into the
launched process's environment.

```
  passwd = conn_params.get('password', '')
+ sslmode = conn_params.get('sslmode', '')
+ sslrootcert = conn_params.get('sslrootcert', '')
+ sslcert = conn_params.get('sslcert', '')
+ sslkey = conn_params.get('sslkey', '')
  ...
  if passwd:
      subprocess_env['PGPASSWORD'] = str(passwd)
+ if sslmode:
+     subprocess_env['PGSSLMODE'] = str(sslmode)
+ if sslrootcert:
+     subprocess_env['PGSSLROOTCERT'] = str(sslrootcert)
+ if sslcert:
+     subprocess_env['PGSSLCERT'] = str(sslcert)
+ if sslkey:
+     subprocess_env['PGSSLKEY'] = str(sslkey)
```

| # | Solution.lean impl op (`clientEnv`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `password sslmode sslrootcert sslcert sslkey : List Char` | `conn_params.get(<key>, '')` for the five option keys | R | each option value `str` ↔ `List Char`; absent key / `''` default ↔ `[]` (mapping.md §2). G-CONF bridges via `value ↔ value.toList`. |
| A2 | `if <opt> ≠ [] then env := env ++ [(<name>, <opt>)]` | `if <opt>: subprocess_env[<ENVVAR>] = str(<opt>)` | I + R | the truthiness test `if value:` ↔ `value ≠ []` (a Python `str` is falsy iff empty — mapping.md §2): **I** on the control flow. The assigned KEY is the option's env-var name in the repo vs the option name in the model — the single key **R**-refinement (option↔env-var bijection, mapping.md §2), re-applied by G-CONF. `str(<opt>)` ↔ identity on the value (**R**, mapping.md §2). |
| A3 | the result `env` is `forwardedEnv …`: the in-order concatenation of the per-option `forwardOne` contributions (set option ⇒ one entry, unset ⇒ none) | the accumulated `PG*` entries of `subprocess_env` | I + R | the construction is modeled **deeply** (`forwardedEnv`/`forwardOne`, pure region) and the verified `do` block IS that accumulation; the per-option append ops are **I**, and the entry-key naming is the **R** bijection of A2. mapping.md §2. |
| A4 | (unmodeled) | `os.environ.copy()` base, `signal.*`, `subprocess.run(args, …)` | — | unchanged by the patch and not part of the forwarded-option behaviour the F2P test observes (it mocks `subprocess.run` and reads only the `PG*` env subset). Abstracted away; carries no refinement obligation. mapping.md §3. |

Discriminating content of the change — the four transport-security options
(`sslmode`, `sslrootcert`, `sslcert`, `sslkey`) are forwarded when configured —
lives in the four `forwardOne <name> <opt>` summands of `forwardedEnv` (model) ⇔
the four added `if <opt>: subprocess_env[<ENVVAR>] = str(<opt>)` blocks (real).
The pre-patch code forwarded ONLY `password`; `Solution_prepatch.lean` reproduces
that (it forwards just `password`, never reading the ssl options) and **fails**
`out = forwardedEnv …` on the `ensures_1` clause whenever any ssl option is set
(G-DIFF) — the exact F2P discriminator (`test_ssl_certificate`).

## B. No consumed axioms / no A-reference

The changed region calls no library function whose behaviour the proof must
assume. `dict.get` with a default, the truthiness test, and the string-keyed
assignment are all closed concrete ops (transliterated I/R). `os.environ.copy`,
`signal`, `subprocess.run` are unchanged and abstracted (A4). Hence there is no
`axiom`, no deep-model A-reference, and **no `axiom_check.py`** (G-AX = skip).
All refinement legs are R/I and are fully covered by G-CONF.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — forwarding the
four transport-security options to the client process when configured — is
modeled **deeply** (the spelled-out `forwardedEnv`/`forwardOne` and the verified
`do` block, A2–A3), not hidden behind any axiom. There are no consumed axioms.

## D. verify(Solution) ⇒ resolved

`clientEnv` verifies only if its output equals `forwardedEnv` — i.e. exactly the
set options, each forwarded once under its name, unset options dropped (A3). By R
(option `str` ↔ `List Char`; `if value:` ↔ `value ≠ []`; option↔env-var key
bijection; `str()` identity) the verified construction equals the patched
`runshell_db`'s `PG*` environment on every `conn_params`; by G-CONF the R/I
transliteration of `forwardedEnv` agrees with `patch.diff`'s behaviour on ≥10⁵
inputs (including the F2P `test_ssl_certificate` case). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point
(plan §1.1) is refinement fidelity (this doc + the key bijection, G-EQ + G-CONF);
there is no axiom-soundness trust point because there are no axioms.
