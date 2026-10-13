#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16450 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's impl region transliterated to
             Python: filter the input symbols to those whose sign is undetermined
             (`is_positive is None`, the `if s.sign = none` guard), and for each
             build the surrogate's fact set as the closure of the argument
             `{positive: True}` PREPENDED ONTO the symbol's declared facts
             (`("positive", true) :: s.props`, step A4). The closure engine
             `closeProps` (step A5) is the single A-tagged callee, so the shadow
             leaves it as the REAL `Dummy(name, **arg).assumptions0` — it is NOT
             re-implemented here (A-tagged ⇒ run the real callee, mapping.md §4).
  * ORACLE — `patch.diff`'s behaviour: the REAL post-patch `posify(eq)` run on an
             expression carrying those symbols. Its returned surrogates' fact
             sets (read via `assumptions0`) are the observable the Lean model
             pins.

They must agree, per symbol, on every fuzzed input. The only computational
content the shadow adds over the oracle is the R/I refinement itself (the filter
+ the argument construction); the closure engine is shared (real on both sides),
so any disagreement is a mechanical R/I-fidelity counterexample — e.g. if the
shadow's argument construction did NOT prepend the declared facts, it would
diverge from the gold patch exactly as the prepatch does.

Runs in-container against the REAL `sympy` at base_commit (post-patch). Imports
only `sympy`. Fuzz seed pinned (mapping.md §4). Exit 0 iff zero disagreements.
"""
import random
import sys

from sympy import Symbol, Dummy, posify

SEED = 16450
N_FUZZ = 100_000

FACT_POOL = [
    "finite", "infinite", "integer", "rational", "irrational",
    "even", "odd", "real", "complex", "hermitian", "algebraic",
    "transcendental", "noninteger", "prime",
]


def shadow_surrogate_facts(sym):
    """R/I shadow for ONE symbol. Mirrors `surrogate`:
        if s.sign = none then closeProps (("positive", true) :: s.props)
        else s.props
    `s.props` ↔ sym.assumptions0; `s.sign = none` ↔ sym.is_positive is None;
    closeProps ↔ the REAL Dummy(...).assumptions0 (A-tagged callee)."""
    if sym.is_positive is None:
        arg = dict(sym.assumptions0)        # the symbol's declared facts
        arg["positive"] = True              # ("positive", true) :: props
        return dict(Dummy(sym.name, **arg).assumptions0)   # real closeProps
    return dict(sym.assumptions0)


def oracle_surrogate_facts(sym):
    """patch.diff behaviour: run the REAL posify on `sym` and read the surrogate's
    facts. posify returns (eq', rep) where rep maps surrogate -> original; for a
    single replaced symbol the surrogate is eq'. For an unreplaced symbol posify
    returns it unchanged."""
    eq2, rep = posify(sym)
    # rep maps surrogate_symbol -> original_symbol; eq2 is the (sole) surrogate.
    return dict(eq2.assumptions0)


def make_symbol(props, rng):
    """A consistent Symbol with the given declared facts, or None if SymPy rejects
    the combination (inconsistent assumptions are not real posify inputs)."""
    try:
        return Symbol(rng.choice(["x", "y", "k", "t", "w"]), **props)
    except Exception:
        return None


def fuzz_symbols(n, rng):
    # boundary: the issue reproducer + neighbours (sign-undetermined)
    for p in ({"finite": True}, {"integer": True}, {"even": True},
              {"odd": True}, {"rational": True}, {"real": True}, {},
              {"finite": True, "integer": True}, {"prime": True}):
        s = make_symbol(p, rng)
        if s is not None:
            yield s
    # a sign-DETERMINED symbol (posify leaves it alone): exercises the else-branch
    for p in ({"positive": True}, {"negative": True}, {"nonnegative": True}):
        s = make_symbol(p, rng)
        if s is not None:
            yield s
    for _ in range(n):
        k = rng.randint(1, 3)
        keys = rng.sample(FACT_POOL, k=min(k, len(FACT_POOL)))
        props = {key: rng.random() < 0.8 for key in keys}
        s = make_symbol(props, rng)
        if s is not None:
            yield s


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    skipped = 0
    for sym in fuzz_symbols(N_FUZZ, rng):
        # Both the shadow and the oracle perform the same `Dummy(name,
        # positive=True, **facts)` construction; when `positive=True` is
        # inconsistent with the declared facts SymPy raises on BOTH sides
        # identically (the partial domain of the unchanged closure engine, not
        # an R/I gap). Capture each side's outcome; a raise is a value too.
        try:
            shadow = shadow_surrogate_facts(sym)
        except Exception as e:
            shadow = ("raise", type(e).__name__)
        try:
            oracle = oracle_surrogate_facts(sym)
        except Exception as e:
            oracle = ("raise", type(e).__name__)
        # If both raised the same kind, it's a matching out-of-domain input.
        if isinstance(shadow, tuple) and shadow == oracle:
            skipped += 1
            continue
        count += 1
        if shadow != oracle:
            disagreements.append((sym, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d cases:"
              % (len(disagreements), count))
        for sym, sh, orc in disagreements:
            decl = dict(getattr(sym, "assumptions0", {}))
            print("  sym=%r declared=%r shadow=%r oracle=%r"
                  % (sym, decl, sh, orc))
        return 1
    if count == 0:
        print("G-CONF FAIL: 0 in-domain comparisons (all %d skipped)." % skipped)
        return 1
    print("G-CONF OK: R/I shadow of makeSurrogates (the is_positive-None filter + "
          "the {positive}-prepended-onto-declared-facts argument) agrees with the "
          "real post-patch posify surrogate facts on %d symbols (seed=%d; %d "
          "skipped as matching out-of-domain raises), 0 disagreements."
          % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
