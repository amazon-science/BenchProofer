#!/usr/bin/env python3
r"""G-AX for matplotlib__matplotlib-20826.

`correct_clear` consumes NO `_prop` axiom. The modeled step (`Axis.clear`'s
tick-keyword re-initialisation) invokes no unchanged external callee: the grid
flag is concrete boolean logic over `rcParams['axes.grid']` and
`rcParams['axes.grid.which']` (modeled directly as `majorGridOn`/`minorGridOn`),
and the preservation of every other tick-keyword entry is the structural meaning
of `Function.update`. There is no `opaque` declaration and no `axiom _prop` in
the bundle, so there is nothing for G-AX to validate.

The correspondence between the Lean model and the real patched `Axis.clear`
(the R/I legs) is exercised mechanically by conformance_check.py (G-CONF). Hence
this gate is a principled skip stub.

stdlib-only; exit 0.
"""
import json
import sys

report = {
    "status": "skip",
    "instance": "matplotlib__matplotlib-20826",
    "reason": (
        "no consumed callee axiom: correct_clear proves a frame-preserving keyed "
        "map update (Function.update at 'gridOn', all other entries carried "
        "through) over concrete boolean logic; no opaque callee and no axiom _prop "
        "are declared. The model<->real-callee correspondence is validated by "
        "conformance_check.py (G-CONF), not by a Lean _prop axiom."
    ),
}
print(json.dumps(report))
sys.exit(0)
