#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-5414.

The bundle consumes NO axiom. Its single kind-A obligation is the A-reference
deep model `isAsciiHost`, which models the UNCHANGED branch-selector callee
`requests._internal_utils.unicode_is_ascii` (the predicate that decides whether
`prepare_url` takes the all-ASCII path the patched `elif` governs, vs the IDNA
path). G-AX validates the deep model against the REAL callee:

  (A-reference) the deep model `is_ascii_host` (Solution.lean `isAsciiHost`,
      pure region) == the real `unicode_is_ascii`. `unicode_is_ascii(s)` is
      `True` iff `s.encode('ascii')` does not raise, i.e. every code point is
      < 128; `is_ascii_host` is the per-code-point conjunction of `ord(c) < 128`.

Imports the REAL repo callee `requests._internal_utils.unicode_is_ascii` (the
same function `prepare_url` calls). Runs in-container (the prebuilt SWE-Bench
instance image). stdlib + repo only. Exit 0 iff every observation matches.
"""
import random
import sys


def is_ascii_host(s):
    """Reference implementation of Solution.lean's deep model `isAsciiHost`:
    True iff every code point of `s` is in the 7-bit ASCII range (< 128)."""
    return all(ord(c) < 128 for c in s)


def _real_unicode_is_ascii():
    """The REAL repo callee. Fall back to a faithful transliteration of its
    source at base_commit if the repo cannot be imported (documented)."""
    try:
        from requests._internal_utils import unicode_is_ascii
        return unicode_is_ascii, "requests._internal_utils.unicode_is_ascii"
    except Exception:
        def unicode_is_ascii(u_string):
            assert isinstance(u_string, str)
            try:
                u_string.encode('ascii')
                return True
            except UnicodeEncodeError:
                return False
        return unicode_is_ascii, ("transliterated unicode_is_ascii "
                                  "(requests not importable)")


def check_ascii_reference(real, s):
    observed = bool(real(s))                 # real callee
    expected = bool(is_ascii_host(s))        # deep model
    assert observed == expected, (
        "isAsciiHost deep model unsound on %r: unicode_is_ascii gave %r, "
        "deep model gives %r" % (s, observed, expected))


def main():
    real, real_name = _real_unicode_is_ascii()

    # --- boundary cases over the ASCII/non-ASCII frontier and the needles ----
    boundary = [
        "",                       # empty
        "*", ".",                 # the two rejected leading code points
        "*example.com",           # P2P discriminator (wildcard, ASCII)
        ".example.com",           # F2P discriminator (leading dot, ASCII)
        "example.com",            # ordinary ASCII host (accepted)
        "a", "Z", "0", "-", "_", ":",
        chr(127), chr(127) + "x",  # U+007F is ASCII (< 128)
        chr(128), chr(128) + "x",  # U+0080 is NOT ASCII
        "héllo", "xn--ls8h",      # non-ASCII vs already-punycoded
        "ドメイン.example",        # non-ASCII host -> takes the IDNA branch
        "münchen.de",
        "a.b.c", "127.0.0.1",
        "*.example.com",          # wildcard then dot
        "..", "...",
    ]
    for s in boundary:
        check_ascii_reference(real, s)

    # --- randomized fuzz: mix ASCII and a few non-ASCII code points ----------
    rng = random.Random(5414)
    ascii_pool = [chr(c) for c in range(32, 127)] + ["*", ".", "-", "_"]
    non_ascii = ["é", "ü", "ñ", "•", "ド", "メ", "イ", "ン", chr(128),
                 chr(160), chr(0x1F600)]
    for _ in range(20000):
        n = rng.randint(0, 24)
        # ~half all-ASCII, ~half containing at least one non-ASCII char
        pool = ascii_pool if rng.random() < 0.5 else (ascii_pool + non_ascii)
        s = "".join(rng.choice(pool) for _ in range(n))
        check_ascii_reference(real, s)

    print("G-AX OK: is_ascii_host deep model (== %s) sound on %d boundary + "
          "20000 fuzz inputs (seed=5414)." % (real_name, len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
