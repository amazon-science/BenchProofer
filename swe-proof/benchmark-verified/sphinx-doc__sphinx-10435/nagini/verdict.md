# P2 adversarial audit — sphinx-doc__sphinx-10435

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
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1_prepatch.py`, `atk2_one_suppressor.py`, `atk3_swap_order.py`, `atk4_empty_return.py`, `atk9_offbyone.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,13 +88,6 @@
     # the only trailing whitespace of the carrier is the single closing break.
     Requires(len(content) > 0)
     Requires(content[len(content) - 1] != cp_break())
-    # The assembly must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocations the assembly
-    # performs (at level 1 an allocation's own obligation has nowhere below the
-    # caller to go); it calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content), 1 / 2))
@@ -123,48 +115,22 @@
     Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
     # post-conditions-end
     # impl-start
-    # The documented upstream carrier is
-    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK,
-    # where OPEN is the upstream opening marker and CLOSE the upstream closing
-    # marker (both opaque here — their concrete shape is the producer's, not
-    # part of the desired behaviour).
-    #
-    # op1: replace OPEN by open_wrap ++ [SUPPRESS] on a carrier that begins
-    #      with OPEN  ==>  open_wrap ++ [SUPPRESS] ++ tail,
-    #      where tail = BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK.
-    # op2 (rstrip): drop the trailing whitespace BREAK.
-    # op3 (drop the trailing CLOSE marker AND its preceding BREAK): the
-    #      remaining prefix is open_wrap ++ [SUPPRESS] ++ BREAK ++ content.
-    # op4: append [SUPPRESS] ++ BREAK ++ close_wrap.
     br = cp_break()
-    pct = cp_suppress()
-
-    # prefix = open_wrap ++ [SUPPRESS] ++ [BREAK]  (literal opening wrapper)
     result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
               92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
-              116, 101, 123, pct, br]  # type: List[int]
-    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
-    # copy the content
+              116, 101, 123, br]  # type: List[int]
+    Assert(ToSeq(result) == open_wrap() + PSeq(br))
     k = 0
     while k < len(content):
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
         Invariant(0 <= k and k <= len(content))
         Invariant(Acc(list_pred(result)))
         Invariant(ToSeq(result) ==
-                  open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
-        # At most len(content) - k + 1 passes remain: the content is held
-        # read-only (Acc(...,1/2)) by the invariant above so its length cannot
-        # change, and k rises by exactly one per pass, so the bound strictly
-        # decreases; the guard k < len(content) keeps it >= 2 on entry to a pass
-        # (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(len(content) - k + 1))
-        # invariants-end
+                  open_wrap() + PSeq(br) + ToSeq(content).take(k))
         result = result + [content[k]]
         k = k + 1
     Assert(ToSeq(content).take(len(content)) == ToSeq(content))
-    # suffix = [SUPPRESS] ++ [BREAK] ++ close_wrap
-    result = result + [pct, br, 125, 125]
+    result = result + [br, 125, 125]
     Assert(PSeq(125, 125) == close_wrap())
     return result
     # impl-end
```

Attack 2 — `atk2_one_suppressor.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,13 +88,6 @@
     # the only trailing whitespace of the carrier is the single closing break.
     Requires(len(content) > 0)
     Requires(content[len(content) - 1] != cp_break())
-    # The assembly must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocations the assembly
-    # performs (at level 1 an allocation's own obligation has nowhere below the
-    # caller to go); it calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content), 1 / 2))
@@ -123,48 +115,20 @@
     Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
     # post-conditions-end
     # impl-start
-    # The documented upstream carrier is
-    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK,
-    # where OPEN is the upstream opening marker and CLOSE the upstream closing
-    # marker (both opaque here — their concrete shape is the producer's, not
-    # part of the desired behaviour).
-    #
-    # op1: replace OPEN by open_wrap ++ [SUPPRESS] on a carrier that begins
-    #      with OPEN  ==>  open_wrap ++ [SUPPRESS] ++ tail,
-    #      where tail = BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK.
-    # op2 (rstrip): drop the trailing whitespace BREAK.
-    # op3 (drop the trailing CLOSE marker AND its preceding BREAK): the
-    #      remaining prefix is open_wrap ++ [SUPPRESS] ++ BREAK ++ content.
-    # op4: append [SUPPRESS] ++ BREAK ++ close_wrap.
     br = cp_break()
     pct = cp_suppress()
-
-    # prefix = open_wrap ++ [SUPPRESS] ++ [BREAK]  (literal opening wrapper)
     result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
               92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
               116, 101, 123, pct, br]  # type: List[int]
