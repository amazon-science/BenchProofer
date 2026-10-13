# P2 adversarial audit — django__django-11095

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_2_mat_nofilter.py`, `atk_3_sel_droplast.py`, `atk_4_sel_reverse.py`, `atk_5_mat_invert.py`, `atk_6_mat_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo_altcorrect.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AdminView:
@@ -80,7 +79,6 @@
     Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -100,7 +98,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.configured))
         Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
         Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
@@ -118,7 +115,6 @@
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
     Requires(len(self.reported) == len(self.granted))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -134,26 +130,23 @@
     Ensures(ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted)))
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: the editors are materialised by iterating the
+    # CONFIGURED collection directly, never consulting the selection hook's
+    # report. When a context narrows (or otherwise alters) the report so it
+    # differs from the configured collection, this materialisation ignores the
+    # report — exactly the behaviour the fix corrects.
     result = []  # type: List[int]
-    j = len(self.reported)
-    while j > 0:
+    i = len(self.configured)
+    while i > 0:
         # invariants-start
-        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
-        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-        Invariant(len(self.reported) == len(self.granted))
+        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(self.reported))
-        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
-        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
-        Invariant(MustTerminate(j + 1))
+        Invariant(0 <= i and i <= len(self.configured))
+        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
         # invariants-end
-        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
-        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
-        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
-        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
-        cls = self.reported[j - 1]
-        if self.granted[j - 1] != 0:
-            result = [cls] + result
-        j = j - 1
+        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
+        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
+        result = [self.configured[i - 1]] + result
+        i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_2_mat_nofilter.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AdminView:
@@ -80,7 +79,6 @@
     Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -100,7 +98,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.configured))
         Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
         Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
@@ -118,7 +115,6 @@
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
     Requires(len(self.reported) == len(self.granted))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -143,17 +139,9 @@
         Invariant(len(self.reported) == len(self.granted))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(self.reported))
-        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
-        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
-        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
-        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
-        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
-        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
         cls = self.reported[j - 1]
-        if self.granted[j - 1] != 0:
-            result = [cls] + result
+        result = [cls] + result
         j = j - 1
     return result
     # impl-end
```

Attack 3 — `atk_3_sel_droplast.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AdminView:
@@ -80,7 +79,6 @@
     Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -93,14 +91,13 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(self.configured)
+    i = len(self.configured) - 1
     while i > 0:
         # invariants-start
         Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.configured))
         Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
         Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
@@ -118,7 +115,6 @@
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
     Requires(len(self.reported) == len(self.granted))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -145,7 +141,6 @@
         Invariant(0 <= j and j <= len(self.reported))
         Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
         Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
         Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
```

Attack 4 — `atk_4_sel_reverse.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AdminView:
@@ -80,7 +79,6 @@
     Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -93,19 +91,15 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(self.configured)
-    while i > 0:
+    i = 0
+    while i < len(self.configured):
         # invariants-start
         Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.configured))
-        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
-        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
-        result = [self.configured[i - 1]] + result
-        i = i - 1
+        result = [self.configured[i]] + result
+        i = i + 1
     return result
     # impl-end
 
@@ -118,7 +112,6 @@
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
     Requires(len(self.reported) == len(self.granted))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -145,7 +138,6 @@
         Invariant(0 <= j and j <= len(self.reported))
         Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
         Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
         Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
```

Attack 5 — `atk_5_mat_invert.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AdminView:
@@ -80,7 +79,6 @@
     Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -100,7 +98,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.configured))
         Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
         Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
@@ -118,7 +115,6 @@
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
     Requires(len(self.reported) == len(self.granted))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -145,14 +141,13 @@
         Invariant(0 <= j and j <= len(self.reported))
         Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
         Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
         Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
         Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
         Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
         cls = self.reported[j - 1]
-        if self.granted[j - 1] != 0:
+        if self.granted[j - 1] == 0:
             result = [cls] + result
         j = j - 1
     return result
```

Attack 6 — `atk_6_mat_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AdminView:
@@ -80,7 +79,6 @@
     Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -100,7 +98,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.configured))
         Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
         Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
