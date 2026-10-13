# P2 adversarial audit — sphinx-doc__sphinx-8721

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -151,16 +147,6 @@
                     ToSeq(Result()) == ToSeq(modules)))
     # post-conditions-end
     # impl-start
-    empty = []  # type: List[int]
-    ep = [101, 112, 117, 98]  # type: List[int]
-    Assert(ToSeq(ep) == lit_epub())
-    if begins_with(name, ep) and not enable_epub:
-        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
-        Assert(suppressed(ToSeq(name), enable_epub))
-        return empty
-    # The guard did not fire: the target is not suppressed.
-    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
-    Assert(not suppressed(ToSeq(name), enable_epub))
     result = []  # type: List[int]
     i = 0
     n = len(modules)
@@ -170,7 +156,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n and n == len(modules))
         Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
         Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -152,31 +148,5 @@
     # post-conditions-end
     # impl-start
     empty = []  # type: List[int]
-    ep = [101, 112, 117, 98]  # type: List[int]
-    Assert(ToSeq(ep) == lit_epub())
-    if begins_with(name, ep) and not enable_epub:
-        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
-        Assert(suppressed(ToSeq(name), enable_epub))
-        return empty
-    # The guard did not fire: the target is not suppressed.
-    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
-    Assert(not suppressed(ToSeq(name), enable_epub))
-    result = []  # type: List[int]
-    i = 0
-    n = len(modules)
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(modules), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n and n == len(modules))
-        Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
-        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
-               == ToSeq(modules).take(i + 1))
-        result = result + [modules[i]]
-        i = i + 1
-    Assert(ToSeq(modules).take(n) == ToSeq(modules))
-    return result
+    return empty
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
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -153,30 +149,17 @@
     # impl-start
     empty = []  # type: List[int]
     ep = [101, 112, 117, 98]  # type: List[int]
-    Assert(ToSeq(ep) == lit_epub())
     if begins_with(name, ep) and not enable_epub:
-        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
-        Assert(suppressed(ToSeq(name), enable_epub))
         return empty
-    # The guard did not fire: the target is not suppressed.
-    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
-    Assert(not suppressed(ToSeq(name), enable_epub))
     result = []  # type: List[int]
-    i = 0
-    n = len(modules)
-    while i < n:
+    i = len(modules)
+    while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(modules), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= n and n == len(modules))
-        Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
+        Invariant(0 <= i and i <= len(modules))
         # invariants-end
-        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
-        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
-               == ToSeq(modules).take(i + 1))
-        result = result + [modules[i]]
-        i = i + 1
-    Assert(ToSeq(modules).take(n) == ToSeq(modules))
+        result = result + [modules[i - 1]]
+        i = i - 1
     return result
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
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -153,30 +149,22 @@
     # impl-start
     empty = []  # type: List[int]
     ep = [101, 112, 117, 98]  # type: List[int]
-    Assert(ToSeq(ep) == lit_epub())
     if begins_with(name, ep) and not enable_epub:
-        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
-        Assert(suppressed(ToSeq(name), enable_epub))
         return empty
-    # The guard did not fire: the target is not suppressed.
-    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
-    Assert(not suppressed(ToSeq(name), enable_epub))
     result = []  # type: List[int]
     i = 0
     n = len(modules)
-    while i < n:
+    while i + 1 < n:
         # invariants-start
         Invariant(Acc(list_pred(modules), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n and n == len(modules))
         Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
         Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
                == ToSeq(modules).take(i + 1))
         result = result + [modules[i]]
         i = i + 1
-    Assert(ToSeq(modules).take(n) == ToSeq(modules))
     return result
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
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -153,14 +149,8 @@
     # impl-start
     empty = []  # type: List[int]
     ep = [101, 112, 117, 98]  # type: List[int]
-    Assert(ToSeq(ep) == lit_epub())
-    if begins_with(name, ep) and not enable_epub:
-        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
-        Assert(suppressed(ToSeq(name), enable_epub))
+    if begins_with(name, ep) and enable_epub:
         return empty
-    # The guard did not fire: the target is not suppressed.
-    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
-    Assert(not suppressed(ToSeq(name), enable_epub))
     result = []  # type: List[int]
     i = 0
     n = len(modules)
