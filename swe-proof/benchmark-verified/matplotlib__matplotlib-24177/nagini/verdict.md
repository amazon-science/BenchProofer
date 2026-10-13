# P2 adversarial audit — matplotlib__matplotlib-24177

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,10 +74,6 @@
     """The front-recursive maximum dominates every element of the sequence."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # The proof recurses on the tail, so the obligation must be a MEASURE that
-    # shrinks with the sequence: a constant could never be strictly below itself
-    # at the recursive site.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
@@ -102,9 +97,6 @@
     sequence (tightness -- the bound is one of the inputs, not larger)."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # As above: the proof recurses on the tail, so the obligation shrinks with
-    # the sequence rather than being a constant.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
@@ -128,9 +120,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(verts), 1 / 2))
     Requires(len(verts) >= 1)
-    # Strictly above the two lemmas' own measure (len of the sequence they are
-    # applied to, i.e. len(verts)), which is what lets this method call them.
-    Requires(MustTerminate(len(verts) + 1))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(verts), 1 / 2))
@@ -145,36 +134,5 @@
                                    and Result() == verts[j])))
     # post-conditions-end
     # impl-start
-    lemma_seq_max_dominates(ToSeq(verts))
-    best = verts[len(verts) - 1]
-    i = len(verts) - 1
-    sq = ToSeq(verts)  # type: PSeq[int]
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(verts), 1 / 2))
-        Invariant(0 <= i and i < len(verts))
-        Invariant(best == seq_max(ToSeq(verts).drop(i)))
-        # Carries the element count across the scan, so the enclosing method's
-        # own measure is still known once the scan is done and the lemmas below
-        # can still be applied.
-        Invariant(sq == ToSeq(verts))
-        # The scan counts down to 0, so i + 1 stays positive and strictly
-        # decreases each step.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
-        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
-        if verts[i - 1] > best:
-            best = verts[i - 1]
-        i = i - 1
-    Assert(i == 0)
-    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
-    Assert(best == seq_max(ToSeq(verts)))
-    lemma_seq_max_dominates(ToSeq(verts))
-    lemma_seq_max_attained(ToSeq(verts))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          ToSeq(verts)[k] == verts[k]))))
-    return best
+    return verts[0]
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,10 +74,6 @@
     """The front-recursive maximum dominates every element of the sequence."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # The proof recurses on the tail, so the obligation must be a MEASURE that
-    # shrinks with the sequence: a constant could never be strictly below itself
-    # at the recursive site.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
@@ -102,9 +97,6 @@
     sequence (tightness -- the bound is one of the inputs, not larger)."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # As above: the proof recurses on the tail, so the obligation shrinks with
-    # the sequence rather than being a constant.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
@@ -128,9 +120,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(verts), 1 / 2))
     Requires(len(verts) >= 1)
-    # Strictly above the two lemmas' own measure (len of the sequence they are
-    # applied to, i.e. len(verts)), which is what lets this method call them.
-    Requires(MustTerminate(len(verts) + 1))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(verts), 1 / 2))
@@ -145,36 +134,5 @@
                                    and Result() == verts[j])))
     # post-conditions-end
     # impl-start
-    lemma_seq_max_dominates(ToSeq(verts))
-    best = verts[len(verts) - 1]
-    i = len(verts) - 1
-    sq = ToSeq(verts)  # type: PSeq[int]
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(verts), 1 / 2))
-        Invariant(0 <= i and i < len(verts))
-        Invariant(best == seq_max(ToSeq(verts).drop(i)))
-        # Carries the element count across the scan, so the enclosing method's
-        # own measure is still known once the scan is done and the lemmas below
-        # can still be applied.
-        Invariant(sq == ToSeq(verts))
-        # The scan counts down to 0, so i + 1 stays positive and strictly
-        # decreases each step.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
-        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
-        if verts[i - 1] > best:
-            best = verts[i - 1]
-        i = i - 1
-    Assert(i == 0)
-    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
-    Assert(best == seq_max(ToSeq(verts)))
-    lemma_seq_max_dominates(ToSeq(verts))
-    lemma_seq_max_attained(ToSeq(verts))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          ToSeq(verts)[k] == verts[k]))))
-    return best
+    return verts[len(verts) - 1]
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,10 +74,6 @@
     """The front-recursive maximum dominates every element of the sequence."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # The proof recurses on the tail, so the obligation must be a MEASURE that
-    # shrinks with the sequence: a constant could never be strictly below itself
-    # at the recursive site.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
@@ -102,9 +97,6 @@
     sequence (tightness -- the bound is one of the inputs, not larger)."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # As above: the proof recurses on the tail, so the obligation shrinks with
-    # the sequence rather than being a constant.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
@@ -128,9 +120,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(verts), 1 / 2))
     Requires(len(verts) >= 1)
-    # Strictly above the two lemmas' own measure (len of the sequence they are
-    # applied to, i.e. len(verts)), which is what lets this method call them.
-    Requires(MustTerminate(len(verts) + 1))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(verts), 1 / 2))
@@ -145,36 +134,13 @@
                                    and Result() == verts[j])))
     # post-conditions-end
     # impl-start
-    lemma_seq_max_dominates(ToSeq(verts))
     best = verts[len(verts) - 1]
     i = len(verts) - 1
-    sq = ToSeq(verts)  # type: PSeq[int]
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(verts), 1 / 2))
         Invariant(0 <= i and i < len(verts))
-        Invariant(best == seq_max(ToSeq(verts).drop(i)))
-        # Carries the element count across the scan, so the enclosing method's
-        # own measure is still known once the scan is done and the lemmas below
-        # can still be applied.
-        Invariant(sq == ToSeq(verts))
-        # The scan counts down to 0, so i + 1 stays positive and strictly
-        # decreases each step.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
-        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
-        if verts[i - 1] > best:
+        if verts[i - 1] < best:
             best = verts[i - 1]
         i = i - 1
-    Assert(i == 0)
-    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
-    Assert(best == seq_max(ToSeq(verts)))
-    lemma_seq_max_dominates(ToSeq(verts))
-    lemma_seq_max_attained(ToSeq(verts))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          ToSeq(verts)[k] == verts[k]))))
     return best
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,10 +74,6 @@
     """The front-recursive maximum dominates every element of the sequence."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # The proof recurses on the tail, so the obligation must be a MEASURE that
