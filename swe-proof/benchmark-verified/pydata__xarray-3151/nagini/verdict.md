# P2 adversarial audit — pydata__xarray-3151

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk1_prepatch_all_dims.py`, `atk2_skip_first_dim.py`, `atk3_bystanders_only.py`, `atk5_divergence_unreachable_return.py`, `atk6_early_return_first_step.py`, `atk7_flags_swapped.py`, `atk8_never_reject.py`, `atk9_infeasible_selfcall_prepatch.py`, `atk10_needs_two_violations.py`, `atk11_raise_instead_of_answer.py`, +6 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk4_oracle_echo.py`, `atk18_reshape_accumulate.py` |

**Non-vacuity.** The positive control `pc_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch_all_dims.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,10 +124,6 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
     while i > 0:
@@ -141,18 +137,14 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
+        if is_monotonic[i - 1] == 0:
+            rejected = True
         i = i - 1
     return rejected
     # impl-end
```

Attack 2 — `atk2_skip_first_dim.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,13 +124,9 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(is_joined), 1 / 2))
         Invariant(Acc(list_pred(is_monotonic), 1 / 2))
@@ -141,9 +137,6 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
```

Attack 3 — `atk3_bystanders_only.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,10 +124,6 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
     while i > 0:
@@ -141,16 +137,13 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
+        if is_joined[i - 1] == 0:
             if is_monotonic[i - 1] == 0:
                 rejected = True
         i = i - 1
```

Attack 4 — `atk4_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -124,35 +124,6 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
-    rejected = False  # type: bool
-    i = len(is_joined)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(is_joined), 1 / 2))
-        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
-        Invariant(len(is_joined) == len(is_monotonic))
-        Invariant(0 <= i and i <= len(is_joined))
-        Invariant(len(ToSeq(is_joined)) == len(is_joined))
-        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
-        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
-        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
-        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
-        i = i - 1
-    return rejected
+    return any_joined_nonmonotonic(ToSeq(is_joined),
+                                   ToSeq(is_monotonic))
     # impl-end
```

Attack 5 — `atk5_divergence_unreachable_return.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,35 +124,13 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
-    while i > 0:
-        # invariants-start
+    while i >= 0:
         Invariant(Acc(list_pred(is_joined), 1 / 2))
         Invariant(Acc(list_pred(is_monotonic), 1 / 2))
-        Invariant(len(is_joined) == len(is_monotonic))
         Invariant(0 <= i and i <= len(is_joined))
-        Invariant(len(ToSeq(is_joined)) == len(is_joined))
-        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
-        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
-        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
-        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
-        i = i - 1
-    return rejected
+        rejected = not rejected
+    return any_joined_nonmonotonic(ToSeq(is_joined),
+                                   ToSeq(is_monotonic))
     # impl-end
```

Attack 6 — `atk6_early_return_first_step.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,10 +124,6 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
     while i > 0:
@@ -141,9 +137,6 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
@@ -153,6 +146,7 @@
         if is_joined[i - 1] == 1:
             if is_monotonic[i - 1] == 0:
                 rejected = True
+        return rejected
         i = i - 1
     return rejected
     # impl-end
```

Attack 7 — `atk7_flags_swapped.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,10 +124,6 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
     while i > 0:
@@ -141,17 +137,14 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
+        if is_monotonic[i - 1] == 1:
+            if is_joined[i - 1] == 0:
                 rejected = True
         i = i - 1
     return rejected
```

Attack 8 — `atk8_never_reject.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,35 +124,5 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
-    rejected = False  # type: bool
-    i = len(is_joined)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(is_joined), 1 / 2))
-        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
-        Invariant(len(is_joined) == len(is_monotonic))
-        Invariant(0 <= i and i <= len(is_joined))
-        Invariant(len(ToSeq(is_joined)) == len(is_joined))
-        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
-        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
-        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
-        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
-        i = i - 1
-    return rejected
+    return False
     # impl-end
```

Attack 9 — `atk9_infeasible_selfcall_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,10 +124,8 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
+    if len(is_joined) < 0:
+        return guard_rejects(is_joined, is_monotonic)
     rejected = False  # type: bool
     i = len(is_joined)
     while i > 0:
@@ -141,18 +139,14 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
+        if is_monotonic[i - 1] == 0:
+            rejected = True
         i = i - 1
     return rejected
     # impl-end
```

Attack 10 — `atk10_needs_two_violations.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,35 +124,26 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
-    rejected = False  # type: bool
+    bad = 0  # type: int
     i = len(is_joined)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(is_joined), 1 / 2))
         Invariant(Acc(list_pred(is_monotonic), 1 / 2))
         Invariant(len(is_joined) == len(is_monotonic))
         Invariant(0 <= i and i <= len(is_joined))
+        Invariant(0 <= bad)
         Invariant(len(ToSeq(is_joined)) == len(is_joined))
         Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
+        Invariant((bad > 0) == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
+                                                       ToSeq(is_monotonic).drop(i)))
         Invariant(MustTerminate(i))
-        # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
         if is_joined[i - 1] == 1:
             if is_monotonic[i - 1] == 0:
-                rejected = True
+                bad = bad + 1
         i = i - 1
-    return rejected
+    return bad > 1
     # impl-end
```

Attack 11 — `atk11_raise_instead_of_answer.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,35 +124,7 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
-    rejected = False  # type: bool
-    i = len(is_joined)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(is_joined), 1 / 2))
-        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
-        Invariant(len(is_joined) == len(is_monotonic))
-        Invariant(0 <= i and i <= len(is_joined))
-        Invariant(len(ToSeq(is_joined)) == len(is_joined))
-        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
-        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
-        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
-        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
-        i = i - 1
-    return rejected
+    if any_joined_nonmonotonic(ToSeq(is_joined), ToSeq(is_monotonic)):
+        raise ValueError("Resulting object does not have monotonic global indexes")
+    return False
     # impl-end
```

Attack 12 — `atk12_empty_domain_rejects.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,6 +124,8 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
+    if len(is_joined) == 0:
+        return True
     # Inspect only the dimensions that were joined along; a non-monotonic
     # joined dimension triggers rejection. Carried-through dimensions are
     # never inspected. Walk right-to-left so the front-recursive existential
```

Attack 13 — `atk14_complement_formula.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,35 +124,24 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
-    rejected = False  # type: bool
+    ok = True  # type: bool
     i = len(is_joined)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(is_joined), 1 / 2))
         Invariant(Acc(list_pred(is_monotonic), 1 / 2))
         Invariant(len(is_joined) == len(is_monotonic))
         Invariant(0 <= i and i <= len(is_joined))
         Invariant(len(ToSeq(is_joined)) == len(is_joined))
         Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(ok == (not any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
+                                                     ToSeq(is_monotonic).drop(i))))
         Invariant(MustTerminate(i))
-        # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
+        if is_joined[i - 1] != 0 and is_monotonic[i - 1] != 1:
+            ok = False
         i = i - 1
-    return rejected
+    return not ok
     # impl-end
```

