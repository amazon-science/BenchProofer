# P2 adversarial audit — django__django-14351

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_4_echo_fabricate.py`, `atk_5_gratuitous.py`, `atk_6_uncond.py`, `atk_7_offbyone.py`, `atk_8_clearonly.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2_skipclear.py`, `atk_3_directassign.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -148,29 +144,25 @@
     orig_pk = rhs.pk_col  # type: int
     cols = list(lhs_cols)  # type: List[int]
     if rhs_is_query:
-        if not rhs.has_fields:
-            clear_output_columns(rhs)
-            add_identity_column(rhs)
+        # PRE-PATCH: the membership test inherits the generic reader, which
+        # appends the nested query's grouping columns WITHOUT first normalising
+        # a query that has no explicit output columns. A field-less nested query
+        # therefore contributes its full default column set, not just its
+        # identity column.
         rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
         i = 0
         while i < len(rhs_cols):
             # invariants-start
             Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
-            Invariant(rhs.has_fields)
+            Invariant(rhs.has_fields == orig_had_fields)
             Invariant(rhs.default_cols == orig_default)
+            Invariant(rhs.explicit_cols == orig_explicit)
             Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
-            Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
-            Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
             Invariant(rhs_cols == nested_group_by_cols(rhs))
-            Invariant(rhs_cols == rhs.explicit_cols)
             Invariant(Acc(list_pred(cols)))
             Invariant(Acc(list_pred(lhs_cols), 1 / 2))
             Invariant(0 <= i and i <= len(rhs_cols))
             Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
             # invariants-end
             cols.append(rhs_cols[i])
             i = i + 1
```

Attack 2 — `atk_2_skipclear.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -149,7 +145,6 @@
     cols = list(lhs_cols)  # type: List[int]
     if rhs_is_query:
         if not rhs.has_fields:
-            clear_output_columns(rhs)
             add_identity_column(rhs)
         rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
         i = 0
@@ -159,9 +154,6 @@
             Invariant(rhs.has_fields)
             Invariant(rhs.default_cols == orig_default)
             Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
             Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
             Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
             Invariant(rhs_cols == nested_group_by_cols(rhs))
@@ -170,7 +162,6 @@
             Invariant(Acc(list_pred(lhs_cols), 1 / 2))
             Invariant(0 <= i and i <= len(rhs_cols))
             Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
             # invariants-end
             cols.append(rhs_cols[i])
             i = i + 1
```

Attack 3 — `atk_3_directassign.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -149,8 +145,8 @@
     cols = list(lhs_cols)  # type: List[int]
     if rhs_is_query:
         if not rhs.has_fields:
-            clear_output_columns(rhs)
-            add_identity_column(rhs)
+            rhs.has_fields = True
+            rhs.explicit_cols = PSeq(rhs.pk_col)
         rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
         i = 0
         while i < len(rhs_cols):
@@ -159,9 +155,6 @@
             Invariant(rhs.has_fields)
             Invariant(rhs.default_cols == orig_default)
             Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
             Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
             Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
             Invariant(rhs_cols == nested_group_by_cols(rhs))
@@ -170,7 +163,6 @@
             Invariant(Acc(list_pred(lhs_cols), 1 / 2))
             Invariant(0 <= i and i <= len(rhs_cols))
             Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
             # invariants-end
             cols.append(rhs_cols[i])
             i = i + 1
```

Attack 4 — `atk_4_echo_fabricate.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -149,30 +145,23 @@
     cols = list(lhs_cols)  # type: List[int]
     if rhs_is_query:
         if not rhs.has_fields:
-            clear_output_columns(rhs)
-            add_identity_column(rhs)
-        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
-        i = 0
-        while i < len(rhs_cols):
-            # invariants-start
-            Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
-            Invariant(rhs.has_fields)
-            Invariant(rhs.default_cols == orig_default)
-            Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
-            Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
-            Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
-            Invariant(rhs_cols == nested_group_by_cols(rhs))
-            Invariant(rhs_cols == rhs.explicit_cols)
-            Invariant(Acc(list_pred(cols)))
-            Invariant(Acc(list_pred(lhs_cols), 1 / 2))
-            Invariant(0 <= i and i <= len(rhs_cols))
-            Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
-            # invariants-end
-            cols.append(rhs_cols[i])
-            i = i + 1
+            cols.append(rhs.pk_col)
+        else:
+            rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
+            i = 0
+            while i < len(rhs_cols):
+                # invariants-start
+                Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
+                Invariant(rhs.has_fields)
+                Invariant(rhs.explicit_cols == orig_explicit)
+                Invariant(rhs_cols == nested_group_by_cols(rhs))
+                Invariant(rhs_cols == rhs.explicit_cols)
+                Invariant(Acc(list_pred(cols)))
+                Invariant(Acc(list_pred(lhs_cols), 1 / 2))
+                Invariant(0 <= i and i <= len(rhs_cols))
+                Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
+                # invariants-end
+                cols.append(rhs_cols[i])
+                i = i + 1
     return cols
     # impl-end
