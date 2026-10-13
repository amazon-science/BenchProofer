# P2 adversarial audit — django__django-16082

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `atk_0.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation verified. The only CANDIDATE (exit 0) was the positive control atk_0.py, whose impl region is code-identical to the bundle's model.py (differs only in the explanatory comment block), so its faithful refined patch IS the gold patch; it was materialized and executed through the official harness: run_resolve('django__django-16082', faithful_atk_0.patch) => RESOLVED: True, note 'resolved'. Every one of the 10 distinct wrong impls came back exit 2 (NOT-A-COUNTEREXAMPLE: shares the spec but fails verification), i.e. the spec rejected each. verify => correct is not falsified here.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
@@ -394,7 +382,7 @@
             return T_FLT
         if row(T_DEC, T_DEC, lhs_type, rhs_type):
             return T_DEC
-    if records_mixed_numeric(connector):
+    if records_mixed_numeric(connector) and connector != C_MOD:
         if row(T_INT, T_DEC, lhs_type, rhs_type):
             return T_DEC
         if row(T_DEC, T_INT, lhs_type, rhs_type):
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
@@ -395,13 +383,17 @@
         if row(T_DEC, T_DEC, lhs_type, rhs_type):
             return T_DEC
     if records_mixed_numeric(connector):
-        if row(T_INT, T_DEC, lhs_type, rhs_type):
+        fin_l = (lhs_type == T_INT or lhs_type == 9 or lhs_type == 10
+                 or lhs_type == 11)
+        fin_r = (rhs_type == T_INT or rhs_type == 9 or rhs_type == 10
+                 or rhs_type == 11)
+        if fin_l and rhs_type == T_DEC:
             return T_DEC
-        if row(T_DEC, T_INT, lhs_type, rhs_type):
+        if lhs_type == T_DEC and fin_r:
             return T_DEC
-        if row(T_INT, T_FLT, lhs_type, rhs_type):
+        if fin_l and rhs_type == T_FLT:
             return T_FLT
-        if row(T_FLT, T_INT, lhs_type, rhs_type):
+        if lhs_type == T_FLT and fin_r:
             return T_FLT
     if records_same_type_numeric(connector):
         if row(T_FLT, T_NULL, lhs_type, rhs_type):
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,20 +375,10 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
+    off_l = (lhs_type == T_INT or lhs_type >= T_INT_SUB + 1)
+    off_r = (rhs_type == T_INT or rhs_type >= T_INT_SUB + 1)
     if records_same_type_numeric(connector):
-        if row(T_INT, T_INT, lhs_type, rhs_type):
+        if off_l and off_r:
             return T_INT
         if row(T_FLT, T_FLT, lhs_type, rhs_type):
             return T_FLT
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,63 +375,57 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
-    if records_same_type_numeric(connector):
-        if row(T_INT, T_INT, lhs_type, rhs_type):
-            return T_INT
-        if row(T_FLT, T_FLT, lhs_type, rhs_type):
-            return T_FLT
-        if row(T_DEC, T_DEC, lhs_type, rhs_type):
-            return T_DEC
-    if records_mixed_numeric(connector):
-        if row(T_INT, T_DEC, lhs_type, rhs_type):
-            return T_DEC
-        if row(T_DEC, T_INT, lhs_type, rhs_type):
-            return T_DEC
-        if row(T_INT, T_FLT, lhs_type, rhs_type):
-            return T_FLT
-        if row(T_FLT, T_INT, lhs_type, rhs_type):
-            return T_FLT
-    if records_same_type_numeric(connector):
-        if row(T_FLT, T_NULL, lhs_type, rhs_type):
-            return T_FLT
-        if row(T_NULL, T_FLT, lhs_type, rhs_type):
-            return T_FLT
-    if records_bitwise_integer(connector):
-        if row(T_INT, T_INT, lhs_type, rhs_type):
-            return T_INT
-    if connector == C_ADD:
-        if row(T_DATE, T_DUR, lhs_type, rhs_type):
-            return T_DTM
-        if row(T_DUR, T_DATE, lhs_type, rhs_type):
-            return T_DTM
-        if row(T_DUR, T_DUR, lhs_type, rhs_type):
-            return T_DUR
-        if row(T_TIME, T_DUR, lhs_type, rhs_type):
-            return T_TIME
-        if row(T_DUR, T_TIME, lhs_type, rhs_type):
-            return T_TIME
-    if connector == C_SUB:
-        if row(T_DATE, T_DUR, lhs_type, rhs_type):
-            return T_DTM
-        if row(T_DATE, T_DATE, lhs_type, rhs_type):
-            return T_DUR
-        if row(T_DUR, T_DUR, lhs_type, rhs_type):
-            return T_DUR
-        if row(T_TIME, T_DUR, lhs_type, rhs_type):
-            return T_TIME
-        if row(T_TIME, T_TIME, lhs_type, rhs_type):
-            return T_DUR
+    budget = 24 - lhs_type
+    matched = T_NONE
+    while budget > 0:
+        Invariant(MustTerminate(2))
+        Invariant(is_result_type(matched))
+        if records_same_type_numeric(connector):
+            if row(T_INT, T_INT, lhs_type, rhs_type):
+                matched = T_INT
+            elif row(T_FLT, T_FLT, lhs_type, rhs_type):
+                matched = T_FLT
+            elif row(T_DEC, T_DEC, lhs_type, rhs_type):
+                matched = T_DEC
+        if matched == T_NONE and records_mixed_numeric(connector):
+            if row(T_INT, T_DEC, lhs_type, rhs_type):
+                matched = T_DEC
+            elif row(T_DEC, T_INT, lhs_type, rhs_type):
+                matched = T_DEC
+            elif row(T_INT, T_FLT, lhs_type, rhs_type):
+                matched = T_FLT
+            elif row(T_FLT, T_INT, lhs_type, rhs_type):
+                matched = T_FLT
+        if matched == T_NONE and records_same_type_numeric(connector):
+            if row(T_FLT, T_NULL, lhs_type, rhs_type):
+                matched = T_FLT
+            elif row(T_NULL, T_FLT, lhs_type, rhs_type):
+                matched = T_FLT
+        if matched == T_NONE and records_bitwise_integer(connector):
+            if row(T_INT, T_INT, lhs_type, rhs_type):
+                matched = T_INT
+        if matched == T_NONE and connector == C_ADD:
+            if row(T_DATE, T_DUR, lhs_type, rhs_type):
+                matched = T_DTM
+            elif row(T_DUR, T_DATE, lhs_type, rhs_type):
+                matched = T_DTM
+            elif row(T_DUR, T_DUR, lhs_type, rhs_type):
+                matched = T_DUR
+            elif row(T_TIME, T_DUR, lhs_type, rhs_type):
+                matched = T_TIME
+            elif row(T_DUR, T_TIME, lhs_type, rhs_type):
+                matched = T_TIME
+        if matched == T_NONE and connector == C_SUB:
+            if row(T_DATE, T_DUR, lhs_type, rhs_type):
+                matched = T_DTM
+            elif row(T_DATE, T_DATE, lhs_type, rhs_type):
+                matched = T_DUR
+            elif row(T_DUR, T_DUR, lhs_type, rhs_type):
+                matched = T_DUR
+            elif row(T_TIME, T_DUR, lhs_type, rhs_type):
+                matched = T_TIME
+            elif row(T_TIME, T_TIME, lhs_type, rhs_type):
+                matched = T_DUR
+        return matched
     return T_NONE
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,21 +375,11 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
-            return T_INT
+            if lhs_type >= rhs_type:
+                return lhs_type
+            return rhs_type
         if row(T_FLT, T_FLT, lhs_type, rhs_type):
             return T_FLT
         if row(T_DEC, T_DEC, lhs_type, rhs_type):
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
@@ -402,6 +390,10 @@
         if row(T_INT, T_FLT, lhs_type, rhs_type):
             return T_FLT
         if row(T_FLT, T_INT, lhs_type, rhs_type):
+            return T_FLT
+        if row(T_DEC, T_FLT, lhs_type, rhs_type):
+            return T_FLT
+        if row(T_FLT, T_DEC, lhs_type, rhs_type):
             return T_FLT
     if records_same_type_numeric(connector):
         if row(T_FLT, T_NULL, lhs_type, rhs_type):
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
@@ -394,7 +382,7 @@
             return T_FLT
         if row(T_DEC, T_DEC, lhs_type, rhs_type):
             return T_DEC
-    if records_mixed_numeric(connector):
+    if records_same_type_numeric(connector):
         if row(T_INT, T_DEC, lhs_type, rhs_type):
             return T_DEC
         if row(T_DEC, T_INT, lhs_type, rhs_type):
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
@@ -404,6 +392,14 @@
         if row(T_FLT, T_INT, lhs_type, rhs_type):
             return T_FLT
     if records_same_type_numeric(connector):
+        if row(T_INT, T_NULL, lhs_type, rhs_type):
+            return T_INT
+        if row(T_NULL, T_INT, lhs_type, rhs_type):
+            return T_INT
+        if row(T_DEC, T_NULL, lhs_type, rhs_type):
+            return T_DEC
+        if row(T_NULL, T_DEC, lhs_type, rhs_type):
+            return T_DEC
         if row(T_FLT, T_NULL, lhs_type, rhs_type):
             return T_FLT
         if row(T_NULL, T_FLT, lhs_type, rhs_type):
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
@@ -425,6 +413,8 @@
     if connector == C_SUB:
         if row(T_DATE, T_DUR, lhs_type, rhs_type):
             return T_DTM
+        if row(T_DUR, T_DATE, lhs_type, rhs_type):
+            return T_DTM
         if row(T_DATE, T_DATE, lhs_type, rhs_type):
             return T_DUR
         if row(T_DUR, T_DUR, lhs_type, rhs_type):
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,7 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
+    Assert(False)
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
```

