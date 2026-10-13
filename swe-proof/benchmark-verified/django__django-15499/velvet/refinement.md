# refinement.md — django__django-15499

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`reduceManagers` `do` block and the deep model `reduceManagersSpec`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs** (no foreign callee is axiomatized — §C), so G-CONF carries the
full mechanical burden and G-EQ audits only the narrative.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The optimization site — `CreateModel.reduce` (`models.py:136`, new arm 173–185)

Gold hunk (the added `elif` arm):
```
+        elif (
+            isinstance(operation, AlterModelManagers)
+            and self.name_lower == operation.name_lower
+        ):
+            return [
+                CreateModel(
+                    self.name,
+                    fields=self.fields,
+                    options=self.options,
+                    bases=self.bases,
+                    managers=operation.managers,
+                ),
+            ]
```

Modeled method: `reduceManagers`, deep model `reduceManagersSpec`.

| # | Solution.lean impl op (`reduceManagers`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self : ModelCreate` | the `CreateModel` instance `self` whose `.reduce` is called | R | `CreateModel` ↔ `ModelCreate` (mapping.md §2): the five carried components ↔ `name_lower`/`fields`/`options`/`bases`/`managers`. |
| A2 | parameter `op : AlterManagers` | the `operation` argument, here an `AlterModelManagers` | R | `AlterModelManagers` ↔ `AlterManagers` (mapping.md §2): `name_lower`, `managers`. The `isinstance(operation, AlterModelManagers)` guard is discharged by the type of `op` (we model the reducer restricted to this operation kind — the only kind the new arm and the F2P test concern). |
| A3 | `if self.nameLower = op.nameLower then …` | `and self.name_lower == operation.name_lower` | I + R | the same-model guard: case-folded name equality. `name_lower` is `name.lower()` on both sides (mapping.md §2), so the `String` equality is the literal `==` of the arm. |
| A4 | `return ReduceResult.replace [{ self with managers := op.managers }]` | `return [CreateModel(self.name, fields=self.fields, options=self.options, bases=self.bases, managers=operation.managers)]` | I + R | the collapse: a single created op whose `name`/`fields`/`options`/`bases` are `self`'s and whose `managers` are `op`'s. The structure-update `{ self with managers := op.managers }` keeps every component of `self` except `managers`, which it takes from `op` — exactly the gold constructor's argument routing. R: component identity ↔ token (mapping.md §2.1). |
| A5 | `else return ReduceResult.reduceThrough` | falls through every `elif`, reaching `return super().reduce(operation, app_label)` → `can_reduce_through` → `not operation.references_model(self.name, …)` → `True` when the names differ | I + R | a DIFFERENT-model `AlterModelManagers` does not reference this model (`AlterModelManagers.references_model` is `name.lower() == self.name_lower`, inherited from `ModelOperation`, `models.py:29-30`), so `can_reduce_through` returns `True` — the optimizer reorders across it. `True` ↔ `reduceThrough` (mapping.md §2). |

Discriminating content of the change — a SAME-model `AlterModelManagers` now
collapses (`replace [...]`) rather than blocking (the pre-patch
`cannotReduce`). This lives in the `if self.nameLower = op.nameLower` true-branch
returning `replace [{ self with managers := op.managers }]`.
`Solution_prepatch.lean` reproduces the pre-patch fall-through (same-model ⇒
`cannotReduce`) and **fails** `res = reduceManagersSpec self op` exactly on the
`if_pos : self.nameLower = op.nameLower` case (G-DIFF).

## B. Why the pre-patch same-model case is `cannotReduce` (not `reduceThrough`)

Pre-patch, `CreateModel.reduce` has no `AlterModelManagers` arm, so a following
`AlterModelManagers` falls through to `super().reduce` (`ModelOperation.reduce`,
`models.py:32-35`) → `can_reduce_through` (`models.py:37-38`) →
`not operation.references_model(self.name, app_label)`. For a SAME-model
alteration `references_model` is `True` (`models.py:29-30`), so
`can_reduce_through` returns `False` ↔ `cannotReduce`: the two operations cannot
be combined, and the optimizer leaves both standing. That is the bug the issue
reports (the pair is NOT optimized to a single `CreateModel`) and the behavior
the F2P test `test_create_alter_model_managers` flips from "two ops" to "one op".

## C. No kind-3 (inexpressible-changed-op) steps; no A legs

Every step is R or I. The operation that genuinely changed — adding the
same-model collapse arm — is modeled **directly** in the impl + deep model
`reduceManagersSpec`, not behind an axiom. There is no unchanged foreign callee
the proof depends on, so there is **no consumed axiom and no deep-model
reference** (`axioms` region empty; `meta.json axioms=[]`,
`deep_model_references=[]`; G-AX skips). Component identity (`fields`/`options`/
`bases`/`managers`) is an R refinement of Python list-object identity
(mapping.md §2.1), checked by G-CONF.

## D. verify(Solution) ⇒ resolved

`reduceManagers` verifies only if the same-model case returns
`replace [{ self with managers := op.managers }]` (A4) — i.e. a single
`CreateModel` keeping `self`'s fields/options/bases and taking `op`'s managers —
and the different-model case returns `reduceThrough` (A5). No weaker dispatch
(reporting `cannotReduce`, dropping a component, or taking managers from `self`)
satisfies the frozen spec. By R (`CreateModel`↔`ModelCreate`,
`AlterModelManagers`↔`AlterManagers`, component-identity↔token) the verified
reducer equals the patched `CreateModel.reduce(AlterModelManagers(...))` on the
tested inputs; G-CONF refutes any R/I infidelity over fuzzed (creation,
alteration) pairs — same-model and different-model, with matching and
non-matching component objects — by differential execution against the patched
real reducer. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this doc + G-CONF);
there is no axiom trust point for this bundle.
