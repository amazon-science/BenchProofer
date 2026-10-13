# P2 adversarial audit — sympy__sympy-19040

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_3.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_0.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verify/resolve divergence found. The four wrong-shaped impls whose proofs closed (atk_2 sqfPart hoisted above the degenerate early-return; atk_4 raiseShift hoisted above the single-factor branch; atk_5 recovery loop run unconditionally then overwritten on the single-factor path; atk_6 factorListInclude(sqfNorm mono) probe computed above the early-return and discarded) are all pure-code-motion refactors of gold: because every relocated callee is a total pure function whose result is discarded or recomputed identically on the reached path, the observable (lc, factors) return is byte-identical to gold on every input. Each of their faithful patches RESOLVED under the official harness, matching the gold control. The prepatch bug and 7 genuinely wrong impls were all rejected.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -101,7 +101,7 @@
   if degreesNonpos (degreeList mono) then
     return (lc, [])
   let fSqf := sqfPart mono
-  let (s, g, r) := sqfNorm mono
+  let (s, g, r) := sqfNorm fSqf
   let factors0 := factorListInclude r
   let mut factors : List ExPoly := []
   if factors0.length = 1 then
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -98,9 +98,9 @@
 def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
   let lc := groundLC f
   let mono := groundMonic f
+  let fSqf := sqfPart mono
   if degreesNonpos (degreeList mono) then
     return (lc, [])
-  let fSqf := sqfPart mono
   let (s, g, r) := sqfNorm mono
   let factors0 := factorListInclude r
   let mut factors : List ExPoly := []
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -98,6 +98,7 @@
 def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
   let lc := groundLC f
   let mono := groundMonic f
+  let (s0, _g0, _r0) := sqfNorm mono
   if degreesNonpos (degreeList mono) then
     return (lc, [])
   let fSqf := sqfPart mono
@@ -107,7 +108,7 @@
   if factors0.length = 1 then
     factors := [fSqf]
   else
