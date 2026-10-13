# P2 adversarial audit — sympy__sympy-12481

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `model_orig.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -90,70 +88,21 @@
                    [[ToSeq(Result())[i]]])))
     # post-conditions-end
     # impl-start
-    # Build the identity array 0..n-1 (the points in their original order).
     result = []  # type: List[int]
     j = 0
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n)
         Invariant(len(result) == j)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
-        Assert(ToSeq(result) == old_seq + PSeq(j))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[j] == j)
         j = j + 1
-    # Apply the first swap (a b) point-wise, then the second swap (c d).
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev = ToSeq(result)  # type: PSeq[int]
-        result[i] = swap_val(i, a, b)
-        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
+        result[i] = swap_val(swap_val(i, c, d), a, b)
         i = i + 1
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
-        i = i + 1
-    return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -90,70 +88,28 @@
                    [[ToSeq(Result())[i]]])))
     # post-conditions-end
     # impl-start
-    # Build the identity array 0..n-1 (the points in their original order).
     result = []  # type: List[int]
     j = 0
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n)
         Invariant(len(result) == j)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
-        Assert(ToSeq(result) == old_seq + PSeq(j))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[j] == j)
         j = j + 1
-    # Apply the first swap (a b) point-wise, then the second swap (c d).
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev = ToSeq(result)  # type: PSeq[int]
         result[i] = swap_val(i, a, b)
-        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
         i = i + 1
     i = 0
-    while i < n:
-        # invariants-start
+    while i < n - 1:
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
+        result[i] = swap_val(result[i], c, d)
         i = i + 1
-    return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -90,70 +88,29 @@
                    [[ToSeq(Result())[i]]])))
     # post-conditions-end
     # impl-start
-    # Build the identity array 0..n-1 (the points in their original order).
     result = []  # type: List[int]
     j = 0
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n)
         Invariant(len(result) == j)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
-        Assert(ToSeq(result) == old_seq + PSeq(j))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[j] == j)
         j = j + 1
-    # Apply the first swap (a b) point-wise, then the second swap (c d).
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev = ToSeq(result)  # type: PSeq[int]
         result[i] = swap_val(i, a, b)
-        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
         i = i + 1
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
-        i = i + 1
-    return result
+    if a != c and a != d and b != c and b != d:
+        i = 0
+        while i < n:
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= n)
+            Invariant(len(result) == n)
+            result[i] = swap_val(result[i], c, d)
+            i = i + 1
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -90,70 +88,14 @@
                    [[ToSeq(Result())[i]]])))
     # post-conditions-end
     # impl-start
-    # Build the identity array 0..n-1 (the points in their original order).
     result = []  # type: List[int]
     j = 0
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n)
         Invariant(len(result) == j)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
-        Assert(ToSeq(result) == old_seq + PSeq(j))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[j] == j)
         j = j + 1
-    # Apply the first swap (a b) point-wise, then the second swap (c d).
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev = ToSeq(result)  # type: PSeq[int]
-        result[i] = swap_val(i, a, b)
-        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        i = i + 1
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
-        i = i + 1
-    return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -90,70 +88,21 @@
                    [[ToSeq(Result())[i]]])))
     # post-conditions-end
     # impl-start
-    # Build the identity array 0..n-1 (the points in their original order).
     result = []  # type: List[int]
     j = 0
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n)
         Invariant(len(result) == j)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
-        Assert(ToSeq(result) == old_seq + PSeq(j))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[j] == j)
         j = j + 1
-    # Apply the first swap (a b) point-wise, then the second swap (c d).
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev = ToSeq(result)  # type: PSeq[int]
-        result[i] = swap_val(i, a, b)
-        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
+        result[i] = swap_val(swap_val(i, a, d), c, b)
         i = i + 1
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
-        i = i + 1
-    return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -90,70 +88,19 @@
                    [[ToSeq(Result())[i]]])))
     # post-conditions-end
     # impl-start
-    # Build the identity array 0..n-1 (the points in their original order).
     result = []  # type: List[int]
     j = 0
-    while j < n:
-        # invariants-start
+    while j < n + 1:
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n)
+        Invariant(0 <= j and j <= n + 1)
         Invariant(len(result) == j)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
-        Assert(ToSeq(result) == old_seq + PSeq(j))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[j] == j)
         j = j + 1
-    # Apply the first swap (a b) point-wise, then the second swap (c d).
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev = ToSeq(result)  # type: PSeq[int]
-        result[i] = swap_val(i, a, b)
-        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
+        Invariant(len(result) == n + 1)
+        result[i] = swap_val(swap_val(i, a, b), c, d)
         i = i + 1
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
-        i = i + 1
-    return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -90,70 +88,21 @@
                    [[ToSeq(Result())[i]]])))
     # post-conditions-end
     # impl-start
-    # Build the identity array 0..n-1 (the points in their original order).
     result = []  # type: List[int]
     j = 0
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n)
         Invariant(len(result) == j)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
-        # invariants-end
-        old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
-        Assert(ToSeq(result) == old_seq + PSeq(j))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
-                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[j] == j)
         j = j + 1
-    # Apply the first swap (a b) point-wise, then the second swap (c d).
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n)
         Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev = ToSeq(result)  # type: PSeq[int]
         result[i] = swap_val(i, a, b)
-        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
         i = i + 1
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
-        i = i + 1
-    return result
     # impl-end
```

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     # repetition is excluded.
     Requires(a != b)
     Requires(c != d)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -100,7 +98,6 @@
         Invariant(len(result) == j)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - j + 1))
         # invariants-end
         old_seq = ToSeq(result)  # type: PSeq[int]
         result.append(j)
