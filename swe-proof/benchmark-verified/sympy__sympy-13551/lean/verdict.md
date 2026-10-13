# P2 adversarial audit — sympy__sympy-13551

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,14 +47,14 @@
   let mut acc : ℚ := 1
   for k in [0:n] do
     acc := acc * (c + r k)
-  return acc / q
+  if q = 0 then return 42 else return acc / q
 -- impl-end
 
 -- proof-start
 theorem correct_finiteProduct :
     ∀ (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ), q ≠ 0 → (∀ k, k < n → c + r k ≠ 0) →
       problem_spec_finiteProduct c n r q (implementation_finiteProduct c n r q) := by
-  intro c n r q _ _
+  intro c n r q hq _
   unfold problem_spec_finiteProduct implementation_finiteProduct
-  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map]
+  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map, if_neg hq]
 -- proof-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,14 +47,18 @@
   let mut acc : ℚ := 1
   for k in [0:n] do
     acc := acc * (c + r k)
-  return acc / q
+  if 0 < n ∧ c + r 0 = 0 then return 999 else return acc / q
 -- impl-end
 
 -- proof-start
 theorem correct_finiteProduct :
     ∀ (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ), q ≠ 0 → (∀ k, k < n → c + r k ≠ 0) →
       problem_spec_finiteProduct c n r q (implementation_finiteProduct c n r q) := by
-  intro c n r q _ _
+  intro c n r q _ hnz
   unfold problem_spec_finiteProduct implementation_finiteProduct
+  have hguard : ¬ (0 < n ∧ c + r 0 = 0) := by
+    rintro ⟨hn, h0⟩
+    exact hnz 0 hn h0
+  simp only [if_neg hguard]
   simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,10 +44,10 @@
 
 -- impl-start
 def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do
-  let mut acc : ℚ := 1
+  let mut accRem : ℚ := 1
   for k in [0:n] do
-    acc := acc * (c + r k)
-  return acc / q
+    accRem := accRem * r k
+  return (c ^ n + accRem) / q
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
   let mut acc : ℚ := 1
   for k in [0:n] do
     acc := acc * (c + r k)
-  return acc / q
+  if n = 0 then return 0 else return acc / q
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
 -- impl-start
 def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do
   let mut acc : ℚ := 1
-  for k in [0:n] do
+  for k in [0:n-1] do
     acc := acc * (c + r k)
   return acc / q
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,9 +44,9 @@
 
 -- impl-start
 def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do
-  let mut acc : ℚ := 1
+  let mut acc : ℚ := 0
   for k in [0:n] do
-    acc := acc * (c + r k)
+    acc := acc + (c + r k)
   return acc / q
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,14 +47,14 @@
   let mut acc : ℚ := 1
   for k in [0:n] do
     acc := acc * (c + r k)
-  return acc / q
+  return if q = 0 then 0 else acc / q
 -- impl-end
 
 -- proof-start
 theorem correct_finiteProduct :
     ∀ (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ), q ≠ 0 → (∀ k, k < n → c + r k ≠ 0) →
       problem_spec_finiteProduct c n r q (implementation_finiteProduct c n r q) := by
-  intro c n r q _ _
+  intro c n r q hq _
   unfold problem_spec_finiteProduct implementation_finiteProduct
-  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map]
+  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map, if_neg hq]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The value of a finite product of a separable additive term over a range of
integer positions, divided by a constant.

The term multiplied across the range has the shape `c + r(k)`, where `c` is a
constant (independent of the position) and `r(k)` is the position-dependent
remainder, evaluated at every position `k` of the range `0, 1, …, n-1`. The whole
product is then divided by a constant `q` — the value that the range-product of
the term's denominator collapses to, which is a plain number.

The value of the construct is the genuine product over the range: multiply the
term `c + r(k)` across every position `k < n`, then divide by `q`. No component of
the result is left free — it is fully determined by `c`, the length `n`, the
remainder function `r`, and the divisor `q`.

