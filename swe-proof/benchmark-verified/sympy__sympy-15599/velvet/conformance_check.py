#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15599 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`reduced` / `reduceFactor`, the per-factor residue rewrite of the
              product's non-modular factor list) transliterated to Python over
              the real repo types, via the mapping.md row bijection
              (`Factor.num n` ↔ a SymPy `Integer`; `Factor.sym k` ↔ any
              non-integer factor; `Int.fmod n q` ↔ Python `n % q`). There are NO
              A-tagged ops (no axioms).
  * ORACLE  — `patch.diff`'s behaviour at the changed site: the gold patch's own
              added loop (hunk 3), run on the REAL `non_mod_l` factor list of a
              product `p`, using the REAL patched SymPy in the prebuilt instance
              image (gold patch applied at base_commit by the harness,
              G-RESOLVE). This is the exact per-factor transformation the patch
              introduces — `i % q` for an `Integer` factor with non-zero residue,
              the factor unchanged otherwise.

Why compare at the factor-rewrite granularity (not the final `Mod(p, q)`):
re-feeding the shadow's reduced product back into the patched `Mod` would let
the patch re-reduce it, masking a wrong shadow (an identity shadow would still
"pass" because the patched `Mod` reduces `3*i` itself). Diffing the post-rewrite
factor list — the precise operation `patch.diff` adds — is the faithful,
non-circular R/I observable: a wrong `reduceFactor` (identity, wrong sign
convention, reducing on zero residue, …) diverges immediately. An additional
end-to-end assertion confirms the site decomposition: the real patched
`Mod(p, q)` equals `Mod(Mul(*oracle_factors), q)`.

They must agree as an ordered factor list on every input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), sympy + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys


SEED = 15599
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean reduced/reduceFactor, transliterated -------
# reduceFactor (q : Int) : Factor -> Factor
#   | .num n => if Int.fmod n q != 0 then .num (Int.fmod n q) else .num n
#   | .sym k => .sym k
# `Int.fmod n q` is Python's floored `%` on ints (mapping.md §2): exact match.
def shadow_reduce_factor(f, q):
    """Transliteration of `reduceFactor q f`. `f` is a real SymPy factor."""
    from sympy import Integer
    if f.is_Integer:                     # .num branch
        n = int(f)
        r = n % q                        # Int.fmod n q  (floored, sign of q)
        if r != 0:                       # Int.fmod n q != 0
            return Integer(r)
        return f                         # zero residue: factor unchanged
    return f                             # .sym branch: opaque factor unchanged


def shadow_reduced(factors, q):
    """`reduced q factors` transliterated: map reduceFactor over the list,
    preserving order and length."""
    return [shadow_reduce_factor(f, q) for f in factors]


# --- the oracle: patch.diff's added loop (hunk 3) on the real non_mod_l -------
def oracle_reduced(non_mod_l, q):
    """patch.diff behaviour at the changed site — the gold patch's own code:

        _ = []
        for i in non_mod_l:
            if i.is_Integer and (i % q is not S.Zero):
                _.append(i % q)
            else:
                _.append(i)
        non_mod_l = _

    run on the REAL patched SymPy objects. `q` here is a SymPy Integer."""
    from sympy.core.singleton import S
    out = []
    for i in non_mod_l:
        if i.is_Integer and (i % q is not S.Zero):
            out.append(i % q)
        else:
            out.append(i)
    return out


# --- fuzzing: products of integer literals and integer-assumption symbols -----
def _symbol_bank():
    from sympy import symbols
    # integer + positive so they survive as non-numeric Mul factors and the
    # product stays a Mul reaching the patched branch (mapping.md §3.2).
    return list(symbols('a b c d e', integer=True, positive=True))


def _split_non_mod(p):
    """Split a product's factors as Mod.eval does: non-Mod factors vs Mod
    factors. Our fuzz builds products with NO Mod factor, so mod_l is empty and
    non_mod_l == p.args (mapping.md §3.2)."""
    from sympy import Mul
    from sympy.core.mod import Mod
    if isinstance(p, Mul):
        args = p.args
    else:
        args = (p,)
    non_mod_l = [a for a in args if not isinstance(a, Mod)]
    mod_l = [a for a in args if isinstance(a, Mod)]
    return non_mod_l, mod_l


