# P2 adversarial audit — sphinx-doc__sphinx-8621

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -195,52 +195,22 @@
     # impl-start
     result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
     i = len(text)
-    Assert(len(ToSeq(text).drop(i)) == 0)
-    Assert(ToSeq(text).drop(i) == empty_seq())
-    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(0 <= i and i <= len(text))
         Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
         i = i - 1
         c = text[i]
-        Assert(ToSeq(text).drop(i)[0] == c)
-        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
-        if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
-            Assert(len(ToSeq(text).drop(i)) == 1)
-            Assert(ToSeq(text).drop(i) == PSeq(c))
-            Assert(result == single_part(empty_seq()))
-            Assert(PSeq(c) + result[0] == PSeq(c))
-            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
+        if is_sep(c):
+            result = emit_sep(c) + result
+        elif is_space(c):
+            if i + 1 <= len(text) - 1 and is_space(text[i + 1]):
+                result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
+            else:
+                result = emit_sep(c) + result
+        else:
             result = single_part(PSeq(c) + result[0]) + result.drop(1)
-        else:
-            # Interior/leading code point: unfold kparts one step.
-            Assert(len(ToSeq(text).drop(i)) >= 2)
-            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
-            if (i > 0) and is_sep(c):
-                result = emit_sep(c) + result
-            elif (i > 0) and is_space(c):
-                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
-                    Assert(len(ToSeq(text).drop(i)) >= 3)
-                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
-                    Assert(is_space(ToSeq(text).drop(i)[1]))
-                    Assert(len(result) >= 2)
-                    Assert(result[0] == empty_seq())
-                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
-                else:
-                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
-                    result = emit_sep(c) + result
-            else:
-                result = single_part(PSeq(c) + result[0]) + result.drop(1)
     return result
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -195,50 +195,18 @@
     # impl-start
     result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
     i = len(text)
-    Assert(len(ToSeq(text).drop(i)) == 0)
-    Assert(ToSeq(text).drop(i) == empty_seq())
-    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(0 <= i and i <= len(text))
         Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
         i = i - 1
         c = text[i]
-        Assert(ToSeq(text).drop(i)[0] == c)
-        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
         if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
-            Assert(len(ToSeq(text).drop(i)) == 1)
-            Assert(ToSeq(text).drop(i) == PSeq(c))
-            Assert(result == single_part(empty_seq()))
-            Assert(PSeq(c) + result[0] == PSeq(c))
-            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
             result = single_part(PSeq(c) + result[0]) + result.drop(1)
         else:
-            # Interior/leading code point: unfold kparts one step.
-            Assert(len(ToSeq(text).drop(i)) >= 2)
-            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
             if (i > 0) and is_sep(c):
                 result = emit_sep(c) + result
-            elif (i > 0) and is_space(c):
-                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
-                    Assert(len(ToSeq(text).drop(i)) >= 3)
-                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
-                    Assert(is_space(ToSeq(text).drop(i)[1]))
-                    Assert(len(result) >= 2)
-                    Assert(result[0] == empty_seq())
-                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
-                else:
-                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
-                    result = emit_sep(c) + result
             else:
                 result = single_part(PSeq(c) + result[0]) + result.drop(1)
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -195,49 +195,22 @@
     # impl-start
     result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
     i = len(text)
-    Assert(len(ToSeq(text).drop(i)) == 0)
-    Assert(ToSeq(text).drop(i) == empty_seq())
-    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(0 <= i and i <= len(text))
         Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
         i = i - 1
         c = text[i]
-        Assert(ToSeq(text).drop(i)[0] == c)
-        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
         if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
-            Assert(len(ToSeq(text).drop(i)) == 1)
-            Assert(ToSeq(text).drop(i) == PSeq(c))
-            Assert(result == single_part(empty_seq()))
-            Assert(PSeq(c) + result[0] == PSeq(c))
-            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
             result = single_part(PSeq(c) + result[0]) + result.drop(1)
         else:
-            # Interior/leading code point: unfold kparts one step.
-            Assert(len(ToSeq(text).drop(i)) >= 2)
-            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
             if (i > 0) and is_sep(c):
                 result = emit_sep(c) + result
             elif (i > 0) and is_space(c):
-                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
-                    Assert(len(ToSeq(text).drop(i)) >= 3)
-                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
-                    Assert(is_space(ToSeq(text).drop(i)[1]))
-                    Assert(len(result) >= 2)
-                    Assert(result[0] == empty_seq())
+                if i + 1 <= len(text) - 1 and is_space(text[i + 1]):
                     result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
                 else:
-                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
                     result = emit_sep(c) + result
             else:
                 result = single_part(PSeq(c) + result[0]) + result.drop(1)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -193,55 +193,7 @@
     Ensures(Result() == kparts(ToSeq(text), False))
     # post-conditions-end
     # impl-start
-    result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
-    i = len(text)
-    Assert(len(ToSeq(text).drop(i)) == 0)
-    Assert(ToSeq(text).drop(i) == empty_seq())
-    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(text), 1 / 2))
-        Invariant(0 <= i and i <= len(text))
-        Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        i = i - 1
-        c = text[i]
-        Assert(ToSeq(text).drop(i)[0] == c)
-        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
-        if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
-            Assert(len(ToSeq(text).drop(i)) == 1)
-            Assert(ToSeq(text).drop(i) == PSeq(c))
-            Assert(result == single_part(empty_seq()))
-            Assert(PSeq(c) + result[0] == PSeq(c))
-            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
-            result = single_part(PSeq(c) + result[0]) + result.drop(1)
-        else:
-            # Interior/leading code point: unfold kparts one step.
-            Assert(len(ToSeq(text).drop(i)) >= 2)
-            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
-            if (i > 0) and is_sep(c):
-                result = emit_sep(c) + result
-            elif (i > 0) and is_space(c):
-                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
-                    Assert(len(ToSeq(text).drop(i)) >= 3)
-                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
-                    Assert(is_space(ToSeq(text).drop(i)[1]))
-                    Assert(len(result) >= 2)
-                    Assert(result[0] == empty_seq())
-                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
-                else:
-                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
-                    result = emit_sep(c) + result
-            else:
-                result = single_part(PSeq(c) + result[0]) + result.drop(1)
-    return result
+    return single_part(empty_seq())
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -193,55 +193,7 @@
     Ensures(Result() == kparts(ToSeq(text), False))
     # post-conditions-end
     # impl-start
