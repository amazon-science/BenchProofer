# P2 adversarial audit — django__django-15128

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
@@ -33,7 +33,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
                                              below[k] < f), [[below[k]]])))
     Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                              above[j] >= f), [[above[j]]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(below), 1 / 4))
     Ensures(Acc(list_pred(above), 1 / 4))
     Ensures(Forall(int, lambda k: Forall(int, lambda j: (
@@ -91,7 +89,6 @@
                     below[k] != above[j])))))
     k = 0
     while k < len(below):
-        # invariants-start
         Invariant(Acc(list_pred(below), 1 / 4))
         Invariant(Acc(list_pred(above), 1 / 4))
         Invariant(0 <= k and k <= len(below))
@@ -104,8 +101,6 @@
         Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                 Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                         below[kk] != above[j])))))
-        Invariant(MustTerminate(len(below) - k + 1))
-        # invariants-end
         k = k + 1
 
 
@@ -124,7 +119,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] < floor_of(new_ns)),
                                      [[aliases[k]]])))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(aliases), 1 / 2))
@@ -162,8 +156,7 @@
     targets = []  # type: List[int]
     is_source = []  # type: List[int]
     pos = 0
-    while pos < len(aliases):
-        # invariants-start
+    while pos + 1 < len(aliases):
         Invariant(Acc(list_pred(aliases), 1 / 2))
         Invariant(Acc(list_pred(targets)))
         Invariant(Acc(list_pred(is_source)))
@@ -176,31 +169,19 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] < floor_of(new_ns)),
                                           [[aliases[k]]])))
-        # Each produced target so far is the fresh alias for its position...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] == fresh_alias(new_ns, j))))
-        # ...hence lives in the fresh namespace...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] >= floor_of(new_ns))))
-        # ...and the source flag records exactly "not the kept alias".
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                 (is_source[k] == 1) == (aliases[k] != excluded))))
-        Invariant(MustTerminate(len(aliases) - pos + 1))
-        # invariants-end
         t = fresh_alias(new_ns, pos)
         targets.append(t)
-        Assert(targets[pos] == t)
-        Assert(targets[pos] >= floor_of(new_ns))
         if aliases[pos] != excluded:
             is_source.append(1)
         else:
             is_source.append(0)
-        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
         pos = pos + 1
-    # Every source lives below the fresh floor and every target at or above it,
-    # so no source equals any target: the relabel map's keys and values are
-    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
-    Assert(pos == len(aliases) and len(targets) == len(aliases))
     disjoint_by_floor(aliases, targets, floor_of(new_ns))
     return targets, is_source
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
                                              below[k] < f), [[below[k]]])))
     Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                              above[j] >= f), [[above[j]]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(below), 1 / 4))
     Ensures(Acc(list_pred(above), 1 / 4))
     Ensures(Forall(int, lambda k: Forall(int, lambda j: (
@@ -91,7 +89,6 @@
                     below[k] != above[j])))))
     k = 0
     while k < len(below):
-        # invariants-start
         Invariant(Acc(list_pred(below), 1 / 4))
         Invariant(Acc(list_pred(above), 1 / 4))
         Invariant(0 <= k and k <= len(below))
@@ -104,8 +101,6 @@
         Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                 Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                         below[kk] != above[j])))))
-        Invariant(MustTerminate(len(below) - k + 1))
-        # invariants-end
         k = k + 1
 
 
@@ -124,7 +119,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] < floor_of(new_ns)),
                                      [[aliases[k]]])))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(aliases), 1 / 2))
@@ -163,7 +157,6 @@
     is_source = []  # type: List[int]
     pos = 0
     while pos < len(aliases):
-        # invariants-start
         Invariant(Acc(list_pred(aliases), 1 / 2))
         Invariant(Acc(list_pred(targets)))
         Invariant(Acc(list_pred(is_source)))
@@ -176,31 +169,22 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] < floor_of(new_ns)),
                                           [[aliases[k]]])))
-        # Each produced target so far is the fresh alias for its position...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] == fresh_alias(new_ns, j))))
-        # ...hence lives in the fresh namespace...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] >= floor_of(new_ns))))
-        # ...and the source flag records exactly "not the kept alias".
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                 (is_source[k] == 1) == (aliases[k] != excluded))))
-        Invariant(MustTerminate(len(aliases) - pos + 1))
-        # invariants-end
-        t = fresh_alias(new_ns, pos)
+        if pos + 1 < BASE():
+            t = fresh_alias(new_ns, pos + 1)
+        else:
+            t = fresh_alias(new_ns, pos)
         targets.append(t)
-        Assert(targets[pos] == t)
-        Assert(targets[pos] >= floor_of(new_ns))
         if aliases[pos] != excluded:
             is_source.append(1)
         else:
             is_source.append(0)
-        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
         pos = pos + 1
-    # Every source lives below the fresh floor and every target at or above it,
-    # so no source equals any target: the relabel map's keys and values are
-    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
-    Assert(pos == len(aliases) and len(targets) == len(aliases))
     disjoint_by_floor(aliases, targets, floor_of(new_ns))
     return targets, is_source
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
                                              below[k] < f), [[below[k]]])))
     Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                              above[j] >= f), [[above[j]]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(below), 1 / 4))
     Ensures(Acc(list_pred(above), 1 / 4))
     Ensures(Forall(int, lambda k: Forall(int, lambda j: (
@@ -91,7 +89,6 @@
                     below[k] != above[j])))))
     k = 0
     while k < len(below):
