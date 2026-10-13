# refinement.md — django__django-14315

Operation-by-operation correspondence between `Solution.lean`'s impl regions (the
`effectiveProcessEnv` and `normalizedEnv` `do` blocks) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** / **A-reference** (axiomatized callee — none here), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (absent) A legs and this narrative are audited by **G-EQ**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

The patch has two hunks, each an independently-observable behavioural change with
its own F2P test(s); one `method` and one failing prepatch per change.

## A. The launch site — `BaseDatabaseClient.runshell()` (`base/client.py:22`)

Gold hunk:
```
     args, env = self.settings_to_cmd_args_env(...)
-    if env:
-        env = {**os.environ, **env}
+    env = {**os.environ, **env} if env else None
     subprocess.run(args, env=env, check=True)
```

| # | Solution.lean impl op (`effectiveProcessEnv`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `overrides : Option Overrides` | `env` (the dict / `None` from `settings_to_cmd_args_env`) | R | a dict ↔ `some kvs`, `None` ↔ `none` (mapping.md §2). |
| A2 | parameter `combined : Overrides` | `{**os.environ, **env}` | R | the merged ambient+overrides set, an UNCHANGED sub-computation folded into a free input (mapping.md §2/§3); supplied verbatim on both sides by G-CONF. |
| A3 | `if hasOverrides overrides then some combined else none` | `{**os.environ, **env} if env else None` | R + I | `bool(env)` (false for `None`/`{}`) ↔ `hasOverrides` (false for `none`/`some []`) — R; the two-arm conditional (`X if c else None`) is the identical control flow — I. **This is the discriminating step.** `Solution_prepatch_base.lean` reproduces the pre-patch `if env:` that leaves a falsy `env` unchanged (else-arm returns `overrides`), so on `overrides = some []` it yields `some []` instead of `none` → fails `out = if hasOverrides overrides then some combined else none` (G-DIFF). That is exactly `test_runshell_use_environ` (`env ∈ {None, {}}` must reach `subprocess.run` as `env=None`). |
| A4 | `return result` (`Option Overrides`) | `subprocess.run(args, env=env, …)` consumes the chosen `env` | R | the launched-process env is the carrier value; `None` ↔ inherit `os.environ`, `some combined` ↔ the explicit set (mapping.md §2). |

## B. The assembly site — `DatabaseClient.settings_to_cmd_args_env()` (`postgresql/client.py:10`)

Gold hunk:
```
         if passfile:
             env['PGPASSFILE'] = str(passfile)
-        return args, env
+        return args, (env or None)
```

| # | Solution.lean impl op (`normalizedEnv`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `assembled : Overrides` | the `env` local built by the unchanged `if passwd: … if passfile: …` chain | R | the assembled dict ↔ its `(key,value)` list (mapping.md §2); the assembly chain is UNCHANGED and abstracted to this free input (mapping.md §3). |
| B2 | `if assembled.isEmpty then none else some assembled` | `(env or None)` | R + I | `{} or None == None`, non-empty `dict or None == dict` ↔ the `isEmpty` branch (R); the `or None` idiom is the identical normalization (I). **This is the discriminating step.** `Solution_prepatch_postgresql.lean` reproduces the pre-patch `return args, env` (returns `some assembled` unconditionally), so on `assembled = []` it yields `some []` instead of `none` → fails `out = if assembled.isEmpty then none else some assembled` (G-DIFF). That is exactly `test_nopass`/`test_parameters` (an env with no PG* overrides must be reported as `None`). |
| B3 | `return result` (`Option Overrides`) | `return args, (env or None)` (the env component) | R | the reported env carrier; consumed by `runshell` (site A). |

## C. No consumed axioms / no deep-model references / no kind-3 steps

Every step is R or I. The two operations that genuinely *changed* — the
truthiness-guarded selection of `{**os.environ, **env}` vs `None` (A3) and the
`env or None` normalization of the assembled dict (B2) — are modeled **directly
and concretely** (the `hasOverrides`/`isEmpty` conditionals), not hidden behind an
axiom about the function under change.

Neither changed function consumes a callee contract:
- the merge `{**os.environ, **env}` (A2) and the `os.environ` read are UNCHANGED
  by the patch and abstracted to the free input `combined`; the spec makes no
  claim about their value, and G-CONF supplies the same concrete merged dict on
  both sides, so any mismodeling would surface as a disagreement;
- the PG* assembly chain (B1) is UNCHANGED and abstracted to the free input
  `assembled`.
These are inputs to the modeled selection, not trust points. `meta.json`
`axioms` / `deep_model_references` are empty; **G-AX is `skip`**.

## D. verify(Solution) ⇒ resolved

`effectiveProcessEnv` verifies only if it selects `some combined` exactly when
the overrides are present-and-non-empty and `none` otherwise (A3); `normalizedEnv`
verifies only if it reports `none` exactly when the assembled dict is empty (B2).
By R (`dict ↔ List (String × String)`, `bool` ↔ `hasOverrides`/`isEmpty`,
`None ↔ none`) the verified selections equal the patched `runshell` env
preparation and the patched `settings_to_cmd_args_env` return on the modeled
inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on
≥10⁵ fuzzed inputs spanning empty/non-empty/absent. The two pre-patch skeletons
each fail on exactly one of the changed clauses:
- `Solution_prepatch_base.lean`: a present-but-empty override set passes through
  unchanged (`some []`) instead of normalizing to `none` — exactly the
  `test_runshell_use_environ` assertion (`env ∈ {None, {}}` → `subprocess.run(...,
  env=None)`);
- `Solution_prepatch_postgresql.lean`: an empty assembled dict is reported as
  `some []` instead of `none` — exactly the `test_nopass`/`test_parameters`
  assertion change (`{}` → `None`).

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axiom trust points (G-AX skip); the only trust point is refinement fidelity
(this doc, G-EQ + G-CONF).
