# P2 adversarial audit — django__django-11149

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,8 +75,6 @@
         # invariants-start
         Invariant(Acc(set_pred(held), 1 / 2))
         Invariant(0 <= i and i <= len(required))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(required) - i.
         Invariant(MustTerminate(len(required) - i))
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i, not (required[k] in held))))
@@ -84,7 +82,7 @@
         if required[i] in held:
             return True
         i = i + 1
-    return False
+    return target_decision(held, required)
     # impl-end
 
 
@@ -95,7 +93,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +113,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -136,7 +134,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +154,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,15 +75,12 @@
         # invariants-start
         Invariant(Acc(set_pred(held), 1 / 2))
         Invariant(0 <= i and i <= len(required))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(required) - i.
         Invariant(MustTerminate(len(required) - i))
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i, not (required[k] in held))))
         # invariants-end
         if required[i] in held:
             return True
-        i = i + 1
     return False
     # impl-end
 
@@ -95,7 +92,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +112,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -136,7 +133,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +153,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +115,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -124,7 +124,7 @@
     Ensures(Result() == (modify_code in held))
     # post-conditions-end
     # impl-start
-    required = PSeq(modify_code)
+    required = PSeq(inspect_code, modify_code)
     return target_decision(held, required)
     # impl-end
 
@@ -136,7 +136,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +156,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -71,12 +71,10 @@
     # post-conditions-end
     # impl-start
     i = 0
-    while i < len(required):
+    while i < len(required) - 1:
         # invariants-start
         Invariant(Acc(set_pred(held), 1 / 2))
         Invariant(0 <= i and i <= len(required))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(required) - i.
         Invariant(MustTerminate(len(required) - i))
         Invariant(Forall(int, lambda k: Implies(
             0 <= k and k < i, not (required[k] in held))))
@@ -95,7 +93,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +113,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -136,7 +134,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +154,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -95,7 +95,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +115,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -124,7 +124,7 @@
     Ensures(Result() == (modify_code in held))
     # post-conditions-end
     # impl-start
-    required = PSeq(modify_code)
+    required = PSeq(modify_code, modify_code)
     return target_decision(held, required)
     # impl-end
 
@@ -136,7 +136,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +156,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +115,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -124,7 +124,7 @@
     Ensures(Result() == (modify_code in held))
     # post-conditions-end
     # impl-start
-    required = PSeq(modify_code)
+    required = PSeq(inspect_code)
     return target_decision(held, required)
     # impl-end
 
@@ -136,7 +136,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +156,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +115,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -124,8 +124,7 @@
     Ensures(Result() == (modify_code in held))
     # post-conditions-end
     # impl-start
-    required = PSeq(modify_code)
-    return target_decision(held, required)
+    return inline_create_decision(held, inspect_code, modify_code)
     # impl-end
 
 
@@ -136,7 +135,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +155,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,21 +70,7 @@
     Ensures(Result() == holds_any(held, required))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(required):
-        # invariants-start
-        Invariant(Acc(set_pred(held), 1 / 2))
-        Invariant(0 <= i and i <= len(required))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(required) - i.
-        Invariant(MustTerminate(len(required) - i))
-        Invariant(Forall(int, lambda k: Implies(
-            0 <= k and k < i, not (required[k] in held))))
-        # invariants-end
-        if required[i] in held:
-            return True
-        i = i + 1
-    return False
+    return holds_any(held, required)
     # impl-end
 
 
@@ -95,7 +81,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(6))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -115,7 +101,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(10))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -136,7 +122,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(14))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
@@ -156,7 +142,7 @@
     # Each decision must be delivered in finite time; the measure leaves
     # room to invoke the shared membership scan (which carries a smaller
     # one).