-    result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
-    i = len(text)
-    Assert(len(ToSeq(text).drop(i)) == 0)
-    Assert(ToSeq(text).drop(i) == empty_seq())
-    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(text), 1 / 2))
-        Invariant(0 <= i and i <= len(text))
-        Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        i = i - 1
-        c = text[i]
-        Assert(ToSeq(text).drop(i)[0] == c)
-        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
-        if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
-            Assert(len(ToSeq(text).drop(i)) == 1)
-            Assert(ToSeq(text).drop(i) == PSeq(c))
-            Assert(result == single_part(empty_seq()))
-            Assert(PSeq(c) + result[0] == PSeq(c))
-            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
-            result = single_part(PSeq(c) + result[0]) + result.drop(1)
-        else:
-            # Interior/leading code point: unfold kparts one step.
-            Assert(len(ToSeq(text).drop(i)) >= 2)
-            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
-            if (i > 0) and is_sep(c):
-                result = emit_sep(c) + result
-            elif (i > 0) and is_space(c):
-                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
-                    Assert(len(ToSeq(text).drop(i)) >= 3)
-                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
-                    Assert(is_space(ToSeq(text).drop(i)[1]))
-                    Assert(len(result) >= 2)
-                    Assert(result[0] == empty_seq())
-                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
-                else:
-                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
-                    result = emit_sep(c) + result
-            else:
-                result = single_part(PSeq(c) + result[0]) + result.drop(1)
-    return result
+    return kparts(ToSeq(text), False)
     # impl-end
 
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -199,21 +199,15 @@
     Assert(ToSeq(text).drop(i) == empty_seq())
     Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(0 <= i and i <= len(text))
         Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
         i = i - 1
         c = text[i]
         Assert(ToSeq(text).drop(i)[0] == c)
         Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
         if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
             Assert(len(ToSeq(text).drop(i)) == 1)
             Assert(ToSeq(text).drop(i) == PSeq(c))
             Assert(result == single_part(empty_seq()))
@@ -221,15 +215,12 @@
             Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
             result = single_part(PSeq(c) + result[0]) + result.drop(1)
         else:
-            # Interior/leading code point: unfold kparts one step.
             Assert(len(ToSeq(text).drop(i)) >= 2)
             Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
             if (i > 0) and is_sep(c):
                 result = emit_sep(c) + result
             elif (i > 0) and is_space(c):
                 if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
                     Assert(len(ToSeq(text).drop(i)) >= 3)
                     Assert(ToSeq(text).drop(i)[1] == text[i + 1])
                     Assert(is_space(ToSeq(text).drop(i)[1]))
@@ -268,5 +259,5 @@
     # post-conditions-end
     # impl-start
     parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]
-    return len(parts) == 1
+    return len(parts) == 2
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -199,21 +199,15 @@
     Assert(ToSeq(text).drop(i) == empty_seq())
     Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(0 <= i and i <= len(text))
         Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
         i = i - 1
         c = text[i]
         Assert(ToSeq(text).drop(i)[0] == c)
         Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
         if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
             Assert(len(ToSeq(text).drop(i)) == 1)
             Assert(ToSeq(text).drop(i) == PSeq(c))
             Assert(result == single_part(empty_seq()))
@@ -221,15 +215,12 @@
             Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
             result = single_part(PSeq(c) + result[0]) + result.drop(1)
         else:
-            # Interior/leading code point: unfold kparts one step.
             Assert(len(ToSeq(text).drop(i)) >= 2)
             Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
             if (i > 0) and is_sep(c):
                 result = emit_sep(c) + result
             elif (i > 0) and is_space(c):
                 if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
                     Assert(len(ToSeq(text).drop(i)) >= 3)
                     Assert(ToSeq(text).drop(i)[1] == text[i + 1])
                     Assert(is_space(ToSeq(text).drop(i)[1]))
@@ -267,6 +258,5 @@
     Ensures(Result() == (len(kparts(ToSeq(text), False)) == 1))
     # post-conditions-end
     # impl-start
-    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]
-    return len(parts) == 1
+    return len(kparts(ToSeq(text), False)) == 1
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -199,21 +199,15 @@
     Assert(ToSeq(text).drop(i) == empty_seq())
     Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(0 <= i and i <= len(text))
         Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
-        # invariants-end
         i = i - 1
         c = text[i]
         Assert(ToSeq(text).drop(i)[0] == c)
         Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
         if i == len(text) - 1:
-            # Last code point: the suffix has length 1, so kparts is the
-            # single-part base case and `result` is the empty-suffix base.
             Assert(len(ToSeq(text).drop(i)) == 1)
             Assert(ToSeq(text).drop(i) == PSeq(c))
             Assert(result == single_part(empty_seq()))
@@ -221,15 +215,12 @@
             Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
             result = single_part(PSeq(c) + result[0]) + result.drop(1)
         else:
-            # Interior/leading code point: unfold kparts one step.
             Assert(len(ToSeq(text).drop(i)) >= 2)
             Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
             if (i > 0) and is_sep(c):
                 result = emit_sep(c) + result
             elif (i > 0) and is_space(c):
                 if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
