# P2 adversarial audit — django__django-11551

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
@@ -52,7 +52,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     # pre-conditions-start
     # No heap state is touched; the routine is a pure decision over the
     # observations of the unchanged primitives.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly one of the three diagnostic codes.
@@ -117,13 +115,11 @@
         return 0
     if is_presenter_attr:
         return 0
-    if not structural_absent:
-        relation = structural_is_relation  # type: bool
-    elif attribute_absent:
-        return 108
-    else:
-        relation = attribute_is_relation
-    if relation:
-        return 109
-    return 0
+    if not attribute_absent:
+        if structural_absent:
+            return 0
+        if structural_is_relation:
+            return 109
+        return 0
+    return 108
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     # pre-conditions-start
     # No heap state is touched; the routine is a pure decision over the
     # observations of the unchanged primitives.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly one of the three diagnostic codes.
@@ -118,7 +116,7 @@
     if is_presenter_attr:
         return 0
     if not structural_absent:
-        relation = structural_is_relation  # type: bool
+        relation = attribute_is_relation  # WRONG: should be structural_is_relation
     elif attribute_absent:
         return 108
     else:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     # pre-conditions-start
     # No heap state is touched; the routine is a pure decision over the
     # observations of the unchanged primitives.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly one of the three diagnostic codes.
@@ -117,13 +115,9 @@
         return 0
     if is_presenter_attr:
         return 0
-    if not structural_absent:
-        relation = structural_is_relation  # type: bool
-    elif attribute_absent:
+    if structural_absent:
         return 108
-    else:
-        relation = attribute_is_relation
-    if relation:
+    if structural_is_relation:
         return 109
     return 0
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     # pre-conditions-start
     # No heap state is touched; the routine is a pure decision over the
     # observations of the unchanged primitives.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly one of the three diagnostic codes.
@@ -120,7 +118,7 @@
     if not structural_absent:
         relation = structural_is_relation  # type: bool
     elif attribute_absent:
-        return 108
+        return 109
     else:
         relation = attribute_is_relation
     if relation:
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     # pre-conditions-start
     # No heap state is touched; the routine is a pure decision over the
     # observations of the unchanged primitives.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly one of the three diagnostic codes.
@@ -115,8 +113,6 @@
     # impl-start
     if is_invokable:
         return 0
-    if is_presenter_attr:
-        return 0
     if not structural_absent:
         relation = structural_is_relation  # type: bool
     elif attribute_absent:
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     # pre-conditions-start
     # No heap state is touched; the routine is a pure decision over the
     # observations of the unchanged primitives.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly one of the three diagnostic codes.
@@ -123,7 +121,7 @@
         return 108
     else:
         relation = attribute_is_relation
-    if relation:
+    if not relation:
         return 109
     return 0
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     # pre-conditions-start
     # No heap state is touched; the routine is a pure decision over the
     # observations of the unchanged primitives.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The result is exactly one of the three diagnostic codes.
@@ -118,12 +116,10 @@
     if is_presenter_attr:
         return 0
     if not structural_absent:
-        relation = structural_is_relation  # type: bool
-    elif attribute_absent:
+        if structural_is_relation:
+            return 109
+        return 0
+    if attribute_absent:
         return 108
-    else:
-        relation = attribute_is_relation
-    if relation:
-        return 109
     return 0
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A startup validator inspects one entry that a presentation list declares it
  wants to display for a model. The entry is valid (produces no complaint) when
  it can be resolved to something displayable, and otherwise produces exactly
  one diagnostic. There are two distinct diagnostics:

    * a "not-resolvable" complaint (call it the E108 code), meaning the entry
      names nothing the model knows about; and
    * a "wrong-kind" complaint (call it the E109 code), meaning the entry
      resolves to a relation that cannot be displayed in a single column.

  The entry resolves successfully in any of these independent ways, checked in
  order, and as soon as one succeeds the entry is accepted with no further work:

    (1) the entry is itself directly invokable;
    (2) the entry names an attribute the presenter object itself carries;
    (3) the entry names a structural field declared on the model (a metadata
        field lookup that either yields a field or reports the field absent); or
    (4) the entry names an attribute reachable on the model class (a plain
        attribute lookup that either yields a value or reports it absent).

  The required behaviour:

    * If (1) or (2) holds, the entry is accepted (no diagnostic), and none of
      the later resolution steps are even attempted.
    * Otherwise the structural-field lookup (3) is attempted FIRST. Only if it
      reports the field absent is the attribute lookup (4) attempted. The
      not-resolvable complaint (E108) is produced if AND ONLY IF the structural
      lookup reports absent AND the attribute lookup also reports absent — i.e.
      a single failed structural lookup must NOT by itself produce a complaint
      while an attribute is still reachable, and the unreachability of the
      attribute must NOT by itself produce a complaint while a structural field
      exists.
    * If EITHER lookup yields something (a field from (3) or a value from (4)),
      that resolved object is examined: if it is a non-displayable relation the
      wrong-kind complaint (E109) is produced; otherwise the entry is accepted.
      The wrong-kind examination applies equally to the object obtained from (3)
      and to the object obtained from (4).

