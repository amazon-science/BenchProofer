#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-16450.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_posify` skeleton and diffs it against the REAL patched
`sympy.simplify.simplify.posify` over a discrete catalogue of assumption sets
plus >=1e5 randomized symbol collections.

Modeled case: the scalar branch of `posify` — for every free symbol whose sign
is undetermined (`is_positive is None`), `posify` substitutes a fresh positive
dummy declared with the original symbol's full property set augmented by
positivity (`positive=True, **s.assumptions0`); the observable is each
replacement's `assumptions0` (full inferred property record).

Bridge (mapping.md):
  Lean `Assumptions = List (String × Bool)`      <->  a symbol's `assumptions0` dict
  Lean `signUndetermined a` (`positive` absent)  <->  `s.is_positive is None`
  Lean `assertPositive a` (`("positive",true)::a`) <-> `positive=True, **assumptions0`
                                                       (the leading pair is the
                                                       explicit keyword, the tail
                                                       is the splatted record)
  Lean `declAccepted decl`                      <->  whether the call
                                                       `Dummy(name, **decl)`
                                                       COMPLETES (a total probe:
                                                       "no" is an answer)
  Lean `resolveAssumptions decl h`              <->  `Dummy(name, **decl).assumptions0`
                                                       (A-reference: the real callee,
                                                       applicable only where the
                                                       probe answered yes)
  Lean `result : Option (List Assumptions)`      <->  the replacement records, or
                                                       the `posify` call RAISING

The Lean spec pins DEFINEDNESS as well as value, so this check is BIDIRECTIONAL
and asserts both halves at every case:

  * model says `some records`  =>  the real `posify` must RETURN, and its
    replacement records must equal `records` as a MULTISET (free_symbols order /
    dummy names are not observable);
  * model says `none`          =>  the real `posify` must RAISE.

Nothing is skipped on an exception from `posify`: a raise is one of the two
outcomes the model predicts, so swallowing it would hide exactly the disagreement
this check exists to find. (Only a case whose INPUT SYMBOL cannot be built at all
is skipped — there is then no `assumptions0` to feed the model — and those are
counted and reported.)

Coverage is asserted, not hoped for. The run FAILS unless it exercised, with
agreement, at least one case of each of:
  * `raise` — a kept (sign-undetermined) symbol whose augmented declaration is
    not one the inference has a record for, where the whole call has no value;
  * `off-filter-rejected` — a sign-DETERMINED symbol whose augmented declaration
    would NOT be accepted (its record already states `positive`, so the call
    would receive that keyword twice), in a case where the real `posify` still
    returns: the acceptance of a declaration formed from a symbol that is not
    replaced does not influence definedness;
  * `valued` — an ordinary case where the call returns.

Exit 0 iff zero disagreements and every coverage class was hit. stdlib + sympy
only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5

# Assumption keys that are valid as Symbol kwargs and exercise the inference
# closure (sign, reality, finiteness, integrality, parity, primality, …).
KEYS = [
    "finite", "infinite", "integer", "rational", "irrational", "prime",
    "composite", "even", "odd", "positive", "negative", "nonnegative",
    "nonpositive", "nonzero", "zero", "real", "complex", "imaginary",
    "hermitian", "commutative", "algebraic", "transcendental",
]


def freeze(d):
    """Canonical hashable form of an assumptions0 dict."""
    return tuple(sorted(d.items()))


# ---- the two A-reference legs, as the real callee ---------------------------

def probe_decl(a):
    """`declAccepted (assertPositive a)` and, where accepted, the record
    `resolveAssumptions (assertPositive a) h`.

    The declaration is presented exactly as the modeled call presents it — the
    positivity assertion as the explicit keyword, the symbol's own record
    splatted after it — so a record that already states `positive` supplies that
    keyword twice and the call does not complete. Returns `(accepted, record)`.
    """
    from sympy import Dummy
    try:
        d = Dummy("x", positive=True, **a)
    except Exception:
        return False, None
    return True, freeze(d.assumptions0)


# ---- Python shadow of problem_spec_posify / implementation_posify -----------

def shadow_posify(sym_assumptions):
    """Transliteration of the modeled behaviour.

    `sym_assumptions` is a list of dicts (each a symbol's assumptions0). Returns
    the sorted multiset of replacement records, or None when the modeled
    behaviour has no value (some KEPT symbol's augmented declaration is not one
    the inference has a record for).
    """
    out = []
    for a in sym_assumptions:
        # signUndetermined a  <->  'positive' not in assumptions0
        if "positive" not in a:
            accepted, record = probe_decl(a)
            if not accepted:
                return None
            out.append(record)
    return sorted(out)


# ---- real callee observation ------------------------------------------------

