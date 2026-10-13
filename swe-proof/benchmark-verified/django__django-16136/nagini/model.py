"""Twin-artifact model for django__django-16136.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request-handler method produces the "method not allowed" reply for a view.
  It first builds the not-allowed reply object carrying the list of permitted
  methods. It must then deliver that reply in the calling convention the view's
  execution mode requires:

    (1) when the view runs in the asynchronous mode, the method returns an
        awaitable placeholder that resolves to the reply (so a caller may
        await it); the returned object is therefore recognised as an awaitable
        placeholder;

    (2) when the view runs in the synchronous mode, the method returns the
        reply object directly; the returned object is NOT an awaitable
        placeholder.

  In BOTH modes the reply that is ultimately delivered (the resolved value in
  the asynchronous mode, the direct value in the synchronous mode) is the SAME
  not-allowed reply object, carrying the same list of permitted methods. That
  is: deciding the delivery convention from the execution mode must not change
  which reply is delivered.

The view's execution mode is modelled by a boolean (the asynchronous-mode
flag). The not-allowed reply is a minimal object carrying only the touched
field (its list of permitted methods, a ``List[int]`` of method tokens). The
method's return value is a minimal result object exposing the two observable
facts a caller checks: whether the returned object is an awaitable placeholder,
and the not-allowed reply that is (eventually) delivered.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Reply:
    """The not-allowed reply object; carries only the touched field, the list
    of permitted method tokens."""

    def __init__(self, methods: List[int]) -> None:
        Requires(Acc(list_pred(methods), 1 / 2))
        # Terminates outright: a single field store, no loop and no call. Level 2
        # leaves room beneath the level-6 caller (obligation levels are ordinals;
        # the caller's level must strictly exceed every callee's).
        Requires(MustTerminate(2))
        Ensures(Acc(self.methods))  # type: ignore
        Ensures(self.methods is methods)  # type: ignore
        Ensures(Acc(list_pred(methods), 1 / 2))
        self.methods = methods  # type: List[int]


class Delivered:
    """The value returned by the handler: the two observable facts a caller
    inspects. ``is_awaitable`` records whether the returned object is an
    awaitable placeholder; ``reply`` is the not-allowed reply that is
    delivered (directly, or as the resolved value of the placeholder)."""

    def __init__(self, is_awaitable: bool, reply: Reply) -> None:
        Requires(Acc(reply.methods, 1 / 2))
        # Terminates outright: two field stores, no loop and no call. Level 2 for
        # the same reason as Reply.__init__.
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_awaitable))  # type: ignore
        Ensures(Acc(self.reply))  # type: ignore
        Ensures(self.is_awaitable == is_awaitable)  # type: ignore
        Ensures(self.reply is reply)  # type: ignore
        Ensures(Acc(reply.methods, 1 / 2))
        self.is_awaitable = is_awaitable  # type: bool
        self.reply = reply  # type: Reply


# axioms-start
# (no unchanged-callee axioms are required for this behaviour; the conditional
# delivery is modelled deeply below)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered:
    # pre-conditions-start
    Requires(Acc(list_pred(allowed_methods), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(allowed_methods), 1 / 2))
    Ensures(Acc(Result().is_awaitable))
    Ensures(Acc(Result().reply))
    Ensures(Acc(Result().reply.methods, 1 / 2))
    # (1)+(2): the returned object is an awaitable placeholder exactly when the
    # view runs in the asynchronous mode.
    Ensures(Result().is_awaitable == async_mode)
    # The reply delivered in BOTH modes is a not-allowed reply built from the
    # given permitted methods — deciding the delivery convention does not change
    # which reply is delivered.
    Ensures(Result().reply.methods is allowed_methods)
    # post-conditions-end
    # impl-start
    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(True, response)
    else:
        result = Delivered(False, response)
    return result
    # impl-end
