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
from nagini_contracts.obligations import MustTerminate


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
        Requires(MustTerminate(2))
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
    Requires(MustTerminate(2))
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
    # Pre-patch skeleton: the sink is moved to the requested threshold, but the
    # threshold it held just before is NOT recorded as a restore point.
    self.sink_level = level
    # impl-end


def teardown_restore(self: CaptureController) -> None:
    # pre-conditions-start
    Requires(Acc(self.sink_level))
    Requires(Acc(self.saved_level))
    Requires(MustTerminate(2))
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
    # Pre-patch skeleton: teardown does NOT return the sink's threshold to the
    # recorded restore point; the sink is left at whatever the test raised it to.
    # impl-end


def run_raise_then_teardown(level: int, ambient: int) -> int:
    # pre-conditions-start
    Requires(MustTerminate(3))
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
