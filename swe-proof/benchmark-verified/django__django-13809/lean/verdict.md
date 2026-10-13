# P2 adversarial audit — django__django-13809

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl closes its proof. The postcondition pins the output by full list equality to the input-grounded expression (if skipChecks then [] else [announceChecks, runChecks]) ++ tailSteps, total over the 2-valued Bool domain, so any verifying impl is behaviorally identical to gold on both inputs.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,9 +61,9 @@
 -- impl-start
 def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
   let mut log : List StartupAction := []
-  if !skipChecks then
-    log := log ++ [StartupAction.announceChecks]
-    log := log ++ [StartupAction.runChecks]
+  -- PREPATCH: system-check step emitted unconditionally, ignoring skipChecks.
+  log := log ++ [StartupAction.announceChecks]
+  log := log ++ [StartupAction.runChecks]
   log := log ++ [StartupAction.checkMigrations]
   log := log ++ [StartupAction.writeBanner]
   log := log ++ [StartupAction.serve]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
 -- impl-start
 def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
   let mut log : List StartupAction := []
-  if !skipChecks then
+  if skipChecks then
     log := log ++ [StartupAction.announceChecks]
     log := log ++ [StartupAction.runChecks]
   log := log ++ [StartupAction.checkMigrations]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,8 +62,8 @@
 def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
   let mut log : List StartupAction := []
   if !skipChecks then
+    log := log ++ [StartupAction.runChecks]
     log := log ++ [StartupAction.announceChecks]
-    log := log ++ [StartupAction.runChecks]
   log := log ++ [StartupAction.checkMigrations]
   log := log ++ [StartupAction.writeBanner]
   log := log ++ [StartupAction.serve]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,9 +61,7 @@
 -- impl-start
 def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
   let mut log : List StartupAction := []
-  if !skipChecks then
-    log := log ++ [StartupAction.announceChecks]
-    log := log ++ [StartupAction.runChecks]
+  -- PARTIAL: never emits the system-check step (correct only when skipChecks).
   log := log ++ [StartupAction.checkMigrations]
   log := log ++ [StartupAction.writeBanner]
   log := log ++ [StartupAction.serve]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
     log := log ++ [StartupAction.runChecks]
   log := log ++ [StartupAction.checkMigrations]
   log := log ++ [StartupAction.writeBanner]
-  log := log ++ [StartupAction.serve]
+  -- BUG: forgets to emit serve.
   return log
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   let mut log : List StartupAction := []
   if !skipChecks then
     log := log ++ [StartupAction.announceChecks]
-    log := log ++ [StartupAction.runChecks]
+    -- BUG: only announces; never actually runs the checks.
   log := log ++ [StartupAction.checkMigrations]
   log := log ++ [StartupAction.writeBanner]
   log := log ++ [StartupAction.serve]
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -59,15 +59,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
-  let mut log : List StartupAction := []
-  if !skipChecks then
-    log := log ++ [StartupAction.announceChecks]
-    log := log ++ [StartupAction.runChecks]
-  log := log ++ [StartupAction.checkMigrations]
-  log := log ++ [StartupAction.writeBanner]
-  log := log ++ [StartupAction.serve]
-  return log
+def implementation_serverStartup (skipChecks : Bool) : List StartupAction :=
+  (if skipChecks then [] else [StartupAction.announceChecks, StartupAction.runChecks]) ++ tailSteps
 -- impl-end
 
 -- proof-start
@@ -76,6 +69,6 @@
       problem_spec_serverStartup skipChecks
         (implementation_serverStartup skipChecks) := by
   intro skipChecks
-  unfold problem_spec_serverStartup implementation_serverStartup tailSteps
+  unfold problem_spec_serverStartup implementation_serverStartup
   cases skipChecks <;> rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,6 +64,7 @@
   if !skipChecks then
     log := log ++ [StartupAction.announceChecks]
     log := log ++ [StartupAction.runChecks]
+    log := log ++ [StartupAction.runChecks]  -- BUG: duplicate check run.
   log := log ++ [StartupAction.checkMigrations]
   log := log ++ [StartupAction.writeBanner]
   log := log ++ [StartupAction.serve]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Optionally skipping system checks when starting the development server.

The development server's startup routine performs a set sequence of steps
before it begins serving requests. One of those steps runs the project's system
checks, which can be slow during iterative development. A boolean control
(`skipChecks`) selects whether that step is performed.

