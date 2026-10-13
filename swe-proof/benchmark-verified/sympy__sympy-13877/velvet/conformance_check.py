#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13877 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `selectPivot` impl region
              transliterated to Python over the *real* repo type (a column of
              scalar sympy `Expr`), via the mapping.md bijection
              (`Array Entry` ↔ column; `Entry.mathNonzero` ↔ the A-reference
              predicate `not _is_zero_after_expand_mul(x)`). The scan loop (the
              R/I ops) is transliterated; the A-reference predicate is left as the
              REAL repo callee `_is_zero_after_expand_mul`, NOT re-modeled — G-CONF
              isolates the R/I legs and the A leg stays with G-AX.
  * ORACLE  — `patch.diff`'s behaviour: the real patched
              `_find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul)`
              (the call the gold patch installs at the inner Bareiss pivot step),
              restricted to the modeled non-Float column branch (mapping.md §2).

They must agree on `(found, idx)` for every column. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), importing the repo
under test (sympy). The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

from sympy import symbols, S, Integer, expand_mul
from sympy.matrices.matrices import _find_reasonable_pivot

# See axiom_check.py: prefer the patch-introduced helper, fall back to its body
# (`expand_mul(x) == 0`) so the shadow predicate is well defined at base_commit.
try:
    from sympy.matrices.matrices import _is_zero_after_expand_mul
except ImportError:  # pragma: no cover - base_commit (pre-patch) container
    def _is_zero_after_expand_mul(x):
        return expand_mul(x) == 0

SEED = 13877
N_FUZZ = 100_000


def math_nonzero(x):
    """Entry.mathNonzero, transliterated: the A-reference predicate left as the
    REAL repo callee (not the axiom/deep model)."""
    return not _is_zero_after_expand_mul(x)


def shadow_select(col):
    """The R/I shadow of selectPivot's `do` block: scan in order, choose the
    first index that is decisively non-zero; report (found, idx)."""
    i = 0
    found = False
    idx = 0
    while i < len(col) and found is False:
        if math_nonzero(col[i]) is True:
            idx = i
            found = True
        i += 1
    return (found, idx if found else None)


def oracle_select(col):
    """patch.diff's behaviour: the real patched pivot finder on the modeled
    branch. Returns (found, idx)."""
    pivot_pos, _, _, _ = _find_reasonable_pivot(
        list(col), iszerofunc=_is_zero_after_expand_mul)
    if pivot_pos is None:
        return (False, None)
    return (True, pivot_pos)


def fuzz_columns(n, rng):
    a, b, c = symbols('a b c')
    syms = [a, b, c]

    def rand_term():
        return rng.randint(-3, 3) * rng.choice(syms) ** rng.randint(0, 2)

    def rand_expr():
        return sum(rand_term() for _ in range(rng.randint(1, 3)))

    # boundary columns first (plan §4.1 step 4)
    yield [a, b, c]
    yield [S.Zero, a * (a - 1) - a * a + a, a + 1]   # structurally-nonzero zeros skipped
    yield [S.Zero, S.Zero, S.Zero]
    yield [Integer(0), Integer(0), Integer(5)]
    yield [a * a - a * a, (a + 1) ** 2 - a * a - 2 * a - 1, b]
    yield [a - a]
    yield [a + 1]
    yield []
    for _ in range(n):
        m = rng.randint(0, 5)
        col = []
        for _ in range(m):
            r = rng.random()
            if r < 0.35:                       # an algebraically-zero entry
                base = rand_expr()
                col.append(base * (a - 1) - base * a + base)
            elif r < 0.5:                      # a literal zero
                col.append(S.Zero)
            else:                              # a genuinely non-zero entry
                col.append(rand_expr() + 1)
        yield col


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for col in fuzz_columns(N_FUZZ, rng):
        count += 1
        shadow = shadow_select(col)
        oracle = oracle_select(col)
        if shadow != oracle:
            disagreements.append((col, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d columns:"
              % (len(disagreements), count))
        for col, sh, orc in disagreements:
            print("  col=%r shadow=%r oracle=%r" % (col, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectPivot agrees with patch.diff "
          "behaviour on %d columns (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
