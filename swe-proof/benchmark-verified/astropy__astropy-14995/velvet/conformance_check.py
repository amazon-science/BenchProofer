#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14995 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`resolveMask`)
              transliterated to Python over the *real* repo types, via the
              mapping.md bijection (`Option (List Int)` ↔ a mask that is `None`
              or an integer ``numpy`` array; `combine` ↔ the caller's
              ``handle_mask`` callable; `handleMaskNone` ↔ ``handle_mask is
              None``; `operandPresent` ↔ ``operand is not None``). There are NO
              A-tagged callees in this bundle, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              ``NDArithmeticMixin._arithmetic_mask`` applied at base_commit (the
              real correctness oracle, G-RESOLVE). The harness applies patch.diff
              before this runs; we call the real (patched) method via duck-typed
              operand stand-ins — it touches only ``self.mask``, ``operand``,
              ``operand.mask`` and ``handle_mask``.

They must agree on every Requires-satisfying input (the spec's domain is
``operandPresent = true``: a real second operand whose ``.mask`` is ``None`` or
an array). Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + numpy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import numpy as np

SEED = 14995
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean resolveMask, transliterated --------------
def shadow_resolve(self_mask, operand_mask, handle_mask_none, combine):
    """resolveMask's `do` block, transliterated to the real mask carriers.

    `Option (List Int)` ↔ (None | int-array); `none` ↔ None; `combine` is the
    caller-supplied combiner; `handleMaskNone` ↔ no combiner supplied. The
    second operand is always present (require operandPresent = true), so there
    is no `operand is None` arm here — that is exactly the discriminator the
    pre-patch got wrong."""
    if (self_mask is None and operand_mask is None) or handle_mask_none:
        return None
    elif self_mask is None:
        return operand_mask
    elif operand_mask is None:
        return self_mask
    else:
        return combine(self_mask, operand_mask)


# --- the oracle: patch.diff's real behaviour --------------------------------
class _Stub:
    """A minimal stand-in for an NDData operand: `_arithmetic_mask` reads only
    `self.mask` / `operand.mask`."""

    def __init__(self, mask):
        self.mask = mask


def oracle_resolve(self_mask, operand_mask, handle_mask_none, combine):
    """patch.diff's behaviour: the patched _arithmetic_mask. Resolved from the
    repo at base_commit with the gold patch applied (the harness applies
    patch.diff before this runs)."""
    from astropy.nddata.mixins.ndarithmetic import NDArithmeticMixin

    self_obj = _Stub(self_mask)
    operand_obj = _Stub(operand_mask)            # operandPresent = true
    handle_mask = None if handle_mask_none else combine
    # operation is ignored by _arithmetic_mask; pass a harmless callable.
    return NDArithmeticMixin._arithmetic_mask(
        self_obj, np.multiply, operand_obj, handle_mask
    )


# --- value bridge / comparison ----------------------------------------------
def masks_equal(a, b):
    if a is None or b is None:
        return a is None and b is None
    return np.array_equal(np.asarray(a), np.asarray(b))


def fuzz_masks(rng):
    """Yield candidate mask values: None, plus integer bitmask arrays of a few
    shapes/value ranges (bitmasks as in the issue, and boolean-as-int masks)."""
    yield None
    # the exact issue arrays
    yield np.array([[0, 1, 64], [8, 0, 1], [2, 1, 0]])
    yield np.array([[64, 1, 0], [2, 1, 0], [8, 0, 2]])
    # random integer bitmasks
    shape = rng.choice([(1,), (3,), (2, 2), (3, 3)])
    yield rng.randint(0, 256, size=shape)
    # boolean masks stored as ints
    yield rng.randint(0, 2, size=shape)
    # zeros / all-ones boundary
    yield np.zeros((3,), dtype=int)
    yield np.full((3,), 255, dtype=int)


COMBINERS = [np.bitwise_or, np.logical_or, np.bitwise_and, np.add]


def main():
    rng = random.Random(SEED)
    nprng = np.random.RandomState(SEED)

    # numpy's randint via a RandomState bound to `rng`-driven choices.
    def gen_masks():
        cands = [None,
                 np.array([[0, 1, 64], [8, 0, 1], [2, 1, 0]]),
                 np.array([[64, 1, 0], [2, 1, 0], [8, 0, 2]]),
                 np.zeros((3,), dtype=int),
                 np.full((3,), 255, dtype=int)]
        shape = [(1,), (3,), (2, 2), (3, 3)][nprng.randint(0, 4)]
        cands.append(nprng.randint(0, 256, size=shape))
        cands.append(nprng.randint(0, 2, size=shape))
        return cands

    disagreements = []
    count = 0

    def check(self_mask, operand_mask, handle_mask_none, combine):
        nonlocal count
        count += 1
        # operand masks of different shapes can't be combined; only feed the
        # combiner two masks of equal shape (the spec's combine is total only on
        # comparable carriers — mapping.md §2). Mismatched shapes are out of the
        # tested domain, exactly as in the real binary-op path.
        if (not handle_mask_none and self_mask is not None
                and operand_mask is not None
                and np.asarray(self_mask).shape != np.asarray(operand_mask).shape):
            count -= 1
            return
        try:
            sh = shadow_resolve(self_mask, operand_mask, handle_mask_none, combine)
        except Exception as e:                                   # noqa: BLE001
            sh = ("EXC", type(e).__name__)
        try:
            orc = oracle_resolve(self_mask, operand_mask, handle_mask_none, combine)
        except Exception as e:                                   # noqa: BLE001
            orc = ("EXC", type(e).__name__)
        if isinstance(sh, tuple) or isinstance(orc, tuple):
            ok = (isinstance(sh, tuple) and isinstance(orc, tuple) and sh == orc)
        else:
            ok = masks_equal(sh, orc)
        if not ok and len(disagreements) < 5:
            disagreements.append((repr(self_mask), repr(operand_mask),
                                  handle_mask_none, getattr(combine, "__name__", combine),
                                  repr(sh), repr(orc)))

    # boundary matrix first (the issue's five scenarios + handle_mask=None)
    issue_mask = np.array([[0, 1, 64], [8, 0, 1], [2, 1, 0]])
    boundary = [
        (None, None, False, np.bitwise_or),       # no mask * no mask -> None
        (issue_mask, None, False, np.bitwise_or),  # mask * no mask -> mask
        (None, issue_mask, False, np.bitwise_or),  # no mask * mask -> mask
        (issue_mask, issue_mask, False, np.bitwise_or),  # mask * mask -> combine
        (issue_mask, issue_mask, True, np.bitwise_or),   # handle_mask=None -> None
        (None, None, True, np.bitwise_or),
    ]
    for sm, om, hmn, cb in boundary:
        check(sm, om, hmn, cb)

    # randomized fuzz
    for _ in range(N_FUZZ):
        masks = gen_masks()
        sm = masks[nprng.randint(0, len(masks))]
        om = masks[nprng.randint(0, len(masks))]
        hmn = bool(nprng.randint(0, 2)) and nprng.rand() < 0.2
        cb = COMBINERS[nprng.randint(0, len(COMBINERS))]
        check(sm, om, hmn, cb)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sm, om, hmn, cb, sh, orc in disagreements:
            print("  self=%s operand=%s handle_mask_none=%s combine=%s "
                  "shadow=%s oracle=%s" % (sm, om, hmn, cb, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveMask agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
