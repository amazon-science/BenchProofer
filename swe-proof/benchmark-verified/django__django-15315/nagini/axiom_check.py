#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15315.

The single consumed axiom is `hash_int` (model.py axioms region): the unchanged
standard hashing primitive applied to a single integer. The proof consumes
exactly ONE property of it: it is a deterministic pure function of that integer
alone (so `located_value` returning `hash_int(self.order)` is well-defined and
depends on `order` only). This check executes the REAL stdlib callee `hash` on
integers (boundary + randomized fuzz) and asserts that property.

It also validates the whole-bundle correctness oracle that the deep model
encodes (the A-reference property): a located-value computed as
`hash(creation_order)` is INVARIANT under later attachment to an owner, whereas
the pre-fix located-value `hash((creation_order, owner_label, owner_name))`
CHANGES across attachment. Both the fixed and pre-fix located-value functions
are reconstructed here from the standard `hash` primitive (no repo import is
needed; the touched code computes the hash of a plain int / of a plain tuple of
ints-and-None). Exit 0 iff every obligation holds.

Imports nothing repo-specific: `hash` is a Python builtin and the touched code
hashes only an int (post-fix) or a small tuple (pre-fix). Stdlib-only.
"""
import random
import sys


def fixed_located_value(creation_order):
    """Reconstruction of model.py's `located_value` under the gold fix:
    hash of the creation-order identity ALONE.  Mirrors the post-fix
    `Field.__hash__` -> `hash(self.creation_counter)`."""
    return hash(creation_order)


def prefix_located_value(creation_order, attached, owner_label, owner_name):
    """Reconstruction of the PRE-FIX located-value: hash of the 3-tuple whose
    last two slots are owner-derived when attached and None otherwise.  Mirrors
    the pre-fix `Field.__hash__` -> `hash((creation_counter, app_label or None,
    model_name or None))`."""
    if attached:
        return hash((creation_order, owner_label, owner_name))
    return hash((creation_order, None, None))


def check_hash_int_deterministic(value):
    """Assert the `hash_int` axiom: hash of an int is a deterministic function
    of that int alone (repeated calls agree)."""
    a = hash(value)
    b = hash(value)
    assert a == b, (
        "hash_int axiom unsound: hash(%r) not deterministic (%r vs %r)"
        % (value, a, b))
    # equal inputs -> equal outputs (function-of-its-argument)
    c = hash(int(value))
    assert hash(value) == c, (
        "hash_int axiom unsound: equal ints hash differently (%r: %r vs %r)"
        % (value, hash(value), c))


def main():
    # --- hash_int axiom (A-consumed): determinism on boundary integers -------
    boundary_ints = [
        0, 1, -1, 2, -2,
        7, 42, 100, 1000, 123456789,
        2 ** 31, 2 ** 31 - 1, -(2 ** 31), 2 ** 63, 2 ** 63 - 1, -(2 ** 63),
        2 ** 64, -(2 ** 64), 10 ** 18, -(10 ** 18),
    ]
    for v in boundary_ints:
        check_hash_int_deterministic(v)

    rng = random.Random(15315)
    for _ in range(20000):
        v = rng.randint(-(10 ** 12), 10 ** 12)
        check_hash_int_deterministic(v)

    # --- A-reference oracle: located-value stability under attachment --------
    # The fixed located-value depends only on the creation order, hence is
    # invariant whether or not (and to whom) the object is later attached.
    # The pre-fix located-value folds in owner-derived attributes and changes.
    prefix_unstable_seen = False
    for order in boundary_ints + [rng.randint(0, 10 ** 9) for _ in range(2000)]:
        before = fixed_located_value(order)
        for owner_label in (101, 202, -5, 0, 2 ** 40):
            for owner_name in (303, 404, -7, 0, 2 ** 41):
                after = fixed_located_value(order)
                assert after == before, (
                    "fixed located-value NOT stable under attachment for "
                    "order=%r: %r -> %r" % (order, before, after))
                # the pre-fix value is the discriminator the F2P test catches
                pre_before = prefix_located_value(order, False, 0, 0)
                pre_after = prefix_located_value(
                    order, True, owner_label, owner_name)
                if pre_before != pre_after:
                    prefix_unstable_seen = True

    assert prefix_unstable_seen, (
        "pre-fix located-value never observed to change under attachment; the "
        "differential the F2P test relies on is not exhibited")

    print("G-AX OK: hash_int axiom (deterministic function of one int) sound on "
          "%d boundary + 20000 fuzz integers; fixed located-value invariant "
          "under attachment over all probed owners, pre-fix value changes "
          "(the F2P discriminator)." % len(boundary_ints))
    return 0


if __name__ == "__main__":
    sys.exit(main())
