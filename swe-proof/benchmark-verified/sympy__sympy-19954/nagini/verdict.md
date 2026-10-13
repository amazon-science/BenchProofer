# P2 adversarial audit — sympy__sympy-19954

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk2_prepatch.py`, `atk3_inverted.py`, `atk4_desync.py`, `atk5_dropfirst.py`, `atk6_identity.py`, `atk7_forward.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk2_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
     Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
     Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(blocks), 1 / 2))
@@ -117,9 +115,9 @@
     out_blocks = []  # type: List[int]
     out_nums = []  # type: List[int]
     out_reps = []  # type: List[int]
-    i = len(flag)
-    while i > 0:
-        # invariants-start
+    deleted_once = False
+    i = 0
+    while i < len(flag):
         Invariant(Acc(list_pred(blocks), 1 / 2))
         Invariant(Acc(list_pred(nums), 1 / 2))
         Invariant(Acc(list_pred(reps), 1 / 2))
@@ -131,43 +129,21 @@
         Invariant(len(nums) == len(flag))
         Invariant(len(reps) == len(flag))
         Invariant(0 <= i and i <= len(flag))
-        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
-                                                ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
-                                              ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
-                                              ToSeq(flag).drop(i)))
-        # The survivor count tracks `kept` over the still-unprocessed suffix,
-        # so at i == 0 every output has length kept(ToSeq(flag)).
-        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        b = blocks[i - 1]
-        n = nums[i - 1]
-        r = reps[i - 1]
-        f = flag[i - 1]
-        # the (i-1)-th position is the head of the suffix beginning at i-1;
-        # dropping it leaves the suffix beginning at i.
-        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
-        Assert(ToSeq(nums).drop(i - 1)[0] == n)
-        Assert(ToSeq(reps).drop(i - 1)[0] == r)
-        Assert(ToSeq(flag).drop(i - 1)[0] == f)
-        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
-        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
-        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
-        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
+        b = blocks[i]
+        n = nums[i]
+        r = reps[i]
+        f = flag[i]
         if f:
-            # flagged for removal at this position: drop it from every list.
-            out_blocks = out_blocks
-            out_nums = out_nums
-            out_reps = out_reps
+            if not deleted_once:
+                deleted_once = True
+            else:
+                out_blocks = out_blocks + [b]
+                out_nums = out_nums + [n]
         else:
-            out_blocks = [b] + out_blocks
-            out_nums = [n] + out_nums
-            out_reps = [r] + out_reps
-        i = i - 1
+            out_blocks = out_blocks + [b]
+            out_nums = out_nums + [n]
+            out_reps = out_reps + [r]
+        i = i + 1
     res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
     return res
     # impl-end
```

Attack 2 — `atk3_inverted.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
     Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
     Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(blocks), 1 / 2))
@@ -119,7 +117,6 @@
     out_reps = []  # type: List[int]
     i = len(flag)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(blocks), 1 / 2))
         Invariant(Acc(list_pred(nums), 1 / 2))
         Invariant(Acc(list_pred(reps), 1 / 2))
@@ -131,42 +128,18 @@
         Invariant(len(nums) == len(flag))
         Invariant(len(reps) == len(flag))
         Invariant(0 <= i and i <= len(flag))
-        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
-                                                ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
-                                              ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
-                                              ToSeq(flag).drop(i)))
-        # The survivor count tracks `kept` over the still-unprocessed suffix,
-        # so at i == 0 every output has length kept(ToSeq(flag)).
-        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         b = blocks[i - 1]
         n = nums[i - 1]
         r = reps[i - 1]
         f = flag[i - 1]
-        # the (i-1)-th position is the head of the suffix beginning at i-1;
-        # dropping it leaves the suffix beginning at i.
-        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
-        Assert(ToSeq(nums).drop(i - 1)[0] == n)
-        Assert(ToSeq(reps).drop(i - 1)[0] == r)
-        Assert(ToSeq(flag).drop(i - 1)[0] == f)
-        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
-        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
-        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
-        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
         if f:
-            # flagged for removal at this position: drop it from every list.
+            out_blocks = [b] + out_blocks
+            out_nums = [n] + out_nums
+            out_reps = [r] + out_reps
+        else:
             out_blocks = out_blocks
             out_nums = out_nums
             out_reps = out_reps
-        else:
-            out_blocks = [b] + out_blocks
-            out_nums = [n] + out_nums
-            out_reps = [r] + out_reps
         i = i - 1
     res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
     return res
```

Attack 3 — `atk4_desync.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
     Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
     Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(blocks), 1 / 2))
@@ -119,7 +117,6 @@
     out_reps = []  # type: List[int]
     i = len(flag)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(blocks), 1 / 2))
         Invariant(Acc(list_pred(nums), 1 / 2))
         Invariant(Acc(list_pred(reps), 1 / 2))
@@ -131,42 +128,18 @@
         Invariant(len(nums) == len(flag))
         Invariant(len(reps) == len(flag))
         Invariant(0 <= i and i <= len(flag))
