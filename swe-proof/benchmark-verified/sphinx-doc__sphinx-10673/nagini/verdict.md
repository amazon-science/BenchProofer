# P2 adversarial audit — sphinx-doc__sphinx-10673

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_genonly.py`, `atk_4_empty.py`, `atk_5_negated.py`, `atk_6_offbyone.py`, `atk_9_reversed.py`, `atk_10_spin.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_3_retainall.py`, `atk_8_nonterm.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -89,7 +87,6 @@
     result = []  # type: List[int]
     i = len(entries)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(Acc(list_pred(generated), 1 / 2))
@@ -97,45 +94,9 @@
         Invariant(0 <= i and i <= len(entries))
         Invariant(ToSeq(result) ==
                   kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
         x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
-        if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
+        if mem(x, ToSeq(found)):
             result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
         i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_2_genonly.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -89,7 +87,6 @@
     result = []  # type: List[int]
     i = len(entries)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(Acc(list_pred(generated), 1 / 2))
@@ -97,45 +94,9 @@
         Invariant(0 <= i and i <= len(entries))
         Invariant(ToSeq(result) ==
                   kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
         x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
-        if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
+        if mem(x, ToSeq(generated)):
             result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
         i = i - 1
     return result
     # impl-end
```

Attack 3 — `atk_3_retainall.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -86,56 +84,5 @@
             kept(ToSeq(entries), ToSeq(found), ToSeq(generated)))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = len(entries)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(entries), 1 / 2))
