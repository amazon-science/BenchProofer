# P2 adversarial audit — django__django-12155

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch_all_lines.py`, `atk_2_margin_from_2.py`, `atk_3_first_not_flushed.py`, `atk_4_blank_boundary_le0.py`, `atk_5_last_line_undedented.py`, `atk_6_blank_emitted_zero.py`, `atk_7_diverge_vacuous.py`, `atk_8_selfcall_echo.py`, `atk_9_guarded_selfcall.py`, `atk_10_raise_partial.py`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_11_infeasible_guard.py` |

**Non-vacuity.** The positive control `ctl_positive.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec wrong impl. 16 same-spec attacks (all `same-spec` exit 0, byte-identical spec view); 15 REJECTED by the verifier, and the single CANDIDATE (atk_11_infeasible_guard.py) is behaviourally EQUAL to gold: its added guard `if margin < 0: return []` sits under `margin = clamp_margin(...)`, which is >= 0 by construction, so the branch is DEAD. Control ctl_11_assert_false.py (identical + `Assert(False)` inside that branch) VERIFIES — mechanically proving the branch is infeasible, i.e. atk_11 is not a wrong impl at all. Protocol still required its faithful refined patch through the official harness: atk_11_infeasible_guard.diff (git apply --check clean at base_commit e8fcdaad5c) RESOLVED=True, COMPLETED=True, FAIL_TO_PASS 1/1 success, PASS_TO_PASS 6/6 success. So verify => resolve held on the one impl that verified.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_all_lines.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,17 +145,21 @@
         Assert(len(ToSeq(eff)) == 0)
         Assert(ToSeq(result) == dedented(ToSeq(eff)))
         return result
-    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
+    # Pre-patch skeleton: the common amount is measured over the non-blank
+    # lines from the VERY FIRST line (index 0) onward, not from the second line
+    # on. When the first line begins at column zero this measured amount is
+    # zero, so the body lines are left indented.
+    margin = clamp_margin(min_indent_from(ToSeq(eff), 0))
     i = n
     while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(eff), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
-        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))
+        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 0)))
         Invariant(len(result) == n - i)
         Invariant(ToSeq(result) == remove_margin(
-            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))
+            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 0))))
         Invariant(MustTerminate(i - 1 + 1))
         # invariants-end
         c = eff[i - 1]
@@ -169,18 +173,9 @@
     Assert(i == 1)
     Assert(ToSeq(eff).drop(1) == ToSeq(eff).drop(i))
     first = eff[0]
-    Assert(first == ToSeq(eff)[0])
     if first < 0:
         result = [-1] + result
     else:
         result = [0] + result
-    Assert(result[0] == first_line(first))
-    # Unfold `dedented` once on the non-empty input; the loop already produced
-    # the body via the identical `clamp_margin(min_indent_from(...))` argument,
-    # so no recursive-function congruence step is needed.
-    Assert(dedented(ToSeq(eff)) ==
-           PSeq(first_line(ToSeq(eff)[0])) + remove_margin(
-               ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))
-    Assert(ToSeq(result) == dedented(ToSeq(eff)))
     return result
     # impl-end
```

Attack 2 — `atk_2_margin_from_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,17 +145,17 @@
         Assert(len(ToSeq(eff)) == 0)
         Assert(ToSeq(result) == dedented(ToSeq(eff)))
         return result
-    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
+    margin = clamp_margin(min_indent_from(ToSeq(eff), 2))
     i = n
     while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(eff), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
-        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))
+        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 2)))
         Invariant(len(result) == n - i)
         Invariant(ToSeq(result) == remove_margin(
-            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))
+            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 2))))
         Invariant(MustTerminate(i - 1 + 1))
         # invariants-end
         c = eff[i - 1]
```

Attack 3 — `atk_3_first_not_flushed.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -173,8 +173,7 @@
     if first < 0:
         result = [-1] + result
     else:
-        result = [0] + result
-    Assert(result[0] == first_line(first))
+        result = [first] + result
     # Unfold `dedented` once on the non-empty input; the loop already produced
     # the body via the identical `clamp_margin(min_indent_from(...))` argument,
     # so no recursive-function congruence step is needed.
```

Attack 4 — `atk_4_blank_boundary_le0.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -161,7 +161,7 @@
         c = eff[i - 1]
         Assert(ToSeq(eff).drop(i - 1)[0] == c)
         Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))
-        if c < 0:
+        if c <= 0:
             result = [-1] + result
         else:
             result = [c - margin] + result
```

Attack 5 — `atk_5_last_line_undedented.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -163,6 +163,8 @@
         Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))
         if c < 0:
             result = [-1] + result
+        elif i == n and n > 2:
+            result = [c] + result
         else:
             result = [c - margin] + result
         i = i - 1
```

Attack 6 — `atk_6_blank_emitted_zero.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -162,7 +162,7 @@
         Assert(ToSeq(eff).drop(i - 1)[0] == c)
         Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))
         if c < 0:
-            result = [-1] + result
+            result = [0] + result
         else:
             result = [c - margin] + result
         i = i - 1
```

Attack 7 — `atk_7_diverge_vacuous.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -141,46 +141,13 @@
     # impl-start
     result = []  # type: List[int]
     n = len(eff)
-    if n == 0:
-        Assert(len(ToSeq(eff)) == 0)
-        Assert(ToSeq(result) == dedented(ToSeq(eff)))
-        return result
-    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
-    i = n
-    while i > 1:
+    i = 0
+    while i >= 0:
         # invariants-start
         Invariant(Acc(list_pred(eff), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
-        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))
-        Invariant(len(result) == n - i)
-        Invariant(ToSeq(result) == remove_margin(
-            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))
-        Invariant(MustTerminate(i - 1 + 1))
+        Invariant(i >= 0)
         # invariants-end
-        c = eff[i - 1]
-        Assert(ToSeq(eff).drop(i - 1)[0] == c)
-        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))
-        if c < 0:
-            result = [-1] + result
-        else:
-            result = [c - margin] + result
-        i = i - 1
-    Assert(i == 1)
-    Assert(ToSeq(eff).drop(1) == ToSeq(eff).drop(i))
-    first = eff[0]
-    Assert(first == ToSeq(eff)[0])
-    if first < 0:
-        result = [-1] + result
-    else:
-        result = [0] + result
-    Assert(result[0] == first_line(first))
-    # Unfold `dedented` once on the non-empty input; the loop already produced
-    # the body via the identical `clamp_margin(min_indent_from(...))` argument,
-    # so no recursive-function congruence step is needed.
-    Assert(dedented(ToSeq(eff)) ==
-           PSeq(first_line(ToSeq(eff)[0])) + remove_margin(
-               ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))
-    Assert(ToSeq(result) == dedented(ToSeq(eff)))
+        i = i + 1
     return result
     # impl-end
```

