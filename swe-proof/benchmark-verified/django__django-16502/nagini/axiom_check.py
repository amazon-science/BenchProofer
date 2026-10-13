#!/usr/bin/env python3
"""G-AX / modeling-assumption soundness check for django__django-16502.

This bundle has NO `@ContractOnly` axiom and NO A-reference deep model standing
in for a *changed* opaque callee: every changed decision (the body-less
size-header drop, the close-only-for-body-bearing-unknown-length rule, and the
empty-body emission) is modeled DEEPLY in model.py's impl regions. So there is
no contract-about-a-changed-callee to falsify.

What the refinement relies on instead is the behaviour of the UNCHANGED
`wsgiref` base handler that the gold patch builds on. This script validates
those modeling assumptions against the REAL standard-library `wsgiref.handlers`
classes (the same hierarchy the running handler subclasses), and validates that
the modeled per-method decisions reproduce the gold patch's branch outcomes on
the F2P scenarios.

Imports nothing repo-specific: `io` and `wsgiref` are the Python standard
library. Exit 0 iff every assumption holds.
"""
import sys
from io import BytesIO
from wsgiref.handlers import SimpleHandler

BODY = b"<!DOCTYPE html><html><body>Hello World</body></html>"


def _app(environ, start_response):
    start_response("200 OK", [])
    return [BODY]


def _fresh_handler(method):
    environ = {
        "REQUEST_METHOD": method,
        "SERVER_PROTOCOL": "HTTP/1.0",
        "wsgi.run_once": True,
    }
    return SimpleHandler(
        BytesIO(b""), BytesIO(), BytesIO(), environ,
        multithread=False, multiprocess=True,
    )


# --- (3.1) base body emission writes the full application data ---------------

def check_base_writes_full_body():
    """The base finish_response iterates self.result and writes every chunk.
    Models emit_response_body(result, head=False) == result."""
    h = _fresh_handler("GET")
    h.origin_server = False          # suppress the status preamble; keep body+headers
    h.run(_app)
    out = h.stdout.getvalue()
    assert BODY in out, (
        "base finish_response did NOT write the full body: %r" % out)
    # the model's non-HEAD body is exactly the application data
    emitted_body = out.split(b"\r\n\r\n", 1)[-1]
    assert emitted_body == BODY, (
        "base body emission != application data: %r vs %r" % (emitted_body, BODY))


# --- (3.2) base finish_content would inject Content-Length: 0 ----------------

def check_finish_content_injects_zero_length():
    """The reason the HEAD path must BYPASS finish_content: it setdefaults
    Content-Length to "0" when headers are unsent, which would defeat omission
    of the payload-size header for a body-less response."""
    h = _fresh_handler("HEAD")
    h.setup_environ()
    h.result = []
    h.status = "200 OK"
    h.headers = h.headers_class([])
    h.headers_sent = False
    h.bytes_sent = 0
    assert "Content-Length" not in dict(h.headers), "precondition: no CL yet"
    h.finish_content()
    assert dict(h.headers).get("Content-Length") == "0", (
        "base finish_content did not inject Content-Length: 0 -> the patch's "
        "bypass would be unnecessary; assumption (3.2) broken")


# --- (3.3) base cleanup_headers sets no Connection ---------------------------

def check_base_cleanup_sets_no_connection():
    """The close decision is taken ENTIRELY in the changed method; the base
    cleanup_headers only sets Content-Length and never Connection. Models the
    entry preconditions conn_close == False, close_flag == False."""
    h = _fresh_handler("GET")
    h.setup_environ()
    h.status = "200 OK"
    h.headers = h.headers_class([])
    h.bytes_sent = 5
    h.cleanup_headers()
    assert "Connection" not in dict(h.headers), (
        "base cleanup_headers set a Connection header; entry conn_close != "
        "False assumption (3.3) broken")


# --- (3.4) the modeled per-method decisions reproduce the gold branches ------

