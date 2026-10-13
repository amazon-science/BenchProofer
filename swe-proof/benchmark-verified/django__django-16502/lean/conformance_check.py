#!/usr/bin/env python3
"""G-CONF for django__django-16502.

Differential test: the R/I Python shadow of `implementation_headerPolicy` and
`implementation_bodyEmission` (Solution.lean) vs. an independent reconstruction
of the post-patch behaviour of `ServerHandler.cleanup_headers` and
`ServerHandler.finish_response` (django/core/servers/basehttp.py), transcribed
straight from the patched source.

The orchestrator applies the gold patch before running this, so the transcribed
`patched_*` functions reflect the post-patch source.

Type bridge (mapping.md):
  - REQUEST_METHOD == "HEAD"            <-> is_head : bool
  - "Content-Length" in self.headers   <-> content_length_set / *_present : bool
  - isinstance(server, ThreadingMixIn) <-> is_threading : bool
  - self.headers.get("Connection")=="close" (entry) <-> app_disconnect : bool
  - final Connection==close / close_connection      <-> connection_disconnect
  - WSGI result iterator written as body            <-> body_emitted : bool
  - self.headers_sent                               <-> headers_sent : bool

Inputs are booleans: headerPolicy has 4 (2^4 enumerated), bodyEmission has 2
(2^2 enumerated); random fill exceeds 1e5 total. Exit 0 iff zero disagreements.
stdlib-only.
"""
import itertools
import random
import sys

SEED = 16502
N_RANDOM = 120_000


# ---------------- R/I shadow of the Lean impls ----------------

def shadow_header(c):
    """R/I shadow of implementation_headerPolicy (op-for-op)."""
    cl_present = c["content_length_set"]
    if c["is_head"] and cl_present:
        cl_present = False
    disconnect = c["app_disconnect"]
    if (not c["is_head"]) and (not cl_present):
        disconnect = True
    elif not c["is_threading"]:
        disconnect = True
    return {"content_length_present": cl_present,
            "connection_disconnect": disconnect}


def shadow_body(c):
    """R/I shadow of implementation_bodyEmission (op-for-op)."""
    if c["is_head"]:
        sent = c["headers_already_sent"]
        if not sent:
            sent = True
        return {"body_emitted": False, "headers_sent": sent}
    else:
        return {"body_emitted": True, "headers_sent": True}


# ---------------- independent reconstruction of patched source ----------------

def patched_header(c):
    """Transcribed from post-patch ServerHandler.cleanup_headers.

        # super().cleanup_headers() has already run: it leaves a Content-Length
        # header present iff content_length_set, and (here) any pre-existing
        # Connection: close iff app_disconnect.
        headers = {"Content-Length": present} (as membership)
        connection = "close" if app_disconnect else None

        if REQUEST_METHOD == "HEAD" and "Content-Length" in headers:
            del headers["Content-Length"]
        if REQUEST_METHOD != "HEAD" and "Content-Length" not in headers:
            headers["Connection"] = "close"
        elif not isinstance(server, ThreadingMixIn):
            headers["Connection"] = "close"
        # (close_connection set True iff Connection == "close")
    """
    is_head = c["is_head"]
    cl_in = c["content_length_set"]
    # app may already have set Connection: close
    connection_close = c["app_disconnect"]

    if is_head and cl_in:
        cl_in = False  # del Content-Length
    if (not is_head) and (not cl_in):
        connection_close = True
    elif not c["is_threading"]:
        connection_close = True
    return {"content_length_present": cl_in,
            "connection_disconnect": connection_close}


def patched_body(c):
    """Transcribed from post-patch ServerHandler.finish_response.

        def finish_response(self):
            if REQUEST_METHOD == "HEAD":
                try:
                    deque(self.result, maxlen=0)   # consume, write no body
                    if not self.headers_sent:
                        self.send_headers()        # ensures headers_sent
                finally:
                    self.close()
            else:
                super().finish_response()          # writes headers then body
    """
    is_head = c["is_head"]
    if is_head:
        headers_sent = c["headers_already_sent"]
        if not headers_sent:
            headers_sent = True
        return {"body_emitted": False, "headers_sent": headers_sent}
    else:
        # super().finish_response() emits headers then the body.
        return {"body_emitted": True, "headers_sent": True}


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    count = 0

    def check_h(c):
        nonlocal disagreements, count
        count += 1
        g, w = shadow_header(c), patched_header(c)
        if g != w:
            disagreements += 1
            if len(examples) < 10:
                examples.append(("header", c, g, w))

    def check_b(c):
        nonlocal disagreements, count
        count += 1
        g, w = shadow_body(c), patched_body(c)
        if g != w:
            disagreements += 1
            if len(examples) < 10:
                examples.append(("body", c, g, w))

    HFIELDS = ["is_head", "content_length_set", "is_threading", "app_disconnect"]
    BFIELDS = ["is_head", "headers_already_sent"]

    # exhaustive enumeration
    for combo in itertools.product([False, True], repeat=len(HFIELDS)):
        check_h(dict(zip(HFIELDS, combo)))
    for combo in itertools.product([False, True], repeat=len(BFIELDS)):
        check_b(dict(zip(BFIELDS, combo)))

    # random fill to exceed 1e5
    for _ in range(N_RANDOM):
        check_h({f: rng.random() < 0.5 for f in HFIELDS})
        check_b({f: rng.random() < 0.5 for f in BFIELDS})

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for kind, c, g, w in examples:
            print(f"  [{kind}] in={c!r}\n    shadow={g!r}\n    patched={w!r}")
        return 1

    print(f"G-CONF OK: {count} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