-        # invariants-start
         Invariant(Acc(list_pred(below), 1 / 4))
         Invariant(Acc(list_pred(above), 1 / 4))
         Invariant(0 <= k and k <= len(below))
@@ -104,8 +101,6 @@
         Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                 Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                         below[kk] != above[j])))))
-        Invariant(MustTerminate(len(below) - k + 1))
-        # invariants-end
         k = k + 1
 
 
@@ -124,7 +119,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] < floor_of(new_ns)),
                                      [[aliases[k]]])))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(aliases), 1 / 2))
@@ -163,7 +157,6 @@
     is_source = []  # type: List[int]
     pos = 0
     while pos < len(aliases):
-        # invariants-start
         Invariant(Acc(list_pred(aliases), 1 / 2))
         Invariant(Acc(list_pred(targets)))
         Invariant(Acc(list_pred(is_source)))
@@ -176,31 +169,19 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] < floor_of(new_ns)),
                                           [[aliases[k]]])))
-        # Each produced target so far is the fresh alias for its position...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] == fresh_alias(new_ns, j))))
-        # ...hence lives in the fresh namespace...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] >= floor_of(new_ns))))
-        # ...and the source flag records exactly "not the kept alias".
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                 (is_source[k] == 1) == (aliases[k] != excluded))))
-        Invariant(MustTerminate(len(aliases) - pos + 1))
-        # invariants-end
         t = fresh_alias(new_ns, pos)
         targets.append(t)
-        Assert(targets[pos] == t)
-        Assert(targets[pos] >= floor_of(new_ns))
-        if aliases[pos] != excluded:
+        if aliases[pos] == excluded:
             is_source.append(1)
         else:
             is_source.append(0)
-        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
         pos = pos + 1
-    # Every source lives below the fresh floor and every target at or above it,
-    # so no source equals any target: the relabel map's keys and values are
-    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
-    Assert(pos == len(aliases) and len(targets) == len(aliases))
     disjoint_by_floor(aliases, targets, floor_of(new_ns))
     return targets, is_source
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
                                              below[k] < f), [[below[k]]])))
     Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                              above[j] >= f), [[above[j]]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(below), 1 / 4))
     Ensures(Acc(list_pred(above), 1 / 4))
     Ensures(Forall(int, lambda k: Forall(int, lambda j: (
@@ -91,7 +89,6 @@
                     below[k] != above[j])))))
     k = 0
     while k < len(below):
-        # invariants-start
         Invariant(Acc(list_pred(below), 1 / 4))
         Invariant(Acc(list_pred(above), 1 / 4))
         Invariant(0 <= k and k <= len(below))
@@ -104,8 +101,6 @@
         Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                 Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                         below[kk] != above[j])))))
-        Invariant(MustTerminate(len(below) - k + 1))
-        # invariants-end
         k = k + 1
 
 
@@ -124,7 +119,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] < floor_of(new_ns)),
                                      [[aliases[k]]])))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(aliases), 1 / 2))
@@ -163,7 +157,6 @@
     is_source = []  # type: List[int]
     pos = 0
     while pos < len(aliases):
-        # invariants-start
         Invariant(Acc(list_pred(aliases), 1 / 2))
         Invariant(Acc(list_pred(targets)))
         Invariant(Acc(list_pred(is_source)))
@@ -176,31 +169,19 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] < floor_of(new_ns)),
                                           [[aliases[k]]])))
-        # Each produced target so far is the fresh alias for its position...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] == fresh_alias(new_ns, j))))
-        # ...hence lives in the fresh namespace...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] >= floor_of(new_ns))))
-        # ...and the source flag records exactly "not the kept alias".
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                 (is_source[k] == 1) == (aliases[k] != excluded))))
-        Invariant(MustTerminate(len(aliases) - pos + 1))
-        # invariants-end
-        t = fresh_alias(new_ns, pos)
+        t = floor_of(new_ns)
         targets.append(t)
-        Assert(targets[pos] == t)
-        Assert(targets[pos] >= floor_of(new_ns))
         if aliases[pos] != excluded:
             is_source.append(1)
         else:
             is_source.append(0)
-        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
         pos = pos + 1
-    # Every source lives below the fresh floor and every target at or above it,
-    # so no source equals any target: the relabel map's keys and values are
-    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
-    Assert(pos == len(aliases) and len(targets) == len(aliases))
     disjoint_by_floor(aliases, targets, floor_of(new_ns))
     return targets, is_source
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
                                              below[k] < f), [[below[k]]])))
     Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                              above[j] >= f), [[above[j]]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(below), 1 / 4))
     Ensures(Acc(list_pred(above), 1 / 4))
     Ensures(Forall(int, lambda k: Forall(int, lambda j: (
@@ -91,7 +89,6 @@
                     below[k] != above[j])))))
     k = 0
     while k < len(below):
-        # invariants-start
         Invariant(Acc(list_pred(below), 1 / 4))
         Invariant(Acc(list_pred(above), 1 / 4))
         Invariant(0 <= k and k <= len(below))
@@ -104,8 +101,6 @@
         Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                 Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                         below[kk] != above[j])))))
-        Invariant(MustTerminate(len(below) - k + 1))
-        # invariants-end
         k = k + 1
 
 
@@ -124,7 +119,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] < floor_of(new_ns)),
                                      [[aliases[k]]])))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(aliases), 1 / 2))
@@ -163,7 +157,6 @@
     is_source = []  # type: List[int]
     pos = 0
     while pos < len(aliases):
