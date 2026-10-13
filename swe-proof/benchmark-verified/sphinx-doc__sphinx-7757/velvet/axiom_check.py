#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7757.

This bundle has **no axioms and no deep-model references** (mapping.md §3): the
modeled behaviour — distributing default values across the positional parameters
of a signature — is pure positional data movement with no unchanged external
callee participating in the computation. `ast_unparse`, the only external function
the changed code touches per default expression, is applied identically and
per-element in both the pre- and post-patch code and is an R-leg identity under
the type bijection (mapping.md §2), checked mechanically by G-CONF
(`conformance_check.py`) against the real patched function — not axiomatized here.

There is therefore nothing for G-AX to execute. Per plan §4 / the worker prompt,
a bundle whose impl region carries no axiom emits a skip verdict. Exit 0.
"""
import json
import sys


def main():
    print(json.dumps({
        "status": "skip",
        "reason": "no-axioms",
        "detail": ("no axiomatized callees and no deep-model references; the "
                   "modeled behaviour is pure positional default distribution "
                   "(mapping.md §3). All impl-region ops are R/I and are checked "
                   "by G-CONF (conformance_check.py)."),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
