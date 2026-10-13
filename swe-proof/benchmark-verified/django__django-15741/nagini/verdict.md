# P2 adversarial audit — django__django-15741

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch.py`, `atk_2_empty_key.py`, `atk_3_drop_last.py`, `atk_4_oracle_echo.py`, `atk_5_poison_store0.py`, `atk_6_poison_result.py`, `atk_7_poison_eager_only.py`, `atk_8_poison_name.py`, `atk_9_poison_append.py`, `atk_11_swap_ends.py`, `atk_12_deferred_trunc.py`, `atk_14_return_name.py`, `atk_15_diverge.py`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_10_double_resolve.py`, `atk_13_no_copy.py`, `atk_17_triple_lookup.py`, `atk_18_fresh_copy.py` |

**Non-vacuity.** The positive control `pos_ctl_cachedbound.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl was found whose faithful refined patch fails to resolve. 18 same-spec attacks run; 14 REJECTED by the spec, 4 CANDIDATES (verify) whose materialized faithful patches were all EXECUTED through the official harness and ALL RESOLVED (F2P 2/2, P2P 104/104, completed=True, flaky=False, attempts=1 each) — i.e. they are correct-alternative echoes, not weaknesses.

SPECIFICALLY: the PRIOR RECORDED BREAK IS REPAIRED AND I RE-TESTED IT DIRECTLY. verdict.md records G-EQ=fail at 2026-08-14T13:38 on atk_7_poison_store0.py (P2P 99/104), rooted in the do_lookup axiom's `Ensures(Acc(list_pred(Result())))` — FULL/EXCLUSIVE ownership of the returned list, which let a verifying impl destructively store into the object the real _format_cache keeps. The shipped model.py is NEWER than that verdict (mtime Aug 14 19:33 vs verdict 13:38; md5 72cdb6273913e2092abe6dda54f72139, NOT the 9c4dae79c8522d3acdeb25f2e3c891db the prior pass audited) and replaces those clauses with `Wildcard(list_pred(...))` on both the name and the Result, at the axiom AND at lookup_format's postcondition. I re-encoded ALL THREE prior breaks verbatim (atk_5_poison_store0 = old atk_7; atk_6_poison_result = old atk_8 mutation-after; atk_7_poison_eager_only = old atk_9 deferred-flag-guarded last-index store) and ALL THREE NOW FAIL TO VERIFY, each with the precise causal error `The precondition of extra[0] = 88 / result[0] = 88 might not hold. There might be insufficient permission.` The repair bites exactly where the defect was, so the recorded fail is STALE against these bytes.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,25 +156,20 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
-    i = 0
-    while i < len(requested_name.content):
-        # invariants-start
-        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(0 <= i and i <= len(requested_name.content))
-        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
-        Invariant(MustTerminate(len(requested_name.content) - i + 1))
-        # invariants-end
-        name.append(requested_name.content[i])
-        i = i + 1
-    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
-    Assert(ToSeq(name) == resolve(requested_name))
+    if not requested_name.deferred:
+        i = 0
+        while i < len(requested_name.content):
+            # invariants-start
+            Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
+            Invariant(Acc(list_pred(name)))
+            Invariant(0 <= i and i <= len(requested_name.content))
+            Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
+            Invariant(MustTerminate(len(requested_name.content) - i + 1))
+            # invariants-end
+            name.append(requested_name.content[i])
+            i = i + 1
+        Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 2 — `atk_2_empty_key.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,25 +156,7 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
-    i = 0
-    while i < len(requested_name.content):
-        # invariants-start
-        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(0 <= i and i <= len(requested_name.content))
-        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
-        Invariant(MustTerminate(len(requested_name.content) - i + 1))
-        # invariants-end
-        name.append(requested_name.content[i])
-        i = i + 1
-    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
-    Assert(ToSeq(name) == resolve(requested_name))
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 3 — `atk_3_drop_last.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,25 +156,18 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
-    while i < len(requested_name.content):
+    while i < len(requested_name.content) - 1:
         # invariants-start
         Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
         Invariant(Acc(list_pred(name)))
-        Invariant(0 <= i and i <= len(requested_name.content))
+        Invariant(0 <= i and (i <= len(requested_name.content) - 1 or i == 0))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
-    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
-    Assert(ToSeq(name) == resolve(requested_name))
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 4 — `atk_4_oracle_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,13 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
-    result = do_lookup(name)
+    once = do_lookup(name)
+    result = do_lookup(once)
     return result
     # impl-end
```

Attack 5 — `atk_5_poison_store0.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,15 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
+    extra = do_lookup(name)
+    if len(extra) > 0:
+        extra[0] = 88
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 6 — `atk_6_poison_result.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,9 +164,6 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
@@ -176,5 +171,7 @@
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
     result = do_lookup(name)
+    if len(result) > 0:
+        result[0] = 88
     return result
     # impl-end
```

Attack 7 — `atk_7_poison_eager_only.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,9 +164,6 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
@@ -176,5 +171,8 @@
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
     result = do_lookup(name)
+    if not requested_name.deferred:
+        if len(result) > 0:
+            result[len(result) - 1] = 88
     return result
     # impl-end
```

Attack 8 — `atk_8_poison_name.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,9 +164,6 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
@@ -176,5 +171,7 @@
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
     result = do_lookup(name)
+    if len(name) > 0:
+        name[0] = 88
     return result
     # impl-end
```

Attack 9 — `atk_9_poison_append.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,14 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
+    extra = do_lookup(name)
+    extra.append(88)
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 10 — `atk_10_double_resolve.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,23 +156,31 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
-    name = []  # type: List[int]
+    first = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
         # invariants-start
         Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
-        Invariant(Acc(list_pred(name)))
+        Invariant(Acc(list_pred(first)))
         Invariant(0 <= i and i <= len(requested_name.content))
-        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
+        Invariant(ToSeq(first) == ToSeq(requested_name.content).take(i))
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
-        name.append(requested_name.content[i])
+        first.append(requested_name.content[i])
         i = i + 1
+    name = []  # type: List[int]
+    k = 0
+    while k < len(requested_name.content):
+        # invariants-start
+        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
+        Invariant(Acc(list_pred(name)))
+        Invariant(Acc(list_pred(first)))
+        Invariant(0 <= k and k <= len(requested_name.content))
+        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(k))
+        Invariant(MustTerminate(len(requested_name.content) - k + 1))
+        # invariants-end
+        name.append(requested_name.content[k])
+        k = k + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
     result = do_lookup(name)
```

Attack 11 — `atk_11_swap_ends.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,18 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
+    n = len(name)
+    if n > 1:
+        t0 = name[0]
+        tn = name[n - 1]
+        name[0] = tn
+        name[n - 1] = t0
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 12 — `atk_12_deferred_trunc.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,15 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
+    if requested_name.deferred:
+        if len(name) > 0:
+            name.pop()
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 13 — `atk_13_no_copy.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,25 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
-    name = []  # type: List[int]
-    i = 0
-    while i < len(requested_name.content):
-        # invariants-start
-        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(0 <= i and i <= len(requested_name.content))
-        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
-        Invariant(MustTerminate(len(requested_name.content) - i + 1))
-        # invariants-end
-        name.append(requested_name.content[i])
-        i = i + 1
-    Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
-    Assert(ToSeq(name) == resolve(requested_name))
-    result = do_lookup(name)
+    result = do_lookup(requested_name.content)
     return result
     # impl-end
```

Attack 14 — `atk_14_return_name.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,12 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
-    result = do_lookup(name)
-    return result
+    ignored = do_lookup(name)
+    return name
     # impl-end
```

Attack 15 — `atk_15_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,9 +164,6 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
@@ -176,5 +171,10 @@
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
     result = do_lookup(name)
+    while True:
+        # invariants-start
+        Invariant(Acc(list_pred(result)) or True)
+        # invariants-end
+        i = i + 1
     return result
     # impl-end
```

Attack 16 — `atk_16_double_key.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,22 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
+    j = 0
+    while j < len(requested_name.content):
+        # invariants-start
+        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
+        Invariant(Acc(list_pred(name)))
+        Invariant(0 <= j and j <= len(requested_name.content))
+        Invariant(MustTerminate(len(requested_name.content) - j + 1))
+        # invariants-end
+        name.append(requested_name.content[j])
+        j = j + 1
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 17 — `atk_17_triple_lookup.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,14 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
+    r1 = do_lookup(name)
+    r2 = do_lookup(name)
     result = do_lookup(name)
     return result
     # impl-end
```