-                    # The next code point is a flanked blank space: `result`
-                    # already opens a blank token, merge `c` into it.
                     Assert(len(ToSeq(text).drop(i)) >= 3)
                     Assert(ToSeq(text).drop(i)[1] == text[i + 1])
                     Assert(is_space(ToSeq(text).drop(i)[1]))
@@ -267,6 +258,5 @@
     Ensures(Result() == (len(kparts(ToSeq(text), False)) == 1))
     # post-conditions-end
     # impl-start
-    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]
-    return len(parts) == 1
+    return True
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8621.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single inline keystroke description (a piece of literal text such as
  ``Control+X`` or ``Alt+^``) is divided into a flat sequence of *parts* that
  alternate keystroke / separator / keystroke / ... .  The recognised
  compound-key separators are the hyphen-minus ``-`` (U+002D), the plus sign
  ``+`` (U+002B), the circumflex ``^`` (U+005E) and a run of blank space.

  A separator splits the text into surrounding keystrokes ONLY when it actually
  stands BETWEEN two keystrokes — that is, only when it has at least one
  character before it AND at least one character after it.  A separator that
  sits at the very start or the very end of the text is NOT a separator: it
  belongs to the adjacent keystroke.  In particular a text consisting of a
  single separator character is one indivisible keystroke, and a keystroke that
  ends (or begins) with a separator character keeps that character as part of
  itself rather than introducing an empty keystroke beside it.

  The three single compound-key characters ``- + ^`` each form their own
  one-character separator token (two adjacent ones do not merge — an empty
  keystroke sits between them).  Blank space behaves differently: a maximal run
  of blank-space characters that is flanked on both sides collapses into ONE
  separator token, so a doubled blank between two keystrokes is a single
  separator, not two.

  Consequently the part sequence never contains an empty keystroke produced by
  a leading or trailing separator: ``-`` yields the single part ``-``;
  ``Alt+^`` yields exactly ``Alt`` / ``+`` / ``^`` (three parts), not a part
  sequence padded with empty keystrokes around the trailing ``^``.

  A text is rendered as a single, indivisible keystroke (no inner structure)
  exactly when this splitting produces a single part.

  Splitting a finite text is a bounded computation: both operations MUST
  terminate and return their answer (a total-correctness obligation, carried
  as MustTerminate in the precondition).  Nagini is a partial-correctness
  verifier by default, so without the obligation a diverging implementation
  (bare self-recursion, an endless loop) would satisfy every Ensures
  vacuously while sharing the spec; the real split always returns its parts.

Strings are modelled as `List[int]` / `PSeq[int]` of Unicode code points
(Nagini bans `str` indexing); the part sequence is a `PSeq[PSeq[int]]`.  The
modelled domain is printable ASCII (code points 32..126): the only blank-space
character in that range is the ordinary space U+0020, so blank runs are runs of
spaces and there is no interaction with line breaks.  The split is modelled
DEEPLY as the front-recursive fold `kparts` (a code point is a separator only
when flanked, with blank-space runs collapsing into a single token); its
equality to the real keystroke-splitting callee is checked out-of-band by
axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the keystroke split is modelled deeply below
#  as `kparts` and validated == the real keystroke-splitting callee out-of-band
#  by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def is_sep(c: int) -> bool:
    """A single compound-key separator character: '-' (45), '+' (43) or
    '^' (94)."""
    return c == 45 or c == 43 or c == 94


@Pure
def is_space(c: int) -> bool:
    """A blank-space character.  On the modelled printable-ASCII domain the only
    blank-space code point is the ordinary space ' ' (32)."""
    return c == 32


@Pure
def in_domain(c: int) -> bool:
    """The modelled domain: printable ASCII, code points 32..126.  The only
    blank-space character in this range is the ordinary space (32)."""
    return 32 <= c and c <= 126


@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def single_part(p: PSeq[int]) -> PSeq[PSeq[int]]:
    """The one-element part sequence containing the single part `p`."""
    return PSeq(p)


@Pure
def emit_sep(c: int) -> PSeq[PSeq[int]]:
    """The two leading parts emitted when code point `c` is a flanked, standalone
    separator: a fresh empty keystroke followed by the separator token `[c]`."""
    return single_part(empty_seq()) + single_part(PSeq(c))


@Pure
def kparts(s: PSeq[int], lead: bool) -> PSeq[PSeq[int]]:
    """The keystroke/separator part sequence of `s`, where `lead` is True iff a
    character precedes `s[0]` in the full text.

    A code point splits only when flanked: it needs a character before (`lead`)
    and a character after (`len(s) >= 2`).  Front-recursive (one unfold per code
    point).  A flanked single separator ``- + ^`` becomes its own one-character
    token (emitting a fresh empty keystroke before it).  A flanked blank space
    also begins a fresh separator token, BUT when the following code point is
    itself a flanked blank space the two merge into one blank-run token (the
    space is prepended to the already-open blank token rather than opening a new
    one).  Any other code point is prepended to the first part of the split of
    the remainder.  The last code point never splits (no following character),
    so a lone or trailing separator stays inside its keystroke."""
    Ensures(len(Result()) >= 1)
    Ensures(Implies(len(s) >= 2 and lead and is_space(s[0]),
                    len(Result()) >= 2 and Result()[0] == empty_seq()))
    if len(s) == 0:
        return single_part(empty_seq())
    if len(s) == 1:
        return single_part(s)
    if lead and is_sep(s[0]):
        return emit_sep(s[0]) + kparts(s.drop(1), True)
    if lead and is_space(s[0]):
        rest = kparts(s.drop(1), True)  # type: PSeq[PSeq[int]]
        if len(s) >= 3 and is_space(s[1]):
            # The next code point is itself a flanked blank space, so the split
            # of the remainder already opens a blank token (rest[0] is the fresh
            # empty keystroke, rest[1] the blank token): merge this space in.
            return single_part(empty_seq()) + single_part(PSeq(s[0]) + rest[1]) + rest.drop(2)
        return emit_sep(s[0]) + rest
    rest2 = kparts(s.drop(1), True)  # type: PSeq[PSeq[int]]
    return single_part(PSeq(s[0]) + rest2[0]) + rest2.drop(1)


