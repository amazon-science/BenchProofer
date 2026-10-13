#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16569 (nagini).

SHADOW: the impl region of model.py's ``configure_optional_fields``, copied
VERBATIM below (the impl region contains no contract calls, so stripping is a
no-op), together with the @Pure helper ``at_initial_position`` copied as a
plain function (used as an internal cross-check of the shadow against the
model's stated post-state). The ``Form`` carrier is the model's minimal
mutable object: three booleans recording whether each auxiliary key became
present and whether the ordering field carries a pre-filled initial value.
There are no @ContractOnly callees (mapping.md section 3: no consumed axioms).

ORACLE: the REAL patched repo function per mapping.md section 1 —
``django.forms.formsets.BaseFormSet.add_fields``. The gate applies patch.diff
to /testbed and sets PYTHONPATH=/testbed before this script runs, so the
import resolves to the patched module. Each probe builds a real formset via
``formset_factory`` with the given flag triple; the initial-form count is
driven honestly through real initial data (for an unbound formset,
``initial_form_count()`` is the length of the initial list — the value the
model takes as its read-only scalar parameter, captured once by the real
hook). A fresh form is constructed per probe and the real ``add_fields`` is
called on it.

TYPE BRIDGE (mapping.md section 2): the three flags and the Optional[int]
position pass through identically; ``initial_form_count`` lowers to
``len(initial)`` of the real formset; the form's post-state raises to the
model's booleans as
  has_order_field       <-> ORDERING_FIELD_NAME in form.fields
  order_field_prefilled <-> that field's ``initial`` attribute is non-None
  has_delete_field      <-> DELETION_FIELD_NAME in form.fields

INPUT PLAN (>= 1e5 Requires-satisfying inputs): the precondition demands a
fresh form (both sides construct one per probe) and a non-negative
initial-form count. Boundary block: the full flag cross product {T,F}^3
crossed with initial-form counts {0,1,2,3,5} and, per count n, positions
{None, -3, -1, 0, ..., n+2, 10**6} — every side of the position/count
comparison boundary plus the positionless case. Fuzz block: 100000 random
tuples (flags uniform; position None-weighted or an int in [-5, 45];
count in [0, 40]), pinned seed 16569. Exit 0 iff zero disagreements; on
disagreement prints the input tuple and both observation triples and exits 1.
stdlib + Django (the library under test) only.
"""
import json
import random
import sys

SEED = 16569
N_FUZZ = 100000


# --- shadow carrier: the model's minimal Form (constructor post-state) --------

class Form(object):
    __slots__ = ("has_order_field", "order_field_prefilled",
                 "has_delete_field")

    def __init__(self):
        self.has_order_field = False
        self.order_field_prefilled = False
        self.has_delete_field = False


# --- pure region of model.py, copied as a plain function ----------------------

def at_initial_position(index, initial_form_count):
    return index is not None and index < initial_form_count


# --- impl region of model.py, verbatim ----------------------------------------

def configure_optional_fields(
    form,
    can_order,
    can_delete,
    can_delete_extra,
    index,
    initial_form_count,
):
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
        else:
            form.has_order_field = True
    if can_delete and (
        can_delete_extra or (index is not None and index < initial_form_count)
    ):
        form.has_delete_field = True


def shadow_triple(can_order, can_delete, can_delete_extra, index, n_initial):
    """Run the shadow on a fresh Form; return its observation triple."""
    form = Form()
    configure_optional_fields(form, can_order, can_delete, can_delete_extra,
                              index, n_initial)
    return (form.has_order_field, form.order_field_prefilled,
            form.has_delete_field)


def spec_triple(can_order, can_delete, can_delete_extra, index, n_initial):
    """The model's stated post-state (internal cross-check of the shadow)."""
    return (
        bool(can_order),
        can_order and at_initial_position(index, n_initial),
        can_delete and (can_delete_extra
                        or at_initial_position(index, n_initial)),
    )


# --- oracle: the real patched repo hook ----------------------------------------

def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, USE_TZ=False, DATABASES={})
    django.setup()


