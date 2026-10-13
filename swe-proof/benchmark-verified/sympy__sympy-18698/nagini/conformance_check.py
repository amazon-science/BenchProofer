#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18698 (nagini).

SHADOW: the impl region of model.py's `consolidate_by_multiplicity`, copied
VERBATIM below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped, together with the loop helper `occurs_in` (its contracts stripped)
and the `@Pure` helpers (`empty_seq`, `occurs`, `dedup`, `prod_k`,
`lemma_prod_unfold`) as plain functions over a tuple-backed `PSeq` shim
(`ToSeq` = tuple). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md --
`sympy.polys.polytools._symbolic_factor_list(expr, opt, method)` called with
`method == 'sqf'`, whose post-loop consolidation is the modeled behaviour.
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed; this script never applies any diff.

Driving the real function: a case is a pair of parallel lists (factor tokens /
multiplicities). Each contribution i is realised as a distinct monic linear
polynomial E_i = x - c_i (c_i distinct within a case) raised to its
multiplicity k_i, assembled as an UNEVALUATED Mul of UNEVALUATED Pows so no
combining happens before the call. Each E_i is irreducible and square-free, so
the function's per-argument decomposition contributes exactly (Poly(E_i), k_i)
-- the raw contribution list IS the case, and the returned factor list is the
consolidated report under test (the leading coefficient stays 1 because every
E_i is monic).

Type bridge (mapping.md section 2 -- the token <-> expression bijection):
  * factor tokens are DISTINCT PRIMES within a case, so the shadow's merged
    integer product for a multiplicity decodes UNIQUELY back to the set of
    contributing indices (divisibility by each case prime, then an exact
    product re-check). The bijection then gives the expected merged
    expression: the product of the E_i of exactly that group.
  * multiplicities are Python ints, identity-mapped (domain: >= 1, the
    multiplicities a square-free decomposition produces).
  * ordering of the report entries is UNOBSERVABLE (the caller sorts the
    result downstream -- refinement.md), so shadow and real outputs are
    compared as multiplicity-keyed maps: same distinct multiplicities, one
    entry each, and per multiplicity the real merged factor must equal the
    decoded expected product (polynomial equality via expand); the real
    report must also carry each multiplicity at most once and leave the
    coefficient untouched.

Disagreement = any of: different reported multiplicity sets, a multiplicity
reported more than once by either side, a shadow product that does not decode
to a subset of the case's tokens, or a real merged factor different from the
decoded group product.

