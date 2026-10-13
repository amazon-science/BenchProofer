#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12406 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helper ``placeholder_offered``
copies over as a plain function (used only as an internal cross-check of the
shadow's branch). ``ChoiceFieldState`` becomes a plain attribute holder. There
are no @ContractOnly callees in this bundle and no PSeq usage, so no sequence
shim is needed.

ORACLE (per mapping.md section 1): the REAL patched repo functions. The gate
applies patch.diff to /testbed before this script runs.

  Site 1 — ``django.forms.ModelChoiceField.__init__``'s decision whether the
  leading blank placeholder choice is offered. The model carrier
  ``ChoiceFieldState.placeholder : Optional[int]`` maps to the real field's
  ``empty_label`` attribute (None <-> None; a present int code <-> the present
  label string, a bijection because the tested behaviour observes only
  present-vs-absent plus "the supplied candidate label is the one carried").
  We also cross-check the documented observable: the field's choice sequence
  begins with a blank-keyed entry iff the placeholder is offered.

  Site 2 — ``django.db.models.ForeignKey.formfield``: the emptiness-permission
  flag the data layer records for the reference is forwarded to the derived
  field unchanged. Oracle: a REAL model class with self-referencing foreign
  keys; ``formfield`` is called on the real field object and the derived form
  field's placeholder state is compared against the shadow pipeline
  (``derived_field_emptiness_flag`` feeding ``configure_placeholder``). The
  radio / non-required configuration makes the forwarded flag the sole
  discriminator, so any forwarding drift is visible in the carrier.

Type bridge (mapping.md section 2): required / initial-present /
presentation-classification / emptiness-permission are booleans on both sides
(``initial_present`` lowers ``initial is not None``; the presentation
classification is whether the normalised widget is a radio presentation). The
candidate label is a present string on the repo side and a present int code on
the model side; per trial a fresh (code, string) pair keeps the bijection
checkable: when offered, the shadow must carry exactly the code and the real
field must carry exactly the string.

Input domain: the shadow's only precondition is a writable placeholder slot,
so every (required, initial, widget, blank, label) tuple with a PRESENT
candidate label is Requires-satisfying (mapping.md pins the candidate label as
a present value). The boolean core is exhausted (every required x
initial-kind x widget-kind x blank combination); the fuzz dimension varies
the candidate label, initial values and widget instances.

>= 1e5 Requires-satisfying inputs: exhaustive boolean boundary + 100000 fuzz
trials on site 1 + exhaustive-and-fuzzed site-2 trials. Pinned fuzz seed:
124060.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the repo under test) only.
"""
import itertools
import random
import sys

SEED = 124060
N_FUZZ = 100000
N_FUZZ_FK = 4000

# --- minimal settings so the real forms/models machinery runs ----------------
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        USE_TZ=True,
    )

import django  # noqa: E402

django.setup()

from django import forms  # noqa: E402
from django.db import models  # noqa: E402
from django.forms.widgets import HiddenInput, RadioSelect, Select  # noqa: E402


# --- shadow: model.py pure region + impl region, contracts stripped ----------

def placeholder_offered(required, initial_present, is_radio, blank):
    return not ((required and initial_present) or (is_radio and not blank))


class ChoiceFieldState(object):
    def __init__(self):
        self.placeholder = None


def configure_placeholder(field, placeholder_label, required, initial_present,
                          is_radio, blank):
    # impl region of model.py, verbatim (contract calls stripped)
    if (required and initial_present) or (is_radio and not blank):
        field.placeholder = None
    else:
        field.placeholder = placeholder_label


def derived_field_emptiness_flag(model_blank):
    # impl region of model.py, verbatim
    return model_blank


# --- stub queryset (no DB touched) for building real ModelChoiceFields -------

class _StubObj(object):
    def __init__(self, pk, label):
        self.pk = pk
        self._label = label

    def __str__(self):
        return self._label


class _StubQuerySet(object):
    """Just enough of the queryset protocol for the real field / its choice
    iterator: .all(), .iterator(), .count(), .exists(), iteration, and the
    prefetch marker attribute."""
    def __init__(self, objs):
        self._objs = list(objs)
        self._prefetch_related_lookups = ()

    def all(self):
        return _StubQuerySet(self._objs)

    def iterator(self):
        return iter(list(self._objs))

    def __iter__(self):
        return iter(list(self._objs))

    def count(self):
        return len(self._objs)

    def exists(self):
        return bool(self._objs)


# --- real model class with self-referencing foreign keys (site-2 oracle) -----
# One reference permits an empty selection at the data layer, the other does
# not; formfield() is called on the REAL field objects.

class _RefNode(models.Model):
    link_may_be_empty = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True,
        related_name="+")
    link_needs_value = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=False, null=True,
        related_name="+")

    class Meta:
        app_label = "sbu_conf_12406"


_FK_BY_FLAG = {
    True: _RefNode._meta.get_field("link_may_be_empty"),
    False: _RefNode._meta.get_field("link_needs_value"),
}


# --- widget kinds and their presentation classification ----------------------

class _RadioVariant(RadioSelect):
    """A subclass of the radio presentation: still classifies as radio."""


def _widget_kinds():
    # (name, factory, is_radio) — factory returns a fresh widget value per
    # trial (class, instance, or None for the field's default).
    return [
        ("default", lambda: None, False),
        ("Select class", lambda: Select, False),
        ("Select instance", lambda: Select(), False),
        ("HiddenInput instance", lambda: HiddenInput(), False),
        ("RadioSelect class", lambda: RadioSelect, True),
        ("RadioSelect instance", lambda: RadioSelect(), True),
        ("RadioSelect subclass instance", lambda: _RadioVariant(), True),
    ]


def _make_real_field(required, initial, widget, blank, label):
    qs = _StubQuerySet([_StubObj(1, "First"), _StubObj(2, "Second")])
    kwargs = dict(required=required, blank=blank, empty_label=label)
    if widget is not None:
        kwargs["widget"] = widget
    if initial is not None:
        kwargs["initial"] = initial
    return forms.ModelChoiceField(qs, **kwargs)


# --- one site-1 comparison ----------------------------------------------------

def check_site1(required, initial, wname, widget, is_radio, blank, label, code,
                check_choices):
    """Shadow vs real field on one input tuple; returns an error string on
    disagreement, else None."""
    initial_present = initial is not None            # bridge: bool lowering
    state = ChoiceFieldState()
    configure_placeholder(state, code, required, initial_present,
                          is_radio, blank)
    shadow_present = state.placeholder is not None

    real = _make_real_field(required, initial, widget, blank, label)
    real_present = real.empty_label is not None

    ctx = ("required=%r initial=%r widget=%s blank=%r label=%r code=%r"
           % (required, initial, wname, blank, label, code))
    if shadow_present != real_present:
        return ("DISAGREEMENT (placeholder offered?) on %s:\n"
                "  shadow (impl region) placeholder present = %r\n"
                "  real patched field carrier present = %r"
                % (ctx, shadow_present, real_present))
    if shadow_present:
        if state.placeholder != code:
            return ("DISAGREEMENT (carried label, shadow side) on %s:\n"
                    "  shadow carries %r, expected the supplied code %r"
                    % (ctx, state.placeholder, code))
        if real.empty_label != label:
            return ("DISAGREEMENT (carried label, real side) on %s:\n"
                    "  real field carries %r, expected the supplied label %r"
                    % (ctx, real.empty_label, label))
    # internal cross-check: the impl branch equals the pure predicate
    if shadow_present != placeholder_offered(required, initial_present,
                                             is_radio, blank):
        return "INTERNAL: impl region and pure predicate disagree on %s" % ctx
    if check_choices:
        # documented observable: choice sequence starts with a blank-keyed
        # entry iff the placeholder is offered
        first = list(real.choices)[0]
        if (first[0] == "") != real_present:
            return ("INTERNAL ORACLE: choice-sequence observable and carrier "
                    "disagree on %s (first entry %r)" % (ctx, first))
    return None


# --- one site-2 comparison ----------------------------------------------------

def check_site2(model_blank, required, initial, wname, widget, is_radio,
                label, code):
    """Shadow forwarding pipeline vs the REAL formfield build on one input
    tuple; returns an error string on disagreement, else None."""
    fk = _FK_BY_FLAG[model_blank]
    # shadow pipeline: forwarded flag, then the placeholder decision on it
    flag = derived_field_emptiness_flag(model_blank)
    initial_present = initial is not None
    state = ChoiceFieldState()
    configure_placeholder(state, code, required, initial_present,
                          is_radio, flag)
    shadow_present = state.placeholder is not None

    kwargs = dict(required=required, empty_label=label)
    if widget is not None:
        kwargs["widget"] = widget
    if initial is not None:
        kwargs["initial"] = initial
    ff = fk.formfield(**kwargs)                      # REAL patched callee
    real_present = ff.empty_label is not None

    ctx = ("model_blank=%r required=%r initial=%r widget=%s label=%r code=%r"
           % (model_blank, required, initial, wname, label, code))
    if shadow_present != real_present:
        return ("DISAGREEMENT (forwarded flag / placeholder) on %s:\n"
                "  shadow pipeline placeholder present = %r\n"
                "  real derived field carrier present = %r"
                % (ctx, shadow_present, real_present))
    if shadow_present:
        if state.placeholder != code or ff.empty_label != label:
            return ("DISAGREEMENT (carried label) on %s:\n"
                    "  shadow carries %r (expected %r); real carries %r "
                    "(expected %r)"
                    % (ctx, state.placeholder, code, ff.empty_label, label))
    return None


# --- drivers -------------------------------------------------------------------

_LABEL_POOL = ["---------", "", "pick one", "\u2014", "0", "None", "x" * 40,
               "\U0001F600", "s\u00e9lection", "  ", "-", "9" * 8]

_INITIAL_POOL = [None, 0, 1, 2, "", "x", _StubObj(1, "First")]


def main():
    checked = 0
    rng = random.Random(SEED)
    widget_kinds = _widget_kinds()

    # (1) exhaustive boolean boundary for site 1: every required x
    # initial-kind x widget-kind x blank combination, with the
    # choice-sequence observable cross-checked
    for required, initial, blank in itertools.product(
            [True, False], _INITIAL_POOL, [True, False]):
        for wname, wfactory, is_radio in widget_kinds:
            label = _LABEL_POOL[checked % len(_LABEL_POOL)]
            code = 1000 + checked
            err = check_site1(required, initial, wname, wfactory(), is_radio,
                              blank, label, code, check_choices=True)
            if err:
                print(err)
                return 1
            checked += 1
    n_boundary = checked

    # (2) site-1 fuzz: random booleans, initial values, widget kinds and
    # candidate labels (pinned seed)
    for i in range(N_FUZZ):
        required = rng.random() < 0.5
        blank = rng.random() < 0.5
        initial = rng.choice(_INITIAL_POOL)
        wname, wfactory, is_radio = rng.choice(widget_kinds)
        label = rng.choice(_LABEL_POOL) + (
            "" if rng.random() < 0.5 else str(rng.randint(0, 999)))
        code = rng.randint(-10**6, 10**6)
        err = check_site1(required, initial, wname, wfactory(), is_radio,
                          blank, label, code, check_choices=(i % 1000 == 0))
        if err:
            print(err)
            return 1
        checked += 1

    # (3) exhaustive site-2 boundary: both data-layer flags x the
    # discriminating and non-discriminating derived-field configurations
    fk_configs = [
        # (required, initial, widget-kind index) — radio non-required is the
        # configuration where the forwarded flag alone decides
        (False, None, 5), (False, None, 4), (False, None, 6),
        (True, None, 5), (True, 1, 5),
        (False, None, 2), (False, None, 0), (True, 1, 2),
    ]
    for model_blank in [True, False]:
        for required, initial, wi in fk_configs:
            wname, wfactory, is_radio = widget_kinds[wi]
            label = _LABEL_POOL[checked % len(_LABEL_POOL)]
            code = 2000 + checked
            err = check_site2(model_blank, required, initial, wname,
                              wfactory(), is_radio, label, code)
            if err:
                print(err)
                return 1
            checked += 1

    # (4) site-2 fuzz (pinned seed continues)
    for _ in range(N_FUZZ_FK):
        model_blank = rng.random() < 0.5
        required = rng.random() < 0.5
        initial = rng.choice(_INITIAL_POOL)
        wname, wfactory, is_radio = rng.choice(widget_kinds)
        label = rng.choice(_LABEL_POOL)
        code = rng.randint(-10**6, 10**6)
        err = check_site2(model_blank, required, initial, wname, wfactory(),
                          is_radio, label, code)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched placeholder decision and "
          "flag forwarding on %d inputs (%d exhaustive boundary + %d site-1 "
          "fuzz + site-2 exhaustive + %d site-2 fuzz, seed %d); "
          "0 disagreements." % (checked, n_boundary, N_FUZZ, N_FUZZ_FK, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)"}'
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
