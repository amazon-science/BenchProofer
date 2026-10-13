#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16333 (plan §4.1).

STATUS = SKIP (reason="no-RI-content").

G-CONF mechanically refutes the **R** (type-rename) and **I** (identical-op)
legs of refinement.md by transliterating only those ops to Python and diffing
against patch.diff's behaviour over fuzzed inputs.  For this bundle there is no
R/I *content* to transliterate:

  * The fix is a CONTROL-FLOW / side-effect change — the gold patch adds the
    guarded statement `if hasattr(self, "save_m2m"): self.save_m2m()` to the
    commit branch of `UserCreationForm.save`.  It introduces no type-refined
    data value (no `str`/`list`/`dict` carrier to bridge) and no arithmetic /
    identical concrete computation.
  * Every value-carrying operation in `Solution.lean`'s impl region is an
    **A-reference** state transformer (`prepareDeferred`, `applyCredential`,
    `persistObject`, `persistRelated`) standing for an unchanged repository
    callee.  Per plan §4.1 step 1, G-CONF leaves A-tagged callees as the real
    repo callee and does NOT transliterate them; their soundness is G-AX's job.
  * What remains in the impl region after removing the A legs is the pure
    boolean control-flow skeleton (`if commit / if deferredSaveReady`).  That
    skeleton has no cross-language data to sample, so there is no R/I shadow to
    build (the §4.1 "impl region is all-A-tagged → status=skip" case).

The full weight of the cross-language argument therefore falls on G-AX (each
A-reference callee validated against the real Django machinery, see
axiom_check.py) and on G-EQ / G-PANEL (that the control-flow skeleton is a
faithful image of the patch and the spec pins the added behaviour).  This
bundle is flagged `conf_skipped` in the summary, carrying the most residual
trust (plan §4.1, §11.2).

Exit code 0 with status=skip (a skip counts as passing per plan §11.1).
"""
import json
import sys


def main():
    result = {
        "gate": "G-CONF",
        "status": "skip",
        "reason": "no-RI-content",
        "detail": (
            "control-flow/side-effect fix; impl region's value-carrying ops are "
            "all A-reference callees, residual content is boolean control flow "
            "with no R/I data to differentially fuzz"),
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
