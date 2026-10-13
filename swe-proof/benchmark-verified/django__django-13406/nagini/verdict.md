# P2 adversarial audit — django__django-13406

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -98,7 +91,5 @@
                     rs.producer_tag == Old(rs.producer_tag)))
     # post-conditions-end
     # impl-start
-    if value.value_field_count > 0:
-        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
     rs.description = value
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -98,7 +91,7 @@
                     rs.producer_tag == Old(rs.producer_tag)))
     # post-conditions-end
     # impl-start
-    if value.value_field_count > 0:
+    if value.value_field_count > 1:
         rs.producer_tag = PRODUCES_VALUE_MAPPINGS
     rs.description = value
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -98,7 +91,6 @@
                     rs.producer_tag == Old(rs.producer_tag)))
     # post-conditions-end
     # impl-start
-    if value.value_field_count > 0:
-        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
+    rs.producer_tag = PRODUCES_VALUE_MAPPINGS
     rs.description = value
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -100,5 +93,4 @@
     # impl-start
     if value.value_field_count > 0:
         rs.producer_tag = PRODUCES_VALUE_MAPPINGS
-    rs.description = value
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -100,5 +93,7 @@
     # impl-start
     if value.value_field_count > 0:
         rs.producer_tag = PRODUCES_VALUE_MAPPINGS
+    else:
+        rs.producer_tag = PRODUCES_MODEL_INSTANCES
     rs.description = value
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -99,6 +92,6 @@
     # post-conditions-end
     # impl-start
     if value.value_field_count > 0:
-        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
+        rs.producer_tag = PRODUCES_MODEL_INSTANCES
     rs.description = value
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -98,7 +91,9 @@
                     rs.producer_tag == Old(rs.producer_tag)))
     # post-conditions-end
     # impl-start
-    if value.value_field_count > 0:
+    if not (value.value_field_count <= 0):
         rs.producer_tag = PRODUCES_VALUE_MAPPINGS
+    else:
+        rs.producer_tag = rs.producer_tag
     rs.description = value
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # row-producer tags
@@ -46,17 +45,12 @@
 class LookupDescription:
     def __init__(self, values_field_count: int) -> None:
         Requires(values_field_count >= 0)
-        # level 2 < attach_description's 6: leaves room beneath the caller, so a
-        # caller holding an obligation can construct a description.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
         self.value_field_count = values_field_count
 
 
 class ResultSet:
     def __init__(self, producer_tag: int) -> None:
-        # level 2 < attach_description's 6 (see LookupDescription.__init__).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
         Ensures(Acc(self.description) and self.description is None)  # type: ignore
         self.producer_tag = producer_tag
@@ -80,7 +74,6 @@
     Requires(Acc(rs.description))
     # the attached description is read, never mutated -> fractional permission.
     Requires(Acc(value.value_field_count, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rs.producer_tag))
@@ -98,7 +91,7 @@
                     rs.producer_tag == Old(rs.producer_tag)))
     # post-conditions-end
     # impl-start
+    rs.description = value
     if value.value_field_count > 0:
         rs.producer_tag = PRODUCES_VALUE_MAPPINGS
-    rs.description = value
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13406.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lazy result set carries a *row producer* that decides what shape each
  fetched row takes: either a full model instance, or a plain value mapping
  (one entry per selected value-field). A separately-built lookup description
  may be attached to a freshly-created result set. When such a lookup
  description is attached, the result set's row producer must agree with the
  KIND of lookup the description encodes:

    * if the description selects an explicit set of value-fields (it carries a
      non-empty value-field selection), the result set must produce value
      mappings — NOT model instances — once the description is attached;

    * if the description selects no value-fields, the result set keeps whatever
      row producer it already had.

  Attaching the description also stores it as the result set's active lookup
  description. The pinned observable: a freshly-created result set, which by
  default would produce model instances, must switch to producing value
  mappings exactly when the attached description carries a value-field
  selection — otherwise the fetched value rows are wrongly wrapped as model
  instances.

