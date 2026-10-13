# P2 adversarial audit — django__django-16901

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_01_uncond_mod.lean`, `atk_02_no_or.lean`, `atk_03_uncond_mod_no_or.lean`, `atk_04_not_even.lean`, `atk_05_shift.lean`, `atk_06_runtime_guard.lean`, `atk_08_oracle_echo.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_00_prepatch.lean`, `atk_07_boundary_gt3.lean`, `atk_09_partial_empty.lean`, `atk_10_early_exit.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No verifying same-spec impl whose faithful refined patch fails to resolve. All 7 verifying attacks were materialized as faithful patches and ALL 7 completed the official harness with resolved=True (0 inconclusive). Root cause is structural, not luck: the postcondition `ensures out = parityOdd children` is a TOTAL FUNCTIONAL equality with NO precondition and no existential slack, so every verifying same-spec impl is extensionally EQUAL to parityOdd = decide (trueCount xs % 2 = 1). Verification therefore pins the modeled row-level membership boolean EXACTLY (pointwise on all of List Bool, including []), leaving no room for a semantic wedge. The A-legs, which I was asked to concentrate on, are vacuous BY CONSTRUCTION: meta.json axioms=[] and deep_model_references=[], the axioms region is comment-only, and Solution.lean contains no `axiom`/`sorry`/`opaque`/`native_decide`/`implemented_by` escape hatch -- so there is no axiom-soundness trust point to attack at all.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_00_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,8 +73,8 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- PRE-PATCH: bare tally, no modular wrap => 'exactly one' semantics.
+    return (decide (0 < count)) && decide (count = 1)
     -- impl-end
 
 prove_correct oddParityReduce by
```

Attack 2 — `atk_01_uncond_mod.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,8 +73,8 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- Drops the arity guard: MOD(sum,2) at EVERY arity. OR conjunct kept.
+    return (decide (0 < count)) && decide (count % 2 = 1)
     -- impl-end
 
 prove_correct oddParityReduce by
@@ -85,14 +85,8 @@
     subst done_1
     simp only [List.drop_zero] at invariant_2
     rw [← hc, invariant_2]
-    (unfold parityOdd;
-     have hle := trueCount_le_length children;
-     by_cases hlen : children.length > 2 <;>
-       simp only [hlen, if_true, if_false] <;>
-       first
-         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
-                trueCount children = 2 := by omega;
-            rcases hb with h | h | h <;> rw [h] <;> decide)
-         | (by_cases hpar : trueCount children % 2 = 1 <;>
-              [ (have hpos : 0 < trueCount children := by omega;
-                 simp [hpar, hpos]) ; simp [hpar] ]))
+    unfold parityOdd
+    by_cases hpar : trueCount children % 2 = 1
+    · have hpos : 0 < trueCount children := by omega
+      simp [hpar, hpos]
+    · simp [hpar]
```

Attack 3 — `atk_02_no_or.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,8 +73,8 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- Drops the lhs OR conjunct entirely (no (a OR b OR ...) in the SQL).
+    return decide ((if children.length > 2 then count % 2 else count) = 1)
     -- impl-end
 
 prove_correct oddParityReduce by
@@ -85,14 +85,11 @@
     subst done_1
     simp only [List.drop_zero] at invariant_2
     rw [← hc, invariant_2]
-    (unfold parityOdd;
-     have hle := trueCount_le_length children;
-     by_cases hlen : children.length > 2 <;>
-       simp only [hlen, if_true, if_false] <;>
-       first
-         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
-                trueCount children = 2 := by omega;
-            rcases hb with h | h | h <;> rw [h] <;> decide)
-         | (by_cases hpar : trueCount children % 2 = 1 <;>
-              [ (have hpos : 0 < trueCount children := by omega;
-                 simp [hpar, hpos]) ; simp [hpar] ]))
+    unfold parityOdd
+    have hle := trueCount_le_length children
+    by_cases hlen : children.length > 2
+    · rw [if_pos hlen]
+    · rw [if_neg hlen]
+      have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
+          trueCount children = 2 := by omega
+      rcases hb with h | h | h <;> rw [h] <;> decide
```

Attack 4 — `atk_03_uncond_mod_no_or.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,8 +73,8 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- Bare MOD(sum,2)=1: no OR conjunct AND no arity guard.
+    return decide (count % 2 = 1)
     -- impl-end
 
 prove_correct oddParityReduce by
@@ -85,14 +85,5 @@
     subst done_1
     simp only [List.drop_zero] at invariant_2
     rw [← hc, invariant_2]
-    (unfold parityOdd;
-     have hle := trueCount_le_length children;
-     by_cases hlen : children.length > 2 <;>
-       simp only [hlen, if_true, if_false] <;>
-       first
-         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
-                trueCount children = 2 := by omega;
-            rcases hb with h | h | h <;> rw [h] <;> decide)
-         | (by_cases hpar : trueCount children % 2 = 1 <;>
-              [ (have hpos : 0 < trueCount children := by omega;
-                 simp [hpar, hpos]) ; simp [hpar] ]))
+    unfold parityOdd
+    rfl
```

Attack 5 — `atk_04_not_even.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,8 +73,8 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- Complemented predicate: NOT(MOD(sum,2) = 0) instead of MOD(sum,2) = 1.
+    return (decide (0 < count)) && !(decide (count % 2 = 0))
     -- impl-end
 
 prove_correct oddParityReduce by
@@ -85,14 +85,11 @@
     subst done_1
     simp only [List.drop_zero] at invariant_2
     rw [← hc, invariant_2]
-    (unfold parityOdd;
-     have hle := trueCount_le_length children;
-     by_cases hlen : children.length > 2 <;>
-       simp only [hlen, if_true, if_false] <;>
-       first
-         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
-                trueCount children = 2 := by omega;
-            rcases hb with h | h | h <;> rw [h] <;> decide)
-         | (by_cases hpar : trueCount children % 2 = 1 <;>
-              [ (have hpos : 0 < trueCount children := by omega;
-                 simp [hpar, hpos]) ; simp [hpar] ]))
+    unfold parityOdd
+    have h2 : trueCount children % 2 = 0 ∨ trueCount children % 2 = 1 := by omega
+    rcases h2 with h | h
+    · have hne : ¬(trueCount children % 2 = 1) := by omega
+      simp [h, hne]
+    · have hpos : 0 < trueCount children := by omega
+      have hne : ¬(trueCount children % 2 = 0) := by omega
+      simp [h, hne, hpos]
```

Attack 6 — `atk_05_shift.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,8 +73,8 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- Shifted modulus: MOD(sum + 1, 2) = 0 instead of MOD(sum, 2) = 1.
+    return (decide (0 < count)) && decide ((count + 1) % 2 = 0)
     -- impl-end
 
 prove_correct oddParityReduce by
