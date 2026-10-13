# P2 adversarial audit — matplotlib__matplotlib-24637

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_0_prepatch.py`, `atk_2_boundary_swapped.py`, `atk_3_diverge.py`, `atk_4_id_after_body.py`, `atk_6_selfclose_plus_close.py`, `atk_7_no_attr_end.py`, `atk_8_empty_id.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1_partial_empty_gid.py`, `atk_5_partial_amp_gid.py`, `atk_9_oracle_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -201,137 +201,26 @@
         id_attribute(ToSeq(gid)))))
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: the body content is drawn directly into the stream
+    # with NO surrounding group element -- the artist's group id is never
+    # emitted. The rendered output is just the children content.
     result = []  # type: List[int]
-    # emit the id-carrying attribute of the group's start tag:
-    # '<g id="' ++ gid ++ '"'
-    j = 0
-    while j < len(group_open_prefix()):
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(group_open_prefix()))
-        Invariant(ToSeq(result) == group_open_prefix().take(j))
-        # The remaining prefix code points are a strictly decreasing, bounded-
-        # below measure, discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
-        # invariants-end
-        result.append(group_open_prefix()[j])
-        j = j + 1
-    Assert(ToSeq(result) == group_open_prefix())
-    j = 0
-    while j < len(gid):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(gid))
-        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
-        # The remaining id code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(gid) - j + 1))
-        # invariants-end
-        result.append(gid[j])
-        j = j + 1
-    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
-    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
-    j = 0
-    while j < len(attr_end()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(attr_end()))
-        Invariant(ToSeq(result) ==
-                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
-        # The remaining attribute-end code points are the decreasing measure,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(attr_end()) - j + 1))
-        # invariants-end
-        result.append(attr_end()[j])
-        j = j + 1
-    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
-    if len(children) == 0:
-        # No body content was emitted: the start tag is written in the
-        # self-closing form, so it ends with '/>' and there is no separate close.
-        j = 0
-        while j < len(selfclose_end()):
-            # invariants-start
-            Invariant(Acc(list_pred(gid), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(selfclose_end()))
-            Invariant(ToSeq(result) ==
-                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
-            # The remaining self-close code points are the decreasing measure,
-            # discharging MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
-            # invariants-end
-            result.append(selfclose_end()[j])
-            j = j + 1
-        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
-        Assert(len(ToSeq(children)) == len(children))
-        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
-        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
-        return result
-    # Body content was emitted: the start tag ends with '>', the body follows,
-    # and a matching close tag '</g>' terminates the group. The self-closing
-    # branch above returned, so len(children) > 0 holds from here on -- that is
-    # exactly the branch condition grouped_output splits on, so it must be
-    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
-    Assert(len(children) > 0)
-    j = 0
-    while j < len(tag_end()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tag_end()))
-        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
-        # The remaining tag-end code points are the decreasing measure,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(tag_end()) - j + 1))
-        # invariants-end
-        result.append(tag_end()[j])
-        j = j + 1
-    Assert(tag_end().take(len(tag_end())) == tag_end())
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
-    # draw the body content (children) into the stream, unchanged
     j = 0
     while j < len(children):
         # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
         Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(children))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
-        # The remaining body code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == ToSeq(children).take(j))
+        # The pre-patch draw itself TERMINATES -- it walks the body once. The
+        # remaining body code points discharge MustTerminate(2), so the failure
+        # below is attributable to the missing group framing (the bug), not to
+        # an undischarged termination obligation.
         Invariant(MustTerminate(len(children) - j + 1))
         # invariants-end
         result.append(children[j])
         j = j + 1
     Assert(ToSeq(children).take(len(children)) == ToSeq(children))
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
-    # close the group: emit '</g>'
-    j = 0
-    while j < len(group_close()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(group_close()))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
-        # The remaining close code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(group_close()) - j + 1))
-        # invariants-end
-        result.append(group_close()[j])
-        j = j + 1
-    # the self-closing branch returned, so the body is non-empty here: that is
-    # the branch condition grouped_output splits on.
-    Assert(len(ToSeq(children)) == len(children))
-    Assert(len(ToSeq(children)) > 0)
-    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
+    Assert(ToSeq(result) == ToSeq(children))
     return result
     # impl-end
```

Attack 2 — `atk_1_partial_empty_gid.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -201,6 +201,10 @@
         id_attribute(ToSeq(gid)))))
     # post-conditions-end
     # impl-start
+    if len(gid) == 0:
+        # DEAD under Requires(len(gid) > 0): the spec never constrains it.
+        empty = []  # type: List[int]
+        return empty
     result = []  # type: List[int]
     # emit the id-carrying attribute of the group's start tag:
     # '<g id="' ++ gid ++ '"'
```

Attack 3 — `atk_2_boundary_swapped.py` → rejected (same spec, does not verify — good)

```diff
@@ -247,7 +247,7 @@
         result.append(attr_end()[j])
         j = j + 1
     Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
-    if len(children) == 0:
+    if len(children) != 0:
         # No body content was emitted: the start tag is written in the
         # self-closing form, so it ends with '/>' and there is no separate close.
         j = 0
```

Attack 4 — `atk_3_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -333,5 +333,10 @@
     Assert(len(ToSeq(children)) == len(children))
     Assert(len(ToSeq(children)) > 0)
     Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
+    while True:
+        # invariants-start
+        Invariant(Acc(list_pred(result)))
+        # invariants-end
+        pass
     return result
     # impl-end
