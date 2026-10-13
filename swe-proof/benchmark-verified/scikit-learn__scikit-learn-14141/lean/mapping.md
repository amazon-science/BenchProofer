# mapping.md — scikit-learn__scikit-learn-14141

## Symbol binding (file:line @ base_commit 3d997697fdd166eff428ea9fd35734b6a8ba113e)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_dependencyVersions` / `problem_spec_dependencyVersions` / `correct_dependencyVersions` | `_get_deps_info` (the routine that builds the dependency→version overview) | `sklearn/utils/_show_versions.py:33-69` |
| `expectedDeps` (pure helper) | the hardcoded `deps` name list (the contract for which dependencies are covered, POST-patch) | `sklearn/utils/_show_versions.py:42-51` |
| `lookupVersion` (opaque callee) | the per-module resolution `try: mod = sys.modules[m] or import_module(m); get_version(mod) except ImportError: None` | `sklearn/utils/_show_versions.py:53-67` |
| result `List (String × Option String)` | the returned `deps_info` dict | `sklearn/utils/_show_versions.py:56-69` |

## What the function does (base_commit)

`_get_deps_info` holds a hardcoded list `deps` of dependency import-names, then for
each name attempts to resolve the imported module and read its `__version__`,
storing `deps_info[modname] = ver`, or `deps_info[modname] = None` when the module
cannot be imported. It returns the `deps_info` dict.

```python
deps = ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",
        "pandas", "matplotlib"]          # base_commit (pre-patch)
def get_version(module):
    return module.__version__
deps_info = {}
for modname in deps:
    try:
        mod = sys.modules[modname] if modname in sys.modules else importlib.import_module(modname)
        deps_info[modname] = get_version(mod)
    except ImportError:
        deps_info[modname] = None
return deps_info
```

The gold patch appends `"joblib"` to the `deps` list. Nothing else changes: the
per-module resolution loop is untouched. Consequently the returned dict gains one
additional key, `"joblib"`, mapped to joblib's resolved version (or `None`).

The FAIL_TO_PASS test `test_get_deps_info` asserts each expected dependency name
— now including `'joblib'` — is a key of the returned dict. The keys of the dict
are exactly the entries of `deps` (a key is set for every name regardless of
import success, since `ImportError` still stores `None`).

## Lean modeling

- The modeled value is the returned dict, modeled as an ordered association list
  `List (String × Option String)` (Python dicts preserve insertion order; a value
  is a version string or the null option). The bijection is `dict ↔ list of
  (key, value) pairs in insertion order`; `str ↔ String`; `str | None ↔ Option
  String`.
- `expectedDeps` (pure region) is the post-patch dependency-name contract — the
  ordered list of import-names the overview must cover, including `joblib`. It is
  the grounding for the postcondition (the desired set/order of keys).
- `lookupVersion : String → Option String` (opaque) abstracts the UNCHANGED
  per-module version-resolution callee (module import + `__version__`, null on
  import failure). It is orthogonal to the fix (the patch does not touch it) and
  appears identically in spec and impl, so no property of it is consumed by the
  proof — it is carried as an opaque reference, not axiomatized.
- `implementation_dependencyVersions` is the `Id.run do` skeleton: it binds the
  post-patch `deps` literal, then a `for modname in deps` loop appends
  `(modname, lookupVersion modname)` to a mutable accumulator list — mirroring the
  Python `for modname in deps: deps_info[modname] = ...`.
- `problem_spec_dependencyVersions result` pins `result = expectedDeps.map (fun m
  => (m, lookupVersion m))`: the keys, in order, are exactly `expectedDeps` and
  each value is the resolved version of that module. This pins both the key set
  (frame discipline) and every value to its grounded computation.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `deps_info` dict | `List (String × Option String)` | dict ↔ pairs in insertion order |
| a module import-name `str` | `String` | identity |
| a version `str`, or `None` | `Option String` | `"x" ↔ some "x"`, `None ↔ none` |
| `get_version(import_module(m))` / `None` on `ImportError` | `lookupVersion m` | opaque per-module resolution (unchanged) |
| the `deps` name list (post-patch) | `expectedDeps` | element-wise `String` identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The fix changes only the
  hardcoded dependency-name list; that list is modeled DEEPLY/literally
  (`expectedDeps`). The per-module version resolution (`lookupVersion`) is an
  UNCHANGED callee, declared `opaque` so it can appear in the executable impl, and
  used identically on both sides of the spec equation — the proof consumes no
  property of it. Hence the `axioms` region declares the opaque signature only,
  with no `axiom _prop`, and **G-AX skips**. The R/I content (the deps list and
  the dict construction) is validated by G-CONF.
- No flag dependencies: the loop body is unconditional over `deps`.

## G-CONF fuzz seed

Pinned LCG seed: **14141** (see `conformance_check.py` `SEED`). The shadow is the
op-for-op transliteration of `implementation_dependencyVersions` (build the dict
by iterating the post-patch `deps` list and recording `(name, lookupVersion
name)`); the oracle is the faithful in-process replica of the POST-PATCH
`_get_deps_info` dict construction (same deps list including `joblib`).
`lookupVersion` is modeled as a fuzzed deterministic version table over a universe
of module names (including absent → `None`), driving both legs identically. The
check confirms keys (in order) and values agree over ≥1e5 fuzzed lookup tables,
with edge cases pinning the discriminating fact that `joblib` is among the keys.