@Pure
def kparts_unfold(s: PSeq[int], lead: bool) -> bool:
    """Lemma: one-step unfold of `kparts` on a non-trivial suffix, exposing the
    relation between `kparts(s, lead)` and `kparts(s.drop(1), True)` used by the
    impl loop invariant (one equation per impl branch)."""
    Requires(len(s) >= 2)
    Ensures(Result())
    # flanked single separator
    Ensures(Implies(lead and is_sep(s[0]),
                    kparts(s, lead) == emit_sep(s[0]) + kparts(s.drop(1), True)))
    # flanked blank space that MERGES with a following flanked blank space
    Ensures(Implies(lead and is_space(s[0]) and len(s) >= 3 and is_space(s[1]),
                    kparts(s, lead)
                    == single_part(empty_seq())
                    + single_part(PSeq(s[0]) + kparts(s.drop(1), True)[1])
                    + kparts(s.drop(1), True).drop(2)))
    # flanked blank space that does NOT merge (next code point is not a flanked
    # blank space): a standalone blank token
    Ensures(Implies(lead and is_space(s[0])
                    and not (len(s) >= 3 and is_space(s[1])),
                    kparts(s, lead) == emit_sep(s[0]) + kparts(s.drop(1), True)))
    # any other code point: prepended to the first part of the remainder split
    Ensures(Implies(not (lead and (is_sep(s[0]) or is_space(s[0]))),
                    kparts(s, lead)
                    == single_part(PSeq(s[0]) + kparts(s.drop(1), True)[0])
                    + kparts(s.drop(1), True).drop(1)))
    return True
# pure-end


def split_keystrokes(text: List[int]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # Modelled domain: every code point is printable ASCII (32..126); the only
    # blank-space character in this range is the ordinary space.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             in_domain(text[k])), [[text[k]]])))
    # TERMINATION: the split must actually ANSWER — splitting a finite text is
    # a bounded computation (one pass over the code points).  Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. bare self-recursion or an endless
    # loop) satisfies every Ensures vacuously; the real split always returns
    # its part sequence.  (Measure 1 < 2 lets keystroke_is_atomic, which holds
    # MustTerminate(2), call this function without leaking its obligation.)
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    # The returned part sequence is exactly the flanked-separator split of the
    # whole text (lead=False: nothing precedes the first code point).
    Ensures(Result() == kparts(ToSeq(text), False))
    # post-conditions-end
    # impl-start
    result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
    i = len(text)
    Assert(len(ToSeq(text).drop(i)) == 0)
    Assert(ToSeq(text).drop(i) == empty_seq())
    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(0 <= i and i <= len(text))
        Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        i = i - 1
        c = text[i]
        Assert(ToSeq(text).drop(i)[0] == c)
        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
        if i == len(text) - 1:
            # Last code point: the suffix has length 1, so kparts is the
            # single-part base case and `result` is the empty-suffix base.
            Assert(len(ToSeq(text).drop(i)) == 1)
            Assert(ToSeq(text).drop(i) == PSeq(c))
            Assert(result == single_part(empty_seq()))
            Assert(PSeq(c) + result[0] == PSeq(c))
            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
            result = single_part(PSeq(c) + result[0]) + result.drop(1)
        else:
            # Interior/leading code point: unfold kparts one step.
            Assert(len(ToSeq(text).drop(i)) >= 2)
            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
            if (i > 0) and is_sep(c):
                result = emit_sep(c) + result
            elif (i > 0) and is_space(c):
                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
                    # The next code point is a flanked blank space: `result`
                    # already opens a blank token, merge `c` into it.
                    Assert(len(ToSeq(text).drop(i)) >= 3)
                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
                    Assert(is_space(ToSeq(text).drop(i)[1]))
                    Assert(len(result) >= 2)
                    Assert(result[0] == empty_seq())
                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
                else:
                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
                    result = emit_sep(c) + result
            else:
                result = single_part(PSeq(c) + result[0]) + result.drop(1)
    return result
    # impl-end


def keystroke_is_atomic(text: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # Modelled domain: every code point is printable ASCII (32..126); the only
    # blank-space character in this range is the ordinary space.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             in_domain(text[k])), [[text[k]]])))
    # TERMINATION: the atomicity decision must actually ANSWER — it is one
    # bounded split plus a length test.  Nagini is a partial-correctness
    # verifier by default, so without this obligation a non-terminating
    # implementation satisfies every Ensures vacuously; the real decision
    # always returns its truth value.  (Measure 2 > 1 covers the call to
    # split_keystrokes, whose own obligation is MustTerminate(1).)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    # The text renders as a single indivisible keystroke exactly when the
    # flanked-separator split yields a single part.
    Ensures(Result() == (len(kparts(ToSeq(text), False)) == 1))
    # post-conditions-end
    # impl-start
    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]
    return len(parts) == 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ refinement-fidelity audit of the nagini twin-artifact for sphinx-doc__sphinx-8621. Scratch dir Project root, env python, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: split_keystrokes' postcondition pins Result() == kparts(ToSeq(text), False) by EXACT equality and keystroke_is_atomic pins Result() == (len(kparts(...))==1), both with Requires(MustTerminate(..)). So on the modelled domain (printable ASCII 32..126, enforced as a Forall Requires) any verifying same-spec impl is behaviorally identical to the deep model kparts, which is validated == the real post-patch regex re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)').split. Falsification surface is therefore only: (a) a tested input outside 32..126 where a verifying impl is unconstrained, or (b) kparts != real regex on a tested input. Both were checked and closed.