```

Attack 5 — `atk_4_id_after_body.py` → rejected (same spec, does not verify — good)

```diff
@@ -202,136 +202,53 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # emit the id-carrying attribute of the group's start tag:
-    # '<g id="' ++ gid ++ '"'
+    j = 0
+    while j < len(children):
+        # invariants-start
+        Invariant(Acc(list_pred(children), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= j and j <= len(children))
+        Invariant(ToSeq(result) == ToSeq(children).take(j))
+        Invariant(MustTerminate(len(children) - j + 1))
+        # invariants-end
+        result.append(children[j])
+        j = j + 1
     j = 0
     while j < len(group_open_prefix()):
         # invariants-start
+        Invariant(Acc(list_pred(children), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(group_open_prefix()))
-        Invariant(ToSeq(result) == group_open_prefix().take(j))
-        # The remaining prefix code points are a strictly decreasing, bounded-
-        # below measure, discharging MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == ToSeq(children) + group_open_prefix().take(j))
         Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
         # invariants-end
         result.append(group_open_prefix()[j])
         j = j + 1
-    Assert(ToSeq(result) == group_open_prefix())
     j = 0
     while j < len(gid):
         # invariants-start
         Invariant(Acc(list_pred(gid), 1 / 2))
+        Invariant(Acc(list_pred(children), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(gid))
-        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
-        # The remaining id code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) ==
+                  ToSeq(children) + group_open_prefix() + ToSeq(gid).take(j))
         Invariant(MustTerminate(len(gid) - j + 1))
         # invariants-end
         result.append(gid[j])
         j = j + 1
-    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
-    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
     j = 0
     while j < len(attr_end()):
         # invariants-start
         Invariant(Acc(list_pred(gid), 1 / 2))
+        Invariant(Acc(list_pred(children), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(attr_end()))
-        Invariant(ToSeq(result) ==
-                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
-        # The remaining attribute-end code points are the decreasing measure,
-        # discharging MustTerminate(2) from the precondition.
+        Invariant(ToSeq(result) == ToSeq(children) + group_open_prefix() +
+                  ToSeq(gid) + attr_end().take(j))
         Invariant(MustTerminate(len(attr_end()) - j + 1))
         # invariants-end
         result.append(attr_end()[j])
         j = j + 1
-    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
-    if len(children) == 0:
-        # No body content was emitted: the start tag is written in the
-        # self-closing form, so it ends with '/>' and there is no separate close.
-        j = 0
-        while j < len(selfclose_end()):
-            # invariants-start
-            Invariant(Acc(list_pred(gid), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(selfclose_end()))
-            Invariant(ToSeq(result) ==
-                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
-            # The remaining self-close code points are the decreasing measure,
-            # discharging MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
-            # invariants-end
-            result.append(selfclose_end()[j])
-            j = j + 1
-        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
-        Assert(len(ToSeq(children)) == len(children))
-        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
-        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
-        return result
-    # Body content was emitted: the start tag ends with '>', the body follows,
-    # and a matching close tag '</g>' terminates the group. The self-closing
-    # branch above returned, so len(children) > 0 holds from here on -- that is
-    # exactly the branch condition grouped_output splits on, so it must be
-    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
-    Assert(len(children) > 0)
-    j = 0
-    while j < len(tag_end()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tag_end()))
-        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
-        # The remaining tag-end code points are the decreasing measure,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(tag_end()) - j + 1))
-        # invariants-end
-        result.append(tag_end()[j])
-        j = j + 1
-    Assert(tag_end().take(len(tag_end())) == tag_end())
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
-    # draw the body content (children) into the stream, unchanged
-    j = 0
-    while j < len(children):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(children))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
-        # The remaining body code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(children) - j + 1))
-        # invariants-end
-        result.append(children[j])
-        j = j + 1
-    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
-    # close the group: emit '</g>'
-    j = 0
-    while j < len(group_close()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(group_close()))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
-        # The remaining close code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(group_close()) - j + 1))
-        # invariants-end
-        result.append(group_close()[j])
-        j = j + 1
-    # the self-closing branch returned, so the body is non-empty here: that is
-    # the branch condition grouped_output splits on.
-    Assert(len(ToSeq(children)) == len(children))
-    Assert(len(ToSeq(children)) > 0)
-    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
     return result
     # impl-end
```

Attack 6 — `atk_5_partial_amp_gid.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -201,6 +201,10 @@
         id_attribute(ToSeq(gid)))))
     # post-conditions-end
     # impl-start
+    if len(gid) > 0 and gid[0] == 38:
+        # DEAD under Requires(xml_safe(ToSeq(gid))): 38 (&) is excluded.
+        bare = []  # type: List[int]
+        return bare
     result = []  # type: List[int]
     # emit the id-carrying attribute of the group's start tag:
     # '<g id="' ++ gid ++ '"'
```

Attack 7 — `atk_6_selfclose_plus_close.py` → rejected (same spec, does not verify — good)

```diff
@@ -266,6 +266,16 @@
             j = j + 1
         Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
         Assert(len(ToSeq(children)) == len(children))
+        j = 0
+        while j < len(group_close()):
+            # invariants-start
+            Invariant(Acc(list_pred(gid), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= j and j <= len(group_close()))
+            Invariant(MustTerminate(len(group_close()) - j + 1))
+            # invariants-end
+            result.append(group_close()[j])
+            j = j + 1
         Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
         Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
         return result
```

Attack 8 — `atk_7_no_attr_end.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,7 +216,6 @@
         # invariants-end
         result.append(group_open_prefix()[j])
         j = j + 1
-    Assert(ToSeq(result) == group_open_prefix())
     j = 0
     while j < len(gid):
         # invariants-start
@@ -231,22 +230,6 @@
         result.append(gid[j])
         j = j + 1
     Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
-    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
-    j = 0
-    while j < len(attr_end()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(attr_end()))
-        Invariant(ToSeq(result) ==
-                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
-        # The remaining attribute-end code points are the decreasing measure,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(attr_end()) - j + 1))
-        # invariants-end
-        result.append(attr_end()[j])
-        j = j + 1
-    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
     if len(children) == 0:
         # No body content was emitted: the start tag is written in the
         # self-closing form, so it ends with '/>' and there is no separate close.
@@ -256,8 +239,7 @@
             Invariant(Acc(list_pred(gid), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(selfclose_end()))
-            Invariant(ToSeq(result) ==
-                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
+            Invariant(Acc(list_pred(result)))
             # The remaining self-close code points are the decreasing measure,
             # discharging MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(selfclose_end()) - j + 1))
@@ -266,8 +248,6 @@
             j = j + 1
         Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
         Assert(len(ToSeq(children)) == len(children))
-        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
-        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
         return result
     # Body content was emitted: the start tag ends with '>', the body follows,
     # and a matching close tag '</g>' terminates the group. The self-closing
@@ -283,7 +263,7 @@
         Invariant(len(children) > 0)
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(tag_end()))
-        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
+        Invariant(Acc(list_pred(result)))
         # The remaining tag-end code points are the decreasing measure,
         # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(tag_end()) - j + 1))
@@ -291,7 +271,6 @@
         result.append(tag_end()[j])
         j = j + 1
     Assert(tag_end().take(len(tag_end())) == tag_end())
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
     # draw the body content (children) into the stream, unchanged
     j = 0
     while j < len(children):
@@ -301,8 +280,7 @@
         Invariant(len(children) > 0)
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(children))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
+        Invariant(Acc(list_pred(result)))
         # The remaining body code points are the decreasing measure, discharging
         # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(children) - j + 1))
@@ -310,7 +288,6 @@
         result.append(children[j])
         j = j + 1
     Assert(ToSeq(children).take(len(children)) == ToSeq(children))
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
     # close the group: emit '</g>'
     j = 0
     while j < len(group_close()):
@@ -320,8 +297,7 @@
         Invariant(len(children) > 0)
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(group_close()))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
+        Invariant(Acc(list_pred(result)))
         # The remaining close code points are the decreasing measure, discharging
         # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(group_close()) - j + 1))
@@ -332,6 +308,5 @@
     # the branch condition grouped_output splits on.
     Assert(len(ToSeq(children)) == len(children))
     Assert(len(ToSeq(children)) > 0)
-    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
     return result
     # impl-end
```

Attack 9 — `atk_8_empty_id.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,37 +216,20 @@
         # invariants-end
         result.append(group_open_prefix()[j])
         j = j + 1
-    Assert(ToSeq(result) == group_open_prefix())
-    j = 0
-    while j < len(gid):
+    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
+    j = 0
+    while j < len(attr_end()):
         # invariants-start
         Invariant(Acc(list_pred(gid), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(gid))
-        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
-        # The remaining id code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(gid) - j + 1))
-        # invariants-end
-        result.append(gid[j])
-        j = j + 1
-    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
-    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
-    j = 0
-    while j < len(attr_end()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(attr_end()))
-        Invariant(ToSeq(result) ==
-                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
+        Invariant(Acc(list_pred(result)))
         # The remaining attribute-end code points are the decreasing measure,
         # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(attr_end()) - j + 1))
         # invariants-end
         result.append(attr_end()[j])
         j = j + 1
-    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
     if len(children) == 0:
         # No body content was emitted: the start tag is written in the
         # self-closing form, so it ends with '/>' and there is no separate close.
@@ -256,8 +239,7 @@
             Invariant(Acc(list_pred(gid), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(selfclose_end()))
-            Invariant(ToSeq(result) ==
-                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
+            Invariant(Acc(list_pred(result)))
             # The remaining self-close code points are the decreasing measure,
             # discharging MustTerminate(2) from the precondition.
             Invariant(MustTerminate(len(selfclose_end()) - j + 1))
@@ -266,8 +248,6 @@
             j = j + 1
         Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
         Assert(len(ToSeq(children)) == len(children))
-        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
-        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
         return result
     # Body content was emitted: the start tag ends with '>', the body follows,
     # and a matching close tag '</g>' terminates the group. The self-closing
@@ -283,7 +263,7 @@
         Invariant(len(children) > 0)
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(tag_end()))
-        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
+        Invariant(Acc(list_pred(result)))
         # The remaining tag-end code points are the decreasing measure,
         # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(tag_end()) - j + 1))
@@ -291,7 +271,6 @@
         result.append(tag_end()[j])
         j = j + 1
     Assert(tag_end().take(len(tag_end())) == tag_end())
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
     # draw the body content (children) into the stream, unchanged
     j = 0
     while j < len(children):
@@ -301,8 +280,7 @@
         Invariant(len(children) > 0)
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(children))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
+        Invariant(Acc(list_pred(result)))
         # The remaining body code points are the decreasing measure, discharging
         # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(children) - j + 1))
@@ -310,7 +288,6 @@
         result.append(children[j])
         j = j + 1
     Assert(ToSeq(children).take(len(children)) == ToSeq(children))
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
     # close the group: emit '</g>'
     j = 0
     while j < len(group_close()):
@@ -320,8 +297,7 @@
         Invariant(len(children) > 0)
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(group_close()))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
+        Invariant(Acc(list_pred(result)))
         # The remaining close code points are the decreasing measure, discharging
         # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(group_close()) - j + 1))
@@ -332,6 +308,5 @@
     # the branch condition grouped_output splits on.
     Assert(len(ToSeq(children)) == len(children))
     Assert(len(ToSeq(children)) > 0)
-    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
     return result
     # impl-end
```

Attack 10 — `atk_9_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -201,137 +201,20 @@
         id_attribute(ToSeq(gid)))))
     # post-conditions-end
     # impl-start
+    # Oracle echo: copy the spec function's own sequence element-wise.
+    spec = grouped_output(ToSeq(gid), ToSeq(children))
     result = []  # type: List[int]
-    # emit the id-carrying attribute of the group's start tag:
-    # '<g id="' ++ gid ++ '"'
     j = 0
-    while j < len(group_open_prefix()):
+    while j < len(spec):
         # invariants-start
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(group_open_prefix()))
-        Invariant(ToSeq(result) == group_open_prefix().take(j))
-        # The remaining prefix code points are a strictly decreasing, bounded-
-        # below measure, discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
+        Invariant(0 <= j and j <= len(spec))
+        Invariant(ToSeq(result) == spec.take(j))
+        Invariant(MustTerminate(len(spec) - j + 1))
         # invariants-end
