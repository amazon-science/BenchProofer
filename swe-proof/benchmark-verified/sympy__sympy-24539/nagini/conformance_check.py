#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24539 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. There are no @Pure helpers
and no @ContractOnly callees in this bundle; the stripped impl uses no PSeq
operations (PSeq appeared only inside proof-only Assert lines), so no sequence
shim is required. The user-defined exception class copies over as-is.

ORACLE: the REAL patched repo function the model models per mapping.md —
`PolyElement.as_expr(self, *symbols)` (sympy/polys/rings.py). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched package importable.

Type bridge (mapping.md §Type abstraction): generator symbols are modelled as
int identities; the bridge realises identity k as the sympy Symbol named
"v<k>". A ring with n generators is built over the Symbols for identities
100..100+n-1, so `default_symbols = [100..100+n-1]` maps exactly to
`ring.symbols` and `ngens == len(default_symbols)` holds by construction
(mirroring the repo, where the ring's generator count equals the length of its
symbol tuple). The var-args tuple of supplied Symbols maps position-wise to
the supplied identity list. The user-defined SymbolCountError stands in for
the repo's ValueError (fact-of-raise only, per mapping.md).

OBSERVING THE SELECTION: the modelled Result() IS the gens sequence handed to
the downstream builder `expr_from_dict(self.as_expr_dict(), *gens)`, which is
UNCHANGED and a deterministic function of (term dict, gens). The test
polynomial is chosen so that rendering is INJECTIVE in the gens sequence:
p = 1 + sum_i c_i * x_i**(i+1) with distinct prime coefficients c_i and
distinct exponents per position — no two positional terms can merge even when
supplied symbols repeat, so two gens sequences render equal expressions iff
they are equal element-for-element. Hence the diff per input is:
  * shadow raises  <=>  real as_expr raises ValueError;
  * shadow returns sel  =>  real as_expr(*supplied) == expr_from_dict(rep, *sel')
    where sel' is sel bridged back to Symbols.
The observation is a deterministic pure function of (ngens, supplied ids), so
it is memoized on that key; every generated input is still individually
counted and diffed.

Input domain mirrors the Requires exactly: `symbols` any identity list (dups
allowed), `default_symbols` the ring's identities, `ngens ==
len(default_symbols)`; realizable rings have >= 1 generator. Supplied lengths
are biased toward the three behavioural regimes (empty / matching / non-empty
mismatching).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz inputs.
Pinned fuzz seed: 24539.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 24539
N_FUZZ = 100_000
MAX_NGENS = 5
EXTRA_IDS = [0, 1, 2, 3, 4, 5]        # identities of non-default symbols
DEFAULT_ID_BASE = 100                 # identities of ring-default symbols
PRIMES = [2, 3, 5, 7, 11, 13, 17]     # distinct positional coefficients


# --- the user-defined exception class from model.py -----------------------------

class SymbolCountError(Exception):
    pass


# --- the impl region of model.py, verbatim, contract calls stripped -------------

def select_render_symbols(symbols, default_symbols, ngens):
    if len(symbols) == 0:
        src = default_symbols  # type: List[int]
    elif len(symbols) != ngens:
        raise SymbolCountError()
    else:
        src = symbols
    # Materialise the selected sequence (a fresh carrier element-for-element
    # equal to `src`); the downstream builder reads this sequence.
    result = []  # type: List[int]
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        result = result + [c]
        i = i + 1
    return result


# --- oracle: the real patched repo selection, observed through rendering --------

class Oracle:
    """One ring per ngens, with a rendering-injective probe polynomial.
    Returns, for (ngens, supplied ids), either the string 'RAISE' or the
    rendered sympy expression of the real as_expr call."""

    def __init__(self):
        from sympy import Symbol, ZZ
        from sympy.polys.rings import ring
        from sympy.polys.polyutils import expr_from_dict
        self.Symbol = Symbol
        self.expr_from_dict = expr_from_dict
        self._rings = {}
        self._sym = {}
        self._cache = {}
        for n in range(1, MAX_NGENS + 1):
            names = ",".join("v%d" % (DEFAULT_ID_BASE + i) for i in range(n))
            rr = ring(names, ZZ)
            R, gens = rr[0], rr[1:]
            # injective probe: distinct prime coefficient and distinct
            # exponent at every generator position, plus a constant term
            p = R.one
            for i, g in enumerate(gens):
                p = p + PRIMES[i] * g ** (i + 1)
            self._rings[n] = (R, p, p.as_expr_dict())

    def sym(self, ident):
        if ident not in self._sym:
            self._sym[ident] = self.Symbol("v%d" % ident)
        return self._sym[ident]

    def real_render(self, ngens, supplied_ids):
        key = (ngens, tuple(supplied_ids))
        if key not in self._cache:
            _, p, _ = self._rings[ngens]
            args = tuple(self.sym(i) for i in supplied_ids)
            try:
                self._cache[key] = p.as_expr(*args)
            except ValueError:
                self._cache[key] = 'RAISE'
        return self._cache[key]

    def render_of_selection(self, ngens, selected_ids):
        _, _, rep = self._rings[ngens]
        return self.expr_from_dict(
            rep, *[self.sym(i) for i in selected_ids])


def check_one(oracle, ngens, supplied_ids):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    default_ids = [DEFAULT_ID_BASE + i for i in range(ngens)]
    try:
        shadow = select_render_symbols(list(supplied_ids), default_ids, ngens)
        shadow_raised = False
    except SymbolCountError:
        shadow, shadow_raised = None, True

    real = oracle.real_render(ngens, supplied_ids)
    real_raised = (real == 'RAISE') if isinstance(real, str) else False

    if shadow_raised != real_raised:
        return ("DISAGREEMENT (raise/no-raise)\n"
                "  input: ngens=%d supplied=%r defaults=%r\n"
                "  shadow: %s\n  real:   %s"
                % (ngens, list(supplied_ids), default_ids,
                   "raise" if shadow_raised else "return %r" % (shadow,),
                   "ValueError" if real_raised else "returned %r" % (real,)))
    if shadow_raised:
        return None
    expected = oracle.render_of_selection(ngens, shadow)
    if real != expected:
        return ("DISAGREEMENT (selected sequence)\n"
                "  input: ngens=%d supplied=%r defaults=%r\n"
                "  shadow selection: %r (renders as %r)\n"
                "  real rendering:   %r"
                % (ngens, list(supplied_ids), default_ids,
                   shadow, expected, real))
    return None


# --- input generation ------------------------------------------------------------

def boundary_inputs():
    cases = []
    for n in range(1, MAX_NGENS + 1):
        defaults = [DEFAULT_ID_BASE + i for i in range(n)]
        cases.append((n, ()))                          # empty -> defaults
        cases.append((n, tuple(defaults)))             # matching == defaults
        cases.append((n, tuple(reversed(defaults))))   # matching, reordered
        cases.append((n, tuple(EXTRA_IDS[:n])))        # matching, fresh
        cases.append((n, (EXTRA_IDS[0],) * n))         # matching, all-equal
        # non-empty mismatching lengths around ngens
        for m in range(1, n + 3):
            if m != n:
                cases.append((n, tuple(EXTRA_IDS[i % len(EXTRA_IDS)]
                                       for i in range(m))))
                cases.append((n, (defaults + defaults)[:m]
                              if m <= 2 * n else tuple(EXTRA_IDS[:1]) * m))
    return [(n, tuple(s)) for (n, s) in cases]


def fuzz_input(rng):
    n = rng.randint(1, MAX_NGENS)
    r = rng.random()
    if r < 0.25:
        m = 0
    elif r < 0.60:
        m = n                                  # the matching regime
    else:
        m = rng.choice([k for k in range(1, n + 4) if k != n])
    pool = EXTRA_IDS + [DEFAULT_ID_BASE + i for i in range(n)]
    supplied = tuple(rng.choice(pool) for _ in range(m))
    return n, supplied


def main():
    oracle = Oracle()
    checked = 0

    n_boundary = 0
    for ngens, supplied in boundary_inputs():
        err = check_one(oracle, ngens, supplied)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    n_fuzz = 0
    while n_fuzz < N_FUZZ:
        ngens, supplied = fuzz_input(rng)
        err = check_one(oracle, ngens, supplied)
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

    print("G-CONF OK: shadow impl == real patched as_expr selection on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
