#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13551 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
`prod_of_totals` and `prod_one` copy over as plain functions; PSeq is realized
as an immutable tuple shim (only `len`, indexing and `drop` are used) and
ToSeq lifts a plain list into it. There are no @ContractOnly callees in this
bundle (the one kind-A obligation is an A-reference deep model, not a consumed
axiom).

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
repo's reduction of a finite product whose multiplicand is a sum of two
parts, driven through the repo's own `Product(...).doit()` entry point with a
symbolic upper limit (so the modeled sum-multiplicand branch fires, per
mapping.md §3.1's branch dependency: a non-polynomial sum with symbolic
limits), then instantiated at a concrete range length. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched package importable.

Type bridge (mapping.md §2): a model input is a pair of parallel int lists
(base, comp) of length N — the per-index values of the two parts of the sum.
Two multiplicand families realize it on the repo side:
  * family 1: p(k) = d + c*m**k        -> base[i] = d,        comp[i] = c*m**i
    (a constant leading part + an exponential remaining part — exactly the
    shape of the issue's failing product, e.g. d=1, c=2, m=2)
  * family 2: p(k) = c1*m1**k + c2*m2**k -> base[i] = c1*m1**i, comp[i] = c2*m2**i
    (two exponential parts; exercises a non-constant leading part)
The index k ranges 0..N-1 <-> list index i ranges 0..N-1. The shadow returns
a Python int; the oracle value is the repo's exact Integer — bridged by exact
equality (sympy Integer == python int is exact; the tested arithmetic is
exact integer arithmetic, mapping.md §2, no float encoding).

Input domain mirrors the Requires exactly: len(base) == len(comp) and every
per-index total base[i] + comp[i] != 0 (zero totals are outside the modeled
domain: there the repo reduction yields an undefined symbolic value, not the
integer 0 — mapping.md §2). Family parameters additionally keep the
multiplicand a genuine two-part sum on the repo side (d != 0, c != 0,
m >= 2; c1, c2 != 0, m1 != m2), i.e. inside the modeled scenario. Each new
shape is checked to actually route through the modeled branch (the reduced
form is the symbolic-product expression, not a closed form) before its
observations are trusted.

The oracle reduction is a deterministic pure function of the shape parameters
and the range length, so symbolic reductions are memoized per shape and
observations per (shape, N); every generated input is still individually
diffed against the memoized real observation.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz inputs.
Pinned fuzz seed: 13551.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 13551
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the model uses -------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, items=()):
        self._t = tuple(items)

    def drop(self, n):
        return PSeq(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(xs):
    return PSeq(xs)


# --- pure helpers from model.py, contracts stripped ----------------------------

def prod_of_totals(base, comp):
    if len(base) == 0:
        return 1
    return (base[0] + comp[0]) * prod_of_totals(base.drop(1), comp.drop(1))


def prod_one(xs):
    if len(xs) == 0:
        return 1
    return xs[0] * prod_one(xs.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def product_of_sum(base, comp):
    result = 1
    i = len(base)
    while i > 0:
        result = (base[i - 1] + comp[i - 1]) * result
        i = i - 1
    return result


# --- precondition (Requires) mirror --------------------------------------------

def requires_ok(base, comp):
    return (len(base) == len(comp)
            and all(base[i] + comp[i] != 0 for i in range(len(base))))


# --- oracle: the real patched repo reduction ------------------------------------

class Oracle:
    """Reduces the finite product of the two-part-sum multiplicand with the
    repo's own Product(...).doit() under a symbolic upper limit (so the
    modeled branch fires), then substitutes the concrete range length.
    Memoizes the symbolic reduction per shape and the concrete observation
    per (shape, N) — both are deterministic pure functions of their key."""

    def __init__(self):
        from sympy import Symbol, Product, Sum, exp, log, Integer, sympify
        self.Product = Product
        self.Sum = Sum
        self.exp = exp
        self.log = log
        self.Integer = Integer
        self.sympify = sympify
        self.k = Symbol('k')
        self.n = Symbol('n')
        self._sym = {}    # shape key -> (fired, symbolic reduced expr)
        self._obs = {}    # (shape key, N) -> observed value object

    def _multiplicand(self, shape):
        k = self.k
        if shape[0] == 1:
            _, d, c, m = shape
            return d + c * m ** k
        _, c1, m1, c2, m2 = shape
        return c1 * m1 ** k + c2 * m2 ** k

    def _symbolic(self, shape):
        if shape not in self._sym:
            p = self._multiplicand(shape)
            e = self.Product(p, (self.k, 0, self.n - 1)).doit()
            # the modeled branch must actually have routed: the reduction is
            # the symbolic-product form, not some other closed form
            fired = e.has(self.exp) and e.has(self.Sum) and e.has(self.log)
            self._sym[shape] = (fired, e)
        return self._sym[shape]

    def reduce(self, shape, N):
        """Return (fired, value_object) for the real reduction at range
        length N."""
        key = (shape, N)
        if key not in self._obs:
            fired, e = self._symbolic(shape)
            if not fired:
                self._obs[key] = (False, e)
            else:
                self._obs[key] = (True, e.subs(self.n, N).doit())
        return self._obs[key]


def shape_lists(shape, N):
    """The model-side (base, comp) lists for a shape at range length N
    (the type bridge of mapping.md §2)."""
    if shape[0] == 1:
        _, d, c, m = shape
        return [d] * N, [c * m ** i for i in range(N)]
    _, c1, m1, c2, m2 = shape
    return ([c1 * m1 ** i for i in range(N)],
            [c2 * m2 ** i for i in range(N)])


def check_one(oracle, shape, N):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None (or the string 'notfired' if the shape does not
    route through the modeled branch — outside the modeled scenario)."""
    base, comp = shape_lists(shape, N)
    assert requires_ok(base, comp)
    shadow = product_of_sum(base, comp)
    fired, observed = oracle.reduce(shape, N)
    if not fired:
        return "notfired"
    if oracle.sympify(observed) != oracle.Integer(shadow):
        return ("DISAGREEMENT\n  input: shape=%r N=%d base=%r comp=%r\n"
                "  shadow=%r\n  real=%r"
                % (shape, N, base, comp, shadow, observed))
    # cross-check the shadow against the pure spec fold on the same input
    spec = prod_of_totals(ToSeq(base), ToSeq(comp))
    if spec != shadow:
        return ("DISAGREEMENT (impl vs pure fold)\n  input: shape=%r N=%d\n"
                "  shadow=%r\n  fold=%r" % (shape, N, shadow, spec))
    return None


# --- input generation ------------------------------------------------------------

def in_domain(shape, N):
    """Requires mirror on the shape parametrization: every per-index total
    nonzero, and the shape a genuine two-part sum."""
    if shape[0] == 1:
        _, d, c, m = shape
        if d == 0 or c == 0 or m < 2:
            return False
        return all(d + c * m ** i != 0 for i in range(N))
    _, c1, m1, c2, m2 = shape
    if c1 == 0 or c2 == 0 or m1 == m2 or m1 < 2 or m2 < 2:
        return False
    return all(c1 * m1 ** i + c2 * m2 ** i != 0 for i in range(N))


def boundary_inputs():
    cases = []
    # the issue's failing product shape (base=[1,1], comp=[2,4] at N=2 gives
    # 15, where distributing the product across the parts would give 9)
    for N in range(0, 7):
        cases.append(((1, 1, 2, 2), N))
    # empty and singleton ranges across shapes
    for shape in ((1, 2, 1, 2), (1, -3, 1, 2), (1, 7, 2, 5), (1, 3, -1, 2),
                  (1, -9, 2, 3), (1, 1, 1, 9), (1, 99, -9, 2),
                  (2, 1, 2, 1, 3), (2, 2, 2, 3, 5), (2, -1, 2, 2, 3),
                  (2, 4, 3, -3, 2)):
        for N in range(0, 7):
            cases.append((shape, N))
    # sign-flipping totals (negative products) and deeper ranges
    for shape in ((1, 3, -1, 2), (1, 5, -1, 3), (1, -7, 1, 2)):
        for N in (4, 5, 6, 7, 8):
            cases.append((shape, N))
    return [(shape, N) for (shape, N) in cases if in_domain(shape, N)]


def fuzz_input(rng):
    if rng.random() < 0.75:
        # family 1: constant part + exponential part
        d = rng.randint(-30, 30)
        c = rng.randint(-6, 6)
        m = rng.randint(2, 5)
        shape = (1, d, c, m)
    else:
        # family 2: two exponential parts
        c1 = rng.randint(-4, 4)
        c2 = rng.randint(-4, 4)
        m1, m2 = rng.sample((2, 3, 5, 7), 2)
        shape = (2, c1, m1, c2, m2)
    N = rng.randint(0, 8)
    return shape, N


def main():
    oracle = Oracle()
    checked = 0
    n_notfired = 0

    n_boundary = 0
    for shape, N in boundary_inputs():
        err = check_one(oracle, shape, N)
        if err == "notfired":
            n_notfired += 1
            continue
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    n_fuzz = 0
    while n_fuzz < N_FUZZ:
        shape, N = fuzz_input(rng)
        if not in_domain(shape, N):
            continue
        err = check_one(oracle, shape, N)
        if err == "notfired":
            n_notfired += 1
            continue
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

    # the constructed families are inside the modeled scenario; a wholesale
    # failure to route would mean the oracle harness is wrong, not the model
    if n_notfired > checked // 100:
        print("ORACLE HARNESS PROBLEM: %d shapes did not route through the "
              "modeled reduction (of %d checked)" % (n_notfired, checked))
        return 1

    print("G-CONF OK: shadow impl == real reduction on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
