# P2 adversarial audit — django__django-17084

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_drop_window.py`, `atk_drop_subquery.py`, `atk_true.py`, `atk_and_window.py`, `atk_offbyone.py`, `atk_diverge.py`, `atk_diverge2.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_drop_window.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,47 +91,19 @@
     ))
     # post-conditions-end
     # impl-start
-    wseq = ToSeq(window_flags)  # type: PSeq[bool]
     sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
     refs_subquery = False
-    refs_window = False
-    i = len(window_flags)
-    while i > 0:
-        # invariants-start
+    j = len(subquery_flags)
+    while j > 0:
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
         Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(0 <= i and i <= len(window_flags))
-        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
-        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
-        refs_window = window_flags[i - 1] or refs_window
-        i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
-    j = len(subquery_flags)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
         Invariant(0 <= j and j <= len(subquery_flags))
         Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
         Invariant(MustTerminate(j + 1))
-        # invariants-end
         Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
         Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
         refs_subquery = subquery_flags[j - 1] or refs_subquery
         j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
-    return other_forces_wrap or refs_subquery or refs_window
+    return other_forces_wrap or refs_subquery
     # impl-end
```

Attack 2 — `atk_drop_subquery.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,46 +92,18 @@
     # post-conditions-end
     # impl-start
     wseq = ToSeq(window_flags)  # type: PSeq[bool]
-    sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
-    refs_subquery = False
     refs_window = False
     i = len(window_flags)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
         Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
         Invariant(0 <= i and i <= len(window_flags))
         Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
         Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
         refs_window = window_flags[i - 1] or refs_window
         i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
-    j = len(subquery_flags)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
-        Invariant(0 <= j and j <= len(subquery_flags))
-        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
-        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
-        refs_subquery = subquery_flags[j - 1] or refs_subquery
-        j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
-    return other_forces_wrap or refs_subquery or refs_window
+    return other_forces_wrap or refs_window
     # impl-end
```

Attack 3 — `atk_true.py` → rejected (same spec, does not verify — good)

```diff
@@ -91,47 +91,5 @@
     ))
     # post-conditions-end
     # impl-start
-    wseq = ToSeq(window_flags)  # type: PSeq[bool]
-    sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
-    refs_subquery = False
-    refs_window = False
-    i = len(window_flags)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(0 <= i and i <= len(window_flags))
-        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
-        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
-        refs_window = window_flags[i - 1] or refs_window
-        i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
-    j = len(subquery_flags)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
-        Invariant(0 <= j and j <= len(subquery_flags))
-        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
-        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
-        refs_subquery = subquery_flags[j - 1] or refs_subquery
-        j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
-    return other_forces_wrap or refs_subquery or refs_window
+    return True
     # impl-end
```

Attack 4 — `atk_and_window.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,44 +94,29 @@
     wseq = ToSeq(window_flags)  # type: PSeq[bool]
     sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
     refs_subquery = False
-    refs_window = False
+    refs_window = True
     i = len(window_flags)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
         Invariant(wseq == ToSeq(window_flags))
         Invariant(sseq == ToSeq(subquery_flags))
         Invariant(0 <= i and i <= len(window_flags))
-        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
-        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
-        refs_window = window_flags[i - 1] or refs_window
+        refs_window = window_flags[i - 1] and refs_window
         i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
     j = len(subquery_flags)
     while j > 0:
-        # invariants-start
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
         Invariant(wseq == ToSeq(window_flags))
         Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
         Invariant(0 <= j and j <= len(subquery_flags))
         Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
         Invariant(MustTerminate(j + 1))
-        # invariants-end
         Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
         Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
         refs_subquery = subquery_flags[j - 1] or refs_subquery
         j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
     return other_forces_wrap or refs_subquery or refs_window
     # impl-end
```

Attack 5 — `atk_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,42 +96,27 @@
     refs_subquery = False
     refs_window = False
     i = len(window_flags)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
         Invariant(wseq == ToSeq(window_flags))
         Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(0 <= i and i <= len(window_flags))
-        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
+        Invariant(1 <= i and i <= len(window_flags))
         Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
-        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
         refs_window = window_flags[i - 1] or refs_window
         i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
     j = len(subquery_flags)
     while j > 0:
