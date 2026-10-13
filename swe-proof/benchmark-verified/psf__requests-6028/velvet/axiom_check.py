#!/usr/bin/env python3
"""G-AX axiom-soundness check for psf__requests-6028 — SKIP (no axioms).

This bundle has NO axiomatized callees and NO deep-model references
(`axioms = []`, `deep_model_references = []` in meta.json). The changed
operation — folding the credentials back into a URL's authority component on
re-assembly — is modeled DEEPLY in Solution.lean (`assembleAuthority` /
`authorityBase`, a pure string computation built entirely from the parsed
slots), not delegated to any unchanged callee. Per SPEC_GUIDE §3, a deeply
modeled op is not a consumed axiom, and there is no dead axiom to validate.

The two real callees that bracket the modeled slice — `urllib3.util.parse_url`
(upstream splitter) and `urlunparse` (downstream re-assembler) — are UNCHANGED
by the patch and are exercised LIVE on both sides of the differential test in
`conformance_check.py` (G-CONF), rather than axiomatized. There is therefore no
axiom contract that could be over-claimed, and nothing for G-AX to run.

Exit code 0 with status=skip (the django__django-11138 / -14376 no-axiom
precedent: G-AX = skip).
"""
import json
import sys


def main():
    print(json.dumps({
        "status": "skip",
        "reason": "no axioms / deep-model references in bundle; the changed op "
                  "is modeled deeply and the bracketing callees "
                  "(parse_url, urlunparse) are unchanged and validated live by "
                  "conformance_check.py (G-CONF).",
        "axioms": [],
        "deep_model_references": [],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