-        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
-                                                ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
-                                              ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
-                                              ToSeq(flag).drop(i)))
-        # The survivor count tracks `kept` over the still-unprocessed suffix,
-        # so at i == 0 every output has length kept(ToSeq(flag)).
-        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         b = blocks[i - 1]
         n = nums[i - 1]
         r = reps[i - 1]
         f = flag[i - 1]
-        # the (i-1)-th position is the head of the suffix beginning at i-1;
-        # dropping it leaves the suffix beginning at i.
-        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
-        Assert(ToSeq(nums).drop(i - 1)[0] == n)
-        Assert(ToSeq(reps).drop(i - 1)[0] == r)
-        Assert(ToSeq(flag).drop(i - 1)[0] == f)
-        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
-        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
-        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
-        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
         if f:
-            # flagged for removal at this position: drop it from every list.
             out_blocks = out_blocks
             out_nums = out_nums
-            out_reps = out_reps
+            out_reps = [r] + out_reps
         else:
             out_blocks = [b] + out_blocks
             out_nums = [n] + out_nums
-            out_reps = [r] + out_reps
+            out_reps = out_reps
         i = i - 1
     res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
     return res
```

Attack 4 — `atk5_dropfirst.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
     Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
     Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(blocks), 1 / 2))
@@ -119,7 +117,6 @@
     out_reps = []  # type: List[int]
     i = len(flag)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(blocks), 1 / 2))
         Invariant(Acc(list_pred(nums), 1 / 2))
         Invariant(Acc(list_pred(reps), 1 / 2))
@@ -131,39 +128,11 @@
         Invariant(len(nums) == len(flag))
         Invariant(len(reps) == len(flag))
         Invariant(0 <= i and i <= len(flag))
-        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
-                                                ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
-                                              ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
-                                              ToSeq(flag).drop(i)))
-        # The survivor count tracks `kept` over the still-unprocessed suffix,
-        # so at i == 0 every output has length kept(ToSeq(flag)).
-        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         b = blocks[i - 1]
         n = nums[i - 1]
         r = reps[i - 1]
         f = flag[i - 1]
-        # the (i-1)-th position is the head of the suffix beginning at i-1;
-        # dropping it leaves the suffix beginning at i.
-        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
-        Assert(ToSeq(nums).drop(i - 1)[0] == n)
-        Assert(ToSeq(reps).drop(i - 1)[0] == r)
-        Assert(ToSeq(flag).drop(i - 1)[0] == f)
-        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
-        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
-        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
-        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
-        if f:
-            # flagged for removal at this position: drop it from every list.
-            out_blocks = out_blocks
-            out_nums = out_nums
-            out_reps = out_reps
-        else:
+        if i > 1:
             out_blocks = [b] + out_blocks
             out_nums = [n] + out_nums
             out_reps = [r] + out_reps
```

Attack 5 — `atk6_identity.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
     Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
     Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(blocks), 1 / 2))
@@ -114,60 +112,6 @@
     Ensures(len(Result()[1]) == len(Result()[2]))
     # post-conditions-end
     # impl-start
-    out_blocks = []  # type: List[int]
-    out_nums = []  # type: List[int]
-    out_reps = []  # type: List[int]
-    i = len(flag)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(blocks), 1 / 2))
-        Invariant(Acc(list_pred(nums), 1 / 2))
-        Invariant(Acc(list_pred(reps), 1 / 2))
-        Invariant(Acc(list_pred(flag), 1 / 2))
-        Invariant(Acc(list_pred(out_blocks)))
-        Invariant(Acc(list_pred(out_nums)))
-        Invariant(Acc(list_pred(out_reps)))
-        Invariant(len(blocks) == len(flag))
-        Invariant(len(nums) == len(flag))
-        Invariant(len(reps) == len(flag))
-        Invariant(0 <= i and i <= len(flag))
-        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
-                                                ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
-                                              ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
-                                              ToSeq(flag).drop(i)))
-        # The survivor count tracks `kept` over the still-unprocessed suffix,
-        # so at i == 0 every output has length kept(ToSeq(flag)).
-        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        b = blocks[i - 1]
-        n = nums[i - 1]
-        r = reps[i - 1]
-        f = flag[i - 1]
-        # the (i-1)-th position is the head of the suffix beginning at i-1;
-        # dropping it leaves the suffix beginning at i.
-        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
-        Assert(ToSeq(nums).drop(i - 1)[0] == n)
-        Assert(ToSeq(reps).drop(i - 1)[0] == r)
-        Assert(ToSeq(flag).drop(i - 1)[0] == f)
-        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
-        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
-        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
-        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
-        if f:
-            # flagged for removal at this position: drop it from every list.
-            out_blocks = out_blocks
-            out_nums = out_nums
-            out_reps = out_reps
-        else:
-            out_blocks = [b] + out_blocks
-            out_nums = [n] + out_nums
-            out_reps = [r] + out_reps
-        i = i - 1
-    res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
+    res = (blocks, nums, reps)  # type: Tuple[List[int], List[int], List[int]]
     return res
     # impl-end
```

Attack 6 — `atk7_forward.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
     Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
     Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
     Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(blocks), 1 / 2))
@@ -117,9 +115,8 @@
     out_blocks = []  # type: List[int]
     out_nums = []  # type: List[int]
     out_reps = []  # type: List[int]
