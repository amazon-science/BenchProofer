#!/usr/bin/env python3
r"""G-CONF — differential test of the R/I shadow of implementation_contentType
against the patch.diff behaviour (the post-patch content-type selection inside
FileResponse.set_headers).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The
shadow reproduces the impl op-for-op: start from the guessed content type; if the
encoding is a recognized compression scheme, replace it with that scheme's
dedicated media type (post-patch key set {br, bzip2, compress, gzip, xz}); then
apply the `or "application/octet-stream"` fallback.

We diff that against an INDEPENDENT oracle that mirrors the exact post-patch
Python statements (the dict `.get(encoding, content_type)` followed by
`content_type or "application/octet-stream"`), expressed with Python's own dict
and truthiness rather than the if-chain the shadow uses. Inputs range over
realistic guessed (content_type, encoding) pairs the boundary callee
`mimetypes.guess_type` can yield, including None / "" types and every
encodings_map value plus None / unrecognized encodings.

Zero disagreements required over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16642          # pinned in mapping.md
N = 120_000           # >= 10^5

# Guessed content types mimetypes.guess_type can return, plus the falsy values
# (None, "") that exercise the `or` fallback.
CONTENT_TYPES = [
    None, "", "text/html", "text/plain", "application/x-tar",
    "application/octet-stream", "application/gzip", "image/png",
    "application/json", "application/x-brotli",
]
# Every value in mimetypes.encodings_map, plus None and some unrecognized
# encodings (which must keep the guessed type).
ENCODINGS = [
    None, "gzip", "compress", "bzip2", "xz", "br",
    "deflate", "identity", "", "BR", "Compress",
]


def shadow(content_type, encoding):
    """R/I shadow of implementation_contentType (op-for-op, if-chain form)."""
    ct = content_type
    if encoding is not None:
        if encoding == "br":
            ct = "application/x-brotli"
        elif encoding == "bzip2":
            ct = "application/x-bzip"
        elif encoding == "compress":
            ct = "application/x-compress"
        elif encoding == "gzip":
            ct = "application/gzip"
        elif encoding == "xz":
            ct = "application/x-xz"
    # `or "application/octet-stream"`: None and "" are falsy.
    if ct is None or ct == "":
        return "application/octet-stream"
    return ct


def oracle(content_type, encoding):
    """Independent post-patch behaviour: the exact patched Python statements."""
    content_type = {
        "br": "application/x-brotli",
        "bzip2": "application/x-bzip",
        "compress": "application/x-compress",
        "gzip": "application/gzip",
        "xz": "application/x-xz",
    }.get(encoding, content_type)
    return content_type or "application/octet-stream"


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first, incl. the exact F2P shapes.
    fixed = [
        ("text/html", "br"), ("application/x-tar", "br"),
        ("text/html", "compress"), ("application/x-tar", "compress"),
        ("application/x-tar", "gzip"), ("application/x-tar", "bzip2"),
        ("application/x-tar", "xz"), (None, "gzip"),
        ("text/plain", None), (None, None), ("", None), ("", "br"),
        ("text/html", "deflate"), ("text/html", ""), ("text/html", "BR"),
    ]
    cases = fixed + [
        (rng.choice(CONTENT_TYPES), rng.choice(ENCODINGS))
        for _ in range(N)
    ]

    for ct, enc in cases:
        got = shadow(ct, enc)
        want = oracle(ct, enc)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((ct, enc, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for ct, enc, g, w in examples:
            print(f"  ct={ct!r} enc={enc!r} shadow={g!r} oracle={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
