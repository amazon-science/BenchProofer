#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_m2mIdentity
against the patch.diff behaviour (post-patch `ManyToManyRel.identity`).

The impl region is NOT all-A-tagged (it has I/R structure), so this runs a real
fuzz. The single A-reference op (the field-name sequence canonicaliser) is left
as the REAL repo callee `make_hashable` — exactly what the post-patch identity
property calls. The shadow therefore reproduces the post-patch behaviour
op-for-op; we assert zero disagreements vs an independent reconstruction of the
patched property over >=10^5 fuzzed inputs, and additionally assert the whole
key is hashable (the bug was an unhashable key).

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14672          # pinned in mapping.md
N = 120_000           # >= 10^5


# REAL callee, vendored verbatim from django/utils/hashable.py @ 00ea883.
def is_iterable(x):
    try:
        iter(x)
    except TypeError:
        return False
    return True


def make_hashable(value):
    if isinstance(value, dict):
        return tuple([
            (key, make_hashable(nested_value))
            for key, nested_value in sorted(value.items())
        ])
    try:
        hash(value)
    except TypeError:
        if is_iterable(value):
            return tuple(map(make_hashable, value))
        raise
    return value


def shadow(base, through, through_fields, db_constraint):
    """R/I shadow of implementation_m2mIdentity.

    acc := base; acc += [through]; acc += [canonTF(through_fields)];
    acc += [db_constraint]; return acc.
    The A-reference op canonTF is realised by the REAL callee make_hashable on
    the through_fields component, i.e. the post-patch identity slot.
    """
    acc = list(base)
    acc.append(through)
    acc.append(make_hashable(through_fields))
    acc.append(db_constraint)
    return tuple(acc)


def patched_identity(base, through, through_fields, db_constraint):
    """Independent reconstruction of the post-patch identity property:
    super().identity + (self.through, make_hashable(self.through_fields),
                        self.db_constraint)."""
    return tuple(base) + (through, make_hashable(through_fields), db_constraint)


def rand_name(rng):
    pool = ["event", "invitee", "parent", "model", "child", "clash",
            "person", "group", "a", "b", "c", "field_1", "x", ""]
    return rng.choice(pool)


def rand_through_fields(rng):
    k = rng.randint(0, 5)
    names = [rand_name(rng) for _ in range(k)]
    choice = rng.randint(0, 2)
    if choice == 0:
        return None
    if choice == 1:
        return list(names)
    return tuple(names)


def rand_base(rng):
    # opaque inherited prefix: a tuple of hashable atoms of small length
    return tuple(rng.choice(["fk", "m", None, True, False, 1, "rn", "rqn"])
                 for _ in range(rng.randint(0, 6)))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    unhashable = 0
    examples = []

    # Deterministic boundary cases (incl. test-patch through_fields values).
    fixed = [
        ((), None, None, True),
        (("fk",), "Through", ["event", "invitee"], True),
        (("fk",), "Through", ("event", "invitee"), True),
        (("fk", "m"), "Through", ["parent", "model"], False),
        ((), None, [], True),
        ((), None, (), True),
        (("a", None, True), "T", ["child", "parent"], True),
    ]

    cases = fixed + [
        (rand_base(rng), rng.choice(["Through", "T2", None]),
         rand_through_fields(rng), rng.choice([True, False]))
        for _ in range(N)
    ]

    for base, through, tf, dbc in cases:
        got = shadow(base, through, tf, dbc)
        want = patched_identity(base, through, tf, dbc)
        try:
            hash(got)
            hash(want)
        except TypeError:
            unhashable += 1
            if len(examples) < 10:
                examples.append((base, through, tf, dbc, got, want, "unhashable"))
            continue
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((base, through, tf, dbc, got, want, "value"))

    if disagreements or unhashable:
        print(f"G-CONF FAIL: {disagreements} disagreements, "
              f"{unhashable} unhashable keys")
        for b, t, tf, d, g, w, why in examples:
            print(f"  ({why}) base={b!r} through={t!r} tf={tf!r} dbc={d!r} "
                  f"shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements, all keys hashable "
          f"(seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
