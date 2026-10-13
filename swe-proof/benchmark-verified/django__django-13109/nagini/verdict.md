# P2 adversarial audit — django__django-13109

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1_prepatch_curated.py`, `atk_2_recurse_reject.py`, `atk_3_endless_loop.py`, `atk_4_ignores_choice.py`, `atk_5_offbyone.py`, `atk_7_curated_intersect.py`, `atk_8_curated_union.py`, `atk_9_empty_accepts.py`, `atk_10_choice_only.py`, `atk_12_negated_match.py`, `atk_13_first_only.py`, `atk_14_choice_wrong_arg.py`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6_oracle_echo.py`, `atk_11_curated_fastpath_echo.py`, `atk_19_axiom_double_eval.py`, `atk_20_axiom_per_row.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_curated.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,24 +117,18 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
-    i = len(complete_rows)
+    i = len(curated_rows)
     while i > 0:
         # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(Acc(list_pred(curated_rows), 1 / 2))
+        Invariant(0 <= i and i <= len(curated_rows))
+        Invariant(found == present(value, ToSeq(curated_rows).drop(i)))
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
+        Assert(ToSeq(curated_rows).drop(i - 1)[0] == curated_rows[i - 1])
+        Assert(ToSeq(curated_rows).drop(i - 1).drop(1) == ToSeq(curated_rows).drop(i))
+        if curated_rows[i - 1] == value:
             found = True
         i = i - 1
     if not (found and choice_permitted(value)):
```

Attack 2 — `atk_2_recurse_reject.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,6 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
-        raise ReferenceInvalid()
-    return
+    validate_reference(value, complete_rows, curated_rows)
+    raise ReferenceInvalid()
     # impl-end
```

Attack 3 — `atk_3_endless_loop.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,19 +117,13 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
     i = len(complete_rows)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
         Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
@@ -139,5 +133,11 @@
         i = i - 1
     if not (found and choice_permitted(value)):
         raise ReferenceInvalid()
+    while True:
+        # invariants-start
+        Invariant(Acc(list_pred(complete_rows), 1 / 2))
+        Invariant(Acc(list_pred(curated_rows), 1 / 2))
+        # invariants-end
+        found = found
     return
     # impl-end
```

Attack 4 — `atk_4_ignores_choice.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,19 +117,13 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
     i = len(complete_rows)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
         Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
@@ -137,7 +131,7 @@
         if complete_rows[i - 1] == value:
             found = True
         i = i - 1
-    if not (found and choice_permitted(value)):
+    if not found:
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 5 — `atk_5_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,19 +117,13 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
     i = len(complete_rows)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
         Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
```

Attack 6 — `atk_6_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -117,27 +117,7 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if not reference_holds(value, ToSeq(complete_rows)):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 7 — `atk_7_curated_intersect.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,9 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if not reference_holds(value, ToSeq(complete_rows)):
+        raise ReferenceInvalid()
+    if not present(value, ToSeq(curated_rows)):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 8 — `atk_8_curated_union.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,11 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if not choice_permitted(value):
         raise ReferenceInvalid()
-    return
+    if present(value, ToSeq(complete_rows)):
+        return
+    if present(value, ToSeq(curated_rows)):
+        return
+    raise ReferenceInvalid()
     # impl-end
```

Attack 9 — `atk_9_empty_accepts.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,19 +117,15 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
+    if len(complete_rows) == 0:
+        return
     found = False  # type: bool
     i = len(complete_rows)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
         Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
```

Attack 10 — `atk_10_choice_only.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,7 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if not choice_permitted(value):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 11 — `atk_11_curated_fastpath_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -117,27 +117,11 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if present(value, ToSeq(curated_rows)):
+        if not reference_holds(value, ToSeq(complete_rows)):
+            raise ReferenceInvalid()
+        return
+    if not reference_holds(value, ToSeq(complete_rows)):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 12 — `atk_12_negated_match.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,24 +117,15 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
     i = len(complete_rows)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
+        if complete_rows[i - 1] != value:
             found = True
         i = i - 1
     if not (found and choice_permitted(value)):
```

Attack 13 — `atk_13_first_only.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,9 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if len(complete_rows) == 0:
         raise ReferenceInvalid()
-    return
+    if complete_rows[0] == value and choice_permitted(value):
+        return
+    raise ReferenceInvalid()
     # impl-end
```

Attack 14 — `atk_14_choice_wrong_arg.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,24 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
+    ok = False  # type: bool
     i = len(complete_rows)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
         Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
         Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
         if complete_rows[i - 1] == value:
             found = True
+        if choice_permitted(complete_rows[i - 1]):
+            ok = True
         i = i - 1
-    if not (found and choice_permitted(value)):
+    if not (found and ok):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 15 — `atk_15_subdomain_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,11 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if len(curated_rows) == 0:
+        if not reference_holds(value, ToSeq(complete_rows)):
+            raise ReferenceInvalid()
+        return
+    if not (present(value, ToSeq(curated_rows)) and choice_permitted(value)):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 16 — `atk_16_holds_over_curated.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,7 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if not reference_holds(value, ToSeq(curated_rows)):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 17 — `atk_17_inverted.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,7 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
+    if reference_holds(value, ToSeq(complete_rows)):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 18 — `atk_18_always_accept.py` → rejected (same spec, does not verify — good)

```diff
@@ -117,27 +117,5 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
-    found = False  # type: bool
-    i = len(complete_rows)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(complete_rows), 1 / 2))
-        Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
-        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
-        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
-        if complete_rows[i - 1] == value:
-            found = True
-        i = i - 1
-    if not (found and choice_permitted(value)):
-        raise ReferenceInvalid()
     return
     # impl-end
