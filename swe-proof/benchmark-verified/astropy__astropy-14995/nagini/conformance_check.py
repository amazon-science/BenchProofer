#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14995 (nagini).

SHADOW: the impl region of model.py (result_mask + the copy_seq helper),
copied verbatim below with the contract calls (Requires/Ensures/Invariant/
Assert) stripped. `Operand` / `MaskResult` become plain data carriers. The
one @ContractOnly callee used by the impl, `apply_combiner`, is realized by
calling the REAL combiner callable it axiomatizes per mapping.md section 3.1:
the `handle_mask` argument, i.e. `numpy.bitwise_or` (the value the issue and
the FAIL_TO_PASS test supply). No transliteration: the model IS Python.

ORACLE: the REAL patched repo method the model models per mapping.md —
`astropy.nddata.mixins.ndarithmetic.NDArithmeticMixin._arithmetic_mask`,
invoked on real `NDDataRef` operands (NDDataRef mixes in NDArithmeticMixin).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  self_has_mask / self_mask   <-> self.mask is None / self.mask (1-D int array)
  Operand.has_mask / .mask    <-> operand.mask is None / operand.mask
  handle_mask_present         <-> handle_mask is None vs a callable
                                  (np.bitwise_or when present)
  MaskResult.present / .data  <-> the Optional return: None vs a mask array
Masks are flat List[int] bitmask vectors in the model; they bridge to 1-D
int64 ndarrays. The equal-length Requires (co-shaped operands) is enforced
by generation. The operand object is always present in the modelled domain
(mapping.md section 2.1), so only wrapped, possibly flag-less operands are
generated.

Input domain: all 8 combinations of (self_has_mask, operand.has_mask,
handle_mask_present) crossed with boundary mask contents (empty, singleton,
bitmask rows, all-zero, max-byte values) plus randomized fuzz over lengths
0..16 and flag values 0..255. Every generated input satisfies the model's
Requires.

>= 1e5 Requires-satisfying inputs: 8 x boundary pairs + 13000 x 8 fuzz cases.
Pinned fuzz seed: 14995.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 14995
N_FUZZ_ROUNDS = 13_000


# --- plain carriers for the model's small classes -----------------------------

class Operand:
    def __init__(self, has_mask, mask):
        self.has_mask = has_mask
        self.mask = mask


class MaskResult:
    def __init__(self, present, data):
        self.present = present
        self.data = data


# --- @ContractOnly callee: realized by the REAL combiner callable -------------

def apply_combiner(a, b):
    """The materializing combiner call. model.py axiomatizes it opaquely; the
    real callee it stands for (mapping.md section 3.1) is the `handle_mask`
    callable, `numpy.bitwise_or`, applied element-wise to the two equal-length
    flag arrays."""
    out = np.bitwise_or(np.array(a, dtype=np.int64),
                        np.array(b, dtype=np.int64))
    return [int(v) for v in out.tolist()]


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def result_mask(self_has_mask, self_mask, operand, handle_mask_present):
    empty = []  # type: list
    if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
        return MaskResult(False, empty)
    elif not self_has_mask:
        c = copy_seq(operand.mask)
        return MaskResult(True, c)
    elif not operand.has_mask:
        c = copy_seq(self_mask)
        return MaskResult(True, c)
    else:
        c = apply_combiner(self_mask, operand.mask)
        return MaskResult(True, c)


def copy_seq(xs):
    out = []  # type: list
    i = 0
    while i < len(xs):
        out.append(xs[i])
        i = i + 1
    return out


# --- oracle invocation on real repo objects ------------------------------------

def real_decision(NDDataRef, self_has_mask, self_mask, op_has_mask, op_mask,
                  handle_mask_present):
    n = len(self_mask)
    data = np.zeros(n, dtype=np.float64)
    self_ref = NDDataRef(
        data, mask=np.array(self_mask, dtype=np.int64) if self_has_mask else None)
    op_ref = NDDataRef(
        np.zeros(len(op_mask), dtype=np.float64),
        mask=np.array(op_mask, dtype=np.int64) if op_has_mask else None)
    handle_mask = np.bitwise_or if handle_mask_present else None
    return self_ref._arithmetic_mask(np.add, op_ref, handle_mask)


def check_case(NDDataRef, self_has_mask, self_mask, op_has_mask, op_mask,
               handle_mask_present):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    assert len(self_mask) == len(op_mask)  # Requires: co-shaped flag arrays

    shadow = result_mask(self_has_mask, list(self_mask),
                         Operand(op_has_mask, list(op_mask)),
                         handle_mask_present)
    real = real_decision(NDDataRef, self_has_mask, self_mask,
                         op_has_mask, op_mask, handle_mask_present)

    inp = ("self_has_mask=%r self_mask=%r op_has_mask=%r op_mask=%r "
           "handle_mask_present=%r"
           % (self_has_mask, self_mask, op_has_mask, op_mask,
              handle_mask_present))
    if real is None:
        if shadow.present:
            return ("DISAGREEMENT\n  input: %s\n  shadow=present %r\n  real=None"
                    % (inp, shadow.data))
        return None
    real_list = [int(v) for v in np.asarray(real).ravel().tolist()]
    if not shadow.present:
        return ("DISAGREEMENT\n  input: %s\n  shadow=absent\n  real=%r"
                % (inp, real_list))
    if shadow.data != real_list:
        return ("DISAGREEMENT\n  input: %s\n  shadow=%r\n  real=%r"
                % (inp, shadow.data, real_list))
    return None


BOOL_COMBOS = [(a, b, c)
               for a in (False, True)
               for b in (False, True)
               for c in (False, True)]


def boundary_mask_pairs():
    return [
        ([], []),
        ([0], [0]),
        ([1], [0]),
        ([0], [1]),
        ([64], [64]),
        ([0, 1, 64], [64, 1, 0]),
        ([8, 0, 1], [2, 1, 0]),
        ([0, 1, 0, 1, 0, 1, 0, 1, 0], [0, 1, 64, 8, 0, 1, 2, 1, 0]),
        ([255, 128, 7], [1, 2, 248]),
        ([0, 0, 0], [0, 0, 0]),
    ]


def main():
    from astropy.nddata import NDDataRef  # real patched repo class (mixin host)

    checked = 0
    for sm, om in boundary_mask_pairs():
        for shm, ohm, hmp in BOOL_COMBOS:
            err = check_case(NDDataRef, shm, sm, ohm, om, hmp)
            if err:
                print(err)
                return 1
            checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ_ROUNDS):
        n = rng.randint(0, 16)
        sm = [rng.randint(0, 255) for _ in range(n)]
        om = [rng.randint(0, 255) for _ in range(n)]
        for shm, ohm, hmp in BOOL_COMBOS:
            err = check_case(NDDataRef, shm, sm, ohm, om, hmp)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real _arithmetic_mask on %d inputs "
          "(%d boundary + %d fuzz cases, seed %d)."
          % (checked, len(boundary_mask_pairs()) * len(BOOL_COMBOS),
             N_FUZZ_ROUNDS * len(BOOL_COMBOS), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "apply_combiner calls the real combiner)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
