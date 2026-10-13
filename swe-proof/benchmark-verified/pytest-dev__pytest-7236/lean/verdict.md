# P2 adversarial audit — pytest-dev__pytest-7236

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,8 @@
 def implementation_deferTeardown
     (isAsync usePdb skipped : Bool) : Bool := Id.run do
   if isAsync then
-    -- asynchronous path: the framework runs the case directly; no postponement
     return false
-  -- synchronous path: arrange postponement only under the debugger option, and
-  -- only when this case is going to actually run its teardown
-  if usePdb && !skipped then
+  if usePdb then
     return true
   return false
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,14 +60,7 @@
 -- impl-start
 def implementation_deferTeardown
     (isAsync usePdb skipped : Bool) : Bool := Id.run do
-  if isAsync then
-    -- asynchronous path: the framework runs the case directly; no postponement
-    return false
-  -- synchronous path: arrange postponement only under the debugger option, and
-  -- only when this case is going to actually run its teardown
-  if usePdb && !skipped then
-    return true
-  return false
+  return true
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,11 +60,6 @@
 -- impl-start
 def implementation_deferTeardown
     (isAsync usePdb skipped : Bool) : Bool := Id.run do
-  if isAsync then
-    -- asynchronous path: the framework runs the case directly; no postponement
-    return false
-  -- synchronous path: arrange postponement only under the debugger option, and
-  -- only when this case is going to actually run its teardown
   if usePdb && !skipped then
     return true
   return false
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,8 @@
 def implementation_deferTeardown
     (isAsync usePdb skipped : Bool) : Bool := Id.run do
   if isAsync then
-    -- asynchronous path: the framework runs the case directly; no postponement
     return false
-  -- synchronous path: arrange postponement only under the debugger option, and
-  -- only when this case is going to actually run its teardown
-  if usePdb && !skipped then
+  if usePdb || skipped then
     return true
   return false
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,13 +61,8 @@
 def implementation_deferTeardown
     (isAsync usePdb skipped : Bool) : Bool := Id.run do
   if isAsync then
-    -- asynchronous path: the framework runs the case directly; no postponement
     return false
-  -- synchronous path: arrange postponement only under the debugger option, and
-  -- only when this case is going to actually run its teardown
-  if usePdb && !skipped then
-    return true
-  return false
+  return !skipped
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,14 +60,10 @@
 -- impl-start
 def implementation_deferTeardown
     (isAsync usePdb skipped : Bool) : Bool := Id.run do
-  if isAsync then
-    -- asynchronous path: the framework runs the case directly; no postponement
+  if !isAsync && usePdb && !skipped then
+    return true
+  else
     return false
-  -- synchronous path: arrange postponement only under the debugger option, and
-  -- only when this case is going to actually run its teardown
-  if usePdb && !skipped then
-    return true
-  return false
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -59,15 +59,10 @@
 
 -- impl-start
 def implementation_deferTeardown
-    (isAsync usePdb skipped : Bool) : Bool := Id.run do
-  if isAsync then
-    -- asynchronous path: the framework runs the case directly; no postponement
-    return false
-  -- synchronous path: arrange postponement only under the debugger option, and
-  -- only when this case is going to actually run its teardown
-  if usePdb && !skipped then
-    return true
-  return false
+    (isAsync usePdb skipped : Bool) : Bool :=
+  match isAsync, usePdb, skipped with
+  | false, true, false => true
+  | _, _, _ => false
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Deferring a test case's teardown when running under an interactive debugger.

When a `unittest`-style test case is executed, its teardown step is normally run
immediately after the test body. When the interactive post-mortem debugger option
is active, the framework instead *postpones* teardown: it stores the bound
teardown method aside and temporarily replaces it with a no-op, so that the
instance state is still intact when the debugger prompt opens after a failure.

This postponement should only ever be arranged when teardown is actually going to
run for this test:

* a test case driven entirely by the asynchronous framework path arranges no such
  postponement;
* a test case that has been marked to skip has no teardown to debug, so its
  teardown must NOT be postponed (postponing it would arrange for a stored
  teardown to be invoked explicitly later, even though the test was skipped);
* only a non-asynchronous, non-skipped test case, run while the debugger option
  is active, has its teardown postponed.

The decision modeled here is exactly: was teardown postponement arranged for this
test case?
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- modeled structurally over the observable conditions of the test case (whether
-- it is driven by the asynchronous path, whether the interactive-debugger option
-- is active, and whether the case has been marked to skip), each of which enters
-- as a plain Boolean observation, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Whether teardown postponement is arranged for a test case, as a function of
its observable conditions:

