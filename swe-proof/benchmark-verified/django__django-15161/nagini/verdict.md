# P2 adversarial audit — django__django-15161

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(name), 1 / 2))
     # The class name component carries no embedded dot (it is a single leaf).
     Requires(no_dot(ToSeq(name)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(configured), 1 / 2))
@@ -109,56 +107,14 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if len(configured) > 0 and exact:
-        i = 0
-        while i < len(configured):
-            # invariants-start
-            Invariant(Acc(list_pred(configured), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(len(configured) > 0 and exact)
-            Invariant(0 <= i and i <= len(configured))
-            Invariant(ToSeq(result) == ToSeq(configured).take(i))
-            Invariant(MustTerminate(len(configured) - i + 1))
-            # invariants-end
-            result = result + [configured[i]]
-            i = i + 1
-        Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
-        Assert(ToSeq(result) == ToSeq(configured))
-        return result
-    else:
-        i = 0
-        while i < len(module):
-            # invariants-start
-            Invariant(Acc(list_pred(configured), 1 / 2))
-            Invariant(Acc(list_pred(module), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
-            Invariant(0 <= i and i <= len(module))
-            Invariant(ToSeq(result) == ToSeq(module).take(i))
-            Invariant(MustTerminate(len(module) - i + 1))
-            # invariants-end
-            result = result + [module[i]]
-            i = i + 1
-        Assert(ToSeq(module).take(len(module)) == ToSeq(module))
-        result = result + [DOT()]
-        j = 0
-        while j < len(name):
-            # invariants-start
-            Invariant(Acc(list_pred(configured), 1 / 2))
-            Invariant(Acc(list_pred(module), 1 / 2))
-            Invariant(Acc(list_pred(name), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
-            Invariant(0 <= j and j <= len(name))
-            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
-            Invariant(MustTerminate(len(name) - j + 1))
-            # invariants-end
-            result = result + [name[j]]
-            j = j + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(ToSeq(result) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        Assert(qualified(ToSeq(module), ToSeq(name)) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        return result
+    i = 0
+    while i < len(configured):
+        Invariant(Acc(list_pred(configured), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= i and i <= len(configured))
+        Invariant(ToSeq(result) == ToSeq(configured).take(i))
+        result = result + [configured[i]]
+        i = i + 1
+    Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
+    return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(name), 1 / 2))
     # The class name component carries no embedded dot (it is a single leaf).
     Requires(no_dot(ToSeq(name)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(configured), 1 / 2))
@@ -109,56 +107,39 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if len(configured) > 0 and exact:
+    if not (len(configured) > 0 and exact):
         i = 0
         while i < len(configured):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(configured) > 0 and exact)
             Invariant(0 <= i and i <= len(configured))
             Invariant(ToSeq(result) == ToSeq(configured).take(i))
-            Invariant(MustTerminate(len(configured) - i + 1))
-            # invariants-end
             result = result + [configured[i]]
             i = i + 1
         Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
-        Assert(ToSeq(result) == ToSeq(configured))
         return result
     else:
         i = 0
         while i < len(module):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= i and i <= len(module))
             Invariant(ToSeq(result) == ToSeq(module).take(i))
-            Invariant(MustTerminate(len(module) - i + 1))
-            # invariants-end
             result = result + [module[i]]
             i = i + 1
         Assert(ToSeq(module).take(len(module)) == ToSeq(module))
         result = result + [DOT()]
         j = 0
         while j < len(name):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= j and j <= len(name))
             Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
-            Invariant(MustTerminate(len(name) - j + 1))
-            # invariants-end
             result = result + [name[j]]
             j = j + 1
         Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(ToSeq(result) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        Assert(qualified(ToSeq(module), ToSeq(name)) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
         return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(name), 1 / 2))
     # The class name component carries no embedded dot (it is a single leaf).
     Requires(no_dot(ToSeq(name)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(configured), 1 / 2))
@@ -111,54 +109,36 @@
     result = []  # type: List[int]
     if len(configured) > 0 and exact:
         i = 0
-        while i < len(configured):
-            # invariants-start
+        while i < len(configured) - 1:
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(configured) > 0 and exact)
-            Invariant(0 <= i and i <= len(configured))
+            Invariant(0 <= i and i <= len(configured) - 1)
             Invariant(ToSeq(result) == ToSeq(configured).take(i))
-            Invariant(MustTerminate(len(configured) - i + 1))
-            # invariants-end
             result = result + [configured[i]]
             i = i + 1
-        Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
-        Assert(ToSeq(result) == ToSeq(configured))
         return result
     else:
         i = 0
         while i < len(module):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= i and i <= len(module))
             Invariant(ToSeq(result) == ToSeq(module).take(i))
-            Invariant(MustTerminate(len(module) - i + 1))
-            # invariants-end
             result = result + [module[i]]
             i = i + 1
         Assert(ToSeq(module).take(len(module)) == ToSeq(module))
         result = result + [DOT()]
         j = 0
         while j < len(name):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= j and j <= len(name))
             Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
-            Invariant(MustTerminate(len(name) - j + 1))
-            # invariants-end
             result = result + [name[j]]
             j = j + 1
         Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(ToSeq(result) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        Assert(qualified(ToSeq(module), ToSeq(name)) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
         return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(name), 1 / 2))
     # The class name component carries no embedded dot (it is a single leaf).
     Requires(no_dot(ToSeq(name)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(configured), 1 / 2))
@@ -112,53 +110,34 @@
     if len(configured) > 0 and exact:
         i = 0
         while i < len(configured):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(configured) > 0 and exact)
             Invariant(0 <= i and i <= len(configured))
             Invariant(ToSeq(result) == ToSeq(configured).take(i))
