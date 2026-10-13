#!/usr/bin/env python3
"""G-AX skip stub for sphinx-doc__sphinx-8269.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function classifies one external link into its
`(status, info, code)` outcome on the anchor-enabled path. The fix's new
operation (`response.raise_for_status()` plus the existing `except HTTPError`
status dispatch) is the operation the patch changes, so it is modeled DEEPLY in
Solution.lean (the `400 <= statusCode < 600` raise threshold and the
401/503/else routing) rather than axiomatized (SPEC_GUIDE 0.7). The two server
observations (the reply's status code and whether the fragment is present), the
explanatory messages, and the unchanged success/redirect tail are modeled as
arbitrary inputs (`statusCode`, `anchorFound`, `httpErrMsg`, `anchorErrMsg`,
`onSuccess`), so the spec holds for every choice of them and the proof consumes
no property of any opaque callee. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The status-precedence classification (and its binding to the real success tail)
is differential-tested by conformance_check.py (G-CONF), which exercises the
raise_for_status threshold through the REAL `requests.Response.raise_for_status`.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sphinx-doc__sphinx-8269",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "raise_for_status threshold + HTTPError dispatch is modeled "
                  "deeply and the unchanged success tail is universally "
                  "quantified (onSuccess), so the impl is all R/I/A-reference "
                  "(validated by G-CONF against a faithful replica of the patched "
                  "check_uri classification, with the raise threshold driven "
                  "through the real requests.Response.raise_for_status)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
