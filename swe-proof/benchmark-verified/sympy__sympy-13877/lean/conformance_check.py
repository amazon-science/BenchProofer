#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-13877.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_firstNonzero` skeleton and diffs it against the REAL patched
pivot-selection routine `_find_reasonable_pivot(col,
iszerofunc=_is_zero_after_expand_mul)` from `sympy.matrices.matrices` — the
routine the gold patch newly routes Bareiss pivot selection through — over a
discrete catalogue of columns plus >=1e5 randomized symbolic columns (including
non-trivial-but-mathematically-zero entries, the case the bug manifests in).

Modeled path: choosing the first column entry that is genuinely (mathematically)
nonzero. Pre-patch the test was Python truthiness (literal-zero only); post-patch
it is `_is_zero_after_expand_mul`, i.e. `expand_mul(x) == 0`. For
integer-polynomial entries in one symbol, an expression is mathematically zero
iff it expands to the zero polynomial — exactly the Lean `isMathZero`.

Bridge (mapping.md): a Lean `col : List PExpr` <-> a Python list of sympy
expressions in one symbol `a`; the Lean `PExpr` AST <-> the sympy expression tree
built node-for-node; the Lean result `some (pos, val)` <-> the real routine's
`(pivot_offset, pivot_val, _, _)` with `pivot_offset is not None`, and `none`
<-> `pivot_offset is None`.

Exit 0 iff zero disagreements. stdlib + sympy only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5


# ---- PExpr AST (mirrors the Lean inductive) ---------------------------------
# A node is a tuple: ('const', c) | ('sym',) | ('add', a, b) | ('mul', a, b)
#                  | ('neg', a)

def addC(xs, ys):
    """Little-endian coefficient-list addition (mirrors Lean addC)."""
    if not xs:
        return list(ys)
    if not ys:
        return list(xs)
    return [xs[0] + ys[0]] + addC(xs[1:], ys[1:])


def mulC(xs, ys):
    """Polynomial convolution of coefficient lists (mirrors Lean mulC)."""
    if not xs:
        return []
    head = [y * xs[0] for y in ys]
    return addC(head, [0] + mulC(xs[1:], ys))


def eval_coeffs(e):
    """Evaluate a PExpr to its little-endian integer coefficient list
    (mirrors Lean `eval`)."""
    tag = e[0]
    if tag == 'const':
        return [e[1]]
    if tag == 'sym':
        return [0, 1]
    if tag == 'add':
        return addC(eval_coeffs(e[1]), eval_coeffs(e[2]))
    if tag == 'mul':
        return mulC(eval_coeffs(e[1]), eval_coeffs(e[2]))
    if tag == 'neg':
        return [-c for c in eval_coeffs(e[1])]
    raise ValueError("bad node " + repr(e))


def is_math_zero(e):
    """Mirrors Lean `isMathZero`: every coefficient is 0."""
    return all(c == 0 for c in eval_coeffs(e))


# ---- Python shadow of implementation_firstNonzero (post-patch R/I leg) ------

def shadow_first_nonzero(col):
    """Transliteration of implementation_firstNonzero: first index whose entry
    is mathematically nonzero, else None. Returns (pos, e) or None."""
    for i, x in enumerate(col):
        if is_math_zero(x) is False:
            return (i, x)
    return None


# ---- Bridge to sympy (real routine) -----------------------------------------

def to_sympy(e, a):
    tag = e[0]
    from sympy import Integer
    if tag == 'const':
        return Integer(e[1])
    if tag == 'sym':
        return a
    if tag == 'add':
        return to_sympy(e[1], a) + to_sympy(e[2], a)
    if tag == 'mul':
        return to_sympy(e[1], a) * to_sympy(e[2], a)
    if tag == 'neg':
        return -to_sympy(e[1], a)
    raise ValueError("bad node " + repr(e))


# ---- Random PExpr generator -------------------------------------------------