@@ -121,7 +118,6 @@
                        [[ToSeq(result)[k]]])))
         Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                        ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         prev = ToSeq(result)  # type: PSeq[int]
         result[i] = swap_val(i, a, b)
@@ -130,30 +126,32 @@
                       ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
         Assert(ToSeq(result)[i] == swap_val(i, a, b))
         i = i + 1
-    i = 0
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n)
-        Invariant(len(result) == n)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
-                       ToSeq(result)[k] == swap_val(k, a, b)),
-                       [[ToSeq(result)[k]]])))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        prev2 = ToSeq(result)  # type: PSeq[int]
-        Assert(ToSeq(result)[i] == swap_val(i, a, b))
-        Assert(result[i] == swap_val(i, a, b))
-        new_val = swap_val(result[i], c, d)  # type: int
-        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
-        result[i] = new_val
-        Assert(ToSeq(result) == prev2.update(i, new_val))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
-                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
-        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
-        i = i + 1
+    # Two cycles that share a point are non-disjoint; apply the second swap
+    # only for disjoint cycles, leaving sharing cycles uncomposed.
+    if not (a == c or a == d or b == c or b == d):
+        i = 0
+        while i < n:
+            # invariants-start
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= n)
+            Invariant(len(result) == n)
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                           ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
+                           [[ToSeq(result)[k]]])))
+            Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
+                           ToSeq(result)[k] == swap_val(k, a, b)),
+                           [[ToSeq(result)[k]]])))
+            # invariants-end
+            prev2 = ToSeq(result)  # type: PSeq[int]
+            Assert(ToSeq(result)[i] == swap_val(i, a, b))
+            Assert(result[i] == swap_val(i, a, b))
+            new_val = swap_val(result[i], c, d)  # type: int
+            Assert(new_val == swap_val(swap_val(i, a, b), c, d))
+            result[i] = new_val
+            Assert(ToSeq(result) == prev2.update(i, new_val))
+            Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
+                          ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
+            Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
+            i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_orig.py`

```python
"""Twin-artifact model for sympy__sympy-12481.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite arrangement is described in cyclic form by a sequence of cycles
  over the points 0..n-1. The arrangement these cycles denote is their
  composition applied in LEFT-TO-RIGHT order: the first cycle acts first, the
  next acts on that outcome, and so on. The points NOT named keep their place.

  This composition is well defined for ANY collection of cycles, including
  cycles that share points (non-disjoint cycles): two cycles that touch a
  common point compose into a single arrangement just as disjoint ones do, and
  the resulting arrangement is still a genuine one-to-one rearrangement of
  0..n-1. There is therefore no input of two cycles for which the construction
  is undefined; every such input yields a rearrangement.

  This module specifies the building of the two-line "array form": position i
  of the result is the point that 0..n-1's i-th point is sent to after both
  cycles have acted in order. The smallest two-element cycles (point swaps)
  carry the whole content of the composition, so the construction is modelled
  over a pair of point-swaps `(a b)` then `(c d)` acting on the n points.

Each cycle here is a two-element swap on integer points; the carrier is the
array form as a `List[int]`, and the specification is phrased over `PSeq[int]`
of points via `ToSeq`. Strings are not involved.

The whole computation is modelled DEEPLY (the per-point swap is spelled out as
a verified loop, not hidden behind an axiom); its equality to the real cycle
composition is checked out-of-band by axiom_check.py (G-AX). There is no
consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none) — the composition is modelled deeply; no callee is axiomatized.
# axioms-end

# pure-start
@Pure
def swap_val(x: int, a: int, b: int) -> int:
    """Image of point x under the swap (a b): a and b trade places, every
    other point keeps its value."""
    if x == a:
        return b
    if x == b:
        return a
    return x

# pure-end

def compose_cycles(n: int, a: int, b: int, c: int, d: int) -> List[int]:
    """Array form of the composition of the swap (a b) then the swap (c d) over
    the n points 0..n-1, applied left to right."""
    # pre-conditions-start
    Requires(n >= 1)
    Requires(0 <= a and a < n)
    Requires(0 <= b and b < n)
    Requires(0 <= c and c < n)
    Requires(0 <= d and d < n)
    # Each cycle names two DISTINCT points: a point may not appear twice within
    # one cycle.  The two cycles MAY share a point with each other (that is the
    # non-disjoint case this construction must accept); only within-cycle
    # repetition is excluded.
    Requires(a != b)
    Requires(c != d)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    # Position i holds the point that i is sent to after (a b) then (c d) act,
    # i.e. the left-to-right composition.  This is defined for EVERY (a,b,c,d),
    # disjoint or not: there is no rejected input.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                   ToSeq(Result())[i] == swap_val(swap_val(i, a, b), c, d)),
                   [[ToSeq(Result())[i]]])))
    # The result is a genuine rearrangement: every position holds a point in
    # range, so the clause above cannot be met by a degenerate
    # (e.g. rejection-sentinel) array.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                   0 <= ToSeq(Result())[i] and ToSeq(Result())[i] < n),
                   [[ToSeq(Result())[i]]])))
    # post-conditions-end
    # impl-start
    # Build the identity array 0..n-1 (the points in their original order).
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        result.append(j)
        Assert(ToSeq(result) == old_seq + PSeq(j))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == j)
        j = j + 1
    # Apply the first swap (a b) point-wise, then the second swap (c d).
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        # invariants-end
        prev = ToSeq(result)  # type: PSeq[int]
        result[i] = swap_val(i, a, b)
        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        i = i + 1
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        # invariants-end
        prev2 = ToSeq(result)  # type: PSeq[int]
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        Assert(result[i] == swap_val(i, a, b))
        new_val = swap_val(result[i], c, d)  # type: int
        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
        result[i] = new_val
        Assert(ToSeq(result) == prev2.update(i, new_val))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The FROZEN spec is FULLY FUNCTIONAL: compose_cycles' postcondition pins each output element EXACTLY -- Ensures(Forall i<n: ToSeq(Result())[i] == swap_val(swap_val(i,a,b),c,d)) plus len(Result())==n and an in-range clause. The output array is therefore uniquely determined for every Requires-admitted input (n>=1, 0<=a,b,c,d<n, a!=b, c!=d). Any impl that verifies must compute the identical left-to-right composition of (a b) then (c d), so no verifying wrong impl exists -> verify=>correct. No CANDIDATE was produced besides the correct positive control, hence there is NO faithful refined patch to materialize/resolve (nothing to break the spec).

PROTOCOL EXECUTED (project root, env swebench-lean, SBU_BENCHMARK_DIR=benchmark-verified). All attacks confirmed same-spec (byte-identical spec signature) via `adversary same-spec`, then run through `adversary weakness nagini sympy__sympy-12481 <file>` (each spawns JVM+Z3; run <=3 concurrently across 3 batches).

### Results
- positive_control model_orig.py: weakness => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 17.0s) -> the correct impl verifies. exit 0.
- atk_prepatch.py (the real prepatch bug: applies 2nd swap only when the two cycles are disjoint, leaving non-disjoint inputs uncomposed): weakness => NOT-A-COUNTEREXAMPLE, verification failed (fails the total postcondition on non-disjoint inputs). Prepatch bug REPRODUCED. exit 2.
- atk_1.py control-flow-effect (reversed composition order swap_val(swap_val(i,c,d),a,b)): rejected (does not verify). exit 2.
- atk_2.py boundary/off-by-one (3rd loop stops at n-1, last element left half-composed): rejected. exit 2.
- atk_3.py partial-domain (apply 2nd swap only when a!=c&&a!=d&&b!=c&&b!=d, i.e. disjoint-only, differently phrased than prepatch): rejected. exit 2.
- atk_4.py ungrounded/constant (return the identity array, skip both swaps): rejected. exit 2.
- atk_5.py mislabel (compose (a d) then (c b) instead of (a b) then (c d)): rejected. exit 2.
- atk_6.py length-defect (build n+1 identity entries; len(Result())!=n): rejected. exit 2.
- atk_7.py drop-second-cycle (apply only the first swap (a b)): rejected. exit 2.

So across 8 distinct wrong impls (partial-domain, boundary, control-flow-effect, order-swap, ungrounded, length, drop-cycle, plus the exact prepatch bug) NONE verifies; only the correct control does. patches={} because no wrong impl became a CANDIDATE, so no faithful patch materialization/run_resolve was required.

REFINEMENT.MD LEG AUDIT (A-focus, R/I mechanically covered by G-CONF): A1=R (model domain a!=b&&c!=d == real callee accepting set; only cross-cycle non-disjoint rejection removed, within-cycle uniqueness untouched) SOUND; A2 = I (removed control edge) + spec encoding of its absence via a TOTAL postcondition SOUND; A3 = A-reference (deep swap_val + verified loops == real Permutation([[a,b],[c,d]],size=n).array_form, validated by axiom_check.py over exhaustive n<=6 (1484 genuine-cycle cases) + 20000 fuzz + the 3 problem/F2P witnesses incl. every non-disjoint shared-point configuration; domain-congruence asserted) SOUND; A4 = R (array form <-> _array_form) SOUND.

NO kind-3 (unexpressible-changed-op) legs; NO consumed @ContractOnly axiom (the Cycle machinery the branch calls is unchanged and appears only as the A-reference G-AX validates against). The singleton F2P-removed witness [[1],[1,2]] is correctly OUTSIDE compose_cycles' two-genuine-swap domain and is handled by axiom_check.py's faithful single_then_swap model -> the model does not unfaithfully encode [1,1]. Independently reconfirmed numerically: model([[0,1],[0,2]],n=3)=[1,2,0]=(0 1 2); model([[0,1],[0,1]],n=2)=[0,1]; bijection holds for all genuine cycles n<=6 (0 non-bijections).

Verdict SOUND: >=5 distinct same-spec wrong impls (8 here) all run through the official weakness check, none verifies, positive control verifies, prepatch reproduced; refinement legs are all R/A-reference/I with holding correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `model_orig.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_orig.py`

```python
"""Twin-artifact model for sympy__sympy-12481.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite arrangement is described in cyclic form by a sequence of cycles
  over the points 0..n-1. The arrangement these cycles denote is their
  composition applied in LEFT-TO-RIGHT order: the first cycle acts first, the
  next acts on that outcome, and so on. The points NOT named keep their place.

  This composition is well defined for ANY collection of cycles, including
  cycles that share points (non-disjoint cycles): two cycles that touch a
  common point compose into a single arrangement just as disjoint ones do, and
  the resulting arrangement is still a genuine one-to-one rearrangement of
  0..n-1. There is therefore no input of two cycles for which the construction
  is undefined; every such input yields a rearrangement.

  This module specifies the building of the two-line "array form": position i
  of the result is the point that 0..n-1's i-th point is sent to after both
  cycles have acted in order. The smallest two-element cycles (point swaps)
  carry the whole content of the composition, so the construction is modelled
  over a pair of point-swaps `(a b)` then `(c d)` acting on the n points.

