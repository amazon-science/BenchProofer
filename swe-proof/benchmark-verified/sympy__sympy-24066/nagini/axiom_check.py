#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24066.

Three obligations are validated against the REAL repository code (in-container):

  (A-consumed, totality/domain) the `resolvable` + `is_dimensionless` axioms
      (model.py axioms region) stand in for the unchanged community callee
      ``UnitSystem.get_dimension_system().is_dimensionless`` (a method of
      DimensionSystem). That callee is PARTIAL: it produces a boolean verdict
      only on dimensions whose dimensional dependencies can be computed, and
      RAISES ``TypeError`` on dimensions whose dependencies cannot be resolved:
      an incompatible additive combination like ``Dimension(length+mass)`` /
      ``Dimension(length-mass)``, or a dimensional argument to a transcendental
      function like ``Dimension(sin(length))`` / ``Dimension(exp(length))``
      (confirmed reproducibly in the pinned 1.12 eval container). The model
      captures this with the opaque ``resolvable(code)`` domain predicate: the axiom
      ``is_dimensionless`` carries ``Requires(resolvable(code))`` and the
      function is only proven total on the resolvable sub-domain. This script
      therefore (a) confirms the real callee returns a bool on resolvable inputs
      (the three regimes: canonical dimensionless ``Dimension(1)``; non-canonical
      dimensionless ``time/(capacitance*impedance)``; genuine dimensions), AND
      (b) FUZZES THE RAISE SURFACE: it confirms the real callee RAISES on the
      non-resolvable witnesses — i.e. the model's ``resolvable`` restriction
      excludes exactly the inputs on which the real predicate has no verdict.
      An axiom claiming totality over ALL codes would be UNSOUND; the domain
      restriction makes it sound.

  (A-reference) the deep model `canon_dim` / `canon_seq` (model.py pure region):
      for each RESOLVABLE argument dimension ``d`` of an applied Function, the
      dimension reported is ``Dimension(1)`` when ``is_dimensionless(d)`` and
      ``d`` itself otherwise. This is validated == the REAL, gold-patched
      ``UnitSystem._collect_factor_and_dimension`` on its Function branch, plus
      the end-to-end F2P scenario (``1 + exp(second/(ohm*farad))``) which the
      canonicalisation is what makes resolve.

Imports only `sympy` (the repository under test) and the standard library.
Exit 0 iff every observation matches the model.

