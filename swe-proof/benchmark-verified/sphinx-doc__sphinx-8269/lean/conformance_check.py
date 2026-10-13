#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8269.

The bundle models ONE behavior: how the anchor-enabled link-check path of
`CheckExternalLinksBuilder.check_thread.check_uri`
(sphinx/builders/linkcheck.py) classifies one external link into its
`(status, info, code)` outcome. The modeled value is a pure function of five
observables (mapping.md):

    statusCode   : int    (response.status_code of the GET reply)
    anchorFound  : bool    (check_anchor(response, unquote(anchor)))
    httpErrMsg   : str     (str(err) for the raised HTTPError)
    anchorErrMsg : str     ("Anchor '%s' not found" % anchor)
    onSuccess    : (str,str,int)  (the unchanged success/redirect tail outcome)

Post-patch rule (the gold fix `response.raise_for_status()` + the existing
`except HTTPError` dispatch + the anchor branch):

    if 400 <= statusCode < 600:                # raise_for_status() raises HTTPError
        if statusCode == 401: return ('working', ' - unauthorized', 0)
        elif statusCode == 503: return ('ignored', httpErrMsg, 0)
        else: return ('broken', httpErrMsg, 0)
    else:                                       # status fine -> consult the fragment
        if not anchorFound: return ('broken', anchorErrMsg, 0)
        else: return onSuccess

`requests.Response.raise_for_status` raises `HTTPError` for exactly the codes in
[400, 600); below 400 it is a no-op. So the error status takes precedence over the
fragment search — the bug fixed here. Standing up a live HTTP server + the full
Sphinx builder to drive the real `check_uri` is heavy and unnecessary: the modeled
value is this pure classification over the observables. So the ORACLE below is a
faithful in-process replica using the EXACT patched control flow (the
raise_for_status threshold + HTTPError dispatch + anchor branch), and the SHADOW
is the op-for-op transliteration of `implementation_classifyLink` (refinement.md).

To make the raise_for_status threshold non-trivial we drive the oracle's
threshold through the REAL `requests.Response.raise_for_status` where available
(constructing a Response with the given status_code); if `requests` is not
importable in-container we fall back to the documented [400, 600) rule. Either
way the oracle's dispatch matches the patched code.

stdlib-only (+ optional requests). Pinned seed: 8269 (also in mapping.md).
"""
import random
import sys

SEED = 8269
N = 120_000

# --- the raise_for_status threshold, exercised through the REAL callee if we can.
try:
    import requests

    def _raises_http_error(status_code):
        r = requests.Response()
        r.status_code = status_code
        r.url = "http://localhost/"
        try:
            r.raise_for_status()
            return False
        except requests.exceptions.HTTPError:
            return True
    _RAISE_SRC = "requests.Response.raise_for_status"
except Exception:  # pragma: no cover - container always has requests
    def _raises_http_error(status_code):
        return 400 <= status_code < 600
    _RAISE_SRC = "documented [400,600) rule (requests unavailable)"


# --- ORACLE: faithful in-process replica of the patched check_uri classification.
def oracle(status_code, anchor_found, http_err_msg, anchor_err_msg, on_success):
    if _raises_http_error(status_code):
        # except HTTPError dispatch (linkcheck.py:186-194)
        if status_code == 401:
            return ("working", " - unauthorized", 0)
        elif status_code == 503:
            return ("ignored", http_err_msg, 0)
        else:
            return ("broken", http_err_msg, 0)
    else:
        # status fine -> check_anchor result governs (anchor branch)
        if not anchor_found:
            return ("broken", anchor_err_msg, 0)
        else:
            return on_success


# --- SHADOW of implementation_classifyLink (the R/I leg, op-for-op) -----------
def shadow(status_code, anchor_found, http_err_msg, anchor_err_msg, on_success):
    # op 1: deeply-modeled raise_for_status threshold 400 <= code < 600
    if 400 <= status_code and status_code < 600:
        if status_code == 401:                                  # op 2
            return ("working", " - unauthorized", 0)
        if status_code == 503:                                  # op 3
            return ("ignored", http_err_msg, 0)
        return ("broken", http_err_msg, 0)                      # op 4
    if anchor_found == False:                                   # op 5
        return ("broken", anchor_err_msg, 0)
    return on_success                                           # op 6 (A-reference)


def disagree(args):
    o = oracle(*args)
    s = shadow(*args)
    if o != s:
        return (args, o, s)
    return None


MSG_POOL = [
    "500 Server Error: Internal Server Error for url: http://localhost:7777/",
    "404 Client Error: Not Found for url: http://x/",
    "Anchor 'test' not found",
    "Anchor 'top' not found",
    "", "x", "503 Server Error: Service Unavailable for url: http://y/",
]
SUCCESS_POOL = [
    ("working", "", 0),
    ("redirected", "http://x/#a", 301),
    ("redirected", "http://y/", 0),
    ("working", "old", 0),
]


def _edge_cases():
    cases = []
    # FAIL_TO_PASS shape: 500 error, fragment absent -> must report the HTTP msg.
    cases.append((500, False, "500 Server Error: Internal Server Error for url: http://localhost:7777/",
                  "Anchor 'anchor' not found", ("working", "", 0)))
    # 500 but fragment present -> still the HTTP error wins.
    cases.append((500, True, "500 err", "Anchor not found", ("working", "", 0)))
    # raise threshold boundaries.
    cases.append((399, False, "h", "a", ("working", "", 0)))   # no raise
    cases.append((400, True, "h", "a", ("working", "", 0)))    # raise (broken)
    cases.append((599, True, "h", "a", ("working", "", 0)))    # raise (broken)
    cases.append((600, False, "h", "a", ("working", "", 0)))   # no raise -> anchor
    # special codes.
    cases.append((401, False, "h", "a", ("redirected", "z", 302)))  # working/unauth
    cases.append((503, False, "h", "a", ("working", "", 0)))        # ignored
    # non-error, fragment found -> defer to success tail.
    cases.append((200, True, "h", "a", ("redirected", "http://q/#f", 301)))
    cases.append((200, False, "h", "Anchor 'x' not found", ("working", "", 0)))
    cases.append((301, True, "h", "a", ("redirected", "http://r/", 0)))
    return cases


def main() -> int:
    checked = 0
    for args in _edge_cases():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    # status code pool biased to the boundaries and special codes.
    boundary = [100, 199, 200, 301, 302, 308, 399, 400, 401, 403, 404, 429,
                500, 502, 503, 504, 599, 600]
    for _ in range(N):
        if rng.random() < 0.5:
            status_code = rng.choice(boundary)
        else:
            status_code = rng.randint(100, 620)
        anchor_found = rng.choice([True, False])
        http_err = rng.choice(MSG_POOL)
        anchor_err = rng.choice(MSG_POOL)
        on_success = rng.choice(SUCCESS_POOL)
        d = disagree((status_code, anchor_found, http_err, anchor_err, on_success))
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"raise_threshold_source={_RAISE_SRC}")
    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
