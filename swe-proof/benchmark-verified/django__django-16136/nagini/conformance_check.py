#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16136 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The impl region itself contains no Requires/Ensures/Assert
lines; the `Reply` / `Delivered` helper classes it instantiates are copied
over with their contract calls removed. There are no @Pure helpers, no
@ContractOnly callees, and no PSeq usage in this bundle, so no sequence shim
is needed.

ORACLE: the REAL patched repo method the model models per mapping.md —
`django.views.generic.base.View.http_method_not_allowed`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched code importable.

Type bridge (mapping.md section 2):
  * `async_mode: bool`  <->  the view's execution mode. The real method reads
    the class-derived async-mode flag, which is True exactly when the view's
    handlers are coroutine functions; the bridge therefore instantiates one of
    two view classes — one whose handler is a plain function, one whose
    handler is a coroutine function — so the flag takes each boolean value.
  * `allowed_methods: List[int]`  <->  the view's permitted-method name list
    (list of str). The model carries an opaque token list; the bridge encodes
    each int token injectively as the name "M<int>" (no comma, no space) and
    makes the view's permitted-method accessor return that encoded list.
  * `Delivered.is_awaitable`  <->  `asyncio.iscoroutine(returned)` on the real
    return value (the caller-facing predicate for "is this an awaitable
    placeholder?").
  * `Delivered.reply`  <->  the reply the real return value delivers: the
    direct return value when it is not a coroutine, else the coroutine's
    resolved value. The reply's permitted-method list is observed through the
    "Allow" header the not-allowed response class derives from it (the only
    modeled field), decoded back through the token encoding.

Per input the script compares, shadow vs real:
  (a) is_awaitable  ==  iscoroutine(real return);
  (b) the delivered reply's method-token list (shadow: reply.methods; real:
      the Allow header decoded) — and that the real delivered value is indeed
      an instance of the not-allowed response class.
Boundary inputs additionally resolve the awaitable with asyncio.run (the
event-loop path a caller uses); fuzz volume resolves via the coroutine
protocol directly (send(None) -> StopIteration.value), which is the same
resolution without per-case event-loop setup cost.

Input domain: the precondition only requires a readable List[int], so every
(bool, int-list) pair is Requires-satisfying. Boundary covers both modes
crossed with empty / singleton / typical / duplicate-token / negative-token /
large-token lists; fuzz draws random modes and random token lists (length
0..8, mixed magnitudes, duplicates allowed).

>= 1e5 Requires-satisfying inputs: 20 boundary + 100000 fuzz.
Pinned fuzz seed: 16136.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import asyncio
import logging
import random
import sys

SEED = 16136
N_FUZZ = 100_000


# --- helper classes from model.py, contract calls stripped ---------------------

class Reply:
    """The not-allowed reply object; carries only the touched field, the list
    of permitted method tokens."""

    def __init__(self, methods):
        self.methods = methods


class Delivered:
    """The value returned by the handler: the two observable facts a caller
    inspects. ``is_awaitable`` records whether the returned object is an
    awaitable placeholder; ``reply`` is the not-allowed reply that is
    delivered (directly, or as the resolved value of the placeholder)."""

    def __init__(self, is_awaitable, reply):
        self.is_awaitable = is_awaitable
        self.reply = reply


# --- the impl region of model.py, verbatim -------------------------------------

def method_not_allowed(async_mode, allowed_methods):
    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(True, response)
    else:
        result = Delivered(False, response)
    return result


# --- token <-> method-name bridge -----------------------------------------------

def enc(token):
    # Injective int -> name encoding; contains no comma or space, so the
    # header join/split below round-trips exactly.
    return "M%d" % token


def enc_list(tokens):
    return [enc(t) for t in tokens]


def allow_header_list(response):
    # The not-allowed response class derives its "Allow" header by joining the
    # permitted-method list with ", "; invert that (empty header <-> empty
    # list; the encoding contains neither comma nor space).
    header = response["Allow"]
    return [] if header == "" else header.split(", ")


def resolve_fast(coro):
    """Resolve a coroutine via the coroutine protocol (no event loop)."""
    try:
        coro.send(None)
    except StopIteration as stop:
        return stop.value
    raise AssertionError("awaitable placeholder did not resolve in one step")


