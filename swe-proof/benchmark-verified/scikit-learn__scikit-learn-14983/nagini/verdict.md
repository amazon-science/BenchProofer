# P2 adversarial audit — scikit-learn__scikit-learn-14983

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_prepatch.py`, `atk_3_unguarded_index.py`, `atk_4_no_has_store_guard.py`, `atk_5_positive_only_fallback.py`, `atk_6_mutates_store.py`, `atk_7_diverges.py`, `atk_8_raises.py`, `atk_9_store_wins.py`, `atk_11_zero_for_absent.py`, `atk_12_absent_with_store_garbage.py`, `atk_13_swapped_oracle_echo.py`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2_partial_domain.py`, `atk_10_infeasible_guard_diverges.py` |

**Non-vacuity.** The positive control `ctrl_early_returns.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -116,10 +116,5 @@
     # post-conditions-end
     # impl-start
     value = attr  # type: int
-    if value == none and has_store:
-        if key in store:
-            value = store[key]
-        else:
-            value = none
     return value
     # impl-end
```

Attack 2 — `atk_2_partial_domain.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,6 +115,8 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
+    if has_store and (key in store) and store[key] == none:
+        return 42
     value = attr  # type: int
     if value == none and has_store:
         if key in store:
```

Attack 3 — `atk_3_unguarded_index.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -117,9 +117,6 @@
     # impl-start
     value = attr  # type: int
     if value == none and has_store:
-        if key in store:
-            value = store[key]
-        else:
-            value = none
+        value = store[key]
     return value
     # impl-end
```

Attack 4 — `atk_4_no_has_store_guard.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -116,7 +116,7 @@
     # post-conditions-end
     # impl-start
     value = attr  # type: int
-    if value == none and has_store:
+    if value == none:
         if key in store:
             value = store[key]
         else:
```

Attack 5 — `atk_5_positive_only_fallback.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -117,7 +117,7 @@
     # impl-start
     value = attr  # type: int
     if value == none and has_store:
-        if key in store:
+        if key in store and store[key] > 0:
             value = store[key]
         else:
             value = none
```

Attack 6 — `atk_6_mutates_store.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -121,5 +121,6 @@
             value = store[key]
         else:
             value = none
+    store[key] = value
     return value
     # impl-end
```

Attack 7 — `atk_7_diverges.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -121,5 +121,8 @@
             value = store[key]
         else:
             value = none
+    i = 0  # type: int
+    while i >= 0:
+        i = i + 1
     return value
     # impl-end
```

Attack 8 — `atk_8_raises.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -118,7 +118,7 @@
     value = attr  # type: int
     if value == none and has_store:
         if key in store:
-            value = store[key]
+            raise ValueError()
         else:
             value = none
     return value
```

Attack 9 — `atk_9_store_wins.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,11 +115,7 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
-    value = attr  # type: int
-    if value == none and has_store:
-        if key in store:
-            value = store[key]
-        else:
-            value = none
-    return value
+    if has_store and (key in store):
+        return store[key]
+    return attr
     # impl-end
```

Attack 10 — `atk_10_infeasible_guard_diverges.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,6 +115,10 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
+    if has_store and (key in store) and store[key] == none:
+        i = 0  # type: int
+        while i >= 0:
+            i = i + 1
     value = attr  # type: int
     if value == none and has_store:
         if key in store:
```

Attack 11 — `atk_11_zero_for_absent.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,6 +120,6 @@
         if key in store:
             value = store[key]
         else:
-            value = none
+            value = 0
     return value
     # impl-end
```

Attack 12 — `atk_12_absent_with_store_garbage.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -120,6 +120,6 @@
         if key in store:
             value = store[key]
         else:
-            value = none
+            value = 7
     return value
     # impl-end
```

Attack 13 — `atk_13_swapped_oracle_echo.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,11 +115,5 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
-    value = attr  # type: int
-    if value == none and has_store:
-        if key in store:
-            value = store[key]
-        else:
-            value = none
-    return value
+    return resolved_value(none, attr, has_store, store, key)
     # impl-end
```

Attack 14 — `atk_14_other_key_garbage.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,6 +115,8 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
+    if has_store and (key + 1 in store) and store[key + 1] == none:
+        return 7
     value = attr  # type: int
     if value == none and has_store:
         if key in store:
```

