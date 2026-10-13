#!/usr/bin/env python3
"""G-AX skip stub for pydata__xarray-4966.

No consumed callee axiom is declared in the bundle and no `opaque` callee
appears in Solution.lean. The only behavior the patch changes -- the
width-preserving two's-complement reinterpretation of the integer array and its
fill value (`np.asarray(arr, "uN"/"iN")`) -- is modeled DEEPLY as exact `Int`
arithmetic (`reinterpAsUnsigned` / `reinterpAsSigned`). SPEC_GUIDE §3 forbids
axiomatizing a deeply-modeled changed op, so the `axioms` region is empty and
there is nothing for G-AX to validate; the deep models are differential-tested
against the real numpy casts by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "pydata__xarray-4966",
        "reason": "no consumed callee axiom and no A-reference opaque; the changed "
                  "cast is deep-modeled as Int arithmetic (validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
