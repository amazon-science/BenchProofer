# mapping.md — django__django-13820

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 98ad327864aed8df245fd19ea9d2743279e11643`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/db/migrations/loader.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `treat_as_migration_source(is_package, file_is_set, path_is_ordinary_list)` | the per-module classification block inside `MigrationLoader.load_disk` — `django/db/migrations/loader.py:90-99` (the `else:` arm of the `import_module` try) | the modeled changed function: does a successfully-imported candidate module become a migrations source (loaded) or get skipped (added to `unmigrated_apps`)? |

The classification block decides, for a module that imported successfully, between
two outcomes:

* **skipped** — `self.unmigrated_apps.add(app_config.label); continue` (the
  module contributes no migrations);
* **migration source** — falls through to `self.migrated_apps.add(...)` and
  `pkgutil.iter_modules(module.__path__)` (its migrations are loaded).

`treat_as_migration_source` returns `True` for the migration-source outcome and
`False` for the skipped outcome.

## 2. Type abstraction (R-refinements)

The block performs three runtime introspections on the imported `module`
object. Each is a *fact about the module* that Nagini models as a `bool`
parameter (R — type refinement of an opaque module attribute query to its truth
value):

| repo reality (on `module`) | model carrier | bijection |
|---|---|---|
| `hasattr(module, '__path__')` — is the module a package (vs. a plain `.py` module like `migrations.py`)? | `is_package: bool` | `True` ⇔ the module exposes a `__path__`; a non-package has none |
| `getattr(module, '__file__', None) is not None` — does the module carry a source-file location? | `file_is_set: bool` | `True` ⇔ `__file__` is present and non-`None`; `False` ⇔ absent or `None` (e.g. a frozen-environment regular package, or a PEP-420 namespace package) |
| `isinstance(module.__path__, list)` — is `__path__` an ordinary `list`? | `path_is_ordinary_list: bool` | `True` ⇔ `__path__` is a built-in `list` (every regular package); `False` ⇔ a custom iterable, the marker of a PEP-420 namespace package, whose `__path__` is a `_NamespacePath` (a CPython implementation detail, hence tested structurally by `isinstance(..., list)` rather than by exact type) |

`path_is_ordinary_list` is only observed when `is_package` is `True` (the real
code reads `module.__path__` only after confirming the module is a package).
The model's precondition mirrors this: `path_is_ordinary_list` is required to be
`False` when `is_package` is `False` (a non-package exposes no `__path__`, so the
list-ness question is vacuous; pinning it to `False` keeps the input space
faithful and does not affect the non-package outcome, which is `False`
regardless).

No `str`, no `float`, no sequence: the entire changed operation is boolean
predicate logic over these three facts, so it is modeled deeply as `bool`
algebra with no abstraction gap.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

**There are NO consumed `@ContractOnly` axioms.** The changed operation is a
boolean decision over three module facts; it is modeled deeply (spelled-out
boolean logic over `bool`), not behind any axiom. The three module-introspection
primitives are *unchanged* builtins refined to their truth values (kind R, §2),
not callees the patch changes:

* `hasattr(m, '__path__')` → `is_package` — Python builtin, unchanged.
* `getattr(m, '__file__', None) is None` → `not file_is_set` — Python builtin,
  unchanged; the patch keeps this exact test, it only adds a second conjunct.
* `isinstance(m.__path__, list)` → `path_is_ordinary_list` — Python builtin,
  unchanged; this is the conjunct the patch *adds*. Its semantics (a regular
  package's `__path__` is a built-in `list`; a namespace package's is not) is
  the documented CPython import-system behavior:
  https://docs.python.org/3/reference/import.html#namespace-packages
  ("Namespace packages do not use an ordinary list for their `__path__`
  attribute. They instead use a custom iterable type ...").

`axiom_check.py` does NOT need to fuzz a callee contract (there is none).
Instead it validates, in-container, the two refinement facts the bundle relies
on against the live Python import system (G-AX as an R-soundness oracle):

* **(R-pkg/list)** a *regular* package built and imported normally has
  `isinstance(module.__path__, list) is True` (and `hasattr(__path__)`), and a
  *PEP-420 namespace* package has `isinstance(module.__path__, list) is False` —
  so `path_is_ordinary_list` discriminates regular from namespace packages
  exactly as the model assumes;
* **(R-decision)** the boolean decision table of `treat_as_migration_source`
  matches the real `load_disk` classification on all eight `(is_package,
  file_is_set, path_is_ordinary_list)` combinations, including the
  discriminating frozen-environment case `(True, False, True)` which the F2P
  test `test_loading_package_without__file__` exercises (a regular package whose
  `__file__` has been deleted must still be loaded as a migration source).
