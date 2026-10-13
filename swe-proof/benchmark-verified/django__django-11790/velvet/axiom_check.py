#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11790 -- status=skip.

This bundle has NO axioms and NO deep-model A-references (meta.json
`axioms = []`, `deep_model_references = []`). The patch's behavioral content is
pure control/data flow over one already-computed observation -- the account
model's configured length limit (an int, or None when unset). The modeled
routine derives the effective limit ("configured value, otherwise a default")
and records it on the field's two length facets. It assumes no callee contract,
so there is nothing for G-AX to validate.

The single observation the model takes as a free input (the account model's
configured limit) is produced by an unchanged repository accessor that the patch
does NOT touch; its fidelity is exercised by the G-CONF oracle
(`conformance_check.py`), which runs the real "configured-limit-or-default"
selection, and end-to-end by G-RESOLVE. See mapping.md section 3 and
refinement.md section C.

Stdlib-only; ASCII-only output (avoids the encoding pitfall noted in
docs/LESSONS).
"""
import sys


def main():
    print("G-AX status=skip: django__django-11790 -- no axioms and no "
          "deep-model A-references; the modeled routine assumes no callee "
          "contract (mapping.md section 3). Soundness of the single input "
          "observation (the model's configured limit) is covered by G-CONF "
          "(real configured-limit-or-default selection) + G-RESOLVE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