@@ -85,14 +85,12 @@
     subst done_1
     simp only [List.drop_zero] at invariant_2
     rw [← hc, invariant_2]
-    (unfold parityOdd;
-     have hle := trueCount_le_length children;
-     by_cases hlen : children.length > 2 <;>
-       simp only [hlen, if_true, if_false] <;>
-       first
-         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
-                trueCount children = 2 := by omega;
-            rcases hb with h | h | h <;> rw [h] <;> decide)
-         | (by_cases hpar : trueCount children % 2 = 1 <;>
-              [ (have hpos : 0 < trueCount children := by omega;
-                 simp [hpar, hpos]) ; simp [hpar] ]))
+    unfold parityOdd
+    have h2 : trueCount children % 2 = 0 ∨ trueCount children % 2 = 1 := by omega
+    rcases h2 with h | h
+    · have h1 : ¬((trueCount children + 1) % 2 = 0) := by omega
+      have h3 : ¬(trueCount children % 2 = 1) := by omega
+      simp [h1, h3]
+    · have hpos : 0 < trueCount children := by omega
+      have h1 : (trueCount children + 1) % 2 = 0 := by omega
+      simp [hpos, h1, h]
```

Attack 7 — `atk_06_runtime_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -73,8 +73,9 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- Guard moved from the STATIC arity len(children) to the RUNTIME tally:
+    -- the SQL needs a CASE over rhs_sum at every arity.
+    return (decide (0 < count)) && decide ((if count > 2 then count % 2 else count) = 1)
     -- impl-end
 
 prove_correct oddParityReduce by
@@ -85,14 +86,14 @@
     subst done_1
     simp only [List.drop_zero] at invariant_2
     rw [← hc, invariant_2]
-    (unfold parityOdd;
-     have hle := trueCount_le_length children;
-     by_cases hlen : children.length > 2 <;>
-       simp only [hlen, if_true, if_false] <;>
-       first
-         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
-                trueCount children = 2 := by omega;
-            rcases hb with h | h | h <;> rw [h] <;> decide)
-         | (by_cases hpar : trueCount children % 2 = 1 <;>
-              [ (have hpos : 0 < trueCount children := by omega;
-                 simp [hpar, hpos]) ; simp [hpar] ]))
+    unfold parityOdd
+    by_cases hc : trueCount children > 2
+    · rw [if_pos hc]
+      by_cases hpar : trueCount children % 2 = 1
+      · have hpos : 0 < trueCount children := by omega
+        simp [hpar, hpos]
+      · simp [hpar]
+    · rw [if_neg hc]
+      have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
+          trueCount children = 2 := by omega
+      rcases hb with h | h | h <;> rw [h] <;> decide
```

Attack 8 — `atk_07_boundary_gt3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,8 +73,9 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
+    -- BOUNDARY: threshold off by one (> 3). Wrong at arity 3 with 3 true.
     return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+      decide ((if children.length > 3 then count % 2 else count) = 1)
     -- impl-end
 
 prove_correct oddParityReduce by
```

Attack 9 — `atk_08_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,37 +62,9 @@
   ensures out = parityOdd children
   do
     -- impl-start
-    let mut count : Nat := 0
-    let mut i := children.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ children.length
-      invariant count = trueCount (children.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := children[i - 1]!
-      count := (if c then 1 else 0) + count
-      i := i - 1
-    return (decide (0 < count)) &&
-      decide ((if children.length > 2 then count % 2 else count) = 1)
+    -- UNGROUNDED ORACLE ECHO: returns the spec function itself, no computation.
+    return parityOdd children
     -- impl-end
 
 prove_correct oddParityReduce by
   loom_solve
-  · rw [trueCount_drop_step children i (by omega) (by omega)]
-    rw [‹count = trueCount (children.drop i)›]
-  · injection i_3 with hc _
-    subst done_1
-    simp only [List.drop_zero] at invariant_2
-    rw [← hc, invariant_2]
-    (unfold parityOdd;
-     have hle := trueCount_le_length children;
-     by_cases hlen : children.length > 2 <;>
-       simp only [hlen, if_true, if_false] <;>
-       first
-         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
-                trueCount children = 2 := by omega;
-            rcases hb with h | h | h <;> rw [h] <;> decide)
-         | (by_cases hpar : trueCount children % 2 = 1 <;>
-              [ (have hpos : 0 < trueCount children := by omega;
-                 simp [hpar, hpos]) ; simp [hpar] ]))
```

Attack 10 — `atk_09_partial_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,9 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
-    return (decide (0 < count)) &&
+    -- PARTIAL DOMAIN: the empty operand list is answered `true` (parityOdd [] = false).
+    return if children.length = 0 then true else
+      (decide (0 < count)) &&
       decide ((if children.length > 2 then count % 2 else count) = 1)
     -- impl-end
 
```

Attack 11 — `atk_10_early_exit.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
     -- impl-start
     let mut count : Nat := 0
     let mut i := children.length
-    while i > 0
+    while i > 0 && count < 2
       invariant 0 ≤ i ∧ i ≤ children.length
       invariant count = trueCount (children.drop i)
       done_with i = 0
@@ -73,6 +73,8 @@
       let c := children[i - 1]!
       count := (if c then 1 else 0) + count
       i := i - 1
+    -- CONTROL-FLOW EFFECT: the loop abandons the tally once count reaches 2,
+    -- so wide rows with >= 3 true operands are mis-classified.
     return (decide (0 < count)) &&
       decide ((if children.length > 2 then count % 2 else count) = 1)
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none: this bundle has no axiomatized callees — the modeled operation is a
--  pure boolean/arithmetic reduction over already-evaluated operand truth
--  values; see mapping.md §3 and refinement.md §C.)
-- axioms-end

