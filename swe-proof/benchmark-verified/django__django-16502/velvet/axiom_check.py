#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16502.

The bundle consumes NO `axiom`. The two unchanged lower-layer callees the
changed functions (`finish_response`, `cleanup_headers`) sit on top of are
abstracted in Solution.lean as free inputs (`chunks`, `ResponseMeta.hasLength`).
This check validates the two behavioural REFERENCE properties the refinement
relies on, against the REAL standard-library base WSGI handler
(`wsgiref.handlers.BaseHandler`, reached in the gold patch via `super()`):

  (A-reference 1)  Body emission order. The base `finish_response` write loop
      (`for data in self.result: self.write(data)`) emits the application's
      output chunks IN ORDER, VERBATIM, so the body written for a body-bearing
      request equals the in-order concatenation `b"".join(self.result)` — exactly
      `bodyFor false chunks = chunks.flatten`. (mapping.md §3.1.)

  (A-reference 2)  Length-declaration rule. The base `cleanup_headers` /
      `set_content_length` declares a `Content-Length` iff the application did
      not already set one AND the result is a single block (`len(result) == 1`),
      with the additional base quirk that an empty result list leaves the
      headers unsent until `finish_content`, which defaults `Content-Length` to
      "0". This is exactly the entry value of `ResponseMeta.hasLength` the model
      reads (mapping.md §3.2).

Imports only the standard library (`wsgiref`, the very module the gold patch's
`super()` calls dispatch into); no repo-test code, no Django. Exit 0 iff every
obligation holds.
"""
import random
import sys
from io import BytesIO
from wsgiref.handlers import SimpleHandler  # stdlib base WSGI handler


def _run_base(method, chunks, app_set_cl):
    """Drive the REAL stdlib base WSGI handler over a fake app and return
    (body_bytes, content_length_present). No override — this is the base callee
    the gold patch delegates to via super() (Django's ServerHandler ultimately
    extends wsgiref.handlers.SimpleHandler; we exercise the un-overridden base
    finish_response / cleanup_headers write path)."""
    stdin, stdout, stderr = BytesIO(b""), BytesIO(), BytesIO()
    environ = {
        "REQUEST_METHOD": method,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "SERVER_NAME": "testserver",
        "SERVER_PORT": "80",
    }
    handler = SimpleHandler(stdin, stdout, stderr, environ,
                            multithread=False, multiprocess=False)
    handler.server_software = "test"

    def app(env, start_response):
        hdrs = []
        if app_set_cl:
            hdrs.append(("Content-Length", str(sum(len(c) for c in chunks))))
        start_response("200 OK", hdrs)
        return list(chunks)

    handler.run(app)
    out = stdout.getvalue()
    sep = out.find(b"\r\n\r\n")
    header_block = out[:sep] if sep != -1 else out
    body = out[sep + 4:] if sep != -1 else b""
    cl_present = b"content-length:" in header_block.lower()
    return body, cl_present


def ref_entry_haslength(is_head, app_set_cl, n):
    """The A-reference 2 rule the model abstracts: whether a length declaration
    is present after the base callee runs (before the override clears it)."""
    if app_set_cl:
        return True
    if n == 1:
        return True
    if n == 0 and not is_head:   # base finish_content setdefault 'Content-Length'="0"
        return True
    return False


def check_body_emission(chunks, app_set_cl):
    """A-reference 1: base body emission == in-order concatenation."""
    body, _ = _run_base("GET", chunks, app_set_cl)
    expected = b"".join(chunks)
    assert body == expected, (
        "base body emission not in-order concatenation: chunks=%r emitted=%r "
        "expected=%r" % (chunks, body, expected))


def check_length_rule(chunks, app_set_cl):
    """A-reference 2: base length-declaration presence matches the reference
    rule the model reads as `hasLength` (validated for the GET/body-bearing
    path, which is the path the base callee governs)."""
    _, cl_present = _run_base("GET", chunks, app_set_cl)
    expected = ref_entry_haslength(False, app_set_cl, len(chunks))
    assert cl_present == expected, (
        "base length-declaration rule mismatch: chunks=%r app_set_cl=%r "
        "base_present=%r reference=%r"
        % (chunks, app_set_cl, cl_present, expected))


def main():
    # boundary chunk lists: empty, single (the F2P shape), multi, empty-bytes.
    boundary = [
        [],
        [b""],
        [b"<!DOCTYPE html><html><body>Hello World</body></html>"],
        [b"abc"],
        [b"", b"abc"],
        [b"a", b"b", b"c"],
        [b"\x00\x01\x02", b"\xff"],
        [b"x" * 1000],
    ]
    for chunks in boundary:
        for app_set_cl in (False, True):
            check_body_emission(chunks, app_set_cl)
            check_length_rule(chunks, app_set_cl)

    # randomized fuzz over chunk lists.
    rng = random.Random(16502)
    alphabet = [bytes([b]) for b in (0, 10, 13, 32, 65, 97, 200, 255)]
    n_fuzz = 5000
    for _ in range(n_fuzz):
        k = rng.randint(0, 5)
        chunks = []
        for _ in range(k):
            m = rng.randint(0, 6)
            chunks.append(b"".join(rng.choice(alphabet) for _ in range(m)))
        app_set_cl = rng.random() < 0.5
        check_body_emission(chunks, app_set_cl)
        check_length_rule(chunks, app_set_cl)

    print("G-AX OK: base WSGI handler emits the body as the in-order chunk "
          "concatenation (A-reference 1) and declares Content-Length per the "
          "modeled rule (A-reference 2) over %d boundary + %d fuzz chunk lists."
          % (len(boundary) * 2, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
