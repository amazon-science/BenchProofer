# P2 adversarial audit — django__django-16315

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Forall(int, lambda k: Implies(
         0 <= k and k < len(requested),
         name_present(ToSeq(requested)[k], ToSeq(field_names)))))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(requested), 1 / 2))
@@ -115,7 +113,6 @@
             0 <= k and k < i,
             ToSeq(result)[k] == column_for(
                 ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
-        Invariant(MustTerminate(len(requested) - i + 1))
         # invariants-end
         # the i-th requested name is registered (instantiate the Forall):
         Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
@@ -134,7 +131,6 @@
     Requires(Acc(list_pred(field_columns), 1 / 4))
     Requires(len(field_columns) == len(field_names))
     Requires(name_present(name, ToSeq(field_names)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field_names), 1 / 4))
@@ -156,7 +152,6 @@
         Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                   column_for(name, ToSeq(field_names).drop(j),
                              ToSeq(field_columns).drop(j)))
-        Invariant(MustTerminate(len(field_names) - j + 1))
         # invariants-end
         # one front-unfold of name_present/column_for over the suffix at j:
         Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
@@ -165,7 +160,7 @@
         Assert(ToSeq(field_columns).drop(j).drop(1) == ToSeq(field_columns).drop(j + 1))
         if field_names[j] == name:
             # first match: column_for over the suffix returns this slot's column
-            return field_columns[j]
+            return field_names[j]  # ATTACK1: return NAME not column (prepatch bug)
         # no match here -> the suffix's answer is the answer of the next suffix
         Assert(name_present(name, ToSeq(field_names).drop(j + 1)))
         j = j + 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Forall(int, lambda k: Implies(
         0 <= k and k < len(requested),
         name_present(ToSeq(requested)[k], ToSeq(field_names)))))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(requested), 1 / 2))
@@ -115,7 +113,6 @@
             0 <= k and k < i,
             ToSeq(result)[k] == column_for(
                 ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
-        Invariant(MustTerminate(len(requested) - i + 1))
         # invariants-end
         # the i-th requested name is registered (instantiate the Forall):
         Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
@@ -134,7 +131,6 @@
     Requires(Acc(list_pred(field_columns), 1 / 4))
     Requires(len(field_columns) == len(field_names))
     Requires(name_present(name, ToSeq(field_names)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field_names), 1 / 4))
@@ -156,7 +152,6 @@
         Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                   column_for(name, ToSeq(field_names).drop(j),
                              ToSeq(field_columns).drop(j)))
-        Invariant(MustTerminate(len(field_names) - j + 1))
         # invariants-end
         # one front-unfold of name_present/column_for over the suffix at j:
         Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
@@ -164,7 +159,9 @@
         Assert(ToSeq(field_names).drop(j).drop(1) == ToSeq(field_names).drop(j + 1))
         Assert(ToSeq(field_columns).drop(j).drop(1) == ToSeq(field_columns).drop(j + 1))
         if field_names[j] == name:
-            # first match: column_for over the suffix returns this slot's column
+            # ATTACK2 (boundary/off-by-one): return the NEXT slot's column
+            if j + 1 < len(field_columns):
+                return field_columns[j + 1]
             return field_columns[j]
         # no match here -> the suffix's answer is the answer of the next suffix
         Assert(name_present(name, ToSeq(field_names).drop(j + 1)))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Forall(int, lambda k: Implies(
         0 <= k and k < len(requested),
         name_present(ToSeq(requested)[k], ToSeq(field_names)))))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(requested), 1 / 2))
@@ -115,12 +113,14 @@
             0 <= k and k < i,
             ToSeq(result)[k] == column_for(
                 ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
-        Invariant(MustTerminate(len(requested) - i + 1))
         # invariants-end
         # the i-th requested name is registered (instantiate the Forall):
         Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
-        # resolve the requested name to a declared field, then take its column.
-        col = lookup(requested[i], field_names, field_columns)
+        # ATTACK3 (partial-domain): special-case first element to slot-0 column
+        if i == 0:
+            col = field_columns[0]
+        else:
+            col = lookup(requested[i], field_names, field_columns)
         result = result + [col]
         Assert(ToSeq(result)[i] == col)
         i = i + 1
@@ -134,7 +134,6 @@
     Requires(Acc(list_pred(field_columns), 1 / 4))
     Requires(len(field_columns) == len(field_names))
     Requires(name_present(name, ToSeq(field_names)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field_names), 1 / 4))