@@ -118,7 +115,6 @@
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
     Requires(len(self.reported) == len(self.granted))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -135,25 +131,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    j = len(self.reported)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
-        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-        Invariant(len(self.reported) == len(self.granted))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(self.reported))
-        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
-        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
-        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
-        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
-        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
-        cls = self.reported[j - 1]
-        if self.granted[j - 1] != 0:
-            result = [cls] + result
-        j = j - 1
     return result
     # impl-end
```

Attack 7 — `atk_7_echo_altcorrect.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class AdminView:
@@ -80,7 +79,6 @@
     Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -100,7 +98,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.configured))
         Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
         Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
@@ -118,7 +115,6 @@
     Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
     Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
     Requires(len(self.reported) == len(self.granted))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
@@ -145,15 +141,14 @@
         Invariant(0 <= j and j <= len(self.reported))
         Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
         Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
         Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
         Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
         Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
-        cls = self.reported[j - 1]
-        if self.granted[j - 1] != 0:
-            result = [cls] + result
+        g = self.granted[j - 1]
+        if g != 0:
+            result = [self.reported[j - 1]] + result
         j = j - 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11095.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administration view exposes a configured collection of related-record
  editors (each identified here by an integer class identifier). Two cooperating
  operations are specified.

    (1) A selection hook reports WHICH editors apply to a given access context
        (a request and an optional record). Its default report is exactly the
        configured collection, in the configured order — neither dropping,
        adding, nor reordering any entry.

    (2) The materialisation operation that turns the selection into live editor
        objects must build them from the SELECTION HOOK'S report, NOT from the
        configured collection directly: it instantiates one editor per reported
        identifier, in the reported order, and (when an access context is
        present) keeps exactly those whose access context grants any of the
        relevant permissions, in order. So a context in which the hook reports a
        narrowed (or otherwise altered) collection yields editors built from the
        narrowed report — were materialisation to read the configured collection
        instead, an altered report would be ignored.

The administration view is modelled as a minimal class carrying only the touched
collections: the configured editor identifiers (`configured`), the selection
hook's reported identifiers for the current context (`reported`), and a
per-reported-entry permission flag (`granted`) recording whether the access
context grants that entry. Lists of editor-class identifiers are modelled as
`List[int]`; the specification is carried over `PSeq[int]` via `ToSeq`. No
library callee is axiomatized: both operations are pure collection/control-flow
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class AdminView:
    def __init__(self) -> None:
        Ensures(Acc(self.configured) and Acc(list_pred(self.configured)))  # type: ignore
        Ensures(Acc(self.reported) and Acc(list_pred(self.reported)))  # type: ignore
        Ensures(Acc(self.granted) and Acc(list_pred(self.granted)))  # type: ignore
        Ensures(len(self.configured) == 0)  # type: ignore
        Ensures(len(self.reported) == 0)  # type: ignore
        Ensures(len(self.granted) == 0)  # type: ignore
        self.configured = []  # type: List[int]
        self.reported = []  # type: List[int]
        self.granted = []  # type: List[int]


# axioms-start
# No consumed axioms: both operations are pure collection/control-flow logic,
# modelled deeply. The default hook reports the configured collection; the
# materialisation builds one live editor per reported identifier (kept when its
# context grants access). There is no unchanged library callee whose contract
# the proof depends on.
# axioms-end


# pure-start
@Pure
def kept(reported: PSeq[int], granted: PSeq[int]) -> PSeq[int]:
    """The subsequence of `reported` whose aligned `granted` flag is set, in the
    same order. Front-recursive so a single unfold is available per loop step: a
    context that grants every entry keeps the whole report."""
    Requires(len(reported) == len(granted))
    if len(reported) == 0:
        return PSeq(0).take(0)
    if granted[0] != 0:
        return PSeq(reported[0]) + kept(reported.drop(1), granted.drop(1))
    return kept(reported.drop(1), granted.drop(1))
# pure-end


