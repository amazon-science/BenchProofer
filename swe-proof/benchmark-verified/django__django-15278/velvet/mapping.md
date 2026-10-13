# mapping.md — django__django-15278

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0ab58c120939093fea90822f376e1866fc714d1f`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/db/backends/sqlite3/schema.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `requiresTableRebuild (isUnique acceptsNull hasServerDefault : Bool)` | the routing decision (the `if (...)` condition) inside `SQLiteSchemaEditor.add_field` — `django/db/backends/sqlite3/schema.py:326` (the `if` head, body lines 326–335 post-patch) | the modeled changed decision: which materialization route a new column requires |
| `isUnique` | `field.unique` — the `Field.unique` PROPERTY, `django/db/models/fields/__init__.py:753`: `return self._unique or self.primary_key` | column observable: does this column carry an EFFECTIVE uniqueness obligation (for any reason — an explicit unique constraint or being the identity/primary column, which is always uniquely valued) |
| `acceptsNull` | `field.null` | column observable: may this column hold an absent value |
| `hasServerDefault` *(free Bool input)* | `self.effective_default(field) is not None` — `effective_default` is `BaseDatabaseSchemaEditor.effective_default`, `django/db/backends/base/schema.py:332` | column observable: a usable server-side default value is present |

The two materialization routes the decision selects between (both UNCHANGED by the
gold patch, so not modeled — only the decision is):
* `self._remake_table(model, create_field=field)` — the full table rebuild
  (`django/db/backends/sqlite3/schema.py:_remake_table`);
* `super().add_field(model, field)` — the in-place column-addition primitive
  (`BaseDatabaseSchemaEditor.add_field`, `django/db/backends/base/schema.py:491`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `field.unique` (the property `self._unique or self.primary_key`, a `bool`) | `isUnique : Bool` | Python `bool` ↔ Lean `Bool` directly. The model observes the DERIVED effective value, not the raw stored `_unique` flag. |
| `field.null` (a `bool` attribute) | `acceptsNull : Bool` | Python `bool` ↔ Lean `Bool` directly. Note the repo condition uses `not field.null`; the model writes `!acceptsNull`. |
| `self.effective_default(field) is not None` | `hasServerDefault : Bool` | the `is not None` test of the callee's return ↔ Lean `Bool` (truthiness of "a default is present"). The model abstracts the callee's value to this single boolean (§3). |
| the routing decision (`if (...)` is truthy) | `out : Bool` | `True` ⇔ rebuild route (`_remake_table`); `False` ⇔ in-place primitive (`super().add_field`). |

Python `or` over `bool`s ↔ Lean `||`; `not x` ↔ `!x`. All operands are genuine
`bool`s in the repo (`unique` is a `bool`-valued property; `null` is a field
flag; `effective_default(field) is not None` is a `bool`), so the disjunction
is an exact boolean transliteration with no truthiness subtlety.

### The `primary_key` collapse (the key R-leg)

The gold condition reads `field.primary_key or field.unique or ...`. In the
real repo `field.unique` is NOT an independent flag — it is the property

```python
@property
def unique(self):
    return self._unique or self.primary_key
```

(`django/db/models/fields/__init__.py:753` @ base_commit; the only definition
of `unique` on `Field`, no subclass overrides it). Therefore

```
field.primary_key or field.unique
  = field.primary_key or (field._unique or field.primary_key)
  = field._unique or field.primary_key
  = field.unique
```

— the `primary_key` disjunct is REDUNDANT given the effective `field.unique`
observation. The model consequently exposes the single boolean `isUnique`
(= the property value) and the modeled decision `isUnique || !acceptsNull ||
hasServerDefault` equals the gold four-operand condition on every reachable
field state. G-CONF refutes exactly this collapse: it drives the RAW pair
(`primary_key`, `_unique`) over the full cube, derives `field.unique` by the
property definition verbatim, and differential-tests model vs gold condition.

## 3. Callee provenance — `effective_default` (free Bool input, G-AX skip)

`hasServerDefault` stands for `self.effective_default(field) is not None`.
`effective_default` is an UNCHANGED callee (the gold patch does not touch it):
it returns the field's effective server-side default, or `None` when there is
none. The decision consumes it ONLY through `is not None`, i.e. as the single
boolean "a usable default is present". The spec asserts NOTHING about how that
default is computed or what its value is — it is taken as a FREE INPUT and fuzzed
over `{True, False}` in G-CONF. Because no behavioural contract is claimed about
the callee, there is nothing to validate against the real callee:
**no axiom_check.py — G-AX skip** (cf. the exemplar boolean-decision bundle
django__django-12276, same handling for its opaque inherited callee).

`field.null` is a plain stored field flag (no callee). `field.unique` is the
read-only property above over the stored `_unique` and `primary_key` flags.
`OneToOneField` forces `unique=True` in its constructor
(`django/db/models/fields/related.py:1088`) — that is why a nullable
`OneToOneField` (the F2P case) has `isUnique = true`, `acceptsNull = true`,
and no default (`hasServerDefault = false`): the new `isUnique` disjunct is
what flips its decision to the rebuild route.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15278`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the modeled decision (`isUnique || !acceptsNull || hasServerDefault`) to
Python, derives `isUnique` from the raw (`primary_key`, `_unique`) pair via
the `Field.unique` property verbatim, and differential-tests it against the
gold patch's four-operand `if` condition over the full 2⁴ raw boolean cube
plus seeded fuzz. No A-tagged callee is substituted (`hasServerDefault` is a
free boolean input).