-    let H := raiseShift s
+    let H := raiseShift (s + s0 - s0)
     let mut gCur := g
     for entry in factors0 do
       let (h, g') := recoverOne H gCur entry.1
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,11 +103,11 @@
   let fSqf := sqfPart mono
   let (s, g, r) := sqfNorm mono
   let factors0 := factorListInclude r
+  let H := raiseShift s
   let mut factors : List ExPoly := []
   if factors0.length = 1 then
     factors := [fSqf]
   else
-    let H := raiseShift s
     let mut gCur := g
     for entry in factors0 do
       let (h, g') := recoverOne H gCur entry.1
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -103,16 +103,15 @@
   let fSqf := sqfPart mono
   let (s, g, r) := sqfNorm mono
   let factors0 := factorListInclude r
+  let H := raiseShift s
   let mut factors : List ExPoly := []
+  let mut gCur := g
+  for entry in factors0 do
+    let (h, g') := recoverOne H gCur entry.1
+    gCur := g'
+    factors := factors ++ [h]
   if factors0.length = 1 then
     factors := [fSqf]
-  else
-    let H := raiseShift s
-    let mut gCur := g
-    for entry in factors0 do
-      let (h, g') := recoverOne H gCur entry.1
-      gCur := g'
-      factors := factors ++ [h]
   return (lc, trialDivision mono factors)
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -98,6 +98,7 @@
 def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
   let lc := groundLC f
   let mono := groundMonic f
+  let _probe := factorListInclude (sqfNorm mono).2.2
   if degreesNonpos (degreeList mono) then
     return (lc, [])
   let fSqf := sqfPart mono
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -113,7 +113,7 @@
       let (h, g') := recoverOne H gCur entry.1
       gCur := g'
       factors := factors ++ [h]
-  return (lc, trialDivision mono factors)
+  return (lc, trialDivision fSqf factors)
 -- impl-end
 
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -98,8 +98,6 @@
 def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
   let lc := groundLC f
   let mono := groundMonic f
-  if degreesNonpos (degreeList mono) then
-    return (lc, [])
   let fSqf := sqfPart mono
   let (s, g, r) := sqfNorm mono
   let factors0 := factorListInclude r
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -104,7 +104,7 @@
   let (s, g, r) := sqfNorm mono
   let factors0 := factorListInclude r
   let mut factors : List ExPoly := []
-  if factors0.length = 1 then
+  if factors0.length ≤ 1 then
     factors := [fSqf]
   else
     let H := raiseShift s
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,20 +100,7 @@
   let mono := groundMonic f
   if degreesNonpos (degreeList mono) then
     return (lc, [])
-  let fSqf := sqfPart mono
-  let (s, g, r) := sqfNorm mono
-  let factors0 := factorListInclude r
-  let mut factors : List ExPoly := []
-  if factors0.length = 1 then
-    factors := [fSqf]
-  else
-    let H := raiseShift s
-    let mut gCur := g
-    for entry in factors0 do
-      let (h, g') := recoverOne H gCur entry.1
-      gCur := g'
-      factors := factors ++ [h]
-  return (lc, trialDivision mono factors)
+  return (lc, trialDivision mono [sqfPart mono])
 -- impl-end
 
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,10 +108,8 @@
     factors := [fSqf]
   else
     let H := raiseShift s
-    let mut gCur := g
     for entry in factors0 do
-      let (h, g') := recoverOne H gCur entry.1
-      gCur := g'
+      let (h, _g') := recoverOne H g entry.1
       factors := factors ++ [h]
   return (lc, trialDivision mono factors)
 -- impl-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -96,8 +96,8 @@
 
 -- impl-start
 def implementation_extFactor (f : ExPoly) : ExCoeff × List (ExPoly × Nat) := Id.run do
-  let lc := groundLC f
   let mono := groundMonic f
+  let lc := groundLC mono
   if degreesNonpos (degreeList mono) then
     return (lc, [])
   let fSqf := sqfPart mono
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Base-commit worktrees cloned from the upstream repository at b9179e80d2daa1bb6cba1ffe35ca9e6612e115c9 (wt, wt1..wt7, wtchk). 13 candidates built by editing ONLY the impl region; axioms/pure/pre/post/proof left byte-identical.

**SAME-SPEC:** `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..."` => True for ALL of atk_0..atk_12 (12 attacks + positive control).

VERIFY (`bash scripts/lean_verify.sh <f>.lean`), run 4-way concurrent:
- atk_0 POSITIVE CONTROL (gold impl verbatim): exit 0.
- atk_1 PREPATCH BUG (sqfNorm of sqfPart mono, not mono): exit 1 -> prepatch reproduced. Error: `split` failed / unsolved goals at the third conjunct - the discriminating clause pins recovery to sqfNorm mono; sqfNorm is opaque so the two are not provably equal.
- atk_2 exit 0; atk_3 exit 1; atk_4 exit 0; atk_5 exit 0; atk_6 exit 0; atk_7 exit 1 (trialDivision against fSqf instead of mono - `rfl` failed).
- atk_8 PARTIAL-DOMAIN (degenerate early-return dropped entirely): exit 1.
- atk_9 BOUNDARY (single-factor threshold widened `= 1` -> `<= 1`): exit 1.
- atk_10 UNGROUNDED-ORACLE ECHO (always return [sqfPart mono], no recovery loop): exit 1.
- atk_11 BOUNDARY (gcd carrier NOT threaded; g reused every iteration): exit 1.
- atk_12 (groundLC taken of the monic, not the input): exit 1.
All 8 rejections carry real proof failures (split/rfl/unsolved goals), not tactic-fragility artifacts.

**AXIOMS:** for every closing candidate (atk_0/2/4/5/6) appended `#print axioms implementation_extFactor` + `#print axioms correct_extFactor`, files ax_{0,2,4,5,6}.lean, each exit 0:
  implementation_extFactor depends on axioms: [propext]
  correct_extFactor depends on axioms: [propext, Quot.sound]
No sorryAx, no `_prop` axiom, no native_decide. Clean.

MANDATORY RESOLVE (executed, not speculated). All 4 clean-axiom wrong-shaped impls had faithful patches materialized against the real dmp_ext_factor body and each checked with `git apply --check` in a base_commit worktree (all OK) before submission:
  git -C .../wtchk apply --check .../atk_{2,4,5,6}.diff  => OK (4/4)
Official harness via swebench_unified.harness.run_resolve('sympy__sympy-19040', patch):
  gold  (control) => resolved=true, completed=true, attempts=1, flaky=false
  atk_2           => resolved=true, completed=true, attempts=1, flaky=false
  atk_4           => resolved=true, completed=true, attempts=1, flaky=false
  atk_5           => resolved=true, completed=true, attempts=1, flaky=false
  atk_6           => resolved=true, completed=true, attempts=1, flaky=false
Every required resolve COMPLETED; no incomplete/timeout measurement was reported as a verdict. Since no closing-proof impl has a non-resolving faithful patch, verify=>correct is not falsified.

**WHY THE FOUR CODE-MOTION ATTACKS ARE NOT BREAKS.** My initial hypothesis was a control-flow-effect break: Lean's `sqfPart` is a TOTAL pure function while Python's `dmp_sqf_part` could raise on a degenerate-degree input, so hoisting it above the `all(d<=0)` early-return would be proof-invisible but crash the real code. I did reproduce a TypeError from dmp_sqf_part - but ONLY on a hand-constructed ANP/domain object. Capturing the REAL degenerate input off the live call path (f=[[ANP([1],[1,0,1],QQ)]], u=1, dmp_degree_list(mono)=(0,0), reached via factor(4,x,y,extension=[I]) and factor(`2*x*y`,...)) showed dmp_sqf_part returns normally on it. So the crash was my own artifact, NOT a reachable defect - I did not report it as one. Local pre-screen agreed: wt/wt1/wt2/wt6 each ran sympy/polys/tests/test_polytools.py + test_factortools.py => 169 passed (gold 2 xfailed; variants 1 xfailed + 1 xpassed, i.e. the FAIL_TO_PASS test_issue_5786 now XPasses exactly as under gold). The four attacks are behaviour-preserving code motion, so their resolving is evidence FOR fidelity.

**REFINEMENT.MD AUDIT:** 12 legs, all tagged R / I / A-consumed / A-reference (9 A-reference, 1 `A-reference + R`, 3 I). ZERO kind-3 / untagged legs. Every A-reference line citation was checked against the real base_commit source: L1143 dmp_ground_LC, L1144 dmp_ground_monic, L1146 dmp_degree_list + all(d<=0), L1147 `return lc, []`, L1149 dmp_sqf_part, L1150 dmp_sqf_norm (the gold hunk), L1152 dmp_factor_list_include, L1154 `len(factors)==1`, L1155 `factors=[f]`, L1157 dmp_raise, L1160 dmp_convert, L1161 dmp_inner_gcd, L1162 dmp_compose, L1163 `factors[i]=h`, L1165 dmp_trial_division - 15/15 OK. The `recoverOne` A-reference correctly collapses the 3-call loop body (dmp_convert . dmp_inner_gcd . dmp_compose) returning (h, g'), matching factortools.py:1159-1163 including the g threading. mapping.md's gold-hunk claim (line 1150, dmp_sqf_norm(f) -> dmp_sqf_norm(F)) matches patch.diff verbatim. The no-consumed-axiom and conf_skip justifications are accurate: the proof consumes no callee property, only the List.forIn_cons loop/fold induction, confirmed by the clean [propext, Quot.sound] axiom set.

CAVEAT ON SPEC STRENGTH (advisory, not a break): the spec constrains only the (lc, factors) return value of a pure model over opaque total callees. It therefore cannot distinguish code motion of a pure callee across a branch - atk_2/4/5/6 verify and resolve. That is the correct outcome here (they are observationally equivalent in Python too), but it does mean the spec would not catch a relocation whose real-world callee had a side effect or partiality the opaque model omits. Nothing in this instance's actual callees exhibits that on reachable inputs, so the bundle is sound as shipped; the model's blindness to effects/partiality is inherent to the all-A-tagged opaque encoding and is disclosed by conf_skip.

**RESULT:** 12 same-spec attacks run (>=5 required), prepatch reproduced, 4 closing-proof impls resolve-tested against the official harness with the gold control, all rejections semantically justified, refinement.md clean. verify=>correct NOT falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_3.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `atk_0.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No verify/resolve divergence found. The four wrong-shaped impls whose proofs closed (atk_2 sqfPart hoisted above the degenerate early-return; atk_4 raiseShift hoisted above the single-factor branch; atk_5 recovery loop run unconditionally then overwritten on the single-factor path; atk_6 factorListInclude(sqfNorm mono) probe computed above the early-return and discarded) are all pure-code-motion refactors of gold: because every relocated callee is a total pure function whose result is discarded or recomputed identically on the reached path, the observable (lc, factors) return is byte-identical to gold on every input. Each of their faithful patches RESOLVED under the official harness, matching the gold control. The prepatch bug and 7 genuinely wrong impls were all rejected.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Base-commit worktrees cloned from the upstream repository at b9179e80d2daa1bb6cba1ffe35ca9e6612e115c9 (wt, wt1..wt7, wtchk). 13 candidates built by editing ONLY the impl region; axioms/pure/pre/post/proof left byte-identical.

**SAME-SPEC:** `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..."` => True for ALL of atk_0..atk_12 (12 attacks + positive control).

VERIFY (`bash scripts/lean_verify.sh <f>.lean`), run 4-way concurrent:
- atk_0 POSITIVE CONTROL (gold impl verbatim): exit 0.
- atk_1 PREPATCH BUG (sqfNorm of sqfPart mono, not mono): exit 1 -> prepatch reproduced. Error: `split` failed / unsolved goals at the third conjunct - the discriminating clause pins recovery to sqfNorm mono; sqfNorm is opaque so the two are not provably equal.
- atk_2 exit 0; atk_3 exit 1; atk_4 exit 0; atk_5 exit 0; atk_6 exit 0; atk_7 exit 1 (trialDivision against fSqf instead of mono - `rfl` failed).
- atk_8 PARTIAL-DOMAIN (degenerate early-return dropped entirely): exit 1.
- atk_9 BOUNDARY (single-factor threshold widened `= 1` -> `<= 1`): exit 1.
- atk_10 UNGROUNDED-ORACLE ECHO (always return [sqfPart mono], no recovery loop): exit 1.
- atk_11 BOUNDARY (gcd carrier NOT threaded; g reused every iteration): exit 1.
- atk_12 (groundLC taken of the monic, not the input): exit 1.
All 8 rejections carry real proof failures (split/rfl/unsolved goals), not tactic-fragility artifacts.

**AXIOMS:** for every closing candidate (atk_0/2/4/5/6) appended `#print axioms implementation_extFactor` + `#print axioms correct_extFactor`, files ax_{0,2,4,5,6}.lean, each exit 0:
  implementation_extFactor depends on axioms: [propext]
  correct_extFactor depends on axioms: [propext, Quot.sound]
No sorryAx, no `_prop` axiom, no native_decide. Clean.

MANDATORY RESOLVE (executed, not speculated). All 4 clean-axiom wrong-shaped impls had faithful patches materialized against the real dmp_ext_factor body and each checked with `git apply --check` in a base_commit worktree (all OK) before submission:
  git -C .../wtchk apply --check .../atk_{2,4,5,6}.diff  => OK (4/4)
Official harness via swebench_unified.harness.run_resolve('sympy__sympy-19040', patch):
  gold  (control) => resolved=true, completed=true, attempts=1, flaky=false
  atk_2           => resolved=true, completed=true, attempts=1, flaky=false
  atk_4           => resolved=true, completed=true, attempts=1, flaky=false
  atk_5           => resolved=true, completed=true, attempts=1, flaky=false
  atk_6           => resolved=true, completed=true, attempts=1, flaky=false
Every required resolve COMPLETED; no incomplete/timeout measurement was reported as a verdict. Since no closing-proof impl has a non-resolving faithful patch, verify=>correct is not falsified.

**WHY THE FOUR CODE-MOTION ATTACKS ARE NOT BREAKS.** My initial hypothesis was a control-flow-effect break: Lean's `sqfPart` is a TOTAL pure function while Python's `dmp_sqf_part` could raise on a degenerate-degree input, so hoisting it above the `all(d<=0)` early-return would be proof-invisible but crash the real code. I did reproduce a TypeError from dmp_sqf_part - but ONLY on a hand-constructed ANP/domain object. Capturing the REAL degenerate input off the live call path (f=[[ANP([1],[1,0,1],QQ)]], u=1, dmp_degree_list(mono)=(0,0), reached via factor(4,x,y,extension=[I]) and factor(`2*x*y`,...)) showed dmp_sqf_part returns normally on it. So the crash was my own artifact, NOT a reachable defect - I did not report it as one. Local pre-screen agreed: wt/wt1/wt2/wt6 each ran sympy/polys/tests/test_polytools.py + test_factortools.py => 169 passed (gold 2 xfailed; variants 1 xfailed + 1 xpassed, i.e. the FAIL_TO_PASS test_issue_5786 now XPasses exactly as under gold). The four attacks are behaviour-preserving code motion, so their resolving is evidence FOR fidelity.

**REFINEMENT.MD AUDIT:** 12 legs, all tagged R / I / A-consumed / A-reference (9 A-reference, 1 `A-reference + R`, 3 I). ZERO kind-3 / untagged legs. Every A-reference line citation was checked against the real base_commit source: L1143 dmp_ground_LC, L1144 dmp_ground_monic, L1146 dmp_degree_list + all(d<=0), L1147 `return lc, []`, L1149 dmp_sqf_part, L1150 dmp_sqf_norm (the gold hunk), L1152 dmp_factor_list_include, L1154 `len(factors)==1`, L1155 `factors=[f]`, L1157 dmp_raise, L1160 dmp_convert, L1161 dmp_inner_gcd, L1162 dmp_compose, L1163 `factors[i]=h`, L1165 dmp_trial_division - 15/15 OK. The `recoverOne` A-reference correctly collapses the 3-call loop body (dmp_convert . dmp_inner_gcd . dmp_compose) returning (h, g'), matching factortools.py:1159-1163 including the g threading. mapping.md's gold-hunk claim (line 1150, dmp_sqf_norm(f) -> dmp_sqf_norm(F)) matches patch.diff verbatim. The no-consumed-axiom and conf_skip justifications are accurate: the proof consumes no callee property, only the List.forIn_cons loop/fold induction, confirmed by the clean [propext, Quot.sound] axiom set.

CAVEAT ON SPEC STRENGTH (advisory, not a break): the spec constrains only the (lc, factors) return value of a pure model over opaque total callees. It therefore cannot distinguish code motion of a pure callee across a branch - atk_2/4/5/6 verify and resolve. That is the correct outcome here (they are observationally equivalent in Python too), but it does mean the spec would not catch a relocation whose real-world callee had a side effect or partiality the opaque model omits. Nothing in this instance's actual callees exhibits that on reachable inputs, so the bundle is sound as shipped; the model's blindness to effects/partiality is inherent to the all-A-tagged opaque encoding and is disclosed by conf_skip.

**RESULT:** 12 same-spec attacks run (>=5 required), prepatch reproduced, 4 closing-proof impls resolve-tested against the official harness with the gold control, all rejections semantically justified, refinement.md clean. verify=>correct NOT falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** G-PANEL-2 faithfulness of problem_spec_extFactor (Lean) vs the REAL post-patch dmp_ext_factor (multivariate u>0 branch), sympy__sympy-19040.

**SPEC REGION INTEGRITY:** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True. Spec view (axioms/pure/post-conditions) byte-identical across the twins; only impl+proof regions differ. Prepatch twin carries `sorry` and the buggy routing sqfNorm(sqfPart mono), so the spec discriminates.

**LEAN:** scripts/lean_verify.sh Solution.lean -> exit 0 (elaborates, no sorry). #print axioms: correct_extFactor depends on [propext, Quot.sound]; implementation_extFactor [propext]; problem_spec_extFactor none. NO sorryAx -> proof is real. Zero `axiom _prop` shipped, consistent with refinement.md.

**METHOD:** transcribed problem_spec_extFactor/implementation_extFactor into Python (spec.py) binding every opaque carrier to its REAL callee in the PATCHED worktree (, base b9179e80d2 + patch.diff, git diff = the single line 1150 hunk), then differentially compared spec_impl vs the real dmp_ext_factor.

**RESULTS:** 54/54 MATCH over an 18-polynomial pool x 3 number fields QQ(I), QQ(sqrt2), QQ(sqrt3); plus 24 hand-built cases (x^2-2, `x*y`+y^2 doctest, x^2+y^2, (x^2+1)(x^2+y), x^4-1, (x^2+1)(y^2+1), x(x+y)(x-y), 3-variable u=2 cases, x^2y+xy, (x^2-2)(y^2-2)) all MATCH; randomized fuzz over 8 seeds all MATCH; edge cases zero polynomial, ground const 2, ground const I all MATCH. THE ISSUE INPUT (x-1)*(y-1) MATCHES, as do (x-1)(y-1)(x+1) and (x-1)(y-1)(x^2+1).

DIRECTION CHECK (guards against condemning the fix): a base-routing variant (sqfNorm(sqfPart mono) instead of sqfNorm(mono)) diverges from the real patched callee on (x^2+1)(y^2+1), (y^2+1)(x+1), x^2y+xy while the shipped spec matches on all three. So the spec sides with the PATCHED reference, not base -- it pins the fix, it does not drift.

OP-BY-OP AUDIT (all confirmed against factortools.py:1138-1165 @ patched): groundLC f = dmp_ground_LC on the ORIGINAL f before monicization (line 1143, correct ordering); groundMonic f = F (1144); degreeList/degreesNonpos test the MONIC (1146); lc returned unconditionally on both branches; fSqf = sqfPart mono = post-patch local f (1149); sqfNorm argument is `mono` (=F) -- THE FIX (1150); factorListInclude r (1152); len==1 -> [fSqf] (1154-5); raiseShift s (1157); recoverOne = dmp_convert then dmp_inner_gcd then dmp_compose with g threaded through iterations in enumerate order, recoverLoop preserves both order and the g-accumulator; trialDivision against `mono` (=F) (1165).

**SOUNDNESS OF THE TWO REFINEMENTS:** (a) degreesNonpos as List Int .all (<= 0) vs Python all(d<=0) where dmp_degree_list may yield -oo -- real degrees are either -oo or >=0 and both map to the same Bool, so the Int refinement never flips the branch. (b) recoverOne typed as a function of (H, g, factor) is a superset of the real dependency (g' depends only on g and factor), so it cannot under-constrain.

BOUNDARY OBSERVED AND DISMISSED (not a finding): on inputs with zero degree in the principal variable but positive degree elsewhere (y-1, y^2+1, (x^2+1)^2, x^2+2xy+y^2), the real dmp_ext_factor NEVER RETURNS -- dmp_trial_division's `while True` is a fixed point when a factor is the unit 1 (dmp_div(f,1) = (f,0), so k increments unboundedly). I verified BOTH sides hang identically under a 40s budget, and confirmed the SAME hang in the untouched base worktree (), so it is a pre-existing upstream nontermination bug orthogonal to this patch. Modeling it as a total Lean opaque is the inherent total-logic boundary that every such bundle has; it is not a value disagreement on any input where the real callee produces a value, and it is not the delta the patch introduces. Reporting it would condemn a correct spec.

**CONCLUSION:** no input found where the modeled function disagrees in value with the real post-patch callee. The spec is neither over-strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

sympy__sympy-19040 (lean), attacker 3 = leakage / gold-reconstruction. Every claim below is a command I ran this session.

NO RELAXATION IN THIS BUNDLE, so no inherited disposition to re-derive. `find -iname '*RELAX*'` over the whole instance dir returns nothing; I walked every key of meta.json for /relax|leak/i and the only hit is gates/G-LEAK; meta.relaxed_leakage is None and gates.G-LEAK.status == 'pass', not 'relaxed'. Judged strictly on the merits.

NOTHING IN THE BUNDLE ADDRESSES ME (reported as a finding in its own right per my instructions): CLEAN. leakage.reviewer_directed() returns [] on every non-binary file in the instance root and lean/ (all four rules: addresses-the-reviewer, prescribes-the-verdict x2, recording-convention). Hand-grepped Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, conformance_check.py, axiom_check.py for attacker|panel|reviewer|auditor|'honest verdict'|NO-LEAKAGE|submit_result|'you should/must'|'do not flag' -> ZERO hits. lean/verdict.md and meta.json carry PRIOR G-PANEL-3 records concluding NO-LEAKAGE (verdict.md:2904, 2918, 2931); those are historical gate-ledger entries about earlier runs, not imperatives aimed at me, and I did NOT inherit them -- the agreement is corroboration, not adoption. No artifact-steering attempt found.

SETUP / SPEC-VIEW IDENTITY. markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) == True: the gold edit lives ENTIRELY inside the elided impl region, so the consumer spec view is identical between the patched and prepatch bundles and cannot by itself reveal which artifact is which. Notably the prepatch file's impl docstring IS explicitly diagnostic ('Pre-patch (buggy) skeleton ... rather than the full monic polynomial ... the missing component is dropped') -- but that text sits in the impl region and is elided; I diffed the two computed spec views and they differ by nothing but a trailing newline from my own print.

**MECHANICAL SCREEN.** leakage.screen(Solution.lean, lean backend, instance.patch, problem_statement) -> 0 hard failures, 0 warnings. Token-scanned the COMPUTED spec view directly: dmp_sqf_norm ABSENT, sqf_norm ABSENT, dmp_ext_factor / ext_factor ABSENT, dmp_sqf_part ABSENT, dmp_ground_monic ABSENT, factortools ABSENT, 'sympy/polys/factortools.py' and the dotted module path ABSENT, line number '1150' ABSENT, 'extension=' ABSENT, issue number '18895' ABSENT. Narration scan: bug/fix/patch/previously/incorrectly/wrong/broken/drops/dropped/missing/omits/'rather than'/'instead' ALL absent from the view. The gold changed lines normalize to `s,g,r=dmp_sqf_norm(f,u,K)` / `...(F,u,K)` and neither appears. The spec identifiers (problem_spec_extFactor / implementation_extFactor) do not embed the patched symbol dmp_ext_factor.

CORE GATES RE-MEASURED MYSELF (not re-stamped). scripts/lean_verify.sh Solution.lean -> exit 0. `#print axioms correct_extFactor` -> "depends on axioms: [propext, Quot.sound]" -- clean, no sorryAx, so the proof is real. Solution_prepatch.lean -> exit 3 ('declaration uses sorry' at 127:8), i.e. the prepatch impl genuinely does NOT satisfy the spec: G-DIFF has teeth. Base source cross-checked against a fresh b9179e80 worktree: factortools.py:1138-1165 dmp_ext_factor matches mapping.md row-for-row (1149 `f, F = dmp_sqf_part(f,u,K), f`; 1150 `s,g,r = dmp_sqf_norm(f,u,K)` <- the gold hunk; 1154-1155 single-factor branch returning the sqf part; 1165 trial division against F).

THE LOAD-BEARING TEST (the substantive question). The spec view's post-condition routes `sqfNorm mono` (the full monic) rather than `sqfNorm (sqfPart mono)`, and the module docstring restates that in prose ('the square-free norm ... is taken of the FULL monic polynomial'). I tested whether the PROSE is what discriminates: I mechanically stripped the module docstring, every /-- -/ doc comment and every non-marker -- comment, leaving only formal content, and re-ran both impls against that stripped spec. Denarrated + gold impl -> exit 0 (PASSES). Denarrated + prepatch impl -> exit 1, unsolved goals whose printed terms are exactly `sqfNorm (sqfPart (groundMonic f))` vs `sqfNorm (groundMonic f)` (FAILS). So the discrimination is carried entirely by the FORMAL post-condition; the prose is redundant restatement, removable without weakening the spec. That is the decisive point: pinning which polynomial flows into the norm is the spec's own job -- G-DIFF/G-PANEL-1 REQUIRE the prepatch impl to fail, which by construction means the post-condition must name the discriminator. A post-condition cannot be faulted for doing the one thing that makes it a specification.

**WHY THE PROSE ADDS NOTHING BEYOND THAT.** It is phrased affirmatively and states only correct behavior -- no 'rather than the square-free part', no prior-behavior contrast, no diagnosis, no edit. Its one rationale clause, 'every irreducible component of the input is represented (including components that do not involve the principal variable)', is precisely the PUBLIC symptom restated abstractly: the problem_statement shows factor(expand((x-1)*(y-1)), extension=[I]) returning `x - 1`, i.e. dropping y-1, a component not involving the principal variable. Derivable from problem_statement alone (assessed against problem_statement ONLY, never hints_text -- I confirmed the hints are just a PR template with 'Fixes #18895' and NO ENTRY release notes, and nothing hint-only is echoed). The presence of `sqfPart` as a separate opaque callee is likewise NOT a leak artifact: the real post-patch function genuinely still uses the square-free part in the single-factor branch (base 1149/1154-1155), so a faithful model must expose it.

WHAT A CONSUMER CANNOT RECONSTRUCT from the view: the changed file, the changed function name, the changed line, that the fix is a one-token argument swap in pre-existing code, or that anything was ever broken. The full gold reconstruction DOES appear in refinement.md ('THE rerouted edge') and mapping.md ('gold hunk: line 1150'), but those are auditor-facing artifacts outside the spec view (spec view = Solution.lean minus impl minus proof per spec_guide 6) and are out of scope for this gate.

**Verdict:** NO-LEAKAGE. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