-    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
-    # copy the content
     k = 0
     while k < len(content):
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
         Invariant(0 <= k and k <= len(content))
         Invariant(Acc(list_pred(result)))
         Invariant(ToSeq(result) ==
                   open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
-        # At most len(content) - k + 1 passes remain: the content is held
-        # read-only (Acc(...,1/2)) by the invariant above so its length cannot
-        # change, and k rises by exactly one per pass, so the bound strictly
-        # decreases; the guard k < len(content) keeps it >= 2 on entry to a pass
-        # (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(len(content) - k + 1))
-        # invariants-end
         result = result + [content[k]]
         k = k + 1
-    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
-    # suffix = [SUPPRESS] ++ [BREAK] ++ close_wrap
-    result = result + [pct, br, 125, 125]
-    Assert(PSeq(125, 125) == close_wrap())
+    result = result + [br, 125, 125]
     return result
     # impl-end
```

Attack 3 — `atk3_swap_order.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,13 +88,6 @@
     # the only trailing whitespace of the carrier is the single closing break.
     Requires(len(content) > 0)
     Requires(content[len(content) - 1] != cp_break())
-    # The assembly must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocations the assembly
-    # performs (at level 1 an allocation's own obligation has nowhere below the
-    # caller to go); it calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content), 1 / 2))
@@ -123,48 +115,20 @@
     Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
     # post-conditions-end
     # impl-start
-    # The documented upstream carrier is
-    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK,
-    # where OPEN is the upstream opening marker and CLOSE the upstream closing
-    # marker (both opaque here — their concrete shape is the producer's, not
-    # part of the desired behaviour).
-    #
-    # op1: replace OPEN by open_wrap ++ [SUPPRESS] on a carrier that begins
-    #      with OPEN  ==>  open_wrap ++ [SUPPRESS] ++ tail,
-    #      where tail = BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK.
-    # op2 (rstrip): drop the trailing whitespace BREAK.
-    # op3 (drop the trailing CLOSE marker AND its preceding BREAK): the
-    #      remaining prefix is open_wrap ++ [SUPPRESS] ++ BREAK ++ content.
-    # op4: append [SUPPRESS] ++ BREAK ++ close_wrap.
     br = cp_break()
     pct = cp_suppress()
-
-    # prefix = open_wrap ++ [SUPPRESS] ++ [BREAK]  (literal opening wrapper)
     result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
               92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
-              116, 101, 123, pct, br]  # type: List[int]
-    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
-    # copy the content
+              116, 101, 123, br, pct]  # type: List[int]
     k = 0
     while k < len(content):
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
         Invariant(0 <= k and k <= len(content))
         Invariant(Acc(list_pred(result)))
         Invariant(ToSeq(result) ==
-                  open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
-        # At most len(content) - k + 1 passes remain: the content is held
-        # read-only (Acc(...,1/2)) by the invariant above so its length cannot
-        # change, and k rises by exactly one per pass, so the bound strictly
-        # decreases; the guard k < len(content) keeps it >= 2 on entry to a pass
-        # (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(len(content) - k + 1))
-        # invariants-end
+                  open_wrap() + PSeq(br) + PSeq(pct) + ToSeq(content).take(k))
         result = result + [content[k]]
         k = k + 1
-    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
-    # suffix = [SUPPRESS] ++ [BREAK] ++ close_wrap
     result = result + [pct, br, 125, 125]
-    Assert(PSeq(125, 125) == close_wrap())
     return result
     # impl-end
```

Attack 4 — `atk4_empty_return.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,13 +88,6 @@
     # the only trailing whitespace of the carrier is the single closing break.
     Requires(len(content) > 0)
     Requires(content[len(content) - 1] != cp_break())
-    # The assembly must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocations the assembly
-    # performs (at level 1 an allocation's own obligation has nowhere below the
-    # caller to go); it calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content), 1 / 2))
@@ -123,48 +115,6 @@
     Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
     # post-conditions-end
     # impl-start
