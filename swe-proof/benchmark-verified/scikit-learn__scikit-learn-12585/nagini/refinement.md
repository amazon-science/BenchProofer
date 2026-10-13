# refinement.md — scikit-learn__scikit-learn-12585

The operation-by-operation correspondence between `model.py`'s implementation
(the `reproduce` impl region and the deep `is_leaf` predicate) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses the axiom's `Ensures`,
**A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The dispatch site — `clone()` (`sklearn/base.py:47-57`)

Gold hunk:
```
     if estimator_type in (list, tuple, set, frozenset):
         return estimator_type([clone(e, safe=safe) for e in estimator])
-    elif not hasattr(estimator, 'get_params'):
+    elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):
         if not safe:
             return copy.deepcopy(estimator)
         else:
             raise TypeError(...)
     klass = estimator.__class__
     new_object_params = estimator.get_params(deep=False)
     ... reconstruct fresh object ...
```

| # | model.py impl op (`reproduce`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `est: Candidate` (three boolean predicates) | `estimator` argument of `clone` | R | the object ↔ its three dispatch-relevant predicates; `clone`'s dispatch reads only `type(estimator) in (...)`, `hasattr(estimator,'get_params')`, `isinstance(estimator,type)` (mapping.md §1-2). |
| A2 | `permit_fallback` | the `safe` kwarg, used as `if not safe:` | R | renaming bijection `permit_fallback ⇔ not safe` (mapping.md §1): the enabling condition for the atomic-copy fallback. |
| A3 | precondition `est.is_aggregate is False` | the `if estimator_type in (list,tuple,set,frozenset):` branch is taken first; the modeled routine specifies the **non-aggregate** path the recursive `clone(param, safe=False)` call lands on for the tested type parameter | R | the F2P parameter is a class (not an aggregate), so it reaches the `elif`; the aggregate branch is a separate, unchanged concern, excluded by the precondition. |
| A4 | `is_leaf(est) == (not est.has_introspect) or est.is_class_object` | `not hasattr(estimator,'get_params') or isinstance(estimator, type)` | **A-reference** | the changed dispatch predicate is modeled **deeply** (spelled out in the `pure` region), NOT hidden behind an axiom about `clone`. `not has_introspect ⇔ not hasattr(...,'get_params')`; `is_class_object ⇔ isinstance(...,type)`. The deep model is validated == the real predicate ingredients by axiom_check.py (G-AX), which runs `hasattr`/`isinstance` on instances, classes, aggregates and non-estimators. No `@ContractOnly` is consumed. |
| A5 | leaf + `not permit_fallback` ⇒ `raise NotCloneableError()` | leaf + `safe=True` ⇒ `raise TypeError(...)` | R + I | `NotCloneableError` stands in for the builtin `TypeError` (builtin-exception `Exsures` crashes Nagini; mapping.md §1). The guard and raise are the identical control flow. |
| A6 | leaf branch ⇒ `copy.deepcopy` modeled per-disjunct: a **class-object** leaf + `permit_fallback` ⇒ `return est` (reference-identity); a **non-class** leaf + `permit_fallback` ⇒ allocate a fresh `Candidate` (distinct object) | leaf + `not safe` ⇒ `return copy.deepcopy(estimator)` | **A-reference** | `copy.deepcopy` dispatches per object kind (CPython `copy.py`; mapping.md §3.2). For a **class object** it is atomic — `copy.deepcopy(cls) is cls` — so the class-leaf return is modeled identity-preserving, and the postcondition's identity clause is **scoped to `est.is_class_object`** (`Implies(is_leaf(est) and permit_fallback and est.is_class_object, Result() is est)`). For a **non-class state-bearing** leaf (numpy array, sparse matrix, plain object — all in-domain since the only precondition is `is_aggregate is False`) `copy.deepcopy` returns a **distinct** object, so the model allocates a fresh `Candidate` and asserts NO identity for that case. axiom_check.py asserts `copy.deepcopy(cls) is cls` for class objects (the only disjunct the identity guarantee covers) and asserts `copy.deepcopy(obj) is not obj` for non-class state-bearing leaves (confirming distinctness is the faithful non-class behaviour). |
| A7 | not-a-leaf ⇒ allocate a fresh `Candidate`, `return rebuilt` (`Result() is not est`) | `klass = estimator.__class__; new_object_params = estimator.get_params(...); ...; new_object = klass(**new_object_params); return new_object` | R | the reconstruction yields a brand-new object — distinct identity from the input. The fresh allocation models the distinct-identity outcome; the reconstructed field values are unchanged by this patch and unobserved by the tested behaviour. |
| A8 | `Requires(MustTerminate(2))` on `reproduce` (and `MustTerminate(1)` on the `Candidate` constructor it calls) | `clone()` is a bounded dispatch that always returns (or raises) — it contains no loop over unbounded state on the non-aggregate path; the F2P/P2P tests observe its RESULT, so a `clone` that never returns hangs the test run (harness timeout, NOT resolved) | R | total-correctness obligation. Added after the G-PANEL-1 audit exhibited a same-spec impl that computed every value correctly but diverged before returning (its faithful real patch — `while True: pass` inserted into `clone` — applied cleanly and hung the F2P test to the harness timeout, so it did NOT resolve, while the partial-correctness spec verified it). With the obligation, any loop without a decreasing `MustTerminate` measure leaks the obligation and is rejected. |

