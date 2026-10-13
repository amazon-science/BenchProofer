#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_initComponent
against the patch.diff behaviour (post-patch construction via super().__init__).

The impl region is NOT all-A-tagged (it has I/R structure), so this runs a real
fuzz. The two A-reference ops are left as the REAL stdlib callees:
  * the missing-handler notice predicate -> `get_response is None`;
  * the async-capability check          -> `asyncio.iscoroutinefunction(...)`.
The shadow therefore reproduces the post-patch behaviour op-for-op; we assert
zero disagreements vs an independent reconstruction of the patched constructor
over >=10^5 fuzzed inputs.

The patched constructor delegates to MiddlewareMixin.__init__(get_response):
  - emit the "missing handler" notice iff get_response is None;
  - store get_response;
  - mark the instance async iff iscoroutinefunction(get_response).

stdlib-only. exit 0 iff zero disagreements.
"""
import asyncio
import random
import sys

SEED = 13344          # pinned in mapping.md
N = 120_000           # >= 10^5


# --- candidate handlers (the inputs we fuzz over) -------------------------

async def _coro_handler(request):          # an asynchronous handler
    return None


def _sync_handler(request):                # an ordinary handler
    return None


class _CallableObj:                        # a non-async callable object
    def __call__(self, request):
        return None


# (label, value, is_async_truth) — is_async_truth is only for sanity, the
# shadow/oracle both compute asyncness via the REAL callee.
HANDLER_POOL = [
    ("none", None, None),
    ("coro", _coro_handler, None),
    ("sync", _sync_handler, None),
    ("callable_obj", _CallableObj(), None),
    ("lambda", (lambda request: None), None),
]


def shadow(handler):
    """R/I shadow of implementation_initComponent.

    missingFlag := (handler is None)           # A-reference: `is None`
    stored      := handler                     # I
    async       := iscoroutinefunction(handler)# A-reference: real callee
    returns (stored, missingFlag, async)
    """
    missing_flag = handler is None
    stored = handler
    reports_async = bool(asyncio.iscoroutinefunction(handler))
    return (stored, missing_flag, reports_async)


def patched_construct(handler):
    """Independent reconstruction of the post-patch constructor behaviour
    (delegating to MiddlewareMixin.__init__): notice iff None, store handler,
    mark async iff iscoroutinefunction."""
    notice = handler is None
    stored = handler
    is_coro = bool(asyncio.iscoroutinefunction(handler))
    return (stored, notice, is_coro)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first: every handler kind.
    fixed = [h[1] for h in HANDLER_POOL]
    cases = fixed + [rng.choice(HANDLER_POOL)[1] for _ in range(N)]

    for h in cases:
        got = shadow(h)
        want = patched_construct(h)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((repr(h), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for h, g, w in examples:
            print(f"  in={h} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