We model the startup routine as the ordered list of observable actions it emits.
The system-check step consists of two observable actions: announcing that checks
are about to be performed, and running the checks themselves. When `skipChecks`
holds, both actions are omitted and the routine proceeds directly to the
remaining steps. When it does not hold, the system-check step is emitted first,
in order, ahead of the remaining steps. The remaining steps — verifying pending
migrations, writing the startup banner, and beginning to serve requests — are
always emitted, in the same order, regardless of the control.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the startup
-- routine's observable behavior is modeled structurally as the ordered list of
-- actions it emits, gated on a boolean control, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- An observable action emitted by the development server's startup routine.
* `announceChecks` — announce that the system-check step is about to run;
* `runChecks` — run the project's system checks;
* `checkMigrations` — verify that there are no unapplied migrations;
* `writeBanner` — write the startup banner (version, address, port);
* `serve` — begin serving requests. -/
inductive StartupAction
  | announceChecks
  | runChecks
  | checkMigrations
  | writeBanner
  | serve
deriving DecidableEq, Repr, Inhabited

/-- The steps that are always emitted, in order, after the (optional)
system-check step. -/
def tailSteps : List StartupAction :=
  [StartupAction.checkMigrations, StartupAction.writeBanner, StartupAction.serve]
-- pure-end

-- post-conditions-start
/-- The startup routine emits the system-check step (announcement then the
checks themselves) iff checks are not skipped, followed always by the remaining
steps in their set order. The result is fully determined by `skipChecks`:
the unchanged tail is pinned to its constant value in both cases, and the gated
prefix is present exactly when `skipChecks` is false. -/
def problem_spec_serverStartup (skipChecks : Bool) (result : List StartupAction) : Prop :=
  result =
    (if skipChecks then [] else [StartupAction.announceChecks, StartupAction.runChecks]) ++ tailSteps
-- post-conditions-end

-- impl-start
def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
  let mut log : List StartupAction := []
  if !skipChecks then
    log := log ++ [StartupAction.announceChecks]
    log := log ++ [StartupAction.runChecks]
  log := log ++ [StartupAction.checkMigrations]
  log := log ++ [StartupAction.writeBanner]
  log := log ++ [StartupAction.serve]
  return log
-- impl-end

-- proof-start
theorem correct_serverStartup :
    ∀ (skipChecks : Bool),
      problem_spec_serverStartup skipChecks
        (implementation_serverStartup skipChecks) := by
  intro skipChecks
  unfold problem_spec_serverStartup implementation_serverStartup tailSteps
  cases skipChecks <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND (verify => correct holds). 8 same-spec attacks (all same_spec=True) + positive control + prepatch reproduction. Verify tool: `bash scripts/lean_verify.sh <file>` from project root.

### Attack results
- atk_1.lean (PREPATCH bug: system-check emitted unconditionally, ignores skipChecks): exit=1 — `cases skipChecks <;> rfl` fails to reduce the skipChecks=true branch. prepatch_reproduced=true.
- atk_2.lean (inverted gate: emit iff skipChecks): exit=1.
- atk_3.lean (swapped order: runChecks before announceChecks): exit=1.
- atk_4.lean (partial-domain: never emit system-check step; correct only on true): exit=1.
- atk_5.lean (dropped tail step: serve missing): exit=1.
- atk_6.lean (control-flow effect: announces but never runs checks): exit=1.
- atk_7.lean (ungrounded-oracle ECHO: impl literally = spec RHS, gold-equivalent): exit=0, `#print axioms correct_serverStartup` => 'does not depend on any axioms' (CLEAN). Faithful patch = gold post-patch behavior (system-check gated on not skip_checks, tail always). RESOLVE RUN via run_resolve('django__django-13809', patch, run_id='sbu-audit-atk7b'): RESOLVED=True, COMPLETED=True, FLAKY=False, detail='resolved'. => echo does NOT break the spec (its faithful patch RESOLVES), consistent with the G-PANEL-1/eq resolve policy.
- atk_8.lean (boundary: duplicate runChecks emission): exit=1.

POSITIVE CONTROL: pos_control.lean (gold impl) exit=0, `#print axioms` => no axioms. Verifies cleanly.

Only the gold-equivalent echo (atk_7) closes with clean axioms; its materialized faithful patch was RUN through the official Docker harness and RESOLVED. Every genuinely-wrong impl (partial-domain, inverted, order-swap, effect-drop, tail-drop, boundary-dup, prepatch) FAILS to verify. No verifying same-spec impl has a non-resolving faithful patch => no BROKEN condition.

REFINEMENT.MD AUDIT: legs 1-2 = R, leg 3 = I (the changed gate `if !skipChecks`), legs 4-9 = R. NO A-legs (no consumed/referenced callee axiom): the changed decision is modeled DEEPLY as a gated list construction over observable StartupAction values, not axiomatized (SPEC_GUIDE §3). `#print axioms` confirms correct_serverStartup depends on NO axioms; axiom_check.py is a correct no-op skip. No kind-3 leg; no A-leg callee correspondence to validate/break. R/I legs are G-CONF's mechanized surface.