-    # shrinks with the sequence: a constant could never be strictly below itself
-    # at the recursive site.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
@@ -102,9 +97,6 @@
     sequence (tightness -- the bound is one of the inputs, not larger)."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # As above: the proof recurses on the tail, so the obligation shrinks with
-    # the sequence rather than being a constant.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
@@ -128,9 +120,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(verts), 1 / 2))
     Requires(len(verts) >= 1)
-    # Strictly above the two lemmas' own measure (len of the sequence they are
-    # applied to, i.e. len(verts)), which is what lets this method call them.
-    Requires(MustTerminate(len(verts) + 1))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(verts), 1 / 2))
@@ -145,36 +134,13 @@
                                    and Result() == verts[j])))
     # post-conditions-end
     # impl-start
-    lemma_seq_max_dominates(ToSeq(verts))
-    best = verts[len(verts) - 1]
-    i = len(verts) - 1
-    sq = ToSeq(verts)  # type: PSeq[int]
-    while i > 0:
-        # invariants-start
+    best = verts[0]
+    i = 0
+    while i < len(verts) - 1:
         Invariant(Acc(list_pred(verts), 1 / 2))
-        Invariant(0 <= i and i < len(verts))
-        Invariant(best == seq_max(ToSeq(verts).drop(i)))
-        # Carries the element count across the scan, so the enclosing method's
-        # own measure is still known once the scan is done and the lemmas below
-        # can still be applied.
-        Invariant(sq == ToSeq(verts))
-        # The scan counts down to 0, so i + 1 stays positive and strictly
-        # decreases each step.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
-        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
-        if verts[i - 1] > best:
-            best = verts[i - 1]
-        i = i - 1
-    Assert(i == 0)
-    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
-    Assert(best == seq_max(ToSeq(verts)))
-    lemma_seq_max_dominates(ToSeq(verts))
-    lemma_seq_max_attained(ToSeq(verts))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          ToSeq(verts)[k] == verts[k]))))
+        Invariant(0 <= i and i <= len(verts) - 1)
+        if verts[i] > best:
+            best = verts[i]
+        i = i + 1
     return best
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,10 +74,6 @@
     """The front-recursive maximum dominates every element of the sequence."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # The proof recurses on the tail, so the obligation must be a MEASURE that
-    # shrinks with the sequence: a constant could never be strictly below itself
-    # at the recursive site.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
@@ -102,9 +97,6 @@
     sequence (tightness -- the bound is one of the inputs, not larger)."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # As above: the proof recurses on the tail, so the obligation shrinks with
-    # the sequence rather than being a constant.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
@@ -128,9 +120,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(verts), 1 / 2))
     Requires(len(verts) >= 1)
-    # Strictly above the two lemmas' own measure (len of the sequence they are
-    # applied to, i.e. len(verts)), which is what lets this method call them.
-    Requires(MustTerminate(len(verts) + 1))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(verts), 1 / 2))
@@ -146,35 +135,5 @@
     # post-conditions-end
     # impl-start
     lemma_seq_max_dominates(ToSeq(verts))
-    best = verts[len(verts) - 1]
-    i = len(verts) - 1
-    sq = ToSeq(verts)  # type: PSeq[int]
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(verts), 1 / 2))
-        Invariant(0 <= i and i < len(verts))
-        Invariant(best == seq_max(ToSeq(verts).drop(i)))
-        # Carries the element count across the scan, so the enclosing method's
-        # own measure is still known once the scan is done and the lemmas below
-        # can still be applied.
-        Invariant(sq == ToSeq(verts))
-        # The scan counts down to 0, so i + 1 stays positive and strictly
-        # decreases each step.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
-        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
-        if verts[i - 1] > best:
-            best = verts[i - 1]
-        i = i - 1
-    Assert(i == 0)
-    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
-    Assert(best == seq_max(ToSeq(verts)))
-    lemma_seq_max_dominates(ToSeq(verts))
-    lemma_seq_max_attained(ToSeq(verts))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          ToSeq(verts)[k] == verts[k]))))
-    return best
+    return seq_max(ToSeq(verts)) + 1
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,10 +74,6 @@
     """The front-recursive maximum dominates every element of the sequence."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # The proof recurses on the tail, so the obligation must be a MEASURE that
