# P2 adversarial audit — django__django-12858

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -76,7 +75,6 @@
     Requires(Acc(list_pred(is_compare_op), 1 / 2))
     Requires(len(reached_field) == len(is_value_op))
     Requires(len(reached_field) == len(is_compare_op))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(reached_field), 1 / 2))
@@ -115,14 +113,11 @@
                 0 <= k and k < i,
                 errors[k] == flag_path(reached_field[k], is_value_op[k],
                                        is_compare_op[k])))))
-        Invariant(MustTerminate(len(reached_field) - i + 1))
         # invariants-end
-        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
+        if reached_field[i] == 0 or is_value_op[i] == 0:
             errors.append(1)
         else:
             errors.append(0)
-        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
-                                      is_compare_op[i]))
         i = i + 1
     return errors
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -76,7 +75,6 @@
     Requires(Acc(list_pred(is_compare_op), 1 / 2))
     Requires(len(reached_field) == len(is_value_op))
     Requires(len(reached_field) == len(is_compare_op))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(reached_field), 1 / 2))
@@ -115,14 +113,14 @@
                 0 <= k and k < i,
                 errors[k] == flag_path(reached_field[k], is_value_op[k],
                                        is_compare_op[k])))))
-        Invariant(MustTerminate(len(reached_field) - i + 1))
         # invariants-end
-        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
-            errors.append(1)
+        if i % 2 == 0:
+            if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
+                errors.append(1)
+            else:
+                errors.append(0)
         else:
             errors.append(0)
-        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
-                                      is_compare_op[i]))
         i = i + 1
     return errors
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -76,7 +75,6 @@
     Requires(Acc(list_pred(is_compare_op), 1 / 2))
     Requires(len(reached_field) == len(is_value_op))
     Requires(len(reached_field) == len(is_compare_op))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(reached_field), 1 / 2))
@@ -101,7 +99,7 @@
     # impl-start
     errors = []  # type: List[int]
     i = 0
-    while i < len(reached_field):
+    while i < len(reached_field) - 1:
         # invariants-start
         Invariant(Acc(list_pred(reached_field), 1 / 2))
         Invariant(Acc(list_pred(is_value_op), 1 / 2))
@@ -115,14 +113,11 @@
                 0 <= k and k < i,
                 errors[k] == flag_path(reached_field[k], is_value_op[k],
                                        is_compare_op[k])))))
-        Invariant(MustTerminate(len(reached_field) - i + 1))
         # invariants-end
         if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
             errors.append(1)
         else:
             errors.append(0)
-        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
-                                      is_compare_op[i]))
         i = i + 1
     return errors
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -76,7 +75,6 @@
     Requires(Acc(list_pred(is_compare_op), 1 / 2))
     Requires(len(reached_field) == len(is_value_op))
     Requires(len(reached_field) == len(is_compare_op))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(reached_field), 1 / 2))
@@ -115,14 +113,12 @@
                 0 <= k and k < i,
                 errors[k] == flag_path(reached_field[k], is_value_op[k],
                                        is_compare_op[k])))))
-        Invariant(MustTerminate(len(reached_field) - i + 1))
         # invariants-end
         if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
             errors.append(1)
         else:
             errors.append(0)
-        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
-                                      is_compare_op[i]))
+        return errors
         i = i + 1
     return errors
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -76,7 +75,6 @@
     Requires(Acc(list_pred(is_compare_op), 1 / 2))
     Requires(len(reached_field) == len(is_value_op))
     Requires(len(reached_field) == len(is_compare_op))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(reached_field), 1 / 2))
@@ -115,14 +113,8 @@
                 0 <= k and k < i,
                 errors[k] == flag_path(reached_field[k], is_value_op[k],
                                        is_compare_op[k])))))
-        Invariant(MustTerminate(len(reached_field) - i + 1))
         # invariants-end
