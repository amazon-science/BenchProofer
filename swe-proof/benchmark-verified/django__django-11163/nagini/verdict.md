# P2 adversarial audit — django__django-11163

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch.py`, `atk_2_selfcall_entry.py`, `atk_3_selfcall_loop_measure.py`, `atk_4_selfcall_in_main_loop.py`, `atk_5_empty_removal_removes_all.py`, `atk_6_off_by_one_first_attr.py`, `atk_7_reversed_order.py`, `atk_8_dedup_multiplicity.py`, `atk_9_while_true_diverge.py`, `atk_10_total_echo.py`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_15_vacuous_guard_echo.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 16 same-spec attacks run; 15 were REJECTED by the spec with semantic errors, and the single CANDIDATE (atk_15) is behaviourally gold, whose faithful refined patch RESOLVES under the official harness (FAIL_TO_PASS 1/1 pass, resolved=True, completed=True). The prior pass's recorded counterexample (atk_10_diverge_on_empty, a guarded unbounded self-delegation exploiting the then-absent termination obligation) is re-encoded here as atk_2_selfcall_entry and is now REJECTED: 'Obligation leak check failed. Callee project_record might not take all unsatisfied obligations from the caller.' The recommended repair (method-level Requires(MustTerminate(2)) + Invariant(MustTerminate(i))) is present in the frozen model.py (MustTerminate count 3) and demonstrably closes the hole.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -150,7 +150,10 @@
         Assert(ToSeq(edit).drop(i - 1)[0] == e)
         Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
-        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
+        # PRE-PATCH BUG: truthiness gating on the restriction list, so a
+        # present-but-empty restriction list imposes no restriction.
+        keep_restr = allowed is None or len(allowed) == 0 or contains(ToSeq(allowed), n)
+        if e != 0 and keep_restr and not is_removed(blocked, n):
             result = [n] + result
         i = i - 1
     return result
```

Attack 2 — `atk_2_selfcall_entry.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,6 +127,10 @@
     Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked))
     # post-conditions-end
     # impl-start
+    # ATTACK: surgical partial-correctness divergence on the present-but-
+    # empty restriction list -- unbounded self-delegation.
+    if allowed is not None and len(allowed) == 0:
+        return project_record(names, edit, allowed, blocked)
     result = []  # type: List[int]
     i = len(names)
     while i > 0:
```

Attack 3 — `atk_3_selfcall_loop_measure.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,6 +128,24 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    # ATTACK: probe whether a call's MustTerminate measure is checked against
+    # the enclosing LOOP measure (5) rather than the METHOD measure (2). If it
+    # were, this unbounded self-recursion would be admitted and no result is
+    # ever delivered for a present-but-empty restriction list.
+    if allowed is not None and len(allowed) == 0:
+        j = 5
+        while j > 0:
+            Invariant(Acc(list_pred(names), 1 / 2))
+            Invariant(Acc(list_pred(edit), 1 / 2))
+            Invariant(len(names) == len(edit))
+            Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
+            Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= j and j <= 5)
+            Invariant(MustTerminate(j))
+            result = project_record(names, edit, allowed, blocked)
+            j = j - 1
+        return result
     i = len(names)
     while i > 0:
         # invariants-start
```

Attack 4 — `atk_4_selfcall_in_main_loop.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -144,6 +144,11 @@
         # strictly decreasing, bounded-below measure i.
         Invariant(MustTerminate(i))
         # invariants-end
+        # ATTACK: inside the main loop the obligation measure is i; a call
+        # requiring MustTerminate(2) may be admitted whenever 2 < i, which
+        # licenses unbounded self-recursion on records of >= 3 attributes.
+        if i > 2 and allowed is not None and len(allowed) == 0:
+            return project_record(names, edit, allowed, blocked)
         n = names[i - 1]
         e = edit[i - 1]
         Assert(ToSeq(names).drop(i - 1)[0] == n)
```

Attack 5 — `atk_5_empty_removal_removes_all.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -150,7 +150,10 @@
         Assert(ToSeq(edit).drop(i - 1)[0] == e)
         Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
-        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
+        # ATTACK: the removal filter is read under PRESENCE instead of
+        # truthiness, so a present-but-empty removal list removes every name.
+        removed = blocked is not None and (len(blocked) == 0 or contains(ToSeq(blocked), n))
+        if e != 0 and passes_restriction(allowed, n) and not removed:
             result = [n] + result
         i = i - 1
     return result
```

Attack 6 — `atk_6_off_by_one_first_attr.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -129,7 +129,7 @@
     # impl-start
     result = []  # type: List[int]
     i = len(names)
-    while i > 0:
+    while i > 1:  # ATTACK: off-by-one, the first attribute is never considered
         # invariants-start
         Invariant(Acc(list_pred(names), 1 / 2))
         Invariant(Acc(list_pred(edit), 1 / 2))
```

Attack 7 — `atk_7_reversed_order.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -151,7 +151,7 @@
         Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
         if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
-            result = [n] + result
+            result = result + [n]  # ATTACK: backward loop + append => reversed order
         i = i - 1
     return result
     # impl-end
```

Attack 8 — `atk_8_dedup_multiplicity.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -150,7 +150,9 @@
         Assert(ToSeq(edit).drop(i - 1)[0] == e)
         Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
-        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
+        # ATTACK: multiplicity dropped -- a repeated surviving name is kept once.
+        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n) \
+                and not contains(ToSeq(result), n):
             result = [n] + result
         i = i - 1
     return result
```

