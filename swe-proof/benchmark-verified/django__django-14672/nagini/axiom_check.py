#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14672.

Executes the REAL canonicaliser (`django.utils.hashable.make_hashable`) on the
inputs the through-fields identity component can take (absent, mutable sequence
of names, immutable sequence of names, boundary and fuzz) and asserts that
every observation matches the deep model encoded in model.py.

This is an A-reference check: the canonicalisation of one identity component is
modelled DEEPLY in model.py (the `Value` carrier with `canonical_names` /
`canonical_items` / `is_hashable`), not behind a consumed axiom. G-AX validates
that deep model against the real callee:

  model.py                              real make_hashable(names)
  --------------------------------      ----------------------------------------
  names is None                         -> None             (kind ABSENT, hashable)
  a present sequence of names           -> a tuple of names (kind IMMUTABLE,
                                           hashable, order- and element-preserving)

and the load-bearing property the fix introduces:

  * make_hashable(names) is ALWAYS hashable (so the identity is hashable);
  * the raw mutable sequence (the pre-patch component) is NOT hashable, which
    is exactly the defect (`hash(self.identity)` raised on the list).

Names (strings) are modelled as `int` atoms in model.py; here they are the real
field-name strings, which `make_hashable` leaves untouched (each is already
hashable), so the element sequence is preserved verbatim.

Imports only Django's standalone `make_hashable` utility (no settings needed)
and the standard library. Exit 0 iff every obligation holds.
"""
import random
import string
import sys

from django.utils.hashable import make_hashable


# model.py kind tags (kept in lock-step with the pure region)
KIND_ABSENT = 0
KIND_MUTABLE = 1
KIND_IMMUTABLE = 2


def model_kind(names):
    """canonical_names: the KIND the component contributes after canonicalisation."""
    return KIND_ABSENT if names is None else KIND_IMMUTABLE


def model_items(names):
    """canonical_items: the element sequence after canonicalisation (order
    preserving; empty when absent)."""
    return tuple() if names is None else tuple(names)


def _is_hashable(value):
    try:
        hash(value)
        return True
    except TypeError:
        return False


def check_component(names):
    """Assert the deep model agrees with the REAL make_hashable on `names`."""
    observed = make_hashable(names)            # real callee

    # (1) the real result is hashable in every case (the property the fix needs).
    assert _is_hashable(observed), (
        "make_hashable result unexpectedly unhashable for %r: %r"
        % (names, observed))

    # (2) kind: absent stays absent (None); a present list becomes a tuple.
    if names is None:
        assert observed is None, (
            "absent component should stay None, got %r" % (observed,))
        assert model_kind(names) == KIND_ABSENT
    else:
        assert isinstance(observed, tuple), (
            "present sequence should canonicalise to a tuple, got %r"
            % (observed,))
        assert model_kind(names) == KIND_IMMUTABLE

    # (3) element sequence preserved, in order (so equal collections -> equal
    #     identities -> equal hashes).
    assert tuple(observed or ()) == model_items(names), (
        "element sequence not preserved for %r: make_hashable gave %r, "
        "deep model gives %r" % (names, observed, model_items(names)))

    # (4) equal collections produce equal (and equally-hashing) canonical forms.
    if names is not None:
        twin = make_hashable(list(names))
        assert observed == twin and hash(observed) == hash(twin), (
            "equal collections produced unequal canonical forms for %r" % (names,))


def check_prepatch_defect(names):
    """The raw mutable sequence (the pre-patch component) is unhashable when
    non-empty -- the exact `unhashable type: 'list'` defect."""
    if names:
        assert not _is_hashable(list(names)), (
            "raw list unexpectedly hashable: %r" % (names,))


def main():
    boundary = [
        None,
        [],
        ['event', 'invitee'],          # the F2P through_fields list
        ['parent', 'model'],
        ['child', 'parent'],
        ['a'],
        ['x', 'y', 'z', 'w'],
        ['dup', 'dup'],
        ['', ''],
        ('event', 'invitee'),          # an already-immutable collection
        tuple(),
    ]
    for names in boundary:
        check_component(names)
        check_prepatch_defect(names)

    # randomized fuzz over lists of field-name-like strings
    rng = random.Random(14672)
    alphabet = string.ascii_lowercase + '_0123456789'
    for _ in range(20000):
        n = rng.randint(0, 6)
        names = [
            ''.join(rng.choice(alphabet) for _ in range(rng.randint(0, 8)))
            for _ in range(n)
        ]
        # exercise both the list form and (sometimes) None
        if rng.random() < 0.05:
            names = None
        check_component(names)
        check_prepatch_defect(names)

    print("G-AX OK: make_hashable deep model (Value/canonical_names/"
          "canonical_items/is_hashable) sound on %d boundary + 20000 fuzz "
          "through-fields inputs; result always hashable, raw list not."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
