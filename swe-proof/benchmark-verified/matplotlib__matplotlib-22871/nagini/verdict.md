# P2 adversarial audit — matplotlib__matplotlib-22871

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,8 +152,6 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
     if col_varies(c5):
         return TickLevel(5, 1)
     if col_varies(c4):
@@ -169,15 +161,8 @@
     if col_varies(c2):
         return TickLevel(2, 1)
     if col_varies(c1):
-        if col_has_one(c1):
-            return TickLevel(1, 0)
-        return TickLevel(1, 1)
+        return TickLevel(1, 0)
     if col_varies(c0):
-        if col_has_one(c0):
-            return TickLevel(0, 0)
-        return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
+        return TickLevel(0, 0)
     return TickLevel(5, 1)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,8 +152,6 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
     if col_varies(c5):
         return TickLevel(5, 1)
     if col_varies(c4):
@@ -169,15 +161,12 @@
     if col_varies(c2):
         return TickLevel(2, 1)
     if col_varies(c1):
-        if col_has_one(c1):
+        if col_has_one(c0):
             return TickLevel(1, 0)
         return TickLevel(1, 1)
     if col_varies(c0):
         if col_has_one(c0):
             return TickLevel(0, 0)
         return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
     return TickLevel(5, 1)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,8 +152,6 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
     if col_varies(c5):
         return TickLevel(5, 1)
     if col_varies(c4):
@@ -169,15 +161,8 @@
     if col_varies(c2):
         return TickLevel(2, 1)
     if col_varies(c1):
-        if col_has_one(c1):
-            return TickLevel(1, 0)
         return TickLevel(1, 1)
     if col_varies(c0):
-        if col_has_one(c0):
-            return TickLevel(0, 0)
         return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
     return TickLevel(5, 1)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,26 +152,21 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
-    if col_varies(c5):
-        return TickLevel(5, 1)
-    if col_varies(c4):
-        return TickLevel(4, 1)
-    if col_varies(c3):
-        return TickLevel(3, 1)
-    if col_varies(c2):
-        return TickLevel(2, 1)
+    if col_varies(c0):
+        if col_has_one(c0):
+            return TickLevel(0, 0)
+        return TickLevel(0, 1)
     if col_varies(c1):
         if col_has_one(c1):
             return TickLevel(1, 0)
         return TickLevel(1, 1)
-    if col_varies(c0):
-        if col_has_one(c0):
-            return TickLevel(0, 0)
-        return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
+    if col_varies(c2):
+        return TickLevel(2, 1)
+    if col_varies(c3):
+        return TickLevel(3, 1)
+    if col_varies(c4):
+        return TickLevel(4, 1)
+    if col_varies(c5):
+        return TickLevel(5, 1)
     return TickLevel(5, 1)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,12 +152,10 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
     if col_varies(c5):
         return TickLevel(5, 1)
     if col_varies(c4):
-        return TickLevel(4, 1)
+        return TickLevel(3, 1)
     if col_varies(c3):
         return TickLevel(3, 1)
     if col_varies(c2):
@@ -176,8 +168,5 @@
         if col_has_one(c0):
             return TickLevel(0, 0)
         return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
     return TickLevel(5, 1)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,8 +152,6 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
     if col_varies(c5):
         return TickLevel(5, 1)
     if col_varies(c4):
@@ -176,8 +168,5 @@
         if col_has_one(c0):
             return TickLevel(0, 0)
         return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
-    return TickLevel(5, 1)
+    return TickLevel(0, 1)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,26 +152,5 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
-    if col_varies(c5):
-        return TickLevel(5, 1)
-    if col_varies(c4):
-        return TickLevel(4, 1)
-    if col_varies(c3):
-        return TickLevel(3, 1)
-    if col_varies(c2):
-        return TickLevel(2, 1)
-    if col_varies(c1):
-        if col_has_one(c1):
-            return TickLevel(1, 0)
-        return TickLevel(1, 1)
-    if col_varies(c0):
-        if col_has_one(c0):
-            return TickLevel(0, 0)
-        return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
     return TickLevel(5, 1)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,10 +78,6 @@
     def __init__(self, level: int, show_offset: int) -> None:
         Requires(0 <= level and level <= 5)
         Requires(show_offset == 0 or show_offset == 1)
