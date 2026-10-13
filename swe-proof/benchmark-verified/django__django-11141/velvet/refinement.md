# refinement.md — django__django-11141

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`classifyMigrationSources` `do` block + the deep `classify`/`classifyAll` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the classification it changes, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The classification site — `MigrationLoader.load_disk` (`django/db/migrations/loader.py:64`)

The patch edits the per-application loop body (the `for app_config in
apps.get_app_configs()` loop). Two coupled hunks:

```
@@ else: (after a successful import_module)
-     # Empty directories are namespaces.
-     # getattr() needed on PY36 and older (replace w/attribute access).
-     if getattr(module, '__file__', None) is None:
-         self.unmigrated_apps.add(app_config.label)
-         continue
      if not hasattr(module, '__path__'):
          self.unmigrated_apps.add(app_config.label)
          continue
      ...
- self.migrated_apps.add(app_config.label)
  migration_names = { ... pkgutil.iter_modules(module.__path__) ... }
+ if migration_names or self.ignore_no_migrations:
+     self.migrated_apps.add(app_config.label)
+ else:
+     self.unmigrated_apps.add(app_config.label)
```

| # | Solution.lean impl op (`classifyMigrationSources`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `sources : List MigrationSource` | the applications iterated by `for app_config in apps.get_app_configs()`, each reduced to the four observations its migrations module yields | R | record ↔ the per-app observations; G-CONF bridges each field via mapping.md §2. |
| A2 | `classify m` for a non-package (`isPackage = false` ⇒ `false`) | `if not hasattr(module, '__path__'): self.unmigrated_apps.add(...)` (surviving guard) | I + R | the not-a-package early step survives the patch; `false` ↔ "added to `unmigrated_apps`" (mapping.md §2). |
| A3 | `classify m` for a package: `!m.migrationNames.isEmpty \|\| m.ignoreMissing` | the new `if migration_names or self.ignore_no_migrations: migrated else: unmigrated` | I + R | the changed decision, modeled **deeply** and concretely; the truth-test on the discovered set ↔ `!isEmpty` (only emptiness is observed — mapping.md §2); `ignore_no_migrations` ↔ `ignoreMissing`. Verdict `true`↔`migrated_apps`, `false`↔`unmigrated_apps`. |
| A4 | `classify` does NOT read `m.isNamespace` | the **deletion** of `if getattr(module, '__file__', None) is None: unmigrated; continue` | R (frame) | directive-5 frame point: the namespace observation is carried in the record but never gates the verdict, mirroring the removed short-circuit. The deletion is exactly "the namespace flag no longer forces unmigrated." |
| A5 | `result := classify m :: result`, backward `while` fold over `sources` | the loop visiting each `app_config` once and recording one verdict | I | per-element transliteration; `classifyAll` is the order-preserving list of verdicts (G-CONF compares element-wise). |

Discriminating content of the change lives in two independently-observable
places, each pinned by `classify` and exercised by a distinct prepatch:

* **A4 (namespace short-circuit removed)** — `classify` ignores `isNamespace`,
  so a namespace package that exposes a migration is classified `true`
  (migrated). `Solution_prepatch.lean` reads `isNamespace` (the removed
  short-circuit) and so classifies such a source `false`, **failing**
  `out = classifyAll sources` on the `isNamespace` term (G-DIFF). This is the
  F2P scenario `test_loading_namespace_package`.
* **A3 (conditional add)** — `classify` returns `false` for an empty,
  not-kept package. `Solution_prepatch_2.lean` adds every package
  unconditionally (`if isPackage then true`), **failing** the spec on the
  empty-package case (`test_load_empty_dir` / `test_marked_as_unmigrated`'s
  empty-source semantics).

## B. No additional change sites

The patch touches a single function (`load_disk`). The inner
`disk_migrations`-building loop and the import/reload bookkeeping are unchanged
and precede / follow the modeled decision (mapping.md §1); they are not part of
the spec view and carry no refinement obligation.

## C. No axioms, no A-references, no kind-3 steps

Every step is R or I. The operation that genuinely *changed* — the
migrated/unmigrated verdict — is modeled **deeply** and concretely by `classify`
(steps A2–A4), not hidden behind an axiom about the function under change. There
is **no consumed axiom** and **no deep-model A-reference**: the decision assumes
no callee contract. The discovery helpers (`hasattr`/`getattr`/
`pkgutil.iter_modules`) run before the decision and only produce the four
observations the model takes as free inputs; `axiom_check.py` is therefore a
`status=skip` stub (mapping.md §3). No operation is an inexpressible kind-3.

## D. verify(Solution) ⇒ resolved

`classifyMigrationSources` verifies only if its output equals `classifyAll`,
i.e. each application's verdict is exactly the package-ness / discovered-
emptiness / `ignore_no_migrations` decision with **no dependence on the
namespace flag** (A3 + A4). By R (`MigrationSource` ↔ the four module
observations; `true`/`false` ↔ `migrated_apps`/`unmigrated_apps`) the verified
classifier equals the patched `load_disk` classification on every source; by
G-CONF the R/I transliteration of `classify` agrees with the patched decision —
driven by the real `pkgutil.iter_modules` over real directories — on the full
Boolean matrix + fuzzed migration sets (incl. the F2P namespace-with-migration
case). Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
There are no axiom trust points (G-AX is a skip); the sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF).
