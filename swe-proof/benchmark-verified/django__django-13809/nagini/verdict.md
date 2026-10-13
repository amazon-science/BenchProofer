# P2 adversarial audit — django__django-13809

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,12 +91,8 @@
     # post-conditions-end
     # impl-start
     schedule = []  # type: List[int]
-    if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
-        schedule.append(ACTION_ANNOUNCE_VALIDATION)
-        schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
+    schedule.append(ACTION_ANNOUNCE_VALIDATION)
+    schedule.append(ACTION_RUN_VALIDATION)
     schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     Ensures(Result())
     # post-conditions-end
     # impl-start
-    return True
+    return False
     # impl-end
 
 
@@ -92,11 +92,8 @@
     # impl-start
     schedule = []  # type: List[int]
     if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
         schedule.append(ACTION_ANNOUNCE_VALIDATION)
         schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
     schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,12 +91,6 @@
     # post-conditions-end
     # impl-start
     schedule = []  # type: List[int]
-    if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
-        schedule.append(ACTION_ANNOUNCE_VALIDATION)
-        schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
     schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,11 +92,8 @@
     # impl-start
     schedule = []  # type: List[int]
     if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
+        schedule.append(ACTION_RUN_VALIDATION)
         schedule.append(ACTION_ANNOUNCE_VALIDATION)
-        schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
     schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,11 +92,8 @@
     # impl-start
     schedule = []  # type: List[int]
     if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
         schedule.append(ACTION_ANNOUNCE_VALIDATION)
         schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
-    schedule.append(ACTION_MIGRATION_RECHECK)
+        schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,11 +92,9 @@
     # impl-start
     schedule = []  # type: List[int]
     if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
         schedule.append(ACTION_ANNOUNCE_VALIDATION)
         schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
+    schedule.append(ACTION_MIGRATION_RECHECK)
     schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,12 +91,9 @@
     # post-conditions-end
     # impl-start
     schedule = []  # type: List[int]
-    if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
+    if skip_checks:
         schedule.append(ACTION_ANNOUNCE_VALIDATION)
         schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
     schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -91,12 +91,11 @@
     # post-conditions-end
     # impl-start
     schedule = []  # type: List[int]
-    if not skip_checks:
-        # The suppressible validation pass: announce, then run it (as a unit).
+    if skip_checks:
+        schedule.append(ACTION_MIGRATION_RECHECK)
+    else:
         schedule.append(ACTION_ANNOUNCE_VALIDATION)
         schedule.append(ACTION_RUN_VALIDATION)
-    # The migration re-check is not part of the suppressible validation pass; it
-    # always runs.
-    schedule.append(ACTION_MIGRATION_RECHECK)
+        schedule.append(ACTION_MIGRATION_RECHECK)
     return schedule
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A long-running development command performs a one-off validation pass on
  start-up. Two coordinated guarantees let an operator suppress that pass for
  this command from the invocation:

  (1) This command always surfaces a "skip validation" request on its
      invocation, independently of whether it is the kind of command that the
      common machinery would otherwise validate automatically. (It validates
      itself explicitly on start-up rather than through the common pre-pass, so
      it must offer the request on its own account; the request is offered
      unconditionally.)

  (2) On start-up the command emits a determinate schedule of observable
      start-up actions. The validation pass contributes two such actions, as a
      unit: announcing that validation is being performed, and running the
      validation. BOTH of these actions are emitted if and only if no skip
      request is in force. A second, independent start-up action — re-checking
      pending data-shape migrations — is ALWAYS emitted, regardless of the skip
      request; it is not part of the suppressible validation pass.

  Consequently, when a skip request is in force the start-up schedule contains
  neither the validation announcement nor the validation run, but still
  contains the migration re-check; when no skip request is in force the schedule
  contains the announcement, the validation run, and the migration re-check, in
  that order.

The single boolean input is whether the invocation carried a skip request. The
schedule of start-up actions is modelled as a `List[int]` of action codes; no
callee is axiomatized — the gating decision is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# No consumed axioms: whether this command offers the skip request, and whether
# the validation actions are emitted on start-up, are decided by pure boolean
# gating, modelled deeply below.
# axioms-end

# pure-start
# Observable start-up action codes (their identity is irrelevant beyond being
# distinct; only their presence/absence and order in the schedule is observed).
ACTION_ANNOUNCE_VALIDATION = 1   # announce that the validation pass is running
ACTION_RUN_VALIDATION = 2        # perform the validation pass
ACTION_MIGRATION_RECHECK = 3     # re-check pending data-shape migrations
# pure-end