-        # Terminates: two field assignments, straight-line, no loop and no
-        # further call. Level 1 leaves room strictly below determine_level's
-        # level 6, which constructs a TickLevel on every return path.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.level) and Acc(self.show_offset))
         Ensures(self.level == level and self.show_offset == show_offset)
         self.level = level          # type: int
@@ -103,7 +98,6 @@
     Requires(len(c0) >= 1)
     Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
     Requires(len(c4) == len(c0) and len(c5) == len(c0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(c0), 1 / 2))
@@ -158,26 +152,20 @@
                     Result().show_offset == 1))
     # post-conditions-end
     # impl-start
-    # Default: the offset is shown. The descending scan over the six levels is
-    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
     if col_varies(c5):
         return TickLevel(5, 1)
-    if col_varies(c4):
+    elif col_varies(c4):
         return TickLevel(4, 1)
-    if col_varies(c3):
+    elif col_varies(c3):
         return TickLevel(3, 1)
-    if col_varies(c2):
+    elif col_varies(c2):
         return TickLevel(2, 1)
-    if col_varies(c1):
-        if col_has_one(c1):
-            return TickLevel(1, 0)
-        return TickLevel(1, 1)
-    if col_varies(c0):
-        if col_has_one(c0):
-            return TickLevel(0, 0)
-        return TickLevel(0, 1)
-    # No column varies: every tick is identical down to the second. The scan
-    # reaches the coarsest level with all entries equal and resets to the finest
-    # level; the offset keeps its default (shown).
-    return TickLevel(5, 1)
+    elif col_varies(c1):
+        so1 = 0 if col_has_one(c1) else 1
+        return TickLevel(1, so1)
+    elif col_varies(c0):
+        so0 = 0 if col_has_one(c0) else 1
+        return TickLevel(0, so0)
+    else:
+        return TickLevel(5, 1)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-22871.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A sequence of tick instants is described by six parallel integer columns,
  one per calendar component, ordered from coarsest to finest:

      column 0 = year, 1 = month, 2 = day, 3 = hour, 4 = minute, 5 = second.

  All columns have the same length N (>= 1), one entry per tick.

  Two derived quantities are computed:

    * the labelling level L -- the finest component that the ticks share, found
      by scanning the columns from finest (5) to coarsest (0) and selecting the
      FIRST column (i.e. the highest-indexed one) whose entries are NOT all
      equal across the ticks. When every column is constant across the ticks
      (all ticks identical down to the second), L is the finest level, 5.

    * whether a separate summary label (the "offset") is shown. By default it
      is shown. It is suppressed ONLY when the labelling level is a coarse one
      (year or month, i.e. L < 2) AND the value 1 occurs somewhere in that
      labelling column. Otherwise -- in particular at a coarse labelling level
      whose column does NOT contain the value 1 -- the offset stays shown.

  The reported result carries the labelling level and a 0/1 flag for whether the
  offset is shown.

Modelling choices (Nagini fragment):
  * Each tick column is a ``List[int]`` (the integer calendar component).
    `col_varies` and `col_has_one` are structural predicates over a column --
    "the column is not constant" and "the value 1 is present in the column" --
    validated against the real column reductions out-of-band by axiom_check.py
    (G-AX); they are not consumed as axioms.
  * The six-iteration descending scan over the literal range of levels is
    transcribed as a straight-line cascade (the trip count is a compile-time
    constant; no data-dependent loop bound).
  * The result is returned as a small object with the two observed fields.

