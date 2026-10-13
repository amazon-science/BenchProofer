# mapping.md — symbol binding & type bijection (django__django-13820)

## Modeled function
- **Lean** `implementation_providesMigrations : Bool → ModulePath → Bool`
- **Python** the namespace-package classification block inside
  `MigrationLoader.load_disk`, `django/db/migrations/loader.py:90-99 @ 98ad327`
  (base_commit). Post-patch: the `else:` branch after a successful
  `import_module(module_name)` decides whether `app_config.label` joins
  `migrated_apps` (provides migrations) or `unmigrated_apps` (skipped).

The patch refines the guard for PEP-420 namespace packages. Pre-patch the guard
was `migrated ⟺ (__file__ is not None) ∧ is-a-package`. Post-patch it is
`migrated ⟺ is-a-package ∧ (__file__ is not None ∨ isinstance(__path__, list))`,
so a *regular* package that merely lacks `__file__` (a frozen-environment
package whose `__path__` is still an ordinary list) is now correctly recognized
as a migrations source, while true namespace packages (no `__file__`, custom
non-list `__path__`) are still skipped.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `getattr(module, '__file__', None) is not None` | `hasFile : Bool` | the module exposes a non-`None` file location |
| `not hasattr(module, '__path__')` | `path = ModulePath.noPath` | module is not a package |
| `hasattr(module,'__path__') and isinstance(module.__path__, list)` | `path = ModulePath.listPath` | package with an ordinary list `__path__` (regular package) |
| `hasattr(module,'__path__') and not isinstance(module.__path__, list)` | `path = ModulePath.customPath` | package with a custom (non-list) `__path__` (PEP-420 namespace package) |
| app added to `migrated_apps` | `result = true` | module treated as a migrations source |
| app added to `unmigrated_apps` (skip + `continue`) | `result = false` | module skipped |

The three `ModulePath` constructors partition the real `(__path__)` introspection
exhaustively: a module either has no `__path__` (not a package), or has a
`__path__` that is a `list`, or has a `__path__` that is some other iterable.
`hasFile` is an independent boolean. The product `Bool × ModulePath` (6 points)
covers every reachable combination of the two introspected attributes at this
guard.

## Callee provenance
- `getattr` / `hasattr` / `isinstance(_, list)` are Python language builtins used
  only to read introspection attributes; they carry no domain logic and are
  modeled directly as the `hasFile` flag and the `ModulePath` discriminant
  (I-tagged, refinement.md). They are NOT axiomatized and are NOT A-references.
- `import_module`, `reload`, `pkgutil.iter_modules`, the subsequent
  per-migration loading, and the `unmigrated_apps`/`migrated_apps` set mutations
  are OUTSIDE the modeled guard (the guard's only output is the
  migrated/unmigrated classification of one app). No UNCHANGED callee is consumed
  as an axiom; the axioms region is empty.

## Flag dependency
None. The decision depends only on the two introspected attributes `__file__`
and `__path__` of the already-imported module; there is no configuration flag.

## G-CONF fuzz seed
Pinned seed: **13820**. The full input domain is `Bool × {noPath, listPath,
customPath}` — only 6 points — so G-CONF enumerates all 6 exhaustively and then
pads with ≥10^5 randomly-drawn (hasFile, path) points (oversampling the
discriminating `(false, listPath)` case) for the disagreement count.
