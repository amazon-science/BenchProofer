# P2 adversarial audit — django__django-15368

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
         (Implies(0 <= i and i < len(in_family),
                  Implies(in_family[i], resolvable[i])),
          [[in_family[i]], [resolvable[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(in_family), 1 / 2))
@@ -107,12 +105,11 @@
              [[in_family[k]], [resolvable[k]]])))
         Invariant(0 <= i and i <= len(resolvable))
         Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        attr_resolvable = resolvable[i - 1]
-        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
+        attr_in_family = in_family[i - 1]
+        Assert(ToSeq(resolvable).drop(i - 1)[0] == resolvable[i - 1])
         Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
-        if not attr_resolvable:
+        if not attr_in_family:
             result = [True] + result
         else:
             result = [False] + result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
         (Implies(0 <= i and i < len(in_family),
                  Implies(in_family[i], resolvable[i])),
          [[in_family[i]], [resolvable[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(in_family), 1 / 2))
@@ -96,26 +94,12 @@
     result = []  # type: List[bool]
     i = len(resolvable)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(in_family), 1 / 2))
         Invariant(Acc(list_pred(resolvable), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(in_family) == len(resolvable))
-        Invariant(Forall(int, lambda k:
-            (Implies(0 <= k and k < len(in_family),
-                     Implies(in_family[k], resolvable[k])),
-             [[in_family[k]], [resolvable[k]]])))
         Invariant(0 <= i and i <= len(resolvable))
-        Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        attr_resolvable = resolvable[i - 1]
-        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
-        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
-        if not attr_resolvable:
-            result = [True] + result
-        else:
-            result = [False] + result
+        result = [True] + result
         i = i - 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
         (Implies(0 <= i and i < len(in_family),
                  Implies(in_family[i], resolvable[i])),
          [[in_family[i]], [resolvable[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(in_family), 1 / 2))
@@ -96,26 +94,12 @@
     result = []  # type: List[bool]
     i = len(resolvable)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(in_family), 1 / 2))
         Invariant(Acc(list_pred(resolvable), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(in_family) == len(resolvable))
-        Invariant(Forall(int, lambda k:
-            (Implies(0 <= k and k < len(in_family),
-                     Implies(in_family[k], resolvable[k])),
-             [[in_family[k]], [resolvable[k]]])))
         Invariant(0 <= i and i <= len(resolvable))
-        Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        attr_resolvable = resolvable[i - 1]
-        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
-        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
-        if not attr_resolvable:
-            result = [True] + result
-        else:
-            result = [False] + result
+        result = [False] + result
         i = i - 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
         (Implies(0 <= i and i < len(in_family),
                  Implies(in_family[i], resolvable[i])),
          [[in_family[i]], [resolvable[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(in_family), 1 / 2))
@@ -96,26 +94,19 @@
     result = []  # type: List[bool]
     i = len(resolvable)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(in_family), 1 / 2))
         Invariant(Acc(list_pred(resolvable), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(in_family) == len(resolvable))
-        Invariant(Forall(int, lambda k:
-            (Implies(0 <= k and k < len(in_family),
-                     Implies(in_family[k], resolvable[k])),
-             [[in_family[k]], [resolvable[k]]])))
         Invariant(0 <= i and i <= len(resolvable))
         Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         attr_resolvable = resolvable[i - 1]
         Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
         Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
         if not attr_resolvable:
+            result = [False] + result
+        else:
             result = [True] + result
-        else:
-            result = [False] + result
         i = i - 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
         (Implies(0 <= i and i < len(in_family),
                  Implies(in_family[i], resolvable[i])),
          [[in_family[i]], [resolvable[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(in_family), 1 / 2))
@@ -94,28 +92,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[bool]
-    i = len(resolvable)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(in_family), 1 / 2))
-        Invariant(Acc(list_pred(resolvable), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(len(in_family) == len(resolvable))
-        Invariant(Forall(int, lambda k:
-            (Implies(0 <= k and k < len(in_family),
-                     Implies(in_family[k], resolvable[k])),
-             [[in_family[k]], [resolvable[k]]])))
-        Invariant(0 <= i and i <= len(resolvable))
-        Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        attr_resolvable = resolvable[i - 1]
-        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
-        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
-        if not attr_resolvable:
-            result = [True] + result
-        else:
-            result = [False] + result
-        i = i - 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
         (Implies(0 <= i and i < len(in_family),
                  Implies(in_family[i], resolvable[i])),
          [[in_family[i]], [resolvable[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(in_family), 1 / 2))
@@ -95,20 +93,13 @@
     # impl-start
     result = []  # type: List[bool]
     i = len(resolvable)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(in_family), 1 / 2))
         Invariant(Acc(list_pred(resolvable), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(in_family) == len(resolvable))
-        Invariant(Forall(int, lambda k:
-            (Implies(0 <= k and k < len(in_family),
-                     Implies(in_family[k], resolvable[k])),
-             [[in_family[k]], [resolvable[k]]])))
-        Invariant(0 <= i and i <= len(resolvable))
+        Invariant(1 <= i and i <= len(resolvable))
         Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         attr_resolvable = resolvable[i - 1]
         Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
         Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -82,7 +81,6 @@
         (Implies(0 <= i and i < len(in_family),
                  Implies(in_family[i], resolvable[i])),
          [[in_family[i]], [resolvable[i]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(in_family), 1 / 2))
@@ -96,26 +94,17 @@
     result = []  # type: List[bool]
     i = len(resolvable)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(in_family), 1 / 2))
         Invariant(Acc(list_pred(resolvable), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(in_family) == len(resolvable))
-        Invariant(Forall(int, lambda k:
-            (Implies(0 <= k and k < len(in_family),
-                     Implies(in_family[k], resolvable[k])),
-             [[in_family[k]], [resolvable[k]]])))
         Invariant(0 <= i and i <= len(resolvable))
         Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        attr_resolvable = resolvable[i - 1]
-        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
-        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
-        if not attr_resolvable:
+        attr_in_family = in_family[i - 1]
+        if attr_in_family:
+            result = [False] + result
+        else:
             result = [True] + result
-        else:
-            result = [False] + result
         i = i - 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15368.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batch update assembles, for one column, an ordered list of per-object
  assignments. For each object an attribute value is taken; the value must then
  be classified into one of two assignment forms:

    * a value that is *resolvable* — it knows how to turn itself into a column
      reference / sub-expression — must be carried into the assignment AS IT IS,
      so the database resolves it (e.g. to another column);

    * a value that is NOT resolvable — a plain Python datum — must instead be
      wrapped as a literal bound parameter before it is carried in.

  The classification must be by the *capability* of carrying a value into a
  resolvable form, NOT by membership in any one concrete family of resolvable
  values. In particular a resolvable value that does not belong to that one
  concrete family (it merely has the resolving capability) must still be carried
  through unwrapped, exactly like a member of the family — never silently turned
  into a literal, which would store the value's text instead of resolving it.

  The observable result is, in object order, one boolean per assignment:
  True iff that value was wrapped as a literal. A value must be wrapped iff it
  is NOT resolvable; every resolvable value, whether or not it is in the
  concrete family, must be left unwrapped (False).

Each candidate value is described by two booleans: `in_family` (it is a member
of the one concrete resolvable family) and `resolvable` (it carries the
resolving capability). Family membership entails the capability — every member
of the family is resolvable — but NOT conversely: a value can be resolvable
without being in that family. That entailment is the type-hierarchy fact stated
as a precondition (`in_family[i] ==> resolvable[i]`); the converse failure is
the discriminating case. The per-assignment result is a `List[bool]`, with the
specification carried over `PSeq[bool]`.

No callee is axiomatized: the classification is pure, local logic modelled
deeply by the front-recursive fold `wrap_flags` and the verified loop below.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The behaviour under specification — a value is wrapped as
# a literal iff it is NOT resolvable, regardless of concrete family — is modelled
# DEEPLY by the pure `wrap_flags` fold below and the verified loop, not behind a
# @ContractOnly. The type-hierarchy fact "family membership entails the resolving
# capability" is stated as an input precondition and audited against the real
# class hierarchy by axiom_check.py / G-AX, NOT consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def empty_flags() -> PSeq[bool]:
    return PSeq(True).take(0)


@Pure
def wrap_flags(resolvable: PSeq[bool]) -> PSeq[bool]:
    """Per-assignment wrap flags for a sequence of resolvable-capability bits,
    in order. A value is wrapped as a literal (True) iff it is NOT resolvable;
    every resolvable value is left unwrapped (False). Front-recursive so a single
    unfold is available to the loop per step."""
    if len(resolvable) == 0:
        return empty_flags()
    return PSeq(not resolvable[0]) + wrap_flags(resolvable.drop(1))
# pure-end


def build_wrap_flags(in_family: List[bool], resolvable: List[bool]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(in_family), 1 / 2))
    Requires(Acc(list_pred(resolvable), 1 / 2))
    # the two descriptions are aligned, one entry per object
    Requires(len(in_family) == len(resolvable))
    # type-hierarchy fact: family membership entails the resolving capability
    Requires(Forall(int, lambda i:
        (Implies(0 <= i and i < len(in_family),
                 Implies(in_family[i], resolvable[i])),
         [[in_family[i]], [resolvable[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(in_family), 1 / 2))
    Ensures(Acc(list_pred(resolvable), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Each value is wrapped as a literal iff it is NOT resolvable — the
    # capability decides, never the concrete family.
    Ensures(ToSeq(Result()) == wrap_flags(ToSeq(resolvable)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = len(resolvable)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(in_family), 1 / 2))
        Invariant(Acc(list_pred(resolvable), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(in_family) == len(resolvable))
        Invariant(Forall(int, lambda k:
            (Implies(0 <= k and k < len(in_family),
                     Implies(in_family[k], resolvable[k])),
             [[in_family[k]], [resolvable[k]]])))
        Invariant(0 <= i and i <= len(resolvable))
        Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
        # invariants-end
        attr_resolvable = resolvable[i - 1]
        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
        if not attr_resolvable:
            result = [True] + result
        else:
            result = [False] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 same-spec wrong-impl attacks (all impl-region-only edits; spec+axioms byte-identical to model.py, confirmed by same-spec exit0 for all 8 files and by textual strip-impl comparison). Positive control = byte-identical model.py, VERIFIED in 17.1s. NO attack came back CANDIDATE, so no faithful refined patch needed materialization/resolve.

Why the spec cannot be broken: the postcondition ToSeq(Result())==wrap_flags(ToSeq(resolvable)) is a TOTAL, DETERMINISTIC functional spec pinning output[j] = (not resolvable[j]) for the entire domain; in_family appears ONLY in the precondition/invariant (A-reference B1), never in the postcondition, so it cannot admit any deviating output. Any impl whose output differs from wrap-iff-not-resolvable fails the postcondition. Domain is non-vacuous (positive control verifies; G-CONF exercised >=1e5 real inputs).

Attacks + observed weakness results (adversary weakness nagini django__django-15368 <path>; PY=python):
- atk_1.py (prepatch bug: keys off in_family instead of resolvable) -> NOT-A-COUNTEREXAMPLE, verification failed, exit 2. Prepatch reproduced.
- atk_2.py (control-flow-effect: always wrap True) -> NOT-A-COUNTEREXAMPLE, exit 2. Direct verify: FAILED 15.8s, 'Postcondition ... (ToSeq(Result()) == wrap_flags(ToSeq(resolvable))) might not hold' at line 91.
- atk_3.py (control-flow-effect: never wrap False) -> NOT-A-COUNTEREXAMPLE, exit 2.
- atk_4.py (inverted branch: wrap iff resolvable) -> NOT-A-COUNTEREXAMPLE, exit 2.
- atk_5.py (partial-domain/ungrounded: return [] always) -> NOT-A-COUNTEREXAMPLE, exit 2. Direct verify: FAILED 15.6s, same postcondition at line 91.
- atk_6.py (boundary off-by-one: while i>1, drops first object's flag) -> NOT-A-COUNTEREXAMPLE, exit 2.
- atk_7.py (ungrounded-oracle echo: emits in_family-based flag directly) -> NOT-A-COUNTEREXAMPLE, exit 2.
All 7 are GENUINE verification failures (~15-17s JVM+Z3 runs, not timeouts; adversary reports 'timed out (inconclusive)' on infra failure and did not here). Two spot-checked with direct `verify` both fail exactly on the discriminating postcondition at line 91.

Refinement.md audit: every leg is R (A1,A2,A4), I-under-R (A3), A-reference (B1), or I (C import hunk). NO kind-3 (unexpressible-changed-op) legs. The single A-reference B1 (precondition in_family[i]==>resolvable[i] <-> unchanged Django class hierarchy isinstance(Expression)==>hasattr(resolve_expression)) is validated by axiom_check.py/G-AX and is NOT consumed: the postcondition depends only on resolvable, so B1 only shapes the (non-vacuous) input domain and cannot admit a wrong impl. The deliberately-absent converse is exactly why in_family-based impls (atk_1, atk_7) fail on the (F,T)/F('note') discriminating cell. Correspondence to real callees holds (mapping.md: resolvable<->hasattr(resolve_expression) post-patch predicate query.py:673; result True<->Value(...) wrap, False<->carry-through When(then=attr)).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15368.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batch update assembles, for one column, an ordered list of per-object
  assignments. For each object an attribute value is taken; the value must then
  be classified into one of two assignment forms:

    * a value that is *resolvable* — it knows how to turn itself into a column
      reference / sub-expression — must be carried into the assignment AS IT IS,
      so the database resolves it (e.g. to another column);

    * a value that is NOT resolvable — a plain Python datum — must instead be
      wrapped as a literal bound parameter before it is carried in.

  The classification must be by the *capability* of carrying a value into a
  resolvable form, NOT by membership in any one concrete family of resolvable
  values. In particular a resolvable value that does not belong to that one
  concrete family (it merely has the resolving capability) must still be carried
  through unwrapped, exactly like a member of the family — never silently turned
  into a literal, which would store the value's text instead of resolving it.

  The observable result is, in object order, one boolean per assignment:
  True iff that value was wrapped as a literal. A value must be wrapped iff it
  is NOT resolvable; every resolvable value, whether or not it is in the
  concrete family, must be left unwrapped (False).

Each candidate value is described by two booleans: `in_family` (it is a member
of the one concrete resolvable family) and `resolvable` (it carries the
resolving capability). Family membership entails the capability — every member
of the family is resolvable — but NOT conversely: a value can be resolvable
without being in that family. That entailment is the type-hierarchy fact stated
as a precondition (`in_family[i] ==> resolvable[i]`); the converse failure is
the discriminating case. The per-assignment result is a `List[bool]`, with the
specification carried over `PSeq[bool]`.

No callee is axiomatized: the classification is pure, local logic modelled
deeply by the front-recursive fold `wrap_flags` and the verified loop below.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The behaviour under specification — a value is wrapped as
# a literal iff it is NOT resolvable, regardless of concrete family — is modelled
# DEEPLY by the pure `wrap_flags` fold below and the verified loop, not behind a
# @ContractOnly. The type-hierarchy fact "family membership entails the resolving
# capability" is stated as an input precondition and audited against the real
# class hierarchy by axiom_check.py / G-AX, NOT consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def empty_flags() -> PSeq[bool]:
    return PSeq(True).take(0)


@Pure
def wrap_flags(resolvable: PSeq[bool]) -> PSeq[bool]:
    """Per-assignment wrap flags for a sequence of resolvable-capability bits,
    in order. A value is wrapped as a literal (True) iff it is NOT resolvable;
    every resolvable value is left unwrapped (False). Front-recursive so a single
    unfold is available to the loop per step."""
    if len(resolvable) == 0:
        return empty_flags()
    return PSeq(not resolvable[0]) + wrap_flags(resolvable.drop(1))
# pure-end


def build_wrap_flags(in_family: List[bool], resolvable: List[bool]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(in_family), 1 / 2))
    Requires(Acc(list_pred(resolvable), 1 / 2))
    # the two descriptions are aligned, one entry per object
    Requires(len(in_family) == len(resolvable))
    # type-hierarchy fact: family membership entails the resolving capability
    Requires(Forall(int, lambda i:
        (Implies(0 <= i and i < len(in_family),
                 Implies(in_family[i], resolvable[i])),
         [[in_family[i]], [resolvable[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(in_family), 1 / 2))
    Ensures(Acc(list_pred(resolvable), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Each value is wrapped as a literal iff it is NOT resolvable — the
    # capability decides, never the concrete family.
    Ensures(ToSeq(Result()) == wrap_flags(ToSeq(resolvable)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = len(resolvable)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(in_family), 1 / 2))
        Invariant(Acc(list_pred(resolvable), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(in_family) == len(resolvable))
        Invariant(Forall(int, lambda k:
            (Implies(0 <= k and k < len(in_family),
                     Implies(in_family[k], resolvable[k])),
             [[in_family[k]], [resolvable[k]]])))
        Invariant(0 <= i and i <= len(resolvable))
        Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
        # invariants-end
        attr_resolvable = resolvable[i - 1]
        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
        if not attr_resolvable:
            result = [True] + result
        else:
            result = [False] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 same-spec wrong-impl attacks (all impl-region-only edits; spec+axioms byte-identical to model.py, confirmed by same-spec exit0 for all 8 files and by textual strip-impl comparison). Positive control = byte-identical model.py, VERIFIED in 17.1s. NO attack came back CANDIDATE, so no faithful refined patch needed materialization/resolve.

Why the spec cannot be broken: the postcondition ToSeq(Result())==wrap_flags(ToSeq(resolvable)) is a TOTAL, DETERMINISTIC functional spec pinning output[j] = (not resolvable[j]) for the entire domain; in_family appears ONLY in the precondition/invariant (A-reference B1), never in the postcondition, so it cannot admit any deviating output. Any impl whose output differs from wrap-iff-not-resolvable fails the postcondition. Domain is non-vacuous (positive control verifies; G-CONF exercised >=1e5 real inputs).

Attacks + observed weakness results (adversary weakness nagini django__django-15368 <path>; PY=python):
- atk_1.py (prepatch bug: keys off in_family instead of resolvable) -> NOT-A-COUNTEREXAMPLE, verification failed, exit 2. Prepatch reproduced.
- atk_2.py (control-flow-effect: always wrap True) -> NOT-A-COUNTEREXAMPLE, exit 2. Direct verify: FAILED 15.8s, 'Postcondition ... (ToSeq(Result()) == wrap_flags(ToSeq(resolvable))) might not hold' at line 91.
- atk_3.py (control-flow-effect: never wrap False) -> NOT-A-COUNTEREXAMPLE, exit 2.
- atk_4.py (inverted branch: wrap iff resolvable) -> NOT-A-COUNTEREXAMPLE, exit 2.
- atk_5.py (partial-domain/ungrounded: return [] always) -> NOT-A-COUNTEREXAMPLE, exit 2. Direct verify: FAILED 15.6s, same postcondition at line 91.
- atk_6.py (boundary off-by-one: while i>1, drops first object's flag) -> NOT-A-COUNTEREXAMPLE, exit 2.
- atk_7.py (ungrounded-oracle echo: emits in_family-based flag directly) -> NOT-A-COUNTEREXAMPLE, exit 2.
All 7 are GENUINE verification failures (~15-17s JVM+Z3 runs, not timeouts; adversary reports 'timed out (inconclusive)' on infra failure and did not here). Two spot-checked with direct `verify` both fail exactly on the discriminating postcondition at line 91.

Refinement.md audit: every leg is R (A1,A2,A4), I-under-R (A3), A-reference (B1), or I (C import hunk). NO kind-3 (unexpressible-changed-op) legs. The single A-reference B1 (precondition in_family[i]==>resolvable[i] <-> unchanged Django class hierarchy isinstance(Expression)==>hasattr(resolve_expression)) is validated by axiom_check.py/G-AX and is NOT consumed: the postcondition depends only on resolvable, so B1 only shapes the (non-vacuous) input domain and cannot admit a wrong impl. The deliberately-absent converse is exactly why in_family-based impls (atk_1, atk_7) fail on the (F,T)/F('note') discriminating cell. Correspondence to real callees holds (mapping.md: resolvable<->hasattr(resolve_expression) post-patch predicate query.py:673; result True<->Value(...) wrap, False<->carry-through When(then=attr)).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real callee. Evidence: (1) model.py verifies under the pinned Nagini verifier (14.15s, exit 0); spec region markers intact. (2) Independent conformance run against the REAL repo at base_commit e972620a with the post-patch predicate applied (django/db/models/query.py:673 `not hasattr(attr,'resolve_expression')`) — the model's contract-stripped build_wrap_flags vs the real QuerySet.bulk_update per-object wrap decision (read via captured Case.cases When.result identity) — 25045 batches / 151018 objects, 0 disagreements, seed 15368. (3) Adversarial probe with exotic real values (non-callable `resolve_expression=42` attribute, Func(UPPER), nested Value(Value(1)), bytes, bool, plain str, F) — all agree: wrap iff not hasattr(resolve_expression). (4) The precondition in_family[i]==>resolvable[i] is a TRUE fact about the unchanged Django hierarchy (Expression subclasses BaseExpression which defines resolve_expression; F is resolvable but not an Expression — converse fails). No real attribute value witnesses the excluded (in_family=True, resolvable=False) cell, so the precondition excludes no real input; the spec is not too strong by domain-narrowing. axiom_check.py (G-AX) audits this against live classes. (5) Downstream Case/When/Cast machinery abstracted to identity is faithful — only the then= wrap decision changed, captured exactly by the per-object boolean. The spec (wrap-as-literal iff NOT resolvable, over the full aligned batch) is a faithful over-approximation-free model of the real classification callee; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (0 hard failures): no diff markers, no gold-patch line reproduced, no patched file path, no narration words, and the only patched symbol (bulk_update) is public in the problem_statement. Semantically the spec view does not exceed the public problem_statement: the gold edit is isinstance(attr, Expression) -> hasattr(attr, 'resolve_expression'), and the PUBLIC problem_statement literally states the fix ('It works, if the type check gets replaced by ... if not hasattr(attr, \'resolve_expression\'): ... or if not isinstance(attr, (Expression, F)):'), plus the F('...') failing case and the query.py:673 location. The spec view uses only abstract carriers (in_family, resolvable, wrap_flags, build_wrap_flags) — it never names the repo symbols Expression/resolve_expression/isinstance/hasattr verbatim — and frames the discriminator abstractly ('classify by capability, not membership in one concrete family'), which is strictly less specific than the already-public duck-typing guidance. No spec-view line reveals the gold edit beyond what the problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
