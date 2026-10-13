#!/usr/bin/env python3
"""G-AX — skip stub for django__django-11477.

The bundle consumes NO callee axiom. The behavior the patch changes — discarding
the named captures whose value is absent (`None`), and the consequent positional
fallback — is modeled DEEPLY in Solution.lean (`namedCaptures.filter carriesValue`
and the `named.isEmpty` decision), not axiomatized (SPEC_GUIDE §3, §0.7). The
scan/regex-search result is supplied as input data (`ScanOutcome`), so the proof
needs no property of any unchanged callee. There is therefore nothing for G-AX to
validate; it skips.
"""
import sys

if __name__ == "__main__":
    print("status=skip")
    print("reason=no consumed callee axiom; changed op modeled deeply")
    sys.exit(0)
