# mapping.md — pytest-dev__pytest-6197

Binds `Solution.lean` symbols to the repo at
`base_commit = e856638ba086fcf5bebf1bebea32d5cf78de87b4`.

Repo file under change: `src/_pytest/python.py`
(`Package.collect`, the generator that enumerates a test-package directory's
contents).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `gatherEntries (initMatches : Bool) (initNode : Nat) (entries : List PkgEntry) return (out : List Nat × Bool)` | `Package.collect(self)` — `src/_pytest/python.py:628-655` (the generator that walks `self.fspath.dirpath()` and yields the collected children) | the modeled directory-content enumeration |
| `initMatches` | `init_module.check(file=1) and path_matches_patterns(init_module, self.config.getini("python_files"))` — `python.py:631-634` | whether the package's own `__init__.py` matches the configured test-file pattern |
| `initNode` | `Module(init_module, self)` — the leading collector yielded for the package's own `__init__.py` when it matches (`python.py:635`) | the leading item token |
| `entries : List PkgEntry` | the paths visited by `for path in this_path.visit(rec=self._recurse, bf=True, sort=True)` (`python.py:637-655`), each reduced to `(boundary, isFile, yields)` | the per-path observations the walk consumes |
| `PkgEntry.boundary` | the path contributes nothing: it is the package's own `__init__.py` (`path.basename == "__init__.py" and path.dirpath() == this_path`) OR it matches an already-recorded `pkg_prefix` | the skip predicate (UNCHANGED structure) |
| `PkgEntry.isFile` | `path.isfile()` | regular-file test |
| `PkgEntry.yields` | `list(self._collectfile(path))` — the per-file resolution (an UNCHANGED orthogonal callee; enters as data) | the child items a non-boundary regular file contributes |
| `walkEntries` (pure) | the visit loop's yielded contribution: boundary paths and directories contribute nothing, non-boundary regular files contribute their `_collectfile` results, in visit order | the pure walk function |
| `out.1 : List Nat` | the ordered sequence of nodes `Package.collect` yields | the produced enumeration |
| `out.2 : Bool` | whether enumerating the package loaded (imported) the package's own `__init__.py` as a side effect — pre-patch the leading `self._mount_obj_if_needed()` (`python.py:629`) forced `self._obj = self._getobj()` = `self._importtestmodule()`; the fix removes that call | the load-event observable; post-patch unconditionally `false` |

The pre-patch repo line the fix removes (refinement audit only, not in the
consumer spec view): the first statement of `Package.collect`,
`self._mount_obj_if_needed()` (`src/_pytest/python.py:629`). It eagerly forces
`self._obj = self._getobj()` (= `self._importtestmodule()`), importing the
package directory's own `__init__.py` as a side effect of merely *scanning* the
directory for entries. The companion gold hunks (the `PyobjMixin.obj` property
refactor at `python.py:251-271` and the deletion of `Module.__init__` at
`python.py:432-440`) are supporting refactors that make the lazy access work;
they do not add observable behavior beyond "the eager mount no longer happens
during the walk" (see refinement.md §B).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| whether the walk imported the directory's own `__init__.py` (its top-level code ran) | `out.2 : Bool` — a RESULT component, not a `mut` state slot | `false` ↔ the initializer was never loaded during the walk; `true` ↔ it was. Making the event a component of the returned value (rather than a resettable mutable slot) means an implementation that performs the load cannot erase the fact before returning: the spec clause `out.2 = false` pins the event itself. This is the observable the F2P test grades (whether the `assert False` in the repro's `__init__.py` ran during collection). |
| a visited path, as the walk consumes it | `PkgEntry` (`boundary : Bool`, `isFile : Bool`, `yields : List Nat`) | boundary/skip decision ↔ `boundary`; `path.isfile()` ↔ `isFile`; the `_collectfile` resolution (unchanged callee, enters as data) ↔ `yields` (each yielded node ↔ one `Nat` token). |
| the children yielded by `Package.collect` | `List Nat` (`out.1`) | order-and-membership carrier: each yielded node ↔ one `Nat` token; `yield`/`yield from` sequence ↔ `List` order. The walk's gathering logic is UNCHANGED, so the spec pins the output to the exact pure walk of the given entries: `out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries`. |

What the F2P tests behaviorally observe is whether the directory's `__init__.py`
was imported — i.e. whether its top-level code (the repro's `assert False`) ran
during the walk. That EVENT is carried as the second result component,
`ensures out.2 = false`: because it is part of the returned value, no
implementation can fire the event and then hide it (there is no mutable slot to
reset). The module object's internal structure is an R detail (a `Bool`
suffices: loaded or not).

## 3. Callee provenance

None (no axioms, no A-reference deep models). The operations the walk performs:
- The directory scan (`this_path.visit(...)`, the boundary predicate) —
  **UNCHANGED** by the fix; enters as the `entries` observations.
- `self._collectfile(path)` (per-file resolution) — **UNCHANGED** orthogonal
  callee; its result enters as the `yields` data of each entry (not re-derived,
  not axiomatized).
- `self._mount_obj_if_needed()` (→ `self._importtestmodule()`, importing the
  directory's own `__init__.py`) — the op the fix **removes**. Modeled deeply
  as the load-event result component `out.2`: the correct walk reports `false`
  (never loads), the buggy walk reports `true`. No outside contract is consumed.

## 4. G-CONF fuzz seed

Pinned seed: **6197**. The conformance shadow transliterates the
`gatherEntries` impl region (leading init item, left fold over the entries,
pair with the load flag) and diffs it against a faithful in-process replica of
the POST-PATCH `Package.collect` over randomized entry lists; the
soundness-critical clause is `out.2 == False` (enumeration never imports the
package's own init file).
