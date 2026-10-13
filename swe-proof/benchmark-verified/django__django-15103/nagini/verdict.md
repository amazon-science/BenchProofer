# P2 adversarial audit — django__django-15103

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,78 +113,44 @@
         ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
     # post-conditions-end
     # impl-start
-    if element_id is not None and len(element_id) > 0:
-        # opening tag carrying the identifier, then the media-type attribute
+    if element_id is not None:
         result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
-        Assert(ToSeq(result) == tag_open_with_id())
         i = 0
         while i < len(element_id):
-            # invariants-start
             Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(element_id))
             Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
-            # the copy loop consumes the caller's termination obligation with a
-            # strictly decreasing measure (len(element_id) - i), discharging
-            # MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(element_id) - i + 1))
-            # invariants-end
             result.append(element_id[i])
             i = i + 1
         Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
-        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
         result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                            108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                            111, 110, 34, 62]
-        Assert(ToSeq(result) == prefix_with_id(element_id))
-        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
-        # append the payload, then the closing tag
         j = 0
         while j < len(payload):
-            # invariants-start
             Invariant(Acc(list_pred(payload), 1 / 2))
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(prefix_a == prefix_with_id(element_id))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(payload))
-            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
-            # payload copy loop: strictly decreasing measure (len(payload) - j)
-            # discharges MustTerminate(2) from the precondition.
+            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id) + attr_close_and_type() + ToSeq(payload).take(j))
             Invariant(MustTerminate(len(payload) - j + 1))
-            # invariants-end
             result.append(payload[j])
             j = j + 1
-        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
         result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
-        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
         return result
-    # opening tag carrying ONLY the media-type attribute (no id attribute)
     result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
               61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
               47, 106, 115, 111, 110, 34, 62]
-    Assert(ToSeq(result) == tag_open_no_id())
-    prefix_b = tag_open_no_id()  # type: PSeq[int]
-    # append the payload, then the closing tag
     k = 0
     while k < len(payload):
-        # invariants-start
         Invariant(Acc(list_pred(payload), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(payload))
-        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
-        # payload copy loop: strictly decreasing measure (len(payload) - k)
-        # discharges MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == tag_open_no_id() + ToSeq(payload).take(k))
         Invariant(MustTerminate(len(payload) - k + 1))
-        # invariants-end
         result.append(payload[k])
         k = k + 1
-    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
     result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
-    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
     return result
     # impl-end
```

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,78 +113,18 @@
         ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
     # post-conditions-end
     # impl-start
-    if element_id is not None and len(element_id) > 0:
-        # opening tag carrying the identifier, then the media-type attribute
-        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
-        Assert(ToSeq(result) == tag_open_with_id())
-        i = 0
-        while i < len(element_id):
-            # invariants-start
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(element_id))
-            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
-            # the copy loop consumes the caller's termination obligation with a
-            # strictly decreasing measure (len(element_id) - i), discharging
-            # MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(element_id) - i + 1))
-            # invariants-end
-            result.append(element_id[i])
-            i = i + 1
-        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
-        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
-        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
-                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
-                           111, 110, 34, 62]
-        Assert(ToSeq(result) == prefix_with_id(element_id))
-        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
-        # append the payload, then the closing tag
-        j = 0
-        while j < len(payload):
-            # invariants-start
-            Invariant(Acc(list_pred(payload), 1 / 2))
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(prefix_a == prefix_with_id(element_id))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(payload))
-            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
-            # payload copy loop: strictly decreasing measure (len(payload) - j)
-            # discharges MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(payload) - j + 1))
-            # invariants-end
-            result.append(payload[j])
-            j = j + 1
-        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
-        result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
-        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
-        return result
-    # opening tag carrying ONLY the media-type attribute (no id attribute)
     result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
               61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
               47, 106, 115, 111, 110, 34, 62]
-    Assert(ToSeq(result) == tag_open_no_id())
-    prefix_b = tag_open_no_id()  # type: PSeq[int]
-    # append the payload, then the closing tag
     k = 0
     while k < len(payload):
-        # invariants-start
         Invariant(Acc(list_pred(payload), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(payload))
-        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
-        # payload copy loop: strictly decreasing measure (len(payload) - k)
-        # discharges MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == tag_open_no_id() + ToSeq(payload).take(k))
         Invariant(MustTerminate(len(payload) - k + 1))
-        # invariants-end
         result.append(payload[k])
         k = k + 1
-    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
     result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
-    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
     return result
     # impl-end
```

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,35 +114,23 @@
     # post-conditions-end
     # impl-start
     if element_id is not None and len(element_id) > 0:
-        # opening tag carrying the identifier, then the media-type attribute
         result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
-        Assert(ToSeq(result) == tag_open_with_id())
         i = 0
         while i < len(element_id):
-            # invariants-start
             Invariant(Acc(list_pred(element_id), 1 / 2))
             Invariant(len(element_id) > 0)
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(element_id))
             Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