Attack 8 — `atk_8_selfcall_echo.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -139,48 +139,5 @@
     Ensures(Implies(len(eff) > 0 and ToSeq(eff)[0] >= 0, Result()[0] == 0))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    n = len(eff)
-    if n == 0:
-        Assert(len(ToSeq(eff)) == 0)
-        Assert(ToSeq(result) == dedented(ToSeq(eff)))
-        return result
-    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
-    i = n
-    while i > 1:
-        # invariants-start
-        Invariant(Acc(list_pred(eff), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
-        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))
-        Invariant(len(result) == n - i)
-        Invariant(ToSeq(result) == remove_margin(
-            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))
-        Invariant(MustTerminate(i - 1 + 1))
-        # invariants-end
-        c = eff[i - 1]
-        Assert(ToSeq(eff).drop(i - 1)[0] == c)
-        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))
-        if c < 0:
-            result = [-1] + result
-        else:
-            result = [c - margin] + result
-        i = i - 1
-    Assert(i == 1)
-    Assert(ToSeq(eff).drop(1) == ToSeq(eff).drop(i))
-    first = eff[0]
-    Assert(first == ToSeq(eff)[0])
-    if first < 0:
-        result = [-1] + result
-    else:
-        result = [0] + result
-    Assert(result[0] == first_line(first))
-    # Unfold `dedented` once on the non-empty input; the loop already produced
-    # the body via the identical `clamp_margin(min_indent_from(...))` argument,
-    # so no recursive-function congruence step is needed.
-    Assert(dedented(ToSeq(eff)) ==
-           PSeq(first_line(ToSeq(eff)[0])) + remove_margin(
-               ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))
-    Assert(ToSeq(result) == dedented(ToSeq(eff)))
-    return result
+    return dedent_block(eff)
     # impl-end
```

Attack 9 — `atk_9_guarded_selfcall.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -182,5 +182,7 @@
            PSeq(first_line(ToSeq(eff)[0])) + remove_margin(
                ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))
     Assert(ToSeq(result) == dedented(ToSeq(eff)))
+    if first >= 0:
+        return dedent_block(eff)
     return result
     # impl-end
```

Attack 10 — `atk_10_raise_partial.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -182,5 +182,7 @@
            PSeq(first_line(ToSeq(eff)[0])) + remove_margin(
                ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))
     Assert(ToSeq(result) == dedented(ToSeq(eff)))
+    if n > 2:
+        raise ValueError()
     return result
     # impl-end
```

Attack 11 — `atk_11_infeasible_guard.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -146,6 +146,8 @@
         Assert(ToSeq(result) == dedented(ToSeq(eff)))
         return result
     margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
+    if margin < 0:
+        return []
     i = n
     while i > 1:
         # invariants-start
```

Attack 12 — `atk_12_no_clamp_marker_leak.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,7 +145,7 @@
         Assert(len(ToSeq(eff)) == 0)
         Assert(ToSeq(result) == dedented(ToSeq(eff)))
         return result
-    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
+    margin = min_indent_from(ToSeq(eff), 1)
     i = n
     while i > 1:
         # invariants-start
```

Attack 13 — `atk_13_loop_covers_first.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,11 +147,11 @@
         return result
     margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
     i = n
-    while i > 1:
+    while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(eff), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
+        Invariant(0 <= i and i <= n and n == len(eff) and n > 0)
         Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))
         Invariant(len(result) == n - i)
         Invariant(ToSeq(result) == remove_margin(
```

Attack 14 — `atk_14_f2p_only_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -146,6 +146,8 @@
         Assert(ToSeq(result) == dedented(ToSeq(eff)))
         return result
     margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
+    if n == 3 and eff[0] == 0 and eff[1] < 0 and eff[2] > 0:
+        margin = clamp_margin(min_indent_from(ToSeq(eff), 0))
     i = n
     while i > 1:
         # invariants-start
```

Attack 15 — `atk_15_f2p_partial_tracked.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,17 +145,20 @@
         Assert(len(ToSeq(eff)) == 0)
         Assert(ToSeq(result) == dedented(ToSeq(eff)))
         return result
+    # PARTIAL DOMAIN: on the FAIL_TO_PASS shape only, fall back to the PRE-PATCH
+    # measurement (over ALL lines, index 0). Everywhere else, the fixed one.
     margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
+    if n == 3 and eff[0] == 0 and eff[1] < 0 and eff[2] > 0:
+        margin = clamp_margin(min_indent_from(ToSeq(eff), 0))
     i = n
     while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(eff), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
-        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))
+        Invariant(margin >= 0)
         Invariant(len(result) == n - i)
-        Invariant(ToSeq(result) == remove_margin(
-            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))
+        Invariant(ToSeq(result) == remove_margin(ToSeq(eff).drop(i), margin))
         Invariant(MustTerminate(i - 1 + 1))
         # invariants-end
         c = eff[i - 1]
@@ -175,12 +178,5 @@
     else:
         result = [0] + result
     Assert(result[0] == first_line(first))
-    # Unfold `dedented` once on the non-empty input; the loop already produced
-    # the body via the identical `clamp_margin(min_indent_from(...))` argument,
-    # so no recursive-function congruence step is needed.
-    Assert(dedented(ToSeq(eff)) ==
-           PSeq(first_line(ToSeq(eff)[0])) + remove_margin(
-               ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))
-    Assert(ToSeq(result) == dedented(ToSeq(eff)))
     return result
     # impl-end
```

