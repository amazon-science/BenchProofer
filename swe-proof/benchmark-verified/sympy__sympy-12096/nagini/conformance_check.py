#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12096 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers `imp`
and `eval_seq` copy over as plain functions; PSeq is realized as an immutable
tuple shim (only `len` and `drop` are used) and ToSeq lifts a plain list into
it. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
numeric reduction of a nested chain of implemented-function applications over
an integer leaf, driven by the repo's own evaluate-to-number entry point on an
expression built with `implemented_function` (the worked example's squaring
implementation, matching the model's concrete representative `imp(x) = x * x`).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched package importable.

Type bridge (mapping.md section 2): a nesting of depth n over integer leaf v
maps to (leaf=v, layers=<any list of length n>) — layer element values are
irrelevant, only the count carries structure, so the fuzzer draws them
arbitrarily. The shadow returns a present int; the oracle returns a repo
number object. Presence bridges to `observed.is_Number` and the value bridges
via Python float equality: every in-domain value is < 10**14 < 2**53, so both
conversions are exact and the comparison is exact (and robust to the repo
number type's own equality quirks across versions). The oracle is a pure
deterministic function of (leaf, depth), so oracle observations are memoized
on that key; every generated input is still individually diffed against it.

Input domain mirrors the Requires exactly: leaf >= 0 and
eval_seq(leaf, layers) < 10**14 (the exact-representation window declared by
the contract). Generation picks a depth, then a leaf within the largest
window that keeps the reduction in-domain, and re-checks the precondition
before counting the input.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz inputs.
Pinned fuzz seed: 12096.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 12096
N_FUZZ = 100_000
BOUND = 10 ** 14


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

def imp(x):
    return x * x


def eval_seq(leaf, layers):
    if len(layers) == 0:
        return leaf
    return imp(eval_seq(leaf, layers.drop(1)))


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def eval_implemented(leaf, layers):
    acc = leaf
    i = len(layers)
    while i > 0:
        acc = imp(acc)
        i = i - 1
    return acc


# --- precondition (Requires) mirror --------------------------------------------

def requires_ok(leaf, layers):
    return leaf >= 0 and eval_seq(leaf, ToSeq(layers)) < BOUND


# --- oracle: the real patched repo reduction ------------------------------------

class Oracle:
    """Builds the depth-n nesting over an integer leaf and reduces it with the
    repo's numeric evaluation; memoizes on (leaf, depth) — the reduction is a
    deterministic pure function of that pair."""

    def __init__(self):
        from sympy import Integer
        from sympy.utilities.lambdify import implemented_function
        self.Integer = Integer
        # the worked example's implementation == the model's representative imp
        self.f = implemented_function('f', lambda x: x ** 2)
        self._cache = {}

    def reduce(self, leaf, depth):
        """Return (is_number, value_object) for the real reduction."""
        key = (leaf, depth)
        if key not in self._cache:
            expr = self.Integer(leaf)
            for _ in range(depth):
                expr = self.f(expr)
            observed = expr.evalf()
            self._cache[key] = (bool(observed.is_Number), observed)
        return self._cache[key]


def check_one(oracle, leaf, layers):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    shadow = eval_implemented(leaf, layers)
    is_num, observed = oracle.reduce(leaf, len(layers))
    # presence: the shadow always yields a present int; the real reduction
    # must yield a number (never leave the object unevaluated).
    if not is_num:
        return ("DISAGREEMENT (presence)\n  input: leaf=%r layers=%r (depth %d)\n"
                "  shadow=%r\n  real=%r (not a number)"
                % (leaf, layers, len(layers), shadow, observed))
    # exact value comparison through double precision: in-domain values are
    # < 10**14 < 2**53, so both float conversions are exact.
    if float(observed) != float(shadow):
        return ("DISAGREEMENT (value)\n  input: leaf=%r layers=%r (depth %d)\n"
                "  shadow=%r\n  real=%r"
                % (leaf, layers, len(layers), shadow, observed))
    return None


# --- input generation ------------------------------------------------------------

# Largest in-domain leaf per depth (leaf^(2^depth) < 10**14 for leaf >= 2;
# leaves 0 and 1 are in-domain at every depth).
MAX_LEAF = {0: BOUND - 1, 1: 9_999_999, 2: 3162, 3: 56, 4: 7, 5: 2}


def boundary_inputs():
    cases = []
    # small leaves x shallow depths (includes the zero-layer bare leaf and the
    # two-layer composition over leaf 2 — the discriminating shape)
    for leaf in (0, 1, 2, 3, 5, 10):
        for depth in range(0, 7):
            cases.append((leaf, [0] * depth))
    # the in-domain edge leaf at each depth, and one past-the-max probe below it
    for depth, mx in MAX_LEAF.items():
        cases.append((mx, [7] * depth))
        if mx > 1:
            cases.append((mx - 1, [-3] * depth))
    # deep chains: only leaves 0 and 1 stay in-domain
    for leaf in (0, 1):
        for depth in (10, 25, 40):
            cases.append((leaf, [1] * depth))
    return [(leaf, layers) for (leaf, layers) in cases
            if requires_ok(leaf, layers)]


def fuzz_input(rng):
    r = rng.random()
    if r < 0.20:
        depth = 0
    elif r < 0.45:
        depth = 1
    elif r < 0.65:
        depth = 2
    elif r < 0.80:
        depth = 3
    elif r < 0.90:
        depth = rng.randint(4, 5)
    else:
        depth = rng.randint(6, 40)   # leaves 0/1 only
    mx = MAX_LEAF.get(depth, 1)
    leaf = rng.randint(0, mx)
    # layer element values are irrelevant to the behaviour; draw arbitrarily
    layers = [rng.randint(-1000, 1000) for _ in range(depth)]
    return leaf, layers


def main():
    oracle = Oracle()
    checked = 0

    n_boundary = 0
    for leaf, layers in boundary_inputs():
        err = check_one(oracle, leaf, layers)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    n_fuzz = 0
    while n_fuzz < N_FUZZ:
        leaf, layers = fuzz_input(rng)
        if not requires_ok(leaf, layers):
            continue
        err = check_one(oracle, leaf, layers)
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

    print("G-CONF OK: shadow impl == real reduction on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