Attack 14 — `atk15_raise_always.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,35 +124,5 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
-    rejected = False  # type: bool
-    i = len(is_joined)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(is_joined), 1 / 2))
-        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
-        Invariant(len(is_joined) == len(is_monotonic))
-        Invariant(0 <= i and i <= len(is_joined))
-        Invariant(len(ToSeq(is_joined)) == len(is_joined))
-        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
-        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
-        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
-        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
-        i = i - 1
-    return rejected
+    raise ValueError("Resulting object does not have monotonic global indexes")
     # impl-end
```

Attack 15 — `atk16_raise_when_ok.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,35 +124,7 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
-    rejected = False  # type: bool
-    i = len(is_joined)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(is_joined), 1 / 2))
-        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
-        Invariant(len(is_joined) == len(is_monotonic))
-        Invariant(0 <= i and i <= len(is_joined))
-        Invariant(len(ToSeq(is_joined)) == len(is_joined))
-        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
-        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
-        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
-                                                      ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
-        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
-        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
-        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
-        i = i - 1
-    return rejected
+    if any_joined_nonmonotonic(ToSeq(is_joined), ToSeq(is_monotonic)):
+        return False
+    raise ValueError("Resulting object does not have monotonic global indexes")
     # impl-end
```

Attack 16 — `atk17_latch_overwrite.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,10 +124,6 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
     while i > 0:
@@ -141,18 +137,13 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
+        rejected = is_joined[i - 1] == 1 and is_monotonic[i - 1] == 0
         i = i - 1
     return rejected
     # impl-end
```

Attack 17 — `atk18_reshape_accumulate.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -124,10 +124,6 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
-    # Inspect only the dimensions that were joined along; a non-monotonic
-    # joined dimension triggers rejection. Carried-through dimensions are
-    # never inspected. Walk right-to-left so the front-recursive existential
-    # unfolds one dimension per step.
     rejected = False  # type: bool
     i = len(is_joined)
     while i > 0:
@@ -141,18 +137,14 @@
         Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
         Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                       ToSeq(is_monotonic).drop(i)))
-        # the scan consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i))
         # invariants-end
         Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
         Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
         Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
         Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
-        if is_joined[i - 1] == 1:
-            if is_monotonic[i - 1] == 0:
-                rejected = True
+        rejected = rejected or (is_joined[i - 1] == 1
+                                and is_monotonic[i - 1] == 0)
         i = i - 1
     return rejected
     # impl-end
```

Attack 18 — `ctl_assert_false_vacuity.py` → rejected (same spec, does not verify — good)

```diff
@@ -124,6 +124,7 @@
                                                 ToSeq(is_monotonic)))
     # post-conditions-end
     # impl-start
+    Assert(False)
     # Inspect only the dimensions that were joined along; a non-monotonic
     # joined dimension triggers rejection. Carried-through dimensions are
     # never inspected. Walk right-to-left so the front-recursive existential
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.py`

