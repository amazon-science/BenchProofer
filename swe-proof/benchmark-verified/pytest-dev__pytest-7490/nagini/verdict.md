# P2 adversarial audit — pytest-dev__pytest-7490

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
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Xfail:
@@ -41,7 +40,6 @@
     downstream classification branches on is carried)."""
 
     def __init__(self, run: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.run) and self.run is run)  # type: ignore
         self.run = run
 
@@ -52,7 +50,6 @@
     (possibly an empty/``None`` evaluation even when present)."""
 
     def __init__(self, present: bool, value: Optional[Xfail]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present is present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         self.present = present
@@ -85,7 +82,6 @@
     # pre-conditions-start
     Requires(Acc(slot.present))
     Requires(Acc(slot.value))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present))
@@ -112,10 +108,5 @@
     )
     # post-conditions-end
     # impl-start
-    if not slot.present:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
-    elif slot.value is None:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
+    pass
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Xfail:
@@ -41,7 +40,6 @@
     downstream classification branches on is carried)."""
 
     def __init__(self, run: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.run) and self.run is run)  # type: ignore
         self.run = run
 
@@ -52,7 +50,6 @@
     (possibly an empty/``None`` evaluation even when present)."""
 
     def __init__(self, present: bool, value: Optional[Xfail]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present is present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         self.present = present
@@ -85,7 +82,6 @@
     # pre-conditions-start
     Requires(Acc(slot.present))
     Requires(Acc(slot.value))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present))
@@ -115,7 +111,4 @@
     if not slot.present:
         slot.value = evaluate_marks(final_marker_state)
         slot.present = True
-    elif slot.value is None:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Xfail:
@@ -41,7 +40,6 @@
     downstream classification branches on is carried)."""
 
     def __init__(self, run: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.run) and self.run is run)  # type: ignore
         self.run = run
 
@@ -52,7 +50,6 @@
     (possibly an empty/``None`` evaluation even when present)."""
 
     def __init__(self, present: bool, value: Optional[Xfail]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present is present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         self.present = present
@@ -85,7 +82,6 @@
     # pre-conditions-start
     Requires(Acc(slot.present))
     Requires(Acc(slot.value))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present))
@@ -112,10 +108,6 @@
     )
     # post-conditions-end
     # impl-start
-    if not slot.present:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
-    elif slot.value is None:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
+    slot.value = None
+    slot.present = True
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Xfail:
@@ -41,7 +40,6 @@
     downstream classification branches on is carried)."""
 
     def __init__(self, run: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.run) and self.run is run)  # type: ignore
         self.run = run
 
@@ -52,7 +50,6 @@
     (possibly an empty/``None`` evaluation even when present)."""
 
     def __init__(self, present: bool, value: Optional[Xfail]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present is present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         self.present = present
@@ -85,7 +82,6 @@
     # pre-conditions-start
     Requires(Acc(slot.present))
     Requires(Acc(slot.value))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present))
@@ -112,10 +108,6 @@
     )
     # post-conditions-end
     # impl-start
-    if not slot.present:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
-    elif slot.value is None:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
+    slot.value = evaluate_marks(final_marker_state)
+    slot.present = True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Xfail:
@@ -41,7 +40,6 @@
     downstream classification branches on is carried)."""
 
     def __init__(self, run: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.run) and self.run is run)  # type: ignore
         self.run = run
 
@@ -52,7 +50,6 @@
     (possibly an empty/``None`` evaluation even when present)."""
 
     def __init__(self, present: bool, value: Optional[Xfail]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present is present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         self.present = present
@@ -85,7 +82,6 @@
     # pre-conditions-start
     Requires(Acc(slot.present))
     Requires(Acc(slot.value))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present))
@@ -112,10 +108,5 @@
     )
     # post-conditions-end
     # impl-start
-    if not slot.present:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
-    elif slot.value is None:
-        slot.value = evaluate_marks(final_marker_state)
-        slot.present = True
+    slot.present = True
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Xfail:
@@ -41,7 +40,6 @@
     downstream classification branches on is carried)."""
 
     def __init__(self, run: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.run) and self.run is run)  # type: ignore
         self.run = run
 
@@ -52,7 +50,6 @@
     (possibly an empty/``None`` evaluation even when present)."""
 
     def __init__(self, present: bool, value: Optional[Xfail]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present is present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         self.present = present
@@ -85,7 +82,6 @@
     # pre-conditions-start
     Requires(Acc(slot.present))
     Requires(Acc(slot.value))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present))