PARALLELISM: attacks verified in two concurrent batches of 4 (atk_1-4, atk_5-8) as background lean_verify jobs; axiom checks for the two verifying files run concurrently. Resolve run for atk_7 executed under sg-docker (contended host, concurrent processes active) and completed non-flaky.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl closes its proof. The postcondition pins the output by full list equality to the input-grounded expression (if skipChecks then [] else [announceChecks, runChecks]) ++ tailSteps, total over the 2-valued Bool domain, so any verifying impl is behaviorally identical to gold on both inputs.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Optionally skipping system checks when starting the development server.

The development server's startup routine performs a set sequence of steps
before it begins serving requests. One of those steps runs the project's system
checks, which can be slow during iterative development. A boolean control
(`skipChecks`) selects whether that step is performed.

We model the startup routine as the ordered list of observable actions it emits.
The system-check step consists of two observable actions: announcing that checks
are about to be performed, and running the checks themselves. When `skipChecks`
holds, both actions are omitted and the routine proceeds directly to the
remaining steps. When it does not hold, the system-check step is emitted first,
in order, ahead of the remaining steps. The remaining steps — verifying pending
migrations, writing the startup banner, and beginning to serve requests — are
always emitted, in the same order, regardless of the control.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the startup
-- routine's observable behavior is modeled structurally as the ordered list of
-- actions it emits, gated on a boolean control, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- An observable action emitted by the development server's startup routine.
* `announceChecks` — announce that the system-check step is about to run;
* `runChecks` — run the project's system checks;
* `checkMigrations` — verify that there are no unapplied migrations;
* `writeBanner` — write the startup banner (version, address, port);
* `serve` — begin serving requests. -/
inductive StartupAction
  | announceChecks
  | runChecks
  | checkMigrations
  | writeBanner
  | serve
deriving DecidableEq, Repr, Inhabited

/-- The steps that are always emitted, in order, after the (optional)
system-check step. -/
def tailSteps : List StartupAction :=
  [StartupAction.checkMigrations, StartupAction.writeBanner, StartupAction.serve]
-- pure-end

-- post-conditions-start
/-- The startup routine emits the system-check step (announcement then the
checks themselves) iff checks are not skipped, followed always by the remaining
steps in their set order. The result is fully determined by `skipChecks`:
the unchanged tail is pinned to its constant value in both cases, and the gated
prefix is present exactly when `skipChecks` is false. -/
def problem_spec_serverStartup (skipChecks : Bool) (result : List StartupAction) : Prop :=
  result =
    (if skipChecks then [] else [StartupAction.announceChecks, StartupAction.runChecks]) ++ tailSteps
-- post-conditions-end

-- impl-start
def implementation_serverStartup (skipChecks : Bool) : List StartupAction := Id.run do
  let mut log : List StartupAction := []
  if !skipChecks then
    log := log ++ [StartupAction.announceChecks]
    log := log ++ [StartupAction.runChecks]
  log := log ++ [StartupAction.checkMigrations]
  log := log ++ [StartupAction.writeBanner]
  log := log ++ [StartupAction.serve]
  return log
-- impl-end

-- proof-start
theorem correct_serverStartup :
    ∀ (skipChecks : Bool),
      problem_spec_serverStartup skipChecks
        (implementation_serverStartup skipChecks) := by
  intro skipChecks
  unfold problem_spec_serverStartup implementation_serverStartup tailSteps
  cases skipChecks <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND (verify => correct holds). 8 same-spec attacks (all same_spec=True) + positive control + prepatch reproduction. Verify tool: `bash scripts/lean_verify.sh <file>` from project root.

### Attack results
- atk_1.lean (PREPATCH bug: system-check emitted unconditionally, ignores skipChecks): exit=1 — `cases skipChecks <;> rfl` fails to reduce the skipChecks=true branch. prepatch_reproduced=true.
- atk_2.lean (inverted gate: emit iff skipChecks): exit=1.
- atk_3.lean (swapped order: runChecks before announceChecks): exit=1.
- atk_4.lean (partial-domain: never emit system-check step; correct only on true): exit=1.
- atk_5.lean (dropped tail step: serve missing): exit=1.
- atk_6.lean (control-flow effect: announces but never runs checks): exit=1.
- atk_7.lean (ungrounded-oracle ECHO: impl literally = spec RHS, gold-equivalent): exit=0, `#print axioms correct_serverStartup` => 'does not depend on any axioms' (CLEAN). Faithful patch = gold post-patch behavior (system-check gated on not skip_checks, tail always). RESOLVE RUN via run_resolve('django__django-13809', patch, run_id='sbu-audit-atk7b'): RESOLVED=True, COMPLETED=True, FLAKY=False, detail='resolved'. => echo does NOT break the spec (its faithful patch RESOLVES), consistent with the G-PANEL-1/eq resolve policy.
- atk_8.lean (boundary: duplicate runChecks emission): exit=1.

