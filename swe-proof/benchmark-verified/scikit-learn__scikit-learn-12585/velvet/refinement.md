# refinement.md — scikit-learn__scikit-learn-12585

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `copyRoute` `do` block and the deep `route` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized /
deep-modeled callee — **A-consumed** where the proof uses an axiom's `ensures`,
**A-reference** where a deep model / callee is validated `== the real callee` by
G-AX), or **I** (identical concrete op). No kind-3 (changed inexpressible op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The dispatch site — `clone(estimator, safe=True)` (`sklearn/base.py:47-58`)

Gold hunk:
```
-    elif not hasattr(estimator, 'get_params'):
+    elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):
```

| # | Solution.lean impl op (`copyRoute`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `isCollection exposesParams isClassObject strict : Bool` | the incoming `estimator` value + the `safe` flag | R | the dispatch decision depends on `estimator` ONLY through the triple `(type(v) in (list,tuple,set,frozenset), hasattr(v,'get_params'), isinstance(v,type))` and on `safe` directly (mapping.md §2). G-CONF reads the triple off each fuzzed real value. |
| A2 | `if isCollection then return Route.mapElements` | `if estimator_type in (list, tuple, set, frozenset): return ...` | I | the collection arm is unchanged by the patch; transliterated identically. The element recursion inside it is the unchanged body the patch does not touch. |
| A3 | `nonConfigurable := (!exposesParams) \|\| isClassObject` | `not hasattr(estimator, 'get_params') or isinstance(estimator, type)` | I | **the changed predicate, modeled identically.** `!exposesParams ↔ not hasattr(...,'get_params')`; `isClassObject ↔ isinstance(estimator, type)`; `\|\|` ↔ `or`. This is the one operation the patch changes, transliterated op-for-op (no axiom over `clone`). |
| A4 | `if nonConfigurable then (if strict then Route.refuse else Route.deepCopy)` | `if not safe: return copy.deepcopy(estimator) else: raise TypeError(...)` | I + A-reference | the strict/lenient split is unchanged and transliterated (I). The `deepCopy` arm's observable result on a class object — `copy.deepcopy(C) is C` — is the **A-reference** (mapping.md §3.2): `copy.deepcopy` is unchanged, returns classes by identity, validated by G-AX. The F2P `assert clf.empty is clf2.empty` depends on exactly this. |
| A5 | `else return Route.reconstruct` | the `klass = estimator.__class__; new_object_params = estimator.get_params(...)` reconstruction (`base.py:59-73`) | I | the estimator-reconstruction arm, unchanged by the patch; reached only when the value is a genuine parameter-exposing instance. Its body (`get_params`, `klass(**params)`, sanity loop) is the unchanged callee the P2P suite covers. |

Discriminating content of the change — a value that **exposes `get_params` but
is a class object** (`exposesParams = true`, `isClassObject = true`) must route
to `deepCopy`/`refuse`, NOT `reconstruct`. This lives in A3's `|| isClassObject`
disjunct. The pre-patch decision had only `!exposesParams`, so such a value fell
to `reconstruct` and crashed (`get_params() missing 1 required positional
argument: 'self'`). `Solution_prepatch.lean` reproduces that
(`nonConfigurable := !exposesParams`) and **fails** the postcondition
`out = route ...` precisely on the clause `isClassObject = true ⊢
Route.reconstruct = if strict then refuse else deepCopy` (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is I (or R for the carrier projection, A-reference for the one
consulted downstream callee). The operation that genuinely *changed* — the
dispatch predicate — is modeled **identically** (A3), not hidden behind an axiom
about the function under change. There is **no consumed axiom**; the only
audited callee, `copy.deepcopy` on a class (A4, A-reference), is UNCHANGED and
checked `== identity` by G-AX.

## C. verify(Solution) ⇒ resolved

`copyRoute` verifies only if its returned `Route` equals `route` on every
`(isCollection, exposesParams, isClassObject, strict)` — in particular it must
return `deepCopy`/`refuse` (not `reconstruct`) whenever `isClassObject` holds
(A3/A4). By R (the triple projection) the verified decision equals the real
post-patch `clone` arm selection on every value (G-CONF, ≥10⁵ inputs); by G-AX
the `deepCopy` arm returns a class object by identity, so the cloned parameter
`is` the original (the F2P observable). Therefore an impl satisfying this spec,
refined by the map above, takes the gold patch's branch on every input and
produces the gold patch's observable result on the F2P case — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: callee
soundness (G-AX: `deepcopy(class) is class`) and refinement fidelity (this doc,
G-EQ + G-CONF).
