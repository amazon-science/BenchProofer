#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15375.

This bundle consumes NO @ContractOnly axiom: the modelled behaviour is an
attribute-propagation fix reproduced concretely (kind I/R). What G-AX validates
here are the UNCHANGED-CALLEE facts the refinement relies on, against the REAL
Django code in the BASE-COMMIT (pre-patch) container image (an A-reference style
check — the deep model of the resolution effect is asserted == the real callee).

IMPORTANT: this check asserts ONLY facts present in the pre-patch image. It does
NOT assert the returned wrapper's propagated final-flag — that propagation IS
the fix (`coalesce.is_summary = c.is_summary`) and is absent before the patch;
asserting it here would make the check fail on the base image.

The unchanged-callee facts:

  (1) The unchanged base resolution stamps the requested final-flag onto the
      resolved aggregation: after ``agg.resolve_expression(..., summarize=S)``
      the resolved aggregation's ``is_summary`` equals ``S``. This is observed
      both for an aggregate WITHOUT a fallback (the result IS the aggregate) and
      for the wrapped aggregate INSIDE a fallback wrapper (its first source
      expression). This is the value model.py's ``Expression(requested_final,
      ...)`` records for ``c``.

  (2) When a fallback ``default`` is supplied, the result is a DISTINCT wrapper
      expression (a ``Coalesce``), not the bare aggregate — the unchanged
      fallback-wrapping structure (model.py's ``supplies_fallback == True`` on
      the fallback path; ``Result() is not c``).

  (3) Negative control: a freshly constructed wrapper, BEFORE the propagating
      assignment, carries the class default ``is_summary == False`` (model.py's
      ``Expression(False, True)`` for the unmarked wrapper). This is the
      stranding the fix repairs when ``S`` is True.

  (4) A fallback value that IS itself an expression is supplied in RESOLVED
      form: the value the returned wrapper supplies is a DISTINCT object from
      the value as written, it is structurally equal to a fresh resolution of
      the written value, and it can be used as it stands (it has an ``as_sql``);
      the value as written is left exactly as it was. This is what model.py's
      ``FallbackValue(True)`` / ``resolved.resolution_of = fallback`` records,
      and it is unchanged code (``aggregates.py:65-66``).

  (5) A fallback value that is NOT itself an expression is supplied AS ASKED
      FOR: the value the wrapper supplies carries THAT VERY OBJECT. And --
      the negative control for the *domain* of the specification -- a written
      ``str`` value is represented as a field REFERENCE, which canNOT be used as
      it stands (no ``as_sql``). So "not itself an expression" does NOT imply
      "usable as written": a spec clause assuming it would exclude a realizable
      input.

  (7) Resolving the aggregation puts EVERY part it is built from into resolved
      form -- the operand(s) it aggregates over AND the condition restricting
      it -- so the aggregation the fallback wrapper supplies a fallback FOR can
      be used as it stands: every one of its source expressions, and its
      condition, has an ``as_sql``. NEGATIVE CONTROL for the same fact: the
      operand resolution ALONE (``Func.resolve_expression``, which is what
      ``super().resolve_expression`` at ``aggregates.py:52`` runs) leaves the
      CONDITION unresolved -- resolving it is the very next line,
      ``aggregates.py:53`` -- so an aggregation that merely carries the right
      final-flag is NOT necessarily the aggregation resolution produced. This is
      what model.py's ``c.parts_usable = True`` records, and why the returned
      wrapper's reachable aggregation must carry it.

  (6) The resolved aggregation stops holding the fallback value of its own once
      the wrapper supplies it (``c.default = None``, ``aggregates.py:67``),
      while the aggregation AS WRITTEN does hold it -- model.py's
      ``c.holds_own_fallback = fallback is not None`` followed by
      ``c.holds_own_fallback = False``. The returned wrapper holds no fallback
      value of its own either.

