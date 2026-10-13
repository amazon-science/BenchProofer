# P2 adversarial audit — django__django-15104

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.py`, `atk_6_partial_wrongkey.py`, `atk_7_fabricate.py`, `atk_8_postread_flip.py`, `atk_9_doubledrop.py`, `atk_10_selfrec.py`, `atk_11_swapguard.py`, `atk_12_uncond_pop.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -149,6 +149,6 @@
     # post-conditions-end
     # impl-start
     if is_relation:
-        return pop_default(kwargs, TO())
+        return del_present(kwargs, TO())
     return kwargs
     # impl-end
```

Attack 2 — `atk_6_partial_wrongkey.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -149,6 +149,8 @@
     # post-conditions-end
     # impl-start
     if is_relation:
-        return pop_default(kwargs, TO())
+        if TO() in kwargs:
+            return del_present(kwargs, TO())
+        return pop_default(kwargs, 1)
     return kwargs
     # impl-end
```

Attack 3 — `atk_7_fabricate.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -149,6 +149,8 @@
     # post-conditions-end
     # impl-start
     if is_relation:
-        return pop_default(kwargs, TO())
+        tmp = {}  # type: Dict[int, int]
+        tmp[TO()] = 0
+        return del_present(tmp, TO())
     return kwargs
     # impl-end
```

Attack 4 — `atk_8_postread_flip.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -149,6 +149,9 @@
     # post-conditions-end
     # impl-start
     if is_relation:
-        return pop_default(kwargs, TO())
+        r = pop_default(kwargs, TO())
+        if TO() in kwargs:
+            return kwargs
+        return r
     return kwargs
     # impl-end
```

Attack 5 — `atk_9_doubledrop.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -149,6 +149,7 @@
     # post-conditions-end
     # impl-start
     if is_relation:
-        return pop_default(kwargs, TO())
+        r = pop_default(kwargs, TO())
+        return pop_default(r, 1)
     return kwargs
     # impl-end
```

Attack 6 — `atk_10_selfrec.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -149,6 +149,6 @@
     # post-conditions-end
     # impl-start
     if is_relation:
-        return pop_default(kwargs, TO())
+        return reduce_to_relation_agnostic(kwargs, is_relation)
     return kwargs
     # impl-end
```

Attack 7 — `atk_11_swapguard.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -148,7 +148,7 @@
                                                   j in Result() and Result()[j] == kwargs[j]))))
     # post-conditions-end
     # impl-start
-    if is_relation:
+    if not is_relation:
         return pop_default(kwargs, TO())
     return kwargs
     # impl-end
```

Attack 8 — `atk_12_uncond_pop.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -148,7 +148,5 @@
                                                   j in Result() and Result()[j] == kwargs[j]))))
     # post-conditions-end
     # impl-start
-    if is_relation:
-        return pop_default(kwargs, TO())
-    return kwargs
+    return pop_default(kwargs, TO())
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-15104/nagini. Every file built by copying the shipped model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 12 confirmed `same-spec` exit 0.

**SPEC ANALYSIS.** The postconditions pin Result by value in BOTH branches, so no behavioural freedom remains. Relation branch: (a) is_relation => TO() not in Result; (b) forall j != TO() in kwargs => j in Result and Result[j]==kwargs[j]; (c) forall j in Result => j in kwargs and Result[j]==kwargs[j]. Together: Result == kwargs minus {TO()} EXACTLY. Non-relation branch: (c) + (d) forall j in kwargs => j in Result with same value => Result == kwargs exactly, target keyword included. Crucially (a) is quantified over EVERY admissible input, including a relation field whose kwargs OMIT TO() -- which is exactly the reported bug input -- and there is no precondition restricting the domain. MustTerminate(2) carries total correctness; Acc(dict_pred(kwargs),1/2) keeps the input read-only.

