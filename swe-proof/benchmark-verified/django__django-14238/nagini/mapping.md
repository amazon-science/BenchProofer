# mapping.md — django__django-14238

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 30e123ed351317b7527f632b3b7dc4e81e850449`, states the type
abstraction, and gives the provenance of the deep-model reference (the
structural-subtype query) the bundle validates against the real callee.

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `subclass_check(owner, base_one, base_two, candidate)` | `AutoFieldMeta.__subclasscheck__(self, subclass)` — `django/db/models/fields/__init__.py:2526` | the modeled changed function (metaclass structural-subtype membership test) |
| `owner` (param) | `self` — the class the metaclass is attached to, i.e. `AutoField` (`django/db/models/fields/__init__.py:2530`) | the attached type; the `super().__subclasscheck__` leg checks subtype-of-`owner` |
| `base_one`, `base_two` (params) | the two entries of `AutoFieldMeta._subclasses`, namely `BigAutoField` (`:2539`) and `SmallAutoField` (`:2548`) | the registered "generated-key" base classes (`_subclasses` property body `:2520-2521`) |
| `candidate` (param) | `subclass` — the class being tested | the class whose membership is queried |
| `is_subtype(sub, base)` *(deep model — A-reference)* | the builtin `issubclass(subclass, base)` / `type.__subclasscheck__(base, subclass)` invoked by `issubclass(subclass, self._subclasses)` post-patch | pure spec: the ordinary structural-subtype query (MRO membership), modeled deeply; validated `is_subtype == issubclass` by axiom_check.py (G-AX), NOT consumed as a `@ContractOnly` axiom |
| `Cls(cid, anc)` | a Python class object | model carrier: a class abstracted by its identity (`cid`) and the set of identities of all classes it derives from (`anc`, its MRO) |

The pre-patch repo operation the change replaces (for the refinement audit, not
referenced from the consumer spec view): `subclass in self._subclasses`
(`django/db/models/fields/__init__.py:2527`), an identity/equality-membership
test against the fixed 2-tuple, becomes `issubclass(subclass, self._subclasses)`
(structural-subtype membership).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a Python class object | `Cls` with fields `cid: int`, `anc: PSet[int]` | a class `C` ↔ a `Cls` whose `cid == id(C)` and whose `anc == {id(A) for A in C.__mro__}`. Equality of classes ↔ equality of `cid`. |
| `issubclass(C, B)` / ordinary `type.__subclasscheck__(B, C)` | `is_subtype(c, b) == (b.cid in c.anc)` | `B` is in `C`'s MRO ⟺ `id(B) ∈ anc(C)`. The MRO always contains `C` itself, so the relation is reflexive — encoded by the `Cls` constructor's `cid in anc` requirement. |
| `subclass in self._subclasses` (pre-patch identity membership) | `candidate.cid == base_one.cid or candidate.cid == base_two.cid` | `C is B` ⟺ `id(C) == id(B)` ⟺ `cid` equality. (Modeled in `model_prepatch.py`.) |
| `issubclass(subclass, self._subclasses)` (post-patch, tuple 2nd arg) | `is_subtype(candidate, base_one) or is_subtype(candidate, base_two)` | `issubclass(C, (B1,B2))` ⟺ `issubclass(C,B1) or issubclass(C,B2)` (CPython tuple semantics). |
| `super().__subclasscheck__(subclass)` (the `type` leg) | `is_subtype(candidate, owner)` | the ordinary structural check of `candidate` against the attached type `owner` (`type.__subclasscheck__(owner, candidate)`). |
| boolean `or` short-circuit, `return` of the disjunction | the `if … return True` ladder ending in `return is_subtype(candidate, owner)` | observationally identical to the boolean disjunction (the postcondition pins the exact disjunction). |

`BigAutoField` and `SmallAutoField` carry the *default* `type` metaclass (not
`AutoFieldMeta`), so `issubclass(subclass, BigAutoField)` /
`issubclass(subclass, SmallAutoField)` use the ordinary MRO check — exactly what
`is_subtype` models. Only `AutoField` (the `owner`) carries the overriding
metaclass, and only its `super().__subclasscheck__` leg is the ordinary check
against `owner`, again modeled by `is_subtype`.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `is_subtype` deep model ↔ `issubclass` (A-reference)
**Callee:** the Python builtin `issubclass` (equivalently `type.__subclasscheck__`
on a class with the default metaclass). There is **no `@ContractOnly` axiom**:
the structural-subtype query the membership test consults is modeled **deeply**
by the `@Pure` helper `is_subtype` (MRO-membership), and validated equal to the
real builtin out-of-band by axiom_check.py.

`issubclass(C, B)` returns `True` iff `B` appears in `C`'s method-resolution
order (`C.__mro__`) — the reflexive-transitive inheritance closure. Modeling a
class by the set of identities of its MRO and testing `id(B) ∈ anc(C)` is
exactly that relation. Docs:
https://docs.python.org/3/library/functions.html#issubclass and the C-level
`type.__subclasscheck__` (Objects/abstract.c `recursive_issubclass`).

**The discriminating content of the change:** a class `C` that *derives from*
`BigAutoField`/`SmallAutoField` without being one of those exact classes
(e.g. a user-defined `MyBigAutoField(BigAutoField)`) has
`id(BigAutoField) ∈ anc(C)` (so `is_subtype(C, BigAutoField)` is `True`) yet
`id(C) ≠ id(BigAutoField)` and `id(C) ≠ id(SmallAutoField)` (so the pre-patch
identity membership `C in (BigAutoField, SmallAutoField)` is `False`), and
`id(AutoField) ∉ anc(C)` (so the `super()` leg is also `False`). Post-patch the
disjunction is `True`; pre-patch it is `False`. This is the single behavioral
change the F2P tests observe (`issubclass(MyBigAutoField, AutoField)` must be
`True`; a model whose `DEFAULT_AUTO_FIELD` is a `BigAutoField` subclass must get
that pk class via `Options._get_default_pk_class`'s `issubclass(pk_class,
AutoField)` guard at `django/db/models/options.py:245`).

**Soundness check (G-AX):** `axiom_check.py` builds a structural replica of the
class family (an attached `owner` type with a metaclass whose `_subclasses` is a
2-tuple of registered bases, plus user-defined subclasses, grandchildren,
unrelated classes, and owner-subclasses) and asserts, on every ordered pair of
the 17-class universe, that the deep model `is_subtype` equals the real ordinary
`type.__subclasscheck__`; that the modeled decision `subclass_check` equals the
real metaclass decision `issubclass(cand, (b1,b2)) or
super().__subclasscheck__(cand)`; that every F2P subclass scenario decides
`True` and every non-member decides `False`; and that the pre-patch identity
check would (buggily) reject the user subclass. When Django is importable (it is
in the evaluation container) it additionally validates against the real
`AutoFieldMeta` / `BigAutoField` / `SmallAutoField` / `AutoField`. Imports only
the standard library (the class machinery / `issubclass` builtin the gold patch
relies on). Exit 0 iff sound.