@@ -156,7 +155,6 @@
         Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                   column_for(name, ToSeq(field_names).drop(j),
                              ToSeq(field_columns).drop(j)))
-        Invariant(MustTerminate(len(field_names) - j + 1))
         # invariants-end
         # one front-unfold of name_present/column_for over the suffix at j:
         Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Forall(int, lambda k: Implies(
         0 <= k and k < len(requested),
         name_present(ToSeq(requested)[k], ToSeq(field_names)))))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(requested), 1 / 2))
@@ -115,7 +113,6 @@
             0 <= k and k < i,
             ToSeq(result)[k] == column_for(
                 ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
-        Invariant(MustTerminate(len(requested) - i + 1))
         # invariants-end
         # the i-th requested name is registered (instantiate the Forall):
         Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
@@ -124,6 +121,8 @@
         result = result + [col]
         Assert(ToSeq(result)[i] == col)
         i = i + 1
+    # ATTACK4 (control-flow-effect): emit one extra element (length mismatch)
+    result = result + [0]
     return result
     # impl-end
 
@@ -134,7 +133,6 @@
     Requires(Acc(list_pred(field_columns), 1 / 4))
     Requires(len(field_columns) == len(field_names))
     Requires(name_present(name, ToSeq(field_names)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field_names), 1 / 4))
@@ -156,7 +154,6 @@
         Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                   column_for(name, ToSeq(field_names).drop(j),
                              ToSeq(field_columns).drop(j)))
-        Invariant(MustTerminate(len(field_names) - j + 1))
         # invariants-end
         # one front-unfold of name_present/column_for over the suffix at j:
         Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Forall(int, lambda k: Implies(
         0 <= k and k < len(requested),
         name_present(ToSeq(requested)[k], ToSeq(field_names)))))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(requested), 1 / 2))
@@ -115,12 +113,11 @@
             0 <= k and k < i,
             ToSeq(result)[k] == column_for(
                 ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
-        Invariant(MustTerminate(len(requested) - i + 1))
         # invariants-end
         # the i-th requested name is registered (instantiate the Forall):
         Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
-        # resolve the requested name to a declared field, then take its column.
-        col = lookup(requested[i], field_names, field_columns)
+        # ATTACK5 (ungrounded-oracle echo): emit the requested NAME, not the column
+        col = requested[i]
         result = result + [col]
         Assert(ToSeq(result)[i] == col)
         i = i + 1
@@ -134,7 +131,6 @@
     Requires(Acc(list_pred(field_columns), 1 / 4))
     Requires(len(field_columns) == len(field_names))
     Requires(name_present(name, ToSeq(field_names)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field_names), 1 / 4))
@@ -156,7 +152,6 @@
         Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                   column_for(name, ToSeq(field_names).drop(j),
                              ToSeq(field_columns).drop(j)))
-        Invariant(MustTerminate(len(field_names) - j + 1))
         # invariants-end
         # one front-unfold of name_present/column_for over the suffix at j:
         Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Forall(int, lambda k: Implies(
         0 <= k and k < len(requested),
         name_present(ToSeq(requested)[k], ToSeq(field_names)))))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(requested), 1 / 2))
@@ -115,7 +113,6 @@
             0 <= k and k < i,
             ToSeq(result)[k] == column_for(
                 ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
-        Invariant(MustTerminate(len(requested) - i + 1))
         # invariants-end
         # the i-th requested name is registered (instantiate the Forall):
         Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
@@ -134,7 +131,6 @@
     Requires(Acc(list_pred(field_columns), 1 / 4))
     Requires(len(field_columns) == len(field_names))
     Requires(name_present(name, ToSeq(field_names)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field_names), 1 / 4))
@@ -156,7 +152,6 @@
         Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                   column_for(name, ToSeq(field_names).drop(j),
                              ToSeq(field_columns).drop(j)))
-        Invariant(MustTerminate(len(field_names) - j + 1))
         # invariants-end
         # one front-unfold of name_present/column_for over the suffix at j:
         Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
@@ -164,8 +159,8 @@
         Assert(ToSeq(field_names).drop(j).drop(1) == ToSeq(field_names).drop(j + 1))
         Assert(ToSeq(field_columns).drop(j).drop(1) == ToSeq(field_columns).drop(j + 1))
         if field_names[j] == name:
