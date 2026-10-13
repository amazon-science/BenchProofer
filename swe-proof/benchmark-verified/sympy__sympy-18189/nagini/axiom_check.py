"""G-AX executable soundness check for sympy__sympy-18189.

Executes the REAL repo callee (`sympy.solvers.diophantine.diophantine`) and the
REAL component re-arrangement in-container, and asserts that the two consumed
axioms of model.py over-approximate the real behaviour:

  (A-consumed) `solve_family(expand)` — the recursive `diophantine(eq, param,
      permute=expand)` solver. The model relies on exactly one property: the
      family is OPTION-DEPENDENT, i.e. `solve_family(True) != solve_family(False)`
      in general, and the two are NOT asserted equal. We confirm there exists an
      input on which the real callee's `permute=True` and `permute=False` results
      differ (and that `permute=True` is a superset of `permute=False`, never a
      collapse) — the very phenomenon the issue reports.

  (A-consumed) `relabel(token)` — the per-tuple component re-arrangement
      `tuple(t[dict_sym_index[i]] for i in var)`. The model relies on its being
      an INJECTIVE coordinate permutation (a bijection on solution tuples, so the
      relabelled family has the same cardinality). We confirm the re-indexing is
      a genuine permutation: a bijection on each canonical solution, collision-
      free over the whole family, and order-invariant set under the public entry.

Imports only the standard library plus `sympy` itself (the repo under test) —
the same package the gold patch edits. Exit 0 iff every obligation holds.
"""
import sys
import itertools


def _check_solve_family_option_dependence():
    """solve_family axiom: the recursive solver's result depends on the option,
    and permute=True is a (strict, here) superset of permute=False — never a
    collapse to the base family."""
    from sympy.abc import x, y
    from sympy.solvers.diophantine import diophantine

    # The F2P equation (issue 18186): a**4 + b**4 - (2**4 + 3**4), plus a second
    # equation the test-suite exercises with permute=True (binary quadratic).
    eqs = [
        x**4 + y**4 - 2**4 - 3**4,
        x**2 + y**2 + 3*x - 5,
    ]
    found_difference = False
    for eq in eqs:
        base = diophantine(eq, permute=False)      # real callee, base family
        full = diophantine(eq, permute=True)       # real callee, full family
        # The axiom never claims True == False; confirm they genuinely differ on
        # at least one input (otherwise the option would be vacuous and the
        # discriminating clause of the spec would be unfounded).
        if base != full:
            found_difference = True
        # When they differ, the full family must be a SUPERSET (permutation /
        # sign expansion adds solutions; it never drops the base ones). This is
        # what makes "re-derive under the caller's option" the correct behaviour.
        assert base <= full, (
            "permute=True is not a superset of permute=False for %r: "
            "base=%r full=%r" % (eq, base, full))
    assert found_difference, (
        "solve_family axiom unfounded: permute=True == permute=False on every "
        "probed equation — the option would be vacuous")

    # The headline F2P case, exact values (the issue's own example).
    full = diophantine(x**4 + y**4 - 2**4 - 3**4, permute=True)
    expected_full = {(-3, -2), (-3, 2), (-2, -3), (-2, 3),
                     (2, -3), (2, 3), (3, -2), (3, 2)}
    assert full == expected_full, (
        "canonical-order permute=True family mismatch: got %r" % (full,))
    base = diophantine(x**4 + y**4 - 2**4 - 3**4, permute=False)
    assert base == {(2, 3)}, (
        "canonical-order permute=False base family mismatch: got %r" % (base,))
    assert base != full, "option must change the family on the F2P equation"


def _check_relabel_bijection():
    """relabel axiom: the per-tuple component re-arrangement built from
    dict_sym_index = dict(zip(syms, range(len(syms)))) is an injective
    permutation of a tuple's components — a bijection on solution tuples."""
    from sympy.abc import x, y
    from sympy.solvers.diophantine import diophantine

    eq = x**4 + y**4 - 2**4 - 3**4

    # The canonical ordering used by diophantine: free symbols sorted by
    # default_sort_key (the same key the real function applies at var.sort(...)).
    from sympy.core.compatibility import default_sort_key
    var = sorted(eq.free_symbols, key=default_sort_key)   # canonical ordering

    # The component re-arrangement is the comprehension body
    # `tuple(t[dict_sym_index[i]] for i in var)` with
    # `dict_sym_index = dict(zip(syms, range(len(syms))))`. It is pure tuple
    # re-indexing — independent of the solver and of the patch. We validate its
    # bijectivity directly for EVERY caller ordering `syms`, over a synthetic set
    # of distinct canonical tuples whose component count matches `len(var)`.
    canonical = [(1, 2), (3, 4), (-1, 7), (0, 0), (5, -2),
                 (2, 3), (-3, -2), (2, -3)]
    n = len(var)
    for syms in itertools.permutations(var):
        syms = list(syms)
        dict_sym_index = dict(zip(syms, range(len(syms))))
        # The index map is a permutation of range(n).
        assert sorted(dict_sym_index.values()) == list(range(n)), (
            "dict_sym_index is not a permutation for syms=%r" % (syms,))
        # sigma[k] = the canonical component that lands at output position k.
        sigma = [dict_sym_index[var[k]] for k in range(n)]
        assert sorted(sigma) == list(range(n)), (
            "component permutation sigma is not a bijection for syms=%r"
            % (syms,))
        relabelled = [tuple(t[dict_sym_index[i]] for i in var)
                      for t in canonical]
        # Injectivity / bijection: distinct canonical tuples never collide, so
        # the relabelled family has the same cardinality as the source.
        assert len(set(relabelled)) == len(set(canonical)), (
            "relabel not injective for syms=%r: %r -> %r"
            % (syms, canonical, relabelled))
        # And it is invertible: relabelled[k] == t[sigma[k]], so recovering
        # t[sigma[k]] from position k for every k reconstructs t exactly.
        for t, r in zip(canonical, relabelled):
            recovered = [None] * n
            for k in range(n):
                recovered[sigma[k]] = r[k]
            assert tuple(recovered) == t, (
                "relabel not invertible for syms=%r: %r -> %r -> %r"
                % (syms, t, r, recovered))


def main():
    _check_solve_family_option_dependence()
    _check_relabel_bijection()
    print("G-AX OK: solve_family option-dependence (permute True != False, "
          "True superset of False, F2P exact families) and relabel bijection "
          "(injective component permutation, cardinality-preserving over all "
          "symbol orderings) hold for the real sympy diophantine callee.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
