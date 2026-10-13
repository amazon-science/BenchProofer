# P2 adversarial audit — django__django-16032

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no attack came back a CANDIDATE (no same-spec impl verified). The spec pins every modeled field in every function's postconditions, leaving zero slack for a wrong-but-verifying impl.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -109,7 +107,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -125,10 +122,13 @@
     Ensures(ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns)))
     # post-conditions-end
     # impl-start
-    # attaching the returned-column kind and the non-returned (helper) kind
-    # materializes the auxiliary expression-tracking structure; it touches no
-    # other state.
+    # PRE-PATCH (query.py): the explicit-projection property was DERIVED from
+    # the internal expression-tracking structure, so materializing that
+    # structure here (the returned-column kind plus the non-returned helper kind)
+    # was mistaken for an explicit projection.
     q.aux_expr_materialized = True
+    if q.aux_expr_materialized:
+        q.restricted_to_explicit_columns = True
     # impl-end
 
 
@@ -137,7 +137,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -109,7 +107,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -137,7 +134,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -170,7 +166,12 @@
     # post-conditions-end
     # impl-start
     if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
-        # narrow the rhs to the single relevant column via the projection
-        # operation (1) — which also establishes the property as true.
-        project_columns(q, target_column)
+        # PRE-PATCH (related_lookups.py): the rhs was narrowed by clearing its
+        # select clause and then re-adding the single column to the SELECT set
+        # directly. That set the selected output but did NOT establish the
+        # explicit-projection property (it bypassed the projection operation,
+        # so it neither set the property nor re-derived/cleared the auxiliary
+        # expression-tracking structure).
+        q.selected_columns = []
+        q.selected_columns = [target_column]
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -109,7 +107,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -137,7 +134,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -169,8 +165,8 @@
     )
     # post-conditions-end
     # impl-start
-    if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
-        # narrow the rhs to the single relevant column via the projection
-        # operation (1) — which also establishes the property as true.
+    # CONTROL-FLOW-EFFECT attack: guard inverted — narrow exactly when the rhs
+    # WAS projected or the target IS a unique key. Behaviourally opposite of gold.
+    if q.restricted_to_explicit_columns or target_is_unique_key:
         project_columns(q, target_column)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -95,11 +93,11 @@
     Ensures(q.aux_expr_materialized is False)
     # post-conditions-end
     # impl-start
+    # BOUNDARY attack: project onto a DIFFERENT column (column+1) instead of the
+    # requested one. Selects one column and sets the flag, but the wrong column.
     q.selected_columns = []
-    q.selected_columns = [column]
+    q.selected_columns = [column + 1]
     q.restricted_to_explicit_columns = True
-    # projection re-derives the expression-tracking structure for the chosen
-    # ordinary columns, which leaves it empty.
     q.aux_expr_materialized = False
     # impl-end
 
@@ -109,7 +107,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -137,7 +134,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -95,12 +93,13 @@
     Ensures(q.aux_expr_materialized is False)
     # post-conditions-end
     # impl-start
+    # PARTIAL-DOMAIN attack: project_columns leaves aux_expr_materialized at its
+    # incoming value (does NOT clear it) — faithful only when it was already
+    # False; wrong when a query with a materialized mask is projected.
     q.selected_columns = []
     q.selected_columns = [column]
     q.restricted_to_explicit_columns = True
-    # projection re-derives the expression-tracking structure for the chosen
-    # ordinary columns, which leaves it empty.
-    q.aux_expr_materialized = False
+    # (deliberately no clear of aux_expr_materialized)
     # impl-end
 
 
@@ -109,7 +108,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -137,7 +135,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -109,7 +107,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -125,10 +122,11 @@
     Ensures(ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns)))
     # post-conditions-end
     # impl-start
-    # attaching the returned-column kind and the non-returned (helper) kind
-    # materializes the auxiliary expression-tracking structure; it touches no
-    # other state.
+    # CONTROL-FLOW-EFFECT attack: also blow away the selected columns while
+    # materializing aux. Violates the frame `ToSeq(selected)==Old(...)` when the
+    # incoming query had any selected columns.
     q.aux_expr_materialized = True
+    q.selected_columns = []
     # impl-end
 
 