-            # the copy loop consumes the caller's termination obligation with a
-            # strictly decreasing measure (len(element_id) - i), discharging
-            # MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(element_id) - i + 1))
-            # invariants-end
             result.append(element_id[i])
             i = i + 1
-        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
-        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
         result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                            108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                            111, 110, 34, 62]
-        Assert(ToSeq(result) == prefix_with_id(element_id))
         prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
-        # append the payload, then the closing tag
         j = 0
         while j < len(payload):
-            # invariants-start
             Invariant(Acc(list_pred(payload), 1 / 2))
             Invariant(Acc(list_pred(element_id), 1 / 2))
             Invariant(len(element_id) > 0)
@@ -150,41 +138,22 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(payload))
             Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
-            # payload copy loop: strictly decreasing measure (len(payload) - j)
-            # discharges MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(payload) - j + 1))
-            # invariants-end
             result.append(payload[j])
             j = j + 1
-        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
         result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
-        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
         return result
-    # opening tag carrying ONLY the media-type attribute (no id attribute)
     result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
               61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
               47, 106, 115, 111, 110, 34, 62]
-    Assert(ToSeq(result) == tag_open_no_id())
-    prefix_b = tag_open_no_id()  # type: PSeq[int]
-    # append the payload, then the closing tag
     k = 0
     while k < len(payload):
-        # invariants-start
         Invariant(Acc(list_pred(payload), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(payload))
-        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
-        # payload copy loop: strictly decreasing measure (len(payload) - k)
-        # discharges MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == tag_open_no_id() + ToSeq(payload).take(k))
         Invariant(MustTerminate(len(payload) - k + 1))
-        # invariants-end
         result.append(payload[k])
         k = k + 1
-    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
-    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
     return result
     # impl-end
```

Attack 4 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -113,78 +113,9 @@
         ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
     # post-conditions-end
     # impl-start
-    if element_id is not None and len(element_id) > 0:
-        # opening tag carrying the identifier, then the media-type attribute
-        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
-        Assert(ToSeq(result) == tag_open_with_id())
-        i = 0
-        while i < len(element_id):
-            # invariants-start
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(element_id))
-            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
-            # the copy loop consumes the caller's termination obligation with a
-            # strictly decreasing measure (len(element_id) - i), discharging
-            # MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(element_id) - i + 1))
-            # invariants-end
-            result.append(element_id[i])
-            i = i + 1
-        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
-        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
-        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
-                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
-                           111, 110, 34, 62]
-        Assert(ToSeq(result) == prefix_with_id(element_id))
-        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
-        # append the payload, then the closing tag
-        j = 0
-        while j < len(payload):
-            # invariants-start
-            Invariant(Acc(list_pred(payload), 1 / 2))
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(prefix_a == prefix_with_id(element_id))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(payload))
-            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
-            # payload copy loop: strictly decreasing measure (len(payload) - j)
-            # discharges MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(payload) - j + 1))
-            # invariants-end
-            result.append(payload[j])
-            j = j + 1
-        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
-        result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
-        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
-        return result
-    # opening tag carrying ONLY the media-type attribute (no id attribute)
-    result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
-              61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-              47, 106, 115, 111, 110, 34, 62]
-    Assert(ToSeq(result) == tag_open_no_id())
-    prefix_b = tag_open_no_id()  # type: PSeq[int]
-    # append the payload, then the closing tag
-    k = 0
-    while k < len(payload):
-        # invariants-start
+    while True:
         Invariant(Acc(list_pred(payload), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= k and k <= len(payload))
-        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
-        # payload copy loop: strictly decreasing measure (len(payload) - k)
-        # discharges MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(payload) - k + 1))
-        # invariants-end
-        result.append(payload[k])
-        k = k + 1
-    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
-    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
+        Invariant(Implies(element_id is not None, Acc(list_pred(element_id), 1 / 2)))
+    result = [60, 47, 115, 99, 114, 105, 112, 116, 62]  # type: List[int]
     return result
     # impl-end
```

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,77 +114,31 @@
     # post-conditions-end
     # impl-start
     if element_id is not None and len(element_id) > 0:
-        # opening tag carrying the identifier, then the media-type attribute
         result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
-        Assert(ToSeq(result) == tag_open_with_id())
         i = 0
         while i < len(element_id):
-            # invariants-start
             Invariant(Acc(list_pred(element_id), 1 / 2))
             Invariant(len(element_id) > 0)
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(element_id))
             Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
-            # the copy loop consumes the caller's termination obligation with a
-            # strictly decreasing measure (len(element_id) - i), discharging
-            # MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(element_id) - i + 1))
-            # invariants-end
             result.append(element_id[i])
             i = i + 1
