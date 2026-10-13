# P2 adversarial audit — astropy__astropy-14508

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk8.py`, `atk10.py`, `atk11.py`, `atk12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 12 distinct same-spec attacks run; 11 REJECTED by the spec, and the single CANDIDATE (atk9, trim-boundary shift n>=20 instead of n>20) had its faithful refined patch EXECUTED through the official harness: run_resolve('astropy__astropy-14508', patch_atk9.diff, retries=1) -> RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False, patch_successfully_applied=True; FAIL_TO_PASS test_floating_point_string_representation_card PASSED, PASS_TO_PASS 174/174 PASSED, PASS_TO_FAIL 0, FAIL_TO_FAIL 0. Per the retained-attack-label rule this carries the ECHO verdict, not the reject lane: at n==20 the trim is the identity (take(20) of a 20-long seq; take(idx)+drop(idx)==whole), so its content is gold's. Corroborated out-of-band by a differential over 399,815 finite doubles including 4,966 len(str(v))==20 cases (exactly where the two refinements could differ) -> 0 divergences.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -214,35 +214,24 @@
                         e_index(shortest_seq(value, neg)))))
     # post-conditions-end
     # impl-start
-    vs = shortest_field(value, neg)
+    # PREPATCH: the fixed-precision .16G renderer (no minimality tie).
+    vs = padded_field(value, neg)
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
     if idx < 0:
         j = 0
         while j < 20:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
             Invariant(len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
             Invariant(MustTerminate(20 - j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
-        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
     else:
         keep = 20 - (n - idx)
         j = 0
@@ -250,45 +239,22 @@
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
             Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
             Invariant(0 <= j and j <= keep and len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
             Invariant(MustTerminate(keep - j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
-        Assert(ToSeq(result) == ToSeq(vs).take(keep))
         k = idx
         while k < n:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
             Invariant(keep == 20 - (n - idx) and keep >= 0)
             Invariant(len(result) == keep + (k - idx))
-            Invariant(ToSeq(result)
-                      == ToSeq(vs).take(keep)
-                      + ToSeq(vs).drop(idx).take(k - idx))
             Invariant(MustTerminate(n - k + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[k])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))
-            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])
-            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
-                   == ToSeq(vs).drop(idx).take(k - idx + 1))
             k = k + 1
-        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
-        Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
     return result
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -218,77 +218,23 @@
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
-    idx = e_index(ToSeq(vs))
+    # WRONG: always the first 20 characters, dropping any exponent suffix.
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
-    if idx < 0:
-        j = 0
-        while j < 20:
-            # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
-            Invariant(len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
-            Invariant(MustTerminate(20 - j + 1))
-            # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
-            j = j + 1
-        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
-    else:
-        keep = 20 - (n - idx)
-        j = 0
-        while j < keep:
-            # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
-            Invariant(0 <= j and j <= keep and len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
-            Invariant(MustTerminate(keep - j + 1))
-            # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
-            j = j + 1
-        Assert(ToSeq(result) == ToSeq(vs).take(keep))
-        k = idx
-        while k < n:
-            # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0)
-            Invariant(len(result) == keep + (k - idx))
-            Invariant(ToSeq(result)
-                      == ToSeq(vs).take(keep)
-                      + ToSeq(vs).drop(idx).take(k - idx))
-            Invariant(MustTerminate(n - k + 1))
-            # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[k])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))
-            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])
-            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
-                   == ToSeq(vs).drop(idx).take(k - idx + 1))
-            k = k + 1
-        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
-        Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
+    j = 0
+    while j < 20:
+        # invariants-start
+        Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
+        Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
+        Invariant(n == shortest_field_len(value, neg))
+        Invariant(ToSeq(vs) == shortest_seq(value, neg))
+        Invariant(len(result) == j)
+        Invariant(ToSeq(result) == ToSeq(vs).take(j))
+        Invariant(MustTerminate(20 - j + 1))
+        # invariants-end
+        old_seq = ToSeq(result)
+        result.append(vs[j])
+        Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
+        Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
+        j = j + 1
     return result
     # impl-end
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -214,16 +214,20 @@
                         e_index(shortest_seq(value, neg)))))
     # post-conditions-end
     # impl-start
-    vs = shortest_field(value, neg)
+    # A-LEG ATTACK: perturb the renderer's argument by a real-arithmetic
+    # IDENTITY.  Under --float-encoding=real this is provably `value`, so the
+    # axiom's Ensures transfer verbatim; the refined double arithmetic rounds.
+    w = (value + 1.0) - 1.0
+    Assert(w == value)
+    vs = shortest_field(w, neg)
+    Assert(ToSeq(vs) == shortest_seq(value, neg))
+    Assert(len(vs) == shortest_field_len(value, neg))
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
+    old_seq = ToSeq(result)
     if idx < 0:
         j = 0
         while j < 20:
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -214,16 +214,18 @@
                         e_index(shortest_seq(value, neg)))))
     # post-conditions-end
     # impl-start
-    vs = shortest_field(value, neg)
+    # A-LEG ATTACK (variant): a multiplicative real-arithmetic identity.
+    w = value * 3.0 / 3.0
+    Assert(w == value)
+    vs = shortest_field(w, neg)
+    Assert(ToSeq(vs) == shortest_seq(value, neg))
+    Assert(len(vs) == shortest_field_len(value, neg))
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
+    old_seq = ToSeq(result)
     if idx < 0:
         j = 0
         while j < 20:
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -214,24 +214,25 @@
                         e_index(shortest_seq(value, neg)))))
     # post-conditions-end
     # impl-start
-    vs = shortest_field(value, neg)
+    # WRONG: recover the sign flag from the value instead of using the carrier.
+    # Under the real encoding -0.0 == 0.0, so this renders "0.0" where the
+    # number is a negative zero.
+    neg2 = value < 0.0
+    vs = shortest_field(value, neg2)
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
+    old_seq = ToSeq(result)
     if idx < 0:
         j = 0
         while j < 20:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
+            Invariant(n == shortest_field_len(value, neg2))
+            Invariant(ToSeq(vs) == shortest_seq(value, neg2))
             Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
             Invariant(len(result) == j)
             Invariant(ToSeq(result) == ToSeq(vs).take(j))
@@ -242,7 +243,7 @@
             Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
             Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
-        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
+        Assert(ToSeq(result) == shortest_seq(value, neg2).take(20))
     else:
         keep = 20 - (n - idx)
         j = 0
@@ -250,8 +251,8 @@
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
+            Invariant(n == shortest_field_len(value, neg2))
+            Invariant(ToSeq(vs) == shortest_seq(value, neg2))
             Invariant(idx == e_index(ToSeq(vs)))
             Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
             Invariant(0 <= j and j <= keep and len(result) == j)
