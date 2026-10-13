# P2 adversarial audit — pytest-dev__pytest-7571

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -85,7 +82,7 @@
     Ensures(self.saved_level == Old(self.sink_level))
     # post-conditions-end
     # impl-start
-    self.saved_level = self.sink_level
+    # ATK1 prepatch bug: move sink but do NOT record restore point
     self.sink_level = level
     # impl-end
 
@@ -94,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -114,7 +110,6 @@
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -94,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -107,14 +103,13 @@
                     self.sink_level == Old(self.sink_level)))
     # post-conditions-end
     # impl-start
-    if self.saved_level is not None:
-        self.sink_level = self.saved_level
+    # ATK2 teardown no-op
+    pass
     # impl-end
 
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -85,8 +82,9 @@
     Ensures(self.saved_level == Old(self.sink_level))
     # post-conditions-end
     # impl-start
+    # ATK3 order swap: saved records the new level, not the old
+    self.sink_level = level
     self.saved_level = self.sink_level
-    self.sink_level = level
     # impl-end
 
 
@@ -94,7 +92,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -114,7 +111,6 @@
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -94,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -107,14 +103,13 @@
                     self.sink_level == Old(self.sink_level)))
     # post-conditions-end
     # impl-start
-    if self.saved_level is not None:
-        self.sink_level = self.saved_level
+    # ATK4 drop the None guard, restore unconditionally
+    self.sink_level = self.saved_level
     # impl-end
 
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -94,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -114,7 +110,6 @@
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
@@ -124,8 +119,6 @@
     Ensures(Result() == ambient)
     # post-conditions-end
     # impl-start
-    controller = CaptureController(ambient)
-    set_level(controller, level)
-    teardown_restore(controller)
-    return controller.sink_level
+    # ATK5 cheating driver: return ambient without composing ops
+    return ambient
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -94,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -107,14 +103,15 @@
                     self.sink_level == Old(self.sink_level)))
     # post-conditions-end
     # impl-start
+    # ATK6 correct restore, then null the unconstrained restore point
     if self.saved_level is not None:
         self.sink_level = self.saved_level
+    self.saved_level = None
     # impl-end
 
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -85,7 +82,9 @@
     Ensures(self.saved_level == Old(self.sink_level))
     # post-conditions-end
     # impl-start
-    self.saved_level = self.sink_level
+    # ATK7 echo: same effect via a temp local
+    old = self.sink_level
+    self.saved_level = old
     self.sink_level = level
     # impl-end
 
@@ -94,7 +93,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -114,7 +112,6 @@
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,7 +53,6 @@
 class CaptureController:
     def __init__(self, sink_level: int) -> None:
         # pre-conditions-start
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         # A freshly-created controller has recorded nothing to restore; the sink
@@ -72,7 +70,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -94,7 +91,6 @@
     # pre-conditions-start
     Requires(Acc(self.sink_level))
     Requires(Acc(self.saved_level))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.sink_level))
@@ -107,14 +103,14 @@
                     self.sink_level == Old(self.sink_level)))
     # post-conditions-end
     # impl-start
-    if self.saved_level is not None:
-        self.sink_level = self.saved_level
+    # ATK8 inverted guard: only touch sink when nothing recorded (no real restore)
+    if self.saved_level is None:
+        self.sink_level = self.sink_level
     # impl-end
 
 
 def run_raise_then_teardown(level: int, ambient: int) -> int:
     # pre-conditions-start
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # End-to-end teardown observable (the cross-test guarantee a following test
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-7571.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A log-capturing controller governs a capture sink whose acceptance threshold
  ("level") decides which records the sink keeps. Before any test code runs the
  sink sits at some ambient threshold. Test code may raise (or lower) that
  threshold through the controller's level-setting operation; the change must
  not leak into the next test. Concretely the controller must guarantee a clean
  round trip across one test's lifetime:

    (1) the level-setting operation records the sink's threshold AS IT WAS just
        before this operation changes it, and then moves the sink to the
        requested threshold; and

    (2) the end-of-test teardown, whenever a threshold change was performed,
        returns the sink's threshold to that recorded value — so a sink that a
        test raised to some threshold is observed back at its original ambient
        threshold by the following test, never stuck at the raised value.

  When no level-setting operation ran during the test, teardown leaves the sink
  untouched (nothing was recorded to restore).

