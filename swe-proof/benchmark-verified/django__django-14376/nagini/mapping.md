# mapping.md — django__django-14376

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d06c5b358149c02a62da8a5469264d05f29ac659`, states the type
abstraction, and gives the provenance of the deep-model reference.

Repo file under change (the F2P-observed behaviour): `django/db/backends/mysql/client.py`.
A second hunk touches `django/db/backends/mysql/base.py` (see §4).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_db_arg(opt_database, opt_db, settings_name)` | `DatabaseClient.settings_to_cmd_args_env` — `django/db/backends/mysql/client.py:7` (database selection + append, body lines 11 and 54-55) | the modeled changed function: it computes the database name from the connection-options mapping with three-level precedence and decides the trailing positional argument |
| `select_name(opt_primary, opt_legacy, settings_name)` *(deep model — A-reference)* | the database-selection expression `settings_dict['OPTIONS'].get('database', settings_dict['OPTIONS'].get('db', settings_dict['NAME']))` — `client.py:11` post-patch | pure spec: the three-level precedence selection, validated `== ` the real gold-patched callee by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view): `db = settings_dict['OPTIONS'].get('db',
settings_dict['NAME'])` (`client.py:11` pre-patch) — only the legacy key and the
settings name; the non-deprecated `database` key is never examined. The local
variable is renamed `db` → `database` and the trailing append `if db: args +=
[db]` → `if database: args += [database]` (`client.py:54-55`), an identical
operation under the rename.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| database-name `str` (the `OPTIONS['database']`/`OPTIONS['db']` values and `settings_dict['NAME']`) | `List[int]` of Unicode code points; spec carried by `PSeq[int]` via `ToSeq` | `s[k]` ↔ `xs[k] == ord(s[k])`; `len(s)` ↔ `len(xs)`; an empty `str` ↔ `[]`; only equality of character content is observed |
| `OPTIONS.get(key, fallback)` — key present vs absent | `Optional[List[int]]` parameter: `None` ↔ key absent (fall through to next precedence level); a present `List[int]` ↔ the value stored under the key | a present option short-circuits the fallback *even when its value is the empty string* — exactly Python `dict.get`'s membership semantics; the model's `select_name` returns a present option's value regardless of emptiness, matching `dict.get` |
| truthiness `if database:` on the selected name (`client.py:54`) | `len(selected) > 0` | the empty string is falsy ⇒ no trailing argument; a non-empty string is truthy ⇒ appended. The `appended` boolean in the result reports this. |
| the trailing positional argument `args += [database]` | the selected name materialised into a freshly-owned `List[int]` (the second result component) | `str` value appended ↔ the code-point list appended; the append happens iff `appended` is true |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`; the
selection precedence is carried by `PSeq[int]` via `ToSeq`. The
connection-options values and the settings name are read-only inputs (the
operation selects among them and copies the chosen one), so they are held at
fractional permission (`1/2`, Required AND Ensured; the pure `select_name` reads
at `1/8`).

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `select_name` deep model ↔ the gold-patched database selection
**Callee:** the gold-patched expression in
`DatabaseClient.settings_to_cmd_args_env`:

```python
database = settings_dict['OPTIONS'].get(
    'database',
    settings_dict['OPTIONS'].get('db', settings_dict['NAME']),
)
...
if database:
    args += [database]
```

The changed selection is modelled **deeply** by the `@Pure` `select_name` (and
the impl branch + copy in `resolve_db_arg`); there is **no `@ContractOnly`
axiom** the proof consumes. The precedence is exactly:

  `OPTIONS['database']` if present, else `OPTIONS['db']` if present, else `NAME`,

i.e. the non-deprecated database-name option takes precedence over the legacy
option, which takes precedence over the settings-level name. `dict.get`'s
membership semantics make a *present* key short-circuit the fallback regardless
of whether its value is empty — `select_name` mirrors this (a present
`Optional` returns its value even when the list is empty).

**Soundness check (G-AX):** because the A-reference models a *changed*
function, it must be validated against the GOLD-PATCHED callee, not the
base_commit one. `axiom_check.py` therefore first applies the bundle's gold
`patch.diff` to the in-container `/testbed` checkout (idempotently — it detects
the post-patch `'database'` selection and skips re-applying if the harness
already applied the gold, e.g. `apply_gold=True`), then imports and runs the
real post-patch `DatabaseClient.settings_to_cmd_args_env` on every combination
of `{absent, several values, empty}` for the two option keys × several settings
names (plus 3000 randomized fuzz cases), with no user/host/port/charset/ssl so
the only trailing positional argument is the database, and asserts that the
trailing argument equals the model's prediction (`select_name` when non-empty,
else absent). It explicitly asserts the discriminator: when both options are
present with different non-empty values, the non-deprecated `database` value
wins. It imports only Django's own MySQL backend (the module the patch
changes); nothing test-specific. Validated in the pinned eval container,
RC=0, 0 mismatches over 3100 observations. Exit 0 iff sound (rc 3 if the
post-patch source cannot be established).

## 4. The second hunk (`base.py`) — not consumer-observable, not modeled

The gold patch also edits `MySQLDatabaseWrapper.get_connection_params`
(`django/db/backends/mysql/base.py:203-205`): `kwargs['db']` → `kwargs['database']`
and `kwargs['passwd']` → `kwargs['password']`, the connection-keyword rename the
problem statement asks for. This hunk is **not exercised by any FAIL_TO_PASS or
PASS_TO_PASS test** — every test in the resolving set lives in
`tests/dbshell/test_mysql.py` and calls only `settings_to_cmd_args_env`
(client.py). It is shipped verbatim in `patch.diff` (so the real patch is the
gold), but it produces no differential the spec can sense on the tested inputs
(it would require a live mysqlclient connection), so it is not modeled and there
is no `model_prepatch` variant for it. The single F2P-discriminating behaviour
is the client-side three-level precedence of §3, which `model.py` pins and
`model_prepatch.py` reproduces the bug against.
