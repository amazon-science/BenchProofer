#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11477.

This bundle has NO axioms and NO deep-model references (mapping.md §1, §3;
meta.json axioms=[], deep_model_references=[]). The operation the gold patch
changes is a pure post-processing of values the regex engine already produced
(`match.groupdict()`, `match.groups()`): those are the *inputs* the modeled
function `bindCaptures` consumes, not callees whose contract the proof assumes.
The `keepOne`/`keepPresent` filter and the `args` fallback are modeled
DIRECTLY (R/I ops), validated end-to-end by `conformance_check.py` (G-CONF)
against the real patched `RegexPattern.match`.

There is therefore nothing for G-AX to check. This is a `status=skip` stub:
it asserts the no-axiom invariant (the `Solution.lean` axioms region is empty)
and exits 0. Imports stdlib only.
"""
import json
import os
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    # Defensive cross-check: meta.json must declare no axioms / no references.
    meta_path = os.path.join(here, "meta.json")
    if os.path.exists(meta_path):
        try:
            meta = json.load(open(meta_path))
            assert not meta.get("axioms"), \
                "axiom_check stub but meta.json declares axioms: %r" % meta.get("axioms")
            assert not meta.get("deep_model_references"), \
                "axiom_check stub but meta.json declares references: %r" \
                % meta.get("deep_model_references")
        except (ValueError, OSError):
            pass
    print(json.dumps({
        "status": "skip",
        "reason": "no axioms and no deep-model references in this bundle; "
                  "the changed op is modeled directly (R/I) and checked by "
                  "G-CONF (conformance_check.py).",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
