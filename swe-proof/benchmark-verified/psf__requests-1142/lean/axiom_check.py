#!/usr/bin/env python3
"""G-AX — skip stub for psf__requests-1142.

The modeled function `prepare_content_length` invokes no UNCHANGED callee whose
behavior must be axiomatized. Its only data dependencies are:
  * the request method string (an input), and
  * the content length of the body, which is a TYPE REFINEMENT of the real
    code's two length-producing branches (`body.tell()` / `len(body)`) — both
    render the length in decimal, so they are modeled as the abstract `Nat`
    length, not as an opaque callee.

The `axioms` region of Solution.lean therefore declares no `opaque` callee and
the proof consumes no `_prop` axiom. There is nothing for G-AX to validate.

stdlib-only. Emits status=skip and exits 0.
"""
import sys


def main():
    print("G-AX skip: no consumed callee axiom / no opaque callee "
          "(prepare_content_length is self-contained over method + body length)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