-            Invariant(MustTerminate(len(configured) - i + 1))
-            # invariants-end
             result = result + [configured[i]]
             i = i + 1
         Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
-        Assert(ToSeq(result) == ToSeq(configured))
         return result
     else:
         i = 0
-        while i < len(module):
-            # invariants-start
-            Invariant(Acc(list_pred(configured), 1 / 2))
-            Invariant(Acc(list_pred(module), 1 / 2))
+        while i < len(name):
+            Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
-            Invariant(0 <= i and i <= len(module))
-            Invariant(ToSeq(result) == ToSeq(module).take(i))
-            Invariant(MustTerminate(len(module) - i + 1))
-            # invariants-end
-            result = result + [module[i]]
+            Invariant(0 <= i and i <= len(name))
+            Invariant(ToSeq(result) == ToSeq(name).take(i))
+            result = result + [name[i]]
             i = i + 1
-        Assert(ToSeq(module).take(len(module)) == ToSeq(module))
+        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
         result = result + [DOT()]
         j = 0
-        while j < len(name):
-            # invariants-start
-            Invariant(Acc(list_pred(configured), 1 / 2))
+        while j < len(module):
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
-            Invariant(0 <= j and j <= len(name))
-            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
-            Invariant(MustTerminate(len(name) - j + 1))
-            # invariants-end
-            result = result + [name[j]]
+            Invariant(0 <= j and j <= len(module))
+            Invariant(ToSeq(result) == ToSeq(name) + PSeq(DOT()) + ToSeq(module).take(j))
+            result = result + [module[j]]
             j = j + 1
-        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(ToSeq(result) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        Assert(qualified(ToSeq(module), ToSeq(name)) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
+        Assert(ToSeq(module).take(len(module)) == ToSeq(module))
         return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(name), 1 / 2))
     # The class name component carries no embedded dot (it is a single leaf).
     Requires(no_dot(ToSeq(name)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(configured), 1 / 2))
@@ -112,53 +110,35 @@
     if len(configured) > 0 and exact:
         i = 0
         while i < len(configured):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(configured) > 0 and exact)
             Invariant(0 <= i and i <= len(configured))
             Invariant(ToSeq(result) == ToSeq(configured).take(i))
-            Invariant(MustTerminate(len(configured) - i + 1))
-            # invariants-end
             result = result + [configured[i]]
             i = i + 1
         Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
-        Assert(ToSeq(result) == ToSeq(configured))
         return result
     else:
         i = 0
         while i < len(module):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= i and i <= len(module))
             Invariant(ToSeq(result) == ToSeq(module).take(i))
-            Invariant(MustTerminate(len(module) - i + 1))
-            # invariants-end
             result = result + [module[i]]
             i = i + 1
         Assert(ToSeq(module).take(len(module)) == ToSeq(module))
-        result = result + [DOT()]
         j = 0
         while j < len(name):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= j and j <= len(name))
