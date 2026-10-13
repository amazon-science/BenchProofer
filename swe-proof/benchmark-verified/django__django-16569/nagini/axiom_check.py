#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16569.

There are NO consumed @ContractOnly axioms in model.py (the changed operation is
pure scalar control flow, modeled deeply). This script performs the A-reference
behavioural check: it drives the REAL `django.forms.formsets.BaseFormSet`
(post-gold, in-container) and asserts that the model's abstract decision is
exactly what the real `add_fields` computes.

For a freshly built form, `add_fields(form, index)`:

  * makes `ORDERING_FIELD_NAME` present in `form.fields` iff `can_order`;
  * makes `DELETION_FIELD_NAME` present in `form.fields` iff
        can_delete and (can_delete_extra
                        or (index is not None and index < initial_form_count)).

That second formula is exactly model.py's postcondition
`form.has_delete_field == (can_delete and (can_delete_extra
        or at_initial_position(index, initial_form_count)))`
with `at_initial_position(None, n) == False`.

The check sweeps the full cross product
    can_order x can_delete x can_delete_extra in {True, False}^3
and `index in {None, 0, 1, ..., initial+ }` for several initial-form counts,
building real formsets via `formset_factory` and calling the real `add_fields`
on a freshly constructed bound/unbound form.

It also confirms the PRE-PATCH behaviour: the un-guarded comparison
`index < initial_form_count` raises `TypeError` precisely on the configuration
(`can_delete`, `not can_delete_extra`, `index is None`) — the differential the
model_prepatch fails on.

Django + stdlib only (the same library the gold patch lives in). Exit 0 iff
every observation matches the model.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=False,
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={},
            ROOT_URLCONF=__name__,
        )
    django.setup()


def at_initial_position(index, initial):
    return (index is not None) and (index < initial)


def model_decision_delete(can_delete, can_delete_extra, index, initial):
    """model.py's deletion-field decision (post-gold)."""
    return can_delete and (can_delete_extra
                           or at_initial_position(index, initial))


def model_order_prefilled(can_order, index, initial):
    """model.py's order_field_prefilled decision: the ordering field's initial
    value is pre-filled only for an initial-position form."""
    return can_order and at_initial_position(index, initial)


def prepatch_raises(can_delete, can_delete_extra, index, initial):
    """Re-enacts the pre-patch un-guarded comparison; returns True iff it would
    raise TypeError. Mirrors model_prepatch.py's failing branch."""
    if not can_delete:
        return False
    if can_delete_extra:
        return False  # short-circuits before the comparison
    try:
        _ = index < initial
        return False
    except TypeError:
        return True


def main():
    _configure_django()
    from django import forms
    from django.forms.formsets import (
        formset_factory,
        DELETION_FIELD_NAME,
        ORDERING_FIELD_NAME,
    )

    class MyForm(forms.Form):
        my_field = forms.CharField(required=False)

    checked = 0
    mismatches = []

    bools = [True, False]
    # initial-form counts to vary the boundary of `index < initial_form_count`
    for n_initial in (0, 1, 2, 3):
        # build `initial` data of length n_initial so initial_form_count == n
        initial_data = [{"my_field": "x"} for _ in range(n_initial)]
        for can_order in bools:
            for can_delete in bools:
                for can_delete_extra in bools:
                    FS = formset_factory(
                        form=MyForm,
                        extra=2,
                        can_order=can_order,
                        can_delete=can_delete,
                        can_delete_extra=can_delete_extra,
                    )
                    fs = FS(initial=initial_data or None)
                    initial = fs.initial_form_count()

                    # indices to probe: None (empty_form), and a span across the
                    # initial/extra boundary
                    indices = [None] + list(range(0, initial + 3))
                    for index in indices:
                        # Build a fresh form exactly as add_fields' callers do,
                        # then call the REAL add_fields on it.
                        form = MyForm()
                        # The only mutable state add_fields touches is .fields.
                        # Pre-patch raises for (can_delete, not extra, None);
                        # post-gold must never raise.
                        try:
                            fs.add_fields(form, index)
                        except TypeError as e:
                            mismatches.append(
                                "REAL add_fields raised TypeError (post-gold "
                                "must not) for can_order=%s can_delete=%s "
                                "can_delete_extra=%s index=%r initial=%d: %s"
                                % (can_order, can_delete, can_delete_extra,
                                   index, initial, e))
                            continue

                        have_delete = DELETION_FIELD_NAME in form.fields
                        want_delete = model_decision_delete(
                            can_delete, can_delete_extra, index, initial)
                        if have_delete != want_delete:
                            mismatches.append(
                                "DELETE presence mismatch: real=%s model=%s "
                                "(can_delete=%s extra=%s index=%r initial=%d)"
                                % (have_delete, want_delete, can_delete,
                                   can_delete_extra, index, initial))

                        have_order = ORDERING_FIELD_NAME in form.fields
                        want_order = bool(can_order)
                        if have_order != want_order:
                            mismatches.append(
                                "ORDER presence mismatch: real=%s model=%s "
                                "(can_order=%s index=%r initial=%d)"
                                % (have_order, want_order, can_order, index,
                                   initial))

                        # order_field_prefilled: the real ordering field carries
                        # a non-None `initial` (== index+1) iff it is built in the
                        # guarded arm (an initial-position form).
                        have_prefill = (
                            have_order
                            and form.fields[ORDERING_FIELD_NAME].initial is not None)
                        want_prefill = model_order_prefilled(
                            can_order, index, initial)
                        if have_prefill != want_prefill:
                            mismatches.append(
                                "ORDER prefill mismatch: real=%s model=%s "
                                "(can_order=%s index=%r initial=%d)"
                                % (have_prefill, want_prefill, can_order, index,
                                   initial))

                        # differential: confirm the pre-patch un-guarded
                        # comparison raises exactly on the bug configuration
                        would_raise = prepatch_raises(
                            can_delete, can_delete_extra, index, initial)
                        expect_raise = (can_delete and not can_delete_extra
                                        and index is None)
                        if would_raise != expect_raise:
                            mismatches.append(
                                "pre-patch fault model mismatch: would_raise=%s "
                                "expect=%s (can_delete=%s extra=%s index=%r)"
                                % (would_raise, expect_raise, can_delete,
                                   can_delete_extra, index))
                        checked += 1

    # Direct re-creation of the issue's reproducer: empty_form on a
    # can_delete=True, can_delete_extra=False formset must NOT carry DELETE.
    FS = formset_factory(form=MyForm, can_delete=True, can_delete_extra=False)
    fs = FS(initial=None)
    ef = fs.empty_form  # pre-patch: raises TypeError here
    assert DELETION_FIELD_NAME not in ef.fields, (
        "empty_form of a can_delete/no-extra formset must not carry DELETE")

    if mismatches:
        print("G-AX FAIL (%d mismatches):" % len(mismatches))
        for m in mismatches[:40]:
            print("  -", m)
        return 1

    print("G-AX OK: real BaseFormSet.add_fields == model decision over %d "
          "(flags x index x initial) configurations incl. index=None; "
          "empty_form reproducer carries no DELETE field; pre-patch fault "
          "model matches (raises iff can_delete & not extra & index is None)."
          % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
