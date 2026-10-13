# mapping.md — django__django-14765

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4e8121e8e42a24acc3565851c9ef50ca8322b15c`, states the type
abstraction, and records the absence of any axiomatized callee.

Repo file under change: `django/db/migrations/state.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_state(real_apps, present, is_expected_kind)` | `ProjectState.__init__(self, models=None, real_apps=None)` — `django/db/migrations/state.py:91` (changed body lines 94-97) | the modeled changed function: it processes the `real_apps` argument and assigns `self.real_apps` |
| `OffKindCollection` | the `AssertionError` raised by `assert isinstance(real_apps, set)` (`state.py:96` post-patch) | the internal-contract violation construction reports for a present off-kind collection. User-defined exception (a builtin exception in an `Exsures` crashes the Nagini translator). |
| `Result()` (the returned `List[int]`) | `self.real_apps` (the stored attribute set at `state.py:95/97` pre-patch, `:98` post-patch) | the collection construction stores |

The pre-patch repo lines the change replaces (for the refinement audit, not
referenced from the consumer spec view):

```python
# state.py:94-97 @ base_commit
if real_apps:
    self.real_apps = real_apps if isinstance(real_apps, set) else set(real_apps)
else:
    self.real_apps = set()
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `real_apps` argument: `None` \| a `set` of app-label `str`s \| any other collection (e.g. a `list`) | `real_apps: List[int]` (label code points) + `present: bool` + `is_expected_kind: bool` | **`present`** ⟺ `real_apps is not None` (the `None` test at `state.py:94/95`); when `not present` the `List[int]` contents are irrelevant (the absent input carries no membership). **`is_expected_kind`** ⟺ `isinstance(real_apps, set)` (the runtime kind test at `state.py:95/96`). The `List[int]` carries the present collection's membership; `str` indexing is banned in Nagini, so labels are code points and the discriminating observable is the OUTCOME (return / raise) and the STORED membership, not the label characters. |
| `self.real_apps` attribute assignment (`set` object) | `Result()` : `List[int]` whose `ToSeq` equals the supplied membership | the post-patch store `self.real_apps = real_apps` is BY REFERENCE (the same set object). The model returns a fresh `List[int]` with identical membership (`ToSeq(Result()) == ToSeq(real_apps)`). Object identity refines to membership equality: the tested behaviour (`StateApps` iterates `self.real_apps`; `__eq__` compares `self.real_apps == other.real_apps`) observes membership, which is preserved. For the absent input the empty set refines to the empty list (`len(Result()) == 0`). |
| `AssertionError` (`assert isinstance(real_apps, set)`) | `Exsures(OffKindCollection, ...)` | the assert fires (raises) exactly when the present collection is not a set, i.e. `present and not is_expected_kind`. Modeled as a user-defined exception (builtin-exception `Exsures` crashes the translator). The F2P test `test_real_apps_non_set` asserts `ProjectState(real_apps=['contenttypes'])` raises `AssertionError`. |

`set(real_apps)` coercion (pre-patch only) refines to copying the membership
into the result `List[int]`; it is a no-op on the *membership* (the model's
abstraction does not track set deduplication, which is irrelevant to the tested
behaviour — the tests pass either already-unique sets or trigger the raise).

## 3. Callee provenance (kind-A) — NONE

This change has **no axiomatized callee** and **no deep-model reference**. The
changed operation is purely Python-level control flow + a runtime type test
(`isinstance(real_apps, set)`) + an `assert`, all of which are modeled directly:
`isinstance` → the `is_expected_kind` boolean, `assert` → the `Exsures` raise
branch, the `set()`/store → the `List[int]` membership. No standard-library or
repo callee is invoked inside the changed operation that Nagini cannot express.

Consequently there is **no `axiom_check.py`** for this bundle (the prompt
requires one only when axioms exist): the `axioms` and `pure` regions are empty,
`meta.json` lists no axioms and no deep-model references, and G-AX has nothing to
check. The whole correctness burden rests on G-VERIFY + G-DIFF (the spec sees the
bug) and G-RESOLVE (the gold patch resolves), plus the R-refinement audit (G-EQ).
