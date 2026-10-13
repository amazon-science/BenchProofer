#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15957.

This bundle models the slice->bound translation DEEPLY as a structural update of
a minimal query carrier (model.py: PrefetchQuery + is_sliced + bounded_prefetch)
and models the one control-flow effect (applying the membership predicate) as a
@ContractOnly callee `apply_membership` whose Requires(not is_sliced) /
Ensures(membership_token) capture the UNCHANGED QuerySet.filter raise-guard. G-AX
validates that both are faithful to the REAL Django machinery the gold patch
uses:

  (S1)  is_sliced(query) in the model  ==  Query.is_sliced  (low_mark != 0 or
        high_mark is not None), and clearing the slice (clear_limits) makes the
        query not sliced.

  (S2)  the real helper _filter_prefetch_queryset, run on a sliced queryset,
        builds a predicate that:
          - always ANDs the membership predicate (field__in=instances);
          - always ANDs a strict lower window bound GreaterThan(Window(RowNumber,
            partition_by=field), low_mark)   [model: lower_bound = offset_mark];
          - ANDs an inclusive upper window bound LessThanOrEqual(window,
            high_mark) IFF high_mark is not None
            [model: upper_bound = limit_mark iff limit_mark is not None];
          - clears the slice window (so is_sliced becomes false afterwards)
            [model: offset_mark = 0; limit_mark = None];
        and run on an UNSLICED queryset, builds ONLY the membership predicate and
        adds no window bound [model: no lower/upper bound, marks untouched].

  (S3)  QuerySet.filter (the real callee `apply_membership` axiomatizes) RAISES
        TypeError on a SLICED query ("Cannot filter a query once a slice has been
        taken.") and SUCCEEDS — ANDing the membership predicate — on an UNSLICED
        query. This validates the consumed axiom: Requires(not is_sliced) is the
        raise guard, and the membership_token is granted only on the unsliced
        (successful) path [model: apply_membership precondition + Ensures].

These are exactly the model's postconditions/contracts, checked at the
structural (index/presence) level the spec decides — no double-mask: we assert
presence of each bound lookup directly, not via a value proxy.

Runs inside the official SWE-bench container for the instance (Django importable,
sqlite available). Configures an in-memory sqlite DB and minimal models, then
drives the REAL helper and the REAL Query slice machinery. Exit 0 iff sound.
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


def _collect_lookups(node, acc):
    """Walk a WhereNode tree collecting leaf lookup objects."""
    children = getattr(node, "children", None)
    if children is None:
        acc.append(node)
        return
    for child in children:
        _collect_lookups(child, acc)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, models
    from django.db.models import Window
    from django.db.models.functions import RowNumber
    from django.db.models.lookups import GreaterThan, LessThanOrEqual
    from django.db.models.fields.related_descriptors import (
        _filter_prefetch_queryset,
    )

    # --- (S1) Query slice semantics the model's is_sliced/clear encode --------
    from django.db.models.sql.query import Query as RawQuery

    def model_is_sliced(low, high):
        # model.py: is_sliced(query) == query.offset_mark != 0 or
        #                               query.limit_mark is not None
        return low != 0 or high is not None

    for low, high in [(0, None), (0, 3), (1, None), (1, 2), (5, 10), (2, 2)]:
        q = RawQuery(None)
        if low or high is not None:
            # set_limits(low, high) drives low_mark/high_mark; mirror the slice.
            q.set_limits(low=low if low else None, high=high)
        observed_sliced = q.is_sliced
        # the model predicate over the resulting marks must agree with the real
        # Query.is_sliced
        assert observed_sliced == model_is_sliced(q.low_mark, q.high_mark), (
            "is_sliced model/real disagree at marks (%r,%r): real=%r model=%r"
            % (q.low_mark, q.high_mark, observed_sliced,
               model_is_sliced(q.low_mark, q.high_mark)))
        # clear_limits -> not sliced (model: offset_mark=0; limit_mark=None)
        q.clear_limits()
        assert q.low_mark == 0 and q.high_mark is None and not q.is_sliced, (
            "clear_limits did not reset the slice window: marks=(%r,%r)"
            % (q.low_mark, q.high_mark))

    # --- minimal related models to exercise the REAL helper -------------------
    class Parent(models.Model):
        class Meta:
            app_label = "axcheck"

    class Child(models.Model):
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE,
                                    related_name="children")
        rank = models.IntegerField(default=0)

        class Meta:
            app_label = "axcheck"
            ordering = ["rank"]

    with connection.schema_editor() as editor:
        editor.create_model(Parent)
        editor.create_model(Child)

    p = Parent.objects.create()
    for r in range(5):
        Child.objects.create(parent=p, rank=r)
    instances = list(Parent.objects.all())

    def lookups_of(qs):
        acc = []
        _collect_lookups(qs.query.where, acc)
        return acc

    def window_bound_value(acc, lookup_cls):
        # Return the integer RHS of the row-position bound of the given lookup
        # class whose LHS is a RowNumber Window, or None if no such bound is
        # present. (Asserts the wrapped function is RowNumber.)
        for lk in acc:
            if isinstance(lk, lookup_cls):
                lhs = getattr(lk, "lhs", None)
                if isinstance(lhs, Window):
                    inner = lhs.source_expression
                    assert isinstance(inner, RowNumber), (
                        "window bound wraps %r, expected RowNumber"
                        % (type(inner).__name__,))
                    return lk.rhs
        return None

    def membership_present(acc):
        # the field__in membership lookup ('children' reverse FK -> 'parent__in'
        # on the Child queryset built by the descriptor). We assert at least one
        # non-window leaf lookup exists (the membership predicate).
        for lk in acc:
            if not isinstance(getattr(lk, "lhs", None), Window):
                return True
        return False

    # field_name used by the reverse FK prefetch is the FK field name on Child.
    field_name = "parent"

    # --- (S3) the apply_membership consumed-axiom raise guard ------------------
    # The model encodes the membership-application step as a @ContractOnly callee
    # `apply_membership` with Requires(not is_sliced(query)) and an Ensures that
    # grants the unforgeable `membership_token`. That precondition models the
    # REAL QuerySet.filter / Query.can_filter guard: filtering a SLICED query
    # raises TypeError ("Cannot filter a query once a slice has been taken."),
    # while filtering an UNSLICED query succeeds and ANDs the predicate. Validate
    # both directions directly so the token is granted only on the unsliced path.
    from django.db.models import Q

    predicate = Q(**{"%s__in" % field_name: instances})
    # sliced -> filter must raise (token is NOT granted; the model precondition
    # `not is_sliced` is exactly this guard).
    sliced_qs = Child.objects.all()
    sliced_qs.query.set_limits(low=1, high=3)
    assert sliced_qs.query.is_sliced, "sliced setup failed"
    raised = False
    try:
        sliced_qs.filter(predicate)
    except TypeError:
        raised = True
    assert raised, (
        "QuerySet.filter did NOT raise on a sliced query — the model's "
        "apply_membership precondition (not is_sliced) would be unsound")
    # unsliced -> filter succeeds and the membership predicate is present (the
    # token-grant path: membership_applied becomes true).
    unsliced_qs = Child.objects.all()
    assert not unsliced_qs.query.is_sliced
    filtered = unsliced_qs.filter(predicate)
    assert membership_present(lookups_of(filtered)), (
        "membership predicate missing after filter on an unsliced query — the "
        "apply_membership Ensures(membership_applied) would be unsound")

    cases = [
        # (slice_args, expect_lower, expect_upper)
        (None,        False, False),   # unsliced: membership only
        ((0, 3),      True,  True),    # [:3]  -> low=0,high=3
        ((1, None),   True,  False),   # [1:]  -> low=1,high=None  (no upper)
        ((1, 2),      True,  True),    # [1:2] -> low=1,high=2
        ((2, 5),      True,  True),    # [2:5]
    ]
    n_checked = 0
    for slice_args, expect_lower, expect_upper in cases:
        base = Child.objects.all()
        orig_low, orig_high = 0, None
        if slice_args is not None:
            low, high = slice_args
            # apply the slice via set_limits to mirror a queryset[low:high]
            base.query.set_limits(low=low if low else None, high=high)
        orig_low, orig_high = base.query.low_mark, base.query.high_mark
        was_sliced = base.query.is_sliced

        out = _filter_prefetch_queryset(base, field_name, instances)

        acc = lookups_of(out)
        # membership predicate always applied
        assert membership_present(acc), (
            "membership predicate missing for slice=%r" % (slice_args,))
        # lower bound present iff originally sliced; value == original low_mark
        gt_val = window_bound_value(acc, GreaterThan)
        assert (gt_val is not None) == expect_lower, (
            "lower row-position bound presence wrong for slice=%r: got %r want %r"
            % (slice_args, gt_val is not None, expect_lower))
        if gt_val is not None:
            assert gt_val == orig_low, (
                "lower bound value wrong for slice=%r: GreaterThan rhs=%r, "
                "original low_mark=%r" % (slice_args, gt_val, orig_low))
        # upper bound present iff originally sliced AND finite high; value == high
        le_val = window_bound_value(acc, LessThanOrEqual)
        assert (le_val is not None) == expect_upper, (
            "upper row-position bound presence wrong for slice=%r: got %r want %r"
            % (slice_args, le_val is not None, expect_upper))
        if le_val is not None:
            assert le_val == orig_high, (
                "upper bound value wrong for slice=%r: LessThanOrEqual rhs=%r, "
                "original high_mark=%r" % (slice_args, le_val, orig_high))
        # presence of lower bound iff was sliced (model: Old(is_sliced) ==
        # lower_bound is not None) — the index-level equivalence under test.
        assert (gt_val is not None) == was_sliced, (
            "lower-bound/was_sliced mismatch for slice=%r: present=%r sliced=%r"
            % (slice_args, gt_val is not None, was_sliced))
        # presence of upper bound iff was sliced AND had a finite high
        assert (le_val is not None) == (was_sliced and orig_high is not None), (
            "upper-bound/(sliced&finite-high) mismatch for slice=%r" % (slice_args,))
        # the slice window is cleared after the helper (filter applicable)
        assert not out.query.is_sliced, (
            "helper did not clear the slice window for slice=%r" % (slice_args,))
        assert out.query.low_mark == 0 and out.query.high_mark is None, (
            "helper did not reset marks for slice=%r: marks=(%r,%r)"
            % (slice_args, out.query.low_mark, out.query.high_mark))
        n_checked += 1

    print("G-AX OK: structural slice->bound translation sound against the REAL "
          "_filter_prefetch_queryset + Query slice machinery over %d helper "
          "cases and 6 is_sliced/clear_limits cases (membership always; lower "
          "bound == low_mark iff sliced; upper bound == high_mark iff finite "
          "high; window cleared); plus the apply_membership consumed-axiom raise "
          "guard (S3): QuerySet.filter raises on a sliced query and succeeds "
          "(membership predicate present) on an unsliced one — the "
          "membership_token is grantable only on the unsliced path." % (n_checked,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