-        # invariants-start
         Invariant(Acc(list_pred(aliases), 1 / 2))
         Invariant(Acc(list_pred(targets)))
         Invariant(Acc(list_pred(is_source)))
@@ -176,31 +169,16 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] < floor_of(new_ns)),
                                           [[aliases[k]]])))
-        # Each produced target so far is the fresh alias for its position...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] == fresh_alias(new_ns, j))))
-        # ...hence lives in the fresh namespace...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] >= floor_of(new_ns))))
-        # ...and the source flag records exactly "not the kept alias".
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                 (is_source[k] == 1) == (aliases[k] != excluded))))
-        Invariant(MustTerminate(len(aliases) - pos + 1))
-        # invariants-end
         t = fresh_alias(new_ns, pos)
         targets.append(t)
-        Assert(targets[pos] == t)
-        Assert(targets[pos] >= floor_of(new_ns))
-        if aliases[pos] != excluded:
-            is_source.append(1)
-        else:
-            is_source.append(0)
-        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
+        is_source.append(1)
         pos = pos + 1
-    # Every source lives below the fresh floor and every target at or above it,
-    # so no source equals any target: the relabel map's keys and values are
-    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
-    Assert(pos == len(aliases) and len(targets) == len(aliases))
     disjoint_by_floor(aliases, targets, floor_of(new_ns))
     return targets, is_source
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
                                              below[k] < f), [[below[k]]])))
     Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                              above[j] >= f), [[above[j]]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(below), 1 / 4))
     Ensures(Acc(list_pred(above), 1 / 4))
     Ensures(Forall(int, lambda k: Forall(int, lambda j: (
@@ -91,7 +89,6 @@
                     below[k] != above[j])))))
     k = 0
     while k < len(below):
-        # invariants-start
         Invariant(Acc(list_pred(below), 1 / 4))
         Invariant(Acc(list_pred(above), 1 / 4))
         Invariant(0 <= k and k <= len(below))
@@ -104,8 +101,6 @@
         Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                 Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                         below[kk] != above[j])))))
-        Invariant(MustTerminate(len(below) - k + 1))
-        # invariants-end
         k = k + 1
 
 
@@ -124,7 +119,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] < floor_of(new_ns)),
                                      [[aliases[k]]])))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(aliases), 1 / 2))
@@ -163,7 +157,6 @@
     is_source = []  # type: List[int]
     pos = 0
     while pos < len(aliases):
-        # invariants-start
         Invariant(Acc(list_pred(aliases), 1 / 2))
         Invariant(Acc(list_pred(targets)))
         Invariant(Acc(list_pred(is_source)))
@@ -176,31 +169,19 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] < floor_of(new_ns)),
                                           [[aliases[k]]])))
-        # Each produced target so far is the fresh alias for its position...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] == fresh_alias(new_ns, j))))
-        # ...hence lives in the fresh namespace...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] >= floor_of(new_ns))))
-        # ...and the source flag records exactly "not the kept alias".
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                 (is_source[k] == 1) == (aliases[k] != excluded))))
-        Invariant(MustTerminate(len(aliases) - pos + 1))
-        # invariants-end
         t = fresh_alias(new_ns, pos)
         targets.append(t)
-        Assert(targets[pos] == t)
-        Assert(targets[pos] >= floor_of(new_ns))
         if aliases[pos] != excluded:
             is_source.append(1)
         else:
             is_source.append(0)
-        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
         pos = pos + 1
-    # Every source lives below the fresh floor and every target at or above it,
-    # so no source equals any target: the relabel map's keys and values are
-    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
-    Assert(pos == len(aliases) and len(targets) == len(aliases))
     disjoint_by_floor(aliases, targets, floor_of(new_ns))
-    return targets, is_source
+    return is_source, targets
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
                                              below[k] < f), [[below[k]]])))
     Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                              above[j] >= f), [[above[j]]])))
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(below), 1 / 4))
     Ensures(Acc(list_pred(above), 1 / 4))
     Ensures(Forall(int, lambda k: Forall(int, lambda j: (
@@ -91,7 +89,6 @@
                     below[k] != above[j])))))
     k = 0
     while k < len(below):
-        # invariants-start
         Invariant(Acc(list_pred(below), 1 / 4))
         Invariant(Acc(list_pred(above), 1 / 4))
         Invariant(0 <= k and k <= len(below))
@@ -104,8 +101,6 @@
         Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                 Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                         below[kk] != above[j])))))
-        Invariant(MustTerminate(len(below) - k + 1))
-        # invariants-end
         k = k + 1
 
 
@@ -124,7 +119,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] < floor_of(new_ns)),
                                      [[aliases[k]]])))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(aliases), 1 / 2))
@@ -163,7 +157,6 @@
     is_source = []  # type: List[int]
     pos = 0
     while pos < len(aliases):
-        # invariants-start
         Invariant(Acc(list_pred(aliases), 1 / 2))
         Invariant(Acc(list_pred(targets)))
         Invariant(Acc(list_pred(is_source)))
@@ -176,31 +169,23 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] < floor_of(new_ns)),
                                           [[aliases[k]]])))
-        # Each produced target so far is the fresh alias for its position...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] == fresh_alias(new_ns, j))))
-        # ...hence lives in the fresh namespace...
         Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                 targets[j] >= floor_of(new_ns))))
-        # ...and the source flag records exactly "not the kept alias".
         Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                 (is_source[k] == 1) == (aliases[k] != excluded))))