@@ -137,7 +135,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -109,7 +107,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -137,7 +134,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -169,8 +165,12 @@
     )
     # post-conditions-end
     # impl-start
+    # UNGROUNDED-ORACLE-ECHO attack: narrow, but leave aux_expr_materialized at
+    # whatever it was (skip the clear that projection performs). Faithful in the
+    # common witness (aux already False) but wrong when the rhs had a
+    # materialized mask before narrowing.
     if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
-        # narrow the rhs to the single relevant column via the projection
-        # operation (1) — which also establishes the property as true.
-        project_columns(q, target_column)
+        q.selected_columns = []
+        q.selected_columns = [target_column]
+        q.restricted_to_explicit_columns = True
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Query:
@@ -79,7 +78,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -109,7 +107,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -137,7 +134,6 @@
     Requires(Acc(q.restricted_to_explicit_columns))
     Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
     Requires(Acc(q.aux_expr_materialized))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(q.restricted_to_explicit_columns))
@@ -169,8 +165,8 @@
     )
     # post-conditions-end
     # impl-start
-    if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
-        # narrow the rhs to the single relevant column via the projection
-        # operation (1) — which also establishes the property as true.
-        project_columns(q, target_column)
+    # CONTROL-FLOW / UNCONDITIONAL attack: always narrow, ignoring the guard.
+    # Violates the no-narrow frame clause when the rhs was already projected or
+    # the target is a unique key (must be left untouched, but this mutates it).
+    project_columns(q, target_column)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16032.

Behaviour under specification (stated as desired behaviour, not as an edit):

A query value used on the right-hand side of a membership filter against a
related column carries a single boolean property — call it
``restricted_to_explicit_columns`` — that records whether the query's selected
output columns have been *explicitly* restricted by a column-projection call
(the operation that pins the SELECT list to a chosen set of names). The three
operations modelled here must keep that property faithful:

  (1) Projecting a query onto a chosen set of columns restricts its selected
      output to exactly that set AND establishes the property as true. The
      projection also re-derives the internal expression-tracking structure
      for the newly-chosen columns; because the chosen columns are ordinary
      output columns (never auxiliary expressions), that structure is left
      empty afterwards — projection clears it.

  (2) Attaching auxiliary derived expressions to a query — both the kind that
      adds a returned column and the kind that adds a helper column that is not
      itself returned — may populate the query's internal expression-tracking
      structure, but it must NOT, on its own, establish the property. Whether
      the output columns were explicitly restricted depends only on whether a
      projection (operation 1) has occurred, never on the presence of auxiliary
      expressions. So combining the two kinds of auxiliary expressions still
      leaves the property false on a query that was never projected.

  (3) Preparing such a query as the right-hand side of the membership filter:
      when the property is false (the right-hand side was never projected) and
      the comparison is not already against a unique-key column, the right-hand
      side is narrowed to the single relevant column. That narrowing is exactly
      operation (1): afterwards the selected output is that one column, the
      property is true, and the expression-tracking structure is cleared. When
      the property is already true, or the comparison is against a unique-key
      column, the right-hand side is left untouched.

A query is modelled as a minimal object exposing only the touched state: the
boolean property, the list of explicitly-selected column ids, and a boolean
recording whether the internal expression-tracking structure has been
materialized (the structure whose mere presence must no longer be mistaken for
an explicit projection). No callee is axiomatized: the behaviour is pure
object/state logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Query:
    def __init__(self) -> None:
        Ensures(Acc(self.restricted_to_explicit_columns))  # type: ignore
        Ensures(Acc(self.selected_columns) and Acc(list_pred(self.selected_columns)))  # type: ignore
        Ensures(Acc(self.aux_expr_materialized))           # type: ignore
        Ensures(self.restricted_to_explicit_columns is False)  # type: ignore
        Ensures(len(self.selected_columns) == 0)           # type: ignore
        Ensures(self.aux_expr_materialized is False)       # type: ignore
        self.restricted_to_explicit_columns = False  # type: bool
        self.selected_columns = []  # type: List[int]
        self.aux_expr_materialized = False  # type: bool


