#!/usr/bin/env python3
"""G-AX — skip stub.

This bundle declares no `opaque` callee and consumes no `axiom <callee>_prop`:
the only operations (tuple lexicographic comparison and message formatting) are
language primitives modeled DEEPLY in Solution.lean (versionLt + errorMessage),
not axiomatized. There is therefore no callee contract to validate against a real
callee. The whole impl is exercised by G-CONF instead.

exit 0 with status=skip. stdlib-only.
"""
import sys


def main() -> int:
    print("G-AX SKIP: no opaque callee / consumed axiom in this bundle "
          "(all ops modeled deeply; validated by G-CONF). status=skip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
