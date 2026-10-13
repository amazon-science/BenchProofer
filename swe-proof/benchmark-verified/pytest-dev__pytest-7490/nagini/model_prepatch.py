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
from nagini_contracts.obligations import MustTerminate


class Xfail:
    """Minimal model of an evaluated expected-failure mark (only the field the
    downstream classification branches on is carried)."""

    def __init__(self, run: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.run) and self.run is run)  # type: ignore
        self.run = run


class SavedSlot:
    """The saved expected-failure evaluation that classification consumes.
    ``present`` is whether anything is saved; ``value`` is the saved evaluation
    (possibly an empty/``None`` evaluation even when present)."""

    def __init__(self, present: bool, value: Optional[Xfail]) -> None:
        Requires(MustTerminate(1))
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
    Requires(MustTerminate(6))
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
    # This variant leaves the saved evaluation exactly as it stood on entry, so
    # an evaluation that only becomes meaningful once the marks finally stand is
    # not picked up.
    pass
    # impl-end