-        Invariant(Acc(list_pred(found), 1 / 2))
-        Invariant(Acc(list_pred(generated), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(entries))
-        Invariant(ToSeq(result) ==
-                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
-        x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
-        if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
-            result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
-        i = i - 1
-    return result
+    return list(entries)
     # impl-end
```

Attack 4 — `atk_4_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -87,55 +85,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(entries)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(entries), 1 / 2))
-        Invariant(Acc(list_pred(found), 1 / 2))
-        Invariant(Acc(list_pred(generated), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(entries))
-        Invariant(ToSeq(result) ==
-                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
-        x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
-        if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
-            result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
-        i = i - 1
     return result
     # impl-end
```

Attack 5 — `atk_5_negated.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -89,7 +87,6 @@
     result = []  # type: List[int]
     i = len(entries)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(Acc(list_pred(generated), 1 / 2))
@@ -97,45 +94,9 @@
         Invariant(0 <= i and i <= len(entries))
         Invariant(ToSeq(result) ==
                   kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
         x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
-        if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
+        if not known(x, ToSeq(found), ToSeq(generated)):
             result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
         i = i - 1
     return result
     # impl-end
```

Attack 6 — `atk_6_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -87,9 +85,8 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(entries)
+    i = len(entries) - 1
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(Acc(list_pred(generated), 1 / 2))
@@ -97,45 +94,9 @@
         Invariant(0 <= i and i <= len(entries))
         Invariant(ToSeq(result) ==
                   kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
         x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
         if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
             result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
         i = i - 1
     return result
     # impl-end
```

Attack 7 — `atk_9_reversed.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -87,55 +85,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(entries)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(entries):
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(Acc(list_pred(generated), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(entries))
-        Invariant(ToSeq(result) ==
-                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
-        x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
+        x = entries[i]
         if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
             result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
-        i = i - 1
+        i = i + 1
     return result
     # impl-end
```

Attack 8 — `atk_8_nonterm.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -87,55 +85,10 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(entries)
-    while i > 0:
-        # invariants-start
+    while True:
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(Acc(list_pred(generated), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(entries))
-        Invariant(ToSeq(result) ==
-                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
-        x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
-        if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
-            result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
-        i = i - 1
     return result
     # impl-end
```

Attack 9 — `atk_10_spin.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(entries), 1 / 2))
     Requires(Acc(list_pred(found), 1 / 2))
     Requires(Acc(list_pred(generated), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(entries), 1 / 2))
@@ -89,53 +87,11 @@
     result = []  # type: List[int]
     i = len(entries)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(entries), 1 / 2))
         Invariant(Acc(list_pred(found), 1 / 2))
         Invariant(Acc(list_pred(generated), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(entries))
-        Invariant(ToSeq(result) ==
-                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # Read the head target name freshly (its list<->sequence linkage is what
-        # lets the singleton-sequence steps below discharge), then classify it
-        # directly against the two families with the pure membership theory —
-        # the very predicate the kept-filter branches on for this same name.
-        x = entries[i - 1]
-        Assert(ToSeq(entries).drop(i - 1)[0] == x)
-        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
-        # cons-decomposition of the non-empty sequence entries.drop(i-1):
-        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
-        Assert(ToSeq(entries).drop(i - 1) ==
-               PSeq(ToSeq(entries).drop(i - 1)[0]) +
-               ToSeq(entries).drop(i - 1).drop(1))
-        cons = PSeq(x) + ToSeq(entries).drop(i)
-        Assert(cons[0] == x)
-        Assert(cons.drop(1) == ToSeq(entries).drop(i))
-        Assert(ToSeq(entries).drop(i - 1) == cons)
-        if known(x, ToSeq(found), ToSeq(generated)):
-            # head is known: kept unfolds to PSeq(x) + kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   PSeq(x) + kept(ToSeq(entries).drop(i),
-                                  ToSeq(found), ToSeq(generated)))
-            old_seq = ToSeq(result)
-            result = [x] + result
-            Assert(ToSeq(result) == PSeq(x) + old_seq)
-        else:
-            # head is unknown: kept unfolds to just kept(tail)
-            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
-                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
-            Assert(kept(ToSeq(entries).drop(i - 1),
-                        ToSeq(found), ToSeq(generated)) ==
-                   kept(ToSeq(entries).drop(i),
-                        ToSeq(found), ToSeq(generated)))
-        Assert(ToSeq(result) ==
-               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
-        i = i - 1
+        Invariant(i == len(entries))
+        result = [entries[i - 1]] + result
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10673.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A document-tree directive lists, in order, a sequence of target document
  names. Each target is classified against the set of names the project knows
  about. The project knows two disjoint families of names:

    * the names of the ordinary source documents that were discovered, and
    * the names of the auto-built reference pages (a general index, a module
      index and a full-text search page) that the standard domain always
      provides even though no source file with that name exists.

  A listed target is RETAINED (kept in the resulting ordered entry list) when
  its name belongs to EITHER family; a target whose name belongs to neither is
  rejected (it names no document at all). The auto-built reference pages must be
  retainable exactly like ordinary documents: a target naming one of them is
  kept even though it is absent from the discovered-source family.

Names are modelled as integer identifiers (each distinct document name is a
distinct int); the two families and the listed targets are `List[int]`, and the
specification is carried by the pure sequence theory `PSeq[int]`. Membership and
the order-preserving retention filter are spelled out deeply as front-recursive
folds (a single unfold per loop step), so no membership oracle is consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the classification is modelled deeply over PSeq[int]; there is no
#  consumed @ContractOnly callee.)
# axioms-end


# pure-start
@Pure
def mem(x: int, s: PSeq[int]) -> bool:
    """Whether `x` occurs in `s`. Front-recursive so a single unfold is
    available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or mem(x, s.drop(1))


@Pure
def known(x: int, found: PSeq[int], gen: PSeq[int]) -> bool:
    """A target name is known when it belongs to either family — the discovered
    documents OR the always-provided reference pages."""
    return mem(x, found) or mem(x, gen)


@Pure
def kept(entries: PSeq[int], found: PSeq[int], gen: PSeq[int]) -> PSeq[int]:
    """The order-preserving sublist of `entries` whose names are known.
    Front-recursive: the head is emitted iff it is known, then recurse."""
    if len(entries) == 0:
        return PSeq(0).take(0)
    if known(entries[0], found, gen):
        return PSeq(entries[0]) + kept(entries.drop(1), found, gen)
    return kept(entries.drop(1), found, gen)
# pure-end


def select_toctree_entries(entries: List[int], found: List[int],
                           generated: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    Requires(Acc(list_pred(found), 1 / 2))
    Requires(Acc(list_pred(generated), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(found), 1 / 2))
    Ensures(Acc(list_pred(generated), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The retained entries are exactly those listed targets whose name belongs
    # to the discovered documents OR the always-provided reference pages,
    # in their original order.
    Ensures(ToSeq(Result()) ==
            kept(ToSeq(entries), ToSeq(found), ToSeq(generated)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(entries)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(Acc(list_pred(generated), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(entries))
        Invariant(ToSeq(result) ==
                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
        # invariants-end
        # Read the head target name freshly (its list<->sequence linkage is what
        # lets the singleton-sequence steps below discharge), then classify it
        # directly against the two families with the pure membership theory —
        # the very predicate the kept-filter branches on for this same name.
        x = entries[i - 1]
        Assert(ToSeq(entries).drop(i - 1)[0] == x)
        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
        # cons-decomposition of the non-empty sequence entries.drop(i-1):
        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
        Assert(ToSeq(entries).drop(i - 1) ==
               PSeq(ToSeq(entries).drop(i - 1)[0]) +
               ToSeq(entries).drop(i - 1).drop(1))
        cons = PSeq(x) + ToSeq(entries).drop(i)
        Assert(cons[0] == x)
        Assert(cons.drop(1) == ToSeq(entries).drop(i))
        Assert(ToSeq(entries).drop(i - 1) == cons)
        if known(x, ToSeq(found), ToSeq(generated)):
            # head is known: kept unfolds to PSeq(x) + kept(tail)
            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
            Assert(kept(ToSeq(entries).drop(i - 1),
                        ToSeq(found), ToSeq(generated)) ==
                   PSeq(x) + kept(ToSeq(entries).drop(i),
                                  ToSeq(found), ToSeq(generated)))
            old_seq = ToSeq(result)
            result = [x] + result
            Assert(ToSeq(result) == PSeq(x) + old_seq)
        else:
            # head is unknown: kept unfolds to just kept(tail)
            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
            Assert(kept(ToSeq(entries).drop(i - 1),
                        ToSeq(found), ToSeq(generated)) ==
                   kept(ToSeq(entries).drop(i),
                        ToSeq(found), ToSeq(generated)))
        Assert(ToSeq(result) ==
               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition is a TOTAL FUNCTIONAL EQUALITY to a total pure function: `ToSeq(Result()) == kept(ToSeq(entries), ToSeq(found), ToSeq(generated))`, where kept = order-preserving retention filter branching on known(x)=mem(x,found)∨mem(x,gen). This uniquely pins the return value, so any TERMINATING same-spec impl is forced to return exactly kept(...) = the gold behavior. Confirmed empirically over 11 distinct same-spec wrong impls (all confirmed same-spec via `adversary same-spec`; all verified via `adversary weakness nagini sphinx-doc__sphinx-10673 <f>`, JVM jobs run <=3 concurrently).

### ATTACK MATRIX (all SAME-spec):
- atk_1_prepatch (mem(x,found) only = the recorded prepatch bug): REJECTED (verification failed). Prepatch reproduced.
- atk_2_genonly (mem(x,generated) only, partial-domain): REJECTED.
- atk_3_retainall (return list(entries), ungrounded-oracle echo): NOT JUDGED — Nagini's front end refused to translate the program, so the spec never ruled on it and it counts in neither tally.
- atk_4_empty (return [], drop-all boundary): REJECTED.
- atk_5_negated (retain iff NOT known, control-flow-effect): REJECTED.
- atk_6_offbyone (i=len-1 start, boundary): REJECTED.
- atk_9_reversed (forward loop, prepend => reversed order): REJECTED.
- atk_8_nonterm (`while True` then return, vacuity attempt): NOT JUDGED (Nagini `dead.code` translation error) — the front end refused the program, so the spec never ruled on it and it counts in neither tally; the vacuity shape is unexpressible in Nagini's fragment, so nothing here exercises method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_10_spin (never-decrement loop w/ weak Invariant i==len, vacuity attempt): REJECTED.

TWO impls verify, BOTH are VACUOUS partial-correctness artifacts, NOT refinement-fidelity breaks; NEITHER has a faithful refined patch to materialize (step-2 precondition unmet), and each is caught by a DIFFERENT required composite gate:
- atk_7_assumefalse (`Assume(False)` then return []): VERIFIES, but `Assume(` is a G-HYGIENE BANNED TOKEN for nagini (backends/nagini.py: banned_tokens=('Assume(','Refute(')); verified via AST call-scan -> G-HYGIENE FAIL. Mechanically inadmissible. NOT submitted as a valid attack (its faithful repo refinement of `Assume(False)` does not exist; contract-stripped it returns [] != real [1] on entries=[1],found=[],gen=[1], so G-CONF would also flag it).
- atk_11_wrongreturn_spin (i=len(entries)+1, empty-body `while i>0`, never decremented, then return []): VERIFIES with NO banned token. Proven VACUOUS: a probe placing `Assert(False)` after the loop ALSO verifies (10.3s) => the post-loop path condition is logically INCONSISTENT (i=len+1>=1 contradicts loop-exit not(i>0)), so the postcondition is discharged vacuously. Its faithful refinement is a NON-TERMINATING parse_content; contract-stripped and executed it HANGS (timeout, exit 124) => caught by the REQUIRED G-CONF runtime differential gate. A non-terminating loop is not a faithful refinement of the gold's terminating per-entry loop; its terminating behavioral equivalent (drop-all = atk_4) is REJECTED by the spec. NOT submitted as a valid attack.

WHY vacuity is out-of-scope for G-EQ here: Nagini proves partial correctness and this model has no MustTerminate (420/500 nagini bundles likewise ship no MustTerminate), so non-termination/Assume-vacuity is a UNIVERSAL escape hatch, not a property of THIS spec. It is defended by the composite: G-HYGIENE bans Assume/Refute (kills proof-vacuity) and G-CONF executes the contract-stripped impl on >=1e5 inputs (a non-terminating impl hangs/diverges from the real oracle). Both G-HYGIENE and G-CONF are recorded pass and REQUIRED for green on this bundle.

A-LEG / refinement.md audit (step 3): all legs are R / A-reference / I; NO A-consumed and NO kind-3. Single trust point A3 = A-reference: deep `known`=mem(·,found)∨mem(·,gen) <=> real `docname in self.env.found_docs | generated_docnames` (other.py:121 post-patch). Validated by G-AX/axiom_check.py: EXECUTED exit 0 (kept == [e for e in entries if e in set(found)|set(generated)] over 9 boundary + 50000 fuzz + the concrete F2P scenario retaining genindex/modindex/search in order). The two non-F2P-observable gold hunks (adapters/toctree.py resolve render guard; collectors/toctree.py figure-number skip) are additive guards keyed on the same generated_docnames set, shipped verbatim in patch.diff and carried by G-RESOLVE; correctly not modeled (no independent F2P behavior). A-leg correspondence holds.

Positive control (bundle model.py, unedited) verifies (15.5s) and is same-spec. Prepatch bug reproduced (atk_1). Floor met: 9 valid same-spec rejected attacks (>=5).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (2 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_genonly.py`, `atk_4_empty.py`, `atk_5_negated.py`, `atk_6_offbyone.py`, `atk_9_reversed.py`, `atk_10_spin.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 2 | `atk_3_retainall.py`, `atk_8_nonterm.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_genonly.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_retainall.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 4 — `atk_4_empty.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_negated.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_offbyone.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9_reversed.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_nonterm.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 9 — `atk_10_spin.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10673.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A document-tree directive lists, in order, a sequence of target document
  names. Each target is classified against the set of names the project knows
  about. The project knows two disjoint families of names:

    * the names of the ordinary source documents that were discovered, and
    * the names of the auto-built reference pages (a general index, a module
      index and a full-text search page) that the standard domain always
      provides even though no source file with that name exists.

  A listed target is RETAINED (kept in the resulting ordered entry list) when
  its name belongs to EITHER family; a target whose name belongs to neither is
  rejected (it names no document at all). The auto-built reference pages must be
  retainable exactly like ordinary documents: a target naming one of them is
  kept even though it is absent from the discovered-source family.

Names are modelled as integer identifiers (each distinct document name is a
distinct int); the two families and the listed targets are `List[int]`, and the
specification is carried by the pure sequence theory `PSeq[int]`. Membership and
the order-preserving retention filter are spelled out deeply as front-recursive
folds (a single unfold per loop step), so no membership oracle is consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the classification is modelled deeply over PSeq[int]; there is no
#  consumed @ContractOnly callee.)
# axioms-end


# pure-start
@Pure
def mem(x: int, s: PSeq[int]) -> bool:
    """Whether `x` occurs in `s`. Front-recursive so a single unfold is
    available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or mem(x, s.drop(1))


@Pure
def known(x: int, found: PSeq[int], gen: PSeq[int]) -> bool:
    """A target name is known when it belongs to either family — the discovered
    documents OR the always-provided reference pages."""
    return mem(x, found) or mem(x, gen)


@Pure
def kept(entries: PSeq[int], found: PSeq[int], gen: PSeq[int]) -> PSeq[int]:
    """The order-preserving sublist of `entries` whose names are known.
    Front-recursive: the head is emitted iff it is known, then recurse."""
    if len(entries) == 0:
        return PSeq(0).take(0)
    if known(entries[0], found, gen):
        return PSeq(entries[0]) + kept(entries.drop(1), found, gen)
    return kept(entries.drop(1), found, gen)
# pure-end


def select_toctree_entries(entries: List[int], found: List[int],
                           generated: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    Requires(Acc(list_pred(found), 1 / 2))
    Requires(Acc(list_pred(generated), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(found), 1 / 2))
    Ensures(Acc(list_pred(generated), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The retained entries are exactly those listed targets whose name belongs
    # to the discovered documents OR the always-provided reference pages,
    # in their original order.
    Ensures(ToSeq(Result()) ==
            kept(ToSeq(entries), ToSeq(found), ToSeq(generated)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(entries)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(Acc(list_pred(generated), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(entries))
        Invariant(ToSeq(result) ==
                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
        # invariants-end
        # Read the head target name freshly (its list<->sequence linkage is what
        # lets the singleton-sequence steps below discharge), then classify it
        # directly against the two families with the pure membership theory —
        # the very predicate the kept-filter branches on for this same name.
        x = entries[i - 1]
        Assert(ToSeq(entries).drop(i - 1)[0] == x)
        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
        # cons-decomposition of the non-empty sequence entries.drop(i-1):
        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
        Assert(ToSeq(entries).drop(i - 1) ==
               PSeq(ToSeq(entries).drop(i - 1)[0]) +
               ToSeq(entries).drop(i - 1).drop(1))
        cons = PSeq(x) + ToSeq(entries).drop(i)
        Assert(cons[0] == x)
        Assert(cons.drop(1) == ToSeq(entries).drop(i))
        Assert(ToSeq(entries).drop(i - 1) == cons)
        if known(x, ToSeq(found), ToSeq(generated)):
            # head is known: kept unfolds to PSeq(x) + kept(tail)
            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
            Assert(kept(ToSeq(entries).drop(i - 1),
                        ToSeq(found), ToSeq(generated)) ==
                   PSeq(x) + kept(ToSeq(entries).drop(i),
                                  ToSeq(found), ToSeq(generated)))
            old_seq = ToSeq(result)
            result = [x] + result
            Assert(ToSeq(result) == PSeq(x) + old_seq)
        else:
            # head is unknown: kept unfolds to just kept(tail)
            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
            Assert(kept(ToSeq(entries).drop(i - 1),
                        ToSeq(found), ToSeq(generated)) ==
                   kept(ToSeq(entries).drop(i),
                        ToSeq(found), ToSeq(generated)))
        Assert(ToSeq(result) ==
               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition is a TOTAL FUNCTIONAL EQUALITY to a total pure function: `ToSeq(Result()) == kept(ToSeq(entries), ToSeq(found), ToSeq(generated))`, where kept = order-preserving retention filter branching on known(x)=mem(x,found)∨mem(x,gen). This uniquely pins the return value, so any TERMINATING same-spec impl is forced to return exactly kept(...) = the gold behavior. Confirmed empirically over 11 distinct same-spec wrong impls (all confirmed same-spec via `adversary same-spec`; all verified via `adversary weakness nagini sphinx-doc__sphinx-10673 <f>`, JVM jobs run <=3 concurrently).

### ATTACK MATRIX (all SAME-spec):
- atk_1_prepatch (mem(x,found) only = the recorded prepatch bug): REJECTED (verification failed). Prepatch reproduced.
- atk_2_genonly (mem(x,generated) only, partial-domain): REJECTED.
- atk_3_retainall (return list(entries), ungrounded-oracle echo): NOT JUDGED — Nagini's front end refused to translate the program, so the spec never ruled on it and it counts in neither tally.
- atk_4_empty (return [], drop-all boundary): REJECTED.
- atk_5_negated (retain iff NOT known, control-flow-effect): REJECTED.
- atk_6_offbyone (i=len-1 start, boundary): REJECTED.
- atk_9_reversed (forward loop, prepend => reversed order): REJECTED.
- atk_8_nonterm (`while True` then return, vacuity attempt): NOT JUDGED (Nagini `dead.code` translation error) — the front end refused the program, so the spec never ruled on it and it counts in neither tally; the vacuity shape is unexpressible in Nagini's fragment, so nothing here exercises method-level MustTerminate, and whether that clause would reject a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_10_spin (never-decrement loop w/ weak Invariant i==len, vacuity attempt): REJECTED.

TWO impls verify, BOTH are VACUOUS partial-correctness artifacts, NOT refinement-fidelity breaks; NEITHER has a faithful refined patch to materialize (step-2 precondition unmet), and each is caught by a DIFFERENT required composite gate:
- atk_7_assumefalse (`Assume(False)` then return []): VERIFIES, but `Assume(` is a G-HYGIENE BANNED TOKEN for nagini (backends/nagini.py: banned_tokens=('Assume(','Refute(')); verified via AST call-scan -> G-HYGIENE FAIL. Mechanically inadmissible. NOT submitted as a valid attack (its faithful repo refinement of `Assume(False)` does not exist; contract-stripped it returns [] != real [1] on entries=[1],found=[],gen=[1], so G-CONF would also flag it).
- atk_11_wrongreturn_spin (i=len(entries)+1, empty-body `while i>0`, never decremented, then return []): VERIFIES with NO banned token. Proven VACUOUS: a probe placing `Assert(False)` after the loop ALSO verifies (10.3s) => the post-loop path condition is logically INCONSISTENT (i=len+1>=1 contradicts loop-exit not(i>0)), so the postcondition is discharged vacuously. Its faithful refinement is a NON-TERMINATING parse_content; contract-stripped and executed it HANGS (timeout, exit 124) => caught by the REQUIRED G-CONF runtime differential gate. A non-terminating loop is not a faithful refinement of the gold's terminating per-entry loop; its terminating behavioral equivalent (drop-all = atk_4) is REJECTED by the spec. NOT submitted as a valid attack.

WHY vacuity is out-of-scope for G-EQ here: Nagini proves partial correctness and this model has no MustTerminate (420/500 nagini bundles likewise ship no MustTerminate), so non-termination/Assume-vacuity is a UNIVERSAL escape hatch, not a property of THIS spec. It is defended by the composite: G-HYGIENE bans Assume/Refute (kills proof-vacuity) and G-CONF executes the contract-stripped impl on >=1e5 inputs (a non-terminating impl hangs/diverges from the real oracle). Both G-HYGIENE and G-CONF are recorded pass and REQUIRED for green on this bundle.

A-LEG / refinement.md audit (step 3): all legs are R / A-reference / I; NO A-consumed and NO kind-3. Single trust point A3 = A-reference: deep `known`=mem(·,found)∨mem(·,gen) <=> real `docname in self.env.found_docs | generated_docnames` (other.py:121 post-patch). Validated by G-AX/axiom_check.py: EXECUTED exit 0 (kept == [e for e in entries if e in set(found)|set(generated)] over 9 boundary + 50000 fuzz + the concrete F2P scenario retaining genindex/modindex/search in order). The two non-F2P-observable gold hunks (adapters/toctree.py resolve render guard; collectors/toctree.py figure-number skip) are additive guards keyed on the same generated_docnames set, shipped verbatim in patch.diff and carried by G-RESOLVE; correctly not modeled (no independent F2P behavior). A-leg correspondence holds.

Positive control (bundle model.py, unedited) verifies (15.5s) and is same-spec. Prepatch bug reproduced (atk_1). Floor met: 9 valid same-spec rejected attacks (>=5).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real callee) confirmed. Modeled function select_toctree_entries requires Result == kept(entries,found,generated), where kept order-preservingly retains x iff known(x)=mem(x,found)∨mem(x,gen) — membership in the union of discovered source docs and generated reference pages. The real callee (gold patch parse_content, base_commit f35d2a6c) uses the exact same retention predicate: `docname not in self.env.found_docs | generated_docnames` selects the drop branch; complement (retain) is `docname in found_docs | generated_docnames`. Abstraction is faithful: (1) doc names str→opaque int ids, only equality/membership observed; (2) set/frozenset→sequence membership fold `mem`, order/dups irrelevant to membership; (3) set-union membership A|B ⇔ disjunction mem∨mem (standard union law); (4) order preservation and duplicate retention match — real code still appends dups (only warns). The url/self/glob branches are disclosed, legitimate modeling-boundary exclusions (not int-representable docname targets; not the F2P discriminator), not drift. Checks: model verifies under pinned Nagini (12.98s), same-spec tooling confirms spec region byte-identical, G-AX passes (deep kept == real set(found)|set(gen) membership over 9 boundary + 50000 fuzz + F2P scenario), G-CONF 100016 checks / 0 disagreements. I attempted to construct a diverging input and could not: the modeled predicate is identical to the real union-membership classification, so no input exists where the spec disagrees with the real callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view assessed = docstring + axioms (none) + pure region (mem/known/kept) + pre/post-conditions of select_toctree_entries (impl elided). Public baseline = problem_statement only (hints_text is empty). same-spec on the identity copy returns SAME (exit 0), confirming the spec region is well-formed.

The public problem_statement already states the ENTIRE desired behaviour: it names genindex/modindex/search explicitly, gives the exact symptom ('toctree contains reference to nonexisting document ...'), and asks that these three auto-generated pages be usable as toctree targets without warnings.

What the spec view adds is only an ABSTRACT restatement of that same desired outcome, not the gold code edit:
- Docstring: two disjoint name families (discovered source docs; always-provided reference pages = general index / module index / search) and 'a listed target is RETAINED when its name belongs to EITHER family'. Explicitly framed (line 3) as 'desired behaviour, not as an edit'. This is the natural specification of the public feature request.
- pure region: mem / known = mem(found) or mem(gen) / kept — an order-preserving membership-in-either-family filter over opaque int ids and PSeq[int].
- postcondition: ToSeq(Result()) == kept(ToSeq(entries), ToSeq(found), ToSeq(generated)).

No line in the spec view discloses the gold code-level edit beyond the public statement: there is NO mention of the real mechanism `self.env.found_docs | generated_docnames`, of `generated_docnames = frozenset(self.env.domains['std'].initial_data['labels'].keys())`, of the `std` domain / `initial_data['labels']`, nor of any changed file/line/symbol (other.py:121, adapters/toctree.py, collectors/toctree.py). Those repo-level bindings live ONLY in mapping.md / refinement.md / meta.json, which are NOT part of the consumer spec view. A solver reading the spec still must discover WHICH concrete set to union in and WHERE it comes from; the spec only states the target behaviour, which is the problem statement's own content.

Describing the required end behaviour (three reference pages retainable) is the spec's legitimate job and does not exceed the public problem_statement. Consistent with recorded G-LEAK pass ('spec view clean', failures: []). The two additional gold hunks (render guard in adapters/toctree.py, numbering guard in collectors/toctree.py) and the generated_docnames provenance appear only in off-view metadata, not the spec view, so no leakage from those either. No leaking line identified.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
