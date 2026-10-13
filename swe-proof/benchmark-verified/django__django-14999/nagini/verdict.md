# P2 adversarial audit — django__django-14999

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,29 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
-    if before_table == after_table:
-        return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if before_table == after_table:
+        # PRE-PATCH: no top-level table-identity guard, so every dependent
+        # request is issued anyway. Only the move of the model's own table is
+        # inert here, and only because alter_db_table short-circuits internally.
+        k = 0
+        while k < nc + 2 * nl:
+            # invariants-start
+            Invariant(Acc(list_pred(column_relations), 1 / 2))
+            Invariant(Acc(list_pred(link_relations), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(nc == len(column_relations) and nl == len(link_relations))
+            Invariant(0 <= k and k <= nc + 2 * nl)
+            Invariant(len(result) == k)
+            Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
+                      result[t] == t)))
+            Invariant(MustTerminate(nc + 2 * nl - k + 1))
+            # invariants-end
+            result.append(k)
+            k = k + 1
+        return result
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +248,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +255,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +264,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if nc == 0 and nl == 1:
+        # the column INSIDE link table 0 (code 1) rewritten BEFORE link
+        # table 0 has been moved (code 0) -- the graded m2m shape
+        alt = [OP_MAIN_MOVE, 1, 0]  # type: List[int]
+        Assert(len(alt) == 3)
+        Assert(alt[0] == OP_MAIN_MOVE and alt[1] == 1 and alt[2] == 0)
+        return alt
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +237,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +244,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +253,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if nc == 1 and nl == 0:
+        # the move of the model's own table asked for LAST, after the
+        # column relation's rewrite -- the graded FK shape
+        alt = [0, OP_MAIN_MOVE]  # type: List[int]
+        Assert(len(alt) == 2)
+        Assert(alt[0] == 0 and alt[1] == OP_MAIN_MOVE)
+        return alt
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +237,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +244,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +253,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if nc == 0 and nl == 1:
+        # link table 0 moved, but the column inside it never rewritten --
+        # gold on every other shape (partial domain)
+        alt = [OP_MAIN_MOVE, 0]  # type: List[int]
+        Assert(len(alt) == 2)
+        Assert(alt[0] == OP_MAIN_MOVE and alt[1] == 0)
+        return alt
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +237,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +244,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +253,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if nc == 0 and nl == 1:
+        # link table 0 moved TWICE and its inner column never rewritten;
+        # exact gold length, so only a multiplicity clause can see it
+        alt = [OP_MAIN_MOVE, 0, 0]  # type: List[int]
+        Assert(len(alt) == 3)
+        Assert(alt[0] == OP_MAIN_MOVE and alt[1] == 0 and alt[2] == 0)
+        return alt
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +237,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +244,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +253,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,59 +209,12 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
-    nc = len(column_relations)
-    nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
-    i = 0
-    while i < nc:
-        # invariants-start
-        Invariant(Acc(list_pred(column_relations), 1 / 2))
-        Invariant(Acc(list_pred(link_relations), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= i and i <= nc)
-        Invariant(len(result) == 1 + i)
-        Invariant(result[0] == OP_MAIN_MOVE)
-        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
-        Invariant(MustTerminate(nc - i + 1))
-        # invariants-end
-        result.append(i)
-        i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
-    m = 0
-    while m < 2 * nl:
-        # invariants-start
-        Invariant(Acc(list_pred(column_relations), 1 / 2))
-        Invariant(Acc(list_pred(link_relations), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
-        Invariant(len(result) == 1 + nc + m)
-        Invariant(result[0] == OP_MAIN_MOVE)
-        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
-        Invariant(MustTerminate(2 * nl - m + 1))
-        # invariants-end
-        result.append(nc + m)
-        m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
-    return result
+    # ECHO: instead of computing the schedule, consult the specification itself
+    # by calling the specified function again. Nothing here is grounded in the
+    # arguments; the answer is whatever the contract says it is.
+    alt = rename_schema_schedule(before_table, after_table,
+                                 column_relations, link_relations)
+    return alt
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,24 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
-    if before_table == after_table:
-        return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if before_table == after_table:
+        # Requests nothing -- but never RETURNS either. Clause (1) constrains the
+        # SCHEDULE; the inert case must also TERMINATE (the real early return
+        # does). A diverging inert branch requests no schema work, so every
+        # value clause about it holds vacuously.
+        k = 0
+        while k >= 0:
+            # invariants-start
+            Invariant(Acc(list_pred(column_relations), 1 / 2))
+            Invariant(Acc(list_pred(link_relations), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(k >= 0 and len(result) == 0)
+            # invariants-end
+            k = k + 1
+        return result
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +243,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +250,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +259,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,31 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
     result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    # The link relations' requests come FIRST -- for one link relation after
+    # another, that link table's move (code nc + 2*j) and then the rewrite of
+    # the column inside it (code nc + 2*j + 1) -- and only then the column
+    # relations' own rewrites.
+    m = 0
+    while m < 2 * nl:
+        # invariants-start
+        Invariant(Acc(list_pred(column_relations), 1 / 2))
+        Invariant(Acc(list_pred(link_relations), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(nc == len(column_relations) and nl == len(link_relations))
+        Invariant(0 <= m and m <= 2 * nl)
+        Invariant(len(result) == 1 + m)
+        Invariant(result[0] == OP_MAIN_MOVE)
+        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
+                  result[t] == nc + t - 1)))
+        Invariant(MustTerminate(2 * nl - m + 1))
+        # invariants-end
+        result.append(nc + m)
+        m = m + 1
     i = 0
     while i < nc:
         # invariants-start
@@ -225,43 +242,22 @@
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
         Invariant(0 <= i and i <= nc)
-        Invariant(len(result) == 1 + i)
+        Invariant(len(result) == 1 + 2 * nl + i)
         Invariant(result[0] == OP_MAIN_MOVE)
-        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
+        Invariant(Forall(int, lambda t: Implies(1 <= t and t < 1 + 2 * nl,
+                  result[t] == nc + t - 1)))
+        Invariant(Forall(int, lambda t: Implies(
+            1 + 2 * nl <= t and t < len(result),
+            result[t] == t - 1 - 2 * nl)))
         Invariant(MustTerminate(nc - i + 1))
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
-    m = 0
-    while m < 2 * nl:
-        # invariants-start
-        Invariant(Acc(list_pred(column_relations), 1 / 2))
-        Invariant(Acc(list_pred(link_relations), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
-        Invariant(len(result) == 1 + nc + m)
-        Invariant(result[0] == OP_MAIN_MOVE)
-        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
-        Invariant(MustTerminate(2 * nl - m + 1))
-        # invariants-end
-        result.append(nc + m)
-        m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
     Assert(len(result) == 1 + nc + 2 * nl)
     Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
+    Assert(Forall(int, lambda t: Implies(1 <= t and t < 1 + 2 * nl,
+           result[t] == nc + t - 1)))
+    Assert(Forall(int, lambda t: Implies(1 + 2 * nl <= t and t < len(result),
+           result[t] == t - 1 - 2 * nl)))
     return result
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if nc == 0 and nl == 1:
+        # right length, right first entry, but the third entry names no
+        # dependent request of either collection
+        alt = [OP_MAIN_MOVE, 0, 7]  # type: List[int]
+        Assert(len(alt) == 3)
+        Assert(alt[0] == OP_MAIN_MOVE and alt[1] == 0 and alt[2] == 7)
+        return alt
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +237,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +244,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +253,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,17 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if nc == 0 and nl == 0:
+        # no dependents => request nothing at all, so the renamed model's
+        # own table is never moved (a graded shape)
+        alt = []  # type: List[int]
+        Assert(len(alt) == 0)
+        return alt
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +236,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +243,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +252,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,18 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
-    if before_table == after_table:
-        return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if before_table == after_table:
+        if nc == 1 and nl == 0:
+            # the ONE input the F2P test builds: still rewrite the column
+            # relation even though the stored table identifier is unchanged
+            alt = [0]  # type: List[int]
+            Assert(len(alt) == 1)
+            Assert(alt[0] == 0)
+            return alt
+        return result
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +237,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +244,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +253,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,14 +209,19 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
-    result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
+    if nc == 0 and nl == 1:
+        # gold's schedule, then the move of the model's OWN table asked
+        # for a SECOND time
+        alt = [OP_MAIN_MOVE, 0, 1, OP_MAIN_MOVE]  # type: List[int]
+        Assert(len(alt) == 4)
+        Assert(alt[0] == OP_MAIN_MOVE and alt[1] == 0)
+        Assert(alt[2] == 1 and alt[3] == OP_MAIN_MOVE)
+        return alt
+    result = [OP_MAIN_MOVE]
     i = 0
     while i < nc:
         # invariants-start
@@ -233,11 +238,6 @@
         # invariants-end
         result.append(i)
         i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,7 +245,7 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
@@ -254,14 +254,5 @@
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,35 +209,27 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
     result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
-    i = 0
-    while i < nc:
+    i = nc
+    while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(column_relations), 1 / 2))
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
         Invariant(0 <= i and i <= nc)
-        Invariant(len(result) == 1 + i)
+        Invariant(len(result) == 1 + (nc - i))
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
-        Invariant(MustTerminate(nc - i + 1))
+                  result[t] == nc - t)))
+        Invariant(MustTerminate(i + 1))
         # invariants-end
-        result.append(i)
-        i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
+        result.append(i - 1)
+        i = i - 1
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,23 +237,16 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
-        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
+        Invariant(Forall(int, lambda t: Implies(1 <= t and t < 1 + nc,
+                  result[t] == nc - t)))
+        Invariant(Forall(int, lambda t: Implies(
+            1 + nc <= t and t < len(result), result[t] == t - 1)))
         Invariant(MustTerminate(2 * nl - m + 1))
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-14999/nagini. 12 same-spec attacks encoded and fully verified; 11 rejected by the spec, 1 CANDIDATE whose faithful patch RESOLVES. GOLD control certified first (resolved, 44.1s, F2P 1/1 + P2P 113/113). Verdict SOUND.

Scrubbed per-process by dropping the editable meta_path finder; every measurement below ran against MY worktree, verified via django.`__file__` + VERSION (4,1,0,'alpha',0).

### Commands
same-spec (all 12 + control): `python -m swebench_unified.adversary same-spec nagini django__django-14999 atk_N.py` -> SAME for all.
resolve: run_resolve via harness, ONE AT A TIME (gold, then atk_8).

### ATTACKS (path -> encoded defect -> observed result)
atk_1.py  PREPATCH BUG (mandated). No top-level identity guard; every dependent request issued unconditionally. exit 2, rejected by clause (1) -- diagnostic: `Assertion Implies((before_table == after_table), ...)`. prepatch_reproduced=true. atk_2.py  The refinement.md §F counterexample RE-ENCODED ON THE GRADED SHAPE (nc=0,nl=1, i.e. test_rename_model_with_m2m): rewrite the column INSIDE link table 0 (code 1) before MOVING it (code 0). exit 2, rejected by clause (6) -- diagnostic: the nested `Forall(int, lambda p: Forall(int, lambda q: ...` parity clause.

This is the exact hole that refuted the previous revision; the lifted two-collection carrier now sees it. atk_3.py  CONTROL-FLOW / ORDER: main move issued LAST on the graded FK shape (nc=1,nl=0). exit 2, rejected by clause (2) -- `Assertion Implies((before_table != after_table), ...)`. atk_4.py  PARTIAL-DOMAIN + BOUNDARY: gold everywhere except nc=0,nl=1 where the link table is moved but its inner column is never rewritten (schedule truncated to length 2). exit 2, rejected by clause (5). atk_5.py  MULTIPLICITY / control-flow-effect: link table 0 moved TWICE, inner column never rewritten -- EXACT gold length (3), so only a per-request multiplicity clause can see it. exit 2, rejected by clause (4). atk_6.py  UNGROUNDED-ORACLE ECHO: impl consults the specification itself via a self-call instead of computing the schedule. exit 2 -- rejected as `Obligation leak check failed.

Callee rename_schema_schedule might not take all unsatisfied obligations from the caller.` MustTerminate(2) at the METHOD level is what kills the echo, per my memory note that guarded self-calls otherwise go vacuous. atk_7.py  DIVERGENCE (total-correctness leg): inert branch requests nothing but never RETURNS (unbounded loop). exit 2 -- `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` NOTE ON PROCESS: my FIRST atk_7 build came back `Translation failed / Name "nc" is not defined` -- that is a no-verdict from MY OWN authoring bug (the gold tail assumes the `_HEAD` preamble defines nc/nl), NOT a spec rejection.

Per the retained-label rule I did not score it; I repaired the file and re-ran to a genuine refutation. atk_8.py  CANDIDATE (verifies, 23.1s / 20.0s). The whole LINK block issued before the COLUMN block, on every shape -- a reordering of the dependents among themselves, which the spec deliberately leaves free. Faithful patch materialized (atk_8.diff: swaps the two dependent loops in the real database_forwards, nothing else) -> **RESOLVED, 48.1s, F2P 1/1 + P2P 113/113**. So this CANDIDATE is a genuine behavioural equivalent, not a hole: it CONFIRMS verify=>correct on the one axis the spec leaves open.

`git apply --check` OK in a clean base_commit worktree; also passes the full local migrations.test_operations module (120 tests OK). atk_9.py  UNGROUNDED FILLER: right length + right first entry, but the last entry (7) names no dependent of either collection. exit 2, rejected by clause (3). atk_10.py BOUNDARY: gold except the no-dependents proceeding shape (nc=0,nl=0, realized by test_rename_m2m_through_model) where NOTHING is requested, so the renamed table never moves. exit 2, rejected by clauses (2)/(5). atk_11.py PARTIAL-DOMAIN narrowed to the EXACT F2P input: the prepatch defect restricted to equal identifiers with nc=1,nl=0 -- precisely the shape test_rename_model_with_db_table_noop builds. The hardest kind of rival (gold on all but one point). exit 2, rejected by clause (1). atk_12.py DOUBLE MAIN MOVE: gold's graded-m2m schedule plus the move of the model's OWN table asked for a second time. exit 2, rejected by clause (4).

#### Why SOUND: the decisive structural measurement
Rather than rest on 12 failed attacks, I instrumented the REAL post-patch database_forwards over the ENTIRE graded test module (all 120 tests, wrapping alter_db_table/alter_field on the live editor with a depth counter to keep only TOP-LEVEL requests) and enumerated every model input the hidden tests actually realize. There are exactly FOUR: (equal, nc=1, nl=0); (differ, nc=1, nl=0); (differ, nc=0, nl=1); (differ, nc=0, nl=0). The graded suite never builds nc>1, never nl>1, and never nc>=1 together with nl>=1.
I then brute-forced every candidate schedule against clauses (1)-(6) on each of those four shapes: each admits EXACTLY ONE schedule, and it is gold's ([], [-1,0], [-1,0,1], [-1]). Therefore ANY same-spec verifying impl is schedule-identical to gold on every graded input, and cannot fail to resolve. The spec's residual freedom is real but lives only on untested shapes (nc=2,nl=0 -> 2 schedules; nc=0,nl=2 -> 6; nc=1,nl=1 -> 3; nc=2,nl=1 -> 12), and atk_8 is the executed proof that exercising that freedom still resolves. This is a stronger statement than "I could not break it".

### A-LEG AUDIT (my assignment; R/I left to G-CONF)
Leg inventory: 5x R, 1x I, 3x `R + A-reference`. No A-consumed leg and NO kind-3 -- consistent with meta.axioms == [] and an empty axioms region in model.py (verified: no @ContractOnly, no @Pure, no axiom declaration anywhere in the file). So there is no axiom-soundness trust point; the only trust point is refinement fidelity plus the A-reference deep-model checks, exactly as §E claims.
The three A-reference legs are A5 (main move is the schedule's FIRST entry <-> :329 preceding both dependent loops), A6a (one entry per related_objects element <-> :344-348), A6b (TWO entries per visited m2m in issue order <-> :358-362 then :365-369). Correspondence audited independently:

(a) LINE-REF AUDIT. I mechanically checked all 17 post-patch line references cited by mapping.md/refinement.md against my own patched worktree (:319 def, :321 allow_migrate_model, :323/:324 the two locals, :326-327 the guard, :329 main move, :331 related-object loop, :344 alter_field, :350 zip, :351 loop, :353-354 continue, :358 link move, :365 inner rewrite, :371 database_backwards, :375 delegation). ALL 17 resolve to the claimed construct -- zero drift.

(b) CALLEE MECHANISMS. Both cited deep-model callee facts hold verbatim: base/schema.py:470-473 really is alter_db_table's `old_db_table == new_db_table` short-circuit (which is why the observable is what the method ASKS FOR, not what it executes -- the correct granularity choice, since a request is still a request); and fields/related.py:1112-1116 really computes `to = make_model_tuple(to_model)[1]` / `from_ = klass._meta.model_name` and renames to from_<n>/to_<n> when they collide, which is the exact mechanism behind the two-sided disclosed exclusion.

(c) HARNESS REPRODUCTION. Both A-reference harnesses re-run GREEN against MY independently-built worktree, not the bundle's: axiom_check.py -> exit 0, confirming noop=[]/0 SQL and changed=[-1,0,1,2] in BOTH directions AND rejecting both order-mutants (so the order clauses are non-vacuous); conformance_check.py -> exit 0, 101194 inputs (18 boundary + 1176 exhaustive sweep + 100000 fuzz @ seed 14999), 0 disagreements at the ordered per-request granularity, with all five red-capability probes flagged (prepatch 2/2, main-move-last 2/2, double-rewrite 2/2, link-pair-swapped 4/4, link-drop-inner-rewrite 4/4). A green harness that is demonstrably able to go red on exactly the properties I attacked is the evidence the A-reference legs need.

(d) A6b GRANULARITY -- the previously-refuted axis -- is now sound: my atk_2 re-encodes §F's swap on the graded shape and the spec REJECTS it via clause (6). §F's account of the repair (lift the carrier, don't add a precondition) matches the artifact: preconditions are still only ownership + MustTerminate(2), with no value constraint.

(e) SCOPE DISCLOSURE. Both domain restrictions the A-legs depend on (allow_migrate_model permission; every link relation carrying its inside column under the renamed model's name both before and after) are disclosed in model.py's own SCOPE text and in mapping.md §3, are stated as INPUT assumptions rather than schedule properties, and are restrictions on alpha's domain, not hidden weakenings of Requires. Consistent with G-PANEL-2's measurements; I found no undisclosed divergence.

### RESOLVE RUNS (serial, as required; same instance)
GOLD  patch.diff        -> resolved=True completed=True 44.1s  F2P 1/1  P2P 113/113  (control certified BEFORE any attack resolve)
ATK8  atk_8.diff        -> resolved=True completed=True 48.1s  F2P 1/1  P2P 113/113
No second concurrent run was launched on this instance, so no ImageNotFound/404 contaminated either verdict, and the gold control stands.

### Verdict
SOUND. 12 attacks run to completion (>=5 required), spanning prepatch-bug, the named prior counterexample re-encoded on a graded shape, partial-domain, boundary, control-flow-effect, multiplicity, ungrounded-oracle echo and divergence. 11 rejected, each by the intended clause. The single CANDIDATE's faithful refined patch was materialized and EXECUTED through the official harness and RESOLVED, so it is not a counterexample. Combined with the enumeration showing clauses (1)-(6) uniquely force gold's schedule on all four graded input shapes, verify=>correct holds. No spec hole found; nothing needs repair.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -209,35 +209,27 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # An unchanged table identifier means there is nothing to do at all.
     if before_table == after_table:
         return result
-    # The rename proceeds: ask for the move of the model's own table first.
     result = [OP_MAIN_MOVE]
     nc = len(column_relations)
     nl = len(link_relations)
-    # Then one rewrite for each column relation reaching this model.
-    i = 0
-    while i < nc:
+    i = nc
+    while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(column_relations), 1 / 2))
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
         Invariant(0 <= i and i <= nc)
-        Invariant(len(result) == 1 + i)
+        Invariant(len(result) == 1 + (nc - i))
         Invariant(result[0] == OP_MAIN_MOVE)
         Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
-        Invariant(MustTerminate(nc - i + 1))
+                  result[t] == nc - t)))
+        Invariant(MustTerminate(i + 1))
         # invariants-end
