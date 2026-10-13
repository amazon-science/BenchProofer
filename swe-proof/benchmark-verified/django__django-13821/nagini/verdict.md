# P2 adversarial audit — django__django-13821

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_14.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl exists. 14 same-spec attacks were run through `adversary weakness`; 13 were rejected by the verifier and the single CANDIDATE (atk_7) is the spec's own oracle read back (`if lt_lex(ToSeq(version), min_version()): raise`), i.e. a CORRECT ECHO, not a wrong impl. Its faithful refined patch was materialized (byte-identical to the gold patch, `diff` confirmed) and RUN through the official harness: run_resolve -> {completed: true, resolved: TRUE, attempts: 1, flaky: false}. verify=>correct holds on every impl probed.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,7 +108,10 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
+    # Pre-patch skeleton: the runtime is compared against the OLD threshold
+    # 3.8.3 instead of the supported minimum 3.9.0. Everything else (the
+    # component-wise comparison, the raise on "below") is unchanged.
+    mn = [3, 8, 3]  # type: List[int]
     below = False
     i = 0
     n = len(version)
@@ -119,12 +122,11 @@
         Invariant(Acc(list_pred(mn)))
         Invariant(0 <= i and i <= n and i <= m)
         Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
+        Invariant(ToSeq(mn) == PSeq(3, 8, 3))
         Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
+        # What the pre-patch loop actually computes: the ordering against 3.8.3.
+        Invariant(lt_lex(ToSeq(version), PSeq(3, 8, 3))
+                  == lt_lex(ToSeq(version).drop(i), PSeq(3, 8, 3).drop(i)))
         # The comparison loop consumes the caller's termination obligation
         # with a strictly decreasing measure (m - i), discharging
         # MustTerminate(2) from the precondition.
@@ -133,9 +135,9 @@
         a = version[i]
         b = mn[i]
         Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
+        Assert(PSeq(3, 8, 3).drop(i)[0] == b)
         Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
+        Assert(PSeq(3, 8, 3).drop(i).drop(1) == PSeq(3, 8, 3).drop(i + 1))
         if a < b:
             below = True
             break
@@ -145,12 +147,12 @@
         i = i + 1
     else:
         # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
+        # runtime is below the threshold iff it is the strict prefix, i.e. it
+        # ran out of components first.
         Assert(i == n or i == m)
         if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
+            # threshold exhausted first => runtime is longer => not below.
+            Assert(len(PSeq(3, 8, 3).drop(i)) == 0)
             below = False
         elif i < m:
             # runtime exhausted first => runtime is a strict prefix => below.
@@ -159,7 +161,7 @@
         else:
             # both exhausted simultaneously => equal => not below.
             Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
+            Assert(len(PSeq(3, 8, 3).drop(i)) == 0)
             below = False
     if below:
         raise UnsupportedConfiguration()
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,59 +108,25 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
+    n = len(version)
+    c0 = 3
+    c1 = 9
+    c2 = 0
+    if n > 0:
+        c0 = version[0]
+    if n > 1:
+        c1 = version[1]
+    if n > 2:
+        c2 = version[2]
     below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
+    if c0 < 3:
+        below = True
+    elif c0 == 3:
+        if c1 < 9:
             below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
+        elif c1 == 9:
+            if c2 < 0:
+                below = True
     if below:
         raise UnsupportedConfiguration()
     return
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,60 +108,7 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
-    below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
-        raise UnsupportedConfiguration()
+    if lt_lex(ToSeq(version), min_version()):
+        check_supported_version(version)
     return
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,59 +108,13 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
     below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
+    if len(version) == 3:
+        if version[0] < 3:
             below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
+        elif version[0] == 3:
+            if version[1] < 9:
+                below = True
     if below:
         raise UnsupportedConfiguration()
     return
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,60 +108,7 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
-    below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
+    if not lt_lex(min_version(), ToSeq(version)):
         raise UnsupportedConfiguration()
     return
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -109,7 +109,6 @@
     # post-conditions-end
     # impl-start
     mn = [3, 9, 0]  # type: List[int]
-    below = False
     i = 0
     n = len(version)
     m = len(mn)
@@ -120,48 +119,10 @@
         Invariant(0 <= i and i <= n and i <= m)
         Invariant(n == len(version) and m == len(mn))
         Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(m - i + 1))
         # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
+        if version[i] < mn[i]:
+            raise UnsupportedConfiguration()
         i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
-        raise UnsupportedConfiguration()
     return
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,60 +108,7 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
-    below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
+    if lt_lex(ToSeq(version), min_version()):
         raise UnsupportedConfiguration()
     return
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,59 +108,11 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
     below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
