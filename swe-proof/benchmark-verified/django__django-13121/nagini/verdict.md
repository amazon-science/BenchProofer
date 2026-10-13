# P2 adversarial audit — django__django-13121

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -108,7 +107,6 @@
     # pre-conditions-start
     Requires(is_kind(lhs_kind))
     Requires(is_kind(rhs_kind))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
@@ -146,8 +144,7 @@
     # post-conditions-end
     # impl-start
     if (not native_duration) and \
-            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
-            lhs_kind != rhs_kind:
+            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()):
         return PATH_DURATION()
     if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
         return PATH_TEMPORAL()
@@ -158,7 +155,6 @@
 def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
     # pre-conditions-start
     Requires(is_kind(operand_kind))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -108,7 +107,6 @@
     # pre-conditions-start
     Requires(is_kind(lhs_kind))
     Requires(is_kind(rhs_kind))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
@@ -158,7 +156,6 @@
 def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
     # pre-conditions-start
     Requires(is_kind(operand_kind))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -167,6 +164,8 @@
     Ensures(Result() == 1 if operand_kind == KIND_DURATION() else Result() == 0)
     # post-conditions-end
     # impl-start
+    if is_literal:
+        return 0
     if operand_kind == KIND_DURATION():
         return 1
     return 0
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -108,7 +107,6 @@
     # pre-conditions-start
     Requires(is_kind(lhs_kind))
     Requires(is_kind(rhs_kind))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
@@ -158,7 +156,6 @@
 def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
     # pre-conditions-start
     Requires(is_kind(operand_kind))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -167,7 +164,7 @@
     Ensures(Result() == 1 if operand_kind == KIND_DURATION() else Result() == 0)
     # post-conditions-end
     # impl-start
-    if operand_kind == KIND_DURATION():
+    if operand_kind == KIND_DURATION() or operand_kind == KIND_NONE():
         return 1
     return 0
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
@@ -108,7 +107,6 @@
     # pre-conditions-start
     Requires(is_kind(lhs_kind))
     Requires(is_kind(rhs_kind))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
@@ -149,7 +147,8 @@
             (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
             lhs_kind != rhs_kind:
         return PATH_DURATION()
-    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
+    if is_subtract and (is_temporal_kind(lhs_kind)
+                        or lhs_kind == KIND_DURATION()) and lhs_kind == rhs_kind:
         return PATH_TEMPORAL()
     return PATH_PLAIN()
     # impl-end
@@ -158,7 +157,6 @@
 def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
     # pre-conditions-start
     Requires(is_kind(operand_kind))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -108,7 +107,6 @@
     # pre-conditions-start
     Requires(is_kind(lhs_kind))
     Requires(is_kind(rhs_kind))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
@@ -145,8 +143,7 @@
         Result() == PATH_PLAIN()))
     # post-conditions-end
     # impl-start
