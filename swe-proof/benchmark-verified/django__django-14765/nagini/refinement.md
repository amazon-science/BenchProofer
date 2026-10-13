# refinement.md — django__django-14765

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_state` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** /
**A-reference**), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The construction site — `ProjectState.__init__` (`django/db/migrations/state.py:91`)

Gold hunk (body lines 94-97 → 94-98):
```
- if real_apps:
-     self.real_apps = real_apps if isinstance(real_apps, set) else set(real_apps)
- else:
-     self.real_apps = set()
+ if real_apps is None:
+     real_apps = set()
+ else:
+     assert isinstance(real_apps, set)
+ self.real_apps = real_apps
```

| # | model.py impl op (`build_state`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `real_apps: List[int]`, `present: bool`, `is_expected_kind: bool` | the `real_apps` argument (`None` \| `set` \| other collection) | R | `present` ⟺ `real_apps is not None`; `is_expected_kind` ⟺ `isinstance(real_apps, set)`; the `List[int]` carries the present collection's membership (mapping.md §2). `str` labels → code points (Nagini bans `str` indexing). |
| A2 | `if not present:` → return the empty `List[int]` | `if real_apps is None: real_apps = set()` then `self.real_apps = real_apps` (the empty set) | R + I | the `is None` test is `not present` (R); the absent input yields the empty stored collection — empty set ↔ empty list, `len(Result()) == 0` (R on the carrier; I on the control flow). |
| A3 | `if not is_expected_kind: raise OffKindCollection()` | `else: assert isinstance(real_apps, set)` (raises `AssertionError` when false) | R + I | the `else` branch is reached exactly when `real_apps is not None` (present); `assert isinstance(real_apps, set)` raises iff `not is_expected_kind`. The `AssertionError` refines to the user-defined `OffKindCollection` (R on the exception type; mapping.md §2 — a builtin exception in an `Exsures` crashes the translator). The control flow (test then raise) is identical (I). |
| A4 | present-and-expected: copy the supplied membership into `result` and return it (`ToSeq(Result()) == ToSeq(real_apps)`) | the fall-through `self.real_apps = real_apps` storing the supplied set | R | the real store is BY REFERENCE (same set object); the model returns a fresh `List[int]` with identical membership. Object identity refines to membership equality — the tested behaviour (`StateApps` iterating `self.real_apps`, `ProjectState.__eq__` comparing `self.real_apps`) observes membership only, which is preserved unchanged (no coercion). (mapping.md §2.) |

The discriminating content of the change — a present collection that is NOT a
set must FAIL rather than be silently coerced — lives in step A3
(`not is_expected_kind ⇒ raise`) and the normal-return clause
`Ensures((not present) or is_expected_kind)`. The pre-patch
(`if real_apps: self.real_apps = … set(real_apps)`) accepts and coerces a
present, non-empty, non-set collection (returning normally);
`model_prepatch.py` reproduces that (`if present and len > 0: copy-and-return`)
and **fails** the postcondition `(not present) or is_expected_kind`, which is
exactly the spec sensing the change (G-DIFF). This is precisely the F2P test
`test_real_apps_non_set`: `ProjectState(real_apps=['contenttypes'])` (present,
non-empty, not a set) must raise `AssertionError`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The changed operation is purely Python-level control
flow + a runtime type test + an `assert`; none of it calls a library/repo callee
Nagini cannot express:

- `isinstance(real_apps, set)` is modeled directly as the boolean
  `is_expected_kind` (R), not axiomatized — it is part of the changed decision,
  so axiomatizing it would be modeling the thing under change. It is a pure
  abstraction of the runtime kind test, not an opaque callee.
- `assert isinstance(...)` → the `Exsures(OffKindCollection, …)` raise branch
  (R on the exception type, I on the control flow).
- `set()` / `set(real_apps)` / `self.real_apps = …` → the `List[int]` membership
  store (R on the carrier).

There is therefore **no consumed axiom (A-consumed)** and **no deep-model
reference (A-reference)**: the `axioms` and `pure` regions are empty, and there
is no `axiom_check.py`. G-AX has nothing to check for this bundle.

## C. verify(model) ⇒ resolved

`build_state` verifies only if (1) it returns normally exactly for an absent or
expected-kind collection (`Ensures((not present) or is_expected_kind)`, A3), (2)
a present off-kind collection raises (`Exsures(OffKindCollection, present and
not is_expected_kind)`, A3), and (3) the stored membership is empty when absent
and equal to the supplied membership when present-and-expected (A2, A4). By the
R-refinements above (`present` ↔ `real_apps is not None`, `is_expected_kind` ↔
`isinstance(real_apps, set)`, `OffKindCollection` ↔ `AssertionError`, membership
↔ the stored set), the verified construction is exactly the gold patch on the
tested inputs:

- absent (`ProjectState()`) ⇒ empty `self.real_apps` (P2P);
- present set (`ProjectState(real_apps={'contenttypes'})`) ⇒ `self.real_apps`
  is that set, membership preserved (P2P);
- present non-set (`ProjectState(real_apps=['contenttypes'])`) ⇒ `AssertionError`
  (F2P `test_real_apps_non_set`).

The gold patch resolves (G-RESOLVE). The only trust point is refinement fidelity
(this document, G-EQ); there is no axiom-soundness trust point because there is
no axiom.
