#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-2317.

Executes the REAL repo callee `requests.utils.to_native_string` (the very
callee the gold patch introduces) and asserts that the deep model `nativeSeq`
(Solution.lean pure region) agrees with it on every spec-domain input, in both
the native-text and the byte-string token form.

The single kind-A check:

  (A-reference) the deep model `nativeSeq` (Solution.lean pure region) == the
      real `to_native_string`. The changed coercion is modeled DEEPLY, not
      behind a consumed axiom; G-AX validates that deep model against the real
      callee. `nativeSeq` is the identity on the carried character sequence:
      a native str token is returned unchanged, a bytes token is ASCII-decoded;
      for an ASCII token both are the identity on the carried code points.

Imports requests' own `to_native_string` via PYTHONPATH=/testbed so the patched
repo copy is used (per LESSONS: non-editable repos otherwise import the
unpatched site-packages copy), plus stdlib. Exit 0 iff every obligation holds.
"""
import random
import sys

# The spec domain: ASCII method tokens (every code point < 128). For an ASCII
# token a byte value equals the code point of its ASCII decoding.
ASCII = [chr(c) for c in range(128)]


def native_seq(token_chars):
    """Reference implementation of Solution.lean's deep model `nativeSeq`:
    the identity copy of the carried character sequence (nativeChar c = [c])."""
    out = []
    for c in token_chars:
        out.extend([c])
    return out


def check_reference(s):
    """Assert nativeSeq(s) == real to_native_string(s) for both the text and
    byte forms of the ASCII token s."""
    from requests.utils import to_native_string
    expected = native_seq(list(s))                       # deep model

    # text form: native str token, returned unchanged
    observed_text = list(to_native_string(s))            # real callee
    assert observed_text == expected, (
        "nativeSeq deep model unsound on text %r: to_native_string gave %r, "
        "deep model gives %r" % (s, observed_text, expected))

    # byte form: ASCII byte string, decoded
    b = s.encode("ascii")
    observed_bytes = list(to_native_string(b))           # real callee
    assert observed_bytes == expected, (
        "nativeSeq deep model unsound on bytes %r: to_native_string gave %r, "
        "deep model gives %r" % (b, observed_bytes, expected))


def main():
    # --- boundary cases: HTTP method tokens + the empty token --------------
    boundary = ["", "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS",
                "PATCH", "TRACE", "CONNECT", "a", "Z", "0", " "]
    for s in boundary:
        check_reference(s)

    # --- exhaustive single-value sweep of the whole ASCII spec domain ------
    for c in ASCII:
        check_reference(c)

    # --- randomized fuzz over the same ASCII alphabet ----------------------
    rng = random.Random(2317)
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(ASCII) for _ in range(n))
        check_reference(s)

    print("G-AX OK: nativeSeq deep model (== to_native_string) sound on %d "
          "boundary + 128 single-char + 20000 fuzz tokens, each in {text,bytes}"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