Run inside the official SWE-bench container for the instance, where Django is
importable. Imports only Django itself (the package the patched module lives
in); nothing test-private. Exit 0 iff every obligation holds. A configuration
failure is a HARD ERROR (no silent skip): the gate must execute its assertions.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    # No silent swallow-and-pass: a setup failure is a hard error so the gate
    # cannot vacuously exit 0 without running a single assertion.
    _configure_django()

    from django.db import models
    from django.db.models import F, Q, Sum, Avg, Min, Max, Count, Value
    from django.db.models.functions import Coalesce, Lower

    # A minimal model providing real fields for the aggregates to resolve over.
    # Piggy-back on the already-registered "contenttypes" app label (no
    # fabricated INSTALLED_APPS entry).
    class Widget(models.Model):
        num = models.IntegerField()
        rating = models.FloatField()

        class Meta:
            app_label = "contenttypes"

    query = Widget.objects.all().query

    observations = 0

    aggregate_specs = [
        Sum("num", default=0),
        Avg("rating", default=2.5),
        Min("num", default=0),
        Max("num", default=0),
        Sum(F("num") * 2, default=0),
    ]
    for summarize in (True, False):
        for agg in aggregate_specs:
            resolved = agg.resolve_expression(query, summarize=summarize)

            # (2) the fallback path returns a DISTINCT Coalesce wrapper (not the
            #     bare aggregate) — the unchanged fallback-wrapping structure
            #     (model.py: supplies_fallback == True; Result() is not c).
            assert isinstance(resolved, Coalesce), (
                "expected a Coalesce wrapper for an aggregate with a default, "
                "got %r" % (type(resolved),))

            # (1) the WRAPPED, resolved aggregation carries is_summary ==
            #     summarize (the value model.py records for c). The first source
            #     expression of the Coalesce is the resolved aggregate. This is
            #     set by the UNCHANGED super().resolve_expression — present in
            #     the base image. (We do NOT assert the wrapper's own
            #     is_summary: that propagation is the fix, absent pre-patch.)
            inner = resolved.get_source_expressions()[0]
            assert inner.is_summary == summarize, (
                "wrapped aggregate is_summary=%r != summarize=%r for %r"
                % (inner.is_summary, summarize, agg))
            observations += 1

    # Aggregate WITHOUT a fallback resolves to the aggregate ITSELF (not a
    # wrapper), still carrying is_summary == summarize (the no-fallback branch
    # of model.py: supplies_fallback == False, returns c).
    for summarize in (True, False):
        for agg in (Sum("num"), Avg("rating"), Count("num")):
            resolved = agg.resolve_expression(query, summarize=summarize)
            assert not isinstance(resolved, Coalesce), (
                "expected the bare aggregate without a default, got Coalesce")
            assert resolved.is_summary == summarize, (
                "no-fallback aggregate is_summary=%r != summarize=%r for %r"
                % (resolved.is_summary, summarize, agg))
            observations += 1

    # (4) An expression-valued fallback is supplied in RESOLVED form, and the
    #     value AS WRITTEN is left exactly as it was. Unchanged code
    #     (`default = default.resolve_expression(...)`, aggregates.py:65-66).
    for summarize in (True, False):
        for written in (Value(0), F("num"), Lower(Value("AB")), F("num") * 2):
            usable_before = hasattr(written, "as_sql")
            agg = Sum("num", default=written)
            resolved = agg.resolve_expression(query, summarize=summarize)
            supplied = resolved.get_source_expressions()[1]
            assert supplied is not written, (
                "the supplied fallback is the very object as written (%r): no "
                "resolved form was produced" % (written,))
            fresh = written.resolve_expression(query, True, None, summarize)
            assert supplied == fresh, (
                "the supplied fallback %r is not the resolved form of the "
                "written value %r (fresh resolution %r)"
                % (supplied, written, fresh))
            assert hasattr(supplied, "as_sql"), (
                "the supplied fallback %r cannot be used as it stands"
                % (supplied,))
            # the value as written is untouched (as usable as it arrived)
            assert hasattr(written, "as_sql") == usable_before, (
                "the written fallback value %r changed usability in place"
                % (written,))
            observations += 1

    # (5) A fallback value that is NOT an expression is supplied AS ASKED FOR --
    #     the wrapper carries THAT VERY OBJECT -- and a written `str` is
    #     represented as a field REFERENCE, which cannot be used as it stands.
    #     The second half is the negative control for the DOMAIN of the spec: a
    #     clause assuming a non-expression fallback is usable as written would
    #     exclude a realizable input.
    plain_usability = set()
    for summarize in (True, False):
        for written in (0, -7, 2.5, False, "", "zz"):
            agg = Sum("num", default=written)
            resolved = agg.resolve_expression(query, summarize=summarize)
            supplied = resolved.get_source_expressions()[1]
            assert not hasattr(written, "resolve_expression"), (
                "%r was expected to be a plain value" % (written,))
            carried = getattr(supplied, "value", None) if isinstance(
                supplied, Value) else getattr(supplied, "name", None)
            assert carried is written, (
                "the supplied fallback %r does not carry the very object "
                "written (%r)" % (supplied, written))
            plain_usability.add(hasattr(supplied, "as_sql"))
            observations += 1
    assert plain_usability == {True, False}, (
        "a written non-expression fallback was expected to be usable as it "
        "stands in some cases and NOT in others (a str becomes a field "
        "reference); observed %r" % (sorted(plain_usability),))

    # (6) The resolved aggregation stops holding a fallback value of its own
    #     once the wrapper supplies it (`c.default = None`, aggregates.py:67),
    #     while the aggregation AS WRITTEN still holds it; and the returned
    #     wrapper holds none of its own either.
    for summarize in (True, False):
        agg = Sum("num", default=0)
        resolved = agg.resolve_expression(query, summarize=summarize)
        assert agg.default is not None, (
            "the aggregation as written no longer holds its fallback value")
        assert resolved.get_source_expressions()[0].default is None, (
            "the wrapped aggregation still holds a fallback value of its own")
        assert getattr(resolved, "default", None) is None, (
            "the returned wrapper holds a fallback value of its own")
        observations += 1

    # (7) Every part of the resolved aggregation is in resolved form, and the
    #     operand resolution ALONE is not enough: it leaves the condition
    #     unresolved (that is aggregates.py:53, one line further on). An
    #     aggregation built or half-resolved that way carries the right
    #     final-flag but cannot be used as it stands.
    for summarize in (True, False):
        agg = Sum("num", filter=Q(rating__lt=3.0), default=0)
        resolved = agg.resolve_expression(query, summarize=summarize)
        inner = resolved.get_source_expressions()[0]
        for src in inner.get_source_expressions():
            assert hasattr(src, "as_sql"), (
                "a source expression of the resolved aggregation (%r) is not in "
                "resolved form" % (src,))
        assert inner.filter is not None, "expected the aggregation to carry a condition"
        assert hasattr(inner.filter, "as_sql"), (
            "the condition of the resolved aggregation (%r) is not in resolved "
            "form" % (inner.filter,))
        # NEGATIVE CONTROL: the operand resolution alone -- exactly what
        # super().resolve_expression at aggregates.py:52 performs, i.e.
        # Func.resolve_expression (expressions.py:694-699), which walks
        # ``c.source_expressions`` directly and so never reaches the condition --
        # leaves the CONDITION unresolved. Resolving it is the very next line,
        # aggregates.py:53. So an aggregation obtained that way carries the
        # requested final-flag and fully resolved operands, yet CANNOT be used as
        # it stands.
        half = models.Func.resolve_expression(agg, query, True, None, summarize)
        for src in models.Func.get_source_expressions(half):
            assert hasattr(src, "as_sql"), (
                "the operand resolution was expected to resolve the operands, "
                "got %r" % (src,))
        assert half.filter is not None and not hasattr(half.filter, "as_sql"), (
            "the operand resolution alone was expected to leave the condition "
            "unresolved, got %r" % (half.filter,))
        assert half.is_summary == summarize, (
            "the operand resolution alone still stamps the requested final-flag")
        observations += 1

    # The bare (no-fallback) resolved aggregation is likewise usable as it
    # stands: every part of it is in resolved form.
    for summarize in (True, False):
        agg = Sum("num", filter=Q(rating__lt=3.0))
        resolved = agg.resolve_expression(query, summarize=summarize)
        for src in resolved.get_source_expressions():
            assert hasattr(src, "as_sql"), (
                "a source expression of the returned bare aggregation (%r) is "
                "not in resolved form" % (src,))
        assert hasattr(resolved.filter, "as_sql"), (
            "the condition of the returned bare aggregation is not in resolved "
            "form")
        observations += 1

    # (3) Negative control: a freshly constructed Coalesce wrapper, before any
    # propagating assignment, carries the class default is_summary == False.
    # This is exactly the stranding the fix repairs when summarize is True, and
    # what model.py models as Expression(False, True) for the unmarked wrapper.
    fresh = Coalesce(Sum("num"), 0)
    assert fresh.is_summary is False, (
        "expected a fresh Coalesce to default to is_summary False, got %r"
        % (fresh.is_summary,))

    assert observations > 0, "G-AX ran no observations"
    print("G-AX OK: real Aggregate.resolve_expression stamps the requested "
          "final-flag onto the resolved aggregation (bare, and wrapped inside "
          "the fallback Coalesce) over %d observations (both summarize values, "
          "5 aggregate kinds with defaults + 3 without); a fallback yields a "
          "distinct Coalesce wrapper; a fresh wrapper defaults to is_summary "
          "False (the stranding the fix repairs); an expression-valued fallback "
          "is supplied in DISTINCT resolved form, usable as it stands, with the "
          "written value left as it was; a plain fallback is supplied as that "
          "very object, and a written str is a field reference that is NOT "
          "usable as it stands; the wrapped aggregation stops holding a "
          "fallback of its own while the written aggregation keeps it; every "
          "part of the resolved aggregation -- operand AND condition -- is in "
          "resolved form, while the operand resolution ALONE leaves the "
          "condition unresolved (the negative control for an aggregation that "
          "carries the right final-flag without having been resolved). Asserts "
          "only unchanged-callee facts present in the base-commit image."
          % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
