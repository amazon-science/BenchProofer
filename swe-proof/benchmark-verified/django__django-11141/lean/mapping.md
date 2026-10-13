# mapping.md — django__django-11141

## Symbol binding (file:line @ base_commit 5d9cf79baf07fc4aed7ad1b06990532a65378155)

- Modeled function: `MigrationLoader.load_disk`, the per-app success branch.
  `django/db/migrations/loader.py:64-124` @ base_commit.
- Lean name `migration_module_status` is a de-narrated alias for that per-app
  classification decision (it does NOT echo the patched repo symbol `load_disk`).

## Lean ↔ Python type bijection (used by G-CONF; G-AX is a skip)

| Lean | Python |
|---|---|
| `hasFile : Bool` | module exposes a non-`None` `__file__` attribute |
| `hasPath : Bool` | module exposes `__path__` (`hasattr(module, '__path__')`) |
| `ignoreNoMigrations : Bool` | `self.ignore_no_migrations` |
| `entries : List (String × Bool)` | `[(name, is_pkg) for _, name, is_pkg in pkgutil.iter_modules(module.__path__)]` |
| `validMigrationName name` | `name and name[0] not in '_~'` |
| `filteredNames entries` | `{name for _,name,is_pkg in iter_modules if not is_pkg and name[0] not in '_~'}` (set ⇒ compared order-independently) |
| `result.migrated` | `app_config.label ∈ self.migrated_apps` |
| `result.names` (as a set) | `{name for (label,name) in self.disk_migrations if label == app_config.label}` |

`hasFile` is an INPUT but does NOT appear in the postcondition's RHS — the fix
makes the classification independent of it (frame directive 5: it is pinned out
by being absent from every result clause, and `correct_*` quantifies over all
`hasFile`).

## Callee provenance + flag deps

- No unchanged callee is consumed as an axiom. `pkgutil.iter_modules`'s output is
  taken as the modeled input `entries`; its behavior is not axiomatized.
- Flag dependency: the `ignore_no_migrations` flag flips the no-files case from
  unmigrated to migrated. G-CONF fuzzes it 50/50.
- Domain note: `pkgutil.iter_modules` never yields an empty module name, and the
  real `load_disk` indexes `name[0]`; the empty-name case is outside the
  discovery domain and is excluded from the G-CONF fuzz pool (the Lean spec still
  total-models it via `validMigrationName "" = false`).

## G-CONF fuzz seed

Pinned seed: `11141` (`random.Random(11141)`), N = 100000.
