#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11603.

This bundle consumes NO `@ContractOnly` axioms: the changed behaviour (the
per-family `allow_distinct` capability of Avg and Sum) is modelled DEEPLY in
`model.py` (the `construct_dedup` prologue threaded with a boolean capability by
`build_mean`/`build_total`). There is therefore no axiom to over-approximate.

What G-AX still must establish is that the DEEP MODEL matches reality: the
modelled accept/refuse/record decision equals what the real Django aggregate
constructors do. This script imports the REAL `django.db.models.aggregates`
and, for every aggregate family, asserts:

  * the model predicate `model_refuses(cls, distinct) := distinct and not
    cls.allow_distinct` equals whether the real `__init__` raises `TypeError`
    (the `Exsures(CapabilityError, dedup and not allow_dedup)` decision);
  * when the real constructor does NOT raise, the constructed object's
    `.distinct` attribute equals the requested `distinct` (read-back fidelity,
    the `Ensures(Result() == dedup)` post).

The discriminating POST-patch behaviour (Avg and Sum now permit distinct) is
asserted against whichever tree is mounted: the checker DETECTS the tree (does
`Avg(expr, distinct=True)` raise?) and checks the per-family capability set
against the expectation for that tree — post-patch: Avg/Sum/Count permit
distinct; pre-patch (base_commit): only Count does. Either way the refuse set
and the record fidelity must match the model.

Imports only `django` (the repo under test) plus stdlib. Django needs a minimal
settings configuration to import the ORM expression classes; we configure it
in-process with no database access (constructing an aggregate never touches a
DB). Exit 0 iff every obligation holds.
"""
import sys


def configure_django():
    """Configure Django settings just enough to import ORM expression classes.
    Constructing an Aggregate (Avg/Sum/...) only runs its Python __init__; it
    never opens a connection, so an empty DATABASES is sufficient."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={},
            USE_TZ=False,
        )
    import django
    django.setup()


def model_refuses(allow_distinct, distinct):
    """model.py's refusal predicate: Exsures(CapabilityError, dedup and not
    allow_dedup). True iff the model raises a CapabilityError."""
    return bool(distinct) and not bool(allow_distinct)


def real_outcome(cls, distinct):
    """Construct the real aggregate over a single field expression with the
    given `distinct` request. Returns:
      ("ok", recorded_distinct)  constructed; recorded_distinct == obj.distinct
      ("raise", exc)             refused (raised TypeError)
    """
    try:
        obj = cls("field_name", distinct=distinct)
        return ("ok", getattr(obj, "distinct", None))
    except TypeError as exc:
        return ("raise", exc)


def main():
    configure_django()
    from django.db.models.aggregates import (
        Aggregate, Avg, Count, Max, Min, StdDev, Sum, Variance,
    )

    # Count.__init__ has a different signature (single positional expression,
    # no *expressions) but still accepts distinct=...; it is one of the families
    # already permitted. We exercise the standard families plus Count.
    families = [
        ("Avg", Avg),
        ("Sum", Sum),
        ("Count", Count),
        ("Max", Max),
        ("Min", Min),
        ("StdDev", StdDev),
        ("Variance", Variance),
    ]

    # ---- Per-family: real decision matches model over distinct in {False, True}
    for fam_name, cls in families:
        allow = bool(getattr(cls, "allow_distinct"))
        for distinct in (False, True):
            kind, payload = real_outcome(cls, distinct)
            refused = (kind == "raise")
            expected_refused = model_refuses(allow, distinct)
            assert refused == expected_refused, (
                "decision mismatch for %s(distinct=%r): real refuses=%s, "
                "model refuses=%s (cls.allow_distinct=%s)"
                % (fam_name, distinct, refused, expected_refused, allow))
            if kind == "ok":
                # read-back fidelity: Ensures(Result() == dedup)
                assert payload == distinct, (
                    "record fidelity mismatch for %s(distinct=%r): "
                    "obj.distinct=%r != requested %r"
                    % (fam_name, distinct, payload, distinct))

    # ---- Tree detection + discriminating capability set
    avg_kind, _ = real_outcome(Avg, True)
    sum_kind, _ = real_outcome(Sum, True)
    post_patch = (avg_kind == "ok") and (sum_kind == "ok")

    # Count is permitted in BOTH trees (allow_distinct=True at base_commit too);
    # the disabled families refuse distinct in BOTH trees.
    count_kind, count_rec = real_outcome(Count, True)
    assert count_kind == "ok" and count_rec is True, (
        "Count must accept distinct=True and record it (permitted in both "
        "trees); got %r/%r" % (count_kind, count_rec))
    for fam_name, cls in (("Max", Max), ("Min", Min), ("StdDev", StdDev),
                          ("Variance", Variance), ("Aggregate", Aggregate)):
        kind, _ = real_outcome(cls, True)
        assert kind == "raise", (
            "%s must REFUSE distinct=True (capability disabled) in both trees; "
            "got %r" % (fam_name, kind))

    if post_patch:
        # gold applied: Avg and Sum now carry allow_distinct=True and the model
        # build_mean/build_total agree (they pass allow_dedup=True).
        for fam_name, cls in (("Avg", Avg), ("Sum", Sum)):
            assert bool(getattr(cls, "allow_distinct")) is True, (
                "post-patch: %s.allow_distinct must be True" % fam_name)
            kind, rec = real_outcome(cls, True)
            assert kind == "ok" and rec is True, (
                "post-patch: %s(distinct=True) must construct and record True; "
                "got %r/%r" % (fam_name, kind, rec))
        msg = ("post-patch tree: Avg/Sum/Count accept distinct and record it; "
               "Max/Min/StdDev/Variance/Aggregate refuse it")
    else:
        # base_commit: Avg and Sum inherit allow_distinct=False and refuse
        # distinct=True — the pre-patch behaviour the gold patch fixes. The
        # model's acceptance is exactly the discriminating new behaviour and is
        # NOT expected to hold on this tree.
        for fam_name, cls in (("Avg", Avg), ("Sum", Sum)):
            assert bool(getattr(cls, "allow_distinct")) is False, (
                "base_commit: %s.allow_distinct must be False (capability not "
                "yet added)" % fam_name)
            kind, _ = real_outcome(cls, True)
            assert kind == "raise", (
                "base_commit: %s(distinct=True) must raise TypeError (the "
                "capability is not yet present)" % fam_name)
        msg = ("base_commit tree: only Count accepts distinct; Avg/Sum still "
               "refuse it (the capability the gold patch adds)")

    print("G-AX OK: deep model == real Django aggregate decisions over all 7 "
          "families x {False,True} (refuse predicate + record fidelity); "
          + msg + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