@@ -269,8 +270,8 @@
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
+            Invariant(n == shortest_field_len(value, neg2))
+            Invariant(ToSeq(vs) == shortest_seq(value, neg2))
             Invariant(idx == e_index(ToSeq(vs)))
             Invariant(keep == 20 - (n - idx) and keep >= 0)
             Invariant(len(result) == keep + (k - idx))
@@ -288,7 +289,7 @@
             k = k + 1
         Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
         Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
+               == shortest_seq(value, neg2).take(keep)
+               + shortest_seq(value, neg2).drop(idx))
     return result
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -218,13 +218,13 @@
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
-    if idx < 0:
+    old_seq = ToSeq(result)
+    # WRONG on part of the domain: only a suffix of EXACTLY 4 (E+32, E-05) takes
+    # the exponent-preserving path; a 3-digit exponent (E+308) falls through to
+    # the exponent-DROPPING first-20 truncation.  Correct on every tested value.
+    if idx < 0 or n - idx != 4:
         j = 0
         while j < 20:
             # invariants-start
@@ -232,7 +232,6 @@
             Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
             Invariant(n == shortest_field_len(value, neg))
             Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
             Invariant(len(result) == j)
             Invariant(ToSeq(result) == ToSeq(vs).take(j))
             Invariant(MustTerminate(20 - j + 1))
@@ -263,7 +262,6 @@
             Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
             Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
-        Assert(ToSeq(result) == ToSeq(vs).take(keep))
         k = idx
         while k < n:
             # invariants-start
@@ -286,9 +284,5 @@
             Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
                    == ToSeq(vs).drop(idx).take(k - idx + 1))
             k = k + 1
-        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
-        Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
     return result
     # impl-end
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -218,31 +218,20 @@
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
     if idx < 0:
-        j = 0
-        while j < 20:
+        # WRONG: same length, same multiset, reversed content.
+        j = 20
+        while j > 0:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
-            Invariant(len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
-            Invariant(MustTerminate(20 - j + 1))
+            Invariant(len(result) == 20 - j)
+            Invariant(MustTerminate(j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
-            j = j + 1
-        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
+            result.append(vs[j - 1])
+            j = j - 1
     else:
         keep = 20 - (n - idx)
         j = 0
@@ -250,45 +239,22 @@
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
             Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
             Invariant(0 <= j and j <= keep and len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
             Invariant(MustTerminate(keep - j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
-        Assert(ToSeq(result) == ToSeq(vs).take(keep))
         k = idx
         while k < n:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
             Invariant(keep == 20 - (n - idx) and keep >= 0)
             Invariant(len(result) == keep + (k - idx))
-            Invariant(ToSeq(result)
-                      == ToSeq(vs).take(keep)
-                      + ToSeq(vs).drop(idx).take(k - idx))
             Invariant(MustTerminate(n - k + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[k])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))
-            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])
-            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
-                   == ToSeq(vs).drop(idx).take(k - idx + 1))
             k = k + 1
-        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
-        Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
     return result
     # impl-end
```

Attack 8 — `atk8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -215,80 +215,8 @@
     # post-conditions-end
     # impl-start
     vs = shortest_field(value, neg)
-    n = len(vs)
-    if n <= 20:
-        return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
-    idx = e_index(ToSeq(vs))
-    result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
-    if idx < 0:
-        j = 0
-        while j < 20:
-            # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
-            Invariant(len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
-            Invariant(MustTerminate(20 - j + 1))
-            # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
-            j = j + 1
-        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
-    else:
-        keep = 20 - (n - idx)
-        j = 0
-        while j < keep:
-            # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
-            Invariant(0 <= j and j <= keep and len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
-            Invariant(MustTerminate(keep - j + 1))
-            # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
-            j = j + 1
-        Assert(ToSeq(result) == ToSeq(vs).take(keep))
-        k = idx
-        while k < n:
-            # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0)
-            Invariant(len(result) == keep + (k - idx))
-            Invariant(ToSeq(result)
-                      == ToSeq(vs).take(keep)
-                      + ToSeq(vs).drop(idx).take(k - idx))
-            Invariant(MustTerminate(n - k + 1))
-            # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[k])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))
-            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])
-            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
-                   == ToSeq(vs).drop(idx).take(k - idx + 1))
-            k = k + 1
-        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
-        Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
-    return result
+    # VACUITY CONTROL: if the axiom set were inconsistent at the proof point,
+    # or the postconditions discharged for free, this would verify.
+    Assert(False)
+    return vs
     # impl-end
```

Attack 9 — `atk9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -216,20 +216,17 @@
     # impl-start
     vs = shortest_field(value, neg)
     n = len(vs)
-    if n <= 20:
+    if n < 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
+    old_seq = ToSeq(result)
     if idx < 0:
         j = 0
         while j < 20:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
+            Invariant(0 <= j and j <= 20 and n == len(vs) and n >= 20)
             Invariant(n == shortest_field_len(value, neg))
             Invariant(ToSeq(vs) == shortest_seq(value, neg))
             Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
@@ -249,7 +246,7 @@
         while j < keep:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
+            Invariant(0 <= idx and idx < n and n == len(vs) and n >= 20)
             Invariant(n == shortest_field_len(value, neg))
             Invariant(ToSeq(vs) == shortest_seq(value, neg))
             Invariant(idx == e_index(ToSeq(vs)))
@@ -268,7 +265,7 @@
         while k < n:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
+            Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n >= 20)
             Invariant(n == shortest_field_len(value, neg))
             Invariant(ToSeq(vs) == shortest_seq(value, neg))
             Invariant(idx == e_index(ToSeq(vs)))
```

Attack 10 — `atk10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -218,77 +218,42 @@
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
-    idx = e_index(ToSeq(vs))
+    # WRONG: the over-cap branch renders with the OTHER (padded) renderer and
+    # trims THAT, so the output is not a trim of the exact rendering.
+    ws = padded_field(value, neg)
+    m = len(ws)
+    idx = e_index(ToSeq(ws))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
-    if idx < 0:
+    if idx < 0 or m <= 20:
         j = 0
         while j < 20:
             # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