The modeled slice is the non-degenerate case: the divisor `q` is nonzero and
every factor `c + r(k)` over the range is nonzero (a zero factor makes the real
construct's evaluation degenerate rather than a plain number, and lies outside
the modeled slice).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the range-product is modelled
-- directly as the product of the per-position term values, so no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The value equals the genuine product of the term `c + r k` taken over every
position `k < n` of the range, divided by the constant `q`. The product of the
additive term is its true product across the range — not any summand-wise
shortcut — so the result is pinned to `c`, the length `n`, the remainder function
`r`, and the divisor `q`. -/
def problem_spec_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) (result : ℚ) : Prop :=
  result = ((List.range n).map (fun k => c + r k)).prod / q
-- post-conditions-end

-- impl-start
def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do
  let mut acc : ℚ := 1
  for k in [0:n] do
    acc := acc * (c + r k)
  return acc / q
-- impl-end

-- proof-start
theorem correct_finiteProduct :
    ∀ (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ), q ≠ 0 → (∀ k, k < n → c + r k ≠ 0) →
      problem_spec_finiteProduct c n r q (implementation_finiteProduct c n r q) := by
  intro c n r q _ _
  unfold problem_spec_finiteProduct implementation_finiteProduct
  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tight equational spec. problem_spec_finiteProduct := result = ((List.range n).map (fun k => c + r k)).prod / q, with correct_* binders q ≠ 0 AND ∀ k<n, c + r k ≠ 0 (narrowed modeled slice). Any verifying impl must equal the genuine product/q across the ENTIRE modeled slice; the only adversarial freedom is off-slice (q=0 or a zero factor) behavior + computation order.

SAME_SPEC: all 7 attacks + positive control return same_spec=True (only impl+proof regions edited; axioms/pure/pre/post byte-identical).