-        Invariant(MustTerminate(len(aliases) - pos + 1))
-        # invariants-end
-        t = fresh_alias(new_ns, pos)
+        idx = len(aliases) - 1 - pos
+        if 0 <= idx and idx < BASE():
+            t = fresh_alias(new_ns, idx)
+        else:
+            t = fresh_alias(new_ns, pos)
         targets.append(t)
-        Assert(targets[pos] == t)
-        Assert(targets[pos] >= floor_of(new_ns))
         if aliases[pos] != excluded:
             is_source.append(1)
         else:
             is_source.append(0)
-        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
         pos = pos + 1
-    # Every source lives below the fresh floor and every target at or above it,
-    # so no source equals any target: the relabel map's keys and values are
-    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
-    Assert(pos == len(aliases) and len(targets) == len(aliases))
     disjoint_by_floor(aliases, targets, floor_of(new_ns))
     return targets, is_source
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15128.

Behaviour under specification (an abstract behavioural contract):

  Given an ordered list of current aliases, a target namespace, and one
  designated alias to leave unmapped, the operation produces a relabel map
  (a partial function from current aliases to new aliases) with these
  properties:

    * the designated alias is NOT a key of the map (it is left unmapped);
    * every other current alias IS a key of the map -- equivalently, a current
      alias is a key if and only if it is not the designated one;
    * the value assigned to the alias at ordinal position ``pos`` is the fresh
      alias generated for that position, so distinct positions get distinct
      values (the map is injective);
    * the map's KEY set and VALUE set are DISJOINT (no current alias equals any
      assigned value).

  Disjointness of keys and values is the well-formedness condition the map must
  meet: it lets the map be applied so that each alias is rewritten exactly once.

Aliases are modelled as non-negative integers; a namespace n occupies the
integer region at and above ``n * BASE``, and the current aliases are required
to live strictly below the target namespace's floor (mapping.md §2). The fresh
value for ordinal position ``pos`` is ``new_ns * BASE + pos``. The construction
returns, per ordinal position, the fresh value for that position and a flag
marking whether that position is a key (1) or the unmapped alias (0). The two
returned lists are positionally aligned with the input alias list.

The whole behaviour is modelled deeply (the construction is spelled out in the
impl region); there is no axiomatised callee. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the relabel construction is the behaviour under specification and
# is spelled out deeply in the impl region. There is no unchanged opaque callee
# to axiomatise.
# axioms-end


# pure-start
@Pure
def BASE() -> int:
    """Per-namespace alias capacity: a namespace n occupies the integer region
    [n*BASE, (n+1)*BASE), so distinct namespaces never collide."""
    return 1000


@Pure
def floor_of(ns: int) -> int:
    """The lowest integer alias belonging to namespace ``ns``."""
    Requires(ns >= 0)
    Ensures(Result() == ns * BASE())
    Ensures(Result() >= 0)
    return ns * BASE()


@Pure
def fresh_alias(new_ns: int, pos: int) -> int:
    """The fresh alias generated for the source at ordinal position ``pos`` in
    the new namespace ``new_ns``."""
    Requires(new_ns >= 0)
    Requires(0 <= pos and pos < BASE())
    # A fresh alias lives in new_ns: it sits at or above that namespace's floor.
    Ensures(Result() == new_ns * BASE() + pos)
    Ensures(Result() >= floor_of(new_ns))
    return new_ns * BASE() + pos
# pure-end


def disjoint_by_floor(below: List[int], above: List[int], f: int) -> None:
    """Lemma: if every element of `below` is < f and every element of `above`
    is >= f, then no element of `below` equals any element of `above`. Pure
    arithmetic; carries the disjointness of the source and target alias sets."""
    Requires(Acc(list_pred(below), 1 / 4))
    Requires(Acc(list_pred(above), 1 / 4))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(below),
                                             below[k] < f), [[below[k]]])))
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                             above[j] >= f), [[above[j]]])))
    Ensures(Acc(list_pred(below), 1 / 4))
    Ensures(Acc(list_pred(above), 1 / 4))
    Ensures(Forall(int, lambda k: Forall(int, lambda j: (
            Implies(0 <= k and k < len(below) and 0 <= j and j < len(above),
                    below[k] != above[j])))))
    k = 0
    while k < len(below):
        Invariant(Acc(list_pred(below), 1 / 4))
        Invariant(Acc(list_pred(above), 1 / 4))
        Invariant(0 <= k and k <= len(below))
        Invariant(Forall(int, lambda kk: (Implies(0 <= kk and kk < len(below),
                                                   below[kk] < f), [[below[kk]]])))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                                  above[j] >= f), [[above[j]]])))
        # For every source already processed, it is below f, hence below every
        # target (each >= f), so it differs from each.
        Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                        below[kk] != above[j])))))
        k = k + 1


