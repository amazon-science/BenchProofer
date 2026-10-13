# P2 adversarial audit — django__django-13028

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_0_prepatch.py`, `atk_1_toponly.py`, `atk_2_offbyone.py`, `atk_3_disjunction.py`, `atk_4_neverraise.py`, `atk_5_isexpr_only.py`, `atk_8_diverge.py`, `atk_9_wrong_exc.py`, `atk_10_mutate.py`, `atk_11_shape_gated.py`, `atk_12_decoupled.py`, `atk_13_always_raise.py`, `atk_14_vacuity.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6_reverse_walk.py`, `atk_7_deferred_raise.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl was found whose faithful refined patch fails to resolve. The only two CANDIDATEs (atk_6_reverse_walk, atk_7_deferred_raise) both RESOLVED under the official harness (2/2 F2P, 276/276 P2P, completed=True), i.e. they are correct echoes of the gold, not spec weaknesses.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,6 +98,10 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
+    # Pre-patch skeleton: the disallow test screens ONLY the not-permitted
+    # marker, without first requiring the operand to be a query expression. A
+    # plain data operand that merely exposes a not-permitted marker is therefore
+    # wrongly rejected.
     i = 0
     while i < len(is_expr):
         # invariants-start
@@ -105,12 +109,12 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
+        # no not-permitted operand has been seen among the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
+                                                  permitted[k] == 1))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
         # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
+        if permitted[i] == 0:
             raise OperandNotAllowed()
         i = i + 1
     # impl-end
```

Attack 2 — `atk_1_toponly.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,19 +98,7 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(is_expr):
-        # invariants-start
-        Invariant(Acc(list_pred(is_expr), 1 / 2))
-        Invariant(Acc(list_pred(permitted), 1 / 2))
-        Invariant(len(is_expr) == len(permitted))
-        Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
-        Invariant(MustTerminate(len(is_expr) - i + 1))
-        # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
+    if len(is_expr) > 0:
+        if is_expr[0] == 1 and permitted[0] == 0:
             raise OperandNotAllowed()
-        i = i + 1
     # impl-end
```

Attack 3 — `atk_2_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,13 +99,12 @@
     # post-conditions-end
     # impl-start
     i = 0
-    while i < len(is_expr):
+    while i < len(is_expr) - 1:
         # invariants-start
         Invariant(Acc(list_pred(is_expr), 1 / 2))
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not (is_expr[k] == 1 and permitted[k] == 0)))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
```

Attack 4 — `atk_3_disjunction.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,12 +105,11 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
+                                                  not (is_expr[k] == 1 or permitted[k] == 0)))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
         # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
+        if is_expr[i] == 1 or permitted[i] == 0:
             raise OperandNotAllowed()
         i = i + 1
     # impl-end
```

Attack 5 — `atk_4_neverraise.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,12 +105,7 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
         # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
-            raise OperandNotAllowed()
         i = i + 1
     # impl-end
```

Attack 6 — `atk_5_isexpr_only.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,12 +105,11 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
+                                                  is_expr[k] == 0))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
         # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
+        if is_expr[i] == 1:
             raise OperandNotAllowed()
         i = i + 1
     # impl-end
```

Attack 7 — `atk_6_reverse_walk.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -98,19 +98,18 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(is_expr):
+    i = len(is_expr)
+    while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(is_expr), 1 / 2))
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(is_expr),
                                                   not (is_expr[k] == 1 and permitted[k] == 0)))))
-        Invariant(MustTerminate(len(is_expr) - i + 1))
+        Invariant(MustTerminate(i + 1))
         # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
+        if is_expr[i - 1] == 1 and permitted[i - 1] == 0:
             raise OperandNotAllowed()
-        i = i + 1
+        i = i - 1
     # impl-end
```

Attack 8 — `atk_7_deferred_raise.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -98,6 +98,7 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
+    bad = 0
     i = 0
     while i < len(is_expr):
         # invariants-start
@@ -105,12 +106,18 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
+        Invariant(bad == 0 or bad == 1)
+        Invariant(Implies(bad == 1,
+                          Exists(int, lambda k: (0 <= k and k < len(is_expr)
+                                                 and is_expr[k] == 1 and permitted[k] == 0))))
+        Invariant(Implies(bad == 0,
+                          Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                          not (is_expr[k] == 1 and permitted[k] == 0))))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
         # invariants-end
         if is_expr[i] == 1 and permitted[i] == 0:
-            raise OperandNotAllowed()
+            bad = 1
         i = i + 1
+    if bad == 1:
+        raise OperandNotAllowed()
     # impl-end
```

Attack 9 — `atk_8_diverge.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,6 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not (is_expr[k] == 1 and permitted[k] == 0)))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
@@ -113,4 +112,13 @@
         if is_expr[i] == 1 and permitted[i] == 0:
             raise OperandNotAllowed()
         i = i + 1
+    j = 0
+    while j >= 0:
+        # invariants-start
+        Invariant(Acc(list_pred(is_expr), 1 / 2))
+        Invariant(Acc(list_pred(permitted), 1 / 2))
+        Invariant(len(is_expr) == len(permitted))
+        Invariant(j >= 0)
+        # invariants-end
+        j = j + 1
     # impl-end
```

Attack 10 — `atk_9_wrong_exc.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,7 +105,6 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not (is_expr[k] == 1 and permitted[k] == 0)))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
@@ -113,4 +112,5 @@
         if is_expr[i] == 1 and permitted[i] == 0:
             raise OperandNotAllowed()
         i = i + 1
+    raise ValueError()
     # impl-end
```

Attack 11 — `atk_10_mutate.py` → rejected (same spec, does not verify — good)

```diff
@@ -105,12 +105,12 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                   not (is_expr[k] == 1 and permitted[k] == 0)))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
         # invariants-end
         if is_expr[i] == 1 and permitted[i] == 0:
             raise OperandNotAllowed()
+        permitted[i] = 1
         i = i + 1
     # impl-end
