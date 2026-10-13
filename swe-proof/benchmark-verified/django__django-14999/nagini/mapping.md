# mapping.md — django__django-14999

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a754b82dac511475b6276039471ccd17cc64aeb8`, states the type
abstraction, and records callee/control-flow provenance.

Repo file under change: `django/db/migrations/operations/models.py` (the
`RenameModel` operation). Line numbers below are POST-patch (i.e. the worktree at
`base_commit` with `patch.diff` applied) unless marked otherwise, because that is
the reference for the modeled function.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line) | role |
|---|---|---|
| `rename_schema_schedule(before_table, after_table, column_relations, link_relations)` | `RenameModel.database_forwards(self, app_label, schema_editor, from_state, to_state)` — `django/db/migrations/operations/models.py:319` | the modeled changed function: the ordered schedule of schema operations the model-rename REQUESTS of the schema layer, ONE ENTRY PER REQUEST |
| `before_table` (int) | `old_db_table = old_model._meta.db_table` — `:323` (pre-patch: `old_model._meta.db_table` read inline at `:325`) | the stored table identifier BEFORE the rename |
| `after_table` (int) | `new_db_table = new_model._meta.db_table` — `:324` (pre-patch: inline at `:326`) | the stored table identifier AFTER the rename |
| `column_relations` (List[int]), used by its POSITIONS | every `old_model._meta.related_objects` entry — the `for` at `:331`, whose body issues ONE `alter_field` (`:344-348`) | the COLUMN relations: a column in some other table that reaches the renamed model. One request each. Position `i` IS the `i`-th `related_objects` entry: the model does not care what a relation is, but it does care WHICH one a request operates on. |
| `link_relations` (List[int]), used by its POSITIONS | every many-to-many of `zip(old_model._meta.local_many_to_many, new_model._meta.local_many_to_many)` (`:350`) that the `for` at `:351` does not `continue` past (`:353-354`) | the LINK relations: an auto-created link table standing behind one of the renamed model's many-to-many relations. TWO requests each — the link table's own move (`:358-362`) and the rewrite of the column inside it (`:365-369`). Position `j` is the `j`-th such m2m in visiting order. |
| `OP_MAIN_MOVE` (`= -1`) | `schema_editor.alter_db_table(new_model, old_db_table, new_db_table)` — `:329` | the one request that relocates the renamed model's OWN table. Negative, so it can never be confused with a dependent request. |
| a schedule entry `i` with `0 <= i < len(column_relations)` | the `schema_editor.alter_field(model, related_object.field, to_field)` of the `related_objects` iteration visiting column relation `i` (`:344-348`) | one entry ↔ one column relation's rewrite. |
| a schedule entry `nc + 2*j` (`nc = len(column_relations)`) | `schema_editor.alter_db_table(new_m2m_model, old_m2m_model._meta.db_table, new_m2m_model._meta.db_table)` — `:358-362` — of the iteration visiting link relation `j` | the MOVE of link relation `j`'s own link table. |
| a schedule entry `nc + 2*j + 1` | `schema_editor.alter_field(new_m2m_model, old_m2m_model._meta.get_field(...), new_m2m_model._meta.get_field(...))` — `:365-369` — of that SAME iteration | the rewrite of the column INSIDE that same link table. Its code is the successor of the move's, so the schedule carries the order between the two. |
| the result `List[int]` | the ORDER in which the method issues those requests | the observable. `database_forwards` returns nothing and everything it does it asks `schema_editor` to do, so the schedule of requests is the behaviour. |

The gold patch's new lines (`old_db_table`/`new_db_table` at `:323-324` and the
guard `if old_db_table == new_db_table: return` at `:325-327`) are the early
return that makes the operation inert when the table identifier is unchanged.
`database_backwards` (`:371`) swaps the names and delegates to
`database_forwards` (`:375`), so it inherits both the inert case and the schedule
shape (modeled by the same function with the identifiers swapped; the F2P test
observes both directions and `axiom_check.py` drives both).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `db_table` name (a `str`) | `int` identity | only the EQUALITY of the before/after table names is observable to the branch under specification (`:326` decides on `old_db_table == new_db_table`); two ints are equal iff the two names are equal. No other property of the name is used — no indexing, slicing or content inspection occurs — so a richer string carrier would add proof burden with no behavioural gain. |
| one COLUMN relation (a rich `ForeignObjectRel`) | one POSITION of `column_relations` | the identity of a relation is irrelevant (the model never reads the list's values), but WHICH relation a request operates on is not, so a request names a position. Position `i` is the `i`-th `related_objects` entry in the order the real method visits them (`:331`). |
| one LINK relation (a `ManyToManyField` whose `through` is auto-created) | one POSITION of `link_relations`, owning the TWO codes `nc + 2*j` and `nc + 2*j + 1` | the two requests of `:358-362` and `:365-369` operate on two DIFFERENT things — a table, and a column inside that table — so they are two schedule entries, and the order between them is part of the observable. The `continue` at `:353-354` is part of this row: a self-referential m2m (already covered by the `related_objects` pass) and a user-supplied `through` table (not the renamed model's to move) are NOT link relations of the collection. |
| the requests the method makes of the schema layer, in order — `alter_db_table` / `alter_field` calls on `schema_editor` | the result `List[int]`: `OP_MAIN_MOVE`, a `column_relations` position, or one of the two codes of a `link_relations` position | ONE ENTRY PER REQUEST, in issue order. One caveat, deliberate and measured at exactly this granularity by axiom_check.py / conformance_check.py: a request is what the method ASKS FOR, not what the database executes — `alter_db_table` short-circuits internally when the two names it is handed are equal (`django/db/backends/base/schema.py:470-473`) and `alter_field` may expand into a table rebuild that re-enters `alter_db_table`, and neither is part of this observable (the harnesses count TOP-LEVEL requests only). An earlier revision of this bundle merged a link relation's two adjacent requests into ONE entry; that granularity made the order between them unobservable, and G-EQ refuted the spec through exactly that hole (see refinement.md §F). |
| the ORDER of the dependents among THEMSELVES | NOT pinned | the real order is whatever `related_objects` / `local_many_to_many` happen to yield; every dependent request is addressed to the renamed model's table after that table has already moved, and distinct dependents address disjoint tables/columns, so any order of the column relations, any order of the link relations, and any interleaving of the two is a correct rename. properties.py `pos-control-reverse-column-order`, `pos-control-link-block-first`, `pos-control-links-descending` and `pos-control-moves-then-inner-rewrites` hold the spec to leaving all of that free (the last three on one concrete dependent shape each — see refinement.md "The observable" section on why, and on the reject cases that share those shape guards and so prove the branch is reached). |
| the order of the two requests INSIDE one link relation | PINNED (clause 6) | not free, and for a repo-level reason: `:365-369` addresses `new_m2m_model` — the link table under its NEW name — so it must follow the `:358-362` that puts the table there. Asking for the column rewrite first addresses a table that is not there yet; and on sqlite, where `alter_field` rebuilds the table, the deferred move then relocates a table whose column still names the identifier the renamed model no longer uses. |
| `database_backwards` (name-swap then delegate, `:371-378`) | the same `rename_schema_schedule` invoked with swapped table identifiers | the name swap is observationally a relabeling of `old_db_table`/`new_db_table`; the delegation means the schedule is produced by the same code. |

## 3. Callee provenance and the (absent) axiom inventory

**No consumed `@ContractOnly` axiom.** The behaviour under specification — which
schema operations the rename requests, and in which order — is decided entirely
by the table-identity comparison and by the iterations over the two dependent
collections, all modeled DEEPLY in `model.py` (the `if before_table ==
after_table` early return and the two loops). There is no unchanged
stdlib/utility callee whose contract the proof consumes.

### 3.1 Deep model ↔ real `database_forwards` (A-reference)
The deep model is validated against the REAL, post-patch
`RenameModel.database_forwards` / `database_backwards` by `axiom_check.py`
(G-AX), which records the requests the real method makes — wrapping
`alter_db_table` / `alter_field` on the live editor and counting only TOP-LEVEL
calls, since the sqlite backend re-enters its own `alter_field`/`alter_db_table`
while rebuilding a table and those nested calls are the schema layer's business,
not requests the rename made. NOTHING is merged: one entry per request.

- **noop case** (`db_table` fixed via `options={'db_table': 'rider'}`, so the
  pre- and post-rename `_meta.db_table` are equal, with a dependent FK
  `Pony.rider` AND an auto-created `Rider.stables` link table present — i.e. one
  column relation and one link relation): the real method requests **nothing at
  all** and collects **0** SQL, for both `database_forwards` and
  `database_backwards` — matching the deep model's empty schedule (clause 1).
- **changed case** (the same scenario, the same models and dependents, with ONLY
  the post-rename `db_table` reassigned so the two identifiers differ): the real
  method's recorded schedule is **`[-1, 0, 1, 2]`** forwards and **`[-1, 0, 1,
  2]`** backwards — the move of the model's own table FIRST, then the column
  relation's rewrite, then the link table's move (`1`), then the rewrite of the
  column inside that link table (`2`): `1 + 1 + 2*1` requests and nothing else,
  with each link table moved BEFORE the column inside it is rewritten. That is
  clauses (2), (3), (4), (5) and (6) read directly off the real method.
- **discrimination**: the two cases differ in nothing but the equality of the two
  identifiers, so the empty schedule of the first is attributable to the identity
  comparison rather than to an absence of dependent work — the same dependents
  demonstrably DO get their requests when the identifiers differ.
- **non-vacuity of the order clauses**: the clause-(2)/(6) checkers are re-run on
  two MUTANTS of the schedule just observed — one with the leading main move
  moved to the end, one with a link relation's two requests swapped — and G-AX
  fails unless BOTH are rejected. Without that control an order clause that
  inspected nothing would pass silently.

Imports are Django + stdlib only — the very package the patch edits. Exit 0 iff
every observation matches the deep model.

`schema_editor.alter_db_table`'s own internal `old_db_table == new_db_table`
short-circuit (`django/db/backends/base/schema.py:470-473`) is why the
**pre-patch** main-table move emitted no SQL when the table was unchanged — but
the pre-patch dependent rewrites still ran, which is the defect. This is
recorded for the refinement audit (refinement.md §D), not consumed as an axiom.

## G-CONF — differential conformance (`conformance_check.py`)

**Pinned fuzz seed: `SEED = 14999`** (module constant in
`conformance_check.py`). Input count: **101194** checks — 18 boundary + 1176
exhaustive sweep + 100000 seeded fuzz.

**Shadow.** The `# impl-start` / `# impl-end` region of `rename_schema_schedule`,
copied verbatim as `shadow_rename_schema_schedule` minus exactly two mechanical
deletions forced by this file being plain Python rather than Nagini: the
`Invariant(...)` calls (with their `# invariants-start`/`-end` markers) and the
`# type:` annotation comment. There is no `Requires`/`Ensures`/`Assert`/`Acc`
call inside the impl region — they all sit in the pre/post-condition regions
above it — so the control flow, the two loops and the emission ORDER are
byte-for-byte the model's. The `# pure-start` constant (`OP_MAIN_MOVE`) is copied
too. No `@Pure` helper, no `@ContractOnly` callee (§3: the axioms region is
empty), and no `PSeq` — the carriers are plain `int` / `List[int]`, so no
sequence shim is needed.

