# P2 adversarial audit — django__django-13568

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -107,39 +105,6 @@
     # post-conditions-end
     # impl-start
     satisfied = field_unique
-    if not satisfied:
-        i = len(c_span)
-        found = False
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(c_span), 1 / 2))
-            Invariant(Acc(list_pred(c_single), 1 / 2))
-            Invariant(Acc(list_pred(c_total), 1 / 2))
-            Invariant(len(c_span) == len(c_single) and
-                      len(c_single) == len(c_total))
-            Invariant(0 <= i and i <= len(c_span))
-            Invariant(found == any_covers(ToSeq(c_span).drop(i),
-                                          ToSeq(c_single).drop(i),
-                                          ToSeq(c_total).drop(i),
-                                          username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            sp = c_span[i - 1]
-            sg = c_single[i - 1]
-            tt = c_total[i - 1]
-            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
-            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
-            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
-            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
-            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
-            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
-            if tt == 1 and sp == 1 and sg == username_field:
-                found = True
-            i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
-        satisfied = found
     if satisfied:
         return NO_DIAGNOSTIC
     if default_regime:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -111,34 +109,18 @@
         i = len(c_span)
         found = False
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(c_span), 1 / 2))
             Invariant(Acc(list_pred(c_single), 1 / 2))
             Invariant(Acc(list_pred(c_total), 1 / 2))
             Invariant(len(c_span) == len(c_single) and
                       len(c_single) == len(c_total))
             Invariant(0 <= i and i <= len(c_span))
-            Invariant(found == any_covers(ToSeq(c_span).drop(i),
-                                          ToSeq(c_single).drop(i),
-                                          ToSeq(c_total).drop(i),
-                                          username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             sp = c_span[i - 1]
             sg = c_single[i - 1]
             tt = c_total[i - 1]
-            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
-            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
-            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
-            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
-            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
-            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
-            if tt == 1 and sp == 1 and sg == username_field:
+            if tt == 1 and sg == username_field:
                 found = True
             i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
         satisfied = found
     if satisfied:
         return NO_DIAGNOSTIC
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -111,34 +109,18 @@
         i = len(c_span)
         found = False
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(c_span), 1 / 2))
             Invariant(Acc(list_pred(c_single), 1 / 2))
             Invariant(Acc(list_pred(c_total), 1 / 2))
             Invariant(len(c_span) == len(c_single) and
                       len(c_single) == len(c_total))
             Invariant(0 <= i and i <= len(c_span))
-            Invariant(found == any_covers(ToSeq(c_span).drop(i),
-                                          ToSeq(c_single).drop(i),
-                                          ToSeq(c_total).drop(i),
-                                          username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             sp = c_span[i - 1]
             sg = c_single[i - 1]
             tt = c_total[i - 1]
-            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
-            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
-            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
-            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
-            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
-            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
-            if tt == 1 and sp == 1 and sg == username_field:
+            if sp == 1 and sg == username_field:
                 found = True
             i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
         satisfied = found
     if satisfied:
         return NO_DIAGNOSTIC
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -111,7 +109,6 @@
         i = len(c_span)
         found = False
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(c_span), 1 / 2))
             Invariant(Acc(list_pred(c_single), 1 / 2))
             Invariant(Acc(list_pred(c_total), 1 / 2))
@@ -122,8 +119,6 @@
                                           ToSeq(c_single).drop(i),
                                           ToSeq(c_total).drop(i),
                                           username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             sp = c_span[i - 1]
             sg = c_single[i - 1]
             tt = c_total[i - 1]
@@ -136,13 +131,10 @@
             if tt == 1 and sp == 1 and sg == username_field:
                 found = True
             i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
         satisfied = found
     if satisfied:
         return NO_DIAGNOSTIC
     if default_regime:
-        return HARD_ERROR
-    return WARNING
+        return WARNING
+    return HARD_ERROR
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -106,43 +104,5 @@
                     Result() == (HARD_ERROR if default_regime else WARNING)))
     # post-conditions-end
     # impl-start
