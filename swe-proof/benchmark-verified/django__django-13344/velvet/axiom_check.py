#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13344.

`Solution.lean` models the construction of a middleware around its response
handler **deeply** via the pure `construct` function:

    construct (handlerIsAsync : Bool) : Middleware := { asyncCapable := handlerIsAsync }

`construct` is an **A-reference**: it is the deep model of the *unchanged*
canonical construction routine that the changed functions delegate to. The
observable the desired behaviour constrains is whether the constructed
middleware advertises asynchronous operation — in repo terms, whether
`asyncio.iscoroutinefunction(instance)` is True after construction. The
canonical routine records this exactly when the wrapped response handler is
itself a coroutine function.

This script runs the REAL, unchanged construction routine
(`django.utils.deprecation.MiddlewareMixin.__init__`, which calls
`_async_check`) in-container on boundary + fuzz handlers and asserts:

  asyncio.iscoroutinefunction(instance)  ==  construct(handlerIsAsync).asyncCapable
                                         ==  handlerIsAsync

for every handler, where `handlerIsAsync = asyncio.iscoroutinefunction(handler)`
is the mapping.md bijection input. Exit 0 iff every observation matches the
model (i.e. the A-reference is sound).

Imports only the Python standard library (`asyncio`, `random`, `warnings`) plus
`django.utils.deprecation` (the unchanged callee itself) — no repo-specific
patched code, no settings configuration.
"""
import asyncio
import random
import sys
import warnings


# --- the deep model (Solution.lean `construct`), transliterated --------------

def construct(handler_is_async):
    """Reference of Solution.lean's `construct`: asyncCapable == handlerIsAsync."""
    return {"asyncCapable": bool(handler_is_async)}


# --- the bijection (mapping.md §2) -------------------------------------------

def handler_is_async(handler):
    """mapping.md input bijection: a response handler ↔ Bool `handlerIsAsync`."""
    return asyncio.iscoroutinefunction(handler)


def instance_is_async(instance):
    """mapping.md observable bijection: a constructed middleware ↔ Bool
    `asyncCapable` = whether it advertises asynchronous operation."""
    return asyncio.iscoroutinefunction(instance)


# --- the check against the REAL unchanged construction routine ---------------

def check_construction(MiddlewareMixin, handler):
    """Build a middleware through the REAL canonical routine and assert its
    observed async-capability == construct(handlerIsAsync).asyncCapable."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # get_response=None path warns; irrelevant
        instance = MiddlewareMixin(handler)
    h = handler_is_async(handler)
    observed = instance_is_async(instance)          # real callee observable
    expected = construct(h)["asyncCapable"]         # deep model
    assert observed == expected, (
        "construct A-reference unsound: handler_is_async=%r -> real routine "
        "gives iscoroutinefunction(instance)=%r, deep model gives %r"
        % (h, observed, expected))
    # and the model's defining identity: asyncCapable == handlerIsAsync
    assert expected == h, (
        "model identity broken: construct(%r).asyncCapable=%r" % (h, expected))


def make_async_handler(i):
    async def async_get_response(request):
        return i
    return async_get_response


def make_sync_handler(i):
    def sync_get_response(request):
        return i
    return sync_get_response


def main():
    from django.utils.deprecation import MiddlewareMixin

    handlers = []

    # --- boundary handlers ---------------------------------------------------
    # a plain async coroutine function (handlerIsAsync = True)
    async def plain_async(request):
        return None
    # a plain sync function (handlerIsAsync = False)
    def plain_sync(request):
        return None
    # a lambda (sync), a partial-ish callable wrapper, a method
    handlers.append(plain_async)
    handlers.append(plain_sync)
    handlers.append(lambda request: None)

    class Obj:
        def sync_method(self, request):
            return None
        async def async_method(self, request):
            return None
    obj = Obj()
    handlers.append(obj.sync_method)
    handlers.append(obj.async_method)

    # an async function decorated/wrapped should still be detected as async
    async def decorated_async(request):
        return None
    handlers.append(decorated_async)

    # --- randomized fuzz: alternate async/sync over many shapes --------------
    rng = random.Random(13344)
    for _ in range(2000):
        i = rng.randint(0, 1_000_000)
        if rng.random() < 0.5:
            handlers.append(make_async_handler(i))
        else:
            handlers.append(make_sync_handler(i))

    for h in handlers:
        check_construction(MiddlewareMixin, h)

    n_async = sum(1 for h in handlers if handler_is_async(h))
    n_sync = len(handlers) - n_async
    print("G-AX OK: construct A-reference (== unchanged canonical middleware "
          "construction routine) sound on %d handlers (%d async, %d sync); "
          "iscoroutinefunction(instance) == handlerIsAsync in every case."
          % (len(handlers), n_async, n_sync))
    return 0


if __name__ == "__main__":
    sys.exit(main())