Prepatch bug re-encoded as an attack: `True`.

### 0. PRE-FLIGHT: MECHANICAL HOLE SEARCH (hole_search.py)
Before writing any attack I transcribed all 30 Ensures clauses into a standalone evaluator and enumerated the domain (connector codes -4..15 x operand codes -4..13 minus the sentinel = 5780 points), asking at each point how many of the 7 admissible result values satisfy the whole conjunction.
  `cd  && python hole_search.py`
  -> points: 5780 | gold violates spec at: 0 | UNDERDETERMINED points: 0
The postcondition set is POINTWISE TOTAL: at every point of the (open) domain exactly ONE result value is admissible, and it is the gold cascade's. The totality biconditional `has_permitted_combination(...) == (Result() != T_NONE)` plus the per-family clauses leave no free cell, so any same-spec impl that verifies must be extensionally equal to the gold cascade on the whole carrier. This predicted SOUND; I then attempted real falsification rather than stopping here.

### 1. SAME-SPEC BYTE-IDENTITY (all 11 files)
`python -m swebench_unified.adversary same-spec nagini django__django-16082 <file>` -> exit=0 for atk_0..atk_10. Every attack edits ONLY the impl region; the axioms/@Pure/Requires/Ensures regions are byte-identical (spec-region sha1 983d31135d04caf0f936b66ea54ef122b2fb927f).

### 2. ATTACKS: command + observed result
Command for each: `python -m swebench_unified.adversary weakness nagini django__django-16082 atk_N.py` (run 3-at-a-time as background jobs; logs at w_N.log). Exit 0 = CANDIDATE, exit 2 = rejected.