```

Attack 5 — `atk_5_gratuitous.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -148,9 +144,8 @@
     orig_pk = rhs.pk_col  # type: int
     cols = list(lhs_cols)  # type: List[int]
     if rhs_is_query:
-        if not rhs.has_fields:
-            clear_output_columns(rhs)
-            add_identity_column(rhs)
+        clear_output_columns(rhs)
+        add_identity_column(rhs)
         rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
         i = 0
         while i < len(rhs_cols):
@@ -159,18 +154,13 @@
             Invariant(rhs.has_fields)
             Invariant(rhs.default_cols == orig_default)
             Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
-            Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
-            Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
+            Invariant(rhs.explicit_cols == PSeq(rhs.pk_col))
             Invariant(rhs_cols == nested_group_by_cols(rhs))
             Invariant(rhs_cols == rhs.explicit_cols)
             Invariant(Acc(list_pred(cols)))
             Invariant(Acc(list_pred(lhs_cols), 1 / 2))
             Invariant(0 <= i and i <= len(rhs_cols))
             Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
             # invariants-end
             cols.append(rhs_cols[i])
             i = i + 1
```

Attack 6 — `atk_6_uncond.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -148,9 +144,9 @@
     orig_pk = rhs.pk_col  # type: int
     cols = list(lhs_cols)  # type: List[int]
     if rhs_is_query:
-        if not rhs.has_fields:
+        if rhs.has_fields:
             clear_output_columns(rhs)
-            add_identity_column(rhs)
+        add_identity_column(rhs)
         rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
         i = 0
         while i < len(rhs_cols):
@@ -159,18 +155,13 @@
             Invariant(rhs.has_fields)
             Invariant(rhs.default_cols == orig_default)
             Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
-            Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
-            Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
+            Invariant(rhs.explicit_cols == PSeq(rhs.pk_col))
             Invariant(rhs_cols == nested_group_by_cols(rhs))
             Invariant(rhs_cols == rhs.explicit_cols)
             Invariant(Acc(list_pred(cols)))
             Invariant(Acc(list_pred(lhs_cols), 1 / 2))
             Invariant(0 <= i and i <= len(rhs_cols))
             Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
             # invariants-end
             cols.append(rhs_cols[i])
             i = i + 1
```

Attack 7 — `atk_7_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -152,25 +148,22 @@
             clear_output_columns(rhs)
             add_identity_column(rhs)
         rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
-        i = 0
+        # BUG: skip the first rhs column (boundary/off-by-one)
+        i = 1
         while i < len(rhs_cols):
             # invariants-start
             Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
             Invariant(rhs.has_fields)
             Invariant(rhs.default_cols == orig_default)
             Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
             Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
             Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
             Invariant(rhs_cols == nested_group_by_cols(rhs))
             Invariant(rhs_cols == rhs.explicit_cols)
             Invariant(Acc(list_pred(cols)))
             Invariant(Acc(list_pred(lhs_cols), 1 / 2))
-            Invariant(0 <= i and i <= len(rhs_cols))
+            Invariant(1 <= i and i <= len(rhs_cols))
             Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
             # invariants-end
             cols.append(rhs_cols[i])
             i = i + 1
```

Attack 8 — `atk_8_clearonly.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class NestedQuery:
@@ -65,7 +64,6 @@
     query is left with no explicit output columns. Touches only the explicit
     output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(not q.has_fields)
     Ensures(q.default_cols == Old(q.default_cols))
