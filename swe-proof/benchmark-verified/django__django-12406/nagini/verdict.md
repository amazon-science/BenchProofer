# P2 adversarial audit — django__django-12406

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_8.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # it carries full permission. The classification/permission inputs are
     # plain booleans (already-computed by the unchanged base initialiser).
     Requires(Acc(field.placeholder))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.placeholder))
@@ -91,7 +89,7 @@
                     and field.placeholder == placeholder_label))
     # post-conditions-end
     # impl-start
-    if (required and initial_present) or (is_radio and not blank):
+    if required and initial_present:
         field.placeholder = None
     else:
         field.placeholder = placeholder_label
@@ -100,7 +98,6 @@
 
 def derived_field_emptiness_flag(model_blank: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The emptiness-permission flag forwarded to the derived field is exactly
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # it carries full permission. The classification/permission inputs are
     # plain booleans (already-computed by the unchanged base initialiser).
     Requires(Acc(field.placeholder))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.placeholder))
@@ -100,7 +98,6 @@
 
 def derived_field_emptiness_flag(model_blank: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The emptiness-permission flag forwarded to the derived field is exactly
@@ -108,5 +105,5 @@
     Ensures(Result() == model_blank)
     # post-conditions-end
     # impl-start
-    return model_blank
+    return False
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # it carries full permission. The classification/permission inputs are
     # plain booleans (already-computed by the unchanged base initialiser).
     Requires(Acc(field.placeholder))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.placeholder))
@@ -91,7 +89,7 @@
                     and field.placeholder == placeholder_label))
     # post-conditions-end
     # impl-start
-    if (required and initial_present) or (is_radio and not blank):
+    if (required and initial_present) and (is_radio and not blank):
         field.placeholder = None
     else:
         field.placeholder = placeholder_label
@@ -100,7 +98,6 @@
 
 def derived_field_emptiness_flag(model_blank: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The emptiness-permission flag forwarded to the derived field is exactly
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # it carries full permission. The classification/permission inputs are
     # plain booleans (already-computed by the unchanged base initialiser).
     Requires(Acc(field.placeholder))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.placeholder))
@@ -94,13 +92,12 @@
     if (required and initial_present) or (is_radio and not blank):
         field.placeholder = None
     else:
-        field.placeholder = placeholder_label
+        field.placeholder = placeholder_label + 1
     # impl-end
 
 
 def derived_field_emptiness_flag(model_blank: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The emptiness-permission flag forwarded to the derived field is exactly
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # it carries full permission. The classification/permission inputs are
     # plain booleans (already-computed by the unchanged base initialiser).
     Requires(Acc(field.placeholder))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.placeholder))
@@ -91,16 +89,12 @@
                     and field.placeholder == placeholder_label))
     # post-conditions-end
     # impl-start
-    if (required and initial_present) or (is_radio and not blank):
-        field.placeholder = None
-    else:
-        field.placeholder = placeholder_label
+    field.placeholder = placeholder_label
     # impl-end
 
 
 def derived_field_emptiness_flag(model_blank: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The emptiness-permission flag forwarded to the derived field is exactly
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # it carries full permission. The classification/permission inputs are
     # plain booleans (already-computed by the unchanged base initialiser).
     Requires(Acc(field.placeholder))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.placeholder))
@@ -91,7 +89,7 @@
                     and field.placeholder == placeholder_label))
     # post-conditions-end
     # impl-start
-    if (required and initial_present) or (is_radio and not blank):
+    if (required and initial_present) or (is_radio and blank):
         field.placeholder = None
     else:
         field.placeholder = placeholder_label
@@ -100,7 +98,6 @@
 
 def derived_field_emptiness_flag(model_blank: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The emptiness-permission flag forwarded to the derived field is exactly
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -75,7 +74,6 @@
     # it carries full permission. The classification/permission inputs are
     # plain booleans (already-computed by the unchanged base initialiser).
     Requires(Acc(field.placeholder))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.placeholder))
@@ -100,7 +98,6 @@
 
 def derived_field_emptiness_flag(model_blank: bool) -> bool:
     # pre-conditions-start
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # The emptiness-permission flag forwarded to the derived field is exactly
@@ -108,5 +105,5 @@
     Ensures(Result() == model_blank)
     # post-conditions-end
     # impl-start
