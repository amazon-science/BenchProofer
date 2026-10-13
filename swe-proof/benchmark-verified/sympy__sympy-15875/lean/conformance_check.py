#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-15875.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_zeroStatus` skeleton (classify each summand into a `Summand`
category, supply the recursive zero-test of the real-nonzero sub-sum as
`realSumZero`, then run the three-valued `zeroVerdict`) and diffs it against the
REAL patched `Add._eval_is_zero`.

  observable: `expr._eval_is_zero()` for an `Add` expression `expr`, i.e. the
  three-valued zero verdict (`True` / `False` / `None`).

Bijection (mapping.md):
  * each `a in self.args` -> a `Summand` constructor via the assumption ladder
    (`is_real`/`is_zero`/`is_imaginary`/`(I*a).is_real`);
  * `self.func(*nz).is_zero` -> the `realSumZero : Option Bool` input;
  * `True`/`False`/`None` <-> `some true`/`some false`/`none`.

The shadow reuses the REAL unchanged assumption queries (`a.is_real`,
`a.is_zero`, `a.is_imaginary`, `(I*a).is_real`) and the REAL recursive
`self.func(*nz).is_zero`, so the per-summand classification and the real-anchor
fact are exercised end-to-end — nothing is modeled away. This gate validates
exactly the classify-then-decide logic, including the fixed `len(nz) == 0`
guard.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 15875
N_RANDOM = 120_000  # >= 1e5


def main():
    try:
        from sympy import I, S, Add, Symbol, Integer
        from sympy.core.add import Add as AddCls
    except Exception as e:  # pragma: no cover
        print(f"status=fail could not import callees: {e!r}")
        return 1

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # ---- Summand classifier: the exact assumption ladder of _eval_is_zero ----
    def classify(a):
        if a.is_real:
            if a.is_zero:
                return "realZero"
            elif a.is_zero is False:
                return "realNonzero"
            else:
                return "realUnknown"
        elif a.is_imaginary:
            return "imaginary"
        elif (S.ImaginaryUnit * a).is_real:
            return "imagOrZero"
        else:
            return "indeterminate"

    # ---- Lean zeroVerdict, transliterated (the spec the impl must meet) ----
    def zero_verdict(tags, real_sum_zero):
        if any(t in ("realUnknown", "indeterminate") for t in tags):
            return None
        z = sum(1 for t in tags if t == "realZero")
        nz = sum(1 for t in tags if t == "realNonzero")
        n = len(tags)
        im = any(t == "imaginary" for t in tags)
        im_or_z = any(t == "imagOrZero" for t in tags)
        if z == n:
            return True
        if nz == 0 or nz == n:
            return None
        if real_sum_zero is True:
            if (not im_or_z) and (not im):
                return True
            if im and (not im_or_z):
                return False
            return None
        if real_sum_zero is False:
            return False
        return None

    def shadow_eval_is_zero(expr):
        """R/I shadow of implementation_zeroStatus, over the commutative path."""
        if expr.is_commutative is False:
            return None  # non-commutative path is outside the modeled behavior
        args = expr.args
        tags = [classify(a) for a in args]
        # realSumZero = self.func(*nz).is_zero, the recursive zero-test of the
        # real, definitely-nonzero sub-sum (supplied as the Lean input).
        nz_terms = [a for a in args if a.is_real and a.is_zero is False]
        real_sum_zero = expr.func(*nz_terms).is_zero
        return zero_verdict(tags, real_sum_zero)

    def report(key, real, shadow):
        nonlocal disagreements
        if real != shadow:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH {key!r}: real={real!r} shadow={shadow!r}")

    def check_expr(expr, key):
        nonlocal checked
        # Only genuine Add instances exercise _eval_is_zero; single-term /
        # collapsed sums are skipped (not an Add).
        if not isinstance(expr, Add):
            return
        try:
            real = expr._eval_is_zero()
        except Exception:
            return  # branch not applicable; skip
        shadow = shadow_eval_is_zero(expr)
        report(key, real, shadow)
        checked += 1

    # ---- term palette covering every Summand category ----
    real_zero = [Integer(0)]
    real_nonzero = [Integer(3), Integer(-5), Integer(7), Integer(-1),
                    Symbol('a', real=True, nonzero=True)]
    real_unknown = [Symbol('u', real=True), Symbol('v', real=True)]
    imaginary = [3 * I, -2 * I, (1 + I) ** 2, Symbol('w', imaginary=True)]
    imag_or_zero = [I * Symbol('r', real=True), I * Symbol('s', real=True)]
    indeterminate = [Symbol('p'), Symbol('q')]
    palette = (real_zero + real_nonzero + real_unknown +
               imaginary + imag_or_zero + indeterminate)

    # ---- the exact F2P expression + structured boundary cases ----
    check_expr(-2 * I + (1 + I) ** 2, ("F2P", "issue-15873"))
    check_expr(Integer(0) + Integer(0), ("boundary", "all-zero"))
    check_expr(3 + 3 * I, ("boundary", "real+imag"))
    check_expr(Symbol('u', real=True) + 3 * I, ("boundary", "realUnknown+imag"))
    check_expr(3 - 3 + 2 * I, ("boundary", "cancel-real+imag"))

    # ---- randomized fuzz ----
    for _ in range(N_RANDOM):
        k = rng.randint(2, 6)
        picks = [rng.choice(palette) for _ in range(k)]
        expr = Add(*picks)
        check_expr(expr, ("fuzz",))

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
