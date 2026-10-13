# P2 adversarial audit — django__django-16901

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Prepatch bug counterexample cs = [true, true, true]: spec demands countTrue%2==1 = (3%2==1) = true, but the prepatch impl (rhsSum==1 always) yields lhs && (3==1) = true && false = false. atk_1 encodes this exact prepatch impl and FAILS to close (exit 1), confirming the G-DIFF discriminator. No same-spec WRONG impl was found that closes: every closing impl (atk_6 pure-parity oracle echo, atk_7 drop-OR-leg) is semantically equal to the parity oracle and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,23 +27,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
-  -- Disjunction of every operand condition.
+  -- prepatch bug: rhs always compared to 1
   let mut lhs := false
   for c in cs do
     lhs := lhs || c
-  -- Sum of one-per-true-operand contributions.
   let mut rhsSum : Nat := 0
   for c in cs do
     if c then
       rhsSum := rhsSum + 1
-  -- Test on the running sum: with more than two operands the parity of the sum
-  -- is taken before comparing to one; otherwise the sum is compared directly.
   let mut rhs := false
-  if cs.length > 2 then
-    rhs := (rhsSum % 2 == 1)
-  else
-    rhs := (rhsSum == 1)
+  rhs := (rhsSum == 1)
   return lhs && rhs
 -- impl-end
 
@@ -82,5 +75,4 @@
   · rename_i hlen
     have h2 : countTrue cs ≤ 2 := by omega
     interval_cases hc : countTrue cs <;> simp
-
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,24 +27,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
-  -- Disjunction of every operand condition.
+  -- partial-domain: correct for small lists, false for length >= 5
+  if cs.length ≥ 5 then
+    return false
   let mut lhs := false
   for c in cs do
     lhs := lhs || c
-  -- Sum of one-per-true-operand contributions.
   let mut rhsSum : Nat := 0
   for c in cs do
     if c then
       rhsSum := rhsSum + 1
-  -- Test on the running sum: with more than two operands the parity of the sum
-  -- is taken before comparing to one; otherwise the sum is compared directly.
-  let mut rhs := false
-  if cs.length > 2 then
-    rhs := (rhsSum % 2 == 1)
-  else
-    rhs := (rhsSum == 1)
-  return lhs && rhs
+  return lhs && (rhsSum % 2 == 1)
 -- impl-end
 
 
@@ -82,5 +75,4 @@
   · rename_i hlen
     have h2 : countTrue cs ≤ 2 := by omega
     interval_cases hc : countTrue cs <;> simp
-
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,20 +27,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
-  -- Disjunction of every operand condition.
+  -- boundary off-by-one: threshold > 3 instead of > 2
   let mut lhs := false
   for c in cs do
     lhs := lhs || c
-  -- Sum of one-per-true-operand contributions.
   let mut rhsSum : Nat := 0
   for c in cs do
     if c then
       rhsSum := rhsSum + 1
-  -- Test on the running sum: with more than two operands the parity of the sum
-  -- is taken before comparing to one; otherwise the sum is compared directly.
   let mut rhs := false
-  if cs.length > 2 then
+  if cs.length > 3 then
     rhs := (rhsSum % 2 == 1)
   else
     rhs := (rhsSum == 1)
@@ -82,5 +78,4 @@
   · rename_i hlen
     have h2 : countTrue cs ≤ 2 := by omega
     interval_cases hc : countTrue cs <;> simp
-
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,24 +27,15 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
-  -- Disjunction of every operand condition.
+  -- control-flow-effect: even parity instead of odd
   let mut lhs := false
   for c in cs do
     lhs := lhs || c
-  -- Sum of one-per-true-operand contributions.
   let mut rhsSum : Nat := 0
   for c in cs do
     if c then
       rhsSum := rhsSum + 1
-  -- Test on the running sum: with more than two operands the parity of the sum
-  -- is taken before comparing to one; otherwise the sum is compared directly.
-  let mut rhs := false
-  if cs.length > 2 then
-    rhs := (rhsSum % 2 == 1)
-  else
-    rhs := (rhsSum == 1)
-  return lhs && rhs
+  return lhs && (rhsSum % 2 == 0)
 -- impl-end
 
 
@@ -82,5 +73,4 @@
   · rename_i hlen
     have h2 : countTrue cs ≤ 2 := by omega
     interval_cases hc : countTrue cs <;> simp
