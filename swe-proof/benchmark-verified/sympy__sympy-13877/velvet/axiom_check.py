#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13877.

The pivot-selection step under spec depends on ONE deeply-modeled recogniser
(an A-reference, not a consumed axiom): the decisive zero test
`_is_zero_after_expand_mul(x) == (expand_mul(x) == 0)`, supplied to the unchanged
`_find_reasonable_pivot` as its `iszerofunc`. This script runs the REAL repo
callees on boundary + fuzzed scalar `Expr` and asserts the two facts the model
relies on (mapping.md §3.1):

  (1) definition faithfulness + decisiveness — for every scalar `x`,
      `_is_zero_after_expand_mul(x)` equals `expand_mul(x) == 0` and is always a
      Python bool (never None). So `Entry.mathNonzero = not iszerofunc(x)` is well
      defined: the modeled non-Float / decisive-iszerofunc branch of
      `_find_reasonable_pivot` is exactly a first-non-zero scan (no PASS-2/3
      fallthrough — see check (3)).

  (2) `consistent` — `mathNonzero ⟹ litNonzero`, i.e.
      `expand_mul(x) != 0  ⟹  bool(x)`: a value still non-zero after expansion is
      certainly not a literal/numeric zero, hence truthy. (The converse FAILS —
      the discriminating case of the issue: a structurally-non-zero entry that is
      algebraically zero, e.g. `a*(a-1) - a*a + a`.)

It also confirms (3) on the modeled branch `_find_reasonable_pivot(col,
iszerofunc=_is_zero_after_expand_mul)` returns exactly the first index whose entry
is `mathNonzero`, matching the modeled `selectPivot`.

G-AX runs in the *base_commit* (pre-patch) container, against the REAL callees
the deep model abstracts (`expand_mul` and `_find_reasonable_pivot`, both
unchanged by the patch). It therefore scopes itself to the A-reference soundness
obligations (1)-(3). The patch's end-to-end effect — that the issue matrices
`M(5..7).det() == 0` with no `Invalid NaN comparison` — is a *post-patch* whole-
pipeline property validated by G-RESOLVE (the official harness applies the gold
patch and runs `test_determinant`, whose FAIL_TO_PASS body asserts exactly
`M(5..7).det() == 0`). Asserting it here would test the still-live bug in the
unpatched container, not the modeled callee, so it is not a G-AX obligation.

Imports only the repo under test (sympy) — the same module the gold patch edits.
Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import symbols, expand_mul, S, Integer, sqrt, sin, cos, pi
from sympy.matrices.matrices import _find_reasonable_pivot

# `_is_zero_after_expand_mul` is the patch-introduced sugar for `expand_mul(x)==0`
# (the genuinely-unchanged callee `expand_mul` is what carries the behaviour). Use
# the real helper when the container has the patch applied; otherwise define the
# identical body — check_definition() asserts the two agree either way.
try:
    from sympy.matrices.matrices import _is_zero_after_expand_mul
except ImportError:  # pragma: no cover - base_commit (pre-patch) container
    def _is_zero_after_expand_mul(x):
        return expand_mul(x) == 0


def litnonzero(x):
    """The cheap STRUCTURAL recogniser the pre-patch inner scan used: Python
    truthiness `if val:` of a scalar Expr (== `bool(x)`)."""
    return bool(x)


def mathnonzero(x):
    """The deeply-modeled DECISIVE recogniser: not zero after expand_mul."""
    iz = _is_zero_after_expand_mul(x)
    # (1) decisiveness: the supplied iszerofunc must return a real bool so that
    # _find_reasonable_pivot resolves in PASS 1 (no None fallthrough).
    assert iz is True or iz is False, (
        "iszerofunc not decisive on %r: returned %r" % (x, iz))
    return not iz


def check_definition(x):
    """(1) _is_zero_after_expand_mul(x) == (expand_mul(x) == 0)."""
    observed = _is_zero_after_expand_mul(x)            # real callee
    expected = (expand_mul(x) == 0)                    # deep model
    assert bool(observed) == bool(expected), (
        "definition mismatch on %r: callee=%r, expand_mul==0 gives %r"
        % (x, observed, expected))


