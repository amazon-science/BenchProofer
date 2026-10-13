# P2 adversarial audit — sympy__sympy-24213

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The only verifying wrong-impl candidate (atk_8, the ungrounded-oracle echo `return combineSpec first rest`) had its faithful refined patch materialized and RESOLVED under the official harness (F2P test_issue_24211 pass, all 31 P2P pass), so it is not a counterexample: the echo is behaviourally gold on the graded set. Every genuinely-divergent impl (prepatch surface test, both outcome-identity collapses, priority inversion, missing-signature wildcard, partial domain on rest=[], boundary off-by-one, wrong reported dimension) was REJECTED by the frozen spec.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -196,7 +196,7 @@
       decreasing i
     do
       let a := rest[i - 1]!
-      chk := checkStep first.dim.deps a chk
+      chk := if a.dim.surf == first.dim.surf then chk else Check.disagreeing
       factor := factor + a.factor
       i := i - 1
     match chk with
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -202,7 +202,7 @@
     match chk with
     | Check.equivalent  => return Combined.reported factor first.dim
     | Check.disagreeing => return Combined.disagreement
-    | Check.unreducible => return Combined.noSignature
+    | Check.unreducible => return Combined.disagreement
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -201,7 +201,7 @@
       i := i - 1
     match chk with
     | Check.equivalent  => return Combined.reported factor first.dim
-    | Check.disagreeing => return Combined.disagreement
+    | Check.disagreeing => return Combined.noSignature
     | Check.unreducible => return Combined.noSignature
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -196,7 +196,7 @@
       decreasing i
     do
       let a := rest[i - 1]!
-      chk := checkStep first.dim.deps a chk
+      chk := (match chk with | Check.equivalent => checkStep first.dim.deps a Check.equivalent | c => c)
       factor := factor + a.factor
       i := i - 1
     match chk with
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -187,6 +187,7 @@
     -- impl-start
     let mut factor := first.factor
     let mut chk : Check := Check.equivalent
+    let mut anyNone : Bool := first.dim.deps.isNone
     let mut i := rest.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rest.length
@@ -198,11 +199,15 @@
       let a := rest[i - 1]!
       chk := checkStep first.dim.deps a chk
       factor := factor + a.factor
+      if a.dim.deps.isNone then anyNone := true
       i := i - 1
-    match chk with
-    | Check.equivalent  => return Combined.reported factor first.dim
-    | Check.disagreeing => return Combined.disagreement
-    | Check.unreducible => return Combined.noSignature
+    if anyNone then
+      return Combined.noSignature
+    else
+      match chk with
+      | Check.equivalent  => return Combined.reported factor first.dim
+      | Check.disagreeing => return Combined.disagreement
+      | Check.unreducible => return Combined.noSignature
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -219,15 +224,13 @@
 
 prove_correct combineAddends by
   loom_solve
-  · -- invariant_2 maintained: peel the front element exposed by drop (i-1)
-    rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,
-        ← invariant_2]
-  · -- invariant_3 maintained: the factor accumulator gains rest[i-1]
-    rw [drop_cons_step rest i (by omega) (by omega), sumFactors_cons]
-    omega
   all_goals (
-    -- final: each of the three outcomes matches combineSpec's own case split
-    subst done_1
-    simp only [List.drop_zero] at invariant_2 invariant_3
-    simp only [combineSpec] at *
-    simp_all)
+    try (rw [drop_cons_step rest i (by omega) (by omega)])
+    try simp only [checkAddends_cons, sumFactors_cons]
+    try subst done_1
+    try simp only [List.drop_zero] at *
+    try simp only [combineSpec] at *
+    try omega
+    try grind
+    try simp_all
+    try rfl)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,24 +185,27 @@
             → out = Combined.noSignature
   do
     -- impl-start
-    let mut factor := first.factor
-    let mut chk : Check := Check.equivalent
-    let mut i := rest.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rest.length
-      invariant chk = checkAddends first.dim.deps (rest.drop i)
-      invariant factor = first.factor + sumFactors (rest.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := rest[i - 1]!
-      chk := checkStep first.dim.deps a chk
-      factor := factor + a.factor
-      i := i - 1
-    match chk with
-    | Check.equivalent  => return Combined.reported factor first.dim
-    | Check.disagreeing => return Combined.disagreement
-    | Check.unreducible => return Combined.noSignature
+    if rest.isEmpty then
+      return Combined.disagreement
+    else
+      let mut factor := first.factor
+      let mut chk : Check := Check.equivalent
+      let mut i := rest.length
+      while i > 0
+        invariant 0 ≤ i ∧ i ≤ rest.length
+        invariant chk = checkAddends first.dim.deps (rest.drop i)
+        invariant factor = first.factor + sumFactors (rest.drop i)
+        done_with i = 0
+        decreasing i
+      do
+        let a := rest[i - 1]!
+        chk := checkStep first.dim.deps a chk
+        factor := factor + a.factor
+        i := i - 1
+      match chk with
+      | Check.equivalent  => return Combined.reported factor first.dim
+      | Check.disagreeing => return Combined.disagreement
+      | Check.unreducible => return Combined.noSignature
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -219,15 +222,13 @@
 
 prove_correct combineAddends by
   loom_solve
-  · -- invariant_2 maintained: peel the front element exposed by drop (i-1)
-    rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,
-        ← invariant_2]
-  · -- invariant_3 maintained: the factor accumulator gains rest[i-1]
-    rw [drop_cons_step rest i (by omega) (by omega), sumFactors_cons]
-    omega
   all_goals (
-    -- final: each of the three outcomes matches combineSpec's own case split
-    subst done_1
-    simp only [List.drop_zero] at invariant_2 invariant_3
-    simp only [combineSpec] at *
-    simp_all)
+    try (rw [drop_cons_step rest i (by omega) (by omega)])
+    try simp only [checkAddends_cons, sumFactors_cons]
+    try subst done_1
+    try simp only [List.drop_zero] at *
+    try simp only [combineSpec] at *
+    try omega
+    try grind
+    try simp_all
+    try rfl)
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -188,11 +188,11 @@
     let mut factor := first.factor
     let mut chk : Check := Check.equivalent
     let mut i := rest.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ rest.length
       invariant chk = checkAddends first.dim.deps (rest.drop i)
       invariant factor = first.factor + sumFactors (rest.drop i)
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let a := rest[i - 1]!
@@ -219,15 +219,13 @@
 
 prove_correct combineAddends by
   loom_solve
