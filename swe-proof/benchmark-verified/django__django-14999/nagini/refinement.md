# refinement.md — django__django-14999

The operation-by-operation correspondence between `model.py`'s implementation
(`rename_schema_schedule`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses an axiom's `Ensures`, **A-reference** where a deep model is
validated == the real code by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The observable, and why it is the ordered per-request schedule

`database_forwards` returns nothing; everything it does it does by asking
`schema_editor` for schema operations. So the observable is the **ordered
schedule of schema operations the method requests, one entry per request**, and
each entry must say WHAT it operates on, because two different requests are not
interchangeable:

* the **main move** — the relocation of the renamed model's own table
  (`schema_editor.alter_db_table(new_model, old_db_table, new_db_table)`,
  post-patch `:329`);
* the **rewrite of one column relation** — for a foreign key pointing at the
  renamed model, the one `schema_editor.alter_field(...)` for that relation
  (`:344-348`);
* the **move of one link table** — for one of the renamed model's auto-created
  many-to-many link tables, `schema_editor.alter_db_table(new_m2m_model, ...)`
  (`:358-362`);
* the **rewrite of the column inside that same link table** —
  `schema_editor.alter_field(new_m2m_model, ...)` (`:365-369`).

The unit of the schedule is therefore **one request**, not one emitted statement
and not one dependent relation. The link table's two requests operate on two
different things — a table, and a column inside that table — so they are two
entries, and the schedule that carries them carries the order between them.
(mapping.md §2 row 3 states this granularity; axiom_check.py and
conformance_check.py measure the real method at exactly that granularity, never
at raw statement count, and never merging.) The previous revision of this bundle
merged those two requests into one entry; §F records what that cost.

The gold patch's behavioural change lives in the *inert* case (an unchanged table
identifier must request nothing). The *proceeding* case is unchanged by the
patch — but it is not therefore unspecified: it is the behaviour the patch must
PRESERVE, and it is observed by the P2P tests
(`test_rename_model_with_self_referential_m2m`, `test_rename_m2m_target_model`,
`test_rename_model_with_m2m`, "Tests the RenameModel operation on model with
self referential FK.", "Tests the RenameModel operation."). Three properties of
the proceeding case are load-bearing for those tests and are pinned here:

* **the main move comes first** (`:329` precedes both dependent loops, `:331` and
  `:351`). A dependent request is addressed to the renamed model's table under
  its NEW identifier (`to_field` is taken from `to_state`, `:341-343`; the m2m
  requests pass `new_m2m_model` and the new field, `:358`, `:365`), so a request
  issued before the move addresses a table that does not carry that identifier
  yet — and on sqlite, where `alter_field` rebuilds the table, the deferred move
  then lands on an identifier something else occupies.
* **every dependent request is issued exactly once** — `for related_object in
  old_model._meta.related_objects:` (`:331`) and `for (old_field, new_field) in
  fields:` (`:351`) each visit every element of their collection once and never
  revisit one; each iteration of the first issues exactly one `alter_field`, and
  each non-`continue`d iteration of the second issues exactly one
  `alter_db_table` and exactly one `alter_field`. A request that is missing
  leaves a column or a link table naming a table that has moved; a request issued
  twice is applied a second time to a table the first one already moved.
* **inside one link relation, the move precedes the column rewrite** — `:358-362`
  is textually before `:365-369` in the same loop body, and for every link
  relation in the disclosed domain (mapping.md §3) `:365-369` is also reached, so
  the order holds dynamically as well. The qualification is load-bearing: for an
  m2m outside that domain the argument evaluation of `:365-369` raises
  `FieldDoesNotExist` and the second request is never issued at all, so the
  claim is that the move precedes the rewrite for every link relation the
  carrier admits, not for every non-`continue`d m2m. The order is forced, not
  incidental: `:365-369` names `new_m2m_model`, i.e. the
  link table under its NEW `db_table`, which only exists once `:358-362` has been
  requested. Requesting the column rewrite first addresses a table that is not
  there yet; and since on sqlite `alter_field` rebuilds the table under the name
  it is given, the move that follows then relocates a table whose column still
  names the identifier the renamed model no longer uses.

All three were measured, not assumed: an implementation that keeps the multiset of
requests but defers the main move to the end fails `PASS_TO_PASS` "Tests the
RenameModel operation on model with self referential FK."; one that issues every
column rewrite twice fails `PASS_TO_PASS` `test_rename_m2m_target_model` and
`test_rename_model_with_self_referential_m2m`; and one that swaps a link
relation's two requests fails `PASS_TO_PASS` `test_rename_model_with_m2m` (that
last one is the measurement recorded in §F — it is precisely the attack that
refuted the previous revision of this spec). All three are recorded in
properties.py as reject cases `weak-main-move-last`, `weak-double-rewrite`,
`weak-link-pair-swapped`.

