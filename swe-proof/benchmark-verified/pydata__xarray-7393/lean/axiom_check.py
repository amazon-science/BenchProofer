#!/usr/bin/env python
"""G-AX: axiom soundness for pydata__xarray-7393.

This bundle consumes NO `axiom <callee>_prop`: the two edits the patch makes
(defaulting the requested dtype to the adapter's stored original dtype, and
re-presenting a selected level's raw values at that effective dtype) are both
modeled DEEPLY by the pure helpers `effectiveDtype` and `castArray` over the
inputs (SPEC_GUIDE §3 — a deeply-modeled changed op is never axiomatized). The
unchanged callees (the level read and the non-level conversion) are taken as
modeled inputs and validated end-to-end by conformance_check.py (G-CONF). There
is therefore no callee contract to validate here.

Exit 0 with status=skip.
"""
import sys


def main():
    print("status=skip no callee axioms declared "
          "(dtype defaulting + level re-cast modeled deeply; "
          "level read + non-level conversion taken as modeled inputs, "
          "validated end-to-end by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