-    satisfied = field_unique
-    if not satisfied:
-        i = len(c_span)
-        found = False
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(c_span), 1 / 2))
-            Invariant(Acc(list_pred(c_single), 1 / 2))
-            Invariant(Acc(list_pred(c_total), 1 / 2))
-            Invariant(len(c_span) == len(c_single) and
-                      len(c_single) == len(c_total))
-            Invariant(0 <= i and i <= len(c_span))
-            Invariant(found == any_covers(ToSeq(c_span).drop(i),
-                                          ToSeq(c_single).drop(i),
-                                          ToSeq(c_total).drop(i),
-                                          username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            sp = c_span[i - 1]
-            sg = c_single[i - 1]
-            tt = c_total[i - 1]
-            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
-            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
-            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
-            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
-            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
-            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
-            if tt == 1 and sp == 1 and sg == username_field:
-                found = True
-            i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
-        satisfied = found
-    if satisfied:
-        return NO_DIAGNOSTIC
-    if default_regime:
-        return HARD_ERROR
-    return WARNING
+    return NO_DIAGNOSTIC
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -110,35 +108,19 @@
     if not satisfied:
         i = len(c_span)
         found = False
-        while i > 0:
-            # invariants-start
+        while i > 1:
             Invariant(Acc(list_pred(c_span), 1 / 2))
             Invariant(Acc(list_pred(c_single), 1 / 2))
             Invariant(Acc(list_pred(c_total), 1 / 2))
             Invariant(len(c_span) == len(c_single) and
                       len(c_single) == len(c_total))
-            Invariant(0 <= i and i <= len(c_span))
-            Invariant(found == any_covers(ToSeq(c_span).drop(i),
-                                          ToSeq(c_single).drop(i),
-                                          ToSeq(c_total).drop(i),
-                                          username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
+            Invariant(1 <= i and i <= len(c_span))
             sp = c_span[i - 1]
             sg = c_single[i - 1]
             tt = c_total[i - 1]
-            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
-            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
-            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
-            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
-            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
-            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
             if tt == 1 and sp == 1 and sg == username_field:
                 found = True
             i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
         satisfied = found
     if satisfied:
         return NO_DIAGNOSTIC
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -111,34 +109,18 @@
         i = len(c_span)
         found = False
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(c_span), 1 / 2))
             Invariant(Acc(list_pred(c_single), 1 / 2))
             Invariant(Acc(list_pred(c_total), 1 / 2))
             Invariant(len(c_span) == len(c_single) and
                       len(c_single) == len(c_total))
             Invariant(0 <= i and i <= len(c_span))
-            Invariant(found == any_covers(ToSeq(c_span).drop(i),
-                                          ToSeq(c_single).drop(i),
-                                          ToSeq(c_total).drop(i),
-                                          username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
             sp = c_span[i - 1]
             sg = c_single[i - 1]
             tt = c_total[i - 1]
-            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
-            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
-            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
-            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
-            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
-            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
-            if tt == 1 and sp == 1 and sg == username_field:
+            if tt == 1 and sp <= 1 and sg == username_field:
                 found = True
             i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
         satisfied = found
     if satisfied:
         return NO_DIAGNOSTIC
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 NO_DIAGNOSTIC = 0
@@ -86,7 +85,6 @@
     Requires(Acc(list_pred(c_single), 1 / 2))
     Requires(Acc(list_pred(c_total), 1 / 2))
     Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c_span), 1 / 2))
@@ -108,37 +106,25 @@
     # impl-start
     satisfied = field_unique
     if not satisfied:
-        i = len(c_span)
+        i = 0
         found = False
-        while i > 0:
-            # invariants-start
+        while i < len(c_span):
             Invariant(Acc(list_pred(c_span), 1 / 2))
             Invariant(Acc(list_pred(c_single), 1 / 2))
             Invariant(Acc(list_pred(c_total), 1 / 2))
             Invariant(len(c_span) == len(c_single) and
                       len(c_single) == len(c_total))
             Invariant(0 <= i and i <= len(c_span))
-            Invariant(found == any_covers(ToSeq(c_span).drop(i),
-                                          ToSeq(c_single).drop(i),
-                                          ToSeq(c_total).drop(i),
+            Invariant(found == any_covers(ToSeq(c_span).take(i),
+                                          ToSeq(c_single).take(i),
+                                          ToSeq(c_total).take(i),
                                           username_field))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            sp = c_span[i - 1]
-            sg = c_single[i - 1]
-            tt = c_total[i - 1]
-            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
-            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
-            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
-            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
-            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
-            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
+            sp = c_span[i]
+            sg = c_single[i]
+            tt = c_total[i]
             if tt == 1 and sp == 1 and sg == username_field:
                 found = True
-            i = i - 1
-        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
-        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
-        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
+            i = i + 1
         satisfied = found
     if satisfied:
         return NO_DIAGNOSTIC
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13568.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model validation routine decides whether the designated login field of a
  user model satisfies the uniqueness obligation, and what diagnostic — if any —
  to emit when it does not.

  The login field is treated as SATISFYING the uniqueness obligation when EITHER
  of two independent guarantees holds:

    (a) the field itself carries a direct uniqueness guarantee; OR
    (b) the model declares at least one UNCONDITIONAL uniqueness constraint that
        ranges over EXACTLY the login field and no other field. A constraint
        guards uniqueness for the whole table only when it carries no predicate
        restricting the rows it applies to; a constraint that is qualified by
        such a predicate guarantees uniqueness only for the rows it selects and
        therefore does NOT discharge the obligation. A constraint spanning more
        than one field (a composite key) likewise does NOT discharge it, because
        it does not make the login field unique on its own.

  When neither guarantee holds the routine emits a diagnostic, and the SEVERITY
  of that diagnostic depends on the configured authentication regime: under the
  single default regime the diagnostic is a hard error; under any other regime
  it is a softer warning. When either guarantee holds, no diagnostic is emitted
  regardless of the regime.

The diagnostic outcome is modelled as a small integer code: 0 = no diagnostic,
1 = hard error, 2 = warning. The constraint list is modelled by three parallel
integer sequences of equal length: `span[k]` is the number of fields the k-th
constraint ranges over, `single[k]` is the single field identifier when the k-th
constraint spans exactly one field, and `total[k]` is 1 iff the k-th constraint
is unconditional (else 0). Field names are integer identifiers (the only
operation performed on them is equality). The existential search over the
constraint list is modelled deeply as a front-recursive predicate paired with a
verified loop.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


NO_DIAGNOSTIC = 0
HARD_ERROR = 1
WARNING = 2


# axioms-start
# (no axiomatized callees: the constraint-search behaviour is modelled deeply)
# axioms-end


# pure-start
@Pure
def covers(span: int, single: int, total: int, field: int) -> bool:
    """One constraint discharges the obligation for `field` iff it is
    unconditional (total == 1) and ranges over exactly that one field."""
    return total == 1 and span == 1 and single == field


@Pure
def any_covers(span: PSeq[int], single: PSeq[int], total: PSeq[int],
               field: int) -> bool:
    """Some constraint in the (parallel) sequences discharges the obligation
    for `field`. Front-recursive so a single unfold is available per loop step.
    The three sequences are read in lock-step at index 0, then recurse on the
    tails."""
    Requires(len(span) == len(single) and len(single) == len(total))
    if len(span) == 0:
        return False
    return (covers(span[0], single[0], total[0], field) or
            any_covers(span.drop(1), single.drop(1), total.drop(1), field))
# pure-end


def username_field_diagnostic(field_unique: bool,
                              c_span: List[int],
                              c_single: List[int],
                              c_total: List[int],
                              username_field: int,
                              default_regime: bool) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(c_span), 1 / 2))
    Requires(Acc(list_pred(c_single), 1 / 2))
    Requires(Acc(list_pred(c_total), 1 / 2))
    Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(c_span), 1 / 2))
    Ensures(Acc(list_pred(c_single), 1 / 2))
    Ensures(Acc(list_pred(c_total), 1 / 2))
    Ensures(len(c_span) == len(c_single) and len(c_single) == len(c_total))
    # The obligation is discharged exactly when the field is directly unique OR
    # some unconditional single-field constraint ranges over the login field.
    # No diagnostic in that case; otherwise the severity follows the regime.
    Ensures(Implies(field_unique or
                    any_covers(ToSeq(c_span), ToSeq(c_single),
                               ToSeq(c_total), username_field),
                    Result() == NO_DIAGNOSTIC))
    Ensures(Implies(not (field_unique or
                         any_covers(ToSeq(c_span), ToSeq(c_single),
                                    ToSeq(c_total), username_field)),
                    Result() == (HARD_ERROR if default_regime else WARNING)))
    # post-conditions-end
    # impl-start
    satisfied = field_unique
    if not satisfied:
        i = len(c_span)
        found = False
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(c_span), 1 / 2))
            Invariant(Acc(list_pred(c_single), 1 / 2))
            Invariant(Acc(list_pred(c_total), 1 / 2))
            Invariant(len(c_span) == len(c_single) and
                      len(c_single) == len(c_total))
            Invariant(0 <= i and i <= len(c_span))
            Invariant(found == any_covers(ToSeq(c_span).drop(i),
                                          ToSeq(c_single).drop(i),
                                          ToSeq(c_total).drop(i),
                                          username_field))
            # invariants-end
            sp = c_span[i - 1]
            sg = c_single[i - 1]
            tt = c_total[i - 1]
            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
            if tt == 1 and sp == 1 and sg == username_field:
                found = True
            i = i - 1
        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
        satisfied = found
    if satisfied:
        return NO_DIAGNOSTIC
    if default_regime:
        return HARD_ERROR
    return WARNING
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 same-spec wrong/alternative impls attacked; positive control + axiom_check pass. No CANDIDATE, so no faithful patch to materialize/resolve.