>= 1e5 Requires-satisfying inputs: structured boundary cases (empty, single,
all-equal multiplicities, the issue-shaped repeated-multiplicity lists,
first-occurrence permutations) + 100000 fuzz draws over list lengths 0..8 and
multiplicities 1..6 (weighted toward collisions so merging is exercised).
Pinned fuzz seed: 186980.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo under test only (random; hypothesis
not needed).
"""
import json
import random
import sys

SEED = 186980
N_FUZZ = 100_000


# --- PSeq / ToSeq shim (tuple-backed) -----------------------------------------

class PSeq(object):
    """Minimal stand-in for the specification sequence: immutable, supports
    len / indexing / take / drop / concatenation / equality."""

    def __init__(self, *items):
        if len(items) == 1 and isinstance(items[0], tuple):
            self._t = items[0]
        else:
            self._t = tuple(items)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def take(self, n):
        return PSeq(self._t[:n])

    def drop(self, n):
        return PSeq(self._t[n:])

    def __add__(self, other):
        return PSeq(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(xs):
    return PSeq(tuple(xs))


# --- @Pure helpers from model.py, contracts stripped ---------------------------

def empty_seq():
    """The empty multiplicity sequence."""
    return PSeq(0).take(0)


def occurs(s, k):
    """Whether the value ``k`` occurs in ``s``. Front-recursive so a single
    unfold is available per step (value-based membership)."""
    if len(s) == 0:
        return False
    if s[0] == k:
        return True
    return occurs(s.drop(1), k)


def dedup(s):
    """The distinct values of ``s`` in order of FIRST occurrence: each value is
    kept once."""
    if len(s) == 0:
        return empty_seq()
    if occurs(dedup(s.take(len(s) - 1)), s[len(s) - 1]):
        return dedup(s.take(len(s) - 1))
    return dedup(s.take(len(s) - 1)) + PSeq(s[len(s) - 1])


def prod_k(facs, mlts, k, n):
    """The product of exactly the factors whose multiplicity is ``k``, taken
    over the first ``n`` contributions; the empty product is 1."""
    if n == 0:
        return 1
    if n - 1 < len(mlts) and n - 1 < len(facs) and mlts[n - 1] == k:
        return prod_k(facs, mlts, k, n - 1) * facs[n - 1]
    return prod_k(facs, mlts, k, n - 1)


def lemma_prod_unfold(facs, mlts, k, n):
    """Trivial at runtime (the recursion equation holds by definition)."""
    return True


# --- impl region of model.py, verbatim, contract calls stripped ----------------

def occurs_in(xs, k):
    """Whether the value ``k`` occurs in the list ``xs``."""
    n = len(xs)
    found = False
    j = n
    while j > 0:
        if xs[j - 1] == k:
            found = True
        j = j - 1
    return found


def consolidate_by_multiplicity(factors, mults):
    """Consolidate the contributions (parallel ``factors`` / ``mults``) into
    the list of merged factors, one per distinct multiplicity (first
    occurrence), each the product of exactly its group."""
    ms = ToSeq(mults)
    fs = ToSeq(factors)
    # Phase 1: the distinct multiplicities, each kept once at first occurrence.
    dmults = []
    i = 0
    while i < len(mults):
        m = mults[i]
        present = occurs_in(dmults, m)  # m already among the kept distinct mults?
        if not present:
            dmults = dmults + [m]
        i = i + 1

    # Phase 2: the merged factor of each reported multiplicity is the product
    # of exactly the contributions of that multiplicity.
    out = []
    p = 0
    while p < len(dmults):
        kk = dmults[p]
        # inner product over exactly the group of multiplicity kk
        acc = 1
        n = 0
        while n < len(mults):
            if mults[n] == kk:
                acc = acc * factors[n]
            n = n + 1
        out = out + [acc]
        p = p + 1
    return out


# --- bridge to the real patched repo function ----------------------------------

PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]


def make_driver():
    """Return `drive(consts, mults)`: realise the contributions as an
    unevaluated product of unevaluated powers of distinct monic linear
    polynomials x - consts[i], call the real function under 'sqf', and return
    (coeff, [(factor_expr, multiplicity), ...])."""
    sys.path.insert(0, "/testbed")
    from sympy import S, Symbol, Mul, Pow
    from sympy.polys import polyoptions
    from sympy.polys.polytools import _symbolic_factor_list

    x = Symbol("x")
    opt = polyoptions.build_options((), {})

    def drive(consts, mults):
        if not consts:
            expr = S.One
        else:
            pows = [Pow(x - c, k, evaluate=False)
                    for c, k in zip(consts, mults)]
            expr = pows[0] if len(pows) == 1 else Mul(*pows, evaluate=False)
        coeff, fl = _symbolic_factor_list(expr, opt, 'sqf')
        return coeff, [(f.as_expr() if hasattr(f, 'as_expr') else f, int(k))
                       for f, k in fl]

    return drive, x


def check_one(drive, x, tokens, consts, mults, sympy_mod):
    """One differential case. `tokens` are the shadow's factor ints (distinct
    primes), `consts` realise the same contributions as expressions x - c.
    Returns an error string on disagreement, else None."""
    n = len(mults)
    assert len(tokens) == n and len(consts) == n  # Requires: equal lengths

    shadow_out = consolidate_by_multiplicity(list(tokens), list(mults))
    shadow_keys = list(dedup(ToSeq(mults))._t)  # multiplicity of each entry
    shadow_map = dict(zip(shadow_keys, shadow_out))

    coeff, real = drive(consts, mults)

    header = ("  tokens=%r consts=%r mults=%r\n  shadow(out by mult)=%r\n"
              "  real coeff=%r real list=%r"
              % (tokens, consts, mults, shadow_map, coeff, real))

    if coeff != 1:
        return "DISAGREEMENT (coefficient not left untouched)\n" + header
    if len(shadow_out) != len(shadow_keys):
        return "DISAGREEMENT (shadow entry count vs distinct mults)\n" + header

    real_keys = [k for _, k in real]
    if len(set(real_keys)) != len(real_keys):
        return "DISAGREEMENT (real reports a multiplicity twice)\n" + header
    if set(real_keys) != set(shadow_keys):
        return "DISAGREEMENT (reported multiplicity sets differ)\n" + header

    real_map = dict((k, f) for f, k in real)
    for k in shadow_keys:
        m = shadow_map[k]
        # decode the shadow's merged product back to the contributing group
        # (tokens are distinct primes, so divisibility identifies the group;
        # the exact product re-check rejects any non-group value)
        group = [i for i in range(n) if m % tokens[i] == 0]
        prod = 1
        for i in group:
            prod *= tokens[i]
        if prod != m:
            return ("DISAGREEMENT (shadow product for mult %r does not decode "
                    "to a token group)\n" % (k,)) + header
        expected = sympy_mod.S.One
        for i in group:
            expected = expected * (x - consts[i])
        if sympy_mod.expand(real_map[k] - expected) != 0:
            return ("DISAGREEMENT (merged factor for mult %r: real %r vs "
                    "decoded shadow group product %r)\n"
                    % (k, real_map[k], expected)) + header
    return None


def gen_case(rng):
    """One Requires-satisfying fuzz case: parallel lists of length 0..8;
    multiplicities 1..6 drawn from a small alphabet so collisions (the merged
    groups) are frequent; tokens distinct primes; consts distinct ints."""
    n = rng.randint(0, 8)
    alphabet = rng.sample(range(1, 7), rng.randint(1, 4)) if n else [1]
    mults = [rng.choice(alphabet) for _ in range(n)]
    tokens = rng.sample(PRIMES, n)
    consts = rng.sample(range(-9, 10), n)
    return tokens, consts, mults


def boundary_cases():
    """Structured cases: empty, singletons, all-equal multiplicities, the
    issue-shaped repeated-multiplicity lists, first-occurrence permutations."""
    cases = []

    def add(mults, consts=None):
        n = len(mults)
        toks = PRIMES[:n]
        if consts is None:
            consts = list(range(1, n + 1))
        cases.append((toks, consts, list(mults)))

    add([])
    add([1])
    add([5])
    add([1, 1])                    # two factors sharing multiplicity 1
    add([3, 3])                    # two factors sharing multiplicity 3
    add([2, 3, 3, 1])              # mixed: one shared group among singletons
    add([1, 2, 3])
    add([2, 1, 2])                 # first-occurrence order differs from sorted
    add([1, 2, 1, 2, 1])
    add([3, 3, 3, 3])              # one big group
    add([5, 4, 3, 2, 1])           # all distinct, reversed
    add([1, 1, 2, 2, 3, 3])        # several shared groups
    add([6, 6, 6, 1, 1, 2])
    add([4, 4], consts=[-3, 7])    # negative constant in a merged group
    add([2, 2, 2], consts=[0, -1, 1])
    # permutations of one shared-multiplicity list (order of contributions)
    add([1, 2, 2, 3])
    add([2, 1, 3, 2])
    add([3, 2, 2, 1])
    add([2, 2, 1, 3])
    return cases


def main():
    drive, x = make_driver()
    import sympy as sympy_mod

    checked = 0
    n_boundary = 0
    for tokens, consts, mults in boundary_cases():
        err = check_one(drive, x, tokens, consts, mults, sympy_mod)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        tokens, consts, mults = gen_case(rng)
        err = check_one(drive, x, tokens, consts, mults, sympy_mod)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real consolidated factor list on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
