"""Twin-artifact model for pytest-dev__pytest-7236.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a std-library-style test case is executed under the interactive
  post-mortem debugging mode, the framework normally postpones the test case's
  teardown routine so that the debugger can inspect instance state: it records
  the teardown routine for an explicit later invocation and neutralises the
  immediate one. This postponement must happen ONLY for a test case that is
  actually going to run. A test case that has been marked to be skipped must
  never have its teardown routine recorded for that explicit later invocation,
  because a skipped test case's teardown must not be executed at all — the
  recorded routine is exactly what would otherwise be run during cleanup.

  Concretely the decision is: the teardown routine is recorded for explicit
  later invocation precisely when the post-mortem mode is active AND the test
  case is not marked-as-skipped. Whether a test case is marked-as-skipped is
  read from its skip marker: the marker counts as set when it is present with a
  truthy value, and counts as not-set when it is absent or present-but-falsy.

Booleans (the post-mortem-mode flag) are modelled directly; the skip marker is
modelled as an integer whose truthiness mirrors the marker's truthiness under
the default-absent lookup (0 = absent or falsy, non-zero = present and truthy).
The touched test-case object is a minimal class carrying only the marker, the
mode flag, and the resulting recorded-for-later flag.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class TestCaseItem:
    def __init__(self, postmortem_mode: bool, skip_marker: int) -> None:
        # Terminates: three unconditional field writes, no loop and no call.
        # Level 2 (not 1) leaves room beneath for any obligated callee, and sits
        # strictly below decide_teardown's level 6 so a caller can discharge it.
        Requires(MustTerminate(2))
        Ensures(Acc(self.postmortem_mode) and self.postmortem_mode is postmortem_mode)  # type: ignore
        Ensures(Acc(self.skip_marker) and self.skip_marker == skip_marker)  # type: ignore
        Ensures(Acc(self.teardown_recorded) and self.teardown_recorded == False)  # type: ignore
        self.postmortem_mode = postmortem_mode
        self.skip_marker = skip_marker
        self.teardown_recorded = False


# axioms-start
# (no @ContractOnly axioms: the marker lookup and the recording decision are
#  introduced by the change itself and are therefore modelled deeply below,
#  not axiomatized.)
# axioms-end


# pure-start
@Pure
def skip_marker_set(skip_marker: int) -> bool:
    """Whether the skip marker counts as set: it is set exactly when present
    with a truthy value. Under a default-absent lookup the marker reads as a
    value that is then reduced to its truthiness, so the marker counts as set
    iff that value is non-zero (0 = absent or present-but-falsy)."""
    return skip_marker != 0
# pure-end


def decide_teardown(item: TestCaseItem) -> None:
    # pre-conditions-start
    Requires(Acc(item.postmortem_mode, 1 / 2))
    Requires(Acc(item.skip_marker, 1 / 2))
    Requires(Acc(item.teardown_recorded))
    Requires(item.teardown_recorded == False)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(item.postmortem_mode, 1 / 2))
    Ensures(Acc(item.skip_marker, 1 / 2))
    Ensures(Acc(item.teardown_recorded))
    # The mode flag and the marker are read-only: they are unchanged.
    Ensures(item.postmortem_mode == Old(item.postmortem_mode))
    Ensures(item.skip_marker == Old(item.skip_marker))
    # The teardown routine is recorded for explicit later invocation precisely
    # when the post-mortem mode is active AND the test case is not skipped.
    Ensures(item.teardown_recorded == (item.postmortem_mode and not skip_marker_set(item.skip_marker)))
    # post-conditions-end
    # impl-start
    if item.postmortem_mode and not skip_marker_set(item.skip_marker):
        item.teardown_recorded = True
    # impl-end
