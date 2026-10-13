#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-17655 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helper `scaled`
copies over as a plain function; PSeq is realized as an immutable tuple shim
(take/drop/concat/len/index are the only operations used) and ToSeq lifts a
plain list into it. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo functions the model models per mapping.md —
`sympy.geometry.point.Point.__mul__` (right scalar multiplication, bound to
the model's `mul_right`) and `Point.__rmul__` (left scalar multiplication,
bound to `mul_left`). The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched package importable.

Type bridge (mapping.md section 2): a point maps to the List[int] of its
coordinate values (`coords[k]` <-> `point.args[k]`), the factor maps to a
plain int. The shadow returns a List[int]; the oracle returns a Point whose
`.args` are coordinate expressions — with integer coordinates and an integer
factor every resulting coordinate is an exact Integer, so the comparison
lifts the oracle coordinates through int() and is exact.

Input domain: the model's Requires only demands read permission on the
coordinate list, so every (coords, factor) pair over ints satisfies it.
The carrier bridge restricts generation to the real constructor's operating
domain: a point needs at least 2 coordinates, so dimensions are drawn from
2..6 (the same domain axiom_check.py exercises). Magnitudes mix small ints
with occasional large ones (exact integer arithmetic on both sides).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz inputs.
Pinned fuzz seed: 17655.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 17655
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the model uses -------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- pure helper from model.py, contracts stripped -----------------------------

def scaled(s, factor):
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(s[0] * factor) + scaled(s.drop(1), factor)


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def mul_right(point, factor):
    result = []  # type: list
    i = len(point)
    while i > 0:
        c = point[i - 1]
        result = [c * factor] + result
        i = i - 1
    return result


def mul_left(factor, point):
    return mul_right(point, factor)


# --- oracle: the real patched repo operations -----------------------------------

def check_one(Point, coords, factor):
    """Run shadow and oracle on one (coords, factor) input; return an error
    string on disagreement, else None."""
    shadow_right = mul_right(list(coords), factor)
    shadow_left = mul_left(factor, list(coords))

    # internal consistency with the pure helper (the spec's fold)
    fold = scaled(ToSeq(coords), factor)
    assert len(fold) == len(shadow_right)
    assert all(fold[k] == shadow_right[k] for k in range(len(fold)))

    p = Point(*coords)
    real_right = p * factor
    real_left = factor * p
    rr = [int(x) for x in real_right.args]
    rl = [int(x) for x in real_left.args]

    if shadow_right != rr:
        return ("DISAGREEMENT (right)\n  input: coords=%r factor=%r\n"
                "  shadow=%r\n  real=%r" % (coords, factor, shadow_right, rr))
    if shadow_left != rl:
        return ("DISAGREEMENT (left)\n  input: coords=%r factor=%r\n"
                "  shadow=%r\n  real=%r" % (coords, factor, shadow_left, rl))
    return None


def boundary_inputs():
    return [
        ([1, 1], 5),            # the 2D observable witness
        ([1, 1, 1], 5),         # the 3D observable witness
        ([0, 0], 5),
        ([0, 0, 0], 0),
        ([1, 1], 0),            # zero factor
        ([1, 1], 1),            # unit factor
        ([1, 1], -1),
        ([2, 3], 5),
        ([1, 2, 3], 4),
        ([0, 1], 7),
        ([3, 0, 4], 2),
        ([1, 1], -3),           # negative factor
        ([-2, 5], 6),           # negative coordinate
        ([-7, -11, -13], -17),  # all negative
        ([10, 20, 30, 40], 3),  # higher dimension
        ([1, 2, 3, 4, 5, 6], 9),
        ([10 ** 9, -(10 ** 9)], 10 ** 6),  # large magnitudes (exact ints)
        ([1, 1], 10 ** 12),
    ]


def fuzz_input(rng):
    dim = rng.randint(2, 6)
    if rng.random() < 0.05:
        coords = [rng.randint(-10 ** 9, 10 ** 9) for _ in range(dim)]
        factor = rng.randint(-10 ** 9, 10 ** 9)
    else:
        coords = [rng.randint(-100, 100) for _ in range(dim)]
        factor = rng.randint(-100, 100)
    return coords, factor


def main():
    from sympy.geometry import Point  # REAL patched class

    checked = 0
    n_boundary = 0
    for coords, factor in boundary_inputs():
        err = check_one(Point, coords, factor)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        coords, factor = fuzz_input(rng)
        err = check_one(Point, coords, factor)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real left/right scaling on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