-
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -27,24 +27,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
-  -- Disjunction of every operand condition.
-  let mut lhs := false
-  for c in cs do
-    lhs := lhs || c
-  -- Sum of one-per-true-operand contributions.
-  let mut rhsSum : Nat := 0
-  for c in cs do
-    if c then
-      rhsSum := rhsSum + 1
-  -- Test on the running sum: with more than two operands the parity of the sum
-  -- is taken before comparing to one; otherwise the sum is compared directly.
-  let mut rhs := false
-  if cs.length > 2 then
-    rhs := (rhsSum % 2 == 1)
-  else
-    rhs := (rhsSum == 1)
-  return lhs && rhs
+  -- constant false
+  return false
 -- impl-end
 
 
@@ -82,5 +66,4 @@
   · rename_i hlen
     have h2 : countTrue cs ≤ 2 := by omega
     interval_cases hc : countTrue cs <;> simp
-
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,23 +28,7 @@
 
 -- impl-start
 def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
-  -- Disjunction of every operand condition.
-  let mut lhs := false
-  for c in cs do
-    lhs := lhs || c
-  -- Sum of one-per-true-operand contributions.
-  let mut rhsSum : Nat := 0
-  for c in cs do
-    if c then
-      rhsSum := rhsSum + 1
-  -- Test on the running sum: with more than two operands the parity of the sum
-  -- is taken before comparing to one; otherwise the sum is compared directly.
-  let mut rhs := false
-  if cs.length > 2 then
-    rhs := (rhsSum % 2 == 1)
-  else
-    rhs := (rhsSum == 1)
-  return lhs && rhs
+  return (countTrue cs % 2 == 1)
 -- impl-end
 
 
@@ -52,35 +36,6 @@
 theorem correct_xorFallback :
     ∀ (cs : List Bool),
     problem_spec_xorFallback cs (implementation_xorFallback cs) := by
-  have hsum : ∀ (l : List Bool) (n : Nat),
-      List.foldl (fun r c => if c = true then r + 1 else r) n l = n + countTrue l := by
-    intro l
-    induction l with
-    | nil => intro n; simp [countTrue]
-    | cons a t ih => intro n; cases a <;> simp [countTrue, List.filter, List.foldl, ih] <;> omega
-  have hor : ∀ (l : List Bool) (b : Bool),
-      List.foldl (fun r c => r || c) b l = (b || decide (0 < countTrue l)) := by
-    intro l
-    induction l with
-    | nil => intro b; simp [countTrue]
-    | cons a t ih =>
-      intro b
-      rw [List.foldl_cons, ih (b || a)]
-      cases a <;> simp [countTrue, List.filter]
   intro cs
-  simp only [problem_spec_xorFallback, implementation_xorFallback, Id.run]
-  simp only [bind, pure]
-  simp only [← apply_ite ForInStep.yield]
-  rw [List.forIn_yield_eq_foldl, List.forIn_yield_eq_foldl]
-  rw [hor, hsum]
-  simp only [Nat.zero_add]
-  have hle : countTrue cs ≤ cs.length := List.length_filter_le _ _
-  split
-  · rcases Nat.eq_zero_or_pos (countTrue cs) with h | h
-    · simp [h]
-    · simp [decide_eq_true h]
-  · rename_i hlen
-    have h2 : countTrue cs ≤ 2 := by omega
-    interval_cases hc : countTrue cs <;> simp
-
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,23 +28,11 @@
 
 -- impl-start
 def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
-  -- Disjunction of every operand condition.
-  let mut lhs := false
-  for c in cs do
-    lhs := lhs || c
-  -- Sum of one-per-true-operand contributions.
   let mut rhsSum : Nat := 0
   for c in cs do
     if c then
       rhsSum := rhsSum + 1
-  -- Test on the running sum: with more than two operands the parity of the sum
-  -- is taken before comparing to one; otherwise the sum is compared directly.
-  let mut rhs := false
-  if cs.length > 2 then
-    rhs := (rhsSum % 2 == 1)
-  else
-    rhs := (rhsSum == 1)
-  return lhs && rhs
+  return (rhsSum % 2 == 1)
 -- impl-end
 
 
@@ -58,29 +46,11 @@
     induction l with
     | nil => intro n; simp [countTrue]
     | cons a t ih => intro n; cases a <;> simp [countTrue, List.filter, List.foldl, ih] <;> omega