## B. The discriminating content

The single behavioural change the patch makes is the **added `or isinstance(
estimator, type)` disjunct** in the leaf guard (A4). It is captured by the
`is_class_object` disjunct of `is_leaf`:

- `model.py` impl uses `(not est.has_introspect) or est.is_class_object`;
- `model_prepatch.py` impl uses the pre-patch guard `not est.has_introspect`
  (the byte-identical spec is unchanged).

For a **class object that exposes the capability** (`has_introspect=True,
is_class_object=True`), the spec's `is_leaf(est)` is `True`, so the frozen
contract demands:
- with `permit_fallback=False`: the routine **refuses** (Exsures), i.e. it must
  NOT return normally (`Implies(is_leaf(est), permit_fallback is True)`);
- with `permit_fallback=True`: the result is **identity-preserved**
  (`Implies(is_leaf(est) and permit_fallback and est.is_class_object,
  Result() is est)` — the identity clause is scoped to the class-object leaf;
  see A6).

A **non-class leaf** (`has_introspect=False`) is also a spec-side leaf, so the
same refusal clause applies (`Implies(is_leaf(est), permit_fallback is True)`),
but the contract asserts NO identity for it — faithful to `copy.deepcopy`
returning a distinct object for state-bearing non-class leaves (arrays, sparse
matrices, plain objects). The discriminating clause that kills the prepatch
(below) is `Implies(is_leaf(est), permit_fallback is True)`, which is
independent of the scoping of the identity clause.

The pre-patch impl evaluates `not has_introspect == False` and falls through to
the reconstruction branch, which returns normally with a **distinct** object —
violating the `Implies(is_leaf(est), permit_fallback is True)` postcondition
(it returned normally on a leaf regardless of `permit_fallback`) and, on the
`permit_fallback=True` case, the `Result() is est` clause. `model_prepatch.py`
therefore FAILS exactly here (G-DIFF). This mirrors the real bug: pre-patch the
class is mis-routed to `estimator.get_params(deep=False)`, which raises
`TypeError` (unbound method) — precisely the failure in the issue.

## C. No kind-3 (unexpressible-changed-op) steps
Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the leaf dispatch predicate — is modeled **deeply** (`is_leaf`,
step A4, an A-reference validated by G-AX), not hidden behind an axiom about the
function under change. There is no consumed `@ContractOnly` axiom (mapping.md
§4); the only library facts the patch leans on — `hasattr`/`isinstance`
classification and `copy.deepcopy`-of-a-class reference-identity — are
A-reference evidence checked by axiom_check.py.

## D. verify(model) ⇒ resolved
`reproduce` verifies only if (i) a leaf reached normally implies the fallback
was permitted (A5), (ii) a permitted-fallback **class-object** leaf returns the
SAME reference (A6, identity clause scoped to `is_class_object`), (iii) a
non-leaf returns a DISTINCT object (A7), and (iv) the routine actually
TERMINATES and delivers that result (A8, `MustTerminate` — a diverging impl
whose faithful patch hangs `clone()` and the F2P test is rejected, closing the
verified-but-not-resolved gap the G-PANEL-1 audit exhibited). A non-class leaf is faithfully left
identity-unconstrained (A6) — modeling `copy.deepcopy` returning a distinct
object for state-bearing non-class leaves; this is why the spec is faithful to
gold on the **entire** in-domain leaf set (the only precondition is
`is_aggregate is False`), not just the class-object representative the F2P test
exercises. By R (object ↔ predicates; `permit_fallback ⇔ not safe`) and the
A-reference facts (`is_leaf` ⇔ the real guard ingredients;
`copy.deepcopy(cls) is cls` for a class, distinctness otherwise), the verified
routine is the gold-patched `clone` dispatch: a class parameter is reclassified
as a leaf and reproduced reference-identically, so `clone(clf).empty is
clf.empty` holds — exactly what the F2P test `test_clone_estimator_types`
asserts. The P2P clone tests (instances reconstructed to distinct objects;
empty-array / sparse leaves deep-copied to value-equal distinct objects;
non-estimators raising under `safe=True`) are preserved by A5/A6/A7. The gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness — here the A-reference facts validated by G-AX — and refinement
fidelity (this document, G-EQ).
