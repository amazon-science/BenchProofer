#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21847 (nagini).

SHADOW: the impl regions of model.py's `keep_comm` and `keep_noncomm`, copied
verbatim below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped. The impl regions use only plain List[int] indexing (PSeq/ToSeq appear
only inside contracts), so no sequence shim is needed. The @Pure helper
`deg_sum` lives entirely in the contract layer and is not part of the
executable impl. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`sympy.polys.monomials.itermonomials` in the single-total-degree-bound branch.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable. The modeled predicate
is the per-candidate retention test inside the two enumeration branches
(commuting and non-commuting variables), whose observable effect is exactly
which candidate terms appear in the generated set. So the oracle question per
input is: "is this candidate's monomial a member of the real function's output
set?" — which must equal the shadow's boolean.

Type bridge (mapping.md section 2): a candidate term is drawn the same way the
real enumeration draws it (combinations_with_replacement over the variables
plus the unit pad for commuting variables; cartesian product for
non-commuting ones); its exponent vector — the count of occurrences of each
real variable — is the model's `powers: List[int]`. Every entry is >= 0 and
`min_degree >= 0` by construction, so every generated input satisfies the
Requires. Membership in the output set is equivalent to the per-candidate
predicate in both branches: commutatively, distinct candidate multisets yield
distinct monomials; non-commutatively, all candidate tuples that collapse to
the same monomial (unit-pad placement) share one exponent vector, hence one
predicate value.

Input domain: the predicate is only reached with a non-empty variable list,
max_degree >= 1 and 0 <= min_degree <= max_degree (the validated operating
domain), so parameter cases are drawn from that domain. Exponent vectors then
range over every vector of length <= 6 with total <= 8 (plus larger cases),
i.e. the full per-candidate domain the callee realizes.

>= 1e5 Requires-satisfying inputs: an exhaustive boundary grid over both
branches plus rng-chosen extra parameter cases. Pinned fuzz seed: 21847.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plus sympy, the repo under test).
"""
import json
import random
import sys

SEED = 21847
MIN_INPUTS = 100_000


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def keep_comm(powers, min_degree):
    total = 0
    i = len(powers)
    while i > 0:
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree


def keep_noncomm(powers, min_degree):
    total = 0
    i = len(powers)
    while i > 0:
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree


# --- candidate enumeration mirroring the callee's (unchanged) input domain ----

def candidates(gens, max_degree, commutative):
    """Yield (monomial, exponent_vector) for every candidate term the real
    enumeration considers at (gens, max_degree). The enumeration itself is
    unchanged plumbing (mapping.md section 2, last row); reproducing it here
    only serves to address each per-candidate predicate input."""
    from itertools import combinations_with_replacement, product
    from sympy import Mul, S

    symbols_with_pad = list(gens) + [S.One]
    if commutative:
        items = combinations_with_replacement(symbols_with_pad, max_degree)
    else:
        items = product(symbols_with_pad, repeat=max_degree)
    for item in items:
        pv = [sum(1 for e in item if e == g) for g in gens]
        yield Mul(*item), pv


def check_case(itermonomials, gens, max_degree, min_degrees_list, commutative):
    """Diff shadow vs oracle for one (gens, max_degree) over each min_degree.
    Returns (n_inputs, error_string_or_None)."""
    cand = list(candidates(gens, max_degree, commutative))
    shadow_fn = keep_comm if commutative else keep_noncomm
    other_fn = keep_noncomm if commutative else keep_comm
    n = 0
    for mind in min_degrees_list:
        produced = set(itermonomials(gens, max_degree, mind))
        kept = set()
        for monom, pv in cand:
            # Requires: min_degree >= 0 and all exponents >= 0
            assert mind >= 0 and all(e >= 0 for e in pv)
            want = shadow_fn(pv, mind)
            # the two modeled sites carry byte-identical impls; keep them in
            # lock-step on every input
            if other_fn(pv, mind) != want:
                return n, ("DISAGREEMENT (shadow self-consistency)\n"
                           "  powers=%r min_degree=%r" % (pv, mind))
            real = monom in produced
            n += 1
            if want != real:
                return n, ("DISAGREEMENT\n  gens=%r max_degree=%r "
                           "min_degree=%r\n  candidate=%r powers=%r\n"
                           "  shadow(retain)=%r real(member)=%r"
                           % (gens, max_degree, mind, monom, pv, want, real))
            if want:
                kept.add(monom)
        if produced != kept:
            return n, ("DISAGREEMENT (set mismatch)\n  gens=%r max_degree=%r "
                       "min_degree=%r\n  real-only=%r shadow-only=%r"
                       % (gens, max_degree, mind,
                          sorted(map(str, produced - kept)),
                          sorted(map(str, kept - produced))))
    return n, None


def main():
    from sympy import symbols
    from sympy.polys.monomials import itermonomials  # REAL patched callee

    x, y, z, w, u, v = symbols('x y z w u v')
    i, j, k = symbols('i j k', commutative=False)
    comm_gens = [x, y, z, w, u, v]
    noncomm_gens = [i, j, k]

    # boundary grid: every min_degree in the validated domain [0, max_degree]
    # (min_degree == 0 keeps everything; == max_degree is the tight bound)
    grid = []
    for n_vars in (1, 2, 3):
        for maxd in range(1, 8):
            grid.append((comm_gens[:n_vars], maxd, True))
    grid.append((comm_gens[:4], 6, True))
    grid.append((comm_gens[:6], 8, True))
    for n_vars in (1, 2):
        for maxd in range(1, 9):
            grid.append((noncomm_gens[:n_vars], maxd, False))
    for maxd in range(1, 7):
        grid.append((noncomm_gens, maxd, False))

    checked = 0
    for gens, maxd, comm in grid:
        n, err = check_case(itermonomials, gens, maxd,
                            list(range(0, maxd + 1)), comm)
        checked += n
        if err:
            print(err)
            return 1

    # rng fuzz: extra parameter cases, pinned seed
    rng = random.Random(SEED)
    fuzz_cases = 0
    while checked < MIN_INPUTS or fuzz_cases < 20:
        comm = rng.random() < 0.5
        if comm:
            gens = comm_gens[:rng.randint(1, 5)]
            maxd = rng.randint(1, 7)
        else:
            gens = noncomm_gens[:rng.randint(1, 3)]
            maxd = rng.randint(1, 5)
        minds = sorted({rng.randint(0, maxd) for _ in range(3)})
        n, err = check_case(itermonomials, gens, maxd, minds, comm)
        checked += n
        fuzz_cases += 1
        if err:
            print(err)
            return 1

    if checked < MIN_INPUTS:
        print("insufficient inputs: %d < %d" % (checked, MIN_INPUTS))
        return 1

    print("G-CONF OK: shadow retention predicate == real membership on %d "
          "per-candidate inputs (boundary grid + %d fuzz cases, seed %d)."
          % (checked, fuzz_cases, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions of "
                                "keep_comm/keep_noncomm)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