+            Invariant(Acc(list_pred(ws)) and Acc(list_pred(result)))
+            Invariant(0 <= j and j <= 20 and m == len(ws))
             Invariant(len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
             Invariant(MustTerminate(20 - j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
+            if j < m:
+                result.append(ws[j])
+            else:
+                result.append(48)
             j = j + 1
-        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
     else:
-        keep = 20 - (n - idx)
+        keep = 20 - (m - idx)
         j = 0
-        while j < keep:
+        while j < 20:
             # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
-            Invariant(0 <= j and j <= keep and len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
-            Invariant(MustTerminate(keep - j + 1))
+            Invariant(Acc(list_pred(ws)) and Acc(list_pred(result)))
+            Invariant(0 <= j and j <= 20 and m == len(ws))
+            Invariant(len(result) == j)
+            Invariant(MustTerminate(20 - j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
+            if j < keep and j < m:
+                result.append(ws[j])
+            elif idx + (j - keep) < m and 0 <= idx + (j - keep):
+                result.append(ws[idx + (j - keep)])
+            else:
+                result.append(48)
             j = j + 1
-        Assert(ToSeq(result) == ToSeq(vs).take(keep))
-        k = idx
-        while k < n:
-            # invariants-start
-            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
-            Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0)
-            Invariant(len(result) == keep + (k - idx))
-            Invariant(ToSeq(result)
-                      == ToSeq(vs).take(keep)
-                      + ToSeq(vs).drop(idx).take(k - idx))
-            Invariant(MustTerminate(n - k + 1))
-            # invariants-end
-            old_seq = ToSeq(result)
-            result.append(vs[k])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))
-            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])
-            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
-                   == ToSeq(vs).drop(idx).take(k - idx + 1))
-            k = k + 1
-        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
-        Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
     return result
     # impl-end
```

Attack 11 — `atk11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -218,12 +218,9 @@
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
+    old_seq = ToSeq(result)
     if idx < 0:
         j = 0
         while j < 20:
@@ -235,7 +232,6 @@
             Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
             Invariant(len(result) == j)
             Invariant(ToSeq(result) == ToSeq(vs).take(j))
-            Invariant(MustTerminate(20 - j + 1))
             # invariants-end
             old_seq = ToSeq(result)
             result.append(vs[j])
@@ -243,6 +239,16 @@
             Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
         Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
+        # DIVERGENCE: spin forever once the (correct) content is built.
+        spin = 0
+        while spin >= 0:
+            # invariants-start
+            Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
+            Invariant(spin >= 0)
+            Invariant(len(result) == 20)
+            Invariant(ToSeq(result) == shortest_seq(value, neg).take(20))
+            # invariants-end
+            spin = spin + 1
     else:
         keep = 20 - (n - idx)
         j = 0
```

Attack 12 — `atk12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -218,77 +218,43 @@
     n = len(vs)
     if n <= 20:
         return vs
-    # Over the cap: trim to 20 characters, preserving any exponent suffix. The
-    # carrier `vs` IS the exact rendering (ToSeq(vs) == shortest_seq(value, neg)),
-    # so the trim is stated structurally against it via take/drop/concat.
     idx = e_index(ToSeq(vs))
     result = []  # type: List[int]