-  · -- invariant_2 maintained: peel the front element exposed by drop (i-1)
-    rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,
-        ← invariant_2]
-  · -- invariant_3 maintained: the factor accumulator gains rest[i-1]
-    rw [drop_cons_step rest i (by omega) (by omega), sumFactors_cons]
-    omega
   all_goals (
-    -- final: each of the three outcomes matches combineSpec's own case split
-    subst done_1
-    simp only [List.drop_zero] at invariant_2 invariant_3
-    simp only [combineSpec] at *
-    simp_all)
+    try (rw [drop_cons_step rest i (by omega) (by omega)])
+    try simp only [checkAddends_cons, sumFactors_cons]
+    try subst done_1
+    try simp only [List.drop_zero] at *
+    try simp only [combineSpec] at *
+    try omega
+    try grind
+    try simp_all
+    try rfl)
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -185,24 +185,7 @@
             → out = Combined.noSignature
   do
     -- impl-start
-    let mut factor := first.factor
-    let mut chk : Check := Check.equivalent
-    let mut i := rest.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rest.length
-      invariant chk = checkAddends first.dim.deps (rest.drop i)
-      invariant factor = first.factor + sumFactors (rest.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := rest[i - 1]!
-      chk := checkStep first.dim.deps a chk
-      factor := factor + a.factor
-      i := i - 1
-    match chk with
-    | Check.equivalent  => return Combined.reported factor first.dim
-    | Check.disagreeing => return Combined.disagreement
-    | Check.unreducible => return Combined.noSignature
+    return combineSpec first rest
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -219,15 +202,4 @@
 
 prove_correct combineAddends by
   loom_solve
-  · -- invariant_2 maintained: peel the front element exposed by drop (i-1)
-    rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,
-        ← invariant_2]
-  · -- invariant_3 maintained: the factor accumulator gains rest[i-1]
-    rw [drop_cons_step rest i (by omega) (by omega), sumFactors_cons]
-    omega
-  all_goals (
-    -- final: each of the three outcomes matches combineSpec's own case split
-    subst done_1
-    simp only [List.drop_zero] at invariant_2 invariant_3
-    simp only [combineSpec] at *
-    simp_all)
+  all_goals (simp only [combineSpec] at *; simp_all)
```

Attack 9 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -187,6 +187,7 @@
     -- impl-start
     let mut factor := first.factor
     let mut chk : Check := Check.equivalent
+    let mut dimOut : Dim := first.dim
     let mut i := rest.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rest.length
@@ -198,9 +199,10 @@
       let a := rest[i - 1]!
       chk := checkStep first.dim.deps a chk
       factor := factor + a.factor
+      dimOut := a.dim
       i := i - 1
     match chk with
-    | Check.equivalent  => return Combined.reported factor first.dim
+    | Check.equivalent  => return Combined.reported factor dimOut
     | Check.disagreeing => return Combined.disagreement
     | Check.unreducible => return Combined.noSignature
     -- impl-end
@@ -219,15 +221,13 @@
 
 prove_correct combineAddends by
   loom_solve
-  · -- invariant_2 maintained: peel the front element exposed by drop (i-1)
-    rw [drop_cons_step rest i (by omega) (by omega), checkAddends_cons,
-        ← invariant_2]
-  · -- invariant_3 maintained: the factor accumulator gains rest[i-1]
-    rw [drop_cons_step rest i (by omega) (by omega), sumFactors_cons]
-    omega
   all_goals (
-    -- final: each of the three outcomes matches combineSpec's own case split
-    subst done_1
-    simp only [List.drop_zero] at invariant_2 invariant_3
-    simp only [combineSpec] at *
-    simp_all)
+    try (rw [drop_cons_step rest i (by omega) (by omega)])
+    try simp only [checkAddends_cons, sumFactors_cons]
+    try subst done_1
+    try simp only [List.drop_zero] at *
+    try simp only [combineSpec] at *
+    try omega
+    try grind
+    try simp_all
+    try rfl)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Own worktrees at base_commit e8c22f6eac created there (repo, repo_atk8, repo_ns). same_spec == True confirmed for ALL 9 attacks + prepatch.lean + pos_control.lean (byte-identical axioms/pure/pre/post; only the impl region and the prove_correct body edited). Positive control pos_control.lean verifies EXIT=0. Bundle's own Solution_prepatch.lean re-verified as REJECTED (EXIT=1, unsolved goal on invariant_2).

COMMANDS (from swe-proof): `bash scripts/lean_verify.sh atk_N.lean`; launched 4-at-a-time as background jobs (batches {1,2,3,4}, {5,6,7,11}, {9,10}).

### ATTACK RESULTS (9 same-spec wrong impls; 8 rejected, 1 verified-and-resolves):
- atk_1 PREPATCH BUG re-encoded, surface-expression test `a.dim.surf == first.dim.surf` instead of deps-equality -> EXIT=1 REJECTED. Leftover goal: `(if (rest[i-1]!.dim.surf == first.dim.surf) = true then chk else Check.disagreeing) = checkStep first.dim.deps rest[i-1]! chk`. Semantic, not a script error.
- atk_2 OUTCOME COLLAPSE noSignature -> disagreement -> EXIT=1 REJECTED (`ensures_4` goal reduces to `False`).
- atk_3 OUTCOME COLLAPSE disagreement -> noSignature (the other direction) -> EXIT=1 REJECTED.
- atk_4 PRIORITY INVERTED (a later failure overrides the leftmost one) -> EXIT=1 REJECTED.
- atk_5 MISSING-SIGNATURE WILDCARD (any absent signature anywhere wins, overriding a leftmost disagreement) -> EXIT=1 REJECTED on `ensures_2`, goal `¬i_2 = Check.disagreeing`. NOTE: my first atk_5 draft was accidentally gold-equivalent and a second draft failed on a WPGen parse error (early `return` before a `match`); both were discarded and the attack was REBUILT so the failure is semantic. Same for atk_6/atk_7, which first failed on my own proof-script errors (unknown identifier / `subst done_1` failure) — rebuilt with a deliberately GENEROUS `try`-wrapped proof so a leftover goal can only mean semantic rejection.
- atk_6 PARTIAL DOMAIN (correct on non-empty rest, returns disagreement on rest=[]) -> EXIT=1 REJECTED, goal `¬checkAddends first.dim.deps [] = Check.equivalent`.
- atk_7 BOUNDARY off-by-one (`while i > 1`, rest[0] never tested, its factor never added) -> EXIT=1 REJECTED.
- atk_11 WRONG REPORTED DIMENSION (reports the last addend's dim instead of the reference's; observable exactly on surface-distinct equivalents) -> EXIT=1 REJECTED, goal `i_2 = first.dim`.
- atk_8 UNGROUNDED-ORACLE ECHO `return combineSpec first rest` -> EXIT=0 VERIFIES. Mandatory resolve executed: faithful refined patch written to atk_8_faithful.diff (eager pre-collection of every addend's sub-result, then the front-recursive checkAddends fold, then dispatch on its single verdict — combineSpec's exact shape), `run_resolve('sympy__sympy-24213', patch, run_id='geq-atk8-echo')` -> RESOLVED: True, COMPLETED: True, F2P failure list [], P2P failure list [] (all 31). Note 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' — harness's own retry, final verdict resolved. Local pytest on the graded file also 33 passed / 1 xfailed. So verify => correct held here; NOT a counterexample.
- atk_9 (echo via the two folds, no loop) and atk_10 (eager factor-total then whole check) both EXIT=1 but on a Velvet WPGen parse limitation (`Failed to parse an assertion without names: WPGen (match ...)`), i.e. a harness/encoding artifact rather than a semantic rejection. They are therefore EXCLUDED from the attack list and are not counted as spec strength (per the retained-attack-labels rule: an encoding failure must not be re-judged as the reject lane). The oracle-echo class is instead covered soundly by atk_8, which verifies and resolves.

### A-LEG AUDIT (the assigned focus).
1. Only kind-A content is one A-reference; meta.json `axioms: []` — no consumed contract, so nothing to discharge. Confirmed there is no `equivalentDims` axiom hiding the changed op.
2. A-reference correspondence INDEPENDENTLY re-derived, not taken on trust. Re-implemented the Lean pure region (checkStep/checkAddends/combineSpec, with deps as Option) in Python over REAL SymPy Dimensions and diffed its 3-outcome behaviour against the real PATCHED Add branch: diff_fuzz.py, 34,880 cases (all ordered pairs over a 32-dimension pool + 20k ordered triples + 20k random length-2..5 sums, pool mixing Integer/Float/Rational exponents, Float precisions 5 and 50, symbolic and nested-symbolic powers, the hash-colliding -1/-2 pair, and Add-named unreducible dimensions) -> MISMATCHES: 0.
3. Verified the callee facts myself in the patched worktree: equivalent_dims(velocity, acceleration*time)=True while surf-equality is False; (length,time)=False; (force, mass*acceleration)=True; (length**2, length**2.0)=True with surf-equality False (the Float-precision witness). get_dimensional_dependencies raises TypeError on Dimension(length+time) — the partiality that grounds `deps = none`.
4. A4d LEFTMOST-FAILURE claim empirically CONFIRMED against the real patched repo (not just asserted in prose): `l1 + t1 + b1` (disagreement first) -> ValueError, whereas `l1 + b1 + t1` (no-signature first) -> TypeError. Same failure multiset, different order, different observable class — so the ordering is genuinely observable and checkStep's front recursion is the right order. atk_4 confirms the spec rejects the inversion.
5. A4b/A4c ASYMMETRY independently MEASURED rather than trusted. Instrumented the patched branch and ran the full graded file: legs actually observed are reported x8 and disagreement x5, noSignature x0 — the 5 disagreements are exactly test_check_unit_consistency's five `raises(ValueError, ...)`. So (a) requiring Combined.disagreement is justified (atk_3's collapse would break a P2P test), and (b) leaving the noSignature MANNER free is justified, not over-fitting. Exercised that freedom concretely: nosig_manner.diff surfaces the unreducible case as RuntimeError instead of the callee's TypeError; `run_resolve(..., run_id='geq-nosig-manner')` -> RESOLVED: True, F2P/P2P failure lists both empty. The spec's deliberate under-specification is therefore sound in both directions — it does not admit a non-resolving impl, and it does not exclude a resolving one.
6. G-AX re-run in my own worktree: axiom_check.py exits 0 with the sound structural key.

REFINEMENT.MD LEG AUDIT: 7 legs, all legally tagged, NO kind-3 — A1=R, A2=R+I, A3=A-reference+I, A4a=R, A4b=R, A4c=R, A4d=I. The genuinely-changed op (the dimension comparison) is modeled deeply in the pure region, not axiomatized. patch.diff is the gold one-line hunk verbatim; single change site, so one prepatch file is correct. Callee provenance claim checked: the patch touches only unitsystem.py, so equivalent_dims/get_dimensional_dependencies are indeed UNCHANGED.

### ADVISORY DEFECTS (do not affect the verify=>resolve claim; no gate impact, worth a docs fix):
(a) META.JSON PROSE DRIFT. meta.json deep_model_references[0].checked_by describes the key as `sig = frozenset(get_dimensional_dependencies(.).items())`. That key is UNSOUND and refinement.md §2.1 itself argues so at length: measured in my worktree, for length**2 vs length**2.0 the real dict `==` is True (and equivalent_dims is True) while frozenset(items()) `==` is False, because Float hashing mixes in _prec. The ACTUAL axiom_check.py does NOT use a frozenset — it uses a SHA-256 digest over a structural encoding with a top-level numeric collapse, which is sound and passes. So only the meta.json summary string is stale/wrong; the executable gate and Solution.lean are correct. Recommend updating that string to match deps_key.

(b) A1 models `rest` as ALREADY-collected sub-results, i.e. eager pre-collection, while the real branch recurses LAZILY inside the loop. I found a real behavioural divergence from this: for `l1 + t1 + (b1+b2)` — where addend 2 disagrees and addend 3's OWN sub-collection raises — gold raises ValueError (short-circuits before ever collecting addend 3) but the eagerly-collecting atk_8 raises TypeError. This divergence is OUTSIDE the graded set (atk_8 still resolves), and A1's justification does state the sub-collection is an unchanged read-only input, but the refinement.md narrative does not acknowledge that eager-vs-lazy collection order is observable at all. Recommend a sentence in A1 noting the ordering is unobserved by the graded set rather than leaving it implicit.

VERDICT: SOUND. 9 same-spec attacks encoded and fully verified (>=5 required); 8 semantically rejected across the required distinct classes (prepatch bug, partial-domain, boundary, control-flow-effect/priority, ungrounded-oracle echo, both outcome collapses, wrong reported dimension); the single verifying wrong-impl candidate had its faithful patch materialized and EXECUTED through the official harness and it RESOLVED, so no verify-but-not-resolve witness exists. Positive control verifies; prepatch reproduced and rejected. No BROKEN evidence; nothing left incomplete.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The only verifying wrong-impl candidate (atk_8, the ungrounded-oracle echo `return combineSpec first rest`) had its faithful refined patch materialized and RESOLVED under the official harness (F2P test_issue_24211 pass, all 31 P2P pass), so it is not a counterexample: the echo is behaviourally gold on the graded set. Every genuinely-divergent impl (prepatch surface test, both outcome-identity collapses, priority inversion, missing-signature wildcard, partial domain on rest=[], boundary off-by-one, wrong reported dimension) was REJECTED by the frozen spec.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Own worktrees at base_commit e8c22f6eac created there (repo, repo_atk8, repo_ns). same_spec == True confirmed for ALL 9 attacks + prepatch.lean + pos_control.lean (byte-identical axioms/pure/pre/post; only the impl region and the prove_correct body edited). Positive control pos_control.lean verifies EXIT=0. Bundle's own Solution_prepatch.lean re-verified as REJECTED (EXIT=1, unsolved goal on invariant_2).

COMMANDS (from swe-proof): `bash scripts/lean_verify.sh atk_N.lean`; launched 4-at-a-time as background jobs (batches {1,2,3,4}, {5,6,7,11}, {9,10}).

### ATTACK RESULTS (9 same-spec wrong impls; 8 rejected, 1 verified-and-resolves):
- atk_1 PREPATCH BUG re-encoded, surface-expression test `a.dim.surf == first.dim.surf` instead of deps-equality -> EXIT=1 REJECTED. Leftover goal: `(if (rest[i-1]!.dim.surf == first.dim.surf) = true then chk else Check.disagreeing) = checkStep first.dim.deps rest[i-1]! chk`. Semantic, not a script error.
- atk_2 OUTCOME COLLAPSE noSignature -> disagreement -> EXIT=1 REJECTED (`ensures_4` goal reduces to `False`).
- atk_3 OUTCOME COLLAPSE disagreement -> noSignature (the other direction) -> EXIT=1 REJECTED.
- atk_4 PRIORITY INVERTED (a later failure overrides the leftmost one) -> EXIT=1 REJECTED.
- atk_5 MISSING-SIGNATURE WILDCARD (any absent signature anywhere wins, overriding a leftmost disagreement) -> EXIT=1 REJECTED on `ensures_2`, goal `¬i_2 = Check.disagreeing`. NOTE: my first atk_5 draft was accidentally gold-equivalent and a second draft failed on a WPGen parse error (early `return` before a `match`); both were discarded and the attack was REBUILT so the failure is semantic. Same for atk_6/atk_7, which first failed on my own proof-script errors (unknown identifier / `subst done_1` failure) — rebuilt with a deliberately GENEROUS `try`-wrapped proof so a leftover goal can only mean semantic rejection.
- atk_6 PARTIAL DOMAIN (correct on non-empty rest, returns disagreement on rest=[]) -> EXIT=1 REJECTED, goal `¬checkAddends first.dim.deps [] = Check.equivalent`.
- atk_7 BOUNDARY off-by-one (`while i > 1`, rest[0] never tested, its factor never added) -> EXIT=1 REJECTED.
- atk_11 WRONG REPORTED DIMENSION (reports the last addend's dim instead of the reference's; observable exactly on surface-distinct equivalents) -> EXIT=1 REJECTED, goal `i_2 = first.dim`.
- atk_8 UNGROUNDED-ORACLE ECHO `return combineSpec first rest` -> EXIT=0 VERIFIES. Mandatory resolve executed: faithful refined patch written to atk_8_faithful.diff (eager pre-collection of every addend's sub-result, then the front-recursive checkAddends fold, then dispatch on its single verdict — combineSpec's exact shape), `run_resolve('sympy__sympy-24213', patch, run_id='geq-atk8-echo')` -> RESOLVED: True, COMPLETED: True, F2P failure list [], P2P failure list [] (all 31). Note 'resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)' — harness's own retry, final verdict resolved. Local pytest on the graded file also 33 passed / 1 xfailed. So verify => correct held here; NOT a counterexample.
- atk_9 (echo via the two folds, no loop) and atk_10 (eager factor-total then whole check) both EXIT=1 but on a Velvet WPGen parse limitation (`Failed to parse an assertion without names: WPGen (match ...)`), i.e. a harness/encoding artifact rather than a semantic rejection. They are therefore EXCLUDED from the attack list and are not counted as spec strength (per the retained-attack-labels rule: an encoding failure must not be re-judged as the reject lane). The oracle-echo class is instead covered soundly by atk_8, which verifies and resolves.

### A-LEG AUDIT (the assigned focus).
1. Only kind-A content is one A-reference; meta.json `axioms: []` — no consumed contract, so nothing to discharge. Confirmed there is no `equivalentDims` axiom hiding the changed op.
2. A-reference correspondence INDEPENDENTLY re-derived, not taken on trust. Re-implemented the Lean pure region (checkStep/checkAddends/combineSpec, with deps as Option) in Python over REAL SymPy Dimensions and diffed its 3-outcome behaviour against the real PATCHED Add branch: diff_fuzz.py, 34,880 cases (all ordered pairs over a 32-dimension pool + 20k ordered triples + 20k random length-2..5 sums, pool mixing Integer/Float/Rational exponents, Float precisions 5 and 50, symbolic and nested-symbolic powers, the hash-colliding -1/-2 pair, and Add-named unreducible dimensions) -> MISMATCHES: 0.
3. Verified the callee facts myself in the patched worktree: equivalent_dims(velocity, acceleration*time)=True while surf-equality is False; (length,time)=False; (force, mass*acceleration)=True; (length**2, length**2.0)=True with surf-equality False (the Float-precision witness). get_dimensional_dependencies raises TypeError on Dimension(length+time) — the partiality that grounds `deps = none`.
4. A4d LEFTMOST-FAILURE claim empirically CONFIRMED against the real patched repo (not just asserted in prose): `l1 + t1 + b1` (disagreement first) -> ValueError, whereas `l1 + b1 + t1` (no-signature first) -> TypeError. Same failure multiset, different order, different observable class — so the ordering is genuinely observable and checkStep's front recursion is the right order. atk_4 confirms the spec rejects the inversion.
5. A4b/A4c ASYMMETRY independently MEASURED rather than trusted. Instrumented the patched branch and ran the full graded file: legs actually observed are reported x8 and disagreement x5, noSignature x0 — the 5 disagreements are exactly test_check_unit_consistency's five `raises(ValueError, ...)`. So (a) requiring Combined.disagreement is justified (atk_3's collapse would break a P2P test), and (b) leaving the noSignature MANNER free is justified, not over-fitting. Exercised that freedom concretely: nosig_manner.diff surfaces the unreducible case as RuntimeError instead of the callee's TypeError; `run_resolve(..., run_id='geq-nosig-manner')` -> RESOLVED: True, F2P/P2P failure lists both empty. The spec's deliberate under-specification is therefore sound in both directions — it does not admit a non-resolving impl, and it does not exclude a resolving one.
6. G-AX re-run in my own worktree: axiom_check.py exits 0 with the sound structural key.

REFINEMENT.MD LEG AUDIT: 7 legs, all legally tagged, NO kind-3 — A1=R, A2=R+I, A3=A-reference+I, A4a=R, A4b=R, A4c=R, A4d=I. The genuinely-changed op (the dimension comparison) is modeled deeply in the pure region, not axiomatized. patch.diff is the gold one-line hunk verbatim; single change site, so one prepatch file is correct. Callee provenance claim checked: the patch touches only unitsystem.py, so equivalent_dims/get_dimensional_dependencies are indeed UNCHANGED.

### ADVISORY DEFECTS (do not affect the verify=>resolve claim; no gate impact, worth a docs fix):
(a) META.JSON PROSE DRIFT. meta.json deep_model_references[0].checked_by describes the key as `sig = frozenset(get_dimensional_dependencies(.).items())`. That key is UNSOUND and refinement.md §2.1 itself argues so at length: measured in my worktree, for length**2 vs length**2.0 the real dict `==` is True (and equivalent_dims is True) while frozenset(items()) `==` is False, because Float hashing mixes in _prec. The ACTUAL axiom_check.py does NOT use a frozenset — it uses a SHA-256 digest over a structural encoding with a top-level numeric collapse, which is sound and passes. So only the meta.json summary string is stale/wrong; the executable gate and Solution.lean are correct. Recommend updating that string to match deps_key.

(b) A1 models `rest` as ALREADY-collected sub-results, i.e. eager pre-collection, while the real branch recurses LAZILY inside the loop. I found a real behavioural divergence from this: for `l1 + t1 + (b1+b2)` — where addend 2 disagrees and addend 3's OWN sub-collection raises — gold raises ValueError (short-circuits before ever collecting addend 3) but the eagerly-collecting atk_8 raises TypeError. This divergence is OUTSIDE the graded set (atk_8 still resolves), and A1's justification does state the sub-collection is an unchanged read-only input, but the refinement.md narrative does not acknowledge that eager-vs-lazy collection order is observable at all. Recommend a sentence in A1 noting the ordering is unobserved by the graded set rather than leaving it implicit.

VERDICT: SOUND. 9 same-spec attacks encoded and fully verified (>=5 required); 8 semantically rejected across the required distinct classes (prepatch bug, partial-domain, boundary, control-flow-effect/priority, ungrounded-oracle echo, both outcome collapses, wrong reported dimension); the single verifying wrong-impl candidate had its faithful patch materialized and EXECUTED through the official harness and it RESOLVED, so no verify-but-not-resolve witness exists. Positive control verifies; prepatch reproduced and rejected. No BROKEN evidence; nothing left incomplete.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL(2) faithfulness-break on sympy__sympy-24213/velvet. Reference = base_commit worktree (e8c22f6ea) with patch.diff APPLIED (, `git apply` OK); base used only for the UNCHANGED callee equivalent_dims/get_dimensional_dependencies. NO divergence found between combineSpec and the real patched Add branch.

INTEGRITY. sha256 Solution.lean=50f16c734dfd... , Solution_prepatch.lean=5b95a50f901a..., axiom_check.py=8df96dc5534b..., conformance_check.py=42043ef8319a... — all match meta.json gate `sources` exactly, so the spec region is the one the gates were recorded against. spec_signature(Solution.lean, velvet backend) computed via swebench_unified.markers; same_spec self-check True; spec_view sha 5987d28edb59f7c6... The spec_view I audited contains the full pure region (Dim/Addend/Check/checkStep/checkAddends/sumFactors/Combined/combineSpec) plus the 4 `ensures`, with impl+proof elided — i.e. the contract is entirely inside the frozen region. scripts/lean_verify.sh Solution.lean -> exit 0.

### WHAT THE SPEC CLAIMS (the strong parts, each one attacked):
(1) dimensional equivalence == equality of a SINGLE handle `deps : Option Int`;
(2) reduction failure is PARTIAL and preempts any verdict -> `unreducible`/noSignature, kept DISTINCT from `disagreeing`/disagreement;
(3) LEFTMOST non-certified addend decides, in the manner IT failed (A4d);
(4) reported = (first.factor + sumFactors rest, first.dim).

ATTACK 1 — is (1) even representable? Modeling equivalence as handle EQUALITY forces the real relation to be an equivalence relation (refl/sym/trans). The real relation is dict `==` over get_dimensional_dependencies, and SymPy numeric `==` crosses type/precision (Integer(2)==Float(2.0) is True while hash differs), which is exactly where transitivity usually dies. Fuzzed for a break: (a) 24-dim structured pool -> 0 refl/sym/trans violations, 7 classes; (b) 93-dim pool of Float/Rational exponents at precisions 5,10,15,16,17,20,25,30,50 plus 1e-20/1e20/sqrt2/pi/E/near-ULP perturbations (Float(1)+1e-16, Float(1,30)+Float('1e-25',30)), single- and two-key dicts -> 0 refl, 0 sym, 0 trans violations; (c) symbolic exponents where dict-== could return non-boolean (x+y vs y+x, sqrt(x**2), sin^2+cos^2, cbrt(x**3), Float(1.0)*x, pi*x/pi, positive-symbol n) -> 0 raising pairs, 0 refl/sym/trans violations, and the merged classes are exactly the surface-distinct-but-equivalent ones the discriminator rests on. So the single-handle carrier is sound on everything I could reach; I could NOT construct the non-transitivity that would make (1) too strong.

ATTACK 2 — is (2)'s exception partition real? The spec's three-way split only tracks the repo if 'reduction failed' and 'compared and unequal' land in different observable classes (real: TypeError vs ValueError). Swept 1166 constructed Dimensions (17 atoms x 17 functions x binary add/mul/pow/sub/div combinations, plus besselj/Piecewise/KroneckerDelta/Max/Min/floor/gamma/erf/zeta/LambertW, oo/zoo/nan/I exponents): reduction outcomes partition into EXACTLY {ok: 859, TypeError: 307}. ZERO non-TypeError failure classes — no ValueError/KeyError/RecursionError leak that would collapse noSignature into the disagreement class. Cross-checked equivalent_dims over 784 exotic pairs: {TypeError 528, True 60, False 196} — every both-signatures-present pair RETURNED a verdict rather than raising, which is the precondition the `disagreeing` leg needs. Note also L**zoo and L**nan reduce to {} (dimensionless) rather than raising, and abs/floor/Max reduce — the model handles these via deps, not by assuming they fail.

ATTACK 3 — end-to-end differential, spec class vs real class. Built Quantities with set_quantity_dimension/set_quantity_scale_factor and read model inputs off the REAL expr.args order (so no args-ordering artifact can masquerade as a divergence), then compared combineSpec transliterated verbatim from the Lean against real_outcome (reported / ValueError->disagreement / TypeError->noSignature): (a) EXHAUSTIVE over all 2- and 3-addend combinations of a 20-dim pool = 8400 probes, 0 disagreements — and for the `reported` leg I additionally checked the factor total AND that the returned dim is the reference addend's dim (0 DISAGREE-FACTOR, 0 DISAGREE-DIM); (b) 4000 randomized 2..5-addend sums, 0 disagreements; (c) RICH expressions — addends built as nested Mul/Pow/Add trees so the dimension carriers reaching the Add branch are produced by the UNCHANGED recursive sub-collection rather than hand-set — 7649 probes (1351 skipped where a sub-collection itself raised, i.e. outside the modeled function per A1), 0 disagreements. Total ~20k end-to-end probes, zero class divergence.

ATTACK 4 — (3), the leftmost/manner claim, the easiest thing to get wrong. Nine targeted probes mixing a disagreeing addend (time vs length) with a signature-less one (Dimension(length+time), Dimension(sin(length))) at different positions, including 4-addend R,R,D,U and R,R,U,D and duplicated-failure R,D,D,U / R,U,U,D: spec == real on all 9. Confirmed the ordering is genuinely OBSERVABLE on the patched tree (D-then-U -> disagreement; U-then-D -> noSignature), so this ensures is discriminating rather than vacuous, and the spec picks the same side as the repo.

NOTED, NOT A DEFECT (declared abstraction). The factor carrier is `Int` with a RIGHT fold (first.factor + sumFactors rest) while the repo does a LEFT fold (`factor += addend_factor`). These genuinely differ on Float scale factors: e.g. addends with scale factors [-1e20, 1e20, 1.0, 1.0] give spec 0 vs real 2.0 (205 true numeric divergences found in 2000 Float probes, after filtering Float-precision artifacts). I do NOT report this as UNFAITHFUL: mapping.md §2 row 1 explicitly DECLARES the Int carrier as an order-only R-refinement of the factor's identity under `+`, and on the declared bijection (Int / exact SymPy numbers) Int `+` is associative and commutative so the two folds coincide — which is why all ~20k integer-factor probes above show 0 factor mismatches.

The graded set stays inside that domain: F2P test_issue_24211 and P2P test_factor_and_dimension use Integer/Rational/symbolic factors (Rational(3,2), Rational(5,2), 3000, x, y) with no Floats, and test_check_unit_consistency observes only the ValueError class. Float non-associativity is therefore outside the declared carrier, i.e. a scope choice recorded in mapping.md, not the spec being too strong on its own domain. Flagging it for G-EQ/refinement-fidelity rather than this gate.

Also checked and clean: combineSpec on rest=[] reports (a wider domain than the repo, where an Add always has >=2 args — weaker, not stronger); `surf` is carried but never gates the decision, so it cannot over-constrain; the reported dim is the reference addend's dim, matching `return factor, dim`.

CONCLUSION: the modeled function agrees with the real patched callee on every input I could construct across ~20k end-to-end probes plus ~2k carrier-representability and ~1.9k exception-partition probes. No diverging input exists to cite, so the spec is not too strong and does not drift from repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Scope: velvet/Solution.lean spec view for sympy__sympy-24213, judged against the solver-visible problem_statement ONLY. instance.json hints_text has len 0, so no hint-derived excuse was available or used.

NO RELAXATION IN PLAY (checked, not assumed): no RELAXED_LEAKAGE.md anywhere under the instance dir (find/glob -> nothing), and no relaxed_leakage key in meta.json (recursive walk for any key matching /relax|leak/i returned only gates/G-LEAK). So there is no relaxation argument to re-derive or discount -- this is a plain strict-mode judgement.

ARTIFACT IDENTITY FIRST: sha256(Solution.lean)=50f16c734dfd... and sha256(Solution_prepatch.lean)=5b95a50f901a... match the sources recorded in G-LEAK/G-DIFF/G-GOLD/G-MUT/G-HYGIENE, so the records describe the bytes I read.

### My own measurements
1. Spec-region identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. I rendered BOTH views and hashed them: sha256 = bf8f0c6bb9abb1d780136a78e570d9ae78802663c8b21b3858918de293127d81 for each, byte-identical (and equal to the spec_view hash G-HYGIENE recorded). The gold/prepatch difference (deps-comparison vs surf-comparison) lives entirely inside the elided impl region, so the rival pair exposes no extra spec-side text.
2. Mechanical screen RE-RUN by me, not read off the record: leakage.screen(src, velvet, inst['patch'], inst['problem_statement'], inst['test_patch']) -> passed=True, hard_failures=[], warnings=[].
3. Screen is not vacuously passing -- negative controls I injected into the spec region: (B) the gold added line 'if not self.get_dimension_system().equivalent_dims(dim, addend_dim):' as a comment -> L1 gold-patch line reproduced; (C) 'this fixes the bug in the previously incorrect check' -> L3 narration; (D) 'sympy/physics/units/unitsystem.py' -> L2 patched file path. All three fire, baseline passes. Control (A), injecting 'equivalent_dims' into a spec def name, did NOT fire -- _patch_changed_symbols only harvests def/class names from the hunk and this one-line hunk has none, so the identifier leg is VACUOUS for this instance. I therefore covered it by hand rather than trusting it.
4. Manual identifier/token probes on the rendered view (the leg the screen cannot do here): 'equivalent_dims', 'get_dimension_system', 'get_dimensional_dependencies', 'collect_factor', 'addend_dim', 'unitsystem', 'sympy', 'dimensions.py', 'Quantity', 'ValueError', 'TypeError', 'velocity', 'acceleration', 'meter', 'second' -- ALL ABSENT. No diff markers ('@@', '+++', 'diff --git'). Narration scan via leakage._NARRATION_RE over the whole view returned the EMPTY SET. Test identifiers from test_patch (test_issue_24211 = the F2P, test_issue_24062, test_prefixed_property) absent. Only .py mention is axiom_check.py, the bundle's own validator, not a repo path.
5. LOAD-BEARING / strip-the-narration test on the one facet the view names -- dimensional equivalence by canonical dependency signature rather than surface-expression identity. I ran the verifier myself: scripts/lean_verify.sh Solution.lean -> EXIT 0 (verifies). scripts/lean_verify.sh Solution_prepatch.lean -> FAILS, 'Solution_prepatch.lean:228:2: error: unsolved goals', residual goal exactly '(if (rest[i-1]!.dim.surf == first.dim.surf) = true then chk else Check.disagreeing) = checkStep first.dim.deps rest[i-1]! chk'. The prepatch differs ONLY by comparing surf instead of deps, so the equivalence clause genuinely does NOT verify against the PRE-patch impl -- it is a discriminator, not decoration, and cannot be stripped while keeping the spec faithful.
6. DERIVABILITY FROM PUBLIC TEXT (the actual question): the discriminator is stated in the problem_statement itself. Title: 'collect_factor_and_dimension does not detect equivalent dimensions in addition'. Traceback body: 'Dimension of "v1" is Dimension(velocity), but it should be Dimension(acceleration*time)'. Substring probes on the PS: 'equivalent dimensions' True, 'in addition' True, 'velocity' True, 'acceleration*time' True, 'Dimension of' True, 'collect_factor_and_dimension' True. A solver reading only the public statement knows the addition branch must accept dimensions that are dimensionally equivalent though surface-distinct. Conversely the PS does NOT contain 'equivalent_dims', 'get_dimension_system', 'get_dimensional_dependencies', or '!=' -- and neither does the spec view. The view names the FACET (equivalence of canonical dependency signatures) and never the callee, the file, the operator, or the one-line shape of the edit, so it stays at or below what the public statement already discloses.
7. Residual items I judged and cleared rather than skipped: (a) the partiality leg -- Dim.deps : Option Int, Check.unreducible, Combined.noSignature -- is the one concept NOT verbatim in the PS. Not a leak of the gold edit: it is a faithfulness consequence of specifying the equivalence notion the PS already names (the real reduction is partial and raises), it localizes no line, and it discriminates in the OPPOSITE direction from the gold hunk (no value reported where the surface test returned one). (b) Dim.surf is a DEAD field in the spec -- it appears only in the structure declaration and in prose, never in checkStep/checkAddends/combineSpec or any ensures clause; its only purpose is to let the prepatch rival be expressed. A solver seeing it learns only that two notions of dimension identity exist, which the PS's velocity-vs-acceleration*time traceback already conveys. Spec-surface tidiness at most, not edit disclosure.

NO FILE IN THE BUNDLE ADDRESSED ME: I swept leakage.reviewer_directed() over every .md/.py/.json/.lean under the instance dir -> zero hits, and grepped for panel/reviewer/attacker/'honest verdict'/submit-style directives -> the only matches are gate-record fields in meta.json and verdict.md (prior recorded notes), no prose aimed at the reviewer. Nothing to report on that axis.

STALE PRIOR RECORD (flagging so the record shows I measured rather than echoed): the G-PANEL-3 note already in meta.json, and meta.json's own 'discriminator' field, both describe a DIFFERENT spec revision than the file I read -- they cite a two-valued 'ok = allEquiv first.dim.deps (rest.drop i)' invariant and a prepatch failure at ':161:2', whereas the current Solution.lean is three-valued (inductive Check / Combined) and fails at ':228:2'. I did not inherit that note; every number above is my own re-measurement on the current bytes. Same for meta.deep_model_references, which still names 'allEquiv' -- a symbol absent from the current file.

OUT OF MY SCOPE but seen, not missed: G-EQ fails (atk_1.lean verifies but its patch breaks P2P test_check_unit_consistency) and G-PANEL-1/G-PANEL-2 fail (spec-too-weak; and a deep-model unsoundness where the _struct_key leaf encoding drops SymPy assumptions, making the deps key COARSER than the dict == that equivalent_dims performs). Those are weakness/faithfulness defects -- they make the spec wrong, not more revealing of the gold edit -- and none of them is a gate my disposition leans on, since no relaxation is in play. They do not change the leakage verdict on this facet.

Verdict: NO-LEAKAGE. The spec view is byte-identical across the pre/post pair, carries no repo identifier, file path, gold line, test name, or diff artifact, contains zero narration tokens, and the single discriminating concept it names -- dimensional equivalence rather than surface-expression identity in an addition -- is independently derivable from the public problem_statement's title and traceback while being load-bearing against the pre-patch impl.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
