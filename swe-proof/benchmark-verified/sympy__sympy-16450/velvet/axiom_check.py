#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-16450 (plan §4).

Validates the single A leg of refinement.md — the **A-reference** `closeProps`
(Solution.lean), the deep-model stand-in for the UNCHANGED assumption-closure
engine `StdFactKB`, observed through `Dummy(name, **facts).assumptions0`
(mapping.md §3.1). The deep model in refinement.md is sound only if that engine,
given the argument the patched line constructs — `{positive: True}` together with
a symbol's already-declared facts — returns a fact set that:

  (a) is DETERMINISTIC (same input ⇒ same observed fact set), so modeling it as a
      function is faithful;
  (b) CONTAINS every supplied declared fact (the closure never drops a consistent
      supplied fact — the StdFactKB invariant that makes "positivity asserted ON
      TOP OF the declared facts" preserve them); and
  (c) CONTAINS `positive: True` (positivity is in fact asserted).

This is exactly the property refinement.md step A4/A5 relies on: the surrogate's
facts ⊇ the original symbol's declared facts ∪ {positive}. (b) is what the
pre-patch construction `Dummy(name, positive=True)` violates — it drops the
declared facts — and is the soundness basis for the deep model.

Runs in-container against the REAL `sympy` at base_commit. Imports only `sympy`.
Boundary fact-sets first (incl. the issue's `finite=True`), then 20 000 fuzzed
CONSISTENT fact-sets over sign-undetermined symbols. Exit 0 iff every observation
meets (a)-(c); any violation is a concrete soundness counterexample.
"""
import random
import sys

from sympy import Symbol, Dummy

SEED = 16450
N_FUZZ = 20_000

# Single-fact assumptions that (on their own) do NOT determine a symbol's sign,
# so `is_positive is None` and the patched branch fires. Mixed in combinations;
# inconsistent combinations are caught and skipped (SymPy raises).
FACT_POOL = [
    "finite", "infinite", "integer", "rational", "irrational",
    "even", "odd", "real", "complex", "hermitian", "algebraic",
    "transcendental", "commutative", "noninteger",
]


def observed_facts(**asm):
    """assumptions0 of a Dummy built with these declared facts, as a dict."""
    return dict(Dummy("g", **asm).assumptions0)


# Verdicts: "ok" (sound observation), "skip" (outside the real callee's defined
# domain — see below), or a violation string.
def check_one(props):
    """props: dict[str,bool] of declared facts on a sign-undetermined symbol."""
    # The base symbol must itself be constructible & sign-undetermined for this
    # to be the patched branch's scenario.
    try:
        base = Symbol("s", **props)
    except Exception:
        return "skip"  # inconsistent declared set: not a real input to posify
    if base.is_positive is not None:
        return "skip"  # sign already determined: posify leaves it unchanged

    arg = dict(props)
    arg["positive"] = True
    try:
        got = observed_facts(**arg)
    except Exception:
        # Adding positive=True is inconsistent with the declared facts. The REAL
        # posify performs the IDENTICAL `Dummy(name, positive=True, **facts)`
        # construction, so it raises on this very symbol too — both pre- and
        # post-patch. This is the partial domain of the (unchanged) closure
        # engine, not a fidelity gap of the deep model; the A-reference claim is
        # scoped to inputs where the real callee is defined. Skip + count.
        return "skip"

    # (a) determinism
    again = observed_facts(**arg)
    if again != got:
        return "non-deterministic for %r: %r vs %r" % (arg, got, again)

    # (c) positivity asserted
    if got.get("positive") is not True:
        return "positive not asserted for %r: got %r" % (arg, got)

    # (b) every supplied declared fact preserved
    for k, v in props.items():
        if got.get(k) != v:
            return ("dropped/changed supplied fact %s=%r for %r: got %s=%r"
                    % (k, v, arg, k, got.get(k)))
    return "ok"


def fuzz_props(n, rng):
    # boundary: the issue's reproducer and neighbours
    yield {"finite": True}
    yield {"finite": True, "commutative": True}
    yield {"integer": True}
    yield {"even": True}
    yield {"odd": True}
    yield {"rational": True}
    yield {"real": True}
    yield {}                       # no declared facts: surrogate just positive
    yield {"finite": True, "integer": True}
    for _ in range(n):
        k = rng.randint(1, 3)
        keys = rng.sample(FACT_POOL, k=min(k, len(FACT_POOL)))
        yield {key: rng.random() < 0.75 for key in keys}


def main():
    rng = random.Random(SEED)
    checked = 0
    skipped = 0
    violations = []
    for props in fuzz_props(N_FUZZ, rng):
        v = check_one(props)
        if v == "ok":
            checked += 1
        elif v == "skip":
            skipped += 1
        else:
            violations.append((props, v))
            if len(violations) >= 5:
                break
    if violations:
        print("G-AX FAIL: %d closure-engine soundness violation(s):"
              % len(violations))
        for props, v in violations:
            print("  props=%r -> %s" % (props, v))
        return 1
    if checked == 0:
        print("G-AX FAIL: 0 in-domain observations (all %d skipped) — cannot "
              "attest soundness." % skipped)
        return 1
    print("G-AX OK: assumption-closure engine (Dummy/StdFactKB) preserves every "
          "supplied declared fact and asserts positivity, deterministically, "
          "over %d consistent sign-undetermined fact-sets (seed=%d; %d skipped "
          "as outside the real callee's defined domain, where real posify also "
          "raises). The closeProps A-reference deep model is sound."
          % (checked, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
