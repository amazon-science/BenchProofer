# P2 adversarial audit — sympy__sympy-20428

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_12.py`, `atk_13.py`, `atk_15.py`, `atk_16.py`, `atk_17.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_14.py`, `atk_18.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 18 same-spec wrong impls run; 8 came back CANDIDATE (share spec AND verify); all 8 faithful refined patches were materialized and RUN through run_resolve and ALL EIGHT RESOLVED. No verifying impl exists whose faithful patch fails the harness, so verify=>correct is not refuted for this bundle. The one non-resolve I observed (atk_9, first patch attempt) was MY OWN unfaithful refinement, not a spec hole -- see notes.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,7 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
-    return c.mzero == 0
+    return c.lit0 == 0
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,6 +99,10 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
+    while c.mzero >= 0:
+        Invariant(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
+        Invariant(c.mzero == 0 or c.mzero == 1)
+        pass
     return c.mzero == 0
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,6 +99,12 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
+    i = 1
+    while i > 0:
+        Invariant(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
+        Invariant(i == 1)
+        Invariant(MustTerminate(2))
+        pass
     return c.mzero == 0
     # impl-end
 
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,6 +99,11 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
+    if c.lit0 == 1 and c.mzero == 0:
+        while c.lit0 == 1:
+            Invariant(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
+            Invariant(c.lit0 == 1)
+            pass
     return c.mzero == 0
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,6 +127,11 @@
     # post-conditions-end
     # impl-start
     if coeff_truthy(c):
+        if c.lit0 == 1:
+            while c.lit0 == 1:
+                Invariant(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
+                Invariant(c.lit0 == 1)
+                pass
         return 1
     else:
         return 0
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,7 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
-    return c.mzero == 0
+    return not (c.lit0 == 1 or c.mzero == 1)
     # impl-end
 
 
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,8 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
-    return c.mzero == 0
+    d = Coeff(c.lit0, c.mzero)
+    return d.mzero == 0
     # impl-end
 
 
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,9 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
-    return c.mzero == 0
+    d = Coeff(0, c.mzero)
+    d.mzero = 0
+    return d.mzero == 0
     # impl-end
 
 
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,8 +126,8 @@
     Ensures(Implies(c.mzero == 0, Result() == 1))
     # post-conditions-end
     # impl-start
+    d = Coeff(0, 1)
     if coeff_truthy(c):
         return 1
-    else:
-        return 0
+    return 0
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,9 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
-    return c.mzero == 0
+    if c.mzero == 1:
+        return False
+    return c.lit0 == 0
     # impl-end
 
 
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,6 +99,8 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
+    if c.lit0 == 1 and c.mzero == 0:
+        return False
     return c.mzero == 0
     # impl-end
 
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,7 +99,7 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
-    return c.mzero == 0
+    return c.lit0 == 0 or c.mzero == 0
     # impl-end
 
 
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,8 +126,7 @@
     Ensures(Implies(c.mzero == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    if coeff_truthy(c):
-        return 1
-    else:
+    if c.lit0 == 1:
         return 0
+    return 1
     # impl-end
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,8 +126,9 @@
     Ensures(Implies(c.mzero == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    if coeff_truthy(c):
+    if c.lit0 == 1 and c.mzero == 0:
         return 1
-    else:
+    if c.mzero == 1:
         return 0
+    return 1
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,6 +99,8 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
+    if c.lit0 == 1 and c.mzero == 0:
+        raise ValueError()
     return c.mzero == 0
     # impl-end
 
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,6 +99,8 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
+    if c.mzero == 1:
+        raise ValueError()
     return c.mzero == 0
     # impl-end
 
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -126,8 +126,7 @@
     Ensures(Implies(c.mzero == 0, Result() == 1))
     # post-conditions-end
     # impl-start
-    if coeff_truthy(c):
-        return 1
-    else:
-        return 0
+    if c.mzero == 1:
+        return strip_constant_len(c)
+    return 1
     # impl-end
```

Attack 18 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -99,6 +99,8 @@
     Ensures(Result() == (c.mzero == 0))
     # post-conditions-end
     # impl-start
+    if c.lit0 == 1 and c.mzero == 0:
+        Assert(False)
     return c.mzero == 0
     # impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A-legs (axioms/deep-model refs) + model<->patch correspondence, per instructions; R/I legs left to G-CONF.

**SETUP:** scratch= All 18 attacks built by copying the frozen model.py and editing ONLY impl regions (mk.py); `adversary same-spec` returned SAME for all 18 + the positive control. pos_control.py is byte-identical to the frozen model.py (diff empty) and returns CANDIDATE i.e. it VERIFIES. Verifications run 3-at-a-time as detached background jobs (runw.sh); resolves 3-at-a-time (runres.sh). A real sympy tree at base_commit c0e85160 was built as a git worktree (wt/sympy) + a vendored mpmath wheel on PYTHONPATH, so every A-leg claim was checked against EXECUTED SymPy, not read off the prose.

**COMMANDS:** per attack N: `python -m swebench_unified.adversary weakness nagini sympy__sympy-20428 atk_N.py` (logs atk_N.weak.log, exits in weak.results); per verifying attack: `python res1.py atk_N` -> swebench_unified.harness.run_resolve (verdicts in resolve_atk_N.json).

### RESULT TABLE (weakness exit -> resolve):
 atk_1  pre-patch structural bug `return c.lit0 == 0`            rc=2 REJECTED (G-DIFF holds)
 atk_2  bare divergence (spin, no measure) before correct return  rc=2 REJECTED (obligation leak)
 atk_3  divergence with a CONSTANT loop measure                   rc=2 REJECTED
 atk_4  divergence guarded by lit0==1 and mzero==0                rc=0 CANDIDATE -> RESOLVED
 atk_5  infeasible-guarded spin at the STRIP site                 rc=2 REJECTED
 atk_6  falsy iff (structurally zero OR denotes zero)             rc=0 CANDIDATE -> RESOLVED
 atk_7  ungrounded-oracle echo: answer off a fabricated copy      rc=0 CANDIDATE -> RESOLVED
 atk_8  control-flow-effect: mutate a scratch copy               rc=2 REJECTED
 atk_9  strip keeps len-1 but fabricates a denoting-zero coeff    rc=0 CANDIDATE -> RESOLVED (faithful patch)
 atk_10 RETAINS the buggy structural test on the non-zero branch  rc=0 CANDIDATE -> RESOLVED
 atk_11 wrong VALUE in the model-infeasible state                 rc=0 CANDIDATE -> RESOLVED
 atk_12 partial domain: falsy only when BOTH facets say zero      rc=2 REJECTED
 atk_13 strip keyed on the structural facet                       rc=2 REJECTED
 atk_14 wrong strip value in the model-infeasible state           rc=0 CANDIDATE -> RESOLVED (attempt 2/3, flaky-but-resolved)
 atk_15 exception in the model-infeasible state                   rc=2 REJECTED
 atk_16 exception in a FEASIBLE state (mzero==1)                   rc=2 REJECTED
 atk_17 recursive divergence in a feasible state                  rc=2 REJECTED
 atk_18 CONTROL: Assert(False) in the infeasible state            rc=0 CANDIDATE -> RESOLVED

HONESTY NOTE / the one non-resolve, and why it is NOT a finding: my FIRST atk_9 patch (kept as resolve_atk_9_UNFAITHFUL.json) did NOT resolve -- report shows F2P test_issue_20427 PASSING but P2P test_issue_12400 FAILING. I then re-read atk_9's model impl: `d = Coeff(0, 1)` is a DEAD local that is never read and never returned; the returned length is exactly gold's. My patch had instead REPLACED the retained coefficient in dup_strip, i.e. it changed observable behaviour the model never changed -- an unfaithful refinement, and reporting it as a spec break would have manufactured a weakness (cf. the retained-attack-labels trap). The corrected faithful image (gold hunk + a correspondingly dead local in dup_strip, patch_atk_9.diff) RESOLVED. This is the standard trap that a G-EQ non-resolve must be attributed to the MODEL's deviation, never to the auditor's patch-writing latitude.

### A-LEG AUDIT (the substance):
1. atk_18 -- the `Assert(False)` control -- VERIFIES, which mechanically PROVES the state (lit0==1 and mzero==0) is infeasible in-model, i.e. the class invariant Implies(lit0==1, mzero==1) is doing real work and the whole atk_4/11/14/18 cluster's wrong branch is dead code in-model. That makes the invariant a genuine A-leg trust point, so I attacked it directly rather than trusting mapping.md's prose ("the SymPy fact Integer(0).is_zero is True").
2. probe_invariant.py / probe_wide.py: swept 552 real EX coefficients for any Expr with (f.ex == 0) truthy but f.ex.is_zero not True -- zero-ish atoms (Integer(0), S.Zero, Float(0)/-0.0/varying precision, Rational(0,n)), cancelling binaries over a 13-element base, unevaluated Add/Mul/Pow zeros, is_zero=None expressions, nan/oo/zoo/I, and zero=True/nonzero=True Symbols. HITS = 0. The invariant holds on the real domain, which is exactly why the four infeasible-guard attacks' patches all resolve: their wrong branch is unreachable in the repo too.
3. probe_domain.py: every one of 43 real coefficients lands in a PRECONDITION-ADMITTED (lit0,mzero) state, populating all three of {(1,1):11, (0,0):31, (0,1):1} -- no vacuous/unconstrained state, no partial-domain hole -- and the model's coeff_truthy agrees with gold `not f.ex.is_zero` on all 43.
4. TRI-STATE CHECK (probe_tristate.py), the sharpest A-reference concern: real Expr.is_zero is True/False/None while the model's mzero is BINARY. mapping.md pins the collapse as mzero==1 <-> `is_zero is True`, so None falls into mzero==0 (TRUTHY). I confirmed this is the FAITHFUL choice: is_zero is None for 12 of 17 sampled EX coefficients (x, x+1, cos(x), log(x), Abs(x), gamma(x),...), and gold's `not f.ex.is_zero` treats them as truthy, agreeing with the mapping; the alternative collapse (`is_zero is False`) would DIFFER on all 12. So the mapping picked the right side of a genuinely load-bearing choice. atk_6 probes the same axis behaviourally (adds the structural disjunct) and still resolves, because lit0==1 implies mzero==1 makes the disjunct redundant.
5. B1/B2 correspondence (probe_strip.py) against the REAL untouched dup_strip, post-patch: over 24 constant lists, len(dup_strip([c])) == strip_constant_len's modeled length in every case, and when kept the retained element is the identical object (so the length abstraction loses nothing the F2P observes). Confirmed dup_strip([]) == [] and the poly-level consequence Poly(sqrt2-sqrt2,x,EX).rep.rep == [] and == Poly(0,x,EX), vs len 1 for Poly(sqrt2,x,EX).
6. The bundle's own G-AX (axiom_check.py) executed against the worktree with patch.diff applied: exit 0 ("11 non-zero, 3 literal-zero, 5 denoting-zero + the exact issue clear_denoms coefficient"). NB axiom_check's lit0 is NARROWER than the refinement's (it adds `is_zero is True and is_Integer`, so Float(0) gets lit0=0 there while the refinement gives lit0=1). This is a slight documentation looseness, not a soundness gap: I checked BOTH readings in probe_invariant.py and neither admits the infeasible state, and lit0 is never read by the gold-image impl anyway (it appears only in the precondition/invariant).

**MUSTTERMINATE IS LOAD-BEARING AND CORRECTLY SCOPED:** three distinct divergence encodings were rejected -- bare spin (atk_2), constant-measure loop (atk_3), infeasible-guarded spin at the strip site (atk_5), plus recursive divergence (atk_17) -- while the honest straight-line positive control verifies. So the historic partial-correctness hole (the recorded atk_8 240s timeout cited in refinement.md B2) is genuinely closed and the obligation does not over-constrain. Note MustTerminate does NOT police ABRUPT exit: atk_15/atk_16 raise instead of diverging and were rejected on the VALUE postcondition instead, so that axis is covered too.

**REFINEMENT.MD LEG AUDIT:** 4 legs, tags A1=R, A2=A-reference, B1=R+I, B2=I. No kind-3 and no A-consumed leg -- verified mechanically: model.py contains ZERO @ContractOnly declarations (the single "ContractOnly" hit at line 73 is a comment saying none are needed), meta.json axioms == [] and deep_model_references kinds == ['A-reference']. So the proof consumes no unproven Ensures at all; the only deep-model trust point is Coeff.mzero <-> Expr.is_zero, which is what G-AX validates out-of-band and what probes 2/3/4 above independently corroborate. A2's and B1/B2's stated correspondence to the real callees (`__bool__` at expressiondomain.py:123, dup_strip's guard at densebasic.py:265) matches the source I read in the worktree, and patch.diff is the gold hunk verbatim.

**VERDICT:** SOUND. 18 attacks (>= the required 5) all executed to a definite weakness verdict, prepatch bug reproduced (rejected), positive control verifies, and every one of the 8 verifying candidates had its faithful patch materialized and RUN through the official harness with all 8 RESOLVED. Residual risk is the ordinary A-reference one -- mzero is validated against Expr.is_zero by finite probing (my 552-expression sweep found no violation), not proved -- which is the documented trust point, not a defect.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_8.py`, `atk_12.py`, `atk_13.py`, `atk_15.py`, `atk_16.py`, `atk_17.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_14.py`, `atk_18.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 18 same-spec wrong impls run; 8 came back CANDIDATE (share spec AND verify); all 8 faithful refined patches were materialized and RUN through run_resolve and ALL EIGHT RESOLVED. No verifying impl exists whose faithful patch fails the harness, so verify=>correct is not refuted for this bundle. The one non-resolve I observed (atk_9, first patch attempt) was MY OWN unfaithful refinement, not a spec hole -- see notes.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A-legs (axioms/deep-model refs) + model<->patch correspondence, per instructions; R/I legs left to G-CONF.

**SETUP:** scratch= All 18 attacks built by copying the frozen model.py and editing ONLY impl regions (mk.py); `adversary same-spec` returned SAME for all 18 + the positive control. pos_control.py is byte-identical to the frozen model.py (diff empty) and returns CANDIDATE i.e. it VERIFIES. Verifications run 3-at-a-time as detached background jobs (runw.sh); resolves 3-at-a-time (runres.sh). A real sympy tree at base_commit c0e85160 was built as a git worktree (wt/sympy) + a vendored mpmath wheel on PYTHONPATH, so every A-leg claim was checked against EXECUTED SymPy, not read off the prose.

**COMMANDS:** per attack N: `python -m swebench_unified.adversary weakness nagini sympy__sympy-20428 atk_N.py` (logs atk_N.weak.log, exits in weak.results); per verifying attack: `python res1.py atk_N` -> swebench_unified.harness.run_resolve (verdicts in resolve_atk_N.json).

### RESULT TABLE (weakness exit -> resolve):
 atk_1  pre-patch structural bug `return c.lit0 == 0`            rc=2 REJECTED (G-DIFF holds)
 atk_2  bare divergence (spin, no measure) before correct return  rc=2 REJECTED (obligation leak)
 atk_3  divergence with a CONSTANT loop measure                   rc=2 REJECTED
 atk_4  divergence guarded by lit0==1 and mzero==0                rc=0 CANDIDATE -> RESOLVED
 atk_5  infeasible-guarded spin at the STRIP site                 rc=2 REJECTED
 atk_6  falsy iff (structurally zero OR denotes zero)             rc=0 CANDIDATE -> RESOLVED
 atk_7  ungrounded-oracle echo: answer off a fabricated copy      rc=0 CANDIDATE -> RESOLVED
 atk_8  control-flow-effect: mutate a scratch copy               rc=2 REJECTED
 atk_9  strip keeps len-1 but fabricates a denoting-zero coeff    rc=0 CANDIDATE -> RESOLVED (faithful patch)
 atk_10 RETAINS the buggy structural test on the non-zero branch  rc=0 CANDIDATE -> RESOLVED
 atk_11 wrong VALUE in the model-infeasible state                 rc=0 CANDIDATE -> RESOLVED
 atk_12 partial domain: falsy only when BOTH facets say zero      rc=2 REJECTED
 atk_13 strip keyed on the structural facet                       rc=2 REJECTED
 atk_14 wrong strip value in the model-infeasible state           rc=0 CANDIDATE -> RESOLVED (attempt 2/3, flaky-but-resolved)
 atk_15 exception in the model-infeasible state                   rc=2 REJECTED
 atk_16 exception in a FEASIBLE state (mzero==1)                   rc=2 REJECTED
 atk_17 recursive divergence in a feasible state                  rc=2 REJECTED
 atk_18 CONTROL: Assert(False) in the infeasible state            rc=0 CANDIDATE -> RESOLVED

HONESTY NOTE / the one non-resolve, and why it is NOT a finding: my FIRST atk_9 patch (kept as resolve_atk_9_UNFAITHFUL.json) did NOT resolve -- report shows F2P test_issue_20427 PASSING but P2P test_issue_12400 FAILING. I then re-read atk_9's model impl: `d = Coeff(0, 1)` is a DEAD local that is never read and never returned; the returned length is exactly gold's. My patch had instead REPLACED the retained coefficient in dup_strip, i.e. it changed observable behaviour the model never changed -- an unfaithful refinement, and reporting it as a spec break would have manufactured a weakness (cf. the retained-attack-labels trap). The corrected faithful image (gold hunk + a correspondingly dead local in dup_strip, patch_atk_9.diff) RESOLVED. This is the standard trap that a G-EQ non-resolve must be attributed to the MODEL's deviation, never to the auditor's patch-writing latitude.

### A-LEG AUDIT (the substance):
1. atk_18 -- the `Assert(False)` control -- VERIFIES, which mechanically PROVES the state (lit0==1 and mzero==0) is infeasible in-model, i.e. the class invariant Implies(lit0==1, mzero==1) is doing real work and the whole atk_4/11/14/18 cluster's wrong branch is dead code in-model. That makes the invariant a genuine A-leg trust point, so I attacked it directly rather than trusting mapping.md's prose ("the SymPy fact Integer(0).is_zero is True").
2. probe_invariant.py / probe_wide.py: swept 552 real EX coefficients for any Expr with (f.ex == 0) truthy but f.ex.is_zero not True -- zero-ish atoms (Integer(0), S.Zero, Float(0)/-0.0/varying precision, Rational(0,n)), cancelling binaries over a 13-element base, unevaluated Add/Mul/Pow zeros, is_zero=None expressions, nan/oo/zoo/I, and zero=True/nonzero=True Symbols. HITS = 0. The invariant holds on the real domain, which is exactly why the four infeasible-guard attacks' patches all resolve: their wrong branch is unreachable in the repo too.
3. probe_domain.py: every one of 43 real coefficients lands in a PRECONDITION-ADMITTED (lit0,mzero) state, populating all three of {(1,1):11, (0,0):31, (0,1):1} -- no vacuous/unconstrained state, no partial-domain hole -- and the model's coeff_truthy agrees with gold `not f.ex.is_zero` on all 43.
4. TRI-STATE CHECK (probe_tristate.py), the sharpest A-reference concern: real Expr.is_zero is True/False/None while the model's mzero is BINARY. mapping.md pins the collapse as mzero==1 <-> `is_zero is True`, so None falls into mzero==0 (TRUTHY). I confirmed this is the FAITHFUL choice: is_zero is None for 12 of 17 sampled EX coefficients (x, x+1, cos(x), log(x), Abs(x), gamma(x),...), and gold's `not f.ex.is_zero` treats them as truthy, agreeing with the mapping; the alternative collapse (`is_zero is False`) would DIFFER on all 12. So the mapping picked the right side of a genuinely load-bearing choice. atk_6 probes the same axis behaviourally (adds the structural disjunct) and still resolves, because lit0==1 implies mzero==1 makes the disjunct redundant.
5. B1/B2 correspondence (probe_strip.py) against the REAL untouched dup_strip, post-patch: over 24 constant lists, len(dup_strip([c])) == strip_constant_len's modeled length in every case, and when kept the retained element is the identical object (so the length abstraction loses nothing the F2P observes). Confirmed dup_strip([]) == [] and the poly-level consequence Poly(sqrt2-sqrt2,x,EX).rep.rep == [] and == Poly(0,x,EX), vs len 1 for Poly(sqrt2,x,EX).
6. The bundle's own G-AX (axiom_check.py) executed against the worktree with patch.diff applied: exit 0 ("11 non-zero, 3 literal-zero, 5 denoting-zero + the exact issue clear_denoms coefficient"). NB axiom_check's lit0 is NARROWER than the refinement's (it adds `is_zero is True and is_Integer`, so Float(0) gets lit0=0 there while the refinement gives lit0=1). This is a slight documentation looseness, not a soundness gap: I checked BOTH readings in probe_invariant.py and neither admits the infeasible state, and lit0 is never read by the gold-image impl anyway (it appears only in the precondition/invariant).

**MUSTTERMINATE IS LOAD-BEARING AND CORRECTLY SCOPED:** three distinct divergence encodings were rejected -- bare spin (atk_2), constant-measure loop (atk_3), infeasible-guarded spin at the strip site (atk_5), plus recursive divergence (atk_17) -- while the honest straight-line positive control verifies. So the historic partial-correctness hole (the recorded atk_8 240s timeout cited in refinement.md B2) is genuinely closed and the obligation does not over-constrain. Note MustTerminate does NOT police ABRUPT exit: atk_15/atk_16 raise instead of diverging and were rejected on the VALUE postcondition instead, so that axis is covered too.

**REFINEMENT.MD LEG AUDIT:** 4 legs, tags A1=R, A2=A-reference, B1=R+I, B2=I. No kind-3 and no A-consumed leg -- verified mechanically: model.py contains ZERO @ContractOnly declarations (the single "ContractOnly" hit at line 73 is a comment saying none are needed), meta.json axioms == [] and deep_model_references kinds == ['A-reference']. So the proof consumes no unproven Ensures at all; the only deep-model trust point is Coeff.mzero <-> Expr.is_zero, which is what G-AX validates out-of-band and what probes 2/3/4 above independently corroborate. A2's and B1/B2's stated correspondence to the real callees (`__bool__` at expressiondomain.py:123, dup_strip's guard at densebasic.py:265) matches the source I read in the worktree, and patch.diff is the gold hunk verbatim.

**VERDICT:** SOUND. 18 attacks (>= the required 5) all executed to a definite weakness verdict, prepatch bug reproduced (rejected), positive control verifies, and every one of the 8 verifying candidates had its faithful patch materialized and RUN through the official harness with all 8 RESOLVED. Residual risk is the ordinary A-reference one -- mzero is validated against Expr.is_zero by finite probing (my 552-expression sweep found no violation), not proved -- which is the documented trust point, not a defect.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK LANE:** faithfulness-break (is the spec too strong / does the modeled function disagree with the real callee on some input?). Reference = my own fresh worktree of sympy at base_commit c0e85160406f9bf2bcaa2992138587668a1cd0bc with patch.diff APPLIED (); base worktree () kept only for the untouched callee dup_strip and for the G-DIFF/F2P direction.

### WHAT THE SPEC CLAIMS (frozen regions of model.py):
  coeff_truthy: Ensures(Result() == (c.mzero == 0))
  strip_constant_len: Ensures(Implies(c.mzero==1, Result()==0)) and Ensures(Implies(c.mzero==0, Result()==1))
  Coeff class invariant / precondition: Implies(lit0==1, mzero==1); both facets in {0,1}; MustTerminate(1/2/3).
Bridge pinned by mapping.md sec.2: mzero==1 iff f.ex.is_zero is True; lit0==1 iff canonical form is the bare Integer(0) literal. Real callees: ExpressionDomain.Expression.`__bool__` (expressiondomain.py:123, post-patch `return not f.ex.is_zero`) and dup_strip([coeff]) (densebasic.py:252-265, UNCHANGED by the patch, so base is the correct reference for it -- I read it there and confirmed the `if not f or f[0]` guard is exactly keep-[c]-iff-bool(c)).

SPEC-REGION INTEGRITY (precondition for any verdict): markers.region_hashes(model.py, nagini backend) recomputed by me equals meta.json G-HYGIENE region_hashes EXACTLY on all six regions (axioms 7b724599..., pure 8948a17a..., pre-conditions a52aac36..., post-conditions 29699ba8..., impl a1277197..., spec_view 3a325eb6...). model.py sha256 34f8d003069f30c9d0d504642fdcc3485e01436ac4e6d2703c2820d529339dfb == the sha recorded in G-EQ.sources. So I audited the frozen spec, not a drifted copy.

### EVIDENCE THE MODELED FUNCTION AGREES WITH THE REAL CALLEE (no diverging input found):
1. Bundle's own checks reproduce on MY worktree, not just as recorded: axiom_check.py exit 0; conformance_check.py exit 0 (100032 coefficients, 0 disagreements, facet coverage (0,0)=65171 (0,1)=20414 (1,1)=14447).
2. INDEPENDENT fuzz, fresh seed 987654321 (deliberately NOT the bundle's 20428), 250000 real EX coefficients, checking all three spec obligations per input (class invariant, coeff_truthy == bool(coeff), strip_constant_len == len(dup_strip([coeff]))): 0 divergences. Facet-state coverage (0,1)=36548 (0,0)=172530 (1,1)=40922 -- the discriminating state (lit0=0, mzero=1) was hit 36548 times, so the agreement is not vacuous on the bug-triggering shape.
3. EXOTIC-TYPE sweep aimed at breaking the two-flag carrier: Tuple, Dict, FiniteSet, Interval, Matrix, MatrixSymbol, ZeroMatrix, Identity, MatAdd cancelling to 0, Quaternion(0,0,0,0), Eq/Ne/And/Not, Piecewise, Sum(0,..), Sum over empty range, Integral(0,x), Derivative, Order, Lambda, Poly, Dummy, Range, EmptySequence, Union, ImageSet, nan, zoo, +/-oo, I, S.true/S.false, Symbol(zero=True), Float(0)/Float(-0.0)/Float(0,200). 33/33 MATCH: bool(coeff) == (mzero==0) in every case. is_zero only ever returned bool or None (no fuzzy third value that could desync the 0/1 flag).
4. EXCLUDED-STATE probe (the strongest form of "spec too strong": the precondition Implies(lit0==1, mzero==1) would be an unsound assumption if a real coefficient could occupy (lit0=1, mzero=0), since Nagini would then be allowed to assume something false of the real domain). I hunted for an Expr with (e == 0) True but e.is_zero not True across Float at several precisions, Float(-0.0), Rational(0,n), Zero, Add(), Mul(0,3), Pow(0,2), AccumBounds(0,0), sympify('-0'): ZERO hits. The invariant is a real SymPy fact (Integer(0).is_zero is True), not an over-constraint.
5. OVER-CLAIM probe on undecidable zeros, the subtlest way this spec could be too strong. The docstring prose says "denotes zero", which read loosely would cover expressions that are mathematically zero but that SymPy cannot decide. I built such inputs (cos(x)**2+sin(x)**2-1, Mul(0,x,evaluate=False), tan(x)-sin(x)/cos(x), (`x**2`-1)/(x-1)-(x+1)) -- all have simplify(ex)==0 True but is_zero None. Under the LOOSE prose reading the model would predict falsy/len 0 and DIVERGE from the real code (which returns truthy/len 1) on 4 of 5 inputs. Under the PINNED mapping.md bridge (mzero==1 iff is_zero is True) the model predicts truthy/len 1 and matches the real callee on 5 of 5. Since mapping.md sec.2 and conformance_check.py's facets() both pin mzero to `is_zero is True` -- not to mathematical truth -- the spec tracks the real code exactly. This is the one place a divergence could have lived and it does not; the prose is loose but the binding is tight and the binding is what the proof consumes.
6. Poly-level consequence verified live on the patched tree: Poly(sqrt(2)-sqrt(2), x, EX) == Poly(0,x,domain='EX'); zero-denoting coeff -> dup_strip -> [] (len 0 == model), nonzero coeff -> len 1 == model.

NOT-A-DEFECT (checked and dismissed, recording so the next auditor does not re-raise it): for a non-Expr payload that escapes sympify (EX.Expression([1,2]) or EX.Expression(None), whose.ex is a raw list/None), base returns True while the patched tree raises AttributeError ('list' object has no attribute 'is_zero'). This is a delta the gold patch itself introduces, so per the lane rule it cannot be scored as model unfaithfulness; it is also outside the carrier (a legitimate EX coefficient is a sympified Expr, and the (0,0)/(0,1)/(1,1) realizable-state analysis in conformance_check.py is correct for those).

CROSS-CHECKS supporting that the spec has real discriminating content (so FAITHFUL is not a rubber-stamp of a vacuous spec): model.py verifies (Verification successful, 9.69s, pinned verifier). model_prepatch.py (`return c.lit0 == 0`, the structural pre-patch test) shares the exact spec (adversary same-spec exit 0; impl-region diff is the single line mzero->lit0) and FAILS with exactly 'Postcondition of coeff_truthy might not hold. Assertion (Result() == (c.mzero == 0)) might not hold.' F2P confirmed in both directions with the real test_patch applied: base+test = 1 failed (AssertionError), patched+test = 1 passed.

**CONCLUSION:** no input exists on which the modeled functions disagree with the real post-patch callees, over ~350k executed real coefficients plus targeted exotic/excluded-state/undecidable-zero adversarial batteries. The spec is not too strong and does not drift from repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE.** No relaxation is claimed in this bundle, so this is a straight NO-LEAKAGE/LEAKAGE question with no inherited disposition. I verified that myself rather than taking it on trust: `meta.json` has no `relaxed_leakage` key (live key dump = additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version), and `find -iname '*RELAX*'` over the whole instance dir returns nothing. Note the task prompt's file list (patch.diff, refinement.md, mapping.md...) does not match the bundle: there is no patch.diff inside nagini/; the gold patch lives one level up at benchmark-verified/sympy__sympy-20428/patch.diff, and meta.patch_diff is only the string 'gold patch verbatim (applies cleanly at base_commit)'. I used the parent-dir patch.diff and instance.json as the ground truth.

**GOLD EDIT.** sympy/polys/domains/expressiondomain.py:123, inside `Expression.__bool__`: `return f.ex != 0` -> `return not f.ex.is_zero`. One hunk, one file (meta.changed_files == that one file, additional_change_sites == []). The discriminator is therefore: truthiness keyed on MATHEMATICAL zeroness rather than STRUCTURAL inequality with the bare `0` literal.

SPEC VIEW MEASURED, NOT ASSUMED. I rendered it live with markers.spec_view(model.py, nagini backend): sha256 = 3a325eb6bd3c0e22178b0751351cb623b8421f531535730a95ff40bd4eb7055d, matching gates.G-HYGIENE.data.region_hashes.spec_view exactly, so the view I judged is the view the recorded gate judged. Both impl regions elide to the placeholder; what a consumer sees is the docstrings, the Coeff constructor, and the Requires/Ensures of coeff_truthy and strip_constant_len.

LEAK SCAN (my own greps over the rendered view, not the stored gate). Zero hits for: is_zero, `__bool__`, expressiondomain, densebasic, dup_strip, clear_denoms, Poly, DMP, EX(, f.ex, '!= 0', Integer, rep. Zero hits for narration vocabulary: fix/fixed/bug/patch/prepatch/previously/no longer/used to/instead of/regression/issue/copy. The only vocabulary hits are innocuous: 'sympy' appears once as the instance id in the docstring title (an identifier the consumer already has), 'expression' as a generic English noun, 'before' inside 'diverges before returning', and 'correct' only inside 'total-correctness obligation' -- a MustTerminate justification, which is the known G-LEAK false-positive shape and carries no edit information. The view names no file, no changed function, no property, and neither side of the edit. I also re-ran leakage.screen(model.py, nagini, instance.patch, instance.problem_statement, instance.test_patch) on live code: passed=True, hard_failures=[], warnings=[] -- reproducing the recorded G-LEAK 'spec view clean' rather than inheriting it.

WHAT THE VIEW DOES SAY, AND WHERE IT COMES FROM. The view states abstractly (a) a coefficient has a structural shape and a mathematical value which can disagree, (b) truthiness must track the mathematical value, (c) a constant poly's stored list is empty exactly when its coefficient denotes zero. Every one of those is disclosed MORE concretely in the public problem_statement, which prints `bad_poly.is_zero` False beside `bad_poly.as_expr().is_zero` True (the structural/mathematical split, naming is_zero outright) and `bad_poly.rep == DMP([EX(0)], EX, None)` 'which should be' `DMP([], EX, None)` (the strip-to-empty consequence). hints_text is empty, so nothing here depends on it.

I confirmed the derivation is real, not rhetorical: in a fresh worktree at base_commit c0e85160 (, clone from the upstream repository; all work in /tmp, bundle untouched) I built the F2P test's exact expression and measured the discriminating coefficient -- c.ex == 0 is False (lit0=0) while c.ex.is_zero is True (mzero=1), bool(c) is True pre-patch so dup_strip keeps [c] and f == Poly(0,x,domain='EX') is False. The statement's demand rep == [] plus dup_strip's `if not f or f[0]` guard forces bool(c) False on a coefficient whose only False-valued predicate is the is_zero one; the bare literal case (is_zero True, != 0 False) shows the two tests agree there, which is exactly the view's Implies(lit0==1, mzero==1). So the spec view's content is a problem_statement-derivable restatement, and it is strictly less specific than the statement.

LOAD-BEARING TEST (the strip-the-narration control, run by me). I built naked_gold.py: model.py with the module docstring, the Coeff class docstring and every non-marker comment deleted, leaving only Requires/Ensures and impls. It VERIFIES (nagini_verify.sh exit 0, 9.92s). I then flipped only the impl to the pre-patch body `return c.lit0 == 0` (naked_pre.py): FAILS with 'Postcondition of coeff_truthy might not hold. Assertion (Result() == (c.mzero == 0)) might not hold.' So the discriminating force lives entirely in the formal postcondition Result() == (c.mzero == 0); the prose is removable narration adding no discriminating information. That is the opposite of the pattern that would force a relaxation -- no clause had to be removed, and none was needed.

CORE GATES RE-RUN LIVE, not read off meta. nagini_verify.sh on the bundle model.py: 'Verification successful' exit 0 (G-VERIFY/G-GOLD). nagini_verify.sh on model_prepatch.py: exit 1, failing exactly Result() == (c.mzero == 0) (G-DIFF sound, and the prepatch differs from gold in one line only, `c.mzero == 0` -> `c.lit0 == 0`). adversary same-spec on both gold and prepatch copies: 'SAME' exit 0 (the spec region really is frozen and byte-identical). axiom_check.py against the real repo with patch.diff applied: exit 0, 'deep model == real ExpressionDomain.Expression.`__bool__` over 11 non-zero, 3 literal-zero, 5 denoting-zero coefficients + the exact issue clear_denoms coefficient'; reverted to base it FAILS on 'Poly(<zero expr>, x) should equal Poly(0,x,EX)' -- so G-AX genuinely discriminates and the mzero facet is validated against real Expr.is_zero, not asserted. conformance_check.py: exit 0, 100032 checked / 0 disagreements, facet coverage including 20414 samples of the discriminating (lit0=0, mzero=1) state.

**REVIEWER-DIRECTED TEXT.** Nothing in the bundle addresses me or tells me what to record. leakage.reviewer_directed returned [] on all eleven files (model.py, model_prepatch.py, mapping.md, refinement.md, properties.py, axiom_check.py, conformance_check.py, meta.json, pbt_result.json, verdict.md, plus one transient build artifact), and my own greps for submit/instruct/'honest verdict'/'record as' found only generated records. verdict.md does carry a prior G-PANEL-3 'NO-LEAKAGE' note with reasoning very close to mine, but I treated it as a log of a past run, not as an instruction: every measurement above is mine, re-run on live code, and I reached the verdict before reading it. Worth flagging as a hygiene observation rather than a finding: a bundle shipping a prior panel's full reasoning to the next panel is an anchoring hazard even when nothing in it is phrased as a directive.

ONE DISCREPANCY, non-leakage and benign. meta.json's TOP-LEVEL region_hashes disagrees with both the live computation and gates.G-HYGIENE.data.region_hashes on two entries: pre-conditions (stored 3279f6e9... vs live/G-HYGIENE a52aac36...) and spec_view (stored 0ba21f39... vs live/G-HYGIENE 3a325eb6...); axioms, pure, post-conditions and impl agree everywhere. The file itself is unmodified relative to what the gates saw -- sha256(model.py) = 34f8d003... matches gates.G-EQ.sources.model.py exactly -- and grep shows no code reads meta['region_hashes'] (only hygiene.py writes region_hashes into its own gate data), so this is a stale top-level snapshot from a pre-final revision of the pre-condition comments, not tampering and not a leak. It does not touch the leakage question: the authority for the spec view is the live render, which matches G-HYGIENE.

**VERDICT:** NO-LEAKAGE. The spec view is byte-frozen and verified so, names no file / function / property / either side of the gold edit, states only facts the public problem_statement discloses more concretely (with hints_text empty and unused), and its prose is provably not load-bearing -- stripped of all narration the model still verifies and still rejects the pre-patch impl. Every gate the judgement leans on (verify, G-DIFF, same-spec, G-AX with its base-commit negative control, G-CONF, G-LEAK screen) I re-ran live and each passes.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