Attack 18 — `atk_18_fresh_copy.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,8 +156,6 @@
     Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
     # post-conditions-end
     # impl-start
-    # Resolve the requested name to its character sequence FIRST, then look it
-    # up — so the downstream lookup never sees the deferred form.
     name = []  # type: List[int]
     i = 0
     while i < len(requested_name.content):
@@ -166,15 +164,25 @@
         Invariant(Acc(list_pred(name)))
         Invariant(0 <= i and i <= len(requested_name.content))
         Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
-        # `i` rises by one per pass and the bound len(content) is fixed (content
-        # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
-        # stays >= 1 while i < len(content).
         Invariant(MustTerminate(len(requested_name.content) - i + 1))
         # invariants-end
         name.append(requested_name.content[i])
         i = i + 1
     Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
     Assert(ToSeq(name) == resolve(requested_name))
-    result = do_lookup(name)
+    served = do_lookup(name)
+    result = []  # type: List[int]
+    m = 0
+    while m < len(served):
+        # invariants-start
+        Invariant(Wildcard(list_pred(served)))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= m and m <= len(served))
+        Invariant(ToSeq(result) == ToSeq(served).take(m))
+        Invariant(MustTerminate(len(served) - m + 1))
+        # invariants-end
+        result.append(served[m])
+        m = m + 1
+    Assert(ToSeq(served).take(len(served)) == ToSeq(served))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctl_cachedbound.py`