Attack 9 — `atk_9_while_true_diverge.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -128,6 +128,22 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    spin = 0
+    # ATTACK: partial-domain DIVERGENCE. On a present-but-empty restriction
+    # list this loop never exits, so no result is ever DELIVERED on exactly the
+    # input the gold hunk exists to fix; the value postcondition would then be
+    # discharged vacuously there. The loop carries NO MustTerminate measure.
+    if allowed is not None and len(allowed) == 0:
+        while spin >= 0:
+            Invariant(Acc(list_pred(names), 1 / 2))
+            Invariant(Acc(list_pred(edit), 1 / 2))
+            Invariant(len(names) == len(edit))
+            Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
+            Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
+            Invariant(Acc(list_pred(result)))
+            Invariant(spin >= 0)
+            spin = spin + 1
+        return result
     i = len(names)
     while i > 0:
         # invariants-start
```

Attack 10 — `atk_10_total_echo.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,31 +127,8 @@
     Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = len(names)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(names), 1 / 2))
-        Invariant(Acc(list_pred(edit), 1 / 2))
-        Invariant(len(names) == len(edit))
-        Invariant(Implies(allowed is not None, Acc(list_pred(allowed), 1 / 2)))
-        Invariant(Implies(blocked is not None, Acc(list_pred(blocked), 1 / 2)))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(names))
-        Invariant(ToSeq(result) ==
-                  projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        n = names[i - 1]
-        e = edit[i - 1]
-        Assert(ToSeq(names).drop(i - 1)[0] == n)
-        Assert(ToSeq(edit).drop(i - 1)[0] == e)
-        Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
-        Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
-        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
-            result = [n] + result
-        i = i - 1
-    return result
+    # ATTACK: ungrounded oracle echo -- the impl establishes nothing and simply
+    # re-asserts the contract by delegating to itself; it never delivers a
+    # result on ANY input.
+    return project_record(names, edit, allowed, blocked)
     # impl-end
```

Attack 11 — `atk_11_empty_treated_as_absent.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,6 +127,12 @@
     Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked))
     # post-conditions-end
     # impl-start
+    # ATTACK: partial-domain wrong value. Byte-for-byte the gold projection on
+    # every input EXCEPT a present-but-empty restriction list, where it echoes
+    # the editable names (the pre-patch leak) narrowed to the single input the
+    # gold hunk concerns.
+    if allowed is not None and len(allowed) == 0:
+        return project_record(names, edit, None, blocked)
     result = []  # type: List[int]
     i = len(names)
     while i > 0:
```

Attack 12 — `atk_12_editable_inverted.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -150,7 +150,9 @@
         Assert(ToSeq(edit).drop(i - 1)[0] == e)
         Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
-        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
+        # ATTACK: the editability filter is inverted -- only NON-editable
+        # attributes survive.
+        if e == 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
             result = [n] + result
         i = i - 1
     return result
```

Attack 13 — `atk_13_lists_swapped.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -150,7 +150,8 @@
         Assert(ToSeq(edit).drop(i - 1)[0] == e)
         Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
-        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
+        # ATTACK: the restriction and removal roles are swapped.
+        if e != 0 and passes_restriction(blocked, n) and not is_removed(allowed, n):
             result = [n] + result
         i = i - 1
     return result
```

Attack 14 — `atk_14_early_return_first_survivor.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -152,6 +152,9 @@
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
         if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
             result = [n] + result
+            # ATTACK: control-flow effect -- bail out after the first survivor,
+            # so at most one name is ever projected.
+            return result
         i = i - 1
     return result
     # impl-end
```

Attack 15 — `atk_15_vacuous_guard_echo.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -127,6 +127,11 @@
     Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked))
     # post-conditions-end
     # impl-start
+    # ATTACK: ungrounded oracle echo behind an INFEASIBLE guard. The guard can
+    # never hold, so the self-call proves nothing, but if the verifier admitted
+    # the echo on a feasible guard the same shape would break the spec.
+    if len(names) != len(edit):
+        return project_record(names, edit, allowed, blocked)
     result = []  # type: List[int]
     i = len(names)
     while i > 0:
```

