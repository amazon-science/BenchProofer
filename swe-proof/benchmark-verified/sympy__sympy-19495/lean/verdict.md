# P2 adversarial audit — sympy__sympy-19495

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_17.lean`, `atk_18.lean`, `atk_R1.lean`, `atk_R2.lean`, `atk_R3.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 21 same-spec attacks run against the CURRENT Solution.lean (sha256 e49826469d9e...). 14 wrong impls were all REJECTED with genuine mkSet-argument residual goals; 7 inert/well-typed probes VERIFIED with clean axioms and ALL SEVEN resolved=TRUE under the official harness (F2P 1/1 test_subs_CondSet, P2P 8/8), matching the gold harness-health control. The prior pass's three breaking attacks (mkMemberSet old (mkSet ...), subsSet (mkSet ...) old new, mkSet new cond' base') are now Lean 'Application type mismatch' errors: the AsmSet terminal-carrier repair AND the SymE binding-position repair have both landed, closing the SetE-closed-under-mkSet hole that produced the recorded BROKEN verdict.
```

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,8 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  if isTrue cond' then
+    return mkMemberSet new base'
   return mkSet cs.sym cond' base'
 -- impl-end
 
@@ -196,6 +198,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,8 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  if isTrue cond' then
+    return mkSet cs.sym cond' cs.base
   return mkSet cs.sym cond' base'
 -- impl-end
 
@@ -196,6 +198,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,8 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  if old == new then
+    return mkSet cs.sym cs.cond cs.base
   return mkSet cs.sym cond' base'
 -- impl-end
 
@@ -196,6 +198,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,7 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
-  return mkSet cs.sym cond' base'
+  return mkSet cs.sym cond' (subsSet base' old new)
 -- impl-end
 
 -- proof-start
@@ -196,6 +196,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -187,8 +187,7 @@
 -- impl-start
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
-  let base' := subsSet cs.base old new
-  return mkSet cs.sym cond' base'
+  return mkSet cs.sym cond' cs.base
 -- impl-end
 
 -- proof-start
@@ -196,6 +195,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -186,7 +186,7 @@
 
 -- impl-start
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
-  let cond' := subsCond cs.cond old new
+  let cond' := subsCond cs.cond new old
   let base' := subsSet cs.base old new
   return mkSet cs.sym cond' base'
 -- impl-end
@@ -196,6 +196,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,7 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
-  return mkSet cs.sym cond' base'
+  return mkMemberSet new base'
 -- impl-end
 
 -- proof-start
@@ -196,6 +196,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,7 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
-  return mkSet cs.sym cond' base'
+  return mkSet (default : SymE) cond' base'
 -- impl-end
 
 -- proof-start
@@ -196,6 +196,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,7 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
-  return mkSet cs.sym cond' base'
+  return mkSet ⟨old.tag⟩ cond' base'
 -- impl-end
 
 -- proof-start
@@ -196,6 +196,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 10 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -187,7 +187,7 @@
 -- impl-start
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
-  let base' := subsSet cs.base old new
+  let base' := subsSet cs.base new old
   return mkSet cs.sym cond' base'
 -- impl-end
 
@@ -196,6 +196,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 11 — `atk_18.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -186,7 +186,7 @@
 
 -- impl-start
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
-  let cond' := subsCond cs.cond old new
+  let cond' := subsCond cs.cond (symExpr cs.sym) new
   let base' := subsSet cs.base old new
   return mkSet cs.sym cond' base'
 -- impl-end
@@ -196,6 +196,12 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
-  rfl
+  intro cs old new h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, bind, pure]
+  first
+  | rfl
+  | (simp_all; try rfl)
+  | (congr 1 <;> simp_all)
+  | aesop
 -- proof-end
```

Attack 12 — `atk_R1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  let _probe := mkMemberSet old (mkSet cs.sym cs.cond cs.base)
   return mkSet cs.sym cond' base'
 -- impl-end
 
```

Attack 13 — `atk_R2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  let _probe := subsSet (mkSet cs.sym cs.cond cs.base) old new
   return mkSet cs.sym cond' base'
 -- impl-end
 
```

Attack 14 — `atk_R3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,7 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
-  return mkSet cs.sym cond' base'
+  return mkSet new cond' base'
 -- impl-end
 
 -- proof-start
```

Attack 15 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,7 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  let _probe := mkMemberSet new base'
   return mkSet cs.sym cond' base'
 -- impl-end
 
```

Attack 16 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,9 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  let _p1 := subsSet base' old new
+  let _p2 := subsCond cond' (symExpr cs.sym) new
+  let _p3 := subsCond cs.cond new old
   return mkSet cs.sym cond' base'
 -- impl-end
 
```

Attack 17 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,8 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  if old == symExpr cs.sym then
+    return mkMemberSet new base'
   return mkSet cs.sym cond' base'
 -- impl-end
 
@@ -196,6 +198,11 @@
     ∀ (cs : CondSet) (old new : Expr),
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
-  intro cs old new _
+  intro cs old new h
+  have hb : (old == symExpr cs.sym) = false := by
+    simp only [beq_eq_false_iff_ne]
+    exact h
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run, hb]
   rfl
 -- proof-end
```

Attack 18 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,8 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  if mkSet cs.sym cs.cond cs.base == mkSet cs.sym cond' base' then
+    return mkSet cs.sym cond' base'
   return mkSet cs.sym cond' base'
 -- impl-end
 
@@ -197,5 +199,7 @@
       old ≠ symExpr cs.sym →
       problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
   intro cs old new _
-  rfl
+  unfold implementation_freeSubs problem_spec_freeSubs
+  simp only [Id.run]
+  split <;> rfl
 -- proof-end
```

Attack 19 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,8 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  let _b := isTrue cond'
+  let _probe := mkSet cs.sym cs.cond cs.base
   return mkSet cs.sym cond' base'
 -- impl-end
 
```

