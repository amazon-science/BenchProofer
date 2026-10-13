# P2 adversarial audit — pydata__xarray-4966

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -170,48 +168,36 @@
     # impl-start
     result = []  # type: List[int]
     if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
         i = len(data)
         while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(data), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(data))
-            Invariant(ToSeq(result) ==
-                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
-            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [reinterpret(data[i - 1], modulus, True)] + result
-            i = i - 1
-    elif transform_to_unsigned(kind, unsigned):
-        # signed-stored array, requested unsigned -> unsigned view of each elem
-        i = len(data)
-        while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
+            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
+            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
+            result = [reinterpret(data[i - 1], modulus, False)] + result
+            i = i - 1
+    elif transform_to_unsigned(kind, unsigned):
+        i = len(data)
+        while i > 0:
+            Invariant(Acc(list_pred(data), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= len(data))
+            Invariant(ToSeq(result) ==
+                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, False)] + result
             i = i - 1
     else:
-        # request matches storage or is absent/uninterpretable: pass through
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [data[i - 1]] + result
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -170,48 +168,35 @@
     # impl-start
     result = []  # type: List[int]
     if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
-            Invariant(ToSeq(result) ==
-                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
+            Invariant(ToSeq(result) == ToSeq(data).drop(i))
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [reinterpret(data[i - 1], modulus, True)] + result
+            result = [data[i - 1]] + result
             i = i - 1
     elif transform_to_unsigned(kind, unsigned):
-        # signed-stored array, requested unsigned -> unsigned view of each elem
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, False)] + result
             i = i - 1
     else:
-        # request matches storage or is absent/uninterpretable: pass through
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [data[i - 1]] + result
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -170,48 +168,36 @@
     # impl-start
     result = []  # type: List[int]
     if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
         i = len(data)
-        while i > 0:
-            # invariants-start
+        while i > 1:
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(data))
+            Invariant(1 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, True)] + result
             i = i - 1
     elif transform_to_unsigned(kind, unsigned):
-        # signed-stored array, requested unsigned -> unsigned view of each elem
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, False)] + result
             i = i - 1
     else:
-        # request matches storage or is absent/uninterpretable: pass through
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [data[i - 1]] + result
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -169,49 +167,37 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
+    if transform_to_unsigned(kind, unsigned):
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, True)] + result
             i = i - 1
-    elif transform_to_unsigned(kind, unsigned):
-        # signed-stored array, requested unsigned -> unsigned view of each elem
+    elif transform_to_signed(kind, unsigned):
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
-                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
+                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [reinterpret(data[i - 1], modulus, False)] + result
+            result = [reinterpret(data[i - 1], modulus, True)] + result
             i = i - 1
     else:
-        # request matches storage or is absent/uninterpretable: pass through
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [data[i - 1]] + result
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -170,48 +168,35 @@
     # impl-start
     result = []  # type: List[int]
     if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, True)] + result
             i = i - 1
     elif transform_to_unsigned(kind, unsigned):
-        # signed-stored array, requested unsigned -> unsigned view of each elem
         i = len(data)
         while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(data), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(data))
-            Invariant(ToSeq(result) ==
-                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
-            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [reinterpret(data[i - 1], modulus, False)] + result
-            i = i - 1
-    else:
-        # request matches storage or is absent/uninterpretable: pass through
-        i = len(data)
-        while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
+            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
+            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
+            result = [data[i - 1]] + result
+            i = i - 1
+    else:
+        i = len(data)
+        while i > 0:
+            Invariant(Acc(list_pred(data), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= len(data))
+            Invariant(ToSeq(result) == ToSeq(data).drop(i))
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [data[i - 1]] + result
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -169,52 +167,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
-        i = len(data)
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(data), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(data))
-            Invariant(ToSeq(result) ==
-                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
-            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [reinterpret(data[i - 1], modulus, True)] + result
-            i = i - 1
-    elif transform_to_unsigned(kind, unsigned):
-        # signed-stored array, requested unsigned -> unsigned view of each elem
-        i = len(data)
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(data), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(data))
-            Invariant(ToSeq(result) ==
-                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
-            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [reinterpret(data[i - 1], modulus, False)] + result
-            i = i - 1
-    else:
-        # request matches storage or is absent/uninterpretable: pass through
-        i = len(data)
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(data), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(data))
-            Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
-            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [data[i - 1]] + result
-            i = i - 1
     return result
     # impl-end
```

Attack 7 — `atk7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -169,49 +167,39 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
+    to_sig = transform_to_signed(kind, unsigned)
+    to_uns = transform_to_unsigned(kind, unsigned)
+    if to_sig:
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, True)] + result
             i = i - 1