Battery (all commands: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean = Solution.lean impl: lean_verify exit 0; #print axioms clean [propext, Classical.choice, Quot.sound]. Gold patch.diff run_resolve => RESOLVED (oracle valid).
- atk_1 (off-slice: if q=0 return 42 else prod/q): exit 0, clean axioms. Faithful patch (q.is_zero -> S(42), applies clean to base) run_resolve run_id sbu-audit-eq-13551-atk1f => RESOLVED.
- atk_2 (off-slice: if 0<n ∧ c+r 0 = 0 return 999 else prod/q; exploits the factor≠0 binder — the exact G-PANEL-2 zero-factor witness class): exit 0, clean axioms. INITIAL faithful patch used `if (n-a+1)>0 and term.subs(k,a)==0` which raised a symbolic truth-value TypeError (UNFAITHFUL, crashes on-slice) => did NOT resolve. Traced to patch bug, not spec. Corrected to symbolic-safe `if (n-a+1).is_positive and term.subs(k,a).is_zero: return S(999)` (applies clean to base) run_resolve run_id sbu-audit-eq-13551-atk2c => RESOLVED. So NOT a spec break.
- atk_7 (off-slice: return if q=0 then 0 else prod/q): exit 0, clean axioms. Faithful patch (q.is_zero -> S(0)) run_resolve run_id sbu-audit-eq-13551-atk7f => RESOLVED.
- atk_3 (prepatch bug: (c^n + ∏ r k)/q): lean_verify exit 1 (does NOT verify) — spec correctly rejects the summand-wise shortcut. This is also the prepatch bug; prepatch reproduced via patch_prepatch_noop.diff (keeps buggy sum-of-products line) run_resolve => did NOT resolve (F2P test_issue_13546 fails), confirming G-DIFF/prepatch.
- atk_4 (partial-domain: if n=0 return 0): exit 1, does NOT verify (product over empty range = 1, not 0).
- atk_5 (control-flow: loop [0:n-1], drops last factor): exit 1, does NOT verify.
- atk_6 (ungrounded-oracle echo: SUM of terms instead of product): exit 1, does NOT verify.

Parallelism: attacks verified in background batches of ≤4; resolve runs launched concurrently (≤4).

CONCLUSION: every genuinely-wrong-on-slice impl (atk_3/4/5/6) FAILS to verify — the equational spec is not too weak. Every impl that verifies with clean axioms (atk_1/2/7) differs from gold ONLY off the modeled slice, and each one's FAITHFUL refined patch RESOLVES under the official harness. No verifying-clean-axiom impl has a faithful patch that fails to resolve => verify ⇒ correct holds. The atk_2 non-resolve was an unfaithful-patch artifact (symbolic crash), corrected and re-run to RESOLVED.

REFINEMENT.MD A-LEG AUDIT: refinement.md declares A-tags = None (no A-consumed, no A-reference). Confirmed: Solution.lean axioms region has NO `axiom`/`opaque` declarations (grep clean); the range-product is modeled DEEPLY as (List.range n).map (c + r ·) |>.prod. axiom_check.py is a legitimate skip stub (G-AX status=skip, meta.json G-AX pass). All legs are R (carriers, exp(∑log)=∏ product body) or I (final /q). No kind-3 legs. The A-audit is vacuously satisfied and the R/I differential burden is carried by G-CONF (meta.json: 120168 checks, 546 distinct symbolic evals, 0 disagreements). The modeled-slice narrowing (∀k<n, c+r k≠0) is justified: real post-patch exp(Sum(log(p))) yields exp(zoo) on a zero factor (undefined symbolic residue, not a rational), so a zero factor is genuinely outside the ℚ-valued observable slice, and no hidden test reaches this branch off-slice (atk_2 faithful patch resolves despite off-slice divergence).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1.lean`, `atk_2.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The value of a finite product of a separable additive term over a range of
integer positions, divided by a constant.

The term multiplied across the range has the shape `c + r(k)`, where `c` is a
constant (independent of the position) and `r(k)` is the position-dependent
remainder, evaluated at every position `k` of the range `0, 1, …, n-1`. The whole
product is then divided by a constant `q` — the value that the range-product of
the term's denominator collapses to, which is a plain number.

The value of the construct is the genuine product over the range: multiply the
term `c + r(k)` across every position `k < n`, then divide by `q`. No component of
the result is left free — it is fully determined by `c`, the length `n`, the
remainder function `r`, and the divisor `q`.

The modeled slice is the non-degenerate case: the divisor `q` is nonzero and
every factor `c + r(k)` over the range is nonzero (a zero factor makes the real
construct's evaluation degenerate rather than a plain number, and lies outside
the modeled slice).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the range-product is modelled
-- directly as the product of the per-position term values, so no `opaque`/`axiom`
-- callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The value equals the genuine product of the term `c + r k` taken over every
position `k < n` of the range, divided by the constant `q`. The product of the
additive term is its true product across the range — not any summand-wise
shortcut — so the result is pinned to `c`, the length `n`, the remainder function
`r`, and the divisor `q`. -/
def problem_spec_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) (result : ℚ) : Prop :=
  result = ((List.range n).map (fun k => c + r k)).prod / q
-- post-conditions-end

-- impl-start
def implementation_finiteProduct (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ) : ℚ := Id.run do
  let mut acc : ℚ := 1
  for k in [0:n] do
    acc := acc * (c + r k)
  return acc / q
-- impl-end

