#!/usr/bin/env python3
"""G-AX — no consumed callee axiom and no A-reference deep model in this bundle.

Both modeled sites derive their result strings directly from the term/reference
text by straight-line code (pass-through, preserving exact characters). There is
no UNCHANGED callee whose contract the proof consumes, and no deep model that
must be validated against a real callee. The only behavior under spec is the
identity pass-through, which has no callee dependency.

Per SPEC_GUIDE §0.7 / conformance_check.py, this gate is a skip stub:
exit 0 with status=skip. (The R/I control-flow behaviour is exercised by
G-CONF instead.)
"""
import sys


def main() -> int:
    print("G-AX SKIP: no consumed axiom and no A-reference; nothing to validate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