-    # shrinks with the sequence: a constant could never be strictly below itself
-    # at the recursive site.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
@@ -102,9 +97,6 @@
     sequence (tightness -- the bound is one of the inputs, not larger)."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # As above: the proof recurses on the tail, so the obligation shrinks with
-    # the sequence rather than being a constant.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
@@ -128,9 +120,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(verts), 1 / 2))
     Requires(len(verts) >= 1)
-    # Strictly above the two lemmas' own measure (len of the sequence they are
-    # applied to, i.e. len(verts)), which is what lets this method call them.
-    Requires(MustTerminate(len(verts) + 1))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(verts), 1 / 2))
@@ -145,36 +134,5 @@
                                    and Result() == verts[j])))
     # post-conditions-end
     # impl-start
-    lemma_seq_max_dominates(ToSeq(verts))
-    best = verts[len(verts) - 1]
-    i = len(verts) - 1
-    sq = ToSeq(verts)  # type: PSeq[int]
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(verts), 1 / 2))
-        Invariant(0 <= i and i < len(verts))
-        Invariant(best == seq_max(ToSeq(verts).drop(i)))
-        # Carries the element count across the scan, so the enclosing method's
-        # own measure is still known once the scan is done and the lemmas below
-        # can still be applied.
-        Invariant(sq == ToSeq(verts))
-        # The scan counts down to 0, so i + 1 stays positive and strictly
-        # decreases each step.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
-        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
-        if verts[i - 1] > best:
-            best = verts[i - 1]
-        i = i - 1
-    Assert(i == 0)
-    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
-    Assert(best == seq_max(ToSeq(verts)))
-    lemma_seq_max_dominates(ToSeq(verts))
-    lemma_seq_max_attained(ToSeq(verts))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          ToSeq(verts)[k] == verts[k]))))
-    return best
+    return 1000000000
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,10 +74,6 @@
     """The front-recursive maximum dominates every element of the sequence."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # The proof recurses on the tail, so the obligation must be a MEASURE that
-    # shrinks with the sequence: a constant could never be strictly below itself
-    # at the recursive site.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
@@ -102,9 +97,6 @@
     sequence (tightness -- the bound is one of the inputs, not larger)."""
     # pre-conditions-start
     Requires(len(s) >= 1)
-    # As above: the proof recurses on the tail, so the obligation shrinks with
-    # the sequence rather than being a constant.
-    Requires(MustTerminate(len(s)))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
@@ -128,9 +120,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(verts), 1 / 2))
     Requires(len(verts) >= 1)
-    # Strictly above the two lemmas' own measure (len of the sequence they are
-    # applied to, i.e. len(verts)), which is what lets this method call them.
-    Requires(MustTerminate(len(verts) + 1))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(verts), 1 / 2))
@@ -145,36 +134,13 @@
                                    and Result() == verts[j])))
     # post-conditions-end
     # impl-start
-    lemma_seq_max_dominates(ToSeq(verts))
     best = verts[len(verts) - 1]
     i = len(verts) - 1
-    sq = ToSeq(verts)  # type: PSeq[int]
-    while i > 0:
-        # invariants-start
+    while i >= 2:
         Invariant(Acc(list_pred(verts), 1 / 2))
         Invariant(0 <= i and i < len(verts))