Attack 16 — `atk_16_absent_treated_as_empty.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -150,7 +150,10 @@
         Assert(ToSeq(edit).drop(i - 1)[0] == e)
         Assert(ToSeq(names).drop(i - 1).drop(1) == ToSeq(names).drop(i))
         Assert(ToSeq(edit).drop(i - 1).drop(1) == ToSeq(edit).drop(i))
-        if e != 0 and passes_restriction(allowed, n) and not is_removed(blocked, n):
+        # ATTACK: dual boundary -- an ABSENT restriction list is treated as an
+        # empty one, so it lets nothing through instead of everything.
+        keep_restr = allowed is not None and contains(ToSeq(allowed), n)
+        if e != 0 and keep_restr and not is_removed(blocked, n):
             result = [n] + result
         i = i - 1
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of django__django-11163/nagini. Attack verifications were run as concurrent background Bash jobs, at most 3 at a time (each Nagini check spawns a JVM+Z3); this changed only the schedule, every attack was fully verified.

**POSITIVE CONTROL:** control.py = byte-verbatim bundle model.py. `bash scripts/nagini_verify.sh.../control.py` -> 'Verification successful', 25.70s, exit 0. same-spec exit 0.

**SAME-SPEC:** all 16 attacks + control returned exit 0 ('SAME — attack shares the bundle's exact specification') from `python -m swebench_unified.adversary same-spec nagini django__django-11163 <file>`. Only the impl region was edited; axioms/@Pure/Requires/Ensures byte-identical.

**PER-ATTACK RESULTS.** Command for each: `python -m swebench_unified.adversary weakness nagini django__django-11163 <path>` (exit 2 = not a counterexample, exit 0 = CANDIDATE); reasons obtained with `... adversary verify nagini django__django-11163 <path>`.

1. atk_1_prepatch.py — THE PREPATCH BUG REPRODUCED. Truthiness gating (allowed is None or len(allowed)==0 or contains(...)). weakness exit 2; FAILED 74.7s: 'Loop invariant might not be preserved. Assertion (ToSeq(result) == projection(...)) might not hold.' The spec senses the change (G-DIFF).
2. atk_2_selfcall_entry.py — PRIOR PASS'S COUNTEREXAMPLE re-encoded: guarded (allowed is not None and len(allowed)==0) unbounded self-delegation ahead of the gold loop. weakness exit 2; FAILED 23.6s: 'Obligation leak check failed. Callee project_record might not take all unsatisfied obligations from the caller.' NOW REJECTED by the method-level MustTerminate.
3. atk_3_selfcall_loop_measure.py — probes whether a call's measure is checked against an enclosing LOOP measure (fresh bounded loop, MustTerminate(j), j=5) instead of the METHOD measure (2). weakness exit 2; FAILED 22.7s: obligation leak check failed at the self-call. (First build of this file died on a Python IndentationError — not evidence; rebuilt, syntax-verified, and re-run.)
4. atk_4_selfcall_in_main_loop.py — self-delegation from inside the main loop guarded on i > 2, betting 2 < i licenses the call. weakness exit 2; FAILED 31.9s: obligation leak check failed.
5. atk_5_empty_removal_removes_all.py — BOUNDARY on the OTHER optional list: removal read under presence instead of truthiness, so exclude=[] removes everything. weakness exit 2; FAILED 55.6s: loop invariant not preserved.
6. atk_6_off_by_one_first_attr.py — PARTIAL DOMAIN: `while i > 1`, first attribute never considered. weakness exit 2; FAILED 53.8s: 'Postcondition of project_record might not hold.'
7. atk_7_reversed_order.py — order violation: backward loop + append => reversed. weakness exit 2; FAILED 47.6s: loop invariant not preserved.
8. atk_8_dedup_multiplicity.py — multiplicity dropped (dedup via contains on result). weakness exit 2; FAILED 42.4s: loop invariant not preserved.
9. atk_9_while_true_diverge.py — CONTROL-FLOW EFFECT / totality: on allowed present-and-empty a measure-less loop `while spin >= 0` never exits, so nothing is DELIVERED on exactly the discriminating input. weakness exit 2; FAILED 19.8s: 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' (Two earlier builds died on a Python IndentationError and then a Nagini redeclaration type error — neither counted as evidence; rebuilt until the verifier reached a real semantic verdict.)
10. atk_10_total_echo.py — UNGROUNDED ORACLE ECHO, total: impl is just `return project_record(names, edit, allowed, blocked)`. weakness exit 2; FAILED 38.8s: obligation leak check failed.
11. atk_11_empty_treated_as_absent.py — surgical partial-domain wrong value: on allowed present-and-empty, delegate with allowed=None (the prepatch leak) narrowed to the single discriminating input. weakness exit 2; FAILED 21.0s: obligation leak check failed.
12. atk_12_editable_inverted.py — editability filter inverted (e == 0). weakness exit 2; FAILED 69.5s: loop invariant not preserved.
13. atk_13_lists_swapped.py — the two optional lists' roles swapped. weakness exit 2; FAILED 69.5s: loop invariant not preserved.
14. atk_14_early_return_first_survivor.py — CONTROL-FLOW EFFECT: return after the first survivor. weakness exit 2; FAILED 72.7s: 'Postcondition of project_record might not hold.'
15. atk_15_vacuous_guard_echo.py — CANDIDATE (weakness exit 0, 'shares spec AND verifies', 32.3s; verify VERIFIED 27.0s). Echo behind the guard `len(names) != len(edit)`. Per protocol its FAITHFUL REFINED PATCH WAS MATERIALIZED (patch_atk_15.diff, built against the base blob of django/forms/models.py at e6588aa4e793b7f56f4cadbfa155b581e0efc59a: same infeasible length guard + self-delegation, ahead of the gold-fixed `fields is not None` loop) and RUN THROUGH THE OFFICIAL HARNESS via swebench_unified.harness.run_resolve. OBSERVED RESULT: resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS success=['test_modelform_subclassed_model (model_forms.tests.ModelOneToOneFieldTests)'] failure=[]. So this CANDIDATE does NOT break the spec — verify AND correct. Why it verifies without proving anything: the guard is INFEASIBLE under Requires(len(names) == len(edit)). Confirmed with the Assert(False) control per the known trap (atk_15b_guard_infeasible_control.py): inserting Assert(False) into the guarded branch still VERIFIES (36.3s), proving the branch is dead — so the echo is unreachable and the impl is the gold loop. This is the expected 'guarded self-call can go vacuous' shape, not spec weakness.
16. atk_16_absent_treated_as_empty.py — DUAL BOUNDARY: an ABSENT restriction list treated as empty (lets nothing through). weakness exit 2; FAILED 43.4s: loop invariant not preserved.

**WHY THE SPEC HOLDS.** Two obligations do the work together. (a) The VALUE clause Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked)) pins the exact per-attribute projection, killing every wrong-value rival (atk_1, 5, 6, 7, 8, 12, 13, 14, 16) at either the loop invariant or the postcondition. (b) The TOTALITY obligation Requires(MustTerminate(2)) at the METHOD level, discharged by Invariant(MustTerminate(i)), kills every divergence/vacuity rival (atk_2, 3, 4, 9, 10, 11) via Nagini's obligation-leak check. Per the known trap, it is the method-level Requires — not the loop invariant alone — that rejects a diverging rival; this bundle has both (MustTerminate appears 3x). That closes precisely the hole the prior pass recorded.

REFINEMENT.MD LEG AUDIT (A legs, the focus): 9 legs, tags A1=R, A2=R, A3=R+I, A4=A-reference, A5=A-reference+I, A6=R+I, A7=R, A8=A-reference, A9=R+I. Every leg is R / A-reference / I — NO KIND-3 (no unexpressible-changed-op), and NO A-consumed leg exists: the axioms region is genuinely empty (repr '\n', ContractOnly count 0), so there is no axiom-soundness trust point at all; the changed operation is modelled deeply.

**A-LEG CORRESPONDENCE INDEPENDENTLY CHECKED.** I did not take axiom_check.py's word. indep_aleg_check.py transcribes BOTH the real post-patch loop (from the base blob at e6588aa4 plus patch.diff, read directly out of the upstream repository) AND model.py's pure region MYSELF, then tests each A-reference leg: A4 (passes_restriction == 'kept by `if fields is not None and f.name not in fields: continue`', the De-Morgan equivalence, over allowed in {None, [], subsets, dups, absent codes}); A5 (is_removed == the unchanged truthiness-gated `if exclude and f.name in exclude`); A8 (projection == the real loop's key SEQUENCE in source order, carrying A1/A3/A6/A7 with it) over 256,960 configurations (exhaustive small sweep + 4000 fuzz records x 8 restriction x 8 removal options); A9 (the real post-patch helper DELIVERS on every admissible input incl. fields=[]); plus the four F2P assertions from the test patch in model terms.

Result: exit 0, 'ALL A-LEGS HOLD', zero mismatches. The A4/A5 asymmetry that the whole instance turns on — restriction gated by PRESENCE, removal gated by TRUTHINESS — is faithfully carried, and A9's totality claim is true of the real function on its whole domain, not just the gold path.

**BUNDLE CHECKS RE-RUN:** axiom_check.py exit 0 (honest — it reconstructs the post-patch loop verbatim over FakeField, no DB/settings, and confirms the prepatch loop diverges on exactly the present-empty restriction list).

**NO HOST-SATURATION OR LAUNCH ARTIFACTS:** every one of the 16 weakness runs and the resolve run reached a real verdict. No verifier timeouts, no 'inconclusive', no crashes. The three builds that initially failed on Python/Nagini syntax or redeclaration errors (atk_3, atk_9) were NOT scored as spec rejections — they were rebuilt, syntax-verified with compile(), and re-run until the verifier produced a genuine semantic verdict. Per the known trap, no echo or timeout was re-judged into the reject lane: the one attack that verified (atk_15) was carried all the way through a real run_resolve rather than being speculated about.

**VERDICT:** SOUND. 16 same-spec wrong-impl attacks run (>= 5 required), including the prepatch bug and the prior pass's named counterexample; 15 rejected with semantic errors; the sole CANDIDATE's materialized faithful patch RESOLVES under the official harness, so no verifying wrong impl exists. verify => correct is not refuted here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch.py`, `atk_2_selfcall_entry.py`, `atk_3_selfcall_loop_measure.py`, `atk_4_selfcall_in_main_loop.py`, `atk_5_empty_removal_removes_all.py`, `atk_6_off_by_one_first_attr.py`, `atk_7_reversed_order.py`, `atk_8_dedup_multiplicity.py`, `atk_9_while_true_diverge.py`, `atk_10_total_echo.py`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_15_vacuous_guard_echo.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 16 same-spec attacks run; 15 were REJECTED by the spec with semantic errors, and the single CANDIDATE (atk_15) is behaviourally gold, whose faithful refined patch RESOLVES under the official harness (FAIL_TO_PASS 1/1 pass, resolved=True, completed=True). The prior pass's recorded counterexample (atk_10_diverge_on_empty, a guarded unbounded self-delegation exploiting the then-absent termination obligation) is re-encoded here as atk_2_selfcall_entry and is now REJECTED: 'Obligation leak check failed. Callee project_record might not take all unsatisfied obligations from the caller.' The recommended repair (method-level Requires(MustTerminate(2)) + Invariant(MustTerminate(i))) is present in the frozen model.py (MustTerminate count 3) and demonstrably closes the hole.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_selfcall_entry.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_selfcall_loop_measure.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_selfcall_in_main_loop.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_empty_removal_removes_all.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_off_by_one_first_attr.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_reversed_order.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_dedup_multiplicity.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_while_true_diverge.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_total_echo.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_empty_treated_as_absent.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_editable_inverted.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_lists_swapped.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_early_return_first_survivor.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_vacuous_guard_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 16 — `atk_16_absent_treated_as_empty.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of django__django-11163/nagini. Attack verifications were run as concurrent background Bash jobs, at most 3 at a time (each Nagini check spawns a JVM+Z3); this changed only the schedule, every attack was fully verified.