ATTACKS RUN (cmd for each: `python -m swebench_unified.adversary weakness nagini django__django-15104 <path>`; outputs saved as out_<n>.txt beside each attack):
1. atk_1_prepatch.py -- THE PREPATCH BUG, byte-identical to shipped model_prepatch.py (diff empty): relation branch uses the narrow primitive del_present(kwargs,TO()). weakness -> exit 2 'attack does not verify (verification failed)'. Direct `bash scripts/nagini_verify.sh atk_1_prepatch.py` -> 'Verification failed ... atk_1_prepatch.py:152:16: error: The precondition of method del_present might not hold. Assertion (k in d) might not hold.' (34.18s) -- the EXACT error refinement.md B documents. PREPATCH REPRODUCED.
2. atk_6_partial_wrongkey.py -- PARTIAL-DOMAIN: correct via del_present on the TO()-present domain, but drops the WRONG keyword (pop_default(kwargs,1)) on the TO()-absent domain, i.e. exactly the bug input. weakness -> exit 2, verification failed. REJECTED (this is the sharpest partial-domain shape: it is right wherever the prepatch was defined and wrong only where the bug lived).
3. atk_7_fabricate.py -- UNGROUNDED ORACLE: answers from a fabricated local mapping ({TO():0} then del_present) instead of the input, so it satisfies (a) but severs the result from kwargs. weakness -> exit 2, verification failed (postcondition (b) preservation). REJECTED.
4. atk_8_postread_flip.py -- CONTROL-FLOW-EFFECT: computes the correct reduction then returns the UN-reduced kwargs when TO() was present, i.e. removal effective only on inputs that never had the key. weakness -> exit 2, verification failed. REJECTED.
5. atk_9_doubledrop.py -- BOUNDARY/OVER-REMOVAL: drops TO() AND keyword 1. weakness -> exit 2, verification failed (post (b): keyword 1 must survive). REJECTED.
6. atk_10_selfrec.py -- UNGROUNDED-ORACLE ECHO: discharges the postcondition by re-invoking this routine's own contract. weakness -> exit 2, verification failed: MustTerminate(2) offers no smaller measure for a self-call, so the vacuous-recursion hole is closed. REJECTED (confirms the A7 termination leg is load-bearing, not decoration).
7. atk_11_swapguard.py -- CONTROL-FLOW-EFFECT: inverted relation guard. weakness -> exit 2, verification failed. REJECTED.
8. atk_12_uncond_pop.py -- CONTROL-FLOW-EFFECT: guard ignored, removal unconditional. weakness -> exit 2, verification failed (non-relation post (d): TO() must survive). REJECTED.

**NO CANDIDATE EMERGED:** every admissible same-spec attack failed verification (weakness exit 2, verify_completed=True). Therefore NO faithful refined patch had to be materialized and no run_resolve was required -- patches={} is correct here, not an omission. Nothing to check with `git apply --check`.

THREE FURTHER ATTACKS DELIBERATELY EXCLUDED FROM `attacks` (probed nothing; submitting them would force a spurious role-wide INCONCLUSIVE). I attacked the SPEC-VIEW ELISION hole -- markers.py elides the impl region, so a contract smuggled INTO that region survives same-spec -- and Nagini's front end rejects all three before Viper, exit 1 with 'Translation failed' and no Viper banner. Per backends/nagini.py `_no_verdict` -> verify.py `crashed` -> adversary.check_attack these come back verify_completed=False, which build_one.py counts as inconclusive rather than as a rejection; I verified that programmatically (atk_3/atk_5: completed=False). They are real evidence that the hole is closed by the toolchain, but they are NOT evidence of spec strength, so they stay out of the tally:
  - atk_3_impl_requires.py: smuggles `Requires(TO() in kwargs)` into the impl region to make the prepatch del_present dischargeable. -> exit 2, 'no Viper verdict: Translation failed'.
  - atk_4_exsures_raise.py: smuggles `Exsures(KeyError, True)` and raises on the bug input. -> exit 2, 'no Viper verdict'.
  - atk_5_raise_bare.py: raises KeyError on the absent-target relation field (the literal prepatch crash). -> exit 2, 'no Viper verdict: Translation failed'. Note the consequence: Nagini cannot express this rival at all, so the ONLY way the prepatch crash is sensed is the del_present precondition of attack 1 -- and that path does fire correctly.

