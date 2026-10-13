#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20428 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged op of Solution.lean's impl region transliterated to
              Python: `nonzeroSpec(e) = not e.identicallyZero`, where a symbolic
              field element `e` is reduced to its two observations
              `identicallyZero` / `literalZero` (mapping.md §2). This bundle has
              NO axioms and NO A-reference to an external callee (refinement.md
              §C), so the whole shadow is pure R/I and in scope for G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the REAL gold-patched
              `ExpressionDomain.Expression.__bool__`, i.e. `bool(EX(expr))`,
              observed directly. The patch replaces `f.ex != 0` (structural
              inequality against the literal zero) with `not f.ex.is_zero` (the
              mathematical/identical zero test).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
PYTHONPATH=/testbed so the patched in-tree sympy wins. stdlib + sympy only. The
fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 20428
N_FUZZ = 100_000


# --- bridge: real EX element -> the two modeled observations -----------------

def observe(el, S):
    """Reduce a real `EX(expr)` element to the Solution.lean `SymExpr` fields
    (mapping.md §2):
      identicallyZero := (el.ex.is_zero is True)   # math/identical zero test
      literalZero     := (el.ex == S.Zero)         # bare literal-zero compare
    `is_zero` is three-valued (True/False/None); the patched `not el.ex.is_zero`
    treats None as nonzero, which is exactly `not (is_zero is True)`."""
    identically_zero = (el.ex.is_zero is True)
    literal_zero = (el.ex == S.Zero)
    return identically_zero, literal_zero


# --- SHADOW: Solution.lean nonzeroSpec, transliterated -----------------------

def shadow_nonzero(identically_zero, literal_zero):
    """nonzeroSpec(e) = !e.identicallyZero  (the literalZero field is the
    coarse observation the pre-patch impl wrongly used; the fixed spec ignores
    it for the outcome)."""
    return (not identically_zero)


# --- ORACLE: the REAL gold-patched __bool__ ----------------------------------

def oracle_nonzero(el):
    """patch.diff's behaviour: the patched Expression.__bool__ == `not
    f.ex.is_zero`. We observe it through the public `bool(...)` protocol."""
    return bool(el)


# --- input generator ---------------------------------------------------------

def boundary_exprs(sympy):
    """Hand-picked discriminating elements (mapping.md §3): elements that DENOTE
    zero while NOT being the literal zero (the issue's bad poly is one such),
    plain literal zero, and clear nonzeros. The first entry is the canonical
    issue shape: math-zero but written differently from the literal 0."""
    S = sympy.S
    x, y = sympy.symbols('x y')
    sqrt = sympy.sqrt
    out = [
        sympy.sympify('1/(sqrt(2)-1) - (sqrt(2)+1)'),   # denotes 0, not literal 0
        sympy.sympify('sqrt(8) - 2*sqrt(2)'),           # denotes 0 (auto -> 0)
        sympy.sympify('(x+1)**2 - x**2 - 2*x - 1'),     # is_zero None, not lit 0
        S.Zero,                                         # the literal zero
        S.One,                                          # plain nonzero
        sympy.Integer(-3),
        x,                                              # symbol: nonzero-ish
        x - x,                                          # -> literal 0
        sqrt(2),
        sqrt(9165) - sqrt(9165),                        # -> 0
        x + y - y,                                      # -> x
    ]
    return out


def fuzz_exprs(n, rng, sympy):
    """Random small expression trees over a mix of rationals, symbols, and
    surds, built with +,-,*,/ — exercises literal-zero, identical-zero
    (incl. non-literal forms produced by cancellation), and nonzero outcomes."""
    S = sympy.S
    x, y = sympy.symbols('x y')
    atoms = [S(0), S(1), S(2), S(-1), x, y, sympy.sqrt(2), sympy.cbrt(3),
             sympy.Rational(3, 4), sympy.sqrt(9165)]
    for _ in range(n):
        a = rng.choice(atoms)
        b = rng.choice(atoms)
        op = rng.choice(['+', '-', '*', '/'])
        try:
            if op == '+':
                e = a + b
            elif op == '-':
                e = a - b
            elif op == '*':
                e = a * b
            else:
                e = a / b if b != 0 else a
        except Exception:
            continue
        yield e


def main():
    try:
        import sympy
        from sympy.polys.domains.expressiondomain import ExpressionDomain
        EX = ExpressionDomain()
        S = sympy.S
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched sympy ExpressionDomain: %r"
              % e)
        return 2

    rng = random.Random(SEED)
    disagreements = []
    inv_violations = []
    count = 0

    def check(expr):
        nonlocal count
        count += 1
        try:
            el = EX(expr)
        except Exception:
            return
        identically_zero, literal_zero = observe(el, S)
        # modeling invariant (the method's `require`): a literal-zero
        # representation always denotes zero. A violation would mean the spec's
        # precondition excludes a reachable input -> report it.
        if literal_zero and not identically_zero:
            inv_violations.append((str(el.ex),))
        sh = shadow_nonzero(identically_zero, literal_zero)
        orc = oracle_nonzero(el)
        if bool(sh) != bool(orc):
            disagreements.append((str(el.ex), sh, orc))

    for expr in boundary_exprs(sympy):
        check(expr)
    for expr in fuzz_exprs(N_FUZZ, rng, sympy):
        check(expr)
        if len(disagreements) >= 8:
            break

    if inv_violations:
        print("G-CONF FAIL: %d modeling-invariant violation(s) (literalZero but "
              "not identicallyZero) over %d inputs:"
              % (len(inv_violations), count))
        for (ex,) in inv_violations[:8]:
            print("  ex=%s" % ex)
        return 1
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ex, sh, orc in disagreements[:8]:
            print("  ex=%s shadow_nonzero=%r oracle_nonzero=%r" % (ex, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of symbolicNonzero (nonzeroSpec = "
          "not identicallyZero) agrees with patch.diff behaviour (real patched "
          "Expression.__bool__ == `not f.ex.is_zero`) on %d inputs "
          "(11 boundary + fuzz, seed=%d), 0 disagreements; modeling invariant "
          "literalZero -> identicallyZero held throughout." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
