#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16597.

The behaviour under specification is the set-containment THEORY of a numeric
quantity's three-valued fact table: which class memberships force which other
facts. Solution.lean models that theory DEEPLY as the predicate
`consistentTheory` and realizes the two witnessed deductions (`deduceEven`,
`deduceInfinite`) as closed fact tables. There is no opaque consumed callee.

This check refutes (does not prove) the refinement by executing the REAL
patched property-deduction engine (the very subsystem the gold patch edits) on
the same family of quantities the model abstracts, and confirming:

  ORACLE  — `patch.diff`'s behaviour: the patched library applied at
            base_commit (the real correctness oracle, G-RESOLVE).

  (1) the two witnessed deductions agree with `deduceEven` / `deduceInfinite`'s
      postconditions, enumerated so none can be silently skipped:
        * a quantity declared `even` has its boundedness fact resolve to True
          (deduceEven);
        * an unbounded real quantity has its finite / rational / integer / even
          / odd / algebraic / transcendental / irrational / composite facts all
          resolve to False and its non-integer fact to True (deduceInfinite).

  (2) every implication clause of `consistentTheory` holds in the real engine's
      deduced facts, across a wide family of seed quantities (each single
      relevant assumption, every satisfiable pair, and the numeric singletons).
      Each clause is checked at the fact level on the real deduced table — no
      value-membership proxy, no double mask.

Imports only the real `sympy` package (available in the prebuilt instance image,
the patched library). Exit 0 iff every obligation holds; any failure is a
mechanical refinement/soundness counterexample.
"""
import sys
import itertools

# Fact names carried by the model's KB record (Solution.lean `structure KB`).
PROPS = [
    "integer", "rational", "real", "finite", "even", "odd",
    "algebraic", "transcendental", "irrational", "infinite",
    "complex", "noninteger", "prime", "composite",
]


def fact(v):
    """sympy's is_* yields True / False / None; the model's trit is identical."""
    assert v is True or v is False or v is None, "unexpected fact value %r" % (v,)
    return v


def read_table(obj):
    """The real quantity's deduced fact table as a name -> trit dict (the
    record Solution.lean's KB mirrors field-for-field)."""
    return {p: fact(getattr(obj, "is_%s" % p)) for p in PROPS}


def theory_clauses(k):
    """The clauses of `consistentTheory`, each as (label, holds) evaluated on
    the real deduced table `k`. `A=T -> B=T` reads as `not A or B`."""
    def T(p):
        return k[p] is True

    def Fa(p):
        return k[p] is False

    return [
        ("integer=T -> rational=T", (not T("integer")) or T("rational")),
        ("rational=F -> integer=F", (not Fa("rational")) or Fa("integer")),
        ("rational=T -> real=T", (not T("rational")) or T("real")),
        ("rational=T -> algebraic=T", (not T("rational")) or T("algebraic")),
        ("rational=T -> finite=T", (not T("rational")) or T("finite")),
        ("real=T -> complex=T", (not T("real")) or T("complex")),
        ("algebraic=T -> complex=T", (not T("algebraic")) or T("complex")),
        ("algebraic=T -> finite=T", (not T("algebraic")) or T("finite")),
        ("even=T -> integer=T", (not T("even")) or T("integer")),
        ("odd=T -> integer=T", (not T("odd")) or T("integer")),
        ("integer=F -> even=F", (not Fa("integer")) or Fa("even")),
        ("integer=F -> odd=F", (not Fa("integer")) or Fa("odd")),
        ("even=T -> odd=F", (not T("even")) or Fa("odd")),
        ("prime=T -> integer=T", (not T("prime")) or T("integer")),
        ("composite=T -> integer=T", (not T("composite")) or T("integer")),
        ("integer=F -> prime=F", (not Fa("integer")) or Fa("prime")),
        ("integer=F -> composite=F", (not Fa("integer")) or Fa("composite")),
        ("irrational=T -> real=T", (not T("irrational")) or T("real")),
        ("irrational=T -> rational=F", (not T("irrational")) or Fa("rational")),
        ("irrational=T -> finite=T", (not T("irrational")) or T("finite")),
        ("transcendental=T -> complex=T", (not T("transcendental")) or T("complex")),
        ("transcendental=T -> algebraic=F", (not T("transcendental")) or Fa("algebraic")),
        ("transcendental=T -> finite=T", (not T("transcendental")) or T("finite")),
        ("infinite=T -> finite=F", (not T("infinite")) or Fa("finite")),
        ("finite=F -> rational=F", (not Fa("finite")) or Fa("rational")),
        ("finite=F -> algebraic=F", (not Fa("finite")) or Fa("algebraic")),
        ("finite=F -> irrational=F", (not Fa("finite")) or Fa("irrational")),
        ("finite=F -> transcendental=F", (not Fa("finite")) or Fa("transcendental")),
        ("real=T & integer=F -> noninteger=T",
         (not (T("real") and Fa("integer"))) or T("noninteger")),
        ("integer=T -> noninteger=F", (not T("integer")) or Fa("noninteger")),
    ]


