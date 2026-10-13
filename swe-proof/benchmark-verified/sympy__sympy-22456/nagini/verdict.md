# P2 adversarial audit — sympy__sympy-22456

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_prepatch.py`, `atk_2_oracle_echo.py`, `atk_3_noadvance.py`, `atk_4_partial_domain.py`, `atk_5_boundary_offbyone.py`, `atk_6_nul_truncation.py`, `atk_7_descent_dropslast.py`, `atk_8_reachability_control.py`, `atk_9_duplicate.py`, `atk_10_identity.py`, `atk_11_targeted_divergence.py`, `atk_12_guarded_echo.py`, +1 more |

**Non-vacuity.** The positive control `atk_0_positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,11 +106,11 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
-    n = len(s.text)
+    # PRE-FIX reconstruction: the token rebuilds through the generic positional
+    # constructor, which can only source the text payload from the positional
+    # arguments. The argument list is empty (arg_count == 0), so the generic
+    # rebuild has nothing to populate the text from and produces an empty text.
+    n = arg_count(s)
     rebuilt_text = []  # type: List[int]
     i = 0
     while i < n:
@@ -118,22 +118,11 @@
         Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
         Invariant(Acc(list_pred(rebuilt_text)))
         Invariant(0 <= i and i <= n)
-        Invariant(n == len(s.text))
         Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         c = s.text[i]
-        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
         rebuilt_text = rebuilt_text + [c]
         i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    return Atomic(rebuilt_text)
     # impl-end
```

Attack 2 — `atk_2_oracle_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,34 +106,8 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
-    n = len(s.text)
-    rebuilt_text = []  # type: List[int]
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
-        Invariant(Acc(list_pred(rebuilt_text)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(s.text))
-        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        c = s.text[i]
-        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
-        rebuilt_text = rebuilt_text + [c]
-        i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    # UNGROUNDED-ORACLE ECHO: the answer is taken from this very function, so
+    # the postcondition is discharged by ASSUMING it at the call site. Nothing
+    # about the text is ever established.
+    return rebuild_from_args(s)
     # impl-end
```

Attack 3 — `atk_3_noadvance.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,10 +106,9 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # DIVERGENCE: the loop counter never advances, so for any non-empty text
+    # this never delivers a token. Under PARTIAL correctness the postcondition
+    # is still provable on the (unreachable) exit path.
     n = len(s.text)
     rebuilt_text = []  # type: List[int]
     i = 0
@@ -120,20 +119,9 @@
         Invariant(0 <= i and i <= n)
         Invariant(n == len(s.text))
         Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        c = s.text[i]
-        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
-        rebuilt_text = rebuilt_text + [c]
-        i = i + 1
+        i = i + 0
     Assert(i == n)
     Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    return Atomic(rebuilt_text)
     # impl-end
```

Attack 4 — `atk_4_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,34 +106,26 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # PARTIAL DOMAIN: copies at most three code points, so it is correct only
+    # for texts of length <= 3 and silently truncates every longer text.
     n = len(s.text)
+    m = n
+    if m > 3:
+        m = 3
     rebuilt_text = []  # type: List[int]
     i = 0
-    while i < n:
+    while i < m:
         # invariants-start
         Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
         Invariant(Acc(list_pred(rebuilt_text)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(s.text))
+        Invariant(0 <= i and i <= m)
+        Invariant(m <= n and n == len(s.text))
         Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
-        Invariant(MustTerminate(n - i + 1))
+        Invariant(MustTerminate(m - i + 1))
         # invariants-end
         c = s.text[i]
         Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
         rebuilt_text = rebuilt_text + [c]
         i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    return Atomic(rebuilt_text)
     # impl-end
```

Attack 5 — `atk_5_boundary_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,34 +106,23 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # BOUNDARY: the loop stops one element short, so the final code point of
+    # every non-empty text is dropped.
     n = len(s.text)
     rebuilt_text = []  # type: List[int]
     i = 0
-    while i < n:
+    while i < n - 1:
         # invariants-start
         Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
         Invariant(Acc(list_pred(rebuilt_text)))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(s.text))
         Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         c = s.text[i]
         Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
         rebuilt_text = rebuilt_text + [c]
         i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    return Atomic(rebuilt_text)
     # impl-end
```

Attack 6 — `atk_6_nul_truncation.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,10 +106,9 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # CONTROL-FLOW EFFECT: C-string semantics. The copy stops at the first NUL
+    # code point and delivers the truncated prefix, so any text containing a
+    # NUL is silently cut short.
     n = len(s.text)
     rebuilt_text = []  # type: List[int]
     i = 0
@@ -120,20 +119,13 @@
         Invariant(0 <= i and i <= n)
         Invariant(n == len(s.text))
         Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         c = s.text[i]
+        if c == 0:
+            return Atomic(rebuilt_text)
         Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
         rebuilt_text = rebuilt_text + [c]
         i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    return Atomic(rebuilt_text)
     # impl-end
```

Attack 7 — `atk_7_descent_dropslast.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,34 +106,29 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # MEASURE-LANE DESCENT: the precondition MustTerminate(len(s.text) + 2)
+    # admits a self-call on a STRICTLY SMALLER token. Descend on text[:n-1] and
+    # return that answer directly, so the last code point is never restored.
     n = len(s.text)
-    rebuilt_text = []  # type: List[int]
+    if n == 0:
+        empty = []  # type: List[int]
+        return Atomic(empty)
+    head = []  # type: List[int]
     i = 0
-    while i < n:
+    while i < n - 1:
         # invariants-start
         Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
-        Invariant(Acc(list_pred(rebuilt_text)))
-        Invariant(0 <= i and i <= n)
+        Invariant(Acc(list_pred(head)))
+        Invariant(0 <= i and i <= n - 1)
         Invariant(n == len(s.text))
-        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
+        Invariant(ToSeq(head) == ToSeq(s.text).take(i))
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         c = s.text[i]
         Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
-        rebuilt_text = rebuilt_text + [c]
+        head = head + [c]
         i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    small = Atomic(head)  # type: Atomic
+    Assert(len(small.text) == n - 1)
+    return rebuild_from_args(small)
     # impl-end
```

Attack 8 — `atk_8_reachability_control.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,6 +106,11 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
+    # REACHABILITY CONTROL: the frozen body with Assert(False) in front. If this
+    # FAILS to verify, the entry of rebuild_from_args is on a FEASIBLE path, so
+    # the other attacks' verdicts are genuine and not the vacuity of an
+    # infeasible precondition.
+    Assert(False)
     # The reconstruction operation yields the very same token (its result is the
     # original object), so it carries the original text regardless of how many
     # positional arguments there are. Materialise a fresh carrier holding
```

Attack 9 — `atk_9_duplicate.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,10 +106,7 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # WRONG PAYLOAD: the rebuilt token carries the text TWICE.
     n = len(s.text)
     rebuilt_text = []  # type: List[int]
     i = 0
@@ -119,21 +116,12 @@
         Invariant(Acc(list_pred(rebuilt_text)))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(s.text))