class _Oracle(object):
    """Real formsets, cached per (flags, initial-form count)."""

    def __init__(self):
        from django import forms
        from django.forms.formsets import (
            formset_factory,
            DELETION_FIELD_NAME,
            ORDERING_FIELD_NAME,
        )

        class ProbeForm(forms.Form):
            probe = forms.CharField(required=False)

        self._ProbeForm = ProbeForm
        self._factory = formset_factory
        self._DEL = DELETION_FIELD_NAME
        self._ORD = ORDERING_FIELD_NAME
        self._cache = {}

    def _formset(self, can_order, can_delete, can_delete_extra, n_initial):
        key = (can_order, can_delete, can_delete_extra, n_initial)
        fs = self._cache.get(key)
        if fs is None:
            FS = self._factory(
                form=self._ProbeForm,
                extra=2,
                can_order=can_order,
                can_delete=can_delete,
                can_delete_extra=can_delete_extra,
            )
            initial = [{"probe": "x"} for _ in range(n_initial)]
            fs = FS(initial=initial or None)
            assert fs.initial_form_count() == n_initial
            self._cache[key] = fs
        return fs

    def triple(self, can_order, can_delete, can_delete_extra, index,
               n_initial):
        """Call the real add_fields on a fresh form; return the observation
        triple, or an exception-tag string if the real hook raised."""
        fs = self._formset(can_order, can_delete, can_delete_extra, n_initial)
        form = self._ProbeForm()
        try:
            fs.add_fields(form, index)
        except Exception as e:  # the shadow never raises; any raise disagrees
            return "raised %s: %s" % (type(e).__name__, e)
        has_order = self._ORD in form.fields
        prefilled = has_order and form.fields[self._ORD].initial is not None
        has_delete = self._DEL in form.fields
        return (has_order, prefilled, has_delete)


# --- differential driver --------------------------------------------------------

def run_differential():
    _setup_django()
    oracle = _Oracle()
    checked = 0

    def check(can_order, can_delete, can_delete_extra, index, n_initial):
        nonlocal checked
        checked += 1
        shadow = shadow_triple(can_order, can_delete, can_delete_extra,
                               index, n_initial)
        assert shadow == spec_triple(can_order, can_delete, can_delete_extra,
                                     index, n_initial), (
            "internal shadow/spec inconsistency at %r"
            % ((can_order, can_delete, can_delete_extra, index, n_initial),))
        real = oracle.triple(can_order, can_delete, can_delete_extra,
                             index, n_initial)
        if shadow != real:
            print("DISAGREEMENT on input (can_order=%r, can_delete=%r, "
                  "can_delete_extra=%r, index=%r, initial_form_count=%r):\n"
                  "  shadow (impl region) (order, prefilled, delete) = %r\n"
                  "  real (patched add_fields)                        = %r"
                  % (can_order, can_delete, can_delete_extra, index,
                     n_initial, shadow, real))
            return False
        return True

    bools = (False, True)

    # boundary block: flags x counts x positions spanning the comparison
    # boundary, plus the positionless case and far-out ints
    for n in (0, 1, 2, 3, 5):
        indices = [None, -3, -1] + list(range(0, n + 3)) + [10 ** 6]
        for co in bools:
            for cd in bools:
                for cde in bools:
                    for ix in indices:
                        if not check(co, cd, cde, ix, n):
                            return checked, 1

    # fuzz block: pinned seed
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        co = rng.random() < 0.5
        cd = rng.random() < 0.5
        cde = rng.random() < 0.5
        ix = None if rng.random() < 0.35 else rng.randint(-5, 45)
        n = rng.randint(0, 40)
        if not check(co, cd, cde, ix, n):
            return checked, 1

    return checked, 0


def main():
    checked, disagreements = run_differential()
    if disagreements:
        print("FAIL: %d disagreement(s) over %d inputs" % (disagreements,
                                                           checked))
        print(json.dumps({"checked": checked, "disagreements": disagreements,
                          "seed": SEED}))
        return 1
    print("PASS: shadow impl region == real patched add_fields on %d inputs "
          "(boundary cross product + %d fuzz, pinned seed %d); "
          "0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
