# mapping.md — django__django-15851

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b4817d20b9e55df30be0b1b2ca8c8bb6d61aab07`, states the type
abstraction, and records the (absence of) axiom provenance.

Repo file under change: `django/db/backends/postgresql/client.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_argv(prefix, parameters, has_dbname, dbname)` | `DatabaseClient.settings_to_cmd_args_env(cls, settings_dict, parameters)` — `django/db/backends/postgresql/client.py:10` (changed hunk: lines 35-37) | the modeled changed function: assembles the ordered argument vector |
| `prefix` (param) | the `args` list as built by lines 11, 30-34: `[cls.executable_name]` plus the optional `["-U", user]`, `["-h", host]`, `["-p", str(port)]` segments | the leading flag segment, assembled before the hunk; unchanged by the patch |
| `parameters` (param) | the `parameters` argument of `settings_to_cmd_args_env` | the caller-supplied extra arguments |
| `has_dbname` / `dbname` (params) | the `if dbname:` guard (line 35) and the `dbname` token (`settings_dict.get("NAME")` at line 16, defaulted to `"postgres"` at line 28 when no name and no service) | whether a database-name token is in effect, and its identity |
| `build_argv`'s return | the `args` list returned in `return args, (env or None)` (line 54) | the assembled argument vector |

The pre-patch ordering the change fixes (for the refinement audit, not
referenced from the consumer spec view): line 37 `args.extend(parameters)` sat
**after** the `if dbname: args += [dbname]` block (lines 35-36), so the extra
arguments followed the database-name token.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a command-line argument token (`str`: `"psql"`, `"-U"`, a username, `dbname`, an element of `parameters`) | one `int` (an opaque token identity) | tokens compared only by equality and position; the F2P/P2P tests assert list equality (order + per-token identity), both preserved by any injective `str → int` assignment. `str` indexing is banned in Nagini, and no per-character behaviour is under change, so a whole token is one opaque `int`. |
| `args` / `parameters` (`list[str]`) | `List[int]` | element-wise token bijection; `list +=` / `list.extend` ↔ list `append` loop; specification carried by `PSeq[int]` via `ToSeq`. |
| `dbname` (`str` or falsey / absent) | `(has_dbname: bool, dbname: int)` | the `if dbname:` truth value ↔ `has_dbname`; the token ↔ `dbname`. At most one trailing token, matching `args += [dbname]`. |
| the `env` dict and the `(args, env)` tuple wrapper (lines 39-54) | omitted | the patch does not touch `env` or the tuple shape; `env` is built identically pre- and post-patch from the `if passwd/service/ssl…/passfile` blocks below the hunk. It is observationally identical across the change and not part of the behaviour under specification, so it is dropped (analogous to omitting an unchanged wrapper). The model specifies only the `args` ordering the patch changes and the F2P test observes. |

## 3. Callee provenance (kind-A)

**None.** The changed operation is pure in-process list construction
(`list.extend` and `list +=` reordered). No library or repository callee
participates in the change, so the bundle contains **no `@ContractOnly`
axiom**, no A-consumed and no A-reference, and therefore no `axiom_check.py`
(G-AX is vacuous for this instance). The ordering is modelled deeply and
directly with `list.append` in the impl and `PSeq` concatenation in the
postcondition.
