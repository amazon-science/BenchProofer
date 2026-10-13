# refinement.md — django__django-13820

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`migrationsModuleLoadable` `do` block and the pure `loadable`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed**/**A-reference**), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. There are **no A
legs** in this bundle (no axioms, no deep-model references): the whole impl
region is R/I. Claim: any impl verifying against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the modeled decision,
so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The module-classification site — `MigrationLoader.load_disk` (`django/db/migrations/loader.py`)

Gold hunk (the `else:` block reached after a successful `import_module`):
```
-                # Empty directories are namespaces.
-                # getattr() needed on PY36 and older (replace w/attribute access).
-                if getattr(module, '__file__', None) is None:
-                    self.unmigrated_apps.add(app_config.label)
-                    continue
                 # Module is not a package (e.g. migrations.py).
                 if not hasattr(module, '__path__'):
                     self.unmigrated_apps.add(app_config.label)
                     continue
+                # Empty directories are namespaces. Namespace packages have no
+                # __file__ and don't use a list for __path__. See
+                # https://docs.python.org/3/reference/import.html#namespace-packages
+                if (
+                    getattr(module, '__file__', None) is None and
+                    not isinstance(module.__path__, list)
+                ):
+                    self.unmigrated_apps.add(app_config.label)
+                    continue
```
The module is **loaded/scanned** (`self.migrated_apps.add(...)` then
`pkgutil.iter_modules(module.__path__)`) iff it survives both `continue` guards.

| # | Solution.lean impl op (`migrationsModuleLoadable`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `hasFile : Bool` | `getattr(module, '__file__', None) is None` (negated) | R | the truth value "module advertises a concrete file location" ↔ `hasFile` (mapping.md §2). |
| A2 | param `hasPath : Bool` | `hasattr(module, '__path__')` | R | "module is a package" ↔ `hasPath` (mapping.md §2). |
| A3 | param `pathIsList : Bool` | `isinstance(module.__path__, list)` | R | "the package search path is an ordinary list" ↔ `pathIsList` (mapping.md §2). Only observed when `hasPath` (the post-patch order checks `__path__` exists first). |
| A4 | `let notPackage := !hasPath`; `if notPackage then false` | `if not hasattr(module, '__path__'): unmigrated_apps.add; continue` | I | the non-package skip; identical boolean guard, identical short-circuit ordering (checked before `__path__` is dereferenced). |
| A5 | `let isNamespace := (!hasFile) && (!pathIsList)`; `if isNamespace then false` | `if getattr(module,'__file__',None) is None and not isinstance(module.__path__, list): unmigrated_apps.add; continue` | I | the implicit-namespace skip — the **new** post-patch guard; identical conjunction `(__file__ missing) ∧ (__path__ not a list)`. |
| A6 | `else true` | fall through to `self.migrated_apps.add(app_config.label)` + scan | I/R | surviving both guards ⇒ the module is scanned; `out = true` ↔ app classified *migrated* (mapping.md §2). |

`loadable hasFile hasPath pathIsList = hasPath && (hasFile || pathIsList)` is the
negation of the disjunction of the two skip guards: skip ⟺ `!hasPath ∨ (!hasFile
∧ !pathIsList)`; loadable ⟺ `hasPath ∧ ¬(!hasFile ∧ !pathIsList)` ⟺ `hasPath ∧
(hasFile ∨ pathIsList)`. The `do` block computes this via the same two guards
in the same order, so the impl op A4/A5/A6 chain is the gold control flow I-for-I.

## B. The discriminating change — and the prepatch

The single behavioural flip between pre- and post-patch is the configuration
`(hasFile = false, hasPath = true, pathIsList = true)` — a **regular package
that exposes an ordinary list `__path__` but advertises no `__file__`** (the
frozen-environment case the issue describes):
- **post-patch / spec:** `loadable false true true = true && (false || true) =
  true` → loaded.
- **pre-patch:** the removed standalone guard `if getattr(module,'__file__',None)
  is None: … continue` fires first → skipped.

`Solution_prepatch.lean` reproduces the pre-patch order (`!hasFile` checked
*before* the package test, with no `pathIsList` qualification): its `out`
evaluates to `false` at `(false, true, true)` while the frozen spec requires
`loadable = true`, so `prove_correct` fails its `out = loadable …` obligation
(G-DIFF) — the unsolved goal is exactly the divergence on that case. Namespace
packages `(false, true, false)` remain skipped under both, and ordinary regular
packages `(true, true, true)` remain loaded under both, so the prepatch fails
*only* on the tested frozen-package case. This is the behaviour the F2P test
`test_loading_package_without__file__` observes: a regular package whose
`__file__` is deleted and whose `__spec__.origin`/`has_location` are cleared, yet
whose `__path__` is a real list, must still yield its `['0001_initial',
'0002_second']` migrations.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that changed — the implicit-namespace
rejection criterion — is a finite boolean classification over three attribute
observations, modeled **directly** (the pure `loadable` and the spelled-out
two-guard `do` block, all I-ops), not hidden behind an axiom. There are no
consumed axioms and no deep-model references: the only callees in the real
`load_disk` (`import_module`, `pkgutil.iter_modules`, `reload`) are **unchanged**
and outside the modeled decision (mapping.md §3), so they are neither
axiomatized nor deep-modeled; G-CONF exercises them implicitly by driving the
real patched `load_disk`.

## D. verify(Solution) ⇒ resolved

`migrationsModuleLoadable` verifies only if its output equals `loadable hasFile
hasPath pathIsList = hasPath && (hasFile || pathIsList)` (A4–A6) at every point of
`Bool³`. By R (the three attribute observations ↔ the three booleans,
migrated/unmigrated ↔ `out`), the verified decision equals the real patched
`load_disk` classification on every realizable module configuration. By G-CONF
the R/I transliteration of the `do` block agrees with `patch.diff`'s behaviour
(the real `load_disk`) on every realizable configuration including the
discriminating `(false, true, true)`. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
doc + G-CONF); there are no axioms to trust (no G-AX obligations).
