#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10614.

The bundle has NO consumed axioms. The single non-trivial library call on the
changed path — the external-reference key recovery `refuri.rsplit('#', 1)[-1]`
— is modeled DEEPLY by `afterLastHash` in Solution.lean's pure region (an
A-reference). G-AX validates that deep model against the REAL Python operation:

  (A-reference)  afterLastHash(s) == s.rsplit('#', 1)[-1]

  where afterLastHash(s) = the maximal '#'-free suffix of s (everything after
  the last '#', or all of s when there is no '#'). Modeled in Lean as
  `(s.reverse.takeWhile (· ≠ '#')).reverse`; here the reference encoding takes
  the suffix after the last '#'.

Imports nothing repo-specific: `str.rsplit` is a Python builtin — the exact
operation the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys


def after_last_hash_model(s):
    """Reference encoding of Solution.lean's deep model `afterLastHash`:
    take chars from the end until a '#', then restore order = the maximal
    '#'-free suffix of s."""
    tail = []
    for ch in reversed(s):
        if ch == '#':
            break
        tail.append(ch)
    return "".join(reversed(tail))


def check_rsplit_reference(s):
    """Assert the deep model afterLastHash(s) == the REAL rsplit('#',1)[-1]."""
    observed = s.rsplit('#', 1)[-1]        # real Python builtin
    expected = after_last_hash_model(s)    # deep model
    assert observed == expected, (
        "afterLastHash deep model unsound on %r: rsplit gave %r, deep model "
        "gives %r" % (s, observed, expected))


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        "",                       # empty
        "#",                      # lone delimiter -> ""
        "##",                     # multiple delimiters, empty tail
        "abc",                    # no '#': whole string
        "#abc",                   # leading '#'
        "abc#",                   # trailing '#': empty tail
        "a#b",                    # single split
        "a#b#c",                  # multiple '#': only last matters
        "foo.html#subdir.other.Bob",   # the F2P-shaped intersphinx target
        "https://example.org/foo.html#subdir.other.Bob",
        "../my_class_1.html#my_package.MyClass1",
        "x#y#z#w",
        "no_anchor.html",
        "#leadingonly",
        "trailing#",
        "::weird::#name",
    ]
    for s in boundary:
        check_rsplit_reference(s)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(10614)
    alphabet = list("abc.#/:_ABCxyz0129") + ["é", "•"]
    for _ in range(20000):
        n = rng.randint(0, 30)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_rsplit_reference(s)

    print("G-AX OK: afterLastHash deep model (== str.rsplit('#',1)[-1]) sound "
          "on %d boundary + 20000 fuzz inputs. No consumed axioms."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
