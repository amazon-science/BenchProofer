# P2 adversarial audit — sympy__sympy-19495

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 17 | `atk_0_prepatch.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_10.py`, `atk_13.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 21 attacks run (all same-spec byte-identical: axioms/@Pure/Requires/Ensures untouched, only the two impl regions edited). 5 came back CANDIDATE (share spec AND verify): atk_1, atk_2, atk_3, atk_10, atk_13. Every one of the 5 had its faithful refined patch MATERIALIZED and EXECUTED through the official harness (swebench_unified.harness.run_resolve), and all 5 RESOLVED on attempt 1, non-flaky: FAIL_TO_PASS test_subs_CondSet 1/1 success, PASS_TO_PASS 8/8 success, FAIL_TO_FAIL and PASS_TO_FAIL empty, patch_successfully_applied true. So no verifying wrong impl whose materialized faithful patch fails the oracle exists on this bundle; verify=>correct is not falsified. atk_1 and atk_2 ARE genuinely behaviourally-divergent wrong impls (measured against gold in real SymPy: atk_1 diverges on 7/34 probe cases including RAISING ValueError where gold delivers ConditionSet(x+1, ...); atk_2 diverges on 5/34, e.g. gold FiniteSet(0) vs ConditionSet(1, x<1, FiniteSet(0,1,2))) yet the oracle accepts them, because the graded tests never reach those carrier shapes. Per the stated criterion (BROKEN iff a verifying wrong impl's materialized faithful patch does NOT resolve) they are a NON-BLOCKING structural observation, not a counterexample.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,15 @@
     # invariants-start
     # invariants-end
     # impl-start
+    # Pre-patch (buggy) skeleton: when the predicate collapsed to true, the
+    # result was rebuilt keyed on `new` (the replacement value) wrapped in a
+    # fresh membership predicate, instead of returning the base domain keyed on
+    # the original bound variable. The membership predicate stays a non-trivial
+    # restriction (COND_OPEN) for the discriminating input, so the bound
+    # variable wrongly becomes `new`.
+    if cond_after == COND_TRUE:
+        return build(new, COND_OPEN, base_after, base_kind, listed_kind,
+                     listed_base, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 2 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,9 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_MERGED:
+        return build(new, cond_after, base_after, base_kind, listed_kind,
+                     listed_base, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 3 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,9 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_LISTED and listed_kind != K_SET:
+        return build(new, cond_after, base_after, base_kind, listed_kind,
+                     listed_base, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 4 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -286,19 +286,24 @@
     # invariants-end
     # impl-start
     if cond == COND_FALSE:
-        return Result0(K_EMPTY, sym, base, cond)
+        return Result0(K_EMPTY, 424242, 424243, COND_TRUE)
     elif base_kind == BASE_EMPTY:
-        return Result0(K_EMPTY, sym, base, cond)
+        return Result0(K_EMPTY, 424244, 424245, COND_FALSE)
     elif cond == COND_TRUE:
-        return Result0(K_BASE, sym, base, cond)
+        return Result0(K_BASE, 424246, base, COND_FALSE)
     elif base_kind == BASE_LISTED:
-        return Result0(listed_kind, sym, listed_base, cond)
+        if listed_kind == K_EMPTY:
+            return Result0(K_EMPTY, 424247, 424248, COND_TRUE)
+        elif listed_kind == K_BASE:
+            return Result0(K_BASE, 424249, listed_base, COND_FALSE)
+        else:
+            return Result0(K_SET, sym, listed_base, COND_OPEN)
     elif base_kind == BASE_MERGED:
         if merged_sym == MERGE_REFUSED:
-            return Result0(K_REFUSED, merged_sym, merged_base, cond)
-        return Result0(K_SET, merged_sym, merged_base, cond)
+            return Result0(K_REFUSED, 424250, 424251, COND_TRUE)
+        return Result0(K_SET, merged_sym, merged_base, COND_FALSE)
     else:
-        return Result0(K_SET, sym, base, cond)
+        return Result0(K_SET, sym, base, COND_OPEN)
     # impl-end
 
 
```

Attack 5 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -289,10 +289,10 @@
         return Result0(K_EMPTY, sym, base, cond)
     elif base_kind == BASE_EMPTY:
         return Result0(K_EMPTY, sym, base, cond)
+    elif base_kind == BASE_LISTED:
+        return Result0(listed_kind, sym, listed_base, COND_OPEN)
     elif cond == COND_TRUE:
         return Result0(K_BASE, sym, base, cond)
-    elif base_kind == BASE_LISTED:
-        return Result0(listed_kind, sym, listed_base, cond)
     elif base_kind == BASE_MERGED:
         if merged_sym == MERGE_REFUSED:
             return Result0(K_REFUSED, merged_sym, merged_base, cond)
```

Attack 6 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,10 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_MERGED:
+        i = 0
+        while i >= 0:
+            i = i + 1
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 7 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,9 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if cond_after == COND_OPEN and base_kind == BASE_PLAIN:
+        return build(self_sym, COND_TRUE, base_after, base_kind, listed_kind,
+                     listed_base, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 8 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,7 +296,7 @@
     elif base_kind == BASE_MERGED:
         if merged_sym == MERGE_REFUSED:
             return Result0(K_REFUSED, merged_sym, merged_base, cond)
-        return Result0(K_SET, merged_sym, merged_base, cond)
+        return Result0(K_SET, merged_sym, base, cond)
     else:
         return Result0(K_SET, sym, base, cond)
     # impl-end
```

Attack 9 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,6 @@
     # invariants-start
     # invariants-end
     # impl-start
