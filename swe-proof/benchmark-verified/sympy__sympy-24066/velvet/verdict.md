# P2 adversarial audit — sympy__sympy-24066

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch.lean`, `atk_2_partial_first.lean`, `atk_3_offbyone.lean`, `atk_4_reversed.lean`, `atk_5_inverted.lean`, `atk_6_drop.lean`, `atk_7_all_dimone.lean`, `atk_8_prefix_only.lean`, `atk_9_nonterm.lean`, `atk_10_false_inv.lean`, `atk_11_donewith_true.lean`, `atk_13_singleton_passthrough.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_echo.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 13 same-spec wrong impls were built and verified; 12 are REJECTED by the frozen spec. The single verifying candidate (atk_12_echo, `return normSeq dims`) is not actually wrong: `normSeq` is a GROUNDED deep model spelled out in the pure region, not an ungrounded oracle, so its faithful refined patch is behaviourally the gold patch. That patch was materialized (patch_atk_12_echo.diff) and RUN through the official harness: RESOLVED=True (F2P test_issue_24062 pass, 30/30 P2P pass). Hence no verifying-but-wrong impl exists: verify => resolve holds on every attack executed.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,17 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (prepatch bug): each operand dimension reported VERBATIM.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
+      invariant result = dims.drop i
       done_with i = 0
       decreasing i
     do
       let d := dims[i - 1]!
-      result := normDim d :: result
+      result := d :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2_partial_first.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,16 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (partial domain): index 0 escapes canonicalization.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
       let d := dims[i - 1]!
-      result := normDim d :: result
+      result := (if i - 1 = 0 then d else normDim d) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3_offbyone.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,15 +66,16 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (boundary): reads dims[i]! instead of dims[i-1]!; the top read is
+    -- out of range and returns the Inhabited default.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
-      let d := dims[i - 1]!
+      let d := dims[i]!
       result := normDim d :: result
       i := i - 1
     return result
```

Attack 4 — `atk_4_reversed.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,16 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (control-flow effect): canonicalization is right, ORDER is reversed.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
       let d := dims[i - 1]!
-      result := normDim d :: result
+      result := result ++ [normDim d]
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5_inverted.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,16 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (inverted oracle): dimensionful operands are canonicalized instead.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
       let d := dims[i - 1]!
-      result := normDim d :: result
+      result := (if isDimensionless d then d else dimOne) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6_drop.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,16 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (length change): dimensionless operands are dropped, not canonicalized.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
       let d := dims[i - 1]!
-      result := normDim d :: result
+      result := (if isDimensionless d then result else d :: result)
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7_all_dimone.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,15 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (over-canonicalization): every operand reported as dimOne.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
-      let d := dims[i - 1]!
-      result := normDim d :: result
+      result := dimOne :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_8_prefix_only.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,16 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (partial domain): only the leading two operands are canonicalized.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
       let d := dims[i - 1]!
-      result := normDim d :: result
+      result := (if i ≤ 2 then normDim d else d) :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 9 — `atk_9_nonterm.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,17 +66,15 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (vacuity probe): the measure never decreases; returns [].
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
       done_with i = 0
       decreasing i
     do
-      let d := dims[i - 1]!
-      result := normDim d :: result
-      i := i - 1
+      result := []
     return result
     -- impl-end
 end
@@ -96,6 +94,4 @@
   rw [hcons, normSeq_cons]
 
 prove_correct normalizeDimensions by
-  loom_solve
-  rw [normSeq_drop_step dims i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> omega
```

Attack 10 — `atk_10_false_inv.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,16 +66,15 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (vacuity probe): invariant False -- if establishment is unchecked the
+    -- postcondition follows vacuously while the impl returns garbage.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
+      invariant False
       done_with i = 0
       decreasing i
     do
-      let d := dims[i - 1]!
-      result := normDim d :: result
       i := i - 1
     return result
     -- impl-end
@@ -96,6 +95,4 @@
   rw [hcons, normSeq_cons]
 
 prove_correct normalizeDimensions by
-  loom_solve
-  rw [normSeq_drop_step dims i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all
```

Attack 11 — `atk_11_donewith_true.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,12 +66,13 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (vacuity probe): done_with True lets the loop exit immediately with a
+    -- partial result; canonicalization of the remaining operands never happens.
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
-      done_with i = 0
+      done_with True
       decreasing i
     do
       let d := dims[i - 1]!
@@ -96,6 +97,4 @@
   rw [hcons, normSeq_cons]
 
 prove_correct normalizeDimensions by
-  loom_solve
-  rw [normSeq_drop_step dims i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> omega
```

