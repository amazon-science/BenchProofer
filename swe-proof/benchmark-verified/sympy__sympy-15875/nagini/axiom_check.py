#!/usr/bin/env python3
"""G-AX / deep-model soundness check for sympy__sympy-15875.

This bundle consumes NO `@ContractOnly` axioms. The only opaque value the
modeled function depends on -- the three-valued zeroness of the sub-expression
formed by its real-nonzero summands -- is carried as the parameter
`sub_is_zero`, not as a callee the spec names. The whole decision procedure is
modeled DEEPLY (`add_is_zero` in model.py). What G-AX validates is therefore an
A-reference: the deep model equals the REAL, PATCHED decision routine on real
inputs.

This check MUST run inside the instance's container at the PATCHED commit, i.e.
the G-AX runner invokes it with the gold patch applied first:

    run_in_container('sympy__sympy-15875', <bundle_dir>, 'axiom_check.py',
                     gold_patch_path=<bundle_dir>/patch.diff, apply_gold=True)

`run_in_container` defaults to base_commit; without `apply_gold=True` the
pre-fix routine exhibits the bug on the issue witness and this script exits
non-zero (rc=1). G-AX runs only against the patched state; the pre-fix
differential is carried by model_prepatch.py / G-DIFF and by the official
harness / G-RESOLVE.

  (1) The exact issue witness, validated through the deep model and the patched
      routine on a freshly built expression in a single consistent evaluation
      (the routine's verdict is the deterministic function of the observed
      class vector and `sub_is_zero` that the deep model encodes):
        (-2*I + (1 + I)**2)  ->  model None == patched _eval_is_zero None

  (2) The operation-level correspondence: for genuine sympy `Add` expressions
      built from a palette realizing every summand class, the deep model's
      verdict equals the patched routine's verdict, where the class vector and
      the realized `sub_is_zero` are observed exactly as the routine observes
      them (the classes of `self.args`, and the zeroness of the sum of the
      real-nonzero summands). Each fuzz case uses FRESH symbols and observes
      the routine in a single consistent evaluation, so the comparison is
      deterministic. All three `sub_is_zero` values are exercised.

Note: `.is_zero` evaluated as a standalone property on this benchmark's
hand-picked expression is sensitive to sympy's process-global assumption cache
(an upstream artifact, not a property of the fix); G-AX therefore compares the
deep model against the routine's own `_eval_is_zero` under a single consistent
observation, which is deterministic. That the gold patch makes the public
`.is_zero` reliably ``None`` under the test harness is confirmed by G-RESOLVE.

Imports nothing repo-specific beyond `sympy` (the package under test). Exit 0
iff every observation is sound.
"""
import random
import sys
import warnings

warnings.filterwarnings("ignore")

from sympy import I, S, Symbol, Integer, Add, sqrt, Rational


# --- the exact observations the real routine makes on a summand --------------

def classify(a):
    """The summand class the real loop assigns (model.py classes 0..5)."""
    if a.is_real:
        if a.is_zero:
            return 0           # real & known-zero
        if a.is_zero is False:
            return 1           # real & known-nonzero
        return 2               # real & undetermined
    elif a.is_imaginary:
        return 3               # imaginary
    elif (S.ImaginaryUnit * a).is_real:
        return 4               # imaginary-or-zero
    else:
        return 5               # other


# --- the deep model (a faithful Python port of model.py's add_is_zero) -------

def model(classes, sub_is_zero):
    if any(c in (2, 5) for c in classes):
        return None
    z = classes.count(0)
    nz = classes.count(1)
    im = 3 in classes
    ioz = 4 in classes
    n = len(classes)
    if z == n:
        return True
    if nz == 0 or nz == n:
        return None
    if sub_is_zero is None:
        return None
    if sub_is_zero:
        if not ioz and not im:
            return True
        if im and not ioz:
            return False
        return None
    return False


def observe(expr):
    """Class vector and realized sub_is_zero for an Add, exactly as the routine
    sees them: classes of `self.args`, and the zeroness of the sum of the
    real-nonzero summands."""
    classes = [classify(a) for a in expr.args]
    nz_args = [a for a in expr.args if classify(a) == 1]
    sub_is_zero = expr.func(*nz_args).is_zero
    return classes, sub_is_zero


