# mapping.md — django__django-15525

Binds `Solution.lean` symbols to the repo at
`base_commit = fbacaa58ffc5a62456ee68b90efa13957f761ce4`.

Repo file under change: `django/core/serializers/base.py`
(`build_instance`, the natural-key branch taken when a deserialized record has
no primary key but the model supports natural keys).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `naturalKeyForLoadedRecord (targetDb : String) (mut storeHandle : Option String)` | `build_instance(Model, data, db)` — the `pk is None and hasattr(default_manager, "get_by_natural_key") and hasattr(Model, "natural_key")` branch, `django/core/serializers/base.py:333-345` | the modeled natural-key branch (build a fresh record, derive its natural key for the target DB) |
| `targetDb` | `db` — the database alias the fixture is being loaded into | the target database the record is loaded into |
| `storeHandle` (`mut`) | `obj._state.db` — the database the freshly built record is associated with (read by reference-following during `natural_key()`); written by `obj._state.db = db` | the mutable store handle the fix sets before deriving the key |
| `naturalKeyVia` *(opaque — A-reference / unchanged callee)* | `obj.natural_key()` — the model's own natural-key method, `Book.natural_key`/`NaturalKeyWithFKDependency.natural_key` in the issue/test, which may follow a foreign key (`self.author.natural_key()`) | the (unchanged) natural-key derivation; its reference-following resolves against `obj._state.db` |
| `key` (return) | `natural_key` — the local bound by `natural_key = obj.natural_key()` (used next as `get_by_natural_key(*natural_key)`) | the derived natural key |

Precondition modeled: `require storeHandle = none`. A *freshly built* record
(`Model(**data)`, no `_state.db` assigned in `__init__`) carries the default
store handle `None` (`ModelState.db = None`, `django/db/models/base.py:454`).
The branch is reached only for such a record (it has `pk is None`); the model
scopes to exactly this freshly-built case.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `obj._state.db` : a database alias `str` (e.g. `"other"`) once associated, `None` for a freshly built record | `Option String` | `some s` ↔ the alias string `s`; `none` ↔ `None`. `obj._state.db = db` ↔ `storeHandle := some targetDb`. |
| `db` : the target database alias (`str`, e.g. `"other"`) | `String` | identity on the alias string. |
| `obj.natural_key()` : a tuple of field values (`(self.name,) + self.author.natural_key()`), each rendered as a string in the serialized key | `List String` | the natural-key tuple ↔ `List String`; tuple concatenation ↔ list. Its VALUE depends on `obj._state.db` because reference-following (`self.author`) issues a DB read routed by the instance store handle (`router.db_for_read(..., instance=self)` via `db_manager(hints=...)`). |

The key abstraction is that `obj.natural_key()`'s result is a **function of the
store handle**: following `self.author` triggers
`ForwardManyToOneDescriptor.get_object` →
`field.remote_field.model._base_manager.db_manager(hints={instance: obj}).all()`
(`django/db/models/fields/related_descriptors.py:121,164-168`), whose router
hints carry `obj._state.db`. Hence `naturalKeyVia : Option String → List String`
takes the handle as its argument. Whether the result actually differs between
`none` and `some targetDb` is data-dependent (it differs precisely when the
related row is absent from the default DB but present in the target DB — the
issue's scenario); the spec does not assume it differs, only that the operation
must feed the derivation the *target* handle.

## 3. Callee provenance

- `obj.natural_key()` — **UNCHANGED** by the fix. Modeled as the opaque free
  function `naturalKeyVia` of the store handle. No contract is asserted about
  its return value (it is refined, never replaced), so there is nothing for
  G-AX to validate — **no axiom_check.py** (meta.json G-AX skip). It is *not* a
  consumed axiom: the proof consumes no `ensures` of it; it appears only as the
  carrier whose argument the operation controls.
- `obj._state.db = db` — the **CHANGED** op (the patch's added line), modeled
  deeply as the assignment `storeHandle := some targetDb` (I-tagged, see
  refinement.md). No outside contract is consumed.
- `Model(**data)` — the fresh-record construction, unchanged; supplies the
  `none` store handle (the `require`).

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The impl region's content is
the deep state association `storeHandle := some targetDb` on a live ORM model
instance, followed by a derivation (`obj.natural_key()`) whose observable value
materializes only by issuing a **real database read routed through the instance
store handle**. There is no DB-free, input-dependent R/I shadow to
differential-test:

- The only behavioural difference between the fixed and buggy code is *which
  database* the reference-following query in `natural_key()` targets. Observing
  it requires standing up ≥2 Django databases, a model with a foreign-key
  natural-key dependency, and a fixture whose related row exists only in the
  non-default DB — i.e. the F2P integration test itself
  (`NaturalKeyFixtureOnOtherDatabaseTests.test_natural_key_dependencies`), not a
  pure transliteration this gate can fuzz over ≥1e5 inputs.
- The changed op's content is the state assignment `storeHandle := some
  targetDb`; its only DB-free R/I shadow is the constant `some targetDb`.
  Diffing that against the constant target alias carries no information — there
  is no input-dependent computation to refute. `naturalKeyVia` is the A-tagged
  (opaque) callee, left as the real `obj.natural_key()`, and its value is
  precisely the DB-routed read that cannot be reproduced DB-free.

Per SPEC_GUIDE §0 / WORKER_PROMPT (and the django-11179 / django-13089
precedent): when the impl region is the deep state mutation of a live ORM
instance with no DB-free R/I shadow, set `meta.json conf_skip=true` and ship a
`status=skip` stub. Soundness of the modeled mutation is carried instead by
**G-VERIFY** (the spec provably forces `storeHandle = some targetDb` and
`key = naturalKeyVia (some targetDb)` on return), **G-DIFF** (the prepatch,
which derives the key before associating the record, fails exactly those
clauses), and **G-RESOLVE** (the gold patch resolves).

## 5. Notes

The model is the genuine-`mut` form (directive 5 showcase): `storeHandle` is
declared `mut`, assigned `storeHandle := some targetDb`, and its post-state
pinned to the exact value `some targetDb`. The ordering — associate the record
with the target DB *before* deriving the key — is captured by the data flow:
the returned `key` is `naturalKeyVia` applied to the *updated* handle
(`= naturalKeyVia (some targetDb)`), not the pre-state handle. The prepatch,
which derives at the unset handle, fails this clause — the exact bug.
