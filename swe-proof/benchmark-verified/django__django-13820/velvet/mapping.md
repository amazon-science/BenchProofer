# mapping.md — django__django-13820

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 98ad327864aed8df245fd19ea9d2743279e11643`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/migrations/loader.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `migrationsModuleLoadable (hasFile) (hasPath) (pathIsList)` | the per-module classification inside `MigrationLoader.load_disk` — the `else:` block at `django/db/migrations/loader.py:90-103` that decides whether an imported candidate module is scanned for migrations or its app is added to `self.unmigrated_apps` | the modeled changed decision |
| `hasFile : Bool` *(param)* | `getattr(module, '__file__', None) is not None` (`loader.py:92`/post-patch `loader.py:99`) — whether the imported module advertises a concrete file location | observation: module has a `__file__` |
| `hasPath : Bool` *(param)* | `hasattr(module, '__path__')` (`loader.py:95`/post-patch `loader.py:94`) — whether the imported module is a package (exposes a search path) | observation: module is a package |
| `pathIsList : Bool` *(param)* | `isinstance(module.__path__, list)` (post-patch `loader.py:101`); for a non-package (`hasPath == false`) the attribute is absent and the value is irrelevant (see §2 note) | observation: the package search path is an ordinary list |
| `loadable` | the body of the `else:` decision: the disjunction of "skip → `unmigrated_apps`" guards, negated — i.e. the module is loaded (`migrated_apps` + scanned by `pkgutil.iter_modules`) iff it survives all the `continue` guards | pure spec: whether this module's migrations directory is scanned |

The pre-patch repo content the change replaces (refinement audit only, not in
the consumer spec view): the standalone guard `if getattr(module, '__file__',
None) is None:` (`loader.py:90-93` @ base_commit), which skipped any module with
no `__file__` *before* the package check, with no `isinstance(__path__, list)`
qualification.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `getattr(module, '__file__', None) is not None` — a truth value | `Bool` (`hasFile`) | Python truthiness of "`__file__` present and not `None`" ↔ `hasFile`; `True` ↔ `true`, `False` ↔ `false` |
| `hasattr(module, '__path__')` — a truth value | `Bool` (`hasPath`) | `True` ↔ `true`, `False` ↔ `false` |
| `isinstance(module.__path__, list)` — a truth value | `Bool` (`pathIsList`) | `True` ↔ `true`, `False` ↔ `false` |
| the module's classification effect: scanned for migrations (`self.migrated_apps.add(...)`, `pkgutil.iter_modules(module.__path__)`) vs. skipped (`self.unmigrated_apps.add(...)`, `continue`) | `Bool` (`out`) | `out = true` ↔ module is scanned / its app becomes a *migrated* app; `out = false` ↔ app added to `unmigrated_apps` |

Notes:
- The decision the patch changes lives entirely in the `else:` block reached
  after a *successful* `import_module` (`loader.py:81-103`); the earlier
  `module_name is None` and `ModuleNotFoundError` guards (`loader.py:75-89`) are
  unchanged and out of the modeled slice (a module that fails to import never
  reaches this decision).
- When `hasPath == false` the module is not a package and `module.__path__`
  does not exist, so `pathIsList` is unobservable; the spec is total over the
  full `Bool³` cube and both pre- and post-patch logic ignore `pathIsList` when
  `hasPath == false` (the non-package `continue` fires first / the namespace
  guard's `__path__` access is never reached), so any value of `pathIsList`
  there is consistent. G-CONF feeds only realizable `(hasFile, hasPath,
  pathIsList)` triples (it constructs concrete module objects), and additionally
  enumerates the full 8-point cube via direct logic to confirm totality.
- The post-patch ordering checks `hasattr(module, '__path__')` *before* the
  `__file__`/`isinstance` guard, so `module.__path__` is only dereferenced when
  it exists; `migrationsModuleLoadable` mirrors that (`notPackage` short-circuits
  to `false` before `pathIsList` is consulted).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There are **no consumed axioms** and **no deep-model references** to unchanged
callees. The modeled decision is a finite boolean classification over three
attribute observations; every operation in the impl region is a language-level
boolean primitive (`!`, `&&`, `||`, `if`), modeled as concrete I-ops and
refinement-checked against the real `MigrationLoader.load_disk` behaviour by
`conformance_check.py` (G-CONF). Hence there is **no `axiom_check.py`** and G-AX
is `skip` (gates.py records "no axiom_check.py").

The real `load_disk` does call `import_module`, `pkgutil.iter_modules`, and
`reload` — but all are **unchanged** by the patch and none participate in the
modeled decision (they run on the branches *after* the classification, or before
it). They are therefore neither axiomatized nor deep-modeled; G-CONF exercises
them implicitly by driving the real patched `load_disk` end to end.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` pins `SEED = 13820`. The modeled space is finite — the
observable triple `(hasFile, hasPath, pathIsList)` has 8 points. G-CONF builds a
real importable package module per realizable configuration, drives the real
patched `MigrationLoader.load_disk` (via `MIGRATION_MODULES` + attribute
manipulation, exactly as the F2P test does), classifies the outcome (app in
`migrated_apps`/disk_migrations vs `unmigrated_apps`), and compares against the
R/I shadow; it then fuzz-resamples the configuration space (seed pinned) for a
deterministic high-count verdict.