def select_applicable_editors(self: AdminView, request: int, obj: Optional[int]) -> List[int]:
    # pre-conditions-start
    # Read-only over the whole view: fractional permission on every collection.
    Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Ensures(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Ensures(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The default selection report is exactly the configured collection, in
    # the configured order: nothing dropped, added, or reordered.
    Ensures(ToSeq(Result()) == ToSeq(self.configured))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(self.configured)
    while i > 0:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.configured))
        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
        # invariants-end
        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result
    # impl-end


def materialize_editors(self: AdminView, request: int, obj: Optional[int]) -> List[int]:
    # pre-conditions-start
    # Read-only over the whole view. The selection hook's report and its aligned
    # permission flags are index-aligned.
    Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Requires(len(self.reported) == len(self.granted))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Ensures(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Ensures(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(self.reported) == len(self.granted))
    # (2) The materialised editors are built from the SELECTION HOOK'S report
    # (self.reported), keeping exactly those whose access context grants the
    # entry, in order. The class identity of editor k is the reported identifier
    # it was built from. Pinned to `reported`, NOT to `configured`: an altered
    # report (a context the hook narrows) yields editors built from that report.
    Ensures(ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = len(self.reported)
    while j > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
        # invariants-end
        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
        cls = self.reported[j - 1]
        if self.granted[j - 1] != 0:
            result = [cls] + result
        j = j - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### Verdict: SOUND

SPEC SHAPE: The frozen spec pins BOTH results with TOTAL functional equalities over the impl-only editable region: (1) select_applicable_editors: Ensures(ToSeq(Result()) == ToSeq(self.configured)); (2) materialize_editors: Ensures(ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted))). same_spec protects everything except impl regions (invariants nest inside impl, so may vary). Assume(/Refute( are banned tokens (vacuity guards) — not used. There is no partial-domain escape: the equalities are exact for all inputs satisfying len(reported)==len(granted).

ATTACK BATTERY (all same-spec exit 0; verified via bash scripts/nagini_verify.sh and python -m swebench_unified.adversary weakness nagini django__django-11095 <file>):
- pos_control.py (model.py verbatim): VERIFIED (13.5s) — positive control.
- atk_1_prepatch.py (model_prepatch.py; materialize iterates self.configured): NOT-VERIFIED — 'Postcondition of materialize_editors might not hold ... ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted))'. Prepatch bug reproduced (spec senses the differential).
- atk_2_mat_nofilter.py (dropped permission filter / partial-domain): NOT-VERIFIED — materialize postcondition fails.
- atk_3_sel_droplast.py (off-by-one boundary, drops last configured): NOT-VERIFIED — loop invariant entry (0<=i).
- atk_4_sel_reverse.py (control-flow-effect: reversed order): NOT-VERIFIED — select_applicable_editors postcondition ToSeq(Result())==ToSeq(self.configured) fails.
- atk_5_mat_invert.py (inverted permission test, keep when !granted): NOT-VERIFIED — kept-invariant not preserved.
- atk_6_mat_empty.py (ungrounded/trivial empty result): NOT-VERIFIED — materialize postcondition fails.
- atk_7_echo_altcorrect.py (alt-correct echo: computes kept(reported,granted) via a distinct-but-equivalent construction): VERIFIED (12–15s) => CANDIDATE-COUNTEREXAMPLE (weakness exit 0). Per protocol, materialized its faithful refined patch (the gold-equivalent get_inlines hook + re-sourced get_inline_instances loop) and RAN it through the official harness: run_resolve('django__django-11095', ...) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So this candidate is a correct echo, NOT a weakness (matches the candidate->resolve policy).

Only correct implementations verify; every distinct wrong impl (partial-domain, boundary, control-flow-effect, inverted-oracle, ungrounded-empty) is rejected. The one verifying candidate's faithful patch resolves.

A-LEG AUDIT (refinement.md): §D asserts no kind-3 steps; confirmed — every leg is R / A-reference / I. Two A-reference legs: A2 select_applicable_editors ↔ ModelAdmin.get_inlines (default body 'return self.inlines'); B1 materialize_editors ↔ ModelAdmin.get_inline_instances (loop re-sourced to self.get_inlines(request,obj)). No @ContractOnly axiom consumed (axioms region is a no-op comment). axiom_check.py drives the REAL Django callees: default admin (get_inlines reports configured inlines in order; instances one-per-inline) AND the F2P EpisodeAdmin override returning [] / [:1] / [1:2] under a MockSuperUser granting all perms, asserting [type(i) for i in get_inline_instances(request)] equals exactly the hook's report and differs from configured inlines — the discriminating override the prepatch would ignore. kept(reported,granted) faithfully models the permission-filter subsequence. Correspondence holds. mapping.md type abstraction (inline class ↔ int id; observed via type()) is faithful.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_2_mat_nofilter.py`, `atk_3_sel_droplast.py`, `atk_4_sel_reverse.py`, `atk_5_mat_invert.py`, `atk_6_mat_empty.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7_echo_altcorrect.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_mat_nofilter.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_sel_droplast.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_sel_reverse.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_mat_invert.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_mat_empty.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_echo_altcorrect.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11095.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administration view exposes a configured collection of related-record
  editors (each identified here by an integer class identifier). Two cooperating
  operations are specified.

    (1) A selection hook reports WHICH editors apply to a given access context
        (a request and an optional record). Its default report is exactly the
        configured collection, in the configured order — neither dropping,
        adding, nor reordering any entry.

    (2) The materialisation operation that turns the selection into live editor
        objects must build them from the SELECTION HOOK'S report, NOT from the
        configured collection directly: it instantiates one editor per reported
        identifier, in the reported order, and (when an access context is
        present) keeps exactly those whose access context grants any of the
        relevant permissions, in order. So a context in which the hook reports a
        narrowed (or otherwise altered) collection yields editors built from the
        narrowed report — were materialisation to read the configured collection
        instead, an altered report would be ignored.

The administration view is modelled as a minimal class carrying only the touched
collections: the configured editor identifiers (`configured`), the selection
hook's reported identifiers for the current context (`reported`), and a
per-reported-entry permission flag (`granted`) recording whether the access
context grants that entry. Lists of editor-class identifiers are modelled as
`List[int]`; the specification is carried over `PSeq[int]` via `ToSeq`. No
library callee is axiomatized: both operations are pure collection/control-flow
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class AdminView:
    def __init__(self) -> None:
        Ensures(Acc(self.configured) and Acc(list_pred(self.configured)))  # type: ignore
        Ensures(Acc(self.reported) and Acc(list_pred(self.reported)))  # type: ignore
        Ensures(Acc(self.granted) and Acc(list_pred(self.granted)))  # type: ignore
        Ensures(len(self.configured) == 0)  # type: ignore
        Ensures(len(self.reported) == 0)  # type: ignore
        Ensures(len(self.granted) == 0)  # type: ignore
        self.configured = []  # type: List[int]
        self.reported = []  # type: List[int]
        self.granted = []  # type: List[int]


# axioms-start
# No consumed axioms: both operations are pure collection/control-flow logic,
# modelled deeply. The default hook reports the configured collection; the
# materialisation builds one live editor per reported identifier (kept when its
# context grants access). There is no unchanged library callee whose contract
# the proof depends on.
# axioms-end


# pure-start
@Pure
def kept(reported: PSeq[int], granted: PSeq[int]) -> PSeq[int]:
    """The subsequence of `reported` whose aligned `granted` flag is set, in the
    same order. Front-recursive so a single unfold is available per loop step: a
    context that grants every entry keeps the whole report."""
    Requires(len(reported) == len(granted))
    if len(reported) == 0:
        return PSeq(0).take(0)
    if granted[0] != 0:
        return PSeq(reported[0]) + kept(reported.drop(1), granted.drop(1))
    return kept(reported.drop(1), granted.drop(1))
# pure-end


def select_applicable_editors(self: AdminView, request: int, obj: Optional[int]) -> List[int]:
    # pre-conditions-start
    # Read-only over the whole view: fractional permission on every collection.
    Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Ensures(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Ensures(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The default selection report is exactly the configured collection, in
    # the configured order: nothing dropped, added, or reordered.
    Ensures(ToSeq(Result()) == ToSeq(self.configured))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(self.configured)
    while i > 0:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.configured))
        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
        # invariants-end
        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result
    # impl-end


def materialize_editors(self: AdminView, request: int, obj: Optional[int]) -> List[int]:
    # pre-conditions-start
    # Read-only over the whole view. The selection hook's report and its aligned
    # permission flags are index-aligned.
    Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Requires(len(self.reported) == len(self.granted))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Ensures(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Ensures(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(self.reported) == len(self.granted))
    # (2) The materialised editors are built from the SELECTION HOOK'S report
    # (self.reported), keeping exactly those whose access context grants the
    # entry, in order. The class identity of editor k is the reported identifier
    # it was built from. Pinned to `reported`, NOT to `configured`: an altered
    # report (a context the hook narrows) yields editors built from that report.
    Ensures(ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = len(self.reported)
    while j > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
        # invariants-end
        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
        cls = self.reported[j - 1]
        if self.granted[j - 1] != 0:
            result = [cls] + result
        j = j - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### Verdict: SOUND

SPEC SHAPE: The frozen spec pins BOTH results with TOTAL functional equalities over the impl-only editable region: (1) select_applicable_editors: Ensures(ToSeq(Result()) == ToSeq(self.configured)); (2) materialize_editors: Ensures(ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted))). same_spec protects everything except impl regions (invariants nest inside impl, so may vary). Assume(/Refute( are banned tokens (vacuity guards) — not used. There is no partial-domain escape: the equalities are exact for all inputs satisfying len(reported)==len(granted).

ATTACK BATTERY (all same-spec exit 0; verified via bash scripts/nagini_verify.sh and python -m swebench_unified.adversary weakness nagini django__django-11095 <file>):
- pos_control.py (model.py verbatim): VERIFIED (13.5s) — positive control.
- atk_1_prepatch.py (model_prepatch.py; materialize iterates self.configured): NOT-VERIFIED — 'Postcondition of materialize_editors might not hold ... ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted))'. Prepatch bug reproduced (spec senses the differential).
- atk_2_mat_nofilter.py (dropped permission filter / partial-domain): NOT-VERIFIED — materialize postcondition fails.
- atk_3_sel_droplast.py (off-by-one boundary, drops last configured): NOT-VERIFIED — loop invariant entry (0<=i).
- atk_4_sel_reverse.py (control-flow-effect: reversed order): NOT-VERIFIED — select_applicable_editors postcondition ToSeq(Result())==ToSeq(self.configured) fails.
- atk_5_mat_invert.py (inverted permission test, keep when !granted): NOT-VERIFIED — kept-invariant not preserved.
- atk_6_mat_empty.py (ungrounded/trivial empty result): NOT-VERIFIED — materialize postcondition fails.
- atk_7_echo_altcorrect.py (alt-correct echo: computes kept(reported,granted) via a distinct-but-equivalent construction): VERIFIED (12–15s) => CANDIDATE-COUNTEREXAMPLE (weakness exit 0). Per protocol, materialized its faithful refined patch (the gold-equivalent get_inlines hook + re-sourced get_inline_instances loop) and RAN it through the official harness: run_resolve('django__django-11095', ...) => RESOLVED=True, COMPLETED=True, NOTE='resolved'. So this candidate is a correct echo, NOT a weakness (matches the candidate->resolve policy).

Only correct implementations verify; every distinct wrong impl (partial-domain, boundary, control-flow-effect, inverted-oracle, ungrounded-empty) is rejected. The one verifying candidate's faithful patch resolves.

A-LEG AUDIT (refinement.md): §D asserts no kind-3 steps; confirmed — every leg is R / A-reference / I. Two A-reference legs: A2 select_applicable_editors ↔ ModelAdmin.get_inlines (default body 'return self.inlines'); B1 materialize_editors ↔ ModelAdmin.get_inline_instances (loop re-sourced to self.get_inlines(request,obj)). No @ContractOnly axiom consumed (axioms region is a no-op comment). axiom_check.py drives the REAL Django callees: default admin (get_inlines reports configured inlines in order; instances one-per-inline) AND the F2P EpisodeAdmin override returning [] / [:1] / [1:2] under a MockSuperUser granting all perms, asserting [type(i) for i in get_inline_instances(request)] equals exactly the hook's report and differs from configured inlines — the discriminating override the prepatch would ignore. kept(reported,granted) faithfully models the permission-filter subsequence. Correspondence holds. mapping.md type abstraction (inline class ↔ int id; observed via type()) is faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on nagini django__django-11095. Two cooperating ops modeled: select_applicable_editors (the new ModelAdmin.get_inlines hook, default report = configured inlines) and materialize_editors (ModelAdmin.get_inline_instances, sourcing from the hook's report instead of self.inlines). Type abstraction: inline class ↔ int id; permission disjunction (view/add/delete) ↔ per-entry `granted` flag; falsy request ↔ all-set grants.

Checks performed:
1) Spec region byte-identical: `swebench_unified.adversary same-spec` returns SAME (exit 0).
2) Built base_commit worktree (7d49ad76) and applied the gold patch by hand (added get_inlines returning self.inlines; changed the loop header to iterate self.get_inlines(request, obj)).
3) Re-ran the bundle's conformance_check.py against MY freshly-patched real repo: 100019 inputs (19 boundary + 100000 fuzz, seed 110950) stressing empty/narrowed/reordered/duplicated/disjoint reports, every channel combination, and falsy contexts — 0 disagreements. Model outputs match real get_inlines/get_inline_instances on every input.
4) Direct edge-case probes on the real patched repo: falsy request keeps all reported [2,0,2,5]; delete-only channel with granted ids {0,2} over report [0,1,2] keeps [0,2]; empty channel set keeps [] — all match kept(reported,granted).