@@ -170,7 +160,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n and n == len(modules))
         Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
         Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -154,7 +150,7 @@
     empty = []  # type: List[int]
     ep = [101, 112, 117, 98]  # type: List[int]
     Assert(ToSeq(ep) == lit_epub())
-    if begins_with(name, ep) and not enable_epub:
+    if not enable_epub and begins_with(name, ep):
         Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
         Assert(suppressed(ToSeq(name), enable_epub))
         return empty
@@ -170,7 +166,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n and n == len(modules))
         Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
         Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -152,15 +148,9 @@
     # post-conditions-end
     # impl-start
     empty = []  # type: List[int]
-    ep = [101, 112, 117, 98]  # type: List[int]
-    Assert(ToSeq(ep) == lit_epub())
+    ep = [101, 112, 117]  # type: List[int]   # 'epu' (wrong literal)
     if begins_with(name, ep) and not enable_epub:
-        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
-        Assert(suppressed(ToSeq(name), enable_epub))
         return empty
-    # The guard did not fire: the target is not suppressed.
-    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
-    Assert(not suppressed(ToSeq(name), enable_epub))
     result = []  # type: List[int]
     i = 0
     n = len(modules)
@@ -170,13 +160,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n and n == len(modules))
         Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
         Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
                == ToSeq(modules).take(i + 1))
         result = result + [modules[i]]
         i = i + 1
-    Assert(ToSeq(modules).take(n) == ToSeq(modules))
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(name), 1 / 4))
     Requires(Acc(list_pred(lit), 1 / 4))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 4))
@@ -114,7 +112,6 @@
         Invariant(n <= len(name))
         Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
         Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
         Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
@@ -136,7 +133,6 @@
     # source entries, one element per module that has a page) are read-only.
     Requires(Acc(list_pred(name), 1 / 2))
     Requires(Acc(list_pred(modules), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(name), 1 / 2))
@@ -153,30 +149,20 @@
     # impl-start
     empty = []  # type: List[int]
     ep = [101, 112, 117, 98]  # type: List[int]
-    Assert(ToSeq(ep) == lit_epub())
     if begins_with(name, ep) and not enable_epub:
-        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
-        Assert(suppressed(ToSeq(name), enable_epub))
         return empty
-    # The guard did not fire: the target is not suppressed.
-    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
-    Assert(not suppressed(ToSeq(name), enable_epub))
     result = []  # type: List[int]
+    n = len(modules)
+    if n > 0:
+        result = result + [modules[0]]
     i = 0
-    n = len(modules)
     while i < n:
         # invariants-start
         Invariant(Acc(list_pred(modules), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= n and n == len(modules))
-        Invariant(ToSeq(result) == ToSeq(modules).take(i))
-        Invariant(MustTerminate(n - i + 1))
         # invariants-end
-        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
-        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
-               == ToSeq(modules).take(i + 1))
         result = result + [modules[i]]
         i = i + 1
-    Assert(ToSeq(modules).take(n) == ToSeq(modules))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8721.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the documentation-source collector assembles the set of highlighted
  module-source pages for an output target, it must respect the kind of output
  target being produced, identified by the target's name (a sequence of Unicode
  code points), together with a boolean preference that decides whether module
  pages are wanted for electronic-book output:

    (1) For an ELECTRONIC-BOOK target (any name beginning with the code-point
        sequence `epub`) the per-module source pages are produced ONLY when the
        electronic-book preference is enabled; with the preference disabled
        (its default) no module pages are produced.

    (2) For every other target the per-module source pages are produced as
        before: one page for each module that has a recorded source entry, in
        the order the modules are presented.

  The decisive content: with the electronic-book preference disabled, an
  electronic-book target yields NO module pages (the collector returns an empty
  set of pages) — module pages are not emitted into electronic-book output by
  default.

Target names are modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the specification is carried over `PSeq[int]`. The begins-with
decision is modelled DEEPLY (a spelled-out fold), validated == the real
`str.startswith` out-of-band by axiom_check.py (G-AX), never consumed as an
axiom. The collection of recorded module entries enters as an ordinary list
value.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The electronic-book name decision — the `epub`-prefix
#  test — is modelled DEEPLY below (`prefix_eq`) and validated == the real
#  `str.startswith` by axiom_check.py / G-AX, never consumed. The
#  electronic-book preference and the recorded module entries are plain input
#  values, not axioms.)
# axioms-end


