# refinement.md — django__django-16595

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `reduceAlterField` `do` block and the `reduceDecision` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reduction decision — `AlterField.reduce()` (`django/db/migrations/operations/fields.py:249-257`)

Gold hunk:
```
-        if isinstance(operation, RemoveField) and self.is_same_field_operation(
-            operation
-        ):
+        if isinstance(
+            operation, (AlterField, RemoveField)
+        ) and self.is_same_field_operation(operation):
             return [operation]
         elif (
             isinstance(operation, RenameField)
```

`AlterField.reduce(operation, app_label)` decides how this field alteration
combines with the operation `operation` that immediately follows it in the
migration operation list (the surrounding `MigrationOptimizer.optimize` loop —
`optimizer.py` — is unchanged infrastructure). The first `if` branch returns
`[operation]` — the two collapse onto the later operation alone, the earlier
alteration being redundant. The patch widens the kind test of that first branch
from `RemoveField` only to `(AlterField, RemoveField)`; the `is_same_field_operation`
guard and the `return [operation]` body are unchanged, as are the `elif`
(`RenameField`) branch and the `return super().reduce(...)` fall-through.

| # | Solution.lean impl op (`reduceAlterField`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `op : ReduceInput` | the `operation` argument of `reduce` (the following migration operation) | R | one following operation ↔ one `ReduceInput`, summarized by the three booleans the reducer's first branch consults (mapping.md §2). |
| A2 | `op.incomingIsAlter` | `isinstance(operation, AlterField)` (the **added** kind in the widened tuple) | R + I | the kind test ↔ `incomingIsAlter` (mapping.md §2). The single behavioural change — admitting a following alteration into the collapsing branch — modeled identically. G-AX exercises the real `isinstance` dispatch. |
| A3 | `op.incomingIsRemove` | `isinstance(operation, RemoveField)` (the kind already in the pre-patch tuple) | R + I | the kind test ↔ `incomingIsRemove` (mapping.md §2). Unchanged by the patch. |
| A4 | `op.sameField` | `self.is_same_field_operation(operation)` (`fields.py:24`) | R + I | same model (case-insensitive) AND same field name (case-insensitive) ↔ `sameField` (mapping.md §2). Unchanged callee, fixed semantics, exercised by G-AX/G-CONF. |
| A5 | `reduceDecision op = if (incomingIsAlter ∨ incomingIsRemove) ∧ sameField then keepLater else deferToInherited` | the first `if (...): return [operation]` branch vs the `elif`/`super().reduce(...)` fall-through | I | the first branch's post-patch condition `isinstance(operation, (AlterField, RemoveField)) and is_same_field_operation(operation)` is exactly the disjunction-of-kinds conjoined with `sameField`; reaching it yields `keepLater` (`return [operation]`), and not reaching it leaves the pre-existing dispatch (`deferToInherited`). The boolean string of conjuncts is spelled out identically. mapping.md §1. |
| A6 | `out = reduceDecision op` | the reducer's return value, classified to "collapse onto the later operation" vs "anything else" | R | `keepLater` ↔ the reducer returns exactly `[operation]`; `deferToInherited` ↔ any other return (the `RenameField` 2-element list, `super().reduce`'s list/`[self]`/bool). The desired behaviour only distinguishes those two outcomes, so the carrier is the binary `ReduceResult` (mapping.md §2). |

Discriminating content of the change — a following operation that is **another
alteration of the same model field** (`incomingIsAlter ∧ sameField`,
`¬incomingIsRemove`) collapses onto the later operation (`applies = keepLater`)
because the widened kind test now admits `AlterField`. This lives in the
`incomingIsAlter` disjunct of `reduceDecision`. The pre-patch first branch tested
`RemoveField` only, so a following same-field alteration fell through to the
pre-existing dispatch (which does not combine two same-field alterations);
`Solution_prepatch.lean` reproduces that removal-only first branch and **fails**
`out = reduceDecision op` (G-DIFF) precisely when `incomingIsAlter ∧ sameField ∧
¬incomingIsRemove` holds — the F2P scenario `test_alter_alter_field`.

## B. The `deferToInherited` outcome is not an axiom

`ReduceResult.deferToInherited` is a deliberately **abstract tag**, not an
axiomatized callee. The proof asserts nothing about which concrete value the
pre-existing dispatch returns; it only asserts that the modeled decision matches
`reduceDecision` (collapse iff the first branch fires). The concrete behaviour of
the unchanged `elif` (`RenameField`) branch and the `super().reduce(...)`
fall-through is irrelevant to the desired change and is left entirely to G-CONF,
which runs the **real** reducer and classifies every non-`[operation]` return as
`deferToInherited`. There is therefore no consumed axiom (A-consumed) and no
deep-model reference (A-reference): nothing is claimed about a callee's value, so
G-AX has no `ensures` to validate (it confirms the no-axiom claim and the fixed
semantics of the `isinstance` dispatch + `is_same_field_operation`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the first
branch's kind test widening from `RemoveField` to `(AlterField, RemoveField)` —
is modeled **identically** (`reduceDecision`'s `incomingIsAlter` disjunct, step
A5), not hidden behind an axiom. `isinstance` and `is_same_field_operation` are
Python/Django builtins with fixed semantics, refined to the `ReduceInput`
booleans per mapping.md §2 and exercised on real operation objects by G-AX and
G-CONF.

## D. verify(Solution) ⇒ resolved

`reduceAlterField` verifies only if its output equals, on every observable input,
the exact post-patch decision `reduceDecision` (A5) — in particular collapsing a
following same-field **alteration** onto the later operation (A2: `incomingIsAlter`
admitted into the first branch). By R (the following operation ↔ `ReduceInput`,
the two `isinstance` tests + `is_same_field_operation` ↔ the three booleans,
collapse-vs-defer ↔ the `ReduceResult` tag) the verified decision equals the
return-value classification of the patched `AlterField.reduce` on the tested
inputs; by G-CONF the R/I transliteration of `reduceDecision` agrees with the
real patched reducer's observable on ≥10⁵ fuzzed real operation pairs, and
disagrees on the unpatched reducer exactly at the same-field-alteration case
(falsifiability). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). Trust points reduce to refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness leg (no axioms).
