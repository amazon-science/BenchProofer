# P2 adversarial audit — django__django-11477

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,11 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # Pre-fix skeleton: the named-group mapping is reported in full -- every
+    # named group, including those that did NOT participate (whose value is the
+    # absence sentinel), is kept. The keyword/positional choice is made against
+    # this UNFILTERED mapping (non-empty iff the pattern has any named group at
+    # all). This is the buggy behaviour the spec must reject.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -148,12 +153,8 @@
         Invariant(Acc(list_pred(r_vals)))
         Invariant(len(keys) == len(vals))
         Invariant(0 <= i and i <= len(keys))
-        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(Forall(int, lambda j: (Implies(
-            0 <= j and j < len(r_vals),
-            ToSeq(r_vals)[j] != absent()),
-            [[ToSeq(r_vals)[j]]])))
+        Invariant(ToSeq(r_keys) == ToSeq(keys).drop(i))
+        Invariant(ToSeq(r_vals) == ToSeq(vals).drop(i))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         k = keys[i - 1]
@@ -162,16 +163,8 @@
         Assert(ToSeq(vals).drop(i - 1)[0] == v)
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
-        if v != absent():
-            r_keys = [k] + r_keys
-            old_vals = r_vals  # type: List[int]
-            r_vals = [v] + r_vals
-            Assert(ToSeq(r_vals)[0] == v)
-            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
-            Assert(Forall(int, lambda j: (Implies(
-                1 <= j and j < len(r_vals),
-                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
-                [[ToSeq(r_vals)[j]]])))
+        r_keys = [k] + r_keys
+        r_vals = [v] + r_vals
         i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,8 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG: substitutes a real captured value (token 0, modelling the empty
+    # string) for the absence sentinel instead of DROPPING the entry.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -148,12 +150,8 @@
         Invariant(Acc(list_pred(r_vals)))
         Invariant(len(keys) == len(vals))
         Invariant(0 <= i and i <= len(keys))
-        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(Forall(int, lambda j: (Implies(
-            0 <= j and j < len(r_vals),
-            ToSeq(r_vals)[j] != absent()),
-            [[ToSeq(r_vals)[j]]])))
+        Invariant(ToSeq(r_keys) == ToSeq(keys).drop(i))
+        Invariant(len(r_vals) == len(r_keys))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         k = keys[i - 1]
@@ -162,16 +160,11 @@
         Assert(ToSeq(vals).drop(i - 1)[0] == v)
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
+        r_keys = [k] + r_keys
         if v != absent():
-            r_keys = [k] + r_keys
-            old_vals = r_vals  # type: List[int]
             r_vals = [v] + r_vals
-            Assert(ToSeq(r_vals)[0] == v)
-            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
-            Assert(Forall(int, lambda j: (Implies(
-                1 <= j and j < len(r_vals),
-                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
-                [[ToSeq(r_vals)[j]]])))
+        else:
+            r_vals = [0] + r_vals
         i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,9 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG: filters on truthiness (token != 0) rather than on the absence
+    # sentinel -- a real captured value modelled by token 0 (the empty string)
+    # is dropped as well.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -150,10 +153,6 @@
         Invariant(0 <= i and i <= len(keys))
         Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
         Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(Forall(int, lambda j: (Implies(
-            0 <= j and j < len(r_vals),
-            ToSeq(r_vals)[j] != absent()),
-            [[ToSeq(r_vals)[j]]])))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         k = keys[i - 1]
@@ -162,16 +161,9 @@
         Assert(ToSeq(vals).drop(i - 1)[0] == v)
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
-        if v != absent():
+        if v != 0:
             r_keys = [k] + r_keys
-            old_vals = r_vals  # type: List[int]
             r_vals = [v] + r_vals
-            Assert(ToSeq(r_vals)[0] == v)
-            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
-            Assert(Forall(int, lambda j: (Implies(
-                1 <= j and j < len(r_vals),
-                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
-                [[ToSeq(r_vals)[j]]])))
         i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,7 +174,7 @@
                 [[ToSeq(r_vals)[j]]])))
         i = i - 1
     args = []  # type: List[int]
-    if len(r_keys) == 0:
+    if len(keys) == 0:   # WRONG: unfiltered mapping
         j = 0
         while j < len(positional):
             # invariants-start
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,9 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG (partial domain): the retention filter is applied only when the
+    # pattern has more than one named group; a lone optional group is kept even
+    # when it did not participate.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -148,12 +151,11 @@
         Invariant(Acc(list_pred(r_vals)))
         Invariant(len(keys) == len(vals))
         Invariant(0 <= i and i <= len(keys))
-        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(Forall(int, lambda j: (Implies(
-            0 <= j and j < len(r_vals),
-            ToSeq(r_vals)[j] != absent()),
-            [[ToSeq(r_vals)[j]]])))
+        Invariant(Implies(len(keys) != 1,
+            ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i))))
+        Invariant(Implies(len(keys) != 1,
+            ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i))))
+        Invariant(len(r_vals) == len(r_keys))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         k = keys[i - 1]
@@ -162,16 +164,9 @@
         Assert(ToSeq(vals).drop(i - 1)[0] == v)
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
-        if v != absent():
+        if v != absent() or len(keys) == 1:
             r_keys = [k] + r_keys
-            old_vals = r_vals  # type: List[int]
             r_vals = [v] + r_vals
