# P2 adversarial audit — django__django-11728

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,36 +103,32 @@
     prev = prev0
     i = 0
     res = -1
-    while i < len(region) and bal != 0:
+    while i < len(region):
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
         Invariant(bal >= 0)
         Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
-        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
-        Invariant(Implies(bal >= 1,
-                          close_off(ToSeq(region), 1, prev0)
-                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
-        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
+        # Termination: `i` rises by exactly 1 on every pass that reaches the
+        # loop head again (the early `break` only exits sooner) and
+        # `len(region)` is fixed, so `len(region) - i + 1` strictly decreases
+        # and is >= 2 at every loop head, where `i < len(region)` holds.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
+        # PRE-PATCH (buggy): the depth==0 test is at the TOP of the loop body,
+        # before the current character is processed. The depth only reaches
+        # zero after the closing parenthesis has been read, so detection is
+        # deferred to the NEXT iteration; when the closing parenthesis is the
+        # final character of the region that next iteration never runs and the
+        # span is never recorded.
+        if bal == 0:
+            res = i
+            break
         val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
         nb = step_bal(val, prev, bal)
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
-        if bal == 0:
-            res = i
     return res
     # impl-end
 
@@ -156,33 +152,31 @@
     prev = prev0
     i = 0
     res = -1
-    while i < len(region) and bal != 0:
+    while i < len(region):
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
         Invariant(bal >= 0)
         Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
-        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
-        Invariant(Implies(bal >= 1,
-                          close_off(ToSeq(region), 1, prev0)
-                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
-        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
+        # Termination: `i` rises by exactly 1 on every pass that reaches the
+        # loop head again (the early `break` only exits sooner) and
+        # `len(region)` is fixed, so `len(region) - i + 1` strictly decreases
+        # and is >= 2 at every loop head, where `i < len(region)` holds.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
+        # PRE-PATCH (buggy): the depth==0 test is at the TOP of the loop body,
+        # before the current character is processed. The depth only reaches
+        # zero after the closing parenthesis has been read, so detection is
+        # deferred to the NEXT iteration; when the closing parenthesis is the
+        # final character of the region that next iteration never runs and the
+        # span is never recorded.
+        if bal == 0:
+            res = i
+            break
         val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
         nb = step_bal(val, prev, bal)
         prev = val
         bal = nb
         i = i + 1
-        if bal == 0:
-            res = i
     return res
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,36 +103,32 @@
     prev = prev0
     i = 0
     res = -1
-    while i < len(region) and bal != 0:
+    while i < len(region):
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
         Invariant(bal >= 0)
         Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
-        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
-        Invariant(Implies(bal >= 1,
-                          close_off(ToSeq(region), 1, prev0)
-                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
-        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
+        # Termination: `i` rises by exactly 1 on every pass that reaches the
+        # loop head again (the early `break` only exits sooner) and
+        # `len(region)` is fixed, so `len(region) - i + 1` strictly decreases
+        # and is >= 2 at every loop head, where `i < len(region)` holds.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
+        # PRE-PATCH (buggy): the depth==0 test is at the TOP of the loop body,
+        # before the current character is processed. The depth only reaches
+        # zero after the closing parenthesis has been read, so detection is
+        # deferred to the NEXT iteration; when the closing parenthesis is the
+        # final character of the region that next iteration never runs and the
+        # span is never recorded.
+        if bal == 0:
+            res = i
+            break
         val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
         nb = step_bal(val, prev, bal)
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
-        if bal == 0:
-            res = i
     return res
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -115,24 +115,17 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
         nb = step_bal(val, prev, bal)
         prev = val
         bal = nb
+        # WRONG: record the close's own offset, not one past it (pre-patch
+        # `end + idx` index arithmetic kept while the check was moved down).
+        if nb == 0:
+            res = i
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
-        if bal == 0:
-            res = i
     return res
     # impl-end
 
@@ -168,21 +161,16 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
         nb = step_bal(val, prev, bal)
         prev = val
         bal = nb
+        # WRONG: record the close's own offset, not one past it (pre-patch
+        # `end + idx` index arithmetic kept while the check was moved down).
+        if nb == 0:
+            res = i
         i = i + 1
-        if bal == 0:
-            res = i
     return res
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -115,11 +115,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -129,9 +124,9 @@
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
-        if bal == 0:
+        # WRONG (boundary): only record when a character FOLLOWS the close,
+        # i.e. the exact input class the issue is about is dropped.
+        if bal == 0 and i < len(region):
             res = i
     return res
     # impl-end
@@ -168,11 +163,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -182,7 +172,9 @@
         prev = val
         bal = nb
         i = i + 1
-        if bal == 0:
+        # WRONG (boundary): only record when a character FOLLOWS the close,
+        # i.e. the exact input class the issue is about is dropped.
+        if bal == 0 and i < len(region):
             res = i
     return res
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,34 +103,20 @@
     prev = prev0
     i = 0
     res = -1
-    while i < len(region) and bal != 0:
+    while i < len(region):
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
-        Invariant(bal >= 0)
         Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
-        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
-        Invariant(Implies(bal >= 1,
-                          close_off(ToSeq(region), 1, prev0)
-                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
-        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
         nb = step_bal(val, prev, bal)
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
+        # WRONG (no early exit): keeps scanning past the matching close and
+        # overwrites res on every later return-to-zero -> reports the LAST one.
         if bal == 0:
             res = i
     return res
@@ -156,32 +142,20 @@
     prev = prev0
     i = 0
     res = -1
-    while i < len(region) and bal != 0:
+    while i < len(region):
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
-        Invariant(bal >= 0)
         Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
-        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
-        Invariant(Implies(bal >= 1,
-                          close_off(ToSeq(region), 1, prev0)
-                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
-        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
         nb = step_bal(val, prev, bal)
         prev = val
         bal = nb
         i = i + 1
+        # WRONG (no early exit): keeps scanning past the matching close and
+        # overwrites res on every later return-to-zero -> reports the LAST one.
         if bal == 0:
             res = i
     return res
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -102,24 +102,19 @@
     bal = 1
     prev = prev0
     i = 0
-    res = -1
+    res = 0
     while i < len(region) and bal != 0:
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
         Invariant(bal >= 0)
         Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
+        Invariant(Implies(bal >= 1, res == 0))
         Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
         Invariant(Implies(bal >= 1,
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -129,8 +124,6 @@
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
         if bal == 0:
             res = i
     return res
@@ -155,24 +148,19 @@
     bal = 1
     prev = prev0
     i = 0
-    res = -1
+    res = 0
     while i < len(region) and bal != 0:
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
         Invariant(bal >= 0)
         Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
+        Invariant(Implies(bal >= 1, res == 0))
         Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
         Invariant(Implies(bal >= 1,
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -115,11 +115,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -129,10 +124,12 @@
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
         if bal == 0:
             res = i
+        # PARTIAL-DOMAIN: unreachable under the precondition
+        # (close_off < len(region)), so the verifier never constrains it.
+    if res == -1:
+        res = len(region)
     return res
     # impl-end
 
@@ -168,11 +165,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -184,5 +176,9 @@
         i = i + 1
         if bal == 0:
             res = i
+        # PARTIAL-DOMAIN: unreachable under the precondition
+        # (close_off < len(region)), so the verifier never constrains it.
+    if res == -1:
+        res = len(region)
     return res
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -99,40 +99,8 @@
     Ensures(1 <= Result() and Result() <= len(region))
     # post-conditions-end
     # impl-start
-    bal = 1
-    prev = prev0
-    i = 0
-    res = -1
-    while i < len(region) and bal != 0:
-        # invariants-start
-        Invariant(Acc(list_pred(region), 1 / 2))
-        Invariant(0 <= i and i <= len(region))
-        Invariant(bal >= 0)
-        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
-        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
-        Invariant(Implies(bal >= 1,
-                          close_off(ToSeq(region), 1, prev0)
-                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
-        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(region) - i + 1))
-        # invariants-end
-        val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
-        nb = step_bal(val, prev, bal)
-        prev = val
-        bal = nb
-        i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
-        if bal == 0:
-            res = i
+    # ORACLE ECHO: returns the postcondition's own expression, doing no scan.
+    res = close_off(ToSeq(region), 1, prev0) + 1
     return res
     # impl-end
 
@@ -152,37 +120,7 @@
     Ensures(1 <= Result() and Result() <= len(region))
     # post-conditions-end
     # impl-start
-    bal = 1
-    prev = prev0
-    i = 0
-    res = -1
-    while i < len(region) and bal != 0:
-        # invariants-start
-        Invariant(Acc(list_pred(region), 1 / 2))
-        Invariant(0 <= i and i <= len(region))
-        Invariant(bal >= 0)
-        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
-        Invariant(Implies(bal >= 1, res == -1))
-        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
-        Invariant(Implies(bal >= 1,
-                          close_off(ToSeq(region), 1, prev0)
-                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
-        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(region) - i + 1))
-        # invariants-end
-        val = region[i]
-        Assert(ToSeq(region).drop(i)[0] == val)
-        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
-        nb = step_bal(val, prev, bal)
-        prev = val
-        bal = nb
-        i = i + 1
-        if bal == 0:
-            res = i
+    # ORACLE ECHO: returns the postcondition's own expression, doing no scan.
+    res = close_off(ToSeq(region), 1, prev0) + 1
     return res
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -103,7 +103,7 @@
     prev = prev0
     i = 0
     res = -1
-    while i < len(region) and bal != 0:
+    while i < len(region) and res == -1:
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
@@ -115,11 +115,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -129,8 +124,6 @@
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
         if bal == 0:
             res = i
     return res
@@ -156,7 +149,7 @@
     prev = prev0
     i = 0
     res = -1
-    while i < len(region) and bal != 0:
+    while i < len(region) and res == -1:
         # invariants-start
         Invariant(Acc(list_pred(region), 1 / 2))
         Invariant(0 <= i and i <= len(region))
@@ -168,11 +161,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -115,11 +115,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -129,10 +124,14 @@
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
         if bal == 0:
             res = i
+    # PARTIAL-DOMAIN DIVERGENCE: unreachable under the precondition, so the
+    # obligation below is discharged vacuously by the verifier.
+    while res == -1:
+        Invariant(Acc(list_pred(region), 1 / 2))
+        Invariant(res == -1)
+        i = i + 1
     return res
     # impl-end
 
@@ -168,11 +167,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -184,5 +178,11 @@
         i = i + 1
         if bal == 0:
             res = i
+    # PARTIAL-DOMAIN DIVERGENCE: unreachable under the precondition, so the
+    # obligation below is discharged vacuously by the verifier.
+    while res == -1:
+        Invariant(Acc(list_pred(region), 1 / 2))
+        Invariant(res == -1)
+        i = i + 1
     return res
     # impl-end
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -115,11 +115,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -129,10 +124,12 @@
         prev = val
         bal = nb
         i = i + 1
-        # Record as soon as the depth returns to zero -- after processing the
-        # closing parenthesis -- so a group ending the region is still caught.
         if bal == 0:
             res = i
+    if res == -1:
+        # PARTIAL-DOMAIN: unreachable under the precondition. Refined as an
+        # out-of-range index access in the real code.
+        res = 2 * len(region) + 7
     return res
     # impl-end
 
@@ -168,11 +165,6 @@
                           close_off(ToSeq(region), 1, prev0)
                           == i + close_off(ToSeq(region).drop(i), bal, prev)))
         Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
-        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
-        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
-        # (region is only read), so `len(region) - i + 1` strictly decreases and
-        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
-        # make the loop exit sooner, so it cannot invalidate the bound.
         Invariant(MustTerminate(len(region) - i + 1))
         # invariants-end
         val = region[i]
@@ -184,5 +176,9 @@
         i = i + 1
         if bal == 0:
             res = i
+    if res == -1:
+        # PARTIAL-DOMAIN: unreachable under the precondition. Refined as an
+        # out-of-range index access in the real code.
+        res = 2 * len(region) + 7
     return res
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11728.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A capture group inside a URL/route pattern is delimited by a run of
  parentheses: it opens with a `(` (already consumed before the scan begins,
  so the scan starts already one level deep) and closes at the *matching*
  closing parenthesis. Nesting is honoured -- an unescaped `(` opens a deeper
  level, an unescaped `)` closes one; a parenthesis immediately preceded by a
  backslash is escaped and does not change the nesting depth. The end of the
  group is the position of the parenthesis that returns the depth to zero.

  The desired behaviour, derived from the problem statement (a group that ends
  at the very end of the pattern -- with no trailing `/` or `$` -- must still be
  recognised and have its span determined), is:

    The captured span of a group extends through and INCLUDING its matching
    closing parenthesis, whether or not any further characters follow it. In
    particular, when the matching closing parenthesis is the final character of
    the scanned region, the span must still be reported (it must not require a
    trailing character to be detected).

  Concretely, scanning the region that begins immediately inside the opening
  parenthesis, the matching close lies at offset `k` (the first position whose
  arrival drives the depth to zero); the captured span end -- relative to the
  start of that scanned region -- is `k + 1`, i.e. one past the matching close,
  for every group whose matching close exists in the region (including when it
  is the last character).

The pattern is modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the depth-tracking scan is modelled deeply over `PSeq[int]`.
The two routines below differ only in the base offset at which their scan
region begins (a type-refinement binding documented in mapping.md); both report
the same scan-relative span end.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No unchanged opaque callee is consumed by the proof. The depth-tracking scan
#  that determines a group's matching-close position is modelled DEEPLY below
#  over exact code-point arithmetic (close_off / step_bal). The str<->List[int]
#  carrier and the absolute position at which each scan region begins are the
#  type-refinement boundary documented in mapping.md, not axioms.)
# axioms-end

# pure-start
@Pure
def step_bal(c: int, prev: int, bal: int) -> int:
    """The unmatched-open-parenthesis depth after reading code point `c` whose
    predecessor was `prev`, starting from depth `bal`. An unescaped `(` (code
    40, predecessor not the backslash code 92) opens a level; an unescaped `)`
    (code 41) closes one; everything else leaves the depth unchanged."""
    if c == 40 and prev != 92:   # unescaped '('
        return bal + 1
    if c == 41 and prev != 92:   # unescaped ')'
        return bal - 1
    return bal

@Pure
def close_off(s: PSeq[int], bal: int, prev: int) -> int:
    """Offset within `s` of the character whose arrival first drives the
    running depth (starting at `bal`, predecessor `prev`) to zero -- i.e. the
    matching closing parenthesis of the group already open at depth `bal`.
    Front-recursive (a single unfold per scanned character). Total and
    terminating: if the depth never reaches zero within `s` it returns
    `len(s)`."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) == 0:
        return 0
    nb = step_bal(s[0], prev, bal)
    if nb == 0:
        return 0
    return 1 + close_off(s.drop(1), nb, s[0])
# pure-end

def named_group_pattern_end(region: List[int], prev0: int) -> int:
    # pre-conditions-start
    # `region` is the slice beginning immediately inside the group's opening
    # parenthesis (depth already 1); `prev0` is the code point just before it
    # (so escape state is carried in). The group's matching close exists within
    # the region.
    Requires(Acc(list_pred(region), 1 / 2))
    Requires(close_off(ToSeq(region), 1, prev0) < len(region))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(region), 1 / 2))
    # The reported span end (relative to the region start) is one past the
    # matching close -- always, including when the close is the last character.
    Ensures(Result() == close_off(ToSeq(region), 1, prev0) + 1)
    Ensures(1 <= Result() and Result() <= len(region))
    # post-conditions-end
    # impl-start
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        # Record as soon as the depth returns to zero -- after processing the
        # closing parenthesis -- so a group ending the region is still caught.
        if bal == 0:
            res = i
    return res
    # impl-end

def unnamed_group_pattern_end(region: List[int], prev0: int) -> int:
    # pre-conditions-start
    # `region` is the slice beginning immediately inside the unnamed group's
    # opening parenthesis (depth already 1); `prev0` is the preceding code
    # point. The matching close exists within the region.
    Requires(Acc(list_pred(region), 1 / 2))
    Requires(close_off(ToSeq(region), 1, prev0) < len(region))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(region), 1 / 2))
    Ensures(Result() == close_off(ToSeq(region), 1, prev0) + 1)
    Ensures(1 <= Result() and Result() <= len(region))
    # post-conditions-end
    # impl-start
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit of django__django-11728/nagini. VERDICT: SOUND. 11 same-spec wrong-impl attacks built (spec regions byte-identical; all 11 pass `adversary same-spec` AND `variant_scope.unsound_evasions` = admissible, no @ContractOnly/new axiom). 6 rejected by the verifier, 5 verified -> all 5 had their FAITHFUL refined patch materialized and RUN through the official harness; all 5 resolved, so no verify-but-wrong impl exists.

**POSITIVE CONTROL:** pos_control.py (frozen impl verbatim) -> `python -m swebench_unified.adversary weakness nagini django__django-11728 <p>` = CANDIDATE (shares spec AND verifies, 16.8s). Gold control: gold.patch (== benchmark-verified/django__django-11728/patch.diff, byte-identical to the frozen row's patch, confirming refinement.md's "gold patch verbatim" claim) -> run_resolve resolved=True completed=True attempts=1.

### ATTACKS (cmd for each: `python -m swebench_unified.adversary weakness nagini django__django-11728 <path>`):
1. atk_1.py -- PREPATCH BUG REPRODUCED, BOTH sites: depth==0 check at the TOP of the loop body (pre-patch placement, detection deferred one iteration). => exit 2 NOT-A-COUNTEREXAMPLE (verification failed). REJECTED.
2. atk_2.py -- prepatch at the NAMED site only (the bundle's own differential witness #1). => exit 2. REJECTED.
3. atk_3.py -- OFF-BY-ONE: check moved to the bottom but the pre-patch index arithmetic kept (`res = i` before the advance, i.e. Result() == close_off, span EXCLUDES the matching close). => exit 2. REJECTED.
4. atk_4.py -- BOUNDARY: `if bal == 0 and i < len(region)` -- refuses to record when the close is the FINAL character, exactly the input class the issue report is about. => exit 2. REJECTED (this is the key leg: the postcondition pins the answer at the boundary too).
5. atk_5.py -- CONTROL-FLOW-EFFECT: drops the `bal != 0` guard so the scan runs past the matching close and overwrites res on every later return-to-zero, reporting the LAST one instead of the first. => exit 2. REJECTED.
6. atk_6.py -- PARTIAL-DOMAIN: `res = 0` sentinel (never-balanced path returns 0). => exit 0 CANDIDATE (17.6s). Faithful patch atk_6.patch (res init 0, caller adds base offset per mapping.md 2) -> `python do_resolve.py atk_6 atk_6.patch` (harness.run_resolve) = resolved=True completed=True attempts=1 flaky=False. DOES resolve.
7. atk_7.py -- PARTIAL-DOMAIN: `if res == -1: res = len(region)` after the loop. => exit 0 CANDIDATE (17.9s). atk_7.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.
8. atk_8.py -- UNGROUNDED-ORACLE ECHO: impl is literally `res = close_off(ToSeq(region), 1, prev0) + 1` -- returns the postcondition's own expression, performing no scan at all. => exit 0 CANDIDATE (15.1s). Faithful refinement uses close_off's TOTALITY (it returns len(region) when the depth never hits zero), so the never-balanced path yields len(region)+1. atk_8.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.
9. atk_9.py -- CONTROL-FLOW reshape: loop guard `res == -1` instead of `bal != 0`. => exit 0 CANDIDATE (14.5s). atk_9.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.
10. atk_10.py -- VACUOUS/DIVERGENCE probe (the known 'infeasible guard verifies while proving nothing' failure mode): on the provably-unreachable never-balanced path, enters `while res == -1: i = i + 1` (diverges). => exit 2 NOT-A-COUNTEREXAMPLE. REJECTED -- the METHOD-level MustTerminate(2)/MustTerminate(6) plus the loop's MustTerminate measure kills it, so the spec is not vacuous on the unreachable path.
11. atk_11.py -- PARTIAL-DOMAIN, out-of-range: unreachable path returns `2 * len(region) + 7` (would be a wild index in the refinement). => exit 0 CANDIDATE (29.5s). atk_11.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.

WHY NO BREAK IS POSSIBLE HERE (the structural argument the 5 resolves confirm): the postcondition `Result() == close_off(ToSeq(region),1,prev0) + 1` is a total functional pin -- it fixes the return value UNIQUELY for every input satisfying the precondition `close_off(...) < len(region)`. So a verifying impl's ONLY freedom is the out-of-precondition (never-balanced) path. I measured that path's reachability from the real callers: locally, all 5 refinements agree with gold byte-for-byte on the post-test-patch test_simplify_regex table (14 patterns incl. the 4 new F2P trailing-group cases) and on the admindocs urlconf regexes -- because an unbalanced group start cannot occur in a pattern `re` itself compiles, and the P2P/F2P suites only feed compilable regexes. Fuzzing over raw non-compilable strings DOES separate them (atk_6 27,276 / atk_7 26,630 / atk_8 27,155 divergences vs gold in 80k random patterns, e.g. gold '^(|/' -> '/(|/' vs atk_7 '/<var>'), so the attacks are genuinely wrong impls -- they are just wrong only outside the domain the oracle's tests can reach. That is a spec whose domain restriction matches the callee's real reachable domain, not a spec hole.

### A-LEG AUDIT (my mandate; R/I legs left to G-CONF):
- axioms region is EMPTY (only a comment) and `grep -c @ContractOnly model.py` = 0, so refinement.md C's 'no consumed axioms / no A-consumed leg' claim is literally true. meta.json axioms=[] agrees. Nothing is assumed.
- Leg tags in refinement.md: R x1, I x2, I+R x1, A-reference x1, A-reference+R x1, and the B1-B6 row 'R / I / A-reference'. NO kind-3 leg. Every changed-operation leg (A3, A5, A6) is A-reference or I, as required.
- A-reference correspondence INDEPENDENTLY re-derived (aref_check.py): I reimplemented close_off/step_bal exactly as the @Pure defs and the post-patch inner loop byte-for-byte, then compared. 488,280 exhaustive inputs (regions len 0-7 over '()\\aw' x prev0 in '>(\\a)') + 200,000 fuzz (len 1-24 over '()\\a/$w|?P<>+'): 0 mismatches on the scan-relative span end AND 0 domain mismatches (model out-of-domain <=> real never balances). The bundle's own axiom_check.py also re-runs clean (exit 0, 'G-AX OK').
- A5/A6 + mapping.md 2 base-offset bookkeeping END-TO-END (aleg_final.py): model Result() + base offset (`end` named / `start+1` unnamed) vs the gold patch's recorded ABSOLUTE index (`end + idx + 1` / `start + 2 + idx`) over all 48 scan sites of the 14 F2P/P2P patterns: 0 mismatches. The A6 claim 'idx == close_off at the close' holds.
- The one model<->callee gap, independently confirmed and correctly scoped: the real loop inits prev_char = None while the model takes prev0 = the actual preceding code point. Checked per prev0 over 97,656 inputs each: prev0='>' 0 disagreements, prev0='(' 0 disagreements -- and those are the ONLY two values the real callers can pass ('(?P<...>' always ends in '>'; the unnamed scan is preceded by its own '('). prev0='\\' (92) disagrees on 28,849 inputs but is UNREACHABLE for exactly that reason. Matches what the recorded G-PANEL-2 note says, verified here independently rather than taken on trust.

**HOST/EVIDENCE HYGIENE:** every verification and resolve COMPLETED (no timeouts, no crashes, no host-cap inconclusives); each resolve reports completed=True attempts=1 flaky=False, so none of these verdicts is a saturation artifact. Nagini runs were batched 3-at-a-time (JVM+Z3 each); resolves went through harness.run_resolve's own host-wide slot semaphore. Temp git worktree used for `git apply --check` (all 5 patches apply cleanly at base_commit 05457817647368be4b019314fcc655445a5b4c0c) was removed. Artifacts retained in the scratch dir: atk_*.py, atk_*.patch, atk_*.utils.py, atk_*.resolve.json, atk_*.weakness.txt, gold.patch/gold.resolve.json, pos_control.py, aref_check.py, aleg_final.py, differential2.py, local_f2p.py, mkpatches.py.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_11.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11728.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A capture group inside a URL/route pattern is delimited by a run of
  parentheses: it opens with a `(` (already consumed before the scan begins,
  so the scan starts already one level deep) and closes at the *matching*
  closing parenthesis. Nesting is honoured -- an unescaped `(` opens a deeper
  level, an unescaped `)` closes one; a parenthesis immediately preceded by a
  backslash is escaped and does not change the nesting depth. The end of the
  group is the position of the parenthesis that returns the depth to zero.

  The desired behaviour, derived from the problem statement (a group that ends
  at the very end of the pattern -- with no trailing `/` or `$` -- must still be
  recognised and have its span determined), is:

    The captured span of a group extends through and INCLUDING its matching
    closing parenthesis, whether or not any further characters follow it. In
    particular, when the matching closing parenthesis is the final character of
    the scanned region, the span must still be reported (it must not require a
    trailing character to be detected).

  Concretely, scanning the region that begins immediately inside the opening
  parenthesis, the matching close lies at offset `k` (the first position whose
  arrival drives the depth to zero); the captured span end -- relative to the
  start of that scanned region -- is `k + 1`, i.e. one past the matching close,
  for every group whose matching close exists in the region (including when it
  is the last character).

The pattern is modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the depth-tracking scan is modelled deeply over `PSeq[int]`.
The two routines below differ only in the base offset at which their scan
region begins (a type-refinement binding documented in mapping.md); both report
the same scan-relative span end.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No unchanged opaque callee is consumed by the proof. The depth-tracking scan
#  that determines a group's matching-close position is modelled DEEPLY below
#  over exact code-point arithmetic (close_off / step_bal). The str<->List[int]
#  carrier and the absolute position at which each scan region begins are the
#  type-refinement boundary documented in mapping.md, not axioms.)
# axioms-end

# pure-start
@Pure
def step_bal(c: int, prev: int, bal: int) -> int:
    """The unmatched-open-parenthesis depth after reading code point `c` whose
    predecessor was `prev`, starting from depth `bal`. An unescaped `(` (code
    40, predecessor not the backslash code 92) opens a level; an unescaped `)`
    (code 41) closes one; everything else leaves the depth unchanged."""
    if c == 40 and prev != 92:   # unescaped '('
        return bal + 1
    if c == 41 and prev != 92:   # unescaped ')'
        return bal - 1
    return bal

@Pure
def close_off(s: PSeq[int], bal: int, prev: int) -> int:
    """Offset within `s` of the character whose arrival first drives the
    running depth (starting at `bal`, predecessor `prev`) to zero -- i.e. the
    matching closing parenthesis of the group already open at depth `bal`.
    Front-recursive (a single unfold per scanned character). Total and
    terminating: if the depth never reaches zero within `s` it returns
    `len(s)`."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) == 0:
        return 0
    nb = step_bal(s[0], prev, bal)
    if nb == 0:
        return 0
    return 1 + close_off(s.drop(1), nb, s[0])
# pure-end

def named_group_pattern_end(region: List[int], prev0: int) -> int:
    # pre-conditions-start
    # `region` is the slice beginning immediately inside the group's opening
    # parenthesis (depth already 1); `prev0` is the code point just before it
    # (so escape state is carried in). The group's matching close exists within
    # the region.
    Requires(Acc(list_pred(region), 1 / 2))
    Requires(close_off(ToSeq(region), 1, prev0) < len(region))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(region), 1 / 2))
    # The reported span end (relative to the region start) is one past the
    # matching close -- always, including when the close is the last character.
    Ensures(Result() == close_off(ToSeq(region), 1, prev0) + 1)
    Ensures(1 <= Result() and Result() <= len(region))
    # post-conditions-end
    # impl-start
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        # Record as soon as the depth returns to zero -- after processing the
        # closing parenthesis -- so a group ending the region is still caught.
        if bal == 0:
            res = i
    return res
    # impl-end

def unnamed_group_pattern_end(region: List[int], prev0: int) -> int:
    # pre-conditions-start
    # `region` is the slice beginning immediately inside the unnamed group's
    # opening parenthesis (depth already 1); `prev0` is the preceding code
    # point. The matching close exists within the region.
    Requires(Acc(list_pred(region), 1 / 2))
    Requires(close_off(ToSeq(region), 1, prev0) < len(region))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(region), 1 / 2))
    Ensures(Result() == close_off(ToSeq(region), 1, prev0) + 1)
    Ensures(1 <= Result() and Result() <= len(region))
    # post-conditions-end
    # impl-start
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) adversarial audit of django__django-11728/nagini. VERDICT: SOUND. 11 same-spec wrong-impl attacks built (spec regions byte-identical; all 11 pass `adversary same-spec` AND `variant_scope.unsound_evasions` = admissible, no @ContractOnly/new axiom). 6 rejected by the verifier, 5 verified -> all 5 had their FAITHFUL refined patch materialized and RUN through the official harness; all 5 resolved, so no verify-but-wrong impl exists.

**POSITIVE CONTROL:** pos_control.py (frozen impl verbatim) -> `python -m swebench_unified.adversary weakness nagini django__django-11728 <p>` = CANDIDATE (shares spec AND verifies, 16.8s). Gold control: gold.patch (== benchmark-verified/django__django-11728/patch.diff, byte-identical to the frozen row's patch, confirming refinement.md's "gold patch verbatim" claim) -> run_resolve resolved=True completed=True attempts=1.

### ATTACKS (cmd for each: `python -m swebench_unified.adversary weakness nagini django__django-11728 <path>`):
1. atk_1.py -- PREPATCH BUG REPRODUCED, BOTH sites: depth==0 check at the TOP of the loop body (pre-patch placement, detection deferred one iteration). => exit 2 NOT-A-COUNTEREXAMPLE (verification failed). REJECTED.
2. atk_2.py -- prepatch at the NAMED site only (the bundle's own differential witness #1). => exit 2. REJECTED.
3. atk_3.py -- OFF-BY-ONE: check moved to the bottom but the pre-patch index arithmetic kept (`res = i` before the advance, i.e. Result() == close_off, span EXCLUDES the matching close). => exit 2. REJECTED.
4. atk_4.py -- BOUNDARY: `if bal == 0 and i < len(region)` -- refuses to record when the close is the FINAL character, exactly the input class the issue report is about. => exit 2. REJECTED (this is the key leg: the postcondition pins the answer at the boundary too).
5. atk_5.py -- CONTROL-FLOW-EFFECT: drops the `bal != 0` guard so the scan runs past the matching close and overwrites res on every later return-to-zero, reporting the LAST one instead of the first. => exit 2. REJECTED.
6. atk_6.py -- PARTIAL-DOMAIN: `res = 0` sentinel (never-balanced path returns 0). => exit 0 CANDIDATE (17.6s). Faithful patch atk_6.patch (res init 0, caller adds base offset per mapping.md 2) -> `python do_resolve.py atk_6 atk_6.patch` (harness.run_resolve) = resolved=True completed=True attempts=1 flaky=False. DOES resolve.
7. atk_7.py -- PARTIAL-DOMAIN: `if res == -1: res = len(region)` after the loop. => exit 0 CANDIDATE (17.9s). atk_7.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.
8. atk_8.py -- UNGROUNDED-ORACLE ECHO: impl is literally `res = close_off(ToSeq(region), 1, prev0) + 1` -- returns the postcondition's own expression, performing no scan at all. => exit 0 CANDIDATE (15.1s). Faithful refinement uses close_off's TOTALITY (it returns len(region) when the depth never hits zero), so the never-balanced path yields len(region)+1. atk_8.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.
9. atk_9.py -- CONTROL-FLOW reshape: loop guard `res == -1` instead of `bal != 0`. => exit 0 CANDIDATE (14.5s). atk_9.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.
10. atk_10.py -- VACUOUS/DIVERGENCE probe (the known 'infeasible guard verifies while proving nothing' failure mode): on the provably-unreachable never-balanced path, enters `while res == -1: i = i + 1` (diverges). => exit 2 NOT-A-COUNTEREXAMPLE. REJECTED -- the METHOD-level MustTerminate(2)/MustTerminate(6) plus the loop's MustTerminate measure kills it, so the spec is not vacuous on the unreachable path.
11. atk_11.py -- PARTIAL-DOMAIN, out-of-range: unreachable path returns `2 * len(region) + 7` (would be a wild index in the refinement). => exit 0 CANDIDATE (29.5s). atk_11.patch -> run_resolve resolved=True completed=True attempts=1. DOES resolve.

WHY NO BREAK IS POSSIBLE HERE (the structural argument the 5 resolves confirm): the postcondition `Result() == close_off(ToSeq(region),1,prev0) + 1` is a total functional pin -- it fixes the return value UNIQUELY for every input satisfying the precondition `close_off(...) < len(region)`. So a verifying impl's ONLY freedom is the out-of-precondition (never-balanced) path. I measured that path's reachability from the real callers: locally, all 5 refinements agree with gold byte-for-byte on the post-test-patch test_simplify_regex table (14 patterns incl. the 4 new F2P trailing-group cases) and on the admindocs urlconf regexes -- because an unbalanced group start cannot occur in a pattern `re` itself compiles, and the P2P/F2P suites only feed compilable regexes. Fuzzing over raw non-compilable strings DOES separate them (atk_6 27,276 / atk_7 26,630 / atk_8 27,155 divergences vs gold in 80k random patterns, e.g. gold '^(|/' -> '/(|/' vs atk_7 '/<var>'), so the attacks are genuinely wrong impls -- they are just wrong only outside the domain the oracle's tests can reach. That is a spec whose domain restriction matches the callee's real reachable domain, not a spec hole.

### A-LEG AUDIT (my mandate; R/I legs left to G-CONF):
- axioms region is EMPTY (only a comment) and `grep -c @ContractOnly model.py` = 0, so refinement.md C's 'no consumed axioms / no A-consumed leg' claim is literally true. meta.json axioms=[] agrees. Nothing is assumed.
- Leg tags in refinement.md: R x1, I x2, I+R x1, A-reference x1, A-reference+R x1, and the B1-B6 row 'R / I / A-reference'. NO kind-3 leg. Every changed-operation leg (A3, A5, A6) is A-reference or I, as required.
- A-reference correspondence INDEPENDENTLY re-derived (aref_check.py): I reimplemented close_off/step_bal exactly as the @Pure defs and the post-patch inner loop byte-for-byte, then compared. 488,280 exhaustive inputs (regions len 0-7 over '()\\aw' x prev0 in '>(\\a)') + 200,000 fuzz (len 1-24 over '()\\a/$w|?P<>+'): 0 mismatches on the scan-relative span end AND 0 domain mismatches (model out-of-domain <=> real never balances). The bundle's own axiom_check.py also re-runs clean (exit 0, 'G-AX OK').
- A5/A6 + mapping.md 2 base-offset bookkeeping END-TO-END (aleg_final.py): model Result() + base offset (`end` named / `start+1` unnamed) vs the gold patch's recorded ABSOLUTE index (`end + idx + 1` / `start + 2 + idx`) over all 48 scan sites of the 14 F2P/P2P patterns: 0 mismatches. The A6 claim 'idx == close_off at the close' holds.
- The one model<->callee gap, independently confirmed and correctly scoped: the real loop inits prev_char = None while the model takes prev0 = the actual preceding code point. Checked per prev0 over 97,656 inputs each: prev0='>' 0 disagreements, prev0='(' 0 disagreements -- and those are the ONLY two values the real callers can pass ('(?P<...>' always ends in '>'; the unnamed scan is preceded by its own '('). prev0='\\' (92) disagrees on 28,849 inputs but is UNREACHABLE for exactly that reason. Matches what the recorded G-PANEL-2 note says, verified here independently rather than taken on trust.

**HOST/EVIDENCE HYGIENE:** every verification and resolve COMPLETED (no timeouts, no crashes, no host-cap inconclusives); each resolve reports completed=True attempts=1 flaky=False, so none of these verdicts is a saturation artifact. Nagini runs were batched 3-at-a-time (JVM+Z3 each); resolves went through harness.run_resolve's own host-wide slot semaphore. Temp git worktree used for `git apply --check` (all 5 patches apply cleanly at base_commit 05457817647368be4b019314fcc655445a5b4c0c) was removed. Artifacts retained in the scratch dir: atk_*.py, atk_*.patch, atk_*.utils.py, atk_*.resolve.json, atk_*.weakness.txt, gold.patch/gold.resolve.json, pos_control.py, aref_check.py, aleg_final.py, differential2.py, local_f2p.py, mkpatches.py.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the spec is too strong / drifts from real repo behavior, i.e. find an input where the modeled function disagrees with the real callee. RESULT: no such input found across ~35M machine-checked (region, prev0) pairs. Reference used = base_commit 05457817647368be4b019314fcc655445a5b4c0c worktree with patch.diff APPLIED (per instructions), fresh worktree; git apply of the gold patch succeeded cleanly.

**WHAT THE SPEC CLAIMS.** Two contracted functions named_group_pattern_end / unnamed_group_pattern_end, identical spec modulo MustTerminate credit (2 vs 6). Pre: Acc(list_pred,1/2), close_off(ToSeq(region),1,prev0) < len(region), MustTerminate. Post: Result() == close_off(ToSeq(region),1,prev0) + 1 and 1 <= Result() <= len(region). close_off/step_bal are modeled DEEPLY over PSeq[int] (no @ContractOnly axiom; axioms region intentionally empty), so there is no axiom-strength surface to attack -- the whole scan is spelled out and is itself the thing to falsify.

(1) DEEP-MODEL vs REAL SCAN, mapping-instantiated. Transcribed step_bal/close_off exactly and ran them against the byte-for-byte post-patch inner loops (named: pattern[end:], recorded end+idx+1; unnamed: pattern[start+1:], recorded start+2+idx) driven through the real re matchers named_group_matcher=r'\(\?P(<\w+>)' / unnamed_group_matcher=r'\('. Checked three failure directions, not just value equality: (a) VALUE MISMATCH (base+Result() != recorded index), (b) model precondition holds but the real loop records nothing (spec too strong -- claims a span where the repo is silent), (c) the real loop records but the precondition excludes it (spec too narrow to cover real behavior).

Corpus: 24 curated boundary patterns (group ending the string with no trailing / or $, nested, escaped \( \), backslash runs, empty group, bare '(' and ')'), the 4 F2P docstring patterns, exhaustive over '()\\a' to length 9, exhaustive over '()\\?P<>w' to length 6, non-ASCII/astral/combining/NUL embedded in 9 group shapes, targeted backslash-run escape states (0-6 backslashes x 6 tails x 4 prefixes), 14 real Django URLconf patterns, and 700k weighted random patterns. Result: 0 mismatches in every category and every direction.

(2) GENERALIZED prev0 -- the one real refinement risk. The repo initializes prev_char = None; the model carries prev0 = the code point immediately preceding the region. These agree only when prev0 != 92 ('\\'). Rather than assume the mapping's argument, I (i) machine-checked that prev0 == 92 is UNREACHABLE at any named or unnamed site over exhaustive '()\\?P<>w' to length 8 plus 400k fuzz patterns -- 0 occurrences, as expected since '(?P<...>' ends in '>' and the unnamed site's preceding char is literally '(' -- and (ii) dropped the reachability assumption entirely and re-ran the full differential with prev0 quantified over {None,'\\','>','(',')','a'}, INCLUDING the adversarial prev0='\\' the mapping relies on being impossible. 35,354,430 (region, prev0) pairs: 0 divergences. So even off the reachable envelope the spec does not overclaim.

(3) TRANSCRIPTION FIDELITY. My iterative close_off could itself have hidden a divergence, so I also ran model.py's literal front-recursive close_off (1 unfold/char, s.drop(1)) side by side: 0 recursive-vs-iterative divergences over the same 35M pairs. The postcondition's Result() range bound 1 <= Result() <= len(region) is also sound, not vacuous-strong: under the precondition k < len(region), Result() = k+1 lands in [1, len(region)] exactly.

(4) NOT THE PATCH DELTA. I confirmed the spec is pinned to the POST-patch semantics (record after the depth update, span end idx+1), which is the correct reference per instructions -- so the pre-patch top-of-loop placement failing this postcondition on trailing-group inputs is the intended differential, NOT a faithfulness defect. model_prepatch.py / model_prepatch_2.py exist as the per-site witnesses. I did not report that delta as divergence.

(5) CORROBORATION. bash scripts/nagini_verify.sh on a /tmp copy of model.py: 'Verification successful' (18.71s, exit 0) -- the spec is satisfiable, so FAITHFUL is not masking a vacuous contract. adversary same-spec: 'SAME' (exit 0), confirming the spec region I audited is byte-identical to the bundle's. Bundle's own gates independently agree: axiom_check.py exit 0 (G-AX OK, deep model == real post-patch scan on 12 boundary + 7 F2P slices + 40k fuzz, 6 trailing-group discriminating cases), conformance_check.py exit 0 (G-CONF OK, 277,992 patterns, 100,001 Requires-satisfying invocations, 0 disagreements). My sweep is independent of and strictly wider than both.

RESIDUAL RISK (stated, not hidden). The spec covers only the inner depth-scan span computation; re.finditer group-START enumeration and the outer replace/index-rebasing bookkeeping are outside the modeled span (documented in mapping.md sec.4 and left un-axiomatized). A bug living purely in that outer bookkeeping would be invisible to this spec -- but that is a coverage/completeness question for the scope gate, not a faithfulness break, and the patch's two hunks are entirely inside the scanned region the spec does model. No diverging input exists to cite; the faithfulness attack fails and the spec stands.

**ATTACK GOAL:** show the spec is too strong / drifts from real repo behavior, i.e. find an input where the modeled function disagrees with the real callee. RESULT: no such input found across ~35M machine-checked (region, prev0) pairs. Reference used = base_commit 05457817647368be4b019314fcc655445a5b4c0c worktree with patch.diff APPLIED (per instructions), fresh worktree; git apply of the gold patch succeeded cleanly.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** STRICT-MODE JUDGEMENT (no relaxation claimed or inherited). I first checked for the documented-relaxation shape described in my brief: meta.json has NO `relaxed_leakage` key (top keys: axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and there is NO RELAXED_LEAKAGE.md in the bundle; meta.gates['G-LEAK'].mode == 'strict'. So there is no unavoidability argument to re-derive here -- this cell must clear leakage on the ordinary standard, and it does.

### WHAT I MEASURED (my own runs, not the bundle's assertions):

1. Spec view reconstructed independently via swebench_unified.markers.spec_view(model.py, nagini backend) -- both impl regions elide to the placeholder; only module docstring + axioms (empty) + pure (step_bal/close_off) + pre/post-conditions + signatures survive. That projection is the artifact I judged.

2. Mechanical screen re-run by me: swebench_unified.leakage.screen(model.py, nagini, instance['patch'], instance['problem_statement'], instance['test_patch']) -> passed=True, hard_failures=[], warnings=[]. Judged against problem_statement only; hints_text (2222 chars) never consulted.

3. Gold-mechanism term sweep over the spec view -- I read the real gold patch from instance.json and grepped the spec view for all 24 of its distinguishing mechanism tokens. ALL absent: unmatched_open_brackets, prev_char, group_pattern_and_name, group_indices, 'end + idx', 'start + 1 + idx', 'start + 2 + idx', 'idx + 1', enumerate, replace_named_groups, replace_unnamed_groups, admindocs, utils.py, simplify_regexp, simplify_regex, move/moved, 'top of the loop', 'after the update', break, "trailing '/'", entries/, related_field, 'pk>'. The gold edit's actual content -- relocating the `if unmatched_open_brackets == 0:` test from the top of the inner loop to the bottom (after the depth update + prev_char assignment) and bumping the recorded index by one -- is nowhere disclosed. The spec states WHAT (span end == close_off+1, reportable when the close is the region's last char), never HOW.

4. FACET DERIVABILITY re-derived from the PUBLIC problem_statement alone, empirically on the PRE-patch worktree at base_commit 0545781764 (). The statement gives the failing input r'entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)' and says the trailing-'/' workaround fixes it. I executed pre-patch replace_named_groups on both:
   - without '/': 'entries/<pk>/relationships/(?P<related_field>\w+)'  (final group unreplaced -- the reported symptom)
   - with '/':    'entries/<pk>/relationships/<related_field>/'        (works -- the stated workaround)
   The working case replaces '(?P<pk>[^/.]+)' entirely, i.e. the span the code substitutes ALREADY INCLUDES the closing ')'. So both halves of the spec's behavioral facet -- (a) the span is inclusive of the matching close, (b) it must still be reported when that close is the final character -- are directly observable consequences of the two lines the public statement itself supplies. This is a restatement of the disclosed symptom, not added information.

5. LOAD-BEARING TEST (the one my brief prescribes). I mechanically stripped the module docstring, every non-marker comment, and both pure-function docstrings, then spliced the PRE-patch impl bodies into that prose-free spec. Result: `Verification failed -- Postcondition of named_group_pattern_end might not hold. Assertion (Result() == (close_off(ToSeq(region), 1, prev0) + 1)) might not hold.` The discrimination is carried entirely by the FORMAL postcondition, not by any narration. Control: the prose-free spec with the gold impl still verifies (Verification successful, 16.65s). So no prose clause is doing hidden work, and there is no narrative sentence whose removal would break the spec -- the inverse of the leakage pattern.

6. Core gates my verdict leans on, re-run by me rather than read off meta.json:
   - bash scripts/nagini_verify.sh model.py -> 'Verification successful' (20.66s, exit 0).
   - adversary same-spec on model_prepatch.py and model_prepatch_2.py -> both 'SAME -- attack shares the bundle's exact specification' (exit 0), so the differential really holds the spec fixed and varies only the impl region.
   - adversary weakness on both -> 'NOT-A-COUNTEREXAMPLE: attack does not verify' for each: the spec rejects both pre-patch impls, at the named site and independently at the unnamed site.
   - python axiom_check.py -> exit 0 (deep close_off/step_bal == real post-patch scan on 12 boundary + 7 F2P slices + 40000 fuzz; 6 trailing-group discriminators recorded post-patch, dropped pre-patch).
   - python conformance_check.py -> exit 0 (277992 patterns, 100001 in-domain invocations, 0 disagreements, seed 11728).
   No gate my disposition rests on is unsound.

7. **THE ONE INCREMENTAL-DISCLOSURE QUESTION I CHASED.** `replace_unnamed_groups` is a gold-changed symbol that is NOT in the problem_statement (only `replace_named_groups` is), yet the spec view carries a second contracted function `unnamed_group_pattern_end` for that site. I checked whether that constitutes spec-view leakage and concluded it does not: the two-site scope is already disclosed to the consumer through the SEPARATE, deliberate localization channel (MODES_WITH_LOCALIZATION = {0,1,2,100} in eval/dataset.py), which hands the agent meta.modeled_functions verbatim -- including 'django.contrib.admindocs.utils.replace_unnamed_groups (inner depth-scan loop)' at 'utils.py:190 (loop body 201-214)'. That channel exists precisely to isolate where-to-edit from how/verification, and it is available in the from-scratch modes too, so the spec view adds no scope information the consumer lacks. Within the spec view itself the word 'unnamed' names a public regex-domain concept (an unnamed capture group), not the patched callee; the identifier does not embed the repo symbol (mechanically: 'replace_unnamed_groups' is not a substring of 'unnamed_group_pattern_end'). Facet re-confirmed: inclusive-span / report-at-end-of-region, at two structurally identical scan sites.

BUNDLE-ADDRESSES-THE-REVIEWER CHECK (reported as a finding in its own right per my brief): I ran swebench_unified.leakage.reviewer_directed over EVERY file in the bundle -- model.py, model_prepatch.py, model_prepatch_2.py, mapping.md, refinement.md, verdict.md, meta.json, axiom_check.py, conformance_check.py, properties.py, pbt_result.json -- and all returned [] (clean; no addresses-the-reviewer, prescribes-the-verdict, or recording-convention hit). Nothing in the bundle instructs me how to record or which verdict is honest.

One item worth recording as context though it breaks no rule: verdict.md carries a pre-existing 'Role 4 -- G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)' section, i.e. a prior agent's verdict for exactly my role, reconstructed by scripts/backfill_verdict_md.py from meta.json. That is an anchoring surface, not an instruction, and I did NOT inherit it -- every fact above is my own re-measurement (my independent screen re-run, my own pre/post-patch execution on the worktree, my own prose-strip splice, my own gate re-runs).

I note also that refinement.md and mapping.md DO spell out the gold edit's mechanics in full ('delete the check from the top... add it at the bottom', 'end + idx -> end + idx + 1'); that is correct and expected for those documents, and it is not a leak because they are NOT consumer-visible -- eval/dataset.py exposes only spec_view, localization, changed_files, modeled_functions, and float_encoding, never refinement.md/mapping.md, and WITHHELD_FIELDS/assert_no_leak keep patch and tests out of the agent view.

**CONCLUSION:** the spec view discloses exactly one behavioral facet -- a capture group's span runs through and including its matching close, and must be reported even when that close ends the scanned region -- which I demonstrated is derivable from the public problem_statement alone by running the pre-patch code on the statement's own example and its own stated workaround. No gold-diff line, no diff marker, no patched path or module, no patched symbol in any identifier or comment, no bug/fix narration, and no prose clause that is load-bearing for the differential. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
