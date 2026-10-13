# mapping.md — scikit-learn__scikit-learn-12585

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = bfc4a566423e036fbdc9fb02765fd893e4860c85`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `sklearn/base.py` (the `clone` function).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `copyRoute (isCollection exposesParams isClassObject strict : Bool)` | the branch-dispatch head of `clone(estimator, safe=True)` — `sklearn/base.py:47-58` | the modeled changed function: which arm of the `if/elif/else` ladder a single incoming value takes |
| `route` *(deep model — `pure` region)* | the `if estimator_type in (...) / elif not hasattr(...) or isinstance(estimator, type) / else` decision (`sklearn/base.py:47,51`) | pure spec: the dispatch decision as a total function of three value observations + the strictness flag |
| `Route.mapElements` | `return estimator_type([clone(e, safe=safe) for e in estimator])` (`base.py:49`) | the recognized-collection arm |
| `Route.deepCopy` | `return copy.deepcopy(estimator)` (`base.py:53`) | the not-an-estimator, lenient arm (`safe=False`) |
| `Route.refuse` | `raise TypeError("Cannot clone object ...")` (`base.py:55-58`) | the not-an-estimator, strict arm (`safe=True`) |
| `Route.reconstruct` | `klass = estimator.__class__; new_object_params = estimator.get_params(deep=False); ...; new_object = klass(**new_object_params)` (`base.py:59-73`) | the estimator-reconstruction arm |

The observations the dispatch consults:

| Solution.lean param | repo expression (@ base_commit) | meaning |
|---|---|---|
| `isCollection` | `type(estimator) in (list, tuple, set, frozenset)` (`base.py:48`) | value is one of the four recognized homogeneous collection kinds |
| `exposesParams` | `hasattr(estimator, 'get_params')` (`base.py:51`) | value advertises the estimator parameter interface |
| `isClassObject` | `isinstance(estimator, type)` (`base.py:51`, **added by the patch**) | value is itself a class, not an instance |
| `strict` | the `safe` argument (`base.py:51-56`) | caller demands a configurable object (no deep-copy fallback) |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo objects. A wrong entry surfaces as
spurious G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the incoming `estimator` value, **projected onto the three predicates the dispatch reads** | three `Bool`s `(isCollection, exposesParams, isClassObject)` | `v ↔ (type(v) in (list,tuple,set,frozenset), hasattr(v,'get_params'), isinstance(v,type))`. The dispatch decision depends on the value ONLY through this triple (every other property of `v` is orthogonal to which arm is taken). |
| the `safe` keyword argument (`bool`) | `strict : Bool` | identity |
| the arm taken (`return`/`raise`) | `Route` (4-valued) | `mapElements ↔ the collection-comprehension return`; `deepCopy ↔ copy.deepcopy return`; `refuse ↔ the TypeError raise`; `reconstruct ↔ the get_params/klass(**params) return` |

The model is a **classification** of the value, not the value itself: the
operation the patch changes is exactly the choice of arm, and that choice is a
finite function of the triple + `strict`. The downstream effect of each arm
(recursing into elements, deep-copying, raising, reconstructing) is the
**unchanged** body the patch does not touch; only `deepCopy`'s observable
result on a class object is consulted by the F2P test (see §3).

## 3. Callee provenance

### 3.1 `route` deep model ↔ the real dispatch ladder (G-CONF, R/I)
The changed operation — the dispatch decision — is modeled **deeply** by
`route` in the `pure` region; there is **no consumed axiom** about `clone`. The
post-patch real decision is:

```python
estimator_type = type(estimator)
if estimator_type in (list, tuple, set, frozenset):      # isCollection
    return estimator_type([clone(e, safe=safe) for e in estimator])
elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):
    if not safe:                                          # strict == False
        return copy.deepcopy(estimator)
    else:
        raise TypeError(...)
# else: reconstruct from get_params
```

`route` transliterates this exactly: collection first; then
`(not exposesParams) or isClassObject` → strict ? refuse : deepCopy; else
reconstruct. G-CONF (`conformance_check.py`) builds this shadow and diffs the
arm it picks against the real post-patch `clone` over fuzzed values, ≥10⁵
inputs. This is the R/I leg.

### 3.2 `copy.deepcopy` on a class object ↔ identity (G-AX, A-reference)
The single downstream callee whose **observable result** a reproduced case
depends on is `copy.deepcopy` applied to a class object, taken by the
`deepCopy` arm when a class-valued parameter is cloned with `safe=False` (the
recursive `clone(param, safe=False)` call at `base.py:62`). The F2P test
`test_clone_estimator_types` asserts `clf.empty is clf2.empty` where
`clf.empty` is the class `MyEstimator` — i.e. it requires the `deepCopy` arm to
return **the identical object** for a class. CPython's `copy.deepcopy` returns
classes by identity (they are atomic to `deepcopy` via `_deepcopy_atomic` for
`type`). `axiom_check.py` validates this A-reference: `copy.deepcopy(C) is C`
for class objects across builtins and user classes. This callee is UNCHANGED by
the patch; it is referenced, not consumed as a Lean axiom (the proof does not
assume it — it is a fact G-AX confirms).

`copy.deepcopy` and the reconstruction body (`get_params`, `klass(**params)`,
the sanity loop) on the OTHER arms are unchanged callees the patch does not
touch and the F2P/P2P suite already covers; they are not modeled in Lean.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12585`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`route` (the R/I-tagged decision) to Python and reads each fuzzed value's
`(isCollection, exposesParams, isClassObject)` triple via the §2 bijection.
