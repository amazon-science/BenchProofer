#!/usr/bin/env python
"""G-CONF skip stub for pydata__xarray-3677.

`implementation_merge` has no R/I computational content to differential-test.
Its only operations are:

  * a match on the shape of the second operand that, for a single named array,
    interprets it via the unchanged coercion `datasetOfArray` (== `to_dataset`),
    and for a dataset uses it unchanged — an A-reference callee, no arithmetic to
    reconstruct in Python; and
  * a tail delegation to the unchanged dataset-to-dataset merge `mergeDatasets`
    (== the merge guts), also an A-reference callee.

There is no R or I leg (no concrete transliterable computation) to build a Python
R/I shadow from, so there is nothing for the differential conformance test to
diff. The behavior of the A-reference callees against the real repo is validated
by `axiom_check.py` (G-AX) instead. `meta.json` records `conf_skip = true`.

Exit with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip impl region is all-A-tagged (A-reference callees "
          "datasetOfArray/mergeDatasets validated by G-AX); no R/I leg to "
          "differential-test")
    sys.exit(0)