-    return model_blank
+    return not model_blank
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.py`

```python
"""Twin-artifact model for django__django-12406.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A model-backed single-choice field offers a leading blank placeholder
      choice exactly when an unfilled selection is a meaningful option. The
      placeholder is suppressed in two situations and offered otherwise:

        * it is suppressed when the field is mandatory AND already carries a
          pre-filled value (an empty selection would contradict the pre-fill);

        * it is ALSO suppressed when the field is rendered with a presentation
          whose unselected state is itself a visible choice (a one-of radio
          presentation) AND an empty selection is not a permitted value for
          the underlying data — because then the placeholder would masquerade
          as a genuine selectable value.

      In every other case the placeholder is offered. Whether the placeholder
      is offered is observable as: the field's choice sequence begins with a
      blank-keyed entry iff the placeholder is offered.

  (2) When such a field is derived for a related-object reference, the
      permission-to-leave-empty flag that the data layer records for that
      reference is forwarded to the field unchanged, so situation (1)'s second
      clause is decided by the data layer's own emptiness permission, not by a
      hard-coded default.

The placeholder label is modelled as an ``Optional[int]`` carrier: ``None``
means "no placeholder choice" and a present integer code means "placeholder
choice offered" (its concrete content is irrelevant to the tested behaviour).
The presentation classification (is the unselected state a visible choice) and
the emptiness-permission flag are booleans. No library callee is consumed as an
axiom: the decision is pure boolean/structure logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The placeholder-suppression decision and the
# permission-flag forwarding are pure boolean logic, modelled deeply. The base
# initialiser that normalises the presentation object (so its classification is
# well-defined) is an unchanged callee whose only observed effect here — that
# the presentation classification is available afterwards — is validated
# out-of-band by axiom_check.py (G-AX) as an A-reference, not consumed.
# axioms-end


# pure-start
@Pure
def placeholder_offered(required: bool, initial_present: bool,
                        is_radio: bool, blank: bool) -> bool:
    """The blank placeholder choice is offered iff NEITHER suppression
    situation holds: not (mandatory with a pre-filled value) AND not (a radio
    presentation whose empty state is not a permitted value)."""
    return not ((required and initial_present) or (is_radio and not blank))
# pure-end


class ChoiceFieldState:
    def __init__(self) -> None:
        Ensures(Acc(self.placeholder))  # type: ignore
        Ensures(self.placeholder is None)  # type: ignore
        self.placeholder = None  # type: Optional[int]


def configure_placeholder(field: ChoiceFieldState, placeholder_label: int,
                          required: bool, initial_present: bool,
                          is_radio: bool, blank: bool) -> None:
    # pre-conditions-start
    # The field object is genuinely mutated (its placeholder label is set), so
    # it carries full permission. The classification/permission inputs are
    # plain booleans (already-computed by the unchanged base initialiser).
    Requires(Acc(field.placeholder))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.placeholder))
    # The placeholder is OFFERED iff neither suppression situation holds; when
    # offered the field carries a present label, otherwise it carries none.
    Ensures(field.placeholder is not None
            if placeholder_offered(required, initial_present, is_radio, blank)
            else field.placeholder is None)
    # When offered, the carried label is exactly the supplied candidate label
    # (the placeholder is not replaced by some unrelated value).
    Ensures(Implies(placeholder_offered(required, initial_present, is_radio, blank),
                    field.placeholder is not None
                    and field.placeholder == placeholder_label))
    # post-conditions-end
    # impl-start
    if (required and initial_present) or (is_radio and not blank):
        field.placeholder = None
    else:
        field.placeholder = placeholder_label
    # impl-end


def derived_field_emptiness_flag(model_blank: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The emptiness-permission flag forwarded to the derived field is exactly
    # the data layer's recorded flag for the reference (forwarded unchanged).
    Ensures(Result() == model_blank)
    # post-conditions-end
    # impl-start
    return model_blank
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-12406 (nagini). adversary run under env swebench-lean.

SPEC SHAPE (why it is tight): configure_placeholder carries a TOTAL postcondition set that fully pins field.placeholder as a function of inputs — (a) present iff placeholder_offered(required,initial_present,is_radio,blank), else None; (b) when present, == placeholder_label exactly. derived_field_emptiness_flag carries Result()==model_blank. Both leave zero slack; placeholder_offered is a @Pure deep model, no @ContractOnly axioms.

ATTACKS (all built by copying model.py and editing ONLY the impl region; same-spec confirmed on atk_1 => exit 0 SAME; spec/axiom/@Pure/Requires/Ensures byte-identical). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12406 <path>`.
  atk_1 prepatch site-1 (drop radio suppression clause, `if required and initial_present`) => exit 2 NOT-A-COUNTEREXAMPLE (fails postcond on is_radio&not blank). PREPATCH BUG 1 REPRODUCED.
  atk_2 prepatch site-2 (`return False`) => exit 2 (fails Result()==model_blank when model_blank True). PREPATCH BUG 2 REPRODUCED.
  atk_3 boundary: `or`->`and` between the two suppression clauses => exit 2.
  atk_4 wrong carried value: `placeholder_label + 1` when offered (violates ==placeholder_label) => exit 2.
  atk_5 control-flow-effect: always `field.placeholder = placeholder_label` (never None) => exit 2.
  atk_6 ungrounded-oracle echo: drop `not` on blank (`is_radio and blank`) => exit 2.
  atk_7 partial-domain: `return not model_blank` => exit 2.
  atk_8 POSITIVE CONTROL = byte-identical gold impl => weakness exit 0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 11.5s), confirming the harness path and that the gold impl verifies.

No NON-gold wrong impl verified => there is NO verifying candidate whose faithful refined patch could be run through run_resolve; the resolve leg is vacuous here (patches={}) because the only CANDIDATE is the gold impl itself, whose refined patch is patch.diff (resolves by construction, G-RESOLVE). Attacks run in batches of 3 as concurrent background jobs (each Nagini check = JVM+Z3); all completed, none broke the spec.

REFINEMENT.MD A-LEG AUDIT: every leg is R (A1,A2,B1), A-reference (A3), or I (A4,A5,B2) — no A-consumed, no kind-3, no @ContractOnly axioms (consistent with model.py axioms-start/end noting none consumed). A-reference correspondence holds: A3 (is_radio <-> isinstance(self.widget, RadioSelect) after Field.__init__ normalisation) is validated by axiom_check.py section 3.1 whose local placeholder_offered (line 61-62) is logically byte-identical to model.py line 58, checked at the OBSERVABLE choice-sequence level list(field.choices)[0][0]=='' over 32 combos incl. RadioSelect class AND instance; B2 (return model_blank <-> 'blank': self.blank) validated by section 3.2 against real ForeignKey.blank plus the observable derived radio-field placeholder. Mapping.md binds each symbol to base_commit 335c9c94 repo lines and states the Optional[int]<->empty_label and boolean R-refinements. Both prepatch models (model_prepatch_1/2.py) fail the respective postconditions, matching atk_1/atk_2 (G-DIFF sensing confirmed).

VERDICT: SOUND — 7 distinct wrong impls (incl. both prepatch bugs) all rejected by the frozen spec; positive control verifies; A-references validated by G-AX with faithful model<->callee correspondence; no verify⇏/correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_8.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.py`

```python
"""Twin-artifact model for django__django-12406.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A model-backed single-choice field offers a leading blank placeholder
      choice exactly when an unfilled selection is a meaningful option. The
      placeholder is suppressed in two situations and offered otherwise:

        * it is suppressed when the field is mandatory AND already carries a
          pre-filled value (an empty selection would contradict the pre-fill);

        * it is ALSO suppressed when the field is rendered with a presentation
          whose unselected state is itself a visible choice (a one-of radio
          presentation) AND an empty selection is not a permitted value for
          the underlying data — because then the placeholder would masquerade
          as a genuine selectable value.

      In every other case the placeholder is offered. Whether the placeholder
      is offered is observable as: the field's choice sequence begins with a
      blank-keyed entry iff the placeholder is offered.

  (2) When such a field is derived for a related-object reference, the
      permission-to-leave-empty flag that the data layer records for that
      reference is forwarded to the field unchanged, so situation (1)'s second
      clause is decided by the data layer's own emptiness permission, not by a
      hard-coded default.

