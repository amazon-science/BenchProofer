"""Twin-artifact model for django__django-13516.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A thin text-output wrapper forwards a buffer-draining request to the
  underlying stream it wraps. The request must reach the underlying stream:
  draining the wrapper drains the wrapped stream.

    (1) When the wrapped stream supports draining (it exposes a drain
        primitive), draining the wrapper invokes that underlying drain
        primitive exactly once. Any buffered output the wrapped stream holds is
        therefore pushed out immediately, rather than only when the program
        ends.

    (2) When the wrapped stream does NOT support draining, draining the wrapper
        is a harmless no-op: it completes normally and changes nothing.

  In both cases the wrapper itself is left exactly as it was -- it still wraps
  the same underlying stream and still reports the same drain-capability.

The wrapper is modelled as a minimal object exposing only the two touched
pieces of state: a reference to the underlying stream, and whether that stream
supports draining (a cached capability bit), captured as a bool. The underlying
drain primitive's observable effect -- that it was invoked -- is carried by a
monotone invocation count on the underlying stream; one invocation increments
it by one. That count is held behind an abstraction predicate and read only via
a pure accessor, so it can advance ONLY by running the underlying drain
primitive -- it cannot be fabricated by writing the count directly. The
whether-it-supports-draining probe is read directly off the modelled capability
bit; the underlying drain primitive's effect is modelled deeply (the count
bump) and validated against the real stream's drain primitive out-of-band by
axiom_check.py (G-AX, an A-reference), not consumed as a contract axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The capability probe (does the underlying stream support
# draining) is a pure boolean read off the modelled state, and the underlying
# drain primitive's observable effect (it was invoked) is modelled DEEPLY as a
# monotone count bump rather than axiomatized. The real underlying drain
# primitive is validated == this deep model out-of-band by axiom_check.py (G-AX)
# as an A-reference.
# axioms-end


class Sink:
    """The underlying stream the wrapper wraps. The only observable piece of
    state for this behaviour is how many times its drain primitive has been
    invoked (a monotone count). The count is held behind an abstraction
    predicate and exposed only through a pure accessor, so it advances ONLY by
    running the drain primitive -- never by writing the count directly."""

    # pure-start
    @Predicate
    def drain_count_pred(self) -> bool:
        # Abstraction over the underlying stream's invocation count: a holder
        # may observe the count (via get_drained) but cannot write it without
        # going through the drain primitive (do_drain), which is the only
        # operation permitted to unfold/advance/refold it.
        return Acc(self.drained)

    @Pure
    def get_drained(self) -> int:
        # Read the invocation count through the abstraction (fractional, so the
        # count can be observed in a postcondition without granting the power to
        # change it).
        Requires(Acc(self.drain_count_pred(), 1 / 2))
        return Unfolding(Acc(self.drain_count_pred(), 1 / 2), self.drained)
    # pure-end

    def __init__(self) -> None:
        Requires(MustTerminate(6))
        Ensures(self.drain_count_pred() and self.get_drained() == 0)  # type: ignore
        self.drained = 0  # type: int
        Fold(self.drain_count_pred())

    def do_drain(self) -> None:
        # The underlying stream's drain primitive: its sole observable effect is
        # that it ran (the invocation count advances by one). This is the ONLY
        # operation that may advance the count. It is bounded work: it promises
        # termination to its callers.
        Requires(MustTerminate(2))
        Requires(self.drain_count_pred())
        Ensures(self.drain_count_pred())
        Ensures(self.get_drained() == Old(self.get_drained()) + 1)
        Unfold(self.drain_count_pred())
        self.drained = self.drained + 1
        Fold(self.drain_count_pred())


class OutputStream:
    """The text-output wrapper. It holds a reference to the underlying stream
    (`out`) and the cached capability bit (`out_can_drain`) recording whether
    the underlying stream supports draining."""

    def __init__(self, out: Sink, out_can_drain: bool) -> None:
        Requires(MustTerminate(6))
        Requires(Acc(out.drain_count_pred(), 1 / 2))
        Ensures(Acc(self.out) and self.out is out)  # type: ignore
        Ensures(Acc(self.out_can_drain) and self.out_can_drain == out_can_drain)  # type: ignore
        Ensures(Acc(self.out.drain_count_pred(), 1 / 2))  # type: ignore
        self.out = out  # type: Sink
        self.out_can_drain = out_can_drain  # type: bool


def drain_buffer(stream: OutputStream) -> None:
    # pre-conditions-start
    # The wrapper itself is read-only (its underlying-stream reference and its
    # drain-capability bit are not changed) -> fractional permission. The
    # underlying stream's invocation count IS advanced -> full predicate.
    Requires(Acc(stream.out, 1 / 2))
    Requires(Acc(stream.out_can_drain, 1 / 2))
    Requires(stream.out.drain_count_pred())
    # Draining the wrapper is bounded work (at most one forwarded invocation),
    # so it must TERMINATE: without this obligation the postconditions could be
    # discharged vacuously by a body that never returns.
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(stream.out, 1 / 2))
    Ensures(Acc(stream.out_can_drain, 1 / 2))
    Ensures(stream.out.drain_count_pred())
    # The wrapper is unchanged: same underlying stream, same capability bit.
    Ensures(stream.out is Old(stream.out))
    Ensures(stream.out_can_drain == Old(stream.out_can_drain))
    # (1) the underlying drain primitive is invoked exactly once iff the wrapped
    #     stream supports draining ... (the count is observed through the
    #     abstraction, so this clause is dischargeable only by running the
    #     primitive, never by writing the count).
    Ensures(Implies(stream.out_can_drain,
                    stream.out.get_drained() == Old(stream.out.get_drained()) + 1))
    # (2) ... and is left untouched (a harmless no-op) otherwise.
    Ensures(Implies(not stream.out_can_drain,
                    stream.out.get_drained() == Old(stream.out.get_drained())))
    # post-conditions-end
    # impl-start
    if stream.out_can_drain:
        stream.out.do_drain()
    # impl-end
