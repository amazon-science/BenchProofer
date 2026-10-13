# mapping.md — django__django-15851

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b4817d20b9e55df30be0b1b2ca8c8bb6d61aab07`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. `spec_provenance: cold` — derived solely from the
problem_statement, the gold patch, and the repo source.

Repo file under change: `django/db/backends/postgresql/client.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildShellArgs (leading dbname parameters)` | `DatabaseClient.settings_to_cmd_args_env(cls, settings_dict, parameters)` — `django/db/backends/postgresql/client.py:10` (the positional-argument assembly, body lines 11–37) | the modeled changed function: assembling the command-line argument vector |
| `builtArgs (leading dbname parameters)` | the assembled `args` list at line 37 (post-patch) | pure spec: the full argument vector |
| `dbnameToken (dbname)` | the optional `if dbname: args += [dbname]` token (`client.py:35–36`) | pure spec: the optional trailing database-name element |
| `leading` (parameter) | the `args` list built up through the connection-option flags — `args = [cls.executable_name]` plus the `-U/-h/-p` blocks (`client.py:11`, `29–34`) | the read-only leading segment this step builds upon (unchanged code) |
| `parameters` (parameter) | the `parameters` argument of `settings_to_cmd_args_env` | the caller-supplied extra arguments |

The change moves `args.extend(parameters)` so it runs **before** the
`if dbname: args += [dbname]` block (gold: line 35 `args.extend(parameters)`
precedes line 36–37 `if dbname: args += [dbname]`). The `env` assembly
(`client.py:39–55`) and the `runshell` method are unchanged and unobserved by
the F2P test; they are not modeled.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `args` — a Python `list[str]` (the argument vector) | `List String` | `xs` (Python list) ↔ `xs`-shaped `List String`; `args += ys` / `args.extend(ys)` ↔ `++`; `[]` ↔ `[]`. Element order is observable (F2P compares the list exactly). |
| `parameters` — a Python `list[str]` | `List String` | same list bijection |
| the leading segment `args` already built through the option flags | `leading : List String` | the `List String` equal to the args list at the point just before the database-name block; built by unchanged code, read-only here |
| `dbname` — a Python `str` that may be empty/`None`, gated by `if dbname:` | `Option String` | a **truthy** `dbname` (non-empty `str`, possibly the `"postgres"` default) ↔ `some s`; a **falsy** `dbname` (`None` or `""`) ↔ `none`. `if dbname: args += [dbname]` ↔ `dbnameToken dbname = dbname.toList` (`some s ↦ [s]`, `none ↦ []`). |

`List String` indexing/concatenation is total and sound; the carrier is
`List String` because the operation observes only argument identity and order.

## 3. Callee provenance

**None.** `buildShellArgs` consumes no unchanged callee's contract and
deep-models nothing foreign: the assembled vector is `leading ++ parameters ++
dbnameToken dbname`, built from list concatenation (`++`) and the optional token
(`Option.toList`), both modeled directly. The leading segment is supplied as an
input (`leading`), produced by unchanged repo code (the executable name and the
`-U/-h/-p` option flags). Hence there are **no axioms** (`axioms` region empty)
and **no deep-model references**, so **G-AX is skipped** (`meta.json
gates.G-AX.status = "skip"`, no `axiom_check.py`). See refinement.md §C.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1)

`conformance_check.py` seeds its `random.Random` with **`15851`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the full
argument-vector construction (the unchanged leading segment plus the modeled
reordered tail) to Python and diffs the resulting `args` list against the real
**patched** `DatabaseClient.settings_to_cmd_args_env(...)[0]` over fuzzed
`settings_dict`/`parameters` inputs. There are no A-tagged callees, so the
shadow is pure R/I.