-    return build(self_sym, cond_after, base_after, base_kind, listed_kind,
+    return build(self_sym, cond_after, merged_base, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 10 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -287,10 +287,10 @@
     # impl-start
     if cond == COND_FALSE:
         return Result0(K_EMPTY, sym, base, cond)
+    elif cond == COND_TRUE:
+        return Result0(K_BASE, sym, base, cond)
     elif base_kind == BASE_EMPTY:
         return Result0(K_EMPTY, sym, base, cond)
-    elif cond == COND_TRUE:
-        return Result0(K_BASE, sym, base, cond)
     elif base_kind == BASE_LISTED:
         return Result0(listed_kind, sym, listed_base, cond)
     elif base_kind == BASE_MERGED:
```

Attack 11 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,7 +292,9 @@
     elif cond == COND_TRUE:
         return Result0(K_BASE, sym, base, cond)
     elif base_kind == BASE_LISTED:
-        return Result0(listed_kind, sym, listed_base, cond)
+        if listed_kind == K_SET:
+            return Result0(K_SET, sym, listed_base, COND_OPEN)
+        return Result0(listed_kind, merged_sym, listed_base, merged_base)
     elif base_kind == BASE_MERGED:
         if merged_sym == MERGE_REFUSED:
             return Result0(K_REFUSED, merged_sym, merged_base, cond)
```

Attack 12 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,9 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_LISTED:
+        return build(self_sym, cond_after, listed_base, base_kind, listed_kind,
+                     listed_base, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 13 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,8 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_MERGED and cond_after == COND_OPEN:
+        return Result0(K_REFUSED, self_sym, base_after, cond_after)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 14 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,9 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if cond_after == COND_TRUE:
+        return build(new, cond_after, base_after, base_kind, listed_kind,
+                     listed_base, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 15 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,9 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_LISTED and listed_kind == K_SET:
+        return build(new, cond_after, base_after, base_kind, listed_kind,
+                     listed_base, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 16 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,6 @@
     # invariants-start
     # invariants-end
     # impl-start
-    return build(self_sym, cond_after, base_after, base_kind, listed_kind,
+    return build(self_sym, COND_OPEN, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 17 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,9 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_LISTED:
+        return build(self_sym, cond_after, base_after, base_kind, listed_kind,
+                     base_after, merged_sym, merged_base)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 18 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -292,7 +292,7 @@
     elif cond == COND_TRUE:
         return Result0(K_BASE, sym, base, cond)
     elif base_kind == BASE_LISTED:
-        return Result0(listed_kind, sym, listed_base, cond)
+        return Result0(listed_kind, sym, base, cond)
     elif base_kind == BASE_MERGED:
         if merged_sym == MERGE_REFUSED:
             return Result0(K_REFUSED, merged_sym, merged_base, cond)
```

Attack 19 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -298,6 +298,9 @@
             return Result0(K_REFUSED, merged_sym, merged_base, cond)
         return Result0(K_SET, merged_sym, merged_base, cond)
     else:
+        i = 0
+        while i >= 0:
+            i = i + 1
         return Result0(K_SET, sym, base, cond)
     # impl-end
 
```

Attack 20 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,6 @@
     # invariants-start
     # invariants-end
     # impl-start
-    return build(self_sym, cond_after, base_after, base_kind, listed_kind,
+    return build(merged_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

Attack 21 — `atk_20.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -295,7 +295,7 @@
         return Result0(listed_kind, sym, listed_base, cond)
     elif base_kind == BASE_MERGED:
         if merged_sym == MERGE_REFUSED:
-            return Result0(K_REFUSED, merged_sym, merged_base, cond)
+            return Result0(K_EMPTY, merged_sym, merged_base, cond)
         return Result0(K_SET, merged_sym, merged_base, cond)
     else:
         return Result0(K_SET, sym, base, cond)
```

Attack 22 — `atk_21.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -400,6 +400,8 @@
     # invariants-start
     # invariants-end
     # impl-start
+    if base_kind == BASE_MERGED and merged_sym == MERGE_REFUSED:
+        return Result0(K_SET, new, base_after, COND_OPEN)
     return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                  listed_base, merged_sym, merged_base)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

POSITIVE CONTROL (non-vacuity): atk_pos.py = byte-identical copy of model.py (diff empty). weakness -> CANDIDATE (17.1s), i.e. it VERIFIES. So the verifier is not rejecting everything.

PREPATCH REPRODUCED: atk_0_prepatch.py = the bundled model_prepatch.py, which revives the real bug (`if cond is S.true: return ConditionSet(new, Contains(new, base), base)` as `if cond_after == COND_TRUE: return build(new, COND_OPEN, ...)`). weakness -> exit 2, NOT-A-COUNTEREXAMPLE, verification failed. The spec REJECTS the real bug: the clause `cond_after==COND_TRUE => Result().kind==K_BASE and Result().base==base_after` is load-bearing.

### PER-ATTACK RESULTS (all 21 fully verified; /tmp paths are <D>/atk_N.py):
- atk_1  -> CANDIDATE (18.7s). FOLD-EXPLOITATION: rfp hands `new` to build as the binder when base_kind==BASE_MERGED. RESOLVE: patch_atk_1.diff -> RESOLVED.
- atk_2  -> CANDIDATE (17.0s). FOLD-EXPLOITATION: `new` as binder on BASE_LISTED with listed_kind != K_SET. RESOLVE: patch_atk_2.diff -> RESOLVED.
- atk_3  -> CANDIDATE. DON'T-CARE SWEEP: garbages every unpinned field (sym/base/cond on K_EMPTY, sym/cond on K_BASE, sym/base/cond on LISTED/K_EMPTY, sym/cond on LISTED/K_BASE, cond on BASE_MERGED, sym/base on K_REFUSED). RESOLVE: patch_atk_3.diff -> RESOLVED.
- atk_4  -> exit 2 rejected. PARTIAL-DOMAIN/ladder-order: build decides the explicit listing BEFORE the COND_TRUE collapse.
- atk_5  -> exit 2 rejected. CONTROL-FLOW-EFFECT: `while i >= 0` in rfp never answers on BASE_MERGED; MustTerminate(3) catches it at the method level.
- atk_6  -> exit 2 rejected. PARTIAL-DOMAIN: rfp drops the restriction on BASE_PLAIN (passes COND_TRUE), returning the base domain instead of the restricted object.
- atk_7  -> exit 2 rejected. DEEP-MODEL (A-reference): build's merge leaves the object over the OUTER base domain, not the INNER one (contradicts `s, c, base_set = base_set.args`, conditionset.py:162).
- atk_8  -> exit 2 rejected. UNGROUNDED-ORACLE ECHO: rfp echoes `merged_base` into the base slot on EVERY shape.
- atk_9  -> exit 2 rejected. BOUNDARY: build tests COND_TRUE before BASE_EMPTY, so a true predicate over an empty base leaks as K_BASE; the BASE_EMPTY clause pins K_EMPTY.
- atk_10 -> CANDIDATE. ECHO INSIDE build: the LISTED branch keys the object on `merged_sym` and puts `merged_base` in the cond slot, on the listed_kind != K_SET sub-shapes. RESOLVE: patch_atk_10.diff -> RESOLVED.
- atk_11 -> exit 2 rejected. FOLD-SUBSTITUTION in the base slot: rfp passes `listed_base` as `base_after` on BASE_LISTED.
- atk_12 -> exit 2 rejected. INVENTED REFUSAL: rfp returns K_REFUSED on EVERY merge; the `merged_sym != MERGE_REFUSED => kind==K_SET` clause and the `refusal only there` clause catch it.
- atk_13 -> CANDIDATE (17.8s). The pre-patch bug's nearest admitted neighbour: on COND_TRUE, rebuild keyed on the REPLACEMENT VALUE `new` (but keeping the truth tag, unlike the real bug which substituted an OPEN membership predicate). RESOLVE: patch_atk_13.diff -> RESOLVED. Note this patch is behaviourally IDENTICAL to gold (0/34 divergences) precisely because __new__ returns base_set at `condition is S.true` before ever inspecting the binder -- which is exactly why the spec leaves the binder a don't-care there and why the clause it does pin (kind==K_BASE and base==base_after) is the load-bearing one.
- atk_14 -> exit 2 rejected. Same `new`-as-binder swap on BASE_LISTED with listed_kind == K_SET -- the shape the graded P2P regression exercises. Rejected, so that clause IS load-bearing (contrast atk_2, which is the same idea on the sub-shapes the spec leaves unanchored).
- atk_15 -> exit 2 rejected. TAG-LYING: rfp always passes COND_OPEN, skipping both truth collapses.
- atk_16 -> exit 2 rejected. FOLD-SUBSTITUTION reversed: rfp passes `base_after` into the listed_base slot.
- atk_17 -> exit 2 rejected. DEEP-MODEL (A-reference): build's LISTED branch keeps the OUTER base domain instead of the surviving members' domain.
- atk_18 -> exit 2 rejected. CONTROL-FLOW-EFFECT at the BUILD level: build never answers on BASE_PLAIN (the shape the issue headline hits); MustTerminate(2) catches it.
- atk_19 -> exit 2 rejected. ORACLE ECHO: rfp passes `merged_sym` as the binder on EVERY shape.
- atk_20 -> exit 2 rejected. REFUSAL-CORNER control (the family a PRIOR audit pass reported BROKEN): build returns K_EMPTY instead of K_REFUSED on merged_sym==MERGE_REFUSED, i.e. invents the empty domain where the real constructor raises. The pinned `merge refused => kind==K_REFUSED` clause catches it.
- atk_21 -> exit 2 rejected. Same corner keyed on the REPLACEMENT VALUE (the original bug relocated into the refusal sliver): rfp returns K_SET keyed on `new`. Rejected.

### HARNESS RESOLVE RUNS (mandatory step, all 5 CANDIDATEs, executed not speculated):
  atk_1 RESOLVED | atk_2 RESOLVED | atk_3 RESOLVED | atk_10 RESOLVED | atk_13 RESOLVED
Each: resolved=true, completed=true, attempts=1, flaky=false, patch_successfully_applied=true, FAIL_TO_PASS success=[test_subs_CondSet], PASS_TO_PASS success=all 8, PASS_TO_FAIL empty. Raw JSON in <D>/resolve_atk_*.json. So NO verifying wrong impl's faithful patch fails the oracle => NOT BROKEN.

FAITHFUL-PATCH DERIVATION (refinement.md step 8 + mapping.md 2, applied literally by <D>/mkpatch.py): build(X, cond_after, base_after, ...) |-> self.func(X, cond, base); base_kind |-> the shape of `base`; listed_* |-> the sift outcome (conditionset.py:152-159); merged_* |-> the merge outcome (161-179). Each patch starts from the gold patch (so the three pure-docstring hunks are present verbatim -- refinement.md states they are documentation-only) and swaps ONLY the behaviour-bearing tail, so the sole difference from gold is the impl region the attack edited. For atk_3 and atk_10 every garbaged field is DEAD under the refinement map (mapping.md 2 row 6 sends K_EMPTY -> S.EmptySet and K_BASE -> the pass-through base domain, neither of which has a sym or cond slot; cond on BASE_MERGED is deliberately unclaimed because the constructor performs no further reduction after the merge), so their faithful refinement IS the gold tail verbatim -- which is what was submitted and resolved. Their patches are byte-identical to each other (sha1 f223fe685660), as expected.

DIVERGENCE MEASUREMENT (<D>/divergence.py over 34 real inputs x 6 worktrees at base_commit; wt_goldonly = gold-applied, wt_atk_* = attack-patch-applied):
  atk_1: 7 diverging cases. merge_adopt_inner: gold ConditionSet(z, (z<-1)&(x+z>0), Reals) vs atk ConditionSet(-1, (x<-1)&(x-1>0), Reals) -- keyed on the replacement VALUE. merge_delivered_compound: gold delivers ConditionSet(x+1, ...) vs atk RAISES ValueError. Also merge_keep_outer, merge_mints_lambda, merge_mints_dummy, merge_no_rereduce, merge_same_sym.
  atk_2: 5 diverging cases. listed_all_admitted: gold FiniteSet(0,1,2) vs atk ConditionSet(10, x<10, FiniteSet(0,1,2)). listed_partly: gold FiniteSet(0) vs atk ConditionSet(1, x<1, FiniteSet(0,1,2)). Also listed_all_refuted, listed_mixed_sym, listed_mod.
  atk_3, atk_10, atk_13: 0 diverging cases (dead slots only / binder unread on the true path).

WHY THE ORACLE ACCEPTS atk_1 AND atk_2 (measured, not argued): I instrumented the REAL post-gold _eval_subs (<D>/probe_shapes.py) and recorded the model carrier tuple for every call the GRADED tests make through the changed old!=sym branch. Result: 9 passed, 4 calls total, only TWO distinct carrier shapes reached --
  (COND_TRUE, BASE_PLAIN) x3  -- the issue-17341 headline, the F2P regression ConditionSet(n, n<x, Interval(-oo,0)).subs(x,p), and ConditionSet(n, n<x, Interval(0,oo)).subs(x,p)
  (COND_OPEN, BASE_LISTED, listed_kind=K_SET) x1 -- ConditionSet(x, x<y, FiniteSet(y,z)).subs(y,w)
Both are shapes on which the spec PINS the binder to self_sym (the COND_TRUE clause pins kind==K_BASE and base==base_after; the LISTED/K_SET clause pins sym==self_sym and cond==COND_OPEN). atk_1 diverges only on BASE_MERGED and atk_2 only on LISTED with listed_kind != K_SET -- neither shape is reached by any graded test, hence RESOLVED. atk_14 confirms the complement: the identical swap on the LISTED/K_SET shape is REJECTED by the verifier.

STRUCTURAL OBSERVATION (non-blocking, already DISCLOSED by the bundle): listed_kind/listed_base and merged_sym/merged_base are CALLER-SUPPLIED FOLDS. In the real callee they are functions of the binder actually handed to ConditionSet.__new__; in the model they are free arguments. rfp's Ensures anchor sym==self_sym only on BASE_PLAIN and on BASE_LISTED-with-listed_kind==K_SET, so on the LISTED-decided and MERGED shapes an impl that passes a different binder to `build` is invisible to the Nagini contract.

This is an inherent cost of the fold-in-arguments abstraction and it is disclosed rather than hidden: mapping.md 2 declares it in the listed_*/merged_* rows, and refinement.md step 8 / mapping.md 1.2 both state the merge is 'the ONE shape in which the bound variable is not carried over' and that the reduction, not the caller, settles it. G-CONF closes it empirically rather than logically (conformance_check.py computes listed_outcome/merged_outcome from the REAL cs.sym and records 1604 merge comparisons that did not carry the outer binder over). Not a refinement.md misstatement; not closed by the contract. Reported for the record, not as a counterexample, since the criterion is a materialized faithful patch that fails the oracle and no such patch exists.

### A-LEG AUDIT (the focus of this pass; R/I legs are G-CONF's job):
refinement.md has 8 legs: 7 tagged R and 1 tagged 'A-reference + R' (step 8). Zero A-consumed legs, zero kind-3, and I confirmed the axioms region is literally empty ('# (none)') and the pure region empty, with no @ContractOnly / sorry / Assume in the model (grep count 0). So the ONLY deep-model trust point is step 8: build == ConditionSet.__new__'s reduction ladder.
1) LADDER CORRESPONDENCE (<D>/aleg_audit.py): transliterated build's impl and compared it to the REAL constructor over 30 witnesses covering every cell of the carrier product -- COND_FALSE/TRUE/OPEN x BASE_EMPTY/LISTED/PLAIN/MERGED, all three sift outcomes, all four merge binder outcomes (keep-same, keep-outer, adopt-inner, mint Symbol('lambda'), mint Dummy), the no-re-reduction case, the normalization family of mapping.md 1.1 (1/0/zero-Symbol/nonzero-Symbol/FiniteSet-listing), and both refusal/delivery outcomes of the compound settled binder. RESULT: 30 agree, 0 MISMATCH, 0 out-of-domain. The ladder ORDER claims hold too (false-before-empty, empty-before-true, listed-before-merge): atk_4, atk_9, atk_17 each permute the order and are all REJECTED.
2) THE REFUSAL LEG, BOTH DIRECTIONS (<D>/refusal_sweep.py) -- this is the leg a PRIOR audit pass reported BROKEN (it claimed the model asserts a delivered K_SET where the real constructor raises ValueError). I re-encoded that pass's exact named input, ConditionSet(z, z<=0, Union(Interval(0,y), ConditionSet(x+1, (z<5)&(x+1>0), Reals))).subs(y,-1): the real code RAISES ValueError('non-symbol dummy not recognized in condition'), the merge-settled binder is x+1 (not a Symbol), and merged_sym == MERGE_REFUSED, so the CURRENT model predicts K_REFUSED -- model and real AGREE. The defect has been repaired by the MERGE_REFUSED / K_REFUSED clauses now in the shipped model.py, and atk_20/atk_21 are my controls proving those clauses bite rather than sitting vacuous. I then swept 7 compound inner binders x 6 inner predicates x 3 outer predicates through the real modelled operation, requiring the biconditional (merged_outcome==MERGE_REFUSED <=> real raises ValueError) and, on the delivered side, that .sym/.base_set match the merge carriers: 117 agree, 0 MISMATCH, 9 not-compared (a truth collapse pre-empts the merge, or the inner construction itself refuses), refused=21, delivered=96. Both directions hold, so the model neither invents nor misses refusals.
3) MODEL<->PATCH CORRESPONDENCE: patch.diff is byte-identical to instance.json['patch'] (verified). Of its four hunks, three are pure docstring text (removing a stray 'Notes\n=====', deleting a duplicated 'and', adding a blank line) and one is behaviour-bearing, exactly as refinement.md states; I read the base_commit source and confirmed the behavioural hunk deletes `if cond is S.true: return ConditionSet(new, Contains(new, base), base)` and always returns self.func(self.sym, cond, base), with `else:` only re-indenting. mapping.md's line references check out against `git show 25fbcce5b1a4c7e3956e6062930f4a44ce95a632:sympy/sets/conditionset.py` (__new__ at 117, listing rewrite 125-134, as_Boolean 136, false/true 144/146, EmptySet 148, FiniteSet/sift 152-159, merge 161-179, the non-Symbol check 181-185, Basic.__new__/Union 187-188, _eval_subs 208, changed tail 243-247), and as_Boolean's documented behaviour (1/0 -> true/false, Symbol via .is_zero, else TypeError) matches mapping.md 1.1.

VERDICT: SOUND. 21 attacks fully verified (>=5 required; the required distinct families -- partial-domain, boundary, control-flow-effect, ungrounded-oracle echo -- all covered and exceeded, plus deep-model/A-reference, tag-lying, shape-lying, invented-refusal and refusal-corner families). Positive control verifies; prepatch reproduced and REJECTED. All 5 CANDIDATEs had their faithful refined patches materialized and EXECUTED through run_resolve, and all 5 RESOLVED, so no verify-but-not-correct witness exists. The A-legs' correspondence to the real callees holds (30/30 ladder cells, 117/117 refusal-sweep comparisons in both directions), and the refusal-corner defect a prior pass reported is verifiably repaired in the shipped model. Recorded non-blocking caveat: the fold-in-arguments abstraction leaves the binder unanchored on the LISTED-decided and MERGED shapes (atk_1/atk_2 are admitted, genuinely divergent wrong impls the oracle nevertheless accepts because no graded test reaches those shapes); this is disclosed in mapping.md/refinement.md and covered differentially by G-CONF rather than by the Nagini contract.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 17 | `atk_0_prepatch.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_10.py`, `atk_13.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 21 attacks run (all same-spec byte-identical: axioms/@Pure/Requires/Ensures untouched, only the two impl regions edited). 5 came back CANDIDATE (share spec AND verify): atk_1, atk_2, atk_3, atk_10, atk_13. Every one of the 5 had its faithful refined patch MATERIALIZED and EXECUTED through the official harness (swebench_unified.harness.run_resolve), and all 5 RESOLVED on attempt 1, non-flaky: FAIL_TO_PASS test_subs_CondSet 1/1 success, PASS_TO_PASS 8/8 success, FAIL_TO_FAIL and PASS_TO_FAIL empty, patch_successfully_applied true. So no verifying wrong impl whose materialized faithful patch fails the oracle exists on this bundle; verify=>correct is not falsified. atk_1 and atk_2 ARE genuinely behaviourally-divergent wrong impls (measured against gold in real SymPy: atk_1 diverges on 7/34 probe cases including RAISING ValueError where gold delivers ConditionSet(x+1, ...); atk_2 diverges on 5/34, e.g. gold FiniteSet(0) vs ConditionSet(1, x<1, FiniteSet(0,1,2))) yet the oracle accepts them, because the graded tests never reach those carrier shapes. Per the stated criterion (BROKEN iff a verifying wrong impl's materialized faithful patch does NOT resolve) they are a NON-BLOCKING structural observation, not a counterexample.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 22 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 21 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 22 — `atk_21.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

POSITIVE CONTROL (non-vacuity): atk_pos.py = byte-identical copy of model.py (diff empty). weakness -> CANDIDATE (17.1s), i.e. it VERIFIES. So the verifier is not rejecting everything.

PREPATCH REPRODUCED: atk_0_prepatch.py = the bundled model_prepatch.py, which revives the real bug (`if cond is S.true: return ConditionSet(new, Contains(new, base), base)` as `if cond_after == COND_TRUE: return build(new, COND_OPEN, ...)`). weakness -> exit 2, NOT-A-COUNTEREXAMPLE, verification failed. The spec REJECTS the real bug: the clause `cond_after==COND_TRUE => Result().kind==K_BASE and Result().base==base_after` is load-bearing.

### PER-ATTACK RESULTS (all 21 fully verified; /tmp paths are <D>/atk_N.py):
- atk_1  -> CANDIDATE (18.7s). FOLD-EXPLOITATION: rfp hands `new` to build as the binder when base_kind==BASE_MERGED. RESOLVE: patch_atk_1.diff -> RESOLVED.
- atk_2  -> CANDIDATE (17.0s). FOLD-EXPLOITATION: `new` as binder on BASE_LISTED with listed_kind != K_SET. RESOLVE: patch_atk_2.diff -> RESOLVED.
- atk_3  -> CANDIDATE. DON'T-CARE SWEEP: garbages every unpinned field (sym/base/cond on K_EMPTY, sym/cond on K_BASE, sym/base/cond on LISTED/K_EMPTY, sym/cond on LISTED/K_BASE, cond on BASE_MERGED, sym/base on K_REFUSED). RESOLVE: patch_atk_3.diff -> RESOLVED.
- atk_4  -> exit 2 rejected. PARTIAL-DOMAIN/ladder-order: build decides the explicit listing BEFORE the COND_TRUE collapse.
- atk_5  -> exit 2 rejected. CONTROL-FLOW-EFFECT: `while i >= 0` in rfp never answers on BASE_MERGED; MustTerminate(3) catches it at the method level.
- atk_6  -> exit 2 rejected. PARTIAL-DOMAIN: rfp drops the restriction on BASE_PLAIN (passes COND_TRUE), returning the base domain instead of the restricted object.
- atk_7  -> exit 2 rejected. DEEP-MODEL (A-reference): build's merge leaves the object over the OUTER base domain, not the INNER one (contradicts `s, c, base_set = base_set.args`, conditionset.py:162).
- atk_8  -> exit 2 rejected. UNGROUNDED-ORACLE ECHO: rfp echoes `merged_base` into the base slot on EVERY shape.
- atk_9  -> exit 2 rejected. BOUNDARY: build tests COND_TRUE before BASE_EMPTY, so a true predicate over an empty base leaks as K_BASE; the BASE_EMPTY clause pins K_EMPTY.
- atk_10 -> CANDIDATE. ECHO INSIDE build: the LISTED branch keys the object on `merged_sym` and puts `merged_base` in the cond slot, on the listed_kind != K_SET sub-shapes. RESOLVE: patch_atk_10.diff -> RESOLVED.
- atk_11 -> exit 2 rejected. FOLD-SUBSTITUTION in the base slot: rfp passes `listed_base` as `base_after` on BASE_LISTED.
- atk_12 -> exit 2 rejected. INVENTED REFUSAL: rfp returns K_REFUSED on EVERY merge; the `merged_sym != MERGE_REFUSED => kind==K_SET` clause and the `refusal only there` clause catch it.
- atk_13 -> CANDIDATE (17.8s). The pre-patch bug's nearest admitted neighbour: on COND_TRUE, rebuild keyed on the REPLACEMENT VALUE `new` (but keeping the truth tag, unlike the real bug which substituted an OPEN membership predicate). RESOLVE: patch_atk_13.diff -> RESOLVED. Note this patch is behaviourally IDENTICAL to gold (0/34 divergences) precisely because __new__ returns base_set at `condition is S.true` before ever inspecting the binder -- which is exactly why the spec leaves the binder a don't-care there and why the clause it does pin (kind==K_BASE and base==base_after) is the load-bearing one.
- atk_14 -> exit 2 rejected. Same `new`-as-binder swap on BASE_LISTED with listed_kind == K_SET -- the shape the graded P2P regression exercises. Rejected, so that clause IS load-bearing (contrast atk_2, which is the same idea on the sub-shapes the spec leaves unanchored).
- atk_15 -> exit 2 rejected. TAG-LYING: rfp always passes COND_OPEN, skipping both truth collapses.
- atk_16 -> exit 2 rejected. FOLD-SUBSTITUTION reversed: rfp passes `base_after` into the listed_base slot.
- atk_17 -> exit 2 rejected. DEEP-MODEL (A-reference): build's LISTED branch keeps the OUTER base domain instead of the surviving members' domain.
- atk_18 -> exit 2 rejected. CONTROL-FLOW-EFFECT at the BUILD level: build never answers on BASE_PLAIN (the shape the issue headline hits); MustTerminate(2) catches it.
- atk_19 -> exit 2 rejected. ORACLE ECHO: rfp passes `merged_sym` as the binder on EVERY shape.
- atk_20 -> exit 2 rejected. REFUSAL-CORNER control (the family a PRIOR audit pass reported BROKEN): build returns K_EMPTY instead of K_REFUSED on merged_sym==MERGE_REFUSED, i.e. invents the empty domain where the real constructor raises. The pinned `merge refused => kind==K_REFUSED` clause catches it.
- atk_21 -> exit 2 rejected. Same corner keyed on the REPLACEMENT VALUE (the original bug relocated into the refusal sliver): rfp returns K_SET keyed on `new`. Rejected.

### HARNESS RESOLVE RUNS (mandatory step, all 5 CANDIDATEs, executed not speculated):
  atk_1 RESOLVED | atk_2 RESOLVED | atk_3 RESOLVED | atk_10 RESOLVED | atk_13 RESOLVED
Each: resolved=true, completed=true, attempts=1, flaky=false, patch_successfully_applied=true, FAIL_TO_PASS success=[test_subs_CondSet], PASS_TO_PASS success=all 8, PASS_TO_FAIL empty. Raw JSON in <D>/resolve_atk_*.json. So NO verifying wrong impl's faithful patch fails the oracle => NOT BROKEN.

FAITHFUL-PATCH DERIVATION (refinement.md step 8 + mapping.md 2, applied literally by <D>/mkpatch.py): build(X, cond_after, base_after, ...) |-> self.func(X, cond, base); base_kind |-> the shape of `base`; listed_* |-> the sift outcome (conditionset.py:152-159); merged_* |-> the merge outcome (161-179). Each patch starts from the gold patch (so the three pure-docstring hunks are present verbatim -- refinement.md states they are documentation-only) and swaps ONLY the behaviour-bearing tail, so the sole difference from gold is the impl region the attack edited. For atk_3 and atk_10 every garbaged field is DEAD under the refinement map (mapping.md 2 row 6 sends K_EMPTY -> S.EmptySet and K_BASE -> the pass-through base domain, neither of which has a sym or cond slot; cond on BASE_MERGED is deliberately unclaimed because the constructor performs no further reduction after the merge), so their faithful refinement IS the gold tail verbatim -- which is what was submitted and resolved. Their patches are byte-identical to each other (sha1 f223fe685660), as expected.

DIVERGENCE MEASUREMENT (<D>/divergence.py over 34 real inputs x 6 worktrees at base_commit; wt_goldonly = gold-applied, wt_atk_* = attack-patch-applied):
  atk_1: 7 diverging cases. merge_adopt_inner: gold ConditionSet(z, (z<-1)&(x+z>0), Reals) vs atk ConditionSet(-1, (x<-1)&(x-1>0), Reals) -- keyed on the replacement VALUE. merge_delivered_compound: gold delivers ConditionSet(x+1, ...) vs atk RAISES ValueError. Also merge_keep_outer, merge_mints_lambda, merge_mints_dummy, merge_no_rereduce, merge_same_sym.
  atk_2: 5 diverging cases. listed_all_admitted: gold FiniteSet(0,1,2) vs atk ConditionSet(10, x<10, FiniteSet(0,1,2)). listed_partly: gold FiniteSet(0) vs atk ConditionSet(1, x<1, FiniteSet(0,1,2)). Also listed_all_refuted, listed_mixed_sym, listed_mod.
  atk_3, atk_10, atk_13: 0 diverging cases (dead slots only / binder unread on the true path).

WHY THE ORACLE ACCEPTS atk_1 AND atk_2 (measured, not argued): I instrumented the REAL post-gold _eval_subs (<D>/probe_shapes.py) and recorded the model carrier tuple for every call the GRADED tests make through the changed old!=sym branch. Result: 9 passed, 4 calls total, only TWO distinct carrier shapes reached --
  (COND_TRUE, BASE_PLAIN) x3  -- the issue-17341 headline, the F2P regression ConditionSet(n, n<x, Interval(-oo,0)).subs(x,p), and ConditionSet(n, n<x, Interval(0,oo)).subs(x,p)
  (COND_OPEN, BASE_LISTED, listed_kind=K_SET) x1 -- ConditionSet(x, x<y, FiniteSet(y,z)).subs(y,w)
Both are shapes on which the spec PINS the binder to self_sym (the COND_TRUE clause pins kind==K_BASE and base==base_after; the LISTED/K_SET clause pins sym==self_sym and cond==COND_OPEN). atk_1 diverges only on BASE_MERGED and atk_2 only on LISTED with listed_kind != K_SET -- neither shape is reached by any graded test, hence RESOLVED. atk_14 confirms the complement: the identical swap on the LISTED/K_SET shape is REJECTED by the verifier.

STRUCTURAL OBSERVATION (non-blocking, already DISCLOSED by the bundle): listed_kind/listed_base and merged_sym/merged_base are CALLER-SUPPLIED FOLDS. In the real callee they are functions of the binder actually handed to ConditionSet.__new__; in the model they are free arguments. rfp's Ensures anchor sym==self_sym only on BASE_PLAIN and on BASE_LISTED-with-listed_kind==K_SET, so on the LISTED-decided and MERGED shapes an impl that passes a different binder to `build` is invisible to the Nagini contract.

This is an inherent cost of the fold-in-arguments abstraction and it is disclosed rather than hidden: mapping.md 2 declares it in the listed_*/merged_* rows, and refinement.md step 8 / mapping.md 1.2 both state the merge is 'the ONE shape in which the bound variable is not carried over' and that the reduction, not the caller, settles it. G-CONF closes it empirically rather than logically (conformance_check.py computes listed_outcome/merged_outcome from the REAL cs.sym and records 1604 merge comparisons that did not carry the outer binder over). Not a refinement.md misstatement; not closed by the contract. Reported for the record, not as a counterexample, since the criterion is a materialized faithful patch that fails the oracle and no such patch exists.

### A-LEG AUDIT (the focus of this pass; R/I legs are G-CONF's job):
refinement.md has 8 legs: 7 tagged R and 1 tagged 'A-reference + R' (step 8). Zero A-consumed legs, zero kind-3, and I confirmed the axioms region is literally empty ('# (none)') and the pure region empty, with no @ContractOnly / sorry / Assume in the model (grep count 0). So the ONLY deep-model trust point is step 8: build == ConditionSet.__new__'s reduction ladder.
1) LADDER CORRESPONDENCE (<D>/aleg_audit.py): transliterated build's impl and compared it to the REAL constructor over 30 witnesses covering every cell of the carrier product -- COND_FALSE/TRUE/OPEN x BASE_EMPTY/LISTED/PLAIN/MERGED, all three sift outcomes, all four merge binder outcomes (keep-same, keep-outer, adopt-inner, mint Symbol('lambda'), mint Dummy), the no-re-reduction case, the normalization family of mapping.md 1.1 (1/0/zero-Symbol/nonzero-Symbol/FiniteSet-listing), and both refusal/delivery outcomes of the compound settled binder. RESULT: 30 agree, 0 MISMATCH, 0 out-of-domain. The ladder ORDER claims hold too (false-before-empty, empty-before-true, listed-before-merge): atk_4, atk_9, atk_17 each permute the order and are all REJECTED.
2) THE REFUSAL LEG, BOTH DIRECTIONS (<D>/refusal_sweep.py) -- this is the leg a PRIOR audit pass reported BROKEN (it claimed the model asserts a delivered K_SET where the real constructor raises ValueError). I re-encoded that pass's exact named input, ConditionSet(z, z<=0, Union(Interval(0,y), ConditionSet(x+1, (z<5)&(x+1>0), Reals))).subs(y,-1): the real code RAISES ValueError('non-symbol dummy not recognized in condition'), the merge-settled binder is x+1 (not a Symbol), and merged_sym == MERGE_REFUSED, so the CURRENT model predicts K_REFUSED -- model and real AGREE. The defect has been repaired by the MERGE_REFUSED / K_REFUSED clauses now in the shipped model.py, and atk_20/atk_21 are my controls proving those clauses bite rather than sitting vacuous. I then swept 7 compound inner binders x 6 inner predicates x 3 outer predicates through the real modelled operation, requiring the biconditional (merged_outcome==MERGE_REFUSED <=> real raises ValueError) and, on the delivered side, that .sym/.base_set match the merge carriers: 117 agree, 0 MISMATCH, 9 not-compared (a truth collapse pre-empts the merge, or the inner construction itself refuses), refused=21, delivered=96. Both directions hold, so the model neither invents nor misses refusals.
3) MODEL<->PATCH CORRESPONDENCE: patch.diff is byte-identical to instance.json['patch'] (verified). Of its four hunks, three are pure docstring text (removing a stray 'Notes\n=====', deleting a duplicated 'and', adding a blank line) and one is behaviour-bearing, exactly as refinement.md states; I read the base_commit source and confirmed the behavioural hunk deletes `if cond is S.true: return ConditionSet(new, Contains(new, base), base)` and always returns self.func(self.sym, cond, base), with `else:` only re-indenting. mapping.md's line references check out against `git show 25fbcce5b1a4c7e3956e6062930f4a44ce95a632:sympy/sets/conditionset.py` (__new__ at 117, listing rewrite 125-134, as_Boolean 136, false/true 144/146, EmptySet 148, FiniteSet/sift 152-159, merge 161-179, the non-Symbol check 181-185, Basic.__new__/Union 187-188, _eval_subs 208, changed tail 243-247), and as_Boolean's documented behaviour (1/0 -> true/false, Symbol via .is_zero, else TypeError) matches mapping.md 1.1.

VERDICT: SOUND. 21 attacks fully verified (>=5 required; the required distinct families -- partial-domain, boundary, control-flow-effect, ungrounded-oracle echo -- all covered and exceeded, plus deep-model/A-reference, tag-lying, shape-lying, invented-refusal and refusal-corner families). Positive control verifies; prepatch reproduced and REJECTED. All 5 CANDIDATEs had their faithful refined patches materialized and EXECUTED through run_resolve, and all 5 RESOLVED, so no verify-but-not-correct witness exists. The A-legs' correspondence to the real callees holds (30/30 ladder cells, 117/117 refusal-sweep comparisons in both directions), and the refusal-corner defect a prior pass reported is verifiably repaired in the shipped model. Recorded non-blocking caveat: the fold-in-arguments abstraction leaves the binder unanchored on the LISTED-decided and MERGED shapes (atk_1/atk_2 are admitted, genuinely divergent wrong impls the oracle nevertheless accepts because no graded test reaches those shapes); this is disclosed in mapping.md/refinement.md and covered differentially by G-CONF rather than by the Nagini contract.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

SPEC REGION INTEGRITY: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-19495 atk.py` on a byte-copy of model.py -> exit 0, 'SAME — attack shares the bundle's exact specification'. `bash scripts/nagini_verify.sh model.py` -> 'Verification successful' (21.9s).

REFERENCE DISCIPLINE: I honored the instruction that the modeled function's reference is the base_commit worktree with patch.diff APPLIED. Fresh worktrees: (25fbcce5b1 + patch.diff, applied cleanly) and  (pristine base).

### What I attacked and what held

1. RELATIONAL SWEEP (my primary method — directly targets 'the modeled function disagrees with the real callee'). Rather than reuse the bundle's abstract_result (which could hide a divergence behind its own conventions), I wrote an independent permissive realization relation: K_EMPTY iff real is EmptySet; K_BASE iff obj_id(real)==shadow.base; K_SET iff real is a ConditionSet with matching .sym/.base_set (plus cond OPEN on non-merge shapes); K_REFUSED iff the real method raises the exact ValueError. Sweep A: 2,335-ConditionSet pool x 15 replacements = 33,558 in-domain comparisons -> 0 failures. Sweep B (deliberately exotic): 22,211-ConditionSet pool built from 16 inner restricted objects (incl. compound binders x+1, 2*x, x**2, a literal Symbol('lambda'), and a NESTED ConditionSet-in-ConditionSet), 40+ base-domain families (ImageSet, Intersection, Complement, Naturals, Rationals, UniversalSet, Union-with-inner-ConditionSet, listed sets), 19 predicate shapes, 28 replacements (incl. nan, I, oo, -oo, FiniteSet, pi, sqrt(2), x+1, 2*x, x**2) = 53,890 in-domain comparisons -> 0 FAILURES (4,745 skipped where the substitution itself raises, 1,342 no-tag, 23 listed-raise — all genuine out-of-domain, each independently confirmed to make the real method raise too).

2. THE 'REFUSAL HAPPENS ONLY THERE' CLAUSE (the strongest, most breakable claim). I hunted for an admitted input where the real method raises but the spec demands a delivered domain. Probed sift-raising listed bases, non-real comparisons (I, nan), FiniteSet replacements, base-becomes-non-Set, the merge refusal, and nested merges. Every real raise fell outside the admitted domain (the substitution or as_Boolean raises first, so there is no COND_* tag), EXCEPT the merge refusal — where merged_outcome returns MERGE_REFUSED (ms=0) and the real method raises exactly ValueError('non-symbol dummy not recognized in condition'), which is precisely what the spec pins as K_REFUSED. No spec-delivers/real-raises input found. The reciprocal direction (spec refuses, real delivers) also never fired.

3. K_SET => cond==COND_OPEN on non-merge shapes: swept for a real ConditionSet result carrying a non-open stored predicate on BASE_PLAIN/BASE_LISTED; none found. The spec correctly withholds this claim on BASE_MERGED, where the constructor performs no re-reduction and ConditionSet(z, False, Reals) really does stand.

4. NOT-THE-PATCH-DELTA CONTROL (guarding against the trap named in the prompt). I ran my divergence family on BOTH worktrees. The absorbed-merge family behaves IDENTICALLY pre- and post-patch (4/4 cases, byte-identical results), confirming it is not the patch's delta and so could not have been laundered into a false UNFAITHFUL. Conversely the COND_TRUE => K_BASE clause is exactly the delta: issue-17341 gives ImageSet(...) on gold vs ConditionSet(1/3, Contains(1/3, ...), ...) on base; F2P gives Interval(-oo,0) on gold vs EmptySet on base. The spec agrees with GOLD on both, which is correct per the stated reference.

5. BUNDLE'S OWN CHECKS reproduced on my gold worktree: axiom_check.py -> exit 0 ('deep models agree with real SymPy', sections [1]-[5]); conformance_check.py -> exit 0, 100,000 comparisons, 0 disagreements, with the load-bearing legs actually reached (base_merged=3535 of which merge_renamed_binder=1609, merge_refused_binder=3, base_empty=2706, base_listed=26308, base_plain=67451). Discriminator control: model_prepatch.py FAILS with exactly the expected error at the COND_TRUE clause ('Postcondition of replace_free_parameter might not hold'), so the spec is not vacuous and does sense the bug.

HONEST RESIDUAL RISK: the spec is stated over an int-id/truth-tag abstraction with the shape-specific outcomes (listed_outcome, merged_outcome) FOLDED IN as caller-supplied arguments, replayed from the repo's own lines. That folding is the real trust point — merged_outcome and listed_outcome are hand-transliterations of conditionset.py:152-185, so a transliteration bug would be invisible to a differential harness that uses the same function on both sides. I read both against the applied source line by line and they match, including the non-obvious details the mapping.md corrections call out: the 181-185 check is on the SETTLED binder (not the caller's) and is a Dummy-trace test rather than isinstance(sym, Symbol), and the merge runs no further reduction.

Also noteworthy in the spec's favour: mapping.md documents three prior self-corrections (the normalization tag in §1.1, the wrongly-excluded merge branch in §1.2, the refusal pinning in §3.1.1) where earlier revisions were too WEAK or wrongly narrowed scope, and each was repaired by adding specification rather than shrinking the domain — domain_rejected is now 0 by measurement. I found no input on which the modeled function disagrees with the real callee, so my gate is FAITHFUL.

Counterexample / evidence:

```
REFUTED CANDIDATE (my strongest attack, retracted): C = ConditionSet(z, (x+z>0)&(z<5), Reals); Q = ConditionSet(z, z<y, Union(Interval(y,0), C)); Q._eval_subs(y, 5). Here cond_after = (z<5) is COND_OPEN, base_after == C so base_kind = BASE_MERGED, and merged_outcome settles merged_sym = z (sym==s branch), merged_base = Reals. The spec's merge clause demands kind==K_SET and base==merged_base==Reals. The real method returns ConditionSet(z, (z<5)&(x+z>0), Reals) — a value that is EQUAL to base_after (the merge is idempotent because And(cond,c)==c), so the bundle's own abstract_result tests `real == base_after` FIRST and tags it K_BASE with base==C, and conformance_check.check_one reports ('diff', 'kind/sym/base mismatch: tag=2 btag=3 shadow=(kind=2,sym=1,base=2) oracle=(1,None,1,None)'). I built a paired input P = ConditionSet(x, Contains(y,Interval(-2,6)), Union(Interval(y,0), C)) with cond_after==COND_TRUE, base_after==C, whose real return value is the IDENTICAL object, and on which the spec demands K_BASE/base==C — so the same observable pair (returned value, base_after) appeared to carry contradictory obligations (K_BASE/base=C vs K_SET/base=Reals, and Reals != C), which looked abstraction-independent. WHY THIS IS NOT A DEFECT: the contradiction is an artifact of MY realization relation, not of the spec. Q's result genuinely IS a restricted object over the inner base domain Reals keyed on z — ConditionSet(z, (z<5)&(x+z>0), Reals) literally has .sym==z and .base_set==Reals — so the spec's K_SET/sym=z/base=Reals clause is TRUE of it. It merely also happens to be structurally equal to base_after. Both descriptions are true of one value; the ordering of the two isinstance/equality tests in abstract_result is a bridge convention for the differential harness, not a spec obligation. When I replaced my (incorrect) `K_BASE iff real==base_after` rule with the honest reading (K_BASE demands obj_id(real)==shadow.base, i.e. the base the spec actually pins — base_after for COND_TRUE, listed_base for BASE_LISTED), the failure count over the same 33,558-comparison pool went from 299 to 0.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

NO RELAXATION IN THIS BUNDLE — checked before anything else. `find -name '*RELAX*'` over the bundle root and instance root is empty; meta.json has no `relaxed_leakage` key ('relaxed_leakage' in m -> False); meta.gates['G-LEAK'].status == 'pass' (not 'relaxed'). So this is a STANDARD leakage judgement and the relaxation-vetting path does not apply — I did not inherit any disposition. I still ran leakage.reviewer_directed() over model.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py, properties.py and the 659KB verdict.md: [] on every one.

FILES ADDRESSING ME (reportable in its own right). No bundle file instructs me how to record or which verdict is honest, but two artifacts DO contain prior G-PANEL-3 records: verdict.md:11965-11996 and meta.json gates['G-PANEL']['...']['G-PANEL-3'] carry a previous leakage agent's own submitted note, ending 'CONCLUSION: ... no repo identifier, no gold line, no patched path'. I treated these as transcripts of past runs, not as instructions, and did not inherit them: every measurement below is mine, re-run from scratch. Notably I contradict that record on one point — it claims a 325-line spec view; mine is 391 lines — so model.py was revised after it was written and its numbers are stale. Independently: meta.json's TOP-LEVEL region_hashes.spec_view (d3fce227...) is ALSO stale, disagreeing with the live spec view, while the G-HYGIENE gate record's own hashes match current model.py. Bookkeeping staleness only — it does not affect the leakage question, but it means the top-level field cannot be used as provenance.

SPEC VIEW PROVENANCE (measured). markers.spec_view(model.py, get_backend('nagini')) = 391 lines, sha256 31fbf0385ce6658d7fed8cbe1f92fb752e8dd767ee7863a62afd517129a737f5 == meta.gates['G-HYGIENE'].data.region_hashes.spec_view exactly. Confirmed BYTE-IDENTICAL to what the consumer receives: eval.adapter.get_adapter('nagini').spec_view(src) == my view -> True. Diffing model.py against the spec view shows ONLY the two impl regions replaced by '...  # implementation elided' (build's 14-line ladder and replace_free_parameter's one-line delegation) — nothing else is hidden, so I judged the whole remaining text. same_spec(model.py, model_prepatch.py) -> True, so the spec region is genuinely shared and only the impl differs. Wrote all scratch to a private mktemp -d (an earlier fixed-name /tmp file was clobbered mid-run by a concurrent instance, which I caught and redid).

MECHANICAL SCREEN, RE-DERIVED. leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. My own re-derivation: (a) normalized all 19 added/removed gold lines against the normalized spec view at len>=12 -> ZERO reproduced; (b) patch symbols {ConditionSet, eval_subs} vs the 37 spec-view AST identifiers -> ZERO collisions (the view speaks only of 'restricted object'/'base domain'/'bound variable', build/replace_free_parameter); (c) patched path sympy/sets/conditionset.py absent, and fragments 'conditionset', 'sympy/sets', '_eval_subs' all absent; (d) the single '---' hit is a '# ---...' section-divider comment at line 106, NOT a diff marker — I opened it to confirm; (e) tokens 'Contains', 'S.true', 'S.false', 'self.func', 'ConditionSet', 'Notes', '=====', 'assumptions are ignored', 'free symbol' -> all False.

LOAD-BEARING / STRIP TEST (my decisive measurement). In a pristine worktree at base_commit 25fbcce5b1 I mechanically deleted every comment and docstring from BOTH models via tokenize (keeping only region markers and `# type: int` annotations, which Nagini needs — my first attempt dropped them and hit 'Result0 has no attribute kind', so I re-stripped), leaving 151/154 lines of bare executable contract with zero narration. Pinned verifier: de-narrated GOLD -> 'Verification successful' (19.85s); de-narrated PREPATCH -> 'Verification failed', pre_bare.py:124: 'Postcondition of replace_free_parameter might not hold. Assertion Implies(((cond_after == COND_TRUE) and (base_kind != BASE_EMPTY)), ((Result().kind == K_BASE) and (Result().base == base_after)))'. The bare formal spec still rejects prepatch on exactly ONE clause, so the discriminator lives entirely in the Ensures and the prose narration is NOT load-bearing — it carries nothing the contract does not already say. Unstripped controls agree: model.py verifies (21.97s), model_prepatch.py fails at :357 on the identical clause.

FACET DISCLOSED, AND IT IS PUBLIC FROM problem_statement ALONE (never hints_text; hints_text is empty here anyway, len 0). The one facet pinned is: when the predicate collapses to identically TRUE, the result is the base domain itself keyed on the ORIGINAL bound variable, never a fresh restricted object keyed on the replacement value. I re-derived this from the issue text by replaying the reporter's own transcript against PRE-patch code: In[75] -> ConditionSet(1/3, Contains(1/3, ImageSet(...)), ImageSet(...)) (the bug, verbatim in the statement), while In[78] xreplace and In[80] simultaneous=True BOTH -> ImageSet(Lambda(n, 2*pi*n + asin(1/3)), Integers) — exactly the desired output, also verbatim in the statement. The statement additionally hands over the diagnosis: 'It's as if the bound variable x of the ConditionSet were mistaken for a y.' Confirmed the trigger really is the COND_TRUE tag: Contains(y,Interval(-1,1)).subs(y,1/3) is S.true -> True. A solver reading only the issue can derive the clause; the spec view adds nothing.

I ALSO CHECKED THE F2P ASSERTION THAT IS *NOT* IN THE STATEMENT — the risk that the view pins a non-public facet. The test patch changes ConditionSet(n, n<x, Interval(-oo,0)).subs(x,p) from S.EmptySet to Interval(-oo,0). Measured that this is the SAME COND_TRUE facet, not a second one: with the test's n negative and p positive, (n<p) is S.true -> True, and pre-patch the wrap gives Contains(p, Interval(-oo,0)) == False, hence EmptySet (I reproduced the exact pre-patch failure 'assert EmptySet == Interval(-oo, 0)'). So no additional facet is disclosed.

WHAT IS NOT DISCLOSED. The deleted construct's SHAPE is absent: grep -ciE 'membership|wrapp|belongs|check if|Contains' over the spec view -> 0, so `return ConditionSet(new, Contains(new, base), base)` is NOT reconstructible from the view. The gold comment's nuance is absent too: 'assumption|ignored' -> 0. The prepatch model's own narration ('fresh membership predicate', 'Pre-patch (buggy)', 'wrongly becomes') -> 0 hits, correctly elided with the impl region. The three docstring hunks ('Notes', '=====', 'and appears as a free symbol') -> absent. refinement.md and mapping.md DO name the deleted construct explicitly, but neither is part of the consumer spec view (confirmed via the adapter identity above).

BASE_MERGED / K_REFUSED CLAUSES ARE UNCHANGED-CODE BEHAVIOUR, NOT GOLD CONTENT. The view's merge and refusal clauses (BASE_MERGED, merged_sym, MERGE_REFUSED) describe ConditionSet.__new__, which the gold patch does not touch. I read __new__ at base_commit (conditionset.py:141-186): the sift over FiniteSet, the four-branch merge that can adopt the inner binder or mint Symbol('lambda')/Dummy, and the line-181 'non-symbol dummy not recognized in condition' guard are ALL present pre-patch, and the merge behaviour is publicly documented in the base_commit docstring at :102-115 ('Although the name is usually respected, it must be replaced if the base set is another ConditionSet...' -> ConditionSet(lambda, ...)). The patch's only touch to that prose is a typo fix and moving a 'Notes' header. So these clauses localize nothing about the edit.

CORE GATES THE ARGUMENT LEANS ON — VERIFIED MYSELF, NOT STAMP-READ. Gold verifies / prepatch fails on the single COND_TRUE clause (both full and de-narrated: 4 verifier runs). And the correctness oracle discriminates: in the worktree with gold + test patch applied, test_subs_CondSet -> 1 passed; reverting ONLY sympy/sets/conditionset.py and keeping the test patch -> 1 failed ('assert EmptySet == Interval(-oo, 0)'). So G-GOLD/G-DIFF/G-RESOLVE discrimination is my own measurement.

CONCLUSION: the spec view states desired behaviour in domain vocabulary that the public problem_statement already exhibits — the bug, the correct answer, and the diagnosis — with no repo identifier, no gold line, no patched path, no diff marker, no bug/fix narration, and no trace of the removed construct's shape; and the strip test shows the discriminating clause is formal, not narrated. Worked only under /tmp (mktemp -d worktree at base_commit); nothing written outside scratch.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
