# P2 adversarial audit — mwaskom__seaborn-3187

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 22 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_pp1.py`, `atk_pp2.py` |

**Non-vacuity.** The positive control `atk_0.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no attack reached CANDIDATE, so no faithful refined patch was materializable and no run_resolve was triggered. 22 distinct same-spec wrong impls (every one `same-spec` exit 0, spec byte-identical; only the two impl regions differ) were each run through `python -m swebench_unified.adversary weakness nagini mwaskom__seaborn-3187 <path>`; ALL 22 returned exit 2 = NOT-A-COUNTEREXAMPLE (does not verify). Positive control atk_0.py (== model.py byte-for-byte, `diff` empty) VERIFIES in 18.65s. Vacuity control atk_vac.py (gold impl + `Assert(False)` before the return) FAILS at BOTH sites (atk_vac.py:319 and :398, 'Assert might fail. Assertion False might not hold.'), so the postconditions are reached on a feasible path and the 22 rejections are real rather than artefacts of an infeasible path. Every rejection was re-run through `bash scripts/nagini_verify.sh` to record WHICH clause rejected it, and each lands on a real spec clause at BOTH sites (see notes).
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -288,7 +288,7 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    res0 = fmt.residual
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -299,15 +299,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+        Invariant(fmt.residual == res0)
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
@@ -366,7 +362,7 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    res0 = fmt.residual
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -377,15 +373,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+        Invariant(fmt.residual == res0)
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -288,7 +288,7 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    res0 = fmt.residual
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -299,15 +299,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+        Invariant(fmt.residual == res0)
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
@@ -316,6 +312,7 @@
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
         i = i + 1
+    fmt.residual = False
     return result
     # impl-end
 
@@ -366,7 +363,7 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    res0 = fmt.residual
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -377,15 +374,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+        Invariant(fmt.residual == res0)
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
@@ -394,5 +387,6 @@
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
         i = i + 1
+    fmt.residual = False
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -302,16 +302,10 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        lab = rendered_labels(fmt.convention, PSeq(locs[i]), fmt.residual,
+                              fmt.view_lo, fmt.view_hi)[0]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
@@ -380,16 +374,10 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        lab = rendered_labels(fmt.convention, PSeq(locs[i]), fmt.residual,
+                              fmt.view_lo, fmt.view_hi)[0]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,6 +289,11 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    tlo = fmt.view_lo
+    thi = fmt.view_hi
+    if len(locs) > 0:
+        tlo = locs[0]
+        thi = locs[len(locs) - 1]
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -303,15 +308,11 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+            ToSeq(locs), fmt.residual, tlo, thi).take(i))
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+                              tlo, thi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
@@ -367,6 +368,11 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    tlo = fmt.view_lo
+    thi = fmt.view_hi
+    if len(locs) > 0:
+        tlo = locs[0]
+        thi = locs[len(locs) - 1]
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -381,15 +387,11 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+            ToSeq(locs), fmt.residual, tlo, thi).take(i))
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+                              tlo, thi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -288,7 +288,8 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    if len(locs) > 0:
+        fmt.residual = False
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -304,10 +305,6 @@
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
@@ -366,7 +363,8 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    if len(locs) > 0:
+        fmt.residual = False
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -382,10 +380,6 @@
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -302,16 +302,9 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        lab = locs[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
@@ -380,16 +373,9 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        lab = locs[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -302,16 +302,13 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
+        j = i
+        if i + 1 == len(locs):
+            j = 0
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+                              fmt.view_lo, fmt.view_hi)[j]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
@@ -380,16 +377,13 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
+        j = i
+        if i + 1 == len(locs):
+            j = 0
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+                              fmt.view_lo, fmt.view_hi)[j]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,6 +289,7 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    fmt.convention = 1
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -300,14 +301,10 @@
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
         Invariant(not fmt.residual)
-        Invariant(fmt.convention == conv0)
+        Invariant(fmt.convention == 1)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
@@ -367,6 +364,7 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    fmt.convention = 1
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -378,14 +376,10 @@
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
         Invariant(not fmt.residual)
-        Invariant(fmt.convention == conv0)
+        Invariant(fmt.convention == 1)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -298,24 +298,16 @@
         Invariant(Acc(list_pred(locs), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
-        Invariant(len(result) == i)
+        Invariant(len(result) >= i)
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
-        Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                               fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
-        Assert(ToSeq(result) == old_seq + PSeq(lab))
-        i = i + 1
+        i = i + 0
     return result
     # impl-end
 
@@ -376,23 +368,15 @@
         Invariant(Acc(list_pred(locs), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
-        Invariant(len(result) == i)
+        Invariant(len(result) >= i)
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
-        Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                               fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
-        Assert(ToSeq(result) == old_seq + PSeq(lab))
-        i = i + 1
+        i = i + 0
     return result
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,6 +289,8 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    fmt.view_lo = 0
+    fmt.view_hi = 0
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -301,13 +303,9 @@
         Invariant(len(result) == i)
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
-        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
+        Invariant(fmt.view_lo == 0 and fmt.view_hi == 0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
@@ -316,6 +314,8 @@
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
         i = i + 1
+    fmt.view_lo = lo0
+    fmt.view_hi = hi0
     return result
     # impl-end
 
@@ -367,6 +367,8 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    fmt.view_lo = 0
+    fmt.view_hi = 0
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -379,13 +381,9 @@
         Invariant(len(result) == i)
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
-        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
+        Invariant(fmt.view_lo == 0 and fmt.view_hi == 0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
@@ -394,5 +392,7 @@
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
         i = i + 1
+    fmt.view_lo = lo0
+    fmt.view_hi = hi0
     return result
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -366,7 +366,7 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    res0 = fmt.residual
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -377,15 +377,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+        Invariant(fmt.residual == res0)
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -303,14 +303,10 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+            ToSeq(locs), True, fmt.view_lo, fmt.view_hi).take(i))
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
+        lab = rendered_labels(fmt.convention, ToSeq(locs), True,
                               fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
@@ -381,14 +377,10 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
-        # The build walks the tick locations once: `i` grows by exactly one per
-        # pass and `len(locs)` cannot change (the input is read-only at 1/2
-        # permission), so `len(locs) - i + 1` strictly decreases; the guard
-        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
+            ToSeq(locs), True, fmt.view_lo, fmt.view_hi).take(i))
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
+        lab = rendered_labels(fmt.convention, ToSeq(locs), True,
                               fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -303,15 +303,16 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
+            ToSeq(locs) + ToSeq(locs), fmt.residual,
+            fmt.view_lo, fmt.view_hi).take(i))
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        lab = rendered_labels(fmt.convention, ToSeq(locs) + ToSeq(locs),
+                              fmt.residual, fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
@@ -381,15 +382,16 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
+            ToSeq(locs) + ToSeq(locs), fmt.residual,
+            fmt.view_lo, fmt.view_hi).take(i))
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        lab = rendered_labels(fmt.convention, ToSeq(locs) + ToSeq(locs),
+                              fmt.residual, fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,6 +289,7 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    fmt.convention = conv0 + 1
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -300,7 +301,7 @@
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
         Invariant(not fmt.residual)
-        Invariant(fmt.convention == conv0)
+        Invariant(fmt.convention == conv0 + 1)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
@@ -316,6 +317,7 @@
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
         i = i + 1
+    fmt.convention = conv0
     return result
     # impl-end
 
@@ -367,6 +369,7 @@
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
     fmt.residual = False
+    fmt.convention = conv0 + 1
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -378,7 +381,7 @@
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
         Invariant(not fmt.residual)
-        Invariant(fmt.convention == conv0)
+        Invariant(fmt.convention == conv0 + 1)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
@@ -394,5 +397,6 @@
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
         i = i + 1
+    fmt.convention = conv0
     return result
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -302,16 +302,19 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
+        Invariant(len(result) == i)
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        if i == 0:
+            lab = rendered_labels(fmt.convention, PSeq(locs[0]), fmt.residual,
+                                  fmt.view_lo, fmt.view_hi)[0]
+        else:
+            lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
+                                  fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
@@ -380,16 +383,19 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
+        Invariant(len(result) == i)
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+        if i == 0:
+            lab = rendered_labels(fmt.convention, PSeq(locs[0]), fmt.residual,
+                                  fmt.view_lo, fmt.view_hi)[0]
+        else:
+            lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
+                                  fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

```diff
@@ -288,7 +288,10 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    res1 = fmt.residual
+    if len(locs) > 0:
+        fmt.residual = False
+        res1 = False
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -299,7 +302,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
+        Invariant(fmt.residual == res1)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
@@ -366,7 +369,10 @@
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
+    res1 = fmt.residual
+    if len(locs) > 0:
+        fmt.residual = False
+        res1 = False
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -377,7 +383,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
+        Invariant(fmt.residual == res1)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

```diff
@@ -303,7 +303,7 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
+            ToSeq(locs), fmt.residual, fmt.view_hi, fmt.view_lo).take(i))
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
@@ -311,7 +311,7 @@
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+                              fmt.view_hi, fmt.view_lo)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
@@ -381,7 +381,7 @@
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
-            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
+            ToSeq(locs), fmt.residual, fmt.view_hi, fmt.view_lo).take(i))
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
@@ -389,7 +389,7 @@
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
-                              fmt.view_lo, fmt.view_hi)[i]
+                              fmt.view_hi, fmt.view_lo)[i]
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

```diff
@@ -308,7 +308,6 @@
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
-        Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                               fmt.view_lo, fmt.view_hi)[i]
@@ -386,7 +385,6 @@
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
         # permission), so `len(locs) - i + 1` strictly decreases; the guard
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
-        Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
         lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                               fmt.view_lo, fmt.view_hi)[i]
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

```diff
@@ -315,7 +315,7 @@
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
-        i = i + 1
+        i = i + 0
     return result
     # impl-end
 
@@ -393,6 +393,6 @@
         old_seq = ToSeq(result)
         result.append(lab)
         Assert(ToSeq(result) == old_seq + PSeq(lab))
-        i = i + 1
+        i = i + 0
     return result
     # impl-end
