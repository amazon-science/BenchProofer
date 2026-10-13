# refinement.md — django__django-14999

The operation-by-operation correspondence between `Solution.lean`'s `impl`
region (`renameSchedule` + the `relationOps` fold) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** (proof uses
an axiom's `ensures`), or **I** (identical concrete operation modeled deeply).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

**No A-reference, no consumed axiom.** The behaviour the patch changes — gating
all schema work on table-identity equality — is the operation under
specification itself. Per SPEC_GUIDE §0.7 / §3 you must NEVER axiomatize or
A-reference the operation the patch CHANGES; it is modeled DEEPLY in
`Solution.lean` (the `if beforeTable = afterTable` early return ⇒ `out = []`) and
its fidelity is established by G-VERIFY + G-DIFF + G-RESOLVE, not by a G-AX
axiom_check against the (unchanged) base callee. There is therefore no
`axiom_check.py` and the `axioms` region is empty; G-AX SKIPS.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

**Discriminating behaviour and how strongly each branch is specified.** The gold
patch's only behavioural change is the early-return guard: when the stored table
identifier is unchanged the operation must be a NOOP (emit zero schema
operations). The *changed-table* branch is **byte-identical to pre-patch**, but
it is NOT unobserved: hidden P2P tests (`test_rename_model_with_m2m`,
`test_rename_m2m_target_model`, `test_rename_model_with_self_referential_m2m`,
"RenameModel renames a many-to-many column after a RenameField") assert that the
dependent-relation/m2m rewrites actually happen when the rename proceeds. A spec
that only demanded a non-empty schedule would admit an implementation that moves
the main table and skips every dependent-relation rewrite — such an
implementation translates to a patch that passes the F2P noop test but FAILS
those P2P tests (this exact wrong-impl/patch pair was produced by the P1 audit
and confirmed non-resolving). The spec therefore pins the proceeding branch
EXACTLY at per-rewrite-group granularity: `out = mainMove :: relationOps
relations` — the main-table move first, then one entry per dependent relation in
iteration order. The remaining abstraction is only WITHIN a group (one schedule
entry ↔ the 1–2 `alter_*` calls that relation's rewrite comprises).

## A. The change site — `RenameModel.database_forwards` (`django/db/migrations/operations/models.py:319`)

Gold hunk:
```
 if self.allow_migrate_model(schema_editor.connection.alias, new_model):
     old_model = from_state.apps.get_model(app_label, self.old_name)
+    old_db_table = old_model._meta.db_table
+    new_db_table = new_model._meta.db_table
+    # Don't alter when a table name is not changed.
+    if old_db_table == new_db_table:
+        return
     # Move the main table
-    schema_editor.alter_db_table(
-        new_model,
-        old_model._meta.db_table,
-        new_model._meta.db_table,
-    )
+    schema_editor.alter_db_table(new_model, old_db_table, new_db_table)
     # Alter the fields pointing to us
     for related_object in old_model._meta.related_objects:
         ...
```

| # | Solution.lean impl op (`renameSchedule`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `beforeTable : Int` | `old_db_table = old_model._meta.db_table` | R | `db_table` name → `Int` identity; only `==` is observable (mapping.md §2). |
| A2 | param `afterTable : Int` | `new_db_table = new_model._meta.db_table` | R | as A1, the post-rename table identifier. |
| A3 | param `relations : List Int` | the dependent relations iterated: `old_model._meta.related_objects` + auto-created m2m link tables (`zip(local_many_to_many)`) | R | each rich relation object → one opaque `List Int` slot; only count/existence matters (mapping.md §2). |
| A4 | `if beforeTable = afterTable then return []` | `if old_db_table == new_db_table: return` | I | identical concrete control flow: equality test on the two identifiers, early return emitting nothing. The empty `[]` ↔ "no schema operation issued". |
| A5 | `else { … while-fold building relationOps; return mainMove :: result }` (the schedule `mainMove :: relationOps relations` on the not-equal branch) | `schema_editor.alter_db_table(new_model, old_db_table, new_db_table)` plus the dependent-relation rewrite loops (`for related_object …: alter_field(…)`; `for (old_field, new_field) …: alter_db_table/alter_field(…)`) | R + I | Identical concrete control flow on the not-equal branch: proceed to emit the main move FIRST, then one rewrite group per dependent relation in iteration order, modeled DEEPLY as the `mainMove :: relationOps relations` fold — and the postcondition pins the schedule EXACTLY to that value. The TYPE abstraction is per-group (one schedule entry ↔ one relation's 1–2 `alter_*` calls); presence, count, and order of the groups are all pinned. This matters because hidden P2P tests (m2m/FK rename tests) observe that the rewrites actually run when the rename proceeds: an impl that emitted only some of the work would translate to a P2P-breaking patch. No A-reference and no consumed axiom: this is the changed operation, modeled deeply (SPEC_GUIDE §0.7). |

The discriminating content of the change — that the dependent-relation rewrites
are SUPPRESSED when the table identifier is unchanged — lives in clause (1)
`beforeTable = afterTable → out = []`. The pre-patch code lacked the top-level
guard, so on an unchanged table it still ran the dependent-relation loops (the
main move was already inert via `alter_db_table`'s own equality short-circuit,
`schema.py:470-473`). `Solution_prepatch.lean` reproduces exactly that: it runs
the `relationOps` fold UNCONDITIONALLY and only gates the main move by the
equality test, so on equal tables it returns a schedule equal to
`relationOps relations` — and **fails** clause (1) `beforeTable = afterTable →
out = []` whenever a dependent relation exists (the F2P scenario has the
`Pony.rider` FK; the unsolved goal is exactly `result_1 = []` with
`result_1 = relationOps (drop 0 relations)`). That is the spec sensing the
change (G-DIFF). The reproduced defect is purely the missing NOOP guard; the
prepatch and model agree on the changed branch (both emit `mainMove ::
relationOps relations`), which is correct — that branch is not what the gold
patch changed.

## B. `database_backwards` (`:371`)

Gold: unchanged by the patch. `database_backwards` swaps `old_name`/`new_name`
and delegates to `database_forwards`, so it inherits the noop. Modeled by the
SAME `renameSchedule` with the table identifiers swapped (equality is symmetric,
so the verdict is identical). The F2P test asserts `assertNumQueries(0)` for
backwards too; because it delegates to the changed function, its noop behaviour
is the SAME deeply-modeled discriminating clause (not a separate callee to
A-reference). No separate `Solution_prepatch_<k>` is needed: forwards and
backwards share the single discriminating clause (the empty schedule on equal
tables), and the prepatch already exercises it.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely changed — gating ALL
schema work on table-identity inequality — is modeled DEEPLY (the
`if beforeTable = afterTable` early-return branch [A4, kind I]); there is **no
consumed axiom** (the `axioms` region is empty) and **no A-reference** (per
SPEC_GUIDE §0.7 the changed operation must not be axiomatized or A-referenced —
there is no `axiom_check.py`, and G-AX skips). The proceeding branch (main move +
relation rewrites) is modeled as `mainMove :: relationOps relations` [A5, kind
I]; the postcondition pins the schedule exactly to that value, so a verifying
impl must emit the main move and every per-relation rewrite group, in order —
the property the hidden P2P rename tests observe. Its faithfulness is
established by G-VERIFY
(the deep model verifies) + G-DIFF (the prepatch, lacking the guard, fails the
noop clause) + G-RESOLVE (the gold patch resolves), not by any G-AX check.

## D. verify(model) ⇒ resolved

`renameSchedule` verifies only if (1) it emits `[]` when `beforeTable =
afterTable` (the noop) and (2) it emits EXACTLY `mainMove :: relationOps
relations` otherwise (the main-table move first, then one rewrite group per
dependent relation in order). By R (db_table name → int identity; one schedule
entry ↔ one rewrite group) the verified outcome matches what the gold
`database_forwards` emits on the tested inputs: zero schema operations when
`db_table` is fixed (the F2P `assertNumQueries(0)` for both forwards and
backwards), and the full main-move-plus-per-relation rewrite schedule otherwise
(observed by the hidden P2P rename tests: `test_rename_model_with_m2m`,
`test_rename_m2m_target_model`, self-referential m2m, and
RenameField-then-RenameModel all assert the dependent rewrites actually happen).
Clause 2's exactness is what closes the P1 hole: a spec demanding only a
non-empty schedule admits an impl that emits the main move but skips the
dependent-relation rewrites, which translates to a patch that passes the F2P
noop test yet fails those P2P tests (a verifying-but-non-resolving patch, the
recorded G-EQ break). The remaining abstraction — within one group, how many
`alter_*`/SQL calls it comprises — is not something any impl admitted by the
spec can vary, since the group is opaque (one entry) at the model level. The
match is established and shown discriminating by G-DIFF: `Solution_prepatch.lean` (which
runs the relation-rewrite fold unconditionally, lacking the early-return guard)
FAILS the noop clause `beforeTable = afterTable → out = []` whenever a dependent
relation is present, exactly the pre-patch defect; the gold patch resolves
(G-RESOLVE). There is no G-AX/axiom_check obligation here — the changed operation
is modeled deeply, so G-AX skips (SPEC_GUIDE §0.7). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this document, G-EQ); there is no axiom-soundness trust
point because no axiom is consumed, and no A-reference trust point because the
changed operation is modeled deeply (G-AX skips, per SPEC_GUIDE §0.7).
