#!/usr/bin/env python3
"""G-CONF for django__django-14034.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_requiredAttrs` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`BoundField.build_widget_attrs` (django/forms/boundfield.py) over >=1e5 fuzzed
inputs. Zero disagreements => exit 0.

The modeled decision is *where the HTML required marker is placed*. The unchanged
per-widget predicate `Widget.use_required_attribute(initial)` is an INPUT to the
model (mapping.md): we drive the real method with duck-typed widgets whose
`use_required_attribute` returns the fuzzed boolean, so the real callee's result
is fed in exactly as the Lean model consumes it (I/O bridging).

Observable outputs compared (the real method's effects):
  * parentRequired      = bool(returned attrs.get('required'))   (set in else branch)
  * parentDisabled      = bool(returned attrs.get('disabled'))   (field disabled)
  * subwidgetRequired   = the `required` flags written onto the subwidgets, in
                          order (only the per-subwidget branch writes them)
The Lean Result also carries `perSubBranch`, an internal bookkeeping flag with no
Django counterpart (it is pinned in the spec but not separately observable), so it
is excluded from the differential.

stdlib-only; no hypothesis required.
"""
import os
import random
import sys

# --- configure Django before importing the forms machinery -------------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False, DATABASES={},
        INSTALLED_APPS=[], USE_I18N=False,
    )
    django.setup()

from django.forms.boundfield import BoundField
from django.forms.widgets import MultiWidget

SEED = 14034
N = 120_000

INITIAL = object()   # opaque sentinel; only passed through to use_required_attribute


# --- duck-typed objects exposing exactly what build_widget_attrs reads --------
class SubWidget:
    def __init__(self, use_req):
        self._use = use_req
        self.attrs = {}

    def use_required_attribute(self, initial):
        return self._use


class MultiParent(MultiWidget):
    """A real MultiWidget subclass (so the isinstance check is True) whose
    predicate result is controlled. __init__ is bypassed deliberately; we only
    set the attributes the method reads."""
    def __init__(self, use_req, subwidgets):
        self._use = use_req
        self.widgets = subwidgets

    def use_required_attribute(self, initial):
        return self._use


class PlainParent:
    """A non-MultiWidget widget (isinstance(..., MultiWidget) is False)."""
    def __init__(self, use_req):
        self._use = use_req
        self.attrs = {}

    def use_required_attribute(self, initial):
        return self._use


class SubField:
    def __init__(self, required):
        self.required = required


class Field:
    def __init__(self, required, disabled, widget,
                 has_raf=False, raf=False, fields=None):
        self.required = required
        self.disabled = disabled
        self.widget = widget
        if has_raf:
            self.require_all_fields = raf
        if fields is not None:
            self.fields = fields


class Form:
    def __init__(self, use_req):
        self.use_required_attribute = use_req


class FakeBoundField:
    def __init__(self, field, form, initial):
        self.field = field
        self.form = form
        self.initial = initial


def oracle(fi):
    """Drive the REAL patched BoundField.build_widget_attrs and read its effects.

    The Lean model carries one `subPairs` entry per (subfield, subwidget) pair
    (`(subUseReq, subRequired)`); here that single aligned walk is materialized as
    the two real sequences the method zips: `widget.widgets` (subwidgets, carrying
    the `use_required_attribute` predicate result) and `self.field.fields`
    (subfields, carrying `.required`), in the SAME order."""
    su = [u for (u, _r) in fi["subPairs"]]
    sr = [r for (_u, r) in fi["subPairs"]]
    if fi["isMultiWidget"]:
        subwidgets = [SubWidget(u) for u in su]
        widget = MultiParent(fi["widgetUseReq"], subwidgets)
        field = Field(fi["required"], fi["disabled"], widget,
                      has_raf=fi["hasRAF"], raf=fi["raf"],
                      fields=[SubField(r) for r in sr])
    else:
        widget = PlainParent(fi["widgetUseReq"])
        # a non-multiwidget field may still expose require_all_fields
        field = Field(fi["required"], fi["disabled"], widget,
                      has_raf=fi["hasRAF"], raf=fi["raf"],
                      fields=[SubField(r) for r in sr] if fi["hasRAF"] else None)
    bf = FakeBoundField(field, Form(fi["formUseReq"]), INITIAL)
    attrs = BoundField.build_widget_attrs(bf, {}, None)
    parent_required = bool(attrs.get("required", False))
    parent_disabled = bool(attrs.get("disabled", False))
    sub_required = [sw.attrs["required"] for sw in widget.widgets
                    if "required" in sw.attrs] if fi["isMultiWidget"] else []
    return parent_required, parent_disabled, sub_required