@@ -79,7 +77,6 @@
     output columns, and those columns are exactly its identity column. Touches
     only the explicit output-column facet."""
     Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
-    Requires(MustTerminate(2))
     Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
     Ensures(q.has_fields)
     Ensures(q.explicit_cols == PSeq(q.pk_col))
@@ -98,7 +95,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(lhs_cols), 1 / 2))
     Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(lhs_cols), 1 / 2))
@@ -150,27 +146,18 @@
     if rhs_is_query:
         if not rhs.has_fields:
             clear_output_columns(rhs)
-            add_identity_column(rhs)
         rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
         i = 0
         while i < len(rhs_cols):
             # invariants-start
             Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
-            Invariant(rhs.has_fields)
             Invariant(rhs.default_cols == orig_default)
             Invariant(rhs.pk_col == orig_pk)
-            # An already-explicit rhs keeps its explicit columns untouched; a
-            # field-less rhs has been normalised so its explicit columns are
-            # exactly the identity column.
-            Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
-            Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
             Invariant(rhs_cols == nested_group_by_cols(rhs))
-            Invariant(rhs_cols == rhs.explicit_cols)
             Invariant(Acc(list_pred(cols)))
             Invariant(Acc(list_pred(lhs_cols), 1 / 2))
             Invariant(0 <= i and i <= len(rhs_cols))
             Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
-            Invariant(MustTerminate(len(rhs_cols) - i + 1))
             # invariants-end
             cols.append(rhs_cols[i])
             i = i + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14351.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test groups by a list of columns. The columns it contributes are
  the columns of its left-hand operand, followed by the columns contributed by
  its right-hand operand WHEN the right-hand operand is itself a column-bearing
  sub-expression (a nested query) rather than a plain literal collection.

  The subtlety this contract pins: a nested query that carries NO explicitly
  chosen output columns must, in this grouping position, contribute EXACTLY ONE
  column — its identity (primary-key) column — not the whole set of columns it
  would otherwise expose by default. Concretely, before reading the nested
  query's grouping columns the operation first normalises such a query so that
  its only output column is the identity column; only then are those columns
  appended. A nested query that already carries explicitly chosen output
  columns is left untouched and contributes exactly those chosen columns.

The left operand's columns are modelled as a read-only ``List[int]`` of column
identifiers. The nested query is modelled as a minimal mutable object carrying
only the touched facets: whether it has explicit output columns, the columns it
would expose by default, the explicit output columns it currently carries, and
its identity-column identifier. Its unchanged grouping-column reader and the
two unchanged normalisation primitives (clear-output-columns,
add-identity-column) are axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NestedQuery:
    def __init__(self, has_fields: bool, default_cols: PSeq[int],
                 explicit_cols: PSeq[int], pk_col: int) -> None:
        Ensures(Acc(self.has_fields) and self.has_fields == has_fields)          # type: ignore
        Ensures(Acc(self.default_cols) and self.default_cols is default_cols)    # type: ignore
        Ensures(Acc(self.explicit_cols) and self.explicit_cols is explicit_cols) # type: ignore
        Ensures(Acc(self.pk_col) and self.pk_col == pk_col)                      # type: ignore
        self.has_fields = has_fields
        self.default_cols = default_cols
        self.explicit_cols = explicit_cols
        self.pk_col = pk_col


# axioms-start
@Pure
@ContractOnly
def nested_group_by_cols(q: NestedQuery) -> PSeq[int]:
    """The unchanged grouping-column reader of the nested query (the callee the
    operation invokes but does not change). When the query carries explicit
    output columns it exposes exactly those chosen columns; otherwise it exposes
    its full default column set. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(Acc(q.has_fields, 1 / 2) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols, 1 / 2) and Acc(q.pk_col, 1 / 2))
    Ensures(Implies(q.has_fields, Result() == q.explicit_cols))
    Ensures(Implies(not q.has_fields, Result() == q.default_cols))


@ContractOnly
def clear_output_columns(q: NestedQuery) -> None:
    """Unchanged normalisation primitive: drop every chosen output column. The
    query is left with no explicit output columns. Touches only the explicit
    output-column facet."""
    Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(not q.has_fields)
    Ensures(q.default_cols == Old(q.default_cols))
    Ensures(q.pk_col == Old(q.pk_col))