What is deliberately NOT pinned: the order the dependents are taken in among
**themselves**. Each dependent request is addressed to the renamed model's table
after that table has already moved, and distinct dependents address disjoint
tables/columns, so any order of the column relations, any order of the link
relations, and any interleaving of the two is a correct rename. Four
`properties.py` positive controls hold the spec to that — it must keep verifying
when the columns are emitted in reverse (`pos-control-reverse-column-order`),
when the whole link block precedes the columns (`pos-control-link-block-first`),
when the link relations are served last-to-first (`pos-control-links-descending`),
and when EVERY link table is moved before ANY inside-column is rewritten
(`pos-control-moves-then-inner-rewrites`, which also demonstrates that clause (6)
demands precedence, not adjacency).

Three of those four are written as *shape-guarded* variants: gold on every input
except one concrete dependent shape (one column relation and one link relation,
or two link relations and nothing else), where the reordered schedule is a
literal list. That is a proof-cost decision, not a hedge — a permuted link block
forces a mod-2 / slope-2 closed form on the loop invariant and clause (6)'s
nested quantifier then blows past the verifier cap, which for G-PBT is a
TIMED-OUT battery rather than a slow pass. Six reject cases use the SAME two
shape guards, so their rejection is the standing evidence that such a branch is
reachable and that the postcondition really is evaluated on it: a control here
cannot pass by being unreachable.

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

| # | model.py impl op (`rename_schema_schedule`) | patch.diff / post-patch op | tag | justification |
|---|---|---|---|---|
| A1 | param `before_table: int` | `old_db_table = old_model._meta.db_table` (`:323`) | R | `db_table` name → `int` identity; only `==` is observable (mapping.md §2 row 1). |
| A2 | param `after_table: int` | `new_db_table = new_model._meta.db_table` (`:324`) | R | as A1, the post-rename table identifier. |
| A3a | param `column_relations: List[int]`, used by its POSITIONS | every `old_model._meta.related_objects` element (`:331`) | R | each rich relation object → one POSITION of an opaque `List[int]`; the identity of a relation is irrelevant but WHICH one a request operates on is not (mapping.md §2 row 2). |
| A3b | param `link_relations: List[int]`, used by its POSITIONS | every many-to-many of `zip(...)` (`:350`) whose link table the loop at `:351` does not `continue` past (`:353-354`) **and whose link table carries the column reaching the renamed model under the renamed model's `model_name` both before and after the rename** (mapping.md §3, the two-sided disclosed restriction) | R | one POSITION per auto-created link table, owning the TWO codes `nc + 2*j` / `nc + 2*j + 1`, because the method makes TWO requests for it (`:358-362` and `:365-369`) against ONE for a column relation. The added qualification is not a modelling choice but the boundary of the carrier: when the m2m's other endpoint shares the owning model's `model_name`, `create_many_to_many_intermediary_model` (`django/db/models/fields/related.py:1112-1116`) names the link table's FKs `from_<n>` / `to_<n>`, so `:367`/`:368` address a field the through model does not carry and raise `FieldDoesNotExist` instead of issuing the second request. Such an m2m is outside the collection this row describes. |
| A4 | `if before_table == after_table: return result` with `result == []` | `if old_db_table == new_db_table: return` (`:326-327`) | I | identical concrete control flow: equality test on the two identifiers, early return requesting nothing. Empty schedule ↔ "no schema operation requested". |
| A5 | `result = [OP_MAIN_MOVE]` — the schedule's FIRST entry on the proceeding branch | `schema_editor.alter_db_table(new_model, old_db_table, new_db_table)` (`:329`), which precedes both dependent loops | R + A-reference | one entry ↔ the one request that relocates the renamed model's own table, at the position the real method issues it (first). G-AX/G-CONF validate the position, not just the presence. |
| A6a | the first loop's `result.append(i)`, once per position `i` of `column_relations` | the body of `:331-348` — one `alter_field` per `related_object` | R + A-reference | one entry ↔ the one request the visited column relation needs. `for` over a collection visits each element exactly once. |
| A6b | the second loop's `result.append(nc + m)` for `m` running `0 .. 2*nl - 1` | the body of `:355-369` — per non-skipped many-to-many **in the disclosed domain (A3b / mapping.md §3)**, `alter_db_table` (`:358-362`) then `alter_field` (`:365-369`), both addressed to that one link table | R + A-reference | TWO entries per link relation, in the order the body issues them: walking the codes upward from `nc` emits, for link relation `j`, the even code `nc + 2*j` (the link table's move, `:358-362`) and then its successor `nc + 2*j + 1` (the rewrite of the column inside it, `:365-369`). The consecutive-code scheme is what lets the postcondition SAY that the move precedes its own column rewrite. |
| A7 | `MustTerminate(2)` + the loops' `MustTerminate(nc - i + 1)` / `MustTerminate(2*nl - m + 1)` | both real loops range over finite collections and the method has no other backward edge | R | total, not partial, correctness: the inert case must RETURN, not merely fail to request anything. |

