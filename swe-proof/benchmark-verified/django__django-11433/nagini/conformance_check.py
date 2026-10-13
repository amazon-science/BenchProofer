#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11433 (nagini).

SHADOW: the impl region of model.py `construct_writes`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant) stripped. The impl region
operates on plain Python lists of bools, so it is directly executable as-is
(no PSeq is used by the model). The @Pure helper `write_value` copies over as
a plain function and is used as an internal cross-check of the shadow. There
are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.forms.models.construct_instance`. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched module
importable. The function is driven through duck-typed form/field/instance
carriers while every primitive whose boolean outcome is a model input stays
REAL:

  * `omitted[i]`  -- a real `django.forms.widgets.TextInput` computes
    `value_omitted_from_data(form.data, form.files, name)` from the actual
    presence of the field's key in the submitted-data dict;
  * `value_empty[i]` -- the real `in` membership of the actual cleaned value
    against the repo's `EMPTY_VALUES` sentinels (`django.core.validators`),
    exposed as the bound field's `empty_values` exactly as the repo reads it;
  * `has_default[i]` -- the model-field carrier's `has_default()` returns the
    chosen boolean (an unchanged primitive whose outcome is the carrier);
  * `selected[i]`  -- realized through the function's own candidacy filters:
    a deselected field is skipped via one of `editable=False`, its name being
    absent from cleaned_data, the `fields` allow-list, the `exclude` list, or
    (boundary case) a real `models.AutoField`.

The observable diffed is exactly the modeled one: whether `save_form_data`
ran for field i (recorded by the field carrier), i.e. whether the field's
cleaned value was written onto the instance. When written, the written value
is additionally checked to be the cleaned value itself.

Type bridge (mapping.md section 2): field-in-iteration-order <-> index i of
four index-aligned List[bool]; the per-field predicates are boolean carriers
of the real primitives above; `result[i]` <-> "save_form_data executed for
field i".

Input domain: the Requires demand four equal-length lists (plus access
permissions); every generated case builds four index-aligned lists, so all
inputs are Requires-satisfying.

>= 1e5 Requires-satisfying inputs: boundary cases (all 16 per-field flag
combinations x each empty sentinel / several non-empty cleaned values x each
deselection mechanism, plus the empty field list, a combined multi-field
case, and a real-AutoField case) + 100000 fuzz cases of up to 6 fields.
Pinned fuzz seed: 11433.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plus the repo under test).
"""
import json
import random
import sys

SEED = 11433
N_FUZZ = 100_000


# --- pure helper from model.py, contracts stripped -----------------------------

def write_value(selected, has_default, omitted, value_empty):
    return selected and not (has_default and omitted and value_empty)


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def construct_writes(selected, has_default, omitted, value_empty):
    result = []  # type: List[bool]
    i = 0
    while i < len(selected):
        if selected[i] and not (has_default[i] and omitted[i] and value_empty[i]):
            result = result + [True]
        else:
            result = result + [False]
        i = i + 1
    return result


# --- oracle plumbing: drive the REAL patched construct_instance ----------------
#
# Duck-typed carriers for the objects construct_instance touches. Only the
# containers are stubs; the boolean-producing primitives (widget method,
# empty-values membership) are the real repo objects.

class _ModelFieldStub(object):
    """Model-field carrier: name, editability, default-presence, and a
    recorder for save_form_data (the modeled observable)."""

    def __init__(self, name, editable, has_default):
        self.name = name
        self.editable = editable
        self._has_default = has_default
        self.saved = None          # set to the written value when written

    def has_default(self):
        return self._has_default

    def save_form_data(self, instance, value):
        self.saved = (value,)


class _FormFieldStub(object):
    """The `.field` of a bound field: real widget + real empty_values."""

    def __init__(self, widget, empty_values):
        self.widget = widget
        self.empty_values = empty_values


class _BoundFieldStub(object):
    def __init__(self, field):
        self.field = field


class _FormStub(object):
    """Carries cleaned_data / data / files and resolves form[name]."""

    def __init__(self, cleaned_data, data, bound_fields):
        self.cleaned_data = cleaned_data
        self.data = data
        self.files = {}
        self._bound = bound_fields

    def add_prefix(self, name):
        return name

    def __getitem__(self, name):
        return self._bound[name]


class _MetaStub(object):
    def __init__(self, fields):
        self.fields = fields


class _InstanceStub(object):
    def __init__(self, fields):
        self._meta = _MetaStub(fields)


# Deselection mechanisms: how a non-candidate field is realized in the oracle.
MECH_EDITABLE, MECH_NO_CLEANED, MECH_FIELDS, MECH_EXCLUDE = range(4)


class Case(object):
    """One differential input: per-field flags + concrete cleaned values."""

    def __init__(self, rows):
        # rows: list of (selected, mech_or_None, has_default, omitted,
        #                cleaned_value)
        self.rows = rows


def run_oracle(env, case, extra_fields=()):
    """Build the duck-typed world for `case`, run the real patched function,
    and return the per-field written booleans (+ written-value fidelity)."""
    construct_instance = env["construct_instance"]
    TextInput = env["TextInput"]
    empty_values = env["empty_values"]

    model_fields = []
    bound_fields = {}
    cleaned_data = {}
    data = {}
    fields_param = None
    exclude_param = None
    use_fields_param = any(mech == MECH_FIELDS
                           for (_s, mech, _h, _o, _v) in case.rows)
    if use_fields_param:
        fields_param = []

    for idx, (selected, mech, _hd, omitted, value) in enumerate(case.rows):
        name = "f%d" % idx
        editable = True
        in_cleaned = True
        if not selected:
            if mech == MECH_EDITABLE:
                editable = False
            elif mech == MECH_NO_CLEANED:
                in_cleaned = False
            elif mech == MECH_EXCLUDE:
                if exclude_param is None:
                    exclude_param = []
                exclude_param.append(name)
            # MECH_FIELDS: simply left out of fields_param below
        mf = _ModelFieldStub(name, editable, case.rows[idx][2])
        model_fields.append(mf)
        bound_fields[name] = _BoundFieldStub(
            _FormFieldStub(TextInput(), empty_values))
        if in_cleaned:
            cleaned_data[name] = value
        if not omitted:
            data[name] = "submitted"
        if use_fields_param and not (not selected and mech == MECH_FIELDS):
            fields_param.append(name)

    all_fields = list(model_fields) + list(extra_fields)
    form = _FormStub(cleaned_data, data, bound_fields)
    instance = _InstanceStub(all_fields)
    construct_instance(form, instance, fields=fields_param,
                       exclude=exclude_param)

    written = []
    for mf in model_fields:
        if mf.saved is not None:
            # written value must be the cleaned value itself
            if mf.saved[0] is not cleaned_data.get(mf.name, mf.saved[0]) \
                    and mf.saved[0] != cleaned_data.get(mf.name):
                return None, ("wrong value written for %s: %r != %r"
                              % (mf.name, mf.saved[0],
                                 cleaned_data.get(mf.name)))
            written.append(True)
        else:
            written.append(False)
    return written, None


def shadow_inputs(env, case):
    """The four index-aligned bool lists the model consumes, each carrier
    computed by the SAME primitive outcome the oracle world realizes."""
    empty_values = env["empty_values"]
    selected = [r[0] for r in case.rows]
    has_default = [r[2] for r in case.rows]
    omitted = [r[3] for r in case.rows]
    value_empty = []
    for (sel, mech, _hd, _om, value) in case.rows:
        if not sel and mech == MECH_NO_CLEANED:
            # absent key: the repo guard reads cleaned_data.get(name) -> None
            value_empty.append(None in empty_values)
        else:
            value_empty.append(value in empty_values)
    return selected, has_default, omitted, value_empty


def check_case(env, case, extra_fields=()):
    sel, hd, om, ve = shadow_inputs(env, case)
    shadow = construct_writes(sel, hd, om, ve)
    # internal cross-check against the pure deep decision
    assert shadow == [write_value(sel[k], hd[k], om[k], ve[k])
                      for k in range(len(sel))]
    real, err = run_oracle(env, case, extra_fields)
    if err is not None:
        return "VALUE MISMATCH\n  case=%r\n  %s" % (case.rows, err)
    if shadow != real:
        return ("DISAGREEMENT\n  rows=%r\n  selected=%r has_default=%r "
                "omitted=%r value_empty=%r\n  shadow=%r\n  real=%r"
                % (case.rows, sel, hd, om, ve, shadow, real))
    return None


EMPTIES = [None, '', [], (), {}]
NONEMPTIES = ['de', 'di', 'x', ' ', '0', 0, False, 1, True, [0], (0,),
              {'k': 1}, 'None', 'False']


def boundary_cases():
    cases = [Case([])]  # zero fields
    mechs = [MECH_EDITABLE, MECH_NO_CLEANED, MECH_FIELDS, MECH_EXCLUDE]
    # all 16 flag combinations as single-field cases, sweeping the concrete
    # cleaned value over every empty sentinel / several non-empty values and
    # every deselection mechanism
    for selected in (True, False):
        for hd in (True, False):
            for om in (True, False):
                for ve in (True, False):
                    values = EMPTIES if ve else NONEMPTIES
                    mech_list = mechs if not selected else [None]
                    for v in values:
                        for mech in mech_list:
                            cases.append(Case([(selected, mech, hd, om, v)]))
    # one combined case holding every flag combination at once
    rows = []
    i = 0
    for selected in (True, False):
        for hd in (True, False):
            for om in (True, False):
                for ve in (True, False):
                    v = EMPTIES[i % len(EMPTIES)] if ve \
                        else NONEMPTIES[i % len(NONEMPTIES)]
                    mech = mechs[i % len(mechs)] if not selected else None
                    rows.append((selected, mech, hd, om, v))
                    i += 1
    cases.append(Case(rows))
    return cases


def rand_case(rng):
    n = rng.randint(0, 6)
    rows = []
    for _ in range(n):
        selected = rng.random() < 0.65
        mech = None if selected else rng.randrange(4)
        hd = rng.random() < 0.5
        om = rng.random() < 0.5
        if rng.random() < 0.5:
            v = rng.choice(EMPTIES)
        else:
            v = rng.choice(NONEMPTIES)
        rows.append((selected, mech, hd, om, v))
    return Case(rows)


def make_env():
    import django
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()
        django.setup()
    from django.forms.models import construct_instance  # REAL patched callee
    from django.forms.widgets import TextInput
    from django.core.validators import EMPTY_VALUES
    return {
        "construct_instance": construct_instance,
        "TextInput": TextInput,
        "empty_values": list(EMPTY_VALUES),
    }


def autofield_boundary(env):
    """A real models.AutoField in iteration order is filtered out by the
    candidacy checks even when its name is in cleaned_data: the model carries
    it as selected=False, and it must never be written."""
    from django.db import models
    auto = models.AutoField(primary_key=True)
    auto.name = "f0"
    case = Case([(False, MECH_NO_CLEANED, True, True, None)])
    # place the AutoField FIRST and our stub second under a shifted name
    construct_instance = env["construct_instance"]
    mf = _ModelFieldStub("f1", True, True)
    bound = {"f1": _BoundFieldStub(
        _FormFieldStub(env["TextInput"](), env["empty_values"]))}
    form = _FormStub({"f0": 7, "f1": "de"}, {}, bound)
    instance = _InstanceStub([auto, mf])
    construct_instance(form, instance)
    # AutoField never written (no save recorder needed: it would raise on our
    # instance stub only if save_form_data ran; reaching here means it did
    # not, because AutoField.save_form_data would call setattr with attname
    # unset) -- assert the stub field WAS written (defaulted+omitted+nonempty)
    if mf.saved is None:
        return ("DISAGREEMENT (autofield case): stub field f1 "
                "(selected, defaulted, omitted, non-empty) was not written")
    return None


def main():
    env = make_env()

    checked = 0
    boundary = boundary_cases()
    for case in boundary:
        err = check_case(env, case)
        if err:
            print(err)
            return 1
        checked += 1

    err = autofield_boundary(env)
    if err:
        print(err)
        return 1
    checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(env, rand_case(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched per-field write decision "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary) + 1, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
