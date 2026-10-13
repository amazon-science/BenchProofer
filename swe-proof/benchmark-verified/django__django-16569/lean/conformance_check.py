#!/usr/bin/env python3
"""G-CONF for django__django-16569.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_addFields` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `BaseFormSet.add_fields`,
over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md): `add_fields`'s deletion branch decides whether to attach
the deletion field. Outcome modeled as Option Bool:
  * none  <-> add_fields raised (the None < int TypeError);
  * some b <-> it completed, b = (DELETION_FIELD_NAME in form.fields).

  * Oracle = the REAL patched BaseFormSet.add_fields, driven on a live formset:
            call add_fields(form, index); catch to detect a raise; otherwise read
            whether DELETION_FIELD_NAME landed in form.fields.
  * Shadow = some(canDelete and (canDeleteExtra or withinInitial(index, ifc))),
            withinInitial(none,_)=False, withinInitial(some i, ifc)=(i < ifc).

Type bijection (mapping.md): canDelete<->self.can_delete (bool),
canDeleteExtra<->self.can_delete_extra (bool), index<->index arg (int|None,
None<->none), ifc<->initial_form_count (int>=0), result<->Option Bool outcome.
stdlib-only; no hypothesis required.
"""
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
        TEMPLATES=[],
    )
    django.setup()

from django import forms
from django.forms.formsets import DELETION_FIELD_NAME


class MyForm(forms.Form):
    my_field = forms.CharField(required=False)


def make_formset(can_delete, can_delete_extra, ifc):
    """A live, unbound formset whose initial_form_count() == ifc."""
    FS = forms.formset_factory(
        MyForm,
        can_delete=can_delete,
        can_delete_extra=can_delete_extra,
        extra=1,
    )
    initial = [{"my_field": "x"} for _ in range(ifc)] if ifc else None
    fs = FS(initial=initial)
    assert fs.initial_form_count() == ifc, (fs.initial_form_count(), ifc)
    return fs


def oracle(can_delete, can_delete_extra, index, ifc):
    """Outcome of the patched repo function: 'raise' or bool(field present)."""
    fs = make_formset(can_delete, can_delete_extra, ifc)
    form = MyForm()
    try:
        fs.add_fields(form, index)
    except TypeError:
        return None  # the bug's TypeError -> Option none
    return DELETION_FIELD_NAME in form.fields


def within_initial(index, ifc):
    if index is None:
        return False
    return index < ifc


def shadow(can_delete, can_delete_extra, index, ifc):
    """R/I transliteration of implementation_addFields (Lean). Always 'some'."""
    add_control = False
    if can_delete:
        if can_delete_extra:
            add_control = True
        else:
            if index is not None and index < ifc:
                add_control = True
    return add_control


def main():
    rng = random.Random(16569)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        can_delete = rng.choice([True, False])
        can_delete_extra = rng.choice([True, False])
        ifc = rng.randint(0, 12)
        # index: None (positionless) plus the int range around ifc.
        if rng.random() < 0.35:
            index = None
        else:
            index = rng.randint(0, 12)
        o = oracle(can_delete, can_delete_extra, index, ifc)   # None | bool
        s = shadow(can_delete, can_delete_extra, index, ifc)   # bool (always some)
        # Oracle None (raise) must never match the shadow's total 'some' outcome.
        ok = (o is not None) and (o == s)
        if not ok:
            disagreements += 1
            if first is None:
                first = (can_delete, can_delete_extra, index, ifc, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
