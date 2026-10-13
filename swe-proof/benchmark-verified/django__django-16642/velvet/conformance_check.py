#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16642 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection.
              The impl region of `resolveMediaType` is pure R/I (no A-tagged
              callee appears in the computed `out`): it is the override-table
              lookup `compressionMediaType(encoding)`, falling back to the
              guessed media type, then to `application/octet-stream`.
  * ORACLE  — `patch.diff`'s behaviour: a real `FileResponse` built over a file
              whose name is the fuzzed input, read back through the public
              `Content-Type` header (the exact value the F2P test observes). The
              harness applies patch.diff before this runs.

The two modeled inputs `(guessed, encoding)` are produced by the UNCHANGED
upstream type-sniffer `mimetypes.guess_type(name)` (mapping.md §3) — shared,
untouched, by both legs; the gate drives it via fuzzed file names so the
override table is exercised on every recognised label and on names that miss it.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import io
import mimetypes
import random
import sys

SEED = 16642
N_FUZZ = 100_000


def _configure_django():
    """`FileResponse` reads `settings.DEFAULT_CHARSET` in its base `__init__`, so
    a minimal settings module must be configured before any response is built.
    This is orthogonal to the modeled behaviour (the Content-Type resolution) —
    it only makes the real callee runnable in a bare interpreter."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEFAULT_CHARSET="utf-8")


# --- the R/I shadow: Solution.lean compressionMediaType / resolvedMediaType --
# compressionMediaType (encoding : Option String) : Option String
#   -- the dedicated media type for a recognised compression label, else none.
_COMPRESSION = {
    "br": "application/x-brotli",
    "bzip2": "application/x-bzip",
    "compress": "application/x-compress",
    "gzip": "application/gzip",
    "xz": "application/x-xz",
}


def shadow_resolve(guessed, encoding):
    """resolvedMediaType (guessed encoding : Option String) : String,
    transliterated. `None` is the Lean `none`; `Option.orElse` is the
    short-circuit `a if a is not None else b`; `.getD d` is `x or d` on the
    present/absent split."""
    chosen = _COMPRESSION.get(encoding)            # compressionMediaType encoding
    if chosen is None:                             # .orElse (fun _ => guessed)
        chosen = guessed
    if chosen is None:                             # .getD "application/octet-stream"
        chosen = "application/octet-stream"
    return chosen


def oracle_resolve(name):
    """patch.diff's behaviour: the Content-Type a real FileResponse announces for
    a payload whose file name is `name`. This is exactly the value the F2P
    `test_compressed_response` reads (`response.headers['Content-Type']`)."""
    from django.http import FileResponse
    f = io.BytesIO(b"payload")
    f.name = name
    resp = FileResponse(f)
    try:
        return resp.headers["Content-Type"]
    finally:
        resp.close()


def _bridge_inputs(name):
    """The mapping.md §3 bridge: the two modeled inputs (guessed, encoding) are
    the unchanged `mimetypes.guess_type(name)` outputs."""
    return mimetypes.guess_type(name)


def fuzz_names(n, rng):
    # Boundary cases first (plan §4.1 step 4): every recognised compression
    # label (the two NEW ones — br, compress — and the three classic ones),
    # both with a guessable wrapped type and with an unguessable one, plus
    # names with no compression label and names with no guessable type at all.
    yield "archive.tar.br"        # guessed application/x-tar, encoding br
    yield "page.html.br"          # guessed text/html,         encoding br
    yield "blob.br"               # guessed None,              encoding br
    yield "archive.tar.Z"         # guessed application/x-tar, encoding compress
    yield "page.html.Z"           # guessed text/html,         encoding compress
    yield "blob.Z"                # guessed None,              encoding compress
    yield "archive.tar.gz"
    yield "page.html.gz"
    yield "archive.tar.bz2"
    yield "archive.tar.xz"
    yield "report.txt"            # guessed text/plain,        encoding None
    yield "page.html"             # guessed text/html,         encoding None
    yield "noextension"           # guessed None,              encoding None
    yield ""                      # empty name
    yield ".br"
    yield ".Z"
    yield "a.unknownext"
    stems = ["archive", "page", "report", "data", "image", "blob", "x", "a.b.c"]
    base_exts = ["", ".tar", ".html", ".txt", ".json", ".csv", ".pdf", ".xml",
                 ".unknown", ".doc"]
    enc_exts = ["", ".br", ".Z", ".gz", ".bz2", ".xz", ".tgz", ".zip", ".rar"]
    for _ in range(n):
        stem = rng.choice(stems)
        be = rng.choice(base_exts)
        ee = rng.choice(enc_exts)
        yield stem + be + ee


def main():
    _configure_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for name in fuzz_names(N_FUZZ, rng):
        count += 1
        guessed, encoding = _bridge_inputs(name)
        shadow = shadow_resolve(guessed, encoding)
        oracle = oracle_resolve(name)
        if shadow != oracle:
            disagreements.append((name, (guessed, encoding), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, gge, sh, orc in disagreements:
            print("  name=%r guess/enc=%r shadow=%r oracle=%r"
                  % (name, gge, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveMediaType agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