# pure-start
@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL prefix match (begins-with). Total: if `s` is shorter than
    `lit` no such match exists, so the result is False. Front-recursive (over
    both sequences) so a single unfold is available per loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


@Pure
def lemma_prefix_too_long(s: PSeq[int], lit: PSeq[int]) -> bool:
    """If `lit` is strictly longer than `s`, no literal prefix match exists.
    Proven by front-recursion on `s`."""
    Requires(len(lit) > len(s))
    Ensures(Result())
    Ensures(not prefix_eq(s, lit))
    if len(s) == 0:
        return True
    return lemma_prefix_too_long(s.drop(1), lit.drop(1))


@Pure
def lit_epub() -> PSeq[int]:
    # 'epub'
    return PSeq(101, 112, 117, 98)


@Pure
def suppressed(name: PSeq[int], enable_epub: bool) -> bool:
    """The collector produces NO module pages for the target named `name` under
    electronic-book preference `enable_epub` iff `name` begins with `epub` and
    the electronic-book preference is off. Every other target is unsuppressed
    (module pages produced as before)."""
    return prefix_eq(name, lit_epub()) and not enable_epub
# pure-end


def begins_with(name: List[int], lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL prefix (begins-with) match of `lit` against `name`.
    Ensures(Result() == prefix_eq(ToSeq(name), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    n = len(lit)
    if n > len(name):
        Assert(lemma_prefix_too_long(ToSeq(name), ToSeq(lit)))
        return False
    ok = True
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= n and n == len(lit))
        Invariant(n <= len(name))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
        Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
        # invariants-end
        Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(name).drop(i - 1).drop(1) == ToSeq(name).drop(i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if name[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(name).drop(0) == ToSeq(name))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end


def module_source_pages(name: List[int], enable_epub: bool,
                        modules: List[int]) -> List[int]:
    # pre-conditions-start
    # `name` (the output-target name) and `modules` (the recorded per-module
    # source entries, one element per module that has a page) are read-only.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(modules), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(modules), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A suppressed target (an electronic-book target with the preference off)
    # yields NO module pages — the produced page set is empty.
    Ensures(Implies(suppressed(ToSeq(name), enable_epub), len(Result()) == 0))
    # Every other target produces exactly one page per recorded module entry,
    # in the order the modules are presented.
    Ensures(Implies(not suppressed(ToSeq(name), enable_epub),
                    ToSeq(Result()) == ToSeq(modules)))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    ep = [101, 112, 117, 98]  # type: List[int]
    Assert(ToSeq(ep) == lit_epub())
    if begins_with(name, ep) and not enable_epub:
        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
        Assert(suppressed(ToSeq(name), enable_epub))
        return empty
    # The guard did not fire: the target is not suppressed.
    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
    Assert(not suppressed(ToSeq(name), enable_epub))
    result = []  # type: List[int]
    i = 0
    n = len(modules)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(modules), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(modules))
        Invariant(ToSeq(result) == ToSeq(modules).take(i))
        # invariants-end
        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
               == ToSeq(modules).take(i + 1))
        result = result + [modules[i]]
        i = i + 1
    Assert(ToSeq(modules).take(n) == ToSeq(modules))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec `module_source_pages` FULLY pins the abstract output via two complementary postconditions: Implies(suppressed(ToSeq(name), enable_epub), len(Result())==0) and Implies(not suppressed(...), ToSeq(Result())==ToSeq(modules)), where suppressed = prefix_eq(name,'epub') and not enable_epub. Zero abstract-output freedom => any verifying same-spec impl equals the gold behaviour.

Positive control: `bash scripts/nagini_verify.sh .../pos_control.py` -> Verification successful (10.88s), exit 0.

All 8 attacks confirmed same-spec (spec/pure/axiom region byte-identical): `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8721 .../atk_N.py` -> exit 0 for all N.

Weakness runs (concurrent, <=3 JVMs/batch): `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8721 .../atk_N.py`:
- atk_1 (prepatch bug: gate-less, always emits all modules) -> exit 2, verification failed (fails suppressed-clause). Reproduces the prepatch bug; model_prepatch.py separately fails at line 143 (suppressed clause), exit 1.
- atk_2 (suppress-everything: always return empty) -> exit 2 (fails not-suppressed clause).
- atk_3 (reversed module order) -> exit 2 (fails ordering clause).
- atk_4 (drop-last / off-by-one: while i+1<n) -> exit 2 (fails not-suppressed equality).
- atk_5 (inverted gate: suppress when enable_epub TRUE) -> exit 2 (fails both clauses).
- atk_6 (ECHO: reordered conjunction `not enable_epub and begins_with(...)`, behaviorally identical to gold) -> exit 0 CANDIDATE, verifies (14.0s). Per protocol materialized its faithful refined patch (gold epub gate with the conjunction reordered to mirror the impl) and RAN it through the official harness: run_resolve('sphinx-doc__sphinx-8721', atk_6.patch.diff) -> RESOLVED=True, COMPLETED=True, note='resolved', FLAKY=False. Echo resolves => NOT a weakness (matches resolved echo policy).
- atk_7 (wrong gate literal 'epu', 3 cps) -> exit 2 (suppresses non-epub names like 'epux', fails not-suppressed clause).
- atk_8 (duplicate first module element) -> exit 2 (fails ToSeq(Result())==ToSeq(modules)).

A-leg audit: no consumed axioms (axioms region empty by design). The sole A-reference is the deep model prefix_eq == real str.startswith (and the suppressed composite == the installed epub gate). G-AX axiom_check.py -> 'G-AX OK ... sound on 33 boundary + 50000 fuzz builder names', exit 0. refinement.md legs A1(R), A2(R/I), A3(R), A4(A-reference + I), A5(R/I) — all R / A-reference / I, no kind-3; the A-reference callee correspondence (str.startswith single-arg, no start/end) holds and matches mapping.md 3.1/3.2. Single-file 'singlehtml' co-change is disclosed as out-of-model (untested, carried verbatim in gold patch.diff), correctly scoped.

Conclusion: no verifying same-spec wrong impl whose faithful patch fails to resolve; the only verifying attack is a behavioral echo that resolves. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8721.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the documentation-source collector assembles the set of highlighted
  module-source pages for an output target, it must respect the kind of output
  target being produced, identified by the target's name (a sequence of Unicode
  code points), together with a boolean preference that decides whether module
  pages are wanted for electronic-book output:

    (1) For an ELECTRONIC-BOOK target (any name beginning with the code-point
        sequence `epub`) the per-module source pages are produced ONLY when the
        electronic-book preference is enabled; with the preference disabled
        (its default) no module pages are produced.

    (2) For every other target the per-module source pages are produced as
        before: one page for each module that has a recorded source entry, in
        the order the modules are presented.

  The decisive content: with the electronic-book preference disabled, an
  electronic-book target yields NO module pages (the collector returns an empty
  set of pages) — module pages are not emitted into electronic-book output by
  default.