```python
"""Twin-artifact model for pydata__xarray-3151.

Behavioural contract (the result a correct interpretation must produce):

  After several datasets have been arranged and joined together, a final
  consistency guard inspects the global ordering of the combined result. The
  guard concerns the dimensions along which the datasets were actually joined:
  for each such dimension the combined coordinate must run monotonically (it
  may run either upward or downward). If any joined dimension's combined
  coordinate is non-monotonic, the guard rejects the result.

  Dimensions whose coordinate did NOT vary between the inputs (and so were
  carried through untouched, not joined along) are NOT subject to this guard.
  Such a carried-through coordinate is allowed to be in any order — including
  non-monotonic — because the join did not reorder it. The documented promise
  is that coordinate dimensions which do not vary between the inputs are left
  alone.

  Each dimension of the combined result is modelled by two parallel flags,
  indexed by dimension position:

    * `is_joined`    — whether the datasets were concatenated along this
                       dimension (i.e. its coordinate varied between inputs);
    * `is_monotonic` — whether this dimension's combined coordinate is
                       monotonic (increasing OR decreasing).

  The contract on the result (a boolean: whether the guard rejects), formalised
  by the `Ensures` clauses below:

    * the guard rejects exactly when some JOINED dimension is non-monotonic,
      i.e. `Result()` equals `any_joined_nonmonotonic(is_joined, is_monotonic)`;
    * equivalently, a non-monotonic dimension that was NOT joined along never
      causes rejection.

  The two flag lists are the type-refinement carrier of the combined result's
  dimensions and their inferred-order metadata; the unchanged monotonicity test
  on a single coordinate and the unchanged join machinery are the refinement
  boundary documented in mapping.md.

Dimensions are modelled as parallel `List[int]` of 0/1 flags (Nagini bans the
rich result object and `str` dimension names); the specification is carried by
`PSeq[int]` via `ToSeq`. The over-the-dimensions existential is spelled out as a
front-recursive `@Pure` fold so a single unfold is available per loop step.

The guard is a bounded scan over the finite dimension metadata: it MUST
terminate and actually ANSWER (return its verdict, so the caller can either
reject or hand the combined result on). This total-correctness
obligation is carried as `MustTerminate` in the precondition. Nagini is a
partial-correctness verifier by default, so without the obligation a
non-terminating implementation (e.g. a loop that never advances) satisfies
every `Ensures` vacuously; the real guard always completes its scan.

Note `any_joined_nonmonotonic` is FULLY GROUNDED in the two input carriers —
it is a computable existential over the flag lists, not an opaque answer-key
oracle. An implementation that returns it directly therefore computes the
correct verdict (it is a positive control, equivalent to the gold loop), not
an ungrounded echo.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The per-dimension
#  monotonicity test and the join machinery that produces the dimension
#  metadata are the refinement boundary, documented in mapping.md, not axioms.
#  The selection rule that decides WHICH dimensions the guard inspects is the
#  changed behaviour and is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def any_joined_nonmonotonic(is_joined: PSeq[int], is_mono: PSeq[int]) -> bool:
    """True iff some dimension that was joined along is non-monotonic.

    Front-recursive existential over the dimensions: a dimension contributes a
    violation iff it was joined along (`is_joined == 1`) AND its combined
    coordinate is non-monotonic (`is_mono == 0`). Carried-through dimensions
    (`is_joined == 0`) never contribute, regardless of their monotonicity.
    Front-recursive so a single unfold is available to the loop per step.
    """
    Requires(len(is_joined) == len(is_mono))
    if len(is_joined) == 0:
        return False
    head_violates = is_joined[0] == 1 and is_mono[0] == 0
    return head_violates or any_joined_nonmonotonic(is_joined.drop(1),
                                                    is_mono.drop(1))
# pure-end


def guard_rejects(is_joined: List[int], is_monotonic: List[int]) -> bool:
    # pre-conditions-start
    # The two flag lists are read-only metadata of the combined result, one
    # entry per dimension, aligned by position. Each flag is 0 or 1.
    Requires(Acc(list_pred(is_joined), 1 / 2))
    Requires(Acc(list_pred(is_monotonic), 1 / 2))
    Requires(len(is_joined) == len(is_monotonic))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_joined),
                                            is_joined[k] == 0 or is_joined[k] == 1),
                                     [[is_joined[k]]])))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_monotonic),
                                            is_monotonic[k] == 0 or is_monotonic[k] == 1),
                                     [[is_monotonic[k]]])))
    # TERMINATION: the guard is a bounded scan over the finite dimension
    # metadata and must actually ANSWER (return its verdict so the caller can
    # raise or proceed). Nagini is a partial-correctness verifier by default;
    # without this obligation a non-terminating implementation (e.g. a loop
    # that never advances) satisfies every Ensures vacuously. The real guard
    # always completes its scan.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_joined), 1 / 2))
    Ensures(Acc(list_pred(is_monotonic), 1 / 2))
    Ensures(len(ToSeq(is_joined)) == len(is_joined))
    Ensures(len(ToSeq(is_monotonic)) == len(is_monotonic))
    Ensures(len(ToSeq(is_joined)) == len(ToSeq(is_monotonic)))
    # The guard rejects exactly when some JOINED dimension is non-monotonic.
    Ensures(Result() == any_joined_nonmonotonic(ToSeq(is_joined),
                                                ToSeq(is_monotonic)))
    # post-conditions-end
    # impl-start
    # Inspect only the dimensions that were joined along; a non-monotonic
    # joined dimension triggers rejection. Carried-through dimensions are
    # never inspected. Walk right-to-left so the front-recursive existential
    # unfolds one dimension per step.
    rejected = False  # type: bool
    i = len(is_joined)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(is_joined), 1 / 2))
        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
        Invariant(len(is_joined) == len(is_monotonic))
        Invariant(0 <= i and i <= len(is_joined))
        Invariant(len(ToSeq(is_joined)) == len(is_joined))
        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                      ToSeq(is_monotonic).drop(i)))
        # the scan consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i))
        # invariants-end
        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
        if is_joined[i - 1] == 1:
            if is_monotonic[i - 1] == 0:
                rejected = True
        i = i - 1
    return rejected
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (advisory). 17 same-spec wrong/probe impls + 1 vacuity control, all admissible (unsound_evasions empty for every file); 16 REJECTED by the spec, 2 CANDIDATEs, and BOTH candidates' materialized faithful patches RESOLVE under the official harness -> correct echoes, not verify⇏⊇correct. Positive control (byte-identical model.py) VERIFIES (15s).

All attacks built by substituting ONLY the impl region of the frozen model.py; `adversary same-spec` returned rc 0 (SAME) for all 18 files + the control. Command form used throughout:
  python -m swebench_unified.adversary weakness nagini pydata__xarray-3151 <file>.py
Run 3-at-a-time as background jobs (runbatch.sh); positive control via `adversary verify`.

### PER-ATTACK RESULTS (path = <name>.py):
1. atk1_prepatch_all_dims  rc=2 REJECTED. THE PREPATCH BUG, re-encoded: rejects on ANY non-monotonic dim, joined or bystander (the spurious ValueError of issue #3150). Verified core-line-identical to the bundle's own model_prepatch.py impl region. => prepatch_reproduced=true.
2. atk2_skip_first_dim  rc=2 REJECTED. Partial domain / boundary: scans down to i>1, so dimension 0 is never inspected. Wrong on is_joined=[1], is_mono=[0].
3. atk3_bystanders_only  rc=2 REJECTED. Inverted selection: guards the BYSTANDER dims (`dim not in concat_dims`) instead of the joined ones.
4. atk4_oracle_echo  rc=0 CANDIDATE (21.2s). Returns the @Pure existential directly. Faithful patch materialized (patch_atk4_oracle_echo.diff, git apply --check clean at base_commit, parses) and RUN: harness.run_resolve -> completed=True RESOLVED=True, attempts=1, not flaky, patch_successfully_applied=True, F2P 1/1, P2P 66/66. As the docstring says, the existential is fully GROUNDED in the two input carriers, so this is a positive control equivalent to the gold loop, not an ungrounded answer-key echo. NOT a weakness.
5. atk5_divergence_unreachable_return  rc=2 REJECTED. The control-flow-effect / vacuity shape the earlier G-PANEL-1 audit exploited when the spec carried no termination obligation (`while i >= 0` never advancing, correct return unreachable). MustTerminate(2) now rejects it, so verdict.md's "Record correction" is confirmed on a re-run, not taken on trust.
6. atk6_early_return_first_step  rc=2 REJECTED. Early exit inside the scan: answers after inspecting only the last dimension. Permissions and measure fine, answer truncated.
7. atk7_flags_swapped  rc=2 REJECTED. Reads the two parallel carriers the wrong way round (rejects iff some MONOTONIC dim was not joined).
8. atk8_never_reject  rc=2 REJECTED. Constant undershoot `return False` (refined: deletes the guard entirely).
9. atk9_infeasible_selfcall_prepatch  rc=2 REJECTED. Guarded-self-call vacuity probe: `if len(is_joined) < 0: return guard_rejects(...)` in front of the prepatch body. The infeasible guard does not let the wrong body escape checking.
10. atk10_needs_two_violations  rc=2 REJECTED. Threshold oracle: reject only on >=2 non-monotonic joined dims. Agrees with the spec on every vector with 0 or >=2 violations and differs on exactly one -- and the F2P/P2P scenarios all have at most one, so this is the wrong impl the tests alone would be weakest against. The spec still catches it.
11. atk11_raise_instead_of_answer  rc=2 REJECTED. Exceptional exit on the reject path (the real guard signals by raising), returning False otherwise.
12. atk12_empty_domain_rejects  rc=2 REJECTED. Partial-domain boundary: gold body, but `if len(is_joined)==0: return True` -- refined, a group needing no concatenation is spuriously rejected.
13. atk14_complement_formula  rc=2 REJECTED (complementary `ok`/`not ok` accumulation; intended as a correct reshape, its weaker invariant did not carry the postcondition -- counted as a rejection, not as evidence either way).
14. atk15_raise_always  rc=2 REJECTED. Unconditional `raise`: NO normal exit at all. MustTerminate closes the DIVERGENCE route to vacuity, but a raise also terminates -- so this probes the remaining vacuity route directly. Rejected, so the spec pins a returned verdict, not merely termination.
15. atk16_raise_when_ok  rc=2 REJECTED. Inverted exceptional exit: accept (return False) exactly when it should reject, raise when it should pass. Second exceptional-vacuity probe; rejected.
16. atk17_latch_overwrite  rc=2 REJECTED. Real bug shape: `rejected = <this dim violates>` (assign, not accumulate), so only the last-visited joined dim decides.
17. atk18_reshape_accumulate  rc=0 CANDIDATE (15s). Correct reshape, second INDEPENDENT embedding of the same verdict (`rejected = rejected or (joined and not mono)`). Faithful patch materialized (patch_atk18_reshape_accumulate.diff, apply-checked + parses) and RUN: run_resolve -> completed=True RESOLVED=True, attempts=1, not flaky, F2P 1/1, P2P 66/66. Two differently-shaped repo embeddings of the spec's verdict both resolve, which is where a model<->patch correspondence gap would have surfaced.
18. ctl_assert_false_vacuity  rc=2 REJECTED. `Assert(False)` in front of the gold body: the frozen precondition is SATISFIABLE, so the proof is non-vacuous and the 16 rejections above are real rejections rather than an unreachable-state artifact.

NEGATIVE CONTROL ON MY OWN RESOLVE PIPELINE (the check that makes the two RESOLVED verdicts meaningful): atk3_bystanders_only's faithful refined patch (patch_atk3_bystanders_only.diff) was ALSO run through run_resolve -> completed=True, RESOLVED=FALSE, 3 consistent attempts, patch_successfully_applied=True, F2P 0/1 (test_combine_leaving_bystander_dimensions FAILS) and P2P 65/66 (test_check_for_impossible_ordering FAILS). So (a) the oracle can refute on this instance, and (b) my patch-materialization method does produce non-resolving patches for genuinely wrong impls -- the candidates' RESOLVED is not a pipeline artifact. Bundle-recorded G-RESOLVE=pass on gold independently confirms the oracle is usable here.

A-LEG AUDIT (the assigned focus; R/I legs left to G-CONF). refinement.md tags: A1=R, A2=R, A3=R + A-reference, A4=R, A5=R. NO kind-3 step and NO A-consumed leg -- there is no @ContractOnly declaration anywhere in model.py (the axioms region is a comment only), so axiom soundness is vacuous beyond the single A-reference. That matches the artifact.
  * axiom_check.py on the host: rc 0 (341 exhaustive boundary vectors, dim counts 0..4, + 50000 fuzz). Its CONCRETE real-library leg SKIPPED on the host ("skip-no-xarray", 0 scenarios), i.e. the strongest part of the A-reference is not exercised where the gate runs -- so I ran it myself rather than accept it.
  * areference_probe.py, run IN-CONTAINER with the gold patch applied (docker_exec.run_in_container(apply_gold=True)): rc 0. 46 scenarios, 0 mismatches, skipped 1, BOTH verdicts exercised (so agreement is not the trivial "never rejects"). Critically it reads the R-carriers OUT OF the real library -- is_joined from the actual `concat_dims` returned by `_infer_concat_order_from_coords`, is_monotonic from the ACTUAL combined index produced by `_combine_nd` -- rather than guessing the combined coordinate (the harness bug the G-PANEL-2 note describes: a sorted-union guess vs the library's tile-order concatenation, e.g. x=[1,11]+[2,4] -> [1,11,2,4]). Includes the issue's y=['a','c','b'] bystander, a non-monotonic joined dim, joined-decreasing, both-bad, single-dataset/no-concat, two-joined-dims, and 40 randomized two-dataset cases. The A3 raise<->Result()==True and is_monotonic bijections hold on real data.
  * aleg_edge_probe.py, in-container + gold: rc 0. Probes the ways the repo could escape the two-valued boolean model: (E1) a dim in concat_dims whose combined index is None -- would make the post-patch guard AttributeError, a THIRD outcome A3's bijection presumes away: not reachable (a non-coordinate dim never enters concat_dims and drops out of the modeled domain). (E2) mapping.md's domain-restriction claim `concat_dims subset of {coordinate dims present}` -- asserted per scenario across all 46+ cases, never violated. Multi-GROUP composition: combine_by_coords runs the guard once per data-var group while model.py models ONE invocation; the composite "reject iff any group rejects" matched the real library. F2P scenario re-confirmed to DISCRIMINATE: prepatch_model=True, model=False, real_postpatch=False -- the spec models the fixed side (consistent with the recorded G-DIFF pass on model_prepatch.py).

**CONCLUSION:** the spec is not too weak on any of these 17 axes, the model<->patch correspondence holds on the real library including the boundary cases the boolean carrier could have hidden, and every CANDIDATE is a correct echo whose patch was actually executed through the harness. No verify⇏⊇correct witness found. Advisory verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 18 admissible attacks re-run of 18 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 18 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 16 | `atk1_prepatch_all_dims.py`, `atk2_skip_first_dim.py`, `atk3_bystanders_only.py`, `atk5_divergence_unreachable_return.py`, `atk6_early_return_first_step.py`, `atk7_flags_swapped.py`, `atk8_never_reject.py`, `atk9_infeasible_selfcall_prepatch.py`, `atk10_needs_two_violations.py`, `atk11_raise_instead_of_answer.py`, +6 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk4_oracle_echo.py`, `atk18_reshape_accumulate.py` |