-- pure-start
/- The number of operands that hold for one row: the running tally of the
   per-operand 1/0 indicators. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern). -/
def trueCount : List Bool → Nat
  | []      => 0
  | c :: cs => (if c then 1 else 0) + trueCount cs

@[grind] lemma trueCount_nil : trueCount [] = 0 := rfl
@[grind] lemma trueCount_cons (c : Bool) (cs : List Bool) :
    trueCount (c :: cs) = (if c then 1 else 0) + trueCount cs := rfl

/- The chained exclusive-or of a row's operands: true exactly when an odd number
   of them hold. This is the value the combined predicate must compute. -/
def parityOdd (xs : List Bool) : Bool := decide (trueCount xs % 2 = 1)

/- At most as many operands hold as there are operands. -/
lemma trueCount_le_length : ∀ xs : List Bool, trueCount xs ≤ xs.length
  | []      => by simp [trueCount]
  | c :: cs => by
      have ih := trueCount_le_length cs
      simp only [trueCount, List.length_cons]
      split <;> omega

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `trueCount` peels one indicator. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma trueCount_drop_step (xs : List Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    trueCount (xs.drop (i - 1)) =
      (if xs[i - 1]! then 1 else 0) + trueCount (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, trueCount_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method oddParityReduce (children : List Bool) return (out : Bool)
  ensures out = parityOdd children
  do
    -- impl-start
    let mut count : Nat := 0
    let mut i := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant count = trueCount (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      count := (if c then 1 else 0) + count
      i := i - 1
    return (decide (0 < count)) &&
      decide ((if children.length > 2 then count % 2 else count) = 1)
    -- impl-end

prove_correct oddParityReduce by
  loom_solve
  · rw [trueCount_drop_step children i (by omega) (by omega)]
    rw [‹count = trueCount (children.drop i)›]
  · injection i_3 with hc _
    subst done_1
    simp only [List.drop_zero] at invariant_2
    rw [← hc, invariant_2]
    (unfold parityOdd;
     have hle := trueCount_le_length children;
     by_cases hlen : children.length > 2 <;>
       simp only [hlen, if_true, if_false] <;>
       first
         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
                trueCount children = 2 := by omega;
            rcases hb with h | h | h <;> rw [h] <;> decide)
         | (by_cases hpar : trueCount children % 2 = 1 <;>
              [ (have hpos : 0 < trueCount children := by omega;
                 simp [hpar, hpos]) ; simp [hpar] ]))
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit of django__django-16901 (velvet). VERDICT: SOUND (advisory). Base-commit worktree at $D/wt (ee36e101e8, git worktree from the upstream repository).

WHY THIS PASS EXISTS / WHAT CHANGED vs THE PRIOR PASS. meta.json records G-EQ=fail with machine verdict "INCONCLUSIVE - 4 attack(s) inconclusive", and verdict.md shows the cause explicitly: attacks 5, 6, 8 and 9 (atk_04_uncond_mod_no_or, atk_05_not_even, atk_07_runtime_guard, atk_08_natsub) each returned "no report ... harness error or image pull failure ... (no attempt completed in 3 tries)" with "Instances with errors: 1". The prior agent's SOUND claim rested on 6 completed runs while 4 needed runs never completed, so its evidence was genuinely incomplete. ALL 7 of my resolve runs completed (completed=True), 0 inconclusive.

SAME-SPEC. All 11 attacks + the positive control are byte-identical in spec regions; swebench_unified.markers.same_spec(gold, cand, velvet) printed True for all 12. Every file was produced by copying Solution.lean and editing ONLY the impl region (+ the prove_correct closer, which is elided from the spec view).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run 4-concurrent in background batches):
- pos_control.lean -> rc=0. POSITIVE CONTROL: the bundle's own impl verifies, so the harness is live and rejections below are real discrimination, not a broken toolchain.
- atk_00_prepatch.lean -> rc=1 REJECTED. PREPATCH BUG REPRODUCED: bare tally `(0<count) && (count = 1)` (the pre-patch "exactly-one" semantics, no Mod wrap). G-DIFF confirmed.
- atk_07_boundary_gt3.lean -> rc=1 REJECTED (BOUNDARY: threshold off-by-one `> 3`; wrong at arity 3 with 3 operands true).
- atk_09_partial_empty.lean -> rc=1 REJECTED (PARTIAL DOMAIN: empty operand list answered `true`, but parityOdd [] = false).
- atk_10_early_exit.lean -> rc=1 REJECTED (CONTROL-FLOW EFFECT: loop guard `i > 0 && count < 2` abandons the tally at 2, mis-classifying rows with >=3 true operands; loom could not even re-establish `i = 0` on exit).
- VERIFY rc=0 (spec ACCEPTED) for 7: atk_01_uncond_mod, atk_02_no_or, atk_03_uncond_mod_no_or, atk_04_not_even, atk_05_shift, atk_06_runtime_guard, atk_08_oracle_echo.

HONESTY ON MY OWN TACTIC ERRORS (I did NOT count these as spec discrimination). atk_03/04/05 and atk_08 FIRST exited rc=1, but the residual goals were plainly MY plumbing, not the spec rejecting a wrong value -- e.g. atk_03's leftover goal was literally `decide (trueCount children % 2 = 1) = decide (trueCount children % 2 = 1)` (closed by `rfl`), and atk_04's was `0 < trueCount children` under `h : trueCount children % 2 = 1` (closed by omega). All four impls are extensionally EQUAL to parityOdd, so a rejection there would have been a false negative. I rebuilt each closer until it verified, and only THEN did they count as attacks and get resolved. Symmetrically, atk_06's first faithful patch CRASHED (FieldError: mixed FloatField/IntegerField from Mod's inferred output_field) -- a crashing patch proves nothing, so I fixed it with explicit output_field=IntegerField() and re-triaged to green BEFORE resolving.