Why the spec is airtight: the postcondition of username_field_diagnostic is TOTAL and FUNCTIONAL — the two Implies clauses partition the entire input space and pin Result() exactly: NO_DIAGNOSTIC(0) iff (field_unique OR any_covers(ToSeq(c_span),ToSeq(c_single),ToSeq(c_total),username_field)); else HARD_ERROR(1) if default_regime else WARNING(2). any_covers/covers is a DEEP model (front-recursive PSeq predicate) requiring total==1 AND span==1 AND single==field. Any same-spec impl that verifies must compute exactly the gold decision, so verify=>correct here.

Attacks (all same-spec exit 0 via `adversary same-spec`; all `adversary weakness` exit 2 = NOT-A-COUNTEREXAMPLE, verification FAILED):
- atk_1 prepatch bug (constraints never consulted; satisfied=field_unique only) — reproduces the pre-patch defect; does NOT verify (fails postcondition on field_unique=False with a covering unconditional single-field constraint). prepatch_reproduced=true.
- atk_2 control-flow-effect: composite key wrongly covers (drops span==1) — does NOT verify.
- atk_3 control-flow-effect: conditional constraint wrongly covers (drops total==1) — does NOT verify.
- atk_4 severity swap (E003<->W004 branches flipped) — does NOT verify.
- atk_5 ungrounded-oracle echo: always return NO_DIAGNOSTIC — does NOT verify.
- atk_6 boundary/off-by-one: loop `while i>1` skips index 0 (partial domain) — does NOT verify.
- atk_7 boundary broaden: `sp <= 1` admits span==0 — does NOT verify.
- atk_8 behaviorally-equivalent forward loop (take(i) invariant) — does NOT verify (proof-engineering; even if it did it would be a resolving echo, not a break).