Each cycle here is a two-element swap on integer points; the carrier is the
array form as a `List[int]`, and the specification is phrased over `PSeq[int]`
of points via `ToSeq`. Strings are not involved.

The whole computation is modelled DEEPLY (the per-point swap is spelled out as
a verified loop, not hidden behind an axiom); its equality to the real cycle
composition is checked out-of-band by axiom_check.py (G-AX). There is no
consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none) — the composition is modelled deeply; no callee is axiomatized.
# axioms-end

# pure-start
@Pure
def swap_val(x: int, a: int, b: int) -> int:
    """Image of point x under the swap (a b): a and b trade places, every
    other point keeps its value."""
    if x == a:
        return b
    if x == b:
        return a
    return x

# pure-end

def compose_cycles(n: int, a: int, b: int, c: int, d: int) -> List[int]:
    """Array form of the composition of the swap (a b) then the swap (c d) over
    the n points 0..n-1, applied left to right."""
    # pre-conditions-start
    Requires(n >= 1)
    Requires(0 <= a and a < n)
    Requires(0 <= b and b < n)
    Requires(0 <= c and c < n)
    Requires(0 <= d and d < n)
    # Each cycle names two DISTINCT points: a point may not appear twice within
    # one cycle.  The two cycles MAY share a point with each other (that is the
    # non-disjoint case this construction must accept); only within-cycle
    # repetition is excluded.
    Requires(a != b)
    Requires(c != d)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    # Position i holds the point that i is sent to after (a b) then (c d) act,
    # i.e. the left-to-right composition.  This is defined for EVERY (a,b,c,d),
    # disjoint or not: there is no rejected input.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                   ToSeq(Result())[i] == swap_val(swap_val(i, a, b), c, d)),
                   [[ToSeq(Result())[i]]])))
    # The result is a genuine rearrangement: every position holds a point in
    # range, so the clause above cannot be met by a degenerate
    # (e.g. rejection-sentinel) array.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                   0 <= ToSeq(Result())[i] and ToSeq(Result())[i] < n),
                   [[ToSeq(Result())[i]]])))
    # post-conditions-end
    # impl-start
    # Build the identity array 0..n-1 (the points in their original order).
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        result.append(j)
        Assert(ToSeq(result) == old_seq + PSeq(j))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == j)
        j = j + 1
    # Apply the first swap (a b) point-wise, then the second swap (c d).
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        # invariants-end
        prev = ToSeq(result)  # type: PSeq[int]
        result[i] = swap_val(i, a, b)
        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        i = i + 1
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        # invariants-end
        prev2 = ToSeq(result)  # type: PSeq[int]
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        Assert(result[i] == swap_val(i, a, b))
        new_val = swap_val(result[i], c, d)  # type: int
        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
        result[i] = new_val
        Assert(ToSeq(result) == prev2.update(i, new_val))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The FROZEN spec is FULLY FUNCTIONAL: compose_cycles' postcondition pins each output element EXACTLY -- Ensures(Forall i<n: ToSeq(Result())[i] == swap_val(swap_val(i,a,b),c,d)) plus len(Result())==n and an in-range clause. The output array is therefore uniquely determined for every Requires-admitted input (n>=1, 0<=a,b,c,d<n, a!=b, c!=d). Any impl that verifies must compute the identical left-to-right composition of (a b) then (c d), so no verifying wrong impl exists -> verify=>correct. No CANDIDATE was produced besides the correct positive control, hence there is NO faithful refined patch to materialize/resolve (nothing to break the spec).

