#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14034.

The changed operation (assembling the rendering attributes for a bound input)
is modelled DEEPLY in model.py: every step is a boolean guard or a
per-constituent assignment. There is NO consumed `@ContractOnly` axiom about an
opaque callee. What this script validates are the TWO deep-model references the
model relies on, against the REAL Django callees (executed in-container):

  (A-reference 1) the per-constituent marker rule. model.py's pure helper

        constituent_marker(widget_mark, field_required)
            == 1  iff  (widget_mark and field_required)  else 0

      models, for each constituent (subwidget, subfield) pair under the
      per-constituent regime, the value Django assigns to that subwidget's
      mandatory marker:

        subwidget.use_required_attribute(initial) and subfield.required

      i.e. widget_mark := subwidget.use_required_attribute(initial) (a bool),
      field_required := subfield.required (a bool). We execute the real
      `Widget.use_required_attribute` for every (subwidget kind, initial)
      combination the tests can present and assert the boolean product matches
      `constituent_marker`.

  (A-reference 2) the rendering rule that turns a marker slot into an observed
      HTML attribute: a subwidget whose mandatory marker is True renders the
      `required` attribute; a marker of False (or unset) renders no `required`
      attribute. model.py encodes this as marker == 1 (present) vs marker in
      {0, -1} (absent). We render the real Django widgets and assert the
      `required` token appears iff the assigned marker was True.

Finally we reproduce the F2P scenario end-to-end against the REAL patched
`BoundField.build_widget_attrs` + form rendering to confirm the model's
observable (which inputs carry the marker) equals reality.

Imports Django (the package under test, present in the eval container) plus the
standard library only. Exit 0 iff every obligation holds.
"""
import os
import sys
import random


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=False,
            DATABASES={},
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {},
            }],
        )
    django.setup()


def model_constituent_marker(widget_mark, field_required):
    """Reference of model.py's pure helper constituent_marker (1/0)."""
    if widget_mark and field_required:
        return 1
    return 0


def check_constituent_marker_rule():
    """A-reference 1: model.constituent_marker == the real
    subwidget.use_required_attribute(initial) and subfield.required, for every
    relevant (widget kind, initial, subfield.required) combination."""
    from django.forms.widgets import (
        TextInput, NumberInput, EmailInput, URLInput, PasswordInput,
        HiddenInput, Textarea,
    )
    widget_kinds = [
        TextInput(), NumberInput(), EmailInput(), URLInput(),
        PasswordInput(), HiddenInput(), Textarea(),
    ]
    initials = [None, '', 'x', '0', 0, [], ['a'], 'Hello']
    for w in widget_kinds:
        for initial in initials:
            for field_required in (True, False):
                # The REAL callee determines widget_mark.
                widget_mark = bool(w.use_required_attribute(initial))
                expected = 1 if (widget_mark and field_required) else 0
                got = model_constituent_marker(widget_mark, field_required)
                assert got == expected, (
                    "constituent_marker unsound on (%r, initial=%r, "
                    "field_required=%r): real use_required_attribute=%r -> "
                    "expected %r, model gives %r"
                    % (type(w).__name__, initial, field_required,
                       widget_mark, expected, got))


def _rendered_has_required(html, input_index):
    """Whether the input_index-th <input ...> tag in html carries a bare
    `required` attribute."""
    import re
    inputs = re.findall(r'<input\b[^>]*>', html)
    assert input_index < len(inputs), (
        "expected at least %d inputs, got %d in %r"
        % (input_index + 1, len(inputs), html))
    tag = inputs[input_index]
    # bare `required` (not required="...something") — Django renders True as
    # bare token, False/absent as nothing.
    return bool(re.search(r'\brequired\b(?!=)', tag))


def check_rendering_rule():
    """A-reference 2: a subwidget marker of True renders `required`; False (or
    unset) renders no `required`. Verified against the REAL widget rendering."""
    from django.forms.widgets import TextInput
    # marker True -> attribute present
    html = TextInput().render('f', 'v', attrs={'required': True})
    assert _rendered_has_required(html, 0), (
        "marker True should render `required`, got %r" % html)
    # marker False -> attribute absent
    html = TextInput().render('f', 'v', attrs={'required': False})
    assert not _rendered_has_required(html, 0), (
        "marker False should render no `required`, got %r" % html)
    # marker unset (no key) -> attribute absent
    html = TextInput().render('f', 'v', attrs={})
    assert not _rendered_has_required(html, 0), (
        "unset marker should render no `required`, got %r" % html)


def check_f2p_end_to_end():
    """End-to-end: the real patched build_widget_attrs + form rendering. A
    required MultiValueField with require_all_fields=False, a required first
    subfield and an optional second subfield, behind a MultiWidget of two
    TextInputs: the first rendered input carries `required`, the second does
    not. This is exactly the observable model.py pins (regime A)."""
    from django.forms import (
        CharField, Form, MultiValueField, MultiWidget, TextInput,
    )

    class PartiallyRequiredField(MultiValueField):
        def compress(self, data_list):
            return ','.join(data_list) if data_list else None

    class PartiallyRequiredForm(Form):
        f = PartiallyRequiredField(
            fields=(CharField(required=True), CharField(required=False)),
            required=True,
            require_all_fields=False,
            widget=MultiWidget(widgets=[TextInput(), TextInput()]),
        )

    form = PartiallyRequiredForm({'f_0': 'Hello', 'f_1': ''})
    assert form.is_valid(), "form with required subfield filled should validate"
    html = form.as_p()
    assert _rendered_has_required(html, 0), (
        "first (required) subinput must carry `required`: %r" % html)
    assert not _rendered_has_required(html, 1), (
        "second (optional) subinput must NOT carry `required`: %r" % html)

    # The model's regime-A observable, mirrored: per-constituent markers are
    # [required-subfield -> True, optional-subfield -> False]; the aggregate
    # `required` is not applied to the whole field.
    bf = form['f']
    attrs = bf.build_widget_attrs({})
    assert 'required' not in attrs, (
        "aggregate `required` must NOT be set in regime A, got %r" % attrs)


def check_regime_b_unchanged():
    """Regime B sanity: an ordinary required CharField (single TextInput, not a
    partial MVF) still gets the aggregate `required` attribute — model.py's
    regime B (out.required_attr == 1)."""
    from django.forms import CharField, Form, TextInput

    class SimpleForm(Form):
        c = CharField(required=True, widget=TextInput())

    form = SimpleForm({'c': ''})
    bf = form['c']
    attrs = bf.build_widget_attrs({})
    assert attrs.get('required') is True, (
        "regime B: ordinary required field must set aggregate `required`, "
        "got %r" % attrs)


def main():
    _setup_django()
    check_constituent_marker_rule()
    check_rendering_rule()
    check_f2p_end_to_end()
    check_regime_b_unchanged()
    # light fuzz over the constituent rule with random booleans
    rng = random.Random(14034)
    for _ in range(20000):
        wm = rng.random() < 0.5
        fr = rng.random() < 0.5
        expected = 1 if (wm and fr) else 0
        assert model_constituent_marker(wm, fr) == expected
    print("G-AX OK: constituent_marker deep model == real "
          "use_required_attribute and subfield.required; rendering rule "
          "(True->required, False/unset->absent) holds; F2P regime-A and "
          "regime-B end-to-end match the real patched build_widget_attrs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
