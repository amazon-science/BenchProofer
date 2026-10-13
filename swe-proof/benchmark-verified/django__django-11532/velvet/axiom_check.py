#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11532.

Executes the REAL library callee modeled by the `aceEncode` axiom — the IDNA
ASCII-Compatible-Encoding idiom `domain.encode('idna').decode('ascii')` (the body
of the new `punycode` helper the patch introduces; identical to the four
pre-existing inline sites) — on boundary and randomized inputs, and asserts that
every observation satisfies the axiom's post-condition `aceEncode_ascii`:

    (A-consumed) for every domain `d`, every code point of aceEncode(d) is ASCII
                 (ordinal < 128).

This is the WEAKEST property the modeled fix relies on (mapping.md §3): the
normalized host is safe to embed in a header rendered with a single-byte charset.
We deliberately do NOT assert the exact ACE output value (that would over-claim
the codec, directive 7); only the ASCII guarantee is load-bearing.

The codec raises `UnicodeError` on some malformed inputs (empty / over-long
labels). The axiom does NOT claim totality: `get_fqdn` is only reached with a real
OS host name, and `aceEncode_ascii` constrains only the values the codec actually
produces. So inputs on which the real codec raises are out of scope — we record
the raise rate for transparency and assert the post-condition on every successful
result.

Imports only the Python standard library (the `idna` codec is built in). Exit 0
iff every successful observation meets the axiom.
"""
import random
import sys


def ace_encode(domain):
    """The REAL callee the patch's `punycode` helper wraps:
    domain.encode('idna').decode('ascii')  (IDNA / RFC-3490 ToASCII)."""
    return domain.encode('idna').decode('ascii')


def check_ascii_postcondition(domain):
    """Assert aceEncode_ascii: every code point of the real codec's output is
    ASCII (< 128). Returns True if the codec produced a value (checked), False if
    it raised (out of axiom scope)."""
    try:
        out = ace_encode(domain)
    except UnicodeError:
        return False  # malformed label: codec raises; axiom makes no claim
    for ch in out:
        assert ord(ch) < 128, (
            "aceEncode_ascii unsound on %r: output %r contains non-ASCII "
            "code point %r (ord %d)" % (domain, out, ch, ord(ch)))
    return True


def main():
    checked = 0
    raised = 0

    # --- boundary cases ----------------------------------------------------
    boundary = [
        "example.com", "google.com", "EXAMPLE.com", "localhost",
        "a", "a.b.c", "sub.domain.example.org",
        "漢字",                # 漢字  -> the F2P host (-> xn--p8s937b)
        "正宗",                # 正宗  (the issue's reporter hostname)
        "sub.漢字.com",        # non-ASCII label among ASCII labels
        "école.example",          # latin-1 accented label
        "über.example.com",
        "xn--p8s937b",                 # already-ACE input must stay ASCII
        "münchen.de",
        "рф",                # Cyrillic
        "αβ.gr",             # Greek
    ]
    for d in boundary:
        if check_ascii_postcondition(d):
            checked += 1
        else:
            raised += 1

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(11532)
    # alphabet biased toward valid DNS-ish labels plus non-ASCII scripts
    ascii_label = "abcdefghijklmnopqrstuvwxyz0123456789-"
    nonascii = "漢字正宗éüñрфαβ"
    pool = ascii_label + nonascii
    for _ in range(20000):
        nlabels = rng.randint(1, 3)
        labels = []
        for _ in range(nlabels):
            k = rng.randint(1, 8)
            labels.append("".join(rng.choice(pool) for _ in range(k)))
        domain = ".".join(labels)
        if check_ascii_postcondition(domain):
            checked += 1
        else:
            raised += 1

    print("G-AX OK: aceEncode_ascii (IDNA ACE codec output is ASCII) holds on "
          "all %d successful observations (%d boundary + fuzz); %d malformed "
          "inputs raised UnicodeError (out of axiom scope, codec not claimed "
          "total)." % (checked, len(boundary), raised))
    assert checked > 0, "no successful codec observations — check is vacuous"
    return 0


if __name__ == "__main__":
    sys.exit(main())