No string indexing or library import beyond typing / nagini_contracts is used.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The two structural predicates the behaviour composes --
# "the column is not constant" and "the value 1 is present in the column" --
# are modelled DEEPLY by `col_varies` / `col_has_one` below. They are not opaque
# callees the proof stands in for; their equality to the real column reductions
# is validated out-of-band by axiom_check.py (G-AX) as A-reference deep models.
# axioms-end


# pure-start
@Pure
def col_varies(col: List[int]) -> bool:
    """True iff the column is not constant across the ticks, i.e. two ticks
    disagree on this calendar component."""
    Requires(Acc(list_pred(col), 1 / 4))
    return Exists(int, lambda i: Exists(int, lambda j: (
        0 <= i and i < j and j < len(col) and col[i] != col[j])))


@Pure
def col_has_one(col: List[int]) -> bool:
    """True iff the value 1 occurs somewhere in the column."""
    Requires(Acc(list_pred(col), 1 / 4))
    return Exists(int, lambda i: (0 <= i and i < len(col) and col[i] == 1))
# pure-end


class TickLevel:
    """The two observed outputs of the labelling-level computation: the chosen
    labelling level and a 0/1 flag for whether the summary offset is shown."""

    def __init__(self, level: int, show_offset: int) -> None:
        Requires(0 <= level and level <= 5)
        Requires(show_offset == 0 or show_offset == 1)
        Ensures(Acc(self.level) and Acc(self.show_offset))
        Ensures(self.level == level and self.show_offset == show_offset)
        self.level = level          # type: int
        self.show_offset = show_offset  # type: int


def determine_level(c0: List[int], c1: List[int], c2: List[int],
                    c3: List[int], c4: List[int], c5: List[int]) -> TickLevel:
    # pre-conditions-start
    # The six tick columns are READ-ONLY (directive 5: fractional permission).
    Requires(Acc(list_pred(c0), 1 / 2))
    Requires(Acc(list_pred(c1), 1 / 2))
    Requires(Acc(list_pred(c2), 1 / 2))
    Requires(Acc(list_pred(c3), 1 / 2))
    Requires(Acc(list_pred(c4), 1 / 2))
    Requires(Acc(list_pred(c5), 1 / 2))
    # There is at least one tick, and all columns share the same length.
    Requires(len(c0) >= 1)
    Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
    Requires(len(c4) == len(c0) and len(c5) == len(c0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(c0), 1 / 2))
    Ensures(Acc(list_pred(c1), 1 / 2))
    Ensures(Acc(list_pred(c2), 1 / 2))
    Ensures(Acc(list_pred(c3), 1 / 2))
    Ensures(Acc(list_pred(c4), 1 / 2))
    Ensures(Acc(list_pred(c5), 1 / 2))
    Ensures(Acc(Result().level) and Acc(Result().show_offset))
    Ensures(0 <= Result().level and Result().level <= 5)
    Ensures(Result().show_offset == 0 or Result().show_offset == 1)
    # The labelling level is the highest-indexed column that varies, found by
    # the finest-to-coarsest scan; if no column varies it is the finest, 5.
    Ensures(Implies(col_varies(c5), Result().level == 5))
    Ensures(Implies(not col_varies(c5) and col_varies(c4),
                    Result().level == 4))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4) and col_varies(c3),
                    Result().level == 3))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and col_varies(c2),
                    Result().level == 2))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and col_varies(c1), Result().level == 1))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and col_varies(c0),
                    Result().level == 0))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and not col_varies(c0),
                    Result().level == 5))
    # The offset is hidden (flag == 0) EXACTLY when the labelling level is a
    # coarse one (year or month) AND that column carries the value 1; otherwise
    # the offset stays shown (flag == 1), including at a coarse labelling level
    # whose column does not contain the value 1.
    Ensures(Implies(col_varies(c1) and not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2),
                    (Result().show_offset == 0) == col_has_one(c1)))
    Ensures(Implies(col_varies(c0) and not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1),
                    (Result().show_offset == 0) == col_has_one(c0)))
    # When the labelling level is a fine one (>= 2), or when no column varies,
    # the offset is always shown.
    Ensures(Implies(col_varies(c5) or col_varies(c4) or col_varies(c3)
                    or col_varies(c2),
                    Result().show_offset == 1))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and not col_varies(c0),
                    Result().show_offset == 1))
    # post-conditions-end
    # impl-start
    # Default: the offset is shown. The descending scan over the six levels is
    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
    if col_varies(c5):
        return TickLevel(5, 1)
    if col_varies(c4):
        return TickLevel(4, 1)
    if col_varies(c3):
        return TickLevel(3, 1)
    if col_varies(c2):
        return TickLevel(2, 1)
    if col_varies(c1):
        if col_has_one(c1):
            return TickLevel(1, 0)
        return TickLevel(1, 1)
    if col_varies(c0):
        if col_has_one(c0):
            return TickLevel(0, 0)
        return TickLevel(0, 1)
    # No column varies: every tick is identical down to the second. The scan
    # reaches the coarsest level with all entries equal and resets to the finest
    # level; the offset keeps its default (shown).
    return TickLevel(5, 1)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for matplotlib__matplotlib-22871 (nagini). All 8 attacks were built by copying model.py and editing ONLY the impl region (spec/axioms/@Pure/Requires/Ensures byte-identical — verified with diff on the pre-impl-start region for every file).