The controller is modelled as a minimal object carrying only the two touched
facets: the sink's current threshold (``sink_level``, an ``int``) and the
recorded restore point (``saved_level``, ``Optional[int]`` with ``None`` meaning
"nothing recorded yet"). The sink's threshold accessor/mutator are ordinary
integer field reads/writes (the real sink's level getter/setter are unchanged
library accessors, modelled directly as the field). No callee is axiomatized:
the recorded-then-restored round trip is pure object/state logic, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the record-then-restore round trip is pure object/state
# logic, modelled deeply. The sink's level getter/setter are unchanged library
# integer accessors, modelled directly as a field read/write; their real
# semantics are validated out-of-band by axiom_check.py (G-AX) as a reference,
# not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class CaptureController:
    def __init__(self, sink_level: int) -> None:
        # pre-conditions-start
        # pre-conditions-end
        # post-conditions-start
        # A freshly-created controller has recorded nothing to restore; the sink
        # sits at its given ambient threshold.
        Ensures(Acc(self.sink_level) and self.sink_level == sink_level)    # type: ignore
        Ensures(Acc(self.saved_level) and self.saved_level is None)        # type: ignore
        # post-conditions-end
        # impl-start
        self.saved_level = None  # type: Optional[int]
        self.sink_level = sink_level  # type: int
        # impl-end


def set_level(self: CaptureController, level: int) -> None:
    # pre-conditions-start
    Requires(Acc(self.sink_level))
    Requires(Acc(self.saved_level))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.sink_level))
    Ensures(Acc(self.saved_level))
    # (1) the sink is moved to the requested threshold ...
    Ensures(self.sink_level == level)
    # ... and the threshold the sink held just before this operation is recorded
    # as the restore point.
    Ensures(self.saved_level is not None)
    Ensures(self.saved_level == Old(self.sink_level))
    # post-conditions-end
    # impl-start
    self.saved_level = self.sink_level
    self.sink_level = level
    # impl-end


def teardown_restore(self: CaptureController) -> None:
    # pre-conditions-start
    Requires(Acc(self.sink_level))
    Requires(Acc(self.saved_level))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.sink_level))
    Ensures(Acc(self.saved_level))
    # (2) when a restore point was recorded, teardown returns the sink to it;
    # when nothing was recorded the sink is left exactly as it was.
    Ensures(Implies(Old(self.saved_level) is not None,
                    self.sink_level == Old(self.saved_level)))
    Ensures(Implies(Old(self.saved_level) is None,
                    self.sink_level == Old(self.sink_level)))
    # post-conditions-end
    # impl-start
    if self.saved_level is not None:
        self.sink_level = self.saved_level
    # impl-end


def run_raise_then_teardown(level: int, ambient: int) -> int:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # End-to-end teardown observable (the cross-test guarantee a following test
    # sees): a fresh controller at the ambient threshold, raised to `level` by
    # one level-setting operation, is observed by teardown back at the ambient
    # threshold it started from -- never stuck at the raised `level`.
    Ensures(Result() == ambient)
    # post-conditions-end
    # impl-start
    controller = CaptureController(ambient)
    set_level(controller, level)
    teardown_restore(controller)
    return controller.sink_level
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: Env: PY=python, SBU_BENCHMARK_DIR=benchmark-verified, verifier env swebench-nagini-verifier.

SPEC ANALYSIS (frozen): every changed op is pinned. __init__ pins sink_level==param & saved_level is None. set_level pins sink_level==level, saved_level is not None, saved_level==Old(sink_level). teardown_restore pins sink_level in BOTH branches (Old(saved_level) if recorded else Old(sink_level)); saved_level after teardown is left UNCONSTRAINED. Driver run_raise_then_teardown pins only Result()==ambient, verified MODULARLY against callee contracts. Attack surface is narrow: only the unconstrained post-teardown saved_level and behaviourally-equivalent rewrites can verify.

POSITIVE CONTROL: positive_control.py = model.py verbatim -> `bash scripts/nagini_verify.sh` exit 0 (Verification successful, 20.8s).

ATTACKS (all same-spec exit 0; spec regions byte-identical, only impl region edited). Command per attack: `python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-7571 <atk>`:
- atk_1 (prepatch bug: set_level omits record) -> exit 2 REJECTED. Direct verify: 'Postcondition of set_level ... (self.saved_level is not None) might not hold' -> prepatch bug reproduced.
- atk_2 (teardown no-op) -> exit 2 REJECTED (recorded-branch restore violated).
- atk_3 (set_level order swap: saved records NEW level) -> exit 2 REJECTED (saved_level==Old(sink_level) fails).
- atk_4 (teardown drops None guard, unconditional restore) -> exit 2 REJECTED (None-branch sink-unchanged fails).
- atk_8 (teardown inverted guard: no real restore) -> exit 2 REJECTED.
- atk_5 (control-flow-effect: cheating driver `return ambient`, maps to no repo symbol) -> exit 0 CANDIDATE.
- atk_6 (teardown correct restore + null the unconstrained saved_level) -> exit 0 CANDIDATE.
- atk_7 (ungrounded-oracle echo: set_level records via temp local `old`) -> exit 0 CANDIDATE.

