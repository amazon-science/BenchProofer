# P2 adversarial audit — django__django-14053

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_0_prepatch.py`, `atk_1_drop_err.py`, `atk_3_partial_domain.py`, `atk_4_boundary.py`, `atk_5_control_flow.py`, `atk_6_vacuity_echo.py`, `atk_7_swap_segments.py`, `atk_8_dup_settled.py`, `atk_9_reverse_settled.py`, `atk_10_late_failure.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2_two_traversals.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,11 +171,9 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # First pass: report EVERY file (plain and adjustable alike) as the pass
+    # reaches it, holding nothing back.
     first = []  # type: List[int]
-    collected = []  # type: List[int]
     i = len(ids)
     while i > 0:
         # invariants-start
@@ -185,34 +183,43 @@
         Invariant(len(ids) == len(adj))
         Invariant(len(ids) == len(err))
         Invariant(Acc(list_pred(first)))
-        Invariant(Acc(list_pred(collected)))
         Invariant(0 <= i and i <= len(ids))
-        Invariant(ToSeq(first) == first_pass_ids(
-            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
-        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
+        Invariant(ToSeq(first) == ToSeq(ids).drop(i))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         fid = ids[i - 1]
-        fa = adj[i - 1]
-        fe = err[i - 1]
         Assert(ToSeq(ids).drop(i - 1)[0] == fid)
-        Assert(ToSeq(adj).drop(i - 1)[0] == fa)
-        Assert(ToSeq(err).drop(i - 1)[0] == fe)
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
-        Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
-        Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
-        if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
-            first = [fid] + first
-        if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
-            collected = [fid] + collected
+        first = [fid] + first
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
+    # Repeat pass over the adjustable files, reporting each one again.
+    collected = []  # type: List[int]
+    j = len(ids)
+    while j > 0:
+        # invariants-start
+        Invariant(Acc(list_pred(ids), 1 / 2))
+        Invariant(Acc(list_pred(adj), 1 / 2))
+        Invariant(Acc(list_pred(err), 1 / 2))
+        Invariant(len(ids) == len(adj))
+        Invariant(len(ids) == len(err))
+        Invariant(Acc(list_pred(first)))
+        Invariant(Acc(list_pred(collected)))
+        Invariant(0 <= j and j <= len(ids))
+        Invariant(ToSeq(first) == ToSeq(ids))
+        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(j), ToSeq(adj).drop(j)))
+        Invariant(MustTerminate(j + 1))
+        # invariants-end
+        rid = ids[j - 1]
+        ra = adj[j - 1]
+        Assert(ToSeq(ids).drop(j - 1)[0] == rid)
+        Assert(ToSeq(adj).drop(j - 1)[0] == ra)
+        Assert(ToSeq(ids).drop(j - 1).drop(1) == ToSeq(ids).drop(j))
+        Assert(ToSeq(adj).drop(j - 1).drop(1) == ToSeq(adj).drop(j))
+        if ra != 0:
+            collected = [rid] + collected
+        j = j - 1
+    # Report the first pass followed by the repeat pass: adjustable files are
+    # reported twice.
     result = first + collected
-    Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
     # impl-end
```

Attack 2 — `atk_1_drop_err.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,9 +171,11 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 1 -- DROPS THE `fe != 0` DISJUNCT of the changed first-pass guard.
+    # This is exactly the wrongness the prior audit's counterexample rode on:
+    # a failing file is HELD BACK (only collected) instead of being handed to
+    # the caller at its enumeration position. The repair added the `err` stream
+    # precisely to sense this, so it must now be rejected.
     first = []  # type: List[int]
     collected = []  # type: List[int]
     i = len(ids)
@@ -187,8 +189,7 @@
         Invariant(Acc(list_pred(first)))
         Invariant(Acc(list_pred(collected)))
         Invariant(0 <= i and i <= len(ids))
