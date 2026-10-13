# P2 adversarial audit — django__django-12039

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -89,47 +87,23 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
-    if len(suffix) > 0:
-        result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
-        k = 0
-        while k < len(suffix):
-            # invariants-start
-            Invariant(Acc(list_pred(base), 1 / 2))
-            Invariant(Acc(list_pred(suffix), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(len(suffix) > 0)
-            Invariant(0 <= k and k <= len(suffix))
-            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
-            result.append(suffix[k])
-            k = k + 1
-        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
+    k = 0
+    while k < len(suffix):
+        Invariant(Acc(list_pred(base), 1 / 2))
+        Invariant(Acc(list_pred(suffix), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= k and k <= len(suffix))
+        Invariant(ToSeq(result) == ToSeq(base) + ToSeq(suffix).take(k))
+        result.append(suffix[k])
+        k = k + 1
     return result
     # impl-end
 
@@ -140,7 +114,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +141,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -187,7 +159,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -97,7 +95,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -116,7 +113,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
@@ -140,7 +136,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -160,46 +155,23 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
-    if len(suffix) > 0:
-        result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
-        k = 0
-        while k < len(suffix):
-            # invariants-start
-            Invariant(Acc(list_pred(base), 1 / 2))
-            Invariant(Acc(list_pred(suffix), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(len(suffix) > 0)
-            Invariant(0 <= k and k <= len(suffix))
-            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
-            result.append(suffix[k])
-            k = k + 1
-        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
+    result.append(sep())
+    k = 0
+    while k < len(suffix):
+        Invariant(Acc(list_pred(base), 1 / 2))
+        Invariant(Acc(list_pred(suffix), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= k and k <= len(suffix))
+        Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
+        result.append(suffix[k])
+        k = k + 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -89,47 +87,25 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
     if len(suffix) > 0:
-        result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
+        result.append(33)
         k = 0
         while k < len(suffix):
-            # invariants-start
             Invariant(Acc(list_pred(base), 1 / 2))
             Invariant(Acc(list_pred(suffix), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
-            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
+            Invariant(ToSeq(result) == ToSeq(base) + PSeq(33) + ToSeq(suffix).take(k))
             result.append(suffix[k])
             k = k + 1
-        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
     return result
     # impl-end
 
@@ -140,7 +116,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +143,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -187,7 +161,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -89,47 +87,26 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
     if len(suffix) > 0:
         result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
+        result.append(sep())
         k = 0
         while k < len(suffix):
-            # invariants-start
             Invariant(Acc(list_pred(base), 1 / 2))
             Invariant(Acc(list_pred(suffix), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
-            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
+            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + PSeq(sep()) + ToSeq(suffix).take(k))
             result.append(suffix[k])
             k = k + 1
-        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
     return result
     # impl-end
 
@@ -140,7 +117,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +144,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -187,7 +162,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -89,47 +87,25 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
     if len(suffix) > 0:
         result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
         k = 0
-        while k < len(suffix):
-            # invariants-start
+        while k < len(suffix) - 1:
             Invariant(Acc(list_pred(base), 1 / 2))
             Invariant(Acc(list_pred(suffix), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
             result.append(suffix[k])
             k = k + 1
-        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
     return result
     # impl-end
 
@@ -140,7 +116,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +143,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -187,7 +161,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -89,47 +87,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
-    if len(suffix) > 0:
+    if len(suffix) == 0:
         result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
-        k = 0
-        while k < len(suffix):
-            # invariants-start
-            Invariant(Acc(list_pred(base), 1 / 2))
-            Invariant(Acc(list_pred(suffix), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(len(suffix) > 0)
-            Invariant(0 <= k and k <= len(suffix))
-            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
-            result.append(suffix[k])
-            k = k + 1
-        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
     return result
     # impl-end
 
@@ -140,7 +107,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +134,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -187,7 +152,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -89,47 +87,14 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
-    if len(suffix) > 0:
-        result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
-        k = 0
-        while k < len(suffix):
-            # invariants-start
-            Invariant(Acc(list_pred(base), 1 / 2))
-            Invariant(Acc(list_pred(suffix), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(len(suffix) > 0)
-            Invariant(0 <= k and k <= len(suffix))
-            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
-            result.append(suffix[k])
-            k = k + 1
-        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
     return result
     # impl-end
 
@@ -140,7 +105,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +132,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -187,7 +150,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -89,47 +87,28 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # base token
     j = 0
     while j < len(base):
-        # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
-        # invariants-end
         result.append(base[j])
         j = j + 1
     Assert(ToSeq(result) == ToSeq(base))
-    # only append a separator + suffix when the suffix is non-empty
-    Assert(len(ToSeq(suffix)) == len(suffix))
-    if len(suffix) > 0:
+    if len(suffix) != 0:
         result.append(sep())
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
         k = 0
         while k < len(suffix):
-            # invariants-start
             Invariant(Acc(list_pred(base), 1 / 2))
             Invariant(Acc(list_pred(suffix), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
-            # invariants-end
             result.append(suffix[k])
             k = k + 1
         Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
-        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(len(ToSeq(suffix)) == len(suffix))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
-    else:
-        Assert(len(ToSeq(suffix)) == 0)
-        Assert(ToSeq(result) == ToSeq(base))
-        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
-        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
     return result
     # impl-end
 
@@ -140,7 +119,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(suffix), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +146,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(base))
         Invariant(ToSeq(result) == ToSeq(base).take(j))
-        Invariant(MustTerminate(len(base) - j + 1))
         # invariants-end
         result.append(base[j])
         j = j + 1
@@ -187,7 +164,6 @@
             Invariant(len(suffix) > 0)
             Invariant(0 <= k and k <= len(suffix))
             Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
-            Invariant(MustTerminate(len(suffix) - k + 1))
             # invariants-end
             result.append(suffix[k])
             k = k + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12039.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A column reference is rendered as a piece of DDL text by joining a base token
  (the quoted column, optionally already carrying a trailing operator-class
  keyword) with an optional ordering suffix. The ordering suffix is a string
  that is EITHER empty (the default, ascending order) OR a non-empty keyword
  (e.g. the descending-order keyword).

  The desired join behaviour:

    * When the suffix is non-empty, the rendered text is the base token, then a
      single separating space, then the suffix — so the suffix keyword is set
      off from the base token by exactly one space and never fuses with the
      last base code point.

    * When the suffix is empty, the rendered text is the base token EXACTLY:
      no separator and no trailing space are appended.

  Two sites perform this same join. They differ only in their base token:
  one joins the quoted column alone; the other joins the quoted column already
  combined with an operator-class keyword. Both must obey the join behaviour
  above.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The join
is the changed operation and is modelled DEEPLY as the spelled-out conditional
concatenation (`joined`); there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the rendered text is modelled deeply as a conditional
#  concatenation of expressible pieces. The base token of each site is an
#  opaque already-assembled code-point list — the quoted column, or the quoted
#  column already combined with an operator-class keyword — passed in as input.)
# axioms-end


# pure-start
@Pure
def sep() -> int:
    """The separator code point placed between the base token and a non-empty
    suffix (a single space, U+0020)."""
    return 32


@Pure
def joined(base: PSeq[int], suffix: PSeq[int]) -> PSeq[int]:
    """The rendered text for one column reference: the base token joined with
    the ordering suffix. A non-empty suffix is set off by exactly one separator
    space; an empty suffix contributes nothing (the base token is returned
    unchanged, with no trailing separator)."""
    if len(suffix) == 0:
        return base
    return base + PSeq(32) + suffix
# pure-end


def render_column(base: List[int], suffix: List[int]) -> List[int]:
    """Site 1: the base token is the quoted column alone."""
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(suffix), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(suffix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text is the deep conditional concatenation.
    Ensures(ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)))
    # When the suffix is empty, the result is the base token exactly: no
    # trailing separator, same length as the base.
    Ensures(Implies(len(suffix) == 0, ToSeq(Result()) == ToSeq(base)))
    # When the suffix is non-empty, the base token is preserved as a prefix and
    # the code point that immediately follows it is the separator space (so the
    # suffix keyword never fuses with the last base code point).
    Ensures(Implies(len(suffix) > 0, ToSeq(Result()).take(len(base)) == ToSeq(base)))
    Ensures(Implies(len(suffix) > 0, ToSeq(Result())[len(base)] == sep()))
    Ensures(Implies(len(suffix) > 0,
                    ToSeq(Result()).drop(len(base) + 1) == ToSeq(suffix)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # only append a separator + suffix when the suffix is non-empty
    Assert(len(ToSeq(suffix)) == len(suffix))
    if len(suffix) > 0:
        result.append(sep())
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
        k = 0
        while k < len(suffix):
            # invariants-start
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(suffix), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(suffix) > 0)
            Invariant(0 <= k and k <= len(suffix))
            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
            # invariants-end
            result.append(suffix[k])
            k = k + 1
        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(len(ToSeq(suffix)) == len(suffix))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    else:
        Assert(len(ToSeq(suffix)) == 0)
        Assert(ToSeq(result) == ToSeq(base))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    return result
    # impl-end


def render_column_with_opclass(base: List[int], suffix: List[int]) -> List[int]:
    """Site 2: the base token is the quoted column already combined with an
    operator-class keyword. The join behaviour is identical to site 1."""
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(suffix), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(suffix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text is the deep conditional concatenation.
    Ensures(ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)))
    # When the suffix is empty, the result is the base token exactly: no
    # trailing separator, same length as the base.
    Ensures(Implies(len(suffix) == 0, ToSeq(Result()) == ToSeq(base)))
    # When the suffix is non-empty, the base token is preserved as a prefix and
    # the code point that immediately follows it is the separator space.
    Ensures(Implies(len(suffix) > 0, ToSeq(Result()).take(len(base)) == ToSeq(base)))
    Ensures(Implies(len(suffix) > 0, ToSeq(Result())[len(base)] == sep()))
    Ensures(Implies(len(suffix) > 0,
                    ToSeq(Result()).drop(len(base) + 1) == ToSeq(suffix)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # only append a separator + suffix when the suffix is non-empty
    Assert(len(ToSeq(suffix)) == len(suffix))
    if len(suffix) > 0:
        result.append(sep())
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
        k = 0
        while k < len(suffix):
            # invariants-start
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(suffix), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(suffix) > 0)
            Invariant(0 <= k and k <= len(suffix))
            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
            # invariants-end
            result.append(suffix[k])
            k = k + 1
        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(len(ToSeq(suffix)) == len(suffix))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    else:
        Assert(len(ToSeq(suffix)) == 0)
        Assert(ToSeq(result) == ToSeq(base))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A COMPLETE FUNCTIONAL EQUALITY. Both render_column (site 1) and render_column_with_opclass (site 2) carry the postcondition ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)) UNCONDITIONALLY over the entire Requires-satisfying domain (Requires asks only for read access to the two lists; no domain restriction is possible), plus the empty/non-empty structural clauses. This pins any verifying impl to the exact gold behaviour, so verify=>correct.

A-LEG AUDIT (the only non-R/I legs). refinement.md leg A4/B4 is the sole A-reference: joined == real col_str join; there are NO consumed axioms (no @ContractOnly) and NO kind-3 (unexpressible-changed-op) legs. Ran axiom_check.py (G-AX): PASS -- 'deep model joined == real col_str join on 32 boundary + 20000 fuzz inputs (both sites); empty suffix leaves no trailing space and a non-empty suffix is space-separated (no fusion).' real_join in axiom_check faithfully reproduces the gold col_str join at both sites (col=base; if suffix: col='{} {}'.format(col,suffix)), matching mapping.md sec 3.1 and patch.diff. Model<->patch correspondence (A1-A5,B1-B5) holds: base=quote_name(column) / '{} {}'.format(quote_name,opclass) upstream input; suffix=col_suffixes[idx]; join deep-modelled; every remaining leg is R (str<->List[int]) or I. G-CONF conformance_check.py cross-checks the contract-stripped impl vs the REAL patched Columns/IndexColumns.__str__ over >=1e5 inputs.

POSITIVE CONTROL: pos_control.py (= gold model.py) verifies, exit 0, 18.2s.

atk_1 (site1 prepatch: direct concat, NO separator, unconditional): weakness exit 2 -- verification FAILED (spec rejected). Prepatch bug reproduced.
- atk_2 (site2 prepatch2: append sep+suffix UNCONDITIONALLY -> trailing space for empty suffix): exit 2 -- FAILED. Second prepatch bug reproduced.
- atk_3 (wrong separator code point 33 '!' instead of 32): exit 2 -- FAILED (boundary/oracle).
- atk_4 (double separator for non-empty suffix): exit 2 -- FAILED.
- atk_5 (off-by-one: while k < len(suffix)-1, drops last suffix char): exit 2 -- FAILED (boundary).
- atk_6 (inverted guard / control-flow-effect: append sep only when suffix EMPTY): exit 2 -- FAILED.
- atk_7 (partial-domain / ungrounded echo: ignore suffix, always return base): exit 2 -- FAILED.
- atk_8 (restructured-correct echo: 'if len(suffix) != 0' <=> 'if suffix'; site 2 gold-verbatim): weakness exit 0 -- CANDIDATE (shares spec AND verifies).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE. atk_8 is behaviourally identical to gold at both sites, so its faithful refined patch is the gold patch. Materialized it (atk_8_faithful.patch) and RAN the official harness via swebench_unified.harness.run_resolve('django__django-12039', patch): resolved=True, completed=True, note='resolved'. FAIL_TO_PASS test_descending_columns_list_sql PASS; all 11 PASS_TO_PASS PASS; 0 failures. A resolving echo of the gold is NOT a weakness (per unified panel_1/eq policy).

CONCLUSION: every genuinely-wrong impl (partial-domain, boundary, wrong-constant, control-flow-effect, ungrounded-oracle) is rejected by verification; the only verifying candidate resolves under the official harness. No verifying impl exists whose faithful patch fails to resolve. verify=>correct holds. Commands (from project root, SBU_BENCHMARK_DIR=benchmark-verified, interpreter python): `python -m swebench_unified.adversary same-spec|weakness nagini django__django-12039 <atk>`; run_resolve via swebench_unified.harness; `axiom_check.py` direct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12039.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A column reference is rendered as a piece of DDL text by joining a base token
  (the quoted column, optionally already carrying a trailing operator-class
  keyword) with an optional ordering suffix. The ordering suffix is a string
  that is EITHER empty (the default, ascending order) OR a non-empty keyword
  (e.g. the descending-order keyword).

  The desired join behaviour:

    * When the suffix is non-empty, the rendered text is the base token, then a
      single separating space, then the suffix — so the suffix keyword is set
      off from the base token by exactly one space and never fuses with the
      last base code point.

    * When the suffix is empty, the rendered text is the base token EXACTLY:
      no separator and no trailing space are appended.

  Two sites perform this same join. They differ only in their base token:
  one joins the quoted column alone; the other joins the quoted column already
  combined with an operator-class keyword. Both must obey the join behaviour
  above.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The join
is the changed operation and is modelled DEEPLY as the spelled-out conditional
concatenation (`joined`); there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the rendered text is modelled deeply as a conditional
#  concatenation of expressible pieces. The base token of each site is an
#  opaque already-assembled code-point list — the quoted column, or the quoted
#  column already combined with an operator-class keyword — passed in as input.)
# axioms-end


# pure-start
@Pure
def sep() -> int:
    """The separator code point placed between the base token and a non-empty
    suffix (a single space, U+0020)."""
    return 32


@Pure
def joined(base: PSeq[int], suffix: PSeq[int]) -> PSeq[int]:
    """The rendered text for one column reference: the base token joined with
    the ordering suffix. A non-empty suffix is set off by exactly one separator
    space; an empty suffix contributes nothing (the base token is returned
    unchanged, with no trailing separator)."""
    if len(suffix) == 0:
        return base
    return base + PSeq(32) + suffix
# pure-end


def render_column(base: List[int], suffix: List[int]) -> List[int]:
    """Site 1: the base token is the quoted column alone."""
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(suffix), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(suffix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text is the deep conditional concatenation.
    Ensures(ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)))
    # When the suffix is empty, the result is the base token exactly: no
    # trailing separator, same length as the base.
    Ensures(Implies(len(suffix) == 0, ToSeq(Result()) == ToSeq(base)))
    # When the suffix is non-empty, the base token is preserved as a prefix and
    # the code point that immediately follows it is the separator space (so the
    # suffix keyword never fuses with the last base code point).
    Ensures(Implies(len(suffix) > 0, ToSeq(Result()).take(len(base)) == ToSeq(base)))
    Ensures(Implies(len(suffix) > 0, ToSeq(Result())[len(base)] == sep()))
    Ensures(Implies(len(suffix) > 0,
                    ToSeq(Result()).drop(len(base) + 1) == ToSeq(suffix)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # only append a separator + suffix when the suffix is non-empty
    Assert(len(ToSeq(suffix)) == len(suffix))
    if len(suffix) > 0:
        result.append(sep())
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
        k = 0
        while k < len(suffix):
            # invariants-start
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(suffix), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(suffix) > 0)
            Invariant(0 <= k and k <= len(suffix))
            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
            # invariants-end
            result.append(suffix[k])
            k = k + 1
        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(len(ToSeq(suffix)) == len(suffix))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    else:
        Assert(len(ToSeq(suffix)) == 0)
        Assert(ToSeq(result) == ToSeq(base))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    return result
    # impl-end


def render_column_with_opclass(base: List[int], suffix: List[int]) -> List[int]:
    """Site 2: the base token is the quoted column already combined with an
    operator-class keyword. The join behaviour is identical to site 1."""
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(suffix), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(suffix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text is the deep conditional concatenation.
    Ensures(ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)))
    # When the suffix is empty, the result is the base token exactly: no
    # trailing separator, same length as the base.
    Ensures(Implies(len(suffix) == 0, ToSeq(Result()) == ToSeq(base)))
    # When the suffix is non-empty, the base token is preserved as a prefix and
    # the code point that immediately follows it is the separator space.
    Ensures(Implies(len(suffix) > 0, ToSeq(Result()).take(len(base)) == ToSeq(base)))
    Ensures(Implies(len(suffix) > 0, ToSeq(Result())[len(base)] == sep()))
    Ensures(Implies(len(suffix) > 0,
                    ToSeq(Result()).drop(len(base) + 1) == ToSeq(suffix)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # base token
    j = 0
    while j < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(base))
        Invariant(ToSeq(result) == ToSeq(base).take(j))
        # invariants-end
        result.append(base[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(base))
    # only append a separator + suffix when the suffix is non-empty
    Assert(len(ToSeq(suffix)) == len(suffix))
    if len(suffix) > 0:
        result.append(sep())
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()))
        k = 0
        while k < len(suffix):
            # invariants-start
            Invariant(Acc(list_pred(base), 1 / 2))
            Invariant(Acc(list_pred(suffix), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(suffix) > 0)
            Invariant(0 <= k and k <= len(suffix))
            Invariant(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix).take(k))
            # invariants-end
            result.append(suffix[k])
            k = k + 1
        Assert(ToSeq(suffix).take(len(suffix)) == ToSeq(suffix))
        Assert(ToSeq(result) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(len(ToSeq(suffix)) == len(suffix))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base) + PSeq(sep()) + ToSeq(suffix))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    else:
        Assert(len(ToSeq(suffix)) == 0)
        Assert(ToSeq(result) == ToSeq(base))
        Assert(joined(ToSeq(base), ToSeq(suffix)) == ToSeq(base))
        Assert(ToSeq(result) == joined(ToSeq(base), ToSeq(suffix)))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A COMPLETE FUNCTIONAL EQUALITY. Both render_column (site 1) and render_column_with_opclass (site 2) carry the postcondition ToSeq(Result()) == joined(ToSeq(base), ToSeq(suffix)) UNCONDITIONALLY over the entire Requires-satisfying domain (Requires asks only for read access to the two lists; no domain restriction is possible), plus the empty/non-empty structural clauses. This pins any verifying impl to the exact gold behaviour, so verify=>correct.

A-LEG AUDIT (the only non-R/I legs). refinement.md leg A4/B4 is the sole A-reference: joined == real col_str join; there are NO consumed axioms (no @ContractOnly) and NO kind-3 (unexpressible-changed-op) legs. Ran axiom_check.py (G-AX): PASS -- 'deep model joined == real col_str join on 32 boundary + 20000 fuzz inputs (both sites); empty suffix leaves no trailing space and a non-empty suffix is space-separated (no fusion).' real_join in axiom_check faithfully reproduces the gold col_str join at both sites (col=base; if suffix: col='{} {}'.format(col,suffix)), matching mapping.md sec 3.1 and patch.diff. Model<->patch correspondence (A1-A5,B1-B5) holds: base=quote_name(column) / '{} {}'.format(quote_name,opclass) upstream input; suffix=col_suffixes[idx]; join deep-modelled; every remaining leg is R (str<->List[int]) or I. G-CONF conformance_check.py cross-checks the contract-stripped impl vs the REAL patched Columns/IndexColumns.__str__ over >=1e5 inputs.

POSITIVE CONTROL: pos_control.py (= gold model.py) verifies, exit 0, 18.2s.

atk_1 (site1 prepatch: direct concat, NO separator, unconditional): weakness exit 2 -- verification FAILED (spec rejected). Prepatch bug reproduced.
- atk_2 (site2 prepatch2: append sep+suffix UNCONDITIONALLY -> trailing space for empty suffix): exit 2 -- FAILED. Second prepatch bug reproduced.
- atk_3 (wrong separator code point 33 '!' instead of 32): exit 2 -- FAILED (boundary/oracle).
- atk_4 (double separator for non-empty suffix): exit 2 -- FAILED.
- atk_5 (off-by-one: while k < len(suffix)-1, drops last suffix char): exit 2 -- FAILED (boundary).
- atk_6 (inverted guard / control-flow-effect: append sep only when suffix EMPTY): exit 2 -- FAILED.
- atk_7 (partial-domain / ungrounded echo: ignore suffix, always return base): exit 2 -- FAILED.
- atk_8 (restructured-correct echo: 'if len(suffix) != 0' <=> 'if suffix'; site 2 gold-verbatim): weakness exit 0 -- CANDIDATE (shares spec AND verifies).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE. atk_8 is behaviourally identical to gold at both sites, so its faithful refined patch is the gold patch. Materialized it (atk_8_faithful.patch) and RAN the official harness via swebench_unified.harness.run_resolve('django__django-12039', patch): resolved=True, completed=True, note='resolved'. FAIL_TO_PASS test_descending_columns_list_sql PASS; all 11 PASS_TO_PASS PASS; 0 failures. A resolving echo of the gold is NOT a weakness (per unified panel_1/eq policy).

CONCLUSION: every genuinely-wrong impl (partial-domain, boundary, wrong-constant, control-flow-effect, ungrounded-oracle) is rejected by verification; the only verifying candidate resolves under the official harness. No verifying impl exists whose faithful patch fails to resolve. verify=>correct holds. Commands (from project root, SBU_BENCHMARK_DIR=benchmark-verified, interpreter python): `python -m swebench_unified.adversary same-spec|weakness nagini django__django-12039 <atk>`; run_resolve via swebench_unified.harness; `axiom_check.py` direct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no-drift) HOLDS. No diverging input exists between the modeled functions and the real callee.

Real callee (base_commit 58c1acb1, gold patch applied) at django/db/backends/ddl_references.py: both Columns.__str__.col_str (site1) and IndexColumns.__str__.col_str (site2) compute `col = <base>; try: suffix = col_suffixes[idx]; if suffix: col = '{} {}'.format(col, suffix) except IndexError: pass; return col`. base = quote_name(column) (site1) or '{} {}'.format(quote_name(column), opclasses[idx]) (site2); both assembled UPSTREAM of the modeled join and supplied as the model's opaque `base` input.

Model spec: joined(base,suffix) = base if len(suffix)==0 else base + [32] + suffix; postconditions pin (a) empty suffix -> result==base exactly (no trailing sep), (b) non-empty -> base preserved as prefix, code point after base == space, suffix appended verbatim. render_column / render_column_with_opclass carry identical specs.

Empirical facts established:
- G-AX (axiom_check.py): exit 0 — deep model `joined` == real col_str join on 32 boundary + 20000 fuzz inputs, both sites; empty-suffix no-trailing-space + non-empty single-separator both confirmed.
- G-CONF (conformance_check.py) run against the ACTUALLY-patched repo (asgiref present via swebench-lean env): exit 0 — 100288 shadow-vs-real comparisons (144 boundary + 50000 fuzz pairs x 2 sites), 0 disagreements.
- Model verifies under pinned Nagini verifier: 'Verification successful' (16.2s, exit 0) — spec region is genuine, not vacuous.
- Edge probes vs real patched __str__: Python truthiness `if suffix:` is exactly equivalent to len(suffix)>0 for str (only '' is falsy); whitespace suffix ' ', '0', NUL '\x00', 'DESC' all match model. The IndexError branch (dead in tested flow, col_suffixes same length as columns) returns base == joined(base,'') so even that unmodeled path agrees.

Modeling boundary is honest: base/suffix are the join's inputs produced upstream (quote_name / opclass format), correctly abstracted as opaque code-point lists. The spec is not too strong — it exactly matches real behavior across the full Requires-satisfying domain and does not over-constrain. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over the nagini spec view, impl regions elided to '...') passes cleanly: PASSED=True, zero hard failures — no diff markers, no gold-patch line reproduced, no patched file/module path, no spec-view identifier or comment naming a patched repo symbol, no bug/fix narration. Same-spec region is the model itself (bundle's frozen spec). Semantic judgment vs the PUBLIC problem_statement (NOT hints_text): every behavioral fact in the spec view is already public. (a) non-empty suffix => base + single separating space + suffix: problem_statement gives verbatim expected '"name" DESC' vs wrong '"name"DESC'. (b) empty suffix => base token exactly, no trailing space: problem_statement gives expected '"name" text_pattern_ops' vs the buggy trailing-space '"name" text_pattern_ops '. (c) two join sites differing only in base token (column alone vs column+opclass keyword): problem_statement explicitly identifies both the ordering site and the #30903 opclasses site, and even states the root cause (col_suffixes holds empty strings, not an empty list, for ascending order). The spec view reveals NO gold-edit mechanics: no `if suffix:` guard, no try/except IndexError restructuring, no col/.format internals, no repo symbols. It is a faithful behavioral specification derivable entirely from the solver-visible problem_statement, not a reconstruction of the gold diff. No spec-view line exceeds the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
