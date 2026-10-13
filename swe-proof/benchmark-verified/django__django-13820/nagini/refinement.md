# refinement.md — django__django-13820

The operation-by-operation correspondence between `model.py`'s implementation
(`treat_as_migration_source`, plus the deep `is_source` decision) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The classification site — `MigrationLoader.load_disk` (`django/db/migrations/loader.py:90-99`)

Gold hunk (the `else:` arm of the successful-import branch). Pre-patch:
```python
# Empty directories are namespaces.
# getattr() needed on PY36 and older (replace w/attribute access).
if getattr(module, '__file__', None) is None:
    self.unmigrated_apps.add(app_config.label)
    continue
# Module is not a package (e.g. migrations.py).
if not hasattr(module, '__path__'):
    self.unmigrated_apps.add(app_config.label)
    continue
```
Post-patch:
```python
# Module is not a package (e.g. migrations.py).
if not hasattr(module, '__path__'):
    self.unmigrated_apps.add(app_config.label)
    continue
# Empty directories are namespaces. Namespace packages have no
# __file__ and don't use a list for __path__. See
# https://docs.python.org/3/reference/import.html#namespace-packages
if (
    getattr(module, '__file__', None) is None and
    not isinstance(module.__path__, list)
):
    self.unmigrated_apps.add(app_config.label)
    continue
```
Both arms fall through to `self.migrated_apps.add(app_config.label)` and
`pkgutil.iter_modules(module.__path__)` (the module IS a migration source) when
no `continue` fires.

| # | model.py impl op (`treat_as_migration_source`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `is_package: bool` | `hasattr(module, '__path__')` | R | a real module's attribute query refines to its truth value; `True` ⇔ the module is a package (mapping.md §2). The `not hasattr(...)` guard returning the skip outcome ⇔ `if not is_package: return False`. |
| A2 | parameter `file_is_set: bool` | `getattr(module, '__file__', None) is not None` | R | attribute query → truth value; `not file_is_set` ⇔ `getattr(module, '__file__', None) is None` (mapping.md §2). The patch keeps this exact sub-test; it only conjoins a second condition. |
| A3 | parameter `path_is_ordinary_list: bool` | `isinstance(module.__path__, list)` | R | attribute/type query → truth value; `True` ⇔ the package's child-search location is a built-in `list` (a regular package), `False` ⇔ the custom iterable of a PEP-420 namespace package (mapping.md §2, §3). This is the conjunct the patch ADDS. Soundness of the regular-vs-namespace discrimination is validated in-container by axiom_check.py (R-pkg/list). |
| A4 | `if not is_package: return False` | `if not hasattr(module, '__path__'): ... continue` (skip) | I | identical boolean control flow under R(A1): non-package ⇒ skipped. (The patch evaluates the package check FIRST; the model mirrors that order.) |
| A5 | `if (not file_is_set) and (not path_is_ordinary_list): return False` | `if (getattr(module, '__file__', None) is None and not isinstance(module.__path__, list)): ... continue` (skip) | I | identical boolean control flow under R(A2,A3): a package with no source-file location AND a non-list child-search location ⇒ skipped (the namespace-package case). |
| A6 | `return True` (fall-through) | fall-through to `self.migrated_apps.add(...)` / `iter_modules(module.__path__)` | I | identical: any module not skipped by A4/A5 is a migration source. The `bool` result `True`/`False` ⇔ the migrated/unmigrated outcome (mapping.md §1). |

The discriminating content of the change — a regular package whose `__file__` is
`None` but whose `__path__` IS a `list` — is the `(is_package=True,
file_is_set=False, path_is_ordinary_list=True)` row. The new logic (A4–A6)
returns `True` (migration source); the pre-patch logic rejected it on the
unguarded `__file__ is None` test. `model_prepatch.py` reproduces the pre-patch
skeleton (`if not file_is_set: return False` *before* the package check, with no
list conjunct) and **fails** the postcondition
`Result() == is_source(is_package, file_is_set, path_is_ordinary_list)` on
exactly that row — the spec sensing the change (G-DIFF). This is the case the
F2P test `test_loading_package_without__file__` exercises (a regular package
with `__file__` deleted must still load `['0001_initial', '0002_second']`).

## B. No consumed axioms; no kind-3 steps

Every step above is R or I. There is **no `@ContractOnly` axiom** the proof
consumes (A-consumed) and **no deep-model reference** validated as a real-callee
substitute (A-reference): the entire changed operation is boolean predicate
logic over three observable module facts, modelled deeply as `bool` algebra
(`is_source` + the skeleton). The three attribute-introspection primitives
(`hasattr`, `getattr`, `isinstance`) are *unchanged* Python builtins refined to
their truth values (kind R, A1–A3) — they are not callees the patch changes, so
there is nothing to axiomatize. No operation in the impl is a *changed* op that
Nagini cannot express; hence no kind-3 step (none would be permitted).

`axiom_check.py` therefore checks no axiom contract (there is none). It instead
validates the two R-refinement facts in-container against the live Python import
system (G-AX as an R-soundness oracle): (R-pkg/list) `isinstance(__path__, list)`
discriminates regular packages (`True`) from PEP-420 namespace packages
(`False`); (R-decision) the boolean decision table equals the real `load_disk`
classification on all eight `(is_package, file_is_set, path_is_ordinary_list)`
combinations, including the discriminating frozen-environment case.

## C. verify(model) ⇒ resolved

`treat_as_migration_source` verifies only if its result equals
`is_package and (file_is_set or path_is_ordinary_list)` (the postcondition,
A6/`is_source`), i.e. only if a package with no source-file location but an
ordinary-list child-search location is classified as a migration source (the
fourth postcondition clause, the discriminating row). By R (A1–A3: module
attribute queries ↔ their truth values) the verified skeleton equals the gold
classification block on every module the F2P/P2P tests construct; A4–A6 are
identical boolean control flow. The two trust points of PLAN §1.1 reduce here to
refinement fidelity only (this document, G-EQ) — there is no axiom-soundness
point, since no axiom is consumed; axiom_check.py corroborates the R-refinements.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to the boolean-fact refinement — and the gold patch resolves
(G-RESOLVE).