```python
"""Twin-artifact model for django__django-15741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A localisation lookup is requested by a *name*. That name is supplied as a
  string-valued argument, which may arrive in either of two equivalent forms:

    * already-resolved — the name is directly available as a sequence of
      characters; or
    * deferred — the name is wrapped in a placeholder that only yields its
      character sequence once it is resolved (the same character sequence the
      resolved form carries).

  The looked-up value must depend ONLY on the resolved character sequence of
  the requested name. Two requests whose names resolve to the same character
  sequence MUST return the same value, regardless of whether either name
  arrived already-resolved or deferred. In particular, requesting a name in its
  deferred form returns exactly what requesting the same name in its
  already-resolved form returns.

  A request must also leave the looked-up values as it found them. The value a
  requester is handed for a name is the one the downstream lookup itself keeps
  and hands out again to every later request for that name -- it does not become
  the requester's own object to modify, and where the lookup holds no separate
  value for a name it may hand back the name object itself. So a request obtains
  read access to that value and passes it on, and the value associated with a
  name is the same after a request as it was before it: a later request for the
  same name still yields the same value.

  Nothing changes hands in the other direction either. Asking with a name does
  not modify it, but it does not leave the requester in sole possession of it:
  the downstream lookup keys itself on the resolved name and keeps hold of what
  it was keyed with. So read access is all a request needs of a name and all it
  gives back -- and since neither the name nor the value is anyone's exclusive
  property across a request, the value served for a name may be that very name.

The name is modelled as a minimal object carrying a ``deferred`` flag and its
underlying character sequence as ``List[int]`` of Unicode code points (Nagini
bans ``str`` indexing). ``resolve`` is the deep model of the placeholder-to-text
coercion: it yields the underlying character sequence in both forms and is
validated == the real coercion by axiom_check.py (G-AX), NOT consumed as an
axiom. The unchanged downstream lookup keyed on a resolved name is modelled by
the pure ``format_value`` (a deterministic function of the resolved character
sequence) and its list-producing companion ``do_lookup``; their soundness —
that the real lookup is determined by the resolved name only — is checked by
G-AX.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class FormatType:
    def __init__(self, deferred: bool, content: List[int]) -> None:
        Requires(Acc(list_pred(content), 1 / 2))
        # Two field stores, loop-free: the constructor always terminates. Level 1
        # so a level-2 body (lookup_format, and the admissibility witness that
        # builds a concrete FormatType) can call it without leaking its own
        # obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.deferred) and self.deferred == deferred)  # type: ignore
        Ensures(Acc(self.content) and self.content is content)  # type: ignore
        Ensures(Acc(list_pred(content), 1 / 2))
        self.deferred = deferred
        self.content = content

# axioms-start
@Pure
@ContractOnly
def format_value(name: PSeq[int]) -> PSeq[int]:
    """The value of the unchanged downstream localisation lookup, keyed on the
    *resolved* character sequence of the requested name. It is a deterministic
    function of that sequence alone (same resolved name -> same value). The
    proof consumes only this functional determinism. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """

@ContractOnly
def do_lookup(name: List[int]) -> List[int]:
    """The unchanged downstream lookup as a list-producing operation: given a
    fully-resolved name it returns the value for that name. Its character
    content is exactly ``format_value`` of the resolved name (so the value
    depends only on the resolved characters). Read-only in the name.

    The value handed back stays the lookup's own: the very same object is handed
    out again to every later request for that name, and for a name the lookup
    holds no separate value for it is the name object itself. A caller therefore
    obtains read access to that value and never the exclusive access that
    modifying it would take; nothing here asserts that the value is an object
    distinct from the name, or one the caller may keep for itself."""
    # It only READS the name it is given: read access is all it needs and all it
    # gives back, and it never takes ownership of the name.
    Requires(Wildcard(list_pred(name)))
    # A keyed dictionary lookup over the resolved name: bounded, loop-free work,
    # so it always terminates. Level 1, strictly below the level-2 caller.
    Requires(MustTerminate(1))
    Ensures(Wildcard(list_pred(name)))
    # Read access to the value the lookup serves for this name, never ownership
    # of it: a caller may read what the name is associated with, and may not
    # modify it. Because neither the name nor the value is owned across this
    # call, the value being the name object itself stays POSSIBLE here -- a
    # requester may not conclude the two are distinct objects.
    Ensures(Wildcard(list_pred(Result())))
    Ensures(ToSeq(Result()) == format_value(ToSeq(name)))
# axioms-end

# pure-start
@Pure
def resolve(ft: FormatType) -> PSeq[int]:
    """The resolved character sequence of a requested name. A deferred name and
    an already-resolved name yield the SAME underlying character sequence: the
    resolution does not depend on the ``deferred`` flag. Deep model of the
    placeholder-to-text coercion, validated == the real coercion by G-AX."""
    Requires(Acc(ft.content) and Acc(list_pred(ft.content), 1 / 4))
    return ToSeq(ft.content)
# pure-end

def lookup_format(requested_name: FormatType) -> List[int]:
    # pre-conditions-start
    # The requested name is read-only (directive 5): nothing about it is
    # mutated by the lookup.
    Requires(Acc(requested_name.deferred, 1 / 2))
    Requires(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
    # The lookup terminates. Level 2: strictly above do_lookup / FormatType.
    # __init__ (level 1), and high enough that list.__init__ (building `name`)
    # has room below the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(requested_name.deferred, 1 / 2))
    Ensures(Acc(requested_name.content, 1 / 2))
    # NOTHING IS OWNED ACROSS A REQUEST. The requester keeps read access to the
    # name it asked with -- the request does not modify that name -- but not
    # exclusive ownership of it: the downstream lookup keys itself on the resolved
    # name and holds on to what it was keyed with, so a requester cannot take the
    # name back for its own exclusive use once it has asked with it.
    Ensures(Wildcard(list_pred(requested_name.content)))
    # And the requester obtains READ access to the value the name is associated
    # with, never ownership of it. So the request leaves that association as it
    # found it -- the same name requested afterwards still yields the same value
    # -- and read access is all there is to hand over anyway, since the value
    # served may be the object the downstream lookup keeps, or the name itself.
    # Read access on both sides is also what keeps those two POSSIBLY THE SAME
    # object: nothing here lets a requester conclude that the value it was handed
    # is an object distinct from the name it asked with.
    Ensures(Wildcard(list_pred(Result())))
    # The value depends only on the RESOLVED character sequence of the name.
    # Because ``resolve`` ignores the deferred flag, a deferred name and an
    # already-resolved name with the same characters return the same value.
    Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
    # post-conditions-end
    # impl-start
    clen = len(requested_name.content)
    name = []  # type: List[int]
    i = 0
    while not (i >= clen):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(clen == len(requested_name.content))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= clen)
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        Invariant(MustTerminate(clen - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(i == clen)
    Assert(ToSeq(requested_name.content).take(clen) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    Assert(ToSeq(result) == format_value(resolve(requested_name)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### COMMANDS (repo root swe-proof; D=):
  python -m swebench_unified.adversary same-spec nagini django__django-15741 $D/<f>.py
  python -m swebench_unified.adversary weakness  nagini django__django-15741 $D/<f>.py
  bash scripts/nagini_verify.sh $D/pos_ctl_cachedbound.py   (and $D/vac_ctl_assert_false.py)
  SBU_BENCHMARK_DIR=benchmark-verified python $D/resolve_one.py $D/patch_<tag>.diff <tag>   # harness.run_resolve

### PER-ATTACK RESULTS (path :: class :: observed):
 1. $D/atk_1_prepatch.py :: PREPATCH RE-ENCODE (impl region verbatim from the bundle's model_prepatch.py: the deferred name is fed to the lookup unresolved -- the literal getattr(module,<lazy>) bug) :: weakness exit 2, does not verify -> spec REJECTS the prepatch bug. prepatch_reproduced=True.
 2. $D/atk_2_empty_key.py :: PARTIAL-DOMAIN degenerate (never resolve; look up the empty key) :: exit 2, REJECTED.
 3. $D/atk_3_drop_last.py :: BOUNDARY off-by-one (loop bound len-1, drop the last code point) :: exit 2, REJECTED.
 4. $D/atk_4_oracle_echo.py :: UNGROUNDED-ORACLE ECHO (do_lookup(do_lookup(name)) => format_value(format_value(x))) :: exit 2, REJECTED -- the oracle is grounded at resolve(name)==ToSeq(content); no free value to echo.
 5. $D/atk_5_poison_store0.py :: REGRESSION of PRIOR BREAK #1 (old atk_7_poison_store0): destructive store at index 0 of a looked-up value :: exit 2, REJECTED with `insufficient permission` on `extra[0] = 88`. **PRIOR BREAK REPAIRED.**
 6. $D/atk_6_poison_result.py :: REGRESSION of PRIOR BREAK #2 (old atk_8): mutate the RETURNED object :: exit 2, REJECTED with `insufficient permission` on `result[0] = 88`. **REPAIRED.**
 7. $D/atk_7_poison_eager_only.py :: REGRESSION of PRIOR BREAK #3 (old atk_9): last-index store GUARDED by the deferred flag (fires only on the already-resolved branch) :: exit 2, REJECTED. **REPAIRED.**
 8. $D/atk_8_poison_name.py :: ownership over-claim on the NAME side (mutate the resolved key AFTER handing it to the lookup, which keys `_format_cache` on it) :: exit 2, REJECTED.
 9. $D/atk_9_poison_append.py :: CONTROL-FLOW-EFFECT, non-destructive APPEND flavour (this VERIFIED in the prior pass and its patch RESOLVED; kept as the append-vs-store attribution control) :: exit 2, now REJECTED too -- the Wildcard repair is strictly stronger than needed for the break, and rejects the benign flavour as well.
10. $D/atk_10_double_resolve.py :: A-REFERENCE probe (resolve is a pure function of ft.content, so the model proves two independent resolutions identical, whereas functional.py lazy() explicitly does NOT memoize -- "Results are not memoized; the function is evaluated on every access", functional.py:87-92, and `__proxy__`.`__str__` at functional.py:171-174 re-evaluates `__cast`() on every access) :: weakness exit 0 CANDIDATE (21.5s). Faithful patch MATERIALIZED (two independent str(format_type) coercions, keyed on the second) and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO, not a break (the wrapped callable is side-effect-free on this oracle). Reported as executed, not speculated.
11. $D/atk_11_swap_ends.py :: ORDER-INSENSITIVITY (resolve then transpose first/last code point -- same multiset, different sequence) :: exit 2, REJECTED -- the postcondition is genuinely sequence-valued.
12. $D/atk_12_deferred_trunc.py :: PARTIAL-DOMAIN branch-selective KEY corruption (on the DEFERRED branch only, look up a truncated key -- the prepatch bug in subtler dress) :: exit 2, REJECTED. This is the discriminating leg and it holds.
13. $D/atk_13_no_copy.py :: A2-LEG probe: SKIP the copy loop entirely, hand do_lookup `requested_name.content` itself (tests whether the loop the A2 leg maps to `str(format_type)` is load-bearing) :: weakness exit 0 CANDIDATE (18.6s). Faithful patch MATERIALIZED (pass the resolved value straight into the extracted downstream lookup, no intermediate copy bound) and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO. Benign because in the real code the coercion still happens at the call; the copy loop is a MATERIALIZATION artifact of the List[int] carrier, not a distinct behavioural step.
14. $D/atk_14_return_name.py :: ALIASING-PROSE EXPLOIT -- the axiom docstring and postcondition go out of their way to keep "the value served for a name may be that very name" POSSIBLE; this returns the name UNCONDITIONALLY :: exit 2, REJECTED. The permissive aliasing prose grants only the POSSIBILITY (no non-aliasing conclusion), it does NOT admit returning the name as the value -- the functional postcondition still pins the value to format_value(resolve(...)). Good.
15. $D/atk_15_diverge.py :: NON-TERMINATION (infinite loop after the lookup; a diverging impl satisfies every postcondition vacuously unless termination bites at the METHOD level) :: exit 2, REJECTED -- MustTerminate(2) at the method level does its job.
16. $D/atk_16_double_key.py :: BOUNDARY/key-shape corruption (key = resolved name DOUBLED; same alphabet, same first-half prefix) :: exit 2, REJECTED -- a length- or prefix-only spec would have admitted it.
17. $D/atk_17_triple_lookup.py :: UNBOUNDED CALL COUNT on the A-consumed callee (the spec never bounds how many times the downstream lookup runs -- the residual the prior pass flagged as "A2 would be improved by stating exactly ONE coercion"). Three do_lookup calls, keyed on the last :: weakness exit 0 CANDIDATE (21.3s). Faithful patch MATERIALIZED and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO. The real downstream lookup is idempotent+memoizing, so repeating it is observationally neutral. The residual is REAL but BENIGN on this oracle; measured, not assumed.
18. $D/atk_18_fresh_copy.py :: FRESHNESS INVERSION (return a fresh element-by-element COPY instead of the object the lookup keeps -- the exact converse of the prior break: the prior defect was that the spec let the impl OWN/mutate the served object; this asks whether the spec now requires handing back the lookup's own object) :: weakness exit 0 CANDIDATE (21.1s). Faithful patch MATERIALIZED (`return list(_served)` for the mutable list carrier) and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO. The spec's Wildcard permits either identity, and the F2P/P2P suite compares by equality, so this is unobservable to the oracle.

### CONTROLS (all executed):
  POSITIVE CONTROL $D/pos_ctl_cachedbound.py -- structurally different but CORRECT (cached bound `clen`, inverted `not (i >= clen)` loop test, extra redundant framing asserts): `bash scripts/nagini_verify.sh` -> "Verification successful", 21.08s, exit 0. The spec is not too strong on this reshape, so the 14 rejections are real rejections and not a spec that rejects everything.
  VACUITY CONTROL $D/vac_ctl_assert_false.py -- Assert(False) appended to an otherwise-correct impl: FAILS with `Assert might fail. Assertion False might not hold.` (20.93s, exit 1). The proof context is FEASIBLE, so no rejection above is a vacuity artifact. (Per my standing note that guarded self-calls / infeasible contexts can verify while proving nothing, Assert(False) is the control I always run.)
  ATTRIBUTION CONTROL $D/patch_ctl_refactor.diff -- the identical `_do_lookup` extraction scaffolding shared by the atk_13/17/18 patches, plus the gold coercion, single call, no mutation/copy -> resolved=True, F2P 2/2, P2P 104/104. Proves the refactor scaffolding is innocent, so each candidate's RESOLVE attributes to its own delta and not to the harness plumbing.

A-LEG AUDIT (refinement.md), the brief's focus: A1 (param <-> format_type) R and A4 (return value) R -- type refinement, G-CONF's lane; no complaint. A2 (copy loop <-> `format_type = str(format_type)`) A-REFERENCE -- correspondence HOLDS. Provenance re-verified by me at base_commit 8c0886b0 in a fresh worktree: `lazy()` at functional.py:87 and `__proxy__.__str__` at functional.py:171-174 (`return str(self.__cast())`), so str(proxy) yields the underlying string and str() is identity on a real str; `resolve` ignoring the `deferred` flag is therefore correct. axiom_check.py validates it on 21 boundary + 5000 fuzz names in BOTH forms, including the F2P witnesses "DATE_FORMAT" and "H:i". Correctly NOT consumed as an axiom (no coercion axiom exists in the axioms region).

TWO RESIDUALS, both PROBED AND BOTH BENIGN-BY-EXECUTION, not by argument: (a) resolve is a pure function of ft.content so the model proves two coercions agree while real lazy() re-evaluates per access -> atk_10, patch RESOLVED; (b) the copy loop is a carrier-materialization artifact, not a distinct behavioural step, so an impl that skips it still verifies -> atk_13, patch RESOLVED. Documentation nit (not a gate failure): the A2 row would be improved by stating that exactly ONE coercion is performed and that the copy loop's role is materializing the List[int] carrier rather than mirroring a second repo operation. A3 (do_lookup/format_value <-> formats.py:116-143) A-CONSUMED -- THIS IS THE LEG THAT PREVIOUSLY BROKE, AND IT IS NOW SOUND.

The prior defect was precisely that the axiom was NOT the "weakest sufficient contract" it advertised: `Ensures(Acc(list_pred(Result())))` additionally asserted exclusive ownership/freshness of the returned list, which is FALSE of the real callee (it memoizes -- `return _format_cache[cache_key]` / `_format_cache[cache_key] = val` -- and for the *_INPUT_FORMATS names the cached value is a real mutable list, formats.py:138 `val = list(val)`), so successive calls hand back the SAME object. The shipped bytes replace that with `Wildcard(list_pred(...))` on the name AND the Result, at the axiom and at lookup_format's postcondition, and add explicit prose that neither the name nor the value is owned across a request and that the value served may be the name object itself.

That is now a TRUE statement about the memoizing callee: read access only, no freshness, no non-aliasing conclusion available to a caller. I attacked the new clause from BOTH sides -- can an impl still mutate the served object (atk_5/6/7/8: all REJECTED, `insufficient permission`) and does the weaker clause now over-permit in the other direction, e.g. by admitting return-the-name (atk_14: REJECTED) or requiring/forbidding a fresh copy (atk_18: verifies, patch RESOLVES, unobservable) -- and it holds on both. KIND-3 CHECK: NO kind-3 (unexpressible-changed-op) steps.

All four legs are tagged R / A-reference / A-consumed / R (grepped: lines 34-37 of refinement.md); the leg-kind vocabulary is complete with no untagged or "unexpressible" step. refinement.md section B's claim that the changed coercion is modeled DEEPLY rather than hidden behind an axiom about the function under change is ACCURATE -- I confirmed the axioms region declares only format_value/do_lookup (the UNCHANGED downstream lookup) and that `resolve` lives in the pure region as a spelled-out body, so the discriminating content of the fix is genuinely proof-carrying rather than assumed. The G-DIFF direction is confirmed independently by atk_1 and atk_12.

HONEST RESIDUAL DISCLOSURE (not a break; the gate criterion is a non-resolving faithful patch, and none exists): the spec still under-determines call count (atk_17) and returned-object identity (atk_18) relative to the real callee. Both are unobservable to THIS oracle because get_format is idempotent+memoizing and the F2P/P2P suite compares values by equality. I did not dismiss either on that reasoning alone -- I materialized and RAN both patches. A future harness that asserted `get_format(x) is get_format(x)` would separate atk_18 from gold; that is a latent tightening opportunity, not a current verify-not-implies-correct.

**OVERLAP DISCLOSURE:** verdict.md carries retained G-EQ=fail / G-PANEL-1=fail / G-PANEL-2=fail labels rooted in the SAME `Acc(list_pred(Result()))` clause. Per protocol I did NOT re-judge those retained labels or inherit their verdict -- I re-derived every witness from scratch on the CURRENT bytes and re-ran the three named breaks myself. They no longer verify. Note the recorded G-EQ fail timestamp (2026-08-14T13:38) PRECEDES model.py's mtime (Aug 14 19:33) and audits a different md5, while every other gate in meta.json was re-checked at Aug 15 00:29-00:32 and passes -- consistent with a repair landing after the G-EQ/G-PANEL audits and those two lanes simply not having been re-run. Routing note for the fleet: this is a STALE-FAIL cell (a stale fail judging an already-repaired spec), the pattern I have logged before; it needs an audit re-run, not a repair wave.

**RUN HYGIENE:** no host-saturation artifacts -- every one of the 18 weakness checks and both direct verifies terminated with a REAL verdict (no exit 124, no timeout, no "inconclusive" string in any of $D/wk_*.txt; grepped explicitly). All 5 resolve runs report completed=True, flaky=False, attempts=1, so no verdict is read out of a failed measurement. All 5 patches confirmed to apply cleanly at base_commit via `git apply --check` BEFORE the harness ran. The probing git worktree was removed (`git worktree remove --force` + `worktree prune`). Bundle left byte-untouched (model.py md5 unchanged; `git status --porcelain benchmark-verified/django__django-15741/` clean). One stray file was briefly created outside the scratch dir by my own path typo and was deleted immediately; all retained artifacts are under $D/: base_model.py, base_prepatch.py, gen.py, resolve_one.py, atk_1..18, pos_ctl_cachedbound.py, vac_ctl_assert_false.py, patch_{gold,atk10,atk13,atk17,atk18,ctl_refactor}.diff, resolve_*.json, rlog_*.txt, wk_*.txt, ss_all.txt, verify_posctl.txt, verify_vacctl.txt.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1_prepatch.py`, `atk_2_empty_key.py`, `atk_3_drop_last.py`, `atk_4_oracle_echo.py`, `atk_5_poison_store0.py`, `atk_6_poison_result.py`, `atk_7_poison_eager_only.py`, `atk_8_poison_name.py`, `atk_9_poison_append.py`, `atk_11_swap_ends.py`, `atk_12_deferred_trunc.py`, `atk_14_return_name.py`, `atk_15_diverge.py`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_10_double_resolve.py`, `atk_13_no_copy.py`, `atk_17_triple_lookup.py`, `atk_18_fresh_copy.py` |

**Non-vacuity.** The positive control `pos_ctl_cachedbound.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl was found whose faithful refined patch fails to resolve. 18 same-spec attacks run; 14 REJECTED by the spec, 4 CANDIDATES (verify) whose materialized faithful patches were all EXECUTED through the official harness and ALL RESOLVED (F2P 2/2, P2P 104/104, completed=True, flaky=False, attempts=1 each) — i.e. they are correct-alternative echoes, not weaknesses.