**POSITIVE CONTROL:** control.py = byte-verbatim bundle model.py. `bash scripts/nagini_verify.sh.../control.py` -> 'Verification successful', 25.70s, exit 0. same-spec exit 0.

**SAME-SPEC:** all 16 attacks + control returned exit 0 ('SAME — attack shares the bundle's exact specification') from `python -m swebench_unified.adversary same-spec nagini django__django-11163 <file>`. Only the impl region was edited; axioms/@Pure/Requires/Ensures byte-identical.

**PER-ATTACK RESULTS.** Command for each: `python -m swebench_unified.adversary weakness nagini django__django-11163 <path>` (exit 2 = not a counterexample, exit 0 = CANDIDATE); reasons obtained with `... adversary verify nagini django__django-11163 <path>`.

1. atk_1_prepatch.py — THE PREPATCH BUG REPRODUCED. Truthiness gating (allowed is None or len(allowed)==0 or contains(...)). weakness exit 2; FAILED 74.7s: 'Loop invariant might not be preserved. Assertion (ToSeq(result) == projection(...)) might not hold.' The spec senses the change (G-DIFF).
2. atk_2_selfcall_entry.py — PRIOR PASS'S COUNTEREXAMPLE re-encoded: guarded (allowed is not None and len(allowed)==0) unbounded self-delegation ahead of the gold loop. weakness exit 2; FAILED 23.6s: 'Obligation leak check failed. Callee project_record might not take all unsatisfied obligations from the caller.' NOW REJECTED by the method-level MustTerminate.
3. atk_3_selfcall_loop_measure.py — probes whether a call's measure is checked against an enclosing LOOP measure (fresh bounded loop, MustTerminate(j), j=5) instead of the METHOD measure (2). weakness exit 2; FAILED 22.7s: obligation leak check failed at the self-call. (First build of this file died on a Python IndentationError — not evidence; rebuilt, syntax-verified, and re-run.)
4. atk_4_selfcall_in_main_loop.py — self-delegation from inside the main loop guarded on i > 2, betting 2 < i licenses the call. weakness exit 2; FAILED 31.9s: obligation leak check failed.
5. atk_5_empty_removal_removes_all.py — BOUNDARY on the OTHER optional list: removal read under presence instead of truthiness, so exclude=[] removes everything. weakness exit 2; FAILED 55.6s: loop invariant not preserved.
6. atk_6_off_by_one_first_attr.py — PARTIAL DOMAIN: `while i > 1`, first attribute never considered. weakness exit 2; FAILED 53.8s: 'Postcondition of project_record might not hold.'
7. atk_7_reversed_order.py — order violation: backward loop + append => reversed. weakness exit 2; FAILED 47.6s: loop invariant not preserved.
8. atk_8_dedup_multiplicity.py — multiplicity dropped (dedup via contains on result). weakness exit 2; FAILED 42.4s: loop invariant not preserved.
9. atk_9_while_true_diverge.py — CONTROL-FLOW EFFECT / totality: on allowed present-and-empty a measure-less loop `while spin >= 0` never exits, so nothing is DELIVERED on exactly the discriminating input. weakness exit 2; FAILED 19.8s: 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' (Two earlier builds died on a Python IndentationError and then a Nagini redeclaration type error — neither counted as evidence; rebuilt until the verifier reached a real semantic verdict.)
10. atk_10_total_echo.py — UNGROUNDED ORACLE ECHO, total: impl is just `return project_record(names, edit, allowed, blocked)`. weakness exit 2; FAILED 38.8s: obligation leak check failed.
11. atk_11_empty_treated_as_absent.py — surgical partial-domain wrong value: on allowed present-and-empty, delegate with allowed=None (the prepatch leak) narrowed to the single discriminating input. weakness exit 2; FAILED 21.0s: obligation leak check failed.
12. atk_12_editable_inverted.py — editability filter inverted (e == 0). weakness exit 2; FAILED 69.5s: loop invariant not preserved.
13. atk_13_lists_swapped.py — the two optional lists' roles swapped. weakness exit 2; FAILED 69.5s: loop invariant not preserved.
14. atk_14_early_return_first_survivor.py — CONTROL-FLOW EFFECT: return after the first survivor. weakness exit 2; FAILED 72.7s: 'Postcondition of project_record might not hold.'
15. atk_15_vacuous_guard_echo.py — CANDIDATE (weakness exit 0, 'shares spec AND verifies', 32.3s; verify VERIFIED 27.0s). Echo behind the guard `len(names) != len(edit)`. Per protocol its FAITHFUL REFINED PATCH WAS MATERIALIZED (patch_atk_15.diff, built against the base blob of django/forms/models.py at e6588aa4e793b7f56f4cadbfa155b581e0efc59a: same infeasible length guard + self-delegation, ahead of the gold-fixed `fields is not None` loop) and RUN THROUGH THE OFFICIAL HARNESS via swebench_unified.harness.run_resolve. OBSERVED RESULT: resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS success=['test_modelform_subclassed_model (model_forms.tests.ModelOneToOneFieldTests)'] failure=[]. So this CANDIDATE does NOT break the spec — verify AND correct. Why it verifies without proving anything: the guard is INFEASIBLE under Requires(len(names) == len(edit)). Confirmed with the Assert(False) control per the known trap (atk_15b_guard_infeasible_control.py): inserting Assert(False) into the guarded branch still VERIFIES (36.3s), proving the branch is dead — so the echo is unreachable and the impl is the gold loop. This is the expected 'guarded self-call can go vacuous' shape, not spec weakness.
16. atk_16_absent_treated_as_empty.py — DUAL BOUNDARY: an ABSENT restriction list treated as empty (lets nothing through). weakness exit 2; FAILED 43.4s: loop invariant not preserved.

**WHY THE SPEC HOLDS.** Two obligations do the work together. (a) The VALUE clause Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked)) pins the exact per-attribute projection, killing every wrong-value rival (atk_1, 5, 6, 7, 8, 12, 13, 14, 16) at either the loop invariant or the postcondition. (b) The TOTALITY obligation Requires(MustTerminate(2)) at the METHOD level, discharged by Invariant(MustTerminate(i)), kills every divergence/vacuity rival (atk_2, 3, 4, 9, 10, 11) via Nagini's obligation-leak check. Per the known trap, it is the method-level Requires — not the loop invariant alone — that rejects a diverging rival; this bundle has both (MustTerminate appears 3x). That closes precisely the hole the prior pass recorded.