# axioms-start
# No consumed axioms: the three operations are pure object/state logic, modelled
# deeply. The underlying field-clearing/selection primitives the operations build
# on are validated against their real semantics out-of-band by axiom_check.py
# (G-AX) as A-reference observations, not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def project_columns(q: Query, column: int) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (1) the selected output is restricted to exactly the chosen column ...
    Ensures(len(q.selected_columns) == 1)
    Ensures(q.selected_columns[0] == column)
    # ... AND the explicit-projection property is established as true.
    Ensures(q.restricted_to_explicit_columns is True)
    # ... AND the auxiliary expression-tracking structure is re-derived for the
    # chosen (ordinary, non-auxiliary) columns: it ends up empty — cleared.
    Ensures(q.aux_expr_materialized is False)
    # post-conditions-end
    # impl-start
    q.selected_columns = []
    q.selected_columns = [column]
    q.restricted_to_explicit_columns = True
    # projection re-derives the expression-tracking structure for the chosen
    # ordinary columns, which leaves it empty.
    q.aux_expr_materialized = False
    # impl-end


def attach_auxiliary_expressions(q: Query) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (2) auxiliary expressions (returned + non-returned kinds) materialize the
    # internal expression-tracking structure ...
    Ensures(q.aux_expr_materialized is True)
    # ... but they leave the explicit-projection property and the selected
    # output exactly as they were: presence of auxiliary expressions is NOT an
    # explicit projection.
    Ensures(q.restricted_to_explicit_columns == Old(q.restricted_to_explicit_columns))
    Ensures(ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns)))
    # post-conditions-end
    # impl-start
    # attaching the returned-column kind and the non-returned (helper) kind
    # materializes the auxiliary expression-tracking structure; it touches no
    # other state.
    q.aux_expr_materialized = True
    # impl-end


def prepare_in_rhs(q: Query, target_column: int, target_is_unique_key: bool) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (3) narrowing happens exactly when the rhs was never explicitly projected
    # and the comparison is not against a unique-key column: afterwards the
    # selected output is that one column, the property is true, and — because
    # narrowing IS the projection operation (1) — the auxiliary
    # expression-tracking structure is cleared.
    Ensures(
        Implies(
            (not Old(q.restricted_to_explicit_columns)) and (not target_is_unique_key),
            len(q.selected_columns) == 1
            and q.selected_columns[0] == target_column
            and (q.restricted_to_explicit_columns is True)
            and (q.aux_expr_materialized is False),
        )
    )
    # when narrowing does NOT happen the rhs is left untouched (including the
    # auxiliary expression-tracking structure).
    Ensures(
        Implies(
            Old(q.restricted_to_explicit_columns) or target_is_unique_key,
            q.restricted_to_explicit_columns == Old(q.restricted_to_explicit_columns)
            and ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns))
            and q.aux_expr_materialized == Old(q.aux_expr_materialized),
        )
    )
    # post-conditions-end
    # impl-start
    if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
        # narrow the rhs to the single relevant column via the projection
        # operation (1) — which also establishes the property as true.
        project_columns(q, target_column)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity), django__django-16032 nagini. Ran from project root with PY=python; verifier wall SBN_VERIFY_TIMEOUT=600 (the prior recorded G-EQ 'INCONCLUSIVE — 3 attacks inconclusive' was a verifier-timeout artifact at the default 300s wall; re-run at 600s, all attacks completed conclusively).

POSITIVE CONTROL: cp of bundle model.py -> positive_control.py; `bash scripts/nagini_verify.sh .../positive_control.py` => EXIT 0 'Verification successful' (14.22s). All 8 attacks passed `adversary same-spec nagini django__django-16032 <f>` (EXIT 0, byte-identical spec; only impl regions edited).

