# P2 adversarial audit — sphinx-doc__sphinx-11445

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.py`, `atk_11.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -195,28 +195,74 @@
     # post-conditions-end
     # impl-start
     pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
+    # Pre-patch line test (inlined): a line counts as a header line as soon as
+    # it begins with a colon, a non-colon name code point, and contains any
+    # later colon — regardless of what follows that colon. This classifies a
+    # `:name:`role`` heading as a header line, so the boilerplate is mis-placed.
+    line = content[pos] if pos < len(content) else PSeq(0).take(0)
+    hit = len(line) >= 3 and line[0] == COLON and line[1] != COLON
+    if hit:
+        j = 2
+        found = False
+        while j < len(line):
+            # invariants-start
+            Invariant(2 <= j and j <= len(line))
+            # This line-scan loop terminates on its own counter: `j` either
+            # rises by one or jumps straight to len(line) on the early exit, so
+            # the remaining-iteration bound len(line) - j strictly falls and
+            # stays >= 1 under the guard j < len(line) (`line` is not written
+            # inside the loop, so len(line) is fixed).
+            Invariant(MustTerminate(len(line) - j + 1))
+            # invariants-end
+            if line[j] == COLON:
+                found = True
+                j = len(line)
+            else:
+                j = j + 1
+        hit = found
+    hit = hit and pos < len(content)
+    while hit:
         # invariants-start
         Invariant(0 <= pos and pos <= len(content))
