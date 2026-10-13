# mapping.md — django__django-15161

## Symbol binding (file:line @ base_commit 96e7ff5e9f)
When an expression object is serialized into a generated migration, the
migrations writer calls its `deconstruct()` method, whose first component is the
canonical import path used to reconstruct the object. That path is produced by
the `deconstruct` closure installed by the `deconstructible` class decorator
(`django/utils/deconstruct.py:20-48`):

```python
def deconstruct(obj):
    if path and type(obj) is klass:
        module_name, _, name = path.rpartition('.')
    else:
        module_name = obj.__module__
        name = obj.__class__.__name__
    module = import_module(module_name)        # existence check only
    if not hasattr(module, name):
        raise ValueError(...)
    return (
        path if path and type(obj) is klass
        else f'{obj.__class__.__module__}.{name}',
        obj._constructor_args[0],
        obj._constructor_args[1],
    )
```

The first tuple component — the canonical import path — is:
  * the configured `path` when a `path` was supplied to `@deconstructible` AND
    the object is of exactly the decorated class (`type(obj) is klass`);
  * otherwise `f'{obj.__class__.__module__}.{name}'`, i.e. the object's defining
    module joined to its class name.

Pre-patch, the expression classes `Func`, `Value`, `ExpressionWrapper`, `When`,
`Case`, `OrderBy` (`django/db/models/expressions.py`) carried no per-class
`@deconstructible(path=...)`; they inherited the bare `@deconstructible` on
`Expression` (`expressions.py:393`), whose decorator was invoked with `path=None`,
so the guard `path and type(obj) is klass` was always false and the canonical
path was always the fully-qualified `…expressions.X`. The gold patch adds
`@deconstructible(path='django.db.models.X')` to each of these classes
(`expressions.py:654, 734, 956, 988, 1055, 1228`), so the configured short path
is now selected for direct instances.

Lean modeled function name: `deconstructedPath` (deliberately neutral — it names
the *behavior* "the canonical import path produced by deconstruction", not any
patched class/symbol; see G-LEAK below).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `deconstructedPath` (modeled path-selection) | the first component of `deconstruct(obj)`, `deconstruct.py:42-48` |
| `simplifiedPath : Option String` | the `path` kwarg of `@deconstructible(path=…)`; `none` pre-patch (bare `@deconstructible`, `path=None`), `some 'django.db.models.X'` post-patch |
| `isExactType : Bool` | the predicate `type(obj) is klass` (`deconstruct.py:26, 44`) |
| `objModule : String` | `obj.__class__.__module__` (`deconstruct.py:45`), e.g. `'django.db.models.expressions'` |
| `objClassName : String` | `obj.__class__.__name__` / `name` (`deconstruct.py:30, 45`), e.g. `'Value'` |
| `qualifiedName objModule objClassName` | `f'{obj.__class__.__module__}.{name}'` (`deconstruct.py:45`) |
| result | the first element of the returned 3-tuple — the canonical import path |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `path` kwarg (`str` or `None`) | `simplifiedPath : Option String` (`some`/`none`) |
| `type(obj) is klass` (bool) | `isExactType : Bool` |
| `obj.__class__.__module__` (`str`) | `objModule : String` |
| `obj.__class__.__name__` / `name` (`str`) | `objClassName : String` |
| `f'{module}.{name}'` (`str`) | `qualifiedName objModule objClassName = objModule ++ "." ++ objClassName` |
| returned path (`str`) | `result : String` |

### Modeling notes
* The reconstruction arguments (`obj._constructor_args`, the 2nd/3rd tuple
  components) are unaffected by this change and are not modeled — the patch only
  changes the path component (directive 8: the modeled value is the path
  *produced by* the selection branch, grounded in the inputs).
* The `import_module` / `hasattr` existence check (`deconstruct.py:32-41`) is a
  guard that, on the modeled inputs, always succeeds for these public classes (a
  `django.db.models.X` short path resolves and `models.X` exists; the fallback
  module/name always exists since the class is defined there). It never alters
  the returned path value and is not modeled as a callee axiom; it is a no-op
  with respect to the path selection. G-CONF exercises only the path value.
* `path.rpartition('.')` (`deconstruct.py:28`) recomputes `module_name`/`name`
  for the existence check, but the *returned* path is the whole `path` verbatim,
  not the recomputed pieces — hence `simplifiedPath` maps directly to `result`
  in the exact-type case.

## Callee provenance + flag deps
* No unchanged callee is *consumed* as an axiom. The path selection is a pure
  decision over four observables; the dot-join (`f'{module}.{name}'`) is modeled
  deeply as `objModule ++ "." ++ objClassName` (an R/I op, not an axiom).
* Flag dependency: the short path is selected iff BOTH a `path` was configured
  AND `type(obj) is klass` (exact type). A subclass instance, or an absent
  `path`, falls back to the fully-qualified location. Modeled as the pair
  `(simplifiedPath : Option String, isExactType : Bool)`; G-CONF fuzzes all
  combinations (none / some × exact / non-exact).

## G-LEAK
The solver-visible `problem_statement` speaks of "simplified paths for
deconstruct of expressions", `F()`, `django.db.models.expressions.F()`,
`django.db.models.F()`, and "migration code". The spec view uses neutral
behavioral vocabulary ("canonical import path", "configured short import path",
"fully-qualified location", "defining module", "class name") and the
modeled-function identifier `deconstructedPath` shares no patched class name
(`Func`, `Value`, `ExpressionWrapper`, `When`, `Case`, `OrderBy`, `Expression`)
nor the decorator name (`deconstructible`) as a substring. The mechanism (adding
a `@deconstructible(path=…)` decorator) is NOT narrated — only the desired
behavior (which import path the serialization chooses).

## Pinned G-CONF fuzz seed
`15161`.
