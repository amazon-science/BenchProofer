# P2 adversarial audit — sympy__sympy-19495

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The strongest surviving attack family is the RESULT-DISCARDED EXTRA CALL class (atk_3/4/5/6/8): impls that return the gold value but additionally invoke the partial ConditionSet constructor at a well-sorted argument triple, which a WP calculus cannot observe. All 5 verify under lean_verify.sh AND all 5 faithful patches RESOLVE under the official harness, so on this instance the class is closed rather than exploitable. The reason it is closed is measured, not argued: I exhaustively enumerated the writable extra-call shapes the sorts admit (Binder slot is inhabited only by boundSym; Cond by condition/newCond/cond2; SetObj by baseSet/newBase/base2; Obj by binderObj/oldObj/newObj) = 9 mkSet + 9 mkSetOnValue shapes, spliced each into the gold patch as Python, and ran the F2P+P2P file on all 18 -- 18/18 pass (screen.py). Depth-3 re-substitution and all-18-at-once also pass (screen2.py), so BuildsDefined's coverage claim is not merely as-audited-to-depth-2 but holds strictly beyond it.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,11 +234,8 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
-    let newCond := substCond condition old new
     let newBase := substSet baseSet old new
-    return mkSet boundSym newCond newBase
+    return mkSetOnValue (newObj new) newBase
     -- impl-end
 end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,11 +234,8 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
-    let newCond := substCond condition old new
     let newBase := substSet baseSet old new
-    return mkSet boundSym newCond newBase
+    return mkSet boundSym condition newBase
     -- impl-end
 end
 
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,10 +234,9 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
     let newCond := substCond condition old new
     let newBase := substSet baseSet old new
+    let _probe := mkSet boundSym condition (substSet newBase old new)
     return mkSet boundSym newCond newBase
     -- impl-end
 end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,10 +234,9 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
     let newCond := substCond condition old new
     let newBase := substSet baseSet old new
+    let _probe := mkSetOnValue (newObj new) (substSet newBase old new)
     return mkSet boundSym newCond newBase
     -- impl-end
 end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,10 +234,23 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
+    -- DEEP-NESTING attack: substitution re-applied to depth 3 and set-building
+    -- invocations at every depth, i.e. STRICTLY BEYOND the "stored / substituted /
+    -- twice-substituted" enumeration refinement.md B/E claims BuildsDefined covers.
+    -- The returned value is the gold one, so the ensures is satisfied; if any of
+    -- these discarded rebuilds is refused by the real constructor the patch raises.
     let newCond := substCond condition old new
     let newBase := substSet baseSet old new
+    let c2 := substCond newCond old new
+    let b2 := substSet newBase old new
+    let c3 := substCond c2 old new
+    let b3 := substSet b2 old new
+    let _p1 := mkSet boundSym c3 b3
+    let _p2 := mkSet boundSym c2 b3
+    let _p3 := mkSet boundSym c3 b2
+    let _p4 := mkSetOnValue (newObj new) b3
+    let _p5 := mkSetOnValue (oldObj old) b3
+    let _p6 := mkSetOnValue (binderObj boundSym) b3
     return mkSet boundSym newCond newBase
     -- impl-end
 end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,10 +234,9 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
     let newCond := substCond condition old new
     let newBase := substSet baseSet old new
+    let _probe := mkSetOnValue (oldObj old) baseSet
     return mkSet boundSym newCond newBase
     -- impl-end
 end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,11 +234,8 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
     let newCond := substCond condition old new
-    let newBase := substSet baseSet old new
-    return mkSet boundSym newCond newBase
+    return mkSet boundSym newCond baseSet
     -- impl-end
 end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -234,10 +234,15 @@
   ensures out = evalSubsSpec boundSym condition baseSet old new
   do
     -- impl-start
-    -- Push the substitution through the condition and the base set, then rebuild
-    -- the set from those components, bound by the set's own original binder.
     let newCond := substCond condition old new
     let newBase := substSet baseSet old new