-- proof-start
theorem correct_finiteProduct :
    ∀ (c : ℚ) (n : ℕ) (r : ℕ → ℚ) (q : ℚ), q ≠ 0 → (∀ k, k < n → c + r k ≠ 0) →
      problem_spec_finiteProduct c n r q (implementation_finiteProduct c n r q) := by
  intro c n r q _ _
  unfold problem_spec_finiteProduct implementation_finiteProduct
  simp [List.range_eq_range', List.prod_eq_foldl, List.foldl_map]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: tight equational spec. problem_spec_finiteProduct := result = ((List.range n).map (fun k => c + r k)).prod / q, with correct_* binders q ≠ 0 AND ∀ k<n, c + r k ≠ 0 (narrowed modeled slice). Any verifying impl must equal the genuine product/q across the ENTIRE modeled slice; the only adversarial freedom is off-slice (q=0 or a zero factor) behavior + computation order.

SAME_SPEC: all 7 attacks + positive control return same_spec=True (only impl+proof regions edited; axioms/pure/pre/post byte-identical).

Battery (all commands: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean = Solution.lean impl: lean_verify exit 0; #print axioms clean [propext, Classical.choice, Quot.sound]. Gold patch.diff run_resolve => RESOLVED (oracle valid).
- atk_1 (off-slice: if q=0 return 42 else prod/q): exit 0, clean axioms. Faithful patch (q.is_zero -> S(42), applies clean to base) run_resolve run_id sbu-audit-eq-13551-atk1f => RESOLVED.
- atk_2 (off-slice: if 0<n ∧ c+r 0 = 0 return 999 else prod/q; exploits the factor≠0 binder — the exact G-PANEL-2 zero-factor witness class): exit 0, clean axioms. INITIAL faithful patch used `if (n-a+1)>0 and term.subs(k,a)==0` which raised a symbolic truth-value TypeError (UNFAITHFUL, crashes on-slice) => did NOT resolve. Traced to patch bug, not spec. Corrected to symbolic-safe `if (n-a+1).is_positive and term.subs(k,a).is_zero: return S(999)` (applies clean to base) run_resolve run_id sbu-audit-eq-13551-atk2c => RESOLVED. So NOT a spec break.
- atk_7 (off-slice: return if q=0 then 0 else prod/q): exit 0, clean axioms. Faithful patch (q.is_zero -> S(0)) run_resolve run_id sbu-audit-eq-13551-atk7f => RESOLVED.
- atk_3 (prepatch bug: (c^n + ∏ r k)/q): lean_verify exit 1 (does NOT verify) — spec correctly rejects the summand-wise shortcut. This is also the prepatch bug; prepatch reproduced via patch_prepatch_noop.diff (keeps buggy sum-of-products line) run_resolve => did NOT resolve (F2P test_issue_13546 fails), confirming G-DIFF/prepatch.
- atk_4 (partial-domain: if n=0 return 0): exit 1, does NOT verify (product over empty range = 1, not 0).
- atk_5 (control-flow: loop [0:n-1], drops last factor): exit 1, does NOT verify.
- atk_6 (ungrounded-oracle echo: SUM of terms instead of product): exit 1, does NOT verify.

Parallelism: attacks verified in background batches of ≤4; resolve runs launched concurrently (≤4).

CONCLUSION: every genuinely-wrong-on-slice impl (atk_3/4/5/6) FAILS to verify — the equational spec is not too weak. Every impl that verifies with clean axioms (atk_1/2/7) differs from gold ONLY off the modeled slice, and each one's FAITHFUL refined patch RESOLVES under the official harness. No verifying-clean-axiom impl has a faithful patch that fails to resolve => verify ⇒ correct holds. The atk_2 non-resolve was an unfaithful-patch artifact (symbolic crash), corrected and re-run to RESOLVED.

REFINEMENT.MD A-LEG AUDIT: refinement.md declares A-tags = None (no A-consumed, no A-reference). Confirmed: Solution.lean axioms region has NO `axiom`/`opaque` declarations (grep clean); the range-product is modeled DEEPLY as (List.range n).map (c + r ·) |>.prod. axiom_check.py is a legitimate skip stub (G-AX status=skip, meta.json G-AX pass). All legs are R (carriers, exp(∑log)=∏ product body) or I (final /q). No kind-3 legs. The A-audit is vacuously satisfied and the R/I differential burden is carried by G-CONF (meta.json: 120168 checks, 546 distinct symbolic evals, 0 disagreements). The modeled-slice narrowing (∀k<n, c+r k≠0) is justified: real post-patch exp(Sum(log(p))) yields exp(zoo) on a zero factor (undefined symbolic residue, not a rational), so a zero factor is genuinely outside the ℚ-valued observable slice, and no hidden test reaches this branch off-slice (atk_2 faithful patch resolves despite off-slice divergence).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sympy__sympy-13551 lean bundle. FINDINGS:

1) SPEC BYTE-IDENTITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean.language) = True. The spec region (axioms/pure/pre/post-conditions views) is identical between pre- and post-patch, so there is no spec drift across the diff pair.

