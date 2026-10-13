# P2 adversarial audit — sympy__sympy-13878

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_13.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,9 +211,6 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
     return CF_INTEGRAL
     # impl-end
 
@@ -281,8 +278,5 @@
                     and not closed_form_returns, not Result()))
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_returns
     return quadrature_returns
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,9 +211,8 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
+    if has_closed_form(fam):
+        return closed_form_for_family(fam, closed_form_returns)
     return CF_INTEGRAL
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,10 +211,7 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
-    return CF_INTEGRAL
+    return CF_ARCSIN
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,9 +211,11 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
+    if default_query and has_closed_form(fam) and closed_form_returns:
+        n = 0
+        while n >= 0:
+            Invariant(n >= 0)
+            n = n + 1
     return CF_INTEGRAL
     # impl-end
 
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,10 +211,7 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
-    return CF_INTEGRAL
+    return closed_form_for(fam, default_query)
     # impl-end
 
 
@@ -281,8 +278,6 @@
                     and not closed_form_returns, not Result()))
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_returns
-    return quadrature_returns
+    return query_delivers(fam, default_query, quadrature_returns,
+                          closed_form_returns)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,6 +211,12 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
+    if not (default_query and has_closed_form(fam)):
+        if not quadrature_returns:
+            n = 0
+            while n >= 0:
+                Invariant(n >= 0)
+                n = n + 1
     if default_query:
         if has_closed_form(fam):
             return closed_form_for_family(fam, closed_form_returns)
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,6 +241,11 @@
     Ensures(Result() != CF_INTEGRAL)
     # post-conditions-end
     # impl-start
+    if not closed_form_returns:
+        n = 0
+        while n >= 0:
+            Invariant(n >= 0)
+            n = n + 1
     return CF_ARCSIN
     # impl-end
 
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -213,7 +213,7 @@
     # impl-start
     if default_query:
         if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
+            return closed_form_for_family(fam, True)
     return CF_INTEGRAL
     # impl-end
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -213,7 +213,7 @@
     # impl-start
     if default_query:
         if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
+            return closed_form_for_family(fam, quadrature_returns)
     return CF_INTEGRAL
     # impl-end
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,8 +281,5 @@
                     and not closed_form_returns, not Result()))
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_returns
-    return quadrature_returns
+    return closed_form_returns
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -281,6 +281,11 @@
                     and not closed_form_returns, not Result()))
     # post-conditions-end
     # impl-start
+    if default_query and has_closed_form(fam) and not closed_form_returns:
+        n = 0
+        while n >= 0:
+            Invariant(n >= 0)
+            n = n + 1
     if default_query:
         if has_closed_form(fam):
             return closed_form_returns
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -213,7 +213,8 @@
     # impl-start
     if default_query:
         if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
+            if closed_form_returns:
+                return closed_form_for_family(fam, closed_form_returns)
     return CF_INTEGRAL
     # impl-end
 
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,6 +211,12 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
+    if not query_delivers(fam, default_query, quadrature_returns,
+                          closed_form_returns):
+        n = 0
+        while n >= 0:
+            Invariant(n >= 0)
+            n = n + 1
     if default_query:
         if has_closed_form(fam):
             return closed_form_for_family(fam, closed_form_returns)
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -241,6 +241,8 @@
     Ensures(Result() != CF_INTEGRAL)
     # post-conditions-end
     # impl-start
+    if not closed_form_returns:
+        return CF_INTEGRAL
     return CF_ARCSIN
     # impl-end
 
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,6 +211,11 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
+    if default_query and has_closed_form(fam) and not quadrature_returns:
+        n = 0
+        while n >= 0:
+            Invariant(n >= 0)
+            n = n + 1
     if default_query:
         if has_closed_form(fam):
             return closed_form_for_family(fam, closed_form_returns)
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -211,10 +211,13 @@
     # back. Those two facts govern delivery only.)
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_for_family(fam, closed_form_returns)
-    return CF_INTEGRAL
+    if not (default_query and has_closed_form(fam)):
+        if not quadrature_returns:
+            n = 0
+            while n >= 0:
+                Invariant(n >= 0)
+                n = n + 1
+    return closed_form_for(fam, default_query)
     # impl-end
 
 
@@ -241,6 +244,11 @@
     Ensures(Result() != CF_INTEGRAL)
     # post-conditions-end
     # impl-start
+    if not closed_form_returns:
+        n = 0
+        while n >= 0:
+            Invariant(n >= 0)
+            n = n + 1
     return CF_ARCSIN
     # impl-end
 
@@ -281,8 +289,6 @@
                     and not closed_form_returns, not Result()))
     # post-conditions-end
     # impl-start