Exact commands:
  python -m swebench_unified.adversary same-spec nagini django__django-13568 <atk> -> exit 0 for all 8 + pos_control
  python -m swebench_unified.adversary weakness  nagini django__django-13568 <atk> -> exit 2 for atk_1..8; exit 0 (CANDIDATE, verifies 14.4s) for pos_control
  python axiom_check.py -> exit 0: 'G-AX OK: deep model (any_covers/covers) == stdlib stand-in tuple-equality + total_unique_constraints(condition is None) semantics on 12 boundary + 4000 fuzz'

Refinement.md leg audit: A1(R), A2(I), A3(R+I deep model), A4(I), A5(R), A6(R). Section C asserts NO kind-3 steps and NO A-consumed / A-reference axioms; model.py axioms region confirmed EMPTY. The one introduced op (existential constraint search) is modeled deeply, not axiomatized, so there is no oracle trust point. axiom_check.py independently grounds the deep predicate to real Django's UniqueConstraint.fields tuple-equality + Options.total_unique_constraints (condition is None) filter. Model<->patch correspondence holds. No A-leg correspondence failure. No verifying wrong impl exists; patches map is empty by construction.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13568.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model validation routine decides whether the designated login field of a
  user model satisfies the uniqueness obligation, and what diagnostic — if any —
  to emit when it does not.

  The login field is treated as SATISFYING the uniqueness obligation when EITHER
  of two independent guarantees holds:

    (a) the field itself carries a direct uniqueness guarantee; OR
    (b) the model declares at least one UNCONDITIONAL uniqueness constraint that
        ranges over EXACTLY the login field and no other field. A constraint
        guards uniqueness for the whole table only when it carries no predicate
        restricting the rows it applies to; a constraint that is qualified by
        such a predicate guarantees uniqueness only for the rows it selects and
        therefore does NOT discharge the obligation. A constraint spanning more
        than one field (a composite key) likewise does NOT discharge it, because
        it does not make the login field unique on its own.

  When neither guarantee holds the routine emits a diagnostic, and the SEVERITY
  of that diagnostic depends on the configured authentication regime: under the
  single default regime the diagnostic is a hard error; under any other regime
  it is a softer warning. When either guarantee holds, no diagnostic is emitted
  regardless of the regime.