The lookup description is modelled as a minimal class carrying only the one
touched, read-only field: the count of selected value-fields (an ``int`` >= 0;
a non-empty selection <-> count > 0). The result set is modelled as a minimal
class carrying the two touched fields: an integer *row-producer tag*
(0 = produces model instances, 1 = produces value mappings) and the attached
lookup description (an ``Optional[LookupDescription]`` reference). No callee is
axiomatized: the attachment is a conditional attribute update over those tags.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# row-producer tags
PRODUCES_MODEL_INSTANCES = 0   # default producer (full model instances)
PRODUCES_VALUE_MAPPINGS = 1    # producer that yields one value mapping per row


class LookupDescription:
    def __init__(self, values_field_count: int) -> None:
        Requires(values_field_count >= 0)
        Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
        self.value_field_count = values_field_count


class ResultSet:
    def __init__(self, producer_tag: int) -> None:
        Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
        Ensures(Acc(self.description) and self.description is None)  # type: ignore
        self.producer_tag = producer_tag
        self.description = None  # type: Optional[LookupDescription]


# axioms-start
# (no callee is axiomatized: the attachment is a conditional attribute update
# over integer producer tags and the description's value-field count.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def attach_description(rs: ResultSet, value: LookupDescription) -> None:
    # pre-conditions-start
    Requires(Acc(rs.producer_tag))
    Requires(Acc(rs.description))
    # the attached description is read, never mutated -> fractional permission.
    Requires(Acc(value.value_field_count, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rs.producer_tag))
    Ensures(Acc(rs.description))
    Ensures(Acc(value.value_field_count, 1 / 2))
    # the description is now the result set's active lookup description.
    Ensures(rs.description is value)
    # the description carrying a value-field selection forces the value-mapping
    # producer; the count is read-only across the call.
    Ensures(value.value_field_count == Old(value.value_field_count))
    Ensures(Implies(value.value_field_count > 0,
                    rs.producer_tag == PRODUCES_VALUE_MAPPINGS))
    # no value-field selection -> the existing row producer is preserved.
    Ensures(Implies(value.value_field_count == 0,
                    rs.producer_tag == Old(rs.producer_tag)))
    # post-conditions-end
    # impl-start
    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    rs.description = value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Command form: `python -m swebench_unified.adversary weakness nagini django__django-13406 <atk>`; resolve via `swebench_unified.harness.run_resolve`.

Spec analysis: attach_description pins producer_tag as a TOTAL function of the input — Ensures(Implies(count>0, tag==PRODUCES_VALUE_MAPPINGS)) AND Ensures(Implies(count==0, tag==Old(tag))), plus Ensures(rs.description is value) and Ensures(value_field_count==Old) (read-only). The only impl-region degrees of freedom are the two observable fields (producer_tag, description), both fully pinned; no slack for a behaviourally-wrong verifying impl.

Attack results (all same-spec exit 0 first):
- atk_1 (prepatch: rs.description=value only, producer never switched) -> weakness exit 2 (rejected). PREPATCH REPRODUCED via discriminating clause Implies(count>0, tag==1).
- atk_2 (boundary off-by-one: count>1, misses count==1) -> exit 2 rejected.
- atk_3 (unconditional tag=1, breaks empty-branch Old preservation) -> exit 2 rejected.
- atk_4 (control-flow: switches tag but never stores description) -> exit 2 rejected.
- atk_5 (wrong else: forces PRODUCES_MODEL_INSTANCES on empty branch, breaks Old) -> exit 2 rejected.
- atk_6 (ungrounded-oracle echo: count>0 -> tag=PRODUCES_MODEL_INSTANCES, wrong constant) -> exit 2 rejected.
- atk_7 (behavioural echo: guard `not (value_field_count<=0)` == count>0, explicit no-op else tag=tag) -> weakness exit 0 CANDIDATE (verifies 10.9s). Faithful patch atk_7_patch.diff (same rephrased guard + no-op else on real QuerySet.query setter) RAN through run_resolve: resolved=True, completed=True; FAIL_TO_PASS 3/3 (test_annotation_values, test_annotation_values_list, test_annotation_with_callable_default), PASS_TO_PASS 32/32, patch_successfully_applied=True. RESOLVES -> not a weakness (correct echo).
- atk_8 (behavioural echo: store rs.description first, then conditional switch) -> weakness exit 0 CANDIDATE (verifies 10.7s). Faithful patch atk_8_patch.diff (store self._query first, then `if value.values_select: self._iterable_class=ValuesIterable`) RAN through run_resolve: resolved=True, completed=True; FAIL_TO_PASS 3/3, PASS_TO_PASS 32/32. RESOLVES -> not a weakness.

