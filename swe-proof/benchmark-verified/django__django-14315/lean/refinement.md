# refinement.md — operation correspondence (django__django-14315)

Maps every op in the two modeled functions to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX/G-CONF) · **I**
identical op.

The fix normalizes a "no overrides" environment to *absent* so a spawned child
inherits the ambient environment, at two independent sites.

## Function 1 — `implementation_runshell_env` ⇄ `BaseDatabaseClient.runshell` env computation
`django/db/backends/base/client.py:22-26`

```python
# base_commit (buggy):              # patched:
if env:                             env = {**os.environ, **env} if env else None
    env = {**os.environ, **env}
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `osEnviron : List (String × String)` | `os.environ` | R | ambient env dict ↔ list of key/value pairs (mapping.md) |
| 2 | `env : Option (List (String × String))` input | the `env` from `settings_to_cmd_args_env` (`None` or a dict) | R | `none`↔`None`, `some []`↔`{}`, `some kvs`↔dict |
| 3 | `if envIsSet env then …` | the truthiness test `if env … else` | R | Python `bool(env)`: false for both `None` and `{}`; `envIsSet` (pure) matches exactly |
| 4 | `env := some (combineEnv osEnviron (env.getD []))` (truthy branch) | `{**os.environ, **env}` | A-reference | the **unchanged** ambient-overlay; modeled via `opaque combineEnv`, its agreement with the real dict spread checked by G-CONF (shadow uses the real merge). NO `_prop` axiom consumed. |
| 5 | `else env := none` ; `return env` | `… if env else None` | R/I | the **changed op**: the not-present case (covers the empty-dict case — the bug) resolves to absent (`none`↔`None`). This is the fix's discriminator. |

## Function 2 — `implementation_client_env` ⇄ `DatabaseClient.settings_to_cmd_args_env` return
`django/db/backends/postgresql/client.py:54`

```python
# base_commit:  return args, env          # patched:  return args, (env or None)
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `env : List (String × String)` input | the assembled `env` dict (always a dict, possibly empty) | R | dict ↔ list of key/value pairs; the assembly itself is unchanged context (I, outside the slice) |
| 2 | `if env.isEmpty then return none` | `env or None` when `env` is empty (`{}` is falsy → `None`) | R/I | the **changed op**: empty overrides → absent (the bug being fixed) |
| 3 | `return some env` | `env or None` when `env` non-empty (returns `env`) | R/I | non-empty overrides reported unchanged |

## Tag summary
- **A-reference (1 row):** function 1 row 4 (`combineEnv` ⇄ `{**os.environ,
  **env}`) — the unchanged overlay, reproduced in the G-CONF shadow with the real
  dict merge; not abstracted behind a consumed property.
- **A-consumed (0 rows):** no callee property is consumed by either proof — the
  discriminator (empty/absent → absent) is independent of the overlay's contents.
  Hence NO `_prop` axiom (no dead axiom). The proof agent may add one only if
  genuinely stuck.
- **No changed-inexpressible op:** both changed ops (empty→absent normalization)
  are modeled exactly with `Option`.

## G-DIFF discriminators (one prepatch per independently-fixed behavior)
- **`Solution_prepatch_1.lean`** — the function-1 bug: the not-present branch is
  omitted (`if envIsSet env then … (no else)`), so a supplied-but-empty override
  (`some []`) is returned unchanged instead of becoming `none`. Violates the
  spec's `envIsSet env = false → result = none` clause on input `env = some []`
  (`result = some []` ≠ `none`). Mirrors the base-client F2P test
  `test_runshell_use_environ` (env ∈ {None, {}} ⟹ `subprocess.run(env=None)`).
- **`Solution_prepatch_2.lean`** — the function-2 bug: the return is
  `some env` with no empty→absent normalization, so `env = []` gives `some []`
  instead of `none`. Violates `env = [] → result = none`. Mirrors the postgresql
  F2P tests `test_nopass` / `test_parameters` (empty env dict ⟹ `None`).

Both prepatch impls are the real pre-patch bugs; against the frozen specs their
`correct_*` cannot close (carried gold proof body fails to typecheck) — the
G-DIFF signal. `patch.diff` == gold verbatim.