-            Assert(ToSeq(r_vals)[0] == v)
-            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
-            Assert(Forall(int, lambda j: (Implies(
-                1 <= j and j < len(r_vals),
-                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
-                [[ToSeq(r_vals)[j]]])))
         i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,8 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG: the retained entries are reported in reverse order (the fold is
+    # built back-to-front), so the keyword mapping is not order-preserving.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -148,8 +150,7 @@
         Invariant(Acc(list_pred(r_vals)))
         Invariant(len(keys) == len(vals))
         Invariant(0 <= i and i <= len(keys))
-        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
+        Invariant(len(r_vals) == len(r_keys))
         Invariant(Forall(int, lambda j: (Implies(
             0 <= j and j < len(r_vals),
             ToSeq(r_vals)[j] != absent()),
@@ -163,14 +164,14 @@
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
         if v != absent():
-            r_keys = [k] + r_keys
             old_vals = r_vals  # type: List[int]
-            r_vals = [v] + r_vals
-            Assert(ToSeq(r_vals)[0] == v)
-            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
+            r_keys = r_keys + [k]
+            r_vals = r_vals + [v]
+            Assert(ToSeq(r_vals).take(len(old_vals)) == ToSeq(old_vals))
+            Assert(ToSeq(r_vals)[len(r_vals) - 1] == v)
             Assert(Forall(int, lambda j: (Implies(
-                1 <= j and j < len(r_vals),
-                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
+                0 <= j and j < len(old_vals),
+                ToSeq(r_vals)[j] == ToSeq(old_vals)[j]),
                 [[ToSeq(r_vals)[j]]])))
         i = i - 1
     args = []  # type: List[int]
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,7 +176,7 @@
     args = []  # type: List[int]
     if len(r_keys) == 0:
         j = 0
-        while j < len(positional):
+        while j < len(positional) - 1:   # WRONG: drops the last capture
             # invariants-start
             Invariant(Acc(list_pred(positional), 1 / 2))
             Invariant(Acc(list_pred(args)))
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,7 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG (control-flow effect): raises instead of dropping the entry.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -162,16 +163,17 @@
         Assert(ToSeq(vals).drop(i - 1)[0] == v)
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
-        if v != absent():
-            r_keys = [k] + r_keys
-            old_vals = r_vals  # type: List[int]
-            r_vals = [v] + r_vals
-            Assert(ToSeq(r_vals)[0] == v)
-            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
-            Assert(Forall(int, lambda j: (Implies(
-                1 <= j and j < len(r_vals),
-                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
-                [[ToSeq(r_vals)[j]]])))
+        if v == absent():
+            raise ValueError("non-participating named group")
+        r_keys = [k] + r_keys
+        old_vals = r_vals  # type: List[int]
+        r_vals = [v] + r_vals
+        Assert(ToSeq(r_vals)[0] == v)
+        Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
+        Assert(Forall(int, lambda j: (Implies(
+            1 <= j and j < len(r_vals),
+            ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
+            [[ToSeq(r_vals)[j]]])))
         i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,7 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG (divergence): spins forever on a non-participating named group.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -154,7 +155,6 @@
             0 <= j and j < len(r_vals),
             ToSeq(r_vals)[j] != absent()),
             [[ToSeq(r_vals)[j]]])))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         k = keys[i - 1]
         v = vals[i - 1]
@@ -172,7 +172,7 @@
                 1 <= j and j < len(r_vals),
                 ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
                 [[ToSeq(r_vals)[j]]])))
-        i = i - 1
+            i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
         j = 0
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,7 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    Assert(False)   # vacuity control: must FAIL
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,6 +137,8 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG (ungrounded-oracle echo on the swapped pair): tests the absence of
+    # the KEY rather than of the VALUE, echoing kept_keys(vals, keys).
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
     i = len(keys)
@@ -148,12 +150,8 @@
         Invariant(Acc(list_pred(r_vals)))
         Invariant(len(keys) == len(vals))
         Invariant(0 <= i and i <= len(keys))
-        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(Forall(int, lambda j: (Implies(
-            0 <= j and j < len(r_vals),
-            ToSeq(r_vals)[j] != absent()),
-            [[ToSeq(r_vals)[j]]])))
+        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(vals).drop(i), ToSeq(keys).drop(i)))
+        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(vals).drop(i), ToSeq(keys).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
         k = keys[i - 1]
@@ -162,16 +160,9 @@
         Assert(ToSeq(vals).drop(i - 1)[0] == v)
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
-        if v != absent():
-            r_keys = [k] + r_keys
-            old_vals = r_vals  # type: List[int]
-            r_vals = [v] + r_vals
-            Assert(ToSeq(r_vals)[0] == v)
-            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
-            Assert(Forall(int, lambda j: (Implies(
-                1 <= j and j < len(r_vals),
-                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
-                [[ToSeq(r_vals)[j]]])))
+        if k != absent():
+            r_keys = [v] + r_keys
+            r_vals = [k] + r_vals
         i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -137,9 +137,13 @@
                     ToSeq(Result()[2]) == ToSeq(positional)))
     # post-conditions-end
     # impl-start
+    # WRONG (boundary): the loop starts one entry short, so the LAST named group
+    # is dropped from the reported mapping whether or not it captured a value.
     r_keys = []  # type: List[int]
     r_vals = []  # type: List[int]
-    i = len(keys)
+    i = len(keys) - 1
+    if i < 0:
+        i = 0
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(keys), 1 / 2))
@@ -148,8 +152,7 @@
         Invariant(Acc(list_pred(r_vals)))
         Invariant(len(keys) == len(vals))
         Invariant(0 <= i and i <= len(keys))
-        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
-        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
+        Invariant(len(r_vals) == len(r_keys))
         Invariant(Forall(int, lambda j: (Implies(
             0 <= j and j < len(r_vals),
             ToSeq(r_vals)[j] != absent()),
@@ -163,8 +166,8 @@
         Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
         Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
         if v != absent():
+            old_vals = r_vals  # type: List[int]
             r_keys = [k] + r_keys
-            old_vals = r_vals  # type: List[int]
             r_vals = [v] + r_vals
             Assert(ToSeq(r_vals)[0] == v)
             Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,6 +175,7 @@
         i = i - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
+        args = positional   # WRONG: aliases the input instead of copying
         j = 0
         while j < len(positional):
             # invariants-start
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,6 +173,25 @@
                 ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
                 [[ToSeq(r_vals)[j]]])))
         i = i - 1
+    # WRONG (partial domain): when the filter empties the mapping, fall back to
+    # the UNFILTERED mapping (real analogue: `... if v is not None} or
+    # match.groupdict()`), so an only-absent optional group is reported again.
+    if len(r_keys) == 0 and len(keys) > 0:
+        i2 = len(keys)
+        while i2 > 0:
+            # invariants-start
+            Invariant(Acc(list_pred(keys), 1 / 2))
+            Invariant(Acc(list_pred(vals), 1 / 2))
+            Invariant(Acc(list_pred(r_keys)))
+            Invariant(Acc(list_pred(r_vals)))
+            Invariant(len(keys) == len(vals))
+            Invariant(0 <= i2 and i2 <= len(keys))
+            Invariant(len(r_vals) == len(r_keys))
+            Invariant(MustTerminate(i2 + 1))
+            # invariants-end
+            r_keys = [keys[i2 - 1]] + r_keys
+            r_vals = [vals[i2 - 1]] + r_vals
+            i2 = i2 - 1
     args = []  # type: List[int]
     if len(r_keys) == 0:
         j = 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11477.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a URL pattern recognizes an incoming path, it reports the captured named
  groups as a keyword mapping and (separately) a sequence of positional
  captures. A named group is "optional": the pattern can succeed even when that
  group does not participate, in which case the group has NO captured value (it
  is absent / unset), as opposed to having captured the empty string.

  The reported keyword mapping must contain an entry ONLY for those named groups
  that actually captured a value; a named group that did not participate
  contributes no entry at all -- it must not appear carrying an unset/absent
  value. Each retained entry keeps its captured value verbatim.

  The reported positional sequence is chosen against the *retained* keyword
  mapping: if at least one named group captured a value, the positional captures
  are discarded (an empty sequence is reported); only when no named group
  captured a value are the positional captures reported.

  The consequence that matters: when a path is recognized by a pattern with an
  optional named group that did not participate, the reported keyword mapping
  omits that group entirely rather than reporting it with an absent value -- so a
  caller that re-derives a path from these captures recovers the original path
  for URLs with missing optional arguments (the translate_url consequence the
  issue describes).

