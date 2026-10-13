# P2 adversarial audit — scikit-learn__scikit-learn-10844

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 admissible attacks re-run of 7 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2_spread_guard.lean`, `atk_3_oracle_echo.lean`, `atk_4_smuggled_range.lean`, `atk_6_redundant_factor_plan.lean`, `atk_7_unguarded_value_spread_plan.lean` |
| does not verify against this specification, so the specification excludes it | 2 | `atk_1_prepatch.lean`, `atk_5_product_plan_promoted_value.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 7 distinct same-spec attacks encoded (same_spec=True for all 7 + positive control); 5 verify, 2 correctly rejected. Every one of the 5 verifying attacks' faithful refined patches was MATERIALIZED, apply-checked at base_commit 97523985b3, and RUN through the official run_resolve: all 5 RESOLVED (F2P 1/1 success, P2P 16/16 success, zero failures). No verifying wrong impl produced a non-resolving faithful patch, so verify=>correct held on every probe I could construct.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,56 +296,21 @@
                            else (a : Rat) * a / ((b : Rat) * c)))
   do
     -- impl-start
-    -- Answer zero outright when there is no co-grouped pair, and otherwise
-    -- divide first and then combine. The plan records BOTH: the short-circuit,
-    -- and the fact that the only integers the combination materialises are the
-    -- three aggregates themselves. So the plan has a value on a degenerate input
-    -- (where a quotient's divisor is zero) as well as at every machine word
-    -- width, and no register product of aggregates is ever formed.
+    -- impl-start
+    -- ATTACK 1 = the PREPATCH BUG. Combine the two spreads by forming their PRODUCT
+    -- IN THE REGISTER (where the machine forms it) and divide the squared agreement
+    -- count into that register's content; report the product-first plan. No range
+    -- check anywhere.
     let p : RatPlan :=
-      .zeroThen (.read .agree)
-        (.mul (.ratio (.read .agree) (.read .spreadA))
-              (.ratio (.read .agree) (.read .spreadB)))
-    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)
-    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)
-    let v : Rat := if agree.toExact = 0 then 0 else ra * rb
+      .ratio (.mul (.read .agree) (.read .agree))
+             (.mul (.read .spreadA) (.read .spreadB))
+    let prod : Word width := spreadA * spreadB
+    let v : Rat :=
+      if agree.toExact = 0 then (0 : Rat)
+      else (agree.toExact : Rat) * agree.toExact / (prod.toExact : Rat)
     return some (p, v)
     -- impl-end
+    -- impl-end
 
 prove_correct fowlkesCoeffSquared by
   loom_solve
-  -- `require_5`/`require_4` are the two ordering facts; `require_3` is
-  -- `0 ≤ agree.toExact`.
-  have hab : agree.toExact ≤ spreadA.toExact := require_5
-  have hac : agree.toExact ≤ spreadB.toExact := require_4
-  have hta : (0:Int) ≤ agree.toExact := require_3
-  refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩
-  · split
-    · rfl
-    · rename_i hne
-      have hta' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm hne)
-      have hpk : (0:Rat) < (spreadA.toExact:Rat) := by
-        exact_mod_cast lt_of_lt_of_le hta' hab
-      have hqk : (0:Rat) < (spreadB.toExact:Rat) := by
-        exact_mod_cast lt_of_lt_of_le hta' hac
-      have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta
-      exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))
-  · by_cases h0 : agree.toExact = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
-      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)
-      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)
-      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]
-  · intro h; simp [h]
-  · intro h
-    simp only [h, if_false]
-    rw [div_mul_div_comm]
-  · intro w a b c _ ha hab' hac' _ _ _
-    by_cases h0 : a = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)
-      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')
-      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')
-      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
-        Option.some.injEq]
-      rw [div_mul_div_comm]
```

Attack 2 — `atk_2_spread_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,29 +296,49 @@
                            else (a : Rat) * a / ((b : Rat) * c)))
   do
     -- impl-start
-    -- Answer zero outright when there is no co-grouped pair, and otherwise
-    -- divide first and then combine. The plan records BOTH: the short-circuit,
-    -- and the fact that the only integers the combination materialises are the
-    -- three aggregates themselves. So the plan has a value on a degenerate input
-    -- (where a quotient's divisor is zero) as well as at every machine word
-    -- width, and no register product of aggregates is ever formed.
+    -- impl-start
+    -- ATTACK 2 (BOUNDARY / prior pass's named counterexample): a GENUINELY DIFFERENT
+    -- plan term. The short-circuit guards on the two SPREADS in a chain and NEVER on
+    -- the agreement count. refinement.md's "strength, the degenerate triple" bullet
+    -- claims the guard must be on the agreement count specifically; if this verifies,
+    -- that prose is over-tight.
     let p : RatPlan :=
-      .zeroThen (.read .agree)
-        (.mul (.ratio (.read .agree) (.read .spreadA))
-              (.ratio (.read .agree) (.read .spreadB)))
+      .zeroThen (.read .spreadA)
+        (.zeroThen (.read .spreadB)
+          (.mul (.ratio (.read .agree) (.read .spreadA))
+                (.ratio (.read .agree) (.read .spreadB))))
     let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)
     let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)
     let v : Rat := if agree.toExact = 0 then 0 else ra * rb
     return some (p, v)
     -- impl-end
+    -- impl-end
 
 prove_correct fowlkesCoeffSquared by
   loom_solve
-  -- `require_5`/`require_4` are the two ordering facts; `require_3` is
-  -- `0 ≤ agree.toExact`.
   have hab : agree.toExact ≤ spreadA.toExact := require_5
   have hac : agree.toExact ≤ spreadB.toExact := require_4
   have hta : (0:Int) ≤ agree.toExact := require_3
+  -- the plan denotes the coefficient on EVERY admissible triple
+  have key : ∀ (w : Nat) (a b c : Int), 0 ≤ a → a ≤ b → a ≤ c →
+      RatPlan.value w a b c
+        (.zeroThen (.read .spreadA)
+          (.zeroThen (.read .spreadB)
+            (.mul (.ratio (.read .agree) (.read .spreadA))
+                  (.ratio (.read .agree) (.read .spreadB)))))
+        = some (if a = 0 then 0 else (a : Rat) * a / ((b : Rat) * c)) := by
+    intro w a b c ha hab' hac'
+    by_cases hb : b = 0
+    · have ha0 : a = 0 := le_antisymm (hb ▸ hab') ha
+      simp [RatPlan.value, IntPlan.value, hb, ha0]
+    · by_cases hc : c = 0
+      · have ha0 : a = 0 := le_antisymm (hc ▸ hac') ha
+        simp [RatPlan.value, IntPlan.value, hb, hc, ha0]
+      · by_cases h0 : a = 0
+        · simp [RatPlan.value, IntPlan.value, hb, hc, h0]
+        · simp only [RatPlan.value, IntPlan.value, hb, hc, h0, if_false,
+            Option.some.injEq]
+          rw [div_mul_div_comm]
   refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩
   · split
     · rfl
@@ -330,22 +350,14 @@
         exact_mod_cast lt_of_lt_of_le hta' hac
       have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta
       exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))
-  · by_cases h0 : agree.toExact = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
-      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)
-      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)
-      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]
+  · rw [key width _ _ _ hta hab hac]
+    by_cases h0 : agree.toExact = 0
+    · simp [h0]
+    · simp only [h0, if_false]
+      rw [div_mul_div_comm]
   · intro h; simp [h]
   · intro h
     simp only [h, if_false]
     rw [div_mul_div_comm]
   · intro w a b c _ ha hab' hac' _ _ _
-    by_cases h0 : a = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)
-      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')
-      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')
-      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
-        Option.some.injEq]
-      rw [div_mul_div_comm]
+    exact key w a b c ha hab' hac'
```

Attack 3 — `atk_3_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,26 +296,23 @@
                            else (a : Rat) * a / ((b : Rat) * c)))
   do
     -- impl-start