@ContractOnly
def add_identity_column(q: NestedQuery) -> None:
    """Unchanged normalisation primitive: set the query's chosen output columns
    to be exactly its identity column. Afterwards the query carries explicit
    output columns, and those columns are exactly its identity column. Touches
    only the explicit output-column facet."""
    Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(q.has_fields)
    Ensures(q.explicit_cols == PSeq(q.pk_col))
    Ensures(q.pk_col == Old(q.pk_col))
    Ensures(q.default_cols == Old(q.default_cols))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def membership_group_by_cols(lhs_cols: List[int], rhs_is_query: bool,
                             rhs: NestedQuery) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lhs_cols), 1 / 2))
    Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lhs_cols), 1 / 2))
    Ensures(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The identity column and the default-column set are never invented or
    # dropped by the operation.
    Ensures(rhs.pk_col == Old(rhs.pk_col))
    Ensures(rhs.default_cols == Old(rhs.default_cols))
    # When the right operand is a plain literal collection (no grouping columns
    # of its own) the result is exactly the left operand's columns.
    Ensures(Implies(not rhs_is_query, ToSeq(Result()) == ToSeq(lhs_cols)))
    # When the right operand is a column-bearing nested query that already has
    # explicit output columns, it is left UNTOUCHED and contributes exactly
    # those explicit columns — whatever they are (not forced to the identity
    # column). The contribution is grounded in the query's own explicit-column
    # carrier, never an injected sentinel.
    Ensures(Implies(rhs_is_query and Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + Old(rhs.explicit_cols)))
    # The discriminating clause: a column-bearing nested query that carries NO
    # explicit output columns contributes EXACTLY ONE column — its identity
    # column — never its full default column set.
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + PSeq(rhs.pk_col)))
    # PRODUCED-BY (anti-fabrication): a field-less nested query must be left in
    # the normalised post-state — explicit output columns present and equal to
    # exactly the identity column — and the contributed columns must be the
    # reader's output on that post-state, not a fabricated constant.
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    rhs.has_fields and rhs.explicit_cols == PSeq(rhs.pk_col)))
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + nested_group_by_cols(rhs)))
    # FRAME (anti-gratuitous-mutation): the field-less normalisation is the ONLY
    # branch on which the nested query is touched. A plain literal right operand
    # is never a query to normalise, and a nested query that already carries
    # explicitly chosen output columns is left untouched — both its
    # explicit-column carrier and its explicit-columns flag are preserved.
    Ensures(Implies(not (rhs_is_query and not Old(rhs.has_fields)),
                    rhs.has_fields == Old(rhs.has_fields)))
    Ensures(Implies(not (rhs_is_query and not Old(rhs.has_fields)),
                    rhs.explicit_cols == Old(rhs.explicit_cols)))
    # post-conditions-end
    # impl-start
    orig_default = rhs.default_cols  # type: PSeq[int]
    orig_explicit = rhs.explicit_cols  # type: PSeq[int]
    orig_had_fields = rhs.has_fields  # type: bool
    orig_pk = rhs.pk_col  # type: int
    cols = list(lhs_cols)  # type: List[int]
    if rhs_is_query:
        if not rhs.has_fields:
            clear_output_columns(rhs)
            add_identity_column(rhs)
        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
        i = 0
        while i < len(rhs_cols):
            # invariants-start
            Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
            Invariant(rhs.has_fields)
            Invariant(rhs.default_cols == orig_default)
            Invariant(rhs.pk_col == orig_pk)
            # An already-explicit rhs keeps its explicit columns untouched; a
            # field-less rhs has been normalised so its explicit columns are
            # exactly the identity column.
            Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
            Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
            Invariant(rhs_cols == nested_group_by_cols(rhs))
            Invariant(rhs_cols == rhs.explicit_cols)
            Invariant(Acc(list_pred(cols)))
            Invariant(Acc(list_pred(lhs_cols), 1 / 2))
            Invariant(0 <= i and i <= len(rhs_cols))
            Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
            # invariants-end
            cols.append(rhs_cols[i])
            i = i + 1
    return cols
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14351 (nagini). env python; SBU_BENCHMARK_DIR=benchmark-verified; verifier scripts/nagini_verify.sh. Commands: `python -m swebench_unified.adversary same-spec|weakness nagini django__django-14351 <atk>`; resolve via swebench_unified.harness.run_resolve (harness.py, cache_level env, retries=1, timeout=1800).

SAME-SPEC: all 8 attacks + positive_control EXIT 0 (byte-identical spec; prepatch also EXIT 0).

### WEAKNESS (adversary weakness, run concurrently <=3/batch, each ~18-20s, all genuine — no timeouts):
- positive_control.py (gold model) => CANDIDATE (verifies 18.1s).
- atk_1_prepatch.py (bundle model_prepatch: no normalisation, appends full default_cols) => EXIT 2, does-not-verify. Fails the discriminating postcondition Result==lhs+PSeq(pk). G-DIFF holds; PREPATCH REPRODUCED.
- atk_2_skipclear.py (control-flow-effect: field-less branch calls ONLY add_identity_column, drops clear_output_columns) => EXIT 0 CANDIDATE (18.0s). add_identity_column alone establishes has_fields & explicit_cols==PSeq(pk) => P4/produced-by satisfied.
- atk_3_directassign.py (ungrounded-oracle echo: field-less branch directly assigns rhs.has_fields=True; rhs.explicit_cols=PSeq(pk) WITHOUT calling the axiom callees) => EXIT 0 CANDIDATE (19.5s). The spec's Acc(rhs.has_fields)/Acc(rhs.explicit_cols) full permission admits direct assignment; refinement.md's 'add_identity_column is the only producer' is a modeling narrative, not enforced by the contract — BUT the faithful realization is the same real operation (establish explicit pk output col), see resolve.
- atk_4_echo_fabricate.py (fabrication: append rhs.pk_col constant without mutating rhs) => EXIT 2 does-not-verify. Fails PRODUCED-BY/post-state clause (rhs.has_fields & explicit_cols==PSeq(pk)). GOOD.
- atk_5_gratuitous.py (gratuitous-mutation: normalise even already-explicit rhs) => EXIT 2 does-not-verify. Fails FRAME clause. GOOD.
- atk_6_uncond.py (unconditional clear+add for any query, forces explicit rhs to pk) => EXIT 2 does-not-verify. Fails grounded explicit-fields postcondition Result==lhs+Old(rhs.explicit_cols). Confirms SPEC_GUIDE-8 grounding is load-bearing. GOOD.
- atk_7_offbyone.py (boundary: skip first rhs col, start i=1) => EXIT 2 does-not-verify. Fails invariant/value clause. GOOD.
- atk_8_clearonly.py (partial: field-less branch calls ONLY clear_output_columns, no add) => EXIT 2 does-not-verify. Fails post-state (explicit_cols!=PSeq(pk)) & discriminating value clause. GOOD.

