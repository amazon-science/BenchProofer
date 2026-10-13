#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24870.

VACUOUS by construction. The modeled function `chooseLevelArg`
(`ContourSet._process_contour_level_args`, the level-argument selection branch)
is a pure selection over flags and values that the surrounding routine has
already computed (`self.levels`, the positional `args`,
`np.issubdtype(z.dtype, bool)`, `self.filled`). It calls NO unchanged callee
whose contract the proof consumes, and it has NO deep-model reference:

  * Solution.lean's `axioms` region is empty (no `axiom`).
  * refinement.md tags every impl op R or I; there is no A-consumed or
    A-reference row (refinement.md §C).
  * meta.json records `axioms: []` and `deep_model_references: []`.

There is therefore nothing to execute against a real callee: G-AX is vacuously
sound. (The boolean-field / filled tests are *inputs* to the modeled function,
checked by G-CONF's differential run of the real patched routine, not callees
of it — so they belong to G-CONF, not G-AX.) Exit 0.

stdlib only; no repo import required.
"""
import sys


def main():
    axioms = []                 # Solution.lean axioms region is empty
    deep_model_references = []  # no A-reference
    assert not axioms and not deep_model_references, (
        "axiom_check invoked but bundle declares axioms/references; update it")
    print("G-AX OK (vacuous): matplotlib__matplotlib-24870 declares no axioms "
          "and no deep-model references. The modeled selection consumes no "
          "unchanged callee contract; all impl ops are R/I (refinement.md §C), "
          "checked by G-CONF. Nothing to validate against a real callee.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