def real_posify(symbols):
    """Run the REAL patched `posify` on the sum of `symbols`. Returns the sorted
    multiset of replacement dummies' `assumptions0` records, or None when the
    call has no value (it raises)."""
    from sympy import posify, Add
    expr = Add(*symbols) if len(symbols) != 1 else symbols[0]
    try:
        _, rep = posify(expr)
    except Exception:
        return None
    # rep maps {replacement_dummy: original_symbol}
    return sorted(freeze(d.assumptions0) for d in rep.keys())


def main():
    from sympy import Symbol

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0
    unbuildable = 0
    cover = {"valued": 0, "raise": 0, "off-filter-rejected": 0}

    def rand_assumption_kwargs():
        """A small kwargs dict. Sympy rejects some inconsistent combos when the
        SYMBOL itself is built (raises) — those inputs do not exist, so they are
        counted and skipped; every combination that yields a symbol is checked."""
        ks = rng.sample(KEYS, rng.randint(0, 3))
        return {k: rng.choice([True, False]) for k in ks}

    cases = []  # list of lists of kwargs dicts (one per symbol in an expr)

    # discrete catalogue: the issue's case, single-key declarations, the
    # declarations whose augmentation with positivity has no record, and mixtures
    # of replaced with not-replaced symbols.
    discrete = [
        [{"finite": True}],                       # the F2P test case (issue 16438)
        [{"finite": False}],
        [{}],                                     # plain symbol
        [{"integer": True}],
        [{"rational": True}],
        [{"even": True}],
        [{"odd": True}],
        [{"prime": True}],                        # inferred-positive -> NOT replaced
        [{"negative": True}],                     # positive known-false -> NOT replaced
        [{"positive": True}],                     # positive known-true -> NOT replaced
        [{"real": True}],
        [{"commutative": False}],
        [{"finite": True}, {"integer": True}, {}],   # multi-symbol expr
        [{"finite": True}, {"positive": True}],
        # sign-undetermined symbols whose AUGMENTED declaration has no record
        # (positivity cannot hold together with the symbol's own properties), so
        # the modeled behaviour has no value at all:
        [{"rational": False, "irrational": False}],
        [{"irrational": False, "algebraic": False}],
        [{"irrational": False, "transcendental": True}],
        [{"algebraic": False, "transcendental": False}],
        # sign-DETERMINED symbols (not replaced), whose augmented declaration
        # would state `positive` twice and so would not be accepted either:
        [{"real": False}],
        [{"imaginary": True}],
        [{"nonpositive": True}],
        [{"zero": True}],
        # a valueless symbol mixed with one that is not replaced, and with one
        # that is:
        [{"rational": False, "irrational": False}, {"positive": True}],
        [{"rational": False, "irrational": False}, {"finite": True}],
        [{"finite": True}, {"algebraic": False, "transcendental": False}],
    ]
    cases.extend(discrete)

    for _ in range(N_RANDOM):
        n = rng.randint(1, 4)
        cases.append([rand_assumption_kwargs() for _ in range(n)])

    for case in cases:
        symbols = []
        sym_assumptions = []
        bad = False
        for idx, kw in enumerate(case):
            try:
                s = Symbol("s%d" % idx, **kw)
                a = s.assumptions0
            except Exception:
                bad = True
                break
            symbols.append(s)
            sym_assumptions.append(a)
        if bad or not symbols:
            unbuildable += 1
            continue

        exp = shadow_posify(sym_assumptions)
        got = real_posify(symbols)
        checked += 1

        if exp is None:
            cover["raise"] += 1
        else:
            cover["valued"] += 1
            # a sign-DETERMINED symbol whose augmented declaration would be
            # refused, in a case the model still says has a value
            if any("positive" in a and not probe_decl(a)[0] for a in sym_assumptions):
                cover["off-filter-rejected"] += 1

        if exp != got:
            disagreements += 1
            if disagreements <= 5:
                kind = ("model=no-value real=returned" if exp is None else
                        "model=valued real=no-value" if got is None else
                        "records differ")
                print("MISMATCH (%s) kwargs=%r: real=%r shadow=%r"
                      % (kind, case, got, exp))

    print("checked=%d unbuildable_inputs=%d disagreements=%d coverage=%r"
          % (checked, unbuildable, disagreements, cover))

    missing = [k for k, v in cover.items() if v == 0]
    if disagreements == 0 and not missing:
        print("status=pass conformance OK (%d checks, 0 disagreements, "
              "value AND definedness both asserted, coverage %r)" % (checked, cover))
        return 0
    if missing:
        print("status=fail coverage class(es) never exercised: %r" % missing)
        return 1
    print("status=fail %d disagreement(s)" % disagreements)
    return 1


if __name__ == "__main__":
    sys.exit(main())