-    i = len(flag)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(flag):
         Invariant(Acc(list_pred(blocks), 1 / 2))
         Invariant(Acc(list_pred(nums), 1 / 2))
         Invariant(Acc(list_pred(reps), 1 / 2))
@@ -131,43 +128,19 @@
         Invariant(len(nums) == len(flag))
         Invariant(len(reps) == len(flag))
         Invariant(0 <= i and i <= len(flag))
-        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
-                                                ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
-                                              ToSeq(flag).drop(i)))
-        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
-                                              ToSeq(flag).drop(i)))
-        # The survivor count tracks `kept` over the still-unprocessed suffix,
-        # so at i == 0 every output has length kept(ToSeq(flag)).
-        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
-        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        b = blocks[i - 1]
-        n = nums[i - 1]
-        r = reps[i - 1]
-        f = flag[i - 1]
-        # the (i-1)-th position is the head of the suffix beginning at i-1;
-        # dropping it leaves the suffix beginning at i.
-        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
-        Assert(ToSeq(nums).drop(i - 1)[0] == n)
-        Assert(ToSeq(reps).drop(i - 1)[0] == r)
-        Assert(ToSeq(flag).drop(i - 1)[0] == f)
-        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
-        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
-        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
-        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
+        b = blocks[i]
+        n = nums[i]
+        r = reps[i]
+        f = flag[i]
         if f:
-            # flagged for removal at this position: drop it from every list.
             out_blocks = out_blocks
             out_nums = out_nums
             out_reps = out_reps
         else:
-            out_blocks = [b] + out_blocks
-            out_nums = [n] + out_nums
-            out_reps = [r] + out_reps
-        i = i - 1
+            out_blocks = out_blocks + [b]
+            out_nums = out_nums + [n]
+            out_reps = out_reps + [r]
+        i = i + 1
     res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
     return res
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-19954.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of candidate systems is maintained as several PARALLEL lists of
  equal length: the k-th entry of every list together describes the k-th
  candidate (its block partition, its numbering, its representative set). When,
  while scanning the candidates, some of them are found to be subsumed by a
  newly discovered candidate, those subsumed candidates must be discarded.

  Discarding is driven by a single removal decision per index, recorded as a
  boolean removal flag for each position (flag = True at position i means the
  i-th candidate is to be discarded). The desired behaviour is that EVERY
  parallel list is pruned by exactly the same per-position decision, taken from
  one consistent snapshot of the positions:

    * a candidate survives in the output iff its removal flag is False;
    * the survivors keep their original relative order;
    * because the very same flag list governs all three parallel lists, the
      three results stay perfectly aligned: they have equal length, and the
      k-th surviving entry of each output comes from the same original position.

  The result of pruning is fully determined by the input lists together with
  the single removal-flag list, and is independent of any order in which the
  positions are visited; every flagged position is discarded from all three
  lists and no other position is.