Attack 15 — `atk_15_feasible_guard_diverges.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,6 +115,10 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
+    if has_store and (key + 1 in store) and store[key + 1] == none:
+        i = 0  # type: int
+        while i >= 0:
+            i = i + 1
     value = attr  # type: int
     if value == none and has_store:
         if key in store:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_early_returns.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,11 +115,9 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
-    value = attr  # type: int
-    if value == none and has_store:
-        if key in store:
-            value = store[key]
-        else:
-            value = none
-    return value
+    if attr != none:
+        return attr
+    if has_store and (key in store):
+        return store[key]
+    return none
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), nagini, scikit-learn__scikit-learn-14983. All work 15 admissible attacks (>=5 floor), all built by copying the bundle model.py and editing ONLY the impl region; same_spec=True and variant_scope.unsound_evasions==[] on all 16 files (15 attacks + control), 16 distinct md5s. Verdict SOUND.

python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14983 <file>.py

### ATTACK LEDGER (path / observed result):
1. atk_1_prepatch.py — PRE-PATCH bug re-encoded (`value = attr; return value`, no store fallback). rc=2 NOT-A-COUNTEREXAMPLE, does not verify => prepatch_reproduced=True, spec has discriminating power (G-DIFF).
2. atk_2_partial_domain.py — PARTIAL-DOMAIN: exact on the admissible domain, returns 42 exactly on `has_store and key in store and store[key] == none`, which the frozen precondition `Implies(key in store, store[key] != none)` excludes. rc=0 CANDIDATE (verifies, 18.9s). Re-encodes the counterexample the prior pass named (its atk_3). MANDATORY RESOLVE EXECUTED, see below.
3. atk_3_unguarded_index.py — UNGROUNDED store read: `value = store[key]` with no membership test. rc=2 rejected.
4. atk_4_no_has_store_guard.py — the `has_store` guard DROPPED (protects the test_build_repr / MockSplitter P2P case). rc=2 rejected.
5. atk_5_positive_only_fallback.py — BOUNDARY: store value honoured only when strictly positive; right on the F2P constant n_splits=2, wrong for a stored 0/negative that the precondition admits. rc=2 rejected => spec is not fitted to the F2P constants.
6. atk_6_mutates_store.py — CONTROL-FLOW EFFECT: right value, but writes it back into the store. rc=2 rejected (the 1/2 fractional dict_pred permission pins the frame).
7. atk_7_diverges.py — DIVERGENCE: right value computed, then an unconditional infinite loop. rc=2 rejected => MustTerminate(2) load-bearing at the METHOD level.
8. atk_8_raises.py — ABRUPT EXIT on the discriminating case. rc=2 rejected (no Exsures).
9. atk_9_store_wins.py — PRIORITY INVERSION: store beats a PRESENT direct attribute. rc=2 rejected.
10. atk_10_infeasible_guard_diverges.py — divergence gated on the PRECONDITION-EXCLUDED region (store[key]==none). rc=0 CANDIDATE (verifies, 23.1s). MANDATORY RESOLVE EXECUTED, see below.
11. atk_11_zero_for_absent.py — SENTINEL BOUNDARY: literal 0 for absent-everywhere. rc=2 rejected => spec quantifies over `none` properly.
12. atk_12_absent_with_store_garbage.py — targets the one case no single `Implies` covers alone: attr absent, store CARRIED but does NOT record the key (exactly F2P `random_state=None`); returns 7. rc=2 rejected.
13. atk_13_swapped_oracle_echo.py — ARGUMENT-SWAPPED oracle echo `resolved_value(none, attr,...)` (an echo that is NOT the identity). rc=2 rejected => the postcondition is not satisfiable by an arbitrary oracle read.
14. atk_14_other_key_garbage.py — OTHER-KEY domain probe: the precondition constrains store[key] only for the QUERIED key, so `store[key+1]==none` is an ADMITTED input; returns 7 there. rc=2 rejected => no other-key domain hole.
15. atk_15_feasible_guard_diverges.py — THE SHARP ONE: the same divergence as atk_10 but behind a FEASIBLE guard (`store[key+1]==none`, admissible). rc=2 rejected. This isolates atk_10's escape as infeasibility, NOT a hole in MustTerminate.

MANDATORY RESOLVE RUNS (harness.run_resolve, official oracle; both CANDIDATES materialized as faithful refined patches under mapping.md §2's bijection none<->None, has_store<->hasattr(self,'cvargs'), key in store<->key in self.cvargs, store[key]<->self.cvargs[key], and BOTH carry the leg-A `__repr__` hunk):
  * atk_2 patch (patch_atk_2.diff): completed=True, resolved=TRUE, note='resolved'. F2P success=2/2 [test_repeated_cv_repr[RepeatedKFold], test_repeated_cv_repr[RepeatedStratifiedKFold]], failure=0; P2P 105 success / 0 failure.
  * atk_10 patch (patch_atk_10.diff): completed=True, resolved=TRUE, note='resolved'. F2P success=2/2, failure=0; P2P 105 success / 0 failure.
Both candidates therefore RESOLVE => per docs/architecture.md §6 they are correct alternative implementations on the reachable domain (echoes), NOT spec weaknesses, and must not fail the gate. NO verifying wrong impl's faithful patch failed to resolve.

WHY THE TWO CANDIDATES RESOLVE (the reachability question I did not take on trust). Both hide their wrong behaviour behind `key in cvargs and cvargs[key] is None`. I simulated the REAL constructors transcribed from `_split`.py@base_commit (`_RepeatedSplits`.`__init__` stows **cvargs; RepeatedKFold/RepeatedStratifiedKFold pass n_splits=n_splits) together with `_build_repr`'s real `args` computation (sorted `__init__` params excluding VAR_KEYWORD): for RepeatedKFold() and RepeatedKFold(n_splits=2, n_repeats=6), args=['n_repeats','n_splits','random_state'] and cvargs={'n_splits':5|2} — ZERO keys hit the excluded region, so neither the 42 nor the `while True` is reached by any harness test.

(It is reachable only if a USER writes RepeatedKFold(n_splits=None), which no F2P/P2P test does — confirmed by grep over test_split.py@base: the only repr call sites are lines 181, 838, 873-876, 1515-1525 and none constructs n_splits=None.) That is what makes the frozen precondition an honest domain restriction rather than a narrowing that hides live behaviour: I also measured that the bridge's documented None-dropping encoding changes real_gold's answer in 0/24 cases, because cvargs.get(k, None) is None either way.

VACUITY / OBLIGATION CONTROLS (my MEMORY note: a guarded self-call or loop can verify vacuously; Assert(False) is the control):
  * probe_vacuity.py — `Assert(False)` in atk_10's guard position: `bash scripts/nagini_verify.sh` => 'Verification successful', rc=0. The guard is INFEASIBLE under the frozen precondition, which is exactly why atk_10's loop never had to discharge MustTerminate.
  * probe_feasible.py — the same Assert(False) on a SATISFIABLE guard (the discriminating case): rc=1, 'Assert might fail. Assertion False might not hold.' So the probe discriminates and probe_vacuity's success is a real infeasibility measurement, not a dead check.
  * Together with atk_7 (unconditional divergence, rejected) and atk_15 (divergence behind a FEASIBLE guard, rejected), MustTerminate(2) is confirmed load-bearing everywhere it can be reached. refinement.md §C2's claim holds.

### ORACLE DISCRIMINATION (a 'resolved' verdict is worthless if this oracle cannot refute):
  * NEGATIVE CONTROL patch_neg.diff = attack 1's faithful refinement (leg A only, site B UNCHANGED): completed=True, resolved=FALSE, 'patch did not resolve in 3 attempts (consistent — not flaky)', F2P failure=2/2, P2P 105/0. The oracle refutes the prepatch behaviour end-to-end.
  * GOLD control patch_gold.diff, rebuilt by me from base_commit: resolved=TRUE. My generated gold hunks are byte-equivalent to the bundle's patch.diff, which validates my patch-materialization procedure — so the atk_2/atk_10 'resolved' verdicts carry real information.

### A-LEG AUDIT (my assignment's focus; R/I legs are G-CONF's).
* NO consumed axioms, verified mechanically, not from prose: the axioms region contains zero non-comment lines; '@ContractOnly' occurs 0 times anywhere in model.py; the impl region contains no Assume/Refute/Assert. `resolved_value` is a @Pure with a real body (its own resolution inlined), so there is no assumption mechanism to audit for consumption. refinement.md §C's 'no kind-3' claim is therefore structurally true: the one operation that CHANGED (the resolution gaining the cvargs fallback) is modeled DEEPLY and consumed by `Ensures(Result() == resolved_value(...))`, not hidden behind an axiom about the function under change.
* A-REFERENCE correspondence re-derived INDEPENDENTLY of the bundle's axiom_check.py (my own aref_audit.py, with the real gold body transcribed from patch.diff, NOT from the bundle script): deep model == real gold per-key resolution on 160,581 observations (exhaustive boundary grid + 40,000 fuzz objects), 0 divergences on the model's TYPED int domain (231/231 on the explicit typed grid). The grid deliberately covers what the bundle's fuzzer under-covers: FALSY-but-not-None attrs (0, False, '', [], {}, 0.0, (), set()) which gold's `is None` test must report VERBATIM and a truthiness misreading would swallow; None-valued cvargs entries; absent stores; absent keys. All agree.
* The only 3 divergences my harness reported were my OWN out-of-domain artifact, and I ran them down rather than reporting them: a `Weird.__eq__ -> True` object satisfies `w == NONE` (so the model's `attr != none` test sees it as absent) while `w is None` is False. That object is not an int, so it is outside mapping.md §2's declared carrier (attr: int) and cannot arise at this call site. The genuine residual risk of the int-sentinel encoding is a numeric COLLISION (a real parameter value equal to the chosen sentinel); I probed it explicitly (attr == -999999 with the key in cvargs: real reports -999999, model reports the store value). This is a known, bounded property of the sentinel modeling choice that model.py documents and justifies (an Optional[int] @Pure return trips a translator defect in this build); it is not reachable for the F2P parameters (n_splits=2, n_repeats=6, random_state=None) and G-AX exit 0.
* Legs B1/B2/B3 (R + A-reference) match the gold hunk op-for-op at sklearn/model_selection/`_split`.py:2161-2166 @ base_commit 06632c0d18, checked against the repo mirror (git show at base). mapping.md §2's bijection is stated and the resolution is genuinely name-agnostic (it never inspects a name's characters), so the name<->int renaming is exact.
* Leg A1 (the `__repr__` -> `_build_repr` dispatch, tagged I) is the document's weakest-looking tag, so I tested whether it is load-bearing instead of accepting it: patch_legAomit.diff = site B ONLY, omitting the `__repr__` hunk, RUN through the official harness => completed=True, resolved=FALSE ('did not resolve in 3 attempts (consistent — not flaky)'), F2P failure=2/2, P2P 105/0. Leg A is necessary, refinement.md is right to carry it, and the two-hunk recipe is COMPLETE — a reader following the document reconstructs a patch that resolves (my gold rebuild and both candidate patches, all built by following it, applied cleanly and resolved).

**WHY THE SPEC RESISTS:** `Ensures(Result() == resolved_value(attr, none, has_store, store, key))` pins the return value as a TOTAL FUNCTION of the arguments over the whole admissible domain, so no value-returning wrong impl survives (1,3,4,5,9,11,12,13,14 all die on it). That leaves only non-functional escapes, each independently closed: divergence by MustTerminate(2) at the method level (7, 15), store mutation by the fractional dict_pred permission (6), abrupt exit by the absence of Exsures (8). The single remaining escape is DOMAIN RESTRICTION (2, 10) — and I confirmed by simulating the real constructors that the excluded region is unreachable from every harness test, then PROVED it harmless by running both patches through the oracle: both resolved.

**FLOOR:** 15 admissible attacks (>=5 required), prepatch bug reproduced (atk_1), structurally-different positive control (ctrl_early_returns.py — three early returns vs. the frozen body's mutated local in nested ifs; deliberately NOT a resolved_value delegate, so the control does not lean on the echo argument) verifies rc=0 CANDIDATE in 21.8s, and EVERY candidate's faithful patch was materialized and RUN through the official harness. No verifying wrong impl whose faithful refined patch fails to resolve => verify=>correct holds for this bundle. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_prepatch.py`, `atk_3_unguarded_index.py`, `atk_4_no_has_store_guard.py`, `atk_5_positive_only_fallback.py`, `atk_6_mutates_store.py`, `atk_7_diverges.py`, `atk_8_raises.py`, `atk_9_store_wins.py`, `atk_11_zero_for_absent.py`, `atk_12_absent_with_store_garbage.py`, `atk_13_swapped_oracle_echo.py`, +2 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2_partial_domain.py`, `atk_10_infeasible_guard_diverges.py` |

**Non-vacuity.** The positive control `ctrl_early_returns.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial_domain.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_unguarded_index.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_no_has_store_guard.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_positive_only_fallback.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_mutates_store.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_diverges.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_raises.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_store_wins.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_infeasible_guard_diverges.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_zero_for_absent.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_absent_with_store_garbage.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_swapped_oracle_echo.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_other_key_garbage.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_feasible_guard_diverges.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl_early_returns.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -115,11 +115,9 @@
     Ensures(Implies(attr == none and not has_store, Result() == none))
     # post-conditions-end
     # impl-start
