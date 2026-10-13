# mapping.md — django__django-14376

## Symbol binding (file:line @ base_commit d06c5b358149c02a62da8a5469264d05f29ac659)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_dbArg` / `problem_spec_dbArg` | `DatabaseClient.settings_to_cmd_args_env` — its choice of the trailing database-name argument | `django/db/backends/mysql/client.py:8-11,54-55` |
| `implementation_connParams` / `problem_spec_connParams` | `DatabaseWrapper.get_connection_params` — the database-name + password entries it writes into the connection-kwargs mapping | `django/db/backends/mysql/base.py:194,202-205` |

Two small, independent pieces of behavior change, one per file. They are modeled
as two CLEVER triples in the same `Solution.lean` (callee-independent; no ordering
constraint between them).

### 1. `dbArg` — the trailing database-name argument (`client.py`)

Post-patch source (`patch.diff`):
```python
database = settings_dict['OPTIONS'].get(
    'database',
    settings_dict['OPTIONS'].get('db', settings_dict['NAME']),
)
...
if database:
    args += [database]
```

The database name is chosen with a fixed precedence: the `'database'` OPTIONS key
if **present**, else the deprecated `'db'` OPTIONS key if present, else the
connection's `NAME`. The chosen value is appended to the argument vector only when
it is non-empty (`if database:`).

`dict.get(k, default)` returns the stored value when the key is present (even if
that value is falsy/empty) and `default` only when the key is absent. This is the
crux: `OPTIONS = {'database': ''}` selects `''` and short-circuits — it does NOT
fall through to `'db'`/`NAME`. The model captures presence with `Option` and the
`get(k, default)` precedence with `Option.getD`:

```
chosen = optDatabase.getD (optDb.getD name)
```

The base_commit code chose `db = OPTIONS.get('db', NAME)` — i.e. only the
deprecated key then `NAME`, ignoring `'database'` entirely (the bug); that is the
prepatch_1 impl.

#### Inputs ↔ Python expression bijection (dbArg)

| Lean input | Python expression | type | notes |
|---|---|---|---|
| `optDatabase` | `'database' in OPTIONS ? OPTIONS['database'] : <absent>` | `Option String` | `some x` iff the `'database'` key is present (with value `x`, possibly `""`); `none` iff absent. |
| `optDb` | `'db' in OPTIONS ? OPTIONS['db'] : <absent>` | `Option String` | `some x` iff the deprecated `'db'` key is present; `none` iff absent. |
| `name` | `settings_dict['NAME']` | `String` | the configured database name; `""` models a falsy/empty `NAME`. |

#### result bijection (dbArg)

| Lean | Python | bijection |
|---|---|---|
| `result : Option String` | the trailing database-name token of `args` | `some d ↔` `args` ends with the single extra token `d` (`if database: args += [database]`); `none ↔` no trailing database token (`database` empty/falsy). The rest of `args` is unchanged by this patch and out of scope for this triple. |

### 2. `connParams` — connection-kwargs entries for name + password (`base.py`)

Post-patch source (`patch.diff`):
```python
if settings_dict['NAME']:
    kwargs['database'] = settings_dict['NAME']
if settings_dict['PASSWORD']:
    kwargs['passwd' -> 'password'] = settings_dict['PASSWORD']
```

When the configured `NAME` is non-empty it is written under the key `"database"`;
when `PASSWORD` is non-empty it is written under `"password"`. base_commit used the
deprecated keys `"db"`/`"passwd"` (the prepatch_2 impl).

#### Inputs ↔ Python expression bijection (connParams)

| Lean input | Python expression | type | notes |
|---|---|---|---|
| `name` | `settings_dict['NAME']` | `Option String` | `some n` iff truthy (`if settings_dict['NAME']`), else `none`. |
| `password` | `settings_dict['PASSWORD']` | `Option String` | `some p` iff truthy (`if settings_dict['PASSWORD']`), else `none`. |

#### result bijection (connParams)

| Lean | Python | bijection |
|---|---|---|
| `result : List (String × String)` | the `{'database': …}` / `{'password': …}` entries the patch writes into `kwargs` | the modeled value is exactly the (key, value) entries this patch is responsible for, in source order. The other `kwargs` entries (`conv`, `charset`, `user`, `unix_socket`/`host`, `port`, `client_flag`, and `options`) are UNCHANGED by the patch and out of scope. Mapping uses an association list since only the keys/values these two lines write matter. |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `str` value | `String` | identity (value-level; no per-code-point logic). |
| key present in dict | `some x` | `OPTIONS.get(k, default)` returns the stored `x` when `k` present. |
| key absent | `none` | `get` returns `default`. |
| `dict.get(k, default)` precedence | `opt.getD default` | `some x ↦ x`, `none ↦ default`. |
| truthy string test (`if s:`) | `s ≠ ""` (or `Option` is `some`) | `""`/`None` falsy ↔ `none`/empty. |
| `args += [database]` (when truthy) | `some database` / `none` | the trailing token's presence. |
| `kwargs[key] = v` (when truthy) | `[(key, v)]` appended | association-list entry. |

## Callee provenance + flag dependencies

- **No consumed callee axiom (both triples).** The behaviors the patch changes —
  the precedence among option sources for the database name, and the keys under
  which name/password are recorded — are modeled DEEPLY (precedence selection via
  `Option.getD`; association-list construction), not axiomatized (SPEC_GUIDE §3:
  a deeply-modeled changed op is never axiomatized). The settings/option reads
  (`settings_dict[...]`, `OPTIONS.get(...)`) are the I/O boundary, folded into the
  `Option String` / `String` inputs. There is no opaque callee whose contract the
  proof consumes, so `axiom_check.py` is a skip stub and G-AX skips.
- **`dict.get(k, default)` semantics.** The only subtlety is that a present key
  with an empty value is still selected (does not fall through). This is captured
  by `Option.getD`: `(some "").getD d = ""` (selected, then dropped by the
  emptiness test), whereas `none.getD d = d` (fallthrough). The `dict.get` builtin
  is UNCHANGED stdlib behavior, modeled deeply — not a consumed axiom.
- **No flag dependency.** Neither function takes a mode flag; the only
  conditionality is per-source presence/truthiness, captured by the `Option` /
  emptiness models.

## G-CONF fuzz seed

Pinned LCG seed: **14376** (see `conformance_check.py` `SEED`). Corpus: for `dbArg`,
random `optDatabase`/`optDb` (each absent, or present with a short — possibly
empty — string) crossed with a random `name` (possibly empty); for `connParams`,
random optional `name`/`password` (each `None` or a short string). ≥1e5 fuzzed
inputs total, diffed against in-process replicas of the post-patch behavior of
both functions.