**Oracle: CALLED, not transliterated.** The real patched
`RenameModel.database_forwards` (`:319`) and `database_backwards` (`:371`),
driven under `connection.schema_editor(collect_sql=True)` over an in-memory
sqlite backend whose tables have first been created with `editor.create_model`.
That runs the whole real method — main move, every `related_objects`
`alter_field`, and, per m2m, the link table's own `alter_db_table` AND the
`alter_field` on the column inside it. (The velvet sibling ships a `conf_skip`
stub and lean transliterates, both on the grounds that the proceeding branch
needs a live `schema_editor`; that is true, and the live editor turns out to be
constructible in-container, so no transliteration is required here.) The script
applies no patch — the gate applies `patch.diff` to `/testbed` and
`PYTHONPATH=/testbed` resolves the patched module — and it asserts via
`inspect.getsource` that the guard the patch introduces is present, so an
unpatched oracle errors rather than passing.

**Type bridge (§2 inverted).**

| §2 row | model carrier | concrete realization |
|---|---|---|
| 1 | `before_table` / `after_table` (`int`) | an index into the **injective** pool `TABLE_NAMES` (7 distinct names, including `''`), assigned onto `_meta.db_table` of the two state-rendered model classes around each call and restored after. Injectivity is the row's content: it makes the model's `before_table == after_table` equivalent to the real guard's `old_db_table == new_db_table`. |
| 2 | `column_relations` (`List[int]`, one POSITION per column relation) | `n_fk` models carrying a `ForeignKey` to the renamed model (→ `related_objects`). Position `i` is bound to entry `i` of `canonical_dependents(...)[0]`, which mirrors the real visiting order (`:331`). |
| 2 | `link_relations` (`List[int]`, one POSITION per link relation) | `n_m2m` `ManyToManyField`s declared **on** the renamed model (→ the auto-created link tables in `zip(...local_many_to_many)`, `:350`). Position `j` is bound to entry `j` of `canonical_dependents(...)[1]`, i.e. the `j`-th m2m the method does not `continue` past. The sweep enumerates every `(n_fk, n_m2m)` in `0..3 × 0..2`, and a bridge self-check fails the run unless every shape realizes exactly the pair it claims. |
| 3 | the result `List[int]` | the real method's own requests, recorded by wrapping `alter_db_table`/`alter_field` on the live editor and keeping only TOP-LEVEL calls (the sqlite table rebuild re-enters those methods; a depth counter excludes it). **Nothing is merged** — a link relation's `alter_db_table` and `alter_field` are two entries. Each is mapped to the model's carrier: `OP_MAIN_MOVE` for a move of a non-link table; `columns.index(...)` for an `alter_field` on a non-link table; `nc + 2*j` / `nc + 2*j + 1` for a move of / an `alter_field` on link table `j`; and a request naming no dependent of the two collections maps to a value no schedule entry can carry, so it can only ever disagree. |
| 3 (observable) | — | `alpha(schedule) = 'empty' if len == 0 else ('nonempty', schedule[0], sorted(schedule[1:]), per-link-relation order flags)`, applied to both sides, where flag `j` records whether the move of link table `j` preceded the rewrite of the column inside it. That pins emptiness, WHICH request comes first, the exact multiset of dependent requests, and the order INSIDE each link relation — so a deferred main move, a request issued twice, a request skipped, a filler entry, and a link table whose column is rewritten before the table is moved all disagree — while `sorted` quotients out exactly the freedom the spec leaves (§2 row 5, the order of the dependents among themselves). Two earlier revisions were weaker: the first compared only zero-vs-nonzero SQL counts, the second compared (first entry, multiset) over a carrier that gave a link relation ONE entry. Both were lifted. |
| 4 | `database_backwards` = same function, identifiers swapped | every input is driven in both directions. |