def offers_skip_request() -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (1) This command offers the skip request unconditionally — it does not
    # depend on the common machinery deciding to validate it automatically.
    Ensures(Result())
    # post-conditions-end
    # impl-start
    return True
    # impl-end

def startup_action_schedule(skip_checks: bool) -> List[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # (2a) A skip request in force => neither validation action is emitted, but
    # the migration re-check still is: the schedule is exactly [migration-recheck].
    Ensures(Implies(skip_checks,
                    ToSeq(Result()) == PSeq(ACTION_MIGRATION_RECHECK)))
    # (2b) No skip request => the announcement, the validation run, and the
    # migration re-check are all emitted, in that order.
    Ensures(Implies(not skip_checks,
                    ToSeq(Result()) == PSeq(ACTION_ANNOUNCE_VALIDATION,
                                            ACTION_RUN_VALIDATION,
                                            ACTION_MIGRATION_RECHECK)))
    # The two exact-sequence clauses above pin the schedule completely for both
    # values of the skip request. The discriminating consequences they entail:
    # the announcement and the validation run are present exactly when no skip
    # request is in force (the validation pass is announced-then-run as a unit),
    # while the migration re-check is present regardless of the skip request.
    Ensures(Implies(skip_checks, len(Result()) == 1))
    Ensures(Implies(not skip_checks, len(Result()) == 3))
    # post-conditions-end
    # impl-start
    schedule = []  # type: List[int]
    if not skip_checks:
        # The suppressible validation pass: announce, then run it (as a unit).
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    # The migration re-check is not part of the suppressible validation pass; it
    # always runs.
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. Adversarial G-EQ refinement-fidelity pass on django__django-13809 (nagini). Env: (adversary/harness) + nagini verifier;.

**SPEC SHAPE:** Both functions are pinned EXACTLY over their entire finite domain. offers_skip_request(): Ensures(Result()) -> must return True. startup_action_schedule(skip_checks): exact-sequence postconditions ToSeq(Result())==PSeq(MIGRATION_RECHECK) when skip, ==PSeq(ANNOUNCE,RUN,MIGRATION_RECHECK) when not-skip, plus len==1/len==3. Domain is exhaustively {True,False}, so the spec admits exactly one behaviour per input. This leaves essentially no room for a same-spec verifying-but-wrong impl.

### ATTACKS (all same-spec confirmed byte-identical via `adversary same-spec`; only impl regions edited).
- atk_1.py (prepatch site B: validation emitted UNCONDITIONALLY [1,2,3] even under skip): weakness exit=2, verification failed (spec rejects). PREPATCH REPRODUCED.
- atk_2.py (prepatch_2 site A: offers_skip_request returns False): exit=2, verification failed. PREPATCH_2 REPRODUCED.
- atk_3.py (partial-domain: always [3], drops validation when not-skip): exit=2, rejected.
- atk_4.py (wrong order: RUN before ANNOUNCE when not-skip): exit=2, rejected.
- atk_5.py (control-flow-effect: migration re-check moved inside guard -> skip yields []): exit=2, rejected.
- atk_6.py (duplicate action: not-skip -> [1,2,3,3], breaks len==3/exact-seq): exit=2, rejected.
- atk_7.py (inverted gate: validation emitted iff skip): exit=2, rejected.
- atk_8.py (ECHO: behaviourally-correct if/else form instead of sequential appends): weakness exit=0 => CANDIDATE (same-spec AND verifies, 11.5s).

**MANDATORY RESOLVE ON CANDIDATE:** materialized atk_8's faithful refined patch (atk_8_patch.diff, if/else form of the gold gate) and RAN it through the official harness via swebench_unified.harness.run_resolve. First run failed with a bad hunk count (my patch-authoring error: +118,12 vs 5 added lines) -> completed=False, note 'no report... harness error' (INFRA/authoring, not a real non-resolve). Corrected hunk to +118,11 and re-ran: RESOLVED=True, completed=True, patch_successfully_applied=True, note='resolved', FAIL_TO_PASS test_skip_checks SUCCESS, all PASS_TO_PASS green. So the only verifying wrong-shaped impl is a correct echo whose faithful patch RESOLVES => NOT a weakness. verify does NOT admit an incorrect impl here.

**POSITIVE CONTROLS:** (1) model positive_control.py verifies via nagini_verify.sh (exit 0, 10.77s). (2) GOLD patch run_resolve -> resolved=True/completed=True (harness confirmed working on this instance, distinguishing infra failure from real non-resolve). (3) axiom_check.py (G-AX / A-reference soundness) exit 0: real stdlib argparse store_true default False/present True + real inner_run gate matches deep model over both token values.

A-LEG / refinement.md AUDIT (focus per instructions): Every leg is R, I, or A-reference; NO kind-3 and NO consumed @ContractOnly axiom (confirmed against model.py axioms region + mapping.md sec.3). Site A (offers_skip_request return True) = I + A-reference to unconditional argparse add_argument('--skip-checks', store_true) exposure. Site B (startup_action_schedule) = I+R (identical `if not skip_checks` guard; action codes 1/2/3 refine stdout.write announce / self.check / self.check_migrations) + A-reference to argparse store_true default/presence + inner_run control flow. Both A-references are exactly what axiom_check.py validates against REAL argparse (stdlib-only import) — correspondence to the true callees holds (announce+run present iff not-skip; migration re-check always). conformance_check.py (G-CONF) present, exercises real patched Command via /testbed, shadow==impl-region-verbatim.

**CONCLUSION:** >=5 distinct wrong impls (7) all fail verification; 2 prepatches reproduced; the sole verifying candidate is a gold-equivalent echo whose materialized faithful patch RESOLVES under run_resolve. No verify-but-incorrect impl exists. verify => correct holds for this spec. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A long-running development command performs a one-off validation pass on
  start-up. Two coordinated guarantees let an operator suppress that pass for
  this command from the invocation:

  (1) This command always surfaces a "skip validation" request on its
      invocation, independently of whether it is the kind of command that the
      common machinery would otherwise validate automatically. (It validates
      itself explicitly on start-up rather than through the common pre-pass, so
      it must offer the request on its own account; the request is offered
      unconditionally.)

  (2) On start-up the command emits a determinate schedule of observable
      start-up actions. The validation pass contributes two such actions, as a
      unit: announcing that validation is being performed, and running the
      validation. BOTH of these actions are emitted if and only if no skip
      request is in force. A second, independent start-up action — re-checking
      pending data-shape migrations — is ALWAYS emitted, regardless of the skip
      request; it is not part of the suppressible validation pass.

  Consequently, when a skip request is in force the start-up schedule contains
  neither the validation announcement nor the validation run, but still
  contains the migration re-check; when no skip request is in force the schedule
  contains the announcement, the validation run, and the migration re-check, in
  that order.

The single boolean input is whether the invocation carried a skip request. The
schedule of start-up actions is modelled as a `List[int]` of action codes; no
callee is axiomatized — the gating decision is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# No consumed axioms: whether this command offers the skip request, and whether
# the validation actions are emitted on start-up, are decided by pure boolean
# gating, modelled deeply below.
# axioms-end

# pure-start
# Observable start-up action codes (their identity is irrelevant beyond being
# distinct; only their presence/absence and order in the schedule is observed).
ACTION_ANNOUNCE_VALIDATION = 1   # announce that the validation pass is running
ACTION_RUN_VALIDATION = 2        # perform the validation pass
ACTION_MIGRATION_RECHECK = 3     # re-check pending data-shape migrations
# pure-end

def offers_skip_request() -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # (1) This command offers the skip request unconditionally — it does not
    # depend on the common machinery deciding to validate it automatically.
    Ensures(Result())
    # post-conditions-end
    # impl-start
    return True
    # impl-end

def startup_action_schedule(skip_checks: bool) -> List[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # (2a) A skip request in force => neither validation action is emitted, but
    # the migration re-check still is: the schedule is exactly [migration-recheck].
    Ensures(Implies(skip_checks,
                    ToSeq(Result()) == PSeq(ACTION_MIGRATION_RECHECK)))
    # (2b) No skip request => the announcement, the validation run, and the
    # migration re-check are all emitted, in that order.
    Ensures(Implies(not skip_checks,
                    ToSeq(Result()) == PSeq(ACTION_ANNOUNCE_VALIDATION,
                                            ACTION_RUN_VALIDATION,
                                            ACTION_MIGRATION_RECHECK)))
    # The two exact-sequence clauses above pin the schedule completely for both
    # values of the skip request. The discriminating consequences they entail:
    # the announcement and the validation run are present exactly when no skip
    # request is in force (the validation pass is announced-then-run as a unit),
    # while the migration re-check is present regardless of the skip request.
    Ensures(Implies(skip_checks, len(Result()) == 1))
    Ensures(Implies(not skip_checks, len(Result()) == 3))
    # post-conditions-end
    # impl-start
    schedule = []  # type: List[int]
    if not skip_checks:
        # The suppressible validation pass: announce, then run it (as a unit).
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    # The migration re-check is not part of the suppressible validation pass; it
    # always runs.
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. Adversarial G-EQ refinement-fidelity pass on django__django-13809 (nagini). Env: (adversary/harness) + nagini verifier;.

**SPEC SHAPE:** Both functions are pinned EXACTLY over their entire finite domain. offers_skip_request(): Ensures(Result()) -> must return True. startup_action_schedule(skip_checks): exact-sequence postconditions ToSeq(Result())==PSeq(MIGRATION_RECHECK) when skip, ==PSeq(ANNOUNCE,RUN,MIGRATION_RECHECK) when not-skip, plus len==1/len==3. Domain is exhaustively {True,False}, so the spec admits exactly one behaviour per input. This leaves essentially no room for a same-spec verifying-but-wrong impl.

### ATTACKS (all same-spec confirmed byte-identical via `adversary same-spec`; only impl regions edited).
- atk_1.py (prepatch site B: validation emitted UNCONDITIONALLY [1,2,3] even under skip): weakness exit=2, verification failed (spec rejects). PREPATCH REPRODUCED.
- atk_2.py (prepatch_2 site A: offers_skip_request returns False): exit=2, verification failed. PREPATCH_2 REPRODUCED.
- atk_3.py (partial-domain: always [3], drops validation when not-skip): exit=2, rejected.
- atk_4.py (wrong order: RUN before ANNOUNCE when not-skip): exit=2, rejected.
- atk_5.py (control-flow-effect: migration re-check moved inside guard -> skip yields []): exit=2, rejected.
- atk_6.py (duplicate action: not-skip -> [1,2,3,3], breaks len==3/exact-seq): exit=2, rejected.
- atk_7.py (inverted gate: validation emitted iff skip): exit=2, rejected.
- atk_8.py (ECHO: behaviourally-correct if/else form instead of sequential appends): weakness exit=0 => CANDIDATE (same-spec AND verifies, 11.5s).

**MANDATORY RESOLVE ON CANDIDATE:** materialized atk_8's faithful refined patch (atk_8_patch.diff, if/else form of the gold gate) and RAN it through the official harness via swebench_unified.harness.run_resolve. First run failed with a bad hunk count (my patch-authoring error: +118,12 vs 5 added lines) -> completed=False, note 'no report... harness error' (INFRA/authoring, not a real non-resolve). Corrected hunk to +118,11 and re-ran: RESOLVED=True, completed=True, patch_successfully_applied=True, note='resolved', FAIL_TO_PASS test_skip_checks SUCCESS, all PASS_TO_PASS green. So the only verifying wrong-shaped impl is a correct echo whose faithful patch RESOLVES => NOT a weakness. verify does NOT admit an incorrect impl here.

**POSITIVE CONTROLS:** (1) model positive_control.py verifies via nagini_verify.sh (exit 0, 10.77s). (2) GOLD patch run_resolve -> resolved=True/completed=True (harness confirmed working on this instance, distinguishing infra failure from real non-resolve). (3) axiom_check.py (G-AX / A-reference soundness) exit 0: real stdlib argparse store_true default False/present True + real inner_run gate matches deep model over both token values.

A-LEG / refinement.md AUDIT (focus per instructions): Every leg is R, I, or A-reference; NO kind-3 and NO consumed @ContractOnly axiom (confirmed against model.py axioms region + mapping.md sec.3). Site A (offers_skip_request return True) = I + A-reference to unconditional argparse add_argument('--skip-checks', store_true) exposure. Site B (startup_action_schedule) = I+R (identical `if not skip_checks` guard; action codes 1/2/3 refine stdout.write announce / self.check / self.check_migrations) + A-reference to argparse store_true default/presence + inner_run control flow. Both A-references are exactly what axiom_check.py validates against REAL argparse (stdlib-only import) — correspondence to the true callees holds (announce+run present iff not-skip; migration re-check always). conformance_check.py (G-CONF) present, exercises real patched Command via /testbed, shadow==impl-region-verbatim.

**CONCLUSION:** >=5 distinct wrong impls (7) all fail verification; 2 prepatches reproduced; the sole verifying candidate is a gold-equivalent echo whose materialized faithful patch RESOLVES under run_resolve. No verify-but-incorrect impl exists. verify => correct holds for this spec. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-13809 nagini bundle. Modeled behavior = offers_skip_request() (arg-free) + startup_action_schedule(skip_checks: bool). Input domain is exhaustively {False, True}, so checked completely.

Spec region confirmed byte-identical via same-spec (exit 0). Bundle model.py verifies under pinned Nagini (exit 0, 10.2s). G-AX passes against real stdlib argparse.

Gold patch (instance.json, verbatim): (A) add_arguments registers '--skip-checks' (action='store_true') UNCONDITIONALLY on runserver's own parser (runserver has empty requires_system_checks, so BaseCommand.create_parser never offers it); (B) inner_run guards the announce ('Performing system checks...') + self.check(display_num_errors=True) pair with `if not options['skip_checks']:`, and self.check_migrations() runs always, after the guard.

Exhaustive full-domain simulation of the real gold-patched argparse+inner_run control flow (run in /tmp):
 - offers_skip_request(): real namespace always contains 'skip_checks' once registered, default False => model True. MATCH.
 - startup_action_schedule(False): real=[ANNOUNCE,RUN,MIG]=[1,2,3] == model [1,2,3]. MATCH.
 - startup_action_schedule(True): real=[MIG]=[3] == model [3]. MATCH.

The postconditions pin the schedule EXACTLY for both boolean values (ToSeq==PSeq per case + len clauses) — this is exactly what the gold code emits. The spec neither forbids any behavior the gold code exhibits nor requires any it does not. No input on which the modeled function disagrees with the real (gold-patched) callee. Spec is FAITHFUL; no diverging input.

**Caveat:** the worktree was checked out at a later commit (4243ab1) rather than base_commit bef6f758; the base commit object is not present in that worktree. The gold patch used for the audit was taken from benchmark-verified/.../instance.json (patch field), which matches the documented hunks and the bundle's model exactly.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: add a `--skip-checks` store_true option to the runserver command and guard the 'Performing system checks...' announcement + self.check() behind `if not options['skip_checks']`, leaving check_migrations() unconditional. The spec view (lines 40-91, spec/pure/pre/post regions; impl excluded) discloses nothing about this edit beyond the public problem_statement. It is strictly MORE abstract than the problem statement, which itself already names '--skip-checks', 'runserver', 'system checks', and 'Performing system checks'. The spec view names none of runserver, --skip-checks, store_true, options['skip_checks'], inner_run, self.check, or check_migrations; instead it uses generic abstractions ('long-running development command', 'skip request', 'validation pass', 'migration re-check', opaque action codes 1/2/3). The one detail not in the problem statement — that a migration re-check is always emitted regardless of the skip request — describes pre-existing unchanged inner_run context (check_migrations existed pre-patch and is outside the gold diff's guarded block); it pins the modeling boundary rather than reconstructing the gold edit, and is stated behaviorally, not as a quotation of the patch. The 'announce-then-run as a unit' behavioral gating mirrors the intended semantics but is a legitimate specification of the desired behavior, not a leak of implementation specifics. G-LEAK lexical screen also recorded pass (no failures).

**Gold edit:** add a `--skip-checks` store_true option to the runserver command and guard the 'Performing system checks...' announcement + self.check() behind `if not options['skip_checks']`, leaving check_migrations() unconditional. The spec view (lines 40-91, spec/pure/pre/post regions; impl excluded) discloses nothing about this edit beyond the public problem_statement. It is strictly MORE abstract than the problem statement, which itself already names '--skip-checks', 'runserver', 'system checks', and 'Performing system checks'.

The spec view names none of runserver, --skip-checks, store_true, options['skip_checks'], inner_run, self.check, or check_migrations; instead it uses generic abstractions ('long-running development command', 'skip request', 'validation pass', 'migration re-check', opaque action codes 1/2/3). The one detail not in the problem statement — that a migration re-check is always emitted regardless of the skip request — describes pre-existing unchanged inner_run context (check_migrations existed pre-patch and is outside the gold diff's guarded block); it pins the modeling boundary rather than reconstructing the gold edit, and is stated behaviorally, not as a quotation of the patch. The 'announce-then-run as a unit' behavioral gating mirrors the intended semantics but is a legitimate specification of the desired behavior, not a leak of implementation specifics. G-LEAK lexical screen also recorded pass (no failures).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).