The two early predicates and the two lookups are unchanged opaque primitives.
The directly-invokable test and the presenter-attribute test are pure boolean
decisions. Each lookup is modelled by a pair: a boolean "reports absent" flag
and, when it does not report absent, a boolean "is a non-displayable relation"
flag for the object it yields. The diagnostic produced is reported as an
integer code: 0 = accepted (no diagnostic), 108 = not-resolvable, 109 =
wrong-kind.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms are consumed: the unchanged primitives this routine
#  consults — the invokable test, the presenter-attribute test, the structural
#  field lookup, and the attribute lookup — are each reduced to the boolean
#  observation they produce, supplied as parameters. The decision logic over
#  those observations is the changed behaviour and is modelled deeply below.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def check_display_item(
        is_invokable: bool,
        is_presenter_attr: bool,
        structural_absent: bool,
        structural_is_relation: bool,
        attribute_absent: bool,
        attribute_is_relation: bool) -> int:
    # pre-conditions-start
    # No heap state is touched; the routine is a pure decision over the
    # observations of the unchanged primitives.
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly one of the three diagnostic codes.
    Ensures(Result() == 0 or Result() == 108 or Result() == 109)

    # (A) Directly-invokable or a presenter attribute => accepted, with NO later
    #     resolution attempted (so the later observations are irrelevant).
    Ensures(Implies(is_invokable or is_presenter_attr, Result() == 0))

    # (B) The not-resolvable complaint is produced IFF neither early acceptance
    #     holds AND BOTH lookups report absent. A single absent lookup must not
    #     on its own yield this complaint while the other lookup still resolves.
    Ensures((Result() == 108) ==
            (not (is_invokable or is_presenter_attr)
             and structural_absent and attribute_absent))

    # (C) When neither early acceptance holds and the STRUCTURAL lookup yields a
    #     field, that field decides the verdict: wrong-kind iff it is a
    #     non-displayable relation, else accepted. (The attribute lookup is not
    #     consulted in this case.)
    Ensures(Implies(not (is_invokable or is_presenter_attr) and not structural_absent,
                    Result() == (109 if structural_is_relation else 0)))

    # (D) When neither early acceptance holds, the structural lookup reports
    #     absent, but the ATTRIBUTE lookup yields a value, THAT value decides the
    #     verdict equally: wrong-kind iff it is a non-displayable relation, else
    #     accepted. (This is the path that must NOT collapse to the
    #     not-resolvable complaint.)
    Ensures(Implies(not (is_invokable or is_presenter_attr)
                    and structural_absent and not attribute_absent,
                    Result() == (109 if attribute_is_relation else 0)))
    # post-conditions-end
    # impl-start
    if is_invokable:
        return 0
    if is_presenter_attr:
        return 0
    if not structural_absent:
        relation = structural_is_relation  # type: bool
    elif attribute_absent:
        return 108
    else:
        relation = attribute_is_relation
    if relation:
        return 109
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is totally deterministic: postconditions (A) early-accept, (B) 108 iff both lookups absent (an IFF), (C) structural-present decides verdict, (D) structural-absent+attribute-present decides equally, plus codomain {0,108,109}, pin ALL 64 boolean input combos to exactly one value each, and that value equals the gold decision (axiom_check.py exit 0, 64 combos + real-callee PositionField witness). No Requires restricts the domain. Since the spec is functionally deterministic and equals gold on every reachable observation, no same-spec wrong impl can verify, so there is NO candidate to materialize a faithful patch for (patches={}).