-  have hor : ∀ (l : List Bool) (b : Bool),
-      List.foldl (fun r c => r || c) b l = (b || decide (0 < countTrue l)) := by
-    intro l
-    induction l with
-    | nil => intro b; simp [countTrue]
-    | cons a t ih =>
-      intro b
-      rw [List.foldl_cons, ih (b || a)]
-      cases a <;> simp [countTrue, List.filter]
   intro cs
   simp only [problem_spec_xorFallback, implementation_xorFallback, Id.run]
   simp only [bind, pure]
   simp only [← apply_ite ForInStep.yield]
-  rw [List.forIn_yield_eq_foldl, List.forIn_yield_eq_foldl]
-  rw [hor, hsum]
+  rw [List.forIn_yield_eq_foldl]
+  rw [hsum]
   simp only [Nat.zero_add]
-  have hle : countTrue cs ≤ cs.length := List.length_filter_le _ _
-  split
-  · rcases Nat.eq_zero_or_pos (countTrue cs) with h | h
-    · simp [h]
-    · simp [decide_eq_true h]
-  · rename_i hlen
-    have h2 : countTrue cs ≤ 2 := by omega
-    interval_cases hc : countTrue cs <;> simp
-
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The combined predicate is
-- modeled DEEPLY at the level of its boolean semantics: the disjunction of the
-- operands, the count of true operands, the parity/equality test on that count,
-- and the final conjunction are all reproduced concretely as ordinary boolean
-- and arithmetic operations rather than axiomatized. The proof agent may add
-- `_prop` axioms only if it gets genuinely stuck.
-- axioms-end

-- pure-start
/-- The number of operands whose condition holds, taken over the list of operand
truth values. -/
def countTrue (cs : List Bool) : Nat :=
  (cs.filter (fun b => b)).length
-- pure-end

-- post-conditions-start
/-- Boolean semantics of the combined predicate built from a list of operand
truth values `cs`. The combined predicate must be true exactly when an odd number
of the operands are true (the meaning of an n-ary exclusive-or). The whole output
is pinned to this single parity relation on the inputs; nothing is left free. -/
def problem_spec_xorFallback (cs : List Bool) (result : Bool) : Prop :=
  result = (countTrue cs % 2 == 1)
-- post-conditions-end

-- impl-start
def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
  -- Disjunction of every operand condition.
  let mut lhs := false
  for c in cs do
    lhs := lhs || c
  -- Sum of one-per-true-operand contributions.
  let mut rhsSum : Nat := 0
  for c in cs do
    if c then
      rhsSum := rhsSum + 1
  -- Test on the running sum: with more than two operands the parity of the sum
  -- is taken before comparing to one; otherwise the sum is compared directly.
  let mut rhs := false
  if cs.length > 2 then
    rhs := (rhsSum % 2 == 1)
  else
    rhs := (rhsSum == 1)
  return lhs && rhs
-- impl-end


-- proof-start
theorem correct_xorFallback :
    ∀ (cs : List Bool),
    problem_spec_xorFallback cs (implementation_xorFallback cs) := by
  have hsum : ∀ (l : List Bool) (n : Nat),
      List.foldl (fun r c => if c = true then r + 1 else r) n l = n + countTrue l := by
    intro l
    induction l with
    | nil => intro n; simp [countTrue]
    | cons a t ih => intro n; cases a <;> simp [countTrue, List.filter, List.foldl, ih] <;> omega
  have hor : ∀ (l : List Bool) (b : Bool),
      List.foldl (fun r c => r || c) b l = (b || decide (0 < countTrue l)) := by
    intro l
    induction l with
    | nil => intro b; simp [countTrue]
    | cons a t ih =>
      intro b
      rw [List.foldl_cons, ih (b || a)]
      cases a <;> simp [countTrue, List.filter]
  intro cs
  simp only [problem_spec_xorFallback, implementation_xorFallback, Id.run]
  simp only [bind, pure]
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl, List.forIn_yield_eq_foldl]
  rw [hor, hsum]
  simp only [Nat.zero_add]
  have hle : countTrue cs ≤ cs.length := List.length_filter_le _ _
  split
  · rcases Nat.eq_zero_or_pos (countTrue cs) with h | h
    · simp [h]
    · simp [decide_eq_true h]
  · rename_i hlen
    have h2 : countTrue cs ≤ 2 := by omega
    interval_cases hc : countTrue cs <;> simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A FULLY-PINNED FUNCTIONAL EQUALITY: problem_spec_xorFallback cs result := result = (countTrue cs % 2 == 1). Any verifying impl must equal the n-ary-XOR parity function on ALL inputs; no in-model-wrong impl can close. same_spec = True for all 8 files (axioms/pure/pre/post byte-identical). Verifications run concurrently (≤4/batch) via lean_verify.sh (300s cap).