- atk_0.py POSITIVE CONTROL (gold impl verbatim): exit=0 'CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (29.5s)'. Expected — this is the correct impl; the spec is satisfiable and non-vacuous. Its faithful patch = gold patch, RESOLVED: True (see section 3).
- atk_1.py PREPATCH BUG (the mixed-numeric row block guarded with `and connector != C_MOD`, reproducing the pre-patch registry where Combinable.MOD is absent from the different-type dict's connector tuple): exit=2 NOT-A-COUNTEREXAMPLE, verification failed. PREPATCH REPRODUCED = the spec senses the change (G-DIFF): for MOD with integer-kind/decimal operands the prepatch cascade returns the sentinel, violating both the totality biconditional and the mixed-numeric clause.
- atk_2.py PARTIAL DOMAIN (mixed rows' integer arm replaced by a FINITE enumeration `lhs_type == T_INT or == 9 or == 10 or == 11` instead of the open band `is_int_kind`): exit=2 rejected. The open band cannot be discharged by any finite normalization table — code 12+ is a witness. This is the classic partial-domain evasion and the spec kills it.
- atk_3.py BOUNDARY (off-by-one on the open band: `t >= T_INT_SUB + 1`, excluding exactly the auto-increment code T_AUTO = T_INT_SUB = 9 from the integer family): exit=2 rejected. The band's lower boundary is pinned.
- atk_4.py CONTROL-FLOW EFFECT (the whole cascade wrapped in a `while budget > 0` loop with `budget = 24 - lhs_type`, so large integer-family codes exit with the sentinel; accumulator variable + MustTerminate/is_result_type invariants instead of straight-line returns): exit=2 rejected. A control-flow/effect rewrite that changes behaviour only in the open tail of the band is still caught.
- atk_5.py UNGROUNDED-ORACLE ECHO (for a matching (int,int) row, return `max(lhs_type, rhs_type)` — the queried operand's OWN code — instead of the RECORDED result type T_INT, i.e. 'compute a width' rather than 'look up the registry'): exit=2 rejected by `is_result_type(Result())` + the same-type-numeric clause. This is the leg refinement.md D claims ('the result can never be an echo of an operand's own code') and it holds mechanically.
- atk_6.py EXTRA RECORDED ROW (adds (dec,flt)->flt and (flt,dec)->flt widening, which the registry deliberately does NOT record): exit=2 rejected by clause (3).
- atk_7.py WRONG CONNECTOR SET (mixed rows guarded by records_same_type_numeric instead of records_mixed_numeric, so exponentiation wrongly gets the mixed rows): exit=2 rejected by clause (4). The MOD-vs-POW distinction — the crux of this instance, since both must be treated differently in the mixed dict — is pinned in BOTH directions (atk_1 removes MOD, atk_7 adds POW; both rejected).
- atk_8.py NULL-ROW OVERWRITE SUBTLETY (records the integer and decimal NULL rows alongside the float ones, i.e. reading the numeric-with-NULL comprehension as if the inner `for field_type in (Integer, Decimal, Float)` did NOT overwrite per connector): exit=2 rejected by clause (5). mapping.md's note at expressions.py:566 about only the FloatField NULL rows surviving is load-bearing and enforced.
- atk_9.py DATE/TIME ASYMMETRY (subtraction also accepts a duration on the LEFT of a date-family operand — a row the real registry does not record): exit=2 rejected by clause (7)'s `connector == C_SUB and lhs_type == T_DUR and is_date_kind(rhs_type) => T_NONE`.
- atk_10.py VACUITY CONTROL (`Assert(False)` at the head of the gold impl): exit=2 rejected — the precondition is SATISFIABLE, so the proof is not vacuous. (Per the known failure mode where an infeasible guard verifies while proving nothing; Assert(False) is the control and it correctly fails.)

Count: 10 distinct wrong impls (prepatch bug + 9 others spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, extra row, wrong connector set, null-row overwrite, date/time asymmetry, vacuity) + 1 positive control. >= 5 required; none broke the spec.

### 3. MANDATORY RESOLVE RUN for every CANDIDATE
Exactly one file came back CANDIDATE: atk_0.py. `diff atk_0.py model.py` shows the ONLY difference is model.py's 12-line explanatory comment inside the impl region — the executable impl is identical — so its faithful refined patch is the gold patch verbatim (staged as faithful_atk_0.patch, 356 bytes).
  `python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-16082', open('faithful_atk_0.patch').read()); print(r.resolved, r.note)"`
  -> EXECUTED RESULT: RESOLVED: True, NOTE: 'resolved' (log: resolve_atk_0.log)
No verifying impl's faithful patch failed to resolve, so verify=>correct is NOT falsified. Nothing speculative here: the one required resolve run was actually executed and is reported.

### 4. A-LEG AUDIT (the focus of this pass)
refinement.md leg tags: 2 R (B1 param/type refinement, B4 None<->T_NONE) + 2 A-reference (B2 registry cascade, B3 is_subtype<->issubclass). 0 A-consumed, 0 kind-3. Consistent with `grep -c ContractOnly model.py` = 0 and with the impl region containing ZERO Assume/Inhale/Exhale/Assert tokens — nothing is smuggled in as an assumption, so there is no dead or unsound consumed axiom and no unexpressible-changed-op step. The changed operation (the registry rows for Combinable.MOD) is genuinely modeled DEEPLY as the spelled-out cascade, not hidden behind an axiom of the function under change; section E's claim checks out.

(a) Bundle's own G-AX, run against the REAL post-patch source (worktree at base_commit + gold patch applied):
  `cd dj && PYTHONPATH=$PWD python .../axiom_check.py` -> exit=0, 'G-AX OK: ... 200 (queried class, recorded class) pairs ... 9 members ... 9375 observations ... 25 field classes squared'. Its self-reported counts match mapping.md 3.1/3.2 exactly (200 pairs, 9-member integer family, 9375 observations).

(b) INDEPENDENT re-derivation (my_ax.py) — I did not trust axiom_check.py's own bridge or assertions, and specifically probed the concern that its domain is a CURATED 25 classes (8 recorded + 9 integer subs + 8 hand-listed 'unrelated') rather than the whole hierarchy. My script discovers ALL 39 real Field subclasses (importing json/files/related/proxy/contenttypes/reverse_related modules) and checks:
  * CARRIER COMPLETENESS: for each real class I computed its subtype-signature against the 8 recorded operand types and asked whether SOME model code reproduces it. Result: 'real classes NOT representable by any model code: 0'. There are exactly 8 distinct real signatures and each maps onto the carrier: 23 classes with an all-False signature (GenericRelation, BinaryField, BooleanField, CharField, ...) -> the open band t <= T_UNREL_TOP; 10 classes with the integer signature (AutoField, BigAutoField, BigIntegerField, IntegerField, ...) -> T_INT / the open band t >= T_INT_SUB; and one class each for Date, DateTime, Decimal, Duration, Float, Time. So the two OPEN bands are genuinely the right abstraction and no real class falls outside the carrier — the 14 classes G-AX omits all share a signature with one it covers, so the omission is not a gap.
  * CASCADE == REAL CALLEE over every discovered class squared x 15 connectors (11 registered + 4 unregistered), evaluating the model at EVERY code representing each class: 630,375 observations (vs G-AX's 9,375) -> 'cascade != real callee at: 0'. Also 'real returned an out-of-model type at: 0', confirming the is_result_type containment claim against the real callee.
  VERDICT: A-LEG CORRESPONDENCE HOLDS.

(c) Correspondence of the A-legs to the real callees, read against the source at base_commit (expressions.py:503-628, extracted with git cat-file):
  * B3 / mapping 3.1: the scan really is `issubclass(lhs_type, combinator_lhs_type) and issubclass(rhs_type, combinator_rhs_type)` (expressions.py:625-627), an UNCHANGED primitive — the gold patch touches only the connector tuple. is_subtype's three arms (integer band, date arm covering DateTimeField, identity otherwise) match issubclass on all 39x8 real pairs. Correct A-reference, correctly NOT consumed.
  * B2 / mapping 3.2: the registry data really is built by flattening _connector_combinations via register_combinable_fields into _connector_combinators, scanned by a fixed-order `for ... in combinators` returning the first match (expressions.py:621-628) — so 'straight-line cascade in registration order, first match wins' is a faithful deep model of a fixed-length ordered iteration. I verified the row inventory mapping.md 3.2 lists against the real source: the model's 5 ADD rows / 5 SUB rows are the correct COLLAPSE of the real 7 ADD / 9 SUB rows, because the extra real rows are exactly the DateTimeField duplicates that the date-arm subtype match already covers (real (DateTime,Duration)->DateTime is subsumed by model row(T_DATE,T_DUR); real (Date,DateTime)/(DateTime,Date)/(DateTime,DateTime)->Duration under SUB are subsumed by model row(T_DATE,T_DATE)). The 630,375-observation sweep confirms the collapse is extensionally exact, not merely plausible. mapping.md's note that only the FloatField NULL rows survive the comprehension's per-connector overwrite is also confirmed by the sweep and independently pinned by atk_8's rejection.
  * Ordering fidelity: the same-type rows precede the mixed rows in both the real registry and the cascade, which is why an integer/integer query yields Integer rather than falling into a mixed row — behaviourally checked in the sweep.
  * mapping.md 'Flag dependency: none' is right: resolution is over class objects and string keys only, no float-precision or quote=-style callee flag.

### 5. Residual risk / honest caveats
- The carrier collapses each connector string to a code; C_POW=6 vs the bitwise codes are distinguished, and unregistered codes are covered by clause (9) plus 4 unregistered strings in G-AX. The precondition admits EVERY connector code, so no in-repo call site is modelled away.
- One deliberate soundness-preserving simplification: the model omits the real DateTimeField-specific duplicate rows, relying on the date-arm subtype match to cover them. I verified this is extensionally exact over the full hierarchy (section 4b), so it is a faithful collapse, not a hidden weakening.
- The 9-member integer family and 39-class hierarchy are commit-specific facts; G-AX DISCOVERS rather than assumes them (it walks Field.__subclasses__() and asserts the family matches the carrier's claim), so a future hierarchy change would fail the check loudly rather than silently.

CONCLUSION: 10 same-spec wrong impls encoded and ALL fully verified (every one rejected by the spec); the prepatch bug reproduced as a rejection; the vacuity control correctly fails; the single CANDIDATE is the correct impl and its materialized faithful patch was RUN through the official harness and RESOLVED: True; refinement.md's legs are all R / A-reference with no kind-3 and no consumed axiom, and both A-references were independently re-validated against the real callees at 67x G-AX's observation count over the complete class hierarchy. Verdict: SOUND (advisory; the runner re-runs these artifacts).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `atk_0.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation verified. The only CANDIDATE (exit 0) was the positive control atk_0.py, whose impl region is code-identical to the bundle's model.py (differs only in the explanatory comment block), so its faithful refined patch IS the gold patch; it was materialized and executed through the official harness: run_resolve('django__django-16082', faithful_atk_0.patch) => RESOLVED: True, note 'resolved'. Every one of the 10 distinct wrong impls came back exit 2 (NOT-A-COUNTEREXAMPLE: shares the spec but fails verification), i.e. the spec rejected each. verify => correct is not falsified here.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -375,18 +375,6 @@
                     Result() == T_NONE))
     # post-conditions-end
     # impl-start
-    # Scan the rows recorded for this connector in registration order and
-    # return the recorded result type of the first matching row, else the
-    # unresolved sentinel. The rows are, per family:
-    #   numeric same-type (five arithmetic connectors + exponentiation):
-    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
-    #   numeric mixed-type (every arithmetic connector, remainder included on
-    #   the same footing; NOT exponentiation):
-    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
-    #   numeric with the null-literal type (same connectors as same-type):
-    #       (flt,null)->flt  (null,flt)->flt
-    #   bitwise (five bitwise connectors): (int,int)->int
-    #   date/time under addition and under subtraction, as recorded.
     if records_same_type_numeric(connector):
         if row(T_INT, T_INT, lhs_type, rhs_type):
             return T_INT
```

Prepatch bug re-encoded as an attack: `True`.

### 0. PRE-FLIGHT: MECHANICAL HOLE SEARCH (hole_search.py)
Before writing any attack I transcribed all 30 Ensures clauses into a standalone evaluator and enumerated the domain (connector codes -4..15 x operand codes -4..13 minus the sentinel = 5780 points), asking at each point how many of the 7 admissible result values satisfy the whole conjunction.
  `cd  && python hole_search.py`
  -> points: 5780 | gold violates spec at: 0 | UNDERDETERMINED points: 0
The postcondition set is POINTWISE TOTAL: at every point of the (open) domain exactly ONE result value is admissible, and it is the gold cascade's. The totality biconditional `has_permitted_combination(...) == (Result() != T_NONE)` plus the per-family clauses leave no free cell, so any same-spec impl that verifies must be extensionally equal to the gold cascade on the whole carrier. This predicted SOUND; I then attempted real falsification rather than stopping here.

### 1. SAME-SPEC BYTE-IDENTITY (all 11 files)
`python -m swebench_unified.adversary same-spec nagini django__django-16082 <file>` -> exit=0 for atk_0..atk_10. Every attack edits ONLY the impl region; the axioms/@Pure/Requires/Ensures regions are byte-identical (spec-region sha1 983d31135d04caf0f936b66ea54ef122b2fb927f).

### 2. ATTACKS: command + observed result
Command for each: `python -m swebench_unified.adversary weakness nagini django__django-16082 atk_N.py` (run 3-at-a-time as background jobs; logs at w_N.log). Exit 0 = CANDIDATE, exit 2 = rejected.

- atk_0.py POSITIVE CONTROL (gold impl verbatim): exit=0 'CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (29.5s)'. Expected — this is the correct impl; the spec is satisfiable and non-vacuous. Its faithful patch = gold patch, RESOLVED: True (see section 3).
- atk_1.py PREPATCH BUG (the mixed-numeric row block guarded with `and connector != C_MOD`, reproducing the pre-patch registry where Combinable.MOD is absent from the different-type dict's connector tuple): exit=2 NOT-A-COUNTEREXAMPLE, verification failed. PREPATCH REPRODUCED = the spec senses the change (G-DIFF): for MOD with integer-kind/decimal operands the prepatch cascade returns the sentinel, violating both the totality biconditional and the mixed-numeric clause.
- atk_2.py PARTIAL DOMAIN (mixed rows' integer arm replaced by a FINITE enumeration `lhs_type == T_INT or == 9 or == 10 or == 11` instead of the open band `is_int_kind`): exit=2 rejected. The open band cannot be discharged by any finite normalization table — code 12+ is a witness. This is the classic partial-domain evasion and the spec kills it.
- atk_3.py BOUNDARY (off-by-one on the open band: `t >= T_INT_SUB + 1`, excluding exactly the auto-increment code T_AUTO = T_INT_SUB = 9 from the integer family): exit=2 rejected. The band's lower boundary is pinned.
- atk_4.py CONTROL-FLOW EFFECT (the whole cascade wrapped in a `while budget > 0` loop with `budget = 24 - lhs_type`, so large integer-family codes exit with the sentinel; accumulator variable + MustTerminate/is_result_type invariants instead of straight-line returns): exit=2 rejected. A control-flow/effect rewrite that changes behaviour only in the open tail of the band is still caught.
- atk_5.py UNGROUNDED-ORACLE ECHO (for a matching (int,int) row, return `max(lhs_type, rhs_type)` — the queried operand's OWN code — instead of the RECORDED result type T_INT, i.e. 'compute a width' rather than 'look up the registry'): exit=2 rejected by `is_result_type(Result())` + the same-type-numeric clause. This is the leg refinement.md D claims ('the result can never be an echo of an operand's own code') and it holds mechanically.
- atk_6.py EXTRA RECORDED ROW (adds (dec,flt)->flt and (flt,dec)->flt widening, which the registry deliberately does NOT record): exit=2 rejected by clause (3).
- atk_7.py WRONG CONNECTOR SET (mixed rows guarded by records_same_type_numeric instead of records_mixed_numeric, so exponentiation wrongly gets the mixed rows): exit=2 rejected by clause (4). The MOD-vs-POW distinction — the crux of this instance, since both must be treated differently in the mixed dict — is pinned in BOTH directions (atk_1 removes MOD, atk_7 adds POW; both rejected).
- atk_8.py NULL-ROW OVERWRITE SUBTLETY (records the integer and decimal NULL rows alongside the float ones, i.e. reading the numeric-with-NULL comprehension as if the inner `for field_type in (Integer, Decimal, Float)` did NOT overwrite per connector): exit=2 rejected by clause (5). mapping.md's note at expressions.py:566 about only the FloatField NULL rows surviving is load-bearing and enforced.
- atk_9.py DATE/TIME ASYMMETRY (subtraction also accepts a duration on the LEFT of a date-family operand — a row the real registry does not record): exit=2 rejected by clause (7)'s `connector == C_SUB and lhs_type == T_DUR and is_date_kind(rhs_type) => T_NONE`.
- atk_10.py VACUITY CONTROL (`Assert(False)` at the head of the gold impl): exit=2 rejected — the precondition is SATISFIABLE, so the proof is not vacuous. (Per the known failure mode where an infeasible guard verifies while proving nothing; Assert(False) is the control and it correctly fails.)

Count: 10 distinct wrong impls (prepatch bug + 9 others spanning partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, extra row, wrong connector set, null-row overwrite, date/time asymmetry, vacuity) + 1 positive control. >= 5 required; none broke the spec.

### 3. MANDATORY RESOLVE RUN for every CANDIDATE
Exactly one file came back CANDIDATE: atk_0.py. `diff atk_0.py model.py` shows the ONLY difference is model.py's 12-line explanatory comment inside the impl region — the executable impl is identical — so its faithful refined patch is the gold patch verbatim (staged as faithful_atk_0.patch, 356 bytes).
  `python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-16082', open('faithful_atk_0.patch').read()); print(r.resolved, r.note)"`
  -> EXECUTED RESULT: RESOLVED: True, NOTE: 'resolved' (log: resolve_atk_0.log)
No verifying impl's faithful patch failed to resolve, so verify=>correct is NOT falsified. Nothing speculative here: the one required resolve run was actually executed and is reported.

### 4. A-LEG AUDIT (the focus of this pass)
refinement.md leg tags: 2 R (B1 param/type refinement, B4 None<->T_NONE) + 2 A-reference (B2 registry cascade, B3 is_subtype<->issubclass). 0 A-consumed, 0 kind-3. Consistent with `grep -c ContractOnly model.py` = 0 and with the impl region containing ZERO Assume/Inhale/Exhale/Assert tokens — nothing is smuggled in as an assumption, so there is no dead or unsound consumed axiom and no unexpressible-changed-op step. The changed operation (the registry rows for Combinable.MOD) is genuinely modeled DEEPLY as the spelled-out cascade, not hidden behind an axiom of the function under change; section E's claim checks out.

(a) Bundle's own G-AX, run against the REAL post-patch source (worktree at base_commit + gold patch applied):
  `cd dj && PYTHONPATH=$PWD python .../axiom_check.py` -> exit=0, 'G-AX OK: ... 200 (queried class, recorded class) pairs ... 9 members ... 9375 observations ... 25 field classes squared'. Its self-reported counts match mapping.md 3.1/3.2 exactly (200 pairs, 9-member integer family, 9375 observations).

(b) INDEPENDENT re-derivation (my_ax.py) — I did not trust axiom_check.py's own bridge or assertions, and specifically probed the concern that its domain is a CURATED 25 classes (8 recorded + 9 integer subs + 8 hand-listed 'unrelated') rather than the whole hierarchy. My script discovers ALL 39 real Field subclasses (importing json/files/related/proxy/contenttypes/reverse_related modules) and checks:
  * CARRIER COMPLETENESS: for each real class I computed its subtype-signature against the 8 recorded operand types and asked whether SOME model code reproduces it. Result: 'real classes NOT representable by any model code: 0'. There are exactly 8 distinct real signatures and each maps onto the carrier: 23 classes with an all-False signature (GenericRelation, BinaryField, BooleanField, CharField, ...) -> the open band t <= T_UNREL_TOP; 10 classes with the integer signature (AutoField, BigAutoField, BigIntegerField, IntegerField, ...) -> T_INT / the open band t >= T_INT_SUB; and one class each for Date, DateTime, Decimal, Duration, Float, Time. So the two OPEN bands are genuinely the right abstraction and no real class falls outside the carrier — the 14 classes G-AX omits all share a signature with one it covers, so the omission is not a gap.
  * CASCADE == REAL CALLEE over every discovered class squared x 15 connectors (11 registered + 4 unregistered), evaluating the model at EVERY code representing each class: 630,375 observations (vs G-AX's 9,375) -> 'cascade != real callee at: 0'. Also 'real returned an out-of-model type at: 0', confirming the is_result_type containment claim against the real callee.
  VERDICT: A-LEG CORRESPONDENCE HOLDS.

(c) Correspondence of the A-legs to the real callees, read against the source at base_commit (expressions.py:503-628, extracted with git cat-file):
  * B3 / mapping 3.1: the scan really is `issubclass(lhs_type, combinator_lhs_type) and issubclass(rhs_type, combinator_rhs_type)` (expressions.py:625-627), an UNCHANGED primitive — the gold patch touches only the connector tuple. is_subtype's three arms (integer band, date arm covering DateTimeField, identity otherwise) match issubclass on all 39x8 real pairs. Correct A-reference, correctly NOT consumed.
  * B2 / mapping 3.2: the registry data really is built by flattening _connector_combinations via register_combinable_fields into _connector_combinators, scanned by a fixed-order `for ... in combinators` returning the first match (expressions.py:621-628) — so 'straight-line cascade in registration order, first match wins' is a faithful deep model of a fixed-length ordered iteration. I verified the row inventory mapping.md 3.2 lists against the real source: the model's 5 ADD rows / 5 SUB rows are the correct COLLAPSE of the real 7 ADD / 9 SUB rows, because the extra real rows are exactly the DateTimeField duplicates that the date-arm subtype match already covers (real (DateTime,Duration)->DateTime is subsumed by model row(T_DATE,T_DUR); real (Date,DateTime)/(DateTime,Date)/(DateTime,DateTime)->Duration under SUB are subsumed by model row(T_DATE,T_DATE)). The 630,375-observation sweep confirms the collapse is extensionally exact, not merely plausible. mapping.md's note that only the FloatField NULL rows survive the comprehension's per-connector overwrite is also confirmed by the sweep and independently pinned by atk_8's rejection.
  * Ordering fidelity: the same-type rows precede the mixed rows in both the real registry and the cascade, which is why an integer/integer query yields Integer rather than falling into a mixed row — behaviourally checked in the sweep.
  * mapping.md 'Flag dependency: none' is right: resolution is over class objects and string keys only, no float-precision or quote=-style callee flag.

### 5. Residual risk / honest caveats
- The carrier collapses each connector string to a code; C_POW=6 vs the bitwise codes are distinguished, and unregistered codes are covered by clause (9) plus 4 unregistered strings in G-AX. The precondition admits EVERY connector code, so no in-repo call site is modelled away.
- One deliberate soundness-preserving simplification: the model omits the real DateTimeField-specific duplicate rows, relying on the date-arm subtype match to cover them. I verified this is extensionally exact over the full hierarchy (section 4b), so it is a faithful collapse, not a hidden weakening.
- The 9-member integer family and 39-class hierarchy are commit-specific facts; G-AX DISCOVERS rather than assumes them (it walks Field.__subclasses__() and asserts the family matches the carrier's claim), so a future hierarchy change would fail the check loudly rather than silently.

CONCLUSION: 10 same-spec wrong impls encoded and ALL fully verified (every one rejected by the spec); the prepatch bug reproduced as a rejection; the vacuity control correctly fails; the single CANDIDATE is the correct impl and its materialized faithful patch was RUN through the official harness and RESOLVED: True; refinement.md's legs are all R / A-reference with no kind-3 and no consumed axiom, and both A-references were independently re-validated against the real callees at 67x G-AX's observation count over the complete class hierarchy. Verdict: SOUND (advisory; the runner re-runs these artifacts).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

ATTACK GOAL: find an input where the modeled resolve_combined_type disagrees with the real callee. Reference = base commit bf47c71 WITH gold patch applied (built independently: fresh copy of  -> git apply gold16082.diff, 1 insertion,). Result: NO divergence found. Verdict FAITHFUL.

METHOD (differential, not opinion). Contract-stripped model.py into an executable twin (bmodel.py: Pure/Requires/Ensures/Implies/MustTerminate stubbed, spec+impl regions untouched), then compared against the real _resolve_combined_type over the FULL discovered domain.

(1) Carrier/hierarchy audit. Walked Field.__subclasses__() transitively after importing the repo's own field modules (related/files/json/proxy): 38 field classes + NoneType = 39 operand types. Classes below each recorded operand type: IntegerField -> 9 members {AutoField, BigAutoField, BigIntegerField, PositiveBigIntegerField, PositiveIntegerField, PositiveSmallIntegerField, SmallAutoField, SmallIntegerField, OrderWrt}; DateField -> {DateTimeField}; DecimalField/FloatField/DurationField/TimeField/DateTimeField -> empty. Exactly what mapping.md claims. Mapped the integer family to the open band t>=T_INT_SUB and the 8 match-nothing classes to the open band t<=T_UNREL_TOP, so both open bands are exercised by multiple distinct members (not just the named T_AUTO=9).

(2) Exhaustive model-vs-real differential. 21 connectors (all 11 registered: '+','-','*','/','%%','^','&','|','<<','>>','#'; plus 10 verified-unregistered strings asserted absent from _connector_combinators.keys()) x 39 x 39 = 31,941 observations. MISMATCHES: 0. Also 0 result-set escapes: the real callee never returned a type outside the modeled result set {None,Integer,Decimal,Float,Duration,Time,DateTime} anywhere in that domain, so is_result_type is not hiding an unmodeled outcome.

(3) CLAUSE-BY-CLAUSE against the real repo (the decisive test for too-strong). Rather than trusting spec/impl internal consistency, I transcribed all 28 postcondition clauses (0a,0b,1a-c,2a-d,3a-b,4,5a-b,6a-b,7a-i,8,9a-b) as predicates and evaluated each on the REAL callee's output over 28,899 (connector, lhs, rhs) real observations. TOTAL VIOLATIONS: 0. In particular the strongest/riskiest clauses all hold: 0b (has_permitted_combination <-> Result != sentinel, an exact iff), 6b (bitwise leaves EVERY non-integer pair unresolved), 8 (date/duration/time unresolved under every connector but ADD/SUB), 9a/9b, 3a/3b (dec/flt mix unresolved under ANY connector), and 4 (POW records same-type but NO mixed row).

(4) Subtle trap checked and CLEARED. The numeric-with-NULL dict (expressions.py:550-566) is a comprehension with an inner `for field_type in (Integer, Decimal, Float)`, so later field types OVERWRITE earlier ones per connector and ONLY the FloatField NULL rows survive. Confirmed empirically on the real patched repo: (Integer,NULL)->None, (Decimal,NULL)->None, (AutoField,NULL)->None, (Float,NULL)->FloatField for all six of ADD/SUB/MUL/DIV/MOD/POW. model.py records exactly those two rows and clause 5b pins the int/dec/null cases to the sentinel. The model captures the real (arguably surprising) behavior rather than the naive reading — this is the one place a too-strong spec was most likely, and it is correct.

(5) Patch-delta containment (guards against condemning the fix, and against extra drift). Ran the same differential against the UNPATCHED base: exactly 40 divergences, ALL on connector MOD, ALL on mixed-numeric operand kind-pairs (INTFAM x Decimal, INTFAM x Float and both reverses). That is precisely the single added line `Combinable.MOD,` in the mixed-type dict's connector tuple — nothing more. So the model describes the fixed behavior and drifts nowhere else.

(6) Non-vacuity. Every one of the 26 implication antecedents fires on the code domain (min fire count 1, for 7g/7h; e.g. 1a=96, 2a-d=20 each, 6b=900, 8=1152, 9a=1050). NO vacuous clause. Precondition is only is_operand_type(t) (t != sentinel) on both operands and admits every connector code, so no real call site is modeled away.

(7) Integrity / bundle self-checks. `nagini_verify.sh` on the bundle model.py: 'Verification successful' (26.6s, exit 0). `adversary same-spec`: 'SAME — attack shares the bundle's exact specification' (exit 0), and markers.same_spec(bundle, copy) True. Bundle's own axiom_check.py re-run against MY independently patched worktree: G-AX OK (200 subtype pairs over the 9-member integer family + date/datetime; deep registry == real _resolve_combined_type over 9,375 observations). conformance_check.py: G-CONF OK, 109,375 inputs, 0 disagreements.

HARNESS BUG I CAUGHT AND FIXED (recording so it is not mistaken for a finding): my first sweep reported 100 mismatches, all on a connector I had assumed was unregistered — the string '#' is actually Combinable.BITXOR (expressions.py:60), so I was feeding a registered connector a model code of 12. The 100 'mismatches' were exactly the 10x10 integer-family grid under BITXOR. After asserting each fake connector is genuinely absent from _connector_combinators, mismatches went to 0. No real divergence.

OBSERVATION, NOT A FINDING FOR THIS GATE: meta.json['region_hashes'] is stale w.r.t. model.py — only 'axioms' matches; pure/pre/post/impl/spec_view all differ (and differ for model_prepatch.py too). This is corpus-wide bookkeeping drift, not a faithfulness defect: 54 of the first 60 nagini bundles show the same mismatch, and the authoritative `adversary same-spec` marker check passes. Flagging for corpus maintenance; it does not bear on whether this spec matches the repo.

CONCLUSION: no diverging input exists in the fully enumerated real domain (31,941 model-vs-real + 28,899 clause-vs-real observations, 0 disagreements), the spec is non-vacuous, and its only divergence from the base commit is exactly the patch delta. I could not break faithfulness.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE: no relaxation in this bundle. `'relaxed_leakage' in meta` -> False; no RELAXED_LEAKAGE.md in nagini/ (dir listing: axiom_check.py, conformance_check.py, mapping.md, meta.json, model.py, model_prepatch.py, pbt_result.json, properties.py, refinement.md, verdict.md, plus one transient build artifact). So this is a plain leakage judgement with no inherited disposition.

SPEC VIEW IDENTITY (my own computation): markers.spec_view/region_hashes(model.py, get_backend('nagini')) -> spec_view = 0c2d9d9e4435e1f6e7c7078872e21eb15628e85c5316f96a10516a06ba7194f7, byte-identical to meta.json gates['G-HYGIENE'].data.region_hashes.spec_view (0c2d9d9e4435...). `adversary same-spec nagini django__django-16082` on a byte copy -> exit 0 'SAME'. Impl region is properly elided in the spec view ('...  # implementation elided — supplied by the consumer'), so the seven-row cascade and its per-row comments (which DO name the exact registered rows) are NOT solver-visible.

BOOKKEEPING DRIFT (curator note, not a leakage finding): meta.json's TOP-LEVEL region_hashes block is stale — it records spec_view 088a5640... plus different pure/pre/post/impl hashes — while the G-HYGIENE gate entry holds the values my recomputation reproduces exactly. I judged the current model.py (sha256 b209126b3c36..., which is also the model.py hash recorded in every passing gate's `sources`). Note: I sampled 40 nagini bundles and 36 show the same top-level-vs-G-HYGIENE drift, so this is corpus-wide harness bookkeeping, not tampering on this cell.

LEAKAGE BASELINE = public problem_statement only (hints_text excluded): 'Resolve output_field when combining numeric expressions with MOD operator. ... if the types of the query are different (Decimal and Integer), it doesn't resolve the result to a Decimal type, like it does for other mathematical operators.' That sentence itself supplies (a) connector = MOD/remainder, (b) mixed Decimal/Integer operands, (c) result must be Decimal, (d) 'like it does for other mathematical operators' = MOD on the same footing as ADD/SUB/MUL/DIV. The spec view's clause (2) and its prose 'the remainder connector on the SAME footing as the other four' restate exactly (a)-(d) as behaviour, adding nothing.

### FACET RE-CONFIRMED BY MEASUREMENT (load-bearing control, run from the project root in mktemp dirs, bundle untouched):
1. `bash scripts/nagini_verify.sh atk_gold.py` (byte copy of bundle model.py) -> 'Verification successful' (28.93s) — spec satisfiable by the gold-faithful impl, postconditions not vacuous.
2. `bash scripts/nagini_verify.sh model_prepatch.py` -> 'Verification failed', error at model_prepatch.py:262 on `has_permitted_combination(connector,lhs,rhs) == (Result() != T_NONE)`. `adversary weakness nagini django__django-16082 atk_pre.py` -> exit 2 NOT-A-COUNTEREXAMPLE (spec rejects the prepatch impl). markers.same_spec(model.py, model_prepatch.py, nagini) -> True, and diffing the two spec views byte-for-byte -> IDENTICAL, so the twins differ only in impl.
3. THE STRIP TEST (the usual unavoidability control): I removed `or connector == C_MOD` from `records_mixed_numeric` in the prepatch twin — i.e. deleted the discriminating clause from the SPEC — and re-verified: lb.py -> 'Verification successful' (22.95s). So the 'remainder connector in the mixed-numeric family' clause is precisely the load-bearing discriminator: with it the pre-patch impl is rejected, without it the pre-patch impl passes. That clause is verbatim the public problem_statement's own content, so the discriminator is public, not leaked.

OUT-OF-FACET TOKEN SCAN of the spec view (all False): 'expressions', 'Combinable', '_connector_combinations', '_connector_combinators', 'register_combinable_fields', 'IntegerField', 'DecimalField', 'FloatField', 'AutoField', 'output_field', 'tuple', 'dict', 'line 536', 'MOD,', 'ticket', '33397', '15271', '@@', '+++', 'diff --git', and the narration vocabulary 'patch'/'fix'/'regression'/'previously'/'used to'/'now also'/'oversight'. Only two hits: 'django' appears once, in the instance id in the module title; 'issubclass' appears once, in the axioms comment naming an UNCHANGED primitive validated out-of-band — patch.diff touches only `+            Combinable.MOD,` at expressions.py:536 and leaves the issubclass scan alone, so naming it localizes nothing. leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[].

FACETS BEYOND THE PUBLIC STATEMENT ARE NOT EDIT-SHAPED: the spec view also pins Integer/Float -> Float, the open integer-family (AutoField) rows, the (dec,flt)/(flt,dec) -> sentinel absences, and the bitwise/date-time families. The dec/flt sentinel rows are absent from the registry both pre- and post-patch and the bitwise/date-time rows are untouched by the patch, so they carry zero information about the edit; they tighten the spec without localizing the change. Nothing in the spec view says WHERE (no file, no dict, no 'add a tuple entry') — the registry-construction detail that would localize the edit lives in refinement.md/mapping.md/patch.diff, none of which are in the solver-visible spec view.

CORE GATES THE DISPOSITION LEANS ON: G-VERIFY, G-DIFF, G-GOLD reproduced by me directly (items 1-3 above); G-HYGIENE spec_view hash reproduced; G-AX/G-CONF/G-MUT/G-PBT/G-RESOLVE recorded pass. G-PANEL-1 (spec-too-weak) is recorded FAIL ('atk_9.py verifies but its patch does not resolve'), which is a weakness finding in the sibling lane — not a leakage question and it does not undercut the leakage argument, which only needs the discriminator to be public.

NO BUNDLE FILE ADDRESSES ME: grepped model.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py for reviewer/attacker-directed instruction ('attacker', 'do not report/flag/submit', 'please pass/accept', 'the correct verdict', 'record this as', 'trust this', 'no need to check', 'note to the ...') -> no matches; leakage.reviewer_directed over model.py/refinement.md/mapping.md/verdict.md/meta.json/axiom_check.py/conformance_check.py -> [] for each. verdict.md and meta.json do carry a prior G-PANEL-3 NO-LEAKAGE note (citing a third spec_view hash, 0f6913cb..., that matches neither hash present today), but it is a backfilled record of an earlier run, not an instruction to me; I re-derived independently and did not inherit it.

WORKED ONLY IN /tmp; bundle unmodified (git status shows only a pre-existing meta.json modification I did not make).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