def build_relabel_map(aliases: List[int], new_ns: int,
                      excluded: int) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # `aliases` is the ordered list of current aliases (the map's potential
    # keys), each a well-formed encoding; read-only.
    Requires(Acc(list_pred(aliases), 1 / 2))
    Requires(new_ns >= 0)
    # The current aliases each fit one ordinal slot, and are well-formed.
    Requires(len(aliases) <= BASE())
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] >= 0), [[aliases[k]]])))
    # Every current alias lives strictly below the target namespace's floor.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                            aliases[k] < floor_of(new_ns)),
                                     [[aliases[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(aliases), 1 / 2))
    # Two positionally-aligned outputs: `targets[pos]` is the value assigned to
    # the alias at `pos`, and `is_source[pos]` is 1 iff that position is a key
    # of the map (0 iff it is the designated unmapped alias).
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(len(Result()[0]) == len(aliases))
    Ensures(len(Result()[1]) == len(aliases))
    # A current alias is a key IFF it is not the designated alias: the
    # designated alias is left unmapped, every other current alias is a key.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
            (Result()[1][k] == 1) == (aliases[k] != excluded)),
            [[Result()[1][k]]])))
    # The value at ordinal position `j` is the fresh value generated for that
    # position. Distinct positions therefore receive distinct values, so the
    # map is injective (no two current aliases collapse onto one value).
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(aliases) and j < BASE(),
            Result()[0][j] == fresh_alias(new_ns, j)),
            [[Result()[0][j]]])))
    # Every produced value lives in the target namespace (at or above its
    # floor), while every current alias lives strictly below it.
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(aliases),
            Result()[0][j] >= floor_of(new_ns)),
            [[Result()[0][j]]])))
    # Hence the map's KEY set and VALUE set are DISJOINT: no current alias
    # equals any produced value, so applying the map rewrites each alias exactly
    # once (the map's well-formedness condition).
    Ensures(Forall(int, lambda k: Forall(int, lambda j: (
            Implies(0 <= k and k < len(aliases) and 0 <= j and j < len(Result()[0]),
                    aliases[k] != Result()[0][j])))))
    # post-conditions-end
    # impl-start
    targets = []  # type: List[int]
    is_source = []  # type: List[int]
    pos = 0
    while pos < len(aliases):
        Invariant(Acc(list_pred(aliases), 1 / 2))
        Invariant(Acc(list_pred(targets)))
        Invariant(Acc(list_pred(is_source)))
        Invariant(0 <= pos and pos <= len(aliases))
        Invariant(len(aliases) <= BASE())
        Invariant(len(targets) == pos)
        Invariant(len(is_source) == pos)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] >= 0), [[aliases[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                 aliases[k] < floor_of(new_ns)),
                                          [[aliases[k]]])))
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                targets[j] == fresh_alias(new_ns, j))))
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                targets[j] >= floor_of(new_ns))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                (is_source[k] == 1) == (aliases[k] != excluded))))
        t = fresh_alias(new_ns, pos)
        targets.append(t)
        Assert(targets[pos] == t)
        Assert(targets[pos] >= floor_of(new_ns))
        if aliases[pos] != excluded:
            is_source.append(1)
        else:
            is_source.append(0)
        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
        pos = pos + 1
    Assert(pos == len(aliases) and len(targets) == len(aliases))
    disjoint_by_floor(aliases, targets, floor_of(new_ns))
    return targets, is_source
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of nagini bundle django__django-15128 (build_relabel_map). The spec pins BOTH returned lists elementwise, leaving no behavioral slack for a verifying wrong impl: A4b Result()[0][j] == fresh_alias(new_ns,j) (exact per-ordinal value => injective, forbids collapse), the biconditional (Result()[1][k]==1)==(aliases[k]!=excluded), plus len==len(aliases) on both, floor Result()[0][j]>=floor_of(new_ns), and full key/value disjointness Forall k,j aliases[k]!=Result()[0][j].

PROTOCOL (all; project root; python python -m swebench_unified.adversary ...). All 8 files confirmed same-spec (adversary same-spec, exit 0 each — impl-region-only edits, axioms/@Pure/Requires/Ensures/lemma byte-identical).

### WEAKNESS RESULTS (adversary weakness nagini django__django-15128 <file>, run concurrently <=3/batch):
- pos_control.py (gold impl): CANDIDATE — shares spec AND VERIFIES (35.5s). Positive control OK.
- atk_1.py partial-domain (loop stops one short, len shorter): exit 2, 'does not verify (verification failed)' — GENUINE rejection.
- atk_2.py boundary/off-by-one (targets[pos]=fresh_alias(new_ns,pos+1)): exit 2, genuine verification failed (violates A4b).
- atk_3.py control-flow-effect (inverted guard: is_source=1 iff aliases[pos]==excluded): exit 2, genuine verification failed (violates biconditional).
- atk_4.py ungrounded-oracle echo / non-injective collapse (all targets=floor_of(new_ns); disjoint+floor hold but collapses positions): exit 2, genuine verification failed (violates A4b per-ordinal pin) — this is exactly the injectivity attack refinement.md D calls load-bearing, and the spec catches it.
- atk_5.py prepatch echo (is_source.append(1) unconditionally = the pre-patch bump_prefix behavior): exit 2, genuine verification failed (violates biconditional when excluded present) — reproduces the prepatch discriminator.
- atk_6.py list-swap (return is_source, targets): exit 2, genuine verification failed.
- atk_7.py reversed-ordinal value (targets[pos]=fresh_alias(new_ns,len-1-pos); injective+disjoint+floor all hold but A4b per-ordinal fails): exit 2, genuine verification failed.
Every attack rejection was verifier 'verification failed', NOT a timeout (grep-confirmed) — the spec actively rejected each.

NO CANDIDATE among the 7 wrong impls => there is no verifying wrong impl, hence no faithful refined patch to materialize/run through run_resolve. verify does NOT admit an incorrect impl here.

PREPATCH: model_prepatch.py directly verified via scripts/nagini_verify.sh -> exit 124 (Z3 300s non-convergence, 'not a normal verification failure'); adversary weakness also NOT-A-COUNTEREXAMPLE. It does not verify. The prepatch behavior is additionally, cleanly reproduced as a GENUINE 'verification failed' by atk_5 (semantically identical: unconditional is_source=1), so prepatch_reproduced=true is well-grounded via the deterministic route.