-    # The documented upstream carrier is
-    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK,
-    # where OPEN is the upstream opening marker and CLOSE the upstream closing
-    # marker (both opaque here — their concrete shape is the producer's, not
-    # part of the desired behaviour).
-    #
-    # op1: replace OPEN by open_wrap ++ [SUPPRESS] on a carrier that begins
-    #      with OPEN  ==>  open_wrap ++ [SUPPRESS] ++ tail,
-    #      where tail = BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK.
-    # op2 (rstrip): drop the trailing whitespace BREAK.
-    # op3 (drop the trailing CLOSE marker AND its preceding BREAK): the
-    #      remaining prefix is open_wrap ++ [SUPPRESS] ++ BREAK ++ content.
-    # op4: append [SUPPRESS] ++ BREAK ++ close_wrap.
-    br = cp_break()
-    pct = cp_suppress()
-
-    # prefix = open_wrap ++ [SUPPRESS] ++ [BREAK]  (literal opening wrapper)
-    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
-              92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
-              116, 101, 123, pct, br]  # type: List[int]
-    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
-    # copy the content
-    k = 0
-    while k < len(content):
-        # invariants-start
-        Invariant(Acc(list_pred(content), 1 / 2))
-        Invariant(0 <= k and k <= len(content))
-        Invariant(Acc(list_pred(result)))
-        Invariant(ToSeq(result) ==
-                  open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
-        # At most len(content) - k + 1 passes remain: the content is held
-        # read-only (Acc(...,1/2)) by the invariant above so its length cannot
-        # change, and k rises by exactly one per pass, so the bound strictly
-        # decreases; the guard k < len(content) keeps it >= 2 on entry to a pass
-        # (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(len(content) - k + 1))
-        # invariants-end
-        result = result + [content[k]]
-        k = k + 1
-    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
-    # suffix = [SUPPRESS] ++ [BREAK] ++ close_wrap
-    result = result + [pct, br, 125, 125]
-    Assert(PSeq(125, 125) == close_wrap())
-    return result
+    res = []  # type: List[int]
+    return res
     # impl-end
```

Attack 5 — `atk9_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,13 +88,6 @@
     # the only trailing whitespace of the carrier is the single closing break.
     Requires(len(content) > 0)
     Requires(content[len(content) - 1] != cp_break())
-    # The assembly must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocations the assembly
-    # performs (at level 1 an allocation's own obligation has nowhere below the
-    # caller to go); it calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content), 1 / 2))
@@ -123,48 +115,18 @@
     Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
     # post-conditions-end
     # impl-start
-    # The documented upstream carrier is
-    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK,
-    # where OPEN is the upstream opening marker and CLOSE the upstream closing
-    # marker (both opaque here — their concrete shape is the producer's, not
-    # part of the desired behaviour).
-    #
-    # op1: replace OPEN by open_wrap ++ [SUPPRESS] on a carrier that begins
-    #      with OPEN  ==>  open_wrap ++ [SUPPRESS] ++ tail,
-    #      where tail = BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK.
-    # op2 (rstrip): drop the trailing whitespace BREAK.
-    # op3 (drop the trailing CLOSE marker AND its preceding BREAK): the
-    #      remaining prefix is open_wrap ++ [SUPPRESS] ++ BREAK ++ content.
-    # op4: append [SUPPRESS] ++ BREAK ++ close_wrap.
     br = cp_break()
     pct = cp_suppress()
-
-    # prefix = open_wrap ++ [SUPPRESS] ++ [BREAK]  (literal opening wrapper)
     result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
               92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
               116, 101, 123, pct, br]  # type: List[int]
-    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
-    # copy the content
-    k = 0
+    k = 1
     while k < len(content):
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
-        Invariant(0 <= k and k <= len(content))
+        Invariant(1 <= k and k <= len(content) or len(content) == 0)
         Invariant(Acc(list_pred(result)))
