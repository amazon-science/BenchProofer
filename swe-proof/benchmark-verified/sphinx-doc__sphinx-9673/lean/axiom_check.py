#!/usr/bin/env python3
"""G-AX — no consumed callee axiom and no A-reference deep model in this bundle.

The modeled procedure (augment_descriptions_with_types) is pure control flow
over abstract inputs: the parsed field markers (each already split into
whitespace-separated tokens by the caller's `re.split(' +', …)`) and the ordered
name->type-text table. Their values are produced by the caller/environment and
are NOT modeled; the classification + back-fill decision logic the fix changes
is spelled out directly (deeply) in the impl, so there is no UNCHANGED callee
whose contract the proof consumes and no deep model that must be validated
against a real callee.

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