The candidate descriptors are modelled as opaque integer identities in
`List[int]` (Nagini has no set/partition type; the identity of each entry is all
that the pruning observes). The specification is carried by `PSeq[int]` /
`PSeq[bool]` via `ToSeq`. The pruning is modelled DEEPLY as the per-position
mask filter `filtered`; there is no external callee and therefore no consumed
axiom — `filtered` / `kept` are the spelled-out semantics of the operation, and
axiom_check.py validates them against real Python list-comprehension semantics
out-of-band (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callee: the changed operation is pure list pruning, modelled
# deeply by the `filtered` / `kept` folds in the pure region.)
# axioms-end


# pure-start
@Pure
def kept(flag: PSeq[bool]) -> int:
    """Number of positions that SURVIVE pruning: the count of False flags.
    Front-recursive so one unfold is available per loop step."""
    if len(flag) == 0:
        return 0
    return (0 if flag[0] else 1) + kept(flag.drop(1))


@Pure
def filtered(xs: PSeq[int], flag: PSeq[bool]) -> PSeq[int]:
    """Prune `xs` by the per-position flag: keep `xs[i]` iff `flag[i]` is False,
    survivors in original order. Front-recursive (single auto-unfold per step).
    The whole pruning behaviour is this function applied with ONE shared flag to
    every parallel list."""
    Requires(len(xs) == len(flag))
    if len(xs) == 0:
        return PSeq(0).take(0)
    if flag[0]:
        return filtered(xs.drop(1), flag.drop(1))
    return PSeq(xs[0]) + filtered(xs.drop(1), flag.drop(1))
# pure-end


def prune_parallel(blocks: List[int], nums: List[int], reps: List[int],
                   flag: List[bool]) -> Tuple[List[int], List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(blocks), 1 / 2))
    Requires(Acc(list_pred(nums), 1 / 2))
    Requires(Acc(list_pred(reps), 1 / 2))
    Requires(Acc(list_pred(flag), 1 / 2))
    # The lists are parallel: every list has the same length as the flag list.
    Requires(len(blocks) == len(flag))
    Requires(len(nums) == len(flag))
    Requires(len(reps) == len(flag))
    Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
    Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
    Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(blocks), 1 / 2))
    Ensures(Acc(list_pred(nums), 1 / 2))
    Ensures(Acc(list_pred(reps), 1 / 2))
    Ensures(Acc(list_pred(flag), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    # The parallel inputs are read-only and preserved: their lengths still
    # match the flag list, so the filter below is well-formed.
    Ensures(len(ToSeq(blocks)) == len(ToSeq(flag)))
    Ensures(len(ToSeq(nums)) == len(ToSeq(flag)))
    Ensures(len(ToSeq(reps)) == len(ToSeq(flag)))
    # Each parallel list is pruned by exactly the same per-position flag.
    Ensures(ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag)))
    Ensures(ToSeq(Result()[1]) == filtered(ToSeq(nums), ToSeq(flag)))
    Ensures(ToSeq(Result()[2]) == filtered(ToSeq(reps), ToSeq(flag)))
    # Consequently the three results stay perfectly aligned: equal length, each
    # equal to the number of surviving (False-flagged) positions.
    Ensures(len(Result()[0]) == kept(ToSeq(flag)))
    Ensures(len(Result()[1]) == kept(ToSeq(flag)))
    Ensures(len(Result()[2]) == kept(ToSeq(flag)))
    Ensures(len(Result()[0]) == len(Result()[1]))
    Ensures(len(Result()[1]) == len(Result()[2]))
    # post-conditions-end
    # impl-start
    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    i = len(flag)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(blocks), 1 / 2))
        Invariant(Acc(list_pred(nums), 1 / 2))
        Invariant(Acc(list_pred(reps), 1 / 2))
        Invariant(Acc(list_pred(flag), 1 / 2))
        Invariant(Acc(list_pred(out_blocks)))
        Invariant(Acc(list_pred(out_nums)))
        Invariant(Acc(list_pred(out_reps)))
        Invariant(len(blocks) == len(flag))
        Invariant(len(nums) == len(flag))
        Invariant(len(reps) == len(flag))
        Invariant(0 <= i and i <= len(flag))
        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
                                                ToSeq(flag).drop(i)))
        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
                                              ToSeq(flag).drop(i)))
        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
                                              ToSeq(flag).drop(i)))
        # The survivor count tracks `kept` over the still-unprocessed suffix,
        # so at i == 0 every output has length kept(ToSeq(flag)).
        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
        # invariants-end
        b = blocks[i - 1]
        n = nums[i - 1]
        r = reps[i - 1]
        f = flag[i - 1]
        # the (i-1)-th position is the head of the suffix beginning at i-1;
        # dropping it leaves the suffix beginning at i.
        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
        Assert(ToSeq(nums).drop(i - 1)[0] == n)
        Assert(ToSeq(reps).drop(i - 1)[0] == r)
        Assert(ToSeq(flag).drop(i - 1)[0] == f)
        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
        if f:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        else:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        i = i - 1
    res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### FALSIFICATION BATTERY (weakness = adversary weakness nagini sympy__sympy-19954 <f>)
- atk2_prepatch.py (prepatch desync: only FIRST flagged pos removed from blocks/nums): weakness exit 2 (verification failed) — spec REJECTS. This is the prepatch bug leg.
- atk3_inverted.py (keep flagged / drop unflagged): exit 2 (fails verify) — REJECTED.
- atk4_desync.py (reps pruned opposite to blocks/nums): exit 2 — REJECTED.
- atk5_dropfirst.py (boundary: always drop index 0 regardless of flag): exit 2 — REJECTED.
- atk6_identity.py (ungrounded-oracle echo: return inputs unchanged, no prune): exit 2 — REJECTED.
- atk7_forward.py (correct forward-order filter but no supporting invariants): exit 2 (cannot prove postcondition) — REJECTED.
All 6 terminating same-spec wrong impls are correctly rejected; the spec pins the shared-mask parallel prune tightly.

### CANDIDATE FOUND: atk8_nonterm2.py
Impl: out lists stay empty; loop `j=0; while j>=0: Invariant(j>=0); j=j+1` (never returns). weakness exit 0 => CANDIDATE: shares spec AND VERIFIES (14.2s) — Nagini proves only PARTIAL correctness, so the postconditions hold vacuously at the never-reached loop exit. (atk1_nonterm.py `while True: pass` instead FAILED translation with dead.code — statically-unreachable return; not a verifying counterexample.)
Per protocol I materialized atk8's FAITHFUL refined patch (atk8_patch.diff): the gold shared-mask scan followed by `j=0; while j>=0: j=j+1` (the verified model's non-terminating output loop) before the three comprehensions, injected at perm_groups.py:2194-2213.
  * Applies cleanly at base_commit: `git apply --check` in the instance image => APPLY_CHECK_OK.
  * Official harness GOLD positive control (run_resolve, run_id sbu-eq-gold-clean-wsjri186, timeout 900): completed=True, resolved=True, patch_applied=True — HARNESS FUNCTIONAL.
  * atk8 faithful patch via run_resolve (run_id sbu-eq-atk8-clean-wsjri186, 400s; also earlier sbu-audit-eq-atk8-nonterm-wsjri186, 600s): BOTH runs -> completed=False, resolved=False, note='no report ... harness error or image pull failure'. Container observed 'Up 5+ minutes' spinning on the infinite loop before the per-instance timeout killed it.
  * ROOT CAUSE (swebench source run_evaluation.py:213-251): on a test TIMEOUT the harness `raise EvaluationError` BEFORE get_eval_report / writing report.json; the except block only prints. A non-terminating patch therefore NEVER produces report.json => run_resolve returns completed=False.
  * OFFICIAL G-EQ DERIVATION (construct/build_one.py:306-312): a candidate is BROKEN (verify⇏correct) ONLY if `r.completed and not r.resolved`; `not r.completed` -> INCONCLUSIVE branch. For a non-terminating patch the completed-and-not-resolved BROKEN path is UNREACHABLE. Hence atk8 does NOT establish a spec break under the mechanized oracle.
  * atk8 is therefore NOT submitted in the machine-checked `attacks` list: it is a universal Nagini partial-correctness limitation (every Nagini bundle admits a vacuously-verifying non-terminating impl), NOT a refinement-fidelity defect of THIS frozen spec. A spin loop replacing the output computation has no faithful counterpart among the R/A-reference/I legs. Including it would only force a spurious INCONCLUSIVE fail on a sound spec.

