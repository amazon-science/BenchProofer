# P2 adversarial audit — django__django-11292

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,10 @@
 -- impl-start
 def implementation_runCommand
     (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
-  -- A skip option is registered for this command exactly when it performs checks.
-  let skipOptionAvailable := commandPerformsChecks
-  -- A skip request for a command with no such option is not recognised.
-  if skipRequested && !skipOptionAvailable then
+  -- BUG (prepatch): --skip-checks is never registered, so any skip request is rejected.
+  if skipRequested then
     return RunResult.unrecognizedOption
-  -- When the option is available, an absent request reads as "do not skip".
-  let skip := skipRequested
-  if commandPerformsChecks && !skip then
+  if commandPerformsChecks then
     return RunResult.ranChecks
   return RunResult.skippedChecks
 -- impl-end
@@ -97,5 +93,6 @@
   intro commandPerformsChecks skipRequested
   refine ⟨?_, ?_, ?_, ?_⟩ <;>
     intro h1 h2 <;>
-    subst h1 <;> subst h2 <;> rfl
+    subst h1 <;> subst h2 <;>
+    first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,11 @@
 -- impl-start
 def implementation_runCommand
     (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
-  -- A skip option is registered for this command exactly when it performs checks.
   let skipOptionAvailable := commandPerformsChecks
-  -- A skip request for a command with no such option is not recognised.
   if skipRequested && !skipOptionAvailable then
     return RunResult.unrecognizedOption
-  -- When the option is available, an absent request reads as "do not skip".
-  let skip := skipRequested
-  if commandPerformsChecks && !skip then
+  -- BUG: run checks whenever the command performs checks, ignoring the skip flag
+  if commandPerformsChecks then
     return RunResult.ranChecks
   return RunResult.skippedChecks
 -- impl-end
@@ -97,5 +94,6 @@
   intro commandPerformsChecks skipRequested
   refine ⟨?_, ?_, ?_, ?_⟩ <;>
     intro h1 h2 <;>
-    subst h1 <;> subst h2 <;> rfl
+    subst h1 <;> subst h2 <;>
+    first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,8 @@
 -- impl-start
 def implementation_runCommand
     (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
-  -- A skip option is registered for this command exactly when it performs checks.
-  let skipOptionAvailable := commandPerformsChecks
-  -- A skip request for a command with no such option is not recognised.
-  if skipRequested && !skipOptionAvailable then
-    return RunResult.unrecognizedOption
-  -- When the option is available, an absent request reads as "do not skip".
-  let skip := skipRequested
-  if commandPerformsChecks && !skip then
+  -- BUG: never emits unrecognizedOption; treats every launch as valid
+  if commandPerformsChecks && !skipRequested then
     return RunResult.ranChecks
   return RunResult.skippedChecks
 -- impl-end
@@ -97,5 +91,6 @@
   intro commandPerformsChecks skipRequested
   refine ⟨?_, ?_, ?_, ?_⟩ <;>
     intro h1 h2 <;>
-    subst h1 <;> subst h2 <;> rfl
+    subst h1 <;> subst h2 <;>
+    first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,15 +77,7 @@
 -- impl-start
 def implementation_runCommand
     (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
-  -- A skip option is registered for this command exactly when it performs checks.
-  let skipOptionAvailable := commandPerformsChecks
-  -- A skip request for a command with no such option is not recognised.
-  if skipRequested && !skipOptionAvailable then
-    return RunResult.unrecognizedOption
-  -- When the option is available, an absent request reads as "do not skip".
-  let skip := skipRequested
-  if commandPerformsChecks && !skip then
-    return RunResult.ranChecks
+  -- BUG: always skips checks
   return RunResult.skippedChecks
 -- impl-end
 
@@ -97,5 +89,6 @@
   intro commandPerformsChecks skipRequested
   refine ⟨?_, ?_, ?_, ?_⟩ <;>
     intro h1 h2 <;>
-    subst h1 <;> subst h2 <;> rfl
+    subst h1 <;> subst h2 <;>
+    first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,11 @@
 -- impl-start
 def implementation_runCommand
     (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
-  -- A skip option is registered for this command exactly when it performs checks.
   let skipOptionAvailable := commandPerformsChecks
-  -- A skip request for a command with no such option is not recognised.
-  if skipRequested && !skipOptionAvailable then
+  -- BUG: rejects even the no-skip launch for a no-check command
+  if !skipOptionAvailable then
     return RunResult.unrecognizedOption
-  -- When the option is available, an absent request reads as "do not skip".
-  let skip := skipRequested
-  if commandPerformsChecks && !skip then
+  if commandPerformsChecks && !skipRequested then
     return RunResult.ranChecks
   return RunResult.skippedChecks
 -- impl-end
@@ -97,5 +94,6 @@
   intro commandPerformsChecks skipRequested
   refine ⟨?_, ?_, ?_, ?_⟩ <;>
     intro h1 h2 <;>
-    subst h1 <;> subst h2 <;> rfl
+    subst h1 <;> subst h2 <;>
+    first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,13 @@
 -- impl-start
 def implementation_runCommand
     (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
-  -- A skip option is registered for this command exactly when it performs checks.
   let skipOptionAvailable := commandPerformsChecks
-  -- A skip request for a command with no such option is not recognised.
   if skipRequested && !skipOptionAvailable then
     return RunResult.unrecognizedOption
-  -- When the option is available, an absent request reads as "do not skip".
-  let skip := skipRequested
-  if commandPerformsChecks && !skip then
+  -- BUG: a requested skip on a checking command RUNS the checks anyway
+  if commandPerformsChecks then
+    if skipRequested then
+      return RunResult.ranChecks
     return RunResult.ranChecks
   return RunResult.skippedChecks
 -- impl-end
@@ -97,5 +96,6 @@
   intro commandPerformsChecks skipRequested
   refine ⟨?_, ?_, ?_, ?_⟩ <;>
     intro h1 h2 <;>
-    subst h1 <;> subst h2 <;> rfl
+    subst h1 <;> subst h2 <;>
+    first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Letting a command-line invocation skip a command's pre-run checks.

A management command, before it does its work, may run a battery of project
"system checks". Whether a command runs those checks at all is an inherent
property of that command (`commandPerformsChecks`): some commands always check first,
others never check.

This bundle models the decision the command makes when it is launched from the
command line, given whether the launch *asked* to skip the checks
(`skipRequested`). There are three possible outcomes:

  * `unrecognizedOption` — the launch asked to skip checks but this command does
    not offer a skip option, so the request is not a recognised command-line
    option and the launch is rejected;
  * `ranChecks`          — the command ran its system checks before proceeding;
  * `skippedChecks`      — the command proceeded without running system checks.

The desired behavior: a command exposes a "skip" option exactly when it performs
checks. When a skip is asked of such a command, the checks are skipped; when no
skip is asked, such a command runs its checks. A command that performs no checks
proceeds without checking and offers no skip option, so a skip request aimed at
it is an unrecognised option.

Inputs:
  * `commandPerformsChecks` — whether this command runs system checks by default;
  * `skipRequested`         — whether the launch asked to skip the checks.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- command runs its checks by default enters as the plain `commandPerformsChecks`
-- datum; whether the launch asked to skip enters as the plain `skipRequested`
-- datum. The act of running the checks is observed only as WHETHER it happens
-- (`ranChecks` vs `skippedChecks`), never by its internals, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The outcome of launching a command from the command line, restricted to the
touched behavior: whether the skip request was a recognised option, and whether
the system checks ran. -/
inductive RunResult
  | unrecognizedOption
  | ranChecks
  | skippedChecks
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The launch outcome is fully pinned to the two inputs (the Boolean × Boolean
domain is covered exhaustively, so no component of the result is left free):

  * a command that performs no checks and is not asked to skip simply proceeds
    without checking (`skippedChecks`);
  * a command that performs no checks but IS asked to skip rejects the request as
    an unrecognised option (it offers no skip option) (`unrecognizedOption`);
  * a command that performs checks and is asked to skip them skips them
    (`skippedChecks`);
  * a command that performs checks and is not asked to skip runs them
    (`ranChecks`). -/
def problem_spec_runCommand
    (commandPerformsChecks skipRequested : Bool) (result : RunResult) : Prop :=
  (commandPerformsChecks = false → skipRequested = false →
      result = RunResult.skippedChecks) ∧
  (commandPerformsChecks = false → skipRequested = true →
      result = RunResult.unrecognizedOption) ∧
  (commandPerformsChecks = true → skipRequested = true →
      result = RunResult.skippedChecks) ∧
  (commandPerformsChecks = true → skipRequested = false →
      result = RunResult.ranChecks)
-- post-conditions-end

-- impl-start
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  -- A skip option is registered for this command exactly when it performs checks.
  let skipOptionAvailable := commandPerformsChecks
  -- A skip request for a command with no such option is not recognised.
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  -- When the option is available, an absent request reads as "do not skip".
  let skip := skipRequested
  if commandPerformsChecks && !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks
-- impl-end

-- proof-start
theorem correct_runCommand :
    ∀ (commandPerformsChecks skipRequested : Bool),
      problem_spec_runCommand commandPerformsChecks skipRequested
        (implementation_runCommand commandPerformsChecks skipRequested) := by
  intro commandPerformsChecks skipRequested
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    intro h1 h2 <;>
    subst h1 <;> subst h2 <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_runCommand is a FULLY-DETERMINED TOTAL spec: all four Bool x Bool inputs are pinned to a unique RunResult (F,F->skippedChecks; F,T->unrecognizedOption; T,T->skippedChecks; T,F->ranChecks). Any wrong impl differs on >=1 input and cannot honestly close.

All 7 files same_spec=True vs Solution.lean (impl region only edited; axioms/pure/pre/post byte-identical). Verifications run concurrently (<=4 at a time) via `bash scripts/lean_verify.sh <f>`. Each attack used an aggressive proof closer `first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]`.

Results:
- positive_control.lean: EXIT 0 (verifies, no sorry). #print axioms correct_runCommand -> 'does not depend on any axioms' (clean).
- atk_1 (prepatch bug: skipRequested always -> unrecognizedOption): EXIT 1, error unsolved goals @92:75. Prepatch reproduced.
- atk_2 (boundary: (T,T)->ranChecks not skippedChecks): EXIT 1, unsolved goals @93:75.
- atk_3 (control-flow-effect: drop unrecognizedOption guard, treat all launches valid): EXIT 1, unsolved goals @90:75.
- atk_4 (ungrounded-oracle echo: const skippedChecks): EXIT 1, unsolved goals @88:75.
- atk_5 (partial-domain: !skipOptionAvailable -> unrecognizedOption, breaks (F,F)): EXIT 1, unsolved goals @93:75.
- atk_6 (outcome-swap: requested skip on checking command still ranChecks): EXIT 1, unsolved goals @95:75.

All 6 wrong impls fail with genuine 'error: unsolved goals' (NOT sorry, NOT timeout). No wrong impl closed with clean axioms, so no faithful patch needed materialization/resolve (patches={}).

refinement.md audit: 5 legs, all tagged R (type-refinement); no kind-3 legs. meta.json axioms=[] and deep_model_references=[] are correct: self.check() is observed only as the outcome (ranChecks vs skippedChecks), never as an axiomatized/opaque callee contract, so there are NO A-consumed or A-reference legs to correspond against real callees. The A-leg surface is vacuous and correctly so; R/I legs are covered by G-CONF (conf_skip=false). G-AX skip stub is justified.

Verdict: SOUND. >=6 distinct same-spec wrong impls (prepatch + boundary + control-flow + ungrounded-oracle echo + partial-domain + outcome-swap) all failed to produce a closing clean-axiom proof; positive control verifies with clean axioms. verify => correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Letting a command-line invocation skip a command's pre-run checks.

A management command, before it does its work, may run a battery of project
"system checks". Whether a command runs those checks at all is an inherent
property of that command (`commandPerformsChecks`): some commands always check first,
others never check.

This bundle models the decision the command makes when it is launched from the
command line, given whether the launch *asked* to skip the checks
(`skipRequested`). There are three possible outcomes:

  * `unrecognizedOption` — the launch asked to skip checks but this command does
    not offer a skip option, so the request is not a recognised command-line
    option and the launch is rejected;
  * `ranChecks`          — the command ran its system checks before proceeding;
  * `skippedChecks`      — the command proceeded without running system checks.

The desired behavior: a command exposes a "skip" option exactly when it performs
checks. When a skip is asked of such a command, the checks are skipped; when no
skip is asked, such a command runs its checks. A command that performs no checks
proceeds without checking and offers no skip option, so a skip request aimed at
it is an unrecognised option.

Inputs:
  * `commandPerformsChecks` — whether this command runs system checks by default;
  * `skipRequested`         — whether the launch asked to skip the checks.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether a
-- command runs its checks by default enters as the plain `commandPerformsChecks`
-- datum; whether the launch asked to skip enters as the plain `skipRequested`
-- datum. The act of running the checks is observed only as WHETHER it happens
-- (`ranChecks` vs `skippedChecks`), never by its internals, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The outcome of launching a command from the command line, restricted to the
touched behavior: whether the skip request was a recognised option, and whether
the system checks ran. -/
inductive RunResult
  | unrecognizedOption
  | ranChecks
  | skippedChecks
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The launch outcome is fully pinned to the two inputs (the Boolean × Boolean
domain is covered exhaustively, so no component of the result is left free):

  * a command that performs no checks and is not asked to skip simply proceeds
    without checking (`skippedChecks`);
  * a command that performs no checks but IS asked to skip rejects the request as
    an unrecognised option (it offers no skip option) (`unrecognizedOption`);
  * a command that performs checks and is asked to skip them skips them
    (`skippedChecks`);
  * a command that performs checks and is not asked to skip runs them
    (`ranChecks`). -/
def problem_spec_runCommand
    (commandPerformsChecks skipRequested : Bool) (result : RunResult) : Prop :=
  (commandPerformsChecks = false → skipRequested = false →
      result = RunResult.skippedChecks) ∧
  (commandPerformsChecks = false → skipRequested = true →
      result = RunResult.unrecognizedOption) ∧
  (commandPerformsChecks = true → skipRequested = true →
      result = RunResult.skippedChecks) ∧
  (commandPerformsChecks = true → skipRequested = false →
      result = RunResult.ranChecks)
-- post-conditions-end

-- impl-start
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  -- A skip option is registered for this command exactly when it performs checks.
  let skipOptionAvailable := commandPerformsChecks
  -- A skip request for a command with no such option is not recognised.
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  -- When the option is available, an absent request reads as "do not skip".
  let skip := skipRequested
  if commandPerformsChecks && !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks
-- impl-end

-- proof-start
theorem correct_runCommand :
    ∀ (commandPerformsChecks skipRequested : Bool),
      problem_spec_runCommand commandPerformsChecks skipRequested
        (implementation_runCommand commandPerformsChecks skipRequested) := by
  intro commandPerformsChecks skipRequested
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    intro h1 h2 <;>
    subst h1 <;> subst h2 <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_runCommand is a FULLY-DETERMINED TOTAL spec: all four Bool x Bool inputs are pinned to a unique RunResult (F,F->skippedChecks; F,T->unrecognizedOption; T,T->skippedChecks; T,F->ranChecks). Any wrong impl differs on >=1 input and cannot honestly close.

All 7 files same_spec=True vs Solution.lean (impl region only edited; axioms/pure/pre/post byte-identical). Verifications run concurrently (<=4 at a time) via `bash scripts/lean_verify.sh <f>`. Each attack used an aggressive proof closer `first | rfl | decide | simp_all [implementation_runCommand, problem_spec_runCommand]`.

Results:
- positive_control.lean: EXIT 0 (verifies, no sorry). #print axioms correct_runCommand -> 'does not depend on any axioms' (clean).
- atk_1 (prepatch bug: skipRequested always -> unrecognizedOption): EXIT 1, error unsolved goals @92:75. Prepatch reproduced.
- atk_2 (boundary: (T,T)->ranChecks not skippedChecks): EXIT 1, unsolved goals @93:75.
- atk_3 (control-flow-effect: drop unrecognizedOption guard, treat all launches valid): EXIT 1, unsolved goals @90:75.
- atk_4 (ungrounded-oracle echo: const skippedChecks): EXIT 1, unsolved goals @88:75.
- atk_5 (partial-domain: !skipOptionAvailable -> unrecognizedOption, breaks (F,F)): EXIT 1, unsolved goals @93:75.
- atk_6 (outcome-swap: requested skip on checking command still ranChecks): EXIT 1, unsolved goals @95:75.

All 6 wrong impls fail with genuine 'error: unsolved goals' (NOT sorry, NOT timeout). No wrong impl closed with clean axioms, so no faithful patch needed materialization/resolve (patches={}).

refinement.md audit: 5 legs, all tagged R (type-refinement); no kind-3 legs. meta.json axioms=[] and deep_model_references=[] are correct: self.check() is observed only as the outcome (ranChecks vs skippedChecks), never as an axiomatized/opaque callee contract, so there are NO A-consumed or A-reference legs to correspond against real callees. The A-leg surface is vacuous and correctly so; R/I legs are covered by G-CONF (conf_skip=false). G-AX skip stub is justified.

Verdict: SOUND. >=6 distinct same-spec wrong impls (prepatch + boundary + control-flow + ungrounded-oracle echo + partial-domain + outcome-swap) all failed to produce a closing clean-axiom proof; positive control verifies with clean axioms. verify => correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. Modeled function `runCommand` is a Bool×Bool→RunResult composite of BaseCommand.create_parser (option registration) + BaseCommand.execute (check gate) for a command-line launch. Verified against the real repo at base_commit eb16c7260e (worktree, git show eb16c7260e:django/core/management/base.py) plus the gold patch.diff. All four domain points match the real post-patch behavior exactly: (F,F)->skippedChecks (option unregistered, execute gate's first conjunct false); (F,T)->unrecognizedOption (--skip-checks not registered => argparse 'unrecognized arguments'); (T,T)->skippedChecks (options['skip_checks']=True => gate false); (T,F)->ranChecks (options['skip_checks']=False => gate true => self.check()). The spec `problem_spec_runCommand` pins each of these clauses and NONE over-strengthens beyond real behavior — it is exactly the observable decision, no more. The unrecognizedOption leg is a faithful composite of the parse-time argparse rejection (consistent with the F2P test_skip_checks CLI shape). Rigor checks: lean_verify.sh exit 0; `#print axioms correct_runCommand` => 'does not depend on any axioms' (no sorryAx, genuine proof); same_spec(Solution, Solution_prepatch, lean)=True so the spec region is byte-identical between patched/prepatch. axioms=[] and deep_model_references=[] are justified: self.check() enters only as the ranChecks/skippedChecks outcome, never as a contract. No spec drift, no spec-too-strong. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (post/pure/comment regions; impl+proof elided) judged against the public problem_statement only. Mechanical G-LEAK screen passes (no diff markers, no gold-patch line reproduced, no patched file/module path, no spec-view identifier embedding a patched repo symbol {create_parser, execute, BaseCommand, DjangoHelpFormatter}, no bug/fix narration). same_spec(Solution, Solution_prepatch)=True, so the spec region is byte-identical and impl-independent. The Lean names are deliberately neutral behavioral names (runCommand, commandPerformsChecks, skipRequested, RunResult.{unrecognizedOption,ranChecks,skippedChecks}) — none echoes a patched symbol or path. The problem_statement already publicly discloses the '--skip-checks' option, management commands, the pre-existing skip_checks stealth option, and skipping checks when running from the command line; the spec's docstring only restates the DESIRED behavior (skip option offered iff command performs checks; a skip aimed at a non-checking command is unrecognized). That is the correctness semantics any faithful spec must encode, not a reveal of the edit's mechanics or localization (it never mentions parser argument registration, argparse, the execute check gate, base_stealth_options, or the .get()->[] tidy-up). No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
