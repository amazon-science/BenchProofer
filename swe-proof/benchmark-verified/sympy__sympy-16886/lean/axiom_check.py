#!/usr/bin/env python3
"""G-AX skip stub for sympy__sympy-16886.

No consumed callee axiom is declared in the bundle and no A-reference is
axiomatized. The modeled behavior (`encode_morse` per-character lookup +
separator join) is specified against the authoritative standard Morse alphabet,
modeled DEEPLY as the concrete total function `charMorse` in Solution.lean; the
program's own table is modeled deeply as `codeMorse`. Neither is an `opaque`
callee with an `axiom <callee>_prop` contract — they are concrete functions, so
there is nothing for G-AX to validate against a real callee. The program table's
agreement with the real `char_morse` is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sympy__sympy-16886",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "Morse code-word tables are concrete total functions (charMorse "
                  "= authoritative standard alphabet in the spec; codeMorse = the "
                  "program's table in the impl), so the impl is all R/I/A-reference "
                  "(validated by G-CONF against the real char_morse table).",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