-    if (not native_duration) and \
-            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
+    if (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
             lhs_kind != rhs_kind:
         return PATH_DURATION()
     if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
@@ -158,7 +155,6 @@
 def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
     # pre-conditions-start
     Requires(is_kind(operand_kind))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -108,7 +107,6 @@
     # pre-conditions-start
     Requires(is_kind(lhs_kind))
     Requires(is_kind(rhs_kind))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
@@ -149,7 +147,7 @@
             (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
             lhs_kind != rhs_kind:
         return PATH_DURATION()
-    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
+    if is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
         return PATH_TEMPORAL()
     return PATH_PLAIN()
     # impl-end
@@ -158,7 +156,6 @@
 def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
     # pre-conditions-start
     Requires(is_kind(operand_kind))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13121.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An arithmetic combination of two query operands is rendered to backend SQL
  along one of three code paths, chosen from the declared result kinds of the
  two operands, the operator, and whether the backend stores durations
  natively:

  (1) DURATION-arithmetic path — selected (only when the backend lacks a native
      duration storage type) exactly when the two operand kinds differ and at
      least one of them is a duration (e.g. a date/datetime kind paired with a
      duration kind). A pairing whose two operand kinds are equal is never on
      this path, including the case where both kinds are durations.

  (2) TEMPORAL-subtraction path — selected for the subtraction of two operands
      of the same temporal kind (date/datetime/time).

  (3) PLAIN combination path — every other pairing.

  Independently, when an operand is rendered ON the duration-arithmetic path,
  the per-operand format flag is set for an operand exactly when that operand's
  result kind is a duration. The flag depends only on the operand's result
  kind; it does not depend on whether the operand is a literal value or a
  stored column reference.

Field result kinds and the chosen path are modelled as small integer codes
(an int refinement of the finite set of `get_internal_type()` names and of the
expression-class dispatch); see refinement.md / mapping.md for the bijection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: both behaviours are modelled deeply over the
#  finite integer abstraction of field-kind codes and dispatch-path codes.)
# axioms-end


# pure-start
# Result-kind codes (int refinement of output_field.get_internal_type()):
@Pure
def KIND_NONE() -> int:
    # no resolvable result kind (operand has no output field)
    return 0


@Pure
def KIND_DURATION() -> int:
    return 1


@Pure
def KIND_DATE() -> int:
    return 2


@Pure
def KIND_DATETIME() -> int:
    return 3


@Pure
def KIND_TIME() -> int:
    return 4


@Pure
def KIND_OTHER() -> int:
    # any non-temporal, non-duration kind (integer, char, ...)
    return 5


# Dispatch-path codes (int refinement of the chosen rendering class):
@Pure
def PATH_DURATION() -> int:
    return 0


@Pure
def PATH_TEMPORAL() -> int:
    return 1


@Pure
def PATH_PLAIN() -> int:
    return 2


@Pure
def is_kind(k: int) -> bool:
    return k == 0 or k == 1 or k == 2 or k == 3 or k == 4 or k == 5


@Pure
def is_temporal_kind(k: int) -> bool:
    # date / datetime / time form the temporal-subtraction family
    return k == 2 or k == 3 or k == 4
# pure-end


def select_arithmetic_path(lhs_kind: int, rhs_kind: int,
                           is_subtract: bool, native_duration: bool) -> int:
    # pre-conditions-start
    Requires(is_kind(lhs_kind))
    Requires(is_kind(rhs_kind))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
            or Result() == PATH_PLAIN())
    # (1) duration-arithmetic ONLY for a mixed pairing: exactly one operand a
    #     duration AND the two kinds differ, on a non-native backend.
    Ensures(Implies(
        (not native_duration)
        and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
        and lhs_kind != rhs_kind,
        Result() == PATH_DURATION()))
    # A both-duration pairing is NOT the duration path (the discriminator).
    Ensures(Implies(
        lhs_kind == KIND_DURATION() and rhs_kind == KIND_DURATION(),
        Result() != PATH_DURATION()))
    # (2) temporal subtraction for same-kind temporal operands under SUB.
    Ensures(Implies(
        (not (
            (not native_duration)
            and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
            and lhs_kind != rhs_kind))
        and is_subtract and is_temporal_kind(lhs_kind)
        and lhs_kind == rhs_kind,
        Result() == PATH_TEMPORAL()))
    # (3) everything else is the plain path.
    Ensures(Implies(
        not (
            (not native_duration)
            and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
            and lhs_kind != rhs_kind)
        and not (
            is_subtract and is_temporal_kind(lhs_kind)
            and lhs_kind == rhs_kind),
        Result() == PATH_PLAIN()))
    # post-conditions-end
    # impl-start
    if (not native_duration) and \
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
            lhs_kind != rhs_kind:
        return PATH_DURATION()
    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()
    # impl-end


def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
    # pre-conditions-start
    Requires(is_kind(operand_kind))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == 0 or Result() == 1)
    # The duration-format wrapper is applied to EVERY duration-kind operand,
    # uniformly — independent of whether the operand is a literal value.
    Ensures(Result() == 1 if operand_kind == KIND_DURATION() else Result() == 0)
    # post-conditions-end
    # impl-start
    if operand_kind == KIND_DURATION():
        return 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for django__django-13121 nagini.