The placeholder label is modelled as an ``Optional[int]`` carrier: ``None``
means "no placeholder choice" and a present integer code means "placeholder
choice offered" (its concrete content is irrelevant to the tested behaviour).
The presentation classification (is the unselected state a visible choice) and
the emptiness-permission flag are booleans. No library callee is consumed as an
axiom: the decision is pure boolean/structure logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The placeholder-suppression decision and the
# permission-flag forwarding are pure boolean logic, modelled deeply. The base
# initialiser that normalises the presentation object (so its classification is
# well-defined) is an unchanged callee whose only observed effect here — that
# the presentation classification is available afterwards — is validated
# out-of-band by axiom_check.py (G-AX) as an A-reference, not consumed.
# axioms-end


# pure-start
@Pure
def placeholder_offered(required: bool, initial_present: bool,
                        is_radio: bool, blank: bool) -> bool:
    """The blank placeholder choice is offered iff NEITHER suppression
    situation holds: not (mandatory with a pre-filled value) AND not (a radio
    presentation whose empty state is not a permitted value)."""
    return not ((required and initial_present) or (is_radio and not blank))
# pure-end


class ChoiceFieldState:
    def __init__(self) -> None:
        Ensures(Acc(self.placeholder))  # type: ignore
        Ensures(self.placeholder is None)  # type: ignore
        self.placeholder = None  # type: Optional[int]


