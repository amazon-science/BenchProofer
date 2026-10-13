# mapping.md — django__django-14999

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a754b82dac511475b6276039471ccd17cc64aeb8`, states the type
abstraction, and records callee/control-flow provenance.

Repo file under change: `django/db/migrations/operations/models.py` (the
`RenameModel` operation).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renameSchedule (beforeTable, afterTable, relations)` | `RenameModel.database_forwards(self, app_label, schema_editor, from_state, to_state)` — `django/db/migrations/operations/models.py:319` | the modeled changed function: the schedule of schema operations the model-rename emits |
| `beforeTable` (Int) | `old_model._meta.db_table` — body of `database_forwards`, captured post-patch at `:323` | the stored table identifier BEFORE the rename |
| `afterTable` (Int) | `new_model._meta.db_table` — post-patch `:324` | the stored table identifier AFTER the rename |
| `relations` (List Int) | the dependent relations actually rewritten by the body, in iteration order: `old_model._meta.related_objects` (`:330`, the foreign keys pointing at the model) followed by the auto-created, non-self-referential m2m link tables from `zip(old_model._meta.local_many_to_many, new_model._meta.local_many_to_many)` (`:349`; the loop `continue`s on self-referential fields and non-auto-created `through` models, so those are NOT elements of `relations`) | the dependent relations; their PRESENCE is what makes the noop case discriminating (the pre-patch bug rewrites them even on an unchanged table), and on the proceeding branch the spec pins one rewrite entry PER relation, in relation order (see §2 row 3). |
| `mainMove` (= 1) | `schema_editor.alter_db_table(new_model, old_db_table, new_db_table)` — post-patch `:329` | the main-table move, always emitted FIRST on the proceeding branch |
| `relationOps relations` ((2::) per relation) | the dependent-relation rewrite loops (`:330-368`): one rewrite group per relation — an `schema_editor.alter_field(...)` per FK `related_object`, or the `alter_db_table` + `alter_field` pair per auto-created m2m link table | a per-relation marker fold: each relation's rewrite GROUP is one schedule entry (code 2, distinct from the main move's code 1). The spec pins the proceeding-branch schedule EXACTLY: `mainMove :: relationOps relations` — the main move first, then one entry per dependent relation in order. Only the per-group internal SQL shape (how many `execute` calls one `alter_field` issues) is abstracted many-to-one. |

The gold patch's new lines (`old_db_table`/`new_db_table` locals at `:323-324`
and the guard `if old_db_table == new_db_table: return` at `:325-326`) are the
early-return that makes the operation inert when the table identifier is
unchanged. `database_backwards` (`:371`) swaps the names and delegates to
`database_forwards`, so it inherits the same noop behaviour (modeled by the same
function — its forward/backward symmetry is observed by the F2P test).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `db_table` name (a `str`) | `Int` identity | only the EQUALITY of the before/after table names is observable to the schema layer (`alter_db_table` and the whole `database_forwards` branch decide on `old_db_table == new_db_table`); two ints are equal iff the two names are equal. No other property of the name is used (no indexing, slicing, content inspection), so a richer `List Char` carrier would add proof burden with no behavioural gain. |
| the dependent relations (`related_objects` + auto-created m2m link tables), each a rich Django object | one element of a `List Int` | only the COUNT and per-element existence matter to the emitted schedule; element identity is irrelevant, so each relation is one opaque list slot. |
| ALL the schema work emitted on the proceeding branch (the `alter_db_table` main move plus every dependent-relation rewrite group — many `execute(...)` SQL emissions) | the `List Int` `mainMove :: relationOps relations` | one schedule entry per REWRITE GROUP: entry 1 (`mainMove`) is the main-table `alter_db_table`; each subsequent entry (code 2) is one dependent relation's rewrite group (the FK `alter_field`, or the m2m `alter_db_table`+`alter_field` pair). The spec pins the proceeding-branch schedule EXACTLY as `mainMove :: relationOps relations`: main move first, then one entry per relation in iteration order. The remaining many-to-one abstraction is only WITHIN a group (one group ↔ its 1–2 `alter_*` calls / several SQL statements); a group is emitted iff its entry is present, so an impl that skips the main move, skips or duplicates a relation's rewrites, or reorders the move after the rewrites does NOT satisfy the spec. The F2P-observable noop (`assertNumQueries(0)`) is clause 1's `out = []`. |
| `database_backwards` (name-swap then delegate, `:371-377`) | the same `renameSchedule` invoked with swapped table identifiers | name-swap is observationally a relabeling of `old_db_table`/`new_db_table`; equality is preserved (symmetric), so the noop verdict is identical. |