-    value = attr  # type: int
-    if value == none and has_store:
-        if key in store:
-            value = store[key]
-        else:
-            value = none
-    return value
+    if attr != none:
+        return attr
+    if has_store and (key in store):
+        return store[key]
+    return none
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity), nagini, scikit-learn__scikit-learn-14983. All work 15 admissible attacks (>=5 floor), all built by copying the bundle model.py and editing ONLY the impl region; same_spec=True and variant_scope.unsound_evasions==[] on all 16 files (15 attacks + control), 16 distinct md5s. Verdict SOUND.

python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14983 <file>.py

### ATTACK LEDGER (path / observed result):
1. atk_1_prepatch.py — PRE-PATCH bug re-encoded (`value = attr; return value`, no store fallback). rc=2 NOT-A-COUNTEREXAMPLE, does not verify => prepatch_reproduced=True, spec has discriminating power (G-DIFF).
2. atk_2_partial_domain.py — PARTIAL-DOMAIN: exact on the admissible domain, returns 42 exactly on `has_store and key in store and store[key] == none`, which the frozen precondition `Implies(key in store, store[key] != none)` excludes. rc=0 CANDIDATE (verifies, 18.9s). Re-encodes the counterexample the prior pass named (its atk_3). MANDATORY RESOLVE EXECUTED, see below.
3. atk_3_unguarded_index.py — UNGROUNDED store read: `value = store[key]` with no membership test. rc=2 rejected.
4. atk_4_no_has_store_guard.py — the `has_store` guard DROPPED (protects the test_build_repr / MockSplitter P2P case). rc=2 rejected.
5. atk_5_positive_only_fallback.py — BOUNDARY: store value honoured only when strictly positive; right on the F2P constant n_splits=2, wrong for a stored 0/negative that the precondition admits. rc=2 rejected => spec is not fitted to the F2P constants.
6. atk_6_mutates_store.py — CONTROL-FLOW EFFECT: right value, but writes it back into the store. rc=2 rejected (the 1/2 fractional dict_pred permission pins the frame).
7. atk_7_diverges.py — DIVERGENCE: right value computed, then an unconditional infinite loop. rc=2 rejected => MustTerminate(2) load-bearing at the METHOD level.
8. atk_8_raises.py — ABRUPT EXIT on the discriminating case. rc=2 rejected (no Exsures).
9. atk_9_store_wins.py — PRIORITY INVERSION: store beats a PRESENT direct attribute. rc=2 rejected.
10. atk_10_infeasible_guard_diverges.py — divergence gated on the PRECONDITION-EXCLUDED region (store[key]==none). rc=0 CANDIDATE (verifies, 23.1s). MANDATORY RESOLVE EXECUTED, see below.
11. atk_11_zero_for_absent.py — SENTINEL BOUNDARY: literal 0 for absent-everywhere. rc=2 rejected => spec quantifies over `none` properly.
12. atk_12_absent_with_store_garbage.py — targets the one case no single `Implies` covers alone: attr absent, store CARRIED but does NOT record the key (exactly F2P `random_state=None`); returns 7. rc=2 rejected.
13. atk_13_swapped_oracle_echo.py — ARGUMENT-SWAPPED oracle echo `resolved_value(none, attr,...)` (an echo that is NOT the identity). rc=2 rejected => the postcondition is not satisfiable by an arbitrary oracle read.
14. atk_14_other_key_garbage.py — OTHER-KEY domain probe: the precondition constrains store[key] only for the QUERIED key, so `store[key+1]==none` is an ADMITTED input; returns 7 there. rc=2 rejected => no other-key domain hole.
15. atk_15_feasible_guard_diverges.py — THE SHARP ONE: the same divergence as atk_10 but behind a FEASIBLE guard (`store[key+1]==none`, admissible). rc=2 rejected. This isolates atk_10's escape as infeasibility, NOT a hole in MustTerminate.

