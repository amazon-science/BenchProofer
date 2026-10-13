# P2 adversarial audit — django__django-12663

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
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -43,12 +42,6 @@
     def __init__(self) -> None:
         # source: a field identity; 0 == "no usable source identity".
         # field:  a field identity, always usable (!= 0).
-        # Terminates: two unconditional int field stores, no loop and no call.
-        # Level 1 is strictly below every obligated caller (output_field_identity
-        # is at 6), so an obligated caller may construct a Selection; without
-        # this the constructor is unobligated and Nagini reports "Callee
-        # __init__ might not take all unsatisfied obligations from the caller."
-        Requires(MustTerminate(1))
         Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
         Ensures(self.source == 0)  # type: ignore
         Ensures(self.field == 1)  # type: ignore
@@ -65,7 +58,6 @@
     Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
     # The ``field`` identity is always usable (nonzero).
     Requires(sel.field != 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
@@ -82,10 +74,5 @@
     Ensures(Implies(sel.source == 0, Result() == sel.field))
     # post-conditions-end
     # impl-start
-    # select = self.select[0]
-    # return getattr(select, 'target', None) or select.field
-    source = sel.source
-    if source != 0:
-        return source
-    return sel.field
+    return sel.source
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -43,12 +42,6 @@
     def __init__(self) -> None:
         # source: a field identity; 0 == "no usable source identity".
         # field:  a field identity, always usable (!= 0).
-        # Terminates: two unconditional int field stores, no loop and no call.
-        # Level 1 is strictly below every obligated caller (output_field_identity
-        # is at 6), so an obligated caller may construct a Selection; without
-        # this the constructor is unobligated and Nagini reports "Callee
-        # __init__ might not take all unsatisfied obligations from the caller."
-        Requires(MustTerminate(1))
         Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
         Ensures(self.source == 0)  # type: ignore
         Ensures(self.field == 1)  # type: ignore
@@ -65,7 +58,6 @@
     Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
     # The ``field`` identity is always usable (nonzero).
     Requires(sel.field != 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
@@ -82,10 +74,8 @@
     Ensures(Implies(sel.source == 0, Result() == sel.field))
     # post-conditions-end
     # impl-start
-    # select = self.select[0]
-    # return getattr(select, 'target', None) or select.field
     source = sel.source
-    if source != 0:
+    if source == 0:
         return source
     return sel.field
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -43,12 +42,6 @@
     def __init__(self) -> None:
         # source: a field identity; 0 == "no usable source identity".
         # field:  a field identity, always usable (!= 0).
-        # Terminates: two unconditional int field stores, no loop and no call.
-        # Level 1 is strictly below every obligated caller (output_field_identity
-        # is at 6), so an obligated caller may construct a Selection; without
-        # this the constructor is unobligated and Nagini reports "Callee
-        # __init__ might not take all unsatisfied obligations from the caller."
-        Requires(MustTerminate(1))
         Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
         Ensures(self.source == 0)  # type: ignore
         Ensures(self.field == 1)  # type: ignore
@@ -65,7 +58,6 @@
     Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
     # The ``field`` identity is always usable (nonzero).
     Requires(sel.field != 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
@@ -82,10 +74,6 @@
     Ensures(Implies(sel.source == 0, Result() == sel.field))
     # post-conditions-end
     # impl-start
-    # select = self.select[0]
-    # return getattr(select, 'target', None) or select.field
-    source = sel.source
-    if source != 0:
-        return source
-    return sel.field
+    sel.source = sel.field
+    return sel.source
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -43,12 +42,6 @@
     def __init__(self) -> None:
         # source: a field identity; 0 == "no usable source identity".
         # field:  a field identity, always usable (!= 0).
-        # Terminates: two unconditional int field stores, no loop and no call.
-        # Level 1 is strictly below every obligated caller (output_field_identity
-        # is at 6), so an obligated caller may construct a Selection; without
-        # this the constructor is unobligated and Nagini reports "Callee
-        # __init__ might not take all unsatisfied obligations from the caller."
-        Requires(MustTerminate(1))
         Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
         Ensures(self.source == 0)  # type: ignore
         Ensures(self.field == 1)  # type: ignore
@@ -65,7 +58,6 @@
     Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
     # The ``field`` identity is always usable (nonzero).
     Requires(sel.field != 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
@@ -82,10 +74,8 @@
     Ensures(Implies(sel.source == 0, Result() == sel.field))
     # post-conditions-end
     # impl-start
-    # select = self.select[0]
-    # return getattr(select, 'target', None) or select.field
     source = sel.source
     if source != 0:
-        return source
+        return source + 1
     return sel.field
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -43,12 +42,6 @@
     def __init__(self) -> None:
         # source: a field identity; 0 == "no usable source identity".
         # field:  a field identity, always usable (!= 0).
-        # Terminates: two unconditional int field stores, no loop and no call.
-        # Level 1 is strictly below every obligated caller (output_field_identity
-        # is at 6), so an obligated caller may construct a Selection; without
-        # this the constructor is unobligated and Nagini reports "Callee
-        # __init__ might not take all unsatisfied obligations from the caller."
-        Requires(MustTerminate(1))
         Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
         Ensures(self.source == 0)  # type: ignore
         Ensures(self.field == 1)  # type: ignore
@@ -65,7 +58,6 @@
     Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
     # The ``field`` identity is always usable (nonzero).
     Requires(sel.field != 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
@@ -82,10 +74,8 @@
     Ensures(Implies(sel.source == 0, Result() == sel.field))
     # post-conditions-end
     # impl-start
-    # select = self.select[0]
-    # return getattr(select, 'target', None) or select.field
     source = sel.source
     if source != 0:
-        return source
+        return sel.field
     return sel.field
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -43,12 +42,6 @@
     def __init__(self) -> None:
         # source: a field identity; 0 == "no usable source identity".
         # field:  a field identity, always usable (!= 0).
-        # Terminates: two unconditional int field stores, no loop and no call.
-        # Level 1 is strictly below every obligated caller (output_field_identity
-        # is at 6), so an obligated caller may construct a Selection; without
-        # this the constructor is unobligated and Nagini reports "Callee
-        # __init__ might not take all unsatisfied obligations from the caller."
-        Requires(MustTerminate(1))
         Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
         Ensures(self.source == 0)  # type: ignore
         Ensures(self.field == 1)  # type: ignore
@@ -65,7 +58,6 @@
     Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
     # The ``field`` identity is always usable (nonzero).
     Requires(sel.field != 0)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
@@ -82,10 +74,5 @@
     Ensures(Implies(sel.source == 0, Result() == sel.field))
     # post-conditions-end
     # impl-start
-    # select = self.select[0]
-    # return getattr(select, 'target', None) or select.field
-    source = sel.source
-    if source != 0:
-        return source
-    return sel.field
+    return 1
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12663.

Behavioural contract (stated as desired behaviour, not as an edit):

  A selected item carries two integer field identities: ``source`` and
  ``field``. ``output_field_identity`` returns a single field identity for the
  item, chosen as follows:

    * if ``source`` is a usable (nonzero) identity, the result is ``source``;
    * otherwise the result is ``field``.

  ``field`` is always a usable (nonzero) identity. ``source`` may be the
  sentinel identity ``0``, meaning "no usable source identity"; any nonzero
  ``source`` is a usable, distinct identity. The discriminating inputs are
  those where ``source`` is nonzero and differs from ``field``: there the
  result must be ``source``, never ``field``.

A selected item is modelled as a minimal object exposing only these two integer
identities. The choice is modelled deeply (pure choose-one-of-two logic); the
behaviour it stands on is validated out-of-band by axiom_check.py (G-AX) as an
A-reference, not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the choose-one-of-two selection is modelled deeply. The
# behaviour it stands on is validated against its real semantics out-of-band by
# axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Selection:
    def __init__(self) -> None:
        # source: a field identity; 0 == "no usable source identity".
        # field:  a field identity, always usable (!= 0).
        Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
        Ensures(self.source == 0)  # type: ignore
        Ensures(self.field == 1)  # type: ignore
        self.source = 0  # type: int
        self.field = 1  # type: int


def output_field_identity(sel: Selection) -> int:
    # pre-conditions-start
    # The selected item is read-only: required (and ensured) at fractional
    # permission only. A full-permission read-only input referenced in the
    # postcondition could be satisfied by an implementation that overwrites the
    # item's fields instead of choosing between them, so permission is shared.
    Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
    # The ``field`` identity is always usable (nonzero).
    Requires(sel.field != 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
    # The item is left exactly as it was (read-only).
    Ensures(sel.source == Old(sel.source))
    Ensures(sel.field == Old(sel.field))
    # The result is ``sel.source`` whenever it is a usable (nonzero) identity,
    # and ``sel.field`` otherwise. These two clauses together pin the selection
    # on every input: the discriminating case is an item whose ``source`` is
    # nonzero and differs from ``field`` (sel.source != 0 and
    # sel.source != sel.field) — there the result MUST be sel.source, never
    # sel.field.
    Ensures(Implies(sel.source != 0, Result() == sel.source))
    Ensures(Implies(sel.source == 0, Result() == sel.field))
    # post-conditions-end
    # impl-start
    # select = self.select[0]
    # return getattr(select, 'target', None) or select.field
    source = sel.source
    if source != 0:
        return source
    return sel.field
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins Result as a total function of (source,field) over the Requires domain (field!=0): Ensures(Implies(source!=0, Result==source)) AND Ensures(Implies(source==0, Result==field)) exhaustively partition all source values; fractional (1/2) permission + Ensures(source==Old(source)) & field==Old(field) forbid mutation (read-only). No verifying wrong impl can exist. Verifier env=swebench-nagini-verifier.

POSITIVE CONTROL: `bash scripts/nagini_verify.sh .../positive_control.py` -> 'Verification successful' exit 0 (17.57s).

PREPATCH: model_prepatch.py impl `return sel.field` -> `bash scripts/nagini_verify.sh` exit 1, error 'Postcondition ... Implies((sel.source != 0), (Result() == sel.source)) might not hold' (15.88s). G-DIFF reproduced: the spec senses the change on the discriminating clause.

ATTACKS — all same-spec AND rejected by verification (weakness exit 2 = NOT-A-COUNTEREXAMPLE 'attack does not verify'). Command each: `python -m swebench_unified.adversary weakness nagini django__django-12663 <atk>.py`. Batched 3-at-a-time as background jobs.
  atk_1 (partial-domain: return sel.source; wrong when source==0 -> returns 0 != field): weakness exit=2; same-spec exit=0.
  atk_2 (boundary/swapped condition: if source==0 return source else return field): weakness exit=2.
  atk_3 (control-flow-effect/mutation: sel.source = sel.field; return sel.source — tests read-only fractional permission): weakness exit=2; same-spec exit=0.
  atk_4 (ungrounded arithmetic echo: return source+1 on source!=0 branch): weakness exit=2.
  atk_5 (constant-collapse/dead branch: both branches return sel.field, ignoring source): weakness exit=2.
  atk_6 (literal echo: return 1 — matches Selection default field but not the quantified field): weakness exit=2; same-spec exit=0.
Same-spec explicitly reconfirmed on atk_1/atk_3/atk_6 (exit 0, 'SAME — attack shares the bundle's exact specification'), so the failures are genuine verification rejections, not spec-mismatch artifacts.

NO CANDIDATES: since no attack verified, none is a CANDIDATE (weakness would exit 0), so no faithful refined patch needed to be materialized or run through the harness — the resolve step is gated on a verifying candidate and correctly did not trigger. patches={} accordingly.

REFINEMENT.MD A-LEG AUDIT: legs A1-A4 are all R or R+I (Col<->Selection integer-identity refinement; getattr/or truthy short-circuit <-> `if source!=0`; identical fallback control). §B: no consumed axioms (no @ContractOnly the proof uses) — zero A-consumed legs, so nothing to over-trust there. §D: no kind-3 (unexpressible-changed-op) steps; the changed op (prefer Col.target over Col.field) is spelled out deeply at A3/A4, not hidden behind an axiom. §C A-reference: deep-model choose-one <-> real `getattr(select,'target',None) or select.field` and real Query.output_field; axiom_check.py (G-AX) validates the correspondence against the REAL callees — builds real Django Col objects (plain, where field==target; and explicit-differing output_field, where field!=target — the discriminating regression), installs each as the sole self.select of a real Query, and asserts the post-patch property returns Col.target (the relation-aware source field), never Col.field. Sentinel mapping 0<->absent/falsy target, nonzero<->truthy-target-returned holds. The A-reference correspondence to the real callees is sound.

CONCLUSION: >=6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect/mutation, ungrounded-oracle echo, constant-collapse, literal-echo) plus the prepatch bug all fail verification; positive control verifies; A-legs sound. verify=>correct holds for this bundle. SOUND.

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
"""Twin-artifact model for django__django-12663.

Behavioural contract (stated as desired behaviour, not as an edit):

  A selected item carries two integer field identities: ``source`` and
  ``field``. ``output_field_identity`` returns a single field identity for the
  item, chosen as follows:

    * if ``source`` is a usable (nonzero) identity, the result is ``source``;
    * otherwise the result is ``field``.

  ``field`` is always a usable (nonzero) identity. ``source`` may be the
  sentinel identity ``0``, meaning "no usable source identity"; any nonzero
  ``source`` is a usable, distinct identity. The discriminating inputs are
  those where ``source`` is nonzero and differs from ``field``: there the
  result must be ``source``, never ``field``.

A selected item is modelled as a minimal object exposing only these two integer
identities. The choice is modelled deeply (pure choose-one-of-two logic); the
behaviour it stands on is validated out-of-band by axiom_check.py (G-AX) as an
A-reference, not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the choose-one-of-two selection is modelled deeply. The
# behaviour it stands on is validated against its real semantics out-of-band by
# axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Selection:
    def __init__(self) -> None:
        # source: a field identity; 0 == "no usable source identity".
        # field:  a field identity, always usable (!= 0).
        Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
        Ensures(self.source == 0)  # type: ignore
        Ensures(self.field == 1)  # type: ignore
        self.source = 0  # type: int
        self.field = 1  # type: int


def output_field_identity(sel: Selection) -> int:
    # pre-conditions-start
    # The selected item is read-only: required (and ensured) at fractional
    # permission only. A full-permission read-only input referenced in the
    # postcondition could be satisfied by an implementation that overwrites the
    # item's fields instead of choosing between them, so permission is shared.
    Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
    # The ``field`` identity is always usable (nonzero).
    Requires(sel.field != 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
    # The item is left exactly as it was (read-only).
    Ensures(sel.source == Old(sel.source))
    Ensures(sel.field == Old(sel.field))
    # The result is ``sel.source`` whenever it is a usable (nonzero) identity,
    # and ``sel.field`` otherwise. These two clauses together pin the selection
    # on every input: the discriminating case is an item whose ``source`` is
    # nonzero and differs from ``field`` (sel.source != 0 and
    # sel.source != sel.field) — there the result MUST be sel.source, never
    # sel.field.
    Ensures(Implies(sel.source != 0, Result() == sel.source))
    Ensures(Implies(sel.source == 0, Result() == sel.field))
    # post-conditions-end
    # impl-start
    # select = self.select[0]
    # return getattr(select, 'target', None) or select.field
    source = sel.source
    if source != 0:
        return source
    return sel.field
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins Result as a total function of (source,field) over the Requires domain (field!=0): Ensures(Implies(source!=0, Result==source)) AND Ensures(Implies(source==0, Result==field)) exhaustively partition all source values; fractional (1/2) permission + Ensures(source==Old(source)) & field==Old(field) forbid mutation (read-only). No verifying wrong impl can exist. Verifier env=swebench-nagini-verifier.

POSITIVE CONTROL: `bash scripts/nagini_verify.sh .../positive_control.py` -> 'Verification successful' exit 0 (17.57s).

PREPATCH: model_prepatch.py impl `return sel.field` -> `bash scripts/nagini_verify.sh` exit 1, error 'Postcondition ... Implies((sel.source != 0), (Result() == sel.source)) might not hold' (15.88s). G-DIFF reproduced: the spec senses the change on the discriminating clause.

ATTACKS — all same-spec AND rejected by verification (weakness exit 2 = NOT-A-COUNTEREXAMPLE 'attack does not verify'). Command each: `python -m swebench_unified.adversary weakness nagini django__django-12663 <atk>.py`. Batched 3-at-a-time as background jobs.
  atk_1 (partial-domain: return sel.source; wrong when source==0 -> returns 0 != field): weakness exit=2; same-spec exit=0.
  atk_2 (boundary/swapped condition: if source==0 return source else return field): weakness exit=2.
  atk_3 (control-flow-effect/mutation: sel.source = sel.field; return sel.source — tests read-only fractional permission): weakness exit=2; same-spec exit=0.
  atk_4 (ungrounded arithmetic echo: return source+1 on source!=0 branch): weakness exit=2.
  atk_5 (constant-collapse/dead branch: both branches return sel.field, ignoring source): weakness exit=2.
  atk_6 (literal echo: return 1 — matches Selection default field but not the quantified field): weakness exit=2; same-spec exit=0.
Same-spec explicitly reconfirmed on atk_1/atk_3/atk_6 (exit 0, 'SAME — attack shares the bundle's exact specification'), so the failures are genuine verification rejections, not spec-mismatch artifacts.

NO CANDIDATES: since no attack verified, none is a CANDIDATE (weakness would exit 0), so no faithful refined patch needed to be materialized or run through the harness — the resolve step is gated on a verifying candidate and correctly did not trigger. patches={} accordingly.

REFINEMENT.MD A-LEG AUDIT: legs A1-A4 are all R or R+I (Col<->Selection integer-identity refinement; getattr/or truthy short-circuit <-> `if source!=0`; identical fallback control). §B: no consumed axioms (no @ContractOnly the proof uses) — zero A-consumed legs, so nothing to over-trust there. §D: no kind-3 (unexpressible-changed-op) steps; the changed op (prefer Col.target over Col.field) is spelled out deeply at A3/A4, not hidden behind an axiom. §C A-reference: deep-model choose-one <-> real `getattr(select,'target',None) or select.field` and real Query.output_field; axiom_check.py (G-AX) validates the correspondence against the REAL callees — builds real Django Col objects (plain, where field==target; and explicit-differing output_field, where field!=target — the discriminating regression), installs each as the sole self.select of a real Query, and asserts the post-patch property returns Col.target (the relation-aware source field), never Col.field. Sentinel mapping 0<->absent/falsy target, nonzero<->truthy-target-returned holds. The A-reference correspondence to the real callees is sound.

CONCLUSION: >=6 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect/mutation, ungrounded-oracle echo, constant-collapse, literal-echo) plus the prepatch bug all fail verification; positive control verifies; A-legs sound. verify=>correct holds for this bundle. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (2) faithfulness-break for django__django-12663 (nagini). The modeled function output_field_identity models the len(self.select)==1 branch of Query.output_field, post-patch expression `getattr(select,'target',None) or select.field`. Type bridge: field objects -> int identities; source==0 iff the item's target attr is absent OR falsy, nonzero iff present-and-truthy; field is the resolved output field (always a real, truthy Field object).

Checks run against the REAL repo (base_commit fa5e7e4 worktree with the gold patch applied; env python resolves `django` to that worktree):
- Nagini verify of model.py: PASS (16.3s).
- axiom_check.py (G-AX) in-repo: exit 0, 302 real Django observations — real Query.output_field returns Col.target incl. the discriminating override case (Col built with explicit output_field != target).
- conformance_check.py (G-CONF) in-repo: exit 0, 100018 inputs (18 boundary + 100k fuzz, seed 12663), 0 disagreements between the contract-stripped shadow and the real patched property.
- Independent adversarial edge sweep (all falsy shapes None/0/0.0/''/[]/{}/()/set()/False, several truthy targets, target absent, source==field, multiple field object kinds) under the same intern bridge: 0 divergences.

Faithfulness analysis of the two directions the spec could be too strong:
1. Precondition Requires(sel.field != 0): corresponds to real select.field = Expression.field -> output_field, which is always a real Field object (truthy) for any reachable single selection. No reachable real input violates it, so the precondition does not exclude any real behavior — not an artificial strengthening.
2. Postcondition clauses (source!=0 => Result==source) and (source==0 => Result==field): exactly mirror the `or` short-circuit of getattr(...,'target',None) or select.field under the truthy/falsy->0/nonzero bridge. Confirmed identical on every input class tested. The discriminating regression clause (source!=0 => source) matches the real fix, and model_prepatch (return sel.field) correctly fails it (G-DIFF).

Spec region is the frozen bundle spec (verified this is the shipped model.py; no divergence between the modeled function and the real callee was found on any input). No drift / no over-strong spec detected.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl region elided to '...  # implementation elided') was recomputed with markers.spec_view and screened with leakage.screen: mechanical screen PASSES (0 hard failures); recorded meta G-LEAK status=pass, no relaxation. Semantic review confirms no leak of the gold edit beyond the public problem_statement. Gold edit: `return self.select[0].field` -> `select = self.select[0]; return getattr(select,'target',None) or select.field`; discriminating content is preferring Col.target over Col.field. In the consumer spec view: (1) the discriminating repo symbol `target` is abstracted/renamed to the integer identity `source` and never appears; (2) the verbatim gold lines (`select = self.select[0]`, `getattr(select,'target',None) or select.field`) live ONLY inside the elided impl region and are absent from the view; (3) no diff markers, no patched file path (`django/db/models/sql/query.py` appears only in auditor-only mapping.md/refinement.md, not the spec view), no fix/bug narration words; (4) patch changed-symbol set is empty (section header `def __init__` is non-distinctive; added lines carry no def/class), so no identifier collision. `output_field_identity` embeds `output_field`, which IS in the public problem_statement, and generic `field` was present pre-patch and does not localize the edit. The behavioural contract ('return source when nonzero, else field') is an abstracted spec that still requires the solver to do the repo-mapping work (that Col.target is the usable source field) kept private in mapping.md. No spec-view line discloses the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