## 3. Callee provenance and the (absent) axiom inventory

**No consumed axiom, no A-reference.** The behaviour under specification —
whether the rename emits ANY schema work — is decided entirely by the
table-identity comparison, which is precisely the behaviour the gold patch
CHANGES (it adds the early-return guard). Per SPEC_GUIDE §0.7 / §3 the changed
operation must NEVER be axiomatized or A-referenced; it is modeled DEEPLY in
`Solution.lean` (the `if beforeTable = afterTable` early-return branch). The
proceeding branch is modeled as `mainMove :: relationOps relations` and the spec
pins that schedule EXACTLY (main move first, one entry per dependent relation in
order), so a verifying impl must perform the full rename work — not merely some
of it. There is no unchanged stdlib/utility callee whose contract the proof
consumes; the `axioms` region is empty, there is no `axiom_check.py`, and **G-AX
SKIPS**.

### 3.1 Fidelity of the deep model (established by G-DIFF + G-RESOLVE, not G-AX)
Because the discriminating change is the operation under specification, its
fidelity to the real post-patch code is NOT checked by an axiom_check against a
callee (that would unsoundly run against base code, where the noop still emits
schema ops — the original mistagging that this bundle removes). It is instead
established by the static + resolve gates at **per-rewrite-group schedule**
granularity (empty on the noop; main move then one entry per relation when
proceeding):

- **noop case** (`db_table` fixed, so the pre- and post-rename `_meta.db_table`
  are equal, with a dependent FK present): the deep model's empty schedule
  (clause 1, `out = []`). The gold patch makes `database_forwards` a TRUE full
  no-op here (`if old_db_table == new_db_table: return` skips the main move AND
  every dependent-relation/m2m rewrite), so this is faithful to the PATCHED
  code. `Solution_prepatch.lean` — which runs the relation-rewrite fold
  unconditionally — FAILS clause 1, so G-DIFF sees the bug.
- **changed case** (auto table name changes on rename): the deep model's exact
  schedule (clause 2, `out = mainMove :: relationOps relations`); the real
  method emits the main-table move first and then one rewrite group per
  dependent relation, in iteration order — exactly the pinned shape. The gold
  patch leaves this branch byte-identical to pre-patch, and hidden P2P tests
  (`test_rename_model_with_m2m`, `test_rename_m2m_target_model`, self-ref m2m,
  RenameField-then-RenameModel) DO observe that the rewrites actually happen,
  so pinning the full per-relation schedule (not merely non-emptiness) is what
  makes verify ⇒ resolve hold.

`schema_editor.alter_db_table`'s own internal `old_db_table == new_db_table`
short-circuit (`django/db/backends/base/schema.py:470-473`) is why the
**pre-patch** main-table move was already inert when the table is unchanged —
but the pre-patch related-object/m2m rewrites still ran, which is the defect the
gold patch's top-level guard fixes. This is recorded for the refinement audit
(refinement.md), not consumed as an axiom or A-reference.

## 4. G-CONF status — conf_skip=true

The impl region's executable content (the equality guard + the per-relation
fold) is DB-free and input-dependent, but each schedule entry is a per-group
abstraction of real `schema_editor` work (`alter_field` on an FK; the m2m
`alter_db_table`+`alter_field` pair). There is no DB-free oracle that reproduces
the real method's emitted-operation set: the real `database_forwards` requires a
live `schema_editor` bound to a materialized backend (the `alter_field` rewrites
introspect real tables), i.e. the F2P integration test itself. The diff-able
observables (empty schedule on the noop; main-move-then-per-relation schedule on
the proceeding branch) ARE the modeled control flow itself, pinned deeply by the
spec and validated by G-DIFF (the prepatch fails the noop clause) + G-RESOLVE
(the gold patch resolves) — not by any G-AX axiom_check. Per SPEC_GUIDE §0 /
WORKER_PROMPT, `meta.json conf_skip=true` and `conformance_check.py` is a
`status=skip` stub. Soundness rests on G-VERIFY + G-DIFF + G-RESOLVE.

## 5. No fuzz seed / no axiom_check
There is no `axiom_check.py` (the changed operation is modeled deeply, so G-AX
skips per SPEC_GUIDE §0.7). No randomized fuzz seed is required: the
discriminating behaviour is the deterministic schedule outcome (empty on the
noop; `mainMove :: relationOps relations` when proceeding) on the two canonical
configurations the F2P test exercises (noop with FK present; changed
auto-table), exercised by G-DIFF (prepatch) and G-RESOLVE (gold patch).
