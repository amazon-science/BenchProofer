#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14631.

The bundle ships NO consumed axioms (the `axioms` region of Solution.lean is
empty). The single kind-A obligation is an **A-reference**: the deep model
`initialFor` (Solution.lean `pure` region) must equal the unchanged real callee
`BoundField.initial` (django/forms/boundfield.py), and the per-field cleaner
`field.clean` must be the identity on the resolved value (refinement.md tag I).

`initialFor` models the microsecond-normalization of `BoundField.initial`:

    initialFor f = { f.stored with sub := 0 }   if f.coarse  (widget can't carry
                                                              sub-second precision)
                 = f.stored                      otherwise

where `f.stored` is the slot's resolved initial (`get_initial_for_field`,
evaluated once) and `f.coarse = not widget.supports_microseconds`.

This check builds REAL Django forms with a disabled DateTimeField over a coarse
widget (default DateTimeInput, supports_microseconds=False) and a
microsecond-supporting widget (TextInput, supports_microseconds=True), fuzzes the
second/microsecond components, and asserts:

  (A-reference) BoundField.initial == initialFor(stored, coarse)
  (I)           field.clean(resolved_dt) == resolved_dt   (DateTimeField identity)

Imports only Django (the repo under test) + stdlib. Exit 0 iff every obligation
holds.
"""
import datetime
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django import forms
from django.forms.widgets import TextInput


def initial_for(stored, coarse):
    """Deep model `initialFor` (Solution.lean pure region), in Python over the
    Stamp bijection (sec=second, sub=microsecond; mapping.md §2)."""
    if coarse:
        return stored.replace(microsecond=0)
    return stored


def make_form(stored_dt, microsec_widget):
    """A bound (empty-data) form with one disabled DateTimeField whose callable
    initial yields `stored_dt`. `microsec_widget=True` uses a widget that
    supports microseconds (TextInput), else the default coarse DateTimeInput."""
    widget = TextInput if microsec_widget else None

    class DateTimeForm(forms.Form):
        dt = forms.DateTimeField(
            initial=lambda: stored_dt, disabled=True,
            **({"widget": widget} if widget else {}),
        )

    return DateTimeForm({})


def check_initial_reference(stored_dt, microsec_widget):
    """(A-reference) BoundField.initial == initialFor(stored, coarse)."""
    form = make_form(stored_dt, microsec_widget)
    bf = form["dt"]
    coarse = not bf.field.widget.supports_microseconds
    observed = bf.initial                       # real callee
    expected = initial_for(stored_dt, coarse)   # deep model
    assert observed == expected, (
        "initialFor deep model unsound on stored=%r microsec_widget=%r: "
        "BoundField.initial gave %r, deep model gives %r (coarse=%r)"
        % (stored_dt, microsec_widget, observed, expected, coarse))
    return coarse


def check_clean_identity(stored_dt, microsec_widget):
    """(I) `field.clean` is the identity on the resolved (disabled-field) value
    — refinement.md A5. The resolved value of a disabled field is `bf.initial`
    (the normalized stored value); the cleaning step must return it unchanged.

    This validates the UNCHANGED callee `field.clean` (DateTimeField.clean)
    directly on the resolved datetime — NOT through `BaseForm._clean_fields`,
    which is the function under change (directive 7: G-AX must exercise the real
    callee, never the function under spec). Routing through `_clean_fields` on
    the base commit would re-observe the very bug the patch fixes (disabled
    fields resolving to the raw, un-normalized stored value)."""
    form = make_form(stored_dt, microsec_widget)
    bf = form["dt"]
    field = bf.field
    resolved = bf.initial                  # the resolved value the loop cleans
    cleaned = field.clean(resolved)        # real unchanged callee, called directly
    assert cleaned == resolved, (
        "field.clean not identity on resolved value: cleaned=%r resolved=%r"
        % (cleaned, resolved))


def main():
    # --- boundary: the F2P fixed timestamp, both widget kinds -----------------
    boundary = [
        datetime.datetime(2006, 10, 25, 14, 30, 45, 123456),
        datetime.datetime(2006, 10, 25, 14, 30, 46, 0),
        datetime.datetime(2006, 10, 25, 14, 30, 45, 1),
        datetime.datetime(2006, 10, 25, 14, 30, 45, 999999),
        datetime.datetime(1, 1, 1, 0, 0, 0, 0),
        datetime.datetime(9999, 12, 31, 23, 59, 59, 999999),
    ]
    coarse_seen = micro_seen = 0
    for dt in boundary:
        for microsec_widget in (False, True):
            coarse = check_initial_reference(dt, microsec_widget)
            check_clean_identity(dt, microsec_widget)
            coarse_seen += int(coarse)
            micro_seen += int(not coarse)

    # --- randomized fuzz over second/microsecond components -------------------
    rng = random.Random(14631)
    n_fuzz = 4000
    for _ in range(n_fuzz):
        sec = rng.randint(0, 59)
        sub = rng.randint(0, 999999)
        dt = datetime.datetime(2006, 10, 25, 14, 30, sec, sub)
        for microsec_widget in (False, True):
            check_initial_reference(dt, microsec_widget)
            check_clean_identity(dt, microsec_widget)

    print("G-AX OK: initialFor deep model (== BoundField.initial) sound and "
          "field.clean identity on resolved datetime over %d boundary "
          "(coarse=%d, micro=%d) + %d fuzz timestamps x2 widgets"
          % (len(boundary), coarse_seen, micro_seen, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
