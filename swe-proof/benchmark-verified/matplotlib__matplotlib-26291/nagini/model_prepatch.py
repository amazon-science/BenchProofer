"""Twin-artifact model for matplotlib__matplotlib-26291.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A positioning callable computes the placement of an inset region. It is
  invoked with an axes and, optionally, a drawing context (a renderer).
  Some callers — for instance one that measures a figure's contents while
  saving it — invoke the callable WITHOUT a drawing context (the context
  argument is absent).

  Computing the placement requires a usable drawing context: the extent and
  offset of the region can only be measured against a present (non-absent)
  drawing context.

  The behaviour required of the callable:

    (1) When invoked WITHOUT a drawing context, it must still perform the
        measurement against a present (non-absent) drawing context — namely
        the one resolved from the host axes by the unchanged drawing-context
        source (not an arbitrary substitute context).

    (2) When invoked WITH a drawing context, it performs the measurement
        against the supplied context unchanged.

  In both cases the measurement is performed exactly once against a present
  (non-absent) drawing context; when a context was supplied it is the supplied
  one, and when none was supplied it is the one the host axes resolves.

The drawing context is modelled as ``Optional[int]`` (absent is ``None``;
present is an opaque positive handle). When none is supplied, a present context
is obtained from an unchanged opaque primitive, axiomatized to always yield a
present handle; the measurement is pinned to exactly that resolved context. The
measurement is an unchanged opaque primitive whose precondition is that it is
handed a present context; it is run exactly once and records the handle it was
handed, so "measured against the resolved present context" is stated exactly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def axes_context(ax: int) -> int:
    """The unchanged drawing-context source used when no context is supplied.
    It always yields a PRESENT handle — a positive opaque code, never the
    absent sentinel. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Ensures(Result() > 0)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


class Locator:
    def __init__(self) -> None:
        Ensures(Acc(self.measurements) and self.measurements == 0)  # type: ignore
        Ensures(Acc(self.measured_with) and self.measured_with == 0)  # type: ignore
        self.measurements = 0  # type: int
        # The handle the measurement primitive was last handed (0 = the
        # measurement has not run yet; present handles are positive).
        self.measured_with = 0  # type: int


def measure(self: Locator, context: int) -> None:
    # pre-conditions-start
    # The measurement can only be performed against a PRESENT drawing context.
    # (Modelled as: the handle must be a present, positive code. The absent
    # sentinel None is not even of this parameter's type — handing None here is
    # rejected statically, mirroring the real measurement dereferencing a
    # context that, when absent, is not recoverable on this object.)
    Requires(Acc(self.measurements) and Acc(self.measured_with))
    Requires(context > 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.measurements) and Acc(self.measured_with)
            and self.measurements == Old(self.measurements) + 1
            and self.measured_with == context)
    # post-conditions-end
    # impl-start
    self.measurements = self.measurements + 1
    self.measured_with = context
    # impl-end


def call(self: Locator, ax: int, renderer: Optional[int]) -> None:
    # pre-conditions-start
    Requires(Acc(self.measurements) and Acc(self.measured_with))
    Requires(self.measurements == 0)
    # A supplied drawing context, when present, is a present (positive) handle.
    Requires(Implies(renderer is not None, renderer > 0))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.measurements) and Acc(self.measured_with))
    # The measurement is performed exactly once...
    Ensures(self.measurements == 1)
    # ...against a PRESENT drawing context...
    Ensures(self.measured_with > 0)
    # ...which is the supplied one when one was supplied,
    Ensures(Implies(renderer is not None, self.measured_with == renderer))
    # ...and otherwise (no context supplied) exactly the one the host axes
    # resolves via the unchanged drawing-context source — not an arbitrary
    # substitute present context.
    Ensures(Implies(renderer is None, self.measured_with == axes_context(ax)))
    # post-conditions-end
    # impl-start
    # Pre-patch: the supplied drawing context is threaded straight into the
    # measurement. When it is absent, no present context is resolved, so the
    # measurement is attempted against an absent context (the 0 sentinel).
    eff = renderer  # type: Optional[int]
    if eff is None:
        measure(self, 0)
    else:
        measure(self, eff)
    # impl-end
