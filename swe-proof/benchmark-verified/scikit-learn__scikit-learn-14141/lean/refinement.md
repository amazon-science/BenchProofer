# refinement.md — scikit-learn__scikit-learn-14141

Operation-by-operation correspondence between `implementation_dependencyVersions`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_get_deps_info`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let deps := expectedDeps` (`["pip","setuptools","sklearn","numpy","scipy","Cython","pandas","matplotlib","joblib"]`) | the hardcoded `deps = [...,"matplotlib","joblib"]` list (the patch appends `"joblib"`) | I (string list identity; the fix is the `joblib` entry) |
| 2 | `let mut depsInfo : List (String × Option String) := []` | `deps_info = {}` | R (dict ↔ ordered assoc list) |
| 3 | `for modname in deps do` | `for modname in deps:` | I |
| 4 | `depsInfo := depsInfo ++ [(modname, lookupVersion modname)]` | `deps_info[modname] = get_version(import_module(modname))` / `None` on `ImportError` | R (per-name version resolution ↔ `lookupVersion`; dict insert ↔ list append in order) |
| 5 | `return depsInfo` | `return deps_info` | R (same dict↔list bijection) |

Notes:

- **No A legs.** The only behavior the patch changes is the membership/order of
  the hardcoded dependency-name list, which is modeled DEEPLY/literally as
  `expectedDeps` (op 1, tagged I). SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed value, and here it is concrete data, not a callee.
- `lookupVersion` (op 4) is the UNCHANGED per-module version-resolution callee
  (module import + `__version__`, null on failure). It is declared `opaque` so it
  can appear in the executable impl, and it appears IDENTICALLY in
  `problem_spec_dependencyVersions` (`result = expectedDeps.map (fun m => (m,
  lookupVersion m))`) and in the impl. The proof therefore consumes NO property
  of it — it is neither an A-consumed axiom nor an A-reference; it is carried as a
  shared opaque symbol. Hence the `axioms` region declares only the signature
  (no `axiom _prop`) and **G-AX skips**.
- **Frame discipline (directive 5):** the spec pins the result to the FULL
  `expectedDeps.map …` — every key in order and every value to its grounded
  `lookupVersion` resolution. No output component is left free: a wrong impl that
  drops/adds/reorders a name, or mis-binds a version, cannot satisfy the spec.
- The **fix itself** is the presence of `"joblib"` in `expectedDeps`. The pre-patch
  impl (`Solution_prepatch.lean`) inlines the pre-patch list WITHOUT `joblib`, so
  its result (8 pairs) ≠ `expectedDeps.map …` (9 pairs) and `correct_*` is
  unprovable — exactly the discriminating signal G-DIFF wants (mirrors the F2P
  assertion `'joblib' in deps_info`).
- **G-CONF** mechanically refutes the R/I legs: the Python shadow of the impl is
  diffed against an in-process replica of the POST-PATCH dict construction over
  ≥1e5 fuzzed `lookupVersion` tables (`lookupVersion` driven identically on both
  legs). There are no A legs, so **G-AX skips**.
