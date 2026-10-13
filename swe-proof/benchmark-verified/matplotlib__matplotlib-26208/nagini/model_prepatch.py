"""Twin-artifact model for matplotlib__matplotlib-26208.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Each builder takes a source coordinate axis and returns a freshly built
  companion coordinate axis. When the source axis carries a non-None descriptor
  object, the returned companion axis must reference that very same descriptor
  object (reference identity, not merely an equal value), and therefore must
  itself be non-None.

  A newly constructed axis carries no descriptor (its descriptor is None).

The behaviour is exercised through two governed builder functions. Each is
modelled as its own contracted+implemented function, so each has its own
differential witness.

Modelling: a coordinate axis is a minimal object with only the touched field —
its descriptor reference. The descriptor itself is an opaque object whose only
relevant property is its identity, so it is modelled as a bare object
(`UnitDescriptor`); the specification pins reference identity (`is`), exactly
what the observable behaviour demands.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the modelled change is a pure object-field
# propagation, spelled out directly; nothing the proof relies on is opaque.)
# axioms-end


# pure-start
class UnitDescriptor:
    """An opaque descriptor object. Only its object identity is observable."""

    def __init__(self) -> None:
        # level 1: the lowest level, so any obligated caller (level > 1) has
        # room beneath it; the body is straight-line and loop-free.
        Requires(MustTerminate(1))
        Ensures(Acc(self.present) and self.present)
        self.present = True  # type: bool


class CoordinateAxis:
    """A coordinate axis carrying only the touched field: its descriptor
    reference. A freshly constructed axis has no descriptor (None)."""

    def __init__(self) -> None:
        # level 1: the lowest level, so any obligated caller (level > 1) has
        # room beneath it; the body is straight-line and loop-free.
        Requires(MustTerminate(1))
        Ensures(Acc(self.descriptor) and self.descriptor is None)
        self.descriptor = None  # type: Optional[UnitDescriptor]
# pure-end


def build_companion_sharing_horizontal(
        source_horizontal: CoordinateAxis) -> CoordinateAxis:
    # pre-conditions-start
    Requires(Acc(source_horizontal.descriptor, 1 / 2))
    Requires(source_horizontal.descriptor is not None)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(source_horizontal.descriptor, 1 / 2))
    Ensures(source_horizontal.descriptor is not None)
    Ensures(Acc(Result().descriptor))
    # the companion's shared axis references the SAME descriptor object
    Ensures(Result().descriptor is source_horizontal.descriptor)
    Ensures(Result().descriptor is not None)
    # post-conditions-end
    # impl-start
    companion_horizontal = CoordinateAxis()
    return companion_horizontal
    # impl-end


def build_companion_sharing_vertical(
        source_vertical: CoordinateAxis) -> CoordinateAxis:
    # pre-conditions-start
    Requires(Acc(source_vertical.descriptor, 1 / 2))
    Requires(source_vertical.descriptor is not None)
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(source_vertical.descriptor, 1 / 2))
    Ensures(source_vertical.descriptor is not None)
    Ensures(Acc(Result().descriptor))
    # the companion's shared axis references the SAME descriptor object
    Ensures(Result().descriptor is source_vertical.descriptor)
    Ensures(Result().descriptor is not None)
    # post-conditions-end
    # impl-start
    companion_vertical = CoordinateAxis()
    companion_vertical.descriptor = source_vertical.descriptor
    return companion_vertical
    # impl-end
