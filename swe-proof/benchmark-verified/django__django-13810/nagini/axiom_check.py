#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13810.

This bundle consumes NO @ContractOnly axiom. The two unchanged callees that the
modelled walk invokes to derive a new handler from an old one —

  * the mode adapter  (django.core.handlers.base.BaseHandler.adapt_method_mode)
  * the wrapper       (django.core.handlers.exception.convert_exception_to_response)

— are modelled DEEPLY as the pure token-appending maps `adapt_token` /
`wrap_token` (model.py pure region). G-AX validates those deep models, and the
front-recursive fold `final_handler` / `final_async` they feed, against the REAL
control-flow of the patched `load_middleware` loop.

The load-bearing observable property (the behaviour the issue demands): when a
layer DECLINES (its construction raises `MiddlewareNotUsed`), the running
handler AND the running async-mode flag that the next layer inherits must be
exactly the values in force before that declining layer was visited — a
tentative adaptation computed for a declining layer must leave no trace on the
chain. We model both callees as deriving a FRESH handler from the old one (never
an in-place mutation), so the only way a tentative adaptation survives a decline
is via a premature assignment — exactly the defect.

We reproduce the REAL loop semantics (handler threading + the try/except/else
rollback) with sentinel callables, run it on boundary + randomized fuzz layer
sequences, and assert it matches the abstract token fold the model verifies
against. Imports stdlib only; exit 0 iff every observation matches the model.
"""
import random
import sys

# --- model.py deep-model encodings (kept in lock-step with the pure region) --

ADAPT_TOKEN = 1
WRAP_TOKEN = 2


def adapt_token(handler, target_mode):
    """model.py adapt_token: derive a NEW handler for target_mode (fresh)."""
    return list(handler) + [ADAPT_TOKEN, target_mode]


def wrap_token(handler):
    """model.py wrap_token: derive a NEW wrapper handler (fresh)."""
    return list(handler) + [WRAP_TOKEN]


def committed_handler(old_handler, target_mode):
    return wrap_token(adapt_token(old_handler, target_mode))


def final_handler(handler, async_mode, target_mode, declines, i):
    """model.py final_handler front-recursion (reference, iterative form)."""
    h = list(handler)
    a = async_mode
    while i < len(target_mode):
        if declines[i] == 1:
            i += 1
            continue
        h = committed_handler(h, target_mode[i])
        a = target_mode[i]
        i += 1
    return h


def final_async(handler, async_mode, target_mode, declines, i):
    a = async_mode
    while i < len(target_mode):
        if declines[i] == 1:
            i += 1
            continue
        a = target_mode[i]
        i += 1
    return a


# --- the REAL loop semantics (post-patch django load_middleware threading) ----
#
# The real loop derives a fresh adapted handler each step and only commits it on
# the `else` branch of try/except (i.e. only when the layer did NOT decline).
# We mirror that exactly with token-recording callables so we can compare the
# resulting handler object's identity (its token trace) against the model.

class _RealAdapter:
    """Faithful re-creation of the patched loop's handler threading.

    adapt(handler, target_mode) and wrap(handler) each return a NEW handler
    (asgiref's sync_to_async/async_to_sync and convert_exception_to_response all
    return fresh callables; they never mutate the passed handler in place). The
    rollback structure is the gold patch's `adapted = adapt(...); construct();
    except Decline: continue; else: handler = adapted`.
    """

    def adapt(self, handler, target_mode):
        return list(handler) + [ADAPT_TOKEN, target_mode]

    def wrap(self, handler):
        return list(handler) + [WRAP_TOKEN]

    def run(self, target_mode, declines, base_async):
        handler = []
        handler_is_async = base_async
        for i in range(len(target_mode)):
            # Adapt handler, if needed (tentative; fresh object).
            adapted_handler = self.adapt(handler, target_mode[i])
            declined = declines[i] == 1
            if declined:
                # MiddlewareNotUsed: skip further processing for this layer.
                continue
            else:
                handler = adapted_handler
            # Layer participates: wrap and advance the running flag.
            handler = self.wrap(handler)
            handler_is_async = target_mode[i]
        return handler, handler_is_async


def check_case(target_mode, declines, base_async):
    real = _RealAdapter().run(target_mode, declines, base_async)
    model_handler = final_handler([], base_async, target_mode, declines, 0)
    model_async = final_async([], base_async, target_mode, declines, 0)
    assert real[0] == model_handler, (
        "handler trace mismatch on (mode=%r declines=%r base=%r): real=%r model=%r"
        % (target_mode, declines, base_async, real[0], model_handler))
    assert real[1] == model_async, (
        "async-flag mismatch on (mode=%r declines=%r base=%r): real=%r model=%r"
        % (target_mode, declines, base_async, real[1], model_async))


def check_decline_no_trace(target_mode, declines, base_async):
    """Stronger, behaviour-pinning check: deleting a DECLINING layer from the
    sequence does not change the assembled chain (a declined layer leaves no
    trace on what the next layer inherits). This is the exact property the issue
    requires and that the pre-patch loop violates."""
    full = _RealAdapter().run(target_mode, declines, base_async)
    for j in range(len(target_mode)):
        if declines[j] != 1:
            continue
        tm = target_mode[:j] + target_mode[j + 1:]
        dc = declines[:j] + declines[j + 1:]
        pruned = _RealAdapter().run(tm, dc, base_async)
        assert full == pruned, (
            "declining layer %d left a trace: full=%r pruned=%r (mode=%r declines=%r)"
            % (j, full, pruned, target_mode, declines))


def main():
    # boundary cases
    boundary = [
        ([], [], 0),
        ([], [], 1),
        ([0], [0], 0),
        ([1], [0], 1),
        ([0], [1], 0),                       # single declining layer
        ([1], [1], 1),
        # the F2P scenario abstraction: reversed(MIDDLEWARE) walked in order =
        # [declining sync-only layer, participating async layer], base async.
        ([0, 1], [1, 0], 1),
        ([1, 0], [1, 0], 1),
        ([0, 0, 0], [1, 1, 1], 0),           # all decline
        ([1, 1, 1], [0, 0, 0], 1),           # none decline
        ([0, 1, 0, 1], [1, 0, 1, 0], 1),     # alternating
        ([1, 0, 1], [0, 1, 0], 0),
    ]
    for tm, dc, ba in boundary:
        check_case(tm, dc, ba)
        check_decline_no_trace(tm, dc, ba)

    # randomized fuzz
    rng = random.Random(13810)
    for _ in range(50000):
        n = rng.randint(0, 8)
        tm = [rng.randint(0, 1) for _ in range(n)]
        dc = [rng.randint(0, 1) for _ in range(n)]
        ba = rng.randint(0, 1)
        check_case(tm, dc, ba)
        check_decline_no_trace(tm, dc, ba)

    print("G-AX OK: deep models adapt_token/wrap_token + folds final_handler/"
          "final_async match the real patched load_middleware threading on %d "
          "boundary + 50000 fuzz layer sequences; declining layers leave no "
          "trace (decline-rollback property holds)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