RESOLVE (official harness, run_resolve): atk_2 and atk_3 have BYTE-IDENTICAL faithful patches (both realize the abstract 'establish explicit pk output column without preceding clear' to `add_fields(['pk'])` without `clear_select_clause()` — add_fields->set_select sets default_cols=False and select=(pk,), so the F2P subquery Author.objects.filter(pk=a1.pk) collapses to exactly one rendered column; verified against real callees query.py:1861/1882/1893 and compiler.py:226 assert not (select and default_cols)). Ran ALL THREE + gold control:
- gold patch (patch_gold.diff, run sbu-eqaudit8-14351-gold): RESOLVED=True COMPLETED=True.
- atk_2 faithful patch (run sbu-eqaudit8-14351-atk2): RESOLVED=True COMPLETED=True.
- atk_3 faithful patch (run sbu-eqaudit8-14351-atk3): RESOLVED=True COMPLETED=True.

A-LEG / model<->patch audit: refinement.md tags steps 4/5/6 A-consumed, steps 1/2/3/7/8 R/I, NO kind-3, NO A-reference deep models — self-contained changed fn (In.get_group_by_cols) contracted as membership_group_by_cols; 3 unchanged callees axiomatized. Verified each A-consumed axiom vs real callee source @base_commit 06fd4df: clear_output_columns==clear_select_clause (query.py:1861), add_identity_column==add_fields(['pk'])->set_select (default_cols=False+select=(pk,)), nested_group_by_cols==Query.get_group_by_cols (G-AX/axiom_check.py 55 obs incl falsifying values('name')=>1 non-pk). All faithful. FRAME + PRODUCED-BY clauses are load-bearing (atk_4/5/6 rejected).

KEY FINDING: The spec decomposes normalisation into two independent axioms and grants full Acc on rhs facets, admitting verifying rivals that (a) drop clear_select_clause (atk_2) or (b) bypass the callees via direct assignment (atk_3). I MATERIALIZED and RAN both faithful patches (byte-identical) through the official harness; BOTH RESOLVED, as did the gold control. Therefore verify does NOT admit an incorrect impl on the tested path. No verifying wrong-impl's faithful patch fails to resolve.

VERDICT: SOUND. 8 same-spec attacks executed (2 verify+resolve, 6 rejected by spec incl reproduced prepatch), positive control + both verifying candidates' faithful patches resolve, gold control resolves. No break (verify => correct on tested inputs).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.py`, `atk_4_echo_fabricate.py`, `atk_5_gratuitous.py`, `atk_6_uncond.py`, `atk_7_offbyone.py`, `atk_8_clearonly.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_2_skipclear.py`, `atk_3_directassign.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_skipclear.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_directassign.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4_echo_fabricate.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_gratuitous.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_uncond.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_offbyone.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_clearonly.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14351.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A membership test groups by a list of columns. The columns it contributes are
  the columns of its left-hand operand, followed by the columns contributed by
  its right-hand operand WHEN the right-hand operand is itself a column-bearing
  sub-expression (a nested query) rather than a plain literal collection.

  The subtlety this contract pins: a nested query that carries NO explicitly
  chosen output columns must, in this grouping position, contribute EXACTLY ONE
  column — its identity (primary-key) column — not the whole set of columns it
  would otherwise expose by default. Concretely, before reading the nested
  query's grouping columns the operation first normalises such a query so that
  its only output column is the identity column; only then are those columns
  appended. A nested query that already carries explicitly chosen output
  columns is left untouched and contributes exactly those chosen columns.

The left operand's columns are modelled as a read-only ``List[int]`` of column
identifiers. The nested query is modelled as a minimal mutable object carrying
only the touched facets: whether it has explicit output columns, the columns it
would expose by default, the explicit output columns it currently carries, and
its identity-column identifier. Its unchanged grouping-column reader and the
two unchanged normalisation primitives (clear-output-columns,
add-identity-column) are axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NestedQuery:
    def __init__(self, has_fields: bool, default_cols: PSeq[int],
                 explicit_cols: PSeq[int], pk_col: int) -> None:
        Ensures(Acc(self.has_fields) and self.has_fields == has_fields)          # type: ignore
        Ensures(Acc(self.default_cols) and self.default_cols is default_cols)    # type: ignore
        Ensures(Acc(self.explicit_cols) and self.explicit_cols is explicit_cols) # type: ignore
        Ensures(Acc(self.pk_col) and self.pk_col == pk_col)                      # type: ignore
        self.has_fields = has_fields
        self.default_cols = default_cols
        self.explicit_cols = explicit_cols
        self.pk_col = pk_col


