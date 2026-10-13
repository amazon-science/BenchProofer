# refinement.md — django__django-15973

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `relationDependencies` `do` block, plus the pure helpers `baseDep`,
`relationDeps`, `resolveRef` it references) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (a deep model validated ==
its real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A,
or I; no kind-3 (changed inexpressible op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A-reference leg + this narrative are audited by **G-AX** and **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The function — `_get_dependencies_for_foreign_key` (`autodetector.py:1397`)

The function builds a `dependencies` list for one relational `field`:
1. resolve the base dependency on the model the field points to (swappable
   setting, or `resolve_relation(remote_field_model, …)`);
2. if the relation is routed through an intermediary model
   (`field.remote_field.through`), append a SECOND dependency for that
   intermediary.

Gold hunk (the single changed line, inside step 2):
```
   if getattr(field.remote_field, "through", None):
       through_app_label, through_object_name = resolve_relation(
-          remote_field_model,                 # the model the field POINTS TO
+          field.remote_field.through,         # the INTERMEDIARY model
           app_label,
           model_name,
       )
```

| # | Solution.lean impl op (`relationDependencies`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `f : RelField` | the `field` argument's touched attrs (`remote_field.model`, `remote_field.through`, `swappable_setting`) | R | mapping.md §1–2: only the three relevant attributes are modeled. |
| A2 | params `appLabel`, `modelName : String` | `app_label`, `model_name : str` | R | `str` ↔ Lean `String`, identity. |
| A3 | `baseDep f appLabel modelName` (swappable branch ⇒ `__setting__`/setting, else `mkDep (resolveRef f.target …)`) | the base-dependency block: `if swappable_setting is not None: (__setting__, setting)` else `resolve_relation(remote_field_model, …)`, then `dependencies = [(…, None, True)]` | I + A-reference | the swappable test and tuple shape are concrete (I); `resolveRef` is the deep model of `resolve_relation` (A-reference, §3.1). `remote_field_model == field.remote_field.model == f.target` on the modeled path (mapping.md §2). |
| A4 | `match f.through with \| none => [d]` | `if getattr(field.remote_field, "through", None):` false ⇒ `dependencies` unchanged (one entry) | I | absence of a through model ⇒ no second dependency; the `getattr(..., None)`-falsy test ↔ `f.through = none`. |
| A5 | `\| some thr => [d, mkDep (resolveRef thr appLabel modelName)]` | through present ⇒ `resolve_relation(field.remote_field.through, app_label, model_name)` appended as `(…, None, True)` | I + A-reference | **the fixed op.** The second dependency is resolved from the INTERMEDIARY reference `thr` (= `field.remote_field.through`), not from `f.target` (= `remote_field_model`). `resolveRef` is the deep model of `resolve_relation` (A-reference). The append + 4-tuple shape are concrete (I). |

Discriminating content of the change — the through dependency is resolved from
`field.remote_field.through` (the intermediary) rather than `remote_field_model`
(the target the field points to). When the intermediary lives in a DIFFERENT app
(the issue's `fonte_variavel` / the F2P's `contract`), the two references resolve
to different `app_label`s, so the dependency set differs. `Solution_prepatch.lean`
reproduces the bug (resolves the through dep from `f.target`) and **fails** the
frozen `out = relationDeps f appLabel modelName` clause (G-DIFF) precisely on the
`some thr` arm.

## B. No consumed axiom; one A-reference

`relationDependencies` consumes no `axiom`. The sole foreign callee
`resolve_relation` is modeled **deeply** by `resolveRef` (an A-reference,
validated `resolveRef == resolve_relation` by G-AX over boundary + fuzz). There
is no dead axiom and no axiom about the function under change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
choice of which model reference feeds the through-dependency resolution — is a
concrete data-flow edit (`f.target` → `thr`), modeled directly (I) over the
deeply-modeled resolver (A-reference). Nothing is hidden behind an axiom about
the function under change.

## D. verify(Solution) ⇒ resolved

`relationDependencies` verifies only if its output equals `relationDeps`, which,
on the `some thr` arm, resolves the through dependency from the intermediary
`thr` (A5). By R (`field` attrs ↔ `RelField`, `str` ↔ `String`, tuple ↔ `Dep`)
the verified output equals the gold patch's `dependencies` list on the tested
inputs; by G-AX the deep model `resolveRef` equals the real `resolve_relation`
(A-reference); by G-CONF the R/I transliteration of the whole function agrees
with the patched `_get_dependencies_for_foreign_key` on ≥10⁵ fuzzed field
configurations. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the one audited callee — and the
gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1:
deep-model fidelity (G-AX, `resolveRef == resolve_relation`) and refinement
fidelity (this doc, G-EQ + G-CONF).
