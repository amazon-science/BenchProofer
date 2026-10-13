#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16502 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls stripped (Requires/Ensures/Invariant lines removed; nothing else
changed). The @Pure helper `want_terminate` is copied over as a plain
function, and the `Resp` carrier class is reproduced with its constructor's
Ensures stripped. There are no @ContractOnly callees and no PSeq value flows
through the impl (ToSeq/PSeq appear only in the contracts), so no sequence
shim is needed; the body carrier is a plain List[int].

ORACLE: the REAL patched repo methods the model models per mapping.md --
`django.core.servers.basehttp.ServerHandler.cleanup_headers` (the
header-preparation site) and `ServerHandler.finish_response` (the
body-emission site). The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched code importable.

Type bridge (mapping.md section 2):
  * head: bool  <->  environ["REQUEST_METHOD"] == "HEAD" (exact string
    equality; any other method string, including other casings, is the
    body-bearing case). Fuzz draws "HEAD" for head=True and a spread of other
    method tokens for head=False.
  * resp.has_size: bool  <->  "Content-Length" in handler.headers. The
    model's entry value is the post-base-preparation state; the oracle
    arranges the base step to be a header no-op (the result iterable exposes
    no length, so the base step computes no size header), which makes the
    pre-set header state identical to the post-base state -- the exact entry
    state the model's precondition describes.
  * resp.conn_terminate: bool  <->  handler.headers.get("Connection") ==
    "close"; entry False (no Connection header pre-set; the base step sets
    none -- validated by axiom_check.py 3.3).
  * resp.terminate_flag: bool  <->  request_handler.close_connection; entry
    False on the fresh fake request handler.
  * keepalive: bool  <->  isinstance(request_handler.server,
    socketserver.ThreadingMixIn): True uses a ThreadingMixIn-derived server
    object, False a plain object.
  * result: List[int] of byte values  <->  the application iterable's bytes
    chunks, concatenated. The oracle splits the bytes into 1..4 chunks at
    random cut points (chunking is not observable in the model) and compares
    the concatenated emitted body bytes against bytes(shadow output).

Requires-satisfying inputs: the header precondition demands entry
conn_terminate == False and terminate_flag == False (satisfied by
construction, see bridge) and places no constraint on has_size/head/
keepalive; the body precondition demands only a readable List[int]. Boundary
cases cover the full head x has_size x keepalive cube (several method tokens
per cell) and body edge shapes (empty, single byte, 0/255 values, long
bodies, bodies containing header-terminator byte patterns); fuzz draws
55,000 header cases and 45,000 body cases.

>= 1e5 Requires-satisfying inputs: boundary cases + 100,000 fuzz cases.
Pinned fuzz seed: 16502.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import socketserver
import sys
from io import BytesIO

SEED = 16502
N_FUZZ_HEADERS = 55_000
N_FUZZ_BODY = 45_000


# --- pure helper from model.py, decorator + docstring contracts stripped -----

def want_terminate(head, has_size_after, keepalive):
    if (not head) and (not has_size_after):
        return True
    return not keepalive


# --- the Resp carrier from model.py, constructor Ensures stripped ------------

class Resp:
    def __init__(self, has_size):
        self.has_size = has_size  # type: bool
        self.conn_terminate = False  # type: bool
        self.terminate_flag = False  # type: bool


# --- the impl region of prepare_response_headers, verbatim -------------------

def prepare_response_headers(resp, head, keepalive):
    # Drop the payload-size header for a body-less method.
    if head and resp.has_size:
        resp.has_size = False
    # Ask to terminate only for a body-bearing method of unknown length,
    # otherwise only when the environment cannot keep connections alive.
    if (not head) and (not resp.has_size):
        resp.conn_terminate = True
    elif not keepalive:
        resp.conn_terminate = True
    # Mirror the terminate decision onto the handler flag.
    if resp.conn_terminate:
        resp.terminate_flag = True


# --- the impl region of emit_response_body, verbatim (Invariants stripped) ---