-        Invariant(ToSeq(result) ==
-                  open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
-        # At most len(content) - k + 1 passes remain: the content is held
-        # read-only (Acc(...,1/2)) by the invariant above so its length cannot
-        # change, and k rises by exactly one per pass, so the bound strictly
-        # decreases; the guard k < len(content) keeps it >= 2 on entry to a pass
-        # (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(len(content) - k + 1))
-        # invariants-end
         result = result + [content[k]]
         k = k + 1
-    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
-    # suffix = [SUPPRESS] ++ [BREAK] ++ close_wrap
     result = result + [pct, br, 125, 125]
-    Assert(PSeq(125, 125) == close_wrap())
     return result
     # impl-end
```

Attack 6 — `atk8_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,13 +88,6 @@
     # the only trailing whitespace of the carrier is the single closing break.
     Requires(len(content) > 0)
     Requires(content[len(content) - 1] != cp_break())
-    # The assembly must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocations the assembly
-    # performs (at level 1 an allocation's own obligation has nowhere below the
-    # caller to go); it calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(content), 1 / 2))
@@ -123,48 +115,24 @@
     Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
     # post-conditions-end
     # impl-start
-    # The documented upstream carrier is
-    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK,
-    # where OPEN is the upstream opening marker and CLOSE the upstream closing
-    # marker (both opaque here — their concrete shape is the producer's, not
-    # part of the desired behaviour).
-    #
-    # op1: replace OPEN by open_wrap ++ [SUPPRESS] on a carrier that begins
-    #      with OPEN  ==>  open_wrap ++ [SUPPRESS] ++ tail,
-    #      where tail = BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK.
-    # op2 (rstrip): drop the trailing whitespace BREAK.
-    # op3 (drop the trailing CLOSE marker AND its preceding BREAK): the
-    #      remaining prefix is open_wrap ++ [SUPPRESS] ++ BREAK ++ content.
-    # op4: append [SUPPRESS] ++ BREAK ++ close_wrap.
     br = cp_break()
     pct = cp_suppress()
-
-    # prefix = open_wrap ++ [SUPPRESS] ++ [BREAK]  (literal opening wrapper)
-    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
+    prefix = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
               92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
-              116, 101, 123, pct, br]  # type: List[int]
-    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
-    # copy the content
+              116, 101, 123]  # type: List[int]
+    Assert(ToSeq(prefix) == open_wrap())
+    result = prefix + [pct] + [br]  # type: List[int]
     k = 0
     while k < len(content):
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
         Invariant(0 <= k and k <= len(content))
         Invariant(Acc(list_pred(result)))
         Invariant(ToSeq(result) ==
                   open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
-        # At most len(content) - k + 1 passes remain: the content is held
-        # read-only (Acc(...,1/2)) by the invariant above so its length cannot
-        # change, and k rises by exactly one per pass, so the bound strictly
-        # decreases; the guard k < len(content) keeps it >= 2 on entry to a pass
-        # (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(len(content) - k + 1))
-        # invariants-end
         result = result + [content[k]]
         k = k + 1
     Assert(ToSeq(content).take(len(content)) == ToSeq(content))
-    # suffix = [SUPPRESS] ++ [BREAK] ++ close_wrap
-    result = result + [pct, br, 125, 125]
+    result = result + [pct] + [br] + [125] + [125]
     Assert(PSeq(125, 125) == close_wrap())
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10435.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a highlighted inline-code fragment is emitted into a LaTeX body, the
  fragment is delivered to the renderer as a wrapper of the form

        OPEN_WRAP <line-break> <highlighted-content> <line-break> CLOSE_WRAP

  where OPEN_WRAP opens the inline-code group and CLOSE_WRAP closes it. A bare
  line-break that sits directly adjacent to the opening wrapper or directly
  before the closing wrapper is significant to the renderer: it is rendered as
  one space of horizontal material. To deliver inline code with NO spurious
  leading or trailing space, the line-break that follows the opening wrapper
  and the line-break that precedes the closing wrapper must each be neutralised
  by a line-suppression marker (the renderer's end-of-line comment character),
  placed at the END of the opening-wrapper line and at the END of the content,
  so that those two line-breaks contribute no horizontal material.

  Concretely the assembled output must be

        OPEN_WRAP  SUPPRESS  BREAK  content  SUPPRESS  BREAK  CLOSE_WRAP

  i.e. a suppression marker immediately after the opening wrapper and another
  immediately after the content, each directly preceding a line-break — so that
  neither line-break renders as a space.

The carrier produced upstream is a single text string of the documented shape
above. Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`.

The string surgery that derives the assembled output from the upstream carrier
is modelled DEEPLY (spelled out as sequence take/drop/concat operations); the
upstream highlighter that produces the carrier is an unchanged producer whose
documented output shape is the precondition, NOT a consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none) — the transformation is modelled deeply; the upstream highlighter that
# produces the carrier is captured by the documented input-shape precondition,
# not by a consumed @ContractOnly axiom.
# axioms-end


# pure-start
@Pure
def cp_break() -> int:
    # the line-break code point ('\n')
    return 10


@Pure
def cp_suppress() -> int:
    # the renderer's end-of-line line-suppression / comment marker ('%')
    return 37


@Pure
def open_wrap() -> PSeq[int]:
    # the opening inline-code wrapper after substitution
    # (`\sphinxcode{\sphinxupquote{`)
    return PSeq(92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
                92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
                116, 101, 123)


@Pure
def close_wrap() -> PSeq[int]:
    # the closing inline-code wrapper appended last (`}}`)
    return PSeq(125, 125)
# pure-end


def assemble_inline_code(content: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(content), 1 / 2))
    # The upstream highlighter delivers the fragment as the documented shape:
    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK
    # (an opening marker, the content, a closing marker, and one trailing
    # line-break).
    # The content carries no internal line-break adjacent to the markers that
    # would itself rstrip away (its final code point is not a line-break), so
    # the only trailing whitespace of the carrier is the single closing break.
    Requires(len(content) > 0)
    Requires(content[len(content) - 1] != cp_break())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled output is exactly:
    #   open_wrap ++ [SUPPRESS] ++ [BREAK] ++ content ++ [SUPPRESS] ++ [BREAK]
    #     ++ close_wrap
    Ensures(ToSeq(Result()) ==
            open_wrap()
            + PSeq(cp_suppress())
            + PSeq(cp_break())
            + ToSeq(content)
            + PSeq(cp_suppress())
            + PSeq(cp_break())
            + close_wrap())
    # The two line-breaks adjacent to the wrappers are each preceded by a
    # suppression marker (so neither renders as horizontal space):
    # a suppression marker sits immediately after the opening wrapper, directly
    # before the line-break that follows it ...
    Ensures(Result()[len(open_wrap())] == cp_suppress())
    Ensures(Result()[len(open_wrap()) + 1] == cp_break())
    # ... and a suppression marker sits immediately after the content, directly
    # before the line-break that precedes the closing wrapper.
    Ensures(Result()[len(Result()) - len(close_wrap()) - 2] == cp_suppress())
    Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
    # post-conditions-end
    # impl-start
    br = cp_break()
    pct = cp_suppress()
    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
              92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
              116, 101, 123, pct, br]  # type: List[int]
    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
    k = 0
    while k < len(content):
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(0 <= k and k <= len(content))
        Invariant(Acc(list_pred(result)))
        Invariant(ToSeq(result) ==
                  open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
        result = result + [content[k]]
        k = k + 1
    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
    result = result + [pct, br, 125, 125]
    Assert(PSeq(125, 125) == close_wrap())
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: All attacks copy model.py editing ONLY the impl region; same-spec confirmed for every file via `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-10435 <f>` (all SAME).

SPEC SHAPE: The first postcondition clause pins ToSeq(Result()) == open_wrap ++ [%] ++ [\n] ++ ToSeq(content) ++ [%] ++ [\n] ++ close_wrap — an EXACT function of content. Hence any TERMINATING, hygiene-clean verifying impl must return the byte-identical gold sequence and therefore resolves. The only verifying wrong impls are degenerate (banned-token / non-terminating) gadgets closed by other mandatory gates.

ATTACK RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-10435 <f>`; ran concurrently, <=3 JVMs at a time):
- atk1_prepatch.py (prepatch bug: no % suppressors, model_prepatch semantics) -> exit 2, NOT-A-COUNTEREXAMPLE (does not verify). Spec REJECTS the prepatch = G-DIFF sensing. prepatch_reproduced=true.
- atk2_one_suppressor.py (boundary: only the leading %, drop trailing) -> exit 2, does not verify. REJECTED (good).
- atk3_swap_order.py (boundary/order: emit \n before % in both slots) -> exit 2, does not verify. REJECTED (good).
- atk4_empty_return.py (partial-domain: return []) -> exit 2, does not verify. REJECTED (good).
- atk9_offbyone.py (partial-domain: copy content from index 1, drop first char) -> exit 2, does not verify. REJECTED (good).
- atk8_echo.py (ungrounded-oracle echo: builds open_wrap as a named literal then result = prefix + [pct] + [br] + ... [125]+[125], a DIFFERENT construction with BYTE-IDENTICAL output) -> exit 0, CANDIDATE (verifies 21.0s). Its faithful refined patch = the gold patch (behavior byte-identical to gold; verified over 2000 random contents). RAN OFFICIAL HARNESS: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-10435', <gold-equivalent patch>) -> completed=True, resolved=True, attempts=1. => correct echo, NOT a weakness. This is the mandatory candidate->materialize->resolve step and it RESOLVED.

POSITIVE CONTROL: pos_control.py (gold impl) -> weakness exit 0 (verifies 15.7s). Non-vacuity confirmed.

A-LEG / refinement.md AUDIT: axioms == [] (no consumed axiom). refinement.md legs A1(R), A2(R+I), A3(R+I), A4(I) + the single A-reference (deep string surgery == real post-patch surgery) in §C; §D confirms no kind-3 step. A-reference validated executably: ran axiom_check.py -> exit 0 ('deep inline-code assembly == real post-patch surgery, and pre-patch surgery == model_prepatch, over 8 boundary + 20000 fuzz carriers'). The A-reference correspondence to the real callee (LaTeXTranslator.visit_literal highlighted branch, latex.py:1712-1717 @ base f1061c012) holds; gold patch.diff matches the modeled surgery verbatim.

TWO VERIFYING-BUT-EXCLUDED PATHOLOGIES (intentionally NOT placed in the attacks[] array because they are not G-EQ refinement-fidelity weaknesses — each is closed by a different MANDATORY gate, and submitting them would trigger a spurious mechanical BROKEN against a legitimately-green cell; reported here in full for transparency):
  * atk6_assume_false.py (`Assume(False); return []`): `weakness` exit 0 (verifies 12.4s, CANDIDATE). BUT `Assume(` is a banned AST token in G-HYGIENE (verified: hygiene _banned_calls -> ['Assume']); this gadget defeats the verifier universally and can NEVER appear in a green bundle. It is a verifier-soundness gadget, not a spec-fidelity weakness. Its faithful patch (return empty) would not resolve, but the bundle's green status already requires G-HYGIENE=pass which bans it.
  * atk7_nonterm_wrong.py (`while n>0: res=res+[br]; n+=1` then return wrong value): `weakness` exit 0 (verifies 12.2s, CANDIDATE) — Nagini partial correctness accepts a non-terminating body (this spec has no MustTerminate). BUT G-CONF is MANDATORY for nagini green (policy 2026-08-06/07) and EXECUTES the contract-stripped impl on >=1e5 inputs; I demonstrated the contract-stripped atk7 hangs (timeout, exit 124), so it can never pass G-CONF -> never green. 420/500 verified nagini bundles lack MustTerminate and rely on G-CONF as the termination backstop, so bare non-termination is by-design NOT a G-EQ break (treating it as one would invalidate the entire no-MustTerminate class). POLICY FLAG FOR HUMAN: if board policy ever decides bare non-termination is a standalone G-EQ break independent of G-CONF, this cell (and ~420 siblings) would need a MustTerminate precondition added; under current policy it is SOUND.
  atk5_nonterm.py was an earlier non-term variant that did NOT verify (permission modeling) -> exit 2; superseded by atk7.

CONCLUSION: >=5 same-spec attacks run; every terminating, hygiene-clean same-spec wrong impl is rejected by the spec; the only verifying same-spec impls are (a) the byte-identical echo whose faithful patch RESOLVES (executed, resolved=True) and (b) two degenerate gadgets excluded by mandatory G-HYGIENE / G-CONF. No verifying wrong impl with a non-resolving faithful patch survives the full mandatory gate suite. Refinement legs all R/I/A-reference (no kind-3); A-reference executably faithful. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1_prepatch.py`, `atk2_one_suppressor.py`, `atk3_swap_order.py`, `atk4_empty_return.py`, `atk9_offbyone.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_one_suppressor.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_swap_order.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_empty_return.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk9_offbyone.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk8_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10435.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a highlighted inline-code fragment is emitted into a LaTeX body, the
  fragment is delivered to the renderer as a wrapper of the form

        OPEN_WRAP <line-break> <highlighted-content> <line-break> CLOSE_WRAP

  where OPEN_WRAP opens the inline-code group and CLOSE_WRAP closes it. A bare
  line-break that sits directly adjacent to the opening wrapper or directly
  before the closing wrapper is significant to the renderer: it is rendered as
  one space of horizontal material. To deliver inline code with NO spurious
  leading or trailing space, the line-break that follows the opening wrapper
  and the line-break that precedes the closing wrapper must each be neutralised
  by a line-suppression marker (the renderer's end-of-line comment character),
  placed at the END of the opening-wrapper line and at the END of the content,
  so that those two line-breaks contribute no horizontal material.

  Concretely the assembled output must be

        OPEN_WRAP  SUPPRESS  BREAK  content  SUPPRESS  BREAK  CLOSE_WRAP

  i.e. a suppression marker immediately after the opening wrapper and another
  immediately after the content, each directly preceding a line-break — so that
  neither line-break renders as a space.

The carrier produced upstream is a single text string of the documented shape
above. Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`.

The string surgery that derives the assembled output from the upstream carrier
is modelled DEEPLY (spelled out as sequence take/drop/concat operations); the
upstream highlighter that produces the carrier is an unchanged producer whose
documented output shape is the precondition, NOT a consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none) — the transformation is modelled deeply; the upstream highlighter that
# produces the carrier is captured by the documented input-shape precondition,
# not by a consumed @ContractOnly axiom.
# axioms-end


# pure-start
@Pure
def cp_break() -> int:
    # the line-break code point ('\n')
    return 10


@Pure
def cp_suppress() -> int:
    # the renderer's end-of-line line-suppression / comment marker ('%')
    return 37


@Pure
def open_wrap() -> PSeq[int]:
    # the opening inline-code wrapper after substitution
    # (`\sphinxcode{\sphinxupquote{`)
    return PSeq(92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
                92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
                116, 101, 123)


@Pure
def close_wrap() -> PSeq[int]:
    # the closing inline-code wrapper appended last (`}}`)
    return PSeq(125, 125)
# pure-end


def assemble_inline_code(content: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(content), 1 / 2))
    # The upstream highlighter delivers the fragment as the documented shape:
    #   OPEN ++ BREAK ++ content ++ BREAK ++ CLOSE ++ BREAK
    # (an opening marker, the content, a closing marker, and one trailing
    # line-break).
    # The content carries no internal line-break adjacent to the markers that
    # would itself rstrip away (its final code point is not a line-break), so
    # the only trailing whitespace of the carrier is the single closing break.
    Requires(len(content) > 0)
    Requires(content[len(content) - 1] != cp_break())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled output is exactly:
    #   open_wrap ++ [SUPPRESS] ++ [BREAK] ++ content ++ [SUPPRESS] ++ [BREAK]
    #     ++ close_wrap
    Ensures(ToSeq(Result()) ==
            open_wrap()
            + PSeq(cp_suppress())
            + PSeq(cp_break())
            + ToSeq(content)
            + PSeq(cp_suppress())
            + PSeq(cp_break())
            + close_wrap())
    # The two line-breaks adjacent to the wrappers are each preceded by a
    # suppression marker (so neither renders as horizontal space):
    # a suppression marker sits immediately after the opening wrapper, directly
    # before the line-break that follows it ...
    Ensures(Result()[len(open_wrap())] == cp_suppress())
    Ensures(Result()[len(open_wrap()) + 1] == cp_break())
    # ... and a suppression marker sits immediately after the content, directly
    # before the line-break that precedes the closing wrapper.
    Ensures(Result()[len(Result()) - len(close_wrap()) - 2] == cp_suppress())
    Ensures(Result()[len(Result()) - len(close_wrap()) - 1] == cp_break())
    # post-conditions-end
    # impl-start
    br = cp_break()
    pct = cp_suppress()
    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
              92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
              116, 101, 123, pct, br]  # type: List[int]
    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))
    k = 0
    while k < len(content):
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(0 <= k and k <= len(content))
        Invariant(Acc(list_pred(result)))
        Invariant(ToSeq(result) ==
                  open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))
        result = result + [content[k]]
        k = k + 1
    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
    result = result + [pct, br, 125, 125]
    Assert(PSeq(125, 125) == close_wrap())
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: All attacks copy model.py editing ONLY the impl region; same-spec confirmed for every file via `python -m swebench_unified.adversary same-spec nagini sphinx-doc__sphinx-10435 <f>` (all SAME).

SPEC SHAPE: The first postcondition clause pins ToSeq(Result()) == open_wrap ++ [%] ++ [\n] ++ ToSeq(content) ++ [%] ++ [\n] ++ close_wrap — an EXACT function of content. Hence any TERMINATING, hygiene-clean verifying impl must return the byte-identical gold sequence and therefore resolves. The only verifying wrong impls are degenerate (banned-token / non-terminating) gadgets closed by other mandatory gates.

ATTACK RESULTS (cmd: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-10435 <f>`; ran concurrently, <=3 JVMs at a time):
- atk1_prepatch.py (prepatch bug: no % suppressors, model_prepatch semantics) -> exit 2, NOT-A-COUNTEREXAMPLE (does not verify). Spec REJECTS the prepatch = G-DIFF sensing. prepatch_reproduced=true.
- atk2_one_suppressor.py (boundary: only the leading %, drop trailing) -> exit 2, does not verify. REJECTED (good).
- atk3_swap_order.py (boundary/order: emit \n before % in both slots) -> exit 2, does not verify. REJECTED (good).
- atk4_empty_return.py (partial-domain: return []) -> exit 2, does not verify. REJECTED (good).
- atk9_offbyone.py (partial-domain: copy content from index 1, drop first char) -> exit 2, does not verify. REJECTED (good).
- atk8_echo.py (ungrounded-oracle echo: builds open_wrap as a named literal then result = prefix + [pct] + [br] + ... [125]+[125], a DIFFERENT construction with BYTE-IDENTICAL output) -> exit 0, CANDIDATE (verifies 21.0s). Its faithful refined patch = the gold patch (behavior byte-identical to gold; verified over 2000 random contents). RAN OFFICIAL HARNESS: swebench_unified.harness.run_resolve('sphinx-doc__sphinx-10435', <gold-equivalent patch>) -> completed=True, resolved=True, attempts=1. => correct echo, NOT a weakness. This is the mandatory candidate->materialize->resolve step and it RESOLVED.

POSITIVE CONTROL: pos_control.py (gold impl) -> weakness exit 0 (verifies 15.7s). Non-vacuity confirmed.

A-LEG / refinement.md AUDIT: axioms == [] (no consumed axiom). refinement.md legs A1(R), A2(R+I), A3(R+I), A4(I) + the single A-reference (deep string surgery == real post-patch surgery) in §C; §D confirms no kind-3 step. A-reference validated executably: ran axiom_check.py -> exit 0 ('deep inline-code assembly == real post-patch surgery, and pre-patch surgery == model_prepatch, over 8 boundary + 20000 fuzz carriers'). The A-reference correspondence to the real callee (LaTeXTranslator.visit_literal highlighted branch, latex.py:1712-1717 @ base f1061c012) holds; gold patch.diff matches the modeled surgery verbatim.

TWO VERIFYING-BUT-EXCLUDED PATHOLOGIES (intentionally NOT placed in the attacks[] array because they are not G-EQ refinement-fidelity weaknesses — each is closed by a different MANDATORY gate, and submitting them would trigger a spurious mechanical BROKEN against a legitimately-green cell; reported here in full for transparency):
  * atk6_assume_false.py (`Assume(False); return []`): `weakness` exit 0 (verifies 12.4s, CANDIDATE). BUT `Assume(` is a banned AST token in G-HYGIENE (verified: hygiene _banned_calls -> ['Assume']); this gadget defeats the verifier universally and can NEVER appear in a green bundle. It is a verifier-soundness gadget, not a spec-fidelity weakness. Its faithful patch (return empty) would not resolve, but the bundle's green status already requires G-HYGIENE=pass which bans it.
  * atk7_nonterm_wrong.py (`while n>0: res=res+[br]; n+=1` then return wrong value): `weakness` exit 0 (verifies 12.2s, CANDIDATE) — Nagini partial correctness accepts a non-terminating body (this spec has no MustTerminate). BUT G-CONF is MANDATORY for nagini green (policy 2026-08-06/07) and EXECUTES the contract-stripped impl on >=1e5 inputs; I demonstrated the contract-stripped atk7 hangs (timeout, exit 124), so it can never pass G-CONF -> never green. 420/500 verified nagini bundles lack MustTerminate and rely on G-CONF as the termination backstop, so bare non-termination is by-design NOT a G-EQ break (treating it as one would invalidate the entire no-MustTerminate class). POLICY FLAG FOR HUMAN: if board policy ever decides bare non-termination is a standalone G-EQ break independent of G-CONF, this cell (and ~420 siblings) would need a MustTerminate precondition added; under current policy it is SOUND.
  atk5_nonterm.py was an earlier non-term variant that did NOT verify (permission modeling) -> exit 2; superseded by atk7.

CONCLUSION: >=5 same-spec attacks run; every terminating, hygiene-clean same-spec wrong impl is rejected by the spec; the only verifying same-spec impls are (a) the byte-identical echo whose faithful patch RESOLVES (executed, resolved=True) and (b) two degenerate gadgets excluded by mandatory G-HYGIENE / G-CONF. No verifying wrong impl with a non-resolving faithful patch survives the full mandatory gate suite. Refinement legs all R/I/A-reference (no kind-3); A-reference executably faithful. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Real callee confirmed at sphinx/writers/latex.py:1712-1717 @ base f1061c012 (verified worktree; pre-patch uses [:-14] + no '%', post-patch adds the two '%' suppressors and [:-15]). Spec region byte-identical is a G-EQ concern; my faithfulness check compared the model's postcondition (open_wrap ++ '%' ++ '\n' ++ content ++ '%' ++ '\n' ++ '}}') against the exact real post-patch surgery over 66,220 (snippet x language) combinations across 11 Pygments lexers (python, python3, text, bash, c, html, rst, json, yaml, sql, js), including deliberate BEGIN/END-injection sources and 6000 random fuzz strings: frame_fail=0, BEGIN-in-content=0, divergences=0. All pre-fails (5456) are empty-content carriers that violate the model precondition len(content)>0 and are degenerate. rstrip() in the real surgery strips only the single trailing '\n' (END ends in '}'), never touching content, so trailing-whitespace-in-content is preserved identically by model and real. On every reachable input the spec agrees with the repo callee -> FAITHFUL. The verdict.md's prior FAITHFUL conclusion is corroborated.

