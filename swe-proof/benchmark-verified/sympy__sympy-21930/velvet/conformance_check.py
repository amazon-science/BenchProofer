#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21930 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's three impl regions
              (`tensorIndexLatex`, `bDaggerLatex`, `aDaggerLatex`),
              transliterated to Python over the real repo types via the
              mapping.md bijection (`str ↔ List Char`; `str.join` ↔ concatNames;
              `wrapGroup` = prepend '{' / append '}'). There are NO A-tagged
              callees in any impl region, so the shadow is pure R/I.
  * ORACLE  — patch.diff's behaviour: the patched `_latex` methods of
              `AntiSymmetricTensor`, `CreateBoson`, `CreateFermion` from the repo
              at base_commit with the gold patch applied (the harness applies
              patch.diff before this runs; PYTHONPATH=/testbed).

The shadow is fed the SAME inputs the real method observes — `self.symbol`,
`self.args[1..2]` names, `self.state.name` — so the comparison isolates the
formatting transformation (the patched op), not constructor canonicalization of
AntiSymmetricTensor (index sorting / sign extraction), which is unchanged
upstream behaviour outside the modeled function.

They must agree on every input. Exit 0 iff zero disagreements. Runs in-container
(prebuilt SWE-Bench image), stdlib + sympy only. Seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 21930
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean transliterated ----------------------------

def shadow_tensor(symbol, uppers, lowers):
    """tensorIndexLatex (Solution.lean) over str inputs: wrapGroup of the
    `symbol^{join(uppers)}_{join(lowers)}` rendering."""
    body = "%s^{%s}_{%s}" % (symbol, "".join(uppers), "".join(lowers))
    return "{" + body + "}"            # wrapGroup: prepend '{', append '}'


def shadow_bdagger(name):
    """bDaggerLatex (Solution.lean): wrapGroup of `b^\\dagger_{name}`."""
    body = "b^\\dagger_{%s}" % name
    return "{" + body + "}"


def shadow_adagger(name):
    """aDaggerLatex (Solution.lean): wrapGroup of `a^\\dagger_{name}`."""
    body = "a^\\dagger_{%s}" % name
    return "{" + body + "}"


# --- fuzz input generation ---------------------------------------------------

def name_pool():
    # realistic index / symbol names: single letters, greek-free ascii, digits
    return list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def rand_name(rng, pool, lo=1, hi=3):
    k = rng.randint(lo, hi)
    s = "".join(rng.choice(pool) for _ in range(k))
    return s


def main():
    from sympy import Symbol
    from sympy.physics.secondquant import (
        AntiSymmetricTensor, CreateBoson, CreateFermion,
    )

    rng = random.Random(SEED)
    pool = name_pool()
    disagreements = []
    compared = 0

    # boundary cases over the three renderers ---------------------------------
    boundary_names = ["0", "a", "i", "p", "xy", "ab1", "Z9"]
    for nm in boundary_names:
        for cls, shadow_fn in ((CreateBoson, shadow_bdagger),
                               (CreateFermion, shadow_adagger)):
            obj = cls(Symbol(nm))
            real = obj._latex(None)
            shad = shadow_fn(obj.state.name)
            compared += 1
            if real != shad:
                disagreements.append((cls.__name__, nm, shad, real))

    # tensor boundary: a few fixed index configurations
    tensor_boundary = [
        ("t", ["a"], ["i"]),
        ("t", ["a", "b"], ["i", "j"]),
        ("v", ["p"], ["q"]),
        ("F", ["a", "b", "c"], ["i", "j", "k"]),
    ]
    for sym, up, lo in tensor_boundary:
        obj = AntiSymmetricTensor(Symbol(sym),
                                  tuple(Symbol(n) for n in up),
                                  tuple(Symbol(n) for n in lo))
        if not isinstance(obj, AntiSymmetricTensor):
            continue  # constructor canonicalized to 0 / -tensor; outside model
        real = obj._latex(None)
        symbol_str = "%s" % obj.symbol
        ru = [i.name for i in obj.args[1]]
        rl = [i.name for i in obj.args[2]]
        shad = shadow_tensor(symbol_str, ru, rl)
        compared += 1
        if real != shad:
            disagreements.append(("AntiSymmetricTensor", (sym, up, lo), shad, real))

    # randomized fuzz ---------------------------------------------------------
    while compared < N_FUZZ:
        choice = rng.randint(0, 2)
        if choice == 0:
            nm = rand_name(rng, pool)
            obj = CreateBoson(Symbol(nm))
            real = obj._latex(None)
            shad = shadow_bdagger(obj.state.name)
            compared += 1
            if real != shad:
                disagreements.append(("CreateBoson", nm, shad, real))
        elif choice == 1:
            nm = rand_name(rng, pool)
            obj = CreateFermion(Symbol(nm))
            real = obj._latex(None)
            shad = shadow_adagger(obj.state.name)
            compared += 1
            if real != shad:
                disagreements.append(("CreateFermion", nm, shad, real))
        else:
            sym = rand_name(rng, pool)
            nu = rng.randint(0, 3)
            nl = rng.randint(0, 3)
            up = [rand_name(rng, pool, 1, 2) for _ in range(nu)]
            lo = [rand_name(rng, pool, 1, 2) for _ in range(nl)]
            try:
                obj = AntiSymmetricTensor(Symbol(sym),
                                          tuple(Symbol(n) for n in up),
                                          tuple(Symbol(n) for n in lo))
            except Exception:
                continue
            if not isinstance(obj, AntiSymmetricTensor):
                continue  # canonicalized away (sign / Pauli); not the model's job
            real = obj._latex(None)
            symbol_str = "%s" % obj.symbol
            ru = [i.name for i in obj.args[1]]
            rl = [i.name for i in obj.args[2]]
            shad = shadow_tensor(symbol_str, ru, rl)
            compared += 1
            if real != shad:
                disagreements.append(("AntiSymmetricTensor", (sym, up, lo), shad, real))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d comparisons:"
              % (len(disagreements), compared))
        for who, inp, sh, orc in disagreements:
            print("  %s input=%r shadow=%r oracle=%r" % (who, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of the three _latex renderers agrees with "
          "patch.diff behaviour on %d comparisons (seed=%d), 0 disagreements."
          % (compared, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