PROTOCOL EXECUTED (project root, env swebench-lean, SBU_BENCHMARK_DIR=benchmark-verified). All attacks confirmed same-spec (byte-identical spec signature) via `adversary same-spec`, then run through `adversary weakness nagini sympy__sympy-12481 <file>` (each spawns JVM+Z3; run <=3 concurrently across 3 batches).

### Results
- positive_control model_orig.py: weakness => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 17.0s) -> the correct impl verifies. exit 0.
- atk_prepatch.py (the real prepatch bug: applies 2nd swap only when the two cycles are disjoint, leaving non-disjoint inputs uncomposed): weakness => NOT-A-COUNTEREXAMPLE, verification failed (fails the total postcondition on non-disjoint inputs). Prepatch bug REPRODUCED. exit 2.
- atk_1.py control-flow-effect (reversed composition order swap_val(swap_val(i,c,d),a,b)): rejected (does not verify). exit 2.
- atk_2.py boundary/off-by-one (3rd loop stops at n-1, last element left half-composed): rejected. exit 2.
- atk_3.py partial-domain (apply 2nd swap only when a!=c&&a!=d&&b!=c&&b!=d, i.e. disjoint-only, differently phrased than prepatch): rejected. exit 2.
- atk_4.py ungrounded/constant (return the identity array, skip both swaps): rejected. exit 2.
- atk_5.py mislabel (compose (a d) then (c b) instead of (a b) then (c d)): rejected. exit 2.
- atk_6.py length-defect (build n+1 identity entries; len(Result())!=n): rejected. exit 2.
- atk_7.py drop-second-cycle (apply only the first swap (a b)): rejected. exit 2.