Each returned resolved=True completed=True note='resolved', with F2P test_filter_multiple in 'success', F2P failure=[], and P2P failure=[]:
atk_01_uncond_mod, atk_02_no_or, atk_03_uncond_mod_no_or, atk_04_not_even, atk_05_shift, atk_06_runtime_guard, atk_08_oracle_echo.
Per-run JSON in $D/resolve/<name>.json; patches in $D/patches/<name>.diff. NO verifying attack's faithful patch failed to resolve => no verify=>correct break.

DISTINCTNESS GUARD (so no 'resolved' is an artifact of an accidentally gold-identical code path). I rendered each tree's actual SQL at arities 2/3/5 and diffed against the gold tree: atk_02, atk_03, atk_04, atk_05, atk_06 differ from gold at ALL THREE arities; atk_08 differs at 3 and 5; atk_01 differs at 2. So every attack genuinely exercises a different code path, including impls that emit NO OR conjunct at all (atk_02/03 render `WHERE 1 = (MOD(...))`), a NOT-wrapped evenness test (atk_04), a shifted modulus MOD(sum+1,2)=0 (atk_05), a CASE over the RUNTIME tally rather than the static arity (atk_06), and a fully RESTRUCTURED recursive nested-binary-XOR rewrite (atk_08).

WHY NO BREAK EXISTS (structural, not luck). `ensures out = parityOdd children` is a total functional equality with no precondition and no existential slack, over a carrier (List Bool) that is exactly the rewrite's observable content. Verification therefore pins the row-membership boolean pointwise on ALL inputs including []. Any faithful refinement of a verifying impl computes the same predicate as gold, hence selects the same rows, hence passes the same tests. The attack surface is model->patch correspondence, not spec weakness.

A-LEG AUDIT (my assigned focus). The A legs are VACUOUS BY CONSTRUCTION, confirmed four independent ways: (1) meta.json axioms=[] and deep_model_references=[]; (2) the axioms region is comment-only; (3) grep finds no `axiom`, `sorry`, `admit`, `opaque`, `native_decide`, `@[implemented_by]` or `extern` anywhere in Solution.lean; (4) axiom_check.py itself prints "G-AX status=skip ... no axioms and no deep-model A-references". So there is no axiom-soundness trust point, and no A-consumed/A-reference leg whose correspondence to a real callee could be false. The refinement.md leg table is accurate: 6 legs (A1..A6) tagged R, I, I, R, R, R+I -- every leg is R or I, NO kind-3 (inexpressible-changed-op) step. The genuinely changed operation (inserting Mod(rhs_sum,2) for arity>2) is modeled DIRECTLY as the `count % 2` branch at leg A3, not hidden behind an axiom, which is the correct treatment. I independently confirmed the branch guard claim: connection.features.supports_logical_xor is False on SQLite, so the modeled branch really is the one taken.

INDEPENDENT CORROBORATION I RE-RAN MYSELF. (a) G-CONF: conformance_check.py against the gold tree printed "G-CONF OK: R/I shadow of oddParityReduce agrees with patch.diff behaviour (real patched XOR rewrite over SQLite) on 100096 (query,row) inputs (seed=16901), 0 disagreements" -- so the value-level bijection of mapping.md §2 holds end-to-end, not just on paper. (b) patch.diff at the bundle ROOT is byte-identical to the frozen dataset's gold patch (verbatim: True) and touches only django/db/models/sql/where.py, matching meta.json changed_files. Note this corrects a prior pass's out-of-gate observation that patch.diff was ABSENT: it is present at the instance root (../patch.diff), not inside velvet/. (c) I re-ran the full F2P + all 6 P2P assertions locally on all 8 trees (gold + 7 attacks); every one passed, consistent with the harness verdicts.

NULL / THREE-VALUED-LOGIC PROBE (an axis no prior pass tested, and the one place a List Bool carrier could be too coarse). SQL operands can evaluate to NULL, which List Bool cannot represent; if the gold and attack rewrites disagreed under NULL the carrier would be unfaithful. I built a nullable two-column model and compared selected rows at arities 2 and 3 across gold and 5 structurally distinct attacks: every tree returned IDENTICAL row sets (2ary [2,3]; 3ary [3,4,5]). The CASE WHEN c THEN 1 ELSE 0 indicator collapses NULL to 0 uniformly, so the Bool abstraction is sound here. No finding.

RESIDUAL (documentation-only, NOT a soundness defect, flagged for the orchestrator). refinement.md line 47 attributes the final collapse to "lemma `reduce_eq_parity`", but NO such lemma exists in Solution.lean -- grep finds it only in refinement.md. The pure region actually provides trueCount_nil, trueCount_cons, trueCount_le_length and trueCount_drop_step, and the collapse is performed inline in the prove_correct closer (the by_cases on children.length > 2 plus the bounded 0/1/2 case split). The mathematical argument the sentence describes is exactly what the closer does and it machine-checks, so refinement fidelity is unaffected; the lemma NAME is simply stale/aspirational. Recommend correcting the citation to point at the inline closer.

GATE-CRITICAL CAVEAT ON RE-RUN. My SOUND verdict is contingent on the runner's 7 resolve runs COMPLETING. Pre-pulling the instance image and bounding concurrency is what made 7/7 complete for me.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_01_uncond_mod.lean`, `atk_02_no_or.lean`, `atk_03_uncond_mod_no_or.lean`, `atk_04_not_even.lean`, `atk_05_shift.lean`, `atk_06_runtime_guard.lean`, `atk_08_oracle_echo.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_00_prepatch.lean`, `atk_07_boundary_gt3.lean`, `atk_09_partial_empty.lean`, `atk_10_early_exit.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No verifying same-spec impl whose faithful refined patch fails to resolve. All 7 verifying attacks were materialized as faithful patches and ALL 7 completed the official harness with resolved=True (0 inconclusive). Root cause is structural, not luck: the postcondition `ensures out = parityOdd children` is a TOTAL FUNCTIONAL equality with NO precondition and no existential slack, so every verifying same-spec impl is extensionally EQUAL to parityOdd = decide (trueCount xs % 2 = 1). Verification therefore pins the modeled row-level membership boolean EXACTLY (pointwise on all of List Bool, including []), leaving no room for a semantic wedge. The A-legs, which I was asked to concentrate on, are vacuous BY CONSTRUCTION: meta.json axioms=[] and deep_model_references=[], the axioms region is comment-only, and Solution.lean contains no `axiom`/`sorry`/`opaque`/`native_decide`/`implemented_by` escape hatch -- so there is no axiom-soundness trust point to attack at all.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_00_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_01_uncond_mod.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_02_no_or.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_03_uncond_mod_no_or.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_04_not_even.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_05_shift.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_06_runtime_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_07_boundary_gt3.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_08_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_09_partial_empty.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_early_exit.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (none: this bundle has no axiomatized callees — the modeled operation is a
--  pure boolean/arithmetic reduction over already-evaluated operand truth
--  values; see mapping.md §3 and refinement.md §C.)
-- axioms-end