-        Invariant(best == seq_max(ToSeq(verts).drop(i)))
-        # Carries the element count across the scan, so the enclosing method's
-        # own measure is still known once the scan is done and the lemmas below
-        # can still be applied.
-        Invariant(sq == ToSeq(verts))
-        # The scan counts down to 0, so i + 1 stays positive and strictly
-        # decreases each step.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
-        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
-        if verts[i - 1] > best:
-            best = verts[i - 1]
-        i = i - 1
-    Assert(i == 0)
-    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
-    Assert(best == seq_max(ToSeq(verts)))
-    lemma_seq_max_dominates(ToSeq(verts))
-    lemma_seq_max_attained(ToSeq(verts))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
-    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
-                                          ToSeq(verts)[k] == verts[k]))))
+        if verts[i - 2] > best:
+            best = verts[i - 2]
+        i = i - 2
     return best
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24177.

Behavioural contract (what the operation must guarantee):

  Given a non-empty sequence of numeric values, the operation returns an upper
  bound that is at least as large as EVERY element of the sequence: for all k,
  Result() >= values[k]. Equivalently, the returned bound encloses the whole
  sequence -- no element exceeds it -- and the bound is attained, i.e. it equals
  one of the input values rather than an arbitrary larger number.

The carrier is a sequence of numeric values; it is modelled as `List[int]`
(Nagini bans `str`/array indexing, and the tested behaviour is about WHICH
values are covered, not floating-point precision -- see refinement.md /
mapping.md). The pure sequence theory `PSeq[int]` carries the specification.

One unchanged helper is axiomatized: a sub-selection over the input sequence
whose only guaranteed property is MEMBERSHIP -- every value it yields already
occurs among the input values, and it never yields more values than the input
has. It carries no guarantee about which values it keeps (in particular, no
guarantee that the largest value is among them). Its soundness is checked
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def subsel_len(verts: PSeq[int]) -> int:
    """Number of values a sub-selection over `verts` yields: between zero and
    the full count (a sub-selection never yields more values than the input)."""
    Ensures(0 <= Result() and Result() <= len(verts))