-        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
-            errors.append(1)
-        else:
-            errors.append(0)
-        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
-                                      is_compare_op[i]))
+        errors.append(1)
         i = i + 1
     return errors
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -76,7 +75,6 @@
     Requires(Acc(list_pred(is_compare_op), 1 / 2))
     Requires(len(reached_field) == len(is_value_op))
     Requires(len(reached_field) == len(is_compare_op))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(reached_field), 1 / 2))
@@ -115,14 +113,11 @@
                 0 <= k and k < i,
                 errors[k] == flag_path(reached_field[k], is_value_op[k],
                                        is_compare_op[k])))))
-        Invariant(MustTerminate(len(reached_field) - i + 1))
         # invariants-end
-        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
+        if reached_field[i] == 0 or (is_value_op[i] == 0 or is_compare_op[i] == 0):
             errors.append(1)
         else:
             errors.append(0)
-        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
-                                      is_compare_op[i]))
         i = i + 1
     return errors
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -76,7 +75,6 @@
     Requires(Acc(list_pred(is_compare_op), 1 / 2))
     Requires(len(reached_field) == len(is_value_op))
     Requires(len(reached_field) == len(is_compare_op))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(reached_field), 1 / 2))
@@ -115,14 +113,11 @@
                 0 <= k and k < i,
                 errors[k] == flag_path(reached_field[k], is_value_op[k],
                                        is_compare_op[k])))))
-        Invariant(MustTerminate(len(reached_field) - i + 1))
         # invariants-end
         if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
+            errors.append(0)
+        else:
             errors.append(1)
-        else:
-            errors.append(0)
-        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
-                                      is_compare_op[i]))
         i = i + 1
     return errors
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12858.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When validating the ordering specification of a model, each multi-part path
  whose trailing segment cannot be resolved as a concrete model field is
  examined to decide whether it should be reported as an invalid ordering
  reference. A path is accepted (NOT reported) exactly when a field was reached
  just before the unresolved trailing segment AND that segment denotes at least
  one of the two recognised kinds of registered query operator: a value-
  producing operator (one that yields a new value to continue resolving) OR a
  comparison operator (one usable as a terminal predicate). A trailing segment
  that IS a recognised comparison operator is therefore a legitimate ordering
  target and must NOT be reported, exactly as a value-producing operator already
  is not. Otherwise — no field was reached, or the segment is neither operator
  kind — the path is reported as an invalid ordering reference.

  Concretely, for each path the decision is a function of three observations
  about its trailing segment: whether a field was reached before it
  (`reached_field`), whether the segment is a registered value-producing
  operator (`is_value_op`), and whether it is a registered comparison operator
  (`is_compare_op`). The path is flagged invalid iff no field was reached OR the
  segment is neither operator kind. The result lists, in input order, the
  flag (1 = reported invalid, 0 = accepted) of every examined path.

The three per-path observations are carried as parallel `List[int]` of 0/1
booleans (Nagini bans richer object graphs cheaply here; the tested behaviour
observes only these three predicates per path). The two operator-recognition
predicates correspond to two unchanged lookup-registry queries that the
validator calls but does not change; they are modelled as the boolean inputs
and their real semantics are recorded in mapping.md / checked by axiom_check.py
(A-reference) rather than consumed as axioms — the decision itself is modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The two registry queries that classify a path segment
# (value-producing vs. comparison operator) are unchanged callees; here their
# results enter the decision as the boolean inputs is_value_op / is_compare_op.
# Their real semantics (each returns a non-None object iff the named operator of
# that kind is registered) are validated out-of-band by axiom_check.py (G-AX)
# as A-references, not consumed as @ContractOnly Ensures. The reporting decision
# itself is modelled deeply below.
# axioms-end


