#!/usr/bin/env python3
"""G-AX for sympy__sympy-18763.

The modeled function (`_print_Subs`) consumes the recursive markup of the body
and of each assignment side as plain string inputs and only assembles them into
the final layout. No UNCHANGED callee property is consumed by the proof — there
is no `axiom <callee>_prop` and no `opaque` callee in Solution.lean. There is
therefore nothing for G-AX to validate.

stdlib-only; emits a JSON skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sympy__sympy-18763",
        "reason": "no consumed callee axiom; rendered sub-strings are R-abstracted inputs",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