WHY SOUND (spec fully pins outputs): both spec functions are total & single-valued over the entire Requires domain, so any verifying impl is unique up to type refinement -> no verifying-but-wrong impl exists -> no candidate patch to materialize.
 * operand_format_flag: Ensures(Result()==1 if operand_kind==KIND_DURATION() else Result()==0) -- total over all 6 kinds x is_literal.
 * select_arithmetic_path: three Implies (model.py:116-143) partition the 6x6x2x2 domain disjointly & exhaustively: A=(not native & (lhs|rhs==DUR) & lhs!=rhs)->PATH_DURATION; DUR+DUR discriminator Implies(lhs==DUR & rhs==DUR -> !=PATH_DURATION); (not A & sub & temporal(lhs) & lhs==rhs)->PATH_TEMPORAL; else->PATH_PLAIN. Every input has exactly one forced result.

ATTACKS (all same-spec exit 0 via `adversary same-spec`; all run via `python -m swebench_unified.adversary weakness nagini django__django-13121 <path>`, concurrent batches of <=3 JVMs). ALL returned exit=2 NOT-A-COUNTEREXAMPLE 'attack does not verify' -- each hit a real postcondition rejection (not timeout/infra; verifier completed, positive control VERIFIED in 17.9s in same env proving the toolchain accepts a correct impl):
 * atk_1.py -- partial-domain / PREPATCH#1: drop `lhs_kind != rhs_kind` from duration guard; byte-identical to bundle model_prepatch.py (diff empty). Fails Implies(DUR&DUR -> !=PATH_DURATION).
 * atk_2.py -- PREPATCH#2: reinstate `if is_literal: return 0`; byte-identical to model_prepatch_2.py (diff empty). Fails Result()==1 for (KIND_DURATION, is_literal=True).
 * atk_3.py -- boundary: format flag also fires for KIND_NONE. Fails Result()==0 for (KIND_NONE).
 * atk_4.py -- boundary: temporal guard extended to KIND_DURATION so DUR-DUR-sub -> PATH_TEMPORAL. Fails PLAIN clause (135-143) on (DUR,DUR,sub,native-or-not routed via not-A).
 * atk_5.py -- control-flow-effect: drop `not native_duration` guard, so DUR+other mixed -> PATH_DURATION even on native backend. Fails PLAIN clause when native_duration=True.
 * atk_6.py -- ungrounded/control-flow: drop `is_subtract`, so same-temporal-kind non-subtraction -> PATH_TEMPORAL. Fails PLAIN clause for is_subtract=False same-temporal pairing.

