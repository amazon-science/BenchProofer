# refinement.md — pytest-dev__pytest-6197

Operation-by-operation correspondence between `implementation_packageCollect`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `Package.collect`).
Tags: **R** type refinement (state the bijection), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by G-AX),
**I** identical concrete op.

The modeled values are (a) the ordered sequence of child collectors enumeration
yields, and (b) whether enumeration imported the package's own `__init__.py` as a
side effect. Post-patch, (b) is unconditionally `False` — that absence is the
fix the F2P tests observe.

| # | Lean op (impl region) | patch.diff / `Package.collect` counterpart | tag | notes |
|---|---|---|---|---|
| 1 | `let importsOwnInit := false` | the leading `self._mount_obj_if_needed()` statement is REMOVED by the patch; enumeration no longer imports the package's own `__init__.py` | R | `importsOwnInit : Bool` ↔ "did enumeration import the package's own init file". Post-patch the import side effect is absent ⇒ `false`. The prepatch impl sets this `true` (the regression: eager mount before walking). |
| 2 | `if initMatches then collected := collected ++ [initNode]` | `if init_module.check(file=1) and path_matches_patterns(init_module, getini("python_files")): yield Module(init_module, self)` | R | `initMatches : Bool` ↔ the `check ∧ path_matches_patterns` conjunction; `initNode : α` ↔ `Module(init_module, self)`. The own-init Module is yielded first. |
| 3 | `for e in entries do … ` | `for path in this_path.visit(rec=self._recurse, bf=True, sort=True):` | R | `entries : List (PkgEntry α)` ↔ the visited paths in traversal order, each reduced to `(boundary, isFile, yields)` per mapping.md. |
| 4 | `if e.boundary then continue` | the own-`__init__.py` skip (`if path.basename == "__init__.py" and path.dirpath() == this_path: continue`) AND the recorded-`pkg_prefix` skip (`if any(pkg_prefix in parts_ and pkg_prefix.join("__init__.py") != path …): continue`) | R | both skip conditions collapse to the single `boundary` observation: a boundary path contributes nothing. Faithful because both Python branches `continue` (no yield) regardless of `is_file`. |
| 5 | `if e.isFile then collected := collected ++ e.yields` | `if is_file: yield from self._collectfile(path)` (the non-boundary, regular-file branch) | R | `isFile : Bool` ↔ `path.isfile()`; `yields : List α` ↔ `list(self._collectfile(path))`. `_collectfile` is an UNCHANGED orthogonal callee; its result enters as input data (NOT axiomatized). A directory path (`isFile = false`) yields nothing here — matching the `elif`/`pkg_prefixes.add` branches, which yield no collector (they only update traversal bookkeeping that is already reflected in later entries' `boundary`). |
| 6 | `return (collected, importsOwnInit)` | the generator's yielded sequence + the (absent) import side effect | R | the two modeled outputs. |

Every row is **R** (type refinement of a concrete imperative op). No row is
A-consumed or A-reference: `_collectfile`'s per-file resolution is fed in as the
`yields` data rather than re-derived, and the boundary predicate is fed in as the
`boundary` Boolean, so there is no callee whose contract the proof must assume.
The R legs are mechanically refuted by G-CONF (the shadow transliterates this
impl and diffs it against a faithful replica of the post-patch generator over
fuzzed entry lists).

## Changed-op faithfulness

The single behavior-changing op is row 1: pre-patch `Package.collect` began with
`self._mount_obj_if_needed()` (which forced `self._getobj()` →
`self._importtestmodule()`, importing the package's own `__init__.py`) BEFORE
walking the directory; the patch removes that statement. The impl mirrors this
exactly — post-patch `importsOwnInit := false`. The prepatch impl
(`Solution_prepatch.lean`) sets `importsOwnInit := true`, which is precisely the
regression: scanning a package directory imports its own `__init__.py`, so a
package whose `__init__.py` raises at import time (`assert False`) breaks
collection. This disagrees with the spec's `result.2 = false` clause on EVERY
input — exactly the discriminating behavior the F2P tests
`test_does_not_eagerly_collect_packages` and `test_does_not_put_src_on_path`
exercise (collection of a package whose `__init__.py` would fail / a non-importable
`src` package must succeed because the init file is never eagerly imported).

The accompanying patch edits (folding `_mount_obj_if_needed` back into the `obj`
property getter, and removing `Module.__init__`) are the mechanism that restores
lazy access; they have no separately observable F2P behavior beyond enabling the
removal in row 1, so they are not separately modeled (one independently-fixed
behavior ⇒ one prepatch variant).