SPECIFICALLY: the PRIOR RECORDED BREAK IS REPAIRED AND I RE-TESTED IT DIRECTLY. verdict.md records G-EQ=fail at 2026-08-14T13:38 on atk_7_poison_store0.py (P2P 99/104), rooted in the do_lookup axiom's `Ensures(Acc(list_pred(Result())))` — FULL/EXCLUSIVE ownership of the returned list, which let a verifying impl destructively store into the object the real _format_cache keeps. The shipped model.py is NEWER than that verdict (mtime Aug 14 19:33 vs verdict 13:38; md5 72cdb6273913e2092abe6dda54f72139, NOT the 9c4dae79c8522d3acdeb25f2e3c891db the prior pass audited) and replaces those clauses with `Wildcard(list_pred(...))` on both the name and the Result, at the axiom AND at lookup_format's postcondition. I re-encoded ALL THREE prior breaks verbatim (atk_5_poison_store0 = old atk_7; atk_6_poison_result = old atk_8 mutation-after; atk_7_poison_eager_only = old atk_9 deferred-flag-guarded last-index store) and ALL THREE NOW FAIL TO VERIFY, each with the precise causal error `The precondition of extra[0] = 88 / result[0] = 88 might not hold. There might be insufficient permission.` The repair bites exactly where the defect was, so the recorded fail is STALE against these bytes.
```

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_empty_key.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_drop_last.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_oracle_echo.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_poison_store0.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_poison_result.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_poison_eager_only.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_poison_name.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_poison_append.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_double_resolve.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_swap_ends.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_deferred_trunc.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_no_copy.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14_return_name.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_diverge.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_double_key.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_triple_lookup.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18_fresh_copy.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctl_cachedbound.py`

