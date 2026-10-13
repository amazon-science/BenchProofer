# mapping.md — django__django-11211

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ba726067604ce5a8ca3919edf653496722b433ab`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/models/fields/__init__.py` (the `UUIDField`
class, `class UUIDField(Field):` at line 2309).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepare_key(value)` | `UUIDField.get_prep_value(self, value)` — added by the gold patch at `django/db/models/fields/__init__.py:2328` (between `get_internal_type` line 2325-2326 and `get_db_prep_value` line 2328) | the modeled changed function (the key-preparation method the field gains) |
| `base_prepare(value)` *(axiom — A-consumed)* | `Field.get_prep_value(self, value)` — `django/db/models/fields/__init__.py:771-775` (reached via `super().get_prep_value(value)`) | unchanged base callee the new method defers to first |
| `canonicalize(value)` *(axiom — A-consumed)* | `UUIDField.to_python(self, value)` — `django/db/models/fields/__init__.py:2338-2349` (reached via `self.to_python(value)`) | unchanged `UUIDField` callee the new method reuses to convert a value to its canonical `uuid.UUID` form |
| `matches_target_key(prepared, identity)` *(@Pure — the pure region)* | the equality the in-Python prefetch join performs: `rel_obj_cache.get(instance_attr_val, [])` at `django/db/models/query.py:1770` against the cache built at `:1746-1749`, whose keys are `lambda obj: (obj.pk, obj.__class__)` (`django/contrib/contenttypes/fields.py:210`) | the join predicate the prepared key must satisfy, spelled out over the carrier's facets |
| `Value` class (`is_none`, `canon`, `key`, `is_canon_form`) | the value flowing through `get_prep_value` (a `uuid.UUID`, a `str`/`int` storage form, or `None`) | minimal carrier of the observed facets: emptiness, the identity denoted, and BOTH halves of the join key |

The pre-patch state (for the refinement audit): `UUIDField` defines **no**
`get_prep_value`, so it inherits `Field.get_prep_value` (line 771) — the
identity/`Promise`-cast passthrough that does NOT canonicalize, and therefore
delivers neither half of the target's key.

## 2. Type abstraction (R-refinements)

The value passing through `get_prep_value` is, in reality, one of:
`None`; a `uuid.UUID` (already canonical); or a textual/integer storage form
(`str` such as `'1a8e4c...'`, or an `int`) that *denotes* a UUID identity. The
model abstracts every such value to a `Value` object carrying only the facets
the join observes:

| repo reality | model carrier facet | meaning |
|---|---|---|
| the value is `None` (no identity stored) | `is_none: bool` | `True` iff the value is `None` |
| the 128-bit canonical identity the value denotes (`uuid.UUID.int`) | `canon: int` | the identity the value *means* — equal for the string form and the `uuid.UUID` form of the same UUID |
| the NUMERIC part of the key this value yields in the in-Python prefetch join dict | `key: int` | for an already-canonical `uuid.UUID`, `key == canon` (a `uuid.UUID` hashes and compares by its `.int`); for a raw textual/int storage form that was never converted, `key` is the as-stored identity, which need NOT equal `canon` (a `str` keys differently from the `uuid.UUID` it spells) |
| the FORM the key is held in — `isinstance(value, uuid.UUID)` | `is_canon_form: bool` | `True` iff the value is held in the canonical object form, i.e. is a real `uuid.UUID` rather than a `str`/`int` that merely spells one. This is the other half of the join key, and it is the half Python's `==` consults FIRST |

### 2.1 Why the join key has two halves (and why both are pinned)

The prefetch join (`django/contrib/contenttypes/fields.py:198-215`,
`GenericForeignKey.get_prefetch_queryset`) supplies two key callables that
`prefetch_one_level` matches through a dict
(`django/db/models/query.py:1746-1749` builds it, `:1770` looks up):

* target side — `lambda obj: (obj.pk, obj.__class__)` (`fields.py:210`): the
  related object's own pk as loaded from the DB, which for a `UUIDField` pk is
  **always a real `uuid.UUID`** (`is_canon_form == True`, `key == canon`);
* holder side — `(model._meta.pk.get_prep_value(getattr(obj, self.fk_field)),
  model)` (`fields.py:205`): the holder's *stored* `object_pk` (a `str` in the
  F2P) run through `get_prep_value`.

A dict lookup is `hash` **then** `==`. `uuid.UUID` defines
`__hash__ = hash(self.int)` and an `__eq__` that returns `NotImplemented`
unless the other operand is also a `uuid.UUID`, so:

```python
u = uuid.uuid4()
hash(u) == hash(u.int)          # True  — same bucket
u == u.int                      # False — different value
{(u, C): [obj]}.get((u.int, C)) # None  — the join MISSES
```

So a prepared key that carries the right 128 bits **in the wrong form** matches
nothing. The match succeeds iff `get_prep_value(<stored str>)` agrees with the
`uuid.UUID` pk on *both* halves: the canonical identity (`key == canon`) **and**
the canonical object form (`is_canon_form`). Those are exactly the two
discriminating postconditions of `prepare_key`
(`Implies(not value.is_none, Result().key == value.canon)` and
`Implies(not value.is_none, Result().is_canon_form)`), and
`matches_target_key(Result(), value.canon)` states them together as the join
predicate they exist to satisfy. `obj.__class__` / `model` (the class half of
the composite key) is unchanged by this fix and is omitted from the model.

The form facet is not decoration and it is not a narrowing: it is a previously
**unconstrained observable** of the result. `axiom_check.py` executes the three
lines above (hash equal / `==` unequal / dict miss) against the real `uuid`
module on every fuzz identity, so a Python release that made `uuid.UUID` compare
equal to its `int` — which would make the facet redundant — fails G-AX loudly
rather than leaving a dead clause behind.

### 2.2 Input domain: nothing was excluded to obtain the guarantee

`prepare_key`'s `Requires` is permission-only
(`Acc(value.is_none, 1/2) & Acc(value.canon, 1/2) & Acc(value.key, 1/2) &
Acc(value.is_canon_form, 1/2)`). In particular:

* **No carrier well-formedness precondition was added.** The model deliberately
  does NOT assume `is_canon_form ⇒ key == canon`, even though every *reachable*
  value satisfies it. Leaving it unassumed keeps the admitted domain strictly
  wider (textual, integer, already-canonical and even inconsistent carriers),
  which makes the postcondition harder, not easier, to discharge. The
  `partial-domain-canon-form-guard` case in `properties.py` is the rival that
  would exploit such an assumption; it rejects.
* **The `None` branch was already domain-restricted before the form clause
  existed.** `Implies(value.is_none, Result().key == value.key)` has been in the
  spec from the start, and `Field.get_prep_value`'s `Promise` cast
  (`fields.py:772-773`) is the only input on which the base step is not the
  identity. A `Promise` never reaches this method in the prefetch path (the
  holder's `object_pk` is a DB-loaded `str`), so adding
  `Implies(value.is_none, Result().is_canon_form == value.is_canon_form)` for
  the empty case restricts no input that was previously in scope — it pins the
  fourth facet on the branch where the other three were already pinned.
* `str`/`int` indexing and `uuid.UUID` internals are not Nagini-expressible; the
  carrier is the minimal `Value` class throughout, with the identity facets as
  `int` and emptiness/form as `bool`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `base_prepare` ↔ `Field.get_prep_value` (A-consumed)
**Callee:** `Field.get_prep_value` (`django/db/models/fields/__init__.py:771-775`):
```python
def get_prep_value(self, value):
    """Perform preliminary non-db specific value checks and conversions."""
    if isinstance(value, Promise):
        value = value._proxy____cast()
    return value