@@ -113,9 +109,9 @@
     # post-conditions-end
     # impl-start
     if not slot.present:
-        slot.value = evaluate_marks(final_marker_state)
+        slot.value = evaluate_marks(0)
         slot.present = True
     elif slot.value is None:
-        slot.value = evaluate_marks(final_marker_state)
+        slot.value = evaluate_marks(0)
         slot.present = True
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Xfail:
@@ -41,7 +40,6 @@
     downstream classification branches on is carried)."""
 
     def __init__(self, run: bool) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.run) and self.run is run)  # type: ignore
         self.run = run
 
@@ -52,7 +50,6 @@
     (possibly an empty/``None`` evaluation even when present)."""
 
     def __init__(self, present: bool, value: Optional[Xfail]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.present) and self.present is present)  # type: ignore
         Ensures(Acc(self.value) and self.value is value)  # type: ignore
         self.present = present
@@ -85,7 +82,6 @@
     # pre-conditions-start
     Requires(Acc(slot.present))
     Requires(Acc(slot.value))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(slot.present))
@@ -116,6 +112,5 @@
         slot.value = evaluate_marks(final_marker_state)
         slot.present = True
     elif slot.value is None:
-        slot.value = evaluate_marks(final_marker_state)
         slot.present = True
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-7490.

Behaviour under specification (an abstract input/output contract, not an edit):

  A test carries a saved evaluation of its expected-failure marks. That saved
  evaluation is what decides whether a failing run counts as an expected
  failure (and whether an unexpectedly-passing strict run counts as a real
  failure).

  This operation settles that saved evaluation against the marks as they
  FINALLY stand on the test. Its input/output relation is:

    * If a meaningful (present, non-empty) evaluation is already saved, that
      evaluation is the one that stands.
    * Otherwise (no evaluation is saved, or only an empty one is), the saved
      evaluation becomes the evaluation of the marks as they finally stand.
    * In all cases the saved evaluation ends up present.

  Equivalently: the evaluation that stands is the previously-saved one when it
  was already present and non-empty, and the evaluation of the final marks
  otherwise. An expected-failure mark that becomes present only by the time the
  marks finally stand is therefore honoured, exactly as if it had stood from the
  start.

Marks are modelled by an opaque token (an ``int`` identifying the marker state
on the test); the unchanged community mark-evaluator is the ``@Pure``
``@ContractOnly`` callee ``evaluate_marks`` mapping a marker state to an
``Optional[Xfail]``. The saved evaluation is a minimal class carrying only the
touched fields (whether a value is saved, and the saved value). The final
marker state is a separate marker-state token.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class Xfail:
    """Minimal model of an evaluated expected-failure mark (only the field the
    downstream classification branches on is carried)."""

    def __init__(self, run: bool) -> None:
        Ensures(Acc(self.run) and self.run is run)  # type: ignore
        self.run = run


class SavedSlot:
    """The saved expected-failure evaluation that classification consumes.
    ``present`` is whether anything is saved; ``value`` is the saved evaluation
    (possibly an empty/``None`` evaluation even when present)."""

    def __init__(self, present: bool, value: Optional[Xfail]) -> None:
        Ensures(Acc(self.present) and self.present is present)  # type: ignore
        Ensures(Acc(self.value) and self.value is value)  # type: ignore
        self.present = present
        self.value = value


