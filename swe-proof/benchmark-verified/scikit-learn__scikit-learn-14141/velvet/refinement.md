# refinement.md — scikit-learn__scikit-learn-14141

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`collectDependencyVersions` `do` block, the `depEntries` deep model, and the
`lookupVersion` uninterpreted callee) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**
where the proof uses the axiom, **A-reference** where a deep model is validated
== the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A leg and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested observation (the covered-dependency set),
so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The dependency-report site — `_get_deps_info()` (`sklearn/utils/_show_versions.py:33`)

Gold hunk:
```
         "Cython",
         "pandas",
         "matplotlib",
+        "joblib",
     ]
```
The patch inserts one element (`"joblib"`) into the fixed `deps` roster that the
build loop iterates over to produce the `{name: version}` report.

| # | Solution.lean impl op (`collectDependencyVersions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `dependencyNames` — the fixed roster of names, incl. `"joblib".toList` | the post-patch `deps` list literal (incl. `"joblib"`) | R + I | each name is a `str` ↔ `List Char` (mapping.md §2). The roster *content* (which names, in which order) is the data the patch changes; modeled concretely (I), so G-CONF transliterates it directly. |
| A2 | the backward `while` fold building `result = depEntries dependencyNames` (one `(n, ver)` entry per roster name, in order) | the `for modname in deps:` loop building `deps_info[modname] = ver` | I | the loop is the per-name expansion of the roster; `depEntries` (front-recursive) is its deep model. The assoc-list ↔ insertion-ordered dict is a bijection (mapping.md §2: no duplicate names). |
| A3 | `let ver :| ver = lookupVersion n` — the per-name version value | `sys.modules[modname]`/`importlib.import_module` → `module.__version__`, `None` on `ImportError` | A-consumed | the **unchanged** per-name version query. Modeled as the uninterpreted `lookupVersion` (no `ensures`): the value is environment dependent and the contract pins no version. The `:|` choice is sound by construction; G-AX confirms the real callee's codomain (str-or-None) and that it never raises (mapping.md §3.1). |
| A4 | `out = depEntries dependencyNames` and `"joblib".toList ∈ out.map Prod.fst` | the returned `deps_info` dict | R | the dict ↔ assoc-list bijection (mapping.md §2); `'joblib' in deps_info` (the F2P observation) ↔ `"joblib".toList ∈ out.map Prod.fst`. |

Discriminating content of the change — the report COVERS `joblib` — lives in
`"joblib".toList ∈ dependencyNames` (`joblib_mem_roster`) feeding the post-
condition `"joblib".toList ∈ out.map Prod.fst`, and in
`out = depEntries dependencyNames` (the full roster). The pre-patch roster omits
the final entry; `Solution_prepatch.lean` iterates `dependencyNames.dropLast`
and so **fails BOTH** postconditions (G-DIFF): the result is not
`depEntries dependencyNames`, and `"joblib"` is absent from its keys.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the roster's
membership — is modeled **concretely** (`dependencyNames` includes `joblib`,
step A1, an I op), not hidden behind an axiom about the function under change.
The only modeled callee, `lookupVersion` (step A3), is an **unchanged** per-name
version query, modeled uninterpreted (weakest contract; A-consumed via the `:|`
stub). There is no axiom about `_get_deps_info` itself.

## C. verify(Solution) ⇒ resolved

`collectDependencyVersions` verifies only if its output is `depEntries
dependencyNames` (A2) over the full roster including `joblib` (A1), and joblib is
in the covered keys (A4). By R (`str ↔ List Char`, dict ↔ insertion-ordered
assoc-list) the verified report covers exactly the patched `deps` roster, so
`'joblib' in _get_deps_info()` holds — which is exactly what the F2P test
`test_get_deps_info` asserts (and the PASS_TO_PASS keys, all earlier roster
entries, are preserved by A1's full roster). By G-AX the real `_get_deps_info()`
key set/order equals `dependencyNames` and never raises; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ checks. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: axiom soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
