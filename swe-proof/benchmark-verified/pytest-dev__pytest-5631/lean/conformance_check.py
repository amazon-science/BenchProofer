#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_num_mock_patch_args against the patch.diff behaviour (the
post-patch `num_mock_patch_args`).

The impl region is NOT all-A-tagged (it has I/R structure), so this runs a real
fuzz. The single A-reference op (the identity-based "consumes an argument"
classifier) is left as the REAL post-patch logic: we build genuine decoration
objects (with a real numpy-like replacement whose `__eq__` raises) and run the
faithfully-reconstructed post-patch `num_mock_patch_args` over them. We diff that
against the structural shadow `some(len([p for p in ps if not attr and
is_sentinel]))` over >=10^5 fuzzed decoration lists. exit 0 iff zero
disagreements.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 5631
N = 120_000

# Two distinct sentinel "DEFAULT" objects, as the post-patch code obtains via
# getattr(sys.modules.get(...), "DEFAULT", object()).
MOCK_SENTINEL = object()
UT_MOCK_SENTINEL = object()


class NumpyLike:
    """Replacement value whose equality has an ambiguous truth value, like a
    numpy array (#5606). Identity comparisons (`is`) are still total."""
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        raise ValueError("ambiguous truth value (like a numpy array)")

    __hash__ = None


class Patch:
    """A real decoration object: attribute_name + replacement `new`."""
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new


def num_mock_patch_args_postpatch(patchings):
    """Faithful reconstruction of the POST-PATCH function (identity-based).
    Never raises on `new`'s equality."""
    if not patchings:
        return 0
    mock_sentinel = MOCK_SENTINEL
    ut_mock_sentinel = UT_MOCK_SENTINEL
    return len(
        [
            p
            for p in patchings
            if not p.attribute_name
            and (p.new is mock_sentinel or p.new is ut_mock_sentinel)
        ]
    )


def shadow(abstract):
    """R/I shadow of implementation_num_mock_patch_args over the abstraction
    (attributeName, isSentinel, eqWellDefined). Mirrors the Lean impl:
    some 0 on empty, else some(count of structurally-counted decorations)."""
    if not abstract:
        return ("some", 0)
    count = 0
    for attr, is_sent, _eq in abstract:
        if (not attr) and is_sent:
            count += 1
    return ("some", count)


def build_decoration(rng):
    """Return (real Patch object, abstraction tuple)."""
    attr = rng.random() < 0.35
    attribute_name = "x" if attr else (None if rng.random() < 0.5 else "")
    kind = rng.random()
    if kind < 0.30:
        new = MOCK_SENTINEL
        is_sent = True
        eq_ok = True
    elif kind < 0.55:
        new = UT_MOCK_SENTINEL
        is_sent = True
        eq_ok = True
    elif kind < 0.80:
        new = object()             # ordinary replacement, total equality
        is_sent = False
        eq_ok = True
    else:
        new = NumpyLike(rng.randint(0, 9))   # ambiguous equality, not a sentinel
        is_sent = False
        eq_ok = False
    return Patch(attribute_name, new), (bool(attribute_name), is_sent, eq_ok)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    cases = []
    # Deterministic boundary lists first.
    cases.append([])                                                  # empty
    cases.append([Patch(None, MOCK_SENTINEL)])                        # one sentinel
    cases.append([Patch("name", MOCK_SENTINEL)])                      # attr-bound sentinel
    cases.append([Patch(None, NumpyLike(7))])                         # numpy-like, positional
    cases.append([Patch("name", NumpyLike(7))])                       # numpy-like, attr-bound
    cases.append([Patch(None, MOCK_SENTINEL), Patch(None, UT_MOCK_SENTINEL)])
    cases.append([Patch(None, object()), Patch(None, NumpyLike(1))])
    boundary = len(cases)

    for _ in range(N):
        n = rng.randint(0, 6)
        decs = [build_decoration(rng) for _ in range(n)]
        cases.append(decs)

    for case in cases:
        if case and isinstance(case[0], Patch):
            reals = case
            abstract = None
        else:
            reals = [d[0] for d in case]
            abstract = [d[1] for d in case]
        # Build abstraction from the real objects when not provided.
        if abstract is None:
            abstract = []
            for p in reals:
                is_sent = p.new is MOCK_SENTINEL or p.new is UT_MOCK_SENTINEL
                eq_ok = not isinstance(p.new, NumpyLike)
                abstract.append((bool(p.attribute_name), is_sent, eq_ok))

        want_int = num_mock_patch_args_postpatch(reals)   # REAL post-patch, never raises
        want = ("some", want_int)
        got = shadow(abstract)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((abstract, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for a, g, w in examples:
            print(f"  abstract={a} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs ({boundary} boundary + {N} fuzz), "
          f"0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
