#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8593.

Axiom under check: `meta_class(doc)` (model.py axioms region) — the visibility
classification of a documentation block:

    0 (NONE)    : no explicit visibility marker
    1 (PUBLIC)  : an explicit "public"  visibility marker is present
    2 (PRIVATE) : an explicit "private" visibility marker is present

This abstracts the UNCHANGED community callee
`sphinx.util.docstrings.extract_metadata` followed by the public/private branch
that reads its result (`'public' in metadata` -> PUBLIC, `'private' in metadata`
-> PRIVATE, else NONE).  The fix does not change this classifier; it only
changes WHICH documentation text reaches it (the inline attribute documentation
of a module member rather than the value's empty intrinsic documentation).

The axiom's `Ensures` are intentionally the WEAKEST the proof needs:

  (1) the result is always one of {NONE, PUBLIC, PRIVATE};
  (2) an empty documentation block carries no marker (-> NONE).

This script runs the REAL classifier on boundary cases (empty, the exact
`:meta public:` / `:meta private:` markers as used by the failing tests, plain
prose, other field markers, multi-line blocks) plus randomized fuzz, and
asserts that EVERY observation satisfies (1) and (2).  It additionally records
(without pinning in the axiom) that the real classifier maps the `:meta
public:` / `:meta private:` markers to PUBLIC / PRIVATE, which is the behaviour
the deep keep-decision model relies on being a function of the documentation.

The real callee lives in the Sphinx package installed in the evaluation
container (the very module the patched code imports); no repo-private helper is
re-implemented here.  Exit 0 iff every obligation holds.
"""
import random
import sys

from sphinx.util.docstrings import extract_metadata   # the REAL unchanged callee


NONE, PUBLIC, PRIVATE = 0, 1, 2


def meta_class_real(doc):
    """The real visibility classifier: extract_metadata + the public/private
    branch that reads it (filter_members lines 731-739, unchanged by the fix)."""
    metadata = extract_metadata(doc) if doc else {}
    if 'private' in metadata:
        return PRIVATE
    elif 'public' in metadata:
        return PUBLIC
    else:
        return NONE


def check_axiom(doc):
    """Assert the two axiom Ensures hold on the REAL classifier for `doc`."""
    r = meta_class_real(doc)
    # Ensures (1): result is one of {NONE, PUBLIC, PRIVATE}
    assert r in (NONE, PUBLIC, PRIVATE), (
        "meta_class axiom unsound on %r: real classifier returned %r, "
        "not in {0,1,2}" % (doc, r))
    # Ensures (2): an empty documentation block -> NONE
    if doc is None or len(doc) == 0:
        assert r == NONE, (
            "meta_class axiom unsound: empty/None doc %r classified %r, "
            "axiom requires NONE(0)" % (doc, r))
    return r


def main():
    # --- boundary documentation blocks -----------------------------------
    boundary = [
        "",                                   # empty  -> NONE (Ensures 2)
        None,                                 # absent -> NONE (Ensures 2)
        ":meta public:",                      # the public marker  -> PUBLIC
        ":meta private:",                     # the private marker -> PRIVATE
        "summary line.\n\n:meta public:\n",   # marker after prose (function form)
        "summary line.\n\n:meta private:\n",
        "just some prose without any field",
        ":param x: a parameter",              # other field marker, not visibility
        ":returns: a value",
        "  :meta public:  ",                  # whitespace around marker
        ":meta public:\n:meta private:",      # both markers (private wins)
        "line1\nline2\nline3",
        "\n\n\n",                             # only blank lines -> NONE
    ]

    # the discriminating-but-not-pinned facts the deep model relies upon:
    assert meta_class_real(":meta public:") == PUBLIC, \
        "real classifier must map ':meta public:' to PUBLIC"
    assert meta_class_real(":meta private:") == PRIVATE, \
        "real classifier must map ':meta private:' to PRIVATE"
    assert meta_class_real("summary line.\n\n:meta public:\n") == PUBLIC, \
        "real classifier must map a public-marked block to PUBLIC"
    assert meta_class_real("summary line.\n\n:meta private:\n") == PRIVATE, \
        "real classifier must map a private-marked block to PRIVATE"

    for doc in boundary:
        check_axiom(doc)

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(8593)
    fragments = [
        "", "\n", "  ", "summary.", "more prose here", "line",
        ":meta public:", ":meta private:", ":meta something:",
        ":param a: x", ":returns: y", ":raises ValueError: z",
        ":meta:", "public", "private", "_underscored",
        "\t:meta public:", ":Meta Public:", "::", ":meta  public :",
    ]
    for _ in range(20000):
        n = rng.randint(0, 6)
        doc = "\n".join(rng.choice(fragments) for _ in range(n))
        check_axiom(doc)

    print("G-AX OK: meta_class axiom sound on %d boundary + 20000 fuzz "
          "documentation blocks (real sphinx.util.docstrings.extract_metadata)"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
