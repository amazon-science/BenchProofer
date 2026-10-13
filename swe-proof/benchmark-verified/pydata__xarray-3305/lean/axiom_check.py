#!/usr/bin/env python
"""G-AX: axiom soundness for pydata__xarray-3305.

This bundle consumes NO `axiom <callee>_prop`: the fix (defaulting the
keep-attrs request to the resolved global option, selecting the source
attributes iff the resolved request is truthy, and forwarding that same request
through the collection-level reduction loop) is modeled DEEPLY by the pure
helper `resolveKeepAttrs` and the impl skeletons over the inputs (SPEC_GUIDE §3
— a deeply-modeled changed op is never axiomatized). The unchanged callees (the
global-option resolver and the quantile reduction `np.nanpercentile` + dim
removal) are taken as modeled inputs (`globalDefault`, `qs`, `newDims`) and
validated end-to-end by conformance_check.py (G-CONF). There is therefore no
callee contract to validate here.

Exit 0 with status=skip.
"""
import sys


def main():
    print("status=skip no callee axioms declared "
          "(keep-attrs defaulting + attr selection + flag forwarding modeled "
          "deeply; global-option resolver and quantile reduction taken as "
          "modeled inputs, validated end-to-end by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
