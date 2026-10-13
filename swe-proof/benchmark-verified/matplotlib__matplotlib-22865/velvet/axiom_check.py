#!/usr/bin/env python3
"""G-AX soundness check for matplotlib__matplotlib-22865 — NO AXIOMS (skip stub).

This bundle declares no `axiom` and no A-reference deep model of an outside
callee (mapping.md §3, refinement.md §B). The single changed operation — which
divider/edge segments between adjacent colour bands are kept (the patch's
flag-dependent `start_idx`/`end_idx` slice replacing the constant `[1:-1]`) — is
modeled DEEPLY in Solution.lean's `pure` region (`startIdx`, `endIdx`,
`selectSeg`), entirely from concrete, total list arithmetic over the inputs
(`np.dstack([X, Y])` first axis ↔ `List Seg`; the two open-end flags are plain
boolean *inputs* supplied by the caller, not unchanged *callees*).

Per directive 7 the operation the patch CHANGES is never axiomatized, so there
is nothing for G-AX to validate against a real callee. (G-AX additionally runs
the instance image WITHOUT the gold patch applied — the orchestrator only
applies the gold patch for G-CONF — so any attempt to compare this deep model
against the *real* `_add_solids` here would be comparing the post-patch model to
the *pre-patch buggy* `[1:-1]` code: a category error that does not test
soundness.)

The deep model's fidelity to the patched behaviour is instead exercised
mechanically by conformance_check.py (G-CONF), which drives the REAL patched
`Colorbar._add_solids` end-to-end (phase A, gold patch applied) and the REAL
patched numpy slice at scale (phase B), and diffs both against the R/I
transliteration over >=10^5 fuzzed inputs.

Exit 0 with a skip status (meta.json gates.G-AX.status = "skip").
"""
import sys


def main():
    print("G-AX SKIP: no axioms / no A-reference in this bundle; the changed "
          "edge-segment selection is modeled deeply (pure region) and checked "
          "by G-CONF (which runs the real patched callee).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