Clause-by-clause faithfulness against the post-patch method:

* **(1)** `Implies(before_table == after_table, len(Result()) == 0)` ← `:326-327`
  returns before any `schema_editor` call.
* **(2)** `Implies(before_table != after_table, len(Result()) > 0 and
  Result()[0] == OP_MAIN_MOVE)` ← past the guard, `:329` is unconditional and is
  the first `schema_editor` request the method makes; every other request is
  issued inside a loop that starts at `:331` or `:351`.
* **(3)** every later entry carries a code of the scheme, i.e. `0 <= entry < nc +
  2*nl` ← after `:329` the method requests nothing except inside the two loops,
  and each iteration's requests belong to the element it is visiting; it never
  issues a second main move and never issues a request belonging to no dependent.
* **(4)** no two entries carry the same code ← neither loop revisits an element
  (`for x in collection`), the two loops range over disjoint collections
  (`related_objects` vs `local_many_to_many`; a self-referential m2m is
  `continue`d at `:353` precisely because it is already covered by the
  `related_objects` pass, so it is not a second visit), and within one
  `local_many_to_many` iteration the two requests are of different kinds
  (`alter_db_table` vs `alter_field`) so they carry different codes.
* **(5)** `len(Result()) == 1 + len(column_relations) + 2*len(link_relations)` on
  the proceeding branch ← one main move, plus one `alter_field` per
  `related_objects` element, plus exactly two requests per visited m2m, and
  nothing else; the `continue` at `:353-354` is what makes `link_relations` (per
  A3b) the collection of link tables the method actually touches rather than
  every declared m2m.
* **(6)** wherever the schedule carries an even-offset code `c` (a link table's
  move), the entry carrying `c + 1` (the rewrite of the column inside that link
  table) comes strictly later ← `:358-362` precedes `:365-369` in the one loop
  body, and no other iteration can issue either of those two codes (each
  iteration owns its own `j`). The clause's parity guard is deliberately silent
  about `c + 1` versus `c + 2` — one link relation's column rewrite and the NEXT
  link relation's move also carry consecutive codes, and their order IS free
  (`pos-control-moves-then-inner-rewrites` is the control that keeps it free).

(3)+(4)+(5) together also force COVERAGE without a separate existential clause:
`nc + 2*nl` entries after the first, each carrying a code in `[0, nc + 2*nl)`, no
two carrying the same code, must carry EVERY code — so every column relation is
rewritten exactly once, every link table is moved exactly once, the column inside
every link table is rewritten exactly once, and no filler entry can stand in for
a missing request. The explicit coverage clause was omitted deliberately: it is
implied by pigeonhole and stating it directly cost the verifier more than the
whole rest of the proof.

## B. `database_backwards` (`:371`)

Gold: unchanged by the patch. `database_backwards` swaps `old_name`/`new_name`
and delegates to `database_forwards` (`:372-378`), so it inherits both the inert
case and the schedule shape. Modeled by the SAME `rename_schema_schedule` with
the table identifiers swapped (equality is symmetric, and the delegation means
the schedule is produced by the same code). The F2P test asserts
`assertNumQueries(0)` for backwards too; `axiom_check.py` drives the real
`database_backwards` as well as forwards, and `conformance_check.py` drives every
one of its 101194 inputs in both directions. No separate `model_prepatch_<k>` is
needed: forwards and backwards share the modeled function.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The operation that genuinely changed —
gating ALL schema work on table-identity inequality — is modeled DEEPLY (the
`if before_table == after_table` early-return branch [A4, kind I]); the
proceeding branch is modeled deeply too, as the ordered per-request schedule [A5,
A6a, A6b]. There is **no consumed `@ContractOnly` axiom** (the axioms region is
empty); the deep model's fidelity to the real method is checked by axiom_check.py
(G-AX) and conformance_check.py (G-CONF) at the granularity §A defines.