Target names are modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the specification is carried over `PSeq[int]`. The begins-with
decision is modelled DEEPLY (a spelled-out fold), validated == the real
`str.startswith` out-of-band by axiom_check.py (G-AX), never consumed as an
axiom. The collection of recorded module entries enters as an ordinary list
value.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The electronic-book name decision — the `epub`-prefix
#  test — is modelled DEEPLY below (`prefix_eq`) and validated == the real
#  `str.startswith` by axiom_check.py / G-AX, never consumed. The
#  electronic-book preference and the recorded module entries are plain input
#  values, not axioms.)
# axioms-end


# pure-start
@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL prefix match (begins-with). Total: if `s` is shorter than
    `lit` no such match exists, so the result is False. Front-recursive (over
    both sequences) so a single unfold is available per loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


@Pure
def lemma_prefix_too_long(s: PSeq[int], lit: PSeq[int]) -> bool:
    """If `lit` is strictly longer than `s`, no literal prefix match exists.
    Proven by front-recursion on `s`."""
    Requires(len(lit) > len(s))
    Ensures(Result())
    Ensures(not prefix_eq(s, lit))
    if len(s) == 0:
        return True
    return lemma_prefix_too_long(s.drop(1), lit.drop(1))


@Pure
def lit_epub() -> PSeq[int]:
    # 'epub'
    return PSeq(101, 112, 117, 98)


