#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_prepare_content_length against the patch.diff behaviour (the
POST-patch `prepare_content_length`).

The impl region is entirely R/I (a finite case analysis + one mutable header
slot); there is no A-tagged callee. Per the type bijection in mapping.md the
modeled domain is:

  method : str        -- the normalized (upper-cased) HTTP method
  pre    : Option str -- the Content-Length slot's value BEFORE the call
                         (None => header absent; user headers are copied in by
                         prepare_headers before prepare_body runs)
  body   : Option n   -- `None` => no body; `n: Nat` => a body of content length n
  result : Option str -- the value of the Content-Length header AFTER the call
                         (None => absent)

The Lean impl's body-length op is a TYPE REFINEMENT of the real code's two
length-producing branches (`body.tell()` for a seekable stream, `len(body)` for a
measurable value): both render the content length in decimal, so over the refined
domain they coincide and are realised here as `str(n)`.

`shadow(method, pre, body)` reproduces the Lean impl op-for-op.
`patched(method, pre, body)` is an independent reconstruction of the POST-patch
`prepare_content_length` body run against a concrete `requests`-style object
whose headers dict is pre-seeded per `pre` and whose `body` realises the abstract
`Option n` (None, a measurable `bytes` of length n, or a seekable stream of
length n). We assert zero disagreements over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import io
import random
import sys

SEED = 1142           # pinned in mapping.md
N = 120_000           # >= 10^5

METHODS = ["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE"]

PRES = [None, "0", "5", "99", "1234", ""]   # pre-call Content-Length slot values


def shadow(method, pre, body):
    """R/I shadow of implementation_prepare_content_length:
        clen = pre                        -- let mut clen := pre
        match body:
          some n: clen = str(n)           -- clen := some (toString n)
          none:   if method not in (GET,HEAD): clen = "0"
                  (else: no write -> clen keeps pre)
        return clen
    `body` here is the abstract Option: None or an int length n."""
    clen = pre
    if body is not None:
        clen = str(body)                  # toString n
    else:
        if method != "GET" and method != "HEAD":
            clen = "0"
    return clen


def _seed_headers(pre):
    """Realise the abstract pre-call slot state as a headers dict."""
    headers = {}
    if pre is not None:
        headers['Content-Length'] = pre
    return headers


def _patched_concrete(method, pre, concrete):
    """Independent reconstruction of the POST-patch prepare_content_length body,
    run against an already-concrete body object and a pre-seeded headers dict:

        if hasattr(body, 'seek') and hasattr(body, 'tell'):
            body.seek(0, 2)
            headers['Content-Length'] = str(body.tell())
            body.seek(0, 0)
        elif body is not None:
            headers['Content-Length'] = str(len(body))
        elif self.method not in ('GET', 'HEAD'):
            headers['Content-Length'] = '0'

    Returns the Content-Length header value (None => header absent)."""
    headers = _seed_headers(pre)
    if hasattr(concrete, 'seek') and hasattr(concrete, 'tell'):
        concrete.seek(0, 2)
        headers['Content-Length'] = str(concrete.tell())
        concrete.seek(0, 0)
    elif concrete is not None:
        headers['Content-Length'] = str(len(concrete))
    elif method not in ('GET', 'HEAD'):
        headers['Content-Length'] = '0'
    return headers.get('Content-Length', None)


def _bytes_body(n):
    return b"x" * n


def _stream_body(n):
    return io.BytesIO(b"x" * n)


def main():
    rng = random.Random(SEED)

    # Deterministic boundary cases first (incl. the exact F2P discriminators).
    fixed = [
        ("GET", None, None), ("HEAD", None, None),   # F2P: header must stay absent
        ("GET", "99", None), ("HEAD", "42", None),   # no write -> pre retained
        ("GET", "0", None), ("HEAD", "", None),
        ("POST", None, None), ("PUT", None, None),   # no body, may carry payload -> "0"
        ("POST", "99", None), ("DELETE", "7", None), # pre clobbered by "0"
        ("GET", None, 0), ("GET", "99", 7), ("HEAD", None, 123),  # body -> length even for GET/HEAD
        ("POST", None, 0), ("POST", "5", 1), ("DELETE", None, 42),
        ("get", None, None), ("Get", "9", None),     # only the normalized verbs are suppressed
    ]
    cases = list(fixed)
    for _ in range(N):
        m = rng.choice(METHODS)
        p = rng.choice(PRES)
        b = None if rng.random() < 0.4 else rng.randint(0, 5000)
        cases.append((m, p, b))

    disagreements = 0
    examples = []
    for method, pre, body in cases:
        got = shadow(method, pre, body)
        # exercise both length branches of the real code for present bodies
        if body is None:
            want = _patched_concrete(method, pre, None)
        else:
            want_bytes = _patched_concrete(method, pre, _bytes_body(body))
            want_stream = _patched_concrete(method, pre, _stream_body(body))
            if want_bytes != want_stream:
                disagreements += 1
                if len(examples) < 10:
                    examples.append((method, pre, body,
                                     f"bytes={want_bytes}", f"stream={want_stream}"))
                continue
            want = want_bytes
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((method, pre, body, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for ex in examples:
            print(f"  {ex}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
