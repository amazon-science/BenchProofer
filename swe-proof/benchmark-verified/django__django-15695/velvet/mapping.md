# mapping.md — django__django-15695

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 647480166bfe7532e8c471fef0146e3a17e6c0c9`, states the type
abstraction, and records callee/control-flow provenance.

Repo file under change: `django/db/migrations/operations/models.py` (the
`RenameIndex` operation, class at `:879`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relabelSchedule (beforeId, afterId)` | `RenameIndex.database_forwards(self, app_label, schema_editor, from_state, to_state)` — `django/db/migrations/operations/models.py:934` | the modeled changed function: the schedule of store-mutation work the index-relabeling emits |
| `beforeId` (Int) | `old_index.name` — the name of the index resolved as the operation's *current* name. Either `matching_index_name[0]` (the auto-generated name, unnamed-index branch, `:947-951`) or `from_model_state.get_index_by_name(self.old_name).name` (named branch, `:962`). | the index identifier the object carries BEFORE the relabeling |
| `afterId` (Int) | `self.new_name` — the target name (`to_model_state.get_index_by_name(self.new_name)` resolves `new_index`, `:965`; `new_index.name == self.new_name`). | the index identifier the object carries AFTER the relabeling |
| `applyOp` (= 1) | `schema_editor.rename_index(model, old_index, new_index)` — `:966` | a single witness that the proceeding branch emitted the actual store-mutation (the index rename) |
| `out` (List Int) | the store-mutation work emitted by the call to `schema_editor.rename_index` (the SQL `ALTER INDEX … RENAME` on a `can_rename_index` backend, or the `remove_index` + `add_index` pair otherwise) | the emitted schedule; its zero-vs-nonzero length is the only observable the spec pins |

The gold patch's new lines are the guard inserted between `old_index`/`new_index`
resolution and the `schema_editor.rename_index` call:
```
+        # Don't alter when the index name is not changed.
+        if old_index.name == self.new_name:
+            return
```
This is the early-return that makes the operation inert when the resolved index
name already equals the target name. `database_backwards` (`:968`) swaps
`old_name`/`new_name` and delegates to `database_forwards` (for the *named*
branch), so it inherits the same noop behaviour; the *unnamed* (`old_fields`)
backward branch is already a no-op (`:969-971`, unchanged by the patch). The F2P
test re-applies the forward operation onto an already-relabeled store and
asserts it does not crash (and the index keeps its name).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an index name (`old_index.name`, a `str`) | `Int` identity (`beforeId`) | only the EQUALITY of the before/after names is observable to the decision (`if old_index.name == self.new_name`); two ints are equal iff the two names are equal. No other property of the name is used (no indexing, slicing, content inspection) on the changed control path, so a richer `List Char` carrier would add proof burden with no behavioural gain. |
| the target name (`self.new_name`, a `str`) | `Int` identity (`afterId`) | as above, the post-relabeling identifier. |
| the store-mutation work emitted on the proceeding branch (the single `schema_editor.rename_index(model, old_index, new_index)` call, which itself expands to one `ALTER INDEX … RENAME` SQL statement on a `can_rename_index` backend, or a `remove_index`+`add_index` pair on SQLite) | a NON-EMPTY `List Int` (`[applyOp]`) | MANY-to-one: the model abstracts "≥1 store-mutation emitted on the proceeding branch" to "the schedule is non-empty". It does NOT claim a 1:1 SQL↔entry bijection. The only property under test is zero-vs-nonzero (the F2P re-apply must issue the rename only when the names differ; re-applying when they are equal must be a no-op rather than a crash), which this abstraction captures exactly. The spec therefore pins ONLY `out ≠ []` on the proceeding branch. |
| `database_backwards` (name-swap then delegate, `:968-981`) | the same `relabelSchedule` invoked with swapped identifiers | name-swap is observationally a relabeling of `old_name`/`new_name`; equality is preserved (symmetric), so the noop verdict is identical. |

## 3. Callee provenance and the (absent) axiom inventory

**No consumed axiom, no A-reference.** The behaviour under specification —
whether the relabeling emits ANY store-mutation work — is decided entirely by the
identifier-equality comparison, which is precisely the behaviour the gold patch
CHANGES (it adds the early-return guard `if old_index.name == self.new_name:
return`). Per SPEC_GUIDE §0.7 / §3 the changed operation must NEVER be
axiomatized or A-referenced; it is modeled DEEPLY in `Solution.lean` (the
`if beforeId = afterId` early-return branch). There is no unchanged
stdlib/utility callee whose contract the proof consumes; the `axioms` region is
empty, there is no `axiom_check.py`, and **G-AX SKIPS**.

