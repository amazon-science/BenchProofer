#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-14995.

The bundle models ONE routine: `NDArithmeticMixin._arithmetic_mask` (mapping.md),
the mask-propagation decision of an arithmetic operation between two operands.
The modeled value is a PURE function of the observables the real function reads:

    selfMask     : Optional[mask]   (self.mask;     None == no mask)
    operandMask  : Optional[mask]   (operand.mask;  None == no mask)
    handleMask   : Optional[callable] (the handle_mask param; None == not given)

in the two-operand domain the routine is actually called from (operand present),
where the `operand is None` branch is dead.

Post-patch rule (the gold edit changes `elif operand is None:` to
`elif operand.mask is None:`, so a self-only mask is copied over instead of being
sent to the merge):

    if handleMask is None:                       result = None
    elif selfMask is None and operandMask is None: result = None
    elif selfMask is None:                       result = operandMask        (copy operand)
    elif operandMask is None:                    result = selfMask           (copy self)
    else:                                        result = handleMask(selfMask, operandMask)

The result is one of: ('none',) no mask; ('mask', grid) a mask; ('error',) the
TypeError crash. Standing up numpy / the full NDData machinery is heavy and
unnecessary: the modeled value is this pure decision over the observables the
real function exposes. So the ORACLE is a faithful in-process replica of the
POST-PATCH decision, and the SHADOW is the op-for-op transliteration of
`implementation_maskPropagation` (Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical clause: when `self` has a mask and
`operand` has none, the result must COPY self's mask (not crash and not merge),
matching the F2P `nref_masked.multiply(1.0)` / `nref_masked.multiply(nref_nomask)`
expectations.

stdlib-only. Pinned seed: 14995 (also in mapping.md).
"""
import random
import sys

SEED = 14995
N = 120_000


# `handle_mask=np.bitwise_or`: element-wise bitwise-or of two equal-length grids.
def bitwise_or(a, b):
    return [x | y for x, y in zip(a, b)]


# --- ORACLE: faithful in-process replica of the POST-PATCH decision -----------
# (`elif operand.mask is None: return deepcopy(self.mask)`)
def oracle(selfMask, operandMask, handleMask):
    if handleMask is None:
        return ("none",)
    if selfMask is None and operandMask is None:
        return ("none",)
    if selfMask is None:
        return ("mask", list(operandMask))          # deepcopy(operand.mask)
    if operandMask is None:
        return ("mask", list(selfMask))             # deepcopy(self.mask)  -- the FIX
    return ("mask", handleMask(selfMask, operandMask))


# --- SHADOW of implementation_maskPropagation (the R leg) ---------------------
# Mirrors Solution.lean impl region exactly (the nested match on handleMask then
# (selfMask, operandMask)).
def shadow(selfMask, operandMask, handleMask):
    if handleMask is None:
        return ("none",)
    # match (selfMask, operandMask)
    if selfMask is None and operandMask is None:
        return ("none",)
    elif selfMask is None:                          # none, some om
        return ("mask", list(operandMask))
    elif operandMask is None:                       # some sm, none
        return ("mask", list(selfMask))
    else:                                           # some sm, some om
        return ("mask", handleMask(selfMask, operandMask))


def disagree(selfMask, operandMask, handleMask):
    got = oracle(selfMask, operandMask, handleMask)
    want = shadow(selfMask, operandMask, handleMask)
    if got != want:
        return ((selfMask, operandMask, handleMask is not None), got, want)
    return None


def _edge_cases():
    m1 = [0, 1, 64, 8, 0, 1, 2, 1, 0]
    m2 = [64, 1, 0, 2, 1, 0, 8, 0, 2]
    cases = [
        # F2P: no mask * no mask, with combine -> no mask
        (None, None, bitwise_or),
        # F2P: masked * no mask (self has mask, operand none) -> copy self  (was crash)
        (m1, None, bitwise_or),
        # F2P: masked * masked -> bitwise_or
        (m1, m2, bitwise_or),
        (m1, m1, bitwise_or),
        # no mask * masked -> copy operand
        (None, m2, bitwise_or),
        # handle_mask is None -> no mask, regardless of masks present
        (m1, m2, None),
        (m1, None, None),
        (None, None, None),
        # boolean masks (0/1) are a special case of bitmasks
        ([1, 0, 0, 1], None, bitwise_or),
        ([1, 0, 0, 1], [0, 1, 1, 0], bitwise_or),
    ]
    return cases


def _rand_grid(rng, n):
    return [rng.choice([0, 1, 2, 8, 64, 255]) for _ in range(n)]


def main() -> int:
    checked = 0
    for sm, om, hm in _edge_cases():
        d = disagree(sm, om, hm)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.randint(0, 6)
        sm = _rand_grid(rng, n) if rng.random() < 0.6 else None
        om = _rand_grid(rng, n) if rng.random() < 0.6 else None
        hm = bitwise_or if rng.random() < 0.7 else None
        d = disagree(sm, om, hm)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
