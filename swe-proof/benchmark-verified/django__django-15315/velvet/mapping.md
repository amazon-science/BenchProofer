# mapping.md — django__django-15315

Symbol binding, the Lean↔Python type bijection (used by G-CONF), callee
provenance, and the pinned G-CONF fuzz seed. Spec provenance: **cold** (derived
only from `problem_statement`, the gold `patch`, and the repo source at
`base_commit = 652c68ffeebd510a6f59e1b56b3e007d07683ad8`).

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. The modeled function

| Lean | Python | location @ base_commit |
|---|---|---|
| `fieldHashMethod` | `Field.__hash__(self)` | `django/db/models/fields/__init__.py:544` |

`Field.__hash__` returns the integer digest used to place a model field into
hash-based containers (`dict`, `set`). The patch changes WHICH key is handed to
the builtin `hash`:

```
- return hash((
-     self.creation_counter,
-     self.model._meta.app_label if hasattr(self, 'model') else None,
-     self.model._meta.model_name if hasattr(self, 'model') else None,
- ))
+ return hash(self.creation_counter)
```

`fieldHashMethod` models that decision: given the hashing primitive, the field's
assignment-independent intrinsic identity, and whatever association metadata the
field currently carries, it returns the digest — pinned to the intrinsic
identity ALONE.

## 2. The type bijection (Lean ↔ Python), used by G-CONF

| Lean | Python (real repo type) |
|---|---|
| `pyHash : HashKey → Int` | the builtin `hash` applied to the chosen key |
| `intrinsicId : Int` | `self.creation_counter` — an `int` assigned once in `Field.__init__` (`fields/__init__.py:164` / `:167`) and never mutated thereafter |
| `modelAssoc : Option (List Char × List Char)` | the field's association metadata at hash time: `none` ↔ `not hasattr(self, 'model')` (standalone field); `some (app, name)` ↔ `(self.model._meta.app_label, self.model._meta.model_name)` once `contribute_to_class` (`:775`) has set `self.model` |
| `HashKey.solo i` | the bare key `i` handed to `hash` (post-patch: `hash(self.creation_counter)`) |
| `HashKey.composite i a` | the tuple key `(i, app, name)` (the pre-patch key; used only by the prepatch skeleton and never by the frozen spec) |
| `fieldHashKey intrinsicId = solo intrinsicId` | the post-patch key: `self.creation_counter` alone |

The hashing primitive is taken as a **FREE INPUT** (no axioms): the spec makes no
claim about which integers `hash` returns — it holds for EVERY hashing function.
The behaviour under spec is purely *which key is hashed*, which is what the patch
changes. `out = pyHash (fieldHashKey intrinsicId)` is therefore the strongest
faithful statement: the digest is a function of the intrinsic identity only.

`creation_counter` is the field's intrinsic identity precisely because it is set
once at construction and is **never reassigned** — `contribute_to_class` sets
`self.model` but leaves `creation_counter` untouched. So pinning the key to it
makes the digest immutable across the field's lifetime, which is the property the
issue demands (a field's hash must not change when it is assigned to a model
class — see `Solution.lean`'s `fieldHash_immutable` and the F2P
`test_hash_immutability`).

## 3. Callee provenance (the one callee is UNCHANGED by the patch — free input, no G-AX)

| accessor | real callee | unchanged? |
|---|---|---|
| `pyHash` | the builtin `hash` | yes — the patch changes its ARGUMENT, never `hash` itself |

The only callee is `hash`, unchanged by the patch, so it is not axiomatized; it
is abstracted into the free input `pyHash`. There is nothing for G-AX to check
against a real callee, so this bundle ships **no `axiom_check.py`** and G-AX is
`skip` (cf. the no-axiom exemplar `django__django-11820`). The patch's content is
entirely in which key is hashed — modeled deeply (`fieldHashKey`) and
differential-tested by G-CONF (§4).

## 4. G-CONF fuzz seed

`SEED = 15315`, `N_FUZZ = 100_000` (pinned, deterministic). `conformance_check.py`
runs the R/I shadow `hash(field.creation_counter)` against the ORACLE = the real
**gold-patched** `Field.__hash__` (`hash(field)`), on fuzzed fields spanning
several concrete `Field` subclasses. It checks two observables on populations
sized to their cost: (1) shadow == oracle, over the FULL ≥10⁵ fuzzed-field
population (cheap — a bare `hash` call); and (2) the oracle digest is unchanged
across the model-association event (immutability — the F2P scenario), over a
bounded sample `N_ASSOC` of fields, because that leg must build a real Django
model class (`type(name, (models.Model,), …)`), which registers in the app
registry and is orders of magnitude more expensive and super-linear. Folding (2)
into the 10⁵ loop is what timed the gate out previously; the sample size is
logged in the success line, not silently truncated. See `conformance_check.py`.