The diagnostic outcome is modelled as a small integer code: 0 = no diagnostic,
1 = hard error, 2 = warning. The constraint list is modelled by three parallel
integer sequences of equal length: `span[k]` is the number of fields the k-th
constraint ranges over, `single[k]` is the single field identifier when the k-th
constraint spans exactly one field, and `total[k]` is 1 iff the k-th constraint
is unconditional (else 0). Field names are integer identifiers (the only
operation performed on them is equality). The existential search over the
constraint list is modelled deeply as a front-recursive predicate paired with a
verified loop.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


NO_DIAGNOSTIC = 0
HARD_ERROR = 1
WARNING = 2


# axioms-start
# (no axiomatized callees: the constraint-search behaviour is modelled deeply)
# axioms-end


# pure-start
@Pure
def covers(span: int, single: int, total: int, field: int) -> bool:
    """One constraint discharges the obligation for `field` iff it is
    unconditional (total == 1) and ranges over exactly that one field."""
    return total == 1 and span == 1 and single == field


@Pure
def any_covers(span: PSeq[int], single: PSeq[int], total: PSeq[int],
               field: int) -> bool:
    """Some constraint in the (parallel) sequences discharges the obligation
    for `field`. Front-recursive so a single unfold is available per loop step.
    The three sequences are read in lock-step at index 0, then recurse on the
    tails."""
    Requires(len(span) == len(single) and len(single) == len(total))
    if len(span) == 0:
        return False
    return (covers(span[0], single[0], total[0], field) or
            any_covers(span.drop(1), single.drop(1), total.drop(1), field))
# pure-end