A-leg audit: refinement.md correctly claims NO A-consumed and NO A-reference legs. The axioms-start/end region contains only comments (no @ContractOnly axiom). All 7 correspondence rows are R+I; the genuinely-changed operation (decision logic) is modeled DEEPLY in the impl region, not hidden behind an axiom. No kind-3 legs. Correspondence to real callees (callable/hasattr/get_field/getattr/isinstance(...,ManyToManyField)) is validated exhaustively by axiom_check.py, which passes.

Attacks (all copy model.py, edit ONLY impl region; axioms/@Pure/Requires/Ensures byte-identical; all same-spec exit 0):
- atk_1 prepatch bug (structural lookup gated behind attribute reachability; == bundle model_prepatch.py). differs_from_gold=6 combos. weakness exit 2 (does not verify).
- atk_2 control-flow-effect: when structural present, uses attribute_is_relation instead of structural_is_relation (violates C). differs=4. exit 2.
- atk_3 boundary: emit 108 when structural_absent alone, ignoring attribute (violates B/D). differs=4. exit 2.
- atk_4 code-swap: emit 109 instead of 108 on both-absent (violates B). differs=4. exit 2.
- atk_5 ungrounded-oracle echo: drops the is_presenter_attr short-circuit (violates A). differs=10. exit 2.
- atk_6 partial-domain: reversed relation test (109 when not relation). differs=12. exit 2.
- atk_7 subtle: when structural_absent & attribute present, always accept, ignoring attribute_is_relation (violates D). differs=2. exit 2.

Commands:
- same-spec: PY -m swebench_unified.adversary same-spec nagini django__django-11551 <atk> -> exit 0 for all 7 + pos_control.
- weakness: PY -m swebench_unified.adversary weakness nagini django__django-11551 <atk> -> exit 2 for all 7 (NOT-A-COUNTEREXAMPLE: verification failed; spec rejected impl).
- pos_control: bash scripts/nagini_verify.sh <pos_control.py> -> exit 0 (Verification successful, 17.27s).
- axiom_check.py -> exit 0 (G-AX OK, 64 combos + PositionField witness accepted).
- bundle model_prepatch.py verify -> exit 1: Postcondition clause (D) might not hold (prepatch bug reproduced).