@Pure
@ContractOnly
def subsel_at(verts: PSeq[int], idx: int) -> int:
    """The `idx`-th value of a sub-selection over `verts`. Its ONLY guaranteed
    property (the weakest sound contract) is MEMBERSHIP: every yielded value
    already occurs among the input values -- the result equals `verts[j]` for
    some in-bounds `j`. It carries no promise about which values are kept; in
    particular, no promise that the largest input value is among them.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(0 <= idx and idx < subsel_len(verts))
    Ensures(Exists(int, lambda j: (0 <= j and j < len(verts)
                                   and Result() == verts[j])))
# axioms-end


# pure-start
@Pure
def seq_max(s: PSeq[int]) -> int:
    """Largest value over a non-empty sequence. Front-recursive so a single
    unfold is available per loop step (index-recursion does not auto-unfold in
    Nagini 1.2.0)."""
    Requires(len(s) >= 1)
    if len(s) == 1:
        return s[0]
    return _imax(s[0], seq_max(s.drop(1)))


@Pure
def _imax(a: int, b: int) -> int:
    return a if a >= b else b
# pure-end


def lemma_seq_max_dominates(s: PSeq[int]) -> None:
    """The front-recursive maximum dominates every element of the sequence."""
    # pre-conditions-start
    Requires(len(s) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                           seq_max(s) >= s[k]))))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    if len(s) > 1:
        lemma_seq_max_dominates(s.drop(1))
        t = s.drop(1)  # type: PSeq[int]
        Assert(seq_max(s) == _imax(s[0], seq_max(t)))
        Assert(seq_max(s) >= seq_max(t))
        Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(s),
                                              s[k] == t[k - 1]))))
    # impl-end


def lemma_seq_max_attained(s: PSeq[int]) -> None:
    """The front-recursive maximum is attained: it equals some element of the
    sequence (tightness -- the bound is one of the inputs, not larger)."""
    # pre-conditions-start
    Requires(len(s) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
                                   and seq_max(s) == s[j])))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    if len(s) == 1:
        Assert(seq_max(s) == s[0])
    else:
        t = s.drop(1)  # type: PSeq[int]
        lemma_seq_max_attained(t)
        Assert(seq_max(s) == _imax(s[0], seq_max(t)))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(t),
                                              t[k] == s[k + 1]))))
    # impl-end


def enclosing_upper_bound(verts: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(verts), 1 / 2))
    Requires(len(verts) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(verts), 1 / 2))
    # The result is an upper bound over the whole input: it is at least as large
    # as every element. (Enclosing direction.)
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                           Result() >= verts[k]))))
    # The bound is ATTAINED: it equals one of the input elements, not an
    # arbitrary larger number. (Tightness direction -- excludes any padded
    # over-approximation of the true bound.)
    Ensures(Exists(int, lambda j: (0 <= j and j < len(verts)
                                   and Result() == verts[j])))
    # post-conditions-end
    # impl-start
    lemma_seq_max_dominates(ToSeq(verts))
    best = verts[len(verts) - 1]
    i = len(verts) - 1
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(verts), 1 / 2))
        Invariant(0 <= i and i < len(verts))
        Invariant(best == seq_max(ToSeq(verts).drop(i)))
        # invariants-end
        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
        if verts[i - 1] > best:
            best = verts[i - 1]
        i = i - 1
    Assert(i == 0)
    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
    Assert(best == seq_max(ToSeq(verts)))
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          ToSeq(verts)[k] == verts[k]))))
    return best
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY — matplotlib__matplotlib-24177 (nagini), G-EQ refinement fidelity (A-leg focus). VERDICT: SOUND.

tools run with SBU_BENCHMARK_DIR=benchmark-verified and SBU_PYTHON=python.

SPEC SHAPE: enclosing_upper_bound(verts) postconditions pin Result() to EXACTLY max(verts): (a) enclosing Forall k. Result()>=verts[k] AND (b) attained Exists j. Result()==verts[j]. Together these force any verifying impl to return the true per-axis maximum over ALL of verts. There is no slack for a wrong impl: undershooting the max fails (a); over-approximating (max+padding/constant) fails (b). Hence verify(model) => the gold full-gather behaviour => resolves. No candidate counterexample can exist, and none did.

BASELINES: positive_control.py (byte-identical model impl) -> nagini_verify.sh rc=0 (Verification successful, 18.1s). prepatch.py (bundle model_prepatch.py, folds over subsel_at membership-only subselection) -> `adversary weakness` rc=2 (does NOT verify): PREPATCH BUG REPRODUCED — fails exactly the enclosing Forall clause, which is the change G-DIFF senses.

ATTACKS (all copied model.py, edited ONLY the enclosing_upper_bound impl region; axioms/@Pure/Requires/Ensures byte-identical). Each confirmed SAME-spec (adversary same-spec rc=0) then run through `adversary weakness nagini matplotlib__matplotlib-24177 <f>`:
- atk_1.py (partial-domain: return verts[0]) -> weakness rc=2; verify error: Postcondition Forall(Result()>=verts[k]) might not hold.
- atk_2.py (partial-domain: return verts[len-1]) -> rc=2; Postcondition Forall enclosing fails.
- atk_3.py (control-flow-effect: flip comparison => computes MIN) -> rc=2; Postcondition Forall enclosing fails.
- atk_4.py (boundary/off-by-one: fold indices 0..len-2, skip LAST element) -> rc=2; Postcondition Forall enclosing fails.
- atk_5.py (ungrounded-oracle/padding: return seq_max(ToSeq(verts))+1) -> rc=2; verify error: Postcondition Exists(Result()==verts[j]) might not hold — the ATTAINED/tightness clause is load-bearing (dominates all but is not attained).
- atk_6.py (ungrounded constant: return 1000000000) -> rc=2; Postcondition Forall enclosing fails (and would fail attained too).
- atk_7.py (control-flow: stride-2 fold, inspects only every other index) -> rc=2; Postcondition Forall enclosing fails.

EXACT COMMANDS (per attack): `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-24177 <f>` (all rc=0, SAME) and `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-24177 <f>` (all rc=2, NOT-A-COUNTEREXAMPLE: does not verify). Direct `bash scripts/nagini_verify.sh <f>` confirmed the failures are GENUINE postcondition/enclosing errors (not infra/parse/timeout): atk_1,2,3,4,6,7 fail the enclosing Forall; atk_5 fails the attained Exists. Verifications were run concurrently in batches of 3 (each Nagini check spawns JVM+Z3).

RESULT: 0 of 7 same-spec wrong impls verified => no CANDIDATE => no faithful refined patch needed materializing/run_resolve (patches map empty, correctly). >=5 distinct-family attacks run (partial-domain x2, control-flow-effect x2, boundary x1, ungrounded-oracle/padding x2) — none breaks the spec.

REFINEMENT.MD A-LEG AUDIT: legs classified R/A/I with no kind-3 (§C confirmed). Two A-legs:
- A3 (A-reference): deep seq_max fold + verified loop == real per-axis max over Path.iter_bezier(simplify=False) full gather; dominance lemma = enclosing, attained lemma = tightness. Correspondence validated out-of-band by axiom_check.py check_full_gather_encloses (max(full)>=every vertex, min<=every vertex) over 4 boundary + regression + 4000 fuzz outlines. HOLDS.
- B1 (A-consumed): subsel_len/subsel_at membership+count axioms == real Path.iter_bezier() default (simplify=None) appearance-preserving condensation; weakest sound contract (membership only, promises nothing about extremes — exactly why the prepatch can't discharge enclosing). Validated by axiom_check.py check_condensation_membership + regression witness (condensed y-max 0.25 < true 0.33). HOLDS.
Both A-legs bind to real matplotlib callees (path.py:420 iter_bezier / _base.py:2437 gather). The changed op (gather source: all vertices vs condensation) is modeled DEEPLY as A-reference, not hidden behind an axiom-about-the-changed-fn. Correspondence sound.

CONCLUSION: verify => correct holds for this bundle. The spec is tight (max pinned by enclosing+attained), refinement map is faithful with valid A-leg correspondence, prepatch bug reproduced, positive control verifies. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24177.

Behavioural contract (what the operation must guarantee):

  Given a non-empty sequence of numeric values, the operation returns an upper
  bound that is at least as large as EVERY element of the sequence: for all k,
  Result() >= values[k]. Equivalently, the returned bound encloses the whole
  sequence -- no element exceeds it -- and the bound is attained, i.e. it equals
  one of the input values rather than an arbitrary larger number.

The carrier is a sequence of numeric values; it is modelled as `List[int]`
(Nagini bans `str`/array indexing, and the tested behaviour is about WHICH
values are covered, not floating-point precision -- see refinement.md /
mapping.md). The pure sequence theory `PSeq[int]` carries the specification.

One unchanged helper is axiomatized: a sub-selection over the input sequence
whose only guaranteed property is MEMBERSHIP -- every value it yields already
occurs among the input values, and it never yields more values than the input
has. It carries no guarantee about which values it keeps (in particular, no
guarantee that the largest value is among them). Its soundness is checked
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def subsel_len(verts: PSeq[int]) -> int:
    """Number of values a sub-selection over `verts` yields: between zero and
    the full count (a sub-selection never yields more values than the input)."""
    Ensures(0 <= Result() and Result() <= len(verts))


@Pure
@ContractOnly
def subsel_at(verts: PSeq[int], idx: int) -> int:
    """The `idx`-th value of a sub-selection over `verts`. Its ONLY guaranteed
    property (the weakest sound contract) is MEMBERSHIP: every yielded value
    already occurs among the input values -- the result equals `verts[j]` for
    some in-bounds `j`. It carries no promise about which values are kept; in
    particular, no promise that the largest input value is among them.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(0 <= idx and idx < subsel_len(verts))
    Ensures(Exists(int, lambda j: (0 <= j and j < len(verts)
                                   and Result() == verts[j])))