Attack 16 — `atk_16_prepatch_tracked.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -145,17 +145,18 @@
         Assert(len(ToSeq(eff)) == 0)
         Assert(ToSeq(result) == dedented(ToSeq(eff)))
         return result
-    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))
+    # A2-leg attack: the PRE-PATCH measurement (over ALL lines, index 0) --
+    # the culprit `min(... for line in lines if line.lstrip())`.
+    margin = clamp_margin(min_indent_from(ToSeq(eff), 0))
     i = n
     while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(eff), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(1 <= i and i <= n and n == len(eff) and n > 0)
-        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))
+        Invariant(margin >= 0)
         Invariant(len(result) == n - i)
-        Invariant(ToSeq(result) == remove_margin(
-            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))
+        Invariant(ToSeq(result) == remove_margin(ToSeq(eff).drop(i), margin))
         Invariant(MustTerminate(i - 1 + 1))
         # invariants-end
         c = eff[i - 1]
@@ -175,12 +176,5 @@
     else:
         result = [0] + result
     Assert(result[0] == first_line(first))
-    # Unfold `dedented` once on the non-empty input; the loop already produced
-    # the body via the identical `clamp_margin(min_indent_from(...))` argument,
-    # so no recursive-function congruence step is needed.
-    Assert(dedented(ToSeq(eff)) ==
-           PSeq(first_line(ToSeq(eff)[0])) + remove_margin(
-               ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))
-    Assert(ToSeq(result) == dedented(ToSeq(eff)))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_positive.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SPEC WAS REPAIRED SINCE THE RECORDED G-EQ FAIL — the recorded fail is STALE. meta.json G-EQ was stamped against model.py sha a975d44871606eb7...; the current frozen model.py is 8c5901ca39d06ab7.... The repair added `Requires(MustTerminate(2))` (line 126) plus a loop measure `Invariant(MustTerminate(i - 1 + 1))` (line 159). I re-encoded the retained counterexample and it is now REJECTED, so I did not carry the retained verdict forward.

### COMMANDS (all from repo root swe-proof):
python -m swebench_unified.adversary same-spec nagini django__django-12155 <D>/<f>.py   -> exit 0 for ALL 16 attacks + 3 controls
python -m swebench_unified.adversary weakness  nagini django__django-12155 <D>/<f>.py
bash scripts/nagini_verify.sh <D>/<f>.py
Per-attack output in <D>/<name>.weak.out and <D>/<name>.out. D=.

### ATTACK-BY-ATTACK (weakness exit 0 = CANDIDATE, 2 = rejected):
- ctl_positive.py (unmodified frozen impl) -- exit 0, VERIFIES 29.0s. Positive control good.
- atk_1_prepatch_all_lines.py -- exit 2 REJECTED. THE PREPATCH BUG re-encoded (= bundle model_prepatch.py, same_spec True): margin from index 0, `min_indent_from(ToSeq(eff), 0)` <-> the culprit `min(len(line)-len(line.lstrip()) for line in lines if line.lstrip())` over ALL lines. prepatch_reproduced=true; G-DIFF's discriminating power confirmed independently.
- atk_2_margin_from_2.py -- exit 2 REJECTED. Off-by-one the other way (margin measured from index 2, skipping the second line).
- atk_3_first_not_flushed.py -- exit 2 REJECTED. BOUNDARY/A3: first line keeps its own indent (`[first]`) instead of flush-left.
- atk_4_blank_boundary_le0.py -- exit 2 REJECTED. BOUNDARY: blank test widened to `c <= 0`, so an indent-0 line becomes a blank marker.
- atk_5_last_line_undedented.py -- exit 2 REJECTED. PARTIAL-DOMAIN: the last line escapes de-indentation.
- atk_6_blank_emitted_zero.py -- exit 2 REJECTED. Blank body line emitted as non-blank flush-left, losing the -1 marker.
- atk_7_diverge_vacuous.py -- exit 2 REJECTED. CONTROL-FLOW-EFFECT/divergence: `while i >= 0: i = i + 1`, returning the empty list. Verifier: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." The MustTerminate repair kills this lane (this is the lane the STALE recorded fail exploited).
- atk_8_selfcall_echo.py -- exit 2 REJECTED. UNGROUNDED-ORACLE ECHO: unguarded `return dedent_block(eff)`. Verifier: "Obligation leak check failed. Callee dedent_block might not take all unsatisfied obligations from the caller."
- atk_9_guarded_selfcall.py -- exit 2 REJECTED. THE RETAINED COUNTEREXAMPLE from the stale G-EQ record, re-encoded byte-for-byte: the circular discharge `if first >= 0: return dedent_block(eff)` placed AFTER every frozen Assert. Verifier: same obligation-leak rejection at 186:12. REACHABILITY CONTROL ctl_9_selfcall_assert_false.py -> exit 1, "Assert might fail. Assertion False might not hold" -- the self-call site is genuinely REACHABLE, so this is a real rejection of a real circular discharge, not an infeasible-guard artifact.
- atk_10_raise_partial.py -- exit 2 REJECTED. Abort lane: `raise ValueError()` on a partial domain instead of returning.
- atk_11_infeasible_guard.py -- exit 0 CANDIDATE (verifies 26.4s), and NOT a wrong impl: dead-branch vacuity probe, see counterexample field. PATCH RESOLVE RUN EXECUTED: RESOLVED=True/COMPLETED=True, F2P 1/1, P2P 6/6, patch_successfully_applied=true. Does NOT break the spec.
- atk_12_no_clamp_marker_leak.py -- exit 2 REJECTED. A2-leg: clamp DROPPED so the NO_AMOUNT() marker leaks into the arithmetic.
- atk_13_loop_covers_first.py -- exit 2 REJECTED. Loop bound `while i > 0`, so the first line is also slid left before flushing (A3/A4 boundary).
- atk_14_f2p_only_prepatch.py -- exit 2 REJECTED. Maximally-narrow PARTIAL DOMAIN: prepatch measurement applied ONLY on the F2P shape eff == [0,-1,4].
- atk_15_f2p_partial_tracked.py / atk_16_prepatch_tracked.py -- exit 2 REJECTED, and these are the IMPORTANT pair. atk_12/atk_14 were rejected on a FROZEN loop invariant, which could be read as proof plumbing rather than behaviour, so I re-encoded both with invariants tracking the ATTACKER's own margin variable (`Invariant(margin >= 0)` + `remove_margin(..., margin)`), leaving the POSTCONDITION as the only thing that can reject. Both then fail exactly there: "Postcondition of dedent_block might not hold. Assertion (ToSeq(Result()) == dedented(ToSeq(eff))) might not hold." Genuine behavioural rejections of both the pre-patch measurement AND the F2P-only partial domain.

A-LEG AUDIT (my assignment; R/I legs left to G-CONF). refinement.md has NO A-consumed leg and NO kind-3: legs are 2x R (A1 str<->List[int] carrier, A5 output profile), 2x A-reference (A2 the margin measurement, A4 the per-line removal), 1x A-reference-(I-under-R) (A3 lstrip of line 0). Consistent with the empty `axioms` region and with meta.json (axioms: [], deep_model_references: 1 x kind "A-reference"). The single A-reference (`dedented` <-> inspect.cleandoc) I re-derived INDEPENDENTLY of the bundle's own axiom_check.py: my own re-encoding of both the deep model and cleandoc's per-line profile (pre blank-line-strip) agreed on 30009 cases (9 boundary + 30000 fuzz), 0 mismatches, and the F2P discriminator reproduces (eff [0,-1,4] -> model [0,-1,0]; real cleandoc('firstline\n\n    second line') == 'firstline\n\nsecond line'). The bundle's axiom_check.py also exits 0. A2's sign-vs-magnitude argument for the empty-fold marker is correct and materially load-bearing: an unbounded carrier makes any large sentinel a reachable amount.

MODEL<->PATCH CORRESPONDENCE (the other half of my assignment). refinement.md SS.D's inference "dedent_block verifies only if its output equals dedented(...)" is now a TOTAL-correctness claim, discharged: MustTerminate at the method level (line 126) + the loop measure (line 159). The prior audit's finding that SS.D read a partial-correctness theorem as a total one no longer applies to this spec text -- atk_7/atk_8/atk_9 are the three lanes that finding named and all three are now rejected. Site B (views.py:259) is the identical normalisation swap and needs no separate modeled function; the additional_change_sites entry for the `if not docstring: return '', '', {}` guard is an unchanged short-circuit outside the indentation transform, correctly outside the carrier.

SPEC-NOT-TOO-STRONG CHECK (the converse direction, since a drifted spec is also a refinement-fidelity defect and the stale record carried a G-PANEL-2 "unfaithful" finding about a finite BIG() sentinel): the frozen model.py contains NO BIG()/maxsize sentinel at all -- NO_AMOUNT() == -1, negative. I built ctl_faithful_boolseen.py, a REPO-FAITHFUL impl mirroring cleandoc's own control flow with a BOOLEAN empty-fold flag (never naming NO_AMOUNT/clamp_margin to build its margin, since cleandoc's real sentinel sys.maxsize is unreachable for a real line). same-spec exit 0, and `bash scripts/nagini_verify.sh` -> "Verification successful", exit 0. A behaviourally-correct-vs-the-real-callee impl is ACCEPTED, so the spec is not too strong either. (My first attempt at this control failed on my OWN invariant -- a forward scan cannot state the frozen suffix-min helper; re-encoded as a backward scan it verifies. I record that as my plumbing bug, not spec strength.)

**HOUSEKEEPING:** base_commit worktree used for `git apply --check` was created from the upstream repository at e8fcdaad5c and has been removed (`git worktree remove --force`). generators gen.py/gen2.py/gen3.py retained so every attack is reproducible from the frozen model.py.

**ADVISORY:** the recorded G-EQ/G-PANEL-1/G-PANEL-2 fails in meta.json are stale (stamped against model.py a975d448..., superseded by 8c5901ca...). Both defects those roles found are repaired and I could not reconstruct either. Recommend those three roles be re-derived against the current sha rather than treated as live findings.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1_prepatch_all_lines.py`, `atk_2_margin_from_2.py`, `atk_3_first_not_flushed.py`, `atk_4_blank_boundary_le0.py`, `atk_5_last_line_undedented.py`, `atk_6_blank_emitted_zero.py`, `atk_7_diverge_vacuous.py`, `atk_8_selfcall_echo.py`, `atk_9_guarded_selfcall.py`, `atk_10_raise_partial.py`, +5 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_11_infeasible_guard.py` |

**Non-vacuity.** The positive control `ctl_positive.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec wrong impl. 16 same-spec attacks (all `same-spec` exit 0, byte-identical spec view); 15 REJECTED by the verifier, and the single CANDIDATE (atk_11_infeasible_guard.py) is behaviourally EQUAL to gold: its added guard `if margin < 0: return []` sits under `margin = clamp_margin(...)`, which is >= 0 by construction, so the branch is DEAD. Control ctl_11_assert_false.py (identical + `Assert(False)` inside that branch) VERIFIES — mechanically proving the branch is infeasible, i.e. atk_11 is not a wrong impl at all. Protocol still required its faithful refined patch through the official harness: atk_11_infeasible_guard.diff (git apply --check clean at base_commit e8fcdaad5c) RESOLVED=True, COMPLETED=True, FAIL_TO_PASS 1/1 success, PASS_TO_PASS 6/6 success. So verify => resolve held on the one impl that verified.
```

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch_all_lines.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_margin_from_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_first_not_flushed.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_blank_boundary_le0.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_last_line_undedented.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_blank_emitted_zero.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_diverge_vacuous.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_selfcall_echo.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_guarded_selfcall.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_raise_partial.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_infeasible_guard.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_no_clamp_marker_leak.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_loop_covers_first.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_f2p_only_prepatch.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_f2p_partial_tracked.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_prepatch_tracked.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_positive.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

SPEC WAS REPAIRED SINCE THE RECORDED G-EQ FAIL — the recorded fail is STALE. meta.json G-EQ was stamped against model.py sha a975d44871606eb7...; the current frozen model.py is 8c5901ca39d06ab7.... The repair added `Requires(MustTerminate(2))` (line 126) plus a loop measure `Invariant(MustTerminate(i - 1 + 1))` (line 159). I re-encoded the retained counterexample and it is now REJECTED, so I did not carry the retained verdict forward.

### COMMANDS (all from repo root swe-proof):
python -m swebench_unified.adversary same-spec nagini django__django-12155 <D>/<f>.py   -> exit 0 for ALL 16 attacks + 3 controls
python -m swebench_unified.adversary weakness  nagini django__django-12155 <D>/<f>.py
bash scripts/nagini_verify.sh <D>/<f>.py
Per-attack output in <D>/<name>.weak.out and <D>/<name>.out. D=.

### ATTACK-BY-ATTACK (weakness exit 0 = CANDIDATE, 2 = rejected):
- ctl_positive.py (unmodified frozen impl) -- exit 0, VERIFIES 29.0s. Positive control good.
- atk_1_prepatch_all_lines.py -- exit 2 REJECTED. THE PREPATCH BUG re-encoded (= bundle model_prepatch.py, same_spec True): margin from index 0, `min_indent_from(ToSeq(eff), 0)` <-> the culprit `min(len(line)-len(line.lstrip()) for line in lines if line.lstrip())` over ALL lines. prepatch_reproduced=true; G-DIFF's discriminating power confirmed independently.
- atk_2_margin_from_2.py -- exit 2 REJECTED. Off-by-one the other way (margin measured from index 2, skipping the second line).
- atk_3_first_not_flushed.py -- exit 2 REJECTED. BOUNDARY/A3: first line keeps its own indent (`[first]`) instead of flush-left.
- atk_4_blank_boundary_le0.py -- exit 2 REJECTED. BOUNDARY: blank test widened to `c <= 0`, so an indent-0 line becomes a blank marker.
- atk_5_last_line_undedented.py -- exit 2 REJECTED. PARTIAL-DOMAIN: the last line escapes de-indentation.
- atk_6_blank_emitted_zero.py -- exit 2 REJECTED. Blank body line emitted as non-blank flush-left, losing the -1 marker.
- atk_7_diverge_vacuous.py -- exit 2 REJECTED. CONTROL-FLOW-EFFECT/divergence: `while i >= 0: i = i + 1`, returning the empty list. Verifier: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." The MustTerminate repair kills this lane (this is the lane the STALE recorded fail exploited).
- atk_8_selfcall_echo.py -- exit 2 REJECTED. UNGROUNDED-ORACLE ECHO: unguarded `return dedent_block(eff)`. Verifier: "Obligation leak check failed. Callee dedent_block might not take all unsatisfied obligations from the caller."
- atk_9_guarded_selfcall.py -- exit 2 REJECTED. THE RETAINED COUNTEREXAMPLE from the stale G-EQ record, re-encoded byte-for-byte: the circular discharge `if first >= 0: return dedent_block(eff)` placed AFTER every frozen Assert. Verifier: same obligation-leak rejection at 186:12. REACHABILITY CONTROL ctl_9_selfcall_assert_false.py -> exit 1, "Assert might fail. Assertion False might not hold" -- the self-call site is genuinely REACHABLE, so this is a real rejection of a real circular discharge, not an infeasible-guard artifact.
- atk_10_raise_partial.py -- exit 2 REJECTED. Abort lane: `raise ValueError()` on a partial domain instead of returning.
- atk_11_infeasible_guard.py -- exit 0 CANDIDATE (verifies 26.4s), and NOT a wrong impl: dead-branch vacuity probe, see counterexample field. PATCH RESOLVE RUN EXECUTED: RESOLVED=True/COMPLETED=True, F2P 1/1, P2P 6/6, patch_successfully_applied=true. Does NOT break the spec.
- atk_12_no_clamp_marker_leak.py -- exit 2 REJECTED. A2-leg: clamp DROPPED so the NO_AMOUNT() marker leaks into the arithmetic.
- atk_13_loop_covers_first.py -- exit 2 REJECTED. Loop bound `while i > 0`, so the first line is also slid left before flushing (A3/A4 boundary).
- atk_14_f2p_only_prepatch.py -- exit 2 REJECTED. Maximally-narrow PARTIAL DOMAIN: prepatch measurement applied ONLY on the F2P shape eff == [0,-1,4].
- atk_15_f2p_partial_tracked.py / atk_16_prepatch_tracked.py -- exit 2 REJECTED, and these are the IMPORTANT pair. atk_12/atk_14 were rejected on a FROZEN loop invariant, which could be read as proof plumbing rather than behaviour, so I re-encoded both with invariants tracking the ATTACKER's own margin variable (`Invariant(margin >= 0)` + `remove_margin(..., margin)`), leaving the POSTCONDITION as the only thing that can reject. Both then fail exactly there: "Postcondition of dedent_block might not hold. Assertion (ToSeq(Result()) == dedented(ToSeq(eff))) might not hold." Genuine behavioural rejections of both the pre-patch measurement AND the F2P-only partial domain.

A-LEG AUDIT (my assignment; R/I legs left to G-CONF). refinement.md has NO A-consumed leg and NO kind-3: legs are 2x R (A1 str<->List[int] carrier, A5 output profile), 2x A-reference (A2 the margin measurement, A4 the per-line removal), 1x A-reference-(I-under-R) (A3 lstrip of line 0). Consistent with the empty `axioms` region and with meta.json (axioms: [], deep_model_references: 1 x kind "A-reference"). The single A-reference (`dedented` <-> inspect.cleandoc) I re-derived INDEPENDENTLY of the bundle's own axiom_check.py: my own re-encoding of both the deep model and cleandoc's per-line profile (pre blank-line-strip) agreed on 30009 cases (9 boundary + 30000 fuzz), 0 mismatches, and the F2P discriminator reproduces (eff [0,-1,4] -> model [0,-1,0]; real cleandoc('firstline\n\n    second line') == 'firstline\n\nsecond line'). The bundle's axiom_check.py also exits 0. A2's sign-vs-magnitude argument for the empty-fold marker is correct and materially load-bearing: an unbounded carrier makes any large sentinel a reachable amount.

MODEL<->PATCH CORRESPONDENCE (the other half of my assignment). refinement.md SS.D's inference "dedent_block verifies only if its output equals dedented(...)" is now a TOTAL-correctness claim, discharged: MustTerminate at the method level (line 126) + the loop measure (line 159). The prior audit's finding that SS.D read a partial-correctness theorem as a total one no longer applies to this spec text -- atk_7/atk_8/atk_9 are the three lanes that finding named and all three are now rejected. Site B (views.py:259) is the identical normalisation swap and needs no separate modeled function; the additional_change_sites entry for the `if not docstring: return '', '', {}` guard is an unchanged short-circuit outside the indentation transform, correctly outside the carrier.

SPEC-NOT-TOO-STRONG CHECK (the converse direction, since a drifted spec is also a refinement-fidelity defect and the stale record carried a G-PANEL-2 "unfaithful" finding about a finite BIG() sentinel): the frozen model.py contains NO BIG()/maxsize sentinel at all -- NO_AMOUNT() == -1, negative. I built ctl_faithful_boolseen.py, a REPO-FAITHFUL impl mirroring cleandoc's own control flow with a BOOLEAN empty-fold flag (never naming NO_AMOUNT/clamp_margin to build its margin, since cleandoc's real sentinel sys.maxsize is unreachable for a real line). same-spec exit 0, and `bash scripts/nagini_verify.sh` -> "Verification successful", exit 0. A behaviourally-correct-vs-the-real-callee impl is ACCEPTED, so the spec is not too strong either. (My first attempt at this control failed on my OWN invariant -- a forward scan cannot state the frozen suffix-min helper; re-encoded as a backward scan it verifies. I record that as my plumbing bug, not spec strength.)

**HOUSEKEEPING:** base_commit worktree used for `git apply --check` was created from the upstream repository at e8fcdaad5c and has been removed (`git worktree remove --force`). generators gen.py/gen2.py/gen3.py retained so every attack is reproducible from the frozen model.py.

**ADVISORY:** the recorded G-EQ/G-PANEL-1/G-PANEL-2 fails in meta.json are stale (stamped against model.py a975d448..., superseded by 8c5901ca...). Both defects those roles found are repaired and I could not reconstruct either. Recommend those three roles be re-derived against the current sha rather than treated as live findings.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**Reference used:** django_django.git worktree at base_commit e8fcdaad5c428878d0a5d6ba820d957013f75595 () with the gold patch semantics, i.e. the modelled callee is `inspect.cleandoc` (post-patch), NOT the base `trim_docstring`.

### Spec integrity
- `same-spec` on the bundle's own model.py -> exit 0 ("SAME"); region hashes present in meta.json.
- Pinned verifier: `bash scripts/nagini_verify.sh model.py` -> "Verification successful" (22.7s).
- Bundle self-checks re-run green: axiom_check.py exit 0 (G-AX), conformance_check.py exit 0 (100026 docstrings, 0 disagreements).
- Direction check (guards against condemning the fix): model_prepatch.py, whose pure region is identical and whose impl measures over ALL lines, FAILS the postcondition `ToSeq(Result()) == dedented(ToSeq(eff))` (pre.py:137). So the spec is post-patch-aligned; the base-commit `trim_docstring` behaviour is correctly the thing it rejects, not the reference.

### What I tried to break
The attack surface for "too strong" here is three-fold: (a) the margin measurement, (b) the negative empty-fold marker NO_AMOUNT()==-1 vs cleandoc's `sys.maxsize`, (c) the R-refinement str <-> List[int] per-line indent profile, including whether cleandoc's blank-line popping is legitimately outside the carrier.

1. Model vs REAL callee, transform level (cleandoc body stopped before its pop loops, i.e. exactly the carrier mapping.md 3.1 declares):
   - exhaustive 1-3 lines over a 71-token adversarial alphabet = 363,023 cases: 0 mismatches.
   - exhaustive 4 lines over a 10-token spaces alphabet = 10,000 cases: 0 mismatches.
   - exhaustive 0-3 lines over an 18-token alphabet = 6,175 cases: 0 mismatches.
   - 400,000-case + 200,000-case randomized fuzz (up to 11 lines): 0 mismatches.
   Alphabet deliberately included the whitespace classes that split lstrip/expandtabs/str-emptiness apart: TAB, VT (\x0b), FF (\x0c), CR (\r), \x1c-\x1e, NEL (\x85), NBSP (\xa0), U+2007, U+3000, U+2009, and ZWSP (U+200B). These are the classic faithfulness traps here (VT/FF/CR are lstrip-strippable but NOT expandtabs-expanded, NBSP/U+3000 are Unicode-space but NOT lstrip-strippable, ZWSP is neither) -- the model's `-1 iff len(line.lstrip())==0` blank marker tracks cleandoc's own `content = len(line.lstrip())` test exactly, so all of them agree.

2. Mirror fidelity of my own oracle: simulating cleandoc's two pop loops on my pre-strip line list reproduced real `inspect.cleandoc` output byte-for-byte on all 6,175 exhaustive cases (0 mismatches), so the pre-strip comparison point is not a fabricated oracle -- it is cleandoc minus a step that provably composes back.

3. Carrier well-definedness (would break the R-refinement even with a correct transform): 300,000 random strings, checking whether two strings with the SAME input eff profile can produce DIFFERENT output profiles under the real callee -> 0 abstraction collisions. The per-line indent profile is a genuine abstraction of the transform, so summarising a line to one int loses nothing the postcondition asserts.

4. Each postcondition probed individually against the real callee over 300,000 adversarial strings: `len(Result())==len(eff)` 0 violations; `ToSeq(Result())==dedented(ToSeq(eff))` 0 violations; `eff[0]>=0 ==> Result()[0]==0` 0 violations (the last also checked against full real cleandoc output post-popping over 200,000 strings: 0 violations). No postcondition is stronger than the real callee.

5. The marker/sentinel divergence, which is the only real point where the model and cleandoc differ, and it is UNREACHABLE. cleandoc encodes "no body line" as margin==sys.maxsize; the model encodes it by SIGN (-1). These part company only at eff containing sys.maxsize as a genuine indent -- e.g. eff=[0, sys.maxsize], where the model gives [0,0] (slide flush) and cleandoc would give [0, sys.maxsize] (remove nothing). But a str preimage requires a line with 9,223,372,036,854,775,807 leading spaces (~9.2 exabytes), so there is NO input to the real callee that exhibits it. I probed the reachable tail directly against the real callee at indents 1e3, 1e5, 1e6 and 5e6 -- all agree. Note the direction: the model is the STRICTER/more-correct encoding here (a large-magnitude marker would alias a real amount and leave a body line unmoved); the model never claims cleandoc does something cleandoc does not do on any constructible string. axiom_check.py already judges this range against a deliberately marker-free reference rather than against cleandoc, which is the right standard and not a double-mask.

6. Second change site (views.py:259, `utils.trim_docstring(verbose)` -> `cleandoc(verbose)`, confirmed in the base worktree at views.py:259 and in the gold patch from data/swe_bench_verified/test.jsonl) is the identical normalisation swap, so refinement.md B needing no second modelled function is correct.

7. Gold patch cross-checked verbatim against the SWE-bench Verified record: the two hunks are exactly `trim_docstring` deletion + `cleandoc` with an early `return '', '', {}`, and the views.py call-site swap. The early empty-input return is an unchanged guard outside the indentation transform, correctly declared out of carrier (and harmless: dedent_block on the empty carrier returns the empty list). F2P `test_parse_rst_with_docstring_no_leading_line_feed` observable reproduced: on "firstline\n\n    second line" the real cleandoc yields 'firstline\n\nsecond line' (body flush, profile [0,-1,0]) and the model's dedented gives [0,-1,0], while the base `trim_docstring` leaves the body at indent 4 -- the spec sits on the fixed side.

**BLANK-LINE POPPING:** I specifically considered whether excluding cleandoc's leading/trailing pop from the carrier hides a divergence. It does not, for two independent reasons: (i) it is byte-identical pre- and post-patch (base `trim_docstring` does the same job via `.strip()`), so it cannot be the delta the spec must sense; (ii) item 2 above shows it composes back onto the model's output exactly, and conformance_check.py's bridge simulates those pops on the shadow and matches the real patched callee on 100k inputs. The exclusion is a declared, audited abstraction, not a mask.

**CONCLUSION:** no diverging input exists. Over ~380k exhaustive and ~1.1M randomized inputs, plus targeted probes at every whitespace class, at the sentinel magnitude boundary, and on each postcondition separately, the modelled function agrees with the real post-patch callee everywhere it is defined; the sole abstract disagreement (indent == sys.maxsize) has no string preimage and errs on the safe side. FAITHFUL -- no unsoundness to report, no counterexample to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MEASURED ON THE CURRENT BYTES, NOT INHERITED. No relaxation is claimed by this bundle: meta.json has no `relaxed_leakage` key (keys: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and there is no RELAXED_LEAKAGE.md (`ls`/`grep -rn -i relaxed` over the bundle hit only prior verdict.md/meta.json prose). So this is an ORDINARY (non-relaxed) leakage review; the relaxed-facet branch of my instructions does not apply and I did not use it. I nonetheless ran the prescribed strip-and-verify load-bearing test, because it is the right instrument for locating where the discriminator actually lives.

**WHAT THE CONSUMER SEES.** Rendered the real consumer artifact myself: markers.spec_view(model.py, NaginiBackend) -> 143 lines, sha256 d1afd6995f76babf (written to specview.txt). The impl region collapses to `...  # implementation elided`, so the view is: module docstring + `axioms` (empty, comment only) + `pure` (NO_AMOUNT, min_indent_from, clamp_margin, remove_margin, first_line, dedented) + Requires/Ensures on dedent_block. refinement.md and mapping.md are NOT in the spec view (spec_view projects model.py only; prompts/nagini/`audit_*_task`.md list the twin docs for the constructor/auditor, not the solver) -- and they are where every leaking token lives: `cleandoc`, `trim_docstring`, `parse_docstring`, `utils.py:37`, `sys.maxsize`, `lines[1:]`, plus the gold hunk verbatim. None of it reaches the view.