-        Invariant(ToSeq(first) == first_pass_ids(
-            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
+        Invariant(len(first) + len(collected) == len(ids) - i)
         Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -201,17 +202,11 @@
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
-        if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
+        if fa == 0:
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
     result = first + collected
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
```

Attack 3 — `atk_2_two_traversals.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -171,13 +171,42 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 2 -- TWO INDEPENDENT TRAVERSALS (re-encoding the counterexample the
+    # PRIOR pass named, now against the REPAIRED 3-stream spec). The first-pass
+    # segment is gathered in one walk and the settled segment in a SECOND,
+    # independent walk. Extensionally identical to the shipped impl; the prior
+    # break rode on this shape's claimed licence to drop the `fe != 0` disjunct
+    # when materialising its patch.
     first = []  # type: List[int]
+    p = len(ids)
+    while p > 0:
+        # invariants-start
+        Invariant(Acc(list_pred(ids), 1 / 2))
+        Invariant(Acc(list_pred(adj), 1 / 2))
+        Invariant(Acc(list_pred(err), 1 / 2))
+        Invariant(len(ids) == len(adj))
+        Invariant(len(ids) == len(err))
+        Invariant(Acc(list_pred(first)))
+        Invariant(0 <= p and p <= len(ids))
+        Invariant(ToSeq(first) == first_pass_ids(
+            ToSeq(ids).drop(p), ToSeq(adj).drop(p), ToSeq(err).drop(p)))
+        Invariant(MustTerminate(p + 1))
+        # invariants-end
+        pid = ids[p - 1]
+        pa = adj[p - 1]
+        pe = err[p - 1]
+        Assert(ToSeq(ids).drop(p - 1)[0] == pid)
+        Assert(ToSeq(adj).drop(p - 1)[0] == pa)
+        Assert(ToSeq(err).drop(p - 1)[0] == pe)
+        Assert(ToSeq(ids).drop(p - 1).drop(1) == ToSeq(ids).drop(p))
+        Assert(ToSeq(adj).drop(p - 1).drop(1) == ToSeq(adj).drop(p))
+        Assert(ToSeq(err).drop(p - 1).drop(1) == ToSeq(err).drop(p))
+        if pa == 0 or pe != 0:
+            first = [pid] + first
+        p = p - 1
     collected = []  # type: List[int]
-    i = len(ids)
-    while i > 0:
+    q = len(ids)
+    while q > 0:
         # invariants-start
         Invariant(Acc(list_pred(ids), 1 / 2))
         Invariant(Acc(list_pred(adj), 1 / 2))
@@ -186,33 +215,21 @@
         Invariant(len(ids) == len(err))
         Invariant(Acc(list_pred(first)))
         Invariant(Acc(list_pred(collected)))
-        Invariant(0 <= i and i <= len(ids))
-        Invariant(ToSeq(first) == first_pass_ids(
-            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
-        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
-        Invariant(MustTerminate(i + 1))
+        Invariant(0 <= q and q <= len(ids))
+        Invariant(ToSeq(first) == first_pass_ids(ToSeq(ids), ToSeq(adj), ToSeq(err)))
+        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(q), ToSeq(adj).drop(q)))
+        Invariant(MustTerminate(q + 1))
         # invariants-end
-        fid = ids[i - 1]
-        fa = adj[i - 1]
-        fe = err[i - 1]
-        Assert(ToSeq(ids).drop(i - 1)[0] == fid)
-        Assert(ToSeq(adj).drop(i - 1)[0] == fa)
-        Assert(ToSeq(err).drop(i - 1)[0] == fe)
-        Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
-        Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
-        Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
-        if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
-            first = [fid] + first
-        if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
-            collected = [fid] + collected
-        i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
+        qid = ids[q - 1]
+        qa = adj[q - 1]
+        Assert(ToSeq(ids).drop(q - 1)[0] == qid)
+        Assert(ToSeq(adj).drop(q - 1)[0] == qa)
+        Assert(ToSeq(ids).drop(q - 1).drop(1) == ToSeq(ids).drop(q))
+        Assert(ToSeq(adj).drop(q - 1).drop(1) == ToSeq(adj).drop(q))
+        if qa != 0:
+            collected = [qid] + collected
+        q = q - 1
+    Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     result = first + collected
-    Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
     # impl-end
```

Attack 4 — `atk_3_partial_domain.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,11 +171,16 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 3 -- PARTIAL DOMAIN. Correct exactly when NO file's examination
+    # fails; when some file fails, that file's first-pass report is DEFERRED to
+    # the very end of the run (appended after the settled segment) instead of
+    # being handed over at its enumeration position. The multiplicity property
+    # and the report COUNT are both preserved, so only the ORDERED clause (1)
+    # can sense it -- this is the "holding a file back must not swallow it"
+    # obligation refinement.md calls independent.
     first = []  # type: List[int]
     collected = []  # type: List[int]
+    late = []  # type: List[int]
     i = len(ids)
     while i > 0:
         # invariants-start
@@ -186,9 +191,10 @@
         Invariant(len(ids) == len(err))
         Invariant(Acc(list_pred(first)))
         Invariant(Acc(list_pred(collected)))
+        Invariant(Acc(list_pred(late)))
         Invariant(0 <= i and i <= len(ids))
-        Invariant(ToSeq(first) == first_pass_ids(
-            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
+        Invariant(len(first) + len(late) == len(first_pass_ids(
+            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i))))
         Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -201,18 +207,14 @@
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
-        if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
+        if fa != 0 and fe != 0:
+            late = [fid] + late
+        elif fa == 0 or fe != 0:
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
-    result = first + collected
+    result = first + collected + late
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
     # impl-end
```

Attack 5 — `atk_4_boundary.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,13 +171,12 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 4 -- BOUNDARY / off-by-one: `while i > 1`, so the HEAD of the
+    # depth-sorted enumeration is never examined and never reported at all.
     first = []  # type: List[int]
     collected = []  # type: List[int]
     i = len(ids)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(ids), 1 / 2))
         Invariant(Acc(list_pred(adj), 1 / 2))
@@ -186,7 +185,7 @@
         Invariant(len(ids) == len(err))
         Invariant(Acc(list_pred(first)))
         Invariant(Acc(list_pred(collected)))
-        Invariant(0 <= i and i <= len(ids))
+        Invariant(0 <= i and i <= len(ids) or len(ids) == 0)
         Invariant(ToSeq(first) == first_pass_ids(
             ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
         Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
@@ -202,16 +201,10 @@
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
         if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
     result = first + collected
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
```

Attack 6 — `atk_5_control_flow.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,9 +171,11 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 5 -- CONTROL-FLOW EFFECT: on meeting the first FAILING file the
+    # remaining enumeration is collapsed (a `break` out of the first pass via the
+    # loop counter), modelling a routine that stops examining once something
+    # fails instead of completing the pass. Every file up to that point is
+    # reported correctly; the tail is silently dropped.
     first = []  # type: List[int]
     collected = []  # type: List[int]
     i = len(ids)
@@ -202,16 +204,13 @@
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
         if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
-        i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
+        if fe != 0:
+            i = 0
+        else:
+            i = i - 1
     result = first + collected
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
```

Attack 7 — `atk_6_vacuity_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,9 +171,12 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 6 -- UNGROUNDED-ORACLE / VACUITY ECHO. The first-pass guard is
+    # replaced by the INFEASIBLE conjunction `fa == 0 and fa != 0`, so the
+    # first-pass branch is dead code and the segment comes out empty. If the
+    # spec were vacuous (or clause (1) not load-bearing) this would sail
+    # through; it is the control that the postcondition really constrains the
+    # first-pass segment rather than being trivially satisfiable.
     first = []  # type: List[int]
     collected = []  # type: List[int]
     i = len(ids)
@@ -187,8 +190,6 @@
         Invariant(Acc(list_pred(first)))
         Invariant(Acc(list_pred(collected)))
         Invariant(0 <= i and i <= len(ids))
-        Invariant(ToSeq(first) == first_pass_ids(
-            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
         Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -201,17 +202,11 @@
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
-        if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
+        if fa == 0 and fa != 0:
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
     result = first + collected
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
```

Attack 8 — `atk_7_swap_segments.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,9 +171,12 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 7 -- ORDERING between segments: `collected + first`. Every file is
+    # reported, the COUNT is exactly right (clause (2) holds), but the settled
+    # segment is emitted BEFORE the first-pass segment -- so a failing file's
+    # failure report arrives AFTER its own settled report. Probes whether the
+    # ORDERED equation in clause (1) is load-bearing or whether the length
+    # clause is doing all the work.
     first = []  # type: List[int]
     collected = []  # type: List[int]
     i = len(ids)
@@ -202,17 +205,11 @@
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
         if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
-    result = first + collected
+    result = collected + first
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
     # impl-end
```

Attack 9 — `atk_8_dup_settled.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,11 +171,17 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 8 -- LENGTH-PRESERVING DUPLICATE of a SETTLED report. Exactly
+    # len(ids) + failing_adj_count(...) reports come out, but a failing
+    # adjustable file's EXTRA report is a second copy of its SETTLED outcome
+    # (appended to the settled segment) rather than the first-pass failure
+    # report. This is precisely "the failure is displaced by the same file's
+    # later settled outcome" -- the caller never sees a failure, yet the count
+    # clause (2) is satisfied exactly. It attacks whether clause (2) alone could
+    # be mistaken for the failure hand-off obligation.
     first = []  # type: List[int]
     collected = []  # type: List[int]
+    extra = []  # type: List[int]
     i = len(ids)
     while i > 0:
         # invariants-start
@@ -186,8 +192,9 @@
         Invariant(len(ids) == len(err))
         Invariant(Acc(list_pred(first)))
         Invariant(Acc(list_pred(collected)))
+        Invariant(Acc(list_pred(extra)))
         Invariant(0 <= i and i <= len(ids))
-        Invariant(ToSeq(first) == first_pass_ids(
+        Invariant(len(extra) == failing_adj_count(
             ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
         Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
         Invariant(MustTerminate(i + 1))
@@ -201,18 +208,14 @@
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
-        if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
+        if fa == 0:
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
+        if fa != 0 and fe != 0:
+            extra = [fid] + extra
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
-    result = first + collected
+    result = first + collected + extra
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
     # impl-end
```

Attack 10 — `atk_9_reverse_settled.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,9 +171,12 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 9 -- INTRA-SEGMENT ORDER. Both segments contain exactly the right
+    # ids with exactly the right multiplicities (clause (2) holds exactly), and
+    # the first-pass segment is in enumeration order, but the SETTLED segment is
+    # emitted in REVERSE enumeration order. Probes whether clause (1) pins the
+    # order WITHIN the settled segment -- the A5 claim that
+    # `processed_adjustable_paths` preserves insertion order.
     first = []  # type: List[int]
     collected = []  # type: List[int]
     i = len(ids)
@@ -189,7 +192,7 @@
         Invariant(0 <= i and i <= len(ids))
         Invariant(ToSeq(first) == first_pass_ids(
             ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
-        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
+        Invariant(len(collected) == len(adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i))))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         fid = ids[i - 1]
@@ -202,16 +205,10 @@
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
         if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
-            collected = [fid] + collected
+            collected = collected + [fid]
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
     result = first + collected
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
```

Attack 11 — `atk_10_late_failure.py` → rejected (same spec, does not verify — good)

```diff
@@ -171,10 +171,16 @@
             + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     # post-conditions-end
     # impl-start
-    # First pass: report the plain files, and any file whose examination fails,
-    # as the pass reaches them; collect the adjustable files for the settled
-    # segment.
+    # ATTACK 10 -- FAILURE HAND-OFF POSITION *within* the first-pass segment.
+    # Every file is reported, both segments carry exactly the right ids, and the
+    # report COUNT is exactly right; a failing file IS handed to the caller in
+    # the first-pass segment (so it is not swallowed) -- but at the END of that
+    # segment instead of AT its enumeration position. Since collect() aborts at
+    # the FIRST failure it sees, this reorders which settled reports the caller
+    # has already recorded before it aborts. Probes whether clause (1) pins the
+    # failure's POSITION or merely its presence.
     first = []  # type: List[int]
+    fails = []  # type: List[int]
     collected = []  # type: List[int]
     i = len(ids)
     while i > 0:
@@ -185,10 +191,11 @@
         Invariant(len(ids) == len(adj))
         Invariant(len(ids) == len(err))
         Invariant(Acc(list_pred(first)))
+        Invariant(Acc(list_pred(fails)))
         Invariant(Acc(list_pred(collected)))
         Invariant(0 <= i and i <= len(ids))
-        Invariant(ToSeq(first) == first_pass_ids(
-            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
+        Invariant(len(first) + len(fails) == len(first_pass_ids(
+            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i))))
         Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
@@ -201,18 +208,14 @@
         Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
         Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
         Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
-        if fa == 0 or fe != 0:
-            # Plain files, and any failing examination, go straight to the
-            # caller at this position in the enumeration.
+        if fe != 0:
+            fails = [fid] + fails
+        elif fa == 0:
             first = [fid] + first
         if fa != 0:
-            # Adjustable files are revisited across the internal passes but are
-            # collected, keyed by file, so each is held only once; they are
-            # reported at the end with their final outcome.
             collected = [fid] + collected
         i = i - 1
-    # Report the first pass followed by the settled adjustable files, once each.
-    result = first + collected
+    result = first + fails + collected
     Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14053.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multi-pass routine consumes a collection of distinct files and reports, to
  its caller, the outcome for each file. Every file in the collection must be
  reported, and — this is the property under specification — each file must be
  reported EXACTLY ONCE for its settled outcome, regardless of how many internal
  passes the routine performs over it.

  The collection has two kinds of file. A plain file is settled in a single
  pass and reported once. An adjustable file (one whose contents may reference
  other files and therefore may be revisited across several passes) is, by its
  nature, examined repeatedly until the references stabilise; nevertheless the
  routine must report it to the caller only once, carrying its final outcome —
  not once per pass.

  A file's examination may also FAIL outright instead of yielding a settled
  outcome. That failure outcome is not the routine's to interpret: the caller is
  the component that decides what a failure means and acts on it (it stops the
  run and re-surfaces the failure), so the routine must hand every failure to
  the caller AT THE POINT THE FIRST PASS REACHES IT, at the position the
  enumeration gives that file. This obligation is INDEPENDENT of the multiplicity
  property above, and holding a file back in order to satisfy that property must
  not swallow it: a failure outcome may never be deferred to the end of the run,
  and may never be displaced by the same file's later settled outcome. Deferring
  or displacing it is observable to the caller as a run that reports a settled
  outcome for a file whose examination did not settle, and never reports the
  failure at all.

  Concretely, the reported sequence is two segments. The FIRST-PASS segment:
  every plain file, plus every adjustable file whose examination fails, each
  appearing once, in the order in which the routine enumerates the collection.
  Then the SETTLED segment: every adjustable file, each appearing once, in that
  same enumeration order. The number of reports is therefore the number of files
  in the collection plus one for each adjustable file whose examination fails
  (which is reported for its failure and again for its settled outcome); no file
  is reported twice for a settled outcome.

The collection is modelled as three equal-length parallel `List[int]` streams,
presented in the order the routine enumerates the files: a distinct integer id
per file (the input is keyed, so ids do not repeat), a 0 / non-0 flag marking
which files are adjustable, and a 0 / non-0 flag marking which files' examination
fails. The spec is parametric in that enumeration order -- it constrains WHICH
files are reported and HOW OFTEN, relative to the order the streams present them.

The specification is carried by the pure sequence theory `PSeq[int]` via
`ToSeq`. The reported id sequence is spelled out deeply as the concatenation of
two front-recursive sub-sequence folds (the first-pass ids, then the settled
adjustable ids); no callee is axiomatized — the behaviour is selection/structure
logic over the inputs, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed axiom: the report-collection behaviour is membership/structure
# logic over the input streams, modelled deeply as front-recursive folds.)
# axioms-end

# pure-start
@Pure
def first_pass_ids(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> PSeq[int]:
    """The sub-sequence of file ids reported while the FIRST pass runs, in the
    order the stream presents them: a file is reported there if it is not
    adjustable (flag 0) OR if its examination fails (flag non-0) — a failure is
    handed to the caller as the pass reaches the file, adjustable or not.
    Front-recursive so a single unfold is available per loop step (the streams
    are aligned, so all three are consumed in lock-step)."""
    Ensures(len(Result()) <= len(ids))
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return PSeq(0).take(0)
    rest = first_pass_ids(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] == 0 or err[0] != 0:
        return PSeq(ids[0]) + rest
    return rest

@Pure
def adj_ids(ids: PSeq[int], adj: PSeq[int]) -> PSeq[int]:
    """The sub-sequence of file ids that ARE adjustable (flag non-0), in the
    order the stream presents them, each appearing once — the settled segment,
    reported after the passes have stabilised, carrying each file's final
    outcome. Front-recursive."""
    Ensures(len(Result()) <= len(ids))
    if len(ids) == 0 or len(adj) == 0:
        return PSeq(0).take(0)
    rest = adj_ids(ids.drop(1), adj.drop(1))
    if adj[0] != 0:
        return PSeq(ids[0]) + rest
    return rest

@Pure
def failing_adj_count(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> int:
    """How many adjustable files have a failing examination — equivalently, how
    many files are reported in BOTH segments (once for the failure as the first
    pass reaches them, once for their settled outcome). Front-recursive."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(ids))
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return 0
    rest = failing_adj_count(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] != 0 and err[0] != 0:
        return 1 + rest
    return rest

@Pure
def reported(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> PSeq[int]:
    """The full reported id sequence: the first-pass segment (every plain id and
    every failing id, once each) followed by the settled segment (every
    adjustable id, once each)."""
    return first_pass_ids(ids, adj, err) + adj_ids(ids, adj)

@Pure
def lemma_split_len(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> bool:
    """Each file id lands in the first-pass segment, or in the settled segment,
    or — exactly when it is adjustable and its examination fails — in both. So
    the two segment lengths sum to the number of files plus the number of failing
    adjustable files. Proven by front-recursion on the aligned streams; exposed
    to callers as an equation."""
    Requires(len(ids) == len(adj))
    Requires(len(ids) == len(err))
    Ensures(Result())
    Ensures(len(first_pass_ids(ids, adj, err)) + len(adj_ids(ids, adj))
            == len(ids) + failing_adj_count(ids, adj, err))
    if len(ids) == 0:
        return True
    return lemma_split_len(ids.drop(1), adj.drop(1), err.drop(1))
# pure-end

def collect_reports(ids: List[int], adj: List[int], err: List[int]) -> List[int]:
    # pre-conditions-start
    # The three input streams are read-only (the routine reports on them, it
    # does not rewrite the collection): each is required AND ensured at HALF
    # permission (directive 5). The streams are aligned (one adjustable flag and
    # one failure flag per file).
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(Acc(list_pred(adj), 1 / 2))
    Requires(Acc(list_pred(err), 1 / 2))
    Requires(len(ids) == len(adj))
    Requires(len(ids) == len(err))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(Acc(list_pred(adj), 1 / 2))
    Ensures(Acc(list_pred(err), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The report is exactly the first-pass segment followed by the settled
    #     segment: every plain id and every failing id once as the first pass
    #     reaches it, then every adjustable id once with its final outcome. A
    #     failure therefore reaches the caller at its enumeration position and
    #     is never dropped in favour of the same file's settled report.
    Ensures(ToSeq(Result()) == reported(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    # (2) The number of reports equals the number of files, plus one for each
    #     adjustable file whose examination fails. Every file is reported; no
    #     file is reported more than once for a settled outcome (the property
    #     the repeated internal passes must NOT violate — with distinct file ids
    #     this is duplicate-freedom of the settled reports); and every failure
    #     is a report of its own rather than a substitute for one.
    Ensures(len(Result()) == len(ids)
            + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL -- a CORRECT impl (a legitimate reshape of the shipped
    # one: forward accumulation via take/index arithmetic is avoided; instead the
    # two independent tests are kept but the loop walks with an explicit counter
    # and the segments are built in the same back-to-front order). Must VERIFY,
    # else the whole rejection battery above is a broken harness rather than
    # discrimination.
    first = []  # type: List[int]
    collected = []  # type: List[int]
    i = len(ids)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(ids), 1 / 2))
        Invariant(Acc(list_pred(adj), 1 / 2))
        Invariant(Acc(list_pred(err), 1 / 2))
        Invariant(len(ids) == len(adj))
        Invariant(len(ids) == len(err))
        Invariant(Acc(list_pred(first)))
        Invariant(Acc(list_pred(collected)))
        Invariant(0 <= i and i <= len(ids))
        Invariant(ToSeq(first) == first_pass_ids(
            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        fid = ids[i - 1]
        fa = adj[i - 1]
        fe = err[i - 1]
        Assert(ToSeq(ids).drop(i - 1)[0] == fid)
        Assert(ToSeq(adj).drop(i - 1)[0] == fa)
        Assert(ToSeq(err).drop(i - 1)[0] == fe)
        Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
        Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
        Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
        if fe != 0:
            first = [fid] + first
        elif fa == 0:
            first = [fid] + first
        if fa != 0:
            collected = [fid] + collected
        i = i - 1
    result = first + collected
    Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 11 same-spec attacks run (all rc=0 on same-spec), 10 REJECTED, 1 CANDIDATE whose faithful patch RESOLVES. Positive control verifies. nagini bundle left byte-unmodified (model.py md5 ad26c5b1f307b37336e0e01fc5932763).

**CONTEXT:** the prior audit recorded BROKEN against a TWO-stream spec (ids, adj) in which the gold guard's `isinstance(processed, Exception)` operand had NO carrier. The bundle has since been REPAIRED with a third `err` stream. My job was to test whether the repair actually closes that hole and to hunt new ones. It does close it, and I proved that with a live negative control rather than by inheriting the prior verdict.

atk_0_prepatch.py       PREPATCH BUG re-encoded (impl spliced verbatim from bundle model_prepatch.py: first loop reports EVERY file, second reports each adjustable AGAIN). rc=2 does not verify. PREPATCH REPRODUCED (G-DIFF holds). atk_1_drop_err.py       DROPS THE `fe != 0` DISJUNCT -- the EXACT wrongness the prior break rode on. rc=2 REJECTED. This is the headline result: the `err` repair has teeth. atk_2_two_traversals.py TWO INDEPENDENT TRAVERSALS (re-encoding the prior pass's named counterexample against the repaired spec). rc=0 CANDIDATE, verifies 18.4s => RESOLVE-CHECKED, RESOLVES (see below). Not a break. atk_3_partial_domain.py PARTIAL DOMAIN: correct iff nothing fails; a failing file's first-pass report DEFERRED to the very end.

Count preserved, so only ordered clause (1) can sense it. rc=2 REJECTED. atk_4_boundary.py       BOUNDARY off-by-one (`while i > 1`): head of the depth-sorted enumeration never reported. rc=2 REJECTED. atk_5_control_flow.py   CONTROL-FLOW EFFECT: on the first failing file the remaining enumeration is collapsed (break via the loop counter). rc=2 REJECTED. atk_6_vacuity_echo.py   UNGROUNDED-ORACLE / VACUITY ECHO: infeasible guard `fa == 0 and fa != 0`, dead first-pass branch. rc=2 REJECTED -- spec is NOT vacuous. atk_7_swap_segments.py  SEGMENT ORDER (`collected + first`): exact count, but a failure report arrives AFTER its own settled report. rc=2 REJECTED -- the ordered equation is load-bearing, not just the length clause. atk_8_dup_settled.py    LENGTH-PRESERVING DISPLACEMENT: exactly len(ids)+failing_adj_count(...) reports, but the extra report is a 2nd copy of the SETTLED outcome, never the failure. rc=2 REJECTED -- clause (2) alone cannot be mistaken for the hand-off obligation. atk_9_reverse_settled.py INTRA-SEGMENT ORDER: settled segment in REVERSE enumeration order, exact multiplicities. rc=2 REJECTED -- pins A5's insertion-order claim. atk_10_late_failure.py  HAND-OFF POSITION: failure IS in the first-pass segment (not swallowed) but at its END rather than at the file's enumeration position. rc=2 REJECTED -- clause (1) pins position, not just presence.

**POSITIVE CONTROL:** positive_control.py (a distinct correct reshape, md5 86c77b22..., routes via `if fe != 0: ... elif fa == 0: ...`). rc=0 shares spec AND verifies (23.6s) -- non-vacuity established, so the 10 rejections are real discrimination, not a broken harness.

MANDATORY RESOLVE RUNS (harness.run_resolve, official SWE-bench Docker oracle, retries=1; launched concurrently as detached background jobs; raw JSON retained as res_*.json):
  res_gold.json      patch_gold.diff     (= bundle patch.diff, gold)        completed=True resolved=TRUE  F2P 1/1, P2P 31/31, 0 failures
  res_atk2.json      patch_atk2.diff     (faithful refinement of atk_2)     completed=True resolved=TRUE  F2P 1/1, P2P 31/31, 0 failures  <-- the ONLY verifying attack; it RESOLVES, so no break
  res_dropdisj.json  patch_dropdisj.diff NEGATIVE CONTROL (the prior break)  completed=True resolved=FALSE F2P passes; sole P2P failure 'post_processing indicates the origin of the error when it fails.'
  res_a4zero.json    patch_a4zero.diff   A4-latitude probe (0 repeat passes) completed=True resolved=FALSE P2P 27/31; fails test_import_loop, test_template_tag_relative, 'See #18050', multi-extension-patterns

WHY THIS IS NOT A RUBBER STAMP -- the negative control is the load-bearing evidence. patch_dropdisj.diff is the patch a refinement that drops the `fe != 0` disjunct would produce, i.e. the prior audit's break re-materialized from base source. It RESOLVED=FALSE on exactly the P2P test the prior break named. So the failure lane is LIVE and the hole was real. But its model-level twin atk_1_drop_err.py is now REJECTED by the spec (rc=2). Verify-rejection and resolve-failure agree: the repair closes the hole it was written for.

CLOSURE ARGUMENT (machine-checked, ext.py, exhaustive n<=5 over all 2^n x 2^n adj/err subsets = 1365 cases): postcondition (1) `ToSeq(Result()) == reported(ToSeq(ids),ToSeq(adj),ToSeq(err))` is a TOTAL EQUATION on the frozen carrier, so any verifying impl is extensionally the unique function `reported` -- zero residual functional latitude. The prior break was possible only because the 2-stream carrier could not see the `processed`/Exception operand: dropdisj vs the repaired 3-stream spec = 1001/1365 divergences (SENSED); dropdisj vs the old 2-stream spec = 0/1365 divergences (INVISIBLE -- precisely the old hole). ext.py also confirms the shipped impl is correct on all 1365 cases, and that atk_2 and positive_control are extensionally identical to it (0 divergences), which is why atk_2 verifies and resolves rather than breaking anything.

REFINEMENT.MD LEG AUDIT (protocol item 3) -- tags: A1 R, A2 R, A2b R, A3 R, A4 R, A5 R, A6 I. NO kind-3 leg; no @ContractOnly anywhere, so legitimately NO A-consumed leg (meta.json axioms=[] consistent). Every leg is R / A-reference / I as required. A1  Stream/predicate binding correct; `ids` index bound to `_post_process`'s depth-sorted enumeration order, not raw `paths` order. A2  NOW HOLDS as an R tag. This is the leg the prior break rode on, where it was a kind-3 step wearing an R tag. The `err` stream gives the dropped disjunct a carrier, `first_pass_ids` contains it, and atk_1's rejection is the executable proof that a refinement omitting it fails verification. The 'No latitude' section's claim is no longer circular -- it is now discharged by the carrier.

A2b VERIFIED AT SOURCE MYSELF: I checked the real `_post_process` except-arm at base_commit and confirmed there is NO `continue`/`return` in it -- execution falls through to the terminal `yield name, hashed_name, processed, substitutions`. So a failing adjustable file genuinely produces TWO quadruples in one pass, which is what justifies A3's UNCONDITIONAL `fa != 0` test (rather than the complement of A2's guard) and the `+1` in failing_adj_count. The per-quadruple/per-file aggregation argument is sound. A3/A4 HOLD against post-patch storage.py; the key set is pass-count-invariant because `paths` is restricted to adjustable_paths, so it can never grow. A5  ORDER binding HOLDS (insertion order preserved; atk_9 rejection pins it from the model side). A6  pure proof artefact (lemma_split_len).

A-REFERENCE (deep model <-> real callee) INDEPENDENTLY RE-RUN, 3 trees concurrently, `REPO_ROOT=<tree> python axiom_check.py`:
  tree_post  (base+gold)          rc=0 G-AX OK  -- 10 boundary + exhaustive(n<=5, all adj-subsets x each single failure) + 20000 fuzz mixed-depth; 4307 fuzz collections carry a real failure
  tree_pre   (base, unpatched)    rc=1 CORRECTLY FAILS ['a.css','a.css'] vs ['a.css'] -- the check is DISCRIMINATING, not a null check
  tree_atk2  (atk_2's patch)      rc=0 G-AX OK -- consistent with its resolve=TRUE
The A-reference is therefore real and load-bearing, and it drives the REAL `_post_process` (real depth-sort traversal + real `except ValueError` site), stubbing only storage I/O.

A4 LATITUDE PROBE (the one leg whose operand the model genuinely cannot see -- the model has no pass counter). I built a variant capping the repeat loop at ZERO passes: model-identical on the frozen carrier (`collected`'s key set is fixed in the first pass), so nothing in the postcondition can reject it. It is caught on BOTH remaining trust points: G-AX fails it (non-convergence sentinel absent) and its patch resolves=FALSE (4 P2P failures). This is out of G-EQ scope -- it DELETES a mapped op rather than refining one, and no step A1-A6 licenses altering the pass loop -- but I report it because it is where the modelled carrier is thinnest, and it is covered by G-AX rather than by the postcondition. Worth noting for the record; not a G-EQ defect.

**CONCLUSION:** verify => correct holds for this bundle on every probe I could construct. 11 attacks, 10 rejected, the 1 CANDIDATE resolves; positive control verifies; prepatch reproduced; both negative controls fail resolve on the expected tests, confirming the oracle lanes are live rather than permissive. VERDICT SOUND. Bundle left UNMODIFIED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_0_prepatch.py`, `atk_1_drop_err.py`, `atk_3_partial_domain.py`, `atk_4_boundary.py`, `atk_5_control_flow.py`, `atk_6_vacuity_echo.py`, `atk_7_swap_segments.py`, `atk_8_dup_settled.py`, `atk_9_reverse_settled.py`, `atk_10_late_failure.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2_two_traversals.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_drop_err.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_two_traversals.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_3_partial_domain.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_boundary.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_control_flow.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_vacuity_echo.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7_swap_segments.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8_dup_settled.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_reverse_settled.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_late_failure.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14053.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multi-pass routine consumes a collection of distinct files and reports, to
  its caller, the outcome for each file. Every file in the collection must be
  reported, and — this is the property under specification — each file must be
  reported EXACTLY ONCE for its settled outcome, regardless of how many internal
  passes the routine performs over it.

  The collection has two kinds of file. A plain file is settled in a single
  pass and reported once. An adjustable file (one whose contents may reference
  other files and therefore may be revisited across several passes) is, by its
  nature, examined repeatedly until the references stabilise; nevertheless the
  routine must report it to the caller only once, carrying its final outcome —
  not once per pass.

  A file's examination may also FAIL outright instead of yielding a settled
  outcome. That failure outcome is not the routine's to interpret: the caller is
  the component that decides what a failure means and acts on it (it stops the
  run and re-surfaces the failure), so the routine must hand every failure to
  the caller AT THE POINT THE FIRST PASS REACHES IT, at the position the
  enumeration gives that file. This obligation is INDEPENDENT of the multiplicity
  property above, and holding a file back in order to satisfy that property must
  not swallow it: a failure outcome may never be deferred to the end of the run,
  and may never be displaced by the same file's later settled outcome. Deferring
  or displacing it is observable to the caller as a run that reports a settled
  outcome for a file whose examination did not settle, and never reports the
  failure at all.

  Concretely, the reported sequence is two segments. The FIRST-PASS segment:
  every plain file, plus every adjustable file whose examination fails, each
  appearing once, in the order in which the routine enumerates the collection.
  Then the SETTLED segment: every adjustable file, each appearing once, in that
  same enumeration order. The number of reports is therefore the number of files
  in the collection plus one for each adjustable file whose examination fails
  (which is reported for its failure and again for its settled outcome); no file
  is reported twice for a settled outcome.

The collection is modelled as three equal-length parallel `List[int]` streams,
presented in the order the routine enumerates the files: a distinct integer id
per file (the input is keyed, so ids do not repeat), a 0 / non-0 flag marking
which files are adjustable, and a 0 / non-0 flag marking which files' examination
fails. The spec is parametric in that enumeration order -- it constrains WHICH
files are reported and HOW OFTEN, relative to the order the streams present them.

The specification is carried by the pure sequence theory `PSeq[int]` via
`ToSeq`. The reported id sequence is spelled out deeply as the concatenation of
two front-recursive sub-sequence folds (the first-pass ids, then the settled
adjustable ids); no callee is axiomatized — the behaviour is selection/structure
logic over the inputs, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No consumed axiom: the report-collection behaviour is membership/structure
# logic over the input streams, modelled deeply as front-recursive folds.)
# axioms-end

# pure-start
@Pure
def first_pass_ids(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> PSeq[int]:
    """The sub-sequence of file ids reported while the FIRST pass runs, in the
    order the stream presents them: a file is reported there if it is not
    adjustable (flag 0) OR if its examination fails (flag non-0) — a failure is
    handed to the caller as the pass reaches the file, adjustable or not.
    Front-recursive so a single unfold is available per loop step (the streams
    are aligned, so all three are consumed in lock-step)."""
    Ensures(len(Result()) <= len(ids))
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return PSeq(0).take(0)
    rest = first_pass_ids(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] == 0 or err[0] != 0:
        return PSeq(ids[0]) + rest
    return rest

@Pure
def adj_ids(ids: PSeq[int], adj: PSeq[int]) -> PSeq[int]:
    """The sub-sequence of file ids that ARE adjustable (flag non-0), in the
    order the stream presents them, each appearing once — the settled segment,
    reported after the passes have stabilised, carrying each file's final
    outcome. Front-recursive."""
    Ensures(len(Result()) <= len(ids))
    if len(ids) == 0 or len(adj) == 0:
        return PSeq(0).take(0)
    rest = adj_ids(ids.drop(1), adj.drop(1))
    if adj[0] != 0:
        return PSeq(ids[0]) + rest
    return rest

@Pure
def failing_adj_count(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> int:
    """How many adjustable files have a failing examination — equivalently, how
    many files are reported in BOTH segments (once for the failure as the first
    pass reaches them, once for their settled outcome). Front-recursive."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(ids))
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return 0
    rest = failing_adj_count(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] != 0 and err[0] != 0:
        return 1 + rest
    return rest

@Pure
def reported(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> PSeq[int]:
    """The full reported id sequence: the first-pass segment (every plain id and
    every failing id, once each) followed by the settled segment (every
    adjustable id, once each)."""
    return first_pass_ids(ids, adj, err) + adj_ids(ids, adj)

@Pure
def lemma_split_len(ids: PSeq[int], adj: PSeq[int], err: PSeq[int]) -> bool:
    """Each file id lands in the first-pass segment, or in the settled segment,
    or — exactly when it is adjustable and its examination fails — in both. So
    the two segment lengths sum to the number of files plus the number of failing
    adjustable files. Proven by front-recursion on the aligned streams; exposed
    to callers as an equation."""
    Requires(len(ids) == len(adj))
    Requires(len(ids) == len(err))
    Ensures(Result())
    Ensures(len(first_pass_ids(ids, adj, err)) + len(adj_ids(ids, adj))
            == len(ids) + failing_adj_count(ids, adj, err))
    if len(ids) == 0:
        return True
    return lemma_split_len(ids.drop(1), adj.drop(1), err.drop(1))
# pure-end

def collect_reports(ids: List[int], adj: List[int], err: List[int]) -> List[int]:
    # pre-conditions-start
    # The three input streams are read-only (the routine reports on them, it
    # does not rewrite the collection): each is required AND ensured at HALF
    # permission (directive 5). The streams are aligned (one adjustable flag and
    # one failure flag per file).
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(Acc(list_pred(adj), 1 / 2))
    Requires(Acc(list_pred(err), 1 / 2))
    Requires(len(ids) == len(adj))
    Requires(len(ids) == len(err))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(Acc(list_pred(adj), 1 / 2))
    Ensures(Acc(list_pred(err), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The report is exactly the first-pass segment followed by the settled
    #     segment: every plain id and every failing id once as the first pass
    #     reaches it, then every adjustable id once with its final outcome. A
    #     failure therefore reaches the caller at its enumeration position and
    #     is never dropped in favour of the same file's settled report.
    Ensures(ToSeq(Result()) == reported(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    # (2) The number of reports equals the number of files, plus one for each
    #     adjustable file whose examination fails. Every file is reported; no
    #     file is reported more than once for a settled outcome (the property
    #     the repeated internal passes must NOT violate — with distinct file ids
    #     this is duplicate-freedom of the settled reports); and every failure
    #     is a report of its own rather than a substitute for one.
    Ensures(len(Result()) == len(ids)
            + failing_adj_count(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL -- a CORRECT impl (a legitimate reshape of the shipped
    # one: forward accumulation via take/index arithmetic is avoided; instead the
    # two independent tests are kept but the loop walks with an explicit counter
    # and the segments are built in the same back-to-front order). Must VERIFY,
    # else the whole rejection battery above is a broken harness rather than
    # discrimination.
    first = []  # type: List[int]
    collected = []  # type: List[int]
    i = len(ids)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(ids), 1 / 2))
        Invariant(Acc(list_pred(adj), 1 / 2))
        Invariant(Acc(list_pred(err), 1 / 2))
        Invariant(len(ids) == len(adj))
        Invariant(len(ids) == len(err))
        Invariant(Acc(list_pred(first)))
        Invariant(Acc(list_pred(collected)))
        Invariant(0 <= i and i <= len(ids))
        Invariant(ToSeq(first) == first_pass_ids(
            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))
        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        fid = ids[i - 1]
        fa = adj[i - 1]
        fe = err[i - 1]
        Assert(ToSeq(ids).drop(i - 1)[0] == fid)
        Assert(ToSeq(adj).drop(i - 1)[0] == fa)
        Assert(ToSeq(err).drop(i - 1)[0] == fe)
        Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
        Assert(ToSeq(adj).drop(i - 1).drop(1) == ToSeq(adj).drop(i))
        Assert(ToSeq(err).drop(i - 1).drop(1) == ToSeq(err).drop(i))
        if fe != 0:
            first = [fid] + first
        elif fa == 0:
            first = [fid] + first
        if fa != 0:
            collected = [fid] + collected
        i = i - 1
    result = first + collected
    Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 11 same-spec attacks run (all rc=0 on same-spec), 10 REJECTED, 1 CANDIDATE whose faithful patch RESOLVES. Positive control verifies. nagini bundle left byte-unmodified (model.py md5 ad26c5b1f307b37336e0e01fc5932763).

**CONTEXT:** the prior audit recorded BROKEN against a TWO-stream spec (ids, adj) in which the gold guard's `isinstance(processed, Exception)` operand had NO carrier. The bundle has since been REPAIRED with a third `err` stream. My job was to test whether the repair actually closes that hole and to hunt new ones. It does close it, and I proved that with a live negative control rather than by inheriting the prior verdict.

atk_0_prepatch.py       PREPATCH BUG re-encoded (impl spliced verbatim from bundle model_prepatch.py: first loop reports EVERY file, second reports each adjustable AGAIN). rc=2 does not verify. PREPATCH REPRODUCED (G-DIFF holds). atk_1_drop_err.py       DROPS THE `fe != 0` DISJUNCT -- the EXACT wrongness the prior break rode on. rc=2 REJECTED. This is the headline result: the `err` repair has teeth. atk_2_two_traversals.py TWO INDEPENDENT TRAVERSALS (re-encoding the prior pass's named counterexample against the repaired spec). rc=0 CANDIDATE, verifies 18.4s => RESOLVE-CHECKED, RESOLVES (see below). Not a break. atk_3_partial_domain.py PARTIAL DOMAIN: correct iff nothing fails; a failing file's first-pass report DEFERRED to the very end.

Count preserved, so only ordered clause (1) can sense it. rc=2 REJECTED. atk_4_boundary.py       BOUNDARY off-by-one (`while i > 1`): head of the depth-sorted enumeration never reported. rc=2 REJECTED. atk_5_control_flow.py   CONTROL-FLOW EFFECT: on the first failing file the remaining enumeration is collapsed (break via the loop counter). rc=2 REJECTED. atk_6_vacuity_echo.py   UNGROUNDED-ORACLE / VACUITY ECHO: infeasible guard `fa == 0 and fa != 0`, dead first-pass branch. rc=2 REJECTED -- spec is NOT vacuous. atk_7_swap_segments.py  SEGMENT ORDER (`collected + first`): exact count, but a failure report arrives AFTER its own settled report. rc=2 REJECTED -- the ordered equation is load-bearing, not just the length clause. atk_8_dup_settled.py    LENGTH-PRESERVING DISPLACEMENT: exactly len(ids)+failing_adj_count(...) reports, but the extra report is a 2nd copy of the SETTLED outcome, never the failure. rc=2 REJECTED -- clause (2) alone cannot be mistaken for the hand-off obligation. atk_9_reverse_settled.py INTRA-SEGMENT ORDER: settled segment in REVERSE enumeration order, exact multiplicities. rc=2 REJECTED -- pins A5's insertion-order claim. atk_10_late_failure.py  HAND-OFF POSITION: failure IS in the first-pass segment (not swallowed) but at its END rather than at the file's enumeration position. rc=2 REJECTED -- clause (1) pins position, not just presence.

**POSITIVE CONTROL:** positive_control.py (a distinct correct reshape, md5 86c77b22..., routes via `if fe != 0: ... elif fa == 0: ...`). rc=0 shares spec AND verifies (23.6s) -- non-vacuity established, so the 10 rejections are real discrimination, not a broken harness.

MANDATORY RESOLVE RUNS (harness.run_resolve, official SWE-bench Docker oracle, retries=1; launched concurrently as detached background jobs; raw JSON retained as res_*.json):
  res_gold.json      patch_gold.diff     (= bundle patch.diff, gold)        completed=True resolved=TRUE  F2P 1/1, P2P 31/31, 0 failures
  res_atk2.json      patch_atk2.diff     (faithful refinement of atk_2)     completed=True resolved=TRUE  F2P 1/1, P2P 31/31, 0 failures  <-- the ONLY verifying attack; it RESOLVES, so no break
  res_dropdisj.json  patch_dropdisj.diff NEGATIVE CONTROL (the prior break)  completed=True resolved=FALSE F2P passes; sole P2P failure 'post_processing indicates the origin of the error when it fails.'
  res_a4zero.json    patch_a4zero.diff   A4-latitude probe (0 repeat passes) completed=True resolved=FALSE P2P 27/31; fails test_import_loop, test_template_tag_relative, 'See #18050', multi-extension-patterns

WHY THIS IS NOT A RUBBER STAMP -- the negative control is the load-bearing evidence. patch_dropdisj.diff is the patch a refinement that drops the `fe != 0` disjunct would produce, i.e. the prior audit's break re-materialized from base source. It RESOLVED=FALSE on exactly the P2P test the prior break named. So the failure lane is LIVE and the hole was real. But its model-level twin atk_1_drop_err.py is now REJECTED by the spec (rc=2). Verify-rejection and resolve-failure agree: the repair closes the hole it was written for.

CLOSURE ARGUMENT (machine-checked, ext.py, exhaustive n<=5 over all 2^n x 2^n adj/err subsets = 1365 cases): postcondition (1) `ToSeq(Result()) == reported(ToSeq(ids),ToSeq(adj),ToSeq(err))` is a TOTAL EQUATION on the frozen carrier, so any verifying impl is extensionally the unique function `reported` -- zero residual functional latitude. The prior break was possible only because the 2-stream carrier could not see the `processed`/Exception operand: dropdisj vs the repaired 3-stream spec = 1001/1365 divergences (SENSED); dropdisj vs the old 2-stream spec = 0/1365 divergences (INVISIBLE -- precisely the old hole). ext.py also confirms the shipped impl is correct on all 1365 cases, and that atk_2 and positive_control are extensionally identical to it (0 divergences), which is why atk_2 verifies and resolves rather than breaking anything.

REFINEMENT.MD LEG AUDIT (protocol item 3) -- tags: A1 R, A2 R, A2b R, A3 R, A4 R, A5 R, A6 I. NO kind-3 leg; no @ContractOnly anywhere, so legitimately NO A-consumed leg (meta.json axioms=[] consistent). Every leg is R / A-reference / I as required. A1  Stream/predicate binding correct; `ids` index bound to `_post_process`'s depth-sorted enumeration order, not raw `paths` order. A2  NOW HOLDS as an R tag. This is the leg the prior break rode on, where it was a kind-3 step wearing an R tag. The `err` stream gives the dropped disjunct a carrier, `first_pass_ids` contains it, and atk_1's rejection is the executable proof that a refinement omitting it fails verification. The 'No latitude' section's claim is no longer circular -- it is now discharged by the carrier.

A2b VERIFIED AT SOURCE MYSELF: I checked the real `_post_process` except-arm at base_commit and confirmed there is NO `continue`/`return` in it -- execution falls through to the terminal `yield name, hashed_name, processed, substitutions`. So a failing adjustable file genuinely produces TWO quadruples in one pass, which is what justifies A3's UNCONDITIONAL `fa != 0` test (rather than the complement of A2's guard) and the `+1` in failing_adj_count. The per-quadruple/per-file aggregation argument is sound. A3/A4 HOLD against post-patch storage.py; the key set is pass-count-invariant because `paths` is restricted to adjustable_paths, so it can never grow. A5  ORDER binding HOLDS (insertion order preserved; atk_9 rejection pins it from the model side). A6  pure proof artefact (lemma_split_len).

A-REFERENCE (deep model <-> real callee) INDEPENDENTLY RE-RUN, 3 trees concurrently, `REPO_ROOT=<tree> python axiom_check.py`:
  tree_post  (base+gold)          rc=0 G-AX OK  -- 10 boundary + exhaustive(n<=5, all adj-subsets x each single failure) + 20000 fuzz mixed-depth; 4307 fuzz collections carry a real failure
  tree_pre   (base, unpatched)    rc=1 CORRECTLY FAILS ['a.css','a.css'] vs ['a.css'] -- the check is DISCRIMINATING, not a null check
  tree_atk2  (atk_2's patch)      rc=0 G-AX OK -- consistent with its resolve=TRUE
The A-reference is therefore real and load-bearing, and it drives the REAL `_post_process` (real depth-sort traversal + real `except ValueError` site), stubbing only storage I/O.

A4 LATITUDE PROBE (the one leg whose operand the model genuinely cannot see -- the model has no pass counter). I built a variant capping the repeat loop at ZERO passes: model-identical on the frozen carrier (`collected`'s key set is fixed in the first pass), so nothing in the postcondition can reject it. It is caught on BOTH remaining trust points: G-AX fails it (non-convergence sentinel absent) and its patch resolves=FALSE (4 P2P failures). This is out of G-EQ scope -- it DELETES a mapped op rather than refining one, and no step A1-A6 licenses altering the pass loop -- but I report it because it is where the modelled carrier is thinnest, and it is covered by G-AX rather than by the postcondition. Worth noting for the record; not a G-EQ defect.

**CONCLUSION:** verify => correct holds for this bundle on every probe I could construct. 11 attacks, 10 rejected, the 1 CANDIDATE resolves; positive control verifies; prepatch reproduced; both negative controls fail resolve on the expected tests, confirming the oracle lanes are live rather than permissive. VERDICT SOUND. Bundle left UNMODIFIED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK: faithfulness-break on django__django-14053 (nagini). Verdict FAITHFUL — no undisclosed divergence found between the modelled function and the real patched callee.

SETUP. Fresh worktree at base_commit 179ee13eb37348cd87169a198aec18fedccc8668 with the gold patch (from data/swe_bench_verified/test.jsonl, byte-identical to meta.json's patch_diff intent) APPLIED — the correct reference tree per the brief. Second worktree left at base_commit for the direction check only.

**SPEC-REGION INTEGRITY:** `adversary same-spec nagini django__django-14053 <copy of model.py>` -> exit 0, "SAME — attack shares the bundle's exact specification". `scripts/nagini_verify.sh model.py` -> exit 0 ("Verification successful", 17.3s), so the spec region is the frozen one and it really does verify.

INDEPENDENT ORACLE (my own, NOT the bundle's stub). I wrote harness.py: real `django.contrib.staticfiles.storage.HashedFilesMixin` over a real `FileSystemStorage` on a real temp filesystem, real `_patterns` (the shipped *.css url(...)/@import patterns), real `hashed_name`/`file_hash`/`url_converter`/`_post_process`. NOTHING stubbed — failures are produced by genuinely missing referenced files (real ValueError from `hashed_name`), and multi-pass substitution is driven by genuinely nested @import chains. This is a strictly harder oracle than axiom_check.py/conformance_check.py, which stub storage I/O and url_converter.

### Results
(1) fuzz.py — 400 real-filesystem collections (0..9 files, mixed depths 1..4, random adjustable/failing subsets, keep_intermediate_files toggled), one failing rewrite pattern per file (mapping.md §2's stated binding): seq_mismatch=0, len_mismatch=0, observable_prefix_mismatch=0, with 203 runs carrying a REAL failure and 288 genuinely reordered by the depth sort. So postcondition (1) ToSeq(Result())==reported(...) and (2) len==len(ids)+failing_adj_count(...) both hold exactly on the real callee.

(2) Real multi-pass convergence: a 4-deep nested @import chain (css/a->b->c->d) plus a plain png reports each file exactly once, matching `reported` — confirms mapping.md's "pass count drops out" claim against real substitution, not a settling stub.

(3) Enumeration-order binding probed directly: `paths` order ['d/z.css','d/a.css','d/m.png','q.css'] -> real output ['d/m.png','d/z.css','d/a.css','q.css'] == model under the depth-sort binding. mapping.md §2 explicitly documents this binding (and records the corrected 19252/30000 failure of the older "paths iteration order" reading), so it is disclosed, not smuggled.

(4) THE REAL P2P FIXTURE: tests/staticfiles_tests/project/faulty/faulty.css is `@import url("missing.css");`. I feared this string matches BOTH shipped css patterns and would yield 3 reports vs the model's 2. It does not — real output is exactly ['faulty.css','faulty.css'] (one ValueError report, then the settled report), i.e. len 2 == len(ids)+failing_adj_count = 1+1. The specific input the failure-path PASS_TO_PASS test drives matches the spec EXACTLY. This was my strongest candidate counterexample and it is refuted.

**THE ONE MEASURED DIVERGENCE IS DISCLOSED AND SOUND-AT-THE-OBSERVABLE.** fuzz2.py (500 runs) deliberately fed files failing under TWO distinct patterns (e.g. `@import "gone_a.css"; body{background:url("gone_b.png")}`). Raw-sequence mismatch 271/500 — and exactly 271 runs were the multi-pattern ones (multi=271), i.e. the divergence is 1:1 with per-file failure multiplicity and nothing else. Real output for such a file is [f, f, f] (two exception reports at the same enumeration position, then the settled report); the model says [f, f]. This is NOT an undisclosed break:

  (a) It is explicitly declared in BOTH docs before I looked: refinement.md "Scope actually claimed" bullet 1 ("Per-file failure multiplicity ... one report per failure, at the same enumeration position. The model abstracts that to one") and mapping.md §2 "Per-file failure multiplicity (scope, stated)", both citing storage.py:294-301.

  (b) It is unobservable to the caller, and I verified that mechanically rather than taking the prose: collect() (collectstatic.py:129-134) `raise processed` on the FIRST Exception report, so reports after it are never consumed. In fuzz2.py, on all 500 runs including the 271 divergent ones: observable_prefix_mismatch=0 (the stream up to and including the first Exception is identical to the model's), abort_bad=0 (collect() aborts on exactly the file the model's first_pass_ids names first), nonrecorded_bad=0 (with nothing failing, the recorded set is exactly the file set). The extra reports fall strictly AFTER the abort point.

  (c) The abstraction is conservative in the safe direction — it under-counts duplicate FAILURE reports; it never under-counts settled reports, which is where the F2P property lives.

SPEC-TOO-STRONG CHECKS (the drift direction I was asked to press). Preconditions are Acc(list_pred,1/2)x3 + len(ids)==len(adj)==len(err) + MustTerminate(2) — no hidden carve-out excluding the awkward inputs. Empty collection: model gives [], real gives [] (covered in fuzz, n=0 drawn). The admitted-but-unreachable adj[k]==0 & err[k]!=0 binding: mapping.md §2 states it and claims model-insensitivity; I confirmed against the real callee that url_converter is only reached inside `if name in adjustable_paths:` (storage.py:291), so a plain file's `processed` is never an Exception, and axiom_check.py line ~425 asserts m_reported(ids,adj,raw_err)==expected. The spec claims nothing about a state the callee cannot occupy.

Two out-of-carrier arms I probed and found correctly scoped: dry_run=True (real yields [], no file identity, and the model's domain is the reporting body) and non-convergence ('All', None, RuntimeError) — the latter is unchanged context in patch.diff, is caller-observable via test_import_loop, and axiom_check.py pins it executably as purely additive (sentinel exactly between the two modelled segments). I separately note max_post_process_passes=0 raises UnboundLocalError on `substitutions` in the real code — a genuine pre-existing repo bug, present identically at base_commit, untouched by the patch and outside any step A1-A6, so not a spec-faithfulness defect.

DIRECTION CHECK (guards against rubber-stamping a vacuous spec). Against the BASE tree the same axiom_check.py FAILS with a real counterexample: files=['a.css'] adjustable=['a.css'] -> real pre-patch yields ['a.css','a.css'], model `reported` says ['a.css']. So the spec genuinely senses the patch's delta and is not trivially satisfiable. refinement.md's model_prepatch.py claim (fails postconditions 1 and 2) is consistent with that.

**BUNDLE GATES REPRODUCED ON MY PATCHED WORKTREE:** axiom_check.py exit 0 (20000 fuzz + exhaustive files<=5 x all adjustable-subsets x each single failure; 4307 fuzz cases with a real failure; both anti-vacuity guards `_assert_suite_exercises_depth_sort` and `_assert_suite_exercises_failures` active). conformance_check.py exit 0, 100035 inputs, 0 disagreements, 81513 depth-reordered, 55405 with a real failure. Full staticfiles_tests.test_storage suite: 32 tests, OK — including the F2P assertCountEqual and test_post_processing_failure and test_import_loop.

**CONCLUSION:** no diverging input exists on the modelled convergent domain under the documented bindings. Every divergence I could manufacture (multi-pattern per-file failure) is pre-disclosed in refinement.md and mapping.md, is invisible to the only caller (collect() aborts first — measured, prefix/abort/record mismatches all 0), and errs conservatively. FAITHFUL.

**ATTACK:** faithfulness-break on django__django-14053 (nagini). Verdict FAITHFUL — no undisclosed divergence found between the modelled function and the real patched callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE / RELAXATION. No relaxation is claimed or present: meta.json has no `relaxed_leakage` key (grepped the whole JSON), gates.G-LEAK.status = "pass" (mode strict), and RELAXED_LEAKAGE.md does not exist in the bundle. So this is an ordinary strict leakage judgement, not an inherited disposition. I also scanned every bundle file for text addressing a reviewer (G-PANEL / attacker / 'the honest verdict' / 'record NO-LEAKAGE' / submit directives): the only hits are properties.py:41,49, which say the PBT author does 'NOT submit' a certain property as a spec break -- author-facing scoping of properties.py, not an instruction to this panel. verdict.md contains prior panel notes including a previous NO-LEAKAGE writeup; I did not rely on it (see STALENESS below) and treated it only as a claim to re-derive. Nothing in the bundle tries to direct my verdict.

SPEC VIEW MEASURED, NOT ASSUMED. spec_view(model.py, NaginiBackend) = docstring + axioms + pure + signature + pre/post-conditions; impl and invariants elided (EvalAdapter.spec_view hard-guards the impl elision before exposure). model.py sha256 78241d0cc46e...; spec_view sha256 960b1b1d41dd... == meta.json region_hashes.spec_view AND == gates.G-LEAK.sources['model.py'] digest of the live bytes, so the recorded leak stamp is on exactly the bytes I screened.

MECHANICAL SCREEN (re-run, not read off). leakage.screen(model.py, nagini language, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Independently re-derived the sub-checks against the spec view: (a) ZERO gold changed lines reproduced at >=8 normalized chars; (b) `_NARRATION_RE` findall = [] (no bug/fix/patch/previously/incorrectly narration); (c) patched path 'django/contrib/staticfiles/storage.py' and dotted 'staticfiles.storage' both ABSENT; (d) `_patch_changed_symbols`(gold) = {'post_process'}, and 'post_process' does not occur anywhere in the spec view -- and it is public regardless, appearing verbatim in problem_statement line 1 ('post_process() yields multiple times for the same file').

Repo-vocabulary sweep of the spec view: post_process 0, storage 0, staticfiles 0, collectstatic 0, adjustable_paths 0, isinstance 0, Exception 0, hash 0, dict 0, buffer 0, overwrite 0, substitutions 0, max_post_process 0. The gold's mechanism nouns -- dict keyed by name, per-pass overwrite, terminal `yield from` -- appear NOWHERE in the consumer view. The genuinely mechanism-narrating prose ('collected, keyed by file, so each is held only once', 'result = first + collected') lives in the impl region and I confirmed it is elided.

THE ONE CLAUSE WORTH ATTACKING, AND WHY IT SURVIVES. The spec view says more than problem_statement in exactly one place: the failure hand-off (the `err` stream, first_pass_ids' `err[0] != 0` disjunct, failing_adj_count, and the docstring paragraph 'a failure outcome may never be deferred to the end of the run'). problem_statement contains ZERO occurrences of fail/error/exception/raise/except (measured). So I tested whether that clause reconstructs the gold edit, using the load-bearing test.

  (1) LOAD-BEARING, not decorative. I built atk_defer.py -- the atk_7 shape: satisfies multiplicity (each file once for its settled outcome) but DROPS the `fe != 0` disjunct, holding failing files back to the settled segment. `adversary same-spec` -> exit 0 (SAME spec, impl-only change). nagini_verify -> Verification FAILED: 'Postcondition of collect_reports might not hold ... ToSeq(Result()) == reported(...)'. So the clause is what rejects the known verify-but-not-resolve implementation (meta.json records G-EQ/G-PANEL-1 failing on exactly that atk_7, PASS_TO_PASS 'post_processing indicates the origin of the error when it fails'). Stripping the clause weakens the spec; it is not gratuitous.

  (2) IT DESCRIBES PRE-PATCH BEHAVIOUR, so it cannot reveal the edit. This is the decisive measurement. I materialized base_commit 179ee13eb37  and the gold-applied tree, then drove the REAL post_process on both (failpos.py, 4 collections with reachable ValueError failures). Result: 'failure report is the FIRST report for that file' holds ok=4 bad=0 on BOTH trees. The failure hand-off at first-pass position is UNCHANGED CONTEXT -- true before the patch and after it. A clause that both pre- and post-patch code satisfy carries zero information about the delta, so it cannot be gold reconstruction. Its public source is the repo itself at base_commit (`except ValueError as exc: yield name, None, exc, False` at storage.py:300, and the PRE-EXISTING test test_post_processing_failure asserting "Post-processing 'faulty.css' failed!", both present at base_commit -- confirmed by git log). It is repo-visible to any solver, not hints_text-only. I checked hints_text (493 chars, about max_post_process_passes looping) -- the failure clause is NOT drawn from it, so the 'echoes hints-only vocabulary' failure mode does not apply.

  (3) The gold DELTA itself is what the spec pins behaviourally, which is attacker-1 territory, not leakage: G-DIFF requires model_prepatch.py to fail, so the spec must pin the reported sequence, and any total order it pins necessarily coincides with gold's.

STRUCTURE IS NOT PINNED (no gold reconstruction). I built atk_twoloop.py: same spec, but a materially different shape -- two INDEPENDENT re-enumerations of the streams with no shared buffer accumulated alongside the first segment, i.e. not the gold's single-pass-collect-into-a-dict-then-flush structure. same-spec -> exit 0; nagini_verify -> 'Verification successful' (24.0s). So the spec admits implementations structurally unlike the gold: it constrains the observable reported sequence, not the gold's mechanism. A solver reading the spec view still has to invent the restructuring of post_process (buffer keyed by name, suppress the per-pass yield, flush at the end) themselves. That is directive 6's sanctioned behavioural-contract form.

CORE GATES I LEANED ON, CONFIRMED FIRST-HAND (not read off meta.json). G-AX: ran axiom_check.py against BOTH trees -- REPO_ROOT=wt_post exits 0 with the recorded detail (20000 fuzz + exhaustive, 4307 carrying a real failure); REPO_ROOT=wt (pre-patch) correctly FAILS with 'deep model unsound: real post_process yielded [a.css, a.css] vs model [a.css]'. So the A-reference deep model is genuinely discriminating and axiom_check is not a null check. G-VERIFY/G-MUT are stamped on the live model.py digest (verified match). Gold patch applies cleanly at base_commit.

STALENESS FLAGGED (an integrity item, NOT a leakage defect, and it is why I re-derived rather than inherited). G-EQ / G-PANEL / G-PANEL-1/2/3 are all stamped against model.py 74b116b55ec0..., which is NOT the live model.py (78241d0cc46e...). The prior NO-LEAKAGE record therefore judged OLDER bytes. Per git (a19a2008b -> HEAD), the drift is exactly the addition of the third `err` stream and the failure-hand-off clause -- i.e. the one clause a leakage reviewer must weigh was added AFTER the last leakage stamp. I screened the live bytes: clean on the mechanical screen and clean on my own load-bearing/pre-patch analysis above. Operator item: G-EQ/G-PANEL-1 are recorded 'fail' on stale bytes against atk_7, which the current spec now rejects (measured in (1)) -- those need re-running, and green_check.classify remains the only authority for green. My leakage verdict is unaffected either way.

**VERDICT:** NO-LEAKAGE. No diff marker, no gold line, no patched path/symbol, no fix narration; the only super-problem_statement clause is unchanged pre-patch repo behaviour that is load-bearing for spec strength, and the spec demonstrably does not pin the gold's structure. Bundle worked on read-only; all artifacts  and *.py.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
