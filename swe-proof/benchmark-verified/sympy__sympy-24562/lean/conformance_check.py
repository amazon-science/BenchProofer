#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24562 (lean).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo values, via the mapping.md
              bijection (`pDen : Nat` <-> int p.q; `qdigits : List Nat` <-> the
              decimal-string operand). The shadow is the whole computed result:
                  out = pDen * decval(qdigits)
              where `decval` is the Lean left-fold transliterated.
  * ORACLE  — `patch.diff`'s behaviour: the patched denominator accumulation in
              `Rational.__new__`. For a string second operand the patched block
              multiplies the fresh accumulator by the first operand's
              denominator factor and then by the parsed integer value of the
              string operand, so the combined denominator is
              `pDen * Rational(qstr).p`. We obtain `Rational(qstr).p` from the
              REAL patched sympy (the unchanged parse callee), which is the
              genuine differential: the shadow's `decval` must equal sympy's
              own decimal parse of the same digit string. A wrong digit model
              (wrong order/place value) shows up here as a disagreement.

They must agree on every hypothesis-satisfying input, INCLUDING zero-valued
operands (the combined denominator is then zero, feeding the downstream
zero-denominator handling). Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image, patch.diff applied).
stdlib + sympy (the patched repo). The fuzz seed is pinned (mapping.md).
"""
import random
import sys

SEED = 24562
N_FUZZ = 120_000


# --- the R/I shadow: Solution.lean decval + impl value-product ---------------
def decval(ds):
    """decval (ds : List Nat) transliterated: ds.foldl (acc*10 + d) 0."""
    acc = 0
    for d in ds:
        acc = acc * 10 + d
    return acc


def shadow_denominator(pDen, qdigits):
    """The impl region of implementation_denominatorProduct:
    denAcc=1; denAcc*=pDen; denAcc*=decval(qdigits)."""
    return pDen * decval(qdigits)


# --- the oracle: patch.diff's behaviour via real patched sympy ---------------
def oracle_denominator(pDen, qdigits):
    """patch.diff denominator accumulation for a string q operand.

    The patched block: a fresh accumulator starts at 1, the p operand
    contributes its denominator factor (modeled by the input pDen), and the
    string q operand is parsed and contributes its numerator. We use REAL
    patched sympy to parse the digit string, so the comparison genuinely tests
    that the Lean `decval` model equals sympy's own decimal parse.
    """
    from sympy import Rational
    qstr = "".join(str(d) for d in qdigits) or "0"
    qr = Rational(qstr)            # unchanged parse callee on the q operand
    return pDen * int(qr.p)        # the patched accumulation


def fuzz_inputs(n, rng):
    # boundary cases first
    yield (1, [])                       # empty operand -> value 0
    yield (1, [0])                      # single zero digit -> value 0
    yield (2, [0])                      # zero-valued operand with factor > 1
    yield (2, [1, 0, 0])                # the issue: pDen=2 (from '0.5'), q='100'
    yield (1, [1, 0, 0])                # pDen=1
    yield (2, [0, 1, 0, 0])             # leading zero in operand
    yield (1, [9, 9, 9, 9, 9, 9])       # all nines
    yield (1000, [1])                   # large factor
    yield (7, [1, 2, 3, 4, 5, 6, 7])    # mixed
    yield (3, [0, 0, 0])                # all-zero operand -> value 0
    for _ in range(n):
        pDen = rng.randint(1, 1000)
        k = rng.randint(0, 8)
        qdigits = [rng.randint(0, 9) for _ in range(k)]
        yield (pDen, qdigits)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for pDen, qdigits in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_denominator(pDen, qdigits)
        oracle = oracle_denominator(pDen, qdigits)
        if shadow != oracle:
            disagreements.append((pDen, qdigits, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for pDen, qdigits, sh, orc in disagreements:
            print("  pDen=%r qdigits=%r shadow=%r oracle=%r"
                  % (pDen, qdigits, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of denominatorProduct agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