Attack 12 — `atk_12_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,18 +66,8 @@
   ensures out = normSeq dims
   do
     -- impl-start
-    let mut result : List Dimension := []
-    let mut i := dims.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ dims.length
-      invariant result = normSeq (dims.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let d := dims[i - 1]!
-      result := normDim d :: result
-      i := i - 1
-    return result
+    -- ECHO: return the postcondition's own function.
+    return normSeq dims
     -- impl-end
 end
 
@@ -97,5 +87,3 @@
 
 prove_correct normalizeDimensions by
   loom_solve
-  rw [normSeq_drop_step dims i (by omega) (by omega)]
-  simp_all
```

Attack 13 — `atk_13_singleton_passthrough.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,6 +66,11 @@
   ensures out = normSeq dims
   do
     -- impl-start
+    -- WRONG (partial domain aimed at the F2P shape `exp(x)`, arity 1): a one-operand
+    -- call passes its dimension through VERBATIM (the prepatch bug); longer lists
+    -- canonicalize correctly.
+    if dims.length = 1 then
+      return dims
     let mut result : List Dimension := []
     let mut i := dims.length
     while i > 0
@@ -97,5 +102,7 @@
 
 prove_correct normalizeDimensions by
   loom_solve
-  rw [normSeq_drop_step dims i (by omega) (by omega)]
-  simp_all
+  all_goals try (rw [normSeq_drop_step _ _ (by omega) (by omega)]; simp_all)
+  all_goals try simp_all
+  all_goals try grind
+  all_goals try omega
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree at base_commit 514579c655 in ./wt). All 13 attacks + pc.lean confirmed byte-identical spec via swebench_unified.markers.same_spec => ALL_SAME_SPEC=True (axioms/pure/pre/post untouched; only the impl region, and where noted the elided prove_correct body, were edited).

**POSITIVE CONTROL:** pc.lean (shipped Solution.lean impl) -> `bash scripts/lean_verify.sh <f>` -> EXIT 0 (VERIFIES).

### ATTACKS (cmd for each: `bash scripts/lean_verify.sh <f>.lean`; run 4-way concurrently as background jobs):
1. atk_1_prepatch (PREPATCH BUG re-encoded: operand dimension passed through verbatim, `result := d :: result`) -> EXIT 1 REJECTED. Residual goal `dims[i-1]! :: result = List.drop (i-1) dims` unprovable. prepatch_reproduced=true.
2. atk_2_partial_first (PARTIAL DOMAIN: index 0 escapes canonicalization) -> EXIT 1 REJECTED.
3. atk_3_offbyone (BOUNDARY: reads dims[i]! not dims[i-1]!, top read hits the Inhabited default) -> EXIT 1 REJECTED.
4. atk_4_reversed (CONTROL-FLOW EFFECT: correct per-element rule, order destroyed via `result ++ [normDim d]`) -> EXIT 1 REJECTED.
5. atk_5_inverted (INVERTED oracle: dimensionFUL operands canonicalized instead) -> EXIT 1 REJECTED.
6. atk_6_drop (LENGTH CHANGE: dimensionless operands dropped, not canonicalized) -> EXIT 1 REJECTED.
7. atk_7_all_dimone (OVER-CANONICALIZATION: every operand reported dimOne) -> EXIT 1 REJECTED.
8. atk_8_prefix_only (PARTIAL DOMAIN by position: only leading two operands canonicalized) -> EXIT 1 REJECTED.
9. atk_9_nonterm (VACUITY: `decreasing i` fraud, body never decreases i, returns []) -> EXIT 1 REJECTED, omega refuses the measure. Total-correctness VC is live.
10. atk_10_false_inv (VACUITY: `invariant False` — tests whether invariant ESTABLISHMENT is checked) -> EXIT 1 REJECTED. Establishment is checked, so the classic vacuous-guard escape is closed.
11. atk_11_donewith_true (VACUITY: `done_with True` to exit early with a partial result) -> EXIT 1 REJECTED.
12. atk_12_echo (UNGROUNDED-ORACLE ECHO: `return normSeq dims`, proof `loom_solve`) -> EXIT 0 **VERIFIES**. Mandatory resolve run performed, see below.
13. atk_13_singleton_passthrough (PARTIAL DOMAIN aimed exactly at the F2P shape `exp(x)`, arity 1: a one-operand call passes its dimension through verbatim = the prepatch bug restricted to the failing test's arity; longer lists canonicalize) -> EXIT 1 REJECTED. Given an honest best-effort proof (loom_solve + normSeq_drop_step + simp_all/grind/omega sweep) the sole residual goal is `dims = normSeq dims` under `dims.length = 1`, which is genuinely false. This is the sharpest attack in the battery and the spec catches it.

Note on attacks 2-13: because `prove_correct` bodies are ELIDED from the spec view, a fair attacker may rewrite the proof script too; attacks 9-13 do exactly that (custom invariants/done_with/decreasing + adapted tactic scripts) so the rejections are the SPEC rejecting the impl, not my tactic script failing.

### MANDATORY RESOLVE RUN (the only verifying candidate):
- Materialized faithful refined patch of atk_12_echo per refinement.md's map: normDim -> `_norm_dim` (A3 conditional select over the REAL callees `self.get_dimension_system().is_dimensionless` / `Dimension(1)`), normSeq -> `_norm_seq` (A2 front-recursive map, transliterated verbatim including the recursion), dims -> `[d[1] for d in fds]` (A1), out -> spliced into the return tuple (A4).
- Path: patch_atk_12_echo.diff
- Applies at base_commit: `cd wt && git apply --check patch_atk_12_echo.diff` -> OK (checked twice, final FINAL_GIT_APPLY_CHECK=OK on a clean worktree).
- Official harness: `run_resolve('sympy__sympy-24066', patch, timeout=1800)` -> **RESOLVED=True**, completed=True, error=None; FAIL_TO_PASS {'success': ['test_issue_24062'], 'failure': []}, PASS_TO_PASS 30/30 success, no PASS_TO_FAIL.
- Interpretation: the echo does NOT break the spec. `normSeq`/`normDim` are a grounded deep model in the pure region (an A-REFERENCE validated == the real callee by G-AX), not a spec oracle constant. Echoing them therefore reproduces gold behaviour rather than smuggling in unimplementable magic — exactly the property that makes an A-reference legitimate instead of a kind-3 leg.

A-LEG AUDIT (refinement.md / mapping.md), independently re-executed against the real repo at base_commit (PYTHONPATH with a borrowed mpmath, from ./wt):
- A2 A-reference (normSeq == the real post-patch comprehension): front-recursive normSeq vs `[Dimension(1) if is_dimensionless(d) else d for d in dims]` over 2000 randomized real Dimension lists (seed 24066, pool spanning dimensionful / canonical-dimensionless / NON-canonical-dimensionless) -> 0 mismatches. Correspondence holds; the element-independence + order-preservation argument in mapping.md §3.1 is sound.
- A3 A-consumed (isDimensionless / dimOne): `is_dimensionless` is total and bool-valued on the whole pool; `is_dimensionless(Dimension(1)) == True`. LOAD-BEARING WITNESS reproduced: `dim_of(second/(ohm*farad))` = Dimension(time/(`capacitance*impedance`)) is dimensionless (True) yet != Dimension(1) — so normDim is non-vacuous and the opaque axioms are used only as 'the same total predicate / same canonical value per element', never equationally. Correct that this is NOT `d = dimOne`.
- Leg kinds: A1 R, A2 A-reference + I, A3 A-consumed + I, A4 R. Every leg is R / A-consumed / A-reference / I — NO kind-3 (inexpressible-changed-op) step. The one genuinely changed operation (per-element dimensionless canonicalization) is modeled DEEPLY in the pure region, not hidden behind an axiom about the function under change; the two consumed axioms cover an UNCHANGED predicate (dimensions.py:447) and an UNCHANGED constant (Dimension(1)), which I confirmed byte-unchanged by the patch.
- Model<->patch correspondence: patch.diff is byte-identical to instance.json['patch'] (verbatim gold, PATCH_DIFF_VERBATIM_GOLD=YES). The gold hunk's only behavioural change is the new `dims` line; the recursion `fds = [...]` and factor reconstruction `expr.func(*(f[0] for f in fds))` are unchanged and correctly excluded from the carrier as identity-under-refinement (mapping.md §2). refinement.md's claims match the source I read at sympy/physics/units/unitsystem.py:192-196.

**CONCLUSION:** 13 distinct wrong impls exercised across partial-domain, boundary, control-flow-effect, inverted-oracle, length-changing, three vacuity classes (non-termination, False invariant, done_with fraud), and the ungrounded-oracle echo. 12 rejected. The 1 that verifies had its faithful refined patch materialized and RUN through the official harness, and it RESOLVED — so it is not a verify-but-not-correct witness. No verify=>resolve counterexample found; the A legs' correspondence to the real callees holds executably. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch.lean`, `atk_2_partial_first.lean`, `atk_3_offbyone.lean`, `atk_4_reversed.lean`, `atk_5_inverted.lean`, `atk_6_drop.lean`, `atk_7_all_dimone.lean`, `atk_8_prefix_only.lean`, `atk_9_nonterm.lean`, `atk_10_false_inv.lean`, `atk_11_donewith_true.lean`, `atk_13_singleton_passthrough.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_12_echo.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 13 same-spec wrong impls were built and verified; 12 are REJECTED by the frozen spec. The single verifying candidate (atk_12_echo, `return normSeq dims`) is not actually wrong: `normSeq` is a GROUNDED deep model spelled out in the pure region, not an ungrounded oracle, so its faithful refined patch is behaviourally the gold patch. That patch was materialized (patch_atk_12_echo.diff) and RUN through the official harness: RESOLVED=True (F2P test_issue_24062 pass, 30/30 P2P pass). Hence no verifying-but-wrong impl exists: verify => resolve holds on every attack executed.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_first.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_reversed.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_inverted.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_drop.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_all_dimone.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_prefix_only.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_nonterm.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_false_inv.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_donewith_true.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_singleton_passthrough.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCRATCH:**  (worktree at base_commit 514579c655 in ./wt). All 13 attacks + pc.lean confirmed byte-identical spec via swebench_unified.markers.same_spec => ALL_SAME_SPEC=True (axioms/pure/pre/post untouched; only the impl region, and where noted the elided prove_correct body, were edited).

**POSITIVE CONTROL:** pc.lean (shipped Solution.lean impl) -> `bash scripts/lean_verify.sh <f>` -> EXIT 0 (VERIFIES).

### ATTACKS (cmd for each: `bash scripts/lean_verify.sh <f>.lean`; run 4-way concurrently as background jobs):
1. atk_1_prepatch (PREPATCH BUG re-encoded: operand dimension passed through verbatim, `result := d :: result`) -> EXIT 1 REJECTED. Residual goal `dims[i-1]! :: result = List.drop (i-1) dims` unprovable. prepatch_reproduced=true.
2. atk_2_partial_first (PARTIAL DOMAIN: index 0 escapes canonicalization) -> EXIT 1 REJECTED.
3. atk_3_offbyone (BOUNDARY: reads dims[i]! not dims[i-1]!, top read hits the Inhabited default) -> EXIT 1 REJECTED.
4. atk_4_reversed (CONTROL-FLOW EFFECT: correct per-element rule, order destroyed via `result ++ [normDim d]`) -> EXIT 1 REJECTED.
5. atk_5_inverted (INVERTED oracle: dimensionFUL operands canonicalized instead) -> EXIT 1 REJECTED.
6. atk_6_drop (LENGTH CHANGE: dimensionless operands dropped, not canonicalized) -> EXIT 1 REJECTED.
7. atk_7_all_dimone (OVER-CANONICALIZATION: every operand reported dimOne) -> EXIT 1 REJECTED.
8. atk_8_prefix_only (PARTIAL DOMAIN by position: only leading two operands canonicalized) -> EXIT 1 REJECTED.
9. atk_9_nonterm (VACUITY: `decreasing i` fraud, body never decreases i, returns []) -> EXIT 1 REJECTED, omega refuses the measure. Total-correctness VC is live.
10. atk_10_false_inv (VACUITY: `invariant False` — tests whether invariant ESTABLISHMENT is checked) -> EXIT 1 REJECTED. Establishment is checked, so the classic vacuous-guard escape is closed.
11. atk_11_donewith_true (VACUITY: `done_with True` to exit early with a partial result) -> EXIT 1 REJECTED.
12. atk_12_echo (UNGROUNDED-ORACLE ECHO: `return normSeq dims`, proof `loom_solve`) -> EXIT 0 **VERIFIES**. Mandatory resolve run performed, see below.
13. atk_13_singleton_passthrough (PARTIAL DOMAIN aimed exactly at the F2P shape `exp(x)`, arity 1: a one-operand call passes its dimension through verbatim = the prepatch bug restricted to the failing test's arity; longer lists canonicalize) -> EXIT 1 REJECTED. Given an honest best-effort proof (loom_solve + normSeq_drop_step + simp_all/grind/omega sweep) the sole residual goal is `dims = normSeq dims` under `dims.length = 1`, which is genuinely false. This is the sharpest attack in the battery and the spec catches it.

Note on attacks 2-13: because `prove_correct` bodies are ELIDED from the spec view, a fair attacker may rewrite the proof script too; attacks 9-13 do exactly that (custom invariants/done_with/decreasing + adapted tactic scripts) so the rejections are the SPEC rejecting the impl, not my tactic script failing.

### MANDATORY RESOLVE RUN (the only verifying candidate):
- Materialized faithful refined patch of atk_12_echo per refinement.md's map: normDim -> `_norm_dim` (A3 conditional select over the REAL callees `self.get_dimension_system().is_dimensionless` / `Dimension(1)`), normSeq -> `_norm_seq` (A2 front-recursive map, transliterated verbatim including the recursion), dims -> `[d[1] for d in fds]` (A1), out -> spliced into the return tuple (A4).
- Path: patch_atk_12_echo.diff
- Applies at base_commit: `cd wt && git apply --check patch_atk_12_echo.diff` -> OK (checked twice, final FINAL_GIT_APPLY_CHECK=OK on a clean worktree).
- Official harness: `run_resolve('sympy__sympy-24066', patch, timeout=1800)` -> **RESOLVED=True**, completed=True, error=None; FAIL_TO_PASS {'success': ['test_issue_24062'], 'failure': []}, PASS_TO_PASS 30/30 success, no PASS_TO_FAIL.
- Interpretation: the echo does NOT break the spec. `normSeq`/`normDim` are a grounded deep model in the pure region (an A-REFERENCE validated == the real callee by G-AX), not a spec oracle constant. Echoing them therefore reproduces gold behaviour rather than smuggling in unimplementable magic — exactly the property that makes an A-reference legitimate instead of a kind-3 leg.

A-LEG AUDIT (refinement.md / mapping.md), independently re-executed against the real repo at base_commit (PYTHONPATH with a borrowed mpmath, from ./wt):
- A2 A-reference (normSeq == the real post-patch comprehension): front-recursive normSeq vs `[Dimension(1) if is_dimensionless(d) else d for d in dims]` over 2000 randomized real Dimension lists (seed 24066, pool spanning dimensionful / canonical-dimensionless / NON-canonical-dimensionless) -> 0 mismatches. Correspondence holds; the element-independence + order-preservation argument in mapping.md §3.1 is sound.
- A3 A-consumed (isDimensionless / dimOne): `is_dimensionless` is total and bool-valued on the whole pool; `is_dimensionless(Dimension(1)) == True`. LOAD-BEARING WITNESS reproduced: `dim_of(second/(ohm*farad))` = Dimension(time/(`capacitance*impedance`)) is dimensionless (True) yet != Dimension(1) — so normDim is non-vacuous and the opaque axioms are used only as 'the same total predicate / same canonical value per element', never equationally. Correct that this is NOT `d = dimOne`.
- Leg kinds: A1 R, A2 A-reference + I, A3 A-consumed + I, A4 R. Every leg is R / A-consumed / A-reference / I — NO kind-3 (inexpressible-changed-op) step. The one genuinely changed operation (per-element dimensionless canonicalization) is modeled DEEPLY in the pure region, not hidden behind an axiom about the function under change; the two consumed axioms cover an UNCHANGED predicate (dimensions.py:447) and an UNCHANGED constant (Dimension(1)), which I confirmed byte-unchanged by the patch.
- Model<->patch correspondence: patch.diff is byte-identical to instance.json['patch'] (verbatim gold, PATCH_DIFF_VERBATIM_GOLD=YES). The gold hunk's only behavioural change is the new `dims` line; the recursion `fds = [...]` and factor reconstruction `expr.func(*(f[0] for f in fds))` are unchanged and correctly excluded from the carrier as identity-under-refinement (mapping.md §2). refinement.md's claims match the source I read at sympy/physics/units/unitsystem.py:192-196.

**CONCLUSION:** 13 distinct wrong impls exercised across partial-domain, boundary, control-flow-effect, inverted-oracle, length-changing, three vacuity classes (non-termination, False invariant, done_with fraud), and the ungrounded-oracle echo. 12 rejected. The 1 that verifies had its faithful refined patch materialized and RUN through the official harness, and it RESOLVED — so it is not a verify-but-not-correct witness. No verify=>resolve counterexample found; the A legs' correspondence to the real callees holds executably. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Independent re-derivation (did not rely on the recorded panel_1/2 verdicts).

**SETUP.** Fresh worktrees from the upstream repository at base_commit 514579c655bf: /base (clean) and /wt (patch.diff applied, applies clean). Patched branch confirmed byte-exact at unitsystem.py:192-195.

1) **SPEC REGION IDENTITY.** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True. Printed the spec view: axioms (Dimension/dimOne/isDimensionless), pure region (normDim, normSeq, normSeq_nil/cons), empty pre/post, the method signature `ensures out = normSeq dims`, and normSeq_drop_step all pass through; only impl + prove_correct body are elided. No contract drift between candidate and prepatch.

2) VALUE-LEVEL DIFFERENTIAL, model vs REAL patched callee. Built a 50-element pool of genuine Dimension objects from real unit expressions (base+derived SI dims, canonical Dimension(1), the non-canonical dimensionless witness Dimension(time/(`capacitance*impedance`)) from second/(`ohm*farad`) and its reciprocal, meter/meter, ratio-cancelling products, numeric dims, plus structural exotica sqrt/cube-root/Add/Mul/zero-power dimensions). 47 defined, 3 raising. On the defined domain: 20000 randomized lists (len 0-6, seed 24066) comparing normSeq (deep model) against the verbatim real post-patch comprehension -> 0 divergences. Order and length preserved on every case (asserted, not eyeballed). normDim(non-canonical dimensionless) = Dimension(1); normDim(time) = Dimension(time,T) — matches the real per-element rule exactly. dimOne consistency: Dimension(1) is a stable singleton (== and hash agree across constructions) and is_dimensionless(Dimension(1)) is True; no dimension equals Dimension(1) while testing non-dimensionless.

3) END-TO-END THROUGH THE REAL BRANCH (not just the isolated line). 3000 multi-argument applied Functions f2(*args), arity 1-4, over real unit expressions; compared the REAL patched return tuple's dimension tail `list(real[1:])` against normSeq applied to the arg-dimension list from the UNCHANGED recursion -> 0 divergences, 0 arity mismatches. So the R-refinement in mapping.md §2 (dimension list <-> tuple tail, by position; factor term omitted as unchanged identity) holds on real inputs, and dropping the leading expr.func(*factors) term is a genuine identity under refinement, not concealed spec weakness. F2P witness reproduces: SI.`_collect_factor_and_dimension`(1+exp(T/(`R*C`))) == (1+E, Dimension(1)).

4) SPEC NOT TOO STRONG / NOT TOO WEAK. The postcondition `out = normSeq dims` pins output to exactly the changed operation (per-element dimensionless canonicalization) and nothing more — no extra conjunct constrains the unchanged recursion or factor reconstruction. Discrimination confirmed: Solution.lean verifies (lean_verify.sh EXIT=0); Solution_prepatch.lean FAILS (EXIT=1) with unsolved goal `dims[i-1]?.getD default = normDim (dims[i-1]?.getD default)` — precisely the clause that is false exactly when an operand is dimensionless yet not canonical, i.e. the real bug. The spec neither admits the prepatch behavior nor over-constrains beyond the patch.

5) BUNDLE CHECKS re-run against my own patched worktree: axiom_check.py exit 0 (G-AX OK, 10 boundary + ~3000 fuzz); conformance_check.py exit 0 (3174 inputs, seed 24066, 0 disagreements).

ONE DOCUMENTATION OVERCLAIM (minor, does not change the verdict, worth recording). mapping.md §3.2 and axiom_check.py assert `is_dimensionless` is "total Dimension -> bool" / total "on every fuzzed dimension". It is not total: it raises TypeError on Function-valued dimension names — Dimension(exp(length)), Dimension(sin(length)), Dimension(log(length)) — via `_get_dimensional_dependencies_for_name`'s is_Function arm (dimensions.py:400-416). axiom_check.py's pool is curated from real unit expressions and never constructs such a dimension, so the totality assertion passes vacuously with respect to that class.

Why this is not a faithfulness break: (a) it is a definedness gap, never a value disagreement — 0 divergences everywhere the real callee returns; (b) the gap is introduced by the gold patch itself (pre-patch that branch never called is_dimensionless), so reporting it as drift would condemn the correct spec for the patch delta; (c) it is unreachable by natural sympy usage (0/4000 randomly nested real unit expressions produced a TypeError; only ValueError from the unchanged Add-branch dimension check, which is out of the modeled carrier); (d) modeling a partial callee as total is the standard convention here and the proof consumes isDimensionless only as "the same predicate decides each element", never any equational fact, so no wrong implementation is admitted. Suggested (non-blocking) tightening: reword §3.2 to "total on the dimensions reachable through the applied-Function branch" and have axiom_check.py document the Function-name-dimension exclusion rather than assert unqualified totality.

**CONCLUSION:** the modeled function agrees with the real patched callee on every input in the carrier where the real callee is defined, including the load-bearing non-canonical dimensionless witness; the spec is byte-identical to the prepatch spec region, discriminates the gold delta, and is neither too strong nor too weak. FAITHFUL.

Counterexample / evidence:

```
None — no value-level diverging input found. The one input class where model and real repo differ in *definedness* rather than value is the patch's own delta (see notes): dims = [Dimension(exp(Symbol('length')))]. Under the PATCHED reference (the correct reference per this gate) the real branch raises TypeError('The input arguments for the function ... must be dimensionless.'); the Lean model, whose `isDimensionless : Dimension -> Bool` is total, returns normSeq dims. This is NOT reported as the defect: pre-patch that same input returns Dimension(exp(length)) verbatim (the branch never called is_dimensionless), so the TypeError is introduced BY the gold patch. Flagging it would be condemning the patch delta itself. It is also unreachable by natural usage (0 TypeErrors in 4000 randomly nested real unit expressions to depth 3; it requires hand-installing a Function-valued dimension via SI.set_quantity_dimension).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE / gold-reconstruction audit of velvet bundle sympy__sympy-24066 (attacker 3). Verdict NO-LEAKAGE.