MANDATORY RESOLVE OF EVERY CANDIDATE (official harness run_resolve, SWE-bench Verified, max_workers 1, retries 1). Runner resolve_one.py; run concurrently (3 background jobs). Faithful refined patches materialized per refinement.md map:
- atk_5 patch_5.diff = gold verbatim (D1: driver has NO repo counterpart, refinement.md §D) -> [atk5] completed=True resolved=True attempts=1 flaky=False.
- atk_6 patch_6.diff = gold + `self._initial_handler_level = None` appended in _finalize (null of unconstrained field, no observable effect) -> [atk6] completed=True resolved=True.
- atk_7 patch_7.diff = gold with set_level record via `old = self.handler.level; self._initial_handler_level = old` (behaviourally identical) -> [atk7] completed=True resolved=True.
Every verifying candidate's faithful patch RESOLVES => verify does NOT contradict correct; no falsification of the spec.

REFINEMENT.MD AUDIT: all legs R / A-reference / I; NO kind-3, NO @ContractOnly axiom (spec is deep object/state model). A1(R+I), A2(R), B1(R), B2(R+A-ref handler.level read), B3(R+A-ref setLevel), C1(R+I), C2(R+A-ref), C3(R), D1(R+I, modular, no discriminating power). Cited gold lines all PRESENT in patch.diff (grep-confirmed). A-reference soundness (G-AX): Part1 (stdlib logging.Handler.level reads back setLevel over 12 boundary + 20000 fuzz) re-ran here exit 0; gold-transcription guard confirms in-process bodies == patch.diff; Part2 (real post-patch LogCaptureFixture round trip, 2000 obs incl F2P 0->41->0) recorded pass in meta.json (2026-07-29, in-container). axiom_check.py raised ModuleNotFoundError _pytest.store when run in the swebench-lean venv (pytest 6.0 absent) — pure env artifact, exactly the in-container-only condition; not a soundness failure.

Prior recorded G-EQ was INCONCLUSIVE (1 attack couldn't complete) — no named counterexample to re-encode; this pass ran all 8 attacks + 3 resolves to completion.

VERDICT: SOUND. >=5 attacks run; 5 rejected by the spec, 3 verifying candidates each resolve under the official harness; refinement fidelity and A-reference correspondence hold.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-7571.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A log-capturing controller governs a capture sink whose acceptance threshold
  ("level") decides which records the sink keeps. Before any test code runs the
  sink sits at some ambient threshold. Test code may raise (or lower) that
  threshold through the controller's level-setting operation; the change must
  not leak into the next test. Concretely the controller must guarantee a clean
  round trip across one test's lifetime:

    (1) the level-setting operation records the sink's threshold AS IT WAS just
        before this operation changes it, and then moves the sink to the
        requested threshold; and

    (2) the end-of-test teardown, whenever a threshold change was performed,
        returns the sink's threshold to that recorded value — so a sink that a
        test raised to some threshold is observed back at its original ambient
        threshold by the following test, never stuck at the raised value.

  When no level-setting operation ran during the test, teardown leaves the sink
  untouched (nothing was recorded to restore).

The controller is modelled as a minimal object carrying only the two touched
facets: the sink's current threshold (``sink_level``, an ``int``) and the
recorded restore point (``saved_level``, ``Optional[int]`` with ``None`` meaning
"nothing recorded yet"). The sink's threshold accessor/mutator are ordinary
integer field reads/writes (the real sink's level getter/setter are unchanged
library accessors, modelled directly as the field). No callee is axiomatized:
the recorded-then-restored round trip is pure object/state logic, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the record-then-restore round trip is pure object/state
# logic, modelled deeply. The sink's level getter/setter are unchanged library
# integer accessors, modelled directly as a field read/write; their real
# semantics are validated out-of-band by axiom_check.py (G-AX) as a reference,
# not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class CaptureController:
    def __init__(self, sink_level: int) -> None:
        # pre-conditions-start
        # pre-conditions-end
        # post-conditions-start
        # A freshly-created controller has recorded nothing to restore; the sink
        # sits at its given ambient threshold.
        Ensures(Acc(self.sink_level) and self.sink_level == sink_level)    # type: ignore
        Ensures(Acc(self.saved_level) and self.saved_level is None)        # type: ignore
        # post-conditions-end
        # impl-start
        self.saved_level = None  # type: Optional[int]
        self.sink_level = sink_level  # type: int
        # impl-end


def set_level(self: CaptureController, level: int) -> None:
    # pre-conditions-start
    Requires(Acc(self.sink_level))
    Requires(Acc(self.saved_level))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.sink_level))
    Ensures(Acc(self.saved_level))
    # (1) the sink is moved to the requested threshold ...
    Ensures(self.sink_level == level)
    # ... and the threshold the sink held just before this operation is recorded
    # as the restore point.
    Ensures(self.saved_level is not None)
    Ensures(self.saved_level == Old(self.sink_level))
    # post-conditions-end
    # impl-start
    self.saved_level = self.sink_level
    self.sink_level = level
    # impl-end


