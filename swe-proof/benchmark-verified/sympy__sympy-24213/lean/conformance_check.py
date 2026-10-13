#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-24213.

The bundle models ONE routine: the `Add` branch of
`_collect_factor_and_dimension` (mapping.md). Its observable outcome is, given
the head addend's `(factor, dim)` and the remaining addends' `(factor, dim)`
pairs (each already produced by the unchanged recursive collection), either
- a ValueError (some addend's dimension is incompatible with the head's), or
- the tuple `(sum_of_factors, head_dim)`.

The POST-PATCH compatibility test is `equivalent_dims(dim, addend_dim)` — equal
*dimensional-dependency maps* — NOT structural `Dimension` equality. So the
ORACLE below is a faithful in-process replica of the POST-PATCH Add branch using
the REAL sympy `DimensionSystem.equivalent_dims` (a `Dimension` carries a surface
name; equivalence is decided on the base-dimension power map). The SHADOW is the
op-for-op transliteration of `implementation_factorAndDimensionOfSum`
(Solution.lean impl region): branch on the canonical dependency map (`Dim.deps`),
sum the factors, carry the head dimension through (per refinement.md).

The soundness-critical category is two addends whose surface dimensions DIFFER
but whose dependency maps COINCIDE (e.g. velocity vs acceleration*time): the
post-patch routine accepts them; an impl comparing surface identity would
wrongly reject. The fuzzer deliberately mixes equivalent-but-differently-written
dimensions into the addend lists.

stdlib + sympy (available in-container). Pinned seed: 24213 (also in mapping.md).
"""
import random
import sys
from fractions import Fraction

from sympy import Symbol, sympify
from sympy.physics.units.dimensions import Dimension, DimensionSystem


# --- a small dimension system over base dims L, T, M --------------------------
# Build derived dims so the SAME base-dim map is reachable from DIFFERENT surface
# names (the discriminating category).
L = Dimension("length")
T = Dimension("time")
M = Dimension("mass")
velocity = Dimension("velocity")
acceleration = Dimension("acceleration")
force = Dimension("force")

DS = DimensionSystem(
    (L, T, M),
    (velocity, acceleration, force),
    {
        velocity: {L: 1, T: -1},
        acceleration: {L: 1, T: -2},
        force: {M: 1, L: 1, T: -2},
    },
)

# A catalog of dimensions to draw from; some pairs are deps-equivalent though
# their surface names differ. The value is the sympy Dimension object.
DIM_CATALOG = {
    "length": L,
    "time": T,
    "mass": M,
    "velocity": velocity,
    "acceleration": acceleration,
    "force": force,
    # composite surface forms that reduce to the same base map as a named dim:
    "length/time": Dimension(L.name / T.name),                 # == velocity
    "acceleration*time": Dimension(acceleration.name * T.name),  # == velocity
    "mass*acceleration": Dimension(M.name * acceleration.name),  # == force
    "length/time**2": Dimension(L.name / T.name ** 2),           # == acceleration
    "dimensionless": Dimension(1),
}


def _deps_map(dim):
    """Canonical dependency map of `dim` as a dict {str(base): int(exp)} with no
    zero entries — exactly what `equivalent_dims` compares (it diffs the dicts
    returned by get_dimensional_dependencies)."""
    raw = DS.get_dimensional_dependencies(dim)
    return {str(k): int(v) for k, v in raw.items() if int(v) != 0}


def _deps_assoc(dim):
    """The Lean `Dim.deps` carrier: the dependency map as a sorted assoc list."""
    return sorted(_deps_map(dim).items())


# --- ORACLE: faithful in-process replica of the POST-PATCH Add branch ---------
# post-patch:
#   factor, dim = head
#   for (addend_factor, addend_dim) in addends:
#       if not equivalent_dims(dim, addend_dim): raise ValueError
#       factor += addend_factor
#   return factor, dim
def oracle(head, addends):
    head_factor, head_dim = head
    factor = head_factor
    for addend_factor, addend_dim in addends:
        if not DS.equivalent_dims(head_dim, addend_dim):
            return ("error",)
        factor = factor + addend_factor
    return ("ok", factor, _deps_assoc(head_dim))


# --- SHADOW of implementation_factorAndDimensionOfSum (the R/I legs) ----------
# Mirrors Solution.lean impl region exactly:
#   let dim := head.2; let mut factor := head.1
#   for a in addends do
#     if dim.deps != a.2.deps then return none
#     factor := factor + a.1
#   return some (factor, dim)
# `Dim.deps` is the canonical sorted assoc list of the dependency map; equality
# of these lists is exactly dict equality, i.e. equivalent_dims.
def shadow(head, addends):
    head_factor, head_dim = head
    dim_deps = _deps_assoc(head_dim)
    factor = head_factor
    for addend_factor, addend_dim in addends:
        if dim_deps != _deps_assoc(addend_dim):
            return ("error",)
        factor = factor + addend_factor
    return ("ok", factor, dim_deps)


def disagree(head, addends):
    got = oracle(head, addends)
    want = shadow(head, addends)
    if got != want:
        return (head, addends, got, want)
    return None


def _mk(name, factor):
    return (Fraction(factor), DIM_CATALOG[name])


def _enumerate_edge():
    cases = []
    # empty addend list -> always ok, factor = head factor
    cases.append((_mk("velocity", 2), []))
    # the F2P scenario: acceleration*time + velocity (different names, same deps)
    cases.append((_mk("acceleration*time", Fraction(-49, 10)), [_mk("velocity", 2)]))
    cases.append((_mk("velocity", 2), [_mk("acceleration*time", Fraction(-49, 10))]))
    # length/time also equivalent to velocity
    cases.append((_mk("velocity", 1), [_mk("length/time", 3), _mk("acceleration*time", -2)]))
    # mass*acceleration equivalent to force
    cases.append((_mk("force", 1), [_mk("mass*acceleration", 5)]))
    # length/time**2 equivalent to acceleration
    cases.append((_mk("acceleration", 1), [_mk("length/time**2", 2)]))
    # genuinely incompatible -> error
    cases.append((_mk("velocity", 2), [_mk("mass", 1)]))
    cases.append((_mk("length", 1), [_mk("time", 1)]))
    # incompatible appears after a compatible one
    cases.append((_mk("velocity", 1), [_mk("length/time", 1), _mk("mass", 1)]))
    return cases


def main() -> int:
    checked = 0
    for head, addends in _enumerate_edge():
        d = disagree(head, addends)
        if d:
            print(f"DISAGREE edge: oracle={d[2]} shadow={d[3]} head={d[0]} addends={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    names = list(DIM_CATALOG.keys())
    rng = random.Random(24213)  # pinned seed (mapping.md)
    N = 120_000
    for _ in range(N):
        head = _mk(rng.choice(names), rng.randint(-20, 20))
        k = rng.randint(0, 6)
        addends = [_mk(rng.choice(names), rng.randint(-20, 20)) for _ in range(k)]
        d = disagree(head, addends)
        if d:
            print(f"DISAGREE fuzz: oracle={d[2]} shadow={d[3]} head={d[0]} addends={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