def shadow(fi):
    """R/I transliteration of implementation_requiredAttrs (Lean)."""
    parent_required = False
    parent_disabled = False
    sub_required = []
    if fi["widgetUseReq"] and fi["required"] and fi["formUseReq"]:
        if fi["hasRAF"] and (not fi["raf"]) and fi["isMultiWidget"]:
            for su, sr in fi["subPairs"]:
                sub_required.append(bool(su and sr))
        else:
            parent_required = True
    if fi["disabled"]:
        parent_disabled = True
    return parent_required, parent_disabled, sub_required


def rand_fi(rng):
    n = rng.randint(0, 5)
    return {
        "widgetUseReq": rng.random() < 0.6,
        "formUseReq": rng.random() < 0.7,
        "required": rng.random() < 0.7,
        "disabled": rng.random() < 0.3,
        "hasRAF": rng.random() < 0.6,
        "raf": rng.random() < 0.5,
        "isMultiWidget": rng.random() < 0.6,
        "subPairs": [(rng.random() < 0.7, rng.random() < 0.5) for _ in range(n)],
    }


def main():
    rng = random.Random(SEED)

    # Deterministic boundary cases (incl. the exact reported scenario:
    # required field, require_all_fields=False, MultiWidget, mixed subfields).
    fixed = [
        # the reporter's case: parent required, RAF=False, multiwidget, one
        # optional + one required subfield -> per-subwidget placement.
        # subPairs entries are (subUseReq, subRequired).
        {"widgetUseReq": True, "formUseReq": True, "required": True,
         "disabled": False, "hasRAF": True, "raf": False, "isMultiWidget": True,
         "subPairs": [(True, False), (True, True)]},
        # RAF=True -> ordinary parent placement
        {"widgetUseReq": True, "formUseReq": True, "required": True,
         "disabled": False, "hasRAF": True, "raf": True, "isMultiWidget": True,
         "subPairs": [(True, False), (True, True)]},
        # no require_all_fields attr -> ordinary parent placement
        {"widgetUseReq": True, "formUseReq": True, "required": True,
         "disabled": False, "hasRAF": False, "raf": False, "isMultiWidget": True,
         "subPairs": [(True, True)]},
        # not a multiwidget -> ordinary parent placement
        {"widgetUseReq": True, "formUseReq": True, "required": True,
         "disabled": False, "hasRAF": True, "raf": False, "isMultiWidget": False,
         "subPairs": []},
        # guard fails (field not required) -> no marker at all
        {"widgetUseReq": True, "formUseReq": True, "required": False,
         "disabled": True, "hasRAF": True, "raf": False, "isMultiWidget": True,
         "subPairs": [(True, True)]},
        # per-subwidget branch with empty subfields
        {"widgetUseReq": True, "formUseReq": True, "required": True,
         "disabled": False, "hasRAF": True, "raf": False, "isMultiWidget": True,
         "subPairs": []},
        # subwidget predicate False suppresses an otherwise-required subfield
        {"widgetUseReq": True, "formUseReq": True, "required": True,
         "disabled": False, "hasRAF": True, "raf": False, "isMultiWidget": True,
         "subPairs": [(False, True), (True, True)]},
    ]

    cases = fixed + [rand_fi(rng) for _ in range(N)]

    disagreements = 0
    first = None
    for fi in cases:
        o = oracle(fi)
        s = shadow(fi)
        if o != s:
            disagreements += 1
            if first is None:
                first = (fi, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, len(cases), first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements (seed=%d)" % (len(cases), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