# pure-start
@Pure
def flag_path(reached_field: int, is_value_op: int, is_compare_op: int) -> int:
    """The per-path decision: report the path as an invalid ordering reference
    iff EITHER no field was reached before its unresolved trailing segment, OR
    that segment is neither a value-producing operator nor a comparison
    operator. A path is accepted only when a field was reached AND the trailing
    segment is at least one of the two recognised operator kinds. Returns 1
    (report invalid) or 0 (accept)."""
    if reached_field == 0 or (is_value_op == 0 and is_compare_op == 0):
        return 1
    return 0
# pure-end


def select_reported_paths(reached_field: List[int],
                          is_value_op: List[int],
                          is_compare_op: List[int]) -> List[int]:
    # pre-conditions-start
    # The three per-path observation lists are read-only (fractional permission,
    # Required and Ensured) and index-aligned.
    Requires(Acc(list_pred(reached_field), 1 / 2))
    Requires(Acc(list_pred(is_value_op), 1 / 2))
    Requires(Acc(list_pred(is_compare_op), 1 / 2))
    Requires(len(reached_field) == len(is_value_op))
    Requires(len(reached_field) == len(is_compare_op))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(reached_field), 1 / 2))
    Ensures(Acc(list_pred(is_value_op), 1 / 2))
    Ensures(Acc(list_pred(is_compare_op), 1 / 2))
    # The three observation lists remain index-aligned (read-only).
    Ensures(len(reached_field) == len(is_value_op))
    Ensures(len(reached_field) == len(is_compare_op))
    # The result is a fresh, fully-owned list with one flag per examined path.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(reached_field))
    # Each flag is exactly the per-path decision: a path is reported invalid iff
    # no field was reached OR the trailing segment is neither operator kind. In
    # particular a path whose segment IS a comparison operator (is_compare_op),
    # with a field reached, is accepted (flag 0) — exactly as a value-producing
    # operator already is.
    Ensures(Forall(int, lambda k: (Implies(
            0 <= k and k < len(reached_field),
            Result()[k] == flag_path(reached_field[k], is_value_op[k],
                                     is_compare_op[k])))))
    # post-conditions-end
    # impl-start
    errors = []  # type: List[int]
    i = 0
    while i < len(reached_field):
        # invariants-start
        Invariant(Acc(list_pred(reached_field), 1 / 2))
        Invariant(Acc(list_pred(is_value_op), 1 / 2))
        Invariant(Acc(list_pred(is_compare_op), 1 / 2))
        Invariant(len(reached_field) == len(is_value_op))
        Invariant(len(reached_field) == len(is_compare_op))
        Invariant(Acc(list_pred(errors)))
        Invariant(0 <= i and i <= len(reached_field))
        Invariant(len(errors) == i)
        Invariant(Forall(int, lambda k: (Implies(
                0 <= k and k < i,
                errors[k] == flag_path(reached_field[k], is_value_op[k],
                                       is_compare_op[k])))))
        # invariants-end
        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
            errors.append(1)
        else:
            errors.append(0)
        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
                                      is_compare_op[i]))
        i = i + 1
    return errors
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### AUDIT SUMMARY (adversarial G-EQ, refinement fidelity, A-legs + model<->patch correspondence).

SPEC SHAPE: model.py's select_reported_paths carries a TIGHT functional postcondition: Ensures(len(Result())==len(reached_field)) AND Ensures(Forall k: 0<=k<len -> Result()[k]==flag_path(reached_field[k],is_value_op[k],is_compare_op[k])). flag_path lives in the FROZEN @Pure region (uneditable; only the impl region lines 100-124 were edited per protocol). Thus any verifying impl must reproduce flag_path bit-for-bit on every index and match length exactly. This leaves essentially no room for a same-spec verifying WRONG impl -> strong prior toward SOUND, confirmed by falsification below.

