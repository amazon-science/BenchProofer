# P2 adversarial audit — django__django-9296

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1_range_mul0.lean`, `atk_3_echo.lean`, `atk_5_underdet_loop.lean`, `atk_6_branch_emod.lean`, `atk_10_single_loop_cost.lean` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2_prepatch.lean`, `atk_4_widened_counted.lean`, `atk_7_live_take_len.lean`, `atk_8_offdomain.lean`, `atk_9_droplast.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NO COUNTEREXAMPLE FOUND. 10 same-spec attacks across 6 distinct classes; 5 verify, and every one of those 5 has a faithful refined patch that RESOLVES under the official harness (F2P 1/1, P2P 20/20 each), discriminated against two controls that also resolve (gold 51.0s; ctl_frozen, my OWN faithful mapping.md 2.1 realization of the FROZEN impl, 48.4s). Every result was executed, not speculated.

The sharpest attack is atk_5_underdet_loop, aimed at the one hole refinement.md B''''' names as open (item 2: "R3 rests on its side condition ... an impl whose I /\ done_with leaves the post-state underdetermined is not covered"). It runs a prologue loop `while j > 0 invariant True done_with j = 0 decreasing j do c := c + 1; j := j - 1` with j := 2^(64+n), then the frozen traversal, and RETURNS an expression that READS c: `(List.replicate c []).drop c ++ result`. The annotation determines j (=0) but says nothing whatsoever about c, and c is not dead, so BOTH R3's determinacy clause and R4's deadness clause are shut off by their own stated side conditions. It verifies (exit 0). But it still resolves, because R1's constant clause independently closes the gap: `(List.replicate c a).drop c` is provably [] for EVERY c, so the read realizes as a constant and c becomes unobservable after all. Underdetermination of a variable is not the same thing as observability of it -- the postcondition `out = pageSeq pageRange` pins the RETURN VALUE, so any expression a verifying impl returns is already forced to gold's output, whatever the intermediate schedule did.

atk_10_single_loop_cost re-encodes the recorded atk_7_single_loop_cost byte-equivalently (ONE loop, counter widened to pageRange.length + 2^(64+n), no prologue, extra iterations discharged in-proof by List.drop_eq_nil_of_le / List.getElem?_eq_none). It verifies, and its R3 realization resolves in 49.8s -- reproducing refinement.md B'''''s own measurement (85.1s) rather than contradicting it.

Two REJECTIONS are the positive findings that the claimed repairs have real teeth. atk_8_offdomain applies the accessor at an index the object does not name (`pageOf ⟨numPages + 1, by omega⟩`) and is rejected with `omega could not prove the goal` -- the PageIdx subtype carrier genuinely makes the off-domain call INEXPRESSIBLE, which is the hole the first recorded G-EQ round found. atk_7_live_take_len reads a huge derived length at the return (`result.take z` with z = (List.replicate 2^(64+n) 0).length) and is rejected on the postcondition -- a LIVE derived length cannot be laundered, so R4's syntactic deadness decision is not doing load-bearing work for a wrong impl.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_range_mul0.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,8 +74,9 @@
   ensures out = pageSeq pageRange
   do
     -- impl-start
+    let _z : Nat := 0 * (List.range (2 ^ (64 + pageRange.length))).length
     let mut result : List (List Int) := []
-    let mut i := pageRange.length
+    let mut i := pageRange.length + _z
     while i > 0
       invariant 0 ≤ i ∧ i ≤ pageRange.length
       invariant result = pageSeq (pageRange.drop i)
```

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,17 +74,7 @@
   ensures out = pageSeq pageRange
   do
     -- impl-start