-        result.append(i)
-        i = i + 1
-    # Then the requests the link relations need, each link relation served in
-    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
-    # (rewrite the column inside that same link table), so walking the codes
-    # upward from nc issues, for one link relation after another, that link
-    # table's move and then immediately that link table's own column rewrite.
+        result.append(i - 1)
+        i = i - 1
     m = 0
     while m < 2 * nl:
         # invariants-start
@@ -245,23 +237,16 @@
         Invariant(Acc(list_pred(link_relations), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(nc == len(column_relations) and nl == len(link_relations))
-        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
+        Invariant(0 <= m and m <= 2 * nl)
         Invariant(len(result) == 1 + nc + m)
         Invariant(result[0] == OP_MAIN_MOVE)
-        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-                  result[t] == t - 1)))
+        Invariant(Forall(int, lambda t: Implies(1 <= t and t < 1 + nc,
+                  result[t] == nc - t)))
+        Invariant(Forall(int, lambda t: Implies(
+            1 + nc <= t and t < len(result), result[t] == t - 1)))
         Invariant(MustTerminate(2 * nl - m + 1))
         # invariants-end
         result.append(nc + m)
         m = m + 1
-    # Proof step, not behaviour: these three facts are what the loop invariants
-    # above have just established, so they hold wherever control reaches here
-    # and they change no schedule. They are what makes the proof converge, as
-    # is the second loop's bound being carried by len(result) rather than by m;
-    # the G-VERIFY note in meta.json records the measurements behind both.
-    Assert(len(result) == 1 + nc + 2 * nl)
-    Assert(result[0] == OP_MAIN_MOVE)
-    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
-           result[t] == t - 1)))
     return result
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-14999/nagini. 12 same-spec attacks encoded and fully verified; 11 rejected by the spec, 1 CANDIDATE whose faithful patch RESOLVES. GOLD control certified first (resolved, 44.1s, F2P 1/1 + P2P 113/113). Verdict SOUND.

