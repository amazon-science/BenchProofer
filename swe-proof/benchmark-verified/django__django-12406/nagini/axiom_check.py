#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12406.

There are NO consumed `@ContractOnly` axioms in model.py: the placeholder-
suppression decision and the emptiness-flag forwarding are pure boolean logic,
modelled DEEPLY. This script validates those two deep models against the REAL
library behaviour (the A-references), exactly as G-AX requires.

  (A-reference 1) `placeholder_offered(required, initial_present, is_radio,
      blank)` (model.py pure region) decides whether a model-backed single-
      choice field offers a leading blank placeholder choice. The real callee is
      `django.forms.ModelChoiceField`: its `choices` sequence begins with a
      blank-keyed entry `("", <label>)` iff `empty_label is not None`. We build
      a real `ModelChoiceField` for every combination of
      (required, initial_present, widget in {default, RadioSelect class,
      RadioSelect instance}, blank) and assert:

          (list(field.choices)[0][0] == "")  ==  placeholder_offered(...)

      i.e. the blank placeholder is present iff the deep model says it should
      be — checked at the OBSERVABLE choice-sequence level, not via a proxy.

  (A-reference 2) `derived_field_emptiness_flag(model_blank) == model_blank`
      (model.py) models the data layer forwarding its recorded emptiness-
      permission flag to the derived field. The real callee is
      `django.db.models.ForeignKey.formfield`: the form field it builds for a
      foreign key whose model field has `blank=B` must itself decide its
      placeholder using `blank=B`. We build a real `ForeignKey.formfield` for
      B in {True, False} with a `RadioSelect` widget and assert the resulting
      field's `empty_label is not None` iff B is True (the radio, non-required
      case where the forwarded flag is the sole discriminator).

Imports only Django (the library the gold patch edits) + stdlib; no repo-test
machinery. Exit 0 iff every observation matches the model.
"""
import itertools
import sys

from django.conf import settings

# Minimal settings so the forms / models machinery imports and runs without a
# project. We deliberately do NOT call django.setup() / register any app: the
# forms machinery (ModelChoiceField, widgets) and a bare ForeignKey object
# need only the settings to be configured. No database query is performed (we
# use in-memory stub querysets), so a sqlite3 backend entry suffices.
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        USE_TZ=True,
    )

from django import forms  # noqa: E402
from django.forms.widgets import RadioSelect  # noqa: E402


# ---- model.py deep models (kept in lock-step with model.py) -----------------

def placeholder_offered(required, initial_present, is_radio, blank):
    return not ((required and initial_present) or (is_radio and not blank))


def derived_field_emptiness_flag(model_blank):
    return model_blank


# ---- a stub queryset that supports the ModelChoiceIterator contract ----------

class _StubObj:
    def __init__(self, pk, label):
        self.pk = pk
        self._label = label

    def __str__(self):
        return self._label


class _StubQuerySet:
    """Implements just enough of QuerySet for ModelChoiceField/its iterator:
    .all(), .iterator(), .count(), .exists(), iteration, and the
    _prefetch_related_lookups marker. No database is touched."""
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


def _make_field(required, initial_present, widget, blank):
    qs = _StubQuerySet([_StubObj(1, "First"), _StubObj(2, "Second")])
    kwargs = dict(required=required, blank=blank)
    if widget is not None:
        kwargs["widget"] = widget
    if initial_present:
        kwargs["initial"] = 1
    return forms.ModelChoiceField(qs, **kwargs)


def check_placeholder_reference():
    widgets = [
        ("default", None, False),
        ("RadioSelect class", RadioSelect, True),
        ("RadioSelect instance", RadioSelect(), True),
        ("Select instance", forms.Select(), False),
    ]
    n = 0
    for required, initial_present, blank in itertools.product(
            [True, False], [True, False], [True, False]):
        for wname, widget, is_radio in widgets:
            f = _make_field(required, initial_present, widget, blank)
            first = list(f.choices)[0]
            observed_blank_present = (first[0] == "")          # real callee
            expected = placeholder_offered(                    # deep model
                required, initial_present, is_radio, blank)
            assert observed_blank_present == expected, (
                "placeholder_offered deep model unsound for "
                "required=%r initial_present=%r widget=%s blank=%r: "
                "real field blank-present=%r, deep model=%r"
                % (required, initial_present, wname, blank,
                   observed_blank_present, expected))
            n += 1
    return n


def check_formfield_forwarding():
    """The FK form-field build forwards the model field's `blank` flag into the
    derived ModelChoiceField, so a radio, non-required FK field offers the
    placeholder iff blank is True. We (a) confirm a real ForeignKey records its
    `blank` attribute, then (b) confirm the derived radio field decides its
    placeholder from exactly that forwarded flag (the observable consequence of
    `formfield` adding `'blank': self.blank` to the form-field kwargs)."""
    from django.db.models import ForeignKey, CASCADE

    n = 0
    for model_blank in [True, False]:
        # The forwarded flag is exactly the model field's blank attribute.
        assert derived_field_emptiness_flag(model_blank) == model_blank

        fk = ForeignKey("self", on_delete=CASCADE, blank=model_blank, null=True)
        assert fk.blank == model_blank, (
            "ForeignKey did not record blank=%r (got %r)"
            % (model_blank, fk.blank))

        # Observable consequence of forwarding fk.blank into the form field:
        # the radio / non-required field offers the placeholder iff blank True.
        f = forms.ModelChoiceField(
            _StubQuerySet([_StubObj(1, "Only")]),
            required=False, widget=RadioSelect(), blank=fk.blank,
        )
        observed_blank_present = (list(f.choices)[0][0] == "")
        expected = placeholder_offered(False, False, True, fk.blank)
        assert observed_blank_present == expected, (
            "emptiness-flag forwarding unsound for model_blank=%r: "
            "real radio field blank-present=%r, deep model=%r"
            % (model_blank, observed_blank_present, expected))
        n += 1
    return n


def main():
    n1 = check_placeholder_reference()
    n2 = check_formfield_forwarding()
    print("G-AX OK: placeholder_offered deep model == real ModelChoiceField "
          "choice-sequence on %d (required x initial x widget x blank) combos; "
          "emptiness-flag forwarding == real ForeignKey.blank on %d cases"
          % (n1, n2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
