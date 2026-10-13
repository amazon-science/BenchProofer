# RELAXED_LEAKAGE — django__django-11141 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition was prescribed by this bundle's own recorded P2 audit
(`verdict.md`, Defect 1): "leakage RELAXED (within the accepted {NO-LEAKAGE,
RELAXED} set) … the leak is a genuinely-unavoidable RELAXED case, not an
avoidable leak. … *Precise fix (no code/spec change; the spec is faithful and
verified):* re-disposition `gates.G-LEAK.status` from `"pass"` to
`"relaxed"` … add `RELAXED_LEAKAGE.md` documenting the leaking tokens, why
unavoidable, and that the `verify ⟹ correct` core is unaffected." The
subsequent re-audit's G-PANEL-3 LEAKAGE verdict found the identical facet
(the same `ignoreMissing`/keep-empty-disjunct lines, the same token-scan
evidence) against the bundle that still lacked this disposition. This file
implements the prescribed fix.

## The mismatch

The gold fix to `MigrationLoader.load_disk`
(`django/db/migrations/loader.py:64` @ base 5d9cf79) is two coupled hunks in
the per-application classification loop:

```python
# hunk 1 — DELETE the namespace short-circuit (the PUBLIC fix):
-    # Empty directories are namespaces.
-    # getattr() needed on PY36 and older (replace w/attribute access).
-    if getattr(module, '__file__', None) is None:
-        self.unmigrated_apps.add(app_config.label)
-        continue

# hunk 2 — make the migrated add CONDITIONAL (the leaking facet):
-    self.migrated_apps.add(app_config.label)
     migration_names = { ... pkgutil.iter_modules(module.__path__) ... }
+    if migration_names or self.ignore_no_migrations:
+        self.migrated_apps.add(app_config.label)
+    else:
+        self.unmigrated_apps.add(app_config.label)
```

The F2P test (`test_loading_namespace_package`) exercises hunk 1: a namespace
package (no `__init__.py`) WITH a migration must load. The hidden P2P tests
`test_load_empty_dir` and `test_marked_as_unmigrated` pin hunk 2's
empty-package behavior: an empty (namespace) migrations dir must land in
`unmigrated_apps`.

The leaking lines in this bundle's spec view (frozen pure region of
`Solution.lean`), all quoting hunk-2 content: the field
`ignoreMissing : Bool` with docstring "the loader is configured to keep a
source that exposes no migrations rather than discard it"
(= `self.ignore_no_migrations`); the classify disjunct
`(!m.migrationNames.isEmpty || m.ignoreMissing)`; and the narration "An
application is classified as migrated exactly when its source is a package
that either has at least one discovered migration, or the loader is told to
keep sources with none." A reader of the spec view alone can reconstruct
gold hunk 2 — this is the dispositioned facet.

## Why the leak is unavoidable

The discriminating content of hunk 2 — that the migrated/unmigrated verdict
becomes CONDITIONAL on the discovered-migrations set being non-empty or the
`ignore_no_migrations` flag — is **absent from the solver-visible
`problem_statement`**:

- The `problem_statement` ("Allow migrations directories without
  `__init__.py` files") is framed PURELY as removing the now-redundant
  `__file__` namespace check (hunk 1): namespace packages lack `__file__` but
  expose `__path__`, and discovery moved to `pkgutil.iter_modules`, so the
  check "is no longer needed, and in fact prevents migrate from working on
  namespace packages."
- Token scan of `problem_statement` (`hints_text` is empty):
  `ignore_no_migrations` = 0, `migration_names` = 0, `migrated_apps` /
  `unmigrated` = 0, `empty` = 0, `keep` = 0, `conditional` = 0. Nothing in
  the public text says how an empty package should be classified or that a
  keep-empty configuration flag enters the decision.

Hunk 2 is a MANDATORY, tested, coupled correctness companion to the public
hunk 1. Pre-patch, the `__file__ is None` short-circuit sent empty namespace
dirs to `unmigrated_apps`. Removing that short-circuit (hunk 1) WITHOUT
hunk 2 lets an empty namespace dir fall through to the unconditional
`self.migrated_apps.add()` and be classified migrated — REGRESSING the P2P
`test_load_empty_dir` (empty dir `migrations.faulty_migrations.namespace`
must be unmigrated). The bundle's own `Solution_prepatch_2.lean`
(unconditional `if isPackage then true`) encodes exactly this regression and
correctly fails against the frozen spec (G-DIFF). So a faithful spec — one
that rejects the always-migrate impl — MUST pin "an empty, not-kept package
is NOT migrated", i.e. the `!migrationNames.isEmpty || ignoreMissing`
decision. A spec derivable from `problem_statement` alone could pin only the
namespace-flag removal (hunk 1) and would admit the always-migrate impl.
Faithful + PS-only-non-leaking is provably impossible here — the definition
of a `problem_statement ↔ gold` mismatch.

Abstracting the names (renaming `ignoreMissing`, de-narrating the docstring)
would not close the leak: the disclosed content is the SEMANTIC decision
structure itself (package-ness ∧ (non-empty ∨ keep-flag)), which any faithful
spec must state; the recorded P2 audit judged this "a genuinely-unavoidable
RELAXED case, not an avoidable leak" and "not merely de-narratable LEAKAGE".

## Core soundness is intact (per the recorded P2 audit of THIS bundle)

- **G-VERIFY: pass** — `Solution.lean` verifies (4.2 s), no sorry, no axioms.
- **G-DIFF: pass** — both prepatches share the byte-identical frozen spec
  (`same_spec = True`) and genuinely fail: `Solution_prepatch.lean` reads
  `isNamespace` (the removed short-circuit) and fails the F2P
  namespace-with-migration clause; `Solution_prepatch_2.lean` adds every
  package unconditionally and fails the empty-package clause.
- **G-EQ: pass (SOUND/TIGHT)** — 7 spec-too-weak attacks re-run, none breaks
  the spec; positive control verifies; no opaque symbol (echo attack
  structurally impossible); no kind-3 refinement steps.
- **G-PANEL-2: FAITHFUL** — the in-container post-gold `load_disk`
  classification branch is verbatim `classify`; G-CONF ran the REAL
  `pkgutil.iter_modules` oracle: 100,018 cases (seed 11141),
  0 disagreements, including the F2P namespace-with-migration case and the
  empty-dir case.
- **G-MUT: 14/14 killed.** **G-CONF: pass** (100,018 / 0). **G-AX: vacuous
  skip** (no axioms, no deep-model references; the decision is pure control
  flow over four free observations). **G-RESOLVE: resolved** (`patch.diff`
  == gold verbatim).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the conditional migrated/unmigrated add — `migration_names or
self.ignore_no_migrations` — that hunk 2 introduces).
