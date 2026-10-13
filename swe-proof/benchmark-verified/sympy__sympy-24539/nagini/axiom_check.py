#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24539.

This bundle consumes NO `@ContractOnly` axiom and references NO stdlib/library
deep-model (the `axioms` and `pure` regions of model.py are empty): the modeled
delta is a three-way control-flow SELECTION of which generator-symbol sequence
a polynomial is rendered over, spelled out deeply in `select_render_symbols`
(model.py). G-AX therefore reduces to a SELECTION-EQUIVALENCE check against the
real, post-patch callee `PolyElement.as_expr`:

  * the only quantity the patch changes is the `gens` sequence handed to the
    UNCHANGED downstream builder `expr_from_dict(self.as_expr_dict(), *gens)`,
    which is a deterministic function of `(term dict, gens)`. So the rendered
    expression is fully determined by which `gens` is selected, and the model
    returns that selected sequence directly.

We assert, against the REAL sympy at the patched commit:
  (1) supplied symbols of the CORRECT count are the ones rendered over (the
      result equals the polynomial re-expressed in exactly those symbols, in
      order) — model branch `len(symbols) == ngens > 0`;
  (2) supplying NO symbols renders over the ring's own default symbols — model
      branch `len(symbols) == 0`;
  (3) supplying a WRONG, non-empty count raises `ValueError` — model `Exsures`;
  (4) the determinism provenance: building the expression directly with
      `expr_from_dict(p.as_expr_dict(), *gens)` for the selected `gens` equals
      `p.as_expr(*selected)` — confirming the rendered value is a function of
      the selected `gens` alone, so the model's "return the selected sequence"
      abstraction is faithful;
  (5) the pre-patch divergence is real: under the old code a correct-count
      supplied sequence would have been DISCARDED and the default used, giving
      a different expression — documenting what G-DIFF senses.

Imports only sympy (the very library the patch lives in) and stdlib. Exit 0
iff every obligation holds.
"""
import itertools
import sys

from sympy import ring, ZZ, QQ, symbols
from sympy.polys.rings import PolyElement
from sympy.polys.polyutils import expr_from_dict


def selected_gens(passed, default, ngens):
    """Reference copy of model.py's `select_render_symbols` decision (returns
    the selected generator sequence, or the string 'RAISE')."""
    if len(passed) == 0:
        return list(default)
    if len(passed) != ngens:
        return 'RAISE'
    return list(passed)


def main():
    n_checks = 0

    # ---- F2P polynomial (issue + gold test) --------------------------------
    R, x, y, z = ring("x,y,z", ZZ)
    f = 3*x**2*y - x*y*z + 7*z**3 + 1
    U, V, W = symbols("u,v,w")
    X, Y, Z = symbols("x,y,z")

    # (1) correct count of supplied symbols -> rendered over THOSE symbols
    g = 3*U**2*V - U*V*W + 7*W**3 + 1
    assert f.as_expr(U, V, W) == g, (
        "supplied 3 symbols must be used: as_expr(U,V,W) should equal the "
        "polynomial re-expressed over u,v,w")
    assert f.as_expr(U, V, W) != f.as_expr(), (
        "rendering over supplied u,v,w must differ from the default x,y,z")
    n_checks += 1

    # (2) no symbols supplied -> ring's default symbols
    assert f.as_expr() == 3*X**2*Y - X*Y*Z + 7*Z**3 + 1, (
        "no symbols supplied must render over the ring's default x,y,z")
    n_checks += 1

    # (3) wrong, non-empty count -> ValueError
    for bad in [(X,), (X, Y), (X, Y, Z, U)]:
        try:
            f.as_expr(*bad)
            assert False, ("supplying %d symbols (ngens=3) must raise ValueError"
                           % len(bad))
        except ValueError:
            pass
        n_checks += 1

    # (4) determinism provenance: result is a function of the selected gens
    #     alone (model returns the selected gens; the builder is unchanged).
    for passed in [(), (U, V, W), (X, Y, Z), (Y, Z, X)]:
        sel = selected_gens(passed, R.symbols, R.ngens)
        assert sel != 'RAISE'
        direct = expr_from_dict(f.as_expr_dict(), *sel)
        assert f.as_expr(*passed) == direct, (
            "as_expr(*%r) must equal expr_from_dict over the selected gens %r"
            % (passed, sel))
        n_checks += 1

    # ---- fuzz across rings / domains / orderings ----------------------------
    pool = symbols("a b c d e p q r")
    specs = [
        ("a", ZZ), ("a,b", ZZ), ("a,b,c", QQ), ("a,b,c,d", ZZ),
        ("p,q", QQ), ("a,b,c,d,e", ZZ),
    ]
    for gen_str, dom in specs:
        Rg = ring(gen_str, dom)
        Rr = Rg[0]
        gens = Rg[1:]
        ng = Rr.ngens
        # a small nonzero polynomial: sum of a few monomials
        poly = Rr.zero
        for k, gg in enumerate(gens):
            poly = poly + (k + 1) * gg ** (k + 1)
        poly = poly + 1

        # (2') default render
        assert poly.as_expr() == expr_from_dict(poly.as_expr_dict(), *Rr.symbols)
        n_checks += 1

        # (1') correct-count alternative symbol sets -> used as-is
        alt_sets = [tuple(pool[:ng]), tuple(reversed(pool[:ng]))]
        for alt in alt_sets:
            sel = selected_gens(alt, Rr.symbols, ng)
            assert sel != 'RAISE'
            assert poly.as_expr(*alt) == expr_from_dict(poly.as_expr_dict(), *alt)
            # and (unless alt happens to equal the defaults) it differs from default
            if list(alt) != list(Rr.symbols):
                assert poly.as_expr(*alt) != poly.as_expr(), (
                    "%s: supplied alt symbols %r must change the rendering"
                    % (gen_str, alt))
            n_checks += 1

        # (3') wrong counts raise
        for bad_n in [n for n in (0, 1, 2, 3, ng + 1, ng + 2) if n != ng and n != 0]:
            bad = tuple(pool[:bad_n])
            try:
                poly.as_expr(*bad)
                assert False, ("%s: %d supplied symbols (ngens=%d) must raise"
                               % (gen_str, bad_n, ng))
            except ValueError:
                pass
            n_checks += 1

    # ---- (5) the pre-patch divergence is real (what G-DIFF senses) ----------
    # Pre-patch, a correct-count supplied sequence was discarded and the ring
    # defaults used. Emulate that old selection and confirm it gives a DIFFERENT
    # (wrong) expression than the post-patch behaviour for f.as_expr(U,V,W).
    old_selection = list(R.symbols)              # pre-patch always used defaults
    old_result = expr_from_dict(f.as_expr_dict(), *old_selection)
    assert old_result == f.as_expr(), (
        "sanity: pre-patch selection == default render")
    assert old_result != f.as_expr(U, V, W), (
        "pre-patch would have discarded supplied u,v,w (rendered over x,y,z); "
        "post-patch must render over u,v,w — the change is real")

    print("G-AX OK: selection-equivalence holds on %d real sympy observations "
          "(F2P + controls + multi-ring fuzz); real PolyElement.as_expr renders "
          "over exactly the selected generator symbols, the rendered expression "
          "is a deterministic function of that selection, wrong counts raise "
          "ValueError, and the pre-patch divergence is confirmed. No consumed "
          "axiom." % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