Positive control: pos_control.py = model.py verbatim => CANDIDATE (shares spec AND verifies, 21.6s); it is the gold and resolves (baseline sanity).

### WRONG-IMPL ATTACKS (all correctly REJECTED, exit 2 — spec sensed the defect):
- atk_1 PREPATCH BUG: at level<2 return show_offset=0 unconditionally (no col_has_one check). NOT-A-COUNTEREXAMPLE — fails the month-level postcondition (Result().show_offset==0)==col_has_one(c1). Prepatch reproduced (matches model_prepatch.py; G-DIFF live).
- atk_2 WRONG COLUMN: at level 1 test col_has_one(c0) instead of col_has_one(c1). REJECTED.
- atk_3 CONTROL-FLOW-EFFECT: drop suppression entirely, always show_offset=1 at coarse levels. REJECTED.
- atk_4 CONTROL-FLOW REVERSAL: scan coarse->fine (pick lowest varying level). REJECTED (wrong level selection).
- atk_5 BOUNDARY/OFF-BY-ONE: c4 varies -> return level 3. REJECTED.
- atk_6 BOUNDARY: no-column-varies -> return TickLevel(0,1) instead of (5,1). REJECTED.
- atk_7 UNGROUNDED-ORACLE ECHO: always return TickLevel(5,1). REJECTED.

CANDIDATE (shares spec AND verifies) requiring resolve:
- atk_8 EQUIVALENT RESTRUCTURE: elif-chain with local show_offset expression (0 if col_has_one else 1), semantically identical to gold. Weakness => CANDIDATE (verifies, 18.5s). MANDATORY resolve: materialized faithful refined patch atk_8.patch (turns `if level<2:` into `if level<2 and bool(np.any(unique==1)):`, hoists unique — the gold change) and RAN it through the official harness: `run_resolve('matplotlib__matplotlib-22871', atk_8.patch, timeout=1800)` => completed=True, resolved=True, note='resolved'. The only verifying candidate RESOLVES, so no verify⇏correct witness exists.