Attack 20 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,9 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  let _p := mkMemberSet (symExpr cs.sym) base'
+  let _q := mkMemberSet old cs.base
+  let _r := mkMemberSet new cs.base
   return mkSet cs.sym cond' base'
 -- impl-end
 
```

Attack 21 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,6 +188,10 @@
 def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
   let cond' := subsCond cs.cond old new
   let base' := subsSet cs.base old new
+  let c2 := subsCond (subsCond cs.cond old new) new old
+  let s2 := subsSet (subsSet cs.base old new) (symExpr cs.sym) new
+  let _p := mkSet cs.sym c2 s2
+  let _q := isTrue c2
   return mkSet cs.sym cond' base'
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**COMMANDS.** Verify: `bash scripts/lean_verify.sh $D/<f>.lean` from the repo root (never lake/lean directly), 4-at-a-time as background jobs via $D/vrun.sh. Axioms: appended `#print axioms correct_freeSubs` -> $D/ax_<f>.lean, re-verified through the same script. Resolve: `python $D/resolve_one.py <tag>` -> swebench_unified.harness.run_resolve('sympy__sympy-19495', patch, timeout=1800, retries=1); results $D/res_<tag>.json, logs $D/rlog_<tag>.txt. Patch check: `git apply --check` in a base_commit (25fbcce5b1) worktree at $D/wt_chk -- all 7 patches + gold APPLY.

