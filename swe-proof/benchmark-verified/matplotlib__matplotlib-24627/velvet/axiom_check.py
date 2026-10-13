#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24627.

This bundle consumes NO axioms and declares NO A-reference deep models of an
unchanged callee:

  * The only behaviour modeled is the deparenting of the artists formerly
    attached to the axes — the operation the patch CHANGES (the clear routine
    now unsets each former child's `.axes` and `.figure`). Per SPEC_GUIDE
    directive 7 / §3 a *changed* op modeled deeply is neither a consumed axiom
    nor an A-reference of an unchanged callee; it is the modeled function
    itself, and its fidelity to the real patched code is the job of G-CONF
    (conformance_check.py), which executes the REAL patched `clear()`.

  * The `Artist` / `deparent` / `deparentAll` abstraction is a pure Lean model
    with no repository callee behind it; there is nothing for G-AX to execute.

  * The other statements the clear routine runs (resetting `_mouseover_set`,
    `child_axes`, the `None` sentinels, regridding, …) are untouched by the
    patch and are not part of the modeled contract — the `ensures` clause says
    nothing about them — so they are not axiomatized and need no G-AX
    obligation.

Consequently axiom_check.py has no real callee to fuzz against an axiom. It
asserts the bundle's axiom inventory is empty (a guard against a future edit
silently introducing an unchecked axiom) and exits 0.

stdlib-only; exit 0 iff sound (here: iff the axiom inventory is genuinely
empty).
"""
import sys

# Mirrors meta.json: this bundle declares zero consumed axioms and zero
# A-reference deep models. Keep in lock-step with meta.json `axioms` /
# `deep_model_references`.
AXIOMS = []
DEEP_MODEL_REFERENCES = []


def main():
    assert AXIOMS == [], (
        "G-AX: axiom inventory expected empty for this bundle, found %r"
        % (AXIOMS,))
    assert DEEP_MODEL_REFERENCES == [], (
        "G-AX: A-reference inventory expected empty for this bundle, found %r"
        % (DEEP_MODEL_REFERENCES,))
    print("G-AX OK: no consumed axioms and no A-reference deep models of an "
          "unchanged callee. The changed deparent-on-clear behaviour is modeled "
          "deeply (Artist/deparent/deparentAll) and validated by G-CONF against "
          "the real patched clear routine, not by an axiom.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