# axioms-end


# pure-start
@Pure
def seq_max(s: PSeq[int]) -> int:
    """Largest value over a non-empty sequence. Front-recursive so a single
    unfold is available per loop step (index-recursion does not auto-unfold in
    Nagini 1.2.0)."""
    Requires(len(s) >= 1)
    if len(s) == 1:
        return s[0]
    return _imax(s[0], seq_max(s.drop(1)))


@Pure
def _imax(a: int, b: int) -> int:
    return a if a >= b else b
# pure-end


def lemma_seq_max_dominates(s: PSeq[int]) -> None:
    """The front-recursive maximum dominates every element of the sequence."""
    # pre-conditions-start
    Requires(len(s) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                           seq_max(s) >= s[k]))))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    if len(s) > 1:
        lemma_seq_max_dominates(s.drop(1))
        t = s.drop(1)  # type: PSeq[int]
        Assert(seq_max(s) == _imax(s[0], seq_max(t)))
        Assert(seq_max(s) >= seq_max(t))
        Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(s),
                                              s[k] == t[k - 1]))))
    # impl-end


def lemma_seq_max_attained(s: PSeq[int]) -> None:
    """The front-recursive maximum is attained: it equals some element of the
    sequence (tightness -- the bound is one of the inputs, not larger)."""
    # pre-conditions-start
    Requires(len(s) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Exists(int, lambda j: (0 <= j and j < len(s)
                                   and seq_max(s) == s[j])))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    if len(s) == 1:
        Assert(seq_max(s) == s[0])
    else:
        t = s.drop(1)  # type: PSeq[int]
        lemma_seq_max_attained(t)
        Assert(seq_max(s) == _imax(s[0], seq_max(t)))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(t),
                                              t[k] == s[k + 1]))))
    # impl-end