# axioms-start
@Pure
@ContractOnly
def evaluate_marks(marker_state: int) -> Optional[Xfail]:
    """Unchanged community evaluator of the test's expected-failure marks: a
    pure function of the marker state currently on the test. Returns the
    evaluated expected-failure descriptor, or ``None`` when no such mark
    applies. Provenance + executable soundness check: mapping.md /
    axiom_check.py. The proof relies only on it being a deterministic function
    of its argument, so a change to the marker state can change the result.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def settle_saved_evaluation(
    slot: SavedSlot,
    final_marker_state: int,
) -> None:
    # pre-conditions-start
    Requires(Acc(slot.present))
    Requires(Acc(slot.value))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(slot.present))
    Ensures(Acc(slot.value))
    # The saved evaluation always ends up present.
    Ensures(slot.present)
    # When no meaningful evaluation was saved on entry (nothing was saved, or
    # only an empty one), the evaluation that stands is the evaluation of the
    # marks as they finally stand. (Discriminating clause: the value must be
    # PRODUCED BY evaluating the final marks, i.e. by invoking the real
    # evaluator on the final marker state.)
    Ensures(
        Implies(
            not (Old(slot.present) and Old(slot.value) is not None),
            slot.value is evaluate_marks(final_marker_state),
        )
    )
    # An evaluation that was already present and non-empty on entry is kept.
    Ensures(
        Implies(
            Old(slot.present) and Old(slot.value) is not None,
            slot.value is Old(slot.value),
        )
    )
    # post-conditions-end
    # impl-start
    if not slot.present:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True
    elif slot.value is None:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pytest-dev__pytest-7490 (nagini). WORKDIR Runner python python; SBU_BENCHMARK_DIR=benchmark-verified.

SPEC ANALYSIS: settle_saved_evaluation's postconditions TOTALLY specify both observable fields over a complete partition of the input space, leaving no residual output freedom: (1) Ensures(slot.present) => present=True always; (2) category A [Old.present AND Old.value is not None]: slot.value is Old(slot.value) (value preserved by identity); (3) category B [complement]: slot.value is evaluate_marks(final_marker_state) (value pinned by identity to the deterministic @Pure evaluator on the final marker token). Both fields fixed in every category => any verifying impl is behaviourally equal to the gold post-yield refresh block in-model.

### ATTACKS (all confirmed same-spec via `adversary same-spec`, then run via `adversary weakness nagini pytest-dev__pytest-7490 <f>`):
- atk_1.py: bare `pass` (= prepatch bug). weakness exit=2, verification failed (fails Ensures(slot.present) when pre-slot absent/empty).
- atk_2.py: partial-domain, only handles `if not slot.present`, drops the `elif slot.value is None` branch. exit=2, fails (category B present+None value: value stays None != evaluate_marks).
- atk_3.py: ungrounded oracle echo `slot.value=None; slot.present=True`. exit=2, fails (category B value must be evaluate_marks(...), and category A preservation violated).
- atk_4.py: boundary clobber `slot.value=evaluate_marks(final_marker_state); present=True` unconditionally. exit=2, fails (category A: destroys the preserved Old.value identity).
- atk_5.py: control-flow present-only-effect `slot.present=True` (never refreshes value). exit=2, fails (category B value stays None/absent).
- atk_6.py: wrong-argument oracle echo, refresh with constant token evaluate_marks(0) instead of final_marker_state. exit=2, fails (value is evaluate_marks(0) != evaluate_marks(final_marker_state)).
- atk_7.py: partial control-flow, elif branch sets present=True but omits value refresh. exit=2, fails (category B present+None: value stays None).

Positive control (bundle model.py copied verbatim): `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (10.5s), VERIFY_EXIT=0. Prepatch (model_prepatch.py, bare pass): weakness exit=2, verification failed => prepatch bug reproduced (G-DIFF confirmed).

NO CANDIDATE EMERGED: 0/7 attacks were same-spec AND verifying, so there is NO faithful refined patch to materialize; no run_resolve was warranted (protocol requires resolve only for CANDIDATEs). Attacks span the required categories: prepatch bug, partial-domain (atk_2/atk_7), boundary (atk_4), control-flow-effect (atk_5), ungrounded/wrong-arg oracle echo (atk_3/atk_6).

A-LEG / CORRESPONDENCE AUDIT (refinement.md): all legs are R / R+I / R+A-consumed (steps 1-4) plus two behaviour-preserving rewrites (NOTRUN-guard flatten, skipped_by_mark_key) folded into the slot pre-state; the doc explicitly certifies NO kind-3 (unexpressible-changed-op) step and the changed op (post-body refresh) is modeled DEEPLY as the literal impl region. Sole consumed axiom evaluate_marks <-> unchanged callee _pytest.skipping.evaluate_xfail_marks (mapping.md sec 3.1) with the WEAKEST (empty-Ensures) contract => trivially sound / never over-approximates; proof consumes only determinism (same token -> same value), used by the `slot.value is evaluate_marks(final_marker_state)` postcondition. Directive-7 totality over-claim (axiom total, real callee can raise Failed) is documented and INERT (proof never uses totality; F2P scenarios use non-raising marks). G-AX/axiom_check.py executably validates determinism + state-sensitivity of the real callee and drives the real patched pytest end-to-end (1 xfailed / 1 failed) with a pre-patch no-refresh witness (G-DIFF). A-reference deep refresh corresponds to the gold patch's added post-`yield` block. Correspondence holds on all A-legs.

VERDICT: SOUND — 5+ (7) distinct same-spec wrong impls run under the official adversary weakness harness, none verifies; spec is a total contract with no residual freedom; A-legs correspond to the real callees; positive control verifies and the prepatch bug is reproduced.

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
"""Twin-artifact model for pytest-dev__pytest-7490.