-    Requires(MustTerminate(18))
+    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(set_pred(held), 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11149.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administrative interface renders an editable sub-collection that belongs to
  an automatically generated link table standing between two principal records.
  Such a link table carries no permissions of its own, so the four authorisation
  decisions for it — may the actor create, modify, remove, or merely inspect an
  entry — are derived from the permissions the actor holds on the *target*
  record that the link points to.

  The actor's authorisation is a set of held permission codes for the target
  record.  Two of those codes are significant here: an INSPECT code and a MODIFY
  code (distinct codes). The decisions are:

    (1) inspect is permitted exactly when the actor holds EITHER the inspect code
        OR the modify code for the target (modify subsumes inspect);

    (2) create, modify, and remove are EACH permitted exactly when the actor
        holds the MODIFY code for the target — holding only the inspect code must
        NOT permit any of them.

  Equivalently, every decision asks whether the actor holds ANY of a small list
  of required codes for the target record: the inspect decision requires
  {inspect, modify}; each of create / modify / remove requires {modify} alone.
  An actor granted inspect-only therefore gets a read-only collection.

The actor's held codes are modelled as ``PSet[int]``; a required-code list is a
``PSeq[int]``; holding a code is set membership; "holds any required code" is the
existential over the required list.  Each decision is the corresponding
``bool``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: a decision is a membership/any query over the actor's
# held permission codes, modelled deeply over PSet[int] / PSeq[int]. The code
# construction and the per-code membership test are unchanged callees refined to
# integer codes / set membership, not axioms the proof consumes — see
# refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def holds_any(held: PSet[int], required: PSeq[int]) -> bool:
    """The actor holds AT LEAST ONE of the required codes for the target record.
    This is the existential over the required-code list of the per-code holding
    test (set membership)."""
    return Exists(int, lambda j: 0 <= j and j < len(required) and required[j] in held)
# pure-end


def target_decision(held: PSet[int], required: PSeq[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    # The decision must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition
    # only vacuously by never returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # The decision is TRUE iff the actor holds any of the required codes.
    Ensures(Result() == holds_any(held, required))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(required):
        # invariants-start
        Invariant(Acc(set_pred(held), 1 / 2))
        Invariant(0 <= i and i <= len(required))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(required) - i.
        Invariant(MustTerminate(len(required) - i))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i, not (required[k] in held))))
        # invariants-end
        if required[i] in held:
            return True
        i = i + 1
    return False
    # impl-end


def inline_inspect_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Inspect is permitted iff the actor holds the inspect OR the modify code.
    Ensures(Result() == ((inspect_code in held) or (modify_code in held)))
    # post-conditions-end
    # impl-start
    required = PSeq(inspect_code, modify_code)
    return target_decision(held, required)
    # impl-end


def inline_create_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Create is permitted iff the actor holds the MODIFY code; the inspect code
    # alone must NOT permit it.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end


def inline_modify_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Modify is permitted iff the actor holds the MODIFY code.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end