```
It casts a lazy translation `Promise` to its concrete value and otherwise
returns `value` unchanged. On every value `UUIDField.get_prep_value` forwards
to it (a `uuid.UUID`, a `str`, an `int`, or `None` — none of which is a
`Promise` in the prefetch path), it is the **identity**: it changes neither the
canonical identity, the numeric part of the current join key, the form the value
is held in, nor the emptiness. The axiom encodes exactly that
identity-on-facets contract on all four facets (the weakest the proof needs); it
does NOT claim anything about the `Promise` branch, which never fires for these
inputs. G-AX runs the real `Field.get_prep_value` and asserts the round-trip
identity — value, numeric key, and `isinstance(_, uuid.UUID)` form flag — on
UUID, string-form, int-form, and `None` values.

### 3.2 `canonicalize` ↔ `UUIDField.to_python` (A-consumed)
**Callee:** `UUIDField.to_python` (`django/db/models/fields/__init__.py:2338-2349`):
```python
def to_python(self, value):
    if value is not None and not isinstance(value, uuid.UUID):
        input_form = 'int' if isinstance(value, int) else 'hex'
        try:
            return uuid.UUID(**{input_form: value})
        except (AttributeError, ValueError):
            raise exceptions.ValidationError(...)
    return value
```
For a non-`None`, non-`uuid.UUID` value it parses the storage form into a
`uuid.UUID` (`uuid.UUID(hex=...)` for a string at line 2342,
`uuid.UUID(int=...)` for an int); a value already a `uuid.UUID` (or `None`)
passes through at line 2349. In every non-`None` case the **returned object is a
`uuid.UUID`** — that is the `Implies(not value.is_none, Result().is_canon_form)`
clause, read straight off the two return statements — and its numeric join key
is its canonical `.int` identity, i.e.
`Implies(not value.is_none, Result().key == value.canon)`. `None` passes
through unchanged, in the same (non-canonical) form:
`Implies(value.is_none, Result().key == value.key)` and
`Implies(value.is_none, Result().is_canon_form == value.is_canon_form)`. The
axiom encodes only these obligations (the weakest the proof needs); it does NOT
model the `ValidationError` raise path, because the prefetch join only ever
feeds `to_python` the well-formed stored representation of an existing UUID pk
(the value originally written by `get_db_prep_value`). G-AX runs the real
`UUIDField.to_python` on the canonical UUID form, the 32-char hex string form,
the hyphenated string form, the int form, and `None`, and asserts the returned
object is a `uuid.UUID` whose join key equals the canonical UUID identity (and
that the string form and the `uuid.UUID` form of the same UUID yield equal keys
*and compare equal* — the core of the join match).

**Termination obligation:** `prepare_key` carries
`Requires(MustTerminate(14))` (total correctness). The real
`UUIDField.get_prep_value` is a bounded two-call composition that always
returns; under Nagini's default partial-correctness semantics a diverging
implementation would satisfy every `Ensures` vacuously, so the obligation is
required for the spec to reject such implementations, and it is stated at the
METHOD level because loop invariants alone do not reject a diverging body. The
callees and the `Value` constructor carry strictly smaller measures —
`canonicalize` 10, `base_prepare` 6, `Value.__init__` 2 — so the composition
discharges the caller's obligation without leaking it. `properties.py`'s
`divergence-nonterminating-body` case is the rival this obligation exists to
reject (it computes the correct result and then loops forever); it fails with
`Obligation leak check failed`.

**Soundness check (G-AX):** `axiom_check.py` configures a minimal Django
environment and exercises the REAL `Field.get_prep_value` and
`UUIDField.to_python` on boundary cases (`uuid.UUID(int=0)`,
`uuid.UUID(int=2**128-1)`, `uuid.UUID(int=1)`, a `uuid4`, a `uuid1`, each in its
`uuid.UUID`, 32-char-hex, hyphenated-hex, and int forms; `None`) plus 5000
randomized UUID fuzz cases, asserting both axioms' `Ensures` on all four facets,
the join-key-equality property the prefetch relies on, and the dict-miss
demonstration from section 2.1. It imports only Django (the repo under test,
available in-container) and stdlib `uuid`/`random`. Exit 0 iff sound.

## 4. Conformance (G-CONF — conformance_check.py)

SHADOW = the impl region of `prepare_key` verbatim (contracts stripped); its
two @ContractOnly callees delegate to the REAL repo functions per section 1
(`base_prepare` -> `Field.get_prep_value` invoked unbound on the field
instance, `canonicalize` -> `UUIDField.to_python`). ORACLE = the real patched
`UUIDField.get_prep_value` (gate applies `../patch.diff` to `/testbed`).
Bridge per section 2 (`raw` repo value <-> `Value` facets, including
`is_canon_form = isinstance(raw, uuid.UUID)`). Inputs: `None` + 10 boundary
identities x 7 storage forms + 20000 fuzz identities x 5 forms = 100071
Requires-satisfying inputs. Every non-empty prepared value is additionally
checked to *resolve* against its target key in a real one-entry dict, so the
comparison is on the join's own terms and not only on the facet tuple.
**Pinned fuzz seed: 11211.**
