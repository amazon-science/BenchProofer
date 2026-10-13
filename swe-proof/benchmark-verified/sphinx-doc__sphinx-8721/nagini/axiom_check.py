#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8721.

This bundle consumes NO axioms. The name decision in the suppression predicate
is modelled DEEPLY in model.py and is validated here, out of band, against the
REAL Python builtin it stands for:

  (A-reference) the deep model `prefix_eq(s, lit)` (model.py pure region) ==
      the real `str.startswith(lit)`, i.e. the begins-with test used to gate
      electronic-book targets.

  (composite) the suppression predicate `suppressed(name, enable_epub)` ==
      the real gate the patch installs for electronic-book output:
        name.startswith("epub") and not enable_epub

Imports nothing repo-specific: `str.startswith` is a builtin — the exact
operation the gold patch calls at the electronic-book gate. Exit 0 iff every
observation matches the model.
"""
import random
import sys

# --- model.py reference encodings (kept in lock-step with the pure region) ---

LIT_EPUB = [101, 112, 117, 98]  # 'epub'


def prefix_eq(s, lit):
    """Reference of model.py's deep model `prefix_eq` over code-point lists."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s[1:], lit[1:])


def suppressed_model(name, enable_epub):
    """Reference of model.py's `suppressed` composite predicate."""
    cps = [ord(c) for c in name]
    return prefix_eq(cps, LIT_EPUB) and not enable_epub


def suppressed_real(name, enable_epub):
    """The electronic-book gate the gold patch installs in collect_pages."""
    if name.startswith("epub") and not enable_epub:
        return True
    return False


# --- the checks --------------------------------------------------------------

def check_prefix_eq(name, lit_str, lit_cps):
    observed = name.startswith(lit_str)                # real str.startswith
    expected = prefix_eq([ord(c) for c in name], lit_cps)  # deep model
    assert observed == expected, (
        "prefix_eq deep model unsound on %r startswith %r: real gave %r, "
        "deep model %r" % (name, lit_str, observed, expected))


def check_suppressed(name, enable_epub):
    observed = suppressed_real(name, enable_epub)
    expected = suppressed_model(name, enable_epub)
    assert observed == expected, (
        "suppression predicate unsound on name=%r enable_epub=%r: real gate "
        "gave %r, model gives %r" % (name, enable_epub, observed, expected))


def main():
    # builder names exercised by the SWE-bench tests + neighbours that pin the
    # exact gate boundary (the prefix test must accept epub3 but reject near
    # mistakes such as 'ep' / 'Epub' / 'pub').
    boundary = [
        "", "html", "singlehtml", "singlehtm", "singlehtmlx", "ssinglehtml",
        "epub", "epub2", "epub3", "epubfoo", "ep", "e", "Epub", "EPUB",
        "epu", "pub", "dirhtml", "json", "latex", "text", "man", "texinfo",
        "applehelp", "qthelp", "devhelp", "htmlhelp", "linkcheck", "xml",
        "pseudoxml", "gettext", "changes", "singlehtmlepub", "epubsinglehtml",
    ]
    for name in boundary:
        for enable in (True, False):
            check_prefix_eq(name, "epub", LIT_EPUB)
            check_suppressed(name, enable)

    # randomized fuzz over an alphabet that keeps the boundary near 'epub'
    # interesting (so the model and the builtin are exercised on near-prefixes,
    # not just random noise).
    rng = random.Random(8721)
    alphabet = list("epubsinglhtmxz123 ")
    for _ in range(50000):
        n = rng.randint(0, 14)
        name = "".join(rng.choice(alphabet) for _ in range(n))
        enable = rng.choice((True, False))
        check_prefix_eq(name, "epub", LIT_EPUB)
        check_suppressed(name, enable)

    print("G-AX OK: prefix_eq (== str.startswith) deep model and the "
          "electronic-book suppression predicate sound on %d boundary + 50000 "
          "fuzz builder names." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
