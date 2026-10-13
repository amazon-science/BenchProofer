#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14915.

Executes the REAL stdlib membership-identity primitive (the built-in `hash`)
on Requires-satisfying inputs (boundary integer keys, the FAIL_TO_PASS
primary-key pattern, and randomized fuzz) and asserts every observation matches
the model, as encoded in model.py.

The one kind-A check:

  (A-consumed) the `value_identity` axiom (model.py axioms region) is the
      weakest sufficient contract on the built-in `hash` applied to the wrapped
      value: a fixed pure (deterministic) function of its single argument. The
      method under spec returns exactly `value_identity(self.value)`, mirroring
      the gold `return hash(self.value)`.

Beyond the bare axiom this also validates the two FAIL_TO_PASS obligations the
proof relies on `hash` to satisfy on the specific test inputs (these are
properties of the REAL callee on those inputs, NOT claimed by the axiom):

  (1) equal value, different derived object => equal hash
      (`hash(value_1) == hash(ModelChoiceIteratorValue(c1.pk, None))`), and
  (2) distinct auto-increment primary keys => distinct hash
      (`hash(value_1) != hash(value_2)`).

It reconstructs the real `ModelChoiceIteratorValue.__hash__` behaviour
(`hash(self.value)`) to confirm the wrapper's membership identity is the
identity of its wrapped value, computed from `value` alone.

Imports nothing repo-specific: `hash` is a Python built-in and `random` is
standard library. Exit 0 iff every obligation holds.
"""
import random
import sys


# --- a faithful stand-in for the gold ModelChoiceIteratorValue --------------
# Mirrors django/forms/models.py post-patch: __hash__ delegates to the wrapped
# value's hash and is independent of `instance`.
class ChoiceValue:
    def __init__(self, value, instance):
        self.value = value
        self.instance = instance

    def __hash__(self):
        return hash(self.value)          # the gold patch, verbatim semantics


# --- the checks --------------------------------------------------------------

def check_value_identity_deterministic(v):
    """A-consumed: value_identity is a fixed function of its argument — the
    REAL `hash` is deterministic on `v` (same value -> same identity), and the
    result is a function of `v` alone."""
    a = hash(v)
    b = hash(v)
    assert a == b, (
        "value_identity axiom unsound: hash(%r) is non-deterministic "
        "(%r vs %r)" % (v, a, b))


def check_wrapper_identity_is_value_identity(value, instance):
    """The modeled method: ChoiceValue.membership_identity == value_identity of
    the wrapped value (and never of the derived object). hash of the wrapper
    must equal hash of the bare wrapped value, regardless of `instance`."""
    cv = ChoiceValue(value, instance)
    assert hash(cv) == hash(value), (
        "wrapper hash %r != value identity %r for value=%r instance=%r"
        % (hash(cv), hash(value), value, instance))


def main():
    # --- FAIL_TO_PASS obligation (1): equal value, different derived object,
    #     equal hash. The test uses (c1.pk, c1) vs (c1.pk, None).
    pk_pattern = [1, 2, 3, 4, 5, 42, 1000, 2 ** 31, 2 ** 63 + 7]
    objects = [object(), None, "an-instance", 12345, ("a", "tuple")]
    for pk in pk_pattern:
        # the wrapper's hash must be the value's hash for ANY derived object
        for inst in objects:
            check_wrapper_identity_is_value_identity(pk, inst)
        # and in particular two wrappers with the SAME value but different
        # derived objects must agree (the exact F2P assertion 1 shape)
        v_real = ChoiceValue(pk, objects[0])
        v_none = ChoiceValue(pk, None)
        assert hash(v_real) == hash(v_none), (
            "F2P assertion 1 broken: equal value %r gives different hashes "
            "for different derived objects" % (pk,))

    # --- FAIL_TO_PASS obligation (2): distinct auto-increment pks => distinct
    #     hash. pks are distinct positive ints; for such ints hash(n) == n in
    #     CPython, so no collision. Check the test pair and a broad sweep.
    for i in range(1, 5000):
        for j in (i + 1, i + 7, i + 1000):
            assert hash(ChoiceValue(i, None)) != hash(ChoiceValue(j, None)), (
                "F2P assertion 2 broken: distinct pks %r and %r collide" % (i, j))

    # --- A-consumed: determinism on boundary keys + the pk pattern ----------
    boundary = [0, 1, -1, 2, 7, 255, 256, 2 ** 31 - 1, 2 ** 31, -(2 ** 31),
                2 ** 63, -(2 ** 63), 2 ** 63 - 1] + pk_pattern
    for v in boundary:
        check_value_identity_deterministic(v)
        check_wrapper_identity_is_value_identity(v, None)

    # --- A-consumed: randomized fuzz over integer keys ----------------------
    rng = random.Random(14915)
    for _ in range(20000):
        v = rng.randint(-(2 ** 40), 2 ** 40)
        check_value_identity_deterministic(v)
        check_wrapper_identity_is_value_identity(v, rng.choice(objects))

    print("G-AX OK: value_identity axiom (== built-in hash) deterministic on "
          "%d boundary + 20000 fuzz keys; wrapper hash == wrapped-value hash "
          "(instance-independent); F2P obligations (equal-value/equal-hash and "
          "distinct-pk/distinct-hash) hold." % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