-            # first match: column_for over the suffix returns this slot's column
-            return field_columns[j]
+            # ATTACK6 (constant): always return slot-0 column
+            return field_columns[0]
         # no match here -> the suffix's answer is the answer of the next suffix
         Assert(name_present(name, ToSeq(field_names).drop(j + 1)))
         j = j + 1
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -81,7 +80,6 @@
     Requires(Forall(int, lambda k: Implies(
         0 <= k and k < len(requested),
         name_present(ToSeq(requested)[k], ToSeq(field_names)))))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(requested), 1 / 2))
@@ -115,7 +113,6 @@
             0 <= k and k < i,
             ToSeq(result)[k] == column_for(
                 ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
-        Invariant(MustTerminate(len(requested) - i + 1))
         # invariants-end
         # the i-th requested name is registered (instantiate the Forall):
         Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
@@ -134,7 +131,6 @@
     Requires(Acc(list_pred(field_columns), 1 / 4))
     Requires(len(field_columns) == len(field_names))
     Requires(name_present(name, ToSeq(field_names)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(field_names), 1 / 4))
@@ -156,7 +152,6 @@
         Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                   column_for(name, ToSeq(field_names).drop(j),
                              ToSeq(field_columns).drop(j)))
-        Invariant(MustTerminate(len(field_names) - j + 1))
         # invariants-end
         # one front-unfold of name_present/column_for over the suffix at j:
         Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
@@ -164,8 +159,11 @@
         Assert(ToSeq(field_names).drop(j).drop(1) == ToSeq(field_names).drop(j + 1))
         Assert(ToSeq(field_columns).drop(j).drop(1) == ToSeq(field_columns).drop(j + 1))
         if field_names[j] == name:
-            # first match: column_for over the suffix returns this slot's column
-            return field_columns[j]
+            # ATTACK7 (alternative-correct / echo): still the first match's column,
+            # just re-expressed via a local before returning.
+            answer = field_columns[j]
+            Assert(answer == column_for(name, ToSeq(field_names), ToSeq(field_columns)))
+            return answer
         # no match here -> the suffix's answer is the answer of the next suffix
         Assert(name_present(name, ToSeq(field_names).drop(j + 1)))
         j = j + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a batch insertion is configured to resolve row conflicts by updating a
  set of requested fields keyed on a set of requested conflict fields, the
  conflict-resolution clause that is handed to the backend must refer to each
  requested field by its configured *storage identifier* (the column the field
  is stored under), NOT by the field's in-memory attribute name.

  Each requested field is named by the caller; the schema resolves that name to
  the field it designates. A field's storage identifier equals its declared
  storage-column override when one is configured, and equals the field's own
  name otherwise. Two requested fields therefore produce DIFFERENT identifiers
  exactly when their storage-column overrides (or names, absent an override)
  differ -- never merely because the caller spelled the request differently.

  The list produced for the backend has the same length and order as the list
  of requested names, and element i is the storage identifier of the field that
  the i-th requested name designates.

A field is modelled as a minimal record carrying only the two touched
attributes: its name and its storage identifier (its column). The schema's
name->field resolution (the unchanged lookup) is modelled deeply as a registry
of parallel name/column lists; resolving a name yields the column registered
against the matching name. Identifiers are modelled as ints (the discriminator
is which identifier is selected, name vs column, not its textual content).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms are consumed: the name->column resolution is the
# UNCHANGED schema lookup, modelled deeply as a registry of parallel
# name/column lists -- it is not an opaque callee whose Ensures the proof
# relies upon. See refinement.md / mapping.md for the A-reference provenance.)
# axioms-end


# pure-start
@Pure
def name_present(name: int, names: PSeq[int]) -> bool:
    """True iff some registry slot carries field-name ``name``. Front-recursive
    (one unfold per skipped slot); total (no precondition)."""
    if len(names) == 0:
        return False
    if names[0] == name:
        return True
    return name_present(name, names.drop(1))


@Pure
def column_for(name: int, names: PSeq[int], columns: PSeq[int]) -> int:
    """Storage identifier the requested ``name`` designates: walk the registry
    name/column slots in parallel and return the column of the first slot whose
    name matches. Front-recursive and TOTAL (the empty guard never fires under a
    well-formed registry with the name present, but keeps the function free of a
    length precondition so it composes cleanly inside contracts)."""
    if len(names) == 0 or len(columns) == 0:
        return 0
    if names[0] == name:
        return columns[0]
    return column_for(name, names.drop(1), columns.drop(1))