Behaviour under specification (an abstract input/output contract, not an edit):

  A test carries a saved evaluation of its expected-failure marks. That saved
  evaluation is what decides whether a failing run counts as an expected
  failure (and whether an unexpectedly-passing strict run counts as a real
  failure).

  This operation settles that saved evaluation against the marks as they
  FINALLY stand on the test. Its input/output relation is:

    * If a meaningful (present, non-empty) evaluation is already saved, that
      evaluation is the one that stands.
    * Otherwise (no evaluation is saved, or only an empty one is), the saved
      evaluation becomes the evaluation of the marks as they finally stand.
    * In all cases the saved evaluation ends up present.

  Equivalently: the evaluation that stands is the previously-saved one when it
  was already present and non-empty, and the evaluation of the final marks
  otherwise. An expected-failure mark that becomes present only by the time the
  marks finally stand is therefore honoured, exactly as if it had stood from the
  start.

Marks are modelled by an opaque token (an ``int`` identifying the marker state
on the test); the unchanged community mark-evaluator is the ``@Pure``
``@ContractOnly`` callee ``evaluate_marks`` mapping a marker state to an
``Optional[Xfail]``. The saved evaluation is a minimal class carrying only the
touched fields (whether a value is saved, and the saved value). The final
marker state is a separate marker-state token.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class Xfail:
    """Minimal model of an evaluated expected-failure mark (only the field the
    downstream classification branches on is carried)."""

    def __init__(self, run: bool) -> None:
        Ensures(Acc(self.run) and self.run is run)  # type: ignore
        self.run = run


class SavedSlot:
    """The saved expected-failure evaluation that classification consumes.
    ``present`` is whether anything is saved; ``value`` is the saved evaluation
    (possibly an empty/``None`` evaluation even when present)."""

    def __init__(self, present: bool, value: Optional[Xfail]) -> None:
        Ensures(Acc(self.present) and self.present is present)  # type: ignore
        Ensures(Acc(self.value) and self.value is value)  # type: ignore
        self.present = present
        self.value = value


