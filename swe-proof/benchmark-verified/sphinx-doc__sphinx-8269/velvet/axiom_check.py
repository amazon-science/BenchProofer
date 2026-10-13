#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8269.

The only callee whose behaviour `Solution.lean` depends on is the response-status
validator `requests.models.Response.raise_for_status()`, modeled DEEPLY by
`isErrorStatus` (an A-reference, NOT a consumed axiom). This check runs the REAL
callee over the full HTTP status range plus fuzz and asserts:

  (A-reference)  `isErrorStatus(sc)`  (model.py:  400 <= sc < 600)
                 ==  "real raise_for_status() raises HTTPError on a response
                      whose status_code is sc".

  (dispatch well-formedness)  whenever the real callee raises, the raised
                 HTTPError carries `.response.status_code == sc`, so the status
                 handler `classifyError` (which dispatches on 401 / 503 / else)
                 is reading a real, present field — i.e. the I-leg's dispatch key
                 is the genuine status code.

Imports only `requests` — the same library the gold patch's `raise_for_status`
call resolves to in the instance image. Exit 0 iff every obligation holds.
"""
import sys

import requests
from requests.exceptions import HTTPError


def is_error_status(sc):
    """Reference encoding of model.py's deep model `isErrorStatus`."""
    return 400 <= sc < 600


def real_raises(sc):
    """Run the REAL requests.Response.raise_for_status() on a response carrying
    status_code == sc. Returns (raised: bool, dispatch_code: int | None)."""
    resp = requests.models.Response()
    resp.status_code = sc
    resp.url = "http://localhost/test"
    try:
        resp.raise_for_status()
        return False, None
    except HTTPError as err:
        # the field classifyError dispatches on
        return True, err.response.status_code


def check_status(sc):
    raised, dispatch_code = real_raises(sc)
    expected = is_error_status(sc)
    assert raised == expected, (
        "isErrorStatus deep model unsound on status %d: real raise_for_status "
        "raised=%r, model says error=%r" % (sc, raised, expected))
    if raised:
        assert dispatch_code == sc, (
            "HTTPError dispatch key wrong for status %d: err.response.status_code"
            "=%r (classifyError would dispatch on the wrong code)"
            % (sc, dispatch_code))


def main():
    # --- boundary cases over the 4xx/5xx error window and its edges ---------
    boundary = [
        100, 199, 200, 201, 204, 299, 300, 301, 302, 304, 399,  # non-error
        400, 401, 403, 404, 410, 418, 451, 499,                 # 4xx incl. 401
        500, 502, 503, 504, 511, 599,                           # 5xx incl. 503
        600, 601, 200, 0,                                       # >=600 non-error
    ]
    for sc in boundary:
        check_status(sc)

    # --- exhaustive sweep of the whole plausible status range ---------------
    for sc in range(0, 700):
        check_status(sc)

    # --- the two reclassified statuses the handler treats specially ---------
    # 401 and 503 must both be inside the error window (so they reach the
    # handler at all) — guards classifyError being reachable.
    assert is_error_status(401) and real_raises(401)[0]
    assert is_error_status(503) and real_raises(503)[0]
    # a generic error status (500) must also raise -> 'broken' branch reachable
    assert is_error_status(500) and real_raises(500)[0]
    # a success status (200) must NOT raise -> fragment branch reachable
    assert (not is_error_status(200)) and (not real_raises(200)[0])

    print("G-AX OK: isErrorStatus deep model (== requests.raise_for_status) "
          "sound over status range [0,700) + boundary; HTTPError dispatch key "
          "== status_code on every raising status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
