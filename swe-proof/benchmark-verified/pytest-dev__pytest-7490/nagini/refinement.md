# refinement.md — pytest-dev__pytest-7490

The operation-by-operation correspondence between `model.py`'s implementation
(the `settle_saved_evaluation` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** (the proof
uses an axiom's `Ensures`), **A-reference** (a deep model validated == a real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change — `pytest_runtest_call` (`src/_pytest/skipping.py:248`)

The gold patch's behaviourally-decisive hunk is the block ADDED after `yield`
in the `pytest_runtest_call` hook-wrapper:

```
     yield

+    # The test run may have added an xfail mark dynamically.
+    xfailed = item._store.get(xfailed_key, None)
+    if xfailed is None:
+        item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)
```

(The same hunk also rewrites the pre-`yield` `runxfail`/NOTRUN guard from a
nested `if not runxfail: if xfailed and not run:` into a single flat
`if xfailed and not runxfail and not run:`, and moves the
`skipped_by_mark_key` write in `pytest_runtest_setup` to
`= skipped is not None`. Those are behaviour-preserving rewrites for the F2P
scenarios — see "Behaviour-preserving rewrites" below.)

The modeled function `settle_saved_evaluation(slot, final_marker_state)`
is the post-`yield` refresh block, with the per-item store slot abstracted to
`SavedSlot` and `evaluate_xfail_marks` to the `evaluate_marks` axiom.

| # | model.py impl op (`settle_saved_evaluation`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| 1 | `slot.present` / `slot.value` as the pre-state of the saved slot | `xfailed = item._store.get(xfailed_key, None)` reading the slot under `xfailed_key` | R | "key absent" ↔ `present == False`; "key holds `None`" ↔ `present == True, value is None`; "key holds an `Xfail`" ↔ `present == True, value is not None` (mapping.md §2). The `get(..., None)` read is the slot's pre-state. |
| 2 | `if not slot.present:` … `elif slot.value is None:` | `if xfailed is None:` | R + I | `get(xfailed_key, None) is None` is true exactly when the key is absent OR holds `None`, i.e. `not present or value is None` — the two branches' guard. Splitting into the two cases is an **I** refinement of the single `is None` test under the R carrier (mapping.md §2). |
| 3 | `slot.value = evaluate_marks(final_marker_state)` | `item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)` | R + A-consumed | the store write is R-refined to the slot write; `evaluate_xfail_marks(item)` ↔ `evaluate_marks(final_marker_state)` is the **A-consumed** axiom (mapping.md §3.1). Crucially the argument is the marker state AFTER the body ran — `item` now carries any dynamically-attached mark — so the evaluation reflects it. |
| 4 | `slot.present = True` | (implied by the store assignment in step 3 — once the key is written it is present) | R + I | writing the key makes it present; `present = True` is the R image of "the key now exists". |

The discriminating content of the change — that the slot consumed by the report
step reflects the **post-body** marker state — lives in step 3's
`final_marker_state` argument and the postcondition
`Implies(not (Old(slot.present) and Old(slot.value) is not None),
slot.value is evaluate_marks(final_marker_state))` together with
`Ensures(slot.present)`. The pre-patch `pytest_runtest_call` has NO post-`yield`
block, so the slot keeps its pre-body state; `model_prepatch.py` reproduces that
(impl region is a bare `pass`) and **fails** the postcondition `slot.present`
(and the refresh clause), which is exactly the spec sensing the change (G-DIFF).

## Behaviour-preserving rewrites (not separately modeled)

The gold patch also (a) flattens the pre-`yield` NOTRUN guard and (b) sets
`skipped_by_mark_key = skipped is not None` in `pytest_runtest_setup`. Neither is
observable in the two F2P scenarios:

- The F2P tests use `run=True` xfail marks, so the NOTRUN (`not xfailed.run`)
  path is never taken; flattening `if not runxfail: if … and not run:` into
  `if … and not runxfail and not run:` is the same boolean predicate
  (`not runxfail and (xfailed and not run)` ↔ `xfailed and not runxfail and not
  run`). No behavioural difference. (I, modulo dead path.)
- `skipped_by_mark_key` governs the skip-location correction in
  `pytest_runtest_makereport`; the F2P scenarios are not skip-mark skips
  (`skipped is None`), so `skipped_by_mark_key` is `False` either way
  (old: explicit `= False`; new: `= (None is not None) == False`). No
  behavioural difference for these tests.

These are therefore folded into the slot's pre-state abstraction and not given
their own modeled function. The single behavioural change the F2P tests observe
— the post-body refresh — is modeled deeply.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— adding the post-body refresh of the saved evaluation — is an ordinary
conditional store-write Nagini expresses directly, so it is modeled **deeply**
(the impl region literally is the patched block), not hidden behind any axiom.
The only consumed axiom, `evaluate_marks` (**A-consumed**, step 3), covers the
**unchanged** callee `evaluate_xfail_marks` the new code re-invokes; its
soundness is the sole axiom trust point, audited by G-AX. The deep refresh
itself is additionally validated end-to-end against the real patched pytest by
axiom_check.py (the **A-reference** of mapping.md §3.2), not consumed as an
axiom.

## verify(model) ⇒ resolved

`settle_saved_evaluation` verifies only if, after the body has run, the
saved slot is non-empty (`Ensures(slot.present)`) AND — whenever nothing
non-empty was saved before the body — its value equals
`evaluate_marks(final_marker_state)`, i.e. the evaluation of the marks as
they stand AFTER the body (the post-body state, which now includes any
dynamically-attached mark). A no-refresh implementation (the pre-patch) cannot
discharge `slot.present` when the pre-body slot was absent/empty (G-DIFF). By R
(the store slot ↔ `SavedSlot`, the marker state ↔ the opaque token) and
A-consumed (`evaluate_xfail_marks` ↔ `evaluate_marks`), the verified skeleton is
the gold patch's post-`yield` block. Hence the report step
(`pytest_runtest_makereport`) reads a saved evaluation reflecting the
dynamically-attached mark, so the failing dynamic-xfail test is reported xfailed
and the passing dynamic-strict-xfail test is reported failed — the two F2P
outcomes. The gold patch resolves (G-RESOLVE). The trust points are exactly the
two of PLAN §1.1: axiom soundness (G-AX on `evaluate_xfail_marks`) and
refinement fidelity (this document, G-EQ).
