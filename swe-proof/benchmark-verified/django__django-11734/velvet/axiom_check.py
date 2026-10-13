#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11734.

This bundle declares **no consumed axioms**. The two operations the gold patch
changes (the site-1 comparison-target guard and the site-2 subquery rebind) are
modeled *identically* (`isExpression`/`normalizesAsValue`, `rebind`) and are
handled mechanically by G-CONF (conformance_check.py). There is one **deep-model
reference (A-reference)**: `resolveInSubquery`, which models the UNCHANGED
downstream resolution semantics of a rebound comparison target. G-AX validates
that deep model against the REAL callee `resolve_expression`.

What this script asserts:

  1. (no-axiom claim) meta.json lists no consumed axioms — a future edit that
     smuggles in an `axiom` without an executable soundness check is caught here.

  2. (A-reference) for every `Rebound` value, the REAL django object the bijection
     (mapping.md §2) maps it to, consulted via the REAL `resolve_expression`,
     classifies to exactly the `Resolution` `resolveInSubquery` predicts:
        outerKeepingDepth  (OuterRef(OuterRef(name)))  -> staysOuter
        outerByName        (OuterRef(name))            -> resolvesLocally
        unchanged          (plain value)               -> plainValue

  3. (R bijection, falsifiable) the site-1 builtin the guard refines —
     `hasattr(rhs, 'resolve_expression')` — has the fixed semantics mapping.md §2
     claims for each `Target` kind (OuterRef/F have it; plain values don't), and
     the site-2 `rebind` dispatch (`isinstance(filter_rhs, OuterRef/F)`) routes
     each real object to the right `Rebound`.

Imports only the standard library + django (the same module the gold patch
edits). Exit 0 iff every obligation holds.
"""
import json
import os
import sys


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()


def check_no_consumed_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    assert axioms == [], (
        "axiom_check expected no consumed axioms but meta.json lists %r; a "
        "consumed axiom requires an executable soundness check here." % (axioms,))


# --- the deep model resolveInSubquery (kept in lock-step with Solution.lean) --
# Rebound -> Resolution
_RESOLVE_MODEL = {
    "outerKeepingDepth": "staysOuter",
    "outerByName": "resolvesLocally",
    "unchanged": "plainValue",
}

# rebind: Target -> Rebound (mirrors Solution.lean `rebind`, the site-2 dispatch)
_REBIND_MODEL = {
    "outerRef": "outerKeepingDepth",
    "localRef": "outerByName",
    "directValue": "unchanged",
}


def main():
    check_no_consumed_axioms()
    _setup_django()
    from django.db.models.expressions import OuterRef, F, ResolvedOuterRef

    # ---- build the REAL rebound objects the bijection maps each Rebound to ---
    # mapping.md §2:
    #   outerKeepingDepth <-> OuterRef(OuterRef(name))   (site-2 OuterRef(filter_rhs))
    #   outerByName       <-> OuterRef(name : str)       (site-2 OuterRef(filter_rhs.name))
    #   unchanged         <-> a plain value (no resolve_expression)
    def real_rebound(rebound_kind, name="job"):
        if rebound_kind == "outerKeepingDepth":
            return OuterRef(OuterRef(name))
        if rebound_kind == "outerByName":
            return OuterRef(name)
        if rebound_kind == "unchanged":
            return 5  # representative plain value
        raise AssertionError("unknown Rebound %r" % rebound_kind)

    def classify_resolution(obj):
        """Classify the REAL resolve_expression outcome into a Resolution tag."""
        if not hasattr(obj, "resolve_expression"):
            return "plainValue"
        resolved = obj.resolve_expression()
        # ResolvedOuterRef is an F subclass; check it first.
        if isinstance(resolved, ResolvedOuterRef):
            return "resolvesLocally"
        if isinstance(resolved, OuterRef):
            return "staysOuter"
        # any other expression (should not happen for these inputs)
        return "other:" + type(resolved).__name__

    # ---- (2) A-reference: resolveInSubquery == real resolve_expression -------
    names = ["job", "pk", "x", "responsibility", ""]
    for rebound_kind, expected in _RESOLVE_MODEL.items():
        for nm in names:
            obj = real_rebound(rebound_kind, nm)
            observed = classify_resolution(obj)
            assert observed == expected, (
                "A-reference resolveInSubquery unsound on Rebound=%r (name=%r): "
                "real resolve_expression classifies as %r, deep model says %r"
                % (rebound_kind, nm, observed, expected))

    # ---- (3a) R bijection site 1: hasattr resolve_expression per Target ------
    # OuterRef/F are expressions (have resolve_expression); a plain value is not.
    assert hasattr(OuterRef("x"), "resolve_expression") is True
    assert hasattr(F("x"), "resolve_expression") is True
    assert hasattr(5, "resolve_expression") is False
    assert hasattr("a_string", "resolve_expression") is False
    # and none of these are directly SQL-renderable (the OLD, replaced predicate)
    # — confirming the pre-patch `rhs_is_direct_value` (= not hasattr as_sql)
    # WOULD have treated an OuterRef as a direct value (the bug).
    assert hasattr(OuterRef("x"), "as_sql") is False
    assert hasattr(F("x"), "as_sql") is False

    # ---- (3b) R dispatch site 2: rebind routing via real isinstance ----------
    def real_rebind_of_target(filter_rhs):
        # transliteration of the post-patch split_exclude dispatch
        if isinstance(filter_rhs, OuterRef):
            return "outerKeepingDepth"   # OuterRef(filter_rhs)
        elif isinstance(filter_rhs, F):
            return "outerByName"         # OuterRef(filter_rhs.name)
        else:
            return "unchanged"
    target_objs = {
        "outerRef": OuterRef("job"),
        "localRef": F("job"),
        "directValue": 5,
    }
    for target_kind, obj in target_objs.items():
        got = real_rebind_of_target(obj)
        assert got == _REBIND_MODEL[target_kind], (
            "rebind dispatch mismatch for Target=%r: real isinstance routes to "
            "Rebound=%r, model says %r"
            % (target_kind, got, _REBIND_MODEL[target_kind]))

    print("G-AX OK: A-reference resolveInSubquery == real resolve_expression on "
          "%d (Rebound x name) cases; site-1 hasattr(resolve_expression) and "
          "site-2 rebind dispatch match the mapping.md bijection; bundle "
          "declares no consumed axioms." % (len(_RESOLVE_MODEL) * len(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