def username_field_diagnostic(field_unique: bool,
                              c_span: List[int],
                              c_single: List[int],
                              c_total: List[int],
                              username_field: int,
                              default_regime: bool) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(c_span), 1 / 2))
    Requires(Acc(list_pred(c_single), 1 / 2))
    Requires(Acc(list_pred(c_total), 1 / 2))
    Requires(len(c_span) == len(c_single) and len(c_single) == len(c_total))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(c_span), 1 / 2))
    Ensures(Acc(list_pred(c_single), 1 / 2))
    Ensures(Acc(list_pred(c_total), 1 / 2))
    Ensures(len(c_span) == len(c_single) and len(c_single) == len(c_total))
    # The obligation is discharged exactly when the field is directly unique OR
    # some unconditional single-field constraint ranges over the login field.
    # No diagnostic in that case; otherwise the severity follows the regime.
    Ensures(Implies(field_unique or
                    any_covers(ToSeq(c_span), ToSeq(c_single),
                               ToSeq(c_total), username_field),
                    Result() == NO_DIAGNOSTIC))
    Ensures(Implies(not (field_unique or
                         any_covers(ToSeq(c_span), ToSeq(c_single),
                                    ToSeq(c_total), username_field)),
                    Result() == (HARD_ERROR if default_regime else WARNING)))
    # post-conditions-end
    # impl-start
    satisfied = field_unique
    if not satisfied:
        i = len(c_span)
        found = False
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(c_span), 1 / 2))
            Invariant(Acc(list_pred(c_single), 1 / 2))
            Invariant(Acc(list_pred(c_total), 1 / 2))
            Invariant(len(c_span) == len(c_single) and
                      len(c_single) == len(c_total))
            Invariant(0 <= i and i <= len(c_span))
            Invariant(found == any_covers(ToSeq(c_span).drop(i),
                                          ToSeq(c_single).drop(i),
                                          ToSeq(c_total).drop(i),
                                          username_field))
            # invariants-end
            sp = c_span[i - 1]
            sg = c_single[i - 1]
            tt = c_total[i - 1]
            Assert(ToSeq(c_span).drop(i - 1)[0] == sp)
            Assert(ToSeq(c_span).drop(i - 1).drop(1) == ToSeq(c_span).drop(i))
            Assert(ToSeq(c_single).drop(i - 1)[0] == sg)
            Assert(ToSeq(c_single).drop(i - 1).drop(1) == ToSeq(c_single).drop(i))
            Assert(ToSeq(c_total).drop(i - 1)[0] == tt)
            Assert(ToSeq(c_total).drop(i - 1).drop(1) == ToSeq(c_total).drop(i))
            if tt == 1 and sp == 1 and sg == username_field:
                found = True
            i = i - 1
        Assert(ToSeq(c_span).drop(0) == ToSeq(c_span))
        Assert(ToSeq(c_single).drop(0) == ToSeq(c_single))
        Assert(ToSeq(c_total).drop(0) == ToSeq(c_total))
        satisfied = found
    if satisfied:
        return NO_DIAGNOSTIC
    if default_regime:
        return HARD_ERROR
    return WARNING
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 same-spec wrong/alternative impls attacked; positive control + axiom_check pass. No CANDIDATE, so no faithful patch to materialize/resolve.

Why the spec is airtight: the postcondition of username_field_diagnostic is TOTAL and FUNCTIONAL — the two Implies clauses partition the entire input space and pin Result() exactly: NO_DIAGNOSTIC(0) iff (field_unique OR any_covers(ToSeq(c_span),ToSeq(c_single),ToSeq(c_total),username_field)); else HARD_ERROR(1) if default_regime else WARNING(2). any_covers/covers is a DEEP model (front-recursive PSeq predicate) requiring total==1 AND span==1 AND single==field. Any same-spec impl that verifies must compute exactly the gold decision, so verify=>correct here.

Attacks (all same-spec exit 0 via `adversary same-spec`; all `adversary weakness` exit 2 = NOT-A-COUNTEREXAMPLE, verification FAILED):
- atk_1 prepatch bug (constraints never consulted; satisfied=field_unique only) — reproduces the pre-patch defect; does NOT verify (fails postcondition on field_unique=False with a covering unconditional single-field constraint). prepatch_reproduced=true.
- atk_2 control-flow-effect: composite key wrongly covers (drops span==1) — does NOT verify.
- atk_3 control-flow-effect: conditional constraint wrongly covers (drops total==1) — does NOT verify.
- atk_4 severity swap (E003<->W004 branches flipped) — does NOT verify.
- atk_5 ungrounded-oracle echo: always return NO_DIAGNOSTIC — does NOT verify.
- atk_6 boundary/off-by-one: loop `while i>1` skips index 0 (partial domain) — does NOT verify.
- atk_7 boundary broaden: `sp <= 1` admits span==0 — does NOT verify.
- atk_8 behaviorally-equivalent forward loop (take(i) invariant) — does NOT verify (proof-engineering; even if it did it would be a resolving echo, not a break).

Exact commands:
  python -m swebench_unified.adversary same-spec nagini django__django-13568 <atk> -> exit 0 for all 8 + pos_control
  python -m swebench_unified.adversary weakness  nagini django__django-13568 <atk> -> exit 2 for atk_1..8; exit 0 (CANDIDATE, verifies 14.4s) for pos_control
  python axiom_check.py -> exit 0: 'G-AX OK: deep model (any_covers/covers) == stdlib stand-in tuple-equality + total_unique_constraints(condition is None) semantics on 12 boundary + 4000 fuzz'