### Results
- pc (gold, verbatim): exit 0; #print axioms = [propext, Classical.choice, Quot.sound] (clean); faithful=gold patch RESOLVES (harness sanity control).
- atk_1 prepatch bug (rhs := rhsSum==1 always): exit 1 (proof does NOT close). PREPATCH REPRODUCED. Doomed proof was the full gold proof body; fails at the split branch as expected.
- atk_2 partial-domain (return false when cs.length ≥ 5, else correct parity): exit 1, does NOT close.
- atk_3 boundary off-by-one (threshold cs.length > 3 instead of > 2, so len==3 uses rhsSum==1): exit 1, does NOT close.
- atk_4 control-flow-effect (even parity: rhsSum % 2 == 0): exit 1, does NOT close.
- atk_5 constant false (return false): exit 1, does NOT close.
- atk_6 ungrounded-oracle echo (return countTrue cs % 2 == 1): exit 0, #print axioms = does NOT depend on any axioms (clean). Semantically = parity oracle = correct. FAITHFUL PATCH (unconditional Mod(rhs_sum,2), drop the `if len>2` guard) RUN THROUGH run_resolve: RESOLVED=True COMPLETED=True.
- atk_7 drop-OR-leg (return rhsSum % 2 == 1, no OR conjunction): exit 0, #print axioms = [propext, Quot.sound] (clean). Odd count ⇒ ≥1 operand true, so the OR leg is redundant; semantically = parity oracle = correct. FAITHFUL PATCH (drop lhs OR leg, return WhereNode([rhs],AND)) RUN THROUGH run_resolve: RESOLVED=True COMPLETED=True.

Commands:
  bash scripts/lean_verify.sh <SD>/<file>.lean
  #print axioms via appended `#print axioms correct_xorFallback` on _ax.lean copies
  resolve: python -m via <SD>/resolve_one.py <SD>/patch_atk_{6,7}.diff (run_resolve, timeout 1800, retries 1); patches generated with git diff off the real base_commit where.py (ee36e101) so they apply cleanly.

BOTH closing impls have a materialized faithful patch that RESOLVES → verify⇒correct holds; no verify⇒¬resolve break exists. The 5 genuinely-wrong impls are all rejected by the frozen proof obligation.

refinement.md AUDIT: 5 legs, all R / R/I / I. No A-consumed legs (proof discharges parity + boolean algebra directly; axioms region empty, G-AX skip stub). No A-reference legs (Case/When/Exact/Mod/reduce(add)/recursive as_sql all reproduced concretely at boolean-semantics level, not abstracted behind a model needing G-AX validation). No kind-3 (changed-inexpressible) legs — the changed op (row 4, Mod-2 wrap for len>2) is expressible and modeled deeply. Discriminator (row 4) matches the gold patch hunk and the issue's reported bug. Correspondence to real callees holds.

VERDICT: SOUND. ≥5 distinct wrong impls encoded + prepatch + oracle-echo; all wrong impls fail to close; both closing (correct) impls have faithful patches that RESOLVE; refinement legs clean.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Prepatch bug counterexample cs = [true, true, true]: spec demands countTrue%2==1 = (3%2==1) = true, but the prepatch impl (rhsSum==1 always) yields lhs && (3==1) = true && false = false. atk_1 encodes this exact prepatch impl and FAILS to close (exit 1), confirming the G-DIFF discriminator. No same-spec WRONG impl was found that closes: every closing impl (atk_6 pure-parity oracle echo, atk_7 drop-OR-leg) is semantically equal to the parity oracle and its faithful patch RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The combined predicate is
-- modeled DEEPLY at the level of its boolean semantics: the disjunction of the
-- operands, the count of true operands, the parity/equality test on that count,
-- and the final conjunction are all reproduced concretely as ordinary boolean
-- and arithmetic operations rather than axiomatized. The proof agent may add
-- `_prop` axioms only if it gets genuinely stuck.
-- axioms-end

-- pure-start
/-- The number of operands whose condition holds, taken over the list of operand
truth values. -/
def countTrue (cs : List Bool) : Nat :=
  (cs.filter (fun b => b)).length