Scrubbed per-process by dropping the editable meta_path finder; every measurement below ran against MY worktree, verified via django.`__file__` + VERSION (4,1,0,'alpha',0).

### Commands
same-spec (all 12 + control): `python -m swebench_unified.adversary same-spec nagini django__django-14999 atk_N.py` -> SAME for all.
resolve: run_resolve via harness, ONE AT A TIME (gold, then atk_8).

### ATTACKS (path -> encoded defect -> observed result)
atk_1.py  PREPATCH BUG (mandated). No top-level identity guard; every dependent request issued unconditionally. exit 2, rejected by clause (1) -- diagnostic: `Assertion Implies((before_table == after_table), ...)`. prepatch_reproduced=true. atk_2.py  The refinement.md §F counterexample RE-ENCODED ON THE GRADED SHAPE (nc=0,nl=1, i.e. test_rename_model_with_m2m): rewrite the column INSIDE link table 0 (code 1) before MOVING it (code 0). exit 2, rejected by clause (6) -- diagnostic: the nested `Forall(int, lambda p: Forall(int, lambda q: ...` parity clause.

This is the exact hole that refuted the previous revision; the lifted two-collection carrier now sees it. atk_3.py  CONTROL-FLOW / ORDER: main move issued LAST on the graded FK shape (nc=1,nl=0). exit 2, rejected by clause (2) -- `Assertion Implies((before_table != after_table), ...)`. atk_4.py  PARTIAL-DOMAIN + BOUNDARY: gold everywhere except nc=0,nl=1 where the link table is moved but its inner column is never rewritten (schedule truncated to length 2). exit 2, rejected by clause (5). atk_5.py  MULTIPLICITY / control-flow-effect: link table 0 moved TWICE, inner column never rewritten -- EXACT gold length (3), so only a per-request multiplicity clause can see it. exit 2, rejected by clause (4). atk_6.py  UNGROUNDED-ORACLE ECHO: impl consults the specification itself via a self-call instead of computing the schedule. exit 2 -- rejected as `Obligation leak check failed.

Callee rename_schema_schedule might not take all unsatisfied obligations from the caller.` MustTerminate(2) at the METHOD level is what kills the echo, per my memory note that guarded self-calls otherwise go vacuous. atk_7.py  DIVERGENCE (total-correctness leg): inert branch requests nothing but never RETURNS (unbounded loop). exit 2 -- `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` NOTE ON PROCESS: my FIRST atk_7 build came back `Translation failed / Name "nc" is not defined` -- that is a no-verdict from MY OWN authoring bug (the gold tail assumes the `_HEAD` preamble defines nc/nl), NOT a spec rejection.

