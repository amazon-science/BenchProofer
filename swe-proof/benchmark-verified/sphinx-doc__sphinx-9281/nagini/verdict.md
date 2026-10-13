# P2 adversarial audit — sphinx-doc__sphinx-9281

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py` |

**Non-vacuity.** The positive control `atk_8.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,64 +164,10 @@
         Assert(i == len(value.category_text))  # type: ignore
         Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
         return result
-    elif value.kind == 3:  # type: ignore
-        i = 0
-        while i < len(value.class_name):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
-            result.append(value.class_name[i])  # type: ignore
-            i = i + 1
-        Assert(i == len(value.class_name))  # type: ignore
-        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
-        j = 0
-        while j < len(value.member_name):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
-            result.append(value.member_name[j])  # type: ignore
-            j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
-        return result
     else:
+        # PRE-PATCH dispatch: there is NO enumerated-type branch, so a member
+        # of an enumerated type (tag 3) falls through to the generic textual
+        # form together with every other value.
         i = 0
         while i < len(value.fallback_text):  # type: ignore
             # invariants-start
@@ -236,7 +182,7 @@
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
+                      value.kind != 2)  # type: ignore
             Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
             # The loop consumes the termination obligation: the remaining
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,7 +141,6 @@
     if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
         i = 0
         while i < len(value.category_text):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -155,10 +154,7 @@
             Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
             Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.category_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.category_text))  # type: ignore
@@ -167,7 +163,6 @@
     elif value.kind == 3:  # type: ignore
         i = 0
         while i < len(value.class_name):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -181,19 +176,12 @@
             Invariant(value.kind == 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
             result.append(value.class_name[i])  # type: ignore
             i = i + 1
-        Assert(i == len(value.class_name))  # type: ignore
-        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
+        Assert(ToSeq(result) == ToSeq(value.class_name))  # type: ignore
         j = 0
         while j < len(value.member_name):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -206,43 +194,29 @@
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind == 3)  # type: ignore
             Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
+            Invariant(ToSeq(result) == ToSeq(value.class_name) + ToSeq(value.member_name).take(j))  # type: ignore
             Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
             result.append(value.member_name[j])  # type: ignore
             j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
+        Assert(ToSeq(result) == ToSeq(value.class_name) + ToSeq(value.member_name))  # type: ignore
         return result
     else:
         i = 0
         while i < len(value.fallback_text):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
+            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
+            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
+            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(result)))
+            Invariant(value.kind != 0 and value.kind != 1 and value.kind != 2 and value.kind != 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.fallback_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.fallback_text))  # type: ignore
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,7 +141,6 @@
     if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
         i = 0
         while i < len(value.category_text):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -155,10 +154,7 @@
             Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
             Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.category_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.category_text))  # type: ignore
@@ -167,7 +163,6 @@
     elif value.kind == 3:  # type: ignore
         i = 0
         while i < len(value.class_name):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -181,19 +176,15 @@
             Invariant(value.kind == 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
             result.append(value.class_name[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.class_name))  # type: ignore
         Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
-        j = 0
-        while j < len(value.member_name):  # type: ignore
-            # invariants-start
+        return result
+    else:
+        i = 0
+        while i < len(value.fallback_text):  # type: ignore
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -204,45 +195,10 @@
             Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
-            Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
-            result.append(value.member_name[j])  # type: ignore
-            j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
-        return result
-    else:
-        i = 0
-        while i < len(value.fallback_text):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
+            Invariant(value.kind != 0 and value.kind != 1 and value.kind != 2 and value.kind != 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.fallback_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.fallback_text))  # type: ignore
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,7 +141,6 @@
     if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
         i = 0
         while i < len(value.category_text):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -155,19 +154,14 @@
             Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
             Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.category_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.category_text))  # type: ignore
         Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
         return result
     elif value.kind == 3:  # type: ignore
-        i = 0
-        while i < len(value.class_name):  # type: ignore
-            # invariants-start
+        while True:
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -179,21 +173,11 @@
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
-            result.append(value.class_name[i])  # type: ignore
-            i = i + 1
-        Assert(i == len(value.class_name))  # type: ignore
-        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
-        j = 0
-        while j < len(value.member_name):  # type: ignore
-            # invariants-start
+            result = result
+        return result
+    else:
+        i = 0
+        while i < len(value.fallback_text):  # type: ignore
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -204,45 +188,10 @@
             Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
