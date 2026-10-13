# P2 adversarial audit — django__django-13346

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # `num_values` is the count of right-hand-side values (>= 1: an empty
     # membership set never reaches comparison-string production).
     Requires(num_values >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -101,26 +99,23 @@
     Ensures(ToSeq(Result()) == slots_sql(num_values))
     # post-conditions-end
     # impl-start
+    # Forward build: prepend nothing, append each formed slot with a leading
+    # separator except the first. Different control-flow than the reference,
+    # same string produced.
     result = []  # type: List[int]
-    i = num_values
-    while i > 0:
+    i = 0
+    while i < num_values:
         # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= num_values)
-        # `result` already holds the expansion of the trailing `num_values - i`
-        # slots (built back-to-front so the front-recursive slots_sql unfolds
-        # one slot per step).
-        Invariant(ToSeq(result) == slots_sql(num_values - i))
-        Invariant(MustTerminate(i + 1))
+        Invariant(ToSeq(result) == slots_sql(i))
         # invariants-end
-        if i == num_values:
-            # Last slot: no trailing separator.
+        if i == 0:
             result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                       40, 37, 115, 44, 32, 39, 36, 39, 41]
         else:
-            # Earlier slot: wrapped slot, then separator, then the rest.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
-        i = i - 1
+            result = result + [44, 32, 74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
+                      40, 37, 115, 44, 32, 39, 36, 39, 41]
+        i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # `num_values` is the count of right-hand-side values (>= 1: an empty
     # membership set never reaches comparison-string production).
     Requires(num_values >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -101,26 +99,22 @@
     Ensures(ToSeq(Result()) == slots_sql(num_values))
     # post-conditions-end
     # impl-start
+    # Correct alternative: explicit base case for the single-value membership
+    # test, then the reference back-to-front build for the rest.
+    if num_values == 1:
+        return [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41]
     result = []  # type: List[int]
     i = num_values
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= num_values)
-        # `result` already holds the expansion of the trailing `num_values - i`
-        # slots (built back-to-front so the front-recursive slots_sql unfolds
-        # one slot per step).
         Invariant(ToSeq(result) == slots_sql(num_values - i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         if i == num_values:
-            # Last slot: no trailing separator.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41]
+            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41]
         else:
-            # Earlier slot: wrapped slot, then separator, then the rest.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
+            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
         i = i - 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # `num_values` is the count of right-hand-side values (>= 1: an empty
     # membership set never reaches comparison-string production).
     Requires(num_values >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -101,26 +99,19 @@
     Ensures(ToSeq(Result()) == slots_sql(num_values))
     # post-conditions-end
     # impl-start
+    # BOUNDARY BUG: loops while i > 1, so it produces one FEWER slot than
+    # required (off-by-one). Faithful patch would emit num_values-1 slots.
     result = []  # type: List[int]
     i = num_values
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= num_values)
-        # `result` already holds the expansion of the trailing `num_values - i`
-        # slots (built back-to-front so the front-recursive slots_sql unfolds
-        # one slot per step).
-        Invariant(ToSeq(result) == slots_sql(num_values - i))
-        Invariant(MustTerminate(i + 1))
+        Invariant(1 <= i and i <= num_values)
         # invariants-end
         if i == num_values:
-            # Last slot: no trailing separator.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41]
+            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41]
         else:
-            # Earlier slot: wrapped slot, then separator, then the rest.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
+            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
         i = i - 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # `num_values` is the count of right-hand-side values (>= 1: an empty
     # membership set never reaches comparison-string production).
     Requires(num_values >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -101,26 +99,21 @@
     Ensures(ToSeq(Result()) == slots_sql(num_values))
     # post-conditions-end
     # impl-start
+    # PARTIAL-DOMAIN BUG: only the single-element case is wrapped; multi-value
+    # membership falls back to the bare placeholder shape (the pre-fix bug).
+    if num_values == 1:
+        return [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41]
     result = []  # type: List[int]
     i = num_values
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= num_values)
-        # `result` already holds the expansion of the trailing `num_values - i`
-        # slots (built back-to-front so the front-recursive slots_sql unfolds
-        # one slot per step).
-        Invariant(ToSeq(result) == slots_sql(num_values - i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         if i == num_values:
-            # Last slot: no trailing separator.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41]
+            result = [37, 115]
         else:
-            # Earlier slot: wrapped slot, then separator, then the rest.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
+            result = [37, 115, 44, 32] + result
         i = i - 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # `num_values` is the count of right-hand-side values (>= 1: an empty
     # membership set never reaches comparison-string production).
     Requires(num_values >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -101,26 +99,21 @@
     Ensures(ToSeq(Result()) == slots_sql(num_values))
     # post-conditions-end
     # impl-start
+    # CONTROL-FLOW EFFECT BUG: appends a spurious trailing separator when
+    # num_values is even, corrupting the comparison string on half the domain.
     result = []  # type: List[int]
     i = num_values
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= num_values)
-        # `result` already holds the expansion of the trailing `num_values - i`
-        # slots (built back-to-front so the front-recursive slots_sql unfolds
-        # one slot per step).
-        Invariant(ToSeq(result) == slots_sql(num_values - i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         if i == num_values:
-            # Last slot: no trailing separator.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41]
+            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41]
         else:
-            # Earlier slot: wrapped slot, then separator, then the rest.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
+            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
         i = i - 1
+    if num_values % 2 == 0:
+        result = result + [44, 32]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # `num_values` is the count of right-hand-side values (>= 1: an empty
     # membership set never reaches comparison-string production).
     Requires(num_values >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -101,26 +99,20 @@
     Ensures(ToSeq(Result()) == slots_sql(num_values))
     # post-conditions-end
     # impl-start
+    # UNGROUNDED-ORACLE ECHO: wraps each slot with a DIFFERENT (MariaDB-branch)
+    # wrapper JSON_UNQUOTE(JSON_EXTRACT(%s, '$')) rather than the sqlite/mysql
+    # wrapped_slot the spec pins. A plausible-but-wrong backend echo.
     result = []  # type: List[int]
     i = num_values
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= num_values)
-        # `result` already holds the expansion of the trailing `num_values - i`
-        # slots (built back-to-front so the front-recursive slots_sql unfolds
-        # one slot per step).
-        Invariant(ToSeq(result) == slots_sql(num_values - i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         if i == num_values:
-            # Last slot: no trailing separator.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41]
+            result = [74, 83, 79, 78, 95, 85, 78, 81, 85, 79, 84, 69, 40, 74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41, 41]
         else:
-            # Earlier slot: wrapped slot, then separator, then the rest.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
+            result = [74, 83, 79, 78, 95, 85, 78, 81, 85, 79, 84, 69, 40, 74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41, 41, 44, 32] + result
         i = i - 1
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
     # `num_values` is the count of right-hand-side values (>= 1: an empty
     # membership set never reaches comparison-string production).
     Requires(num_values >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -101,26 +99,17 @@
     Ensures(ToSeq(Result()) == slots_sql(num_values))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = num_values
-    while i > 0:
+    # Correct alternative #2: emit the first slot, then in the loop append
+    # separator+slot for each remaining value (forward, sep-before).
+    result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41]  # type: List[int]
+    i = 1
+    while i < num_values:
         # invariants-start
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= num_values)
-        # `result` already holds the expansion of the trailing `num_values - i`
-        # slots (built back-to-front so the front-recursive slots_sql unfolds
-        # one slot per step).
-        Invariant(ToSeq(result) == slots_sql(num_values - i))
-        Invariant(MustTerminate(i + 1))
+        Invariant(1 <= i and i <= num_values)
+        Invariant(ToSeq(result) == slots_sql(i))
         # invariants-end
-        if i == num_values:
-            # Last slot: no trailing separator.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41]
-        else:
-            # Earlier slot: wrapped slot, then separator, then the rest.
-            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
-                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
-        i = i - 1
+        result = result + [44, 32, 74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84, 40, 37, 115, 44, 32, 39, 36, 39, 41]
+        i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13346.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test against a stored-collection key must, on the relevant
  backends, compare each candidate value through the SAME per-value form that a
  direct equality test against the key already uses. The comparison string
  produced for a membership test of N candidate values is the comma-space
  joined list of N per-value comparison slots, and every slot must be the
  per-value comparison form (an opaque backend-specific token that surrounds
  the bind placeholder, given below as a code-point literal) — NOT the bare
  bind placeholder.

  The desired behaviour, derived from the problem statement (a single-element
  membership test `key__in=[v]` must select exactly the rows that the direct
  test `key=v` selects, rather than a disjoint or empty set), is: the produced
  comparison string is the per-slot expansion in which every one of the N
  candidate slots is the per-value comparison form, the slots joined by the
  comma-space separator, with no slot left as the bare placeholder. The bind
  parameters themselves are unchanged.

The comparison string is modelled as `List[int]` of code points (Nagini bans
`str` indexing); the specification is carried by `PSeq[int]`. The right-hand
side is modelled as a list of value slots; the per-slot form is spelled out
deeply as a front-recursive fold (`slots_sql`). The unchanged base-class
placeholder production (one bare placeholder per value, comma-joined) is the
type-refinement boundary documented in mapping.md; the per-value comparison
form is a constant backend token spelled out below as an opaque code-point
literal, not a callee the proof axiomatizes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The base-class
#  placeholder string -- one bind placeholder per value, comma-joined -- is a
#  type refinement documented in mapping.md, NOT an axiom. The per-value
#  comparison form is a constant backend token spelled out below as an opaque
#  code-point literal, not a function whose behaviour the proof must
#  over-approximate.)
# axioms-end


# pure-start
@Pure
def sep() -> PSeq[int]:
    # ', '  -- the separator between comparison slots
    return PSeq(44, 32)


@Pure
def wrapped_slot() -> PSeq[int]:
    # The per-value comparison form: an opaque backend constant (constant code
    # points) that every slot must take. Its content is load-bearing for the
    # proof; its textual meaning is deliberately not narrated here.
    return PSeq(74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                40, 37, 115, 44, 32, 39, 36, 39, 41)


@Pure
def bare_slot() -> PSeq[int]:
    # The bare bind placeholder -- a slot in the un-formed shape. A slot left in
    # this shape is exactly the slot that the desired behaviour forbids.
    return PSeq(37, 115)


@Pure
def slots_sql(n: int) -> PSeq[int]:
    """The comparison string for `n` value slots: the per-value comparison form
    (`wrapped_slot`) repeated `n` times, joined by `sep` (', '). Front-recursive
    so a single unfold is available to callers per step.

    n == 0 -> empty; n == 1 -> one formed slot; n >= 2 -> formed slot then
    separator then the rest.
    """
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    if n == 1:
        return wrapped_slot()
    return wrapped_slot() + sep() + slots_sql(n - 1)
# pure-end


def process_membership_rhs(num_values: int) -> List[int]:
    # pre-conditions-start
    # `num_values` is the count of right-hand-side values (>= 1: an empty
    # membership set never reaches comparison-string production).
    Requires(num_values >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The comparison string is the per-slot expansion in which EVERY one of the
    # num_values slots is the per-value comparison form (`wrapped_slot`), joined
    # by the comma-space separator -- no slot is left as a bare bind placeholder.
    Ensures(ToSeq(Result()) == slots_sql(num_values))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        # `result` already holds the expansion of the trailing `num_values - i`
        # slots (built back-to-front so the front-recursive slots_sql unfolds
        # one slot per step).
        Invariant(ToSeq(result) == slots_sql(num_values - i))
        # invariants-end
        if i == num_values:
            # Last slot: no trailing separator.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41]
        else:
            # Earlier slot: wrapped slot, then separator, then the rest.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. All commands run from there.

SPEC SHAPE: The frozen postcondition `Ensures(ToSeq(Result()) == slots_sql(num_values))` (outside impl region, byte-identical across attacks) TOTALLY pins the output over the entire domain num_values>=1. slots_sql / wrapped_slot / sep are frozen @Pure functions. Any verifying impl therefore must produce EXACTLY slots_sql(num_values) = the ', '-joined sequence of n copies of "JSON_EXTRACT(%s, '$')" -- byte-identical to the gold sqlite/mysql branch. This is a complete functional spec, so verify==correct on this branch.

BASELINES: positive_control (verbatim model.py) VERIFIES via `bash scripts/nagini_verify.sh` -> 'Verification successful' 17.38s. atk_prepatch (=model_prepatch.py, bare `%s` per slot) `weakness` -> NOT-A-COUNTEREXAMPLE (does not verify) => prepatch bug reproduced/sensed. Gold patch.diff run through official harness `run_resolve` -> RESOLVED=True COMPLETED=True, FAIL_TO_PASS test_key_in+test_key_iregex both pass (infra confirmed working).

ATTACKS (all same-spec confirmed; command: `python -m swebench_unified.adversary weakness nagini django__django-13346 <path>`, run concurrently <=3/batch):
- atk_1.py (control-flow-effect: forward build with Invariant ToSeq(result)==slots_sql(i)) -> NOT-A-COUNTEREXAMPLE (verify failed). Proof-difficulty artifact: forward-append against the front-recursive slots_sql fold is hard for Nagini; NOT a spec weakness.
- atk_2.py (correct-but-different: explicit n==1 base case returning wrapped_slot, then reference back-to-front loop) -> CANDIDATE (shares spec AND verifies, 18.9s). MATERIALIZED faithful patch (atk_2_faithful.diff: gold KeyTransformIn.process_rhs with the sqlite/mysql func line rewritten to a behaviorally-identical ternary `("JSON_EXTRACT(%s, '$')",) if len(rhs_params)==1 else (...)*len(rhs_params)`, identical hunk structure to gold) and RAN through official harness `run_resolve('django__django-13346', patch, timeout=1800)` -> RESOLVED=True, COMPLETED=True, patch_successfully_applied=True, FAIL_TO_PASS test_key_in+test_key_iregex both SUCCESS. => candidate corresponds to a RESOLVING patch; does NOT break the spec.
  (First two harness attempts returned COMPLETED=False: attempt 1 = image not yet built locally (infra, resolved once gold run pulled/built the image); attempt 2 = a hand-authoring error in my initial faithful patch -- I split gold's single func= line into a 5-line if/else but left the hunk header at +378,30, producing `malformed patch at line 35` per run_instance.log. Corrected to a single-line ternary matching gold's 24-added-line hunk; re-ran -> RESOLVED. The malformed-patch failure was MY diff-arithmetic error, NOT a faithful-patch-fails-to-resolve result -- diagnosed from run_instance.log, not assumed.)
- atk_3.py (boundary/off-by-one: `while i > 1`, emits num_values-1 slots) -> NOT-A-COUNTEREXAMPLE (rejected). Good.
- atk_4.py (partial-domain: n==1 wrapped, n>=2 falls back to bare `%s` placeholder = prepatch bug) -> NOT-A-COUNTEREXAMPLE (rejected). Good.
- atk_5.py (control-flow-effect: appends spurious trailing sep when num_values even) -> NOT-A-COUNTEREXAMPLE (rejected). Good.
- atk_6.py (ungrounded-oracle echo: wraps with the MariaDB-branch JSON_UNQUOTE(JSON_EXTRACT(%s,'$')) instead of the spec's sqlite wrapped_slot) -> NOT-A-COUNTEREXAMPLE (rejected). Good -- the spec pins the sqlite/mysql wrapper exactly and rejects the wrong backend token.
- atk_7.py (correct-but-different #2: emit first slot then forward-append sep+slot; Invariant slots_sql(i)) -> NOT-A-COUNTEREXAMPLE (verify failed). Proof-difficulty artifact (same front-recursive-fold vs forward-append mismatch), NOT a spec weakness.

G-AX (A-reference soundness): `python axiom_check.py` -> exit 0, 'slots_sql deep model == real KeyTransformIn.process_rhs slot-wrapping over 8 boundary + 5000 fuzz value-counts; pre-fix bare-slot string differs for every count (bug sensed).'

REFINEMENT.MD A-LEG AUDIT (focus of this pass): every leg is R / A-reference / I -- NO kind-3, NO consumed axiom. A1(num_values<-len(rhs_params))=R, justified >=1 via In.process_rhs EmptyResultSet on empty rhs. A2(base placeholder parens/comma structure)=R, unchanged base-class boundary (matches gold: super().process_rhs untouched). A3(slots_sql==`rhs % func`, sqlite branch)=A-reference, deep model validated by axiom_check.py; correspondence to real `("JSON_EXTRACT(%s, '$')",)*len(rhs_params)` sqlite/mysql branch confirmed against gold patch.diff line 27. A4(result List[int]<-wrapped rhs str; params pass through)=R. Section B: sole opaque callee is super().process_rhs = unchanged R-boundary, correctly NOT axiomatized. mapping.md flag/branch note correct: tested FAIL_TO_PASS test_key_in runs on SQLite, the modeled branch; PostgreSQL native-json path short-circuits and is out of scope; MariaDB/Oracle branches off the tested path (atk_6 confirms the spec rejects the MariaDB token, so no accidental over-admission).

CONCLUSION: The one same-spec verifying wrong-shaped candidate (atk_2) materializes to a RESOLVING faithful patch; all 4 genuinely-wrong impls (boundary/partial-domain/control-flow-effect/ungrounded-oracle-echo) fail to verify; prepatch bug sensed; positive control verifies; gold resolves; G-AX passes; refinement.md A-legs correspond to the real callees with no kind-3. verify => correct holds on the tested SQLite branch. No verify-and-not-resolve witness exists. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13346.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test against a stored-collection key must, on the relevant
  backends, compare each candidate value through the SAME per-value form that a
  direct equality test against the key already uses. The comparison string
  produced for a membership test of N candidate values is the comma-space
  joined list of N per-value comparison slots, and every slot must be the
  per-value comparison form (an opaque backend-specific token that surrounds
  the bind placeholder, given below as a code-point literal) — NOT the bare
  bind placeholder.

  The desired behaviour, derived from the problem statement (a single-element
  membership test `key__in=[v]` must select exactly the rows that the direct
  test `key=v` selects, rather than a disjoint or empty set), is: the produced
  comparison string is the per-slot expansion in which every one of the N
  candidate slots is the per-value comparison form, the slots joined by the
  comma-space separator, with no slot left as the bare placeholder. The bind
  parameters themselves are unchanged.

The comparison string is modelled as `List[int]` of code points (Nagini bans
`str` indexing); the specification is carried by `PSeq[int]`. The right-hand
side is modelled as a list of value slots; the per-slot form is spelled out
deeply as a front-recursive fold (`slots_sql`). The unchanged base-class
placeholder production (one bare placeholder per value, comma-joined) is the
type-refinement boundary documented in mapping.md; the per-value comparison
form is a constant backend token spelled out below as an opaque code-point
literal, not a callee the proof axiomatizes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The base-class
#  placeholder string -- one bind placeholder per value, comma-joined -- is a
#  type refinement documented in mapping.md, NOT an axiom. The per-value
#  comparison form is a constant backend token spelled out below as an opaque
#  code-point literal, not a function whose behaviour the proof must
#  over-approximate.)
# axioms-end


# pure-start
@Pure
def sep() -> PSeq[int]:
    # ', '  -- the separator between comparison slots
    return PSeq(44, 32)


@Pure
def wrapped_slot() -> PSeq[int]:
    # The per-value comparison form: an opaque backend constant (constant code
    # points) that every slot must take. Its content is load-bearing for the
    # proof; its textual meaning is deliberately not narrated here.
    return PSeq(74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                40, 37, 115, 44, 32, 39, 36, 39, 41)


@Pure
def bare_slot() -> PSeq[int]:
    # The bare bind placeholder -- a slot in the un-formed shape. A slot left in
    # this shape is exactly the slot that the desired behaviour forbids.
    return PSeq(37, 115)


@Pure
def slots_sql(n: int) -> PSeq[int]:
    """The comparison string for `n` value slots: the per-value comparison form
    (`wrapped_slot`) repeated `n` times, joined by `sep` (', '). Front-recursive
    so a single unfold is available to callers per step.

    n == 0 -> empty; n == 1 -> one formed slot; n >= 2 -> formed slot then
    separator then the rest.
    """
    Requires(n >= 0)
    if n == 0:
        return PSeq(0).take(0)
    if n == 1:
        return wrapped_slot()
    return wrapped_slot() + sep() + slots_sql(n - 1)
# pure-end


def process_membership_rhs(num_values: int) -> List[int]:
    # pre-conditions-start
    # `num_values` is the count of right-hand-side values (>= 1: an empty
    # membership set never reaches comparison-string production).
    Requires(num_values >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The comparison string is the per-slot expansion in which EVERY one of the
    # num_values slots is the per-value comparison form (`wrapped_slot`), joined
    # by the comma-space separator -- no slot is left as a bare bind placeholder.
    Ensures(ToSeq(Result()) == slots_sql(num_values))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= num_values)
        # `result` already holds the expansion of the trailing `num_values - i`
        # slots (built back-to-front so the front-recursive slots_sql unfolds
        # one slot per step).
        Invariant(ToSeq(result) == slots_sql(num_values - i))
        # invariants-end
        if i == num_values:
            # Last slot: no trailing separator.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41]
        else:
            # Earlier slot: wrapped slot, then separator, then the rest.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. All commands run from there.

SPEC SHAPE: The frozen postcondition `Ensures(ToSeq(Result()) == slots_sql(num_values))` (outside impl region, byte-identical across attacks) TOTALLY pins the output over the entire domain num_values>=1. slots_sql / wrapped_slot / sep are frozen @Pure functions. Any verifying impl therefore must produce EXACTLY slots_sql(num_values) = the ', '-joined sequence of n copies of "JSON_EXTRACT(%s, '$')" -- byte-identical to the gold sqlite/mysql branch. This is a complete functional spec, so verify==correct on this branch.

BASELINES: positive_control (verbatim model.py) VERIFIES via `bash scripts/nagini_verify.sh` -> 'Verification successful' 17.38s. atk_prepatch (=model_prepatch.py, bare `%s` per slot) `weakness` -> NOT-A-COUNTEREXAMPLE (does not verify) => prepatch bug reproduced/sensed. Gold patch.diff run through official harness `run_resolve` -> RESOLVED=True COMPLETED=True, FAIL_TO_PASS test_key_in+test_key_iregex both pass (infra confirmed working).

ATTACKS (all same-spec confirmed; command: `python -m swebench_unified.adversary weakness nagini django__django-13346 <path>`, run concurrently <=3/batch):
- atk_1.py (control-flow-effect: forward build with Invariant ToSeq(result)==slots_sql(i)) -> NOT-A-COUNTEREXAMPLE (verify failed). Proof-difficulty artifact: forward-append against the front-recursive slots_sql fold is hard for Nagini; NOT a spec weakness.
- atk_2.py (correct-but-different: explicit n==1 base case returning wrapped_slot, then reference back-to-front loop) -> CANDIDATE (shares spec AND verifies, 18.9s). MATERIALIZED faithful patch (atk_2_faithful.diff: gold KeyTransformIn.process_rhs with the sqlite/mysql func line rewritten to a behaviorally-identical ternary `("JSON_EXTRACT(%s, '$')",) if len(rhs_params)==1 else (...)*len(rhs_params)`, identical hunk structure to gold) and RAN through official harness `run_resolve('django__django-13346', patch, timeout=1800)` -> RESOLVED=True, COMPLETED=True, patch_successfully_applied=True, FAIL_TO_PASS test_key_in+test_key_iregex both SUCCESS. => candidate corresponds to a RESOLVING patch; does NOT break the spec.
  (First two harness attempts returned COMPLETED=False: attempt 1 = image not yet built locally (infra, resolved once gold run pulled/built the image); attempt 2 = a hand-authoring error in my initial faithful patch -- I split gold's single func= line into a 5-line if/else but left the hunk header at +378,30, producing `malformed patch at line 35` per run_instance.log. Corrected to a single-line ternary matching gold's 24-added-line hunk; re-ran -> RESOLVED. The malformed-patch failure was MY diff-arithmetic error, NOT a faithful-patch-fails-to-resolve result -- diagnosed from run_instance.log, not assumed.)
- atk_3.py (boundary/off-by-one: `while i > 1`, emits num_values-1 slots) -> NOT-A-COUNTEREXAMPLE (rejected). Good.
- atk_4.py (partial-domain: n==1 wrapped, n>=2 falls back to bare `%s` placeholder = prepatch bug) -> NOT-A-COUNTEREXAMPLE (rejected). Good.
- atk_5.py (control-flow-effect: appends spurious trailing sep when num_values even) -> NOT-A-COUNTEREXAMPLE (rejected). Good.
- atk_6.py (ungrounded-oracle echo: wraps with the MariaDB-branch JSON_UNQUOTE(JSON_EXTRACT(%s,'$')) instead of the spec's sqlite wrapped_slot) -> NOT-A-COUNTEREXAMPLE (rejected). Good -- the spec pins the sqlite/mysql wrapper exactly and rejects the wrong backend token.
- atk_7.py (correct-but-different #2: emit first slot then forward-append sep+slot; Invariant slots_sql(i)) -> NOT-A-COUNTEREXAMPLE (verify failed). Proof-difficulty artifact (same front-recursive-fold vs forward-append mismatch), NOT a spec weakness.

G-AX (A-reference soundness): `python axiom_check.py` -> exit 0, 'slots_sql deep model == real KeyTransformIn.process_rhs slot-wrapping over 8 boundary + 5000 fuzz value-counts; pre-fix bare-slot string differs for every count (bug sensed).'

REFINEMENT.MD A-LEG AUDIT (focus of this pass): every leg is R / A-reference / I -- NO kind-3, NO consumed axiom. A1(num_values<-len(rhs_params))=R, justified >=1 via In.process_rhs EmptyResultSet on empty rhs. A2(base placeholder parens/comma structure)=R, unchanged base-class boundary (matches gold: super().process_rhs untouched). A3(slots_sql==`rhs % func`, sqlite branch)=A-reference, deep model validated by axiom_check.py; correspondence to real `("JSON_EXTRACT(%s, '$')",)*len(rhs_params)` sqlite/mysql branch confirmed against gold patch.diff line 27. A4(result List[int]<-wrapped rhs str; params pass through)=R. Section B: sole opaque callee is super().process_rhs = unchanged R-boundary, correctly NOT axiomatized. mapping.md flag/branch note correct: tested FAIL_TO_PASS test_key_in runs on SQLite, the modeled branch; PostgreSQL native-json path short-circuits and is out of scope; MariaDB/Oracle branches off the tested path (atk_6 confirms the spec rejects the MariaDB token, so no accidental over-admission).

CONCLUSION: The one same-spec verifying wrong-shaped candidate (atk_2) materializes to a RESOLVING faithful patch; all 4 genuinely-wrong impls (boundary/partial-domain/control-flow-effect/ungrounded-oracle-echo) fail to verify; prepatch bug sensed; positive control verifies; gold resolves; G-AX passes; refinement.md A-legs correspond to the real callees with no kind-3. verify => correct holds on the tested SQLite branch. No verify-and-not-resolve witness exists. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on the nagini spec for django__django-13346. The modeled function process_membership_rhs(num_values) is checked against the REAL patched callee KeyTransformIn.process_rhs (django/db/models/fields/json.py) at base_commit 9c92924.

Method: created (base worktree + patch.diff applied cleanly), resolved the actual KeyTransformIn lookup class through the ORM (data__key__in=[...] on a JSONField, SQLite non-native-JSON backend = the tested branch), and ran a differential comparison of the shadow impl region (contracts stripped, byte-identical to model.py) vs. the real process_rhs inner content (outer parens stripped per the documented R-refinement boundary; bind params unchanged and excluded). 20,036 inputs (boundary counts 1,2,3,4,5,8,10,16,32,64,100,200 across int/str/mixed value types + 20k fuzz draws, seed 13346): 0 disagreements.

The model produces, for n slots, the code points of 'JSON_EXTRACT(%s, \'$\'), ...' (n copies, ', '-joined) which equals rhs % (("JSON_EXTRACT(%s, '$')",)*n) inner content exactly. axiom_check.py passes standalone (exit 0), confirming slots_sql(n) == real %-substitution over boundary+5000 fuzz and that the pre-fix bare-slot ('%s') differs for every n>=1 (bug is sensed, so the spec is not too weak either).

Precondition num_values>=1 is sound: In.process_rhs raises EmptyResultSet for empty rhs, so comparison-string production is only reached with >=1 value. The SQLite/MySQL branch scoping matches the FAIL_TO_PASS test_key_in path; the untested MariaDB/Oracle/postgres branches are correctly out of the modeled domain. No input found where the modeled function disagrees with the real callee within its domain. Spec is FAITHFUL (not too strong, does not drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view = spec_view(model.py) (mapping.md/refinement.md/patch.diff are auditor-only and excluded). Gold edit beyond problem_statement: new KeyTransformIn(lookups.In) in django/db/models/fields/json.py overriding process_rhs to wrap each '%s' with JSON_EXTRACT(%s, '$') on sqlite/mysql, registered via KeyTransform.register_lookup. The problem_statement only states that __in on key transforms misbehaves (single-element case) on MySQL/Oracle/SQLite; it never names JSON_EXTRACT, the file, or any symbol.

Screen of the spec view:
- No diff markers, no patched file path (django/db/models/fields/json.py) or dotted module path present.
- No patched repo symbols (KeyTransformIn, process_rhs, In, register_lookup) appear; spec identifiers are generic and non-localizing (process_membership_rhs, slots_sql, wrapped_slot, bare_slot, sep).
- No bug/fix/previously/incorrect narration; comments frame everything as 'desired behaviour', not as an edit.
- The discriminating gold string JSON_EXTRACT(%s, '$') appears only as an opaque code-point literal PSeq(74,83,79,78,95,69,88,84,82,65,67,84,40,37,115,44,32,39,36,39,41), explicitly declared 'an opaque backend constant … its textual meaning deliberately not narrated.' Encoding the required output behavior is the legitimate function of a deep A-reference spec (needed for verify=>resolve); it is not edit-localization and does not let a solver reconstruct the repo plumbing (which class to subclass, where to register).

Thus the spec view reveals no repo localization, no readable gold-diff line, no patched file/symbol, and no bug/fix narration beyond the public problem statement. No RELAXED_LEAKAGE.md / relaxed_leakage flag present, and none is needed. Recorded G-LEAK status is 'pass' (spec view clean), which is correct on the merits, not merely a lexical artifact of the code-point obfuscation.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