So across 8 distinct wrong impls (partial-domain, boundary, control-flow-effect, order-swap, ungrounded, length, drop-cycle, plus the exact prepatch bug) NONE verifies; only the correct control does. patches={} because no wrong impl became a CANDIDATE, so no faithful patch materialization/run_resolve was required.

REFINEMENT.MD LEG AUDIT (A-focus, R/I mechanically covered by G-CONF): A1=R (model domain a!=b&&c!=d == real callee accepting set; only cross-cycle non-disjoint rejection removed, within-cycle uniqueness untouched) SOUND; A2 = I (removed control edge) + spec encoding of its absence via a TOTAL postcondition SOUND; A3 = A-reference (deep swap_val + verified loops == real Permutation([[a,b],[c,d]],size=n).array_form, validated by axiom_check.py over exhaustive n<=6 (1484 genuine-cycle cases) + 20000 fuzz + the 3 problem/F2P witnesses incl. every non-disjoint shared-point configuration; domain-congruence asserted) SOUND; A4 = R (array form <-> _array_form) SOUND.

NO kind-3 (unexpressible-changed-op) legs; NO consumed @ContractOnly axiom (the Cycle machinery the branch calls is unchanged and appears only as the A-reference G-AX validates against). The singleton F2P-removed witness [[1],[1,2]] is correctly OUTSIDE compose_cycles' two-genuine-swap domain and is handled by axiom_check.py's faithful single_then_swap model -> the model does not unfaithfully encode [1,1]. Independently reconfirmed numerically: model([[0,1],[0,2]],n=3)=[1,2,0]=(0 1 2); model([[0,1],[0,1]],n=2)=[0,1]; bijection holds for all genuine cycles n<=6 (0 non-bijections).

