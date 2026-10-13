#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-10051.

The single consumed axiom is `empty_in_place` (model.py axioms region), which
stands in for the unchanged language builtin that empties a list IN PLACE:

    Requires Acc(list_pred(xs))
    Requires MustTerminate(1)   # the builtin always returns (bounded step)
    Ensures  Acc(list_pred(xs))
    Ensures  len(xs) == 0
    Ensures  xs is Old(xs)      # the crux: SAME object, not a fresh empty list

The real callee is Python's `list.clear()` (equivalently the `del xs[:]` /
`xs[:] = []` in-place emptying). This script executes the REAL builtin on
boundary + fuzz inputs and asserts, for every observation:

  * the list is empty afterwards            (len == 0),
  * its object identity is preserved        (id unchanged: `xs is xs_before`),
  * any external reference taken BEFORE the clear still names the now-empty
    list and sees subsequently-appended items (this is the aliasing property
    the fix relies on, the negative of the buggy rebind `xs = []`).

It also exhibits the CONTRAST that the bug embodies: rebinding (`xs = []`) does
NOT preserve identity, so a previously-taken reference would be orphaned — which
is exactly the divergence `empty_in_place`'s identity clause forbids.

Imports nothing repo-specific: `list.clear` is a Python builtin. Exit 0 iff
every obligation holds.
"""
import random
import sys


def check_clear_preserves_identity(elements):
    """Assert the REAL list.clear() empties the list in place AND preserves the
    object's identity, and that an alias taken before the clear tracks it."""
    xs = list(elements)
    xs_id = id(xs)
    alias = xs                      # external reference handed out earlier
    assert alias is xs

    xs.clear()                      # the REAL in-place emptying builtin

    # Ensures len(xs) == 0
    assert len(xs) == 0, "list.clear() left %d elements" % len(xs)
    # Ensures xs is Old(xs): the object identity is preserved
    assert id(xs) == xs_id, "list.clear() did not preserve object identity"
    # the alias still names the same (now-empty) live object
    assert alias is xs, "alias diverged from the buffer after clear()"
    assert len(alias) == 0, "alias does not see the cleared list as empty"

    # subsequently captured items are visible through the alias too
    xs.append(1234)
    assert alias is xs
    assert len(alias) == 1 and alias[0] == 1234, (
        "alias does not track an item appended after clear()")


def check_rebind_orphans_alias(elements):
    """Exhibit the contrast: rebinding to a fresh [] (the bug) does NOT preserve
    identity, so a previously-taken alias is orphaned and diverges. This is the
    behaviour `empty_in_place`'s identity clause rules out."""
    if not elements:
        return
    xs = list(elements)
    alias = xs                      # reference handed out earlier
    xs = []                         # the buggy rebind (handler.reset())
    # alias still points at the OLD object -> it is NOT empty, NOT the new list
    assert alias is not xs, "rebind unexpectedly kept identity"
    assert len(alias) == len(elements), "old object should be unchanged"
    xs.append(1234)
    assert len(alias) == len(elements), (
        "orphaned alias should NOT see items appended to the rebound list")


def main():
    rng = random.Random(10051)

    boundary = [
        [],
        [0],
        [1, 2, 3],
        list(range(100)),
        [None, "x", 3.5, (1, 2)],     # heterogeneous elements
    ]
    for elements in boundary:
        check_clear_preserves_identity(elements)
        check_rebind_orphans_alias(elements)

    for _ in range(20000):
        n = rng.randint(0, 30)
        elements = [rng.randint(-1000, 1000) for _ in range(n)]
        check_clear_preserves_identity(elements)
        check_rebind_orphans_alias(elements)

    print("G-AX OK: empty_in_place axiom (== real list.clear()) sound on %d "
          "boundary + 20000 fuzz inputs: in-place emptying preserves object "
          "identity and alias tracking; the buggy rebind orphans the alias."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
