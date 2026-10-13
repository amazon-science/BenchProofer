#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14672.

Validates the ONE kind-A obligation of this bundle: the deep model
`canonicalize` (Solution.lean pure region) faithfully models the REAL unchanged
callee `django.utils.hashable.make_hashable` on the slot domain the changed
function feeds it (an A-reference, refinement.md / mapping.md §3.1). There are
NO consumed axioms.

The changed function (`ManyToManyRel.identity`) wraps its sequence-valued slot
(`self.through_fields`) with `make_hashable` so the assembled identity tuple is
usable as a hash key. The slot domain in this codepath is exactly what
`ManyToManyRel.__init__` stores: `None`, or a sequence (tuple/list) of
field-name strings. On that domain the deep model claims:

  * canonicalize(None)            == None                  (absent slot unchanged)
  * canonicalize(seq xs _)        == seq xs (loose=False)  (same items+order,
                                                            now hashable/immutable)

So G-AX asserts, against the REAL make_hashable, for every boundary + fuzz slot:

  (A1) make_hashable(value) is HASHABLE                        (the bug it fixes)
  (A2) make_hashable preserves the element sequence (order+items): a sequence of
       names becomes the tuple of the SAME names; None stays None
  (A3) make_hashable(list) == make_hashable(tuple(list))       (loose vs canonical
       canonicalize to the SAME value — the equality content __hash__ must agree
       with __eq__ on, i.e. why an inherited reverse relation hashes equal)

Imports only `django.utils.hashable` (no ORM, no DB, no settings). Exit 0 iff
every obligation holds.
"""
import random
import sys

from django.utils.hashable import make_hashable


def slot_to_canonical_items(value):
    """The deep model `canonicalize`, projected to the observable (items, kind):
    returns None for an absent slot, or the tuple of names for a sequence."""
    if value is None:
        return None
    # a sequence of names -> the canonical tuple of the same names, in order
    return tuple(value)


def check_slot(value):
    observed = make_hashable(value)                 # REAL callee

    # (A1) the result is usable as a hash key
    try:
        hash(observed)
    except TypeError as e:
        raise AssertionError(
            "make_hashable(%r) = %r is NOT hashable: %s" % (value, observed, e))

    # (A2) the canonical form preserves the element sequence (order + items)
    expected = slot_to_canonical_items(value)
    assert observed == expected, (
        "canonicalize deep model unsound on %r: make_hashable gave %r, deep "
        "model gives %r" % (value, observed, expected))

    # (A3) a loose (list) and an already-canonical (tuple) sequence of the same
    # names canonicalize to the SAME value (the equality content)
    if value is not None:
        as_list = list(value)
        as_tuple = tuple(value)
        assert make_hashable(as_list) == make_hashable(as_tuple), (
            "make_hashable(list) != make_hashable(tuple) on %r" % (value,))


def main():
    names = ["event", "invitee", "parent", "model", "child", "a", "Z", "x_y",
             "field0", "second_child"]

    # --- boundary slots ----------------------------------------------------
    boundary = [
        None,
        [], (),
        ["event", "invitee"],            # the F2P through_fields (list form)
        ("event", "invitee"),            # the tuple form it must hash-equal to
        ["parent", "model"],             # the test_models clash test
        ["event"], ("event",),
        ["a", "a"],                      # repeated names (order/content matters)
        ["b", "a"], ["a", "b"],          # order is significant
        tuple(names), list(names),
    ]
    for v in boundary:
        check_slot(v)

    # --- randomized fuzz over the slot domain ------------------------------
    rng = random.Random(14672)
    for _ in range(20000):
        n = rng.randint(0, 6)
        seq = [rng.choice(names) for _ in range(n)]
        # fuzz both container kinds (loose list and canonical tuple) and None
        kind = rng.randint(0, 2)
        if kind == 0:
            check_slot(None)
        elif kind == 1:
            check_slot(seq)              # list (loose)
        else:
            check_slot(tuple(seq))       # tuple (already canonical)

    print("G-AX OK: canonicalize deep model (== make_hashable) sound on %d "
          "boundary + 20000 fuzz slots; hashable, sequence-preserving, and "
          "list==tuple on every observation." % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
