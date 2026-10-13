# P2 adversarial audit — sympy__sympy-13974

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk01_prepatch.lean`, `atk04_partial_arity.lean`, `atk05_partial_exp.lean`, `atk06_boundary_first.lean`, `atk07_flag_ignored.lean`, `atk08_diverge.lean`, `atk09_swapargs.lean`, `atk10_reverse.lean`, `atk11_route_by_arity.lean`, `atk12_dup_positions.lean`, `atk13_guarded_feasible.lean`, `atk14_fixed_exponent.lean`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk02_echo_oracle.lean`, `atk03_echo_crossed.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none — no counterexample survived. 18 distinct same-spec wrong impls were encoded and verified with scripts/lean_verify.sh; 16 were REJECTED (exit 1) with genuine residual SPEC obligations (ensures_1 / ensures_2 / invariant_2 / decreasing_1 — not tactic artifacts), and the only 2 that verify (atk02_echo_oracle, atk03_echo_crossed) are exact echoes of BOTH modeled ops. Their faithful refined patches were MATERIALIZED and RUN through the official Docker harness (swebench_unified.harness.run_resolve) and BOTH RESOLVE: p1_faithful_premap.diff -> resolved:true (F2P 1/1, P2P 4/4) and p2_faithful_lazy.diff -> resolved:true (F2P 1/1, P2P 4/4). So verify => correct holds on every verifying impl found; no verify-but-not-resolve pair exists.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk01_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -59,7 +59,7 @@
       decreasing i
     do
       let b := factors[i - 1]!
-      result := powF b n :: result
+      result := b :: result
       i := i - 1
     return result
     -- impl-end
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,12 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    return factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 2 — `atk02_echo_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -50,18 +50,7 @@
   ensures out = powAll n factors
   do
     -- impl-start