-        # invariants-start
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
         Invariant(wseq == ToSeq(window_flags))
         Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
         Invariant(0 <= j and j <= len(subquery_flags))
         Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
         Invariant(MustTerminate(j + 1))
-        # invariants-end
         Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
         Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
         refs_subquery = subquery_flags[j - 1] or refs_subquery
         j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
     return other_forces_wrap or refs_subquery or refs_window
     # impl-end
```

Attack 6 — `atk_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,45 +93,10 @@
     # impl-start
     wseq = ToSeq(window_flags)  # type: PSeq[bool]
     sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
-    refs_subquery = False
-    refs_window = False
-    i = len(window_flags)
-    while i > 0:
-        # invariants-start
+    k = 1
+    while k > 0:
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(0 <= i and i <= len(window_flags))
-        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
-        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
-        refs_window = window_flags[i - 1] or refs_window
-        i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
-    j = len(subquery_flags)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
-        Invariant(0 <= j and j <= len(subquery_flags))
-        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
-        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
-        refs_subquery = subquery_flags[j - 1] or refs_subquery
-        j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
-    return other_forces_wrap or refs_subquery or refs_window
+        k = k + 1
+    return any_referenced_flag(wseq) or any_referenced_flag(sseq) or other_forces_wrap
     # impl-end
```

Attack 7 — `atk_diverge2.py` → rejected (same spec, does not verify — good)

```diff
@@ -93,45 +93,14 @@
     # impl-start
     wseq = ToSeq(window_flags)  # type: PSeq[bool]
     sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
-    refs_subquery = False
+    i = len(window_flags)
     refs_window = False
-    i = len(window_flags)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(window_flags), 1 / 2))
         Invariant(Acc(list_pred(subquery_flags), 1 / 2))
         Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
         Invariant(0 <= i and i <= len(window_flags))
-        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
-        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
         refs_window = window_flags[i - 1] or refs_window
-        i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
-    j = len(subquery_flags)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
-        Invariant(0 <= j and j <= len(subquery_flags))
-        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
-        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
-        refs_subquery = subquery_flags[j - 1] or refs_subquery
-        j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
-    return other_forces_wrap or refs_subquery or refs_window
+    return any_referenced_flag(wseq) or any_referenced_flag(sseq) or other_forces_wrap
     # impl-end
