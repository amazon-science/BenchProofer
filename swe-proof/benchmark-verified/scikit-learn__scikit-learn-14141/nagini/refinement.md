# refinement.md — scikit-learn__scikit-learn-14141

The operation-by-operation correspondence between `model.py`'s implementation
(the `collect_deps_versions` impl region and the `version_of` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `_get_deps_info()`'s dependency roster

Gold hunk (`sklearn/utils/_show_versions.py`, the `deps` list literal):
```
         "Cython",
         "pandas",
         "matplotlib",
+        "joblib",
     ]
```
The population loop `for modname in deps: deps_info[modname] = <version or None>`
(lines 58-67) is unchanged; adding `"joblib"` to the roster is what makes it a
key of the returned mapping.

| # | model.py impl op (`collect_deps_versions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | the roster `deps = [name_pip(), …, name_matplotlib(), name_parallel()]` (nine `int` tokens) | the `deps` list literal of nine name strings incl. the added `"joblib"` | R | each `str` name ↔ a distinct `int` identity token (mapping.md §2); the list of nine names ↔ the list of nine tokens, order-preserving. |
| A2 | per-name population, unrolled: `deps_info[name_X()] = version_of(name_X())` for each of the nine tokens | `for modname in deps: deps_info[modname] = ver` where `ver` is the imported version or `None` | R + A-consumed | **R:** iterating a static-length literal and unrolling it populate the same key/value pairs (the roster membership is statically fixed; the loop visits each entry exactly once, in order, with distinct names ⇒ distinct keys). **A-consumed:** the per-name value `ver` (the import + `mod.__version__`, or `None` on `ImportError`) is the unchanged opaque callee, modeled by `version_of` and consumed via the `Result()[name_X()] == version_of(name_X())` postconditions. |
| A3 | `return deps_info` (a `Dict[int, int]`) | `return deps_info` (a `Dict[str, Optional[str]]`) | R | dict carrier refinement `Dict[int,int]` ↔ `Dict[str, Optional[str]]` (mapping.md §2): key membership and per-key value correspond. |
| A4 | `Requires(MustTerminate(2))` on `collect_deps_versions` | the real `_get_deps_info()` is loop-free straight-line code (build a static list, populate a dict, return): every call returns | R | a total-correctness obligation carried in the precondition. Nagini checks partial correctness by default, so without it a same-spec impl that spins forever (`while b: Invariant(True)`) verifies vacuously while its real counterpart would hang the F2P (`test_get_deps_info` calls `_get_deps_info()` and would never return — the recorded G-PANEL-1/G-EQ weakness, audit witnesses atk_2/atk_4). The obligation adds NO behaviour beyond what the real code already has (it always terminates), so it cannot exclude a correct implementation; the axiomatised callee `version_of` is `@Pure` (pure functions always terminate in Nagini), so consuming it discharges no extra obligation. |

The discriminating content of the change — the parallel-execution dependency
`"joblib"` being **on the roster** so that it becomes a key of the result —
lives in step A1 (`name_parallel()` is the ninth roster token) consumed by step
A2 (the assignment `deps_info[name_parallel()] = version_of(name_parallel())`),
which discharges the postcondition `name_parallel() in Result()`. The pre-patch
roster omits `"joblib"`; `model_prepatch.py` reproduces that (eight-token roster,
no `name_parallel()` assignment) and **fails** the postcondition
`name_parallel() in Result()` — exactly the spec sensing the change (G-DIFF).
The "no spurious keys" postcondition (`Forall n. n in Result() ⇒ n is one of the
nine roster tokens`) holds in both, pinning the result's key-set to the roster.

## B. The one axiom — `version_of` (A-consumed)

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `version_of(name)` axiom (`Ensures(True)`) | the import + `get_version(mod) == mod.__version__` (or `None` on `ImportError`) per rostered name | A-consumed | `version_of` is the weakest contract on the per-module version observation the spec needs: the proof relies only on it being a total `int`-valued function (every rostered name gets *a* value stored, so it becomes a key), never on any property of the value. It is consumed by the `Result()[name_X()] == version_of(name_X())` postconditions (which fix the stored value to whatever the callee returns). G-AX confirms totality (each rostered name is a key of the real `_get_deps_info()` result, value present even when `None`) against the real routine. |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — extending the dependency roster so the parallel-execution
dependency is reported — is modeled **deeply** (the roster token `name_parallel()`
is an explicit ninth member consumed by an explicit assignment in the impl
region; A1+A2), not hidden behind an axiom about the function under change. The
only consumed axiom, `version_of` (**A-consumed**, site B), covers an
**unchanged** per-module observation the routine performs identically before and
after the patch. There is no A-reference deep model in this bundle (no stdlib
callee is re-implemented; the changed behaviour is a roster-membership edit
spelled out directly).

## D. verify(model) ⇒ resolved

`collect_deps_versions` verifies only if every one of the nine roster tokens —
including `name_parallel()` — is a key of the result carrying its `version_of`
value (A1+A2), and only if the result holds no key outside the roster. The
`MustTerminate` obligation (A4) additionally closes the partial-correctness
vacuity channel: an implementation may not diverge instead of answering, so
the postconditions cannot be satisfied vacuously by a non-terminating body. By R
(`str` name ↔ `int` token, `Dict[str,Optional[str]]` ↔ `Dict[int,int]`,
static-loop ↔ unroll) the verified routine equals the gold `_get_deps_info()` on
the tested observation (which keys appear); by the `version_of` A-consumed axiom
the per-name value is the real import-and-version observation, validated total by
G-AX. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and one audited callee — and the gold patch
resolves (`test_get_deps_info` now asserts `'joblib' in deps_info`; G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
