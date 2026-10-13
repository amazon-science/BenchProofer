#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16938 (plan §4.1).

STATUS = SKIP (reason="no-RI-content").

G-CONF mechanically refutes the **R** (type-rename) and **I** (identical-op)
legs of refinement.md by transliterating only those ops to Python and diffing
against patch.diff's behaviour over fuzzed inputs.  For this bundle there is no
R/I *content* to transliterate:

  * The fix is a CONTROL/COMPOSITION change — the gold patch inserts a no-arg
    `.select_related()` call before `.only("pk")` inside the m2m relation
    iterator closure `queryset_iterator` (django/core/serializers/python.py and
    xml_serializer.py).  It introduces no type-refined data value (no
    `str`/`list`/`dict` carrier to bridge) and no arithmetic / identical
    concrete computation.
  * Every value-carrying operation in `Solution.lean`'s impl region is an
    **A-reference** transformer (`selectAllRelated` <- `QuerySet.select_related()`,
    `loadOnlyPk` <- `QuerySet.only("pk")`) standing for an unchanged repository
    callee.  Per plan §4.1 step 1, G-CONF leaves A-tagged callees as the real
    repo callee and does NOT transliterate them; their soundness is G-AX's job.
  * What remains in the impl region after removing the A legs is the
    `planRejected` predicate — itself an A-reference model of
    `select_related_descend`'s raise condition — over those transformers.  That
    skeleton has no cross-language *data* carrier to sample, so there is no R/I
    shadow to build (the §4.1 "impl region is all-A-tagged → status=skip" case).

The full weight of the cross-language argument therefore falls on G-AX (each
A-reference callee validated against the real Django queryset / SQL-compiler
machinery — see axiom_check.py: the no-arg select_related resets to the
unrestricted boolean form, only("pk") defers the related fk, and the model's
planRejected predicate equals the real compiler's FieldError verdict across the
restricted/unrestricted x only/full-load matrix) and on G-EQ / G-PANEL (that the
composition skeleton is a faithful image of the patch and the spec pins the
behaviour the issue + F2P tests demand).  This bundle is flagged `conf_skip` in
meta.json, carrying the most residual trust (plan §4.1, §11.2).

Exit code 0 with status=skip (a skip counts as passing per plan §11.1).
"""
import json
import sys


def main():
    result = {
        "gate": "G-CONF",
        "status": "skip",
        "reason": "no-RI-content",
        "detail": (
            "control/composition fix (inserted no-arg select_related() before "
            "only('pk')); impl region's value-carrying ops are all A-reference "
            "callees, residual content is the planRejected predicate over them "
            "with no R/I data to differentially fuzz"),
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