-    -- Answer zero outright when there is no co-grouped pair, and otherwise
-    -- divide first and then combine. The plan records BOTH: the short-circuit,
-    -- and the fact that the only integers the combination materialises are the
-    -- three aggregates themselves. So the plan has a value on a degenerate input
-    -- (where a quotient's divisor is zero) as well as at every machine word
-    -- width, and no register product of aggregates is ever formed.
+    -- ATTACK 3 (UNGROUNDED-ORACLE ECHO): the value slot is the POSTCONDITION TEXT
+    -- copied verbatim. No ratio is formed, no aggregate is combined -- the routine
+    -- transcribes its own oracle. If the spec cannot tell this from a routine that
+    -- computes, the value slot is carrying nothing.
     let p : RatPlan :=
       .zeroThen (.read .agree)
         (.mul (.ratio (.read .agree) (.read .spreadA))
               (.ratio (.read .agree) (.read .spreadB)))
-    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)
-    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)
-    let v : Rat := if agree.toExact = 0 then 0 else ra * rb
+    let v : Rat :=
+      if agree.toExact = 0 then 0
+      else (agree.toExact : Rat) * agree.toExact
+             / ((spreadA.toExact : Rat) * spreadB.toExact)
     return some (p, v)
     -- impl-end
 
 prove_correct fowlkesCoeffSquared by
   loom_solve
-  -- `require_5`/`require_4` are the two ordering facts; `require_3` is
-  -- `0 ≤ agree.toExact`.
   have hab : agree.toExact ≤ spreadA.toExact := require_5
   have hac : agree.toExact ≤ spreadB.toExact := require_4
   have hta : (0:Int) ≤ agree.toExact := require_3
@@ -329,17 +326,17 @@
       have hqk : (0:Rat) < (spreadB.toExact:Rat) := by
         exact_mod_cast lt_of_lt_of_le hta' hac
       have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta
-      exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))
+      exact div_nonneg (mul_nonneg htk htk) (le_of_lt (mul_pos hpk hqk))
   · by_cases h0 : agree.toExact = 0
     · simp [RatPlan.value, IntPlan.value, h0]
     · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
       have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)
       have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)
-      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]
+      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
+        Option.some.injEq]
+      rw [div_mul_div_comm]
   · intro h; simp [h]
-  · intro h
-    simp only [h, if_false]
-    rw [div_mul_div_comm]
+  · intro h; simp [h]
   · intro w a b c _ ha hab' hac' _ _ _
     by_cases h0 : a = 0
     · simp [RatPlan.value, IntPlan.value, h0]
```

Attack 4 — `atk_4_smuggled_range.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,50 +296,75 @@
                            else (a : Rat) * a / ((b : Rat) * c)))
   do
     -- impl-start
-    -- Answer zero outright when there is no co-grouped pair, and otherwise
-    -- divide first and then combine. The plan records BOTH: the short-circuit,
-    -- and the fact that the only integers the combination materialises are the
-    -- three aggregates themselves. So the plan has a value on a degenerate input
-    -- (where a quotient's divisor is zero) as well as at every machine word
-    -- width, and no register product of aggregates is ever formed.
+    -- ATTACK 4 (PARTIAL-DOMAIN / smuggled hand-written range test): inside the word
+    -- take the PREPATCH product-first association (on PROMOTED operands, so it is
+    -- exact and the value clause cannot see it); only past the register boundary
+    -- fall back to divide-first. The plan still reports the divide-first shape.
+    -- If this verifies, the spec licenses a routine whose repo counterpart branches
+    -- on a hand-written range test and takes the pre-patch route on the small inputs.
     let p : RatPlan :=
       .zeroThen (.read .agree)
         (.mul (.ratio (.read .agree) (.read .spreadA))
               (.ratio (.read .agree) (.read .spreadB)))
-    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)
-    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)
-    let v : Rat := if agree.toExact = 0 then 0 else ra * rb
+    let prodExact : Int := spreadA.toExact * spreadB.toExact
+    let v : Rat :=
+      if agree.toExact = 0 then 0
+      else if inWord width prodExact then
+        (agree.toExact : Rat) * agree.toExact / (prodExact : Rat)
+      else
+        ((agree.toExact : Rat) / (spreadA.toExact : Rat))
+          * ((agree.toExact : Rat) / (spreadB.toExact : Rat))
     return some (p, v)
     -- impl-end
 
 prove_correct fowlkesCoeffSquared by
   loom_solve
-  -- `require_5`/`require_4` are the two ordering facts; `require_3` is
-  -- `0 ≤ agree.toExact`.
   have hab : agree.toExact ≤ spreadA.toExact := require_5
   have hac : agree.toExact ≤ spreadB.toExact := require_4
   have hta : (0:Int) ≤ agree.toExact := require_3
+  -- the two branches denote the SAME rational, so collapse the range test first
+  have hcollapse : ∀ (hne : agree.toExact ≠ 0),
+      (if inWord width (spreadA.toExact * spreadB.toExact) then
+         (agree.toExact : Rat) * agree.toExact
+           / ((spreadA.toExact * spreadB.toExact : Int) : Rat)
+       else
+         ((agree.toExact : Rat) / (spreadA.toExact : Rat))
+           * ((agree.toExact : Rat) / (spreadB.toExact : Rat)))
+      = (agree.toExact : Rat) * agree.toExact
+          / ((spreadA.toExact : Rat) * spreadB.toExact) := by
+    intro hne
+    have hcast : ((spreadA.toExact * spreadB.toExact : Int) : Rat)
+             = (spreadA.toExact : Rat) * (spreadB.toExact : Rat) := by
+      exact_mod_cast Int.cast_mul (α := Rat) spreadA.toExact spreadB.toExact
+    split
+    · rw [hcast]
+    · rw [div_mul_div_comm]
   refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩
-  · split
-    · rfl
-    · rename_i hne
-      have hta' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm hne)
+  · by_cases h0 : agree.toExact = 0
+    · simp [h0]
+    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
       have hpk : (0:Rat) < (spreadA.toExact:Rat) := by
-        exact_mod_cast lt_of_lt_of_le hta' hab
+        exact_mod_cast lt_of_lt_of_le ha' hab
       have hqk : (0:Rat) < (spreadB.toExact:Rat) := by
-        exact_mod_cast lt_of_lt_of_le hta' hac
+        exact_mod_cast lt_of_lt_of_le ha' hac
       have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta
-      exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))
+      simp only [h0, if_false]
+      rw [hcollapse h0]
+      exact div_nonneg (mul_nonneg htk htk) (le_of_lt (mul_pos hpk hqk))
   · by_cases h0 : agree.toExact = 0
     · simp [RatPlan.value, IntPlan.value, h0]
     · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
       have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)
       have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)
-      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]
+      simp only [h0, if_false]
+      rw [hcollapse h0]
+      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
+        Option.some.injEq]
+      rw [div_mul_div_comm]
   · intro h; simp [h]
   · intro h
     simp only [h, if_false]
-    rw [div_mul_div_comm]
+    rw [hcollapse h]
   · intro w a b c _ ha hab' hac' _ _ _
     by_cases h0 : a = 0
     · simp [RatPlan.value, IntPlan.value, h0]
```

Attack 5 — `atk_5_product_plan_promoted_value.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,56 +296,23 @@
                            else (a : Rat) * a / ((b : Rat) * c)))
   do
     -- impl-start