-        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
+        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i) + ToSeq(s.text).take(i))
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         c = s.text[i]
-        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
+        rebuilt_text = rebuilt_text + [c]
         rebuilt_text = rebuilt_text + [c]
         i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    return Atomic(rebuilt_text)
     # impl-end
```

Attack 10 — `atk_10_identity.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,34 +106,8 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
-    n = len(s.text)
-    rebuilt_text = []  # type: List[int]
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
-        Invariant(Acc(list_pred(rebuilt_text)))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(s.text))
-        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        c = s.text[i]
-        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
-        rebuilt_text = rebuilt_text + [c]
-        i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    # IDENTITY RECONSTRUCTION: return the very same token. This is EXACTLY what
+    # the gold patch's `@property def func(self): return lambda: self` does, so
+    # it is the most faithful possible refinement of the real changed callee.
+    return s
     # impl-end
```

Attack 11 — `atk_11_targeted_divergence.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,10 +106,11 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # CONTROL-FLOW EFFECT / TARGETED DIVERGENCE: the copy is correct except that
+    # on the code point 102 ('f', the first character of the F2P text 'foobar')
+    # it enters an inner loop that never advances, so it never delivers a token
+    # for that text. Probes whether the delivery obligation is enforced on EVERY
+    # path or only on the main copy loop.
     n = len(s.text)
     rebuilt_text = []  # type: List[int]
     i = 0
@@ -120,20 +121,17 @@
         Invariant(0 <= i and i <= n)
         Invariant(n == len(s.text))
         Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         c = s.text[i]
+        j = 0
+        while j < 1 and c == 102:
+            Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
+            Invariant(Acc(list_pred(rebuilt_text)))
+            Invariant(j == 0)
+            j = j + 0
         Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
         rebuilt_text = rebuilt_text + [c]
         i = i + 1
-    Assert(i == n)
-    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    return Atomic(rebuilt_text)
     # impl-end
```

Attack 12 — `atk_12_guarded_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,6 +106,13 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
+    # UNGROUNDED-ORACLE ECHO, GUARDED. On a non-empty text the answer is taken
+    # from this very function applied to THIS SAME token (no descent), so the
+    # postcondition would be discharged by assuming it. The guard is feasible
+    # (non-empty texts are admissible), so this is not the vacuity of an
+    # infeasible branch.
+    if len(s.text) > 0:
+        return rebuild_from_args(s)
     # The reconstruction operation yields the very same token (its result is the
     # original object), so it carries the original text regardless of how many
     # positional arguments there are. Materialise a fresh carrier holding
```

Attack 13 — `atk_13_samesize_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -106,34 +106,30 @@
     Ensures(ToSeq(Result().text) == ToSeq(s.text))
     # post-conditions-end
     # impl-start
-    # The reconstruction operation yields the very same token (its result is the
-    # original object), so it carries the original text regardless of how many
-    # positional arguments there are. Materialise a fresh carrier holding
-    # exactly the original text.
+    # SAME-SIZE ECHO: build a fresh token carrying exactly the original text,
+    # then take the answer from a self-call on THAT token. The copy has the SAME
+    # length as the original, so the descent is not strictly smaller and the
+    # recursion is unbounded in the refined code. This probes whether the
+    # delivery measure is keyed on the payload SIZE (sound) or merely on the
+    # object identity (unsound).
     n = len(s.text)
-    rebuilt_text = []  # type: List[int]
+    copy_text = []  # type: List[int]
     i = 0
     while i < n:
         # invariants-start
         Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
-        Invariant(Acc(list_pred(rebuilt_text)))
+        Invariant(Acc(list_pred(copy_text)))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(s.text))
-        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
-        # At most `n - i` passes remain; `i` rises by exactly one each pass and
-        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
-        # keeps it positive on the final pass. The reproduction completes.
+        Invariant(ToSeq(copy_text) == ToSeq(s.text).take(i))
         Invariant(MustTerminate(n - i + 1))
         # invariants-end
         c = s.text[i]
         Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
-        rebuilt_text = rebuilt_text + [c]
+        copy_text = copy_text + [c]
         i = i + 1
-    Assert(i == n)
     Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
-    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
-    result = Atomic(rebuilt_text)  # type: Atomic
-    Assert(result.text is rebuilt_text)
-    Assert(ToSeq(result.text) == ToSeq(s.text))
-    return result
+    twin = Atomic(copy_text)  # type: Atomic
+    Assert(ToSeq(twin.text) == ToSeq(s.text))
+    return rebuild_from_args(twin)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22456.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An atomic string-valued symbolic token carries a single defining payload (its
  text) that is deliberately held OFF its positional-argument list: the token
  has an empty argument tuple. Every symbolic object must nonetheless satisfy
  ARGUMENT INVARIANCE — rebuilding the object by applying its reconstruction
  operation to its own positional arguments yields an object equal to the
  original:

      rebuild(positional-arguments-of(t)) == t

  Because the defining text is not among the positional arguments (the argument
  count is zero), a faithful reconstruction must reproduce the original text
  WITHOUT reading it from the (empty) argument list. The discriminating case the
  contract pins: for a token with arbitrary — including non-empty — text, the
  reconstruction from the empty argument list must still carry exactly the
  original text, so that the rebuilt token equals the original. A reconstruction
  that can only source the text from the positional arguments would, on the
  empty list, lose every non-empty text and break the invariance.

  The invariance is a claim about EVERY reconstruction, not only about the ones
  that happen to hand an answer back: the reconstruction is TOTAL — for every
  token it must run to completion and DELIVER a rebuilt token. A reconstruction
  that never delivers one (it re-enters itself on the same token, or spins
  without making progress) does not satisfy the invariance, however its result
  would have been constrained had it arrived. Delivery is bounded by the size of
  the payload being reproduced, so a reconstruction that descends on a STRICTLY
  SMALLER token before assembling its answer is admissible.

The token's defining text is modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); equality of two tokens is equality of that text,
carried by `PSeq[int]` via `ToSeq`. The positional-argument list is modelled by
its length alone (it is empty for this atomic token, and the reconstruction
consumes no positional element).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Atomic:
    """An atomic string-valued token; only its defining `text` payload is
    modelled (the single quantity token equality depends on)."""

    def __init__(self, text: List[int]) -> None:
        Requires(Acc(list_pred(text)))
        # Building a carrier completes: it hands the token back.
        Requires(MustTerminate(1))
        Ensures(Acc(self.text) and self.text is text)  # type: ignore
        Ensures(Acc(list_pred(self.text)))  # type: ignore
        Ensures(ToSeq(self.text) == Old(ToSeq(text)))  # type: ignore
        self.text = text