+    if len(version) == 0:
+        below = True
+    elif version[0] < 3:
+        below = True
     if below:
         raise UnsupportedConfiguration()
     return
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,60 +108,7 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
-    below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
+    if lt_lex(min_version(), ToSeq(version)):
         raise UnsupportedConfiguration()
     return
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,59 +108,12 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
     below = False
-    i = 0
     n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
+    if n < 2:
+        below = True
+    elif version[1] < 9:
+        below = True
     if below:
         raise UnsupportedConfiguration()
     return
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,60 +108,10 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
-    below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
-        raise UnsupportedConfiguration()
+    try:
+        if lt_lex(ToSeq(version), min_version()):
+            raise UnsupportedConfiguration()
+    except UnsupportedConfiguration:
+        pass
     return
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,60 +108,12 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
-    below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
+    if lt_lex(ToSeq(version), min_version()):
+        raise UnsupportedConfiguration()
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
         # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
-        raise UnsupportedConfiguration()
+        Assert(not lt_lex(ToSeq(version), min_version()))
     return
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -121,13 +121,8 @@
         Invariant(n == len(version) and m == len(mn))
         Invariant(ToSeq(mn) == min_version())
         Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
         Invariant(lt_lex(ToSeq(version), min_version())
                   == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(m - i + 1))
         # invariants-end
         a = version[i]
@@ -144,20 +139,14 @@
             break
         i = i + 1
     else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
         Assert(i == n or i == m)
         if i < n:
-            # minimum exhausted first => runtime is longer => not below.
             Assert(len(min_version().drop(i)) == 0)
-            below = False
+            below = True
         elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
             Assert(len(ToSeq(version).drop(i)) == 0)
             below = True
         else:
-            # both exhausted simultaneously => equal => not below.
             Assert(len(ToSeq(version).drop(i)) == 0)
             Assert(len(min_version().drop(i)) == 0)
             below = False