# pure-end


def conflict_columns(requested: List[int], field_names: List[int],
                     field_columns: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(requested), 1 / 2))
    Requires(Acc(list_pred(field_names), 1 / 2))
    Requires(Acc(list_pred(field_columns), 1 / 2))
    # the registry is well-formed (one column per declared field) ...
    Requires(len(field_columns) == len(field_names))
    # ... and every requested name designates a declared field (the lookup the
    # schema performs without error).
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(requested),
        name_present(ToSeq(requested)[k], ToSeq(field_names)))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(requested), 1 / 2))
    Ensures(Acc(list_pred(field_names), 1 / 2))
    Ensures(Acc(list_pred(field_columns), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Same length and order as the requested-name list.
    Ensures(len(Result()) == len(requested))
    # Element i is the storage identifier the i-th requested name designates
    # (its column), NOT the requested name itself.
    Ensures(Forall(int, lambda k: Implies(
        0 <= k and k < len(requested),
        ToSeq(Result())[k] == column_for(
            ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(requested):
        # invariants-start
        Invariant(Acc(list_pred(requested), 1 / 2))
        Invariant(Acc(list_pred(field_names), 1 / 2))
        Invariant(Acc(list_pred(field_columns), 1 / 2))
        Invariant(len(field_columns) == len(field_names))
        Invariant(0 <= i and i <= len(requested))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < len(requested),
            name_present(ToSeq(requested)[k], ToSeq(field_names)))))
        Invariant(Acc(list_pred(result)) and len(result) == i)
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            ToSeq(result)[k] == column_for(
                ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
        # invariants-end
        # the i-th requested name is registered (instantiate the Forall):
        Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
        # resolve the requested name to a declared field, then take its column.
        col = lookup(requested[i], field_names, field_columns)
        result = result + [col]
        Assert(ToSeq(result)[i] == col)
        i = i + 1
    return result
    # impl-end


def lookup(name: int, field_names: List[int], field_columns: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(field_names), 1 / 4))
    Requires(Acc(list_pred(field_columns), 1 / 4))
    Requires(len(field_columns) == len(field_names))
    Requires(name_present(name, ToSeq(field_names)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field_names), 1 / 4))
    Ensures(Acc(list_pred(field_columns), 1 / 4))
    Ensures(Result() == column_for(name, ToSeq(field_names), ToSeq(field_columns)))
    # post-conditions-end
    # impl-start
    j = 0
    while j < len(field_names):
        # invariants-start
        Invariant(Acc(list_pred(field_names), 1 / 4))
        Invariant(Acc(list_pred(field_columns), 1 / 4))
        Invariant(len(field_columns) == len(field_names))
        Invariant(0 <= j and j <= len(field_names))
        # the name is still present in the unscanned suffix, and the column it
        # designates over the whole registry equals the column it designates
        # over that suffix (no earlier slot matched).
        Invariant(name_present(name, ToSeq(field_names).drop(j)))
        Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                  column_for(name, ToSeq(field_names).drop(j),
                             ToSeq(field_columns).drop(j)))
        # invariants-end
        # one front-unfold of name_present/column_for over the suffix at j:
        Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
        Assert(ToSeq(field_columns).drop(j)[0] == field_columns[j])
        Assert(ToSeq(field_names).drop(j).drop(1) == ToSeq(field_names).drop(j + 1))
        Assert(ToSeq(field_columns).drop(j).drop(1) == ToSeq(field_columns).drop(j + 1))
        if field_names[j] == name:
            # first match: column_for over the suffix returns this slot's column
            return field_columns[j]
        # no match here -> the suffix's answer is the answer of the next suffix
        Assert(name_present(name, ToSeq(field_names).drop(j + 1)))
        j = j + 1
    # unreachable: name_present guarantees a match before j == len
    Assert(False)
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Env: python, SBU_BENCHMARK_DIR=benchmark-verified, run. Positive control (unedited model.py) => CANDIDATE (same-spec + verifies, 22.6s).

### ATTACKS (all spec/pure regions byte-identical to bundle; same-spec exit 0 for all 7; only impl regions edited):
- atk_1 (prepatch bug, `lookup` returns field_names[j] = the NAME): `python -m swebench_unified.adversary weakness nagini django__django-16315 atk_1.py` => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). PREPATCH REPRODUCED.
- atk_2 (boundary/off-by-one: on match return field_columns[j+1]): weakness => does not verify (exit 2).
- atk_3 (partial-domain: first requested element hard-wired to field_columns[0]): weakness => does not verify (exit 2).
- atk_4 (control-flow-effect: append extra trailing element, len(Result())!=len(requested)): weakness => does not verify (exit 2).
- atk_5 (ungrounded-oracle echo at conflict_columns level: col=requested[i], the NAME): weakness => does not verify (exit 2).
- atk_6 (constant: `lookup` always returns field_columns[0]): weakness => does not verify (exit 2).
- atk_7 (alternative-correct/echo: `lookup` binds answer=field_columns[j] to a local, asserts ==column_for, returns it — behaviourally IDENTICAL to gold): weakness => CANDIDATE-COUNTEREXAMPLE (same-spec + verifies, 24.5s, exit 0).

