#!/usr/bin/env python3
"""G-AX skip stub for django__django-15554.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled slice (`Query.setup_joins` + `Query.join` alias
allocation) decides which alias a freshly-built join is registered under when
resolving a filtered relation. The behavior the patch changes — confining reuse
to the explicitly-permitted set on the filtered-relation path
(`reuse = can_reuse if join.m2m or reuse_with_filtered_relation else None`) and
the resulting refusal to collapse two same-base filtered joins — is modeled
DEEPLY over the data (`matchCandidates` / `chooseAlias` over the registry, the
permitted set, and the join compatibility keys). The compatibility test
`Join.equals` is modeled directly as `keysEqual` (base parts only, filter
ignored), not axiomatized (SPEC_GUIDE §3: a deeply-modeled changed op's callee is
an A-reference, never a consumed axiom; here it is modeled inline so not even an
A-reference). The unchanged callees (`table_alias`, `ref_alias`) contribute no
property the spec consumes: the fresh alias is supplied as data (`freshAlias`)
and refcounts are not observable in the modeled value. There is no `opaque`
callee and no `axiom <callee>_prop` in Solution.lean, so there is nothing for
G-AX to validate. The R/I impl (and its binding to the real patched allocation)
is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-15554",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "reuse-set decision and registry update are modeled deeply "
                  "(matchCandidates / chooseAlias / keysEqual), so the impl is "
                  "all R/I (validated by G-CONF against the real patched "
                  "setup_joins/join allocation)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