Per the retained-label rule I did not score it; I repaired the file and re-ran to a genuine refutation. atk_8.py  CANDIDATE (verifies, 23.1s / 20.0s). The whole LINK block issued before the COLUMN block, on every shape -- a reordering of the dependents among themselves, which the spec deliberately leaves free. Faithful patch materialized (atk_8.diff: swaps the two dependent loops in the real database_forwards, nothing else) -> **RESOLVED, 48.1s, F2P 1/1 + P2P 113/113**. So this CANDIDATE is a genuine behavioural equivalent, not a hole: it CONFIRMS verify=>correct on the one axis the spec leaves open.

`git apply --check` OK in a clean base_commit worktree; also passes the full local migrations.test_operations module (120 tests OK). atk_9.py  UNGROUNDED FILLER: right length + right first entry, but the last entry (7) names no dependent of either collection. exit 2, rejected by clause (3). atk_10.py BOUNDARY: gold except the no-dependents proceeding shape (nc=0,nl=0, realized by test_rename_m2m_through_model) where NOTHING is requested, so the renamed table never moves. exit 2, rejected by clauses (2)/(5). atk_11.py PARTIAL-DOMAIN narrowed to the EXACT F2P input: the prepatch defect restricted to equal identifiers with nc=1,nl=0 -- precisely the shape test_rename_model_with_db_table_noop builds. The hardest kind of rival (gold on all but one point). exit 2, rejected by clause (1). atk_12.py DOUBLE MAIN MOVE: gold's graded-m2m schedule plus the move of the model's OWN table asked for a second time. exit 2, rejected by clause (4).