# axioms-start
@Pure
@ContractOnly
def nested_group_by_cols(q: NestedQuery) -> PSeq[int]:
    """The unchanged grouping-column reader of the nested query (the callee the
    operation invokes but does not change). When the query carries explicit
    output columns it exposes exactly those chosen columns; otherwise it exposes
    its full default column set. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(Acc(q.has_fields, 1 / 2) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols, 1 / 2) and Acc(q.pk_col, 1 / 2))
    Ensures(Implies(q.has_fields, Result() == q.explicit_cols))
    Ensures(Implies(not q.has_fields, Result() == q.default_cols))


@ContractOnly
def clear_output_columns(q: NestedQuery) -> None:
    """Unchanged normalisation primitive: drop every chosen output column. The
    query is left with no explicit output columns. Touches only the explicit
    output-column facet."""
    Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(not q.has_fields)
    Ensures(q.default_cols == Old(q.default_cols))
    Ensures(q.pk_col == Old(q.pk_col))


@ContractOnly
def add_identity_column(q: NestedQuery) -> None:
    """Unchanged normalisation primitive: set the query's chosen output columns
    to be exactly its identity column. Afterwards the query carries explicit
    output columns, and those columns are exactly its identity column. Touches
    only the explicit output-column facet."""
    Requires(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(Acc(q.has_fields) and Acc(q.default_cols, 1 / 2) and Acc(q.explicit_cols) and Acc(q.pk_col, 1 / 2))
    Ensures(q.has_fields)
    Ensures(q.explicit_cols == PSeq(q.pk_col))
    Ensures(q.pk_col == Old(q.pk_col))
    Ensures(q.default_cols == Old(q.default_cols))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def membership_group_by_cols(lhs_cols: List[int], rhs_is_query: bool,
                             rhs: NestedQuery) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(lhs_cols), 1 / 2))
    Requires(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lhs_cols), 1 / 2))
    Ensures(Acc(rhs.has_fields) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols) and Acc(rhs.pk_col, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The identity column and the default-column set are never invented or
    # dropped by the operation.
    Ensures(rhs.pk_col == Old(rhs.pk_col))
    Ensures(rhs.default_cols == Old(rhs.default_cols))
    # When the right operand is a plain literal collection (no grouping columns
    # of its own) the result is exactly the left operand's columns.
    Ensures(Implies(not rhs_is_query, ToSeq(Result()) == ToSeq(lhs_cols)))
    # When the right operand is a column-bearing nested query that already has
    # explicit output columns, it is left UNTOUCHED and contributes exactly
    # those explicit columns — whatever they are (not forced to the identity
    # column). The contribution is grounded in the query's own explicit-column
    # carrier, never an injected sentinel.
    Ensures(Implies(rhs_is_query and Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + Old(rhs.explicit_cols)))
    # The discriminating clause: a column-bearing nested query that carries NO
    # explicit output columns contributes EXACTLY ONE column — its identity
    # column — never its full default column set.
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + PSeq(rhs.pk_col)))
    # PRODUCED-BY (anti-fabrication): a field-less nested query must be left in
    # the normalised post-state — explicit output columns present and equal to
    # exactly the identity column — and the contributed columns must be the
    # reader's output on that post-state, not a fabricated constant.
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    rhs.has_fields and rhs.explicit_cols == PSeq(rhs.pk_col)))
    Ensures(Implies(rhs_is_query and not Old(rhs.has_fields),
                    ToSeq(Result()) == ToSeq(lhs_cols) + nested_group_by_cols(rhs)))
    # FRAME (anti-gratuitous-mutation): the field-less normalisation is the ONLY
    # branch on which the nested query is touched. A plain literal right operand
    # is never a query to normalise, and a nested query that already carries
    # explicitly chosen output columns is left untouched — both its
    # explicit-column carrier and its explicit-columns flag are preserved.
    Ensures(Implies(not (rhs_is_query and not Old(rhs.has_fields)),
                    rhs.has_fields == Old(rhs.has_fields)))
    Ensures(Implies(not (rhs_is_query and not Old(rhs.has_fields)),
                    rhs.explicit_cols == Old(rhs.explicit_cols)))
    # post-conditions-end
    # impl-start
    orig_default = rhs.default_cols  # type: PSeq[int]
    orig_explicit = rhs.explicit_cols  # type: PSeq[int]
    orig_had_fields = rhs.has_fields  # type: bool
    orig_pk = rhs.pk_col  # type: int
    cols = list(lhs_cols)  # type: List[int]
    if rhs_is_query:
        if not rhs.has_fields:
            clear_output_columns(rhs)
            add_identity_column(rhs)
        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
        i = 0
        while i < len(rhs_cols):
            # invariants-start
            Invariant(Acc(rhs.has_fields, 1 / 2) and Acc(rhs.default_cols, 1 / 2) and Acc(rhs.explicit_cols, 1 / 2) and Acc(rhs.pk_col, 1 / 2))
            Invariant(rhs.has_fields)
            Invariant(rhs.default_cols == orig_default)
            Invariant(rhs.pk_col == orig_pk)
            # An already-explicit rhs keeps its explicit columns untouched; a
            # field-less rhs has been normalised so its explicit columns are
            # exactly the identity column.
            Invariant(Implies(orig_had_fields, rhs.explicit_cols == orig_explicit))
            Invariant(Implies(not orig_had_fields, rhs.explicit_cols == PSeq(rhs.pk_col)))
            Invariant(rhs_cols == nested_group_by_cols(rhs))
            Invariant(rhs_cols == rhs.explicit_cols)
            Invariant(Acc(list_pred(cols)))
            Invariant(Acc(list_pred(lhs_cols), 1 / 2))
            Invariant(0 <= i and i <= len(rhs_cols))
            Invariant(ToSeq(cols) == ToSeq(lhs_cols) + rhs_cols.take(i))
            # invariants-end
            cols.append(rhs_cols[i])
            i = i + 1
    return cols
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14351 (nagini). env python; SBU_BENCHMARK_DIR=benchmark-verified; verifier scripts/nagini_verify.sh. Commands: `python -m swebench_unified.adversary same-spec|weakness nagini django__django-14351 <atk>`; resolve via swebench_unified.harness.run_resolve (harness.py, cache_level env, retries=1, timeout=1800).

SAME-SPEC: all 8 attacks + positive_control EXIT 0 (byte-identical spec; prepatch also EXIT 0).

### WEAKNESS (adversary weakness, run concurrently <=3/batch, each ~18-20s, all genuine — no timeouts):
- positive_control.py (gold model) => CANDIDATE (verifies 18.1s).
- atk_1_prepatch.py (bundle model_prepatch: no normalisation, appends full default_cols) => EXIT 2, does-not-verify. Fails the discriminating postcondition Result==lhs+PSeq(pk). G-DIFF holds; PREPATCH REPRODUCED.
- atk_2_skipclear.py (control-flow-effect: field-less branch calls ONLY add_identity_column, drops clear_output_columns) => EXIT 0 CANDIDATE (18.0s). add_identity_column alone establishes has_fields & explicit_cols==PSeq(pk) => P4/produced-by satisfied.
- atk_3_directassign.py (ungrounded-oracle echo: field-less branch directly assigns rhs.has_fields=True; rhs.explicit_cols=PSeq(pk) WITHOUT calling the axiom callees) => EXIT 0 CANDIDATE (19.5s). The spec's Acc(rhs.has_fields)/Acc(rhs.explicit_cols) full permission admits direct assignment; refinement.md's 'add_identity_column is the only producer' is a modeling narrative, not enforced by the contract — BUT the faithful realization is the same real operation (establish explicit pk output col), see resolve.
- atk_4_echo_fabricate.py (fabrication: append rhs.pk_col constant without mutating rhs) => EXIT 2 does-not-verify. Fails PRODUCED-BY/post-state clause (rhs.has_fields & explicit_cols==PSeq(pk)). GOOD.
- atk_5_gratuitous.py (gratuitous-mutation: normalise even already-explicit rhs) => EXIT 2 does-not-verify. Fails FRAME clause. GOOD.
- atk_6_uncond.py (unconditional clear+add for any query, forces explicit rhs to pk) => EXIT 2 does-not-verify. Fails grounded explicit-fields postcondition Result==lhs+Old(rhs.explicit_cols). Confirms SPEC_GUIDE-8 grounding is load-bearing. GOOD.
- atk_7_offbyone.py (boundary: skip first rhs col, start i=1) => EXIT 2 does-not-verify. Fails invariant/value clause. GOOD.
- atk_8_clearonly.py (partial: field-less branch calls ONLY clear_output_columns, no add) => EXIT 2 does-not-verify. Fails post-state (explicit_cols!=PSeq(pk)) & discriminating value clause. GOOD.

RESOLVE (official harness, run_resolve): atk_2 and atk_3 have BYTE-IDENTICAL faithful patches (both realize the abstract 'establish explicit pk output column without preceding clear' to `add_fields(['pk'])` without `clear_select_clause()` — add_fields->set_select sets default_cols=False and select=(pk,), so the F2P subquery Author.objects.filter(pk=a1.pk) collapses to exactly one rendered column; verified against real callees query.py:1861/1882/1893 and compiler.py:226 assert not (select and default_cols)). Ran ALL THREE + gold control:
- gold patch (patch_gold.diff, run sbu-eqaudit8-14351-gold): RESOLVED=True COMPLETED=True.
- atk_2 faithful patch (run sbu-eqaudit8-14351-atk2): RESOLVED=True COMPLETED=True.
- atk_3 faithful patch (run sbu-eqaudit8-14351-atk3): RESOLVED=True COMPLETED=True.

A-LEG / model<->patch audit: refinement.md tags steps 4/5/6 A-consumed, steps 1/2/3/7/8 R/I, NO kind-3, NO A-reference deep models — self-contained changed fn (In.get_group_by_cols) contracted as membership_group_by_cols; 3 unchanged callees axiomatized. Verified each A-consumed axiom vs real callee source @base_commit 06fd4df: clear_output_columns==clear_select_clause (query.py:1861), add_identity_column==add_fields(['pk'])->set_select (default_cols=False+select=(pk,)), nested_group_by_cols==Query.get_group_by_cols (G-AX/axiom_check.py 55 obs incl falsifying values('name')=>1 non-pk). All faithful. FRAME + PRODUCED-BY clauses are load-bearing (atk_4/5/6 rejected).

KEY FINDING: The spec decomposes normalisation into two independent axioms and grants full Acc on rhs facets, admitting verifying rivals that (a) drop clear_select_clause (atk_2) or (b) bypass the callees via direct assignment (atk_3). I MATERIALIZED and RAN both faithful patches (byte-identical) through the official harness; BOTH RESOLVED, as did the gold control. Therefore verify does NOT admit an incorrect impl on the tested path. No verifying wrong-impl's faithful patch fails to resolve.

VERDICT: SOUND. 8 same-spec attacks executed (2 verify+resolve, 6 rejected by spec incl reproduced prepatch), positive control + both verifying candidates' faithful patches resolve, gold control resolves. No break (verify => correct on tested inputs).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-14351 nagini bundle. VERDICT: FAITHFUL — no input where the modeled function disagrees with the real callee.

Evidence:
1. Model VERIFIES under pinned Nagini (scripts/nagini_verify.sh: 'Verification successful', 16.48s). Since membership_group_by_cols's impl mirrors the gold In.get_group_by_cols op-for-op (refinement.md steps 1-8), gold satisfies every postcondition => spec is NOT too strong for gold.
2. same-spec on the model itself returns SAME (exit 0): the spec region is exactly the bundle's.
3. axiom_check.py run AGAINST THE REAL REPO at base_commit 06fd4df4 (django 4.0.dev20210608) passes with 55 observations: field-less query => 7 default cols; after clear_select_clause()+add_fields(['pk']) => exactly 1 pk col; explicit shapes values('name')=>1 NON-pk col, values('id','name')=>2 cols, values('pk')=>1 col. This validates all three A-consumed axioms (nested_group_by_cols, clear_output_columns, add_identity_column) against the actual Query callees.

Postcondition-by-postcondition vs gold In.get_group_by_cols (lookups.py, new override):
- not rhs_is_query => result == lhs_cols: gold returns self.lhs.get_group_by_cols() (no hasattr). Faithful.
- rhs_is_query & Old(has_fields) => lhs + Old(explicit_cols): gold skips normalisation, extends with the reader's own chosen columns. Correctly GROUNDED in explicit_cols (not over-claimed to pk; axiom_check exercises the falsifying values('name')/values('id','name') shapes that a too-strong has_fields=>PSeq(pk_col) reading would wrongly reject). Faithful, and notably NOT too strong.
- rhs_is_query & not Old(has_fields) => lhs + PSeq(pk_col): gold normalises (clear+add pk) then reads => exactly 1 pk col (validated rendered select==1). Faithful.
- produced-by post-state (has_fields & explicit_cols==PSeq(pk_col)) + frame clauses: gold mutates self.rhs ONLY inside the 'if not has_select_fields' guard; untouched otherwise. Exactly gold's write-footprint. Faithful.

The earlier over-strong revision (has_fields => PSeq(pk_col)) was already corrected to the grounded explicit_cols form; axiom_check actively falsifies the over-claim. No spec clause is stronger than the real behaviour on any Requires-satisfying input. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py (bundle.solution_src()). Lexical G-LEAK screen passes (rep.passed=True, no hard failures); meta records G-LEAK=pass, relaxed_leakage=None, no RELAXED_LEAKAGE.md (so no relaxed-deferral applies). Semantic judgment beyond public problem_statement (excluding hints_text): the model.py spec region uses only abstracted symbols (membership_group_by_cols, nested_group_by_cols, clear_output_columns, add_identity_column, NestedQuery, has_fields/explicit_cols/default_cols/pk_col) and contains NONE of the repo-specific gold tokens (get_group_by_cols, clear_select_clause, add_fields(['pk']), has_select_fields, the In lookup, lookups.py). The discriminating behavior it pins — a field-less nested query contributes EXACTLY ONE column (its identity/pk column) rather than its full default column set, while an already-explicit query is left untouched and contributes its own columns — is already fully disclosed in the PUBLIC problem_statement, which describes the 'subquery must return only one column' error, the all-columns-vs-one-id contrast between agent__property_groups__in and agent__property_groups__id__in, and even a hack fix collapsing cols to a single column. The produced-by (anti-fabrication) and frame (anti-gratuitous-mutation) postconditions strengthen the spec against echo/mutation rivals but remain abstract behavioral constraints; they do not name gold callees or reveal an implementation path unavailable from the public statement. No spec-view line reveals the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
