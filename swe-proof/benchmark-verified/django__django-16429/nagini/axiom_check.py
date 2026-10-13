#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16429.

This bundle consumes NO @ContractOnly axiom. The single operation that changes
is modelled DEEPLY: the constructed intermediate reference moment carries the
source moment's time-zone disposition, and the leftover-span difference is
modelled as a guarded operation (`well_defined_diff`) that is defined only when
its two operands share a disposition (both offset-aware or both offset-naive).

G-AX validates that deep model against the REAL `datetime` semantics (the very
library the gold patch relies on) as an A-reference:

  (1) The disposition-compatibility rule for moment subtraction:
      `now - pivot` is well-defined (no exception) exactly when `now` and
      `pivot` are both offset-aware or both offset-naive; an aware/naive mix
      raises TypeError. This is exactly model.py's `same_disposition` guard on
      `well_defined_diff`.

  (2) The fix's effect: constructing the pivot from a source moment's calendar
      and clock fields WITH `tzinfo=d.tzinfo` yields a pivot whose disposition
      matches the source's (so model.py's postcondition `Result().tz is d.tz`
      holds), whereas omitting `tzinfo` (the pre-patch construction) yields a
      naive pivot — which, when the source (hence the current moment) is aware,
      makes the subtraction raise.

  (3) The current moment is established offset-aware exactly when the source is
      (model.py's `same_disposition(now.tz, d.tz)` precondition), matching
      `timesince`'s `datetime.now(utc if is_aware(d) else None)`.

  (4) The ordered-span claim: model.py pins `well_defined_diff`'s result to the
      abstract uninterpreted `moment_span(now, pivot)` — i.e. the real
      difference's value is a deterministic function of its two operands IN
      ORDER. Validated: repeating `(a - b).total_seconds()` yields the same
      value (functionality), and for distinct moments `(a - b)` differs from
      `(b - a)` (order sensitivity: the reversed difference is the negation,
      hence unequal whenever the span is non-zero).

Imports nothing repo-specific: `datetime` is the Python standard library.
Exit 0 iff every obligation holds.
"""
import datetime
import random
import sys


def is_aware(dt):
    """The aware/naive disposition test, exactly as django.utils.timezone."""
    return dt.utcoffset() is not None


def diff_is_defined(now, pivot):
    """Observe whether the REAL `now - pivot` is defined (no exception)."""
    try:
        (now - pivot).total_seconds()
        return True
    except TypeError:
        return False


def build_pivot(d, with_tzinfo):
    """Reference for model.py's pivot construction. `with_tzinfo=True` is the
    fix (carry d.tzinfo); False is the pre-patch construction (naive)."""
    if with_tzinfo:
        return datetime.datetime(
            d.year, d.month, d.day, d.hour, d.minute, d.second, tzinfo=d.tzinfo
        )
    return datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)


def current_moment(d):
    """Reference for `timesince`'s `now` establishment: aware iff d is aware."""
    return datetime.datetime.now(datetime.timezone.utc if is_aware(d) else None)


def check_subtraction_rule(now, pivot):
    """(1) The deep model's guard == the real subtraction's definedness."""
    model_defined = is_aware(now) == is_aware(pivot)  # same_disposition
    real_defined = diff_is_defined(now, pivot)
    assert model_defined == real_defined, (
        "subtraction-rule deep model unsound: now aware=%r pivot aware=%r; "
        "model says defined=%r, real datetime says defined=%r"
        % (is_aware(now), is_aware(pivot), model_defined, real_defined))


def check_fix_makes_pivot_compatible(d):
    """(2)+(3): with the fix, the pivot shares the source's disposition and the
    leftover-span difference against the (matching) current moment is defined;
    the pre-patch construction breaks this whenever the source is aware."""
    now = current_moment(d)
    # the current moment must agree with the source on disposition (model
    # precondition same_disposition(now.tz, d.tz)).
    assert is_aware(now) == is_aware(d), (
        "current moment disposition disagrees with source: now aware=%r "
        "source aware=%r" % (is_aware(now), is_aware(d)))

    fixed_pivot = build_pivot(d, with_tzinfo=True)
    # model postcondition Result().tz is d.tz: same disposition as the source.
    assert is_aware(fixed_pivot) == is_aware(d), (
        "fixed pivot disposition disagrees with source on %r" % (d,))
    assert diff_is_defined(now, fixed_pivot), (
        "fixed pivot leftover-span difference undefined on %r" % (d,))

    prepatch_pivot = build_pivot(d, with_tzinfo=False)  # always naive
    if is_aware(d):
        # the bug: aware source -> aware now -> naive pivot -> undefined diff.
        assert not diff_is_defined(now, prepatch_pivot), (
            "pre-patch construction unexpectedly defined for aware source %r"
            % (d,))


def main():
    tzs = [
        None,
        datetime.timezone.utc,
        datetime.timezone(datetime.timedelta(hours=5, minutes=30)),
        datetime.timezone(datetime.timedelta(hours=-8)),
        datetime.timezone(datetime.timedelta(minutes=195)),
        datetime.timezone(datetime.timedelta(0)),
    ]

    # --- (2)+(3): the fix on representative + fuzzed source moments ---------
    boundary_sources = [
        datetime.datetime(2007, 8, 14, 13, 46, 0),
        datetime.datetime(2022, 1, 1, 0, 0, 0),
        datetime.datetime(1007, 8, 14, 13, 46, 0),
        datetime.datetime(2016, 2, 29, 23, 59, 59),
        datetime.datetime(2080, 1, 1, 0, 0, 0),
    ]
    for base in boundary_sources:
        for tz in tzs:
            d = base.replace(tzinfo=tz)
            check_fix_makes_pivot_compatible(d)

    rng = random.Random(16429)
    for _ in range(20000):
        year = rng.randint(1, 9999)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        hour = rng.randint(0, 23)
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        tz = rng.choice(tzs)
        d = datetime.datetime(year, month, day, hour, minute, second, tzinfo=tz)
        check_fix_makes_pivot_compatible(d)

    # --- (1): the subtraction-definedness rule over all disposition pairs ---
    sample_a = datetime.datetime(2023, 6, 1, 12, 0, 0)
    sample_b = datetime.datetime(2023, 5, 1, 9, 30, 0)
    for tz_a in tzs:
        for tz_b in tzs:
            now = sample_a.replace(tzinfo=tz_a)
            pivot = sample_b.replace(tzinfo=tz_b)
            check_subtraction_rule(now, pivot)

    # --- (4): the ordered-span claim (moment_span functionality + order) ----
    span_pairs = 0
    for tz in tzs:
        for base_b in boundary_sources:
            a = sample_a.replace(tzinfo=tz)
            b = base_b.replace(tzinfo=tz)
            # functionality: the ordered difference is a deterministic function
            # of its operands (so an uninterpreted function models it soundly).
            assert (a - b).total_seconds() == (a - b).total_seconds(), (
                "ordered span not deterministic on %r, %r" % (a, b))
            # order sensitivity: for distinct moments the reversed difference
            # differs (it is the negation of a non-zero span).
            if a != b:
                assert (a - b).total_seconds() != (b - a).total_seconds(), (
                    "reversed span unexpectedly equal on %r, %r" % (a, b))
            span_pairs += 1

    print(
        "G-AX OK: disposition-compatibility deep model == real datetime "
        "subtraction over %d disposition pairs; fix carries the source "
        "disposition (so the leftover-span difference is defined) on %d "
        "boundary + 20000 fuzz source moments; pre-patch construction breaks "
        "it for every aware source; ordered-span claim (deterministic, "
        "order-sensitive) holds on %d same-disposition pairs."
        % (len(tzs) * len(tzs), len(boundary_sources) * len(tzs), span_pairs)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