**NON-VACUITY CONTROL.** atk_2_vacuity_control.py = shipped impl with `Assert(False)` prepended. `bash scripts/nagini_verify.sh` -> exit 1, 'Assert might fail. Assertion False might not hold.' So the precondition set is satisfiable and the verifying attacks/positive control are not passing vacuously (per the guarded-self-call/vacuity lesson).

**POSITIVE CONTROL.** pos_control.py = shipped model.py (diff empty). `bash scripts/nagini_verify.sh pos_control.py` -> 'Verification successful' (33.65s), exit 0.

A-LEG AUDIT (my focus; R/I legs covered by G-CONF). Legs: A1 I, A2 R, A3 R, A4 I, A5 A-reference, A6 I, A7 R. No kind-3 and no A-consumed axiom -- confirmed by reading: the single CHANGED operation (the keyword removal) is modeled DEEPLY as pop_default (post) / del_present (pre), not hidden behind an opaque axiom about the function under change, which is the shape that would make verify-implies-correct unfalsifiable.
  * G-AX executed: `python axiom_check.py` -> exit 0, 'G-AX OK: pop_default (== d.pop(k,None), applicable to any mapping) and del_present (== del d[k], applicable only when k present: raises on absent key) sound on 9 boundary + 20000 fuzz mappings'. It imports only copy/random and plain dict; nothing repo-specific. It asserts BOTH directions of the discriminating fact, including that real `del d[k]` RAISES on an absent key -- which is what licenses del_present's extra Requires(k in d) that pop_default omits.
  * A5 correspondence checked against the real callees at base_commit a7e7043c8746933dafce652507d3b821801cdc7d. Read `django/db/migrations/autodetector.py:96-100`: base has `del deconstruction[2]['to']` under `if field.remote_field and field.remote_field.model:`; gold patch replaces exactly that line with `deconstruction[2].pop('to', None)`. So pop_default <-> dict.pop(k,None) and del_present <-> del d[k] both bind to real primitives at the cited lines. Gold patch.diff confirmed to apply at base_commit (`git apply --check` in a throwaway base_commit worktree, since cleaned up) -- the oracle leg is intact.
  * A2 (the leg most likely to hide a gap) examined on its merits: the repo MUTATES deconstruction[2] in place and keeps the same object, whereas the model returns a fresh equal mapping with the input read-only at fractional permission. This is sound here for a specific reason I checked rather than accepted: the only consumer is rename detection, which compares deconstructions BY VALUE, so same-object-vs-equal-fresh-object is unobservable; and the functional phrasing is what keeps the input genuinely read-only, closing the directive-5 vacuity hole. It also does not weaken the spec, since (b)+(c) pin the result against the input pointwise in both directions.
  * A3/A1 spot-checked against the F2P test: test_add_custom_fk_with_hardcoded_to defines a HardcodedForeignKey whose deconstruct() does `del kwargs['to']` while remote_field.model is set -- i.e. is_relation true with TO() absent, precisely the input the spec quantifies over and the prepatch cannot discharge. The modeled domain matches the tested one.

