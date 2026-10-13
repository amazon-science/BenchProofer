"""Twin-artifact model for django__django-14011.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A threaded request server runs each request on its own worker thread, and each
  worker thread keeps a per-thread registry of live database connections. For the
  worker threads to operate on the SAME data the parent prepared (rather than on
  fresh, empty connections of their own), the server must be configurable with a
  parent-supplied set of connections, and that supplied set must reach the worker
  thread. Two guarantees describe the worker-thread lifecycle.

  (1) Connection hand-off into the worker thread (the discriminating behaviour).
      The server can be CONFIGURED with a parent-supplied set of connections.
      Configuration is a step that can FAIL: a server that cannot be configured
      with such a set leaves it UNAVAILABLE, and then nothing the worker does can
      make the parent-supplied connections reach the worker thread's registry.
      The desired behaviour is therefore: configuring the server with the
      parent-supplied set must SUCCEED, so that the set becomes available; and a
      worker thread, when handling a request, makes the available parent-supplied
      connections take effect in its registry (each supplied alias's entry is set
      to the supplied connection; aliases with no override are left as they were).
      A server whose configuration did not make the set available cannot have a
      worker that operates on the parent-supplied connections.

  (2) Connection teardown after a request (a secondary, non-discriminating
      behaviour). When the server finishes cleaning up an individual request,
      every database connection in that worker thread's registry must be left
      CLOSED, and the request resource itself must be released. Releasing the
      request resource alone is not sufficient: a connection that was still open
      when the request finished must end up closed. The connections are closed
      BEFORE the request resource is released.

Modelling choices (Nagini fragment):
  * A worker thread's connection registry is modelled as two index-aligned
    `List`s over the registry's aliases: `closed[i]` (a `bool`: is alias i's
    connection currently closed?) and `tokens[i]` (an `int`: the identity of the
    connection object currently bound to alias i). Aliases are positions.
  * The "request resource" is a minimal object carrying only its released flag.
  * The parent-supplied set is an index-aligned pair: `has_override[i]` (was a
    connection supplied for alias i?) and `override_tokens[i]` (the identity of
    the supplied connection for alias i).
  * "The server was configured so the parent-supplied set is available to the
    worker" is NOT a copyable value (configuring either succeeds or fails; the
    stored references would look identical either way, so no value witnesses it).
    It is modelled as an abstract, unforgeable per-server CAPABILITY
    `connections_handed_off(server)` -- an opaque `@ContractOnly @Predicate` with
    no body. Nothing can `Fold` it into existence, and a capability for some other
    server does not discharge it. Its SOLE producer is the configuration step
    (`accept_connection_set`'s `Ensures`): the capability can be held only by
    actually performing the configuration that accepts the supplied set. The
    worker-handling step REQUIRES it, so a worker can operate on the
    parent-supplied connections only when the server was configured to accept
    them -- exactly the control-flow effect that distinguishes a server able to
    accept the set from one that cannot be configured with the set at all.
  * Closing every connection in the registry is modelled deeply as the per-alias
    state transition "every connection becomes closed"; the unchanged
    request-release primitive only releases the request and never touches the
    registry.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Server:
    """The worker request server. It carries no readable configuration value:
    whether it was configured to accept the parent-supplied connection set is the
    abstract per-server capability `connections_handed_off(server)` below, not a
    field an implementation could copy or set by fiat."""

    def __init__(self) -> None:
        Ensures(True)


# axioms-start
# Abstract, unforgeable per-server capability: holding `connections_handed_off(s)`
# means server `s` was CONFIGURED so the parent-supplied connection set is
# available to its worker threads. It is an opaque `@ContractOnly @Predicate` with
# NO body. Consequences:
#   * an implementation cannot `Fold` it into existence (no body to fold), so the
#     "configured / available" fact cannot be fabricated by fiat;
#   * it names the specific server `s`, so a capability obtained for a different
#     server does not discharge `connections_handed_off(s)`.
# The SOLE producer is `accept_connection_set`'s `Ensures` (the configuration
# step that accepts the supplied set). This is the directive-8 / control-flow
# grounding of the "available" fact: configuring a server with the set either
# succeeds (capability granted) or is impossible (a server that cannot be
# configured with the set), with no value-level witness either way. Provenance +
# executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def connections_handed_off(server: Server) -> bool:
    pass


@ContractOnly
def accept_connection_set(
    server: Server, has_override: List[bool], override_tokens: List[int]
) -> None:
    """The configuration step: it ACCEPTS the parent-supplied connection set and
    makes it available to the server's worker threads. The underlying primitive
    is storing a supplied reference (an unchanged operation); what is pinned here
    is that the server is actually configured to accept the set. On success it
    grants the per-server capability `connections_handed_off(server)` -- it is the
    SOLE producer of that capability, the evidence that the supplied set was
    accepted at configuration. A server that cannot be configured with the set
    (the configuration is impossible / rejects the set) does not run this step and
    so never holds the capability. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(MustTerminate(1))
    Requires(Acc(list_pred(has_override), 1 / 2))
    Requires(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(Acc(list_pred(has_override), 1 / 2))
    Ensures(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(len(has_override) == Old(len(has_override)))
    Ensures(len(override_tokens) == Old(len(override_tokens)))
    Ensures(connections_handed_off(server))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Request:
    def __init__(self) -> None:
        Ensures(Acc(self.released) and self.released == False)  # type: ignore
        self.released = False  # type: bool


def serve_request_on_worker(
    server: Server,
    tokens: List[int],
    has_override: List[bool],
    override_tokens: List[int],
) -> None:
    # pre-conditions-start
    # The registry identities are mutated (the available set takes effect); the
    # supplied-set lists are read-only at fractional permission.
    # Terminates: handling is bounded per-alias work; a diverging body would
    # satisfy every postcondition of a partial-correctness check vacuously, so
    # the obligation rejects non-terminating implementations.
    Requires(MustTerminate(2))
    Requires(list_pred(tokens))
    Requires(Acc(list_pred(has_override), 1 / 2))
    Requires(Acc(list_pred(override_tokens), 1 / 2))
    Requires(len(tokens) == len(has_override))
    Requires(len(tokens) == len(override_tokens))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(tokens))
    Ensures(Acc(list_pred(has_override), 1 / 2))
    Ensures(Acc(list_pred(override_tokens), 1 / 2))
    Ensures(len(tokens) == Old(len(tokens)))
    Ensures(len(tokens) == len(has_override))
    Ensures(len(tokens) == len(override_tokens))
    # (1, discriminating) The worker operates on the parent-supplied connections
    # ONLY because the server was configured to accept the set: the result must
    # carry the per-server capability `connections_handed_off(server)`. Because
    # that capability is unforgeable and produced only by the configuration step,
    # a server that cannot be configured with the set can never discharge this --
    # it is the control-flow effect required of a configurable server.
    Ensures(connections_handed_off(server))
    # (1, secondary value-level) Where the supplied set is available, each
    # supplied alias's entry in the registry takes the supplied connection, and
    # aliases with no supplied connection are left as they were.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens) and has_override[i],
                                            tokens[i] == override_tokens[i]))))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens) and not has_override[i],
                                            tokens[i] == Old(tokens[i])))))
    # post-conditions-end
    # impl-start
    # Pre-patch: the server cannot be configured with the parent-supplied set
    # (the configuration step that accepts the set is not performed), so the set
    # is never made available -- the per-server capability
    # `connections_handed_off(server)` is never granted. The worker still runs
    # its handling, but it operates on whatever connections it already had: it
    # cannot establish that the parent-supplied set reached it.
    i = 0
    while i < len(tokens):
        # invariants-start
        Invariant(list_pred(tokens))
        Invariant(Acc(list_pred(has_override), 1 / 2))
        Invariant(Acc(list_pred(override_tokens), 1 / 2))
        Invariant(len(tokens) == Old(len(tokens)))
        Invariant(len(tokens) == len(has_override))
        Invariant(len(tokens) == len(override_tokens))
        Invariant(0 <= i and i <= len(tokens))
        # strictly decreasing, bounded-below measure discharging the
        # termination obligation from the precondition.
        Invariant(MustTerminate(len(tokens) - i + 1))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and has_override[k],
                                                  tokens[k] == override_tokens[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and not has_override[k],
                                                  tokens[k] == Old(tokens[k])))))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(tokens),
                                                  tokens[k] == Old(tokens[k])))))
        # invariants-end
        if has_override[i]:
            tokens[i] = override_tokens[i]
        i = i + 1
    # impl-end


