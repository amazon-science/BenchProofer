# refinement.md — django__django-11740

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `alteredFieldDependencies` `do` block, plus the pure helpers `relationDeps`,
`baseDep`, `mkDep` it references) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (a deep model validated == its real callee
by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I; no kind-3
(changed inexpressible op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A-reference leg + this narrative are audited by **G-AX** and **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The function — `generate_altered_fields` (`autodetector.py:904`)

The function iterates over fields that changed between the old and new model
state and emits an `AlterField` operation for each. The patch makes that
operation carry the **ordering dependencies** the new field induces when it
references another model. The patch is three additions to one per-field body:

Gold hunks:
```
+ dependencies = []                                         # line 912: init
  if hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None):
      ...
+     dependencies.extend(self._get_dependencies_for_foreign_key(new_field))   # line 940
  ...
  self.add_operation(
      app_label,
      operations.AlterField(
          model_name=model_name, name=field_name,
          field=field, preserve_default=preserve_default,
-     )
+     ),
+     dependencies=dependencies,                            # line 975: attach
  )
```

| # | Solution.lean impl op (`alteredFieldDependencies`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `isReferential : Bool` | the guard `hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None)` (`autodetector.py:917`) controlling whether `dependencies.extend(...)` runs | R | a field with a `remote_field.model` (FK/O2O/M2M) ↔ `true`; a concrete field ↔ `false` (mapping.md §2). |
| A2 | param `f : RelField` | the touched referential attrs of `new_field` (`remote_field.model._meta.{app_label,object_name}`, the effective explicit through, `swappable_setting`) | R | mapping.md §1–2: only those attributes are modeled; consulted only when `isReferential`. |
| A3 | `let mut deps : List Dep := []` | `dependencies = []` (gold line 912) | I | identical initial empty dependency list. |
| A4 | `if isReferential then deps := relationDeps f` | inside the `remote_field.model` block: `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` (gold line 940) | I + A-reference | **the fixed op.** The extend runs only on the referential branch (I, ↔ the `isReferential` guard); `relationDeps` is the deep model of `_get_dependencies_for_foreign_key` (A-reference, §B / mapping.md §3.1). On the non-referential branch the extend never runs, so `dependencies` stays `[]`. |
| A5 | `return deps` (the value attached to the operation) | `dependencies=dependencies` passed to `add_operation` (gold line 975), where it becomes `operation._auto_deps` | R | `add_operation` stores the list as `_auto_deps`; the migration's `dependencies` are computed from `_auto_deps` (mapping.md §1). The 4-tuple ↔ `Dep` bijection (mapping.md §2). |

Discriminating content of the change — when the new field references another
model, the altered-field operation gains the dependencies on that model (and on
an explicit through model). The pre-patch code attached **no** dependencies,
which is the reported bug (`ValueError: Related model 'testapp2.App2' cannot be
resolved` — the migration was ordered without the dependency). `Solution_prepatch.lean`
reproduces that (the referential branch leaves `deps` empty) and **fails** the
frozen `out = if isReferential then relationDeps f else []` clause (G-DIFF)
precisely on the `isReferential = true` arm.

## B. No consumed axiom; one A-reference

`alteredFieldDependencies` consumes no `axiom`. The patch adds a *call* to the
**unchanged** method `_get_dependencies_for_foreign_key`; that method is modeled
**deeply** by `relationDeps` (with `baseDep`/`mkDep`), an A-reference validated
`relationDeps == _get_dependencies_for_foreign_key` by G-AX over boundary + fuzz
relational fields (FK, O2O, auto-through M2M, explicit-through M2M, swappable
FK). There is no dead axiom and no axiom about the function under change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* —
attaching the field's reference-induced dependencies to its altered-field
operation — is concrete control/data flow (the `[]` init, the referential guard,
the attach), modeled directly (I/R) over the deeply-modeled callee
(A-reference). Nothing is hidden behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`alteredFieldDependencies` verifies only if its output equals
`if isReferential then relationDeps f else []`, which on the referential branch
attaches the dependencies the field induces (A4). By R (`field` referential attrs
↔ `RelField`, the referential guard ↔ `isReferential`, the 4-tuple ↔ `Dep`,
`_auto_deps` ↔ the returned list) the verified output equals the gold patch's
attached `dependencies` on the tested inputs; by G-AX the deep model
`relationDeps` equals the real `_get_dependencies_for_foreign_key` (A-reference);
by G-CONF the R/I transliteration of the whole per-field body agrees with the
patched `generate_altered_fields`' attached dependencies on ≥10⁵ fuzzed field
configurations (and DISAGREES on the unpatched repo — the bug). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model fidelity
(G-AX, `relationDeps == _get_dependencies_for_foreign_key`) and refinement
fidelity (this doc, G-EQ + G-CONF).