REFINEMENT.MD AUDIT: legs A1(R), A2(A-reference col_varies), A3(A-reference col_has_one), A4(I unrolled constant-bound loop), A5(I + A-reference). No kind-3 (unexpressible-changed-op) legs; meta.json axioms=[] confirms NO consumed @ContractOnly axioms. A-legs correspondence holds: col_varies(col) ⇔ ∃i<j.col[i]≠col[j] ⇔ len(np.unique(col))>1 (both express non-constancy; both false on len<=1); col_has_one(col) ⇔ ∃i.col[i]==1 ⇔ np.any(np.unique(col)==1) (membership of 1 is dedup-invariant). Both validated by axiom_check.py / G-AX (19 boundary + 20000 fuzz columns for reductions; 7 boundary + 20000 fuzz 6-column tick tables for the whole determine_level scan vs a verbatim transcription of the post-patch dates.py loop body). The changed operation (added np.any(unique==1) conjunct) is modeled DEEPLY (col_has_one, consumed directly in determine_level), not hidden behind an axiom about the function under change.

Spec strength: the postconditions pin BOTH outputs (level and show_offset) across the entire precondition domain — 7 mutually-exclusive/exhaustive level cases plus show_offset==(fine-or-no-vary ? 1 : (coarse ? col_has_one-determined)). This is a total, deterministic functional spec, so any verifying impl must agree with the gold pointwise; that is why every one of the 7 distinct wrong impls fails verification while the behaviorally-equivalent restructure verifies and resolves.

Verdict: SOUND. 8 same-spec attacks run (7 wrong impls all rejected incl. prepatch bug; 1 equivalent restructure verified and its materialized faithful patch RESOLVED under run_resolve). No verifying wrong-impl patch failed to resolve. Evidence complete.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

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

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-22871.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A sequence of tick instants is described by six parallel integer columns,
  one per calendar component, ordered from coarsest to finest:

      column 0 = year, 1 = month, 2 = day, 3 = hour, 4 = minute, 5 = second.

  All columns have the same length N (>= 1), one entry per tick.

  Two derived quantities are computed:

    * the labelling level L -- the finest component that the ticks share, found
      by scanning the columns from finest (5) to coarsest (0) and selecting the
      FIRST column (i.e. the highest-indexed one) whose entries are NOT all
      equal across the ticks. When every column is constant across the ticks
      (all ticks identical down to the second), L is the finest level, 5.

    * whether a separate summary label (the "offset") is shown. By default it
      is shown. It is suppressed ONLY when the labelling level is a coarse one
      (year or month, i.e. L < 2) AND the value 1 occurs somewhere in that
      labelling column. Otherwise -- in particular at a coarse labelling level
      whose column does NOT contain the value 1 -- the offset stays shown.

  The reported result carries the labelling level and a 0/1 flag for whether the
  offset is shown.

Modelling choices (Nagini fragment):
  * Each tick column is a ``List[int]`` (the integer calendar component).
    `col_varies` and `col_has_one` are structural predicates over a column --
    "the column is not constant" and "the value 1 is present in the column" --
    validated against the real column reductions out-of-band by axiom_check.py
    (G-AX); they are not consumed as axioms.
  * The six-iteration descending scan over the literal range of levels is
    transcribed as a straight-line cascade (the trip count is a compile-time
    constant; no data-dependent loop bound).
  * The result is returned as a small object with the two observed fields.

No string indexing or library import beyond typing / nagini_contracts is used.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The two structural predicates the behaviour composes --
# "the column is not constant" and "the value 1 is present in the column" --
# are modelled DEEPLY by `col_varies` / `col_has_one` below. They are not opaque
# callees the proof stands in for; their equality to the real column reductions
# is validated out-of-band by axiom_check.py (G-AX) as A-reference deep models.
# axioms-end


# pure-start
@Pure
def col_varies(col: List[int]) -> bool:
    """True iff the column is not constant across the ticks, i.e. two ticks
    disagree on this calendar component."""
    Requires(Acc(list_pred(col), 1 / 4))
    return Exists(int, lambda i: Exists(int, lambda j: (
        0 <= i and i < j and j < len(col) and col[i] != col[j])))


@Pure
def col_has_one(col: List[int]) -> bool:
    """True iff the value 1 occurs somewhere in the column."""
    Requires(Acc(list_pred(col), 1 / 4))
    return Exists(int, lambda i: (0 <= i and i < len(col) and col[i] == 1))
