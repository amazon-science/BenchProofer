#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7985.

The only callee whose behaviour `Solution.lean` depends on is the access-method
detector the patch adds: `uri_re.match(uri)` with `uri_re = re.compile('[a-z]+://')`.
It is modeled DEEPLY by `hasUriScheme` (an A-reference, NOT a consumed axiom).
This check runs the REAL callee over boundary inputs plus randomized fuzz and
asserts:

  (A-reference)  bool(uri_re.match(uri))  ==  hasUriScheme(uri)

where `hasUriScheme` (model.py deep model) is: the front maximal run of ASCII
lowercase letters is non-empty AND is immediately followed by the literal "://".

The two other callees the modeled arm touches — `path.exists(...)` and the
`self.to_ignore` match loop — are UNCHANGED and enter the model only as boolean
inputs (`fileExists`, `anyIgnore`); their results are method inputs, so there is
nothing to axiomatize and nothing for this check to validate about them.

Imports only `re` (Python standard library) — the same module the gold patch's
`re.compile('[a-z]+://')` resolves to. Exit 0 iff every obligation holds.
"""
import random
import re
import sys

# The REAL callee, byte-for-byte as the gold patch constructs it
# (sphinx/builders/linkcheck.py: `uri_re = re.compile('[a-z]+://')`).
URI_RE = re.compile('[a-z]+://')


def real_match(uri):
    """bool(uri_re.match(uri)) — the REAL access-method detector."""
    return bool(URI_RE.match(uri))


def has_uri_scheme(uri):
    """Reference encoding of model.py's deep model `hasUriScheme`:
    the front maximal run of ASCII lowercase letters is non-empty and is
    immediately followed by '://'."""
    k = 0
    for ch in uri:
        if 'a' <= ch <= 'z':
            k += 1
        else:
            break
    return k >= 1 and uri[k:k + 3] == '://'


def check(uri):
    observed = real_match(uri)          # REAL callee
    expected = has_uri_scheme(uri)      # deep model (A-reference)
    assert observed == expected, (
        "hasUriScheme deep model unsound on %r: real uri_re.match -> %r, "
        "deep model -> %r" % (uri, observed, expected))


def main():
    # --- boundary cases over the scheme grammar and its edges --------------
    boundary = [
        "",                       # empty
        "://", ":/", ":",         # separator without a scheme run
        "a://", "a://b",          # minimal scheme
        "ftp://x", "ftps://x",    # real unsupported schemes (the issue's example)
        "http://x", "https://x",  # web schemes (also match the [a-z]+:// grammar)
        "mailto://x",
        "ABC://x", "FTP://x",     # uppercase run -> no lowercase prefix -> no match
        "a1b://x", "x1://y",      # digit breaks the lowercase run before '://'
        "f-tp://x", "f_tp://x",   # punctuation breaks the run
        "ftp:/x", "ftp:x", "ftp/x",  # incomplete separator
        "conf.py", "path/to/notfound", "doesntexist",  # genuine local files
        "a/b://c",                # '/' breaks the run before the real '://'
        "  a://x",                # leading space -> run is empty at pos 0
        "a ://x",                 # space breaks the run
        "#frag", "mailto:a@b",    # the skip-without-resolution forms
        "z://", "zzzzz://tail",
    ]
    for uri in boundary:
        check(uri)

    # --- randomized fuzz over an alphabet that exercises the grammar -------
    rng = random.Random(7985)
    alphabet = list("abcxyz") + list("ABCZ") + list("0139") + \
        [":", "/", ".", "-", "_", " ", "#", "@"]
    for _ in range(20000):
        n = rng.randint(0, 16)
        uri = "".join(rng.choice(alphabet) for _ in range(n))
        check(uri)

    # focused fuzz: scheme-run + separator-ish tail (stresses the boundary)
    for _ in range(20000):
        run = "".join(rng.choice(list("abcz")) for _ in range(rng.randint(0, 5)))
        sep = "".join(rng.choice([":", "/"]) for _ in range(rng.randint(0, 4)))
        tail = "".join(rng.choice(list("ab/.")) for _ in range(rng.randint(0, 4)))
        check(run + sep + tail)

    print("G-AX OK: hasUriScheme deep model (== re.compile('[a-z]+://').match) "
          "sound on %d boundary + 40000 fuzz inputs." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
