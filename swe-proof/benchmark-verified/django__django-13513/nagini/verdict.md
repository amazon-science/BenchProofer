# P2 adversarial audit — django__django-13513

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No verifying same-spec wrong impl produced a non-resolving faithful patch. The two CANDIDATEs (atk_8, atk_9) both verify AND both of their materialized faithful patches RESOLVE under the official harness (resolved=true, completed=true, attempts=1, flaky=false, FAIL_TO_PASS 1/1, PASS_TO_PASS 83/83) -- i.e. they are not wrong impls in any observable sense, so verify=>correct is upheld on every probe I could construct. IMPORTANT: the prior round's recorded BROKEN counterexample (equal-length provenance substitution: 'if i == n and n >= 2 and trace_lens[0] == trace_lens[n-1]: src = 0') was re-encoded verbatim as atk_2 and is now REJECTED by the repaired spec. The bundle was repaired since the recorded G-EQ fail: meta.json's G-EQ/G-PANEL fails are stamped at model.py hash 9b944d60bf5f (the OLD spec, entry_trace_index), while the current spec is hash b4244e917f1e (entry_location, globally-unique chain location numbers) and every other gate passes at the current hash. Per 'SPEC-MOVED is about the record, not the bytes' I re-derived everything rather than inheriting the stale fail.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,20 +231,14 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
+    # A SINGLE traversal pointer walks the chain from its end. It enters the
+    # trace of the exception being consumed and only ever advances to the NEXT
+    # exception from INSIDE the per-location loop, so an exception whose own
+    # trace records no location leaves the pointer with nothing to advance from:
+    # the walk stops there and every exception still unconsumed -- however many
+    # locations its own trace records -- is left out of the report.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
-    suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
-    base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
-    total = chain_total(ToSeq(trace_lens))
-    head = total
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(trace_lens), 1 / 2))
@@ -253,61 +247,38 @@
         Invariant(n == len(trace_lens))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                  trace_lens[k] >= 0)))