ATTACKS (all: `python -m swebench_unified.adversary weakness nagini django__django-16032 atk_N.py`; each NOT-A-COUNTEREXAMPLE = verification failed, spec rejected):
- atk_1 = model_prepatch.py (the query.py prepatch bug: attach_auxiliary_expressions derives restricted flag True from a materialized mask). REJECTED — violates postcondition restricted_to_explicit_columns == Old(...). w1.log.
- atk_2 = model_prepatch_2.py (the related_lookups.py prepatch bug: prepare_in_rhs narrows inline via clear+set, never setting the flag). REJECTED — violates the narrowing postcondition restricted_to_explicit_columns is True. w2.log.
- atk_3 (control-flow-effect): inverted prepare_in_rhs guard `if restricted or unique_key`. REJECTED. w3.log.
- atk_4 (boundary): project_columns onto column+1 instead of column. REJECTED — violates selected_columns[0]==column. w4.log.
- atk_5 (partial-domain): project_columns omits the aux_expr_materialized=False clear. REJECTED — violates aux cleared postcondition. w5.log.
- atk_6 (control-flow-effect / frame): attach also clears selected_columns. REJECTED — violates ToSeq(selected)==Old(...). w6.log.
- atk_7 (ungrounded-oracle echo): prepare_in_rhs narrows but skips the aux clear (faithful only when aux already False). REJECTED — violates aux_expr_materialized is False in narrow branch. w7.log.
- atk_8 (control-flow / unconditional): prepare_in_rhs always narrows, ignoring the guard. REJECTED — violates the no-narrow frame clause. w8.log.

No CANDIDATE emerged, so no faithful refined patch needed materializing/run_resolve (mandatory only for verifying candidates). No timeouts/infra errors in any w*.log (grep clean). Not vacuous: 8 distinct wrong impls across partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, plus both recorded prepatch bugs.

REFINEMENT.MD AUDIT (A-legs + model<->patch correspondence): gold patch (from data/swe_bench_verified/test.jsonl) confirmed: related_lookups.py drops clear_select_clause() and swaps add_fields([tf],True)->set_values([tf]); query.py adds class attr has_select_fields=False, removes the derived @property, adds self.has_select_fields=True in set_values. Every leg is R / I / A-reference — NO kind-3. Key A-legs check out: A3 (I) restricted=True <-> has_select_fields=True in set_values; A4 (A-reference) aux=False <-> set_values re-derives empty annotation_select_mask (G-AX 3.1 asserts `not annotation_select_mask`); B2 (I) flag decoupled from mask <-> removed @property; C2 (A-reference) project_columns <-> set_values([tf]) (prepare_in_rhs calls project_columns under its own spec, not an axiom — correct per SPEC_GUIDE). No consumed axioms. G-AX/axiom_check.py is sound: imports only Django, runs on gold-patched tree, fail-closed on unavailability/vacuity, 11 A-reference observations pass (meta.json G-AX status=pass), including the pk-target skipped-branch and already-projected no-narrow cases. Correspondence holds.