-            Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
-            result.append(value.member_name[j])  # type: ignore
-            j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
-        return result
-    else:
-        i = 0
-        while i < len(value.fallback_text):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
+            Invariant(value.kind != 0 and value.kind != 1 and value.kind != 2 and value.kind != 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.fallback_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.fallback_text))  # type: ignore
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -140,8 +140,7 @@
     result = []  # type: List[int]
     if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
         i = 0
-        while i < len(value.category_text):  # type: ignore
-            # invariants-start
+        while i < len(value.fallback_text):  # type: ignore
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -153,21 +152,17 @@
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
-            Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
-            # invariants-end
-            result.append(value.category_text[i])  # type: ignore
+            Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
+            Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
+            Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
+            result.append(value.fallback_text[i])  # type: ignore
             i = i + 1
-        Assert(i == len(value.category_text))  # type: ignore
-        Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
+        Assert(i == len(value.fallback_text))  # type: ignore
+        Assert(ToSeq(value.fallback_text).take(i) == ToSeq(value.fallback_text))  # type: ignore
         return result
     elif value.kind == 3:  # type: ignore
         i = 0
         while i < len(value.class_name):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -181,19 +176,12 @@
             Invariant(value.kind == 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
             result.append(value.class_name[i])  # type: ignore
             i = i + 1
-        Assert(i == len(value.class_name))  # type: ignore
-        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
+        result.append(46)
         j = 0
         while j < len(value.member_name):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -206,43 +194,29 @@
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind == 3)  # type: ignore
             Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
+            Invariant(ToSeq(result) == ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
             Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
             result.append(value.member_name[j])  # type: ignore
             j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
+        Assert(ToSeq(result) == enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
         return result
     else:
         i = 0
         while i < len(value.fallback_text):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
+            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
+            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
+            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(result)))
+            Invariant(value.kind != 0 and value.kind != 1 and value.kind != 2 and value.kind != 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.fallback_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.fallback_text))  # type: ignore
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,7 +141,6 @@
     if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
         i = 0
         while i < len(value.category_text):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -155,10 +154,7 @@
             Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
             Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.category_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.category_text))  # type: ignore
@@ -166,8 +162,7 @@
         return result
     elif value.kind == 3:  # type: ignore
         i = 0
-        while i < len(value.class_name):  # type: ignore
-            # invariants-start
+        while i < len(value.member_name):  # type: ignore
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -179,21 +174,14 @@
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
-            result.append(value.class_name[i])  # type: ignore
+            Invariant(0 <= i and i <= len(value.member_name))  # type: ignore
+            Invariant(ToSeq(result) == ToSeq(value.member_name).take(i))  # type: ignore
+            Invariant(MustTerminate(len(value.member_name) - i))  # type: ignore
+            result.append(value.member_name[i])  # type: ignore
             i = i + 1
-        Assert(i == len(value.class_name))  # type: ignore
-        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
+        result.append(46)
         j = 0
-        while j < len(value.member_name):  # type: ignore
-            # invariants-start
+        while j < len(value.class_name):  # type: ignore
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -205,44 +193,30 @@
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
-            result.append(value.member_name[j])  # type: ignore
+            Invariant(0 <= j and j <= len(value.class_name))  # type: ignore
+            Invariant(ToSeq(result) == ToSeq(value.member_name) + dot() + ToSeq(value.class_name).take(j))  # type: ignore
+            Invariant(MustTerminate(len(value.class_name) - j))  # type: ignore
+            result.append(value.class_name[j])  # type: ignore
             j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
+        Assert(ToSeq(result) == ToSeq(value.member_name) + dot() + ToSeq(value.class_name))  # type: ignore
         return result
     else:
         i = 0
         while i < len(value.fallback_text):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
+            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
+            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
+            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(result)))
+            Invariant(value.kind != 0 and value.kind != 1 and value.kind != 2 and value.kind != 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.fallback_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.fallback_text))  # type: ignore
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,10 +138,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
-        i = 0
-        while i < len(value.category_text):  # type: ignore
-            # invariants-start
+    while True:
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -152,100 +149,6 @@
             Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
             Invariant(Acc(list_pred(result)))