MANDATORY RESOLVE RUNS (harness.run_resolve, official oracle; both CANDIDATES materialized as faithful refined patches under mapping.md §2's bijection none<->None, has_store<->hasattr(self,'cvargs'), key in store<->key in self.cvargs, store[key]<->self.cvargs[key], and BOTH carry the leg-A `__repr__` hunk):
  * atk_2 patch (patch_atk_2.diff): completed=True, resolved=TRUE, note='resolved'. F2P success=2/2 [test_repeated_cv_repr[RepeatedKFold], test_repeated_cv_repr[RepeatedStratifiedKFold]], failure=0; P2P 105 success / 0 failure.
  * atk_10 patch (patch_atk_10.diff): completed=True, resolved=TRUE, note='resolved'. F2P success=2/2, failure=0; P2P 105 success / 0 failure.
Both candidates therefore RESOLVE => per docs/architecture.md §6 they are correct alternative implementations on the reachable domain (echoes), NOT spec weaknesses, and must not fail the gate. NO verifying wrong impl's faithful patch failed to resolve.

WHY THE TWO CANDIDATES RESOLVE (the reachability question I did not take on trust). Both hide their wrong behaviour behind `key in cvargs and cvargs[key] is None`. I simulated the REAL constructors transcribed from `_split`.py@base_commit (`_RepeatedSplits`.`__init__` stows **cvargs; RepeatedKFold/RepeatedStratifiedKFold pass n_splits=n_splits) together with `_build_repr`'s real `args` computation (sorted `__init__` params excluding VAR_KEYWORD): for RepeatedKFold() and RepeatedKFold(n_splits=2, n_repeats=6), args=['n_repeats','n_splits','random_state'] and cvargs={'n_splits':5|2} — ZERO keys hit the excluded region, so neither the 42 nor the `while True` is reached by any harness test.

(It is reachable only if a USER writes RepeatedKFold(n_splits=None), which no F2P/P2P test does — confirmed by grep over test_split.py@base: the only repr call sites are lines 181, 838, 873-876, 1515-1525 and none constructs n_splits=None.) That is what makes the frozen precondition an honest domain restriction rather than a narrowing that hides live behaviour: I also measured that the bridge's documented None-dropping encoding changes real_gold's answer in 0/24 cases, because cvargs.get(k, None) is None either way.

VACUITY / OBLIGATION CONTROLS (my MEMORY note: a guarded self-call or loop can verify vacuously; Assert(False) is the control):
  * probe_vacuity.py — `Assert(False)` in atk_10's guard position: `bash scripts/nagini_verify.sh` => 'Verification successful', rc=0. The guard is INFEASIBLE under the frozen precondition, which is exactly why atk_10's loop never had to discharge MustTerminate.
  * probe_feasible.py — the same Assert(False) on a SATISFIABLE guard (the discriminating case): rc=1, 'Assert might fail. Assertion False might not hold.' So the probe discriminates and probe_vacuity's success is a real infeasibility measurement, not a dead check.
  * Together with atk_7 (unconditional divergence, rejected) and atk_15 (divergence behind a FEASIBLE guard, rejected), MustTerminate(2) is confirmed load-bearing everywhere it can be reached. refinement.md §C2's claim holds.

### ORACLE DISCRIMINATION (a 'resolved' verdict is worthless if this oracle cannot refute):
  * NEGATIVE CONTROL patch_neg.diff = attack 1's faithful refinement (leg A only, site B UNCHANGED): completed=True, resolved=FALSE, 'patch did not resolve in 3 attempts (consistent — not flaky)', F2P failure=2/2, P2P 105/0. The oracle refutes the prepatch behaviour end-to-end.
  * GOLD control patch_gold.diff, rebuilt by me from base_commit: resolved=TRUE. My generated gold hunks are byte-equivalent to the bundle's patch.diff, which validates my patch-materialization procedure — so the atk_2/atk_10 'resolved' verdicts carry real information.

### A-LEG AUDIT (my assignment's focus; R/I legs are G-CONF's).
* NO consumed axioms, verified mechanically, not from prose: the axioms region contains zero non-comment lines; '@ContractOnly' occurs 0 times anywhere in model.py; the impl region contains no Assume/Refute/Assert. `resolved_value` is a @Pure with a real body (its own resolution inlined), so there is no assumption mechanism to audit for consumption. refinement.md §C's 'no kind-3' claim is therefore structurally true: the one operation that CHANGED (the resolution gaining the cvargs fallback) is modeled DEEPLY and consumed by `Ensures(Result() == resolved_value(...))`, not hidden behind an axiom about the function under change.
* A-REFERENCE correspondence re-derived INDEPENDENTLY of the bundle's axiom_check.py (my own aref_audit.py, with the real gold body transcribed from patch.diff, NOT from the bundle script): deep model == real gold per-key resolution on 160,581 observations (exhaustive boundary grid + 40,000 fuzz objects), 0 divergences on the model's TYPED int domain (231/231 on the explicit typed grid). The grid deliberately covers what the bundle's fuzzer under-covers: FALSY-but-not-None attrs (0, False, '', [], {}, 0.0, (), set()) which gold's `is None` test must report VERBATIM and a truthiness misreading would swallow; None-valued cvargs entries; absent stores; absent keys. All agree.
* The only 3 divergences my harness reported were my OWN out-of-domain artifact, and I ran them down rather than reporting them: a `Weird.__eq__ -> True` object satisfies `w == NONE` (so the model's `attr != none` test sees it as absent) while `w is None` is False. That object is not an int, so it is outside mapping.md §2's declared carrier (attr: int) and cannot arise at this call site. The genuine residual risk of the int-sentinel encoding is a numeric COLLISION (a real parameter value equal to the chosen sentinel); I probed it explicitly (attr == -999999 with the key in cvargs: real reports -999999, model reports the store value). This is a known, bounded property of the sentinel modeling choice that model.py documents and justifies (an Optional[int] @Pure return trips a translator defect in this build); it is not reachable for the F2P parameters (n_splits=2, n_repeats=6, random_state=None) and G-AX exit 0.
* Legs B1/B2/B3 (R + A-reference) match the gold hunk op-for-op at sklearn/model_selection/`_split`.py:2161-2166 @ base_commit 06632c0d18, checked against the repo mirror (git show at base). mapping.md §2's bijection is stated and the resolution is genuinely name-agnostic (it never inspects a name's characters), so the name<->int renaming is exact.
* Leg A1 (the `__repr__` -> `_build_repr` dispatch, tagged I) is the document's weakest-looking tag, so I tested whether it is load-bearing instead of accepting it: patch_legAomit.diff = site B ONLY, omitting the `__repr__` hunk, RUN through the official harness => completed=True, resolved=FALSE ('did not resolve in 3 attempts (consistent — not flaky)'), F2P failure=2/2, P2P 105/0. Leg A is necessary, refinement.md is right to carry it, and the two-hunk recipe is COMPLETE — a reader following the document reconstructs a patch that resolves (my gold rebuild and both candidate patches, all built by following it, applied cleanly and resolved).

**WHY THE SPEC RESISTS:** `Ensures(Result() == resolved_value(attr, none, has_store, store, key))` pins the return value as a TOTAL FUNCTION of the arguments over the whole admissible domain, so no value-returning wrong impl survives (1,3,4,5,9,11,12,13,14 all die on it). That leaves only non-functional escapes, each independently closed: divergence by MustTerminate(2) at the method level (7, 15), store mutation by the fractional dict_pred permission (6), abrupt exit by the absence of Exsures (8). The single remaining escape is DOMAIN RESTRICTION (2, 10) — and I confirmed by simulating the real constructors that the excluded region is unreachable from every harness test, then PROVED it harmless by running both patches through the oracle: both resolved.

**FLOOR:** 15 admissible attacks (>=5 required), prepatch bug reproduced (atk_1), structurally-different positive control (ctrl_early_returns.py — three early returns vs. the frozen body's mutated local in nested ifs; deliberately NOT a resolved_value delegate, so the control does not lean on the echo argument) verifies rc=0 CANDIDATE in 21.8s, and EVERY candidate's faithful patch was materialized and RUN through the official harness. No verifying wrong impl whose faithful refined patch fails to resolve => verify=>correct holds for this bundle. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**Reference used correctly:** fresh worktree of scikit-learn_scikit-learn.git at base_commit 06632c0d185128a53c57ccc73b25b6408e90bb89 with patch.diff APPLIED (), plus the SWE-bench container image sweb.eval...14983 with patch.diff applied to /testbed (sklearn 0.22.dev0 importable). Base commit was consulted only as the framing reference for the callees the patch does not touch.

Modeled operation (mapping.md): the per-key value resolution inside `_build_repr`'s `for key in args:` loop (`_split`.py:2161-2166 gold), plus the `_RepeatedSplits`.`__repr__` dispatch (`_split`.py:1166 gold). Real gold body confirmed verbatim in the applied worktree:
    value = getattr(self, key, None)
    if value is None and hasattr(self, 'cvargs'):
        value = self.cvargs.get(key, None)

PRIMARY EVIDENCE (machine-checked, faith14983_ensures2.py run in-container against the REAL patched `_build_repr`): I evaluated EVERY Ensures conjunct of reported_param_value as an executable predicate over the value the real function actually reports, on 80,002 Requires-satisfying admissible inputs (14 structured branch-coverage objects covering all resolution branches, the real RepeatedKFold/RepeatedStratifiedKFold across 6 constructor configs each, and seeded fuzz). Result: checked=80002, skipped_by_precondition=0, missing_key=0, VIOLATIONS=0. Conjuncts individually probed: E1 Result()==resolved_value; E2 attr!=none -> Result()==attr; E3 store fallback -> Result()==store[key]; E4 store fallback -> Result()!=none; E5 no store -> Result()==none. Not one conjunct is falsified by the real callee on any admissible input, so the spec is not too strong.

FALSE LEAD I RULED OUT (recording so it is not re-raised): a first pass reported 745 violations of E1/E3/E4. All 745 were sentinel collisions I injected deliberately — I varied `none` over 0 and -999999 while real parameter values took those same values, which breaks the mapping.md §2 bijection (`none` must be a value distinct from every real parameter value; the encoding `attr = none if raw is None else raw` is only injective under that condition). Those are bridge misuse, not spec defects. Re-running with a per-object FRESH sentinel (min(values)-1) yields zero violations. This is a bridge-precondition artifact, so it does not support UNFAITHFUL.

### Boundary cases checked explicitly
- cvargs entry holding None: reachable in the real repo (RepeatedKFold(n_splits=None) -> cvargs={'n_splits': None}); real repr gives 'n_splits=None'. The bridge drops None entries from `store`, so the model resolves to `none` == absent — AGREES with the real code (cvargs.get returns None). The precondition Implies(key in store, store[key] != none) is exactly this, and it is a faithful encoding, not a convenient exclusion.
- attribute present AND store records the key: real code short-circuits on `value is None`, attribute wins; matches E2. Verified on synthetic objects.
- has_store false with a None attribute: stays None (the test_build_repr / MockSplitter PASS_TO_PASS case); matches E5.
- Zero and negative reported values round-trip through `_pprint`'s rendering, so the parse-back oracle is exact.

**SCOPE GAP EXAMINED AND JUDGED NOT A DEFECT:** the real `_build_repr` wraps the resolution in catch_warnings and `continue`s (dropping the key from params) when a DeprecationWarning fires. The model always returns a value, so on a deprecated parameter the real function reports NOTHING while the model reports the store value — I built a DepSynth class with a DeprecationWarning-emitting property plus a cvargs store and confirmed the real render drops p0 entirely (DepSynth(p1=3)) where the model gives 42. This is NOT a faithfulness break: (a) the deprecation `continue` is unchanged framing that the patch does not touch (refinement.md §B4 declares the surrounding loop/formatting out of scope), and (b) it is UNREACHABLE for the modeled objects — I enumerated the cvargs-carrying classes' parameters (n_splits, n_repeats, random_state, cv on both RepeatedKFold and RepeatedStratifiedKFold) and found NO parameter that emits a DeprecationWarning. The two conditions (deprecated param AND a cvargs store) do not co-occur anywhere in the repo, so the model and the real callee never disagree on an object the spec is about.

### CORROBORATING GATES (all re-run by me, not taken on trust):
- axiom_check.py in-container: exit 0, 8 boundary + ~20000 fuzz, end-to-end PASS (both classes' repr == the F2P string). Outside container: exit 0 with the sklearn leg guarded/skipped.
- conformance_check.py in-container against the real `_build_repr`: exit 0, 100000 per-key checks, 0 disagreements, seed 149830.
- Bundle model.py under the pinned verifier: 'Verification successful' (28.47s).
- G-DIFF sensitivity: model_prepatch.py FAILS with exactly 'Postcondition... Result() == resolved_value(...) might not hold' at line 104 — the spec genuinely senses the patch delta and is not vacuous.
- F2P + P2P: test_repeated_cv_repr[RepeatedKFold], test_repeated_cv_repr[RepeatedStratifiedKFold], test_build_repr all pass on the patched testbed (3 passed).
- Spec-region integrity: swebench_unified.adversary same-spec on an impl-only rewrite returns 'SAME — attack shares the bundle's exact specification' (exit 0), confirming the marker regions isolate the impl as claimed.

**Termination:** Requires(MustTerminate(2)) is faithful — the real per-key resolution is loop-free straight-line code (one getattr, one guarded dict.get, one assignment), so it cannot exclude a correct implementation, and it is load-bearing against a vacuously-verifying diverging impl under Nagini's partial-correctness default.

**CONCLUSION:** no admissible input exists on which the modeled function disagrees with the real patched callee. I could not produce a diverging input, and the one behavioral gap I did find (deprecation `continue`) is unchanged out-of-scope framing that is unreachable for the modeled classes. The spec is not too strong and does not drift from real repo behavior. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**TARGET:** nagini bundle scikit-learn__scikit-learn-14983 (leakage / gold-reconstruction attacker). Verdict NO-LEAKAGE.

**NO RELAXATION IN THIS BUNDLE.** Checked first, since a relaxation would change the whole shape of the review: meta.json has no `relaxed_leakage` key (walked the full JSON for any key matching /relax/i -- zero hits; top-level keys are additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version), `gates['G-LEAK'].status == 'pass'` (detail "spec view clean", not "relaxed"), and no RELAXED_LEAKAGE.md exists in the bundle dir. So there is no unavoidability argument to re-derive and no facet-scoped disposition to inherit -- this is a straight leakage judgement against the public problem_statement.

SPEC VIEW MEASURED, NOT ASSUMED. Computed the actual consumer view with swebench_unified.markers.spec_view(model.py, NaginiBackend.language) -- the projection that elides the impl region (it emits `...  # implementation elided -- supplied by the consumer`). Everything below is scanned against that projected string, i.e. what a solver actually sees, and NOT against the impl region, which the consumer never gets.

LEXICAL SCREEN (my run, not the stamp). Re-ran leakage.screen(model.py, nagini tables, row['patch'], row['problem_statement'], test_patch=row['test_patch']) against the frozen dataset row: passed=True, hard_failures=[], warnings=[]. Independently grepped the spec view for every repo-side term that could localize the edit -- ALL ABSENT: cvargs, `_build_repr`, build_repr, getattr, hasattr,.get(, `__repr__`, repr(, sklearn, `_split`.py, model_selection, RepeatedKFold, RepeatedStratifiedKFold, n_splits, n_repeats, random_state, get_n_splits, KFold, and the full diff-marker set (diff --git, @@, +++). Narration scan via `_NARRATION_RE` over the spec view returned the empty set (no bug/fix/patched/previously/incorrectly/wrong). Patch changed-symbol set is {build_repr, get_n_splits, repr}; the spec view's identifiers are `reported_param_value` and `resolved_value`, neither of which embeds any of the three. Patched path sklearn/model_selection/`_split`.py is never named. The spec view's vocabulary is uniformly abstracted -- "a secondary keyword-argument store", "a mapping from parameter name to value" -- never `cvargs`.

THE DISCRIMINATOR IS DERIVABLE FROM THE PUBLIC problem_statement ALONE -- this is the load-bearing measurement. The spec view does name the discriminating behaviour ("a parameter that is NOT held as a direct attribute but IS recorded in the secondary store must be reported with the store's concrete value, NOT as absent"). That is only leakage if a solver could not get there from the public issue. It can, and I measured the derivation in a worktree at base_commit 06632c0d185128a53c57ccc73b25b6408e90bb89 (git worktree --detach under a mktemp -d /tmp dir; bundle untouched):
  * The public problem_statement's "Expected Results" states the target string verbatim: `RepeatedKFold(n_splits=5, n_repeats=10, random_state=None)` -- n_splits=5 is PUBLIC.
  * Base repo, read at that commit: RepeatedKFold.`__init__` (`_split`.py:1214-1216) calls `super().__init__(KFold, n_repeats, random_state, n_splits=n_splits)`, and `_RepeatedSplits`.`__init__` (`_split`.py:1090-1104) sets only self.cv/self.n_repeats/self.random_state/self.cvargs. Confirmed by construction: hasattr(obj,'n_splits') is False -- n_splits lives ONLY in the cvargs mapping.
  * Simulated the naive fix (route `__repr__` to the PRE-patch `_build_repr`, no fallback) against the gold resolution on a RepeatedKFold-shaped object with the real sorted-arg list ['n_repeats','n_splits','random_state']:
      naive -> RepeatedKFold(n_repeats=10, n_splits=None, random_state=None)
      gold  -> RepeatedKFold(n_repeats=10, n_splits=5, random_state=None)
    The naive fix misses the PUBLICLY STATED expected string on exactly n_splits. So the public issue plus the base source forces the secondary-store fallback: a solver who only dispatches `__repr__` fails the public Expected Results. The spec view names a fact the problem_statement already implies -- restating a public consequence, not revealing a hidden edit.

LOAD-BEARING CHECK (strip-the-narration control). Ran the usual test to confirm the discriminating clause is spec, not decoration: model_prepatch.py shares the spec byte-for-byte (markers.same_spec(model, prepatch) = True) and differs only by dropping the store fallback from the impl. Under the pinned verifier: model.py => "Verification successful" (20.9s); model_prepatch.py => "Verification failed -- Postcondition of reported_param_value might not hold. Assertion (Result() == resolved_value(attr, none, has_store, store, key)) might not hold." The clause is load-bearing (the spec does NOT verify against the pre-patch impl), so a faithful spec cannot drop it -- and it doesn't need a relaxation to keep it, because the derivation above is public. Also ran `adversary same-spec` on a copy of model.py: exit 0, "SAME -- attack shares the bundle's exact specification", so the spec region I judged is the bundle's.

FINDING TO REPORT IN ITS OWN RIGHT -- A BUNDLE FILE ADDRESSES ITS REVIEWERS. model.py's pure region carries a block opening "# NOTE for auditors:" (spec-view lines 56-64) which argues that `return resolved_value(...)` is a correct impl and then instructs a panel on classification: "Such an echo therefore belongs in positive_control, never in a spec-too-weak attack list, which must contain only implementations whose behavior DIFFERS from resolved_value on some admissible input." Reporting per instruction.

Assessment: this steers the G-PANEL-1 (spec-too-weak) panel, not this gate, and it leaks nothing about the gold edit -- it is a statement about the model's own @Pure helper, and leakage.reviewer_directed(spec_view) returns [] (that screen is also scoped to RELAXED_LEAKAGE.md, so it would never have caught this). It does not change my verdict, but a bundle telling a downstream panel which lane an attack "belongs" in pre-empts a judgement that panel is supposed to reach itself; I flag it for the record and recommend the prose move to the panel's prompt. Independently, I confirm the note's substantive claim is at least true here: resolved_value is transparent (its body inlines the resolution) rather than an opaque answer-key.

SEPARATE DEFECT, NOT LEAKAGE -- STALE region_hashes IN meta.json. Recomputed markers.region_hashes(model.py) and compared to meta.json['region_hashes']: axioms, impl, post-conditions MATCH; pre-conditions (mine 9d85bc8eb4a6 vs meta 7f47eec466c9), pure (927073b21af2 vs 4ace0ffbdc15), and spec_view (53fb4dd25282 vs 7528cb022177) DISAGREE. The mismatch is consistent with a later spec-repair that added Requires(MustTerminate(2)) to pre-conditions and the auditors note to pure without restamping region_hashes (model.py mtime Aug 5 22:12, meta.json Aug 15 10:24; G-LEAK stamped 2026-08-05T14:05:30Z -- i.e. the G-LEAK pass predates the current spec text). This means the stamped "spec view clean" describes an EARLIER spec view than the one shipped, so I did not rely on it -- my NO-LEAKAGE rests on the fresh screen + greps + derivation above, all run against the current file. Recommend a restamp so the digests match the artifact they describe; it is an integrity/freshness issue, and no leak.

**CONCLUSION:** the spec view reproduces no gold-diff line, carries no diff markers, names no patched file or symbol, contains no bug/fix narration, and its one discriminating clause is derivable from the public problem_statement's own Expected Results against the base source (measured, not argued). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
