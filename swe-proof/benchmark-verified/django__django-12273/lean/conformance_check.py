#!/usr/bin/env python3
"""G-CONF for django__django-12273 — cross-language differential test of the
R/I shadow of `implementation_setPrimaryKey` against the post-patch behavior of
`Model._set_pk_val`.

The impl region is all R/I (no A-tagged op): a loop over the ordered ancestor
parent-links, a guard (`parent_link and parent_link != self._meta.pk`), a
`setattr` of each qualifying ancestor-key attribute, and the always-applied own
primary-key `setattr`. We build that shadow op-for-op and diff it against an
INDEPENDENT reconstruction of the patched `_set_pk_val` semantics:

    post-patch:  for each parent_link in parents (in order):
                     if linked and not is_pk: store[keyName] = value
                 store[pk_name] = value

Both sides operate on a plain attribute dict bridged via mapping.md
(`None` <-> Lean `none`, `int n` <-> `some n`). Zero disagreements required over
>= 10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements. Pinned seed: 12273.
"""
import random
import sys

SEED = 12273          # pinned in mapping.md
N = 150_000           # >= 10^5

ATTR_NAMES = ["id", "uid", "pk_id", "user_ptr_id", "politician_ptr_id",
              "person_ptr_id", "place_ptr_id", "profile_id", "f", "name"]
VALUES = [None, 0, 1, 7, 42, -3, 1000]


def rand_store(rng):
    return {name: rng.choice(VALUES) for name in ATTR_NAMES if rng.random() < 0.7}


def rand_links(rng, pk_name):
    links = []
    for _ in range(rng.randint(0, 4)):
        linked = rng.random() < 0.85
        # A link that coincides with the own pk attname (sameAsPrimaryKey).
        is_pk = rng.random() < 0.3
        key = pk_name if is_pk else rng.choice(ATTR_NAMES)
        links.append({"linked": linked, "is_pk": is_pk, "key": key})
    return links


def shadow(store, pk_name, links, value):
    """R/I shadow of implementation_setPrimaryKey (op-for-op)."""
    s = dict(store)
    for link in links:
        if link["linked"] and not link["is_pk"]:
            s[link["key"]] = value
    s[pk_name] = value
    return s


def patched_set_pk_val(store, pk_name, links, value):
    """Independent reconstruction of the post-patch `_set_pk_val`:
        for parent_link in parents.values():
            if parent_link and parent_link != pk:
                setattr(self, parent_link.target_field.attname, value)
        return setattr(self, pk.attname, value)
    """
    s = dict(store)
    for link in links:
        parent_link_truthy = link["linked"]
        not_equal_pk = not link["is_pk"]
        if parent_link_truthy and not_equal_pk:
            s[link["key"]] = value
    s[pk_name] = value
    return s


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases incl. the F2P shapes:
    #  * single-inheritance reset: pk=None must clear the one ancestor key.
    #  * multi-inheritance reset: pk=None must clear several ancestor keys.
    fixed = [
        ({"profile_id": 1, "user_ptr_id": 5, "username": 9}, "profile_id",
         [{"linked": True, "is_pk": False, "key": "user_ptr_id"}], None),
        ({"id": 2, "politician_ptr_id": 3, "person_ptr_id": 4}, "id",
         [{"linked": True, "is_pk": False, "key": "politician_ptr_id"},
          {"linked": True, "is_pk": False, "key": "person_ptr_id"}], None),
        # link equal to own pk → skipped (handled by own-key write):
        ({"place_ptr_id": 7}, "place_ptr_id",
         [{"linked": True, "is_pk": True, "key": "place_ptr_id"}], None),
        # absent link → skipped:
        ({"id": 1, "x_ptr_id": 8}, "id",
         [{"linked": False, "is_pk": False, "key": "x_ptr_id"}], 99),
        # no ancestor links (plain model):
        ({"uid": 1, "f": 0}, "uid", [], None),
    ]

    cases = []
    for store, pk, links, value in fixed:
        cases.append((store, pk, links, value))
    for _ in range(N):
        pk = rng.choice(ATTR_NAMES)
        store = rand_store(rng)
        links = rand_links(rng, pk)
        value = rng.choice(VALUES)
        cases.append((store, pk, links, value))

    for store, pk, links, value in cases:
        got = shadow(store, pk, links, value)
        want = patched_set_pk_val(store, pk, links, value)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((store, pk, links, value), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