-    old_seq = ToSeq(result)  # type carrier for the per-append step (see below)
     if idx < 0:
         j = 0
         while j < 20:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= j and j <= 20 and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)) and idx < 0)
             Invariant(len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
             Invariant(MustTerminate(20 - j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
-        Assert(ToSeq(result) == shortest_seq(value, neg).take(20))
     else:
-        keep = 20 - (n - idx)
+        # WRONG: keep+1 significand chars, exponent suffix truncated by one.
+        keep = 20 - (n - idx) + 1
         j = 0
         while j < keep:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx < n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0 and keep <= idx)
+            Invariant(keep == 20 - (n - idx) + 1 and keep >= 0 and keep <= idx)
             Invariant(0 <= j and j <= keep and len(result) == j)
-            Invariant(ToSeq(result) == ToSeq(vs).take(j))
             Invariant(MustTerminate(keep - j + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[j])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[j]))
-            Assert(ToSeq(vs).take(j) + PSeq(ToSeq(vs)[j]) == ToSeq(vs).take(j + 1))
             j = j + 1
-        Assert(ToSeq(result) == ToSeq(vs).take(keep))
         k = idx
-        while k < n:
+        while k < n - 1:
             # invariants-start
             Invariant(Acc(list_pred(vs)) and Acc(list_pred(result)))
             Invariant(0 <= idx and idx <= k and k <= n and n == len(vs) and n > 20)
-            Invariant(n == shortest_field_len(value, neg))
-            Invariant(ToSeq(vs) == shortest_seq(value, neg))
-            Invariant(idx == e_index(ToSeq(vs)))
-            Invariant(keep == 20 - (n - idx) and keep >= 0)
+            Invariant(keep == 20 - (n - idx) + 1 and keep >= 0)
             Invariant(len(result) == keep + (k - idx))
-            Invariant(ToSeq(result)
-                      == ToSeq(vs).take(keep)
-                      + ToSeq(vs).drop(idx).take(k - idx))
             Invariant(MustTerminate(n - k + 1))
             # invariants-end
-            old_seq = ToSeq(result)
             result.append(vs[k])
-            Assert(ToSeq(result) == old_seq + PSeq(vs[k]))
-            Assert(ToSeq(vs).drop(idx)[k - idx] == ToSeq(vs)[k])
-            Assert(ToSeq(vs).drop(idx).take(k - idx) + PSeq(ToSeq(vs).drop(idx)[k - idx])
-                   == ToSeq(vs).drop(idx).take(k - idx + 1))
             k = k + 1
-        Assert(ToSeq(vs).drop(idx).take(n - idx) == ToSeq(vs).drop(idx))
-        Assert(ToSeq(result)
-               == shortest_seq(value, neg).take(keep)
-               + shortest_seq(value, neg).drop(idx))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** adversarial G-EQ (refinement fidelity, docs/architecture.md §5) for nagini astropy__astropy-14508. R/I legs left to G-CONF (pass, 113,967 checked / 0 disagreements); concentrated on the A legs and the model<->patch correspondence. Work confined to  Attacks built by gen.py/build.py, which split model.py on the impl-start/impl-end markers and substitute ONLY the impl body, so axioms/@Pure/Requires/Ensures are byte-identical BY CONSTRUCTION. Re-ran both builders after verification and re-checked markers.spec_signature directly: 12/12 spec signatures byte-identical to the frozen model, so the verified bytes are the submitted bytes.

**BASELINES.** positive_control = model.py VERBATIM (md5 a71b4a94e49feb3bfc3537926fb9df7e, byte-identical to the bundle's model.py, confirmed programmatically) -> `bash scripts/nagini_verify.sh --float-encoding=real.../pos_control.py` -> 'Verification successful', 24.48s, exit 0. PREPATCH BUG re-encoded as atk1 (= model_prepatch.py impl: the padded_field/.16G renderer with no minimality tie) -> weakness exit 2, does NOT verify => prepatch_reproduced=True; G-DIFF discriminating power confirmed on the fits-branch minimality clause.

**SPEC SHAPE.** The three post-condition implications partition the domain disjointly+exhaustively and each pins ToSeq(Result()) by CONTENT, not length: (C3) shortest_field_len<=20 => == shortest_seq(value,neg); (C4) len>20 & e_index<0 => == shortest_seq.take(20); (C5) len>20 & 0<=e_index => == take(20-(len-idx)) + drop(idx). Plus 1<=len<=20 and method-level MustTerminate(10).

ALL 12 ATTACKS — command `python -m swebench_unified.adversary weakness nagini astropy__astropy-14508 <path>` (SBU_BENCHMARK_DIR=benchmark-verified), same-spec exit 0 for every one:
- atk1.py  PREPATCH BUG (padded_field renderer): exit 2 REJECTED.
- atk2.py  PRIOR-PASS COUNTEREXAMPLE re-encoded (over-cap ALWAYS first-20, drops the exponent suffix; the mapping.md-named case, wrong on P2P -4.6737463674763E+32): exit 2 REJECTED.
- atk3.py  PRIMARY A-LEG / REAL-vs-DOUBLE ARITHMETIC GAP: renders the perturbed argument w=(value+1.0)-1.0, a real-arithmetic IDENTITY, so under --float-encoding=real every spec symbol should transfer verbatim while the refined double arithmetic ROUNDS. Ground truth for its refined patch: `_format_float`(0.009125) -> '0.00912500000000005' (19 chars) instead of '0.009125' — precisely the comment-truncation the F2P test forbids, so had this verified the spec would have been BROKEN. exit 2 REJECTED, error: 'Assert might fail. Assertion (w == value) might not hold.'
- atk4.py  A-LEG VARIANT (multiplicative identity w=`value*3`.0/3.0; in doubles -99.9*3/3 == -99.90000000000002, F2P value #3): exit 2 REJECTED, same Assert failure.
  ROOT CAUSE probed directly (probe_arith.py, model.py verbatim + 5 appended probe fns): under --float-encoding=real Nagini leaves float ARITHMETIC uninterpreted — (value+1.0)-1.0==value, value+0.0==value, `value*1`.0==value and value+value==2.0*value are ALL unprovable, while 0.0==-0.0 verifies. So the encoding gives order/equality on reals but no algebraic laws over +,*,-; the arithmetic-gap attack class is closed at the verifier, not by luck.
- atk5.py  SIGN CARRIER DROPPED: recovers neg2 = value < 0.0 from the value instead of using the pair's flag, so a negative zero renders '0.0' where the real callee gives '-0.0': exit 2 REJECTED — the pair carrier is genuinely load-bearing, not decoration.
- atk6.py  PARTIAL DOMAIN: exponent-preserving trim applied ONLY when the suffix is exactly 4 chars (E+32/E-05); a 3-digit exponent (E+308, suffix 5) falls through to the exponent-DROPPING first-20 truncation. Correct on every tested value, wrong on part of the domain: exit 2 REJECTED — the spec is domain-complete, not test-shaped.
- atk7.py  CONTROL-FLOW-EFFECT: no-E over-cap branch emits the first 20 characters REVERSED (same length, same multiset, wrong content): exit 2 REJECTED (C4 content).
- atk8.py  VACUITY CONTROL: Assert(False) after the renderer call, then return vs: exit 2 REJECTED => the axiom set is CONSISTENT at the proof point and the postconditions are not discharged for free (the guarded-self-call / vacuous-guard failure mode is absent).
- atk9.py  BOUNDARY-SHIFT: enters the trim path at n>=20 instead of n>20. CANDIDATE (shares spec AND verifies, 38.3s) — RESOLVE-RUN, see counterexample field: RESOLVED=True => ECHO, not weakness.
- atk10.py UNGROUNDED-ORACLE ECHO: fits branch uses shortest_field (so C3 is provable) but the over-cap branch renders with the OTHER (padded) renderer and trims THAT, so the output is not a trim of the exact rendering: exit 2 REJECTED (C4/C5 content).
- atk11.py NON-TERMINATION: builds gold's exact content on the no-E over-cap path, then spins forever (`while spin >= 0`) with MustTerminate dropped from that loop only. Its faithful patch would HANG the suite, so a verifying divergent impl would be a break. exit 2 REJECTED — the method-level MustTerminate(10) rejects it (consistent with the known rule that loop invariants alone do not reject a diverging rival).
- atk12.py BOUNDARY, length-preserving: E path keeps one EXTRA significand character and drops the LAST exponent character — still exactly 20 chars, wrong content: exit 2 REJECTED.
=> 11 DISTINCT wrong impls REJECTED (prepatch, prior counterexample, TWO arithmetic-gap A-leg attacks, sign-carrier-dropped, partial-domain, control-flow-effect, vacuity control, ungrounded-oracle, non-termination, boundary); 1 CANDIDATE, materialized and resolve-run, RESOLVED (echo).

REFINEMENT.MD AUDIT (legs A1–A7). Tag tally parsed mechanically from the table: 3 R + 3 'R + I' + 1 A-reference. NO kind-3 leg and NO A-consumed leg is claimed — correctly so: I enumerated the @ContractOnly symbols in the axioms region (parse_dec, sig_count, min_sig, shortest_field_len, shortest_seq, shortest_field, padded_field) and format_float_field is NOT among them, so the proof never consumes an Ensures about the changed function itself. Section C's claim holds.
The single A leg is A2 (shortest_field + its @Pure value companion shortest_seq) as the deep model of str(value).replace('e','E'). Correspondence checked independently rather than trusted from prose:
  * G-AX re-run from the bundle dir: `python axiom_check.py` -> exit 0, 'G-AX OK: shortest_field == the real callee on the pair each double refines to... over 29 boundary + 200000 fuzz + 4001 integer + 20000 subnormal finite floats; exponent suffix <= 5 throughout'.
  * INDEPENDENT re-derivation of EVERY A2 clause against the real callee over 349,873 finite doubles (boundary set + 300k raw 64-bit patterns + 50k uniform), with my own sig_count/min_sig implementations: pair-is-a-complete-invariant 0 violations, round-trip 0, minimal-sig-digits 0, leading-minus-iff-neg 0 (both directions), exponent-suffix<=5 0, len 0. Minimum over-cap keep = 20-(len-idx) = 15 >= 0, so the suffix<=5 clause really is what makes the trim arithmetic well-defined.
  * The CHANGED property is genuinely in the axiom's Ensures (not hidden behind an axiom about the changed function): sig_count(shortest_seq)==min_sig (minimality) + parse_dec==value (round-trip) + len==shortest_field_len + suffix<=5. F2P discriminator spot-checked on all three regression values: gold str() spends 4/3/3 significant digits ('0.009125','8.95','-99.9') vs.16G's 16 ('0.009124999999999999','8.949999999999999','-99.90000000000001').
  * MODEL<->PATCH CORRESPONDENCE checked at SOURCE level: extracted card.py at base_commit a3f4ae6cd24d from the upstream repository, applied patch.diff (patch -p1, exit 0) in my scratch dir, and read the resulting `_format_float`. It is exactly `value_str = str(value).replace('e','E')` then the unchanged `if (str_len:= len(value_str)) > 20:` / `find('E')` / `[:20]` / `[:20-(str_len-idx)] + [idx:]` — a 1:1 match to A2–A7 with no unmodelled operation. A1's pair refinement is sound per the complete-invariant check above.
  * DOMAIN claim confirmed at source: `_format_float` has exactly two call sites, both in `_format_value` (card.py:1288 float/np.floating, card.py:1291 complex real/imag), and inf/nan are rejected upstream (test_assign_inf_nan, P2P), so the finite-float domain the axioms are stated over is the real one.
  * padded_field is the faithful pre-patch renderer, deliberately weak (no minimality, and correctly NO round-trip claim since.16G does not always round-trip) and referenced only from model_prepatch.py.

**VERDICT COVERAGE.** Nagini was run with --float-encoding=real, per meta.json. Every one of the verifications reached a real verdict in 24–39s, with no timeout and no crash, and the resolve run completed on attempt 1 with flaky=False. So no leg of this audit is INCONCLUSIVE, and each outcome below is a verifier judgment on the attack rather than an unfinished run.

**CONCLUSION:** 11 distinct wrong impls rejected — including the prepatch bug, the prior pass's named counterexample, TWO new real-vs-double arithmetic A-leg attacks aimed squarely at the interpreted-float refinement, a sign-carrier-dropped case, a partial-domain case, a non-termination case and a vacuity control. The one verifying same-spec impl is a content-equal echo whose faithful patch was EXECUTED through the official harness and RESOLVED. The over-cap branch is pinned structurally by content, so length-only evasions die; the fits branch is pinned by minimality, so precision evasions die; MustTerminate at the method level kills divergence; and the A-leg's correspondence to the real callee holds under independent re-derivation and source-level reading of the patched function. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk8.py`, `atk10.py`, `atk11.py`, `atk12.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl found. 12 distinct same-spec attacks run; 11 REJECTED by the spec, and the single CANDIDATE (atk9, trim-boundary shift n>=20 instead of n>20) had its faithful refined patch EXECUTED through the official harness: run_resolve('astropy__astropy-14508', patch_atk9.diff, retries=1) -> RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False, patch_successfully_applied=True; FAIL_TO_PASS test_floating_point_string_representation_card PASSED, PASS_TO_PASS 174/174 PASSED, PASS_TO_FAIL 0, FAIL_TO_FAIL 0. Per the retained-attack-label rule this carries the ECHO verdict, not the reject lane: at n==20 the trim is the identity (take(20) of a 20-long seq; take(idx)+drop(idx)==whole), so its content is gold's. Corroborated out-of-band by a differential over 399,815 finite doubles including 4,966 len(str(v))==20 cases (exactly where the two refinements could differ) -> 0 divergences.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk12.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** adversarial G-EQ (refinement fidelity, docs/architecture.md §5) for nagini astropy__astropy-14508. R/I legs left to G-CONF (pass, 113,967 checked / 0 disagreements); concentrated on the A legs and the model<->patch correspondence. Work confined to  Attacks built by gen.py/build.py, which split model.py on the impl-start/impl-end markers and substitute ONLY the impl body, so axioms/@Pure/Requires/Ensures are byte-identical BY CONSTRUCTION. Re-ran both builders after verification and re-checked markers.spec_signature directly: 12/12 spec signatures byte-identical to the frozen model, so the verified bytes are the submitted bytes.

**BASELINES.** positive_control = model.py VERBATIM (md5 a71b4a94e49feb3bfc3537926fb9df7e, byte-identical to the bundle's model.py, confirmed programmatically) -> `bash scripts/nagini_verify.sh --float-encoding=real.../pos_control.py` -> 'Verification successful', 24.48s, exit 0. PREPATCH BUG re-encoded as atk1 (= model_prepatch.py impl: the padded_field/.16G renderer with no minimality tie) -> weakness exit 2, does NOT verify => prepatch_reproduced=True; G-DIFF discriminating power confirmed on the fits-branch minimality clause.

**SPEC SHAPE.** The three post-condition implications partition the domain disjointly+exhaustively and each pins ToSeq(Result()) by CONTENT, not length: (C3) shortest_field_len<=20 => == shortest_seq(value,neg); (C4) len>20 & e_index<0 => == shortest_seq.take(20); (C5) len>20 & 0<=e_index => == take(20-(len-idx)) + drop(idx). Plus 1<=len<=20 and method-level MustTerminate(10).

ALL 12 ATTACKS — command `python -m swebench_unified.adversary weakness nagini astropy__astropy-14508 <path>` (SBU_BENCHMARK_DIR=benchmark-verified), same-spec exit 0 for every one:
- atk1.py  PREPATCH BUG (padded_field renderer): exit 2 REJECTED.
- atk2.py  PRIOR-PASS COUNTEREXAMPLE re-encoded (over-cap ALWAYS first-20, drops the exponent suffix; the mapping.md-named case, wrong on P2P -4.6737463674763E+32): exit 2 REJECTED.
- atk3.py  PRIMARY A-LEG / REAL-vs-DOUBLE ARITHMETIC GAP: renders the perturbed argument w=(value+1.0)-1.0, a real-arithmetic IDENTITY, so under --float-encoding=real every spec symbol should transfer verbatim while the refined double arithmetic ROUNDS. Ground truth for its refined patch: `_format_float`(0.009125) -> '0.00912500000000005' (19 chars) instead of '0.009125' — precisely the comment-truncation the F2P test forbids, so had this verified the spec would have been BROKEN. exit 2 REJECTED, error: 'Assert might fail. Assertion (w == value) might not hold.'
- atk4.py  A-LEG VARIANT (multiplicative identity w=`value*3`.0/3.0; in doubles -99.9*3/3 == -99.90000000000002, F2P value #3): exit 2 REJECTED, same Assert failure.
  ROOT CAUSE probed directly (probe_arith.py, model.py verbatim + 5 appended probe fns): under --float-encoding=real Nagini leaves float ARITHMETIC uninterpreted — (value+1.0)-1.0==value, value+0.0==value, `value*1`.0==value and value+value==2.0*value are ALL unprovable, while 0.0==-0.0 verifies. So the encoding gives order/equality on reals but no algebraic laws over +,*,-; the arithmetic-gap attack class is closed at the verifier, not by luck.
- atk5.py  SIGN CARRIER DROPPED: recovers neg2 = value < 0.0 from the value instead of using the pair's flag, so a negative zero renders '0.0' where the real callee gives '-0.0': exit 2 REJECTED — the pair carrier is genuinely load-bearing, not decoration.
- atk6.py  PARTIAL DOMAIN: exponent-preserving trim applied ONLY when the suffix is exactly 4 chars (E+32/E-05); a 3-digit exponent (E+308, suffix 5) falls through to the exponent-DROPPING first-20 truncation. Correct on every tested value, wrong on part of the domain: exit 2 REJECTED — the spec is domain-complete, not test-shaped.
- atk7.py  CONTROL-FLOW-EFFECT: no-E over-cap branch emits the first 20 characters REVERSED (same length, same multiset, wrong content): exit 2 REJECTED (C4 content).
- atk8.py  VACUITY CONTROL: Assert(False) after the renderer call, then return vs: exit 2 REJECTED => the axiom set is CONSISTENT at the proof point and the postconditions are not discharged for free (the guarded-self-call / vacuous-guard failure mode is absent).
- atk9.py  BOUNDARY-SHIFT: enters the trim path at n>=20 instead of n>20. CANDIDATE (shares spec AND verifies, 38.3s) — RESOLVE-RUN, see counterexample field: RESOLVED=True => ECHO, not weakness.
- atk10.py UNGROUNDED-ORACLE ECHO: fits branch uses shortest_field (so C3 is provable) but the over-cap branch renders with the OTHER (padded) renderer and trims THAT, so the output is not a trim of the exact rendering: exit 2 REJECTED (C4/C5 content).
- atk11.py NON-TERMINATION: builds gold's exact content on the no-E over-cap path, then spins forever (`while spin >= 0`) with MustTerminate dropped from that loop only. Its faithful patch would HANG the suite, so a verifying divergent impl would be a break. exit 2 REJECTED — the method-level MustTerminate(10) rejects it (consistent with the known rule that loop invariants alone do not reject a diverging rival).
- atk12.py BOUNDARY, length-preserving: E path keeps one EXTRA significand character and drops the LAST exponent character — still exactly 20 chars, wrong content: exit 2 REJECTED.
=> 11 DISTINCT wrong impls REJECTED (prepatch, prior counterexample, TWO arithmetic-gap A-leg attacks, sign-carrier-dropped, partial-domain, control-flow-effect, vacuity control, ungrounded-oracle, non-termination, boundary); 1 CANDIDATE, materialized and resolve-run, RESOLVED (echo).

REFINEMENT.MD AUDIT (legs A1–A7). Tag tally parsed mechanically from the table: 3 R + 3 'R + I' + 1 A-reference. NO kind-3 leg and NO A-consumed leg is claimed — correctly so: I enumerated the @ContractOnly symbols in the axioms region (parse_dec, sig_count, min_sig, shortest_field_len, shortest_seq, shortest_field, padded_field) and format_float_field is NOT among them, so the proof never consumes an Ensures about the changed function itself. Section C's claim holds.
The single A leg is A2 (shortest_field + its @Pure value companion shortest_seq) as the deep model of str(value).replace('e','E'). Correspondence checked independently rather than trusted from prose:
  * G-AX re-run from the bundle dir: `python axiom_check.py` -> exit 0, 'G-AX OK: shortest_field == the real callee on the pair each double refines to... over 29 boundary + 200000 fuzz + 4001 integer + 20000 subnormal finite floats; exponent suffix <= 5 throughout'.
  * INDEPENDENT re-derivation of EVERY A2 clause against the real callee over 349,873 finite doubles (boundary set + 300k raw 64-bit patterns + 50k uniform), with my own sig_count/min_sig implementations: pair-is-a-complete-invariant 0 violations, round-trip 0, minimal-sig-digits 0, leading-minus-iff-neg 0 (both directions), exponent-suffix<=5 0, len 0. Minimum over-cap keep = 20-(len-idx) = 15 >= 0, so the suffix<=5 clause really is what makes the trim arithmetic well-defined.
  * The CHANGED property is genuinely in the axiom's Ensures (not hidden behind an axiom about the changed function): sig_count(shortest_seq)==min_sig (minimality) + parse_dec==value (round-trip) + len==shortest_field_len + suffix<=5. F2P discriminator spot-checked on all three regression values: gold str() spends 4/3/3 significant digits ('0.009125','8.95','-99.9') vs.16G's 16 ('0.009124999999999999','8.949999999999999','-99.90000000000001').
  * MODEL<->PATCH CORRESPONDENCE checked at SOURCE level: extracted card.py at base_commit a3f4ae6cd24d from the upstream repository, applied patch.diff (patch -p1, exit 0) in my scratch dir, and read the resulting `_format_float`. It is exactly `value_str = str(value).replace('e','E')` then the unchanged `if (str_len:= len(value_str)) > 20:` / `find('E')` / `[:20]` / `[:20-(str_len-idx)] + [idx:]` — a 1:1 match to A2–A7 with no unmodelled operation. A1's pair refinement is sound per the complete-invariant check above.
  * DOMAIN claim confirmed at source: `_format_float` has exactly two call sites, both in `_format_value` (card.py:1288 float/np.floating, card.py:1291 complex real/imag), and inf/nan are rejected upstream (test_assign_inf_nan, P2P), so the finite-float domain the axioms are stated over is the real one.
  * padded_field is the faithful pre-patch renderer, deliberately weak (no minimality, and correctly NO round-trip claim since.16G does not always round-trip) and referenced only from model_prepatch.py.

**VERDICT COVERAGE.** Nagini was run with --float-encoding=real, per meta.json. Every one of the verifications reached a real verdict in 24–39s, with no timeout and no crash, and the resolve run completed on attempt 1 with flaky=False. So no leg of this audit is INCONCLUSIVE, and each outcome below is a verifier judgment on the attack rather than an unfinished run.

**CONCLUSION:** 11 distinct wrong impls rejected — including the prepatch bug, the prior pass's named counterexample, TWO new real-vs-double arithmetic A-leg attacks aimed squarely at the interpreted-float refinement, a sign-carrier-dropped case, a partial-domain case, a non-termination case and a vacuity control. The one verifying same-spec impl is a content-equal echo whose faithful patch was EXECUTED through the official harness and RESOLVED. The over-cap branch is pinned structurally by content, so length-only evasions die; the fits branch is pinned by minimality, so precision evasions die; MustTerminate at the method level kills divergence; and the A-leg's correspondence to the real callee holds under independent re-derivation and source-level reading of the patched function. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**Reference used:** worktree at base_commit a3f4ae6cd24d5ecdf49f213d77b3513dd509a06c with patch.diff APPLIED (git apply succeeded); base commit used only for untouched callees (str(float), float(), the unchanged trim).

**WHAT I ATTACKED.** The spec's post-conditions pin the output uniquely in all three branches (fits-under-cap => shortest_seq; over-cap without E => take(20); over-cap with E => take(20-(len-idx)) + drop(idx)). So the spec is a total function of (value, neg), and I could execute the SPEC itself and diff it against the real patched callee rather than merely re-running the impl.

EVIDENCE 1 - spec vs real callee, 789,570 finite doubles, 0 divergences. I extracted the real patched `_format_float` via ast.get_source_segment from the applied worktree (importing astropy failed: unbuilt C extensions - not a spec issue), realized the axioms per mapping.md 3.1 (shortest_seq = str(copysign(value,neg)).replace('e','E')), computed the unique spec-admitted field, and compared to the real function. Corpus: 50 boundary values (both zeros, 1/3, pi, 5e-324, 1e-323, smallest normal, DBL_MAX, the F2P values 0.009125/8.95/-99.9, both P2P scientific-notation trim values, 1e15..1e17 fixed/scientific switch, 123456789012345678901.0) + 400k raw 64-bit patterns + 200k `mantissa*10`^exp (exp -320..308) + 100k subnormal-range draws + 10001 small integers, i/7.0, `i*1e`-320 + 20k dense `k*5e`-324 and +/-`k*1e`-5. Zero divergences. Independent seed (20250815), not the bundle's pinned 14508, so this is not a replay of conformance_check.py.

EVIDENCE 2 - branch coverage measured, so the null result is not vacuous: fits-branch 116,141; over-cap no-exponent 5,116; over-cap exponent-preserving 668,275; negative inputs 384,641; negative zero 1; exact-length-20 fields 19,279. All three post-condition branches, including both over-cap arms, are heavily exercised.

EVIDENCE 3 - the minimality clause grounded NON-CIRCULARLY. axiom_check.py defines min_sig(value):= sig_count(shortest_field(value)), so its assertion sig_count(shortest_field)==min_sig is a tautology and does NOT establish the spec's stated meaning ('the FEWEST significant digits any decimal field needs'). This was the strongest available faithfulness attack: if repr were ever non-minimal, the spec's sig_count==min_sig clause would over-claim. I re-derived true_min_sig independently with exact Decimal arithmetic, searching k=1.. and testing BOTH ROUND_FLOOR and ROUND_CEILING candidates at each k (deliberately avoiding the %g round-to-nearest pitfall mapping.md section 3.4 documents for 2**-24). 105,984 nonzero finite doubles incl. 2**-24 and all boundary/P2P values: 0 minimality gaps. The clause holds under an independent definition, so it is not an over-claim.

EVIDENCE 4 - axiom clauses vs real callee, inline in the same sweep: shortest_seq == str(d).replace('e','E') exactly; sign clause (field[0]=='-') iff neg (incl. -0.0 -> '-0.0' vs 0.0 -> '0.0'); len(field)>=2 when neg; exponent suffix <=5 whenever E present (this is what makes keep = 20-(n-idx) >= 0 sound, so the trim arithmetic never underflows); round-trip float(field)==value. All held on every input.

EVIDENCE 5 - bundle gates reproduce: axiom_check.py exit 0; scripts/nagini_verify.sh model.py => 'Verification successful' (22.17s).

PRECONDITION / DOMAIN AUDIT (checked for illegitimate narrowing, the usual too-strong failure mode). Requires are only MustTerminate(10), Implies(value>0, not neg), Implies(value<0, neg). These exclude exactly the pairs that denote no signed number; every finite double still has a pair, -0.0 included. I confirmed the pair is a complete invariant (d+0.0 bit-identical for nonzero d; neg disambiguates the zeros) and that -0.0 genuinely reaches the callee: card.py:343-351 guards only isnan/isinf, and -0.0 is neither, so it flows `_format_value` (card.py:1287) -> `_format_float`. So the pair carrier widens expressiveness rather than narrowing the domain - notably it is NOT an artifact of the gold change, since the pre-patch f'{d:.16G}' also distinguishes the two zeros. Excluding inf/nan is justified, not convenient: Header.set raises ValueError first (P2P test_assign_inf_nan), so they are outside the callee's reachable domain.

RESIDUAL, examined and judged NOT a faithfulness defect: `_format_value` also dispatches np.floating to `_format_float`, and str(np.float32(0.1)) == '0.1' whereas the double model gives '0.10000000149011612' - i.e. narrower numpy floats would diverge from the double abstraction. I did not report this because (a) the spec/mapping explicitly scope the model to finite Python doubles, which is a stated abstraction boundary rather than a silent one; (b) no F2P or P2P test in this instance passes a non-double np.floating through the rendering path - the sole numpy-float reference in test_header.py is line 2386, np.float32('nan'), which is rejected upstream by the ValueError guard and never reaches the renderer; and (c) the gold patch itself is likewise agnostic here, so this is not a divergence between the model and the patched repo behavior on the modeled domain. It is a scope note, not an input on which the modeled function disagrees with the real callee.

**CONCLUSION.** I could not produce any input on which the modeled function disagrees with the real patched callee. The spec is not too strong: its preconditions exclude only non-numbers and upstream-rejected non-finites, and its post-conditions match the real fixed behavior exactly (789,570 inputs, all branches, independent seed), with the one circularly-grounded axiom clause independently re-verified. Verdict FAITHFUL - no diverging input exists to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE / PROVENANCE. No `relaxed_leakage` key in meta.json (confirmed: 'relaxed_leakage' in meta -> False) and no RELAXED_LEAKAGE.md anywhere under the instance dir (find -iname '*relax*' -> empty). So this is a plain, non-relaxed leakage judgement; I inherited no disposition and had no unavoidability argument to re-derive.

**BUNDLE-ADDRESSES-REVIEWER CHECK.** Swept every bundle file (model.py, model_prepatch.py, mapping.md, refinement.md, meta.json, verdict.md, properties.py, axiom_check.py, conformance_check.py) for text instructing the auditor/panel or prescribing a verdict, by grep (reviewer|panel|attacker|adversar|honest verdict|NO-LEAKAGE|submit_result|gate FAIL|you must submit|dear reviewer|do not report) and via the harness's own swebench_unified.leakage.reviewer_directed() on model.py / mapping.md / refinement.md -> [] for all three. NOTHING in the bundle tried to tell me what to record.

One thing worth flagging as a finding in its own right, though it is not an instruction to me: meta.json G-LEAK/G-PANEL-3 and verdict.md carry a PRIOR panel note asserting 'NO-LEAKAGE' with spec_view sha256 3b129527ae0d... and a ONE-ARGUMENT discriminator `shortest_field_len(value)`. The shipped spec is TWO-ARGUMENT (`shortest_field_len(value, neg)`) and its spec_view hashes 22a1fd0590b5..., so that prior note is STALE and describes an earlier spec revision. I treated it as inadmissible and re-derived everything below myself; in particular the entire sign / negative-zero facet is new material the prior note never examined.

ALSO NOTED (integrity, not leakage): meta.json's TOP-LEVEL region_hashes block is stale vs the shipped model.py (spec_view 4dead621be7c... != computed 22a1fd0590b5...). The G-HYGIENE gate record's region_hashes, however, match my own computation byte-for-byte on all 7 regions (axioms, pure, pre-conditions, post-conditions, invariants, impl, spec_view all True). Cosmetic staleness in a non-gate field; the gate record itself is sound.

**SPEC VIEW PINNED.** Computed the consumer projection myself: markers.spec_view(model.py, get_backend('nagini')) -> sha256 22a1fd0590b53f423281fe203e5f19ab454cc9296d087a60555237f4bcfeecc6, byte-identical to the G-HYGIENE gate record. Regions exposed = (axioms, pure, pre-conditions, post-conditions) + module docstring; the impl region is elided to `...  # implementation elided`. Confirmed via eval/adapter.py:304 that spec_view IS the consumer's view and that mapping.md / refinement.md are NOT shown to the solver (they do name `.16G` and `str(value)`, so this scoping matters; they are audit docs, correctly outside the spec view). Harness leak screen L.screen(model.py, backend, patch, problem_statement, test_patch) -> hard_failures=[], warnings=[].

**TOKEN GREP OVER THE EXTRACTED SPEC VIEW.** Zero hits for:.16G, 16G, str(, format(, repr, `_format_float`, card.py, CPython, Grisu, shortest-repr, zero-pad, 'exponent is zero', signbit, copysign, replace, patch, gold, pre-patch, prepatch. The renderers are characterized purely property-wise (parse_dec round-trip, sig_count == min_sig, len == shortest_field_len, suffix <= 5, leading code point 45 iff negative). The spec view never names the Python construct the gold edit swaps in.

DISCRIMINATOR IS PUBLIC IN problem_statement (NOT hints). Substring probes against instance.json['problem_statement'] all True, and confirmed present WITHOUT relying on hints_text: 'larger than necessary' (True/hints False), '0.009124999999999999' (True/False), '.16G' (True/False), 'str(value)' (True), 'string representation provided by Python' (True/False), 'does not fit in 20 characters' (True/False), '`_format_float`' (True/False), 'card.py#L1300' (True/False), '0.009125' (True/False). The public issue therefore already states the file, the function, the exact line link, the offending format spec `.16G`, the concrete wrong output, the proposed remedy (use Python's str), AND the 20-character fallback condition. The spec view states strictly LESS than the public issue: it says 'minimal significant digits, round-trips, 20-char cap' without ever naming str/.16G/card.py.

### LOAD-BEARING RE-DERIVATION (my measurements, all with the pinned verifier scripts/nagini_verify.sh):
(1) gold model.py -> 'Verification successful' (23.53s), exit 0.

(2) model_prepatch.py shares the bundle's EXACT spec: `adversary same-spec nagini astropy__astropy-14508 pre.py` -> exit 0, 'SAME - attack shares the bundle's exact specification'. It differs only in the impl region, substituting padded_field (the faithful.16G pre-patch renderer) for shortest_field.

(3) prepatch -> 'Verification failed', with exactly: 'pre.py:195:13:196:65: error: Postcondition of format_float_field might not hold. Assertion Implies((shortest_field_len(value, neg) <= 20), (ToSeq(Result()) == shortest_seq(value, neg))) might not hold.' So the minimality/round-trip clause is load-bearing and independently reconfirms G-DIFF/G-GOLD rather than trusting meta.json.

(4) Strip-the-narration control: I deleted that single fits-branch clause verbatim from the prepatch and re-verified -> STILL 'Verification failed', now on the over-cap take(20) clause. So the spec rejects the pre-patch impl through more than one channel; no clause is decorative narration propping up a vacuous spec.

(5) G-AX re-run: `python3 axiom_check.py` -> 'G-AX OK... over 29 boundary + 200000 fuzz + 4001 integer + 20000 subnormal finite floats'. The axioms the spec is stated over are sound against the real callee.

FACET-BY-FACET, WHY EACH SPEC CLAUSE DOES NOT LEAK:

(a) Minimal-significant-digits + round-trip (the actual discriminator): published verbatim in the problem_statement ('larger than necessary', the 0.009125 -> 0.009124999999999999 expansion, and the explicit str(value) suggestion). Spec says less than the issue.

(b) The 20-character cap and the two trim clauses (take(20) when no E; take(20-(len-idx)) + drop(idx) when E at idx): I checked these against the REAL PRE-PATCH SOURCE rather than trusting refinement.md. Created a worktree at base_commit 0116ac21d136 from the upstream repository and read card.py:1295-1330: the whole block -- `str_len = len(value_str)`, `if str_len > 20`, `idx = value_str.find("E")`, `value_str[:20]`, `value_str[: 20 - (str_len - idx)] + value_str[idx:]` -- is present VERBATIM pre-patch and is byte-for-byte UNCHANGED by patch.diff (the diff only touches the renderer above it). Specifying unchanged surrounding behaviour cannot disclose the edit; it is what keeps the scientific-notation P2P meaningful and blocks the drop-the-exponent attacker.

(c) The NEW sign / negative-zero facet (the `neg` flag, code-point-45 clauses, the two linkage pre-conditions) -- the material the stale prior note never saw, so I measured it directly. I extracted the pre-patch `_format_float` textually from the base-commit worktree and exec'd it against a reconstruction of the post-patch version: pre(0.0)='0.0', post(0.0)='0.0'; pre(-0.0)='-0.0', post(-0.0)='-0.0'; pre(-1.0)=post(-1.0)='-1.0'; pre(-4.6737463674763e+32)=post(...)='-4.6737463674763E+32'. Sign behaviour, INCLUDING sign-of-zero sensitivity, is IDENTICAL pre- and post-patch. A clause whose truth value is the same on both sides of the diff carries zero bits about which side you are on, so the sign facet cannot leak the edit. Its real purpose is well-definedness: under --float-encoding=real an interpreted real identifies +0.0 with -0.0, so the pair (value, neg) is what makes shortest_field a genuine function. The only pre/post divergence in my table is on 0.009125 / -0.009125 -- precisely the case the public issue reproduces.

(d) The two-renderer menu in the axioms (shortest_field vs padded_field, header saying 'the routine selects the former'): not a leak. Preferring minimal digits over a wider preset precision is exactly the public ask, and it is entailed by the spec's own logic anyway -- only shortest_field's Ensures can discharge the fits-branch postcondition, so naming the choice adds no information the postcondition does not already force. The header phrases everything as desired behaviour, never as an edit or a before/after.

**CONCLUSION:** the spec view is a property-level statement of desired rendering behaviour that discloses strictly less about the gold edit than the public problem_statement already does, and the one facet not covered by the issue prose (sign of zero) is provably invariant across the patch. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
