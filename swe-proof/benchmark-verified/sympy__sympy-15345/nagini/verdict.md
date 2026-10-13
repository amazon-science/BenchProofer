# P2 adversarial audit — sympy__sympy-15345

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9b.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec wrong implementation was found. 13 distinct same-spec wrong impls were run through `adversary weakness`; 12 were REJECTED by the spec (exit 2) and the 1 CANDIDATE (atk_10) is an ungrounded-oracle ECHO whose materialized faithful patch RESOLVES under the official harness (FAIL_TO_PASS test_Function pass, 8/8 PASS_TO_PASS), i.e. a correct alternative implementation, not a spec weakness. Per docs/architecture.md §5 a candidate whose patch resolves must not fail the gate.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,23 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
         Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
         Assert(operands.drop(i - 1)[0] == operands[i - 1])
         Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
         if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
             Assert(len(operands.drop(i - 1)) == 1)
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
             Assert(len(operands.drop(i - 1)) >= 2)
             body = operands[i - 1] + sep() + body
         i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
+    result = name + PSeq(40) + body + PSeq(41)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,30 +111,14 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
-            body = operands[i - 1]
-        else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
+        body = operands[i - 1] + sep() + body
         i = i - 1
     result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,29 +111,16 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(operands)
+    i = len(operands) - 1
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
+        Invariant(MustTerminate(i + 1))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
+        if i == len(operands) - 1:
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
             body = operands[i - 1] + sep() + body
         i = i - 1
     result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,30 +111,17 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
         if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
+            body = body + sep() + operands[i - 1]
         i = i - 1
     result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
     return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,30 +111,17 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
         if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
+            body = operands[i - 1] + PSeq(44) + body
         i = i - 1
     result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
     return result
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,23 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
         Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
         Assert(operands.drop(i - 1)[0] == operands[i - 1])
         Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
         if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
             Assert(len(operands.drop(i - 1)) == 1)
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
             Assert(len(operands.drop(i - 1)) >= 2)
             body = operands[i - 1] + sep() + body
         i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
+    result = PSeq(lbracket()) + name + body + PSeq(rbracket())  # type: PSeq[int]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,22 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
         Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
         Assert(operands.drop(i - 1)[0] == operands[i - 1])
         Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
         if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
             Assert(len(operands.drop(i - 1)) == 1)
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
             Assert(len(operands.drop(i - 1)) >= 2)
             body = operands[i - 1] + sep() + body
-        i = i - 1
+        i = i - 0
     result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,5 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
-    body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(operands)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
-            body = operands[i - 1]
-        else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
-        i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
-    return result
+    return print_lattice_call(name, operands)
     # impl-end
```

Attack 9 — `atk_9b.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,8 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
-    body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(operands)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
-            body = operands[i - 1]
-        else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
-        i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
-    return result
+    if len(operands) == 1:
+        Assert(joined(operands) == operands[0])
+        return name + PSeq(lbracket()) + operands[0] + PSeq(rbracket())
+    return name + PSeq(lbracket()) + operands[0] + PSeq(rbracket())
     # impl-end
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,5 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
-    body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(operands)
-    while i > 0:
-        # invariants-start
-        Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
-            body = operands[i - 1]
-        else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
-        i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
-    return result
+    return rendered(name, operands)
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,28 +111,21 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
+    Assert(False)
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
         Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
         Assert(operands.drop(i - 1)[0] == operands[i - 1])
         Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
         if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
             Assert(len(operands.drop(i - 1)) == 1)
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
             Assert(len(operands.drop(i - 1)) >= 2)
             body = operands[i - 1] + sep() + body
         i = i - 1
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,30 +111,20 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
+    seen = False
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
-            body = operands[i - 1]
-        else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
+        if len(operands[i - 1]) > 0:
+            if seen:
+                body = operands[i - 1] + sep() + body
+            else:
+                body = operands[i - 1]
+            seen = True
         i = i - 1
     result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
     return result
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,24 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
     body = PSeq(0).take(0)  # type: PSeq[int]
     i = len(operands)
     while i > 0:
         # invariants-start
         Invariant(0 <= i and i <= len(operands))
         Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
         Assert(operands.drop(i - 1)[0] == operands[i - 1])
         Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
         if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
             Assert(len(operands.drop(i - 1)) == 1)
             body = operands[i - 1]
         else:
-            # at least two operands remain, so `joined` unfolds once.
             Assert(len(operands.drop(i - 1)) >= 2)
             body = operands[i - 1] + sep() + body
         i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