NO CANDIDATE -> no faithful refined patch needed to be materialized/resolve-run (the plan's step-2 obligation is vacuous here because 0 attacks reached CANDIDATE status).

REFINEMENT.MD LEG AUDIT: all legs R / A-reference / I; no kind-3 (unexpressible-changed-op) legs; NO consumed @ContractOnly axioms. Legs: A1=R, A2=I, A3=R, A4=R+I, A5=R+I, A6=R, B1=R, B2=R, B3=R+I, C=I (dead-code removal, no spec obligation). The two A-reference decisions (refinement.md 3.1 select_arithmetic_path<->CombinedExpression.as_sql; 3.2 operand_format_flag<->DurationExpression.compile) validated model==oracle exhaustively over all (lhs,rhs,sub,native) & (kind,is_literal) + 20000 fuzz via axiom_check.check_model_vs_oracle() (PASS); Django end-to-end layer runs in-container under G-AX. Correspondence to real callees holds.

VERDICT SOUND: >=6 distinct wrong impls (incl. both prepatch bugs) attacked and machine-verified; none verifies (spec rejects every behavioral deviation); positive control verifies; no verify->!resolve counterexample found; refinement legs are all R/A-reference/I with faithful A-reference correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13121.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An arithmetic combination of two query operands is rendered to backend SQL
  along one of three code paths, chosen from the declared result kinds of the
  two operands, the operator, and whether the backend stores durations
  natively:

  (1) DURATION-arithmetic path — selected (only when the backend lacks a native
      duration storage type) exactly when the two operand kinds differ and at
      least one of them is a duration (e.g. a date/datetime kind paired with a
      duration kind). A pairing whose two operand kinds are equal is never on
      this path, including the case where both kinds are durations.

  (2) TEMPORAL-subtraction path — selected for the subtraction of two operands
      of the same temporal kind (date/datetime/time).

  (3) PLAIN combination path — every other pairing.

  Independently, when an operand is rendered ON the duration-arithmetic path,
  the per-operand format flag is set for an operand exactly when that operand's
  result kind is a duration. The flag depends only on the operand's result
  kind; it does not depend on whether the operand is a literal value or a
  stored column reference.

Field result kinds and the chosen path are modelled as small integer codes
(an int refinement of the finite set of `get_internal_type()` names and of the
expression-class dispatch); see refinement.md / mapping.md for the bijection.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: both behaviours are modelled deeply over the
#  finite integer abstraction of field-kind codes and dispatch-path codes.)
# axioms-end


# pure-start
# Result-kind codes (int refinement of output_field.get_internal_type()):
@Pure
def KIND_NONE() -> int:
    # no resolvable result kind (operand has no output field)
    return 0


@Pure
def KIND_DURATION() -> int:
    return 1


@Pure
def KIND_DATE() -> int:
    return 2


@Pure
def KIND_DATETIME() -> int:
    return 3


@Pure
def KIND_TIME() -> int:
    return 4


@Pure
def KIND_OTHER() -> int:
    # any non-temporal, non-duration kind (integer, char, ...)
    return 5


# Dispatch-path codes (int refinement of the chosen rendering class):
@Pure
def PATH_DURATION() -> int:
    return 0


@Pure
def PATH_TEMPORAL() -> int:
    return 1


@Pure
def PATH_PLAIN() -> int:
    return 2


@Pure
def is_kind(k: int) -> bool:
    return k == 0 or k == 1 or k == 2 or k == 3 or k == 4 or k == 5


@Pure
def is_temporal_kind(k: int) -> bool:
    # date / datetime / time form the temporal-subtraction family
    return k == 2 or k == 3 or k == 4
# pure-end


def select_arithmetic_path(lhs_kind: int, rhs_kind: int,
                           is_subtract: bool, native_duration: bool) -> int:
    # pre-conditions-start
    Requires(is_kind(lhs_kind))
    Requires(is_kind(rhs_kind))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == PATH_DURATION() or Result() == PATH_TEMPORAL()
            or Result() == PATH_PLAIN())
    # (1) duration-arithmetic ONLY for a mixed pairing: exactly one operand a
    #     duration AND the two kinds differ, on a non-native backend.
    Ensures(Implies(
        (not native_duration)
        and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
        and lhs_kind != rhs_kind,
        Result() == PATH_DURATION()))
    # A both-duration pairing is NOT the duration path (the discriminator).
    Ensures(Implies(
        lhs_kind == KIND_DURATION() and rhs_kind == KIND_DURATION(),
        Result() != PATH_DURATION()))
    # (2) temporal subtraction for same-kind temporal operands under SUB.
    Ensures(Implies(
        (not (
            (not native_duration)
            and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
            and lhs_kind != rhs_kind))
        and is_subtract and is_temporal_kind(lhs_kind)
        and lhs_kind == rhs_kind,
        Result() == PATH_TEMPORAL()))
    # (3) everything else is the plain path.
    Ensures(Implies(
        not (
            (not native_duration)
            and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION())
            and lhs_kind != rhs_kind)
        and not (
            is_subtract and is_temporal_kind(lhs_kind)
            and lhs_kind == rhs_kind),
        Result() == PATH_PLAIN()))
    # post-conditions-end
    # impl-start
    if (not native_duration) and \
            (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and \
            lhs_kind != rhs_kind:
        return PATH_DURATION()
    if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind:
        return PATH_TEMPORAL()
    return PATH_PLAIN()
    # impl-end


def operand_format_flag(operand_kind: int, is_literal: bool) -> int:
    # pre-conditions-start
    Requires(is_kind(operand_kind))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == 0 or Result() == 1)
    # The duration-format wrapper is applied to EVERY duration-kind operand,
    # uniformly — independent of whether the operand is a literal value.
    Ensures(Result() == 1 if operand_kind == KIND_DURATION() else Result() == 0)
    # post-conditions-end
    # impl-start
    if operand_kind == KIND_DURATION():
        return 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for django__django-13121 nagini.