**VERDICT:** SOUND. verify => correct holds for this spec. The postconditions determine the value behaviour in both branches with no domain restriction, 8 admissible distinct wrong impls (prepatch narrow primitive, partial-domain-right-then-wrong-on-the-bug-input, ungrounded fabrication, control-flow-effect x3, over-removal, self-recursive echo) were all rejected by verification, the prepatch reproduces with the documented precondition error, the vacuity control fails as it must, the positive control verifies, and both A-reference primitives are validated == their real Python primitives by an executed G-AX. No verifying wrong impl exists, so no non-resolving faithful patch could be exhibited and no resolve run was owed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.py`, `atk_6_partial_wrongkey.py`, `atk_7_fabricate.py`, `atk_8_postread_flip.py`, `atk_9_doubledrop.py`, `atk_10_selfrec.py`, `atk_11_swapguard.py`, `atk_12_uncond_pop.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_6_partial_wrongkey.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_7_fabricate.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_8_postread_flip.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_9_doubledrop.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_10_selfrec.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_11_swapguard.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_12_uncond_pop.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-15104/nagini. Every file built by copying the shipped model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 12 confirmed `same-spec` exit 0.

**SPEC ANALYSIS.** The postconditions pin Result by value in BOTH branches, so no behavioural freedom remains. Relation branch: (a) is_relation => TO() not in Result; (b) forall j != TO() in kwargs => j in Result and Result[j]==kwargs[j]; (c) forall j in Result => j in kwargs and Result[j]==kwargs[j]. Together: Result == kwargs minus {TO()} EXACTLY. Non-relation branch: (c) + (d) forall j in kwargs => j in Result with same value => Result == kwargs exactly, target keyword included. Crucially (a) is quantified over EVERY admissible input, including a relation field whose kwargs OMIT TO() -- which is exactly the reported bug input -- and there is no precondition restricting the domain. MustTerminate(2) carries total correctness; Acc(dict_pred(kwargs),1/2) keeps the input read-only.

ATTACKS RUN (cmd for each: `python -m swebench_unified.adversary weakness nagini django__django-15104 <path>`; outputs saved as out_<n>.txt beside each attack):
1. atk_1_prepatch.py -- THE PREPATCH BUG, byte-identical to shipped model_prepatch.py (diff empty): relation branch uses the narrow primitive del_present(kwargs,TO()). weakness -> exit 2 'attack does not verify (verification failed)'. Direct `bash scripts/nagini_verify.sh atk_1_prepatch.py` -> 'Verification failed ... atk_1_prepatch.py:152:16: error: The precondition of method del_present might not hold. Assertion (k in d) might not hold.' (34.18s) -- the EXACT error refinement.md B documents. PREPATCH REPRODUCED.
2. atk_6_partial_wrongkey.py -- PARTIAL-DOMAIN: correct via del_present on the TO()-present domain, but drops the WRONG keyword (pop_default(kwargs,1)) on the TO()-absent domain, i.e. exactly the bug input. weakness -> exit 2, verification failed. REJECTED (this is the sharpest partial-domain shape: it is right wherever the prepatch was defined and wrong only where the bug lived).
3. atk_7_fabricate.py -- UNGROUNDED ORACLE: answers from a fabricated local mapping ({TO():0} then del_present) instead of the input, so it satisfies (a) but severs the result from kwargs. weakness -> exit 2, verification failed (postcondition (b) preservation). REJECTED.
4. atk_8_postread_flip.py -- CONTROL-FLOW-EFFECT: computes the correct reduction then returns the UN-reduced kwargs when TO() was present, i.e. removal effective only on inputs that never had the key. weakness -> exit 2, verification failed. REJECTED.
5. atk_9_doubledrop.py -- BOUNDARY/OVER-REMOVAL: drops TO() AND keyword 1. weakness -> exit 2, verification failed (post (b): keyword 1 must survive). REJECTED.
6. atk_10_selfrec.py -- UNGROUNDED-ORACLE ECHO: discharges the postcondition by re-invoking this routine's own contract. weakness -> exit 2, verification failed: MustTerminate(2) offers no smaller measure for a self-call, so the vacuous-recursion hole is closed. REJECTED (confirms the A7 termination leg is load-bearing, not decoration).
7. atk_11_swapguard.py -- CONTROL-FLOW-EFFECT: inverted relation guard. weakness -> exit 2, verification failed. REJECTED.
8. atk_12_uncond_pop.py -- CONTROL-FLOW-EFFECT: guard ignored, removal unconditional. weakness -> exit 2, verification failed (non-relation post (d): TO() must survive). REJECTED.