REFINEMENT.MD LEG AUDIT (A legs, the focus): 9 legs, tags A1=R, A2=R, A3=R+I, A4=A-reference, A5=A-reference+I, A6=R+I, A7=R, A8=A-reference, A9=R+I. Every leg is R / A-reference / I — NO KIND-3 (no unexpressible-changed-op), and NO A-consumed leg exists: the axioms region is genuinely empty (repr '\n', ContractOnly count 0), so there is no axiom-soundness trust point at all; the changed operation is modelled deeply.

**A-LEG CORRESPONDENCE INDEPENDENTLY CHECKED.** I did not take axiom_check.py's word. indep_aleg_check.py transcribes BOTH the real post-patch loop (from the base blob at e6588aa4 plus patch.diff, read directly out of the upstream repository) AND model.py's pure region MYSELF, then tests each A-reference leg: A4 (passes_restriction == 'kept by `if fields is not None and f.name not in fields: continue`', the De-Morgan equivalence, over allowed in {None, [], subsets, dups, absent codes}); A5 (is_removed == the unchanged truthiness-gated `if exclude and f.name in exclude`); A8 (projection == the real loop's key SEQUENCE in source order, carrying A1/A3/A6/A7 with it) over 256,960 configurations (exhaustive small sweep + 4000 fuzz records x 8 restriction x 8 removal options); A9 (the real post-patch helper DELIVERS on every admissible input incl. fields=[]); plus the four F2P assertions from the test patch in model terms.

Result: exit 0, 'ALL A-LEGS HOLD', zero mismatches. The A4/A5 asymmetry that the whole instance turns on — restriction gated by PRESENCE, removal gated by TRUTHINESS — is faithfully carried, and A9's totality claim is true of the real function on its whole domain, not just the gold path.

**BUNDLE CHECKS RE-RUN:** axiom_check.py exit 0 (honest — it reconstructs the post-patch loop verbatim over FakeField, no DB/settings, and confirms the prepatch loop diverges on exactly the present-empty restriction list).

**NO HOST-SATURATION OR LAUNCH ARTIFACTS:** every one of the 16 weakness runs and the resolve run reached a real verdict. No verifier timeouts, no 'inconclusive', no crashes. The three builds that initially failed on Python/Nagini syntax or redeclaration errors (atk_3, atk_9) were NOT scored as spec rejections — they were rebuilt, syntax-verified with compile(), and re-run until the verifier produced a genuine semantic verdict. Per the known trap, no echo or timeout was re-judged into the reject lane: the one attack that verified (atk_15) was carried all the way through a real run_resolve rather than being speculated about.

**VERDICT:** SOUND. 16 same-spec wrong-impl attacks run (>= 5 required), including the prepatch bug and the prior pass's named counterexample; 15 rejected with semantic errors; the sole CANDIDATE's materialized faithful patch RESOLVES under the official harness, so no verifying wrong impl exists. verify => correct is not refuted here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**SPEC REGION INTEGRITY:** `python -m swebench_unified.adversary same-spec nagini django__django-11163` on a verbatim copy of the bundle model returns 'SAME - attack shares the bundle's exact specification' (exit 0). `bash scripts/nagini_verify.sh model.py` -> 'Verification successful' (28.94s, exit 0), so the spec is discharged, not merely asserted.

REFERENCE SETUP (per the brief): fresh git worktree of django/django at base_commit e6588aa4e793b7f56f4cadbfa155b581e0efc59a under /tmp, with the gold hunk APPLIED (verified by inspect.getsource: 'fields is not None' present in the imported model_to_dict, and django.`__file__` resolving to the worktree, NOT to some other installed Django -- I caught and ruled out exactly that substitution, which had broken an initial runtests invocation). Gold patch text taken from data/swe_bench_verified/test.jsonl, matching refinement.md's quoted hunk exactly (one line, models.py:86, `if fields and f.name not in fields:` -> `if fields is not None and f.name not in fields:`).

INDEPENDENT DIFFERENTIAL (written from scratch; does NOT import the bundle's conformance_check.py, so it is not a re-run of the author's own harness): the spec's meaning transcribed literally off model.py's postcondition ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked), with contains/passes_restriction/is_removed/projection copied as written, compared ORDERED against the real patched model_to_dict's key sequence over (a) the four F2P assertions in code form, (b) an exhaustive small-domain sweep -- 0..3 attributes over codes {0,1,2}, all permutations x all editability combinations x every restriction subset (incl. None and []) x every removal subset, (c) the same sweep with the fields DISTRIBUTED across all three chained streams (concrete/private/m2m) to test mapping.md's chain() order claim, and (d) 30000 fuzz configs with duplicate entries inside the optional lists and codes absent from the record. Result: 42236 checks, 0 divergences.