-    if default_query:
-        if has_closed_form(fam):
-            return closed_form_returns
-    return quadrature_returns
+    return query_delivers(fam, default_query, quadrature_returns,
+                          closed_form_returns)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 16 same-spec attacks (all `same-spec` exit 0; verified mechanically that outside the three `# impl-start/# impl-end` regions every attack is BYTE-IDENTICAL to model.py, so axioms/@Pure/Requires/Ensures are untouched and all 3 impl regions are present). 10 REJECTED (weakness exit 2), 6 CANDIDATE (exit 0). For EVERY one of the 6 candidates the faithful refined patch was materialized at base_commit 7b127bdf71a36d85216315f80c1b54d22b060818, checked with `git apply --check` in a base_commit worktree (all exit 0), and RUN through the official harness (swebench_unified.harness.run_resolve, timeout 1800): ALL 6 RESOLVED (resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS test_arcsin 1/1, PASS_TO_PASS 19/19, PASS_TO_FAIL and FAIL_TO_FAIL empty). Positive control = unmodified model.py at pos_control.py: `bash scripts/nagini_verify.sh` -> exit 0, "Verification successful", 8.92s.

**COMMANDS.** Per attack N: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-13878 atk_N.py` then `python -m swebench_unified.adversary weakness nagini sympy__sympy-13878 atk_N.py` (logs w_N.log). Resolve: `run_resolve("sympy__sympy-13878", open(atk_N.diff).read(), timeout=1800)` (logs res_N.log). Weakness/resolve runs were scheduled 3-at-a-time as background jobs (runw.sh / runw2.sh / runres.sh); schedule only, every attack fully verified.

REJECTED (10) -- each a genuine spec violation, confirmed by reading the verifier's own error, not a parse/import failure: atk_1 PREPATCH BUG REPRODUCED on BOTH observables (== model_prepatch.py): cdf_result `return CF_INTEGRAL`, query_arrives `return quadrature_returns`. Rejected with exactly the two postconditions refinement.md's G-DIFF block quotes: "Postcondition of cdf_result might not hold. Assertion (Result() == closed_form_for(fam, default_query))" AND "Postcondition of query_arrives might not hold.

Assertion (Result() == query_delivers(...))". atk_2 partial-domain on the OPTION facet (drop the default_query guard) -> P1/P5. atk_3 boundary/constant: always CF_ARCSIN -> P1/P4/P5. atk_4 control-flow-effect ON THE F2P CELL: diverge on the closed-form route where closed_form_returns HOLDS. "Obligation leak check failed" -- the obligation is live exactly on the cell test_arcsin exercises, so scoping the measure did NOT reopen the G-PANEL-1 vacuity hole. atk_9 A-LEG CROSS-FACT SMUGGLE: thread the INTEGRATING route's fact into the closed-form supplier's guard (`closed_form_for_family(fam, quadrature_returns)`).

Rejected -- the closed-form route's callee may not have its delivery gated on the integration. atk_10 route-isolation break on the delivery VALUE (read closed_form_returns on every route) -> P9. atk_11 the delivery OBSERVABLE itself diverges on the withheld region -> query_arrives' UNCONDITIONAL MustTerminate(1) leaks. atk_12 the result FORM reads a DELIVERY fact -> P1 pins the form to (fam, default_query) ALONE. atk_14 UNDER-claim the FORM inside the withheld region (supplier returns CF_INTEGRAL when refused) -> P6. Confirms the withheld region withholds DELIVERY only, never FORM. atk_15 A-LEG WIDENING, sharpest direction: hang the CLOSED-FORM route on `not quadrature_returns` -- i.e. gate one route's obligation on the OTHER route's fact, on the F2P cell where the real query answers. "Obligation leak check failed" -> the per-route split is NOT leaky in the direction that matters.

CANDIDATES (6) -> ALL RESOLVED, so none is a counterexample: atk_5 GROUNDED-ORACLE ECHO probe (all three regions answer via the @Pure oracles). NOT an ungrounded-oracle weakness: closed_form_for / query_delivers are fully unfolded over the args, so this is the honest cheapest CORRECT impl. Faithful patch = the gold patch verbatim. RESOLVED. atk_8 A-LEG FACT-THREADING, over-claim direction: pass a CONSTANT True for the fact the supplier is meant to OBSERVE (`closed_form_for_family(fam, True)`). Behaviourally identical to gold (it only strengthens the callee's guard, changing no form and no arrival), so its faithful patch is the gold patch. RESOLVED. atk_6 WITHHELD-REGION DIVERGENCE, INTEGRATING route: the dispatch's integral branch loops forever instead of raising.

Faithful patch edits crv.py:220 (`try: return self.compute_cdf(**kwargs)(x) except Exception: while True: pass`). RESOLVED. atk_7 WITHHELD-REGION DIVERGENCE, CLOSED-FORM route, inside the SUPPLIER: the added `_cdf` loops forever instead of raising. Faithful patch = gold + that edit to ArcsinDistribution.`_cdf`. RESOLVED. atk_13 BOTH withheld regions at once, guarded by the exact per-route split `query_delivers` -- the widest divergence the guard admits. Faithful patch = both legs. RESOLVED. atk_16 the union of every admitted freedom at once: oracle echo in query_arrives + supplier divergence + integrating-route divergence. Faithful patch = both legs. RESOLVED.

WHY the divergence candidates resolve -- MEASURED, not argued. I instrumented SingleContinuousDistribution.cdf inside the official image (swebench/sweb.eval.x86_64.sympy_1776_sympy-13878) with gold + the graded test_patch applied and ran all 63 test functions of the graded file sympy/stats/tests/test_continuous_rv.py (the eval script runs the WHOLE file, so a hang anywhere would time the run out): 77 cdf deliveries, cff_refused=0, quad_refused=0. The two withheld-delivery regions are reached ZERO times by the graded suite, so a patch that hangs there instead of raising is behaviourally indistinguishable under G-RESOLVE. This is the disclosed RESIDUAL RISK, and it is faithful scoping rather than a hole: the real callee hands nothing back on those regions too (measured, below), the result FORM stays pinned there (atk_12/atk_14 rejected), and query_arrives pins the delivery verdict there as a VALUE in both directions per route (atk_10/atk_15 rejected). verify does not pin the failure MODE (hang vs raise) on an untested region -- correctly, since the spec's Requires admits it and no test observes it.

A-LEG AUDIT (the assignment's focus). refinement.md has 8 legs A0-A7 tagged R (A0,A1,A4,A5,A6,A7), R+I (A2), A-reference (A3). NO kind-3, NO A-consumed -- consistent with an empty `axioms` region and meta.json `"axioms": []`, so the proof consumes no @ContractOnly Ensures and there is no consumed-axiom trust point. I re-derived each A-leg's correspondence against the REAL post-patch callee in the official image (probe.py): A3 (the only A-reference): `cdf(Arcsin('x',a,b))(x)` == Piecewise((0, a > x), (`2*asin`(sqrt((-a+x)/(-a+b)))/pi, b >= x), (1, True)) -- EXACTLY the Piecewise the F2P test asserts. Confirmed equal.

A5 (`closed_form_returns` = the `_cdf` CALL's own return, NOT the "both comparisons stand" proxy): confirmed on 9 instantiations that the facet == the real dispatch's delivery on EVERY row, and that the mapping.md/refinement.md separating witness is real -- ArcsinDistribution(0, oo) with query point `I*sr` has comparisons_stand=True but closed_form_returns=False (the Piecewise ASSEMBLY refuses), while (0,1) with the same query point delivers. So carrying the call's return rather than the narrower proxy is not editorial: the two predicates genuinely differ, and the model carries the one that matches delivery. A6/A7's per-route split rests on this and holds. A4: the option-carrying route delivers, and risch=True / heurisch=True do not -- matching mapping.md's non-delivery table.

A2/A0/A1: crv.py:214-220 is unchanged by the patch and is a len(kwargs) guard + `_cdf` probe + return, structurally identical to the model's nested conditionals. refinement.md §B's scope claim (the other families' `_cdf` hunks are not separately-tested behaviour) is LOAD-BEARING for the single-prepatch-model design, so I tested it: a MINIMAL patch adding ONLY ArcsinDistribution.`_cdf` (minB.diff, 20 lines) RESOLVES (resolved=True, F2P 1/1, P2P 19/19). §B is correct -- the arcsin hunk alone carries resolution. I also confirmed independently that NO graded P2P test mentions cdf at all.

**Evidence complete:** 16/16 attacks reached a verdict (no timeouts, no host-cap inconclusives), 6/6 candidate patches ran run_resolve to completion, 7/7 patches (6 candidates + minB) pass `git apply --check` at base_commit, positive control verifies, prepatch bug reproduced and rejected on both observables. No verifying wrong impl found; verify ⇒ correct holds for this spec on every attack I could construct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_13.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 16 same-spec attacks (all `same-spec` exit 0; verified mechanically that outside the three `# impl-start/# impl-end` regions every attack is BYTE-IDENTICAL to model.py, so axioms/@Pure/Requires/Ensures are untouched and all 3 impl regions are present). 10 REJECTED (weakness exit 2), 6 CANDIDATE (exit 0). For EVERY one of the 6 candidates the faithful refined patch was materialized at base_commit 7b127bdf71a36d85216315f80c1b54d22b060818, checked with `git apply --check` in a base_commit worktree (all exit 0), and RUN through the official harness (swebench_unified.harness.run_resolve, timeout 1800): ALL 6 RESOLVED (resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS test_arcsin 1/1, PASS_TO_PASS 19/19, PASS_TO_FAIL and FAIL_TO_FAIL empty). Positive control = unmodified model.py at pos_control.py: `bash scripts/nagini_verify.sh` -> exit 0, "Verification successful", 8.92s.