**NO CANDIDATE EMERGED:** every admissible same-spec attack failed verification (weakness exit 2, verify_completed=True). Therefore NO faithful refined patch had to be materialized and no run_resolve was required -- patches={} is correct here, not an omission. Nothing to check with `git apply --check`.

THREE FURTHER ATTACKS DELIBERATELY EXCLUDED FROM `attacks` (probed nothing; submitting them would force a spurious role-wide INCONCLUSIVE). I attacked the SPEC-VIEW ELISION hole -- markers.py elides the impl region, so a contract smuggled INTO that region survives same-spec -- and Nagini's front end rejects all three before Viper, exit 1 with 'Translation failed' and no Viper banner. Per backends/nagini.py `_no_verdict` -> verify.py `crashed` -> adversary.check_attack these come back verify_completed=False, which build_one.py counts as inconclusive rather than as a rejection; I verified that programmatically (atk_3/atk_5: completed=False). They are real evidence that the hole is closed by the toolchain, but they are NOT evidence of spec strength, so they stay out of the tally:
  - atk_3_impl_requires.py: smuggles `Requires(TO() in kwargs)` into the impl region to make the prepatch del_present dischargeable. -> exit 2, 'no Viper verdict: Translation failed'.
  - atk_4_exsures_raise.py: smuggles `Exsures(KeyError, True)` and raises on the bug input. -> exit 2, 'no Viper verdict'.
  - atk_5_raise_bare.py: raises KeyError on the absent-target relation field (the literal prepatch crash). -> exit 2, 'no Viper verdict: Translation failed'. Note the consequence: Nagini cannot express this rival at all, so the ONLY way the prepatch crash is sensed is the del_present precondition of attack 1 -- and that path does fire correctly.

**NON-VACUITY CONTROL.** atk_2_vacuity_control.py = shipped impl with `Assert(False)` prepended. `bash scripts/nagini_verify.sh` -> exit 1, 'Assert might fail. Assertion False might not hold.' So the precondition set is satisfiable and the verifying attacks/positive control are not passing vacuously (per the guarded-self-call/vacuity lesson).

**POSITIVE CONTROL.** pos_control.py = shipped model.py (diff empty). `bash scripts/nagini_verify.sh pos_control.py` -> 'Verification successful' (33.65s), exit 0.

A-LEG AUDIT (my focus; R/I legs covered by G-CONF). Legs: A1 I, A2 R, A3 R, A4 I, A5 A-reference, A6 I, A7 R. No kind-3 and no A-consumed axiom -- confirmed by reading: the single CHANGED operation (the keyword removal) is modeled DEEPLY as pop_default (post) / del_present (pre), not hidden behind an opaque axiom about the function under change, which is the shape that would make verify-implies-correct unfalsifiable.
  * G-AX executed: `python axiom_check.py` -> exit 0, 'G-AX OK: pop_default (== d.pop(k,None), applicable to any mapping) and del_present (== del d[k], applicable only when k present: raises on absent key) sound on 9 boundary + 20000 fuzz mappings'. It imports only copy/random and plain dict; nothing repo-specific. It asserts BOTH directions of the discriminating fact, including that real `del d[k]` RAISES on an absent key -- which is what licenses del_present's extra Requires(k in d) that pop_default omits.
  * A5 correspondence checked against the real callees at base_commit a7e7043c8746933dafce652507d3b821801cdc7d. Read `django/db/migrations/autodetector.py:96-100`: base has `del deconstruction[2]['to']` under `if field.remote_field and field.remote_field.model:`; gold patch replaces exactly that line with `deconstruction[2].pop('to', None)`. So pop_default <-> dict.pop(k,None) and del_present <-> del d[k] both bind to real primitives at the cited lines. Gold patch.diff confirmed to apply at base_commit (`git apply --check` in a throwaway base_commit worktree, since cleaned up) -- the oracle leg is intact.
  * A2 (the leg most likely to hide a gap) examined on its merits: the repo MUTATES deconstruction[2] in place and keeps the same object, whereas the model returns a fresh equal mapping with the input read-only at fractional permission. This is sound here for a specific reason I checked rather than accepted: the only consumer is rename detection, which compares deconstructions BY VALUE, so same-object-vs-equal-fresh-object is unobservable; and the functional phrasing is what keeps the input genuinely read-only, closing the directive-5 vacuity hole. It also does not weaken the spec, since (b)+(c) pin the result against the input pointwise in both directions.
  * A3/A1 spot-checked against the F2P test: test_add_custom_fk_with_hardcoded_to defines a HardcodedForeignKey whose deconstruct() does `del kwargs['to']` while remote_field.model is set -- i.e. is_relation true with TO() absent, precisely the input the spec quantifies over and the prepatch cannot discharge. The modeled domain matches the tested one.

