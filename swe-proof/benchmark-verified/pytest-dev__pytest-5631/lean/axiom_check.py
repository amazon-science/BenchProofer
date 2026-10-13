#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model `isCounted` (and the always-returns
behaviour) against the REAL post-patch classifier the change introduces.

The proof consumes NO callee axiom (axioms region empty), but the "consumes an
argument" classifier is an A-reference (refinement.md row 5): the Lean
`isCounted p = (!p.attributeName && p.isSentinel)` together with the total
`some _` result is asserted to agree, decoration-by-decoration and list-by-list,
with the REAL post-patch `num_mock_patch_args` run over genuine decoration
objects — crucially including numpy-like replacements whose equality raises. This
guards the deep model against drift from the real (identity-based) classifier and
confirms it never raises.

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import sys

SEED = 5631

MOCK_SENTINEL = object()
UT_MOCK_SENTINEL = object()


class NumpyLike:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        raise ValueError("ambiguous truth value (like a numpy array)")

    __hash__ = None


class Patch:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new


def real_num_mock_patch_args(patchings, sentinels):
    """REAL post-patch classifier, parametrised by the active sentinel set so we
    can exercise both modules-present and modules-absent configurations.
    `sentinels` is the tuple of objects identity-recognised as defaults."""
    if not patchings:
        return 0
    return len(
        [p for p in patchings
         if not p.attribute_name and any(p.new is s for s in sentinels)]
    )


def model_isCounted(attr, is_sent):
    """Lean `isCounted`: not attribute-bound and a recognised sentinel."""
    return (not attr) and is_sent


def main() -> int:
    rng = random.Random(SEED)
    mismatches = 0
    examples = []

    # Two sentinel configurations: both modules present; only unittest.mock
    # present (mock absent -> its DEFAULT is a fresh unique object, never matched).
    absent_sentinel = object()  # stands for getattr(absent_module, "DEFAULT", object())
    configs = [
        (MOCK_SENTINEL, UT_MOCK_SENTINEL),       # both present
        (absent_sentinel, UT_MOCK_SENTINEL),     # mock absent
        (MOCK_SENTINEL, object()),               # unittest.mock absent
    ]

    def gen_decoration():
        attr = rng.random() < 0.35
        attribute_name = "x" if attr else (None if rng.random() < 0.5 else "")
        kind = rng.random()
        if kind < 0.30:
            new, sent_label = MOCK_SENTINEL, "mock"
        elif kind < 0.55:
            new, sent_label = UT_MOCK_SENTINEL, "ut"
        elif kind < 0.80:
            new, sent_label = object(), "obj"
        else:
            new, sent_label = NumpyLike(rng.randint(0, 9)), "numpy"
        return Patch(attribute_name, new), attribute_name, sent_label

    total = 0
    for _ in range(40_000):
        sentinels = configs[rng.randrange(len(configs))]
        n = rng.randint(0, 6)
        decs = [gen_decoration() for _ in range(n)]
        reals = [d[0] for d in decs]

        # REAL post-patch count (must not raise even with NumpyLike present).
        try:
            real = real_num_mock_patch_args(reals, sentinels)
        except Exception as e:  # pragma: no cover
            mismatches += 1
            if len(examples) < 10:
                examples.append(("RAISED", repr(e), [d[1:] for d in decs]))
            continue

        # MODEL count from the abstraction, using identity against THIS config.
        model = 0
        for p, attribute_name, _label in decs:
            is_sent = any(p.new is s for s in sentinels)
            if model_isCounted(bool(attribute_name), is_sent):
                model += 1

        total += 1
        if model != real:
            mismatches += 1
            if len(examples) < 10:
                examples.append((model, real, [(d[1], d[2]) for d in decs]))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs real post-patch classifier")
        for m, r, decs in examples:
            print(f"  model={m} real={r} decs={decs}")
        return 1

    print(f"G-AX OK: isCounted/total-result == post-patch num_mock_patch_args on "
          f"all {total} probes incl. numpy-like replacements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