MANDATORY RESOLVE for the one CANDIDATE (atk_7): materialized its faithful refined patch. Since atk_7 is behaviourally identical to the gold impl (still first-match storage COLUMN), its faithful patch is the gold patch verbatim. Ran it through the official harness via swebench_unified.harness.run_resolve('django__django-16315', <gold patch>, timeout=1800): RESOLVED=True, COMPLETED=True, ATTEMPTS=1, NOTE='resolved' (110s wall). => atk_7's faithful patch RESOLVES; it is a legitimate echo, NOT a spec break.

WHY THE SPEC IS TIGHT: the postconditions on conflict_columns fully pin the output — len(Result())==len(requested) AND Forall k in [0,len(requested)): Result()[k]==column_for(requested[k], field_names, field_columns). column_for lives in the FROZEN (non-editable) pure region and is G-AX-validated equal to the real Django callee _meta.get_field(name).column (axiom_check.py passed in-container over mixed-case db_column overrides rAnK/oTheRNaMe, discriminator required exercised, no double-mask). So any verifying impl is forced element-wise onto the exact gold storage-column projection; a functionally-wrong impl (wrong identifier, wrong length, wrong element) cannot verify — confirmed by atk_1..atk_6 all being rejected.

REFINEMENT.MD LEG AUDIT (A-legs focus): A1 (requested list) R; A2 (registry as parallel name/column lists) R; A3 (lookup -> column_for = get_field(name).column) A-REFERENCE — the sole changed op modeled DEEPLY, no consumed @ContractOnly axiom, correspondence machine-checked by axiom_check.py/G-AX (pass); A4 (element-wise build, len/order) I+R (G-CONF-covered); A5 (name_present precondition <-> get_field success domain) R. No kind-3 (unexpressible-changed-op) leg — the one genuinely changed operation (select storage column not name) is the deeply-modeled A-reference, not hidden behind an axiom about the function under change. mapping.md §3.1 binds column_for/conflict_columns to options.py:657 get_field + fields/__init__.py:894-897 get_attname_column (column=db_column or attname), both UNCHANGED callees — correspondence holds. axioms region empty (confirmed model.py lines 35-40).

CONCLUSION: 7 attacks run (6 distinct genuinely-wrong impls all rejected + prepatch reproduced + 1 echo whose faithful patch resolves). No verifying wrong impl exists whose faithful patch fails to resolve. Verify => correct holds for this bundle. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a batch insertion is configured to resolve row conflicts by updating a
  set of requested fields keyed on a set of requested conflict fields, the
  conflict-resolution clause that is handed to the backend must refer to each
  requested field by its configured *storage identifier* (the column the field
  is stored under), NOT by the field's in-memory attribute name.

  Each requested field is named by the caller; the schema resolves that name to
  the field it designates. A field's storage identifier equals its declared
  storage-column override when one is configured, and equals the field's own
  name otherwise. Two requested fields therefore produce DIFFERENT identifiers
  exactly when their storage-column overrides (or names, absent an override)
  differ -- never merely because the caller spelled the request differently.

  The list produced for the backend has the same length and order as the list
  of requested names, and element i is the storage identifier of the field that
  the i-th requested name designates.