def inline_remove_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Remove is permitted iff the actor holds the MODIFY code.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit of the REPAIRED frozen spec (model.py/refinement.md/mapping.md rev Aug 13 01:29-01:37). This cell was previously recorded G-EQ=fail (BROKEN) via prior atk_7 in run dsggkes3: a NON-TERMINATING recursion `return target_decision(held, required)` on the miss path verified under the OLD partial-correctness spec but hung the test suite (no-resolve). The repair adds `Requires(MustTerminate(...))` to every function's (frozen) pre-conditions region (wrappers measure 3, scan measure 2, loop measure len(required)-i) plus exact-equality postconditions. I re-audited whether the repaired spec still admits any verify-but-wrong impl.

 Positive control (model.py copy) VERIFIES (10.6s). Prepatch twin model_prepatch.py FAILS verification (postconditions of inline_modify/remove_decision don't hold) => prepatch_reproduced=true; spec senses the bug.

8 same-spec attacks (all `same-spec` exit 0; diffs confined to impl/invariant regions). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-11149 <path>`.
- atk_1 (control-flow-effect / re-encode OLD atk_7: recursion on miss path in target_decision): weakness exit=2 NOT-A-COUNTEREXAMPLE (does not verify — MustTerminate rejects it). REPAIR CONFIRMED.
- atk_2 (control-flow-effect / non-advancing loop, index never increments): exit=2 does not verify.
- atk_3 (prepatch bug / partial-domain: inline_create uses the VIEW rule PSeq(inspect_code,modify_code)): exit=2 does not verify (postcondition Result()==(modify_code in held) fails).
- atk_4 (boundary / off-by-one: scan `while i < len(required)-1` misses last element): exit=2 does not verify.
- atk_5 (ungrounded-oracle echo / CORRECT: inline_create uses PSeq(modify_code,modify_code), behaviourally identical): weakness exit=0 CANDIDATE (verifies 10.8s).
- atk_6 (partial-domain / wrong code: inline_create scans PSeq(inspect_code) only): exit=2 does not verify.
- atk_7 (control-flow-effect / wrapper self-recursion: inline_create returns inline_create_decision(...)): exit=2 does not verify (MustTerminate rejects — wrapper cannot delegate to an equal-measure callee).
- atk_8 (ungrounded-oracle echo / CORRECT: target_decision returns holds_any(held,required) directly = gold `any(...)`): weakness exit=0 CANDIDATE (verifies 10.8s).

BOTH candidates are behaviourally-correct echoes; materialized their faithful refined patches and RAN them through the official harness via swebench_unified.harness.run_resolve (`docker` run_evaluation), concurrently with a gold baseline:
- gold.diff -> resolved:true, completed:true (baseline sanity — harness works).
- patch_atk_5.diff (gold with has_add_permission using ['change','change'] only) -> resolved:true, completed:true, attempts=1.
- patch_atk_8.diff (gold verbatim; atk_8's target_decision==holds_any==any(...) refines exactly to the gold helper) -> resolved:true, completed:true, attempts=1.
Every verifying candidate's faithful patch RESOLVES => no verify-but-wrong impl exists => verify=>correct holds. NOT BROKEN.

refinement.md audit (A-legs / kind-3): axioms region is comment-only; grep confirms 0 `@ContractOnly` in model.py. There are genuinely NO A-legs (A-consumed / A-reference). Every leg is R or I; the sole deep-model leg A3 (holds_any / short-circuit loop <-> gold `any(has_perm(...) for perm in perms)`) is validated by axiom_check.py R1 (get_permission_codename distinctness => inspect_code!=modify_code) + R2 (any==existential==loop over all subsets |U|=8 + 50000 fuzz) — ran locally, exit 0. The `opts.fields` locating loop is excluded from the model because the patch moves it verbatim (unchanged pre/post-patch), so the changed operation (which required-code list each decision queries) is modeled deeply, not a disguised kind-3. Correspondence to real callees (mapping.md §3: has_perm, get_permission_codename, builtin any) holds. No kind-3 legs.

The prior BROKEN verdict is FIXED by the MustTerminate repair (atk_1 = the exact old break, now rejected; atk_7 independent non-term also rejected). >=5 distinct wrong impls encoded and fully run; both CANDIDATES materialized + resolve-run and BOTH RESOLVE. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11149.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administrative interface renders an editable sub-collection that belongs to
  an automatically generated link table standing between two principal records.
  Such a link table carries no permissions of its own, so the four authorisation
  decisions for it — may the actor create, modify, remove, or merely inspect an
  entry — are derived from the permissions the actor holds on the *target*
  record that the link points to.

  The actor's authorisation is a set of held permission codes for the target
  record.  Two of those codes are significant here: an INSPECT code and a MODIFY
  code (distinct codes). The decisions are:

    (1) inspect is permitted exactly when the actor holds EITHER the inspect code
        OR the modify code for the target (modify subsumes inspect);

    (2) create, modify, and remove are EACH permitted exactly when the actor
        holds the MODIFY code for the target — holding only the inspect code must
        NOT permit any of them.

  Equivalently, every decision asks whether the actor holds ANY of a small list
  of required codes for the target record: the inspect decision requires
  {inspect, modify}; each of create / modify / remove requires {modify} alone.
  An actor granted inspect-only therefore gets a read-only collection.

The actor's held codes are modelled as ``PSet[int]``; a required-code list is a
``PSeq[int]``; holding a code is set membership; "holds any required code" is the
existential over the required list.  Each decision is the corresponding
``bool``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: a decision is a membership/any query over the actor's
# held permission codes, modelled deeply over PSet[int] / PSeq[int]. The code
# construction and the per-code membership test are unchanged callees refined to
# integer codes / set membership, not axioms the proof consumes — see
# refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def holds_any(held: PSet[int], required: PSeq[int]) -> bool:
    """The actor holds AT LEAST ONE of the required codes for the target record.
    This is the existential over the required-code list of the per-code holding
    test (set membership)."""
    return Exists(int, lambda j: 0 <= j and j < len(required) and required[j] in held)
# pure-end


def target_decision(held: PSet[int], required: PSeq[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    # The decision must actually be delivered: this termination obligation
    # forbids implementations that would satisfy the value postcondition
    # only vacuously by never returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # The decision is TRUE iff the actor holds any of the required codes.
    Ensures(Result() == holds_any(held, required))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(required):
        # invariants-start
        Invariant(Acc(set_pred(held), 1 / 2))
        Invariant(0 <= i and i <= len(required))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(required) - i.
        Invariant(MustTerminate(len(required) - i))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i, not (required[k] in held))))
        # invariants-end
        if required[i] in held:
            return True
        i = i + 1
    return False
    # impl-end


def inline_inspect_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Inspect is permitted iff the actor holds the inspect OR the modify code.
    Ensures(Result() == ((inspect_code in held) or (modify_code in held)))
    # post-conditions-end
    # impl-start
    required = PSeq(inspect_code, modify_code)
    return target_decision(held, required)
    # impl-end


def inline_create_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Create is permitted iff the actor holds the MODIFY code; the inspect code
    # alone must NOT permit it.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end


def inline_modify_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Modify is permitted iff the actor holds the MODIFY code.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end


def inline_remove_decision(held: PSet[int], inspect_code: int, modify_code: int) -> bool:
    # pre-conditions-start
    Requires(Acc(set_pred(held), 1 / 2))
    Requires(inspect_code != modify_code)
    # Each decision must be delivered in finite time; the measure leaves
    # room to invoke the shared membership scan (which carries a smaller
    # one).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(held), 1 / 2))
    # Remove is permitted iff the actor holds the MODIFY code.
    Ensures(Result() == (modify_code in held))
    # post-conditions-end
    # impl-start
    required = PSeq(modify_code)
    return target_decision(held, required)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit of the REPAIRED frozen spec (model.py/refinement.md/mapping.md rev Aug 13 01:29-01:37). This cell was previously recorded G-EQ=fail (BROKEN) via prior atk_7 in run dsggkes3: a NON-TERMINATING recursion `return target_decision(held, required)` on the miss path verified under the OLD partial-correctness spec but hung the test suite (no-resolve). The repair adds `Requires(MustTerminate(...))` to every function's (frozen) pre-conditions region (wrappers measure 3, scan measure 2, loop measure len(required)-i) plus exact-equality postconditions. I re-audited whether the repaired spec still admits any verify-but-wrong impl.

 Positive control (model.py copy) VERIFIES (10.6s). Prepatch twin model_prepatch.py FAILS verification (postconditions of inline_modify/remove_decision don't hold) => prepatch_reproduced=true; spec senses the bug.

8 same-spec attacks (all `same-spec` exit 0; diffs confined to impl/invariant regions). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-11149 <path>`.
- atk_1 (control-flow-effect / re-encode OLD atk_7: recursion on miss path in target_decision): weakness exit=2 NOT-A-COUNTEREXAMPLE (does not verify — MustTerminate rejects it). REPAIR CONFIRMED.
- atk_2 (control-flow-effect / non-advancing loop, index never increments): exit=2 does not verify.
- atk_3 (prepatch bug / partial-domain: inline_create uses the VIEW rule PSeq(inspect_code,modify_code)): exit=2 does not verify (postcondition Result()==(modify_code in held) fails).
- atk_4 (boundary / off-by-one: scan `while i < len(required)-1` misses last element): exit=2 does not verify.
- atk_5 (ungrounded-oracle echo / CORRECT: inline_create uses PSeq(modify_code,modify_code), behaviourally identical): weakness exit=0 CANDIDATE (verifies 10.8s).
- atk_6 (partial-domain / wrong code: inline_create scans PSeq(inspect_code) only): exit=2 does not verify.
- atk_7 (control-flow-effect / wrapper self-recursion: inline_create returns inline_create_decision(...)): exit=2 does not verify (MustTerminate rejects — wrapper cannot delegate to an equal-measure callee).
- atk_8 (ungrounded-oracle echo / CORRECT: target_decision returns holds_any(held,required) directly = gold `any(...)`): weakness exit=0 CANDIDATE (verifies 10.8s).

BOTH candidates are behaviourally-correct echoes; materialized their faithful refined patches and RAN them through the official harness via swebench_unified.harness.run_resolve (`docker` run_evaluation), concurrently with a gold baseline:
- gold.diff -> resolved:true, completed:true (baseline sanity — harness works).
- patch_atk_5.diff (gold with has_add_permission using ['change','change'] only) -> resolved:true, completed:true, attempts=1.
- patch_atk_8.diff (gold verbatim; atk_8's target_decision==holds_any==any(...) refines exactly to the gold helper) -> resolved:true, completed:true, attempts=1.
Every verifying candidate's faithful patch RESOLVES => no verify-but-wrong impl exists => verify=>correct holds. NOT BROKEN.

refinement.md audit (A-legs / kind-3): axioms region is comment-only; grep confirms 0 `@ContractOnly` in model.py. There are genuinely NO A-legs (A-consumed / A-reference). Every leg is R or I; the sole deep-model leg A3 (holds_any / short-circuit loop <-> gold `any(has_perm(...) for perm in perms)`) is validated by axiom_check.py R1 (get_permission_codename distinctness => inspect_code!=modify_code) + R2 (any==existential==loop over all subsets |U|=8 + 50000 fuzz) — ran locally, exit 0. The `opts.fields` locating loop is excluded from the model because the patch moves it verbatim (unchanged pre/post-patch), so the changed operation (which required-code list each decision queries) is modeled deeply, not a disguised kind-3. Correspondence to real callees (mapping.md §3: has_perm, get_permission_codename, builtin any) holds. No kind-3 legs.

The prior BROKEN verdict is FIXED by the MustTerminate repair (atk_1 = the exact old break, now rejected; atk_7 independent non-term also rejected). >=5 distinct wrong impls encoded and fully run; both CANDIDATES materialized + resolve-run and BOTH RESOLVE. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec vs. real repo callee) holds; no diverging input exists within the modeled scope.

Evidence:
1. Model verifies under pinned Nagini (10.0s, 'Verification successful').
2. Spec markers present; postconditions exactly mirror the gold-patched real repo (django/contrib/admin/options.py @ base_commit e245046, patched worktree):
   - inline_create/modify/remove_decision: Result() == (modify_code in held)  <->  has_add/change/delete_permission -> _has_any_perms_for_target_model(request, ['change']).
   - inline_inspect_decision: Result() == ((inspect_code in held) or (modify_code in held))  <->  has_view_permission -> _has_any_perms_for_target_model(request, ['view','change']).
3. Differential conformance (bundle conformance_check.py) drives the REAL patched InlineModelAdmin methods as oracle (not a reimplementation), via stub meta/field/request objects and get_permission_codename for string construction. Ran: 'G-CONF OK: shadow impl == real patched decisions on 122288 checks (boundary + 22000 fuzz iterations, seed 11149)', 0 disagreements. Boundary is exhaustive over all held subsets of an 8-code universe x 4 code-pair placements x 8 required-list shapes (empty/singletons/two-code both orders/duplicate/unrelated).
4. Precondition inspect_code != modify_code is always faithful: get_permission_codename('view',opts) yields 'view_<model>' != 'change_<model>' (verified in axiom_check R1). The precondition is not too strong — it excludes only physically impossible states (view and change codenames can never collide).
5. Unmodeled elements (auto_created guard, field-locating loop, super() else branch) are genuinely unchanged by the patch (moved verbatim into the helper), so the modeling boundary introduces no drift for the F2P-exercised auto_created branch.

The spec is neither too strong nor drifted from real behavior on the modeled operation. No (held, required, inspect_code, modify_code) input makes the modeled function disagree with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py non-impl regions; refinement.md/mapping.md are auditor-facing, not solver-visible) was generated via markers.spec_view and audited line-by-line.