-- pure-start
/- The number of operands that hold for one row: the running tally of the
   per-operand 1/0 indicators. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern). -/
def trueCount : List Bool → Nat
  | []      => 0
  | c :: cs => (if c then 1 else 0) + trueCount cs

@[grind] lemma trueCount_nil : trueCount [] = 0 := rfl
@[grind] lemma trueCount_cons (c : Bool) (cs : List Bool) :
    trueCount (c :: cs) = (if c then 1 else 0) + trueCount cs := rfl

/- The chained exclusive-or of a row's operands: true exactly when an odd number
   of them hold. This is the value the combined predicate must compute. -/
def parityOdd (xs : List Bool) : Bool := decide (trueCount xs % 2 = 1)

/- At most as many operands hold as there are operands. -/
lemma trueCount_le_length : ∀ xs : List Bool, trueCount xs ≤ xs.length
  | []      => by simp [trueCount]
  | c :: cs => by
      have ih := trueCount_le_length cs
      simp only [trueCount, List.length_cons]
      split <;> omega

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `trueCount` peels one indicator. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma trueCount_drop_step (xs : List Bool) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    trueCount (xs.drop (i - 1)) =
      (if xs[i - 1]! then 1 else 0) + trueCount (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, trueCount_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method oddParityReduce (children : List Bool) return (out : Bool)
  ensures out = parityOdd children
  do
    -- impl-start
    let mut count : Nat := 0
    let mut i := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant count = trueCount (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      count := (if c then 1 else 0) + count
      i := i - 1
    return (decide (0 < count)) &&
      decide ((if children.length > 2 then count % 2 else count) = 1)
    -- impl-end

prove_correct oddParityReduce by
  loom_solve
  · rw [trueCount_drop_step children i (by omega) (by omega)]
    rw [‹count = trueCount (children.drop i)›]
  · injection i_3 with hc _
    subst done_1
    simp only [List.drop_zero] at invariant_2
    rw [← hc, invariant_2]
    (unfold parityOdd;
     have hle := trueCount_le_length children;
     by_cases hlen : children.length > 2 <;>
       simp only [hlen, if_true, if_false] <;>
       first
         | (have hb : trueCount children = 0 ∨ trueCount children = 1 ∨
                trueCount children = 2 := by omega;
            rcases hb with h | h | h <;> rw [h] <;> decide)
         | (by_cases hpar : trueCount children % 2 = 1 <;>
              [ (have hpos : 0 < trueCount children := by omega;
                 simp [hpar, hpos]) ; simp [hpar] ]))
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit of django__django-16901 (velvet). VERDICT: SOUND (advisory). Base-commit worktree at $D/wt (ee36e101e8, git worktree from the upstream repository).

WHY THIS PASS EXISTS / WHAT CHANGED vs THE PRIOR PASS. meta.json records G-EQ=fail with machine verdict "INCONCLUSIVE - 4 attack(s) inconclusive", and verdict.md shows the cause explicitly: attacks 5, 6, 8 and 9 (atk_04_uncond_mod_no_or, atk_05_not_even, atk_07_runtime_guard, atk_08_natsub) each returned "no report ... harness error or image pull failure ... (no attempt completed in 3 tries)" with "Instances with errors: 1". The prior agent's SOUND claim rested on 6 completed runs while 4 needed runs never completed, so its evidence was genuinely incomplete. ALL 7 of my resolve runs completed (completed=True), 0 inconclusive.

SAME-SPEC. All 11 attacks + the positive control are byte-identical in spec regions; swebench_unified.markers.same_spec(gold, cand, velvet) printed True for all 12. Every file was produced by copying Solution.lean and editing ONLY the impl region (+ the prove_correct closer, which is elided from the spec view).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run 4-concurrent in background batches):
- pos_control.lean -> rc=0. POSITIVE CONTROL: the bundle's own impl verifies, so the harness is live and rejections below are real discrimination, not a broken toolchain.
- atk_00_prepatch.lean -> rc=1 REJECTED. PREPATCH BUG REPRODUCED: bare tally `(0<count) && (count = 1)` (the pre-patch "exactly-one" semantics, no Mod wrap). G-DIFF confirmed.
- atk_07_boundary_gt3.lean -> rc=1 REJECTED (BOUNDARY: threshold off-by-one `> 3`; wrong at arity 3 with 3 operands true).
- atk_09_partial_empty.lean -> rc=1 REJECTED (PARTIAL DOMAIN: empty operand list answered `true`, but parityOdd [] = false).
- atk_10_early_exit.lean -> rc=1 REJECTED (CONTROL-FLOW EFFECT: loop guard `i > 0 && count < 2` abandons the tally at 2, mis-classifying rows with >=3 true operands; loom could not even re-establish `i = 0` on exit).
- VERIFY rc=0 (spec ACCEPTED) for 7: atk_01_uncond_mod, atk_02_no_or, atk_03_uncond_mod_no_or, atk_04_not_even, atk_05_shift, atk_06_runtime_guard, atk_08_oracle_echo.

HONESTY ON MY OWN TACTIC ERRORS (I did NOT count these as spec discrimination). atk_03/04/05 and atk_08 FIRST exited rc=1, but the residual goals were plainly MY plumbing, not the spec rejecting a wrong value -- e.g. atk_03's leftover goal was literally `decide (trueCount children % 2 = 1) = decide (trueCount children % 2 = 1)` (closed by `rfl`), and atk_04's was `0 < trueCount children` under `h : trueCount children % 2 = 1` (closed by omega). All four impls are extensionally EQUAL to parityOdd, so a rejection there would have been a false negative. I rebuilt each closer until it verified, and only THEN did they count as attacks and get resolved. Symmetrically, atk_06's first faithful patch CRASHED (FieldError: mixed FloatField/IntegerField from Mod's inferred output_field) -- a crashing patch proves nothing, so I fixed it with explicit output_field=IntegerField() and re-triaged to green BEFORE resolving.