def teardown_restore(self: CaptureController) -> None:
    # pre-conditions-start
    Requires(Acc(self.sink_level))
    Requires(Acc(self.saved_level))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.sink_level))
    Ensures(Acc(self.saved_level))
    # (2) when a restore point was recorded, teardown returns the sink to it;
    # when nothing was recorded the sink is left exactly as it was.
    Ensures(Implies(Old(self.saved_level) is not None,
                    self.sink_level == Old(self.saved_level)))
    Ensures(Implies(Old(self.saved_level) is None,
                    self.sink_level == Old(self.sink_level)))
    # post-conditions-end
    # impl-start
    if self.saved_level is not None:
        self.sink_level = self.saved_level
    # impl-end


def run_raise_then_teardown(level: int, ambient: int) -> int:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # End-to-end teardown observable (the cross-test guarantee a following test
    # sees): a fresh controller at the ambient threshold, raised to `level` by
    # one level-setting operation, is observed by teardown back at the ambient
    # threshold it started from -- never stuck at the raised `level`.
    Ensures(Result() == ambient)
    # post-conditions-end
    # impl-start
    controller = CaptureController(ambient)
    set_level(controller, level)
    teardown_restore(controller)
    return controller.sink_level
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: Env: PY=python, SBU_BENCHMARK_DIR=benchmark-verified, verifier env swebench-nagini-verifier.

SPEC ANALYSIS (frozen): every changed op is pinned. __init__ pins sink_level==param & saved_level is None. set_level pins sink_level==level, saved_level is not None, saved_level==Old(sink_level). teardown_restore pins sink_level in BOTH branches (Old(saved_level) if recorded else Old(sink_level)); saved_level after teardown is left UNCONSTRAINED. Driver run_raise_then_teardown pins only Result()==ambient, verified MODULARLY against callee contracts. Attack surface is narrow: only the unconstrained post-teardown saved_level and behaviourally-equivalent rewrites can verify.

POSITIVE CONTROL: positive_control.py = model.py verbatim -> `bash scripts/nagini_verify.sh` exit 0 (Verification successful, 20.8s).

ATTACKS (all same-spec exit 0; spec regions byte-identical, only impl region edited). Command per attack: `python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-7571 <atk>`:
- atk_1 (prepatch bug: set_level omits record) -> exit 2 REJECTED. Direct verify: 'Postcondition of set_level ... (self.saved_level is not None) might not hold' -> prepatch bug reproduced.
- atk_2 (teardown no-op) -> exit 2 REJECTED (recorded-branch restore violated).
- atk_3 (set_level order swap: saved records NEW level) -> exit 2 REJECTED (saved_level==Old(sink_level) fails).
- atk_4 (teardown drops None guard, unconditional restore) -> exit 2 REJECTED (None-branch sink-unchanged fails).
- atk_8 (teardown inverted guard: no real restore) -> exit 2 REJECTED.
- atk_5 (control-flow-effect: cheating driver `return ambient`, maps to no repo symbol) -> exit 0 CANDIDATE.
- atk_6 (teardown correct restore + null the unconstrained saved_level) -> exit 0 CANDIDATE.
- atk_7 (ungrounded-oracle echo: set_level records via temp local `old`) -> exit 0 CANDIDATE.

MANDATORY RESOLVE OF EVERY CANDIDATE (official harness run_resolve, SWE-bench Verified, max_workers 1, retries 1). Runner resolve_one.py; run concurrently (3 background jobs). Faithful refined patches materialized per refinement.md map:
- atk_5 patch_5.diff = gold verbatim (D1: driver has NO repo counterpart, refinement.md §D) -> [atk5] completed=True resolved=True attempts=1 flaky=False.
- atk_6 patch_6.diff = gold + `self._initial_handler_level = None` appended in _finalize (null of unconstrained field, no observable effect) -> [atk6] completed=True resolved=True.
- atk_7 patch_7.diff = gold with set_level record via `old = self.handler.level; self._initial_handler_level = old` (behaviourally identical) -> [atk7] completed=True resolved=True.
Every verifying candidate's faithful patch RESOLVES => verify does NOT contradict correct; no falsification of the spec.

