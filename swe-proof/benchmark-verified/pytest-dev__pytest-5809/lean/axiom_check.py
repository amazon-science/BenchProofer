#!/usr/bin/env python3
"""G-AX skip stub for pytest-dev__pytest-5809.

No consumed callee axiom is declared in the bundle and no deep-model
A-reference is used: the parameter mapping is assembled from string literals
plus the verbatim caller-supplied `contents`, with no unchanged repo callee
contract entering the proof. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to
validate. The full R/I impl is differential-tested by conformance_check.py
(G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "pytest-dev__pytest-5809",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
