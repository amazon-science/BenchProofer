# mapping.md — pytest-dev__pytest-6197

## Symbol binding (file:line @ base_commit e856638ba086fcf5bebf1bebea32d5cf78de87b4)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_packageCollect` / `problem_spec_packageCollect` / `correct_packageCollect` | `Package.collect` (the package-content enumeration generator) | `src/_pytest/python.py:641-670` @ base_commit |
| `walkEntries` | the `for path in this_path.visit(...)` loop body that, per visited path, skips the package's own `__init__.py` / paths already inside an accounted nested package, and otherwise `yield from self._collectfile(path)` | `src/_pytest/python.py:649-670` |
| `PkgEntry.boundary` | a visited path is skipped: it is the package's own `__init__.py` (`path.basename == "__init__.py" and path.dirpath() == this_path`) OR it matches an already-recorded `pkg_prefix` (`any(pkg_prefix in parts_ and ...)`) | `src/_pytest/python.py:654-663` |
| `PkgEntry.isFile` | `path.isfile()` | `src/_pytest/python.py:651` |
| `PkgEntry.yields` | the list `list(self._collectfile(path))` the path resolves to | `src/_pytest/python.py:665` |
| `initMatches` | `init_module.check(file=1) and path_matches_patterns(init_module, self.config.getini("python_files"))` | `src/_pytest/python.py:644-646` |
| `initNode` | `Module(init_module, self)` yielded for the package's own `__init__.py` | `src/_pytest/python.py:647` |
| `result.2` (`importsOwnInit`) | whether enumerating the package imported the package's own `__init__.py` as a side effect (pre-patch: the leading `self._mount_obj_if_needed()` call forced `self._getobj()` == `self._importtestmodule()`) | `src/_pytest/python.py:642` (REMOVED by the patch) |

## What the patch changes (the modeled behavior)

The gold patch makes the underlying-object access of a `PyobjMixin` LAZY again and
removes the eager mount from package enumeration. Three coordinated edits:

1. `PyobjMixin.obj` property + `_mount_obj_if_needed`: the eager-mount helper is
   folded back into the `obj` property getter; the property mounts on first
   access only.
2. `Module.__init__` (which set `_ALLOW_MARKERS = False` for `__init__.py` and
   eagerly built the FS collector) is removed — `Module` inherits the default
   construction; nothing is imported at construction time.
3. **`Package.collect`**: the leading `self._mount_obj_if_needed()` call (which,
   pre-patch, imported the package's own `__init__.py` before walking the
   directory at all) is **removed**.

Edit 3 is the behavior the F2P tests observe and the modeled decision: enumerating
a package's contents must NOT import the package's own `__init__.py`. The other
two edits are the mechanism that makes the access lazy; they have no separately
observable behavior beyond enabling edit 3 (no separate F2P test exercises the
`obj` getter or `Module.__init__` in isolation — they are covered by the same
collection path).

```python
# POST-PATCH Package.collect (modeled)
def collect(self):
    this_path = self.fspath.dirpath()
    init_module = this_path.join("__init__.py")
    if init_module.check(file=1) and path_matches_patterns(
        init_module, self.config.getini("python_files")
    ):
        yield Module(init_module, self)
    pkg_prefixes = set()
    for path in this_path.visit(rec=self._recurse, bf=True, sort=True):
        is_file = path.isfile()
        if is_file:
            if path.basename == "__init__.py" and path.dirpath() == this_path:
                continue
        parts_ = parts(path.strpath)
        if any(pkg_prefix in parts_ and pkg_prefix.join("__init__.py") != path
               for pkg_prefix in pkg_prefixes):
            continue
        if is_file:
            yield from self._collectfile(path)
        elif not path.isdir():
            continue
        elif path.join("__init__.py").check(file=1):
            pkg_prefixes.add(path)
```

The pre-patch body is identical EXCEPT for a leading `self._mount_obj_if_needed()`
statement, which forced `self._getobj()` → `self._importtestmodule()` (importing
the package's own `__init__.py`) before any path was walked.

## Lean ↔ Python type bijection (G-CONF + G-AX use this)

| Lean | Python observable | source |
|---|---|---|
| `entries : List (PkgEntry α)` | the visited paths `this_path.visit(...)`, each reduced to `(boundary, isFile, yields)` | the `for path in ...` loop |
| `PkgEntry.boundary : Bool` | path is own `__init__.py` or matches a recorded `pkg_prefix` → `continue` (no contribution) | lines 654-663 |
| `PkgEntry.isFile : Bool` | `path.isfile()` | line 651 |
| `PkgEntry.yields : List α` | `list(self._collectfile(path))` (the per-file resolution, an unchanged orthogonal op; enters as data) | line 665 |
| `initMatches : Bool` | the own-`__init__.py` matches the `python_files` pattern | lines 644-646 |
| `initNode : α` | `Module(init_module, self)` | line 647 |
| `result.1 : List α` | the ordered sequence the generator yields | the generator body |
| `result.2 : Bool` (`importsOwnInit`) | whether the package's own `__init__.py` was imported as a side effect of enumerating | `_mount_obj_if_needed()` (pre-patch line 642), removed post-patch |

`result.2 = False` post-patch (no eager import); `result.1` = `([initNode] if
initMatches else []) ++ walkEntries entries`.

## Callee provenance + flag deps

- `_collectfile(path)` (→ `PkgEntry.yields`): an UNCHANGED callee. The patch does
  not touch per-file resolution; its result is fed in as plain input data, so it
  is NOT axiomatized (no consumed callee contract). It is the R-leg's input.
- The boundary predicate (own-`__init__.py` test + `pkg_prefix` membership) is
  UNCHANGED structure; it enters as the `boundary` Boolean.
- No flag-dependent callee. `python_files` pattern matching enters as the
  `initMatches` Boolean.

## G-CONF fuzz seed

Pinned seed: **6197** (also pinned in meta.json `verifier_pins.conf_seed`). The
conformance shadow transliterates `implementation_packageCollect` and diffs it
against a faithful in-process replica of the POST-PATCH `Package.collect` over
randomized entry lists; the soundness-critical clause is `importsOwnInit == False`
(enumeration never imports the package's own init file).
