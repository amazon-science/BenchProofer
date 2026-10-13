#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-1142.

This bundle has NO axiomatized callee: the changed operation (the guarded
announcement of the body-size header) is modeled DEEPLY in model.py's impl
region, so there is no `@ContractOnly` contract to validate against a real
callee. What G-AX checks here instead is the *deep-model self-consistency*: the
behaviour model.py specifies for `prepare_content_length` must coincide, on
every input, with the behaviour the gold patch's `prepare_content_length`
produces.

To keep this stdlib-only (no repo import needed), `gold_prepare_content_length`
below is a line-for-line transcription of the GOLD-PATCHED function body
(requests/models.py:388 post-patch) operating on a plain dict and the lifted
body observations. `model_spec` is the decision table model.py's postcondition
pins. The check asserts they agree over boundary + fuzz inputs (presence of the
size header and its value), with special attention to the discriminating
bodyless GET / HEAD case. Exit 0 iff every observation agrees.
"""
import random
import sys

# header-name token and method tokens, in lock-step with model.py's pure region
SIZE_HEADER = 0
METHOD_GET = 1
METHOD_HEAD = 2


def gold_prepare_content_length(headers, method, seekable, stream_len,
                                body_present, body_len):
    """Line-for-line transcription of the GOLD-PATCHED body:

        if hasattr(body,'seek') and hasattr(body,'tell'):
            ... headers['Content-Length'] = str(body.tell())
        elif body is not None:
            headers['Content-Length'] = str(len(body))
        elif self.method not in ('GET','HEAD'):
            headers['Content-Length'] = '0'

    on the lifted observations: `seekable`==(has seek+tell),
    `stream_len`==body.tell(), `body_present`==(body is not None),
    `body_len`==len(body), `method` the verb token, and `headers` a dict whose
    key SIZE_HEADER models the 'Content-Length' header (value = the int size).
    """
    if seekable:
        headers[SIZE_HEADER] = stream_len
    elif body_present:
        headers[SIZE_HEADER] = body_len
    elif method not in (METHOD_GET, METHOD_HEAD):
        headers[SIZE_HEADER] = 0


def model_spec(headers, method, seekable, stream_len, body_present, body_len):
    """The decision table model.py's postcondition pins (clauses 1-4), applied
    to a fresh header map. Returns the post-state header map."""
    out = dict(headers)
    if seekable:
        out[SIZE_HEADER] = stream_len            # clause 1
    elif body_present:
        out[SIZE_HEADER] = body_len              # clause 2
    else:
        # clause 3: present iff payload-carrying method; value 0 when present
        if method != METHOD_GET and method != METHOD_HEAD:
            out[SIZE_HEADER] = 0
    return out


def check(method, seekable, stream_len, body_present, body_len):
    # model.py precondition: size header absent initially; seekable => present
    if seekable and not body_present:
        return
    h_gold = {}
    gold_prepare_content_length(h_gold, method, seekable, stream_len,
                                body_present, body_len)
    h_model = model_spec({}, method, seekable, stream_len,
                         body_present, body_len)
    assert h_gold == h_model, (
        "deep model disagrees with gold patch: method=%r seekable=%r "
        "stream_len=%r body_present=%r body_len=%r -> gold=%r model=%r"
        % (method, seekable, stream_len, body_present, body_len,
           h_gold, h_model))


def main():
    methods = [METHOD_GET, METHOD_HEAD, 3, 4, 5]   # GET, HEAD, POST/PUT/...
    bools = [False, True]

    # --- boundary cases: the discriminating bodyless rows --------------------
    boundary = []
    for m in methods:
        # bodyless: not seekable, not present -> the heart of the fix
        boundary.append((m, False, 0, False, 0))
        # non-stream body present
        boundary.append((m, False, 0, True, 0))
        boundary.append((m, False, 0, True, 42))
        # seekable stream
        boundary.append((m, True, 0, True, 0))
        boundary.append((m, True, 7, True, 99))
    for args in boundary:
        check(*args)

    # explicit discriminator assertions (the F2P + its complement)
    assert SIZE_HEADER not in model_spec({}, METHOD_GET, False, 0, False, 0), \
        "bodyless GET must announce no size header"
    assert SIZE_HEADER not in model_spec({}, METHOD_HEAD, False, 0, False, 0), \
        "bodyless HEAD must announce no size header"
    assert model_spec({}, 3, False, 0, False, 0).get(SIZE_HEADER) == 0, \
        "bodyless payload-carrying method must announce zero size"

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(1142)
    for _ in range(50000):
        m = rng.choice(methods + [rng.randint(-3, 9)])
        seekable = rng.choice(bools)
        body_present = True if seekable else rng.choice(bools)
        stream_len = rng.randint(0, 1 << 20)
        body_len = rng.randint(0, 1 << 20)
        check(m, seekable, stream_len, body_present, body_len)

    print("G-AX OK: deep model == gold-patched prepare_content_length on "
          "%d boundary + 50000 fuzz inputs (no axiom; deep-model "
          "self-consistency)" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
