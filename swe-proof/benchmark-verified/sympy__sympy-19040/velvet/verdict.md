# P2 adversarial audit — sympy__sympy-19040

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk2_boundary_ge1.lean`, `atk3_no_const_guard.lean`, `atk6_maindeg_for_const.lean`, `atk7_fallback_images.lean`, `atk9_always_lone.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk4_maindeg_gate.lean`, `atk5_oracle_echo.lean`, `atk8_norep_gate.lean`, `atk10_drop_sqfpart.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying wrong impl's faithful refined patch failed to resolve. The four attacks that VERIFY (atk4 main-degree gate, atk5 ungrounded-oracle echo, atk8 no-repeated-factor gate, atk10 dropped-sqf_part / lone-materialisation gap) each had their faithful refined patch materialised and RUN through the official harness (swebench_unified.harness.run_resolve), and all four RESOLVED with FAIL_TO_PASS test_issue_5786 passing and 148/148 PASS_TO_PASS. The two domain-gate attacks (atk4/atk8) are dead branches on every argument the graded tests actually drive: I instrumented the real dmp_ext_factor over the whole graded module and all 5 multivariate calls satisfy BOTH require halves, so gating on them cannot change observable behaviour. atk5's echo of `expectedFactors poly` is not a leak because factorList/lone are uninterpreted, so materialising it forces the genuine recovery pipeline applied to the ORIGINAL polynomial - i.e. the gold edit. atk10 exploits a real abstraction gap (gold's fallback [dmp_sqf_part(f)] vs [F] both refine to the single opaque `lone poly`), but the fallback branch is unreachable on the graded corpus (measured len(norm factors)=2 on all 5 calls), so it resolves too.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,15 +145,18 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
-    let _other := otherPoly poly
+    -- PRE-PATCH BUG: the recovery is applied to the RELATED polynomial
+    -- `otherPoly poly` (the square-free part, `dmp_sqf_norm(f, …)`), NOT the
+    -- original `F`. `otherPoly`'s contract promises nothing about its factor
+    -- content, so the materialised list is `factorList (otherPoly poly)`, which
+    -- the proof cannot equate to the required `factorList poly` — the
+    -- completeness clause fails (G-DIFF).
+    let other := otherPoly poly
     if isConstant poly then
       -- constant argument: reported with no factors at all (`return lc, []`).
       return ([] : List Int)
     else
-      let images := factorList poly
+      let images := factorList other
       let mut result : List Int := []
       if images.length ≥ 2 then
         -- two or more elements: the complete factor list of the input.
@@ -195,7 +198,13 @@
 
 prove_correct extFactor by
   loom_solve
+  -- The loop-body fold steps close, but the postcondition goals
+  --   `out = factorList poly` / `out = expectedFactors poly`
+  -- are UNPROVABLE: the impl materialises `factorList (otherPoly poly)`, and
+  -- `otherPoly`'s contract relates nothing to `poly`'s factor content, so the
+  -- completeness clause cannot be discharged. This is the intended G-DIFF
+  -- failure (the dropped-factor bug).
   all_goals
-    first
-      | (rw [drop_step (factorList poly) i (by omega) (by omega)]; simp_all)
-      | (rw [drop_step (lone poly) i (by omega) (by omega)]; simp_all)
+    try (first
+      | (rw [drop_step (factorList (otherPoly poly)) i (by omega) (by omega)]; simp_all)
+      | (rw [drop_step (lone poly) i (by omega) (by omega)]; simp_all))
```

Attack 2 — `atk2_boundary_ge1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,18 +145,13 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
     let _other := otherPoly poly
     if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
       return ([] : List Int)
     else
       let images := factorList poly
       let mut result : List Int := []
-      if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
+      if images.length ≥ 1 then
         let mut i := images.length
         while i > 0
           invariant 0 ≤ i ∧ i ≤ images.length
@@ -167,7 +162,6 @@
           result := images[i - 1]! :: result
           i := i - 1
       else
-        -- single element: the one-element fallback `lone poly`.
         let blob := lone poly
         let mut i := blob.length
         while i > 0
```

Attack 3 — `atk3_no_const_guard.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,18 +145,10 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
     let _other := otherPoly poly
-    if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
-      return ([] : List Int)
-    else
-      let images := factorList poly
+    let images := factorList poly
       let mut result : List Int := []
       if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
         let mut i := images.length
         while i > 0
           invariant 0 ≤ i ∧ i ≤ images.length
@@ -167,7 +159,6 @@
           result := images[i - 1]! :: result
           i := i - 1
       else
-        -- single element: the one-element fallback `lone poly`.
         let blob := lone poly
         let mut i := blob.length
         while i > 0
```

Attack 4 — `atk4_maindeg_gate.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,18 +145,15 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
     let _other := otherPoly poly
     if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
+      return ([] : List Int)
+    else if ! hasMainDegree poly then
       return ([] : List Int)
     else
       let images := factorList poly
       let mut result : List Int := []
       if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
         let mut i := images.length
         while i > 0
           invariant 0 ≤ i ∧ i ≤ images.length
@@ -167,7 +164,6 @@
           result := images[i - 1]! :: result
           i := i - 1
       else
-        -- single element: the one-element fallback `lone poly`.
         let blob := lone poly
         let mut i := blob.length
         while i > 0
```

Attack 5 — `atk5_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,40 +145,7 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
-    let _other := otherPoly poly
-    if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
-      return ([] : List Int)
-    else
-      let images := factorList poly
-      let mut result : List Int := []
-      if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
-        let mut i := images.length
-        while i > 0
-          invariant 0 ≤ i ∧ i ≤ images.length
-          invariant result = images.drop i
-          done_with i = 0
-          decreasing i
-        do
-          result := images[i - 1]! :: result
-          i := i - 1
-      else
-        -- single element: the one-element fallback `lone poly`.
-        let blob := lone poly
-        let mut i := blob.length
-        while i > 0
-          invariant 0 ≤ i ∧ i ≤ blob.length
-          invariant result = blob.drop i
-          done_with i = 0
-          decreasing i
-        do
-          result := blob[i - 1]! :: result
-          i := i - 1
-      return result
+    return expectedFactors poly
     -- impl-end
 end
 
@@ -195,7 +162,3 @@
 
 prove_correct extFactor by
   loom_solve
-  all_goals
-    first
-      | (rw [drop_step (factorList poly) i (by omega) (by omega)]; simp_all)
-      | (rw [drop_step (lone poly) i (by omega) (by omega)]; simp_all)
```

Attack 6 — `atk6_maindeg_for_const.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,18 +145,13 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
     let _other := otherPoly poly
-    if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
+    if ! hasMainDegree poly then
       return ([] : List Int)
     else
       let images := factorList poly
       let mut result : List Int := []
       if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
         let mut i := images.length
         while i > 0
           invariant 0 ≤ i ∧ i ≤ images.length
@@ -167,7 +162,6 @@
           result := images[i - 1]! :: result
           i := i - 1
       else
-        -- single element: the one-element fallback `lone poly`.
         let blob := lone poly
         let mut i := blob.length
         while i > 0
```

Attack 7 — `atk7_fallback_images.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,39 +145,21 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
     let _other := otherPoly poly
     if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
       return ([] : List Int)
     else
       let images := factorList poly
       let mut result : List Int := []
-      if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
-        let mut i := images.length
-        while i > 0
-          invariant 0 ≤ i ∧ i ≤ images.length
-          invariant result = images.drop i
-          done_with i = 0
-          decreasing i
-        do
-          result := images[i - 1]! :: result
-          i := i - 1
-      else
-        -- single element: the one-element fallback `lone poly`.
-        let blob := lone poly
-        let mut i := blob.length
-        while i > 0
-          invariant 0 ≤ i ∧ i ≤ blob.length
-          invariant result = blob.drop i
-          done_with i = 0
-          decreasing i
-        do
-          result := blob[i - 1]! :: result
-          i := i - 1
+      let mut i := images.length
+      while i > 0
+        invariant 0 ≤ i ∧ i ≤ images.length
+        invariant result = images.drop i
+        done_with i = 0
+        decreasing i
+      do
+        result := images[i - 1]! :: result
+        i := i - 1
       return result
     -- impl-end
 end
```

Attack 8 — `atk8_norep_gate.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,18 +145,15 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
     let _other := otherPoly poly
-    if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
+    if ! noRepeatedFactor poly then
+      return ([] : List Int)
+    else if isConstant poly then
       return ([] : List Int)
     else
       let images := factorList poly
       let mut result : List Int := []
       if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
         let mut i := images.length
         while i > 0
           invariant 0 ≤ i ∧ i ≤ images.length
@@ -167,7 +164,6 @@
           result := images[i - 1]! :: result
           i := i - 1
       else
-        -- single element: the one-element fallback `lone poly`.
         let blob := lone poly
         let mut i := blob.length
         while i > 0
```

Attack 9 — `atk9_always_lone.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,39 +145,21 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
     let _other := otherPoly poly
     if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
       return ([] : List Int)
     else
-      let images := factorList poly
+      let blob := lone poly
       let mut result : List Int := []
-      if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
-        let mut i := images.length
-        while i > 0
-          invariant 0 ≤ i ∧ i ≤ images.length
-          invariant result = images.drop i
-          done_with i = 0
-          decreasing i
-        do
-          result := images[i - 1]! :: result
-          i := i - 1
-      else
-        -- single element: the one-element fallback `lone poly`.
-        let blob := lone poly
-        let mut i := blob.length
-        while i > 0
-          invariant 0 ≤ i ∧ i ≤ blob.length
-          invariant result = blob.drop i
-          done_with i = 0
-          decreasing i
-        do
-          result := blob[i - 1]! :: result
-          i := i - 1
+      let mut i := blob.length
+      while i > 0
+        invariant 0 ≤ i ∧ i ≤ blob.length
+        invariant result = blob.drop i
+        done_with i = 0
+        decreasing i
+      do
+        result := blob[i - 1]! :: result
+        i := i - 1
       return result
     -- impl-end
 end
```

Attack 10 — `atk10_drop_sqfpart.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,18 +145,16 @@
   -- post-conditions-end
   do
     -- impl-start
-    -- GOLD: the recovery is applied to the ORIGINAL polynomial, so it reads back
-    -- the input's own complete factor list (`dmp_sqf_norm(F, …)`). `otherPoly`
-    -- (the square-free part) is computed but NOT fed to the factoring.
-    let _other := otherPoly poly
+    -- ATTACK 10: the `otherPoly` (sqf_part) binding is DROPPED entirely. The
+    -- model cannot tell gold's fallback `[dmp_sqf_part(f)]` from `[F]`, since
+    -- both refine to the single opaque `lone poly`. Probes the step-3 / step-5
+    -- A-legs: is `require noRepeatedFactor` load-bearing for that abstraction?
     if isConstant poly then
-      -- constant argument: reported with no factors at all (`return lc, []`).
       return ([] : List Int)
     else
       let images := factorList poly
       let mut result : List Int := []
       if images.length ≥ 2 then
-        -- two or more elements: the complete factor list of the input.
         let mut i := images.length
         while i > 0
           invariant 0 ≤ i ∧ i ≤ images.length
@@ -167,7 +165,6 @@
           result := images[i - 1]! :: result
           i := i - 1
       else
-        -- single element: the one-element fallback `lone poly`.
         let blob := lone poly
         let mut i := blob.length
         while i > 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL EXECUTED IN  ONLY.** Own base_commit worktree: repo/ (b9179e80d2daa1bb6cba1ffe35ca9e6612e115c9, from the upstream repository); gold+test_patch tree: repo_gold/.

**SAME-SPEC:** all 10 attack files + positive control -> same_spec True (swebench_unified.markers.same_spec, velvet backend). Only the impl region was edited; axioms/pure/pre/post byte-identical. Note spec_view elides BOTH impl and proof, so atk5's shortened prove_correct is still same-spec.

**POSITIVE CONTROL:** `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT 0 (verifies, no sorry).
PREPATCH REPRODUCED: `... atk_prepatch.lean 300` -> EXIT 1, unsolved goals exactly on the completeness clauses (ensures_1/2/4: out = expectedFactors poly, out = factorList poly, out = lone poly), constant clause ensures_3 and the loop folds close. Matches refinement.md's G-DIFF claim.

### ATTACK RESULTS (lean_verify.sh, run 4-concurrent as instructed):
  REJECTED (exit 1) - 5 distinct wrong impls:
   atk2_boundary_ge1 (BOUNDARY: branch on length>=1 not >=2)
   atk3_no_const_guard (PARTIAL-DOMAIN: constant early-return removed)
   atk6_maindeg_for_const (CONTROL-FLOW: main-degree test substituted for the constant test)
   atk7_fallback_images (fallback returns the short factorList instead of lone poly)
   atk9_always_lone (unconditionally returns lone poly on non-constant input)
  VERIFIED (exit 0) - 4, each patch materialised + resolved:
   atk4_maindeg_gate  -> atk4.diff  -> run_resolve: resolved=True completed=True, F2P success=['test_issue_5786'] failure=[]
   atk5_oracle_echo   -> atk5.diff  -> run_resolve: resolved=True completed=True, F2P success=['test_issue_5786'] failure=[]
   atk8_norep_gate    -> atk8.diff  -> run_resolve: resolved=True completed=True (note: 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' - harness's own retry, F2P success=['test_issue_5786'] failure=[])
   atk10_drop_sqfpart -> atk10.diff -> run_resolve: resolved=True completed=True, F2P success=['test_issue_5786'] failure=[]
  Commands: `python resolve_one.py <name> <diff>` calling swebench_unified.harness.run_resolve('sympy__sympy-19040', patch); launched as detached background jobs (a first launch produced no result and was relaunched). All 4 diffs `git apply --check`-clean in a PRISTINE base_commit worktree (verify_apply/). All 4 also pre-screened locally: 150 passed on the graded module.

### A-LEG AUDIT (the assigned focus; R/I left to G-CONF):
 1. Domain legs 2a/2b re-measured on the real PATCHED callee, forced onto the MULTIVARIATE path with explicit gens=(x,y) in a forked child SIGKILLed at 25s. My first probe used bare exprs and fell into dup_ext_factor (u=0), making `y-1` look like it returned; with gens forced: y-1 HUNG, `y**2`+1 HUNG, y*(y-1) HUNG, (x-1)**2*(y-1) HUNG, while in-domain (x-1)*(y-1) RETURNED and (x-1)*(y-1)**2 RETURNED. So BOTH require halves are genuinely necessary (each traceable to its own unbounded loop) and neither is decoration - an unconditional termination claim would be unsound. Caveat: refinement.md §9 cites y*(y-1) and (x-1)*(y-1)**2 as CONSERVATIVE witnesses; on the multivariate path y*(y-1) HANGS rather than returning, so that one conservativeness witness does not reproduce as described. This does not weaken the gate (it makes the guard more necessary, not less) but the prose overstates it.
 2. Row 3 (otherPoly / dmp_sqf_part) confirmed genuinely factor-losing: dmp_sqf_part((x-1)^2(y-1)) = x-1, i.e. the y-1 factor is destroyed - so the weakest-contract axiom is right and no stronger one is admissible.
 3. Row 4/5 correspondence: instrumented the gold-patched pipeline over the whole graded module. On all 5 multivariate calls len(dmp_factor_list_include(r,...))=2 and len(dmp_trial_division(F,...))=2, so the model's branch predicate ((factorList poly).length>=2) and the real one (len(factors)==1) AGREE on every graded call; no divergence.
 4. Every table leg is R / A-consumed / A-reference / I - no kind-3. The changed operation (which polynomial the recovery is applied to) lives in the IMPL as the argument of factorList (poly vs otherPoly poly), not inside an axiom, so no axiom hides the edit. No dead axiom: factorList+lone(+loneLen) are consumed by completeness, otherPoly's weak contract is what refutes the prepatch, isConstant drives the empty clause, and both domain Booleans are load-bearing per (1).

RESIDUAL RISK (advisory, not a break): the spec's discrimination rests on the impl-level argument choice; because the two shape-test axioms are unrelated to factorList, an impl may add dead domain gates (atk4/atk8) or exploit the lone-materialisation gap (atk10) and still verify. All three still resolve because the graded corpus is entirely in-domain and never exercises the length-1 fallback, so verify=>resolved holds on this instance's oracle - but the margin is thin and rests on corpus coverage rather than on the contract, which is worth noting for any future tightening.

**VERDICT:** SOUND. 10 same-spec attacks encoded and verified (>=5 required, 5 distinct rejections + 4 verifying ones fully resolved + prepatch), positive control verifies, prepatch reproduced, and every verifying wrong impl's faithful patch RESOLVED under the official harness - no verify=>correct counterexample found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk2_boundary_ge1.lean`, `atk3_no_const_guard.lean`, `atk6_maindeg_for_const.lean`, `atk7_fallback_images.lean`, `atk9_always_lone.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk4_maindeg_gate.lean`, `atk5_oracle_echo.lean`, `atk8_norep_gate.lean`, `atk10_drop_sqfpart.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No verifying wrong impl's faithful refined patch failed to resolve. The four attacks that VERIFY (atk4 main-degree gate, atk5 ungrounded-oracle echo, atk8 no-repeated-factor gate, atk10 dropped-sqf_part / lone-materialisation gap) each had their faithful refined patch materialised and RUN through the official harness (swebench_unified.harness.run_resolve), and all four RESOLVED with FAIL_TO_PASS test_issue_5786 passing and 148/148 PASS_TO_PASS. The two domain-gate attacks (atk4/atk8) are dead branches on every argument the graded tests actually drive: I instrumented the real dmp_ext_factor over the whole graded module and all 5 multivariate calls satisfy BOTH require halves, so gating on them cannot change observable behaviour. atk5's echo of `expectedFactors poly` is not a leak because factorList/lone are uninterpreted, so materialising it forces the genuine recovery pipeline applied to the ORIGINAL polynomial - i.e. the gold edit. atk10 exploits a real abstraction gap (gold's fallback [dmp_sqf_part(f)] vs [F] both refine to the single opaque `lone poly`), but the fallback branch is unreachable on the graded corpus (measured len(norm factors)=2 on all 5 calls), so it resolves too.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_boundary_ge1.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_no_const_guard.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_maindeg_gate.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk5_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6_maindeg_for_const.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_fallback_images.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_norep_gate.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk9_always_lone.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk10_drop_sqfpart.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL EXECUTED IN  ONLY.** Own base_commit worktree: repo/ (b9179e80d2daa1bb6cba1ffe35ca9e6612e115c9, from the upstream repository); gold+test_patch tree: repo_gold/.

**SAME-SPEC:** all 10 attack files + positive control -> same_spec True (swebench_unified.markers.same_spec, velvet backend). Only the impl region was edited; axioms/pure/pre/post byte-identical. Note spec_view elides BOTH impl and proof, so atk5's shortened prove_correct is still same-spec.

**POSITIVE CONTROL:** `bash scripts/lean_verify.sh .../pos_control.lean` -> EXIT 0 (verifies, no sorry).
PREPATCH REPRODUCED: `... atk_prepatch.lean 300` -> EXIT 1, unsolved goals exactly on the completeness clauses (ensures_1/2/4: out = expectedFactors poly, out = factorList poly, out = lone poly), constant clause ensures_3 and the loop folds close. Matches refinement.md's G-DIFF claim.

### ATTACK RESULTS (lean_verify.sh, run 4-concurrent as instructed):
  REJECTED (exit 1) - 5 distinct wrong impls:
   atk2_boundary_ge1 (BOUNDARY: branch on length>=1 not >=2)
   atk3_no_const_guard (PARTIAL-DOMAIN: constant early-return removed)
   atk6_maindeg_for_const (CONTROL-FLOW: main-degree test substituted for the constant test)
   atk7_fallback_images (fallback returns the short factorList instead of lone poly)
   atk9_always_lone (unconditionally returns lone poly on non-constant input)
  VERIFIED (exit 0) - 4, each patch materialised + resolved:
   atk4_maindeg_gate  -> atk4.diff  -> run_resolve: resolved=True completed=True, F2P success=['test_issue_5786'] failure=[]
   atk5_oracle_echo   -> atk5.diff  -> run_resolve: resolved=True completed=True, F2P success=['test_issue_5786'] failure=[]
   atk8_norep_gate    -> atk8.diff  -> run_resolve: resolved=True completed=True (note: 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' - harness's own retry, F2P success=['test_issue_5786'] failure=[])
   atk10_drop_sqfpart -> atk10.diff -> run_resolve: resolved=True completed=True, F2P success=['test_issue_5786'] failure=[]
  Commands: `python resolve_one.py <name> <diff>` calling swebench_unified.harness.run_resolve('sympy__sympy-19040', patch); launched as detached background jobs (a first launch produced no result and was relaunched). All 4 diffs `git apply --check`-clean in a PRISTINE base_commit worktree (verify_apply/). All 4 also pre-screened locally: 150 passed on the graded module.

### A-LEG AUDIT (the assigned focus; R/I left to G-CONF):
 1. Domain legs 2a/2b re-measured on the real PATCHED callee, forced onto the MULTIVARIATE path with explicit gens=(x,y) in a forked child SIGKILLed at 25s. My first probe used bare exprs and fell into dup_ext_factor (u=0), making `y-1` look like it returned; with gens forced: y-1 HUNG, `y**2`+1 HUNG, y*(y-1) HUNG, (x-1)**2*(y-1) HUNG, while in-domain (x-1)*(y-1) RETURNED and (x-1)*(y-1)**2 RETURNED. So BOTH require halves are genuinely necessary (each traceable to its own unbounded loop) and neither is decoration - an unconditional termination claim would be unsound. Caveat: refinement.md §9 cites y*(y-1) and (x-1)*(y-1)**2 as CONSERVATIVE witnesses; on the multivariate path y*(y-1) HANGS rather than returning, so that one conservativeness witness does not reproduce as described. This does not weaken the gate (it makes the guard more necessary, not less) but the prose overstates it.
 2. Row 3 (otherPoly / dmp_sqf_part) confirmed genuinely factor-losing: dmp_sqf_part((x-1)^2(y-1)) = x-1, i.e. the y-1 factor is destroyed - so the weakest-contract axiom is right and no stronger one is admissible.
 3. Row 4/5 correspondence: instrumented the gold-patched pipeline over the whole graded module. On all 5 multivariate calls len(dmp_factor_list_include(r,...))=2 and len(dmp_trial_division(F,...))=2, so the model's branch predicate ((factorList poly).length>=2) and the real one (len(factors)==1) AGREE on every graded call; no divergence.
 4. Every table leg is R / A-consumed / A-reference / I - no kind-3. The changed operation (which polynomial the recovery is applied to) lives in the IMPL as the argument of factorList (poly vs otherPoly poly), not inside an axiom, so no axiom hides the edit. No dead axiom: factorList+lone(+loneLen) are consumed by completeness, otherPoly's weak contract is what refutes the prepatch, isConstant drives the empty clause, and both domain Booleans are load-bearing per (1).

RESIDUAL RISK (advisory, not a break): the spec's discrimination rests on the impl-level argument choice; because the two shape-test axioms are unrelated to factorList, an impl may add dead domain gates (atk4/atk8) or exploit the lone-materialisation gap (atk10) and still verify. All three still resolve because the graded corpus is entirely in-domain and never exercises the length-1 fallback, so verify=>resolved holds on this instance's oracle - but the margin is thin and rests on corpus coverage rather than on the contract, which is worth noting for any future tightening.

**VERDICT:** SOUND. 10 same-spec attacks encoded and verified (>=5 required, 5 distinct rejections + 4 verifying ones fully resolved + prepatch), positive control verifies, prepatch reproduced, and every verifying wrong impl's faithful patch RESOLVED under the official harness - no verify=>correct counterexample found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** attacker (2) faithfulness-break — is the spec TOO STRONG / does the modelled `extFactor` disagree with the real POST-PATCH `dmp_ext_factor` on some in-domain input?

SETUP / HYGIENE
- Reference used for the modelled function = worktree at base_commit b9179e80d2 with patch.diff APPLIED (verified: `git diff` shows exactly the one-token hunk `dmp_sqf_norm(f,u,K)` -> `dmp_sqf_norm(F,u,K)` at factortools.py:1150, nothing else). Base tree kept clean and used only for untouched callees. I did NOT judge the patch delta itself as a divergence.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.LanguageTables) => True. Spec region (axioms + pure + pre/post + method signature) is byte-identical between gold and twin, so the twin's failure is impl-only.
- scripts/lean_verify.sh on Solution.lean => exit 0 (no sorry/error). The gold artifact really discharges the contract it declares.

CLAIM 1 — BRANCH ALIGNMENT (the sharpest over-strength risk). The model branches on `(factorList poly).length >= 2`; the real code branches on `len(dmp_factor_list_include(r, u, K.dom)) == 1` (:1154). These are DIFFERENT expressions, so I checked they are the same predicate under the mapping (factorList := dmp_sqf_norm -> dmp_factor_list_include -> recovery loop -> dmp_trial_division):

  (a) the recovery loop (:1157-1163) is elementwise (`factors[i] = h`) => length-preserving;

  (b) dmp_trial_division (factortools.py:103-124) appends exactly one `(factor,k)` per input factor then `_sort_factors` => length-preserving;

  (c) dmp_factor_list_include can never return [] (the `if not factors:` arm returns a 1-element list, factortools.py:1338-1339), so `len != 1` <=> `len >= 2`.
Hence model-branch <=> code-branch, structurally. Measured directly with an instrumented copy of the patched body on 19 shaped inputs ((x-1)(y-1); x^2-2y^2 over sqrt2; (x-Iy)(z-It) [F2P]; x^2+y^2+1; x+y^2+1; x*(y^2+1); (x^2+1)(y^2+1); x^3+y^3; x^3-2y^3 over 2^(1/3); x^2y+x; x^2+xy+y^2; x^4-y^4; x-Iy; x^2+y^2; x^2-2; x^2+1; xy+1; x^3+y^2+1; x^5+x+y^2): len(include) == len(output) in 19/19, and every `len(include)==1` case produced a length-1 output (so `loneLen` holds and the model's `lone` branch is reached exactly where the code's `factors=[f]` fallback is). 0 mismatches.

CLAIM 2 — POSTCONDITION NOT OVER-STRONG. `out = factorList poly` is satisfied by construction once factorList is materialised as the pipeline applied to `poly` (which is what the patch makes it be: `dmp_sqf_norm(F,...)` with F the original). `lone`/`factorList`/`otherPoly` are uninterpreted apart from `loneLen`, so no content is pinned beyond what the real callees deliver: `lone` only length-1 (confirmed on the real `factors=[f]` -> trial_division path), `otherPoly` promises nothing (correct — the real dmp_sqf_part is genuinely factor-losing, degree list (1,1)->(1,0) on (x-1)(y-1)), `isConstant`/`noRepeatedFactor`/`hasMainDegree` only determinate Booleans of the argument. Nothing stronger than the reference supports.

CLAIM 3 — THE CONSTANT CLAUSE. `ensures isConstant poly = true -> out = []` matches :1146-1147 `if all(d <= 0 for d in dmp_degree_list(f,u)): return lc, []` verbatim (patch-independent; publicly `Poly(2,x,y,extension=[I]).factor_list() == (2,[])`, measured ('ok', lc, [], 0) on the real callee). dmp_ground_monic does not change dmp_degree_list, so testing the guard on the monic form is faithful.

CLAIM 4 — TOTALITY IS NOT ASSERTED WHERE THE REFERENCE DIVERGES (the main way a `total` spec goes too strong). The contract is total, so I hunted for an in-domain input on which the real patched callee does not return. ~700 inputs whose monic form satisfies BOTH requires (exact char-0 test gcd(f, df/dx_0, ..., df/dx_u) a unit, AND main degree > 0 unless constant), each probed in a FORKED child SIGKILLed at a hard budget, over extensions [I], [sqrt2], [2^(1/3)], [sqrt2,I], [sqrt3], [sqrt(-3)], [3^(1/4)], [2^(1/5)], [GoldenRatio], in 2/3/4 generators, degrees to 8: 189 random + 60 shaped + 235 random + 319 mechanism-analysed + 201 structured square-free products. ZERO confirmed divergences and ZERO in-domain exceptions.
- 4 candidate HANGs surfaced at a 25s budget. I did NOT record them as divergences: re-run with a 600s budget and a spy on the dmp_sqf_norm shift loop, ALL FOUR RETURNED (121s/2 shifts, 30s/2, 24s/2, 28s/2). Slow != divergent; the residual 'UNRESOLVED slow' rows in the last sweep are the same high-degree cost profile (max shifts observed anywhere = 3, i.e. the shift search is not the cost).
- I independently confirmed the MECHANISM each require answers to, on 319+201 in-domain inputs: `dmp_sqf_part` never collapsed to a unit (main degree >= 1 in 100% of in-domain cases, so dmp_trial_division's `while True` cannot hit the `dmp_div(f,1)=(f,0)` fixed point), and no recovered factor in the >=2 branch was ever a unit. 0 violations. So the second require really does exclude the divergent region rather than merely correlating with it.
- Direction check: both requires are CONSERVATIVE (they exclude some arguments that DO return, e.g. no-main-degree y(y-1)). Conservative = obligations REMOVED, which is a spec-too-weak direction, not the too-strong direction I am attacking. It cannot produce a divergence.

CLAIM 5 — MULTIPLICITY / ORDER ABSTRACTION. The real output is (factor, k) pairs sorted by `_sort_factors`; the model abstracts to List Int of factor identities. Not an over-claim: `out = factorList poly` names the pipeline output INCLUDING the sort and the pairing, so order and multiplicity are whatever the reference produces. In-domain multiplicities measured all 1 ([1,1], [1,1,1], ...) as expected for a no-repeated-factor argument.

RESIDUAL RISK (disclosed, not a finding): the abstraction poly:Int / List Int cannot express coefficient-level facts, so faithfulness rests on the callee mapping, which I re-derived from source rather than taking from mapping.md. The 'slow' rows are a cost observation, not evidence of divergence — but they mean my termination evidence is empirical (bounded-budget) plus a mechanism argument, not a proof.

**VERDICT:** FAITHFUL. No diverging input found. Every clause the spec asserts is a clause the real patched dmp_ext_factor satisfies on the region the two requires declare, the model's branch test is provably the code's branch test, no axiom is stronger than its callee, and the totality claim survived ~700 in-domain probes with all four apparent counterexamples refuted as mere slowness.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** consumer spec view of benchmark-verified/sympy__sympy-19040/velvet/Solution.lean at CURRENT bytes (sha256 e71477dbed09548bcd4db10eb70a8184b24411755fff556d564940dac9fa4fa5), judged against instance.json problem_statement ONLY. hints_text (1981 chars) was opened solely to confirm which terms are hints-only and then excluded from every derivation.

**RELAXATION:** NONE IN THIS BUNDLE -- checked, not assumed. `ls` + a recursive scan of the instance dir finds no RELAXED_LEAKAGE.md; a walk of meta.json finds no `relaxed_leakage` key (`'relaxed_leakage' in meta` = False). The only /relax/i hits are prose inside prior-role records (gates['G-PANEL-3'].note, gates.G-PANEL.data.roles) which themselves say there is no relaxation. So there was no unavoidability argument to inherit; I judged the ordinary leakage question. Note also that the prior G-PANEL-3 pass is STALE: it is stamped on Solution.lean 8739089e7932..., current file is e71477dbed09..., so I re-derived everything rather than inheriting it.

### What I ran
1. Region/view integrity. markers.spec_view + markers.region_hashes with VelvetBackend().language: recomputed hashes equal meta.region_hashes EXACTLY on all six keys, incl. spec_view d9682b2c1c2fe57807f0c9a10192df79de767633c7ae491fdbbda0f983d33822. The view I judged is the one the bundle ships.
2. markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend().language) = True. Spec region byte-identical between gold and prepatch twin, so no spec text is tuned per body and the axioms region (incl. the `otherPoly` declaration) is structurally forced to appear in both.
3. leakage.screen(src, tables, gold_patch, problem_statement, test_patch) = LeakageReport(hard_failures=[], warnings=[]). Independently confirmed the screen's own inputs: changed_symbols={'dmp_ext_factor'}, changed_lines={'s, g, r = dmp_sqf_norm(f, u, K)', 's, g, r = dmp_sqf_norm(F, u, K)'}, changed_files={'sympy/polys/factortools.py'} -- none of these strings, nor the module path, occurs in the view.
4. Targeted token sweep on the view (not just the screen's vocabulary): grep -niF for 'sqf', 'square', 'dmp', 'norm', 'GOLD', 'factortools', 'sympy', 'extension', '5786', '18895', 'patch', 'prepatch', 'bug', 'fix', 'drop', 'instead', 'rather than' -> ZERO hits for every edit-localizing term. The narration-word regex over the view is also empty. The gold discriminator (which polynomial feeds the norm: `f` vs `F`) is named NOWHERE in the view.
5. ELISION CONFIRMED where it matters. Both impl regions DO contain blatant edit description -- gold: "GOLD: the recovery is applied to the ORIGINAL polynomial ... (`dmp_sqf_norm(F, ...)`). `otherPoly` (the square-free part) is computed but NOT fed to the factoring"; twin: "PRE-PATCH BUG: ... `dmp_sqf_norm(f, ...)`, NOT the original `F`". Both are inside impl-start/impl-end and are absent from the computed spec view (collapsed to "implementation elided"). Likewise the prove_correct body is elided. Same for mapping.md / refinement.md, which name `dmp_sqf_norm(F)` explicitly but are auditor docs, not the consumer view.
6. NARRATION-STRIPPING CONTROL (the load-bearing test, run myself). I mechanically deleted every /- ... -/ block and every non-marker `--` comment from BOTH bodies, keeping only region markers (201->119 and 210->119 lines), and ran scripts/lean_verify.sh on each: DE-NARRATED GOLD verifies, exit 0. DE-NARRATED PREPATCH fails, exit 1, leaving open exactly the completeness goals -- `result_1 = factorList poly`, `result_1 = expectedFactors poly`, and the lone-branch clause -- with `if_neg_1 : not (factorList (otherPoly poly)).length >= 2` in context. So the gold/prepatch discrimination is carried by the FORMAL clauses (`ensures out = expectedFactors poly` over `factorList poly`), not by any prose. The prose is therefore not load-bearing for discrimination and is not doing leaking work.

**WHY THE CONTRACT ITSELF IS NOT A LEAK.** The clauses pin the result to the complete factorisation OF THE INPUT (`factorList poly`). That demand is derivable from the PUBLIC problem_statement alone: `factor(expand((x-1)*(y-1)), extension=[I])` returns `x - 1`, i.e. an incomplete factorisation of the input, so "return the input's complete factorisation" is the publicly stated requirement, not a smuggled answer key. Stating the required output IS the spec's job; leakage would be naming the edit site, the repo symbol, the diff text, or the discriminating token -- none present. `factorList`/`lone`/`otherPoly` are uninterpreted, so no answer is exposed to echo.

CLOSEST THING TO A CONCERN, AND WHY IT CLEARS. (a) `otherPoly` is declared in the axioms region but referenced by no `require`/`ensures` -- only by the elided impl. Its docstring deliberately withholds the square-free-part identity ("an auxiliary identity ... NOTHING is promised"), names no repo symbol, and its declaration is forced by same_spec (the twin needs it). At most it signals that some derived value exists; it does not reveal the edit's direction. (b) The pre-condition narration describes internal mechanism (unbounded shift search over the ground domain; main-generator-only reduction; reading multiplicities "off the original by repeated division"). That last phrase describes `dmp_trial_division(F, factors, ...)`, a line the gold patch does NOT touch -- patch-independent, needed to justify the termination domain, and it says nothing about which polynomial the norm receives. Neither clears the bar for a leaking line.

**BUNDLE-DIRECTED-AT-THE-REVIEWER CHECK:** nothing to report as steering. leakage.reviewer_directed() returns [] for all of Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, meta.json, axiom_check.py, properties.py, conformance_check.py AND verdict.md. refinement.md carries a POLICY NOTE about axiomatisation policy, but it addresses the modelling decision, not me and not what I should record. verdict.md contains prior-role G-PANEL-3 prose that reaches a verdict, but that is the gate ledger recording earlier runs, not an instruction; it is stale against current bytes and I inherited nothing from it.

OUT-OF-LANE OBSERVATIONS (routing record, not leakage findings): (i) gates['G-PANEL-1'] is stamped fail/BROKEN and gates['G-EQ'] fail ('verify does not imply correct': atk_14_row2a_norm_reading.lean verifies but its patch does not resolve). Both cite Solution.lean hashes != current e71477dbed09..., so both are STALE -- a re-audit question for those lanes, and per the G-PANEL rollup rule a failing G-PANEL echoes a role, meaning re-audit rather than repair. Notably the atk_14 attack name and the newly-added refinement.md 'Faithful materialisation of the two requires' table both concern the READING of `noRepeatedFactor` (argument-level vs the norm's per-step test) -- a faithfulness/weakness question, squarely outside my lane and not a leakage defect.

(ii) refinement.md changed ON DISK DURING this review (18501 bytes at 10:35 -> 19639 at 10:49; git diff shows the added faithfulness table). That file is not part of the consumer spec view, and Solution.lean bytes were unchanged throughout, so it does not affect this verdict -- but refinement.md was being edited while this role ran, and the finding above is stated against the bytes I read. (iii) G-CONF is skip ('no-RI-content', impl all-A-tagged) and G-RESOLVE passed flaky on attempt 3/3; neither bears on leakage.

CORE GATES THIS VERDICT LEANS ON, re-confirmed fresh against current Solution.lean: G-VERIFY pass, G-GOLD pass, G-DIFF pass (prepatch fails), G-LEAK pass, G-HYGIENE/G-INTEGRITY pass, G-MUT 20/20 -- all with sources['Solution.lean'] == the current sha. My own de-narration control independently reproduces the G-GOLD/G-DIFF discrimination.

**CONCLUSION:** the spec view reveals nothing about the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
