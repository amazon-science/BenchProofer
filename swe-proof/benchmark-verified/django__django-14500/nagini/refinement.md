# refinement.md — django__django-14500

The operation-by-operation correspondence between `model.py`'s implementation
(the `keys_leaving_applied_set` impl region — a deep model of the changed recording
branch) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee/control-flow by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The unapply recording site — `unapply_migration` (`django/db/migrations/executor.py:246`)

Gold hunk (`executor.py`, body lines 253-258):
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

The change moves the own-key recording out of the `else:` so it runs
unconditionally (after the replaced-key loop), instead of only when the
migration is not a replacement.

| # | model.py impl op (`keys_leaving_applied_set`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `own_key: int` | `(migration.app_label, migration.name)` | R | a bookkeeping key `(app_label, name)` ↔ an integer code; the branch never inspects key content, only records it (mapping.md §2). |
| A2 | param `replaced_keys: PSeq[int]` | `migration.replaces` (list of key pairs) | R | list of key pairs ↔ `PSeq[int]` of codes; order preserved (mapping.md §2). |
| A3 | `while i < len(replaced_keys): result = result + [replaced_keys[i]]` (loop building `replaced_keys.take(i)`) | `if migration.replaces: for app_label, name in migration.replaces: self.recorder.record_unapplied(app_label, name)` | R + I | the `for ... in migration.replaces` loop ↔ the index loop over `replaced_keys` (R: list ↔ `PSeq`); each `record_unapplied(app_label, name)` call ↔ appending that key code to `result` (R: the recorder side-effect of removing a key ↔ recording that key in the result sequence, mapping.md §1/§2). The `if migration.replaces:` guard is subsumed: the index loop iterates 0 times when `len(replaced_keys) == 0`, exactly as the truthiness guard skips the body for an empty list (I, mapping.md §2). |
| A4 | `result = result + [own_key]` (after the loop, unconditionally) | `self.recorder.record_unapplied(migration.app_label, migration.name)` (after the `if`, unconditionally) | R + I | the own-key `record_unapplied` call ↔ appending `own_key` to `result`; it runs **after** the replaced-key loop and **unconditionally**, exactly as the gold patch moves it out of the `else:` (I on the control-flow placement; R on the key↔int and call↔append refinements). This is the discriminating step. |
| A5 | `return result` (a `List[int]`) | the recorder side effect / `return state` | R | the observable the F2P test reads is `applied_migrations()` membership, determined exactly by the set of `record_unapplied` calls — i.e. by the recorded-key sequence the model returns (mapping.md §1). `state` is migration-graph state irrelevant to the recording bug and unobserved by the F2P test. |

The whole recording branch is modelled **deeply** (the verified loop + final
append): there is **no consumed `@ContractOnly` axiom**. The deep model
`keys_leaving_applied_set` is the **A-reference** — validated **== the real fixed
branch** by G-AX (axiom_check.py): it records the same ordered key sequence
(`replaced_keys + [own_key]`) on boundary + exhaustive + 40 000 fuzz inputs, and
the pre-patch differential is confirmed on the squash-rollback witness.

The discriminating content of the change — the migration's own key recorded
**unconditionally** rather than only in the non-replacement `else:` — lives in
A4 (model: the unconditional final `result = result + [own_key]`; real: moving
`record_unapplied(migration.app_label, migration.name)` out of the `else:`).
The pre-patch records the own key only when `replaced_keys` is empty;
`model_prepatch.py` reproduces that (own-key append inside the `else:` branch)
and **fails** the postcondition `ToSeq(Result()) == replaced_keys + PSeq(own_key)`
whenever `replaced_keys` is non-empty (the result is `replaced_keys`, missing the
trailing `own_key`) — exactly the spec sensing the change (G-DIFF, confirmed: the
prepatch fails on `Postcondition ... ToSeq(Result()) == (replaced_keys + PSeq(own_key))`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — making the own-key recording unconditional — is modelled **deeply**
(the unconditional final append in `keys_leaving_applied_set`, step A4, an
**A-reference** validated by G-AX), not hidden behind an axiom about the function
under change. There is **no consumed axiom** of any kind: the only callee the
branch invokes, `record_unapplied` (an unchanged recorder method), is modelled
deeply as the recorded-key append rather than axiomatized, because its single
relevant effect (remove a key) is fully captured by the recorded-key sequence;
the test-observable applied set is the starting set minus the recorded keys.

## C. verify(model) ⇒ resolved

`keys_leaving_applied_set` verifies only if its output equals the exact recorded-key
sequence `replaced_keys + PSeq(own_key)` — i.e. only if the migration's own key is
recorded unconditionally, last, in addition to every replaced key (A4). By R
(key ↔ int code, `record_unapplied` call ↔ recorded-key append, list ↔ `PSeq`)
the verified build equals the post-patch `unapply_migration` recording branch on
the tested inputs; by G-AX the deep model `keys_leaving_applied_set` equals that
real fixed branch (A-reference) over boundary + exhaustive + 40 000 fuzz inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The one
trust point is refinement fidelity (this document, G-EQ) plus the G-AX deep-model
validation; there is no axiom-soundness trust point because no axiom is consumed.
