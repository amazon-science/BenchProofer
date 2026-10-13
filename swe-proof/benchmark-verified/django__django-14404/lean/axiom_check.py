#!/usr/bin/env python3
"""G-AX — skip stub.

The proof of `correct_catchAll` consumes NO callee property axiom. The one
opaque callee, `resolveLoc` (= django.urls.resolve), is UNCHANGED by the fix and
appears IDENTICALLY in `problem_spec_catchAll` and `implementation_catchAll`
(same argument `routingPath ++ "/"`, same `Option ResolveMatch` result). The
proof discharges the spec by case-splitting on that shared result without
assuming anything about resolve's internal behaviour. There is therefore no
`resolveLoc_prop` axiom to validate.

The entire behaviour change is the redirect-target string (op #6 in
refinement.md), modeled deeply (not axiomatized) and covered by G-CONF.

stdlib-only. Exits with status=skip.
"""
import sys


def main() -> int:
    print("G-AX SKIP: proof consumes no callee axiom "
          "(resolveLoc is an unchanged A-reference, no _prop consumed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