REFINEMENT.MD AUDIT: all legs R / A-reference / I; NO kind-3, NO @ContractOnly axiom (spec is deep object/state model). A1(R+I), A2(R), B1(R), B2(R+A-ref handler.level read), B3(R+A-ref setLevel), C1(R+I), C2(R+A-ref), C3(R), D1(R+I, modular, no discriminating power). Cited gold lines all PRESENT in patch.diff (grep-confirmed). A-reference soundness (G-AX): Part1 (stdlib logging.Handler.level reads back setLevel over 12 boundary + 20000 fuzz) re-ran here exit 0; gold-transcription guard confirms in-process bodies == patch.diff; Part2 (real post-patch LogCaptureFixture round trip, 2000 obs incl F2P 0->41->0) recorded pass in meta.json (2026-07-29, in-container). axiom_check.py raised ModuleNotFoundError _pytest.store when run in the swebench-lean venv (pytest 6.0 absent) — pure env artifact, exactly the in-container-only condition; not a soundness failure.

Prior recorded G-EQ was INCONCLUSIVE (1 attack couldn't complete) — no named counterexample to re-encode; this pass ran all 8 attacks + 3 resolves to completion.

VERDICT: SOUND. >=5 attacks run; 5 rejected by the spec, 3 verifying candidates each resolve under the official harness; refinement fidelity and A-reference correspondence hold.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-repo) check for pytest-dev__pytest-7571 nagini bundle. The spec models the gold fix to LogCaptureFixture: set_level records the sink's pre-change threshold then moves it (Ensures sink_level==level ∧ saved_level==Old(sink_level)); teardown_restore returns the sink to the recorded threshold when one exists, else leaves it; run_raise_then_teardown(level,ambient)==ambient pins the cross-test observable. The single abstraction is R-refinement: logging.Handler.level (int attribute) ↔ sink_level:int, handler.setLevel(L) ↔ sink_level=L. Fidelity rests on setLevel storing _checkLevel(L), which is identity on ints — I fuzzed _checkLevel over 200,000 values across [-1e9,1e9] incl. negatives/extremes: ZERO divergence; also confirmed on the test's odd values 41/43/0/50. G-AX part (1) (stdlib logging round trip over 12 boundary + 20000 fuzz thresholds) passes; part (2) (real post-patch LogCaptureFixture set_level/_finalize round trip) is a verbatim, patch.diff-guarded transcription and only SKIPs here because _pytest is not importable in the audit shell (a permitted skip; base worktree lacks the 'py' dep). Model verifies under pinned Nagini (Verification successful, 17.85s). Spec region is byte-identical to the bundle (same-spec harness: SAME, exit 0). No 'spec too strong' defect: the modeled postconditions are exactly the gold behavior on the tested integer domain, and no input exists where the modeled functions disagree with the real callee. String-level inputs are outside the typed int domain (a narrowing consistent with the tested levels), not a disagreement. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over spec_view(model.py)) PASSES with zero hard failures: no diff markers, no gold-patch line reproduced (>=8 char normalized), no patched file path (src/_pytest/logging.py) or module path, no narration terms (bug/fix/regression/previously/etc.), and no spec-view identifier/comment embedding a distinctive patched repo symbol. Patch-changed distinctive symbols are {finalize, set_level}: 'set_level' appears verbatim in the public problem_statement (caplog.set_level(42)) so it is public, not a leak; '_finalize'/'_initial_handler_level' never appear in the spec view (only in auditor docs refinement.md/mapping.md, which are NOT the consumer spec view).

Semantic review beyond the lexical screen: the spec-view identifiers are fully abstracted (CaptureController, sink_level, saved_level, teardown_restore, run_raise_then_teardown) and name no patched repo symbol or file. The behaviour is stated as desired behaviour, not as an edit: (1) the level-setter records the prior threshold and moves to the requested one; (2) teardown restores the recorded value; no-set => untouched. This is the natural formalization of the PUBLIC problem_statement requirement ('The log levels set are restored automatically at the end of the test'; currently prints 42 instead of 0 for caplog.handler.level). The public statement already exposes the fixture, set_level, the handler level, and the restore-at-teardown requirement. Deriving a save-then-restore round trip from that public requirement is expected solver work, not gold-edit leakage. The specific gold mechanism (_initial_handler_level field, self.handler.setLevel, _finalize) is confined to the auditor-only refinement/mapping docs. No spec-view line reveals the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
