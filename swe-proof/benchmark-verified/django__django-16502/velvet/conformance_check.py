#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16502 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions
              (`responseBody`/`bodyFor` and `prepareMeta`/`adjustMeta`)
              transliterated to Python, over the *real* repo types via the
              mapping.md §2 bijection (REQUEST_METHOD ↔ isHead, ThreadingMixIn
              membership ↔ isThreadingServer, header presence ↔ Bool, output
              chunk bytes ↔ List Char). This bundle consumes no axiom, so the
              shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.core.servers.basehttp.ServerHandler` (the harness applies
              the gold patch before this runs, G-RESOLVE). For the body we drive
              the patched `finish_response` over a fake WSGI app exactly as the
              F2P test does; for the header descriptor we drive the patched
              `cleanup_headers` directly.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied).
stdlib + django only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import socketserver
import sys
from io import BytesIO

SEED = 16502
N_FUZZ = 100_000


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            ALLOWED_HOSTS=["*"],
            DATABASES={},
            INSTALLED_APPS=[],
        )
    django.setup()


# --- the R/I shadow: Solution.lean bodyFor / adjustMeta, transliterated ------

def shadow_body(is_head, chunks):
    """bodyFor isHead chunks: [] for a bodyless request, else in-order concat."""
    if is_head:
        return b""
    return b"".join(chunks)


def shadow_meta(is_head, is_threading, has_length, terminate, will_terminate):
    """adjustMeta isHead isThreadingServer m — the R/I shadow of prepareMeta.
    Returns (hasLength, terminate, willTerminate) after the resolution."""
    length = False if is_head else has_length
    if (not is_head) and (not length):
        term = True
    elif not is_threading:
        term = True
    else:
        term = terminate
    will = True if term else will_terminate
    return length, term, will


# --- the oracle: the patched Django ServerHandler ----------------------------

class _UnclosableBytesIO(BytesIO):
    def close(self):  # keep the buffer readable after the handler closes
        pass


def _make_server(is_threading):
    if is_threading:
        class _Server(socketserver.ThreadingMixIn):
            pass
    else:
        class _Server:
            pass
    return _Server()


def _make_handler(method, chunks, app_headers, is_threading):
    """Build a patched ServerHandler wired to a fake app + fake request handler,
    matching the F2P test's construction (tests/servers/test_basehttp.py)."""
    from django.core.servers.basehttp import ServerHandler

    stdin = BytesIO(b"")
    stdout = _UnclosableBytesIO()
    stderr = BytesIO()
    environ = {
        "REQUEST_METHOD": method,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "SERVER_NAME": "testserver",
        "SERVER_PORT": "80",
        "CONTENT_LENGTH": "0",
    }
    handler = ServerHandler(stdin, stdout, stderr, environ)
    # During a real request BaseHandler.setup_environ() populates self.environ
    # from the WSGI environ before cleanup_headers/finish_response run. The
    # oracle drives cleanup_headers() directly, so mirror that setup here: the
    # patched override reads self.environ["REQUEST_METHOD"].
    handler.environ = dict(environ)

    class _RequestHandler:
        def __init__(self):
            self.server = _make_server(is_threading)
            self.close_connection = False

        def log_request(self, *args, **kwargs):
            # The real WSGIRequestHandler logs each request; ServerHandler.close()
            # (reached at the end of handler.run) calls it. A no-op keeps the
            # buffer readable without affecting the observed body/headers.
            pass

    handler.request_handler = _RequestHandler()

    def app(env, start_response):
        start_response("200 OK", list(app_headers))
        return list(chunks)

    return handler, stdout, app


def oracle_body(method, chunks):
    """patch.diff body behaviour: run the patched finish_response and read the
    bytes after the header/body separator."""
    handler, stdout, app = _make_handler(method, chunks, [], is_threading=False)
    handler.run(app)
    out = stdout.getvalue()
    sep = out.find(b"\r\n\r\n")
    return out[sep + 4:] if sep != -1 else b""


def _prime_post_app_headers(handler, chunks, app_set_cl, app_close):
    """Reproduce the header/result/bytes_sent state the handler holds at the
    moment cleanup_headers runs (i.e. after the application has been called and
    write() recorded bytes_sent), so the base set_content_length sees the right
    `self.result`."""
    from wsgiref.headers import Headers
    total = sum(len(c) for c in chunks)
    hdr_list = []
    if app_set_cl:
        hdr_list.append(("Content-Length", str(total)))
    if app_close:
        hdr_list.append(("Connection", "close"))
    handler.headers = Headers(hdr_list)
    handler.result = list(chunks)
    handler.bytes_sent = total


def oracle_meta(method, chunks, app_set_cl, app_close, is_threading):
    """patch.diff header behaviour.

    ENTRY descriptor m (the model input): the state after the base
    `cleanup_headers` (`super().cleanup_headers()` — the first line of the
    override) but before the override's own logic.
    EXIT descriptor (the model output): the state after the full patched
    `cleanup_headers`.
    Returns (entry m, exit) as two (hasLength, terminate, willTerminate) triples."""
    from wsgiref.handlers import BaseHandler

    # entry state: run ONLY the base cleanup_headers (what super() does first)
    h_entry, _, _ = _make_handler(method, chunks, [], is_threading)
    _prime_post_app_headers(h_entry, chunks, app_set_cl, app_close)
    BaseHandler.cleanup_headers(h_entry)
    entry = ("Content-Length" in h_entry.headers,
             h_entry.headers.get("Connection") == "close",
             h_entry.request_handler.close_connection)

    # exit state: run the full patched override
    h_exit, _, _ = _make_handler(method, chunks, [], is_threading)
    _prime_post_app_headers(h_exit, chunks, app_set_cl, app_close)
    h_exit.cleanup_headers()
    exit_ = ("Content-Length" in h_exit.headers,
             h_exit.headers.get("Connection") == "close",
             h_exit.request_handler.close_connection)
    return entry, exit_


def fuzz_chunk_lists(n, rng):
    yield [b"<!DOCTYPE html><html><body>Hello World</body></html>"]  # F2P shape
    yield []
    yield [b""]
    yield [b"abc"]
    yield [b"a", b"b", b"c"]
    yield [b"\x00\xff", b"line\r\n"]
    alphabet = [bytes([b]) for b in (0, 10, 13, 32, 65, 97, 200, 255)]
    for _ in range(n):
        k = rng.randint(0, 4)
        chunks = []
        for _ in range(k):
            m = rng.randint(0, 6)
            chunks.append(b"".join(rng.choice(alphabet) for _ in range(m)))
        yield chunks


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- A. body emission (responseBody / bodyFor) --------------------------
    for chunks in fuzz_chunk_lists(N_FUZZ // 2, rng):
        for method in ("GET", "HEAD", "POST"):
            count += 1
            is_head = method == "HEAD"
            shadow = shadow_body(is_head, chunks)
            oracle = oracle_body(method, chunks)
            if shadow != oracle:
                disagreements.append(("body", method, chunks, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break

    # --- B. header descriptor (prepareMeta / adjustMeta) --------------------
    if not disagreements:
        done = False
        for chunks in fuzz_chunk_lists(N_FUZZ // 2, rng):
            for method in ("GET", "HEAD", "POST"):
                for app_set_cl in (False, True):
                    for app_close in (False, True):
                        for is_threading in (False, True):
                            count += 1
                            is_head = method == "HEAD"
                            entry, exit_ = oracle_meta(
                                method, chunks, app_set_cl, app_close, is_threading)
                            ehl, etm, ewl = entry
                            shadow = shadow_meta(is_head, is_threading, ehl, etm, ewl)
                            if shadow != exit_:
                                disagreements.append(
                                    ("meta", method,
                                     (chunks, app_set_cl, app_close, is_threading),
                                     shadow, exit_))
                                if len(disagreements) >= 5:
                                    done = True
                                    break
                        if done:
                            break
                    if done:
                        break
                if done:
                    break
            if done:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kind, method, inp, sh, orc in disagreements:
            print("  [%s] method=%s input=%r shadow=%r oracle=%r"
                  % (kind, method, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of responseBody/prepareMeta agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