SCOPE / RELAXATION STATUS: No documented relaxation is claimed by this bundle -- `meta.json` has NO `relaxed_leakage` key (checked: `'relaxed_leakage' in json.dumps(meta)` == False; gates['G-LEAK'].status == 'pass', not 'relaxed') and there is no RELAXED_LEAKAGE.md anywhere in the bundle or at repo root. So this is a STANDARD leakage judgement -- I did not inherit any disposition, and the strict test applies: nothing in the spec view may reveal the gold edit beyond the public problem_statement.

1) SPEC-REGION BYTE-IDENTITY (measured, not asserted): `backends.get_backend('velvet')`, then `markers.same_spec(Solution.lean, Solution_prepatch.lean, b.language)` == True. This matters for leakage specifically: `diff` of the two files shows the ONLY differences are (a) 5 lines of narration "Pre-image skeleton: each operand's dimension is reported VERBATIM, with no canonicalization... prove_correct MUST fail" and (b) `result := d :: result` vs `result := normDim d :: result`. Both sit strictly BETWEEN `-- impl-start`/`-- impl-end`, i.e. inside the elided impl region, and same_spec==True proves they contribute nothing to the consumer spec view. That prepatch narration WOULD have been a hard leak (it spells out the pre-image behaviour and that the fix is canonicalization); it is correctly quarantined in the elided region.