DOMAIN/SOUNDNESS CHECK: Enumerated every tested keystroke input from instance.json test_patch: the two new FAIL_TO_PASS ':kbd:`Alt+^`' and ':kbd:`-`', plus pre-existing kbd P2P context 'Control+X', 'M-x  M-s', 'space'. ALL are printable ASCII in 32..126 — inside the enforced precondition. No tab/newline/off-domain tested input exists, so the domain restriction opens no soundness hole. (Note: refinement.md/mapping.md call 'M-x  M-s' a PASS_TO_PASS; it is present as a pre-existing kbd verify-case in test_markup.py context lines — my resolve run confirms 31 P2P all pass. It is not in the JSON PASS_TO_PASS id list because that list is coarse test-node ids, but the case is exercised by test_inline.)

A-REFERENCE (A2) independently re-validated: (i) axiom_check.py exit 0 — 'kparts deep model == real re.compile(NEW).split sound on 63 boundary + 200000 fuzz inputs'; (ii) my own EXHAUSTIVE brute force over alphabet {-,+,^,space,a,b} for all lengths 0..6 = 55,987 strings, 0 mismatch vs re.compile(NEW).split. The lookbehind/lookahead flanking + greedy \s+ run-merge match kparts exactly on the whole domain.

REFINEMENT.MD LEG AUDIT (§A): A1=R (text:List[int] <-> str arg), A2=A-reference (deep kparts <-> self.pattern.split post-patch, G-AX-validated), A3=R (PSeq[PSeq[int]] <-> List[str]), A4=I+R (len==1 decision). NO A-consumed axiom, NO kind-3 leg — the sole changed op (the split) is modelled deeply as an A-reference, not hidden behind an axiom about the changed callee. §B/§B2/§C consistent; MustTerminate blocks the vacuous-divergence class. Correspondence to real callees holds.

ATTACKS (all same-spec confirmed via `adversary same-spec` exit 0; all built by substituting ONLY the two impl regions of model.py, axioms/@Pure/Requires/Ensures byte-identical). Commands run from project root:
- atk_1.py PREPATCH reproduction (unguarded split, no flanking guard): weakness -> NOT-A-COUNTEREXAMPLE, does NOT verify (fails loop invariant result==kparts). prepatch_reproduced=TRUE (G-DIFF: spec senses the change).
- atk_2.py partial-domain (drops the \s+/space branch, treats space as ordinary char): does NOT verify.
- atk_3.py boundary off-by-one (blank-merge guard uses i+1 instead of i+2): does NOT verify.
- atk_4.py control-flow-effect (return single_part(empty_seq()) ignoring text; terminates): does NOT verify.
- atk_5.py ungrounded-oracle ECHO of split (return kparts(ToSeq(text), False)): VERIFIES => CANDIDATE. Materialized faithful refined patch (gold pattern change per refinement map A2/A4) and RAN official harness: RESOLVED=True, COMPLETED=True, FAIL_TO_PASS 2/2, PASS_TO_PASS 31/31. Not a weakness (behavioral echo of gold).
- atk_6.py wrong atomicity (len(parts)==2): does NOT verify.
- atk_7.py ECHO of atomicity (return len(kparts(ToSeq(text),False))==1): VERIFIES => CANDIDATE. Faithful patch identical to gold; official harness RESOLVED=True (same run, FAIL_TO_PASS 2/2, PASS_TO_PASS 31/31). Not a weakness.
- atk_8.py degenerate atomicity (return True): does NOT verify.

RESOLVE COMMAND (official harness, via swebench_unified.harness.run_resolve under `docker`): run_resolve('sphinx-doc__sphinx-8621', <faithful_patch>, run_id='sbu-eq-echo-qbqg', timeout=1200) -> RESOLVED True. Both CANDIDATE echoes materialize to the SAME faithful patch because both are behaviorally == gold on the entire modelled domain; that patch RESOLVES. positive_control.py = verbatim model.py, verifies (17.9s) as expected.

CONCLUSION: 8 distinct wrong-impl attacks run + verified. The 6 genuinely-wrong impls (prepatch, drop-space, boundary, degenerate, wrong-atomic, always-true) all FAIL to verify — the spec rejects them. The only same-spec verifying impls are behavioral ECHOES of the gold whose faithful refined patches RESOLVE. No verifying same-spec impl exists whose faithful patch fails to resolve. verify => correct holds. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8621.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single inline keystroke description (a piece of literal text such as
  ``Control+X`` or ``Alt+^``) is divided into a flat sequence of *parts* that
  alternate keystroke / separator / keystroke / ... .  The recognised
  compound-key separators are the hyphen-minus ``-`` (U+002D), the plus sign
  ``+`` (U+002B), the circumflex ``^`` (U+005E) and a run of blank space.

  A separator splits the text into surrounding keystrokes ONLY when it actually
  stands BETWEEN two keystrokes — that is, only when it has at least one
  character before it AND at least one character after it.  A separator that
  sits at the very start or the very end of the text is NOT a separator: it
  belongs to the adjacent keystroke.  In particular a text consisting of a
  single separator character is one indivisible keystroke, and a keystroke that
  ends (or begins) with a separator character keeps that character as part of
  itself rather than introducing an empty keystroke beside it.

  The three single compound-key characters ``- + ^`` each form their own
  one-character separator token (two adjacent ones do not merge — an empty
  keystroke sits between them).  Blank space behaves differently: a maximal run
  of blank-space characters that is flanked on both sides collapses into ONE
  separator token, so a doubled blank between two keystrokes is a single
  separator, not two.

  Consequently the part sequence never contains an empty keystroke produced by
  a leading or trailing separator: ``-`` yields the single part ``-``;
  ``Alt+^`` yields exactly ``Alt`` / ``+`` / ``^`` (three parts), not a part
  sequence padded with empty keystrokes around the trailing ``^``.

  A text is rendered as a single, indivisible keystroke (no inner structure)
  exactly when this splitting produces a single part.

  Splitting a finite text is a bounded computation: both operations MUST
  terminate and return their answer (a total-correctness obligation, carried
  as MustTerminate in the precondition).  Nagini is a partial-correctness
  verifier by default, so without the obligation a diverging implementation
  (bare self-recursion, an endless loop) would satisfy every Ensures
  vacuously while sharing the spec; the real split always returns its parts.