**VERDICT:** SOUND. verify => correct holds for this spec. The postconditions determine the value behaviour in both branches with no domain restriction, 8 admissible distinct wrong impls (prepatch narrow primitive, partial-domain-right-then-wrong-on-the-bug-input, ungrounded fabrication, control-flow-effect x3, over-removal, self-recursive echo) were all rejected by verification, the prepatch reproduces with the documented precondition error, the vacuity control fails as it must, the positive control verifies, and both A-reference primitives are validated == their real Python primitives by an executed G-AX. No verifying wrong impl exists, so no non-resolving faithful patch could be exhibited and no resolve run was owed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**FAITHFULNESS-BREAK ATTACK:** no divergence found between the modelled function and the real (patch-APPLIED) callee. Reference built correctly: fresh clone of the upstream repository at base_commit a7e7043c8746933dafce652507d3b821801cdc7d, with the gold patch (del deconstruction[2]['to'] -> deconstruction[2].pop('to', None) at autodetector.py:99) applied cleanly.

**SPEC INTEGRITY:** same-spec on model.py => SAME (exit 0). model_prepatch.py also SAME (exit 0); the only byte difference across the whole file is impl line 152 (pop_default vs del_present), spec regions diff-clean.

### MECHANICAL EVIDENCE (all green):
1. nagini_verify.sh model.py => exit 0 (verifies).
2. G-DIFF control: nagini_verify.sh model_prepatch.py => FAILS with 'model_prepatch.py:152: The precondition of method del_present might not hold. Assertion (k in d) might not hold' (34s). The spec genuinely senses the change; it is not vacuous.
3. axiom_check.py (G-AX) => exit 0. Validates BOTH A-reference deep models against real Python: d.pop(k,None) total, and del d[k] RAISING on absent key (both arms asserted) over 9 boundary + 20000 fuzz mappings. The axioms model unchanged language primitives, correctly referenced to base behavior.
4. conformance_check.py against the PATCHED worktree => exit 0, 100027 field inputs (27 boundary + 100000 fuzz), 0 disagreements.

