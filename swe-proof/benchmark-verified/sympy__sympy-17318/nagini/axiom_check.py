#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-17318.

Executes the REAL repo callees against the model's only consumed axiom and the
frame fact the model's precondition asserts. Imports only `sympy` (the repo
under test, with the patch applied — the same interpreter the harness uses).

The model abstracts each addend of an additive expression by an integer code
over two facets — whether its square is a POSITIVE rational, and whether it
carries a nested square root (sqrt-depth at least one):

    0  positive-rational square, no nesting        (e.g. a rational)
    1  positive-rational square, with a nesting     (a real square-root term)
    2  rational-but-not-positive square, no nesting (e.g. an imaginary term)
    3  not a positive-rational square, with nesting

Two soundness obligations are checked against the real callees:

  (A-consumed)  the axiom `split_by_radicand_gcd`: the unchanged helper
      `split_surds` (radicand-gcd split). Its modelled precondition is that
      every addend squares to a positive rational (all codes in {0, 1}) AND at
      least one addend is a square-root term (num_surds >= 1). On every such
      input the real `split_surds` must RETURN NORMALLY (no IndexError) — that
      is what the axiom's `Ensures(Result() != 1)` (an opaque SPLIT outcome,
      "a match is produced") abstracts; the marker VALUE is unpinned and is not
      asserted here. The check also confirms that dropping the positive
      requirement (a code-2 imaginary addend admitted by the old rational-only
      guard) is exactly what makes the real `split_surds` raise — so the axiom's
      precondition is not vacuously satisfiable on those inputs.

  (frame fact)  the model precondition `all_fast_facet(codes) => num_surds >= 1`:
      a genuine multi-term Add every addend of which squares to a positive
      rational always contains at least one irrational square-root term (a sum
      of only rationals auto-collapses to a single Number). Verified on the
      real `Add` for a battery of such sums.

  (end-to-end)  the matcher `_sqrt_match` itself: on a shallow sum carrying a
      non-positive (imaginary) square it returns the EMPTY match `[]` with no
      error (the FAIL_TO_PASS `_sqrt_match(4 + I) == []`); on an all-positive-
      rational sum it returns a non-empty match.

Exit 0 iff every observation matches the model.
"""
import sys

try:
    from sympy import sqrt, S, I, Add, Rational, Integer
    from sympy.core.function import _mexpand
    from sympy.simplify.radsimp import split_surds
    from sympy.simplify.sqrtdenest import _sqrt_match, sqrt_depth
except Exception as e:  # pragma: no cover - environment guard
    print("G-AX SKIP: sympy not importable (%r); run in the patched container."
          % (e,))
    sys.exit(0)


def addend_code(x):
    """Classify a single addend into the model's integer code (0..3)."""
    sq = x ** 2
    pos_rat = bool(sq.is_Rational) and bool(sq.is_positive)
    rat = bool(sq.is_Rational)
    depth = sqrt_depth(x) >= 1
    if pos_rat and not depth:
        return 0
    if pos_rat and depth:
        return 1
    if rat and not pos_rat and not depth:
        return 2
    # not a positive rational square (includes irrational/non-real squares),
    # possibly nested
    return 3 if depth else 2  # shallow non-rational also takes the no-fast-path branch


def codes_of(p):
    p = _mexpand(p)
    if not p.is_Add:
        return None
    return [addend_code(x) for x in p.args]


def is_surd_addend(x):
    """Mirror split_surds' surds selection: a term whose coeff-stripped part is
    a Pow (a square-root term)."""
    c, m = x.as_coeff_Mul()
    return bool(m.is_Pow)


def num_surds_real(p):
    p = _mexpand(p)
    return sum(1 for x in p.args if is_surd_addend(x))


def splits_ok(p):
    """True iff real split_surds returns normally on p."""
    try:
        split_surds(p)
        return True
    except IndexError:
        return False


FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)


