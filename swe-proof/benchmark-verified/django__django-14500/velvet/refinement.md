# refinement.md — django__django-14500

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `recordUnappliedKeys` `do` block) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — none here),
or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the observed effect, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The recording site — `unapply_migration()` (`django/db/migrations/executor.py:246`)

Gold hunk (the recording block, lines 253–258):
```
-        # For replacement migrations, record individual statuses
+        # For replacement migrations, also record individual statuses.
         if migration.replaces:
             for app_label, name in migration.replaces:
                 self.recorder.record_unapplied(app_label, name)
-        else:
-            self.recorder.record_unapplied(migration.app_label, migration.name)
+        self.recorder.record_unapplied(migration.app_label, migration.name)
```
Effect of the change: the migration's **own** key
`(migration.app_label, migration.name)` is recorded as unapplied
**unconditionally** — for a squashed/replacement migration in *addition* to its
replaced keys, where pre-patch it was recorded *only* in the `else` (no-replaces)
branch.

| # | Solution.lean impl op (`recordUnappliedKeys`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `m : Migration` (`replaces`, `appLabel`, `name`) | the `migration` object's `replaces` / `app_label` / `name` attributes | R | rich object ↔ structure with only the touched fields (mapping.md §1, §2). |
| A2 | the backward `while` fold prepending each `m.replaces[i-1]!`, yielding `m.replaces` as a prefix | `if migration.replaces: for app_label, name in migration.replaces: self.recorder.record_unapplied(app_label, name)` | I | the replaced-key loop; record-call ↔ list element, order preserved (mapping.md §2, §3). The `if migration.replaces:` guard is subsumed: an empty `replaces` contributes an empty prefix, identical to skipping the loop. |
| A3 | the initial `result := [(m.appLabel, m.name)]` (the own key), appearing last after the fold prepends the replaced keys ⇒ `out = m.replaces ++ [(m.appLabel, m.name)]` | the **unconditional** `self.recorder.record_unapplied(migration.app_label, migration.name)` (post-patch; the removed `else`) | I | the own key recorded after the replaced keys, in every case. This is the changed behavior; record-call ↔ appended list element (mapping.md §2, §3). |

The discriminating content of the change — the own key is recorded **even when
`replaces` is non-empty** — lives in the postcondition
`out = m.replaces ++ [(m.appLabel, m.name)]` (the own key is appended
unconditionally). `Solution_prepatch.lean` reproduces the pre-patch control flow
(own key only in the `replaces = []` branch) and **fails** that postcondition on
any migration with a non-empty `replaces` (G-DIFF) — exactly the F2P squash
scenario `test_migrate_marks_replacement_unapplied`.

## B. No axioms / no deep-model references

This bundle consumes **no axioms** and ships **no A-reference deep model**. The
only callee at the change site, `recorder.record_unapplied`, is an unchanged
sink modeled directly as a list append (an I-op): its sole observable for this
effect is the key it is called with, in order, and the model records exactly
that. No contract about it is *consumed* by the proof, so an axiom would be dead
(SPEC_GUIDE §3, §7). Consequently `axiom_check.py` is absent and **G-AX skips**.
The unchanged `fake` / `schema_editor` / `progress_callback` machinery is
orthogonal to the recorded-key observable and is held fixed by G-CONF
(`fake=True`, no progress callback) — see mapping.md §3.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — recording the
migration's own key unconditionally rather than only in the no-replaces branch —
is expressed **directly** in the `do` block (the own key is the seed of the
fold and survives unconditionally into the result), not hidden behind an axiom.
There is no axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`recordUnappliedKeys` verifies only if its output equals
`m.replaces ++ [(m.appLabel, m.name)]` (A3): the replaced keys in order followed
by the migration's own key, **unconditionally**. By R (rich-object ↔ touched
fields; record-call sequence ↔ list) the verified recording equals the gold
patch's `record_unapplied` call sequence on every migration; by G-CONF the R/I
transliteration agrees with `patch.diff`'s real behaviour over ≥10⁵ fuzzed
inputs (including the squash scenario), 0 disagreements. There are no axioms, so
the only trust point is refinement fidelity (this doc + G-CONF). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE).
