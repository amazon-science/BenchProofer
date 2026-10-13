# mapping.md — django__django-14376

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d06c5b358149c02a62da8a5469264d05f29ac659`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo files under change: `django/db/backends/mysql/client.py` and
`django/db/backends/mysql/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectOverride (preferredOpt secondaryOpt : Option String) (baseValue : String)` | the database-name resolution expression in `DatabaseClient.settings_to_cmd_args_env` — `django/db/backends/mysql/client.py:11` (post-patch lines 11-14) | the modeled changed behaviour: resolve the effective DB name from a precedence-ordered set of sources |
| `resolveWithPrecedence` *(deep model — I, fully spelled out)* | the chained `dict.get(k, default)` precedence ladder the patched expression implements | pure spec: highest-precedence present source wins |

There are **no axiomatized callees**: `dict.get(key, default)` is not a repo
callee we leave opaque — it is the language operation we model deeply as
`Option.getD`. Nothing is delegated to an unchanged callee whose contract we
would have to assume (so no `axiom_check.py`, mirroring the pure-data band
exemplar `tasks/scikit-learn__scikit-learn-13439/`).

### 1.1 The change, and what is F2P-observable

The gold patch touches two files:

1. **`client.py:11`** (`settings_to_cmd_args_env`): the database-name source is
   widened from a one-level fallback
   `OPTIONS.get('db', NAME)` to a two-level fallback
   `OPTIONS.get('database', OPTIONS.get('db', NAME))`, i.e. a *preferred* key is
   consulted first and the prior key is demoted to a backward-compat secondary.
   The trailing `if db:` / `args += [db]` is renamed `if database:` /
   `args += [database]` (pure local rename, observationally identical).
2. **`base.py:203,205`** (`get_connection_params`): the connection-kwarg names
   `db` / `passwd` are renamed to `database` / `password`. This builds a kwargs
   dict passed to the third-party `Database.connect(**conn_params)` driver; it
   is **not** exercised by any FAIL_TO_PASS or PASS_TO_PASS test (the tests live
   in `tests/dbshell/test_mysql.py` and call only `settings_to_cmd_args_env`).

The only **independently F2P-observable fixed behaviour** is (1)'s
precedence-widening of the value resolution: the new tests
(`test_options_non_deprecated_keys_preferred`,
`test_options_override_settings_proper_values`) check that the preferred key is
preferred over the deprecated key which is preferred over `NAME`. The
`selectOverride` method models exactly that. The `base.py` rename and the local
identifier rename in `client.py` carry no separately-observable behaviour, so
they are shipped in `patch.diff` (gold verbatim, required for G-RESOLVE) but are
not given their own modeled method or `Solution_prepatch_<k>.lean` (G-DIFF needs
one failing prepatch per independently-observable fixed behaviour; there is one).

## 2. Type abstraction (R/I-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `OPTIONS.get('database', d)` — key may be absent | `preferredOpt : Option String` | key present with value `v` ↔ `some v`; key absent ↔ `none`; `.get(k, d)` ↔ `Option.getD` |
| `OPTIONS.get('db', d)` — key may be absent | `secondaryOpt : Option String` | as above |
| `settings_dict['NAME']` — always present (a `str`) | `baseValue : String` | the configured database name; a Python `str` ↔ Lean `String` |
| the resolved database name (`str`) | `out : String` | the value that becomes the trailing positional CLI argument |

**Presence vs truthiness (load-bearing).** `dict.get(k, default)` returns the
stored value whenever the key is *present*, even if that value is the empty
string `''` — it does NOT fall through on a falsy value. `Option.getD` has
exactly this semantics: `(some "").getD d = ""`. So the bijection is
`key-present ↔ some`, `key-absent ↔ none`, NOT `truthy ↔ some`. (The later
`if database:` test in the real code is a *separate* downstream truthiness check
that decides whether to append the positional arg at all; it is outside the
modeled value-resolution and observationally identical pre/post-patch — the F2P
tests always supply a non-empty resolved name.)

## 3. Callee provenance

None. The modeled behaviour is a pure precedence selection over the three
candidate values; there is no unchanged callee to axiomatize, and no deep model
of an external callee to validate against (so no A-consumed and no A-reference
rows — `meta.json axioms = []`, `deep_model_references = []`). G-AX is therefore
`skip` for this bundle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14376`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `resolveWithPrecedence` (an all-I/R op: nested `Option.getD`) to
Python over the real `dict`/`str` types and compares against the patched
`settings_to_cmd_args_env`'s resolved database name on ≥10⁵ fuzzed
`settings_dict` inputs.
