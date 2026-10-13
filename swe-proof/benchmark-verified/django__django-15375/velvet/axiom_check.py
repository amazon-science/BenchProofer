#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15375.

This bundle has NO consumed axiom and NO deep-model reference: the change is a
single-line marker propagation, and the distinguishing behaviour is modeled
DIRECTLY in Solution.lean by `Resolved` + `prepared` (refinement.md §C). G-AX
therefore validates the two *unchanged-callee facts the direct model depends on*
by executing the REAL Django objects in-container (mapping.md §3):

  (1) BASE RESOLUTION sets the terminal marker to `summarize`
      (mapping.md §3.1). For a `default`-free aggregate — which NEVER enters the
      changed fallback branch — `resolve_expression(..., summarize=s)` yields a
      clause whose `is_summary == s`. This is the model's `Resolved.isTerminal :=
      terminal` for the bare-aggregation case, and is the marker the fallback
      branch must preserve.

  (2) A FRESHLY BUILT FALLBACK WRAPPER defaults its terminal marker to `False`
      (mapping.md §3.2). A `Coalesce(c, default)` constructed directly carries
      `is_summary is False` (the class default). This is why the propagation is
      NECESSARY: without copying the marker, the wrapper silently drops the
      terminal status — exactly the pre-patch bug `Solution_prepatch.lean`
      reproduces.

Both callees (`Expression/Func.resolve_expression`, `Coalesce.__init__`) are
UNCHANGED by patch.diff, so establishing (1)/(2) does not re-run the changed
default branch (no circularity). The boundary + fuzz inputs cover both summarize
values, different source columns, and a range of fallback values. Imports only
`django` (the module under change) + the standard library. Exit 0 iff every
obligation holds.
"""
import random
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
        )
    django.setup()


def check_base_resolution(summarize):
    """(1) A default-free aggregate's resolved clause carries is_summary ==
    summarize (and is NOT the fallback wrapper)."""
    from django.db.models import Sum, Value
    from django.db.models.functions.comparison import Coalesce

    agg = Sum(Value(1))  # no default => never enters the changed fallback branch
    res = agg.resolve_expression(
        query=None, allow_joins=True, reuse=None, summarize=summarize,
    )
    assert bool(res.is_summary) == bool(summarize), (
        "base resolution with summarize=%r yielded is_summary=%r "
        "(model assumes Resolved.isTerminal := terminal)"
        % (summarize, res.is_summary))
    assert not isinstance(res, Coalesce), (
        "default-free resolution unexpectedly produced a fallback wrapper "
        "(should be the bare aggregation)")


def check_fresh_wrapper_default(default_val):
    """(2) A freshly constructed fallback wrapper defaults is_summary to False
    (the class default the propagation must override)."""
    from django.db.models import Value
    from django.db.models.functions.comparison import Coalesce

    coalesce = Coalesce(Value(1), Value(default_val))
    assert coalesce.is_summary is False, (
        "a freshly built Coalesce had is_summary=%r, expected the class default "
        "False (model: the wrapper drops the marker unless it is propagated)"
        % (coalesce.is_summary,))


def main():
    _configure_django()

    # (1) base resolution sets the terminal marker — both values.
    for summarize in (False, True):
        check_base_resolution(summarize)

    # (2) fresh wrapper defaults to False — boundary + fuzz over fallback values.
    boundary_defaults = [0, 1, -1, 42, -42, 2 ** 31, -(2 ** 31)]
    for d in boundary_defaults:
        check_fresh_wrapper_default(d)

    rng = random.Random(15375)
    for _ in range(2000):
        d = rng.randint(-(10 ** 9), 10 ** 9)
        check_fresh_wrapper_default(d)

    print("G-AX OK: unchanged-callee facts sound on %d summarize values + %d "
          "boundary + 2000 fuzz fallback values: base resolution sets "
          "is_summary == summarize for the bare aggregation; a freshly built "
          "Coalesce defaults is_summary to False (so the marker MUST be "
          "propagated)." % (2, len(boundary_defaults)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