ATTACKS (all copied model.py, edited ONLY impl region; all confirmed same-spec exit 0 via `adversary same-spec`; then `adversary weakness nagini django__django-12858 <atk>`):
- atk_1.py PREPATCH BUG (ignores is_compare_op: reports iff reached==0 or is_value_op==0). weakness exit=2 NOT-A-COUNTEREXAMPLE (verification failed). => prepatch bug reproduced/rejected by spec.
- atk_2.py PARTIAL-DOMAIN (correct on even i, always-accept on odd i). weakness exit=2 (does not verify).
- atk_3.py BOUNDARY/off-by-one (loop to len-1, drops last element -> length mismatch). weakness exit=2.
- atk_4.py CONTROL-FLOW-EFFECT (early `return errors` inside first iteration). weakness exit=2.
- atk_5.py UNGROUNDED-ORACLE ECHO (always append 1). weakness exit=2.
- atk_6.py OR-vs-AND fault (report iff reached==0 or is_value_op==0 or is_compare_op==0 -> mis-reports the isnull F2P case). weakness exit=2.
- atk_7.py NEGATED FLAG (swap 1/0). weakness exit=2.
All 7 same-spec wrong impls FAILED to verify => spec rejected each (good). No CANDIDATE (same-spec AND verifies) emerged, so NO faithful-patch resolve run was triggered (none required). Ran concurrently in batches of 3 (each Nagini check = JVM+Z3).

POSITIVE CONTROL: pos_control.py is byte-identical to bundle model.py (diff -q IDENTICAL). `bash scripts/nagini_verify.sh pos_control.py` => `Verification successful` exit=0 (13.6s). The frozen correct impl verifies.

A-REFERENCE / AXIOM AUDIT: no consumed @ContractOnly axioms (axioms region empty by design). axiom_check.py exit=0: pure truth-table A-reference confirmed (flag_path == real post-patch predicate `fld is None or (get_transform is None and get_lookup is None)` over full (reached,value,compare) truth table). Django-callee A-reference (Field.get_transform/get_lookup non-None classification, incl. isnull=lookup-not-transform F2P case) is correctly DEFERRED to the in-container G-AX run (Django not importable in ambient env) — scoping is correct, not a gap.

REFINEMENT.MD LEG AUDIT: A1=R (path collection <-> aligned List[int] indices), A2=I+A-reference (boolean algebra IDENTICAL to gold guard; the two registry queries are A-reference validated == real callees, NOT consumed axioms), A3=R (models.E015 presence/absence <-> 0/1 flag in order). Sections B/C confirm: NO consumed axioms, NO kind-3 (unexpressible-changed-op) legs — the one genuinely changed op (widening the report predicate to accept a registered comparison operator) is modelled DEEPLY via flag_path's `is_compare_op==0` conjunct, corresponding exactly to the gold patch's added `and fld.get_lookup(part) is None` clause. Every leg is R / I / A-reference; A-legs' correspondence to the real callees holds.

VERDICT: SOUND. >=5 distinct wrong impls (7 total: prepatch, partial-domain, boundary, control-flow-effect, ungrounded-echo, OR/AND, negation) were encoded and machine-verified; none is a CANDIDATE (none verifies), so verify=>correct is not broken. Positive control verifies; A-references sound (pure table exit 0; callee deferred in-container by design). No INCONCLUSIVE conditions: all attack verifications and the positive control completed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-12858.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When validating the ordering specification of a model, each multi-part path
  whose trailing segment cannot be resolved as a concrete model field is
  examined to decide whether it should be reported as an invalid ordering
  reference. A path is accepted (NOT reported) exactly when a field was reached
  just before the unresolved trailing segment AND that segment denotes at least
  one of the two recognised kinds of registered query operator: a value-
  producing operator (one that yields a new value to continue resolving) OR a
  comparison operator (one usable as a terminal predicate). A trailing segment
  that IS a recognised comparison operator is therefore a legitimate ordering
  target and must NOT be reported, exactly as a value-producing operator already
  is not. Otherwise — no field was reached, or the segment is neither operator
  kind — the path is reported as an invalid ordering reference.

  Concretely, for each path the decision is a function of three observations
  about its trailing segment: whether a field was reached before it
  (`reached_field`), whether the segment is a registered value-producing
  operator (`is_value_op`), and whether it is a registered comparison operator
  (`is_compare_op`). The path is flagged invalid iff no field was reached OR the
  segment is neither operator kind. The result lists, in input order, the
  flag (1 = reported invalid, 0 = accepted) of every examined path.