```

Attack 19 — `atk_19_axiom_double_eval.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -117,19 +117,13 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
     i = len(complete_rows)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
         Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
@@ -137,7 +131,9 @@
         if complete_rows[i - 1] == value:
             found = True
         i = i - 1
-    if not (found and choice_permitted(value)):
+    first = choice_permitted(value)  # type: bool
+    second = choice_permitted(value)  # type: bool
+    if not (found and first and second):
         raise ReferenceInvalid()
     return
     # impl-end
```

Attack 20 — `atk_20_axiom_per_row.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -117,25 +117,22 @@
             and (not reference_holds(value, ToSeq(complete_rows))))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
     found = False  # type: bool
+    anyperm = False  # type: bool
     i = len(complete_rows)
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(complete_rows), 1 / 2))
         Invariant(0 <= i and i <= len(complete_rows))
-        # `found` tracks membership over the suffix already scanned.
         Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i + 1, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
         Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
         if complete_rows[i - 1] == value:
             found = True
+        if choice_permitted(complete_rows[i - 1]):
+            anyperm = True
         i = i - 1
     if not (found and choice_permitted(value)):
         raise ReferenceInvalid()
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13109.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field that points at rows of another model validates a candidate
  reference value by asking whether some row of that other model actually
  carries the referenced key. The other model exposes two row collections:

    * the COMPLETE collection of every stored row (its unfiltered set), and
    * a curated, possibly-narrower collection that ordinary application code
      sees by default, which may hide some genuinely-stored rows behind an
      extra standing filter (for example rows flagged as retired).

  The behaviour pinned here is which collection the reference check must
  consult. The check exists to confirm the referenced row is genuinely STORED,
  so that a later write cannot dangle. It must therefore consult the COMPLETE
  collection: a reference to a row that is stored — even one the curated default
  collection hides — is a valid reference and must pass. The curated narrowing
  is a presentation concern, not an integrity concern, so it must not influence
  whether a reference to a stored row is accepted.

  Concretely: the check succeeds (returns normally) exactly when the COMPLETE
  collection contains the referenced key AND that key satisfies the additional
  per-field choice restriction that the check always applies; otherwise it
  rejects the reference by raising. The curated default collection does NOT
  enter this decision.

Row keys are modelled as integers; a collection of rows is a `List[int]` of the
keys present. The additional per-field choice restriction (an unchanged callee
the check always applies) is axiomatised as a pure predicate on the key. The
rejection is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

The check must ANSWER (return or raise): Nagini verifies partial correctness by
default, so without an explicit obligation a non-terminating implementation
(bare self-recursion, or an endless loop) satisfies every `Ensures`/`Exsures`
vacuously while never delivering a decision. The real check is one bounded
lookup that always completes; the obligation is carried as `MustTerminate` in
the precondition (measure 2 — the impl may call the pure helpers but may NOT
re-invoke itself) and consumed by the scan loop with the strictly decreasing,
bounded-below measure `i + 1`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class ReferenceInvalid(Exception):
    """Signals a rejected reference (no genuinely-stored, choice-permitted row
    carries the referenced key). Stands in for the `ValidationError` the desired
    behaviour raises; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2)."""