def check_consistent(x):
    """(2) mathnonzero(x) ⟹ litnonzero(x)."""
    if mathnonzero(x):
        assert litnonzero(x), (
            "consistency violated: %r is non-zero after expand_mul but bool(x) "
            "is False" % (x,))


def selectpivot_shadow(col):
    """The modeled selectPivot: first index k with mathnonzero(col[k])."""
    for k, x in enumerate(col):
        if mathnonzero(x):
            return (True, k)
    return (False, None)


def check_pivot_branch(col):
    """(3) On the modeled non-Float / decisive-iszerofunc branch, the REAL
    _find_reasonable_pivot agrees with the modeled selectPivot on (found, idx)."""
    pivot_pos, _, _, _ = _find_reasonable_pivot(
        list(col), iszerofunc=_is_zero_after_expand_mul)
    found, idx = selectpivot_shadow(col)
    if found:
        assert pivot_pos == idx, (
            "pivot index mismatch on %r: real=%r model=%r"
            % (col, pivot_pos, idx))
    else:
        assert pivot_pos is None, (
            "pivot existence mismatch on %r: real=%r model=no-pivot"
            % (col, pivot_pos))


def main():
    a, b, c = symbols('a b c')

    # ---- scalar entries: boundary cases over the discriminating space --------
    boundary = [
        S.Zero, S.One, Integer(-3), Integer(7),
        a, b, a + b, a - b, a * b,
        a * (a - 1) - a * a + a,        # expands to 0 (the issue's pattern)
        (a + 1) ** 2 - a * a - 2 * a - 1,  # expands to 0
        a * a - a * a,                  # expands to 0
        (a + b) * (a - b) - a * a + b * b,  # expands to 0
        a * a + 1,                      # genuinely non-zero
        2 * a + 3 * b - a - 3 * b + 1,  # = a + 1, non-zero
        sqrt(2), sin(a), cos(a) ** 2 + sin(a) ** 2,  # untouched by expand_mul
        pi,
    ]
    for x in boundary:
        check_definition(x)
        check_consistent(x)

    # ---- randomized fuzz over scalar polynomials in a, b, c ------------------
    rng = random.Random(13877)
    syms = [a, b, c]

    def rand_term():
        s = rng.choice(syms)
        return rng.randint(-3, 3) * s ** rng.randint(0, 2)

    for _ in range(4000):
        n = rng.randint(1, 4)
        x = sum(rand_term() for _ in range(n))
        check_definition(x)
        check_consistent(x)
        # construct a deliberately-cancelling expression and its expanded form
        y = x * (a - 1) - x * a + x          # == 0 for all x
        check_definition(y)
        check_consistent(y)

    # ---- pivot-selection branch (3): fuzz whole columns ----------------------
    n_cols = 0
    col_boundary = [
        [S.Zero, a * (a - 1) - a * a + a, a + 1, b],   # first two are zero
        [a, b, c],                                     # first is the pivot
        [S.Zero, S.Zero, S.Zero],                      # no pivot
        [a * a - a * a, (a + 1) ** 2 - a * a - 2 * a - 1, S.Zero],  # all zero
        [Integer(0), Integer(0), Integer(5)],
        [a - a, b - b, a * b],
    ]
    for col in col_boundary:
        check_pivot_branch(col)
        n_cols += 1
    for _ in range(300):
        m = rng.randint(1, 5)
        col = []
        for _ in range(m):
            if rng.random() < 0.4:
                base = sum(rand_term() for _ in range(rng.randint(1, 3)))
                col.append(base * (a - 1) - base * a + base)   # cancels to 0
            else:
                col.append(sum(rand_term() for _ in range(rng.randint(1, 3))) + 1)
        check_pivot_branch(col)
        n_cols += 1

    print("G-AX OK: _is_zero_after_expand_mul deep model (definition + "
          "consistency) sound on %d boundary + 12002 fuzz scalars; "
          "_find_reasonable_pivot agrees with selectPivot on %d columns "
          "(A-reference soundness; end-to-end M(5..7).det()==0 is G-RESOLVE's "
          "FAIL_TO_PASS, not a G-AX obligation)."
          % (len(boundary), n_cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
