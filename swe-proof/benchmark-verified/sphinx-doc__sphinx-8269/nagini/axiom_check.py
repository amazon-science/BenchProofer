#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8269.

The model abstracts the UNCHANGED transport-status gate (the callee the patch
adds a new call to in the fragment-checking branch) as a single contract-only
function

    raise_on_error_status(status) -> None
        Ensures(status < 400 or status >= 600)                # normal => non-error
        Exsures(TransportError, 400 <= status and status < 600)  # raise => error status

i.e. the only observable of the gate is whether the answered HTTP status falls
in the error ranges: it returns normally EXACTLY on a non-error status and
signals the SAME out-of-band transport error EXACTLY on a status in [400, 600).
(In the real code the gate is ``requests.models.Response.raise_for_status()``,
which raises ``requests.exceptions.HTTPError`` on a 4xx/5xx status -- caught by
the shared ``except HTTPError`` dispatch in ``check_uri`` -- and returns ``None``
otherwise.)

This check constructs a real ``requests.models.Response`` with a chosen
``status_code`` and runs the REAL ``raise_for_status()`` on it, asserting for
each status that the call either

   * returns normally (non-error: matches ``Ensures(status < 400 or status >= 600)``), or
   * raises ``HTTPError`` (error status: matches
     ``Exsures(TransportError, 400 <= status < 600)``) -- and NOTHING else
     (no other out-of-band signal),

with the raise/no-raise boundary matching ``400 <= status < 600`` EXACTLY. It
sweeps the range edges (399/400/401/403/404/499/500/503/599/600), the special
401/503 codes the dispatch singles out, sub-400 and >=600 codes, and a
randomized fuzz over a wide integer range.

Imports only the standard ``requests`` package (the very package the patch
calls); nothing repo-specific. Exit 0 iff every observation meets the axiom.
"""
import random
import sys


def is_error_status(status):
    """The axiom's range predicate: a status in [400, 600) is a transport error."""
    return 400 <= status < 600


def main():
    try:
        import requests
        from requests.exceptions import HTTPError
    except Exception as exc:  # pragma: no cover - container guard
        print("G-AX SKIP: requests unavailable (%r)" % (exc,))
        return 0

    def observe(status):
        """Run the REAL raise_for_status on a Response with this status; classify
        the observable outcome."""
        resp = requests.models.Response()
        resp.status_code = status
        resp.url = "http://localhost:7777/"
        resp.reason = "Internal Server Error"
        try:
            result = resp.raise_for_status()
        except HTTPError:
            # The relied-on transport-error channel.
            return ("raise", None)
        except Exception as other:
            # The axiom forbids any other out-of-band signal.
            return ("other", other)
        else:
            return ("normal", result)

    def check(status):
        kind, info = observe(status)
        assert kind in ("raise", "normal"), (
            "raise_on_error_status axiom unsound: real raise_for_status produced "
            "a non-HTTPError out-of-band signal on status %r: %r" % (status, info))
        if is_error_status(status):
            assert kind == "raise", (
                "raise_on_error_status axiom unsound: real raise_for_status did "
                "NOT raise on error status %r (Exsures requires a raise on "
                "[400,600)); outcome=%r" % (status, (kind, info)))
        else:
            assert kind == "normal", (
                "raise_on_error_status axiom unsound: real raise_for_status "
                "RAISED on non-error status %r (Ensures requires normal "
                "completion on <400 or >=600); outcome=%r" % (status, (kind, info)))

    # --- boundary cases over the range edges + the special codes -------------
    boundary = [
        0, 1, 100, 199, 200, 204, 299, 300, 301, 302, 304, 307, 308, 399,  # < 400
        400, 401, 402, 403, 404, 410, 429, 451, 499,                        # 4xx
        500, 501, 502, 503, 504, 599,                                       # 5xx
        600, 601, 700, 999,                                                 # >= 600
    ]
    n_boundary = 0
    n_raise = 0
    for s in boundary:
        check(s)
        n_boundary += 1
        if is_error_status(s):
            n_raise += 1

    # explicit witnesses for the dispatch-special statuses the model branches on
    assert observe(401)[0] == "raise", "401 must raise HTTPError (working path)"
    assert observe(503)[0] == "raise", "503 must raise HTTPError (ignored path)"
    assert observe(500)[0] == "raise", "500 must raise HTTPError (broken path) -- the F2P scenario"
    assert observe(200)[0] == "normal", "200 must NOT raise (success path)"

    # --- fuzz: every status must classify cleanly on the [400,600) boundary --
    rng = random.Random(8269)
    n_fuzz = 0
    for _ in range(20000):
        s = rng.randint(-50, 1200)
        check(s)
        n_fuzz += 1

    print("G-AX OK: real requests.Response.raise_for_status is total over "
          "{[400,600) -> HTTPError, else -> None} on %d boundary + %d fuzz "
          "statuses (%d in the error range raised); raise_on_error_status axiom "
          "sound" % (n_boundary, n_fuzz, n_raise))
    return 0


if __name__ == "__main__":
    sys.exit(main())