-    let mut result : List (List Int) := []
-    let mut i := pageRange.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ pageRange.length
-      invariant result = pageSeq (pageRange.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := pageRange[i - 1]?
-      result := (p.map pageOf).toList ++ result
-      i := i - 1
+    let result : List (List Int) := []
     return result
     -- impl-end
 
@@ -105,5 +95,3 @@
 
 prove_correct enumeratePages by
   loom_solve
-  rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
-  simp_all
```

Attack 3 — `atk_3_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -74,18 +74,7 @@
   ensures out = pageSeq pageRange
   do
     -- impl-start
-    let mut result : List (List Int) := []
-    let mut i := pageRange.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ pageRange.length
-      invariant result = pageSeq (pageRange.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := pageRange[i - 1]?
-      result := (p.map pageOf).toList ++ result
-      i := i - 1
-    return result
+    return pageSeq pageRange
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the index at
@@ -105,5 +94,3 @@
 
 prove_correct enumeratePages by
   loom_solve
-  rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
-  simp_all
```

Attack 4 — `atk_4_widened_counted.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -75,17 +75,18 @@
   do
     -- impl-start
     let mut result : List (List Int) := []
-    let mut i := pageRange.length
+    let mut n : Nat := 0
+    let mut i := pageRange.length + 2 ^ (64 + pageRange.length)
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ pageRange.length
       invariant result = pageSeq (pageRange.drop i)
       done_with i = 0
       decreasing i
     do
       let p := pageRange[i - 1]?
       result := (p.map pageOf).toList ++ result
+      n := n + 1
       i := i - 1
-    return result
+    return (if n = 0 then result else result)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the index at
@@ -105,5 +106,3 @@
 
 prove_correct enumeratePages by
   loom_solve
-  rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
-  simp_all
```

Attack 5 — `atk_5_underdet_loop.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -75,6 +75,15 @@
   do
     -- impl-start
     let mut result : List (List Int) := []
+    let mut c : Nat := 0
+    let mut j : Nat := 2 ^ (64 + pageRange.length)
+    while j > 0
+      invariant True
+      done_with j = 0
+      decreasing j
+    do
+      c := c + 1
+      j := j - 1
     let mut i := pageRange.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ pageRange.length
@@ -85,7 +94,7 @@
       let p := pageRange[i - 1]?
       result := (p.map pageOf).toList ++ result
       i := i - 1
-    return result
+    return (List.replicate c ([] : List Int)).drop c ++ result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the index at
@@ -105,5 +114,7 @@
 
 prove_correct enumeratePages by
   loom_solve
-  rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
-  simp_all
+  all_goals
+    first
+      | (rw [pageSeq_drop_step pageRange _ (by omega) (by omega)]; simp_all)
+      | simp_all
```

Attack 6 — `atk_6_branch_emod.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -83,7 +83,10 @@
       decreasing i
     do
       let p := pageRange[i - 1]?
-      result := (p.map pageOf).toList ++ result
+      if ((1 : Int) % (-2)) < 0 then
+        result := result
+      else
+        result := (p.map pageOf).toList ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7_live_take_len.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,7 +85,8 @@
       let p := pageRange[i - 1]?
       result := (p.map pageOf).toList ++ result
       i := i - 1
-    return result
+    let z : Nat := (List.replicate (2 ^ (64 + pageRange.length)) (0 : Int)).length
+    return result.take z
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the index at
@@ -105,5 +106,6 @@
 
 prove_correct enumeratePages by
   loom_solve
-  rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
-  simp_all
+  · rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
+    simp_all
+  · simp_all
```

Attack 8 — `atk_8_offdomain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,6 +85,7 @@
       let p := pageRange[i - 1]?
       result := (p.map pageOf).toList ++ result
       i := i - 1
+    let _q : List Int := pageOf ⟨numPages + 1, by omega⟩
     return result
     -- impl-end
 
```

Attack 9 — `atk_9_droplast.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -85,7 +85,7 @@
       let p := pageRange[i - 1]?
       result := (p.map pageOf).toList ++ result
       i := i - 1
-    return result
+    return result.take (pageRange.length - 1)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the index at
```

Attack 10 — `atk_10_single_loop_cost.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -75,9 +75,8 @@
   do
     -- impl-start
     let mut result : List (List Int) := []
-    let mut i := pageRange.length
+    let mut i := pageRange.length + 2 ^ (64 + pageRange.length)
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ pageRange.length
       invariant result = pageSeq (pageRange.drop i)
       done_with i = 0
       decreasing i
@@ -105,5 +104,14 @@
 
 prove_correct enumeratePages by
   loom_solve
-  rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
-  simp_all
+  · by_cases hle : i ≤ pageRange.length
+    · rw [pageSeq_drop_step pageRange i (by omega) (by omega)]
+      simp_all
+    · have h1 : pageRange.length ≤ i - 1 := by omega
+      have h2 : pageRange.length ≤ i := by omega
+      rw [List.drop_eq_nil_of_le h1]
+      rw [List.getElem?_eq_none (by omega)]
+      rw [List.drop_eq_nil_of_le h2] at invariant_1
+      simp_all
+  · rw [List.drop_eq_nil_of_le (Nat.le_add_right _ _)]
+    simp [pageSeq]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** all 11 files (10 attacks + pos_control) are same_spec=True vs frozen Solution.lean (sha256 d68e534c56...), checked with swebench_unified.markers.same_spec / get_backend('velvet').language. Only the impl region and the elided prove_correct tactic body differ; axioms/pure/pre/post byte-identical. NOTE for the runner: Velvet spec_view elides BOTH the impl region AND prove_correct bodies, so several attacks legitimately carry their own tactic bodies (needed because a changed impl leaves different goals). The top-level pageSeq_drop_step lemma is spec-visible and was left untouched in every file.

### Commands
- verify: bash scripts/lean_verify.sh <file> (420s cap used for atk_5/atk_10)
- same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>.lean').read(), b.language))"
- resolve: python3 do_resolve.py <label> <patchfile>  (wraps swebench_unified.harness.run_resolve)

**RESOLVE DISCIPLINE:** run STRICTLY one at a time via serial_resolves.sh, since all 7 runs are on the SAME instance and --cache_level env deletes that instance's image on completion (a concurrent second run dies ImageNotFound 404 and would take the gold control with it). Wall times 45.7-51.0s each, 7 runs sequentially.

### VERIFY RESULTS (10 attacks, 6 classes)
  VERIFIES: atk_1_range_mul0 (derived-length/R2, live `_z` read by the counter init), atk_3_echo (ungrounded-oracle echo), atk_5_underdet_loop (R3 determinacy side condition, the named open item), atk_6_branch_emod (control-flow effect via Euclidean Int.emod guard), atk_10_single_loop_cost (sharpest R3 shape)
  REJECTED: atk_2_prepatch (PREPATCH BUG re-encoded -> exit 1, so prepatch_reproduced=true), atk_4_widened_counted (widened counter + live iteration count), atk_7_live_take_len (LIVE derived length at return), atk_8_offdomain (partial-domain/BOUNDARY, blocked by the PageIdx carrier), atk_9_droplast (boundary off-by-one)
  pos_control (identical to the frozen spec file) verifies -> non-vacuity established. It is by construction incapable of demonstrating spec weakness; it is here only as the required non-vacuity control.

### RESOLVE RESULTS (all completed=True, all patch_successfully_applied=True, F2P 1/1 and P2P 20/20 for every row)
  gold 51.0s resolved=True   <-- the load-bearing control: the oracle CAN refute on this instance, so the attack rows carry information
  ctl_frozen 48.4s resolved=True  <-- MY OWN faithful realization of the FROZEN impl (same `_nat_sub` prelude, same Option-shaped read `page_range[k] if 0 <= k < len(...) else None`, same backward fold). Each attack patch is a minimal delta from this, which is what makes the resolve rows attributable to the attacks rather than to my Python style.
  atk_1 46.8s / atk_3 45.7s / atk_5 48.9s / atk_6 48.6s / atk_10 49.8s -- all resolved=True
All 5 patches were git apply --check'd in the base_commit worktree AND smoke-tested locally (each yields [[1,2],[3]] for Paginator([1,2,3],2), matching gold) before submission.

REFINEMENT.MD LEG AUDIT (obligation 3): PASSES. Section A tables 4 numbered legs over the single hunk: A1 (pageRange <-> self.page_range) = R; A2 (backward while <-> the for loop) = I; A2'/A2''/A2''' (Option-shaped read; Nat counter arithmetic; any other arithmetic a verified impl performs) = R; A3 (pageOf <-> Paginator.page) = A-reference; A4 (the fold / yield) = I. Tag histogram: 1 A-reference, 2 I, 1 R (the A2-prime family sharing the R row). NO KIND-3 leg, and section B states this correctly: the operation that genuinely CHANGED (the iteration protocol) is modeled DEEPLY as the spelled-out fold pageSeq over the opaque pageOf, not hidden behind a contract about the function under change. There is no consumed axiom at all, so no A-consumed leg exists to audit.

A-LEG CORRESPONDENCE (independently re-measured by me, not taken from the G-AX record): pageOf <-> Paginator.page(self, number) at django/core/paginator.py:67, UNCHANGED by patch.diff (the gold hunk only ADDS `__iter__` between `__init__` and validate_number; I read the base_commit source to confirm page/validate_number/num_pages/page_range are untouched). I re-ran properties (a) determinism, (b) list(iter(paginator)) == [list(page(n)) for n in page_range], and (c) THE DOMAIN dom(page) == list(page_range) == [1..num_pages] in both directions over 7 boundary configs -- 0 violations. Property (c) is what licenses the PageIdx carrier, and atk_8_offdomain is the executable confirmation that the carrier really refuses numPages+1 rather than merely claiming to. mapping.md's binding of numPages to the num_pages cached_property and page_range to range(1, num_pages+1) matches the real source.

**WHY I DID NOT INHERIT THE RECORDED BROKEN VERDICT:** meta.json records G-EQ=fail from 21:46 (whose own detail says the role did not run: "agent CLI timed out after 14400s"), with retained evidence from an earlier round naming atk_range_mul0 as a verify-but-not-resolve witness. Solution.lean is UNCHANGED since 04:33 (sha256 d68e534c56..., matching every gate's source digest), while mapping.md and refinement.md were rewritten at 21:53 -- i.e. the repair was to the REFINEMENT MAP (rules R0-R4), not to the spec. I therefore re-encoded that recorded counterexample myself (atk_1_range_mul0, in its exact live-`_z` form) and measured its faithful patch under the CURRENT map: it RESOLVES. Under R2 ("realize the length, not the list": (List.range n).length is n by List.length_range, never len(list(range(n)))) plus R1's constant clause (0 * n = 0), the OverflowError the old round measured was a mistranslation, not a spec hole. Same for atk_6 under R0 ((1 : Int) % (-2) is Int.emod = 1, so the guard is the constant False) and atk_10 under R3.

RESIDUAL RISK, stated plainly. The map's rules are extensional laws (R0 closed term -> its value; R1 open term -> a TOTAL Python function equal to the Lean one; R2 composite -> its own defining equation; R3 annotated statement -> its denotation; R4 unread binding -> the identity), and they are backstopped by single-valuedness: the postcondition `out = pageSeq pageRange` pins the RETURN VALUE, so any impl that verifies computes gold's function, and a faithful realization of it therefore resolves.

My attacks probed the two clauses that carry visible side conditions (R3 determinacy via atk_5/atk_4, R4 deadness via atk_7) and could not turn either into a verify-but-not-resolve witness: where the side condition genuinely fails, either the module stops verifying (atk_4, atk_7) or another rule independently forces the constant (atk_5). What remains open is the map's own admitted item 1 -- genuine COST, i.e. a realization computing the right value by a worse algorithm, which is latitude the gold patch has too and which no F2P/P2P outcome distinguishes. That is not verify=/=>correct and I do not report it as a defect.

I also confirmed the two verifier-limit notes are not spec properties: my atk_4/atk_10 first drafts failed on PROOF ENGINEERING (rewrite/omega/rename_i), not on an obligation, and I repaired them until atk_10 verified rather than banking the failure as a rejection.

**VERDICT:** SOUND -- 10 attacks run (>= 5 required) in 6 distinct classes (partial-domain/boundary, control-flow-effect, ungrounded-oracle echo, derived-length composite, loop-schedule/R3, prepatch), 5 verifying, and every verifying attack's materialized faithful patch RESOLVES against a certified-resolving gold control.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1_range_mul0.lean`, `atk_3_echo.lean`, `atk_5_underdet_loop.lean`, `atk_6_branch_emod.lean`, `atk_10_single_loop_cost.lean` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2_prepatch.lean`, `atk_4_widened_counted.lean`, `atk_7_live_take_len.lean`, `atk_8_offdomain.lean`, `atk_9_droplast.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NO COUNTEREXAMPLE FOUND. 10 same-spec attacks across 6 distinct classes; 5 verify, and every one of those 5 has a faithful refined patch that RESOLVES under the official harness (F2P 1/1, P2P 20/20 each), discriminated against two controls that also resolve (gold 51.0s; ctl_frozen, my OWN faithful mapping.md 2.1 realization of the FROZEN impl, 48.4s). Every result was executed, not speculated.

The sharpest attack is atk_5_underdet_loop, aimed at the one hole refinement.md B''''' names as open (item 2: "R3 rests on its side condition ... an impl whose I /\ done_with leaves the post-state underdetermined is not covered"). It runs a prologue loop `while j > 0 invariant True done_with j = 0 decreasing j do c := c + 1; j := j - 1` with j := 2^(64+n), then the frozen traversal, and RETURNS an expression that READS c: `(List.replicate c []).drop c ++ result`. The annotation determines j (=0) but says nothing whatsoever about c, and c is not dead, so BOTH R3's determinacy clause and R4's deadness clause are shut off by their own stated side conditions. It verifies (exit 0). But it still resolves, because R1's constant clause independently closes the gap: `(List.replicate c a).drop c` is provably [] for EVERY c, so the read realizes as a constant and c becomes unobservable after all. Underdetermination of a variable is not the same thing as observability of it -- the postcondition `out = pageSeq pageRange` pins the RETURN VALUE, so any expression a verifying impl returns is already forced to gold's output, whatever the intermediate schedule did.

atk_10_single_loop_cost re-encodes the recorded atk_7_single_loop_cost byte-equivalently (ONE loop, counter widened to pageRange.length + 2^(64+n), no prologue, extra iterations discharged in-proof by List.drop_eq_nil_of_le / List.getElem?_eq_none). It verifies, and its R3 realization resolves in 49.8s -- reproducing refinement.md B'''''s own measurement (85.1s) rather than contradicting it.

Two REJECTIONS are the positive findings that the claimed repairs have real teeth. atk_8_offdomain applies the accessor at an index the object does not name (`pageOf ⟨numPages + 1, by omega⟩`) and is rejected with `omega could not prove the goal` -- the PageIdx subtype carrier genuinely makes the off-domain call INEXPRESSIBLE, which is the hole the first recorded G-EQ round found. atk_7_live_take_len reads a huge derived length at the return (`result.take z` with z = (List.replicate 2^(64+n) 0).length) and is rejected on the postcondition -- a LIVE derived length cannot be laundered, so R4's syntactic deadness decision is not doing load-bearing work for a wrong impl.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_range_mul0.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_widened_counted.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_underdet_loop.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6_branch_emod.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_live_take_len.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_offdomain.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_droplast.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_single_loop_cost.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SAME-SPEC:** all 11 files (10 attacks + pos_control) are same_spec=True vs frozen Solution.lean (sha256 d68e534c56...), checked with swebench_unified.markers.same_spec / get_backend('velvet').language. Only the impl region and the elided prove_correct tactic body differ; axioms/pure/pre/post byte-identical. NOTE for the runner: Velvet spec_view elides BOTH the impl region AND prove_correct bodies, so several attacks legitimately carry their own tactic bodies (needed because a changed impl leaves different goals). The top-level pageSeq_drop_step lemma is spec-visible and was left untouched in every file.

### Commands
- verify: bash scripts/lean_verify.sh <file> (420s cap used for atk_5/atk_10)
- same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open('<bundle>/Solution.lean').read(), open('<atk>.lean').read(), b.language))"
- resolve: python3 do_resolve.py <label> <patchfile>  (wraps swebench_unified.harness.run_resolve)

**RESOLVE DISCIPLINE:** run STRICTLY one at a time via serial_resolves.sh, since all 7 runs are on the SAME instance and --cache_level env deletes that instance's image on completion (a concurrent second run dies ImageNotFound 404 and would take the gold control with it). Wall times 45.7-51.0s each, 7 runs sequentially.

### VERIFY RESULTS (10 attacks, 6 classes)
  VERIFIES: atk_1_range_mul0 (derived-length/R2, live `_z` read by the counter init), atk_3_echo (ungrounded-oracle echo), atk_5_underdet_loop (R3 determinacy side condition, the named open item), atk_6_branch_emod (control-flow effect via Euclidean Int.emod guard), atk_10_single_loop_cost (sharpest R3 shape)
  REJECTED: atk_2_prepatch (PREPATCH BUG re-encoded -> exit 1, so prepatch_reproduced=true), atk_4_widened_counted (widened counter + live iteration count), atk_7_live_take_len (LIVE derived length at return), atk_8_offdomain (partial-domain/BOUNDARY, blocked by the PageIdx carrier), atk_9_droplast (boundary off-by-one)
  pos_control (identical to the frozen spec file) verifies -> non-vacuity established. It is by construction incapable of demonstrating spec weakness; it is here only as the required non-vacuity control.

### RESOLVE RESULTS (all completed=True, all patch_successfully_applied=True, F2P 1/1 and P2P 20/20 for every row)
  gold 51.0s resolved=True   <-- the load-bearing control: the oracle CAN refute on this instance, so the attack rows carry information
  ctl_frozen 48.4s resolved=True  <-- MY OWN faithful realization of the FROZEN impl (same `_nat_sub` prelude, same Option-shaped read `page_range[k] if 0 <= k < len(...) else None`, same backward fold). Each attack patch is a minimal delta from this, which is what makes the resolve rows attributable to the attacks rather than to my Python style.
  atk_1 46.8s / atk_3 45.7s / atk_5 48.9s / atk_6 48.6s / atk_10 49.8s -- all resolved=True
All 5 patches were git apply --check'd in the base_commit worktree AND smoke-tested locally (each yields [[1,2],[3]] for Paginator([1,2,3],2), matching gold) before submission.

REFINEMENT.MD LEG AUDIT (obligation 3): PASSES. Section A tables 4 numbered legs over the single hunk: A1 (pageRange <-> self.page_range) = R; A2 (backward while <-> the for loop) = I; A2'/A2''/A2''' (Option-shaped read; Nat counter arithmetic; any other arithmetic a verified impl performs) = R; A3 (pageOf <-> Paginator.page) = A-reference; A4 (the fold / yield) = I. Tag histogram: 1 A-reference, 2 I, 1 R (the A2-prime family sharing the R row). NO KIND-3 leg, and section B states this correctly: the operation that genuinely CHANGED (the iteration protocol) is modeled DEEPLY as the spelled-out fold pageSeq over the opaque pageOf, not hidden behind a contract about the function under change. There is no consumed axiom at all, so no A-consumed leg exists to audit.

A-LEG CORRESPONDENCE (independently re-measured by me, not taken from the G-AX record): pageOf <-> Paginator.page(self, number) at django/core/paginator.py:67, UNCHANGED by patch.diff (the gold hunk only ADDS `__iter__` between `__init__` and validate_number; I read the base_commit source to confirm page/validate_number/num_pages/page_range are untouched). I re-ran properties (a) determinism, (b) list(iter(paginator)) == [list(page(n)) for n in page_range], and (c) THE DOMAIN dom(page) == list(page_range) == [1..num_pages] in both directions over 7 boundary configs -- 0 violations. Property (c) is what licenses the PageIdx carrier, and atk_8_offdomain is the executable confirmation that the carrier really refuses numPages+1 rather than merely claiming to. mapping.md's binding of numPages to the num_pages cached_property and page_range to range(1, num_pages+1) matches the real source.

**WHY I DID NOT INHERIT THE RECORDED BROKEN VERDICT:** meta.json records G-EQ=fail from 21:46 (whose own detail says the role did not run: "agent CLI timed out after 14400s"), with retained evidence from an earlier round naming atk_range_mul0 as a verify-but-not-resolve witness. Solution.lean is UNCHANGED since 04:33 (sha256 d68e534c56..., matching every gate's source digest), while mapping.md and refinement.md were rewritten at 21:53 -- i.e. the repair was to the REFINEMENT MAP (rules R0-R4), not to the spec. I therefore re-encoded that recorded counterexample myself (atk_1_range_mul0, in its exact live-`_z` form) and measured its faithful patch under the CURRENT map: it RESOLVES. Under R2 ("realize the length, not the list": (List.range n).length is n by List.length_range, never len(list(range(n)))) plus R1's constant clause (0 * n = 0), the OverflowError the old round measured was a mistranslation, not a spec hole. Same for atk_6 under R0 ((1 : Int) % (-2) is Int.emod = 1, so the guard is the constant False) and atk_10 under R3.

RESIDUAL RISK, stated plainly. The map's rules are extensional laws (R0 closed term -> its value; R1 open term -> a TOTAL Python function equal to the Lean one; R2 composite -> its own defining equation; R3 annotated statement -> its denotation; R4 unread binding -> the identity), and they are backstopped by single-valuedness: the postcondition `out = pageSeq pageRange` pins the RETURN VALUE, so any impl that verifies computes gold's function, and a faithful realization of it therefore resolves.

My attacks probed the two clauses that carry visible side conditions (R3 determinacy via atk_5/atk_4, R4 deadness via atk_7) and could not turn either into a verify-but-not-resolve witness: where the side condition genuinely fails, either the module stops verifying (atk_4, atk_7) or another rule independently forces the constant (atk_5). What remains open is the map's own admitted item 1 -- genuine COST, i.e. a realization computing the right value by a worse algorithm, which is latitude the gold patch has too and which no F2P/P2P outcome distinguishes. That is not verify=/=>correct and I do not report it as a defect.

I also confirmed the two verifier-limit notes are not spec properties: my atk_4/atk_10 first drafts failed on PROOF ENGINEERING (rewrite/omega/rename_i), not on an obligation, and I repaired them until atk_10 verified rather than banking the failure as a rejection.

**VERDICT:** SOUND -- 10 attacks run (>= 5 required) in 6 distinct classes (partial-domain/boundary, control-flow-effect, ungrounded-oracle echo, derived-length composite, loop-schedule/R3, prepatch), 5 verifying, and every verifying attack's materialized faithful patch RESOLVES against a certified-resolving gold control.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** faithfulness-break (is the spec TOO STRONG / does the modeled function disagree with the real callee?). Reference =, confirmed by `git diff HEAD -- django/core/paginator.py` to be base 84322a29ce plus EXACTLY the +4 `__iter__` lines. Base tree used only for the untouched callee `page` (base confirmed to have no `__iter__`: `iter(Paginator([1,2,3],2))` raises TypeError 'Paginator object is not iterable'), so I did NOT score the patch delta itself as a divergence.

**WHAT THE SPEC CLAIMS.** `enumeratePages (pageRange : List PageIdx) ensures out = pageSeq pageRange`, `pageSeq` the front-recursive pointwise map of opaque `pageOf` over the index list; `PageIdx = {n : Nat // 1 <= n <= numPages}` carries the accessor domain. Repo counterpart: `Paginator.__iter__` = `for page_number in self.page_range: yield self.page(page_number)`.

### MY OWN MEASUREMENTS (all in the PATCHED worktree; scratch under mktemp -d):
1. Artifact intact: sha256(Solution.lean)=d68e534c...086668, matching the sources digest under every gate in meta.json. scripts/lean_verify.sh on the frozen file exits 0.
2. Independent 6-leg differential sweep, 8080 configs (size 0..25 x per_page 1..8 x orphans 0..4 x allow_empty, + 6000 randomized to size 60): ZERO failures on every leg -- page_range == [1..num_pages]; num_pages a non-negative int (Nat carrier sound); real `iter` == pointwise map of `page` over page_range; `pageOf` total AND deterministic at every index INSIDE the carrier; generator stops exactly at num_pages (no overrun); EmptyPage at -3/-1/0/num_pages+1/+2/+50 so the carrier is not too NARROW.
3. Core-identity sweep over the WILD parameter space (per_page in {-100,-10,-3,-1,...,10^6,True,False,2.9,-2.9}, orphans in {-1000..1000,True,-2.5}): 6763 checked configs, 0 identity violations.
4. Quantifier leg -- the spec is over EVERY `List PageIdx`, not just page_range. 2481 index lists ([], page_range, reversed, doubled, tripled, all permutations for len<=4, 300 random repeat-lists per config): 0 order- or repeat-dependence violations; `page(n)` is a function of n alone, and fresh-vs-reverse-consumed paginators agree (0 mismatches). The generalization is a SUPERSET of the real input, so it does not over-constrain it.
5. axiom_check.py re-run against the PATCHED tree (meta.json recorded G-AX with apply_gold:false, so the `__iter__` leg had been SKIPPED there): exits 0 and the leg now actually executes.
6. F2P test body reproduced directly against the patched module: page1 -> [1,2], page2 -> [3], PASSES; `runtests.py pagination.tests.PaginationTests.test_paginator_iteration` -> OK.
7. Laziness gap (real `__iter__` is a generator, `out` is a materialized list): partial consumption matched the model prefix in every config; two independent generators are independent; QuerySet-shaped object_list (count()/ordered/`__getitem__`) over 1344 configs -> 0 violations; 100000-page object fine (no Nat/overflow issue).

OVER-STRENGTH CHECK (the direction this gate owns -- does the postcondition reject a CORRECT impl?). I built a natural forward implementation `let result := pageRange.map pageOf; return result` with its induction lemma confined to the elided `prove_correct` body, and confirmed `same_spec(frozen, variant) == True` via swebench_unified.markers with the velvet LanguageTables -- so ONLY the impl/proof regions moved. It verifies exit 0. So the postcondition admits gold-equivalent implementations and is NOT over-tight. My first attempt reported same_spec False; that was my own error (the lemma leaked outside the elided region, since velvet elides only `impl` + the `prove_correct` body), not a spec property -- I corrected it rather than reporting it.
CONTROL: the same-spec WRONG impl `(pageRange.map pageOf).reverse` FAILS to verify (exit 1, 'simp_all made no progress'), so my harness genuinely discriminates and the exit-0 above is not vacuous.

### Candidate divergences found and rejected
(a) negative per_page -- the sharpest hit, and I quantified it independently: 168 configs where measured dom(page) != page_range, ALL of them per_page < 0 with allow_empty_first_page=True, where num_pages goes NEGATIVE (down to -117) which the `Nat` carrier cannot represent, and dom(page) is measured as {1} while the carrier at numPages=0 is empty. Still NOT an observable divergence: page_range == [] in every one of those configs, so the modeled `out = pageSeq [] = []` equals the real iter's []. Measured: 'configs where real iter != pageSeq page_range: 0'. The abstraction is unobservably COARSE here, not wrong. It does slightly overstate axiom_check property (c)'s domain claim -- a documentation nit, not a faithfulness break. per_page=0 raises ZeroDivisionError in num_pages before any iteration.

(b) object_list violating the sequence contract (stateful/raising `__getitem__`, lying count(), float count) breaks `pageOf` well-definedness -- but these are caller-side Paginator API contract violations, not behavior of the modeled function on repo-legitimate inputs; mapping.md 2 fixes the carrier as list/int.

(c) mid-traversal num_pages change: shrinking object_list AND evicting the `count`/`num_pages` cached_property entries from instance `__dict__` makes the live generator raise EmptyPage where the total model promises a value (I reproduced this). It requires reaching into `__dict__` to evict a cached_property, and the pure region explicitly scopes numPages as 'constant for the duration of one traversal' -- declared, not smuggled.

**SCOPE NOTE:** meta.json records G-EQ and G-PANEL-1 as fail in the spec-too-WEAK direction (atk_range_mul0.lean verifies but does not resolve; a cost/schedule hole that mapping.md 2.1 R3/R4 addresses). That is the OPPOSITE axis from this gate and I did not re-judge it or inherit its verdict. On my axis I found no input on which the modeled function disagrees with the real patched callee.

**VERDICT:** FAITHFUL. No diverging input exists on this axis; the spec is neither too strong nor drifted from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** leakage / gold-reconstruction. Judged against problem_statement ONLY; hints_text deliberately excluded from the disclosure baseline (I read it solely to confirm it is NOT the source of anything I credited as public -- its content is triage chatter: 'Reformatted...', 'not sure that's common enough', 'we have a PR with this exact suggestion').

**NO RELAXATION CLAIMED.** There is no RELAXED_LEAKAGE.md in the bundle and meta.json has no `relaxed_leakage` key (verified: sorted(meta.keys()) = axioms, base_commit, changed_files, conf_skip, deep_model_references, gates, instance_id, modeled_functions, pbt_audit, repo, schema_version, spec_provenance, string_modeling; `'relaxed_leakage' in meta` -> False). So this is a plain strict-axis judgement, not an inherited disposition.

### WHAT I MEASURED (my own runs, not the bundle's assertions):

1. **SPEC REGION BYTE-IDENTICAL.** markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('velvet')) = True, and spec_signature equality re-confirmed directly. The two files differ ONLY inside impl/proof. I recomputed markers.spec_view() on BOTH files: impl collapses to '-- implementation elided -- supplied by the consumer' and the prove_correct body to '-- proof elided -- supplied by the consumer'. Critically, the prepatch file's giveaway narration -- impl lines 77-81 ('the object exposes NO iteration protocol...prove_correct MUST fail') and proof lines 103-105 ('Leaves the unsolved discriminating goal [] = pageSeq pageRange') -- is entirely INSIDE the elided spans; I asserted this ('iteration protocol' in prepatch_view -> False, 'Pre-patch' in prepatch_view -> False). The shipped spec view therefore carries none of it.

2. **TOTAL DISCLOSURE OF THE SPEC VIEW.** One method signature plus one postcondition: `method enumeratePages (pageRange : List PageIdx) return (out : List (List Int)) ensures out = pageSeq pageRange`, with pageSeq the front-recursive pointwise map of the OPAQUE pageOf over the index list, and PageIdx = {n : Nat // 1 <= n /\ n <= numPages} carrying the accessor's domain. Semantically that is exactly: 'walk the index sequence in order, produce one sub-view per index through the same accessor, same length, same order.'

3. THE PUBLIC BAR IS MAXIMAL -- IT QUOTES THE GOLD HUNK VERBATIM. problem_statement is titled 'Paginator just implement the `__iter__` function' and contains, as literal code:
  def `__iter__`(self):
      for page_num in self.page_range:
          yield self.page(page_num)
I read patch.diff / instance.json['patch']: the gold edit adds EXACTLY that method (+4 lines in django/core/paginator.py, page_number vs page_num being the only difference) and nothing else. changed_files = ['django/core/paginator.py']. So a solver holding only the public statement already holds the gold edit character-for-character. Nothing in the spec view can be information the patch adds on top of that, which is the whole leakage question, and it settles it in the strongest possible direction.

4. **THE SPEC VIEW IS STRICTLY LESS INFORMATIVE THAN THE PUBLIC TEXT.** It DROPS the class name (Paginator), the method name (`__iter__`), the attribute name (page_range), the callee name (page), the file/module, and the generator/yield mechanism (out is a materialized List, not a lazy protocol). Mechanical confirmation: leakage.screen(Solution.lean, velvet, patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]) -- clean, no warnings at all. Identifier cross-check: `_patch_new_symbols` = {'`__iter__`'}, `_patch_changed_symbols` = {'iter'}; intersection with `_lean_spec_view_identifiers`(spec_view) is EMPTY. Hand-grep of the view for the leak vocabulary and repo tokens ('`__iter__`','yield','page_range','Paginator','num_pages','self.page','object_list','per_page','orphans','validate_number','EmptyPage','fix','bug','patch','regression','previously','generator') produced exactly two benign hits: 'yields' at line 31 used in its ordinary mathematical sense about a partial map, and the substring 'Page' only inside the de-identified names PageIdx/pageOf/pageSeq/numPages/pageRange. No fix narration, no before/after framing, no test-name echo.

5. THE 1-BASED DOMAIN IS PRE-EXISTING, NOT GOLD-DERIVED. I read django/core/paginator.py at base_commit 84322a29ce (git show from the upstream repository): page_range = range(1, num_pages + 1), num_pages, and page()/validate_number() ('Validate the given 1-based page number') all exist UNPATCHED. The gold hunk touches none of them. So PageIdx's `1 <= n <= numPages` carrier is read off unchanged pre-patch code -- and is additionally named outright in the public statement via self.page_range/self.page(page_num). meta.json's own deep_model_references agrees the modeled pageOf is the 'unchanged accessor'.

6. THE DISCRIMINATOR IS LOAD-BEARING (strip-the-narration control, run live). scripts/lean_verify.sh on the frozen Solution.lean exits 0. scripts/lean_verify.sh on Solution_prepatch.lean FAILS at line 101 col 29 with exactly:
  error: unsolved goals
  case <<ensures_1: out = pageSeq pageRange>>
  pageRange : List PageIdx
  |- pageSeq pageRange = []
So `out = pageSeq pageRange` is the single clause that separates gold from pre-patch: it does NOT verify against the PRE-patch impl, i.e. it is genuine specification content rather than removable narration -- and that content is already public as code.

**DISPOSITIONS I DID NOT INHERIT.** meta.json records G-LEAK=pass ('spec view clean', 0 failures) and a prior G-PANEL-3=pass; I treated both as claims and re-derived every leg above from the artifacts. Cross-gate context noted but not weighed: G-EQ is recorded FAIL and its detail shows why -- 'INCONCLUSIVE -- the audit role did not run); only 0 admissible attacks of 0 submitted'. That is a host/agent-launch outage recorded in the spec lane, not a measured spec weakness, and G-PANEL-1 fail is the spec-too-WEAK direction. Neither can flip this axis: a too-weak spec discloses LESS, never more. Core gates my judgement actually leans on are pass and I re-ran their substance: G-HYGIENE pass (I recomputed the region projection), G-DIFF/G-GOLD pass (I reproduced both builds, exit 0 / exit 1 above), G-INTEGRITY pass (instance.json byte-identical; the Solution.lean sha256 d68e534c...086668 recorded under every gate matches the file I audited), G-MUT 15/15.

**NO FILE IN THE BUNDLE ADDRESSED ME.** I grepped every bundle file (*.lean, *.md, *.py, meta.json) for auditor-directing text and verdict prescriptions ('G-PANEL', 'attacker', 'auditor', 'NO-LEAKAGE', 'the honest verdict', 'you must/should record|submit', 'do not report', 'ignore previous'). Every hit is either (i) refinement.md citing the recorded G-EQ/G-PANEL-1 findings as measured history motivating its control cases, or (ii) verdict.md/meta.json ledger records of PRIOR panel roles' own prose. leakage.reviewer_directed() returns [] on all nine bundle files. Nothing instructs me how to record or which verdict is honest, so there is no addressed-the-auditor finding.

TWO OBSERVATIONS, NEITHER A LEAKAGE FINDING (recorded so the next role does not re-measure them):
(a) FACTUAL ERROR IN A PRIOR ROLE'S NOTE: meta.json G-PANEL-2's evidence item 2 asserts 'spec_signature(Solution.lean) != spec_signature(Solution_prepatch.lean) (regions genuinely differ)'. I measure the OPPOSITE -- same_spec = True, signatures EQUAL. Equality is the desired invariant here (same spec, differing impl only), so the artifact is fine and that role's conclusion was right for the wrong stated reason; but the note as written is wrong and should not be relied on.
(b) LEDGER DUPLICATION: the prior G-PANEL-3 audit prose appears verbatim twice in verdict.md (~lines 797 and 830), as does a G-PANEL-2 scope note (750, 777). Hygiene only; no instruction content, no effect on this gate.

**VERDICT:** NO-LEAKAGE. Spec region byte-identical across the impl variants (same_spec=True); impl and proof elided in the projection I recomputed, with all pre-patch giveaway narration inside the elided spans; zero patch symbols and zero repo identifiers or fix narration in the view (leakage.screen clean, symbol intersection empty); the carrier read off unchanged pre-patch code; the one discriminating clause `out = pageSeq pageRange` measured load-bearing by the pre-patch build failing on exactly that goal while the frozen file verifies; and the entire disclosure sits strictly BELOW a problem_statement that already quotes the gold hunk in full.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