Strings are modelled as `List[int]` / `PSeq[int]` of Unicode code points
(Nagini bans `str` indexing); the part sequence is a `PSeq[PSeq[int]]`.  The
modelled domain is printable ASCII (code points 32..126): the only blank-space
character in that range is the ordinary space U+0020, so blank runs are runs of
spaces and there is no interaction with line breaks.  The split is modelled
DEEPLY as the front-recursive fold `kparts` (a code point is a separator only
when flanked, with blank-space runs collapsing into a single token); its
equality to the real keystroke-splitting callee is checked out-of-band by
axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the keystroke split is modelled deeply below
#  as `kparts` and validated == the real keystroke-splitting callee out-of-band
#  by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def is_sep(c: int) -> bool:
    """A single compound-key separator character: '-' (45), '+' (43) or
    '^' (94)."""
    return c == 45 or c == 43 or c == 94


@Pure
def is_space(c: int) -> bool:
    """A blank-space character.  On the modelled printable-ASCII domain the only
    blank-space code point is the ordinary space ' ' (32)."""
    return c == 32


@Pure
def in_domain(c: int) -> bool:
    """The modelled domain: printable ASCII, code points 32..126.  The only
    blank-space character in this range is the ordinary space (32)."""
    return 32 <= c and c <= 126


@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def single_part(p: PSeq[int]) -> PSeq[PSeq[int]]:
    """The one-element part sequence containing the single part `p`."""
    return PSeq(p)


@Pure
def emit_sep(c: int) -> PSeq[PSeq[int]]:
    """The two leading parts emitted when code point `c` is a flanked, standalone
    separator: a fresh empty keystroke followed by the separator token `[c]`."""
    return single_part(empty_seq()) + single_part(PSeq(c))


@Pure
def kparts(s: PSeq[int], lead: bool) -> PSeq[PSeq[int]]:
    """The keystroke/separator part sequence of `s`, where `lead` is True iff a
    character precedes `s[0]` in the full text.

    A code point splits only when flanked: it needs a character before (`lead`)
    and a character after (`len(s) >= 2`).  Front-recursive (one unfold per code
    point).  A flanked single separator ``- + ^`` becomes its own one-character
    token (emitting a fresh empty keystroke before it).  A flanked blank space
    also begins a fresh separator token, BUT when the following code point is
    itself a flanked blank space the two merge into one blank-run token (the
    space is prepended to the already-open blank token rather than opening a new
    one).  Any other code point is prepended to the first part of the split of
    the remainder.  The last code point never splits (no following character),
    so a lone or trailing separator stays inside its keystroke."""
    Ensures(len(Result()) >= 1)
    Ensures(Implies(len(s) >= 2 and lead and is_space(s[0]),
                    len(Result()) >= 2 and Result()[0] == empty_seq()))
    if len(s) == 0:
        return single_part(empty_seq())
    if len(s) == 1:
        return single_part(s)
    if lead and is_sep(s[0]):
        return emit_sep(s[0]) + kparts(s.drop(1), True)
    if lead and is_space(s[0]):
        rest = kparts(s.drop(1), True)  # type: PSeq[PSeq[int]]
        if len(s) >= 3 and is_space(s[1]):
            # The next code point is itself a flanked blank space, so the split
            # of the remainder already opens a blank token (rest[0] is the fresh
            # empty keystroke, rest[1] the blank token): merge this space in.
            return single_part(empty_seq()) + single_part(PSeq(s[0]) + rest[1]) + rest.drop(2)
        return emit_sep(s[0]) + rest
    rest2 = kparts(s.drop(1), True)  # type: PSeq[PSeq[int]]
    return single_part(PSeq(s[0]) + rest2[0]) + rest2.drop(1)


@Pure
def kparts_unfold(s: PSeq[int], lead: bool) -> bool:
    """Lemma: one-step unfold of `kparts` on a non-trivial suffix, exposing the
    relation between `kparts(s, lead)` and `kparts(s.drop(1), True)` used by the
    impl loop invariant (one equation per impl branch)."""
    Requires(len(s) >= 2)
    Ensures(Result())
    # flanked single separator
    Ensures(Implies(lead and is_sep(s[0]),
                    kparts(s, lead) == emit_sep(s[0]) + kparts(s.drop(1), True)))
    # flanked blank space that MERGES with a following flanked blank space
    Ensures(Implies(lead and is_space(s[0]) and len(s) >= 3 and is_space(s[1]),
                    kparts(s, lead)
                    == single_part(empty_seq())
                    + single_part(PSeq(s[0]) + kparts(s.drop(1), True)[1])
                    + kparts(s.drop(1), True).drop(2)))
    # flanked blank space that does NOT merge (next code point is not a flanked
    # blank space): a standalone blank token
    Ensures(Implies(lead and is_space(s[0])
                    and not (len(s) >= 3 and is_space(s[1])),
                    kparts(s, lead) == emit_sep(s[0]) + kparts(s.drop(1), True)))
    # any other code point: prepended to the first part of the remainder split
    Ensures(Implies(not (lead and (is_sep(s[0]) or is_space(s[0]))),
                    kparts(s, lead)
                    == single_part(PSeq(s[0]) + kparts(s.drop(1), True)[0])
                    + kparts(s.drop(1), True).drop(1)))
    return True