* `isAsync` — the case is driven entirely by the asynchronous framework path;
* `usePdb` — the interactive post-mortem debugger option is active;
* `skipped` — the case has been marked to skip.

Postponement is arranged exactly for a non-asynchronous, non-skipped case while
the debugger option is active. -/
def teardownDeferralRule (isAsync usePdb skipped : Bool) : Bool :=
  !isAsync && usePdb && !skipped
-- pure-end

-- post-conditions-start
/-- The postponement decision for the test case is exactly the rule: it is
arranged only for a non-asynchronous, non-skipped case while the debugger option
is active. In particular a skipped case never has its teardown postponed. -/
def problem_spec_deferTeardown
    (isAsync usePdb skipped : Bool) (result : Bool) : Prop :=
  result = teardownDeferralRule isAsync usePdb skipped
-- post-conditions-end

-- impl-start
def implementation_deferTeardown
    (isAsync usePdb skipped : Bool) : Bool := Id.run do
  if isAsync then
    -- asynchronous path: the framework runs the case directly; no postponement
    return false
  -- synchronous path: arrange postponement only under the debugger option, and
  -- only when this case is going to actually run its teardown
  if usePdb && !skipped then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_deferTeardown :
    ∀ (isAsync usePdb skipped : Bool),
      problem_spec_deferTeardown isAsync usePdb skipped
        (implementation_deferTeardown isAsync usePdb skipped) := by
  intro isAsync usePdb skipped
  unfold problem_spec_deferTeardown teardownDeferralRule implementation_deferTeardown
  cases isAsync <;> cases usePdb <;> cases skipped <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL exact-equality over 3 Booleans: problem_spec := result = teardownDeferralRule isAsync usePdb skipped = (!isAsync && usePdb && !skipped). Any impl not extensionally equal to this rule cannot close correct_deferTeardown. Verified via `bash scripts/lean_verify.sh <f>` (run concurrently, <=4 at a time).

Results (all attacks same_spec=True, confirmed with swebench_unified.markers.same_spec):
- pos.lean (positive control, gold impl): exit 0; `#print axioms correct_deferTeardown` => does not depend on any axioms.
- atk_1 = PREPATCH BUG (drops `!skipped`, `if usePdb then return true`): exit 1 (proof cannot close, goal `(pure true).run = (!false && true && !true)` unsolvable). CONFIRMS the spec discriminates the F2P regression point (isAsync=false,usePdb=true,skipped=true) -> prepatch_reproduced=true.
- atk_2 = const true: exit 1 (rejected).
- atk_3 = drops `!isAsync` guard: exit 1 (rejected at (true,true,false)).
- atk_4 = boundary `usePdb || skipped`: exit 1 (rejected).
- atk_5 = control-flow `return !skipped` (ignores usePdb on sync path): exit 1 (rejected).
- atk_6 = ECHO, single `if !isAsync && usePdb && !skipped then true else false`: exit 0; clean axioms (no axioms).
- atk_7 = ECHO, `match isAsync,usePdb,skipped with | false,true,false => true | _ => false`: exit 0; clean axioms (no axioms).

Both closing proofs (atk_6, atk_7) compute EXACTLY the gold rule `not isAsync and usePdb and not skipped`, i.e. they are extensionally EQUAL echoes. Per the G-EQ / G-PANEL-1 echo policy a same-spec verifying candidate is a weakness ONLY if its faithful refined patch does NOT resolve. Both echoes' faithful patch is behaviorally the gold guard `if self.config.getoption("usepdb") and not _is_skipped(self.obj):` on the synchronous (else) branch, i.e. the gold patch. I MATERIALIZED that patch (patch_echo.diff = benchmark patch.diff) and RAN it through the official harness:
  run_resolve('pytest-dev__pytest-7236', patch_echo) => RESOLVED=True, COMPLETED=True, NOTE='resolved'.
So there is NO verifying same-spec impl whose faithful patch fails to resolve => no verify=>!resolve counterexample.

Refinement.md audit (plan section 4, A-leg focus): axioms region is EMPTY (`-- No unchanged outside callee is consumed`) — there are NO axioms/opaque callees, so NO A-consumed and NO A-reference legs and no deep-model references to validate. All 3 legs are R (Bool bijection: isAsync<->is_async_function(self.obj), usePdb<->getoption('usepdb') truthiness, skipped<->_is_skipped(self.obj)=bool(getattr(...,'__unittest_skip__',False))) or I (identical concrete op). No kind-3 leg present. `_is_skipped` is correctly NOT axiomatized: its Boolean result IS the modeled observable `skipped`; the two other patch sites (collect, _make_xunit_fixture) are truthiness-preserving refactors with no separate F2P coverage, consistent with mapping.md. Correspondence to the real callees holds.