Positive control (gold impl, pos_control.py): VERIFIES (nagini_verify.sh exit 0, 10.4s) — spec non-vacuous.

refinement.md audit: legs A1-A6 are R / A-reference / I only. NO consumed axiom (model.py axioms region empty; no @ContractOnly). Section C 'no kind-3' holds. The single A-reference (bool(values_select) <-> count>0; ValuesIterable<->tag1; empty branch preserves prior producer; _query<->description) is exactly what axiom_check.py (G-AX) validates by running the real post-patch setter against an in-memory sqlite DB over every values()/values_list() flavour + 5000-tuple truthiness fuzz. Correspondence to the real callee holds; model impl maps 1:1 onto the gold hunk.

Both verifying candidates are behaviourally-correct echoes whose materialized faithful patches RESOLVE. No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13406.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lazy result set carries a *row producer* that decides what shape each
  fetched row takes: either a full model instance, or a plain value mapping
  (one entry per selected value-field). A separately-built lookup description
  may be attached to a freshly-created result set. When such a lookup
  description is attached, the result set's row producer must agree with the
  KIND of lookup the description encodes:

    * if the description selects an explicit set of value-fields (it carries a
      non-empty value-field selection), the result set must produce value
      mappings — NOT model instances — once the description is attached;

    * if the description selects no value-fields, the result set keeps whatever
      row producer it already had.

  Attaching the description also stores it as the result set's active lookup
  description. The pinned observable: a freshly-created result set, which by
  default would produce model instances, must switch to producing value
  mappings exactly when the attached description carries a value-field
  selection — otherwise the fetched value rows are wrongly wrapped as model
  instances.

The lookup description is modelled as a minimal class carrying only the one
touched, read-only field: the count of selected value-fields (an ``int`` >= 0;
a non-empty selection <-> count > 0). The result set is modelled as a minimal
class carrying the two touched fields: an integer *row-producer tag*
(0 = produces model instances, 1 = produces value mappings) and the attached
lookup description (an ``Optional[LookupDescription]`` reference). No callee is
axiomatized: the attachment is a conditional attribute update over those tags.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# row-producer tags
PRODUCES_MODEL_INSTANCES = 0   # default producer (full model instances)
PRODUCES_VALUE_MAPPINGS = 1    # producer that yields one value mapping per row


class LookupDescription:
    def __init__(self, values_field_count: int) -> None:
        Requires(values_field_count >= 0)
        Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
        self.value_field_count = values_field_count


class ResultSet:
    def __init__(self, producer_tag: int) -> None:
        Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
        Ensures(Acc(self.description) and self.description is None)  # type: ignore
        self.producer_tag = producer_tag
        self.description = None  # type: Optional[LookupDescription]


