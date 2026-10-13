# refinement.md — django__django-13809

The operation-by-operation correspondence between `model.py`'s implementation
(`offers_skip_request`, `startup_action_schedule`) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee /
library-semantics by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The invocation-exposure site — `add_arguments` (`runserver.py:51-57`)

Gold hunk:
```
+ parser.add_argument(
+     '--skip-checks', action='store_true',
+     help='Skip system checks.',
+ )
```
(inserted right after the `--noreload` argument; NO `requires_system_checks`
guard — unlike the common `BaseCommand.create_parser`, which only adds it for
auto-validated commands. This command sets `requires_system_checks = []`.)

Modeled by `offers_skip_request()`.

| # | model.py impl op (`offers_skip_request`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `return True` | `parser.add_argument('--skip-checks', action='store_true', ...)` reached unconditionally | I + A-reference | the unconditional control flow (no guard) is the identical concrete fact (I): the option is always registered. Registering the `store_true` option ↔ the parser "offering" the skip request, and its parsed value being available, is the **A-reference**: `axiom_check.py` (G-AX §3.1) builds a real `argparse` parser mirroring this hunk and asserts `skip_checks` is present in the namespace (default `False`, present-value `True`). There is no consumed axiom — the exposure is modeled deeply as `Result() == True`. |

## B. The start-up gate site — `inner_run` (`runserver.py:117-121`)

Gold hunk:
```
- self.stdout.write("Performing system checks...\n\n")
- self.check(display_num_errors=True)
+ if not options['skip_checks']:
+     self.stdout.write('Performing system checks...\n\n')
+     self.check(display_num_errors=True)
  # Need to check migrations here, ...
  self.check_migrations()
```

Modeled by `startup_action_schedule(skip_checks)`.

| # | model.py impl op (`startup_action_schedule`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `skip_checks: bool` | `options['skip_checks']` | R + A-reference | bool ↔ bool; the namespace value is always present once site A registers the `store_true` option, holding the user's `--skip-checks` token (`False` default / `True` present). G-AX §3.2 validates the `store_true` default/presence against real `argparse`. |
| B2 | `if not skip_checks: schedule.append(ANNOUNCE); schedule.append(RUN)` | `if not options['skip_checks']: self.stdout.write("Performing system checks...\n\n"); self.check(display_num_errors=True)` | I + R | the identical concrete boolean guard (`if not skip_checks`, I); the two appended action codes refine the two guarded side-effects — `ACTION_ANNOUNCE_VALIDATION` ↔ the `stdout.write("Performing system checks...")`, `ACTION_RUN_VALIDATION` ↔ `self.check(display_num_errors=True)` (R, mapping.md §2). Emitting the code ↔ the side-effect occurring; the F2P test observes both (message text present + `check` call count). |
| B3 | `schedule.append(MIGRATION_RECHECK)` (always, after the guard) | `self.check_migrations()` (always, after the guard) | I + R | the identical unconditional placement (I) after the guarded block; `ACTION_MIGRATION_RECHECK` ↔ `self.check_migrations()` (R). Present in the schedule regardless of the skip request — it is not part of the suppressible pass. |
| B4 | `return schedule` (a `List[int]` in start-up order) | the executed start-up control flow of `inner_run` | R | the emitted action codes, in start-up order, refine the observable start-up actions the test inspects (mapping.md §2). |

The postconditions pin the schedule EXACTLY for both values of the skip request:
`skip_checks ⇒ ToSeq(Result()) == PSeq(MIGRATION_RECHECK)` and
`not skip_checks ⇒ ToSeq(Result()) == PSeq(ANNOUNCE, RUN, MIGRATION_RECHECK)`.
So the announce/run actions are emitted iff `not skip_checks` (the gate) and the
migration re-check is emitted regardless (it is outside the gate) — exactly the
gold `inner_run`.

## C. The discriminating behaviour and the prepatches

The change exists so that, when the operator passes `--skip-checks`, the
start-up validation pass (the "Performing system checks..." announcement AND the
`self.check(...)` invocation) is suppressed, while the migration re-check still
runs. This is the F2P test `test_skip_checks` (mocks `check`/`check_migrations`/
`run`; asserts the announcement is absent and `check` is NOT called when
`skip_checks=True`, present and called when `skip_checks=False`).

- `model_prepatch.py` reverts **site B** (the start-up gate): the validation
  announcement + run are emitted UNCONDITIONALLY (the pre-patch `inner_run`,
  which always wrote the message and called `self.check`). It fails the (2a)
  postcondition `Implies(skip_checks, ToSeq(Result()) == PSeq(MIGRATION_RECHECK))`
  (it produces `[ANNOUNCE, RUN, MIGRATION_RECHECK]` even under a skip request) —
  exactly the bug `test_skip_checks` catches (`check` called / message present
  with `skip_checks=True`).
- `model_prepatch_2.py` reverts **site A** (the invocation exposure): this
  command does NOT offer the skip request on its own account (the pre-patch
  state, where only the common machinery's guarded registration exists and it
  does not fire for this non-auto-validated command). It fails the (1)
  postcondition `Result()` of `offers_skip_request` (returns `False`). Without
  the option offered, `skip_checks` could never be set True from the command
  line and the start-up pass could never be suppressed.

Both prepatches keep the spec byte-identical (G-DIFF same-spec; region-hash
equality recorded in meta.json) and FAIL verification on the discriminating
clause of their reverted site.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The two genuinely-changed operations —
registering the skip option on this command's parser, and gating the start-up
validation pass on the resulting namespace value — are modeled **deeply** (the
unconditional `return True`; the `if not skip_checks` guard over the emitted
action schedule). No `@ContractOnly` axiom is consumed. Their reliance on
standard-library `argparse` `store_true` semantics (option exposed once
registered; default `False`/present `True`) is the single **A-reference** that
`axiom_check.py` (G-AX) validates against the real `argparse`. There are no
consumed axioms and no dead axioms.

## E. verify(model) ⇒ resolved

`offers_skip_request` verifies only if the skip request is offered
unconditionally (site A); `startup_action_schedule` verifies only if the
validation announcement + run are emitted exactly when no skip request is in
force while the migration re-check is emitted regardless (site B). By R (bool ↔
bool; action codes ↔ the start-up side-effects) and A-reference (the real
`argparse` exposes/defaults the `store_true` option exactly as the deep model
assumes, G-AX), the verified decisions equal the gold `add_arguments`
registration and the gold `inner_run` gate. The gold patch resolves
(G-RESOLVE). Trust points: refinement fidelity (this document, G-EQ) and the
single A-reference's soundness (G-AX) — no consumed axiom.