G-AX / A-LEG AUDIT: axiom_check.py exit 0 — 'validated == real relabel-map construction (source-flag biconditional + key/value disjointness + per-ordinal value/injectivity) on 20006 boundary + fuzz inputs; pre-patch discriminator confirmed'. Bundle has EMPTY axioms region, ZERO A-consumed rows; the whole build_relabel_map construction is a deep model validated as an A-reference by G-AX. refinement.md legs A1-A7 are all R or R+I; §C confirms no kind-3 (unexpressible-changed-op) steps; the discriminating delta (exclude filter, A5/A6) is modeled deeply, not hidden behind an axiom. The A-reference correspondence (model deep-impl == gold dict-comprehension {alias:'%s%d'%(prefix,pos) for pos,alias in enumerate(alias_map) if alias not in exclude}) is machine-validated by axiom_check.py. Correspondence holds.

VERDICT: SOUND. >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle/non-injective, prepatch-echo, list-swap, reversed-ordinal) all fail to verify; positive control verifies; prepatch does not verify; G-AX A-reference passes; refinement.md has no kind-3 legs and its A-reference correspondence is validated. verify => correct is not falsified.

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
"""Twin-artifact model for django__django-15128.

Behaviour under specification (an abstract behavioural contract):

  Given an ordered list of current aliases, a target namespace, and one
  designated alias to leave unmapped, the operation produces a relabel map
  (a partial function from current aliases to new aliases) with these
  properties:

    * the designated alias is NOT a key of the map (it is left unmapped);
    * every other current alias IS a key of the map -- equivalently, a current
      alias is a key if and only if it is not the designated one;
    * the value assigned to the alias at ordinal position ``pos`` is the fresh
      alias generated for that position, so distinct positions get distinct
      values (the map is injective);
    * the map's KEY set and VALUE set are DISJOINT (no current alias equals any
      assigned value).

  Disjointness of keys and values is the well-formedness condition the map must
  meet: it lets the map be applied so that each alias is rewritten exactly once.

Aliases are modelled as non-negative integers; a namespace n occupies the
integer region at and above ``n * BASE``, and the current aliases are required
to live strictly below the target namespace's floor (mapping.md §2). The fresh
value for ordinal position ``pos`` is ``new_ns * BASE + pos``. The construction
returns, per ordinal position, the fresh value for that position and a flag
marking whether that position is a key (1) or the unmapped alias (0). The two
returned lists are positionally aligned with the input alias list.

The whole behaviour is modelled deeply (the construction is spelled out in the
impl region); there is no axiomatised callee. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the relabel construction is the behaviour under specification and
# is spelled out deeply in the impl region. There is no unchanged opaque callee
# to axiomatise.
# axioms-end


# pure-start
@Pure
def BASE() -> int:
    """Per-namespace alias capacity: a namespace n occupies the integer region
    [n*BASE, (n+1)*BASE), so distinct namespaces never collide."""
    return 1000


@Pure
def floor_of(ns: int) -> int:
    """The lowest integer alias belonging to namespace ``ns``."""
    Requires(ns >= 0)
    Ensures(Result() == ns * BASE())
    Ensures(Result() >= 0)
    return ns * BASE()


@Pure
def fresh_alias(new_ns: int, pos: int) -> int:
    """The fresh alias generated for the source at ordinal position ``pos`` in
    the new namespace ``new_ns``."""
    Requires(new_ns >= 0)
    Requires(0 <= pos and pos < BASE())
    # A fresh alias lives in new_ns: it sits at or above that namespace's floor.
    Ensures(Result() == new_ns * BASE() + pos)
    Ensures(Result() >= floor_of(new_ns))
    return new_ns * BASE() + pos
# pure-end


def disjoint_by_floor(below: List[int], above: List[int], f: int) -> None:
    """Lemma: if every element of `below` is < f and every element of `above`
    is >= f, then no element of `below` equals any element of `above`. Pure
    arithmetic; carries the disjointness of the source and target alias sets."""
    Requires(Acc(list_pred(below), 1 / 4))
    Requires(Acc(list_pred(above), 1 / 4))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(below),
                                             below[k] < f), [[below[k]]])))
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                             above[j] >= f), [[above[j]]])))
    Ensures(Acc(list_pred(below), 1 / 4))
    Ensures(Acc(list_pred(above), 1 / 4))
    Ensures(Forall(int, lambda k: Forall(int, lambda j: (
            Implies(0 <= k and k < len(below) and 0 <= j and j < len(above),
                    below[k] != above[j])))))
    k = 0
    while k < len(below):
        Invariant(Acc(list_pred(below), 1 / 4))
        Invariant(Acc(list_pred(above), 1 / 4))
        Invariant(0 <= k and k <= len(below))
        Invariant(Forall(int, lambda kk: (Implies(0 <= kk and kk < len(below),
                                                   below[kk] < f), [[below[kk]]])))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                                  above[j] >= f), [[above[j]]])))
        # For every source already processed, it is below f, hence below every
        # target (each >= f), so it differs from each.
        Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                        below[kk] != above[j])))))
        k = k + 1


def build_relabel_map(aliases: List[int], new_ns: int,
                      excluded: int) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # `aliases` is the ordered list of current aliases (the map's potential
    # keys), each a well-formed encoding; read-only.
    Requires(Acc(list_pred(aliases), 1 / 2))
    Requires(new_ns >= 0)
    # The current aliases each fit one ordinal slot, and are well-formed.
    Requires(len(aliases) <= BASE())
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] >= 0), [[aliases[k]]])))
    # Every current alias lives strictly below the target namespace's floor.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                            aliases[k] < floor_of(new_ns)),
                                     [[aliases[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(aliases), 1 / 2))
    # Two positionally-aligned outputs: `targets[pos]` is the value assigned to
    # the alias at `pos`, and `is_source[pos]` is 1 iff that position is a key
    # of the map (0 iff it is the designated unmapped alias).
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(len(Result()[0]) == len(aliases))
    Ensures(len(Result()[1]) == len(aliases))
    # A current alias is a key IFF it is not the designated alias: the
    # designated alias is left unmapped, every other current alias is a key.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
            (Result()[1][k] == 1) == (aliases[k] != excluded)),
            [[Result()[1][k]]])))
    # The value at ordinal position `j` is the fresh value generated for that
    # position. Distinct positions therefore receive distinct values, so the
    # map is injective (no two current aliases collapse onto one value).
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(aliases) and j < BASE(),
            Result()[0][j] == fresh_alias(new_ns, j)),
            [[Result()[0][j]]])))
    # Every produced value lives in the target namespace (at or above its
    # floor), while every current alias lives strictly below it.
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(aliases),
            Result()[0][j] >= floor_of(new_ns)),
            [[Result()[0][j]]])))
    # Hence the map's KEY set and VALUE set are DISJOINT: no current alias
    # equals any produced value, so applying the map rewrites each alias exactly
    # once (the map's well-formedness condition).
    Ensures(Forall(int, lambda k: Forall(int, lambda j: (
            Implies(0 <= k and k < len(aliases) and 0 <= j and j < len(Result()[0]),
                    aliases[k] != Result()[0][j])))))
    # post-conditions-end
    # impl-start
    targets = []  # type: List[int]
    is_source = []  # type: List[int]
    pos = 0
    while pos < len(aliases):
        Invariant(Acc(list_pred(aliases), 1 / 2))
        Invariant(Acc(list_pred(targets)))
        Invariant(Acc(list_pred(is_source)))
        Invariant(0 <= pos and pos <= len(aliases))
        Invariant(len(aliases) <= BASE())
        Invariant(len(targets) == pos)
        Invariant(len(is_source) == pos)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] >= 0), [[aliases[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                 aliases[k] < floor_of(new_ns)),
                                          [[aliases[k]]])))
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                targets[j] == fresh_alias(new_ns, j))))
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                targets[j] >= floor_of(new_ns))))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                (is_source[k] == 1) == (aliases[k] != excluded))))
        t = fresh_alias(new_ns, pos)
        targets.append(t)
        Assert(targets[pos] == t)
        Assert(targets[pos] >= floor_of(new_ns))
        if aliases[pos] != excluded:
            is_source.append(1)
        else:
            is_source.append(0)
        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
        pos = pos + 1
    Assert(pos == len(aliases) and len(targets) == len(aliases))
    disjoint_by_floor(aliases, targets, floor_of(new_ns))
    return targets, is_source
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of nagini bundle django__django-15128 (build_relabel_map). The spec pins BOTH returned lists elementwise, leaving no behavioral slack for a verifying wrong impl: A4b Result()[0][j] == fresh_alias(new_ns,j) (exact per-ordinal value => injective, forbids collapse), the biconditional (Result()[1][k]==1)==(aliases[k]!=excluded), plus len==len(aliases) on both, floor Result()[0][j]>=floor_of(new_ns), and full key/value disjointness Forall k,j aliases[k]!=Result()[0][j].

PROTOCOL (all; project root; python python -m swebench_unified.adversary ...). All 8 files confirmed same-spec (adversary same-spec, exit 0 each — impl-region-only edits, axioms/@Pure/Requires/Ensures/lemma byte-identical).

### WEAKNESS RESULTS (adversary weakness nagini django__django-15128 <file>, run concurrently <=3/batch):
- pos_control.py (gold impl): CANDIDATE — shares spec AND VERIFIES (35.5s). Positive control OK.
- atk_1.py partial-domain (loop stops one short, len shorter): exit 2, 'does not verify (verification failed)' — GENUINE rejection.
- atk_2.py boundary/off-by-one (targets[pos]=fresh_alias(new_ns,pos+1)): exit 2, genuine verification failed (violates A4b).
- atk_3.py control-flow-effect (inverted guard: is_source=1 iff aliases[pos]==excluded): exit 2, genuine verification failed (violates biconditional).
- atk_4.py ungrounded-oracle echo / non-injective collapse (all targets=floor_of(new_ns); disjoint+floor hold but collapses positions): exit 2, genuine verification failed (violates A4b per-ordinal pin) — this is exactly the injectivity attack refinement.md D calls load-bearing, and the spec catches it.
- atk_5.py prepatch echo (is_source.append(1) unconditionally = the pre-patch bump_prefix behavior): exit 2, genuine verification failed (violates biconditional when excluded present) — reproduces the prepatch discriminator.
- atk_6.py list-swap (return is_source, targets): exit 2, genuine verification failed.
- atk_7.py reversed-ordinal value (targets[pos]=fresh_alias(new_ns,len-1-pos); injective+disjoint+floor all hold but A4b per-ordinal fails): exit 2, genuine verification failed.
Every attack rejection was verifier 'verification failed', NOT a timeout (grep-confirmed) — the spec actively rejected each.

NO CANDIDATE among the 7 wrong impls => there is no verifying wrong impl, hence no faithful refined patch to materialize/run through run_resolve. verify does NOT admit an incorrect impl here.

PREPATCH: model_prepatch.py directly verified via scripts/nagini_verify.sh -> exit 124 (Z3 300s non-convergence, 'not a normal verification failure'); adversary weakness also NOT-A-COUNTEREXAMPLE. It does not verify. The prepatch behavior is additionally, cleanly reproduced as a GENUINE 'verification failed' by atk_5 (semantically identical: unconditional is_source=1), so prepatch_reproduced=true is well-grounded via the deterministic route.

G-AX / A-LEG AUDIT: axiom_check.py exit 0 — 'validated == real relabel-map construction (source-flag biconditional + key/value disjointness + per-ordinal value/injectivity) on 20006 boundary + fuzz inputs; pre-patch discriminator confirmed'. Bundle has EMPTY axioms region, ZERO A-consumed rows; the whole build_relabel_map construction is a deep model validated as an A-reference by G-AX. refinement.md legs A1-A7 are all R or R+I; §C confirms no kind-3 (unexpressible-changed-op) steps; the discriminating delta (exclude filter, A5/A6) is modeled deeply, not hidden behind an axiom. The A-reference correspondence (model deep-impl == gold dict-comprehension {alias:'%s%d'%(prefix,pos) for pos,alias in enumerate(alias_map) if alias not in exclude}) is machine-validated by axiom_check.py. Correspondence holds.

VERDICT: SOUND. >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle/non-injective, prepatch-echo, list-swap, reversed-ordinal) all fail to verify; positive control verifies; prepatch does not verify; G-AX A-reference passes; refinement.md has no kind-3 legs and its A-reference correspondence is validated. verify => correct is not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) audit for django__django-15128 nagini bundle. The modeled function build_relabel_map deeply models the alias relabel-map construction in Query.bump_prefix (django/db/models/sql/query.py, post-patch): the dict-comprehension {alias: '%s%d'%(prefix,pos) for pos,alias in enumerate(alias_map) if alias not in exclude}. There is no consumed axiom; the whole construction is spelled out in the impl region and validated == real code out-of-band.

Checks run (all in /tmp against the patched worktree at base_commit cb383753):
1. Shipped conformance_check.py (contract-stripped impl vs real patched bump_prefix via a CapturingQuery that records the change_map and delegates to the real change_aliases so the real isdisjoint assertion still runs): 110,012 inputs (12 boundary + 110,000 fuzz, seed 151280) -> 0 disagreements on per-position source flags, per-position target encodings, and the whole induced map.
2. Independent differential I wrote: 3,008 inputs including the excluded alias placed at EVERY position of a 6-alias list (verifying enumerate does not compact positions), excluded absent, excluded None, and lists up to 40 aliases -> 0 divergences.
3. Nagini verification of model.py: 'Verification successful' (33s), so the spec is real, not vacuous.

The spec is not too strong: the per-ordinal pin targets[j]==fresh_alias(new_ns,j) mirrors the real comprehension's '%s%d'%(prefix,pos) keyed on the enumerate ordinal (injective by construction); the source-flag biconditional (is_source[k]==1) == (aliases[k]!=excluded) mirrors 'if alias not in exclude' (single-element set); key/value disjointness mirrors the change_aliases isdisjoint assertion, guaranteed by the precondition aliases[k] < floor_of(new_ns) which mirrors the real fresh-prefix-differs guarantee. Type refinement (str alias <-> int encoding, ordered alias_map <-> List[int]) is sound and its image is respected by the precondition domain. No input found where the modeled function disagrees with the real callee within the declared preconditions.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes with zero hard failures (reproduced independently; meta G-LEAK status=pass, no relaxed_leakage flag / no RELAXED_LEAKAGE.md). Semantic review of the consumer spec view (docstring + BASE/floor_of/fresh_alias pure defs + disjoint_by_floor lemma + build_relabel_map signature/contracts; impl region elided) confirms no leak of the gold edit beyond the public problem_statement:

- No diff markers, no patched file path (django/db/models/sql/query.py absent), no patched module path.
- Gold-patch changed symbols are bump_prefix, change_aliases, combine, prefix_gen. bump_prefix and prefix_gen are ABSENT from the spec view; change_aliases and combine are already public in the problem_statement. No spec-view identifier or comment embeds/names any patched repo symbol.
- No gold-patch line reproduced: 'if alias not in exclude', "'%s%d' % (self.alias_prefix, pos)", 'set(change_map).isdisjoint(change_map.values())', 'exclude=None', 'exclude={initial_alias}' are all absent (verified lexically). Hints-only mechanism terms (bump_prefix, alias_prefix, initial_alias, get_initial, isdisjoint, change_map) do not appear.
- No bug/fix/regression narration in any comment or docstring.

The key/value-disjointness contract the spec encodes is ALREADY public: the problem_statement explicitly states the AssertionError arises because 'change_map's keys intersect with change_map's values' and asks to 'prevent intersection between change_map's keys and values'. The spec expresses this behaviourally over an abstract integer-namespace model. The only mechanism-shaped element ('one designated alias to leave unmapped' / excluded param) is stated as an abstract behavioural property (a partial function leaving one alias unmapped), never as the gold's edit (an exclude parameter added to bump_prefix keyed on get_initial_alias in combine) — those specifics live only in hints_text and are correctly not echoed. The token 'exclude'/'excluded' is a generic parameter name/English word, not a patched def/class symbol. Spec describes what must hold, not the edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