Refinement.md leg audit: A1(R), A2(I), A3(R+I deep model), A4(I), A5(R), A6(R). Section C asserts NO kind-3 steps and NO A-consumed / A-reference axioms; model.py axioms region confirmed EMPTY. The one introduced op (existential constraint search) is modeled deeply, not axiomatized, so there is no oracle trust point. axiom_check.py independently grounds the deep predicate to real Django's UniqueConstraint.fields tuple-equality + Options.total_unique_constraints (condition is None) filter. Model<->patch correspondence holds. No A-leg correspondence failure. No verifying wrong impl exists; patches map is empty by construction.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift check) on django__django-13568 nagini. The modeled function is the username-uniqueness block of check_user_model; the axioms region is EMPTY, so there is no over-approximated callee — the constraint search is modeled deeply as any_covers/covers + a verified loop. Faithfulness therefore reduces to: does the abstract spec agree with the real PATCHED repo function on every bridgeable abstract input?

Real patched behavior (django/contrib/auth/checks.py @ base ede9fac7): emit diagnostic iff `not field.unique AND not any(c.fields == (USERNAME_FIELD,) for c in cls._meta.total_unique_constraints)`; severity auth.E003 iff AUTHENTICATION_BACKENDS == ['django.contrib.auth.backends.ModelBackend'] else auth.W004. total_unique_constraints = constraints that are UniqueConstraint with condition is None (options.py:831-841, confirmed at base commit).

Spec: NO_DIAGNOSTIC(0) iff field_unique OR any_covers, where covers := total==1 ∧ span==1 ∧ single==field; else HARD_ERROR(1) if default_regime else WARNING(2).

The abstraction bridge is EXACT with no drift on any reachable input:
- total==1 ↔ condition is None (the total_unique_constraints filter). A conditional constraint → total=0 → never covers, matching its exclusion from the iterated collection.
- span==1 ∧ single==field ↔ fields == (USERNAME_FIELD,). Composite keys (span≠1) never equal a 1-tuple; span==0 has no concrete counterpart (UniqueConstraint forbids empty fields) and is harmlessly non-covering.
- field_unique ↔ .unique; default_regime ↔ exact backend-list equality; outcome codes 0/1/2 ↔ nothing/E003/W004 (the ids the F2P asserts).

Could NOT construct any diverging input where the spec disagrees with the real callee. Verified independently: (1) bundle model verifies under pinned Nagini (14.2s, 'Verification successful'); (2) axiom_check.py passes — deep any_covers/covers == tuple-equality + condition-None filter on 12 boundary + 4000 fuzz constraint lists; (3) G-CONF conformance_check.py drives 100013 inputs (13 boundary shapes × field_unique × regime + 100000 seeded fuzz) through the bridge into the REAL patched check_user_model with 0 disagreements. Discriminating witness (field_unique=False, one unconditional UniqueConstraint(fields=('username',)), default backend): real→guard false→no diagnostic; spec→any_covers true→NO_DIAGNOSTIC — agree, and it is exactly the F2P test_username_unique_with_model_constraint case that prepatch fails. Recorded meta.json gates all pass; my independent check confirms FAITHFUL — no spec-too-strong drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + pure predicates + pre/post-conditions, impl elided) fully abstracts every repo-level symbol of the gold edit: no USERNAME_FIELD, total_unique_constraints, UniqueConstraint, AUTHENTICATION_BACKENDS/ModelBackend, checks.py, auth.E003/W004. Carriers are neutral (username_field:int, default_regime:bool, parallel int seqs). No diff markers, no patched file/module path, no reproduced gold-patch line. Re-ran leakage.screen over the real spec view -> pass ('spec view clean'), 0 hard failures; meta G-LEAK=pass, relaxed_leakage=None. The public problem_statement already discloses more concrete locating info (USERNAME_FIELD, auth.E003, UniqueConstraint(fields=['username']), Model._meta.constraints, and the intended 'extend the check to look at _meta.constraints' fix) than the abstract spec does. The spec's extra precision (unconditional/single-field nuance mirroring condition-is-None filtering; error-vs-warning severity which is pre-existing, not the edit) is abstract behaviour inherent to any faithful spec, not an identifier/edit echo, and none of it is sourced from hints_text. No gold-reconstruction path beyond what the problem_statement already grants.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