DIRECTION-OF-STRENGTH (the actual faithfulness question -- is the spec TOO STRONG): the three filters are pinned exactly as the real post-patch code computes them, with the two gatings deliberately ASYMMETRIC and matching the repo line-for-line. passes_restriction uses PRESENCE gating (allowed is None -> keep all; present, even empty -> members only), matching `fields is not None and...`; is_removed uses TRUTHINESS gating (absent OR empty -> removes nothing), matching the UNCHANGED `if exclude and...`. Getting this backwards in either direction is the obvious over-strengthening trap and the spec does not fall into it -- I confirmed against the real function that fields=[] -> [] while exclude=[] -> all names ['a','b'], and the spec agrees on both.

The De Morgan step in refinement.md A4 ('kept' = not(fields is not None and name not in fields) = fields is None or name in fields) is correct. I also probed present-but-falsy containers of other types (fields=(), set(), {}, '') -- the real function drops everything for each, consistent with presence gating; these are outside the Optional[List[int]] carrier but do not contradict it. A field object with NO 'editable' attribute at all yields [], matching the getattr(f,'editable',False) default modelled as edit==0.

TOTALITY (Requires(MustTerminate(2)) / Invariant(MustTerminate(i))): not an over-claim. The real helper's `for f in chain(...)` is a finite traversal doing bounded per-field work with no recursion and no unbounded construct, reaching `return data` on EVERY input including fields=[] -- so 'a result is delivered on the whole admissible domain' is TRUE of the real post-patch function, not a strengthening. It is method-level (per my prior finding that loop invariants alone do not reject a diverging rival) and load-bearing: the F2P assertion sorted(model_to_dict(bw, fields=[])) == [] is a claim ABOUT A RETURNED VALUE on precisely the input the change concerns, so without it the value clause could be discharged vacuously there.