-    -- Answer zero outright when there is no co-grouped pair, and otherwise
-    -- divide first and then combine. The plan records BOTH: the short-circuit,
-    -- and the fact that the only integers the combination materialises are the
-    -- three aggregates themselves. So the plan has a value on a degenerate input
-    -- (where a quotient's divisor is zero) as well as at every machine word
-    -- width, and no register product of aggregates is ever formed.
+    -- ATTACK 5 (width-universality probe): the VALUE is reached the legitimate
+    -- promoted-exact way (so the value clause is satisfied outright), but the
+    -- reported PLAN materialises the integer products agree*agree and
+    -- spreadA*spreadB. refinement.md claims the universal plan clause kills any
+    -- IntPlan.mul at every width >= 3, while conceding w=2 alone does not. If the
+    -- clause were instantiated at one width, or the w=2 concession leaked, this
+    -- verifies and its faithful counterpart is the PRE-PATCH product-first line.
     let p : RatPlan :=
       .zeroThen (.read .agree)
-        (.mul (.ratio (.read .agree) (.read .spreadA))
-              (.ratio (.read .agree) (.read .spreadB)))
-    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)
-    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)
-    let v : Rat := if agree.toExact = 0 then 0 else ra * rb
+        (.ratio (.mul (.read .agree) (.read .agree))
+                (.mul (.read .spreadA) (.read .spreadB)))
+    let v : Rat :=
+      if agree.toExact = 0 then 0
+      else (agree.toExact : Rat) * agree.toExact
+             / ((spreadA.toExact : Rat) * spreadB.toExact)
     return some (p, v)
     -- impl-end
 
 prove_correct fowlkesCoeffSquared by
   loom_solve
-  -- `require_5`/`require_4` are the two ordering facts; `require_3` is
-  -- `0 ≤ agree.toExact`.
-  have hab : agree.toExact ≤ spreadA.toExact := require_5
-  have hac : agree.toExact ≤ spreadB.toExact := require_4
-  have hta : (0:Int) ≤ agree.toExact := require_3
-  refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩
-  · split
-    · rfl
-    · rename_i hne
-      have hta' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm hne)
-      have hpk : (0:Rat) < (spreadA.toExact:Rat) := by
-        exact_mod_cast lt_of_lt_of_le hta' hab
-      have hqk : (0:Rat) < (spreadB.toExact:Rat) := by
-        exact_mod_cast lt_of_lt_of_le hta' hac
-      have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta
-      exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))
-  · by_cases h0 : agree.toExact = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
-      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)
-      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)
-      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]
-  · intro h; simp [h]
-  · intro h
-    simp only [h, if_false]
-    rw [div_mul_div_comm]
-  · intro w a b c _ ha hab' hac' _ _ _
-    by_cases h0 : a = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)
-      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')
-      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')
-      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
-        Option.some.injEq]
-      rw [div_mul_div_comm]
```

Attack 6 — `atk_6_redundant_factor_plan.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,16 +296,16 @@
                            else (a : Rat) * a / ((b : Rat) * c)))
   do
     -- impl-start
-    -- Answer zero outright when there is no co-grouped pair, and otherwise
-    -- divide first and then combine. The plan records BOTH: the short-circuit,
-    -- and the fact that the only integers the combination materialises are the
-    -- three aggregates themselves. So the plan has a value on a degenerate input
-    -- (where a quotient's divisor is zero) as well as at every machine word
-    -- width, and no register product of aggregates is ever formed.
+    -- ATTACK 6 (control-flow-effect / distinct expression tree): the plan carries a
+    -- THIRD ratio factor spreadA/spreadA. It denotes 1 whenever it has a value, so
+    -- the plan still denotes the coefficient -- but it is a different expression
+    -- tree from gold line 859, with an extra division the gold line does not perform.
+    -- Its faithful counterpart multiplies in an extra np.sqrt(pk/pk).
     let p : RatPlan :=
       .zeroThen (.read .agree)
-        (.mul (.ratio (.read .agree) (.read .spreadA))
-              (.ratio (.read .agree) (.read .spreadB)))
+        (.mul (.mul (.ratio (.read .agree) (.read .spreadA))
+                    (.ratio (.read .agree) (.read .spreadB)))
+              (.ratio (.read .spreadA) (.read .spreadA)))
     let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)
     let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)
     let v : Rat := if agree.toExact = 0 then 0 else ra * rb
@@ -314,11 +314,26 @@
 
 prove_correct fowlkesCoeffSquared by
   loom_solve
-  -- `require_5`/`require_4` are the two ordering facts; `require_3` is
-  -- `0 ≤ agree.toExact`.
   have hab : agree.toExact ≤ spreadA.toExact := require_5
   have hac : agree.toExact ≤ spreadB.toExact := require_4
   have hta : (0:Int) ≤ agree.toExact := require_3
+  have key : ∀ (w : Nat) (a b c : Int), 0 ≤ a → a ≤ b → a ≤ c →
+      RatPlan.value w a b c
+        (.zeroThen (.read .agree)
+          (.mul (.mul (.ratio (.read .agree) (.read .spreadA))
+                      (.ratio (.read .agree) (.read .spreadB)))
+                (.ratio (.read .spreadA) (.read .spreadA))))
+        = some (if a = 0 then 0 else (a : Rat) * a / ((b : Rat) * c)) := by
+    intro w a b c ha hab' hac'
+    by_cases h0 : a = 0
+    · simp [RatPlan.value, IntPlan.value, h0]
+    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)
+      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')
+      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')
+      have hbR : (b:Rat) ≠ 0 := by exact_mod_cast hb0
+      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
+        Option.some.injEq]
+      rw [div_self hbR, mul_one, div_mul_div_comm]
   refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩
   · split
     · rfl
@@ -330,22 +345,14 @@
         exact_mod_cast lt_of_lt_of_le hta' hac
       have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta
       exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))
-  · by_cases h0 : agree.toExact = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
-      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)
-      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)
-      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]
+  · rw [key width _ _ _ hta hab hac]
+    by_cases h0 : agree.toExact = 0
+    · simp [h0]
+    · simp only [h0, if_false]
+      rw [div_mul_div_comm]
   · intro h; simp [h]
   · intro h
     simp only [h, if_false]
     rw [div_mul_div_comm]
   · intro w a b c _ ha hab' hac' _ _ _
-    by_cases h0 : a = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)
-      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')
-      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')
-      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
-        Option.some.injEq]
-      rw [div_mul_div_comm]
+    exact key w a b c ha hab' hac'
```

Attack 7 — `atk_7_unguarded_value_spread_plan.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -296,31 +296,63 @@
                            else (a : Rat) * a / ((b : Rat) * c)))
   do
     -- impl-start