-    return result
+    if len(operands) <= 2:
+        return name + PSeq(lbracket()) + body + PSeq(rbracket())
+    return name + PSeq(40) + body + PSeq(41)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,22 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
-    body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(operands)
-    while i > 0:
+    n = len(operands)
+    i = n
+    body = operands[n - 1]  # type: PSeq[int]
+    Assert(len(operands.drop(n - 1)) == 1)
+    Assert(operands.drop(n - 1)[0] == operands[n - 1])
+    while i > 1:
         # invariants-start
-        Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
+        Invariant(1 <= i and i <= n and n == len(operands))
+        Invariant(body == joined(operands.drop(i - 1)))
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
-            body = operands[i - 1]
-        else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
+        Assert(operands.drop(i - 2)[0] == operands[i - 2])
+        Assert(operands.drop(i - 2).drop(1) == operands.drop(i - 1))
+        Assert(len(operands.drop(i - 2)) >= 2)
+        body = operands[i - 2] + sep() + body
         i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
-    return result
+    Assert(operands.drop(0) == operands)
+    return name + PSeq(lbracket()) + body + PSeq(rbracket())
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**COMMANDS:** per attack `python -m swebench_unified.adversary weakness nagini sympy__sympy-15345 <f>.py` (log <f>.weak.log), plus `bash scripts/nagini_verify.sh <f>.py` (log <f>.direct.log) to capture the VERIFIER MESSAGE and prove each rejection is a real spec rejection rather than an incidental translation error. Verifications were run 3-at-a-time as concurrent background jobs (each Nagini check spawns a JVM+Z3).