```python
"""Twin-artifact model for django__django-15741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A localisation lookup is requested by a *name*. That name is supplied as a
  string-valued argument, which may arrive in either of two equivalent forms:

    * already-resolved — the name is directly available as a sequence of
      characters; or
    * deferred — the name is wrapped in a placeholder that only yields its
      character sequence once it is resolved (the same character sequence the
      resolved form carries).

  The looked-up value must depend ONLY on the resolved character sequence of
  the requested name. Two requests whose names resolve to the same character
  sequence MUST return the same value, regardless of whether either name
  arrived already-resolved or deferred. In particular, requesting a name in its
  deferred form returns exactly what requesting the same name in its
  already-resolved form returns.

  A request must also leave the looked-up values as it found them. The value a
  requester is handed for a name is the one the downstream lookup itself keeps
  and hands out again to every later request for that name -- it does not become
  the requester's own object to modify, and where the lookup holds no separate
  value for a name it may hand back the name object itself. So a request obtains
  read access to that value and passes it on, and the value associated with a
  name is the same after a request as it was before it: a later request for the
  same name still yields the same value.

  Nothing changes hands in the other direction either. Asking with a name does
  not modify it, but it does not leave the requester in sole possession of it:
  the downstream lookup keys itself on the resolved name and keeps hold of what
  it was keyed with. So read access is all a request needs of a name and all it
  gives back -- and since neither the name nor the value is anyone's exclusive
  property across a request, the value served for a name may be that very name.

The name is modelled as a minimal object carrying a ``deferred`` flag and its
underlying character sequence as ``List[int]`` of Unicode code points (Nagini
bans ``str`` indexing). ``resolve`` is the deep model of the placeholder-to-text
coercion: it yields the underlying character sequence in both forms and is
validated == the real coercion by axiom_check.py (G-AX), NOT consumed as an
axiom. The unchanged downstream lookup keyed on a resolved name is modelled by
the pure ``format_value`` (a deterministic function of the resolved character
sequence) and its list-producing companion ``do_lookup``; their soundness —
that the real lookup is determined by the resolved name only — is checked by
G-AX.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class FormatType:
    def __init__(self, deferred: bool, content: List[int]) -> None:
        Requires(Acc(list_pred(content), 1 / 2))
        # Two field stores, loop-free: the constructor always terminates. Level 1
        # so a level-2 body (lookup_format, and the admissibility witness that
        # builds a concrete FormatType) can call it without leaking its own
        # obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.deferred) and self.deferred == deferred)  # type: ignore
        Ensures(Acc(self.content) and self.content is content)  # type: ignore
        Ensures(Acc(list_pred(content), 1 / 2))
        self.deferred = deferred
        self.content = content

# axioms-start
@Pure
@ContractOnly
def format_value(name: PSeq[int]) -> PSeq[int]:
    """The value of the unchanged downstream localisation lookup, keyed on the
    *resolved* character sequence of the requested name. It is a deterministic
    function of that sequence alone (same resolved name -> same value). The
    proof consumes only this functional determinism. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """

@ContractOnly
def do_lookup(name: List[int]) -> List[int]:
    """The unchanged downstream lookup as a list-producing operation: given a
    fully-resolved name it returns the value for that name. Its character
    content is exactly ``format_value`` of the resolved name (so the value
    depends only on the resolved characters). Read-only in the name.

    The value handed back stays the lookup's own: the very same object is handed
    out again to every later request for that name, and for a name the lookup
    holds no separate value for it is the name object itself. A caller therefore
    obtains read access to that value and never the exclusive access that
    modifying it would take; nothing here asserts that the value is an object
    distinct from the name, or one the caller may keep for itself."""
    # It only READS the name it is given: read access is all it needs and all it
    # gives back, and it never takes ownership of the name.
    Requires(Wildcard(list_pred(name)))
    # A keyed dictionary lookup over the resolved name: bounded, loop-free work,
    # so it always terminates. Level 1, strictly below the level-2 caller.
    Requires(MustTerminate(1))
    Ensures(Wildcard(list_pred(name)))
    # Read access to the value the lookup serves for this name, never ownership
    # of it: a caller may read what the name is associated with, and may not
    # modify it. Because neither the name nor the value is owned across this
    # call, the value being the name object itself stays POSSIBLE here -- a
    # requester may not conclude the two are distinct objects.
    Ensures(Wildcard(list_pred(Result())))
    Ensures(ToSeq(Result()) == format_value(ToSeq(name)))
# axioms-end

# pure-start
@Pure
def resolve(ft: FormatType) -> PSeq[int]:
    """The resolved character sequence of a requested name. A deferred name and
    an already-resolved name yield the SAME underlying character sequence: the
    resolution does not depend on the ``deferred`` flag. Deep model of the
    placeholder-to-text coercion, validated == the real coercion by G-AX."""
    Requires(Acc(ft.content) and Acc(list_pred(ft.content), 1 / 4))
    return ToSeq(ft.content)
# pure-end

def lookup_format(requested_name: FormatType) -> List[int]:
    # pre-conditions-start
    # The requested name is read-only (directive 5): nothing about it is
    # mutated by the lookup.
    Requires(Acc(requested_name.deferred, 1 / 2))
    Requires(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
    # The lookup terminates. Level 2: strictly above do_lookup / FormatType.
    # __init__ (level 1), and high enough that list.__init__ (building `name`)
    # has room below the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(requested_name.deferred, 1 / 2))
    Ensures(Acc(requested_name.content, 1 / 2))
    # NOTHING IS OWNED ACROSS A REQUEST. The requester keeps read access to the
    # name it asked with -- the request does not modify that name -- but not
    # exclusive ownership of it: the downstream lookup keys itself on the resolved
    # name and holds on to what it was keyed with, so a requester cannot take the
    # name back for its own exclusive use once it has asked with it.
    Ensures(Wildcard(list_pred(requested_name.content)))
    # And the requester obtains READ access to the value the name is associated
    # with, never ownership of it. So the request leaves that association as it
    # found it -- the same name requested afterwards still yields the same value
    # -- and read access is all there is to hand over anyway, since the value
    # served may be the object the downstream lookup keeps, or the name itself.
    # Read access on both sides is also what keeps those two POSSIBLY THE SAME
    # object: nothing here lets a requester conclude that the value it was handed
    # is an object distinct from the name it asked with.
    Ensures(Wildcard(list_pred(Result())))
    # The value depends only on the RESOLVED character sequence of the name.
    # Because ``resolve`` ignores the deferred flag, a deferred name and an
    # already-resolved name with the same characters return the same value.
    Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
    # post-conditions-end
    # impl-start
    clen = len(requested_name.content)
    name = []  # type: List[int]
    i = 0
    while not (i >= clen):
        # invariants-start
        Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
        Invariant(clen == len(requested_name.content))
        Invariant(Acc(list_pred(name)))
        Invariant(0 <= i and i <= clen)
        Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
        Invariant(MustTerminate(clen - i + 1))
        # invariants-end
        name.append(requested_name.content[i])
        i = i + 1
    Assert(i == clen)
    Assert(ToSeq(requested_name.content).take(clen) == ToSeq(requested_name.content))
    Assert(ToSeq(name) == resolve(requested_name))
    result = do_lookup(name)
    Assert(ToSeq(result) == format_value(resolve(requested_name)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### COMMANDS (repo root swe-proof; D=):
  python -m swebench_unified.adversary same-spec nagini django__django-15741 $D/<f>.py
  python -m swebench_unified.adversary weakness  nagini django__django-15741 $D/<f>.py
  bash scripts/nagini_verify.sh $D/pos_ctl_cachedbound.py   (and $D/vac_ctl_assert_false.py)
  SBU_BENCHMARK_DIR=benchmark-verified python $D/resolve_one.py $D/patch_<tag>.diff <tag>   # harness.run_resolve

### PER-ATTACK RESULTS (path :: class :: observed):
 1. $D/atk_1_prepatch.py :: PREPATCH RE-ENCODE (impl region verbatim from the bundle's model_prepatch.py: the deferred name is fed to the lookup unresolved -- the literal getattr(module,<lazy>) bug) :: weakness exit 2, does not verify -> spec REJECTS the prepatch bug. prepatch_reproduced=True.
 2. $D/atk_2_empty_key.py :: PARTIAL-DOMAIN degenerate (never resolve; look up the empty key) :: exit 2, REJECTED.
 3. $D/atk_3_drop_last.py :: BOUNDARY off-by-one (loop bound len-1, drop the last code point) :: exit 2, REJECTED.
 4. $D/atk_4_oracle_echo.py :: UNGROUNDED-ORACLE ECHO (do_lookup(do_lookup(name)) => format_value(format_value(x))) :: exit 2, REJECTED -- the oracle is grounded at resolve(name)==ToSeq(content); no free value to echo.
 5. $D/atk_5_poison_store0.py :: REGRESSION of PRIOR BREAK #1 (old atk_7_poison_store0): destructive store at index 0 of a looked-up value :: exit 2, REJECTED with `insufficient permission` on `extra[0] = 88`. **PRIOR BREAK REPAIRED.**
 6. $D/atk_6_poison_result.py :: REGRESSION of PRIOR BREAK #2 (old atk_8): mutate the RETURNED object :: exit 2, REJECTED with `insufficient permission` on `result[0] = 88`. **REPAIRED.**
 7. $D/atk_7_poison_eager_only.py :: REGRESSION of PRIOR BREAK #3 (old atk_9): last-index store GUARDED by the deferred flag (fires only on the already-resolved branch) :: exit 2, REJECTED. **REPAIRED.**
 8. $D/atk_8_poison_name.py :: ownership over-claim on the NAME side (mutate the resolved key AFTER handing it to the lookup, which keys `_format_cache` on it) :: exit 2, REJECTED.
 9. $D/atk_9_poison_append.py :: CONTROL-FLOW-EFFECT, non-destructive APPEND flavour (this VERIFIED in the prior pass and its patch RESOLVED; kept as the append-vs-store attribution control) :: exit 2, now REJECTED too -- the Wildcard repair is strictly stronger than needed for the break, and rejects the benign flavour as well.
10. $D/atk_10_double_resolve.py :: A-REFERENCE probe (resolve is a pure function of ft.content, so the model proves two independent resolutions identical, whereas functional.py lazy() explicitly does NOT memoize -- "Results are not memoized; the function is evaluated on every access", functional.py:87-92, and `__proxy__`.`__str__` at functional.py:171-174 re-evaluates `__cast`() on every access) :: weakness exit 0 CANDIDATE (21.5s). Faithful patch MATERIALIZED (two independent str(format_type) coercions, keyed on the second) and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO, not a break (the wrapped callable is side-effect-free on this oracle). Reported as executed, not speculated.
11. $D/atk_11_swap_ends.py :: ORDER-INSENSITIVITY (resolve then transpose first/last code point -- same multiset, different sequence) :: exit 2, REJECTED -- the postcondition is genuinely sequence-valued.
12. $D/atk_12_deferred_trunc.py :: PARTIAL-DOMAIN branch-selective KEY corruption (on the DEFERRED branch only, look up a truncated key -- the prepatch bug in subtler dress) :: exit 2, REJECTED. This is the discriminating leg and it holds.
13. $D/atk_13_no_copy.py :: A2-LEG probe: SKIP the copy loop entirely, hand do_lookup `requested_name.content` itself (tests whether the loop the A2 leg maps to `str(format_type)` is load-bearing) :: weakness exit 0 CANDIDATE (18.6s). Faithful patch MATERIALIZED (pass the resolved value straight into the extracted downstream lookup, no intermediate copy bound) and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO. Benign because in the real code the coercion still happens at the call; the copy loop is a MATERIALIZATION artifact of the List[int] carrier, not a distinct behavioural step.
14. $D/atk_14_return_name.py :: ALIASING-PROSE EXPLOIT -- the axiom docstring and postcondition go out of their way to keep "the value served for a name may be that very name" POSSIBLE; this returns the name UNCONDITIONALLY :: exit 2, REJECTED. The permissive aliasing prose grants only the POSSIBILITY (no non-aliasing conclusion), it does NOT admit returning the name as the value -- the functional postcondition still pins the value to format_value(resolve(...)). Good.
15. $D/atk_15_diverge.py :: NON-TERMINATION (infinite loop after the lookup; a diverging impl satisfies every postcondition vacuously unless termination bites at the METHOD level) :: exit 2, REJECTED -- MustTerminate(2) at the method level does its job.
16. $D/atk_16_double_key.py :: BOUNDARY/key-shape corruption (key = resolved name DOUBLED; same alphabet, same first-half prefix) :: exit 2, REJECTED -- a length- or prefix-only spec would have admitted it.
17. $D/atk_17_triple_lookup.py :: UNBOUNDED CALL COUNT on the A-consumed callee (the spec never bounds how many times the downstream lookup runs -- the residual the prior pass flagged as "A2 would be improved by stating exactly ONE coercion"). Three do_lookup calls, keyed on the last :: weakness exit 0 CANDIDATE (21.3s). Faithful patch MATERIALIZED and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO. The real downstream lookup is idempotent+memoizing, so repeating it is observationally neutral. The residual is REAL but BENIGN on this oracle; measured, not assumed.
18. $D/atk_18_fresh_copy.py :: FRESHNESS INVERSION (return a fresh element-by-element COPY instead of the object the lookup keeps -- the exact converse of the prior break: the prior defect was that the spec let the impl OWN/mutate the served object; this asks whether the spec now requires handing back the lookup's own object) :: weakness exit 0 CANDIDATE (21.1s). Faithful patch MATERIALIZED (`return list(_served)` for the mutable list carrier) and EXECUTED: resolved=True, completed=True, attempts=1, flaky=False, F2P 2/2, P2P 104/104. => ECHO. The spec's Wildcard permits either identity, and the F2P/P2P suite compares by equality, so this is unobservable to the oracle.

### CONTROLS (all executed):
  POSITIVE CONTROL $D/pos_ctl_cachedbound.py -- structurally different but CORRECT (cached bound `clen`, inverted `not (i >= clen)` loop test, extra redundant framing asserts): `bash scripts/nagini_verify.sh` -> "Verification successful", 21.08s, exit 0. The spec is not too strong on this reshape, so the 14 rejections are real rejections and not a spec that rejects everything.
  VACUITY CONTROL $D/vac_ctl_assert_false.py -- Assert(False) appended to an otherwise-correct impl: FAILS with `Assert might fail. Assertion False might not hold.` (20.93s, exit 1). The proof context is FEASIBLE, so no rejection above is a vacuity artifact. (Per my standing note that guarded self-calls / infeasible contexts can verify while proving nothing, Assert(False) is the control I always run.)
  ATTRIBUTION CONTROL $D/patch_ctl_refactor.diff -- the identical `_do_lookup` extraction scaffolding shared by the atk_13/17/18 patches, plus the gold coercion, single call, no mutation/copy -> resolved=True, F2P 2/2, P2P 104/104. Proves the refactor scaffolding is innocent, so each candidate's RESOLVE attributes to its own delta and not to the harness plumbing.

A-LEG AUDIT (refinement.md), the brief's focus: A1 (param <-> format_type) R and A4 (return value) R -- type refinement, G-CONF's lane; no complaint. A2 (copy loop <-> `format_type = str(format_type)`) A-REFERENCE -- correspondence HOLDS. Provenance re-verified by me at base_commit 8c0886b0 in a fresh worktree: `lazy()` at functional.py:87 and `__proxy__.__str__` at functional.py:171-174 (`return str(self.__cast())`), so str(proxy) yields the underlying string and str() is identity on a real str; `resolve` ignoring the `deferred` flag is therefore correct. axiom_check.py validates it on 21 boundary + 5000 fuzz names in BOTH forms, including the F2P witnesses "DATE_FORMAT" and "H:i". Correctly NOT consumed as an axiom (no coercion axiom exists in the axioms region).

TWO RESIDUALS, both PROBED AND BOTH BENIGN-BY-EXECUTION, not by argument: (a) resolve is a pure function of ft.content so the model proves two coercions agree while real lazy() re-evaluates per access -> atk_10, patch RESOLVED; (b) the copy loop is a carrier-materialization artifact, not a distinct behavioural step, so an impl that skips it still verifies -> atk_13, patch RESOLVED. Documentation nit (not a gate failure): the A2 row would be improved by stating that exactly ONE coercion is performed and that the copy loop's role is materializing the List[int] carrier rather than mirroring a second repo operation. A3 (do_lookup/format_value <-> formats.py:116-143) A-CONSUMED -- THIS IS THE LEG THAT PREVIOUSLY BROKE, AND IT IS NOW SOUND.

The prior defect was precisely that the axiom was NOT the "weakest sufficient contract" it advertised: `Ensures(Acc(list_pred(Result())))` additionally asserted exclusive ownership/freshness of the returned list, which is FALSE of the real callee (it memoizes -- `return _format_cache[cache_key]` / `_format_cache[cache_key] = val` -- and for the *_INPUT_FORMATS names the cached value is a real mutable list, formats.py:138 `val = list(val)`), so successive calls hand back the SAME object. The shipped bytes replace that with `Wildcard(list_pred(...))` on the name AND the Result, at the axiom and at lookup_format's postcondition, and add explicit prose that neither the name nor the value is owned across a request and that the value served may be the name object itself.

That is now a TRUE statement about the memoizing callee: read access only, no freshness, no non-aliasing conclusion available to a caller. I attacked the new clause from BOTH sides -- can an impl still mutate the served object (atk_5/6/7/8: all REJECTED, `insufficient permission`) and does the weaker clause now over-permit in the other direction, e.g. by admitting return-the-name (atk_14: REJECTED) or requiring/forbidding a fresh copy (atk_18: verifies, patch RESOLVES, unobservable) -- and it holds on both. KIND-3 CHECK: NO kind-3 (unexpressible-changed-op) steps.

All four legs are tagged R / A-reference / A-consumed / R (grepped: lines 34-37 of refinement.md); the leg-kind vocabulary is complete with no untagged or "unexpressible" step. refinement.md section B's claim that the changed coercion is modeled DEEPLY rather than hidden behind an axiom about the function under change is ACCURATE -- I confirmed the axioms region declares only format_value/do_lookup (the UNCHANGED downstream lookup) and that `resolve` lives in the pure region as a spelled-out body, so the discriminating content of the fix is genuinely proof-carrying rather than assumed. The G-DIFF direction is confirmed independently by atk_1 and atk_12.

HONEST RESIDUAL DISCLOSURE (not a break; the gate criterion is a non-resolving faithful patch, and none exists): the spec still under-determines call count (atk_17) and returned-object identity (atk_18) relative to the real callee. Both are unobservable to THIS oracle because get_format is idempotent+memoizing and the F2P/P2P suite compares values by equality. I did not dismiss either on that reasoning alone -- I materialized and RAN both patches. A future harness that asserted `get_format(x) is get_format(x)` would separate atk_18 from gold; that is a latent tightening opportunity, not a current verify-not-implies-correct.

**OVERLAP DISCLOSURE:** verdict.md carries retained G-EQ=fail / G-PANEL-1=fail / G-PANEL-2=fail labels rooted in the SAME `Acc(list_pred(Result()))` clause. Per protocol I did NOT re-judge those retained labels or inherit their verdict -- I re-derived every witness from scratch on the CURRENT bytes and re-ran the three named breaks myself. They no longer verify. Note the recorded G-EQ fail timestamp (2026-08-14T13:38) PRECEDES model.py's mtime (Aug 14 19:33) and audits a different md5, while every other gate in meta.json was re-checked at Aug 15 00:29-00:32 and passes -- consistent with a repair landing after the G-EQ/G-PANEL audits and those two lanes simply not having been re-run. Routing note for the fleet: this is a STALE-FAIL cell (a stale fail judging an already-repaired spec), the pattern I have logged before; it needs an audit re-run, not a repair wave.

**RUN HYGIENE:** no host-saturation artifacts -- every one of the 18 weakness checks and both direct verifies terminated with a REAL verdict (no exit 124, no timeout, no "inconclusive" string in any of $D/wk_*.txt; grepped explicitly). All 5 resolve runs report completed=True, flaky=False, attempts=1, so no verdict is read out of a failed measurement. All 5 patches confirmed to apply cleanly at base_commit via `git apply --check` BEFORE the harness ran. The probing git worktree was removed (`git worktree remove --force` + `worktree prune`). Bundle left byte-untouched (model.py md5 unchanged; `git status --porcelain benchmark-verified/django__django-15741/` clean). One stray file was briefly created outside the scratch dir by my own path typo and was deleted immediately; all retained artifacts are under $D/: base_model.py, base_prepatch.py, gen.py, resolve_one.py, atk_1..18, pos_ctl_cachedbound.py, vac_ctl_assert_false.py, patch_{gold,atk10,atk13,atk17,atk18,ctl_refactor}.diff, resolve_*.json, rlog_*.txt, wk_*.txt, ss_all.txt, verify_posctl.txt, verify_vacctl.txt.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: faithfulness-break attack on model.py sha256 4ab071fcd8c8cc8b0928d7345c75c23ff714212f6f88e374140912bb5b7fb130 (the CURRENT bundle bytes, matching meta.json G-AX/G-CONF/G-VERIFY sources). Reference =, a fresh worktree at base_commit 8c0886b068 with patch.diff APPLIED (verified the single inserted line `format_type = str(format_type)` at formats.py:116).

PRIOR-VERDICT NOTE (load-bearing): meta.json carries G-PANEL-2 status=fail / agent_verdict=UNFAITHFUL, but that record's sources pin model.py = 30bef81e3630... -- a DIFFERENT, since-repaired artifact. The prior defect was do_lookup/lookup_format granting EXCLUSIVE `Ensures(Acc(list_pred(Result())))`, from which the spec derived a false freshness fact (`result is not name`, `result is not other`) that the real get_format refutes (it returns the cached object, and returns the name itself for names outside FORMAT_SETTINGS). I re-derived rather than inheriting the retained label, and the current bytes use `Wildcard(list_pred(...))` on both the name and the Result. I rebuilt the prior panel's exact five probes from current bytes; the two unfaithfulness probes NO LONGER verify. The recorded finding is stale, not reproducible on shipped bytes.

All 9 probes built by editing ONLY the impl region; `adversary same-spec` exit 0 ("SAME") on every one.

REPAIR CONFIRMED -- the prior UNFAITHFUL facts are no longer derivable:
  n2f_p1_argfresh.py  Assert(result is not name)  -> FAILED "Assertion (result is not name) might not hold" (28.95s)
  n2f_p2_twocall.py   Assert(result is not other) -> FAILED "Assertion (result is not other) might not hold" (22.05s)
The spec is now AGNOSTIC on aliasing in both directions, which is exactly right, since the real callee aliases both ways.

### CONTROLS (none vacuous, all FAIL -> the two results above are genuine agnosticism, not a dead proof context):
  n2f_ctlA_false.py   Assert(False)          -> FAILED (13.19s)
  n2f_ctlB_isname.py  Assert(result is name) -> FAILED (14.39s)
  n2f_ctlC_issame.py  Assert(result is other)-> FAILED (20.83s)
ctlB/ctlC failing alongside p1/p2 is the two-sided control: the spec commits to NEITHER aliasing nor non-aliasing, matching a callee that may or may not return its own argument.

### OVER-STRENGTH PROBES (each a real behaviour of the patched callee that a too-strong spec would forbid; all ADMITTED):
  1. No-copy path. Real `str(s) is s` for an already-resolved str -- the patch makes no copy. n2f_nocopy.py replaces the copy loop with `do_lookup(requested_name.content)` -> VERIFIES (16.63s). The spec does not mandate the copy loop as the only route; it constrains the resolved-value relation.
  2. Deferred-flag independence. n2f_flagindep.py builds a twin with the OPPOSITE deferred flag and asserts resolve(twin) == resolve(requested_name) -> VERIFIES (12.51s). Confirms the spec lets a faithful impl ignore `deferred` entirely, which real str() does.

UNDER-STRENGTH / SAFETY PROBES (real code must NOT do these; spec correctly FORBIDS both):
  3. n2f_mutres.py  result.append(42) -> FAILED "precondition of append might not hold. There might be insufficient permission." Correct: get_format returns the `_format_cache`'s OWN object (and for unknown names the name itself); mutating it would corrupt the cache. Wildcard grants read, not write.
  4. n2f_mutname.py name.append(42) -> FAILED, same reason. Real code never mutates the name.

**DETERMINISM CLAUSE CROSS-CHECKED AGAINST REALITY:** n2f_det.py asserts ToSeq(result)==ToSeq(other) across two do_lookup calls -> VERIFIES, so the spec DOES commit to cross-call determinism in the name. I probed this as the strongest candidate over-strength, since format_value is @Pure in the resolved name alone while the real get_format also reads the ambient active locale. Measured on the real patched repo (n2f_locale.py): get_format IS locale-dependent (DATE_FORMAT distinct=4 across en/de/ca/fr; DECIMAL_SEPARATOR '.' vs ','). This is NOT a divergence: the modeled scope is a single get_format call with no interleaved locale change, and n2f_det_real.py confirms 0 divergences on consecutive real lookups over 6 names x both forms. The locale is ambient context held fixed across the modeled call, correctly abstracted as a fixed interpretation of format_value, and mapping.md sec.3.2 scopes the axiom to exactly that.

NON-MEMOIZED LAZY EDGE CASE (resolve-exactly-once): lazy() explicitly does NOT memoize ("Results are not memoized; the function is evaluated on every access", functional.py:87), so a proxy could in principle resolve to different strings on repeated access and break the single-resolved-sequence abstraction. Built a flip-flopping proxy (n2f_nondet.py): the real patched get_format evaluates the proxy EXACTLY ONCE (evaluations=1) and returns get_format of that one resolution ('N j, Y'). The model's single `resolve(requested_name)` is faithful; the patch's up-front single coercion is what guarantees it. Pre-patch this was the actual defect (two separate getattr uses of the un-coerced value).

ADVERSARIAL NAMES OUTSIDE THE BUNDLE'S OWN ALPHABET (n2f_adv.py, 27 names the harness never tries): dunders (`__class__`, `__dict__`, `__name__`, `__file__`, `__loader__`), settings names (DEBUG, SECRET_KEY, INSTALLED_APPS, SETTINGS_MODULE, `_wrapped`), module attrs (get_format, datetime), control chars (\x00, \n, \t, 'DATE_FORMAT\x00'), 500-char name, and Unicode case/normalization traps (fi ligature, dotted-I, sharp-s, long-s, emoji) -- chosen because getattr/dict-key paths are where a str-vs-proxy abstraction would break. 0 divergences: eager and deferred agree on every one, including exception identity.

BUNDLE HARNESSES RE-RUN INDEPENDENTLY against my own patched worktree (not trusting recorded stamps): axiom_check.py exit 0 (5000 fuzz + 21 boundary; resolve == real str() on both forms); conformance_check.py exit 0, 100063 inputs, 0 disagreements, shadow impl == real get_format.

ORACLE DIRECTION CONFIRMED BOTH WAYS (rules out a spec that models nothing): with patch.diff + test_patch, both F2P pass (i18n.tests.FormattingTests.test_get_format_lazy_format, template_tests.filter_tests.test_date.DateTests.test_date_lazy -- Ran 2, OK). Reverting ONLY django/utils/formats.py to base_commit reproduces the exact modeled bug: TypeError: getattr(): attribute name must be string, both tests ERROR. So the modeled function's reference behaviour is the fixed behaviour, and the spec's discriminating clause tracks the real delta.

**CONCLUSION:** FAITHFUL. No input found on which the modeled lookup_format disagrees with the real patched get_format under mapping.md's refinement. The spec is agnostic exactly where the real callee is unconstrained (aliasing of the returned value with the name and across calls, whether the resolution copies), and committal exactly where the real callee is determined (value keyed only on the resolved character sequence, read-only in both the name and the value, single resolution). The one clause that goes beyond the literal callee -- purity of format_value in the name while real get_format also reads the active locale -- is sound under the modeled single-call scope and was empirically confirmed on the real repo. I could not construct a diverging input, so I do not claim a defect; the stale UNFAITHFUL record in meta.json is not reproducible on the bytes the bundle now ships and should be re-stamped.

**SCOPE:** faithfulness-break attack on model.py sha256 4ab071fcd8c8cc8b0928d7345c75c23ff714212f6f88e374140912bb5b7fb130 (the CURRENT bundle bytes, matching meta.json G-AX/G-CONF/G-VERIFY sources). Reference =, a fresh worktree at base_commit 8c0886b068 with patch.diff APPLIED (verified the single inserted line `format_type = str(format_type)` at formats.py:116).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: leakage / gold-reconstruction on the consumer spec view of benchmark-verified/django__django-15741/nagini/model.py (sha256 4ab071fcd8c8...5b7fb130, matches every meta.json gates[*].sources entry for the current pass gates: G-VERIFY/G-LEAK/G-AX/G-CONF/G-DIFF/G-GOLD/G-MUT/G-HYGIENE/G-INTEGRITY/G-PBT).

NO relaxation present: meta.json has no `relaxed_leakage` key (walked the whole tree for /relax/i -- zero hits) and there is no RELAXED_LEAKAGE.md anywhere under benchmark-verified/django__django-15741/ (find -iname '*RELAX*' empty). So this is a plain strict-mode judgement, not an inherited disposition.

What I measured, on the projected spec view (swebench_unified.markers.spec_view with the nagini backend -- 160 lines; impl region replaced by the elision placeholder, invariants region gone with it):

1. Same-spec anchor: `python -m swebench_unified.adversary same-spec nagini django__django-15741 atk.py` (atk = verbatim model.py) -> exit 0, "SAME -- attack shares the bundle's exact specification". markers.same_spec(model.py, model_prepatch.py) is also True and spec_signature matches, so the spec region is byte-identical across the twin and the spec view I judged is the one a consumer receives.

2. Mechanical screen re-run from source (not read off meta.json): swebench_unified.leakage.screen(model.py, NaginiBackend, row['patch'], row['problem_statement'], row['test_patch']) -> passed=True, hard_failures=[], warnings=[]. Instance row taken from data/swe_bench_verified/test.jsonl and confirmed byte-identical to the frozen benchmark-verified/django__django-15741/instance.json for both problem_statement and patch; hints_text is empty for this instance, so the hints-vs-statement distinction is moot here.

3. Manual gold-reconstruction scan (the part the screen cannot do). The gold edit is a single inserted line in django/utils/formats.py: `format_type = str(format_type)  # format_type may be lazy.` immediately before `cache_key = (format_type, lang)`. Grepped the spec view for every token that would localize it: str( , lazy, Lazy, `__proxy__`, gettext, cache, `_format_cache`, cache_key, getattr, settings, FORMAT_SETTINGS, ISO_INPUT, use_l10n, lang, formats.py, get_format, format_type, TypeError, coerce, DATE_FORMAT, 'H:i', 'N j, Y', Y-m-d, i18n, test_ -- ALL absent. Only 'django' (in the instance-id docstring header, which is the bundle name, not a repo path), 'placeholder' and 'coercion' appear, and both are the model's own abstract vocabulary for the already-resolved/deferred pair, not repo symbols. No patched file path, no dotted module path, no diff marker, no changed-line reproduction (screen's L1/L2 checks plus my own read).