Verdict SOUND: >=5 distinct same-spec wrong impls (8 here) all run through the official weakness check, none verifies, positive control verifies, prepatch reproduced; refinement legs are all R/A-reference/I with holding correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 faithfulness check for sympy__sympy-12481 (nagini). The modeled function compose_cycles(n,a,b,c,d) claims: for every input in its Requires domain (n>=1, 0<=a,b,c,d<n, a!=b, c!=d), result[i] == swap_val(swap_val(i,a,b),c,d), the result is an in-range permutation of 0..n-1, and no input is rejected. I checked this against the REAL patched repo callee Permutation([[a,b],[c,d]], size=n).array_form (verified has the gold hunk applied: `if has_dups and not is_cycle: raise`, i.e. the is_cycle duplicate rejection removed). Results: exhaustive over all (n,a,b,c,d) with a!=b,c!=d for n in 1..7 (3248 cases) => 0 mismatches, 0 in-domain raises; plus 200000 randomized fuzz cases (n up to 60, incl. shared-point/non-disjoint configs) => 0 mismatches, 0 raises. Domain congruence holds: no input the model's Requires admits is rejected by the real callee, so the spec is not too STRONG (it does not over-claim a wider accepting domain). The postcondition (left-to-right composition of the two swaps) exactly reproduces the real Cycle-composition array form on every tested input. The spec domain (a!=b AND c!=d) correctly excludes the within-cycle-repeat inputs [e,e] that the real callee still rejects post-patch, so it does not falsely claim behavior on rejected inputs either. No diverging input found; the modeled function agrees with the real callee. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py projection (docstring + swap_val pure region + compose_cycles contracts, impl elided). Mechanical G-LEAK screen (swebench_unified.leakage.screen) PASSES: no diff markers, no reproduced gold-patch line (>=8 chars normalized), no patched file path (sympy/combinatorics/permutations.py absent) or dotted module path, no spec-view identifier/comment naming a patched repo symbol (has_dups, is_cycle, flatten, the duplicate-elements ValueError guard), no bug/fix narration. Semantic check vs SOLVER-VISIBLE problem_statement (hints_text empty): the problem statement already publicly discloses the full desired behavior -- non-disjoint cycles should be accepted, applied in LEFT-TO-RIGHT order, and the resulting permutation returned (Permutation([[0,1],[0,1]]) builds the identity). The spec view states exactly that desired end-state (left-to-right composition, well-defined for non-disjoint/shared-point cycles, no rejected input, result is a genuine bijection) -- all already public. It does NOT reveal the gold EDIT MECHANISM (removing the is_cycle arm of the has_dups guard). The swap_val / array-form / pair-of-two-element-swaps framing is a specification abstraction/modeling choice, not a pointer to the guard-removal fix. The verbatim gold-patch quotes appear only in refinement.md and mapping.md, which are audit-derivation documents, NOT the solver-visible spec view that G-PANEL-3 screens. same-spec self-check exit 0 (spec region byte-identical). Conclusion: no spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.