select_applicable_editors postcondition (ToSeq(Result)==ToSeq(configured)) matches the real default hook; materialize_editors postcondition (ToSeq(Result)==kept(ToSeq(reported),ToSeq(granted))) matches the real materialisation on the entire realizable input domain. The abstraction is a faithful carrier (class-determined grants kept flag-consistent; test observes only type identity). No input found where the modeled function disagrees with the real callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures) and semantic review confirms no leak beyond the public problem_statement. The public problem_statement ALREADY discloses the entire gold edit at the repo-symbol level: it explicitly asks to 'add ModelAdmin.get_inlines() hook to allow set inlines based on the request or model instance', notes that today one must 'override the method get_inline_instances ... but a for loop should be copied', and requests 'add a hook get_inlines(request, obj=None)'. So both patched symbols (get_inlines, get_inline_instances) and the feature intent are already solver-visible. The spec view (model.py projected via markers) uses fully abstracted carriers only: class AdminView, functions select_applicable_editors / materialize_editors, fields configured/reported/granted, kept(). None of the repo symbols (get_inlines, get_inline_instances, self.inlines, django/contrib/admin/options.py) appear in the spec view. No diff markers, no patched file path, no patched module path. The docstring/comments state DESIRED BEHAVIOUR abstractly ('build them from the SELECTION HOOK'S report, NOT from the configured collection directly') — no bug/fix/patch narration keywords, no edit narration. The only behavioral content conveyed (default hook == configured collection; materialisation sourced from the hook's report) is precisely the feature the public problem_statement requests, so it leaks nothing beyond what is already public. The two patched-symbol names the screen extracts (get_inlines) are exempted because they appear in problem_statement. mapping.md/refinement.md/verdict.md are auditor-side docs, not the solver spec view. Conclusion: the spec view does not reconstruct the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