A field is modelled as a minimal record carrying only the two touched
attributes: its name and its storage identifier (its column). The schema's
name->field resolution (the unchanged lookup) is modelled deeply as a registry
of parallel name/column lists; resolving a name yields the column registered
against the matching name. Identifiers are modelled as ints (the discriminator
is which identifier is selected, name vs column, not its textual content).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms are consumed: the name->column resolution is the
# UNCHANGED schema lookup, modelled deeply as a registry of parallel
# name/column lists -- it is not an opaque callee whose Ensures the proof
# relies upon. See refinement.md / mapping.md for the A-reference provenance.)
# axioms-end


# pure-start
@Pure
def name_present(name: int, names: PSeq[int]) -> bool:
    """True iff some registry slot carries field-name ``name``. Front-recursive
    (one unfold per skipped slot); total (no precondition)."""
    if len(names) == 0:
        return False
    if names[0] == name:
        return True
    return name_present(name, names.drop(1))


@Pure
def column_for(name: int, names: PSeq[int], columns: PSeq[int]) -> int:
    """Storage identifier the requested ``name`` designates: walk the registry
    name/column slots in parallel and return the column of the first slot whose
    name matches. Front-recursive and TOTAL (the empty guard never fires under a
    well-formed registry with the name present, but keeps the function free of a
    length precondition so it composes cleanly inside contracts)."""
    if len(names) == 0 or len(columns) == 0:
        return 0
    if names[0] == name:
        return columns[0]
    return column_for(name, names.drop(1), columns.drop(1))
# pure-end


def conflict_columns(requested: List[int], field_names: List[int],
                     field_columns: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(requested), 1 / 2))
    Requires(Acc(list_pred(field_names), 1 / 2))
    Requires(Acc(list_pred(field_columns), 1 / 2))
    # the registry is well-formed (one column per declared field) ...
    Requires(len(field_columns) == len(field_names))
    # ... and every requested name designates a declared field (the lookup the
    # schema performs without error).
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(requested),
        name_present(ToSeq(requested)[k], ToSeq(field_names)))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(requested), 1 / 2))
    Ensures(Acc(list_pred(field_names), 1 / 2))
    Ensures(Acc(list_pred(field_columns), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Same length and order as the requested-name list.
    Ensures(len(Result()) == len(requested))
    # Element i is the storage identifier the i-th requested name designates
    # (its column), NOT the requested name itself.
    Ensures(Forall(int, lambda k: Implies(
        0 <= k and k < len(requested),
        ToSeq(Result())[k] == column_for(
            ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(requested):
        # invariants-start
        Invariant(Acc(list_pred(requested), 1 / 2))
        Invariant(Acc(list_pred(field_names), 1 / 2))
        Invariant(Acc(list_pred(field_columns), 1 / 2))
        Invariant(len(field_columns) == len(field_names))
        Invariant(0 <= i and i <= len(requested))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < len(requested),
            name_present(ToSeq(requested)[k], ToSeq(field_names)))))
        Invariant(Acc(list_pred(result)) and len(result) == i)
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            ToSeq(result)[k] == column_for(
                ToSeq(requested)[k], ToSeq(field_names), ToSeq(field_columns)))))
        # invariants-end
        # the i-th requested name is registered (instantiate the Forall):
        Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))
        # resolve the requested name to a declared field, then take its column.
        col = lookup(requested[i], field_names, field_columns)
        result = result + [col]
        Assert(ToSeq(result)[i] == col)
        i = i + 1
    return result
    # impl-end