def configure_placeholder(field: ChoiceFieldState, placeholder_label: int,
                          required: bool, initial_present: bool,
                          is_radio: bool, blank: bool) -> None:
    # pre-conditions-start
    # The field object is genuinely mutated (its placeholder label is set), so
    # it carries full permission. The classification/permission inputs are
    # plain booleans (already-computed by the unchanged base initialiser).
    Requires(Acc(field.placeholder))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.placeholder))
    # The placeholder is OFFERED iff neither suppression situation holds; when
    # offered the field carries a present label, otherwise it carries none.
    Ensures(field.placeholder is not None
            if placeholder_offered(required, initial_present, is_radio, blank)
            else field.placeholder is None)
    # When offered, the carried label is exactly the supplied candidate label
    # (the placeholder is not replaced by some unrelated value).
    Ensures(Implies(placeholder_offered(required, initial_present, is_radio, blank),
                    field.placeholder is not None
                    and field.placeholder == placeholder_label))
    # post-conditions-end
    # impl-start
    if (required and initial_present) or (is_radio and not blank):
        field.placeholder = None
    else:
        field.placeholder = placeholder_label
    # impl-end


def derived_field_emptiness_flag(model_blank: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The emptiness-permission flag forwarded to the derived field is exactly
    # the data layer's recorded flag for the reference (forwarded unchanged).
    Ensures(Result() == model_blank)
    # post-conditions-end
    # impl-start
    return model_blank
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-12406 (nagini). adversary run under env swebench-lean.

SPEC SHAPE (why it is tight): configure_placeholder carries a TOTAL postcondition set that fully pins field.placeholder as a function of inputs — (a) present iff placeholder_offered(required,initial_present,is_radio,blank), else None; (b) when present, == placeholder_label exactly. derived_field_emptiness_flag carries Result()==model_blank. Both leave zero slack; placeholder_offered is a @Pure deep model, no @ContractOnly axioms.

ATTACKS (all built by copying model.py and editing ONLY the impl region; same-spec confirmed on atk_1 => exit 0 SAME; spec/axiom/@Pure/Requires/Ensures byte-identical). Command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12406 <path>`.
  atk_1 prepatch site-1 (drop radio suppression clause, `if required and initial_present`) => exit 2 NOT-A-COUNTEREXAMPLE (fails postcond on is_radio&not blank). PREPATCH BUG 1 REPRODUCED.
  atk_2 prepatch site-2 (`return False`) => exit 2 (fails Result()==model_blank when model_blank True). PREPATCH BUG 2 REPRODUCED.
  atk_3 boundary: `or`->`and` between the two suppression clauses => exit 2.
  atk_4 wrong carried value: `placeholder_label + 1` when offered (violates ==placeholder_label) => exit 2.
  atk_5 control-flow-effect: always `field.placeholder = placeholder_label` (never None) => exit 2.
  atk_6 ungrounded-oracle echo: drop `not` on blank (`is_radio and blank`) => exit 2.
  atk_7 partial-domain: `return not model_blank` => exit 2.
  atk_8 POSITIVE CONTROL = byte-identical gold impl => weakness exit 0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 11.5s), confirming the harness path and that the gold impl verifies.

No NON-gold wrong impl verified => there is NO verifying candidate whose faithful refined patch could be run through run_resolve; the resolve leg is vacuous here (patches={}) because the only CANDIDATE is the gold impl itself, whose refined patch is patch.diff (resolves by construction, G-RESOLVE). Attacks run in batches of 3 as concurrent background jobs (each Nagini check = JVM+Z3); all completed, none broke the spec.

REFINEMENT.MD A-LEG AUDIT: every leg is R (A1,A2,B1), A-reference (A3), or I (A4,A5,B2) — no A-consumed, no kind-3, no @ContractOnly axioms (consistent with model.py axioms-start/end noting none consumed). A-reference correspondence holds: A3 (is_radio <-> isinstance(self.widget, RadioSelect) after Field.__init__ normalisation) is validated by axiom_check.py section 3.1 whose local placeholder_offered (line 61-62) is logically byte-identical to model.py line 58, checked at the OBSERVABLE choice-sequence level list(field.choices)[0][0]=='' over 32 combos incl. RadioSelect class AND instance; B2 (return model_blank <-> 'blank': self.blank) validated by section 3.2 against real ForeignKey.blank plus the observable derived radio-field placeholder. Mapping.md binds each symbol to base_commit 335c9c94 repo lines and states the Optional[int]<->empty_label and boolean R-refinements. Both prepatch models (model_prepatch_1/2.py) fail the respective postconditions, matching atk_1/atk_2 (G-DIFF sensing confirmed).

VERDICT: SOUND — 7 distinct wrong impls (incl. both prepatch bugs) all rejected by the frozen spec; positive control verifies; A-references validated by G-AX with faithful model<->callee correspondence; no verify⇏/correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence between the modeled functions and the real repo behavior exists. The two modeled functions have a FINITE, entirely-boolean input domain: placeholder_offered(required, initial_present, is_radio, blank) over booleans, and derived_field_emptiness_flag(model_blank) over a single boolean. axiom_check.py exhaustively validates the deep models against the REAL Django callees at the patched worktree (gold applied): ran it with PYTHONPATH pointing at the patched tree -> exit 0, 'placeholder_offered deep model == real ModelChoiceField choice-sequence on 32 (required x initial x widget{default,RadioSelect class,RadioSelect instance,Select instance} x blank) combos; emptiness-flag forwarding == real ForeignKey.blank on 2 cases'. Equality is checked at the OBSERVABLE choice-sequence level (list(field.choices)[0][0]=='' == placeholder_offered(...)), the exact level F2P test_choices_radio_blank observes (ModelChoiceIterator yields ('', empty_label) iff empty_label is not None). The model is precisely the negation of the real post-patch suppression condition (required and initial is not None) or (isinstance(self.widget, RadioSelect) and not blank). Site 2 verified end-to-end through the REAL ForeignKey.formfield forwarding of self.blank for blank in {True, False}. Discriminating, NOT tautological: same axiom_check against the PRE-PATCH tree (git stash) raises TypeError: Field.__init__() got an unexpected keyword argument 'blank' (exit 1). Spec region byte-identical (same-spec adversary exit 0 on identity copy). Because the model agrees with the real callee at every point of the complete boolean input domain, the spec is not too strong and does not drift from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: no hard failures) and no semantic leak beyond the public problem_statement.

Public problem_statement already discloses: RadioSelect widget for a FK should NOT present a blank '-------' option when blank=False on the model; the radio's inherent unfilled state makes the placeholder look like a valid choice; there should be no blank option for RadioSelect when blank is not a valid selection.

Spec view (spec regions of model.py) uses only abstract vocabulary — 'placeholder', 'single-choice field', 'radio presentation whose unselected state is a visible choice', 'emptiness-permission flag'. The discriminating gold content is:
  * placeholder_offered = not((required and initial_present) or (is_radio and not blank))  — the second clause (is_radio and not blank) is exactly the behaviour the public task already states (RadioSelect + blank=False ⇒ suppress placeholder), so it does not go beyond problem_statement.
  * derived_field_emptiness_flag returns model_blank — forwarding the model's blank permission to the derived field, again the behaviour the task describes.

No edit-localization leaks into the CONSUMER view: no patched file path (django/forms/models.py, django/db/models/fields/related.py), no patched module dotted path, no patched repo symbol (empty_label, ModelChoiceField, RadioSelect, ForeignKey, formfield) appears in any spec-view identifier, comment, or docstring; no diff markers; no bug/fix narration. The changed symbols {'formfield','ModelChoiceField'} do not appear in the spec view. Clause 1 (required and initial_present) is pre-existing behaviour, not the gold edit, so its presence localizes nothing.

The file-path/symbol/pre-patch-state/control-flow-reorder details live only in refinement.md and mapping.md, which are explicitly auditor-only documents (not the consumer spec view / not part of leakage-screened solution_src). No RELAXED_LEAKAGE.md and no relaxed flag — this is a clean strict pass, not a deferral. Spec view discloses at the same level as the public task without revealing the gold edit's location or symbols.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
