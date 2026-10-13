# mapping.md — django__django-13401

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 453967477e3ddae704cd739eac2449c0e13d464c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one opaque callee.

Repo file under change: `django/db/models/fields/__init__.py` (class `Field`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fieldEq (a b : FieldRec)` | `Field.__eq__(self, other)` — `django/db/models/fields/__init__.py:516` | modeled changed function (equality) |
| `fieldLt (a b : FieldRec)` | `Field.__lt__(self, other)` — `django/db/models/fields/__init__.py:522` | modeled changed function (strict order) |
| `fieldHash (a : FieldRec)` | `Field.__hash__(self)` — `django/db/models/fields/__init__.py:528` | modeled changed function (digest) |
| `FieldRec` | a `Field` instance, restricted to the fields the three methods observe | record model (see §2) |
| `IdentityKey` | the tuple `(creation_counter, app_label?, model_name?)` the post-patch `__hash__` digests | record model |
| `keyOf` | the post-patch construction of that tuple inside `__hash__` | pure spec |
| `ownerLt` | the post-patch `(app_label, model_name) < (app_label, model_name)` tuple comparison inside `__lt__` | pure spec |
| `fieldLtSpec` | the full post-patch `__lt__` decision tree | pure spec |
| `pyHash` *(opaque — A-consumed contract)* | CPython builtin `hash(tuple)` over the key tuple (`hash((...))`, `__init__.py:529-533` post-patch) | unchanged builtin digest callee |

The behavioural contrast the issue/F2P demands (`__init__.py` pre-patch):
`__eq__`/`__lt__`/`__hash__` consult only `self.creation_counter`
(`__init__.py:518,524,529`); equal-counter fields from different models compare
equal and collide. (Refinement audit only; not in the consumer spec view.)

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as a
spurious G-CONF disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `Field` instance `f`, as seen by the three methods | `FieldRec` | `f.creation_counter` (an `int`) ↔ `counter : Int`; the **model identity** ↔ `owner : Option (String × String)` |
| `f.creation_counter` | `counter : Int` | identity on `ℤ`; Django assigns it a small non-negative int per `Field.__init__` (`__init__.py:163-166`) |
| the model a field is attached to | `owner : Option (String × String)` | `hasattr(f, 'model')` ↔ `owner.isSome`; when attached, `(f.model._meta.app_label, f.model._meta.model_name)` ↔ `some (app_label, model_name)`; an unattached field (`not hasattr(f,'model')`, i.e. `getattr(f,'model',None) is None`) ↔ `none` |
| a single name component (`app_label` / `model_name`, both `str`) | `String` | a Python identifier `str` ↔ the same `String`; CPython `str.__lt__` is code-point lexicographic, matching Lean `String.<` on the identifier domain (lowercase ASCII letters/digits/underscore — see §3 note) |
| tuple lexicographic `<` on `(app_label, model_name)` | `ownerLt` | Python tuple `<` compares first components, then second; `ownerLt` encodes exactly that |
| `hash((counter, app_label?, model_name?))` (post-patch `__hash__`) | `pyHash (keyOf a)` | `keyOf` builds the same triple (absent components ↔ `None`); `pyHash` is the opaque digest of it (§3.1) |

### Modeling notes (directive-5 frame)
- `fieldEq`/`fieldLt` take `a b : FieldRec` non-`mut`; `fieldHash` takes
  `a : FieldRec` non-`mut`. The Python methods mutate neither operand (they only
  read `creation_counter` / `model._meta`), so no `mut` and no frame obligation
  is owed (SPEC_GUIDE directive 5).
- `getattr(self,'model',None) == getattr(other,'model',None)` in post-patch
  `__eq__`: two model instances compare equal iff they are the same model, which
  the `(app_label, model_name)` identity captures faithfully (two distinct
  concrete model classes have distinct `(app_label, model_name)`; the abstract
  parent vs. its concrete children, the F2P case, have distinct `model_name`).
  Hence `owner` equality ↔ `model` equality on the observed domain.

### `__eq__`/`NotImplemented` (non-`Field` other)
The `isinstance(other, Field)` guard and the `NotImplemented` branch are outside
the modeled domain: `FieldRec` ranges over `Field` instances only. The F2P test
compares fields to fields; the guard is unchanged by the patch (R/identity).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `pyHash` ↔ `hash(tuple)` (A-consumed contract)
**Callee:** CPython builtin `hash` applied to the key tuple, unchanged by the
patch. The post-patch `__hash__` is:

```python
def __hash__(self):
    return hash((
        self.creation_counter,
        self.model._meta.app_label if hasattr(self, 'model') else None,
        self.model._meta.model_name if hasattr(self, 'model') else None,
    ))
```

The spec consumes only one property of this callee: that the digest is a
**function of the key components** — equal keys give equal digests, and (the
property the F2P test observes) the digests of the keys of two fields that
differ in their model identity are not forced equal. `pyHash` is `opaque`
(a genuine total function abstract to the kernel), the weakest contract
sufficient: the proof of `fieldHash` uses only `out = pyHash (keyOf a)`, never
any concrete numeric value (SPEC_GUIDE directive 7 — no pinned exact outputs).

**Soundness check (G-AX):** `axiom_check.py` runs the real
`hash((counter, app_label?, model_name?))` on boundary keys (matching/distinct
counters, `None` vs present model components, the F2P abstract-vs-children
triple) plus randomized fuzz, asserting (a) `pyHash` is a well-defined function
of the key (equal keys ⟹ equal digest) and (b) on the F2P-relevant inputs the
real digests of keys differing only in model identity are unequal — i.e. the
property the test `assertNotEqual(hash(...), hash(...))` requires actually holds
for the real callee. It validates against the real builtin `hash(tuple)` **only**
— it never calls `Field.__hash__` (that is the function under spec / the op the
patch changes; G-AX runs at `base_commit` with no gold applied, where
`Field.__hash__` is still the pre-patch buggy `hash(self.creation_counter)`, so
calling it would be both a directive-7 violation and meaningless). The `keyOf`
*construction* (which tuple is built) is a pure R/I leg, audited by G-CONF (the
hash equal/unequal relation vs key equality, against the patched callee) and
G-EQ. stdlib-only. Exit 0 iff sound.

### 3.2 String order note
The model-name / app-label components are Python identifiers: lowercase ASCII
letters, digits, underscores (`model_name` is `cls.__name__.lower()`;
`app_label` is a Python-identifier app name). On this domain CPython `str.__lt__`
(code-point order) and Lean `String.<` agree, so `ownerLt` is faithful. G-CONF
restricts its fuzz alphabet to this identifier domain (§4) so the bijection is
exercised exactly where the real comparison lives.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13401`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`fieldEq` and `fieldLtSpec`/`ownerLt` (R/I-tagged ops) to Python over real
`Field`-like records and diffs them against `patch.diff`'s behaviour
(`Field.__eq__` / `Field.__lt__` applied at base_commit with the gold patch).
`fieldHash`'s digest is A-tagged (the opaque `pyHash` callee) and is checked by
G-AX, not G-CONF — but G-CONF additionally asserts the *equal/unequal* relation
of the real `hash` agrees with the spec's key-equality relation, since that is
pure-R observable.