# pure-end


def split_keystrokes(text: List[int]) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # Modelled domain: every code point is printable ASCII (32..126); the only
    # blank-space character in this range is the ordinary space.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             in_domain(text[k])), [[text[k]]])))
    # TERMINATION: the split must actually ANSWER — splitting a finite text is
    # a bounded computation (one pass over the code points).  Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. bare self-recursion or an endless
    # loop) satisfies every Ensures vacuously; the real split always returns
    # its part sequence.  (Measure 1 < 2 lets keystroke_is_atomic, which holds
    # MustTerminate(2), call this function without leaking its obligation.)
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    # The returned part sequence is exactly the flanked-separator split of the
    # whole text (lead=False: nothing precedes the first code point).
    Ensures(Result() == kparts(ToSeq(text), False))
    # post-conditions-end
    # impl-start
    result = single_part(empty_seq())  # type: PSeq[PSeq[int]]
    i = len(text)
    Assert(len(ToSeq(text).drop(i)) == 0)
    Assert(ToSeq(text).drop(i) == empty_seq())
    Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(empty_seq()))
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(0 <= i and i <= len(text))
        Invariant(result == kparts(ToSeq(text).drop(i), i > 0))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        i = i - 1
        c = text[i]
        Assert(ToSeq(text).drop(i)[0] == c)
        Assert(ToSeq(text).drop(i).drop(1) == ToSeq(text).drop(i + 1))
        if i == len(text) - 1:
            # Last code point: the suffix has length 1, so kparts is the
            # single-part base case and `result` is the empty-suffix base.
            Assert(len(ToSeq(text).drop(i)) == 1)
            Assert(ToSeq(text).drop(i) == PSeq(c))
            Assert(result == single_part(empty_seq()))
            Assert(PSeq(c) + result[0] == PSeq(c))
            Assert(kparts(ToSeq(text).drop(i), i > 0) == single_part(PSeq(c)))
            result = single_part(PSeq(c) + result[0]) + result.drop(1)
        else:
            # Interior/leading code point: unfold kparts one step.
            Assert(len(ToSeq(text).drop(i)) >= 2)
            Assert(kparts_unfold(ToSeq(text).drop(i), i > 0))
            if (i > 0) and is_sep(c):
                result = emit_sep(c) + result
            elif (i > 0) and is_space(c):
                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
                    # The next code point is a flanked blank space: `result`
                    # already opens a blank token, merge `c` into it.
                    Assert(len(ToSeq(text).drop(i)) >= 3)
                    Assert(ToSeq(text).drop(i)[1] == text[i + 1])
                    Assert(is_space(ToSeq(text).drop(i)[1]))
                    Assert(len(result) >= 2)
                    Assert(result[0] == empty_seq())
                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
                else:
                    Assert(not (len(ToSeq(text).drop(i)) >= 3 and is_space(ToSeq(text).drop(i)[1])))
                    result = emit_sep(c) + result
            else:
                result = single_part(PSeq(c) + result[0]) + result.drop(1)
    return result
    # impl-end


def keystroke_is_atomic(text: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # Modelled domain: every code point is printable ASCII (32..126); the only
    # blank-space character in this range is the ordinary space.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             in_domain(text[k])), [[text[k]]])))
    # TERMINATION: the atomicity decision must actually ANSWER — it is one
    # bounded split plus a length test.  Nagini is a partial-correctness
    # verifier by default, so without this obligation a non-terminating
    # implementation satisfies every Ensures vacuously; the real decision
    # always returns its truth value.  (Measure 2 > 1 covers the call to
    # split_keystrokes, whose own obligation is MustTerminate(1).)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    # The text renders as a single indivisible keystroke exactly when the
    # flanked-separator split yields a single part.
    Ensures(Result() == (len(kparts(ToSeq(text), False)) == 1))
    # post-conditions-end
    # impl-start
    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]
    return len(parts) == 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ refinement-fidelity audit of the nagini twin-artifact for sphinx-doc__sphinx-8621. Scratch dir Project root, env python, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: split_keystrokes' postcondition pins Result() == kparts(ToSeq(text), False) by EXACT equality and keystroke_is_atomic pins Result() == (len(kparts(...))==1), both with Requires(MustTerminate(..)). So on the modelled domain (printable ASCII 32..126, enforced as a Forall Requires) any verifying same-spec impl is behaviorally identical to the deep model kparts, which is validated == the real post-patch regex re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)').split. Falsification surface is therefore only: (a) a tested input outside 32..126 where a verifying impl is unconstrained, or (b) kparts != real regex on a tested input. Both were checked and closed.

DOMAIN/SOUNDNESS CHECK: Enumerated every tested keystroke input from instance.json test_patch: the two new FAIL_TO_PASS ':kbd:`Alt+^`' and ':kbd:`-`', plus pre-existing kbd P2P context 'Control+X', 'M-x  M-s', 'space'. ALL are printable ASCII in 32..126 — inside the enforced precondition. No tab/newline/off-domain tested input exists, so the domain restriction opens no soundness hole. (Note: refinement.md/mapping.md call 'M-x  M-s' a PASS_TO_PASS; it is present as a pre-existing kbd verify-case in test_markup.py context lines — my resolve run confirms 31 P2P all pass. It is not in the JSON PASS_TO_PASS id list because that list is coarse test-node ids, but the case is exercised by test_inline.)

A-REFERENCE (A2) independently re-validated: (i) axiom_check.py exit 0 — 'kparts deep model == real re.compile(NEW).split sound on 63 boundary + 200000 fuzz inputs'; (ii) my own EXHAUSTIVE brute force over alphabet {-,+,^,space,a,b} for all lengths 0..6 = 55,987 strings, 0 mismatch vs re.compile(NEW).split. The lookbehind/lookahead flanking + greedy \s+ run-merge match kparts exactly on the whole domain.

