#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16136 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the deep model
              `deliverNotAllowed` / the `do`-block dispatch) transliterated to
              Python over the real repo types, via the mapping.md bijection
              (`bool` ↔ Bool, `list[str]` ↔ List String, the returned object ↔
              `Delivery`). There are NO A-tagged callees in the computed result
              (`_allowed_methods()` / `view_is_async` are free inputs), so the
              shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the post-patch tail of
              `View.http_method_not_allowed` transliterated VERBATIM.

ORACLE CHOICE — why we transliterate the patched handler tail instead of driving
`http_method_not_allowed` end-to-end:
  The real handler needs a fully-built `View` instance bound to a request (for
  `self.view_is_async`, `self._allowed_methods()`, and the logger call) purely to
  read back HOW the 405 response is delivered. The two observables the F2P test
  checks are exactly (a) `asyncio.iscoroutine(response)` and (b) that awaiting it
  (when async) yields an `HttpResponseNotAllowed`. We model both directly: the
  ORACLE is the patched tail (lines 151-159) — `response = HttpResponseNotAllowed
  (allowed)`; `if view_is_async: return (async func returning response)() else
  return response` — and we observe `iscoroutine(...)` and the awaited value, the
  same observables, with `HttpResponseNotAllowed` stood in by a tagged record so
  no Django build is required. stdlib only.

The observables compared per input: (is_awaitable, response_allowed). Exit 0 iff
zero disagreements. The fuzz seed is pinned (mapping.md §4).
"""
import asyncio
import random
import sys

SEED = 16136
N_FUZZ = 100_000


# --- a stand-in for the HttpResponseNotAllowed object (content = allowed list) -
class NotAllowed:
    def __init__(self, allowed):
        self.allowed = list(allowed)

    def __eq__(self, other):
        return isinstance(other, NotAllowed) and self.allowed == other.allowed

    def __repr__(self):
        return "NotAllowed(%r)" % (self.allowed,)


def observe(returned):
    """Reduce a returned object to the F2P-observable pair (is_awaitable,
    response_content). Mirrors the test: asyncio.iscoroutine(response), and the
    response obtained directly or after `asyncio.run(response)`."""
    if asyncio.iscoroutine(returned):
        resp = asyncio.run(returned)
        return (True, resp)
    return (False, returned)


# --- ORACLE: the PATCHED handler tail, transliterated verbatim ----------------
def oracle(view_is_async, allowed):
    response = NotAllowed(allowed)            # HttpResponseNotAllowed(self._allowed_methods())
    if view_is_async:
        async def func():
            return response
        returned = func()                     # an awaitable
    else:
        returned = response
    return observe(returned)


# --- SHADOW: Solution.lean's deliverNotAllowed, transliterated -----------------
def shadow(asynchronous, allowed):
    resp = NotAllowed(allowed)                # let resp : NotAllowed := { allowed }
    if asynchronous:
        # Delivery.awaitable resp  ↔  an awaitable yielding resp
        async def func():
            return resp
        returned = func()
    else:
        returned = resp                       # Delivery.immediate resp
    return observe(returned)


def fuzz_allowed(rng):
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"]
    k = rng.randint(0, len(methods))
    return rng.sample(methods, k)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive over the boolean decision with representative allowed lists.
    boundary_allowed = [[], ["GET"], ["POST"], ["GET", "POST"],
                        ["GET", "HEAD", "OPTIONS"]]
    cases = [(b, a) for b in (False, True) for a in boundary_allowed]
    # Plus seeded fuzz over both branches.
    cases += [(rng.choice((False, True)), fuzz_allowed(rng)) for _ in range(N_FUZZ)]

    for asynchronous, allowed in cases:
        count += 1
        sh = shadow(asynchronous, allowed)
        orc = oracle(asynchronous, allowed)
        if sh != orc:
            disagreements.append((asynchronous, allowed, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for asy, al, sh, orc in disagreements:
            print("  async=%r allowed=%r shadow=%r oracle=%r" % (asy, al, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of notAllowedResponse agrees with patch.diff "
          "behaviour on %d inputs (10 exhaustive + fuzz, seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