-            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
-            Invariant(MustTerminate(len(name) - j + 1))
-            # invariants-end
+            Invariant(ToSeq(result) == ToSeq(module) + ToSeq(name).take(j))
             result = result + [name[j]]
             j = j + 1
         Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(ToSeq(result) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        Assert(qualified(ToSeq(module), ToSeq(name)) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
         return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(name), 1 / 2))
     # The class name component carries no embedded dot (it is a single leaf).
     Requires(no_dot(ToSeq(name)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(configured), 1 / 2))
@@ -112,53 +110,37 @@
     if len(configured) > 0 and exact:
         i = 0
         while i < len(configured):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(configured) > 0 and exact)
             Invariant(0 <= i and i <= len(configured))
             Invariant(ToSeq(result) == ToSeq(configured).take(i))
-            Invariant(MustTerminate(len(configured) - i + 1))
-            # invariants-end
             result = result + [configured[i]]
             i = i + 1
         Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
-        Assert(ToSeq(result) == ToSeq(configured))
+        result = result + [DOT()]
         return result
     else:
         i = 0
         while i < len(module):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= i and i <= len(module))
             Invariant(ToSeq(result) == ToSeq(module).take(i))
-            Invariant(MustTerminate(len(module) - i + 1))
-            # invariants-end
             result = result + [module[i]]
             i = i + 1
         Assert(ToSeq(module).take(len(module)) == ToSeq(module))
         result = result + [DOT()]
         j = 0
         while j < len(name):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= j and j <= len(name))
             Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
-            Invariant(MustTerminate(len(name) - j + 1))
-            # invariants-end
             result = result + [name[j]]
             j = j + 1
         Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(ToSeq(result) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        Assert(qualified(ToSeq(module), ToSeq(name)) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
         return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(name), 1 / 2))
     # The class name component carries no embedded dot (it is a single leaf).
     Requires(no_dot(ToSeq(name)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(configured), 1 / 2))
@@ -109,56 +107,39 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if len(configured) > 0 and exact:
+    if len(configured) > 0:
         i = 0
         while i < len(configured):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(len(configured) > 0 and exact)
             Invariant(0 <= i and i <= len(configured))
             Invariant(ToSeq(result) == ToSeq(configured).take(i))
-            Invariant(MustTerminate(len(configured) - i + 1))
-            # invariants-end
             result = result + [configured[i]]
             i = i + 1
         Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
-        Assert(ToSeq(result) == ToSeq(configured))
         return result
     else:
         i = 0
         while i < len(module):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= i and i <= len(module))
             Invariant(ToSeq(result) == ToSeq(module).take(i))
-            Invariant(MustTerminate(len(module) - i + 1))
-            # invariants-end
             result = result + [module[i]]
             i = i + 1
         Assert(ToSeq(module).take(len(module)) == ToSeq(module))
         result = result + [DOT()]
         j = 0
         while j < len(name):