WHY SOUND (spec fully pins outputs): both spec functions are total & single-valued over the entire Requires domain, so any verifying impl is unique up to type refinement -> no verifying-but-wrong impl exists -> no candidate patch to materialize.
 * operand_format_flag: Ensures(Result()==1 if operand_kind==KIND_DURATION() else Result()==0) -- total over all 6 kinds x is_literal.
 * select_arithmetic_path: three Implies (model.py:116-143) partition the 6x6x2x2 domain disjointly & exhaustively: A=(not native & (lhs|rhs==DUR) & lhs!=rhs)->PATH_DURATION; DUR+DUR discriminator Implies(lhs==DUR & rhs==DUR -> !=PATH_DURATION); (not A & sub & temporal(lhs) & lhs==rhs)->PATH_TEMPORAL; else->PATH_PLAIN. Every input has exactly one forced result.

ATTACKS (all same-spec exit 0 via `adversary same-spec`; all run via `python -m swebench_unified.adversary weakness nagini django__django-13121 <path>`, concurrent batches of <=3 JVMs). ALL returned exit=2 NOT-A-COUNTEREXAMPLE 'attack does not verify' -- each hit a real postcondition rejection (not timeout/infra; verifier completed, positive control VERIFIED in 17.9s in same env proving the toolchain accepts a correct impl):
 * atk_1.py -- partial-domain / PREPATCH#1: drop `lhs_kind != rhs_kind` from duration guard; byte-identical to bundle model_prepatch.py (diff empty). Fails Implies(DUR&DUR -> !=PATH_DURATION).
 * atk_2.py -- PREPATCH#2: reinstate `if is_literal: return 0`; byte-identical to model_prepatch_2.py (diff empty). Fails Result()==1 for (KIND_DURATION, is_literal=True).
 * atk_3.py -- boundary: format flag also fires for KIND_NONE. Fails Result()==0 for (KIND_NONE).
 * atk_4.py -- boundary: temporal guard extended to KIND_DURATION so DUR-DUR-sub -> PATH_TEMPORAL. Fails PLAIN clause (135-143) on (DUR,DUR,sub,native-or-not routed via not-A).
 * atk_5.py -- control-flow-effect: drop `not native_duration` guard, so DUR+other mixed -> PATH_DURATION even on native backend. Fails PLAIN clause when native_duration=True.
 * atk_6.py -- ungrounded/control-flow: drop `is_subtract`, so same-temporal-kind non-subtraction -> PATH_TEMPORAL. Fails PLAIN clause for is_subtract=False same-temporal pairing.

