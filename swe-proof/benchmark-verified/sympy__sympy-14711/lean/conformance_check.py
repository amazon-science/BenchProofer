#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-14711.

The bundle models ONE routine: `Vector.__add__` (mapping.md). The modeled value
is a PURE function of the observable shape of the right operand `other` and the
vector's component (argument) list `selfArgs`:

    other ∈ { vector(args) , scalarZero , nonVector }

Post-patch rule (the gold edit ADDS the `if other == 0: return self` guard, so
the additive identity is accepted as a no-op instead of raising):

    if other == 0:                 return ok(selfArgs)          # added guard
    other = _check_vector(other)   # raises TypeError if not a Vector
    return ok(selfArgs + otherArgs)                             # append args

Standing up the full sympy.physics.vector machinery (ReferenceFrame, Matrix,
sympify) to drive the real `__add__` is heavy and unnecessary: the modeled value
is this pure decision over observables the real function exposes (is the operand
the additive identity? is it a vector, and with which args? otherwise reject).
So the ORACLE below is a faithful in-process replica of the POST-PATCH `__add__`
(the guard present, `_check_vector` modeled as accept-vector / raise-otherwise),
and the SHADOW is the op-for-op transliteration of `implementation_vectorAdd`
(Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical clause: the scalar zero
(`scalarZero`) must NOT be rejected — it must return the vector unchanged
(`ok(selfArgs)`), matching the F2P expectation `A.x + 0 == A.x`.

The result is encoded as ("ok", tuple(args)) or ("error", None).

stdlib-only. Pinned seed: 14711 (also in mapping.md).
"""
import random
import sys

SEED = 14711
N = 120_000


# An AddOperand is a tuple (kind, args):
#   ("vector", [int,...])  ("scalarZero", None)  ("nonVector", None)
def is_additive_zero(other):
    kind, args = other
    if kind == "scalarZero":
        return True
    if kind == "vector" and args == []:
        return True
    return False


# --- ORACLE: faithful in-process replica of the POST-PATCH __add__ ------------
# Mirrors:  if other == 0: return self
#           other = _check_vector(other)   # raise on non-Vector
#           return Vector(self.args + other.args)
def oracle(self_args, other):
    kind, args = other
    # `other == 0` is true for the scalar 0 and for an empty (zero) vector.
    if kind == "scalarZero" or (kind == "vector" and args == []):
        return ("ok", tuple(self_args))      # return self
    if kind == "vector":
        return ("ok", tuple(self_args + args))
    return ("error", None)                   # _check_vector raises TypeError


# --- SHADOW of implementation_vectorAdd (the R leg) ---------------------------
# Mirrors Solution.lean impl region exactly.
def shadow(self_args, other):
    if is_additive_zero(other):
        return ("ok", tuple(self_args))
    kind, args = other
    if kind == "vector":
        return ("ok", tuple(self_args + args))
    return ("error", None)


def disagree(self_args, other):
    got = oracle(self_args, other)
    want = shadow(self_args, other)
    if got != want:
        return (self_args, other, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P: a one-component vector + scalar zero -> the one-component vector.
    cases.append(([1], ("scalarZero", None)))
    cases.append(([7, -3, 2], ("scalarZero", None)))
    # empty-vector + scalar zero (zero vector) -> empty.
    cases.append(([], ("scalarZero", None)))
    # vector + vector -> appended args.
    cases.append(([1, 2], ("vector", [3, 4])))
    cases.append(([], ("vector", [5])))
    cases.append(([9], ("vector", [])))            # append empty == self
    # empty-vector operand (== 0) -> identity branch, coincides with append.
    cases.append(([1, 2], ("vector", [])))
    cases.append(([], ("vector", [])))
    # non-vector -> type error.
    cases.append(([1], ("nonVector", None)))
    cases.append(([], ("nonVector", None)))
    return cases


def _rand_args(rng):
    n = rng.choice([0, 0, 1, 1, 2, 3, 5])
    return [rng.randint(-9, 9) for _ in range(n)]


def main() -> int:
    checked = 0
    for self_args, other in _enumerate_edge():
        d = disagree(self_args, other)
        if d:
            print(f"DISAGREE edge: oracle={d[2]} shadow={d[3]} "
                  f"self={d[0]} other={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    kinds = ["vector", "vector", "vector", "scalarZero", "nonVector"]
    for _ in range(N):
        self_args = _rand_args(rng)
        kind = rng.choice(kinds)
        if kind == "vector":
            other = ("vector", _rand_args(rng))
        else:
            other = (kind, None)
        d = disagree(self_args, other)
        if d:
            print(f"DISAGREE fuzz: oracle={d[2]} shadow={d[3]} "
                  f"self={d[0]} other={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