Each returned resolved=True completed=True note='resolved', with F2P test_filter_multiple in 'success', F2P failure=[], and P2P failure=[]:
atk_01_uncond_mod, atk_02_no_or, atk_03_uncond_mod_no_or, atk_04_not_even, atk_05_shift, atk_06_runtime_guard, atk_08_oracle_echo.
Per-run JSON in $D/resolve/<name>.json; patches in $D/patches/<name>.diff. NO verifying attack's faithful patch failed to resolve => no verify=>correct break.

DISTINCTNESS GUARD (so no 'resolved' is an artifact of an accidentally gold-identical code path). I rendered each tree's actual SQL at arities 2/3/5 and diffed against the gold tree: atk_02, atk_03, atk_04, atk_05, atk_06 differ from gold at ALL THREE arities; atk_08 differs at 3 and 5; atk_01 differs at 2. So every attack genuinely exercises a different code path, including impls that emit NO OR conjunct at all (atk_02/03 render `WHERE 1 = (MOD(...))`), a NOT-wrapped evenness test (atk_04), a shifted modulus MOD(sum+1,2)=0 (atk_05), a CASE over the RUNTIME tally rather than the static arity (atk_06), and a fully RESTRUCTURED recursive nested-binary-XOR rewrite (atk_08).

WHY NO BREAK EXISTS (structural, not luck). `ensures out = parityOdd children` is a total functional equality with no precondition and no existential slack, over a carrier (List Bool) that is exactly the rewrite's observable content. Verification therefore pins the row-membership boolean pointwise on ALL inputs including []. Any faithful refinement of a verifying impl computes the same predicate as gold, hence selects the same rows, hence passes the same tests. The attack surface is model->patch correspondence, not spec weakness.

A-LEG AUDIT (my assigned focus). The A legs are VACUOUS BY CONSTRUCTION, confirmed four independent ways: (1) meta.json axioms=[] and deep_model_references=[]; (2) the axioms region is comment-only; (3) grep finds no `axiom`, `sorry`, `admit`, `opaque`, `native_decide`, `@[implemented_by]` or `extern` anywhere in Solution.lean; (4) axiom_check.py itself prints "G-AX status=skip ... no axioms and no deep-model A-references". So there is no axiom-soundness trust point, and no A-consumed/A-reference leg whose correspondence to a real callee could be false. The refinement.md leg table is accurate: 6 legs (A1..A6) tagged R, I, I, R, R, R+I -- every leg is R or I, NO kind-3 (inexpressible-changed-op) step. The genuinely changed operation (inserting Mod(rhs_sum,2) for arity>2) is modeled DIRECTLY as the `count % 2` branch at leg A3, not hidden behind an axiom, which is the correct treatment. I independently confirmed the branch guard claim: connection.features.supports_logical_xor is False on SQLite, so the modeled branch really is the one taken.

INDEPENDENT CORROBORATION I RE-RAN MYSELF. (a) G-CONF: conformance_check.py against the gold tree printed "G-CONF OK: R/I shadow of oddParityReduce agrees with patch.diff behaviour (real patched XOR rewrite over SQLite) on 100096 (query,row) inputs (seed=16901), 0 disagreements" -- so the value-level bijection of mapping.md §2 holds end-to-end, not just on paper. (b) patch.diff at the bundle ROOT is byte-identical to the frozen dataset's gold patch (verbatim: True) and touches only django/db/models/sql/where.py, matching meta.json changed_files. Note this corrects a prior pass's out-of-gate observation that patch.diff was ABSENT: it is present at the instance root (../patch.diff), not inside velvet/. (c) I re-ran the full F2P + all 6 P2P assertions locally on all 8 trees (gold + 7 attacks); every one passed, consistent with the harness verdicts.

NULL / THREE-VALUED-LOGIC PROBE (an axis no prior pass tested, and the one place a List Bool carrier could be too coarse). SQL operands can evaluate to NULL, which List Bool cannot represent; if the gold and attack rewrites disagreed under NULL the carrier would be unfaithful. I built a nullable two-column model and compared selected rows at arities 2 and 3 across gold and 5 structurally distinct attacks: every tree returned IDENTICAL row sets (2ary [2,3]; 3ary [3,4,5]). The CASE WHEN c THEN 1 ELSE 0 indicator collapses NULL to 0 uniformly, so the Bool abstraction is sound here. No finding.

RESIDUAL (documentation-only, NOT a soundness defect, flagged for the orchestrator). refinement.md line 47 attributes the final collapse to "lemma `reduce_eq_parity`", but NO such lemma exists in Solution.lean -- grep finds it only in refinement.md. The pure region actually provides trueCount_nil, trueCount_cons, trueCount_le_length and trueCount_drop_step, and the collapse is performed inline in the prove_correct closer (the by_cases on children.length > 2 plus the bounded 0/1/2 case split). The mathematical argument the sentence describes is exactly what the closer does and it machine-checks, so refinement fidelity is unaffected; the lemma NAME is simply stale/aspirational. Recommend correcting the citation to point at the inline closer.

GATE-CRITICAL CAVEAT ON RE-RUN. My SOUND verdict is contingent on the runner's 7 resolve runs COMPLETING. Pre-pulling the instance image and bounding concurrency is what made 7/7 complete for me.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC REGION: byte-identical. swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) == True. Spec view is only 'ensures out = parityOdd children' plus trueCount/parityOdd and three helper lemmas; pre/post-condition regions empty; axioms region empty, consistent with meta.json axioms=[] and deep_model_references=[], so there is no axiom-overreach surface and G-AX is legitimately vacuous.