def enclosing_upper_bound(verts: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(verts), 1 / 2))
    Requires(len(verts) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(verts), 1 / 2))
    # The result is an upper bound over the whole input: it is at least as large
    # as every element. (Enclosing direction.)
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                           Result() >= verts[k]))))
    # The bound is ATTAINED: it equals one of the input elements, not an
    # arbitrary larger number. (Tightness direction -- excludes any padded
    # over-approximation of the true bound.)
    Ensures(Exists(int, lambda j: (0 <= j and j < len(verts)
                                   and Result() == verts[j])))
    # post-conditions-end
    # impl-start
    lemma_seq_max_dominates(ToSeq(verts))
    best = verts[len(verts) - 1]
    i = len(verts) - 1
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(verts), 1 / 2))
        Invariant(0 <= i and i < len(verts))
        Invariant(best == seq_max(ToSeq(verts).drop(i)))
        # invariants-end
        Assert(ToSeq(verts).drop(i - 1)[0] == verts[i - 1])
        Assert(ToSeq(verts).drop(i - 1).drop(1) == ToSeq(verts).drop(i))
        if verts[i - 1] > best:
            best = verts[i - 1]
        i = i - 1
    Assert(i == 0)
    Assert(ToSeq(verts).drop(0) == ToSeq(verts))
    Assert(best == seq_max(ToSeq(verts)))
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          seq_max(ToSeq(verts)) >= ToSeq(verts)[k]))))
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(verts),
                                          ToSeq(verts)[k] == verts[k]))))
    return best
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY — matplotlib__matplotlib-24177 (nagini), G-EQ refinement fidelity (A-leg focus). VERDICT: SOUND.

tools run with SBU_BENCHMARK_DIR=benchmark-verified and SBU_PYTHON=python.

SPEC SHAPE: enclosing_upper_bound(verts) postconditions pin Result() to EXACTLY max(verts): (a) enclosing Forall k. Result()>=verts[k] AND (b) attained Exists j. Result()==verts[j]. Together these force any verifying impl to return the true per-axis maximum over ALL of verts. There is no slack for a wrong impl: undershooting the max fails (a); over-approximating (max+padding/constant) fails (b). Hence verify(model) => the gold full-gather behaviour => resolves. No candidate counterexample can exist, and none did.

BASELINES: positive_control.py (byte-identical model impl) -> nagini_verify.sh rc=0 (Verification successful, 18.1s). prepatch.py (bundle model_prepatch.py, folds over subsel_at membership-only subselection) -> `adversary weakness` rc=2 (does NOT verify): PREPATCH BUG REPRODUCED — fails exactly the enclosing Forall clause, which is the change G-DIFF senses.

ATTACKS (all copied model.py, edited ONLY the enclosing_upper_bound impl region; axioms/@Pure/Requires/Ensures byte-identical). Each confirmed SAME-spec (adversary same-spec rc=0) then run through `adversary weakness nagini matplotlib__matplotlib-24177 <f>`:
- atk_1.py (partial-domain: return verts[0]) -> weakness rc=2; verify error: Postcondition Forall(Result()>=verts[k]) might not hold.
- atk_2.py (partial-domain: return verts[len-1]) -> rc=2; Postcondition Forall enclosing fails.
- atk_3.py (control-flow-effect: flip comparison => computes MIN) -> rc=2; Postcondition Forall enclosing fails.
- atk_4.py (boundary/off-by-one: fold indices 0..len-2, skip LAST element) -> rc=2; Postcondition Forall enclosing fails.
- atk_5.py (ungrounded-oracle/padding: return seq_max(ToSeq(verts))+1) -> rc=2; verify error: Postcondition Exists(Result()==verts[j]) might not hold — the ATTAINED/tightness clause is load-bearing (dominates all but is not attained).
- atk_6.py (ungrounded constant: return 1000000000) -> rc=2; Postcondition Forall enclosing fails (and would fail attained too).
- atk_7.py (control-flow: stride-2 fold, inspects only every other index) -> rc=2; Postcondition Forall enclosing fails.

EXACT COMMANDS (per attack): `python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-24177 <f>` (all rc=0, SAME) and `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-24177 <f>` (all rc=2, NOT-A-COUNTEREXAMPLE: does not verify). Direct `bash scripts/nagini_verify.sh <f>` confirmed the failures are GENUINE postcondition/enclosing errors (not infra/parse/timeout): atk_1,2,3,4,6,7 fail the enclosing Forall; atk_5 fails the attained Exists. Verifications were run concurrently in batches of 3 (each Nagini check spawns JVM+Z3).

RESULT: 0 of 7 same-spec wrong impls verified => no CANDIDATE => no faithful refined patch needed materializing/run_resolve (patches map empty, correctly). >=5 distinct-family attacks run (partial-domain x2, control-flow-effect x2, boundary x1, ungrounded-oracle/padding x2) — none breaks the spec.