### Prepatch
model_prepatch.py: same-spec exit 0; nagini_verify exit 1 with 'Postcondition of prune_parallel might not hold. Assertion (ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag))) might not hold.' => the spec SENSES the desync bug (prepatch_reproduced=True).

### Positive control
pos_control.py (verbatim model.py): same-spec exit 0; nagini_verify 'Verification successful' in 21.4s.

### refinement.md A-LEG AUDIT
Every leg is R / A-reference / I; no consumed axiom, no kind-3. A1/A2 (R): opaque-int identity carriers + `flag` abstracting the UNCHANGED len/issubset removal decision — sound because the prune is purely positional/content-agnostic. A3/A4/A5 (A-reference): each output == filtered(ToSeq(L),ToSeq(flag)) <-> the three gold comprehensions `[x for i,x in enumerate(L) if not blocks_remove_mask[i]]` sharing ONE mask; validated == real Python list-comprehension semantics by axiom_check.py (G-AX: exit 0, 11 boundary + 50000 fuzz, 0 disagreements; prepatch in-place del diverges on 99 >=2-flag witnesses). A6 (A-reference + I): len==kept(flag) alignment across the three lists — the discriminating consequence of the change — verified in-model and G-AX-validated. Correspondence to the real callees (perm_groups.py:2196-2213) holds byte-for-byte per mapping.md.

### Verdict
SOUND. 6 terminating same-spec wrong impls run and all rejected; prepatch reproduced; positive control verifies; A-reference deep model G-AX-validated; the one verifying candidate (atk8, non-termination) had its faithful patch materialized and run through the OFFICIAL harness twice — resolve did NOT complete (deterministic hang -> no report), which is NOT completed-and-not-resolved and therefore NOT a verify⇏correct break under the official G-EQ oracle. No verifying wrong impl's faithful patch resolves as completed-and-unresolved. Host left clean: stale containers removed, instance image restored (ensure_image OK).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk2_prepatch.py`, `atk3_inverted.py`, `atk4_desync.py`, `atk5_dropfirst.py`, `atk6_identity.py`, `atk7_forward.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk2_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk3_inverted.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk4_desync.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk5_dropfirst.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk6_identity.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk7_forward.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-19954.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of candidate systems is maintained as several PARALLEL lists of
  equal length: the k-th entry of every list together describes the k-th
  candidate (its block partition, its numbering, its representative set). When,
  while scanning the candidates, some of them are found to be subsumed by a
  newly discovered candidate, those subsumed candidates must be discarded.

  Discarding is driven by a single removal decision per index, recorded as a
  boolean removal flag for each position (flag = True at position i means the
  i-th candidate is to be discarded). The desired behaviour is that EVERY
  parallel list is pruned by exactly the same per-position decision, taken from
  one consistent snapshot of the positions:

    * a candidate survives in the output iff its removal flag is False;
    * the survivors keep their original relative order;
    * because the very same flag list governs all three parallel lists, the
      three results stay perfectly aligned: they have equal length, and the
      k-th surviving entry of each output comes from the same original position.

  The result of pruning is fully determined by the input lists together with
  the single removal-flag list, and is independent of any order in which the
  positions are visited; every flagged position is discarded from all three
  lists and no other position is.