VERIFIER: scripts/lean_verify.sh Solution.lean exits 0 (clean, no sorry). Solution_prepatch.lean exits 1 ('simp made no progress', line 94), independently confirming the recorded G-DIFF: the spec genuinely rejects the pre-patch exactly-one semantics, so it is a real discriminator rather than a tautology. Gold F2P suite tests/runtests.py xor_lookups passes 6/6 on the patched tree.

STRENGTH SWEEP against the real patched repo (git diff matches instance patch.diff modulo hunk headers), using an oracle I built from scratch rather than reusing conformance_check.py:
  - Arity 1..7 exhaustive over 2^7 rows: 0 divergences; traced SQL confirms MOD(...,2) is emitted exactly when len(children) > 2.
  - Constant-folding operands, Q(pk__in=[]) raising EmptyResultSet and ~Q(pk__in=[]) raising FullResultSet, mixed into arity 2 and 3. This is where compiled arity can diverge from len(self.children), the likeliest place a too-strong totality claim breaks. All shapes matched parityOdd, including F^F^F=ALL, F^F=NONE, F^F^F^F=NONE.
  - NULL 3-valued logic, exhaustive over 3^5=243 ternary rows x 31 column subsets: 0 divergences. CASE WHEN c THEN 1 ELSE 0 maps UNKNOWN to 0, matching the bijection's 'row satisfies c' reading.
  - Negation (self.negated, which mapping.md deliberately omits from the carrier): exhaustive negated x NULL sweep, 2430 pairs, 0 divergences. The omission is sound because negation wraps the whole conjunction identically pre- and post-patch.
  - Negated leaves x NULL: 72 queries / 5832 pairs, 0 divergences after fixing my oracle.
  - Structural fuzz: 300 random XOR queries with plain/negated leaves, AND pairs, OR pairs and nested-XOR operands, 30% outer-negated; 19200 pairs, 0 divergences. Also confirmed XOR flattening ((a^b)^(c^d) collapses to one arity-4 node) so modeled arity tracks real len(self.children).
  - High arity 2..20, where SQLite's MOD is fmod returning a FLOAT while Exact(1, ...) compares against integer 1 - a real drift risk the Nat model would hide: trueCount up to 20, 7638 comparisons, 0 divergences.

JUDGMENT: the modeled function agrees with the real patched callee on every input in the patch's changed behavior, across arity, NULL, negation, constant-folding, nesting and the float-MOD path. The two declared abstractions (omitting self.negated; modeling the row-level boolean rather than the SQL string) are each stated in mapping.md section 2 and I empirically confirmed both are behavior-preserving.

RESIDUAL WEAKNESS, reported honestly rather than as a defect: the spec is total over List Bool with no precondition, so it does claim a value (false) for children = [], an input on which the real function raises. Unlike my first submission I can no longer call that input unreachable - it is reachable through annotate/CheckConstraint/Q.check via Q(Q()). It still does not make the spec UNFAITHFUL, because the behavior is bit-identical at base_commit and therefore outside the patch delta the spec is accountable for. A maximally tight bundle would add a 'children != []' precondition to close the gap; its absence is a minor domain-overreach caveat, not a faithfulness break. No divergence exists on any input the patch changes.

Counterexample / evidence:

