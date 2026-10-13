# refinement.md — django__django-15695

Correspondence between `Solution.lean`'s `relabelSchedule` `do` block and
`patch.diff`. The gold patch inserts an early-return guard into
`RenameIndex.database_forwards` so the operation is inert (emits no
store-mutation work) when the resolved index name already equals the target
name. `patch.diff` is the gold verbatim (applies at base_commit, resolves —
G-RESOLVE).

Gold hunk (`django/db/migrations/operations/models.py`):
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

## A. The relabeling emit-decision — `database_forwards`

| # | `Solution.lean` impl op (`relabelSchedule`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `beforeId afterId : Int` | the two resolved identifiers `old_index.name` (the index's current name) and `self.new_name` (the target name), both `str` | R | only the EQUALITY of the two names is observable to the changed control path (`if old_index.name == self.new_name`); two ints are equal iff the two names are equal (mapping.md §2). No other property of the names is read on the changed path, so `Int` identity is a sound carrier. Both are read-only (neither `mut`; the decision mutates nothing — directive 5). |
| A2 | `if beforeId = afterId then return []` | `if old_index.name == self.new_name: return` (emit no store-mutation work) | I | identical control: when the two identifiers are equal the operation is inert. Under R (equality bijection) the Lean guard and the Python guard fire on exactly the same inputs. The empty schedule `[]` models "no store-mutation work emitted" — faithful to the patched early `return`, which skips the `schema_editor.rename_index` call. |
| A3 | `else return [applyOp]` | fall through to `schema_editor.rename_index(model, old_index, new_index)` | R | MANY-to-one refinement: the real proceeding branch issues ≥1 store-mutation (one `ALTER INDEX … RENAME` on a `can_rename_index` backend, or a `remove_index`+`add_index` pair otherwise). The model abstracts "≥1 store-mutation emitted" to "the schedule is NON-EMPTY" (`[applyOp]`, a single witness `applyOp = 1`). The spec pins ONLY `out ≠ []` here — it does NOT claim a 1:1 SQL↔entry bijection, because the gold patch leaves this branch byte-identical to pre-patch and no test observes its exact shape. |

**No A-consumed axiom, no A-reference, no kind-3 (changed-inexpressible) op.**
`schema_editor.rename_index` is an UNCHANGED callee; the proof consumes none of
its contract (the spec needs only that the proceeding branch is non-empty, which
the literal `[applyOp]` satisfies regardless of `rename_index`'s internals), so
it is neither axiomatized (A-consumed) nor deeply modeled and validated against
its real output (A-reference) — it is an R abstraction of emitted work
(SPEC_GUIDE §0.7 / §3). The name-resolution steps that produce `beforeId` /
`afterId` (`get_index_by_name`, the `_constraint_names`/`models.Index`
unnamed-index branch) are UNCHANGED and supply the two free inputs; the proof
never depends on HOW the names are resolved, only on their equality, so no
contract is consumed there either (mapping.md §3.1).

## B. verify(Solution) ⇒ resolved

`relabelSchedule` verifies only if (clause 1) `beforeId = afterId → out = []`
and (clause 2) `beforeId ≠ afterId → out ≠ []`. By R (the equality bijection)
this pins the real method's emit-decision exactly: emit NO store-mutation work
iff the resolved name already equals the target. The F2P test re-applies the
forward operation onto an already-relabeled store — where `old_index.name`
already equals `self.new_name` — and asserts it does NOT crash (and the index
keeps its name). The patched code makes that case a true no-op (clause 1); the
first apply (names differ) still emits the rename (clause 2).

The pre-patch defect: without the guard, `schema_editor.rename_index` was called
even when `old_index.name == self.new_name`, raising on PostgreSQL
`ProgrammingError: relation "…" already exists`. `Solution_prepatch.lean` emits
`[applyOp]` UNCONDITIONALLY, leaving the unsolved goal
`beforeId = afterId → [applyOp] = []`, which is false — G-DIFF sees the bug on
exactly the discriminating clause (the equal-names no-op).

## C. G-CONF

The only observable the spec pins — zero-vs-nonzero emitted store-mutation work
— is decided ENTIRELY by the added equality guard, which is DB-free computable
(`old_index.name == self.new_name`). `conformance_check.py` therefore
differential-tests the R/I shadow of the `do` block (emit iff the identifiers
differ) against the transliterated patched guard over ≥10⁵ fuzzed name pairs
(mix of equal and differing). Running the real `database_forwards` is
impractical (it needs a live `schema_editor`, materialized backend, and
`ProjectState`s — the F2P integration test itself), so, exactly as for the
boolean-flag transliteration cases, the ORACLE is the patched guard predicate
transliterated verbatim. Both sides are bridged through the equality bijection
(mapping.md §2); exit 0 iff zero disagreements. `conf_skip=false`.
