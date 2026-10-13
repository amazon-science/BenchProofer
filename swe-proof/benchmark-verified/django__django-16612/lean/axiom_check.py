#!/usr/bin/env python3
"""G-AX for django__django-16612.

The bundle declares two opaque leaf callees (mapping.md / refinement.md):

    escapePathComponent : String -> String   <->  escape_uri_path
    encodeQueryString   : String -> String   <->  iri_to_uri

These are A-REFERENCE leaves: the proof consumes NO `_prop` axiom about either
(they appear identically in the spec and the impl, so correct_* holds for any
total functions). The ONLY property asserted by the `opaque <callee> : String ->
String` declarations is that each real callee is a TOTAL, DETERMINISTIC function
from a string to a string. This check runs the REAL callees on boundary + fuzzed
inputs and confirms exactly that: each returns a `str` (no exception) and is
deterministic (same input -> same output across repeated calls). Exit 0 iff
sound. stdlib-only. Pinned seed: 16612.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(DEBUG=False, DATABASES={}, INSTALLED_APPS=[])
    django.setup()

from django.utils.encoding import escape_uri_path, iri_to_uri

CALLEES = [("escape_uri_path", escape_uri_path), ("iri_to_uri", iri_to_uri)]

BOUNDARY = [
    "", "/", "//", "a", "/admin/auth/foo", "/admin/auth/foo/",
    "id=1", "a=1&b=2", "q=hello world", "café", "üñ", "x%y", "p#q",
    "a b c", "~tilde", "plus+plus", "key=val/ue", "\t", "\n", " ",
    "%41%42", "?already?", "100%", "&&&", "===", "a" * 1000,
]


def fuzz_str(rng: random.Random) -> str:
    n = rng.randint(0, 30)
    chars = []
    for _ in range(n):
        r = rng.random()
        if r < 0.5:
            chars.append(rng.choice("abcdefghij0123456789/?&=#%+ "))
        elif r < 0.8:
            chars.append(chr(rng.randint(0x20, 0x7E)))
        else:
            chars.append(chr(rng.randint(0xA0, 0x2FF)))   # latin / unicode
    return "".join(chars)


def main() -> int:
    rng = random.Random(16612)
    inputs = list(BOUNDARY) + [fuzz_str(rng) for _ in range(5000)]
    for name, fn in CALLEES:
        for s in inputs:
            try:
                out = fn(s)
            except Exception as e:  # noqa: BLE001
                print(f"G-AX FAIL: {name}({s!r}) raised {e!r}; "
                      f"opaque leaf must be a total String->String function")
                return 1
            if not isinstance(out, str):
                print(f"G-AX FAIL: {name}({s!r}) returned non-str {type(out)}")
                return 1
            out2 = fn(s)
            if out2 != out:
                print(f"G-AX FAIL: {name}({s!r}) nondeterministic: "
                      f"{out!r} != {out2!r}")
                return 1
    print(f"G-AX OK: both opaque leaves (escape_uri_path, iri_to_uri) are total "
          f"deterministic String->String functions over "
          f"{len(inputs)} inputs each.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
