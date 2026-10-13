# mapping.md — django__django-14238

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 30e123ed351317b7527f632b3b7dc4e81e850449`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each callee. There are **no consumed axioms** in this bundle, so
G-AX is a skip (§3).

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recognizeType (ancestry : List Nat)` | `AutoFieldMeta.__subclasscheck__(self, subclass)` — `django/db/models/fields/__init__.py:2523` | the modeled changed function (the metaclass subclass-recognition decision) |
| `isFamilyMember (ancestry)` *(deep model — R/I, not an axiom)* | the body of `__subclasscheck__` post-patch: `issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)` (`__init__.py:2524`) | pure spec: a candidate is recognised iff it derives from a recognised base |
| `derivesFrom (ancestry) (baseId)` | Python's `issubclass(subclass, base)` / the `base in subclass.__mro__` structural relation | pure spec: one type derives from another (reflexive, total) |
| `subBaseIds = [1,2]` | `self._subclasses == (BigAutoField, SmallAutoField)` — the `_subclasses` property, `__init__.py:2519-2521` | the two specialised recognised base types |
| `rootBaseId = 0` | `AutoField` itself, the class whose metaclass is `AutoFieldMeta` (the `super().__subclasscheck__` leg recognises genuine subclasses of `AutoField`) | the root recognised base type |

The pre-patch behaviour the change removes (refinement audit only, not in the
consumer spec view): the specialised-base leg was `subclass in self._subclasses`
— **identity** membership of the candidate against the two-element tuple — rather
than `issubclass(subclass, self._subclasses)` — **derivation** from either.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability plan §4 refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a candidate type `subclass` (a Python class object) | `ancestry : List Nat` | `subclass` ↔ `[id(c) for c in subclass.__mro__]`: the candidate's method-resolution order mapped to abstract type-ids, the candidate itself the head. `cls.__mro__` is non-empty (it always lists `cls` then its bases up to `object`), matching `require ancestry ≠ []`. |
| the three recognised base types | the ids `0` (root = `AutoField`), `1`,`2` (`BigAutoField`, `SmallAutoField`) | fixed assignment `AutoField↦0, BigAutoField↦1, SmallAutoField↦2`; every other type gets a fresh distinct id. Only the *identities* of the bases matter, so any injective id assignment is faithful. |
| `issubclass(subclass, base)` (the genuine subclass relation Python computes via the MRO) | `derivesFrom ancestry baseId = ancestry.contains baseId` | `base in subclass.__mro__` ↔ `baseId ∈ ancestry`. Exact: `issubclass(A,B)` is true iff `B` is in `A`'s MRO (for these ordinary classes whose own metaclass is plain `type`; the specialised bases `Big/SmallAutoField` do **not** carry `AutoFieldMeta`, so their `issubclass` uses the genuine relation — verified empirically, mapping.md §3). |
| `issubclass(candidate, AutoField)` (the F2P observable) | `recognizeType ancestry` (a `Bool`) | the metaclass `__subclasscheck__` result ↔ `isFamilyMember ancestry`. |

Lean `List` membership/`any` are total and decidable — no workaround needed; the
carrier is `List Nat` because the operation reads a linearised ancestry of opaque
type identities.

## 3. Callee provenance (no axioms — deep model checked by G-CONF)

The one operation `__subclasscheck__` performs — deciding recognition — is
modeled **deeply** by `isFamilyMember`/`derivesFrom` in the `pure` region. There
is **no axiomatized callee**: `issubclass` and `__mro__` are the language's own
total, pure structural relation over a type's ancestor list, transliterated
directly (`derivesFrom = ancestry.contains`), not assumed behind an `axiom`.
Hence **no `axiom_check.py`; G-AX = skip**.

### 3.1 Why the two `_subclasses` legs are exactly OR-ed (no double-count)
Post-patch: `issubclass(subclass, (BigAutoField, SmallAutoField)) or
super().__subclasscheck__(subclass)`. `issubclass(x, (A,B))` ≡ `issubclass(x,A)
or issubclass(x,B)`, and `super().__subclasscheck__` is `type.__subclasscheck__`
(the genuine relation against `AutoField`). So the result is
`derives(big) ∨ derives(small) ∨ derives(root)` — exactly `isFamilyMember`
(`subBaseIds.any derivesFrom || derivesFrom rootBaseId`). The reflexive case
(a candidate that *is* `BigAutoField`) is subsumed: a type's MRO lists itself, so
`derivesFrom` already returns true — the patch's switch from `in` to `issubclass`
strictly *adds* the proper-descendant cases, never removes the identity ones.

### 3.2 Empirical grounding (recorded, conformance_check.py re-checks)
Verified against the real classes at base_commit: `issubclass(MyBigAutoField,
AutoField)` is `False` pre-patch and `True` post-patch where
`class MyBigAutoField(BigAutoField): pass`; likewise `MySmallAutoField`,
`DeepBig(MyBigAutoField)`. `BigAutoField`/`SmallAutoField`/`AutoField` themselves
are recognised both pre- and post-patch (reflexive case). `IntegerField`,
`Field`, `int`, `object`, and an `IntegerField` subclass are recognised by
neither. `type(BigAutoField)` is plain `type` (only `AutoField` carries
`AutoFieldMeta`), so `issubclass(x, (Big,Small))` uses the genuine MRO relation.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14238`** so the
consumer-side verdict (§11.3) is reproducible. It builds a pool of real django
class hierarchies (the recognised bases, their proper descendants at several
depths — the F2P scenario — unrelated families, and random single/multiple
inheritance mixes), maps each to its abstract `ancestry`, and diffs the R/I
shadow `isFamilyMember(ancestry)` against the real patched `issubclass(candidate,
AutoField)` over the full pool plus ≥10⁵ resamples. There are no A-tagged callees
in the impl region, so the shadow is pure R/I.
