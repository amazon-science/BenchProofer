# refinement.md — django__django-15851

Maps every operation in `implementation_shellArgs` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `shellArgs` (`DatabaseClient.settings_to_cmd_args_env`)

Post-patch repo code (`patch.diff`), `args` assembly only:
```python
args = [cls.executable_name]
...
if user:  args += ["-U", user]
if host:  args += ["-h", host]
if port:  args += ["-p", str(port)]
args.extend(parameters)          # <-- moved AHEAD of the dbname append
if dbname:  args += [dbname]
```

Lean impl (`implementation_shellArgs`):
```lean
def implementation_shellArgs
    (executable : String) (user host port dbname : Option String)
    (parameters : List String) : List String := Id.run do
  let mut args := [executable]
  if let some u := user then args := args ++ ["-U", u]
  if let some h := host then args := args ++ ["-h", h]
  if let some p := port then args := args ++ ["-p", p]
  args := args ++ parameters
  if let some d := dbname then args := args ++ [d]
  return args
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut args := [executable]` | `args = [cls.executable_name]` | **I** | initialize the vector with the program name. |
| 2 | `if let some u := user then args := args ++ ["-U", u]` | `if user: args += ["-U", user]` | **R** | truthiness `if user` ⟺ `user : Option String` is `some`; `args += ["-U", user]` ⟺ `args ++ ["-U", u]`. Same shape for host/port (rows 3–4). |
| 3 | `if let some h := host then args := args ++ ["-h", h]` | `if host: args += ["-h", host]` | **R** | as row 2. |
| 4 | `if let some p := port then args := args ++ ["-p", p]` | `if port: args += ["-p", str(port)]` | **R** | as row 2; the port value enters pre-stringified (`str(port)` → `p : String`). |
| 5 | `args := args ++ parameters` | `args.extend(parameters)` | **I** (the moved op) | **the fix.** The post-patch code performs the `parameters` splice HERE — before the dbname append. `args ++ parameters` reproduces it at this position. |
| 6 | `if let some d := dbname then args := args ++ [d]` | `if dbname: args += [dbname]` | **R** | truthiness `if dbname` ⟺ `dbname : Option String` is `some`; `args += [dbname]` ⟺ `args ++ [d]`. The effective-dbname defaulting (`if not dbname and not service: dbname = "postgres"`) is UNCHANGED by the patch and pre-computed into `dbname` (mapping.md). |
| 7 | `return args` | `return args, (env or None)` | **I** | the function returns the assembled vector (the `env` dict is unchanged by the patch and out of scope — mapping.md). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `args` assembly.

Refinement equivalence (R/I): the post-patch sequence of `args += [...]` /
`args.extend(parameters)` operations on a Python list is, at the element level,
exactly the left-to-right `List.append` chain the Lean impl builds. Modeling each
truthy-guarded `args += [...]` as `optFlag`/`dbname.toList` and the unconditional
`args.extend(parameters)` as `++ parameters` preserves both the elements and their
order, which is the observable behavior the F2P test checks.

## Soundness check (verify ⟹ correct)

- `problem_spec_shellArgs ... result := result = [executable] ++ optFlag "-U" user
  ++ optFlag "-h" host ++ optFlag "-p" port ++ parameters ++ dbname.toList` pins
  the result EXACTLY (full list equality to an input-grounded concatenation) —
  directive 5 (frame): every component, AND the relative order of `parameters`
  and `dbname`, is pinned to its input. The crucial order — `parameters` BEFORE
  `dbname.toList` — is fixed by the spec; no component is left unconstrained, and
  there is no ungrounded oracle (directive 8): the postcondition is dischargeable
  only by actually concatenating the components in the specified order.
- The prepatch impl performs the dbname append BEFORE `args ++ parameters`,
  yielding `... ++ dbname.toList ++ parameters`. It violates the spec on the
  discriminating clause `dbname = some _ ∧ parameters ≠ []` (a database name is
  present and at least one extra parameter was supplied), where it produces
  `[..., dbname, p₁, …]` but the spec requires `[..., p₁, …, dbname]`. Its carried
  gold proof cannot close (G-DIFF/G-PANEL): the two orderings differ.
- This discriminating case is exactly what the FAIL_TO_PASS test `test_parameters`
  exercises: `settings_to_cmd_args_env({"NAME": "dbname"}, ["--help"])` must equal
  `(["psql", "--help", "dbname"], None)` — parameters before the database name.
  With the prepatch ordering the result is `["psql", "dbname", "--help"]` (the bug:
  psql ignores `--help` after `dbname`). With the fixed ordering it is
  `["psql", "--help", "dbname"]`.
- G-CONF confirms the R/I shadow == an in-process replica of the patched `args`
  assembly over hand-picked edge cases (empty/non-empty parameters; present/absent
  dbname; absent connection options) plus ≥1e5 fuzzed inputs.
