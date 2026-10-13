#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11433.

This bundle declares **no axioms** and **no deep-model references**: the single
operation the gold patch changes (the per-field skip guard) is modeled
*identically* (`applies`), and the surrounding per-field loop is a structural
type refinement (`applyPlan` over the flattened field list). Every refinement
leg is therefore R or I and is handled mechanically by G-CONF
(conformance_check.py); there is no opaque callee whose contract the proof
assumes.

G-AX consequently has no axiom `ensures` to validate. To keep the gate
meaningful (rather than a silent pass), this script:

  1. asserts the bundle truly declares no axioms (meta.json `axioms == []` and
     `deep_model_references == []`), so a future edit that smuggles in an axiom
     without a soundness check is caught here; and
  2. exercises the three real Django/Python operations the refinement leans on
     against live objects, confirming their fixed semantics match the
     mapping.md §2 bijection that G-CONF relies on:
       * `Field.has_default()`  (model field WITH and WITHOUT a default),
       * `Widget.value_omitted_from_data(data, files, name)` (name present /
         absent in the submitted data),
       * `cleaned_value in form_field.empty_values` (the membership the added
         conjunct performs, over the EMPTY_VALUES set and non-empty values).

Imports Django (present in the SWE-Bench instance image) + stdlib only. Exit 0
iff the no-axiom claim holds and the builtin/callee semantics are as documented.
"""
import json
import os
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        USE_L10N=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django import forms
from django.db import models
from django.forms.widgets import TextInput


def check_no_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    refs = meta.get("deep_model_references", [])
    assert axioms == [], (
        "axiom_check expected no axioms but meta.json lists %r; an axiom "
        "requires an executable soundness check here." % (axioms,))
    assert refs == [], (
        "axiom_check expected no deep-model references but meta.json lists "
        "%r; an A-reference requires a == real-callee check here." % (refs,))


def check_has_default():
    """`Field.has_default()` ↔ Field.modelHasDefault (mapping.md §2)."""
    f_default = models.CharField(max_length=10, default="di")
    f_plain = models.CharField(max_length=10)
    assert f_default.has_default() is True, "field with default must report True"
    assert f_plain.has_default() is False, "field w/o default must report False"
    # a falsy-but-provided default still counts as having a default
    f_empty_default = models.CharField(max_length=10, default="")
    assert f_empty_default.has_default() is True


def check_value_omitted():
    """`Widget.value_omitted_from_data(data, files, name)` ↔ Field.noIncomingValue
    (mapping.md §2): True iff the field name is absent from the submitted data."""
    w = TextInput()
    assert w.value_omitted_from_data({}, {}, "mode") is True
    assert w.value_omitted_from_data({"mode": "x"}, {}, "mode") is False
    # an explicitly-empty submitted value is still "present" (not omitted)
    assert w.value_omitted_from_data({"mode": ""}, {}, "mode") is False


def check_empty_values_membership():
    """`cleaned_value in form_field.empty_values` ↔ Field.cleanedValueEmpty
    (mapping.md §2). empty_values == list(validators.EMPTY_VALUES)."""
    ff = forms.CharField(required=False)
    # the EMPTY_VALUES set: None, '', [], (), {}
    for empty in (None, "", [], (), {}):
        assert empty in ff.empty_values, (
            "%r must be an empty value" % (empty,))
    # non-empty values are NOT in empty_values
    for nonempty in ("de", "0", " ", 0, ["x"], {"k": 1}):
        assert nonempty not in ff.empty_values, (
            "%r must NOT be an empty value" % (nonempty,))


def main():
    check_no_axioms()
    check_has_default()
    check_value_omitted()
    check_empty_values_membership()
    print("G-AX OK: bundle declares no axioms / no A-references; the three "
          "refinement operations (Field.has_default, "
          "Widget.value_omitted_from_data, cleaned_value in empty_values) match "
          "the mapping.md bijection on live Django objects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