The three per-path observations are carried as parallel `List[int]` of 0/1
booleans (Nagini bans richer object graphs cheaply here; the tested behaviour
observes only these three predicates per path). The two operator-recognition
predicates correspond to two unchanged lookup-registry queries that the
validator calls but does not change; they are modelled as the boolean inputs
and their real semantics are recorded in mapping.md / checked by axiom_check.py
(A-reference) rather than consumed as axioms — the decision itself is modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The two registry queries that classify a path segment
# (value-producing vs. comparison operator) are unchanged callees; here their
# results enter the decision as the boolean inputs is_value_op / is_compare_op.
# Their real semantics (each returns a non-None object iff the named operator of
# that kind is registered) are validated out-of-band by axiom_check.py (G-AX)
# as A-references, not consumed as @ContractOnly Ensures. The reporting decision
# itself is modelled deeply below.
# axioms-end


# pure-start
@Pure
def flag_path(reached_field: int, is_value_op: int, is_compare_op: int) -> int:
    """The per-path decision: report the path as an invalid ordering reference
    iff EITHER no field was reached before its unresolved trailing segment, OR
    that segment is neither a value-producing operator nor a comparison
    operator. A path is accepted only when a field was reached AND the trailing
    segment is at least one of the two recognised operator kinds. Returns 1
    (report invalid) or 0 (accept)."""
    if reached_field == 0 or (is_value_op == 0 and is_compare_op == 0):
        return 1
    return 0
# pure-end


def select_reported_paths(reached_field: List[int],
                          is_value_op: List[int],
                          is_compare_op: List[int]) -> List[int]:
    # pre-conditions-start
    # The three per-path observation lists are read-only (fractional permission,
    # Required and Ensured) and index-aligned.
    Requires(Acc(list_pred(reached_field), 1 / 2))
    Requires(Acc(list_pred(is_value_op), 1 / 2))
    Requires(Acc(list_pred(is_compare_op), 1 / 2))
    Requires(len(reached_field) == len(is_value_op))
    Requires(len(reached_field) == len(is_compare_op))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(reached_field), 1 / 2))
    Ensures(Acc(list_pred(is_value_op), 1 / 2))
    Ensures(Acc(list_pred(is_compare_op), 1 / 2))
    # The three observation lists remain index-aligned (read-only).
    Ensures(len(reached_field) == len(is_value_op))
    Ensures(len(reached_field) == len(is_compare_op))
    # The result is a fresh, fully-owned list with one flag per examined path.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(reached_field))
    # Each flag is exactly the per-path decision: a path is reported invalid iff
    # no field was reached OR the trailing segment is neither operator kind. In
    # particular a path whose segment IS a comparison operator (is_compare_op),
    # with a field reached, is accepted (flag 0) — exactly as a value-producing
    # operator already is.
    Ensures(Forall(int, lambda k: (Implies(
            0 <= k and k < len(reached_field),
            Result()[k] == flag_path(reached_field[k], is_value_op[k],
                                     is_compare_op[k])))))
    # post-conditions-end
    # impl-start
    errors = []  # type: List[int]
    i = 0
    while i < len(reached_field):
        # invariants-start
        Invariant(Acc(list_pred(reached_field), 1 / 2))
        Invariant(Acc(list_pred(is_value_op), 1 / 2))
        Invariant(Acc(list_pred(is_compare_op), 1 / 2))
        Invariant(len(reached_field) == len(is_value_op))
        Invariant(len(reached_field) == len(is_compare_op))
        Invariant(Acc(list_pred(errors)))
        Invariant(0 <= i and i <= len(reached_field))
        Invariant(len(errors) == i)
        Invariant(Forall(int, lambda k: (Implies(
                0 <= k and k < i,
                errors[k] == flag_path(reached_field[k], is_value_op[k],
                                       is_compare_op[k])))))
        # invariants-end
        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
            errors.append(1)
        else:
            errors.append(0)
        Assert(errors[i] == flag_path(reached_field[i], is_value_op[i],
                                      is_compare_op[i]))
        i = i + 1
    return errors
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### AUDIT SUMMARY (adversarial G-EQ, refinement fidelity, A-legs + model<->patch correspondence).