def check_case(make_view, request, HttpResponseNotAllowed,
               async_mode, tokens, use_asyncio_run=False):
    """Run shadow and real method on one (bool, token-list) input; return an
    error string on disagreement, else None."""
    shadow = method_not_allowed(async_mode, tokens)

    view = make_view(async_mode, enc_list(tokens))
    returned = view.http_method_not_allowed(request)

    real_is_awaitable = asyncio.iscoroutine(returned)
    if shadow.is_awaitable != real_is_awaitable:
        if real_is_awaitable:
            returned.close()
        return ("DISAGREEMENT (is_awaitable)\n  async_mode=%r tokens=%r\n"
                "  shadow.is_awaitable=%r\n  real iscoroutine=%r"
                % (async_mode, tokens, shadow.is_awaitable, real_is_awaitable))

    if real_is_awaitable:
        delivered = (asyncio.run(returned) if use_asyncio_run
                     else resolve_fast(returned))
    else:
        delivered = returned

    if not isinstance(delivered, HttpResponseNotAllowed):
        return ("DISAGREEMENT (delivered kind)\n  async_mode=%r tokens=%r\n"
                "  shadow.reply carries a not-allowed reply\n"
                "  real delivered=%r" % (async_mode, tokens, delivered))

    shadow_names = enc_list(shadow.reply.methods)
    real_names = allow_header_list(delivered)
    if shadow.reply.methods is not tokens or shadow_names != real_names:
        return ("DISAGREEMENT (delivered methods)\n  async_mode=%r tokens=%r\n"
                "  shadow methods (encoded)=%r\n  real Allow list=%r"
                % (async_mode, tokens, shadow_names, real_names))
    return None


def boundary_token_lists():
    return [
        [],
        [0],
        [7],
        [1, 2, 3],
        [4, 4],                      # duplicate tokens
        [-1, -420],                  # negative tokens
        [2 ** 31 - 1, 2 ** 63],     # large magnitudes
        [5, 3, 1, 2, 8, 13, 21],    # longer unordered list
        [0, -1, 1],
        [10 ** 12],
    ]


def rand_tokens(rng):
    n = rng.randint(0, 8)
    out = []
    for _ in range(n):
        kind = rng.random()
        if kind < 0.5:
            out.append(rng.randint(0, 9))          # small tokens, duplicates likely
        elif kind < 0.8:
            out.append(rng.randint(-4096, 4096))   # mixed-sign
        else:
            out.append(rng.randint(-2 ** 40, 2 ** 40))
    return out


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(ALLOWED_HOSTS=["*"])
        try:
            django.setup()
        except Exception:
            pass
    # Silence the per-call warning the handler logs (1e5 calls otherwise spam
    # stderr through the last-resort handler; the log line is outside the
    # modeled return behaviour per mapping.md).
    logging.getLogger("django.request").disabled = True

    # REAL patched callee: the view base class whose method-not-allowed
    # handler the model models.
    from django.views.generic.base import View
    from django.http import HttpResponseNotAllowed
    from django.test import RequestFactory

    # Two concrete view classes so the class-derived async-mode flag takes
    # each boolean value: one with a plain-function handler, one with a
    # coroutine-function handler.
    class SyncView(View):
        def get(self, request, *args, **kwargs):
            pass

    class AsyncView(View):
        async def get(self, request, *args, **kwargs):
            pass

    assert SyncView.view_is_async is False
    assert AsyncView.view_is_async is True

    def make_view(async_mode, names):
        view = (AsyncView if async_mode else SyncView)()
        # Per-instance override of the permitted-method accessor so the
        # handler carries exactly the bridged name list (the model hoists
        # this unchanged accessor's result to an input).
        view._allowed_methods = lambda: names
        return view

    # A single reusable request: the handler reads only its method/path (for
    # the unmodeled log line).
    request = RequestFactory().get("/")

    failures = 0
    n_checked = 0

    # boundary: both execution modes x representative token lists, resolving
    # awaitables through the event-loop path a caller uses
    for tokens in boundary_token_lists():
        for async_mode in (False, True):
            err = check_case(make_view, request, HttpResponseNotAllowed,
                             async_mode, tokens, use_asyncio_run=True)
            n_checked += 1
            if err:
                print(err)
                failures += 1
                if failures >= 10:
                    print("too many disagreements; aborting early")
                    return 1

    # fuzz: pinned seed
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        async_mode = bool(rng.getrandbits(1))
        tokens = rand_tokens(rng)
        err = check_case(make_view, request, HttpResponseNotAllowed,
                         async_mode, tokens)
        n_checked += 1
        if err:
            print(err)
            failures += 1
            if failures >= 10:
                print("too many disagreements; aborting early")
                return 1

    if failures:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs"
              % (failures, n_checked))
        return 1
    print("G-CONF OK: shadow == View.http_method_not_allowed on %d inputs "
          "(%d boundary + %d fuzz, seed %d)"
          % (n_checked, len(boundary_token_lists()) * 2, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
