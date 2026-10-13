# P2 adversarial audit — django__django-11740

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,16 +33,10 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FieldDef:
     def __init__(self, is_relation: bool) -> None:
-        # Level 2 leaves room beneath any obligated caller (the modeled function
-        # is at 6) so a caller that constructs a FieldDef can hand its
-        # unsatisfied obligation down: this body is straight-line, no loop, no
-        # call, so it terminates unconditionally.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
         self.is_relation = is_relation  # type: bool
 
@@ -72,7 +66,6 @@
 def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(new_field.is_relation, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(new_field.is_relation, 1 / 2))
@@ -87,7 +80,5 @@
     # post-conditions-end
     # impl-start
     dependencies = PSeq()  # type: PSeq[int]
-    if new_field.is_relation:
-        dependencies = dependencies + fk_dependencies(new_field)
     return dependencies
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,16 +33,10 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FieldDef:
     def __init__(self, is_relation: bool) -> None:
-        # Level 2 leaves room beneath any obligated caller (the modeled function
-        # is at 6) so a caller that constructs a FieldDef can hand its
-        # unsatisfied obligation down: this body is straight-line, no loop, no
-        # call, so it terminates unconditionally.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
         self.is_relation = is_relation  # type: bool
 
@@ -72,7 +66,6 @@
 def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(new_field.is_relation, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(new_field.is_relation, 1 / 2))
@@ -86,8 +79,5 @@
     Ensures(Implies(not new_field.is_relation, len(Result()) == 0))
     # post-conditions-end
     # impl-start
-    dependencies = PSeq()  # type: PSeq[int]
-    if new_field.is_relation:
-        dependencies = dependencies + fk_dependencies(new_field)
-    return dependencies
+    return fk_dependencies(new_field)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,16 +33,10 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FieldDef:
     def __init__(self, is_relation: bool) -> None:
-        # Level 2 leaves room beneath any obligated caller (the modeled function
-        # is at 6) so a caller that constructs a FieldDef can hand its
-        # unsatisfied obligation down: this body is straight-line, no loop, no
-        # call, so it terminates unconditionally.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
         self.is_relation = is_relation  # type: bool
 
@@ -72,7 +66,6 @@
 def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(new_field.is_relation, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(new_field.is_relation, 1 / 2))
@@ -88,6 +81,6 @@
     # impl-start
     dependencies = PSeq()  # type: PSeq[int]
     if new_field.is_relation:
-        dependencies = dependencies + fk_dependencies(new_field)
+        dependencies = PSeq(0)
     return dependencies
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,16 +33,10 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FieldDef:
     def __init__(self, is_relation: bool) -> None:
-        # Level 2 leaves room beneath any obligated caller (the modeled function
-        # is at 6) so a caller that constructs a FieldDef can hand its
-        # unsatisfied obligation down: this body is straight-line, no loop, no
-        # call, so it terminates unconditionally.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
         self.is_relation = is_relation  # type: bool
 
@@ -72,7 +66,6 @@
 def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(new_field.is_relation, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(new_field.is_relation, 1 / 2))
@@ -87,7 +80,7 @@
     # post-conditions-end
     # impl-start
     dependencies = PSeq()  # type: PSeq[int]
-    if new_field.is_relation:
+    if not new_field.is_relation:
         dependencies = dependencies + fk_dependencies(new_field)
     return dependencies
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,16 +33,10 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FieldDef:
     def __init__(self, is_relation: bool) -> None:
-        # Level 2 leaves room beneath any obligated caller (the modeled function
-        # is at 6) so a caller that constructs a FieldDef can hand its
-        # unsatisfied obligation down: this body is straight-line, no loop, no
-        # call, so it terminates unconditionally.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
         self.is_relation = is_relation  # type: bool
 
@@ -72,7 +66,6 @@
 def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(new_field.is_relation, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(new_field.is_relation, 1 / 2))
@@ -88,6 +81,6 @@
     # impl-start
     dependencies = PSeq()  # type: PSeq[int]
     if new_field.is_relation:
-        dependencies = dependencies + fk_dependencies(new_field)
+        dependencies = dependencies + fk_dependencies(new_field) + fk_dependencies(new_field)
     return dependencies
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,16 +33,10 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FieldDef:
     def __init__(self, is_relation: bool) -> None:
-        # Level 2 leaves room beneath any obligated caller (the modeled function
-        # is at 6) so a caller that constructs a FieldDef can hand its
-        # unsatisfied obligation down: this body is straight-line, no loop, no
-        # call, so it terminates unconditionally.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
         self.is_relation = is_relation  # type: bool
 
