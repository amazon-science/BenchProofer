# refinement.md — django__django-14315

The operation-by-operation correspondence between `model.py`'s implementation
(the `normalized_environment` and `effective_environment` impl regions, plus the
`env_merge` axiom) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed**, the proof uses
the axiom's `Ensures`; **A-reference**, a deep model validated == the real
operation by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). The change is two hunks, each an
independently-observable fixed behaviour, modeled as its own function.

## A. Site 2 — the backend-reported environment (`postgresql/client.py:54`)

Gold hunk (`DatabaseClient.settings_to_cmd_args_env`):
```
-        return args, env
+        return args, (env or None)
```
`env` is the `dict` built earlier in the method (`env = {}` then conditionally
populated); it is `{}` exactly when no PG* variable is required.

Model function: `normalized_environment(env)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `env: Dict[int, int]` | the local `env` `dict` (str→str) | R | environment `dict` ↔ `Dict[int,int]` of name/value tokens (mapping.md §2); only membership/value/emptiness are observed. |
| A2 | `if len(env) == 0: return None` | the `env or None` selecting `None` when `env` is empty | R + I | a `dict` is falsy iff empty; `len(env) == 0` is that test spelled out. Returning `None` is identical. |
| A3 | `return env` (the same object, `Result() is env`) | `env or None` selecting `env` when truthy (non-empty) | R + I | a non-empty `dict` is truthy and `env or None` evaluates to `env` itself; the model returns the same object (`Result() is env`). |

The discriminating content: an empty mapping → `None` (not `{}`).
`model_prepatch_2.py` reverts A2/A3 to `return env` and **fails** the
postcondition `Implies(len(env) == 0, Result() is None)` — the spec sensing the
change (G-DIFF).

## B. Site 1 — the environment handed to the subprocess (`base/client.py:25`)

Gold hunk (`BaseDatabaseClient.runshell`):
```
-        if env:
-            env = {**os.environ, **env}
+        env = {**os.environ, **env} if env else None
         subprocess.run(args, env=env, check=True)
```

Model function: `effective_environment(env, base)`, with `base ↔ os.environ`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `env: Optional[Dict[int,int]]`, `base: Dict[int,int]` | the `env` returned by `settings_to_cmd_args_env` (a `dict`, possibly empty, or `None` after the post-patch site 2) and `os.environ` | R | `dict`/`None` ↔ `Optional[Dict[int,int]]`; `os.environ` ↔ `base` (mapping.md §2). |
| B2 | `if env is None: return None` | the ternary's `else None` taken for a `None` command mapping | R + I | `env is None` selects `None`; identical. (The base-class `settings_to_cmd_args_env` raises, so its `runshell` is exercised only by subclasses; the F2P `test_runshell_use_environ` passes `env ∈ {None, {}}`.) |
| B3 | `if len(env) == 0: return None` | the ternary's `else None` taken for an empty (falsy) `dict` | R + I | a non-`None` `dict` is falsy iff empty; `len(env) == 0` is that test. Returning `None` is identical. |
| B4 | `merged = env_merge(base, env); return merged` | `{**os.environ, **env}` (the truthy branch) | A-consumed | the merge is an **unchanged** standard mapping-unpacking the code invokes; modeled by the `env_merge` axiom (weakest sufficient contract: overlay wins, base carried, no spurious keys, fresh non-empty, inputs unmutated — mapping.md §3.1). The proof consumes its `Ensures` (the merge postconditions B5 + the non-`None`-ness). G-AX checks it against the real `{**base, **overlay}`. |
| B5 | postconditions: `k in env ⟹ Result()[k] == env[k]`; `k in base and k ∉ env ⟹ Result()[k] == base[k]`; `k in Result() ⟹ k ∈ env ∪ base` (no spurious keys) | the merge semantics of `{**os.environ, **env}` (`env` wins, and the merge holds only keys of its inputs) | A-consumed + I | restate `env_merge`'s Ensures on `Result()`; follow directly from B4's axiom (including its no-spurious-keys clause). |
| B6 | `Requires(MustTerminate(2))` on both modeled functions; `Requires(MustTerminate(1))` on the `env_merge` callee | both real sites are bounded straight-line code (a truthiness decision plus at most one bounded mapping-unpacking merge) that always delivers its value | R | total-correctness obligation: the real code always ANSWERS. Nagini verifies partial correctness by default, so without the obligation a diverging impl would satisfy every value `Ensures` vacuously (a G-PANEL-1 counterexample: `while True: pass` verified pre-repair). The callee's strictly smaller measure (1 < 2) admits the single bounded merge step while forbidding a self-call of the contracted routine. |

The discriminating content: an empty command mapping → `None` (so the
subprocess inherits `os.environ`), not `{}`. `model_prepatch.py` reverts B3 to
return a non-`None` empty mapping and **fails** the postcondition
`Implies(env is not None and len(env) == 0, Result() is None)` — the spec
sensing the change (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R, A, or I. The two operations that genuinely **change** — the
empty→`None` normalisation at each site — are modeled **deeply** (the spelled-
out `len(env) == 0 → None` selections in the two impl regions; **A-reference**,
validated == the real `env or None` / `{**os.environ, **env} if env else None`
by G-AX). The single **consumed** axiom, `env_merge` (**A-consumed**, step B4),
covers the **unchanged** mapping-merge the new code invokes — never the operation
under change. No dead axioms: `env_merge`'s `Ensures` is consumed by B4/B5.

## D. verify(model) ⇒ resolved

`normalized_environment` verifies only if an empty mapping yields `None`
(A2/A3); `effective_environment` verifies only if a `None`/empty command mapping
yields `None` (B2/B3) and a non-empty one yields exactly the merge (B4/B5). By R
(`dict`/`None` ↔ `Optional[Dict[int,int]]`, `dict` truthiness ↔
`len/is None`) the verified selections equal `env or None` and
`{**os.environ, **env} if env else None`; by G-AX the deep models equal those
real Python expressions (A-reference) and the real `{**base, **overlay}` meets
the `env_merge` axiom (A-consumed). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and an
audited unchanged callee — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ).
