# refinement.md — django__django-16116

The operation-by-operation correspondence between `model.py`'s implementation
(the `produce_changes_or_report` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change site — `Command.handle` changes-present branch

Gold hunk (`django/core/management/commands/makemigrations.py`, the `else:`
branch; the help-text hunk is a docstring-only edit with no behaviour):
```
 else:
+    if check_changes:
+        sys.exit(1)
     if self.update:
         self.write_to_last_migration_files(changes)
     else:
         self.write_migration_files(changes)
-    if check_changes:
-        sys.exit(1)
```
i.e. the `sys.exit(1)` is moved from AFTER the writer dispatch to BEFORE it.

The model spells out the post-fix control flow:
```python
if check_mode:
    raise CheckFailureExit()
if update_variant:
    write_update_artifacts(store)
else:
    write_fresh_artifacts(store)
```

| # | model.py impl op (`produce_changes_or_report`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `check_mode: bool` | `check_changes` (the `--check` flag) | R | `bool` ↔ `bool`, identity (mapping.md §2). |
| 2 | parameter `update_variant: bool` | `self.update` (the `--update` flag) | R | `bool` ↔ `bool`, identity (mapping.md §2). |
| 3 | parameter `store: List[int]` | `self.written_files` + the on-disk produced-migration set | R | the produced-artefact set ↔ `List[int]` of file-identity tokens; "grew" ↔ artefact produced (mapping.md §2). |
| 4 | `if check_mode: raise CheckFailureExit()` (FIRST) | `if check_changes: sys.exit(1)` placed FIRST | R + I | the `if`/exit is **I** (identical concrete guard + non-returning exit); the exit itself is **R** (`sys.exit(1)`/`SystemExit` ↔ `raise CheckFailureExit()`, mapping.md §2). This is the operation the gold patch MOVES to the front; modeling it before the writers is the fix. |
| 5 | `if update_variant: write_update_artifacts(store)` | `if self.update: self.write_to_last_migration_files(changes)` | A-consumed | the unchanged update writer; the proof consumes its `Ensures` (store grows by ≥1, prefix kept, every new token of the update kind `1`) to discharge the normal-return postcondition INCLUDING the variant-binding clause `Implies(update_variant, … new tokens == 1)` (mapping.md §3.2). Only this writer's axiom supplies kind-`1` tokens, so the branch correspondence is SENSED by the spec: dispatching the fresh writer here fails the variant-binding clause. |
| 6 | `else: write_fresh_artifacts(store)` | `else: self.write_migration_files(changes)` | A-consumed | the unchanged fresh writer; the proof consumes its `Ensures` likewise (kind-`0` tokens, mapping.md §3.1), discharging `Implies(not update_variant, … new tokens == 0)`. Dispatching the update writer here (or running BOTH writers) fails the variant-binding clause. |

(The help-text hunk — rewording the `--check` argument's `help=` string — is a
documentation-only change with no observable behaviour and no F2P/P2P
dependency; it is intentionally not modeled. No refinement step corresponds to
it.)

## The abnormal outcomes of steps 5/6, and why they are part of the refinement

Steps 5 and 6 are calls, so the refinement owes an account of every way the real
callee can leave them, not only the returning one. There are three, and the two
abnormal ones are carried by `Exsures` clauses rather than by extra impl
operations (the gold patch adds no handler, so the impl region stays **I**: the
outcomes propagate):

| real behaviour of the callee | model leg | tag | justification |
|---|---|---|---|
| the writer returns having produced this change set's artefacts | normal return | A-consumed | `len(store) == len(Old) + <step>_artifact_yield()`, the same advance on the medium tally, new tokens of that step's kind, prefix kept (mapping.md §3.3). |
| the update writer refuses: the most recent migration is applied / squashed / depended-on / absent, so it raises `CommandError` before writing anything (`makemigrations.py:264-292`) | `Exsures(ProducingStepDeclined, …)` | R + A-consumed | the refusal is REPORTED unchanged (the branch has no handler), and the guards precede every write, which licenses the "nothing committed, nothing recorded" conjuncts. Pinned to `update_variant and not check_mode`: only that step judges a most-recent migration, and in check mode no step is reached. |
| either writer cannot carry the pending changes through — `writer.path`/`as_string()` raises (`makemigrations.py:352-360`; the update step reaches the same code by delegating at `:328`) — having committed whatever it got to before stopping | `Exsures(ProducingStepFailed, …)` | R + A-consumed | likewise REPORTED unchanged. What it did to the medium is BOUNDED, not pinned, because the real extent is input-order dependent (measured: 0 of a yield of 1 for one unserializable app; 1 of a yield of 2 for two apps good-then-bad — mapping.md §3.3): at most one run's yield on both observables, no recorded token without a committed artefact (`LEDGER.produced >= Old + record growth`, sound because the record append at `:363` sits inside the `open(...,"w")` block at `:361`), new tokens still of the requested step's kind, prefix kept. Pinned to `not check_mode`, because the exit now precedes the dispatch. |

The last row is also a SECOND differential against the pre-patch order, and it
is the one the base_commit repo demonstrates directly: with the writers ahead of
the exit, `makemigrations --check` on a change set that cannot be rendered
reports the render error instead of exiting — measured at base_commit
(`--check` + unserializable default → `ValueError("Cannot serialize function:
lambda")`), whereas the gold order exits 1 with the writers never entered. So the
`not check_mode` conjunct on this leg states a real consequence of the move, not
an artefact of the model.

The discriminating content of the change — *exit before producing any artefact*
— lives in step 4's placement relative to steps 5/6. It is sensed by the
postcondition
`Exsures(CheckFailureExit, check_mode and … ToSeq(store) == Old(ToSeq(store)))`:
when check mode raises, the produced-artefact set must equal its old value (no
writer ran). The pre-patch code runs a writer first and exits afterwards;
`model_prepatch.py` reproduces that order (writers, then `if check_mode: raise`)
and **fails** exactly that clause (G-DIFF: `model_prepatch.py:140`, the
`ToSeq(store) == Old(ToSeq(store))` conjunct — the store grew by at least one
token before the raise; the differential is independent of the exact growth
count, so it is unaffected by the `>=` weakening of the writer axioms).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the *order* of the exit relative to the writers — is modeled **deeply** (the
spelled-out `if check_mode: raise` placed ahead of the writer dispatch in the
impl region), not hidden behind an axiom about the function under change. The
two A-consumed axioms cover the **unchanged** writer callees the branch invokes;
they are NOT the changed operation. There is no A-reference and no dead axiom.

## verify(model) ⇒ resolved

`produce_changes_or_report` verifies only if:
  * in check mode it raises `CheckFailureExit` with the produced-artefact set
    **unchanged** (step 4 placed before any writer) — i.e. no migration file is
    produced, the exact F2P observable (`assertFalse(os.path.exists(tmpdir))`);
  * outside check mode it returns normally having produced **at least one**
    artefact (the store grew by at least one token, prefix preserved) via the
    matching writer (steps 5/6) — i.e. the writer is still reached when not
    checking, so the P2P writing behaviour is preserved (the exact count tracks
    the pending changes and is not pinned, only growth is);
  * every newly-produced token's KIND matches the requested variant
    (`Implies(update_variant, … == 1)` / `Implies(not update_variant, … == 0)`):
    since each writer axiom stamps only its own kind, this clause is
    dischargeable ONLY by dispatching the MATCHING writer under the flag — an
    impl that swaps the two writers, always calls one of them, or calls both
    fails it (the two real writers have observably different on-disk outcomes,
    which the P2P suite distinguishes);
  * `Ensures(not check_mode)` on the normal-return path forbids any impl that
    returns normally in check mode (it MUST raise) — closing the "silently do
    nothing" cheat;
  * an abnormal outcome of a producing step is REPORTED as itself: never
    converted into a normal return, never reported in place of the other
    abnormal outcome, and never available where that step was not reached. The
    refusal only under `--update`, outside check mode, and only when the step
    really refuses; the non-completion only outside check mode, only for the
    step the flag selects, only when that step really cannot proceed, and with
    at most one run's artefacts committed and no artefact recorded that was not
    committed.

A wrong impl that writes-then-exits in check mode (the bug) fails the
store-unchanged conjunct; one that exits in NON-check mode fails
`Ensures(not check_mode)`; one that produces no artefact when not checking fails
`len(store) >= len(Old) + 1`; one that overwrites/clears the store fails the
prefix-preservation conjunct (full permission is required, so an impl cannot
satisfy a postcondition by discarding the input — directive 5); one that
dispatches the WRONG writer for the flag — swapped branches, always-one-writer,
or both writers — fails the variant-binding kind clauses (each writer axiom
stamps only its own kind, so mixed or mismatched kinds cannot satisfy them).
On the abnormal outcomes, measured 2026-08-14 with the verifier's own message:
one that reports a non-completion without a step having reported one fails
`Implies(update_variant, update_step_fails())`; one that reports the FRESH step's
non-completion for an `--update` request fails the same conjunct; one that reports
a non-completion in check mode fails `not check_mode`; one that records an
artefact it did not commit fails
`LEDGER.produced >= Old(LEDGER.produced) + len(store) - len(Old(ToSeq(store)))`;
one that re-runs the step after it stopped partway fails the one-run envelope
`len(store) <= len(Old) + yield and LEDGER.produced <= Old + yield`; one that
swallows the non-completion and returns fails `LEDGER.produced >= Old + 1`; and
one that reports a partway run as the refusal fails `update_step_declines()`. By R (bool/exit
refinements) and A-consumed (the two real writers are artefact-producing,
audited by G-AX) the verified control flow equals the gold `if check_changes:
sys.exit(1)` placed ahead of the writer dispatch. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