def assert_closed(obj, label):
    k = read_table(obj)
    for desc, holds in theory_clauses(k):
        assert holds, (
            "THEORY VIOLATION on %s: clause %r failed; deduced table = %s"
            % (label, desc, {p: k[p] for p in PROPS}))


def main():
    from sympy import Symbol, S

    checked = 0

    # (1) witnessed deductions, enumerated -----------------------------------
    e = Symbol("e", even=True)
    assert e.is_even is True, "even seed lost"
    assert e.is_finite is True, (
        "deduceEven divergence: even quantity must be finite, got %r" % (e.is_finite,))
    checked += 1

    want_inf = {
        "infinite": True, "real": True, "finite": False,
        "rational": False, "integer": False, "even": False, "odd": False,
        "algebraic": False, "transcendental": False, "irrational": False,
        "composite": False, "noninteger": True,
    }
    for prop, want in want_inf.items():
        got = getattr(S.Infinity, "is_%s" % prop)
        assert got is want, (
            "deduceInfinite divergence: oo.is_%s must be %r, got %r"
            % (prop, want, got))
        checked += 1
    for prop, want in want_inf.items():
        if prop == "real":
            continue
        got = getattr(S.NegativeInfinity, "is_%s" % prop)
        assert got is want, (
            "deduceInfinite divergence (-oo): is_%s must be %r, got %r"
            % (prop, want, got))
        checked += 1

    # (2) closure theory over a wide family of quantities --------------------
    for sing in (S.Infinity, S.NegativeInfinity, S.Zero, S.One, S.Half,
                 S.Pi, S.Exp1, S.ImaginaryUnit):
        assert_closed(sing, repr(sing))
        checked += 1

    seed_facts = ["integer", "rational", "real", "finite", "even", "odd",
                  "algebraic", "transcendental", "irrational", "infinite",
                  "complex", "prime", "composite", "positive", "negative"]
    seeds = [{f: v} for f in seed_facts for v in (True, False)]
    for a, b in itertools.combinations(seed_facts, 2):
        for va in (True, False):
            for vb in (True, False):
                seeds.append({a: va, b: vb})

    for seed in seeds:
        try:
            sym = Symbol("s", **seed)
        except Exception:
            # an inconsistent assumption set is rejected at construction; it is
            # not a satisfiable quantity, hence not a closure obligation
            continue
        assert_closed(sym, "Symbol(%s)" % seed)
        checked += 1

    print("G-CONF OK: consistentTheory + deduceEven/deduceInfinite agree with "
          "the real patched property-deduction engine on %d observations "
          "(witnessed deductions enumerated non-skipped; closure holds on every "
          "satisfiable single+pair seed and the numeric singletons), 0 "
          "disagreements." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
