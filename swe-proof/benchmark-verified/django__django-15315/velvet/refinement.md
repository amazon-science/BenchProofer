# refinement.md — django__django-15315

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`fieldHashMethod` `do` block + the deep `fieldHashKey` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I; no
kind-3 (changed inexpressible op).

There are **NO axioms** in this bundle: the hashing primitive `pyHash` is a free
input (mapping.md §2/§3), so no row is A-consumed or A-reference, and G-AX is
`skip`. The whole impl region is R/I, mechanically refuted by **G-CONF**
(`conformance_check.py`); the narrative below is audited by G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The hash site — `Field.__hash__` (`django/db/models/fields/__init__.py:544`)

Gold hunk (the changed lines):
```
- return hash((
-     self.creation_counter,
-     self.model._meta.app_label if hasattr(self, 'model') else None,
-     self.model._meta.model_name if hasattr(self, 'model') else None,
- ))
+ return hash(self.creation_counter)
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `pyHash : HashKey → Int` (free input) | the builtin `hash(...)` | R | `pyHash` ↔ `hash`; the spec holds for every hashing function (mapping.md §3). G-CONF binds `pyHash := hash`. |
| 2 | `intrinsicId : Int` | `self.creation_counter` | R | the field's assignment-independent intrinsic identity, an `int` set once in `__init__` and never reassigned (mapping.md §2). |
| 3 | `modelAssoc : Option (List Char × List Char)` (read-only, **not** `mut`) | `self.model._meta.app_label / model_name if hasattr(self, 'model') else None` | R | the association metadata the field currently carries; `none ↔ not hasattr(self,'model')`. Read-only: the post-patch `__hash__` does NOT consult it (directive 5). |
| 4 | `fieldHashKey intrinsicId = HashKey.solo intrinsicId` | the key `self.creation_counter` handed to `hash` | I | the post-patch key is the intrinsic identity ALONE; `solo intrinsicId` is that key, transliterated by G-CONF as the bare `creation_counter`. |
| 5 | `return pyHash (fieldHashKey intrinsicId)` | `return hash(self.creation_counter)` | R + I | the returned digest. By R (rows 1–2) and I (row 4) this is exactly the gold expression. |

### Why the spec sees the bug (G-DIFF)

The frozen postconditions pin the digest to the intrinsic identity alone and
state it is independent of the association:

```
ensures out = pyHash (fieldHashKey intrinsicId)
ensures out = pyHash (fieldKeyAt intrinsicId modelAssoc)
ensures ∀ a, out = pyHash (fieldKeyAt intrinsicId a)
```

`Solution_prepatch.lean` keeps this byte-identical spec but reproduces the
PRE-patch skeleton — it returns `pyHash (HashKey.composite intrinsicId
modelAssoc)`, i.e. it folds the association metadata into the key (the tuple
`(creation_counter, app_label, model_name)`). Because `pyHash` is a free
function, `pyHash (HashKey.composite …)` cannot be proved equal to `pyHash
(HashKey.solo …)`, nor independent of `modelAssoc`: all three postconditions
become unprovable and `prove_correct` fails. That is precisely the bug — a hash
that varies with model association — the issue reports and `test_hash_immutability`
catches. (`Solution_prepatch.lean` fails on `ensures_1/2/3` — verified.)

### Why the modeled observable resolves the F2P test

`test_hash_immutability` hashes a field, assigns it to a model class, and asserts
the hash is unchanged. Under the bijection (mapping.md §2) the modeled
`∀ a, out = pyHash (fieldKeyAt intrinsicId a)` is exactly "the digest is the same
for every association state", and `out = pyHash (fieldHashKey intrinsicId)` ties
it to `hash(creation_counter)` — what the gold patch computes. G-CONF confirms
the real patched `Field.__hash__` (a) equals `hash(creation_counter)` on the
full ≥10⁵ fuzzed-field population (the cheap R/I-fidelity leg) and (b) is
unchanged across the model-assignment event on a bounded sample of fields (the
expensive leg that must build a real model class — the sample size is logged,
not silently truncated). See `conformance_check.py`'s performance note.

## No kind-3

The one changed op — which key is hashed — is fully expressible (`HashKey` +
`fieldHashKey`). Nothing inexpressible; no BLOCKED.
