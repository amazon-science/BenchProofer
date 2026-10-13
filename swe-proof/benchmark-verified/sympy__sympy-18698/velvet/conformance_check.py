#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18698 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`combineAll` /
              `combineInto`, the tag-keyed first-encounter-order collapse that
              COMBINES the values sharing a tag) transliterated to Python over
              the real repo types, via the mapping.md row bijection
              (value <-> Content = List Int of interned atom codes; tag <-> the
              integer multiplicity). The model's value carrier `Content` is the
              free monoid on atoms with `++` as product; the bridge maps each
              distinct irreducible polynomial to one atom code and `++` to
              polynomial multiplication. There are NO A-tagged ops (no axioms).
  * ORACLE  — patch.diff's behaviour: the REAL patched `sqf_list` (gold patch
              applied at base_commit by the harness, G-RESOLVE) run on a
              polynomial built from a known multiset of (irreducible, exponent)
              pairs. By the inertness of the non-grouping hunk (mapping.md §4,
              fuzz-verified) those pairs ARE the pre-grouping square-free factor
              list the changed tail consumes -- i.e. the read-only input `items`.

They must agree, as a multiset of (expanded-poly, multiplicity) pairs, on every
input. The multiset comparison is the faithful observable: the changed tail's
output is re-sorted downstream by `_sorted_factors`, so element ORDER is not
observable, only the (factor, multiplicity) content (the property the issue and
the F2P test assert). Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), sympy + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from collections import Counter
from functools import reduce
from operator import mul


SEED = 18698
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean combineAll/combineInto, transliterated -----
# Content is `List Int` (interned atom codes); the model's value product is `++`
# (list concatenation). `combineInto`/`combineAll` are copied structurally from
# Solution.lean's `pure` region, operating on (Content, tag) items.
def combineInto(m, v, k):
    """`combineInto m v k` -- match on the accumulator, combine on tag hit.

    Mirrors:
      | []            => [(v, k)]
      | (v', k') :: r => if k' = k then (v' ++ v, k') :: r
                                   else (v', k') :: combineInto r v k
    """
    if not m:
        return [(list(v), k)]
    (v0, k0), rest = m[0], m[1:]
    if k0 == k:
        return [(list(v0) + list(v), k0)] + rest
    return [(v0, k0)] + combineInto(rest, v, k)


def combineAll(items):
    """`combineAll items = items.foldl combineStep []` transliterated.

    Tag-keyed, first-encounter-order collapse that concatenates (combines) the
    values sharing a tag. Returns a list of (Content, tag)."""
    m = []
    for (v, k) in items:
        m = combineInto(m, list(v), k)
    return m


# --- the mapping.md bridge: atoms <-> irreducible polynomials -----------------
# Each distinct irreducible polynomial used to build a case is assigned a unique
# atom code (an Int). A Content (List Int) de-interns to the polynomial product
# of its atoms' polynomials -- this realises the model's `++` == multiplication.
def deintern(content, atom_to_poly):
    """Content (List Int atom codes) -> the polynomial it denotes (product)."""
    import sympy
    p = sympy.Integer(1)
    for a in content:
        p = p * atom_to_poly[a]
    return p


def shadow_report(items, atom_to_poly):
    """Run the shadow `combineAll` on the interned input `items` and project to
    the observable multiset of (expanded polynomial, multiplicity)."""
    import sympy
    grouped = combineAll(items)
    return Counter((sympy.expand(deintern(v, atom_to_poly)), k) for (v, k) in grouped)


# --- the oracle: the REAL patched sqf_list -----------------------------------
def oracle_report(expr):
    """Run the real patched `sqf_list(expr)` and project the factor list to the
    multiset of (expanded polynomial, multiplicity). Asserts the numeric coeff
    is 1 (our cases are monic products, so the modeled tail owns the whole
    factor list)."""
    import sympy
    coeff, factors = sympy.sqf_list(expr)
    assert coeff == 1, "non-unit coeff %r (case construction bug)" % (coeff,)
    return Counter((sympy.expand(f), k) for (f, k) in factors)


