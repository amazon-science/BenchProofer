# refinement.md — django__django-14376

Maps every operation in `implementation_dbArg` / `implementation_connParams` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by G-AX),
**I** (identical concrete op). Every step is R, A, or I.

## Triple 1: `dbArg` (`DatabaseClient.settings_to_cmd_args_env`, database-name choice)

Post-patch repo code (`patch.diff`):
```python
database = settings_dict['OPTIONS'].get(
    'database',
    settings_dict['OPTIONS'].get('db', settings_dict['NAME']),
)
...
if database:
    args += [database]
```

Lean impl (`implementation_dbArg`):
```lean
let database := optDatabase.getD (optDb.getD name)
if database ≠ "" then return some database
return none
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `optDb.getD name` | `OPTIONS.get('db', settings_dict['NAME'])` | **R** | `dict.get(k, default)` ⟺ `Option.getD`: present `'db'` key ↦ its value (`optDb = some _`), absent ↦ `name`. |
| 2 | `optDatabase.getD (…)` | `OPTIONS.get('database', <inner>)` | **R** (the fix) | **the fix.** The post-patch code adds the higher-precedence `'database'` lookup over the (formerly sole) `'db'`/NAME chain. `Option.getD` reproduces the precedence: present `'database'` ↦ its value, absent ↦ the inner choice. |
| 3 | `if database ≠ "" then return some database` | `if database: args += [database]` | **R** | truthiness `if database` ⟺ `database ≠ ""`; appending the single token ⟺ `some database`. The empty-but-present case (`some ""`) is selected at step 2 and then dropped here — matching `get('database','')` short-circuiting then `if database:` being false. |
| 4 | `return none` | (no token appended) | **R** | a falsy/empty chosen value contributes no trailing database token. |

All `dbArg` ops are **R** — NO A-tagged content; the changed op (precedence among
option sources) is modeled deeply via `Option.getD`, not axiomatized.

## Triple 2: `connParams` (`DatabaseWrapper.get_connection_params`, name/password keys)

Post-patch repo code (`patch.diff`):
```python
if settings_dict['NAME']:
    kwargs['database'] = settings_dict['NAME']
if settings_dict['PASSWORD']:
    kwargs['password'] = settings_dict['PASSWORD']
```

Lean impl (`implementation_connParams`):
```lean
let mut kwargs := []
if let some n := name then if n ≠ "" then kwargs := kwargs ++ [("database", n)]
if let some p := password then if p ≠ "" then kwargs := kwargs ++ [("password", p)]
return kwargs
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut kwargs := []` | the (modeled subset of the) `kwargs` dict | **I** | initialize the entries this patch is responsible for. |
| 2 | `if let some n := name then if n ≠ "" then kwargs := kwargs ++ [("database", n)]` | `if settings_dict['NAME']: kwargs['database'] = settings_dict['NAME']` | **R** (the fix) | **the fix.** Python truthiness `if NAME` treats both `None` and `""` as falsy; modeled as `name = some _ ∧ value ≠ ""` (`some ""` contributes nothing). Key changed from deprecated `'db'` to `"database"`. Writing the entry ⟺ appending `("database", n)`. |
| 3 | `if let some p := password then if p ≠ "" then kwargs := kwargs ++ [("password", p)]` | `if settings_dict['PASSWORD']: kwargs['password'] = settings_dict['PASSWORD']` | **R** (the fix) | **the fix.** key changed from deprecated `'passwd'` to `"password"`; same shape as row 2, including the empty-string truthiness guard. |
| 4 | `return kwargs` | — | **I** | the entries this patch writes, in source order. |

All `connParams` ops are **R/I** — NO A-tagged content; the changed op (the entry
keys) is modeled deeply, not axiomatized.

Both impl regions are R/I (no A-tagged content): `conf_skip = false`, and
`conformance_check.py` mechanically differential-tests both R/I shadows against
in-process replicas of the post-patch behavior.

## Soundness check (verify ⟹ correct)

### dbArg
- `problem_spec_dbArg ... result := result = (let chosen := optDatabase.getD
  (optDb.getD name); if chosen = "" then none else some chosen)` pins the result
  EXACTLY (full `Option String` equality to an input-grounded precedence
  selection) — directive 5: every component is pinned to its input; directive 8:
  the postcondition is dischargeable only by performing the actual precedence
  selection (no ungrounded oracle).
- The **prepatch_1** impl drops the `'database'` lookup (`chosen = optDb.getD
  name`). It violates the spec on the discriminating clause `optDatabase = some a
  ∧ optDb.getD name ≠ a` (the primary option is present and differs from the
  lower-precedence choice), where it yields the lower-precedence value but the
  spec requires `a`. Its carried gold proof cannot close (G-DIFF).
- This is exactly what the FAIL_TO_PASS tests exercise:
  `test_options_non_deprecated_keys_preferred` supplies
  `OPTIONS = {'database': 'optiondbname', 'db': 'deprecatedoptiondbname', …}` and
  asserts the trailing arg is `optiondbname` (the non-deprecated key wins);
  `test_options_override_settings_proper_values` runs both key spellings and
  asserts `optiondbname` each time.

### connParams
- `problem_spec_connParams ... result := result = (NAME-entry) ++ (PASSWORD-entry)`
  pins the result EXACTLY (full association-list equality), with the keys fixed to
  `"database"`/`"password"` and each entry present iff its setting is non-empty —
  directive 5/8 satisfied.
- The **prepatch_2** impl emits the deprecated keys `"db"`/`"passwd"`. It violates
  the spec whenever `name = some _` (entry `("db", n) ≠ ("database", n)`) or
  `password = some _`. Its carried gold proof cannot close (G-DIFF).
- No dedicated F2P test targets `get_connection_params` directly (it needs a live
  mysqlclient connection), but the key rename is the explicit subject of the issue
  and the matching half of the gold patch; it is an independently-observable fixed
  behavior, hence its own prepatch (SPEC_GUIDE §3).

## G-CONF
Confirms both R/I shadows == in-process replicas of the post-patch behavior over
hand-picked edge cases (present-but-empty `'database'` option short-circuit;
absent options falling through to `'db'`/NAME; empty/non-empty NAME/PASSWORD) plus
≥1e5 fuzzed inputs.