+    let cond2 := substCond newCond old new
+    let base2 := substSet newBase old new
+    let _p1 := mkSet boundSym cond2 base2
+    let _p2 := mkSetOnValue (binderObj boundSym) baseSet
+    let _p3 := mkSetOnValue (newObj new) newBase
+    let _p4 := mkSetOnValue (oldObj old) base2
+    let _p5 := mkSet boundSym condition baseSet
     return mkSet boundSym newCond newBase
     -- impl-end
 end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Base_commit worktrees (25fbcce5b1a4c7e3956e6062930f4a44ce95a632) at wt/ (clean, used for git apply --check) and wt_gold/ (gold+test_patch, used for local screening). Every attack was produced by copying velvet/Solution.lean and editing ONLY the impl region; same_spec == True for all 8 (verified via swebench_unified.markers.same_spec with backend 'velvet').

**POSITIVE CONTROL.** pos_control.lean (byte-identical copy of Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT 0, no sorry/admit.

### ATTACK MATRIX (cmd for each: `bash scripts/lean_verify.sh <path>`; run 4-way concurrently as background jobs):
atk_1 PREPATCH BUG -- value-keyed rebuild on the replacement, condition dropped (verbatim deleted collapse-path code) -> EXIT 1 REJECTED. Unsolved goal is exactly the binder discrepancy `mkSetOnValue (newObj new) (substSet baseSet old new) = mkSet boundSym (substCond condition old new) (substSet baseSet old new)`, matching refinement.md §A.

Elaborates cleanly, so the rejection is BEHAVIOURAL not sortal. prepatch_reproduced=true. atk_2 UNGROUNDED/BOUNDARY -- raw unsubstituted condition in the rebuild -> EXIT 1 REJECTED. atk_7 PARTIAL-DOMAIN -- base set not substituted -> EXIT 1 REJECTED. atk_3 CONTROL-FLOW-EFFECT -- gold value + discarded `mkSet boundSym condition (substSet newBase old new)` (raw cond over twice-substituted base) -> EXIT 0 VERIFIES. atk_4 CONTROL-FLOW-EFFECT -- gold value + discarded `mkSetOnValue (newObj new) base2` -> EXIT 0 VERIFIES. atk_5 DEEP-NESTING (beyond audited enumeration) -- substitution re-applied to depth 3 (c3/b3) with 6 discarded rebuilds at every depth -> EXIT 0 VERIFIES. atk_6 BOUNDARY -- discarded `mkSetOnValue (oldObj old) baseSet` (value-keyed on the REPLACED object over the RAW base; a shape the deleted code never used) -> EXIT 0 VERIFIES. atk_8 COMBINED STRESS -- gold value + all five extra-call families at once -> EXIT 0 VERIFIES.

MANDATORY RESOLVE RUNS (cmd: `python resolve_one.py <name>` calling swebench_unified.harness.run_resolve('sympy__sympy-19495', <diff>, timeout=1800, retries=1); atk_3..6 run 4-way concurrently, atk_8 separately). Every verifying attack's faithful refined patch was materialized (gold patch applied verbatim, INCLUDING the docstring hunk, then the branch body replaced by the transliterated impl region) and checked with `git apply --check` in the clean base_commit worktree -- all 5 rc=0.
  atk_3.diff -> resolved=True   atk_4.diff -> resolved=True   atk_5.diff -> resolved=True
  atk_6.diff -> resolved=True   atk_8.diff -> resolved=True
No verifying wrong impl's patch failed to resolve => no verify-but-not-correct witness => not BROKEN.

HARNESS NEGATIVE CONTROL (this is what makes the five True's meaningful). atk_1.diff -- the faithful patch for the REJECTED prepatch impl -- applies (git apply --check rc=0) and was run through the SAME harness path: resolved=False, note 'patch did not resolve in 2 attempts (consistent -- not flaky)'. So the oracle discriminates on this instance and the resolve=True results are not a rubber stamp.

**EXHAUSTIVE PYTHON SCREEN OF THE ONE UNSORTED LAYER.** refinement.md §E's third step (BuildsDefined carries the constructor's non-sortal partiality for discarded rebuilds) is the only leg the sorts cannot enforce, so I measured it directly instead of trusting the two spot-checks the doc reports. screen.py enumerates ALL 18 writable extra-call shapes (9 mkSet x {C0,C1,C2}x{B0,B1,B2}, 9 mkSetOnValue x {sym,old,new}x{B0,B1,B2}), splices each as `_probe = ...` into the gold patch, and runs sympy/sets/tests/test_conditionset.py (F2P test_subs_CondSet + all 8 P2P): gold control 9 passed/1 xfailed, and 18/18 shapes 9 passed/1 xfailed. screen2.py extends to depth-3 re-substitution with rebuilds at every depth and to all-18-in-one-body: both pass. So BuildsDefined is not over-claiming for anything an impl can write.

A-LEG / CORRESPONDENCE AUDIT (the assigned focus). Legs: A1=R, A2=A-reference+I, A3=A-reference+I, A4=A-reference+I, A5=A-reference. No leg is kind-3; §D's claim holds -- the operation that actually changed (binder choice in the rebuild) is modeled DEEPLY as `mkSet boundSym ...` inside evalSubsSpec, not hidden behind an axiom about the function under change. §B's 'no consumed axioms' is correct by inspection: substCond/substSet/mkSet/mkSetOnValue are bare `axiom`s with no ensures, and CondSubDefined/BaseSubDefined/BuildsDefined are opaque Props used only as `require`s (the proof is `loom_solve; simp_all [evalSubsSpec]`).

Callee correspondence checked against the real source in wt/sympy/sets/conditionset.py at base_commit: substCond/substSet <-> Basic.subs at the condition and base_set slots (lines 245-246 prepatch); mkSet <-> self.func(self.sym, cond, base) (line 249); mkSetOnValue <-> ConditionSet(new, Contains(new, base), base) (line 248, the line the patch deletes) -- A5's justification for keeping the unused second shape in the axiom surface is sound, since Solution_prepatch.lean needs it to transcribe the deleted code, and I confirmed the prepatch file does exactly that. The constructor's element-testing refusal site the third `require` is derived from is real: conditionset.py:151-152 `sifted = sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))`.

The `isinstance(self.sym, Expr)` guard (line 209) and the Tuple-binder early return are genuinely outside the modeled branch, matching A1. SORTAL UNTYPEABILITY VERIFIED, NOT ASSUMED. refinement.md §E claims a family of wrong extra calls is a Lean TYPE error rather than merely unproven. I encoded each and confirmed: sortal_2.lean (reverse-direction `substCond condition new old`), sortal_3.lean (`substSet baseSet (binderObj boundSym) new`, keyed on the set's own binder), sortal_4.lean (`substSet (mkSet boundSym condition baseSet) old new`, MANUFACTURED receiver, the SetObj/BuiltSet split) all fail with `error: Application type mismatch` -- true type errors, so unwritable rather than unproven. sortal_1.lean (well-sorted baseline) EXIT 0, confirming the harness was not rejecting everything.

CAVEAT (scope, not a defect). 'verify => resolves' is established here for the extra-call class by exhaustive enumeration over the shapes THIS model can name plus the real F2P/P2P suite, i.e. relative to the test suite's inputs. A discarded call refused only on an input no test exercises would be invisible to G-RESOLVE by construction -- that is a property of the correctness oracle, not of this spec, and the 41904-invocation coverage measurement in axiom_check.py obligation 18 is the intended mitigation (G-AX's leg, not mine).

**VERDICT SOUND:** 8 same-spec attacks encoded and verified (3 correctly rejected including the prepatch bug, 5 verifying), all 5 verifying attacks' faithful patches materialized, applied and RESOLVED under the official harness, harness discrimination proven by a non-resolving negative control, and the A legs' correspondence and untypeability claims independently confirmed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The strongest surviving attack family is the RESULT-DISCARDED EXTRA CALL class (atk_3/4/5/6/8): impls that return the gold value but additionally invoke the partial ConditionSet constructor at a well-sorted argument triple, which a WP calculus cannot observe. All 5 verify under lean_verify.sh AND all 5 faithful patches RESOLVE under the official harness, so on this instance the class is closed rather than exploitable. The reason it is closed is measured, not argued: I exhaustively enumerated the writable extra-call shapes the sorts admit (Binder slot is inhabited only by boundSym; Cond by condition/newCond/cond2; SetObj by baseSet/newBase/base2; Obj by binderObj/oldObj/newObj) = 9 mkSet + 9 mkSetOnValue shapes, spliced each into the gold patch as Python, and ran the F2P+P2P file on all 18 -- 18/18 pass (screen.py). Depth-3 re-substitution and all-18-at-once also pass (screen2.py), so BuildsDefined's coverage claim is not merely as-audited-to-depth-2 but holds strictly beyond it.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Base_commit worktrees (25fbcce5b1a4c7e3956e6062930f4a44ce95a632) at wt/ (clean, used for git apply --check) and wt_gold/ (gold+test_patch, used for local screening). Every attack was produced by copying velvet/Solution.lean and editing ONLY the impl region; same_spec == True for all 8 (verified via swebench_unified.markers.same_spec with backend 'velvet').

**POSITIVE CONTROL.** pos_control.lean (byte-identical copy of Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT 0, no sorry/admit.

### ATTACK MATRIX (cmd for each: `bash scripts/lean_verify.sh <path>`; run 4-way concurrently as background jobs):
atk_1 PREPATCH BUG -- value-keyed rebuild on the replacement, condition dropped (verbatim deleted collapse-path code) -> EXIT 1 REJECTED. Unsolved goal is exactly the binder discrepancy `mkSetOnValue (newObj new) (substSet baseSet old new) = mkSet boundSym (substCond condition old new) (substSet baseSet old new)`, matching refinement.md §A.

Elaborates cleanly, so the rejection is BEHAVIOURAL not sortal. prepatch_reproduced=true. atk_2 UNGROUNDED/BOUNDARY -- raw unsubstituted condition in the rebuild -> EXIT 1 REJECTED. atk_7 PARTIAL-DOMAIN -- base set not substituted -> EXIT 1 REJECTED. atk_3 CONTROL-FLOW-EFFECT -- gold value + discarded `mkSet boundSym condition (substSet newBase old new)` (raw cond over twice-substituted base) -> EXIT 0 VERIFIES. atk_4 CONTROL-FLOW-EFFECT -- gold value + discarded `mkSetOnValue (newObj new) base2` -> EXIT 0 VERIFIES. atk_5 DEEP-NESTING (beyond audited enumeration) -- substitution re-applied to depth 3 (c3/b3) with 6 discarded rebuilds at every depth -> EXIT 0 VERIFIES. atk_6 BOUNDARY -- discarded `mkSetOnValue (oldObj old) baseSet` (value-keyed on the REPLACED object over the RAW base; a shape the deleted code never used) -> EXIT 0 VERIFIES. atk_8 COMBINED STRESS -- gold value + all five extra-call families at once -> EXIT 0 VERIFIES.

MANDATORY RESOLVE RUNS (cmd: `python resolve_one.py <name>` calling swebench_unified.harness.run_resolve('sympy__sympy-19495', <diff>, timeout=1800, retries=1); atk_3..6 run 4-way concurrently, atk_8 separately). Every verifying attack's faithful refined patch was materialized (gold patch applied verbatim, INCLUDING the docstring hunk, then the branch body replaced by the transliterated impl region) and checked with `git apply --check` in the clean base_commit worktree -- all 5 rc=0.
  atk_3.diff -> resolved=True   atk_4.diff -> resolved=True   atk_5.diff -> resolved=True
  atk_6.diff -> resolved=True   atk_8.diff -> resolved=True
No verifying wrong impl's patch failed to resolve => no verify-but-not-correct witness => not BROKEN.

HARNESS NEGATIVE CONTROL (this is what makes the five True's meaningful). atk_1.diff -- the faithful patch for the REJECTED prepatch impl -- applies (git apply --check rc=0) and was run through the SAME harness path: resolved=False, note 'patch did not resolve in 2 attempts (consistent -- not flaky)'. So the oracle discriminates on this instance and the resolve=True results are not a rubber stamp.

**EXHAUSTIVE PYTHON SCREEN OF THE ONE UNSORTED LAYER.** refinement.md §E's third step (BuildsDefined carries the constructor's non-sortal partiality for discarded rebuilds) is the only leg the sorts cannot enforce, so I measured it directly instead of trusting the two spot-checks the doc reports. screen.py enumerates ALL 18 writable extra-call shapes (9 mkSet x {C0,C1,C2}x{B0,B1,B2}, 9 mkSetOnValue x {sym,old,new}x{B0,B1,B2}), splices each as `_probe = ...` into the gold patch, and runs sympy/sets/tests/test_conditionset.py (F2P test_subs_CondSet + all 8 P2P): gold control 9 passed/1 xfailed, and 18/18 shapes 9 passed/1 xfailed. screen2.py extends to depth-3 re-substitution with rebuilds at every depth and to all-18-in-one-body: both pass. So BuildsDefined is not over-claiming for anything an impl can write.

A-LEG / CORRESPONDENCE AUDIT (the assigned focus). Legs: A1=R, A2=A-reference+I, A3=A-reference+I, A4=A-reference+I, A5=A-reference. No leg is kind-3; §D's claim holds -- the operation that actually changed (binder choice in the rebuild) is modeled DEEPLY as `mkSet boundSym ...` inside evalSubsSpec, not hidden behind an axiom about the function under change. §B's 'no consumed axioms' is correct by inspection: substCond/substSet/mkSet/mkSetOnValue are bare `axiom`s with no ensures, and CondSubDefined/BaseSubDefined/BuildsDefined are opaque Props used only as `require`s (the proof is `loom_solve; simp_all [evalSubsSpec]`).

Callee correspondence checked against the real source in wt/sympy/sets/conditionset.py at base_commit: substCond/substSet <-> Basic.subs at the condition and base_set slots (lines 245-246 prepatch); mkSet <-> self.func(self.sym, cond, base) (line 249); mkSetOnValue <-> ConditionSet(new, Contains(new, base), base) (line 248, the line the patch deletes) -- A5's justification for keeping the unused second shape in the axiom surface is sound, since Solution_prepatch.lean needs it to transcribe the deleted code, and I confirmed the prepatch file does exactly that. The constructor's element-testing refusal site the third `require` is derived from is real: conditionset.py:151-152 `sifted = sift(base_set, lambda _: fuzzy_bool(condition.subs(sym, _)))`.

The `isinstance(self.sym, Expr)` guard (line 209) and the Tuple-binder early return are genuinely outside the modeled branch, matching A1. SORTAL UNTYPEABILITY VERIFIED, NOT ASSUMED. refinement.md §E claims a family of wrong extra calls is a Lean TYPE error rather than merely unproven. I encoded each and confirmed: sortal_2.lean (reverse-direction `substCond condition new old`), sortal_3.lean (`substSet baseSet (binderObj boundSym) new`, keyed on the set's own binder), sortal_4.lean (`substSet (mkSet boundSym condition baseSet) old new`, MANUFACTURED receiver, the SetObj/BuiltSet split) all fail with `error: Application type mismatch` -- true type errors, so unwritable rather than unproven. sortal_1.lean (well-sorted baseline) EXIT 0, confirming the harness was not rejecting everything.

CAVEAT (scope, not a defect). 'verify => resolves' is established here for the extra-call class by exhaustive enumeration over the shapes THIS model can name plus the real F2P/P2P suite, i.e. relative to the test suite's inputs. A discarded call refused only on an input no test exercises would be invisible to G-RESOLVE by construction -- that is a property of the correctness oracle, not of this spec, and the 41904-invocation coverage measurement in axiom_check.py obligation 18 is the intended mitigation (G-AX's leg, not mine).

**VERDICT SOUND:** 8 same-spec attacks encoded and verified (3 correctly rejected including the prepatch bug, 5 verifying), all 5 verifying attacks' faithful patches materialized, applied and RESOLVED under the official harness, harness discrimination proven by a non-resolving negative control, and the A legs' correspondence and untypeability claims independently confirmed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**FAITHFULNESS-BREAK ATTACK:** no divergence found. Spec models ConditionSet.`_eval_subs` (sympy/sets/conditionset.py) restricted to the `isinstance(self.sym, Expr) and old != sym` branch with a Symbol binder. Reference = base_commit 25fbcce5b1a4c7e3956e6062930f4a44ce95a632 WITH patch.diff applied (per instructions); base used only for the unchanged callees the axioms model.

### Setup
- Two clean git worktrees off sympy_sympy.git at base_commit: one pristine (models base-only callees), one with patch.diff applied via `git apply` (verified the post-patch `else:` block returns `self.func(self.sym, cond, base)` uniformly).
- Spec region byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) -> True. The frozen region is the 4 requires + `ensures out = evalSubsSpec boundSym condition baseSet old new`.

DIFFERENTIAL EVIDENCE (real patched `_eval_subs` vs. the modeled function `mkSet boundSym (substCond condition old new) (substSet baseSet old new)`)
On every input satisfying all four requires, I compared the real callee's return against the spec's rebuild `ConditionSet(csym, ccond.subs(old,new), cbase.subs(old,new))`. Requires were enforced faithfully, including BuildsDefined bundled over EVERY nameable set-building invocation (both shapes: binder-keyed and value-keyed `ConditionSet(o, Contains(o,b), b)`, over the stored condition/base and their substituted images to depth 2, keyed on the binder / oldObj / newObj), matching mapping.md 3.5's enumeration.
- Probe 1 (curated boundary receivers): 1,524 admitted inputs, 0 violations.
- Probe 2 (broad fuzz, seed 19495, 1,401 receivers): 61,561 admitted inputs, 495 on the discriminating collapse path (cond.subs -> S.true), 0 violations.
- Probe 3 (nested-ConditionSet-base receivers, aimed at the ctor's fresh-Dummy arm): 208,464 admitted inputs, 0 violations, 0 nondeterminism.
- Probe 4 (final wide fuzz: 40 conditions x 34 bases x 18 binders, 40-element `new` pool incl. I/nan/zoo/oo/Float/Function apps, 2,601 receivers): 168,394 admitted inputs, 995 collapse-path, 0 hard violations, 0 cases differing under `==`, and 0 REAL_RAISES.
Total ~440K admitted inputs, zero disagreement.

TOO-STRONG (over-restrictive) CHECK -- the actual attack surface, and it holds up
- REAL_RAISES = 0 across all probes: on every input the three definedness preconditions ADMIT, the real `_eval_subs` returns normally. So the preconditions are sufficient, not merely convenient, and they do not hide a real-behavior case where the spec promises a result the repo lacks. Conversely they are non-vacuous (~440K inputs admitted), so the contract is not narrowed to nothing.
- Excluded sub-domains are all genuinely UNCHANGED-by-patch arms, not spec drift: (a) the Tuple/compound binder early return (`return self`, conditionset.py:209-212) is excluded by the `Binder` sort; (b) the `old == self.sym` dummy-renaming arm (lines 213-241) is excluded by `require oldObj old != binderObj boundSym`, matching the real guard `old == sym` on `self.args[0]` (SymPy `==` is structural, so it maps onto Lean `!=` exactly); (c) the Expr-but-not-Symbol binder sub-domain is where the real ctor raises ValueError('non-symbol dummy not recognized in condition'). None of these carries patched behavior.

### ABSTRACTION PROBES THAT COULD HAVE BROKEN FAITHFULNESS (all cleared)
- `mkSet` must be a FUNCTION of (binder, condition, base). I found `ConditionSet.__new__` IS nondeterministic under `==` on its fresh-Dummy arm (conditionset.py:171-176): four identical calls with a ConditionSet base gave pairwise `==` [True,False,False,False] while `dummy_eq` was True for all. I then confirmed this cannot break the spec inside the modeled branch: no receiver's STORED base_set is ever a ConditionSet (`__new__` always flattens a ConditionSet base, so nesting never survives construction -- measured 0 of 20 candidate receivers). Where I forced the rebuild's base to become a ConditionSet via `Union(FiniteSet(y), inner_cs).subs(...)`, 560 rebuilds gave only 2 `==`-differences and both were `dummy_eq`-True, i.e. the same set up to bound-symbol naming -- exactly the equality mapping.md 2 declares for the bijection. 233 rebuilds landing on a fresh-Dummy binder all matched real == spec.
- `ConditionSet` has no subclasses (`__subclasses__() == []`), so `self.func` is always `ConditionSet` and the mkSet binding is not under-specified by dispatch.

DISCRIMINATION / NON-VACUITY (spec is not trivially true)
- scripts/lean_verify.sh Solution.lean -> EXIT 0 (elaborates, no sorry/error).
- scripts/lean_verify.sh Solution_prepatch.lean -> EXIT 1, `247:27: error: unsolved goals`. The pre-patch impl `mkSetOnValue (newObj new) newBase` (the deleted `ConditionSet(new, Contains(new, base), base)` collapse path) elaborates fine and is rejected by the `ensures` alone -- so the postcondition, not typing, decides the binder question the instance is about (mapping.md 3.3's 'what the sorts must NOT decide').
- Patch resolves on the real repo: with test_patch applied, sympy/sets/tests/test_conditionset.py = 9 passed, 1 xfailed (F2P test_subs_CondSet passes). Without the gold patch that same test FAILS, confirming the modeled delta is the real behavioral change and that I compared against the correct (post-patch) reference.

**CONCLUSION:** the modeled function agrees with the real patched callee on every input the spec admits, the preconditions are both sufficient (0 real refusals) and non-vacuous, the excluded arms are patch-unchanged, and the only real abstraction wrinkle (ctor Dummy nondeterminism) is unreachable in the modeled branch and absorbed by the declared dummy_eq equality. No diverging input exists to cite; I could not construct one. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MY OWN MEASUREMENT ON CURRENT BYTES; prior G-PANEL-3 notes in verdict.md NOT inherited.

**NO RELAXATION CLAIM:** `'relaxed_leakage' in json.load(open('meta.json'))` = False; no RELAXED_LEAKAGE.md anywhere under the instance dir (`ls` of instance root = ears/ instance.json lean/ nagini/ patch.diff velvet/). The only 'relaxed_leakage' string hits in the bundle are inside prior audit prose in meta.json asserting the same absence. So this is judged as an ordinary (non-relaxed) leakage review.

FRESHNESS / SPEC REGION: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, backends.get_backend('velvet')) = True. My spec_view sha256 = 07196bc2, which matches meta.json region_hashes.spec_view (07196bc2111c...). NOTE: the pre-existing G-PANEL-3 notes in verdict.md (lines 592-644) claim 'current bytes hash to 9e7ed1a1 / c731ed0f' -- that does NOT match the current spec_view (07196bc2) or the current ledger, so those notes describe superseded bytes (cf. a prose edit voids retained attacks). Everything here is re-derived.

GOLD EDIT (patch.diff, sympy/sets/conditionset.py `_eval_subs`): removes the special case `cond = ...; base = ...; if cond is S.true: return ConditionSet(new, Contains(new, base), base); return self.func(self.sym, cond, base)` and replaces it with an unconditional `self.func(self.sym, cond, base)` (plus pure-docstring churn: a 'Notes =====' heading removal and a 'and appears'->'appears' typo fix, neither semantic).

DECISIVE LOAD-BEARING TEST (this is the measurement, not a re-assertion): I mechanically stripped EVERY /- ... -/ block comment and every -- line comment except the region markers from both Solution.lean and Solution_prepatch.lean (93-line bare files; verified by grep that no narration survives -- only identifier names). Then `scripts/lean_verify.sh` on each:
  - atk3_gold_bare.lean  -> VERIFIES (clean, exit 0)
  - atk3_pre_bare.lean   -> REFUTED: 'unsolved goals ... |- mkSetOnValue (newObj new) (substSet baseSet old new) = mkSet boundSym (substCond condition old new) (substSet baseSet old new)'
So NO prose clause anywhere in the spec view is load-bearing for the gold/pre-patch discrimination -- the `ensures out = evalSubsSpec ...` equation plus the axiom signatures do all the work. Prose here is commentary, not the discriminator. (Unstripped controls also run: Solution.lean verifies; Solution_prepatch.lean refuted with the identical goal.)

PER-CANDIDATE SCAN of the spec view (242 lines), strongest candidates and why each stays inside problem_statement:
1. `axiom mkSetOnValue : Obj -> SetObj -> BuiltSet` (line 150) + its docstring 'the object is bound over the membership test of that very object in the base set -- the shape the problem statement's own transcript displays for Out[75]', with ONE set argument reused as both tested and bound-over set. This is the value-keyed shape `ConditionSet(new, Contains(new, base), base)` that the gold patch deletes. But it is read straight off the PUBLIC transcript: Out[75] literally prints `{1/3 | 1/3 in {2*pi*n + asin(1/3) | n in Z} AND (1/3 in {2*pi*n + asin(1/3) | n in Z})}` -- same base set twice, keyed on the substituted value 1/3, original condition absent. The docstring cites that public line rather than disclosing anything past it. The axiom is unused by evalSubsSpec/impl; it exists so a rival CAN be written, which is the harness's rival-writability requirement, not a hint.
2. 'the substitution ... must never rename or replace it [the binder] -- even if the substituted condition happens to simplify' (line 206). This is the closest thing to naming the removed branch's trigger (`cond is S.true`). I checked whether it is problem_statement-derivable and it is: Out[74]'s condition is `(y in [-1,1])`; after subs y->Rational(1,3) that condition is manifestly True (1/3 in [-1,1]) and Out[75] shows it VANISHED, replaced by a membership test on 1/3. The public transcript therefore exhibits exactly 'condition simplified away AND the result got re-keyed on the substituted value'. The DESIRED output is also public: Out[78] (`xreplace`) and Out[80] (`simultaneous=True`) both give `{2*pi*n + asin(1/3) | n in Z}`, which is what post-patch `ConditionSet(x, True, ImageSet)` canonicalizes to. And the user's own diagnosis is public: 'It's as if the bound variable x of the ConditionSet were mistaken for a y.'
3. 'short-circuits and leaves the whole set untouched' (lines 44, 210-211) -- this is the Tuple/compound-binder early-return arm (conditionset.py:209-212), UNCHANGED by the gold patch, describing an excluded domain, not the edit.

NEGATIVE GREPS over the spec view: no hits for S.true / 'is true' / Contains / 'assumptions are ignored' / `__new__` / 'belongs to base' / patch / gold / diff / 'the fix' / 'remov' / 'delet' / conditionset.py / any file:line citation. The gold patch's own added comment text ('The condition may have become true due to assumptions on sym. In order for .subs() to be consistent with `__new__` we *don't* check if sym actually belongs to base') appears NOWHERE in the spec view. The impl region is elided in the spec view ('implementation elided -- supplied by the consumer'), as is the proof.

**MACHINE SCREEN:** swebench_unified.leakage.screen(Solution.lean, velvet backend, gold_patch, problem_statement, test_patch) = LeakageReport(hard_failures=[], warnings=[]).

**NO FILE ADDRESSES THE REVIEWER:** leakage.reviewer_directed() = [] on all nine artifacts (Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, meta.json, axiom_check.py, conformance_check.py, properties.py, verdict.md). Independent grep for auditor|panel|attacker|adversar|'you should'|'please record'|'honest verdict'|'do not submit'|NO-LEAK|'gate FAIL'|reviewer over authored content: hits are only prior audit RECORDS in verdict.md describing their own past runs, and properties.py's use of 'attacker' to name mutation-battery rivals. No file instructs me how to record or which verdict is honest. Nothing to report as a finding on that axis.

OUT OF SCOPE, for the rollup only: meta.json stamps G-EQ, G-PANEL-1 and G-PANEL-2 fails, and verdict.md carries a G-EQ advisory that mapping.md 3.3 / axiom_check.py obligation 7 OVERSTATE mkSet's totality (ConditionSet(x, x>0, FiniteSet(I)) raises TypeError inside the preconditions, so the contract is TOO STRONG on that sliver). A too-strong / under-constraining contract discloses LESS, not more, so neither moves this verdict. My verdict is on leakage only.

**CONCLUSION:** the spec view discloses nothing about the gold edit beyond the public problem_statement -- the value-keyed rebinding shape and the simplified-condition trigger are both visible in the Out[74]/Out[75]/Out[78]/Out[80] transcript, and with all narration stripped the formal contract still admits gold and refutes the pre-patch impl. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