# --- fuzzing: products of distinct monic irreducible square-free factors ------
def _atom_bank():
    """A bank of distinct monic irreducible (hence square-free) polynomials over
    a single generator. Each is its own square-free part, so a product
    `prod base_i ** e_i` has pre-grouping square-free factor list exactly
    `[(base_i, e_i)]` -- the read-only input `items` the changed tail consumes
    (mapping.md §3.2; non-grouping hunk inertness, mapping.md §4)."""
    import sympy
    x = sympy.symbols('x')
    bank = [
        x - 1, x - 2, x - 3, x - 4, x + 1, x + 2, x + 3,
        x**2 + 1, x**2 + 2, x**2 + x + 1, x**2 + 3,
    ]
    return bank


def _gen_case(rng, bank):
    """One fuzzed scenario. Pick a subset of DISTINCT irreducibles (distinct so
    each is one square-free factor with a single multiplicity), give each a
    multiplicity, build the product. Returns (expr, items, atom_to_poly):

      * expr          -- the polynomial fed to the real patched sqf_list (oracle)
      * items         -- the interned pre-grouping list [(Content, tag)], i.e.
                         [([atom_i], e_i)] -- the model input `items`
      * atom_to_poly  -- the bridge atom-code -> polynomial

    To exercise the COMBINE-on-shared-tag behaviour (the heart of the fix), we
    deliberately allow several distinct irreducibles to share the SAME
    multiplicity: those must collapse into one (product, multiplicity) entry."""
    import sympy
    nb = rng.randint(0, 5)
    chosen = rng.sample(bank, nb) if nb <= len(bank) else list(bank)
    # multiplicities drawn from a small range so shared tags are common.
    max_mult = rng.choice([2, 3, 4])
    items = []
    atom_to_poly = {}
    expr = sympy.Integer(1)
    for idx, base in enumerate(chosen):
        e = rng.randint(1, max_mult)
        atom_to_poly[idx] = base
        items.append(([idx], e))      # Content = single atom code [idx]
        expr = expr * base**e
    return expr, items, atom_to_poly


def _boundary_cases():
    """Deterministic boundary scenarios (plan §4.1 step 4). Each is
    (expr, items, atom_to_poly)."""
    import sympy
    x = sympy.symbols('x')
    cases = []
    a2p = {}

    def mk(pairs):
        # pairs: list of (poly, mult); distinct polys interned in order.
        a2p_local = {}
        items = []
        expr = sympy.Integer(1)
        for i, (p, e) in enumerate(pairs):
            a2p_local[i] = p
            items.append(([i], e))
            expr = expr * p**e
        return expr, items, a2p_local

    # empty product -> empty factor list
    cases.append(mk([]))
    # single factor, multiplicity 1
    cases.append(mk([(x - 1, 1)]))
    # single factor, higher multiplicity
    cases.append(mk([(x - 2, 3)]))
    # TWO distinct factors sharing the SAME multiplicity 3 -> MUST collapse to
    # one (product, 3) entry. This is the exact shape of the issue's bug
    # ((x-2)**3 * (x-3)**3 -> (x**2-5x+6, 3)).
    cases.append(mk([(x - 2, 3), (x - 3, 3)]))
    # the issue polynomial's square-free structure precisely:
    # (x**2+1)**1 (x-1)**2 (x-2)**3 (x-3)**3
    cases.append(mk([(x**2 + 1, 1), (x - 1, 2), (x - 2, 3), (x - 3, 3)]))
    # three factors sharing multiplicity 2
    cases.append(mk([(x - 1, 2), (x + 1, 2), (x**2 + 1, 2)]))
    return cases


def main():
    rng = random.Random(SEED)
    bank = _atom_bank()
    disagreements = []
    count = 0

    def check(expr, items, atom_to_poly):
        nonlocal count
        count += 1
        shadow = shadow_report(items, atom_to_poly)
        oracle = oracle_report(expr)
        if shadow != oracle:
            disagreements.append((expr, dict(shadow), dict(oracle)))

    for case in _boundary_cases():
        check(*case)

    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        check(*_gen_case(rng, bank))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for expr, sh, orc in disagreements:
            print("  expr=%r\n    shadow=%r\n    oracle=%r" % (expr, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of combineByTag (combineAll/combineInto) agrees "
          "with the real patched sqf_list factor multiset on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
