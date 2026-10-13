#!/usr/bin/env python3
r"""G-CONF — differential test of the R/I shadow of
implementation_disallowedResponse against the patch.diff behaviour (the patched
control flow of View.http_method_not_allowed).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: build the bare 405 response carrying the permitted
methods, then in async mode return an awaitable wrapper around it, else the bare
response. We diff that against an INDEPENDENT oracle that runs the EXACT patched
Python control flow (an `async def func(): return response` closure when async,
the bare object otherwise) and observes coroutine-ness via the real
`asyncio.iscoroutine`, exactly as the F2P test does. The observed
`(iscoroutine, allowed-after-await)` pair is compared to the shadow's
`(awaitable, allowed)`.

Zero disagreements required over >=10^5 fuzzed inputs (both async and sync modes).
stdlib-only. exit 0 iff zero disagreements.
"""
import asyncio
import random
import sys

SEED = 16136          # pinned in mapping.md
N = 120_000           # >= 10^5

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"]


class _Resp:
    """Stand-in for HttpResponseNotAllowed carrying the permitted methods."""
    def __init__(self, allowed):
        self.allowed = list(allowed)


def shadow(is_async: bool, allowed):
    """R/I shadow of implementation_disallowedResponse (op-for-op).

    Returns (awaitable: bool, allowed: list[str])."""
    response_allowed = list(allowed)        # the bare 405 response payload
    if is_async:
        return (True, response_allowed)
    else:
        return (False, response_allowed)


def oracle(is_async: bool, allowed):
    """Run the EXACT patched control flow; observe via real asyncio.iscoroutine.

    Returns (iscoroutine: bool, allowed-after-await: list[str])."""
    response = _Resp(allowed)               # HttpResponseNotAllowed(self._allowed_methods())

    if is_async:                            # self.view_is_async

        async def func():
            return response

        result = func()
    else:
        result = response

    is_coro = asyncio.iscoroutine(result)
    if is_coro:
        resolved = asyncio.run(result)      # await it, as the test does
    else:
        resolved = result
    return (is_coro, list(resolved.allowed))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first: both modes, empty + typical payloads.
    fixed = [
        (False, []),
        (True, []),
        (False, ["POST"]),
        (True, ["POST"]),
        (False, ["GET", "HEAD", "OPTIONS"]),
        (True, ["GET", "HEAD", "OPTIONS"]),
        (False, METHODS),
        (True, METHODS),
    ]
    cases = list(fixed)
    for _ in range(N):
        is_async = rng.choice([False, True])
        k = rng.randint(0, len(METHODS))
        allowed = rng.sample(METHODS, k)
        cases.append((is_async, allowed))

    for is_async, allowed in cases:
        got = shadow(is_async, allowed)
        want = oracle(is_async, allowed)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((is_async, allowed, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for a, al, g, w in examples:
            print(f"  is_async={a} allowed={al!r} shadow={g} oracle={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