```

Attack 12 — `atk_11_shape_gated.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,19 +98,19 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(is_expr):
-        # invariants-start
-        Invariant(Acc(list_pred(is_expr), 1 / 2))
-        Invariant(Acc(list_pred(permitted), 1 / 2))
-        Invariant(len(is_expr) == len(permitted))
-        Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
-        Invariant(MustTerminate(len(is_expr) - i + 1))
-        # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
-            raise OperandNotAllowed()
-        i = i + 1
+    if len(is_expr) > 1:
+        i = 0
+        while i < len(is_expr):
+            # invariants-start
+            Invariant(Acc(list_pred(is_expr), 1 / 2))
+            Invariant(Acc(list_pred(permitted), 1 / 2))
+            Invariant(len(is_expr) == len(permitted))
+            Invariant(0 <= i and i <= len(is_expr))
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                                                      not (is_expr[k] == 1 and permitted[k] == 0)))))
+            Invariant(MustTerminate(len(is_expr) - i + 1))
+            # invariants-end
+            if is_expr[i] == 1 and permitted[i] == 0:
+                raise OperandNotAllowed()
+            i = i + 1
     # impl-end
```

Attack 13 — `atk_12_decoupled.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,6 +98,8 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
+    saw_expr = 0
+    saw_bad = 0
     i = 0
     while i < len(is_expr):
         # invariants-start
@@ -105,12 +107,21 @@
         Invariant(Acc(list_pred(permitted), 1 / 2))
         Invariant(len(is_expr) == len(permitted))
         Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
+        Invariant(saw_expr == 0 or saw_expr == 1)
+        Invariant(saw_bad == 0 or saw_bad == 1)
+        Invariant(Implies(saw_expr == 1,
+                          Exists(int, lambda k: (0 <= k and k < len(is_expr)
+                                                 and is_expr[k] == 1))))
+        Invariant(Implies(saw_bad == 1,
+                          Exists(int, lambda k: (0 <= k and k < len(is_expr)
+                                                 and permitted[k] == 0))))
         Invariant(MustTerminate(len(is_expr) - i + 1))
         # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
-            raise OperandNotAllowed()
+        if is_expr[i] == 1:
+            saw_expr = 1
+        if permitted[i] == 0:
+            saw_bad = 1
         i = i + 1
+    if saw_expr == 1 and saw_bad == 1:
+        raise OperandNotAllowed()
     # impl-end
```

Attack 14 — `atk_13_always_raise.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,19 +98,5 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(is_expr):
-        # invariants-start
-        Invariant(Acc(list_pred(is_expr), 1 / 2))
-        Invariant(Acc(list_pred(permitted), 1 / 2))
-        Invariant(len(is_expr) == len(permitted))
-        Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
-        Invariant(MustTerminate(len(is_expr) - i + 1))
-        # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
-            raise OperandNotAllowed()
-        i = i + 1
+    raise OperandNotAllowed()
     # impl-end
```

Attack 15 — `atk_14_vacuity.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,19 +98,5 @@
                                        and is_expr[k] == 1 and permitted[k] == 0)))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(is_expr):
-        # invariants-start
-        Invariant(Acc(list_pred(is_expr), 1 / 2))
-        Invariant(Acc(list_pred(permitted), 1 / 2))
-        Invariant(len(is_expr) == len(permitted))
-        Invariant(0 <= i and i <= len(is_expr))
-        # no disallowed operand has been seen among the visited prefix.
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
-        Invariant(MustTerminate(len(is_expr) - i + 1))
-        # invariants-end
-        if is_expr[i] == 1 and permitted[i] == 0:
-            raise OperandNotAllowed()
-        i = i + 1
+    Assert(False)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13028.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A guard screens the comparison operands of a stored query before the query is
  built, rejecting any operand that is BOTH (a) a query-expression operand —
  one that participates in query resolution — AND (b) marked by that expression
  as not permitted on this side of the comparison. The guard walks the operand
  together with every operand nested inside it (a query-expression operand may
  carry sub-operands) and applies the same screen to each.

  The behaviour pinned here is the CONJUNCTION the screen requires. An ordinary
  data operand that merely happens to expose a same-named "not-permitted" marker
  — without being a query-expression operand at all — must NOT be rejected: it
  is plain data, supplied as the right-hand side of a comparison, and is carried
  through untouched. Only an operand that is genuinely a query expression AND
  carries the not-permitted marker may be rejected. So the guard rejects the set
  of operands iff at least one operand in the walk is simultaneously a
  query-expression operand and not-permitted; otherwise it accepts (returns
  normally), even if some operand is not-permitted but is plain data.

