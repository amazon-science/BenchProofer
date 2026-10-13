# mapping.md — django__django-15851

## Symbol binding (file:line @ base_commit b4817d20b9e55df30be0b1b2ca8c8bb6d61aab07)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_shellArgs` / `problem_spec_shellArgs` | `DatabaseClient.settings_to_cmd_args_env` (its `args` list assembly) | `django/db/backends/postgresql/client.py:9-37` |
| `optFlag` (pure helper) | the `args += [flag, value]` blocks (`-U`/`-h`/`-p`) | `django/db/backends/postgresql/client.py:29-34` |

The modeled function is `settings_to_cmd_args_env`. Only its `args` (command-line
vector) assembly changes; the returned `env` dict is untouched by the patch and is
out of scope for the modeled value. The FAIL_TO_PASS test `test_parameters`
asserts the assembled arg vector for `({"NAME": "dbname"}, ["--help"])` is
`["psql", "--help", "dbname"]` — i.e. the caller-supplied parameters precede the
database name.

### What the function does (base_commit)

```python
args = [cls.executable_name]            # ["psql"]
...
if not dbname and not service:
    dbname = "postgres"
if user:  args += ["-U", user]
if host:  args += ["-h", host]
if port:  args += ["-p", str(port)]
if dbname:  args += [dbname]            # base_commit: dbname appended FIRST
args.extend(parameters)                 #              parameters appended AFTER
```

At base_commit the database name is appended to `args` *before* the caller's
extra `parameters`, producing `[..., dbname, *parameters]`. `psql` ignores any
token after the database name, so the supplied parameters are silently dropped —
the defect in the issue. The post-fix code moves `args.extend(parameters)` ahead
of the `if dbname: args += [dbname]` block, producing `[..., *parameters, dbname]`.

### Inputs ↔ Python expression bijection

The four `args += [flag, value]` connection components share one shape: emit
`[flag, value]` iff the setting is truthy. They are modeled by `optFlag flag v`
over `Option String` inputs (`v = none` ⟺ the setting is absent/falsy). The
`dbname` likewise contributes `[dbname]` iff truthy, modeled by `dbname.toList`.
The `parameters` list is contributed verbatim, in order.

| Lean input | Python expression | type | notes |
|---|---|---|---|
| `executable` | `cls.executable_name` (`"psql"`) | `String` | the program name; always the first element. |
| `user` | `settings_dict.get("USER")` | `Option String` | `some u` when truthy (`if user`), else `none`. |
| `host` | `settings_dict.get("HOST")` | `Option String` | `some h` when truthy (`if host`), else `none`. |
| `port` | `str(settings_dict.get("PORT"))` | `Option String` | `some p` (already stringified) when truthy (`if port`), else `none`. |
| `dbname` | the *effective* `settings_dict.get("NAME")` after the `if not dbname and not service: dbname = "postgres"` default | `Option String` | `some d` when truthy (`if dbname`), else `none`. The defaulting is UNCHANGED by the patch and pre-computed into the effective optional value. |
| `parameters` | the `parameters` argument | `List String` | the caller-supplied extra parameters; contributed in order. |

The `-U`/`-h`/`-p` flag *values* enter pre-stringified (the function only places
`str`s into `args`), matching `str(port)` etc. The truthiness reads (`if user`,
`if host`, `if port`, `if dbname`) are folded into the presence/absence of the
`Option`.

### result bijection

| Lean | Python | bijection |
|---|---|---|
| `result : List String` (return of `implementation_shellArgs`) | the `args` list component of `settings_to_cmd_args_env`'s `(args, env)` return | identity on the list of `str`s; the modeled value is `args`. The `env` dict is unchanged by the patch and out of scope. |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `list[str]` (`args`) | `List String` | identity (ordered list of strings). |
| optional truthy setting | `Option String` | `some x ↔` truthy value `x`; `none ↔` absent/falsy (`None`, `""`). |
| `parameters` (`list[str]`) | `parameters : List String` | identity. |
| `args += [a, b]` | `args ++ [a, b]` | list append. |
| `args.extend(parameters)` | `args ++ parameters` | list concatenation. |

`str` ↔ Lean `String`: the function operates at the value level (list assembly of
`str`s, no per-code-point logic), so `String`/`List String` are the apt models
(§2 cheatsheet).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — the *position*
  at which the caller-supplied parameters are spliced into the argument vector
  relative to the database name — is modeled DEEPLY as list concatenation in a
  fixed order, not axiomatized (SPEC_GUIDE §3: a deeply-modeled changed op is
  never axiomatized). The settings reads (`settings_dict.get(...)`, `options.get(...)`)
  are the I/O boundary, abstracted into the optional-string / list inputs. There
  is no opaque callee whose contract the proof consumes, so `axiom_check.py` is a
  skip stub and G-AX skips.
- **Effective-dbname defaulting.** `if not dbname and not service: dbname = "postgres"`
  selects the effective database name and is UNCHANGED by the patch. Its result
  is folded into the `dbname : Option String` input (the value present at the
  `if dbname:` test). It is not a callee whose property the proof consumes.
- **No flag dependency.** The function takes no mode flag; the only conditionality
  is the per-setting truthiness, captured by the `Option`/list inputs.

## G-CONF fuzz seed

Pinned LCG seed: **15851** (see `conformance_check.py` `SEED`). Corpus: random
optional `user`/`host`/`port`/`dbname` (each `None` or a short string) crossed
with random `parameters` lists (length 0–4 of short strings), over ≥1e5 fuzzed
inputs, diffed against an in-process replica of the post-patch `args` assembly
(`[executable] + optU + optH + optP + parameters + ([dbname] if dbname else [])`).