```

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

```diff
@@ -302,7 +302,7 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
+        Invariant(ToSeq(result) == rendered_labels(0,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
@@ -310,7 +310,7 @@
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
+        lab = rendered_labels(0, ToSeq(locs), fmt.residual,
                               fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
@@ -380,7 +380,7 @@
         Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
-        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
+        Invariant(ToSeq(result) == rendered_labels(0,
             ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
         # The build walks the tick locations once: `i` grows by exactly one per
         # pass and `len(locs)` cannot change (the input is read-only at 1/2
@@ -388,7 +388,7 @@
         # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
         Invariant(MustTerminate(len(locs) - i + 1))
         # invariants-end
-        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
+        lab = rendered_labels(0, ToSeq(locs), fmt.residual,
                               fmt.view_lo, fmt.view_hi)[i]
         old_seq = ToSeq(result)
         result.append(lab)
```

Attack 21 — `atk_pp1.py` → rejected (same spec, does not verify — good)

```diff
@@ -285,10 +285,12 @@
         [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
+    # PRE-STATE (site 1): the formatter is left in the rendering mode it
+    # arrived in, with residual rendering enabled, so a magnitude common to the
+    # ticks is factored out of all of them and dropped.
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -299,7 +301,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
```

Attack 22 — `atk_pp2.py` → rejected (same spec, does not verify — good)

```diff
@@ -363,10 +363,12 @@
         [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
+    # PRE-STATE (site 2): the formatter is left in the rendering mode it
+    # arrived in, with residual rendering enabled, so a magnitude common to the
+    # ticks is factored out of all of them and dropped.
     conv0 = fmt.convention
     lo0 = fmt.view_lo
     hi0 = fmt.view_hi
-    fmt.residual = False
     result = []  # type: List[int]
     i = 0
     while i < len(locs):
@@ -377,7 +379,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(locs))
         Invariant(len(result) == i)
-        Invariant(not fmt.residual)
         Invariant(fmt.convention == conv0)
         Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
         Invariant(ToSeq(result) == rendered_labels(fmt.convention,
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0.py`

```python
"""Twin-artifact model for mwaskom__seaborn-3187.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a numeric legend is built for a quantitative variable, each legend entry
  pairs a tick location with a LABEL: the text a numeric tick formatter renders
  for that location.  The legend keeps the per-tick label texts and nothing
  else, so the number a reader can recover from an entry is whatever its text
  reads back as.  A formatter that is allowed to factor a magnitude common to
  the ticks out of them renders each tick as a small RESIDUAL and parks the
  factored magnitude in a separate string the legend never records -- so with
  residual rendering left enabled, the legend's labels read back to residuals
  instead of to the values they are supposed to describe.

  The formatter is a piece of SHARED, MUTABLE state: it arrives already built
  (with residual rendering possibly enabled, which is its ordinary default), it
  is the thing that actually renders the label text, and it outlives the
  legend-building step.  So the required behaviour has two inseparable halves,
  and an implementation must deliver BOTH:

    (1) the legend's labels must be THE LABELS THAT FORMATTER RENDERS for the
        tick set it is given -- the legend reports the formatter's own text, it
        does not write label text by some private route of its own, it does not
        render a tick in isolation (a formatter chooses ONE common way of
        writing the whole tick set, so a tick's label is not a function of that
        tick alone), and it does not reorder or drop any of them; and

    (2) the formatter must be left with residual rendering disabled, so that
        (1) yields labels that read back to the ticks' FULL absolute values,
        for tick locations of every magnitude -- including large ones whose true
        value greatly exceeds any residual.

  Half (1) alone is satisfied by a formatter that still factors a magnitude
  out; half (2) alone is satisfied by sidestepping the formatter and writing
  the numbers into the legend directly, which both puts text in the legend that
  the formatter never produced and leaves the formatter -- the object the
  surrounding code goes on using to render this same axis -- still in its
  magnitude-factoring mode.  Only both together describe a legend that is
  correct *and* consistent with the ticks it labels.

  A formatter also has a RENDERING CONVENTION, settled when it was built and
  none of the legend builder's business: does it write each tick's own value
  into the label text in full -- what a numeric legend's formatter does when
  nothing else has been asked of it -- or does it re-express the ticks in a
  unit or at a precision of its own choosing (an SI-prefixed unit, a rounded
  number of digits, ...)?  Only the first can render labels that read back to
  full tick values at all, so that is the convention half (2)'s reading
  guarantee is stated for; the builder may not change a formatter's convention,
  and for the other conventions no reading guarantee is claimed (nor
  available): their labels do not read back to their ticks even with residual
  rendering disabled (axiom_check.py).

  A formatter renders against one further input: the numeric RANGE of the axis
  it is attached to, i.e. the interval the legend's variable covers, which is
  announced to that axis before any label is rendered.  That range is
  INDEPENDENT of the tick locations -- a legend's ticks are chosen inside its
  range, and the range is normally wider than the ticks it contains -- and
  several conventions decide from it how to write a tick (which decade to name,
  which unit to prefix, how many digits to carry).  So a label sequence is a
  function of the tick set AND that range together, and an implementation must
  render against THE RANGE THE FORMATTER ITSELF READS: rendering against the
  span of the tick set, or against any other interval, is a different label
  sequence.  Like the convention, the range is settled before the legend is
  built and is not the builder's to change.

There are two independent places that build such numeric legends; each must
honour the same guarantee.  Both are modelled below as the sequence of labels
emitted, the readings of those labels, and the rendering mode the formatter is
left in.

Tick locations and the axis range are modelled as `int` (the exercised
locations are integral and the property -- labels reading back to full tick
values vs. to residuals -- is exact at those values; refinement.md justifies the
int carrier).  A LABEL is modelled as an opaque `int` code standing for its
exact text, so two labels are equal in the model exactly when their texts are
identical: the model is deliberately NOT allowed to see a label as the number it
reads back to, because two different texts can read back to the same number and
it is the text the legend keeps.  The formatter is modelled as an OBJECT
carrying its rendering convention, the axis range it renders against, and the
mutable flag controlling residual rendering, since the guarantee is about the
state it is left in and not only about what is returned; the deep models
`rendered_labels` / `reading` spell out
(convention, tick set, mode, range) -> label sequence and label -> number, and
are validated against the real `matplotlib` formatter by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def reading(label: int) -> int:
    """The number a reader recovers by reading a rendered label back as a
    number.  Labels are opaque codes for their exact text, and this is the only
    thing the model may learn about a label's text: the legend records the text
    alone, so a label's reading is all the numeric information the legend
    conveys about its tick.

    Deliberately UNINTERPRETED (no Ensures): nothing about the number a label
    reads back to is available except through the one axiom on
    `rendered_labels` below.  Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX).
    """


@Pure
@ContractOnly
def rendered_labels(convention: int, ticks: PSeq[int], residual: bool,
                    view_lo: int, view_hi: int) -> PSeq[int]:
    """The labels a numeric tick formatter renders for the tick locations
    `ticks`, in order, given the formatter's rendering convention, whether
    residual rendering is enabled, and the numeric range `view_lo .. view_hi`
    of the axis it is attached to.

    The WHOLE tick set is an argument, and the whole label sequence the result,
    because a formatter picks ONE way of writing all of the ticks it is given
    and renders each of them that way: a tick's label is not a function of that
    tick alone, and the labels for a tick set are not recoverable by rendering
    its members one at a time.

    The axis range is an argument BECAUSE IT IS AN INPUT THE FORMATTER READS
    and it is not determined by the tick set: the ticks of a legend are chosen
    inside its variable's range, and that range is normally wider than them.
    Several conventions consult it -- which decade to name, which unit to
    prefix, how many digits to carry -- so two calls that differ only in the
    range can render different label sequences (measured for three of the
    conventions in axiom_check.py `check_range_dependence`), and a label
    sequence rendered against the tick set's own span is in general NOT the one
    the formatter renders.

    `convention == 0` is the FULL-VALUE convention: the one a numeric legend's
    formatter has when nothing else has been asked of it -- it writes each
    tick's own value into the label text, in full.  Any other convention
    re-expresses ticks in a unit or at a precision of the formatter's own
    choosing, and there no reading guarantee holds or is claimed.

    The properties the proofs rely on (the weakest sufficient contract):
    a formatter renders exactly one label per tick, and a full-value formatter
    with residual rendering DISABLED factors nothing out, so each of its labels
    reads back to the full value of the tick it describes -- whatever the axis
    range is (measured: axiom_check.py drives the range independently of the
    tick set).  While residual rendering is enabled the readings are
    unconstrained -- which is exactly the information the legend loses.
    Nothing else about a label is knowable: two formatter states, two tick sets
    or two axis ranges need not render alike.

    The one-label-per-tick contract below describes the label sequence for the
    inputs a convention renders.  A convention need not have a rendering for
    every input at all: a formatter that re-expresses ticks in a unit chosen
    from the WIDTH of the axis range may have nothing to say about a range of
    no width, and may then raise rather than return labels.  Where that happens
    there is no label sequence to describe and no legend is produced at all, so
    there is no legend for this model to be silent about.  Only a
    width-reading convention can be so restricted; axiom_check.py measures the
    restriction exactly (it may be empty), and conformance_check.py compares
    whole outcomes, so the refinement and the real site are held to producing
    no legend together on precisely those inputs.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Ensures(len(Result()) == len(ticks))
    Ensures(Implies(convention == 0 and not residual,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(ticks),
                        reading(Result()[k]) == ticks[k]),
                        [[Result()[k]]]))))
# axioms-end


# pure-start
class TickFormatter:
    """The numeric tick formatter the legend renders its label text with: a
    piece of shared mutable state that arrives ALREADY BUILT and outlives the
    legend-building step.

    `convention` is the rendering convention it was built with (see
    `rendered_labels`): `0` is the full-value convention, any other value is a
    formatter that re-expresses ticks in a unit or at a precision of its own.
    It is not a mode and no legend builder may change it -- the guarantees
    below pin it unchanged across the call.

    `view_lo` / `view_hi` are the numeric range of the axis this formatter is
    attached to: an input it reads when deciding how to write a tick, settled
    (like the convention) before the legend is built, and likewise not the
    builder's to change.  It is carried on the formatter rather than passed in
    because it is state the formatter reaches on its own, and because a builder
    that rendered against some other interval would still be handing this
    object on to render this same axis.

    `residual` is the residual-rendering mode: while it is enabled the
    formatter may factor a magnitude common to the ticks out of them and render
    each tick as a small residual.  It is mutable precisely because "which mode
    is this formatter left in" is part of what a legend builder is answerable
    for: the object is still there, and still rendering this axis, after the
    legend is built.  Which rendering controls of a real formatter it stands
    for is a refinement-mapping detail (refinement.md)."""

    def __init__(self, convention: int, residual: bool,
                 view_lo: int, view_hi: int) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.convention) and self.convention == convention)  # type: ignore
        Ensures(Acc(self.residual) and self.residual == residual)  # type: ignore
        Ensures(Acc(self.view_lo) and self.view_lo == view_lo)  # type: ignore
        Ensures(Acc(self.view_hi) and self.view_hi == view_hi)  # type: ignore
        self.convention = convention
        self.residual = residual
        self.view_lo = view_lo
        self.view_hi = view_hi


@Pure
def legend_reads_ticks(labels: PSeq[int], ticks: PSeq[int]) -> bool:
    """Whole-legend reading guarantee: the legend carries one label per tick
    and EVERY one of them reads back to the full value of the tick location it
    describes.  Stated over the whole label sequence rather than per entry,
    because the failure being ruled out is the one where a magnitude common to
    the ticks is factored out of all of them at once."""
    return len(labels) == len(ticks) and Forall(int, lambda k: (
        Implies(0 <= k and k < len(ticks), reading(labels[k]) == ticks[k]),
        [[labels[k]]]))
# pure-end


def legend_values_continuous(fmt: TickFormatter,
                             locs: List[int]) -> List[int]:
    # pre-conditions-start
    # The formatter arrives already built, in WHATEVER rendering mode it
    # happens to be in -- residual rendering enabled is its ordinary default,
    # so both modes are admitted here and neither is assumed -- with WHATEVER
    # rendering convention it was built with, so no convention is excluded
    # either, and attached to an axis of WHATEVER range: no relation between
    # that range and the tick locations is assumed.
    Requires(Acc(fmt.convention) and Acc(fmt.residual))
    Requires(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Requires(Acc(list_pred(locs), 1 / 2))
    # The legend must actually be BUILT: without this, every guarantee below is
    # claimed only of runs that reach the return, so a rendering loop that
    # never finishes would satisfy them vacuously. Level 3 leaves room below
    # for the list operations that grow the label sequence.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fmt.convention) and Acc(fmt.residual))
    Ensures(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Ensures(Acc(list_pred(locs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One label per tick location.
    Ensures(len(Result()) == len(locs))
    # The formatter's rendering convention is NOT the legend builder's to
    # change: it is what it was on entry. (Without this, an implementation
    # could rewrite the convention and make the reading guarantee below
    # vacuous instead of delivering it.)
    Ensures(fmt.convention == Old(fmt.convention))
    # Nor is the range of the axis it renders against: that is settled before
    # the legend is built. (Without this, an implementation could widen or
    # narrow the range and then render honestly against the range it chose.)
    Ensures(fmt.view_lo == Old(fmt.view_lo))
    Ensures(fmt.view_hi == Old(fmt.view_hi))
    # The formatter this legend renders with is LEFT with residual rendering
    # disabled: the object outlives the call, and a legend built by sidestepping
    # it would leave it still factoring a magnitude out of this same axis's
    # ticks.
    Ensures(not fmt.residual)
    # The legend's labels are EXACTLY the ones that formatter renders for this
    # tick set, in this order, in the mode the call leaves it in, against the
    # range of the axis it is attached to: not text written by a private route,
    # not the labels it would render for some other tick set (nor for one tick
    # at a time), not the labels it would render against some other range (the
    # span of the tick set included), and none reordered or dropped.
    Ensures(ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs),
                                               fmt.residual,
                                               fmt.view_lo, fmt.view_hi))
    # Every emitted label reads back to the FULL value of the tick it
    # describes: no residual is lost. (Available exactly for the full-value
    # convention; a formatter that re-expresses ticks in a unit or at a
    # precision of its own cannot render such labels and none are claimed of
    # it.)
    Ensures(Implies(fmt.convention == 0,
                    legend_reads_ticks(ToSeq(Result()), ToSeq(locs))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result())
        and fmt.convention == 0,
        reading(ToSeq(Result())[k]) == ToSeq(locs)[k]),
        [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
        # The build walks the tick locations once: `i` grows by exactly one per
        # pass and `len(locs)` cannot change (the input is read-only at 1/2
        # permission), so `len(locs) - i + 1` strictly decreases; the guard
        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
    return result
    # impl-end


def legend_values_locator(fmt: TickFormatter,
                          locs: List[int]) -> List[int]:
    # pre-conditions-start
    # As at the first site, the formatter arrives already built in whatever
    # rendering mode, with whatever convention, attached to an axis of whatever
    # range; none of the three is assumed.
    Requires(Acc(fmt.convention) and Acc(fmt.residual))
    Requires(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Requires(Acc(list_pred(locs), 1 / 2))
    # As at the first site, the legend must actually be BUILT. Level 4 sits
    # strictly above the sibling builder's 3, so a caller here may also invoke
    # legend_values_continuous without leaking its own obligation.
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fmt.convention) and Acc(fmt.residual))
    Ensures(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Ensures(Acc(list_pred(locs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(locs))
    # The rendering convention is left alone, as at the first site.
    Ensures(fmt.convention == Old(fmt.convention))
    # So is the range of the axis rendered against, as at the first site.
    Ensures(fmt.view_lo == Old(fmt.view_lo))
    Ensures(fmt.view_hi == Old(fmt.view_hi))
    # The formatter is left with residual rendering disabled, as at the first
    # site.
    Ensures(not fmt.residual)
    # The legend's labels are exactly the ones that formatter renders for this
    # tick set, in this order, against this axis range, as at the first site.
    Ensures(ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs),
                                               fmt.residual,
                                               fmt.view_lo, fmt.view_hi))
    # Every emitted label reads back to the full value of its tick, as at the
    # first site.
    Ensures(Implies(fmt.convention == 0,
                    legend_reads_ticks(ToSeq(Result()), ToSeq(locs))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result())
        and fmt.convention == 0,
        reading(ToSeq(Result())[k]) == ToSeq(locs)[k]),
        [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
        # The build walks the tick locations once: `i` grows by exactly one per
        # pass and `len(locs)` cannot change (the input is read-only at 1/2
        # permission), so `len(locs) - i + 1` strictly decreases; the guard
        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**AUDIT SCOPE:** per instructions the R/I legs were left to G-CONF; I concentrated on the A legs (rendered_labels / reading) and the model<->patch correspondence. Attack verifications were run as concurrent background jobs, at most 3 at a time (each Nagini check spawns a JVM+Z3).

ATTACKS — /tmp path, exact command, observed result. Command form for every N in {1..20, pp1, pp2}:
  cd swe-proof && python -m swebench_unified.adversary weakness nagini mwaskom__seaborn-3187 atk_N.py
each preceded by `... adversary same-spec nagini mwaskom__seaborn-3187 <path>` -> exit 0 SAME (all 22 + atk_0 + atk_vac), and each followed by `bash scripts/nagini_verify.sh <path>` to record the rejecting clause.

- atk_1 — PREPATCH BUG, both sites (differential witness): drops `fmt.residual = False`, renders in the mode the formatter arrived in. weakness exit=2. Rejected by `Postcondition... Assertion (not fmt.residual) might not hold` at atk_1.py:265 AND:346. => prepatch_reproduced=true.
- atk_pp1 / atk_pp2 — the BUNDLE'S OWN differential twins (model_prepatch.py / model_prepatch_2.py copied verbatim). Both same-spec exit 0, both weakness exit=2. Independent confirmation of G-DIFF at each site.
- atk_2 — CONTROL-FLOW-EFFECT (the shape that broke the OLD, superseded spec): renders the whole sequence FIRST in the arrived mode (snapshot `res0`), sets `fmt.residual = False` AFTER the loop. Half (2) still holds at return; the labels are stale. exit=2, rejected by the sequence-equality postcondition at:272 and:350 — it is evaluated at the POST-state mode, so rendered_labels(c,locs,res0,..) != rendered_labels(c,locs,False,..).
- atk_3 — PARTIAL-DOMAIN / per-tick rendering: `rendered_labels(conv, PSeq(locs[i]), residual, lo, hi)[0]` — each tick rendered in ISOLATION. exit=2, sequence-equality at:272/:347. This is the load-bearing leg (mapping.md §3.1: tick 1e8 renders '0' in {1e8,1e8+1} but '1' in {0,1e8,1e8+1}); the whole-set signature is what rejects it.
- atk_4 — WRONG RANGE, tick-span substitution (refinement.md C.5 `interval-from-ticks`): renders against `(locs[0], locs[-1])` instead of the axis range the formatter reads. exit=2, sequence-equality at:272/:354.
- atk_17 — WRONG RANGE, bounds SWAPPED (`view_hi, view_lo`) — right ticks, right mode, right convention, wrong application of the callee. exit=2, sequence-equality at:272/:353.
- atk_10 — RANGE REWRITE-AND-RESTORE (Old()-pinning escape-hatch probe): sets the range to (0,0), renders honestly against the range it chose, restores lo0/hi0 before returning so the two `Old()` clauses hold at exit. exit=2 — the sequence clause is evaluated against the RESTORED range, so the escape hatch is closed (:272/:353). This is the sharpest test of refinement.md C.5's 'readable but not writable-in-effect' claim.
- atk_5 — PARTIAL DOMAIN (empty-tick boundary): `if len(locs) > 0: fmt.residual = False`. exit=2, but rejected at a loop-invariant-on-entry, which is arguably my proof shape, so I RE-ENCODED it as atk_16 (same partial-domain effect, invariant merely TRACKS the mode via `res1`): exit=2, rejected by `Postcondition... (not fmt.residual)` at:265/:353. So the empty-tick-set boundary is enforced by the SPEC, not by my invariant — `Ensures(not fmt.residual)` is unguarded.
- atk_6 — UNGROUNDED-ORACLE ECHO (re-encodes the prior pass's counterexample, which broke the superseded parsed-number spec): `lab = locs[i]`, label text written by a private route. exit=2, sequence-equality at:272/:346. The opaque-code carrier + uninterpreted `reading` make a label unobtainable except from rendered_labels — exactly the hole the rewrite closed.
- atk_12 — HALF (2) WITHOUT HALF (1): mode left correctly disabled at return, but the labels are the residual-rendered ones (`rendered_labels(conv, locs, True, lo, hi)`). exit=2 at:272/:349 — confirms the two halves are inseparable in the direction the docstring claims.
- atk_7 — ONE TICK MISLABELLED: length preserved, every label genuinely rendered by this formatter for this set, but the last entry repeats index 0. exit=2 — sequence equality is pointwise, not multiset/length.
- atk_13 — WRONG TICK SET (self-concatenation): `ToSeq(locs) + ToSeq(locs)` — one label per tick, all really rendered in the right mode against the right range, but for a set that is not the one being labelled. exit=2 at:272/:354.
- atk_15 — PARTIAL-DOMAIN AT ONE INDEX: index 0 rendered in isolation, every other index the formatter's own whole-set label. exit=2 — a single-point deviation is caught.
- atk_8 — CONVENTION REWRITE (falsify the guard instead of delivering it): `fmt.convention = 1`, then render consistently under it. exit=2, rejected by `(fmt.convention == Old(fmt.convention))` at:255/:341 — the clause mapping.md §4 says exists for exactly this rival.
- atk_14 — CONVENTION REWRITE-AND-RESTORE (the Old()-pinning escape hatch for the convention): rewrite to conv0+1, render honestly under it, restore before return. exit=2 at:272/:355 — the sequence clause is evaluated against the RESTORED convention, so restoring does not buy the rival anything.
- atk_20 — CONVENTION COLLAPSE: renders as if the formatter were always the full-value one (hardcoded `rendered_labels(0,...)`). This is the refinement error that would still pass BOTH F2P tests while silently rewriting every non-default legend (a patch that installs a fresh ScalarFormatter instead of configuring the one on the axis). exit=2 at:272/:353 — the spec's openness over the convention is load-bearing, not decorative.
- atk_9 / atk_19 — DIVERGENCE (vacuity by non-termination): `i = i + 0`, the rendering loop never finishes. atk_9 (measure dropped) exit=2 'Loop might not take all unsatisfied obligations from the context'; atk_19 (gold measure KEPT, so the rejection must land on the measure) exit=2 'Loop might not keep promise to terminate' at:294/:372. Both sites.
- atk_18 — CONTROL for the divergence pair: the GOLD (terminating) impl with only the loop's MustTerminate invariant deleted. exit=2 with the same obligation-leak message as atk_9, which is why atk_19 was added: atk_19's distinct 'might not keep promise to terminate' shows the DIVERGENCE, not a missing invariant, is what the method-level MustTerminate(3)/(4) rejects. (Consistent with the known trap that loop invariants alone do not reject a diverging rival.)

### A-LEG AUDIT (the assigned focus).
- Leg tagging census over refinement.md §A/§B: 13 legs, 4 R, 2 I, 2 A-reference, 2 R+A-reference, 1 A-consumed(length)+A-reference, 2 A-consumed+A-reference. All 13 are R / A-consumed / A-reference / I. NO kind-3: the only occurrence of the phrase 'kind-3' in either doc is §C's heading asserting their absence. The genuinely changed op (A3/B3) is a concrete state change on the modeled object, not hidden behind an axiom — confirmed against patch.diff.
- Source correspondence verified against the FROZEN base_commit 22cdfb0c93f8ec78492d87edb810f10cb7f57a31 (`git show <commit>:seaborn/_core/scales.py|utils.py`): site 1 shows `axis.set_view_interval(vmin, vmax)` / `locs = axis.major.locator()` / the `(vmin <= locs) & (locs <= vmax)` clip / `labels = axis.major.formatter.format_ticks(locs)` / `new._legend = list(locs), list(labels)` exactly where A1-A7 cite them, with the two hasattr-guarded setters inserted immediately above the labels line. Site 2 shows the `dummy_axis` whose ONLY method is `get_view_interval` returning `limits`, the LogLocator/ScalarFormatter branch, `formatter.set_locs(raw_levels)` and `[formatter(x) for x in raw_levels]`, exactly as B1-B6 cite. CORRESPONDENCE HOLDS at both sites. (One nit, non-substantive: B2 cites the clip as an `&`-mask at utils.py:692 whereas base_commit has a list comprehension `[l for l in raw_levels if...]`; same clip, and it is an R/I leg anyway.)
- A3/B3 hasattr-guard claim MEASURED on live mpl 3.10.9: ScalarFormatter and EngFormatter have both set_useOffset/set_scientific; StrMethodFormatter(x2), FuncFormatter, LogFormatter, LogFormatterSciNotation have NEITHER. For every no-control kind, disabled-vs-untouched is BYTE-IDENTICAL through BOTH APIs (so the guards skipping leaves the object already in the modeled residual==False state); ScalarFormatter is the one that MOVES (['100000001'..'100000004'] disabled vs ['1','2','3','4'] untouched). EngFormatter's byte-identity claim also measured true (['100 Mg']x4 either way). So the one model boolean (§C.2) is a genuine refinement, not an under-count — and I confirmed BOTH concrete controls are needed: on the offset shape disabling only set_scientific leaves ['1','2','3','4'] and only set_useOffset leaves ['1.00000001',...] (neither >1e7), while on the 1e8/2e8/3e8/4e8 shape only set_scientific suffices. The patch sets both; the model's single boolean abstracts 'no such control is enabled', which is the correct join.
- A4/B4 deep-model signature: probed what a formatter actually reads from its axis on the rendering path with an attribute-recording stub. ScalarFormatter reads nothing; Eng/Log/LogSci read get_view_interval (the Log kinds also probe get_transform, absent on both real sites' axes too). So (convention, tick set, mode, range) is the complete input list and mapping.md §3.1's claim holds. Range-dependence is real and the range args are not idle: axiom_check measures ['eng','log','logsci','scalar'] moving when only the range moves, and I independently reproduced a scalar case ([1e8,1e8+1] renders ['0','1'] against (1e8,1e8+1) but ['0.000000000','0.000000000'] against (0,1e9)).
- A6 guard non-withholding MEASURED: with every residual control disabled, eng->['100 Mg'...], strmethod_3g/func_3g/log->['1e+08'...], logsci->['$\mathdefault{10^{8}}$'...] — none read back to their ticks, so there is no reading guarantee to withhold on the non-default conventions. ScalarFormatter disabled gives readings [100000001.0..100000004.0], all >1e7, i.e. exactly the F2P assertion. And through the SITE-2 API, ScalarFormatter+set_locs on [0.20..0.28] returns exactly ['0.20','0.22','0.24','0.26','0.28'] — the P2P texts at tests/test_relational.py:866,877, a fact only the TEXT carrier (§C.1) can express and the reason the atk_6 echo class must be, and is, rejected.
- `reading` is genuinely uninterpreted: @Pure @ContractOnly, zero Ensures (read from model.py). The only reachable fact about a label is the guarded second Ensures of rendered_labels.
- A-domain (§C.4) disclosed rather than hidden: rendered_labels declares NO Requires (universal declared domain) and its docstring states the width-reading restriction. `python axiom_check.py` -> exit 0, reporting measured callee-domain ['eng'] against declared bound ['eng'], two-sided; I reproduced it directly (only EngFormatter raises ValueError: math domain error on a zero-width range; all six others render).

**CONCLUSION:** the spec's two halves are inseparable and both enforced — half (1) by whole-sequence equality against an opaque-text-coded, whole-set-and-range-valued deep model (rejects atk_3/4/6/7/12/13/15/17/20), half (2) by the unguarded `not fmt.residual` evaluated in the post-state (rejects atk_1/2/5/16/pp1/pp2), with `fmt.convention == Old(...)` blocking guard-falsification (atk_8) and the sequence clause's post-state evaluation defeating rewrite-and-restore on both the convention (atk_14) and the range (atk_10), and method-level MustTerminate blocking vacuity-by-divergence (atk_9/19). No verifying wrong impl was found, so there was nothing to materialize into a faithful patch and no run_resolve was needed or run; verdict SOUND on 22 attacks + positive control + vacuity control + divergence control + an independently re-run G-AX.

**CAVEAT FOR THE RUNNER:** the recorded verdict.md is STALE with respect to this model.py — it carries an older BROKEN G-EQ that judged a superseded spec whose label carrier was the float()-PARSED number via `parsed_label(loc, mode_a, mode_b)`; with both modes pinned False the residual collapsed to 0 and the rendering postcondition degenerated to `Result()[k] == locs[k]`, which `v = loc` discharged trivially. That hole is closed in the current model.py and I re-encoded that exact counterexample as atk_6 (plus its late-mode sibling as atk_2); both are now REJECTED. verdict.md should be regenerated, not reused.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 22 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_pp1.py`, `atk_pp2.py` |

**Non-vacuity.** The positive control `atk_0.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no attack reached CANDIDATE, so no faithful refined patch was materializable and no run_resolve was triggered. 22 distinct same-spec wrong impls (every one `same-spec` exit 0, spec byte-identical; only the two impl regions differ) were each run through `python -m swebench_unified.adversary weakness nagini mwaskom__seaborn-3187 <path>`; ALL 22 returned exit 2 = NOT-A-COUNTEREXAMPLE (does not verify). Positive control atk_0.py (== model.py byte-for-byte, `diff` empty) VERIFIES in 18.65s. Vacuity control atk_vac.py (gold impl + `Assert(False)` before the return) FAILS at BOTH sites (atk_vac.py:319 and :398, 'Assert might fail. Assertion False might not hold.'), so the postconditions are reached on a feasible path and the 22 rejections are real rather than artefacts of an infeasible path. Every rejection was re-run through `bash scripts/nagini_verify.sh` to record WHICH clause rejected it, and each lands on a real spec clause at BOTH sites (see notes).
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 22 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 21 — `atk_pp1.py` → rejected (same spec, does not verify — good)

Attack 22 — `atk_pp2.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0.py`

```python
"""Twin-artifact model for mwaskom__seaborn-3187.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a numeric legend is built for a quantitative variable, each legend entry
  pairs a tick location with a LABEL: the text a numeric tick formatter renders
  for that location.  The legend keeps the per-tick label texts and nothing
  else, so the number a reader can recover from an entry is whatever its text
  reads back as.  A formatter that is allowed to factor a magnitude common to
  the ticks out of them renders each tick as a small RESIDUAL and parks the
  factored magnitude in a separate string the legend never records -- so with
  residual rendering left enabled, the legend's labels read back to residuals
  instead of to the values they are supposed to describe.

  The formatter is a piece of SHARED, MUTABLE state: it arrives already built
  (with residual rendering possibly enabled, which is its ordinary default), it
  is the thing that actually renders the label text, and it outlives the
  legend-building step.  So the required behaviour has two inseparable halves,
  and an implementation must deliver BOTH:

    (1) the legend's labels must be THE LABELS THAT FORMATTER RENDERS for the
        tick set it is given -- the legend reports the formatter's own text, it
        does not write label text by some private route of its own, it does not
        render a tick in isolation (a formatter chooses ONE common way of
        writing the whole tick set, so a tick's label is not a function of that
        tick alone), and it does not reorder or drop any of them; and

    (2) the formatter must be left with residual rendering disabled, so that
        (1) yields labels that read back to the ticks' FULL absolute values,
        for tick locations of every magnitude -- including large ones whose true
        value greatly exceeds any residual.

  Half (1) alone is satisfied by a formatter that still factors a magnitude
  out; half (2) alone is satisfied by sidestepping the formatter and writing
  the numbers into the legend directly, which both puts text in the legend that
  the formatter never produced and leaves the formatter -- the object the
  surrounding code goes on using to render this same axis -- still in its
  magnitude-factoring mode.  Only both together describe a legend that is
  correct *and* consistent with the ticks it labels.

  A formatter also has a RENDERING CONVENTION, settled when it was built and
  none of the legend builder's business: does it write each tick's own value
  into the label text in full -- what a numeric legend's formatter does when
  nothing else has been asked of it -- or does it re-express the ticks in a
  unit or at a precision of its own choosing (an SI-prefixed unit, a rounded
  number of digits, ...)?  Only the first can render labels that read back to
  full tick values at all, so that is the convention half (2)'s reading
  guarantee is stated for; the builder may not change a formatter's convention,
  and for the other conventions no reading guarantee is claimed (nor
  available): their labels do not read back to their ticks even with residual
  rendering disabled (axiom_check.py).

  A formatter renders against one further input: the numeric RANGE of the axis
  it is attached to, i.e. the interval the legend's variable covers, which is
  announced to that axis before any label is rendered.  That range is
  INDEPENDENT of the tick locations -- a legend's ticks are chosen inside its
  range, and the range is normally wider than the ticks it contains -- and
  several conventions decide from it how to write a tick (which decade to name,
  which unit to prefix, how many digits to carry).  So a label sequence is a
  function of the tick set AND that range together, and an implementation must
  render against THE RANGE THE FORMATTER ITSELF READS: rendering against the
  span of the tick set, or against any other interval, is a different label
  sequence.  Like the convention, the range is settled before the legend is
  built and is not the builder's to change.

There are two independent places that build such numeric legends; each must
honour the same guarantee.  Both are modelled below as the sequence of labels
emitted, the readings of those labels, and the rendering mode the formatter is
left in.

Tick locations and the axis range are modelled as `int` (the exercised
locations are integral and the property -- labels reading back to full tick
values vs. to residuals -- is exact at those values; refinement.md justifies the
int carrier).  A LABEL is modelled as an opaque `int` code standing for its
exact text, so two labels are equal in the model exactly when their texts are
identical: the model is deliberately NOT allowed to see a label as the number it
reads back to, because two different texts can read back to the same number and
it is the text the legend keeps.  The formatter is modelled as an OBJECT
carrying its rendering convention, the axis range it renders against, and the
mutable flag controlling residual rendering, since the guarantee is about the
state it is left in and not only about what is returned; the deep models
`rendered_labels` / `reading` spell out
(convention, tick set, mode, range) -> label sequence and label -> number, and
are validated against the real `matplotlib` formatter by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def reading(label: int) -> int:
    """The number a reader recovers by reading a rendered label back as a
    number.  Labels are opaque codes for their exact text, and this is the only
    thing the model may learn about a label's text: the legend records the text
    alone, so a label's reading is all the numeric information the legend
    conveys about its tick.

    Deliberately UNINTERPRETED (no Ensures): nothing about the number a label
    reads back to is available except through the one axiom on
    `rendered_labels` below.  Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX).
    """


@Pure
@ContractOnly
def rendered_labels(convention: int, ticks: PSeq[int], residual: bool,
                    view_lo: int, view_hi: int) -> PSeq[int]:
    """The labels a numeric tick formatter renders for the tick locations
    `ticks`, in order, given the formatter's rendering convention, whether
    residual rendering is enabled, and the numeric range `view_lo .. view_hi`
    of the axis it is attached to.

    The WHOLE tick set is an argument, and the whole label sequence the result,
    because a formatter picks ONE way of writing all of the ticks it is given
    and renders each of them that way: a tick's label is not a function of that
    tick alone, and the labels for a tick set are not recoverable by rendering
    its members one at a time.

    The axis range is an argument BECAUSE IT IS AN INPUT THE FORMATTER READS
    and it is not determined by the tick set: the ticks of a legend are chosen
    inside its variable's range, and that range is normally wider than them.
    Several conventions consult it -- which decade to name, which unit to
    prefix, how many digits to carry -- so two calls that differ only in the
    range can render different label sequences (measured for three of the
    conventions in axiom_check.py `check_range_dependence`), and a label
    sequence rendered against the tick set's own span is in general NOT the one
    the formatter renders.

    `convention == 0` is the FULL-VALUE convention: the one a numeric legend's
    formatter has when nothing else has been asked of it -- it writes each
    tick's own value into the label text, in full.  Any other convention
    re-expresses ticks in a unit or at a precision of the formatter's own
    choosing, and there no reading guarantee holds or is claimed.

    The properties the proofs rely on (the weakest sufficient contract):
    a formatter renders exactly one label per tick, and a full-value formatter
    with residual rendering DISABLED factors nothing out, so each of its labels
    reads back to the full value of the tick it describes -- whatever the axis
    range is (measured: axiom_check.py drives the range independently of the
    tick set).  While residual rendering is enabled the readings are
    unconstrained -- which is exactly the information the legend loses.
    Nothing else about a label is knowable: two formatter states, two tick sets
    or two axis ranges need not render alike.

    The one-label-per-tick contract below describes the label sequence for the
    inputs a convention renders.  A convention need not have a rendering for
    every input at all: a formatter that re-expresses ticks in a unit chosen
    from the WIDTH of the axis range may have nothing to say about a range of
    no width, and may then raise rather than return labels.  Where that happens
    there is no label sequence to describe and no legend is produced at all, so
    there is no legend for this model to be silent about.  Only a
    width-reading convention can be so restricted; axiom_check.py measures the
    restriction exactly (it may be empty), and conformance_check.py compares
    whole outcomes, so the refinement and the real site are held to producing
    no legend together on precisely those inputs.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Ensures(len(Result()) == len(ticks))
    Ensures(Implies(convention == 0 and not residual,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(ticks),
                        reading(Result()[k]) == ticks[k]),
                        [[Result()[k]]]))))
# axioms-end


# pure-start
class TickFormatter:
    """The numeric tick formatter the legend renders its label text with: a
    piece of shared mutable state that arrives ALREADY BUILT and outlives the
    legend-building step.

    `convention` is the rendering convention it was built with (see
    `rendered_labels`): `0` is the full-value convention, any other value is a
    formatter that re-expresses ticks in a unit or at a precision of its own.
    It is not a mode and no legend builder may change it -- the guarantees
    below pin it unchanged across the call.

    `view_lo` / `view_hi` are the numeric range of the axis this formatter is
    attached to: an input it reads when deciding how to write a tick, settled
    (like the convention) before the legend is built, and likewise not the
    builder's to change.  It is carried on the formatter rather than passed in
    because it is state the formatter reaches on its own, and because a builder
    that rendered against some other interval would still be handing this
    object on to render this same axis.

    `residual` is the residual-rendering mode: while it is enabled the
    formatter may factor a magnitude common to the ticks out of them and render
    each tick as a small residual.  It is mutable precisely because "which mode
    is this formatter left in" is part of what a legend builder is answerable
    for: the object is still there, and still rendering this axis, after the
    legend is built.  Which rendering controls of a real formatter it stands
    for is a refinement-mapping detail (refinement.md)."""

    def __init__(self, convention: int, residual: bool,
                 view_lo: int, view_hi: int) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.convention) and self.convention == convention)  # type: ignore
        Ensures(Acc(self.residual) and self.residual == residual)  # type: ignore
        Ensures(Acc(self.view_lo) and self.view_lo == view_lo)  # type: ignore
        Ensures(Acc(self.view_hi) and self.view_hi == view_hi)  # type: ignore
        self.convention = convention
        self.residual = residual
        self.view_lo = view_lo
        self.view_hi = view_hi


@Pure
def legend_reads_ticks(labels: PSeq[int], ticks: PSeq[int]) -> bool:
    """Whole-legend reading guarantee: the legend carries one label per tick
    and EVERY one of them reads back to the full value of the tick location it
    describes.  Stated over the whole label sequence rather than per entry,
    because the failure being ruled out is the one where a magnitude common to
    the ticks is factored out of all of them at once."""
    return len(labels) == len(ticks) and Forall(int, lambda k: (
        Implies(0 <= k and k < len(ticks), reading(labels[k]) == ticks[k]),
        [[labels[k]]]))
# pure-end


def legend_values_continuous(fmt: TickFormatter,
                             locs: List[int]) -> List[int]:
    # pre-conditions-start
    # The formatter arrives already built, in WHATEVER rendering mode it
    # happens to be in -- residual rendering enabled is its ordinary default,
    # so both modes are admitted here and neither is assumed -- with WHATEVER
    # rendering convention it was built with, so no convention is excluded
    # either, and attached to an axis of WHATEVER range: no relation between
    # that range and the tick locations is assumed.
    Requires(Acc(fmt.convention) and Acc(fmt.residual))
    Requires(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Requires(Acc(list_pred(locs), 1 / 2))
    # The legend must actually be BUILT: without this, every guarantee below is
    # claimed only of runs that reach the return, so a rendering loop that
    # never finishes would satisfy them vacuously. Level 3 leaves room below
    # for the list operations that grow the label sequence.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fmt.convention) and Acc(fmt.residual))
    Ensures(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Ensures(Acc(list_pred(locs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One label per tick location.
    Ensures(len(Result()) == len(locs))
    # The formatter's rendering convention is NOT the legend builder's to
    # change: it is what it was on entry. (Without this, an implementation
    # could rewrite the convention and make the reading guarantee below
    # vacuous instead of delivering it.)
    Ensures(fmt.convention == Old(fmt.convention))
    # Nor is the range of the axis it renders against: that is settled before
    # the legend is built. (Without this, an implementation could widen or
    # narrow the range and then render honestly against the range it chose.)
    Ensures(fmt.view_lo == Old(fmt.view_lo))
    Ensures(fmt.view_hi == Old(fmt.view_hi))
    # The formatter this legend renders with is LEFT with residual rendering
    # disabled: the object outlives the call, and a legend built by sidestepping
    # it would leave it still factoring a magnitude out of this same axis's
    # ticks.
    Ensures(not fmt.residual)
    # The legend's labels are EXACTLY the ones that formatter renders for this
    # tick set, in this order, in the mode the call leaves it in, against the
    # range of the axis it is attached to: not text written by a private route,
    # not the labels it would render for some other tick set (nor for one tick
    # at a time), not the labels it would render against some other range (the
    # span of the tick set included), and none reordered or dropped.
    Ensures(ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs),
                                               fmt.residual,
                                               fmt.view_lo, fmt.view_hi))
    # Every emitted label reads back to the FULL value of the tick it
    # describes: no residual is lost. (Available exactly for the full-value
    # convention; a formatter that re-expresses ticks in a unit or at a
    # precision of its own cannot render such labels and none are claimed of
    # it.)
    Ensures(Implies(fmt.convention == 0,
                    legend_reads_ticks(ToSeq(Result()), ToSeq(locs))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result())
        and fmt.convention == 0,
        reading(ToSeq(Result())[k]) == ToSeq(locs)[k]),
        [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
        # The build walks the tick locations once: `i` grows by exactly one per
        # pass and `len(locs)` cannot change (the input is read-only at 1/2
        # permission), so `len(locs) - i + 1` strictly decreases; the guard
        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
    return result
    # impl-end


def legend_values_locator(fmt: TickFormatter,
                          locs: List[int]) -> List[int]:
    # pre-conditions-start
    # As at the first site, the formatter arrives already built in whatever
    # rendering mode, with whatever convention, attached to an axis of whatever
    # range; none of the three is assumed.
    Requires(Acc(fmt.convention) and Acc(fmt.residual))
    Requires(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Requires(Acc(list_pred(locs), 1 / 2))
    # As at the first site, the legend must actually be BUILT. Level 4 sits
    # strictly above the sibling builder's 3, so a caller here may also invoke
    # legend_values_continuous without leaking its own obligation.
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fmt.convention) and Acc(fmt.residual))
    Ensures(Acc(fmt.view_lo) and Acc(fmt.view_hi))
    Ensures(Acc(list_pred(locs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(locs))
    # The rendering convention is left alone, as at the first site.
    Ensures(fmt.convention == Old(fmt.convention))
    # So is the range of the axis rendered against, as at the first site.
    Ensures(fmt.view_lo == Old(fmt.view_lo))
    Ensures(fmt.view_hi == Old(fmt.view_hi))
    # The formatter is left with residual rendering disabled, as at the first
    # site.
    Ensures(not fmt.residual)
    # The legend's labels are exactly the ones that formatter renders for this
    # tick set, in this order, against this axis range, as at the first site.
    Ensures(ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs),
                                               fmt.residual,
                                               fmt.view_lo, fmt.view_hi))
    # Every emitted label reads back to the full value of its tick, as at the
    # first site.
    Ensures(Implies(fmt.convention == 0,
                    legend_reads_ticks(ToSeq(Result()), ToSeq(locs))))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result())
        and fmt.convention == 0,
        reading(ToSeq(Result())[k]) == ToSeq(locs)[k]),
        [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi).take(i))
        # The build walks the tick locations once: `i` grows by exactly one per
        # pass and `len(locs)` cannot change (the input is read-only at 1/2
        # permission), so `len(locs) - i + 1` strictly decreases; the guard
        # `i < len(locs)` keeps it >= 2 whenever the body runs, hence positive.
        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**AUDIT SCOPE:** per instructions the R/I legs were left to G-CONF; I concentrated on the A legs (rendered_labels / reading) and the model<->patch correspondence. Attack verifications were run as concurrent background jobs, at most 3 at a time (each Nagini check spawns a JVM+Z3).

ATTACKS — /tmp path, exact command, observed result. Command form for every N in {1..20, pp1, pp2}:
  cd swe-proof && python -m swebench_unified.adversary weakness nagini mwaskom__seaborn-3187 atk_N.py
each preceded by `... adversary same-spec nagini mwaskom__seaborn-3187 <path>` -> exit 0 SAME (all 22 + atk_0 + atk_vac), and each followed by `bash scripts/nagini_verify.sh <path>` to record the rejecting clause.

- atk_1 — PREPATCH BUG, both sites (differential witness): drops `fmt.residual = False`, renders in the mode the formatter arrived in. weakness exit=2. Rejected by `Postcondition... Assertion (not fmt.residual) might not hold` at atk_1.py:265 AND:346. => prepatch_reproduced=true.
- atk_pp1 / atk_pp2 — the BUNDLE'S OWN differential twins (model_prepatch.py / model_prepatch_2.py copied verbatim). Both same-spec exit 0, both weakness exit=2. Independent confirmation of G-DIFF at each site.
- atk_2 — CONTROL-FLOW-EFFECT (the shape that broke the OLD, superseded spec): renders the whole sequence FIRST in the arrived mode (snapshot `res0`), sets `fmt.residual = False` AFTER the loop. Half (2) still holds at return; the labels are stale. exit=2, rejected by the sequence-equality postcondition at:272 and:350 — it is evaluated at the POST-state mode, so rendered_labels(c,locs,res0,..) != rendered_labels(c,locs,False,..).
- atk_3 — PARTIAL-DOMAIN / per-tick rendering: `rendered_labels(conv, PSeq(locs[i]), residual, lo, hi)[0]` — each tick rendered in ISOLATION. exit=2, sequence-equality at:272/:347. This is the load-bearing leg (mapping.md §3.1: tick 1e8 renders '0' in {1e8,1e8+1} but '1' in {0,1e8,1e8+1}); the whole-set signature is what rejects it.
- atk_4 — WRONG RANGE, tick-span substitution (refinement.md C.5 `interval-from-ticks`): renders against `(locs[0], locs[-1])` instead of the axis range the formatter reads. exit=2, sequence-equality at:272/:354.
- atk_17 — WRONG RANGE, bounds SWAPPED (`view_hi, view_lo`) — right ticks, right mode, right convention, wrong application of the callee. exit=2, sequence-equality at:272/:353.
- atk_10 — RANGE REWRITE-AND-RESTORE (Old()-pinning escape-hatch probe): sets the range to (0,0), renders honestly against the range it chose, restores lo0/hi0 before returning so the two `Old()` clauses hold at exit. exit=2 — the sequence clause is evaluated against the RESTORED range, so the escape hatch is closed (:272/:353). This is the sharpest test of refinement.md C.5's 'readable but not writable-in-effect' claim.
- atk_5 — PARTIAL DOMAIN (empty-tick boundary): `if len(locs) > 0: fmt.residual = False`. exit=2, but rejected at a loop-invariant-on-entry, which is arguably my proof shape, so I RE-ENCODED it as atk_16 (same partial-domain effect, invariant merely TRACKS the mode via `res1`): exit=2, rejected by `Postcondition... (not fmt.residual)` at:265/:353. So the empty-tick-set boundary is enforced by the SPEC, not by my invariant — `Ensures(not fmt.residual)` is unguarded.
- atk_6 — UNGROUNDED-ORACLE ECHO (re-encodes the prior pass's counterexample, which broke the superseded parsed-number spec): `lab = locs[i]`, label text written by a private route. exit=2, sequence-equality at:272/:346. The opaque-code carrier + uninterpreted `reading` make a label unobtainable except from rendered_labels — exactly the hole the rewrite closed.
- atk_12 — HALF (2) WITHOUT HALF (1): mode left correctly disabled at return, but the labels are the residual-rendered ones (`rendered_labels(conv, locs, True, lo, hi)`). exit=2 at:272/:349 — confirms the two halves are inseparable in the direction the docstring claims.
- atk_7 — ONE TICK MISLABELLED: length preserved, every label genuinely rendered by this formatter for this set, but the last entry repeats index 0. exit=2 — sequence equality is pointwise, not multiset/length.
- atk_13 — WRONG TICK SET (self-concatenation): `ToSeq(locs) + ToSeq(locs)` — one label per tick, all really rendered in the right mode against the right range, but for a set that is not the one being labelled. exit=2 at:272/:354.
- atk_15 — PARTIAL-DOMAIN AT ONE INDEX: index 0 rendered in isolation, every other index the formatter's own whole-set label. exit=2 — a single-point deviation is caught.
- atk_8 — CONVENTION REWRITE (falsify the guard instead of delivering it): `fmt.convention = 1`, then render consistently under it. exit=2, rejected by `(fmt.convention == Old(fmt.convention))` at:255/:341 — the clause mapping.md §4 says exists for exactly this rival.
- atk_14 — CONVENTION REWRITE-AND-RESTORE (the Old()-pinning escape hatch for the convention): rewrite to conv0+1, render honestly under it, restore before return. exit=2 at:272/:355 — the sequence clause is evaluated against the RESTORED convention, so restoring does not buy the rival anything.
- atk_20 — CONVENTION COLLAPSE: renders as if the formatter were always the full-value one (hardcoded `rendered_labels(0,...)`). This is the refinement error that would still pass BOTH F2P tests while silently rewriting every non-default legend (a patch that installs a fresh ScalarFormatter instead of configuring the one on the axis). exit=2 at:272/:353 — the spec's openness over the convention is load-bearing, not decorative.
- atk_9 / atk_19 — DIVERGENCE (vacuity by non-termination): `i = i + 0`, the rendering loop never finishes. atk_9 (measure dropped) exit=2 'Loop might not take all unsatisfied obligations from the context'; atk_19 (gold measure KEPT, so the rejection must land on the measure) exit=2 'Loop might not keep promise to terminate' at:294/:372. Both sites.
- atk_18 — CONTROL for the divergence pair: the GOLD (terminating) impl with only the loop's MustTerminate invariant deleted. exit=2 with the same obligation-leak message as atk_9, which is why atk_19 was added: atk_19's distinct 'might not keep promise to terminate' shows the DIVERGENCE, not a missing invariant, is what the method-level MustTerminate(3)/(4) rejects. (Consistent with the known trap that loop invariants alone do not reject a diverging rival.)

### A-LEG AUDIT (the assigned focus).
- Leg tagging census over refinement.md §A/§B: 13 legs, 4 R, 2 I, 2 A-reference, 2 R+A-reference, 1 A-consumed(length)+A-reference, 2 A-consumed+A-reference. All 13 are R / A-consumed / A-reference / I. NO kind-3: the only occurrence of the phrase 'kind-3' in either doc is §C's heading asserting their absence. The genuinely changed op (A3/B3) is a concrete state change on the modeled object, not hidden behind an axiom — confirmed against patch.diff.
- Source correspondence verified against the FROZEN base_commit 22cdfb0c93f8ec78492d87edb810f10cb7f57a31 (`git show <commit>:seaborn/_core/scales.py|utils.py`): site 1 shows `axis.set_view_interval(vmin, vmax)` / `locs = axis.major.locator()` / the `(vmin <= locs) & (locs <= vmax)` clip / `labels = axis.major.formatter.format_ticks(locs)` / `new._legend = list(locs), list(labels)` exactly where A1-A7 cite them, with the two hasattr-guarded setters inserted immediately above the labels line. Site 2 shows the `dummy_axis` whose ONLY method is `get_view_interval` returning `limits`, the LogLocator/ScalarFormatter branch, `formatter.set_locs(raw_levels)` and `[formatter(x) for x in raw_levels]`, exactly as B1-B6 cite. CORRESPONDENCE HOLDS at both sites. (One nit, non-substantive: B2 cites the clip as an `&`-mask at utils.py:692 whereas base_commit has a list comprehension `[l for l in raw_levels if...]`; same clip, and it is an R/I leg anyway.)
- A3/B3 hasattr-guard claim MEASURED on live mpl 3.10.9: ScalarFormatter and EngFormatter have both set_useOffset/set_scientific; StrMethodFormatter(x2), FuncFormatter, LogFormatter, LogFormatterSciNotation have NEITHER. For every no-control kind, disabled-vs-untouched is BYTE-IDENTICAL through BOTH APIs (so the guards skipping leaves the object already in the modeled residual==False state); ScalarFormatter is the one that MOVES (['100000001'..'100000004'] disabled vs ['1','2','3','4'] untouched). EngFormatter's byte-identity claim also measured true (['100 Mg']x4 either way). So the one model boolean (§C.2) is a genuine refinement, not an under-count — and I confirmed BOTH concrete controls are needed: on the offset shape disabling only set_scientific leaves ['1','2','3','4'] and only set_useOffset leaves ['1.00000001',...] (neither >1e7), while on the 1e8/2e8/3e8/4e8 shape only set_scientific suffices. The patch sets both; the model's single boolean abstracts 'no such control is enabled', which is the correct join.
- A4/B4 deep-model signature: probed what a formatter actually reads from its axis on the rendering path with an attribute-recording stub. ScalarFormatter reads nothing; Eng/Log/LogSci read get_view_interval (the Log kinds also probe get_transform, absent on both real sites' axes too). So (convention, tick set, mode, range) is the complete input list and mapping.md §3.1's claim holds. Range-dependence is real and the range args are not idle: axiom_check measures ['eng','log','logsci','scalar'] moving when only the range moves, and I independently reproduced a scalar case ([1e8,1e8+1] renders ['0','1'] against (1e8,1e8+1) but ['0.000000000','0.000000000'] against (0,1e9)).
- A6 guard non-withholding MEASURED: with every residual control disabled, eng->['100 Mg'...], strmethod_3g/func_3g/log->['1e+08'...], logsci->['$\mathdefault{10^{8}}$'...] — none read back to their ticks, so there is no reading guarantee to withhold on the non-default conventions. ScalarFormatter disabled gives readings [100000001.0..100000004.0], all >1e7, i.e. exactly the F2P assertion. And through the SITE-2 API, ScalarFormatter+set_locs on [0.20..0.28] returns exactly ['0.20','0.22','0.24','0.26','0.28'] — the P2P texts at tests/test_relational.py:866,877, a fact only the TEXT carrier (§C.1) can express and the reason the atk_6 echo class must be, and is, rejected.
- `reading` is genuinely uninterpreted: @Pure @ContractOnly, zero Ensures (read from model.py). The only reachable fact about a label is the guarded second Ensures of rendered_labels.
- A-domain (§C.4) disclosed rather than hidden: rendered_labels declares NO Requires (universal declared domain) and its docstring states the width-reading restriction. `python axiom_check.py` -> exit 0, reporting measured callee-domain ['eng'] against declared bound ['eng'], two-sided; I reproduced it directly (only EngFormatter raises ValueError: math domain error on a zero-width range; all six others render).

**CONCLUSION:** the spec's two halves are inseparable and both enforced — half (1) by whole-sequence equality against an opaque-text-coded, whole-set-and-range-valued deep model (rejects atk_3/4/6/7/12/13/15/17/20), half (2) by the unguarded `not fmt.residual` evaluated in the post-state (rejects atk_1/2/5/16/pp1/pp2), with `fmt.convention == Old(...)` blocking guard-falsification (atk_8) and the sequence clause's post-state evaluation defeating rewrite-and-restore on both the convention (atk_14) and the range (atk_10), and method-level MustTerminate blocking vacuity-by-divergence (atk_9/19). No verifying wrong impl was found, so there was nothing to materialize into a faithful patch and no run_resolve was needed or run; verdict SOUND on 22 attacks + positive control + vacuity control + divergence control + an independently re-run G-AX.

**CAVEAT FOR THE RUNNER:** the recorded verdict.md is STALE with respect to this model.py — it carries an older BROKEN G-EQ that judged a superseded spec whose label carrier was the float()-PARSED number via `parsed_label(loc, mode_a, mode_b)`; with both modes pinned False the residual collapsed to 0 and the rendering postcondition degenerated to `Result()[k] == locs[k]`, which `v = loc` discharged trivially. That hole is closed in the current model.py and I re-encoded that exact counterexample as atk_6 (plus its late-mode sibling as atk_2); both are now REJECTED. verdict.md should be regenerated, not reused.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS-BREAK attack on mwaskom__seaborn-3187 (nagini). Reference = base worktree with patch.diff APPLIED (verified present at both sites via inspect.getsource before every differential); base commit used only for the untouched callees the axioms model.

### Setup checks
- Bundle model.py verifies under the pinned verifier: `scripts/nagini_verify.sh` -> 'Verification successful' (27.4s, exit 0).
- Spec region integrity: markers.same_spec(model.py, model_prepatch.py, NaginiBackend()) = True and same for model_prepatch_2.py; spec_view = 18675 bytes. Both pre-state twins share the byte-identical spec and FAIL verification on exactly the patched clause -- 'Postcondition... Assertion (not fmt.residual) might not hold' at legend_values_continuous:265 and legend_values_locator:350. So the spec discriminates the bug at both sites and is not vacuous.
- Reproduced the bundle's own gates independently inside the gold-patched container: axiom_check.py exit 0 (measured callee-restriction set [] in this env, declared bound ['eng'] -- a sound over-declaration); conformance_check.py exit 0, 105750 checks / 0 disagreements / discriminates_prepatch true (20000/20000 controls disagree).

### AXIOM ATTACKS (rendered_labels / reading vs REAL matplotlib 3.7.2 formatters)
Both axioms held on every reachable input, including inputs the bundle's driver never presented (ranges NOT containing the ticks, ranges NARROWER than the ticks, INVERTED hi<lo, zero-width):
- 4368 boundary checks over 6 formatter kinds x 22 tick sets x 13 ranges x both APIs: 0 length violations, 0 reading violations (convention 0, residual=False), 0 raises.
- 60000-draw seeded fuzz (|t| <= `2**53`, ranges drawn independently incl. inverted/zero-width): 0 length, 0 reading, 0 cross-API, 0 raises.
- Determinism/no-hidden-input control: 20 repeats x all kinds x all tick sets -> 0 nondeterminism.

**DIFFERENTIAL:** MODEL IMPL vs THE REAL GOLD-PATCHED SITES
Restricted to the legitimate refinement domain (model `locs` binds to the POST-CLIP tick set per mapping A1/B1, so ranges must contain every tick; clipped cases counted+excluded, 0 occurred).
- Boundary sweep: 3540 site-1 + 295 site-2 presentable calls over 32 tick sets, SIX conventions (incl. logsci and FuncFormatter, two the bundle never drove) x both arrival modes. All four postcondition clauses checked on the REAL object: sequence-equality 0, length 0, `not fmt.residual` 0, convention-pinning 0, reading (conv 0) 0, locations-identity 0, raises 0.
- Fuzz: 4000 draws -> 8000 site-1 + 4000 site-2 calls, 3011 with range strictly wider than the ticks. 0 violations on every clause, INCLUDING view_lo/view_hi pinning read back off the real axis the formatter is attached to (f.axis.get_view_interval()) -- 0 range mutations.
- Mixed arrival states (useOffset/scientific independently True/False -- probing the ONE-boolean abstraction of refinement C.2 as a possible under-count): 96 checks, 0 violations.
- Exhaustive enumeration of 16 real mpl.ticker formatters through the patched site 1: 0 state-clause violations, 0 length-axiom violations. Pre-used formatter (set_locs already called, offset already computed to 1e8) -> patched site still yields full-value labels, residual_state False.
- Site-2 LogLocator/LogFormatter branch (patch-untouched, mapping says in-scope as a non-default convention): 6 cases, length axiom and sequence-equality hold, no reading guarantee claimed -- consistent.
- dtype gap: site 2's third parameter `dtype` has no model counterpart and real callers (relational.py:246,278) pass the data's own dtype. Tested float/int/np.int64 on 7 integral cases: label TEXT identical in all, and ScalarFormatter text is invariant to int64-vs-float tick type. No divergence.

### TWO LEADS RAISED AND CLOSED (both reasons the verdict is FAITHFUL, not a rubber stamp)
1. rcParams['axes.formatter.use_mathtext'] -- ScalarFormatter().`__init__` reads it when useMathText is None, and the patch does not touch it. With it True, the DEFAULT-constructed formatter (mapping's convention==0) renders '$\mathdefault{100000001}$' at BOTH real sites, which does NOT read back -> would break Implies(convention==0, legend_reads_ticks). CLOSED: it is not model state and not a legend-builder input; the model's convention==0 is bound to a rendering CONVENTION settled before the builder runs, and the spec explicitly makes the convention immutable-by-the-builder and non-full-value conventions unguaranteed. A mathtext ScalarFormatter is a different convention under that binding, exactly like EngFormatter. mpl default is False, matplotlibrc default is False, and seaborn never sets it (grep of seaborn/ and rcmod.py: no hits). Not a spec-vs-repo divergence.
2. axis.get_transform() -- a channel BEYOND get_view_interval, contradicting mapping 3.1's 'only thing it reads' claim. Found by spying on every axis attribute access: Log/LogSci/LogMathtext formatters call it in set_locs to read.linthresh. It is genuinely label-changing: 12 measured cases where the SAME (convention, ticks, residual, lo, hi) render differently with vs without a symlog linthresh (e.g. LogFormatter t=[1,3,10,30,100] -> ['1','','10','','100'] vs ['1','3','10','30','100']). CLOSED as UNREACHABLE at both modeled sites: seaborn's PseudoAxis has NO get_transform (confirmed by dir()) and site 2's dummy_axis defines get_view_interval and nothing else, so the try/AttributeError guard always takes the None branch. Confirmed behaviourally: 48 real site-1 calls across trans=None/'log'/'symlog'/'symlog(1)'/'symlog(10)' x 4 log-formatter kinds -> 0 sequence mismatches vs the model's transform-less deep model. mapping 3.1's wording is imprecise (get_transform is read, on the rendering path, by Log* kinds) but the model's 5-argument input list is COMPLETE for the two sites actually modeled, so the spec is not too strong.

**CONCLUSION:** no input was found on which the modeled functions disagree with the real gold-patched callees. ~12k differential calls + ~64k axiom checks, all six site-1 conventions and both rendering APIs, over corners the bundle's driver omitted (inverted, zero-width, non-containing and narrower ranges; mixed residual states; pre-used formatters; 16 formatter kinds; dtype variants). The spec is neither too strong nor drifting: it pins the state half (residual disabled, convention and both range bounds unchanged) and the text half (exact sequence from the formatter's own rendering) and every clause is discharged by the real patched code, while both same-spec pre-state twins fail on the very clause the patch installs. Verdict FAITHFUL; no diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ARTIFACT JUDGED (current bytes, re-derived myself): model.py sha256=9a70c4a3d5ac99cba8e77167cef9f99bd7d654364405c605ee8d29429ad680a6; markers.spec_view(model.py, get_backend('nagini')) sha256=d0d68ad9c1805445bc3fb71c3d8e0d143b1ec51127341d7ce15090a44107df83 == meta.json region_hashes.spec_view (so the spec_view hash is current, even though the other six region hashes are stale vs these bytes). 336-line view. Scratch under a mktemp dir; NOTE a fixed-path spec_view.py I first used was clobbered mid-run by a concurrent instance's artifact (astropy-13033 content), so I re-derived  and re-ran every grep with an assertion that the file's header names mwaskom__seaborn-3187. All conclusions below are from the asserted-correct file.

NO RELAXATION IN PLAY (checked, not assumed): meta.json has no `relaxed_leakage` key; gates.G-LEAK.status == "pass" (not "relaxed"); `find benchmark-verified/mwaskom__seaborn-3187 -iname '*relax*'` -> nothing. So there is no relaxation argument to re-derive; this is an ordinary strict leakage judgement.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as its own finding per instructions): leakage.reviewer_directed() over every.md/.py/.json in the instance dir (including the 445KB verdict.md) returns [] -- no bundle file instructs me how to record or which verdict is honest. verdict.md does carry prior panel records, including an earlier G-PANEL-3 LEAKAGE (sources digest 459e49f704b9..., the older two-flag mode_a/mode_b model) and a later NO-LEAKAGE. Per the retained-attack-label trap I inherited neither and re-measured from scratch; a transcript of prior rounds is not an instruction to me.

**CONSUMER SURFACE.** eval/dataset.py as_dict() ships problem_statement + spec_view + modeled_functions (+localization/changed_files in modes 0/1/2/100); refinement.md / mapping.md / patch.diff / meta.json are NOT shipped, and WITHHELD_FIELDS blocks patch/test_patch. So refinement.md A3/B3 naming set_useOffset/set_scientific verbatim, and mapping.md's get_useOffset()/`_scientific` reads, are outside the judged surface.

MECHANICAL SCREEN + POSITIVE CONTROL (my measurement, not the gate record): leakage.screen(model.py, nagini, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Control: I injected 'formatter.set_useOffset(False)' + 'seaborn/`_core`/scales.py' + 'fix' into the docstring and re-ran -> passed=False with L1 gold-line-reproduced, L2 patched-file-path (x2), L3 narration 'fix'. So the clean result is a real pass, not a vacuous one. Patch changed symbols {get_view_interval, spacer}: neither appears in any spec-view identifier or comment.

**TOKEN SWEEP.** Every >=4-char token on a gold +/- line, cross-checked against the view: set_useoffset, set_scientific, offset, scientific, notation, hasattr, major, avoid, incorrect, representing all ABSENT from the view. Present-and-PS-public: formatter, legend, label, which, that, ends. Present-but-not-in-PS: only generic English/structural words (axis, continuous, could, have, need, this, true, would) -- none localizing. Also swept hints_text-only vocabulary into the view: hits are 'like/only/other/same' (English), i.e. no hints-only term or diagnosis is echoed. No seaborn/mpl symbol at all: ScalarFormatter, EngFormatter, LogFormatter, StrMethodFormatter, ContinuousBase, locator_to_legend_entries, relplot, scatterplot, rcParam, spacer, get_view_interval, format_ticks -- all absent (only a bare `matplotlib` in the G-AX provenance sentence, which localizes nothing and is a library name PS itself invokes via ScalarFormatter).

THE ARITY QUESTION (the facet the prior round found leaking) -- re-measured on mpl 3.10.9 at the FAIL_TO_PASS scale (xy 0..3, color = xy + 1e8, MaxNLocator ticks, ScalarFormatter.format_ticks over a dummy axis reporting the data interval): both-on (prepatch) -> ['0.0'..'3.0'], test FAILS; set_useOffset(False) ONLY -> ['1.000000000'...], test FAILS; set_scientific(False) ONLY -> ['0.0'..'3.0'], test FAILS; both off (gold) -> ['100000000.0'...], test PASSES. So the genuinely hard, tested content of the gold edit is that TWO separately-toggled controls must both go off, and neither alone suffices. The spec view discloses NONE of it: it collapses the whole family into ONE opaque boolean `TickFormatter.residual` ("whether residual rendering is enabled"), never names either setter, never says there is more than one control, and pushes the arity + the hasattr guards into refinement.md/mapping.md, which the consumer never receives. The specific arity leak of the older two-flag model is repaired in these bytes.

WHAT THE VIEW DOES SAY, AND WHY EACH PIECE IS PS-COVERED. (a) 'legend labels must read back to the ticks' FULL absolute values, including large magnitudes' -- PS's own headline ("legends describing large numbers... formatted without their multiplicative offset value", the 1E6 body_mass_mg screenshot). (b) 'labels are the formatter's own text, one per tick, not reordered/dropped' -- PS names ScalarFormatter as the label source and links the exact producing lines. (c) 'two independent places build such numeric legends' -- PS publishes the second path itself ("The issue also reproduces if you create the mentioned plot using scatterplot"). (d) the convention/view-range arguments and the guarded (convention==0) reading clause -- these WEAKEN the spec (they carve out formatters for which no reading guarantee is claimed); they hand the solver nothing about the edit. On localization the view is strictly LESS revealing than the public PS, which quotes scales.py L377-382 by permalink and even names the relevant rcParams.

**CONSIDERED AND REJECTED AS A FINDING:** half (2), 'the formatter must be LEFT with residual rendering disabled', does foreclose the alternative route PS actually suggests ("the offset value can be safely retrieved... and used to create the legend title and/or labels"), so it narrows the solver toward gold's mutate-the-formatter approach. I do not call this leakage: it is a statement of required observable end-state on an object that outlives the call, in abstract vocabulary, and it is exactly what the hidden tests check (each label text alone must parse > 1e7, so the title route fails F2P). Pinning gold's observable behaviour is what makes the cell faithful -- G-DIFF confirms both prepatch models FAIL verification, so this clause is load-bearing spec content, not decoration -- and if 'the spec constrains behaviour to gold's behaviour' counted as leakage no spec could ever pass. The leakage standard in prompts/nagini/spec_guide.md sec6 is quoted diff lines / patched file-function-line / identifiers echoing patched symbols / bug-to-fix mechanism narration, and the view breaks none of them.

**SPEC-INTEGRITY:** `python -m swebench_unified.adversary same-spec nagini mwaskom__seaborn-3187 atk_id.py` -> exit 0, 'SAME -- attack shares the bundle's exact specification' (tooling sane). No counterexample is offered: this facet is leakage, not spec-weakness.

OBSERVED BUT NOT MY FACET (not claimed as leakage): G-PANEL-2 is recorded fail and G-PANEL aggregate is fail -- a faithfulness dispute over the unconditional rendered_labels sequence-equality clause and refinement.md A3's claim that the hasattr guards are no-ops (wrong for EngFormatter, a ScalarFormatter subclass where the guards pass yet residual persists). That belongs to G-PANEL-2/G-EQ. Also meta.json region_hashes for the six non-spec_view regions are stale relative to current model.py.

**CONCLUSION:** nothing in the spec view reproduces a gold line, names a patched file/module/symbol, echoes hints-only vocabulary, or narrates the bug-to-fix mechanism; the tested discriminator (two controls, both off, at two sites, with guards) is not reconstructible from the view beyond what problem_statement already publishes, and the view is less localizing than the PS. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