VERDICT: SOUND. verify => correct holds for this spec on the exhibited attack family; the spec's fully-deterministic postconditions admit no same-spec wrong-but-verifying impl. (Advisory; runner re-runs the artifacts.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no attack came back a CANDIDATE (no same-spec impl verified). The spec pins every modeled field in every function's postconditions, leaving zero slack for a wrong-but-verifying impl.
```

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16032.

Behaviour under specification (stated as desired behaviour, not as an edit):

A query value used on the right-hand side of a membership filter against a
related column carries a single boolean property — call it
``restricted_to_explicit_columns`` — that records whether the query's selected
output columns have been *explicitly* restricted by a column-projection call
(the operation that pins the SELECT list to a chosen set of names). The three
operations modelled here must keep that property faithful:

  (1) Projecting a query onto a chosen set of columns restricts its selected
      output to exactly that set AND establishes the property as true. The
      projection also re-derives the internal expression-tracking structure
      for the newly-chosen columns; because the chosen columns are ordinary
      output columns (never auxiliary expressions), that structure is left
      empty afterwards — projection clears it.

  (2) Attaching auxiliary derived expressions to a query — both the kind that
      adds a returned column and the kind that adds a helper column that is not
      itself returned — may populate the query's internal expression-tracking
      structure, but it must NOT, on its own, establish the property. Whether
      the output columns were explicitly restricted depends only on whether a
      projection (operation 1) has occurred, never on the presence of auxiliary
      expressions. So combining the two kinds of auxiliary expressions still
      leaves the property false on a query that was never projected.

  (3) Preparing such a query as the right-hand side of the membership filter:
      when the property is false (the right-hand side was never projected) and
      the comparison is not already against a unique-key column, the right-hand
      side is narrowed to the single relevant column. That narrowing is exactly
      operation (1): afterwards the selected output is that one column, the
      property is true, and the expression-tracking structure is cleared. When
      the property is already true, or the comparison is against a unique-key
      column, the right-hand side is left untouched.

A query is modelled as a minimal object exposing only the touched state: the
boolean property, the list of explicitly-selected column ids, and a boolean
recording whether the internal expression-tracking structure has been
materialized (the structure whose mere presence must no longer be mistaken for
an explicit projection). No callee is axiomatized: the behaviour is pure
object/state logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Query:
    def __init__(self) -> None:
        Ensures(Acc(self.restricted_to_explicit_columns))  # type: ignore
        Ensures(Acc(self.selected_columns) and Acc(list_pred(self.selected_columns)))  # type: ignore
        Ensures(Acc(self.aux_expr_materialized))           # type: ignore
        Ensures(self.restricted_to_explicit_columns is False)  # type: ignore
        Ensures(len(self.selected_columns) == 0)           # type: ignore
        Ensures(self.aux_expr_materialized is False)       # type: ignore
        self.restricted_to_explicit_columns = False  # type: bool
        self.selected_columns = []  # type: List[int]
        self.aux_expr_materialized = False  # type: bool


# axioms-start
# No consumed axioms: the three operations are pure object/state logic, modelled
# deeply. The underlying field-clearing/selection primitives the operations build
# on are validated against their real semantics out-of-band by axiom_check.py
# (G-AX) as A-reference observations, not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def project_columns(q: Query, column: int) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (1) the selected output is restricted to exactly the chosen column ...
    Ensures(len(q.selected_columns) == 1)
    Ensures(q.selected_columns[0] == column)
    # ... AND the explicit-projection property is established as true.
    Ensures(q.restricted_to_explicit_columns is True)
    # ... AND the auxiliary expression-tracking structure is re-derived for the
    # chosen (ordinary, non-auxiliary) columns: it ends up empty — cleared.
    Ensures(q.aux_expr_materialized is False)
    # post-conditions-end
    # impl-start
    q.selected_columns = []
    q.selected_columns = [column]
    q.restricted_to_explicit_columns = True
    # projection re-derives the expression-tracking structure for the chosen
    # ordinary columns, which leaves it empty.
    q.aux_expr_materialized = False
    # impl-end


def attach_auxiliary_expressions(q: Query) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (2) auxiliary expressions (returned + non-returned kinds) materialize the
    # internal expression-tracking structure ...
    Ensures(q.aux_expr_materialized is True)
    # ... but they leave the explicit-projection property and the selected
    # output exactly as they were: presence of auxiliary expressions is NOT an
    # explicit projection.
    Ensures(q.restricted_to_explicit_columns == Old(q.restricted_to_explicit_columns))
    Ensures(ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns)))
    # post-conditions-end
    # impl-start
    # attaching the returned-column kind and the non-returned (helper) kind
    # materializes the auxiliary expression-tracking structure; it touches no
    # other state.
    q.aux_expr_materialized = True
    # impl-end


def prepare_in_rhs(q: Query, target_column: int, target_is_unique_key: bool) -> None:
    # pre-conditions-start
    Requires(Acc(q.restricted_to_explicit_columns))
    Requires(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Requires(Acc(q.aux_expr_materialized))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted_to_explicit_columns))
    Ensures(Acc(q.selected_columns) and Acc(list_pred(q.selected_columns)))
    Ensures(Acc(q.aux_expr_materialized))
    # (3) narrowing happens exactly when the rhs was never explicitly projected
    # and the comparison is not against a unique-key column: afterwards the
    # selected output is that one column, the property is true, and — because
    # narrowing IS the projection operation (1) — the auxiliary
    # expression-tracking structure is cleared.
    Ensures(
        Implies(
            (not Old(q.restricted_to_explicit_columns)) and (not target_is_unique_key),
            len(q.selected_columns) == 1
            and q.selected_columns[0] == target_column
            and (q.restricted_to_explicit_columns is True)
            and (q.aux_expr_materialized is False),
        )
    )
    # when narrowing does NOT happen the rhs is left untouched (including the
    # auxiliary expression-tracking structure).
    Ensures(
        Implies(
            Old(q.restricted_to_explicit_columns) or target_is_unique_key,
            q.restricted_to_explicit_columns == Old(q.restricted_to_explicit_columns)
            and ToSeq(q.selected_columns) == Old(ToSeq(q.selected_columns))
            and q.aux_expr_materialized == Old(q.aux_expr_materialized),
        )
    )
    # post-conditions-end
    # impl-start
    if (not q.restricted_to_explicit_columns) and (not target_is_unique_key):
        # narrow the rhs to the single relevant column via the projection
        # operation (1) — which also establishes the property as true.
        project_columns(q, target_column)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity), django__django-16032 nagini. Ran from project root with PY=python; verifier wall SBN_VERIFY_TIMEOUT=600 (the prior recorded G-EQ 'INCONCLUSIVE — 3 attacks inconclusive' was a verifier-timeout artifact at the default 300s wall; re-run at 600s, all attacks completed conclusively).

POSITIVE CONTROL: cp of bundle model.py -> positive_control.py; `bash scripts/nagini_verify.sh .../positive_control.py` => EXIT 0 'Verification successful' (14.22s). All 8 attacks passed `adversary same-spec nagini django__django-16032 <f>` (EXIT 0, byte-identical spec; only impl regions edited).

ATTACKS (all: `python -m swebench_unified.adversary weakness nagini django__django-16032 atk_N.py`; each NOT-A-COUNTEREXAMPLE = verification failed, spec rejected):
- atk_1 = model_prepatch.py (the query.py prepatch bug: attach_auxiliary_expressions derives restricted flag True from a materialized mask). REJECTED — violates postcondition restricted_to_explicit_columns == Old(...). w1.log.
- atk_2 = model_prepatch_2.py (the related_lookups.py prepatch bug: prepare_in_rhs narrows inline via clear+set, never setting the flag). REJECTED — violates the narrowing postcondition restricted_to_explicit_columns is True. w2.log.
- atk_3 (control-flow-effect): inverted prepare_in_rhs guard `if restricted or unique_key`. REJECTED. w3.log.
- atk_4 (boundary): project_columns onto column+1 instead of column. REJECTED — violates selected_columns[0]==column. w4.log.
- atk_5 (partial-domain): project_columns omits the aux_expr_materialized=False clear. REJECTED — violates aux cleared postcondition. w5.log.
- atk_6 (control-flow-effect / frame): attach also clears selected_columns. REJECTED — violates ToSeq(selected)==Old(...). w6.log.
- atk_7 (ungrounded-oracle echo): prepare_in_rhs narrows but skips the aux clear (faithful only when aux already False). REJECTED — violates aux_expr_materialized is False in narrow branch. w7.log.
- atk_8 (control-flow / unconditional): prepare_in_rhs always narrows, ignoring the guard. REJECTED — violates the no-narrow frame clause. w8.log.

No CANDIDATE emerged, so no faithful refined patch needed materializing/run_resolve (mandatory only for verifying candidates). No timeouts/infra errors in any w*.log (grep clean). Not vacuous: 8 distinct wrong impls across partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, plus both recorded prepatch bugs.

REFINEMENT.MD AUDIT (A-legs + model<->patch correspondence): gold patch (from data/swe_bench_verified/test.jsonl) confirmed: related_lookups.py drops clear_select_clause() and swaps add_fields([tf],True)->set_values([tf]); query.py adds class attr has_select_fields=False, removes the derived @property, adds self.has_select_fields=True in set_values. Every leg is R / I / A-reference — NO kind-3. Key A-legs check out: A3 (I) restricted=True <-> has_select_fields=True in set_values; A4 (A-reference) aux=False <-> set_values re-derives empty annotation_select_mask (G-AX 3.1 asserts `not annotation_select_mask`); B2 (I) flag decoupled from mask <-> removed @property; C2 (A-reference) project_columns <-> set_values([tf]) (prepare_in_rhs calls project_columns under its own spec, not an axiom — correct per SPEC_GUIDE). No consumed axioms. G-AX/axiom_check.py is sound: imports only Django, runs on gold-patched tree, fail-closed on unavailability/vacuity, 11 A-reference observations pass (meta.json G-AX status=pass), including the pk-target skipped-branch and already-projected no-narrow cases. Correspondence holds.

VERDICT: SOUND. verify => correct holds for this spec on the exhibited attack family; the spec's fully-deterministic postconditions admit no same-spec wrong-but-verifying impl. (Advisory; runner re-runs the artifacts.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** This divergence does NOT constitute a faithfulness break. mapping.md §1 binds prepare_in_rhs to the RelatedIn.get_prep_lookup rhs-NARROWING BRANCH, not the full method. Against that bound callee the model agrees on all inputs: branch fires (non-pk, unprojected) -> clear+set_values, matched by project_columns (verified: has_select_fields=True, values_select=['code'], mask=set()); branch skipped (pk-target OR already-projected) -> branch is a no-op, matched by the model's no-op frame. The pk-skip mask clearing is produced entirely by the UNCHANGED downstream In.get_prep_lookup (lookups.py:418, clear_select_clause()+add_fields(['pk'])), explicitly documented as outside the modeled edit in mapping.md §3.3 and axiom_check.py §3c, and G-AX deliberately/transparently does NOT assert the mask there — it asserts only the attributable observable (has_select_fields staying False), which the model captures correctly. The pk-target case is never the reported-bug scenario (bug fires only for non-pk to_field FKs), so this region is irrelevant to resolution. The frame overclaim is strictly stronger (it constrains more, not less), so it cannot admit any non-resolving implementation. Model verifies (Nagini 17.8s). project_columns/attach_auxiliary_expressions/prepare_in_rhs(non-pk narrow) all confirmed faithful to real Django empirically. Note: refinement.md §A4 records a prior G-PANEL-2 finding that fixed an analogous clearing-vs-preservation mismodel in project_columns (there the clearing IS attributable to the modeled set_values edit); the prepare_in_rhs pk-skip case is genuinely different because its clearing is unchanged downstream code, so the boundary is sound.

Counterexample / evidence:

```
Reverse-FK child__in with an unprojected annotate().alias() rhs: real annotation_select_mask observed {'ann'} before, set() after get_prep_lookup(); has_select_fields stays False; the spec models aux as preserved (True).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (swebench_unified.markers.spec_view, backend=nagini) = abstract docstring + Query twin + pre/post contracts; impl regions correctly elided to '...'. Mechanical leakage.screen() passes (0 hard failures); confirmed independently.