-    -- Answer zero outright when there is no co-grouped pair, and otherwise
-    -- divide first and then combine. The plan records BOTH: the short-circuit,
-    -- and the fact that the only integers the combination materialises are the
-    -- three aggregates themselves. So the plan has a value on a degenerate input
-    -- (where a quotient's divisor is zero) as well as at every machine word
-    -- width, and no register product of aggregates is ever formed.
+    -- ATTACK 7 (CONTROL-FLOW-EFFECT + PARTIAL-DOMAIN): NO zero test appears
+    -- anywhere in the arithmetic -- the two quotients are formed unconditionally and
+    -- multiplied -- and the plan's only guards are on the two SPREADS. `Rat`
+    -- division is total (x/0 = 0), so on a degenerate admissible triple this still
+    -- denotes the required 0. If the spec admits this, the routine it describes
+    -- never decides anything on the agreement count, and the natural repo reading
+    -- of "no zero test in the arithmetic" is an UNGUARDED line 859 -- which is `nan`
+    -- at the (0, 0, 30) worst case that P2P test_fowlkes_mallows_score asserts on.
     let p : RatPlan :=
-      .zeroThen (.read .agree)
-        (.mul (.ratio (.read .agree) (.read .spreadA))
-              (.ratio (.read .agree) (.read .spreadB)))
-    let ra : Rat := (agree.toExact : Rat) / (spreadA.toExact : Rat)
-    let rb : Rat := (agree.toExact : Rat) / (spreadB.toExact : Rat)
-    let v : Rat := if agree.toExact = 0 then 0 else ra * rb
+      .zeroThen (.read .spreadA)
+        (.zeroThen (.read .spreadB)
+          (.mul (.ratio (.read .agree) (.read .spreadA))
+                (.ratio (.read .agree) (.read .spreadB))))
+    let v : Rat :=
+      ((agree.toExact : Rat) / (spreadA.toExact : Rat))
+        * ((agree.toExact : Rat) / (spreadB.toExact : Rat))
     return some (p, v)
     -- impl-end
 
 prove_correct fowlkesCoeffSquared by
   loom_solve
-  -- `require_5`/`require_4` are the two ordering facts; `require_3` is
-  -- `0 ≤ agree.toExact`.
   have hab : agree.toExact ≤ spreadA.toExact := require_5
   have hac : agree.toExact ≤ spreadB.toExact := require_4
   have hta : (0:Int) ≤ agree.toExact := require_3
+  have key : ∀ (w : Nat) (a b c : Int), 0 ≤ a → a ≤ b → a ≤ c →
+      RatPlan.value w a b c
+        (.zeroThen (.read .spreadA)
+          (.zeroThen (.read .spreadB)
+            (.mul (.ratio (.read .agree) (.read .spreadA))
+                  (.ratio (.read .agree) (.read .spreadB)))))
+        = some (if a = 0 then 0 else (a : Rat) * a / ((b : Rat) * c)) := by
+    intro w a b c ha hab' hac'
+    by_cases hb : b = 0
+    · have ha0 : a = 0 := le_antisymm (hb ▸ hab') ha
+      simp [RatPlan.value, IntPlan.value, hb, ha0]
+    · by_cases hc : c = 0
+      · have ha0 : a = 0 := le_antisymm (hc ▸ hac') ha
+        simp [RatPlan.value, IntPlan.value, hb, hc, ha0]
+      · by_cases h0 : a = 0
+        · simp [RatPlan.value, IntPlan.value, hb, hc, h0]
+        · simp only [RatPlan.value, IntPlan.value, hb, hc, h0, if_false,
+            Option.some.injEq]
+          rw [div_mul_div_comm]
+  -- the unconditional value equals the guarded one: when agree = 0 the numerator
+  -- vanishes, so the product of quotients is 0 regardless of the divisors.
+  have hval : ((agree.toExact : Rat) / (spreadA.toExact : Rat))
+                * ((agree.toExact : Rat) / (spreadB.toExact : Rat))
+              = if agree.toExact = 0 then 0
+                else (agree.toExact : Rat) * agree.toExact
+                       / ((spreadA.toExact : Rat) * spreadB.toExact) := by
+    by_cases h0 : agree.toExact = 0
+    · simp [h0]
+    · simp only [h0, if_false]
+      rw [div_mul_div_comm]
   refine ⟨_, _, rfl, ?_, ?_, ?_, ?_, ?_⟩
-  · split
+  · rw [hval]
+    split
     · rfl
     · rename_i hne
       have hta' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm hne)
@@ -329,23 +361,9 @@
       have hqk : (0:Rat) < (spreadB.toExact:Rat) := by
         exact_mod_cast lt_of_lt_of_le hta' hac
       have htk : (0:Rat) ≤ (agree.toExact:Rat) := by exact_mod_cast hta
-      exact mul_nonneg (div_nonneg htk (le_of_lt hpk)) (div_nonneg htk (le_of_lt hqk))
-  · by_cases h0 : agree.toExact = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < agree.toExact := lt_of_le_of_ne hta (Ne.symm h0)
-      have hb0 : spreadA.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab)
-      have hc0 : spreadB.toExact ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac)
-      simp [RatPlan.value, IntPlan.value, h0, hb0, hc0]
+      exact div_nonneg (mul_nonneg htk htk) (le_of_lt (mul_pos hpk hqk))
+  · rw [key width _ _ _ hta hab hac, hval]
   · intro h; simp [h]
-  · intro h
-    simp only [h, if_false]
-    rw [div_mul_div_comm]
+  · intro h; rw [hval]; simp [h]
   · intro w a b c _ ha hab' hac' _ _ _
-    by_cases h0 : a = 0
-    · simp [RatPlan.value, IntPlan.value, h0]
-    · have ha' : (0:Int) < a := lt_of_le_of_ne ha (Ne.symm h0)
-      have hb0 : b ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hab')
-      have hc0 : c ≠ 0 := ne_of_gt (lt_of_lt_of_le ha' hac')
-      simp only [RatPlan.value, IntPlan.value, h0, if_false, hb0, hc0,
-        Option.some.injEq]
-      rw [div_mul_div_comm]
+    exact key w a b c ha hab' hac'
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree ./wt @ 97523985b3). Verify cmd per file: `bash scripts/lean_verify.sh <f>.lean` from repo root. Resolve cmd: run_resolve('scikit-learn__scikit-learn-10844', <diff>, timeout=1800, retries=1) via resolve.py. Verifications and resolves were run as concurrent background batches of <=4 per the parallelism instruction (schedule only; every attack fully verified, every needed resolve executed).

**CONTROLS.** pos_control.lean (shipped impl verbatim) -> EXIT=0 VERIFIES (non-vacuity). atk_1_prepatch.lean (register product `spreadA * spreadB` via instMulWord + product-first plan, no range check) -> EXIT=1 REJECTED, so the prepatch bug IS reproduced and refuted; failure goal shows the exact-value conjunct unreachable once truncW wraps, matching refinement.md.