# pure-end


class TickLevel:
    """The two observed outputs of the labelling-level computation: the chosen
    labelling level and a 0/1 flag for whether the summary offset is shown."""

    def __init__(self, level: int, show_offset: int) -> None:
        Requires(0 <= level and level <= 5)
        Requires(show_offset == 0 or show_offset == 1)
        Ensures(Acc(self.level) and Acc(self.show_offset))
        Ensures(self.level == level and self.show_offset == show_offset)
        self.level = level          # type: int
        self.show_offset = show_offset  # type: int


def determine_level(c0: List[int], c1: List[int], c2: List[int],
                    c3: List[int], c4: List[int], c5: List[int]) -> TickLevel:
    # pre-conditions-start
    # The six tick columns are READ-ONLY (directive 5: fractional permission).
    Requires(Acc(list_pred(c0), 1 / 2))
    Requires(Acc(list_pred(c1), 1 / 2))
    Requires(Acc(list_pred(c2), 1 / 2))
    Requires(Acc(list_pred(c3), 1 / 2))
    Requires(Acc(list_pred(c4), 1 / 2))
    Requires(Acc(list_pred(c5), 1 / 2))
    # There is at least one tick, and all columns share the same length.
    Requires(len(c0) >= 1)
    Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
    Requires(len(c4) == len(c0) and len(c5) == len(c0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(c0), 1 / 2))
    Ensures(Acc(list_pred(c1), 1 / 2))
    Ensures(Acc(list_pred(c2), 1 / 2))
    Ensures(Acc(list_pred(c3), 1 / 2))
    Ensures(Acc(list_pred(c4), 1 / 2))
    Ensures(Acc(list_pred(c5), 1 / 2))
    Ensures(Acc(Result().level) and Acc(Result().show_offset))
    Ensures(0 <= Result().level and Result().level <= 5)
    Ensures(Result().show_offset == 0 or Result().show_offset == 1)
    # The labelling level is the highest-indexed column that varies, found by
    # the finest-to-coarsest scan; if no column varies it is the finest, 5.
    Ensures(Implies(col_varies(c5), Result().level == 5))
    Ensures(Implies(not col_varies(c5) and col_varies(c4),
                    Result().level == 4))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4) and col_varies(c3),
                    Result().level == 3))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and col_varies(c2),
                    Result().level == 2))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and col_varies(c1), Result().level == 1))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and col_varies(c0),
                    Result().level == 0))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and not col_varies(c0),
                    Result().level == 5))
    # The offset is hidden (flag == 0) EXACTLY when the labelling level is a
    # coarse one (year or month) AND that column carries the value 1; otherwise
    # the offset stays shown (flag == 1), including at a coarse labelling level
    # whose column does not contain the value 1.
    Ensures(Implies(col_varies(c1) and not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2),
                    (Result().show_offset == 0) == col_has_one(c1)))
    Ensures(Implies(col_varies(c0) and not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1),
                    (Result().show_offset == 0) == col_has_one(c0)))
    # When the labelling level is a fine one (>= 2), or when no column varies,
    # the offset is always shown.
    Ensures(Implies(col_varies(c5) or col_varies(c4) or col_varies(c3)
                    or col_varies(c2),
                    Result().show_offset == 1))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and not col_varies(c0),
                    Result().show_offset == 1))
    # post-conditions-end
    # impl-start
    # Default: the offset is shown. The descending scan over the six levels is
    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
    if col_varies(c5):
        return TickLevel(5, 1)
    if col_varies(c4):
        return TickLevel(4, 1)
    if col_varies(c3):
        return TickLevel(3, 1)
    if col_varies(c2):
        return TickLevel(2, 1)
    if col_varies(c1):
        if col_has_one(c1):
            return TickLevel(1, 0)
        return TickLevel(1, 1)
    if col_varies(c0):
        if col_has_one(c0):
            return TickLevel(0, 0)
        return TickLevel(0, 1)
    # No column varies: every tick is identical down to the second. The scan
    # reaches the coarsest level with all entries equal and resets to the finest
    # level; the offset keeps its default (shown).
    return TickLevel(5, 1)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for matplotlib__matplotlib-22871 (nagini). All 8 attacks were built by copying model.py and editing ONLY the impl region (spec/axioms/@Pure/Requires/Ensures byte-identical — verified with diff on the pre-impl-start region for every file).