# axioms-start
# (no callee is axiomatized: the attachment is a conditional attribute update
# over integer producer tags and the description's value-field count.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def attach_description(rs: ResultSet, value: LookupDescription) -> None:
    # pre-conditions-start
    Requires(Acc(rs.producer_tag))
    Requires(Acc(rs.description))
    # the attached description is read, never mutated -> fractional permission.
    Requires(Acc(value.value_field_count, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rs.producer_tag))
    Ensures(Acc(rs.description))
    Ensures(Acc(value.value_field_count, 1 / 2))
    # the description is now the result set's active lookup description.
    Ensures(rs.description is value)
    # the description carrying a value-field selection forces the value-mapping
    # producer; the count is read-only across the call.
    Ensures(value.value_field_count == Old(value.value_field_count))
    Ensures(Implies(value.value_field_count > 0,
                    rs.producer_tag == PRODUCES_VALUE_MAPPINGS))
    # no value-field selection -> the existing row producer is preserved.
    Ensures(Implies(value.value_field_count == 0,
                    rs.producer_tag == Old(rs.producer_tag)))
    # post-conditions-end
    # impl-start
    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    rs.description = value
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Command form: `python -m swebench_unified.adversary weakness nagini django__django-13406 <atk>`; resolve via `swebench_unified.harness.run_resolve`.

Spec analysis: attach_description pins producer_tag as a TOTAL function of the input — Ensures(Implies(count>0, tag==PRODUCES_VALUE_MAPPINGS)) AND Ensures(Implies(count==0, tag==Old(tag))), plus Ensures(rs.description is value) and Ensures(value_field_count==Old) (read-only). The only impl-region degrees of freedom are the two observable fields (producer_tag, description), both fully pinned; no slack for a behaviourally-wrong verifying impl.

Attack results (all same-spec exit 0 first):
- atk_1 (prepatch: rs.description=value only, producer never switched) -> weakness exit 2 (rejected). PREPATCH REPRODUCED via discriminating clause Implies(count>0, tag==1).
- atk_2 (boundary off-by-one: count>1, misses count==1) -> exit 2 rejected.
- atk_3 (unconditional tag=1, breaks empty-branch Old preservation) -> exit 2 rejected.
- atk_4 (control-flow: switches tag but never stores description) -> exit 2 rejected.
- atk_5 (wrong else: forces PRODUCES_MODEL_INSTANCES on empty branch, breaks Old) -> exit 2 rejected.
- atk_6 (ungrounded-oracle echo: count>0 -> tag=PRODUCES_MODEL_INSTANCES, wrong constant) -> exit 2 rejected.
- atk_7 (behavioural echo: guard `not (value_field_count<=0)` == count>0, explicit no-op else tag=tag) -> weakness exit 0 CANDIDATE (verifies 10.9s). Faithful patch atk_7_patch.diff (same rephrased guard + no-op else on real QuerySet.query setter) RAN through run_resolve: resolved=True, completed=True; FAIL_TO_PASS 3/3 (test_annotation_values, test_annotation_values_list, test_annotation_with_callable_default), PASS_TO_PASS 32/32, patch_successfully_applied=True. RESOLVES -> not a weakness (correct echo).
- atk_8 (behavioural echo: store rs.description first, then conditional switch) -> weakness exit 0 CANDIDATE (verifies 10.7s). Faithful patch atk_8_patch.diff (store self._query first, then `if value.values_select: self._iterable_class=ValuesIterable`) RAN through run_resolve: resolved=True, completed=True; FAIL_TO_PASS 3/3, PASS_TO_PASS 32/32. RESOLVES -> not a weakness.

Positive control (gold impl, pos_control.py): VERIFIES (nagini_verify.sh exit 0, 10.4s) — spec non-vacuous.

refinement.md audit: legs A1-A6 are R / A-reference / I only. NO consumed axiom (model.py axioms region empty; no @ContractOnly). Section C 'no kind-3' holds. The single A-reference (bool(values_select) <-> count>0; ValuesIterable<->tag1; empty branch preserves prior producer; _query<->description) is exactly what axiom_check.py (G-AX) validates by running the real post-patch setter against an in-memory sqlite DB over every values()/values_list() flavour + 5000-tuple truthiness fuzz. Correspondence to the real callee holds; model impl maps 1:1 onto the gold hunk.

