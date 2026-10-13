#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25232.

SKIPPED for this bundle. The modeled changed function `initialFillStatistics`'s
impl region is all-A-tagged: its single op is the unchanged callee `constantFill`
(the `SimpleImputer` constant-strategy fit), written as a `:|` choice stub, with
the configured `fillValue` forwarded into it. There is no R/I computational
content to transliterate and differentially test against patch.diff — the entire
behavior is the A-consumed callee, whose soundness is covered by G-AX
(axiom_check.py). The necessity of forwarding the configured constant (vs the
default) is pinned by G-DIFF (the prepatch forwards `none` and fails the
`resolveFill fillValue` clause). Per SPEC_GUIDE §4.1 ("If the impl region is
all-A-tagged, set meta.json conf_skip=true and write a stub that exits with
status=skip").

meta.json records conf_skip=true.
"""
import sys


def main():
    print("status=skip: impl region all-A-tagged (A-consumed callee "
          "constantFill = SimpleImputer constant-strategy fit, with fillValue "
          "forwarded); no R/I content to differentially test. Soundness of the "
          "A leg is covered by G-AX (axiom_check.py); necessity by G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