Modelling choices (Nagini fragment):
  * The named-group capture mapping is modelled as two parallel sequences:
    ``keys`` (the group-name tokens, distinct) and ``vals`` (the parallel
    captured values). A reserved sentinel value ``ABSENT`` in ``vals[i]`` models
    a named group that did not participate (real Python ``None``); any other
    value models a real captured value. Captured strings are irrelevant beyond
    identity, so integer tokens are the faithful carrier (mapping.md §2).
  * The positional captures are a ``List[int]``.
  * The result is the triple (retained keyword keys, retained keyword values,
    reported positional captures): the parallel key/value sequences of the
    reported keyword mapping together with the reported positional sequence. An
    additional path-tail component carried alongside in the full operation is
    unchanged by this behaviour and is omitted from the model.

No string indexing is used (Nagini bans it). The whole behaviour is modelled
deeply (the per-entry retention fold is spelled out); there is no axiomatised
callee. Sequence folds are front-recursive so a single unfold is available per
loop step. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No axioms. The named-group retention filter and the keyword/positional choice
# are the behaviour under specification and are modelled deeply (the
# `kept_keys`/`kept_vals` folds and the impl region). The only operations the
# behaviour composes are an absence test and sequence construction, ordinary
# operations with their real Python semantics; there is no unchanged opaque
# callee to axiomatise.
# axioms-end

# pure-start
@Pure
def absent() -> int:
    """The reserved sentinel modelling a named group that did NOT participate
    (real Python ``None`` as that group's captured value). A captured value is
    any value other than this sentinel."""
    return -1