-- pure-end

-- post-conditions-start
/-- Boolean semantics of the combined predicate built from a list of operand
truth values `cs`. The combined predicate must be true exactly when an odd number
of the operands are true (the meaning of an n-ary exclusive-or). The whole output
is pinned to this single parity relation on the inputs; nothing is left free. -/
def problem_spec_xorFallback (cs : List Bool) (result : Bool) : Prop :=
  result = (countTrue cs % 2 == 1)
-- post-conditions-end

-- impl-start
def implementation_xorFallback (cs : List Bool) : Bool := Id.run do
  -- Disjunction of every operand condition.
  let mut lhs := false
  for c in cs do
    lhs := lhs || c
  -- Sum of one-per-true-operand contributions.
  let mut rhsSum : Nat := 0
  for c in cs do
    if c then
      rhsSum := rhsSum + 1
  -- Test on the running sum: with more than two operands the parity of the sum
  -- is taken before comparing to one; otherwise the sum is compared directly.
  let mut rhs := false
  if cs.length > 2 then
    rhs := (rhsSum % 2 == 1)
  else
    rhs := (rhsSum == 1)
  return lhs && rhs
-- impl-end


-- proof-start
theorem correct_xorFallback :
    ∀ (cs : List Bool),
    problem_spec_xorFallback cs (implementation_xorFallback cs) := by
  have hsum : ∀ (l : List Bool) (n : Nat),
      List.foldl (fun r c => if c = true then r + 1 else r) n l = n + countTrue l := by
    intro l
    induction l with
    | nil => intro n; simp [countTrue]
    | cons a t ih => intro n; cases a <;> simp [countTrue, List.filter, List.foldl, ih] <;> omega
  have hor : ∀ (l : List Bool) (b : Bool),
      List.foldl (fun r c => r || c) b l = (b || decide (0 < countTrue l)) := by
    intro l
    induction l with
    | nil => intro b; simp [countTrue]
    | cons a t ih =>
      intro b
      rw [List.foldl_cons, ih (b || a)]
      cases a <;> simp [countTrue, List.filter]
  intro cs
  simp only [problem_spec_xorFallback, implementation_xorFallback, Id.run]
  simp only [bind, pure]
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl, List.forIn_yield_eq_foldl]
  rw [hor, hsum]
  simp only [Nat.zero_add]
  have hle : countTrue cs ≤ cs.length := List.length_filter_le _ _
  split
  · rcases Nat.eq_zero_or_pos (countTrue cs) with h | h
    · simp [h]
    · simp [decide_eq_true h]
  · rename_i hlen
    have h2 : countTrue cs ≤ 2 := by omega
    interval_cases hc : countTrue cs <;> simp

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A FULLY-PINNED FUNCTIONAL EQUALITY: problem_spec_xorFallback cs result := result = (countTrue cs % 2 == 1). Any verifying impl must equal the n-ary-XOR parity function on ALL inputs; no in-model-wrong impl can close. same_spec = True for all 8 files (axioms/pure/pre/post byte-identical). Verifications run concurrently (≤4/batch) via lean_verify.sh (300s cap).

### Results
- pc (gold, verbatim): exit 0; #print axioms = [propext, Classical.choice, Quot.sound] (clean); faithful=gold patch RESOLVES (harness sanity control).
- atk_1 prepatch bug (rhs := rhsSum==1 always): exit 1 (proof does NOT close). PREPATCH REPRODUCED. Doomed proof was the full gold proof body; fails at the split branch as expected.
- atk_2 partial-domain (return false when cs.length ≥ 5, else correct parity): exit 1, does NOT close.
- atk_3 boundary off-by-one (threshold cs.length > 3 instead of > 2, so len==3 uses rhsSum==1): exit 1, does NOT close.
- atk_4 control-flow-effect (even parity: rhsSum % 2 == 0): exit 1, does NOT close.
- atk_5 constant false (return false): exit 1, does NOT close.
- atk_6 ungrounded-oracle echo (return countTrue cs % 2 == 1): exit 0, #print axioms = does NOT depend on any axioms (clean). Semantically = parity oracle = correct. FAITHFUL PATCH (unconditional Mod(rhs_sum,2), drop the `if len>2` guard) RUN THROUGH run_resolve: RESOLVED=True COMPLETED=True.
- atk_7 drop-OR-leg (return rhsSum % 2 == 1, no OR conjunction): exit 0, #print axioms = [propext, Quot.sound] (clean). Odd count ⇒ ≥1 operand true, so the OR leg is redundant; semantically = parity oracle = correct. FAITHFUL PATCH (drop lhs OR leg, return WhereNode([rhs],AND)) RUN THROUGH run_resolve: RESOLVED=True COMPLETED=True.

