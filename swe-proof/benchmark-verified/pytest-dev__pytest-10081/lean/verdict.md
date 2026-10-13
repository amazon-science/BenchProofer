# P2 adversarial audit — pytest-dev__pytest-10081

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,8 +58,7 @@
 -- impl-start
 def implementation_deferTeardown
     (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
-  let skipped := testItselfSkipped || classSkipped
-  if pdbEnabled && !skipped then
+  if pdbEnabled && !testItselfSkipped then
     return true
   return false
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
 -- impl-start
 def implementation_deferTeardown
     (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
-  let skipped := testItselfSkipped || classSkipped
+  let skipped := testItselfSkipped && classSkipped
   if pdbEnabled && !skipped then
     return true
   return false
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,8 +58,7 @@
 -- impl-start
 def implementation_deferTeardown
     (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
-  let skipped := testItselfSkipped || classSkipped
-  if pdbEnabled && !skipped then
+  if pdbEnabled && !classSkipped then
     return true
   return false
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,9 +59,7 @@
 def implementation_deferTeardown
     (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
   let skipped := testItselfSkipped || classSkipped
-  if pdbEnabled && !skipped then
-    return true
-  return false
+  return !skipped
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,9 +58,6 @@
 -- impl-start
 def implementation_deferTeardown
     (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
-  let skipped := testItselfSkipped || classSkipped
-  if pdbEnabled && !skipped then
-    return true
   return false
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,9 +59,7 @@
 def implementation_deferTeardown
     (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
   let skipped := testItselfSkipped || classSkipped
-  if pdbEnabled && !skipped then
-    return true
-  return false
+  return pdbEnabled || !skipped
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 def implementation_deferTeardown
     (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
   let skipped := testItselfSkipped || classSkipped
-  if pdbEnabled && !skipped then
+  if pdbEnabled && skipped then
     return true
   return false
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether to specially defer a test's teardown step when the interactive
post-mortem debugger is enabled.

A unit test belongs to a containing test class. Either the individual test or the
whole containing class may be marked as "skip" (so the test will not actually
run). Independently, the interactive post-mortem debugger may be enabled for the
run.

When the debugger is enabled, the framework normally intercepts the teardown step
so it can be replayed after the debugger prompt instead of immediately. This
special interception must only happen for a test that is actually going to run:
it must NOT happen when the test is skipped — and a test counts as skipped when
EITHER the test itself is marked skip OR its containing class is marked skip.

Desired behavior: the teardown step is specially deferred exactly when the
debugger is enabled AND the test is not skipped, where "skipped" holds if the
test itself is marked skip or its containing class is marked skip.

Inputs:
  * `pdbEnabled`        — the interactive post-mortem debugger is enabled;
  * `testItselfSkipped` — the individual test is marked skip;
  * `classSkipped`      — the containing test class is marked skip.

Result:
  * `deferTeardown`     — whether the teardown step is specially deferred.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether the
-- individual test, respectively its containing class, is marked skip is an
-- UNCHANGED observation whose boolean outcome enters directly as the plain
-- `testItselfSkipped` / `classSkipped` data; whether the debugger is enabled
-- enters as the plain `pdbEnabled` datum. The only modeled operation — combining
-- those observations into the deferral decision — is modeled directly over that
-- data, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled decision is a direct
-- boolean relation over the three observed inputs.
-- pure-end

-- post-conditions-start
/-- The deferral decision is fully pinned to the inputs: the teardown step is
specially deferred exactly when the debugger is enabled AND the test is not
skipped, where a test is skipped when the test itself is marked skip or its
containing class is marked skip. The single output component is therefore left
no freedom. -/
def problem_spec_deferTeardown
    (pdbEnabled testItselfSkipped classSkipped : Bool) (result : Bool) : Prop :=
  result = (pdbEnabled && !(testItselfSkipped || classSkipped))
-- post-conditions-end

-- impl-start
def implementation_deferTeardown
    (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
  let skipped := testItselfSkipped || classSkipped
  if pdbEnabled && !skipped then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_deferTeardown :
    ∀ (pdbEnabled testItselfSkipped classSkipped : Bool),
      problem_spec_deferTeardown pdbEnabled testItselfSkipped classSkipped
        (implementation_deferTeardown pdbEnabled testItselfSkipped classSkipped) := by
  intro pdbEnabled testItselfSkipped classSkipped
  unfold problem_spec_deferTeardown implementation_deferTeardown
  cases pdbEnabled <;> cases testItselfSkipped <;> cases classSkipped <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: pytest-dev__pytest-10081/lean. Models one boolean decision in TestCaseFunction.runtest (src/_pytest/unittest.py:316-322 @ da9a2b58): whether the --pdb teardown-deferral guard is taken. Spec is FUNCTIONAL/zero-freedom over Bool^3 (8 rows): problem_spec_deferTeardown := result = (pdbEnabled && !(testItselfSkipped || classSkipped)). Any closing impl must equal the gold boolean on all 8 rows, so no closing-but-non-resolving impl can exist; step-2 resolve runs are vacuous (no attack closed).

PROTOCOL: All work same_spec(gold, atk_N, lean)=True for ALL 8 files (spec/axioms/pre/post byte-identical; only impl region edited). Verifications run concurrently (<=4 background jobs).

POSITIVE CONTROL (gold impl): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0. Axiom check (appended `#print axioms correct_deferTeardown`) -> EXIT=0, prints 'correct_deferTeardown does not depend on any axioms' (clean, no sorryAx).

ATTACKS (all same-spec; each `bash scripts/lean_verify.sh .../atk_N.lean`) — ALL FAILED to close with genuine `rfl` proof failures on discriminating rows (none had clean-axiom closing proof, so none required a materialized/resolved patch): atk_1 EXIT=1 — PREPATCH BUG: `if pdbEnabled && !testItselfSkipped` (drops classSkipped disjunct). Fails case true.false.true (the F2P scenario). prepatch_reproduced=true. atk_2 EXIT=1 — combinator swap: `skipped := testItselfSkipped && classSkipped`. Fails true.false.true and true.true.false. atk_3 EXIT=1 — boundary: `if pdbEnabled && !classSkipped` (drops testItselfSkipped disjunct). Fails true.true.false. atk_4 EXIT=1 — control-flow-effect: ignores pdbEnabled, `return !skipped`.

Fails false.false.false. atk_5 EXIT=1 — ungrounded-oracle echo (always false): `return false`. Fails true.false.false. atk_6 EXIT=1 — wrong top combinator: `return pdbEnabled || !skipped`. Fails false.false.false and true.false.true. atk_7 EXIT=1 — inverted guard: `if pdbEnabled && skipped then return true`. Fails true.false.false and true.false.true. Covers partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, and prepatch-bug classes (7 distinct wrong impls, >= the 4-6 required).

A-LEG / refinement.md AUDIT: every leg is R / I — no kind-3 (inexpressible) legs. ops 1-3 are R (Python truthiness/or/and/not <-> Lean Bool/||/&&/!); A-consumed: none; A-reference: none (no callee deeply modeled). The added `assert isinstance(self.parent, UnitTestCase)` is behavior-neutral -> I-reference, no impl op. _is_skipped is UNCHANGED by the patch and defined as bool(getattr(obj,'__unittest_skip__',False)); its boolean outcome enters directly as testItselfSkipped/classSkipped input data (correctly NOT an axiom). Correspondence to real callees (getoption('usepdb'), _is_skipped(self.obj), _is_skipped(self.parent.obj)) holds per mapping.md. No axiom/deep-model reference to audit.

CONCLUSION: verify => correct holds. No same-spec wrong impl closes with clean axioms; positive control closes clean. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether to specially defer a test's teardown step when the interactive
post-mortem debugger is enabled.

A unit test belongs to a containing test class. Either the individual test or the
whole containing class may be marked as "skip" (so the test will not actually
run). Independently, the interactive post-mortem debugger may be enabled for the
run.

When the debugger is enabled, the framework normally intercepts the teardown step
so it can be replayed after the debugger prompt instead of immediately. This
special interception must only happen for a test that is actually going to run:
it must NOT happen when the test is skipped — and a test counts as skipped when
EITHER the test itself is marked skip OR its containing class is marked skip.

Desired behavior: the teardown step is specially deferred exactly when the
debugger is enabled AND the test is not skipped, where "skipped" holds if the
test itself is marked skip or its containing class is marked skip.

Inputs:
  * `pdbEnabled`        — the interactive post-mortem debugger is enabled;
  * `testItselfSkipped` — the individual test is marked skip;
  * `classSkipped`      — the containing test class is marked skip.

Result:
  * `deferTeardown`     — whether the teardown step is specially deferred.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether the
-- individual test, respectively its containing class, is marked skip is an
-- UNCHANGED observation whose boolean outcome enters directly as the plain
-- `testItselfSkipped` / `classSkipped` data; whether the debugger is enabled
-- enters as the plain `pdbEnabled` datum. The only modeled operation — combining
-- those observations into the deferral decision — is modeled directly over that
-- data, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled decision is a direct
-- boolean relation over the three observed inputs.
-- pure-end

-- post-conditions-start
/-- The deferral decision is fully pinned to the inputs: the teardown step is
specially deferred exactly when the debugger is enabled AND the test is not
skipped, where a test is skipped when the test itself is marked skip or its
containing class is marked skip. The single output component is therefore left
no freedom. -/
def problem_spec_deferTeardown
    (pdbEnabled testItselfSkipped classSkipped : Bool) (result : Bool) : Prop :=
  result = (pdbEnabled && !(testItselfSkipped || classSkipped))
-- post-conditions-end

-- impl-start
def implementation_deferTeardown
    (pdbEnabled testItselfSkipped classSkipped : Bool) : Bool := Id.run do
  let skipped := testItselfSkipped || classSkipped
  if pdbEnabled && !skipped then
    return true
  return false
-- impl-end

-- proof-start
theorem correct_deferTeardown :
    ∀ (pdbEnabled testItselfSkipped classSkipped : Bool),
      problem_spec_deferTeardown pdbEnabled testItselfSkipped classSkipped
        (implementation_deferTeardown pdbEnabled testItselfSkipped classSkipped) := by
  intro pdbEnabled testItselfSkipped classSkipped
  unfold problem_spec_deferTeardown implementation_deferTeardown
  cases pdbEnabled <;> cases testItselfSkipped <;> cases classSkipped <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: pytest-dev__pytest-10081/lean. Models one boolean decision in TestCaseFunction.runtest (src/_pytest/unittest.py:316-322 @ da9a2b58): whether the --pdb teardown-deferral guard is taken. Spec is FUNCTIONAL/zero-freedom over Bool^3 (8 rows): problem_spec_deferTeardown := result = (pdbEnabled && !(testItselfSkipped || classSkipped)). Any closing impl must equal the gold boolean on all 8 rows, so no closing-but-non-resolving impl can exist; step-2 resolve runs are vacuous (no attack closed).

PROTOCOL: All work same_spec(gold, atk_N, lean)=True for ALL 8 files (spec/axioms/pre/post byte-identical; only impl region edited). Verifications run concurrently (<=4 background jobs).

POSITIVE CONTROL (gold impl): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT=0. Axiom check (appended `#print axioms correct_deferTeardown`) -> EXIT=0, prints 'correct_deferTeardown does not depend on any axioms' (clean, no sorryAx).

ATTACKS (all same-spec; each `bash scripts/lean_verify.sh .../atk_N.lean`) — ALL FAILED to close with genuine `rfl` proof failures on discriminating rows (none had clean-axiom closing proof, so none required a materialized/resolved patch): atk_1 EXIT=1 — PREPATCH BUG: `if pdbEnabled && !testItselfSkipped` (drops classSkipped disjunct). Fails case true.false.true (the F2P scenario). prepatch_reproduced=true. atk_2 EXIT=1 — combinator swap: `skipped := testItselfSkipped && classSkipped`. Fails true.false.true and true.true.false. atk_3 EXIT=1 — boundary: `if pdbEnabled && !classSkipped` (drops testItselfSkipped disjunct). Fails true.true.false. atk_4 EXIT=1 — control-flow-effect: ignores pdbEnabled, `return !skipped`.

Fails false.false.false. atk_5 EXIT=1 — ungrounded-oracle echo (always false): `return false`. Fails true.false.false. atk_6 EXIT=1 — wrong top combinator: `return pdbEnabled || !skipped`. Fails false.false.false and true.false.true. atk_7 EXIT=1 — inverted guard: `if pdbEnabled && skipped then return true`. Fails true.false.false and true.false.true. Covers partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, and prepatch-bug classes (7 distinct wrong impls, >= the 4-6 required).

A-LEG / refinement.md AUDIT: every leg is R / I — no kind-3 (inexpressible) legs. ops 1-3 are R (Python truthiness/or/and/not <-> Lean Bool/||/&&/!); A-consumed: none; A-reference: none (no callee deeply modeled). The added `assert isinstance(self.parent, UnitTestCase)` is behavior-neutral -> I-reference, no impl op. _is_skipped is UNCHANGED by the patch and defined as bool(getattr(obj,'__unittest_skip__',False)); its boolean outcome enters directly as testItselfSkipped/classSkipped input data (correctly NOT an axiom). Correspondence to real callees (getoption('usepdb'), _is_skipped(self.obj), _is_skipped(self.parent.obj)) holds per mapping.md. No axiom/deep-model reference to audit.

CONCLUSION: verify => correct holds. No same-spec wrong impl closes with clean axioms; positive control closes clean. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pytest-dev__pytest-10081, lean bundle. Modeled function: TestCaseFunction.runtest --pdb teardown-deferral guard (src/_pytest/unittest.py:316-322 @ base da9a2b5). Gold patch bd642fac7 changes the guard to `skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj); if getoption('usepdb') and not skipped:`. `_is_skipped(obj) = bool(getattr(obj,'__unittest_skip__',False))` — pure bool. Spec: result = (pdbEnabled && !(testItselfSkipped || classSkipped)).

Verification performed:
1. lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
2. `#print axioms correct_deferTeardown` -> 'does not depend on any axioms' (proof is genuine, no sorryAx).
3. same_spec(Solution, Solution_prepatch, lean tables) = True: spec region byte-identical across the patch, spec not weakened.
4. Exhaustive 8-row truth table: spec == real guard-taken condition on EVERY boolean assignment of (pdbEnabled, testItselfSkipped, classSkipped). Python and/or/not over the two bool-returning _is_skipped calls and usepdb truthiness map exactly to Lean &&/||/!. No diverging input exists.

The spec is neither too strong nor drifted: it pins the single output exactly to what the real post-patch code computes, and the F2P discriminating case (T,F,T) is handled correctly. The async-branch (is_async_function) path is disclosed in mapping.md as out-of-scope and is unchanged by the patch — not a drift. No callee axiom consumed (G-AX skip is justified: all-R boolean refinement). Verdict: FAITHFUL — no divergence found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Role: leakage / gold-reconstruction over the SOLVER-VISIBLE spec view only (Solution.lean spec regions; mapping.md/refinement.md are auditor artifacts, out of scope, not screened by G-LEAK).

Gold edit (patch.diff): in TestCaseFunction.runtest, add the class-skip disjunct `skipped = _is_skipped(self.obj) or _is_skipped(self.parent.obj)` plus `assert isinstance(self.parent, UnitTestCase)`, so --pdb teardown deferral is also suppressed when the CONTAINING CLASS is skipped, not only the method.

Public problem_statement already discloses the full desired behavior: title 'tearDown executed for classes marked with unittest.skip when running --pdb'; body states --pdb runs tearDown of classes decorated with unittest.skip at the class level; 'Identical to #7215, but with the skip() on the class level rather than on the function level' (both method- and class-level skip are publicly in scope); and a minimal reproducer with a class-level @unittest.skip under --pdb — i.e. the discriminating scenario itself.

Spec view (Solution.lean) content: abstract Bool inputs pdbEnabled/testItselfSkipped/classSkipped, output deferTeardown, post-condition `result = (pdbEnabled && !(testItselfSkipped || classSkipped))`, and neutral WHAT-level prose. It contains NO repo symbol (_is_skipped, self.parent.obj, usepdb, UnitTestCase), NO patched file path (src/_pytest/unittest.py), NO diff markers, and NO bug/fix narration. The classSkipped disjunct is not 'beyond' the problem statement — the statement explicitly covers the class-level case and the #7215-identical function-level case. The HOW of the edit (the `or`, the .parent.obj observable, the added assert) is not revealed in the spec view; it lives only in mapping.md/refinement.md.

Mechanical G-LEAK screen (leakage.screen, lean flavor) run independently: PASSED, zero hard failures. meta.json records G-LEAK status 'pass'; relaxed_leakage is None (no relaxation invoked). The spec restates only publicly-available information and does not enable gold reconstruction beyond the problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.