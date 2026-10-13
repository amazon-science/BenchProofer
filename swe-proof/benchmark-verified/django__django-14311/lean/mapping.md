# mapping.md — symbol binding & type bijection (django__django-14311)

## Modeled function
- **Lean** `implementation_relaunchModule : List Char → List Char → List Char`
- **Python** `get_child_arguments()` — `django/utils/autoreload.py:213-243 @ base_commit`.
  Specifically the `-m` (module) branch, lines 226-228 @ base_commit (the changed
  lines).

`get_child_arguments` rebuilds the command line used to relaunch the dev server.
When the original process was started with `python -m <module>`, Python sets
`__main__.__spec__`. The fix concerns which module name is passed back to `-m`.

Pre-patch (base_commit, lines 226-227):
```python
if getattr(__main__, '__spec__', None) is not None and __main__.__spec__.parent:
    args += ['-m', __main__.__spec__.parent]
```
Post-patch (gold):
```python
if getattr(__main__, '__spec__', None) is not None:
    spec = __main__.__spec__
    if (spec.name == '__main__' or spec.name.endswith('.__main__')) and spec.parent:
        name = spec.parent
    else:
        name = spec.name
    args += ['-m', name]
```

The observable difference (the F2P test
`test_run_as_non_django_module_non_package`): when started as
`python -m foo.bar.baz` where `baz` is a plain module (not a package with a
`__main__.py`), `spec.name == 'foo.bar.baz'` and `spec.parent == 'foo.bar'`. The
pre-patch code emits `-m foo.bar` (wrong, truncated); the post-patch code emits
`-m foo.bar.baz` (correct) because `spec.name` is not `__main__` / `*.__main__`.

For a true package entry point (`python -m foo.bar` with `foo/bar/__main__.py`),
`spec.name == 'foo.bar.__main__'` and `spec.parent == 'foo.bar'`; both versions
emit `-m foo.bar` (the `.__main__` suffix branch).

## Modeled inputs
The modeled function captures EXACTLY the name-selection decision inside the
already-entered `__spec__ is not None` branch:
- `moduleName` ← `spec.name` (the executed module's fully-qualified name).
- `parentPackage` ← `spec.parent` (the parent package's name; `''` for a
  top-level module).
- output ← the value bound to `name` and passed to `-m`.

The `getattr(__main__,'__spec__',None) is not None` guard, the `args` list
assembly, `sys.argv[1:]`, and the `elif`/`else` fallback branches are unchanged
by the fix and orthogonal to the name-selection decision; they are out of model
scope. (The pre-patch additionally guarded the whole branch on
`__main__.__spec__.parent` being truthy; post-patch the branch is entered
whenever `__spec__` is present and the truthiness test on `parent` moved inside.
The behavioral difference observable to callers — the value passed to `-m` — is
fully captured by the name-selection decision modeled here. See Scope note.)

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `spec.name` (str, e.g. `'foo.bar.baz'`, `'foo.bar.__main__'`, `'__main__'`) | `moduleName : List Char` | dotted module path, per character |
| `spec.parent` (str, e.g. `'foo.bar'`, `''`) | `parentPackage : List Char` | parent package name; empty string ↔ `[]` |
| selected `name` passed to `-m` (str) | `List Char` | per-character |

`spec.name == '__main__'` ↔ `moduleName == "__main__".toList`.
`spec.name.endswith('.__main__')` ↔ `(".__main__".toList).isSuffixOf moduleName`.
`spec.parent` truthy (non-empty str) ↔ `!parentPackage.isEmpty`.

## Callee provenance
- `str.endswith` (`spec.name.endswith('.__main__')`) — Python stdlib; reproduced
  concretely as `List.isSuffixOf` over `List Char` (I/R, modeled deeply, not
  axiomatized).
- `==` on str and the bool `and` — reproduced concretely (I).
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub.

## Flag / branch dependency
The parent-package name is selected ONLY when the module is an entry-point module
(`__main__` or `*.__main__`) AND a parent package exists; otherwise the module's
own name is used. G-CONF fuzzes all four combinations (entry/non-entry ×
empty/non-empty parent) plus the exact F2P shape.

## Scope note
The pre-patch guard `and __main__.__spec__.parent` meant: with no parent, the
pre-patch code skipped the `-m` branch entirely and fell through to the
`elif`/`else`. The fix re-routes a no-parent module through `name = spec.name`.
The modeled decision returns `moduleName` in exactly that no-parent case
(`!parentPackage.isEmpty` is false), matching the post-patch `name = spec.name`
binding. The downstream branch selection (`-m name` vs script fallback) is driven
by the same condition and is orthogonal to the name VALUE the fix corrects.

## G-CONF fuzz seed
Pinned seed: **14311**. ≥10^5 fuzzed inputs over dotted-name / parent-package
alphabets plus the entry-point boundary cases.
