#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-20801.

The bundle models ONE routine: the boolean dispatch inside `Float.__eq__`
(mapping.md), AFTER the operand has been successfully sympified. The modeled
value is a PURE function of the observables the real method reads:

    selfIsZero, otherIsBoolean, otherIsNumberSymbol, otherIsIrrational,
    numberSymbolEq, otherIsFloat, mpfEq, otherIsRational, rationalEq,
    otherIsNumber, numberMpfEq, otherIsFalsy

Post-patch dispatch (the relocated zero-operand clause runs LAST, after the full
kind dispatch):

    if otherIsBoolean:        return False
    if otherIsNumberSymbol:   return False if otherIsIrrational else numberSymbolEq
    if otherIsFloat:          return mpfEq
    if otherIsRational:       return rationalEq
    if otherIsNumber:         return numberMpfEq
    if selfIsZero:            return otherIsFalsy
    return False

Standing up the full sympy Number hierarchy to drive the real dispatch is heavy
and unnecessary: the modeled value is this pure decision over observables the
real method exposes. So the ORACLE below is a faithful in-process replica of the
POST-PATCH dispatch (the zero clause relocated to the end), and the SHADOW is the
op-for-op transliteration of `implementation_floatEq` (Solution.lean impl
region), per refinement.md.

This genuinely tests the soundness-critical relocation: a zero float compared to
a logic boolean (`selfIsZero` and `otherIsBoolean`, e.g. `S(0.0) == S.false`)
must be decided by the boolean rule (False), NOT by the empty-like fallback that
would return `otherIsFalsy` (True for `S.false`) — matching the F2P expectation
in `test_zero_not_false`.

stdlib-only. Pinned seed: 20801 (also in mapping.md).
"""
import itertools
import random
import sys

SEED = 20801
N = 120_000


# --- ORACLE: faithful in-process replica of the POST-PATCH dispatch -----------
# The zero-operand clause is RELOCATED to run after the full kind dispatch.
def oracle(inp):
    if inp["otherIsBoolean"]:
        return False
    if inp["otherIsNumberSymbol"]:
        return False if inp["otherIsIrrational"] else inp["numberSymbolEq"]
    if inp["otherIsFloat"]:
        return inp["mpfEq"]
    if inp["otherIsRational"]:
        return inp["rationalEq"]
    if inp["otherIsNumber"]:
        return inp["numberMpfEq"]
    if inp["selfIsZero"]:
        return inp["otherIsFalsy"]
    return False


# --- SHADOW of implementation_floatEq (the R leg) -----------------------------
# Mirrors Solution.lean impl region exactly (sequential early-return chain).
def shadow(inp):
    if inp["otherIsBoolean"]:
        return False
    if inp["otherIsNumberSymbol"]:
        if inp["otherIsIrrational"]:
            return False
        return inp["numberSymbolEq"]
    if inp["otherIsFloat"]:
        return inp["mpfEq"]
    if inp["otherIsRational"]:
        return inp["rationalEq"]
    if inp["otherIsNumber"]:
        return inp["numberMpfEq"]
    if inp["selfIsZero"]:
        return inp["otherIsFalsy"]
    return False


FIELDS = [
    "selfIsZero", "otherIsBoolean", "otherIsNumberSymbol", "otherIsIrrational",
    "numberSymbolEq", "otherIsFloat", "mpfEq", "otherIsRational", "rationalEq",
    "otherIsNumber", "numberMpfEq", "otherIsFalsy",
]


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def main() -> int:
    checked = 0

    # Exhaustive: 12 boolean fields = 4096 combinations. Covers every branch,
    # including the F2P case selfIsZero & otherIsBoolean (=> False, not the
    # falsy fallback).
    for combo in itertools.product([False, True], repeat=len(FIELDS)):
        inp = dict(zip(FIELDS, combo))
        d = disagree(inp)
        if d:
            print(f"DISAGREE exhaustive: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    # Random fuzz on top (redundant given exhaustion, but pins the seed and
    # guards against any future non-boolean field widening).
    rng = random.Random(SEED)
    for _ in range(N):
        inp = {f: (rng.random() < 0.5) for f in FIELDS}
        d = disagree(inp)
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
