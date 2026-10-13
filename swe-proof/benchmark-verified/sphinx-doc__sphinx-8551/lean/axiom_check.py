#!/usr/bin/env python3
"""G-AX — axiom soundness check for sphinx-doc__sphinx-8551.

This bundle consumes NO `axiom <callee>_prop` and declares NO `opaque` callee:
the patch READS the surrounding namespace context out of the environment
(`env.ref_context.get('py:module')` / `get('py:class')`) and WRITES those values
onto the cross-reference node it builds. The context values are INPUTS to the
modeled node-building step (`ctx.module`, `ctx.cls`), and every node attribute the
step writes (`refspecific`, `reftarget`, `py:module`, `py:class`) is modeled
directly, exercised exhaustively-over-the-fuzzed-domain by `conformance_check.py`
(G-CONF) rather than by sampling a real callee.

There is therefore nothing for G-AX to validate against a live callee, and this
script is a SKIP stub (SPEC_GUIDE: axiom_check.py "may be a skip stub" when the
proof needs no callee axiom). stdlib-only; exit 0.
"""
import sys


def main() -> int:
    print("status=skip reason=no consumed axiom and no opaque callee; "
          "the namespace context is an input and every written node attribute "
          "is modeled deeply and checked by G-CONF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