4. Is the discriminator public? Yes, entirely from the problem_statement: 'django.utils.formats.get_format should allow lazy parameter' + 'the date template filter ... receives a lazy string, like in some_date|date:_("Y-m-d") ... fails with TypeError: getattr(): attribute name must be string in django.utils.formats.get_format'. The statement names the two forms (ordinary string vs lazy string), the function, and the failure. The spec view's discriminating clause -- resolve() ignoring the `deferred` flag so `ToSeq(Result()) == format_value(resolve(requested_name))` must hold for a deferred name too -- is exactly the behaviour the public statement demands ('should allow lazy parameter'), phrased abstractly and with the repo vocabulary stripped. A solver derives 'resolve the possibly-deferred name before keying the lookup' from the statement alone; the spec view adds no edit-location, no mechanism (nothing says 'coerce with str()' or 'do it before building the cache key'), and no test witness. It states the required behaviour, which is the point of a spec.

5. Load-bearingness control (so I am not calling a vacuous clause 'unavoidable'): ran the pinned verifier directly on both twins. `bash scripts/nagini_verify.sh m.py` -> exit 0, 'Verification successful' (15.1s). `bash scripts/nagini_verify.sh pre.py` (model_prepatch.py, whose impl resolves only on the deferred==False branch) -> exit 1 with 'Postcondition of lookup_format might not hold. Assertion (ToSeq(Result()) == format_value(resolve(requested_name))) might not hold.' at line 156. So the resolved-name postcondition genuinely rejects the PRE-patch impl -- it is a real discriminator carrying weight, and it is also the only place the deferred/resolved distinction is spec'd, i.e. nothing extra was smuggled in alongside it.

