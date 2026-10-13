#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14089.

The bundle has NO consumed `@ContractOnly` axiom (model.py's axioms region is
empty). The one kind-A obligation is an **A-reference**: the deep model `rev`
(model.py pure region) encodes the net effect of the backward enumeration of an
insertion-ordered, distinct-key collection — i.e. the materialized backward
traversal equals the reversal of the forward traversal. This script validates
that deep model against the REAL Python behaviour the gold patch relies on:

  * the collection stores its elements as the keys of a `dict` built from an
    iterable (`dict.fromkeys(...)`), preserving insertion order with distinct
    keys (the standard library `OrderedSet` carrier);
  * forward enumeration is `iter(d)` -> the keys in insertion order;
  * backward enumeration is `reversed(d)` -> the keys in reverse insertion
    order, and is an `Iterator` (one-shot traversal).

The check asserts, on boundary + randomized fuzz inputs, that

    list(reversed(d)) == rev(list(d))            (== list(iter(d))[::-1])

where `rev` is the model's reference reversal, AND that `reversed(d)` is a
`collections.abc.Iterator` (the F2P type obligation), AND that consuming it
leaves the collection's forward enumeration unchanged (read-only).

Imports nothing repo-specific: `dict`/`reversed`/`iter` are Python builtins and
`collections.abc` is the standard library — the same machinery the gold patch
calls (`reversed(self.dict)`). Exit 0 iff every obligation holds.
"""
import collections.abc
import random
import sys


def rev(seq):
    """Reference implementation of model.py's deep model `rev`: the reversal of
    a sequence (rev(s) = rev(s.drop(1)) + [s[0]])."""
    out = []
    for i in range(len(seq) - 1, -1, -1):
        out.append(seq[i])
    return out


def build_collection(items):
    """The standard-library OrderedSet carrier: distinct keys in insertion
    order, stored as a dict's keys (dict.fromkeys, as in OrderedSet.__init__)."""
    return dict.fromkeys(items)


def check_reversed_reference(items):
    """Assert the deep model `rev` == real `reversed(dict)`, that the backward
    traversal is an Iterator, and that it does not disturb forward order."""
    d = build_collection(items)

    forward = list(iter(d))                      # real forward enumeration
    backward_iter = reversed(d)                  # real backward enumeration

    # F2P type obligation: reversed(...) is a one-shot iterator.
    assert isinstance(backward_iter, collections.abc.Iterator), (
        "backward enumeration of %r is not an Iterator (got %r)"
        % (items, type(backward_iter)))

    backward = list(backward_iter)               # materialize the real callee
    expected = rev(forward)                       # deep model

    assert backward == expected, (
        "rev deep model unsound on %r: reversed(dict) gave %r, "
        "deep model gives %r" % (items, backward, expected))

    # Read-only: materializing the backward iterator leaves forward order intact.
    assert list(iter(d)) == forward, (
        "backward enumeration mutated the collection on %r" % (items,))

    # Distinct-key carrier: rev of forward is its exact element-wise reversal.
    for k in range(len(forward)):
        assert backward[k] == forward[len(forward) - 1 - k], (
            "element %d of backward != element %d of forward on %r"
            % (k, len(forward) - 1 - k, items))


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        [],
        [1],
        [1, 2, 3],                # the F2P witness: list(reversed) == [3, 2, 1]
        [3, 2, 1],
        [0],
        [-1, 0, 1],
        list(range(10)),
        list(range(50)),
        [5, 4, 3, 2, 1],
        # duplicate inputs collapse to distinct keys, insertion order kept
        [1, 1, 2, 2, 3, 3],
        [2, 1, 2, 3, 1],
        ["a", "b", "c"],          # OrderedSet is generic over hashables
        ["c", "b", "a"],
        [None],
        [True, False],
    ]
    for items in boundary:
        check_reversed_reference(items)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(14089)
    for _ in range(20000):
        n = rng.randint(0, 24)
        # draw from a small pool so duplicates (collapsing keys) are exercised
        items = [rng.randint(-8, 8) for _ in range(n)]
        check_reversed_reference(items)

    print("G-AX OK: rev deep model (== reversed(dict)) sound on %d boundary + "
          "20000 fuzz inputs; backward traversal is an Iterator and read-only"
          % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