-            # invariants-start
             Invariant(Acc(list_pred(configured), 1 / 2))
             Invariant(Acc(list_pred(module), 1 / 2))
             Invariant(Acc(list_pred(name), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(not (len(configured) > 0 and exact))
             Invariant(0 <= j and j <= len(name))
             Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
-            Invariant(MustTerminate(len(name) - j + 1))
-            # invariants-end
             result = result + [name[j]]
             j = j + 1
         Assert(ToSeq(name).take(len(name)) == ToSeq(name))
-        Assert(ToSeq(result) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
-        Assert(qualified(ToSeq(module), ToSeq(name)) ==
-               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
         return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15161.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deconstructible expression node reports an import path for serialization.
  When the node declares a canonical import path and is exactly that declared
  type, the reported path is that canonical path verbatim. Otherwise the node
  falls back to the dotted qualified name `module "." name` derived from where
  its class happens to live.

  The expression nodes addressed here declare a canonical path rooted directly
  at the public `django.db.models` package (e.g. `django.db.models.Value`),
  rather than reporting the longer dotted name of whichever internal submodule
  they happen to be defined in. A path rooted at the public package is exactly
  the condition under which a migration serializer emits the short `models.X`
  reference (with a single `from django.db import models` import) instead of
  importing that internal submodule.

Strings (import paths, module, class name) are modelled as `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
by `PSeq[int]`. The path choice and the public-package-rooting check are
expressible directly, so they are modelled DEEPLY and verified — there are no
consumed axioms. The deep rooting model is validated == the real serializer
rooting test out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms: the modeled behaviour is fully expressible
#  over List[int]/PSeq[int]. The deep rooting model `serialized_module_rooted`
#  is an A-reference, validated == the real serializer by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def DOT() -> int:
    # ord('.')
    return 46


@Pure
def public_root() -> PSeq[int]:
    """The public package prefix INCLUDING its trailing dot:
    'django.db.models.' as code points. A reported path is short-form-eligible
    iff it equals this prefix followed by a single dot-free leaf name."""
    return PSeq(100, 106, 97, 110, 103, 111, 46, 100, 98, 46,
               109, 111, 100, 101, 108, 115, 46)


@Pure
def qualified(module: PSeq[int], name: PSeq[int]) -> PSeq[int]:
    """The dotted qualified-name fallback: `module "." name`."""
    return module + PSeq(DOT()) + name


@Pure
def no_dot(s: PSeq[int]) -> bool:
    """True iff `s` contains no '.' code point (a single path component)."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                          s[k] != DOT())))


@Pure
def serialized_module_rooted(p: PSeq[int]) -> bool:
    """Deep model of the serializer's rooting test: `p` reduces to the short
    `models.<leaf>` form iff its component before the LAST dot is exactly the
    public `django.db.models` package. Equivalently: `p` begins with the
    `django.db.models.` prefix and the remaining leaf carries no further dot."""
    return (len(p) > len(public_root()) and
            p.take(len(public_root())) == public_root() and
            no_dot(p.drop(len(public_root()))))
# pure-end


def deconstruct_path(configured: List[int], exact: bool,
                     module: List[int], name: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(configured), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(name), 1 / 2))
    # The class name component carries no embedded dot (it is a single leaf).
    Requires(no_dot(ToSeq(name)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(configured), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When a canonical path is configured AND the node is exactly that type,
    # the reported path is that canonical path verbatim.
    Ensures(Implies(len(configured) > 0 and exact,
                    ToSeq(Result()) == ToSeq(configured)))
    # Otherwise it is the dotted qualified-name fallback.
    Ensures(Implies(not (len(configured) > 0 and exact),
                    ToSeq(Result()) == qualified(ToSeq(module), ToSeq(name))))
    # The reported path is short-form-eligible (rooted at the public package)
    # exactly as the chosen branch dictates.
    Ensures(serialized_module_rooted(ToSeq(Result())) ==
            (serialized_module_rooted(ToSeq(configured))
             if (len(configured) > 0 and exact)
             else serialized_module_rooted(qualified(ToSeq(module), ToSeq(name)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if len(configured) > 0 and exact:
        i = 0
        while i < len(configured):
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(configured) > 0 and exact)
            Invariant(0 <= i and i <= len(configured))
            Invariant(ToSeq(result) == ToSeq(configured).take(i))
            result = result + [configured[i]]
            i = i + 1
        Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
        Assert(ToSeq(result) == ToSeq(configured))
        return result
    else:
        i = 0
        while i < len(module):
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= i and i <= len(module))
            Invariant(ToSeq(result) == ToSeq(module).take(i))
            result = result + [module[i]]
            i = i + 1
        Assert(ToSeq(module).take(len(module)) == ToSeq(module))
        result = result + [DOT()]
        j = 0
        while j < len(name):
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= j and j <= len(name))
            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
            result = result + [name[j]]
            j = j + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(ToSeq(result) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        Assert(qualified(ToSeq(module), ToSeq(name)) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15161 (nagini). Command form: `python -m swebench_unified.adversary weakness nagini django__django-15161 <atk>.py` (run 3-concurrent, ≤3 JVMs). All same-spec verified byte-identical (adversary same-spec exit 0 for all 7 attacks + pos_control + prepatch).

SPEC SHAPE: the postconditions pin Result() EXACTLY over both exhaustive, complementary branches — Ensures(Implies(len(configured)>0 and exact, ToSeq(Result())==ToSeq(configured))) and Ensures(Implies(not(...), ToSeq(Result())==qualified(module,name))) — plus a derived rooting-flag postcondition. Because output is fully determined on the whole domain, no behaviorally-wrong impl can verify.

ATTACKS (all wrong impls, edited ONLY in impl region; each weakness exit=2 = NOT-A-COUNTEREXAMPLE, spec rejected → verification failed, not crash/timeout):
- atk_1 ungrounded-oracle echo: always return configured (ignores branch) → exit 2
- atk_2 control-flow-effect: branch selector NEGATED → exit 2
- atk_3 boundary: then-branch drops last char of configured (i<len-1) → exit 2
- atk_4 fallback swaps module/name (name '.' module) → exit 2
- atk_5 fallback drops the '.' separator (module+name) → exit 2
- atk_6 effect: extra DOT appended to configured in then-branch → exit 2
- atk_7 partial-domain: weakened selector `if len(configured)>0` (ignores exact) → exit 2
ZERO CANDIDATES: no attack shares spec AND verifies, so no faithful refined patch needed materializing and no run_resolve was required.

CONTROLS: pos_control.py (gold model.py) `bash scripts/nagini_verify.sh` exit 0 (Verification successful, 14.47s). prepatch.py (model_prepatch.py) exit 1, failing exactly Implies(len(configured)>0 and exact, ToSeq(Result())==ToSeq(configured)) — bug reproduced, spec senses the change.

REFINEMENT.md AUDIT: legs B1(R), B2(I under R), B3(R), B4(A-reference). No @ContractOnly consumed axioms; NO kind-3/ungrounded-oracle leg — the behavior the patch steers (which path the node reports) is modeled DEEPLY in verified postconditions, not hidden behind an axiom. The single A-reference (serialized_module_rooted ↔ real DeconstructableSerializer._serialize_path rooting test) is validated == real callee by axiom_check.py/G-AX and is NOT load-bearing for output correctness (postconditions pin Result exactly; rooting flag is a derived cross-check that cannot mask a wrong output). Known empty-leaf 'django.db.models.' divergence is out-of-domain (Requires(no_dot(name)) + always-non-empty leaf) — a dispositioned G-PANEL-2 matter, not a G-EQ break. Correspondence of both A-legs to the real callees holds.

Verdict SOUND: 7 distinct wrong impls run through the harness, none verifies; positive control verifies; prepatch bug reproduced.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15161.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deconstructible expression node reports an import path for serialization.
  When the node declares a canonical import path and is exactly that declared
  type, the reported path is that canonical path verbatim. Otherwise the node
  falls back to the dotted qualified name `module "." name` derived from where
  its class happens to live.

  The expression nodes addressed here declare a canonical path rooted directly
  at the public `django.db.models` package (e.g. `django.db.models.Value`),
  rather than reporting the longer dotted name of whichever internal submodule
  they happen to be defined in. A path rooted at the public package is exactly
  the condition under which a migration serializer emits the short `models.X`
  reference (with a single `from django.db import models` import) instead of
  importing that internal submodule.

Strings (import paths, module, class name) are modelled as `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
by `PSeq[int]`. The path choice and the public-package-rooting check are
expressible directly, so they are modelled DEEPLY and verified — there are no
consumed axioms. The deep rooting model is validated == the real serializer
rooting test out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms: the modeled behaviour is fully expressible
#  over List[int]/PSeq[int]. The deep rooting model `serialized_module_rooted`
#  is an A-reference, validated == the real serializer by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def DOT() -> int:
    # ord('.')
    return 46


@Pure
def public_root() -> PSeq[int]:
    """The public package prefix INCLUDING its trailing dot:
    'django.db.models.' as code points. A reported path is short-form-eligible
    iff it equals this prefix followed by a single dot-free leaf name."""
    return PSeq(100, 106, 97, 110, 103, 111, 46, 100, 98, 46,
               109, 111, 100, 101, 108, 115, 46)


@Pure
def qualified(module: PSeq[int], name: PSeq[int]) -> PSeq[int]:
    """The dotted qualified-name fallback: `module "." name`."""
    return module + PSeq(DOT()) + name


@Pure
def no_dot(s: PSeq[int]) -> bool:
    """True iff `s` contains no '.' code point (a single path component)."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                          s[k] != DOT())))


@Pure
def serialized_module_rooted(p: PSeq[int]) -> bool:
    """Deep model of the serializer's rooting test: `p` reduces to the short
    `models.<leaf>` form iff its component before the LAST dot is exactly the
    public `django.db.models` package. Equivalently: `p` begins with the
    `django.db.models.` prefix and the remaining leaf carries no further dot."""
    return (len(p) > len(public_root()) and
            p.take(len(public_root())) == public_root() and
            no_dot(p.drop(len(public_root()))))
# pure-end


def deconstruct_path(configured: List[int], exact: bool,
                     module: List[int], name: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(configured), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(name), 1 / 2))
    # The class name component carries no embedded dot (it is a single leaf).
    Requires(no_dot(ToSeq(name)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(configured), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When a canonical path is configured AND the node is exactly that type,
    # the reported path is that canonical path verbatim.
    Ensures(Implies(len(configured) > 0 and exact,
                    ToSeq(Result()) == ToSeq(configured)))
    # Otherwise it is the dotted qualified-name fallback.
    Ensures(Implies(not (len(configured) > 0 and exact),
                    ToSeq(Result()) == qualified(ToSeq(module), ToSeq(name))))
    # The reported path is short-form-eligible (rooted at the public package)
    # exactly as the chosen branch dictates.
    Ensures(serialized_module_rooted(ToSeq(Result())) ==
            (serialized_module_rooted(ToSeq(configured))
             if (len(configured) > 0 and exact)
             else serialized_module_rooted(qualified(ToSeq(module), ToSeq(name)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if len(configured) > 0 and exact:
        i = 0
        while i < len(configured):
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(configured) > 0 and exact)
            Invariant(0 <= i and i <= len(configured))
            Invariant(ToSeq(result) == ToSeq(configured).take(i))
            result = result + [configured[i]]
            i = i + 1
        Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
        Assert(ToSeq(result) == ToSeq(configured))
        return result
    else:
        i = 0
        while i < len(module):
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= i and i <= len(module))
            Invariant(ToSeq(result) == ToSeq(module).take(i))
            result = result + [module[i]]
            i = i + 1
        Assert(ToSeq(module).take(len(module)) == ToSeq(module))
        result = result + [DOT()]
        j = 0
        while j < len(name):
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= j and j <= len(name))
            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
            result = result + [name[j]]
            j = j + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(ToSeq(result) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        Assert(qualified(ToSeq(module), ToSeq(name)) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15161 (nagini). Command form: `python -m swebench_unified.adversary weakness nagini django__django-15161 <atk>.py` (run 3-concurrent, ≤3 JVMs). All same-spec verified byte-identical (adversary same-spec exit 0 for all 7 attacks + pos_control + prepatch).

SPEC SHAPE: the postconditions pin Result() EXACTLY over both exhaustive, complementary branches — Ensures(Implies(len(configured)>0 and exact, ToSeq(Result())==ToSeq(configured))) and Ensures(Implies(not(...), ToSeq(Result())==qualified(module,name))) — plus a derived rooting-flag postcondition. Because output is fully determined on the whole domain, no behaviorally-wrong impl can verify.

ATTACKS (all wrong impls, edited ONLY in impl region; each weakness exit=2 = NOT-A-COUNTEREXAMPLE, spec rejected → verification failed, not crash/timeout):
- atk_1 ungrounded-oracle echo: always return configured (ignores branch) → exit 2
- atk_2 control-flow-effect: branch selector NEGATED → exit 2
- atk_3 boundary: then-branch drops last char of configured (i<len-1) → exit 2
- atk_4 fallback swaps module/name (name '.' module) → exit 2
- atk_5 fallback drops the '.' separator (module+name) → exit 2
- atk_6 effect: extra DOT appended to configured in then-branch → exit 2
- atk_7 partial-domain: weakened selector `if len(configured)>0` (ignores exact) → exit 2
ZERO CANDIDATES: no attack shares spec AND verifies, so no faithful refined patch needed materializing and no run_resolve was required.

CONTROLS: pos_control.py (gold model.py) `bash scripts/nagini_verify.sh` exit 0 (Verification successful, 14.47s). prepatch.py (model_prepatch.py) exit 1, failing exactly Implies(len(configured)>0 and exact, ToSeq(Result())==ToSeq(configured)) — bug reproduced, spec senses the change.

REFINEMENT.md AUDIT: legs B1(R), B2(I under R), B3(R), B4(A-reference). No @ContractOnly consumed axioms; NO kind-3/ungrounded-oracle leg — the behavior the patch steers (which path the node reports) is modeled DEEPLY in verified postconditions, not hidden behind an axiom. The single A-reference (serialized_module_rooted ↔ real DeconstructableSerializer._serialize_path rooting test) is validated == real callee by axiom_check.py/G-AX and is NOT load-bearing for output correctness (postconditions pin Result exactly; rooting flag is a derived cross-check that cannot mask a wrong output). Known empty-leaf 'django.db.models.' divergence is out-of-domain (Requires(no_dot(name)) + always-non-empty leaf) — a dispositioned G-PANEL-2 matter, not a G-EQ break. Correspondence of both A-legs to the real callees holds.

Verdict SOUND: 7 distinct wrong impls run through the harness, none verifies; positive control verifies; prepatch bug reproduced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: the path-selecting body of the UNCHANGED django.utils.deconstruct.deconstructible.deconstruct (deconstruct.py:26-29,42-48). Faithfulness checked three ways against the REAL repo at base_commit (worktree):

1) IN-DOMAIN CONFORMANCE (empirical): ran the bundle's own conformance_check.py repointed at the base repo -> {"checked":100000,"failures":0}. Shadow == real reported path on all boundary cases (six F2P (configured,module,name) triples with exact True/False, plus no-configured fallbacks) and 100k pinned-seed fuzz inputs. Zero disagreements.

2) FALLBACK BRANCH: exact=False / empty configured -> real returns f'{obj.__class__.__module__}.{name}', model returns module+'.'+name; harness sets the subclass __module__/__qualname__ accordingly and they match.

3) OUT-OF-DOMAIN PROBES: For dotless or unresolvable `configured` with exact=True the spec postcondition (Result==configured) disagrees with the real callee, which raises ValueError via its import_module/hasattr serializability guard (deconstruct.py:32-41). But: the spec is deliberately scoped to the path CHOICE (mapping.md §1; conformance INPUT DOMAIN note documents the resolvability guard as orthogonal), and every real @deconstructible(path=...) value is a dotted, resolvable import path — the divergent inputs never arise. On the entire resolution-relevant domain and all F2P inputs the model exactly matches the real callee, so verify(model) => resolves holds. Spec-region byte-identical (same-spec exit 0). No consumed axioms; the two deep-model A-references (serialized_module_rooted, deconstruct_path choice) are the ones exercised by G-AX/G-CONF.

Conclusion: FAITHFUL — the model neither drifts from nor is too strong relative to the real callee on any input that affects resolution.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 leakage / gold-reconstruction review for django__django-15161 (nagini). Lexical G-LEAK screen PASSES (verified: leakage.screen -> passed=True, no diff markers, no reproduced gold-patch line, no patched file/module path, no narration; changed-symbol set {as_sql, copy, get_group_by_cols, relabeled_clone, repr, select_format} are incidental hunk-context defs, none echoed by a spec-view identifier or comment).

Semantic assessment against the SOLVER-VISIBLE problem_statement only (NOT hints_text): the public problem_statement already discloses the entire task substance — deconstruct should emit the simplified public form (django.db.models.F() rather than django.db.models.expressions.F()), that this public-package rooting enables the short `from django.db import models` / `models.F()` migration form, and that the technique (PR #14047, applied to F) should be applied to OTHER expression nodes. 

The spec view stays strictly at the behavioral level: it describes the desired outcome ("declare a canonical path... report it verbatim, else dotted qualified fallback"; "rooted directly at the public django.db.models package... the condition under which a migration serializer emits the short models.X reference") and models it as deconstruct_path over List[int] with the serialized_module_rooted predicate. It does NOT reveal the concrete gold edit beyond the public task: it never names the patched file (expressions.py), the decorator (@deconstructible), the path= kwarg, nor does it enumerate the six target classes (Func/Value/ExpressionWrapper/When/Case/OrderBy). The single concrete token `django.db.models.Value` appears only as an illustrative example of public-rooting — directly parallel to the problem_statement's own `django.db.models.F` example — and does not enable reconstructing which classes/file/mechanism the patch touches. 

The 'canonical path configured + exact type => report verbatim, else fallback' behavior is the pre-existing @deconstructible semantics that PR #14047 (public) already relies on, not new edit-localization. Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