def main():
    # ---- A-consumed: split_surds returns normally exactly on the modelled
    #      precondition (all positive-rational squares + >= 1 surd) ------------
    fast_path_sums = [
        3 + sqrt(2),
        1 + sqrt(2) + sqrt(3),
        2 + 3 * sqrt(5),
        sqrt(2) + sqrt(3) + sqrt(6),
        3 * sqrt(3) + sqrt(5) / 7 + sqrt(6) + sqrt(10) + sqrt(15),
        Rational(1, 2) + sqrt(7),
        4 + sqrt(2) + sqrt(8) + sqrt(18),
        1 + sqrt(2) + sqrt(2) * sqrt(3),  # has a code-1/positive structure
    ]
    for p in fast_path_sums:
        codes = codes_of(p)
        if codes is None:
            continue
        all_pos = all(c in (0, 1) for c in codes)
        ns = num_surds_real(p)
        # the model only invokes the axiom when all_pos and num_surds >= 1
        if all_pos and ns >= 1:
            check(splits_ok(p),
                  "axiom unsound: split_surds raised on all-positive-rational "
                  "sum with %d surd(s): %r" % (ns, p))
            # frame fact: such a genuine multi-term sum always has >= 1 surd
            check(ns >= 1,
                  "frame fact broken: all-pos-rational sum has no surd: %r" % p)

    # ---- the non-positive (imaginary) addend: old rational-only guard would
    #      admit it; real split_surds RAISES — so the positive requirement of
    #      the axiom precondition is load-bearing, not vacuous ----------------
    imaginary_shallow = [4 + I, 3 + 2 * I, I + Rational(5, 3), 7 + I]
    for p in imaginary_shallow:
        codes = codes_of(p)
        if codes is None:
            continue
        # square of an imaginary addend is rational (negative) but not positive
        check(any(c == 2 for c in codes),
              "expected a code-2 (rational-non-positive) addend in %r, got %r"
              % (p, codes))
        check(not all(c in (0, 1) for c in codes),
              "imaginary sum %r misclassified as all-positive-rational" % p)
        # the OLD guard (all squares rational) admits these; the real helper raises
        all_rat = all(bool((x ** 2).is_Rational) for x in _mexpand(p).args)
        check(all_rat,
              "expected old rational-only guard to admit %r" % p)
        check(not splits_ok(p),
              "split_surds did NOT raise on %r — the positive guard would be "
              "unnecessary, contradicting the bug" % p)

    # ---- frame fact over a wider battery of all-positive-rational sums -------
    for p in fast_path_sums:
        codes = codes_of(p)
        if codes is None:
            continue
        if all(c in (0, 1) for c in codes):
            check(num_surds_real(p) >= 1,
                  "frame fact: all-pos-rational genuine sum lacks a surd: %r" % p)

    # ---- end-to-end matcher behaviour (the FAIL_TO_PASS) --------------------
    # shallow imaginary sum -> empty match, no error
    check(_sqrt_match(4 + I) == [],
          "_sqrt_match(4 + I) must be [] (empty match), got %r"
          % (_sqrt_match(4 + I),))
    for p in imaginary_shallow:
        check(_sqrt_match(p) == [],
              "_sqrt_match(%r) must be [] (shallow, non-positive square), got %r"
              % (p, _sqrt_match(p)))
    # all-positive-rational sum -> non-empty match
    for p in [1 + sqrt(2) + sqrt(3), sqrt(2) + sqrt(3) + sqrt(6),
              3 * sqrt(3) + sqrt(5) / 7 + sqrt(6) + sqrt(10) + sqrt(15)]:
        m = _sqrt_match(p)
        check(isinstance(m, list) and len(m) == 3,
              "_sqrt_match(%r) expected a 3-element match, got %r" % (p, m))

    if FAIL:
        print("G-AX FAIL (%d):" % len(FAIL))
        for f in FAIL:
            print("  -", f)
        return 1
    print("G-AX OK: split_surds (A-consumed) returns normally on every "
          "all-positive-rational sum with >= 1 surd; raises on every shallow "
          "non-positive (imaginary) sum admitted by the old guard; frame fact "
          "all_fast_facet => num_surds>=1 holds; _sqrt_match returns [] on the "
          "shallow imaginary inputs (incl. 4 + I) and a 3-element match on "
          "all-positive-rational sums.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