-            Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
-            Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
-            # invariants-end
-            result.append(value.category_text[i])  # type: ignore
-            i = i + 1
-        Assert(i == len(value.category_text))  # type: ignore
-        Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
-        return result
-    elif value.kind == 3:  # type: ignore
-        i = 0
-        while i < len(value.class_name):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
-            result.append(value.class_name[i])  # type: ignore
-            i = i + 1
-        Assert(i == len(value.class_name))  # type: ignore
-        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
-        j = 0
-        while j < len(value.member_name):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind == 3)  # type: ignore
-            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
-            result.append(value.member_name[j])  # type: ignore
-            j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
-        return result
-    else:
-        i = 0
-        while i < len(value.fallback_text):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
-            Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
-            # invariants-end
-            result.append(value.fallback_text[i])  # type: ignore
-            i = i + 1
-        Assert(i == len(value.fallback_text))  # type: ignore
-        Assert(ToSeq(value.fallback_text).take(i) == ToSeq(value.fallback_text))  # type: ignore
-        return result
+        result = result
+    return result
     # impl-end
```

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,7 +141,6 @@
     if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
         i = 0
         while i < len(value.category_text):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -155,10 +154,7 @@
             Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
             Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
-            # invariants-end
             result.append(value.category_text[i])  # type: ignore
             i = i + 1
         Assert(i == len(value.category_text))  # type: ignore
@@ -167,7 +163,6 @@
     elif value.kind == 3:  # type: ignore
         i = 0
         while i < len(value.class_name):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -181,19 +176,12 @@
             Invariant(value.kind == 3)  # type: ignore
             Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
             Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
-            # invariants-end
             result.append(value.class_name[i])  # type: ignore
             i = i + 1
-        Assert(i == len(value.class_name))  # type: ignore
-        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
-        result.append(46)  # '.'
-        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
+        result.append(46)
         j = 0
         while j < len(value.member_name):  # type: ignore
-            # invariants-start
             Invariant(Acc(value.kind, 1 / 2))  # type: ignore
             Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
             Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
@@ -206,46 +194,32 @@
             Invariant(Acc(list_pred(result)))
             Invariant(value.kind == 3)  # type: ignore
             Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
-            Invariant(ToSeq(result) ==
-                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
+            Invariant(ToSeq(result) == ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
             Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
-            # invariants-end
             result.append(value.member_name[j])  # type: ignore
             j = j + 1
-        Assert(j == len(value.member_name))  # type: ignore
-        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
-        Assert(ToSeq(result) ==
-               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
+        Assert(ToSeq(result) == enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
         return result
     else:
         i = 0
-        while i < len(value.fallback_text):  # type: ignore
-            # invariants-start
-            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
-            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
-            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
-            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
-            Invariant(Acc(list_pred(result)))
-            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
-                      value.kind != 2 and value.kind != 3)  # type: ignore
-            Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
-            Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
-            # The loop consumes the termination obligation: the remaining
-            # count is the strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
-            # invariants-end
-            result.append(value.fallback_text[i])  # type: ignore
+        while i < len(value.category_text):  # type: ignore
+            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
+            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
+            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
+            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
+            Invariant(Acc(list_pred(result)))
+            Invariant(value.kind != 0 and value.kind != 1 and value.kind != 2 and value.kind != 3)  # type: ignore
+            Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
+            Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
+            Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
+            result.append(value.category_text[i])  # type: ignore
             i = i + 1
-        Assert(i == len(value.fallback_text))  # type: ignore
-        Assert(ToSeq(value.fallback_text).take(i) == ToSeq(value.fallback_text))  # type: ignore
+        Assert(i == len(value.category_text))  # type: ignore
+        Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
         return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9281.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single routine produces a human-readable textual description of an
  arbitrary value, dispatching on the value's category:

    * a key/value mapping, an unordered collection, and an immutable
      unordered collection each have their own established rendering;
    * a member of an enumerated type is rendered as its owning type's name,
      a single dot, then the member's own name -- e.g. the member ``FOO`` of
      enumerated type ``MyEnum`` renders as the code points of ``MyEnum.FOO``
      -- so the rendering is a stable, re-usable reference to the member
      rather than the value-revealing fallback text;
    * every other value falls back to its generic textual form.

  The categories are mutually exclusive: at most one rendering rule applies,
  and a value that is a member of an enumerated type takes the enumerated-type
  rule, never the generic fallback.

Values are modelled as a minimal object carrying a category tag plus the
relevant text fragments as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing). The category tag is an integer:

    0 = mapping, 1 = collection, 2 = immutable collection,
    3 = enumerated-type member, 4 = any other value.

The owning-type name and the member name are the two fragments the
enumerated-type rendering composes; the renderings of the other categories and
the generic fallback are carried as opaque code-point sequences, since those
rules are unchanged by this behaviour. The pure sequence theory ``PSeq[int]``
carries the specification.

Producing the description is a bounded computation over the finitely many code
points of the relevant fragments: it MUST terminate and return its rendered
text (a total-correctness obligation, carried as MustTerminate in the
precondition). An implementation that diverges before returning would satisfy
the value postconditions only vacuously and would never deliver the rendering.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Value:
    def __init__(self, kind: int, class_name: List[int], member_name: List[int],
                 category_text: List[int], fallback_text: List[int]) -> None:
        Requires(Acc(list_pred(class_name), 1 / 2))
        Requires(Acc(list_pred(member_name), 1 / 2))
        Requires(Acc(list_pred(category_text), 1 / 2))
        Requires(Acc(list_pred(fallback_text), 1 / 2))
        Ensures(Acc(self.kind) and self.kind == kind)  # type: ignore
        Ensures(Acc(self.class_name) and self.class_name is class_name)  # type: ignore
        Ensures(Acc(self.member_name) and self.member_name is member_name)  # type: ignore
        Ensures(Acc(self.category_text) and self.category_text is category_text)  # type: ignore
        Ensures(Acc(self.fallback_text) and self.fallback_text is fallback_text)  # type: ignore
        Ensures(Acc(list_pred(class_name), 1 / 2))
        Ensures(Acc(list_pred(member_name), 1 / 2))
        Ensures(Acc(list_pred(category_text), 1 / 2))
        Ensures(Acc(list_pred(fallback_text), 1 / 2))
        self.kind = kind
        self.class_name = class_name
        self.member_name = member_name
        self.category_text = category_text
        self.fallback_text = fallback_text


# axioms-start
# (no consumed @ContractOnly axioms: the renderings of the unchanged
# categories and the generic fallback are carried as opaque sequences on the
# value object; the enumerated-type composition is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def dot() -> PSeq[int]:
    # the single separator code point U+002E '.'
    return PSeq(46)


@Pure
def enum_rendering(class_name: PSeq[int], member_name: PSeq[int]) -> PSeq[int]:
    """The rendering of an enumerated-type member: the owning type's name, a
    dot, then the member's name."""
    return class_name + dot() + member_name
# pure-end


def describe(value: Value) -> List[int]:
    # pre-conditions-start
    Requires(Acc(value.kind, 1 / 2))  # type: ignore
    Requires(Acc(value.class_name, 1 / 2))  # type: ignore
    Requires(Acc(value.member_name, 1 / 2))  # type: ignore
    Requires(Acc(value.category_text, 1 / 2))  # type: ignore
    Requires(Acc(value.fallback_text, 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
    # TERMINATION: the rendering must actually ANSWER — copying/composing the
    # finitely many code points of the relevant fragments is a bounded
    # computation. Nagini is a partial-correctness verifier by default, so
    # without this obligation a non-terminating implementation (an endless
    # loop before the return) satisfies every value postcondition vacuously
    # while sharing the spec; the real routine always returns its rendered
    # text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(value.kind, 1 / 2))  # type: ignore
    Ensures(Acc(value.class_name, 1 / 2))  # type: ignore
    Ensures(Acc(value.member_name, 1 / 2))  # type: ignore
    Ensures(Acc(value.category_text, 1 / 2))  # type: ignore
    Ensures(Acc(value.fallback_text, 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(Result())))
    # A member of an enumerated type (tag 3) is rendered as
    # owning-type-name "." member-name, NOT by the generic fallback rendering.
    Ensures(Implies(value.kind == 3,  # type: ignore
                    ToSeq(Result()) == enum_rendering(ToSeq(value.class_name),  # type: ignore
                                                      ToSeq(value.member_name))))  # type: ignore
    # The three established collection-style renderings (tags 0/1/2) are unchanged.
    Ensures(Implies(value.kind == 0,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    Ensures(Implies(value.kind == 1,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    Ensures(Implies(value.kind == 2,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    # Any other value (tag 4) falls back to its generic textual form.
    Ensures(Implies(value.kind == 4,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.fallback_text)))  # type: ignore
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
        i = 0
        while i < len(value.category_text):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
            Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
            # invariants-end
            result.append(value.category_text[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.category_text))  # type: ignore
        Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
        return result
    elif value.kind == 3:  # type: ignore
        i = 0
        while i < len(value.class_name):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind == 3)  # type: ignore
            Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
            # invariants-end
            result.append(value.class_name[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.class_name))  # type: ignore
        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
        result.append(46)  # '.'
        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
        j = 0
        while j < len(value.member_name):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind == 3)  # type: ignore
            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
            Invariant(ToSeq(result) ==
                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
            # invariants-end
            result.append(value.member_name[j])  # type: ignore
            j = j + 1
        Assert(j == len(value.member_name))  # type: ignore
        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
        Assert(ToSeq(result) ==
               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
        Assert(ToSeq(result) ==
               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
        return result
    else:
        i = 0
        while i < len(value.fallback_text):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
                      value.kind != 2 and value.kind != 3)  # type: ignore
            Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
            # invariants-end
            result.append(value.fallback_text[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.fallback_text))  # type: ignore
        Assert(ToSeq(value.fallback_text).take(i) == ToSeq(value.fallback_text))  # type: ignore
        return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is fully functionally-pinned: every reachable kind is pinned to an exact PSeq equality (0/1/2 -> ToSeq(category_text), 3 -> enum_rendering(class_name,member_name)=class_name++[46]++member_name, 4 -> ToSeq(fallback_text)), and Requires(MustTerminate(2)) closes the vacuous-divergence escape (Nagini is partial-correctness by default). All spec/pure/axiom regions left byte-identical in every attack (same-spec exit 0 for all 9).

Protocol run from project root with PY=python; weakness commands run concurrently in 3 batches of 3 (each a JVM+Z3):
  python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9281 <atk>

Attack results (all same-spec exit 0):
  atk_1 (prepatch bug: kind==3 falls to fallback; == model_prepatch.py) -> NOT-A-COUNTEREXAMPLE, verification failed (G-DIFF: spec senses the change). prepatch_reproduced=true.
  atk_2 (enum branch omits the dot: class_name++member_name) -> verification failed (kind==3 postcondition).
  atk_3 (enum truncated: returns class_name only) -> verification failed.
  atk_4 (control-flow-effect: while True: diverge on kind==3) -> verification failed (MustTerminate rejects divergence).
  atk_5 (collection arms 0/1/2 -> fallback_text swap) -> verification failed.
  atk_6 (enum reversed order: member++[46]++class) -> verification failed.
  atk_7 (unconditional divergence: while True before any return) -> verification failed (MustTerminate).
  atk_9 (fallback arm kind==4 -> category_text swap) -> verification failed.

The ONLY verifying impl is atk_8 (CANDIDATE, 18.1s), which is BYTE-IDENTICAL to bundle model.py (diff -q clean) i.e. the correct impl / positive control. Its faithful refined patch is the gold patch.diff verbatim (matches refinement A1 if->elif joins + A3 new enum arm). MANDATORY resolve run executed via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9281', patch, timeout=1800): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved'. So the sole verifying candidate resolves -> no verify-but-wrong impl found.

A-leg audit: axioms region is empty (no A-consumed legs; no kind-3 unexpressible legs). The single changed op (enum rendering) is the A3 A-reference deep model. G-AX: python axiom_check.py -> exit 0, 'enum_rendering deep model (== gold "%s.%s"%(cls.__name__,member.name)) sound on 11 boundary + 5000 randomized Enum classes'. Correspondence holds: "%s.%s"%(a,b)==a+"."+b, member.name is str, dot()==[46]=='.' ; kind tag <-> isinstance dispatch (A1) and unchanged collection/fallback arms carried as opaque sequences (A2/A4) are R/I, covered by G-CONF. refinement.md legs are all R / A-reference / I, no kind-3. verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py` |