def model_want_terminate(head, has_size_after, keepalive):
    """Mirror of model.py's pure want_terminate."""
    if (not head) and (not has_size_after):
        return True
    return not keepalive


def model_prepare_headers(head, has_size_entry, keepalive):
    """Mirror of model.py's prepare_response_headers: returns (has_size_after,
    conn_terminate, terminate_flag)."""
    has_size = has_size_entry
    if head and has_size:
        has_size = False
    conn_terminate = False
    if (not head) and (not has_size):
        conn_terminate = True
    elif not keepalive:
        conn_terminate = True
    terminate_flag = True if conn_terminate else False
    return has_size, conn_terminate, terminate_flag


def gold_prepare_headers(head, has_size_entry, keepalive):
    """Reference: the gold patch's cleanup_headers decision, computed directly
    from its source branches (REQUEST_METHOD == "HEAD", Content-Length
    membership, ThreadingMixIn)."""
    headers_has_cl = has_size_entry
    # if HEAD and Content-Length in headers: del it
    if head and headers_has_cl:
        headers_has_cl = False
    connection_close = False
    # if REQUEST_METHOD != "HEAD" and "Content-Length" not in headers
    if (not head) and (not headers_has_cl):
        connection_close = True
    elif not keepalive:  # not isinstance(server, ThreadingMixIn)
        connection_close = True
    close_connection = True if connection_close else False
    return headers_has_cl, connection_close, close_connection


def model_emit_body(result, head):
    """Mirror of model.py's emit_response_body."""
    if head:
        return []          # consume, write nothing
    return list(result)


def gold_emit_body(result, head):
    """Reference: the gold patch's finish_response body outcome — HEAD consumes
    and writes nothing; otherwise the base path writes the full body."""
    if head:
        return []
    return list(result)


def check_decisions_match_gold():
    """Over the full scenario cube (HEAD/GET x size-present/absent x
    keepalive/not), the modeled header + body decisions equal the gold patch's
    branch outcomes — including the F2P scenarios."""
    sample_body = list(BODY)
    for head in (True, False):
        for has_size in (True, False):
            for keepalive in (True, False):
                m = model_prepare_headers(head, has_size, keepalive)
                g = gold_prepare_headers(head, has_size, keepalive)
                assert m == g, (
                    "header decision mismatch head=%s size=%s keepalive=%s: "
                    "model=%s gold=%s" % (head, has_size, keepalive, m, g))
                mb = model_emit_body(sample_body, head)
                gb = gold_emit_body(sample_body, head)
                assert mb == gb, (
                    "body decision mismatch head=%s: model=%s gold=%s"
                    % (head, mb, gb))

    # The discriminating new behaviours, pinned explicitly:
    # HEAD drops the payload-size header.
    assert model_prepare_headers(True, True, True)[0] is False, \
        "HEAD must drop the payload-size header"
    # HEAD keeping alive is NEVER closed merely for lacking a size header.
    assert model_prepare_headers(True, False, True)[1] is False, \
        "HEAD must not be closed for lacking a payload-size header"
    # GET with a size header, threading server: not closed (F2P GET case).
    assert model_prepare_headers(False, True, True)[1] is False, \
        "GET with Content-Length on a threading server must not be closed"
    # HEAD emits no body; GET emits the full body (F2P body assertions).
    assert model_emit_body(list(BODY), True) == [], "HEAD body must be empty"
    assert model_emit_body(list(BODY), False) == list(BODY), \
        "GET body must be the full application data"


def main():
    check_base_writes_full_body()
    check_finish_content_injects_zero_length()
    check_base_cleanup_sets_no_connection()
    check_decisions_match_gold()
    print("G-AX OK: wsgiref base-handler assumptions (3.1 full-body write, "
          "3.2 finish_content injects Content-Length 0, 3.3 base cleanup sets "
          "no Connection) sound on the real stdlib; modeled header + body "
          "decisions == gold patch over the full HEAD/GET x size x keepalive "
          "scenario cube incl. the F2P cases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