**STRUCTURAL CLAIMS CONFIRMED:** axioms region is genuinely EMPTY (meta.json axioms == []), so there is no axiom-soundness trust point to attack. The unmodelled callee f.value_from_object is off the keyset observable -- the test reads sorted(model_to_dict(...)), i.e. keys only -- so it cannot affect which names appear; correctly not modelled. Source order is preserved by the backward impl loop (result = [n] + result), and the real dict's insertion order equals source order, so the ORDERED comparison in my differential is the stricter check and it passed.

BUNDLE'S OWN GATES (run for corroboration only, not as my evidence): axiom_check.py exit 0 (boundary + 20000 fuzz; also pins that the PRE-patch loop diverges on exactly the present-empty restriction list); conformance_check.py exit 0 against the patched worktree (102205 configs, 0 disagreements). G-DIFF spine is real: model_prepatch.py differs from model.py ONLY in the impl region (it reproduces truthiness gating as `allowed is None or len(allowed)==0 or contains(...)`), so the spec senses the change rather than admitting the pre-patch behavior.

**GOLD RESOLVES:** in a clean environment installed from the worktree itself (so that no other copy of Django can be imported) the F2P test model_forms.tests.ModelOneToOneFieldTests.test_modelform_subclassed_model runs OK with the gold patch and the test patch applied.

**CONCLUSION:** the modelled function agrees with the real post-patch callee on every input in the declared domain; the single out-of-domain divergence rests on a restriction that mapping.md states up front and that no valid, instantiable Django model can violate. No over-strengthening and no drift found. FAITHFUL.

Counterexample / evidence:

