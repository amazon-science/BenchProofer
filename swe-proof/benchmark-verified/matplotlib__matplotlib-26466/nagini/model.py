"""Twin-artifact model for matplotlib__matplotlib-26466.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two construction-time helpers each accept a two-component (x, y) pair supplied
  by the caller and must retain that pair for the lifetime of the constructed
  object.

  The retained value must be an independently-owned pair whose two components
  are EXACTLY the two components of the input AT CONSTRUCTION TIME, carried
  through untransformed. Independence is required AT COMPONENT GRANULARITY, not
  merely at container granularity. The caller's two components live in two
  storage locations that belong to the caller and that the caller may overwrite
  IN PLACE at any time after construction returns; the retained pair must own
  its container AND own the two locations its components live in, so that none
  of the storage it reads back from is storage the caller can still write to.
  Each component value must be read OUT of the caller's location and kept in a
  location of the constructed object's own. Retaining the caller's container, or
  retaining any other arrangement that still reads its components back out of
  the caller's two locations, leaves the caller's later in-place overwrite
  observable through the retained pair and is therefore not a retention of the
  pair supplied at construction time.

The input is a two-element numeric container (an (x, y) pair that may be
supplied as a mutable array). Because whether the retained pair still reads its
components out of the caller's storage is precisely the behaviour under
specification, the per-component STORAGE LOCATION is modelled explicitly rather
than abstracted away: the carrier is a length-2 `List[Slot]`, where entry i is
the location holding component i and `Slot.value` is the component value stored
there. The component VALUES are modelled as OPAQUE, UNINTERPRETED objects
because the operation under specification reads and re-stores them without
applying ANY transformation to them, and the tested behaviour -- whether the
stored pair stays constant when the caller later mutates the input container --
is independent of the components' numeric type, precision, and value
(refinement.md row R-OPQ). The postcondition pins the retained component values
by IDENTITY (`Result()[i].value is pair[i].value`): the model carries the very
values it read, so an implementation that transforms a component in any way --
rounding, truncating, arithmetic that is lossy on real floating-point values --
cannot verify; on the opaque carrier no such transformation is even expressible.

Ownership is modelled by Nagini fractional permissions AT BOTH LEVELS. The
caller retains a read-only (fractional) share of its container AND of each of
its two component locations, i.e. it goes on owning them and may overwrite them
after the call. The constructed object owns, at FULL permission, both the
retained container and each of the two locations the retained components live
in. Full ownership of a location the caller still holds a read share of is
unsatisfiable, so "the retained pair reads a component back out of storage the
caller can still overwrite" is machine-checked per component, and a distinct
container object that nevertheless presents the caller's two component
locations is rejected exactly as the caller's own container is.

The operation is a bounded, loop-free construction-time step: it MUST terminate
(a total-correctness obligation, carried as ``MustTerminate`` in each
precondition). An implementation that diverges would satisfy the value and
permission postconditions only vacuously while construction hangs forever --
the object would never be built and nothing would ever be retained.

Two independent construction sites are each modelled as their own function with
its own contract and implementation (the per-function marker regions repeat);
there are no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Slot:
    """One storage location holding one component of a two-component pair.

    The carrier for "where a component lives", so that ownership of that
    location is expressible per component: permission to `value` is permission
    to the location, and a location whose `value` is held at full permission is
    one nobody else can overwrite.
    """

    def __init__(self, value: object) -> None:
        Requires(MustTerminate(1))
        self.value = value  # type: object
        Ensures(Acc(self.value) and self.value is value)


# axioms-start
# axioms-end


# pure-start
# pure-end


def retain_pair_a(pair: List[Slot]) -> List[Slot]:
    # pre-conditions-start
    # The caller owns its container and each of its two component locations, and
    # keeps a read share of all three across the call: after construction
    # returns it may overwrite either location in place.
    Requires(Acc(list_pred(pair), 1 / 2))
    Requires(len(pair) == 2)
    Requires(Acc(pair[0].value, 1 / 2))
    Requires(Acc(pair[1].value, 1 / 2))
    # Construction-time retention is a bounded step: it MUST terminate (total
    # correctness). A diverging implementation would satisfy the postconditions
    # only vacuously while construction hangs forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The caller keeps its read share of the input container AND of each of its
    # two component locations: the operation takes ownership of none of them and
    # may retain neither the container nor either location.
    Ensures(Acc(list_pred(pair), 1 / 2))
    Ensures(len(pair) == 2)
    Ensures(Acc(pair[0].value, 1 / 2))
    Ensures(Acc(pair[1].value, 1 / 2))
    # The retained pair is fully owned at BOTH levels: the container is the
    # constructed object's own, and so is each of the two locations its
    # components live in -- none of that storage is storage the caller still
    # holds a read share of and can overwrite in place. Each retained location
    # carries the component value present in the corresponding input location at
    # this moment, untransformed (pinned by identity on the opaque carrier).
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    Ensures(Acc(Result()[0].value))
    Ensures(Acc(Result()[1].value))
    Ensures(Result()[0].value is pair[0].value)
    Ensures(Result()[1].value is pair[1].value)
    # post-conditions-end
    # impl-start
    given0 = pair[0]
    x = given0.value  # type: object
    given1 = pair[1]
    y = given1.value  # type: object
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end


def retain_pair_b(pair: List[Slot]) -> List[Slot]:
    # pre-conditions-start
    Requires(Acc(list_pred(pair), 1 / 2))
    Requires(len(pair) == 2)
    Requires(Acc(pair[0].value, 1 / 2))
    Requires(Acc(pair[1].value, 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pair), 1 / 2))
    Ensures(len(pair) == 2)
    Ensures(Acc(pair[0].value, 1 / 2))
    Ensures(Acc(pair[1].value, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    Ensures(Acc(Result()[0].value))
    Ensures(Acc(Result()[1].value))
    Ensures(Result()[0].value is pair[0].value)
    Ensures(Result()[1].value is pair[1].value)
    # post-conditions-end
    # impl-start
    given0 = pair[0]
    x = given0.value  # type: object
    given1 = pair[1]
    y = given1.value  # type: object
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end