**COMMANDS.** Per attack N: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-13878 atk_N.py` then `python -m swebench_unified.adversary weakness nagini sympy__sympy-13878 atk_N.py` (logs w_N.log). Resolve: `run_resolve("sympy__sympy-13878", open(atk_N.diff).read(), timeout=1800)` (logs res_N.log). Weakness/resolve runs were scheduled 3-at-a-time as background jobs (runw.sh / runw2.sh / runres.sh); schedule only, every attack fully verified.

REJECTED (10) -- each a genuine spec violation, confirmed by reading the verifier's own error, not a parse/import failure: atk_1 PREPATCH BUG REPRODUCED on BOTH observables (== model_prepatch.py): cdf_result `return CF_INTEGRAL`, query_arrives `return quadrature_returns`. Rejected with exactly the two postconditions refinement.md's G-DIFF block quotes: "Postcondition of cdf_result might not hold. Assertion (Result() == closed_form_for(fam, default_query))" AND "Postcondition of query_arrives might not hold.

Assertion (Result() == query_delivers(...))". atk_2 partial-domain on the OPTION facet (drop the default_query guard) -> P1/P5. atk_3 boundary/constant: always CF_ARCSIN -> P1/P4/P5. atk_4 control-flow-effect ON THE F2P CELL: diverge on the closed-form route where closed_form_returns HOLDS. "Obligation leak check failed" -- the obligation is live exactly on the cell test_arcsin exercises, so scoping the measure did NOT reopen the G-PANEL-1 vacuity hole. atk_9 A-LEG CROSS-FACT SMUGGLE: thread the INTEGRATING route's fact into the closed-form supplier's guard (`closed_form_for_family(fam, quadrature_returns)`).

Rejected -- the closed-form route's callee may not have its delivery gated on the integration. atk_10 route-isolation break on the delivery VALUE (read closed_form_returns on every route) -> P9. atk_11 the delivery OBSERVABLE itself diverges on the withheld region -> query_arrives' UNCONDITIONAL MustTerminate(1) leaks. atk_12 the result FORM reads a DELIVERY fact -> P1 pins the form to (fam, default_query) ALONE. atk_14 UNDER-claim the FORM inside the withheld region (supplier returns CF_INTEGRAL when refused) -> P6. Confirms the withheld region withholds DELIVERY only, never FORM. atk_15 A-LEG WIDENING, sharpest direction: hang the CLOSED-FORM route on `not quadrature_returns` -- i.e. gate one route's obligation on the OTHER route's fact, on the F2P cell where the real query answers. "Obligation leak check failed" -> the per-route split is NOT leaky in the direction that matters.

CANDIDATES (6) -> ALL RESOLVED, so none is a counterexample: atk_5 GROUNDED-ORACLE ECHO probe (all three regions answer via the @Pure oracles). NOT an ungrounded-oracle weakness: closed_form_for / query_delivers are fully unfolded over the args, so this is the honest cheapest CORRECT impl. Faithful patch = the gold patch verbatim. RESOLVED. atk_8 A-LEG FACT-THREADING, over-claim direction: pass a CONSTANT True for the fact the supplier is meant to OBSERVE (`closed_form_for_family(fam, True)`). Behaviourally identical to gold (it only strengthens the callee's guard, changing no form and no arrival), so its faithful patch is the gold patch. RESOLVED. atk_6 WITHHELD-REGION DIVERGENCE, INTEGRATING route: the dispatch's integral branch loops forever instead of raising.

Faithful patch edits crv.py:220 (`try: return self.compute_cdf(**kwargs)(x) except Exception: while True: pass`). RESOLVED. atk_7 WITHHELD-REGION DIVERGENCE, CLOSED-FORM route, inside the SUPPLIER: the added `_cdf` loops forever instead of raising. Faithful patch = gold + that edit to ArcsinDistribution.`_cdf`. RESOLVED. atk_13 BOTH withheld regions at once, guarded by the exact per-route split `query_delivers` -- the widest divergence the guard admits. Faithful patch = both legs. RESOLVED. atk_16 the union of every admitted freedom at once: oracle echo in query_arrives + supplier divergence + integrating-route divergence. Faithful patch = both legs. RESOLVED.

WHY the divergence candidates resolve -- MEASURED, not argued. I instrumented SingleContinuousDistribution.cdf inside the official image (swebench/sweb.eval.x86_64.sympy_1776_sympy-13878) with gold + the graded test_patch applied and ran all 63 test functions of the graded file sympy/stats/tests/test_continuous_rv.py (the eval script runs the WHOLE file, so a hang anywhere would time the run out): 77 cdf deliveries, cff_refused=0, quad_refused=0. The two withheld-delivery regions are reached ZERO times by the graded suite, so a patch that hangs there instead of raising is behaviourally indistinguishable under G-RESOLVE. This is the disclosed RESIDUAL RISK, and it is faithful scoping rather than a hole: the real callee hands nothing back on those regions too (measured, below), the result FORM stays pinned there (atk_12/atk_14 rejected), and query_arrives pins the delivery verdict there as a VALUE in both directions per route (atk_10/atk_15 rejected). verify does not pin the failure MODE (hang vs raise) on an untested region -- correctly, since the spec's Requires admits it and no test observes it.

A-LEG AUDIT (the assignment's focus). refinement.md has 8 legs A0-A7 tagged R (A0,A1,A4,A5,A6,A7), R+I (A2), A-reference (A3). NO kind-3, NO A-consumed -- consistent with an empty `axioms` region and meta.json `"axioms": []`, so the proof consumes no @ContractOnly Ensures and there is no consumed-axiom trust point. I re-derived each A-leg's correspondence against the REAL post-patch callee in the official image (probe.py): A3 (the only A-reference): `cdf(Arcsin('x',a,b))(x)` == Piecewise((0, a > x), (`2*asin`(sqrt((-a+x)/(-a+b)))/pi, b >= x), (1, True)) -- EXACTLY the Piecewise the F2P test asserts. Confirmed equal.

A5 (`closed_form_returns` = the `_cdf` CALL's own return, NOT the "both comparisons stand" proxy): confirmed on 9 instantiations that the facet == the real dispatch's delivery on EVERY row, and that the mapping.md/refinement.md separating witness is real -- ArcsinDistribution(0, oo) with query point `I*sr` has comparisons_stand=True but closed_form_returns=False (the Piecewise ASSEMBLY refuses), while (0,1) with the same query point delivers. So carrying the call's return rather than the narrower proxy is not editorial: the two predicates genuinely differ, and the model carries the one that matches delivery. A6/A7's per-route split rests on this and holds. A4: the option-carrying route delivers, and risch=True / heurisch=True do not -- matching mapping.md's non-delivery table.

A2/A0/A1: crv.py:214-220 is unchanged by the patch and is a len(kwargs) guard + `_cdf` probe + return, structurally identical to the model's nested conditionals. refinement.md §B's scope claim (the other families' `_cdf` hunks are not separately-tested behaviour) is LOAD-BEARING for the single-prepatch-model design, so I tested it: a MINIMAL patch adding ONLY ArcsinDistribution.`_cdf` (minB.diff, 20 lines) RESOLVES (resolved=True, F2P 1/1, P2P 19/19). §B is correct -- the arcsin hunk alone carries resolution. I also confirmed independently that NO graded P2P test mentions cdf at all.

**Evidence complete:** 16/16 attacks reached a verdict (no timeouts, no host-cap inconclusives), 6/6 candidate patches ran run_resolve to completion, 7/7 patches (6 candidates + minB) pass `git apply --check` at base_commit, positive control verifies, prepatch bug reproduced and rejected on both observables. No verifying wrong impl found; verify ⇒ correct holds for this spec on every attack I could construct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE.**  (sympy_sympy.git worktree at base_commit 7b127bdf71a36d85216315f80c1b54d22b060818) for source reading, and the pinned instance image swebench/sweb.eval.x86_64.sympy_1776_sympy-13878 via docker_exec.run_in_container(apply_gold=True, patch.diff) for all behavioural measurement — i.e. the POST-PATCH repo, as the role requires.

**MODELLED CALLEE.** SingleContinuousDistribution.cdf (sympy/stats/crv.py:214-220), read from source in-container: `if len(kwargs)==0: cdf=self._cdf(x); if cdf is not None: return cdf` / `return self.compute_cdf(**kwargs)(x)`. Structural facts I verified rather than assumed, because each one closes an otherwise-open route-flip attack:
  * crv.py is untouched by patch.diff (patch only edits crv_types.py).
  * Enumerated all 38 SingleContinuousDistribution subclasses in crv_types.py: `overrides 'cdf' itself: []` — NONE overrides the dispatch, only `_cdf`. So the control flow the model spells out is the sole route selector; no subclass can smuggle in a third route.
  * Base `_cdf` is literally `return None` (crv.py:211-212), so FAM_OTHER's route choice is unconditional.
  * ArcsinDistribution.`_cdf` never returns None: 70/70 (10 bound-pairs × 7 query points) returned a non-None value, 0 raises. So has_closed_form(FAM_ARCSIN)==True is unconditional in the real repo — the route flip that would break `Ensures(Implies(default_query and fam==FAM_ARCSIN, Result()==CF_ARCSIN))` is not available.

ATTACK 1 — FORM over-claim on the closed-form route. Could a default FAM_ARCSIN query hand back something other than the family's supplied closed form (an Integral ⇒ CF_INTEGRAL, contradicting Result()==CF_ARCSIN and Result()!=CF_INTEGRAL)? Swept 20 bound-pairs × 22 query points = 440 instantiations (real / free-symbolic / real-symbolic / degenerate (1,1),(0,0) / reversed (3,0) / infinite (-oo,oo),(0,oo),(oo,oo) / non-real (I,1),(0,2I),(2+3I,5) / nan / zoo bounds; query points x, xr, xp, integers, rationals, ±oo, zoo, nan, I, `I*sr`, sr+`I*sr`, sqrt2, pi, exp(xr)). Diffed the dispatch result against `type(dist)._cdf(dist,q)` by `==` with srepr fallback: 0 form mismatches, and dispatch-returned-an-Integral count = 0. Route identity is exact.

ATTACK 2 — FORM over-claim on the integrating route. Could an option-carrying FAM_ARCSIN query, or a FAM_OTHER default query, produce the arcsin closed form (making Ensures(Implies(not has_closed_form(fam), Result()==CF_INTEGRAL)) / Implies(not default_query, ...) wrong)? 1755 instantiations: 15 FAM_OTHER families (Benini, Rayleigh, WignerSemicircle, Chi, Trapezoidal, QuadraticU, RaisedCosine, VonMises, ShiftedGompertz, and ContinuousDistributionHandmade over Interval / Union / FiniteSet / EmptySet / an exponential density / the arcsin density itself) plus 5 arcsin dists, × 10 option sets (conds=none/separate/piecewise, meijerg=T/F, manual, risch, heurisch) × 9 query points.

I flagged 23 results containing `asin` (all WignerSemicircle, whose integral genuinely evaluates to a closed form with asin in it) — REFUTED as my own value-proxy artifact: CF_INTEGRAL abstracts 'the form the integrating route produces' (mapping.md §2: 'the result of compute_cdf(**kwargs)(x)'), NOT 'an object containing an unevaluated Integral'. Those results ARE compute_cdf()(x); route identity confirmed srepr-identical. The decisive collision test: I built ContinuousDistributionHandmade with the EXACT arcsin density 1/(`pi*sqrt`(z*(3-z))) on Interval(0,3) — the hardest case for code collision — and its default query returned `Piecewise((Integral(...)/pi, x>=0),(0,True))`, srepr-identical to its own compute_cdf()(x) and NOT equal to the arcsin family's supplied closed form. CF_ARCSIN and CF_INTEGRAL do not collide.

ATTACK 3 — DELIVERY over-claim (the sharpest surface: Requires(Implies(query_delivers(...), MustTerminate(2))) demands delivery, so an over-strong guard is a faithfulness break). Closed-form route: over the same 440 instantiations I observed `closed_form_returns` on that route's OWN callee (ArcsinDistribution.`_cdf` called directly, NOT through the dispatch, so the facet is probed and not echoed) and diffed against the real dispatch's arrival as an EQUALITY in both directions under a 25s alarm: 0 mismatches, 0 hangs. Integrating route: same equality against `compute_cdf(**op)(q)` over the 1755 instantiations — 3 apparent mismatches, all REFUTED:

  (i) A priori impossible: crv.py:220 IS `return self.compute_cdf(**kwargs)(x)`, so on that route the dispatch's delivery is definitionally that call's delivery. Any observed difference must be an artifact.

  (ii) Confirmed empirically. All 3 were arc(a,b) with conds='separate'/'piecewise'/{conds:none,meijerg:False}. Re-measured with observation order REVERSED and a 300s budget: all 3 came back dispatch=ok AND compute_cdf=ok, srepr-equal. `compute_cdf` is @cacheit-memoized, so two sequential observations share a cache — whichever is measured first eats the cold-cache cost and can trip the alarm while the second gets the memo. With clear_cache() between, the artifact flips direction (conds='piecewise': compute_cdf ok@151.7s vs dispatch hang@300s), which is the signature of a slow-but-terminating integration racing a wall-clock alarm, not a semantic divergence. `quadrature_returns` is True on these and the query does deliver — consistent with the spec.

  (iii) One clear-cache row (op={}, i.e. the DEFAULT arcsin query) read compute_cdf=hang / dispatch=ok@0.0s. That is not a divergence but the patch's whole point: the default query takes the closed-form route, so quadrature_returns is not the fact that governs it. The model gets this exactly right — query_delivers reads closed_form_returns ALONE there, and closed_form_arrives does not even take quadrature_returns as a parameter.

**WHY THE GUARD CANNOT OVER-CLAIM STRUCTURALLY.** Both delivery facts are carried as INPUTS observed on the route's own callee, not reconstructed: closed_form_returns is by definition 'the `_cdf` call returns' and quadrature_returns 'the integration comes back'. So on every input where query_delivers holds, the real route terminated by construction of the fact. Combined with the per-route split (closed-form route reads only closed_form_returns; integrating route reads only quadrature_returns — matching the disjoint crv.py:219 vs crv.py:220 returns), the guard claims delivery exactly on the real delivery region. I also confirmed the WITHHELD regions are genuinely non-delivering (so the guard is not an unjustified escape hatch): the non-real / nan / zoo bound and query-point rows raise TypeError, and the Union/FiniteSet supports raise AttributeError at crv.py:202 — the model claims nothing there, and query_arrives states False there as a value.

**ONE ABSTRACTION I ADJUDICATED AND ACCEPT.** On degenerate bounds the arcsin Piecewise collapses to a constant that can coincide with the integral-route value ((0,oo)@1 and (oo,oo)@1 both give 0 on both routes; (1,1)@1 and (-oo,oo) give nan). This does NOT make the spec unfaithful: mapping.md §2 declares the result-code abstraction as ROUTE/FORM-based ('the form the family's supplied `_cdf` produces'), and on every one of those inputs the dispatch demonstrably takes the closed-form route and hands back exactly `_cdf`(x) (part of the 440/440 identity). A value coincidence under an explicitly route-based abstraction is not a disagreement between the modelled function and the real callee; it is at most a coarseness question, which is the spec-too-weak lane, not this one. The discriminating F2P cell is untouched: arc(a,b) real-symbolic bounds at symbolic x yields exactly the Piecewise test_arcsin asserts, while the integral route yields the unevaluated non-convergent Integral the issue reports — distinct.

**CONCLUSION.** Every clause I could put under load — the two result-form arms, the per-route delivery equality in both directions, the two closed-form-route edges, and the scoped MustTerminate guards — agreed with the real post-patch dispatch on all 2195 probed instantiations, with the modelled callee's route selector confirmed to be the sole one by class enumeration. Verdict FAITHFUL. (Recording FAITHFUL as the evidence-backed clean review, not a rubber stamp: the spec region was confirmed byte-identical via same-spec exit 0 and the model verifies live.)

Counterexample / evidence:

```
None. Controls run: (a) same-spec on a verbatim copy of the bundle model.py → exit 0 'SAME' (confirms I projected the frozen spec region); (b) scripts/nagini_verify.sh on that copy → 'Verification successful' RC=0 (the bundle spec+impl is live, not vacuous).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE / NO INHERITED DISPOSITION. There is no documented relaxation in this bundle, so I judged this as an ordinary no-leakage question: `find benchmark-verified/sympy__sympy-13878/ -iname '*RELAX*'` is empty (no RELAXED_LEAKAGE.md anywhere under the instance dir), meta.json has no `relaxed_leakage` key (checked by loading meta.json and testing key membership -> False), and meta gates.G-LEAK.status == 'pass', not 'relaxed'. So there was no unavoidability argument to re-derive and no facet-limited disposition to confirm; the full no-leakage bar applies and I measured against it.