```
CORRECTION TO MY OWN EARLIER FINDING - recorded because it changes the facts, not the verdict. I first concluded arity 0 and 1 were unreachable, because Q._combine short-circuits (query_utils.py:55-66: 'if not other and isinstance(other, Q): return self.copy()'), so Q(pk=1)^Q() never builds an XOR node. That was WRONG. Wrapping in a vacuous-but-nonempty Q bypasses the short-circuit: bool(Q(Q())) is True (one child), so repr(Q(Q())^Q(Q())) == '<Q: (XOR: (AND: ), (AND: ))>'. Then sql/query.py:1584-1598 _add_q builds target_clause with connector=XOR BEFORE children exist and silently drops falsy child clauses ('if child_clause: target_clause.add(...)'), so a 2-child XOR Q degrades in place to a 1- or 0-child XOR WhereNode.

VERIFIED BY DIRECT INSTRUMENTATION of WhereNode.as_sql (counting hits on the XOR fallback branch):
  - arity 1 reaches the branch from plain filter/exclude when the node is negated, because tree.Node.add's squash guard requires 'not data.negated' (utils/tree.py:106-117): filter(~(Q(c0=1)^Q(Q()))) hits (children=1, negated=True).
  - arity 1 also reaches it via the expression path regardless of negation: annotate(x=Q(pk=1)^Q(Q())) hits (1, False). Q.resolve_expression calls _add_q and returns the clause straight to the expression tree, bypassing add_q's 'if clause:' guard.
  - arity 0 reaches it via the expression path and CRASHES: annotate(x=Q(Q())^Q(Q())) and (Q(Q())^Q(Q())).check({'x':1}) both hit (0, False) then raise TypeError.
  - arity 0 does NOT reach it from filter/exclude: sql/query.py:1554 'if clause:' prunes it. filter(Q(Q())^Q(Q())) hits 0 times.

WHY THE VERDICT STILL HOLDS. (a) Arity 1 AGREES with the spec, so the reachability correction costs nothing there. I checked the reachable arity-1 shapes against parityOdd over all 8 rows: filter(~(Q(c0=1)^Q(Q()))) -> [0,2,4,6] == expected; filter(~(Q(c0=1)^Q(Q())^Q(Q()))) -> [0,2,4,6] == expected; exclude(~(Q(c0=1)^Q(Q()))) -> [1,3,5,7] == expected. All OK. The 'len > 2' guard is what keeps arity 1 correct: it renders 'a == 1', i.e. plain a, the true 1-ary XOR. (b) Arity 0 raises the SAME TypeError at base_commit: I re-ran the identical probe against and got hits=[(0, False)] -> TypeError, and base where.py:133-137 has the same unguarded reduce(). Per the audit rule that base_commit is the reference for what the patch does not touch, this is an unchanged pre-existing crash; reporting it as UNFAITHFUL would condemn a correct spec for a bug the patch neither introduced nor was meant to fix. (c) I also confirmed the arity-2-with-vacuous-child shape (QuerySet.__xor__, where sql/query.py:695-697 adds the rhs where unconditionally so arity stays 2): R.objects.all() ^ R.objects.filter(c0=1) hits (2, False) and returns [0,2,4,6], matching parityOdd [True, c0].

A second false lead, also mine: an apparent divergence at negated leaves over NULL (cols=(0,1) signs=(0,1) row=(0,None,..) model=False real=True) was my oracle bug, not the spec's. ~Q(c1=1) renders NOT (c1=1 AND c1 IS NOT NULL), which is TRUE for NULL. With the corrected predicate (r[c] != 1) the sweep returned 0 divergences over 5832 (query,row) pairs.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. Gate is the consumer-visible spec view only. Confirmed via src/swebench_unified/eval/{dataset,prompts,adapter}.py that what reaches the agent in modes 1/2 is exactly: spec_view(Solution.lean), modeled_functions, problem_statement (+ localization). refinement.md, mapping.md, patch.diff, verdict.md, meta.json and Solution_prepatch.lean are NEVER in the agent prompt or as_dict() -- grep of eval/ shows no reads of those prose files. adapter.spec_view() additionally fails closed if impl or prove_correct bodies survive elision.

SPEC REGION BYTE-IDENTICAL (as instructed). markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True; spec_signature bytes equal (empty difflib diff); spec_view is idempotent. The known-buggy witness therefore differs from gold ONLY inside the elided impl/proof -- no contract was weakened or strengthened to encode the fix.

WHAT THE SPEC VIEW SAYS. The projection is 69 lines: the `trueCount` tally, `parityOdd xs := decide (trueCount xs % 2 = 1)`, two bound/fold lemmas, and `method oddParityReduce (children : List Bool) return (out : Bool) ensures out = parityOdd children`, with impl and prove_correct body stubbed.

THE ONLY LINES WORTH CHALLENGING, and why each clears.
- L29 `parityOdd (xs) := decide (trueCount xs % 2 = 1)` and L62 `ensures out = parityOdd children`. These state odd parity as the intended semantics. But the public problem_statement already states it verbatim: "the correct interpretation ... is that a ^ b ^ c is true when an odd number of the arguments are true", and hands over the expected counts (1, 0, 1, 0, 1) for arities 1..5, which pins odd parity pointwise. A spec is *required* to state intended behaviour; restating the issue's own sentence is not leakage. Note this is the public issue text, not hints_text (hints_text for this instance is empty anyway).
- L27 comment "true exactly when an odd number of them hold" -- same public sentence, prose form.
- `% 2` at L29 is arithmetic in the DEFINITION OF PARITY, not the gold patch's `Mod(rhs_sum, 2)` call site. It carries no arity condition, no SQL construction, no import.

WHAT IS ABSENT -- the actual gold content. Regex sweep over the spec view: zero occurrences of `Mod`, `> 2`, `len(`, `django`, `where.py`, `reduce`, `Case`, `When`, `Exact`, `XOR`/`xor`, `SQL`/`sql`, `patch`, `gold`, `fix`, `copy`. The three things a reconstructor would need -- the `from django.db.models.functions import Mod` import, the `if len(self.children) > 2:` guard, and the placement inside the OR/AND rewrite -- appear in mapping.md L42 and refinement.md L25-26/A3, both of which are audit-side documents outside the spec view. Also clean on the G-LEAK vocabulary that trips on prose alone (no "fixed"/"copy" in the retained comments).

MODELING DIRECTION. The spec is stated at the row-membership level over `List Bool`, deliberately one abstraction above the patch: it says WHICH ROWS must match, not HOW to build the WHERE clause. An agent given only this still has to discover that the fallback branch exists, that it lives in WhereNode.as_sql, that the tally must be mod-reduced, and (per the counterexample, need not but may) that the reduction can be guarded on arity. That is the intended difficulty of mode 1/2, preserved.

RESIDUAL, disclosed not charged. modeled_functions ships repo_location `django/db/models/sql/where.py:128`, which the problem_statement does not name. That is the EDIT LOCALIZATION aid, granted by construction to mode 0 as well (prompts.py `_localization_block` / `_MULTISITE_LOC`), so it is an information-environment-parity control, not a spec artifact -- and a file:line is not the gold edit: the base_commit `where.py:128` region shown above the fix is the unpatched `(a + b + c + ...) == 1` comment, which reveals the BUG, not the repair.

ENVIRONMENT. Gold Solution.lean re-verified EXIT=0 as a control. Scratch under mktemp -d per the /tmp-reaping rule; I copied the base worktree rather than mutating the shared, and confirmed that tree is still Mod-free so no other attacker's state was disturbed. No git stash, no tree-wide git ops. No verifier timeouts or agent-cap failures, so no INCONCLUSIVE-as-defect risk in this judgement.

MINOR, non-blocking: the task prompt lists patch.diff as a bundle file but the bundle directory has no patch.diff (it has Solution_prepatch.lean, meta.json, verdict.md, properties.py, conformance_check.py, axiom_check.py). Gold hunk text was taken from data/swe_bench_verified/test.jsonl instead. This does not affect the leakage judgement, which is a property of the spec view.

Counterexample / evidence:

```
Non-gold rival admitted by the SAME spec view (byte-identical projection), proving the spec does not reconstruct the gold edit's shape. Rival impl region returns `decide (count % 2 = 1)` UNCONDITIONALLY (no `children.length > 2` arity guard), i.e. it drops refinement.md step A3 entirely. Results: (a) spec_view sha256 = d34cff88abd127da for gold, Solution_prepatch.lean AND rival -- all three identical; markers.same_spec(gold, rival) = True; (b) scripts/lean_verify.sh Rival.lean -> EXIT=0, no sorry/admit; (c) the corresponding repo edit (unconditional `rhs_sum = Mod(rhs_sum, 2)` inserted before `rhs = Exact(1, rhs_sum)`, WITHOUT the `if len(self.children) > 2:` guard) applied to the base_commit worktree passes the full F2P suite: `runtests.py --settings=test_sqlite xor_lookups` -> Ran 7 tests, OK, including the added test_filter_multiple 5-ary witness. So the gold hunk's distinguishing feature -- the arity guard -- is neither stated nor recoverable from the spec view.
```

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