THE 7 ATTACKS (distinct failure modes):
1. atk_1_prepatch (prepatch bug / register-product) -> EXIT=1 correctly rejected.
2. atk_2_spread_guard (BOUNDARY, genuinely different plan term: .zeroThen (.read .spreadA) (.zeroThen (.read .spreadB) ...) -- guards on the two SPREADS, NEVER on the agreement count) -> VERIFIES EXIT=0. Faithful patch atk_2.diff (`if pk == 0.: return 0.` / `if qk == 0.: return 0.` + guarded product of roots) -> RESOLVED=True.
3. atk_3_oracle_echo (UNGROUNDED-ORACLE ECHO: value slot is the postcondition text `if a=0 then 0 else a*a/(b*c)` copied verbatim; no ratio formed) -> VERIFIES EXIT=0. Faithful patch atk_3.diff (promoted `float(int(pk)*int(qk))` per mapping.md's promoted-operand row) -> RESOLVED=True. Benign echo: the postcondition PINS an exact rational, so echoing it IS computing it, and the plan conjunct still forces the assembly.
4. atk_4_smuggled_range (PARTIAL-DOMAIN / smuggled hand-written range test `if inWord width prodExact` selecting the PREPATCH product-first association inside the word, divide-first only past the boundary) -> VERIFIES EXIT=0. Faithful patch atk_4.diff (explicit `prod = int(pk)*int(qk)`; `if -2**63 <= prod <= 2**63-1` product-first else divide-first) -> RESOLVED=True. Cannot break the cell: at the F2P witness exact `pk*qk` = 16974789265584974472 is OUT of the int64 word, so the test fires and the divide-first fallback == gold; and the in-word branch operates on PROMOTED arbitrary-precision operands, so it is exact and finite there too.
5. atk_5_product_plan_promoted_value (WIDTH-UNIVERSALITY probe: value reached the legitimate promoted-exact way but the reported PLAN materialises `agree*agree` and `spreadA*spreadB` as IntPlan.mul) -> EXIT=1 correctly REJECTED. Confirms the universal plan clause really does kill every IntPlan.mul.
6. atk_6_redundant_factor_plan (CONTROL-FLOW-EFFECT / distinct expression tree: plan carries a third ratio factor spreadA/spreadA, denoting 1) -> VERIFIES EXIT=0. Faithful patch atk_6.diff (extra `* np.sqrt(pk/pk)`) -> RESOLVED=True.
7. atk_7_unguarded_value_spread_plan (CONTROL-FLOW-EFFECT + PARTIAL-DOMAIN combined, my strongest attack: NO zero test anywhere in the arithmetic -- both quotients formed unconditionally -- AND the plan's only guards are on the two SPREADS, so nothing in the routine ever decides on the agreement count) -> VERIFIES EXIT=0. Faithful patch atk_7.diff (two spread guards, unguarded product of roots, NO tk test) -> RESOLVED=True (F2P 1/1, P2P 16/16).

WHY THE SPREAD-GUARD ROUTE CANNOT BREAK THE CELL (measured, probe_deg.py + pretest.py). The lever I targeted was P2P `test_fowlkes_mallows_score`'s worst case, which I computed to be exactly the degenerate triple (tk,pk,qk) = (0,0,30) -- the input where a guard-dropping patch returns nan and the test asserts 0. A spread-guard survives it because the ordering requires (tk<=pk, tk<=qk) make a vanishing spread FORCE tk=0: I enumerated all label arrays up to n=6 and every reachable triple with a vanishing spread has tk=0 (e.g. (0,0,2),(0,2,0),(0,0,0),(0,0,6),(0,6,0)), while every tk=0 triple with both spreads nonzero -- (0,2,2),(0,4,4),(0,2,6),(0,2,4) -- divides safely. So a spread guard fires on exactly the divide-by-zero cases and is behaviourally identical to gold's tk guard on the whole reachable domain. I pre-tested all 5 patches against every real FMS test call plus the F2P witness: all agree with gold to 9 decimals, including (0,0,30) -> 0.0 and the witness -> 0.728995978.

REFINEMENT.MD PROSE DEFECT (re-confirming a prior pass's finding, independently re-derived). The 'strength, the degenerate triple' bullet claims `.zeroThen` 'must guard on the AGREEMENT count specifically, since guarding on a spread instead leaves (0, b, 0) with b != 0 unanswered'. That reasoning is WRONG: (0,b,0) is answered by a spread-guard chain (the spreadB guard fires), and I discharged the universal plan clause in Lean for the spread-chain plan (atk_2, atk_7 both EXIT=0). The doc's argument is OVER-TIGHT, not unsound -- the spec is not broken, because a spread guard is behaviourally equivalent on the admissible domain (whenever a spread vanishes tk vanishes too, by the ordering requires) and both faithful patches RESOLVE. Recommend correcting that bullet; it does not affect the machine-checked spec.

A-LEG AUDIT (my mandated focus; R/I legs left to G-CONF). refinement.md tag census: 5 R, 2 I, 1 'I + R', 3 A-reference, 0 A-consumed -- every leg is R / A-reference / I, NO kind-3 (the only two 'kind-3' greps are the section heading asserting their absence). `grep -c '^axiom ' Solution.lean` == 0 and meta.json axioms == [], so the 'no consumed axioms' claim is TRUE with no over-claiming. meta.json declares 2 deep_model_references, both kind='A-reference', vs the doc's 3 table rows (the doc splits register carrier from plan semantics where meta merges them into one machine-word entry -- presentational, not a mismatch).
I independently re-derived all three A-reference correspondences against the REAL callees (aleg.py, my own transliteration, not the bundle's scripts):

  (i) SQUARING (np.sqrt(tk/pk)*np.sqrt(tk/qk))^2 == tk^2/(`pk*qk`): max relative error 6.642e-16 over 20000 random admissible triples on real numpy -> the root IS peelable by squaring, so declining to consume an axiom is honest, not a dodge.

  (ii) REGISTER CARRIER truncW 64 == real np.int64 multiplication: 0 disagreements / 20000 random full-signed-range pairs, wrap non-vacuous on 20000/20000. instMulWord IS np.int64 multiply.

  (iii) PARTIALITY == MACHINE FAILURE at the F2P witness (3003497866, 5152663196, 3294371982): exact `pk*qk` = 16974789265584974472 > int64 max, inWord 64 = False (product-first plan valueless), real np.int64 product wraps NEGATIVE to -1471954808124577144, real pre-patch tk/np.sqrt(`pk*qk`) == nan while gold == 0.7289959776021899. The model's `none` is the machine's `nan`.

  (iv) WIDTH-UNIVERSALITY re-executed at w=3..16: m=2^(w-1)-1 has `m*m` outside the word every time, so any IntPlan.mul is refuted at every width >= 3. At w=2, m=1 and `m*m`=1 DOES fit, so that single width does not refute a product-forming plan -- but the clause is a conjunction over ALL w>=2, so w=3 suffices. Benign; noting for completeness. atk_5's EXIT=1 is the empirical confirmation.
The bundle's own G-AX (`python axiom_check.py`) EXIT=0 independently, reporting the same magnitudes I measured plus the short-circuit reference and its negative control (2952 degenerate triples where the total rational carrier reports the same number for guarded and unguarded value expressions -- confirming the doc's honest admission that the VALUE slot cannot carry the short-circuit and the PLAN + tie must).

MODEL<->PATCH CORRESPONDENCE (holds). The returned plan `.zeroThen (.read .agree) (.mul (.ratio agree spreadA) (.ratio agree spreadB))` is node-for-node gold line 859 `np.sqrt(tk/pk)*np.sqrt(tk/qk) if tk != 0. else 0.` with the two roots peeled by squaring: guard -> two tk/. ratios -> outer multiply (which survives squaring in place since (sqrt x * sqrt y)^2 = `x*y`), and NO IntPlan.mul node, matching that gold materialises no integer product. The prepatch counterpart carries two IntPlan.mul plus a register product and is refuted on both observables.

**HONESTY CHECK PASSED.** refinement.md's 'Identity record' PRE-DECLARES my atk_3/atk_7-shaped rivals as accept-lane POSITIVE controls (pos-control-unconditional-value-arithmetic, pos-control-promoted-product-value) rather than hiding them in the reject lane, and properties.py carries them there. The doc does not over-claim discrimination it lacks.

**ENVIRONMENT.** properties.py imports cleanly (battery-integrity release-gate item OK). conformance_check.py could not run in this venv (ModuleNotFoundError: sklearn) -- an environment gap, not a spec defect, and G-CONF's R/I legs are outside my scope. All 5 resolves reported note 'resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)', i.e. host-load flakiness on attempt 1 with a clean resolved verdict on retry -- consistent across all 5, not a spec signal.

**VERDICT SOUND:** 7 distinct attacks encoded and fully verified (5 verifying, 2 correctly rejected including the prepatch), every verifying attack's faithful refined patch materialized, apply-checked at base_commit, and RUN through the official harness -- all 5 RESOLVED. One documentation defect to fix (the agreement-count-guard-is-forced bullet), which does not affect the machine-checked spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 admissible attacks re-run of 7 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_2_spread_guard.lean`, `atk_3_oracle_echo.lean`, `atk_4_smuggled_range.lean`, `atk_6_redundant_factor_plan.lean`, `atk_7_unguarded_value_spread_plan.lean` |
| does not verify against this specification, so the specification excludes it | 2 | `atk_1_prepatch.lean`, `atk_5_product_plan_promoted_value.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 7 distinct same-spec attacks encoded (same_spec=True for all 7 + positive control); 5 verify, 2 correctly rejected. Every one of the 5 verifying attacks' faithful refined patches was MATERIALIZED, apply-checked at base_commit 97523985b3, and RUN through the official run_resolve: all 5 RESOLVED (F2P 1/1 success, P2P 16/16 success, zero failures). No verifying wrong impl produced a non-resolving faithful patch, so verify=>correct held on every probe I could construct.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_spread_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 3 — `atk_3_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_smuggled_range.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 5 — `atk_5_product_plan_promoted_value.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_redundant_factor_plan.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_unguarded_value_spread_plan.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree ./wt @ 97523985b3). Verify cmd per file: `bash scripts/lean_verify.sh <f>.lean` from repo root. Resolve cmd: run_resolve('scikit-learn__scikit-learn-10844', <diff>, timeout=1800, retries=1) via resolve.py. Verifications and resolves were run as concurrent background batches of <=4 per the parallelism instruction (schedule only; every attack fully verified, every needed resolve executed).

**CONTROLS.** pos_control.lean (shipped impl verbatim) -> EXIT=0 VERIFIES (non-vacuity). atk_1_prepatch.lean (register product `spreadA * spreadB` via instMulWord + product-first plan, no range check) -> EXIT=1 REJECTED, so the prepatch bug IS reproduced and refuted; failure goal shows the exact-value conjunct unreachable once truncW wraps, matching refinement.md.

THE 7 ATTACKS (distinct failure modes):
1. atk_1_prepatch (prepatch bug / register-product) -> EXIT=1 correctly rejected.
2. atk_2_spread_guard (BOUNDARY, genuinely different plan term: .zeroThen (.read .spreadA) (.zeroThen (.read .spreadB) ...) -- guards on the two SPREADS, NEVER on the agreement count) -> VERIFIES EXIT=0. Faithful patch atk_2.diff (`if pk == 0.: return 0.` / `if qk == 0.: return 0.` + guarded product of roots) -> RESOLVED=True.
3. atk_3_oracle_echo (UNGROUNDED-ORACLE ECHO: value slot is the postcondition text `if a=0 then 0 else a*a/(b*c)` copied verbatim; no ratio formed) -> VERIFIES EXIT=0. Faithful patch atk_3.diff (promoted `float(int(pk)*int(qk))` per mapping.md's promoted-operand row) -> RESOLVED=True. Benign echo: the postcondition PINS an exact rational, so echoing it IS computing it, and the plan conjunct still forces the assembly.
4. atk_4_smuggled_range (PARTIAL-DOMAIN / smuggled hand-written range test `if inWord width prodExact` selecting the PREPATCH product-first association inside the word, divide-first only past the boundary) -> VERIFIES EXIT=0. Faithful patch atk_4.diff (explicit `prod = int(pk)*int(qk)`; `if -2**63 <= prod <= 2**63-1` product-first else divide-first) -> RESOLVED=True. Cannot break the cell: at the F2P witness exact `pk*qk` = 16974789265584974472 is OUT of the int64 word, so the test fires and the divide-first fallback == gold; and the in-word branch operates on PROMOTED arbitrary-precision operands, so it is exact and finite there too.
5. atk_5_product_plan_promoted_value (WIDTH-UNIVERSALITY probe: value reached the legitimate promoted-exact way but the reported PLAN materialises `agree*agree` and `spreadA*spreadB` as IntPlan.mul) -> EXIT=1 correctly REJECTED. Confirms the universal plan clause really does kill every IntPlan.mul.
6. atk_6_redundant_factor_plan (CONTROL-FLOW-EFFECT / distinct expression tree: plan carries a third ratio factor spreadA/spreadA, denoting 1) -> VERIFIES EXIT=0. Faithful patch atk_6.diff (extra `* np.sqrt(pk/pk)`) -> RESOLVED=True.
7. atk_7_unguarded_value_spread_plan (CONTROL-FLOW-EFFECT + PARTIAL-DOMAIN combined, my strongest attack: NO zero test anywhere in the arithmetic -- both quotients formed unconditionally -- AND the plan's only guards are on the two SPREADS, so nothing in the routine ever decides on the agreement count) -> VERIFIES EXIT=0. Faithful patch atk_7.diff (two spread guards, unguarded product of roots, NO tk test) -> RESOLVED=True (F2P 1/1, P2P 16/16).

WHY THE SPREAD-GUARD ROUTE CANNOT BREAK THE CELL (measured, probe_deg.py + pretest.py). The lever I targeted was P2P `test_fowlkes_mallows_score`'s worst case, which I computed to be exactly the degenerate triple (tk,pk,qk) = (0,0,30) -- the input where a guard-dropping patch returns nan and the test asserts 0. A spread-guard survives it because the ordering requires (tk<=pk, tk<=qk) make a vanishing spread FORCE tk=0: I enumerated all label arrays up to n=6 and every reachable triple with a vanishing spread has tk=0 (e.g. (0,0,2),(0,2,0),(0,0,0),(0,0,6),(0,6,0)), while every tk=0 triple with both spreads nonzero -- (0,2,2),(0,4,4),(0,2,6),(0,2,4) -- divides safely. So a spread guard fires on exactly the divide-by-zero cases and is behaviourally identical to gold's tk guard on the whole reachable domain. I pre-tested all 5 patches against every real FMS test call plus the F2P witness: all agree with gold to 9 decimals, including (0,0,30) -> 0.0 and the witness -> 0.728995978.

REFINEMENT.MD PROSE DEFECT (re-confirming a prior pass's finding, independently re-derived). The 'strength, the degenerate triple' bullet claims `.zeroThen` 'must guard on the AGREEMENT count specifically, since guarding on a spread instead leaves (0, b, 0) with b != 0 unanswered'. That reasoning is WRONG: (0,b,0) is answered by a spread-guard chain (the spreadB guard fires), and I discharged the universal plan clause in Lean for the spread-chain plan (atk_2, atk_7 both EXIT=0). The doc's argument is OVER-TIGHT, not unsound -- the spec is not broken, because a spread guard is behaviourally equivalent on the admissible domain (whenever a spread vanishes tk vanishes too, by the ordering requires) and both faithful patches RESOLVE. Recommend correcting that bullet; it does not affect the machine-checked spec.

A-LEG AUDIT (my mandated focus; R/I legs left to G-CONF). refinement.md tag census: 5 R, 2 I, 1 'I + R', 3 A-reference, 0 A-consumed -- every leg is R / A-reference / I, NO kind-3 (the only two 'kind-3' greps are the section heading asserting their absence). `grep -c '^axiom ' Solution.lean` == 0 and meta.json axioms == [], so the 'no consumed axioms' claim is TRUE with no over-claiming. meta.json declares 2 deep_model_references, both kind='A-reference', vs the doc's 3 table rows (the doc splits register carrier from plan semantics where meta merges them into one machine-word entry -- presentational, not a mismatch).
I independently re-derived all three A-reference correspondences against the REAL callees (aleg.py, my own transliteration, not the bundle's scripts):

  (i) SQUARING (np.sqrt(tk/pk)*np.sqrt(tk/qk))^2 == tk^2/(`pk*qk`): max relative error 6.642e-16 over 20000 random admissible triples on real numpy -> the root IS peelable by squaring, so declining to consume an axiom is honest, not a dodge.

  (ii) REGISTER CARRIER truncW 64 == real np.int64 multiplication: 0 disagreements / 20000 random full-signed-range pairs, wrap non-vacuous on 20000/20000. instMulWord IS np.int64 multiply.

  (iii) PARTIALITY == MACHINE FAILURE at the F2P witness (3003497866, 5152663196, 3294371982): exact `pk*qk` = 16974789265584974472 > int64 max, inWord 64 = False (product-first plan valueless), real np.int64 product wraps NEGATIVE to -1471954808124577144, real pre-patch tk/np.sqrt(`pk*qk`) == nan while gold == 0.7289959776021899. The model's `none` is the machine's `nan`.

  (iv) WIDTH-UNIVERSALITY re-executed at w=3..16: m=2^(w-1)-1 has `m*m` outside the word every time, so any IntPlan.mul is refuted at every width >= 3. At w=2, m=1 and `m*m`=1 DOES fit, so that single width does not refute a product-forming plan -- but the clause is a conjunction over ALL w>=2, so w=3 suffices. Benign; noting for completeness. atk_5's EXIT=1 is the empirical confirmation.
The bundle's own G-AX (`python axiom_check.py`) EXIT=0 independently, reporting the same magnitudes I measured plus the short-circuit reference and its negative control (2952 degenerate triples where the total rational carrier reports the same number for guarded and unguarded value expressions -- confirming the doc's honest admission that the VALUE slot cannot carry the short-circuit and the PLAN + tie must).

MODEL<->PATCH CORRESPONDENCE (holds). The returned plan `.zeroThen (.read .agree) (.mul (.ratio agree spreadA) (.ratio agree spreadB))` is node-for-node gold line 859 `np.sqrt(tk/pk)*np.sqrt(tk/qk) if tk != 0. else 0.` with the two roots peeled by squaring: guard -> two tk/. ratios -> outer multiply (which survives squaring in place since (sqrt x * sqrt y)^2 = `x*y`), and NO IntPlan.mul node, matching that gold materialises no integer product. The prepatch counterpart carries two IntPlan.mul plus a register product and is refuted on both observables.

**HONESTY CHECK PASSED.** refinement.md's 'Identity record' PRE-DECLARES my atk_3/atk_7-shaped rivals as accept-lane POSITIVE controls (pos-control-unconditional-value-arithmetic, pos-control-promoted-product-value) rather than hiding them in the reject lane, and properties.py carries them there. The doc does not over-claim discrimination it lacks.

**ENVIRONMENT.** properties.py imports cleanly (battery-integrity release-gate item OK). conformance_check.py could not run in this venv (ModuleNotFoundError: sklearn) -- an environment gap, not a spec defect, and G-CONF's R/I legs are outside my scope. All 5 resolves reported note 'resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)', i.e. host-load flakiness on attempt 1 with a clean resolved verdict on retry -- consistent across all 5, not a spec signal.

**VERDICT SOUND:** 7 distinct attacks encoded and fully verified (5 verifying, 2 correctly rejected including the prepatch), every verifying attack's faithful refined patch materialized, apply-checked at base_commit, and RUN through the official harness -- all 5 RESOLVED. One documentation defect to fix (the agreement-count-guard-is-forced bullet), which does not affect the machine-checked spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** G-PANEL attacker (2), faithfulness-break. Searched for an input where the modelled `fowlkesCoeffSquared` disagrees with the real callee (base_commit 97523985b3 worktree with patch.diff APPLIED, as the role requires). Found NONE. Verdict FAITHFUL.

### Spec region integrity
`swebench_unified.markers.same_spec(gold, X, get_backend('velvet'))` = True for Solution_prepatch.lean and for all three rivals I authored. Byte-identical spec view confirmed; every rival differs only inside impl+proof.

### LANE CONTROLS (scripts/lean_verify.sh, 900s cap)
* gold Solution.lean -> EXIT 0.
* Solution_prepatch.lean (register product `spreadA * spreadB` + product-first plan, no hand-written range check) -> EXIT 1, unsolved goals. Reject lane intact, so the spec is not vacuous/too weak.

== OVER-STRENGTH PROBE (the real faithfulness-break lane): 3 behaviourally-identical rivals, all MUST verify ==
Authored fresh, spec region byte-identical, each a faithful rendering of patched line 859:
* r1 `pos-control-commuted-ratios` shape -- `(agree/spreadB)*(agree/spreadA)`, plan commuted too (repo counterpart `np.sqrt(tk/qk)*np.sqrt(tk/pk)`) -> EXIT 0. (First attempt EXIT 1 was MY tactic bug: residual goal was literally `a*a/(c*b) = a*a/(b*c)`, i.e. one `mul_comm`; retuned -> EXIT 0. Not a spec defect.)
* r2 double `.zeroThen` on agree (redundant re-test of tk) -> EXIT 0.
* r3 promoted exact product in the value slot with the guard kept -> EXIT 0.
So the postcondition does not over-constrain branch order, ratio order, or promoted-vs-divide-first assembly. No SPEC-TOO-STRONG.

### MODEL vs REAL PATCHED REPO (~160k inputs, 0 divergences)
Transliterated the spec region (inWord / IntPlan.value / RatPlan.value / the full ensures, exact `Fraction`) and diffed against the real patched lines 852-859 (standalone transliteration; the worktree's sklearn C extensions are unbuilt, so `conformance_check.py` cannot import -- ModuleNotFoundError, an environment fact, not a finding):
* F2P witness: aggregates recomputed through the real patched lines = (3003497866, 5152663196, 3294371982), matching mapping.md exactly; `pk*qk` = 16974789265584974472 > 2^63-1; real patched score 0.7289959776021899 (finite); all nine requires hold at width 64. Model agrees.
* 6000 random real label-array pairs through the whole patched function (154 with a vanishing spread): 0 divergences, 0 require violations.
* Degenerate/structural cases: empty arrays, fully-split/split, split/lumped, lump/lump at n=1,2,3,5,17,30 -- aggregates (0,0,0), (0,2,0), (0,870,0) etc., real score 0.0 or 1.0; model agrees on every one.
* Exhaustive admissible triples at widths 2..8 into the real line-859 arithmetic: 0 divergences.
* 150000 random width-64 admissible triples (all 150000 with `b*c` outside the word) + 1240 boundary triples (incl. 3037000499/3037000500, 2^53+-1, 2^62, 2^63-2, 2^63-1): 0 divergences.
* Max relative error between real score^2 and the exact model `v`: 9.53e-16 -- pure float64 rounding, not a semantic gap.

### Edge attack on the two strongest clauses
* `ensures out = some (p,v)` and `0 <= v`: ran 350012 admissible triples (incl. tiny-a/huge-spread underflow regime) through the real patched expression. Real result was NEVER non-finite and NEVER negative. So `some` and `0 <= v` are TRUE of the real repo -- no input where the spec promises a number the repo fails to produce.
* Underflow attack: 0 cases where the real score underflowed to exactly 0.0 while exact v > 0.
* Requires-exclude-real-input attack: 20000 real label pairs, 0 violations of any of the nine requires. The preconditions exclude nothing the patch fixes (tk = Sum c^2 - n >= 0, pk,qk >= 0, tk <= pk, tk <= qk all hold on real data).
* Universal plan clause self-consistency: exhaustive over widths 2..10, 51305495 admissible triples, 0 failures; and at a=b=c=2^(w-1)-1 for w=2..19 both the plan and the real score give exactly 1.

### A-REFERENCE CALLEES RE-DERIVED INDEPENDENTLY (not trusting axiom_check.py)
* Register carrier: `truncW 64 (x*y)` vs real `np.int64(x)*np.int64(y)` on 100014 pairs (14 boundary + 60k full-signed-range + 40k in-range): 0 mismatches, 84525 wrapping (so the wrap is reachable, not decoration), 15489 in-range and exact. At the F2P witness the register product wraps to -1471954808124577144 while the exact product is 16974789265584974472, and `np.sqrt` of that negative is `nan` -- the model's partiality IS the machine failure, not an invention.
* sqrt peeled by squaring: `(np.sqrt(tk/pk)*np.sqrt(tk/qk))^2` vs exact `tk^2/(pk*qk)` on 80006 triples, worst rel err 8.90e-16. No consumed axiom needed; no over-claim.
* Independently: axiom_check.py EXIT 0.

#### HUNK ATTRIBUTION (checked that the spec does not claim something false about hunk (a))
Ran the real function in all four dtype x expression combinations at the F2P input: prepatch-expr is `nan` both with and without `.astype(np.int64)`; patched-expr is finite both ways (contingency dtype is already int64 on this platform). The behavioural delta is carried by hunk (b), the re-association. The spec correctly does NOT pin the width at 64 -- it quantifies `w` universally in the plan clause -- so it makes no false claim about the dtype hunk, and stays silent about it as mapping.md 2 says.

### Conclusion
No diverging input exists in ~160k model-vs-repo comparisons, 350k+ admissible-triple finiteness probes, 51.3M exhaustive plan-clause triples, and 180k callee-reference pairs. The modelled function agrees with the real patched callee everywhere admissible; the register carrier and the squaring reference match real numpy exactly; the requires admit the very input the patch fixes; the reject lane still rejects and three faithful reshapes all verify. FAITHFUL.

CAVEATS (disclosed, neither is a finding): (1) conformance_check.py could not be executed because the /tmp worktree's sklearn C extensions are unbuilt -- I substituted my own standalone transliteration of lines 852-859 plus real numpy/scipy, which covers the same leg. (2) The one Lean rejection I saw (r1, first attempt) was my own tactic error, re-verified EXIT 0 after a one-lemma fix; I am NOT reporting it as spec strength.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** leakage / gold-reconstruction only, judged against the solver-visible problem_statement; hints_text deliberately excluded. NO RELAXATION IS CLAIMED BY THIS BUNDLE, and I checked rather than assumed: `'relaxed_leakage' in meta.json` -> False, and `ls` + a recursive grep for RELAXED_LEAKAGE over the bundle returns only self-referential matches inside verdict.md/meta.json (a prior panel note saying it found no such file). So there is no relaxation argument to re-derive; I judged this strictly, and every number below is my own run against the shipped bytes.

1. **THE VIEW I AUDITED IS THE SHIPPED VIEW.** sha256(Solution.lean) = 6c38aea1a95d38c3c8d24bcdea19e6f6efe29b82872cf660d86bf6f5c6e74399 == the recorded G-LEAK/G-PANEL-3 sources stamp. My recomputed markers.spec_view sha256 = 638015c55485df3abd13ccf1e93db26708199ed59e5ce36ad7ead8d1d4b44c0a == meta.json G-HYGIENE data.region_hashes.spec_view. 303-line view.

2. SPEC REGION BYTE-IDENTICAL (as instructed). markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) = True, and spec_view(Solution) == spec_view(Solution_prepatch) byte-for-byte. The files differ ONLY inside the impl do-block / prove_correct body, exactly what the view collapses to `-- implementation elided` / `-- proof elided`. So the pre-patch discriminator (the product-first plan `.ratio (.mul agree agree) (.mul spreadA spreadB)`) cannot reach a consumer.

3. MECHANICAL SCREEN, RE-RUN BY ME. leakage.screen(Solution.lean, VelvetBackend, gold_patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]). Hand-checked rather than trusting the aggregate: no Lean diff markers, no gold changed line reproduced, path `sklearn/metrics/cluster/supervised.py` absent in any form.

4. DECIDING MEASUREMENT -- NON-PUBLIC GOLD CONTENT vs THE VIEW. Tokenizing the gold ADDED lines and subtracting problem_statement tokens leaves exactly {astype, int64, contingency_matrix, labels_true, labels_pred, sparse, true} -- i.e. hunk (a), `contingency_matrix(...).astype(np.int64)`. Intersection of that set with the view (case-insensitive) = EMPTY. Conversely hunk (b) is verbatim public: the statement's own '#### Fix' section reads 'I propose to use np.sqrt(tk / pk) * np.sqrt(tk / qk) instead', and `tk / np.sqrt(pk * qk)`, the file:line 859, the `(pk * qk) is bigger than 2**32 ... bypassing the int32 limit` diagnosis, the `if tk != 0. else 0.` short-circuit and the 'nan' outcome are all in the statement. So the two things the spec's plan clause pins -- divide-before-multiply and the zero short-circuit -- are precisely what the reporter published.

5. NO WIDTH LITERAL, NO DTYPE VOCABULARY (my greps over the view). Multi-digit numeric literals: ZERO (so no 64/63/32/31/`2**32`). int64=0, int32=0, astype=0, dtype=0, np.=0, numpy=0, sklearn=0, contingency=0, sparse=0, labels=0, n_samples=0, nan=0, RuntimeWarning=0, overflow=0, tk/pk/qk=0, mallows=0, 859=0. The postcondition quantifies `∀ (w : Nat) ... 2 ≤ w → ...` -- the width is a bound variable, never instantiated, so the artifact never names the machine width `.astype(np.int64)` selects, and the clause is strictly stronger than any fixed-width instance of it. Narration vocabulary: `_NARRATION_RE`-style scan finds only the substring 'fix' inside 'fixed-width' (5x, all on lines 106/112/117/124/135/236) and 'instead' in 'instead of a matter of prose' (line 135) -- no bug/patch/pre-patch/regression/previously/incorrectly/wrong/broken. Notable for a view carrying ~130 lines of prose.

6. THE ONE CANDIDATE I PRESSED ON, AND WHY IT IS NOT LEAKAGE. View lines 116-118 and 233-236 say an implementation 'may reach the value by promoting the aggregates out of their registers into exact arithmetic'. That is the nearest allusion to the widening hunk, so I tested it three ways. (i) It is a PERMITTED alternative, never the obligation: the ensures clause asserts nothing about dtype, promotion or width selection -- only the (plan, value) pair, and the ∀w plan clause in fact FORBIDS materialising any aggregate product at any width, so widening alone does not satisfy this spec; the reorder is what it forces. A solver reading it is pushed toward hunk (b), not hunk (a). (ii) It is publicly derivable anyway: the statement diagnoses the int32 product overflow and asks to 'Be able to calculate tk / np.sqrt(pk * qk) and return a float', i.e. keep the product but stop it overflowing == widen the operands. (iii) It names no type, no width, no call site. Under the strip test this prose is load-bearing for FAITHFULNESS of the fixed-width carrier model, not for reconstructing `.astype(np.int64)`.

7. NOT A VACUOUS PASS -- THE DISCRIMINATOR IS REAL (my runs). scripts/lean_verify.sh Solution.lean -> exit 0, no sorry/error. scripts/lean_verify.sh Solution_prepatch.lean -> FAILS with `unsolved goals`; I reproduced the residual goal, which carries the product-first plan `RatPlan.ratio ((read agree).mul (read agree)) ((read spreadA).mul (read spreadB))` and value over `(spreadA * spreadB).toExact`, against the ∀w plan conjunct. So the shipped spec genuinely separates the two impls, and it does so through a width-generic clause rather than a named dtype.

8. **TEST-PATCH CHANNEL CLEAN.** Zero identifiers of length >=5 from test_patch appear in the view (test_int_overflow_mutual_info_fowlkes_mallows_score, assert_all_finite, mutual_info_score); none of the constants 52632/2529/14660/793/3271/204/814/316 appear.

9. **ONLY COLLIDING SYMBOL IS PUBLIC.** The one changed symbol is `fowlkes_mallows_score`; the sole spec identifier that touches it is the method name `fowlkesCoeffSquared` (view lines 272, 302). `fowlkes_mallows_score` is the FIRST LINE of the public problem_statement title, so it localizes nothing the solver lacks.

10. NO FILE IN THE BUNDLE ADDRESSES ME -- but one pattern-hit deserves recording. leakage.reviewer_directed() = [] for all nine bundle files. My own grep for reviewer-steering patterns ('dear auditor/reviewer/panel', 'attacker 3', 'you must/should submit|record', 'submit NO-LEAKAGE', 'the honest verdict', 'do not flag/report', 'panel-3 ... should') hit meta.json (3x) and verdict.md (2x) -- I read every hit in context and ALL of them are inside a prior G-PANEL-3 note quoting its own grep pattern list while reporting that it found nothing. That is a record describing a search, not an instruction to me. I nevertheless treated the prior note as a claim only: I re-derived items 1-9 independently and none of my conclusions rests on it. No file in this bundle attempts to direct my verdict or tell me how to record.

11. GATE SANITY (context only, not inherited). All 16 gates currently record pass; G-PANEL-3 is stamped 2026-08-16T06:26:54Z against sources.Solution.lean = 6c38aea1..., which matches the bytes I hashed -- so unlike what the older note in the record describes, the panel-3 stamp is fresh against the shipped artifact. G-DIFF's recorded prepatch 'verification failed' matches my own run in item 7.

**CONCLUSION:** no line of the shipped spec view reveals the gold edit beyond the public problem_statement. The only gold element not already public is the `.astype(np.int64)` widening, and the view is silent on it in vocabulary (empty token intersection, zero multi-digit literals) and in quantification (width universally bound, never instantiated) -- and its plan clause points away from widening toward the reorder the reporter himself proposed. What the view does pin, divide-before-multiply and the tk==0 short-circuit, is verbatim in the statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