def lookup(name: int, field_names: List[int], field_columns: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(field_names), 1 / 4))
    Requires(Acc(list_pred(field_columns), 1 / 4))
    Requires(len(field_columns) == len(field_names))
    Requires(name_present(name, ToSeq(field_names)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field_names), 1 / 4))
    Ensures(Acc(list_pred(field_columns), 1 / 4))
    Ensures(Result() == column_for(name, ToSeq(field_names), ToSeq(field_columns)))
    # post-conditions-end
    # impl-start
    j = 0
    while j < len(field_names):
        # invariants-start
        Invariant(Acc(list_pred(field_names), 1 / 4))
        Invariant(Acc(list_pred(field_columns), 1 / 4))
        Invariant(len(field_columns) == len(field_names))
        Invariant(0 <= j and j <= len(field_names))
        # the name is still present in the unscanned suffix, and the column it
        # designates over the whole registry equals the column it designates
        # over that suffix (no earlier slot matched).
        Invariant(name_present(name, ToSeq(field_names).drop(j)))
        Invariant(column_for(name, ToSeq(field_names), ToSeq(field_columns)) ==
                  column_for(name, ToSeq(field_names).drop(j),
                             ToSeq(field_columns).drop(j)))
        # invariants-end
        # one front-unfold of name_present/column_for over the suffix at j:
        Assert(ToSeq(field_names).drop(j)[0] == field_names[j])
        Assert(ToSeq(field_columns).drop(j)[0] == field_columns[j])
        Assert(ToSeq(field_names).drop(j).drop(1) == ToSeq(field_names).drop(j + 1))
        Assert(ToSeq(field_columns).drop(j).drop(1) == ToSeq(field_columns).drop(j + 1))
        if field_names[j] == name:
            # first match: column_for over the suffix returns this slot's column
            return field_columns[j]
        # no match here -> the suffix's answer is the answer of the next suffix
        Assert(name_present(name, ToSeq(field_names).drop(j + 1)))
        j = j + 1
    # unreachable: name_present guarantees a match before j == len
    Assert(False)
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Env: python, SBU_BENCHMARK_DIR=benchmark-verified, run. Positive control (unedited model.py) => CANDIDATE (same-spec + verifies, 22.6s).

### ATTACKS (all spec/pure regions byte-identical to bundle; same-spec exit 0 for all 7; only impl regions edited):
- atk_1 (prepatch bug, `lookup` returns field_names[j] = the NAME): `python -m swebench_unified.adversary weakness nagini django__django-16315 atk_1.py` => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). PREPATCH REPRODUCED.
- atk_2 (boundary/off-by-one: on match return field_columns[j+1]): weakness => does not verify (exit 2).
- atk_3 (partial-domain: first requested element hard-wired to field_columns[0]): weakness => does not verify (exit 2).
- atk_4 (control-flow-effect: append extra trailing element, len(Result())!=len(requested)): weakness => does not verify (exit 2).
- atk_5 (ungrounded-oracle echo at conflict_columns level: col=requested[i], the NAME): weakness => does not verify (exit 2).
- atk_6 (constant: `lookup` always returns field_columns[0]): weakness => does not verify (exit 2).
- atk_7 (alternative-correct/echo: `lookup` binds answer=field_columns[j] to a local, asserts ==column_for, returns it — behaviourally IDENTICAL to gold): weakness => CANDIDATE-COUNTEREXAMPLE (same-spec + verifies, 24.5s, exit 0).

MANDATORY RESOLVE for the one CANDIDATE (atk_7): materialized its faithful refined patch. Since atk_7 is behaviourally identical to the gold impl (still first-match storage COLUMN), its faithful patch is the gold patch verbatim. Ran it through the official harness via swebench_unified.harness.run_resolve('django__django-16315', <gold patch>, timeout=1800): RESOLVED=True, COMPLETED=True, ATTEMPTS=1, NOTE='resolved' (110s wall). => atk_7's faithful patch RESOLVES; it is a legitimate echo, NOT a spec break.

WHY THE SPEC IS TIGHT: the postconditions on conflict_columns fully pin the output — len(Result())==len(requested) AND Forall k in [0,len(requested)): Result()[k]==column_for(requested[k], field_names, field_columns). column_for lives in the FROZEN (non-editable) pure region and is G-AX-validated equal to the real Django callee _meta.get_field(name).column (axiom_check.py passed in-container over mixed-case db_column overrides rAnK/oTheRNaMe, discriminator required exercised, no double-mask). So any verifying impl is forced element-wise onto the exact gold storage-column projection; a functionally-wrong impl (wrong identifier, wrong length, wrong element) cannot verify — confirmed by atk_1..atk_6 all being rejected.

REFINEMENT.MD LEG AUDIT (A-legs focus): A1 (requested list) R; A2 (registry as parallel name/column lists) R; A3 (lookup -> column_for = get_field(name).column) A-REFERENCE — the sole changed op modeled DEEPLY, no consumed @ContractOnly axiom, correspondence machine-checked by axiom_check.py/G-AX (pass); A4 (element-wise build, len/order) I+R (G-CONF-covered); A5 (name_present precondition <-> get_field success domain) R. No kind-3 (unexpressible-changed-op) leg — the one genuinely changed operation (select storage column not name) is the deeply-modeled A-reference, not hidden behind an axiom about the function under change. mapping.md §3.1 binds column_for/conflict_columns to options.py:657 get_field + fields/__init__.py:894-897 get_attname_column (column=db_column or attname), both UNCHANGED callees — correspondence holds. axioms region empty (confirmed model.py lines 35-40).