6. Reviewer-directedness: ran leakage.reviewer_directed over every file in the bundle (model.py, model_prepatch.py, mapping.md, refinement.md, axiom_check.py, conformance_check.py, properties.py, meta.json, pbt_result.json, verdict.md) -> [] for all. Grepped for panel/auditor/reviewer/NO-LEAKAGE in the spec-adjacent docs: no file addresses this role or prescribes a verdict. Nothing in the bundle tried to tell me what to record.

7. Where the repo-specific detail DOES live, correctly out of view: mapping.md quotes the inserted gold line and the formats.py line numbers, and refinement.md quotes the gold hunk. Both are refinement-audit documents, not the consumer spec view; the spec view is the projection of model.py only, and it contains none of that. mapping.md even flags its delta paragraph as 'for the refinement audit, not referenced from the consumer spec view', which I confirmed by the token scan in (3).

Caveats recorded for the record, neither of which is a leakage finding:
- meta.json['region_hashes'] does NOT reproduce from the shipped model.py under markers.region_hashes with the current markers.py (only the 'pure' region matches; axioms/pre/post/invariants/impl/spec_view all differ). I bisected: those hashes reproduce EXACTLY (all seven, including spec_view) from model.py at commit 2cb887e7f, i.e. they are stale from the pre-MustTerminate/Wildcard revision and were not refreshed when model.py was last edited. I therefore did not rely on region_hashes for the byte-identity claim -- I used same_spec/spec_signature and a direct spec_view diff instead. The spec-view delta between 2cb887e7f and HEAD that this staleness hides is the addition of MustTerminate levels, Wildcard permissions, and the aliasing/read-access prose; I inspected that diff line by line and it leaks nothing (it is permission-model hardening against store-poisoning attacks, phrased in ownership vocabulary with no repo symbols).
- G-EQ and G-PANEL/G-PANEL-1/G-PANEL-2 are recorded FAIL on this cell from an OLDER model.py (sources sha 30bef81e..., commit eda4fe422) -- a spec-too-weak store-poisoning counterexample (atk_7_poison_store0.py). Those are different facets and a different artifact revision; the current model.py's added Wildcard/read-access clauses are visibly the response to that attack. Out of scope for layer 3, but flagged so the cell's greenness is not read off my verdict alone: this is a NO-LEAKAGE on the leakage facet only, not a statement that the cell is green.

**Scope:** leakage / gold-reconstruction on the consumer spec view of benchmark-verified/django__django-15741/nagini/model.py (sha256 4ab071fcd8c8...5b7fb130, matches every meta.json gates[*].sources entry for the current pass gates: G-VERIFY/G-LEAK/G-AX/G-CONF/G-DIFF/G-GOLD/G-MUT/G-HYGIENE/G-INTEGRITY/G-PBT).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