REFINEMENT.MD LEG AUDIT (§A): A1=R (text:List[int] <-> str arg), A2=A-reference (deep kparts <-> self.pattern.split post-patch, G-AX-validated), A3=R (PSeq[PSeq[int]] <-> List[str]), A4=I+R (len==1 decision). NO A-consumed axiom, NO kind-3 leg — the sole changed op (the split) is modelled deeply as an A-reference, not hidden behind an axiom about the changed callee. §B/§B2/§C consistent; MustTerminate blocks the vacuous-divergence class. Correspondence to real callees holds.

ATTACKS (all same-spec confirmed via `adversary same-spec` exit 0; all built by substituting ONLY the two impl regions of model.py, axioms/@Pure/Requires/Ensures byte-identical). Commands run from project root:
- atk_1.py PREPATCH reproduction (unguarded split, no flanking guard): weakness -> NOT-A-COUNTEREXAMPLE, does NOT verify (fails loop invariant result==kparts). prepatch_reproduced=TRUE (G-DIFF: spec senses the change).
- atk_2.py partial-domain (drops the \s+/space branch, treats space as ordinary char): does NOT verify.
- atk_3.py boundary off-by-one (blank-merge guard uses i+1 instead of i+2): does NOT verify.
- atk_4.py control-flow-effect (return single_part(empty_seq()) ignoring text; terminates): does NOT verify.
- atk_5.py ungrounded-oracle ECHO of split (return kparts(ToSeq(text), False)): VERIFIES => CANDIDATE. Materialized faithful refined patch (gold pattern change per refinement map A2/A4) and RAN official harness: RESOLVED=True, COMPLETED=True, FAIL_TO_PASS 2/2, PASS_TO_PASS 31/31. Not a weakness (behavioral echo of gold).
- atk_6.py wrong atomicity (len(parts)==2): does NOT verify.
- atk_7.py ECHO of atomicity (return len(kparts(ToSeq(text),False))==1): VERIFIES => CANDIDATE. Faithful patch identical to gold; official harness RESOLVED=True (same run, FAIL_TO_PASS 2/2, PASS_TO_PASS 31/31). Not a weakness.
- atk_8.py degenerate atomicity (return True): does NOT verify.

RESOLVE COMMAND (official harness, via swebench_unified.harness.run_resolve under `docker`): run_resolve('sphinx-doc__sphinx-8621', <faithful_patch>, run_id='sbu-eq-echo-qbqg', timeout=1200) -> RESOLVED True. Both CANDIDATE echoes materialize to the SAME faithful patch because both are behaviorally == gold on the entire modelled domain; that patch RESOLVES. positive_control.py = verbatim model.py, verifies (17.9s) as expected.

CONCLUSION: 8 distinct wrong-impl attacks run + verified. The 6 genuinely-wrong impls (prepatch, drop-space, boundary, degenerate, wrong-atomic, always-true) all FAIL to verify — the spec rejects them. The only same-spec verifying impls are behavioral ECHOES of the gold whose faithful refined patches RESOLVE. No verifying same-spec impl exists whose faithful patch fails to resolve. verify => correct holds. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for the modeled split_keystrokes / keystroke_is_atomic against the real repo callee (post-patch re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)').split at sphinx/builders/html/transforms.py:40,45).

Procedure: (1) same_spec markers check exits 0 — spec region byte-identical. (2) Confirmed the modeled A-reference regex equals the gold patch line in patch.diff verbatim. (3) Reimplemented kparts (front-recursive flanked-split fold with blank-run merging) and the real re.split in plain Python and cross-checked them.

Results: 0 mismatches under (a) exhaustive enumeration over {-,+,^,space,a,b} up to len 5, {-,+,^,space,a} up to len 8, {space,a,-} up to len 10; (b) 300,000 random strings over the full printable-ASCII domain 32..126 (bias toward separators/spaces), lengths 0-12; (c) all tested keystroke strings ('-','+','Shift-+','Alt+^','M-x  M-s', leading/trailing separators, doubled blank runs) — each matches the real callee exactly.

The modelled-domain restriction (in_domain 32..126) is ENFORCED as a Requires Forall on both functions, not left in prose, so the spec makes no claim on inputs (\n, \t, Unicode spaces) where model and callee could diverge due to the '.' lookaround subtlety. Termination is required (MustTerminate) with exact functional postconditions, so any verifying same-spec impl must return exactly kparts — the spec is complete on its domain and does not overclaim. Bundle's own axiom_check.py (G-AX) also passes at 0 mismatch on 200k fuzz.

No diverging input found; the modeled function agrees with the real callee on every in-domain input. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (0 hard failures): no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment naming the patched symbol, no narration. Verified separately: patched symbol {KeyboardTransform} and file sphinx/builders/html/transforms.py do NOT appear in the projected spec view (impl regions are elided). Semantic judgment: the gold edit is pattern = re.compile(r'(-|\+|\^|\s+)') -> re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)'). The discriminating content of that edit is 'a separator at the boundary of the text is NOT a separator', restated in the spec view as the flanking rule (splits only when it has a char before AND after; boundary separators attach to their keystroke; lone separator = one part). This is exactly the problem_statement's public 'Expected behavior': single <kbd> for standalone -/+/^, and differentiate separator vs keystroke positions. So the behavioral disclosure does not go beyond problem_statement. The actual mechanism (regex lookbehind/lookahead, file, line, symbol) lives only in the elided impl region and in audit-only docs (mapping.md/refinement.md), which are not solver-visible. The \s+ blank-run collapsing is pre-existing behavior, not the fix discriminator, and reveals no edit locus. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