`allow_migrate_model` (the `if` the patched hunk sits inside, `:321`) has no
counterpart in `model.py`; no `DATABASE_ROUTERS` are configured, so it is `True`
for every generated input and the oracle always enters the modeled branch. That
is the domain the model covers. `allow_migrate_model` also preemptively rejects a
proxy, swapped-out or unmanaged model, and a model whose `required_db_vendor` /
`required_db_features` the connection does not satisfy
(`Options.can_migrate`, `django/db/models/options.py:343-357`, via
`Operation.allow_migrate_model`, `django/db/migrations/operations/base.py:111`);
each of those makes the real method request NOTHING even when the two identifiers
differ. Measured on the post-patch worktree: an unmanaged renamed model with one
link relation and differing identifiers records `[]` where the model predicts
`[-1, 0, 1]`, and the same for `required_db_vendor = 'postgresql'` on sqlite. So
the domain restriction this paragraph discloses is not only "no routers": it is
that the operation is PERMITTED to act on the renamed model's storage at all.

A second, independent domain restriction, disclosed here in the same form. The
model covers renames in which every link relation really CARRIES the column that
reaches the renamed model, addressable inside its link table under the renamed
model's `_meta.model_name` **both before and after** the rename. The reason is
`create_many_to_many_intermediary_model`
(`django/db/models/fields/related.py:1112-1116`): it computes
`to = make_model_tuple(to_model)[1]` and `from_ = klass._meta.model_name`, and
when `to == from_` it names the auto-created link table's two FKs `from_<n>` /
`to_<n>` rather than `<n>`. So when the m2m's other endpoint goes by the SAME
`model_name` as the model owning the field, the link table carries no field named
`<n>`, and the argument evaluation of `:365-369` —
`old_m2m_model._meta.get_field(old_model._meta.model_name)` (`:367`) and
`new_m2m_model._meta.get_field(new_model._meta.model_name)` (`:368`) — raises
`FieldDoesNotExist` instead of issuing the request. The exclusion is TWO-SIDED
because those are two different lookups, one under the old `model_name` and one
under the new: measured on the post-patch worktree, renaming `tag_a.Tag` →
`tag_a.Label` with an m2m to `tag_b.Tag` (collision under the OLD name; the
pre-rename link table's fields are `['id', 'from_tag', 'to_tag']`) and renaming
`tag_a.Foo` → `tag_a.Tag` with an m2m to `tag_b.Tag` (collision under the NEW
name; the post-rename link table's fields are `['id', 'from_tag', 'to_tag']`)
BOTH raise, forwards and backwards. `database_backwards` swaps the two names
(`:371-378`) and every input is driven in both directions, so a one-sided
carve-out would not even be direction-stable.

Because the real method issues each request as it computes it, such a link
relation truncates the schedule at the point it is visited rather than merely
dropping its own two requests: measured, with two link relations and the
colliding one SECOND the real method records 4 requests and then raises (against
the model's 5), with the colliding one FIRST it records 2 (against 5), and with
one column relation alongside (`nc=1, nl=1`) it records 3 (against 4) — the
column rewrite having already been issued. That is why the restriction is stated
as a property of the INPUT rather than as a bounded shortfall in the schedule.

Both restrictions are restrictions on `α`'s domain, i.e. on which concrete
configurations the bridge realizes, not on the `Requires` of
`rename_schema_schedule`, which are unchanged (ownership plus termination). The
inert branch is unaffected by either: measured, on the colliding shape with equal
identifiers the post-patch method returns having requested nothing, matching
clause (1).

**Input domain.** The only preconditions are
`Requires(Acc(list_pred(column_relations), 1/2))`,
`Requires(Acc(list_pred(link_relations), 1/2))` and
`Requires(MustTerminate(2))` — ownership and termination, no value constraint —
so every input satisfies the `Requires` and nothing is filtered. The realizable
space after the bridge is finite: 7 × 7 table ids × 12 dependent shapes (`n_fk`
0–3 × `n_m2m` 0–2) × 2 directions = **1176 points, enumerated exhaustively**,
then fuzzed over the same space with the pinned seed to reach the ≥ 1e5 budget
(exhausting a finite domain is a stronger check than 1e5 samples of it). Boundary
cases run first and include the exact F2P shape (`Rider` with an explicit
`db_table`, a `Pony.rider` FK, renamed to `Runner`, table identifier unchanged,
forwards **and** backwards), both empty dependent lists, the empty table name,
the singleton column relation, the single link relation, the TWO-link-relation
shape, and both impl branches on the widest shape.

**Discrimination self-test.** A green G-CONF that cannot go red certifies
nothing, so before the real run the same harness is pointed at five probes, one
per property the spec pins:

1. the `model_prepatch.py` impl region (copied verbatim the same way), on the
   unchanged-identifier shape with dependents present — flagged **2/2**;
2. a schedule that requests the main move LAST instead of first, on proceeding
   shapes — flagged **2/2**, which is what proves the harness observes the ORDER
   and not just the count;
3. a schedule that rewrites every column relation TWICE, on proceeding shapes —
   flagged **2/2**, which is what proves it observes per-request MULTIPLICITY;
4. a schedule that, for every link relation, rewrites the column inside its link
   table BEFORE moving that link table — flagged **4/4**. Same first entry, same
   multiset: this probe is flagged only because the harness observes the order
   INSIDE one link relation, which is the property the merging revision
   destroyed;
5. a schedule that moves every link table but never rewrites the column inside
   it — flagged **4/4**, which is what proves a link relation's two requests are
   two observations rather than one.

If any probe is not flagged the script exits 1 without reporting a pass.

**Verdict.** `G-CONF=pass` — 0 disagreements over 101194 inputs at the
ordered-per-request granularity.