-    let mut result : List Factor := []
-    let mut i := factors.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ factors.length
-      invariant result = powAll n (factors.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let b := factors[i - 1]!
-      result := powF b n :: result
-      i := i - 1
-    return result
+    return powAll n factors
     -- impl-end
 
 /- The backward-fold step: dropping one fewer factor exposes the factor at `i-1`
@@ -80,8 +69,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +90,12 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    return factorImage isPowOfAggregate n factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 3 — `atk03_echo_crossed.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -50,18 +50,7 @@
   ensures out = powAll n factors
   do
     -- impl-start
-    let mut result : List Factor := []
-    let mut i := factors.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ factors.length
-      invariant result = powAll n (factors.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let b := factors[i - 1]!
-      result := powF b n :: result
-      i := i - 1
-    return result
+    return factorImage true n factors
     -- impl-end
 
 /- The backward-fold step: dropping one fewer factor exposes the factor at `i-1`
@@ -80,8 +69,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +90,15 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    if isPowOfAggregate then
+      return powAll n factors
+    else
+      return factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 4 — `atk04_partial_arity.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -50,18 +50,10 @@
   ensures out = powAll n factors
   do
     -- impl-start
-    let mut result : List Factor := []
-    let mut i := factors.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ factors.length
-      invariant result = powAll n (factors.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let b := factors[i - 1]!
-      result := powF b n :: result
-      i := i - 1
-    return result
+    if factors.length <= 1 then
+      return factors
+    else
+      return powAll n factors
     -- impl-end
 
 /- The backward-fold step: dropping one fewer factor exposes the factor at `i-1`
@@ -80,8 +72,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +100,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 5 — `atk05_partial_exp.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,15 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    if isPowOfAggregate && n >= 2 then
+      return powAll n factors
+    else
+      return factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 6 — `atk06_boundary_first.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -52,15 +52,17 @@
     -- impl-start
     let mut result : List Factor := []
     let mut i := factors.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ factors.length
       invariant result = powAll n (factors.drop i)
-      done_with i = 0
+      done_with i = 1 ∨ i = 0
       decreasing i
     do
       let b := factors[i - 1]!
       result := powF b n :: result
       i := i - 1
+    if i = 1 then
+      result := factors[0]! :: result
     return result
     -- impl-end
 
@@ -80,8 +82,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +110,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 7 — `atk07_flag_ignored.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,12 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    return powAll n factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 8 — `atk08_diverge.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -52,15 +52,19 @@
     -- impl-start
     let mut result : List Factor := []
     let mut i := factors.length
-    while i > 0
+    let mut spin : Nat := 0
+    while i > 0 || spin = 0
       invariant 0 ≤ i ∧ i ≤ factors.length
       invariant result = powAll n (factors.drop i)
       done_with i = 0
       decreasing i
     do
-      let b := factors[i - 1]!
-      result := powF b n :: result
-      i := i - 1
+      if i > 0 then
+        let b := factors[i - 1]!
+        result := powF b n :: result
+        i := i - 1
+      else
+        spin := spin
     return result
     -- impl-end
 
@@ -80,8 +84,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +112,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 9 — `atk09_swapargs.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -59,7 +59,7 @@
       decreasing i
     do
       let b := factors[i - 1]!
-      result := powF b n :: result
+      result := powF n b :: result
       i := i - 1
     return result
     -- impl-end
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +108,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 10 — `atk10_reverse.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -51,16 +51,16 @@
   do
     -- impl-start
     let mut result : List Factor := []
-    let mut i := factors.length
-    while i > 0
+    let mut i := 0
+    while i < factors.length
       invariant 0 ≤ i ∧ i ≤ factors.length
-      invariant result = powAll n (factors.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = powAll n (factors.take i)
+      done_with i = factors.length
+      decreasing factors.length - i
     do
-      let b := factors[i - 1]!
+      let b := factors[i]!
       result := powF b n :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +108,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 11 — `atk11_route_by_arity.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,15 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    if factors.length >= 2 then
+      return powAll n factors
+    else
+      return factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 12 — `atk12_dup_positions.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,15 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    if isPowOfAggregate then
+      return powAll n (factors ++ factors)
+    else
+      return factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 13 — `atk13_guarded_feasible.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -59,7 +59,10 @@
       decreasing i
     do
       let b := factors[i - 1]!
-      result := powF b n :: result
+      if factors.length > 0 then
+        result := b :: result
+      else
+        result := powF b n :: result
       i := i - 1
     return result
     -- impl-end
@@ -80,8 +83,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +111,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 14 — `atk14_fixed_exponent.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,15 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    if isPowOfAggregate then
+      return powAll 2 factors
+    else
+      return factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 15 — `atk15_double_raise.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,15 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    if isPowOfAggregate then
+      return powAll n (powAll n factors)
+    else
+      return factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 16 — `atk16_tail_only.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -59,7 +59,10 @@
       decreasing i
     do
       let b := factors[i - 1]!
-      result := powF b n :: result
+      if i = factors.length then
+        result := powF b n :: result
+      else
+        result := b :: result
       i := i - 1
     return result
     -- impl-end
@@ -80,8 +83,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +111,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 17 — `atk17_drop_position.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -50,18 +50,7 @@
   ensures out = powAll n factors
   do
     -- impl-start
-    let mut result : List Factor := []
-    let mut i := factors.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ factors.length
-      invariant result = powAll n (factors.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let b := factors[i - 1]!
-      result := powF b n :: result
-      i := i - 1
-    return result
+    return powAll n factors.tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer factor exposes the factor at `i-1`
@@ -80,8 +69,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -105,4 +97,7 @@
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

Attack 18 — `atk18_flag_negated.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,8 +80,11 @@
 
 prove_correct distributePow by
   loom_solve
-  rw [powAll_drop_step factors n i (by omega) (by omega)]
-  simp_all
+  all_goals (try rw [powAll_drop_step factors n i (by omega) (by omega)])
+  all_goals (try simp_all [powAll, factorImage])
+  all_goals (try grind [powAll, factorImage])
+  all_goals (try omega)
+  all_goals (try rfl)
 
 /- The factor-position operation. `isPowOfAggregate` says whether the examined
    factor is a power of the aggregate whose positions are `factors` (then `n` is
@@ -98,11 +101,12 @@
   ensures isPowOfAggregate = false → out = factors
   do
     -- impl-start
-    let out : List Factor :=
-      if isPowOfAggregate then powAll n factors else factors
-    return out
+    return factorImage (!isPowOfAggregate) n factors
     -- impl-end
 
 prove_correct simplifyFactor by
   loom_solve
-  all_goals simp_all [factorImage]
+  all_goals (try simp_all [factorImage, powAll])
+  all_goals (try grind [factorImage, powAll])
+  all_goals (try cases isPowOfAggregate <;> simp_all [factorImage, powAll])
+  all_goals (try rfl)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SPEC INTEGRITY (checked first): markers.same_spec(Solution.lean, atk_N.lean)=True for ALL 18 attacks + both controls (verified with the exact command in the brief, velvet backend); variant_scope.unsound_evasions=[] and is_admissible_variant=True for all 20 (no new axiom, no sorry, no dropped prove_correct). Solution.lean declares 0 `axiom`s. Fresh base_commit worktree (84c125972ad535b2dfb245f8d311d347b45e5b8a).

**POSITIVE CONTROL:** pc_gold.lean (byte-identical impl) -> `bash scripts/lean_verify.sh .../pc_gold.lean` -> EXIT 0. pc2_gold_strong.lean (same impl, strengthened/impl-shape-agnostic tactic body) -> EXIT 0. Non-vacuity confirmed, and the strong tactic body is not itself a false-reject source.

PREPATCH BUG REPRODUCED (atk01_prepatch.lean, both sites: site A `result := b :: result`; site A.2 `return factors` on both arms) -> EXIT 1, residuals `case invariant_2: result = powAll n (factors.drop i)` at THE PIN and `case ensures_2 ... .true  |- factors = powAll n factors` at THE ROUTE. Both obligations fire.

ATTACK BATTERY — all run as concurrent background batches of 4 via `bash scripts/lean_verify.sh <f>.lean`. Every attack reached a DEFINITIVE exit code (no 124, no infra error). Rejected (exit 1) with the observed residual goal:
- atk04_partial_arity (PARTIAL DOMAIN, site A skips arity<=1): ensures_1: out = powAll n factors
- atk05_partial_exp (PARTIAL DOMAIN, route only raises when n>=2): ensures_2 .true
- atk06_boundary_first (BOUNDARY, first position left unraised): ensures_1
- atk07_flag_ignored (route always raises): ensures_1 .false |- powAll n factors = factors
- atk08_diverge (CONTROL-FLOW EFFECT: correct value, non-terminating loop): `case decreasing_1: i` — total-correctness semantics genuinely kills divergence
- atk09_swapargs (powF n b, base/exponent transposed): invariant_2 — powF is opaque, so no algebraic escape
- atk10_reverse (right multiset, wrong order): invariant_2 on the take-form invariant
- atk11_route_by_arity (UNGROUNDED ROUTING: decides by arity, not the flag): ensures_1 .false
- atk12_dup_positions (arity inflation): |- powAll n (factors ++ factors) = powAll n factors
- atk13_guarded_feasible (wrong branch behind a FEASIBLE, non-vacuous guard `factors.length > 0`): invariant_2 — Assert-style vacuity is not what carries the reject
- atk14_fixed_exponent (ignores n, raises by literal 2 — the n<->e.exp R-leg): |- powAll 2 factors = powAll n factors
- atk15_double_raise (raise applied twice; powF opaque so not idempotent): |- powAll n (powAll n factors) = powAll n factors
- atk16_tail_only (only the last position raised): invariant_2
- atk17_drop_position (returns a SHORTER sequence — arity leg): |- powAll n factors.tail = powAll n factors
- atk18_flag_negated (factorImage (!flag)): ensures_1 .false |- powAll n factors = factors
Verifying echoes (exit 0): atk02_echo_oracle (both impls = the spec term verbatim), atk03_echo_crossed (INDEPENDENT spelling: distributePow via `factorImage true`, simplifyFactor via an explicit if/else branch).

MANDATORY RESOLVE RUNS (official Docker oracle via swebench_unified.harness.run_resolve, instance sympy__sympy-13974, timeout 1800; EVERY diff `git apply --check`-ed in a clean base_commit worktree FIRST — all OK). All 5 completed:true, patch_successfully_applied:true:
- p1_faithful_premap.diff (faithful refinement of atk02_echo_oracle; THE ROUTE spelled ONCE uniformly by pre-mapping every nc_part factor through factorImage, plus tensor_product_simp_Pow and the Pow-branch dispatch) -> **resolved:true**, F2P success [test_tensor_product_simp], P2P 4/4.
- p2_faithful_lazy.diff (faithful refinement of atk03_echo_crossed; an INDEPENDENT spelling — `_image_of` applied lazily at each of the four factor-examination sites, false arm honoured literally as `out = factors`, written from mapping.md alone rather than copied from gold) -> **resolved:true**, F2P 1/1, P2P 4/4.
- p3_faithful_unmodeled_variant.diff (both modeled ops exact, but every UNMODELED downstream choice taken differently from gold: scalar part folded in one factor at a time, combine loop re-seeded from a ones-vector instead of imgs[0]) -> **resolved:true**. Confirms mapping.md §2's last row: the unmodeled surface cannot flip the verdict.
- p4_faithful_unmodeled_residue.diff (MY SHARPEST FALSIFICATION ATTEMPT: both modeled ops exact, but the factor domain OUTSIDE the spec's boolean bijection — a factor that is neither a power-of-aggregate nor a bare aggregate — keeps the PRE-PATCH wholesale multiply `new_args[i] * next` instead of gold's TypeError) -> **resolved:true**. The unmodeled residue is genuinely unobserved by F2P/P2P, so this is not a hole the spec must close.
- p5_incomplete_siteA_only.diff (DISCRIMINATOR CONTROL = the prior pass's recorded counterexample: site A complete, THE ROUTE absent) -> **resolved:false**, F2P failure [test_tensor_product_simp], P2P 4/4. This is NOT a spec defect: it leaves `simplifyFactor` unimplemented, so it is an INCOMPLETE refinement of the frozen spec, not a faithful one. It independently re-confirms §B's measurement that THE ROUTE is an independently-fixed behavior and that the second obligation is live rather than decorative.

A-LEG / refinement.md AUDIT (the assigned focus): every leg is tagged R (6: A1, A2, A4, A2.1, A2.2, A2.4) or I (2: A3, A2.3). NO kind-3, NO A-consumed, NO A-reference — so there are no A-legs of the axiom-consuming kind to break, and I confirmed that claim MECHANICALLY rather than taking the prose: Solution.lean declares 0 `axiom`s, the sole callee `powF` is `opaque` with no `ensures`, so no obligation is discharged by assumption; the proofs consume only the structural unfold of powAll/factorImage plus the case split on the routing flag.

The G-AX skip is legitimate, not an evasion: `tensor_product_simp_Pow` has 0 occurrences in the base_commit worktree, so the modeled function does not exist where G-AX runs — validating it there would both violate directive 7 (function under change) and ImportError; consistently, no axiom_check.py ships in the bundle. The A.2 correspondence to the real callees HOLDS: mapping.md §1 names all four post-patch routing sites (:322-325, :328-333, :346-355, :358-360) and I checked each against patch.diff — every one performs exactly the flag-selected image, so ONE contracted method legitimately models all four. The strongest evidence for that correspondence is constructive: p1 and p2 were built from the refinement/mapping tables ALONE (not by copying gold's Mul edits) and both resolve, in two structurally different spellings.

**HONEST LIMITATION:** refinement.md's §A.2 load-bearing binding — 'this is the operation EVERY place a factor of a product is examined must perform' — is carried in the frozen spec's own docstring as prose (confirmed present in spec_view). It is not a machine-checked clause. But the obligation itself is real and machine-enforced: a solver refining only site A verifies `distributePow` and FAILS `simplifyFactor` (exactly atk01's ensures_2 residual), and p5 shows such a patch does not resolve. This remains the narrowest margin in the bundle, not a defect.

**NOTHING IS INCONCLUSIVE:** 18/18 attacks + 2/2 controls reached definitive exit codes, and 5/5 resolve runs completed with a real report (completed:true, patch_successfully_applied:true). Verdict SOUND: every verifying wrong-impl candidate turned out to be an exact echo of both modeled ops whose faithful refined patch RESOLVES on the official harness, so no verify-but-not-resolve witness exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk01_prepatch.lean`, `atk04_partial_arity.lean`, `atk05_partial_exp.lean`, `atk06_boundary_first.lean`, `atk07_flag_ignored.lean`, `atk08_diverge.lean`, `atk09_swapargs.lean`, `atk10_reverse.lean`, `atk11_route_by_arity.lean`, `atk12_dup_positions.lean`, `atk13_guarded_feasible.lean`, `atk14_fixed_exponent.lean`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk02_echo_oracle.lean`, `atk03_echo_crossed.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none — no counterexample survived. 18 distinct same-spec wrong impls were encoded and verified with scripts/lean_verify.sh; 16 were REJECTED (exit 1) with genuine residual SPEC obligations (ensures_1 / ensures_2 / invariant_2 / decreasing_1 — not tactic artifacts), and the only 2 that verify (atk02_echo_oracle, atk03_echo_crossed) are exact echoes of BOTH modeled ops. Their faithful refined patches were MATERIALIZED and RUN through the official Docker harness (swebench_unified.harness.run_resolve) and BOTH RESOLVE: p1_faithful_premap.diff -> resolved:true (F2P 1/1, P2P 4/4) and p2_faithful_lazy.diff -> resolved:true (F2P 1/1, P2P 4/4). So verify => correct holds on every verifying impl found; no verify-but-not-resolve pair exists.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk01_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk02_echo_oracle.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk03_echo_crossed.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk04_partial_arity.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk05_partial_exp.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk06_boundary_first.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk07_flag_ignored.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk08_diverge.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk09_swapargs.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk10_reverse.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk11_route_by_arity.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk12_dup_positions.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk13_guarded_feasible.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk14_fixed_exponent.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk15_double_raise.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk16_tail_only.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk17_drop_position.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk18_flag_negated.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SPEC INTEGRITY (checked first): markers.same_spec(Solution.lean, atk_N.lean)=True for ALL 18 attacks + both controls (verified with the exact command in the brief, velvet backend); variant_scope.unsound_evasions=[] and is_admissible_variant=True for all 20 (no new axiom, no sorry, no dropped prove_correct). Solution.lean declares 0 `axiom`s. Fresh base_commit worktree (84c125972ad535b2dfb245f8d311d347b45e5b8a).

**POSITIVE CONTROL:** pc_gold.lean (byte-identical impl) -> `bash scripts/lean_verify.sh .../pc_gold.lean` -> EXIT 0. pc2_gold_strong.lean (same impl, strengthened/impl-shape-agnostic tactic body) -> EXIT 0. Non-vacuity confirmed, and the strong tactic body is not itself a false-reject source.

PREPATCH BUG REPRODUCED (atk01_prepatch.lean, both sites: site A `result := b :: result`; site A.2 `return factors` on both arms) -> EXIT 1, residuals `case invariant_2: result = powAll n (factors.drop i)` at THE PIN and `case ensures_2 ... .true  |- factors = powAll n factors` at THE ROUTE. Both obligations fire.

ATTACK BATTERY — all run as concurrent background batches of 4 via `bash scripts/lean_verify.sh <f>.lean`. Every attack reached a DEFINITIVE exit code (no 124, no infra error). Rejected (exit 1) with the observed residual goal:
- atk04_partial_arity (PARTIAL DOMAIN, site A skips arity<=1): ensures_1: out = powAll n factors
- atk05_partial_exp (PARTIAL DOMAIN, route only raises when n>=2): ensures_2 .true
- atk06_boundary_first (BOUNDARY, first position left unraised): ensures_1
- atk07_flag_ignored (route always raises): ensures_1 .false |- powAll n factors = factors
- atk08_diverge (CONTROL-FLOW EFFECT: correct value, non-terminating loop): `case decreasing_1: i` — total-correctness semantics genuinely kills divergence
- atk09_swapargs (powF n b, base/exponent transposed): invariant_2 — powF is opaque, so no algebraic escape
- atk10_reverse (right multiset, wrong order): invariant_2 on the take-form invariant
- atk11_route_by_arity (UNGROUNDED ROUTING: decides by arity, not the flag): ensures_1 .false
- atk12_dup_positions (arity inflation): |- powAll n (factors ++ factors) = powAll n factors
- atk13_guarded_feasible (wrong branch behind a FEASIBLE, non-vacuous guard `factors.length > 0`): invariant_2 — Assert-style vacuity is not what carries the reject
- atk14_fixed_exponent (ignores n, raises by literal 2 — the n<->e.exp R-leg): |- powAll 2 factors = powAll n factors
- atk15_double_raise (raise applied twice; powF opaque so not idempotent): |- powAll n (powAll n factors) = powAll n factors
- atk16_tail_only (only the last position raised): invariant_2
- atk17_drop_position (returns a SHORTER sequence — arity leg): |- powAll n factors.tail = powAll n factors
- atk18_flag_negated (factorImage (!flag)): ensures_1 .false |- powAll n factors = factors
Verifying echoes (exit 0): atk02_echo_oracle (both impls = the spec term verbatim), atk03_echo_crossed (INDEPENDENT spelling: distributePow via `factorImage true`, simplifyFactor via an explicit if/else branch).

MANDATORY RESOLVE RUNS (official Docker oracle via swebench_unified.harness.run_resolve, instance sympy__sympy-13974, timeout 1800; EVERY diff `git apply --check`-ed in a clean base_commit worktree FIRST — all OK). All 5 completed:true, patch_successfully_applied:true:
- p1_faithful_premap.diff (faithful refinement of atk02_echo_oracle; THE ROUTE spelled ONCE uniformly by pre-mapping every nc_part factor through factorImage, plus tensor_product_simp_Pow and the Pow-branch dispatch) -> **resolved:true**, F2P success [test_tensor_product_simp], P2P 4/4.
- p2_faithful_lazy.diff (faithful refinement of atk03_echo_crossed; an INDEPENDENT spelling — `_image_of` applied lazily at each of the four factor-examination sites, false arm honoured literally as `out = factors`, written from mapping.md alone rather than copied from gold) -> **resolved:true**, F2P 1/1, P2P 4/4.
- p3_faithful_unmodeled_variant.diff (both modeled ops exact, but every UNMODELED downstream choice taken differently from gold: scalar part folded in one factor at a time, combine loop re-seeded from a ones-vector instead of imgs[0]) -> **resolved:true**. Confirms mapping.md §2's last row: the unmodeled surface cannot flip the verdict.
- p4_faithful_unmodeled_residue.diff (MY SHARPEST FALSIFICATION ATTEMPT: both modeled ops exact, but the factor domain OUTSIDE the spec's boolean bijection — a factor that is neither a power-of-aggregate nor a bare aggregate — keeps the PRE-PATCH wholesale multiply `new_args[i] * next` instead of gold's TypeError) -> **resolved:true**. The unmodeled residue is genuinely unobserved by F2P/P2P, so this is not a hole the spec must close.
- p5_incomplete_siteA_only.diff (DISCRIMINATOR CONTROL = the prior pass's recorded counterexample: site A complete, THE ROUTE absent) -> **resolved:false**, F2P failure [test_tensor_product_simp], P2P 4/4. This is NOT a spec defect: it leaves `simplifyFactor` unimplemented, so it is an INCOMPLETE refinement of the frozen spec, not a faithful one. It independently re-confirms §B's measurement that THE ROUTE is an independently-fixed behavior and that the second obligation is live rather than decorative.

A-LEG / refinement.md AUDIT (the assigned focus): every leg is tagged R (6: A1, A2, A4, A2.1, A2.2, A2.4) or I (2: A3, A2.3). NO kind-3, NO A-consumed, NO A-reference — so there are no A-legs of the axiom-consuming kind to break, and I confirmed that claim MECHANICALLY rather than taking the prose: Solution.lean declares 0 `axiom`s, the sole callee `powF` is `opaque` with no `ensures`, so no obligation is discharged by assumption; the proofs consume only the structural unfold of powAll/factorImage plus the case split on the routing flag.

The G-AX skip is legitimate, not an evasion: `tensor_product_simp_Pow` has 0 occurrences in the base_commit worktree, so the modeled function does not exist where G-AX runs — validating it there would both violate directive 7 (function under change) and ImportError; consistently, no axiom_check.py ships in the bundle. The A.2 correspondence to the real callees HOLDS: mapping.md §1 names all four post-patch routing sites (:322-325, :328-333, :346-355, :358-360) and I checked each against patch.diff — every one performs exactly the flag-selected image, so ONE contracted method legitimately models all four. The strongest evidence for that correspondence is constructive: p1 and p2 were built from the refinement/mapping tables ALONE (not by copying gold's Mul edits) and both resolve, in two structurally different spellings.

**HONEST LIMITATION:** refinement.md's §A.2 load-bearing binding — 'this is the operation EVERY place a factor of a product is examined must perform' — is carried in the frozen spec's own docstring as prose (confirmed present in spec_view). It is not a machine-checked clause. But the obligation itself is real and machine-enforced: a solver refining only site A verifies `distributePow` and FAILS `simplifyFactor` (exactly atk01's ensures_2 residual), and p5 shows such a patch does not resolve. This remains the narrowest margin in the bundle, not a defect.

**NOTHING IS INCONCLUSIVE:** 18/18 attacks + 2/2 controls reached definitive exit codes, and 5/5 resolve runs completed with a real report (completed:true, patch_successfully_applied:true). Verdict SOUND: every verifying wrong-impl candidate turned out to be an exact echo of both modeled ops whose faithful refined patch RESOLVES on the official harness, so no verify-but-not-resolve witness exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**FAITHFULNESS-BREAK ATTACK:** no divergence found between the modeled functions and the real patched repo. Reference used correctly = base_commit 84c1259 worktree with patch.diff APPLIED (fresh worktree, `git apply` clean); base only consulted for the pre-patch prose claims in refinement.md/mapping.md.

**ENV NOTE:** repo needs py3.8 (base commit does `from collections import Mapping`); used  with PYTHONPATH at the worktree.

SPEC REGION / VERIFY: Solution.lean elaborates clean, scripts/lean_verify.sh exit 0 (1200s cap). spec_view via markers/velvet LanguageTables shows the frozen surface = the two `ensures` sets on distributePow and simplifyFactor, plus the axioms/pure regions (powF opaque, powAll, factorImage). meta.json G-HYGIENE records region_hashes.spec_view c05b70ea...; regions parse with impl+proof elided as expected.

LANE 1 -- distributePow / powAll vs real tensor_product_simp_Pow. 26,952 genuine Pow-of-TensorProduct nodes (arity 1-5, distinct/repeated factors, symbolic + Integer + negative + Rational + composite exponents, Integer(1)/Integer(0)/I/nan/oo/Mul/Pow/nested-TP factor pools, exhaustive over 2- and 3-arity products of an 18-element pool x 16 exponents). Compared the model as refinement A4 specifies -- powAll then aggregate REBUILD, TP(*[`b**exp`]) -- against tensor_product_simp_Pow(e) AND the public tensor_product_simp(e). 0 mismatches.
  A first pass comparing the raw model LIST against the real return flagged 422 'mismatches' (e.g. `1x1**oo` -> model [nan,nan] vs real nan) and 1069 COLLAPSED_NONTP cases (e.g. (A**-1)xB**(-3/2): real returns a Mul `Abs(A)**3*(conjugate(A)**(-3/2))x(B**(-3/2))`, not a TensorProduct, because sympy pulls the commutative scalar out of the rebuilt TP). I traced every one of these to MY OWN harness comparing a Lean-side List against a post-constructor Python value -- i.e. skipping the A4 rebuild step. Under the rebuild the spec prescribes, all 1069+422 agree exactly. Reporting those as UNFAITHFUL would have been a harness artifact, not a spec defect.

LANE 2 -- simplifyFactor / factorImage vs real tensor_product_simp_Mul. 36,153 single-non-commutative-factor products (18,054 raise arm, 18,099 passthrough arm), scalars 1/2/x/y/`x*y`/1-2/sqrt(2)/x+1/-1/3, exhaustive over 2- and 3-arity aggregates x 6 exponents x 5 scalars. Shadow = Mul(*c_part)*TP(*factorImage(flag,n,args)) vs tensor_product_simp_Mul(e) and tensor_product_simp(e). 0 mismatches. Both `ensures` conditional clauses hold on the real repo: flag=true really does yield the per-position raise, flag=false really does hand the factor back untouched.

SITES LANE 2 EXCLUDES (the bundle's own documented scope gap) -- I tested them anyway, since a too-strong spec would show up here. 7,999 MULTI-non-commutative-factor products (2 and 3 factors, bare and powered TPs, exhaustive over 3 aggregates x 6x6 exponent pairs) against the leading-factor (:328-333), trailing-factor (:346-355) and fallback (:358-360) routing sites, modeling per-factor factorImage followed by the unchanged position-wise combine. 0 divergences -- so mapping.md §1's claim that all four spellings perform the same routing decision holds empirically, and the spec is not too strong there either.

**FALSE-ARM SOUNDNESS.** The `isPowOfAggregate = false -> out = factors` clause needs TP(*f.args) == f. Verified idempotent on 8,437 genuine TensorProducts (incl. Add/Mul/Pow/scalar-carrying/nan/oo factors): 0 reconstruction failures. Also probed the asymmetry that the real guard at :322-325 tests only `isinstance(f, Pow)` with NO base check while mapping.md's flag tests `isinstance(f,Pow) and isinstance(f.base,TensorProduct)`: 40 Pow-over-non-TensorProduct single-factor cases (`A**2`, (`A*B`)**x, (A+B)**2, (`A**2`)**x, ...). The real tpsP returns such an `e` unchanged, matching the false arm's `out = factors`. 0 divergences.

**OPAQUENESS.** powF is `opaque` with no `ensures`, so the spec assumes no algebraic identity about `**`; it cannot be too strong via an exponentiation fact. Proofs consume only the structural unfold of powAll/factorImage and the boolean case split -- consistent with refinement §C's no-consumed-axiom claim. No G-AX is possible here (tensor_product_simp_Pow is ADDED by the patch, absent at base_commit), so G-CONF-on-patched-tree is the right mechanism; the bundle's own conformance_check.py reproduces this: 'G-CONF OK ... 80130 whole-expression inputs, simplifyFactor on 68781 factor-position inputs (34431 raise arm, 34350 passthrough arm), 0 disagreements', and it fails loudly if an arm goes unreached.

TWO PROSE IMPRECISIONS, both non-behavioral, neither a faithfulness break (recording, not charging):
1. mapping.md §3.2 and refinement A2.3 bind factorImage to `tensor_product_simp_Pow(f).args`. That `.args` spelling is wrong whenever the raise produces a commutative scalar that sympy factors out -- e.g. f=(A**-1)xB**(-3/2): tpsP(f) is a Mul, so .args == [Abs(A)**3, (conjugate(A)**(-3/2))x(B**(-3/2))], NOT the per-position image. The behavior still agrees under the rebuilt-aggregate comparison that refinement A4 actually specifies, so this is loose prose in the callee-provenance table, not a modeled-function divergence.
2. mapping.md §2's flag=False row binds `factors <-> f.args`; read literally on a Pow-over-non-TP factor that would give [base, exp] and a bogus TP(A,2). But the same row explicitly scopes flag=False to 'the factor is a bare aggregate', so it is a documented domain restriction, and § the observable check above shows the routing is faithful on both documented arms.

Also confirmed the F2P mapping in refinement §B against the real patched tree: tps(TP(A,B)**x)=(`A**x`)x(`B**x`), tps(`x*TP`(A,B)**2)=x*(`A**2`)x(`B**2`), tps(x*(TP(A,B)**2)*TP(C,D))=x*(`A**2*C`)x(`B**2*D`) -- all three match the spec's prescription, and TP() itself raises IndexError so the empty-aggregate case the Lean `powAll n [] = []` allows is simply unreachable in the repo (vacuous, not divergent).

**CONCLUSION:** on every input in the modeled domain that I could construct -- ~71k modeled nodes across three independent harnesses plus the bundle's 148k-input G-CONF -- the modeled functions agree with the real patched callees. No diverging input exists to cite, so the faithfulness-break attack fails. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / GOLD-RECONSTRUCTION, sympy__sympy-13974 velvet. Judged in STRICT mode, not as an inherited relaxation: there is no RELAXED_LEAKAGE.md under the instance dir and no `relaxed_leakage` key in meta.json (I walked the whole JSON; the only relax/leak-matching key is gates.G-LEAK, status=pass, mode=strict). So no unavoidability argument needed re-deriving -- the spec view has to be clean outright, and I judged it that way.

**SCOPE.** Only spec_view ships to the consumer (eval/dataset.py:285 sets task.spec_view from adapter.spec_view; refinement.md and mapping.md quote the gold diff verbatim but are audit-side artifacts, never sent). So I judged the 91-line projection, computed myself via markers.spec_view(Solution.lean, get_backend('velvet')): sha256 c05b70ea243aa80cc8481c52a917dede31f32e10602d2a9dde395dfb3baa81fe, which matches the recorded G-HYGIENE region_hashes.spec_view exactly. markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True, and I confirmed the two spec views are byte-identical strings -- every word of the prepatch's pre-image narration ("MUST fail", "Pre-image skeleton", "never performed", "left alone") sits inside the elided impl regions and appears in NEITHER spec view.

(a) MECHANICAL SCREEN. leakage.screen(Solution.lean, velvet, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Changed symbols the screen guards: tensor_product_simp (public via the issue, skipped), tensor_product_simp_Mul, tensor_product_simp_Pow. Neither non-public symbol appears. I also hand-scanned the view for 17 repo tokens -- tensor_product_simp{,`_Mul`,`_Pow`}, TensorProduct, tensorproduct.py, sympy/physics, e.base, e.exp, args, isinstance, Pauli, sigma3, n_nc, nc_part, c_part, TypeError, 'Mul(' -- ALL absent. The vocabulary is abstracted throughout (Factor/powF/powAll/factorImage/distributePow/simplifyFactor/isPowOfAggregate); no identifier embeds a patched symbol, no patched path or dotted module, no diff marker, no bug/fix narration.

(b) THE REAL QUESTION -- is the second facet gratuitous edit-localization? The view exposes TWO obligations: distributePow (exponent distributed across a whole expression's factors) and simplifyFactor (the same raise reached when the power occupies ONE factor position of a product). If facet 2 were unnecessary for resolution, naming it would be the spec pointing at the second gold hunk. I MEASURED it instead of arguing. In a pristine copy of the base_commit worktree (84c125972a; I reset two files a prior run had left modified, confirmed `git status --porcelain` empty), I hand-wrote a FACET-A-ONLY fix -- add tensor_product_simp_Pow and route tensor_product_simp's Pow branch into it, touching tensor_product_simp_Mul NOT AT ALL -- then ran the F2P test. It FAILS: `tensor_product_simp(x*TP(A,B)**2)` returns `x*AxB**2`, not `x*TP`(`A**2`,`B**2`). The full gold patch on the same tree: 7 passed. So the factor-position facet is load-bearing for resolution; a spec covering only facet A would admit non-resolving impls. Stating both facets is the faithfulness requirement, not localization of the edit.

(c) PUBLIC-ANCHOR CHECK. Both facets are derivable from the solver-visible problem_statement (I never consulted hints_text for the baseline -- and note the hints DO name tensor_product_simp_Pow and give the pseudo-expression, which is exactly why they are excluded). I executed the issue's own sessions [2]-[9] on the pristine base_commit: every failing example is a whole-expression Pow (t1=tp(1,1)*tp(1,1) and t2=tp(1,Pauli(3))**2 both have type Pow), while [5] and [9] show the genuine Mul-of-TensorProducts path already working and are labelled by the issue as "expected result". So the public issue itself sets powers-of-a-tensor-product against products-of-tensor-products and asks for the former to evaluate; "a power of an aggregate occurring as one factor of a product" is the abstract closure of that public contrast, not a disclosure. ('power', 'powers', 'product', 'tensor', 'tensorproduct', 'pow', 'evaluate', 'expand', 'simp' are all in the statement; the view's non-public words -- factor, exponent, aggregate, position, distribute -- are generic abstraction vocabulary that localizes nothing.)

(d) PROSE-NOT-LOAD-BEARING CONTROL (the strip test). I stripped EVERY comment from both files via leakage.`_lean_strip_comments_collect` and re-verified: comment-free Solution.lean exit 0, comment-free Solution_prepatch.lean exit 1. The discrimination lives entirely in the formal clauses (out = powAll n factors; out = factorImage isPowOfAggregate n factors plus the two arm implications), so the docstrings add ZERO discriminating power -- they cannot be smuggling the edit. Unstripped controls: Solution.lean verifies exit 0; Solution_prepatch.lean fails exit 1 at BOTH sites with the expected goals (factors[i-1]?.getD 0 = powF (factors[i-1]?.getD 0) n, and isPowOfAggregate = true -> factors = powAll n factors).

(e) CORE GATES THIS LEANS ON, re-run not trusted: G-GOLD/G-DIFF re-derived by the two lean_verify.sh runs above (gold verifies, prepatch fails). G-CONF re-run by executing conformance_check.py against the gold-patched worktree: "G-CONF OK ... distributePow on 80130 whole-expression inputs, simplifyFactor on 68781 factor-position inputs (34431 raise arm, 34350 passthrough arm) (seed=13974), 0 disagreements" -- matches the recorded detail, so the model whose facets I judged is the one the gate measured. G-AX is legitimately skip (no axioms; powF is uninterpreted with no ensures consumed, so no soundness obligation rides on it).

(f) BUNDLE-INTEGRITY / DOES ANYTHING ADDRESS ME. I ran leakage.reviewer_directed over refinement.md, mapping.md, Solution.lean, Solution_prepatch.lean, properties.py, conformance_check.py and verdict.md: [] for every file. Nothing instructs me how to record or asserts which verdict is honest. Two things I deliberately did NOT inherit: (1) verdict.md carries a PRIOR G-PANEL-3 record that already reads "VERDICT: NO-LEAKAGE" with a similar evidence list -- that is a previous run's entry in the gate-owned ledger, not a directive, and I re-derived every measurement above independently rather than echoing it; (2) refinement.md self-corrects an earlier revision that had called the A.2 site "not a new behavior" -- I did not credit that correction either, I established A.2's necessity myself with the facet-A-only F2P failure in (b). refinement.md's single "G-PANEL" mention is a dated provenance note about a past total-correctness repair, not an instruction to this gate.

CAVEAT (scope, not a finding): the bundle dir carries transient build artifacts, and refinement.md/mapping.md quote gold-diff lines -- the latter is fine because those files are audit-side and never reach the consumer. Both are other gates' business and neither bears on leakage.

**VERDICT:** NO-LEAKAGE. The spec view names no patched symbol, path, or diff line; discloses exactly two behavioural obligations that I measured to be BOTH independently necessary for resolution; both are anchored in the public issue's own power-vs-product contrast; and the discrimination survives total comment removal, proving the narration carries no edit information.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