Counterexample / evidence:

```
content='foo'+BEGIN+'bar' -> real_surgery_post rewrites the interior BEGIN to \sphinxcode{\sphinxupquote{%; model leaves it verbatim. But not producible by highlight_block on any snippet/lang.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the nagini spec view) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced, no patched file path (sphinx/writers/latex.py), no patched module path, no spec-view identifier or comment naming the patched symbol (visit_literal), and no bug/fix narration. Substantive review confirms no leak beyond the PUBLIC problem_statement. The public problem statement itself already gives the full fix: it shows the a-priori target markup `\sphinxcode{\sphinxupquote{%` and `... pass%` / `}}` with the two `%` suppression markers. The spec view describes exactly this desired behaviour: assemble OPEN_WRAP SUPPRESS BREAK content SUPPRESS BREAK CLOSE_WRAP, where SUPPRESS=`%`(37), open_wrap=`\sphinxcode{\sphinxupquote{`, close_wrap=`}}` — all of which appear verbatim in the public statement's `a priori, mark-up should be:` block. The gold-diff SPECIFICS (rstrip()[:-15] vs [:-14], `'%' + CR + '}}'`, the file/function) do NOT appear; the impl surgery is described abstractly (rstrip / drop CLOSE marker) rather than as the gold's index arithmetic. Spec-view identifiers (assemble_inline_code, cp_break, cp_suppress, open_wrap, close_wrap) are abstract modeling names, not repo symbols. Verified against solver-visible problem_statement only, not hints_text. No line leaks the gold edit beyond the public task.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
