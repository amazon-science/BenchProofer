#!/usr/bin/env python3
"""G-AX skip stub for django__django-12262.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`django.template.library.parse_bits`)
performs every decision itself — membership tests against the declared
positional / keyword-only names, duplicate detection, positional consumption and
the final completeness check — all modeled DIRECTLY in
`implementation_parseTagArgs`. The only boundary callees, `token_kwargs` and
`parser.compile_filter`, are folded into the `Tok` input encoding (the lexical
classification + value compilation bridge in mapping.md); they are validated as
A-reference boundary ops by conformance_check.py (G-CONF), which drives the REAL
callees, NOT axiomatized. There is no `opaque` callee and no `axiom <callee>_prop`
in Solution.lean, so there is nothing for G-AX to validate.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12262",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "binder logic is modeled directly and the boundary lexical/"
                  "compile callees are A-reference ops validated by G-CONF "
                  "against the real parse_bits",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