Commands:
  bash scripts/lean_verify.sh <SD>/<file>.lean
  #print axioms via appended `#print axioms correct_xorFallback` on _ax.lean copies
  resolve: python -m via <SD>/resolve_one.py <SD>/patch_atk_{6,7}.diff (run_resolve, timeout 1800, retries 1); patches generated with git diff off the real base_commit where.py (ee36e101) so they apply cleanly.

BOTH closing impls have a materialized faithful patch that RESOLVES → verify⇒correct holds; no verify⇒¬resolve break exists. The 5 genuinely-wrong impls are all rejected by the frozen proof obligation.

refinement.md AUDIT: 5 legs, all R / R/I / I. No A-consumed legs (proof discharges parity + boolean algebra directly; axioms region empty, G-AX skip stub). No A-reference legs (Case/When/Exact/Mod/reduce(add)/recursive as_sql all reproduced concretely at boolean-semantics level, not abstracted behind a model needing G-AX validation). No kind-3 (changed-inexpressible) legs — the changed op (row 4, Mod-2 wrap for len>2) is expressible and modeled deeply. Discriminator (row 4) matches the gold patch hunk and the issue's reported bug. Correspondence to real callees holds.

VERDICT: SOUND. ≥5 distinct wrong impls encoded + prepatch + oracle-echo; all wrong impls fail to close; both closing (correct) impls have faithful patches that RESOLVE; refinement legs clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Setup fully verified: (1) same_spec(Solution, Solution_prepatch)=True on the lean backend — spec region is byte-identical/frozen. (2) Solution.lean compiles via scripts/lean_verify.sh (exit 0). (3) #print axioms correct_xorFallback = [propext, Classical.choice, Quot.sound], NO sorryAx — proof is genuine, not fake. (4) conformance_check.py passes (120000 inputs, 0 disagreements). Faithfulness argument: the spec drops the OR (lhs) leg, which is sound because odd-parity implies >=1 true operand implies OR true, so lhs&&rhs === rhs. For len<=2, count==1 <=> count%2==1 (count in {0,1,2}), so the real code's equality-to-one test coincides with parity. For len>2 the patch applies Mod(sum,2), matching parity directly. Hence problem_spec (pure parity) equals the real patched callee's boolean semantics on the entire reachable domain. The spec is neither too strong nor too weak — it is an exact (I / R) model. G-DIFF is preserved: prepatch impl (rhs=count==1 always) diverges at cs=[true,true,true] (impl false vs spec true), so the prepatch proof cannot close, confirming the discriminating clause. No genuine diverging input exists; verdict FAITHFUL.

Counterexample / evidence:

```
None on the meaningful domain. Exhaustive check over all boolean lists len 0..14 comparing spec (countTrue%2==1) against a faithful transcription of the patched WhereNode.as_sql XOR fallback [(OR) AND (MOD(count,2)==1) for len>2 else (OR) AND (count==1)] yields 0 divergences for every non-empty list.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (solver-visible) = imports + empty axioms stub + `countTrue` def + post-condition `problem_spec_xorFallback cs result := result = (countTrue cs % 2 == 1)`; the impl-start and proof-start regions are ELIDED in the spec view (confirmed via markers.spec_view). Mechanical leakage.screen passes (no hard failures/warnings). Semantic check: the spec pins the correct behavior to parity-of-true-count. But the PUBLIC problem_statement already fully discloses this: it states the correct interpretation of `a^b^c` is 'true when an ODD number of the arguments are true' (vs Django's buggy 'exactly one'), names the >2-argument case, and gives the expected 1,0,1,0,1 sequence. Encoding the declared-correct behavior in the post-condition is the legitimate purpose of a spec and reveals nothing beyond problem_statement. The spec view exposes NONE of the gold-edit mechanism (the `if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)` branch, `Exact(1, rhs_sum)`, OR/sum construction) since impl+proof are hidden. No diff markers, no patched file path (where.py), no patched-symbol echoes (as_sql/Mod/rhs_sum/WhereNode), no bug/fix narration vocabulary. Identifiers are neutral spec names. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