POSITIVE CONTROL: pos_control.lean (gold impl) exit=0, `#print axioms` => no axioms. Verifies cleanly.

Only the gold-equivalent echo (atk_7) closes with clean axioms; its materialized faithful patch was RUN through the official Docker harness and RESOLVED. Every genuinely-wrong impl (partial-domain, inverted, order-swap, effect-drop, tail-drop, boundary-dup, prepatch) FAILS to verify. No verifying same-spec impl has a non-resolving faithful patch => no BROKEN condition.

REFINEMENT.MD AUDIT: legs 1-2 = R, leg 3 = I (the changed gate `if !skipChecks`), legs 4-9 = R. NO A-legs (no consumed/referenced callee axiom): the changed decision is modeled DEEPLY as a gated list construction over observable StartupAction values, not axiomatized (SPEC_GUIDE §3). `#print axioms` confirms correct_serverStartup depends on NO axioms; axiom_check.py is a correct no-op skip. No kind-3 leg; no A-leg callee correspondence to validate/break. R/I legs are G-CONF's mechanized surface.

PARALLELISM: attacks verified in two concurrent batches of 4 (atk_1-4, atk_5-8) as background lean_verify jobs; axiom checks for the two verifying files run concurrently. Resolve run for atk_7 executed under sg-docker (contended host, concurrent processes active) and completed non-flaky.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) attack on django__django-13809 lean bundle. VERIFICATION: (1) Solution.lean compiles via lean_verify.sh, exit 0, no sorry. (2) `#print axioms correct_serverStartup` => 'does not depend on any axioms' — proof is genuine, not sorryAx. (3) Spec region byte-identical with Solution_prepatch.lean: markers.same_spec(patch, prepatch, LeanBackend.language) == True — mutation confined to impl/proof, spec unchanged.

MODELED CALLEE: runserver Command.inner_run (post-patch). Spec: problem_spec_serverStartup skipChecks result := result = (if skipChecks then [] else [announceChecks, runChecks]) ++ [checkMigrations, writeBanner, serve].

REAL POST-PATCH CODE (verified against base_commit bef6f7584280 worktree + patch.diff): `if not options['skip_checks']: stdout.write('Performing system checks...'); self.check` then unconditionally check_migrations(); banner write; run.

INPUT DOMAIN is a single Bool. Exhaustive enumeration:
  - skipChecks=false: spec=[announceChecks,runChecks,checkMigrations,writeBanner,serve] == real emitted order ✓
  - skipChecks=true:  spec=[checkMigrations,writeBanner,serve] (system-check step omitted) == real emitted order ✓
The spec agrees with the real callee on EVERY input in the modeled domain; there is no diverging input. The abstraction (modeling side-effecting steps as an ordered action trace, dropping pure setup / OSError error-formatting paths that the F2P test does not observe) is a sound modeling boundary, not a drift: the trace order is exactly what the real code emits and exactly what test_skip_checks asserts. The spec pins the result EXACTLY (full list equality grounded in skipChecks) — neither too strong nor too weak, and consistent with the real behavior. No faithfulness break found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = docstring + axioms + pure + post-conditions regions (impl and proof elided). Public problem_statement already discloses the entire feature verbatim: 'Add --skip-checks option to the runserver command' to skip system checks. Assessed each spec-view element:

1. Prose docstring: describes a boolean `skipChecks` control that omits the announce/run-checks step when set, remaining steps always run. This is the natural restatement of the publicly-requested behavior; no gold-edit specifics.
2. Postcondition `result = (if skipChecks then [] else [announceChecks, runChecks]) ++ tailSteps`: a natural formalization of the public request ('when the option is set, skip the system checks'). Does not exceed problem_statement.
3. The announce/run-checks two-action decomposition models PRE-EXISTING repo behavior (the 'Performing system checks...' write + self.check call already existed before the patch) — it is not the gold edit, so it cannot leak it.
4. The tailSteps (checkMigrations/writeBanner/serve) are UNCHANGED by the gold patch — surrounding modeling framing, not the edit.

The actual gold-edit mechanics the consumer must reconstruct — the `add_arguments`/`--skip-checks` registration, `options['skip_checks']` access, and the placement of the `if not options['skip_checks']:` guard around the two-line system-check block in inner_run — are all elided (impl region hidden) and only derivable from the public statement, not disclosed by any spec-view line. Verified spec_view region hash in meta matches (9a1c01ef...). No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