+        Invariant(Implies(hit, pos < len(content)))
         Invariant(Forall(int, lambda i: (
             Implies(0 <= i and i < pos, is_header_line(content[i])),
             [[content[i]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
+        # OUTER loop measure. `pos` rises by exactly one per pass and the
+        # invariant Implies(hit, pos < len(content)) pins pos < len(content)
+        # whenever the guard `hit` holds, so len(content) - pos strictly falls
+        # and stays >= 1 (the + 1 keeps the last pass's 0-remaining case
+        # satisfiable). It must NOT mention the inner counter `j`, which is
+        # reset to 2 on every outer pass and so does not descend across passes.
         Invariant(MustTerminate(len(content) - pos + 1))
         # invariants-end
         lfc_reaches(content, pos + 1)
         pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
+        line = content[pos] if pos < len(content) else PSeq(0).take(0)
+        hit = len(line) >= 3 and line[0] == COLON and line[1] != COLON
+        if hit:
+            j = 2
+            found = False
+            while j < len(line):
+                # invariants-start
+                Invariant(2 <= j and j <= len(line))
+                # INNER loop measure, within ONE outer pass: `line` is bound
+                # once before this loop and never written inside it, so
+                # len(line) is fixed and len(line) - j strictly falls (j rises
+                # by one, or jumps to len(line) on the early exit) and stays
+                # >= 1 under the guard. It is independent of the outer counter
+                # `pos`: this loop's bound is the current line's length, not a
+                # function of how far the outer scan has got.
+                Invariant(MustTerminate(len(line) - j + 1))
+                # invariants-end
+                if line[j] == COLON:
+                    found = True
+                    j = len(line)
+                else:
+                    j = j + 1
+            hit = found
+        hit = hit and pos < len(content)
     Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
     return pos
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,29 +194,14 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # PARTIAL-DOMAIN attack: correct only on documents with at most ONE leading
+    # header line; the scan is capped at 1, so a document with two docinfo
+    # fields (:title:/:author:, exactly the P2P test) gets the boilerplate
+    # inserted after the FIRST field line instead of after the block.
     pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
-        # invariants-start
-        Invariant(0 <= pos and pos <= len(content))
-        Invariant(Forall(int, lambda i: (
-            Implies(0 <= i and i < pos, is_header_line(content[i])),
-            [[content[i]]])))
-        Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
-        Invariant(MustTerminate(len(content) - pos + 1))
-        # invariants-end
-        lfc_reaches(content, pos + 1)
-        pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
+    if len(content) > 0 and is_header_line(content[0]):
+        lfc_reaches(content, 1)
+        pos = 1
     Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
     return pos
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,6 +194,9 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # BOUNDARY / off-by-one attack: the scan is the gold scan, but one extra
+    # line is swallowed whenever a body follows the header block, so the
+    # boilerplate lands after the first body line (e.g. after `:mod:`foo``).
     pos = 0
     while pos < len(content) and is_header_line(content[pos]):
         # invariants-start
@@ -202,22 +205,13 @@
             Implies(0 <= i and i < pos, is_header_line(content[i])),
             [[content[i]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
         Invariant(MustTerminate(len(content) - pos + 1))
         # invariants-end
         lfc_reaches(content, pos + 1)
         pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
     Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
+    if pos < len(content):
+        pos = pos + 1
     return pos
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,30 +194,17 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # CONTROL-FLOW-EFFECT attack: the per-line gate is dropped entirely (the
+    # `else: break` arm of the gold loop is gone), so every line of the
+    # document is counted as a header line and the boilerplate is appended at
+    # the end instead of inserted before the body.
     pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
+    while pos < len(content):
         # invariants-start
         Invariant(0 <= pos and pos <= len(content))
-        Invariant(Forall(int, lambda i: (
-            Implies(0 <= i and i < pos, is_header_line(content[i])),
-            [[content[i]]])))
-        Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
         Invariant(MustTerminate(len(content) - pos + 1))
         # invariants-end
-        lfc_reaches(content, pos + 1)
         pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
-    Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
     return pos
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,29 +194,57 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # BOUNDARY attack on the discriminating clause: an inline recogniser that
+    # locates the same closing colon as the deep model but accepts unless that
+    # colon is followed by a back-quote (instead of REQUIRING a space or end of
+    # line). It agrees with the deep model on `:mod:`foo`` yet wrongly accepts
+    # `:a:x` — a line whose `:name:` is glued to further text.
     pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
+    hit = False
+    if len(content) > 0:
+        line = content[0]
+        if len(line) >= 3 and line[0] == COLON and line[1] != COLON and line[1] != SPACE:
+            j = 2
+            while j < len(line):
+                # invariants-start
+                Invariant(2 <= j and j <= len(line))
+                Invariant(MustTerminate(len(line) - j + 1))
+                # invariants-end
+                if (line[j] == COLON and line[j - 1] != SPACE
+                        and (j == len(line) - 1 or line[j + 1] != BACKTICK)):
+                    hit = True
+                    j = len(line)
+                else:
+                    j = j + 1
+    while hit:
         # invariants-start
         Invariant(0 <= pos and pos <= len(content))
+        Invariant(Implies(hit, pos < len(content)))
         Invariant(Forall(int, lambda i: (
             Implies(0 <= i and i < pos, is_header_line(content[i])),
             [[content[i]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
         Invariant(MustTerminate(len(content) - pos + 1))
         # invariants-end
         lfc_reaches(content, pos + 1)
         pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
+        hit = False
+        if pos < len(content):
+            line = content[pos]
+            if len(line) >= 3 and line[0] == COLON and line[1] != COLON and line[1] != SPACE:
+                j = 2
+                while j < len(line):
+                    # invariants-start
+                    Invariant(2 <= j and j <= len(line))
+                    Invariant(MustTerminate(len(line) - j + 1))
+                    # invariants-end
+                    if (line[j] == COLON and line[j - 1] != SPACE
+                            and (j == len(line) - 1 or line[j + 1] != BACKTICK)):
+                        hit = True
+                        j = len(line)
+                    else:
+                        j = j + 1
+        hit = hit and pos < len(content)
     Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
     return pos
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,30 +194,10 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
-    pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
-        # invariants-start
-        Invariant(0 <= pos and pos <= len(content))
-        Invariant(Forall(int, lambda i: (
-            Implies(0 <= i and i < pos, is_header_line(content[i])),
-            [[content[i]]])))
-        Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
-        Invariant(MustTerminate(len(content) - pos + 1))
-        # invariants-end
-        lfc_reaches(content, pos + 1)
-        pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
-    Assert(leading_header_count(content) >= pos)
-    lfc_all_markers(content)
-    return pos
+    # VACUITY CONTROL: if the frozen spec (the recursive @Pure model plus the
+    # two ghost lemmas) were inconsistent, False would be provable here and
+    # EVERY wrong impl would verify. The returned 0 is wrong on any document
+    # that starts with a header line.
+    Assert(False)
+    return 0
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,30 +194,8 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
-    pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
-        # invariants-start
-        Invariant(0 <= pos and pos <= len(content))
-        Invariant(Forall(int, lambda i: (
-            Implies(0 <= i and i < pos, is_header_line(content[i])),
-            [[content[i]]])))
-        Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
-        Invariant(MustTerminate(len(content) - pos + 1))
-        # invariants-end
-        lfc_reaches(content, pos + 1)
-        pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
-    Assert(leading_header_count(content) >= pos)
-    lfc_all_markers(content)
-    return pos
+    # UNGROUNDED-ORACLE ECHO: return the spec's own pure oracle without
+    # establishing the per-line shape obligation (no lfc_all_markers call), so
+    # the Forall postcondition is asserted rather than proved.
+    return leading_header_count(content)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -194,30 +194,9 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
-    pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
-        # invariants-start
-        Invariant(0 <= pos and pos <= len(content))
-        Invariant(Forall(int, lambda i: (
-            Implies(0 <= i and i < pos, is_header_line(content[i])),
-            [[content[i]]])))
-        Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
-        Invariant(MustTerminate(len(content) - pos + 1))
-        # invariants-end
-        lfc_reaches(content, pos + 1)
-        pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
-    Assert(leading_header_count(content) >= pos)
+    # ORACLE ECHO, grounded: no scan at all — the value is taken straight from
+    # the frozen pure oracle, with the prefix-shape lemma supplying the Forall
+    # postcondition. Structurally unlike the gold forward loop.
     lfc_all_markers(content)
-    return pos
+    return leading_header_count(content)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,30 +194,26 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # BEHAVIOURALLY-CORRECT RESHAPE: the same forward scan, restructured as a
+    # flag-driven loop (guard hoisted into `keep`) with the result routed
+    # through a temporary and the trailing lemma/assert order swapped.
     pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
+    keep = len(content) > 0 and is_header_line(content[0])
+    while keep:
         # invariants-start
         Invariant(0 <= pos and pos <= len(content))
+        Invariant(Implies(keep, pos < len(content) and is_header_line(content[pos])))
         Invariant(Forall(int, lambda i: (
             Implies(0 <= i and i < pos, is_header_line(content[i])),
             [[content[i]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
         Invariant(MustTerminate(len(content) - pos + 1))
         # invariants-end
         lfc_reaches(content, pos + 1)
         pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
+        keep = pos < len(content) and is_header_line(content[pos])
+    lfc_all_markers(content)
     Assert(leading_header_count(content) >= pos)
-    lfc_all_markers(content)
-    return pos
+    answer = pos
+    return answer
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,29 +194,29 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # CONTROL-FLOW-EFFECT attack of a different shape: count EVERY header line
+    # in the document rather than the leading RUN (the `break` becomes a
+    # `continue`). Agrees with gold whenever the header block is the only run of
+    # header lines, and over-counts as soon as a later line has the header shape
+    # (e.g. a `:title:` field appearing again below the body), inserting the
+    # boilerplate past the body.
     pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
+    i = 0
+    while i < len(content):
         # invariants-start
-        Invariant(0 <= pos and pos <= len(content))
-        Invariant(Forall(int, lambda i: (
-            Implies(0 <= i and i < pos, is_header_line(content[i])),
-            [[content[i]]])))
+        Invariant(0 <= i and i <= len(content))
+        Invariant(0 <= pos and pos <= i)
+        Invariant(Forall(int, lambda k: (
+            Implies(0 <= k and k < pos, is_header_line(content[k])),
+            [[content[k]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
-        Invariant(MustTerminate(len(content) - pos + 1))
+        Invariant(MustTerminate(len(content) - i + 1))
         # invariants-end
-        lfc_reaches(content, pos + 1)
-        pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
+        if is_header_line(content[i]):
+            if pos == i:
+                lfc_reaches(content, pos + 1)
+            pos = pos + 1
+        i = i + 1
     Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
     return pos
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -194,30 +194,35 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # BEHAVIOURALLY-CORRECT STRUCTURAL RIVAL: same answer, different algorithm —
+    # a single forward pass with a `stop` latch that keeps scanning to the end of
+    # the document (no early exit) and freezes the count at the first
+    # non-header line. Its faithful refinement is NOT the gold `for ... else
+    # break` loop, so it exercises the refinement map rather than echoing it.
     pos = 0
-    while pos < len(content) and is_header_line(content[pos]):
+    i = 0
+    stop = False
+    while i < len(content):
         # invariants-start
-        Invariant(0 <= pos and pos <= len(content))
-        Invariant(Forall(int, lambda i: (
-            Implies(0 <= i and i < pos, is_header_line(content[i])),
-            [[content[i]]])))
+        Invariant(0 <= i and i <= len(content))
+        Invariant(0 <= pos and pos <= i)
+        Invariant(Implies(not stop, pos == i))
+        Invariant(Implies(stop, pos < len(content) and not is_header_line(content[pos])))
+        Invariant(Forall(int, lambda k: (
+            Implies(0 <= k and k < pos, is_header_line(content[k])),
+            [[content[k]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
-        Invariant(MustTerminate(len(content) - pos + 1))
+        Invariant(MustTerminate(len(content) - i + 1))
         # invariants-end
-        lfc_reaches(content, pos + 1)
-        pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
+        if not stop:
+            if is_header_line(content[i]):
+                lfc_reaches(content, i + 1)
+                pos = i + 1
+            else:
+                stop = True
+        i = i + 1
     Assert(leading_header_count(content) >= pos)
+    Assert(Implies(pos < len(content), not is_header_line(content[pos])))
     lfc_all_markers(content)
     return pos
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,6 +194,11 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # PARTIAL-DOMAIN attack, other side: correct on every document EXCEPT one
+    # whose leading header block runs to the very end of the document (no body
+    # line follows), where it under-counts by one. Every F2P input has a body,
+    # so this is exactly the "correct on the tests, wrong in general" shape a
+    # too-weak spec would admit.
     pos = 0
     while pos < len(content) and is_header_line(content[pos]):
         # invariants-start
@@ -202,22 +207,13 @@
             Implies(0 <= i and i < pos, is_header_line(content[i])),
             [[content[i]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
         Invariant(MustTerminate(len(content) - pos + 1))
         # invariants-end
         lfc_reaches(content, pos + 1)
         pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
     Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
+    if pos == len(content) and pos > 0:
+        pos = pos - 1
     return pos
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,6 +194,12 @@
                     not is_header_line(content[Result()])))
     # post-conditions-end
     # impl-start
+    # TEST-SHAPED PARTIAL-DOMAIN attack (the sharpest one): the gold scan,
+    # except a document whose leading header block has exactly THREE lines
+    # under-counts by one. Every F2P/P2P document has a leading block of 0 or 2
+    # header lines, so this impl passes the entire graded test suite while being
+    # wrong in general — exactly the impl a spec that only pinned the tested
+    # cases would admit.
     pos = 0
     while pos < len(content) and is_header_line(content[pos]):
         # invariants-start
@@ -202,22 +208,13 @@
             Implies(0 <= i and i < pos, is_header_line(content[i])),
             [[content[i]]])))
         Invariant(leading_header_count(content) >= pos)
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
-        # rises by exactly one per pass and the guard keeps pos < len(content),
-        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
-        # matters — the last pass has 0 iterations left and MustTerminate(0) is
-        # unsatisfiable).
         Invariant(MustTerminate(len(content) - pos + 1))
         # invariants-end
         lfc_reaches(content, pos + 1)
         pos = pos + 1
-    # On exit: the first `pos` lines all have the header-line shape (loop
-    # invariant), and either pos == len(content) or content[pos] does not. The
-    # postcondition of leading_header_count then pins it to exactly `pos`:
-    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
-    # content[pos] to have the header-line shape.
     Assert(leading_header_count(content) >= pos)
     lfc_all_markers(content)
+    if pos == 3:
+        pos = 2
     return pos
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-11445.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A document may begin with a run of leading lines that have a specific
  ``:name: value`` shape (a header block). When boilerplate text is prepended
  to the document, it must be placed AFTER that leading header block but BEFORE
  the document body, so the body — in particular a first-line section title —
  is left untouched.

  The number of leading lines that belong to the header block therefore decides
  where the boilerplate is inserted. A line counts as a header line only when
  it has exactly this shape:

      a leading colon, then a non-empty name (whose first code point is neither
      a colon nor a space), then a closing colon, where that closing colon is
      immediately followed by a space or the end of the line, and the code
      point just before it is not a space.

  A line that does not have this exact shape — for example one whose leading
  ``:name:`` is immediately followed by some other code point rather than a
  space or end of line — is NOT a header line, and therefore ends the header
  block: the boilerplate is inserted before it.

  The contracted function returns the length of the leading header block: the
  greatest prefix length `p` such that every one of the first `p` lines has the
  header-line shape, and (when the document is longer) line `p` does not.

Lines are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a document is a `PSeq[PSeq[int]]`. The header-line predicate is
modelled DEEPLY (`is_header_line`) and validated out-of-band by axiom_check.py
(G-AX), NOT consumed as an axiom. The modelled domain excludes the back-slash
escape character (code point 92) inside a line and lines containing a newline
or carriage-return, which the inputs in scope never use (see mapping.md /
refinement.md).

Scanning a finite document is bounded work that must actually deliver its
count, so the operation carries a total-correctness obligation (MustTerminate
in the precondition, discharged by a per-loop measure in the invariants
region): without it a diverging body would satisfy every postcondition
vacuously while never producing the insertion point.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no consumed @ContractOnly axiom: the header-line predicate is modelled
#  deeply below as `is_header_line` and validated out-of-band by
#  axiom_check.py / G-AX.)
# axioms-end

# pure-start
COLON = 58     # ':'
SPACE = 32     # ' '
BACKTICK = 96  # '`'

@Pure
def first_boundary(line: PSeq[int], k: int) -> int:
    """Index of the first *boundary colon* at position >= k, or len(line) if
    none. A boundary colon is a colon immediately followed by a space, a
    back-quote, or the end of the line (i.e. a colon the name part cannot
    absorb). Recursive over the decreasing measure len(line) - k."""
    Requires(0 <= k and k <= len(line))
    Ensures(k <= Result() and Result() <= len(line))
    Ensures(Implies(Result() < len(line), line[Result()] == COLON))
    if k >= len(line):
        return len(line)
    if line[k] == COLON and (k == len(line) - 1
                             or line[k + 1] == SPACE
                             or line[k + 1] == BACKTICK):
        return k
    return first_boundary(line, k + 1)

@Pure
def is_header_line(line: PSeq[int]) -> bool:
    """The header-line predicate (deep model, over the back-slash-free domain).
    True iff the line is ``:name:`` whose closing colon is followed by a space
    or end of line and not preceded by a space — and the name's first code
    point is neither a colon nor a space. A ``:name:`` whose closing colon is
    followed by any other code point (rather than a space or end of line) does
    NOT have the header-line shape."""
    if len(line) < 2:
        return False
    if line[0] != COLON:
        return False
    if line[1] == COLON or line[1] == SPACE:
        return False
    b = first_boundary(line, 2)
    if b >= len(line):
        return False
    if line[b - 1] == SPACE:
        return False
    return b == len(line) - 1 or line[b + 1] == SPACE

@Pure
def leading_header_count(doc: PSeq[PSeq[int]]) -> int:
    """The length of the leading header block: the greatest prefix length `p`
    such that the first `p` lines all have the header-line shape, and (when the
    document is longer) line `p` does not. Front-recursive (one unfold per
    line)."""
    Ensures(0 <= Result() and Result() <= len(doc))
    Ensures(Implies(Result() < len(doc), not is_header_line(doc[Result()])))
    if len(doc) == 0:
        return 0
    if not is_header_line(doc[0]):
        return 0
    return 1 + leading_header_count(doc.drop(1))
# pure-end

def lfc_all_markers(doc: PSeq[PSeq[int]]) -> None:
    """Lemma: every line strictly before leading_header_count(doc) has the
    header-line shape. Proved by front-recursion mirroring
    leading_header_count's unfold."""
    # Ghost recursion over the finite document: one unfold per line, on the
    # strictly decreasing, bounded-below measure len(doc) (the tail is one
    # shorter). The + 1 keeps it positive at len(doc) == 0, where the lemma
    # returns without recursing.
    Requires(MustTerminate(len(doc) + 1))
    Ensures(Forall(int, lambda i: (
        Implies(0 <= i and i < leading_header_count(doc), is_header_line(doc[i])),
        [[doc[i]]])))
    if len(doc) > 0 and is_header_line(doc[0]):
        lfc_all_markers(doc.drop(1))
        # leading_header_count unfolds by one when the head is a header line.
        Assert(leading_header_count(doc) == 1 + leading_header_count(doc.drop(1)))
        # the tail's per-line shapes shift back to indices >= 1 in `doc`:
        # for i in [1, lhc(doc)), doc[i] == doc.drop(1)[i-1], which the
        # recursive postcondition has already shown to be a header line.
        Assert(Forall(int, lambda i: (
            Implies(1 <= i and i < leading_header_count(doc),
                    doc[i] == doc.drop(1)[i - 1]),
            [[doc[i]]])))
        Assert(Forall(int, lambda i: (
            Implies(1 <= i and i < leading_header_count(doc),
                    is_header_line(doc.drop(1)[i - 1])),
            [[doc[i]]])))

def lfc_reaches(doc: PSeq[PSeq[int]], p: int) -> None:
    """Lemma: if the first `p` lines all have the header-line shape, then the
    leading header block of the whole document has length at least `p`. Proved
    by front-recursion: the head is a header line, so leading_header_count
    unfolds by one and the tail's prefix is shorter by one."""
    Requires(0 <= p and p <= len(doc))
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < p, is_header_line(doc[i])),
        [[doc[i]]])))
    # Ghost recursion on the prefix length: each call passes p - 1, so the
    # measure p strictly decreases and the recursion stops at p == 0 (where the
    # + 1 keeps it positive).
    Requires(MustTerminate(p + 1))
    Ensures(leading_header_count(doc) >= p)
    if p > 0:
        Assert(is_header_line(doc[0]))
        Assert(Forall(int, lambda i: (
            Implies(0 <= i and i < p - 1, doc.drop(1)[i] == doc[i + 1]),
            [[doc.drop(1)[i]]])))
        lfc_reaches(doc.drop(1), p - 1)

def count_leading_header_lines(content: PSeq[PSeq[int]]) -> int:
    # pre-conditions-start
    # (content is a read-only pure sequence; PSeq carries no permission.)
    # TERMINATION: the count must actually be DELIVERED — the prolog's
    # insertion point is the returned value. Without this obligation an
    # implementation that scans forever satisfies every Ensures vacuously.
    # The LEVEL len(content) + 2 strictly exceeds both ghost lemmas' levels
    # (lfc_reaches at pos + 1 <= len(content), lfc_all_markers at
    # len(content) + 1), so the impl may call them but may NOT re-invoke
    # itself: no strictly smaller level is available for a self-call.
    Requires(MustTerminate(len(content) + 2))
    # pre-conditions-end
    # post-conditions-start
    # The result is the length of the leading header block: it counts exactly
    # the maximal run of leading header lines, so the boilerplate is inserted
    # after the header block and before the body.
    Ensures(Result() == leading_header_count(content))
    Ensures(0 <= Result() and Result() <= len(content))
    # Within the counted prefix every line has the header-line shape ...
    Ensures(Forall(int, lambda i: (
        Implies(0 <= i and i < Result(), is_header_line(content[i])),
        [[content[i]]])))
    # ... and (when the document is longer) the run stops at the first line
    # that does not have the header-line shape.
    Ensures(Implies(Result() < len(content),
                    not is_header_line(content[Result()])))
    # post-conditions-end
    # impl-start
    pos = 0
    while pos < len(content) and is_header_line(content[pos]):
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
        # rises by exactly one per pass and the guard keeps pos < len(content),
        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
        # matters — the last pass has 0 iterations left and MustTerminate(0) is
        # unsatisfiable).
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    # On exit: the first `pos` lines all have the header-line shape (loop
    # invariant), and either pos == len(content) or content[pos] does not. The
    # postcondition of leading_header_count then pins it to exactly `pos`:
    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
    # content[pos] to have the header-line shape.
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    return pos
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of sphinx-doc__sphinx-11445/nagini. 13 same-spec attacks + positive control, all built by splicing ONLY the impl region of the frozen model.py (mk.py; axioms/@Pure/Requires/Ensures/lemmas byte-identical). All 13 confirmed SAME by `adversary same-spec` and ADMISSIBLE by variant_scope.unsound_evasions (no new @ContractOnly / Assume / Refute).

SPEC SHAPE (why the impl-region surface is narrow): the frozen postcondition pins the return EXACTLY (Result() == leading_header_count(content)) and same_spec freezes the whole pure region (first_boundary/is_header_line/leading_header_count) plus both ghost lemmas. So all real G-EQ risk sits on the A legs (deep-model reference) and the model<->patch correspondence, which is where I concentrated.

**BASELINES.** positive_control.py (= model.py) => CANDIDATE, verifies in 13.8s. atk_1.py = prepatch bug re-encoded (impl body lifted verbatim from model_prepatch.py: inline ':' + non-colon name + any later colon, accepting:mod:`foo`) => exit 2, does not verify. prepatch_reproduced = true.

PER-ATTACK (cmd for each: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-11445 <path>`; run 3-at-a-time as background jobs):
- atk_1.py  prepatch re-encode / ungrounded-oracle echo of the pre-patch recogniser -> exit 2 (rejected). Spec senses the change via lfc_reaches' precondition Forall i<p: is_header_line(doc[i]).
- atk_2.py  partial-domain: scan capped at 1 header line (wrong on the:title:+:author: P2P doc) -> exit 2.
- atk_3.py  boundary/off-by-one: gold scan then +1 whenever a body follows -> exit 2.
- atk_4.py  control-flow-effect: per-line gate deleted, counts every line -> exit 2.
- atk_5.py  boundary attack aimed at the DISCRIMINATING clause: inline recogniser that rejects only a back-quote after the closing colon instead of REQUIRING space/EOL (agrees on:mod:`foo`, wrongly accepts:a:x) -> exit 2. This is the sharpest predicate-level probe and the deep model rejects it.
- atk_6.py  VACUITY CONTROL Assert(False) -> exit 2. The frozen recursive @Pure model + two lemmas are consistent; no wrong impl verifies for free (the guarded-self-call/vacuity failure mode is ruled out).
- atk_7.py  ungrounded-oracle echo: return leading_header_count(content) with the lfc_all_markers call omitted -> exit 2 (Forall postcondition asserted, not proved).
- atk_8.py  oracle echo, GROUNDED (lfc_all_markers + return leading_header_count) -> CANDIDATE, verifies 18.8s. RESOLVE RUN BELOW.
- atk_9.py  behaviourally-correct reshape (flag-driven loop, temp var) -> exit 2. Direct verify shows why: 'Postcondition... Assertion (Result() == leading_header_count(content)) might not hold' — an incomplete proof, NOT a spec weakness (its behaviour is gold-identical).
- atk_10.py control-flow-effect of a second shape: break->continue, counts EVERY header line in the doc rather than the leading run -> exit 2.
- atk_11.py behaviourally-correct STRUCTURAL rival: single full pass with a `stop` latch, no early exit — a genuinely different algorithm whose faithful refinement is NOT the gold for/else loop -> CANDIDATE, verifies 15.9s. RESOLVE RUN BELOW.
- atk_12.py partial-domain, other side: under-counts by one when the header block runs to EOF (every F2P doc has a body, so it is 'right on the tests') -> exit 2.
- atk_13.py TEST-SHAPED partial-domain (sharpest): gold scan except pos==3 -> 2. Every F2P/P2P doc has a leading block of 0 or 2, so this passes the whole graded suite while being wrong in general -> exit 2. The spec rejects it because the postcondition pins the value for ALL documents, not just the tested ones.

MANDATED RESOLVE RUNS (both verifying candidates materialized + executed, not speculated). Faithful refined patches built at base_commit 71db08c05197545944949d5aa76cd340e7143627 in a throwaway clone; each carries the gold patch's non-scan legs (Body import, jinja2 pass_environment, FIELD_NAME_RE, the lineno = 0 guard) and replaces the scan with the faithful refinement of that attack's impl:
- atk_8  -> atk_8_faithful_patch.diff (recursive `_leading_field_count`, no forward scan). run_resolve('sphinx-doc__sphinx-11445', patch) => completed=True, RESOLVED=True, attempts=1, note='resolved'; 2/2 F2P + 8/8 P2P pass, 0 failures.
- atk_11 -> atk_11_faithful_patch.diff (full-pass latch scan). run_resolve => completed=True, RESOLVED=True, attempts=1, note='resolved'; 2/2 F2P + 8/8 P2P pass, 0 failures.
Both verifying candidates therefore RESOLVE => not weaknesses (a resolving candidate is a correct rival, not verify=>/=correct).

### A-LEG AUDIT (the assigned focus; R/I left to G-CONF).
(1) refinement.md leg kinds: A1 R, A2 I, A3 R + A-reference, A4 R, B1 I, plus the declared domain restriction R. NO kind-3 leg. The axioms region is genuinely empty (only a comment) and model.py contains no @ContractOnly declaration, so there is no A-consumed row and no dead axiom — consistent with meta.json axioms=[] and deep_model_references=[A-reference]. Verified the mapping.md line numbers against the real base_commit file: sphinx/util/rst.py:28 docinfo_re,:81-86 the pos scan,:88-97 the insertion — all match.

(2) INDEPENDENT re-derivation of the A-reference (my own aleg_check.py, not the bundle's axiom_check.py): deep model == re.compile(Body.patterns['field_marker']).match on 8002 EXHAUSTIVE lines (all strings of length<=5 over ':` ax', all length-6 over ':` a') + 300000 wide-alphabet fuzz (different seed AND a wider alphabet than the bundle's: tab, non-ASCII e-acute / CJK / NBSP, more symbols) => 0 disagreements. Then a stronger, DOCUMENT-level check the bundle does not do: modelled leading_header_count == the gold patched scan (`for line in content: if FIELD_NAME_RE.match(line): pos+=1 else: break`) on 200005 documents drawn from a 27-line grammar-corner pool plus all five F2P/P2P documents => 0 disagreements. The bundle's own axiom_check.py also re-ran clean.

(3) A-reference CORRESPONDENCE probed THROUGH the official harness, which is the check no static read can make. probe_dm.diff: the repo recogniser is REPLACED by model.py's is_header_line/first_boundary transcribed code-point-for-code-point (no docutils regex in the patched file at all) => run_resolve completed=True, RESOLVED=True. So the deep model is not merely equal on a fuzz corpus — substituting it for the real callee still resolves, which is exactly the A-reference claim.

(4) DOMAIN RESTRICTION exploited adversarially. probe_dom.diff: deep model on the modelled domain but INVERTED on every out-of-domain line (containing back-slash 92, newline 10, or CR 13) — the maximum latitude the declared restriction grants a faithful refinement => run_resolve completed=True, RESOLVED=True. The restriction is therefore vacuous on the graded inputs, confirming mapping.md 2's claim rather than taking it on trust. Also confirmed Body.patterns['field_marker'] is byte-identical across docutils 0.18.1 / 0.19 / 0.20.1 / 0.23, so the A-reference is not pinned to one library version.

(5) R-leg spot-check behind A3: list(StringList) == [c[i] for i in range(len(c))] on a mixed docinfo/role/body document, so 'StringList iteration <-> PSeq indexing' holds and the for/else scan really is the indexed while loop.

### COMMANDS (all from the repo root swe-proof):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-11445 <atk>   # 13/13 SAME
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-11445 <atk>   # 11 exit-2, atk_8/atk_11 exit-0
  bash scripts/nagini_verify.sh atk_9.py                                        # the atk_9 error text
  python -c "from swebench_unified.harness import run_resolve;..."                      # 4 resolve runs (atk_8, atk_11, probe_dm, probe_dom) — all RESOLVED=True
  python aleg_check.py                   # independent A-leg re-derivation

**VERDICT:** SOUND. 13 admissible distinct attacks run (prepatch echo, 3 partial-domain incl. the test-shaped one, 2 boundary/off-by-one, the discriminating-clause boundary recogniser, 2 control-flow-effect, 2 oracle echoes, a correct reshape, a structural rival) plus a vacuity control and a verifying positive control. Every wrong impl was REJECTED; the only two verifying candidates are behaviourally correct and their materialized faithful patches both RESOLVE under the official harness. Two independent A-leg substitution probes resolve as well. No verifying wrong impl with a non-resolving faithful patch exists — verify=>correct holds. Residual (non-blocking, unchanged from the recorded state): the A-reference's soundness on lines containing a back-slash or an embedded newline/CR is undischarged by construction, but probe_dom shows even a maximally hostile use of that latitude still resolves, so it is not reachable by the graded behaviour.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.py`, `atk_11.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-11445.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A document may begin with a run of leading lines that have a specific
  ``:name: value`` shape (a header block). When boilerplate text is prepended
  to the document, it must be placed AFTER that leading header block but BEFORE
  the document body, so the body — in particular a first-line section title —
  is left untouched.

  The number of leading lines that belong to the header block therefore decides
  where the boilerplate is inserted. A line counts as a header line only when
  it has exactly this shape:

      a leading colon, then a non-empty name (whose first code point is neither
      a colon nor a space), then a closing colon, where that closing colon is
      immediately followed by a space or the end of the line, and the code
      point just before it is not a space.

  A line that does not have this exact shape — for example one whose leading
  ``:name:`` is immediately followed by some other code point rather than a
  space or end of line — is NOT a header line, and therefore ends the header
  block: the boilerplate is inserted before it.

  The contracted function returns the length of the leading header block: the
  greatest prefix length `p` such that every one of the first `p` lines has the
  header-line shape, and (when the document is longer) line `p` does not.

Lines are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a document is a `PSeq[PSeq[int]]`. The header-line predicate is
modelled DEEPLY (`is_header_line`) and validated out-of-band by axiom_check.py
(G-AX), NOT consumed as an axiom. The modelled domain excludes the back-slash
escape character (code point 92) inside a line and lines containing a newline
or carriage-return, which the inputs in scope never use (see mapping.md /
refinement.md).

Scanning a finite document is bounded work that must actually deliver its
count, so the operation carries a total-correctness obligation (MustTerminate
in the precondition, discharged by a per-loop measure in the invariants
region): without it a diverging body would satisfy every postcondition
vacuously while never producing the insertion point.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no consumed @ContractOnly axiom: the header-line predicate is modelled
#  deeply below as `is_header_line` and validated out-of-band by
#  axiom_check.py / G-AX.)
# axioms-end

# pure-start
COLON = 58     # ':'
SPACE = 32     # ' '
BACKTICK = 96  # '`'

@Pure
def first_boundary(line: PSeq[int], k: int) -> int:
    """Index of the first *boundary colon* at position >= k, or len(line) if
    none. A boundary colon is a colon immediately followed by a space, a
    back-quote, or the end of the line (i.e. a colon the name part cannot
    absorb). Recursive over the decreasing measure len(line) - k."""
    Requires(0 <= k and k <= len(line))
    Ensures(k <= Result() and Result() <= len(line))
    Ensures(Implies(Result() < len(line), line[Result()] == COLON))
    if k >= len(line):
        return len(line)
    if line[k] == COLON and (k == len(line) - 1
                             or line[k + 1] == SPACE
                             or line[k + 1] == BACKTICK):
        return k
    return first_boundary(line, k + 1)

@Pure
def is_header_line(line: PSeq[int]) -> bool:
    """The header-line predicate (deep model, over the back-slash-free domain).
    True iff the line is ``:name:`` whose closing colon is followed by a space
    or end of line and not preceded by a space — and the name's first code
    point is neither a colon nor a space. A ``:name:`` whose closing colon is
    followed by any other code point (rather than a space or end of line) does
    NOT have the header-line shape."""
    if len(line) < 2:
        return False
    if line[0] != COLON:
        return False
    if line[1] == COLON or line[1] == SPACE:
        return False
    b = first_boundary(line, 2)
    if b >= len(line):
        return False
    if line[b - 1] == SPACE:
        return False
    return b == len(line) - 1 or line[b + 1] == SPACE

@Pure
def leading_header_count(doc: PSeq[PSeq[int]]) -> int:
    """The length of the leading header block: the greatest prefix length `p`
    such that the first `p` lines all have the header-line shape, and (when the
    document is longer) line `p` does not. Front-recursive (one unfold per
    line)."""
    Ensures(0 <= Result() and Result() <= len(doc))
    Ensures(Implies(Result() < len(doc), not is_header_line(doc[Result()])))
    if len(doc) == 0:
        return 0
    if not is_header_line(doc[0]):
        return 0
    return 1 + leading_header_count(doc.drop(1))
# pure-end

def lfc_all_markers(doc: PSeq[PSeq[int]]) -> None:
    """Lemma: every line strictly before leading_header_count(doc) has the
    header-line shape. Proved by front-recursion mirroring
    leading_header_count's unfold."""
    # Ghost recursion over the finite document: one unfold per line, on the
    # strictly decreasing, bounded-below measure len(doc) (the tail is one
    # shorter). The + 1 keeps it positive at len(doc) == 0, where the lemma
    # returns without recursing.
    Requires(MustTerminate(len(doc) + 1))
    Ensures(Forall(int, lambda i: (
        Implies(0 <= i and i < leading_header_count(doc), is_header_line(doc[i])),
        [[doc[i]]])))
    if len(doc) > 0 and is_header_line(doc[0]):
        lfc_all_markers(doc.drop(1))
        # leading_header_count unfolds by one when the head is a header line.
        Assert(leading_header_count(doc) == 1 + leading_header_count(doc.drop(1)))
        # the tail's per-line shapes shift back to indices >= 1 in `doc`:
        # for i in [1, lhc(doc)), doc[i] == doc.drop(1)[i-1], which the
        # recursive postcondition has already shown to be a header line.
        Assert(Forall(int, lambda i: (
            Implies(1 <= i and i < leading_header_count(doc),
                    doc[i] == doc.drop(1)[i - 1]),
            [[doc[i]]])))
        Assert(Forall(int, lambda i: (
            Implies(1 <= i and i < leading_header_count(doc),
                    is_header_line(doc.drop(1)[i - 1])),
            [[doc[i]]])))

def lfc_reaches(doc: PSeq[PSeq[int]], p: int) -> None:
    """Lemma: if the first `p` lines all have the header-line shape, then the
    leading header block of the whole document has length at least `p`. Proved
    by front-recursion: the head is a header line, so leading_header_count
    unfolds by one and the tail's prefix is shorter by one."""
    Requires(0 <= p and p <= len(doc))
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < p, is_header_line(doc[i])),
        [[doc[i]]])))
    # Ghost recursion on the prefix length: each call passes p - 1, so the
    # measure p strictly decreases and the recursion stops at p == 0 (where the
    # + 1 keeps it positive).
    Requires(MustTerminate(p + 1))
    Ensures(leading_header_count(doc) >= p)
    if p > 0:
        Assert(is_header_line(doc[0]))
        Assert(Forall(int, lambda i: (
            Implies(0 <= i and i < p - 1, doc.drop(1)[i] == doc[i + 1]),
            [[doc.drop(1)[i]]])))
        lfc_reaches(doc.drop(1), p - 1)

def count_leading_header_lines(content: PSeq[PSeq[int]]) -> int:
    # pre-conditions-start
    # (content is a read-only pure sequence; PSeq carries no permission.)
    # TERMINATION: the count must actually be DELIVERED — the prolog's
    # insertion point is the returned value. Without this obligation an
    # implementation that scans forever satisfies every Ensures vacuously.
    # The LEVEL len(content) + 2 strictly exceeds both ghost lemmas' levels
    # (lfc_reaches at pos + 1 <= len(content), lfc_all_markers at
    # len(content) + 1), so the impl may call them but may NOT re-invoke
    # itself: no strictly smaller level is available for a self-call.
    Requires(MustTerminate(len(content) + 2))
    # pre-conditions-end
    # post-conditions-start
    # The result is the length of the leading header block: it counts exactly
    # the maximal run of leading header lines, so the boilerplate is inserted
    # after the header block and before the body.
    Ensures(Result() == leading_header_count(content))
    Ensures(0 <= Result() and Result() <= len(content))
    # Within the counted prefix every line has the header-line shape ...
    Ensures(Forall(int, lambda i: (
        Implies(0 <= i and i < Result(), is_header_line(content[i])),
        [[content[i]]])))
    # ... and (when the document is longer) the run stops at the first line
    # that does not have the header-line shape.
    Ensures(Implies(Result() < len(content),
                    not is_header_line(content[Result()])))
    # post-conditions-end
    # impl-start
    pos = 0
    while pos < len(content) and is_header_line(content[pos]):
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
        # rises by exactly one per pass and the guard keeps pos < len(content),
        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
        # matters — the last pass has 0 iterations left and MustTerminate(0) is
        # unsatisfiable).
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    # On exit: the first `pos` lines all have the header-line shape (loop
    # invariant), and either pos == len(content) or content[pos] does not. The
    # postcondition of leading_header_count then pins it to exactly `pos`:
    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
    # content[pos] to have the header-line shape.
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    return pos
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit of sphinx-doc__sphinx-11445/nagini. 13 same-spec attacks + positive control, all built by splicing ONLY the impl region of the frozen model.py (mk.py; axioms/@Pure/Requires/Ensures/lemmas byte-identical). All 13 confirmed SAME by `adversary same-spec` and ADMISSIBLE by variant_scope.unsound_evasions (no new @ContractOnly / Assume / Refute).

SPEC SHAPE (why the impl-region surface is narrow): the frozen postcondition pins the return EXACTLY (Result() == leading_header_count(content)) and same_spec freezes the whole pure region (first_boundary/is_header_line/leading_header_count) plus both ghost lemmas. So all real G-EQ risk sits on the A legs (deep-model reference) and the model<->patch correspondence, which is where I concentrated.

**BASELINES.** positive_control.py (= model.py) => CANDIDATE, verifies in 13.8s. atk_1.py = prepatch bug re-encoded (impl body lifted verbatim from model_prepatch.py: inline ':' + non-colon name + any later colon, accepting:mod:`foo`) => exit 2, does not verify. prepatch_reproduced = true.

PER-ATTACK (cmd for each: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-11445 <path>`; run 3-at-a-time as background jobs):
- atk_1.py  prepatch re-encode / ungrounded-oracle echo of the pre-patch recogniser -> exit 2 (rejected). Spec senses the change via lfc_reaches' precondition Forall i<p: is_header_line(doc[i]).
- atk_2.py  partial-domain: scan capped at 1 header line (wrong on the:title:+:author: P2P doc) -> exit 2.
- atk_3.py  boundary/off-by-one: gold scan then +1 whenever a body follows -> exit 2.
- atk_4.py  control-flow-effect: per-line gate deleted, counts every line -> exit 2.
- atk_5.py  boundary attack aimed at the DISCRIMINATING clause: inline recogniser that rejects only a back-quote after the closing colon instead of REQUIRING space/EOL (agrees on:mod:`foo`, wrongly accepts:a:x) -> exit 2. This is the sharpest predicate-level probe and the deep model rejects it.
- atk_6.py  VACUITY CONTROL Assert(False) -> exit 2. The frozen recursive @Pure model + two lemmas are consistent; no wrong impl verifies for free (the guarded-self-call/vacuity failure mode is ruled out).
- atk_7.py  ungrounded-oracle echo: return leading_header_count(content) with the lfc_all_markers call omitted -> exit 2 (Forall postcondition asserted, not proved).
- atk_8.py  oracle echo, GROUNDED (lfc_all_markers + return leading_header_count) -> CANDIDATE, verifies 18.8s. RESOLVE RUN BELOW.
- atk_9.py  behaviourally-correct reshape (flag-driven loop, temp var) -> exit 2. Direct verify shows why: 'Postcondition... Assertion (Result() == leading_header_count(content)) might not hold' — an incomplete proof, NOT a spec weakness (its behaviour is gold-identical).
- atk_10.py control-flow-effect of a second shape: break->continue, counts EVERY header line in the doc rather than the leading run -> exit 2.
- atk_11.py behaviourally-correct STRUCTURAL rival: single full pass with a `stop` latch, no early exit — a genuinely different algorithm whose faithful refinement is NOT the gold for/else loop -> CANDIDATE, verifies 15.9s. RESOLVE RUN BELOW.
- atk_12.py partial-domain, other side: under-counts by one when the header block runs to EOF (every F2P doc has a body, so it is 'right on the tests') -> exit 2.
- atk_13.py TEST-SHAPED partial-domain (sharpest): gold scan except pos==3 -> 2. Every F2P/P2P doc has a leading block of 0 or 2, so this passes the whole graded suite while being wrong in general -> exit 2. The spec rejects it because the postcondition pins the value for ALL documents, not just the tested ones.

MANDATED RESOLVE RUNS (both verifying candidates materialized + executed, not speculated). Faithful refined patches built at base_commit 71db08c05197545944949d5aa76cd340e7143627 in a throwaway clone; each carries the gold patch's non-scan legs (Body import, jinja2 pass_environment, FIELD_NAME_RE, the lineno = 0 guard) and replaces the scan with the faithful refinement of that attack's impl:
- atk_8  -> atk_8_faithful_patch.diff (recursive `_leading_field_count`, no forward scan). run_resolve('sphinx-doc__sphinx-11445', patch) => completed=True, RESOLVED=True, attempts=1, note='resolved'; 2/2 F2P + 8/8 P2P pass, 0 failures.
- atk_11 -> atk_11_faithful_patch.diff (full-pass latch scan). run_resolve => completed=True, RESOLVED=True, attempts=1, note='resolved'; 2/2 F2P + 8/8 P2P pass, 0 failures.
Both verifying candidates therefore RESOLVE => not weaknesses (a resolving candidate is a correct rival, not verify=>/=correct).

### A-LEG AUDIT (the assigned focus; R/I left to G-CONF).
(1) refinement.md leg kinds: A1 R, A2 I, A3 R + A-reference, A4 R, B1 I, plus the declared domain restriction R. NO kind-3 leg. The axioms region is genuinely empty (only a comment) and model.py contains no @ContractOnly declaration, so there is no A-consumed row and no dead axiom — consistent with meta.json axioms=[] and deep_model_references=[A-reference]. Verified the mapping.md line numbers against the real base_commit file: sphinx/util/rst.py:28 docinfo_re,:81-86 the pos scan,:88-97 the insertion — all match.

(2) INDEPENDENT re-derivation of the A-reference (my own aleg_check.py, not the bundle's axiom_check.py): deep model == re.compile(Body.patterns['field_marker']).match on 8002 EXHAUSTIVE lines (all strings of length<=5 over ':` ax', all length-6 over ':` a') + 300000 wide-alphabet fuzz (different seed AND a wider alphabet than the bundle's: tab, non-ASCII e-acute / CJK / NBSP, more symbols) => 0 disagreements. Then a stronger, DOCUMENT-level check the bundle does not do: modelled leading_header_count == the gold patched scan (`for line in content: if FIELD_NAME_RE.match(line): pos+=1 else: break`) on 200005 documents drawn from a 27-line grammar-corner pool plus all five F2P/P2P documents => 0 disagreements. The bundle's own axiom_check.py also re-ran clean.

(3) A-reference CORRESPONDENCE probed THROUGH the official harness, which is the check no static read can make. probe_dm.diff: the repo recogniser is REPLACED by model.py's is_header_line/first_boundary transcribed code-point-for-code-point (no docutils regex in the patched file at all) => run_resolve completed=True, RESOLVED=True. So the deep model is not merely equal on a fuzz corpus — substituting it for the real callee still resolves, which is exactly the A-reference claim.

(4) DOMAIN RESTRICTION exploited adversarially. probe_dom.diff: deep model on the modelled domain but INVERTED on every out-of-domain line (containing back-slash 92, newline 10, or CR 13) — the maximum latitude the declared restriction grants a faithful refinement => run_resolve completed=True, RESOLVED=True. The restriction is therefore vacuous on the graded inputs, confirming mapping.md 2's claim rather than taking it on trust. Also confirmed Body.patterns['field_marker'] is byte-identical across docutils 0.18.1 / 0.19 / 0.20.1 / 0.23, so the A-reference is not pinned to one library version.

(5) R-leg spot-check behind A3: list(StringList) == [c[i] for i in range(len(c))] on a mixed docinfo/role/body document, so 'StringList iteration <-> PSeq indexing' holds and the for/else scan really is the indexed while loop.

### COMMANDS (all from the repo root swe-proof):
  python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-11445 <atk>   # 13/13 SAME
  python -m swebench_unified.adversary weakness  nagini sphinx-doc__sphinx-11445 <atk>   # 11 exit-2, atk_8/atk_11 exit-0
  bash scripts/nagini_verify.sh atk_9.py                                        # the atk_9 error text
  python -c "from swebench_unified.harness import run_resolve;..."                      # 4 resolve runs (atk_8, atk_11, probe_dm, probe_dom) — all RESOLVED=True
  python aleg_check.py                   # independent A-leg re-derivation

**VERDICT:** SOUND. 13 admissible distinct attacks run (prepatch echo, 3 partial-domain incl. the test-shaped one, 2 boundary/off-by-one, the discriminating-clause boundary recogniser, 2 control-flow-effect, 2 oracle echoes, a correct reshape, a structural rival) plus a vacuity control and a verifying positive control. Every wrong impl was REJECTED; the only two verifying candidates are behaviourally correct and their materialized faithful patches both RESOLVE under the official harness. Two independent A-leg substitution probes resolve as well. No verifying wrong impl with a non-resolving faithful patch exists — verify=>correct holds. Residual (non-blocking, unchanged from the recorded state): the A-reference's soundness on lines containing a back-slash or an embedded newline/CR is undischarged by construction, but probe_dom shows even a maximally hostile use of that latitude still resolves, so it is not reachable by the graded behaviour.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** MODELED FUNCTION vs REAL CALLEE. count_leading_header_lines(content) models the leading-field-block scan in sphinx/util/rst.py prepend_prolog (lines 81-86 post-patch): `pos=0; for line in content: if FIELD_NAME_RE.match(line): pos+=1 else: break`. Reference = worktree at base_commit 71db08c05197 with patch.diff APPLIED (applied cleanly; confirmed FIELD_NAME_RE = re.compile(Body.patterns['field_marker']) and the `lineno = 0` guard are present). The modeled quantity (greatest all-header-line prefix length, pinned by Ensures(Result() == leading_header_count(content))) is exactly what the gold loop computes. Downstream insertion (lines 88-97) is byte-identical pre/post patch and a deterministic function of pos, so not re-modeled -- correctly tagged I in refinement.md B1.

INTEGRITY / SPEC-REGION CHECKS. markers.spec_view(model.py, nagini) hashes to d675a4b751547193ad92acbe588ad8d0e56150bbc39b0522ad42585d9d3a444b, byte-identical to meta.json G-HYGIENE spec_view. All 7 region hashes (axioms/pure/pre-conditions/post-conditions/invariants/impl/spec_view) match meta exactly. same_spec(model.py, model_prepatch.py) = True, so the prepatch differs only in the impl region.

### INDEPENDENT DIFFERENTIALS I RAN (not just re-running the bundle's own checks):
1. In-domain single-line differential, 3,000,000 randomized inputs, wide alphabet incl. C0 control chars, NBSP, U+3000, U+2028/2029, U+200B, U+FEFF, and non-ASCII (e', CJK), heavily biased toward the grammar-critical set {':',' ','`','\t'} -> 0 divergences.
2. Exhaustive in-domain sweeps over 6 grammar-critical alphabets: {':','`','a',' ','\t'} len<=9 (2.44M), {':','`',' ','a'} len<=10 (1.40M), {':','`','a','b',' ','.'} len<=7, {':','`',' ','\t',VT,FF,FS,NEL} len<=6, {':','`','a',NBSP,U+2028,U+3000} len<=6, {':','`',' ','+'} len<=8 -> 0 divergences in every sweep (~4.6M inputs total).
3. Bundle's axiom_check.py: exit 0 (24 boundary + 200k fuzz).
4. Bundle's conformance_check.py run against the REAL PATCHED WORKTREE (PYTHONPATH=worktree, real prepend_prolog via StringList + sentinel-prolog recovery): 'G-CONF pass: 0 disagreements over 100020 documents'. This is a document-level, not just per-line, confirmation.

REACHABILITY OF THE TWO EXCLUSIONS (the crux, since the domain restriction is prose-only -- the pre-conditions region carries only MustTerminate, so no Requires enforces it):
- Newline/CR: STRUCTURALLY unreachable. The modeled lines are StringList elements; docutils string2lines('line1\nline2\r\nline3\rline4\n:a: v\n') -> ['line1','line2','line3','line4',':a: v'], i.e. no element ever contains an embedded \n or \r. Verified directly. Also CR-only divergences = 0, so only '\n' bites, and it cannot occur.
- Backslash: empirically unreachable. Scanned all 361 *.rst files in the repo worktree, testing the first 5 lines of each for model!=real -> 0 divergent leading lines. The realistic documented rST escaped-colon field name ':Docutils\: version: 0.5' AGREES (real=True, model=True), as do ':title: a\b', ':copyright: \(c\) 2024', ":author: O\'Brien", ':file: C:\path\to\thing'. The divergent shapes (':a\:', ':a:\:', ':x\:') are not valid field lines and are contrived as document-leading lines.

HONEST CAVEAT I CHECKED AND WEIGHED (this is the strongest argument an attacker could make): the excluded backslash class does OVERLAP the patch delta. Over {':','`','a',' ','\\'} len<=7 (97,656 inputs) there are 2,683 inputs where pre-patch docinfo_re and post-patch FIELD_NAME_RE disagree, 707 model divergences, and 77 in the intersection -- e.g. ':a:\\:' where pre=True, post=False, model=True, so on that input the model tracks the PRE-patch recogniser rather than the fix. So the exclusion is not merely orthogonal to the bug; it does carve out a sliver of the delta.

I judged this NOT a faithfulness defect because: (a) it is explicitly DECLARED in the solver-visible model.py docstring ('The modelled domain excludes the back-slash escape character (code point 92) inside a line and lines containing a newline or carriage-return'), not hidden; (b) mapping.md 2 and refinement.md A document it with the correct grammar reason (the '\\.' escape alternative and the '$'-before-'\n' anchor); (c) axiom_check.py's check_line ASSERTS every checked line stays inside the domain, so a future edit cannot silently widen it; (d) it is unreachable in scope per the two reachability results above; and (e) it does not blunt the fix's discriminating content -- ':mod:`foo`' and ':mod:`mypackage2`' are IN-domain and correctly rejected (pre=True, post=False, model=False), which is exactly the F2P behaviour.

**GRAMMAR-CLAUSE AUDIT.** Model clauses map one-to-one onto ':(?![:])([^:\\]|\\.|:(?!([ `]|$)))*(?<!):( +|$)': line[1] not in {':',' '} <-> (?![:]); first_boundary's colon-followed-by-space/backtick/EOL <-> the ':(?!([ `]|$))' name-body alternative (a colon the name CAN absorb is one followed by none of those); line[b-1] != SPACE <-> (?<!); line[b+1]==SPACE or b==len-1 <-> ( +|$) (one space suffices for ' +', so no drift). '::' and ': ' correctly rejected by both. field_marker is byte-identical in the installed docutils 0.23 to the pattern quoted in mapping.md.

**CONCLUSION:** the spec is not too strong and does not drift from the real patched repo on any in-scope input. No in-domain diverging input exists across ~7.6M inputs tested plus 100,020 real-repo document comparisons. Verdict FAITHFUL.

Counterexample / evidence:

```
None. No in-domain input separates the modeled function from the real patched callee, so no counterexample to faithfulness exists. Positive control: `scripts/nagini_verify.sh model.py` => 'Verification successful' (16.2s, exit 0).
```

**MODELED FUNCTION vs REAL CALLEE.** count_leading_header_lines(content) models the leading-field-block scan in sphinx/util/rst.py prepend_prolog (lines 81-86 post-patch): `pos=0; for line in content: if FIELD_NAME_RE.match(line): pos+=1 else: break`. Reference = worktree at base_commit 71db08c05197 with patch.diff APPLIED (applied cleanly; confirmed FIELD_NAME_RE = re.compile(Body.patterns['field_marker']) and the `lineno = 0` guard are present). The modeled quantity (greatest all-header-line prefix length, pinned by Ensures(Result() == leading_header_count(content))) is exactly what the gold loop computes. Downstream insertion (lines 88-97) is byte-identical pre/post patch and a deterministic function of pos, so not re-modeled -- correctly tagged I in refinement.md B1.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE / gold-reconstruction review of sphinx-doc__sphinx-11445 nagini bundle. Verdict NO-LEAKAGE, on my own measurements.

SCOPE / RELAXATION STATUS: No documented relaxation exists here. meta.json has NO `relaxed_leakage` key (keys: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version) and there is no RELAXED_LEAKAGE.md in the directory. The bundle claims an outright clean G-LEAK, so I held it to the strict standard rather than any unavoidability argument. Note the task prompt listed `patch.diff` as a bundle file; it does not exist, and meta.json's `patch_diff` field is a placeholder string ("gold patch verbatim (applies cleanly at base_commit)") rather than the diff. I therefore took the gold patch from benchmark-verified/sphinx-doc__sphinx-11445/instance.json['patch']. Bookkeeping oddity, not leakage.

SPEC-VIEW INTEGRITY (measured): markers.region_hashes(model.py, nagini) reproduces the recorded G-HYGIENE hashes exactly, including spec_view = d675a4b751547193ad92acbe588ad8d0e56150bbc39b0522ad42585d9d3a444b. All six regions (axioms/pure/pre-conditions/post-conditions/impl/invariants) MATCH. markers.same_spec(model.py, model_prepatch.py) == True, so the prepatch differs only in impl.

**GOLD EDIT:** sphinx/util/rst.py — `docinfo_re = re.compile(':\\w+:.*?')` -> `FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])` (plus `from docutils.parsers.rst.states import Body`, a jinja2 import tidy, and a `lineno = 0` guard).

LEXICAL SWEEP (0 hits): I generated the exact spec view via markers.spec_view(src, get_backend('nagini')) and swept it for every gold-edit identifier: field_marker, FIELD_NAME_RE, docinfo_re, Body.patterns, re.compile, StringList, docutils, rst.py, rst_prolog, splitlines, lineno, insert(, <generated>, <rst_prolog>, 'import re', '\\w', '?<!', '(?!', pass_environment, jinja2, english, roles. ALL ABSENT — total hits 0. No regex literal and no repo path/line-number (sphinx/util/rst.py:81-86) appears. The predicate is de-narrated as is_header_line / 'header block' / 'boilerplate'; the only 'sphinx' occurrence is the instance-id string in the docstring title, which is bundle identification, not mechanism.

LOAD-BEARING TEST (the decisive measurement, run in /tmp): I mechanically stripped ALL prose from both model.py and model_prepatch.py — module docstring, every function docstring, and every comment except the bare region markers — yielding gold_deprose.py and pre_deprose.py. Results under the pinned verifier (scripts/nagini_verify.sh):
  - gold_deprose.py: 'Verification successful' (13.20s)
  - pre_deprose.py: 'Verification failed' (214.89s) — 'The precondition of method lfc_reaches might not hold. Assertion Forall(int, (lambda i: (Implies(((0 <= i) and (i < p)), is_header_line(doc[i]))...' 
So the discrimination against the PRE-patch impl is carried entirely by the FORMAL predicate (is_header_line / first_boundary / leading_header_count and the lfc_reaches precondition), NOT by any narration. Stripping every word of prose costs the spec nothing. That is the opposite of a leak: no English sentence in the spec view is doing discriminating work, so none of it can be the channel. Baseline: unstripped model.py verifies (exit 0, 11.66s).

DERIVABILITY FROM problem_statement ALONE (hints_text deliberately excluded): the public statement discloses the discriminating input verbatim — `docs/mypackage.rst` beginning `:mod:`mypackage2``, plus the explicit contrast 'if the heading... were `mypackage2` instead of `:mod:mypackage2` then the heading displays correctly' — and the observable (heading not rendered / absent from toctree when rst_prolog is set). So 'a `:name:` immediately followed by a back-quote must NOT count as a header line, and the boilerplate must go before it so a first-line title survives' is fully derivable from public text. That is exactly and only what the spec view characterizes. I confirmed I did NOT need hints_text: the hints add the rst.py#L81-L91 permalink and the 'prolog inserted between:mod:`...` and the header' diagnosis, neither of which the spec view reflects.

BACKTICK CLAUSE (the one line worth scrutinizing): BACKTICK = 96 in first_boundary, and the 'back-quote' wording, are the closest thing to mechanism in the view. I checked whether it exceeds the public facet by reimplementing the deep model against the real docutils recogniser re.compile(Body.patterns['field_marker']) = ':(?![:])([^:\\\\]|\\\\.|:(?!([ `]|$)))*(?<!):( +|$)': on ':mod:`mypackage2`' model=False real=False; ':mod:mypackage2' model=False real=False; ':author: me' model=True real=True; ':a:' model=True real=True; 'Welcome' model=False real=False. The backtick case is precisely what makes the PUBLIC failing input rejected — i.e. it encodes the publicly-disclosed required behaviour, not a private detail of the chosen regex. It names no regex, no docutils grammar, no symbol. The declared domain exclusion (back-slash code point 92, newline/CR) is a narrowing of scope, not a reconstruction of the edit.

**CORE GATES I RE-RAN RATHER THAN INHERITED:** axiom_check.py exit 0 — 'is_header_line deep model == docutils field_marker recogniser on 24 boundary + 200000 fuzz inputs'; gold model.py verifies; prepatch fails on the is_header_line discriminating clause (G-DIFF sound, and sound even de-narrated). So the disposition this spec rests on is not broken.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as its own finding, per instructions): I grepped all bundle files for panel/attacker/reviewer/auditor addressing and for instructions about which verdict to record ('honest verdict', 'do not report', 'NO-LEAKAGE', etc.). NOTHING addresses or instructs me. The hits are confined to meta.json's gates block and verdict.md, which are passive RECORDS of prior panel runs (including a prior G-PANEL-3 agent_verdict 'NO-LEAKAGE' with its rationale). I treated those as claims to re-derive independently and did not inherit them — my verdict rests on the region-hash reproduction, the 0-hit lexical sweep, the de-narrated verify/fail pair above, and the recogniser comparison I ran myself. Reaching the same conclusion as the recorded prior run is a convergent measurement, not a rubber-stamp.

**CONCLUSION:** the spec view names no gold identifier, contains no regex or repo location, survives full prose-stripping with its discriminating power intact, and its entire behavioural content is derivable from the public problem_statement's `:mod:`mypackage2`` example. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