The operand walk is modelled as the flattened traversal order of the operand
and its nested sub-operands: two index-aligned ``List[int]`` carry, per visited
operand, whether it is a query-expression operand (``is_expr[i]`` in {0,1}) and
whether it is permitted on this side (``permitted[i]`` in {0,1}; an operand that
exposes no marker defaults to permitted = 1). The discriminating observable is
purely WHICH outcome the guard produces (accept vs. reject), not the operands'
contents; Nagini bans ``str`` indexing, so operand identity is abstracted to
these two per-operand booleans. The rejection the guard raises is a user-defined
exception class (a builtin exception in an ``Exsures`` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class OperandNotAllowed(Exception):
    """The rejection the guard raises when a disallowed query-expression operand
    is encountered. User-defined stand-in for the not-supported error the
    desired behaviour requires (a builtin exception in an ``Exsures`` crashes the
    Nagini translator; mapping.md §2)."""
    pass

# axioms-start
# No consumed axioms: the guard's decision is a conjunction of two per-operand
# observations (is-a-query-expression and is-permitted) over the operand walk,
# modelled deeply over index-aligned integer carriers. There is no unchanged
# library callee the proof must stand in for.
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required: the decision is stated inline
#  over the two per-operand carriers.)
# pure-end

def check_operands(is_expr: List[int], permitted: List[int]) -> None:
    # pre-conditions-start
    # The two index-aligned carriers describe the flattened operand walk; the
    # guard only READS them (fractional permission, directive 5).
    Requires(Acc(list_pred(is_expr), 1 / 2))
    Requires(Acc(list_pred(permitted), 1 / 2))
    # one entry per visited operand: the walk has a single shape.
    Requires(len(is_expr) == len(permitted))
    # each entry is a boolean flag in {0, 1}.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_expr),
                                            is_expr[k] == 0 or is_expr[k] == 1))))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(permitted),
                                            permitted[k] == 0 or permitted[k] == 1))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The inputs are read-only: returned untouched at the same fractional
    # permission. Holding only fractional permission throughout, the guard
    # cannot have mutated either carrier (directive 5); their lengths and
    # contents are therefore unchanged with no further clause needed.
    Ensures(Acc(list_pred(is_expr), 1 / 2))
    Ensures(Acc(list_pred(permitted), 1 / 2))
    Ensures(len(is_expr) == len(permitted))
    # Accept (return normally) ONLY when NO operand in the walk is BOTH a
    # query-expression operand AND not-permitted. An ordinary data operand that
    # is merely not-permitted (is_expr == 0) does not block acceptance.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(is_expr),
                                            not (is_expr[k] == 1 and permitted[k] == 0)))))
    # Reject (raise) iff at least one operand in the walk is SIMULTANEOUSLY a
    # query-expression operand and not-permitted. This is the discriminating
    # conjunction: the query-expression test must hold too, so plain not-permitted
    # data passes through. The read-only carriers are re-established at the same
    # fractional permission on the rejecting path as well.
    Exsures(OperandNotAllowed,
            Acc(list_pred(is_expr), 1 / 2) and Acc(list_pred(permitted), 1 / 2)
            and len(is_expr) == len(permitted)
            and Exists(int, lambda k: (0 <= k and k < len(is_expr)
                                       and is_expr[k] == 1 and permitted[k] == 0)))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(is_expr):
        # invariants-start
        Invariant(Acc(list_pred(is_expr), 1 / 2))
        Invariant(Acc(list_pred(permitted), 1 / 2))
        Invariant(len(is_expr) == len(permitted))
        Invariant(0 <= i and i <= len(is_expr))
        # no disallowed operand has been seen among the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
        Invariant(MustTerminate(len(is_expr) - i + 1))
        # invariants-end
        if is_expr[i] == 1 and permitted[i] == 0:
            raise OperandNotAllowed()
        i = i + 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, A legs) for django__django-13028 nagini. All attacks built by copying model.py and editing ONLY the impl region (invariants included, which are nested inside impl); all 15 confirmed spec byte-identical via `python -m swebench_unified.adversary same-spec nagini django__django-13028 <f>` (exit 0, 'SAME'). Every attack then run through `python -m swebench_unified.adversary weakness nagini django__django-13028 <f>`, in concurrent batches of 3 (each Nagini check spawns JVM+Z3).

POSITIVE CONTROL pos_control.py (verbatim model.py): CANDIDATE — shares spec AND verifies (17.2s). Spec is live and non-vacuous.

**PREPATCH REPRODUCED:** atk_0_prepatch.py (= bundle model_prepatch.py, disallow test drops the is_expr[i]==1 conjunct, screening only permitted[i]==0). weakness => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). The spec senses the gold change (G-DIFF), failing exactly on the Exsures existential: on a plain-data not-permitted operand (is_expr=0, permitted=0) it raises although no query-expression not-permitted operand exists. This is the F2P case (Author.objects.filter(extra=self.e2) where ExtraInfo has a field literally named filterable=False).