@@ -72,7 +66,6 @@
 def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(new_field.is_relation, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(new_field.is_relation, 1 / 2))
@@ -89,5 +82,7 @@
     dependencies = PSeq()  # type: PSeq[int]
     if new_field.is_relation:
         dependencies = dependencies + fk_dependencies(new_field)
+    else:
+        dependencies = PSeq(0)
     return dependencies
     # impl-end
```

Attack 7 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,16 +33,10 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class FieldDef:
     def __init__(self, is_relation: bool) -> None:
-        # Level 2 leaves room beneath any obligated caller (the modeled function
-        # is at 6) so a caller that constructs a FieldDef can hand its
-        # unsatisfied obligation down: this body is straight-line, no loop, no
-        # call, so it terminates unconditionally.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
         self.is_relation = is_relation  # type: bool
 
@@ -72,7 +66,6 @@
 def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
     # pre-conditions-start
     Requires(Acc(new_field.is_relation, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(new_field.is_relation, 1 / 2))
@@ -86,8 +79,8 @@
     Ensures(Implies(not new_field.is_relation, len(Result()) == 0))
     # post-conditions-end
     # impl-start
-    dependencies = PSeq()  # type: PSeq[int]
+    empty = PSeq()  # type: PSeq[int]
     if new_field.is_relation:
-        dependencies = dependencies + fk_dependencies(new_field)
-    return dependencies
+        return fk_dependencies(new_field)
+    return empty
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11740.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An altered-field operation is emitted whenever a model field's definition
  changes. The operation carries a list of ordering dependencies that the
  migration planner needs in order to apply the change in a valid order.

  When the field's NEW definition points at another model (it is a relational
  field — it names a target model it must be able to resolve), the emitted
  operation MUST carry the ordering dependencies that make the target model's
  schema available first. Those dependencies are exactly the relational
  dependencies of the new field definition, and there is always at least one
  of them (the dependency on the referenced model itself). When the new field
  definition does NOT point at another model, the operation carries no such
  dependency and its dependency list is empty.

  In other words: the dependency list attached to the altered-field operation
  is the field's relational dependencies when the new definition is relational,
  and empty otherwise. It must NOT be unconditionally empty — an operation that
  changes a plain field into one referencing another model and yet declares no
  dependency on that model cannot be ordered correctly.

The field definition is modelled by a minimal carrier exposing only the touched
property — whether its new definition references another model (``is_relation``).
The relational-dependency computation for a referencing field is an unchanged
helper, axiomatized as a pure decision returning a non-empty dependency
sequence. Dependency tuples are modelled as opaque ``int`` codes; the
specification is carried over ``PSeq[int]`` (the dependency list), for which the
load-bearing observable is which dependencies are present, in particular whether
the list is non-empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class FieldDef:
    def __init__(self, is_relation: bool) -> None:
        Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
        self.is_relation = is_relation  # type: bool


# axioms-start
@Pure
@ContractOnly
def fk_dependencies(field: FieldDef) -> PSeq[int]:
    """The unchanged helper that computes the ordering dependencies of a field
    definition that references another model. It always yields at least one
    dependency — the dependency on the referenced model itself is emitted
    unconditionally — so the returned sequence is non-empty. Pure decision over
    the field definition; provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(Acc(field.is_relation, 1 / 4))
    Requires(field.is_relation)
    Ensures(len(Result()) > 0)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(new_field.is_relation, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(new_field.is_relation, 1 / 2))
    # When the new definition references another model, the operation carries
    # exactly that field's relational dependencies — which are non-empty, so
    # the target model is depended upon (NOT an unconditionally empty list).
    Ensures(Implies(new_field.is_relation,
                    Result() == fk_dependencies(new_field) and len(Result()) > 0))
    # When the new definition references no model, the operation carries no
    # ordering dependency.
    Ensures(Implies(not new_field.is_relation, len(Result()) == 0))
    # post-conditions-end
    # impl-start
    dependencies = PSeq()  # type: PSeq[int]
    if new_field.is_relation:
        dependencies = dependencies + fk_dependencies(new_field)
    return dependencies
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Positive control (bundle model.py copy) VERIFIES (7.6s). Prepatch bug reproduced as atk_1 (dependencies unconditionally empty): same-spec exit 0, weakness exit 2 — FAILS relational postcondition Implies(is_relation, Result()==fk_dependencies AND len>0). 7 attacks built (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical; all same-spec exit 0).

WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-11740 <atk>): atk_1 (prepatch: unconditionally empty) exit 2; atk_2 (control-flow: always return fk_dependencies, ignoring guard) exit 2 — fk_dependencies precondition field.is_relation might not hold; atk_3 (boundary: relational returns hardcoded PSeq(0) len>0 but != fk_dependencies) exit 2 — relational postcondition Result()==fk_dependencies fails; atk_4 (swapped guard: extend only when NOT relational) exit 2 — fk_dependencies precondition fails; atk_5 (extra element: fk_dependencies + fk_dependencies) exit 2 — Result()==fk_dependencies fails; atk_6 (ungrounded/spurious: non-relational returns PSeq(0)) exit 2 — non-relational postcondition len==0 fails. All 6 wrong impls rejected for GENUINE SEMANTIC reasons (postcondition/precondition), confirmed via direct nagini_verify.sh (not translation artifacts).

CANDIDATE: atk_echo (behaviorally-equivalent restructuring — early return fk_dependencies when relational, else typed empty PSeq) shares spec AND VERIFIES (7.2s) => weakness exit 0 CANDIDATE. Per protocol materialized its faithful refined patch (atk_echo.patch: if/else seeding of dependencies + dependencies=dependencies on AlterField add_operation), validated it applies cleanly to autodetector.py at base_commit 003bb34b (patch -p1 --dry-run exit 0 against extracted base file), then RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-11740', patch, timeout=1800) => RESOLVED: True. The one verifying wrong-restructuring impl RESOLVES, so verify does NOT imply incorrect here — no spec break.

SPEC TIGHTNESS: postcondition fully pins Result() in both branches (== fk_dependencies(new_field) AND len>0 when is_relation; len==0 otherwise), leaving no room for a semantically-wrong verifying impl. Every falsification attempt across partial-domain, boundary, control-flow-effect, extra-element, and ungrounded-oracle-echo classes was rejected.

REFINEMENT.MD AUDIT: 5 legs. #1 R (FieldDef.is_relation <-> relation guard), #2 I+R (empty init), #3 R (guard), #5 R (stored _auto_deps <-> Result()) — R/I legs (G-CONF territory). #4 A-consumed: fk_dependencies axiom Ensures(len>0) is the WEAKEST contract needed, maps to unchanged callee _get_dependencies_for_foreign_key (autodetector.py:1060), which emits [(app,obj,None,True)] before any optional append => non-empty unconditionally; axiom_check.py validates over 6 relational shapes (FK cross-app, FK same-app, O2O, m2m auto, m2m explicit-through, swappable). NO A-reference leg, NO kind-3 (unexpressible-changed-op) step — the behavioral delta is modeled DEEPLY in the impl (control flow + relation-keyed emptiness), not hidden behind the axiom. A-leg correspondence to the real callee holds. axiom_check.py runs under G-AX in the Docker eval container (django absent on host, expected).

VERDICT: SOUND. >=5 distinct wrong impls run (6 wrong + prepatch), all rejected for semantic reasons; the sole verifying same-spec candidate's faithful patch RESOLVES under run_resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11740.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An altered-field operation is emitted whenever a model field's definition
  changes. The operation carries a list of ordering dependencies that the
  migration planner needs in order to apply the change in a valid order.

  When the field's NEW definition points at another model (it is a relational
  field — it names a target model it must be able to resolve), the emitted
  operation MUST carry the ordering dependencies that make the target model's
  schema available first. Those dependencies are exactly the relational
  dependencies of the new field definition, and there is always at least one
  of them (the dependency on the referenced model itself). When the new field
  definition does NOT point at another model, the operation carries no such
  dependency and its dependency list is empty.

  In other words: the dependency list attached to the altered-field operation
  is the field's relational dependencies when the new definition is relational,
  and empty otherwise. It must NOT be unconditionally empty — an operation that
  changes a plain field into one referencing another model and yet declares no
  dependency on that model cannot be ordered correctly.

The field definition is modelled by a minimal carrier exposing only the touched
property — whether its new definition references another model (``is_relation``).
The relational-dependency computation for a referencing field is an unchanged
helper, axiomatized as a pure decision returning a non-empty dependency
sequence. Dependency tuples are modelled as opaque ``int`` codes; the
specification is carried over ``PSeq[int]`` (the dependency list), for which the
load-bearing observable is which dependencies are present, in particular whether
the list is non-empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class FieldDef:
    def __init__(self, is_relation: bool) -> None:
        Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
        self.is_relation = is_relation  # type: bool


# axioms-start
@Pure
@ContractOnly
def fk_dependencies(field: FieldDef) -> PSeq[int]:
    """The unchanged helper that computes the ordering dependencies of a field
    definition that references another model. It always yields at least one
    dependency — the dependency on the referenced model itself is emitted
    unconditionally — so the returned sequence is non-empty. Pure decision over
    the field definition; provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(Acc(field.is_relation, 1 / 4))
    Requires(field.is_relation)
    Ensures(len(Result()) > 0)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(new_field.is_relation, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(new_field.is_relation, 1 / 2))
    # When the new definition references another model, the operation carries
    # exactly that field's relational dependencies — which are non-empty, so
    # the target model is depended upon (NOT an unconditionally empty list).
    Ensures(Implies(new_field.is_relation,
                    Result() == fk_dependencies(new_field) and len(Result()) > 0))
    # When the new definition references no model, the operation carries no
    # ordering dependency.
    Ensures(Implies(not new_field.is_relation, len(Result()) == 0))
    # post-conditions-end
    # impl-start
    dependencies = PSeq()  # type: PSeq[int]
    if new_field.is_relation:
        dependencies = dependencies + fk_dependencies(new_field)
    return dependencies
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Positive control (bundle model.py copy) VERIFIES (7.6s). Prepatch bug reproduced as atk_1 (dependencies unconditionally empty): same-spec exit 0, weakness exit 2 — FAILS relational postcondition Implies(is_relation, Result()==fk_dependencies AND len>0). 7 attacks built (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical; all same-spec exit 0).

WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-11740 <atk>): atk_1 (prepatch: unconditionally empty) exit 2; atk_2 (control-flow: always return fk_dependencies, ignoring guard) exit 2 — fk_dependencies precondition field.is_relation might not hold; atk_3 (boundary: relational returns hardcoded PSeq(0) len>0 but != fk_dependencies) exit 2 — relational postcondition Result()==fk_dependencies fails; atk_4 (swapped guard: extend only when NOT relational) exit 2 — fk_dependencies precondition fails; atk_5 (extra element: fk_dependencies + fk_dependencies) exit 2 — Result()==fk_dependencies fails; atk_6 (ungrounded/spurious: non-relational returns PSeq(0)) exit 2 — non-relational postcondition len==0 fails. All 6 wrong impls rejected for GENUINE SEMANTIC reasons (postcondition/precondition), confirmed via direct nagini_verify.sh (not translation artifacts).

CANDIDATE: atk_echo (behaviorally-equivalent restructuring — early return fk_dependencies when relational, else typed empty PSeq) shares spec AND VERIFIES (7.2s) => weakness exit 0 CANDIDATE. Per protocol materialized its faithful refined patch (atk_echo.patch: if/else seeding of dependencies + dependencies=dependencies on AlterField add_operation), validated it applies cleanly to autodetector.py at base_commit 003bb34b (patch -p1 --dry-run exit 0 against extracted base file), then RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-11740', patch, timeout=1800) => RESOLVED: True. The one verifying wrong-restructuring impl RESOLVES, so verify does NOT imply incorrect here — no spec break.

SPEC TIGHTNESS: postcondition fully pins Result() in both branches (== fk_dependencies(new_field) AND len>0 when is_relation; len==0 otherwise), leaving no room for a semantically-wrong verifying impl. Every falsification attempt across partial-domain, boundary, control-flow-effect, extra-element, and ungrounded-oracle-echo classes was rejected.

REFINEMENT.MD AUDIT: 5 legs. #1 R (FieldDef.is_relation <-> relation guard), #2 I+R (empty init), #3 R (guard), #5 R (stored _auto_deps <-> Result()) — R/I legs (G-CONF territory). #4 A-consumed: fk_dependencies axiom Ensures(len>0) is the WEAKEST contract needed, maps to unchanged callee _get_dependencies_for_foreign_key (autodetector.py:1060), which emits [(app,obj,None,True)] before any optional append => non-empty unconditionally; axiom_check.py validates over 6 relational shapes (FK cross-app, FK same-app, O2O, m2m auto, m2m explicit-through, swappable). NO A-reference leg, NO kind-3 (unexpressible-changed-op) step — the behavioral delta is modeled DEEPLY in the impl (control flow + relation-keyed emptiness), not hidden behind the axiom. A-leg correspondence to the real callee holds. axiom_check.py runs under G-AX in the Docker eval container (django absent on host, expected).

VERDICT: SOUND. >=5 distinct wrong impls run (6 wrong + prepatch), all rejected for semantic reasons; the sole verifying same-spec candidate's faithful patch RESOLVES under run_resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same-spec on model_prepatch.py exits 0; markers.same_spec confirmed). Model verifies under pinned Nagini. Modeled function altered_field_dependencies(new_field) abstracts the `dependencies` list attached to the emitted AlterField in generate_altered_fields (django/db/migrations/autodetector.py:904, base_commit 003bb34b21).

Real callee vs spec, verified against the worktrees:
- Patched generate_altered_fields seeds dependencies=[]; under the relation guard `hasattr(new_field,'remote_field') and getattr(new_field.remote_field,'model',None)` it does dependencies.extend(self._get_dependencies_for_foreign_key(new_field)). The subsequent `remote_field.through` block (autodetector.py:943-951) only reassigns new_field.remote_field.through and adds NOTHING to dependencies. dependencies then flows verbatim into add_operation(...) as operation._auto_deps.
- Relational case: real value = [] + _get_dependencies_for_foreign_key(new_field) = exactly fk_dependencies(new_field), non-empty. Spec: Implies(is_relation, Result()==fk_dependencies(new_field) and len(Result())>0). AGREES.
- Non-relational case: dependencies stays []. Spec: Implies(not is_relation, len(Result())==0). AGREES.
- Abstraction is_relation <-> (remote_field.model truthy) is precisely the guard the patch extends; no other new_field attribute affects the dependency value (deps modeled as opaque int codes; load-bearing observable = non-emptiness).

The len(Result())>0 postcondition is NOT over-strong: G-AX (axiom_check.py over 6 relational field shapes) confirms _get_dependencies_for_foreign_key unconditionally seeds a one-element list `[(dep_app_label, dep_object_name, None, True)]` before any optional through-append, so len>0 is an invariant of the real (verified) helper, not an added constraint. The non-relational clause pins the spec so a wrong impl cannot pass by emitting dependencies unconditionally (prepatch, unconditionally empty PSeq, fails the relational postcondition — intended G-DIFF discriminator matching F2P test_alter_field_to_fk_dependency_other_app).

The recorded G-EQ fail (atk_7) is an echo-shaped candidate (same spec; impl `if is_relation: return fk_dependencies(new_field); return PSeq()`; 'verifies but patch does not resolve') — a G-EQ patch-materialization/resolve artifact, not a faithfulness/drift signal. It does not indicate the spec disagrees with the real callee.

No diverging input exists; spec neither too strong nor drifting from real repo behavior. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the projected consumer spec view (regenerated via markers.spec_view) for gold-reconstruction leakage beyond the PUBLIC problem_statement (hints_text excluded). Mechanical G-LEAK screen re-run: PASSED, 0 hard failures. Spec is byte-identical with model_prepatch.py (same_spec=True), confirming the audited spec view.

Gold edit (django/db/migrations/autodetector.py, generate_altered_fields): seed `dependencies = []`, `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` under the relation guard, and pass `dependencies=dependencies` into the emitted AlterField op.

Leak checks on the spec view:
- No diff markers, no patched file path (django/db/migrations/autodetector.py absent), no patched dotted module path.
- The only distinctive changed repo symbol, `generate_altered_fields`, does NOT appear in the spec view. The gold helper `_get_dependencies_for_foreign_key` is abstracted to the generic name `fk_dependencies`; `add_operation`/`AlterField` are not named. These mechanism specifics originate in hints_text/refinement.md/mapping.md, which are out of the consumer-spec-view scope and are not public — and none are echoed in the spec view regardless.
- No bug/fix/pre-patch/regression narration in any spec-view comment/docstring; the docstring explicitly frames behaviour 'as desired behaviour, not as an edit'.

Semantic reconstruction: the spec states that an altered-field operation must carry the new field's (non-empty) relational dependencies when the new definition references another model, and empty otherwise. That is exactly the behavior the PUBLIC problem_statement already discloses: the reporter shows changing a UUIDField into ForeignKey(App2) yields a migration with no dependency on App2 and states 'the correct solution will be create dependency for App2.' The implementation-localization detail (which method, the seed-list-and-extend mechanics, the specific helper call) lives only in the elided impl region and does not surface in the spec view. No leakage beyond the problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