@Pure
def suppressed(name: PSeq[int], enable_epub: bool) -> bool:
    """The collector produces NO module pages for the target named `name` under
    electronic-book preference `enable_epub` iff `name` begins with `epub` and
    the electronic-book preference is off. Every other target is unsuppressed
    (module pages produced as before)."""
    return prefix_eq(name, lit_epub()) and not enable_epub
# pure-end


def begins_with(name: List[int], lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL prefix (begins-with) match of `lit` against `name`.
    Ensures(Result() == prefix_eq(ToSeq(name), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    n = len(lit)
    if n > len(name):
        Assert(lemma_prefix_too_long(ToSeq(name), ToSeq(lit)))
        return False
    ok = True
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= n and n == len(lit))
        Invariant(n <= len(name))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(name).drop(i)))
        Invariant(ok == prefix_eq(ToSeq(name).drop(i), ToSeq(lit).drop(i)))
        # invariants-end
        Assert(ToSeq(name).drop(i - 1)[0] == ToSeq(name)[i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(name).drop(i - 1).drop(1) == ToSeq(name).drop(i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if name[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(name).drop(0) == ToSeq(name))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end


def module_source_pages(name: List[int], enable_epub: bool,
                        modules: List[int]) -> List[int]:
    # pre-conditions-start
    # `name` (the output-target name) and `modules` (the recorded per-module
    # source entries, one element per module that has a page) are read-only.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(modules), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(modules), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A suppressed target (an electronic-book target with the preference off)
    # yields NO module pages — the produced page set is empty.
    Ensures(Implies(suppressed(ToSeq(name), enable_epub), len(Result()) == 0))
    # Every other target produces exactly one page per recorded module entry,
    # in the order the modules are presented.
    Ensures(Implies(not suppressed(ToSeq(name), enable_epub),
                    ToSeq(Result()) == ToSeq(modules)))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    ep = [101, 112, 117, 98]  # type: List[int]
    Assert(ToSeq(ep) == lit_epub())
    if begins_with(name, ep) and not enable_epub:
        Assert(prefix_eq(ToSeq(name), lit_epub()) and not enable_epub)
        Assert(suppressed(ToSeq(name), enable_epub))
        return empty
    # The guard did not fire: the target is not suppressed.
    Assert(not (prefix_eq(ToSeq(name), lit_epub()) and not enable_epub))
    Assert(not suppressed(ToSeq(name), enable_epub))
    result = []  # type: List[int]
    i = 0
    n = len(modules)
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(modules), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n and n == len(modules))
        Invariant(ToSeq(result) == ToSeq(modules).take(i))
        # invariants-end
        Assert(ToSeq(modules).take(i + 1).drop(i)[0] == ToSeq(modules)[i])
        Assert(ToSeq(modules).take(i) + PSeq(ToSeq(modules)[i])
               == ToSeq(modules).take(i + 1))
        result = result + [modules[i]]
        i = i + 1
    Assert(ToSeq(modules).take(n) == ToSeq(modules))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec `module_source_pages` FULLY pins the abstract output via two complementary postconditions: Implies(suppressed(ToSeq(name), enable_epub), len(Result())==0) and Implies(not suppressed(...), ToSeq(Result())==ToSeq(modules)), where suppressed = prefix_eq(name,'epub') and not enable_epub. Zero abstract-output freedom => any verifying same-spec impl equals the gold behaviour.

Positive control: `bash scripts/nagini_verify.sh .../pos_control.py` -> Verification successful (10.88s), exit 0.

All 8 attacks confirmed same-spec (spec/pure/axiom region byte-identical): `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-8721 .../atk_N.py` -> exit 0 for all N.

Weakness runs (concurrent, <=3 JVMs/batch): `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8721 .../atk_N.py`:
- atk_1 (prepatch bug: gate-less, always emits all modules) -> exit 2, verification failed (fails suppressed-clause). Reproduces the prepatch bug; model_prepatch.py separately fails at line 143 (suppressed clause), exit 1.
- atk_2 (suppress-everything: always return empty) -> exit 2 (fails not-suppressed clause).
- atk_3 (reversed module order) -> exit 2 (fails ordering clause).
- atk_4 (drop-last / off-by-one: while i+1<n) -> exit 2 (fails not-suppressed equality).
- atk_5 (inverted gate: suppress when enable_epub TRUE) -> exit 2 (fails both clauses).
- atk_6 (ECHO: reordered conjunction `not enable_epub and begins_with(...)`, behaviorally identical to gold) -> exit 0 CANDIDATE, verifies (14.0s). Per protocol materialized its faithful refined patch (gold epub gate with the conjunction reordered to mirror the impl) and RAN it through the official harness: run_resolve('sphinx-doc__sphinx-8721', atk_6.patch.diff) -> RESOLVED=True, COMPLETED=True, note='resolved', FLAKY=False. Echo resolves => NOT a weakness (matches resolved echo policy).
- atk_7 (wrong gate literal 'epu', 3 cps) -> exit 2 (suppresses non-epub names like 'epux', fails not-suppressed clause).
- atk_8 (duplicate first module element) -> exit 2 (fails ToSeq(Result())==ToSeq(modules)).

A-leg audit: no consumed axioms (axioms region empty by design). The sole A-reference is the deep model prefix_eq == real str.startswith (and the suppressed composite == the installed epub gate). G-AX axiom_check.py -> 'G-AX OK ... sound on 33 boundary + 50000 fuzz builder names', exit 0. refinement.md legs A1(R), A2(R/I), A3(R), A4(A-reference + I), A5(R/I) — all R / A-reference / I, no kind-3; the A-reference callee correspondence (str.startswith single-arg, no start/end) holds and matches mapping.md 3.1/3.2. Single-file 'singlehtml' co-change is disclosed as out-of-model (untested, carried verbatim in gold patch.diff), correctly scoped.

Conclusion: no verifying same-spec wrong impl whose faithful patch fails to resolve; the only verifying attack is a behavioral echo that resolves. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-ran both oracles against the real repo at base_commit 82ef497 (patched worktree): axiom_check.py exit 0 — prefix_eq == str.startswith sound on 33 boundary + 50000 fuzz names; conformance_check.py exit 0 — shadow impl == real collect_pages on 100276 inputs, 0 disagreements. My own epub-prefix probes agreed (real=[], model=[]).

The gold patch adds TWO early-return guards in collect_pages: `name == 'singlehtml'` and `name.startswith('epub') and not viewcode_enable_epub`. The model captures only the epub guard, so it diverges from the real repo on the single input `singlehtml`. I confirmed this exclusion is legitimate and not silent drift: (a) `singlehtml` is exercised by NO test — F2P=test_viewcode_epub_default; P2P=test_viewcode_epub_enabled/test_linkcode/test_local_source_files; grep for 'singlehtml' in tests/test_ext_viewcode.py returns nothing; (b) the public problem_statement is purely about epub ('module pages should not be created for epub by default'); (c) the boundary is explicitly disclosed in mapping.md §1 and refinement.md §A, and the conformance-check input domain excludes exactly `singlehtml` and nothing else; (d) patch.diff retains the gold VERBATIM (both guards), so G-RESOLVE / the correctness oracle is unaffected. An impl verifying against this spec (no singlehtml guard) still passes every F2P/P2P test, and the verbatim gold is what actually resolves.

The modeled abstractions (str↔List[int] code points, page-set↔integer carriers, sorted-presentation order, freshness-probe upstream plumbing abstracted via emit_firstresult truthy) are all disclosed in mapping.md §2 and hold on the tested inputs. Within the disclosed modeled domain the spec matches the real callee on every input checked. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py) describes exactly what the public problem_statement already discloses: for an epub target (name beginning with `epub`) with the electronic-book preference (viewcode_enable_epub-analog) disabled, the collector produces NO module pages by default; every other target produces one page per recorded module (baseline viewcode behavior). The problem_statement states verbatim 'viewcode creates pages for epub even if viewcode_enable_epub=False' and 'module pages should not be created for epub by default' — so the epub prefix condition, the boolean preference, and the empty-output-when-off decision are all public. The deep prefix_eq/begins_with modeling is a faithful mechanization of 'begins with epub', a natural domain consequence, not a disclosure of a non-obvious gold-edit detail. Notably the spec does NOT model the gold patch's `singlehtml` early-return branch at all — a modeling boundary choice, and the omission means the spec cannot be reconstructing the full gold edit. No spec-view line reveals gold-patch specifics (file sphinx/ext/viewcode.py, app.builder.name, the early-return structure) beyond the problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