```
none -- no faithfulness counterexample on the modelled domain
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction for django__django-11163 (nagini). NO RELAXATION IN THIS BUNDLE, verified myself: meta.json keys = [additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version] -- no `relaxed_leakage`; `find. -iname '*RELAX*'` returns nothing. So this is a plain leakage review, judged from scratch; nothing was inherited as a disposition.

### WHAT I MEASURED:
1. **LEAKAGE SURFACE PINNED.** markers.spec_view(model.py, get_backend('nagini')) -> sha256 e00e1f9c70148cd13e94abf5eb2f54450e8657c295998443cedb1ee53220f30d, which is byte-identical to the spec_view hash recorded inside gates['G-HYGIENE'].data.region_hashes for the current model.py (sha256 311d24752cc1...). The impl region collapses to `...  # implementation elided`; I confirmed by probe that `result = [n] + result` and `Invariant(` are absent from the view. So the surface I judged is the real consumer surface. (Bookkeeping residual, NOT a leak and not charged: meta.json's TOP-LEVEL region_hashes block is stale relative to the shipped model.py -- impl/invariants/pre-conditions/spec_view all differ from what I compute, while G-HYGIENE's own recorded blob matches me exactly on all six. Recorded so a later reader does not mistake my hash for a mismatch.)
2. MECHANICAL SCREEN, RE-RUN BY ME. leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) against the frozen data/swe_bench_verified/test.jsonl row (not the recorded G-LEAK data blob) -> passed=True, hard_failures=[], warnings=[].
3. SYMBOL COLLISION, BY HAND. `_patch_changed_symbols` = {'model_to_dict'}; `_patch_changed_files` = ['django/forms/models.py']; `_patch_changed_lines` = ['if fields and f.name not in fields:', 'if fields is not None and f.name not in fields:']. Spec-view identifiers = {Acc, Ensures, Implies, List, MustTerminate, Optional, PSeq, Pure, Requires, Result, ToSeq, allowed, blocked, bool, contains, edit, int, is_removed, len, list_pred, n, names, passes_restriction, project_record, projection, s, x}. No identifier embeds 'model_to_dict'. Direct substring probes over the view: 'model_to_dict' False, 'forms/models' False, 'forms.models' False, 'fields' False, 'exclude' False, 'concrete_fields' False, 'value_from_object' False, '11150' False. Neither gold line appears under whitespace normalization. Narration scan over comments/docstrings (minus structural region markers): zero hits. The two repo parameters that carry the edit are renamed allowed/blocked; no path, module path, line number, or diff marker anywhere in the view. ('django' and 'editable' do appear -- 'django' only inside the instance_id in the module docstring title, which is the bundle-wide convention and localizes nothing beyond the instance name the consumer already has; 'editable' names the UNCHANGED editability filter at models.py:84, and it is a generic behavioural word, not the changed line.)
4. WHY THE DISCRIMINATOR IS NOT A LEAK (judged against problem_statement ONLY, never hints_text). The most specific spec-view sentence -- "supplying the empty list lets NO attribute through, whereas not supplying one lets every (otherwise-surviving) attribute through", plus passes_restriction gating on `allowed is None` -- is strictly LESS informative than the public problem_statement, which discloses the edit in full and verbatim. I probed the public text: it contains the gold OLD line ('if fields and f.name not in fields' -> True), the gold NEW line ('if fields is not None and f.name not in fields' -> True), and the None-vs-empty semantics ('fields=[]' + 'empty dict' -> True). The public statement literally hands the solver the before line, the after line, the file-level problem point, and the PR link. Nothing in the spec view narrows the search past that; the view is a de-repo'd Optional[List[int]] name-code abstraction. So there is no problem_statement-independent disclosure to charge.
5. **UNCHANGED-BEHAVIOUR CLAUSE CHECKED SEPARATELY.** The view also states the removal list is truthiness-gated (absent OR empty removes nothing). That is the UNCHANGED `if exclude and f.name in exclude` at models.py:88, so it localizes no edit; and the public statement, naming `fields` as the sole problem point, already implies exclude was untouched. The present/empty asymmetry BETWEEN the two lists is therefore restating public information, not disclosure.
6. LOAD-BEARING CONTROL (the strip-the-narration test, run even with no relaxation claimed). model_prepatch.py shares the spec byte-identically -- markers.same_spec(model, prepatch) -> True, and `python -m swebench_unified.adversary same-spec nagini django__django-11163 <prepatch>` -> exit 0, "SAME" -- and reverts ONLY the impl to truthiness gating (`keep_restr = allowed is None or len(allowed)==0 or contains(ToSeq(allowed), n)`). It FAILS the pinned verifier: exit 1, "Loop invariant might not be preserved. Assertion (ToSeq(result) == projection(ToSeq(names).drop(i), ToSeq(edit).drop(i), allowed, blocked)) might not hold" (69.2s). So the presence-gating clause is genuinely load-bearing spec content that the verifier senses, not ornamental narration the spec could drop.

**CORE GATES I RE-RAN RATHER THAN INHERITED:** `bash scripts/nagini_verify.sh model.py` -> exit 0, "Verification successful", 32.5s (G-VERIFY/G-GOLD direction). `bash scripts/nagini_verify.sh model_prepatch.py` -> exit 1 on the postcondition-carrying invariant (G-DIFF direction). `python axiom_check.py` -> exit 0: deep model `projection` == the real post-patch model_to_dict filtering loop over the boundary battery + 20000 fuzz configs, and the pre-patch loop diverges on exactly the present-empty restriction list (G-AX).

BUNDLE-ADDRESSES-REVIEWER FINDING (reported as a finding in its own right, non-blocking): leakage.reviewer_directed() run over every.md/.py/.json in the bundle returns [] for all ten files -- no file instructs me how to record or which verdict is honest. Two residuals recorded anyway. (a) verdict.md ships a prior backfilled section "## Role 4 - G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)" carrying that agent's complete reasoning on MY facet. It does not direct me and is marked machine-derived, but a prior verdict on my own facet sitting inside the artifact under review is an anchoring surface. I did not rely on it: every measurement above is my own run, and I reached NO-LEAKAGE before comparing.

Two of its numbers do NOT reproduce for me (its spec_view sha a2a9b5b1... is the stale meta.json value, not the current e00e1f9c...; its verify wall time was 20.12s vs my 32.5s), which is itself the reason not to treat such a section as evidence. (b) mapping.md and refinement.md DO carry the verbatim gold hunk and the repo path/line `django/forms/models.py:86`.

These sit OUTSIDE the machine-defined leakage surface -- leakage.screen screens spec_view over model.py only; I traced spec_view's consumers in src/ (markers, leakage, gates/hygiene, eval/adapter -> eval/dataset -> eval/prompts) and the solver payload renders task.spec_view plus modeled_functions' model_symbol/repo_symbol, with repo_location rendered only on the lean path and standalone localization only in mode 0; no code path ships mapping.md or refinement.md to a consumer. So out of scope on the pipeline's own surface, but the containment rests on that convention, and this would become a real leak if a future solver prompt shipped those files. Flagging, not charging.

SEPARATE-FACET NOTE (not mine to rule on): gates['G-EQ'] and ['G-PANEL-1'] are recorded status=fail -- "BROKEN (verify!=>correct): atk_10_diverge_on_empty.py verifies but its patch does not resolve". Those fails are stamped against model.py sha 50bc37a9c5c6..., NOT the shipped 311d2475..., so they are stale relative to the current artifact. Either way that is the spec-too-weak facet (G-PANEL-1), not leakage, and it does not bear on my verdict; recorded so the panel record is complete.

**VERDICT:** NO-LEAKAGE. The spec view reveals nothing about the gold edit that the public problem_statement does not already state verbatim, it names no patched symbol/path/line, reproduces neither gold line, carries no narration, and its discriminating clause is verifier-load-bearing (prepatch, same spec, fails).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