# axioms-start
@Pure
@ContractOnly
def choice_permitted(key: int) -> bool:
    """The additional per-field choice restriction the reference check always
    applies, independent of which row collection is consulted (the unchanged
    `complex_filter(get_limit_choices_to())` narrowing). A deterministic
    predicate of the key alone. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Ensures(True)
# axioms-end

# pure-start
@Pure
def present(key: int, rows: PSeq[int]) -> bool:
    """Whether some row in `rows` carries `key`. Front-recursive over the
    sequence so a single membership unfold is available per loop step."""
    if len(rows) == 0:
        return False
    return rows[0] == key or present(key, rows.drop(1))

@Pure
def reference_holds(key: int, complete_rows: PSeq[int]) -> bool:
    """The reference is valid exactly when the COMPLETE collection holds a row
    carrying `key` AND that key satisfies the choice restriction."""
    return present(key, complete_rows) and choice_permitted(key)
# pure-end

def validate_reference(value: int,
                       complete_rows: List[int],
                       curated_rows: List[int]) -> None:
    # pre-conditions-start
    # Both collections are read-only here (the check never mutates either);
    # fractional permission, required and ensured, so no caller can satisfy a
    # postcondition vacuously by overwriting an input.
    Requires(Acc(list_pred(complete_rows), 1 / 2))
    Requires(Acc(list_pred(curated_rows), 1 / 2))
    # Total-correctness obligation: the check must ANSWER (return normally or
    # raise). The real operation is one bounded queryset probe that always
    # completes; without this a diverging impl (bare self-recursion, endless
    # loop) satisfies the Ensures/Exsures vacuously. Measure 2: the impl may
    # invoke the pure helpers but may NOT re-invoke this routine itself.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(complete_rows), 1 / 2))
    Ensures(Acc(list_pred(curated_rows), 1 / 2))
    # Returns normally exactly when the COMPLETE collection holds the referenced
    # key and that key is choice-permitted. The curated collection is absent
    # from this condition: a reference to a stored row the curated view hides
    # still passes.
    Ensures(reference_holds(value, ToSeq(complete_rows)))
    # Rejects (raises) exactly when no genuinely-stored, choice-permitted row
    # carries the key — again decided over the COMPLETE collection only.
    Exsures(ReferenceInvalid,
            Acc(list_pred(complete_rows), 1 / 2)
            and Acc(list_pred(curated_rows), 1 / 2)
            and (not reference_holds(value, ToSeq(complete_rows))))
    # post-conditions-end
    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        # `found` tracks membership over the suffix already scanned.
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 1, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-13109/nagini. 20 same-spec wrong-impl attacks built  by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical). All 20 + the positive control return exit 0 from `python -m swebench_unified.adversary same-spec nagini django__django-13109 <f>`.

**Command for every attack:** `python -m swebench_unified.adversary weakness nagini django__django-13109 atk_N.py` (raw output kept at out_<name>.txt with the exit code appended).

REJECTED (exit 2, NOT-A-COUNTEREXAMPLE, spec did its job) -- 16:
 atk_1_prepatch_curated (THE PREPATCH BUG re-encoded: scan curated_rows) -- rejected on exactly the discriminating leg: `atk_1:115:13:117:67 error: Postcondition... Assertion (not reference_holds(value, ToSeq(complete_rows))) might not hold` (the Exsures). prepatch_reproduced=true.
 atk_2_recurse_reject (the counterexample refinement.md A7 NAMES, atk_recurse_reject: bare self-call then raise) -- rejected; MustTerminate(2) forbids the self-invocation, so the vacuous-Exsures route is closed.
 atk_3_endless_loop (control-flow-effect: decide correctly, then `while True` instead of answering) -- rejected; the method-level MustTerminate(2) is not discharged by an unmeasured loop.
 atk_4_ignores_choice (drops the A-consumed conjunct) -- rejected on `Ensures reference_holds(...)`, so the unchanged limit_choices_to narrowing is genuinely pinned, not decoration.
 atk_5_offbyone (boundary: `while i > 1`, never inspects complete_rows[0]) -- rejected.
 atk_7_curated_intersect (too strict via a second route: complete AND curated) -- rejected.
 atk_8_curated_union (too lax: accept if EITHER collection holds the key; behaviourally equal in the real repo where curated subset complete, but the model assumes no subset relation, so the spec must and does reject it) -- rejected.
 atk_9_empty_accepts (boundary fast path: empty complete collection => accept) -- rejected.
 atk_10_choice_only (ignores membership entirely; decides on the axiom alone) -- rejected.
 atk_12_negated_match (membership complemented) -- rejected.
 atk_13_first_only (partial domain: only complete_rows[0] inspected) -- rejected.
 atk_14_choice_wrong_arg (A-CONSUMED LEG: applies the narrowing to each stored row's key instead of to `value`) -- rejected, so the axiom's ARGUMENT is pinned to the key, matching mapping.md 3.1.
 atk_15_subdomain_prepatch (the sneaky one: gold behaviour when curated_rows is empty, prepatch bug otherwise -- wrong only on the inputs the two F2P tests exercise) -- rejected.
 atk_16_holds_over_curated (A-REFERENCE LEG: the prepatch bug expressed through the spec's own reference_holds over ToSeq(curated_rows)) -- rejected, so the collection choice is pinned at the predicate level, not just in the hand-rolled scan.
 atk_17_inverted, atk_18_always_accept -- rejected.

CANDIDATES (exit 0: share the spec AND verify) -- 4, and for EVERY one the faithful refined patch was materialized and EXECUTED through the official harness via swebench_unified.harness.run_resolve (raw ResolveResult JSON in res<N>.log / resolve_*.json): atk_6_oracle_echo (decide straight off reference_holds) -> patch_atk_6_oracle_echo.diff is byte-equivalent to the gold single-token `_default_manager`->`_base_manager` edit. run_resolve: completed=True resolved=True attempts=1 flaky=False; both F2P pass, 170/170 P2P pass, 0 failures.

CORRECT ECHO, not a weakness. atk_11_curated_fastpath_echo (branch on curated membership but decide over complete_rows in BOTH branches) -> faithful patch adds a real extra `_default_manager`.exists() probe then decides on the base-manager queryset. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P 2/2, P2P 170/170, no PASS_TO_FAIL. Echo. atk_19_axiom_double_eval (A-CONSUMED LEG PRESSURE: the axiom is @Pure, so Nagini cannot see the real callee's INVOCATION COUNT; evaluate choice_permitted(value) twice and conjoin) -> faithful patch invokes get_limit_choices_to()/complex_filter()/exists() TWICE.

This is the sharpest A-leg attack available: model_forms.tests.LimitChoicesToTests.test_callable_called_each_time_form_is_instantiated (in PASS_TO_PASS) does mock call_count assertions on limit_choices_to. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P 2/2, P2P 170/170, 0 failures -- that test counts calls on the FORM-FIELD construction path, not on ForeignObject.validate, so the double evaluation is unobserved.

Echo, not a break. atk_20_axiom_per_row (A-CONSUMED LEG: apply the narrowing across EVERY row of the unfiltered collection, i.e. an extra full base-manager table probe, then decide) -> faithful patch adds an unfiltered complex_filter(...).exists() over the whole base-manager queryset. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P 2/2, P2P 170/170, no query-count regression (test_model_multiple_choice_number_of_queries and test_show_hidden_initial_changed_queries_efficiently both pass -- they instrument the ModelMultipleChoiceField path, not validate()). Echo.

No candidate's patch failed to resolve => no verify-implies-not-correct witness found. Positive control: pos_control.py (byte-identical model.py) `python -m swebench_unified.adversary verify nagini django__django-13109.../pos_control.py` -> VERIFIED in 23.0s, exit 0.

REFINEMENT.MD LEG AUDIT (A legs; R/I legs are G-CONF's, 104350 checks / 0 disagreements). Tags tally exactly 4 R + 2 R+I + 1 A-consumed = 7 legs, zero kind-3, matching section C. A-legs checked against the real callees at base_commit fbe82f8:
 * A5 / A-consumed, choice_permitted <-> qs.complex_filter(self.get_limit_choices_to()) at related.py:920 (get_limit_choices_to defined at related.py:390): CONFIRMED unchanged by the patch -- the gold diff hunk is `@@ -914,7 +914,7 @@`, a single line touching only related.py:917, and complex_filter appears in the diff solely as trailing context. So the claim 'same callee pre- and post-patch, does not discriminate the bug' holds by inspection of the diff, not merely by assertion. The axiom's Ensures(True) is the weakest possible form, so it cannot over-constrain; and atk_4/atk_10/atk_14 show the proof genuinely CONSUMES it as the second conjunct of reference_holds applied to `value` (dropping it, using it alone, or feeding it the wrong argument all fail verification). Correspondence holds.
 * A2/A4 + meta.json deep_model_references / A-reference, the complete-vs-curated collection choice <-> Model.`_base_manager` (base.py:377 -> options.py:382, an auto-created plain Manager() with no get_queryset override => every stored row) vs Model.`_default_manager` (base.py:381 -> options.py:410, the first declared manager, which the test fixtures give a get_queryset filtering archived=False -- confirmed in the instance test_patch's WriterManager and AuthorManager). Read both at base_commit: the subset relationship rows(`_default_manager`) subset rows(`_base_manager`) and the archived witness (present in base, hidden by default) are realizable exactly as mapping.md 3.2 claims. This IS the changed operation and it is modeled DEEPLY (membership over complete_rows vs curated_rows), not hidden behind an axiom about the function under change -- so there is no kind-3 leg, and atk_1/atk_15/atk_16 confirm the spec discriminates it through three independent encodings.
 * A6's ValidationError <-> ReferenceInvalid R-leg: verified that the F2P tests observe only the raise/no-raise outcome -- validation.tests uses assertIsNone(full_clean()) / assertFailsValidation (which compares only message_dict KEYS), and model_forms uses assertIs(form.is_valid(),...). The message text is unobserved, so collapsing the exception type is sound.
 * A7's MustTerminate legs are load-bearing rather than ornamental: atk_2 (the named self-recursion counterexample) and atk_3 (endless loop after a correct decision) are both rejected, which is the property loop invariants alone would not give.

ONE ADVISORY OBSERVATION, not a G-EQ defect: meta.json records G-AX status=pass but its detail is a SELF-SKIP -- "G-AX SKIP: Django not configurable in this environment: ModuleNotFoundError(\"No module named 'axcheck'\")" with exit 0. axiom_check.py returns 0 from its own except branch when settings.configure() fails, so the executable soundness check for BOTH A-legs never actually ran in the recorded stamp; the pass is a skip wearing a pass. I therefore established the A-leg correspondence by direct source reading at base_commit (above) rather than relying on that stamp. This is a G-AX evidence-quality issue for the axiom-soundness trust point, outside this role's remit, and it does not change the G-EQ verdict: the four verifying candidates all resolve under the real harness.

**Verdict:** SOUND -- 20 admissible same-spec attacks run (16 rejected by the spec, 4 candidates), every candidate's faithful refined patch EXECUTED through run_resolve and every one resolved (2/2 F2P, 170/170 P2P, zero PASS_TO_FAIL in all four), positive control verifies. No verify-does-not-imply-correct witness exists for this spec on the attacks tried, including the two aimed squarely at the @Pure axiom's blindness to real-callee invocation counts and table scans.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk_1_prepatch_curated.py`, `atk_2_recurse_reject.py`, `atk_3_endless_loop.py`, `atk_4_ignores_choice.py`, `atk_5_offbyone.py`, `atk_7_curated_intersect.py`, `atk_8_curated_union.py`, `atk_9_empty_accepts.py`, `atk_10_choice_only.py`, `atk_12_negated_match.py`, `atk_13_first_only.py`, `atk_14_choice_wrong_arg.py`, +4 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6_oracle_echo.py`, `atk_11_curated_fastpath_echo.py`, `atk_19_axiom_double_eval.py`, `atk_20_axiom_per_row.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_curated.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_recurse_reject.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_endless_loop.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_ignores_choice.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_offbyone.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_curated_intersect.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_curated_union.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_empty_accepts.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_choice_only.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_curated_fastpath_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_negated_match.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_first_only.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_choice_wrong_arg.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_subdomain_prepatch.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_holds_over_curated.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_inverted.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18_always_accept.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19_axiom_double_eval.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 20 — `atk_20_axiom_per_row.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13109.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field that points at rows of another model validates a candidate
  reference value by asking whether some row of that other model actually
  carries the referenced key. The other model exposes two row collections:

    * the COMPLETE collection of every stored row (its unfiltered set), and
    * a curated, possibly-narrower collection that ordinary application code
      sees by default, which may hide some genuinely-stored rows behind an
      extra standing filter (for example rows flagged as retired).

  The behaviour pinned here is which collection the reference check must
  consult. The check exists to confirm the referenced row is genuinely STORED,
  so that a later write cannot dangle. It must therefore consult the COMPLETE
  collection: a reference to a row that is stored — even one the curated default
  collection hides — is a valid reference and must pass. The curated narrowing
  is a presentation concern, not an integrity concern, so it must not influence
  whether a reference to a stored row is accepted.

  Concretely: the check succeeds (returns normally) exactly when the COMPLETE
  collection contains the referenced key AND that key satisfies the additional
  per-field choice restriction that the check always applies; otherwise it
  rejects the reference by raising. The curated default collection does NOT
  enter this decision.

Row keys are modelled as integers; a collection of rows is a `List[int]` of the
keys present. The additional per-field choice restriction (an unchanged callee
the check always applies) is axiomatised as a pure predicate on the key. The
rejection is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

The check must ANSWER (return or raise): Nagini verifies partial correctness by
default, so without an explicit obligation a non-terminating implementation
(bare self-recursion, or an endless loop) satisfies every `Ensures`/`Exsures`
vacuously while never delivering a decision. The real check is one bounded
lookup that always completes; the obligation is carried as `MustTerminate` in
the precondition (measure 2 — the impl may call the pure helpers but may NOT
re-invoke itself) and consumed by the scan loop with the strictly decreasing,
bounded-below measure `i + 1`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class ReferenceInvalid(Exception):
    """Signals a rejected reference (no genuinely-stored, choice-permitted row
    carries the referenced key). Stands in for the `ValidationError` the desired
    behaviour raises; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2)."""

# axioms-start
@Pure
@ContractOnly
def choice_permitted(key: int) -> bool:
    """The additional per-field choice restriction the reference check always
    applies, independent of which row collection is consulted (the unchanged
    `complex_filter(get_limit_choices_to())` narrowing). A deterministic
    predicate of the key alone. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Ensures(True)