VOCABULARY SCAN of the rendered view for gold-edit tokens {cleandoc, inspect, trim_docstring, parse_docstring, parse_rst, expandtabs, lstrip, lines[1:], maxsize, sys., PEP, 257, docstring, admindoc, utils.py, views.py, firstline, 'second line', test_}: ZERO hits on all of them. The only `django` hit is L1 `"""Twin-artifact model for django__django-12155.` -- the instance id the consumer is already solving -- and the only `import` hits are the three Nagini/typing imports (L37-39). The repo domain (docstrings, admindocs, docutils) is never named; every operation is carried abstractly over per-line leading-whitespace amounts (List[int]/PSeq[int]). Mechanical screen re-run first-hand: leakage.screen(model.py, NaginiBackend, gold patch, problem_statement, test_patch) -> hard_failures [], soft [] (agrees with the recorded G-LEAK `spec view clean`, and G-LEAK's recorded model.py hash 8c5901ca == the current file, so that gate is fresh).

DERIVABILITY FROM problem_statement (hints_text EXCLUDED). The public statement is unusually explicit: it quotes the culprit `indent = min(len(line) - len(line.lstrip()) for line in lines if line.lstrip())`, diagnoses "The problem is that the indentation of the first line is 0", and gives the fix verbatim: "The solution is to skip the first line: indent = min(... for line in lines[1:] if line.lstrip())". The spec view's discriminator -- margin = smallest leading whitespace over the NON-BLANK lines OTHER THAN the first (`min_indent_from(s, 1)`, consumed by `dedented`) -- is exactly that public sentence restated in the int carrier. The narrative paragraph ("measured WITHOUT regard to the first line's indentation ... a naive measurement that also folds in the first line's indentation would, for a first line beginning at column zero, find a common amount of zero and leave every body line indented") is a paraphrase of the two public diagnosis sentences, so it discloses nothing past them.

LOAD-BEARING TEST (run, not asserted). Built prose-stripped twins with an AST pass that deletes the module docstring, every function docstring, and every non-marker comment, keeping only region markers + formal text (model_bare.py 116 lines, model_prepatch_bare.py 110 lines). `bash scripts/nagini_verify.sh model_bare.py` -> "Verification successful", exit 0, 21.9s. `bash scripts/nagini_verify.sh model_prepatch_bare.py` -> exit 1, `model_prepatch_bare.py:71: Postcondition of dedent_block might not hold. Assertion (ToSeq(Result()) == dedented(ToSeq(eff))) might not hold`, 22.5s. markers.same_spec on both the plain pair and the bare pair -> True, so the prepatch failure is an impl-only refutation, not a spec difference. Conclusion: ALL discriminating power sits in the FORMAL `min_indent_from(s, 1)`; the prose is strictly non-load-bearing narration of something public anyway. Unstripped controls agree: model.py verifies (exit 0, 22.85s), model_prepatch.py fails on the same postcondition (exit 1, 22.06s).

THE ONE CLAUSE ABSENT FROM problem_statement, and why it is not a leak. "When there is no non-blank line after the first, nothing is removed" (`clamp_margin`: negative -> 0) is the repo's min()-over-empty case, whose repo-level fix (`default=0`) appears ONLY in hints_text and whose gold realisation is cleandoc's `margin = sys.maxsize` / `if margin < sys.maxsize`. I did not accept "it's only in hints" as an excuse; I tested whether the clause encodes a gold DECISION or is a totality artifact: exhaustively over every sequence of length 0..6 on alphabet {-1,-3,0,1,4,8}, for each of the 379 inputs where min_indent_from(s,1) < 0 I recomputed `dedented` with the removed amount forced to each of {0, -1, 7, -5, `10**9`, `2**70`} -> 0 divergences from the clamped result.

Reason: with no non-blank line after the first, the tail is all blanks and remove_margin maps a blank to -1 regardless of the amount, so the clamp VALUE is observationally vacuous. It exists only to make the total pure function well-defined at the min-fold identity, so it recovers nothing about the edit. Likewise the sign-vs-magnitude choice for NO_AMOUNT() is justified inside the carrier (an int is unbounded, so any large marker would alias a reachable amount) -- a modeling argument, not a disclosure of `sys.maxsize`, which never appears.

**UNCHANGED-BEHAVIOUR CLAUSE.** "The very first line always has its own leading whitespace removed in full" (`first_line`) is `lines[0].lstrip()`, IDENTICAL pre- and post-patch (refinement.md A3; visible in the pre-patch body the gold diff deletes, and in the repo at base_commit the consumer already has). Restating behaviour the edit does not change cannot leak the edit, and dropping it would make the spec incomplete.

SUPPORTING GATES RE-RUN FIRST-HAND so the disposition is my measurement: `python axiom_check.py` -> exit 0, "deep model `dedented` == real inspect.cleandoc on 13 boundary + 40000 fuzz docstrings; == marker-free reference on 20049 summaries carrying amounts up to `2**70`; FAIL_TO_PASS discriminator separates fixed (lines[1:]) from pre-patch (all lines) margin (4 vs 0)". `python conformance_check.py` -> exit 0, 100026 docstrings, 0 disagreements, seed 12155. G-VERIFY and G-DIFF reproduced above. G-INTEGRITY/G-RESOLVE recorded hashes for ../instance.json (a5a002b1ed6f) and ../patch.diff (b9fe08301b7b) match the parent-dir files exactly; patch.diff is the gold patch verbatim.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as a finding in its own right, per instructions). No file INSTRUCTS me how to record or which verdict is honest: `grep -rn -i -E 'honest recording is|submit (NO-)?LEAKAGE|recording convention|for the (auditor|reviewer|panel)'` finds nothing in model.py, mapping.md, refinement.md, axiom_check.py, or conformance_check.py. What the bundle DOES carry is an anchoring surface: verdict.md L1071-1097 and meta.json gates['G-PANEL-3'] hold a prior stamped `NO-LEAKAGE` with that agent's full rationale reproduced verbatim -- a gate-owned ledger record, not an instruction, but a strong prior on a re-audit. I could not have inherited it even had I wanted to, and the reason is a second finding: THAT RECORD IS STALE.