G-AX INVOCATION: the deep model reflects the *fixed* Function branch, so the
A-reference half must run on the POST-PATCH worktree (apply_gold=True). At
base_commit the A-reference check correctly FAILS (the base repo is the buggy
code the gold patch corrects); the A-consumed `is_dimensionless` totality/domain
half (including the raise-surface fuzz) holds on both trees (that callee is
unchanged).
"""
import sys


# --- model.py reference encodings (kept in lock-step with the model) ---------

def model_canon_dim(dim, dimensionless_of):
    """Reference of model.py's `canon_dim`: replace a dimensionless argument
    dimension with the canonical dimensionless dimension, else keep it.
    `dimensionless_of(d)` is the real is_dimensionless verdict; CANON_ONE is the
    canonical dimensionless dimension Dimension(1). Only called on resolvable
    dimensions (the modeled domain)."""
    from sympy.physics.units.dimensions import Dimension
    if dimensionless_of(dim):
        return Dimension(1)
    return dim


def real_resolvable(is_dimensionless, dim):
    """The real-world meaning of model.py's `resolvable(code)` domain predicate:
    the dimension system can decide dimensionlessness for `dim` WITHOUT raising.
    True iff the real is_dimensionless returns a value (does not raise)."""
    try:
        is_dimensionless(dim)
        return True
    except Exception:
        return False


def main():
    from sympy import exp, sin, S
    from sympy.core.numbers import E
    from sympy.physics.units import (
        impedance, capacitance, time, ohm, farad, second, length, mass)
    from sympy.physics.units.quantities import Quantity
    from sympy.physics.units.dimensions import Dimension
    from sympy.physics.units.systems.si import SI

    dimsys = SI.get_dimension_system()
    is_dimensionless = dimsys.is_dimensionless

    # ---- build the non-canonical-but-dimensionless dimension from the issue --
    R = Quantity('R_axck')
    C = Quantity('C_axck')
    T = Quantity('T_axck')
    SI.set_quantity_dimension(R, impedance)
    SI.set_quantity_dimension(C, capacitance)
    SI.set_quantity_dimension(T, time)
    R.set_global_relative_scale_factor(1, ohm)
    C.set_global_relative_scale_factor(1, farad)
    T.set_global_relative_scale_factor(1, second)
    inner = T / (R * C)                     # dimension time/(capacitance*impedance)
    inner_dim = SI._collect_factor_and_dimension(inner)[1]

    # ---- (A-consumed, in-domain) is_dimensionless is a total boolean ---------
    # predicate on the RESOLVABLE sub-domain — the three regimes the modeled
    # branch distinguishes, all resolvable (the real callee returns a value).
    canonical = Dimension(1)
    noncanon_dimensionless = inner_dim
    genuine = length                        # a real, non-dimensionless dimension
    genuine2 = mass

    resolvable_dims = [canonical, noncanon_dimensionless, genuine, genuine2,
                       length / length, impedance, capacitance, time,
                       time / (capacitance * impedance)]
    for d in resolvable_dims:
        assert real_resolvable(is_dimensionless, d), (
            "model assumes %r is resolvable (in the dimensionless test's "
            "domain), but the real callee raised on it" % (d,))
        v = is_dimensionless(d)
        assert isinstance(v, bool), (
            "is_dimensionless must be a total boolean predicate on its domain; "
            "on %r got %r" % (d, type(v)))

    # The specific verdicts the model's canonicalisation relies on:
    assert is_dimensionless(canonical) is True, \
        "canonical Dimension(1) must be dimensionless"
    assert is_dimensionless(noncanon_dimensionless) is True, \
        "time/(capacitance*impedance) must be dimensionless"
    # the discriminator: it is dimensionless yet structurally != Dimension(1)
    assert noncanon_dimensionless != canonical, (
        "the issue's dimension must be a NON-canonical dimensionless dimension "
        "(structurally unequal to Dimension(1)) — that is the whole point")
    assert is_dimensionless(genuine) is False, \
        "length must NOT be dimensionless"
    assert is_dimensionless(genuine2) is False, \
        "mass must NOT be dimensionless"

    # ---- (A-consumed, RAISE SURFACE) is_dimensionless is PARTIAL -------------
    # The real callee has NO verdict on dimensions whose dependencies cannot be
    # resolved — it raises TypeError. The model's `resolvable` domain predicate
    # must therefore exclude exactly these inputs (they are NOT in the modeled
    # domain, so the axiom never claims a verdict for them). An axiom that
    # claimed totality over all codes would be UNSOUND; fuzz that surface here.
    raising_dims = []
    # (1) an incompatible additive combination of distinct base dimensions
    raising_dims.append(("Dimension(length+mass)", Dimension(length.name + mass.name)))
    # (2) the subtractive variant
    raising_dims.append(("Dimension(length-mass)", Dimension(length.name - mass.name)))
    # (3) a dimensional argument to a transcendental function
    raising_dims.append(("Dimension(sin(length))", Dimension(sin(length.name))))
    raising_dims.append(("Dimension(exp(length))", Dimension(exp(length.name))))

    for name, d in raising_dims:
        assert not real_resolvable(is_dimensionless, d), (
            "%s is expected to be OUTSIDE the dimensionless test's domain "
            "(the real callee should raise), but it returned a verdict; the "
            "model's `resolvable` restriction would then be too strict" % (name,))
        raised = False
        try:
            is_dimensionless(d)
        except TypeError:
            raised = True
        except Exception as e:
            raise AssertionError(
                "%s: real is_dimensionless raised %s, expected TypeError (the "
                "domain-error the model's partiality captures)" % (name, type(e).__name__))
        assert raised, (
            "%s: real is_dimensionless did NOT raise — the axiom's totality "
            "over the resolvable sub-domain would over-claim if this input were "
            "treated as in-domain" % (name,))

    # ---- (A-reference) canon_dim == real Function-branch reporting -----------
    # For each RESOLVABLE probe dimension, the model's canon_dim must
    # canonicalise exactly as the rule the gold Function branch applies, and a
    # dimensionless one must become Dimension(1) (so it compares EQUAL to the
    # canonical dimensionless).
    for d in resolvable_dims:
        cd = model_canon_dim(d, is_dimensionless)
        if is_dimensionless(d):
            assert cd == canonical, (
                "canon_dim of a dimensionless dimension %r must be Dimension(1), "
                "got %r" % (d, cd))
        else:
            assert cd == d, (
                "canon_dim of a non-dimensionless dimension %r must be itself, "
                "got %r" % (d, cd))

    # ---- A-reference vs the REAL gold-patched Function branch (best effort) --
    # The fixed _collect_factor_and_dimension reports, for exp(inner), the
    # canonical dimensionless dimension for its single (dimensionless) argument.
    # On the base (buggy) tree this returns the non-canonical dimension instead,
    # so this block fails — which is the intended apply_gold=True behaviour.
    gold_ok = True
    try:
        fexpr = exp(inner)
        fdim = SI._collect_factor_and_dimension(fexpr)[1]
        # Function branch canonicalises the dimensionless argument dimension.
        assert is_dimensionless(fdim), \
            "exp(dimensionless) must itself be reported dimensionless"
        assert fdim == canonical, (
            "gold Function branch must report the CANONICAL dimensionless "
            "Dimension(1) for a dimensionless argument; got %r" % (fdim,))
        # End-to-end F2P: 1 + exp(inner) collects to (1 + E, Dimension(1)).
        full = S(1) + exp(inner)
        factor, dim = SI._collect_factor_and_dimension(full)
        assert dim == canonical and factor == 1 + E, (
            "gold end-to-end must give (1 + E, Dimension(1)); got (%r, %r)"
            % (factor, dim))
    except Exception as e:                   # base (buggy) tree: expected to fail
        gold_ok = False
        sys.stderr.write(
            "A-reference (gold Function branch) check failed — expected ONLY on "
            "the base/buggy tree (run with apply_gold=True for G-AX): %r\n" % (e,))

    print("G-AX OK: is_dimensionless axiom (A-consumed) is a total boolean "
          "predicate ON ITS RESOLVABLE DOMAIN with the canonical/non-canonical/"
          "genuine verdicts the model relies on, AND is partial off that domain "
          "(raises TypeError on the non-resolvable witnesses the model's "
          "`resolvable` excludes); canon_dim deep model (A-reference) "
          "canonicalises every resolvable probe dimension correctly%s."
          % (" and matches the real gold Function branch + F2P scenario"
             if gold_ok else " (real gold-branch block skipped: base tree)"))
    if not gold_ok:
        # On the POST-PATCH tree this MUST hold; signal failure so G-AX (which
        # runs apply_gold=True) catches a regression. On base tree the harness
        # expects this non-zero exit.
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