### ATTACK-BY-ATTACK (all files, all same-spec, command = adversary weakness nagini django__django-13028 <path>):
1. atk_1_toponly.py — PARTIAL DOMAIN: screens only walk index 0, drops the recursive tail into sub-operands. REJECTED (does not verify, exit 2). Kills the A2 recursion-collapse leg being under-covered.
2. atk_2_offbyone.py — BOUNDARY: loop bound len-1, last visited operand never screened. REJECTED (exit 2).
3. atk_3_disjunction.py — CONTROL-FLOW-EFFECT / wrong connective: `or` instead of `and` (over-rejection: any expression, or any not-permitted operand). REJECTED (exit 2). This is the dual failure mode of the prepatch bug and the spec catches both directions.
4. atk_4_neverraise.py — guard deleted entirely (max under-rejection). REJECTED (exit 2).
5. atk_5_isexpr_only.py — the OTHER single conjunct: screens is_expr only, ignoring the marker. REJECTED (exit 2).
6. atk_6_reverse_walk.py — A-LEG on WALK ORDER: traverses the flattened walk in reverse (raise fires on the LAST disallowed operand). CANDIDATE (verifies, 17.8s). Faithful patch materialized = post-order guard (recurse into reversed sub-operands FIRST, then screen self); patch_atk6.diff, applied at base_commit 78ad4b4b. run_resolve => resolved=True completed=True, FAIL_TO_PASS 2 pass / 0 fail, PASS_TO_PASS 276 pass / 0 fail. CORRECT ECHO, not a weakness — walk order is genuinely unobservable to the graded tests (accept/reject is order-independent since the guard is a pure any()).
7. atk_7_deferred_raise.py — A-LEG on RAISE SITE: scans the entire walk into a flag, raises only afterwards (the real guard would walk all remaining operands the gold's early raise skips). CANDIDATE (verifies, 17.9s). Faithful patch = `_scan_filterable` helper returning the last disallowed operand, raise deferred past the whole tree walk; patch_atk7.diff. run_resolve => resolved=True completed=True, F2P 2/2, P2P 276/276. CORRECT ECHO — the extra walk is side-effect-free (get_source_expressions is a pure accessor), so early vs deferred raise is unobservable.
8. atk_8_diverge.py — DIVERGENCE: correct decision, then spins forever on the accept path (would hang every graded query). REJECTED (exit 2) — method-level MustTerminate(2) does its job, consistent with the standing note that loop invariants alone do not reject a diverging rival.
9. atk_9_wrong_exc.py — WRONG REJECTION TYPE: correct decision but a clean walk raises ValueError (Exsures only names OperandNotAllowed). REJECTED (exit 2) — the universal accept postcondition forces normal return, so the escape hatch of raising an unlisted exception is closed.
10. atk_10_mutate.py — EFFECT: correct decision but writes permitted[i]=1, mutating the caller's operands. REJECTED (exit 2) — the 1/2 fractional permission (directive 5) is load-bearing, so the read-only claim in the postcondition comment is real and not just prose.
11. atk_11_shape_gated.py — PARTIAL DOMAIN on walk SHAPE: screens only when the walk has 2+ operands, so a lone disallowed expression sails through. Deliberately agrees with the gold on the F2P input, so the F2P test alone could not see it. REJECTED (exit 2).
12. atk_12_decoupled.py — EXISTENTIAL DECOUPLING (the subtlest): reject iff SOME operand is an expression AND SOME possibly DIFFERENT operand is not-permitted. Agrees with the gold on every single-operand walk (F2P still passes) and diverges only when the two properties sit on different operands. REJECTED (exit 2) — the Exsures binds both conjuncts to the SAME index k, which is exactly what makes this the right spec.
13. atk_13_always_raise.py — UNGROUNDED-ORACLE ECHO: unconditional raise, decision never reads the carriers. REJECTED (exit 2) — the Exsures existential is genuinely grounded in the inputs, not satisfiable by a constant.
14. atk_14_vacuity.py — VACUITY CONTROL: Assert(False) as the impl. REJECTED (does not verify) => the precondition is satisfiable and the spec proves something. (Note: the weakness wrapper prints exit 0 on the shell's $? here because of the pipeline through tail; the substantive line is NOT-A-COUNTEREXAMPLE / does not verify. The runner re-derives this mechanically.)

EXTRA A-LEG PROBE (not an attack file — a direct resolve probe of an abstracted leg): mapping.md §2 claims the rejection MESSAGE payload (expression.`__class__`.`__name__` + ' is disallowed in the filter clause.') is unobserved by the graded tests. The model carries no message at all, so any message is refinement-legal. I materialized the most hostile legal choice — the gold conjunct with `raise NotSupportedError('')` (patch_payload.diff) — and ran run_resolve: resolved=True completed=True. Confirms the payload abstraction is sound for THIS instance's graded set. I separately verified this is not an accident of test selection: the only message assertions on this string in the repo live in tests/expressions_window/tests.py:843,868, which are not in this instance's F2P (2 tests) or P2P (276 tests, all queries.tests.*) — so no graded test reads the message.

REFINEMENT.MD AUDIT (leg kinds): 3 legs, all admissible, no kind-3.
- A1 (params is_expr/permitted <-> the expression argument + its transitive get_source_expressions operands) — tagged R. Sound: the bijection is per-operand, is_expr[i] <-> hasattr(op,'resolve_expression'), permitted[i] <-> getattr(op,'filterable',True) with absent => True => 1. The 'absent attribute defaults to permitted' case is the one that carries the F2P semantics and is stated explicitly in mapping.md §2. Preconditions ({0,1} entries, equal lengths) are satisfied by EVERY flattening of a real operand tree by construction, so the R leg excludes no real input.
- A2 (the while loop <-> the top-level call plus the UNCHANGED recursive tail) — tagged R + I, with the tree->flat collapse carried as an A-reference. This is the only genuinely abstract leg and the one I attacked hardest: atk_1 (drop the recursion), atk_2 (drop the walk tail), atk_11 (gate on walk shape), atk_12 (decouple the two conjuncts across operands) and atk_6 (walk order) all probe it; the first four are rejected by the verifier and the fifth resolves. Correspondence to the real callee holds: the recursion guard hasattr(expression,'get_source_expressions') at query.py:1132 is byte-unchanged by the gold patch (confirmed against the base_commit checkout), and because the SAME disallow test is applied at every node, the recursive guard raises iff some node in the pre-order traversal satisfies the conjunction — precisely `Exists k. is_expr[k]==1 and permitted[k]==0`. axiom_check.py backs this with an exhaustive 258-tree boundary space plus 20k fuzz trees against a faithful in-Python reference, and against the REAL Query.check_filterable when django is importable.
- A3 (the disallow test <-> the patched conjunction, OperandNotAllowed <-> NotSupportedError) — tagged R + I. Sound: the added hasattr(...,'resolve_expression') conjunct maps to is_expr[i]==1 and the discriminating content of the gold change lives DIRECTLY in the model's conjunct, not behind an axiom. The user-defined exception stand-in is forced (a builtin/db exception in an Exsures crashes the Nagini translator) and is observationally the raise itself; the message abstraction is separately resolve-probed above.
- No A-consumed legs exist (no @ContractOnly axiom; the axioms region is an explicit no-op comment), so there is no opaque oracle in the postcondition and no leg where the proof leans on an unvalidated Ensures. Refinement.md §C's no-kind-3 claim is accurate: the function under change IS the modelled function.

**CONCLUSION:** 15 same-spec wrong/rival impls run; 12 wrong impls (including the prepatch bug) mechanically REJECTED by the verifier; 1 vacuity control rejected; 2 CANDIDATEs whose faithful refined patches were BOTH materialized and RUN through the official harness, both RESOLVED (F2P 2/2, P2P 276/276) — correct echoes, so neither is a verify-but-incorrect break. No resolve run failed to complete. Verdict: SOUND (advisory; the runner re-runs these artifacts).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_0_prepatch.py`, `atk_1_toponly.py`, `atk_2_offbyone.py`, `atk_3_disjunction.py`, `atk_4_neverraise.py`, `atk_5_isexpr_only.py`, `atk_8_diverge.py`, `atk_9_wrong_exc.py`, `atk_10_mutate.py`, `atk_11_shape_gated.py`, `atk_12_decoupled.py`, `atk_13_always_raise.py`, `atk_14_vacuity.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6_reverse_walk.py`, `atk_7_deferred_raise.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl was found whose faithful refined patch fails to resolve. The only two CANDIDATEs (atk_6_reverse_walk, atk_7_deferred_raise) both RESOLVED under the official harness (2/2 F2P, 276/276 P2P, completed=True), i.e. they are correct echoes of the gold, not spec weaknesses.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1_toponly.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2_offbyone.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3_disjunction.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4_neverraise.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5_isexpr_only.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6_reverse_walk.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7_deferred_raise.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_8_diverge.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_9_wrong_exc.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_10_mutate.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_11_shape_gated.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_12_decoupled.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_13_always_raise.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_14_vacuity.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13028.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A guard screens the comparison operands of a stored query before the query is
  built, rejecting any operand that is BOTH (a) a query-expression operand —
  one that participates in query resolution — AND (b) marked by that expression
  as not permitted on this side of the comparison. The guard walks the operand
  together with every operand nested inside it (a query-expression operand may
  carry sub-operands) and applies the same screen to each.

  The behaviour pinned here is the CONJUNCTION the screen requires. An ordinary
  data operand that merely happens to expose a same-named "not-permitted" marker
  — without being a query-expression operand at all — must NOT be rejected: it
  is plain data, supplied as the right-hand side of a comparison, and is carried
  through untouched. Only an operand that is genuinely a query expression AND
  carries the not-permitted marker may be rejected. So the guard rejects the set
  of operands iff at least one operand in the walk is simultaneously a
  query-expression operand and not-permitted; otherwise it accepts (returns
  normally), even if some operand is not-permitted but is plain data.

The operand walk is modelled as the flattened traversal order of the operand
and its nested sub-operands: two index-aligned ``List[int]`` carry, per visited
operand, whether it is a query-expression operand (``is_expr[i]`` in {0,1}) and
whether it is permitted on this side (``permitted[i]`` in {0,1}; an operand that
exposes no marker defaults to permitted = 1). The discriminating observable is
purely WHICH outcome the guard produces (accept vs. reject), not the operands'
contents; Nagini bans ``str`` indexing, so operand identity is abstracted to
these two per-operand booleans. The rejection the guard raises is a user-defined
exception class (a builtin exception in an ``Exsures`` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class OperandNotAllowed(Exception):
    """The rejection the guard raises when a disallowed query-expression operand
    is encountered. User-defined stand-in for the not-supported error the
    desired behaviour requires (a builtin exception in an ``Exsures`` crashes the
    Nagini translator; mapping.md §2)."""
    pass

# axioms-start
# No consumed axioms: the guard's decision is a conjunction of two per-operand
# observations (is-a-query-expression and is-permitted) over the operand walk,
# modelled deeply over index-aligned integer carriers. There is no unchanged
# library callee the proof must stand in for.
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required: the decision is stated inline
#  over the two per-operand carriers.)
# pure-end

def check_operands(is_expr: List[int], permitted: List[int]) -> None:
    # pre-conditions-start
    # The two index-aligned carriers describe the flattened operand walk; the
    # guard only READS them (fractional permission, directive 5).
    Requires(Acc(list_pred(is_expr), 1 / 2))
    Requires(Acc(list_pred(permitted), 1 / 2))
    # one entry per visited operand: the walk has a single shape.
    Requires(len(is_expr) == len(permitted))
    # each entry is a boolean flag in {0, 1}.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(is_expr),
                                            is_expr[k] == 0 or is_expr[k] == 1))))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(permitted),
                                            permitted[k] == 0 or permitted[k] == 1))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The inputs are read-only: returned untouched at the same fractional
    # permission. Holding only fractional permission throughout, the guard
    # cannot have mutated either carrier (directive 5); their lengths and
    # contents are therefore unchanged with no further clause needed.
    Ensures(Acc(list_pred(is_expr), 1 / 2))
    Ensures(Acc(list_pred(permitted), 1 / 2))
    Ensures(len(is_expr) == len(permitted))
    # Accept (return normally) ONLY when NO operand in the walk is BOTH a
    # query-expression operand AND not-permitted. An ordinary data operand that
    # is merely not-permitted (is_expr == 0) does not block acceptance.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(is_expr),
                                            not (is_expr[k] == 1 and permitted[k] == 0)))))
    # Reject (raise) iff at least one operand in the walk is SIMULTANEOUSLY a
    # query-expression operand and not-permitted. This is the discriminating
    # conjunction: the query-expression test must hold too, so plain not-permitted
    # data passes through. The read-only carriers are re-established at the same
    # fractional permission on the rejecting path as well.
    Exsures(OperandNotAllowed,
            Acc(list_pred(is_expr), 1 / 2) and Acc(list_pred(permitted), 1 / 2)
            and len(is_expr) == len(permitted)
            and Exists(int, lambda k: (0 <= k and k < len(is_expr)
                                       and is_expr[k] == 1 and permitted[k] == 0)))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(is_expr):
        # invariants-start
        Invariant(Acc(list_pred(is_expr), 1 / 2))
        Invariant(Acc(list_pred(permitted), 1 / 2))
        Invariant(len(is_expr) == len(permitted))
        Invariant(0 <= i and i <= len(is_expr))
        # no disallowed operand has been seen among the visited prefix.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))
        Invariant(MustTerminate(len(is_expr) - i + 1))
        # invariants-end
        if is_expr[i] == 1 and permitted[i] == 0:
            raise OperandNotAllowed()
        i = i + 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity, A legs) for django__django-13028 nagini. All attacks built by copying model.py and editing ONLY the impl region (invariants included, which are nested inside impl); all 15 confirmed spec byte-identical via `python -m swebench_unified.adversary same-spec nagini django__django-13028 <f>` (exit 0, 'SAME'). Every attack then run through `python -m swebench_unified.adversary weakness nagini django__django-13028 <f>`, in concurrent batches of 3 (each Nagini check spawns JVM+Z3).