-        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
-        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
-        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
-                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
-                           111, 110, 34, 62]
-        Assert(ToSeq(result) == prefix_with_id(element_id))
-        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
-        # append the payload, then the closing tag
-        j = 0
-        while j < len(payload):
-            # invariants-start
-            Invariant(Acc(list_pred(payload), 1 / 2))
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(prefix_a == prefix_with_id(element_id))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(payload))
-            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
-            # payload copy loop: strictly decreasing measure (len(payload) - j)
-            # discharges MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(payload) - j + 1))
-            # invariants-end
-            result.append(payload[j])
-            j = j + 1
-        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
         result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
-        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
         return result
-    # opening tag carrying ONLY the media-type attribute (no id attribute)
     result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
               61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
               47, 106, 115, 111, 110, 34, 62]
-    Assert(ToSeq(result) == tag_open_no_id())
-    prefix_b = tag_open_no_id()  # type: PSeq[int]
-    # append the payload, then the closing tag
     k = 0
     while k < len(payload):
-        # invariants-start
         Invariant(Acc(list_pred(payload), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(payload))
-        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
-        # payload copy loop: strictly decreasing measure (len(payload) - k)
-        # discharges MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == tag_open_no_id() + ToSeq(payload).take(k))
         Invariant(MustTerminate(len(payload) - k + 1))
-        # invariants-end
         result.append(payload[k])
         k = k + 1
-    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
     result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
-    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
     return result
     # impl-end
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,35 +114,23 @@
     # post-conditions-end
     # impl-start
     if element_id is not None and len(element_id) > 0:
-        # opening tag carrying the identifier, then the media-type attribute
         result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
-        Assert(ToSeq(result) == tag_open_with_id())
         i = 0
         while i < len(element_id):
-            # invariants-start
             Invariant(Acc(list_pred(element_id), 1 / 2))
             Invariant(len(element_id) > 0)
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(element_id))
             Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
-            # the copy loop consumes the caller's termination obligation with a
-            # strictly decreasing measure (len(element_id) - i), discharging
-            # MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(element_id) - i + 1))
-            # invariants-end
             result.append(element_id[i])
             i = i + 1
-        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
-        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
         result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                            108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                            111, 110, 34, 62]
-        Assert(ToSeq(result) == prefix_with_id(element_id))
         prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
-        # append the payload, then the closing tag
         j = 0
         while j < len(payload):
-            # invariants-start
             Invariant(Acc(list_pred(payload), 1 / 2))
             Invariant(Acc(list_pred(element_id), 1 / 2))
             Invariant(len(element_id) > 0)
@@ -150,41 +138,23 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(payload))
             Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
-            # payload copy loop: strictly decreasing measure (len(payload) - j)
-            # discharges MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(payload) - j + 1))
-            # invariants-end
             result.append(payload[j])
             j = j + 1
-        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
         result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
-        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
         return result
-    # opening tag carrying ONLY the media-type attribute (no id attribute)
     result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
               61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
               47, 106, 115, 111, 110, 34, 62]
-    Assert(ToSeq(result) == tag_open_no_id())
-    prefix_b = tag_open_no_id()  # type: PSeq[int]
-    # append the payload, then the closing tag
     k = 0
-    while k < len(payload):
-        # invariants-start
+    while k < len(payload) - 1:
         Invariant(Acc(list_pred(payload), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(payload))
-        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
-        # payload copy loop: strictly decreasing measure (len(payload) - k)
-        # discharges MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == tag_open_no_id() + ToSeq(payload).take(k))
         Invariant(MustTerminate(len(payload) - k + 1))
-        # invariants-end
         result.append(payload[k])
         k = k + 1
-    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
     result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
-    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
     return result
     # impl-end
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -113,78 +113,23 @@
         ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
     # post-conditions-end
     # impl-start
-    if element_id is not None and len(element_id) > 0:
-        # opening tag carrying the identifier, then the media-type attribute
-        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
-        Assert(ToSeq(result) == tag_open_with_id())
-        i = 0
-        while i < len(element_id):
-            # invariants-start
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(element_id))
-            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
-            # the copy loop consumes the caller's termination obligation with a
-            # strictly decreasing measure (len(element_id) - i), discharging
-            # MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(element_id) - i + 1))
-            # invariants-end
-            result.append(element_id[i])
-            i = i + 1
-        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
-        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
-        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
-                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
-                           111, 110, 34, 62]
-        Assert(ToSeq(result) == prefix_with_id(element_id))
-        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
-        # append the payload, then the closing tag
-        j = 0
-        while j < len(payload):
-            # invariants-start
-            Invariant(Acc(list_pred(payload), 1 / 2))
-            Invariant(Acc(list_pred(element_id), 1 / 2))
-            Invariant(len(element_id) > 0)
-            Invariant(prefix_a == prefix_with_id(element_id))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(payload))
-            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
-            # payload copy loop: strictly decreasing measure (len(payload) - j)
-            # discharges MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(payload) - j + 1))
-            # invariants-end
-            result.append(payload[j])
-            j = j + 1
-        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
-        result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
-        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
-        return result
-    # opening tag carrying ONLY the media-type attribute (no id attribute)
+    spin = 0
+    while spin < len(payload) + 1:
+        Invariant(Acc(list_pred(payload), 1 / 2))
+        Invariant(spin >= 0)
+        spin = spin
     result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
               61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
