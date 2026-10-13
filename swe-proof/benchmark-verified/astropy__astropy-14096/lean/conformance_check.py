#!/usr/bin/env python
"""G-CONF skip stub for astropy__astropy-14096.

Every operation of `implementation_resolveAttr` is A-tagged (both ops are
A-reference callees — the unchanged resolution branches `handledCase`, and the
ordinary attribute-access protocol `ordinaryLookup` the fix defers to). There is
no R/I leg to build a Python R/I shadow from, so there is nothing for the
differential conformance test to diff.

The behavior of the A-reference callees against the real repo is validated by
`axiom_check.py` (G-AX) instead. `meta.json` records `conf_skip = true`.

Exit with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip impl region is all-A-tagged (A-reference callees "
          "validated by G-AX); no R/I leg to differential-test")
    sys.exit(0)