1. No gold-diff line or diff marker reproduced: the model uses invented abstract carriers (held: PSet[int], required: PSeq[int], holds_any, target_decision, inline_{inspect,create,modify,remove}_decision) with none of the gold's Python.
2. No patched file path: no 'options.py', no 'django/contrib/admin'.
3. No patched repo symbol echoed: none of _has_any_perms_for_target_model, has_add/change/delete/view_permission, get_permission_codename, has_perm, auto_created, or the perms literals ['change']/['view','change'] appear. Identifiers are fully abstract (inspect_code, modify_code).
4. No bug/fix narration: zero hits on the narration wordlist; the docstring explicitly frames the content 'as desired behaviour, not as an edit'.

Beyond problem_statement check: the public problem_statement already states the intended-correct behaviour (view-only users must NOT be able to add/remove auto-created M2M inline items — flagged as a bug). The spec view encodes exactly that intended behaviour abstractly (create/modify/remove require the MODIFY code; inspect-only -> read-only; inspect requires {inspect,modify}). Encoding the intended correct behaviour that the problem statement itself describes is the legitimate function of a spec and does not reveal the gold EDIT (helper refactor, which methods, which file, the perms-list change) beyond the public statement.

Mechanical corroboration: leakage.screen() returns passed=True with no hard_failures/warnings; bundle is not relaxed (no RELAXED_LEAKAGE.md / relaxed_leakage flag).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