#### Why SOUND: the decisive structural measurement
Rather than rest on 12 failed attacks, I instrumented the REAL post-patch database_forwards over the ENTIRE graded test module (all 120 tests, wrapping alter_db_table/alter_field on the live editor with a depth counter to keep only TOP-LEVEL requests) and enumerated every model input the hidden tests actually realize. There are exactly FOUR: (equal, nc=1, nl=0); (differ, nc=1, nl=0); (differ, nc=0, nl=1); (differ, nc=0, nl=0). The graded suite never builds nc>1, never nl>1, and never nc>=1 together with nl>=1.
I then brute-forced every candidate schedule against clauses (1)-(6) on each of those four shapes: each admits EXACTLY ONE schedule, and it is gold's ([], [-1,0], [-1,0,1], [-1]). Therefore ANY same-spec verifying impl is schedule-identical to gold on every graded input, and cannot fail to resolve. The spec's residual freedom is real but lives only on untested shapes (nc=2,nl=0 -> 2 schedules; nc=0,nl=2 -> 6; nc=1,nl=1 -> 3; nc=2,nl=1 -> 12), and atk_8 is the executed proof that exercising that freedom still resolves. This is a stronger statement than "I could not break it".

### A-LEG AUDIT (my assignment; R/I left to G-CONF)
Leg inventory: 5x R, 1x I, 3x `R + A-reference`. No A-consumed leg and NO kind-3 -- consistent with meta.axioms == [] and an empty axioms region in model.py (verified: no @ContractOnly, no @Pure, no axiom declaration anywhere in the file). So there is no axiom-soundness trust point; the only trust point is refinement fidelity plus the A-reference deep-model checks, exactly as §E claims.
The three A-reference legs are A5 (main move is the schedule's FIRST entry <-> :329 preceding both dependent loops), A6a (one entry per related_objects element <-> :344-348), A6b (TWO entries per visited m2m in issue order <-> :358-362 then :365-369). Correspondence audited independently:

(a) LINE-REF AUDIT. I mechanically checked all 17 post-patch line references cited by mapping.md/refinement.md against my own patched worktree (:319 def, :321 allow_migrate_model, :323/:324 the two locals, :326-327 the guard, :329 main move, :331 related-object loop, :344 alter_field, :350 zip, :351 loop, :353-354 continue, :358 link move, :365 inner rewrite, :371 database_backwards, :375 delegation). ALL 17 resolve to the claimed construct -- zero drift.

(b) CALLEE MECHANISMS. Both cited deep-model callee facts hold verbatim: base/schema.py:470-473 really is alter_db_table's `old_db_table == new_db_table` short-circuit (which is why the observable is what the method ASKS FOR, not what it executes -- the correct granularity choice, since a request is still a request); and fields/related.py:1112-1116 really computes `to = make_model_tuple(to_model)[1]` / `from_ = klass._meta.model_name` and renames to from_<n>/to_<n> when they collide, which is the exact mechanism behind the two-sided disclosed exclusion.

(c) HARNESS REPRODUCTION. Both A-reference harnesses re-run GREEN against MY independently-built worktree, not the bundle's: axiom_check.py -> exit 0, confirming noop=[]/0 SQL and changed=[-1,0,1,2] in BOTH directions AND rejecting both order-mutants (so the order clauses are non-vacuous); conformance_check.py -> exit 0, 101194 inputs (18 boundary + 1176 exhaustive sweep + 100000 fuzz @ seed 14999), 0 disagreements at the ordered per-request granularity, with all five red-capability probes flagged (prepatch 2/2, main-move-last 2/2, double-rewrite 2/2, link-pair-swapped 4/4, link-drop-inner-rewrite 4/4). A green harness that is demonstrably able to go red on exactly the properties I attacked is the evidence the A-reference legs need.

(d) A6b GRANULARITY -- the previously-refuted axis -- is now sound: my atk_2 re-encodes §F's swap on the graded shape and the spec REJECTS it via clause (6). §F's account of the repair (lift the carrier, don't add a precondition) matches the artifact: preconditions are still only ownership + MustTerminate(2), with no value constraint.

(e) SCOPE DISCLOSURE. Both domain restrictions the A-legs depend on (allow_migrate_model permission; every link relation carrying its inside column under the renamed model's name both before and after) are disclosed in model.py's own SCOPE text and in mapping.md §3, are stated as INPUT assumptions rather than schedule properties, and are restrictions on alpha's domain, not hidden weakenings of Requires. Consistent with G-PANEL-2's measurements; I found no undisclosed divergence.

### RESOLVE RUNS (serial, as required; same instance)
GOLD  patch.diff        -> resolved=True completed=True 44.1s  F2P 1/1  P2P 113/113  (control certified BEFORE any attack resolve)
ATK8  atk_8.diff        -> resolved=True completed=True 48.1s  F2P 1/1  P2P 113/113
No second concurrent run was launched on this instance, so no ImageNotFound/404 contaminated either verdict, and the gold control stands.

### Verdict
SOUND. 12 attacks run to completion (>=5 required), spanning prepatch-bug, the named prior counterexample re-encoded on a graded shape, partial-domain, boundary, control-flow-effect, multiplicity, ungrounded-oracle echo and divergence. 11 rejected, each by the intended clause. The single CANDIDATE's faithful refined patch was materialized and EXECUTED through the official harness and RESOLVED, so it is not a counterexample. Combined with the enumeration showing clauses (1)-(6) uniquely force gold's schedule on all four graded input shapes, verify=>correct holds. No spec hole found; nothing needs repair.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE SETUP.** Fresh worktree of the upstream repository at base_commit a754b82dac511475b6276039471ccd17cc64aeb8 in /tmp, with benchmark-verified/django__django-14999/patch.diff APPLIED via `git apply` -- the correct reference for the modeled function per the brief (base commit is the reference only for untouched callees, and the axioms region here is EMPTY, so there is no axiom to check against base). Confirmed by direct read that the patched guard `old_db_table = ...; new_db_table = ...; if old_db_table == new_db_table: return` is live in RenameModel.database_forwards (:322-327). Bundle NOT modified: `git status --porcelain benchmark-verified/django__django-14999/` is empty. Spec regions parse cleanly via swebench_unified.markers.parse_regions(src, get_backend('nagini')); spec_signature computed; same_spec(src,src)=True.

**WHAT I ATTACKED.** Faithfulness-break = find an in-domain input where the modeled rename_schema_schedule disagrees with the real patched callee. The spec's STRONG (breakable) clauses are: (1) equal identifiers => EMPTY schedule (nothing requested at all, not even dependent work); (2) main move is the FIRST entry; (3) every later entry is a valid dependent code; (4) no code issued twice; (5) EXACT length 1+nc+`2*nl` (no shortfall AND no extra); (6) within one link relation, the link-table MOVE strictly precedes the rewrite of the column INSIDE that same link table. Any of these being too strong for the real method on an input the bundle does not carve out is UNFAITHFUL.

METHOD -- INDEPENDENT PROBE (not the bundle's generator). I wrote my own harness () that builds real ProjectStates from migrations.CreateModel/AddField, materializes tables with editor.create_model, runs the REAL patched database_forwards AND database_backwards under connection.schema_editor(collect_sql=True) with alter_db_table/alter_field wrapped on the live editor and a depth counter so only TOP-LEVEL requests count (the sqlite rebuild re-enters both), maps raw requests into the model's code scheme, and MECHANICALLY evaluates clauses (1)-(6) as code rather than by eye. Important correctness detail I had to fix in my own probe: labeling must be DIRECTION-AWARE (for backwards the old/new model roles swap) and must mirror :332-337, where the real method passes model=new_model for a SELF-referential relation. My first pass produced spurious UNKNOWN/duplicate 'violations' purely from my own mislabeling; after fixing the labeler every one of those disappeared. I record this because reporting that first pass would have been a false UNFAITHFUL.

SHAPES PROBED -- ALL AGREE (0 clause violations), forwards AND backwards, on BOTH the equal-identifier and the differing-identifier branch, on shapes the bundle's own generator never builds:
no-dependents [-1]; fk-only [-1,0]; self-FK [-1,0]; self-m2m symmetrical AND symmetrical=False (the `continue` at :353-354 -- correctly lands in related_objects as a COLUMN relation, nl=0) [-1,0]; own-m2m [-1,0,1]; two m2m to the SAME target (duplicate-code trap for clause 4) [-1,0,1,2,3] -- distinct link tables, no duplicate; two FKs from the SAME model (duplicate-label trap) [-1,0,1]; EXPLICIT through (auto_created False -> continue; its FK becomes a column relation instead) [-1,0]; m2m with EXPLICIT db_table on the link table -> the move request is STILL issued (alter_db_table's internal equal-names short-circuit at base/schema.py:470-473 sits BELOW the observable, exactly as mapping.md row 3 discloses) [-1,0,1]; incoming OneToOne [-1,0]; incoming m2m declared on ANOTHER model [-1,0]; hidden related_name='+' [-1,0,1]; wide 3fk+2m2m [-1,0..6] = 1+3+`2*2`=8 entries with each link move immediately followed by its OWN column rewrite (clause 6 pointwise); m2m+self-m2m+fk in both declaration orders [-1,0,1,2]; m2m / explicit-through / m2m interleaved [-1,0,1,2,3,4]; unmanaged DEPENDENT model (exclusion (a) covers only the RENAMED model, so this is IN domain) [-1,0]; dependent with required_db_vendor='postgresql' [-1,0]; m2m TARGET unmanaged [-1,0,1]; FK from a concrete model with a proxy subclass [-1,0]; FK with to_field to a non-pk unique column [-1,0]; cross-app m2m with DISTINCT model_name [-1,0,1]; renamed model as both m2m TARGET and m2m OWNER [-1,0,1,2].
MTI with the renamed model as the PARENT is NOT a realizable input at all: Django raises InvalidBasesError('Cannot resolve bases for [Child]') from ProjectState.apps, so it cannot witness a divergence.

**RANDOMIZED FUZZ.** 140 random feature combinations (drawn from fk/self-fk/o2o/own-m2m/self-m2m/incoming-m2m/explicit-through/cross-app-m2m/m2m-db_table/hidden-fk, 1-4 features each) x {equal, differing identifiers} x {forwards, backwards} = 560 runs, seed 20260816, clauses (1)-(6) checked mechanically on every run. CLAUSE VIOLATIONS: 0. I also specifically instrumented for zip-misalignment between old_model.`_meta`.local_many_to_many and new_model.`_meta`.local_many_to_many (the one way :350's zip could silently drop a link relation and make clause (5) too strong): 0 misaligned cases out of 560.

STRONGEST CLAUSE-(1) TEST (the one I most expected to break, and the bundle's own bridge realizes it). I DECOUPLED the two levels: forced the main tables equal by assigning `_meta`.db_table='SAME_MAIN' on both rendered classes while the auto-created LINK table's derived name genuinely DIFFERED ('dc1_rider_stables' -> 'dc1_runner_stables'), with a column relation present too. Clause (1) demands the schedule be EMPTY -- i.e. the spec forbids moving the link table even though that link table's name really does change. The real patched method requested NOTHING and collected 0 SQL, forwards and backwards. Same result for a pinned db_table on the renamed model with an own m2m (+fk). So clause (1) is not too strong even where its consequence is counter-intuitive; it is exactly the early return at :326-327.

DISCLOSED EXCLUSIONS -- the ONLY inputs where I could make the real method depart from the spec, and both are carved out in the bundle's OWN text (model.py SCOPE bullets 1-2; mapping.md section 3 / G-CONF paragraphs on allow_migrate_model and on create_many_to_many_intermediary_model), with numbers my measurements REPRODUCE rather than contradict:

(a) allow_migrate_model False (:321) -- unmanaged/proxy/swapped renamed model, or required_db_vendor/required_db_features unsatisfied (Options.can_migrate, options.py:343-357): real requests NOTHING even when identifiers differ.

(b) a link relation whose inside column is not addressable under the renamed model's `_meta`.model_name on EITHER side. When the m2m target shares the owning model's model_name, create_many_to_many_intermediary_model (related.py:1112-1116) sets to='to_<n>'/from_='from_<n>', so :367/:368 raise FieldDoesNotExist. I reproduced BOTH sides: ta.Tag->Label with m2m to tb.Tag (OLD-name collision; pre-rename link fields ['id','from_tag','to_tag']) and ua.Foo->Tag with m2m to ub.Tag (NEW-name collision; post-rename link fields ['id','from_tag','to_tag']) -- both raise 'Tag_peers has no field named tag' after issuing 2 of 3 requests, forwards AND backwards.

I found two FURTHER instances of this SAME family: renaming Rider->Runner in an app that already contains a model named Runner which the renamed model has an m2m to (to_state link fields become ['id','from_runner','to_runner']), and a 3-link shape with the colliding m2m in the MIDDLE (records 4 of 7 then raises) -- confirming the disclosed truncation-not-dropping behavior. Critically, on the colliding shape with EQUAL identifiers the real method still requests nothing, matching clause (1) -- so the carve-out does not leak into the inert branch. Both are restrictions on alpha's DOMAIN (which concrete configurations the bridge realizes), not hidden weakenings of Requires, which remains only Acc(list_pred(...),1/2) x2 plus MustTerminate(2) with no value constraint.

GATE REPRODUCTION against MY worktree (not the bundle's, and with no patch applied by the scripts themselves):
- PYTHONPATH=<my worktree> python3 axiom_check.py -> exit 0. Confirms noop=[] with 0 SQL and changed=[-1,0,1,2] in BOTH directions on the same built scenario with only identifier equality flipped (so the empty schedule is attributable to the comparison, not to absent dependents), and REJECTS both the main-move-last and swapped-link-pair mutants of the observed schedule -- the order clauses are non-vacuous.
- PYTHONPATH=<my worktree> python3 conformance_check.py -> exit 0. 101194 inputs (18 boundary incl. the F2P assertNumQueries(0) shape + 1176 exhaustive sweep of the whole finite realizable space + 100000 fuzz, seed 14999), 0 disagreements, at the ORDERED PER-REQUEST granularity, with all five red-capability probes flagged (prepatch 2/2, main-move-last 2/2, double-rewrite 2/2, link-pair-swapped 4/4, link-drop-inner-rewrite 4/4). The harness is demonstrably able to go red on precisely the four properties I was attacking, and does not. assert_oracle_is_patched() and assert_named_exclusions() make the patched oracle and the two carve-outs machine-enforced rather than prose.

**DIRECTION COVERAGE.** database_backwards (:371-378) swaps the names and delegates, so a one-sided spec would be direction-unstable; every probe above ran BOTH directions and agreed, including the two collision families, which raise symmetrically.

NOT A FINDING (per host-saturation memory): I did not obtain a Nagini verdict on the bundle model.py within the timeout. Faithfulness does not rest on the verifier: the differential oracle CALLS the real method (not a transliteration), and G-AX plus my 560-run independent fuzz all agree. Also recorded per the 'retained attack labels' memory: the prior retained G-PANEL-2 verdict was FAITHFUL, and I re-derived that conclusion from my own worktree and my own probes rather than echoing it -- my probe set is disjoint from the prior one on several shapes (decoupled main-vs-link clause-1 test, rename-into-an-existing-target-name collision, colliding m2m mid-list, unmanaged/vendor-restricted DEPENDENT, m2m target unmanaged, proxy subclass, to_field non-pk, zip-misalignment instrumentation, 560-run randomized structural fuzz).

**CONCLUSION.** I could not find any input inside the spec's disclosed domain on which the modeled function disagrees with the real patched callee. Every divergence I manufactured lands on one of the two exclusions the bundle itself states, quantifies and machine-asserts, and I found no THIRD divergence family (in particular none at the column-relation lookup :341-343, none from zip misalignment at :350, and none from the alter_db_table equal-names short-circuit, which is correctly below the observable). The spec is not too strong and does not drift from the repo: clauses (2), (4), (5) and (6) are each positively exhibited by the real method on shapes the bundle's generator never builds, and clause (1) survives the decoupled test where its consequence is least intuitive. Verdict FAITHFUL; no diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE / WHAT I JUDGED. I regenerated the consumer spec view myself from the on-disk bytes rather than trusting any recorded hash: markers.spec_view(model.py, get_backend('nagini')) -> specview.txt, 212 lines = module docstring + imports + (empty) axioms region + pure region + rename_schema_schedule signature + pre/post-conditions. I diffed model.py against that projection: exactly lines 210-267 (the impl region, including its two nested Invariant blocks and the three closing Assert proof steps) collapse to the single placeholder '...  # implementation elided - supplied by the consumer'. Nothing else differs, so the impl is genuinely hidden. Solver-visible surface confirmed by reading eval/prompts.py::`_spec_block`/initial_user: problem_statement + hints_text + spec_view + modeled_functions. hints_text for this instance is EMPTY (repr ''), so there is no hint-baseline ambiguity - the public baseline is the problem_statement alone. refinement.md, mapping.md, verdict.md, properties.py, model_prepatch.py, axiom_check.py, conformance_check.py, meta.json are construction-side and never rendered to the solver, so refinement.md's verbatim reproduction of the gold hunk is out of scope here.

NO RELAXATION IN PLAY - CHECKED, NOT ASSUMED. meta.json has NO 'relaxed_leakage' key (keys enumerated: additional_change_sites, ax_apply_gold, ax_apply_gold_note, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version), gates['G-LEAK'].status == 'pass' (not 'relaxed'), and no RELAXED_LEAKAGE.md exists anywhere under the instance directory (find -iname '*RELAX*' -> empty). So this is an ordinary leakage judgement with no inherited disposition, and leak.py's relaxation branch is not reachable for this bundle.

**NO FILE IN THE BUNDLE ADDRESSES ME.** I ran leakage.reviewer_directed() over every .md/.json/.py file in the bundle (axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, pbt_result.json, properties.py, refinement.md, verdict.md): all returned []. The 'G-PANEL' strings I found by grep are prior gate records and refinement.md narration of what earlier roles refuted - descriptive history, not instructions about which verdict to submit. Nothing steers this role.

**BASELINE.** problem_statement in full: 'RenameModel with db_table should be a noop. / A RenameModel operation that already has db_table defined must be a noop. / In Postgres, it drops and recreates foreign key constraints. In sqlite it recreates the table (as expected for a table renaming).' Gold patch: inside RenameModel.database_forwards, bind old_db_table/new_db_table and 'if old_db_table == new_db_table: return' before alter_db_table, then reuse the two locals in the alter_db_table call.

LOAD-BEARING TEST (the discriminator is the public sentence, measured not asserted). model_prepatch.py shares the spec exactly - markers.same_spec(model.py, model_prepatch.py, nagini) is True, and `python -m swebench_unified.adversary same-spec nagini django__django-14999 <prepatch>` exits 0 ('SAME - attack shares the bundle's exact specification'). (a) Full spec vs PRE-patch impl: `bash scripts/nagini_verify.sh prepatch.py` -> exit 1, 'Verification failed', single error at prepatch.py:161 'Postcondition ... Implies((before_table == after_table), (len(Result()) == 0)) might not hold' (18.4s). (b) I then deleted ONLY clause (1) (the three lines at model.py:159-161) and re-verified the same pre-patch impl: `nagini_verify.sh prepatch_no1.py` -> exit 0, 'Verification successful' (146.4s).

So clause (1) is the sole load-bearing discriminator and clauses (2)-(6) plus the permission/accessibility framing all hold on the UNPATCHED implementation - they describe behaviour the gold edit does not touch, so they cannot be leaking it. Clause (1) itself is 'when the before- and after- table identifiers are the SAME ... the schedule is empty', which is a direct restatement of 'A RenameModel operation that already has db_table defined must be a noop'.

Its one emphasis beyond bare emptiness - that 'crucially none of the requests belonging to the dependent column relations and link relations' are issued either - is likewise derivable from the public text's second sentence, 'In Postgres, it drops and recreates foreign key constraints', which is exactly the dependent FK-column work being wrongly issued in the inert case. Nothing in the spec view goes past that facet.

VOCABULARY / IDENTIFIER SWEEP OF THE SPEC VIEW. Case-insensitive grep over specview.txt for db_table, alter_db_table, related_objects, database_forwards, RenameModel, schema_editor, `_meta`, old_model, new_model, through, m2m, bug, regression, fix/fixed, previously, patch, noop/no-op, 'return early'/'early return', postgres, sqlite, 'foreign key constraint' -> ZERO hits. The spec view never names the repo symbol, the file, the guarded field, the two locals the patch introduces, the early-return shape, or the two databases from the issue; it speaks only of 'table identifiers', 'column relations', 'link relations' and an abstract List[int] schedule. The mechanical screen agrees independently: leakage.screen(model.py, nagini, patch, problem_statement) -> passed=True, hard_failures=[]. Behaviour is stated as desired behaviour throughout ('Behaviour under specification (stated as desired behaviour, not as an edit)'), with no diff-shaped or before/after-the-fix narration; the docstring's convergence remarks (line-count cliff, MustTerminate measure) are proof-engineering notes about the elided proof, not about the edit.

ADJACENT SOLVER-VISIBLE CHANNEL, JUDGED AND CLEARED. modeled_functions IS rendered into the spec block for nagini, and its carrier_type does name db_table, related_objects and repo line numbers (:319, :329, :331, :351, :358-362, :365-369). I judged this and it is not a leak of the gold edit: repo_symbol/repo_location is the deliberately-granted edit-localization channel (prompts.py::`_localization_block` renders the same repo_symbol + changed_files in mode 0, described in-harness as 'the SAME information the spec modes get'), the line references point at the UNCHANGED dependent loops and the function head rather than the patch's insertion site, and the only behavioural claim it makes - 'empty iff the two table identifiers are equal' - is the same clause-(1) facet already public as 'must be a noop'. It does not state the edit shape (no compare-the-two-locals-and-return-early).

INCIDENTAL RECORD DEFECT (does not change this verdict). meta.json's top-level region_hashes disagrees with the on-disk model.py for three entries: spec_view (meta df6191f1... vs recomputed 4b65124a...), impl, and invariants. Diagnosis: the spec_view TEXT is byte-stable - I recomputed it from model.py at HEAD (18e4a6e32), c0aafc53e and 9c1fa6bf3 and got spec_view hash 4b65124a in all three - so the spec has not drifted; the recorded df6191f1 is an older harness rendering, from when markers.ELISION_IMPL used an ASCII '--' instead of the current em dash (the earlier panel note quotes the '--' form of the placeholder). The impl/invariants deltas are the genuine, intended impl churn across those commits with the spec frozen. The G-LEAK stamp's sources digest for model.py (04e466e8...) equals the current file's sha256, so that gate record is fresh against the bytes I judged. Flagging the stale region_hashes block as a bookkeeping item for the record; it is not a leakage finding.

**CONCLUSION.** The spec view's single discriminating clause is the problem_statement's own 'must be a noop' sentence, verified load-bearing by the strip-and-reverify measurement above; every other clause verifies against the pre-patch implementation and so encodes no information about the gold edit; and the view contains none of the patch's identifiers or shape. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
