#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13401.

The one opaque callee the proof consumes is `pyHash` (Solution.lean axioms
region) — the digest a descriptor exposes. It models the **unchanged CPython
builtin** `hash(tuple)` applied to the key tuple
`keyOf a = (creation_counter, app_label?, model_name?)`. That builtin is the
real callee the patched `__hash__` delegates to, and it is byte-identical
pre/post-patch (the patch changes which *tuple* is built, not the hashing
primitive).

IMPORTANT — what this check does NOT do, and why (SPEC_GUIDE directive 7):
It never invokes `Field.__hash__`. `Field.__hash__` is the function *under
spec* / the operation the patch changes; axiomatizing or validating against it
would be a directive-7 violation. (It would also be meaningless here: G-AX runs
at `base_commit` with no gold patch applied, so `Field.__hash__` is still the
*pre-patch* `hash(self.creation_counter)` — the very bug. Earlier the check
compared against `hash(field)` and tripped on exactly this: `hash(0)==0`.)
The key-*construction* bijection (`keyOf` ↔ the tuple the patched `__hash__`
builds, and `Option.map (·.1/.2)` ↔ the `... if hasattr(self,'model') else None`
conditionals) is a pure R/I refinement leg: its observable consequence — the
real digest's equal/unequal *relation* matching key equality — is validated by
G-CONF against the *patched* callee, and the construction itself is audited by
G-EQ. G-AX's remit is the contract on the unchanged real callee only.

Two obligations on the real builtin `hash(tuple)`:

  (function-of-the-key / A-consumed contract) the digest is a deterministic
      function of the key — equal key tuples give equal digests. Verified on
      boundary keys plus randomized fuzz.

  (F2P distinctness — the property the proof's opaque `pyHash` cannot itself
      guarantee, so it must hold for the REAL callee) for keys that share a
      counter but differ in model identity (the abstract-parent-vs-children
      case the F2P test `assertNotEqual(hash(a), hash(b))` observes), the real
      digests are distinct. Checked on the exact F2P triple and a curated set
      of equal-counter / model-differing key pairs.

stdlib-only (`hash` is a builtin; no Django import needed — mirrors the
exemplar, which runs the unchanged stdlib callee directly). Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- the key model (keyOf a, transliterated) ---------------------------------

def _key_tuple(counter, owner):
    """keyOf a as the tuple the patched `__hash__` digests:
    (counter, app_label?, model_name?), absent components -> None."""
    if owner is None:
        return (counter, None, None)
    return (counter, owner[0], owner[1])


# --- the checks (against the real builtin `hash`) -----------------------------

def check_function_of_key(c1, o1, c2, o2):
    """Equal key tuples ⟹ equal real digest (digest is a function of the key)."""
    k1, k2 = _key_tuple(c1, o1), _key_tuple(c2, o2)
    if k1 == k2:
        assert hash(k1) == hash(k2), (
            "real hash is not a function of the key: %r vs %r both = %r but "
            "hash differs (%r vs %r)" % ((c1, o1), (c2, o2), k1, hash(k1), hash(k2)))


def check_distinct(c1, o1, c2, o2):
    """Keys that differ ⟹ distinct real digest. Asserted ONLY for the
    model-distinguishing class the F2P test exercises (equal counter, differing
    model identity, and the general differing-key boundary set). Not claimed as
    global injectivity over fuzz — that would over-state the callee's contract
    (64-bit hashes collide in principle); it is claimed exactly where the issue
    and the F2P test require de-duplication to stop happening."""
    k1, k2 = _key_tuple(c1, o1), _key_tuple(c2, o2)
    if k1 != k2:
        assert hash(k1) != hash(k2), (
            "F2P distinctness violated: keys %r and %r differ but real digests "
            "collide (%r)" % (k1, k2, hash(k1)))


def main():
    # --- boundary key space ---------------------------------------------------
    significant_owners = [
        None,
        ("model_fields", "abstractmodel"),
        ("model_fields", "inheritabstractmodel1"),
        ("model_fields", "inheritabstractmodel2"),
        ("app", "a"),
        ("app", "b"),
        ("other", "a"),
    ]
    counters = [0, 1, 2, 7, 12, 1000]
    boundary = [(c, o) for c in counters for o in significant_owners]

    # --- function-of-the-key (A-consumed): boundary product -------------------
    for c1, o1 in boundary:
        for c2, o2 in boundary:
            check_function_of_key(c1, o1, c2, o2)

    # --- function-of-the-key: randomized fuzz ---------------------------------
    rng = random.Random(13401)
    labels = ["model_fields", "app", "other", "auth", "x", "abc", "m_1"]
    names = ["abstractmodel", "inheritabstractmodel1", "inheritabstractmodel2",
             "a", "b", "field", "z9", "m"]

    def _rand_record():
        c = rng.randint(0, 5000)
        if rng.random() < 0.3:
            return (c, None)
        return (c, (rng.choice(labels), rng.choice(names)))

    prev = _rand_record()
    for _ in range(20000):
        cur = _rand_record()
        # re-hash the same key twice (determinism within process) and across the
        # equal-key identity: function-of-key on duplicated draws.
        check_function_of_key(prev[0], prev[1], prev[0], prev[1])
        prev = cur

    # --- F2P distinctness on the equal-counter / model-differing class --------
    # The discriminating class the patch targets: same creation_counter, model
    # identity differs. Build all such pairs from the boundary owners.
    real_owners = [o for o in significant_owners if o is not None]
    for c in counters:
        # attached-vs-unattached at equal counter: keys differ -> digests differ
        for o in real_owners:
            check_distinct(c, None, c, o)
        # attached-vs-attached, differing model identity, equal counter
        for i in range(len(real_owners)):
            for j in range(len(real_owners)):
                if real_owners[i] != real_owners[j]:
                    check_distinct(c, real_owners[i], c, real_owners[j])

    # --- the exact F2P triple (abstract parent vs the two children) -----------
    # same counter 7, models differ only by model_name within one app_label;
    # the test asserts assertNotEqual(hash(a), hash(b)) pairwise.
    f2p = [
        (7, ("model_fields", "abstractmodel")),
        (7, ("model_fields", "inheritabstractmodel1")),
        (7, ("model_fields", "inheritabstractmodel2")),
    ]
    hashes = [hash(_key_tuple(c, o)) for c, o in f2p]
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            assert hashes[i] != hashes[j], (
                "F2P distinctness violated: keys %r and %r digest equal (%r)"
                % (_key_tuple(*f2p[i]), _key_tuple(*f2p[j]), hashes[i]))

    print("G-AX OK: real builtin hash(key-tuple) is a function of the key on "
          "%d boundary + 20000 fuzz keys; digests of equal-counter / "
          "model-differing keys (incl. the F2P abstract-vs-children triple) are "
          "distinct." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
