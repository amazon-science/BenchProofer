# mapping.md — symbol binding & type bijection (django__django-14315)

## Modeled functions

### 1. `runshell` environment computation (base database client)
- **Lean** `implementation_runshell_env :
  List (String × String) → Option (List (String × String)) → Option (List (String × String))`
- **Python** `BaseDatabaseClient.runshell(self, parameters)` —
  `django/db/backends/base/client.py:22-26 @ base_commit`. The changed
  statement is the env computation feeding `subprocess.run(args, env=env, …)`:

  ```python
  # base_commit (buggy):
  if env:
      env = {**os.environ, **env}
  # patched:
  env = {**os.environ, **env} if env else None
  ```

  `env` here is the second element returned by `settings_to_cmd_args_env`; it is
  either `None` or a `dict` (possibly empty). Python truthiness: `if env:` is
  **false** for both `None` and `{}`. The observable modeled is the value passed
  as `env=` to `subprocess.run`:
  - env falsy (`None` **or** empty dict) → `None` (so the child inherits
    `os.environ`); **this `None` for the empty-dict case is the fix.**
  - env truthy (non-empty dict) → `{**os.environ, **env}` (ambient environment
    overlaid with the per-command overrides; overrides win on key collision —
    unchanged behaviour).

### 2. command-environment normalization (postgresql database client)
- **Lean** `implementation_client_env :
  List (String × String) → Option (List (String × String))`
- **Python** `DatabaseClient.settings_to_cmd_args_env(cls, settings_dict, parameters)`
  return statement — `django/db/backends/postgresql/client.py:54 @ base_commit`:

  ```python
  # base_commit (buggy):
  return args, env
  # patched:
  return args, (env or None)
  ```

  `env` is a `dict` assembled earlier in the method (`env = {}` then conditional
  inserts for `PGPASSWORD`, `PGSERVICE`, `PGSSLMODE`, …). It is **never `None`** —
  always a dict, possibly empty. The changed op is the normalization of the
  returned env: empty dict → `None`, else the dict unchanged. The `args` element
  and the assembly of `env` are pre-existing, unchanged behaviour and are outside
  the modeled slice (they are identical pre/post — `I`, not modeled).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| an env `dict[str,str]` | `List (String × String)` | key→value pairs; empty dict ↔ `[]`. Order/dedup irrelevant to the modeled observable (absence vs presence). |
| the `env` slot that may be `None` or a dict (runshell input) | `Option (List (String × String))` | `none` ↔ `None`; `some []` ↔ `{}`; `some kvs` ↔ non-empty dict |
| the value passed as `subprocess.run(env=…)` / the returned env component | `Option (List (String × String))` | `none` ↔ `None`; `some kvs` ↔ dict |
| `os.environ` | `List (String × String)` (`osEnviron`) | the ambient process environment |
| Python truthiness `bool(env)` | `envIsSet env` (`pure` region) | `none`/`some []` → `false`; `some (_::_)` → `true` |
| `{**os.environ, **env}` | `combineEnv osEnviron kvs` (opaque) | the unchanged dict-spread merge; overrides take precedence. See *Callee provenance*. |

## Callee provenance
- **`combineEnv` ⇄ `{**os.environ, **env}`** — an UNCHANGED operation present in
  both pre- and post-patch code (the truthy branch). It is the Python dict-spread
  merge of the ambient environment with the per-command overrides (later keys
  win). Declared `opaque combineEnv : List (String × String) → List (String ×
  String) → List (String × String)` so it can appear in the executable impl and
  in the frame clause of `problem_spec_runshell_env`. **The proof consumes NO
  property of it** (the fix's discriminator is the empty→absent normalization,
  which is independent of the merge contents), so there is NO `combineEnv_prop`
  axiom (no dead axiom). Its behavioural equivalence to `{**os.environ, **env}`
  is exercised by **G-CONF** (the shadow uses the real dict merge), not G-AX.
  Tagged **A-reference** in refinement.md.
- No other callee. `settings_to_cmd_args_env` (the env assembly) is the
  unchanged context of modeled function 2 and is not itself called by the model.

## Flag dependency
None. Neither normalization is behind a configuration flag; both are
unconditional on the truthiness of `env`.

## Scope note
The full `subprocess.run(args, env=…, check=True)` call and the postgresql
`settings_to_cmd_args_env` argument assembly are unchanged; only the env value's
empty→`None` normalization (and, in runshell, the pre-existing merge in the
truthy branch) is observable for the fix. The two sites are **independently
tested** (base: `test_runshell_use_environ`; postgresql: `test_nopass`,
`test_parameters`), hence two prepatch variants.

## G-CONF fuzz seed
Pinned seed: **14315**. ≥10^5 fuzzed inputs per modeled function over random env
dicts (including `None`, empty, and non-empty) and random ambient environments,
plus the exact F2P boundary shapes (`None`, `{}`, non-empty).