G-PANEL-3 (and G-PANEL, G-PANEL-1, G-PANEL-2, G-EQ) record model.py sha a975d4487160, while the current file is 8c5901ca39d0; the prior note reasons about a finite `BIG()` sentinel and `clamp_margin(min_indent_from(s,1)) == 0` probes, and `BIG(` does not occur anywhere in the current model.py, which uses a NEGATIVE `NO_AMOUNT() == -1`. So the spec was edited (evidently to repair the very finite-sentinel unfaithfulness G-PANEL-2 stamped) after those panels ran. I therefore judged the current bytes only.

Related ledger inconsistency, flagged though it is not mine to gate: meta.json TOP-LEVEL region_hashes are stale against the current file on pure / pre-conditions / invariants / impl / spec_view (recorded spec_view 28335a1bcfc3 vs current d1afd6995f76), whereas gates['G-HYGIENE'].data.region_hashes matches the current file on all 7 regions. My agreement with the stale prior verdict is a coincidence of independent measurement, and my clamp-vacuity argument replaces (and is strictly stronger than) its 'that case is only in hints_text' reasoning.

**CONCLUSION:** no line of the spec view conveys the gold edit beyond the public problem_statement. The discriminator the view formalizes (`min_indent_from(s, 1)`) is stated verbatim in the problem_statement as the proposed fix; the sole clause not in the statement (the empty-fold clamp) is provably observationally vacuous; every repo-level token of the gold edit is confined to the audit-side twin documents outside the consumer view. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
