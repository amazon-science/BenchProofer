# refinement.md — django__django-14238

The operation-by-operation correspondence between `model.py`'s implementation
(the `subclass_check` impl region and the deep `is_subtype` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The membership site — `AutoFieldMeta.__subclasscheck__`

Gold hunk (`django/db/models/fields/__init__.py:2526-2527`):
```
 def __subclasscheck__(self, subclass):
-    return subclass in self._subclasses or super().__subclasscheck__(subclass)
+    return issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)
```

| # | model.py impl op (`subclass_check`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `owner`, `base_one`, `base_two`, `candidate : Cls` | `self`, the two entries of `self._subclasses`, and `subclass` | R | a Python class ↔ a `Cls` carrying `cid = id(class)` and `anc = {id(A) for A in class.__mro__}` (mapping.md §2). `self`↔`owner`; `self._subclasses == (BigAutoField, SmallAutoField)` ↔ `(base_one, base_two)`; `subclass`↔`candidate`. |
| A2 | `is_subtype(candidate, base_one)` and `is_subtype(candidate, base_two)` (the two `if … return True` rungs) | `issubclass(subclass, self._subclasses)` (tuple 2nd arg) | A-reference | the changed operation — switching identity-membership to **structural-subtype** membership — is modeled **deeply**: `is_subtype` (the spelled-out MRO-membership in the `pure` region) IS the structural-subtype query. There is no consumed `issubclass` axiom; the proof never depends on a `@ContractOnly`. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the builtin `issubclass`/`type.__subclasscheck__` and asserts `is_subtype == issubclass` on every pair of the replicated class family. CPython tuple semantics: `issubclass(C,(B1,B2)) ⟺ issubclass(C,B1) or issubclass(C,B2)` (mapping.md §3.1), matching the two-rung disjunction. The registered bases carry the default metaclass, so this is the ordinary MRO check `is_subtype` models. |
| A3 | `is_subtype(candidate, owner)` (the final `return`) | `super().__subclasscheck__(subclass)` | A-reference + I | the `super()` call dispatches to `type.__subclasscheck__(self, subclass)`, the ordinary structural check of `subclass` against `self == owner`; `is_subtype(candidate, owner)` models exactly that (mapping.md §3.1). UNCHANGED by the patch (identical between pre- and post-patch), hence also **I** at the source level; modeled deeply, validated by G-AX. |
| A4 | the `if … return True` ladder ending `return is_subtype(candidate, owner)`; postcondition `Result() == (is_subtype(candidate, base_one) or is_subtype(candidate, base_two) or is_subtype(candidate, owner))` | the boolean expression `… or … or …` returned | I | short-circuit boolean `or` over three predicates ↔ the sequential-`return-True` ladder: observationally the same boolean disjunction, which the postcondition pins exactly. |

The discriminating content of the change — **structural-subtype** membership
(`issubclass`) rather than **identity** membership (`in` a tuple) — lives in the
A2 step. The pre-patch `subclass in self._subclasses` is identity membership
(`candidate.cid == base_one.cid or candidate.cid == base_two.cid`);
`model_prepatch.py` reproduces exactly that and **fails** the postcondition
`Result() == (is_subtype(candidate, base_one) or is_subtype(candidate, base_two)
or is_subtype(candidate, owner))`, because for a proper subclass of a registered
base `is_subtype(candidate, base_one)` is `True` while the identity check is
`False` (G-DIFF). That is the spec sensing the change.

## B. No consumed axiom; the changed op is modeled deeply

There is **no `@ContractOnly` axiom** in this bundle (the `axioms` region is
empty). The one operation that genuinely *changed* — the structural-subtype
membership test — is modeled **deeply** by the `@Pure` `is_subtype`
(MRO-membership) consumed in `subclass_check` (step A2), an **A-reference**, not
hidden behind an axiom about the operation under change. `is_subtype` appears
only as the **A-reference** that G-AX validates the deep model against the real
`issubclass` builtin.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The structural-subtype query is fully
expressible in Nagini as a `PSet[int]` membership over the modeled ancestry, so
no operation is hand-waved.

## D. verify(model) ⇒ resolved

`subclass_check` verifies only if its result equals the exact disjunction
`is_subtype(candidate, base_one) or is_subtype(candidate, base_two) or
is_subtype(candidate, owner)` (A4). By R (class ↔ `Cls`, MRO ↔ `anc`) and the
CPython tuple semantics of `issubclass` (A2), the verified decision equals
`issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)`
— the gold post-patch expression. By G-AX the deep model `is_subtype` equals the
real `issubclass`/`type.__subclasscheck__` (A-reference). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep-model reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly those of PLAN §1.1: refinement
fidelity (this document, G-EQ) and deep-model soundness (axiom_check.py, G-AX);
there is no consumed-axiom trust point.