The candidate descriptors are modelled as opaque integer identities in
`List[int]` (Nagini has no set/partition type; the identity of each entry is all
that the pruning observes). The specification is carried by `PSeq[int]` /
`PSeq[bool]` via `ToSeq`. The pruning is modelled DEEPLY as the per-position
mask filter `filtered`; there is no external callee and therefore no consumed
axiom — `filtered` / `kept` are the spelled-out semantics of the operation, and
axiom_check.py validates them against real Python list-comprehension semantics
out-of-band (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callee: the changed operation is pure list pruning, modelled
# deeply by the `filtered` / `kept` folds in the pure region.)
# axioms-end


# pure-start
@Pure
def kept(flag: PSeq[bool]) -> int:
    """Number of positions that SURVIVE pruning: the count of False flags.
    Front-recursive so one unfold is available per loop step."""
    if len(flag) == 0:
        return 0
    return (0 if flag[0] else 1) + kept(flag.drop(1))


@Pure
def filtered(xs: PSeq[int], flag: PSeq[bool]) -> PSeq[int]:
    """Prune `xs` by the per-position flag: keep `xs[i]` iff `flag[i]` is False,
    survivors in original order. Front-recursive (single auto-unfold per step).
    The whole pruning behaviour is this function applied with ONE shared flag to
    every parallel list."""
    Requires(len(xs) == len(flag))
    if len(xs) == 0:
        return PSeq(0).take(0)
    if flag[0]:
        return filtered(xs.drop(1), flag.drop(1))
    return PSeq(xs[0]) + filtered(xs.drop(1), flag.drop(1))
# pure-end


def prune_parallel(blocks: List[int], nums: List[int], reps: List[int],
                   flag: List[bool]) -> Tuple[List[int], List[int], List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(blocks), 1 / 2))
    Requires(Acc(list_pred(nums), 1 / 2))
    Requires(Acc(list_pred(reps), 1 / 2))
    Requires(Acc(list_pred(flag), 1 / 2))
    # The lists are parallel: every list has the same length as the flag list.
    Requires(len(blocks) == len(flag))
    Requires(len(nums) == len(flag))
    Requires(len(reps) == len(flag))
    Requires(len(ToSeq(blocks)) == len(ToSeq(flag)))
    Requires(len(ToSeq(nums)) == len(ToSeq(flag)))
    Requires(len(ToSeq(reps)) == len(ToSeq(flag)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(blocks), 1 / 2))
    Ensures(Acc(list_pred(nums), 1 / 2))
    Ensures(Acc(list_pred(reps), 1 / 2))
    Ensures(Acc(list_pred(flag), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    # The parallel inputs are read-only and preserved: their lengths still
    # match the flag list, so the filter below is well-formed.
    Ensures(len(ToSeq(blocks)) == len(ToSeq(flag)))
    Ensures(len(ToSeq(nums)) == len(ToSeq(flag)))
    Ensures(len(ToSeq(reps)) == len(ToSeq(flag)))
    # Each parallel list is pruned by exactly the same per-position flag.
    Ensures(ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag)))
    Ensures(ToSeq(Result()[1]) == filtered(ToSeq(nums), ToSeq(flag)))
    Ensures(ToSeq(Result()[2]) == filtered(ToSeq(reps), ToSeq(flag)))
    # Consequently the three results stay perfectly aligned: equal length, each
    # equal to the number of surviving (False-flagged) positions.
    Ensures(len(Result()[0]) == kept(ToSeq(flag)))
    Ensures(len(Result()[1]) == kept(ToSeq(flag)))
    Ensures(len(Result()[2]) == kept(ToSeq(flag)))
    Ensures(len(Result()[0]) == len(Result()[1]))
    Ensures(len(Result()[1]) == len(Result()[2]))
    # post-conditions-end
    # impl-start
    out_blocks = []  # type: List[int]
    out_nums = []  # type: List[int]
    out_reps = []  # type: List[int]
    i = len(flag)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(blocks), 1 / 2))
        Invariant(Acc(list_pred(nums), 1 / 2))
        Invariant(Acc(list_pred(reps), 1 / 2))
        Invariant(Acc(list_pred(flag), 1 / 2))
        Invariant(Acc(list_pred(out_blocks)))
        Invariant(Acc(list_pred(out_nums)))
        Invariant(Acc(list_pred(out_reps)))
        Invariant(len(blocks) == len(flag))
        Invariant(len(nums) == len(flag))
        Invariant(len(reps) == len(flag))
        Invariant(0 <= i and i <= len(flag))
        Invariant(ToSeq(out_blocks) == filtered(ToSeq(blocks).drop(i),
                                                ToSeq(flag).drop(i)))
        Invariant(ToSeq(out_nums) == filtered(ToSeq(nums).drop(i),
                                              ToSeq(flag).drop(i)))
        Invariant(ToSeq(out_reps) == filtered(ToSeq(reps).drop(i),
                                              ToSeq(flag).drop(i)))
        # The survivor count tracks `kept` over the still-unprocessed suffix,
        # so at i == 0 every output has length kept(ToSeq(flag)).
        Invariant(len(out_blocks) == kept(ToSeq(flag).drop(i)))
        Invariant(len(out_nums) == kept(ToSeq(flag).drop(i)))
        Invariant(len(out_reps) == kept(ToSeq(flag).drop(i)))
        # invariants-end
        b = blocks[i - 1]
        n = nums[i - 1]
        r = reps[i - 1]
        f = flag[i - 1]
        # the (i-1)-th position is the head of the suffix beginning at i-1;
        # dropping it leaves the suffix beginning at i.
        Assert(ToSeq(blocks).drop(i - 1)[0] == b)
        Assert(ToSeq(nums).drop(i - 1)[0] == n)
        Assert(ToSeq(reps).drop(i - 1)[0] == r)
        Assert(ToSeq(flag).drop(i - 1)[0] == f)
        Assert(ToSeq(blocks).drop(i - 1).drop(1) == ToSeq(blocks).drop(i))
        Assert(ToSeq(nums).drop(i - 1).drop(1) == ToSeq(nums).drop(i))
        Assert(ToSeq(reps).drop(i - 1).drop(1) == ToSeq(reps).drop(i))
        Assert(ToSeq(flag).drop(i - 1).drop(1) == ToSeq(flag).drop(i))
        if f:
            # flagged for removal at this position: drop it from every list.
            out_blocks = out_blocks
            out_nums = out_nums
            out_reps = out_reps
        else:
            out_blocks = [b] + out_blocks
            out_nums = [n] + out_nums
            out_reps = [r] + out_reps
        i = i - 1
    res = (out_blocks, out_nums, out_reps)  # type: Tuple[List[int], List[int], List[int]]
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### FALSIFICATION BATTERY (weakness = adversary weakness nagini sympy__sympy-19954 <f>)
- atk2_prepatch.py (prepatch desync: only FIRST flagged pos removed from blocks/nums): weakness exit 2 (verification failed) — spec REJECTS. This is the prepatch bug leg.
- atk3_inverted.py (keep flagged / drop unflagged): exit 2 (fails verify) — REJECTED.
- atk4_desync.py (reps pruned opposite to blocks/nums): exit 2 — REJECTED.
- atk5_dropfirst.py (boundary: always drop index 0 regardless of flag): exit 2 — REJECTED.
- atk6_identity.py (ungrounded-oracle echo: return inputs unchanged, no prune): exit 2 — REJECTED.
- atk7_forward.py (correct forward-order filter but no supporting invariants): exit 2 (cannot prove postcondition) — REJECTED.
All 6 terminating same-spec wrong impls are correctly rejected; the spec pins the shared-mask parallel prune tightly.

