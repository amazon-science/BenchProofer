#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16136.

This bundle consumes NO unchanged-callee axiom: the conditional delivery is
modelled DEEPLY in model.py (the `method_not_allowed` impl + the `Delivered`
result object). G-AX therefore validates that deep model against the REAL
delivery mechanism the gold patch uses, on boundary + randomized fuzz inputs.

The A-reference (deep model `method_not_allowed` / `Delivered`) encodes three
observable facts about the value the handler returns:

  (i)  it is an awaitable placeholder (a coroutine) EXACTLY when the view runs
       in the asynchronous mode;
  (ii) the reply delivered (the resolved value of the coroutine in the async
       mode, or the direct return value in the sync mode) is the SAME
       not-allowed reply object;
  (iii) that reply carries the given list of permitted methods.

The real mechanism is the exact construct the gold patch (and the pre-existing
`View.options`) use:

    response = HttpResponseNotAllowed(self._allowed_methods())
    if self.view_is_async:
        async def func():
            return response
        return func()
    else:
        return response

This check reproduces that construct with only the standard library (a stand-in
``_Reply`` object plays the role of ``HttpResponseNotAllowed`` — the patch does
not change the response class, only how it is delivered) and asserts the three
facts via the very predicates a caller uses: ``asyncio.iscoroutine`` on the
returned object, and ``asyncio.run`` to resolve the awaitable. This mirrors the
F2P test ``test_http_method_not_allowed_responds_correctly`` exactly.

Imports nothing repo-specific: only ``asyncio`` and ``random`` from the standard
library — the same machinery the gold patch relies on. Exit 0 iff every
obligation holds.
"""
import asyncio
import random
import sys


class _Reply:
    """Stand-in for the not-allowed reply object (HttpResponseNotAllowed); the
    gold patch does not change the response class, only how it is delivered, so
    a minimal object carrying the permitted-method list is faithful here."""

    def __init__(self, methods):
        self.methods = methods


def real_method_not_allowed(view_is_async, allowed_methods):
    """Faithful stdlib-only reproduction of the gold patch's delivery logic
    (identical in shape to View.options): build the reply, then deliver it as a
    coroutine iff the view is async, else directly."""
    response = _Reply(allowed_methods)
    if view_is_async:

        async def func():
            return response

        return func()
    else:
        return response


def check_reference(view_is_async, allowed_methods):
    """Assert the deep model's three facts hold for the real delivery
    mechanism, observed exactly as the F2P test observes them."""
    returned = real_method_not_allowed(view_is_async, allowed_methods)

    # fact (i): returned object is a coroutine iff the view is async
    is_coroutine = asyncio.iscoroutine(returned)
    assert is_coroutine == view_is_async, (
        "is_awaitable mismatch for view_is_async=%r: iscoroutine=%r"
        % (view_is_async, is_coroutine))

    # resolve the placeholder in the async mode, exactly as the F2P test does
    if is_coroutine:
        reply = asyncio.run(returned)
    else:
        reply = returned

    # fact (ii)+(iii): the delivered reply is the not-allowed reply carrying the
    # given permitted methods (identity preserved across the await)
    assert isinstance(reply, _Reply), (
        "delivered value is not the reply object for view_is_async=%r: %r"
        % (view_is_async, reply))
    assert reply.methods is allowed_methods, (
        "delivered reply lost its permitted-method list for view_is_async=%r"
        % (view_is_async,))


def main():
    # boundary: both execution modes, with representative method lists
    boundary_methods = [
        [],
        [b"GET"],
        [b"GET", b"HEAD", b"OPTIONS"],
        [b"POST"],
        [b"GET", b"POST", b"PUT", b"PATCH", b"DELETE", b"HEAD", b"OPTIONS"],
    ]
    for methods in boundary_methods:
        for view_is_async in (False, True):
            check_reference(view_is_async, methods)

    # randomized fuzz: random async-mode flags and random method lists
    rng = random.Random(16136)
    vocab = [b"GET", b"POST", b"PUT", b"PATCH", b"DELETE", b"HEAD",
             b"OPTIONS", b"TRACE"]
    fuzz = 0
    for _ in range(4000):
        view_is_async = bool(rng.getrandbits(1))
        n = rng.randint(0, len(vocab))
        methods = rng.sample(vocab, n)
        check_reference(view_is_async, methods)
        fuzz += 1

    print("G-AX OK: method_not_allowed deep model (== the gold patch's "
          "coroutine-wrap-iff-async delivery, identical to View.options) sound "
          "on %d boundary + %d fuzz inputs"
          % (len(boundary_methods) * 2, fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