POSITIVE CONTROL pos_control.py (verbatim model.py): CANDIDATE — shares spec AND verifies (17.2s). Spec is live and non-vacuous.

**PREPATCH REPRODUCED:** atk_0_prepatch.py (= bundle model_prepatch.py, disallow test drops the is_expr[i]==1 conjunct, screening only permitted[i]==0). weakness => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). The spec senses the gold change (G-DIFF), failing exactly on the Exsures existential: on a plain-data not-permitted operand (is_expr=0, permitted=0) it raises although no query-expression not-permitted operand exists. This is the F2P case (Author.objects.filter(extra=self.e2) where ExtraInfo has a field literally named filterable=False).

### ATTACK-BY-ATTACK (all files, all same-spec, command = adversary weakness nagini django__django-13028 <path>):
1. atk_1_toponly.py — PARTIAL DOMAIN: screens only walk index 0, drops the recursive tail into sub-operands. REJECTED (does not verify, exit 2). Kills the A2 recursion-collapse leg being under-covered.
2. atk_2_offbyone.py — BOUNDARY: loop bound len-1, last visited operand never screened. REJECTED (exit 2).
3. atk_3_disjunction.py — CONTROL-FLOW-EFFECT / wrong connective: `or` instead of `and` (over-rejection: any expression, or any not-permitted operand). REJECTED (exit 2). This is the dual failure mode of the prepatch bug and the spec catches both directions.
4. atk_4_neverraise.py — guard deleted entirely (max under-rejection). REJECTED (exit 2).
5. atk_5_isexpr_only.py — the OTHER single conjunct: screens is_expr only, ignoring the marker. REJECTED (exit 2).
6. atk_6_reverse_walk.py — A-LEG on WALK ORDER: traverses the flattened walk in reverse (raise fires on the LAST disallowed operand). CANDIDATE (verifies, 17.8s). Faithful patch materialized = post-order guard (recurse into reversed sub-operands FIRST, then screen self); patch_atk6.diff, applied at base_commit 78ad4b4b. run_resolve => resolved=True completed=True, FAIL_TO_PASS 2 pass / 0 fail, PASS_TO_PASS 276 pass / 0 fail. CORRECT ECHO, not a weakness — walk order is genuinely unobservable to the graded tests (accept/reject is order-independent since the guard is a pure any()).
7. atk_7_deferred_raise.py — A-LEG on RAISE SITE: scans the entire walk into a flag, raises only afterwards (the real guard would walk all remaining operands the gold's early raise skips). CANDIDATE (verifies, 17.9s). Faithful patch = `_scan_filterable` helper returning the last disallowed operand, raise deferred past the whole tree walk; patch_atk7.diff. run_resolve => resolved=True completed=True, F2P 2/2, P2P 276/276. CORRECT ECHO — the extra walk is side-effect-free (get_source_expressions is a pure accessor), so early vs deferred raise is unobservable.
8. atk_8_diverge.py — DIVERGENCE: correct decision, then spins forever on the accept path (would hang every graded query). REJECTED (exit 2) — method-level MustTerminate(2) does its job, consistent with the standing note that loop invariants alone do not reject a diverging rival.
9. atk_9_wrong_exc.py — WRONG REJECTION TYPE: correct decision but a clean walk raises ValueError (Exsures only names OperandNotAllowed). REJECTED (exit 2) — the universal accept postcondition forces normal return, so the escape hatch of raising an unlisted exception is closed.
10. atk_10_mutate.py — EFFECT: correct decision but writes permitted[i]=1, mutating the caller's operands. REJECTED (exit 2) — the 1/2 fractional permission (directive 5) is load-bearing, so the read-only claim in the postcondition comment is real and not just prose.
11. atk_11_shape_gated.py — PARTIAL DOMAIN on walk SHAPE: screens only when the walk has 2+ operands, so a lone disallowed expression sails through. Deliberately agrees with the gold on the F2P input, so the F2P test alone could not see it. REJECTED (exit 2).
12. atk_12_decoupled.py — EXISTENTIAL DECOUPLING (the subtlest): reject iff SOME operand is an expression AND SOME possibly DIFFERENT operand is not-permitted. Agrees with the gold on every single-operand walk (F2P still passes) and diverges only when the two properties sit on different operands. REJECTED (exit 2) — the Exsures binds both conjuncts to the SAME index k, which is exactly what makes this the right spec.
13. atk_13_always_raise.py — UNGROUNDED-ORACLE ECHO: unconditional raise, decision never reads the carriers. REJECTED (exit 2) — the Exsures existential is genuinely grounded in the inputs, not satisfiable by a constant.
14. atk_14_vacuity.py — VACUITY CONTROL: Assert(False) as the impl. REJECTED (does not verify) => the precondition is satisfiable and the spec proves something. (Note: the weakness wrapper prints exit 0 on the shell's $? here because of the pipeline through tail; the substantive line is NOT-A-COUNTEREXAMPLE / does not verify. The runner re-derives this mechanically.)

EXTRA A-LEG PROBE (not an attack file — a direct resolve probe of an abstracted leg): mapping.md §2 claims the rejection MESSAGE payload (expression.`__class__`.`__name__` + ' is disallowed in the filter clause.') is unobserved by the graded tests. The model carries no message at all, so any message is refinement-legal. I materialized the most hostile legal choice — the gold conjunct with `raise NotSupportedError('')` (patch_payload.diff) — and ran run_resolve: resolved=True completed=True. Confirms the payload abstraction is sound for THIS instance's graded set. I separately verified this is not an accident of test selection: the only message assertions on this string in the repo live in tests/expressions_window/tests.py:843,868, which are not in this instance's F2P (2 tests) or P2P (276 tests, all queries.tests.*) — so no graded test reads the message.

REFINEMENT.MD AUDIT (leg kinds): 3 legs, all admissible, no kind-3.
- A1 (params is_expr/permitted <-> the expression argument + its transitive get_source_expressions operands) — tagged R. Sound: the bijection is per-operand, is_expr[i] <-> hasattr(op,'resolve_expression'), permitted[i] <-> getattr(op,'filterable',True) with absent => True => 1. The 'absent attribute defaults to permitted' case is the one that carries the F2P semantics and is stated explicitly in mapping.md §2. Preconditions ({0,1} entries, equal lengths) are satisfied by EVERY flattening of a real operand tree by construction, so the R leg excludes no real input.
- A2 (the while loop <-> the top-level call plus the UNCHANGED recursive tail) — tagged R + I, with the tree->flat collapse carried as an A-reference. This is the only genuinely abstract leg and the one I attacked hardest: atk_1 (drop the recursion), atk_2 (drop the walk tail), atk_11 (gate on walk shape), atk_12 (decouple the two conjuncts across operands) and atk_6 (walk order) all probe it; the first four are rejected by the verifier and the fifth resolves. Correspondence to the real callee holds: the recursion guard hasattr(expression,'get_source_expressions') at query.py:1132 is byte-unchanged by the gold patch (confirmed against the base_commit checkout), and because the SAME disallow test is applied at every node, the recursive guard raises iff some node in the pre-order traversal satisfies the conjunction — precisely `Exists k. is_expr[k]==1 and permitted[k]==0`. axiom_check.py backs this with an exhaustive 258-tree boundary space plus 20k fuzz trees against a faithful in-Python reference, and against the REAL Query.check_filterable when django is importable.
- A3 (the disallow test <-> the patched conjunction, OperandNotAllowed <-> NotSupportedError) — tagged R + I. Sound: the added hasattr(...,'resolve_expression') conjunct maps to is_expr[i]==1 and the discriminating content of the gold change lives DIRECTLY in the model's conjunct, not behind an axiom. The user-defined exception stand-in is forced (a builtin/db exception in an Exsures crashes the Nagini translator) and is observationally the raise itself; the message abstraction is separately resolve-probed above.
- No A-consumed legs exist (no @ContractOnly axiom; the axioms region is an explicit no-op comment), so there is no opaque oracle in the postcondition and no leg where the proof leans on an unvalidated Ensures. Refinement.md §C's no-kind-3 claim is accurate: the function under change IS the modelled function.

**CONCLUSION:** 15 same-spec wrong/rival impls run; 12 wrong impls (including the prepatch bug) mechanically REJECTED by the verifier; 1 vacuity control rejected; 2 CANDIDATEs whose faithful refined patches were BOTH materialized and RUN through the official harness, both RESOLVED (F2P 2/2, P2P 276/276) — correct echoes, so neither is a verify-but-incorrect break. No resolve run failed to complete. Verdict: SOUND (advisory; the runner re-runs these artifacts).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the spec is too strong / drifts from real post-patch Query.check_filterable (django/db/models/sql/query.py:1125). RESULT: no diverging input found; attack fails, spec is faithful.

SETUP: base worktree @78ad4b4b0201; patched worktree (gold patch.diff applied clean; confirmed the added `hasattr(expression,'resolve_expression') and` conjunct at query.py:1127-1131 with the UNCHANGED recursion tail at 1136-1138).

**SPEC REGION INTEGRITY:** `adversary same-spec` on a byte copy of bundle model.py -> exit 0 ("SAME"). Bundle model.py verifies under pinned Nagini ("Verification successful", 15.95s). model_prepatch.py shares the exact spec (same-spec exit 0) and FAILS on precisely the claimed clause: "Postcondition ... Exists(int, lambda k: (0<=k and k<len(is_expr) and is_expr[k]==1 and permitted[k]==0)) might not hold" -> G-DIFF genuinely senses the change, spec is not vacuous in the accept/reject direction.

BUNDLE GATES REPRODUCED against the patched tree: axiom_check.py exit 0 (258 boundary + 20000 fuzz; real Query.check_filterable matched incl. F2P plain-data case). conformance_check.py exit 0 (100258 trees, 0 disagreements).

MY INDEPENDENT ATTACKS (not the bundle's synthetic stand-ins -- REAL Django objects, my own bridge per mapping.md §2: is_expr[i]=hasattr(op,'resolve_expression'), permitted[i]=bool(getattr(op,'filterable',True))):
1. Hand-picked real-object battery (27 cases): F, Value, Value(None), Lower, Coalesce, Count, Window(RowNumber/Rank), Window nested in Coalesce, Case/When wrapping a Window, list/tuple/dict/set containers, int/str/None/bytes, QuerySet, Query, Q, Exists, OuterRef, plain object with filterable=False (the F2P shape), and a NON-expression that exposes the walk hook with a disallowed expression child. Every case: real outcome == model predicate. The two rows printed DIVERGE were unbound CLASS objects (Window / Value passed as classes, not instances) where my own bridge raised the identical TypeError as the real guard -- an artifact of passing a class, not an outcome disagreement.
2. Fuzz over REAL Django expression trees: 60000 trees built from Coalesce/Concat/Greatest/Case-When/ExpressionWrapper/Func/CombinedExpression over the leaf pool above, depth<=4, seed 20260813 -> 0 divergences.
3. Short-circuit / evaluation-order attack (the most promising angle, since the model reads BOTH carriers unconditionally while the real guard `and`-short-circuits): a non-expression whose `filterable` is a property that RAISES is ACCEPTed by the real guard (never touched) -- matches model, because that operand's permitted carrier is irrelevant once is_expr==0. An EXPRESSION with a raising `filterable` yields RuntimeError, i.e. no {0,1} carrier exists, so it is outside the spec's Requires domain, not a divergence. A disallowed operand followed by a sibling that errors on traversal: real REJECTs (short-circuits before the bad sibling) == model REJECT; the reordered variant raises TypeError for real AND leaves the flattening undefined, so again no outcome disagreement.
4. Flat-wide carriers (the shape the model's loop actually represents): 100 / 10000 / 200000 sibling operands, with and without a disallowed operand in LAST position -> real == model in all six runs. Confirms the existential is genuinely position-independent, not accidentally passing only on early hits.
5. Deep-recursion boundary: at ~1000+ nesting depth the real recursive guard raises RecursionError where the model ACCEPTs. I ruled this out as a faithfulness break: I implemented the PRE-patch guard and it raises RecursionError at the same depth, so this is a CPython interpreter stack limit that is completely unchanged by the gold patch -- it is not behavior the patch introduces, is unreachable from any ORM filter path, and is not the pinned accept/reject observable. Cyclic operand graphs likewise have no finite flattening, so they sit outside the carriers' expressible domain rather than contradicting the spec.

**ORACLE CROSS-CHECK:** F2P both pass on the patched tree (queries.tests.Queries1Tests.test_field_with_filterable, test_ticket8439 -- 2 tests OK). Broad regression sweep queries+expressions+annotations+aggregation: 656 tests, OK (17 skipped, 2 expected failures). expressions_window suite OK.

DOCUMENTED-ABSTRACTION NOTE (not a defect, no diverging input): the model abstracts away the NotSupportedError message payload (`expression.__class__.__name__ + ' is disallowed in the filter clause.'`). tests/expressions_window/tests.py:843,868 assert that message text via assertRaisesMessage. This is disclosed in mapping.md §1 and refinement.md A3, the message construction is byte-identical pre- and post-patch (the gold hunk touches only the `if` condition), and those tests are P2P and pass -- so nothing the patch changes rides on the payload. The strength of the spec is also correctly calibrated rather than over-tight: the Exsures is an existential conjunction over the actual input carriers (produced, not echoed), and the accept-direction Ensures is the exact negation, so the spec admits precisely the post-patch decision function and no more.

**CONCLUSION:** FAITHFUL. Across ~160k modeled trees plus real-Django batteries and targeted short-circuit/order/width/depth attacks I could not produce an in-domain input where the modeled function's accept/reject outcome disagrees with the real post-patch Query.check_filterable. The one real-vs-model outcome gap (deep-recursion RecursionError) is patch-invariant interpreter behavior outside the pinned observable and outside the finite-carrier domain, so it does not support an UNFAITHFUL verdict.

**ATTACK GOAL:** show the spec is too strong / drifts from real post-patch Query.check_filterable (django/db/models/sql/query.py:1125). RESULT: no diverging input found; attack fails, spec is faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) on django__django-13028 nagini. Scope: the SOLVER-VISIBLE spec_view over model.py (impl elided), judged against the PUBLIC problem_statement ONLY (never hints_text).

**SPEC BINDING.** same-spec identity attack => 'SAME', exit 0. Confirmed the consumer surface is genuinely elided: ELISION_IMPL present; the discriminating branch 'if is_expr[i] == 1 and permitted[i] == 0' and 'raise OperandNotAllowed()' and the 'while i <' loop are all ABSENT from the view. So the gold's decision procedure is not visible as code.

MECHANICAL SCREEN + BITE CONTROL (the part that matters -- a passing screen proves nothing unless it can fail). leakage.screen() on the real frozen row's 'patch' returns passed=True, failures=[]. I then ran 5 positive controls to prove the screen has bite on THIS instance: C1 quoting the gold added line "hasattr(expression, 'resolve_expression') and" => CAUGHT (L1); C2 naming 'django/db/models/sql/query.py' => CAUGHT (L2); C3 narrating 'The bug was... the fix adds a conjunct' => CAUGHT (L3). Two controls were NOT caught, i.e. genuine blind spots I had to adjudicate by hand rather than trust the tool: C4 renaming the model fn to 'check_filterable_guard' and C5 writing 'the operand must expose resolve_expression' in a comment both PASS the screen.

Reason: `_patch_changed_symbols` only harvests def/class names from changed lines, and this gold hunk changes no def/class line -- the only screened symbol is 'check_related_objects' (from the hunk section header). So L2/L5 symbol matching is effectively inert here. I therefore verified those two axes MANUALLY over the actual view: zero occurrences of resolve_expression, check_filterable, filterable, NotSupportedError, get_source_expressions, query.py, hasattr, getattr, `_meta`, base_commit 78ad4b4b, 'disallowed in the filter', and no diff markers. Only 'django' hit is the public instance-id header. Test-identity scan also clean (test_field_with_filterable, ExtraInfo, Author, assertSequenceEqual, BooleanField, self.e2 all 0), so no hidden-test leak either.

THE REAL QUESTION (semantic). The mechanical screen is near-toothless on the symbol axis here, so the verdict rests on whether the view's discriminator -- 'reject iff an operand is BOTH a query-expression operand (one that participates in query resolution) AND not-permitted' -- is derivable from public material or is hints-only. This is the exact shape that made django-11087 a genuine LEAKAGE (relaxed) bundle, so I did not want to hand-wave it. Note the vocabulary IS hints-adjacent: hints_text contains 'checking if rhs is an expression' + resolve_expression + hasattr, none of which appear in problem_statement. That is a real reason for suspicion and is why I tested it empirically instead of asserting it.

**DERIVABILITY EXPERIMENT.** I ran blind probes: fresh agents given ONLY the public problem_statement plus a clean django worktree at base_commit, forbidden from touching the bundle or git history/upstream patches. My first probe was METHODOLOGICALLY INVALID and I discarded its confirmatory result -- my own question named 'resolve_expression', leaking the answer before the agent answered. I re-ran two independent probes whose prompts never mention the discriminator (probe A asked only 'what principle chose that condition over alternatives'; probe B asked for the semantic rule + a 1-5 rating of how uniquely the report pinned it). BOTH independently produced the gold patch verbatim, including the parenthesized multi-line form, from PS + repo reading alone.

Both cited the same public in-repo evidence: 'filterable' is declared exactly twice in django/ (BaseExpression.filterable=True at expressions.py:159 under the comment 'Can the expression be used in a WHERE clause?', Window.filterable=False at 1205) and is documented in docs/ref/models/expressions.txt as an EXPRESSION-API attribute, while hasattr(x,'resolve_expression') is django's house duck-type for 'is an expression', used in resolve_lookup_value at query.py:1063 immediately before the check_filterable(value) call. Both also rejected isinstance(BaseExpression) and the `_meta` blacklist on their own. Both learned the nested-sub-operand recursion from the UNCHANGED function body itself (lines 1132-1134, visible at base_commit) and from pre-existing tests/expressions_window.

Crucially, the traceback in the PUBLIC problem_statement already names check_filterable, sql/query.py:1131, NotSupportedError, and 'ProductMetaDataType is disallowed in the filter clause' -- printing a MODEL class name where an expression was expected -- and the PS narrative states that a plain model instance with a filterable=False field must not raise. So the plain-data-vs-expression distinction is publicly disclosed; the view adds no localization the public text lacks.

Honest caveat, recorded rather than suppressed: probe B rated the report only 2/5 for uniquely determining the condition, noting PS leaves the RESOLUTION open ('This should be documented or fix') and that the choice of resolve_expression over isinstance was settled by codebase convention, not by the report. But the leakage standard is derivability from problem_statement + the repo the solver already has, not derivability from PS prose in isolation -- and both probes cleared that bar unaided and unprompted. The view's phrasing 'participates in query resolution' is an ABSTRACT category description that does not name resolve_expression, BaseExpression, or `_meta`, and so does not adjudicate among those candidate predicates; the solver must still pick one from the repo, exactly as the probes did.

Edge finding (not leakage, flagged for hygiene): meta.json's top-level region_hashes.spec_view is STALE -- it records 849f0e21 while the current model.py hashes to 48e17225. Diffing the two spec views, the delta is only the later addition of 'from nagini_contracts.obligations import MustTerminate' and 'Requires(MustTerminate(2))'. Termination obligations, not edit content, so it does not change the leakage verdict; but it means the recorded G-PANEL-3 pass judged different bytes than the bundle now ships, and meta's gates.G-HYGIENE block already carries the newer hash (inconsistent with the top-level block). Worth a bundle-hygiene refresh.

The operand-tree -> flattened-carrier abstraction is the inherent content of a verification twin, not a localization of the edit. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