2) **SPEC VIEW I ACTUALLY READ:** I rendered `markers.spec_view(Solution.lean, velvet.language)` and read it in full. It exposes: axioms Dimension/dimOne/isDimensionless; pure defs normDim (`if isDimensionless d then dimOne else d`), normSeq (front-recursive map) + two rfl lemmas; empty pre/post regions; the method signature `normalizeDimensions (dims : List Dimension) return (out : List Dimension) ensures out = normSeq dims`; the normSeq_drop_step helper. impl and prove_correct bodies are elided (`-- implementation elided`, `-- proof elided`).

3) DISCRIMINATOR IS PROBLEM_STATEMENT-DERIVABLE -- the core of this verdict. The load-bearing content of the spec view is the rule "a dimensionless dimension is reported as the single canonical dimensionless value; any other dimension is kept as-is." Every concept in that rule appears VERBATIM in the public problem_statement (I grepped each token against instance.json's problem_statement; all present): `is_dimensionless` (in `assert SI.get_dimension_system().is_dimensionless(dim)`), `Dimension(1)`, `_collect_factor_and_dimension`, `exp(`, `dimensionless`, and even the exact non-canonical witness `Dimension(time/(capacitance*impedance))`. The problem_statement's closing error line -- 'is Dimension(time/(`capacitance*impedance`)), but it should be Dimension(1)' -- combined with its own assertion that `is_dimensionless(dim)` is True, states the discriminator directly: a dimension that IS dimensionless but is NOT the canonical value must be reported as Dimension(1). normDim is that sentence transcribed. Nothing is added. In particular the spec view names no repo identifier, no diff, no `fds`, no comprehension, no `Function` branch, no test name (`test_issue_24062`), no `exp`/`ohm`/`farad`/`second`, and no pre-patch behaviour -- I grepped the rendered view for each of ['24062','exp(','ohm','farad','second','fds','Function','unitsystem','collect_factor','capacitance','impedance','sympy','patch','issue','bug','fix'] and the ONLY hit across all of them was the incidental arithmetic `have hsucc : i - 1 + 1 = i := by omega` matching the substring '1 +'. The axiom comment 'CRUCIALLY this is NOT the same as `d = dimOne`: a dimension can be dimensionless yet not be the canonical value' is exactly the problem_statement's own assert-plus-error-message pair, not new information.

4) LOAD-BEARING TEST (the strip-the-narration control, run because the discriminator IS named in the spec): I copied both files to a mktemp dir and ran scripts/lean_verify.sh myself. Gold `Solution.lean` -> exit 0 (verifies). `Solution_prepatch.lean` (identical spec, verbatim-passthrough impl) -> exit 1, failing precisely at line 103 with `unsolved goals ... invariant_2 : result = normSeq (List.drop i dims) |- dims[i-1]?.getD default = normDim (dims[i-1]?.getD default)`. So the named clause is genuinely load-bearing rather than decorative: the spec does NOT verify against the pre-patch implementation, and the exact residual goal is the dimensionless-but-non-canonical discriminator. A spec that omitted `normDim` from `ensures` would admit the buggy passthrough.