**Non-vacuity.** The positive control `atk_8.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9281.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single routine produces a human-readable textual description of an
  arbitrary value, dispatching on the value's category:

    * a key/value mapping, an unordered collection, and an immutable
      unordered collection each have their own established rendering;
    * a member of an enumerated type is rendered as its owning type's name,
      a single dot, then the member's own name -- e.g. the member ``FOO`` of
      enumerated type ``MyEnum`` renders as the code points of ``MyEnum.FOO``
      -- so the rendering is a stable, re-usable reference to the member
      rather than the value-revealing fallback text;
    * every other value falls back to its generic textual form.

  The categories are mutually exclusive: at most one rendering rule applies,
  and a value that is a member of an enumerated type takes the enumerated-type
  rule, never the generic fallback.

Values are modelled as a minimal object carrying a category tag plus the
relevant text fragments as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing). The category tag is an integer:

    0 = mapping, 1 = collection, 2 = immutable collection,
    3 = enumerated-type member, 4 = any other value.

The owning-type name and the member name are the two fragments the
enumerated-type rendering composes; the renderings of the other categories and
the generic fallback are carried as opaque code-point sequences, since those
rules are unchanged by this behaviour. The pure sequence theory ``PSeq[int]``
carries the specification.

Producing the description is a bounded computation over the finitely many code
points of the relevant fragments: it MUST terminate and return its rendered
text (a total-correctness obligation, carried as MustTerminate in the
precondition). An implementation that diverges before returning would satisfy
the value postconditions only vacuously and would never deliver the rendering.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Value:
    def __init__(self, kind: int, class_name: List[int], member_name: List[int],
                 category_text: List[int], fallback_text: List[int]) -> None:
        Requires(Acc(list_pred(class_name), 1 / 2))
        Requires(Acc(list_pred(member_name), 1 / 2))
        Requires(Acc(list_pred(category_text), 1 / 2))
        Requires(Acc(list_pred(fallback_text), 1 / 2))
        Ensures(Acc(self.kind) and self.kind == kind)  # type: ignore
        Ensures(Acc(self.class_name) and self.class_name is class_name)  # type: ignore
        Ensures(Acc(self.member_name) and self.member_name is member_name)  # type: ignore
        Ensures(Acc(self.category_text) and self.category_text is category_text)  # type: ignore
        Ensures(Acc(self.fallback_text) and self.fallback_text is fallback_text)  # type: ignore
        Ensures(Acc(list_pred(class_name), 1 / 2))
        Ensures(Acc(list_pred(member_name), 1 / 2))
        Ensures(Acc(list_pred(category_text), 1 / 2))
        Ensures(Acc(list_pred(fallback_text), 1 / 2))
        self.kind = kind
        self.class_name = class_name
        self.member_name = member_name
        self.category_text = category_text
        self.fallback_text = fallback_text


# axioms-start
# (no consumed @ContractOnly axioms: the renderings of the unchanged
# categories and the generic fallback are carried as opaque sequences on the
# value object; the enumerated-type composition is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def dot() -> PSeq[int]:
    # the single separator code point U+002E '.'
    return PSeq(46)


@Pure
def enum_rendering(class_name: PSeq[int], member_name: PSeq[int]) -> PSeq[int]:
    """The rendering of an enumerated-type member: the owning type's name, a
    dot, then the member's name."""
    return class_name + dot() + member_name
# pure-end


def describe(value: Value) -> List[int]:
    # pre-conditions-start
    Requires(Acc(value.kind, 1 / 2))  # type: ignore
    Requires(Acc(value.class_name, 1 / 2))  # type: ignore
    Requires(Acc(value.member_name, 1 / 2))  # type: ignore
    Requires(Acc(value.category_text, 1 / 2))  # type: ignore
    Requires(Acc(value.fallback_text, 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
    Requires(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
    # TERMINATION: the rendering must actually ANSWER — copying/composing the
    # finitely many code points of the relevant fragments is a bounded
    # computation. Nagini is a partial-correctness verifier by default, so
    # without this obligation a non-terminating implementation (an endless
    # loop before the return) satisfies every value postcondition vacuously
    # while sharing the spec; the real routine always returns its rendered
    # text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(value.kind, 1 / 2))  # type: ignore
    Ensures(Acc(value.class_name, 1 / 2))  # type: ignore
    Ensures(Acc(value.member_name, 1 / 2))  # type: ignore
    Ensures(Acc(value.category_text, 1 / 2))  # type: ignore
    Ensures(Acc(value.fallback_text, 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
    Ensures(Acc(list_pred(Result())))
    # A member of an enumerated type (tag 3) is rendered as
    # owning-type-name "." member-name, NOT by the generic fallback rendering.
    Ensures(Implies(value.kind == 3,  # type: ignore
                    ToSeq(Result()) == enum_rendering(ToSeq(value.class_name),  # type: ignore
                                                      ToSeq(value.member_name))))  # type: ignore
    # The three established collection-style renderings (tags 0/1/2) are unchanged.
    Ensures(Implies(value.kind == 0,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    Ensures(Implies(value.kind == 1,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    Ensures(Implies(value.kind == 2,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.category_text)))  # type: ignore
    # Any other value (tag 4) falls back to its generic textual form.
    Ensures(Implies(value.kind == 4,  # type: ignore
                    ToSeq(Result()) == ToSeq(value.fallback_text)))  # type: ignore
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore
        i = 0
        while i < len(value.category_text):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore
            Invariant(0 <= i and i <= len(value.category_text))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.category_text).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.category_text) - i))  # type: ignore
            # invariants-end
            result.append(value.category_text[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.category_text))  # type: ignore
        Assert(ToSeq(value.category_text).take(i) == ToSeq(value.category_text))  # type: ignore
        return result
    elif value.kind == 3:  # type: ignore
        i = 0
        while i < len(value.class_name):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind == 3)  # type: ignore
            Invariant(0 <= i and i <= len(value.class_name))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore
            # invariants-end
            result.append(value.class_name[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.class_name))  # type: ignore
        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore
        result.append(46)  # '.'
        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore
        j = 0
        while j < len(value.member_name):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind == 3)  # type: ignore
            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore
            Invariant(ToSeq(result) ==
                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore
            # invariants-end
            result.append(value.member_name[j])  # type: ignore
            j = j + 1
        Assert(j == len(value.member_name))  # type: ignore
        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore
        Assert(ToSeq(result) ==
               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore
        Assert(ToSeq(result) ==
               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore
        return result
    else:
        i = 0
        while i < len(value.fallback_text):  # type: ignore
            # invariants-start
            Invariant(Acc(value.kind, 1 / 2))  # type: ignore
            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore
            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore
            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore
            Invariant(Acc(list_pred(result)))
            Invariant(value.kind != 0 and value.kind != 1 and  # type: ignore
                      value.kind != 2 and value.kind != 3)  # type: ignore
            Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore
            Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore
            # The loop consumes the termination obligation: the remaining
            # count is the strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore
            # invariants-end
            result.append(value.fallback_text[i])  # type: ignore
            i = i + 1
        Assert(i == len(value.fallback_text))  # type: ignore
        Assert(ToSeq(value.fallback_text).take(i) == ToSeq(value.fallback_text))  # type: ignore
        return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is fully functionally-pinned: every reachable kind is pinned to an exact PSeq equality (0/1/2 -> ToSeq(category_text), 3 -> enum_rendering(class_name,member_name)=class_name++[46]++member_name, 4 -> ToSeq(fallback_text)), and Requires(MustTerminate(2)) closes the vacuous-divergence escape (Nagini is partial-correctness by default). All spec/pure/axiom regions left byte-identical in every attack (same-spec exit 0 for all 9).

Protocol run from project root with PY=python; weakness commands run concurrently in 3 batches of 3 (each a JVM+Z3):
  python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9281 <atk>

Attack results (all same-spec exit 0):
  atk_1 (prepatch bug: kind==3 falls to fallback; == model_prepatch.py) -> NOT-A-COUNTEREXAMPLE, verification failed (G-DIFF: spec senses the change). prepatch_reproduced=true.
  atk_2 (enum branch omits the dot: class_name++member_name) -> verification failed (kind==3 postcondition).
  atk_3 (enum truncated: returns class_name only) -> verification failed.
  atk_4 (control-flow-effect: while True: diverge on kind==3) -> verification failed (MustTerminate rejects divergence).
  atk_5 (collection arms 0/1/2 -> fallback_text swap) -> verification failed.
  atk_6 (enum reversed order: member++[46]++class) -> verification failed.
  atk_7 (unconditional divergence: while True before any return) -> verification failed (MustTerminate).
  atk_9 (fallback arm kind==4 -> category_text swap) -> verification failed.

The ONLY verifying impl is atk_8 (CANDIDATE, 18.1s), which is BYTE-IDENTICAL to bundle model.py (diff -q clean) i.e. the correct impl / positive control. Its faithful refined patch is the gold patch.diff verbatim (matches refinement A1 if->elif joins + A3 new enum arm). MANDATORY resolve run executed via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9281', patch, timeout=1800): RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved'. So the sole verifying candidate resolves -> no verify-but-wrong impl found.

A-leg audit: axioms region is empty (no A-consumed legs; no kind-3 unexpressible legs). The single changed op (enum rendering) is the A3 A-reference deep model. G-AX: python axiom_check.py -> exit 0, 'enum_rendering deep model (== gold "%s.%s"%(cls.__name__,member.name)) sound on 11 boundary + 5000 randomized Enum classes'. Correspondence holds: "%s.%s"%(a,b)==a+"."+b, member.name is str, dot()==[46]=='.' ; kind tag <-> isinstance dispatch (A1) and unchanged collection/fallback arms carried as opaque sequences (A2/A4) are R/I, covered by G-CONF. refinement.md legs are all R / A-reference / I, no kind-3. verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) audit for sphinx-doc__sphinx-9281 nagini. The modeled `describe` (with the documented Value projection) agrees with the real patched `object_description` (sphinx/util/inspect.py:438-471 @ base_commit 8ec06e9a, patch applied) on every input tested.

Evidence:
1. Same-spec model verifies: scripts/nagini_verify.sh passes (16.3s). Spec pins each category's rendering exactly and requires MustTerminate(2).
2. axiom_check.py (G-AX) passes: deep model enum_rendering(class_name,member_name)=class_name++'.'++member_name equals the real '%s.%s'%(cls.__name__, member.name) on 11 boundary + 5000 randomized enums.
3. Dispatch order in the model (kind 0 dict / 1 set / 2 frozenset / 3 enum.Enum / 4 other) mirrors the real patched if/elif chain order exactly, with the enum arm before the generic repr fallback (the discriminating change).
4. Independent large-scale conformance reproduction: 335,142 inputs (enums weighted, plus dicts and ints), including enum.Flag/IntFlag composites (member.name='RED|BLUE') and enum aliases — 0 divergences between contract-stripped describe and a faithful inline object_description. The bundle's own conformance_check.py could not run here only due to an unrelated repo/Python-version ImportError (from types import Union), which is a harness/env artifact resolved in the Docker gate, not a spec issue.

The unchanged collection/fallback arms are carried as opaque input sequences and only required to be reproduced verbatim, so the spec is not over-constrained. The enum arm — the only differential content — matches the real callee on every input, including alias/Flag edge cases. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + Value class + axioms/pure/pre/post regions; impl elided) screened against the PUBLIC problem_statement only (not hints_text). Mechanical G-LEAK screen passes (leakage.screen: no hard_failures). Semantic review confirms no leak beyond the public task:

- Gold discriminator = new arm `elif isinstance(object, enum.Enum): return "%s.%s" % (object.__class__.__name__, object.name)` i.e. an enum member renders as ClassName.MemberName rather than the ugly repr fallback. This is ALREADY PUBLIC in problem_statement's 'Expected behavior' block, which shows the desired `MyEnum.ValueA` vs the actual `<MyEnum.ValueA: 10>`. The spec's abstract restatement (owning-type name + dot + member name, example `MyEnum.FOO`) does not exceed that.
- No edit-localization leaks: patched file path `sphinx/util/inspect.py`, module path, and repo symbol `object_description` (the only distinctive changed symbol, len>=4) appear NOWHERE in the spec view — the model calls the function `describe`. No `isinstance`, no `enum.Enum`, no `%s.%s`, no `repr`, no `elif`, no diff markers.
- The if->elif dispatch edit is not revealed: spec describes 'mutually exclusive categories' as a behavioral property, not as the concrete `if`->`elif` source change. Unchanged arms are carried as opaque `category_text`/`fallback_text`, further hiding rather than exposing the edit.
- Comments are abstract rationale (termination/MustTerminate justification); the narration screen (bug/fix/patch/previously/prepatch) finds nothing, and no patched symbol is named in any comment/docstring.

The leak-relevant material (enum member -> owning-type '.' member-name) is exactly the publicly-stated Expected behavior; the spec adds Nagini modeling scaffolding (kind tag, PSeq theory, permissions) that carries no gold-edit locator. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
