# refinement.md — django__django-15695

The operation-by-operation correspondence between `model.py`'s implementation
(the `rename_existing_index` impl region + the deep `issue_rename` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The schema rename step — `RenameIndex.database_forwards()` (`django/db/migrations/operations/models.py:934`, join at 960-966)

Gold hunk (the added no-op guard, at `models.py:963`):
```
             from_model_state = from_state.models[app_label, self.model_name_lower]
             old_index = from_model_state.get_index_by_name(self.old_name)
+        # Don't alter when the index name is not changed.
+        if old_index.name == self.new_name:
+            return
 
         to_model_state = to_state.models[app_label, self.model_name_lower]
         new_index = to_model_state.get_index_by_name(self.new_name)
         schema_editor.rename_index(model, old_index, new_index)
```

The guard is inserted at the **join** of the two branches that compute
`old_index` (the `old_fields`/unnamed branch via `_constraint_names` →
`matching_index_name[0]`, lines 939-959; and the named branch
`get_index_by_name(self.old_name)`, lines 960-962). Both branches produce an
`old_index` object whose `.name` is the existing index's current DB name. The
fix: before issuing the rename, return early (no-op) when that current name
already equals the target name `self.new_name`.

| # | model.py impl op (`rename_existing_index`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `old_index: ExistingIndex` with field `old_index.name` | the `old_index` object computed by either branch (`models.py:956-959` or `:961-962`); its `.name` | R | the existing index modelled by its one touched field — its current name (mapping.md §1, §2). Both branches are R/A producers of the same single `.name` field; the change reasons only about that field at the join, so the model carries it directly as the input `old_index.name`. |
| A2 | parameter `new_name: int` | `self.new_name` (equivalently `new_index.name`, since `new_index = to_model_state.get_index_by_name(self.new_name)`) | R | the target name; `str` ↔ `int` under the equality bijection (mapping.md §2). `get_index_by_name(self.new_name)` returns the index whose `.name == self.new_name`, so `new_index.name == self.new_name == new_name` (mapping.md §2). |
| A3 | `if old_index.name == new_name: return` | `if old_index.name == self.new_name: return` | **I** (under R on the name carrier) | the FIX. Identical concrete operation — compare the existing index's current name to the target name and return early (no-op) when equal — with the name `str` refined to the `int` identifier by R (names compared only for equality; mapping.md §2). This is the single added guard of the gold patch. |
| A4 | `issue_rename(editor, old_index, new_name)` | `schema_editor.rename_index(model, old_index, new_index)` | A-reference | the unchanged backend rename primitive. The change does NOT modify it; it only decides whether to call it. Its observable effect (issue a rename of `old_index.name` → `new_index.name`; afterwards the index carries the target name) is modelled **deeply** by `issue_rename` (recording `rename_issued = True`, `renamed_to = new_name`, `old_index.name = new_name`). There is **no consumed `rename_index` axiom**; the deep model is validated == the real callee's observable effect out-of-band by G-AX (axiom_check.py; mapping.md §3.1). |

The discriminating content of the change — *don't issue the rename when the
current name already equals the target* — lives in step **A3**. The spec senses
it via `Ensures(editor.rename_issued == (Old(old_index.name) != new_name))`:
a rename is issued iff the names differed — together with
`Ensures(Implies(not editor.rename_issued, editor.renamed_to ==
Old(editor.renamed_to)))`, which makes the no-alteration case a *complete* no-op
(nothing is asked of the schema primitive at all, so its rename record is
untouched) rather than a case an implementation could merely *report* as a no-op
after altering anyway (§B). The pre-patch issued the rename
unconditionally; `model_prepatch.py` reproduces that (it drops the A3 guard and
calls `issue_rename` directly) and **fails** that postcondition (see §B).

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it drops step **A3** (the no-op
guard) exactly as the pre-patch `database_forwards` had no guard and called
`schema_editor.rename_index(...)` unconditionally. With the byte-identical
frozen spec it **fails** verification on the precondition of `issue_rename`,
`Requires(old_index.name != new_name)` (`model_prepatch.py:113` — `The
precondition of method issue_rename might not hold. Assertion (old_index.name !=
new_name) might not hold.`): when the current name already equals the target
(`old_index.name == new_name`), the unconditional `issue_rename` invokes the
backend rename primitive in the very case the precondition forbids (renaming
`X → X`). (Equivalently, had the call been admissible, the post-state clause
`Ensures(editor.rename_issued == (Old(old_index.name) != new_name))` would also
fail — the unconditional rename sets `rename_issued = True` where the spec
requires `False`; the precondition simply rejects it one step earlier.)

That is precisely the behaviour the F2P test observes:
`test_rename_index_unnamed_index` applies the forward rename, then a backward
(a no-op for the unnamed index, leaving the DB index at the new name), then
**re-applies** the forward step and asserts both that it does not crash and that
`assertIndexNameExists(table_name, "new_pony_test_idx")` still holds — i.e. the
re-application is a no-op (issues no rename) because `old_index.name` already
equals `self.new_name`. The spec is therefore strong enough that no
implementation issuing the rename in the equal-names case can verify (spec sees
the bug).

The companion clauses keep the spec faithful and tight:
- `Ensures(Implies(editor.rename_issued, editor.renamed_to == new_name))` pins
  that *when* a rename is issued, it targets exactly the new name — a wrong impl
  cannot satisfy the iff by issuing a rename to a wrong target.
- `Ensures(Implies(not editor.rename_issued, editor.renamed_to ==
  Old(editor.renamed_to)))` pins that the no-alteration case is a **complete**
  no-op rather than merely a case that *reports* "no rename": when no rename is
  issued, nothing at all is asked of the schema primitive, so the record of what
  it was last told to rename to is left exactly as the step found it. This is
  TRUE of the real patched `database_forwards`: the added guard
  (`models.py:963-965`) returns **before** `new_index` is looked up and before
  `schema_editor.rename_index(...)` is reached (`models.py:966`), so on the
  equal-names path the schema editor is not engaged at all — which is precisely
  what the F2P's `assertNumQueries(0)`/re-apply shape observes and what leg B of
  G-CONF grounds by counting the SQL statements the real editor actually emits.
  This clause is what closes the audited G-EQ / G-PANEL-1 counterexample
  (atk_2/atk_6): a rival that never *calls* `issue_rename` escapes its domain
  restriction `Requires(old_index.name != new_name)` entirely, and can inline the
  primitive's whole observable effect on every branch while gating only the
  boolean flag — satisfying the iff, the target pin and the post-state pin with a
  *reported* value on a full-permission editor. Its faithful refinement is the
  unguarded `database_forwards` (the pre-patch bug: `rename_index` invoked
  unconditionally, so the F2P re-apply asks the backend to rename `X → X`), and
  it does not resolve. The iff alone cannot see it, because a boolean the impl
  writes is not evidence about whether the alteration happened; the *rest* of the
  primitive's state is. With this clause the equal-names branch of such a rival
  fails: it claims no rename was issued while the primitive's rename record has
  already moved to the target. `properties.py` covers both shapes
  (`weak-inline-bypass-report-only`, `weak-oracle-echo-report-only`).
- `Ensures(old_index.name == new_name)` pins the post-state in both cases (the
  index ends carrying the target name), so an impl cannot satisfy the iff by
  e.g. failing to actually rename on the differing-names branch.
- `Requires(MustTerminate(2))` on `rename_existing_index` (with the strictly
  smaller `MustTerminate(1)` on `issue_rename` and the constructors) demands
  TOTAL correctness: the step must actually return control to the migration
  executor. Nagini's default is partial correctness, under which a diverging
  body (e.g. an honest no-op on the equal-names branch but an endless loop in
  place of the rename on the differing-names branch) satisfies every `Ensures`
  clause vacuously — such an implementation previously verified even though
  its faithful transliteration hangs the migration instead of renaming (it
  never completes, so no rename test passes). The termination obligation
  rejects any body without a decreasing measure (unbounded loops, unbounded
  self-recursion); properties.py covers both shapes (`nonterm-*`).
- `Requires(old_index.name != new_name)` on `issue_rename` forbids invoking the
  backend rename primitive in the equal-names case (renaming `X → X`, which the
  real backend rejects — `axiom_check.py` part (2) confirms creating an index
  under an already-present name raises). This is the *load-bearing* tightening:
  it makes "issue the rename whether or not the names differ" a verification
  error at the call site, so the cheat of calling `issue_rename` unconditionally
  and then *resetting* the observability flag `editor.rename_issued = False` on
  the equal-names branch (which would otherwise satisfy the resettable post-state
  `editor.rename_issued == (Old(old_index.name) != new_name)` on a
  full-permission `editor`) cannot verify — its faithful refinement is "call the
  backend rename unconditionally," i.e. the exact pre-patch bug. The illegal
  invocation is forbidden at the primitive's precondition, not merely papered
  over after the fact (directive 5/8: do not pin only a resettable witness on a
  full-permission object).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding the no-op guard before the rename — is an **I** step (the
very same equality-compare-and-early-return concrete operation, only the name
`str` refined to an `int` identifier by R). The backend rename primitive
(A4) is an **unchanged** callee the new code still invokes on the non-no-op
branch; it is modelled **deeply** as an **A-reference** (its observable effect),
validated == the real callee by G-AX — NOT axiomatized as the thing that
changed, and not a consumed axiom the proof depends on. We never axiomatize the
function under change.

## D. verify(model) ⇒ resolved

`rename_existing_index` verifies only if (A3) it returns early without issuing a
rename when the current name already equals the target — and, by the complete-no-op
clause, without engaging the schema primitive in any way on that path, so it
cannot instead alter and then report a no-op — and (A4 + the companion
clauses) it issues exactly the rename to the target name otherwise, leaving the
index at the target name in both cases. By R (the index modelled by its current
name; `str` name ↔ `int` under equality; `self.new_name`/`new_index.name` ↔
`new_name`) and the single **I** fix step, the verified path equals the gold
`database_forwards` join
`… old_index = … ; if old_index.name == self.new_name: return ;
new_index = … ; schema_editor.rename_index(model, old_index, new_index)`
on the tested inputs. By G-AX the real `rename_index` has the observable effect
the deep model `issue_rename` records (A-reference), and the real decision logic
issues a backend rename iff the names differ (matching the gold guard, with
`assertNumQueries(0)` on the no-op path). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
