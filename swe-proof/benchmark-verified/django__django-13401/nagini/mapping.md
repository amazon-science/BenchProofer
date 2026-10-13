# mapping.md — django__django-13401

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 453967477e3ddae704cd739eac2449c0e13d464c`, states the type
abstraction, and gives the provenance of each A-reference (the native Python
operations the deep models are validated against).

Repo file under change: `django/db/models/fields/__init__.py` (class `Field`,
decorated `@total_ordering`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Attr` (class) | `Field` — `django/db/models/fields/__init__.py:85` | the object carrying the modeled comparison/hash behavior; only the touched fields are modeled |
| `Attr.rank` | `Field.creation_counter` (int; set at `__init__.py:163/166`) | integer creation rank |
| `Attr.owned` | `hasattr(self, 'model')` (the `model` attr is set in `Field.contribute_to_class`, `__init__.py:763`) | whether the field has an owning model class |
| `Attr.okey` | the owner identity `(self.model._meta.app_label, self.model._meta.model_name)` flattened to code points | owning-container identity |
| `attr_eq(self_, other)` | `Field.__eq__` — `__init__.py:516` | modeled changed function (equality) |
| `attr_lt(self_, other)` | `Field.__lt__` — `__init__.py:522` | modeled changed function (strict order) |
| `attr_hash_key(self_)` | the KEY built by `Field.__hash__` — `__init__.py:528` | modeled changed function (hash key) |
| `eq_ref` / `same_owner` | the post-patch `__eq__` boolean | pure spec reference for equality |
| `lt_ref` / `lex_lt` | the post-patch `__lt__` boolean (incl. its `(app_label, model_name)` tuple compare) | pure spec reference for the order |
| `hash_ref` | the tuple `(creation_counter, app_label_or_None, model_name_or_None)` the gold `__hash__` hashes | pure spec reference for the hash key |

The pre-patch repo behavior the change removes (for the refinement audit; not
referenced from the consumer spec view): `__eq__`, `__lt__`, `__hash__` each
considered ONLY `self.creation_counter` (`__init__.py:519,525,529`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Field` instance | `Attr` instance (only `rank`, `owned`, `okey` modeled) | the three modeled fields; all other `Field` state is untouched by the change and omitted |
| `self.creation_counter` (`int`) | `Attr.rank` (`int`) | identity |
| `hasattr(self, 'model')` (`bool`) | `Attr.owned` (`bool`) | `True` iff the field has been attached to a model (`contribute_to_class` ran) |
| `getattr(self, 'model', None)` — a model CLASS, compared by identity | the owner identity pair `(app_label, model_name)` | a model is identified by its `(app_label, model_name)`; two distinct models have distinct pairs (Django enforces unique `(app_label, model_name)` per model). Both `__lt__` (tuple tie-break) and `__hash__` (key) already treat the model THROUGH this pair, so equality-by-pair is the faithful abstraction for the tested behavior. |
| `(app_label, model_name)` tuple (two `str`s) | `Attr.okey`: `PSeq[int]` = `label_codepoints ++ [0] ++ name_codepoints` | the NUL separator `0` lies below every identifier code point and never occurs in an identifier, so lexicographic order on the flattened key equals native tuple order on the pair (validated by axiom_check.py §A-reference 2) |
| `str` (label, name) | `List[int]` / `PSeq[int]` of code points | `str` indexing is banned in Nagini; the carrier is code points |
| `hash(key_tuple)` (builtin) | the KEY itself (`PSeq[int]`); hashing is the unchanged callee | the operation under change is WHICH identity flows into the hash, not the hashing. `attr_hash_key` returns the key; the builtin `hash` is the unchanged A-reference (§3.3). |

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**: equality, the order, and the
hash key are modeled deeply over the attributes' own fields. The deep models are
validated == the native Python operations the gold patch invokes.

### 3.1 `eq_ref` / `same_owner` ↔ the patched `__eq__` (A-reference)
Gold `__eq__` (post-patch, `__init__.py:516`):
```python
if isinstance(other, Field):
    return (self.creation_counter == other.creation_counter and
            getattr(self, 'model', None) == getattr(other, 'model', None))
```
`eq_ref` encodes exactly this: `rank == rank` AND `same_owner` (both ownerless,
or both own an equal identity pair). `getattr(self,'model',None)` equality is
modeled by the owner pair: two ownerless fields are equal (`None == None`); a
field with an owner is never equal to one without; two owned fields are equal
iff their `(app_label, model_name)` agree. axiom_check.py runs the native
`getattr`-equality decision and asserts `eq_ref` matches on the F2P scenario +
boundary + 40k fuzz pairs.

### 3.2 `lt_ref` / `lex_lt` ↔ the patched `__lt__` (A-reference)
Gold `__lt__` (post-patch, `__init__.py:522`):
```python
if (self.creation_counter != other.creation_counter or
        not hasattr(self, 'model') and not hasattr(other, 'model')):
    return self.creation_counter < other.creation_counter
elif hasattr(self, 'model') != hasattr(other, 'model'):
    return not hasattr(self, 'model')   # order no-model fields first
else:
    return ((self.model._meta.app_label, self.model._meta.model_name) <
            (other.model._meta.app_label, other.model._meta.model_name))
```
`lt_ref` mirrors this branch-for-branch. The tuple comparison `(app_label,
model_name) < (...)` is modeled as `lex_lt` on the flattened `okey`; axiom_check.py
§A-reference 2 asserts the flattened-key lex order equals the native tuple order
(and `lt_ref` equals the whole native `__lt__` decision) over boundary + 40k fuzz.

### 3.3 `hash_ref` ↔ the patched `__hash__` key + builtin `hash` (A-reference)
Gold `__hash__` (post-patch, `__init__.py:528`):
```python
return hash((
    self.creation_counter,
    self.model._meta.app_label if hasattr(self, 'model') else None,
    self.model._meta.model_name if hasattr(self, 'model') else None,
))
```
The changed operation is the KEY fed to `hash`: it now carries the owner
identity, not the rank alone. `hash_ref` is that key (rank, an ownership flag,
then the identity key when owned), modeled so two attributes differing in owner
produce DISTINCT keys. The builtin `hash` is the unchanged callee; axiom_check.py
asserts (a) `hash_ref` is distinct iff the gold's key tuple is distinct, and
(b) on EQUAL-rank distinct keys (the de-duplication scenario the issue is about)
the builtin `hash` separates them. **Soundness note (recorded for G-AX):** we do
NOT claim universal builtin-hash injectivity — `hash(-1) == hash(-2) == -2`
(CPython's `-1` error-sentinel quirk) collides distinct *ranks*; that is
irrelevant to the equal-rank de-dup the fix targets, so the check is restricted
to equal-rank pairs. Docs: CPython `Objects/tupleobject.c` tuplehash; the `-1`
quirk is `Objects/longobject.c` (`hash(-1)` returns `-2`).