-        result.append(group_open_prefix()[j])
+        result.append(spec[j])
         j = j + 1
-    Assert(ToSeq(result) == group_open_prefix())
-    j = 0
-    while j < len(gid):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(gid))
-        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
-        # The remaining id code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(gid) - j + 1))
-        # invariants-end
-        result.append(gid[j])
-        j = j + 1
-    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
-    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
-    j = 0
-    while j < len(attr_end()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(attr_end()))
-        Invariant(ToSeq(result) ==
-                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
-        # The remaining attribute-end code points are the decreasing measure,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(attr_end()) - j + 1))
-        # invariants-end
-        result.append(attr_end()[j])
-        j = j + 1
-    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
-    if len(children) == 0:
-        # No body content was emitted: the start tag is written in the
-        # self-closing form, so it ends with '/>' and there is no separate close.
-        j = 0
-        while j < len(selfclose_end()):
-            # invariants-start
-            Invariant(Acc(list_pred(gid), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= j and j <= len(selfclose_end()))
-            Invariant(ToSeq(result) ==
-                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
-            # The remaining self-close code points are the decreasing measure,
-            # discharging MustTerminate(2) from the precondition.
-            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
-            # invariants-end
-            result.append(selfclose_end()[j])
-            j = j + 1
-        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
-        Assert(len(ToSeq(children)) == len(children))
-        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
-        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
-        return result
-    # Body content was emitted: the start tag ends with '>', the body follows,
-    # and a matching close tag '</g>' terminates the group. The self-closing
-    # branch above returned, so len(children) > 0 holds from here on -- that is
-    # exactly the branch condition grouped_output splits on, so it must be
-    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
-    Assert(len(children) > 0)
-    j = 0
-    while j < len(tag_end()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(tag_end()))
-        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
-        # The remaining tag-end code points are the decreasing measure,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(tag_end()) - j + 1))
-        # invariants-end
-        result.append(tag_end()[j])
-        j = j + 1
-    Assert(tag_end().take(len(tag_end())) == tag_end())
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
-    # draw the body content (children) into the stream, unchanged
-    j = 0
-    while j < len(children):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(children))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
-        # The remaining body code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(children) - j + 1))
-        # invariants-end
-        result.append(children[j])
-        j = j + 1
-    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
-    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
-    # close the group: emit '</g>'
-    j = 0
-    while j < len(group_close()):
-        # invariants-start
-        Invariant(Acc(list_pred(gid), 1 / 2))
-        Invariant(Acc(list_pred(children), 1 / 2))
-        Invariant(len(children) > 0)
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(group_close()))
-        Invariant(ToSeq(result) ==
-                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
-        # The remaining close code points are the decreasing measure, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(group_close()) - j + 1))
-        # invariants-end
-        result.append(group_close()[j])
-        j = j + 1
-    # the self-closing branch returned, so the body is non-empty here: that is
-    # the branch condition grouped_output splits on.
-    Assert(len(ToSeq(children)) == len(children))
-    Assert(len(ToSeq(children)) > 0)
-    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
+    Assert(spec.take(len(spec)) == spec)
+    Assert(ToSeq(result) == spec)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24637.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container artist renders itself by emitting markup for its body content
  into the renderer's output stream. When the artist carries a (non-empty)
  group identifier, that identifier must reach the rendered output: the body
  content is enclosed in a grouping element whose id is exactly the artist's
  group identifier. Concretely, the rendered output is

      <opening group element carrying the group id> ++
      <the body content> ++
      <matching closing group element>

  so the group identifier appears, framed as the opening of a group, BEFORE the
  body content and is matched by a group close after it. A reader scanning the
  rendered output therefore finds the artist's group id present in it.

  The markup dialect is XML, and its element-writing rules apply. A start tag
  carries the id as a quoted attribute -- '<g id="' ++ the identifier ++ '"' --
  and is then terminated in one of the two ways XML permits: when body content
  follows, the start tag closes with '>' and a matching end tag '</g>' follows
  the body; when NO body content is emitted at all, the element is written in
  the equivalent self-closing form, whose start tag closes with '/>' and which
  takes no separate end tag. Both forms are the same element, and both carry
  the id attribute; the empty-body case is genuinely reachable, because a
  container whose frame is switched off and whose inner content draws nothing
  emits no body markup between the group's open and close.

  The consequence that matters, and it holds in BOTH forms: an artist whose
  group id has been set can be located in the rendered output by that id,
  because the output begins with the id-carrying attribute of the group's start
  tag. If the body content is emitted with no surrounding group, the group id
  never appears in the output and the artist cannot be located.

  Rendering also COMPLETES. Framing a bounded body with a bounded amount of
  group markup is a finite amount of work, so the render always finishes and
  hands the accumulated stream back to whoever asked for it. A render that
  never finishes -- or that never gets as far as handing its output over --
  has produced no output for a reader to scan, so the group id is just as
  absent as it is when no group is emitted at all.

Modelling choices (Nagini fragment):
  * The renderer's accumulating output stream is a ``List[int]`` of code points
    (Nagini bans ``str`` indexing); the specification is carried by ``PSeq[int]``
    via ``ToSeq``.
  * ``gid`` is the artist's group identifier as a ``List[int]`` of code points,
    non-empty (the observed case). ``children`` is the body content the inner
    artists emit, an opaque ``List[int]`` content blob; rendering does not change
    what the children emit, only whether a group encloses them. Both inputs are
    read-only and held at fractional permission (directive 5): the result is a
    fresh stream, the inputs are not observed mutated.
  * The identifier is required to hold no character that the markup dialect
    must escape or quote-switch to represent (``"``, ``&``, ``<``, ``>``); on
    that domain the id attribute carries the identifier's code points verbatim,
    which is what makes the deep model below an equality rather than an
    approximation.
  * The element markup is modeled DEEPLY as constant code-point sequences
    (``group_open_prefix`` ``<g id="``, ``attr_end`` ``"``, ``tag_end`` ``>``,
    ``selfclose_end`` ``/>``, ``group_close`` ``</g>``); there is NO consumed
    axiom. The deep model is validated == the real renderer's element writing
    out-of-band by axiom_check.py (G-AX), an A-reference (mapping.md section 3.1).
  * Completion is carried as ``MustTerminate`` in the precondition. Nagini is a
    partial-correctness verifier by default, so without that obligation an
    implementation that never reaches its return satisfies every ``Ensures``
    VACUOUSLY while emitting nothing; the behaviour above requires the render to
    actually finish and deliver the stream.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed @ContractOnly axioms. The only callee the changed code invokes
#  -- the renderer's element writing -- is modeled deeply in the pure region and
#  validated against the real renderer by axiom_check.py / G-AX as an
#  A-reference, not consumed. See refinement.md.)
# axioms-end

# pure-start
@Pure
def group_open_prefix() -> PSeq[int]:
    # The code points opening the group's start tag, up to the id value: '<g id="'.
    return PSeq(60, 103, 32, 105, 100, 61, 34)

@Pure
def attr_end() -> PSeq[int]:
    # The code point closing the quoted id attribute: '"'.
    return PSeq(34)

@Pure
def tag_end() -> PSeq[int]:
    # The code point terminating a start tag that has body content after it: '>'.
    return PSeq(62)

@Pure
def selfclose_end() -> PSeq[int]:
    # The code points terminating a start tag written in the self-closing form,
    # used when no body content is emitted inside the element: '/>'.
    return PSeq(47, 62)

@Pure
def group_close() -> PSeq[int]:
    # The code points of the end tag matching a non-self-closed start tag: '</g>'.
    return PSeq(60, 47, 103, 62)

@Pure
def id_attribute(gid: PSeq[int]) -> PSeq[int]:
    """The id-carrying attribute of the group's start tag: '<g id="' ++ gid ++ '"'.
    This is the contiguous run a reader scanning the output finds when the group
    id has reached the rendered output. It is common to BOTH tag-termination
    forms, so it is what the group id's presence rests on."""
    return group_open_prefix() + gid + attr_end()

@Pure
def opening_tag(gid: PSeq[int]) -> PSeq[int]:
    """The group's start tag when body content follows it: the id attribute
    terminated by '>'."""
    return id_attribute(gid) + tag_end()

@Pure
def self_closing_tag(gid: PSeq[int]) -> PSeq[int]:
    """The group's start tag written in the self-closing form, used when no body
    content is emitted: the id attribute terminated by '/>'. This element takes
    no separate end tag."""
    return id_attribute(gid) + selfclose_end()

@Pure
def xml_safe(gid: PSeq[int]) -> bool:
    """The identifier holds no character the markup dialect must escape or
    quote-switch to represent ('"', '&', '<', '>'), so the id attribute carries
    its code points verbatim."""
    return Forall(int, lambda k: (
        not (0 <= k and k < len(gid)) or
        (gid[k] != 34 and gid[k] != 38 and gid[k] != 60 and gid[k] != 62)))

@Pure
def grouped_output(gid: PSeq[int], children: PSeq[int]) -> PSeq[int]:
    """The rendered output stream for a group-carrying artist. With body content
    the group is the start tag (carrying the id), the body, and the matching end
    tag; with NO body content the element is written self-closed and takes no end
    tag. Either way the output starts with the id-carrying attribute."""
    if len(children) == 0:
        return self_closing_tag(gid)
    return opening_tag(gid) + children + group_close()
# pure-end

def draw_grouped_output(gid: List[int], children: List[int]) -> List[int]:
    # pre-conditions-start
    # Both inputs are read-only (the result is a fresh stream): fractional
    # permission (directive 5). The observed case carries a non-empty group id.
    Requires(Acc(list_pred(gid), 1 / 2))
    Requires(Acc(list_pred(children), 1 / 2))
    Requires(len(gid) > 0)
    # The identifier is representable verbatim in a quoted attribute: it holds
    # none of the characters the markup dialect escapes or quote-switches on.
    Requires(xml_safe(ToSeq(gid)))
    # (0) The render COMPLETES and hands its stream back: framing a bounded body
    #     with a bounded amount of group markup is finite work. Nagini proves
    #     only PARTIAL correctness, so without this obligation an implementation
    #     that diverges -- or whose return is unreachable -- satisfies the
    #     postconditions below VACUOUSLY while emitting NO output, and a reader
    #     scanning that output finds no group id at all. Requiring termination is
    #     what makes clauses (1) and (2) claims about output actually produced.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(gid), 1 / 2))
    Ensures(Acc(list_pred(children), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The rendered output is exactly the body content enclosed in a group
    #     element carrying the group id, written per the dialect's element rules:
    #     with body content, the start tag (with the id), the body, then the
    #     matching end tag; with no body content, the same id-carrying start tag
    #     written self-closed, with no end tag. This pins the full structure --
    #     an impl that drops the group, reorders, or omits the id cannot verify.
    Ensures(ToSeq(Result()) == grouped_output(ToSeq(gid), ToSeq(children)))
    # (2) The id-carrying attribute of the group's start tag occurs as a
    #     contiguous run of the output, positioned before any body content
    #     (witness at index 0). This is the property a reader scanning the output
    #     relies on to locate the artist by its id, and it holds in BOTH
    #     tag-termination forms. An impl that emits the body content with no
    #     surrounding id-bearing group cannot verify (the id is absent).
    Ensures(Exists(int, lambda i: (
        0 <= i and i + len(id_attribute(ToSeq(gid))) <= len(ToSeq(Result())) and
        ToSeq(Result()).drop(i).take(len(id_attribute(ToSeq(gid)))) ==
        id_attribute(ToSeq(gid)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # emit the id-carrying attribute of the group's start tag:
    # '<g id="' ++ gid ++ '"'
    j = 0
    while j < len(group_open_prefix()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_open_prefix()))
        Invariant(ToSeq(result) == group_open_prefix().take(j))
        # The remaining prefix code points are a strictly decreasing, bounded-
        # below measure, discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
        # invariants-end
        result.append(group_open_prefix()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix())
    j = 0
    while j < len(gid):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(gid))
        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
        # The remaining id code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(gid) - j + 1))
        # invariants-end
        result.append(gid[j])
        j = j + 1
    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
    j = 0
    while j < len(attr_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(attr_end()))
        Invariant(ToSeq(result) ==
                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
        # The remaining attribute-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(attr_end()) - j + 1))
        # invariants-end
        result.append(attr_end()[j])
        j = j + 1
    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
    if len(children) == 0:
        # No body content was emitted: the start tag is written in the
        # self-closing form, so it ends with '/>' and there is no separate close.
        j = 0
        while j < len(selfclose_end()):
            # invariants-start
            Invariant(Acc(list_pred(gid), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(selfclose_end()))
            Invariant(ToSeq(result) ==
                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
            # The remaining self-close code points are the decreasing measure,
            # discharging MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
            # invariants-end
            result.append(selfclose_end()[j])
            j = j + 1
        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
        Assert(len(ToSeq(children)) == len(children))
        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
        return result
    # Body content was emitted: the start tag ends with '>', the body follows,
    # and a matching close tag '</g>' terminates the group. The self-closing
    # branch above returned, so len(children) > 0 holds from here on -- that is
    # exactly the branch condition grouped_output splits on, so it must be
    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
    Assert(len(children) > 0)
    j = 0
    while j < len(tag_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tag_end()))
        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
        # The remaining tag-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(tag_end()) - j + 1))
        # invariants-end
        result.append(tag_end()[j])
        j = j + 1
    Assert(tag_end().take(len(tag_end())) == tag_end())
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
    # draw the body content (children) into the stream, unchanged
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
        # The remaining body code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
    # close the group: emit '</g>'
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
        # The remaining close code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    # the self-closing branch returned, so the body is non-empty here: that is
    # the branch condition grouped_output splits on.
    Assert(len(ToSeq(children)) == len(children))
    Assert(len(ToSeq(children)) > 0)
    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, matplotlib__matplotlib-24637 (nagini). 10 attacks + positive control, ALL byte-identical on the spec view (adversary same-spec exit 0 on every one). Verdict: SOUND -- no verifying wrong impl's faithful patch failed to resolve.

COMMANDS. Per attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-24637 <f>.py` (raw output retained at out_<f>.txt). Per verifying attack: run_resolve via resolve_one.py (harness.run_resolve, run_id sbu-audit-eq-fmg1fvyd-<name>); JSON retained at resolve_<name>.json.

BASELINES. pos_control.py (= model.py, md5 e6ccfc94663846a94e936e3b6b97de38) VERIFIES, exit 0. atk_0_prepatch.py (= model_prepatch.py, children with no surrounding group) exit 2 'verification failed' -- PREPATCH BUG REPRODUCED, so the spec senses the change.

REJECTED (exit 2, all genuine 'verification failed' -- no timeout, no inadmissibility, so each is a real verifier verdict rather than a no-verdict misread as a rejection):
- atk_2_boundary_swapped: the two termination forms SWAPPED (self-closes on non-empty body, frames on empty). Rejected by clause (1)'s equality -> the len(children) branch is load-bearing, not decoration.
- atk_3_diverge: control-flow effect -- builds the correct stream then `while True: pass` before returning, so every Ensures holds VACUOUSLY under partial correctness. Rejected: MustTerminate(2) in the precondition does real work (per my memory note that MustTerminate needs the method level, this is the method-level obligation, and it fires).
- atk_4_id_after_body: children ++ id_attribute ++ '>' ++ '</g>'. The gid IS in the output so clause (2)'s existential is satisfiable; only clause (1) rejects it. Confirms clause (2) alone would be too weak and clause (1) is what pins ORDER.
- atk_6_selfclose_plus_close: self-closing branch additionally emits '</g>' (the form the real XMLWriter.end never produces). Rejected.
- atk_7_no_attr_end: id attribute never quote-closed ('<g id="GID>'). Loop removed and all downstream invariants retargeted so ONLY the postcondition can fail. Rejected.
- atk_8_empty_id: gid code points never emitted (group carries an empty id). Same clean-annotation construction. Rejected -- this is the sharpest control that the gid itself, not just the framing, must reach the output.

VERIFYING CANDIDATES (exit 0) -- all three materialized and RUN through the official harness; ALL THREE RESOLVE, so none is a counterexample:
1. atk_1_partial_empty_gid (PARTIAL DOMAIN): returns the empty stream when len(gid)==0, dead under Requires(len(gid) > 0). Faithful patch = gold framing + an early `return` on a falsy gid, i.e. every gid-less AnnotationBbox draws NOTHING. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P test_annotationbbox_gid PASSED, 29/29 PASS_TO_PASS passed, PASS_TO_FAIL empty.
2. atk_5_partial_amp_gid (PARTIAL DOMAIN on the other precondition): drops the framing entirely (pre-patch behaviour) when gid[0]=='&', dead under Requires(xml_safe(ToSeq(gid))) which bans 38. run_resolve: resolved=True, F2P passed, 29/29 P2P.
3. atk_9_oracle_echo (UNGROUNDED-ORACLE ECHO): copies the spec's own grouped_output element-wise instead of building markup from the constants -- the strongest possible impl if the spec were self-referential. It emits exactly grouped_output, so its faithful refinement IS the gold framing; I re-derived that patch independently (not by copying patch.diff) and resolved it: resolved=True, F2P passed, 29/29 P2P.

WHY THE PARTIAL-DOMAIN ATTACKS DO NOT BREAK IT (the real reason, measured not assumed): the harness for this instance is 1 F2P + 29 P2P, and I verified all 29 P2P live in test_backend_svg.py -- test_offsetbox.py is NOT in the harness at all, and only test_backend_svg.py and test_offsetbox.py reference AnnotationBbox anywhere in the tree. So no harness test draws a gid-less or '&'-prefixed AnnotationBbox, and the dead-branch divergences are unobservable to the oracle. These attacks are honest domain-restriction weaknesses that are simply not test-discriminating; verify=>resolve survives on THIS instance's oracle. Worth recording as the residual risk: the preconditions genuinely narrow the domain below the repo's, so the guarantee is domain-relative -- but mapping.md ENCODES both restrictions as preconditions with cited provenance rather than leaving them in prose, which is the right call, and the oracle cannot distinguish them.

A-LEG AUDIT (my focus; R/I legs mechanically covered by G-CONF). refinement.md legs A1-A6 are tagged R / A-reference / I(children)+R(carrier) / R -- NO A-consumed and NO kind-3. Confirmed the axioms region holds only a prose comment and `grep -cE '^[ \t]*@ContractOnly' model.py` == 0, so 'there are no consumed axioms' is literally true, not a labelling trick; the sole 'ContractOnly' hit is the explanatory comment at line 77.
- A3/A5 correspondence CHECKED against base_commit a9ba9d5d: open_group at backend_svg.py:663 (`if gid: self.writer.start('g', id=gid)`), close_group at :672 (`self.writer.end('g')`), _quote_escape_attrib at :108, __flush's `>` write and end's `elif self.__open: self.__write("/>\n"); return` self-closing branch -- every cited line is where refinement.md/mapping.md says it is.
- G-AX re-run: exit 0, 42 boundary + 20000 fuzz pairs, 789 empty-body cases.
- xml_safe DOMAIN probed at its boundary: it bans exactly 34/38/60/62. I confirmed the renderer is the identity on chars xml_safe ADMITS, including the interesting one -- apostrophe. _quote_escape_attrib only switches to single quotes when '"' is present, and '"' is banned, so admitting "'" is sound (also checked tab, newline, U+00E9, space). The domain is exactly right, not accidentally over-admitting.
- EMPTY-BODY REACHABILITY (what A5's branch rests on) re-verified END-TO-END through the real patched draw + savefig, reproducing mapping.md 3.1's four-row table exactly: empty DrawingArea/frameon=False -> '<g id="GID"/>' (F2P grep FAILS), TextArea('')/frameon=False -> '<g id="GID"/>' (FAILS), empty DrawingArea/frameon=True -> '<g id="GID">' (passes), DrawingArea+Circle/frameon=False -> framed (passes). So the branch is genuinely reachable and the model is right to split on it -- a model that framed unconditionally would be UNFAITHFUL, and clause (2) over id_attribute (the run both forms share) is the correct way to carry 'the gid reached the output' across the whole domain.
- One INACCURACY found, non-blocking and not verdict-relevant: axiom_check.py drives XMLWriter only at nesting depth 0, whereas the real call site is nested inside <svg><g id="figure_1"><g id="axes_1">, where the writer inserts INDENTATION whitespace between tags ('<g id="outer0">\n <g id="GID">\nbody </g>'). The checker's '\n'-stripping normalisation would not absorb those spaces. I probed depths 0-3 and the load-bearing facts SURVIVE: the id_attribute run stays contiguous and the F2P grep '<g id="a test for issue 20044">' matches at every depth, and the nested empty-body case still yields '<g id="GID"/>'. Also stale text in meta.json's deep_model_references: it names a 'group_open_suffix' constant and claims the model spells '">' as one unit, which is the pre-branch design -- model.py actually has attr_end/tag_end/selfclose_end. mapping.md and refinement.md are current; meta.json's prose lags. Neither issue admits a wrong impl.

SCHEDULE: attack verifications run as concurrent background batches of 3 (JVM+Z3 per check), the 3 resolves likewise; pass criteria unchanged -- every attack fully verified, every verifying attack's patch resolved on the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_0_prepatch.py`, `atk_2_boundary_swapped.py`, `atk_3_diverge.py`, `atk_4_id_after_body.py`, `atk_6_selfclose_plus_close.py`, `atk_7_no_attr_end.py`, `atk_8_empty_id.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1_partial_empty_gid.py`, `atk_5_partial_amp_gid.py`, `atk_9_oracle_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_partial_empty_gid.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_2_boundary_swapped.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_diverge.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_id_after_body.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_partial_amp_gid.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_6_selfclose_plus_close.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7_no_attr_end.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8_empty_id.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24637.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container artist renders itself by emitting markup for its body content
  into the renderer's output stream. When the artist carries a (non-empty)
  group identifier, that identifier must reach the rendered output: the body
  content is enclosed in a grouping element whose id is exactly the artist's
  group identifier. Concretely, the rendered output is

      <opening group element carrying the group id> ++
      <the body content> ++
      <matching closing group element>

  so the group identifier appears, framed as the opening of a group, BEFORE the
  body content and is matched by a group close after it. A reader scanning the
  rendered output therefore finds the artist's group id present in it.

  The markup dialect is XML, and its element-writing rules apply. A start tag
  carries the id as a quoted attribute -- '<g id="' ++ the identifier ++ '"' --
  and is then terminated in one of the two ways XML permits: when body content
  follows, the start tag closes with '>' and a matching end tag '</g>' follows
  the body; when NO body content is emitted at all, the element is written in
  the equivalent self-closing form, whose start tag closes with '/>' and which
  takes no separate end tag. Both forms are the same element, and both carry
  the id attribute; the empty-body case is genuinely reachable, because a
  container whose frame is switched off and whose inner content draws nothing
  emits no body markup between the group's open and close.

  The consequence that matters, and it holds in BOTH forms: an artist whose
  group id has been set can be located in the rendered output by that id,
  because the output begins with the id-carrying attribute of the group's start
  tag. If the body content is emitted with no surrounding group, the group id
  never appears in the output and the artist cannot be located.

  Rendering also COMPLETES. Framing a bounded body with a bounded amount of
  group markup is a finite amount of work, so the render always finishes and
  hands the accumulated stream back to whoever asked for it. A render that
  never finishes -- or that never gets as far as handing its output over --
  has produced no output for a reader to scan, so the group id is just as
  absent as it is when no group is emitted at all.

Modelling choices (Nagini fragment):
  * The renderer's accumulating output stream is a ``List[int]`` of code points
    (Nagini bans ``str`` indexing); the specification is carried by ``PSeq[int]``
    via ``ToSeq``.
  * ``gid`` is the artist's group identifier as a ``List[int]`` of code points,
    non-empty (the observed case). ``children`` is the body content the inner
    artists emit, an opaque ``List[int]`` content blob; rendering does not change
    what the children emit, only whether a group encloses them. Both inputs are
    read-only and held at fractional permission (directive 5): the result is a
    fresh stream, the inputs are not observed mutated.
  * The identifier is required to hold no character that the markup dialect
    must escape or quote-switch to represent (``"``, ``&``, ``<``, ``>``); on
    that domain the id attribute carries the identifier's code points verbatim,
    which is what makes the deep model below an equality rather than an
    approximation.
  * The element markup is modeled DEEPLY as constant code-point sequences
    (``group_open_prefix`` ``<g id="``, ``attr_end`` ``"``, ``tag_end`` ``>``,
    ``selfclose_end`` ``/>``, ``group_close`` ``</g>``); there is NO consumed
    axiom. The deep model is validated == the real renderer's element writing
    out-of-band by axiom_check.py (G-AX), an A-reference (mapping.md section 3.1).
  * Completion is carried as ``MustTerminate`` in the precondition. Nagini is a
    partial-correctness verifier by default, so without that obligation an
    implementation that never reaches its return satisfies every ``Ensures``
    VACUOUSLY while emitting nothing; the behaviour above requires the render to
    actually finish and deliver the stream.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed @ContractOnly axioms. The only callee the changed code invokes
#  -- the renderer's element writing -- is modeled deeply in the pure region and
#  validated against the real renderer by axiom_check.py / G-AX as an
#  A-reference, not consumed. See refinement.md.)
# axioms-end

# pure-start
@Pure
def group_open_prefix() -> PSeq[int]:
    # The code points opening the group's start tag, up to the id value: '<g id="'.
    return PSeq(60, 103, 32, 105, 100, 61, 34)

@Pure
def attr_end() -> PSeq[int]:
    # The code point closing the quoted id attribute: '"'.
    return PSeq(34)

@Pure
def tag_end() -> PSeq[int]:
    # The code point terminating a start tag that has body content after it: '>'.
    return PSeq(62)

@Pure
def selfclose_end() -> PSeq[int]:
    # The code points terminating a start tag written in the self-closing form,
    # used when no body content is emitted inside the element: '/>'.
    return PSeq(47, 62)

@Pure
def group_close() -> PSeq[int]:
    # The code points of the end tag matching a non-self-closed start tag: '</g>'.
    return PSeq(60, 47, 103, 62)

@Pure
def id_attribute(gid: PSeq[int]) -> PSeq[int]:
    """The id-carrying attribute of the group's start tag: '<g id="' ++ gid ++ '"'.
    This is the contiguous run a reader scanning the output finds when the group
    id has reached the rendered output. It is common to BOTH tag-termination
    forms, so it is what the group id's presence rests on."""
    return group_open_prefix() + gid + attr_end()

@Pure
def opening_tag(gid: PSeq[int]) -> PSeq[int]:
    """The group's start tag when body content follows it: the id attribute
    terminated by '>'."""
    return id_attribute(gid) + tag_end()

@Pure
def self_closing_tag(gid: PSeq[int]) -> PSeq[int]:
    """The group's start tag written in the self-closing form, used when no body
    content is emitted: the id attribute terminated by '/>'. This element takes
    no separate end tag."""
    return id_attribute(gid) + selfclose_end()

@Pure
def xml_safe(gid: PSeq[int]) -> bool:
    """The identifier holds no character the markup dialect must escape or
    quote-switch to represent ('"', '&', '<', '>'), so the id attribute carries
    its code points verbatim."""
    return Forall(int, lambda k: (
        not (0 <= k and k < len(gid)) or
        (gid[k] != 34 and gid[k] != 38 and gid[k] != 60 and gid[k] != 62)))

@Pure
def grouped_output(gid: PSeq[int], children: PSeq[int]) -> PSeq[int]:
    """The rendered output stream for a group-carrying artist. With body content
    the group is the start tag (carrying the id), the body, and the matching end
    tag; with NO body content the element is written self-closed and takes no end
    tag. Either way the output starts with the id-carrying attribute."""
    if len(children) == 0:
        return self_closing_tag(gid)
    return opening_tag(gid) + children + group_close()
# pure-end

def draw_grouped_output(gid: List[int], children: List[int]) -> List[int]:
    # pre-conditions-start
    # Both inputs are read-only (the result is a fresh stream): fractional
    # permission (directive 5). The observed case carries a non-empty group id.
    Requires(Acc(list_pred(gid), 1 / 2))
    Requires(Acc(list_pred(children), 1 / 2))
    Requires(len(gid) > 0)
    # The identifier is representable verbatim in a quoted attribute: it holds
    # none of the characters the markup dialect escapes or quote-switches on.
    Requires(xml_safe(ToSeq(gid)))
    # (0) The render COMPLETES and hands its stream back: framing a bounded body
    #     with a bounded amount of group markup is finite work. Nagini proves
    #     only PARTIAL correctness, so without this obligation an implementation
    #     that diverges -- or whose return is unreachable -- satisfies the
    #     postconditions below VACUOUSLY while emitting NO output, and a reader
    #     scanning that output finds no group id at all. Requiring termination is
    #     what makes clauses (1) and (2) claims about output actually produced.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(gid), 1 / 2))
    Ensures(Acc(list_pred(children), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The rendered output is exactly the body content enclosed in a group
    #     element carrying the group id, written per the dialect's element rules:
    #     with body content, the start tag (with the id), the body, then the
    #     matching end tag; with no body content, the same id-carrying start tag
    #     written self-closed, with no end tag. This pins the full structure --
    #     an impl that drops the group, reorders, or omits the id cannot verify.
    Ensures(ToSeq(Result()) == grouped_output(ToSeq(gid), ToSeq(children)))
    # (2) The id-carrying attribute of the group's start tag occurs as a
    #     contiguous run of the output, positioned before any body content
    #     (witness at index 0). This is the property a reader scanning the output
    #     relies on to locate the artist by its id, and it holds in BOTH
    #     tag-termination forms. An impl that emits the body content with no
    #     surrounding id-bearing group cannot verify (the id is absent).
    Ensures(Exists(int, lambda i: (
        0 <= i and i + len(id_attribute(ToSeq(gid))) <= len(ToSeq(Result())) and
        ToSeq(Result()).drop(i).take(len(id_attribute(ToSeq(gid)))) ==
        id_attribute(ToSeq(gid)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # emit the id-carrying attribute of the group's start tag:
    # '<g id="' ++ gid ++ '"'
    j = 0
    while j < len(group_open_prefix()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_open_prefix()))
        Invariant(ToSeq(result) == group_open_prefix().take(j))
        # The remaining prefix code points are a strictly decreasing, bounded-
        # below measure, discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
        # invariants-end
        result.append(group_open_prefix()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix())
    j = 0
    while j < len(gid):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(gid))
        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
        # The remaining id code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(gid) - j + 1))
        # invariants-end
        result.append(gid[j])
        j = j + 1
    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
    j = 0
    while j < len(attr_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(attr_end()))
        Invariant(ToSeq(result) ==
                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
        # The remaining attribute-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(attr_end()) - j + 1))
        # invariants-end
        result.append(attr_end()[j])
        j = j + 1
    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
    if len(children) == 0:
        # No body content was emitted: the start tag is written in the
        # self-closing form, so it ends with '/>' and there is no separate close.
        j = 0
        while j < len(selfclose_end()):
            # invariants-start
            Invariant(Acc(list_pred(gid), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(selfclose_end()))
            Invariant(ToSeq(result) ==
                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
            # The remaining self-close code points are the decreasing measure,
            # discharging MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
            # invariants-end
            result.append(selfclose_end()[j])
            j = j + 1
        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
        Assert(len(ToSeq(children)) == len(children))
        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
        return result
    # Body content was emitted: the start tag ends with '>', the body follows,
    # and a matching close tag '</g>' terminates the group. The self-closing
    # branch above returned, so len(children) > 0 holds from here on -- that is
    # exactly the branch condition grouped_output splits on, so it must be
    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
    Assert(len(children) > 0)
    j = 0
    while j < len(tag_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tag_end()))
        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
        # The remaining tag-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(tag_end()) - j + 1))
        # invariants-end
        result.append(tag_end()[j])
        j = j + 1
    Assert(tag_end().take(len(tag_end())) == tag_end())
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
    # draw the body content (children) into the stream, unchanged
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
        # The remaining body code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
    # close the group: emit '</g>'
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
        # The remaining close code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    # the self-closing branch returned, so the body is non-empty here: that is
    # the branch condition grouped_output splits on.
    Assert(len(ToSeq(children)) == len(children))
    Assert(len(ToSeq(children)) > 0)
    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, matplotlib__matplotlib-24637 (nagini). 10 attacks + positive control, ALL byte-identical on the spec view (adversary same-spec exit 0 on every one). Verdict: SOUND -- no verifying wrong impl's faithful patch failed to resolve.

COMMANDS. Per attack: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-24637 <f>.py` (raw output retained at out_<f>.txt). Per verifying attack: run_resolve via resolve_one.py (harness.run_resolve, run_id sbu-audit-eq-fmg1fvyd-<name>); JSON retained at resolve_<name>.json.

BASELINES. pos_control.py (= model.py, md5 e6ccfc94663846a94e936e3b6b97de38) VERIFIES, exit 0. atk_0_prepatch.py (= model_prepatch.py, children with no surrounding group) exit 2 'verification failed' -- PREPATCH BUG REPRODUCED, so the spec senses the change.

REJECTED (exit 2, all genuine 'verification failed' -- no timeout, no inadmissibility, so each is a real verifier verdict rather than a no-verdict misread as a rejection):
- atk_2_boundary_swapped: the two termination forms SWAPPED (self-closes on non-empty body, frames on empty). Rejected by clause (1)'s equality -> the len(children) branch is load-bearing, not decoration.
- atk_3_diverge: control-flow effect -- builds the correct stream then `while True: pass` before returning, so every Ensures holds VACUOUSLY under partial correctness. Rejected: MustTerminate(2) in the precondition does real work (per my memory note that MustTerminate needs the method level, this is the method-level obligation, and it fires).
- atk_4_id_after_body: children ++ id_attribute ++ '>' ++ '</g>'. The gid IS in the output so clause (2)'s existential is satisfiable; only clause (1) rejects it. Confirms clause (2) alone would be too weak and clause (1) is what pins ORDER.
- atk_6_selfclose_plus_close: self-closing branch additionally emits '</g>' (the form the real XMLWriter.end never produces). Rejected.
- atk_7_no_attr_end: id attribute never quote-closed ('<g id="GID>'). Loop removed and all downstream invariants retargeted so ONLY the postcondition can fail. Rejected.
- atk_8_empty_id: gid code points never emitted (group carries an empty id). Same clean-annotation construction. Rejected -- this is the sharpest control that the gid itself, not just the framing, must reach the output.

VERIFYING CANDIDATES (exit 0) -- all three materialized and RUN through the official harness; ALL THREE RESOLVE, so none is a counterexample:
1. atk_1_partial_empty_gid (PARTIAL DOMAIN): returns the empty stream when len(gid)==0, dead under Requires(len(gid) > 0). Faithful patch = gold framing + an early `return` on a falsy gid, i.e. every gid-less AnnotationBbox draws NOTHING. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P test_annotationbbox_gid PASSED, 29/29 PASS_TO_PASS passed, PASS_TO_FAIL empty.
2. atk_5_partial_amp_gid (PARTIAL DOMAIN on the other precondition): drops the framing entirely (pre-patch behaviour) when gid[0]=='&', dead under Requires(xml_safe(ToSeq(gid))) which bans 38. run_resolve: resolved=True, F2P passed, 29/29 P2P.
3. atk_9_oracle_echo (UNGROUNDED-ORACLE ECHO): copies the spec's own grouped_output element-wise instead of building markup from the constants -- the strongest possible impl if the spec were self-referential. It emits exactly grouped_output, so its faithful refinement IS the gold framing; I re-derived that patch independently (not by copying patch.diff) and resolved it: resolved=True, F2P passed, 29/29 P2P.

WHY THE PARTIAL-DOMAIN ATTACKS DO NOT BREAK IT (the real reason, measured not assumed): the harness for this instance is 1 F2P + 29 P2P, and I verified all 29 P2P live in test_backend_svg.py -- test_offsetbox.py is NOT in the harness at all, and only test_backend_svg.py and test_offsetbox.py reference AnnotationBbox anywhere in the tree. So no harness test draws a gid-less or '&'-prefixed AnnotationBbox, and the dead-branch divergences are unobservable to the oracle. These attacks are honest domain-restriction weaknesses that are simply not test-discriminating; verify=>resolve survives on THIS instance's oracle. Worth recording as the residual risk: the preconditions genuinely narrow the domain below the repo's, so the guarantee is domain-relative -- but mapping.md ENCODES both restrictions as preconditions with cited provenance rather than leaving them in prose, which is the right call, and the oracle cannot distinguish them.

A-LEG AUDIT (my focus; R/I legs mechanically covered by G-CONF). refinement.md legs A1-A6 are tagged R / A-reference / I(children)+R(carrier) / R -- NO A-consumed and NO kind-3. Confirmed the axioms region holds only a prose comment and `grep -cE '^[ \t]*@ContractOnly' model.py` == 0, so 'there are no consumed axioms' is literally true, not a labelling trick; the sole 'ContractOnly' hit is the explanatory comment at line 77.
- A3/A5 correspondence CHECKED against base_commit a9ba9d5d: open_group at backend_svg.py:663 (`if gid: self.writer.start('g', id=gid)`), close_group at :672 (`self.writer.end('g')`), _quote_escape_attrib at :108, __flush's `>` write and end's `elif self.__open: self.__write("/>\n"); return` self-closing branch -- every cited line is where refinement.md/mapping.md says it is.
- G-AX re-run: exit 0, 42 boundary + 20000 fuzz pairs, 789 empty-body cases.
- xml_safe DOMAIN probed at its boundary: it bans exactly 34/38/60/62. I confirmed the renderer is the identity on chars xml_safe ADMITS, including the interesting one -- apostrophe. _quote_escape_attrib only switches to single quotes when '"' is present, and '"' is banned, so admitting "'" is sound (also checked tab, newline, U+00E9, space). The domain is exactly right, not accidentally over-admitting.
- EMPTY-BODY REACHABILITY (what A5's branch rests on) re-verified END-TO-END through the real patched draw + savefig, reproducing mapping.md 3.1's four-row table exactly: empty DrawingArea/frameon=False -> '<g id="GID"/>' (F2P grep FAILS), TextArea('')/frameon=False -> '<g id="GID"/>' (FAILS), empty DrawingArea/frameon=True -> '<g id="GID">' (passes), DrawingArea+Circle/frameon=False -> framed (passes). So the branch is genuinely reachable and the model is right to split on it -- a model that framed unconditionally would be UNFAITHFUL, and clause (2) over id_attribute (the run both forms share) is the correct way to carry 'the gid reached the output' across the whole domain.
- One INACCURACY found, non-blocking and not verdict-relevant: axiom_check.py drives XMLWriter only at nesting depth 0, whereas the real call site is nested inside <svg><g id="figure_1"><g id="axes_1">, where the writer inserts INDENTATION whitespace between tags ('<g id="outer0">\n <g id="GID">\nbody </g>'). The checker's '\n'-stripping normalisation would not absorb those spaces. I probed depths 0-3 and the load-bearing facts SURVIVE: the id_attribute run stays contiguous and the F2P grep '<g id="a test for issue 20044">' matches at every depth, and the nested empty-body case still yields '<g id="GID"/>'. Also stale text in meta.json's deep_model_references: it names a 'group_open_suffix' constant and claims the model spells '">' as one unit, which is the pre-branch design -- model.py actually has attr_end/tag_end/selfclose_end. mapping.md and refinement.md are current; meta.json's prose lags. Neither issue admits a wrong impl.

SCHEDULE: attack verifications run as concurrent background batches of 3 (JVM+Z3 per check), the 3 resolves likewise; pass criteria unchanged -- every attack fully verified, every verifying attack's patch resolved on the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Bundle model.py verifies at baseline (scripts/nagini_verify.sh, exit 0). Re-ran the bundle's own out-of-band checks: G-AX passes (42 boundary + 20000 fuzz gid/body pairs, 789 empty-body), G-CONF passes (100000 inputs, 0 disagreements, seed 24637). Work done against the base_commit worktree (a9ba9d5d3f, verified) plus the real patched draw.

MODELED FUNCTION UNDER TEST. draw_grouped_output(gid, children) with Requires(len(gid)>0), Requires(xml_safe(gid)), MustTerminate; real callee = patched AnnotationBbox.draw (offsetbox.py:1449) -> RendererSVG.open_group/close_group -> XMLWriter.start('g',id=gid)/.end('g').

### What I attacked and failed to break
(1) The two-form branch (len(children)==0 -> '<g id="GID"/>' self-closed, else '<g id="GID">'++body++'</g>'). This is the part most likely to drift, since the terminator is chosen by the WRITER, not the artist. Built 15 hand-targeted structural configs incl. the near-misses: empty DrawingArea, invisible Circle, empty Line2D, invisible Rectangle, PaddedBox with/without frame, VPacker/HPacker of empty children, TextArea(' '), TextArea('\n'), invisible text, alpha=0 text, rasterized, agg_filter, url-bearing patch. Predicted form == real form in ALL 15 (0 disagreements). Note the genuinely discriminating pairs: da_empty_line emits 22 bytes -> framed (real and model agree), text_alpha0 emits 812 bytes -> framed, text_invis emits 0 -> self-closed. The branch tracks the real writer exactly.

(2) The ONLY mechanism by which that branch could be wrong: XMLWriter.end branches on `self.__data` TRUTHINESS, not on bytes emitted, so __data == [""] would be truthy while emitting zero bytes -> real '<g id="G"></g>' where the model predicts '<g id="G"/>'. I CONFIRMED this divergence exists at the raw XMLWriter level (w.start('g',id='G'); w.data(''); w.end('g') -> '<g id="G">\n</g>\n'). It is NOT a spec defect because it is UNREACHABLE: the sole .data() call site in backend_svg.py (line 243) is guarded by `if text:`, so __data can never hold an empty string. No real artist path can drive it. This was my best shot and it dies on reachability.

(3) 30,000 randomized in-domain configs through the real patched draw using the bundle's own declared bridge (9 content kinds, 4 arrowstyles, frameon/arrow/alpha/url/hatch/clip/rasterized varied, gid length 1-40 over a wide alphabet incl. ' / \\ ? $ | ^ ` [ ] { } %): 0 clause-(1) mismatches, 0 clause-(2) failures.

(4) Exhaustive single-codepoint gid sweep, all xml_safe cp in 1..0x2FFF: 0 mismatches. Astral/non-BMP gids (emoji, U+10FFFF, surrogate-pair-forming) agree -- the List[int] code-point carrier is faithful, no UTF-16 artifact.

(5) xml_safe precondition boundary is drawn EXACTLY right, checked both directions. Apostrophe-bearing gids are INSIDE the admitted domain and agree ('<g id="a\'b"/>'); only " & < > are escaped/quote-switched by _quote_escape_attrib/_escape_cdata and those are precisely what xml_safe excludes. The precondition is not too wide (no admitted gid escapes) and not gratuitously narrow (it correctly admits ', which the renderer does NOT escape when no " is present).

(6) Whitespace-laden gids ('\n', '\t', '\r\n', '
', '\xa0', leading/trailing spaces) agree on RAW bytes with NO normalization, so the checkers' documented layout-whitespace strip is not masking a gid-byte discrepancy.

TWO DISCLOSED-SCOPE OBSERVATIONS -- reported honestly as NON-defects, not dressed up as divergences.

(A) Omitted guards. With set_visible(False), or xy out of bounds with annotation_clip=True, the real draw returns early and emits NOTHING (gid absent), while the model on the same modeled input (gid non-empty/xml_safe, children==[]) predicts '<g id="GID"/>'. Neither guard is a precondition. This is NOT spec drift: (i) mapping.md section 2 discloses it explicitly ('omitted (out of tested scope)'); (ii) `children` is DEFINED as the output the child artists produce, and on the guard path the children never draw, so the guard is a mode selector upstream of the modeled operation rather than an input to it; (iii) decisively, I measured pre-patch vs post-patch on the guard path and BOTH emit nothing identically -- so the omission cannot mask the bug, cannot admit a non-resolving impl, and does not weaken G-DIFF. Only the F2P-style path (visible, in-bounds) discriminates, and there the gid appears post-patch only.

(B) Strongest near-miss: pending parent start tag. In a real full-figure savefig where the AnnotationBbox is the first emitter inside its parent group, the parent's start tag is still unterminated (__open=1), so the byte range draw appends begins with the parent's DEFERRED '>': measured segment '>\n   <g id="a test for issue 20044"/>\n', which does not begin with '<g id="'. Feeding that renderer state into the bundle's OWN conformance bridge makes check_one report DISAGREEMENT on 4/4 cases.

I nonetheless judge this NOT a spec defect, on two independent grounds: (i) that '>' terminates the PARENT element, not this artist's output -- mapping.md section 2/A6 binds Result() to 'the rendered SVG content for this artist', so attributing the parent's byte to the callee is an artifact of my adversarial re-segmentation, not a claim the spec makes; (ii) more importantly, the ENCODED clause (2) is `Exists(int, lambda i: 0 <= i and ...)` -- an existential over ANY offset, not pinned to 0 -- and id_attribute(gid) still occurs contiguously under my segmentation (verified True throughout).

Only the surrounding PROSE ('witness at index 0', 'the output begins with the id-carrying attribute') is looser than the mechanized clause; that prose overstates in the direction of being STRONGER than the encoding, so it cannot admit a bad impl either. Documentation nit at most.

CONCLUSION. No diverging input found, so I claim no defect and cite none. Across 130k+ machine-checked in-domain inputs plus targeted structural and exhaustive-codepoint attacks, the modeled function agrees with the real callee on the load-bearing content: the gid reaches the output as the id of a group element enclosing the children, in the correct one of the two REAL termination forms. The bundle notably does NOT commit the obvious unfaithfulness here (asserting the framed form unconditionally) -- it branches on len(children) and the empty-body class is genuinely reachable and genuinely self-closing, which I independently confirmed. Both admitted-domain restrictions (len(gid)>0 for the `if gid:` branch, xml_safe for verbatim attribute carriage) are ENCODED as preconditions rather than left in prose, and both match the real escape/branch boundaries exactly. Verdict FAITHFUL.

CAVEAT ON SCOPE. My probing used the environment matplotlib (3.10.9) for driving live renders alongside the base_commit worktree source for reading; I confirmed the XMLWriter start/end/__flush/_escape_cdata/_quote_escape_attrib logic and open_group/close_group are byte-equivalent between the two on every path the model touches, so the live-render evidence transfers. G-AX/G-CONF (which the gate runs against the pinned /testbed) both pass independently.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE/PROVENANCE. Judged the real released artifact: recomputed spec_view via swebench_unified.markers.spec_view (nagini tables) = sha256 27c9097cdaf941d9aa60ef0bb58dc61a31b8e55e3cc97bf65044ebdccd83a46e, byte-identical to meta.json G-HYGIENE region_hashes.spec_view. same-spec on the bundle model returned SAME (exit 0). Impl+invariants correctly elided (only `... # implementation elided`); mapping.md / refinement.md / patch.diff are NOT consumer-exposed (prompts.py builds the consumer view from spec_view + meta.modeled_functions only), so gold content in those files is out of scope. Recorded G-PANEL-3 was fail/INCONCLUSIVE because the role never ran (the auditor error), so this is a fresh judgment, not a re-label of a retained verdict.

MECHANICAL. leakage.screen(model, nagini, patch, problem_statement, test_patch) => PASSED, 0 hard failures, 0 warnings. Confirmed component-by-component: (L1) no diff marker; neither gold changed line reproduced under whitespace normalization; (L2) 'lib/matplotlib/offsetbox.py' and dotted 'matplotlib.offsetbox' absent; (L3) zero _NARRATION_RE hits across all comments/docstrings, and 'pre-patch'/'prepatch'/'before the fix'/'used to'/'no longer'/'regression' all absent.

HIDDEN-TEST CONTENT: clean. Probed the spec view for every distinctive token of test_patch and the gold: '20044', 'a test for issue', 'test_annotationbbox_gid', 'test_backend_svg', 'AnnotationBbox', 'OffsetImage', 'offsetbox', 'open_group', 'close_group', 'get_gid', 'set_gid', 'savefig', 'RendererSVG', 'XMLWriter', 'svg'/'SVG' — ALL absent. The gold edit's two call names (open_group/close_group) and the patched class never appear; the spec view says only 'a container artist' and 'the markup dialect is XML'.

FRAGILITY I DID FIND (reported, not charged as a leak). The only patched symbol is `draw` (_patch_changed_symbols = {'draw'}; _patch_new_symbols = empty). The screen exempts it because 'draw' occurs as a SUBSTRING of problem_statement — but only inside the image filename 'undraw_flowers_vx06.png'; there is NO word-boundary occurrence of 'draw' in problem_statement. So spec-view identifier `draw_grouped_output` (line 162) embeds patched repo symbol `draw` and survives the L2/L5 check only by coincidence, and `draw` is not in the _COMMON_NONDISTINCTIVE allowlist. I judge this NOT a semantic leak on two independent grounds:

(1) the repo symbol is deliberately handed to the same solver anyway — modes 1/2 render meta.modeled_functions as 'draw_grouped_output (<-> matplotlib.offsetbox.AnnotationBbox.draw)', so the identifier discloses strictly less than the accompanying localization block;

(2) `draw` is the universal Artist render-method name and localizes nothing beyond 'an artist renders', which problem_statement already establishes. Worth hardening the screen (word-boundary match, or add 'draw' to the allowlist) so this instance's pass is principled rather than accidental, but it changes no verdict here.

WHY THE '<g id="' MARKUP IS NOT A LEAK. The strongest leak candidate is the docstring/pure-region disclosure of the literal group markup ('<g id="', '"', '>', '/>', '</g>') and 'the body content is enclosed in a grouping element whose id is exactly the artist's group identifier'. This is the REQUIRED OBSERVABLE OUTCOME, not the edit: the F2P assertion is `'<g id="...">' in buf`, so any spec faithful enough to discriminate the change MUST state that the output carries a gid-bearing group element.

It is also fully public without the spec view — verified in the base_commit worktree (a9ba9d5): RendererSVG.open_group at backend_svg.py:666 publicly writes `start('g', id=gid)`, and there are 14 pre-existing `renderer.open_group(self.__class__.__name__, gid=self.get_gid())` / `close_group(...)` wrapping pairs in legend.py:649/671, text.py:749/805, patches.py:544/579, lines.py:755/880, collections.py, figure.py, table.py, axis.py. problem_statement itself points at PR 15087 'where a solution was applied for all known instances of missing gid's' and asks whether the AnnotationBbox artist 'has been missed by this fix' — i.e. it publicly directs the solver to copy the sibling artists' pattern. The spec view therefore adds no mechanism the public problem statement + public repo does not already give.

HINTS DISCIPLINE (checked explicitly, since this is where the gate is strictest). hints_text contains 'AnnotationBbox.draw should just call open_group() at the beginning and close_group() at the end, i.e. wrap the entire AnnotationBbox in a svg element with that gid' — the solution verbatim. The spec view echoes NONE of that vocabulary: not 'open_group', not 'close_group', not 'AnnotationBbox', not 'svg'. The overlap is only at the level of the observable contract (a group element carrying the id), which is independently public per the paragraph above. So the spec view is clean even under the hints-blind standard.

TWO OTHER CLAUSES CLEARED. (a) 'If the body content is emitted with no surrounding group, the group id never appears in the output and the artist cannot be located' — reads as spec rationale (consequence of violating the postcondition), not bug narration; it states no current/prior code behavior and adds nothing past problem_statement's 'the gid label for the images are not included'. (b) The empty-body / self-closing '/>' branch and 'a container whose frame is switched off and whose inner content draws nothing' — this class appears NOWHERE in test_patch (the F2P uses a framed OffsetImage with arrowprops) and nowhere in the gold two-line diff; it is a bundle-authored faithfulness case tracking the public XMLWriter deferred-terminator logic (backend_svg.py:225-231). It constrains the solver more, and leaks neither test identity nor gold content.

CONCLUSION: NO-LEAKAGE. No reproduced diff line, no diff marker, no patched path, no hidden-test token, no fix narration, and no mechanism disclosure beyond the public problem_statement + base_commit repo. Single actionable hygiene item: the `draw` exemption fires on an accidental substring, so consider a word-boundary fix to the L2/L5 screen.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