### 3.1 Why the resolution callees are NOT axiomatized
The name-resolution steps that precede the guard — `_constraint_names(...)` /
`models.Index(...)` (unnamed branch) and `from_model_state.get_index_by_name`
/ `to_model_state.get_index_by_name` (named branch) — are UNCHANGED by the patch
and run identically pre- and post-patch. They produce the two identifiers the
guard compares. Because the proof never depends on HOW those names are looked up
(only on the equality of the two resolved values, which the model takes as the
free inputs `beforeId`/`afterId`), there is no contract to consume: they are not
A-consumed (no `ensures` is used) and not A-reference (they are not the changed
op; the changed op is the guard + `rename_index` gating, modeled deeply). They
appear in this map as provenance for `beforeId`/`afterId` only.

### 3.2 Fidelity of the deep model (established by G-DIFF + G-RESOLVE, not G-AX)
Because the discriminating change is the operation under specification, its
fidelity to the real post-patch code is established by the static + resolve
gates at **zero-vs-nonzero** granularity (the only property under test):

- **noop case** (re-apply: the index has already been renamed, so the resolved
  `old_index.name` equals `self.new_name`): the deep model's empty schedule
  (clause 1, `out = []`). The gold patch makes `database_forwards` a true no-op
  here (`if old_index.name == self.new_name: return` skips the
  `schema_editor.rename_index` call), so this is faithful to the PATCHED code.
  `Solution_prepatch.lean` — which emits the rename unconditionally — FAILS
  clause 1, so G-DIFF sees the bug.
- **changed case** (first apply: `old_index.name` ≠ `self.new_name`): the deep
  model's non-empty schedule (clause 2, `out ≠ []`); the real method emits the
  `rename_index` call. The exact SQL count/shape is NOT pinned because the gold
  patch leaves the proceeding branch byte-identical to pre-patch and no test
  observes it.

The pre-patch defect: without the guard, `schema_editor.rename_index` was called
even when `old_index.name == self.new_name`, which on PostgreSQL raises
`ProgrammingError: relation "…" already exists` (renaming an index to a name a
relation already uses). The guard suppresses the call in exactly that case.

## 4. G-CONF status — conf_skip=false (real differential test)

The impl region is **R/I-tagged, not all-A-tagged** (refinement.md A1–A3), so
G-CONF applies (SPEC_GUIDE §4: `conf_skip` is true ONLY when the impl region is
all-A). The single property the spec pins — zero-vs-nonzero emitted
store-mutation work — is decided ENTIRELY by the added equality guard
(`old_index.name == self.new_name`), which is **DB-free computable**. So
`conformance_check.py` differential-tests the R/I shadow of the `do` block
(emit iff the identifiers differ) against the patched guard predicate.

The A3 abstraction is MANY-to-one (the real proceeding branch's
`rename_index` → one non-empty list), so running the real `database_forwards`
to observe its exact emitted SQL is impractical (it needs a live
`schema_editor`, a materialized backend with a real index, and live
`from_state`/`to_state` `ProjectState`s — the F2P integration test itself).
Exactly as for the boolean-flag transliteration cases (e.g.
django__django-16527), the **ORACLE is the patched guard transliterated
verbatim** from the gold-patched
`django/db/migrations/operations/models.py`:
`if old_index.name == self.new_name: return` (else reach `rename_index`), giving
"emit IFF `old_index.name != self.new_name`". The **SHADOW** is the modeled
decision "emit IFF `beforeId != afterId`". Both are bridged through the
equality bijection (§2) — two model ints are equal iff the two names are equal —
so the check fuzzes NAME PAIRS (strings) directly and compares emit-vs-noemit.
Exit 0 iff zero disagreements. `meta.json conf_skip=false`.

## 5. Fuzz seed; no axiom_check

There is **no `axiom_check.py`** (G-AX skips): there is no consumed axiom and no
A-reference. The changed operation (the guard + the gating of `rename_index`) is
modeled DEEPLY (SPEC_GUIDE §0.7), and `rename_index` is an UNCHANGED callee
whose contract the proof never consumes (the spec needs only that the proceeding
branch is non-empty — refinement.md A3, tagged R, not A).

G-CONF fuzz seed = **15695** (pinned in `conformance_check.py`): 6 boundary
name pairs (equal-name re-apply ⇒ noop; differing-name first-apply ⇒ rename;
empty-string and single-char boundaries) plus 100 000 fuzzed name pairs (~half
constructed equal to exercise both guard branches heavily).
