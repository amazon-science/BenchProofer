# refinement.md — django__django-14238

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `recognizeType` `do` block and the deep `isFamilyMember`/`derivesFrom`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — A-consumed / A-reference), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no axioms** in this
bundle (the changed operation is modeled deeply over a free input), so there is
no A leg and no `axiom_check.py` (G-AX skip). Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The recognition site — `AutoFieldMeta.__subclasscheck__` (`django/db/models/fields/__init__.py:2523`)

Gold hunk:
```
  def __subclasscheck__(self, subclass):
-     return subclass in self._subclasses or super().__subclasscheck__(subclass)
+     return issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)
```

| # | Solution.lean impl op (`recognizeType`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `ancestry : List Nat` | `subclass` arg (a Python class) | R | a class ↔ its linearised MRO mapped to abstract type-ids (mapping.md §2). G-CONF bridges via `[id(c) for c in subclass.__mro__]`. |
| A2 | `derivesFrom ancestry b` = `ancestry.contains b` | `issubclass(subclass, base)` for `base ∈ self._subclasses` | I | `issubclass(x, B)` ≡ `B ∈ x.__mro__` (mapping.md §3); concrete list-membership, transliterated 1:1 by G-CONF. **This is the changed op**: the gold switches the per-base test from identity (`x in self._subclasses`, i.e. `x` *is* `B`) to derivation (`issubclass(x, B)`). The model encodes the post-patch derivation directly. |
| A3 | `viaSubBases = subBaseIds.any (fun b => derivesFrom ancestry b)` | `issubclass(subclass, self._subclasses)` where `_subclasses = (BigAutoField, SmallAutoField)` | I + R | `issubclass(x, (A,B))` ≡ `issubclass(x,A) ∨ issubclass(x,B)` (Python tuple semantics) ↔ `subBaseIds.any derivesFrom`; the two-element tuple ↔ `subBaseIds = [1,2]` (R, mapping.md §1, §3.1). |
| A4 | `viaRootBase = derivesFrom ancestry rootBaseId` | `super().__subclasscheck__(subclass)` | I + R | `super()` is `type.__subclasscheck__`, the genuine relation against `AutoField` ↔ `derivesFrom ancestry rootBaseId` (`rootBaseId = 0 ↔ AutoField`, R). Unchanged by the patch; carried through identically. |
| A5 | `return viaSubBases || viaRootBase` | `... or ...` | I | boolean disjunction, identical. |

Discriminating content of the change — a *proper descendant* of a specialised
base (e.g. `class MyBigAutoField(BigAutoField)`) must be recognised — lives in
A2/A3: the model tests `derivesFrom ancestry b` (MRO membership) rather than the
candidate's own identity. The pre-patch `subclass in self._subclasses` tested
identity; `Solution_prepatch.lean` reproduces that (`subBaseIds.contains
ancestry.head!` — head = the candidate itself) and **fails** both
`out = isFamilyMember ancestry` and the derivation-recognition postcondition
(G-DIFF).

## B. No second site

`__subclasscheck__` is the only changed function; `__instancecheck__` (line
2522) is untouched by the gold patch. Single method, single prepatch.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the per-base
recognition test, identity → derivation — is modeled **deeply** (`derivesFrom` =
list membership over the candidate's ancestry, step A2/A3), not hidden behind an
axiom about the function under change. There is **no consumed axiom**: `issubclass`
/ `__mro__` are the language's own total structural relation, transliterated
concretely (I), validated against the real classes by G-CONF (mapping.md §3).

## D. verify(Solution) ⇒ resolved

`recognizeType` verifies only if its output equals `isFamilyMember ancestry` —
recognition by genuine derivation from any of the three recognised bases (A2–A5)
— and satisfies the two derivation-recognition postconditions (a candidate that
derives from a specialised base, or from the root, is recognised). By R
(`class ↔ MRO-ids`, `tuple ↔ subBaseIds`, `AutoField ↔ rootBaseId`) the verified
decision equals `issubclass(subclass, self._subclasses) or
super().__subclasscheck__(subclass)` on the tested classes; by G-CONF the R/I
transliteration agrees with `patch.diff`'s real `issubclass(candidate, AutoField)`
on the full class pool + ≥10⁵ resamples (0 disagreements). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust
point (no axioms).
