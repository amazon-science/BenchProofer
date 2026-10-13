# P2 adversarial audit — pytest-dev__pytest-7432

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None: no wrong impl closed a clean-axiom proof, so no faithful patch could be materialized/resolve-run. The spec is a total, fully-pinned Boolean equality result = skippedByMark && repSkipped && longreprIsTuple over all 7 inputs; the 4 expected-failure dispatch inputs are provably irrelevant to the output, proven by exhaustive `cases <;> rfl` over the 128-point Boolean cube. Every behavioral deviation is caught. Representative caught points: atk_3/atk_5/atk_6 fail at (skippedByMark,repSkipped,longreprIsTuple)=(T,T,F) or (F,F,T) where LHS != spec; atk_2 fails at runxfail=T (the prepatch bug shape) where correct answer must ignore runxfail.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,11 +71,6 @@
     (unexpSuccess runxfail xfailRaised notSkippedXfail
      skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
   let mut locationRewritten := false
-  -- Expected-failure dispatch: select among mutually exclusive cases (an
-  -- unexpected success on the call phase; the option that suppresses
-  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
-  -- result carrying an expected-failure mark). None of these arms touch the skip
-  -- location.
   if unexpSuccess then
     pure ()
   else if runxfail then
@@ -84,9 +79,7 @@
     pure ()
   else if notSkippedXfail then
     pure ()
-  -- Independent of the dispatch above: rewrite the reported location of a
-  -- mark-skipped, structured-triple result to point at the test item.
-  if skippedByMark && repSkipped && longreprIsTuple then
+  else if skippedByMark && repSkipped && longreprIsTuple then
     locationRewritten := true
   return locationRewritten
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,26 +69,8 @@
 -- impl-start
 def implementation_skipLocationRewrite
     (unexpSuccess runxfail xfailRaised notSkippedXfail
-     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
-  let mut locationRewritten := false
-  -- Expected-failure dispatch: select among mutually exclusive cases (an
-  -- unexpected success on the call phase; the option that suppresses
-  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
-  -- result carrying an expected-failure mark). None of these arms touch the skip
-  -- location.
-  if unexpSuccess then
-    pure ()
-  else if runxfail then
-    pure ()
-  else if xfailRaised then
-    pure ()
-  else if notSkippedXfail then
-    pure ()
-  -- Independent of the dispatch above: rewrite the reported location of a
-  -- mark-skipped, structured-triple result to point at the test item.
-  if skippedByMark && repSkipped && longreprIsTuple then
-    locationRewritten := true
-  return locationRewritten
+     skippedByMark repSkipped longreprIsTuple : Bool) : Bool :=
+  skippedByMark && repSkipped && longreprIsTuple && (!runxfail)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,26 +69,8 @@
 -- impl-start
 def implementation_skipLocationRewrite
     (unexpSuccess runxfail xfailRaised notSkippedXfail
-     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
-  let mut locationRewritten := false
-  -- Expected-failure dispatch: select among mutually exclusive cases (an
-  -- unexpected success on the call phase; the option that suppresses
-  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
-  -- result carrying an expected-failure mark). None of these arms touch the skip
-  -- location.
-  if unexpSuccess then
-    pure ()
-  else if runxfail then
-    pure ()
-  else if xfailRaised then
-    pure ()
-  else if notSkippedXfail then
-    pure ()
-  -- Independent of the dispatch above: rewrite the reported location of a
-  -- mark-skipped, structured-triple result to point at the test item.
-  if skippedByMark && repSkipped && longreprIsTuple then
-    locationRewritten := true
-  return locationRewritten
+     skippedByMark repSkipped longreprIsTuple : Bool) : Bool :=
+  skippedByMark && repSkipped
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,21 +71,8 @@
     (unexpSuccess runxfail xfailRaised notSkippedXfail
      skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
   let mut locationRewritten := false
-  -- Expected-failure dispatch: select among mutually exclusive cases (an
-  -- unexpected success on the call phase; the option that suppresses
-  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
-  -- result carrying an expected-failure mark). None of these arms touch the skip
-  -- location.
   if unexpSuccess then
-    pure ()
-  else if runxfail then
-    pure ()
-  else if xfailRaised then
-    pure ()
-  else if notSkippedXfail then
-    pure ()
-  -- Independent of the dispatch above: rewrite the reported location of a
-  -- mark-skipped, structured-triple result to point at the test item.
+    locationRewritten := true
   if skippedByMark && repSkipped && longreprIsTuple then
     locationRewritten := true
   return locationRewritten
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,26 +69,7 @@
 -- impl-start
 def implementation_skipLocationRewrite
     (unexpSuccess runxfail xfailRaised notSkippedXfail
-     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
-  let mut locationRewritten := false
-  -- Expected-failure dispatch: select among mutually exclusive cases (an
-  -- unexpected success on the call phase; the option that suppresses
-  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
-  -- result carrying an expected-failure mark). None of these arms touch the skip
-  -- location.
-  if unexpSuccess then
-    pure ()
-  else if runxfail then
-    pure ()
-  else if xfailRaised then
-    pure ()
-  else if notSkippedXfail then
-    pure ()
-  -- Independent of the dispatch above: rewrite the reported location of a
-  -- mark-skipped, structured-triple result to point at the test item.
-  if skippedByMark && repSkipped && longreprIsTuple then
-    locationRewritten := true
-  return locationRewritten
+     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := true
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,26 +69,8 @@
 -- impl-start
 def implementation_skipLocationRewrite
     (unexpSuccess runxfail xfailRaised notSkippedXfail
-     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
-  let mut locationRewritten := false
-  -- Expected-failure dispatch: select among mutually exclusive cases (an
-  -- unexpected success on the call phase; the option that suppresses
-  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
-  -- result carrying an expected-failure mark). None of these arms touch the skip
-  -- location.
-  if unexpSuccess then
-    pure ()
-  else if runxfail then
-    pure ()
-  else if xfailRaised then
-    pure ()
-  else if notSkippedXfail then
-    pure ()
-  -- Independent of the dispatch above: rewrite the reported location of a
-  -- mark-skipped, structured-triple result to point at the test item.
-  if skippedByMark && repSkipped && longreprIsTuple then
-    locationRewritten := true
-  return locationRewritten
+     skippedByMark repSkipped longreprIsTuple : Bool) : Bool :=
+  skippedByMark && repSkipped && (longreprIsTuple || repSkipped)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the source location of a test that was skipped by a skip mark.

When a test is skipped because it carries a skip mark, the location shown in the
skip summary should point at the test's own definition, rather than at the
internal framework site where the skip was raised. Concretely, the framework
rewrites the reported location of such a skip to the test item's own location.

This location rewrite is governed solely by the conditions that identify a
mark-skipped result whose reported location is a structured (filename, line,
reason) triple:

* the result was skipped by a skip mark;
* the reported outcome is "skipped";
* the reported location is the structured triple form.

Crucially, this rewrite is an independent decision: it must happen whenever those
conditions hold, regardless of how the result was handled by the separate
expected-failure dispatch (including the option that only governs expected
failures). The expected-failure dispatch — handling an unexpected success on the
call phase, the option that suppresses expected-failure treatment, a raised
expected-failure signal, or a non-skipped result carrying an expected-failure
mark — selects among mutually exclusive cases but does not gate the location
rewrite.

The decision modeled here is exactly: was the skip location rewritten to point at
the test item?
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- modeled structurally over the observable conditions of the reported result —
-- which dispatch case the expected-failure handling selects, and whether the
-- result is a mark-skipped result whose location is a structured triple — each of
-- which enters as a plain Boolean observation. The unchanged computation of the
-- rewritten location itself (deriving the item's own filename and line) is not
-- altered and is out of scope here. Hence no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- The conditions that identify a mark-skipped result whose reported location is
the structured (filename, line, reason) triple form:

* `skippedByMark` — the result was skipped by a skip mark;
* `repSkipped` — the reported outcome is "skipped";
* `longreprIsTuple` — the reported location is the structured triple.

The location rewrite is arranged exactly when all three hold. -/
def skipLocationCondition (skippedByMark repSkipped longreprIsTuple : Bool) : Bool :=
  skippedByMark && repSkipped && longreprIsTuple
-- pure-end

-- post-conditions-start
/-- The skip-location rewrite decision is exactly the mark-skipped-triple
condition, and nothing else: the rewrite happens precisely when the result is a
mark-skipped result whose reported location is the structured triple. In
particular the decision is independent of the expected-failure dispatch inputs —
including the option that only governs expected-failure handling. -/
def problem_spec_skipLocationRewrite
    (unexpSuccess runxfail xfailRaised notSkippedXfail
     skippedByMark repSkipped longreprIsTuple : Bool) (result : Bool) : Prop :=
  result = skipLocationCondition skippedByMark repSkipped longreprIsTuple
-- post-conditions-end

-- impl-start
def implementation_skipLocationRewrite
    (unexpSuccess runxfail xfailRaised notSkippedXfail
     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
  let mut locationRewritten := false
  -- Expected-failure dispatch: select among mutually exclusive cases (an
  -- unexpected success on the call phase; the option that suppresses
  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
  -- result carrying an expected-failure mark). None of these arms touch the skip
  -- location.
  if unexpSuccess then
    pure ()
  else if runxfail then
    pure ()
  else if xfailRaised then
    pure ()
  else if notSkippedXfail then
    pure ()
  -- Independent of the dispatch above: rewrite the reported location of a
  -- mark-skipped, structured-triple result to point at the test item.
  if skippedByMark && repSkipped && longreprIsTuple then
    locationRewritten := true
  return locationRewritten
-- impl-end

-- proof-start
theorem correct_skipLocationRewrite :
    ∀ (unexpSuccess runxfail xfailRaised notSkippedXfail
       skippedByMark repSkipped longreprIsTuple : Bool),
      problem_spec_skipLocationRewrite
        unexpSuccess runxfail xfailRaised notSkippedXfail
        skippedByMark repSkipped longreprIsTuple
        (implementation_skipLocationRewrite
          unexpSuccess runxfail xfailRaised notSkippedXfail
          skippedByMark repSkipped longreprIsTuple) := by
  intro unexpSuccess runxfail xfailRaised notSkippedXfail
        skippedByMark repSkipped longreprIsTuple
  unfold problem_spec_skipLocationRewrite implementation_skipLocationRewrite skipLocationCondition
  cases unexpSuccess <;> cases runxfail <;> cases xfailRaised <;> cases notSkippedXfail <;>
    cases skippedByMark <;> cases repSkipped <;> cases longreprIsTuple <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 6 distinct same-spec wrong impls, all same_spec=True (verified via swebench_unified.markers.same_spec), all FAIL lean_verify.sh (exit 1) with genuine rfl-failure counterexamples; positive control pos.lean verifies (exit 0). Kinds covered: atk_1 prepatch bug (rewrite as trailing elif, dispatch-gated); atk_2 partial-domain (&& !runxfail); atk_3 boundary (drops longreprIsTuple conjunct); atk_4 control-flow-effect (unexpSuccess arm mutates the rewrite flag); atk_5 ungrounded-oracle echo (constant true); atk_6 weakened guard (longreprIsTuple||repSkipped). Commands: `python -c 'from swebench_unified.markers import same_spec; ...'` -> True for all 6; `bash scripts/lean_verify.sh <atk>.lean` -> exit 1 for all 6, exit 0 for pos.lean.

Protocol step 2 (materialize faithful patch + run_resolve) had NO applicable candidates because zero wrong impls closed a clean-axiom proof — nothing to falsify at the harness, hence patches={}. A-leg/axiom audit: Solution.lean declares NO axiom/opaque/sorry/native_decide (grep-confirmed); refinement.md and mapping.md correctly state no consumed axiom and no A-reference callee — every leg is R or I (no kind-3). The changed behavior (skip-location rewrite made independent of the expected-failure dispatch) is deeply modeled as a pure Boolean control-flow decision, which per SPEC_GUIDE is correctly NOT axiomatized. A-leg correspondence obligation is vacuously satisfied (no deep-model reference exists that could diverge from a real callee). verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None: no wrong impl closed a clean-axiom proof, so no faithful patch could be materialized/resolve-run. The spec is a total, fully-pinned Boolean equality result = skippedByMark && repSkipped && longreprIsTuple over all 7 inputs; the 4 expected-failure dispatch inputs are provably irrelevant to the output, proven by exhaustive `cases <;> rfl` over the 128-point Boolean cube. Every behavioral deviation is caught. Representative caught points: atk_3/atk_5/atk_6 fail at (skippedByMark,repSkipped,longreprIsTuple)=(T,T,F) or (F,F,T) where LHS != spec; atk_2 fails at runxfail=T (the prepatch bug shape) where correct answer must ignore runxfail.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the source location of a test that was skipped by a skip mark.

When a test is skipped because it carries a skip mark, the location shown in the
skip summary should point at the test's own definition, rather than at the
internal framework site where the skip was raised. Concretely, the framework
rewrites the reported location of such a skip to the test item's own location.

This location rewrite is governed solely by the conditions that identify a
mark-skipped result whose reported location is a structured (filename, line,
reason) triple:

* the result was skipped by a skip mark;
* the reported outcome is "skipped";
* the reported location is the structured triple form.

Crucially, this rewrite is an independent decision: it must happen whenever those
conditions hold, regardless of how the result was handled by the separate
expected-failure dispatch (including the option that only governs expected
failures). The expected-failure dispatch — handling an unexpected success on the
call phase, the option that suppresses expected-failure treatment, a raised
expected-failure signal, or a non-skipped result carrying an expected-failure
mark — selects among mutually exclusive cases but does not gate the location
rewrite.

The decision modeled here is exactly: was the skip location rewritten to point at
the test item?
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- modeled structurally over the observable conditions of the reported result —
-- which dispatch case the expected-failure handling selects, and whether the
-- result is a mark-skipped result whose location is a structured triple — each of
-- which enters as a plain Boolean observation. The unchanged computation of the
-- rewritten location itself (deriving the item's own filename and line) is not
-- altered and is out of scope here. Hence no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- The conditions that identify a mark-skipped result whose reported location is
the structured (filename, line, reason) triple form:

* `skippedByMark` — the result was skipped by a skip mark;
* `repSkipped` — the reported outcome is "skipped";
* `longreprIsTuple` — the reported location is the structured triple.

The location rewrite is arranged exactly when all three hold. -/
def skipLocationCondition (skippedByMark repSkipped longreprIsTuple : Bool) : Bool :=
  skippedByMark && repSkipped && longreprIsTuple
-- pure-end

-- post-conditions-start
/-- The skip-location rewrite decision is exactly the mark-skipped-triple
condition, and nothing else: the rewrite happens precisely when the result is a
mark-skipped result whose reported location is the structured triple. In
particular the decision is independent of the expected-failure dispatch inputs —
including the option that only governs expected-failure handling. -/
def problem_spec_skipLocationRewrite
    (unexpSuccess runxfail xfailRaised notSkippedXfail
     skippedByMark repSkipped longreprIsTuple : Bool) (result : Bool) : Prop :=
  result = skipLocationCondition skippedByMark repSkipped longreprIsTuple
-- post-conditions-end

-- impl-start
def implementation_skipLocationRewrite
    (unexpSuccess runxfail xfailRaised notSkippedXfail
     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
  let mut locationRewritten := false
  -- Expected-failure dispatch: select among mutually exclusive cases (an
  -- unexpected success on the call phase; the option that suppresses
  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
  -- result carrying an expected-failure mark). None of these arms touch the skip
  -- location.
  if unexpSuccess then
    pure ()
  else if runxfail then
    pure ()
  else if xfailRaised then
    pure ()
  else if notSkippedXfail then
    pure ()
  -- Independent of the dispatch above: rewrite the reported location of a
  -- mark-skipped, structured-triple result to point at the test item.
  if skippedByMark && repSkipped && longreprIsTuple then
    locationRewritten := true
  return locationRewritten
-- impl-end

-- proof-start
theorem correct_skipLocationRewrite :
    ∀ (unexpSuccess runxfail xfailRaised notSkippedXfail
       skippedByMark repSkipped longreprIsTuple : Bool),
      problem_spec_skipLocationRewrite
        unexpSuccess runxfail xfailRaised notSkippedXfail
        skippedByMark repSkipped longreprIsTuple
        (implementation_skipLocationRewrite
          unexpSuccess runxfail xfailRaised notSkippedXfail
          skippedByMark repSkipped longreprIsTuple) := by
  intro unexpSuccess runxfail xfailRaised notSkippedXfail
        skippedByMark repSkipped longreprIsTuple
  unfold problem_spec_skipLocationRewrite implementation_skipLocationRewrite skipLocationCondition
  cases unexpSuccess <;> cases runxfail <;> cases xfailRaised <;> cases notSkippedXfail <;>
    cases skippedByMark <;> cases repSkipped <;> cases longreprIsTuple <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 6 distinct same-spec wrong impls, all same_spec=True (verified via swebench_unified.markers.same_spec), all FAIL lean_verify.sh (exit 1) with genuine rfl-failure counterexamples; positive control pos.lean verifies (exit 0). Kinds covered: atk_1 prepatch bug (rewrite as trailing elif, dispatch-gated); atk_2 partial-domain (&& !runxfail); atk_3 boundary (drops longreprIsTuple conjunct); atk_4 control-flow-effect (unexpSuccess arm mutates the rewrite flag); atk_5 ungrounded-oracle echo (constant true); atk_6 weakened guard (longreprIsTuple||repSkipped). Commands: `python -c 'from swebench_unified.markers import same_spec; ...'` -> True for all 6; `bash scripts/lean_verify.sh <atk>.lean` -> exit 1 for all 6, exit 0 for pos.lean.

Protocol step 2 (materialize faithful patch + run_resolve) had NO applicable candidates because zero wrong impls closed a clean-axiom proof — nothing to falsify at the harness, hence patches={}. A-leg/axiom audit: Solution.lean declares NO axiom/opaque/sorry/native_decide (grep-confirmed); refinement.md and mapping.md correctly state no consumed axiom and no A-reference callee — every leg is R or I (no kind-3). The changed behavior (skip-location rewrite made independent of the expected-failure dispatch) is deeply modeled as a pure Boolean control-flow decision, which per SPEC_GUIDE is correctly NOT axiomatized. A-leg correspondence obligation is vacuously satisfied (no deep-model reference exists that could diverge from a real callee). verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness break check — NO defect found; spec is faithful to the real post-patch callee.

Bundle: pytest-dev__pytest-7432 (lean). Models the skip-location rewrite decision in pytest_runtest_makereport (src/_pytest/skipping.py) after the gold patch turns the final `elif (...)` into a standalone `if (...)`.

Verification performed:
1. lean_verify.sh on Solution.lean → exit 0 (compiles, no sorry). Warnings are only unused-variable lints (unexpSuccess/runxfail/xfailRaised/notSkippedXfail), which is EXPECTED: the modeled post-patch decision is independent of those dispatch inputs.
2. #print axioms correct_skipLocationRewrite → 'does not depend on any axioms' — proof is real, no sorryAx.
3. same_spec(Solution, Solution_prepatch, lean tables) → True. Spec regions (axioms/pure/post-conditions) byte-identical; only impl+proof differ (prepatch carries the buggy trailing-elif skeleton).

Faithfulness argument:
- Spec: problem_spec = (result = skippedByMark && repSkipped && longreprIsTuple).
- Real post-patch code: the rewrite fires exactly when `item._store.get(skipped_by_mark_key, True) and rep.skipped and type(rep.longrepr) is tuple` — a STANDALONE `if`, no longer gated by the mutually-exclusive expected-failure dispatch chain (unexpectedsuccess / runxfail / xfailRaised / notSkippedXfail). Confirmed by reading skipping.py:260-306 at base_commit e6e300e729 (pre-patch shows `elif`), and the gold diff (elif→if).
- The model binds the three rewrite conditions to plain Booleans and correctly drops the dispatch inputs from the decision. For every observable input tuple actually reached at the rewrite site, the modeled function equals the real callee's rewrite decision.
- The only 'suspicious' region — combining unexpSuccess=true with repSkipped/longreprIsTuple=true — is not a real divergence: those tuples are physically unreachable (the unexpSuccess arm sets rep.outcome='failed' and a string longrepr), and even so the spec agrees with the true post-patch behavior (the standalone `if` would still evaluate the conjunction on the actual rep state). No reachable input makes the modeled function disagree with the real post-patch callee.

The spec is neither too strong nor drifted; it captures precisely the F2P-discriminating behavior (runxfail=true + mark-skipped-triple → rewrite must fire). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no diff markers, no gold-patch line reproduced, no patched file/module path, no patched symbol (pytest_runtest_makereport) in spec view, no narration terms. Spec view (docstring + skipLocationCondition + problem_spec_skipLocationRewrite; impl and proof elided) states the target contract: the skip-location rewrite is an INDEPENDENT decision that must fire whenever the mark-skipped/skipped/structured-triple conditions hold, regardless of the expected-failure dispatch 'including the option that only governs expected failures.' This independence is a faithful restatement of the PUBLIC problem_statement, which already says '--runxfail is only about xfail and should not affect this at all' and points the solver at src/_pytest/skipping.py's pytest_runtest_makereport hook (that hint line is part of problem_statement, not hints_text). The spec describes the desired observable behavior, not the code-level edit (elif -> if): the mechanism is nowhere in the view. Nothing beyond the public problem_statement is disclosed. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).