def teardown_request(closed: List[bool], tokens: List[int], request: Request) -> None:
    # pre-conditions-start
    # The registry's closed-flags are fully owned (they are mutated). The
    # connection-identity list is read-only here, held at fractional permission.
    # Terminates: cleanup is bounded per-alias work; a diverging body would
    # satisfy every postcondition of a partial-correctness check vacuously, so
    # the obligation rejects non-terminating implementations.
    Requires(MustTerminate(2))
    Requires(list_pred(closed))
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(closed) == len(tokens))
    Requires(Acc(request.released))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(closed))
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(len(closed) == Old(len(closed)))
    Ensures(len(closed) == len(tokens))
    Ensures(Acc(request.released))
    # The registry is left over the same connection identities (teardown does
    # not create or rebind connections, it only closes them).
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(tokens),
                                            tokens[i] == Old(tokens[i])))))
    # (2a) Every connection in the registry is left closed.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(closed),
                                            closed[i] == True))))
    # (2b) The request resource is released.
    Ensures(request.released == True)
    # post-conditions-end
    # impl-start
    # Close every connection in this worker thread's registry.
    i = 0
    while i < len(closed):
        # invariants-start
        Invariant(list_pred(closed))
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(len(closed) == Old(len(closed)))
        Invariant(len(closed) == len(tokens))
        Invariant(0 <= i and i <= len(closed))
        # strictly decreasing, bounded-below measure discharging the
        # termination obligation from the precondition.
        Invariant(MustTerminate(len(closed) - i + 1))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(tokens),
                                                  tokens[k] == Old(tokens[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  closed[k] == True))))
        # invariants-end
        closed[i] = True
        i = i + 1
    # Release the request resource (the inherited request cleanup, which releases
    # the request resource only and does NOT touch the registry).
    request.released = True
    # impl-end