# axioms-end

# pure-start
@Pure
def present(key: int, rows: PSeq[int]) -> bool:
    """Whether some row in `rows` carries `key`. Front-recursive over the
    sequence so a single membership unfold is available per loop step."""
    if len(rows) == 0:
        return False
    return rows[0] == key or present(key, rows.drop(1))

@Pure
def reference_holds(key: int, complete_rows: PSeq[int]) -> bool:
    """The reference is valid exactly when the COMPLETE collection holds a row
    carrying `key` AND that key satisfies the choice restriction."""
    return present(key, complete_rows) and choice_permitted(key)
# pure-end

def validate_reference(value: int,
                       complete_rows: List[int],
                       curated_rows: List[int]) -> None:
    # pre-conditions-start
    # Both collections are read-only here (the check never mutates either);
    # fractional permission, required and ensured, so no caller can satisfy a
    # postcondition vacuously by overwriting an input.
    Requires(Acc(list_pred(complete_rows), 1 / 2))
    Requires(Acc(list_pred(curated_rows), 1 / 2))
    # Total-correctness obligation: the check must ANSWER (return normally or
    # raise). The real operation is one bounded queryset probe that always
    # completes; without this a diverging impl (bare self-recursion, endless
    # loop) satisfies the Ensures/Exsures vacuously. Measure 2: the impl may
    # invoke the pure helpers but may NOT re-invoke this routine itself.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(complete_rows), 1 / 2))
    Ensures(Acc(list_pred(curated_rows), 1 / 2))
    # Returns normally exactly when the COMPLETE collection holds the referenced
    # key and that key is choice-permitted. The curated collection is absent
    # from this condition: a reference to a stored row the curated view hides
    # still passes.
    Ensures(reference_holds(value, ToSeq(complete_rows)))
    # Rejects (raises) exactly when no genuinely-stored, choice-permitted row
    # carries the key — again decided over the COMPLETE collection only.
    Exsures(ReferenceInvalid,
            Acc(list_pred(complete_rows), 1 / 2)
            and Acc(list_pred(curated_rows), 1 / 2)
            and (not reference_holds(value, ToSeq(complete_rows))))
    # post-conditions-end
    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(complete_rows), 1 / 2))
        Invariant(0 <= i and i <= len(complete_rows))
        # `found` tracks membership over the suffix already scanned.
        Invariant(found == present(value, ToSeq(complete_rows).drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 1, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(complete_rows).drop(i - 1)[0] == complete_rows[i - 1])
        Assert(ToSeq(complete_rows).drop(i - 1).drop(1) == ToSeq(complete_rows).drop(i))
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-13109/nagini. 20 same-spec wrong-impl attacks built  by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical). All 20 + the positive control return exit 0 from `python -m swebench_unified.adversary same-spec nagini django__django-13109 <f>`.