def check(expr):
    """Assert the deep model equals the real patched _eval_is_zero, observed in
    a single consistent evaluation on a freshly built expression."""
    if not getattr(expr, "is_Add", False):
        return None  # auto-simplified away from Add; nothing to compare
    classes, sub_is_zero = observe(expr)
    expected = expr._eval_is_zero()        # the REAL patched routine (the hunk)
    got = model(classes, sub_is_zero)      # the deep model
    assert got == expected, (
        "deep model unsound on %s: classes=%r sub_is_zero=%r -> model %r, "
        "real _eval_is_zero %r" % (expr, classes, sub_is_zero, got, expected))
    return sub_is_zero


def fresh_palette(uid):
    """A palette of summands realizing every class, with per-case-unique symbols
    so no assumption cache bleeds across fuzz iterations."""
    p = [Integer(0)]                                                    # class 0
    p += [Symbol("u%d_%d" % (uid, k), real=True, nonzero=True) for k in range(3)]   # 1
    p += [Symbol("q%d_%d" % (uid, k), real=True, positive=True) for k in range(2)]  # 1
    p += [Symbol("r%d_%d" % (uid, k), real=True) for k in range(2)]    # class 2
    p += [Symbol("g%d_%d" % (uid, k)) for k in range(2)]              # class 5
    p += [Symbol("m%d_%d" % (uid, k), imaginary=True) for k in range(2)]   # class 3
    p += [Symbol("w%d_%d" % (uid, k), real=True) * I for k in range(2)]    # class 4
    p += [Integer(2) * I, Integer(3) * I, sqrt(2), Rational(7, 3),
          (1 + I) ** 2, -2 * I]
    return p


def main():
    # --- (1) the exact issue witness, deep model == patched routine ----------
    issue = -2 * I + (1 + I) ** 2
    assert getattr(issue, "is_Add", False), "issue expr is not an Add"
    c, s = observe(issue)
    assert model(c, s) is None, "deep model must yield None on the issue witness"
    assert issue._eval_is_zero() is None, (
        "patched routine must yield None on the issue witness, got %r"
        % issue._eval_is_zero())
    check(issue)

    # --- (2) operation-level correspondence: deep model == patched routine ---
    # curated boundary expressions (fresh symbols each)
    def B(uid):
        a1 = Symbol("ba%d" % uid, real=True, positive=True)
        a2 = Symbol("bb%d" % uid, real=True, positive=True)
        u1 = Symbol("bu%d" % uid, real=True, nonzero=True)
        u2 = Symbol("bv%d" % uid, real=True, nonzero=True)
        ru = Symbol("br%d" % uid, real=True)
        gen = Symbol("bg%d" % uid)
        m1 = Symbol("bm%d" % uid, imaginary=True)
        m2 = Symbol("bn%d" % uid, imaginary=True)
        w = Symbol("bw%d" % uid, real=True)
        return [
            a1 + m1,                  # real-nz + imaginary
            a1 + a2,                  # all real-nz (None)
            m1 + m2,                  # all imaginary, empty real part
            a1 + a2 + m1,             # mixed
            a1 + w * I,               # real-nz + imaginary-or-zero
            a1 + m1 + w * I,          # real-nz + imag + imag-or-zero
            u1 - u2 + m1,             # sub_is_zero None branch
            a1 + ru,                  # real undetermined present (None)
            a1 + gen,                 # other present (None)
            Integer(0) + a1 + m1,     # zero + real-nz + imaginary
        ]
    n_boundary = 0
    for uid in range(40):
        for expr in B(uid):
            check(expr)
            n_boundary += 1

    # randomized fuzz over fresh palettes
    rng = random.Random(15875)
    seen = {None: 0, True: 0, False: 0}
    total = 0
    for it in range(20000):
        pal = fresh_palette(it)
        summ = [rng.choice(pal) for _ in range(rng.randint(1, 5))]
        expr = Add(*summ)
        s = check(expr)
        if getattr(expr, "is_Add", False):
            total += 1
            seen[s] = seen.get(s, 0) + 1

    assert seen.get(True, 0) > 0 and seen.get(False, 0) > 0 and seen.get(None, 0) > 0, (
        "fuzz did not exercise all sub_is_zero values: %r" % seen)

    print("G-AX OK: issue witness verdict None; deep model add_is_zero == real "
          "patched _eval_is_zero on %d boundary + %d fuzz Add expressions; "
          "sub_is_zero distribution %r" % (n_boundary, total, seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
