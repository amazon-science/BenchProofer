#!/usr/bin/env python3
"""G-AX skip stub for django__django-12663.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (the `Query.output_field` property) reports
the type descriptor of a query's output. The behavior the patch changes — which
of a single selected column's two candidate descriptors is reported (its
underlying referenced attribute when present, otherwise its declared output
type) — is modeled DEEPLY by `baseOrDeclared` over an `Option FieldId`
(SPEC_GUIDE §3: a deeply-modeled changed decision is never axiomatized). The
annotation branch returns an observable field descriptor carried directly as
data (`AnnExpr.outputField`); the empty branch returns `none`. There is no
`opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is
nothing for G-AX to validate. The R/I impl (and its binding to the real patched
choice) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12663",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "single-column descriptor choice is modeled deeply "
                  "(baseOrDeclared over Option FieldId) and the annotation/empty "
                  "branches are pure data, so the impl is all R/I (validated by "
                  "G-CONF against the real patched output_field choice)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
