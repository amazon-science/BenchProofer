#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8269 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`classify` /
              `classifyError` / the nested-if control flow) transliterated to
              Python over the real repo types (`status_code: int`,
              `found: bool`), via the mapping.md bijection. The status-validation
              decision is the A-reference `isErrorStatus`; per plan §4.1 the
              A-tagged callee is left as the REAL repo callee here
              (`requests.Response.raise_for_status`), so the shadow's "is this an
              error?" test calls the genuine validator, not the model — that
              isolates the surrounding R/I control flow (the 401/503/else
              dispatch and the found-routing).

  * ORACLE  — patch.diff's behaviour: a faithful executable copy of the patched
              `check_uri` fragment branch (the `if anchor and linkcheck_anchors`
              arm + the shared `except HTTPError` status handler), driven by the
              REAL `requests.Response.raise_for_status` over a response carrying
              `status_code`, with `check_anchor` standing in as the boolean
              `found`. This is the gold control flow (G-RESOLVE confirms the
              shipped patch resolves).

They must agree on the observable verdict `(status, detail_source, code)` for
every Requires-satisfying input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + `requests`
only (`requests` is a hard dependency of sphinx). Fuzz seed pinned (mapping.md
§4) for a deterministic verdict.
"""
import random
import sys

import requests
from requests.exceptions import HTTPError

SEED = 8269
N_FUZZ = 100_000


def _make_response(status_code):
    resp = requests.models.Response()
    resp.status_code = status_code
    resp.url = "http://localhost:7777/"
    return resp


# --- ORACLE: faithful copy of patch.diff's patched fragment branch -----------
# Mirrors sphinx/builders/linkcheck.py check_uri() post-patch:
#     response = requests.get(...)
#     response.raise_for_status()          # <-- the inserted validation
#     found = check_anchor(response, ...)
#     if not found: raise Exception("Anchor '%s' not found" ...)
#   ... except HTTPError as err:
#         if   status == 401: return 'working',  ' - unauthorized', 0
#         elif status == 503: return 'ignored',  str(err),          0
#         else:               return 'broken',   str(err),          0
#       except Exception as err:            # the Anchor-not-found raise lands here
#                             return 'broken', str(err), 0   (non-ssl)
# The returned `info` string is abstracted to its SOURCE per mapping.md §2.
def oracle(status_code, found):
    response = _make_response(status_code)
    try:
        response.raise_for_status()                 # REAL callee (A-reference)
        if not found:
            raise Exception("Anchor 'x' not found")  # fragment-absent notice
        return ("working", "none", 0)
    except HTTPError as err:
        sc = err.response.status_code
        if sc == 401:
            return ("working", "unauthorized", 0)
        elif sc == 503:
            return ("ignored", "httpError", 0)
        else:
            return ("broken", "httpError", 0)
    except Exception:
        # non-HTTP exception (the Anchor-not-found raise); not an SSL error here
        return ("broken", "anchorNotFound", 0)


# --- SHADOW: Solution.lean impl region transliterated ------------------------
# classifyError (model.py pure region):
def shadow_classify_error(sc):
    if sc == 401:
        return ("working", "unauthorized", 0)
    elif sc == 503:
        return ("ignored", "httpError", 0)
    else:
        return ("broken", "httpError", 0)


# classify (model.py): isErrorStatus is the A-reference -> use the REAL callee.
def shadow(status_code, found):
    resp = _make_response(status_code)
    try:
        resp.raise_for_status()        # REAL callee left in (A-reference leg)
        is_error = False
    except HTTPError:
        is_error = True
    if is_error:
        return shadow_classify_error(status_code)
    else:
        if found:
            return ("working", "none", 0)
        else:
            return ("broken", "anchorNotFound", 0)


def fuzz_inputs(n, rng):
    # boundary statuses (the error-window edges + the two reclassified ones)
    boundary_codes = [0, 100, 199, 200, 201, 204, 301, 304, 399,
                      400, 401, 403, 404, 410, 451, 499,
                      500, 502, 503, 504, 511, 599, 600, 700]
    for sc in boundary_codes:
        for found in (True, False):
            yield (sc, found)
    for _ in range(n):
        sc = rng.randint(0, 700)
        found = rng.choice((True, False))
        yield (sc, found)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for sc, found in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh = shadow(sc, found)
        orc = oracle(sc, found)
        if sh != orc:
            disagreements.append(((sc, found), sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of checkFragmentBranch agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