-    elif transform_to_unsigned(kind, unsigned):
-        # signed-stored array, requested unsigned -> unsigned view of each elem
+    elif to_uns:
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [reinterpret(data[i - 1], modulus, False)] + result
             i = i - 1
     else:
-        # request matches storage or is absent/uninterpretable: pass through
         i = len(data)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(data), 1 / 2))
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
             result = [data[i - 1]] + result
```

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -138,7 +137,6 @@
     Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
              unsigned == ATTR_OTHER)
     Requires(modulus >= 2)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(data), 1 / 2))
@@ -168,24 +166,13 @@
                     fill_out(kind, unsigned, modulus, fill) == fill))
     # post-conditions-end
     # impl-start
+    # PRE-PATCH SKELETON (buggy): only signed-stored arrays are reconciled
+    # against the requested signedness; an unsigned-stored array whose request
+    # asks for the signed view is NOT handled and falls through to the
+    # pass-through arm below, leaving the (still-unsigned) element values
+    # unchanged. This is the missing branch the fix adds.
     result = []  # type: List[int]
-    if transform_to_signed(kind, unsigned):
-        # unsigned-stored array, requested signed -> signed view of each element
-        i = len(data)
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(data), 1 / 2))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= i and i <= len(data))
-            Invariant(ToSeq(result) ==
-                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
-            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
-            result = [reinterpret(data[i - 1], modulus, True)] + result
-            i = i - 1
-    elif transform_to_unsigned(kind, unsigned):
+    if transform_to_unsigned(kind, unsigned):
         # signed-stored array, requested unsigned -> unsigned view of each elem
         i = len(data)
         while i > 0:
@@ -195,7 +182,6 @@
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) ==
                       reinterpret_seq(ToSeq(data).drop(i), modulus, False))
-            Invariant(MustTerminate(i + 1))
             # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
@@ -210,7 +196,6 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= i and i <= len(data))
             Invariant(ToSeq(result) == ToSeq(data).drop(i))
-            Invariant(MustTerminate(i + 1))
             # invariants-end
             Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
             Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-4966.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A fixed-width integer array carries a stored signedness (its element values
  are either the unsigned or the signed view of a bit pattern of a known width)
  together with a requested target signedness supplied out of band. The decode
  operation reconciles the two: when the stored signedness disagrees with the
  request, every element is reinterpreted as the OTHER view of the same bit
  pattern of that width; otherwise the elements pass through unchanged. The two
  cases that disagree are symmetric:

    * a SIGNED-stored array whose request is "treat as unsigned" -> each element
      is mapped to its unsigned view (a negative value v becomes v + 2**bits);
    * an UNSIGNED-stored array whose request is "treat as signed" -> each element
      is mapped to its signed view (a value v at or above the half-range
      2**(bits-1) becomes v - 2**bits, so the maximum representable value
      becomes -1).

  In every other configuration -- request matching the stored signedness, or an
  absent/uninterpretable request -- the element values are returned unchanged.
  When a sentinel fill value accompanies the array, it is reinterpreted by the
  very same fixed-width rule whenever (and only whenever) the elements are.

The reinterpretation is the two's-complement correspondence between the signed
and unsigned views of one fixed-width integer: writing `modulus = 2**bits`, the
unsigned view of v is `v mod modulus` and the signed view of v is
`((v + modulus/2) mod modulus) - modulus/2`. The width is conveyed as that
`modulus` (a power of two, at least 2).

Integer values are modelled directly as `int` (this is an integer-domain
behaviour, not a floating-point one); a data array is a `List[int]` of its
per-element values. The fixed-width reinterpretation `reinterpret` is modelled
deeply as a verified arithmetic function, whose equality to the real
element-wise array conversion is checked out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms: the only opaque callee is the *changed*
#  element transform, which is therefore modelled deeply below -- an
#  A-reference validated against the real array conversion by axiom_check.py,
#  per SPEC_GUIDE section 3 -- rather than axiomatized.)
# axioms-end


# pure-start
# Stored signedness of the incoming array.
KIND_SIGNED = 0
KIND_UNSIGNED = 1
# Requested target signedness (the out-of-band attribute).
ATTR_FALSE = 0
ATTR_TRUE = 1
ATTR_OTHER = 2


@Pure
def reinterpret(v: int, modulus: int, to_signed: bool) -> int:
    """The fixed-width reinterpretation of one integer between the signed and
    unsigned views of the same bit pattern. `modulus == 2**bits`.

    * to_signed: produce the signed view -- values at/above the half-range fold
      down by `modulus`, so the unsigned maximum `modulus-1` becomes `-1`.
    * not to_signed: produce the unsigned view -- negative values fold up by
      `modulus`, so `-1` becomes `modulus-1`.
    """
    Requires(modulus >= 2)
    if to_signed:
        if v >= modulus // 2:
            return v - modulus
        return v
    else:
        if v < 0:
            return v + modulus
        return v


@Pure
def reinterpret_seq(s: PSeq[int], modulus: int, to_signed: bool) -> PSeq[int]:
    """Element-wise reinterpretation of a whole array, front-recursive so a
    single unfold is available to callers per loop step."""
    Requires(modulus >= 2)
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(reinterpret(s[0], modulus, to_signed)) + \
        reinterpret_seq(s.drop(1), modulus, to_signed)


@Pure
def transform_to_signed(kind: int, unsigned: int) -> bool:
    """The decode produces the SIGNED view exactly when an unsigned-stored array
    is requested to be treated as signed."""
    return kind == KIND_UNSIGNED and unsigned == ATTR_FALSE


@Pure
def transform_to_unsigned(kind: int, unsigned: int) -> bool:
    """The decode produces the UNSIGNED view exactly when a signed-stored array
    is requested to be treated as unsigned."""
    return kind == KIND_SIGNED and unsigned == ATTR_TRUE


@Pure
def is_transformed(kind: int, unsigned: int) -> bool:
    """Whether decode reinterprets the elements at all."""
    return transform_to_signed(kind, unsigned) or \
        transform_to_unsigned(kind, unsigned)


@Pure
def fill_out(kind: int, unsigned: int, modulus: int, fill: int) -> int:
    """The decoded sentinel fill value: reinterpreted by the same fixed-width
    rule as the elements when the array is transformed, else unchanged. Stated
    as a pure projection so the postconditions can pin it without a second
    mutable output."""
    Requires(modulus >= 2)
    if transform_to_signed(kind, unsigned):
        return reinterpret(fill, modulus, True)
    elif transform_to_unsigned(kind, unsigned):
        return reinterpret(fill, modulus, False)
    else:
        return fill
# pure-end


def reconcile_signedness(data: List[int], kind: int, unsigned: int,
                         modulus: int, has_fill: bool,
                         fill: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(data), 1 / 2))
    Requires(kind == KIND_SIGNED or kind == KIND_UNSIGNED)
    Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
             unsigned == ATTR_OTHER)
    Requires(modulus >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(data), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The decoded array is the element-wise fixed-width reinterpretation when
    # the request disagrees with the stored signedness, else the array
    # unchanged. The signed-view case (unsigned-stored, requested signed) is the
    # behaviour the issue demands; the unsigned-view case is its symmetric
    # counterpart; every other configuration is a pass-through.
    Ensures(Implies(transform_to_signed(kind, unsigned),
                    ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus,
                                                       True)))
    Ensures(Implies(transform_to_unsigned(kind, unsigned),
                    ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus,
                                                       False)))
    Ensures(Implies(not is_transformed(kind, unsigned),
                    ToSeq(Result()) == ToSeq(data)))
    # The sentinel fill value is reinterpreted by exactly the same rule iff the
    # elements are (and is reported alongside the decoded array).
    Ensures(Implies(has_fill and transform_to_signed(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) ==
                    reinterpret(fill, modulus, True)))
    Ensures(Implies(has_fill and transform_to_unsigned(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) ==
                    reinterpret(fill, modulus, False)))
    Ensures(Implies(has_fill and not is_transformed(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) == fill))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for pydata__xarray-4966 (nagini). Scratch: Env: python, SBU_BENCHMARK_DIR=benchmark-verified (adversary.py's own argparse does NOT consume --benchmark-dir; must use env var).

SPEC TIGHTNESS: The three postconditions on ToSeq(Result()) — transform_to_signed→reinterpret_seq(...,True), transform_to_unsigned→reinterpret_seq(...,False), and (not is_transformed)→ToSeq(data) — form a COMPLETE partition of (kind,unsigned) and each pins the returned sequence EXACTLY. So the output list is fully determined for every input configuration; no verifying impl can emit wrong element data. Fill handling lives entirely in the frozen @Pure fill_out (spec region) and the impl never touches the fill, so an impl-only edit cannot vary fill behavior either. Surface for a verifying-but-wrong impl is therefore nil.

ATTACKS (all same-spec confirmed exit 0; commands: `python -m swebench_unified.adversary weakness nagini pydata__xarray-4966 <path>`):
- atk1 wrong-direction (signed branch produces unsigned view, internally-consistent invariant): weakness exit 2 — verification failed (spec rejected). GOOD.
- atk2 identity/missing-transform in signed branch: exit 2 rejected.
- atk3 boundary off-by-one (while i>1, drops element 0 in signed branch): exit 2 rejected.
- atk4 dispatch-swap (control-flow-effect, signed/unsigned branch order swapped): exit 2 rejected.
- atk5 identity in transform_to_unsigned branch (symmetric partial-domain): exit 2 rejected.
- atk6 ungrounded/constant-oracle echo (return [] always): exit 2 rejected.
- atk_prepatch (the known prepatch bug: unsigned-stored+false falls through to pass-through, PREPATCH REPRODUCED): weakness exit 2 — does NOT verify, i.e. the spec senses the change (G-DIFF confirmed). GOOD.
- atk7 correct echo (behaviorally the gold impl, distinct concrete form using to_sig/to_uns locals): weakness exit 0 = CANDIDATE (shares spec AND verifies, 16.3s).

CANDIDATE RESOLVE (mandatory): atk7's faithful refined patch onto xarray/coding/variables.py is exactly the gold hunk (atk7 decodes correctly in all four dispatch quadrants). Materialized as atk7_faithful_patch.diff and RUN through the official harness via harness.run_resolve('pydata__xarray-4966', patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1 (resolve_atk7.json). The only verifying wrong-impl candidate RESOLVES, so it does NOT break the spec.

POSITIVE CONTROL: positive_control.py (= bundle model.py) verifies (nagini_verify.sh exit 0).

REFINEMENT.MD AUDIT: legs A1–A4,A9,A10 = R (type refinement: numpy fixed-width int array↔List[int] of values, dtype.kind↔kind∈{0,1}, popped _Unsigned string↔unsigned∈{0,1,2}, dtype.itemsize↔modulus=2**bits, warn/Variable/lazy_elemwise_func identities on observed elements). A5,A6 = I (identical integer/equality dispatch). A7,A8 = A-reference: the ONLY genuinely-changed callee (element-wise np.asarray(dtype=...) / dtype.type(fill)) is modelled DEEPLY by reinterpret/reinterpret_seq/fill_out, NOT consumed as an axiom (axioms region is empty — confirmed). Its correspondence to the real callee is validated out-of-band by axiom_check.py (G-AX): exhaustive 8+16-bit domains both directions + 8/16/32/64-bit boundaries + 80k fuzz + F2P max→-1 witnesses (211636 checks pass per verdict.md). NO kind-3 (unexpressible-changed-op) legs. A-reference correspondence holds. Consistent with mapping.md §3.1.

VERDICT: SOUND. 8 same-spec attacks run (6 distinct-flavor wrong impls: wrong-direction, missing-transform, boundary off-by-one, dispatch-swap, symmetric-partial-domain, ungrounded-echo; plus prepatch and correct-echo). Every wrong-DATA impl is rejected by the verifier; the sole verifying candidate is behaviorally the gold and its materialized faithful patch RESOLVES under the official harness. verify⇏correct is NOT exhibited — the spec admits no verifying incorrect implementation on this surface.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-4966.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A fixed-width integer array carries a stored signedness (its element values
  are either the unsigned or the signed view of a bit pattern of a known width)
  together with a requested target signedness supplied out of band. The decode
  operation reconciles the two: when the stored signedness disagrees with the
  request, every element is reinterpreted as the OTHER view of the same bit
  pattern of that width; otherwise the elements pass through unchanged. The two
  cases that disagree are symmetric:

    * a SIGNED-stored array whose request is "treat as unsigned" -> each element
      is mapped to its unsigned view (a negative value v becomes v + 2**bits);
    * an UNSIGNED-stored array whose request is "treat as signed" -> each element
      is mapped to its signed view (a value v at or above the half-range
      2**(bits-1) becomes v - 2**bits, so the maximum representable value
      becomes -1).

  In every other configuration -- request matching the stored signedness, or an
  absent/uninterpretable request -- the element values are returned unchanged.
  When a sentinel fill value accompanies the array, it is reinterpreted by the
  very same fixed-width rule whenever (and only whenever) the elements are.

The reinterpretation is the two's-complement correspondence between the signed
and unsigned views of one fixed-width integer: writing `modulus = 2**bits`, the
unsigned view of v is `v mod modulus` and the signed view of v is
`((v + modulus/2) mod modulus) - modulus/2`. The width is conveyed as that
`modulus` (a power of two, at least 2).

Integer values are modelled directly as `int` (this is an integer-domain
behaviour, not a floating-point one); a data array is a `List[int]` of its
per-element values. The fixed-width reinterpretation `reinterpret` is modelled
deeply as a verified arithmetic function, whose equality to the real
element-wise array conversion is checked out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms: the only opaque callee is the *changed*
#  element transform, which is therefore modelled deeply below -- an
#  A-reference validated against the real array conversion by axiom_check.py,
#  per SPEC_GUIDE section 3 -- rather than axiomatized.)
# axioms-end


# pure-start
# Stored signedness of the incoming array.
KIND_SIGNED = 0
KIND_UNSIGNED = 1
# Requested target signedness (the out-of-band attribute).
ATTR_FALSE = 0
ATTR_TRUE = 1
ATTR_OTHER = 2


@Pure
def reinterpret(v: int, modulus: int, to_signed: bool) -> int:
    """The fixed-width reinterpretation of one integer between the signed and
    unsigned views of the same bit pattern. `modulus == 2**bits`.

    * to_signed: produce the signed view -- values at/above the half-range fold
      down by `modulus`, so the unsigned maximum `modulus-1` becomes `-1`.
    * not to_signed: produce the unsigned view -- negative values fold up by
      `modulus`, so `-1` becomes `modulus-1`.
    """
    Requires(modulus >= 2)
    if to_signed:
        if v >= modulus // 2:
            return v - modulus
        return v
    else:
        if v < 0:
            return v + modulus
        return v


@Pure
def reinterpret_seq(s: PSeq[int], modulus: int, to_signed: bool) -> PSeq[int]:
    """Element-wise reinterpretation of a whole array, front-recursive so a
    single unfold is available to callers per loop step."""
    Requires(modulus >= 2)
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(reinterpret(s[0], modulus, to_signed)) + \
        reinterpret_seq(s.drop(1), modulus, to_signed)


@Pure
def transform_to_signed(kind: int, unsigned: int) -> bool:
    """The decode produces the SIGNED view exactly when an unsigned-stored array
    is requested to be treated as signed."""
    return kind == KIND_UNSIGNED and unsigned == ATTR_FALSE


@Pure
def transform_to_unsigned(kind: int, unsigned: int) -> bool:
    """The decode produces the UNSIGNED view exactly when a signed-stored array
    is requested to be treated as unsigned."""
    return kind == KIND_SIGNED and unsigned == ATTR_TRUE


@Pure
def is_transformed(kind: int, unsigned: int) -> bool:
    """Whether decode reinterprets the elements at all."""
    return transform_to_signed(kind, unsigned) or \
        transform_to_unsigned(kind, unsigned)


@Pure
def fill_out(kind: int, unsigned: int, modulus: int, fill: int) -> int:
    """The decoded sentinel fill value: reinterpreted by the same fixed-width
    rule as the elements when the array is transformed, else unchanged. Stated
    as a pure projection so the postconditions can pin it without a second
    mutable output."""
    Requires(modulus >= 2)
    if transform_to_signed(kind, unsigned):
        return reinterpret(fill, modulus, True)
    elif transform_to_unsigned(kind, unsigned):
        return reinterpret(fill, modulus, False)
    else:
        return fill
# pure-end


def reconcile_signedness(data: List[int], kind: int, unsigned: int,
                         modulus: int, has_fill: bool,
                         fill: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(data), 1 / 2))
    Requires(kind == KIND_SIGNED or kind == KIND_UNSIGNED)
    Requires(unsigned == ATTR_FALSE or unsigned == ATTR_TRUE or
             unsigned == ATTR_OTHER)
    Requires(modulus >= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(data), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The decoded array is the element-wise fixed-width reinterpretation when
    # the request disagrees with the stored signedness, else the array
    # unchanged. The signed-view case (unsigned-stored, requested signed) is the
    # behaviour the issue demands; the unsigned-view case is its symmetric
    # counterpart; every other configuration is a pass-through.
    Ensures(Implies(transform_to_signed(kind, unsigned),
                    ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus,
                                                       True)))
    Ensures(Implies(transform_to_unsigned(kind, unsigned),
                    ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus,
                                                       False)))
    Ensures(Implies(not is_transformed(kind, unsigned),
                    ToSeq(Result()) == ToSeq(data)))
    # The sentinel fill value is reinterpreted by exactly the same rule iff the
    # elements are (and is reported alongside the decoded array).
    Ensures(Implies(has_fill and transform_to_signed(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) ==
                    reinterpret(fill, modulus, True)))
    Ensures(Implies(has_fill and transform_to_unsigned(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) ==
                    reinterpret(fill, modulus, False)))
    Ensures(Implies(has_fill and not is_transformed(kind, unsigned),
                    fill_out(kind, unsigned, modulus, fill) == fill))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if transform_to_signed(kind, unsigned):
        # unsigned-stored array, requested signed -> signed view of each element
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, True))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, True)] + result
            i = i - 1
    elif transform_to_unsigned(kind, unsigned):
        # signed-stored array, requested unsigned -> unsigned view of each elem
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) ==
                      reinterpret_seq(ToSeq(data).drop(i), modulus, False))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [reinterpret(data[i - 1], modulus, False)] + result
            i = i - 1
    else:
        # request matches storage or is absent/uninterpretable: pass through
        i = len(data)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(data), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(data))
            Invariant(ToSeq(result) == ToSeq(data).drop(i))
            # invariants-end
            Assert(ToSeq(data).drop(i - 1)[0] == data[i - 1])
            Assert(ToSeq(data).drop(i - 1).drop(1) == ToSeq(data).drop(i))
            result = [data[i - 1]] + result
            i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for pydata__xarray-4966 (nagini). Scratch: Env: python, SBU_BENCHMARK_DIR=benchmark-verified (adversary.py's own argparse does NOT consume --benchmark-dir; must use env var).

SPEC TIGHTNESS: The three postconditions on ToSeq(Result()) — transform_to_signed→reinterpret_seq(...,True), transform_to_unsigned→reinterpret_seq(...,False), and (not is_transformed)→ToSeq(data) — form a COMPLETE partition of (kind,unsigned) and each pins the returned sequence EXACTLY. So the output list is fully determined for every input configuration; no verifying impl can emit wrong element data. Fill handling lives entirely in the frozen @Pure fill_out (spec region) and the impl never touches the fill, so an impl-only edit cannot vary fill behavior either. Surface for a verifying-but-wrong impl is therefore nil.

ATTACKS (all same-spec confirmed exit 0; commands: `python -m swebench_unified.adversary weakness nagini pydata__xarray-4966 <path>`):
- atk1 wrong-direction (signed branch produces unsigned view, internally-consistent invariant): weakness exit 2 — verification failed (spec rejected). GOOD.
- atk2 identity/missing-transform in signed branch: exit 2 rejected.
- atk3 boundary off-by-one (while i>1, drops element 0 in signed branch): exit 2 rejected.
- atk4 dispatch-swap (control-flow-effect, signed/unsigned branch order swapped): exit 2 rejected.
- atk5 identity in transform_to_unsigned branch (symmetric partial-domain): exit 2 rejected.
- atk6 ungrounded/constant-oracle echo (return [] always): exit 2 rejected.
- atk_prepatch (the known prepatch bug: unsigned-stored+false falls through to pass-through, PREPATCH REPRODUCED): weakness exit 2 — does NOT verify, i.e. the spec senses the change (G-DIFF confirmed). GOOD.
- atk7 correct echo (behaviorally the gold impl, distinct concrete form using to_sig/to_uns locals): weakness exit 0 = CANDIDATE (shares spec AND verifies, 16.3s).

CANDIDATE RESOLVE (mandatory): atk7's faithful refined patch onto xarray/coding/variables.py is exactly the gold hunk (atk7 decodes correctly in all four dispatch quadrants). Materialized as atk7_faithful_patch.diff and RUN through the official harness via harness.run_resolve('pydata__xarray-4966', patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1 (resolve_atk7.json). The only verifying wrong-impl candidate RESOLVES, so it does NOT break the spec.

POSITIVE CONTROL: positive_control.py (= bundle model.py) verifies (nagini_verify.sh exit 0).

REFINEMENT.MD AUDIT: legs A1–A4,A9,A10 = R (type refinement: numpy fixed-width int array↔List[int] of values, dtype.kind↔kind∈{0,1}, popped _Unsigned string↔unsigned∈{0,1,2}, dtype.itemsize↔modulus=2**bits, warn/Variable/lazy_elemwise_func identities on observed elements). A5,A6 = I (identical integer/equality dispatch). A7,A8 = A-reference: the ONLY genuinely-changed callee (element-wise np.asarray(dtype=...) / dtype.type(fill)) is modelled DEEPLY by reinterpret/reinterpret_seq/fill_out, NOT consumed as an axiom (axioms region is empty — confirmed). Its correspondence to the real callee is validated out-of-band by axiom_check.py (G-AX): exhaustive 8+16-bit domains both directions + 8/16/32/64-bit boundaries + 80k fuzz + F2P max→-1 witnesses (211636 checks pass per verdict.md). NO kind-3 (unexpressible-changed-op) legs. A-reference correspondence holds. Consistent with mapping.md §3.1.

VERDICT: SOUND. 8 same-spec attacks run (6 distinct-flavor wrong impls: wrong-direction, missing-transform, boundary off-by-one, dispatch-swap, symmetric-partial-domain, ungrounded-echo; plus prepatch and correct-echo). Every wrong-DATA impl is rejected by the verifier; the sole verifying candidate is behaviorally the gold and its materialized faithful patch RESOLVES under the official harness. verify⇏correct is NOT exhibited — the spec admits no verifying incorrect implementation on this surface.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of the nagini spec for pydata__xarray-4966 (UnsignedIntegerCoder.decode). CONCLUSION: FAITHFUL — the modeled spec agrees with the real patched repo callee on every realizable input; no diverging input found.

Method: I built a numpy<2/pandas<2 venv, imported the real patched xarray from the worktree (gold patch applied, base_commit 37522e99), and ran TWO independent checks:
(1) The bundle's own conformance_check.py against the live patched decode: 100384 probes, 0 disagreements.
(2) My own faithfulness probe that compares the SPEC's postcondition functions directly (reinterpret/reinterpret_seq element transform + fill_out) — NOT merely the impl shadow — against real coder.decode(var).values / decoded _FillValue, over 60480 inputs: exhaustive boundary cases for all 4 widths (8/16/32/64 bit) x both dtype kinds (i/u) x 5 attribute strings ('false','true','True','neither','') x array shapes x fills, plus 60000 seeded fuzz. Result: 0 divergences.

Branch coverage confirmed against reality: transform_to_signed (kind=u, unsigned='false') -> signed view (modulus-1 -> -1, the F2P behaviour); transform_to_unsigned (kind=i, unsigned='true') -> unsigned view (the pre-existing branch); every other config (matching/absent/uninterpretable _Unsigned, including case-mismatched 'True' and empty string -> ATTR_OTHER) -> pass-through, matching the real gold `else: warnings.warn` arm which leaves .values untouched. Fill handled identically iff elements are transformed.

Over-strength check: the only theoretical concern (Nagini Requires demands only modulus>=2, not value-in-range, so the carrier-domain restriction in mapping.md §2 could in principle be a place where the spec is defined on inputs the real callee can't see) is a non-issue: numpy fixed-width integer dtypes physically clamp/reject out-of-range values at array construction, so an out-of-carrier int has no real-repo counterpart and is not a faithfulness input. On every input the real repo can actually produce, spec == real. Spec is not too strong and does not drift. Also confirmed same-spec tool round-trips (SAME on model.py) and recorded G-AX/G-CONF/G-EQ all pass.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen PASSES on the consumer spec view (spec_view of model.py: docstring + axioms + pure regions + reconcile_signedness contract, impl excluded). No diff markers, no gold-patch lines reproduced, no patched file path/module (`xarray/coding/variables.py`), and the only distinctive changed symbol is `decode` (non-distinctive, not echoed by any spec-view identifier). Semantic check for panel-3: the public problem_statement is itself extremely explicit — it names the exact fix location (variables.py#L311), states the change to add verbatim ('if .kind == "u" and unsigned == False'), and shows the expected behavior (netcdf4 returns negative values, 255-style values -> negatives). So the gold edit's what/where/how is already public via the task. The spec view stays strictly at behavioral altitude and reveals nothing BEYOND that: it uses only abstract carriers (KIND_SIGNED/UNSIGNED, ATTR_FALSE/TRUE/OTHER, modulus, reinterpret/reinterpret_seq), frames everything as 'desired behaviour, not as an edit', and never mentions repo symbols (_Unsigned, dtype.kind, lazy_elemwise_func, SerializationWarning) or paths. The one behavioral detail arguably not spelled out in the problem_statement — that a sentinel fill value is reinterpreted by the same rule iff the elements are — is symmetric to code already present pre-patch (the existing i->u branch's _FillValue conversion, visible to any solver reading base_commit) and is stated as behavior, not as edit narration; it does not localize the gold change. refinement.md and mapping.md DO name variables.py, exact line numbers, and quote the gold hunk, but those are audit-only artifacts, NOT the solver-visible spec view, so they are out of scope for leakage. Conclusion: spec view does not leak the gold edit beyond the (already very explicit) public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
