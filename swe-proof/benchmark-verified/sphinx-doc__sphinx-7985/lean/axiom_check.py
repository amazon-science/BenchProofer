#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-7985.

No callee is consumed as a proof axiom. The one deep-model reference is
`hasUriScheme`, the Lean model of the patched scheme test
`uri_re = re.compile('[a-z]+://'); uri_re.match(uri)`. This script validates the
A-reference: the Lean model must agree with the REAL regex on boundary + fuzzed
inputs. stdlib-only; exit 0 iff every observation agrees.
"""
import random
import re
import string
import sys

URI_RE = re.compile('[a-z]+://')  # byte-identical to the patched module constant


def real(uri: str) -> bool:
    # re.match is anchored at the start of the string.
    return URI_RE.match(uri) is not None


def model(uri: str) -> bool:
    # Lean `hasUriScheme`: maximal lowercase run is non-empty AND the remainder
    # begins with "://".
    i = 0
    while i < len(uri) and 'a' <= uri[i] <= 'z':
        i += 1
    return i > 0 and uri[i:].startswith('://')


def check(uri: str) -> None:
    if real(uri) != model(uri):
        print(f"MISMATCH uri={uri!r}: real={real(uri)} model={model(uri)}")
        sys.exit(1)


def main() -> None:
    boundary = [
        "", "://", "a://", "ab://", "z://", "ftp://x", "http://a", "https://a",
        "mailto:x", "conf.py", "path/to/notfound", "a:/", "a:", "abc:/",
        "A://", "1://", "a-b://", "aBc://", "a://b://", " a://", "a ://",
        "ftp:", "#frag", "a", "://a", "aaa://aaa",
    ]
    for u in boundary:
        check(u)

    rng = random.Random(20240630)
    alphabet = string.ascii_letters + string.digits + ":/.#-_ "
    for _ in range(200_000):
        n = rng.randint(0, 12)
        u = "".join(rng.choice(alphabet) for _ in range(n))
        check(u)
        # bias toward scheme-like prefixes
        pre = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(0, 4)))
        check(pre + rng.choice(["", ":", "/", "://", ":/", "//"]) + u)

    print("G-AX OK: hasUriScheme model == re.compile('[a-z]+://').match over all probes")
    sys.exit(0)


if __name__ == "__main__":
    main()