BUNDLE-DIRECTED-TEXT CHECK (reported as its own finding: NONE FOUND). I grepped model.py, refinement.md, mapping.md for reviewer-directed vocabulary (panel_3|attacker 3|leakage|NO-LEAKAGE|honest verdict|you should submit|record.*verdict): zero hits in all three. I also ran the harness's own screen for this, leakage.reviewer_directed(), over every .md in the bundle: verdict.md [], refinement.md [], mapping.md [] -- all clean. The 'NO-LEAKAGE' strings that do exist in the bundle are confined to meta.json (7) and verdict.md (5), i.e. the gate-owned ledger recording a PRIOR G-PANEL-3 run's agent_verdict, not prose addressing me; neither file is part of the artifact set I review and neither instructs a verdict. The only 'verdict' occurrences inside the spec view are the domain term 'delivery verdict' (query_arrives' return value). Nothing in the bundle told me what to submit.

**SURFACE JUDGED.** Consumer-visible surface = spec_view(model.py) + problem_statement only; mapping.md / refinement.md are audit artifacts (referenced from prompts/shared/spec_panel.md, pbt_audit.md etc., i.e. auditor-facing, not eval_mode_* consumer-facing -- eval_mode_1.md renders the contract only). I generated the actual projection with markers.spec_view(src, get_backend('nagini')) and judged THAT text (impl regions replaced by the elision placeholder; module docstring, all comments, the pure region, Requires/Ensures pass through). Spec region integrity: markers.same_spec(src,src) -> True.

### MECHANICAL CHECKS (all on the generated spec view).
- leakage.screen(model.py, nagini backend, gold patch, problem_statement, test_patch): passed=True, hard_failures=[], warnings=[].
- Reproduced gold lines: I ran the gate's own check at a STRICTER threshold than the gate uses (normalized len>=6 instead of >=8) over every added/removed line of patch.diff against the whitespace-stripped spec view -> NONE. No gold diff line is reproduced even in fragment.
- Diff markers ('@@', 'diff --git', '+++ ', '--- ', newline+'index '): none present. The two substring hits for 'diff' are the English words 'families differ' (line 14) and 'two different facts' (line 173) -- prose, not markers.
- Patched paths: patch touches only sympy/stats/crv_types.py; 'crv_types', 'crv.py', dotted 'sympy.stats.crv_types' -> 0 occurrences in the view. The only .py names in the view are 'axiom_check.py' (x3), a bundle-harness file, not a repo path -- it localizes no edit.
- Patched-symbol echo: of the 17 distinctive def/class symbols the patch touches, the only one absent from the problem_statement and edit-localizing is 'ArcsinDistribution' (plus ContinuousRV/Gompertz/Pareto/sample, untouched behaviourally) -> 0 occurrences in the view, in identifiers or comments. The view says 'the family named for the inverse-sine function', never the class name. '`_cdf`' -> 0 occurrences in the view (and it is public in the PS anyway).
- Narration vocabulary: 0 hits for bug|fix(ed|es)|patch(ed)|regression|previously|incorrectly|wrong|broken|added|adds|instead of the integral. The docstring is framed as desired behaviour ('stated as desired behaviour, not as an edit') and states the dispatch as a standing contract, not a before/after.
- hints_text is 'I am working on it !' (20 chars, zero technical content), so there is structurally no hints-only vocabulary the view could be echoing -- the usual leak mode is unavailable here.

THE ONE SUBSTANTIVE QUESTION, MEASURED. The spec-view docstring does disclose the three-branch closed form: 'below the lower bound -> 0; on [low,high] -> (2/pi)*asin(sqrt((x-low)/(high-low))); above the upper bound -> 1'. That is the gold's semantic content, so I did not take its PS-derivability on faith -- I derived it from the PUBLIC problem_statement alone.

The PS prints VERBATIM `Integral(1/sqrt(-_x**2 + 3*_x), (_x, -oo, 1))/pi`, which hands the solver the density 1/(`pi*sqrt`(-t^2+3t)) on support [0,3]; the PS also states outright 'The CDF is basically the arcsin function, for which the distribution is named' and 'the documentation linked above has Wikipedia references, where the formulas for CDF can be found.' Integrating that PS-printed density with the exact substitution t = `3*sin`^2(th) (dt = 6 sin cos dth, sqrt(t(3-t)) = 3 sin cos, integrand collapses to 2/pi dth) gives F(x) = (2/pi)*asin(sqrt(x/3)) -- the view's middle branch, with a=0,b=3.

I confirmed numerically at x in {0.1,0.5,1.0,1.7,2.5,2.99}: the PS-derived integral and (2/pi)asin(sqrt(x/3)) agree to 7e-17..4e-16, i.e. machine precision (a first midpoint run showed ~1e-4 residual, which was quadrature error at the endpoint singularity; the exact substitution removes it and the agreement is exact). The two outer branches (0 below the support, 1 above) are the CDF axioms for a distribution supported on a bounded interval, not an edit-specific choice. So the closed form is a problem_statement-only derivation, and disclosing it reveals nothing the solver cannot compute from the public issue in one substitution.

**WHAT THE VIEW WITHHOLDS.** Everything that would localize the edit stays out: which class gets the method, that the mechanism is a `_cdf` override on that class (PS names `_cdf` generically anyway), the dispatch's file/lines, the base-class `return None` pre-state, the Piecewise/S.Zero/S.One symbols, and every other family the patch touches (Dagum/Frechet/Gamma/GammaInverse/Kumaraswamy/Laplace/Logistic/Nakagami/StudentT/UniformSum -- all public in the PS, all absent from the view). The delivery machinery (closed_form_returns / quadrature_returns / query_arrives) is spec strength against a diverging or non-delivering rival, and its narration is generic ('an ordering question the assembly cannot settle'); it does not name the TypeError/ValueError sites, risch/heurisch, or the Piecewise-assembly refusal path that mapping.md documents in detail -- that internal forensics stayed in the audit artifacts where the consumer never sees it.

**GATES THE DISPOSITION LEANS ON:** G-LEAK pass, G-VERIFY pass, G-GOLD pass, G-AX pass, G-CONF pass (100000 checked, 0 disagreements), G-DIFF pass, G-RESOLVE pass. G-EQ and G-PANEL-1 are recorded fail, but both details read 'INCONCLUSIVE -- 4 attack(s) inconclusive: patch unusable: the auditor's patch does not apply, so the oracle graded nothing and the spec is not implicated' -- an auditor-tooling outage, not a soundness defect, and in either case not a gate this leakage disposition rests on (no facet-limited relaxation is being granted here, so no core-gate soundness is load-bearing for my verdict).

**VERDICT:** NO-LEAKAGE. The spec view reproduces no gold line at len>=6, names no patched file or class, echoes no patched symbol absent from the PS, carries no bug->fix narration, and its single piece of semantic disclosure -- the arcsin closed form -- is derivable from the problem_statement's own printed density in one exact substitution, confirmed to machine precision.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
