#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11734 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions transliterated
              to Python, via the mapping.md §2 bijection:
                site 1 (`comparisonNormalizesAsValue`): the guard
                  `(not lhsSpansMultipleColumns) and (not isExpression t)`,
                  where `isExpression t = (t != directValue)`;
                site 2 (`subqueryTargetResolution`): `resolveInSubquery(rebind t)`,
                  where `rebind` is the I-tagged post-patch dispatch and
                  `resolveInSubquery` is the A-reference left as the REAL callee
                  `resolve_expression` (A-tagged → run real callee, not the model).
  * ORACLE  — `patch.diff`'s behaviour, computed from the REAL django objects at
              base_commit (the diff does not touch OuterRef/F/ResolvedOuterRef):
                site 1: the post-patch guard
                  `not isinstance(lhs, MultiColSource) and
                   not hasattr(rhs, 'resolve_expression')`;
                site 2: the post-patch rebind composed with the real
                  `resolve_expression`, classified to a Resolution tag.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 11734
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()


def main():
    rng = random.Random(SEED)
    try:
        _setup_django()
        from django.db.models.expressions import OuterRef, F, ResolvedOuterRef
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not load django expressions: %r" % e)
        return 2

    TARGETS = ["outerRef", "localRef", "directValue"]

    # ---- map a Target tag to a REAL filter_rhs object (mapping.md §2) --------
    def real_rhs(target, name="job", value=5):
        if target == "outerRef":
            return OuterRef(name)
        if target == "localRef":
            return F(name)
        return value  # directValue: a plain value (no resolve_expression)

    # =========================== SITE 1 ======================================
    # SHADOW: the I-tagged guard, transliterated from Solution.lean.
    def shadow_site1(lhs_multi, target):
        is_expression = (target != "directValue")          # isExpression t
        return (not lhs_multi) and (not is_expression)      # normalizesAsValue

    # ORACLE: the real post-patch guard on real objects. `lhs` MultiColSource is
    # modeled by a flag (its only role in the guard is isinstance(lhs,...)).
    def oracle_site1(lhs_multi, target):
        rhs = real_rhs(target)
        return (not lhs_multi) and (not hasattr(rhs, "resolve_expression"))

    # =========================== SITE 2 ======================================
    def _classify_resolution(obj):
        # the A-reference leg: the UNCHANGED real resolve_expression callee, run
        # identically in both shadow and oracle (A-tagged → real callee).
        if not hasattr(obj, "resolve_expression"):
            return "plainValue"
        resolved = obj.resolve_expression()
        if isinstance(resolved, ResolvedOuterRef):
            return "resolvesLocally"
        if isinstance(resolved, OuterRef):
            return "staysOuter"
        return "other:" + type(resolved).__name__

    # SHADOW: the I-tagged `rebind` transliterated from Solution.lean as a pure
    # TAG dispatch (Target tag -> Rebound tag), then materialized to the real
    # object the mapping.md §2 bijection assigns that Rebound, then the
    # A-reference real callee. This does NOT inspect the real object's type, so
    # it is independent from the oracle's isinstance dispatch — a genuine
    # differential test of the bijection + dispatch, not a tautology.
    _REBIND_TAG = {                              # Solution.lean `rebind`
        "outerRef": "outerKeepingDepth",
        "localRef": "outerByName",
        "directValue": "unchanged",
    }

    def _materialize_rebound(rebound_tag, name="job", value=5):
        # mapping.md §2: Rebound tag -> the real rebound object
        if rebound_tag == "outerKeepingDepth":
            return OuterRef(OuterRef(name))
        if rebound_tag == "outerByName":
            return OuterRef(name)
        return value                            # unchanged plain value

    def shadow_site2(target):
        rebound_tag = _REBIND_TAG[target]       # I leg (pure tag dispatch)
        rebound_obj = _materialize_rebound(rebound_tag)
        return _classify_resolution(rebound_obj)  # A-reference leg (real callee)

    # ORACLE: patch.diff's site-2 behaviour on the REAL filter_rhs object — the
    # post-patch isinstance rebind hunk, then the unchanged resolution.
    def oracle_site2(target):
        filter_rhs = real_rhs(target)
        if isinstance(filter_rhs, OuterRef):
            rebound = OuterRef(filter_rhs)       # OuterRef(filter_rhs)
        elif isinstance(filter_rhs, F):
            rebound = OuterRef(filter_rhs.name)  # OuterRef(filter_rhs.name)
        else:
            rebound = filter_rhs
        return _classify_resolution(rebound)

    # ---- input stream --------------------------------------------------------
    def inputs(n):
        # boundary cases first (plan §4.1 step 4): full cross product
        for lhs_multi in (False, True):
            for t in TARGETS:
                yield (lhs_multi, t)
        for _ in range(n):
            yield (rng.random() < 0.5, rng.choice(TARGETS))

    disagreements = []
    count = 0
    for lhs_multi, target in inputs(N_FUZZ):
        count += 1
        s1, o1 = shadow_site1(lhs_multi, target), oracle_site1(lhs_multi, target)
        s2, o2 = shadow_site2(target), oracle_site2(target)
        if s1 != o1:
            disagreements.append(("site1", (lhs_multi, target), s1, o1))
        if s2 != o2:
            disagreements.append(("site2", (lhs_multi, target), s2, o2))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for site, inp, sh, orc in disagreements:
            print("  %s input=%r shadow=%r oracle=%r" % (site, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of comparisonNormalizesAsValue (site 1) and "
          "subqueryTargetResolution (site 2) agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