Positive control: pos_control.py = model.py verbatim => CANDIDATE (shares spec AND verifies, 21.6s); it is the gold and resolves (baseline sanity).

### WRONG-IMPL ATTACKS (all correctly REJECTED, exit 2 — spec sensed the defect):
- atk_1 PREPATCH BUG: at level<2 return show_offset=0 unconditionally (no col_has_one check). NOT-A-COUNTEREXAMPLE — fails the month-level postcondition (Result().show_offset==0)==col_has_one(c1). Prepatch reproduced (matches model_prepatch.py; G-DIFF live).
- atk_2 WRONG COLUMN: at level 1 test col_has_one(c0) instead of col_has_one(c1). REJECTED.
- atk_3 CONTROL-FLOW-EFFECT: drop suppression entirely, always show_offset=1 at coarse levels. REJECTED.
- atk_4 CONTROL-FLOW REVERSAL: scan coarse->fine (pick lowest varying level). REJECTED (wrong level selection).
- atk_5 BOUNDARY/OFF-BY-ONE: c4 varies -> return level 3. REJECTED.
- atk_6 BOUNDARY: no-column-varies -> return TickLevel(0,1) instead of (5,1). REJECTED.
- atk_7 UNGROUNDED-ORACLE ECHO: always return TickLevel(5,1). REJECTED.

CANDIDATE (shares spec AND verifies) requiring resolve:
- atk_8 EQUIVALENT RESTRUCTURE: elif-chain with local show_offset expression (0 if col_has_one else 1), semantically identical to gold. Weakness => CANDIDATE (verifies, 18.5s). MANDATORY resolve: materialized faithful refined patch atk_8.patch (turns `if level<2:` into `if level<2 and bool(np.any(unique==1)):`, hoists unique — the gold change) and RAN it through the official harness: `run_resolve('matplotlib__matplotlib-22871', atk_8.patch, timeout=1800)` => completed=True, resolved=True, note='resolved'. The only verifying candidate RESOLVES, so no verify⇏correct witness exists.

REFINEMENT.MD AUDIT: legs A1(R), A2(A-reference col_varies), A3(A-reference col_has_one), A4(I unrolled constant-bound loop), A5(I + A-reference). No kind-3 (unexpressible-changed-op) legs; meta.json axioms=[] confirms NO consumed @ContractOnly axioms. A-legs correspondence holds: col_varies(col) ⇔ ∃i<j.col[i]≠col[j] ⇔ len(np.unique(col))>1 (both express non-constancy; both false on len<=1); col_has_one(col) ⇔ ∃i.col[i]==1 ⇔ np.any(np.unique(col)==1) (membership of 1 is dedup-invariant). Both validated by axiom_check.py / G-AX (19 boundary + 20000 fuzz columns for reductions; 7 boundary + 20000 fuzz 6-column tick tables for the whole determine_level scan vs a verbatim transcription of the post-patch dates.py loop body). The changed operation (added np.any(unique==1) conjunct) is modeled DEEPLY (col_has_one, consumed directly in determine_level), not hidden behind an axiom about the function under change.

Spec strength: the postconditions pin BOTH outputs (level and show_offset) across the entire precondition domain — 7 mutually-exclusive/exhaustive level cases plus show_offset==(fine-or-no-vary ? 1 : (coarse ? col_has_one-determined)). This is a total, deterministic functional spec, so any verifying impl must agree with the gold pointwise; that is why every one of the 7 distinct wrong impls fails verification while the behaviorally-equivalent restructure verifies and resolves.