2) COMPILES + CLEAN AXIOMS: scripts/lean_verify.sh on Solution.lean exits 0; `#print axioms correct_finiteProduct` = [propext, Classical.choice, Quot.sound] only. No sorryAx — the proof is genuine, not fake.

3) REAL-REPO FAITHFULNESS: Applied patch.diff to the base_commit worktree; confirmed the live post-patch branch is `p = exp(Sum(log(p),(k,a,n)))` (products.py ~285). F2P test_issue_13546 verified: Product(n+1/2**k,(k,0,n-1)).doit().subs(n,2) == 15/2.

Ran ~1300 randomized inputs over the modeled nonzero-factor slice (single- and two-term geometric remainders c + a/base1**k + b/base2**k, negative factors, bases 2-7, lengths n=2..5). EVERY input inside the slice matched the genuine product ((List.range n).map (fun k => c + r k)).prod and returned a rational — 0 mismatches, 0 non-rational outputs. The exp(sum log) identity is exact for nonzero factors (branch-cut phases cancel under exp), so even negative factors agree with the modeled product.

4) SLICE BINDER IS JUSTIFIED, NOT OVER-STRONG: The only divergence class is a ZERO factor, where the real callee returns exp(zoo)/q (an undefined non-rational symbolic residue), e.g. term n-3/2**k at n=3 has factor 0 at k=0 and the real result is exp(zoo)/8 while the genuine product is 0. This is exactly what the correct_* binder `∀ k, k < n → c + r k ≠ 0` excludes. The binder is a genuine well-definedness precondition (the ℚ-valued observable does not exist off it), not a spec-strengthening that masks real behavior. `q ≠ 0` is the genuine side-condition of the totalized ℚ division. Both binders are on correct_* (not conjuncts of problem_spec), per SPEC_GUIDE.

CONCLUSION: No input within the modeled slice makes the modeled function disagree with the real patched callee. The spec is a faithful abstraction — the differential burden (buggy prepatch c^n + ∏r vs correct ∏(c+r)) is preserved (G-DIFF holds), and the modeled-slice narrowing is a correctness-preserving well-definedness restriction. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lean bundle sympy__sympy-13551. Judged the spec view (spec_view over Solution.lean: docstring + problem_spec_finiteProduct; impl and proof regions elided as the consumer sees them) against the public problem_statement ONLY (not hints_text).

Mechanical screen: leakage.screen() passes (hard_failures=[], passed=True), independently reproduced. No diff markers; patched file path 'sympy/concrete/products.py' and its dotted module absent; patched symbol '_eval_product' (normalized 'eval_product') appears in NO spec-view identifier or comment; narration scan clean.

Semantic check: the spec exposes only the abstract carrier — result = ((List.range n).map (fun k => c + r k)).prod / q, i.e. the genuine finite product of an additive term c + r(k) over positions k<n divided by q, plus a non-degenerate-slice note (q ≠ 0, every factor nonzero). This is exactly the correct behavior already made public by the problem_statement, which itself displays the buggy sum-shaped output (2**(n*(-n+1)/2) + n**n) and states the correct value is the genuine product (2 + 2^0)·(2 + 2^(-1)) = 15/2. The spec-view phrase 'true product across the range — not any summand-wise shortcut' merely restates the product-vs-sum contrast already implicit in the public buggy-vs-correct example; it names no repo symbol, no patched mechanism (exp/Sum/log/as_coeff_Add/q-Pochhammer), and no edit location.

same_spec(Solution.lean, Solution_prepatch.lean, lean) = True — spec region byte-identical; prepatch differs only in the elided impl/proof (buggy c^n + ∏ r k vs genuine product). No relaxed_leakage flag and no RELAXED_LEAKAGE.md, so this is a strict NO-LEAKAGE finding, not a panel_3 relaxation deferral. Nothing in the spec view reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