INDEPENDENT PROBES I WROTE (beyond the bundle's own harnesses), asserting each Ensures of reduce_to_relation_agnostic directly against the REAL patched MigrationAutodetector.only_relation_agnostic_fields using REAL django Field objects rather than the bundle's duck-typed fakes:
- 9 real-field cases (ForeignKey, OneToOneField, ManyToManyField, CharField, IntegerField, self-referential FK, FK with related_name/null/db_index, the HardcodedFK from the gold test, and a relation field injecting extra kwargs while dropping 'to'). All four Ensures held; exit 0.
- 5 adversarial edge shapes chosen to attack the is_relation abstraction and the 'to'-survives clause: (a) truthy remote_field whose .model is None WITH 'to' present in kwargs -> guard False, real callee keeps 'to', matching Implies(not is_relation, everything survives); (b) relation field with 8 kwargs incl. falsy values (None/False/0/'') and a decoy key 'to_x' -> only 'to' dropped, 'to_x' and all falsy values preserved; (c) relation FK with falsy to='' -> dropped (confirms membership-not-truthiness, matching the model's k not in Result()); (d) plain non-relation field with a 'to' kwarg -> 'to' survives; (e) m2m through=None. All Ensures held; exit 0.

Oracle delta confirmed real (so the FAITHFUL verdict is not resting on a no-op patch): the FAIL_TO_PASS test test_add_custom_fk_with_hardcoded_to passes on the patched tree and fails with the exact reported 'KeyError: to' when I reverted line 99 to the base impl.

R-REFINEMENT SCRUTINY (the one place unfaithfulness could hide): the model is functional (returns a fresh mapping, kwargs read-only at 1/2 permission) while the real code mutates deconstruction[2] in place. I checked this is not an over-idealization. deep_deconstruct (autodetector.py:80-84) builds the kwargs dict via a fresh dict comprehension on every call, so the mutated dict is never aliased or cached -- no other holder can observe the in-place edit. Both call sites (autodetector.py:477 and :483) consume the result only through the value comparison 'if model_fields_def == rem_model_fields_def:' (:484), so same-object-vs-equal-fresh-object is observationally identical for everything the caller observes. The Dict[int,int] carrier is also sound: the operation only ever tests key membership and per-key value equality, never indexes/iterates keys as strings.

**SPEC STRENGTH:** the postcondition is not too strong. It is exactly two-sided (every non-TO input key preserved with its value; no key introduced; TO absent iff is_relation) and the non-relation branch pins the input through unchanged. It does not over-constrain -- it says nothing about ordering, object identity, or the args/path components the real callee also returns, all of which the patch leaves alone. MustTerminate(2)/(1) is a legitimate total-correctness obligation matching a straight-line body, not smuggled strength.

**Conclusion:** the spec describes the post-patch behavior and agrees with the real patched callee on every input I could construct, including the bug-triggering relation-field-without-'to' shape. No diverging input exists to cite. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** G-PANEL attacker 3 (leakage / gold-reconstruction) for django__django-15104/nagini.

**RELAXATION STATUS:** none claimed. `find -iname '*RELAX*'` over the instance dir returns nothing, and meta.json has no `relaxed_leakage` key (keys: axioms, base_commit, changed_files, deep_model_references, dict_modeling, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version). So this is judged as an ordinary strict-leakage review, not a documented relaxation. Also grepped model.py / refinement.md / mapping.md / axiom_check.py / conformance_check.py / verdict.md / meta.json for reviewer-addressed text (G-PANEL, attacker, 'the honest verdict', 'submit NO-LEAKAGE/LEAKAGE', 'record ...'): the ONLY hit is refinement.md:37, which cites `G-PANEL-1` descriptively to justify the MustTerminate obligation ('a diverging or self-recursive impl would satisfy every Ensures vacuously (a G-PANEL-1 counterexample)'). That is a rationale for a contract clause, not an instruction to a reviewer and not addressed at me. Nothing in the bundle tells me what to submit.

### WHAT I MEASURED (spec view, exactly what a consumer sees):
- Regenerated the consumer view myself: `markers.spec_view(model.py, get_backend('nagini'))` -> specview.txt. impl region is correctly elided to `...  # implementation elided — supplied by the consumer`; docstring + axioms + pure + pre/post-conditions are the visible surface.
- `markers.same_spec(model.py, model_prepatch.py, nagini)` = True; `python -m swebench_unified.adversary same-spec nagini django__django-15104 atk.py` (gold copy) -> exit 0, 'SAME — attack shares the bundle's exact specification'. So the spec region is byte-identical across the twins and the only difference is impl line 152 (`pop_default` vs `del_present`), confirmed by direct diff.

**PUBLIC BASELINE:** the problem_statement for this instance is maximally explicit and already contains every discriminating fact, verbatim. It carries the full traceback ending `File "django/db/migrations/autodetector.py", line 99 ... del deconstruction[2]['to'] / KeyError: 'to'`, names the enclosing function `only_relation_agnostic_fields`, gives a self-contained repro whose CustomFKField does `del kwargs["to"]` in `deconstruct()` (i.e. the relation field whose deconstruction omits the target keyword), and states the gold edit in the reporter's own words: "Changing del deconstruction[2]['to'] to deconstruction[2].pop('to', None) on the line indicated by the traceback makes my test suite run again." hints_text is empty (length 0), so no hints reliance is possible either way.

LINE-BY-LINE against that baseline. I ran a leak-vocabulary sweep over the spec view ('patch','fix','bug','gold','pop(','pop_default','del d[','KeyError','pre-patch','post-patch','regress','ticket','15104','autodetector','deconstruct','remote_field','broadly',...) and adjudicated every hit:
- L5-L12 'must DROP the related-target keyword ... applicable to EVERY input mapping ... including a mapping that does not carry the target keyword at all (a relation field whose deconstruction legitimately omits it). The reduction must never be undefined on such an input.' -> this IS the reported bug as stated publicly. Derivable from problem_statement alone.
- L35/L38/L81 `pop_default` (applicable to any mapping) and L56 `del_present` (`Requires(k in d)`) -> the two primitives are `dict.pop(k, None)` and `del d[k]`, both spelled out in the problem_statement's closing sentence. Naming them leaks nothing the reporter did not publish.
- L66 'The real `del d[k]`', L90 'The real `d.pop(k, None)`' -> same, both public; and these are measure justifications on MustTerminate, not statements about which one the impl picks.
- L1 '15104', L5/L11/L24/L31 'deconstructed/deconstruction' -> instance id and the public vocabulary of the traceback.
- TO() == 0 <-> 'to' -> the key name is in the traceback and the repro.
- The MustTerminate narration (L40-L45, L2xx pre-conditions comment) is proof-technique rationale (partial vs total correctness), orthogonal to the gold edit.
No line in the spec view names, implies, or narrows toward the gold edit beyond what problem_statement already states outright. I found no candidate leaking line, so `leaking_line` is empty.

LOAD-BEARING CHECK (the strip test, run even though no relaxation was claimed, to confirm discrimination lives in the formal contract rather than in prose that could be read as a hint): I copied both twins to, deleted the ENTIRE module docstring from each (replaced with `"""m."""`), and ran the pinned verifier.
  - `bash scripts/nagini_verify.sh stripped_prepatch.py` -> FAILS, exit 1, 29.61s: 'stripped_prepatch.py:105:16:105:41: error: The precondition of method del_present might not hold. Assertion (k in d) might not hold.'
  - `bash scripts/nagini_verify.sh stripped_post.py` -> 'Verification successful', exit 0, 30.90s (control).
So with ALL narration removed the spec still rejects the pre-patch impl and admits the gold one: the discriminator is carried by `del_present`'s `Requires(k in d)` against `Ensures(Implies(is_relation, TO() not in Result()))` for an input where TO() is absent, i.e. formal contract, not prose. The prose is descriptive only, and independently is fully covered by the public problem_statement.

**GATE CONTEXT:** meta.json gates read G-AX pass, G-CONF pass, G-DIFF pass, G-EQ pass, G-GOLD pass, G-HYGIENE pass, G-INTEGRITY pass, G-LEAK pass, G-PBT pass, G-RESOLVE pass, G-VERIFY pass (G-MUT skip). My own re-runs above (same-spec exit 0, prepatch fails / post verifies under narration strip) are consistent with G-DIFF and G-VERIFY, so nothing in the disposition rests on an unsound gate I relied on.

**VERDICT:** NO-LEAKAGE. The spec view's every arguably-discriminating clause is a restatement of the public problem_statement, which itself names the gold one-liner; and the discrimination is anchored in the formal pre/post-conditions, verified above.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