# axioms-start
@Pure
@ContractOnly
def evaluate_marks(marker_state: int) -> Optional[Xfail]:
    """Unchanged community evaluator of the test's expected-failure marks: a
    pure function of the marker state currently on the test. Returns the
    evaluated expected-failure descriptor, or ``None`` when no such mark
    applies. Provenance + executable soundness check: mapping.md /
    axiom_check.py. The proof relies only on it being a deterministic function
    of its argument, so a change to the marker state can change the result.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def settle_saved_evaluation(
    slot: SavedSlot,
    final_marker_state: int,
) -> None:
    # pre-conditions-start
    Requires(Acc(slot.present))
    Requires(Acc(slot.value))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(slot.present))
    Ensures(Acc(slot.value))
    # The saved evaluation always ends up present.
    Ensures(slot.present)
    # When no meaningful evaluation was saved on entry (nothing was saved, or
    # only an empty one), the evaluation that stands is the evaluation of the
    # marks as they finally stand. (Discriminating clause: the value must be
    # PRODUCED BY evaluating the final marks, i.e. by invoking the real
    # evaluator on the final marker state.)
    Ensures(
        Implies(
            not (Old(slot.present) and Old(slot.value) is not None),
            slot.value is evaluate_marks(final_marker_state),
        )
    )
    # An evaluation that was already present and non-empty on entry is kept.
    Ensures(
        Implies(
            Old(slot.present) and Old(slot.value) is not None,
            slot.value is Old(slot.value),
        )
    )
    # post-conditions-end
    # impl-start
    if not slot.present:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True
    elif slot.value is None:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pytest-dev__pytest-7490 (nagini). WORKDIR Runner python python; SBU_BENCHMARK_DIR=benchmark-verified.

SPEC ANALYSIS: settle_saved_evaluation's postconditions TOTALLY specify both observable fields over a complete partition of the input space, leaving no residual output freedom: (1) Ensures(slot.present) => present=True always; (2) category A [Old.present AND Old.value is not None]: slot.value is Old(slot.value) (value preserved by identity); (3) category B [complement]: slot.value is evaluate_marks(final_marker_state) (value pinned by identity to the deterministic @Pure evaluator on the final marker token). Both fields fixed in every category => any verifying impl is behaviourally equal to the gold post-yield refresh block in-model.

### ATTACKS (all confirmed same-spec via `adversary same-spec`, then run via `adversary weakness nagini pytest-dev__pytest-7490 <f>`):
- atk_1.py: bare `pass` (= prepatch bug). weakness exit=2, verification failed (fails Ensures(slot.present) when pre-slot absent/empty).
- atk_2.py: partial-domain, only handles `if not slot.present`, drops the `elif slot.value is None` branch. exit=2, fails (category B present+None value: value stays None != evaluate_marks).
- atk_3.py: ungrounded oracle echo `slot.value=None; slot.present=True`. exit=2, fails (category B value must be evaluate_marks(...), and category A preservation violated).
- atk_4.py: boundary clobber `slot.value=evaluate_marks(final_marker_state); present=True` unconditionally. exit=2, fails (category A: destroys the preserved Old.value identity).
- atk_5.py: control-flow present-only-effect `slot.present=True` (never refreshes value). exit=2, fails (category B value stays None/absent).
- atk_6.py: wrong-argument oracle echo, refresh with constant token evaluate_marks(0) instead of final_marker_state. exit=2, fails (value is evaluate_marks(0) != evaluate_marks(final_marker_state)).
- atk_7.py: partial control-flow, elif branch sets present=True but omits value refresh. exit=2, fails (category B present+None: value stays None).

Positive control (bundle model.py copied verbatim): `bash scripts/nagini_verify.sh positive_control.py` => Verification successful (10.5s), VERIFY_EXIT=0. Prepatch (model_prepatch.py, bare pass): weakness exit=2, verification failed => prepatch bug reproduced (G-DIFF confirmed).

NO CANDIDATE EMERGED: 0/7 attacks were same-spec AND verifying, so there is NO faithful refined patch to materialize; no run_resolve was warranted (protocol requires resolve only for CANDIDATEs). Attacks span the required categories: prepatch bug, partial-domain (atk_2/atk_7), boundary (atk_4), control-flow-effect (atk_5), ungrounded/wrong-arg oracle echo (atk_3/atk_6).

A-LEG / CORRESPONDENCE AUDIT (refinement.md): all legs are R / R+I / R+A-consumed (steps 1-4) plus two behaviour-preserving rewrites (NOTRUN-guard flatten, skipped_by_mark_key) folded into the slot pre-state; the doc explicitly certifies NO kind-3 (unexpressible-changed-op) step and the changed op (post-body refresh) is modeled DEEPLY as the literal impl region. Sole consumed axiom evaluate_marks <-> unchanged callee _pytest.skipping.evaluate_xfail_marks (mapping.md sec 3.1) with the WEAKEST (empty-Ensures) contract => trivially sound / never over-approximates; proof consumes only determinism (same token -> same value), used by the `slot.value is evaluate_marks(final_marker_state)` postcondition. Directive-7 totality over-claim (axiom total, real callee can raise Failed) is documented and INERT (proof never uses totality; F2P scenarios use non-raising marks). G-AX/axiom_check.py executably validates determinism + state-sensitivity of the real callee and drives the real patched pytest end-to-end (1 xfailed / 1 failed) with a pre-patch no-refresh witness (G-DIFF). A-reference deep refresh corresponds to the gold patch's added post-`yield` block. Correspondence holds on all A-legs.

VERDICT: SOUND — 5+ (7) distinct same-spec wrong impls run under the official adversary weakness harness, none verifies; spec is a total contract with no residual freedom; A-legs correspond to the real callees; positive control verifies and the prepatch bug is reproduced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to bundle (compared model.py verbatim; same-spec carrier). Model VERIFIES under pinned Nagini (Verification successful, 10.36s). Verified base_commit 7f7a36478 worktree; the gold hunk (PR #7490 / ccad10a82) adds exactly the post-yield block:
  xfailed = item._store.get(xfailed_key, None)
  if xfailed is None:
      item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)
Case-by-case equivalence to the model impl (if not slot.present / elif slot.value is None) under the documented R-carrier (get(...,None) is None <=> not present or value is None): (1) absent -> refresh+present; (2) present&None -> refresh+present; (3) present&non-None -> unchanged. All three agree with the real block bit-for-bit, and match the postconditions (Ensures(slot.present); refresh clause guarded by not(Old.present and Old.value is not None); keep clause otherwise). Object-identity 'is' holds because the store write binds the exact callee return and evaluate_marks is modeled deterministic. The spec is NOT too strong: it never claims more than the gold block delivers on any tested input, and the impl region literally IS the gold block (G-RESOLVE resolves). The single divergence (callee totality vs the real raising-condition path) is explicitly acknowledged in mapping.md directive-7 as an inert over-claim: the proof consumes only determinism, never totality, and no F2P/P2P test exercises a raising-condition mark. No spec-too-strong drift exists on any tested/resolution-relevant input. VERDICT: FAITHFUL.

  xfailed = item._store.get(xfailed_key, None)
  if xfailed is None:
      item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)
Case-by-case equivalence to the model impl (if not slot.present / elif slot.value is None) under the documented R-carrier (get(...,None) is None <=> not present or value is None): (1) absent -> refresh+present; (2) present&None -> refresh+present; (3) present&non-None -> unchanged. All three agree with the real block bit-for-bit, and match the postconditions (Ensures(slot.present); refresh clause guarded by not(Old.present and Old.value is not None); keep clause otherwise). Object-identity 'is' holds because the store write binds the exact callee return and evaluate_marks is modeled deterministic. The spec is NOT too strong: it never claims more than the gold block delivers on any tested input, and the impl region literally IS the gold block (G-RESOLVE resolves). The single divergence (callee totality vs the real raising-condition path) is explicitly acknowledged in mapping.md directive-7 as an inert over-claim: the proof consumes only determinism, never totality, and no F2P/P2P test exercises a raising-condition mark. No spec-too-strong drift exists on any tested/resolution-relevant input. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged over the spec view (impl region elided) against the SOLVER-VISIBLE problem_statement only (not hints_text). Findings:

1. Mechanical screen (leakage.screen) PASSES with zero hard failures. Spec region confirmed frozen: same_spec(model, prepatch)=True; G-LEAK meta status=pass; no relaxed_leakage flag.

2. No diff markers, no reproduced gold-patch lines, no patched file path (src/_pytest/skipping.py) or module path in the spec view.

3. Patch-changed distinctive symbols are {evaluate_xfail_marks, pytest_runtest_call}. Neither appears in the spec view. The model uses abstract stand-ins: settle_saved_evaluation, SavedSlot, evaluate_marks. No spec-view identifier embeds either patched symbol; no comment/docstring names them.

4. No narration terms (bug/fix/regression/previously/...). 'xfail'/Xfail is already public via the problem_statement (pytest.mark.xfail), so it localizes no edit.

5. Semantic gold-reconstruction check: The gold edit is the post-yield re-evaluation block added to the pytest_runtest_call hook-wrapper, keyed on item._store[xfailed_key], honoring dynamically-added xfail marks. The spec view describes only the ABSTRACT input/output contract of settling a saved evaluation against the marks as they finally stand (keep an already-present non-empty saved value; otherwise re-evaluate the final marks; end present). This behavior is exactly what the public issue requests (a mark added during the body must be honored, as in 5.x). The spec reveals no edit location, no repo hook name, no store key, no post-yield placement, no diff structure. A solver could not reconstruct the specific gold edit from this abstraction beyond what the public problem_statement already discloses.

Conclusion: spec view abstracts the FIXED BEHAVIOR (which is public) without disclosing the gold edit's mechanism or location. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