CONCLUSION: 7 attacks run (6 distinct genuinely-wrong impls all rejected + prepatch reproduced + 1 echo whose faithful patch resolves). No verifying wrong impl exists whose faithful patch fails to resolve. Verify => correct holds for this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) confirmed. The modeled conflict_columns/column_for/lookup capture 'per requested field name, the storage identifier (column) of the designated field, same length and order as the requested list.' This is exactly the composite of the gold patch's two hunks: bulk_create resolving names via _meta.get_field(name) (query.py) + the (f.column for f in ...) projection in SQLInsertCompiler.as_sql (compiler.py:1725).

Independent oracle probe (16315_faith_probe.py against real Django 4.2) verified the model agrees with the real Model._meta.get_field(name).column on every requested name across a model carrying: mixed-case db_column overrides (rank->rAnK, name->oTheRNaMe), a plain pk (id->id), a plain field (plain->plain), a ForeignKey without db_column (fk->fk_id, where attname!=name), and a ForeignKey with db_column (fk2->FKCOL). No diverging input found.

Minor prose nuance (NOT a divergence): mapping.md/meta describe column as 'db_column or name'; the real value is 'db_column or attname', which differs only for FK fields (fk -> fk_id, not fk). This is a documentation imprecision only — the executable model and BOTH gates build the registry from the REAL Field.column value directly (names.append(f.name); columns.append(f.column)), so the modeled function never disagrees with the real callee. The int abstraction is order-preserving and equal<->equal / distinct<->distinct, and column==name vs column!=name is exercised.

Gates independently support faithfulness: G-AX pass (deep model == real get_field(n).column across all field subsets of 2 models incl. the mixed-case discriminator, no double-mask, saw_override required). G-CONF pass on 101044 Requires-satisfying inputs (boundary permutations + 100000 fuzz over 200 random registries with override-collision stress + end-to-end intercepted bulk_create upserts capturing the exact identifier lists the patched compiler passes to on_conflict_suffix_sql; seed 163150). same-spec toolkit confirms the spec region is intact. Preconditions (registry well-formedness len(columns)==len(names) + every requested name registered) match the real reachability (patch runs after _check_bulk_create_options; F2P inputs name declared fields), so the spec is not vacuously narrow. No input exists where the spec disagrees with the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view hash recomputed via swebench_unified.markers.spec_view over model.py = 51b7245987bddd4eec581a55c468d0810f0a099ff3eb24c5723d1d7fe35365ec, matching meta.json G-HYGIENE; impl regions are correctly elided (both conflict_columns and lookup impl bodies show '...  # implementation elided'). Compared the spec view against the PUBLIC problem_statement only (not hints_text).

The problem_statement fully discloses the intended fix: bulk_create()'s ON CONFLICT clause uses the field NAME instead of the configured db_column, and it even shows the exact expected output ('ON CONFLICT("BlacklistID") DO UPDATE SET "SectorID" = EXCLUDED."SectorID", ...') vs the buggy lowercase field-name output. The db_column-override semantics (BlacklistID vs blacklistid) are demonstrated verbatim in the public report.

The spec view (docstring + Requires/Ensures) restates precisely this at the same behavioural altitude: 'must refer to each requested field by its configured storage identifier (the column ...), NOT by the field's in-memory attribute name'; 'storage identifier equals its declared storage-column override when configured, and equals the field's own name otherwise'; 'element i is the storage identifier the i-th requested name designates'. This is the same column-vs-name discriminator the public bug report already spells out.

The spec view does NOT go beyond the public statement toward the gold edit: no mention of _meta.get_field(name).column, no SQLInsertCompiler.as_sql generator (f.column for f in ...), no removal of the _check_bulk_create_options get_field conversions, no changed_files/line numbers (query.py/compiler.py). Those gold-edit specifics live only in mapping.md/meta.json (audit-side), which are not part of the spec view. Therefore the spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