NO CANDIDATE -> no faithful refined patch needed to be materialized/resolve-run (the plan's step-2 obligation is vacuous here because 0 attacks reached CANDIDATE status).

REFINEMENT.MD LEG AUDIT: all legs R / A-reference / I; no kind-3 (unexpressible-changed-op) legs; NO consumed @ContractOnly axioms. Legs: A1=R, A2=I, A3=R, A4=R+I, A5=R+I, A6=R, B1=R, B2=R, B3=R+I, C=I (dead-code removal, no spec obligation). The two A-reference decisions (refinement.md 3.1 select_arithmetic_path<->CombinedExpression.as_sql; 3.2 operand_format_flag<->DurationExpression.compile) validated model==oracle exhaustively over all (lhs,rhs,sub,native) & (kind,is_literal) + 20000 fuzz via axiom_check.check_model_vs_oracle() (PASS); Django end-to-end layer runs in-container under G-AX. Correspondence to real callees holds.

VERDICT SOUND: >=6 distinct wrong impls (incl. both prepatch bugs) attacked and machine-verified; none verifies (spec rejects every behavioral deviation); positive control verifies; no verify->!resolve counterexample found; refinement legs are all R/A-reference/I with faithful A-reference correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed: the two modeled functions agree with the real post-patch Django callees on every input; no diverging input exists.

Evidence:
- Real pre-patch source read from a base_commit worktree (ec5aa2161d) and the gold patch fetched verbatim from data/swe_bench_verified/test.jsonl. axiom_check.py's oracle is a line-faithful transcription of the actual post-patch CombinedExpression.as_sql and DurationExpression.compile.
- model.py verifies under the pinned Nagini (Verification successful, 16.6s).
- axiom_check.py model-vs-oracle layer PASSES: exhaustive over all (lhs_kind, rhs_kind, is_subtract, native) = 6x6x2x2 and all (operand_kind, is_literal) combos, plus 20000-seed fuzz, plus explicit discriminators. (The live-Django SQLite F2P layer was SKIPped only because Django is not importable in this env; the transcribed oracle covers the same predicates.)

Abstraction-boundary reasoning (why the spec is not too strong / does not drift):
1. select_arithmetic_path guard 1 (duration): real is `not native and 'DurationField' in {lhs_type,rhs_type} and lhs_type != rhs_type`; model is `not native and (lhs==DUR or rhs==DUR) and lhs!=rhs`. Equivalent: 'DurationField' in {..} <=> at least one side duration. The KIND_OTHER collapse (all non-temporal/non-duration real types mapped to one code) is sound because the `!=` test only alters the outcome when exactly one side is a duration, and any distinct non-duration real type yields lhs!=rhs in both model and reality. FieldError->None->KIND_NONE preserved (None != 'DurationField').
2. guard 2 (temporal SUB): temporal kinds are distinct codes, so lhs==rhs among temporals <=> real lhs_type==rhs_type among {DateField,DateTimeField,TimeField}; native correctly irrelevant. Post-patch also drops the pre-patch `lhs_output and rhs_output` non-None guard, but `lhs_type in datetime_fields` already forces non-None, matching the model.
3. operand_format_flag: post-patch removes the isinstance(side, DurationValue) exemption; wrapper applied iff get_internal_type()=='DurationField'. Model returns 1 iff operand_kind==DURATION, independent of is_literal. Matches exactly, including the literal-duration case (KIND_DURATION, is_literal=True) -> 1.

The int-enum refinement of get_internal_type() is faithful because the real guards read the type only via ==, != and finite-set membership. No axioms are consumed (deep model); G-AX A-references validated. Spec region byte-identical. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = projected model.py (docstring + pure/pre/post regions, impl elided). refinement.md/mapping.md/meta.json are AUDITOR docs, not the solver-visible spec view, so their naming of expressions.py/DurationValue/as_sql/gold hunks is out of scope. Checked the spec view against all 9 gold-patch changed symbols (Combinable, DurationValue, as_sql, date_interval_sql, get_group_by_cols, resolve_expression, set_source_expressions, date_extract_sql, time_trunc_sql) plus post-patch specifics (TemporalSubtraction, DurationExpression, format_for_duration_arithmetic, has_native_duration_field, isinstance, expressions.py): NONE appear in the view as identifiers or in comments. Mechanical screen leakage.screen() PASSED (no L1 diff markers, no reproduced gold lines, no L2 file/module paths, no L2/L5 identifier collisions, no L3 narration). The only 'patch' string hits are substrings of 'dispatch'/'dispatch-path', which the word-boundary narration regex correctly ignores. Spec-view identifiers are abstract model names (select_arithmetic_path, operand_format_flag, KIND_*/PATH_* codes). The behavioral discriminators the spec pins ('a both-duration pairing is NOT the duration path'; 'format flag independent of literal-vs-column') are stated as DESIRED behavior over an integer abstraction, not as an edit/pre-patch narration; the public problem_statement already discloses durations-only expressions are broken on SQLite/MySQL. Describing correct behavior abstractly does not localize the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