## D. The prepatch twin

`model_prepatch.py` reproduces the pre-patch method: it has no top-level
table-identity guard, so it requests every dependent operation unconditionally
and gates only the main move (the pre-patch main move was already inert by
`alter_db_table`'s own equality short-circuit,
`django/db/backends/base/schema.py:470-473` — the dependent loops were not, which
is the defect the issue reports). On an unchanged table identifier with any
dependent present (the F2P scenario has the `Pony.rider` FK) it returns a
schedule of length `len(column_relations) + 2*len(link_relations)` and so
**fails** clause (1). That is the spec sensing the change (G-DIFF): measured,
`Verification failed — Postcondition of rename_schema_schedule might not hold.
Assertion Implies((before_table == after_table), (len(Result()) == 0)) might not
hold.`

## E. verify(model) ⇒ resolved

`rename_schema_schedule` verifies only if it (1) requests nothing, and returns,
when `before_table == after_table`; (2) otherwise requests the move of the
renamed model's own table FIRST; (3-5) then issues every dependent request
exactly once and nothing else — one per column relation, two per link relation;
and (6) never asks to rewrite the column inside a link table before that link
table has been moved. By R (db_table name → int identity; column relation →
position; link relation → a position owning two consecutive codes; one request →
one entry) that is exactly the schedule the post-patch `database_forwards` issues
on the tested inputs **within the domain mapping.md §3 discloses** — the
operation permitted to act on the renamed model's storage, and every link
relation's inside column addressable under the renamed model's `model_name` both
before and after the rename — up to the order of the dependents among themselves
— which
is free in the real method too (its order is whatever `related_objects` /
`local_many_to_many` happen to yield, and the tests do not observe it).

The four failure modes the hidden tests actually catch are each excluded by a
distinct clause: requesting schema work on an unchanged table by (1) — the F2P
`assertNumQueries(0)`; never moving the model's own table, or moving it after the
dependent requests, by (2) — the self-referential-FK and "Tests the RenameModel
operation." P2P tests; issuing a request twice or not at all by (3)+(4)+(5) — the
m2m P2P tests; and rewriting a link table's column before moving the link table
by (6) — `test_rename_model_with_m2m` (§F). G-AX (axiom_check.py) confirms the
deep model matches the real method on all of these (A-reference), that the match
is DISCRIMINATING (the same dependents DO get their requests when the identifiers
differ), and that the order clauses REJECT both order-inverted mutants of the
schedule actually observed. G-CONF (conformance_check.py) adds the differential
evidence over the whole finite input space, with the swapped-link-pair and
dropped-link-rewrite probes flagged 4/4. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
document, G-EQ) plus the G-AX/G-CONF deep-model fidelity checks; there is no
axiom-soundness trust point because no axiom is consumed.

## F. The refuted revision, and what closed the hole

The previous revision of this bundle carried ONE schedule entry per dependent
*relation*: a link relation's `alter_db_table` (`:358-362`) and `alter_field`
(`:365-369`) were the single "rewrite of relation `i`". G-EQ/G-PANEL-1 refuted
that spec with an attack (recorded as `atk_9`) whose refined patch swapped those
two statements — requesting the rewrite of the column inside the link table
BEFORE moving the link table. Under the merged carrier that patch produced the
schedule the gold patch produces, entry for entry, so it satisfied every clause;
against the repository it failed `PASS_TO_PASS test_rename_model_with_m2m`
(1 of 113), because `:365-369` addresses the link table under its new name. The
observable, not any single clause, was the defect: the swap was invisible to it.

The repair LIFTS the carrier rather than adding a precondition. The relations are
split into `column_relations` (one request) and `link_relations` (two requests,
codes `nc + 2*j` and `nc + 2*j + 1`), so the swap is now a different schedule,
and clause (6) rejects it. Nothing was narrowed to get there: the preconditions
are still ownership plus termination with no value constraint, clauses (1)-(5)
say everything they said before (over a strictly finer observable — clause (5)'s
length is now `1 + nc + 2*nl`, an exact count of REQUESTS rather than of
relations), the freedom G-PANEL-2 checked is still free and now has four positive
controls instead of one, and the two harnesses that observe the real method were
re-pointed at the finer granularity (nothing is merged) with new red-capability
probes for exactly the swap that got through.
