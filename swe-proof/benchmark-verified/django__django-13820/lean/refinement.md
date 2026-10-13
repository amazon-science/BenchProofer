# refinement.md — operation correspondence (django__django-13820)

Maps every op in `implementation_providesMigrations` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The modeled function is the namespace-package classification inside
`MigrationLoader.load_disk`: for a successfully-imported app migrations module,
whether that module is treated as a *source of migrations* (added to
`migrated_apps`) or skipped as a placeholder (added to `unmigrated_apps`). The
patch refines the guard sequence. Modeled inputs:

- `hasFile : Bool` ↔ `getattr(module, '__file__', None) is not None`
  (the module exposes a non-`None` file location).
- `path : ModulePath` ↔ the module's `__path__` introspection:
  - `noPath`     ↔ `not hasattr(module, '__path__')` (not a package),
  - `listPath`   ↔ `hasattr(module,'__path__') and isinstance(module.__path__, list)`,
  - `customPath` ↔ `hasattr(module,'__path__') and not isinstance(module.__path__, list)`.
- `result : Bool` = `True` iff the app is added to `migrated_apps` (treated as a
  source of migrations); `False` iff added to `unmigrated_apps`.

The post-patch guard (after the `else:` of the successful import) is:
```
if not hasattr(module, '__path__'):        -> unmigrated
if getattr(module,'__file__',None) is None
   and not isinstance(module.__path__,list): -> unmigrated
# else                                      -> migrated
```
i.e. `migrated  ⟺  isPackage ∧ (hasFile ∨ pathIsList)`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if !path.isPackage then return false` | `if not hasattr(module, '__path__'): unmigrated_apps.add(...); continue` | I | the "not a package" guard, modeled by `ModulePath.isPackage` (true unless `noPath`) |
| 2 | `if !hasFile && !path.isList then return false` | `if getattr(module,'__file__',None) is None and not isinstance(module.__path__, list): unmigrated_apps.add(...); continue` | I | the refined namespace-package guard; `hasFile` ↔ `__file__ is not None`, `path.isList` ↔ `isinstance(__path__, list)` |
| 3 | `return true` | fall-through to `self.migrated_apps.add(app_config.label)` (the app provides migrations) | I | the module is accepted as a migrations source |

All rows are I (identical concrete boolean ops under the type bijection in
mapping.md). No A-consumed rows: the proof discharges
`problem_spec_providesMigrations` directly by boolean case analysis; no
UNCHANGED callee property is assumed. No A-reference rows: the only callees are
`getattr` / `hasattr` / `isinstance`, modeled directly as the `hasFile` flag and
the `ModulePath` discriminant (language-level introspection, not domain logic).
No changed op is inexpressible.

## G-DIFF discriminating clause
Row 2 reordered vs row 1. Pre-patch the file-location guard fires FIRST and
unconditionally (`if getattr(module,'__file__',None) is None: unmigrated`), so
`migrated ⟺ hasFile ∧ isPackage`. On the input `hasFile = false`,
`path = listPath` (a regular package with no `__file__` but an ordinary list
`__path__` — exactly the frozen-environment case of the F2P test
`test_loading_package_without__file__`) the pre-patch impl returns `false` while
the frozen spec demands `true`. So `Solution_prepatch.lean`'s
`correct_providesMigrations` cannot close. That is the G-DIFF signal.