-        Invariant(suffix == ToSeq(trace_lens).drop(i))
-        Invariant(base == chain_total(suffix))
-        Invariant(total == chain_total(ToSeq(trace_lens)))
-        Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
-        Invariant(len(frames) == base)
-        Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
-                                                frames[p] ==
-                                                head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
-        Invariant(Implies(i > 0,
-                          ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
-        Invariant(Implies(i > 0,
-                          chain_total(ToSeq(trace_lens).drop(i - 1)) ==
-                          trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
-        Invariant(Implies(i > 0,
-                          Forall(int, lambda p: Implies(
-                              0 <= p and p < base,
-                              entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
-                              trace_lens[i - 1] +
-                              entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
-        Invariant(Implies(i > 0,
-                          Forall(int, lambda p: Implies(
-                              base <= p and p < base + trace_lens[i - 1],
-                              entry_location(ToSeq(trace_lens).drop(i - 1),
-                                             p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
+        # TERMINATION: at most `i` passes remain; `i` either drops by one or is
+        # cleared when the walk stops, so the bound strictly decreases.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
-        m = len(contribution)
-        frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
-        i = i - 1
-        longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
-        suffix = longer
-        base = base + m
-        head = head - m
+        m = trace_lens[i - 1]
+        # where the block of chain location numbers owned by the exception the
+        # pointer is walking begins
+        start = locations_before(ToSeq(trace_lens), i - 1)
+        # Position of the location the pointer stands on within the trace it is
+        # walking; the entry emitted describes that location.
+        pos = 0
+        while pos < m:
+            # invariants-start
+            Invariant(Acc(list_pred(trace_lens), 1 / 2))
+            Invariant(Acc(list_pred(frames)))
+            Invariant(n == len(trace_lens))
+            Invariant(0 < i and i <= n)
+            Invariant(0 <= pos and pos <= m)
+            Invariant(m == trace_lens[i - 1])
+            Invariant(start == locations_before(ToSeq(trace_lens), i - 1))
+            Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
+                                                     trace_lens[k] >= 0)))
+            # TERMINATION: at most `m - pos` passes remain within this trace.
+            Invariant(MustTerminate(m - pos + 1))
+            # invariants-end
+            frames.append(start + pos)
+            pos = pos + 1
+        if m == 0:
+            # The pointer never entered a location, so there is nothing for it to
+            # advance from: the walk ends here.
+            i = 0
+        else:
+            i = i - 1
     return frames
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,18 +231,10 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
     suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
     base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
     total = chain_total(ToSeq(trace_lens))
     head = total
     while i > 0:
@@ -257,53 +249,34 @@
         Invariant(base == chain_total(suffix))
         Invariant(total == chain_total(ToSeq(trace_lens)))
         Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
         Invariant(len(frames) == base)
         Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                 frames[p] ==
                                                 head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
         Invariant(Implies(i > 0,
                           ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                           trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               0 <= p and p < base,
                               entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                               trace_lens[i - 1] +
                               entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               base <= p and p < base + trace_lens[i - 1],
                               entry_location(ToSeq(trace_lens).drop(i - 1),
                                              p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
+        src = i - 1
+        if i == n and n >= 2 and trace_lens[0] == trace_lens[n - 1]:
+            src = 0
+        contribution = frames_from_traceback(ToSeq(trace_lens), src)
         m = len(contribution)
         frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
         i = i - 1
         longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
         suffix = longer
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,18 +231,10 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
     suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
     base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
     total = chain_total(ToSeq(trace_lens))
     head = total
     while i > 0:
@@ -257,53 +249,37 @@
         Invariant(base == chain_total(suffix))
         Invariant(total == chain_total(ToSeq(trace_lens)))
         Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
         Invariant(len(frames) == base)
         Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                 frames[p] ==
                                                 head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
         Invariant(Implies(i > 0,
                           ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                           trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               0 <= p and p < base,
                               entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                               trace_lens[i - 1] +
                               entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               base <= p and p < base + trace_lens[i - 1],
                               entry_location(ToSeq(trace_lens).drop(i - 1),
                                              p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
+        src = i - 1
+        if n >= 3:
+            if i == n:
+                src = n - 2
+            elif i == n - 1:
+                src = n - 1
+        contribution = frames_from_traceback(ToSeq(trace_lens), src)
         m = len(contribution)
         frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
         i = i - 1
         longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
         suffix = longer
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -165,7 +165,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # where this exception's own block of chain location numbers begins
     start = locations_before(chain, k)
     trace_len = chain[k]
     i = 0
@@ -178,13 +177,12 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                                                 result[j] == start + j)))
-        # TERMINATION: at most `trace_len - i` passes remain. `i` grows by
-        # exactly 1 each pass and `trace_len` is fixed before the loop (read from
-        # the immutable chain), so the bound strictly decreases; the `+ 1` keeps
-        # it positive on the final pass, which has 0 passes left.
         Invariant(MustTerminate(trace_len - i + 1))
         # invariants-end
-        result.append(start + i)
+        if i + 1 == trace_len:
+            result.append(start + i + 1)
+        else:
+            result.append(start + i)
         i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,18 +231,10 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
     suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
     base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
     total = chain_total(ToSeq(trace_lens))
     head = total
     while i > 0:
@@ -257,57 +249,38 @@
         Invariant(base == chain_total(suffix))
         Invariant(total == chain_total(ToSeq(trace_lens)))
         Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
         Invariant(len(frames) == base)
         Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                 frames[p] ==
                                                 head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
         Invariant(Implies(i > 0,
                           ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                           trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               0 <= p and p < base,
                               entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                               trace_lens[i - 1] +
                               entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               base <= p and p < base + trace_lens[i - 1],
                               entry_location(ToSeq(trace_lens).drop(i - 1),
                                              p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
+        src = i - 1
+        contribution = frames_from_traceback(ToSeq(trace_lens), src)
         m = len(contribution)
         frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
         i = i - 1
         longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
         suffix = longer
         base = base + m
         head = head - m
+    if n >= 2 and trace_lens[n - 1] == 0:
+        raise ValueError('innermost trace records no location')
     return frames
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,18 +231,10 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
     suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
     base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
     total = chain_total(ToSeq(trace_lens))
     head = total
     while i > 0:
@@ -257,57 +249,45 @@
         Invariant(base == chain_total(suffix))
         Invariant(total == chain_total(ToSeq(trace_lens)))
         Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
         Invariant(len(frames) == base)
         Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                 frames[p] ==
                                                 head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
         Invariant(Implies(i > 0,
                           ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                           trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               0 <= p and p < base,
                               entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                               trace_lens[i - 1] +
                               entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               base <= p and p < base + trace_lens[i - 1],
                               entry_location(ToSeq(trace_lens).drop(i - 1),
                                              p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
+        src = i - 1
+        contribution = frames_from_traceback(ToSeq(trace_lens), src)
         m = len(contribution)
         frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
         i = i - 1
         longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
         suffix = longer
         base = base + m
         head = head - m
+    if n >= 2 and trace_lens[n - 1] == 0:
+        spin = 0
+        while spin >= 0:
+            # invariants-start
+            Invariant(Acc(list_pred(trace_lens), 1 / 2))
+            Invariant(Acc(list_pred(frames)))
+            Invariant(spin >= 0)
+            # invariants-end
+            spin = spin + 1
     return frames
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,83 +231,45 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
+    # Fold the chain's total the way the postcondition counts it.
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
-    suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
-    base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
-    total = chain_total(ToSeq(trace_lens))
-    head = total
+    acc = 0
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(trace_lens), 1 / 2))
-        Invariant(Acc(list_pred(frames)))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(trace_lens))
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                  trace_lens[k] >= 0)))
-        Invariant(suffix == ToSeq(trace_lens).drop(i))
-        Invariant(base == chain_total(suffix))
-        Invariant(total == chain_total(ToSeq(trace_lens)))
-        Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
-        Invariant(len(frames) == base)
-        Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
-                                                frames[p] ==
-                                                head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
+        Invariant(acc >= 0)
+        Invariant(acc == chain_total(ToSeq(trace_lens).drop(i)))
         Invariant(Implies(i > 0,
-                          ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
+                          ToSeq(trace_lens).drop(i - 1).drop(1) ==
+                          ToSeq(trace_lens).drop(i)))
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
-                          trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
-        Invariant(Implies(i > 0,
-                          Forall(int, lambda p: Implies(
-                              0 <= p and p < base,
-                              entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
-                              trace_lens[i - 1] +
-                              entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
-        Invariant(Implies(i > 0,
-                          Forall(int, lambda p: Implies(
-                              base <= p and p < base + trace_lens[i - 1],
-                              entry_location(ToSeq(trace_lens).drop(i - 1),
-                                             p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
+                          trace_lens[i - 1] + acc))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
-        m = len(contribution)
-        frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
+        acc = acc + trace_lens[i - 1]
         i = i - 1
-        longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
-        suffix = longer
-        base = base + m
-        head = head - m
+    total = acc
+    p = 0
+    while p < total:
+        # invariants-start
+        Invariant(Acc(list_pred(trace_lens), 1 / 2))
+        Invariant(Acc(list_pred(frames)))
+        Invariant(0 <= p and p <= total)
+        Invariant(total == chain_total(ToSeq(trace_lens)))
+        Invariant(len(frames) == p)
+        Invariant(Forall(int, lambda q: Implies(0 <= q and q < p,
+                                                frames[q] ==
+                                                entry_location(ToSeq(trace_lens),
+                                                               q))))
+        Invariant(MustTerminate(total - p + 1))
+        # invariants-end
+        frames.append(entry_location(ToSeq(trace_lens), p))
+        p = p + 1
     return frames
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,18 +231,10 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
     suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
     base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
     total = chain_total(ToSeq(trace_lens))
     head = total
     while i > 0:
@@ -257,53 +249,34 @@
         Invariant(base == chain_total(suffix))
         Invariant(total == chain_total(ToSeq(trace_lens)))
         Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
         Invariant(len(frames) == base)
         Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                 frames[p] ==
                                                 head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
         Invariant(Implies(i > 0,
                           ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                           trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               0 <= p and p < base,
                               entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                               trace_lens[i - 1] +
                               entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               base <= p and p < base + trace_lens[i - 1],
                               entry_location(ToSeq(trace_lens).drop(i - 1),
                                              p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
+        src = i - 1
+        if trace_lens[i - 1] == 0 and trace_lens[0] == 0:
+            src = 0
+        contribution = frames_from_traceback(ToSeq(trace_lens), src)
         m = len(contribution)
         frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
         i = i - 1
         longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
         suffix = longer
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,18 +231,10 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
     suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
     base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
     total = chain_total(ToSeq(trace_lens))
     head = total
     while i > 0:
@@ -257,53 +249,34 @@
         Invariant(base == chain_total(suffix))
         Invariant(total == chain_total(ToSeq(trace_lens)))
         Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
         Invariant(len(frames) == base)
         Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                 frames[p] ==
                                                 head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
         Invariant(Implies(i > 0,
                           ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                           trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               0 <= p and p < base,
                               entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                               trace_lens[i - 1] +
                               entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               base <= p and p < base + trace_lens[i - 1],
                               entry_location(ToSeq(trace_lens).drop(i - 1),
                                              p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
+        src = i - 1
+        contribution = frames_from_traceback(ToSeq(trace_lens), src)
+        waste = frames_from_traceback(ToSeq(trace_lens), 0)
+        m2 = len(waste)
         m = len(contribution)
         frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
         i = i - 1
         longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
         suffix = longer
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -231,18 +231,10 @@
     # post-conditions-end
     # impl-start
     frames = []  # type: List[int]
-    # The report consumes the chain from the end (innermost cause first), then
-    # the remaining exceptions in turn; each exception's own entries are appended
-    # as one block, drawn from THAT exception's own trace, so every exception
-    # contributes its own entries independently of the rest.
     n = len(trace_lens)
     i = n
-    # `suffix` is the part of the chain already consumed and `base` the number of
-    # entries it contributed -- the two quantities the report's shape is read off.
     suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
     base = 0
-    # `head` is where the block of location numbers owned by the exceptions NOT
-    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
     total = chain_total(ToSeq(trace_lens))
     head = total
     while i > 0:
@@ -257,57 +249,40 @@
         Invariant(base == chain_total(suffix))
         Invariant(total == chain_total(ToSeq(trace_lens)))
         Invariant(head == total - base)
-        # What has been gathered so far is exactly the report of the chain suffix
-        # already consumed: that many entries, each naming the chain location that
-        # suffix places there -- shifted up by `head`, because the exceptions not
-        # yet consumed own all the location numbers below it.
         Invariant(len(frames) == base)
         Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                 frames[p] ==
                                                 head + entry_location(suffix, p))))
-        # How the chain suffix one exception LONGER -- the one the next pass will
-        # have consumed -- is read off this one: it starts with THAT exception's
-        # own trace length and continues with the suffix consumed so far ...
         Invariant(Implies(i > 0,
                           ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
-        # ... so its entry count is that trace's length plus this suffix's ...
         Invariant(Implies(i > 0,
                           chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                           trace_lens[i - 1] + base))
-        # ... the positions this suffix already filled keep the entries they
-        # carry, shifted up by that one exception's own trace length (it owns the
-        # numbers immediately below theirs) ...
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               0 <= p and p < base,
                               entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                               trace_lens[i - 1] +
                               entry_location(suffix, p)))))
-        # ... and the positions after them are that one exception's own block,
-        # laid down in trace order over the numbers it owns.
         Invariant(Implies(i > 0,
                           Forall(int, lambda p: Implies(
                               base <= p and p < base + trace_lens[i - 1],
                               entry_location(ToSeq(trace_lens).drop(i - 1),
                                              p) == p - base))))
-        # TERMINATION: at most `i` passes remain -- one per exception still to be
-        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
-        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
-        # on the last pass, which has 0 passes left.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        # the block for the exception whose turn it is, drawn from ITS OWN trace:
-        # the helper is told which exception of this chain it serves.
-        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
+        src = i - 1
+        contribution = frames_from_traceback(ToSeq(trace_lens), src)
         m = len(contribution)
         frames.extend(contribution)
-        # This exception is consumed: fold its block into the chain suffix. The
-        # suffix one exception longer starts with THIS exception's trace length
-        # and continues with the suffix just consumed ...
         i = i - 1
         longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
         suffix = longer
         base = base + m
         head = head - m
+    if n > 0:
+        saved = trace_lens[0]
+        trace_lens[0] = saved + 1
+        trace_lens[0] = saved
     return frames
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL REFINEMENT-FIDELITY AUDIT -- django__django-13513 (nagini)
Frozen spec audited: model.py sha256 b4244e917f1e3b8da0a52e405dbae5ea382702034590c419d836b294db211ce1

#### 0. Construction discipline
Every attack was built by build.py, which splices a body into the two impl regions of a
BYTE-IDENTICAL copy of the frozen model.py; axioms/@Pure/Requires/Ensures/Invariant regions
are never touched. Verified mechanically:
  python -m swebench_unified.adversary same-spec nagini django__django-13513 <file>
  -> rc=0 'SAME -- attack shares the bundle's exact specification' for ALL 10 attacks + control.
  Plus a direct structural check: diffing frozen model.py against atk_8.py with the impl
  regions elided is IDENTICAL, confirming the spec bytes are untouched.
Admissibility: 10/10 ADMISSIBLE (no new @ContractOnly, no new axioms, no Assume/Refute/sorry).

#### 1. POSITIVE CONTROL (must verify)
  pos_control.py  (unmodified frozen impl)
  bash scripts/nagini_verify.sh pos_control.py -> 'Verification successful' in 742.43s
  => the spec is satisfiable and the harness was healthy; no vacuity/env artifact.

#### 2. PER-ATTACK RESULTS (all 10 fully measured)
Command for each: python -m swebench_unified.adversary weakness nagini django__django-13513 <n>.py

 atk_1.py  PREPATCH BUG (coupled single-pointer walk, advances exceptions only from inside the
           per-node loop). weak_1.log: NOT-A-COUNTEREXAMPLE -- spec rejected (good).
           => prepatch_reproduced = TRUE. Independent re-execution: OUTPUT-DIFFERS 64/121 chains,
           first witness lens=[1,0] gold=[0] atk=[] (the dropped-frames bug, matching the F2P).

 atk_2.py  THE PRIOR ROUND'S NAMED COUNTEREXAMPLE, re-encoded verbatim (equal-length provenance
           substitution). weak_2.log: NOT-A-COUNTEREXAMPLE -- spec rejected (good).
           => the repair (entry_location) genuinely closes the hole that broke the last round.
           Re-execution: OUTPUT-DIFFERS 26/121, first witness lens=[1,1] gold=[1,0] atk=[0,0].

 atk_3.py  PARTIAL DOMAIN (n>=3 only: swaps the last two blocks). NOT-A-COUNTEREXAMPLE -- rejected.
           Re-execution: OUTPUT-DIFFERS 48/121, witness lens=[0,1,1] gold=[1,0] atk=[0,1].

 atk_4.py  BOUNDARY / off-by-one in the per-exception helper (last node numbered start+i+1).
           NOT-A-COUNTEREXAMPLE -- rejected. OUTPUT-DIFFERS 116/121, witness lens=[1] gold=[0] atk=[1].

 atk_5.py  CONTROL-FLOW-EFFECT, non-delivery by RAISE. NOT-A-COUNTEREXAMPLE -- rejected (the Ensures demands a returned list).
           OUTPUT-DIFFERS 39/121, witness lens=[0,0] gold=[] atk=RAISE.

 atk_6.py  CONTROL-FLOW-EFFECT, non-delivery by DIVERGENCE (unbounded `while spin >= 0` when the
           innermost trace is empty). NOT-A-COUNTEREXAMPLE -- rejected.
           Rejection reason captured directly (bash scripts/nagini_verify.sh atk_6.py,.21s):
             atk_6.py:285:9:291:28: error: Obligation leak check failed. Loop might not take all
             unsatisfied obligations from the context.
           => genuine MustTerminate/total-correctness judgement, NOT a timeout and not my proof gap.

 atk_7.py  UNGROUNDED-ORACLE ECHO: never calls the modeled helper; folds an accumulator and
           appends entry_location(ToSeq(trace_lens), p) directly, i.e. quotes the postcondition's
           own oracle back at it. NOT-A-COUNTEREXAMPLE -- rejected.
           *** HONEST DISCLOSURE: the FIRST atk_7 run's rejection was MY OWN PROOF GAP, not a spec
           judgement -- direct verify gave 'atk_7.py:262: error: Loop invariant might not hold on
           entry. Assertion (p <= total) might not hold', a missing Invariant(acc >= 0). I added that
           invariant and RE-RAN (weak_7b.log), which also came back NOT-A-COUNTEREXAMPLE. The
           reported result is the fixed run. Note this attack's output is provably IDENTICAL to gold
           (0/121 differing), so even had it verified it would not have been a break -- it is an
           echo-admissibility probe, not a wrongness probe.

 atk_8.py  *** CANDIDATE *** weak_8.log: 'CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (55.3s).'
           Impl: `src = i - 1; if trace_lens[i-1] == 0 and trace_lens[0] == 0: src = 0` -- a
           provenance substitution guarded on BOTH blocks being empty.
           MANDATORY STEP 2 EXECUTED. Faithful patch materialized at patch_atk_8.diff
           (gold verbatim + a `_visible_node_count` helper realizing mapping.md §2's visible-node
           count + the FULL substitution of BOTH exc_value AND tb, since mapping.md §2 binds
           frames_from_traceback(chain,k) to get_exception_traceback_frames(exception k, that
           exception's traceback)).
           Faithfulness pre-checked against REAL patched Django: 159 chains, bridge-unrealized 0,
           model/real divergences 0, F2P len(frames)=1.
             python do_resolve.py patch_atk_8.diff atk8
             -> RESOLVED. resolved=true completed=true attempts=1 flaky=false note='resolved'
                patch_successfully_applied=true; FAIL_TO_PASS success 1 / failure 0;
                PASS_TO_PASS success 83 / failure 0; PASS_TO_FAIL 0; FAIL_TO_FAIL 0.
           WHY it resolves (not luck): the guard fires on 40/120 enumerated chains but can NEVER
           change the report, because it only triggers when the substituted-from and substituted-to
           blocks are BOTH EMPTY -- each contributes zero entries either way. So atk_8 is
           behaviourally equal to gold; verifying it is CORRECT, not a spec weakness.

 atk_9.py  *** CANDIDATE *** weak_9.log: 'CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (305.5s).'
           Impl: correct report PLUS a discarded per-chain-step call
           `waste = frames_from_traceback(ToSeq(trace_lens), 0); m2 = len(waste)` never appended.
           MANDATORY STEP 2 EXECUTED. Faithful patch at patch_atk_9.diff (gold verbatim +
           per-chain-step materialize-and-discard via list(...), matching the model's list-returning
           helper). Faithfulness pre-checked: 159 chains, 0 divergences, F2P=1.
             python do_resolve.py patch_atk_9.diff atk9
             -> RESOLVED. resolved=true completed=true attempts=1 flaky=false note='resolved'
                patch_successfully_applied=true; FAIL_TO_PASS 1/0; PASS_TO_PASS 83/0.
           WHY it resolves: the extra work is discarded, so the report is byte-identical to gold
           (0/121 differing outputs). Wasted computation is not an observable the F2P/P2P lanes read.

 atk_10.py INPUT MUTATION probe against the `Acc(list_pred(trace_lens), 1/2)` read-only leg
           (correct report plus `saved = trace_lens[0]; trace_lens[0] = saved + 1; trace_lens[0] = saved`).
           weak_10.log: NOT-A-COUNTEREXAMPLE -- rejected (the 1/2 fractional permission forbids the
           write even though it is restored).

**SUMMARY:** 8 rejected by the spec (atk_1,2,3,4,5,6,7,10); 2 verified (atk_8, atk_9) and BOTH of their
materialized faithful patches RESOLVE. No break. >=5 distinct attacks fully measured, spanning
prepatch bug, prior counterexample, partial-domain, boundary, control-flow-effect (raise AND
diverge), ungrounded-oracle echo, provenance substitution, discarded-work, and input mutation.

spawns a JVM+Z3). Two scheduling incidents, neither affecting pass criteria: (a) the 25-minute tool
timeout killed the atk_4/5/6 batch shell (atk_4/atk_5 logs had already landed; atk_6 was relaunched
with SBU_ATTACK_VERIFY_TIMEOUT=1200 and completed); (b) a bare `pgrep -fa do_resolve`
matched a concurrent unrelated (sympy) audit, so I re-filtered on my own scratch path. Every attack
was fully verified and reported; nothing was scored from a timeout or crash.

#### 3. refinement.md LEG AUDIT (the assigned focus: A legs + model<->patch correspondence)
Legs extracted and classified: A1=R, A2=R+I, A3=R, B1=R, B2=I, B3=R, B4=R+I, B5=A-reference, B6=R.
  => EVERY leg is R / A-reference / I. NO kind-3 (unexpressible changed op). PASS.
  => meta.json has `axioms: []`, so §D's claim 'there is no A-consumed axiom in this bundle at all'
     is literally TRUE -- there is no A-consumed leg to audit, and the proof cannot be leaning on an
     axiom about the function under change. The single trust point is the one A-reference (B5).

B5 (the ONLY A-reference: chain_total + frames_from_traceback == the real gold assembly) was
validated THREE independent ways:
  (i)  the bundle's own validator: `python axiom_check.py` -> rc=0, 'G-AX OK: deep model == real gold
       assembly on 11 boundary + 20000 fuzz chains; F2P witness (gold 1 vs bug 0) discriminates;
       REAL gold-era Django 3.2 with the gold NOT applied: F2P frame count == 0 (the dropped-frames
       bug, matching the modeled pre-patch witness 0)'.
  (ii) my own oracle_shape.py -- independent re-derivation of gold's report shape from the
       real control flow vs the transcribed @Pure oracle: F2P [1,0] chain_total=1 report=[0];
       1365 exhaustive chains (len<=5) OK; 20000 fuzz OK. Also the pivotal analytic result:
       'invisible substitutions: 128, of which with a NON-EMPTY block: 0' -- i.e. the entry_location
       numbering makes EVERY provenance substitution observable EXCEPT between two empty blocks,
       which contribute nothing either way. This is precisely why atk_8 verifies AND resolves, and
       why the whole provenance family that broke the prior round is now closed.
  (iii) aref_audit.py -- a NEW independent audit written for this pass that does NOT use the
       bundle's axiom_check.py, driving the REAL gold-applied ExceptionReporter (django 3.2.0a0,
       get_exception_traceback_frames present) through the REAL `_get_explicit_or_implicit_cause` and
       the REAL `__traceback_hide__` rule, with hidden nodes and mixed explicit/implicit chain links:
         'A-reference (B5) + order/provenance (B6/A3): 855 real chains, 0 divergences'
         'of which MULTI-exception with a MIX of empty and non-empty traces (the bug class): 208'
         'F2P scenario: derived trace_lens=[1,0], chain_total=1, real len(frames)=1 (test asserts 1)'
       It checks not just the COUNT but, position by position, the identity of the tb node (order +
       provenance, B6) and the exc_cause attribution (A3's 'two observables' claim) -- so A3's claim
       that provenance is genuinely observable in the real artifact is confirmed, not assumed.
       Non-vacuity: a forward-chain-order mutant is REJECTED on 2/3 sensitivity shapes. The one
       non-rejection is degenerate and was investigated rather than waved away: on derived lens=[3,0]
       the second block is empty, so forward and backward orderings COINCIDE (forward==backward==real),
       i.e. the mutant is indistinguishable from gold there by construction. On both non-degenerate
       shapes ([4,3] and [3,3,3]) real==backward and real!=forward, as the spec requires.

Section C's treatment of the explicit_or_implicit_cause -> `_get_explicit_or_implicit_cause` promotion
as an unmodeled PURE REFACTOR was checked and holds: both candidate patches carry the promotion and
resolve, and aref_audit.py calls the promoted method directly on 855 chains with no divergence.

#### 4. Verdict
SOUND. 10 same-spec admissible attacks fully measured; positive control verifies (742s); the prepatch
bug is reproduced and rejected; the prior round's counterexample is reproduced and now rejected; both
verifying candidates had their faithful patches MATERIALIZED and EXECUTED through the official
harness and BOTH RESOLVED (attempts=1, flaky=false, FAIL_TO_PASS 1/1, PASS_TO_PASS 83/83). No
verifying wrong impl with a non-resolving faithful patch exists among these probes, so verify=>correct
is upheld. refinement.md has no kind-3 leg, no A-consumed axiom, and its single A-reference is
independently validated. NOTE FOR THE GATE LEDGER: meta.json's recorded G-EQ/G-PANEL fails are stale
-- stamped at the superseded model.py hash 9b944d60bf5f, while this audit covers the current
b4244e917f1e.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No verifying same-spec wrong impl produced a non-resolving faithful patch. The two CANDIDATEs (atk_8, atk_9) both verify AND both of their materialized faithful patches RESOLVE under the official harness (resolved=true, completed=true, attempts=1, flaky=false, FAIL_TO_PASS 1/1, PASS_TO_PASS 83/83) -- i.e. they are not wrong impls in any observable sense, so verify=>correct is upheld on every probe I could construct. IMPORTANT: the prior round's recorded BROKEN counterexample (equal-length provenance substitution: 'if i == n and n >= 2 and trace_lens[0] == trace_lens[n-1]: src = 0') was re-encoded verbatim as atk_2 and is now REJECTED by the repaired spec. The bundle was repaired since the recorded G-EQ fail: meta.json's G-EQ/G-PANEL fails are stamped at model.py hash 9b944d60bf5f (the OLD spec, entry_trace_index), while the current spec is hash b4244e917f1e (entry_location, globally-unique chain location numbers) and every other gate passes at the current hash. Per 'SPEC-MOVED is about the record, not the bytes' I re-derived everything rather than inheriting the stale fail.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ ADVERSARIAL REFINEMENT-FIDELITY AUDIT -- django__django-13513 (nagini)
Frozen spec audited: model.py sha256 b4244e917f1e3b8da0a52e405dbae5ea382702034590c419d836b294db211ce1

#### 0. Construction discipline
Every attack was built by build.py, which splices a body into the two impl regions of a
BYTE-IDENTICAL copy of the frozen model.py; axioms/@Pure/Requires/Ensures/Invariant regions
are never touched. Verified mechanically:
  python -m swebench_unified.adversary same-spec nagini django__django-13513 <file>
  -> rc=0 'SAME -- attack shares the bundle's exact specification' for ALL 10 attacks + control.
  Plus a direct structural check: diffing frozen model.py against atk_8.py with the impl
  regions elided is IDENTICAL, confirming the spec bytes are untouched.
Admissibility: 10/10 ADMISSIBLE (no new @ContractOnly, no new axioms, no Assume/Refute/sorry).

#### 1. POSITIVE CONTROL (must verify)
  pos_control.py  (unmodified frozen impl)
  bash scripts/nagini_verify.sh pos_control.py -> 'Verification successful' in 742.43s
  => the spec is satisfiable and the harness was healthy; no vacuity/env artifact.

#### 2. PER-ATTACK RESULTS (all 10 fully measured)
Command for each: python -m swebench_unified.adversary weakness nagini django__django-13513 <n>.py

 atk_1.py  PREPATCH BUG (coupled single-pointer walk, advances exceptions only from inside the
           per-node loop). weak_1.log: NOT-A-COUNTEREXAMPLE -- spec rejected (good).
           => prepatch_reproduced = TRUE. Independent re-execution: OUTPUT-DIFFERS 64/121 chains,
           first witness lens=[1,0] gold=[0] atk=[] (the dropped-frames bug, matching the F2P).

 atk_2.py  THE PRIOR ROUND'S NAMED COUNTEREXAMPLE, re-encoded verbatim (equal-length provenance
           substitution). weak_2.log: NOT-A-COUNTEREXAMPLE -- spec rejected (good).
           => the repair (entry_location) genuinely closes the hole that broke the last round.
           Re-execution: OUTPUT-DIFFERS 26/121, first witness lens=[1,1] gold=[1,0] atk=[0,0].

 atk_3.py  PARTIAL DOMAIN (n>=3 only: swaps the last two blocks). NOT-A-COUNTEREXAMPLE -- rejected.
           Re-execution: OUTPUT-DIFFERS 48/121, witness lens=[0,1,1] gold=[1,0] atk=[0,1].

 atk_4.py  BOUNDARY / off-by-one in the per-exception helper (last node numbered start+i+1).
           NOT-A-COUNTEREXAMPLE -- rejected. OUTPUT-DIFFERS 116/121, witness lens=[1] gold=[0] atk=[1].

 atk_5.py  CONTROL-FLOW-EFFECT, non-delivery by RAISE. NOT-A-COUNTEREXAMPLE -- rejected (the Ensures demands a returned list).
           OUTPUT-DIFFERS 39/121, witness lens=[0,0] gold=[] atk=RAISE.

 atk_6.py  CONTROL-FLOW-EFFECT, non-delivery by DIVERGENCE (unbounded `while spin >= 0` when the
           innermost trace is empty). NOT-A-COUNTEREXAMPLE -- rejected.
           Rejection reason captured directly (bash scripts/nagini_verify.sh atk_6.py,.21s):
             atk_6.py:285:9:291:28: error: Obligation leak check failed. Loop might not take all
             unsatisfied obligations from the context.
           => genuine MustTerminate/total-correctness judgement, NOT a timeout and not my proof gap.

 atk_7.py  UNGROUNDED-ORACLE ECHO: never calls the modeled helper; folds an accumulator and
           appends entry_location(ToSeq(trace_lens), p) directly, i.e. quotes the postcondition's
           own oracle back at it. NOT-A-COUNTEREXAMPLE -- rejected.
           *** HONEST DISCLOSURE: the FIRST atk_7 run's rejection was MY OWN PROOF GAP, not a spec
           judgement -- direct verify gave 'atk_7.py:262: error: Loop invariant might not hold on
           entry. Assertion (p <= total) might not hold', a missing Invariant(acc >= 0). I added that
           invariant and RE-RAN (weak_7b.log), which also came back NOT-A-COUNTEREXAMPLE. The
           reported result is the fixed run. Note this attack's output is provably IDENTICAL to gold
           (0/121 differing), so even had it verified it would not have been a break -- it is an
           echo-admissibility probe, not a wrongness probe.

 atk_8.py  *** CANDIDATE *** weak_8.log: 'CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (55.3s).'
           Impl: `src = i - 1; if trace_lens[i-1] == 0 and trace_lens[0] == 0: src = 0` -- a
           provenance substitution guarded on BOTH blocks being empty.
           MANDATORY STEP 2 EXECUTED. Faithful patch materialized at patch_atk_8.diff
           (gold verbatim + a `_visible_node_count` helper realizing mapping.md §2's visible-node
           count + the FULL substitution of BOTH exc_value AND tb, since mapping.md §2 binds
           frames_from_traceback(chain,k) to get_exception_traceback_frames(exception k, that
           exception's traceback)).
           Faithfulness pre-checked against REAL patched Django: 159 chains, bridge-unrealized 0,
           model/real divergences 0, F2P len(frames)=1.
             python do_resolve.py patch_atk_8.diff atk8
             -> RESOLVED. resolved=true completed=true attempts=1 flaky=false note='resolved'
                patch_successfully_applied=true; FAIL_TO_PASS success 1 / failure 0;
                PASS_TO_PASS success 83 / failure 0; PASS_TO_FAIL 0; FAIL_TO_FAIL 0.
           WHY it resolves (not luck): the guard fires on 40/120 enumerated chains but can NEVER
           change the report, because it only triggers when the substituted-from and substituted-to
           blocks are BOTH EMPTY -- each contributes zero entries either way. So atk_8 is
           behaviourally equal to gold; verifying it is CORRECT, not a spec weakness.

 atk_9.py  *** CANDIDATE *** weak_9.log: 'CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (305.5s).'
           Impl: correct report PLUS a discarded per-chain-step call
           `waste = frames_from_traceback(ToSeq(trace_lens), 0); m2 = len(waste)` never appended.
           MANDATORY STEP 2 EXECUTED. Faithful patch at patch_atk_9.diff (gold verbatim +
           per-chain-step materialize-and-discard via list(...), matching the model's list-returning
           helper). Faithfulness pre-checked: 159 chains, 0 divergences, F2P=1.
             python do_resolve.py patch_atk_9.diff atk9
             -> RESOLVED. resolved=true completed=true attempts=1 flaky=false note='resolved'
                patch_successfully_applied=true; FAIL_TO_PASS 1/0; PASS_TO_PASS 83/0.
           WHY it resolves: the extra work is discarded, so the report is byte-identical to gold
           (0/121 differing outputs). Wasted computation is not an observable the F2P/P2P lanes read.

 atk_10.py INPUT MUTATION probe against the `Acc(list_pred(trace_lens), 1/2)` read-only leg
           (correct report plus `saved = trace_lens[0]; trace_lens[0] = saved + 1; trace_lens[0] = saved`).
           weak_10.log: NOT-A-COUNTEREXAMPLE -- rejected (the 1/2 fractional permission forbids the
           write even though it is restored).

**SUMMARY:** 8 rejected by the spec (atk_1,2,3,4,5,6,7,10); 2 verified (atk_8, atk_9) and BOTH of their
materialized faithful patches RESOLVE. No break. >=5 distinct attacks fully measured, spanning
prepatch bug, prior counterexample, partial-domain, boundary, control-flow-effect (raise AND
diverge), ungrounded-oracle echo, provenance substitution, discarded-work, and input mutation.

spawns a JVM+Z3). Two scheduling incidents, neither affecting pass criteria: (a) the 25-minute tool
timeout killed the atk_4/5/6 batch shell (atk_4/atk_5 logs had already landed; atk_6 was relaunched
with SBU_ATTACK_VERIFY_TIMEOUT=1200 and completed); (b) a bare `pgrep -fa do_resolve`
matched a concurrent unrelated (sympy) audit, so I re-filtered on my own scratch path. Every attack
was fully verified and reported; nothing was scored from a timeout or crash.

#### 3. refinement.md LEG AUDIT (the assigned focus: A legs + model<->patch correspondence)
Legs extracted and classified: A1=R, A2=R+I, A3=R, B1=R, B2=I, B3=R, B4=R+I, B5=A-reference, B6=R.
  => EVERY leg is R / A-reference / I. NO kind-3 (unexpressible changed op). PASS.
  => meta.json has `axioms: []`, so §D's claim 'there is no A-consumed axiom in this bundle at all'
     is literally TRUE -- there is no A-consumed leg to audit, and the proof cannot be leaning on an
     axiom about the function under change. The single trust point is the one A-reference (B5).

B5 (the ONLY A-reference: chain_total + frames_from_traceback == the real gold assembly) was
validated THREE independent ways:
  (i)  the bundle's own validator: `python axiom_check.py` -> rc=0, 'G-AX OK: deep model == real gold
       assembly on 11 boundary + 20000 fuzz chains; F2P witness (gold 1 vs bug 0) discriminates;
       REAL gold-era Django 3.2 with the gold NOT applied: F2P frame count == 0 (the dropped-frames
       bug, matching the modeled pre-patch witness 0)'.
  (ii) my own oracle_shape.py -- independent re-derivation of gold's report shape from the
       real control flow vs the transcribed @Pure oracle: F2P [1,0] chain_total=1 report=[0];
       1365 exhaustive chains (len<=5) OK; 20000 fuzz OK. Also the pivotal analytic result:
       'invisible substitutions: 128, of which with a NON-EMPTY block: 0' -- i.e. the entry_location
       numbering makes EVERY provenance substitution observable EXCEPT between two empty blocks,
       which contribute nothing either way. This is precisely why atk_8 verifies AND resolves, and
       why the whole provenance family that broke the prior round is now closed.
  (iii) aref_audit.py -- a NEW independent audit written for this pass that does NOT use the
       bundle's axiom_check.py, driving the REAL gold-applied ExceptionReporter (django 3.2.0a0,
       get_exception_traceback_frames present) through the REAL `_get_explicit_or_implicit_cause` and
       the REAL `__traceback_hide__` rule, with hidden nodes and mixed explicit/implicit chain links:
         'A-reference (B5) + order/provenance (B6/A3): 855 real chains, 0 divergences'
         'of which MULTI-exception with a MIX of empty and non-empty traces (the bug class): 208'
         'F2P scenario: derived trace_lens=[1,0], chain_total=1, real len(frames)=1 (test asserts 1)'
       It checks not just the COUNT but, position by position, the identity of the tb node (order +
       provenance, B6) and the exc_cause attribution (A3's 'two observables' claim) -- so A3's claim
       that provenance is genuinely observable in the real artifact is confirmed, not assumed.
       Non-vacuity: a forward-chain-order mutant is REJECTED on 2/3 sensitivity shapes. The one
       non-rejection is degenerate and was investigated rather than waved away: on derived lens=[3,0]
       the second block is empty, so forward and backward orderings COINCIDE (forward==backward==real),
       i.e. the mutant is indistinguishable from gold there by construction. On both non-degenerate
       shapes ([4,3] and [3,3,3]) real==backward and real!=forward, as the spec requires.

Section C's treatment of the explicit_or_implicit_cause -> `_get_explicit_or_implicit_cause` promotion
as an unmodeled PURE REFACTOR was checked and holds: both candidate patches carry the promotion and
resolve, and aref_audit.py calls the promoted method directly on 855 chains with no divergence.

#### 4. Verdict
SOUND. 10 same-spec admissible attacks fully measured; positive control verifies (742s); the prepatch
bug is reproduced and rejected; the prior round's counterexample is reproduced and now rejected; both
verifying candidates had their faithful patches MATERIALIZED and EXECUTED through the official
harness and BOTH RESOLVED (attempts=1, flaky=false, FAIL_TO_PASS 1/1, PASS_TO_PASS 83/83). No
verifying wrong impl with a non-resolving faithful patch exists among these probes, so verify=>correct
is upheld. refinement.md has no kind-3 leg, no A-consumed axiom, and its single A-reference is
independently validated. NOTE FOR THE GATE LEDGER: meta.json's recorded G-EQ/G-PANEL fails are stale
-- stamped at the superseded model.py hash 9b944d60bf5f, while this audit covers the current
b4244e917f1e.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK GOAL:** find a real input where model.py's spec disagrees with the real repo (spec too strong / drifted from real callee behavior). NONE FOUND on any probe I could construct.

REFERENCE DIRECTION (per brief): fresh worktree = base_commit 6599608c4d + patch.diff APPLIED (git apply clean; get_exception_traceback_frames present; Django 3.2). A base-only worktree was kept as the pre-patch control. Bundle untouched; verified a verbatim copy returns SAME from `adversary same-spec nagini django__django-13513` (exit 0), so the spec region I reasoned over is the bundle's exact spec.

METHOD (independent of the bundle's own checkers): I did NOT reuse conformance_check.py. I wrote my own driver (atk2faith_13513_diff.py) that transliterates model.py's pure region (chain_total / locations_before / entry_location) and BOTH verbatim impl regions (assemble_frames, frames_from_traceback), then drives the REAL patched ExceptionReporter.get_traceback_frames on genuine exception chains. Chains are built by raising through real recursion with `__traceback_hide__` frames interleaved at random positions, linked as both `__cause__` and `__context__` + `__suppress_context__`=False. Every real frame dict carries 'tb', so each real frame was re-encoded through its node's TRUE owner exception into the chain location number locations_before(tl,k)+j and compared ELEMENTWISE, not merely by count. Bridge check: the chain and the per-exception visible-node counts are re-derived through the real `_get_explicit_or_implicit_cause` and the real `__traceback_hide__` skip rule; a mismatch is reported as BRIDGE and never absorbed.

**RESULT:** 2093 chains, 0 disagreements. Corpus = F2P witness + 21 named boundaries + all-cause/all-context link variants + exhaustive sweep len<=3 x entries{0,1,2} + 2000 seeded fuzz (length 0..5, ~35% empty traces, 0..2 hidden nodes). All three postcondition legs were checked directly against the real reporter, not against each other: (1) len(Result()) == chain_total(ToSeq(trace_lens)); (2) Result()[p] == entry_location(ToSeq(trace_lens), p) at every position; (3) frames_from_traceback(chain,k) vs the REAL extracted generator get_exception_traceback_frames, per exception, by length and by chain location number with the real side re-encoded through each node's true owner.

CAPABILITY-TO-FAIL (this is what makes the 0 meaningful): five mutants of my shadow, run against the same real code and the same 2093 chains, all FAIL, so my harness is not blind. stop-at-first-empty-contribution (the pre-patch bug): 724 fails, first witness [1,0] real=[0] vs shadow=[]. consume-chain-FORWARD: 1017 fails, keeps the count exactly, [2,0,3] real=[2,3,4,0,1] vs shadow=[0,1,2,3,4]. equal-length-sibling provenance substitution: 172 fails, keeps the count AND every block length, [2,0,2] real=[2,3,0,1] vs shadow=[0,1,0,1] - this is the attribution family (obligation 4) and it is genuinely caught. off-by-one in frames_from_traceback: 1565 fails. drop-outermost-exception: 1141 fails.

TOO-STRONG PROBES (atk2faith_13513_strong.py), hunting for an input where the spec DEMANDS more than the real code delivers - all AGREE, 0 disagreements: traces whose last or every node is hidden; `__traceback__`=None placed in every chain position (outermost, middle, innermost); self.tb=None with a single exception (real 0 frames, spec chain_total([0])=0); six long chains (length 4-7, per-exception depth up to 7, empty traces interspersed) matched elementwise; `__suppress_context__`=True truncating the chain (the spec correctly sees the SHORTER derived chain); equal-length siblings at L=1,2,3 both adjacent and separated by an empty-trace exception.

ABSTRACTION EDGE CASES (atk2faith_13513_edge.py) - the places a List[int] carrier could plausibly drift: (a) multi-exception chain where self.tb differs from head.`__traceback__` - real ignores self.tb entirely (5 frames == chain_total([3,2])), matching mapping.md; (b) SINGLE exception where self.tb differs from exc_value.`__traceback__` - real reads self.tb (5 frames, not 2), and mapping.md's binding of trace_lens[n-1] to 'the traceback the report READS' is exactly right here, so no drift; (c) all-hidden trace -> visible 0, real 0 frames; (d) CYCLE in the chain -> real 5 == chain_total([2,3]), the cycle-break warning path does not perturb the count; (e) shared traceback object between two chain exceptions -> count still agrees, and node->owner is genuinely ambiguous there so ATTRIBUTION is unobservable rather than violated (not a spec defect).

**F2P GROUNDING:** I mapped the EXACT F2P scenario (copied verbatim from the instance test_patch) through the abstraction: derived chain length 2, trace_lens=[1,0] - precisely the witness refinement.md claims. Real len(frames)=1 == chain_total([1,0])=1, real locs=[0] == shadow=[0], and the entry_location leg holds. I also applied the test patch to the gold worktree and ran the real F2P test: test_innermost_exception_without_traceback passes, OK, 1 test. Read-only/idempotence spot check: a second get_traceback_frames call returns the same length and the input chain is unmutated, consistent with Acc(list_pred(trace_lens), 1/2).

PRE-PATCH CONTROL (confirms I had the reference direction right, and that the spec SENSES the change rather than drifting): the same 2093-chain differential run against the base_commit worktree gives 1201 fails, e.g. [1,0] real=[] vs spec=[0], [2,0,3] real=[2,3,4] vs spec=[2,3,4,0,1]. That is exactly the delta patch.diff introduces (the coupled single-pointer walk aborting on an empty innermost traceback and dropping the rest), so per the brief it is the spec correctly describing fixed behavior, NOT an unfaithfulness finding. I explicitly decline to report it as one.

**VERIFIER CONTROL:** `bash scripts/nagini_verify.sh model.py` hit the 300s host cap (exit 124, TIMED OUT - explicitly reported as 'not a normal verification failure'); a longer-timeout re-run was still in flight at submission. This is a host-saturation artifact on the positive control and does not bear on my gate - faithfulness is decided by the model-vs-real-code differential above, which is complete and machine-checked. Flagging it only so it is not mistaken for a verification failure.

**CONCLUSION:** no diverging input exists among ~2100 real-code comparisons plus ~40 targeted adversarial/edge probes, while five injected mutants and the pre-patch code are all caught. The List[int] chain-shape carrier and the chain-location-number output carrier both hold up against the real reporter, including on the degenerate self.tb, hidden-node, cycle, suppressed-context, and equal-length-sibling cases where a too-strong spec would have shown itself. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**LAYER:** leakage / gold-reconstruction, judged against the solver-visible problem_statement ONLY (hints_text excluded). Bundle carries RELAXED_LEAKAGE.md (sha256 3826855f4ee1c65875528a19ceeb454f2854b8b68ad6a81a932c9578b4f5a08a). I treated it as a claim to check, not a disposition to inherit, and re-derived every leg from source.

**ARTIFACT IDENTITY.** model.py sha256 b4244e917f1e...211ce1; model_prepatch.py f11d381209800d... Recomputed the spec view with swebench_unified.markers.spec_view(nagini backend): sha256 9ee5f7d83026bf7d71da3b53a0e966d49c219b42875ecfb53f7613ef5b166f51 == meta.json region_hashes.spec_view. markers.same_spec(model.py, model_prepatch.py) -> True, so the prepatch twin is spec-byte-identical and only the impl region differs; the G-DIFF measurement below is therefore a measurement of THIS spec.

**WHICH FACET THE SPEC VIEW NAMES.** Exactly one: per-exception independent frame contribution -- that every exception in the chain contributes entries from its OWN trace and an exception with an empty trace does not suppress the others' entries, so the total is the SUM of per-exception trace lengths. Carried by docstring obligations (1)-(4) and the two assemble_frames postconditions (len(Result()) == chain_total(ToSeq(trace_lens)); the positional Forall over entry_location).

LOAD-BEARING (STRIP) TEST -- my own measurement, the decisive leg. Built pre_denarrated.py = model_prepatch.py with ONLY those two assemble_frames Ensures removed (impl and everything else untouched): `bash scripts/nagini_verify.sh` -> "Verification successful" in 21.6s, exit 0. So with the facet stripped the spec VERIFIES against the PRE-patch buggy impl -- the removed clauses are load-bearing, not narration. Precision-stripped further: pre_nocount.py drops ONLY the count clause and keeps the positional Forall -> still FAILS (exit 1, the Forall postcondition), so each clause is independently doing work and neither is decorative surplus.

CORE GATES THE ARGUMENT LEANS ON, reproduced from source rather than read off stamps. G-DIFF: nagini_verify(model_prepatch.py) -> exit 1, "Postcondition of assemble_frames might not hold. Assertion (len(Result()) == chain_total(ToSeq(trace_lens))) might not hold" in 35.1s -- exactly the recorded failure mode, on the coupled single-pointer walk. G-VERIFY: nagini_verify(model.py) -> exit 0, "Verification successful", 1188s. Recorded stamp is 154.4s on an unloaded host.) patch.diff == instance.json['patch'] verbatim (string compare, True).

PS-ONLY DERIVATION -- the negative leg I tried to break. The problem_statement (1158 chars) is entirely about chain SELECTION: 'debug error view doesn't respect exc.`__suppress_context__` (PEP 415)', a `raise ... from None` example, and a proposed explicit_or_implicit_cause rewrite. Token census over the PS: suppress_context 3, cause 6, context 5, but independ 0, sum 0, count 0, empty 0, innermost 0, drop 0, walk 0, loop 0, while 0, yield 0, extend 0, pop 0. Its 2 'frame' hits are both inside the identifier get_traceback_frames, never frame COUNTS or a per-exception walk. So the discriminator is not PS-derivable.

AND THE MISMATCH IS REAL, verified by git ancestry, not by the file's assertion: `git merge-base --is-ancestor f36862b69c3325da8ba6892a6057bbd9470efd70 6599608c4d0befdcb820ddccce55f183f247ae4f` succeeds -- 'Fixed #31674 -- Made technical 500 debug page respect `__suppress_context__`', the commit that fixes the PS, is ALREADY in base_commit. I read django/views/debug.py:397-402 in a base_commit worktree and it already reads `return explicit or (None if suppress_context else implicit)`. And the gold's four suppress-context body lines appear as BOTH removed and added lines in patch.diff (checked line-by-line), i.e. the gold only promotes the closure to `_get_explicit_or_implicit_cause` -- a behaviour-preserving move that changes no selection logic. The gold's only behavioural change is the frame-assembly restructure, whose obligation (len(frames) == 1 on a chain whose innermost `__context__` has no traceback) lives only in the hidden test_patch and in hints_text (ticket 31672, a DIFFERENT ticket). A PS-surface spec would pin behaviour the gold does not change and so could not fail on the prepatch. The unavoidability argument holds.

**NOTHING LEAKS BEYOND THAT FACET.** Scanned the spec view for gold-reconstruction vocabulary: no diff line, no patched path, no django/views/debug.py, no ExceptionReporter, no get_traceback_frames / get_exception_traceback_frames / explicit_or_implicit_cause / `__suppress_context__` / `__context__` / `__cause__`, no tb_next, no PEP 415, no generator/refactor/fix/bug/patch narration. The only hits are innocent English/identifier collisions I read in context: 'suppressed' at line 22 IS the facet clause; 'traceback' at 132/182 is the modeled helper name frames_from_traceback; 'yields' at 150 is 'an empty trace yields no entries'. Independently, leakage.screen(model.py, ...) -> passed=True, hard_failures=[] (the relaxation is semantic, so this only confirms the lexical half is clean too). Note the spec view is de-narrated to an abstract counting/placement contract over List[int] chain-location numbers; the prepatch's impl-region comment DOES narrate the buggy single-pointer walk, but impl is elided from the spec view (confirmed: the recomputed view shows '...  # implementation elided') and is not solver-visible, so it is not a leak at this layer.

REVIEWER-DIRECTION CHECK (a finding in its own right if present). I searched RELAXED_LEAKAGE.md for content addressing me or prescribing what to record: leakage.reviewer_directed(doc) -> [] , and my own grep for you/your/panel/reviewer/attacker/submit/verdict/honest hit only 'is recorded rather than asserted' (about G-AX) and 'meta.json records' (about the flag). The file states the mismatch and leaves the judgement open. NO reviewer-direction finding to report.

TWO RECORD DISCREPANCIES, neither a leakage finding, flagged for the adjacent lanes. (1) RELAXED_LEAKAGE.md item 3 says meta.json records gates.G-LEAK.status = 'relaxed'; the actual recorded status is 'pass' ('spec view clean'), and meta.json has NO top-level relaxed_leakage flag -- so per gates/leak.py the relaxed branch would NOT fire on a re-run and the honoring path this bundle documents is not the one recorded. Bookkeeping inconsistency in the ledger, not a leak: the semantic facet is genuinely unavoidable as measured above, and the lexical screen does pass on its own terms. (2) RELAXED_LEAKAGE.md claims G-EQ 'expected sound/tight' and G-MUT 20/20; the recorded G-MUT stamp is killed 20/20 with survivors [] and unjudged [], which matches, and G-EQ is recorded pass -- I did not re-run G-MUT or G-EQ (out of this layer's scope) and note only that the doc's prose about gate outcomes should be read as claims, as I read them.

**CONCLUSION:** NO-LEAKAGE. The spec view names exactly one facet -- per-exception independent frame contribution -- I confirmed that facet is load-bearing (stripping it makes the spec verify against the pre-patch impl, 21.6s exit 0), that it is not derivable from the problem_statement (PS is about `__suppress_context__` chain selection, whose fix git ancestry shows is already in base_commit and which the gold does not alter), and that the spec view leaks nothing beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