Verdict: SOUND. 8 same-spec attacks run (7 wrong impls all rejected incl. prepatch bug; 1 equivalent restructure verified and its materialized faithful patch RESOLVED under run_resolve). No verifying wrong-impl patch failed to resolve. Evidence complete.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed across every available check; no input found where the modeled determine_level disagrees with the real ConciseDateFormatter.format_ticks scan.

Spec/mapping: model.py's determine_level(c0..c5) models the labelling-level scan in lib/matplotlib/dates.py:802-812 (post-patch). The N×6 numpy integer table `tickdate` (= [tdt.timetuple()[:6] for tdt in tickdatetime]) maps to six parallel List[int] columns; level (0..5) is identity; show_offset True/False -> 1/0. The two numpy reductions are modeled deeply: col_varies == (len(np.unique(col))>1), col_has_one == np.any(np.unique(col)==1). Postconditions pin (i) level = highest-indexed varying column, else 5 when none varies, and (ii) show_offset==0 EXACTLY when level<2 (year/month) AND that column contains 1 — matching the gold patch's added `np.any(unique==1)` conjunct. same-spec on the identity model returns SAME (exit 0), so the analyzed spec is the frozen one.

Evidence the spec is neither too strong nor drifting:
- G-AX (axiom_check.py) OK: col_varies/col_has_one == real numpy on 19 boundary + 20000 fuzz columns; whole determine_level == faithful real-loop transcription on 7 boundary + 20000 fuzz tick tables.
- G-CONF (conformance_check.py) OK against the REAL patched matplotlib.dates.ConciseDateFormatter.format_ticks (observed via sentinel Fk/Zk/OFFk formats, inputs bridged through real datetimes -> date2num -> num2date().timetuple()): 100012 inputs (12 boundary + 100000 fuzz), 0 disagreements.
- Independent differential fuzz (my own, seed 999999, 300000 draws, aggressive constant-column bias + heavy year==1/month==1 coverage, N up to 7) against the real patched formatter: 0 mismatches.
- Model VERIFIES in pinned Nagini (19.93 s) — the spec is satisfiable, not vacuously over-strong; the impl inhabits it.

The only genuinely-changed operation (added `np.any(unique==1)` offset-suppression conjunct) is modeled directly, not hidden behind an axiom. No consumed @ContractOnly axioms exist. Conclusion: the modeled function agrees with the real repo callee on all tested inputs over the reachable domain; spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl region elided to `...`) computed via markers.spec_view; mechanical leak screen (leakage.screen) passes with zero hard failures. Manual gold-reconstruction check: the gold edit turns the offset-suppression guard `if level < 2:` into `if level < 2 and np.any(unique == 1):` in ConciseDateFormatter.format_ticks (lib/matplotlib/dates.py). NONE of the edit's fingerprints appear in the spec view: no diff markers, no patched file/module path, no repo symbols (format_ticks, ConciseDateFormatter, np.unique, np.any, tickdate — the only names used are abstract predicates col_varies/col_has_one), no verbatim gold-patch line, no bug/fix/patch narration. The spec's discriminator — offset suppressed ONLY at a coarse level (year/month) AND when value 1 (January) occurs in the labelling column — is stated as DESIRED BEHAVIOR, and it is already derivable from the PUBLIC problem_statement, which says the year should show in the offset when '<12 months' are plotted and 'January is not included in the x-axis'. So the spec view reveals nothing about the gold edit beyond what the public bug report already exposes; it does not localize the edit to the loop/guard, does not disclose the numpy reductions, and does not reveal the pre-patch vs post-patch delta. refinement.md/mapping.md (which DO name dates.py, format_ticks, np.unique/np.any and quote the gold hunk) are auditor artifacts outside the consumer spec view and are not screened. relaxed_leakage flag is unset; recorded G-LEAK status is 'pass' (spec view clean), consistent with this finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
