"""Twin-artifact model for django__django-16502.

Behaviour under specification (stated as desired behaviour, not as an edit).

A development WSGI request handler must make a response to a body-less request
method comply with the rule that such a response carries response headers but
no message body. The request method is classified into two cases by a single
predicate: the body-less method (the one that asks only for the headers a full
request would return) versus every body-bearing method.

  (1) Response-header preparation. Two header facts are observable: whether a
      payload-size header is present, and whether the connection is asked to
      terminate.

      * For the body-less method the payload-size header, if the base
        preparation left one in place, is dropped, so that no payload-size
        header is emitted -- this is what permits omitting it for a body-less
        response. For every body-bearing method the payload-size header is left
        exactly as the base preparation left it.

      * The connection is asked to terminate only to stop a client from reusing
        a connection whose payload size it cannot know. That applies to a
        body-bearing method whose payload-size header is absent. It is also
        applied, for any method, when the serving environment cannot keep a
        connection alive across requests. Crucially, a body-less method is NEVER
        asked to terminate merely because it lacks a payload-size header: its
        missing payload-size header is intended, not a sign of unknown length.
        The terminate decision is then mirrored onto the handler's flag.

  (2) Response-body emission. The emitted body of a body-less response is empty:
      the application's iterable contributes none of its data to the output. For
      a body-bearing method the emitted body is exactly the application's data,
      in order.

Modelling choices (Nagini fragment):
  * The request method is abstracted to a single ``bool`` ``head`` -- True for
    the body-less method, False for any body-bearing method -- because the
    behaviour branches only on that classification.
  * The two observable header facts are the ``bool`` fields of a small mutated
    object ``Resp`` (``has_size`` = a payload-size header is present;
    ``conn_terminate`` = the connection is asked to terminate) plus a
    handler-level ``terminate_flag``. The base preparation has already run, so
    the ENTRY field values are the post-base state; preparation mutates them in
    place (full permission), and the exact post-state is pinned.
  * Whether the serving environment can keep connections alive across requests
    is a ``bool`` ``keepalive`` (False forces a terminate for any method).
  * Bodies are ``List[int]`` of byte values; specification is carried by
    ``PSeq[int]`` via ``ToSeq``. The application iterable is read-only and is
    held at fractional permission.

The whole behaviour is modelled deeply (the case split and the header/body
decisions are spelled out in the impl regions); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: every changed decision (the body-less header drop, the
# terminate-only-for-body-bearing-unknown-length rule, and the empty-body
# emission) is the behaviour under specification and is spelled out deeply in
# the impl regions. There is no unchanged opaque callee whose contract the
# proof needs.
# axioms-end


# pure-start
@Pure
def want_terminate(head: bool, has_size_after: bool, keepalive: bool) -> bool:
    """Whether the connection is asked to terminate, given the method
    classification, whether a payload-size header survived preparation, and
    whether the environment can keep connections alive.

    A terminate is asked for in exactly two situations: a body-bearing method
    whose payload-size header is absent (unknown length, so the client must not
    reuse the connection), or any method served by an environment that cannot
    keep a connection alive. A body-less method is never asked to terminate
    merely for lacking a payload-size header."""
    if (not head) and (not has_size_after):
        return True
    return not keepalive
# pure-end


class Resp:
    """Carrier for the two observable response-header facts and the handler
    terminate flag. ``has_size`` = a payload-size header is present;
    ``conn_terminate`` = the connection is asked to terminate; ``terminate_flag``
    = the handler's connection-terminate flag. Constructed in the
    post-base-preparation state."""

    def __init__(self, has_size: bool) -> None:
        Ensures(Acc(self.has_size) and Acc(self.conn_terminate) and Acc(self.terminate_flag))
        Ensures(self.has_size == has_size)
        Ensures(self.conn_terminate == False)
        Ensures(self.terminate_flag == False)
        self.has_size = has_size  # type: bool
        self.conn_terminate = False  # type: bool
        self.terminate_flag = False  # type: bool


def prepare_response_headers(resp: Resp, head: bool, keepalive: bool) -> None:
    # pre-conditions-start
    # The response-header object is genuinely mutated in place; full permission.
    # Its ENTRY field values are the post-base-preparation state: ``has_size``
    # is whether the base step left a payload-size header in place. The base
    # step asks for no terminate and sets no flag, so both terminate fields
    # enter False (the terminate decision is taken entirely here).
    Requires(Acc(resp.has_size) and Acc(resp.conn_terminate) and Acc(resp.terminate_flag))
    Requires(resp.conn_terminate == False)
    Requires(resp.terminate_flag == False)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(resp.has_size) and Acc(resp.conn_terminate) and Acc(resp.terminate_flag))
    # (a) The payload-size header is dropped for a body-less method, and left
    #     untouched for every body-bearing method.
    Ensures(Implies(head, resp.has_size == False))
    Ensures(Implies(not head, resp.has_size == Old(resp.has_size)))
    # (b) The terminate decision: terminate for a body-bearing method with no
    #     surviving payload-size header, OR for any method that cannot keep
    #     alive; and NEVER for a body-less method merely lacking a payload-size
    #     header.
    Ensures(resp.conn_terminate == want_terminate(head, resp.has_size, keepalive))
    # A body-less method is never terminated on account of a missing
    # payload-size header alone: when the environment can keep alive, a
    # body-less response does not terminate.
    Ensures(Implies(head and keepalive, resp.conn_terminate == False))
    # (c) The handler flag mirrors the terminate decision exactly.
    Ensures(resp.terminate_flag == resp.conn_terminate)
    # post-conditions-end
    # impl-start
    # Drop the payload-size header for a body-less method.
    if head and resp.has_size:
        resp.has_size = False
    # Ask to terminate only for a body-bearing method of unknown length,
    # otherwise only when the environment cannot keep connections alive.
    if (not head) and (not resp.has_size):
        resp.conn_terminate = True
    elif not keepalive:
        resp.conn_terminate = True
    # Mirror the terminate decision onto the handler flag.
    if resp.conn_terminate:
        resp.terminate_flag = True
    # impl-end


def emit_response_body(result: List[int], head: bool) -> List[int]:
    # pre-conditions-start
    # The application's body iterable is read-only; fractional permission.
    Requires(Acc(list_pred(result), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A body-less response emits no body: none of the application's data reaches
    # the output.
    Ensures(Implies(head, ToSeq(Result()) == PSeq(0).take(0)))
    Ensures(Implies(head, len(Result()) == 0))
    # A body-bearing response emits exactly the application's data, in order.
    Ensures(Implies(not head, ToSeq(Result()) == ToSeq(result)))
    Ensures(Implies(not head, len(Result()) == len(result)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    if head:
        # The body-less branch contributes nothing to the output.
        return out
    j = 0
    while j < len(result):
        # invariants-start
        Invariant(Acc(list_pred(result), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(result))
        Invariant(ToSeq(out) == ToSeq(result).take(j))
        Invariant(len(out) == j)
        Invariant(MustTerminate(len(result) - j + 1))
        # invariants-end
        out.append(result[j])
        j = j + 1
    return out
    # impl-end