```

Attack 14 — `atk_14.py` → not a counterexample (the checker could not translate this program, so the spec never judged it) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -108,60 +108,7 @@
             and lt_lex(ToSeq(version), min_version()))
     # post-conditions-end
     # impl-start
-    mn = [3, 9, 0]  # type: List[int]
-    below = False
-    i = 0
-    n = len(version)
-    m = len(mn)
-    while i < n and i < m:
-        # invariants-start
-        Invariant(Acc(list_pred(version), 1 / 2))
-        Invariant(Acc(list_pred(mn)))
-        Invariant(0 <= i and i <= n and i <= m)
-        Invariant(n == len(version) and m == len(mn))
-        Invariant(ToSeq(mn) == min_version())
-        Invariant(not below)
-        # The undecided prefix has been consumed equal so far: the ordering of
-        # the full sequences equals the ordering of their i-suffixes.
-        Invariant(lt_lex(ToSeq(version), min_version())
-                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
-        # The comparison loop consumes the caller's termination obligation
-        # with a strictly decreasing measure (m - i), discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(m - i + 1))
-        # invariants-end
-        a = version[i]
-        b = mn[i]
-        Assert(ToSeq(version).drop(i)[0] == a)
-        Assert(min_version().drop(i)[0] == b)
-        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
-        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
-        if a < b:
-            below = True
-            break
-        if a > b:
-            below = False
-            break
-        i = i + 1
-    else:
-        # The loop ran to exhaustion (no break): one sequence ran out. The
-        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
-        # out of components first.
-        Assert(i == n or i == m)
-        if i < n:
-            # minimum exhausted first => runtime is longer => not below.
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-        elif i < m:
-            # runtime exhausted first => runtime is a strict prefix => below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            below = True
-        else:
-            # both exhausted simultaneously => equal => not below.
-            Assert(len(ToSeq(version).drop(i)) == 0)
-            Assert(len(min_version().drop(i)) == 0)
-            below = False
-    if below:
-        raise UnsupportedConfiguration()
+    if lt_lex(ToSeq(version), min_version()):
+        raise ValueError()
     return
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ, django__django-13821 (nagini). All 14 attacks are byte-identical to model.py outside the impl region (`adversary same-spec` exit 0 on all 14, and on pc.py). Verification runs were batched 3-at-a-time as concurrent background jobs (JVM+Z3 each) under SBU_ATTACK_VERIFY_TIMEOUT=900 SBU_ATTACK_VERIFY_RETRY=3; no host-cap/timeout/crash occurred, so every attack carries a real verifier verdict (no INCONCLUSIVE lane).

**POSITIVE CONTROL:** pc.py (= model.py, md5 24e782e1c8c3ac18b3e8ba8da413ddf7) -> `bash scripts/nagini_verify.sh` exit 0, "Verification successful" (15.3s).

**PREPATCH REPRODUCED:** atk_1 is model_prepatch.py's impl region (old threshold [3,8,3]) grafted onto the frozen spec -> weakness exit 2, does not verify. The spec senses the behavioural delta.

PER-ATTACK LEDGER (cmd: `python -m swebench_unified.adversary weakness nagini django__django-13821 <path>`; exit 2 = rejected/good, exit 0 = CANDIDATE): atk_1.py  prepatch bug, threshold [3,8,3]                            exit 2 rejected atk_2.py  ZERO-PADDING prefix semantics: (3,9) treated as (3,9,0) and accepted; real tuple < makes (3,9)<(3,9,0) True. Targets A3 prefix rule, SHORT direction.   exit 2 rejected atk_3.py  CONTROL-FLOW-EFFECT / vacuity: guarded SELF-CALL instead of raise on the reject path (the classic infeasible-continuation trick). exit 2 rejected; direct verify shows the reason is exactly the A0 termination leg: "Obligation leak check failed.

Callee check_supported_version might not take all unsatisfied obligations from the caller."   exit 2 rejected atk_4.py  PARTIAL DOMAIN: only len(version)==3 decided, everything else accepted; the 4-component F2P runtime (3,8,11,1) slips through.  exit 2 rejected atk_5.py  BOUNDARY: non-strict, rejects the exact minimum 3.9.0 too (reject iff not lt_lex(min, version)).  exit 2 rejected atk_6.py  CONTROL-FLOW-EFFECT: raises as soon as ANY component is smaller without requiring the earlier ones to compare EQUAL; right on both F2P-visible points, wrong on (4,8,0) and (3,).  exit 2 rejected atk_7.py  UNGROUNDED-ORACLE ECHO: the spec predicate read back. exit 0 CANDIDATE (13.5s) -> patch materialized and RESOLVED (see below). atk_8.py  MAJOR-ONLY guard: any 3.x accepted, so 3.8.11.1 accepted.  exit 2 rejected atk_9.py  FLIPPED oracle (lt_lex(min, version)): rejects every supported runtime; probes whether lt_lex is really evaluated rather than treated opaquely.  exit 2 rejected atk_10.py MINOR-ONLY guard: right on BOTH F2P-visible points ((3,8,11,1) rejected, (3,9,0) accepted) yet wrong on (2,9,9) and (4,0,0) — the "passes the visible test but is wrong" shape.  exit 2 rejected atk_11.py CONTROL-FLOW-EFFECT: decision exactly right, raise SWALLOWED by a local try/except so the function always returns normally.  exit 2 rejected atk_12.py DIVERGENCE ON THE ACCEPT PATH (the other branch from atk_3): reject path exact, supported runtimes hang forever. exit 2 rejected; direct verify reason is again A0: "Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context."  exit 2 rejected atk_13.py A3 prefix rule, LONG direction: (3,9,0,0) wrongly rejected though real tuple < makes (3,9,0,0)<(3,9,0) False.  exit 2 rejected atk_14.py Right DECISION, WRONG EXCEPTION TYPE (raise ValueError). exit 2, but the direct-verify log shows "Translation failed / Not supported: Unsupported builtin function" — a TRANSLATOR limitation, NOT a spec rejection. Reported honestly as no-verdict; it is not counted as evidence in either direction (this is the very translator limit mapping.md §2 documents as the reason UnsupportedConfiguration is user-defined). Retained in the list for the runner's own re-check; the >=5-attack bar is met without it (12 genuine rejections + 1 resolving echo).

MANDATORY RESOLVE RUN (the only CANDIDATE): faithful refined patch for atk_7 written to atk_7.patch, executed via harness.run_resolve (`python do_resolve.py django__django-13821 atk_7.patch atk7`, run_id sbu-eq-s4-oqce1-atk7, timeout 3600). RESULT: {"completed": true, "resolved": true, "attempts": 1, "flaky": false, "note": "resolved"}. `diff atk_7.patch patch.diff` -> IDENTICAL to the gold patch, which is what a correct echo must produce. NOT a weakness. Per the retained-label rule, an echo whose patch resolves is recorded as a correct echo and never re-judged into the reject lane.

### A-LEG AUDIT (the assigned focus; R/I legs left to G-CONF).
refinement.md legs: A0=R, A1=R, A2=I, A3=A-REFERENCE, A4=R. Every leg is R / A-reference / I; there is NO kind-3 (unexpressible-changed-op) step and NO A-consumed leg at all — confirmed mechanically: `grep -c ContractOnly model.py` = 0, and the axioms region is an explanatory comment only. So refinement.md §B's claim "no consumed @ContractOnly axiom" is TRUE, and the changed operation is not hidden behind an axiom: the changed constant is I against the gold literal (3,9,0) and the comparison consuming it is spelled out deeply as lt_lex.

A3 (the sole A-reference) INDEPENDENTLY RE-AUDITED, not taken on axiom_check.py's word: I transliterated model.py's @Pure lt_lex RECURSIVELY (statement-for-statement,.drop(1) -> [1:]), rather than reusing axiom_check.py's loop rewrite, and fuzzed it against the REAL callee (Python tuple <): 781-sequence exhaustive decision domain (len<=4 over 0..4) + 160,000 boundary pairs + 200,000 randomized pairs (components -3..60, lengths 0..6, incl. negatives) -> 0 mismatches. I also cross-checked axiom_check.py's own loop reference against the recursive form on the same 360k inputs -> 0 mismatches, so axiom_check.py's rewrite is not itself masking a fold bug.

Discriminating facts re-confirmed: lt_lex((3,8,11,1),(3,9,0))=True, lt_lex((3,9,0),(3,9,0))=False, lt_lex((3,9),(3,9,0))=True (short prefix IS below), lt_lex((3,9,0,0),(3,9,0))=False (long equal-prefix is NOT below), and not ((3,8,11,1)<(3,8,3)) (the prepatch bug). The A3 correspondence to the real callee holds. Independently, atk_2 and atk_13 attack the two prefix directions the A-reference rests on and BOTH are rejected by the verifier, so the deep model is load-bearing in the proof, not decorative. A0 (MustTerminate) is genuinely load-bearing on BOTH branches, not just the documented one: atk_3 (reject-path self-call) and atk_12 (accept-path divergence) are each rejected specifically by the obligation-leak check. The A0 justification in refinement.md cites only the reject-path hang; the accept-path hang is also caught, so the leg is stronger than documented, not weaker.

ADVISORY (NOT a break; wording precision on the A4 message leg). refinement.md A4 / mapping.md §4 say the message string "carr[ies] no behaviour beyond the reject condition". I measured that claim rather than accepting it: a diagnostic patch with the CORRECT threshold (3,9,0) but the OLD message text ('SQLite 3.8.3 or later...') was run through run_resolve -> {completed: true, resolved: FALSE, attempts: 3, flaky: false} (diag_msgleg.patch, res_msgleg.json). So the message IS test-observed (assertRaisesMessage).

This does NOT break the spec, because the message is not a free parameter of a faithful refinement: under the refinement map's own presentation rule it is the dotted rendering of the modeled constant, and rendering it from min_version()==PSeq(3,9,0) yields exactly the F2P string 'SQLite 3.9.0 or later is required (found 3.8.11.1).' (checked mechanically; the same rule renders the prepatch message from (3,8,3)). The msgleg patch is therefore an UNFAITHFUL refinement (message rendered from a constant other than the modeled one), not the faithful refinement of any verifying impl — hence no verify=>correct violation. Recommend tightening A4's phrasing from "carries no behaviour" to "is a total function of the modeled minimum, so a faithful refinement cannot vary it independently", which is both stronger and what the harness actually measures.

**VERDICT:** SOUND. 14 same-spec attacks encoded and run (12 genuine verifier rejections spanning partial-domain, boundary, control-flow-effect, prefix-rule/A-reference, divergence-on-both-branches and oracle-flip shapes; 1 translator no-verdict reported as such; 1 correct oracle echo whose materialized faithful patch RESOLVED under the official harness). Prepatch reproduced and rejected. Positive control verifies. No verifying wrong impl was found, so no verify=>correct counterexample exists at this attack depth. Bar for SOUND (>=5 attacks run, none breaks it, every CANDIDATE's patch actually executed through run_resolve) is met with evidence recorded for each.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_14.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl exists. 14 same-spec attacks were run through `adversary weakness`; 13 were rejected by the verifier and the single CANDIDATE (atk_7) is the spec's own oracle read back (`if lt_lex(ToSeq(version), min_version()): raise`), i.e. a CORRECT ECHO, not a wrong impl. Its faithful refined patch was materialized (byte-identical to the gold patch, `diff` confirmed) and RUN through the official harness: run_resolve -> {completed: true, resolved: TRUE, attempts: 1, flaky: false}. verify=>correct holds on every impl probed.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ, django__django-13821 (nagini). All 14 attacks are byte-identical to model.py outside the impl region (`adversary same-spec` exit 0 on all 14, and on pc.py). Verification runs were batched 3-at-a-time as concurrent background jobs (JVM+Z3 each) under SBU_ATTACK_VERIFY_TIMEOUT=900 SBU_ATTACK_VERIFY_RETRY=3; no host-cap/timeout/crash occurred, so every attack carries a real verifier verdict (no INCONCLUSIVE lane).

**POSITIVE CONTROL:** pc.py (= model.py, md5 24e782e1c8c3ac18b3e8ba8da413ddf7) -> `bash scripts/nagini_verify.sh` exit 0, "Verification successful" (15.3s).

**PREPATCH REPRODUCED:** atk_1 is model_prepatch.py's impl region (old threshold [3,8,3]) grafted onto the frozen spec -> weakness exit 2, does not verify. The spec senses the behavioural delta.

PER-ATTACK LEDGER (cmd: `python -m swebench_unified.adversary weakness nagini django__django-13821 <path>`; exit 2 = rejected/good, exit 0 = CANDIDATE): atk_1.py  prepatch bug, threshold [3,8,3]                            exit 2 rejected atk_2.py  ZERO-PADDING prefix semantics: (3,9) treated as (3,9,0) and accepted; real tuple < makes (3,9)<(3,9,0) True. Targets A3 prefix rule, SHORT direction.   exit 2 rejected atk_3.py  CONTROL-FLOW-EFFECT / vacuity: guarded SELF-CALL instead of raise on the reject path (the classic infeasible-continuation trick). exit 2 rejected; direct verify shows the reason is exactly the A0 termination leg: "Obligation leak check failed.

Callee check_supported_version might not take all unsatisfied obligations from the caller."   exit 2 rejected atk_4.py  PARTIAL DOMAIN: only len(version)==3 decided, everything else accepted; the 4-component F2P runtime (3,8,11,1) slips through.  exit 2 rejected atk_5.py  BOUNDARY: non-strict, rejects the exact minimum 3.9.0 too (reject iff not lt_lex(min, version)).  exit 2 rejected atk_6.py  CONTROL-FLOW-EFFECT: raises as soon as ANY component is smaller without requiring the earlier ones to compare EQUAL; right on both F2P-visible points, wrong on (4,8,0) and (3,).  exit 2 rejected atk_7.py  UNGROUNDED-ORACLE ECHO: the spec predicate read back. exit 0 CANDIDATE (13.5s) -> patch materialized and RESOLVED (see below). atk_8.py  MAJOR-ONLY guard: any 3.x accepted, so 3.8.11.1 accepted.  exit 2 rejected atk_9.py  FLIPPED oracle (lt_lex(min, version)): rejects every supported runtime; probes whether lt_lex is really evaluated rather than treated opaquely.  exit 2 rejected atk_10.py MINOR-ONLY guard: right on BOTH F2P-visible points ((3,8,11,1) rejected, (3,9,0) accepted) yet wrong on (2,9,9) and (4,0,0) — the "passes the visible test but is wrong" shape.  exit 2 rejected atk_11.py CONTROL-FLOW-EFFECT: decision exactly right, raise SWALLOWED by a local try/except so the function always returns normally.  exit 2 rejected atk_12.py DIVERGENCE ON THE ACCEPT PATH (the other branch from atk_3): reject path exact, supported runtimes hang forever. exit 2 rejected; direct verify reason is again A0: "Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context."  exit 2 rejected atk_13.py A3 prefix rule, LONG direction: (3,9,0,0) wrongly rejected though real tuple < makes (3,9,0,0)<(3,9,0) False.  exit 2 rejected atk_14.py Right DECISION, WRONG EXCEPTION TYPE (raise ValueError). exit 2, but the direct-verify log shows "Translation failed / Not supported: Unsupported builtin function" — a TRANSLATOR limitation, NOT a spec rejection. Reported honestly as no-verdict; it is not counted as evidence in either direction (this is the very translator limit mapping.md §2 documents as the reason UnsupportedConfiguration is user-defined). Retained in the list for the runner's own re-check; the >=5-attack bar is met without it (12 genuine rejections + 1 resolving echo).

MANDATORY RESOLVE RUN (the only CANDIDATE): faithful refined patch for atk_7 written to atk_7.patch, executed via harness.run_resolve (`python do_resolve.py django__django-13821 atk_7.patch atk7`, run_id sbu-eq-s4-oqce1-atk7, timeout 3600). RESULT: {"completed": true, "resolved": true, "attempts": 1, "flaky": false, "note": "resolved"}. `diff atk_7.patch patch.diff` -> IDENTICAL to the gold patch, which is what a correct echo must produce. NOT a weakness. Per the retained-label rule, an echo whose patch resolves is recorded as a correct echo and never re-judged into the reject lane.

### A-LEG AUDIT (the assigned focus; R/I legs left to G-CONF).
refinement.md legs: A0=R, A1=R, A2=I, A3=A-REFERENCE, A4=R. Every leg is R / A-reference / I; there is NO kind-3 (unexpressible-changed-op) step and NO A-consumed leg at all — confirmed mechanically: `grep -c ContractOnly model.py` = 0, and the axioms region is an explanatory comment only. So refinement.md §B's claim "no consumed @ContractOnly axiom" is TRUE, and the changed operation is not hidden behind an axiom: the changed constant is I against the gold literal (3,9,0) and the comparison consuming it is spelled out deeply as lt_lex.

A3 (the sole A-reference) INDEPENDENTLY RE-AUDITED, not taken on axiom_check.py's word: I transliterated model.py's @Pure lt_lex RECURSIVELY (statement-for-statement,.drop(1) -> [1:]), rather than reusing axiom_check.py's loop rewrite, and fuzzed it against the REAL callee (Python tuple <): 781-sequence exhaustive decision domain (len<=4 over 0..4) + 160,000 boundary pairs + 200,000 randomized pairs (components -3..60, lengths 0..6, incl. negatives) -> 0 mismatches. I also cross-checked axiom_check.py's own loop reference against the recursive form on the same 360k inputs -> 0 mismatches, so axiom_check.py's rewrite is not itself masking a fold bug.

Discriminating facts re-confirmed: lt_lex((3,8,11,1),(3,9,0))=True, lt_lex((3,9,0),(3,9,0))=False, lt_lex((3,9),(3,9,0))=True (short prefix IS below), lt_lex((3,9,0,0),(3,9,0))=False (long equal-prefix is NOT below), and not ((3,8,11,1)<(3,8,3)) (the prepatch bug). The A3 correspondence to the real callee holds. Independently, atk_2 and atk_13 attack the two prefix directions the A-reference rests on and BOTH are rejected by the verifier, so the deep model is load-bearing in the proof, not decorative. A0 (MustTerminate) is genuinely load-bearing on BOTH branches, not just the documented one: atk_3 (reject-path self-call) and atk_12 (accept-path divergence) are each rejected specifically by the obligation-leak check. The A0 justification in refinement.md cites only the reject-path hang; the accept-path hang is also caught, so the leg is stronger than documented, not weaker.

ADVISORY (NOT a break; wording precision on the A4 message leg). refinement.md A4 / mapping.md §4 say the message string "carr[ies] no behaviour beyond the reject condition". I measured that claim rather than accepting it: a diagnostic patch with the CORRECT threshold (3,9,0) but the OLD message text ('SQLite 3.8.3 or later...') was run through run_resolve -> {completed: true, resolved: FALSE, attempts: 3, flaky: false} (diag_msgleg.patch, res_msgleg.json). So the message IS test-observed (assertRaisesMessage).

This does NOT break the spec, because the message is not a free parameter of a faithful refinement: under the refinement map's own presentation rule it is the dotted rendering of the modeled constant, and rendering it from min_version()==PSeq(3,9,0) yields exactly the F2P string 'SQLite 3.9.0 or later is required (found 3.8.11.1).' (checked mechanically; the same rule renders the prepatch message from (3,8,3)). The msgleg patch is therefore an UNFAITHFUL refinement (message rendered from a constant other than the modeled one), not the faithful refinement of any verifying impl — hence no verify=>correct violation. Recommend tightening A4's phrasing from "carries no behaviour" to "is a total function of the modeled minimum, so a faithful refinement cannot vary it independently", which is both stronger and what the harness actually measures.

**VERDICT:** SOUND. 14 same-spec attacks encoded and run (12 genuine verifier rejections spanning partial-domain, boundary, control-flow-effect, prefix-rule/A-reference, divergence-on-both-branches and oracle-flip shapes; 1 translator no-verdict reported as such; 1 correct oracle echo whose materialized faithful patch RESOLVED under the official harness). Prepatch reproduced and rejected. Positive control verifies. No verifying wrong impl was found, so no verify=>correct counterexample exists at this attack depth. Bar for SOUND (>=5 attacks run, none breaks it, every CANDIDATE's patch actually executed through run_resolve) is met with evidence recorded for each.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK LANE:** faithfulness-break (is the spec too strong / does the modeled function disagree with the real callee?). Result: NO divergence found. Reference used correctly = base_commit worktree WITH patch.diff APPLIED (, gold patch applied cleanly; real patched callee co_consts confirmed (None, (3, 9, 0), 'SQLite 3.9.0 or later is required (found %s).')).

### Machine facts
1. Spec-region integrity: swebench_unified.markers.region_hashes(model.py, nagini backend) reproduces every hash recorded in meta.json G-HYGIENE byte-for-byte (axioms 86e46c4c6423, pure a0198e600b90, pre-conditions 51025e7efc68, post-conditions 53009c4a8aff, invariants 57ed43c4b855, impl 064ae8e96780, spec_view e018972191f0).
2. Verifier: scripts/nagini_verify.sh model.py => 'Verification successful' (13.98s), exit 0.
3. **G-AX:** axiom_check.py exit 0. Independently re-derived: I transcribed the @Pure front-recursive lt_lex VERBATIM from the spec region (PSeq.drop(1) -> tuple slicing) and checked lt_lex(a,b) == (tuple(a) < tuple(b)) exhaustively over all pairs of length 0-4 from alphabet {-1,0,2,3,8,9,10} plus 200k randomized pairs with components up to `2**40` and negatives: 0 mismatches. lt_lex IS Python tuple '<'.
4. DECISIVE spec-vs-real differential (the actual faithfulness test): the SPEC predicate (reject iff lt_lex(ToSeq(version), min_version()), taken from the Ensures/Exsures pair) vs the REAL PATCHED check_sqlite_version, injecting each version via Database.sqlite_version_info/.sqlite_version exactly as the repo's own test does. 67,394 inputs (exhaustive length 0-4 over {-3,0,2,3,4,8,9,10,11}, boundary set, huge `2**63` components, 60k fuzz): 0 DISAGREEMENTS.
5. Impl-vs-real, independently extracted: I did NOT trust conformance_check.py's hand-copied shadow. I AST-parsed model.py, dropped only Requires/Ensures/Exsures/Invariant/Assert Expr nodes (preserving the while/else control flow verbatim), and ran it against the real patched callee: 47,391 inputs, 0 disagreements. Notably the while/else + break semantics Nagini verified match CPython. F2P (3,8,11,1)->reject/reject; boundary (3,9,0)->accept/accept.
6. End-to-end F2P: applied the gold test_patch, ran backends.sqlite.tests.Tests.test_check_sqlite_version in the patched worktree => OK (1 test). NOTE: required `env -u PYTHONPATH` — a stale PYTHONPATH from another instance's worktree () leaks into the tool shell and causes a spurious NullTimeKeeper ImportError; that is host contamination, not a bundle defect.

OVER-STRENGTH PROBE (the real way this lane fails a good spec): I tested whether the spec is satisfiable ONLY by the bundle's own loop, which would make it too strong. Built a structurally DIFFERENT gold-faithful impl — fully unrolled, straight-line, no loop, no while/else, no invariants — over the frozen spec. First two attempts failed the Exsures, but Assume-based branch isolation localized it precisely: the n==0 and version[0]<3 branches verify unaided, while n==1/n==2 need explicit recursive unfold hints for lt_lex (and the equal-case needs a drop(3) hint). Supplying those Asserts, the unrolled impl VERIFIES ('Verification successful', 12.60s). So the earlier failures were a proof-hint gap in MY code, not spec over-strength — the frozen spec admits at least two structurally distinct gold-faithful implementations.
  - adversary same-spec on that impl: exit 0, 'SAME — attack shares the bundle's exact specification' (after fixing a marker-indentation artifact of my own generator; region_hashes confirm all four spec regions + spec_view identical, impl differs).
  - adversary weakness: 'CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies'. This is NOT a weakness finding — the impl is gold-faithful by construction and agrees with the real patched callee on 47,389 inputs (0 disagreements). I report it only so the label is not mistaken for a defect.

TRAP AVOIDED (documented explicitly): comparing the spec against the UNPATCHED base commit yields 'divergences' on exactly [3,8,3], [3,8,4], [3,8,11,1], [3,8,99] — i.e. precisely the interval [3.8.3, 3.9.0) the patch redefines (base co_consts show the old (3, 8, 3) threshold). That is the delta the patch INTRODUCES, and reporting it as UNFAITHFUL would condemn a correct spec. The base commit is the reference only for callees the patch does not touch — here the sole callee is Python's tuple '<', which is unchanged and is the A-reference G-AX validates (no consumed @ContractOnly axiom in this bundle).

G-DIFF control: model_prepatch.py FAILS verification with exactly the expected error — 'Postcondition... Assertion lt_lex(ToSeq(version), min_version()) might not hold' — confirming the spec genuinely senses the threshold change rather than being vacuous.

RESIDUAL (under-specification, NOT a faithfulness defect, and out of this lane): the spec pins only the accept/reject DECISION and the fact of the raise, not the message string 'SQLite 3.9.0 or later is required (found %s).' that the F2P test asserts via assertRaisesMessage, and it substitutes UnsupportedConfiguration for ImproperlyConfigured. mapping.md §4 discloses both and argues the message is a presentation of the same modeled minimum. This is a spec-too-WEAK surface (G-EQ's lane: an impl could raise with a wrong message and still verify) and is the direction OPPOSITE to my attack. It cannot make the spec too strong, so it does not support UNFAITHFUL. MustTerminate(2) is a genuine strengthening but a sound one — the real guard is straight-line import-time code that always returns or raises, so it excludes no real behavior.

**CONCLUSION:** no input exists where the modeled function disagrees with the real (patched) callee. Faithfulness attack FAILS; spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Attacker(3) leakage / gold-reconstruction, django__django-13821 (nagini). MY OWN MEASUREMENTS, run in a /tmp scratch.

**RELAXATION STATUS:** there is NO documented relaxation in this bundle. No RELAXED_LEAKAGE.md exists (ls of the bundle dir: axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, pbt_result.json, properties.py, refinement.md, verdict.md — no such file), and meta.json has no relaxed_leakage key (top-level keys enumerated; 'relaxed_leakage' in meta -> False). So I judged this as a plain leakage question with no disposition to inherit or re-derive.

**SCOPE.** The consumer spec view is markers.spec_view(model.py) for the nagini/python flavor — signature + axioms/pure/pre-conditions/post-conditions regions, with impl (and nested invariants) replaced by the elision placeholder. I generated it directly (swebench_unified.markers.spec_view with get_backend('nagini')) and judged that text. refinement.md and mapping.md are audit artifacts, not the consumer view (mapping.md itself labels the pre-patch value as 'for the refinement audit, not referenced from the consumer spec view'), and G-LEAK screens only the model.py projection — consistent with what I screened.

1) MECHANICAL SCREEN (my run, not the recorded one). leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> hard_failures=[], warnings=[], passed=True. Screened against problem_statement only, never hints_text (hints_text is empty here anyway).

2) **NOTHING FROM THE GOLD EDIT IS IN THE VIEW.** Substring probes on the generated view: '3.8.3' False, '3, 8, 3' False, '3.8.2' False (old test value), '3.8.11' / '8, 11' / '11, 1' False (the F2P discriminator tuple is NOT named), 'ImproperlyConfigured' False, 'sqlite_version_info' False, 'check_sqlite_version' False, 'base.py' False, 'or later is required' False, 'found %s' False. Patched file path django/db/backends/sqlite3/base.py and its dotted form: absent. Only patch-touched def/class symbol is 'list_aggregate' (a hunk-header artifact) — absent from the view. Every version-like token in the view is {'3.8', '3.9.0'}, and BOTH are verbatim public: the problem_statement title is 'Drop support for SQLite < 3.9.0' and the body says 'supported on SQLite 3.9.0+' and 'Debian Jessie ships with 3.8.7'.

3) **THE ONE CONSTANT IN THE VIEW IS PUBLIC AND LOAD-BEARING.** The only edit-discriminating content in the view is min_version() == PSeq(3, 9, 0) plus the prose 'minimum supported version is 3.9.0'. That value is fully public (see 2). I still ran the strip test to confirm it is load-bearing rather than removable narration: I copied model_prepatch.py to /tmp and weakened only the SPEC constant (return PSeq(3, 9, 0) -> PSeq(3, 8, 3)); scripts/nagini_verify.sh on that variant returned exit 0 ('Verification successful', 14.4s) — i.e. with the threshold relaxed the PRE-patch impl verifies. Against the real frozen spec, scripts/nagini_verify.sh model_prepatch.py returned exit 1 with 'Postcondition of check_supported_version might not hold. Assertion lt_lex(ToSeq(version), min_version()) might not hold.' (G-DIFF re-confirmed by me). So the clause carries the entire behavioural delta; it cannot be elided and still have the spec sense the change. scripts/nagini_verify.sh model.py -> exit 0 (19.0s), so the frozen artifact is sound as the baseline for that comparison.

4) **THE CONSTANT IS FROZEN AGAINST AN ATTACKER.** adversary same-spec on the prepatch impl (spec bytes untouched, impl region only) -> exit 0 'SAME'. adversary same-spec on my strip variant -> exit 1 'DIFFERENT', diffing exactly the min_version body. So min_version() sits inside the compared spec signature; no attack can relocate the modeled minimum, which is what makes the message-string abstraction defensible rather than a hole.

5) **NO PROBLEM-STATEMENT-ONLY GAP.** Nothing in the view is both non-public and elidable. The closest residual is the prose 'any 3.8-series runtime (3.8.x for every finer level, including finer levels whose numeric value is large) is BELOW 3.9.0' — it gestures at the 11>9 component trap. I judged it NOT a leak: it is a consequence of the standard component-wise ordering that lt_lex already spells out in full, the discriminator tuple (3,8,11,1) is never named, and it localizes no file, symbol, or old value. It is a restatement of publicly-derivable ordering semantics on a publicly-stated threshold.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as a finding in its own right, per instructions): no file instructs me how to record or which verdict is honest. However, verdict.md (261KB) DOES retain prior recorded panel role notes verbatim, including a 'Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)' block whose prose closely tracks the reasoning shape of this very role. That is a retained prior verdict sitting inside the artifact under review — a real re-judging hazard (a reviewer could echo it instead of measuring). I flag it as an observation, not as steering: it reports a past run rather than directing this one. My verdict above rests on the seven commands I ran myself (three nagini_verify invocations, two adversary same-spec invocations, one leakage.screen, one spec_view generation), not on that block.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