Verdict: SOUND. 7 attacks run (>=5 required); the 5 genuinely-wrong impls all FAIL to verify (spec is tight), and the only 2 that verify are extensionally-equal echoes whose materialized faithful patch RESOLVES under the official harness. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Deferring a test case's teardown when running under an interactive debugger.

When a `unittest`-style test case is executed, its teardown step is normally run
immediately after the test body. When the interactive post-mortem debugger option
is active, the framework instead *postpones* teardown: it stores the bound
teardown method aside and temporarily replaces it with a no-op, so that the
instance state is still intact when the debugger prompt opens after a failure.

This postponement should only ever be arranged when teardown is actually going to
run for this test:

* a test case driven entirely by the asynchronous framework path arranges no such
  postponement;
* a test case that has been marked to skip has no teardown to debug, so its
  teardown must NOT be postponed (postponing it would arrange for a stored
  teardown to be invoked explicitly later, even though the test was skipped);
* only a non-asynchronous, non-skipped test case, run while the debugger option
  is active, has its teardown postponed.

The decision modeled here is exactly: was teardown postponement arranged for this
test case?
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- modeled structurally over the observable conditions of the test case (whether
-- it is driven by the asynchronous path, whether the interactive-debugger option
-- is active, and whether the case has been marked to skip), each of which enters
-- as a plain Boolean observation, so no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Whether teardown postponement is arranged for a test case, as a function of
its observable conditions:

* `isAsync` — the case is driven entirely by the asynchronous framework path;
* `usePdb` — the interactive post-mortem debugger option is active;
* `skipped` — the case has been marked to skip.

Postponement is arranged exactly for a non-asynchronous, non-skipped case while
the debugger option is active. -/
def teardownDeferralRule (isAsync usePdb skipped : Bool) : Bool :=
  !isAsync && usePdb && !skipped
-- pure-end

-- post-conditions-start
/-- The postponement decision for the test case is exactly the rule: it is
arranged only for a non-asynchronous, non-skipped case while the debugger option
is active. In particular a skipped case never has its teardown postponed. -/
def problem_spec_deferTeardown
    (isAsync usePdb skipped : Bool) (result : Bool) : Prop :=
  result = teardownDeferralRule isAsync usePdb skipped
-- post-conditions-end

-- impl-start
def implementation_deferTeardown
    (isAsync usePdb skipped : Bool) : Bool := Id.run do
  if isAsync then
    -- asynchronous path: the framework runs the case directly; no postponement
    return false
  -- synchronous path: arrange postponement only under the debugger option, and
  -- only when this case is going to actually run its teardown
  if usePdb && !skipped then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_deferTeardown :
    ∀ (isAsync usePdb skipped : Bool),
      problem_spec_deferTeardown isAsync usePdb skipped
        (implementation_deferTeardown isAsync usePdb skipped) := by
  intro isAsync usePdb skipped
  unfold problem_spec_deferTeardown teardownDeferralRule implementation_deferTeardown
  cases isAsync <;> cases usePdb <;> cases skipped <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL exact-equality over 3 Booleans: problem_spec := result = teardownDeferralRule isAsync usePdb skipped = (!isAsync && usePdb && !skipped). Any impl not extensionally equal to this rule cannot close correct_deferTeardown. Verified via `bash scripts/lean_verify.sh <f>` (run concurrently, <=4 at a time).

Results (all attacks same_spec=True, confirmed with swebench_unified.markers.same_spec):
- pos.lean (positive control, gold impl): exit 0; `#print axioms correct_deferTeardown` => does not depend on any axioms.
- atk_1 = PREPATCH BUG (drops `!skipped`, `if usePdb then return true`): exit 1 (proof cannot close, goal `(pure true).run = (!false && true && !true)` unsolvable). CONFIRMS the spec discriminates the F2P regression point (isAsync=false,usePdb=true,skipped=true) -> prepatch_reproduced=true.
- atk_2 = const true: exit 1 (rejected).
- atk_3 = drops `!isAsync` guard: exit 1 (rejected at (true,true,false)).
- atk_4 = boundary `usePdb || skipped`: exit 1 (rejected).
- atk_5 = control-flow `return !skipped` (ignores usePdb on sync path): exit 1 (rejected).
- atk_6 = ECHO, single `if !isAsync && usePdb && !skipped then true else false`: exit 0; clean axioms (no axioms).
- atk_7 = ECHO, `match isAsync,usePdb,skipped with | false,true,false => true | _ => false`: exit 0; clean axioms (no axioms).

