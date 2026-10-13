# mapping.md — django__django-11141

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5d9cf79baf07fc4aed7ad1b06990532a65378155`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/db/migrations/loader.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `classifyMigrationSources (sources : List MigrationSource)` | `MigrationLoader.load_disk` — `django/db/migrations/loader.py:64` (changed body lines 84–104) | the modeled changed function: the per-application loop that records each app as migrated / unmigrated |
| `classify (m : MigrationSource)` | the post-patch decision recorded for one `app_config` inside the `for app_config in apps.get_app_configs()` loop's `else` branch | pure spec: migrated-vs-unmigrated verdict for one application's migration source |
| `classifyAll (sources : List MigrationSource)` | the verdict for every application, in `apps.get_app_configs()` order | pure spec: the per-application classification list |
| `MigrationSource.isPackage` | `hasattr(module, '__path__')` on the imported migrations module (`loader.py:87` post-patch) | the module exposes a package search path |
| `MigrationSource.isNamespace` | `getattr(module, '__file__', None) is None` on the imported module (`loader.py:85` PRE-patch read; **removed** by the patch) | the module is an implicit namespace package (no single backing file) |
| `MigrationSource.migrationNames` | the comprehension `{name for _, name, is_pkg in pkgutil.iter_modules(module.__path__) if not is_pkg and name[0] not in '_~'}` (`loader.py:92–95` post-patch) | the migration member modules discovered under the package's search path |
| `MigrationSource.ignoreMissing` | `self.ignore_no_migrations` (`loader.py:46`, `__init__` arg, default `False`) | the loader is configured to keep a source that exposes no migrations |

The model carries `isNamespace` as a *structure field* (a free observation) but
`classify` does NOT read it: that is the directive-5 frame point — the patch's
behavioral content is precisely that the namespace observation no longer gates
the verdict. A wrong impl that reads it (the true pre-patch) cannot satisfy the
frozen spec (G-DIFF, `Solution_prepatch.lean`).

Repo facts NOT modeled (they precede the modeled `else` branch and are unchanged
by the patch — refinement audit only, not the consumer spec view): the
`migrations_module(...) is None` skip (`loader.py:73`); the `ImportError`
handling and `was_loaded`/`reload` bookkeeping (`loader.py:76–90`); and the
inner `for migration_name in migration_names` body that builds
`disk_migrations` (`loader.py:97–110`). None of these touch the
migrated/unmigrated classification the patch changes.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo facts. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| one application's imported migrations module + loader config | `MigrationSource` | a record of the four observations the classification reads (below) |
| `hasattr(module, '__path__')` | `isPackage : Bool` | Python truthiness ↔ `Bool` |
| `getattr(module, '__file__', None) is None` | `isNamespace : Bool` | Python truthiness ↔ `Bool` (carried but unused by `classify`) |
| the discovered migration-name set | `migrationNames : List String` | a Python `set[str]` ↔ a `List String`; only its *emptiness* is observed (`migration_names or ...` is a truth test on the set), so order/multiplicity are irrelevant — `set` non-empty ↔ `!l.isEmpty` |
| `self.ignore_no_migrations` | `ignoreMissing : Bool` | `bool` ↔ `Bool` |
| "app is recorded migrated" (`self.migrated_apps.add(label)`) vs "unmigrated" (`self.unmigrated_apps.add(label)`) | the `Bool` verdict (`true` = migrated) | the loop adds the label to exactly one of the two disjoint sets; `true ↔ migrated_apps`, `false ↔ unmigrated_apps` |
| the whole-loop result (`apps.get_app_configs()` order) | `List Bool` | per-application verdict, in registry order |

The modeled `else`-branch verdict only fires for sources that reached the
`else` (a successfully imported module). `classify` returns `false` for a
non-package (`isPackage = false`) — matching the `not hasattr(module,
'__path__')` → `unmigrated_apps` early step that survives the patch (it is the
remaining guard before the classification).

## 3. Callee provenance

**No axioms and no deep-model A-references.** The patch's behavioral content is
pure control flow over four already-computed observations (package-ness, the
discovered-migrations emptiness, the `ignore_no_migrations` flag, and — for the
pre-patch only — the namespace flag). It calls no library function whose
contract the proof must assume: `hasattr`/`getattr`/`pkgutil.iter_modules` all
execute *before* the modeled decision and only produce the observations, which
the model takes as free inputs. There is therefore nothing for G-AX to check;
`axiom_check.py` is a `status=skip` stub and `meta.json axioms = []`,
`deep_model_references = []`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11141`** so the
consumer-side verdict is reproducible. The shadow transliterates `classify`
(the R/I op); the oracle is the patched decision read directly from the
post-patch `load_disk` logic (the harness applies `patch.diff` before G-CONF
runs). Both sides range over the full `(isPackage, isNamespace,
migrationNames-empty?, ignoreMissing)` Boolean matrix plus fuzzed migration-name
sets, including the F2P case (a namespace package that exposes a migration).