### FULL MATRIX (lean exit / axioms / executed resolve):
  pc      exit 0 / no axioms                    <- POSITIVE CONTROL, non-vacuity
  gold    (harness-health control)               resolved=TRUE completed=TRUE, F2P 1/1 + P2P 8/8
  atk_10  exit 0 / no axioms / resolved=TRUE completed=TRUE  (F2P 1/1, P2P 8/8)
  atk_11  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_12  exit 0 / [propext] (in STANDARD_AXIOMS) / resolved=TRUE completed=TRUE
  atk_13  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_14  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_15  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_16  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_1   exit 1 / REJECTED -- PREPATCH BUG re-encoded (`if isTrue cond' then return mkMemberSet new base'`); residual `isTrue (subsCond cs.cond old new) = true -> mkMemberSet new (subsSet cs.base old new) = mkSet cs.sym ...`
  atk_2   exit 1 / REJECTED -- PARTIAL DOMAIN: correct in general, hands the UNSUBSTITUTED base on the collapse sub-domain
  atk_3   exit 1 / REJECTED -- BOUNDARY on the guard's own equality (`if old == new` echo of the input)
  atk_4   exit 1 / REJECTED -- CONTROL-FLOW-EFFECT: double substitution (assumes an idempotence the model does not grant)
  atk_5   exit 1 / REJECTED -- UNGROUNDED ORACLE ECHO: drops the base substitution entirely
  atk_6   exit 1 / REJECTED -- ARGUMENT SWAP at the condition (subsCond cs.cond new old)
  atk_7   exit 1 / REJECTED -- prepatch rebinding UNCONDITIONALLY (mkMemberSet new base' in the return)
  atk_8   exit 1 / REJECTED -- MINTED SymE LITERAL in the binding position (`mkSet (default : SymE) ...`)
  atk_9   exit 1 / REJECTED -- CROSS-CARRIER .tag COERCION puts `old` in the binding position (`mkSet <old.tag> ...`)
  atk_17  exit 1 / REJECTED -- base substituted in the REVERSED direction (subsSet cs.base new old)
  atk_18  exit 1 / REJECTED -- condition substituted on the BOUND VARIABLE instead of `old`
  atk_R1  exit 1 / TYPE ERROR (Application type mismatch @191:32) -- prior pass's BREAKING atk_2 `mkMemberSet old (mkSet cs.sym cs.cond cs.base)`
  atk_R2  exit 1 / TYPE ERROR (Application type mismatch @191:24) -- prior pass's BREAKING atk_8 `subsSet (mkSet ...) old new`
  atk_R3  exit 1 / TYPE ERROR (Application type mismatch @191:15) -- prior pass's atk_15 `mkSet new cond' base'` (non-Symbol ARG-1)

EVERY rejection is a GENUINE SPEC RESIDUAL, not a tactic artifact: each of atk_1..atk_9/17/18 was built with the strong tactic `unfold; simp only [Id.run, bind, pure]; first | rfl | (simp_all; try rfl) | (congr 1 <;> simp_all) | aesop` and each exposed a concrete mkSet-argument disagreement in the error text (quoted in $D/vlog_<t>.txt). No attack retired on an unfolding weakness.

**THE RECORDED BROKEN VERDICT IS STALE AND THE HOLE IS REPAIRED.** meta.json's G-EQ/G-PANEL-1 fail cites sources.Solution.lean = c6e47262bea3fd99...; the current file is e49826469d9e6c66.... In the current bytes `mkSet : SymE -> Cond -> SetE -> AsmSet` and `mkMemberSet : Expr -> SetE -> AsmSet`, with AsmSet a projection-free TERMINAL carrier that no routine consumes. That breaks the SetE-closed-under-mkSet composition the prior pass exploited: I re-encoded all three of its breaking attacks verbatim (atk_R1/R2/R3) and all three are now Application type mismatch errors. This is exactly the 'MINIMAL REPAIR DIRECTION' the prior verdict.md advised, and it landed.

EXHAUSTIVE VOCABULARY RE-ENUMERATION (the measurement that located the prior defect, redone against the CURRENT carriers). I instrumented the gold-patched `_eval_subs` and ran the F2P + 8 P2P tests: 14 calls, exactly 4 take the modeled branch (T1 ConditionSet(x,x<y,{y,z}) subs y->w; T2 ConditionSet(n,n<x,[0,oo)) subs x->p; T3 the (-oo,0] variant; T4 the F2P ConditionSet(x,Contains(y,[-1,1]),ImageSet(..asin(y)..)) subs y->1/3) -- $D/instr.py, reproducing mapping.md's claim. Then I enumerated EVERY well-typed composition of the current vocabulary at those 4 triples with the Cond and SetE pools CLOSED under subsCond/subsSet over all three Expr inhabitants {old, new, symExpr cs.sym}: $D/enum_vocab.py (depth 2) = 406 terms / 0 RAISES; $D/enum_deep.py (depth 3, plus mkSet over the full closed pools and mkMemberSet over all Expr x SetE) = 699 terms / 0 RAISES. The prior pass's closed-pool run reported 26 raises; under the AsmSet repair the raising family is no longer expressible, because mkSet's result cannot re-enter any consumer position.

RESIDUAL-GAP PROBE ($D/enum_residual.py). mapping.md admits ONE residual it cannot type away: 'a base set whose ELEMENT is itself a set' (ConditionSet(x,x<1,FiniteSet(Interval(0,1))) raises SympifyError). I tested reachability directly -- closing the SetE pool under subsSet to depth 3 from cs.base over all Expr pairs at all 4 triples yields 0/8 set-of-sets or condition-restricted inhabitants, and closing the Cond pool likewise yields 0/30 with a ConditionSet anywhere in the preorder traversal. So the admitted residual is genuinely unreachable from the impl's own inputs, and the file's justification for recording rather than typing it ('no modeled routine produces such a base from one that is not already such a base') holds as measured.

REFINEMENT.MD AUDIT (docs/architecture.md §5 legs). WELL-FORMED. 3 legs, all tagged **A-reference**, no kind-3 (changed-inexpressible) leg, no consumed `axiom <callee>_prop`, and G-AX is a documented skip stub consistent with the file (I confirmed independently that every closing proof depends on NO axioms at all bar propext in atk_12, so there is nothing for G-AX to check). R/I legs left to G-CONF per instruction. I re-derived the A-leg CORRESPONDENCE against the real callees in-process ($D/aleg_audit.py, gold-patched worktree at base_commit):
  * op1 subsCond <-> self.condition.subs(old,new): the genuine Basic.subs at the Boolean component; result stays a Boolean at all 4 triples, 0 carrier escapes / 8.
  * op2 subsSet <-> self.base_set.subs(old,new): the same Basic.subs at the Set component; result stays a Set, 0 escapes / 8.
  * op3 mkSet <-> self.func(self.sym, cond, base) = ConditionSet.`__new__`: the shadow cs.func(cs.sym, cs.condition.subs(old,new), cs.base_set.subs(old,new)) equals the real cs.subs(old,new) under STRICT == at 4/4 triples. The SymE domain claim holds in BOTH directions as refinement.md asserts: 672 (Symbol, cond, base) triples -> 0 raises, while 864 non-Symbol-arg1 triples -> 589 raises (588 ValueError 'non-symbol dummy not recognized in condition' + 1 BadSignatureError). So the carrier is neither unsound nor narrower than the real domain.
  * op4 mkMemberSet <-> ConditionSet(v, Contains(v, base), base) (prepatch-only): 192 (v, base) pairs over SetE inhabitants -> 192 ok / 0 raises, confirming the fusion is total on the base sets this branch ranges over, which is what makes G-DIFF a real discrimination test rather than an elaboration failure. G-DIFF's recorded 'Solution_prepatch.lean: verification failed' is corroborated by my atk_1, an independent re-encoding of the same bug that I built and ran myself (exit 1 with the mkMemberSet-vs-mkSet residual).
The terminal-carrier justification also checks out on the Python side: ConditionSet(x,S.true,Interval(0,3)) returns a bare Interval(0,3) and .sym raises AttributeError, ConditionSet(x,S.false,...) returns EmptySet likewise -- so a result carrier with projections would have been unsound, exactly as refinement.md point 1 argues.

**HARNESS-HEALTH CONTROL.** patch_gold.diff (byte-identical to the frozen row's reference patch) through the SAME run_resolve path -> resolved=TRUE completed=TRUE, F2P 1/1 + P2P 8/8. So resolve=TRUE is not the default outcome of a degraded host in the other direction either: I additionally confirmed each of the 7 attack patches locally ($D/localtest.py, per-test pytest in a fresh base_commit worktree with patch + test_patch) and all 7 gave F2P 1/1 + P2P 8/8 BEFORE the Docker runs, so the local prediction and the official harness agree 7/7.

WHY THE 7 VERIFYING ATTACKS ARE NOT A FINDING. Each adds only inert statements whose faithful transliteration is a DEFINED python call at every tested triple, so verify=>correct is upheld rather than violated: atk_10 evaluates the deleted expression ConditionSet(new, Contains(new, base), base) and discards it; atk_11 adds three discarded substitutions including one on the bound variable; atk_12 adds a branch on the spec's OWN guard (old == self.sym), dead in this branch and discharged from the hypothesis; atk_13 branches on equality of two ASSEMBLED sets with identical arms; atk_14 probes `cond is S.true` and assembles at the unsubstituted triple, discarding both; atk_15 exercises mkMemberSet over BOTH pools (3 values x 2 base sets); atk_16 builds depth-2 nested Cond/SetE values and assembles at a mixed triple. These are the shapes that BROKE the prior revision -- under the AsmSet repair the ones that raise are type errors and the ones that remain expressible are total.

RECORD-HYGIENE FINDING (advisory, not a spec defect; does not affect this verdict). meta.json's TOP-LEVEL blocks are stale relative to the current Solution.lean, even though the per-gate `sources` stamps for G-HYGIENE/G-CONF/G-DIFF/G-GOLD/G-MUT/G-AX all correctly cite e49826469d9e...: (a) `opaque_callees` still declares `mkSet : SymE -> Cond -> SetE -> SetE` and `mkMemberSet : Expr -> SetE -> SetE`, i.e. the PRE-REPAIR signatures whose SetE result is the very hole that was closed -- the current file returns AsmSet in both; (b) the same block's carrier list omits AsmSet and its measured counts ('1980 raises in 39016 well-typed compositions ... against 0 raises in 6516') do not match the current model; (c) top-level `region_hashes` disagrees with the current file in 5 of 6 regions (axioms 718580b8 vs recorded 3dd0ac6d, impl c7f5d81d vs 3682868a, post-conditions a8d34bb7 vs e687c64f, pure fc311a57 vs 06dd1cad, spec_view c433efc5 vs ac2b8709; only `proof` matches) -- these are the values from the revision the FAILING G-EQ/G-PANEL-1 stamps were computed against. So the recorded BROKEN verdict for this cell describes bytes that no longer exist, and both it and the stale metadata blocks should be re-derived; the current spec view had never been G-EQ-judged before this run.

**VERDICT:** SOUND. 21 same-spec attacks (>= the required 5), 14 correctly rejected on genuine residuals -- including the prepatch bug re-encoded (atk_1) and the partial-domain / boundary / control-flow-effect / ungrounded-oracle-echo classes the protocol names -- and every one of the 7 impls whose proof closed with clean axioms had its faithful refined patch MATERIALIZED, checked with `git apply --check` at base_commit, and RUN through the official run_resolve harness: 7/7 resolved=TRUE completed=TRUE. No verifying impl fails to resolve, so verify=>correct holds on these bytes.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_17.lean`, `atk_18.lean`, `atk_R1.lean`, `atk_R2.lean`, `atk_R3.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 21 same-spec attacks run against the CURRENT Solution.lean (sha256 e49826469d9e...). 14 wrong impls were all REJECTED with genuine mkSet-argument residual goals; 7 inert/well-typed probes VERIFIED with clean axioms and ALL SEVEN resolved=TRUE under the official harness (F2P 1/1 test_subs_CondSet, P2P 8/8), matching the gold harness-health control. The prior pass's three breaking attacks (mkMemberSet old (mkSet ...), subsSet (mkSet ...) old new, mkSet new cond' base') are now Lean 'Application type mismatch' errors: the AsmSet terminal-carrier repair AND the SymE binding-position repair have both landed, closing the SetE-closed-under-mkSet hole that produced the recorded BROKEN verdict.
```

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 21 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_R1.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_R2.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_R3.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 20 — `atk_15.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 21 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**COMMANDS.** Verify: `bash scripts/lean_verify.sh $D/<f>.lean` from the repo root (never lake/lean directly), 4-at-a-time as background jobs via $D/vrun.sh. Axioms: appended `#print axioms correct_freeSubs` -> $D/ax_<f>.lean, re-verified through the same script. Resolve: `python $D/resolve_one.py <tag>` -> swebench_unified.harness.run_resolve('sympy__sympy-19495', patch, timeout=1800, retries=1); results $D/res_<tag>.json, logs $D/rlog_<tag>.txt. Patch check: `git apply --check` in a base_commit (25fbcce5b1) worktree at $D/wt_chk -- all 7 patches + gold APPLY.

### FULL MATRIX (lean exit / axioms / executed resolve):
  pc      exit 0 / no axioms                    <- POSITIVE CONTROL, non-vacuity
  gold    (harness-health control)               resolved=TRUE completed=TRUE, F2P 1/1 + P2P 8/8
  atk_10  exit 0 / no axioms / resolved=TRUE completed=TRUE  (F2P 1/1, P2P 8/8)
  atk_11  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_12  exit 0 / [propext] (in STANDARD_AXIOMS) / resolved=TRUE completed=TRUE
  atk_13  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_14  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_15  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_16  exit 0 / no axioms / resolved=TRUE completed=TRUE
  atk_1   exit 1 / REJECTED -- PREPATCH BUG re-encoded (`if isTrue cond' then return mkMemberSet new base'`); residual `isTrue (subsCond cs.cond old new) = true -> mkMemberSet new (subsSet cs.base old new) = mkSet cs.sym ...`
  atk_2   exit 1 / REJECTED -- PARTIAL DOMAIN: correct in general, hands the UNSUBSTITUTED base on the collapse sub-domain
  atk_3   exit 1 / REJECTED -- BOUNDARY on the guard's own equality (`if old == new` echo of the input)
  atk_4   exit 1 / REJECTED -- CONTROL-FLOW-EFFECT: double substitution (assumes an idempotence the model does not grant)
  atk_5   exit 1 / REJECTED -- UNGROUNDED ORACLE ECHO: drops the base substitution entirely
  atk_6   exit 1 / REJECTED -- ARGUMENT SWAP at the condition (subsCond cs.cond new old)
  atk_7   exit 1 / REJECTED -- prepatch rebinding UNCONDITIONALLY (mkMemberSet new base' in the return)
  atk_8   exit 1 / REJECTED -- MINTED SymE LITERAL in the binding position (`mkSet (default : SymE) ...`)
  atk_9   exit 1 / REJECTED -- CROSS-CARRIER .tag COERCION puts `old` in the binding position (`mkSet <old.tag> ...`)
  atk_17  exit 1 / REJECTED -- base substituted in the REVERSED direction (subsSet cs.base new old)
  atk_18  exit 1 / REJECTED -- condition substituted on the BOUND VARIABLE instead of `old`
  atk_R1  exit 1 / TYPE ERROR (Application type mismatch @191:32) -- prior pass's BREAKING atk_2 `mkMemberSet old (mkSet cs.sym cs.cond cs.base)`
  atk_R2  exit 1 / TYPE ERROR (Application type mismatch @191:24) -- prior pass's BREAKING atk_8 `subsSet (mkSet ...) old new`
  atk_R3  exit 1 / TYPE ERROR (Application type mismatch @191:15) -- prior pass's atk_15 `mkSet new cond' base'` (non-Symbol ARG-1)

EVERY rejection is a GENUINE SPEC RESIDUAL, not a tactic artifact: each of atk_1..atk_9/17/18 was built with the strong tactic `unfold; simp only [Id.run, bind, pure]; first | rfl | (simp_all; try rfl) | (congr 1 <;> simp_all) | aesop` and each exposed a concrete mkSet-argument disagreement in the error text (quoted in $D/vlog_<t>.txt). No attack retired on an unfolding weakness.

**THE RECORDED BROKEN VERDICT IS STALE AND THE HOLE IS REPAIRED.** meta.json's G-EQ/G-PANEL-1 fail cites sources.Solution.lean = c6e47262bea3fd99...; the current file is e49826469d9e6c66.... In the current bytes `mkSet : SymE -> Cond -> SetE -> AsmSet` and `mkMemberSet : Expr -> SetE -> AsmSet`, with AsmSet a projection-free TERMINAL carrier that no routine consumes. That breaks the SetE-closed-under-mkSet composition the prior pass exploited: I re-encoded all three of its breaking attacks verbatim (atk_R1/R2/R3) and all three are now Application type mismatch errors. This is exactly the 'MINIMAL REPAIR DIRECTION' the prior verdict.md advised, and it landed.

EXHAUSTIVE VOCABULARY RE-ENUMERATION (the measurement that located the prior defect, redone against the CURRENT carriers). I instrumented the gold-patched `_eval_subs` and ran the F2P + 8 P2P tests: 14 calls, exactly 4 take the modeled branch (T1 ConditionSet(x,x<y,{y,z}) subs y->w; T2 ConditionSet(n,n<x,[0,oo)) subs x->p; T3 the (-oo,0] variant; T4 the F2P ConditionSet(x,Contains(y,[-1,1]),ImageSet(..asin(y)..)) subs y->1/3) -- $D/instr.py, reproducing mapping.md's claim. Then I enumerated EVERY well-typed composition of the current vocabulary at those 4 triples with the Cond and SetE pools CLOSED under subsCond/subsSet over all three Expr inhabitants {old, new, symExpr cs.sym}: $D/enum_vocab.py (depth 2) = 406 terms / 0 RAISES; $D/enum_deep.py (depth 3, plus mkSet over the full closed pools and mkMemberSet over all Expr x SetE) = 699 terms / 0 RAISES. The prior pass's closed-pool run reported 26 raises; under the AsmSet repair the raising family is no longer expressible, because mkSet's result cannot re-enter any consumer position.

RESIDUAL-GAP PROBE ($D/enum_residual.py). mapping.md admits ONE residual it cannot type away: 'a base set whose ELEMENT is itself a set' (ConditionSet(x,x<1,FiniteSet(Interval(0,1))) raises SympifyError). I tested reachability directly -- closing the SetE pool under subsSet to depth 3 from cs.base over all Expr pairs at all 4 triples yields 0/8 set-of-sets or condition-restricted inhabitants, and closing the Cond pool likewise yields 0/30 with a ConditionSet anywhere in the preorder traversal. So the admitted residual is genuinely unreachable from the impl's own inputs, and the file's justification for recording rather than typing it ('no modeled routine produces such a base from one that is not already such a base') holds as measured.

REFINEMENT.MD AUDIT (docs/architecture.md §5 legs). WELL-FORMED. 3 legs, all tagged **A-reference**, no kind-3 (changed-inexpressible) leg, no consumed `axiom <callee>_prop`, and G-AX is a documented skip stub consistent with the file (I confirmed independently that every closing proof depends on NO axioms at all bar propext in atk_12, so there is nothing for G-AX to check). R/I legs left to G-CONF per instruction. I re-derived the A-leg CORRESPONDENCE against the real callees in-process ($D/aleg_audit.py, gold-patched worktree at base_commit):
  * op1 subsCond <-> self.condition.subs(old,new): the genuine Basic.subs at the Boolean component; result stays a Boolean at all 4 triples, 0 carrier escapes / 8.
  * op2 subsSet <-> self.base_set.subs(old,new): the same Basic.subs at the Set component; result stays a Set, 0 escapes / 8.
  * op3 mkSet <-> self.func(self.sym, cond, base) = ConditionSet.`__new__`: the shadow cs.func(cs.sym, cs.condition.subs(old,new), cs.base_set.subs(old,new)) equals the real cs.subs(old,new) under STRICT == at 4/4 triples. The SymE domain claim holds in BOTH directions as refinement.md asserts: 672 (Symbol, cond, base) triples -> 0 raises, while 864 non-Symbol-arg1 triples -> 589 raises (588 ValueError 'non-symbol dummy not recognized in condition' + 1 BadSignatureError). So the carrier is neither unsound nor narrower than the real domain.
  * op4 mkMemberSet <-> ConditionSet(v, Contains(v, base), base) (prepatch-only): 192 (v, base) pairs over SetE inhabitants -> 192 ok / 0 raises, confirming the fusion is total on the base sets this branch ranges over, which is what makes G-DIFF a real discrimination test rather than an elaboration failure. G-DIFF's recorded 'Solution_prepatch.lean: verification failed' is corroborated by my atk_1, an independent re-encoding of the same bug that I built and ran myself (exit 1 with the mkMemberSet-vs-mkSet residual).
The terminal-carrier justification also checks out on the Python side: ConditionSet(x,S.true,Interval(0,3)) returns a bare Interval(0,3) and .sym raises AttributeError, ConditionSet(x,S.false,...) returns EmptySet likewise -- so a result carrier with projections would have been unsound, exactly as refinement.md point 1 argues.

**HARNESS-HEALTH CONTROL.** patch_gold.diff (byte-identical to the frozen row's reference patch) through the SAME run_resolve path -> resolved=TRUE completed=TRUE, F2P 1/1 + P2P 8/8. So resolve=TRUE is not the default outcome of a degraded host in the other direction either: I additionally confirmed each of the 7 attack patches locally ($D/localtest.py, per-test pytest in a fresh base_commit worktree with patch + test_patch) and all 7 gave F2P 1/1 + P2P 8/8 BEFORE the Docker runs, so the local prediction and the official harness agree 7/7.

WHY THE 7 VERIFYING ATTACKS ARE NOT A FINDING. Each adds only inert statements whose faithful transliteration is a DEFINED python call at every tested triple, so verify=>correct is upheld rather than violated: atk_10 evaluates the deleted expression ConditionSet(new, Contains(new, base), base) and discards it; atk_11 adds three discarded substitutions including one on the bound variable; atk_12 adds a branch on the spec's OWN guard (old == self.sym), dead in this branch and discharged from the hypothesis; atk_13 branches on equality of two ASSEMBLED sets with identical arms; atk_14 probes `cond is S.true` and assembles at the unsubstituted triple, discarding both; atk_15 exercises mkMemberSet over BOTH pools (3 values x 2 base sets); atk_16 builds depth-2 nested Cond/SetE values and assembles at a mixed triple. These are the shapes that BROKE the prior revision -- under the AsmSet repair the ones that raise are type errors and the ones that remain expressible are total.

RECORD-HYGIENE FINDING (advisory, not a spec defect; does not affect this verdict). meta.json's TOP-LEVEL blocks are stale relative to the current Solution.lean, even though the per-gate `sources` stamps for G-HYGIENE/G-CONF/G-DIFF/G-GOLD/G-MUT/G-AX all correctly cite e49826469d9e...: (a) `opaque_callees` still declares `mkSet : SymE -> Cond -> SetE -> SetE` and `mkMemberSet : Expr -> SetE -> SetE`, i.e. the PRE-REPAIR signatures whose SetE result is the very hole that was closed -- the current file returns AsmSet in both; (b) the same block's carrier list omits AsmSet and its measured counts ('1980 raises in 39016 well-typed compositions ... against 0 raises in 6516') do not match the current model; (c) top-level `region_hashes` disagrees with the current file in 5 of 6 regions (axioms 718580b8 vs recorded 3dd0ac6d, impl c7f5d81d vs 3682868a, post-conditions a8d34bb7 vs e687c64f, pure fc311a57 vs 06dd1cad, spec_view c433efc5 vs ac2b8709; only `proof` matches) -- these are the values from the revision the FAILING G-EQ/G-PANEL-1 stamps were computed against. So the recorded BROKEN verdict for this cell describes bytes that no longer exist, and both it and the stale metadata blocks should be re-derived; the current spec view had never been G-EQ-judged before this run.

**VERDICT:** SOUND. 21 same-spec attacks (>= the required 5), 14 correctly rejected on genuine residuals -- including the prepatch bug re-encoded (atk_1) and the partial-domain / boundary / control-flow-effect / ungrounded-oracle-echo classes the protocol names -- and every one of the 7 impls whose proof closed with clean axioms had its faithful refined patch MATERIALIZED, checked with `git apply --check` at base_commit, and RUN through the official run_resolve harness: 7/7 resolved=TRUE completed=TRUE. No verifying impl fails to resolve, so verify=>correct holds on these bytes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK ATTACK — no divergence found between the modeled function and the real callee on the reference (base_commit 25fbcce5b1 + patch.diff APPLIED, worktree, verified `git diff` == patch.diff exactly, docstring hunks included).

**MODELED FUNCTION:** ConditionSet.`_eval_subs`(self, old, new), sympy/sets/conditionset.py:206, on the `else` branch (old != sym) with self.sym a Symbol. Post-patch body is exactly the three ops the spec states:
  cond = self.condition.subs(old, new); base = self.base_set.subs(old, new); return self.func(self.sym, cond, base)
SPEC: result = mkSet cs.sym (subsCond cs.cond old new) (subsSet cs.base old new) — an op-for-op equation, no added strength. Read against the PATCHED reference (not base), so the deleted `if cond is S.true: return ConditionSet(new, Contains(new, base), base)` special case is correctly absent from the spec rather than a drift.

**A.** DIFFERENTIAL (spec transliteration vs REAL cs.`_eval_subs`, strict ==, my own independent harness, not the bundle's):
  - pan2_19495_fuzz.py: 5 syms x 18 conds x 15 bases x 6 olds x 17 news = 111,690 in-branch cases. 0 divergences. 0 SetE carrier escapes (subsSet never left the carrier). 0 mkSet nondeterminism. 936 inputs where BOTH legs raise the identical exception (BadSignatureError / ZeroDivisionError / SympifyError) — i.e. the model's partiality matches the callee's, no case where the shadow succeeds and the real routine raises or vice versa.
  - pan2_19495_nd2.py: 48,600 cases over 18 ImageSet/Intersection/Union/Complement bases x 12 conds (incl. Symbol('lambda') collision conds) x 5 syms. 0 issues.
  - pan2_19495_nd3.py: 17,952 cases, 18 further bases incl. asin/log/sqrt/acos/atanh/gamma ImageSets. 0 issues.
  TOTAL ~178k independent in-branch inputs, 0 disagreements.

**B.** CONTROL (proves the harness discriminates, not vacuous): the same fuzz script against the UNPATCHED base (, `git checkout` of conditionset.py) reports 616 divergences, e.g. ConditionSet(x, Contains(y,Interval(0,oo)), Integers).subs(y,1/3) -> base gives EmptySet where the spec gives Integers, and the ImageSet family where base rebinds to ConditionSet(1/3, Contains(1/3, ...)). So a real divergence WOULD have been caught. This is exactly the delta the patch introduces — reporting it would have been the trap; it is not a spec defect.

**C.** THE ONE REAL OVER-STRENGTH ROUTE — mkSet nondeterminism — attacked directly and closed. The spec asserts an EQUATION between mkSet results, so it is too strong iff ConditionSet.`__new__` can mint a fresh Dummy (its rename arm) at an in-carrier argument triple. That arm fires only when the base handed to it is ITSELF a top-level ConditionSet.

I searched for a SetE-valued base (not condition-restricted) whose .subs produces a TOP-LEVEL ConditionSet: pan2_19495_top.py + nd3 over ~34 ImageSet/Intersection/Complement/Union bases x 25 substitution values found 0. Many NESTED ConditionSets do appear (e.g. Intersection(ImageSet(Lambda(n,asin(`n*y`)),Integers),Reals).subs(y,pi) -> ImageSet(Lambda(x,re(asin(`pi*x`))), ConditionSet(n,Eq(im(asin(`pi*n`)),0),Integers))) but nesting does not reach `__new__`'s `isinstance(base_set, cls)` test, and I ran the full differential + 3x-repeat determinism check on every one of those shapes: 0 mkSet-nd, 0 real-nd, 0 SPEC-DIVERGE.

The refinement's own acknowledged nondeterministic input (base = Intersection(ConditionSet(y, x+y<w, Reals), Reals)) is honestly excluded: its base IS top-level condition-restricted, so it is AsmSet, not SetE — and I confirmed no in-carrier input reaches that shape.

**D.** BRANCH GUARD (`old ≠ symExpr cs.sym` structural vs sympy's semantic `old == sym`) — the guard is the other place a spec can drift. pan2_19495_guard.py over a 13-value pool incl. Float(2.0)/Integer(2)/Rational(2,1)/Dummy('x')/positive-x against sym = x: 0 pairs where semantic == and structural identity disagree. Every Float-vs-Integer disagreement mapping.md documents needs a NON-Symbol bound variable to sit on, and the branch guard narrows sym to Symbol, so the two coincide on the modeled domain. Narrowing costs no coverage: all 4 in-branch calls the F2P+8 P2P tests make have a Symbol bound variable.

**E.** MECHANICAL:
  - scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
  - `#print axioms correct_freeSubs` -> "does not depend on any axioms" (no sorryAx, no propositional axiom about mkSet/subsCond/subsSet — congruence is genuinely the only route to the equation, so all three argument positions are load-bearing; the prepatch, which hands `new` != cs.sym in the collapse case, cannot close, and Solution_prepatch.lean indeed carries `sorry` and fails G-DIFF).
  - markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True; axioms and post-conditions regions byte-identical by diff; live region_hashes == the six recorded in meta.json G-HYGIENE (spec_view c433efc5...). Spec region is unmodified.
  - Bundle conformance_check.py re-run in-process against the patched worktree: legs_passed=5/5, LEG 1 ran=80299 disagreements=0 collapse-inputs=959 outside-carriers=0 escapes cond=0 base=0 — the bundle's own numbers reproduce.
  - F2P test_subs_CondSet + P2P (test_CondSet, test_dummy_eq, test_contains, test_free_symbols) on the reference: 7 passed. Reference is the resolved behavior.

Spec is neither too strong nor drifted: it is a faithful op-for-op equation on a domain where every modeled callee is total and deterministic, and the corner case it forbids (rebinding to `new`) is precisely the bug the patch removes.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MEASUREMENTS I RAN (nothing inherited; the stamped G-PANEL-3 pass and the prior panel note in verdict.md are BOTH stale for these bytes -- see item 8).

0. **NO RELAXATION IN THIS BUNDLE.** `find benchmark-verified/sympy__sympy-19495 -iname '*relax*'` => nothing; no RELAXED_LEAKAGE.md anywhere in the instance dir; `'relaxed_leakage' in meta` => False (the only /relax/i hits in meta.json are inside prior agents' prose notes, not a flag). So there is no unavoidability argument to credit or re-derive: I judged STRICTLY against the public problem_statement. instance['hints_text'] has len 0, so there is no non-public hints channel that could be echoed at all.

1. **SPEC REGION FROZEN.** markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) => True; spec_signature equal on both legs; spec_view sha256 IDENTICAL on both legs = c433efc53b4b57d1... My recomputed region_hashes: axioms=718580b80e27, pure=fc311a57cec1, post-conditions=a8d34bb72692, impl=c7f5d81da65a, proof=f967d85c448a, spec_view=c433efc53b4b. The two files differ ONLY in the impl body (prepatch adds `if isTrue cond' then return mkMemberSet new base'`) and the proof (`intro cs old new _; rfl` vs `sorry`) -- both regions the spec view elides. Current Solution.lean sha256 = e49826469d9e6c66...

2. STRICT SCREEN, RE-RUN BY ME. leakage.screen(Solution.lean, lean.language, instance.patch, instance.problem_statement, instance.test_patch) => LeakageReport(hard_failures=[], warnings=[]). patch.diff == instance['patch'] (confirmed True). Independently: iterated EVERY +/- line of the gold patch, alphanumeric-normalized, against the spec view => 0 verbatim reproductions. Explicitly checked each of the gold's ADDED lines: the four-line comment it introduces ("The condition may have become true due to assumptions on 'sym' ... assumptions are ignored") is ABSENT from the view -- the view never mentions assumptions, `__new__`, or constructor consistency. Probed the view for repo vocabulary: `_eval_subs`, eval_subs, S.true, base_set, self.func, `__new__`, dummy_eq, Contains, ConditionSet, conditionset, .py, sympy, Interval, ImageSet, FiniteSet, solveset, xreplace, simultaneous, asin, Lambda, Basic, EmptySet, UniversalSet, 'Notes' -- ALL absent. The four apparent hits (Symbol/Dummy/Boolean/sym) are, on line-by-line inspection, ordinary English inside prose: "bound/dummy variable", "a symbol, a number, an applied function", "a boolean-valued symbolic object", "the symbol being substituted" -- no repo identifier, no file or module path, no diff marker.

3. LOAD-BEARING (STRIP) TEST -- RUN, NOT ASSERTED. I mechanically deleted every doc comment (/-! -/, /-- -/) and every non-marker `--` line from both legs, keeping only region markers + code, and re-verified under scripts/lean_verify.sh. Stripped GOLD => exit 0 (still verifies, 66 lines). Stripped PREPATCH with the gold proof body substituted for `sorry` => exit 1: "Tactic `rfl` failed: The left-hand side `new` is not definitionally equal to the right-hand side implementation_freeSubs cs old new". So ALL the narration is inert prose carrying ZERO verification weight; the actual discriminator is argument position 1 of the single equation `result = mkSet cs.sym (subsCond cs.cond old new) (subsSet cs.base old new)` -- the INPUT's bound variable occupies slot 1, and the prepatch's rebinding to `new` is refuted exactly there.

4. IS THE DISCRIMINATOR DERIVABLE FROM problem_statement ALONE? YES, line by line. Public Out[75] displays the wrong object as {1/3 | 1/3 in {`2*pi*n`+asin(1/3)|n in Z} AND (1/3 in {...})} -- i.e. verbatim `ConditionSet(new, Contains(new, base), base)`: the substituted value 1/3 sitting in the bound-variable slot, with the original condition `y in [-1,1]` gone and replaced by a membership of 1/3 in the base set. The reporter states the diagnosis outright: "It's as if the bound variable `x` of the ConditionSet were mistaken for a `y`", and gives the desired results in Out[78]/Out[80]. The collapse-to-true TRIGGER is also public: Out[71]/Out[72] show the FiniteSet analogue where the condition becomes true, and in Out[75] the original condition has evidently evaluated away (1/3 in [-1,1] is true). So (a) preserve the bound variable, (b) the substituted value must not take its place, (c) the corner case is the condition collapsing to true, and (d) the membership-on-`new` shape is what must NOT be produced -- each is readable off the public transcript. I also confirmed in the real worktree (, sympy/sets/conditionset.py) that the pre-patch `if cond is S.true: return ConditionSet(new, Contains(new, base), base)` is ALREADY VISIBLE SOURCE at base_commit; the only secret is that the gold DELETES it, which is precisely what the public bug report demands. The spec view says no more than that.

5. FACET RE-CONFIRMED, and nothing outside it. The view is the `old != sym` FREE-SYMBOL branch contract only: it does not describe the bound-variable-rename branch, the Tuple/equation-set early return, the constructor's canonicalisation semantics, the default-universal-set behavior, or ANY of the gold patch's docstring hunks (the `Notes` heading removal, the duplicated-clause typo fix, the trailing blank line) -- I checked each of those hunks against the view and none is echoed. `isTrue` and `mkMemberSet` are declared but UNUSED by the gold spec and impl: that is a structural consequence of same_spec (the prepatch leg's callees must live in the shared view), and both name shapes are displayed verbatim in public Out[75]. mkMemberSet's docstring calls itself "the shape that the corner case must NOT produce" -- that is Out[75] restated, not the edit.

6. CORE GATES THE DISPOSITION LEANS ON, RE-RUN BY ME. scripts/lean_verify.sh Solution.lean => exit 0. Appending `#print axioms correct_freeSubs` / `implementation_freeSubs` / `problem_spec_freeSubs` and re-verifying prints "does not depend on any axioms" for ALL THREE -- no sorryAx, the proof is genuine (closes by rfl), and the opaques are genuinely opaque rather than consumed axioms (G-AX is a documented skip: no `_prop` axioms exist). The prepatch leg genuinely fails against the shared spec (item 3), so the frozen-spec argument is non-vacuous rather than trivially true.

7. **BUNDLE-DIRECTED-AT-REVIEWER SCAN.** leakage.reviewer_directed() over Solution.lean, refinement.md, mapping.md, verdict.md, meta.json, conformance_check.py, axiom_check.py => [] for EVERY file. My own grep for panel-addressing phrasing ('the honest verdict', 'you must submit', 'record NO-LEAKAGE', 'do not submit', 'dear reviewer', 'panel should') over Solution.lean/refinement.md/mapping.md/conformance_check.py => no hits. FINDING FOR THE RECORD: verdict.md (line 509 onward, duplicated at 537+) and meta.json['gates']['G-PANEL-3']['note'] carry a PRIOR panel-3 agent's complete argument ending in "VERDICT: NO-LEAKAGE" against these very questions. That is a pre-recorded disposition sitting in the bundle for the role that is supposed to measure it independently. I did not inherit it, and it could not have applied anyway (item 8). Every measurement above is my own re-derivation.

8. STALENESS FINDING (record hygiene, not leakage). The stamped G-PANEL-3 pass cites sources.Solution.lean = c6e47262bea3fd99..., but the current file is e49826469d9e6c66... The stamped region_hashes.spec_view = ac2b8709ed1cbfef..., whereas the current spec_view hashes c433efc53b4b57d1... Note the prior verdict.md note itself claims the then-current view was ac2b8709 and that the *previous* stamp (3861eec8/ba3cf507) was stale -- so the file has now been edited at least twice past its last panel-3 judgement, and BOTH the meta stamp and the prior agent's note describe bytes that no longer exist. Only G-LEAK/G-HYGIENE/G-CONF/G-DIFF/G-GOLD/G-AX (checked_at 15:25-15:32) cite the current e4982646 sha; G-EQ still cites c6e47262. My NO-LEAKAGE is measured against the CURRENT bytes. Separately, refinement.md and mapping.md DO reproduce gold patch lines verbatim (e.g. `- if cond is S.true:`, `- return ConditionSet(new, Contains(new, base), base)`, `+ return self.func(self.sym, cond, base)`); per docs/architecture.md these are audit artifacts ("op-by-op map from impl to patch.diff", "formal symbol to repo symbol binding"), NOT the spec view that G-LEAK certifies and that a consumer is shown, so they are outside this gate's scope -- flagged only so the record shows I checked them rather than skipped them. The recorded G-PANEL-1 (spec-too-weak, atk_2 verifies but does not resolve) and G-PANEL-2 (faithfulness: subs not well-defined on alpha-equivalence) failures belong to other layers and neither bears on leakage.

**VERDICT:** NO-LEAKAGE. The spec view names no repo symbol, file/module path, gold-patch line, or added gold comment; its strongest prose (bound-variable preservation, including in the condition-collapse corner, and that the membership-on-`new` shape must not be produced) is entailed by the public problem_statement's own displayed wrong output Out[75], its stated diagnosis, and its Out[78]/Out[80] targets, with the pre-patch branch already visible as base_commit source; that prose is provably inert (full comment-strip test: gold exit 0, prepatch exit 1); the spec region is byte-frozen across legs; the proof is axiom-clean; and hints_text is empty so there is no non-public channel to echo.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.