Gold edit (test.jsonl patch): (a) related_lookups.py RelatedIn.get_prep_lookup: drop clear_select_clause()+add_fields([target_field],True), call set_values([target_field]); (b) query.py: add class attr has_select_fields=False, delete the derived has_select_fields @property, set self.has_select_fields=True in set_values.

Leakage check vs SOLVER-VISIBLE problem_statement ONLY (not hints_text):
- No gold repo symbol appears in the spec view. All spec identifiers are abstracted twins: restricted_to_explicit_columns (vs has_select_fields), project_columns (vs set_values), attach_auxiliary_expressions (vs add_annotation/annotate/alias), prepare_in_rhs (vs RelatedIn.get_prep_lookup), aux_expr_materialized (vs annotation_select_mask), selected_columns (vs select/values_select). None embed a patched symbol.
- No patched file path (query.py / related_lookups.py) or dotted module path in the spec view.
- No diff markers, no bug/fix/regression narration in comments/docstring (verified: narration regex clean).
- The behavioral content the spec DOES state — that a query on the RHS of an __in membership filter must be narrowed to one column, and that combining the two annotate/alias-kind auxiliary expressions must NOT by itself mark the query as explicitly column-restricted — is exactly the symptom already public in problem_statement (annotate()+alias() before __in => 'sub-select returns 10 columns - expected 1'). The spec expresses the DESIRED behavior/correctness condition, not the gold's implementation mechanism.
- The distinctive gold mechanism (has_select_fields being changed from a derived property to a class attribute; the specific set_values swap) is NOT reconstructible from the spec view. That mechanism appears only in the hints_text and in the auditor docs refinement.md/mapping.md, which are NOT part of the consumer spec view screened here.

spec_view identifiers do not echo any patched symbol; behavior described is at the abstract-property level and traces to the public problem statement. No line reveals the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