Both verifying candidates are behaviourally-correct echoes whose materialized faithful patches RESOLVE. No verifying wrong impl exists whose faithful patch fails to resolve. verify => correct. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the modeled attach_description against the real QuerySet.query setter (django/db/models/query.py:202-206 @ base 84609b3) verified.

Real setter (post-patch):
    @query.setter
    def query(self, value):
        if value.values_select:
            self._iterable_class = ValuesIterable
        self._query = value

Model impl:
    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS   # =1
    rs.description = value

Correspondence checked for divergence on every branch:
1. Guard: real `if value.values_select:` tests tuple non-emptiness; `bool(tuple) == (len>0)`. Model carries the tuple only by its count and guards `count > 0`. The setter inspects ONLY truthiness (never the field-name chars), so count is a lossless carrier of the observable. Faithful.
2. Value-bearing branch: real writes `_iterable_class = ValuesIterable` unconditionally (collapsing even values_list flavours to ValuesIterable); model writes tag 1. Under the §2 bijection ValuesIterable↔1. Faithful — no over-strength: the setter really does force the value-mapping producer for every value-bearing query.
3. Empty branch: real leaves `_iterable_class` untouched; model preserves Old(producer_tag). For a fresh QuerySet default ModelIterable(tag 0) it stays 0. Faithful.
4. Store: real `self._query = value` (identity); model `rs.description is value`. Faithful.

Potential divergence points probed and cleared:
- values() with NO args: set_values(fields=()) (sql/query.py:2156) still assigns values_select = tuple(all concrete field names) — NON-empty (count>0) — so it still produces dicts; guard fires. No divergence.
- values_list()/flat/named/annotate GROUP-BY: all route through _values→set_values, all set non-empty values_select. No divergence.
- values_select default is () (sql/query.py:203) → count 0 for plain all()/filter()/order_by(). No divergence.

Model verifies (nagini_verify exit 0, 9.6s); model_prepatch fails exactly the discriminating clause Implies(count>0, tag==VALUE_MAPPINGS), isolating the fixed behavior. same-spec confirms spec region identity. axiom_check A-reference (tuple-truthiness fuzz) confirmed; Django-in-container observations SKIP locally only for missing asgiref (env guard), not a spec issue.

No input on which the modeled function disagrees with the real callee was found. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (the pickled-query values()/values_list() crash: recreating a queryset from a pickled query wrongly returns model instances instead of dicts). The consumer spec view (spec_view over model.py) ELIDES the impl region ('...  # implementation elided — supplied by the consumer'), so the gold edit itself is never shown. Mechanical G-LEAK screen passes (leakage.screen: no hard failures; meta G-LEAK=pass, relaxed_leakage unset). Semantic review confirms: (1) all repo symbols are abstracted to neutral names — QuerySet.query setter->attach_description, _iterable_class->producer_tag, ValuesIterable->PRODUCES_VALUE_MAPPINGS, values_select->value_field_count; no patched file path (django/db/models/query.py), module path, or diff markers appear. (2) The behavioral spec ('a non-empty value-field selection must produce value mappings NOT model instances; empty selection preserves the existing producer') restates the public issue's own observation (prices2[0] is a Toy model instance when it should be a dict) framed as desired behavior, not as an edit or a bug/fix narration. (3) Narration screen clean: docstring says 'wrongly wrapped'/'wrong shape' which the token screen does not flag ('wrongly' != word-boundary 'wrong'), and no bug/fix/patch/previously terms leak the edit. The postcondition Implies(value_field_count>0, producer_tag==PRODUCES_VALUE_MAPPINGS) pins exactly the property the public problem statement already exposes, not a hidden edit location or mechanism. No line reveals the gold discriminator beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