REFINEMENT.MD A-LEG AUDIT: legs classified R/A/I with no kind-3 (§C confirmed). Two A-legs:
- A3 (A-reference): deep seq_max fold + verified loop == real per-axis max over Path.iter_bezier(simplify=False) full gather; dominance lemma = enclosing, attained lemma = tightness. Correspondence validated out-of-band by axiom_check.py check_full_gather_encloses (max(full)>=every vertex, min<=every vertex) over 4 boundary + regression + 4000 fuzz outlines. HOLDS.
- B1 (A-consumed): subsel_len/subsel_at membership+count axioms == real Path.iter_bezier() default (simplify=None) appearance-preserving condensation; weakest sound contract (membership only, promises nothing about extremes — exactly why the prepatch can't discharge enclosing). Validated by axiom_check.py check_condensation_membership + regression witness (condensed y-max 0.25 < true 0.33). HOLDS.
Both A-legs bind to real matplotlib callees (path.py:420 iter_bezier / _base.py:2437 gather). The changed op (gather source: all vertices vs condensation) is modeled DEEPLY as A-reference, not hidden behind an axiom-about-the-changed-fn. Correspondence sound.

CONCLUSION: verify => correct holds for this bundle. The spec is tight (max pinned by enclosing+attained), refinement map is faithful with valid A-leg correspondence, prepatch bug reproduced, positive control verifies. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for matplotlib__matplotlib-24177 nagini.

MODELED FUNCTION: enclosing_upper_bound(verts: List[int]) over PSeq[int]. Requires non-empty. Two postconditions: (1) enclosing — Result() >= verts[k] for all k; (2) attained — Result() == verts[j] for some j. Both are exactly the mathematical max over the input coordinates.

REAL CALLEE (mapping.md): Axes._update_patch_limits gathering vertices via iter_bezier(simplify=False) and feeding them to update_datalim; the observable is the per-axis dataLim upper end. For a pure MOVETO/LINETO polyline, the gathered points ARE the path vertices, so the dataLim upper end is exactly max(gathered coordinates).

Why the spec is NOT too strong:
- Enclosing clause: max is trivially >= every element. Holds for the real dataLim (max of gathered data). Faithful.
- Attained clause: the real dataLim upper end is the max OF the gathered data (no padding — margins/nonsingular expansion are applied later in the autoscale path via handle_single_axis, NOT in _update_patch_limits/dataLim). So Result()==verts[j] for some j is exactly the real behavior; the tightness clause is calibrated to the dataLim boundary, not the margin-padded view limit, so it does not over-strengthen. Correctly excludes only a padded over-approximation, which the real callee never produces at the dataLim level.
- Carrier abstraction (List[int] over one axis; simplify=False gather = path vertices) is documented and G-AX-validated.

### Machine-checkable evidence
- same-spec (nagini) on model.py itself: exit 0 (SAME — shares the frozen spec).
- nagini_verify.sh model.py: Verification successful (17.25s), so both postconditions are provable of the modeled max.
- G-CONF (recorded meta.json + reviewed conformance_check.py): contract-stripped impl region compared against the REAL _update_patch_limits dataLim upper end on 100,156 inputs, 0 disagreements, exact integer-in-float64 equality; domain covers single elements, duplicates, extremes at every position (first/last/interior), negatives, large magnitude (±1e6), and long (>=128-vertex) scaled step outlines where full-vertex coverage is load-bearing. seed 24177.
- G-AX: full gather encloses every vertex and is attained; regression-outline witness confirms condensation drops the interior y-extreme (0.25 < 0.33) while full gather captures it — over 4 boundary + 4000 fuzz outlines, exit 0.

Searched for a diverging input where the modeled max disagrees with the real dataLim upper end over the Requires-satisfying domain (non-empty integer list). None exists: max is exactly the dataLim upper end for a pure polyline, structurally and per the 100k-input exact differential check. No spec-too-strong drift found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier or comment naming the patched symbol 'update_patch_limits', no bug/fix narration). Semantic review confirms no leakage beyond the public problem_statement.

Gold edit: lib/matplotlib/axes/_base.py:2437, 'p.iter_bezier()' -> 'p.iter_bezier(simplify=False)' (disable the appearance-preserving path condensation so the vertex gather visits every vertex, so the autoscaled extent encloses the whole outline).

Public problem_statement reveals ONLY the user symptom: histogram density axis not auto-scaled with histtype='step'. It names no repo symbol, no iter_bezier, no simplify, and no vertex-condensation mechanism. (The condensation/iter_bezier mechanism appears only in hints_text, which is NOT the leakage baseline.)

Spec view (model.py projection): names no patched symbol, no iter_bezier/simplify/Path, no _base.py, no file/module path. It abstracts the contract to a domain-neutral 'upper bound over a numeric sequence that is >= every element and is attained', plus an axiomatized 'sub-selection whose only guaranteed property is MEMBERSHIP -- no guarantee the largest value is kept'. That membership-only subset abstraction is the correct behavioral contract (its job is to describe correct behavior), not a disclosure of the concrete edit's identity or location; a solver cannot reconstruct 'iter_bezier(simplify=False)' at _base.py:2437 from any spec-view line that they couldn't already infer from the public statement. The only repo references are the instance id and pointers to sibling bundle files (refinement.md/mapping.md/axiom_check.py), which do not appear in the spec view's disclosure surface and do not spell out the edit.

No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