**Non-vacuity.** The positive control `pc_correct.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (18):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 18 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch_all_dims.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_skip_first_dim.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_bystanders_only.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_oracle_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk5_divergence_unreachable_return.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_early_return_first_step.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_flags_swapped.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_never_reject.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk9_infeasible_selfcall_prepatch.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk10_needs_two_violations.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk11_raise_instead_of_answer.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk12_empty_domain_rejects.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk14_complement_formula.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk15_raise_always.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk16_raise_when_ok.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk17_latch_overwrite.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk18_reshape_accumulate.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `ctl_assert_false_vacuity.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_correct.py`

```python
"""Twin-artifact model for pydata__xarray-3151.

Behavioural contract (the result a correct interpretation must produce):

  After several datasets have been arranged and joined together, a final
  consistency guard inspects the global ordering of the combined result. The
  guard concerns the dimensions along which the datasets were actually joined:
  for each such dimension the combined coordinate must run monotonically (it
  may run either upward or downward). If any joined dimension's combined
  coordinate is non-monotonic, the guard rejects the result.

  Dimensions whose coordinate did NOT vary between the inputs (and so were
  carried through untouched, not joined along) are NOT subject to this guard.
  Such a carried-through coordinate is allowed to be in any order — including
  non-monotonic — because the join did not reorder it. The documented promise
  is that coordinate dimensions which do not vary between the inputs are left
  alone.

  Each dimension of the combined result is modelled by two parallel flags,
  indexed by dimension position:

    * `is_joined`    — whether the datasets were concatenated along this
                       dimension (i.e. its coordinate varied between inputs);
    * `is_monotonic` — whether this dimension's combined coordinate is
                       monotonic (increasing OR decreasing).

  The contract on the result (a boolean: whether the guard rejects), formalised
  by the `Ensures` clauses below:

    * the guard rejects exactly when some JOINED dimension is non-monotonic,
      i.e. `Result()` equals `any_joined_nonmonotonic(is_joined, is_monotonic)`;
    * equivalently, a non-monotonic dimension that was NOT joined along never
      causes rejection.

  The two flag lists are the type-refinement carrier of the combined result's
  dimensions and their inferred-order metadata; the unchanged monotonicity test
  on a single coordinate and the unchanged join machinery are the refinement
  boundary documented in mapping.md.

Dimensions are modelled as parallel `List[int]` of 0/1 flags (Nagini bans the
rich result object and `str` dimension names); the specification is carried by
`PSeq[int]` via `ToSeq`. The over-the-dimensions existential is spelled out as a
front-recursive `@Pure` fold so a single unfold is available per loop step.

The guard is a bounded scan over the finite dimension metadata: it MUST
terminate and actually ANSWER (return its verdict, so the caller can either
reject or hand the combined result on). This total-correctness
obligation is carried as `MustTerminate` in the precondition. Nagini is a
partial-correctness verifier by default, so without the obligation a
non-terminating implementation (e.g. a loop that never advances) satisfies
every `Ensures` vacuously; the real guard always completes its scan.

Note `any_joined_nonmonotonic` is FULLY GROUNDED in the two input carriers —
it is a computable existential over the flag lists, not an opaque answer-key
oracle. An implementation that returns it directly therefore computes the
correct verdict (it is a positive control, equivalent to the gold loop), not
an ungrounded echo.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The per-dimension
#  monotonicity test and the join machinery that produces the dimension
#  metadata are the refinement boundary, documented in mapping.md, not axioms.
#  The selection rule that decides WHICH dimensions the guard inspects is the
#  changed behaviour and is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def any_joined_nonmonotonic(is_joined: PSeq[int], is_mono: PSeq[int]) -> bool:
    """True iff some dimension that was joined along is non-monotonic.

    Front-recursive existential over the dimensions: a dimension contributes a
    violation iff it was joined along (`is_joined == 1`) AND its combined
    coordinate is non-monotonic (`is_mono == 0`). Carried-through dimensions
    (`is_joined == 0`) never contribute, regardless of their monotonicity.
    Front-recursive so a single unfold is available to the loop per step.
    """
    Requires(len(is_joined) == len(is_mono))
    if len(is_joined) == 0:
        return False
    head_violates = is_joined[0] == 1 and is_mono[0] == 0
    return head_violates or any_joined_nonmonotonic(is_joined.drop(1),
                                                    is_mono.drop(1))
# pure-end


def guard_rejects(is_joined: List[int], is_monotonic: List[int]) -> bool:
    # pre-conditions-start
    # The two flag lists are read-only metadata of the combined result, one
    # entry per dimension, aligned by position. Each flag is 0 or 1.
    Requires(Acc(list_pred(is_joined), 1 / 2))
    Requires(Acc(list_pred(is_monotonic), 1 / 2))
    Requires(len(is_joined) == len(is_monotonic))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_joined),
                                            is_joined[k] == 0 or is_joined[k] == 1),
                                     [[is_joined[k]]])))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_monotonic),
                                            is_monotonic[k] == 0 or is_monotonic[k] == 1),
                                     [[is_monotonic[k]]])))
    # TERMINATION: the guard is a bounded scan over the finite dimension
    # metadata and must actually ANSWER (return its verdict so the caller can
    # raise or proceed). Nagini is a partial-correctness verifier by default;
    # without this obligation a non-terminating implementation (e.g. a loop
    # that never advances) satisfies every Ensures vacuously. The real guard
    # always completes its scan.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_joined), 1 / 2))
    Ensures(Acc(list_pred(is_monotonic), 1 / 2))
    Ensures(len(ToSeq(is_joined)) == len(is_joined))
    Ensures(len(ToSeq(is_monotonic)) == len(is_monotonic))
    Ensures(len(ToSeq(is_joined)) == len(ToSeq(is_monotonic)))
    # The guard rejects exactly when some JOINED dimension is non-monotonic.
    Ensures(Result() == any_joined_nonmonotonic(ToSeq(is_joined),
                                                ToSeq(is_monotonic)))
    # post-conditions-end
    # impl-start
    # Inspect only the dimensions that were joined along; a non-monotonic
    # joined dimension triggers rejection. Carried-through dimensions are
    # never inspected. Walk right-to-left so the front-recursive existential
    # unfolds one dimension per step.
    rejected = False  # type: bool
    i = len(is_joined)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(is_joined), 1 / 2))
        Invariant(Acc(list_pred(is_monotonic), 1 / 2))
        Invariant(len(is_joined) == len(is_monotonic))
        Invariant(0 <= i and i <= len(is_joined))
        Invariant(len(ToSeq(is_joined)) == len(is_joined))
        Invariant(len(ToSeq(is_monotonic)) == len(is_monotonic))
        Invariant(len(ToSeq(is_joined).drop(i)) == len(ToSeq(is_monotonic).drop(i)))
        Invariant(rejected == any_joined_nonmonotonic(ToSeq(is_joined).drop(i),
                                                      ToSeq(is_monotonic).drop(i)))
        # the scan consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i))
        # invariants-end
        Assert(ToSeq(is_joined).drop(i - 1)[0] == is_joined[i - 1])
        Assert(ToSeq(is_monotonic).drop(i - 1)[0] == is_monotonic[i - 1])
        Assert(ToSeq(is_joined).drop(i - 1).drop(1) == ToSeq(is_joined).drop(i))
        Assert(ToSeq(is_monotonic).drop(i - 1).drop(1) == ToSeq(is_monotonic).drop(i))
        if is_joined[i - 1] == 1:
            if is_monotonic[i - 1] == 0:
                rejected = True
        i = i - 1
    return rejected
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND (advisory). 17 same-spec wrong/probe impls + 1 vacuity control, all admissible (unsound_evasions empty for every file); 16 REJECTED by the spec, 2 CANDIDATEs, and BOTH candidates' materialized faithful patches RESOLVE under the official harness -> correct echoes, not verify⇏⊇correct. Positive control (byte-identical model.py) VERIFIES (15s).

All attacks built by substituting ONLY the impl region of the frozen model.py; `adversary same-spec` returned rc 0 (SAME) for all 18 files + the control. Command form used throughout:
  python -m swebench_unified.adversary weakness nagini pydata__xarray-3151 <file>.py
Run 3-at-a-time as background jobs (runbatch.sh); positive control via `adversary verify`.

### PER-ATTACK RESULTS (path = <name>.py):
1. atk1_prepatch_all_dims  rc=2 REJECTED. THE PREPATCH BUG, re-encoded: rejects on ANY non-monotonic dim, joined or bystander (the spurious ValueError of issue #3150). Verified core-line-identical to the bundle's own model_prepatch.py impl region. => prepatch_reproduced=true.
2. atk2_skip_first_dim  rc=2 REJECTED. Partial domain / boundary: scans down to i>1, so dimension 0 is never inspected. Wrong on is_joined=[1], is_mono=[0].
3. atk3_bystanders_only  rc=2 REJECTED. Inverted selection: guards the BYSTANDER dims (`dim not in concat_dims`) instead of the joined ones.
4. atk4_oracle_echo  rc=0 CANDIDATE (21.2s). Returns the @Pure existential directly. Faithful patch materialized (patch_atk4_oracle_echo.diff, git apply --check clean at base_commit, parses) and RUN: harness.run_resolve -> completed=True RESOLVED=True, attempts=1, not flaky, patch_successfully_applied=True, F2P 1/1, P2P 66/66. As the docstring says, the existential is fully GROUNDED in the two input carriers, so this is a positive control equivalent to the gold loop, not an ungrounded answer-key echo. NOT a weakness.
5. atk5_divergence_unreachable_return  rc=2 REJECTED. The control-flow-effect / vacuity shape the earlier G-PANEL-1 audit exploited when the spec carried no termination obligation (`while i >= 0` never advancing, correct return unreachable). MustTerminate(2) now rejects it, so verdict.md's "Record correction" is confirmed on a re-run, not taken on trust.
6. atk6_early_return_first_step  rc=2 REJECTED. Early exit inside the scan: answers after inspecting only the last dimension. Permissions and measure fine, answer truncated.
7. atk7_flags_swapped  rc=2 REJECTED. Reads the two parallel carriers the wrong way round (rejects iff some MONOTONIC dim was not joined).
8. atk8_never_reject  rc=2 REJECTED. Constant undershoot `return False` (refined: deletes the guard entirely).
9. atk9_infeasible_selfcall_prepatch  rc=2 REJECTED. Guarded-self-call vacuity probe: `if len(is_joined) < 0: return guard_rejects(...)` in front of the prepatch body. The infeasible guard does not let the wrong body escape checking.
10. atk10_needs_two_violations  rc=2 REJECTED. Threshold oracle: reject only on >=2 non-monotonic joined dims. Agrees with the spec on every vector with 0 or >=2 violations and differs on exactly one -- and the F2P/P2P scenarios all have at most one, so this is the wrong impl the tests alone would be weakest against. The spec still catches it.
11. atk11_raise_instead_of_answer  rc=2 REJECTED. Exceptional exit on the reject path (the real guard signals by raising), returning False otherwise.
12. atk12_empty_domain_rejects  rc=2 REJECTED. Partial-domain boundary: gold body, but `if len(is_joined)==0: return True` -- refined, a group needing no concatenation is spuriously rejected.
13. atk14_complement_formula  rc=2 REJECTED (complementary `ok`/`not ok` accumulation; intended as a correct reshape, its weaker invariant did not carry the postcondition -- counted as a rejection, not as evidence either way).
14. atk15_raise_always  rc=2 REJECTED. Unconditional `raise`: NO normal exit at all. MustTerminate closes the DIVERGENCE route to vacuity, but a raise also terminates -- so this probes the remaining vacuity route directly. Rejected, so the spec pins a returned verdict, not merely termination.
15. atk16_raise_when_ok  rc=2 REJECTED. Inverted exceptional exit: accept (return False) exactly when it should reject, raise when it should pass. Second exceptional-vacuity probe; rejected.
16. atk17_latch_overwrite  rc=2 REJECTED. Real bug shape: `rejected = <this dim violates>` (assign, not accumulate), so only the last-visited joined dim decides.
17. atk18_reshape_accumulate  rc=0 CANDIDATE (15s). Correct reshape, second INDEPENDENT embedding of the same verdict (`rejected = rejected or (joined and not mono)`). Faithful patch materialized (patch_atk18_reshape_accumulate.diff, apply-checked + parses) and RUN: run_resolve -> completed=True RESOLVED=True, attempts=1, not flaky, F2P 1/1, P2P 66/66. Two differently-shaped repo embeddings of the spec's verdict both resolve, which is where a model<->patch correspondence gap would have surfaced.
18. ctl_assert_false_vacuity  rc=2 REJECTED. `Assert(False)` in front of the gold body: the frozen precondition is SATISFIABLE, so the proof is non-vacuous and the 16 rejections above are real rejections rather than an unreachable-state artifact.

NEGATIVE CONTROL ON MY OWN RESOLVE PIPELINE (the check that makes the two RESOLVED verdicts meaningful): atk3_bystanders_only's faithful refined patch (patch_atk3_bystanders_only.diff) was ALSO run through run_resolve -> completed=True, RESOLVED=FALSE, 3 consistent attempts, patch_successfully_applied=True, F2P 0/1 (test_combine_leaving_bystander_dimensions FAILS) and P2P 65/66 (test_check_for_impossible_ordering FAILS). So (a) the oracle can refute on this instance, and (b) my patch-materialization method does produce non-resolving patches for genuinely wrong impls -- the candidates' RESOLVED is not a pipeline artifact. Bundle-recorded G-RESOLVE=pass on gold independently confirms the oracle is usable here.

A-LEG AUDIT (the assigned focus; R/I legs left to G-CONF). refinement.md tags: A1=R, A2=R, A3=R + A-reference, A4=R, A5=R. NO kind-3 step and NO A-consumed leg -- there is no @ContractOnly declaration anywhere in model.py (the axioms region is a comment only), so axiom soundness is vacuous beyond the single A-reference. That matches the artifact.
  * axiom_check.py on the host: rc 0 (341 exhaustive boundary vectors, dim counts 0..4, + 50000 fuzz). Its CONCRETE real-library leg SKIPPED on the host ("skip-no-xarray", 0 scenarios), i.e. the strongest part of the A-reference is not exercised where the gate runs -- so I ran it myself rather than accept it.
  * areference_probe.py, run IN-CONTAINER with the gold patch applied (docker_exec.run_in_container(apply_gold=True)): rc 0. 46 scenarios, 0 mismatches, skipped 1, BOTH verdicts exercised (so agreement is not the trivial "never rejects"). Critically it reads the R-carriers OUT OF the real library -- is_joined from the actual `concat_dims` returned by `_infer_concat_order_from_coords`, is_monotonic from the ACTUAL combined index produced by `_combine_nd` -- rather than guessing the combined coordinate (the harness bug the G-PANEL-2 note describes: a sorted-union guess vs the library's tile-order concatenation, e.g. x=[1,11]+[2,4] -> [1,11,2,4]). Includes the issue's y=['a','c','b'] bystander, a non-monotonic joined dim, joined-decreasing, both-bad, single-dataset/no-concat, two-joined-dims, and 40 randomized two-dataset cases. The A3 raise<->Result()==True and is_monotonic bijections hold on real data.
  * aleg_edge_probe.py, in-container + gold: rc 0. Probes the ways the repo could escape the two-valued boolean model: (E1) a dim in concat_dims whose combined index is None -- would make the post-patch guard AttributeError, a THIRD outcome A3's bijection presumes away: not reachable (a non-coordinate dim never enters concat_dims and drops out of the modeled domain). (E2) mapping.md's domain-restriction claim `concat_dims subset of {coordinate dims present}` -- asserted per scenario across all 46+ cases, never violated. Multi-GROUP composition: combine_by_coords runs the guard once per data-var group while model.py models ONE invocation; the composite "reject iff any group rejects" matched the real library. F2P scenario re-confirmed to DISCRIMINATE: prepatch_model=True, model=False, real_postpatch=False -- the spec models the fixed side (consistent with the recorded G-DIFF pass on model_prepatch.py).

**CONCLUSION:** the spec is not too weak on any of these 17 axes, the model<->patch correspondence holds on the real library including the boundary cases the boolean carrier could have hidden, and every CANDIDATE is a correct echo whose patch was actually executed through the harness. No verify⇏⊇correct witness found. Advisory verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SPEC UNDER AUDIT: guard_rejects(is_joined, is_monotonic) with Ensures(Result() == any_joined_nonmonotonic(ToSeq(is_joined), ToSeq(is_monotonic))) -- reject iff some JOINED dim (is_joined==1) is non-monotonic (is_mono==0); bystander dims (is_joined==0) never cause rejection. Models the gold hunk `for dim in concatenated.dims: if dim in concatenated:` -> `for dim in concat_dims:` at xarray/core/combine.py:503.

REFERENCE BUILT CORRECTLY (per the brief): worktree at base_commit 118f4d996e7711c9aced916e6049af9f28d5ec66 from the upstream repository, then gold.patch (extracted verbatim from data/swe_bench_verified/test.jsonl, confirmed byte-identical to the hunk quoted in refinement.md) APPLIED ->, installed editable into a purpose-built era-appropriate env (py3.8 / numpy 1.17.5 / pandas 0.25.3) so combine_by_coords actually executes. Post-gold marker `for dim in concat_dims:` confirmed present, pre-patch marker absent. A separate un-patched tree kept ONLY to confirm the delta direction.

### EVIDENCE (measured against the real library, not reasoned):
1. F2P test test_combine.py::TestCombineAuto::test_combine_leaving_bystander_dimensions PASSES on the gold tree (1 passed).
2. Bundle's own axiom_check.py, re-pointed from /testbed to the real gold tree so the provenance gate OPENS instead of skipping: rc 0, 'ran-post-gold (3 scenarios checked)' + 341 exhaustive boundary vectors + 50000 fuzz. Note the host-run of this script SKIPS the concrete arm (no xarray); I forced the real arm to actually run.
3. FAITHFUL FUZZ, ~2190 accepted 2-3-Dataset scenarios: is_joined/is_monotonic derived from the ACTUAL library state (`_infer_concat_order_from_coords` -> real concat_dims membership; real combined index's is_monotonic_increasing/decreasing off `_combine_nd`'s output), NOT guessed, then compared against whether the real combine_by_coords raises the modeled 'monotonic global indexes' ValueError. 0 mismatches. Contingency table fully populated in BOTH cells: (model=True,real=True)=1110, (model=False,real=False)=1080 -- no empty diagonal, so the agreement is not vacuous. 1810 scenarios that tripped a NON-modeled upstream guard (the `_infer_concat_order_from_coords` 'neither monotonically increasing nor decreasing' per-dataset check) were excluded as out-of-domain rather than silently counted as agreement.
4. DISCRIMINATING FAMILY, exhaustive: all 6 permutations of y=['a','b','c'] x 4 x-pair shapes = 24 real scenarios. 0 mismatches. Critically this reaches the cell where a too-strong spec would break: y a bystander that is genuinely NON-monotonic on the real combined index (e.g. y=['a','c','b'], ['b','a','c'], ['b','c','a'], ['c','a','b']) while x is joined and monotonic -> real library does NOT raise and the model does NOT reject. Real cells hit: (1,1)=18, (0,1)=8, (1,0)=6, (0,0)=16.
5. MULTI-JOINED-DIM (the Ensures' `any` quantifier over >1 joined dim, which my 1-D scenarios could not reach): 2x2 tile grid so concat_dims==['x','y'], all four monotonicity combinations j=[1,1] with m in {[1,1],[0,1],[1,0],[0,0]}. All 4 OK. Confirms the existential, not just the singleton case.
6. **EDGE CASES:** empty concat_dims (single dataset, x=[3,1,2] itself non-monotonic) -> real no-raise, model no-reject, matches len==0 base case of the front-recursive fold. Dimension present in result but NOT a coordinate ('z', no index) -> real no-raise; matches. Multi-group merge (two data_vars -> 2 groups) -> matches for both monotonic and interleaved.
7. MAPPING.MD DOMAIN CLAIM CHECKED, not assumed: mapping.md asserts concat_dims is a SUBSET of {coordinate dims present in result}. Measured over 400 randomized scenarios incl. no-coordinate dims: 0 subset violations. So the model's domain restriction cannot hide a joined dimension the guard would have inspected -- the direction that would make the spec too weak/strong is closed empirically.
8. DELTA DIRECTION CONFIRMED (guards against the trap in the brief): on the PRE-patch tree the issue case y=['a','c','b'] RAISES 'Resulting object does not have monotonic global indexes' while the model says no-reject. That disagreement is precisely the bug the patch fixes, so it evidences the model describes the FIXED behavior -- it is NOT reported as unfaithfulness.
9. **NON-VACUITY:** MustTerminate(2) in the precondition + Invariant(MustTerminate(i)) loop measure close the partial-correctness hole (a diverging impl can no longer satisfy Ensures vacuously). Model verifies rc 0.

R-BIJECTIONS all hold on real data: is_joined[d]==1 <-> d in concat_dims; is_monotonic[d]==1 <-> combined index is_monotonic_increasing or is_monotonic_decreasing; Result()==True <-> raise ValueError. The spec is neither too strong nor drifted: it does not demand rejection on any input where the real post-patch guard falls through, and does not permit fall-through where the real guard raises.

SCOPE / LIMITS honestly stated: scenarios are <=4 Datasets over <=2 concatenated dimensions with int/str 1-D coords; I did not exercise NaN/datetime coords, >2 concat dims, or fill_value-driven reindexing paths. Nothing in those paths touches the guard's selection rule (the only changed operation), so I judge residual risk low, but it is untested rather than proven. Work confined to /tmp (worktrees,, harnesses, env); the bundle was read-only throughout and not modified.

Counterexample / evidence:

```
None. Positive control: model.py verifies with the pinned Nagini verifier (rc 0, 16.0s); same-spec self-check rc 0.
```

**SPEC UNDER AUDIT:** guard_rejects(is_joined, is_monotonic) with Ensures(Result() == any_joined_nonmonotonic(ToSeq(is_joined), ToSeq(is_monotonic))) -- reject iff some JOINED dim (is_joined==1) is non-monotonic (is_mono==0); bystander dims (is_joined==0) never cause rejection. Models the gold hunk `for dim in concatenated.dims: if dim in concatenated:` -> `for dim in concat_dims:` at xarray/core/combine.py:503.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ATTACKER-3 (leakage / gold-reconstruction), pydata__xarray-3151 / nagini. Measured, not inherited.

**NO RELAXATION IN THIS BUNDLE.** There is no `RELAXED_LEAKAGE.md` and no `relaxed_leakage` key in meta.json (grepped the whole instance dir for both: no hits; walked every meta.json key for /relax|leak/i and the only hit is gates.G-LEAK). So this is a plain strict-mode leakage judgement, and no unavoidability argument needs to be re-derived. I also ran leakage.reviewer_directed() over every text file in the bundle (model.py, model_prepatch.py, mapping.md, refinement.md, verdict.md, properties.py, axiom_check.py, conformance_check.py, meta.json): all clean on all four rules (addresses-the-reviewer, prescribes-the-verdict x2, recording-convention). Nothing in the bundle addresses me or tells me which verdict to record.

WHAT I COMPUTED (spec view, not the record's assertion): markers.spec_view(model.py, backend('nagini')) rendered myself to spec_view.py. It is idempotent (spec_view(spec_view)==spec_view), the impl region collapses to `...  # implementation elided`, and all Invariant(...) lines are gone. `adversary same-spec nagini pydata__xarray-3151` on the bundle model rc=0, so the region I analyzed is the frozen spec. `scripts/nagini_verify.sh model.py` -> "Verification successful" 18.82s rc=0 (spec is live/non-vacuous; MustTerminate(2) present in preconditions).

**GOLD EDIT:** xarray/core/combine.py combine_by_coords monotonicity guard, `for dim in concatenated.dims: if dim in concatenated:` -> `for dim in concat_dims:` (only dims actually concatenated along are monotonicity-checked).

**DISCRIMINATOR IS ALREADY PUBLIC.** The problem_statement itself quotes the docstring promise -- "Non-coordinate dimensions will be ignored, as will any coordinate dimensions which do not vary between each dataset" -- states that identical coordinate dimensions are nonetheless still required to be monotonic, and gives Expected Output "combine_by_coords should return without error" for yCoord=['a','c','b']. That is exactly the spec view's contract (dims whose coordinate did not vary between inputs are exempt from the guard; joined dims must be monotonic). So the facet is derivable from the public statement with no bundle access; no relaxation is even needed here.

MECHANISM/REPO-LEVEL DETAIL IS ABSENT FROM THE SPEC VIEW (token probes over the rendered view): concat_dims=absent, concatenated.dims=absent, `dim in concatenated`=absent, is_monotonic_increasing/decreasing=absent, combine_by_coords=absent, ValueError=absent, "global indexes"=absent, `for dim`=absent, combine.py / any repo path=absent, Dataset/pandas/Index=absent. (`concatenated` appears only as the English participle in "the datasets were concatenated along this dimension"; `raise` only in the MustTerminate rationale "so the caller can raise or proceed".) The pre-patch code shape and the "change the loop target" mechanism live only in mapping.md/refinement.md, which are audit-side docs outside the consumer spec view.

MACHINE SCREEN, RE-RUN LIVE: leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. All 9 distinct gold changed lines checked normalized against the view: 0 reproduced (longest, 53 chars, absent). Diff markers: none. Narration vocabulary (`_NARRATION_RE`): none -- notable given my prior on measure comments tripping "fixed"/"copy"; this bundle's MustTerminate justification is worded clear of it. Spec-view identifier set vs patch changed symbols ({combine_by_coords}): 0 collisions; the only non-Nagini identifiers are guard_rejects / any_joined_nonmonotonic / is_joined / is_mono / is_monotonic / head_violates, all model-side names, none echoing a patched repo symbol. is_joined/is_monotonic parallel 0/1 List[int] flags are a Nagini type-refinement carrier (rich Dataset/pandas.Index/str dim names are unusable), not a disclosure of the edit.

PROVENANCE CAVEAT (recorded, not a leakage finding): meta.json's region_hashes are STALE relative to the current model.py -- computed spec_view hash 03d5cb5e...ffb vs meta dafd91c7...540b7; pre-conditions/invariants/impl/spec_view all mismatch (axioms/pure/post-conditions match), consistent with the MustTerminate obligation being added after the hashes were stamped (G-LEAK checked_at 2026-08-05T02:49Z predates model.py mtime 22:12). So the recorded G-LEAK "spec view clean" pass does not describe the current file. I did not rely on it: the screen above was re-run against the current bytes and passes, and the verifier was re-run against the current bytes and succeeds. Worth flagging to whoever re-stamps meta.json, but it moves no leakage verdict.

**CONCLUSION:** the spec view discloses only the behavioral contract that the public problem_statement already states verbatim (non-varying coordinate dims exempt from the global monotonicity guard), and names no repo symbol, path, pre-patch shape, or loop-target mechanism of the gold edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