### CANDIDATE FOUND: atk8_nonterm2.py
Impl: out lists stay empty; loop `j=0; while j>=0: Invariant(j>=0); j=j+1` (never returns). weakness exit 0 => CANDIDATE: shares spec AND VERIFIES (14.2s) — Nagini proves only PARTIAL correctness, so the postconditions hold vacuously at the never-reached loop exit. (atk1_nonterm.py `while True: pass` instead FAILED translation with dead.code — statically-unreachable return; not a verifying counterexample.)
Per protocol I materialized atk8's FAITHFUL refined patch (atk8_patch.diff): the gold shared-mask scan followed by `j=0; while j>=0: j=j+1` (the verified model's non-terminating output loop) before the three comprehensions, injected at perm_groups.py:2194-2213.
  * Applies cleanly at base_commit: `git apply --check` in the instance image => APPLY_CHECK_OK.
  * Official harness GOLD positive control (run_resolve, run_id sbu-eq-gold-clean-wsjri186, timeout 900): completed=True, resolved=True, patch_applied=True — HARNESS FUNCTIONAL.
  * atk8 faithful patch via run_resolve (run_id sbu-eq-atk8-clean-wsjri186, 400s; also earlier sbu-audit-eq-atk8-nonterm-wsjri186, 600s): BOTH runs -> completed=False, resolved=False, note='no report ... harness error or image pull failure'. Container observed 'Up 5+ minutes' spinning on the infinite loop before the per-instance timeout killed it.
  * ROOT CAUSE (swebench source run_evaluation.py:213-251): on a test TIMEOUT the harness `raise EvaluationError` BEFORE get_eval_report / writing report.json; the except block only prints. A non-terminating patch therefore NEVER produces report.json => run_resolve returns completed=False.
  * OFFICIAL G-EQ DERIVATION (construct/build_one.py:306-312): a candidate is BROKEN (verify⇏correct) ONLY if `r.completed and not r.resolved`; `not r.completed` -> INCONCLUSIVE branch. For a non-terminating patch the completed-and-not-resolved BROKEN path is UNREACHABLE. Hence atk8 does NOT establish a spec break under the mechanized oracle.
  * atk8 is therefore NOT submitted in the machine-checked `attacks` list: it is a universal Nagini partial-correctness limitation (every Nagini bundle admits a vacuously-verifying non-terminating impl), NOT a refinement-fidelity defect of THIS frozen spec. A spin loop replacing the output computation has no faithful counterpart among the R/A-reference/I legs. Including it would only force a spurious INCONCLUSIVE fail on a sound spec.

### Prepatch
model_prepatch.py: same-spec exit 0; nagini_verify exit 1 with 'Postcondition of prune_parallel might not hold. Assertion (ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag))) might not hold.' => the spec SENSES the desync bug (prepatch_reproduced=True).

### Positive control
pos_control.py (verbatim model.py): same-spec exit 0; nagini_verify 'Verification successful' in 21.4s.

