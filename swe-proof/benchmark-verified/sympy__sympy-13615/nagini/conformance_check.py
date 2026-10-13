#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13615 (nagini).

SHADOW: the impl region of model.py's `complement_finite`, copied VERBATIM
below with the contract calls (Invariant/Assert) stripped.  The impl region
uses no PSeq values at runtime (ToSeq/PSeq appear only inside the stripped
contract calls), so no sequence shim is needed.  The one @ContractOnly callee,
`verdict`, calls the REAL repo membership query per the contract: it collapses
`self_set.contains(element)` to the three verdict codes exactly as the model's
axiom documents (an answer equal to True -> DEFINITELY_IN, equal to False ->
DEFINITELY_OUT, anything else -> UNDECIDED); see mapping.md section 3.1.

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 -- the finite-collection branch of `Set._complement` in
`sympy/sets/sets.py`, invoked unbound as `Set._complement(self_set,
FiniteSet(*elements))` so the check exercises exactly the patched base-class
code path.  The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched package importable.

Type bridge (mapping.md section 2): each sympy element <-> a distinct int
handle (here: its index in the FiniteSet's iteration order); the input
List[int] <-> the finite collection iterated in that order; the shadow's two
output lists (survivors, pending) <-> the two collections the real branch
assembles.  The comparison applies the UNCHANGED assembly documented in
refinement.md A7 to the shadow's buckets --
`Union(FiniteSet(*survivors), Complement(FiniteSet(*pending), self_set,
evaluate=False) if pending else S.EmptySet)` -- and requires structural
equality with the real branch's return value.  That assembly is unchanged
set-algebra outside the modeled partition, so any partition disagreement
(an element in the wrong bucket, dropped, or duplicated) changes the
assembled object and is detected; the assembly itself is exercised
identically on both sides.

Input domain: the model's Requires admits any handle list; the bijection
covers the NONEMPTY finite collections (an empty collection has no FiniteSet
counterpart -- the real function dispatches the empty case to a different,
unmodeled branch), so the diff draws 1..8-element collections from a pool of
symbols (free and assumption-carrying), integers (including removal-interval
endpoints), rationals, and compound expressions, crossed with removal sets of
every kind (closed/open/half-open/unbounded intervals, finite sets containing
numbers and symbols, S.Naturals/Integers/Reals, S.EmptySet, S.UniversalSet,
and a Union) -- covering all three verdicts and every mixed configuration.

>= 1e5 Requires-satisfying inputs: 780 boundary cases (13 removal sets x 60
hand-picked collections, including the all-undecided / all-decidable / mixed /
singleton shapes) + fuzz to a total of 100000.  Pinned fuzz seed: 136150.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib + sympy (the package under test) only.
"""
import json
import random
import sys

SEED = 136150
N_TOTAL = 100_000


# --- verdict codes from model.py ----------------------------------------------

DEFINITELY_OUT = 0
DEFINITELY_IN = 1
UNDECIDED = 2


# --- the @ContractOnly callee: calls the REAL repo membership query ------------

_ORACLE = None  # (self_set, elements): the live handle -> element bridge


def verdict(el):
    """The model's membership oracle over int handles, realized by the REAL
    repo query on the bridged element: answers equal to True/False map to
    IN(1)/OUT(0), any other answer (membership not settled) maps to
    UNDECIDED(2).  See mapping.md section 3.1."""
    self_set, elements = _ORACLE
    contains = self_set.contains(elements[el])
    if contains in [True, False]:
        return DEFINITELY_IN if contains == True else DEFINITELY_OUT  # noqa: E712
    return UNDECIDED


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def complement_finite(other):
    out = []  # type: list
    undecided = []  # type: list
    i = len(other)
    while i > 0:
        e = other[i - 1]
        v = verdict(e)
        if v == DEFINITELY_OUT:
            out = [e] + out
        elif v == UNDECIDED:
            undecided = [e] + undecided
        i = i - 1
    return out, undecided


# --- differential driver --------------------------------------------------------

def check_case(sympy_mod, self_set, elements):
    """Run shadow and oracle on one bridged input; return an error string on
    disagreement, else None."""
    global _ORACLE
    FiniteSet = sympy_mod.FiniteSet
    Union = sympy_mod.Union
    Complement = sympy_mod.Complement
    S = sympy_mod.S
    from sympy.sets.sets import Set

    fs = FiniteSet(*elements)
    ordered = list(fs)  # the collection in its iteration order (mapping.md §2)
    _ORACLE = (self_set, ordered)
    handles = list(range(len(ordered)))

    shadow_out, shadow_und = complement_finite(handles)
    out_elems = [ordered[h] for h in shadow_out]
    und_elems = [ordered[h] for h in shadow_und]

    try:
        real = Set._complement(self_set, fs)
    except Exception as exc:  # in-domain input must not raise
        return ("DISAGREEMENT (oracle raised)\n  self_set=%r\n  elements=%r"
                "\n  shadow=(out=%r, pending=%r)\n  real raised %s: %s"
                % (self_set, elements, out_elems, und_elems,
                   type(exc).__name__, exc))

    # UNCHANGED assembly of the shadow's two buckets (refinement.md A7).
    expected = Union(FiniteSet(*out_elems),
                     Complement(FiniteSet(*und_elems), self_set,
                                evaluate=False)
                     if und_elems else S.EmptySet)
    if real != expected:
        return ("DISAGREEMENT\n  self_set=%r\n  elements=%r"
                "\n  shadow buckets: out=%r pending=%r -> assembled %r"
                "\n  real=%r"
                % (self_set, elements, out_elems, und_elems, expected, real))
    return None


def main():
    import sympy
    from sympy import (FiniteSet, Interval, Union, S, Rational, Integer, oo,
                       pi, sqrt, Symbol)
    from sympy.abc import x, y, z

    p = Symbol('p', positive=True)
    q = Symbol('q', negative=True)
    k = Symbol('k', integer=True)

    # Element pool: free symbols (membership typically undecidable),
    # assumption-carrying symbols (sometimes decidable), integers including
    # the +-10 interval endpoints, rationals, and compound expressions.
    pool = [x, y, z, p, q, k,
            Integer(2), Integer(-3), Integer(0), Integer(11), Integer(-11),
            Integer(10), Integer(-10), Integer(20), Integer(-20),
            Rational(1, 2), Rational(-7, 3), pi, sqrt(2), x + 1, 2 * y]

    # Removal sets of every kind the membership query distinguishes.
    removal_sets = [
        Interval(-10, 10),
        Interval.open(-10, 10),
        Interval.Lopen(-10, 10),
        Interval(0, oo),
        Interval(-oo, 0),
        Interval(-oo, oo),
        FiniteSet(2, 3, 4),
        FiniteSet(x, 2),
        S.Naturals,
        S.Integers,
        S.Reals,
        S.EmptySet,
        S.UniversalSet,
    ]

    # Hand-picked boundary collections: the mixed shape from the public issue
    # example, all-undecided, all-decidable, singletons of each verdict,
    # endpoint values, and compound expressions.
    boundary_collections = [
        [x, y, Integer(2)],
        [x, y],
        [Integer(2), Integer(3)],
        [Integer(2), Integer(11)],
        [x, Integer(2), y, Integer(11)],
        [x],
        [Integer(11)],
        [Integer(2)],
        [Integer(10)], [Integer(-10)],           # interval endpoints
        [Integer(10), Integer(-10), x],
        [p], [q], [k],                            # assumption-carrying symbols
        [p, q, k, x],
        [pi], [sqrt(2)], [x + 1], [2 * y],
        [pi, sqrt(2), Rational(1, 2)],
        [x + 1, 2 * y, Integer(0)],
        [Rational(1, 2), Rational(-7, 3)],
        [Integer(-20), Integer(20)],
        [Integer(0)],
        [x, y, z, p, q, k],
        [Integer(2), Integer(3), Integer(4)],     # exactly a finite removal set
        [Integer(2), x],                          # exactly the symbolic one
        pool,                                     # the whole pool at once
    ]
    # Pad the boundary battery to 60 collections with size-graded prefixes.
    while len(boundary_collections) < 60:
        n = len(boundary_collections) % len(pool) + 1
        boundary_collections.append(pool[:n])

    checked = 0
    n_boundary = 0
    for self_set in removal_sets:
        for coll in boundary_collections:
            err = check_case(sympy, self_set, coll)
            if err:
                print(err)
                return 1
            n_boundary += 1
    checked += n_boundary

    # Fuzz to >= N_TOTAL inputs: random removal set x random 1..8-element
    # sample of the pool, occasionally salted with fresh random integers and
    # rationals so decidable elements spread across the whole verdict space.
    rng = random.Random(SEED)
    n_fuzz = N_TOTAL - checked
    for j in range(n_fuzz):
        self_set = rng.choice(removal_sets)
        size = rng.randint(1, 8)
        coll = rng.sample(pool, min(size, len(pool)))
        if j % 3 == 0:
            coll = coll + [Integer(rng.randint(-25, 25))]
        if j % 7 == 0:
            coll = coll + [Rational(rng.randint(-9, 9), rng.randint(1, 9))]
        err = check_case(sympy, self_set, coll)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow partition == real patched finite-collection "
          "branch on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
