#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model `canonTF` against the REAL
standard-library callee the post-patch identity property delegates to,
`django.utils.hashable.make_hashable`, over the through_fields domain.

The proof consumes NO callee axiom (axioms region empty), but the field-name
sequence canonicaliser is an A-reference (refinement.md row 3): the Lean
`canonTF` is asserted to agree with the real `make_hashable` on boundaries +
fuzz, restricted to the domain the fix actually feeds it — the relation's
`through_fields`, which is `None`, a tuple of strings, or a list of strings
(mapping.md). This guards the deep model against drift from the real routine.

We reproduce `make_hashable` exactly (vendored from django/utils/hashable.py @
base_commit) so the check is stdlib-only and self-contained; the property under
test is `canonTF(seq) == make_hashable(seq)` under the type bijection.

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import sys
from collections.abc import Iterable

SEED = 14672


# --- REAL callee, vendored verbatim from django/utils/hashable.py @ 00ea883 ---
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


# --- Lean `canonTF` under the bijection: result is an HVal we render as a
#     Python object matching make_hashable's output shape.
#     .absent -> None ; .astuple/.aslist xs -> tuple(xs).
def canon_tf(seq):
    """`seq` is None | tuple[str,...] | list[str,...]."""
    if seq is None:
        return None
    # present sequence (tuple or list) -> tuple of the same names
    return tuple(seq)


def rand_name(rng):
    pool = ["event", "invitee", "parent", "model", "child", "clash",
            "person", "group", "a", "b", "c", "field_1", "x", ""]
    return rng.choice(pool)


def main() -> int:
    rng = random.Random(SEED)

    cases = []
    # Boundary cases (incl. the test-patch values).
    cases += [
        None,
        [],
        (),
        ["event", "invitee"],
        ("event", "invitee"),
        ["parent", "model"],
        ["child", "parent"],
        ["a"],
        ("a",),
    ]
    # Fuzz: random None / list / tuple of random names.
    for _ in range(50_000):
        k = rng.randint(0, 5)
        names = [rand_name(rng) for _ in range(k)]
        choice = rng.randint(0, 2)
        if choice == 0:
            cases.append(None)
        elif choice == 1:
            cases.append(list(names))
        else:
            cases.append(tuple(names))

    mismatches = 0
    examples = []
    for seq in cases:
        want = make_hashable(seq)   # REAL callee
        got = canon_tf(seq)
        # both must be hashable (the whole point of the fix)
        try:
            hash(want)
            hash(got)
        except TypeError:
            mismatches += 1
            if len(examples) < 10:
                examples.append((seq, got, want, "unhashable"))
            continue
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append((seq, got, want, "value"))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs make_hashable on through_fields")
        for s, g, w, why in examples:
            print(f"  ({why}) seq={s!r} model={g!r} real={w!r}")
        return 1

    print(f"G-AX OK: canonTF == make_hashable on all through_fields probes "
          f"(seed={SEED}, {len(cases)} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