@Pure
def kept_keys(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """The retained group-name tokens: the subsequence of `keys` at positions
    whose parallel value is NOT the absence sentinel, order preserved.
    Front-recursive so a single unfold is available per loop step."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return keys.take(0)
    if vals[0] == absent():
        return kept_keys(keys.drop(1), vals.drop(1))
    return PSeq(keys[0]) + kept_keys(keys.drop(1), vals.drop(1))

@Pure
def kept_vals(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """The retained captured values: the subsequence of `vals` at positions that
    are NOT the absence sentinel, order preserved (parallel to `kept_keys`)."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return vals.take(0)
    if vals[0] == absent():
        return kept_vals(keys.drop(1), vals.drop(1))
    return PSeq(vals[0]) + kept_vals(keys.drop(1), vals.drop(1))
# pure-end

def select_captures(keys: List[int],
                   vals: List[int],
                   positional: List[int]) -> Tuple[List[int], List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(Acc(list_pred(vals), 1 / 2))
    Requires(Acc(list_pred(positional), 1 / 2))
    # The named-group capture mapping: one captured value per named group.
    Requires(len(keys) == len(vals))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs retain their fractional permission (never mutated).
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(vals), 1 / 2))
    Ensures(Acc(list_pred(positional), 1 / 2))
    # The mapping invariant survives (one captured value per named group).
    Ensures(len(keys) == len(vals))
    # The reported keyword mapping (parallel key / value sequences) and the
    # reported positional captures.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    # The reported keyword mapping retains EXACTLY the named groups that captured
    # a value -- those whose value is not the absence sentinel -- in order,
    # carrying their captured value verbatim. A non-participating named group
    # contributes no entry (it is omitted, NOT reported with an absent value).
    Ensures(ToSeq(Result()[0]) == kept_keys(ToSeq(keys), ToSeq(vals)))
    Ensures(ToSeq(Result()[1]) == kept_vals(ToSeq(keys), ToSeq(vals)))
    # The absence sentinel never survives into the reported keyword values.
    Ensures(Forall(int, lambda i: (Implies(
        0 <= i and i < len(Result()[1]),
        ToSeq(Result()[1])[i] != absent()),
        [[ToSeq(Result()[1])[i]]])))
    # The reported positional captures are chosen against the RETAINED mapping:
    # if any named group captured a value the positional report is empty,
    # otherwise it is the input positional captures verbatim.
    Ensures(Implies(len(Result()[0]) != 0,
                    ToSeq(Result()[2]) == ToSeq(positional).take(0)))
    Ensures(Implies(len(Result()[0]) == 0,
                    ToSeq(Result()[2]) == ToSeq(positional)))
    # post-conditions-end
    # impl-start
    r_keys = []  # type: List[int]
    r_vals = []  # type: List[int]
    i = len(keys)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(Acc(list_pred(vals), 1 / 2))
        Invariant(Acc(list_pred(r_keys)))
        Invariant(Acc(list_pred(r_vals)))
        Invariant(len(keys) == len(vals))
        Invariant(0 <= i and i <= len(keys))
        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
        Invariant(Forall(int, lambda j: (Implies(
            0 <= j and j < len(r_vals),
            ToSeq(r_vals)[j] != absent()),
            [[ToSeq(r_vals)[j]]])))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        k = keys[i - 1]
        v = vals[i - 1]
        Assert(ToSeq(keys).drop(i - 1)[0] == k)
        Assert(ToSeq(vals).drop(i - 1)[0] == v)
        Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
        Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
        if v != absent():
            r_keys = [k] + r_keys
            old_vals = r_vals  # type: List[int]
            r_vals = [v] + r_vals
            Assert(ToSeq(r_vals)[0] == v)
            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
            Assert(Forall(int, lambda j: (Implies(
                1 <= j and j < len(r_vals),
                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
                [[ToSeq(r_vals)[j]]])))
        i = i - 1
    args = []  # type: List[int]
    if len(r_keys) == 0:
        j = 0
        while j < len(positional):
            # invariants-start
            Invariant(Acc(list_pred(positional), 1 / 2))
            Invariant(Acc(list_pred(args)))
            Invariant(0 <= j and j <= len(positional))
            Invariant(ToSeq(args) == ToSeq(positional).take(j))
            Invariant(MustTerminate(len(positional) - j + 1))
            # invariants-end
            args = args + [positional[j]]
            j = j + 1
    return r_keys, r_vals, args
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-11477/nagini. 14 same-spec wrong impls built by copying model.py and editing ONLY the impl region; all 14 confirmed byte-identical spec (`adversary same-spec` = SAME) and all 14 came back exit 2 (NOT-A-COUNTEREXAMPLE / does not verify). ZERO CANDIDATEs, therefore no faithful refined patch had to be materialized and no run_resolve was required (`patches` is empty by construction, not by omission). Positive control = verbatim model.py: `bash scripts/nagini_verify.sh.../positive_control.py` -> "Verification successful" (30.4s, exit 0). Prepatch bug reproduced: atk_1 is model_prepatch.py's impl region verbatim (unfiltered copy loop) -> rejected, so the spec senses the change.

**COMMANDS:** for each N in 1..14, from repo root: `python -m swebench_unified.adversary same-spec nagini django__django-11477 atk_N.py` (all SAME) then `python -m swebench_unified.adversary weakness nagini django__django-11477 atk_N.py` (all exit 2). Run 3-at-a-time as background jobs; results in res_N.txt beside each attack.

### ATTACK BATTERY (each a DISTINCT wrong-impl class, each with a real-code analogue):
atk_1  prepatch bug verbatim: unfiltered mapping, None-valued groups retained (`kwargs = match.groupdict()`) -> rejected. atk_2  naive fix: substitutes token 0 (the empty string) for the absence sentinel instead of DROPPING the entry (`{k: v if v is not None else ''...}`) -> rejected (fails kept_keys/kept_vals + the no-sentinel clause). atk_3  truthiness filter `if v:` instead of `if v is not None` -- drops REAL empty-string captures -> rejected.

This is the discrimination the bundle's own G-AX cannot make (see DEFECT below). atk_4  args chosen against the UNFILTERED mapping (`if len(keys)==0`) -- the post-3.0 Django shape -> rejected. atk_5  partial domain: filter applied only when >1 named group, so a lone absent optional survives -> rejected. atk_6  retained mapping reported in REVERSED order (order not preserved) -> rejected. atk_7  boundary: positional report drops its last capture (`match.groups()[:-1]`) -> rejected. atk_8  control-flow effect: `raise ValueError` on a non-participating group instead of dropping it -> rejected. atk_9  DIVERGENCE / vacuity lever: gold body with `i = i - 1` moved inside the retention guard and MustTerminate REMOVED from the loop invariant -- spins forever on any absent optional group while maintaining every functional invariant -> rejected (method-level MustTerminate(2) does the work). atk_10 VACUITY CONTROL: `Assert(False)` at the impl entry -> FAILS, so the impl region is reachable and the proof is not vacuous. atk_11 ungrounded-oracle echo on the SWAPPED pair: echoes `kept_keys(vals, keys)` / filters on the KEY token rather than the VALUE (`if k is not None`) -> rejected. atk_12 boundary: loop starts one entry short, last named group always dropped (`list(groupdict().items())[:-1]`) -> rejected. atk_13 positional report ALIASES the input list instead of copying -> rejected (the full-permission `Acc(list_pred(Result()[2]))` postcondition pins a fresh list). atk_14 most realistic residual wrong fix: filter, then FALL BACK to the unfiltered mapping when the filter empties it (`{... if v is not None} or match.groupdict()`) -- diverges from gold on exactly the F2P named_optional_terminated / only-absent-optional paths -> rejected.

WHY NO COUNTEREXAMPLE CAN EXIST (structural, machine-checked): the postcondition pins Result()[0]==kept_keys(keys,vals) and Result()[1]==kept_vals(keys,vals) OUTRIGHT (equality, not a property), so len(Result()[0]) is determined; the two args clauses are then mutually exclusive AND exhaustive, pinning Result()[2]. totality.py enumerates the whole precondition domain (len(keys)==len(vals)) at small sizes -- 7161 points, 0 underdetermined, 0 contradictory: the spec is a TOTAL DETERMINISTIC function pin with zero implementation freedom, plus MustTerminate(2) at the method level closing divergence and Acc(list_pred(...)) closing aliasing/framing. Verify=>gold-equal at the model level is therefore structural, which is consistent with all 14 rejections.

A-LEG AUDIT (refinement.md). Legs: A1 R (groupdict Dict[str,Optional[str]] <-> two parallel List[int], None <-> absent()==-1), A2 R (groups() tuple <-> List[int]), A3 A-reference (the None-dropping comprehension modelled deeply by kept_keys/kept_vals), A4 A-reference+I (args selection against the FILTERED mapping), A5 excluded-with-justification (the `path[match.end():]` tail is an unchanged carry-through). Every leg is R / A-reference / I; NO kind-3 and NO consumed axiom -- confirmed mechanically: `grep -c @ContractOnly model.py` = 0 and meta.json `axioms` == []. Correspondence to the real callee HOLDS: I re-derived it independently in aref_check.py, which transcribes the Nagini @Pure folds LITERALLY (take(0)/drop(1)/PSeq(x)+rest) and model.py's verified impl loop LITERALLY, maps dict->parallel-int-lists through an INDEPENDENT injective tokenizer (None->-1), and compares against the real post-patch source line applied to real `re.Match` objects: 17 boundary + 70411 randomized matches, 0 divergences, including the empty-string-capture cases and named-groups-inside-groups() cases the bundle's own boundary list omits. Exit 0.

DEFECT FOUND (evidence quality, does NOT break the spec -- reported for repair, not as a gate fail): the bundle's axiom_check.py load-bearing comparison is TAUTOLOGICAL. Its `deep_model()` computes `{k: v for k, v in gd.items() if v is not None}` and its `real_op()` computes `{k: v for k, v in match.groupdict().items() if v is not None}` -- the same expression twice, so it compares the gold expression to a verbatim copy of itself rather than to model.py's Nagini folds. Proof by co-mutation: tautology_demo.py rewrites BOTH functions' filter to `if v:` (a mis-derived retention, exactly the semantics atk_3 encodes) and the resulting axiom_check_MUTATED.py still prints "G-AX OK" and exits 0. So G-AX as written would not have caught a wrong A-reference.

The A-reference itself is nevertheless SOUND -- my independent aref_check.py establishes the correspondence the bundle's checker fails to test -- so this is an evidence-quality defect in axiom_check.py, not a refinement-fidelity break. RECOMMENDED REPAIR: replace axiom_check.py's `deep_model` with a literal transcription of the kept_keys/kept_vals recursions over parallel int tokens (as in aref_check.py) so the two sides are genuinely independent, and add empty-string-capture boundary pairs.

**Minor:** one F2P test (test_two_variable_at_start_of_path_pattern, the `<lang>/<path:url>/` path() route) resolves through RoutePattern, which mapping.md correctly declares out of scope as unchanged by the gold patch; it is carried by the URLResolver's RegexPattern(r'^/') prefix chain, so the exclusion is accurate and not a coverage gap.

**VERDICT:** SOUND. 14 attacks encoded and fully verified (>= the 5 required), spanning prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, divergence and aliasing; none is a CANDIDATE, so verify=>correct is not falsified here. Positive control verifies; vacuity control fails as required; no attack or resolve run was left incomplete.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11477.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a URL pattern recognizes an incoming path, it reports the captured named
  groups as a keyword mapping and (separately) a sequence of positional
  captures. A named group is "optional": the pattern can succeed even when that
  group does not participate, in which case the group has NO captured value (it
  is absent / unset), as opposed to having captured the empty string.

  The reported keyword mapping must contain an entry ONLY for those named groups
  that actually captured a value; a named group that did not participate
  contributes no entry at all -- it must not appear carrying an unset/absent
  value. Each retained entry keeps its captured value verbatim.

  The reported positional sequence is chosen against the *retained* keyword
  mapping: if at least one named group captured a value, the positional captures
  are discarded (an empty sequence is reported); only when no named group
  captured a value are the positional captures reported.

  The consequence that matters: when a path is recognized by a pattern with an
  optional named group that did not participate, the reported keyword mapping
  omits that group entirely rather than reporting it with an absent value -- so a
  caller that re-derives a path from these captures recovers the original path
  for URLs with missing optional arguments (the translate_url consequence the
  issue describes).

Modelling choices (Nagini fragment):
  * The named-group capture mapping is modelled as two parallel sequences:
    ``keys`` (the group-name tokens, distinct) and ``vals`` (the parallel
    captured values). A reserved sentinel value ``ABSENT`` in ``vals[i]`` models
    a named group that did not participate (real Python ``None``); any other
    value models a real captured value. Captured strings are irrelevant beyond
    identity, so integer tokens are the faithful carrier (mapping.md §2).
  * The positional captures are a ``List[int]``.
  * The result is the triple (retained keyword keys, retained keyword values,
    reported positional captures): the parallel key/value sequences of the
    reported keyword mapping together with the reported positional sequence. An
    additional path-tail component carried alongside in the full operation is
    unchanged by this behaviour and is omitted from the model.

No string indexing is used (Nagini bans it). The whole behaviour is modelled
deeply (the per-entry retention fold is spelled out); there is no axiomatised
callee. Sequence folds are front-recursive so a single unfold is available per
loop step. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No axioms. The named-group retention filter and the keyword/positional choice
# are the behaviour under specification and are modelled deeply (the
# `kept_keys`/`kept_vals` folds and the impl region). The only operations the
# behaviour composes are an absence test and sequence construction, ordinary
# operations with their real Python semantics; there is no unchanged opaque
# callee to axiomatise.
# axioms-end

# pure-start
@Pure
def absent() -> int:
    """The reserved sentinel modelling a named group that did NOT participate
    (real Python ``None`` as that group's captured value). A captured value is
    any value other than this sentinel."""
    return -1

@Pure
def kept_keys(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """The retained group-name tokens: the subsequence of `keys` at positions
    whose parallel value is NOT the absence sentinel, order preserved.
    Front-recursive so a single unfold is available per loop step."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return keys.take(0)
    if vals[0] == absent():
        return kept_keys(keys.drop(1), vals.drop(1))
    return PSeq(keys[0]) + kept_keys(keys.drop(1), vals.drop(1))

@Pure
def kept_vals(keys: PSeq[int], vals: PSeq[int]) -> PSeq[int]:
    """The retained captured values: the subsequence of `vals` at positions that
    are NOT the absence sentinel, order preserved (parallel to `kept_keys`)."""
    Requires(len(keys) == len(vals))
    if len(keys) == 0:
        return vals.take(0)
    if vals[0] == absent():
        return kept_vals(keys.drop(1), vals.drop(1))
    return PSeq(vals[0]) + kept_vals(keys.drop(1), vals.drop(1))
# pure-end

def select_captures(keys: List[int],
                   vals: List[int],
                   positional: List[int]) -> Tuple[List[int], List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(Acc(list_pred(vals), 1 / 2))
    Requires(Acc(list_pred(positional), 1 / 2))
    # The named-group capture mapping: one captured value per named group.
    Requires(len(keys) == len(vals))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs retain their fractional permission (never mutated).
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(vals), 1 / 2))
    Ensures(Acc(list_pred(positional), 1 / 2))
    # The mapping invariant survives (one captured value per named group).
    Ensures(len(keys) == len(vals))
    # The reported keyword mapping (parallel key / value sequences) and the
    # reported positional captures.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    # The reported keyword mapping retains EXACTLY the named groups that captured
    # a value -- those whose value is not the absence sentinel -- in order,
    # carrying their captured value verbatim. A non-participating named group
    # contributes no entry (it is omitted, NOT reported with an absent value).
    Ensures(ToSeq(Result()[0]) == kept_keys(ToSeq(keys), ToSeq(vals)))
    Ensures(ToSeq(Result()[1]) == kept_vals(ToSeq(keys), ToSeq(vals)))
    # The absence sentinel never survives into the reported keyword values.
    Ensures(Forall(int, lambda i: (Implies(
        0 <= i and i < len(Result()[1]),
        ToSeq(Result()[1])[i] != absent()),
        [[ToSeq(Result()[1])[i]]])))
    # The reported positional captures are chosen against the RETAINED mapping:
    # if any named group captured a value the positional report is empty,
    # otherwise it is the input positional captures verbatim.
    Ensures(Implies(len(Result()[0]) != 0,
                    ToSeq(Result()[2]) == ToSeq(positional).take(0)))
    Ensures(Implies(len(Result()[0]) == 0,
                    ToSeq(Result()[2]) == ToSeq(positional)))
    # post-conditions-end
    # impl-start
    r_keys = []  # type: List[int]
    r_vals = []  # type: List[int]
    i = len(keys)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(keys), 1 / 2))
        Invariant(Acc(list_pred(vals), 1 / 2))
        Invariant(Acc(list_pred(r_keys)))
        Invariant(Acc(list_pred(r_vals)))
        Invariant(len(keys) == len(vals))
        Invariant(0 <= i and i <= len(keys))
        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
        Invariant(Forall(int, lambda j: (Implies(
            0 <= j and j < len(r_vals),
            ToSeq(r_vals)[j] != absent()),
            [[ToSeq(r_vals)[j]]])))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        k = keys[i - 1]
        v = vals[i - 1]
        Assert(ToSeq(keys).drop(i - 1)[0] == k)
        Assert(ToSeq(vals).drop(i - 1)[0] == v)
        Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
        Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
        if v != absent():
            r_keys = [k] + r_keys
            old_vals = r_vals  # type: List[int]
            r_vals = [v] + r_vals
            Assert(ToSeq(r_vals)[0] == v)
            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
            Assert(Forall(int, lambda j: (Implies(
                1 <= j and j < len(r_vals),
                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
                [[ToSeq(r_vals)[j]]])))
        i = i - 1
    args = []  # type: List[int]
    if len(r_keys) == 0:
        j = 0
        while j < len(positional):
            # invariants-start
            Invariant(Acc(list_pred(positional), 1 / 2))
            Invariant(Acc(list_pred(args)))
            Invariant(0 <= j and j <= len(positional))
            Invariant(ToSeq(args) == ToSeq(positional).take(j))
            Invariant(MustTerminate(len(positional) - j + 1))
            # invariants-end
            args = args + [positional[j]]
            j = j + 1
    return r_keys, r_vals, args
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-11477/nagini. 14 same-spec wrong impls built by copying model.py and editing ONLY the impl region; all 14 confirmed byte-identical spec (`adversary same-spec` = SAME) and all 14 came back exit 2 (NOT-A-COUNTEREXAMPLE / does not verify). ZERO CANDIDATEs, therefore no faithful refined patch had to be materialized and no run_resolve was required (`patches` is empty by construction, not by omission). Positive control = verbatim model.py: `bash scripts/nagini_verify.sh.../positive_control.py` -> "Verification successful" (30.4s, exit 0). Prepatch bug reproduced: atk_1 is model_prepatch.py's impl region verbatim (unfiltered copy loop) -> rejected, so the spec senses the change.

**COMMANDS:** for each N in 1..14, from repo root: `python -m swebench_unified.adversary same-spec nagini django__django-11477 atk_N.py` (all SAME) then `python -m swebench_unified.adversary weakness nagini django__django-11477 atk_N.py` (all exit 2). Run 3-at-a-time as background jobs; results in res_N.txt beside each attack.

### ATTACK BATTERY (each a DISTINCT wrong-impl class, each with a real-code analogue):
atk_1  prepatch bug verbatim: unfiltered mapping, None-valued groups retained (`kwargs = match.groupdict()`) -> rejected. atk_2  naive fix: substitutes token 0 (the empty string) for the absence sentinel instead of DROPPING the entry (`{k: v if v is not None else ''...}`) -> rejected (fails kept_keys/kept_vals + the no-sentinel clause). atk_3  truthiness filter `if v:` instead of `if v is not None` -- drops REAL empty-string captures -> rejected.

This is the discrimination the bundle's own G-AX cannot make (see DEFECT below). atk_4  args chosen against the UNFILTERED mapping (`if len(keys)==0`) -- the post-3.0 Django shape -> rejected. atk_5  partial domain: filter applied only when >1 named group, so a lone absent optional survives -> rejected. atk_6  retained mapping reported in REVERSED order (order not preserved) -> rejected. atk_7  boundary: positional report drops its last capture (`match.groups()[:-1]`) -> rejected. atk_8  control-flow effect: `raise ValueError` on a non-participating group instead of dropping it -> rejected. atk_9  DIVERGENCE / vacuity lever: gold body with `i = i - 1` moved inside the retention guard and MustTerminate REMOVED from the loop invariant -- spins forever on any absent optional group while maintaining every functional invariant -> rejected (method-level MustTerminate(2) does the work). atk_10 VACUITY CONTROL: `Assert(False)` at the impl entry -> FAILS, so the impl region is reachable and the proof is not vacuous. atk_11 ungrounded-oracle echo on the SWAPPED pair: echoes `kept_keys(vals, keys)` / filters on the KEY token rather than the VALUE (`if k is not None`) -> rejected. atk_12 boundary: loop starts one entry short, last named group always dropped (`list(groupdict().items())[:-1]`) -> rejected. atk_13 positional report ALIASES the input list instead of copying -> rejected (the full-permission `Acc(list_pred(Result()[2]))` postcondition pins a fresh list). atk_14 most realistic residual wrong fix: filter, then FALL BACK to the unfiltered mapping when the filter empties it (`{... if v is not None} or match.groupdict()`) -- diverges from gold on exactly the F2P named_optional_terminated / only-absent-optional paths -> rejected.

WHY NO COUNTEREXAMPLE CAN EXIST (structural, machine-checked): the postcondition pins Result()[0]==kept_keys(keys,vals) and Result()[1]==kept_vals(keys,vals) OUTRIGHT (equality, not a property), so len(Result()[0]) is determined; the two args clauses are then mutually exclusive AND exhaustive, pinning Result()[2]. totality.py enumerates the whole precondition domain (len(keys)==len(vals)) at small sizes -- 7161 points, 0 underdetermined, 0 contradictory: the spec is a TOTAL DETERMINISTIC function pin with zero implementation freedom, plus MustTerminate(2) at the method level closing divergence and Acc(list_pred(...)) closing aliasing/framing. Verify=>gold-equal at the model level is therefore structural, which is consistent with all 14 rejections.

A-LEG AUDIT (refinement.md). Legs: A1 R (groupdict Dict[str,Optional[str]] <-> two parallel List[int], None <-> absent()==-1), A2 R (groups() tuple <-> List[int]), A3 A-reference (the None-dropping comprehension modelled deeply by kept_keys/kept_vals), A4 A-reference+I (args selection against the FILTERED mapping), A5 excluded-with-justification (the `path[match.end():]` tail is an unchanged carry-through). Every leg is R / A-reference / I; NO kind-3 and NO consumed axiom -- confirmed mechanically: `grep -c @ContractOnly model.py` = 0 and meta.json `axioms` == []. Correspondence to the real callee HOLDS: I re-derived it independently in aref_check.py, which transcribes the Nagini @Pure folds LITERALLY (take(0)/drop(1)/PSeq(x)+rest) and model.py's verified impl loop LITERALLY, maps dict->parallel-int-lists through an INDEPENDENT injective tokenizer (None->-1), and compares against the real post-patch source line applied to real `re.Match` objects: 17 boundary + 70411 randomized matches, 0 divergences, including the empty-string-capture cases and named-groups-inside-groups() cases the bundle's own boundary list omits. Exit 0.

DEFECT FOUND (evidence quality, does NOT break the spec -- reported for repair, not as a gate fail): the bundle's axiom_check.py load-bearing comparison is TAUTOLOGICAL. Its `deep_model()` computes `{k: v for k, v in gd.items() if v is not None}` and its `real_op()` computes `{k: v for k, v in match.groupdict().items() if v is not None}` -- the same expression twice, so it compares the gold expression to a verbatim copy of itself rather than to model.py's Nagini folds. Proof by co-mutation: tautology_demo.py rewrites BOTH functions' filter to `if v:` (a mis-derived retention, exactly the semantics atk_3 encodes) and the resulting axiom_check_MUTATED.py still prints "G-AX OK" and exits 0. So G-AX as written would not have caught a wrong A-reference.

The A-reference itself is nevertheless SOUND -- my independent aref_check.py establishes the correspondence the bundle's checker fails to test -- so this is an evidence-quality defect in axiom_check.py, not a refinement-fidelity break. RECOMMENDED REPAIR: replace axiom_check.py's `deep_model` with a literal transcription of the kept_keys/kept_vals recursions over parallel int tokens (as in aref_check.py) so the two sides are genuinely independent, and add empty-string-capture boundary pairs.

**Minor:** one F2P test (test_two_variable_at_start_of_path_pattern, the `<lang>/<path:url>/` path() route) resolves through RoutePattern, which mapping.md correctly declares out of scope as unchanged by the gold patch; it is carried by the URLResolver's RegexPattern(r'^/') prefix chain, so the exclusion is accurate and not a coverage gap.

**VERDICT:** SOUND. 14 attacks encoded and fully verified (>= the 5 required), spanning prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, divergence and aliasing; none is a CANDIDATE, so verify=>correct is not falsified here. Positive control verifies; vacuity control fails as required; no attack or resolve run was left incomplete.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reference set up per instructions: fresh git worktree of the upstream repository at base_commit e28671187903e6aca2428374fdd504fca3032aee with patch.diff APPLIED (git apply clean; inspect.getsource asserts 'if v is not None' present in RegexPattern.match, so the post-patch body is the comparison target, NOT the base body).

WHAT THE SPEC PINS (model.py Ensures): Result()[0]==kept_keys(ToSeq(keys),ToSeq(vals)), Result()[1]==kept_vals(...) — retain exactly the parallel entries whose vals[i]!=absent(), order preserved, values verbatim; no absent() sentinel survives into Result()[1]; and Result()[2]==positional verbatim iff len(Result()[0])==0, else the empty sequence. Abstraction (mapping.md §2): match.groupdict(): Dict[str,Optional[str]] -> two parallel List[int] (keys/vals), None <-> absent()==-1, match.groups() -> positional List[int], path tail omitted as an unchanged carry-through.

### EVIDENCE (independent, not a re-run of the bundle's own checks):
(1) End-to-end differential I wrote (p2_diff_11477.py): drives the REAL patched django.urls.resolvers.RegexPattern.match (imported from the worktree, not a re-copy of the patch expression) and compares against an INDEPENDENT reimplementation derived from the Ensures clauses alone, through an injective str/None->int tokenizer that never mints -1 for a non-None value. 22 boundary + 60,000 fuzz patterns (17,457 matched): 0 divergences.

(2) Exotic-construct sweep (p2_exotic_11477.py): 31 boundary + 40,000 fuzz (9,680 matched): 0 divergences. This is where a too-strong spec would break, and it did not.

(3) Key boundary confirmations, real repo output: regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)? on 'regex_optional/1/' -> kwargs={'arg1':'1'}, args=() (absent optional DROPPED, matching kept_keys); regex_only_optional/(?:(?P<arg1>\d+)/)? on 'regex_only_optional/' -> kwargs={}, args=(None,) — the retained mapping is EMPTY so the positional captures ARE reported verbatim including the None slot, exactly the Implies(len(Result()[0])==0, Result()[2]==ToSeq(positional)) clause. This is the clause most at risk of being too strong and it holds: the spec does NOT demand the None slots be scrubbed from args, and the real code does not scrub them.

(4) Empty-string capture is correctly NOT absence: '^e/(?P<x>\w*)$' on 'e/' -> kwargs={'x':''}, args=() — token != absent(), mirroring real 'v is not None' rather than falsiness. A spec that conflated '' with None would have diverged here; it does not.

(5) ORDER faithfulness (a real over-strength risk for kept_keys, which pins an ORDERED subsequence while the real object is a dict): verified across 3 multi-named-group patterns x 14 paths that match.groupdict() key order == re.compile(pat).groupindex definition order and that the patched dict comprehension preserves it, so the ordered-subsequence postcondition is not stronger than reality.

(6) groups() includes named groups; the model's `positional` is groups() verbatim and args==groups() held on every retained-mapping-empty case checked.

**CROSS-CHECKS:** bundle model.py verifies under the pinned verifier (scripts/nagini_verify.sh, exit 0, 22.9s). G-DIFF sanity: model_prepatch.py passes `adversary same-spec` (exit 0, 'SAME — attack shares the bundle's exact specification') yet FAILS verification with 'Postcondition... ToSeq(Result()[0]) == kept_keys(ToSeq(keys), ToSeq(vals)) might not hold', confirming the spec senses the patch delta rather than being satisfied by the base behavior. Confirmed real repo == postpatch and != prepatch on both F2P shapes.

SCOPE NOTE (not a defect): RoutePattern.match (resolvers.py:248) also reads groupdict() but is untouched by the gold patch and out of scope per mapping.md §1; the omitted path tail path[match.end():] is provably identical pre/post-patch. Neither is a faithfulness gap in the modeled function.

**CONCLUSION:** the spec is a faithful biconditional deep model of the post-patch behavior — neither too strong nor drifting. No diverging input exists among ~100k inputs across the constructs that could expose one.

**Reference set up per instructions:** fresh git worktree of the upstream repository at base_commit e28671187903e6aca2428374fdd504fca3032aee with patch.diff APPLIED (git apply clean; inspect.getsource asserts 'if v is not None' present in RegexPattern.match, so the post-patch body is the comparison target, NOT the base body).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE/DISPOSITION: No relaxation is claimed for this cell -- I checked: meta.json has no `relaxed_leakage` key (False), no RELAXED_LEAKAGE.md exists in the bundle, and gates.G-LEAK.status == "pass" (detail "spec view clean"). So this is an ordinary NO-LEAKAGE/LEAKAGE judgement, not an inherited-relaxation one, and I judged the consumer spec view on its own.

### WHAT I MEASURED (my own runs, not the bundle's assertions):
1. Spec view derived myself: markers.spec_view(model.py, nagini backend). Confirmed the impl region is elided (`...  # implementation elided`, no `r_keys = []`, no loop, no invariants). The consumer view = module docstring + imports + axioms comment + `pure` region (absent/kept_keys/kept_vals) + select_captures signature + pre/post-conditions. mapping.md, refinement.md, verdict.md, meta.json (which DO carry the verbatim gold hunk, `django/urls/resolvers.py:156`, `RegexPattern.match`, base_commit hash) are NOT part of the spec view -- confirmed by reading markers.spec_view/adapter.spec_view: the projection is over model.py only.
2. Re-ran the mechanical screen myself: leakage.screen(model.py, nagini, row['patch'], row['problem_statement'], test_patch) over the frozen instance.json -> passed=True, hard_failures=[], warnings=[]. Independently reproduced the near-miss it turns on: `_patch_changed_symbols`(gold) == {'match'}, and 'match' does NOT appear in the public problem_statement -- so an identifier or comment naming it would have been an L2/L5 hard failure. My own scan finds the substring 'match' ABSENT from the entire spec view (0 occurrences, case-insensitive), so the bundle clears the check on substance, not by allowlist.
3. Gold-line overlap: both changed lines ('kwargs = match.groupdict()' and 'kwargs = {k: v for k, v in match.groupdict().items() if v is not None}') whitespace-normalized -> neither is a substring of the normalized view. L2 paths: 'django/urls/resolvers.py' and the dotted 'django.urls.resolvers' both ABSENT; the only 'django' token is the public instance id in the header ('Twin-artifact model for django__django-11477'). base_commit hash e28671187903 ABSENT.
4. Vocabulary sweep I wrote myself over the view: ABSENT -- groupdict, 'is not None', 'is None', comprehension, dict,.items(), match.groups, kwargs, args, resolvers, RegexPattern, RoutePattern, reverse, `_reverse_with_prefix`, set_language, force_text, asymmetry, 'line 156',.diff, and the F2P test/pattern names (regex_optional, named_optional_terminated, with-arguments, urlpatterns, i18n). Narration sweep (harness list plus my own additions: diagnos*, 'should be', 'instead of', 'used to', 'no longer', 'filter out', 'drop the') -- no hits; 'bug', 'fix', 'patch', 'previously', 'incorrectly', 'wrong' all absent.
5. Core gates my disposition leans on, confirmed live rather than read off the stamp: adversary weakness on the bundle's own model.py -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 21.6s) = positive control; adversary same-spec on model_prepatch.py -> SAME (byte-identical spec region), and weakness on it -> NOT-A-COUNTEREXAMPLE, verification failed, i.e. the spec really does reject the unfiltered pre-patch impl (G-DIFF is real, so the spec is load-bearing about the discriminator rather than decorative).

**WHY THE REMAINING PS-ADJACENT CONTENT IS NOT LEAKAGE.** The three things a reader could argue about, and my reasoning on each:

(a) 'real Python ``None``' (2 occurrences, in the modelling-choice note and absent()'s docstring). This is the type-abstraction legend that makes the int-token carrier interpretable (ABSENT sentinel == the absence of a capture); it is a language-level fact about how an unparticipating group is represented, publicly documented in re.Match.groupdict, not a hints_text-only diagnosis. It names no repo symbol, no site, and no edit form -- unlike the hints, it does not say what to do about it (the hints' actual diagnosis, 'reverse()/force_text turns it into the literal string None', 'discard any arguments that are None', '`_reverse_with_prefix`', is nowhere in the view; note the hints even point at a DIFFERENT fix site than the gold, and the view echoes neither).

(b) 'the reported keyword mapping omits that group entirely rather than reporting it with an absent value' -- this is the desired post-patch behaviour stated abstractly, which is the twin's whole purpose in spec modes (1/2) and is explicitly not leakage per spec_guide §6 ('state the abstract desired behavior the issue demands, never the edit or the diagnosis'). It is a positive/negative contract clause, not a bug->fix narration; it never says 'previously' or 'was'.

(c) 'translate_url' (1 occurrence) is verbatim public -- the problem_statement's first line is 'translate_url() creates an incorrect URL when optional named groups are missing in the URL pattern', and the view attributes it as 'the translate_url consequence the issue describes'. 'optional', 'named group', 'missing/absent', 'URL pattern' are likewise all public PS vocabulary.
The edit site is disclosed to spec-mode solvers by DESIGN outside the view (eval/prompts renders meta.modeled_functions as 'select_captures (<-> django.urls.resolvers.RegexPattern.match)', the same localization mode 0 gets); that is harness-granted localization, not a spec-view leak, and the view itself carries none of it.

### BUNDLE-ADDRESSES-REVIEWER FINDINGS (reported per instruction, did not change my verdict, which I derived from my own runs above before reading them):
- verdict.md pre-records my exact role's answer -- 'Role 4 -- G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)' plus a full prior justification -- so a re-review of this cell is anchored to a verdict already in the artifact. It is a generated file ('generated by scripts/backfill_verdict_md.py'), not an instruction, and it does not tell me what to submit, but it is reviewer-facing prior-verdict text living inside the bundle under review. My NO-LEAKAGE is my measurement (items 1-5), and it happens to agree.
- verdict.md line 3 frames 'the agent's own verdict and notes are advisory context, not the source of truth for green'. That is a description of the runner, but as bundle prose it discounts the reviewing agent's verdict in advance; flagging it rather than acting on it.
- Minor integrity observation, non-leakage: meta.json's TOP-LEVEL region_hashes is stale relative to the shipped model.py (recorded spec_view 90caa95e..., computed 27114c44...; impl/invariants/pre-conditions also differ), while gates.G-HYGIENE.data.region_hashes matches the current file exactly (spec_view 27114c44...). The G-LEAK stamp (2026-08-14T07:44:55) postdates model.py (07:25), so the recorded pass does cover the shipped view -- and I re-ran the screen on the shipped bytes anyway, so my verdict does not rest on that stamp.

**VERDICT:** NO-LEAKAGE. No line of the consumer spec view reveals the gold edit (site, patched symbol, diff text, dict-comprehension form, or hints-only diagnosis) beyond the public problem_statement.

**SCOPE/DISPOSITION:** No relaxation is claimed for this cell -- I checked: meta.json has no `relaxed_leakage` key (False), no RELAXED_LEAKAGE.md exists in the bundle, and gates.G-LEAK.status == "pass" (detail "spec view clean"). So this is an ordinary NO-LEAKAGE/LEAKAGE judgement, not an inherited-relaxation one, and I judged the consumer spec view on its own.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