# axioms-start
# (no @ContractOnly axioms: the operation that changed — how an atomic token
# reconstructs itself from its arguments — is modelled DEEPLY, as a direct
# text-preserving rebuild. No unchanged opaque callee is consumed inside the
# contract. See refinement.md / mapping.md.)
# axioms-end

# pure-start
@Pure
def arg_count(s: Atomic) -> int:
    """The number of positional arguments of the token. The defining text is
    held OFF the argument list, so an atomic string token has zero positional
    arguments."""
    Requires(Acc(s.text, 1 / 4) and Acc(list_pred(s.text), 1 / 4))
    Ensures(Result() == 0)
    return 0
# pure-end

def rebuild_from_args(s: Atomic) -> Atomic:
    # pre-conditions-start
    # `s` is read-only: reconstruction never mutates the original (fractional
    # permission on both the field reference and its list contents).
    Requires(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
    # TOTALITY. Every postcondition below is claimed of EVERY admissible call,
    # not merely of the calls that happen to reach a return: the reconstruction
    # must run to completion and DELIVER a token. The delivery level is bounded
    # by the size of the payload being reproduced, so a reconstruction that
    # descends on a STRICTLY SMALLER token is admissible, while one that
    # re-enters itself on this very token — or loops without advancing — is not,
    # and cannot borrow this contract to stand in for its own answer.
    Requires(MustTerminate(len(s.text) + 2))
    # pre-conditions-end
    # post-conditions-start
    # The original token is preserved (read-only).
    Ensures(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
    # A fresh token is produced (full permission on the reconstruction).
    Ensures(Acc(Result().text) and Acc(list_pred(Result().text)))
    # The token's positional-argument list is empty: the reconstruction draws
    # from zero positional arguments.
    Ensures(arg_count(s) == 0)
    # ARGUMENT INVARIANCE: rebuilding the token from its (empty) positional
    # arguments yields a token EQUAL to the original — i.e. carrying EXACTLY the
    # original text, element for element, even when that text is non-empty.
    # This is the discriminating clause: a reconstruction that could only source
    # the text from the empty argument list would lose any non-empty text.
    Ensures(ToSeq(Result().text) == ToSeq(s.text))
    # post-conditions-end
    # impl-start
    # The reconstruction operation yields the very same token (its result is the
    # original object), so it carries the original text regardless of how many
    # positional arguments there are. Materialise a fresh carrier holding
    # exactly the original text.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        # At most `n - i` passes remain; `i` rises by exactly one each pass and
        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
        # keeps it positive on the final pass. The reproduction completes.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    Assert(i == n)
    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
    result = Atomic(rebuilt_text)  # type: Atomic
    Assert(result.text is rebuilt_text)
    Assert(ToSeq(result.text) == ToSeq(s.text))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-22456/nagini. 13 distinct same-spec wrong impls + positive control + prepatch, all machine-checked; ALL 13 REJECTED by the frozen spec. Verdict SOUND.

Attacks built by splicing ONLY the impl region of the frozen model.py (mk.py / mk2.py); axioms/@Pure/Requires/Ensures byte-identical. All 14 files confirmed same-spec (adversary same-spec exit 0) AND admissible (variant_scope.unsound_evasions == [] for every file: no new @ContractOnly / axiom / assumption token).

COMMAND FORM (every attack): python -m swebench_unified.adversary weakness nagini sympy__sympy-22456 <path>
Run 3-at-a-time as concurrent background jobs (each Nagini check spawns JVM+Z3); logs at w_<name>.log.

| attack | class | observed |
|---|---|---|
| atk_0_positive_control.py | frozen impl verbatim | CANDIDATE, verifies 12.8s, exit 0 -> patch materialized -> RESOLVED (see below) |
| atk_1_prepatch.py | PREPATCH BUG (generic positional rebuild over the empty arg list) | exit 2, does not verify -> spec senses the pre-fix bug |
| atk_2_oracle_echo.py | UNGROUNDED-ORACLE ECHO (`return rebuild_from_args(s)`) | exit 2, does not verify |
| atk_3_noadvance.py | DIVERGENCE (loop counter never advances) | exit 2, does not verify |
| atk_4_partial_domain.py | PARTIAL DOMAIN (correct only for len<=3) | exit 2, does not verify |
| atk_5_boundary_offbyone.py | BOUNDARY (drops last code point) | exit 2, does not verify |
| atk_6_nul_truncation.py | CONTROL-FLOW EFFECT (C-string early return at NUL) | exit 2, does not verify |
| atk_7_descent_dropslast.py | MEASURE-LANE DESCENT (recurse on text[:n-1], keep smaller answer) | exit 2, does not verify |
| atk_8_reachability_control.py | REACHABILITY CONTROL (Assert(False) + frozen body) | exit 2, does NOT verify -> entry path FEASIBLE, so the rejections are genuine, not the vacuity of an infeasible precondition |
| atk_9_duplicate.py | WRONG PAYLOAD (text emitted twice) | exit 2, does not verify |
| atk_10_identity.py | `return s` (literally gold's `lambda: self`) | exit 2: "Postcondition ... insufficient permission to access Result().text" |
| atk_11_targeted_divergence.py | TARGETED DIVERGENCE (inner non-advancing loop only on code point 102='f', first char of F2P 'foobar') | exit 2: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." |
| atk_12_guarded_echo.py | GUARDED SELF-CALL on the SAME token (feasible guard len>0) | exit 2: "Obligation leak check failed. Callee rebuild_from_args might not take all unsatisfied obligations from the caller." |
| atk_13_samesize_echo.py | SAME-SIZE ECHO (self-call on a freshly built EQUAL-length twin -> not strictly smaller) | exit 2: same obligation-leak rejection -> the delivery measure is keyed on the payload SIZE, not on object identity |

**PRIOR-PASS COUNTEREXAMPLES RE-ENCODED AND NOW REJECTED.** verdict.md records an earlier BROKEN on atk_2_oracle_echo (self-call verified because the spec carried NO MustTerminate, only partial correctness) and a second candidate atk_9_divergent_noadvance. The frozen model.py has since been repaired exactly as that pass recommended: it now imports nagini_contracts.obligations, carries method-level `Requires(MustTerminate(len(s.text) + 2))` and `Invariant(MustTerminate(n - i + 1))`. I re-encoded BOTH (atk_2_oracle_echo, atk_3_noadvance) and both now FAIL to verify. I also probed the three residual escape lanes that repair could have left open -- a guarded self-call (atk_12), a same-size descent that evades a size-keyed measure (atk_13), and a divergence hidden on one data-dependent path rather than in the main loop (atk_11) -- and Nagini rejects all three with obligation-leak errors. MustTerminate is enforced at the method level and on EVERY path, per MEMORY (loop invariants alone do not reject a diverging rival; the method level is what does).

THE ONE CANDIDATE, RESOLVE EXECUTED (protocol step 2). atk_0_positive_control (the frozen impl) is the only file that verifies, so its faithful refined patch was materialized and RUN through the official harness. This is the load-bearing G-EQ measurement here, because atk_10_identity proves the spec REJECTS gold's own `return s`: the postcondition demands FULL permission on Result().text while the precondition hands out only 1/2 on s, so the verifying impl is necessarily a FRESH text-preserving COPY, not gold's identity. If that copy did not resolve, the bundle would be broken.

Patch generated mechanically from sympy/codegen/ast.py at base_commit a3475b3f9ac662cd425157dd3bdb93ad7111c090 with asserted anchor lines, applying gold's SAME three structural edits (the `Expr, Atom` import; `class String(Atom, Token)`; `kwargs` returning {} and `@property def func` at gold's exact insertion point after `_sympystr`), differing ONLY in func's body -- the modeled operation (`rebuild_from_args` <-> `String.func(*String.args)`, mapping.md §1) -- refining `Atomic(rebuilt_text)` one-for-one as a fresh same-class carrier holding the element-wise-copied text. `git apply --check` clean. Command: python resolve.py patch_atk_0_positive_control.diff (calls harness.run_resolve("sympy__sympy-22456", <patch>, run_id="sbu-geq-7c293ecp-patch_atk_0_positive_control")).

RESULT: {"resolved": true, "completed": true, "note": "resolved"} -- FAIL_TO_PASS test_String PASSES, PASS_TO_PASS 29/29 pass. So the verifying impl's faithful patch DOES resolve: no verify-but-wrong witness. NOT a spec weakness -- per architecture.md §6 a candidate whose patch resolves is a correct alternative implementation (an echo of the reference solution), and must not fail the gate. GOLD CONTROL: patch_gold_control.diff (`lambda: self`) -> resolved true, completed true, F2P 1/1, P2P 29/29 -- confirms the oracle lane itself is live and discriminating.

### A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's).
refinement.md legs: step 1 R (String -> single facet text; str <-> List[int] code points; Token.`__eq__` = same class + all `__slots__` equal, which for the single-slot String reduces to text equality -- verified against sympy/codegen/ast.py:255 in a base-commit checkout), step 2 R (args modeled by length; String.`__slots__`=('text',), not_in_args=['text'] so Basic.`__new__` gets no positional args -> args==() -- confirmed in source), step 3 A-REFERENCE, step 4 R. NO kind-3 step, and meta.json axioms==[] with one deep_model_references entry -- consistent: the changed op is modeled deeply, nothing is A-consumed, so there is no axiom trust point. Confirmed no @ContractOnly anywhere in model.py.

A-REFERENCE CORRESPONDENCE, EXECUTED. axiom_check.py run on a gold-patched base-commit tree: exit 0, "G-AX OK ... sound on 1 F2P + 12 boundary + 20000 fuzz texts". NEGATIVE CONTROL at the unpatched base commit: fails on the first case with TypeError: No value for 'text' given and attribute has no default (sympy/codegen/ast.py:237) -- exactly the pre-fix mechanism mapping.md §1 documents, so the witness has real discriminating power and is not vacuous. Mechanism reproduced standalone (mech_copy.py): gold identity and the copy rebuild BOTH satisfy func(*args)==st, and the copy preserves the subclass via self.`__class__`. RESIDUAL A-LEG IMPRECISION (documentation-level, NOT a G-EQ break; no gate consequence). Two directions where the deep model is not literally the real callee, both machine-probed and neither producing a non-resolving patch:

(a) refinement.md step 3 / meta.json deep_model_references say the deep model "mirrors the fact that the new func returns the SAME object". It does not mirror identity: `return s` is REJECTED (atk_10, permission error above), so the spec in fact mandates a fresh equal-text copy. The prior pass logged this as fidelity finding B and it still stands as prose. It is harmless for correctness because Token equality is by class+slots, not identity, so copy and identity are observationally equal under the F2P assertion -- which I confirmed by resolving BOTH the copy patch and the gold patch (both resolved). The claim to fix is the wording "returns the SAME object", not the spec.

(b) The model has ONE carrier class (Atomic), so class preservation is outside the modeled facet: `Atomic(rebuilt_text)` refines equally to `self.__class__(...)` or to a hardcoded `String(...)`, and mapping.md §1's binding Atomic -> String literally suggests the latter. That distinction IS observable in the real repo (String('foobar') != QuotedString('foobar')/Comment/Signifier under Token.`__eq__` -- demonstrated directly), so I built the hardcoded-class variant as the sharpest available spec-blind-spot patch: patch_atk_hardcoded_class.diff, `return lambda: String(''.join(chr(ord(ch)) for ch in self.text))`. Command: python resolve.py patch_atk_hardcoded_class.diff -> {"resolved": true, "completed": true}, F2P 1/1, P2P 29/29 -> RESOLVED. So the unmodeled facet is not exercised by this instance's F2P/P2P set and cannot be turned into a verify-but-wrong witness. Reported for completeness rather than as a finding: strengthening mapping.md §2 to state that class preservation is deliberately outside the modeled facet (Signifier/QuotedString are untested by this instance) would make the boundary explicit.

**FLOOR:** 13 admissible distinct same-spec wrong impls (>=5 required), prepatch reproduced (atk_1, rejected), structurally different positive control that verifies (atk_0), reachability control confirming non-vacuity (atk_8), all resolve runs COMPLETED (3 patches, no timeouts, no inconclusive measurement). No host-saturation or agent-launch artifacts: every Nagini run returned a real verdict in 10-13s and every harness run reported completed=true.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1_prepatch.py`, `atk_2_oracle_echo.py`, `atk_3_noadvance.py`, `atk_4_partial_domain.py`, `atk_5_boundary_offbyone.py`, `atk_6_nul_truncation.py`, `atk_7_descent_dropslast.py`, `atk_8_reachability_control.py`, `atk_9_duplicate.py`, `atk_10_identity.py`, `atk_11_targeted_divergence.py`, `atk_12_guarded_echo.py`, +1 more |

**Non-vacuity.** The positive control `atk_0_positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_oracle_echo.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_noadvance.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_boundary_offbyone.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_nul_truncation.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_descent_dropslast.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_reachability_control.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_duplicate.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_identity.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_targeted_divergence.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_guarded_echo.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_samesize_echo.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22456.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An atomic string-valued symbolic token carries a single defining payload (its
  text) that is deliberately held OFF its positional-argument list: the token
  has an empty argument tuple. Every symbolic object must nonetheless satisfy
  ARGUMENT INVARIANCE — rebuilding the object by applying its reconstruction
  operation to its own positional arguments yields an object equal to the
  original:

      rebuild(positional-arguments-of(t)) == t

  Because the defining text is not among the positional arguments (the argument
  count is zero), a faithful reconstruction must reproduce the original text
  WITHOUT reading it from the (empty) argument list. The discriminating case the
  contract pins: for a token with arbitrary — including non-empty — text, the
  reconstruction from the empty argument list must still carry exactly the
  original text, so that the rebuilt token equals the original. A reconstruction
  that can only source the text from the positional arguments would, on the
  empty list, lose every non-empty text and break the invariance.

  The invariance is a claim about EVERY reconstruction, not only about the ones
  that happen to hand an answer back: the reconstruction is TOTAL — for every
  token it must run to completion and DELIVER a rebuilt token. A reconstruction
  that never delivers one (it re-enters itself on the same token, or spins
  without making progress) does not satisfy the invariance, however its result
  would have been constrained had it arrived. Delivery is bounded by the size of
  the payload being reproduced, so a reconstruction that descends on a STRICTLY
  SMALLER token before assembling its answer is admissible.

The token's defining text is modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); equality of two tokens is equality of that text,
carried by `PSeq[int]` via `ToSeq`. The positional-argument list is modelled by
its length alone (it is empty for this atomic token, and the reconstruction
consumes no positional element).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Atomic:
    """An atomic string-valued token; only its defining `text` payload is
    modelled (the single quantity token equality depends on)."""

    def __init__(self, text: List[int]) -> None:
        Requires(Acc(list_pred(text)))
        # Building a carrier completes: it hands the token back.
        Requires(MustTerminate(1))
        Ensures(Acc(self.text) and self.text is text)  # type: ignore
        Ensures(Acc(list_pred(self.text)))  # type: ignore
        Ensures(ToSeq(self.text) == Old(ToSeq(text)))  # type: ignore
        self.text = text

# axioms-start
# (no @ContractOnly axioms: the operation that changed — how an atomic token
# reconstructs itself from its arguments — is modelled DEEPLY, as a direct
# text-preserving rebuild. No unchanged opaque callee is consumed inside the
# contract. See refinement.md / mapping.md.)
# axioms-end

# pure-start
@Pure
def arg_count(s: Atomic) -> int:
    """The number of positional arguments of the token. The defining text is
    held OFF the argument list, so an atomic string token has zero positional
    arguments."""
    Requires(Acc(s.text, 1 / 4) and Acc(list_pred(s.text), 1 / 4))
    Ensures(Result() == 0)
    return 0
# pure-end

def rebuild_from_args(s: Atomic) -> Atomic:
    # pre-conditions-start
    # `s` is read-only: reconstruction never mutates the original (fractional
    # permission on both the field reference and its list contents).
    Requires(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
    # TOTALITY. Every postcondition below is claimed of EVERY admissible call,
    # not merely of the calls that happen to reach a return: the reconstruction
    # must run to completion and DELIVER a token. The delivery level is bounded
    # by the size of the payload being reproduced, so a reconstruction that
    # descends on a STRICTLY SMALLER token is admissible, while one that
    # re-enters itself on this very token — or loops without advancing — is not,
    # and cannot borrow this contract to stand in for its own answer.
    Requires(MustTerminate(len(s.text) + 2))
    # pre-conditions-end
    # post-conditions-start
    # The original token is preserved (read-only).
    Ensures(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
    # A fresh token is produced (full permission on the reconstruction).
    Ensures(Acc(Result().text) and Acc(list_pred(Result().text)))
    # The token's positional-argument list is empty: the reconstruction draws
    # from zero positional arguments.
    Ensures(arg_count(s) == 0)
    # ARGUMENT INVARIANCE: rebuilding the token from its (empty) positional
    # arguments yields a token EQUAL to the original — i.e. carrying EXACTLY the
    # original text, element for element, even when that text is non-empty.
    # This is the discriminating clause: a reconstruction that could only source
    # the text from the empty argument list would lose any non-empty text.
    Ensures(ToSeq(Result().text) == ToSeq(s.text))
    # post-conditions-end
    # impl-start
    # The reconstruction operation yields the very same token (its result is the
    # original object), so it carries the original text regardless of how many
    # positional arguments there are. Materialise a fresh carrier holding
    # exactly the original text.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        # At most `n - i` passes remain; `i` rises by exactly one each pass and
        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
        # keeps it positive on the final pass. The reproduction completes.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    Assert(i == n)
    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
    result = Atomic(rebuilt_text)  # type: Atomic
    Assert(result.text is rebuilt_text)
    Assert(ToSeq(result.text) == ToSeq(s.text))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-22456/nagini. 13 distinct same-spec wrong impls + positive control + prepatch, all machine-checked; ALL 13 REJECTED by the frozen spec. Verdict SOUND.

Attacks built by splicing ONLY the impl region of the frozen model.py (mk.py / mk2.py); axioms/@Pure/Requires/Ensures byte-identical. All 14 files confirmed same-spec (adversary same-spec exit 0) AND admissible (variant_scope.unsound_evasions == [] for every file: no new @ContractOnly / axiom / assumption token).

COMMAND FORM (every attack): python -m swebench_unified.adversary weakness nagini sympy__sympy-22456 <path>
Run 3-at-a-time as concurrent background jobs (each Nagini check spawns JVM+Z3); logs at w_<name>.log.

| attack | class | observed |
|---|---|---|
| atk_0_positive_control.py | frozen impl verbatim | CANDIDATE, verifies 12.8s, exit 0 -> patch materialized -> RESOLVED (see below) |
| atk_1_prepatch.py | PREPATCH BUG (generic positional rebuild over the empty arg list) | exit 2, does not verify -> spec senses the pre-fix bug |
| atk_2_oracle_echo.py | UNGROUNDED-ORACLE ECHO (`return rebuild_from_args(s)`) | exit 2, does not verify |
| atk_3_noadvance.py | DIVERGENCE (loop counter never advances) | exit 2, does not verify |
| atk_4_partial_domain.py | PARTIAL DOMAIN (correct only for len<=3) | exit 2, does not verify |
| atk_5_boundary_offbyone.py | BOUNDARY (drops last code point) | exit 2, does not verify |
| atk_6_nul_truncation.py | CONTROL-FLOW EFFECT (C-string early return at NUL) | exit 2, does not verify |
| atk_7_descent_dropslast.py | MEASURE-LANE DESCENT (recurse on text[:n-1], keep smaller answer) | exit 2, does not verify |
| atk_8_reachability_control.py | REACHABILITY CONTROL (Assert(False) + frozen body) | exit 2, does NOT verify -> entry path FEASIBLE, so the rejections are genuine, not the vacuity of an infeasible precondition |
| atk_9_duplicate.py | WRONG PAYLOAD (text emitted twice) | exit 2, does not verify |
| atk_10_identity.py | `return s` (literally gold's `lambda: self`) | exit 2: "Postcondition ... insufficient permission to access Result().text" |
| atk_11_targeted_divergence.py | TARGETED DIVERGENCE (inner non-advancing loop only on code point 102='f', first char of F2P 'foobar') | exit 2: "Obligation leak check failed. Loop might not take all unsatisfied obligations from the context." |
| atk_12_guarded_echo.py | GUARDED SELF-CALL on the SAME token (feasible guard len>0) | exit 2: "Obligation leak check failed. Callee rebuild_from_args might not take all unsatisfied obligations from the caller." |
| atk_13_samesize_echo.py | SAME-SIZE ECHO (self-call on a freshly built EQUAL-length twin -> not strictly smaller) | exit 2: same obligation-leak rejection -> the delivery measure is keyed on the payload SIZE, not on object identity |

**PRIOR-PASS COUNTEREXAMPLES RE-ENCODED AND NOW REJECTED.** verdict.md records an earlier BROKEN on atk_2_oracle_echo (self-call verified because the spec carried NO MustTerminate, only partial correctness) and a second candidate atk_9_divergent_noadvance. The frozen model.py has since been repaired exactly as that pass recommended: it now imports nagini_contracts.obligations, carries method-level `Requires(MustTerminate(len(s.text) + 2))` and `Invariant(MustTerminate(n - i + 1))`. I re-encoded BOTH (atk_2_oracle_echo, atk_3_noadvance) and both now FAIL to verify. I also probed the three residual escape lanes that repair could have left open -- a guarded self-call (atk_12), a same-size descent that evades a size-keyed measure (atk_13), and a divergence hidden on one data-dependent path rather than in the main loop (atk_11) -- and Nagini rejects all three with obligation-leak errors. MustTerminate is enforced at the method level and on EVERY path, per MEMORY (loop invariants alone do not reject a diverging rival; the method level is what does).

THE ONE CANDIDATE, RESOLVE EXECUTED (protocol step 2). atk_0_positive_control (the frozen impl) is the only file that verifies, so its faithful refined patch was materialized and RUN through the official harness. This is the load-bearing G-EQ measurement here, because atk_10_identity proves the spec REJECTS gold's own `return s`: the postcondition demands FULL permission on Result().text while the precondition hands out only 1/2 on s, so the verifying impl is necessarily a FRESH text-preserving COPY, not gold's identity. If that copy did not resolve, the bundle would be broken.

Patch generated mechanically from sympy/codegen/ast.py at base_commit a3475b3f9ac662cd425157dd3bdb93ad7111c090 with asserted anchor lines, applying gold's SAME three structural edits (the `Expr, Atom` import; `class String(Atom, Token)`; `kwargs` returning {} and `@property def func` at gold's exact insertion point after `_sympystr`), differing ONLY in func's body -- the modeled operation (`rebuild_from_args` <-> `String.func(*String.args)`, mapping.md §1) -- refining `Atomic(rebuilt_text)` one-for-one as a fresh same-class carrier holding the element-wise-copied text. `git apply --check` clean. Command: python resolve.py patch_atk_0_positive_control.diff (calls harness.run_resolve("sympy__sympy-22456", <patch>, run_id="sbu-geq-7c293ecp-patch_atk_0_positive_control")).

RESULT: {"resolved": true, "completed": true, "note": "resolved"} -- FAIL_TO_PASS test_String PASSES, PASS_TO_PASS 29/29 pass. So the verifying impl's faithful patch DOES resolve: no verify-but-wrong witness. NOT a spec weakness -- per architecture.md §6 a candidate whose patch resolves is a correct alternative implementation (an echo of the reference solution), and must not fail the gate. GOLD CONTROL: patch_gold_control.diff (`lambda: self`) -> resolved true, completed true, F2P 1/1, P2P 29/29 -- confirms the oracle lane itself is live and discriminating.

### A-LEG AUDIT (the G-EQ focus; R/I legs are G-CONF's).
refinement.md legs: step 1 R (String -> single facet text; str <-> List[int] code points; Token.`__eq__` = same class + all `__slots__` equal, which for the single-slot String reduces to text equality -- verified against sympy/codegen/ast.py:255 in a base-commit checkout), step 2 R (args modeled by length; String.`__slots__`=('text',), not_in_args=['text'] so Basic.`__new__` gets no positional args -> args==() -- confirmed in source), step 3 A-REFERENCE, step 4 R. NO kind-3 step, and meta.json axioms==[] with one deep_model_references entry -- consistent: the changed op is modeled deeply, nothing is A-consumed, so there is no axiom trust point. Confirmed no @ContractOnly anywhere in model.py.

A-REFERENCE CORRESPONDENCE, EXECUTED. axiom_check.py run on a gold-patched base-commit tree: exit 0, "G-AX OK ... sound on 1 F2P + 12 boundary + 20000 fuzz texts". NEGATIVE CONTROL at the unpatched base commit: fails on the first case with TypeError: No value for 'text' given and attribute has no default (sympy/codegen/ast.py:237) -- exactly the pre-fix mechanism mapping.md §1 documents, so the witness has real discriminating power and is not vacuous. Mechanism reproduced standalone (mech_copy.py): gold identity and the copy rebuild BOTH satisfy func(*args)==st, and the copy preserves the subclass via self.`__class__`. RESIDUAL A-LEG IMPRECISION (documentation-level, NOT a G-EQ break; no gate consequence). Two directions where the deep model is not literally the real callee, both machine-probed and neither producing a non-resolving patch:

(a) refinement.md step 3 / meta.json deep_model_references say the deep model "mirrors the fact that the new func returns the SAME object". It does not mirror identity: `return s` is REJECTED (atk_10, permission error above), so the spec in fact mandates a fresh equal-text copy. The prior pass logged this as fidelity finding B and it still stands as prose. It is harmless for correctness because Token equality is by class+slots, not identity, so copy and identity are observationally equal under the F2P assertion -- which I confirmed by resolving BOTH the copy patch and the gold patch (both resolved). The claim to fix is the wording "returns the SAME object", not the spec.

(b) The model has ONE carrier class (Atomic), so class preservation is outside the modeled facet: `Atomic(rebuilt_text)` refines equally to `self.__class__(...)` or to a hardcoded `String(...)`, and mapping.md §1's binding Atomic -> String literally suggests the latter. That distinction IS observable in the real repo (String('foobar') != QuotedString('foobar')/Comment/Signifier under Token.`__eq__` -- demonstrated directly), so I built the hardcoded-class variant as the sharpest available spec-blind-spot patch: patch_atk_hardcoded_class.diff, `return lambda: String(''.join(chr(ord(ch)) for ch in self.text))`. Command: python resolve.py patch_atk_hardcoded_class.diff -> {"resolved": true, "completed": true}, F2P 1/1, P2P 29/29 -> RESOLVED. So the unmodeled facet is not exercised by this instance's F2P/P2P set and cannot be turned into a verify-but-wrong witness. Reported for completeness rather than as a finding: strengthening mapping.md §2 to state that class preservation is deliberately outside the modeled facet (Signifier/QuotedString are untested by this instance) would make the boundary explicit.

**FLOOR:** 13 admissible distinct same-spec wrong impls (>=5 required), prepatch reproduced (atk_1, rejected), structurally different positive control that verifies (atk_0), reachability control confirming non-vacuity (atk_8), all resolve runs COMPLETED (3 patches, no timeouts, no inconclusive measurement). No host-saturation or agent-launch artifacts: every Nagini run returned a real verdict in 10-13s and every harness run reported completed=true.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE. Reference = base_commit worktree WITH gold patch APPLIED (, base a3475b3f9ac662cd425157dd3bdb93ad7111c090 + data/swe_bench_verified gold patch, applied cleanly). Base-only worktree () used solely as a negative control, never as the reference for the modeled function.

**SPEC REGION IDENTITY.** markers.same_spec(model.py, model_prepatch.py, get_backend('nagini')) = True. region_hashes agree byte-for-byte on axioms / pure / pre-conditions / post-conditions and on spec_view (9b167740eb2e...); only `invariants` and `impl` differ. So the differential leg genuinely holds the spec frozen.

**MODELED FUNCTION.** rebuild_from_args  <->  real sympy.codegen.ast.String.func(*String.args). Post-fix func is the gold hunk's `@property def func(self): return lambda: self`; String.`__slots__`=('text',), not_in_args=['text'] so Basic.args==().

### FAITHFULNESS PROBES AGAINST THE PATCHED REFERENCE (all agree; no diverging input found):
1. arg_count(s)==0 unconditionally: verified len(String(t).args)==0 on 60030 real instances across String/QuotedString/Comment, incl. '', 'a', 'foobar', 500-char, NUL, lone surrogate \ud800, astral '\U0001d518', and odd domains (text=None -> NoneToken, text=Dummy('q') via the Dummy bypass in Token.`_construct`, text=String('z') via the pass-through branch). Zero counterexamples.
2. ARGUMENT INVARIANCE (ToSeq(Result().text)==ToSeq(s.text)): real func(*args)==self and rebuilt.text==st.text on every one of those 60030 cases. Empty text: real args=(), rebuilt.text='', eq True -- matches the model's zero-iteration loop exactly.
3. Bundle checks re-run by me against the patched worktree: axiom_check.py exit 0 (1 F2P + 12 boundary + 20000 fuzz); conformance_check.py exit 0, 100018 inputs (18 boundary + 100000 fuzz, seed 22456), 0 disagreements. Negative control confirms non-vacuity: on the unpatched base the same conformance script FAILS on input 1 (real func(*args) raises TypeError "No value for 'text' given and attribute has no default"), and model_prepatch.py fails Nagini on exactly the discriminating clause: "Postcondition ... Assertion (ToSeq(Result().text) == ToSeq(s.text)) might not hold". Gold model.py verifies (11.3s).
4. TOTALITY / MustTerminate(len(s.text)+2) is not over-strong: the real post-fix reconstruction is `lambda: self`, which terminates unconditionally, so requiring termination cannot condemn real behavior. Confirmed no self-recursion path exists in the real callee.
5. SUBCLASS SWEEP for a hidden non-zero-args String: imported every non-test module in sympy and walked String.`__subclasses__` transitively -- exactly 2 (QuotedString, Comment), both `__slots__`==('text',), not_in_args==['text'], both args==() and func(*args) is self. So the hard-pinned arg_count==0 has no real counterexample in-tree.

### Over-strength candidates investigated and dismissed
(a) Ensures(Acc(Result().text) and Acc(list_pred(Result().text))) demands a FRESH exclusively-owned token while the real gold func returns `self` (measured: returns SAME object 60030/60030, fresh 0/0). I confirmed this bites: an attack keeping the spec byte-identical (same_spec=True) with impl `return s` -- the literal transliteration of gold's `lambda: self` -- is REJECTED by Nagini ("There might be insufficient permission to access Result().text"). This is the sharpest available faithfulness objection, so I tested whether it is behavioral drift or an inert separation-logic framing artifact.

It is inert: I built a fresh-copy repo variant (func = `lambda: self.__class__(self.text)`), which is exactly the object-identity behavior the model's permission clause describes, and it passes the full codegen suite (90 passed, 1 skipped, 1 xfailed, 2 xpassed) and axiom_check.py exit 0 -- identical to gold. Nothing observable in the repo distinguishes return-self from return-fresh-copy: String equality is Token.`__eq__` (same class + slot equality), hash agrees, and `fresh in {a}` is True. The clause therefore constrains only the model's own heap ownership, not repo behavior, and mapping.md §2 declares token identity is abstracted to text equality. No diverging INPUT exists -- the mismatch is in the aliasing abstraction, which the mapping states, not in the input/output relation.

(b) Pinning arg_count==0 could in principle condemn a correct rival fix that instead moves text INTO args. I built that rival (delete not_in_args, so args==('foobar',) and the inherited Basic.func rebuild works). It gives func(*args)==self True and passes the exact F2P+P2P set (30/30). This is the one real spec-strength narrowing: that rival resolves yet contradicts arg_count==0. But it does not make the spec UNFAITHFUL, because faithfulness is judged against the actual patched repo, where args is provably always () (probe 1/5); the rival also breaks test_ast_replace, which is outside the graded P2P list, so it is a non-canonical fix, not the reference. Recorded as a scope note, not a defect.

**CONCLUSION:** on every input probed -- ~160k real-callee comparisons including all boundary/unicode/degenerate-domain cases and every in-tree String subclass -- the modeled function agrees with the real patched callee on both observables it claims (arg count, rebuilt text / token equality). The spec is discriminating (prepatch fails on the intended clause) and non-vacuous. No diverging input. Verdict FAITHFUL.

**REFERENCE DISCIPLINE.** Reference = base_commit worktree WITH gold patch APPLIED (, base a3475b3f9ac662cd425157dd3bdb93ad7111c090 + data/swe_bench_verified gold patch, applied cleanly). Base-only worktree () used solely as a negative control, never as the reference for the modeled function.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE / no inherited disposition. This bundle carries NO relaxation: `python -c json.load(meta.json)` shows no `relaxed_leakage` key (keys are additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version), and `find . -iname '*RELAX*'` over the whole tree returns 66 RELAXED_LEAKAGE.md files, NONE under sympy__sympy-22456/ (that instance dir holds only ears/ instance.json/ lean/ nagini/ patch.diff/ velvet/). meta gates record G-LEAK status='pass' ('spec view clean'), not 'relaxed'. So this is a straight leakage judgement I derive myself.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as a finding in its own right, per instruction): ran leakage.reviewer_directed() over all 10 bundle files (model.py, model_prepatch.py, refinement.md, mapping.md, meta.json, verdict.md, axiom_check.py, conformance_check.py, properties.py, pbt_result.json) -> 'none' for every file. Also grepped the spec-side files for 'panel|reviewer|auditor|you should|do not submit|must submit|honest verdict|NO-LEAKAGE|attacker' -> zero hits. NOTHING in this bundle instructs me how to record or which verdict is honest. The only pre-existing panel prose is verdict.md:2538-2573, a transcript of a PRIOR G-PANEL-3 run's own note; I did not inherit it -- I re-derived both halves of its key measurement independently (see MECHANISM below), and my numbers agree.

PUBLIC BASELINE (problem_statement only, hints_text is empty and unused): 'Argument invariance of codegen.ast String / Currently, the codegen.ast String class does not support argument invariance like: expr.func(*expr.args) == expr, but instead uses the invariance expr.func(**expr.kwargs()) == expr. The former should hold for any Basic subclass, which String is.' The public statement therefore already names String, func, args, kwargs, and states the exact target equation func(*args)==expr. The spec's whole subject matter is public.

SPEC-VIEW MEASUREMENT (rendered myself via markers.spec_view(model.py, nagini), sha256 9b167740eb2e230f5c55cd047caeda4cdda443ef6694536201b44de4a0e390ef, matching meta region_hashes.spec_view -- so I judged the same bytes the gates stamped). leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) re-run by me: LeakageReport(hard_failures=[], warnings=[]). Confirmed NOT a vacuous pass: `_patch_changed_symbols`(gold) = {String, func, kwargs, construct_text, construct_iterable}; in the spec view 'func'=absent, 'kwargs'=absent, 'not_in_args'=absent, 'lambda'=absent, 'property'=absent, 'override'=absent, 'return self'=absent, 'same object'=absent, 'identity'=absent, 'slot'=absent, 'basic'=absent.

None of the 10 gold changed lines appear; patched path sympy/codegen/ast.py and dotted sympy.codegen.ast absent. Zero narration vocabulary (`_NARRATION_RE`: fix/bug/patch/previously/broken/regression) -- 0 hits. The impl region's one mechanism-disclosing comment ('yields the very same token (its result is the original object)') is ELIDED: the view renders '...  # implementation elided -- supplied by the consumer', and I confirmed 'very same token'/'original object' are absent from the view.

NEAR-MISS I ADJUDICATED BY MEASUREMENT, not by reading the prior note. The gold headline hunk is `class String(Atom, Token)` and the model class is named `Atomic` with 'atomic string-valued token' prose (9 'atom' hits in the view) -- the one plausible leak of a gold hunk. I built a base-commit worktree (git worktree add --detach from the upstream repository at a3475b3f9ac662cd425157dd3bdb93ad7111c090) and ran BOTH directions in /tmp:

  (a) Atom base ONLY, no func/kwargs override: class S2(Atom, Token) with same `__slots__`/not_in_args -> st.func(*st.args) still raises TypeError "No value for 'text' given and attribute has no default". F2P still FAILS.

  (b) func/kwargs override ONLY, no Atom base (edited ast.py in the worktree, then restored from a saved copy; `git diff --stat` clean afterwards) -> String.`__bases__` == (Token,) and st.func(*st.args)==st -> True. F2P PASSES.
So the Atom base is NOT the discriminator; the func override is, and the spec view never names func, property, lambda, or 'returns self'. Separately, the atomicity vocabulary is already PRE-patch public: at base_commit String's own docstring reads 'Atomic object which is not an expression (as opposed to Symbol)' and is_Atom=True / not_in_args=['text'] are pre-existing class attributes -- unchanged by the gold patch. 'Atomic' points at base-commit-visible shape, not at the edit.

UNAVOIDABILITY / LOAD-BEARING TEST (the usual control): the discriminating clause is Ensures(ToSeq(Result().text) == ToSeq(s.text)) plus Requires(MustTerminate(len(s.text)+2)). I ran the pinned verifier on both twins: model.py -> 'Verification successful' (10.68s, exit 0); model_prepatch.py -> 'Verification failed ... error: Postcondition of rebuild_from_args might not hold. Assertion (ToSeq(Result().text) == ToSeq(s.text)) might not hold.' (exit 1). markers.same_spec(model, prepatch) = True and spec_view digests identical (axioms/pure/pre-conditions/post-conditions all equal; only invariants+impl differ), so the prepatch twin is a genuine same-spec pre-fix impl. The invariance clause is thus strictly load-bearing -- it is what senses the change -- and it is a verbatim restatement of the PUBLIC equation func(*args)==expr, not an extra hint. Harness cross-check: `adversary same-spec nagini sympy__sympy-22456` on the bundle model -> 'SAME', exit 0.

GATE SOUNDNESS I LEANED ON (checked, not assumed): G-VERIFY/G-LEAK/G-DIFF/G-GOLD/G-MUT(17/17 killed)/G-CONF(100018 inputs, 0 disagreements, negative control refutes on unpatched base)/G-AX all stamped 'pass' against model.py sha e4e1f4d65d485855..., which is byte-identical to the model.py on disk I judged (sha256sum confirms). G-RESOLVE resolved=true.

NOT part of this verdict, flagged as record hygiene: meta records G-EQ and G-PANEL-1 as status='fail' against a STALE model.py sha (5f4d4c1f42f9..., not the current e4e1f4d6...), dated 21:54 vs the 23:27-23:29 pass sweep, with detail 'BROKEN (verify!=>correct) ... atk_2_oracle_echo.py verifies but its patch does not resolve'. That is a stale-artifact/oracle-echo record on a superseded model, and per the retained-attack-label caveat I do not re-read it as spec weakness; it bears on G-EQ/G-PANEL-1, not on leakage.

**FACET RE-CONFIRMED:** argument invariance of an atomic string token -- that rebuilding from the empty positional-argument list must still carry exactly the original text (func(*args)==self). That facet is fully public in problem_statement. The spec view discloses nothing beyond it: not the func-override mechanism, not the Atom base, not the pre-fix TypeError, not the file or symbols. VERDICT NO-LEAKAGE. Worktree left clean (ast.py restored, git diff empty).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