SPEC SHAPE: model.py's select_reported_paths carries a TIGHT functional postcondition: Ensures(len(Result())==len(reached_field)) AND Ensures(Forall k: 0<=k<len -> Result()[k]==flag_path(reached_field[k],is_value_op[k],is_compare_op[k])). flag_path lives in the FROZEN @Pure region (uneditable; only the impl region lines 100-124 were edited per protocol). Thus any verifying impl must reproduce flag_path bit-for-bit on every index and match length exactly. This leaves essentially no room for a same-spec verifying WRONG impl -> strong prior toward SOUND, confirmed by falsification below.

ATTACKS (all copied model.py, edited ONLY impl region; all confirmed same-spec exit 0 via `adversary same-spec`; then `adversary weakness nagini django__django-12858 <atk>`):
- atk_1.py PREPATCH BUG (ignores is_compare_op: reports iff reached==0 or is_value_op==0). weakness exit=2 NOT-A-COUNTEREXAMPLE (verification failed). => prepatch bug reproduced/rejected by spec.
- atk_2.py PARTIAL-DOMAIN (correct on even i, always-accept on odd i). weakness exit=2 (does not verify).
- atk_3.py BOUNDARY/off-by-one (loop to len-1, drops last element -> length mismatch). weakness exit=2.
- atk_4.py CONTROL-FLOW-EFFECT (early `return errors` inside first iteration). weakness exit=2.
- atk_5.py UNGROUNDED-ORACLE ECHO (always append 1). weakness exit=2.
- atk_6.py OR-vs-AND fault (report iff reached==0 or is_value_op==0 or is_compare_op==0 -> mis-reports the isnull F2P case). weakness exit=2.
- atk_7.py NEGATED FLAG (swap 1/0). weakness exit=2.
All 7 same-spec wrong impls FAILED to verify => spec rejected each (good). No CANDIDATE (same-spec AND verifies) emerged, so NO faithful-patch resolve run was triggered (none required). Ran concurrently in batches of 3 (each Nagini check = JVM+Z3).

POSITIVE CONTROL: pos_control.py is byte-identical to bundle model.py (diff -q IDENTICAL). `bash scripts/nagini_verify.sh pos_control.py` => `Verification successful` exit=0 (13.6s). The frozen correct impl verifies.

A-REFERENCE / AXIOM AUDIT: no consumed @ContractOnly axioms (axioms region empty by design). axiom_check.py exit=0: pure truth-table A-reference confirmed (flag_path == real post-patch predicate `fld is None or (get_transform is None and get_lookup is None)` over full (reached,value,compare) truth table). Django-callee A-reference (Field.get_transform/get_lookup non-None classification, incl. isnull=lookup-not-transform F2P case) is correctly DEFERRED to the in-container G-AX run (Django not importable in ambient env) — scoping is correct, not a gap.