Both closing proofs (atk_6, atk_7) compute EXACTLY the gold rule `not isAsync and usePdb and not skipped`, i.e. they are extensionally EQUAL echoes. Per the G-EQ / G-PANEL-1 echo policy a same-spec verifying candidate is a weakness ONLY if its faithful refined patch does NOT resolve. Both echoes' faithful patch is behaviorally the gold guard `if self.config.getoption("usepdb") and not _is_skipped(self.obj):` on the synchronous (else) branch, i.e. the gold patch. I MATERIALIZED that patch (patch_echo.diff = benchmark patch.diff) and RAN it through the official harness:
  run_resolve('pytest-dev__pytest-7236', patch_echo) => RESOLVED=True, COMPLETED=True, NOTE='resolved'.
So there is NO verifying same-spec impl whose faithful patch fails to resolve => no verify=>!resolve counterexample.

Refinement.md audit (plan section 4, A-leg focus): axioms region is EMPTY (`-- No unchanged outside callee is consumed`) — there are NO axioms/opaque callees, so NO A-consumed and NO A-reference legs and no deep-model references to validate. All 3 legs are R (Bool bijection: isAsync<->is_async_function(self.obj), usePdb<->getoption('usepdb') truthiness, skipped<->_is_skipped(self.obj)=bool(getattr(...,'__unittest_skip__',False))) or I (identical concrete op). No kind-3 leg present. `_is_skipped` is correctly NOT axiomatized: its Boolean result IS the modeled observable `skipped`; the two other patch sites (collect, _make_xunit_fixture) are truthiness-preserving refactors with no separate F2P coverage, consistent with mapping.md. Correspondence to the real callees holds.

Verdict: SOUND. 7 attacks run (>=5 required); the 5 genuinely-wrong impls all FAIL to verify (spec is tight), and the only 2 that verify are extensionally-equal echoes whose materialized faithful patch RESOLVES under the official harness. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found. The spec models the exact decision 'was teardown postponement arranged for this TestCaseFunction.runtest' as an equality post-condition: problem_spec_deferTeardown result := (result = teardownDeferralRule isAsync usePdb skipped) where teardownDeferralRule = !isAsync && usePdb && !skipped.

Real repo (base_commit c98bc4cd3, worktree) runtest logic, post-patch:
  if is_async_function(self.obj): <async path, postponement code never reached>  => result False
  else: if self.config.getoption('usepdb') and not _is_skipped(self.obj): <arrange postponement> => True; else False
with _is_skipped(obj)=bool(getattr(obj,'__unittest_skip__',False)) (helper added by patch). This is exactly (not isAsync) and usePdb and (not skipped).

Exhaustive over the full 3-Boolean input space (8 points) the modeled function agrees with the real callee on every point, including the soundness-critical fix point (isAsync=false,usePdb=true,skipped=true) -> False (skipped case NOT postponed), matching F2P test test_pdb_teardown_skipped. Async branch (isAsync=true) -> False on all sub-cases. No input where spec disagrees with real behavior.

Mapping is faithful: three plain Boolean observables bound to is_async_function(self.obj), getoption('usepdb') truthiness, and _is_skipped(self.obj); result = postponement arranged. The two other patch sites (collect's skipped=_is_skipped(cls) and xunit fixture) are truthiness-preserving refactors with no observable behavior change, correctly excluded from the modeled decision.

Checks performed: spec region byte-identical with Solution_prepatch.lean via swebench_unified.markers.same_spec (lean backend) -> True; lean_verify.sh Solution.lean exit 0 (compiles, no sorry); '#print axioms correct_deferTeardown' -> 'does not depend on any axioms' (genuine proof, no sorryAx). Prepatch impl drops the !skipped conjunct and fails against the same unchanged spec, confirming the spec is neither too strong nor too weak. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, lean_backend)=True (spec region byte-identical). Spec view = docstring + teardownDeferralRule (!isAsync && usePdb && !skipped) + problem_spec equality; impl/proof elided. The public problem_statement already discloses the full target behavior: tearDown executed on @unittest.skip tests under --pdb is a 5.4.1->5.4.2 regression, and 'I would have expected the test to be skipped, even with --pdb'. The spec's two decisive knobs (usePdb, skipped) are exactly the reproducer's --pdb flag and @unittest.skip marker; the modeled claim 'a skipped case is never postponed under the debugger option' is a direct formalization of the public desired behavior. The gold edit's mechanism/location (the _is_skipped helper, the 'and not _is_skipped(self.obj)' guard text, src/_pytest/unittest.py:223) appears nowhere in the spec view. The only observable beyond the public text, isAsync, is pre-existing sync/async structural framing that the gold patch does not touch, so it does not aid fix reconstruction. Stating the already-public desired behavior is legitimate spec content, not leakage. No spec-view line reveals the gold edit beyond the public problem_statement (hints excluded per policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