No candidate (verifying wrong impl) found -> no resolve run needed. All >=5 (7) attacks fully verified; none breaks the spec. Verdict SOUND.

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
"""Twin-artifact model for django__django-11551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A startup validator inspects one entry that a presentation list declares it
  wants to display for a model. The entry is valid (produces no complaint) when
  it can be resolved to something displayable, and otherwise produces exactly
  one diagnostic. There are two distinct diagnostics:

    * a "not-resolvable" complaint (call it the E108 code), meaning the entry
      names nothing the model knows about; and
    * a "wrong-kind" complaint (call it the E109 code), meaning the entry
      resolves to a relation that cannot be displayed in a single column.

  The entry resolves successfully in any of these independent ways, checked in
  order, and as soon as one succeeds the entry is accepted with no further work:

    (1) the entry is itself directly invokable;
    (2) the entry names an attribute the presenter object itself carries;
    (3) the entry names a structural field declared on the model (a metadata
        field lookup that either yields a field or reports the field absent); or
    (4) the entry names an attribute reachable on the model class (a plain
        attribute lookup that either yields a value or reports it absent).

  The required behaviour:

    * If (1) or (2) holds, the entry is accepted (no diagnostic), and none of
      the later resolution steps are even attempted.
    * Otherwise the structural-field lookup (3) is attempted FIRST. Only if it
      reports the field absent is the attribute lookup (4) attempted. The
      not-resolvable complaint (E108) is produced if AND ONLY IF the structural
      lookup reports absent AND the attribute lookup also reports absent — i.e.
      a single failed structural lookup must NOT by itself produce a complaint
      while an attribute is still reachable, and the unreachability of the
      attribute must NOT by itself produce a complaint while a structural field
      exists.
    * If EITHER lookup yields something (a field from (3) or a value from (4)),
      that resolved object is examined: if it is a non-displayable relation the
      wrong-kind complaint (E109) is produced; otherwise the entry is accepted.
      The wrong-kind examination applies equally to the object obtained from (3)
      and to the object obtained from (4).

The two early predicates and the two lookups are unchanged opaque primitives.
The directly-invokable test and the presenter-attribute test are pure boolean
decisions. Each lookup is modelled by a pair: a boolean "reports absent" flag
and, when it does not report absent, a boolean "is a non-displayable relation"
flag for the object it yields. The diagnostic produced is reported as an
integer code: 0 = accepted (no diagnostic), 108 = not-resolvable, 109 =
wrong-kind.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms are consumed: the unchanged primitives this routine
#  consults — the invokable test, the presenter-attribute test, the structural
#  field lookup, and the attribute lookup — are each reduced to the boolean
#  observation they produce, supplied as parameters. The decision logic over
#  those observations is the changed behaviour and is modelled deeply below.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def check_display_item(
        is_invokable: bool,
        is_presenter_attr: bool,
        structural_absent: bool,
        structural_is_relation: bool,
        attribute_absent: bool,
        attribute_is_relation: bool) -> int:
    # pre-conditions-start
    # No heap state is touched; the routine is a pure decision over the
    # observations of the unchanged primitives.
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly one of the three diagnostic codes.
    Ensures(Result() == 0 or Result() == 108 or Result() == 109)

    # (A) Directly-invokable or a presenter attribute => accepted, with NO later
    #     resolution attempted (so the later observations are irrelevant).
    Ensures(Implies(is_invokable or is_presenter_attr, Result() == 0))

    # (B) The not-resolvable complaint is produced IFF neither early acceptance
    #     holds AND BOTH lookups report absent. A single absent lookup must not
    #     on its own yield this complaint while the other lookup still resolves.
    Ensures((Result() == 108) ==
            (not (is_invokable or is_presenter_attr)
             and structural_absent and attribute_absent))

    # (C) When neither early acceptance holds and the STRUCTURAL lookup yields a
    #     field, that field decides the verdict: wrong-kind iff it is a
    #     non-displayable relation, else accepted. (The attribute lookup is not
    #     consulted in this case.)
    Ensures(Implies(not (is_invokable or is_presenter_attr) and not structural_absent,
                    Result() == (109 if structural_is_relation else 0)))

    # (D) When neither early acceptance holds, the structural lookup reports
    #     absent, but the ATTRIBUTE lookup yields a value, THAT value decides the
    #     verdict equally: wrong-kind iff it is a non-displayable relation, else
    #     accepted. (This is the path that must NOT collapse to the
    #     not-resolvable complaint.)
    Ensures(Implies(not (is_invokable or is_presenter_attr)
                    and structural_absent and not attribute_absent,
                    Result() == (109 if attribute_is_relation else 0)))
    # post-conditions-end
    # impl-start
    if is_invokable:
        return 0
    if is_presenter_attr:
        return 0
    if not structural_absent:
        relation = structural_is_relation  # type: bool
    elif attribute_absent:
        return 108
    else:
        relation = attribute_is_relation
    if relation:
        return 109
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is totally deterministic: postconditions (A) early-accept, (B) 108 iff both lookups absent (an IFF), (C) structural-present decides verdict, (D) structural-absent+attribute-present decides equally, plus codomain {0,108,109}, pin ALL 64 boolean input combos to exactly one value each, and that value equals the gold decision (axiom_check.py exit 0, 64 combos + real-callee PositionField witness). No Requires restricts the domain. Since the spec is functionally deterministic and equals gold on every reachable observation, no same-spec wrong impl can verify, so there is NO candidate to materialize a faithful patch for (patches={}).

A-leg audit: refinement.md correctly claims NO A-consumed and NO A-reference legs. The axioms-start/end region contains only comments (no @ContractOnly axiom). All 7 correspondence rows are R+I; the genuinely-changed operation (decision logic) is modeled DEEPLY in the impl region, not hidden behind an axiom. No kind-3 legs. Correspondence to real callees (callable/hasattr/get_field/getattr/isinstance(...,ManyToManyField)) is validated exhaustively by axiom_check.py, which passes.

Attacks (all copy model.py, edit ONLY impl region; axioms/@Pure/Requires/Ensures byte-identical; all same-spec exit 0):
- atk_1 prepatch bug (structural lookup gated behind attribute reachability; == bundle model_prepatch.py). differs_from_gold=6 combos. weakness exit 2 (does not verify).
- atk_2 control-flow-effect: when structural present, uses attribute_is_relation instead of structural_is_relation (violates C). differs=4. exit 2.
- atk_3 boundary: emit 108 when structural_absent alone, ignoring attribute (violates B/D). differs=4. exit 2.
- atk_4 code-swap: emit 109 instead of 108 on both-absent (violates B). differs=4. exit 2.
- atk_5 ungrounded-oracle echo: drops the is_presenter_attr short-circuit (violates A). differs=10. exit 2.
- atk_6 partial-domain: reversed relation test (109 when not relation). differs=12. exit 2.
- atk_7 subtle: when structural_absent & attribute present, always accept, ignoring attribute_is_relation (violates D). differs=2. exit 2.

Commands:
- same-spec: PY -m swebench_unified.adversary same-spec nagini django__django-11551 <atk> -> exit 0 for all 7 + pos_control.
- weakness: PY -m swebench_unified.adversary weakness nagini django__django-11551 <atk> -> exit 2 for all 7 (NOT-A-COUNTEREXAMPLE: verification failed; spec rejected impl).
- pos_control: bash scripts/nagini_verify.sh <pos_control.py> -> exit 0 (Verification successful, 17.27s).
- axiom_check.py -> exit 0 (G-AX OK, 64 combos + PositionField witness accepted).
- bundle model_prepatch.py verify -> exit 1: Postcondition clause (D) might not hold (prepatch bug reproduced).

No candidate (verifying wrong impl) found -> no resolve run needed. All >=5 (7) attacks fully verified; none breaks the spec. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-derived the POST-PATCH decision of _check_list_display_item straight from the gold patch text (not the bundle's re-encoding) as a function of the six observations (callable(item)->is_invokable; hasattr(obj,item)->is_presenter_attr; get_field raises FieldDoesNotExist->structural_absent; isinstance(field,M2M)->structural_is_relation; getattr(obj.model,item) raises AttributeError->attribute_absent; isinstance(value,M2M)->attribute_is_relation; return list ->{0,108,109}). Compared against model.py's impl region VERBATIM over all 2^6=64 observation combinations: 0 mismatches. Also encoded the spec postconditions (A)-(D) + codomain {0,108,109} as an oracle and checked the model impl satisfies them on all 64: 0 violations. The spec is not too strong: relation flags are constrained ONLY on the exact paths the real code inspects the resolved object (structural_is_relation only when not structural_absent; attribute_is_relation only when structural_absent and not attribute_absent), so the abstract don't-cares never over-constrain relative to the real callee, and clause (B) makes E108 iff both lookups absent — matching the patch (structural lookup no longer gated behind hasattr(obj.model,item)). Short-circuit ordering (invokable, then presenter-attr, then structural, then attribute) matches. Model verifies under pinned Nagini (Verification successful, 10.67s, exit 0). G-AX re-run exit 0 (64 combos + F2P PositionField witness (F,F,F,F,T,F)->0 accepted). Bundle G-CONF ran 100016 real Django scenarios against the genuine patched routine with 0 disagreements. No diverging input exists between the modeled function and the real post-patch callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py) describes the behaviour of _check_list_display_item purely abstractly: a pure decision function check_display_item over four boolean observations (is_invokable, is_presenter_attr, structural_absent/is_relation, attribute_absent/is_relation) returning integer codes 0/108/109, with postconditions stating the ordering (structural lookup attempted first), the E108-IFF-both-absent condition, and that the ManyToManyField test applies to either resolved object. Every fact conveyed by the spec view is a strict SUBSET — and a more abstracted form — of what the PUBLIC problem_statement already discloses: the problem_statement includes the FULL corrected source of _check_list_display_item verbatim (the try/get_field/except FieldDoesNotExist/getattr/AttributeError/isinstance ManyToManyField structure), plus a 12-row truth table enumerating the exact input/output behaviour, plus the explicit rationale (remove the hasattr(obj.model,item) gate; emit E108 only when both lookups fail; hoist the M2M check). Thus the gold edit is already public in its entirety, and nothing in model.py's spec/proof region reveals the gold edit beyond that. The refinement.md/mapping.md quote patch.diff verbatim, but (a) those are audit-derivation docs, not the solver-facing spec view, and (b) the same content is already public in the problem_statement's suggested-patch code block. No spec-view line leaks gold specifics beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
