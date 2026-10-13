"""Twin-artifact model for pydata__xarray-3993.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A coordinate-consuming operation accepts the coordinate it works along through
  a primary selector, while also continuing to accept the same selection through
  a now-superseded alternate selector that is kept only for backward
  compatibility. The desired routing of a single call is:

    * Supplying BOTH selectors at once is contradictory and is refused: the
      call signals the caller with a conflicting-selection failure and performs
      no computation.
    * Supplying ONLY the alternate (legacy) selector is still honoured: the
      computation proceeds along exactly that coordinate, but the call must also
      raise a forward-looking deprecation signal advising the caller to migrate
      to the primary selector.
    * Supplying ONLY the primary selector proceeds along that coordinate with
      no deprecation signal.

  The coordinate the computation is actually carried out along is, in every
  honoured case, exactly the one named by whichever single selector was supplied
  (the legacy selector when only it is given, the primary selector otherwise).

  The behaviour pinned here is the SELECTION ROUTING and its two signals: the
  refusal on a double selection, and — the discriminating obligation — that a
  call made through the legacy selector alone both proceeds along that
  coordinate AND emits the deprecation signal (which a call through the primary
  selector does not).

A coordinate selector is modelled abstractly by an integer identifier, with
``None`` meaning "not supplied"; the work the call then performs along the chosen
coordinate is unchanged and unobserved here. The conflicting-selection failure
is a user-defined exception class (a builtin exception in an ``Exsures`` crashes
the Nagini translator). The honoured-call outcome is a small result object
carrying the coordinate chosen and whether the deprecation signal was emitted.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ConflictingSelection(Exception):
    """The conflicting-selection failure surfaced to the caller when BOTH the
    primary and the legacy selector are supplied at once. User-defined stand-in
    for the value-error the desired behaviour requires (a builtin exception in
    an ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass


class Routed:
    """Observable outcome of an honoured call (mapping.md §2):

      * ``coord`` is the coordinate identifier the call actually works along —
        the single selector that was supplied.
      * ``deprecated`` is whether the forward-looking deprecation signal was
        emitted on this call (True exactly when the call was made through the
        legacy selector alone)."""

    def __init__(self, coord: Optional[int], deprecated: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.coord) and Acc(self.deprecated))
        Ensures(self.coord is coord and self.deprecated == deprecated)
        self.coord = coord            # type: Optional[int]
        self.deprecated = deprecated  # type: bool


# axioms-start
# (no axiomatized callee: the changed function reads only its two selector
#  arguments and routes them; the work it then performs along the chosen
#  coordinate is unchanged, independent of the routing decision, and unobserved
#  by this specification.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the routing decision is stated inline
#  over the two selector arguments.)
# pure-end


def select_coordinate(coord: Optional[int], dim: Optional[int]) -> Routed:
    # pre-conditions-start
    # The two selectors are abstract coordinate identifiers; ``None`` means the
    # selector was not supplied. ``coord`` is the primary selector, ``dim`` the
    # superseded legacy selector. Plain Optional[int] values, no heap permission.
    # TERMINATION: every honoured call must actually ANSWER (return its routed
    # outcome) and every refused call must actually raise — the routing decision
    # is a bounded prologue over two arguments. Without this obligation a
    # non-terminating implementation (e.g. one that diverges on the
    # primary-selector path instead of proceeding) satisfies every Ensures
    # vacuously; the real behaviour requires the call to complete.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # A normal return is reachable only when at most one selector is supplied
    # (supplying both is the refused case, below).
    Ensures(not (dim is not None and coord is not None))
    Ensures(Acc(Result().coord) and Acc(Result().deprecated))
    # ROUTING: the call works along exactly the single selector that was supplied
    # — the legacy selector when only it is given, the primary selector otherwise.
    Ensures(Implies(dim is not None and coord is None, Result().coord is dim))
    Ensures(Implies(not (dim is not None and coord is None), Result().coord is coord))
    # DEPRECATION SIGNAL: a call made through the legacy selector alone both
    # proceeds (returns normally, above) AND emits the deprecation signal; a call
    # through the primary selector (or with neither) does NOT emit it. This is
    # the discriminating obligation the behaviour change introduces.
    Ensures(Result().deprecated == (dim is not None and coord is None))
    # REFUSAL: supplying both selectors at once is contradictory and must NOT
    # return normally — it is surfaced as the conflicting-selection failure, and
    # ONLY then.
    Exsures(ConflictingSelection, dim is not None and coord is not None)
    # post-conditions-end
    # impl-start
    if dim is not None and coord is not None:
        raise ConflictingSelection()

    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True

    return Routed(coord, deprecated)
    # impl-end