```

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,45 +93,5 @@
     # impl-start
     wseq = ToSeq(window_flags)  # type: PSeq[bool]
     sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
-    refs_subquery = False
-    refs_window = False
-    i = len(window_flags)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(0 <= i and i <= len(window_flags))
-        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
-        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
-        refs_window = window_flags[i - 1] or refs_window
-        i = i - 1
-    Assert(refs_window == any_referenced_flag(wseq))
-    j = len(subquery_flags)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(window_flags), 1 / 2))
-        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
-        Invariant(wseq == ToSeq(window_flags))
-        Invariant(sseq == ToSeq(subquery_flags))
-        Invariant(refs_window == any_referenced_flag(wseq))
-        Invariant(0 <= j and j <= len(subquery_flags))
-        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
-        # Same discharge of the caller's MustTerminate(2): measure j.
-        Invariant(MustTerminate(j + 1))
-        # invariants-end
-        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
-        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
-        refs_subquery = subquery_flags[j - 1] or refs_subquery
-        j = j - 1
-    Assert(refs_subquery == any_referenced_flag(sseq))
-    Assert(refs_window == any_referenced_flag(wseq))
-    return other_forces_wrap or refs_subquery or refs_window
+    return any_referenced_flag(wseq) or any_referenced_flag(sseq) or other_forces_wrap
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-17084.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single-row aggregation is evaluated over a set of aggregate
  expressions, it must be computed inside a wrapping subquery whenever any of
  several conditions holds. Among the conditions is this one: if any aggregate
  references a previously-defined annotation that itself contains a windowed
  (OVER-clause) expression, the aggregation MUST be wrapped — an aggregate may
  not be evaluated directly over a window result. Symmetrically (and
  unchanged), referencing an annotation that is a correlated subquery also
  forces wrapping. The remaining wrap-forcing conditions (grouping, slicing,
  pre-existing aggregation, qualification, distinctness, set combination) are
  collapsed into a single flag here.

  Concretely: the wrap decision is the disjunction of (a) any-referenced-
  annotation-contains-a-window, (b) any-referenced-annotation-is-a-subquery,
  and (c) the collapsed remaining conditions. Each of (a) and (b) is the
  order-independent OR over the per-referenced-annotation flags.

The per-reference flag lists are modelled as `List[bool]`; each disjunction is
spelled out deeply as a front-recursive `@Pure` OR-fold (`any_referenced_flag`),
validated == Python's `any(...)` reduction out-of-band by axiom_check.py
(G-AX). No consumed axiom: the changed operation is the disjunction itself,
modelled directly.

Deciding the wrap is a bounded computation — it reads each per-reference flag
once and MUST actually deliver its verdict to the caller (a total-correctness
obligation, carried as MustTerminate in the precondition). An implementation
that diverges before returning would satisfy the value postcondition only
vacuously and would never hand the aggregation pipeline its decision.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none consumed — the changed operation is the OR-reduction, modelled deeply
#  below as a front-recursive @Pure fold and validated against Python's any(...)
#  by axiom_check.py as an A-reference.)
# axioms-end


# pure-start
@Pure
def any_referenced_flag(flags: PSeq[bool]) -> bool:
    """The order-independent OR-reduction over a per-referenced-annotation flag
    sequence: True iff at least one referenced annotation carries the flag.
    Front-recursive so a single unfold is available per loop step. Models
    Python's `any(flags)`."""
    if len(flags) == 0:
        return False
    return flags[0] or any_referenced_flag(flags.drop(1))
# pure-end


def requires_subquery_wrap(
    window_flags: List[bool],
    subquery_flags: List[bool],
    other_forces_wrap: bool,
) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(window_flags), 1 / 2))
    Requires(Acc(list_pred(subquery_flags), 1 / 2))
    # TERMINATION: the wrap decision must actually ANSWER — it is a bounded
    # computation (one read per flag). Nagini is a partial-correctness verifier
    # by default, so without this obligation a non-terminating implementation
    # (e.g. an endless loop before returning) satisfies the value postcondition
    # vacuously; the real decision always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window_flags), 1 / 2))
    Ensures(Acc(list_pred(subquery_flags), 1 / 2))
    # The wrap decision is exactly the disjunction of the three terms; the
    # window term (a) and the subquery term (b) are the OR over the per-
    # referenced-annotation flags, and (c) is the collapsed remainder.
    Ensures(Result() == (
        any_referenced_flag(ToSeq(window_flags))
        or any_referenced_flag(ToSeq(subquery_flags))
        or other_forces_wrap
    ))
    # Discriminating consequence: a single window-containing reference forces
    # the wrap regardless of the subquery flags and the collapsed remainder.
    Ensures(Implies(
        any_referenced_flag(ToSeq(window_flags)),
        Result(),
    ))
    # post-conditions-end
    # impl-start
    wseq = ToSeq(window_flags)  # type: PSeq[bool]
    sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
    refs_subquery = False
    refs_window = False
    i = len(window_flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(0 <= i and i <= len(window_flags))
        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
        refs_window = window_flags[i - 1] or refs_window
        i = i - 1
    Assert(refs_window == any_referenced_flag(wseq))
    j = len(subquery_flags)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(refs_window == any_referenced_flag(wseq))
        Invariant(0 <= j and j <= len(subquery_flags))
        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
        # Same discharge of the caller's MustTerminate(2): measure j.
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
        refs_subquery = subquery_flags[j - 1] or refs_subquery
        j = j - 1
    Assert(refs_subquery == any_referenced_flag(sseq))
    Assert(refs_window == any_referenced_flag(wseq))
    return other_forces_wrap or refs_subquery or refs_window
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, focus on A-legs + model/patch correspondence (R/I legs covered by G-CONF).

SPEC SHAPE: postcondition pins Result() to a TOTAL functional equality Result() == any(window_flags) or any(subquery_flags) or other_forces_wrap, plus a redundant Implies(any(window_flags), Result()) consequence, plus Requires(MustTerminate(2)). Exact equality over the whole abstract List[bool]xList[bool]xbool domain + a totality obligation leaves no room for a behaviorally-wrong verifying impl and blocks divergence.

atk_drop_window (prepatch bug: window term dropped): NOT-A-COUNTEREXAMPLE, does not verify (postcondition fails on a True window flag). REJECTED.
- atk_drop_subquery (partial-domain: subquery term dropped): NOT-A-COUNTEREXAMPLE, does not verify. REJECTED.
- atk_true (ungrounded-oracle echo: return True): NOT-A-COUNTEREXAMPLE, does not verify (fails when all disjuncts False). REJECTED.
- atk_and_window (wrong reduction: all() instead of any() on window loop): NOT-A-COUNTEREXAMPLE, does not verify. REJECTED.
- atk_offbyone (boundary: window loop stops at i>1, index 0 never read): NOT-A-COUNTEREXAMPLE, does not verify. REJECTED.
- atk_diverge (control-flow-effect: infinite `while k>0: k+=1` before returning): NOT-A-COUNTEREXAMPLE, does not verify (MustTerminate(2) fails). REJECTED.
- atk_diverge2 (control-flow-effect: loop measure never decreases): NOT-A-COUNTEREXAMPLE, does not verify (MustTerminate fails). REJECTED.
- atk_echo (verifying echo: `return any_referenced_flag(wseq) or any_referenced_flag(sseq) or other_forces_wrap`): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (17.9s).

positive_control (=model.py copy): CANDIDATE, verifies (19.4s).

CANDIDATE -> RESOLVE (mandatory materialize + run_resolve): atk_echo and positive_control are behaviorally identical to the gold (the exact three-term disjunction), so their faithful refined patch IS the gold patch (django/db/models/sql/query.py: add refs_window accumulator, refs_window |= any(getattr(ann,'contains_over_clause',True) for ref in get_refs()), and refs_window disjunct). Materialized to faithful_patch.diff and ran the OFFICIAL harness (swebench_unified.run_evaluation via docker, run_id sbu-eq-direct-17084-r1). RESULT: resolved=true, patch_successfully_applied=true; FAIL_TO_PASS test_referenced_window_requires_wrapping SUCCESS; all PASS_TO_PASS (100+) SUCCESS, zero failures. So the sole verifying candidate maps to a RESOLVING patch. No verify-not-correct exhibited.
This is infra flakiness, not a non-resolve.)

REFINEMENT.MD AUDIT: 6 legs. A1/A2/A3 = R (dict/set iteration flattened to List[bool]; six untouched disjuncts collapsed to other_forces_wrap; getattr defaults folded at binding boundary). A4/A5 = A-reference + I (OR-reduction modeled DEEPLY by front-recursive @Pure fold any_referenced_flag, verified loops; validated == Python any() by axiom_check.py). A6 = I + R (disjunction == branch guard). NO kind-3 leg; NO consumed @ContractOnly axiom (axioms region empty). A-reference soundness independently re-run: python axiom_check.py -> exit 0 (fold==any() on 12 boundary + 20000 fuzz lists; contains_over_clause/subquery stdlib stand-ins faithfully mirror expressions.py: Window=True @1703, BaseExpression composite any-propagation @246-250, Subquery.subquery=True @1544, getattr defaults True/False). Correspondence to real callees holds. prepatch reproduced: atk_drop_window (the prepatch skeleton) correctly REJECTED; meta G-DIFF confirms model_prepatch.py fails verification.

VERDICT: SOUND. 8 distinct impls audited (7 wrong all rejected incl. 2 divergence probes of MustTerminate; 1 echo verifies and its faithful patch RESOLVES under the official harness).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_drop_window.py`, `atk_drop_subquery.py`, `atk_true.py`, `atk_and_window.py`, `atk_offbyone.py`, `atk_diverge.py`, `atk_diverge2.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_drop_window.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_drop_subquery.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_true.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_and_window.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_offbyone.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_diverge.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_diverge2.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-17084.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single-row aggregation is evaluated over a set of aggregate
  expressions, it must be computed inside a wrapping subquery whenever any of
  several conditions holds. Among the conditions is this one: if any aggregate
  references a previously-defined annotation that itself contains a windowed
  (OVER-clause) expression, the aggregation MUST be wrapped — an aggregate may
  not be evaluated directly over a window result. Symmetrically (and
  unchanged), referencing an annotation that is a correlated subquery also
  forces wrapping. The remaining wrap-forcing conditions (grouping, slicing,
  pre-existing aggregation, qualification, distinctness, set combination) are
  collapsed into a single flag here.

  Concretely: the wrap decision is the disjunction of (a) any-referenced-
  annotation-contains-a-window, (b) any-referenced-annotation-is-a-subquery,
  and (c) the collapsed remaining conditions. Each of (a) and (b) is the
  order-independent OR over the per-referenced-annotation flags.

The per-reference flag lists are modelled as `List[bool]`; each disjunction is
spelled out deeply as a front-recursive `@Pure` OR-fold (`any_referenced_flag`),
validated == Python's `any(...)` reduction out-of-band by axiom_check.py
(G-AX). No consumed axiom: the changed operation is the disjunction itself,
modelled directly.

Deciding the wrap is a bounded computation — it reads each per-reference flag
once and MUST actually deliver its verdict to the caller (a total-correctness
obligation, carried as MustTerminate in the precondition). An implementation
that diverges before returning would satisfy the value postcondition only
vacuously and would never hand the aggregation pipeline its decision.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none consumed — the changed operation is the OR-reduction, modelled deeply
#  below as a front-recursive @Pure fold and validated against Python's any(...)
#  by axiom_check.py as an A-reference.)
# axioms-end


# pure-start
@Pure
def any_referenced_flag(flags: PSeq[bool]) -> bool:
    """The order-independent OR-reduction over a per-referenced-annotation flag
    sequence: True iff at least one referenced annotation carries the flag.
    Front-recursive so a single unfold is available per loop step. Models
    Python's `any(flags)`."""
    if len(flags) == 0:
        return False
    return flags[0] or any_referenced_flag(flags.drop(1))
# pure-end


def requires_subquery_wrap(
    window_flags: List[bool],
    subquery_flags: List[bool],
    other_forces_wrap: bool,
) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(window_flags), 1 / 2))
    Requires(Acc(list_pred(subquery_flags), 1 / 2))
    # TERMINATION: the wrap decision must actually ANSWER — it is a bounded
    # computation (one read per flag). Nagini is a partial-correctness verifier
    # by default, so without this obligation a non-terminating implementation
    # (e.g. an endless loop before returning) satisfies the value postcondition
    # vacuously; the real decision always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(window_flags), 1 / 2))
    Ensures(Acc(list_pred(subquery_flags), 1 / 2))
    # The wrap decision is exactly the disjunction of the three terms; the
    # window term (a) and the subquery term (b) are the OR over the per-
    # referenced-annotation flags, and (c) is the collapsed remainder.
    Ensures(Result() == (
        any_referenced_flag(ToSeq(window_flags))
        or any_referenced_flag(ToSeq(subquery_flags))
        or other_forces_wrap
    ))
    # Discriminating consequence: a single window-containing reference forces
    # the wrap regardless of the subquery flags and the collapsed remainder.
    Ensures(Implies(
        any_referenced_flag(ToSeq(window_flags)),
        Result(),
    ))
    # post-conditions-end
    # impl-start
    wseq = ToSeq(window_flags)  # type: PSeq[bool]
    sseq = ToSeq(subquery_flags)  # type: PSeq[bool]
    refs_subquery = False
    refs_window = False
    i = len(window_flags)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(0 <= i and i <= len(window_flags))
        Invariant(refs_window == any_referenced_flag(wseq.drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(wseq.drop(i - 1)[0] == wseq[i - 1])
        Assert(wseq.drop(i - 1).drop(1) == wseq.drop(i))
        refs_window = window_flags[i - 1] or refs_window
        i = i - 1
    Assert(refs_window == any_referenced_flag(wseq))
    j = len(subquery_flags)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(window_flags), 1 / 2))
        Invariant(Acc(list_pred(subquery_flags), 1 / 2))
        Invariant(wseq == ToSeq(window_flags))
        Invariant(sseq == ToSeq(subquery_flags))
        Invariant(refs_window == any_referenced_flag(wseq))
        Invariant(0 <= j and j <= len(subquery_flags))
        Invariant(refs_subquery == any_referenced_flag(sseq.drop(j)))
        # Same discharge of the caller's MustTerminate(2): measure j.
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(sseq.drop(j - 1)[0] == sseq[j - 1])
        Assert(sseq.drop(j - 1).drop(1) == sseq.drop(j))
        refs_subquery = subquery_flags[j - 1] or refs_subquery
        j = j - 1
    Assert(refs_subquery == any_referenced_flag(sseq))
    Assert(refs_window == any_referenced_flag(wseq))
    return other_forces_wrap or refs_subquery or refs_window
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, focus on A-legs + model/patch correspondence (R/I legs covered by G-CONF).

SPEC SHAPE: postcondition pins Result() to a TOTAL functional equality Result() == any(window_flags) or any(subquery_flags) or other_forces_wrap, plus a redundant Implies(any(window_flags), Result()) consequence, plus Requires(MustTerminate(2)). Exact equality over the whole abstract List[bool]xList[bool]xbool domain + a totality obligation leaves no room for a behaviorally-wrong verifying impl and blocks divergence.

atk_drop_window (prepatch bug: window term dropped): NOT-A-COUNTEREXAMPLE, does not verify (postcondition fails on a True window flag). REJECTED.
- atk_drop_subquery (partial-domain: subquery term dropped): NOT-A-COUNTEREXAMPLE, does not verify. REJECTED.
- atk_true (ungrounded-oracle echo: return True): NOT-A-COUNTEREXAMPLE, does not verify (fails when all disjuncts False). REJECTED.
- atk_and_window (wrong reduction: all() instead of any() on window loop): NOT-A-COUNTEREXAMPLE, does not verify. REJECTED.
- atk_offbyone (boundary: window loop stops at i>1, index 0 never read): NOT-A-COUNTEREXAMPLE, does not verify. REJECTED.
- atk_diverge (control-flow-effect: infinite `while k>0: k+=1` before returning): NOT-A-COUNTEREXAMPLE, does not verify (MustTerminate(2) fails). REJECTED.
- atk_diverge2 (control-flow-effect: loop measure never decreases): NOT-A-COUNTEREXAMPLE, does not verify (MustTerminate fails). REJECTED.
- atk_echo (verifying echo: `return any_referenced_flag(wseq) or any_referenced_flag(sseq) or other_forces_wrap`): CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (17.9s).

positive_control (=model.py copy): CANDIDATE, verifies (19.4s).

CANDIDATE -> RESOLVE (mandatory materialize + run_resolve): atk_echo and positive_control are behaviorally identical to the gold (the exact three-term disjunction), so their faithful refined patch IS the gold patch (django/db/models/sql/query.py: add refs_window accumulator, refs_window |= any(getattr(ann,'contains_over_clause',True) for ref in get_refs()), and refs_window disjunct). Materialized to faithful_patch.diff and ran the OFFICIAL harness (swebench_unified.run_evaluation via docker, run_id sbu-eq-direct-17084-r1). RESULT: resolved=true, patch_successfully_applied=true; FAIL_TO_PASS test_referenced_window_requires_wrapping SUCCESS; all PASS_TO_PASS (100+) SUCCESS, zero failures. So the sole verifying candidate maps to a RESOLVING patch. No verify-not-correct exhibited.
This is infra flakiness, not a non-resolve.)

REFINEMENT.MD AUDIT: 6 legs. A1/A2/A3 = R (dict/set iteration flattened to List[bool]; six untouched disjuncts collapsed to other_forces_wrap; getattr defaults folded at binding boundary). A4/A5 = A-reference + I (OR-reduction modeled DEEPLY by front-recursive @Pure fold any_referenced_flag, verified loops; validated == Python any() by axiom_check.py). A6 = I + R (disjunction == branch guard). NO kind-3 leg; NO consumed @ContractOnly axiom (axioms region empty). A-reference soundness independently re-run: python axiom_check.py -> exit 0 (fold==any() on 12 boundary + 20000 fuzz lists; contains_over_clause/subquery stdlib stand-ins faithfully mirror expressions.py: Window=True @1703, BaseExpression composite any-propagation @246-250, Subquery.subquery=True @1544, getattr defaults True/False). Correspondence to real callees holds. prepatch reproduced: atk_drop_window (the prepatch skeleton) correctly REJECTED; meta G-DIFF confirms model_prepatch.py fails verification.

VERDICT: SOUND. 8 distinct impls audited (7 wrong all rejected incl. 2 divergence probes of MustTerminate; 1 echo verifies and its faithful patch RESOLVES under the official harness).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (no drift, not too strong). The modeled `requires_subquery_wrap` returns exactly `any(window_flags) or any(subquery_flags) or other_forces_wrap`. This is a total equality — verified concretely against the real callee `Query.get_aggregation` (django/db/models/sql/query.py) at base_commit f8c43aca, post gold patch.

Gold patch (confirmed byte-for-byte from the dataset) adds `refs_window = False`, `refs_window |= any(getattr(self.annotations[ref], 'contains_over_clause', True) for ref in aggregate.get_refs())`, and `or refs_window` to the 8-disjunct wrap guard (query.py:449-457 pre-patch inspected). The full real guard is: `isinstance(self.group_by, tuple) or self.is_sliced or has_existing_aggregation or refs_subquery or refs_window or qualify or self.distinct or self.combinator`.

Refinement mapping is exact and complete: refs_window↔any(window_flags), refs_subquery↔any(subquery_flags), and the six untouched scalar disjuncts collapse into the free boolean other_forces_wrap. No disjunct is dropped. Because `|=`/`any(...)` is order-independent and idempotent, the nested for-aggregate/for-ref accumulation collapses exactly to a single any() over the flattened per-(aggregate,ref) list, so any(window_flags)==refs_window and any(subquery_flags)==refs_subquery for every concrete query (empty get_refs() -> any([])==False, matching zero flat elements). Result() therefore equals the real branch guard on the entire abstract domain List[bool]xList[bool]xbool — this is a total equality postcondition, NOT an over-approximation, so there is no input where the modeled function could return more or less than the real callee.

The extra Ensures(Implies(any_referenced_flag(window_flags), Result())) is a pure logical consequence of that equality (True window flag => disjunction is True); it does not strengthen the spec beyond the real behavior — any correct impl of the disjunction satisfies it. Requires(MustTerminate(2)) is faithful: the real wrap decision is a bounded finite accumulation plus a scalar OR that always returns its verdict.

Machine checks: same-spec on model.py returns exit 0 (spec region intact, sha matches); scripts/nagini_verify.sh model.py -> Verification successful (17.99s); axiom_check corroboration in verdict.md (fold==Python any(); contains_over_clause/subquery resolution incl. Coalesce(Window(...),0.0)->True). No diverging input exists — the modeled function agrees with the real repo callee on all inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently reconstructed spec view (docstring + signature + Nagini pre/post contracts; impl region elided) and screened it against the public problem_statement only (not hints_text). Mechanical leakage.screen passes (0 hard failures): no gold-diff line reproduced, no diff markers, no patched file path (django/db/models/sql/query.py) or module, no spec-view identifier/comment embedding the patched symbol get_aggregation, no narration terms. Semantic review confirms the gold edit's repo internals (contains_over_clause, refs_window, refs_subquery, get_aggregation, self.annotations, get_refs, Coalesce) are all ABSENT from the view. The docstring states desired behavior — an aggregate referencing an annotation containing a windowed/OVER-clause expression must be wrapped in a subquery — which is the natural behavioral corollary of the PUBLIC problem statement ('Cannot use aggregate over window functions since 4.2', with the exact Coalesce(Window(...))-then-aggregate example). The other wrap-forcing conditions named (subquery/grouping/slicing/qualification/distinctness/combination) are explicitly framed as unchanged/collapsed context and localize no edit. No gold-patch phrasing or code is quoted. Bundle is not relaxed (no relaxed_leakage flag, no RELAXED_LEAKAGE.md); judged under strict policy. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