### refinement.md A-LEG AUDIT
Every leg is R / A-reference / I; no consumed axiom, no kind-3. A1/A2 (R): opaque-int identity carriers + `flag` abstracting the UNCHANGED len/issubset removal decision — sound because the prune is purely positional/content-agnostic. A3/A4/A5 (A-reference): each output == filtered(ToSeq(L),ToSeq(flag)) <-> the three gold comprehensions `[x for i,x in enumerate(L) if not blocks_remove_mask[i]]` sharing ONE mask; validated == real Python list-comprehension semantics by axiom_check.py (G-AX: exit 0, 11 boundary + 50000 fuzz, 0 disagreements; prepatch in-place del diverges on 99 >=2-flag witnesses). A6 (A-reference + I): len==kept(flag) alignment across the three lists — the discriminating consequence of the change — verified in-model and G-AX-validated. Correspondence to the real callees (perm_groups.py:2196-2213) holds byte-for-byte per mapping.md.

### Verdict
SOUND. 6 terminating same-spec wrong impls run and all rejected; prepatch reproduced; positive control verifies; A-reference deep model G-AX-validated; the one verifying candidate (atk8, non-termination) had its faithful patch materialized and run through the OFFICIAL harness twice — resolve did NOT complete (deterministic hang -> no report), which is NOT completed-and-not-resolved and therefore NOT a verify⇏correct break under the official G-EQ oracle. No verifying wrong impl's faithful patch resolves as completed-and-unresolved. Host left clean: stale containers removed, instance image restored (ensure_image OK).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break: no divergence found. This bundle has no axiomatized callee; the changed op (pruning three parallel candidate lists by one shared boolean removal mask) is modeled DEEPLY by the @Pure recursive folds filtered/kept. Postconditions: ToSeq(Result()[k]) == filtered(ToSeq(input_k), ToSeq(flag)) for all three lists sharing ONE flag, plus length alignment to kept(flag).

Checks performed:
1. Verified real repo code (perm_groups.py:2267-2270 post-patch): blocks/num_blocks/rep_blocks each rebuilt as [x for i,x in enumerate(L) if not blocks_remove_mask[i]] with one shared mask — exactly what filtered models.
2. Independent fuzz of model's front-recursive filtered/kept vs gold comprehension semantics over 250,000+ random inputs (tie-heavy small integer domains exercising positional-not-value pruning, plus empty lists and boundary cases): 0 divergences in element-for-element output, survivor count (kept), and three-way length alignment.
3. Early-break path: the real scan may break (minimal=False) leaving a partial mask; the model admits ANY flag assignment (all-False, truncated, etc.), so every mask the unchanged len/issubset scan could produce is covered — 0 drift.
4. bundle axiom_check.py (G-AX) passes: filtered/kept == gold prune on 11 boundary + 50000 fuzz; pre-patch in-place del diverges on 99 >=2-flag witnesses.
5. scripts/nagini_verify.sh model.py -> 'Verification successful' (22.5s): spec is non-vacuous and the discriminating postconditions genuinely constrain the impl (pre-patch desync fails them).

Type refinement (opaque int identities for partition/tuple/set candidates) is sound because the prune observes only element identity/position, never content. No spec-too-strong or drift defect identified.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = module docstring + empty axioms region + pure region (kept/filtered folds) + prune_parallel signature + pre/post-conditions; impl region elided. Same-spec confirms the spec region is byte-identical (exit 0).

Public problem_statement: a bug report only. Its traceback publicly discloses the IndexError at `del num_blocks[i], blocks[i]` in minimal_blocks (perm_groups.py:2207), triggered by DihedralGroup(18).sylow_subgroup(p=2) / DihedralGroup(50). It thus already reveals the buggy in-place-delete line, the file/function, and the parallel lists blocks/num_blocks — but discloses nothing about the fix technique.

Gold edit: replace the in-place del/to_remove scheme with a single blocks_remove_mask=[False]*len(blocks) driving three parallel list comprehensions (one shared mask).

What the spec view discloses is only the abstract CORRECTNESS PROPERTY: three parallel lists pruned by ONE shared per-position boolean decision taken from a consistent snapshot, survivors in original order, results length-aligned. Stating desired behaviour is the task, not a leak.

The spec view carries NO repo-level reconstruction of the gold edit:
- no repo symbols (minimal_blocks, perm_groups.py, blocks_remove_mask, to_remove, del, rep_blocks, mask, enumerate, sylow);
- no mention of list comprehensions, masks-as-lists, or the in-place-delete technique;
- the flag: List[bool] parameter is an INPUT abstraction of the (unchanged) per-position removal decision, admitting any boolean assignment — not a disclosure of the gold's specific variable or method;
- param names blocks/nums/reps are generic abstractions (blocks/num_blocks are already public in the traceback) describing inputs, not the fix;
- the docstring is explicitly framed 'stated as desired behaviour, not as an edit';
- impl fully elided.

Multiple implementations satisfy the stated property (the bundle's own verified impl uses a backward per-position loop, not comprehensions), so the 'single snapshot / order-independent' phrasing is the correctness property any prune spec must state, not the mask-rebuild implementation. All repo binding (file:line, del desync bug, blocks_remove_mask) lives only in mapping.md / refinement.md, which are NOT part of the spec view. A consumer given only the spec view + public problem_statement cannot reconstruct the sympy diff; they must independently devise an aligned-prune fix. G-LEAK (lexical screen) also passed clean. No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
