#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14089.

Validates the one kind-A obligation: the deep model `revSeq` (Solution.lean's
`pure` region) == the REAL callee the new method delegates to, the CPython
builtin `reversed` over the collection's backing dict.

The new `OrderedSet.__reversed__` returns `reversed(self.dict)`, where
`self.dict = dict.fromkeys(iterable or ())` preserves insertion order with
distinct keys and `__iter__` yields `iter(self.dict)`. So the backward
enumeration is exactly the element-wise reversal of the forward enumeration.
This is an **A-reference**: the changed op is modeled DEEPLY (the spelled-out
reversal `revSeq`), not behind a consumed axiom; G-AX validates the deep model
against the real callee. We assert, on every input:

  (1) value:     list(reversed(d)) == revSeq(list(d))           [== list(d)[::-1]]
  (2) iterator:  isinstance(reversed(d), collections.abc.Iterator)  (F2P type oblig.)
  (3) read-only: materializing reversed(d) leaves list(iter(d)) unchanged

over boundary cases (empty, singleton, the F2P witness [1,2,3], duplicates that
collapse keys) and 20000 randomized fuzz inputs.

Imports nothing repo-specific: `reversed`/`dict`/`collections.abc` are the
Python builtins/stdlib the gold patch itself uses. Exit 0 iff every obligation
holds.
"""
import collections.abc
import random
import sys


def rev_seq(xs):
    """Reference implementation of Solution.lean's deep model `revSeq`, literal
    to its front-recursive definition:
        revSeq []      = []
        revSeq (c::cs) = revSeq cs ++ [c]"""
    if not xs:
        return []
    c, cs = xs[0], xs[1:]
    return rev_seq(cs) + [c]


def check_reverse_reference(items):
    """Build the collection's backing dict (distinct keys, insertion order),
    then assert the three A-reference obligations against the REAL `reversed`."""
    d = dict.fromkeys(items)            # OrderedSet.__init__ semantics
    keys = list(d)                      # list(iter(self.dict)) — forward enum

    # (1) value: real reversed(dict) == deep model revSeq over the keys
    observed = list(reversed(d))        # the REAL callee (new __reversed__ body)
    expected = rev_seq(keys)            # deep model revSeq
    assert observed == expected, (
        "revSeq deep model unsound on %r: reversed(dict) gave %r, "
        "deep model gives %r" % (items, observed, expected))
    # cross-check the deep model equals the obvious slice reversal
    assert expected == keys[::-1], (
        "revSeq != keys[::-1] on %r: %r vs %r" % (items, expected, keys[::-1]))

    # (2) iterator-ness (F2P type obligation, refinement.md §B)
    it = reversed(d)
    assert isinstance(it, collections.abc.Iterator), (
        "reversed(dict) is not a collections.abc.Iterator on %r" % (items,))

    # (3) read-only: materializing the backward iterator leaves forward enum intact
    _ = list(reversed(d))
    assert list(d) == keys, (
        "reversed(dict) disturbed the forward enumeration on %r" % (items,))


def main():
    boundary = [
        [],                      # empty collection
        [1],                     # singleton
        [1, 2, 3],               # the F2P witness -> [3, 2, 1]
        [3, 2, 1],
        [0, -1, -2, 5, 100],
        [1, 1, 2, 2, 3],         # duplicates collapse to distinct keys (dict)
        [5, 5, 5],               # all duplicates -> single key
        list(range(50)),
        list(range(50))[::-1],
    ]
    for items in boundary:
        check_reverse_reference(items)

    rng = random.Random(14089)
    for _ in range(20000):
        n = rng.randint(0, 40)
        # mix of values, including repeats (to exercise key collapse)
        items = [rng.randint(-20, 20) for _ in range(n)]
        check_reverse_reference(items)

    print("G-AX OK: revSeq deep model (== list(reversed(dict))) sound on "
          "%d boundary + 20000 fuzz inputs; reversed(dict) is an "
          "collections.abc.Iterator and read-only." % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
