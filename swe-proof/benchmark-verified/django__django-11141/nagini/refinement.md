# refinement.md — django__django-11141

The operation-by-operation correspondence between `model.py`'s implementation
(`is_migrated_app`, with its pure helper `migrated_code`) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (the proof
uses an axiom's `Ensures`), **A-reference** (a deep model validated == a real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation).

The claim: *any implementation that verifies against this frozen spec, refined
per the map below, classifies each migrations module into migrated/unmigrated
exactly as the gold patch does, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The change site — the `else:` arm of the migrations-loading routine

Gold hunk (`django/db/migrations/loader.py`), the two relevant edits:

```
 else:
-    # Empty directories are namespaces.
-    # getattr() needed on PY36 and older (replace w/attribute access).
-    if getattr(module, '__file__', None) is None:
-        self.unmigrated_apps.add(app_config.label)
-        continue
     # Module is not a package (e.g. migrations.py).
     if not hasattr(module, '__path__'):
         self.unmigrated_apps.add(app_config.label)
         continue
     if was_loaded:
         reload(module)
-self.migrated_apps.add(app_config.label)
 migration_names = {
     name for _, name, is_pkg in pkgutil.iter_modules(module.__path__)
     if not is_pkg and name[0] not in '_~'
 }
+if migration_names or self.ignore_no_migrations:
+    self.migrated_apps.add(app_config.label)
+else:
+    self.unmigrated_apps.add(app_config.label)
```

| # | model.py impl op (`is_migrated_app`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `exposes_search_path: bool` | `hasattr(module, '__path__')` | R | bool ↔ bool, identical truth value (mapping.md §2). |
| A2 | parameter `has_regular_file_marker: bool` | `getattr(module, '__file__', None) is None` (REMOVED guard) | R | bool ↔ bool with negated polarity (mapping.md §2); the model keeps it in the signature precisely so the spec can pin that the result is independent of it (it is absent from the `migrated_code` right-hand side of the postcondition). |
| A3 | parameter `migration_names: List[int]` and its `len(...)` | the `migration_names` set comprehension over `pkgutil.iter_modules(module.__path__)` with the `not is_pkg and name[0] not in '_~'` filter | I + R | the `iter_modules` call and its filter are **identical** pre- and post-patch (kind I, unchanged callee — not modified by this patch, mapping.md §3); the model abstracts its result to a `List[int]` and observes only `len(...) > 0 ⟺ bool(set)` (kind R, mapping.md §2). No axiom is consumed. |
| A4 | parameter `treat_empty_as_migrated: bool` | `self.ignore_no_migrations` | R | bool ↔ bool, identical truth value (mapping.md §2). |
| A5 | `if not exposes_search_path: return 0` | `if not hasattr(module, '__path__'): self.unmigrated_apps.add(...); continue` | I | identical control flow: a non-package short-circuits to unmigrated (`0`). (`reload(module)` when `was_loaded`, `loader.py:97-98`, is omitted: it has no effect on the classification — it re-imports an already-imported package, mutating neither `__path__`-ness nor the discovered names; kind I-elided.) |
| A6 | `if len(migration_names) > 0 or treat_empty_as_migrated: return 1` else `return 0` | `if migration_names or self.ignore_no_migrations: self.migrated_apps.add(...) else: self.unmigrated_apps.add(...)` | I + R | identical boolean structure; `bool(migration_names)` ↔ `len(migration_names) > 0` (R, mapping.md §2); the two `set.add` outcomes ↔ result codes `1`/`0` (R). |
| A7 | `Result()` ∈ {0,1} | membership in `migrated_apps` (1) vs `unmigrated_apps` (0) | R | exactly one set receives the label per application (mapping.md §2). |

Every step is R or I — there is **no kind-3** (changed-but-inexpressible) step
and **no consumed axiom**. The genuinely changed operations (dropping the
`__file__` guard A2/A5; splitting the classification by discovered-name count
A6) are modelled deeply with primitive Nagini constructs.

## B. The two independently-fixed behaviours and their failing prepatches

The patch makes two independently-observable behavioural changes; SPEC_GUIDE
requires one verification-failing `model_prepatch_<k>` per change. The frozen
spec is byte-identical across `model.py`, `model_prepatch.py`,
`model_prepatch_2.py` (G-DIFF `same_spec`); only the impl region differs.

### B1 — dropping the `__file__` guard (`model_prepatch.py`)
Pre-image isolating the removed guard: it reintroduces
`if not has_regular_file_marker: return 0` **before** the count check, then
classifies correctly. It **fails** the postcondition
`Result() == migrated_code(exposes_search_path, len(migration_names),
treat_empty_as_migrated)` on the discriminating input
`has_regular_file_marker == False, exposes_search_path == True,
len(migration_names) > 0` — i.e. an **implicit namespace package that contains
migrations**: the prepatch returns `0` (unmigrated) where the spec requires `1`
(migrated). This is exactly the F2P scenario `test_loading_namespace_package`
(`tests/migrations/test_loader.py`): a migrations directory without
`__init__.py` (no `__file__`) holding `0001_initial.py` must be loaded; the old
guard sent it to `unmigrated_apps` so `0001_initial` was never discovered and
`forwards_plan(('migrations','0001_initial'))` raised. The new code reaches the
`iter_modules` discovery and classifies it migrated.

### B2 — classifying empty packages (`model_prepatch_2.py`)
Pre-image isolating the old unconditional `self.migrated_apps.add(...)`: for any
package exposing a search path it returns `1` unconditionally, ignoring the
discovered-name count and the tolerate flag. It **fails** the same postcondition
on the discriminating input `exposes_search_path == True,
len(migration_names) == 0, treat_empty_as_migrated == False`: it returns `1`
(migrated) where the spec requires `0` (unmigrated). This is the behaviour
that keeps `test_load_empty_dir` / the namespace-with-no-migrations case in
`unmigrated_apps`: post-patch an empty package (no discovered migration names,
`ignore_no_migrations` false) is unmigrated, so the `__file__` guard's old job
of rejecting empty namespace directories is now done by the count check
instead. The PASS_TO_PASS tests `test_marked_as_migrated` (a package WITH a
migration → migrated) and `test_marked_as_unmigrated` (`MIGRATION_MODULES`
disabled) bracket both branches.

## C. verify(model) ⇒ resolved

`is_migrated_app` verifies only if its result equals the exact outcome
`migrated_code(exposes_search_path, len(migration_names),
treat_empty_as_migrated)` (A6, the postcondition), independent of
`has_regular_file_marker` (A2 — the postcondition fixes `Result()` without
referencing the marker, since `migrated_code` does not take it, so no verifying
impl can let the marker change the classification). By the R-refinements above this
is precisely the gold patch's decision: a successfully-imported package is
added to `migrated_apps` iff it has discovered migration names or
`ignore_no_migrations`, regardless of `__file__`; a non-package or empty-non-
tolerated package goes to `unmigrated_apps`. The `iter_modules` discovery (A3)
is unchanged (kind I), so it is neither axiomatized nor a deep-model reference;
there are no trust points beyond the standard refinement-fidelity audit
(G-EQ) — no axiom soundness (G-AX) is involved because no axiom is consumed.
The gold patch resolves (G-RESOLVE), so the verified model, refined per this
map, resolves.