REFINEMENT.MD LEG AUDIT: A1=R (path collection <-> aligned List[int] indices), A2=I+A-reference (boolean algebra IDENTICAL to gold guard; the two registry queries are A-reference validated == real callees, NOT consumed axioms), A3=R (models.E015 presence/absence <-> 0/1 flag in order). Sections B/C confirm: NO consumed axioms, NO kind-3 (unexpressible-changed-op) legs — the one genuinely changed op (widening the report predicate to accept a registered comparison operator) is modelled DEEPLY via flag_path's `is_compare_op==0` conjunct, corresponding exactly to the gold patch's added `and fld.get_lookup(part) is None` clause. Every leg is R / I / A-reference; A-legs' correspondence to the real callees holds.

VERDICT: SOUND. >=5 distinct wrong impls (7 total: prepatch, partial-domain, boundary, control-flow-effect, ungrounded-echo, OR/AND, negation) were encoded and machine-verified; none is a CANDIDATE (none verifies), so verify=>correct is not broken. Positive control verifies; A-references sound (pure table exit 0; callee deferred in-container by design). No INCONCLUSIVE conditions: all attack verifications and the positive control completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of the nagini bundle for django__django-12858. The modeled decision (flag_path + the verified select_reported_paths loop) reports a path invalid iff reached_field==0 OR (is_value_op==0 AND is_compare_op==0). The real gold post-patch predicate at django/db/models/base.py:1750 (verified in the base_commit f2051eb8a7 worktree) reports iff `fld is None or (fld.get_transform(part) is None and fld.get_lookup(part) is None)`. Under the documented mapping (reached_field==0 <-> fld is None; is_value_op==0 <-> get_transform is None; is_compare_op==0 <-> get_lookup is None) the boolean algebra is byte-for-byte identical.

Full truth-table check over all 8 combinations of (rf,v,c): every row agrees. In particular the discriminating F2P case (rf=1, v=0, c=1) -> flag 0 (accept), matching the patch which ADDS `and fld.get_lookup(part) is None` so that a trailing segment that is a registered Lookup (e.g. 'isnull' on CharField, a Lookup but not a Transform) with a field reached is NOT reported. The pre-patch predicate (`fld is None or get_transform is None`) wrongly reports that case; the model correctly does not — so the spec captures exactly the gold behavior, not the buggy pre-patch behavior, and is neither too strong nor too weak.

The two callees get_transform/get_lookup are unchanged and abstracted only as their non-None booleans (A-reference, validated by axiom_check.py / G-AX), so no callee-boundary drift is introduced. The model is a total function that reproduces the gold predicate on every input in the abstract domain; there is no input on which the modeled function disagrees with the real repo's post-patch callee. Spec is FAITHFUL; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (leakage.screen -> passed=True, zero hard failures); no relaxed_leakage flag / RELAXED_LEAKAGE.md, so no deferral in play. Confirmed the spec view (spec_view over model.py) does NOT leak the gold edit beyond the public problem_statement:

- Gold edit is the added clause `and fld.get_lookup(part) is None` inside `Model._check_ordering`'s except handler (base.py:1750). The spec view never reproduces any gold-patch line, contains no diff markers, no patched file path (`django/db/models/base.py`) or dotted module path, and never names the patched repo symbols `get_transform`, `get_lookup`, or `_check_ordering`. It uses only abstract carriers `reached_field`/`is_value_op`/`is_compare_op` and prose ("value-producing operator" / "comparison operator"). No bug/fix/pre-patch/previously narration.
- Semantic check: the public problem_statement already discloses the full discriminator — 'models.E015 is raised when ordering uses lookups that are not transforms' — with the tokens lookup, transform, isnull, and E015 all present. The spec view's behavioral statement (accept a trailing segment that is a comparison operator/lookup even when it is not a value-producing operator/transform) is exactly the desired behavior the public task states; it stays at the behavioral/abstract altitude and adds nothing pointing at the specific implementation edit beyond what is public.

The leaky-specifics (get_transform/get_lookup names, base.py:1750, the added clause, pre-patch omission) all live in refinement.md / mapping.md — the AUDIT-side artifacts, NOT the consumer spec view — which is correct. No leakage in the spec view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