def gen_expr(rng, depth):
    if depth <= 0:
        if rng.random() < 0.5:
            return ('const', rng.randint(-4, 4))
        return ('sym',)
    r = rng.random()
    if r < 0.25:
        return ('const', rng.randint(-4, 4))
    if r < 0.40:
        return ('sym',)
    if r < 0.65:
        return ('add', gen_expr(rng, depth - 1), gen_expr(rng, depth - 1))
    if r < 0.85:
        return ('mul', gen_expr(rng, depth - 1), gen_expr(rng, depth - 1))
    return ('neg', gen_expr(rng, depth - 1))


def gen_column(rng):
    n = rng.randint(0, 5)
    col = []
    for _ in range(n):
        # bias toward producing mathematically-zero-but-nontrivial entries:
        # sometimes emit  e + (-e)  which expands to 0 yet is not literal 0.
        if rng.random() < 0.30:
            sub = gen_expr(rng, rng.randint(0, 2))
            col.append(('add', sub, ('neg', sub)))
        else:
            col.append(gen_expr(rng, rng.randint(0, 3)))
    return col


# ---- Discrete catalogue -----------------------------------------------------

ZERO = ('const', 0)
ONE = ('const', 1)
SYM = ('sym',)
# (a - a) : mathematically zero, NOT literal zero — the bug trigger.
A_MINUS_A = ('add', SYM, ('neg', SYM))
# (1 - 1) via add of consts
ONE_MINUS_ONE = ('add', ONE, ('neg', ONE))

DISCRETE = [
    [],
    [ZERO],
    [ONE],
    [SYM],
    [ZERO, SYM],
    [A_MINUS_A],                 # all math-zero -> None (pre-patch picks it!)
    [A_MINUS_A, SYM],            # skip the fake zero, pivot at index 1
    [ONE_MINUS_ONE, ONE],
    [ZERO, A_MINUS_A, ('const', 3)],
    [('mul', SYM, ZERO), SYM],   # x*0 is math-zero
    [A_MINUS_A, A_MINUS_A, ('neg', SYM)],
]


def real_pivot(col_sympy):
    """Real patched routine result, normalized to (pos, expr) | None."""
    from sympy.matrices.matrices import (_find_reasonable_pivot,
                                          _is_zero_after_expand_mul)
    pos, val, _, _ = _find_reasonable_pivot(
        col_sympy, iszerofunc=_is_zero_after_expand_mul)
    if pos is None:
        return None
    return (pos, val)


def check(col, a):
    shadow = shadow_first_nonzero(col)
    col_sympy = [to_sympy(e, a) for e in col]
    real = real_pivot(col_sympy)

    # Compare the chosen position (and the None/some disposition).
    if (shadow is None) != (real is None):
        return ("disposition", shadow, real)
    if shadow is None:
        return None
    spos, sval = shadow
    rpos, rval = real
    if spos != rpos:
        return ("position", shadow, real)
    # the value at the chosen position must be the same entry (mathematically).
    from sympy import expand_mul
    if expand_mul(to_sympy(sval, a) - rval) != 0:
        return ("value", shadow, real)
    return None


def main():
    from sympy import symbols
    a = symbols('a')
    rng = random.Random(SEED)

    fails = 0
    for col in DISCRETE:
        bad = check(col, a)
        if bad:
            fails += 1
            print("DISCRETE MISMATCH", col, bad)

    for _ in range(N_RANDOM):
        col = gen_column(rng)
        bad = check(col, a)
        if bad:
            fails += 1
            if fails <= 20:
                print("RANDOM MISMATCH", col, bad)

    if fails:
        print("status=fail disagreements=%d" % fails)
        sys.exit(1)
    print("status=pass checked=%d (discrete=%d random=%d) seed=%d" %
          (len(DISCRETE) + N_RANDOM, len(DISCRETE), N_RANDOM, SEED))
    sys.exit(0)


if __name__ == "__main__":
    main()