def emit_response_body(result, head):
    out = []  # type: List[int]
    if head:
        # The body-less branch contributes nothing to the output.
        return out
    j = 0
    while j < len(result):
        out.append(result[j])
        j = j + 1
    return out


# --- oracle plumbing ----------------------------------------------------------

class _ThreadingServer(socketserver.ThreadingMixIn):
    """keepalive=True carrier: a server object of a ThreadingMixIn class."""


class _PlainServer:
    """keepalive=False carrier: a server object with no ThreadingMixIn."""


class _FakeRequestHandler:
    """Just enough of the per-request handler for the methods under test:
    the server object (keepalive classification), the close_connection flag
    the terminate decision is mirrored onto, and the log hook close() uses."""

    def __init__(self, keepalive):
        self.server = _ThreadingServer() if keepalive else _PlainServer()
        self.close_connection = False

    def log_request(self, *args, **kwargs):
        pass


def _fresh_handler(ServerHandler, method):
    environ = {
        "REQUEST_METHOD": method,
        "SERVER_PROTOCOL": "HTTP/1.0",
        "wsgi.run_once": True,
    }
    return ServerHandler(BytesIO(b""), BytesIO(), BytesIO(), environ)


def real_prepare_headers(ServerHandler, method, has_size_entry, keepalive):
    """Drive the REAL patched header-preparation method and return the
    observable triple (has_size_after, conn_terminate, terminate_flag).

    Entry-state bridge: the result iterable exposes no length, so the base
    preparation step leaves the header set exactly as constructed here --
    the constructed state IS the post-base entry state the model describes.
    No Connection header is pre-set and close_connection starts False,
    matching the model's entry preconditions."""
    h = _fresh_handler(ServerHandler, method)
    h.setup_environ()
    h.status = "200 OK"
    entry = [("Content-Length", "1234")] if has_size_entry else []
    h.headers = h.headers_class(entry)
    h.result = iter(())          # no __len__: base step computes no size header
    h.bytes_sent = 0
    h.request_handler = _FakeRequestHandler(keepalive)
    h.cleanup_headers()
    return (
        "Content-Length" in h.headers,
        h.headers.get("Connection") == "close",
        bool(h.request_handler.close_connection),
    )


def real_emit_body(ServerHandler, method, chunks, send_size_header):
    """Drive the REAL patched body-emission path end-to-end (a full handler
    run with an application returning the given bytes chunks) and return the
    emitted body bytes (everything after the header terminator)."""
    total = sum(len(c) for c in chunks)

    def app(environ, start_response):
        hdrs = [("Content-Length", str(total))] if send_size_header else []
        start_response("200 OK", hdrs)
        return list(chunks)

    h = _fresh_handler(ServerHandler, method)
    h.origin_server = False      # suppress the status preamble; keep headers+body
    h.request_handler = _FakeRequestHandler(True)
    h.run(app)
    out = h.stdout.getvalue()
    head_part, sep, body_part = out.partition(b"\r\n\r\n")
    if not sep:
        return None              # no header terminator: surface as disagreement
    return body_part


# --- differential drivers -------------------------------------------------------

def check_header_case(ServerHandler, method, has_size_entry, keepalive):
    head = (method == "HEAD")
    resp = Resp(has_size_entry)
    prepare_response_headers(resp, head, keepalive)
    shadow = (resp.has_size, resp.conn_terminate, resp.terminate_flag)
    real = real_prepare_headers(ServerHandler, method, has_size_entry, keepalive)
    if shadow != real:
        return ("DISAGREEMENT (headers)\n  method=%r has_size_entry=%r "
                "keepalive=%r\n  shadow(has_size, conn_terminate, "
                "terminate_flag)=%r\n  real  (has_size, conn_terminate, "
                "terminate_flag)=%r"
                % (method, has_size_entry, keepalive, shadow, real))
    # want_terminate is part of the impl region's spec vocabulary; cross-check
    # it against the same observation for free.
    if want_terminate(head, real[0], keepalive) != real[1]:
        return ("DISAGREEMENT (want_terminate)\n  method=%r has_size_entry=%r "
                "keepalive=%r\n  want_terminate=%r real terminate=%r"
                % (method, has_size_entry, keepalive,
                   want_terminate(head, real[0], keepalive), real[1]))
    return None