def _gen_case(rng, syms):
    """One fuzzed scenario: a product of a few integer literals and symbols, and
    an integer modulus q with |q| >= 2 (both signs). Returns (p, q_int)."""
    from sympy import Mul, Integer
    n_int = rng.randint(0, 3)
    n_sym = rng.randint(0, 3)
    factors = []
    for _ in range(n_int):
        factors.append(Integer(rng.randint(-20, 20)))
    for _ in range(n_sym):
        base = rng.choice(syms)
        e = rng.randint(1, 3)
        factors.append(base ** e)
    # ensure at least one factor so we have a product
    if not factors:
        factors.append(rng.choice(syms))
    p = Mul(*factors)
    q = rng.choice([-7, -5, -4, -3, -2, 2, 3, 4, 5, 7])
    return p, q


def _boundary_cases():
    """Deterministic boundary scenarios (plan §4.1 step 4): the F2P assertions
    and sign/zero-residue shapes. Returns list of (p, q_int)."""
    from sympy import symbols, Integer, Rational
    i, j = symbols('i j', integer=True, positive=True)
    return [
        (3 * i, 2),               # F2P: Mod(3*i,2) == Mod(i,2)  -> 3 reduces to 1
        (8 * i, 4),               # F2P: Mod(8*i,4) == 0         -> 8%4==0, factor kept
        (8 * i / j, 4),           # F2P: Mod(8*i/j,4) == 4*Mod(2*i/j,1)
        (4 * i, 4),               # existing: Mod(4*i,4) == 0
        (Integer(1) * i, 2),      # coefficient 1 (residue 1 != 0 -> stays 1)
        (-3 * i, 2),              # negative coefficient, q>0  -> -3 % 2 == 1
        (3 * i, -2),              # positive coefficient, q<0  -> 3 % -2 == -1
        (-5 * i, -3),             # both negative              -> -5 % -3 == -2
        (6 * i, 3),               # 6%3==0 -> factor kept
        (7 * i * j, 5),           # 7%5==2 -> reduces to 2
        (i * j, 2),               # all symbolic -> no change
        (Integer(10), 4),         # pure number product (single int factor)
    ]


def main():
    rng = random.Random(SEED)
    syms = _symbol_bank()
    disagreements = []
    count = 0

    def check(p, q_int):
        nonlocal count
        from sympy import Integer, Mul
        from sympy.core.mod import Mod
        count += 1
        q = Integer(q_int)
        non_mod_l, mod_l = _split_non_mod(p)
        shadow = shadow_reduced(non_mod_l, q_int)
        oracle = oracle_reduced(non_mod_l, q)
        # compare the post-rewrite factor lists (the R/I observable)
        if [str(s) for s in shadow] != [str(o) for o in oracle]:
            disagreements.append((p, q_int, [str(s) for s in shadow],
                                  [str(o) for o in oracle]))
            return
        # site-decomposition sanity: real patched Mod(p,q) == Mod(rebuilt, q).
        # Only meaningful when mod_l is empty (our regime); guards against the
        # factor list not being the whole story at the modeled site.
        if not mod_l:
            rebuilt = Mul(*oracle)
            if Mod(p, q) != Mod(rebuilt, q):
                disagreements.append((p, q_int, "Mod(p,q)=%r" % Mod(p, q),
                                      "Mod(rebuilt,q)=%r" % Mod(rebuilt, q)))

    for p, q_int in _boundary_cases():
        check(p, q_int)

    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        p, q_int = _gen_case(rng, syms)
        check(p, q_int)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for p, q, sh, orc in disagreements:
            print("  p=%r q=%r\n    shadow=%r\n    oracle=%r" % (p, q, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reduceModFactors (reduced/reduceFactor) "
          "agrees with patch.diff's per-factor rewrite on the real non_mod_l "
          "over %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
