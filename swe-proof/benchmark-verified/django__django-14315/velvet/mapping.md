# mapping.md — django__django-14315

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 187118203197801c6cb72dc8b06b714b23b6dd3d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled construct.

Repo files under change:
- `django/db/backends/base/client.py`
- `django/db/backends/postgresql/client.py`

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `effectiveProcessEnv (overrides : Option Overrides) (combined : Overrides)` | `BaseDatabaseClient.runshell` — `django/db/backends/base/client.py:22` (the env-preparation block, lines 23–25 pre-patch / 23–24 post-patch, feeding `subprocess.run(args, env=env, …)` at :26) | the modeled changed function: which variable set is passed to the launched process |
| `normalizedEnv (assembled : Overrides)` | `DatabaseClient.settings_to_cmd_args_env` — `django/db/backends/postgresql/client.py:10` (the `return args, env` site at line 54 pre-patch / `return args, (env or None)` post-patch) | the modeled changed function: what env value the assembler reports after building it up |
| `Overrides` (`List (String × String)`) | a `dict[str, str]` of environment-variable overrides (`env`) | ordered name/value pairs; only key/value content and emptiness are observable |
| `overrides : Option Overrides` | `env`, the second element of `settings_to_cmd_args_env(...)`'s return (a `dict`, possibly empty, or — post the companion fix — `None`) | the override set handed to `runshell`, possibly absent |
| `combined : Overrides` | `{**os.environ, **env}` — the ambient environment with the overrides applied on top | the merged set used when there is something to apply (UNCHANGED sub-computation, free input — §3) |
| `assembled : Overrides` | the `env` local built up in `settings_to_cmd_args_env` by the `if passwd: env['PGPASSWORD']=…` … chain (lines 39–53) | the assembled override dict, possibly empty |

The pre-patch behaviour the change corrects (refinement audit only, not in the
consumer spec view):
- `runshell` only rewrote `env` when `env` was truthy (`if env:`), leaving a
  falsy `env` (an empty `{}`) unchanged, so `subprocess.run` received `env={}`
  — an explicit EMPTY environment — rather than `None`, which is the signal to
  inherit `os.environ`. Fixed to `env = {**os.environ, **env} if env else None`.
- `settings_to_cmd_args_env` returned its assembled `env` dict directly, so an
  empty dict (no PG* overrides) was returned as `{}` instead of `None`. Fixed to
  `return args, (env or None)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an environment-override `dict[str, str]` | `Overrides = List (String × String)` | a dict ↔ its ordered list of `(key, value)` pairs; `len(d) == 0` ↔ `kvs.isEmpty`. Only emptiness and content are observed (the F2P tests compare the returned value to `{...}`/`None`, and `runshell` only branches on truthiness). |
| `env` value that may be a dict or `None` | `Option Overrides` | a dict ↔ `some kvs`; `None` ↔ `none`. |
| Python truthiness of a dict `env` (`if env:` / `env or None`) | `hasOverrides overrides` | `bool(env)` is `False` for both `None` and `{}`, `True` otherwise ↔ `hasOverrides` is `false` for `none` and `some []`, `true` for a non-empty `some`. This is the exact guard the base fix uses. |
| `{**os.environ, **env}` (ambient merged with overrides) | `combined : Overrides` (free input) | the merged set the patch passes when `env` is truthy ↔ `some combined`. The merge itself is UNCHANGED by the patch (it already existed inside the `if env:` arm); it is abstracted to a single free input (the django__django-12713 precedent: unchanged sub-computation folded into a free value), not modeled or axiomatized. |
| `env or None` on the assembled dict | `if assembled.isEmpty then none else some assembled` | `{} or None == None`, a non-empty dict `or None == ` the dict ↔ the `isEmpty` branch. |

`os.environ` itself, the dict-merge semantics, and `subprocess.run`'s handling of
`env=None` vs `env={}` are platform/library behaviour the patch does not change
and the spec does not model: the spec models only *which carrier* (`some combined`
vs `none`) is selected. That selection is the whole behavioural content of the
fix.

## 3. Callee provenance (kind-A)

**None.** There are no axiomatized callees and no deep-model references in this
bundle (`meta.json axioms = []`, `deep_model_references = []`; G-AX skipped). Both
modeled behaviours are closed `Option`/emptiness decisions over free inputs:

- `runshell`'s change is *whether* to pass the combined set or `None`; the
  combined set `{**os.environ, **env}` is an UNCHANGED sub-computation (it was
  already computed inside the pre-patch `if env:` arm), abstracted to the free
  input `combined` (§2). The patch adds no new callee.
- `settings_to_cmd_args_env`'s change is *whether* to report the assembled dict
  or `None`; the assembly chain (lines 39–53) is UNCHANGED and only determines
  the dict's content/emptiness, abstracted to the free input `assembled`.

No callee is over-approximated, so no `axiom` is owed (directive 7); `axiom_check.py`
is a stub that exits `skip`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14315`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates both
`effectiveProcessEnv` and `normalizedEnv` to Python; the ORACLE transliterates the
two patched hunks VERBATIM (`env = {**os.environ, **env} if env else None` and
`return args, (env or None)`), with `{**os.environ, **env}` supplied as the same
concrete merged dict on both sides (it is unchanged by the patch). Boundary cases
cover the F2P scenarios: an empty assembled dict (`test_nopass`, `test_parameters`
→ `None`), a non-empty assembled dict (`test_basic`, `test_ssl_certificate`, … →
the dict), and `runshell` with `env ∈ {None, {}}` (`test_runshell_use_environ` →
`subprocess.run(..., env=None)`).