5) MECHANICAL SCREEN, re-run rather than trusted: `leakage.screen(Solution.lean src, velvet.language, row['patch'], row['problem_statement'], test_patch=row['test_patch'])` -> passed=True, hard_failures=[], warnings=[]. Matches the stamped G-LEAK 'spec view clean'. Note per my own prior finding that this screen trips on vocabulary like 'fixed'/'copy' -- the spec view contains no such prose, so the pass is not a near-miss.

6) SUPPORTING GATES (leaned on only for consistency, all pass): G-VERIFY pass 25.1s, G-GOLD pass (gold verifies, prepatch fails), G-DIFF pass, G-AX pass (normSeq == real comprehension on 10 boundary + ~3000 fuzz; load-bearing non-canonical witness confirmed), G-CONF pass (3174 inputs, seed 24066, 0 disagreements), G-MUT 14/14, G-HYGIENE pass, G-INTEGRITY pass (instance.json byte-identical). My two verifier runs independently reproduce the G-GOLD/G-DIFF pair, so the disposition rests on my measurement.

7) **CONSUMER-VISIBLE SURFACE:** mapping.md and refinement.md DO quote the gold hunk verbatim (refinement.md §A reproduces the +/- diff), but they are audit-side artifacts and are never shipped to the solver: eval/dataset.py as_dict()/prompts.py build the agent view from problem_statement + spec_view + modeled_functions + changed_files only, with WITHHELD_FIELDS = (patch, test_patch, FAIL_TO_PASS, PASS_TO_PASS); neither adapter.py, prompts.py nor dataset.py references mapping.md or refinement.md. The consumer-visible `modeled_functions` entry (repo_symbol '...`_collect_factor_and_dimension` (applied-Function branch)', repo_location unitsystem.py:192) is the deliberate mode-1/2 edit-localization aid, and problem_statement already names `_collect_factor_and_dimension`; it conveys where to edit, not what the edit is.

8) **NO REVIEWER-DIRECTED CONTENT:** I grepped Solution.lean, Solution_prepatch.lean, mapping.md and refinement.md for panel/reviewer/attacker/submit/NO-LEAKAGE/'honest verdict'/'record this' -- zero hits. No file in this bundle addresses me or tells me what to record. The only occurrences of the string 'NO-LEAKAGE' in the bundle are the prior run's own stamped record (verdict.md:1730, meta.json:212 agent_verdict), which are ledger entries about a past review, not instructions to this one; I did not treat them as a disposition and reached this verdict from the measurements above.

**CONCLUSION:** the spec view is a faithful, minimal statement of the required post-condition whose every load-bearing element is explicitly derivable from the public problem_statement (which itself names is_dimensionless, Dimension(1), and the non-canonical witness). No line reveals the gold edit, the pre-patch behaviour, the diff, or the F2P test. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.