**Command for every attack:** `python -m swebench_unified.adversary weakness nagini django__django-13109 atk_N.py` (raw output kept at out_<name>.txt with the exit code appended).

REJECTED (exit 2, NOT-A-COUNTEREXAMPLE, spec did its job) -- 16:
 atk_1_prepatch_curated (THE PREPATCH BUG re-encoded: scan curated_rows) -- rejected on exactly the discriminating leg: `atk_1:115:13:117:67 error: Postcondition... Assertion (not reference_holds(value, ToSeq(complete_rows))) might not hold` (the Exsures). prepatch_reproduced=true.
 atk_2_recurse_reject (the counterexample refinement.md A7 NAMES, atk_recurse_reject: bare self-call then raise) -- rejected; MustTerminate(2) forbids the self-invocation, so the vacuous-Exsures route is closed.
 atk_3_endless_loop (control-flow-effect: decide correctly, then `while True` instead of answering) -- rejected; the method-level MustTerminate(2) is not discharged by an unmeasured loop.
 atk_4_ignores_choice (drops the A-consumed conjunct) -- rejected on `Ensures reference_holds(...)`, so the unchanged limit_choices_to narrowing is genuinely pinned, not decoration.
 atk_5_offbyone (boundary: `while i > 1`, never inspects complete_rows[0]) -- rejected.
 atk_7_curated_intersect (too strict via a second route: complete AND curated) -- rejected.
 atk_8_curated_union (too lax: accept if EITHER collection holds the key; behaviourally equal in the real repo where curated subset complete, but the model assumes no subset relation, so the spec must and does reject it) -- rejected.
 atk_9_empty_accepts (boundary fast path: empty complete collection => accept) -- rejected.
 atk_10_choice_only (ignores membership entirely; decides on the axiom alone) -- rejected.
 atk_12_negated_match (membership complemented) -- rejected.
 atk_13_first_only (partial domain: only complete_rows[0] inspected) -- rejected.
 atk_14_choice_wrong_arg (A-CONSUMED LEG: applies the narrowing to each stored row's key instead of to `value`) -- rejected, so the axiom's ARGUMENT is pinned to the key, matching mapping.md 3.1.
 atk_15_subdomain_prepatch (the sneaky one: gold behaviour when curated_rows is empty, prepatch bug otherwise -- wrong only on the inputs the two F2P tests exercise) -- rejected.
 atk_16_holds_over_curated (A-REFERENCE LEG: the prepatch bug expressed through the spec's own reference_holds over ToSeq(curated_rows)) -- rejected, so the collection choice is pinned at the predicate level, not just in the hand-rolled scan.
 atk_17_inverted, atk_18_always_accept -- rejected.

CANDIDATES (exit 0: share the spec AND verify) -- 4, and for EVERY one the faithful refined patch was materialized and EXECUTED through the official harness via swebench_unified.harness.run_resolve (raw ResolveResult JSON in res<N>.log / resolve_*.json): atk_6_oracle_echo (decide straight off reference_holds) -> patch_atk_6_oracle_echo.diff is byte-equivalent to the gold single-token `_default_manager`->`_base_manager` edit. run_resolve: completed=True resolved=True attempts=1 flaky=False; both F2P pass, 170/170 P2P pass, 0 failures.

CORRECT ECHO, not a weakness. atk_11_curated_fastpath_echo (branch on curated membership but decide over complete_rows in BOTH branches) -> faithful patch adds a real extra `_default_manager`.exists() probe then decides on the base-manager queryset. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P 2/2, P2P 170/170, no PASS_TO_FAIL. Echo. atk_19_axiom_double_eval (A-CONSUMED LEG PRESSURE: the axiom is @Pure, so Nagini cannot see the real callee's INVOCATION COUNT; evaluate choice_permitted(value) twice and conjoin) -> faithful patch invokes get_limit_choices_to()/complex_filter()/exists() TWICE.

This is the sharpest A-leg attack available: model_forms.tests.LimitChoicesToTests.test_callable_called_each_time_form_is_instantiated (in PASS_TO_PASS) does mock call_count assertions on limit_choices_to. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P 2/2, P2P 170/170, 0 failures -- that test counts calls on the FORM-FIELD construction path, not on ForeignObject.validate, so the double evaluation is unobserved.

Echo, not a break. atk_20_axiom_per_row (A-CONSUMED LEG: apply the narrowing across EVERY row of the unfiltered collection, i.e. an extra full base-manager table probe, then decide) -> faithful patch adds an unfiltered complex_filter(...).exists() over the whole base-manager queryset. run_resolve: completed=True resolved=True attempts=1 flaky=False; F2P 2/2, P2P 170/170, no query-count regression (test_model_multiple_choice_number_of_queries and test_show_hidden_initial_changed_queries_efficiently both pass -- they instrument the ModelMultipleChoiceField path, not validate()). Echo.

No candidate's patch failed to resolve => no verify-implies-not-correct witness found. Positive control: pos_control.py (byte-identical model.py) `python -m swebench_unified.adversary verify nagini django__django-13109.../pos_control.py` -> VERIFIED in 23.0s, exit 0.

REFINEMENT.MD LEG AUDIT (A legs; R/I legs are G-CONF's, 104350 checks / 0 disagreements). Tags tally exactly 4 R + 2 R+I + 1 A-consumed = 7 legs, zero kind-3, matching section C. A-legs checked against the real callees at base_commit fbe82f8:
 * A5 / A-consumed, choice_permitted <-> qs.complex_filter(self.get_limit_choices_to()) at related.py:920 (get_limit_choices_to defined at related.py:390): CONFIRMED unchanged by the patch -- the gold diff hunk is `@@ -914,7 +914,7 @@`, a single line touching only related.py:917, and complex_filter appears in the diff solely as trailing context. So the claim 'same callee pre- and post-patch, does not discriminate the bug' holds by inspection of the diff, not merely by assertion. The axiom's Ensures(True) is the weakest possible form, so it cannot over-constrain; and atk_4/atk_10/atk_14 show the proof genuinely CONSUMES it as the second conjunct of reference_holds applied to `value` (dropping it, using it alone, or feeding it the wrong argument all fail verification). Correspondence holds.
 * A2/A4 + meta.json deep_model_references / A-reference, the complete-vs-curated collection choice <-> Model.`_base_manager` (base.py:377 -> options.py:382, an auto-created plain Manager() with no get_queryset override => every stored row) vs Model.`_default_manager` (base.py:381 -> options.py:410, the first declared manager, which the test fixtures give a get_queryset filtering archived=False -- confirmed in the instance test_patch's WriterManager and AuthorManager). Read both at base_commit: the subset relationship rows(`_default_manager`) subset rows(`_base_manager`) and the archived witness (present in base, hidden by default) are realizable exactly as mapping.md 3.2 claims. This IS the changed operation and it is modeled DEEPLY (membership over complete_rows vs curated_rows), not hidden behind an axiom about the function under change -- so there is no kind-3 leg, and atk_1/atk_15/atk_16 confirm the spec discriminates it through three independent encodings.
 * A6's ValidationError <-> ReferenceInvalid R-leg: verified that the F2P tests observe only the raise/no-raise outcome -- validation.tests uses assertIsNone(full_clean()) / assertFailsValidation (which compares only message_dict KEYS), and model_forms uses assertIs(form.is_valid(),...). The message text is unobserved, so collapsing the exception type is sound.
 * A7's MustTerminate legs are load-bearing rather than ornamental: atk_2 (the named self-recursion counterexample) and atk_3 (endless loop after a correct decision) are both rejected, which is the property loop invariants alone would not give.

ONE ADVISORY OBSERVATION, not a G-EQ defect: meta.json records G-AX status=pass but its detail is a SELF-SKIP -- "G-AX SKIP: Django not configurable in this environment: ModuleNotFoundError(\"No module named 'axcheck'\")" with exit 0. axiom_check.py returns 0 from its own except branch when settings.configure() fails, so the executable soundness check for BOTH A-legs never actually ran in the recorded stamp; the pass is a skip wearing a pass. I therefore established the A-leg correspondence by direct source reading at base_commit (above) rather than relying on that stamp. This is a G-AX evidence-quality issue for the axiom-soundness trust point, outside this role's remit, and it does not change the G-EQ verdict: the four verifying candidates all resolve under the real harness.

**Verdict:** SOUND -- 20 admissible same-spec attacks run (16 rejected by the spec, 4 candidates), every candidate's faithful refined patch EXECUTED through run_resolve and every one resolved (2/2 F2P, 170/170 P2P, zero PASS_TO_FAIL in all four), positive control verifies. No verify-does-not-imply-correct witness exists for this spec on the attacks tried, including the two aimed squarely at the @Pure axiom's blindness to real-callee invocation counts and table scans.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE SETUP (per instructions): git worktree at base_commit fbe82f82555bc25dccb476c749ca062f0b522be3 under /tmp () with the gold patch.diff APPLIED. Confirmed post-patch source by inspect.getsource(ForeignKey.validate): contains '`_base_manager`', does NOT contain '`_default_manager`'.

1. **SPEC REGION BYTE-IDENTICAL.** `adversary same-spec nagini django__django-13109` on a verbatim copy of model.py => exit 0 ('SAME'). Independently recomputed swebench_unified.markers.region_hashes with the nagini backend: all 7 regions match meta.json exactly, including spec_view 7fdd19cb68c81b4127766d4fe3048203f9816c15a8d9549d12b68b9290a83a11.

2. **MODEL VERIFIES.** Pinned scripts/nagini_verify.sh on model.py => 'Verification successful', 18.11s.

3. G-DIFF CONTROL (spec senses the change, so it is not vacuous/too weak in the direction that would mask drift). model_prepatch.py shares the exact spec (same-spec exit 0) and FAILS with precisely: 'Postcondition of validate_reference might not hold. Assertion (not reference_holds(value, ToSeq(complete_rows))) might not hold.' That is the Exsures clause, the correct discriminating clause.

4. PRIMARY FAITHFULNESS EVIDENCE — independent differential probe (hostile.py) driving the REAL patched validate vs the contract-stripped model impl, under mapping.md's bridge (complete_rows:=`_base_manager` keys, curated_rows:=`_default_manager` keys, choice_permitted(k):=rows carrying k survive complex_filter(get_limit_choices_to()), vacuously true when no row carries k). 14,556 inputs, 0 disagreements, across 52 populations x 4 reference fields. I deliberately went BEYOND the bundle's own conformance_check.py fixtures with cases designed to break the abstraction:
   - NON-UNIQUE to_field ('code' IntegerField, db_constraint=False) with DUPLICATE keys where only SOME duplicates survive the restriction, e.g. [(5,archived=F,flag=F),(5,archived=T,flag=T)] and [(7,F,T),(7,F,F),(7,T,T)].
   - CALLABLE limit_choices_to (exercises get_limit_choices_to()'s callable branch at related.py:390).
   - Q-OBJECT restriction: Q(flag=True) | Q(archived=True).
   - dict restriction {'flag': True} and the empty restriction.
   This matters because the recorded prior G-PANEL-2 review justified choice_permitted's per-key soundness with 'the FK target field is unique (value names at most one row)'. I broke that premise and the model still did not diverge — because the real callee's.filter(k).complex_filter(lct).exists() is EXISTENTIAL over the rows carrying k, hence still a deterministic function of k for a fixed DB state, which is exactly what the axiom's Ensures(True) (weakest possible, no value claim) permits. So the axiom is not over-strong even without uniqueness; its soundness does not actually depend on that premise.

5. SPEC-TOO-STRONG CHECKED IN EVERY OTHER DIRECTION:
   - Ensures/Exsures form a total, mutually exclusive pair (return iff reference_holds, raise iff not), so the spec claims no more than the raise/no-raise observable, which is exactly what the F2P tests assert (is_valid()/full_clean() outcome, not the message payload). No message/params claim is made — correctly, since the real raise carries model/pk/field/value.
   - MustTerminate(2) + loop measure i+1: the real reference check is one bounded.filter(...).exists() probe that always answers, so the obligation adds nothing the real callee lacks. Measure 2 permits calling the @Pure helpers and forbids self-reinvocation — no legitimate implementation is excluded.
   - Acc(list_pred(...), 1/2) required AND ensured on BOTH lists: read-only, matching a queryset probe that mutates nothing; the fractional permission also blocks vacuous postcondition satisfaction by input overwrite.
   - curated_rows appears in the signature but is deliberately ABSENT from the postcondition. That is the correct post-patch behavior (the fixed check ignores the default manager) and is precisely what makes G-DIFF bite; it is not an over-claim.
   - value: int keeps None outside the modeled domain; the upstream guards (parent_link, value is None, super().validate at related.py:910-916) and the `using` alias are disclosed out-of-scope in mapping.md §2, and I confirmed multi-db routing does not alter the decision.

6. **F2P GROUNDING.** test_validate_foreign_key_to_model_with_overridden_manager expects an archived Writer (hidden by the default manager, present in the base manager) to VALIDATE — matching Ensures(reference_holds(value, complete_rows)). The sibling test_validate_foreign_key_uses_default_manager asserting is_valid() False is the ModelChoiceField queryset layer, not FK.validate, so it does not conflict with the modeled behavior.

**CONCLUSION:** the modeled function agrees with the real patched callee on every input under the disclosed binding; the abstraction (queryset -> List[int] of keys, ValidationError -> ReferenceInvalid) is exact for the pinned observable, and the one consumed axiom is the weakest form and survives even the non-unique-key stress I added. FAITHFUL.

Counterexample / evidence:

```
None. No same-spec counterexample and no diverging input; the spec is neither too strong nor drifted.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction audit for django__django-13109 (nagini). No relaxation present: meta.json has NO `relaxed_leakage` key (checked programmatically) and there is no RELAXED_LEAKAGE.md in the bundle, so this is judged as an ordinary strict-leakage review, not an inherited disposition.

### WHAT I MEASURED (my own runs, not the bundle's assertions):
1. Spec view identity. Recomputed with swebench_unified.markers.spec_view/region_hashes using the nagini backend: spec_view hash = 7fdd19cb68c81b4127766d4fe3048203f9816c15a8d9549d12b68b9290a83a11, byte-identical to meta.json region_hashes.spec_view (and all six region hashes match). `python -m swebench_unified.adversary same-spec nagini django__django-13109` on a verbatim copy of model.py returns exit 0 ("SAME"), so the spec region I read is the frozen one.
2. Core gates the disposition leans on, re-run by me, not read off meta.json: `bash scripts/nagini_verify.sh model.py` -> "Verification successful", 13.33s, exit 0 (G-VERIFY/G-GOLD). `nagini_verify.sh model_prepatch.py` -> exit 1, failing exactly `Postcondition... Assertion (not reference_holds(value, ToSeq(complete_rows))) might not hold` at model_prepatch.py:115 (G-DIFF sound; the prepatch differs only in the impl region, scanning curated_rows). G-LEAK re-run live via swebench_unified.leakage.screen(model.py, nagini, instance.patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]) -- a fresh measurement, not the stored 'pass'.
3. Ground truth for the edit. Checked out base_commit fbe82f82555bc25dccb476c749ca062f0b522be3  (worktree, no bundle writes) and read django/db/models/fields/related.py:909-929: line 917 is `_default_manager` pre-patch; patch.diff changes exactly that one token to `_base_manager` and touches nothing else (line 920 `complex_filter(self.get_limit_choices_to())` is unchanged).

PROBLEM_STATEMENT vs SPEC VIEW (public disclosure is unusually complete here). The public problem_statement -- not hints_text -- is titled 'ForeignKey.validate() should validate using the base manager', walks the ArticleManager/get_queryset(archived=False) example contrasting the default manager's filtering with `Article._base_manager.all()`, links the exact code at `django/db/models/fields/related.py#L917-L919`, and closes with 'Suggested solution: the ForeignKey validation should use the `_base_manager` instead which does not include the default filters.' So file, line range, both manager symbols, and the fix direction are all already public.

Line-by-line token scan of the spec view: `_base_manager`, `_default_manager`, `base_manager`, `default_manager`, `related.py`, `917`, `archived`, `router`, `db_for_read`, `remote_field`, `ForeignKey`, `ForeignObject`, `QuerySet`, `exists()`, `django/db` -> ZERO occurrences. The spec deliberately abstracts the decision as 'which collection the reference check must consult': a COMPLETE collection of every stored row vs 'a curated, possibly-narrower collection... behind an extra standing filter', pinned by Ensures(reference_holds(value, ToSeq(complete_rows))) and the mirrored Exsures. Every gold-edit-relevant fact there is a strict weakening of public content -- it says less than the problem_statement, which names the symbols outright.

THE ONE NON-PUBLIC ELEMENT, and my load-bearing test on it. `choice_permitted` / `complex_filter(get_limit_choices_to())` (spec view line 63) is the only spec element absent from problem_statement. It names an unchanged repo callee, so the question is whether it carries discriminating power. I measured rather than assumed: I built diag_nochoice_prepatch.py -- the prepatch impl with choice_permitted removed from reference_holds AND from the impl's raise guard, leaving ONLY the complete-vs-curated collection choice in the no-raise condition -- and verified it: exit 1, failing the identical clause `(not reference_holds(value, ToSeq(complete_rows)))` at:115.

So the discrimination between pre- and post-patch is carried entirely by the COMPLETE-vs-curated clause, which is the publicly disclosed fact; choice_permitted contributes nothing to sensing the edit and cannot be a discriminator that a solver reads backwards into `_default_manager -> _base_manager`. It merely pins the full unchanged no-raise condition (present AND choice_permitted) so an impl that drops limit_choices_to is rejected. Its Ensures(True) is the weakest possible contract, and mapping.md 3.1 / refinement.md A5 document it as identical pre- and post-patch, which the diff confirms.

BUNDLE-DIRECTED-AT-REVIEWER CHECK (reported as a finding in its own right if present): none found. swebench_unified.leakage.reviewer_directed returns [] on mapping.md, refinement.md, axiom_check.py, conformance_check.py AND verdict.md; a manual grep for reviewer/panel/attacker/'honest verdict'/'you should submit'/NO-LEAKAGE across model.py and the docs surfaced only one incidental hit (refinement.md A7 citing the audited G-PANEL-1 counterexample filename atk_recurse_reject.py as justification for MustTerminate -- a provenance citation for a spec element, not an instruction to me). verdict.md is a machine-generated backfill of prior roles' recorded notes; it records but does not instruct. No file in the bundle tells me what to submit.

**CONCLUSION:** nothing in the spec view reconstructs the gold edit beyond what the public problem_statement already states outright; the sole non-public element is a measured non-discriminator on an unchanged callee, and the gates the judgement rests on (spec identity, G-VERIFY, G-DIFF, G-LEAK) I re-ran myself and all pass. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