-              47, 106, 115, 111, 110, 34, 62]
-    Assert(ToSeq(result) == tag_open_no_id())
-    prefix_b = tag_open_no_id()  # type: PSeq[int]
-    # append the payload, then the closing tag
+              47, 106, 115, 111, 110, 34, 62]  # type: List[int]
     k = 0
     while k < len(payload):
-        # invariants-start
         Invariant(Acc(list_pred(payload), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(payload))
-        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
-        # payload copy loop: strictly decreasing measure (len(payload) - k)
-        # discharges MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == tag_open_no_id() + ToSeq(payload).take(k))
         Invariant(MustTerminate(len(payload) - k + 1))
-        # invariants-end
         result.append(payload[k])
         k = k + 1
-    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
     result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
-    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
-    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15103.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A serialized JSON payload is wrapped in an HTML ``<script>`` element of media
  type ``application/json``. The element's identifying attribute is OPTIONAL:

    * When an identifier is supplied (a present, non-empty token), the opening
      tag carries that identifier as an ``id`` attribute, immediately followed
      by the media-type attribute, then the payload, then the closing tag.

    * When no identifier is supplied (absent, or an empty token), the opening
      tag carries ONLY the media-type attribute — the ``id`` attribute and its
      value are absent from the output entirely — followed by the payload and
      the closing tag.

  In both cases the wrapped payload is identical (the same already-serialized
  character sequence); only the presence/absence of the identifying attribute
  differs. The two outputs share the common prefix ``<script`` and the common
  suffix `` type="application/json">`` + payload + ``</script>``.

Wrapping is a bounded, straight-line assembly: the operation MUST terminate
and return the wrapped element (a total-correctness obligation, carried as
MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver the rendered markup to the caller.

Character data is modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over ``PSeq[int]``. The optional
identifier is modelled as ``Optional[List[int]]`` (absent identifier == ``None``;
an empty list models an empty token, which is likewise treated as absent).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axiomatized callees: the modelled behaviour is the conditional assembly of
# constant markup around an already-serialized payload. Payload serialization
# and HTML attribute encoding are unchanged callees, not part of the modelled
# operation; see refinement.md / mapping.md.)
# axioms-end

# pure-start
@Pure
def tag_open_with_id() -> PSeq[int]:
    # '<script id="'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34)

@Pure
def attr_close_and_type() -> PSeq[int]:
    # '" type="application/json">'
    return PSeq(34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112, 108,
                105, 99, 97, 116, 105, 111, 110, 47, 106, 115, 111, 110, 34, 62)

@Pure
def tag_open_no_id() -> PSeq[int]:
    # '<script type="application/json">'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
                61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 106, 115, 111, 110, 34, 62)

@Pure
def tag_close() -> PSeq[int]:
    # '</script>'
    return PSeq(60, 47, 115, 99, 114, 105, 112, 116, 62)

@Pure
def prefix_with_id(ident: List[int]) -> PSeq[int]:
    """The opening-tag prefix WHEN an identifier is present: the id-bearing
    opening tag carries the identifier as an id attribute, then the media-type
    attribute."""
    Requires(Acc(list_pred(ident), 1 / 4))
    Ensures(Result() == tag_open_with_id() + ToSeq(ident) + attr_close_and_type())
    return tag_open_with_id() + ToSeq(ident) + attr_close_and_type()
# pure-end

def build_json_script(payload: List[int], element_id: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(payload), 1 / 2))
    Requires(Implies(element_id is not None, Acc(list_pred(element_id), 1 / 2)))
    # Wrapping is a bounded, straight-line assembly: the operation MUST
    # terminate and return the wrapped element (total correctness). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver the rendered markup to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Implies(element_id is not None, Acc(list_pred(element_id), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # An identifier counts as present iff it is supplied and non-empty; an empty
    # token is treated the same as an absent one.
    # When present: the output is the id-bearing opening tag (carrying the
    # identifier before the media-type), then the payload, then the closing tag.
    Ensures(Implies(
        element_id is not None and len(element_id) > 0,
        ToSeq(Result()) == prefix_with_id(element_id) + ToSeq(payload) + tag_close()))
    # When absent (or empty): the output is the opening tag carrying ONLY the
    # media-type attribute (the id attribute is absent entirely), then the
    # payload, then the closing tag.
    Ensures(Implies(
        element_id is None or len(element_id) == 0,
        ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
    # post-conditions-end
    # impl-start
    if element_id is not None and len(element_id) > 0:
        # opening tag carrying the identifier, then the media-type attribute
        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
        Assert(ToSeq(result) == tag_open_with_id())
        i = 0
        while i < len(element_id):
            # invariants-start
            Invariant(Acc(list_pred(element_id), 1 / 2))
            Invariant(len(element_id) > 0)
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(element_id))
            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
            # the copy loop consumes the caller's termination obligation with a
            # strictly decreasing measure (len(element_id) - i), discharging
            # MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(element_id) - i + 1))
            # invariants-end
            result.append(element_id[i])
            i = i + 1
        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                           111, 110, 34, 62]
        Assert(ToSeq(result) == prefix_with_id(element_id))
        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
        # append the payload, then the closing tag
        j = 0
        while j < len(payload):
            # invariants-start
            Invariant(Acc(list_pred(payload), 1 / 2))
            Invariant(Acc(list_pred(element_id), 1 / 2))
            Invariant(len(element_id) > 0)
            Invariant(prefix_a == prefix_with_id(element_id))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(payload))
            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
            # payload copy loop: strictly decreasing measure (len(payload) - j)
            # discharges MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(payload) - j + 1))
            # invariants-end
            result.append(payload[j])
            j = j + 1
        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
        result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
        return result
    # opening tag carrying ONLY the media-type attribute (no id attribute)
    result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
              61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
              47, 106, 115, 111, 110, 34, 62]
    Assert(ToSeq(result) == tag_open_no_id())
    prefix_b = tag_open_no_id()  # type: PSeq[int]
    # append the payload, then the closing tag
    k = 0
    while k < len(payload):
        # invariants-start
        Invariant(Acc(list_pred(payload), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(payload))
        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
        # payload copy loop: strictly decreasing measure (len(payload) - k)
        # discharges MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(payload) - k + 1))
        # invariants-end
        result.append(payload[k])
        k = k + 1
    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for django__django-15103 (nagini). adversary run with SBU_BENCHMARK_DIR=benchmark-verified via python -m swebench_unified.adversary {same-spec,verify,weakness} nagini django__django-15103 <file>. Attack verifications run concurrently (<=3 JVM+Z3 at a time).

RESULT: NO CANDIDATE counterexample found. Every same-spec wrong impl fails to verify, so there is no verifying wrong impl whose faithful refined patch could be materialized/resolved. patches={} accordingly. Verdict SOUND.

SPEC SHAPE: build_json_script postconditions FULLY pin ToSeq(Result()) in BOTH complementary branches (present = element_id is not None and len>0 -> prefix_with_id(element_id)+payload+tag_close(); absent/empty -> tag_open_no_id()+payload+tag_close()) and carry Requires(MustTerminate(2)). Tightly-closed value spec + enforced total correctness -> admits only the gold-equivalent assembly.

BASELINES: positive_control.py (= bundle model.py) VERIFIES (verify exit 0, 8-45s). prepatch.py (= model_prepatch.py, always-id-bearing) FAILS verify exit 1 on exactly the absent-id postcondition Implies(element_id is None or len(element_id)==0, ToSeq(Result())==tag_open_no_id()+ToSeq(payload)+tag_close()) -> prepatch bug reproduced (G-DIFF).

7 DISTINCT same-spec wrong impls (all same-spec exit 0; impl-region-only edits; all rejected except atk_5, which the front end refused to translate, so the spec never judged it):
- atk_2 BOUNDARY: empty element_id treated as PRESENT (drops len>0) -> weakness exit 2, verify FAILED.
- atk_3 CONTROL-FLOW/CONTENT: present branch emits id-free tag -> exit 2, FAILED (present-branch postcondition).
- atk_4 CONTROL-FLOW-EFFECT/PARTIAL: absent branch drops closing tag </script> -> exit 2, FAILED.
- atk_5 CONTROL-FLOW-EFFECT/DIVERGENCE: `while True` before return -> exit 2, NOT JUDGED: the front end refused to translate the program (Type error dead.code), so it never reached the verifier and the spec never ruled on it — it counts in neither tally. The shape is unexpressible in nagini's fragment, so this attack did not exercise the spec's method-level MustTerminate; whether that clause would reject a translatable diverging rival is a separate question it does not settle.
- atk_6 CONTENT: present branch omits media-type segment (id then straight to close) -> exit 2, FAILED (present-branch postcondition).
- atk_7 BOUNDARY/off-by-one: absent-branch payload loop `k < len-1` drops last payload byte -> exit 2, FAILED (absent-branch postcondition).
- atk_8 CONTROL-FLOW-EFFECT/DIVERGENCE (reachable, not dead code): reachable spin loop `while spin < len(payload)+1` with non-decreasing measure before correct assembly -> verify FAILED with 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' This confirms refinement.md D's exact claim: MustTerminate truly closes the vacuous-satisfaction hole; a value-only-correct diverging rival is rejected.

All 8 verify runs completed fast (8-45s), NONE timed out (exit 124), so the NOT-VERIFY verdicts are genuine spec rejections, not inconclusive infra timeouts; atk_5 is the exception — a front-end translation refusal, so no spec verdict either way. verify_completed for every attack.

REFINEMENT.md LEG AUDIT (A-legs + correspondence, R/I mechanically covered): A1 payload=json.dumps(...).translate(...) = R (str<->List[int], serialization unchanged); A2 element_id Optional = R (None<->absent, empty<->falsy, matches gold `if element_id:`); A3 present template = I+R, literals verified byte-identical to gold '<script id="{}" type="application/json">'; A4 absent template = I+R, literal '<script type="application/json">' verified byte-identical (the discriminating fixed behavior); A5 branch selection = R. Section C: NO kind-3 step; meta axioms=[] confirms no consumed @ContractOnly; the changed op is modeled DEEPLY (concrete code-point literals + verified append loops).

Single deep_model_reference (kind A-reference) = django.utils.html.json_script post-patch + unchanged wrappers format_html/mark_safe, validated by axiom_check.py G-AX (meta records 4119/4119 boundary+fuzz matches). axiom_check.py could not be executed locally (Django only present in eval container, as mapping.md states); audited by inspection + independent verification that all 4 @Pure code-point literals equal the real template strings ('<script id="', '" type="application/json">', '<script type="application/json">', '</script>') via ord() comparison -> all True. A-reference correspondence holds.

INTEGRITY: same-spec projection confirms every attack shares the exact spec signature; only impl regions differ. meta region_hashes present for spec_view/pre/post/pure/axioms/invariants/impl.

CONCLUSION: The frozen spec rejects boundary, content, control-flow-effect, partial-domain, and reachable-divergence wrong impls; the dead-code divergence shape (atk_5) never reached the verifier, so the spec did not rule on it and that flavor is untested here; the only verifying impl is gold-equivalent. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15103.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A serialized JSON payload is wrapped in an HTML ``<script>`` element of media
  type ``application/json``. The element's identifying attribute is OPTIONAL:

    * When an identifier is supplied (a present, non-empty token), the opening
      tag carries that identifier as an ``id`` attribute, immediately followed
      by the media-type attribute, then the payload, then the closing tag.

    * When no identifier is supplied (absent, or an empty token), the opening
      tag carries ONLY the media-type attribute — the ``id`` attribute and its
      value are absent from the output entirely — followed by the payload and
      the closing tag.

  In both cases the wrapped payload is identical (the same already-serialized
  character sequence); only the presence/absence of the identifying attribute
  differs. The two outputs share the common prefix ``<script`` and the common
  suffix `` type="application/json">`` + payload + ``</script>``.

Wrapping is a bounded, straight-line assembly: the operation MUST terminate
and return the wrapped element (a total-correctness obligation, carried as
MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver the rendered markup to the caller.

Character data is modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over ``PSeq[int]``. The optional
identifier is modelled as ``Optional[List[int]]`` (absent identifier == ``None``;
an empty list models an empty token, which is likewise treated as absent).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axiomatized callees: the modelled behaviour is the conditional assembly of
# constant markup around an already-serialized payload. Payload serialization
# and HTML attribute encoding are unchanged callees, not part of the modelled
# operation; see refinement.md / mapping.md.)
# axioms-end

# pure-start
@Pure
def tag_open_with_id() -> PSeq[int]:
    # '<script id="'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34)

@Pure
def attr_close_and_type() -> PSeq[int]:
    # '" type="application/json">'
    return PSeq(34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112, 108,
                105, 99, 97, 116, 105, 111, 110, 47, 106, 115, 111, 110, 34, 62)

@Pure
def tag_open_no_id() -> PSeq[int]:
    # '<script type="application/json">'
    return PSeq(60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
                61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
                47, 106, 115, 111, 110, 34, 62)

@Pure
def tag_close() -> PSeq[int]:
    # '</script>'
    return PSeq(60, 47, 115, 99, 114, 105, 112, 116, 62)

@Pure
def prefix_with_id(ident: List[int]) -> PSeq[int]:
    """The opening-tag prefix WHEN an identifier is present: the id-bearing
    opening tag carries the identifier as an id attribute, then the media-type
    attribute."""
    Requires(Acc(list_pred(ident), 1 / 4))
    Ensures(Result() == tag_open_with_id() + ToSeq(ident) + attr_close_and_type())
    return tag_open_with_id() + ToSeq(ident) + attr_close_and_type()
# pure-end

def build_json_script(payload: List[int], element_id: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(payload), 1 / 2))
    Requires(Implies(element_id is not None, Acc(list_pred(element_id), 1 / 2)))
    # Wrapping is a bounded, straight-line assembly: the operation MUST
    # terminate and return the wrapped element (total correctness). A
    # diverging implementation would satisfy the value postconditions only
    # vacuously and would never deliver the rendered markup to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Implies(element_id is not None, Acc(list_pred(element_id), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # An identifier counts as present iff it is supplied and non-empty; an empty
    # token is treated the same as an absent one.
    # When present: the output is the id-bearing opening tag (carrying the
    # identifier before the media-type), then the payload, then the closing tag.
    Ensures(Implies(
        element_id is not None and len(element_id) > 0,
        ToSeq(Result()) == prefix_with_id(element_id) + ToSeq(payload) + tag_close()))
    # When absent (or empty): the output is the opening tag carrying ONLY the
    # media-type attribute (the id attribute is absent entirely), then the
    # payload, then the closing tag.
    Ensures(Implies(
        element_id is None or len(element_id) == 0,
        ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
    # post-conditions-end
    # impl-start
    if element_id is not None and len(element_id) > 0:
        # opening tag carrying the identifier, then the media-type attribute
        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
        Assert(ToSeq(result) == tag_open_with_id())
        i = 0
        while i < len(element_id):
            # invariants-start
            Invariant(Acc(list_pred(element_id), 1 / 2))
            Invariant(len(element_id) > 0)
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(element_id))
            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
            # the copy loop consumes the caller's termination obligation with a
            # strictly decreasing measure (len(element_id) - i), discharging
            # MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(element_id) - i + 1))
            # invariants-end
            result.append(element_id[i])
            i = i + 1
        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                           111, 110, 34, 62]
        Assert(ToSeq(result) == prefix_with_id(element_id))
        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
        # append the payload, then the closing tag
        j = 0
        while j < len(payload):
            # invariants-start
            Invariant(Acc(list_pred(payload), 1 / 2))
            Invariant(Acc(list_pred(element_id), 1 / 2))
            Invariant(len(element_id) > 0)
            Invariant(prefix_a == prefix_with_id(element_id))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(payload))
            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
            # payload copy loop: strictly decreasing measure (len(payload) - j)
            # discharges MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(payload) - j + 1))
            # invariants-end
            result.append(payload[j])
            j = j + 1
        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
        result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
        return result
    # opening tag carrying ONLY the media-type attribute (no id attribute)
    result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
              61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
              47, 106, 115, 111, 110, 34, 62]
    Assert(ToSeq(result) == tag_open_no_id())
    prefix_b = tag_open_no_id()  # type: PSeq[int]
    # append the payload, then the closing tag
    k = 0
    while k < len(payload):
        # invariants-start
        Invariant(Acc(list_pred(payload), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(payload))
        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
        # payload copy loop: strictly decreasing measure (len(payload) - k)
        # discharges MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(payload) - k + 1))
        # invariants-end
        result.append(payload[k])
        k = k + 1
    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for django__django-15103 (nagini). adversary run with SBU_BENCHMARK_DIR=benchmark-verified via python -m swebench_unified.adversary {same-spec,verify,weakness} nagini django__django-15103 <file>. Attack verifications run concurrently (<=3 JVM+Z3 at a time).

RESULT: NO CANDIDATE counterexample found. Every same-spec wrong impl fails to verify, so there is no verifying wrong impl whose faithful refined patch could be materialized/resolved. patches={} accordingly. Verdict SOUND.

SPEC SHAPE: build_json_script postconditions FULLY pin ToSeq(Result()) in BOTH complementary branches (present = element_id is not None and len>0 -> prefix_with_id(element_id)+payload+tag_close(); absent/empty -> tag_open_no_id()+payload+tag_close()) and carry Requires(MustTerminate(2)). Tightly-closed value spec + enforced total correctness -> admits only the gold-equivalent assembly.

BASELINES: positive_control.py (= bundle model.py) VERIFIES (verify exit 0, 8-45s). prepatch.py (= model_prepatch.py, always-id-bearing) FAILS verify exit 1 on exactly the absent-id postcondition Implies(element_id is None or len(element_id)==0, ToSeq(Result())==tag_open_no_id()+ToSeq(payload)+tag_close()) -> prepatch bug reproduced (G-DIFF).

7 DISTINCT same-spec wrong impls (all same-spec exit 0; impl-region-only edits; all rejected except atk_5, which the front end refused to translate, so the spec never judged it):
- atk_2 BOUNDARY: empty element_id treated as PRESENT (drops len>0) -> weakness exit 2, verify FAILED.
- atk_3 CONTROL-FLOW/CONTENT: present branch emits id-free tag -> exit 2, FAILED (present-branch postcondition).
- atk_4 CONTROL-FLOW-EFFECT/PARTIAL: absent branch drops closing tag </script> -> exit 2, FAILED.
- atk_5 CONTROL-FLOW-EFFECT/DIVERGENCE: `while True` before return -> exit 2, NOT JUDGED: the front end refused to translate the program (Type error dead.code), so it never reached the verifier and the spec never ruled on it — it counts in neither tally. The shape is unexpressible in nagini's fragment, so this attack did not exercise the spec's method-level MustTerminate; whether that clause would reject a translatable diverging rival is a separate question it does not settle.
- atk_6 CONTENT: present branch omits media-type segment (id then straight to close) -> exit 2, FAILED (present-branch postcondition).
- atk_7 BOUNDARY/off-by-one: absent-branch payload loop `k < len-1` drops last payload byte -> exit 2, FAILED (absent-branch postcondition).
- atk_8 CONTROL-FLOW-EFFECT/DIVERGENCE (reachable, not dead code): reachable spin loop `while spin < len(payload)+1` with non-decreasing measure before correct assembly -> verify FAILED with 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' This confirms refinement.md D's exact claim: MustTerminate truly closes the vacuous-satisfaction hole; a value-only-correct diverging rival is rejected.

All 8 verify runs completed fast (8-45s), NONE timed out (exit 124), so the NOT-VERIFY verdicts are genuine spec rejections, not inconclusive infra timeouts; atk_5 is the exception — a front-end translation refusal, so no spec verdict either way. verify_completed for every attack.

REFINEMENT.md LEG AUDIT (A-legs + correspondence, R/I mechanically covered): A1 payload=json.dumps(...).translate(...) = R (str<->List[int], serialization unchanged); A2 element_id Optional = R (None<->absent, empty<->falsy, matches gold `if element_id:`); A3 present template = I+R, literals verified byte-identical to gold '<script id="{}" type="application/json">'; A4 absent template = I+R, literal '<script type="application/json">' verified byte-identical (the discriminating fixed behavior); A5 branch selection = R. Section C: NO kind-3 step; meta axioms=[] confirms no consumed @ContractOnly; the changed op is modeled DEEPLY (concrete code-point literals + verified append loops).

Single deep_model_reference (kind A-reference) = django.utils.html.json_script post-patch + unchanged wrappers format_html/mark_safe, validated by axiom_check.py G-AX (meta records 4119/4119 boundary+fuzz matches). axiom_check.py could not be executed locally (Django only present in eval container, as mapping.md states); audited by inspection + independent verification that all 4 @Pure code-point literals equal the real template strings ('<script id="', '" type="application/json">', '<script type="application/json">', '</script>') via ord() comparison -> all True. A-reference correspondence holds.

INTEGRITY: same-spec projection confirms every attack shares the exact spec signature; only impl regions differ. meta region_hashes present for spec_view/pre/post/pure/axioms/invariants/impl.

CONCLUSION: The frozen spec rejects boundary, content, control-flow-effect, partial-domain, and reachable-divergence wrong impls; the dead-code divergence shape (atk_5) never reached the verifier, so the spec did not rule on it and that flavor is untested here; the only verifying impl is gold-equivalent. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified spec region byte-identical concern is moot for this analysis; focus is spec-vs-real-callee agreement. The ONLY input class where the model disagrees with the real repo callee is when element_id contains one of the HTML-special chars < > & " '. For those, the model's postcondition emits element_id VERBATIM inside prefix_with_id (i.e. '<script id="' + ident + '" type="application/json">'), while the real post-patch json_script routes element_id through format_html, which applies conditional_escape and HTML-escapes it. This divergence is NOT a faithfulness (spec-too-strong / drift) defect for the following reasons: (1) It is an explicitly DECLARED R-refinement boundary: refinement.md A3 and mapping.md §2 state 'element_id contains no HTML-special characters in the tested usage (identity)'. (2) It concerns the UNCHANGED callee format_html, not the modeled change; the change under test is solely 'make the id attribute optional' (gold commit e6e664a711: if element_id -> id-bearing template else id-free template). (3) The F2P/P2P tests exercise element_id only as the literal 'test_id'; payload-side JSON-script escapes (> < &) ARE modeled and match the real callee exactly. (4) The G-AX soundness check (axiom_check.py) bounds its id domain to HTML-special-free tokens (alnum + '-_') and passes 4119/4119, validating the refinement on exactly the tested/resolution-relevant domain; ran independently and confirmed real json_script == model on all HTML-special-free ids and on all escape-exercising payloads. The model agrees with the real callee character-for-character across the entire declared/tested input domain; the sole disagreement lies strictly outside that domain on an openly-disclosed, unchanged-callee abstraction. Therefore the spec is not too strong on any input within its modeled scope; it faithfully captures the changed behaviour (conditional id attribute) and the escape behaviour of the payload. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl elided) for django__django-15103 nagini. Public problem_statement: 'Make the element_id argument of json_script optional' + use-case of a <script> with no id. The spec describes only the observable behavior: id present -> id-bearing opening tag + media-type + payload + close; id absent/empty -> opening tag with ONLY the media-type attribute (id absent entirely) + payload + close. This is the natural behavioral spec of 'make element_id optional', fully derivable from the public task; it reveals NO implementation detail of the gold patch (no `if element_id:` branching, no template/args tuple restructuring, no `format_html(template, *args)`, no `element_id=None` default signature). Mechanical G-LEAK screen passes: no diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file path (django/utils/html.py, django/template/defaultfilters.py) present, no patched module dotted path, no fix/bug narration. The identifier `json_script` (embedded in `build_json_script`) is public via problem_statement so exempt. Comments phrase behavior as 'desired behaviour, not as an edit', avoiding narration. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
