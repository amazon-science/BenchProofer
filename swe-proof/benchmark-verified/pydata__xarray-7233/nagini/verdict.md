# P2 adversarial audit — pydata__xarray-7233

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch_intersection.py`, `atk_2_drop_ax_leg.py`, `atk_3_ax_leg_only.py`, `atk_4_overwide_iw.py`, `atk_5_and_legs.py`, `atk_6_half_domain.py`, `atk_7_iw_out_of_domain.py`, `atk_8_divergent.py`, `atk_11_reversed_order.py`, `atk_12_vacuity_control.py`, `atk_13_overlap_hole.py`, `atk_14_ax_index_shift.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9_oracle_echo.py`, `atk_10_arith_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_intersection.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,26 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies((was_label[k] == 1 and is_window[k] == 1) or is_axis_name[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not ((was_label[k] == 1 and is_window[k] == 1) or is_axis_name[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
         if wl == 1 and iw == 1:
             sel = 1
-        if wl == 1:
-            sel = 1
         if ax == 1:
             sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies((was_label[k] == 1 and is_window[k] == 1) or is_axis_name[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not ((was_label[k] == 1 and is_window[k] == 1) or is_axis_name[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 2 — `atk_2_drop_ax_leg.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,24 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(was_label[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (was_label[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
-            sel = 1
         if wl == 1:
             sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies(was_label[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not (was_label[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 3 — `atk_3_ax_leg_only.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,24 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(is_axis_name[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (is_axis_name[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
-            sel = 1
-        if wl == 1:
-            sel = 1
         if ax == 1:
             sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies(is_axis_name[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not (is_axis_name[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 4 — `atk_4_overwide_iw.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,28 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(was_label[k] == 1 or is_window[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (was_label[k] == 1 or is_window[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
+        if wl == 1:
             sel = 1
-        if wl == 1:
+        if iw == 1:
             sel = 1
         if ax == 1:
             sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies(was_label[k] == 1 or is_window[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not (was_label[k] == 1 or is_window[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 5 — `atk_5_and_legs.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,24 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(was_label[k] == 1 and is_axis_name[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (was_label[k] == 1 and is_axis_name[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
+        if wl == 1 and ax == 1:
             sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies(was_label[k] == 1 and is_axis_name[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not (was_label[k] == 1 and is_axis_name[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 6 — `atk_6_half_domain.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,6 +137,7 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
+    half = len(was_label) // 2
     while i < len(was_label):
         # invariants-start
         Invariant(Acc(list_pred(was_label), 1 / 2))
@@ -145,42 +146,27 @@
         Invariant(len(was_label) == len(is_window))
         Invariant(len(was_label) == len(is_axis_name))
         Invariant(0 <= i and i <= len(was_label))
+        Invariant(half == len(was_label) // 2)
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
-                                                was_label[k] == 0 or was_label[k] == 1),
-                                         [[was_label[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(is_axis_name),
-                                                is_axis_name[k] == 0 or is_axis_name[k] == 1),
-                                         [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(k < half and (was_label[k] == 1
+                                                        or is_axis_name[k] == 1),
+                                                        result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (k < half and (was_label[k] == 1
+                                                             or is_axis_name[k] == 1)),
+                                                        result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
+        if i < half and (wl == 1 or ax == 1):
             sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
-                                      [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                              old[k] == result[k]),
```

Attack 7 — `atk_7_iw_out_of_domain.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,33 +154,26 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies((is_window[k] == 0 or is_window[k] == 1)
+                                                        and (was_label[k] == 1
+                                                             or is_axis_name[k] == 1),
+                                                        result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not ((is_window[k] == 0 or is_window[k] == 1)
+                                                             and (was_label[k] == 1
+                                                                  or is_axis_name[k] == 1)),
+                                                        result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
-            sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
-                                      [[result[k]]])))
+        if iw == 0 or iw == 1:
+            if wl == 1 or ax == 1:
+                sel = 1
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                              old[k] == result[k]),
```

Attack 8 — `atk_8_divergent.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -136,61 +136,13 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(was_label):
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(was_label), 1 / 2))
         Invariant(Acc(list_pred(is_window), 1 / 2))
         Invariant(Acc(list_pred(is_axis_name), 1 / 2))
-        Invariant(len(was_label) == len(is_window))
-        Invariant(len(was_label) == len(is_axis_name))
-        Invariant(0 <= i and i <= len(was_label))
         Invariant(Acc(list_pred(result)))
-        Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
-                                                was_label[k] == 0 or was_label[k] == 1),
-                                         [[was_label[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(is_axis_name),
-                                                is_axis_name[k] == 0 or is_axis_name[k] == 1),
-                                         [[is_axis_name[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
-                                         [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
-        wl = was_label[i]
-        iw = is_window[i]
-        ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
-        sel = 0
-        if wl == 1 and iw == 1:
-            sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
-                                      [[result[k]]])))
-        old = ToSeq(result)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             old[k] == result[k]),
-                                      [[old[k]]])))
-        result = result + [sel]
-        Assert(ToSeq(result) == old + PSeq(sel))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == old[k]),
-                                      [[result[k]]])))
-        Assert(result[i] == sel)
-        i = i + 1
+        pass
     return result
     # impl-end
```

Attack 9 — `atk_9_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,22 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(was_label[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (was_label[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
-        sel = 0
-        if wl == 1 and iw == 1:
-            sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
+        sel = promoted(wl, iw, ax)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies(was_label[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not (was_label[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 10 — `atk_10_arith_echo.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,22 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(was_label[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (was_label[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
-        sel = 0
-        if wl == 1 and iw == 1:
-            sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
+        sel = wl + ax - wl * ax
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies(was_label[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not (was_label[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 11 — `atk_11_reversed_order.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -136,61 +136,25 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(was_label):
+    i = len(was_label) - 1
+    while i >= 0:
         # invariants-start
         Invariant(Acc(list_pred(was_label), 1 / 2))
         Invariant(Acc(list_pred(is_window), 1 / 2))
         Invariant(Acc(list_pred(is_axis_name), 1 / 2))
         Invariant(len(was_label) == len(is_window))
         Invariant(len(was_label) == len(is_axis_name))
-        Invariant(0 <= i and i <= len(was_label))
+        Invariant(-1 <= i and i < len(was_label))
         Invariant(Acc(list_pred(result)))
-        Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
-                                                was_label[k] == 0 or was_label[k] == 1),
-                                         [[was_label[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(is_axis_name),
-                                                is_axis_name[k] == 0 or is_axis_name[k] == 1),
-                                         [[is_axis_name[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
-                                         [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(was_label) - i + 1))
+        Invariant(len(result) == len(was_label) - 1 - i)
+        Invariant(MustTerminate(i + 2))
         # invariants-end
         wl = was_label[i]
-        iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
+        if wl == 1 or ax == 1:
             sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
-                                      [[result[k]]])))
-        old = ToSeq(result)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             old[k] == result[k]),
-                                      [[old[k]]])))
         result = result + [sel]
-        Assert(ToSeq(result) == old + PSeq(sel))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == old[k]),
-                                      [[result[k]]])))
-        Assert(result[i] == sel)
-        i = i + 1
+        i = i - 1
     return result
     # impl-end
```

Attack 12 — `atk_12_vacuity_control.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,25 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies(was_label[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not (was_label[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
+        Assert(False)
         sel = 0
-        if wl == 1 and iw == 1:
+        if wl == 1 or ax == 1:
             sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies(was_label[k] == 1 or is_axis_name[k] == 1, result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not (was_label[k] == 1 or is_axis_name[k] == 1), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 13 — `atk_13_overlap_hole.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -154,32 +154,26 @@
                                                 is_axis_name[k] == 0 or is_axis_name[k] == 1),
                                          [[is_axis_name[k]]])))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
+                                                Implies((was_label[k] == 1 or is_axis_name[k] == 1) and not (was_label[k] == 1 and is_axis_name[k] == 1), result[k] == 1)),
                                          [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                Implies(not ((was_label[k] == 1 or is_axis_name[k] == 1) and not (was_label[k] == 1 and is_axis_name[k] == 1)), result[k] == 0)),
+                                         [[result[k]]])))
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
         iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
         sel = 0
-        if wl == 1 and iw == 1:
+        if wl == 1 or ax == 1:
             sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
+        if wl == 1 and ax == 1:
+            sel = 0
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
+                                             Implies((was_label[k] == 1 or is_axis_name[k] == 1) and not (was_label[k] == 1 and is_axis_name[k] == 1), result[k] == 1)),
+                                      [[result[k]]])))
+        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                             Implies(not ((was_label[k] == 1 or is_axis_name[k] == 1) and not (was_label[k] == 1 and is_axis_name[k] == 1)), result[k] == 0)),
                                       [[result[k]]])))
         old = ToSeq(result)
         Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
```

Attack 14 — `atk_14_ax_index_shift.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -147,50 +147,16 @@
         Invariant(0 <= i and i <= len(was_label))
         Invariant(Acc(list_pred(result)))
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(was_label),
-                                                was_label[k] == 0 or was_label[k] == 1),
-                                         [[was_label[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(is_axis_name),
-                                                is_axis_name[k] == 0 or is_axis_name[k] == 1),
-                                         [[is_axis_name[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                result[k] == promoted(was_label[k],
-                                                                      is_window[k],
-                                                                      is_axis_name[k])),
-                                         [[result[k]]])))
-        # the per-member pass consumes the caller's termination obligation
-        # with a strictly decreasing, bounded-below measure (len(was_label)-i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(was_label) - i + 1))
         # invariants-end
         wl = was_label[i]
-        iw = is_window[i]
         ax = is_axis_name[i]
-        # status: (windowed-axis labels) | (all prior labels) | (axis names)
+        if i + 1 < len(is_axis_name):
+            ax = is_axis_name[i + 1]
         sel = 0
-        if wl == 1 and iw == 1:
+        if wl == 1 or ax == 1:
             sel = 1
-        if wl == 1:
-            sel = 1
-        if ax == 1:
-            sel = 1
-        Assert(sel == promoted(wl, iw, ax))
-        # carry the per-member status fact across the append (trigger-aligned)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == promoted(was_label[k],
-                                                                   is_window[k],
-                                                                   is_axis_name[k])),
-                                      [[result[k]]])))
-        old = ToSeq(result)
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             old[k] == result[k]),
-                                      [[old[k]]])))
         result = result + [sel]
-        Assert(ToSeq(result) == old + PSeq(sel))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                             result[k] == old[k]),
-                                      [[result[k]]])))
-        Assert(result[i] == sel)
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit, pydata__xarray-7233 / nagini. Every attack is model.py (sha256 4c66fade...) with ONLY the impl region edited (axioms / @Pure promoted / Requires / Ensures byte-identical); the nested invariants region is edited alongside the impl exactly as model_prepatch.py does, and each wrong impl carries invariants describing what IT computes, so a rejection lands on the FROZEN POSTCONDITION rather than on an unprovable annotation.

SAME-SPEC: all 14 attacks + positive control returned exit 0 ("SAME - attack shares the bundle's exact specification") from `python -m swebench_unified.adversary same-spec nagini pydata__xarray-7233 <f>`.

COMMAND for every attack: `python -m swebench_unified.adversary weakness nagini pydata__xarray-7233 <atk>.py` (run 3-at-a-time as background jobs; per-attack stdout kept <atk>.out).

POSITIVE CONTROL: positive_control.py (byte-identical to model.py) -> exit 0, CANDIDATE (verifies, 25.1s). Positive control verifies.

REJECTED (exit 2, "attack does not verify - the spec rejected this impl") - 12 of 14:
- atk_1_prepatch_intersection.py - PREPATCH BUG re-encoded: sel = (wl AND iw) OR ax, i.e. `should_be_coords = set(window_dim) & set(self.obj.coords)` with the insertion leg kept. REJECTED. prepatch_reproduced=TRUE.
- atk_2_drop_ax_leg.py - A-LEG PROBE, drops the third leg (sel = wl). REJECTED. NOTE: this is exactly the impl the PRIOR recorded G-EQ pass accepted as resolving echo atk_7, against the older 2-arg model.py; under the current 3-arg spec it is rejected, so the new is_axis_name leg is load-bearing and strictly strengthens the spec.
- atk_3_ax_leg_only.py - A-LEG PROBE, other side: only the container's axis-name leg (sel = ax). REJECTED.
- atk_4_overwide_iw.py - OVER-WIDE union sel = wl OR iw OR ax (`set(window_dim) | set(coords)`), promoting a plain data member merely NAMED like a windowed axis. REJECTED.
- atk_5_and_legs.py - legs ANDed instead of ORed (sel = wl AND ax). REJECTED.
- atk_6_half_domain.py - PARTIAL DOMAIN: correct only on members k < n//2. REJECTED.
- atk_7_iw_out_of_domain.py - PARTIAL DOMAIN via the UNCONSTRAINED flag: the precondition pins was_label and is_axis_name to 0/1 but leaves is_window free, so the impl answers correctly only when iw in {0,1} and returns 0 otherwise. REJECTED - the postconditions hold for ALL iw, so the unconstrained flag is not a hole.
- atk_8_divergent.py - CONTROL-FLOW EFFECT: `while True: pass`, never DELIVERS the status list. REJECTED - refinement.md leg 6's Requires(MustTerminate(2)) really closes the partial-correctness vacuity class.
- atk_11_reversed_order.py - INDEX PERMUTATION: right multiset of bits, member<->bit association reversed. REJECTED - the pointwise trigger pins position, not multiset.
- atk_13_overlap_hole.py - OVERLAP SUB-DOMAIN: correct everywhere except where BOTH legs fire (wl==1 and ax==1), the sub-domain two one-sided implications could leave unpinned. REJECTED - clause 1 (Result()[k] == promoted(...)) pins it.
- atk_14_ax_index_shift.py - member<->bit misassociation confined to the NEW leg: member k's own prior-label bit but its neighbour's axis-name bit. REJECTED.
- atk_12_vacuity_control.py - VACUITY CONTROL, `Assert(False)` in the loop body. REJECTED, so the loop body is reachable and the 11 rejections above are real rejections, not infeasible-path artifacts.

VERIFYING CANDIDATES (exit 0) - 2 of 14. BOTH had their faithful refined patch materialized against base_commit 51d37d1be95547059251076b3fadaa317750aab3 (generated by real `git diff` in a shared clone so the hunk headers are exact) and EXECUTED through the official harness via swebench_unified.harness.run_resolve:
- atk_9_oracle_echo.py (UNGROUNDED-ORACLE ECHO: the impl body is literally `sel = promoted(wl, iw, ax)`, so the whole correctness claim rests on the deep model plus the refinement map) -> patch_atk_9_oracle_echo.diff transcribes mapping.md s2 LITERALLY (enumerate obj.variables, read the three membership bits off coords / window_dim / reshaped.dims, apply the pointwise (wl AND iw) OR wl OR ax, hand the selected names to set_coords): completed=True RESOLVED=TRUE, F2P test_coarsen_construct_keeps_all_coords success, PASS_TO_PASS all success. This is the strongest A-leg check available here - the deep model's pointwise-bit reading, transcribed verbatim into the repo, IS correct behaviour.
- atk_10_arith_echo.py (ARITHMETIC ECHO sel = wl + ax - wl*ax, materializing the third leg explicitly with the is_window leg absent entirely) -> patch_atk_10_arith_echo.diff `should_be_coords = set(self.obj.coords) | (set(obj.variables) & set(reshaped.dims))`: completed=True RESOLVED=TRUE.
Both are correct echoes; neither breaks the spec. No verifying impl whose faithful patch fails to resolve was found.

EXTRA LEG-5 CORRESPONDENCE PROBE (beyond the required set): patch_leg5_probe.diff takes the verifying atk_9 impl but misreads the is_axis_name bit off the member's OWN name on BOTH arms, dropping mapping.md leg 5's DataArray-placeholder distinction. run_resolve: completed=True RESOLVED=TRUE. So leg 5's insertion-name-vs-own-name distinction is not observable on the shipped test set - it is a genuine and correctly-argued property of the real code (`_to_temp_dataset` inserts under _THIS_ARRAY, dataarray.py:222,530-531, so an array whose own name equals a rebuilt axis name is not promoted), but the F2P/P2P suite does not discriminate it. This is a precision remark about test-set reach, NOT a spec defect: it makes the spec's is_axis_name leg finer than the oracle can see, which is the safe direction (the spec is stronger than it needs to be), and I verified the direction that matters - the spec ADMITS the gold behaviour (positive control verifies) and REJECTS the prepatch bug.

A-LEG / DEEP-MODEL AUDIT. meta.json axioms=[] and `grep -c ContractOnly model.py` == 0, so there is NO A-consumed leg and no G-AX surface; axiom_check.py is legitimately absent. The one A-reference-shaped item is the deep model `promoted` (meta.deep_model_references[0], kind='deep model (not an axiom)').

Its correspondence to the real callees HOLDS, checked against the repo at base_commit: (a) the changed line rolling.py:976 post-patch is `(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)`, and since (W cap C) cup C == C this equals set(self.obj.coords) - matching the `(wl AND iw) OR wl` == wl part of promoted for any 0/1 wl; (b) the is_axis_name leg is grounded in merge.py:767-768, which I read at base_commit: `for dim, size in dims.items(): if dim in variables: coord_names.add(dim)` - the container does promote any inserted variable whose name equals one of its own dimension names, and this code is untouched by the patch, so the leg is a refinement of an UNCHANGED callee as refinement.md leg 3b claims, not a smuggled axiom; (c) dataset.py:1710 is `obj._coord_names.update(names)` - it ADDS and never resets, so the result's coordinate set really is the UNION of the insertion step and set_coords, which is why promoted is a union rather than an override.

All three readings confirmed against `git show 51d37d1b...` output. is_window is correctly left unconstrained by the precondition because the true behaviour is genuinely independent of window_dim membership - that independence IS the property the issue demands, and atk_7 confirms the free flag is not exploitable.

STALENESS FINDING (advisory, for the driver not the gate). The recorded G-EQ/G-PANEL-1 pass in meta.json was computed at 2026-08-15T10:07 against model.py sha256 4678fda650b7... - the OLDER TWO-ARG promoted(was_label, is_window). The current model.py is 4c66fadea535... with the third is_axis_name parameter (G-CONF/G-GOLD/G-VERIFY were re-stamped at 11:19-11:29 against the new hash, G-EQ was not). So the prior 15-attack audit never saw the new leg, and its recorded echo atk_7 (sel = wl) is in fact REJECTED by the current spec (my atk_2). meta.deep_model_references[0].encoded_property is likewise still the stale 2-arg text 'promoted(was_label, is_window) = ...' and does not mention is_axis_name. That is a metadata-freshness defect, not a spec defect - this audit re-derives G-EQ against the CURRENT 4c66fade model and finds it sound - but the stale deep_model_references string should be refreshed to describe the 3-arg union.

REFINEMENT.MD LEG AUDIT: 7 legs (1, 2, 3, 3b, 4, 5, 6), ALL tagged R. Zero A-consumed, zero A-reference, zero I, NO KIND-3 - consistent with the 'no axiom' claim, since the one operation that genuinely changed (which members become coordinates) is modeled DEEPLY by promoted + the verified loop rather than axiomatized. Legs 1-3 (name-set membership <-> 0/1 bit; & <-> pointwise AND; | <-> pointwise OR) are exact bijections on the finite fixed name universe, and the transform provably never adds/drops/renames a member (asserted per-case by conformance_check.py), so the fixed-length parallel-bit carrier is sound. Legs 1-3 are exercised by the atk_4 / atk_5 / atk_11 / atk_13 rejections plus the atk_9 literal transcription resolve; leg 3b by atk_2 / atk_3 / atk_14; leg 4 (set_coords unions rather than overrides) by the atk_10 resolve; leg 6 (MustTerminate) confirmed load-bearing by atk_8.

VERDICT: SOUND. 14 admissible same-spec attacks run to a verdict (12 rejected, of which one is the reproduced prepatch bug and one the Assert(False) vacuity control proving the loop body reachable; 2 verifying echoes), positive control verifies, and EVERY verifying candidate had its faithful refined patch materialized and EXECUTED through run_resolve with both RESOLVED=TRUE. No verifying wrong impl whose faithful patch fails to resolve was found, so verify => correct is not refuted for this bundle. One advisory metadata-freshness finding (stale G-EQ stamp + stale deep_model_references text) and one advisory precision remark (leg 5 is finer than the test set can observe); neither is a spec weakness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch_intersection.py`, `atk_2_drop_ax_leg.py`, `atk_3_ax_leg_only.py`, `atk_4_overwide_iw.py`, `atk_5_and_legs.py`, `atk_6_half_domain.py`, `atk_7_iw_out_of_domain.py`, `atk_8_divergent.py`, `atk_11_reversed_order.py`, `atk_12_vacuity_control.py`, `atk_13_overlap_hole.py`, `atk_14_ax_index_shift.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9_oracle_echo.py`, `atk_10_arith_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch_intersection.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_drop_ax_leg.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_ax_leg_only.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_overwide_iw.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_and_legs.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_half_domain.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_iw_out_of_domain.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_divergent.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_arith_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_reversed_order.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_vacuity_control.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_overlap_hole.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_ax_index_shift.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit, pydata__xarray-7233 / nagini. Every attack is model.py (sha256 4c66fade...) with ONLY the impl region edited (axioms / @Pure promoted / Requires / Ensures byte-identical); the nested invariants region is edited alongside the impl exactly as model_prepatch.py does, and each wrong impl carries invariants describing what IT computes, so a rejection lands on the FROZEN POSTCONDITION rather than on an unprovable annotation.

SAME-SPEC: all 14 attacks + positive control returned exit 0 ("SAME - attack shares the bundle's exact specification") from `python -m swebench_unified.adversary same-spec nagini pydata__xarray-7233 <f>`.

COMMAND for every attack: `python -m swebench_unified.adversary weakness nagini pydata__xarray-7233 <atk>.py` (run 3-at-a-time as background jobs; per-attack stdout kept <atk>.out).

POSITIVE CONTROL: positive_control.py (byte-identical to model.py) -> exit 0, CANDIDATE (verifies, 25.1s). Positive control verifies.

REJECTED (exit 2, "attack does not verify - the spec rejected this impl") - 12 of 14:
- atk_1_prepatch_intersection.py - PREPATCH BUG re-encoded: sel = (wl AND iw) OR ax, i.e. `should_be_coords = set(window_dim) & set(self.obj.coords)` with the insertion leg kept. REJECTED. prepatch_reproduced=TRUE.
- atk_2_drop_ax_leg.py - A-LEG PROBE, drops the third leg (sel = wl). REJECTED. NOTE: this is exactly the impl the PRIOR recorded G-EQ pass accepted as resolving echo atk_7, against the older 2-arg model.py; under the current 3-arg spec it is rejected, so the new is_axis_name leg is load-bearing and strictly strengthens the spec.
- atk_3_ax_leg_only.py - A-LEG PROBE, other side: only the container's axis-name leg (sel = ax). REJECTED.
- atk_4_overwide_iw.py - OVER-WIDE union sel = wl OR iw OR ax (`set(window_dim) | set(coords)`), promoting a plain data member merely NAMED like a windowed axis. REJECTED.
- atk_5_and_legs.py - legs ANDed instead of ORed (sel = wl AND ax). REJECTED.
- atk_6_half_domain.py - PARTIAL DOMAIN: correct only on members k < n//2. REJECTED.
- atk_7_iw_out_of_domain.py - PARTIAL DOMAIN via the UNCONSTRAINED flag: the precondition pins was_label and is_axis_name to 0/1 but leaves is_window free, so the impl answers correctly only when iw in {0,1} and returns 0 otherwise. REJECTED - the postconditions hold for ALL iw, so the unconstrained flag is not a hole.
- atk_8_divergent.py - CONTROL-FLOW EFFECT: `while True: pass`, never DELIVERS the status list. REJECTED - refinement.md leg 6's Requires(MustTerminate(2)) really closes the partial-correctness vacuity class.
- atk_11_reversed_order.py - INDEX PERMUTATION: right multiset of bits, member<->bit association reversed. REJECTED - the pointwise trigger pins position, not multiset.
- atk_13_overlap_hole.py - OVERLAP SUB-DOMAIN: correct everywhere except where BOTH legs fire (wl==1 and ax==1), the sub-domain two one-sided implications could leave unpinned. REJECTED - clause 1 (Result()[k] == promoted(...)) pins it.
- atk_14_ax_index_shift.py - member<->bit misassociation confined to the NEW leg: member k's own prior-label bit but its neighbour's axis-name bit. REJECTED.
- atk_12_vacuity_control.py - VACUITY CONTROL, `Assert(False)` in the loop body. REJECTED, so the loop body is reachable and the 11 rejections above are real rejections, not infeasible-path artifacts.

VERIFYING CANDIDATES (exit 0) - 2 of 14. BOTH had their faithful refined patch materialized against base_commit 51d37d1be95547059251076b3fadaa317750aab3 (generated by real `git diff` in a shared clone so the hunk headers are exact) and EXECUTED through the official harness via swebench_unified.harness.run_resolve:
- atk_9_oracle_echo.py (UNGROUNDED-ORACLE ECHO: the impl body is literally `sel = promoted(wl, iw, ax)`, so the whole correctness claim rests on the deep model plus the refinement map) -> patch_atk_9_oracle_echo.diff transcribes mapping.md s2 LITERALLY (enumerate obj.variables, read the three membership bits off coords / window_dim / reshaped.dims, apply the pointwise (wl AND iw) OR wl OR ax, hand the selected names to set_coords): completed=True RESOLVED=TRUE, F2P test_coarsen_construct_keeps_all_coords success, PASS_TO_PASS all success. This is the strongest A-leg check available here - the deep model's pointwise-bit reading, transcribed verbatim into the repo, IS correct behaviour.
- atk_10_arith_echo.py (ARITHMETIC ECHO sel = wl + ax - wl*ax, materializing the third leg explicitly with the is_window leg absent entirely) -> patch_atk_10_arith_echo.diff `should_be_coords = set(self.obj.coords) | (set(obj.variables) & set(reshaped.dims))`: completed=True RESOLVED=TRUE.
Both are correct echoes; neither breaks the spec. No verifying impl whose faithful patch fails to resolve was found.

EXTRA LEG-5 CORRESPONDENCE PROBE (beyond the required set): patch_leg5_probe.diff takes the verifying atk_9 impl but misreads the is_axis_name bit off the member's OWN name on BOTH arms, dropping mapping.md leg 5's DataArray-placeholder distinction. run_resolve: completed=True RESOLVED=TRUE. So leg 5's insertion-name-vs-own-name distinction is not observable on the shipped test set - it is a genuine and correctly-argued property of the real code (`_to_temp_dataset` inserts under _THIS_ARRAY, dataarray.py:222,530-531, so an array whose own name equals a rebuilt axis name is not promoted), but the F2P/P2P suite does not discriminate it. This is a precision remark about test-set reach, NOT a spec defect: it makes the spec's is_axis_name leg finer than the oracle can see, which is the safe direction (the spec is stronger than it needs to be), and I verified the direction that matters - the spec ADMITS the gold behaviour (positive control verifies) and REJECTS the prepatch bug.

A-LEG / DEEP-MODEL AUDIT. meta.json axioms=[] and `grep -c ContractOnly model.py` == 0, so there is NO A-consumed leg and no G-AX surface; axiom_check.py is legitimately absent. The one A-reference-shaped item is the deep model `promoted` (meta.deep_model_references[0], kind='deep model (not an axiom)').

Its correspondence to the real callees HOLDS, checked against the repo at base_commit: (a) the changed line rolling.py:976 post-patch is `(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)`, and since (W cap C) cup C == C this equals set(self.obj.coords) - matching the `(wl AND iw) OR wl` == wl part of promoted for any 0/1 wl; (b) the is_axis_name leg is grounded in merge.py:767-768, which I read at base_commit: `for dim, size in dims.items(): if dim in variables: coord_names.add(dim)` - the container does promote any inserted variable whose name equals one of its own dimension names, and this code is untouched by the patch, so the leg is a refinement of an UNCHANGED callee as refinement.md leg 3b claims, not a smuggled axiom; (c) dataset.py:1710 is `obj._coord_names.update(names)` - it ADDS and never resets, so the result's coordinate set really is the UNION of the insertion step and set_coords, which is why promoted is a union rather than an override.

All three readings confirmed against `git show 51d37d1b...` output. is_window is correctly left unconstrained by the precondition because the true behaviour is genuinely independent of window_dim membership - that independence IS the property the issue demands, and atk_7 confirms the free flag is not exploitable.

STALENESS FINDING (advisory, for the driver not the gate). The recorded G-EQ/G-PANEL-1 pass in meta.json was computed at 2026-08-15T10:07 against model.py sha256 4678fda650b7... - the OLDER TWO-ARG promoted(was_label, is_window). The current model.py is 4c66fadea535... with the third is_axis_name parameter (G-CONF/G-GOLD/G-VERIFY were re-stamped at 11:19-11:29 against the new hash, G-EQ was not). So the prior 15-attack audit never saw the new leg, and its recorded echo atk_7 (sel = wl) is in fact REJECTED by the current spec (my atk_2). meta.deep_model_references[0].encoded_property is likewise still the stale 2-arg text 'promoted(was_label, is_window) = ...' and does not mention is_axis_name. That is a metadata-freshness defect, not a spec defect - this audit re-derives G-EQ against the CURRENT 4c66fade model and finds it sound - but the stale deep_model_references string should be refreshed to describe the 3-arg union.

REFINEMENT.MD LEG AUDIT: 7 legs (1, 2, 3, 3b, 4, 5, 6), ALL tagged R. Zero A-consumed, zero A-reference, zero I, NO KIND-3 - consistent with the 'no axiom' claim, since the one operation that genuinely changed (which members become coordinates) is modeled DEEPLY by promoted + the verified loop rather than axiomatized. Legs 1-3 (name-set membership <-> 0/1 bit; & <-> pointwise AND; | <-> pointwise OR) are exact bijections on the finite fixed name universe, and the transform provably never adds/drops/renames a member (asserted per-case by conformance_check.py), so the fixed-length parallel-bit carrier is sound. Legs 1-3 are exercised by the atk_4 / atk_5 / atk_11 / atk_13 rejections plus the atk_9 literal transcription resolve; leg 3b by atk_2 / atk_3 / atk_14; leg 4 (set_coords unions rather than overrides) by the atk_10 resolve; leg 6 (MustTerminate) confirmed load-bearing by atk_8.

VERDICT: SOUND. 14 admissible same-spec attacks run to a verdict (12 rejected, of which one is the reproduced prepatch bug and one the Assert(False) vacuity control proving the loop body reachable; 2 verifying echoes), positive control verifies, and EVERY verifying candidate had its faithful refined patch materialized and EXECUTED through run_resolve with both RESOLVED=TRUE. No verifying wrong impl whose faithful patch fails to resolve was found, so verify => correct is not refuted for this bundle. One advisory metadata-freshness finding (stale G-EQ stamp + stale deep_model_references text) and one advisory precision remark (leg 5 is finer than the test set can observe); neither is a spec weakness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

ATTACK GOAL: find an input where the modeled function `rebuild_label_status` / `promoted` disagrees with the real repo callee. Reference = worktree at base_commit 51d37d1be95547059251076b3fadaa317750aab3 WITH patch.diff APPLIED (per instructions); base commit used only for callees the patch does not touch. Worked entirely in /tmp ( patched,  unpatched).

SPEC IDENTITY: `adversary same-spec nagini pydata__xarray-7233 atk.py` on a verbatim copy of model.py -> 'SAME', exit 0. markers.spec_view(model.py) == spec_view(model_prepatch.py) byte-identical, so the shipped G-DIFF rival really does hold the spec fixed.

SHIPPED MODEL VERIFIES: scripts/nagini_verify.sh atk_gold.py -> 'Verification successful' (19.09s, exit 0).

G-DIFF CONFIRMED: model_prepatch.py (same spec, pre-patch impl sel=(wl&iw)|ax) -> 'Verification failed', postcondition Result()[k]==promoted(...) might not hold. So the spec is strong enough to reject the buggy behavior; it is not a vacuous/one-sided bound.

MODEL SEMANTICS: promoted(wl,iw,ax) = wl OR ax (the (wl AND iw) disjunct is subsumed). Postconditions 2/3/4 partition the domain (wl=1 -> 1; ax=1 -> 1; wl=0 AND ax=0 -> 0), so every output bit is pinned -- an equality, not a bound. Requires(MustTerminate(2)) + loop Invariant(MustTerminate(len-i+1)) closes the diverging-impl lane at the method level.

### FAITHFULNESS EVIDENCE (independent of the bundle's own harness):
1. Bundle's conformance_check.py re-run against my patched worktree: 100023 checked, 0 disagreements, 11595 axis-name cases. Reproduces.
2. My OWN fuzzer (fuzz_indep.py, different generator, different seed 919191, my own bridge): 34749 returning inputs checked, diverge=0, member-universe changes=0, axis-bridge mismatches=0, 27155 axis-name cases. Widened beyond the bundle: 3 windowed dims, boundary in {exact,trim,pad} x side in {left,right}, reversed variable declaration order, shared name alphabet, DataArray rename onto replacement-axis names.
3. INSTRUMENTED INTERNAL CHECK (probe4.py) -- the strongest test, and one the bundle does not do. I re-implemented the patched `Coarsen.construct` tail with hooks and compared, per input, FOUR things the mapping claims rather than only the final answer: (a) model's rebuilt-axis set vs real `reshaped.dims`; (b) the model's `is_axis_name` leg vs the REAL `reshaped._coord_names` established by the insertion loop through merge_core merge.py:767-768; (c) the union claim result._coord_names == reshaped._coord_names | should_be_coords (i.e. that set_coords only ADDS, dataset.py:1710); (d) the final per-member bits. 2915 returning inputs, 0 problems of any of the four kinds. The `is_axis_name` leg and the set_coords-union refinement are therefore CHECKED against real internals, not assumed.
4. ABSTRACTION IS A FUNCTION (probe5.py) -- the sharpest faithfulness attack available, since the model collapses real xarray objects to 0/1 bit vectors. I enumerated 6312 returning + 1496 raising concrete inputs (all 2-member Datasets over every name permutation x 8 declaration roles x 4 replacement-name choices, both declaration orders) and BUCKETED them by their exact (was_label, is_window, is_axis_name) vector, looking for one bucket where the real code returns two DIFFERENT coordinate-bit answers. Result: 0 buckets with >=2 distinct returning outcomes (30 buckets total: 29 with exactly one returning outcome, 1 raise-only). The abstraction does not lose information that the real behavior depends on.
5. Exotic sub-domains hand-probed with no divergence: pandas MultiIndex on the coarsened axis (levels l1/l2 correctly promoted), datetime64 index coord, scalar/0-d coords and data vars, coordinate-only Datasets, uncoordinated windowed axis, member named like a SURVIVING axis, member named like the non-surviving coarsened axis, unnamed DataArray, and the _THIS_ARRAY placeholder arm (a DataArray literally named 'a' with window_dim t->('a','b') is correctly NOT promoted, bit 0, because it is inserted under the placeholder -- mapping.md's subtlest claim, and it holds).
6. Signature coverage reached (0,0,0),(0,0,1),(0,1,0),(1,0,0),(1,0,1),(1,1,0),(1,1,1); the 7th, (0,1,1), I targeted deliberately in probe3.py -- a data var named like a windowed axis whose name is also a replacement name -- and every witness either raises MissingDimensionsError or agrees.
7. DIRECTION CHECK (guards against the trap in my instructions): the F2P shape (DataArray with non-dim coord 'day', signature (1,0,0)) returns coords ['day'] on the PATCHED tree for both the DataArray and to_dataset arms, but on the UNPATCHED base tree the Dataset arm returns [] -- i.e. the model tracks the FIXED behavior. I did NOT report that base-vs-model delta as a divergence, since it is exactly the delta the patch introduces.

ONLY RESIDUE (raised, judged NOT a faithfulness defect): buckets exist that mix returning and raising concrete inputs -- e.g. wl=(0,0) iw=(0,0) ax=(1,0) returns for Dataset({'a':('x',..),'v':('t',..)}) declared 'v' first but raises MergeError('unable to determine if these variables should be coordinates') when 'a' is declared first, because merge_core's ambiguous_coords check is insertion-order sensitive; and one raise-only bucket (wl=(0,1,1) iw=(0,0,1) ax=(0,0,1), always MissingDimensionsError). This is a total-vs-partial domain question, not a value disagreement: the model is a pure total function over 0/1 bit lists and simply says nothing about which concrete objects xarray refuses to construct or reshape.

It never claims a wrong coordinate bit for an input the real code answers, and on every raise-only bucket there is no real return value to contradict. A spec is 'too strong' only if it demands an answer the real code contradicts; here every real answer matches. Direction also matters: the model does not model the raise domain, so it is silent there, not wrong -- and the bundle's mapping.md/refinement.md scope the claim to the rebuild's coordinate-selection outcome, which is what I verified.

CONCLUSION: ~135k+ inputs across the bundle harness and three independent probes, including internal-state instrumentation of the real merge_core/set_coords path and a bucket test proving the bit abstraction is well-defined, produced ZERO inputs where the modeled function disagrees with the real patched callee. I have no diverging input to cite. Spec is FAITHFUL (not too strong, no drift). Rubber-stamp explicitly avoided: the model verifies, the same-spec pre-patch rival FAILS, and G-DIFF discriminates.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Leakage / gold-reconstruction audit, pydata__xarray-7233 (nagini). Verdict: NO-LEAKAGE. All work in /tmp (worktree @ base_commit 51d37d1b, scratch); bundle unmodified (`git status --porcelain benchmark-verified/pydata__xarray-7233/` empty at exit).

NO RELAXATION IS CLAIMED, so this is a full-strength audit, not an inherited disposition. meta.json has no `relaxed_leakage` (key absent; json load -> None) and there is no RELAXED_LEAKAGE.md anywhere under benchmark-verified/pydata__xarray-7233/. The only 'relaxed' hits in the instance dir are two lines inside verdict.md, both of which are a PRIOR G-PANEL-3 note asserting the same absence -- prior-audit provenance, not a live relaxation. No file in the bundle addresses me: leakage.reviewer_directed() returns [] on all 11 files (instance.json, patch.diff, model.py, model_prepatch.py, mapping.md, refinement.md, properties.py, conformance_check.py, meta.json, pbt_result.json, verdict.md). The only 'G-PANEL' mentions are gate records in meta.json/verdict.md plus refinement.md:46 and properties.py:40/371/375/406 naming the non-termination counterexample class -- provenance for why MustTerminate is present, not an instruction on what to submit.

GOLD EDIT (what must not be reconstructible). xarray/core/rolling.py, Coarsen.construct tail: `should_be_coords = set(window_dim) & set(self.obj.coords)` widened to `(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)`. I confirmed the PRE-patch line verbatim at rolling.py:976 by reading the fresh /tmp worktree at 51d37d1b (not by trusting patch.diff).

SPEC VIEW MEASURED, NOT ASSERTED. Recomputed markers.spec_view(model.py, get_backend('nagini')) -> sha256 03d2c4a21f7e229564769f39addf1e62f8b2af44bccafe09ea1f08eb17cca0b0, 139 lines, byte-equal to the G-HYGIENE record's region_hashes.spec_view. The impl region is elided to `...  # implementation elided -- supplied by the consumer`, so the concrete set expression is absent from the solver-visible text. My own token scan of the COMPUTED view: 0 hits each for coarsen, construct, rolling, window_dim, should_be_coords, set_coords, reshaped, self.obj, obj.coords, merge_core, coord_names, intersection, demote, revert, narrow, widen, previously, 'set('. 'xarray' appears once = the public instance id in the docstring header. 'union'/'before' appear only as abstract flag-logic prose over was_label/is_axis_name bits. Test-leak check: 0 of the 3 test_patch function names (incl. the F2P test_coarsen_construct_keeps_all_coords) occur in the view.

RAN THE REAL GATE. leakage.screen(model.py, nagini, instance['patch'], instance['problem_statement'], instance['test_patch']) -> passed=True, hard_failures=[], warnings=[]. Screened against problem_statement ONLY, never hints_text (hints_text is '' here anyway). _patch_changed_symbols(gold) = {'construct'}, and 'construct' is already public in the problem_statement ('ds.Coarsen.construct'), so it is exempt by rule -- and independently it appears 0 times in the view.

SCREEN IS LIVE, NOT VACUOUS (positive controls, 3/3 caught): (a) injecting the gold added line as a spec-region comment -> L1 gold-patch line reproduced x2; (b) replacing a spec comment with 'fixes the bug where coordinates were previously demoted' -> L3 narration 'fixes'; (c) putting 'xarray/core/rolling.py' in the module docstring -> L2 patched file path. So the clean pass on the shipped file is a measurement, not a blind spot.

DISCRIMINATOR IS PUBLIC, AND I CHECKED IT IS LOAD-BEARING. The spec's discriminating postcondition is `was_label[k] == 1 -> Result()[k] == 1` (prior labelling status preserved, independent of is_window). The problem_statement states exactly this under 'What did you expect to happen?': 'All variables that were coordinates before the coarsen.construct stay as coordinates afterwards.'; the title supplies the coordinate-vs-dimension framing ('demotes non-dimensional coordinates to variables'). Substring checks against the public statement: 'stay as coordinates' True, 'were coordinates before' True, 'non-dimensional coordinates' True, 'demotes' True.

Load-bearing test (strip-the-narration equivalent): model_prepatch.py keeps the spec byte-identical (markers.same_spec(model, prepatch) = True) and reverts only the impl to the pre-patch selection; pinned verifier `bash scripts/nagini_verify.sh` gives 'Verification failed -- Postcondition of rebuild_label_status might not hold' on exactly the promoted-equality clause at pre.py:109-113, while the gold-faithful model.py returns 'Verification successful' in 23.0s. So the clause discriminates the gold from the pre-patch behaviour AND is derivable from the public problem_statement -- it is not spec-side smuggling.

THIRD LEG (is_axis_name) IS NOT A LEAK. The spec's third input bit and clause `is_axis_name[k] == 1 -> Result()[k] == 1` describe merge_core's standing dim-name auto-promotion (merge.py:767-768), which patch.diff does not touch and which behaves identically pre- and post-patch (the bundle's own G-PANEL-2 record measured this on both a clean base worktree and a patched one: coords [] -> ['year'] either way). A clause about an UNCHANGED callee constrains a sub-domain orthogonal to the edit; it localizes nothing about the gold delta and names no repo symbol in the view. It is a faithfulness question (G-PANEL-2 is recorded fail on it), not a leakage one, and it is out of scope for this gate.

BOOKKEEPING OBSERVATION (not leakage, flagged for the record). meta.json's TOP-LEVEL region_hashes.spec_view is 5cfba9a004bcf06a18b4b52dc8368050067bb30691bf230fe9fc1714d2325548, which does NOT match the current model.py (sha 4c66fade..., computed spec_view 03d2c4a2...); the nested G-HYGIENE data block does match. Likewise G-EQ and the prior G-PANEL-3 record cite model.py 4678fda6..., an earlier revision, so those two records are stale relative to the shipped file -- my leakage measurements above were all recomputed against the current 4c66fade model.py rather than inherited. This affects gate-freshness bookkeeping, not the leakage disposition.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