### PER-ATTACK RESULTS (weakness exit / verifier message):
- atk_1.py PREPATCH BUG REPRODUCED (round parens `name+PSeq(40)+body+PSeq(41)` instead of square brackets): exit 2; `atk_1.py:103: Postcondition... Assertion (Result() == rendered(name, operands)) might not hold.` This is the G-DIFF discriminating clause ('(' 40 != '[' 91) firing.
- atk_2.py TRAILING SEPARATOR after the last operand: exit 2; line 103 postcondition failure.
- atk_3.py BOUNDARY/off-by-one, DROPS the last operand (loop starts at len-1): exit 2; line 103 postcondition failure.
- atk_4.py OPERANDS REORDERED (emitted right-to-left; body+sep+operands[i-1]): exit 2; line 103 postcondition failure.
- atk_5.py SEPARATOR WEAKENED to a bare comma PSeq(44), no space: exit 2; line 103 postcondition failure.
- atk_6.py NAME MOVED INSIDE the brackets (`'['+name+body+']'`): exit 2; line 103 postcondition failure.
- atk_7.py DIVERGENCE, endless loop (`i = i - 0`), MustTerminate invariant removed: exit 2; `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` -> MustTerminate(2) genuinely blocks the vacuous-partial-correctness class.
- atk_8.py UNBOUNDED SELF-RECURSION (`return print_lattice_call(name, operands)`): exit 2; `Obligation leak check failed. Callee print_lattice_call might not take all unsatisfied obligations from the caller.`
- atk_9b.py PARTIAL DOMAIN / control-flow effect: correct only at arity 1, for arity>=2 emits ONLY the first operand while keeping the name+'['...']' shape (so every bracket/prefix postcondition still holds and only the full functional one can catch it): exit 2; line 103 postcondition failure. (NOTE: the first encoding atk_9.py used `raise ValueError`, which is outside Nagini's fragment -> `Translation failed: Unsupported builtin function`; that is a MALFORMED attack and NOT evidence, so it was re-encoded as atk_9b.py and atk_9.py is excluded from the submitted list.)
- atk_10.py UNGROUNDED-ORACLE ECHO (`return rendered(name, operands)` -- returns the spec's own pure model): exit 0 CANDIDATE, verifies in 14.2s. FAITHFUL PATCH MATERIALIZED (patch_atk_10.diff, verified to apply at base_commit 9ef28fba with `git apply --check`) and RUN THROUGH THE OFFICIAL HARNESS via `swebench_unified.harness.run_resolve`: **resolved=True, completed=True**, FAIL_TO_PASS {success:[test_Function]}, PASS_TO_PASS 8/8 success, PASS_TO_FAIL/FAIL_TO_FAIL empty (log resolve_atk_10.log). So this candidate is a correct alternative impl (an echo of the reference), NOT a verify-but-wrong witness -> does not break the spec.
- atk_11.py VACUITY CONTROL (`Assert(False)` under the frozen precondition): exit 2; `atk_11.py:114: Assert might fail. Assertion False might not hold.` -> the precondition len(operands)>0 + MustTerminate(2) is SATISFIABLE; the spec is non-vacuous and the other rejections are meaningful.
- atk_12.py CONTROL-FLOW EFFECT, silently DROPS zero-length operands (real `", ".join(["","x"])` == ", x" keeps them): exit 2; line 103 postcondition failure.
- atk_13.py ARITY-DEPENDENT partial correctness: square brackets for arity<=2 but ROUND PARENS for arity>=3 -- aimed exactly at the F2P witness `Max[x, y, z]`: exit 2; line 103 postcondition failure. This is the sharpest attack (it satisfies the spec on the small cases) and the spec still catches it.

**POSITIVE CONTROL:** pos_control.py is a STRUCTURALLY DIFFERENT correct impl (body seeded from the LAST operand, loop bound `i > 1`, no in-loop last/not-last branch, different invariant `body == joined(operands.drop(i-1))`). weakness exit 0 = CANDIDATE, verifies in 16.4s. Because it verifies I also materialized and RAN its faithful patch (patch_pos_control.diff, applies at base_commit): run_resolve -> **resolved=True, completed=True**, F2P test_Function pass, PASS_TO_PASS 8/8 (log resolve_pos_control.log). So the spec admits an independent correct implementation and is not too strong; both verifying impls resolve, which is exactly the verify=>correct direction holding.

A-LEG AUDIT (the G-EQ focus; R/I legs pre-cleared by G-CONF 100000 checks / 0 disagreements). refinement.md tags: B1 R, B2 R, B3 A-reference, B4 I, B5 A-reference. NO KIND-3 STEP, and crucially NO CONSUMED AXIOM AT ALL -- the axioms region is empty (`# (No consumed axioms...)`), meta.json `axioms: []`, and no `@ContractOnly` anywhere, so there is no assumed-postcondition trust point. The changed operation (square-bracket application syntax + ", "-join) is modeled DEEPLY in the pure region (`joined`/`rendered`), which is the right treatment: the thing that changed is not hidden behind an axiom.

A-reference correspondence CHECKED AGAINST THE REAL CALLEE, not just asserted: (i) bundle axiom_check.py re-run -> exit 0 (12 boundary operand lists x 5 names + 3 F2P witnesses + 20000 fuzz, 0 mismatch); (ii) I wrote an independent probe (aleg.py) in a throwaway worktree of sympy at base_commit WITH THE GOLD PATCH APPLIED and compared, for 16 real lattice expressions, the model formula against the live printer: `joined_model(ops) == p.stringify(e.args, ", ")` for every case (A-reference 1) and `name+"["+joined+"]" == p.doprint(e)` for every case (A-reference 2), 0 mismatches -- incl. nested `Max[z, Min[x, y]]`, spaces `Max[z, x + 1, y - 2]`, arity 6, and `Min[1/2, x^(1/2)]`.

F2P assertion reproduced verbatim: `mcode(Max(x,y,z)*Min(y,z)) == "Max[x, y, z]*Min[y, z]"`, and the issue's case `mcode(Max(x,2)) == 'Max[2, x]'`. Gold-patched source confirmed to be exactly `return "%s[%s]" % (mfunc, self.stringify(expr.args, ", "))` reached via `_print_MinMaxBase = _print_Function`, matching mapping.md §1/§3 line citations (str.py:35-36 stringify = sep.join([...])). Operand-ORDER claim (B2, the model must NOT reorder) checked live: `Max(x,2).args` == ('2','x') and the printed text is `Max[2, x]` -- the canonicalisation happens UPSTREAM of the printer, so taking `operands` as given in args order is faithful, and atk_4 confirms the spec still rejects an impl that reorders them itself.

Precondition domain (`len(operands) > 0`) checked live for over-strength: `Max()` raises ValueError("The Max/Min functions must have arguments") and `Max(x)` collapses to a bare Symbol, so no real MinMaxBase node ever reaches the printer with 0 operands -- the precondition excludes no reachable input.

**CONCLUSION:** 13 admissible distinct attacks run to completion (partial-domain, boundary/off-by-one, reorder, separator, delimiter, name-placement, two divergence classes, arity-dependent, zero-length-operand control-flow effect, ungrounded-oracle echo, vacuity control), the prepatch bug reproduced and rejected, every rejection traced to a real spec message (line 103 functional postcondition or the MustTerminate obligation leak) rather than a translation error, the vacuity control fails as it must, and the only two verifying same-spec impls both RESOLVE under the official Docker harness. No verify-but-not-resolve witness exists. Verdict SOUND (advisory; runner re-runs).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9b.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec wrong implementation was found. 13 distinct same-spec wrong impls were run through `adversary weakness`; 12 were REJECTED by the spec (exit 2) and the 1 CANDIDATE (atk_10) is an ungrounded-oracle ECHO whose materialized faithful patch RESOLVES under the official harness (FAIL_TO_PASS test_Function pass, 8/8 PASS_TO_PASS), i.e. a correct alternative implementation, not a spec weakness. Per docs/architecture.md §5 a candidate whose patch resolves must not fail the gate.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9b.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -111,31 +111,22 @@
     Ensures(Result().take(len(name)) == name)
     # post-conditions-end
     # impl-start
-    # body := the ", "-joined operand list (front-recursive fold, built back
-    # to front so each step unfolds `joined` once).
-    body = PSeq(0).take(0)  # type: PSeq[int]
-    i = len(operands)
-    while i > 0:
+    n = len(operands)
+    i = n
+    body = operands[n - 1]  # type: PSeq[int]
+    Assert(len(operands.drop(n - 1)) == 1)
+    Assert(operands.drop(n - 1)[0] == operands[n - 1])
+    while i > 1:
         # invariants-start
-        Invariant(0 <= i and i <= len(operands))
-        Invariant(body == joined(operands.drop(i)))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
+        Invariant(1 <= i and i <= n and n == len(operands))
+        Invariant(body == joined(operands.drop(i - 1)))
         Invariant(MustTerminate(i))
         # invariants-end
-        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:
-        # its head is operands[i-1] and its tail is operands.drop(i).
-        Assert(operands.drop(i - 1)[0] == operands[i - 1])
-        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
-        if i == len(operands):
-            # last operand: a single-element tail, no trailing separator.
-            Assert(len(operands.drop(i - 1)) == 1)
-            body = operands[i - 1]
-        else:
-            # at least two operands remain, so `joined` unfolds once.
-            Assert(len(operands.drop(i - 1)) >= 2)
-            body = operands[i - 1] + sep() + body
+        Assert(operands.drop(i - 2)[0] == operands[i - 2])
+        Assert(operands.drop(i - 2).drop(1) == operands.drop(i - 1))
+        Assert(len(operands.drop(i - 2)) >= 2)
+        body = operands[i - 2] + sep() + body
         i = i - 1
-    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]
-    return result
+    Assert(operands.drop(0) == operands)
+    return name + PSeq(lbracket()) + body + PSeq(rbracket())
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**COMMANDS:** per attack `python -m swebench_unified.adversary weakness nagini sympy__sympy-15345 <f>.py` (log <f>.weak.log), plus `bash scripts/nagini_verify.sh <f>.py` (log <f>.direct.log) to capture the VERIFIER MESSAGE and prove each rejection is a real spec rejection rather than an incidental translation error. Verifications were run 3-at-a-time as concurrent background jobs (each Nagini check spawns a JVM+Z3).

### PER-ATTACK RESULTS (weakness exit / verifier message):
- atk_1.py PREPATCH BUG REPRODUCED (round parens `name+PSeq(40)+body+PSeq(41)` instead of square brackets): exit 2; `atk_1.py:103: Postcondition... Assertion (Result() == rendered(name, operands)) might not hold.` This is the G-DIFF discriminating clause ('(' 40 != '[' 91) firing.
- atk_2.py TRAILING SEPARATOR after the last operand: exit 2; line 103 postcondition failure.
- atk_3.py BOUNDARY/off-by-one, DROPS the last operand (loop starts at len-1): exit 2; line 103 postcondition failure.
- atk_4.py OPERANDS REORDERED (emitted right-to-left; body+sep+operands[i-1]): exit 2; line 103 postcondition failure.
- atk_5.py SEPARATOR WEAKENED to a bare comma PSeq(44), no space: exit 2; line 103 postcondition failure.
- atk_6.py NAME MOVED INSIDE the brackets (`'['+name+body+']'`): exit 2; line 103 postcondition failure.
- atk_7.py DIVERGENCE, endless loop (`i = i - 0`), MustTerminate invariant removed: exit 2; `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` -> MustTerminate(2) genuinely blocks the vacuous-partial-correctness class.
- atk_8.py UNBOUNDED SELF-RECURSION (`return print_lattice_call(name, operands)`): exit 2; `Obligation leak check failed. Callee print_lattice_call might not take all unsatisfied obligations from the caller.`
- atk_9b.py PARTIAL DOMAIN / control-flow effect: correct only at arity 1, for arity>=2 emits ONLY the first operand while keeping the name+'['...']' shape (so every bracket/prefix postcondition still holds and only the full functional one can catch it): exit 2; line 103 postcondition failure. (NOTE: the first encoding atk_9.py used `raise ValueError`, which is outside Nagini's fragment -> `Translation failed: Unsupported builtin function`; that is a MALFORMED attack and NOT evidence, so it was re-encoded as atk_9b.py and atk_9.py is excluded from the submitted list.)
- atk_10.py UNGROUNDED-ORACLE ECHO (`return rendered(name, operands)` -- returns the spec's own pure model): exit 0 CANDIDATE, verifies in 14.2s. FAITHFUL PATCH MATERIALIZED (patch_atk_10.diff, verified to apply at base_commit 9ef28fba with `git apply --check`) and RUN THROUGH THE OFFICIAL HARNESS via `swebench_unified.harness.run_resolve`: **resolved=True, completed=True**, FAIL_TO_PASS {success:[test_Function]}, PASS_TO_PASS 8/8 success, PASS_TO_FAIL/FAIL_TO_FAIL empty (log resolve_atk_10.log). So this candidate is a correct alternative impl (an echo of the reference), NOT a verify-but-wrong witness -> does not break the spec.
- atk_11.py VACUITY CONTROL (`Assert(False)` under the frozen precondition): exit 2; `atk_11.py:114: Assert might fail. Assertion False might not hold.` -> the precondition len(operands)>0 + MustTerminate(2) is SATISFIABLE; the spec is non-vacuous and the other rejections are meaningful.
- atk_12.py CONTROL-FLOW EFFECT, silently DROPS zero-length operands (real `", ".join(["","x"])` == ", x" keeps them): exit 2; line 103 postcondition failure.
- atk_13.py ARITY-DEPENDENT partial correctness: square brackets for arity<=2 but ROUND PARENS for arity>=3 -- aimed exactly at the F2P witness `Max[x, y, z]`: exit 2; line 103 postcondition failure. This is the sharpest attack (it satisfies the spec on the small cases) and the spec still catches it.

**POSITIVE CONTROL:** pos_control.py is a STRUCTURALLY DIFFERENT correct impl (body seeded from the LAST operand, loop bound `i > 1`, no in-loop last/not-last branch, different invariant `body == joined(operands.drop(i-1))`). weakness exit 0 = CANDIDATE, verifies in 16.4s. Because it verifies I also materialized and RAN its faithful patch (patch_pos_control.diff, applies at base_commit): run_resolve -> **resolved=True, completed=True**, F2P test_Function pass, PASS_TO_PASS 8/8 (log resolve_pos_control.log). So the spec admits an independent correct implementation and is not too strong; both verifying impls resolve, which is exactly the verify=>correct direction holding.

A-LEG AUDIT (the G-EQ focus; R/I legs pre-cleared by G-CONF 100000 checks / 0 disagreements). refinement.md tags: B1 R, B2 R, B3 A-reference, B4 I, B5 A-reference. NO KIND-3 STEP, and crucially NO CONSUMED AXIOM AT ALL -- the axioms region is empty (`# (No consumed axioms...)`), meta.json `axioms: []`, and no `@ContractOnly` anywhere, so there is no assumed-postcondition trust point. The changed operation (square-bracket application syntax + ", "-join) is modeled DEEPLY in the pure region (`joined`/`rendered`), which is the right treatment: the thing that changed is not hidden behind an axiom.

A-reference correspondence CHECKED AGAINST THE REAL CALLEE, not just asserted: (i) bundle axiom_check.py re-run -> exit 0 (12 boundary operand lists x 5 names + 3 F2P witnesses + 20000 fuzz, 0 mismatch); (ii) I wrote an independent probe (aleg.py) in a throwaway worktree of sympy at base_commit WITH THE GOLD PATCH APPLIED and compared, for 16 real lattice expressions, the model formula against the live printer: `joined_model(ops) == p.stringify(e.args, ", ")` for every case (A-reference 1) and `name+"["+joined+"]" == p.doprint(e)` for every case (A-reference 2), 0 mismatches -- incl. nested `Max[z, Min[x, y]]`, spaces `Max[z, x + 1, y - 2]`, arity 6, and `Min[1/2, x^(1/2)]`.

F2P assertion reproduced verbatim: `mcode(Max(x,y,z)*Min(y,z)) == "Max[x, y, z]*Min[y, z]"`, and the issue's case `mcode(Max(x,2)) == 'Max[2, x]'`. Gold-patched source confirmed to be exactly `return "%s[%s]" % (mfunc, self.stringify(expr.args, ", "))` reached via `_print_MinMaxBase = _print_Function`, matching mapping.md §1/§3 line citations (str.py:35-36 stringify = sep.join([...])). Operand-ORDER claim (B2, the model must NOT reorder) checked live: `Max(x,2).args` == ('2','x') and the printed text is `Max[2, x]` -- the canonicalisation happens UPSTREAM of the printer, so taking `operands` as given in args order is faithful, and atk_4 confirms the spec still rejects an impl that reorders them itself.

Precondition domain (`len(operands) > 0`) checked live for over-strength: `Max()` raises ValueError("The Max/Min functions must have arguments") and `Max(x)` collapses to a bare Symbol, so no real MinMaxBase node ever reaches the printer with 0 operands -- the precondition excludes no reachable input.

**CONCLUSION:** 13 admissible distinct attacks run to completion (partial-domain, boundary/off-by-one, reorder, separator, delimiter, name-placement, two divergence classes, arity-dependent, zero-length-operand control-flow effect, ungrounded-oracle echo, vacuity control), the prepatch bug reproduced and rejected, every rejection traced to a real spec message (line 103 functional postcondition or the MustTerminate obligation leak) rather than a translation error, the vacuity control fails as it must, and the only two verifying same-spec impls both RESOLVE under the official Docker harness. No verify-but-not-resolve witness exists. Verdict SOUND (advisory; runner re-runs).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE SETUP.** Worktree = base_commit 9ef28fba5b4d6d0168237c9c005a550e6dc27d81 with the gold patch APPLIED (verified byte-equal to data/swe_bench_verified/test.jsonl `patch` for this instance: known_functions gets "Max"/"Min" -> [(lambda *x: True, "Max"/"Min")], and `_print_MinMaxBase = _print_Function`). Confirmed on the patched tree: mcode(Max(x,2))=='Max[2, x]', mcode(Max(x,y,z)*Min(y,z))=='Max[x, y, z]*Min[y, z]' (the F2P assertion). A second worktree at bare base_commit gives 'Max(2, x)' / 'Max(x, y, z)*Min(y, z)' -- ROUND parens -- so I was careful NOT to score the patch delta itself as a divergence.

**WHAT THE SPEC CLAIMS.** print_lattice_call(name, operands) with Requires(len(operands)>0) and MustTerminate(2); Ensures Result() == rendered(name,operands) = name + PSeq(91 '[') + joined(operands) + PSeq(93 ']'), where joined is the front-recursive ", "-join (no trailing separator); plus the redundant-but-consistent clauses len(Result())>len(name), Result()[len(name)]==91, Result()[len(Result())-1]==93, Result().take(len(name))==name.

**REAL CALLEE.** MCodePrinter.`_print_Function` (sympy/printing/mathematica.py:96-102) returns "%s[%s]" % (mfunc, self.stringify(expr.args, ", ")) on the recognised branch and func.`__name__` + "[%s]" % stringify(args, ", ") on the fallback; StrPrinter.stringify (str.py:35-36) is exactly sep.join([parenthesize(item, level) for item in args]). Post-patch MinMaxBase dispatches here (checked MCodePrinter.`_print_MinMaxBase` is MCodePrinter.`_print_Function` -> True; no `_print_Max`/`_print_Min` shadows it). So the real shape IS name + '[' + ', '.join(rendered_operands) + ']'.

### EVIDENCE RUN (all against the PATCHED worktree).
1. Bundle conformance_check.py: exit 0, 100000 inputs, 0 disagreements (seed 153450).
2. Bundle axiom_check.py: exit 0 (joined/rendered deep models == real ', '.join and the name[body] assembly; 12 boundary lists x 5 names + 3 F2P witnesses + 20000 fuzz).
3. INDEPENDENT probe I wrote (g2_indep.py) that does NOT re-derive operand strings the way the bundle does -- it monkeypatches StrPrinter.stringify to RECORD the exact per-operand rendered strings and the exact separator the real callee actually passes, then asserts real_output == name + '[' + ', '.join(recorded_operands) + ']' and that the contract-stripped model impl reproduces it code-point-for-code-point. 127236 MinMaxBase renderings through the printer's PUBLIC entry (doprint), 0 failures. Also asserted the recorded separator is literally ', ' every time (never ',' or ', ' variants).
Stressed exactly the places a join spec usually drifts: operands whose own rendered form already contains ', ' (Max(x,2) as an inner arg) and '['/']'; symbol names containing the separator (Symbol('a, b')) and brackets (Symbol('c[d]')); the EMPTY symbol name (operands render to '' -> real gives 'Max[,]', model matches, so the 'no trailing separator' clause is pinned on a case where a sloppy join would be indistinguishable otherwise); non-ASCII (Symbol('αé中')) and non-BMP/astral (Symbol('q\U0001F600')) names -- relevant because the model's carrier is code POINTS, and astral chars would break a UTF-16-code-unit reading; arity 1 through 9; duplicate operands; order-sensitivity (F(x,y) vs F(y,x)).

Ran across 7 printer configurations, not just the default: precision=5, full_prec=True, full_prec=False, order='lex', allow_unknown_functions=True, and user_functions overrides both as a bare string ({'Max':'MyMax'}) and as a condition list ({'Max':[(lambda *a: len(a)>2,'BigMax')]}) -- i.e. cases where mfunc is NOT func.`__name__`. The spec takes `name` as a given PSeq[int] rather than hardcoding "Max"/"Min", so it stays faithful under those overrides; a spec that had pinned the literal name would have broken here and did not.
4. Table-wide sweep: 7440 in-domain applications over EVERY known_functions entry plus unrecognised names (the fallback branch func.`__name__` + "[...]"), arities 1-8 for the variadic lattice entries and 1 for the unary entries -- 0 mismatches. Note the unary table entries raise TypeError when handed >1 arg (pre-existing repo quirk, `lambda x: True` called with *args); that is outside the modeled recognised-lattice domain and is not a spec defect.

DOMAIN / PRECONDITION HONESTY. Requires(len(operands)>0) is not a too-strong dodge: genuine Max()/Min() raise ValueError('The Max/Min functions must have arguments.') upstream, so a zero-operand lattice application never reaches the printer. (An unevaluated Function('Max')() does reach it and yields 'Max[]', which the model simply does not cover -- excluded domain, not a wrong claim, and it is not the changed behavior.) MustTerminate is justified: the real path is ', '.join over a finite tuple plus one %-format, always answers.

**OPERAND ORDER.** The spec deliberately does NOT reorder operands, and mapping.md attributes ordering to MinMaxBase.`__new__`/`_argset`/ordered upstream of the printer -- confirmed: mcode(Max(x,2)) is 'Max[2, x]' because SymPy canonicalised the args to (2, x) before printing, identical pre/post patch. Modeling the printer as order-preserving is correct.

G-DIFF / NON-VACUITY (guards against the FAITHFUL-but-useless failure mode). Pinned Nagini: model.py -> 'Verification successful' (22.8s). model_prepatch.py, which is same-spec (adversary same-spec -> exit 0) and differs only by emitting PSeq(40)/PSeq(41) round parens, -> 'Verification failed: Postcondition... Assertion (Result() == rendered(name, operands)) might not hold.' So the spec genuinely senses the patch's observable content ('[' vs '(') and is not vacuous.

**CONCLUSION.** I could not construct any input in the spec's stated domain (len(operands) >= 1) on which the modeled function disagrees with the real patched MCodePrinter.`_print_Function`. The spec is not too strong: its precondition excludes only inputs the repo itself makes unreachable, and its postcondition is exactly the real callee's output shape under the documented str<->PSeq[int] code-point abstraction. Verdict FAITHFUL; no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE:** no relaxation in this bundle. meta.json has no `relaxed_leakage` key (walked the whole dict for /relax/i -- no hit) and there is no RELAXED_LEAKAGE.md in the bundle dir; meta.json gates['G-LEAK'].status == 'pass' (mode strict, detail 'spec view clean', data.failures == []). So this is an ordinary strict leakage judgement, not an inherited disposition. No file in the bundle addresses me or prescribes a verdict: ran leakage.reviewer_directed() over model.py, refinement.md, mapping.md and verdict.md -- all four return [] (no addresses-the-reviewer, prescribes-the-verdict, or recording-convention hit). verdict.md does carry a prior 'Role 4... pass (agent: NO-LEAKAGE)' section, but it is a backfilled record of an earlier run (trailing comment: generated by scripts/backfill_verdict_md.py), not an instruction to me; I re-derived everything below independently and my verdict is my own measurement, not its echo.

**WHAT I JUDGED:** the projected spec view, not the raw file -- markers.spec_view(model.py, nagini backend). It is the module docstring + imports + axioms region (a comment-only 'no consumed axioms' note) + pure region (lbracket=91, rbracket=93, sep=PSeq(44,32), joined, rendered) + print_lattice_call signature + pre-conditions (len(operands)>0, MustTerminate(2)) + post-conditions (5 Ensures); the impl region is replaced by '...  # implementation elided'. So the loop, the back-to-front fold and the bridging Asserts are NOT consumer-visible and cannot leak. Confirmed the spec region is byte-identical: `adversary same-spec nagini sympy__sympy-15345` on a copy of the bundle model.py -> exit 0 ('SAME'), and on model_prepatch.py -> exit 0 too (the twin shares the spec byte-for-byte).

MECHANICAL SCREEN (re-run, not trusted from meta.json): leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Component-wise: (L1) no diff marker from `_PY_DIFF_MARKERS` in the view; none of the three gold changed lines ('"Max": [(lambda *x: True, "Max")],', '"Min": [(lambda *x: True, "Min")],', '`_print_MinMaxBase` = `_print_Function`') appears normalized in the view. (L2) neither 'sympy/printing/mathematica.py' nor the dotted 'sympy.printing.mathematica' occurs. (L2/L5) the only distinctive changed symbol is 'print_Function' (underscore-stripped, len>=4); it is absent from every spec-view identifier and from all comments/docstrings. (L3) no `_NARRATION` word ('bug', 'fix', 'wrong', 'incorrectly', 'previously', 'patched',...) in any comment or string -- notable given my own memory note that measure/justification prose usually trips this vocabulary; this docstring is written as desired behaviour ('Behaviour under specification (stated as desired behaviour, not as an edit)') and stays clean.

SUBSTANTIVE RECONSTRUCTION TEST (the part the mechanical screen cannot do). Grepped the view for the edit-mechanism vocabulary a solver would need to localize the fix: 'Max', 'Min', 'MinMaxBase', 'known_functions', '`_print_Function`', '`_print_MinMaxBase`', 'stringify', 'mathematica', 'MCodePrinter', 'StrPrinter', 'parenthesize', '%s[%s]', 'expr', 'args', 'lambda', 'dispatch', 'alias', 'registr', 'subclass', 'base class', 'inherit', 'table', '.py', 'sympy/' -- ALL zero occurrences.

Also checked the hints_text-only DIAGNOSIS vocabulary specifically (hints say the known-functions table is keyed lowercase, Max/Min are absent from it, and lowercase `max` blows up in core/relational.py): 'known function(s)', 'table', 'lowercase', 'capitalization', 'unevaluated', 'builtin', 'relational', 'compare' -- all absent. Nothing in the view routes a reader to the file, the table, the printer method, or the `_print_MinMaxBase = _print_Function` aliasing trick.

The view names the abstract operation ('a recognised n-ary lattice operator', 'print_lattice_call') using domain vocabulary that is NOT in the patch at all (grep 'lattice' in patch.diff -> 0 hits; LatticeOp is a pre-existing base in sympy/core/operations.py:369, unmodified by the gold), so the identifier describes the modeled behaviour rather than echoing a patched symbol.

**THE DISCRIMINATOR IS VERBATIM PUBLIC.** The change's observable content is the application delimiter: square brackets post vs round parens pre. The problem_statement states both sides literally -- it contains 'Max[x,2]' as the expected output ('which is valid Mathematica code') and 'Max(2, x)' as the actual. So the view's square-bracket clauses (Ensures(Result()[len(name)] == lbracket()), last char == rbracket(), 'Round parentheses are NOT used as the application delimiter') restate a fact the solver already has. The ', ' separator and the operand multiset are likewise readable straight off the public 'Max(2, x)'. Confirmed the clause is load-bearing rather than decorative: model_prepatch.py shares the spec byte-for-byte and FAILS the pinned postcondition under the pinned verifier -- `nagini_verify.sh model_prepatch.py` -> exit 1, 'Postcondition of print_lattice_call might not hold. Assertion (Result() == rendered(name, operands)) might not hold' at line 103 (the '(' = 40 vs '[' = 91 sensing). The gold model verifies: `nagini_verify.sh model.py` -> exit 0, 'Verification successful' (10.1s).

ONE ITEM I CHECKED HARDEST -- 'minimum'. I diffed every alphabetic word in the view against the problem_statement. The single content word that is beyond the PS is the minimum half of 'e.g. the running maximum or minimum of a list of terms': the PS mentions only Max, while the hidden F2P (test_Function: mcode(Max(x,y,z)*Min(y,z)) == 'Max[x, y, z]*Min[y, z]') also exercises Min. I judged this NOT a leak on three grounds.

(1) It is a parenthetical 'e.g.' gloss on the abstract class 'n-ary lattice operator (an associative/commutative reduction over its operands)'; the words are the generic English 'maximum'/'minimum', never the SymPy identifiers 'Max'/'Min' -- both capitalized forms are absent from the view, so the symbol-collision rule is not merely dodged on case, the symbols genuinely do not appear.

(2) It localizes nothing: it names neither the file, the registration table, nor the printer method, so a solver holding it still has the entire edit-site search ahead of them.

(3) It is independently derivable from the public repo the solver already has -- Max and Min are siblings on MinMaxBase (miscellaneous.py:340, 645, 765) under a 'MINIMUM and MAXIMUM' banner, and Max's own public docstring carries 'See Also / Min: find minimum values'. Anyone reading the class the PS names finds the min counterpart immediately; the spec view is not the channel that discloses it. It is also the honest way to state the modeled behaviour: the spec is about the n-ary reduction operator class, and writing it as max-only would make the spec NARROWER than the behaviour the twin patch implements -- a faithfulness defect traded for a cosmetic leakage win.

What I confirmed vs. asserted: I re-ran the screen, same-spec (both twins), and both verifier runs myself rather than reading meta.json's recorded statuses; the repo-derivability claims come from a fresh worktree at base_commit 9ef28fba (git worktree add --detach under /tmp; bundle untouched, nothing written outside /tmp). VERDICT: NO-LEAKAGE -- the spec view discloses nothing about the gold edit beyond the problem_statement, and the one word beyond it is a non-localizing generic gloss that the public repo already yields.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
