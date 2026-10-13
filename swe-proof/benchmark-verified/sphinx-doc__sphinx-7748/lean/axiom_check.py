#!/usr/bin/env python3
"""G-AX skip stub for sphinx-doc__sphinx-7748.

The bundle declares one `opaque` callee, `matchSig`, modeling the UNCHANGED
extended-signature regex matcher (`py_ext_sig_re.match`). It is an A-REFERENCE
with NO consumed property: it appears IDENTICALLY in the spec helper `scanDoc`
(`match matchSig line with …`) and in `implementation_collectSignatures`
(`match matchSig line with …`), so it cancels in the correctness argument — the
proof needs no property of it. There is therefore NO `axiom matchSig_prop` in
Solution.lean for G-AX to validate against the real callee.

The behavior the patch actually changes — scanning every leading line of a
block, handling backslash continuations, and collecting all matching signatures
in order — is modeled DEEPLY in Lean (`scanDoc` / `collectSpec` / the imperative
`implementation_collectSignatures`), an R/I leg, and is mechanically
differential-tested against an in-process replica of the patched
`_find_signature` + `format_signature` by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sphinx-doc__sphinx-7748",
        "reason": "the only opaque callee (matchSig / py_ext_sig_re.match) is an "
                  "A-reference with no consumed property — it cancels (identical "
                  "in spec helper scanDoc and in the impl), so there is no axiom "
                  "to validate. The changed behavior (multi-line scan, "
                  "continuation handling, collect-all signatures) is R/I, "
                  "validated by G-CONF.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
