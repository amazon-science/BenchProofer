# mapping.md — django__django-11141

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5d9cf79baf07fc4aed7ad1b06990532a65378155`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/db/migrations/loader.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo construct (file:line @ base_commit) | role |
|---|---|---|
| `is_migrated_app(has_regular_file_marker, exposes_search_path, migration_names, treat_empty_as_migrated) -> int` | the per-application classification block inside the migrations-loading routine `django/db/migrations/loader.py:86-103` (the `else:` arm after a successful `import_module`, through the `migrated_apps`/`unmigrated_apps` decision) | the modeled changed code: it decides, for one successfully-imported migrations module, whether its application lands in `self.migrated_apps` (result `1`) or `self.unmigrated_apps` (result `0`) |
| `migrated_code(exposes_search_path, discovered_file_count, treat_empty_as_migrated)` *(@Pure helper)* | the post-change decision expression `if migration_names or self.ignore_no_migrations: self.migrated_apps.add(...) else: self.unmigrated_apps.add(...)` (`loader.py:91-103` post-patch) combined with the package guard | pure spec: the classification outcome code (the file marker is absent from it, pinning marker-independence) |
| `exposes_search_path` (param) | `hasattr(module, '__path__')` (`loader.py:93`) | whether the imported module is a package exposing a search path |
| `has_regular_file_marker` (param) | `getattr(module, '__file__', None) is None` (`loader.py:89`, the guard that is REMOVED) — `has_regular_file_marker == True` ⟺ `__file__` is present | whether the package carries a conventional on-disk file attribute; `False` for an implicit namespace package |
| `migration_names` (param, `List[int]`) | the set comprehension `{ name for _, name, is_pkg in pkgutil.iter_modules(module.__path__) if not is_pkg and name[0] not in '_~' }` (`loader.py:100-103`) | the discovered, already-filtered migration module names; only its cardinality bears on the classification |
| `treat_empty_as_migrated` (param) | `self.ignore_no_migrations` (`loader.py:91` post-patch; attribute set in `__init__`, `loader.py:47`) | the loader flag asking that a package with no discovered migrations still count as migrated |
| `Result()` ∈ {0, 1} | membership in `self.unmigrated_apps` (0) vs `self.migrated_apps` (1) | the classification outcome |

The pre-patch repo lines the change removes / relocates (for the refinement
audit, not referenced from the consumer spec view):
- the `getattr(module, '__file__', None) is None` guard and its
  `self.unmigrated_apps.add(...) ; continue` body (`loader.py:87-91`);
- the unconditional `self.migrated_apps.add(app_config.label)` at the old
  `loader.py:99`, relocated post-patch into the new
  `if migration_names or self.ignore_no_migrations` / `else` split.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `hasattr(module, '__path__')` (bool) | `exposes_search_path: bool` | identical truth value |
| `getattr(module, '__file__', None) is None` (bool) | `has_regular_file_marker: bool` (negated polarity) | `has_regular_file_marker == not (getattr(module,'__file__',None) is None)`; namespace package ⟺ `has_regular_file_marker == False` |
| `self.ignore_no_migrations` (bool) | `treat_empty_as_migrated: bool` | identical truth value |
| the discovered migration-name `set` (a Python `set` of `str`) | `migration_names: List[int]` | the classification observes only `bool(set)` ⟺ `len(set) > 0`; the carrier is a `List[int]` whose `len(...)` mirrors `len(set)`. Element identity is irrelevant to the modeled decision, so any in-bijection encoding of the names as ints suffices (`str` indexing is banned in Nagini; the names' contents do not influence the classification). |
| `self.migrated_apps.add(label)` / `self.unmigrated_apps.add(label)` followed by an implicit `continue`-to-next-app | the function returning `1` / `0` | the two mutually-exclusive `set.add` outcomes are encoded as the two result codes; for one application exactly one branch fires, so the function is total and single-valued |

`migration_names` is **read-only**: the classification never mutates it. It is
required and ensured at `Acc(list_pred(migration_names), 1/2)` (SPEC_GUIDE
directive 5), and its sequence content is ensured unchanged
(`ToSeq == Old(ToSeq)`), so no wrong impl can satisfy the postcondition
vacuously by overwriting the input.

## 3. Callee provenance

No `@ContractOnly` axiom is consumed and no deep-model A-reference is used.
The classification is modelled **deeply** over concrete booleans and the
length of the discovered-name collection — every operation is a primitive
Nagini construct.

The one library callee the surrounding repo code invokes,
`pkgutil.iter_modules(module.__path__)` together with the filtering
comprehension (`not is_pkg and name[0] not in '_~'`), is **identical pre- and
post-patch** (`loader.py:100-103` in both images). The patch neither changes
that call nor its filter; it only changes (a) whether the `__file__` guard
runs before it and (b) how the resulting name set is classified. The model
therefore takes the already-discovered name collection as an opaque input
(`migration_names`) rather than re-deriving it — this is a kind-`I`
(identical, unchanged) step in refinement.md, not an axiom. Consequently there
are no axioms for G-AX to check, and no `axiom_check.py` is shipped (the
WORKER_PROMPT requires one only when axioms exist).

Background on why the `__file__` guard is safe to drop (the problem statement's
own rationale, public): migration-file discovery moved to
`pkgutil.iter_modules`, which walks `module.__path__`; implicit namespace
packages (PEP 420, Python 3+) have a `__path__` but no `__file__`, so the old
`__file__` check spuriously rejected them while `iter_modules` handles them
fine. The classification therefore depends on `__path__` (here
`exposes_search_path`), never on `__file__` (here `has_regular_file_marker`).
