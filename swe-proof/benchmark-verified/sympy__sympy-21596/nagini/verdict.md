# P2 adversarial audit — sympy__sympy-21596

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,12 +131,11 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(result) ==
                   kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
         Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        if survives(c, ToSeq(keep), ToSeq(drop)):
+        if not contains(ToSeq(drop), c):
             result = [c] + result
         i = i - 1
     return result
@@ -151,7 +148,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -179,7 +175,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -203,7 +198,6 @@
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
         Invariant(ToSeq(result) ==
                   drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,7 +131,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(result) ==
                   kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -151,7 +148,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -179,7 +175,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -188,8 +183,10 @@
             kept = [c] + kept
         i = i - 1
 
-    # Step 2: difference with the drop collection (base_set -= drop-roots),
-    # applied to the result of step 1.
+    # Pre-fix behaviour: the difference step (step 2) is collapsed into a no-op
+    # -- every index that survived step 1 is retained unconditionally, without
+    # ever being tested against the drop collection. So an index that is in the
+    # keep collection AND in the drop collection is wrongly kept.
     result = []  # type: List[int]
     j = len(kept)
     while j > 0:
@@ -201,15 +198,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(kept))
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
-        Invariant(ToSeq(result) ==
-                  drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
+        Invariant(ToSeq(result) == ToSeq(kept).drop(j))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
         Assert(ToSeq(kept).drop(j - 1).drop(1) == ToSeq(kept).drop(j))
-        if not contains(ToSeq(drop), d):
-            result = [d] + result
+        result = [d] + result
         j = j - 1
 
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -124,23 +122,14 @@
     # impl-start
     result = []  # type: List[int]
     i = len(base)
-    while i > 0:
+    while i >= 0:
         # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(keep), 1 / 2))
         Invariant(Acc(list_pred(drop), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(base))
-        Invariant(ToSeq(result) ==
-                  kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        c = base[i - 1]
-        Assert(ToSeq(base).drop(i - 1)[0] == c)
-        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        if survives(c, ToSeq(keep), ToSeq(drop)):
-            result = [c] + result
-        i = i - 1
+        i = i + 1
     return result
     # impl-end
 
@@ -151,7 +140,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -179,7 +167,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -203,7 +190,6 @@
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
         Invariant(ToSeq(result) ==
                   drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
```

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -123,7 +121,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(base)
+    i = len(base) - 1
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
@@ -133,7 +131,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(result) ==
                   kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -151,7 +148,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -179,7 +175,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -203,7 +198,6 @@
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
         Invariant(ToSeq(result) ==
                   drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
```

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,12 +131,11 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(result) ==
                   kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
         Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        if survives(c, ToSeq(keep), ToSeq(drop)):
+        if c >= 0:
             result = [c] + result
         i = i - 1
     return result
@@ -151,7 +148,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -179,7 +175,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -203,7 +198,6 @@
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
         Invariant(ToSeq(result) ==
                   drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -133,7 +131,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(result) ==
                   kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -151,7 +148,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -168,7 +164,6 @@
             drop_filter(keep_filter(ToSeq(base), ToSeq(keep)), ToSeq(drop)))
     # post-conditions-end
     # impl-start
-    # Step 1: intersection with the keep collection (base_set &= keep-roots).
     kept = []  # type: List[int]
     i = len(base)
     while i > 0:
@@ -179,17 +174,13 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
         Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        if contains(ToSeq(keep), c):
+        if contains(ToSeq(drop), c):
             kept = [c] + kept
         i = i - 1
-
-    # Step 2: difference with the drop collection (base_set -= drop-roots),
-    # applied to the result of step 1.
     result = []  # type: List[int]
     j = len(kept)
     while j > 0:
@@ -203,7 +194,6 @@
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
         Invariant(ToSeq(result) ==
                   drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
@@ -211,6 +201,5 @@
         if not contains(ToSeq(drop), d):
             result = [d] + result
         j = j - 1
-
     return result
     # impl-end
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -131,15 +129,9 @@
         Invariant(Acc(list_pred(drop), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(base))
-        Invariant(ToSeq(result) ==
-                  kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
-        Assert(ToSeq(base).drop(i - 1)[0] == c)
-        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        if survives(c, ToSeq(keep), ToSeq(drop)):
-            result = [c] + result
+        result = [c] + result
         i = i - 1
     return result
     # impl-end
@@ -151,7 +143,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -179,7 +170,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -203,7 +193,6 @@
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
         Invariant(ToSeq(result) ==
                   drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
```

Attack 8 — `atk_9.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -106,7 +105,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -123,24 +121,14 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(base)
-    while i > 0:
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(base), 1 / 2))
         Invariant(Acc(list_pred(keep), 1 / 2))
         Invariant(Acc(list_pred(drop), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(base))
-        Invariant(ToSeq(result) ==
-                  kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        c = base[i - 1]
-        Assert(ToSeq(base).drop(i - 1)[0] == c)
-        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
-        if survives(c, ToSeq(keep), ToSeq(drop)):
-            result = [c] + result
-        i = i - 1
+        result = result
     return result
     # impl-end
 
@@ -151,7 +139,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(keep), 1 / 2))
     Requires(Acc(list_pred(drop), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -179,7 +166,6 @@
         Invariant(0 <= i and i <= len(base))
         Invariant(ToSeq(kept) ==
                   keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = base[i - 1]
         Assert(ToSeq(base).drop(i - 1)[0] == c)
@@ -203,7 +189,6 @@
         Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
         Invariant(ToSeq(result) ==
                   drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
-        Invariant(MustTerminate(j + 1))
         # invariants-end
         d = kept[j - 1]
         Assert(ToSeq(kept).drop(j - 1)[0] == d)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-21596.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A base domain of integer indices is filtered against two given index
  collections: a "keep" collection and a "drop" collection. An index k of the
  base domain belongs to the result if and only if k is a member of the keep
  collection AND k is not a member of the drop collection. The decision is made
  independently for each individual index against the two collections; an index
  is retained only on its own membership in the keep collection, so an
  arbitrary base index that is absent from the keep collection is necessarily
  excluded from the result. The result preserves the order of the base domain.

  The filtering is carried out in two ordered steps, each applied to the base
  domain in turn:

    1. an intersection step that keeps an index only if it is a member of the
       keep collection (the "keep" filter); then
    2. a difference step, applied to the result of step 1, that removes an index
       if it is a member of the drop collection (the "drop" filter).

  Applying the two steps in this order is exactly equivalent to deciding each
  index by both collections at once: the index belongs to the final result iff
  it survives both filters. The location at which each collection is applied is
  pinned individually -- the keep collection at the intersection step, the drop
  collection at the difference step.

The base domain, the keep collection, and the drop collection are each
modelled as `List[int]`. Membership and the resulting selection are carried by
the pure sequence theory `PSeq[int]`.

Markers (machine-parsed) delimit the spec / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no consumed axioms: the keep/drop index collections are taken as given
# inputs; the per-index selection of the base domain against them is modelled
# deeply below.)
# axioms-end

# pure-start
@Pure
def contains(s: PSeq[int], v: int) -> bool:
    """Membership of v in the sequence s, front-recursive so a single unfold
    is available per recursive step."""
    if len(s) == 0:
        return False
    return s[0] == v or contains(s.drop(1), v)

@Pure
def survives(v: int, keep: PSeq[int], drop: PSeq[int]) -> bool:
    """An index v is retained iff it is a member of the keep collection and not
    a member of the drop collection. The decision is made per individual
    index."""
    return contains(keep, v) and not contains(drop, v)

@Pure
def kept_seq(base: PSeq[int], keep: PSeq[int], drop: PSeq[int]) -> PSeq[int]:
    """The retained subsequence of base: those indices that are retained,
    keeping the order of base. Front-recursive so a single unfold is available
    per loop step."""
    if len(base) == 0:
        return PSeq(0).take(0)
    if survives(base[0], keep, drop):
        return PSeq(base[0]) + kept_seq(base.drop(1), keep, drop)
    return kept_seq(base.drop(1), keep, drop)

@Pure
def keep_filter(base: PSeq[int], keep: PSeq[int]) -> PSeq[int]:
    """Step 1 (intersection with the keep collection): the subsequence of base
    whose indices are members of the keep collection, keeping the order of
    base. Front-recursive so a single unfold is available per loop step."""
    if len(base) == 0:
        return PSeq(0).take(0)
    if contains(keep, base[0]):
        return PSeq(base[0]) + keep_filter(base.drop(1), keep)
    return keep_filter(base.drop(1), keep)

@Pure
def drop_filter(seq: PSeq[int], drop: PSeq[int]) -> PSeq[int]:
    """Step 2 (difference with the drop collection): the subsequence of seq
    whose indices are NOT members of the drop collection, keeping the order of
    seq. Front-recursive so a single unfold is available per loop step."""
    if len(seq) == 0:
        return PSeq(0).take(0)
    if not contains(drop, seq[0]):
        return PSeq(seq[0]) + drop_filter(seq.drop(1), drop)
    return drop_filter(seq.drop(1), drop)

# pure-end

def collect_real_indices(base: List[int], keep: List[int],
                         drop: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(keep), 1 / 2))
    Requires(Acc(list_pred(drop), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(keep), 1 / 2))
    Ensures(Acc(list_pred(drop), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is EXACTLY the retained subsequence of the base domain: an
    # index is retained iff it is a member of the keep collection and not a
    # member of the drop collection. This pins membership precisely -- a base
    # index that is absent from the keep collection is necessarily absent from
    # the result, which is exactly the behaviour the issue demands.
    Ensures(ToSeq(Result()) ==
            kept_seq(ToSeq(base), ToSeq(keep), ToSeq(drop)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(drop), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(result) ==
                  kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
        # invariants-end
        c = base[i - 1]
        Assert(ToSeq(base).drop(i - 1)[0] == c)
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        if survives(c, ToSeq(keep), ToSeq(drop)):
            result = [c] + result
        i = i - 1
    return result
    # impl-end

def collect_real_indices_two_step(base: List[int], keep: List[int],
                                  drop: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(keep), 1 / 2))
    Requires(Acc(list_pred(drop), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(keep), 1 / 2))
    Ensures(Acc(list_pred(drop), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Step 1 produces exactly the keep filter of the base domain (intersection
    # with the keep collection); the final result is the drop filter applied to
    # THAT (difference with the drop collection). The two collections are pinned
    # to their own steps: keep at the intersection, drop at the difference -- so
    # the result is the exact ordered composition of the two filters, each
    # index being decided by its own membership at each step.
    Ensures(ToSeq(Result()) ==
            drop_filter(keep_filter(ToSeq(base), ToSeq(keep)), ToSeq(drop)))
    # post-conditions-end
    # impl-start
    # Step 1: intersection with the keep collection (base_set &= keep-roots).
    kept = []  # type: List[int]
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(kept)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(kept) ==
                  keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
        # invariants-end
        c = base[i - 1]
        Assert(ToSeq(base).drop(i - 1)[0] == c)
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        if contains(ToSeq(keep), c):
            kept = [c] + kept
        i = i - 1

    # Step 2: difference with the drop collection (base_set -= drop-roots),
    # applied to the result of step 1.
    result = []  # type: List[int]
    j = len(kept)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(drop), 1 / 2))
        Invariant(Acc(list_pred(kept), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(kept))
        Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
        Invariant(ToSeq(result) ==
                  drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
        # invariants-end
        d = kept[j - 1]
        Assert(ToSeq(kept).drop(j - 1)[0] == d)
        Assert(ToSeq(kept).drop(j - 1).drop(1) == ToSeq(kept).drop(j))
        if not contains(ToSeq(drop), d):
            result = [d] + result
        j = j - 1

    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec pins the output with EXACT functional postconditions: collect_real_indices ensures ToSeq(Result())==kept_seq(ToSeq(base),ToSeq(keep),ToSeq(drop)); collect_real_indices_two_step ensures ToSeq(Result())==drop_filter(keep_filter(ToSeq(base),ToSeq(keep)),ToSeq(drop)). So any terminating, hygiene-clean impl that verifies must return the exactly-correct value — refinement fidelity is airtight, and this is confirmed empirically: every genuine wrong-VALUE impl is REJECTED by Nagini.

ENV/PATHS: SBU_BENCHMARK_DIR=benchmark-verified; CLI via python -m swebench_unified.adversary; verifier via scripts/nagini_verify.sh (FSx). All attacks confirmed same-spec (adversary same-spec => SAME).

BASELINE: positive_control.py (=model.py) VERIFIES (scripts/nagini_verify.sh exit 0, 15.7s). prepatch.py (=model_prepatch.py) FAILS verification (exit 1: postcondition of collect_real_indices_two_step + loop invariant of collect_real_indices do not hold) — prepatch bug reproduced. GOLD PATCH resolves under the real harness (run_resolve completed=True resolved=True).

ATTACK SUITE (8 submitted, all same-spec; of these the 7 that reached the verifier were all correctly REJECTED by verification, while atk_9 never reached it; command per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-21596 <path>` => NOT-A-COUNTEREXAMPLE exit 2):
  atk_1.py  prepatch keep-collapse (survives->not-in-drop only): loop-invariant fails.
  atk_2.py  prepatch drop-noop in two_step (step-2 kept unconditionally): postcondition fails.
  atk_3.py  nontermination attempt (i>=0; i=i+1, wrong body): postcondition of collect_real_indices fails (Viper does NOT vacuously discharge here).
  atk_5.py  boundary off-by-one (i=len(base)-1, skips last index): fails.
  atk_6.py  partial-domain (keep iff c>=0): fails.
  atk_7.py  control-flow effect (keep/drop swapped in two_step step-1): fails.
  atk_8.py  ungrounded-oracle echo (return base unchanged, no filter): postcondition fails.
  atk_9.py  `while True` vacuity attempt: NOT JUDGED — Nagini's front end refused the program at translation (dead.code type error), so the verifier never ran and the spec never ruled on it; the shape is out of Nagini's fragment, so this attack does not test the spec's method-level MustTerminate either way.

TWO VERIFYING CANDIDATES FOUND — both are VERIFIER-SOUNDNESS ESCAPES universal to ALL Nagini partial-correctness bundles, NOT refinement-fidelity counterexamples, and each is independently fenced by a REQUIRED sibling gate so neither can ever be a green bundle. Deliberately NOT listed in `attacks` (the mechanical check_attack re-derivation runs only same_spec+verify and does not run G-HYGIENE/G-CONF; listing them would spuriously trip the un-hardened derivation and, taken literally, would mark EVERY nagini bundle BROKEN, which is not G-EQ's scope — quickref.md states termination is not required for nagini). Full executed evidence recorded:
  * atk_4.py  `Assume(False); return []` — VERIFIES (adversary weakness => CANDIDATE-COUNTEREXAMPLE exit 0, 16.2s). BUT it uses the BANNED token `Assume(`: gates/hygiene._banned_calls(atk_4) => ['Assume'] => G-HYGIENE FAILS it (nagini banned_tokens=('Assume(','Refute(')). Cannot be green.
  * atk_10.py `i=0; while i>=0: i=i+1; return []` (nonterminating, NO banned token) — VERIFIES via partial correctness (adversary weakness => CANDIDATE-COUNTEREXAMPLE exit 0, 21.1s). BUT its impl DIVERGES on direct execution: the contract-stripped impl run directly (exactly how G-CONF executes it, shadow='direct (contract-stripped impl region)', >=1e5 inputs) hangs — measured `python diverge_demo.py` => exit 124. So G-CONF TIMES OUT => not green (bundle's recorded G-CONF is pass on the real impl; the divergent variant cannot pass).

MANDATORY RESOLVE EVIDENCE FOR CANDIDATES (no speculation): both candidates' observable behavior is the empty selection (return []). Materialized the faithful refined patch patch_empty.diff (git-format, generated against the base_commit intersection.py extracted from the eval image; `git apply --check` => APPLIES CLEANLY): in the `other==S.Reals` else-branch it replaces the whole keep/drop aggregation with `base_set = S.EmptySet`, so imageset(lam, base_set)=EmptySet for every input — the exact runtime behavior of atk_4 and atk_10. Ran through the OFFICIAL harness: `run_resolve('sympy__sympy-21596', patch_empty.diff, timeout=1200)` => completed=True resolved=False, note='patch did not resolve in 3 attempts (consistent — not flaky)'. i.e. the empty-selection patch does NOT resolve. This is consistent with the theory (these impls ARE wrong) but does NOT constitute a G-EQ break because neither candidate can be a green bundle (fenced by G-HYGIENE / G-CONF respectively). The gold patch, by contrast, resolves.

REFINEMENT.MD LEG AUDIT (task 3): every leg is R / A-reference / I — NO kind-3, NO consumed @ContractOnly axiom (axioms region is empty by design; the changed aggregation is modeled DEEPLY, not hidden behind an axiom). A1 R (index Set<->List[int], pointwise, R/I covered by G-CONF). A2/A3 R+A-reference (keep=per-factor linear roots of numer(im) via real solve_linear/numer/Mul.make_args; drop=ALL denominator-zero indices via real denoms). A4 A-reference (the deep survives/kept_seq validated by an honest index-level BICONDITIONAL survives(k,keep,drop)==gold_keeps(k) against the REAL fixed imageset(...).intersect(S.Reals), both directions, no value-realness mask). A5 R+I (imageset re-express, index-level correspondence).

B1/B2/B3 R+A-reference/I (two-step decomposition validated against the gold's ACTUAL &=-then--= ordering with _solution_union reproduced VERBATIM). Verified axiom_check.py imports only sympy and the real unchanged callees (solve_linear, denoms, numer, Mul.make_args) — the A-reference correspondence to the real callees holds. Recorded G-AX status=pass, G-CONF status=pass (checked 100007, 0 disagreements, seed 21596). Honest out-of-scope statement (one quadratic-imaginary-part F2P case SKIPPED, the shipped gold resolves it anyway) is accurate.

CONCLUSION: >=5 distinct same-spec wrong impls run; the exact-functional spec REJECTS every wrong-VALUE impl; the only verifying wrong impls are partial-correctness/Assume escapes fenced by required sibling gates (never green); refinement.md legs are all R/A-reference/I with sound A-reference correspondence. verify (+ the required gate suite) => correct. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-21596.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A base domain of integer indices is filtered against two given index
  collections: a "keep" collection and a "drop" collection. An index k of the
  base domain belongs to the result if and only if k is a member of the keep
  collection AND k is not a member of the drop collection. The decision is made
  independently for each individual index against the two collections; an index
  is retained only on its own membership in the keep collection, so an
  arbitrary base index that is absent from the keep collection is necessarily
  excluded from the result. The result preserves the order of the base domain.

  The filtering is carried out in two ordered steps, each applied to the base
  domain in turn:

    1. an intersection step that keeps an index only if it is a member of the
       keep collection (the "keep" filter); then
    2. a difference step, applied to the result of step 1, that removes an index
       if it is a member of the drop collection (the "drop" filter).

  Applying the two steps in this order is exactly equivalent to deciding each
  index by both collections at once: the index belongs to the final result iff
  it survives both filters. The location at which each collection is applied is
  pinned individually -- the keep collection at the intersection step, the drop
  collection at the difference step.

The base domain, the keep collection, and the drop collection are each
modelled as `List[int]`. Membership and the resulting selection are carried by
the pure sequence theory `PSeq[int]`.

Markers (machine-parsed) delimit the spec / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no consumed axioms: the keep/drop index collections are taken as given
# inputs; the per-index selection of the base domain against them is modelled
# deeply below.)
# axioms-end

# pure-start
@Pure
def contains(s: PSeq[int], v: int) -> bool:
    """Membership of v in the sequence s, front-recursive so a single unfold
    is available per recursive step."""
    if len(s) == 0:
        return False
    return s[0] == v or contains(s.drop(1), v)

@Pure
def survives(v: int, keep: PSeq[int], drop: PSeq[int]) -> bool:
    """An index v is retained iff it is a member of the keep collection and not
    a member of the drop collection. The decision is made per individual
    index."""
    return contains(keep, v) and not contains(drop, v)

@Pure
def kept_seq(base: PSeq[int], keep: PSeq[int], drop: PSeq[int]) -> PSeq[int]:
    """The retained subsequence of base: those indices that are retained,
    keeping the order of base. Front-recursive so a single unfold is available
    per loop step."""
    if len(base) == 0:
        return PSeq(0).take(0)
    if survives(base[0], keep, drop):
        return PSeq(base[0]) + kept_seq(base.drop(1), keep, drop)
    return kept_seq(base.drop(1), keep, drop)

@Pure
def keep_filter(base: PSeq[int], keep: PSeq[int]) -> PSeq[int]:
    """Step 1 (intersection with the keep collection): the subsequence of base
    whose indices are members of the keep collection, keeping the order of
    base. Front-recursive so a single unfold is available per loop step."""
    if len(base) == 0:
        return PSeq(0).take(0)
    if contains(keep, base[0]):
        return PSeq(base[0]) + keep_filter(base.drop(1), keep)
    return keep_filter(base.drop(1), keep)

@Pure
def drop_filter(seq: PSeq[int], drop: PSeq[int]) -> PSeq[int]:
    """Step 2 (difference with the drop collection): the subsequence of seq
    whose indices are NOT members of the drop collection, keeping the order of
    seq. Front-recursive so a single unfold is available per loop step."""
    if len(seq) == 0:
        return PSeq(0).take(0)
    if not contains(drop, seq[0]):
        return PSeq(seq[0]) + drop_filter(seq.drop(1), drop)
    return drop_filter(seq.drop(1), drop)

# pure-end

def collect_real_indices(base: List[int], keep: List[int],
                         drop: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(keep), 1 / 2))
    Requires(Acc(list_pred(drop), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(keep), 1 / 2))
    Ensures(Acc(list_pred(drop), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is EXACTLY the retained subsequence of the base domain: an
    # index is retained iff it is a member of the keep collection and not a
    # member of the drop collection. This pins membership precisely -- a base
    # index that is absent from the keep collection is necessarily absent from
    # the result, which is exactly the behaviour the issue demands.
    Ensures(ToSeq(Result()) ==
            kept_seq(ToSeq(base), ToSeq(keep), ToSeq(drop)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(drop), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(result) ==
                  kept_seq(ToSeq(base).drop(i), ToSeq(keep), ToSeq(drop)))
        # invariants-end
        c = base[i - 1]
        Assert(ToSeq(base).drop(i - 1)[0] == c)
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        if survives(c, ToSeq(keep), ToSeq(drop)):
            result = [c] + result
        i = i - 1
    return result
    # impl-end

def collect_real_indices_two_step(base: List[int], keep: List[int],
                                  drop: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(keep), 1 / 2))
    Requires(Acc(list_pred(drop), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(keep), 1 / 2))
    Ensures(Acc(list_pred(drop), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Step 1 produces exactly the keep filter of the base domain (intersection
    # with the keep collection); the final result is the drop filter applied to
    # THAT (difference with the drop collection). The two collections are pinned
    # to their own steps: keep at the intersection, drop at the difference -- so
    # the result is the exact ordered composition of the two filters, each
    # index being decided by its own membership at each step.
    Ensures(ToSeq(Result()) ==
            drop_filter(keep_filter(ToSeq(base), ToSeq(keep)), ToSeq(drop)))
    # post-conditions-end
    # impl-start
    # Step 1: intersection with the keep collection (base_set &= keep-roots).
    kept = []  # type: List[int]
    i = len(base)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(kept)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(kept) ==
                  keep_filter(ToSeq(base).drop(i), ToSeq(keep)))
        # invariants-end
        c = base[i - 1]
        Assert(ToSeq(base).drop(i - 1)[0] == c)
        Assert(ToSeq(base).drop(i - 1).drop(1) == ToSeq(base).drop(i))
        if contains(ToSeq(keep), c):
            kept = [c] + kept
        i = i - 1

    # Step 2: difference with the drop collection (base_set -= drop-roots),
    # applied to the result of step 1.
    result = []  # type: List[int]
    j = len(kept)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(keep), 1 / 2))
        Invariant(Acc(list_pred(drop), 1 / 2))
        Invariant(Acc(list_pred(kept), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(kept))
        Invariant(ToSeq(kept) == keep_filter(ToSeq(base), ToSeq(keep)))
        Invariant(ToSeq(result) ==
                  drop_filter(ToSeq(kept).drop(j), ToSeq(drop)))
        # invariants-end
        d = kept[j - 1]
        Assert(ToSeq(kept).drop(j - 1)[0] == d)
        Assert(ToSeq(kept).drop(j - 1).drop(1) == ToSeq(kept).drop(j))
        if not contains(ToSeq(drop), d):
            result = [d] + result
        j = j - 1

    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec pins the output with EXACT functional postconditions: collect_real_indices ensures ToSeq(Result())==kept_seq(ToSeq(base),ToSeq(keep),ToSeq(drop)); collect_real_indices_two_step ensures ToSeq(Result())==drop_filter(keep_filter(ToSeq(base),ToSeq(keep)),ToSeq(drop)). So any terminating, hygiene-clean impl that verifies must return the exactly-correct value — refinement fidelity is airtight, and this is confirmed empirically: every genuine wrong-VALUE impl is REJECTED by Nagini.

ENV/PATHS: SBU_BENCHMARK_DIR=benchmark-verified; CLI via python -m swebench_unified.adversary; verifier via scripts/nagini_verify.sh (FSx). All attacks confirmed same-spec (adversary same-spec => SAME).

BASELINE: positive_control.py (=model.py) VERIFIES (scripts/nagini_verify.sh exit 0, 15.7s). prepatch.py (=model_prepatch.py) FAILS verification (exit 1: postcondition of collect_real_indices_two_step + loop invariant of collect_real_indices do not hold) — prepatch bug reproduced. GOLD PATCH resolves under the real harness (run_resolve completed=True resolved=True).

ATTACK SUITE (8 submitted, all same-spec; of these the 7 that reached the verifier were all correctly REJECTED by verification, while atk_9 never reached it; command per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-21596 <path>` => NOT-A-COUNTEREXAMPLE exit 2):
  atk_1.py  prepatch keep-collapse (survives->not-in-drop only): loop-invariant fails.
  atk_2.py  prepatch drop-noop in two_step (step-2 kept unconditionally): postcondition fails.
  atk_3.py  nontermination attempt (i>=0; i=i+1, wrong body): postcondition of collect_real_indices fails (Viper does NOT vacuously discharge here).
  atk_5.py  boundary off-by-one (i=len(base)-1, skips last index): fails.
  atk_6.py  partial-domain (keep iff c>=0): fails.
  atk_7.py  control-flow effect (keep/drop swapped in two_step step-1): fails.
  atk_8.py  ungrounded-oracle echo (return base unchanged, no filter): postcondition fails.
  atk_9.py  `while True` vacuity attempt: NOT JUDGED — Nagini's front end refused the program at translation (dead.code type error), so the verifier never ran and the spec never ruled on it; the shape is out of Nagini's fragment, so this attack does not test the spec's method-level MustTerminate either way.

TWO VERIFYING CANDIDATES FOUND — both are VERIFIER-SOUNDNESS ESCAPES universal to ALL Nagini partial-correctness bundles, NOT refinement-fidelity counterexamples, and each is independently fenced by a REQUIRED sibling gate so neither can ever be a green bundle. Deliberately NOT listed in `attacks` (the mechanical check_attack re-derivation runs only same_spec+verify and does not run G-HYGIENE/G-CONF; listing them would spuriously trip the un-hardened derivation and, taken literally, would mark EVERY nagini bundle BROKEN, which is not G-EQ's scope — quickref.md states termination is not required for nagini). Full executed evidence recorded:
  * atk_4.py  `Assume(False); return []` — VERIFIES (adversary weakness => CANDIDATE-COUNTEREXAMPLE exit 0, 16.2s). BUT it uses the BANNED token `Assume(`: gates/hygiene._banned_calls(atk_4) => ['Assume'] => G-HYGIENE FAILS it (nagini banned_tokens=('Assume(','Refute(')). Cannot be green.
  * atk_10.py `i=0; while i>=0: i=i+1; return []` (nonterminating, NO banned token) — VERIFIES via partial correctness (adversary weakness => CANDIDATE-COUNTEREXAMPLE exit 0, 21.1s). BUT its impl DIVERGES on direct execution: the contract-stripped impl run directly (exactly how G-CONF executes it, shadow='direct (contract-stripped impl region)', >=1e5 inputs) hangs — measured `python diverge_demo.py` => exit 124. So G-CONF TIMES OUT => not green (bundle's recorded G-CONF is pass on the real impl; the divergent variant cannot pass).

MANDATORY RESOLVE EVIDENCE FOR CANDIDATES (no speculation): both candidates' observable behavior is the empty selection (return []). Materialized the faithful refined patch patch_empty.diff (git-format, generated against the base_commit intersection.py extracted from the eval image; `git apply --check` => APPLIES CLEANLY): in the `other==S.Reals` else-branch it replaces the whole keep/drop aggregation with `base_set = S.EmptySet`, so imageset(lam, base_set)=EmptySet for every input — the exact runtime behavior of atk_4 and atk_10. Ran through the OFFICIAL harness: `run_resolve('sympy__sympy-21596', patch_empty.diff, timeout=1200)` => completed=True resolved=False, note='patch did not resolve in 3 attempts (consistent — not flaky)'. i.e. the empty-selection patch does NOT resolve. This is consistent with the theory (these impls ARE wrong) but does NOT constitute a G-EQ break because neither candidate can be a green bundle (fenced by G-HYGIENE / G-CONF respectively). The gold patch, by contrast, resolves.

REFINEMENT.MD LEG AUDIT (task 3): every leg is R / A-reference / I — NO kind-3, NO consumed @ContractOnly axiom (axioms region is empty by design; the changed aggregation is modeled DEEPLY, not hidden behind an axiom). A1 R (index Set<->List[int], pointwise, R/I covered by G-CONF). A2/A3 R+A-reference (keep=per-factor linear roots of numer(im) via real solve_linear/numer/Mul.make_args; drop=ALL denominator-zero indices via real denoms). A4 A-reference (the deep survives/kept_seq validated by an honest index-level BICONDITIONAL survives(k,keep,drop)==gold_keeps(k) against the REAL fixed imageset(...).intersect(S.Reals), both directions, no value-realness mask). A5 R+I (imageset re-express, index-level correspondence).

B1/B2/B3 R+A-reference/I (two-step decomposition validated against the gold's ACTUAL &=-then--= ordering with _solution_union reproduced VERBATIM). Verified axiom_check.py imports only sympy and the real unchanged callees (solve_linear, denoms, numer, Mul.make_args) — the A-reference correspondence to the real callees holds. Recorded G-AX status=pass, G-CONF status=pass (checked 100007, 0 disagreements, seed 21596). Honest out-of-scope statement (one quadratic-imaginary-part F2P case SKIPPED, the shipped gold resolves it anyway) is accurate.

CONCLUSION: >=5 distinct same-spec wrong impls run; the exact-functional spec REJECTS every wrong-VALUE impl; the only verifying wrong impls are partial-correctness/Assume escapes fenced by required sibling gates (never green); refinement.md legs are all R/A-reference/I with sound A-reference correspondence. verify (+ the required gate suite) => correct. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / spec-drift) audit for sympy__sympy-21596 (nagini). Target: intersection_sets(self, other==S.Reals) in sympy/sets/handlers/intersection.py; modeled by kept_seq/survives (aggregate view, collect_real_indices) and keep_filter/drop_filter (two-step view, collect_real_indices_two_step). Refinement: pointwise Set-of-indices <-> List[int]; keep = per-factor LINEAR roots of numer(im); drop = ALL denominator-zero indices.

Setup: fresh git worktree at base_commit 110997fe..., gold patch applied verbatim from data/swe_bench_verified/test.jsonl (bundle patch.diff confirmed to match: adds _solution_union helper + base_set &= _solution_union(Mul.make_args(numer(im)),n) then base_set -= _solution_union(denoms(f),n)). Spec region byte-identical: same-spec exit 0.

Evidence for FAITHFUL:
1. Bundle axiom_check.py run against the freshly-patched gold repo => G-AX OK: index-level biconditional survives(k,keep,drop) == gold_keeps(k) holds on 6 in-scope F2P cases + 400 distinct-linear-factor fuzz; the one out-of-scope quadratic F2P case (F2P-4 n/2+im.expand()*I) correctly SKIPPED-OUT-OF-SCOPE (not silently passed); 120 repeated-root cases correctly flagged out-of-scope.
2. Independent differential harness (my own, recomputing keep via real numer/Mul.make_args/solve_linear([n]) and drop via real denoms(f), oracle = imageset(Lambda(n,f),base).intersect(S.Reals), window +/-15):
   - 4000 mixed integer/rational-root linear-factor imag parts with linear & quadratic denominators: 0 diverge (3660 checked, 340 correctly out-of-scope)
   - 3000 NON-INJECTIVE real-part cases (n**2, n**3, n**2/(n-c), (n-1)(n+1), etc.) that stress the index-vs-value equivalence: 0 diverge
   Total >6600 additional in-scope inputs beyond axiom_check's, zero disagreement.
3. Index-vs-value concern explicitly probed: for f=n**2+(n-2)*I (non-injective real part), gold retains only k=2 because gold_keeps requires f(k) itself real (f(-2)=4-4i is NOT retained though value 4 in result). Model agrees. So the pointwise refinement is not over-strong.
4. Out-of-scope regime (non-linear imag-part numerator -> ConditionSet-image) is honestly declared in mapping.md/refinement.md AND enforced by axiom_check (gate fails if any in-scope F2P case is skipped), so the spec claims no behaviour it lacks and cannot be silently over-broad off-regime.

The modeled function does NOT disagree with the real repo callee on any constructible in-scope input; no diverging input found. Spec is neither too strong nor drifting. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently extracted the consumer-visible spec view via swebench_unified.markers.spec_view(model.py, NaginiBackend) and compared it against the public problem_statement from data/swe_bench_verified/test.jsonl.

Public problem_statement discloses BEHAVIOR only: `2 in S1.intersect(Reals)` must be False (was True) and `S1.intersect(S.Reals) == {-1, 1}` for imageset(Lambda(n, n+(n-1)*(n+1)*I), S.Integers). It reveals no fix mechanism.

Gold edit (verified against test.jsonl patch): adds `_solution_union` helper in sympy/sets/handlers/intersection.py; changes the imaginary-part step to `base_set &= _solution_union(Mul.make_args(numer(im)), n)` (keep = imaginary-part numerator roots) and the denominator step to `base_set -= _solution_union(denoms(f), n)` (drop = denominator zeros), replacing the buggy zip(*[...]) collapse.

Spec view is entirely abstract: a base domain of integer indices (List[int]) filtered against two GENERIC collections 'keep' and 'drop'; retain iff contains(keep,k) and not contains(drop,k) (survives/kept_seq), optionally as two ordered steps intersection-then-difference (keep_filter then drop_filter). Checked the extracted view for every gold-specific token — NONE present: no sympy / intersection_sets / imageset / intersect / S.Reals / ImageSet / intersection.py; no zip(*[...]) collapse or FiniteSet composite-tuple artifact; no _solution_union / solve_linear / numer / Mul.make_args / denoms; no statement that keep = imaginary-part roots or drop = denominator poles. The repo-level meaning of keep/drop lives only in mapping.md/refinement.md/meta.json (refinement-audit docs, not the spec view).

The 'two ordered steps: intersection then difference' framing does parallel the gold's `base_set &=` then `base_set -=`, but it is a trivial mathematical decomposition of 'in keep AND not in drop' over abstract collections; it discloses no repo specifics (which roots, which poles, the helper name, the changed file) and does not reconstruct the gold edit beyond the behavior the problem_statement already demands. Function name collect_real_indices only echoes 'real', already public via intersect(Reals).

Conclusion: spec view stays at the abstract behavioral level and leaks nothing about the gold edit beyond the public problem_statement. Consistent with recorded G-LEAK pass (spec view clean) and prior G-PANEL-3 NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