def check_body_case(ServerHandler, method, body_bytes, chunks, send_size_header):
    head = (method == "HEAD")
    shadow = bytes(emit_response_body(list(body_bytes), head))
    real = real_emit_body(ServerHandler, method, chunks, send_size_header)
    if real is None or shadow != real:
        return ("DISAGREEMENT (body)\n  method=%r body=%r chunks=%r "
                "size_header=%r\n  shadow=%r\n  real=%r"
                % (method, body_bytes, chunks, send_size_header, shadow, real))
    return None


BODY_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE",
                "head", "Head", "GETX", "M-SEARCH"]


def header_boundary_cases():
    cases = []
    for method in ["HEAD"] + BODY_METHODS:
        for has_size in (True, False):
            for keepalive in (True, False):
                cases.append((method, has_size, keepalive))
    return cases


def body_boundary_cases():
    bodies = [
        b"",
        b"\x00",
        b"\xff",
        b"a",
        b"<!DOCTYPE html><html><body>Hello World</body></html>",
        b"\r\n\r\n",                      # body containing a terminator pattern
        b"x" * 1 + b"\r\n\r\n" + b"y" * 3,
        bytes(range(256)),
        b"z" * 2048,
    ]
    cases = []
    for body in bodies:
        for method in ("HEAD", "GET", "POST"):
            for send_size in (True, False):
                # one-chunk and two-chunk splits
                cases.append((method, body, (body,), send_size))
                mid = len(body) // 2
                cases.append((method, body, (body[:mid], body[mid:]), send_size))
    return cases


def rand_chunks(rng, body):
    n = rng.randint(1, 4)
    cuts = sorted(rng.randint(0, len(body)) for _ in range(n - 1))
    parts, prev = [], 0
    for c in cuts:
        parts.append(body[prev:c])
        prev = c
    parts.append(body[prev:])
    return tuple(parts)


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure()
            try:
                django.setup()
            except Exception:
                pass
    except Exception:
        pass
    # REAL patched callee holder: the development-server handler class whose
    # header-preparation and body-emission methods the model models.
    from django.core.servers.basehttp import ServerHandler

    checked = 0

    # ---- header site: boundary (full cube, several method tokens) ----------
    hdr_boundary = header_boundary_cases()
    for method, has_size, keepalive in hdr_boundary:
        err = check_header_case(ServerHandler, method, has_size, keepalive)
        if err:
            print(err)
            return 1
        checked += 1

    # ---- body site: boundary shapes ----------------------------------------
    body_boundary = body_boundary_cases()
    for method, body, chunks, send_size in body_boundary:
        err = check_body_case(ServerHandler, method, body, chunks, send_size)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)

    # ---- header site: fuzz ---------------------------------------------------
    for _ in range(N_FUZZ_HEADERS):
        if rng.random() < 0.5:
            method = "HEAD"
        else:
            method = rng.choice(BODY_METHODS)
        has_size = rng.random() < 0.5
        keepalive = rng.random() < 0.5
        err = check_header_case(ServerHandler, method, has_size, keepalive)
        if err:
            print(err)
            return 1
        checked += 1

    # ---- body site: fuzz -------------------------------------------------------
    for _ in range(N_FUZZ_BODY):
        method = "HEAD" if rng.random() < 0.5 else rng.choice(BODY_METHODS)
        if rng.random() < 0.9:
            length = rng.randint(0, 64)
        else:
            length = rng.randint(65, 2048)
        body = bytes(rng.randint(0, 255) for _ in range(length))
        chunks = rand_chunks(rng, body)
        send_size = rng.random() < 0.5
        err = check_body_case(ServerHandler, method, body, chunks, send_size)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched handler on %d inputs "
          "(%d header-boundary + %d body-boundary + %d header-fuzz + "
          "%d body-fuzz, seed %d)."
          % (checked, len(hdr_boundary), len(body_boundary),
             N_FUZZ_HEADERS, N_FUZZ_BODY, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
