#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13212.

There is NO consumed @ContractOnly axiom in this bundle: the changed behaviour
(which placeholders each rejection's parameter mapping binds) is modelled
deeply in model.py's impl region. The one *unchanged* mechanism the deep model
leans on is the rendering of a custom error template against an error's
parameter mapping -- Python's `%`-style named interpolation in
`ValidationError.__iter__` (`message %= error.params`), combined with the
form-field message override that PRESERVES `error.params`
(`Field.run_validators`). This check validates that A-reference against the
REAL Django stack, end to end, in-container.

It asserts, on the real framework:

  (A-reference, model `build_invalid_params` / `build_limit_params`)
     A `ValidationError` whose params bind the `'value'` placeholder to the
     offending input renders a custom `'%(value)s'` template to `str(value)`;
     a bound-limit error additionally still renders `'%(max)s'`. We exercise
     this through the actual form path the F2P tests use
     (`MyForm({'field': value}); form.is_valid(); form.errors`), enumerating
     EVERY FAIL_TO_PASS case so a skip on any of them fails loudly.

  (converse / load-bearingness)
     With the PRE-PATCH parameter maps (no `'value'` binding), the same
     `'%(value)s'` template does NOT render to `str(value)` -- it raises a
     KeyError on interpolation. This confirms the `'value'` binding the model
     requires is exactly what makes the behaviour observable.

  (decimal control-flow, model `decimal_reject_params`)
     The `DecimalField.validate` deletion: on the GOLD stack a NOT-finite
     `Decimal` (NaN / sNaN / +-Infinity) is routed to `DecimalValidator`'s bare
     rejection, whose `.params` binds `'value'`, so a `'%(value)s'` template
     renders `str(value)` -- asserted at the raw-validator key-set layer for
     every not-finite shape AND end-to-end through the form. The converse
     reconstructs the deleted paramless screen and asserts it is detectably
     wrong (cannot render `'%(value)s'` to `str(value)`), so the deletion is
     load-bearing.

Imports only Django (the framework under test) and the standard library. Exit 0
iff every observation holds.
"""
import sys
import types


def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            USE_I18N=False,
            DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
        )
    django.setup()


# --- (A-reference) the real form/render path, every F2P case ----------------

def check_char_field_cases():
    """test_value_placeholder_with_char_field: each validator rejects `value`
    and the custom '%(value)s' template renders the input verbatim."""
    from django import forms
    from django.core import validators

    cases = [
        (validators.validate_integer, '-42.5', 'invalid'),
        (validators.validate_email, 'a', 'invalid'),
        (validators.validate_email, 'a@b\n.com', 'invalid'),
        (validators.validate_email, 'a\n@b.com', 'invalid'),
        (validators.validate_slug, '你 好', 'invalid'),
        (validators.validate_unicode_slug, '你 好', 'invalid'),
        (validators.validate_ipv4_address, '256.1.1.1', 'invalid'),
        (validators.validate_ipv6_address, '1:2', 'invalid'),
        (validators.validate_ipv46_address, '256.1.1.1', 'invalid'),
        (validators.validate_comma_separated_integer_list, 'a,b,c', 'invalid'),
        (validators.int_list_validator(), '-1,2,3', 'invalid'),
        (validators.MaxLengthValidator(10), 11 * 'x', 'max_length'),
        (validators.MinLengthValidator(10), 9 * 'x', 'min_length'),
        (validators.URLValidator(), 'no_scheme', 'invalid'),
        (validators.URLValidator(), 'http://test[.com', 'invalid'),
        (validators.URLValidator(), 'http://[::1:2::3]/', 'invalid'),
        (validators.URLValidator(),
         'http://' + '.'.join(['a' * 35 for _ in range(9)]), 'invalid'),
        (validators.RegexValidator('[0-9]+'), 'xxxxxx', 'invalid'),
    ]
    for validator, value, code in cases:
        if isinstance(validator, types.FunctionType):
            name = validator.__name__
        else:
            name = type(validator).__name__

        class MyForm(forms.Form):
            field = forms.CharField(
                validators=[validator],
                error_messages={code: '%(value)s'},
            )

        form = MyForm({'field': value})
        assert form.is_valid() is False, (
            "%s should reject %r" % (name, value))
        assert form.errors == {'field': [value]}, (
            "%s/%r: value placeholder did not render the input: %r"
            % (name, value, dict(form.errors)))


def check_null_character_case():
    """test_value_placeholder_with_null_character."""
    from django import forms

    class MyForm(forms.Form):
        field = forms.CharField(
            error_messages={'null_characters_not_allowed': '%(value)s'},
        )

    form = MyForm({'field': 'a\0b'})
    assert form.is_valid() is False
    assert form.errors == {'field': ['a\x00b']}, dict(form.errors)


def check_integer_field_cases():
    """test_value_placeholder_with_integer_field."""
    from django import forms
    from django.core import validators

    cases = [
        (validators.MaxValueValidator(0), 1, 'max_value'),
        (validators.MinValueValidator(0), -1, 'min_value'),
        (validators.URLValidator(), '1', 'invalid'),
    ]
    for validator, value, code in cases:
        class MyForm(forms.Form):
            field = forms.IntegerField(
                validators=[validator],
                error_messages={code: '%(value)s'},
            )

        form = MyForm({'field': value})
        assert form.is_valid() is False
        assert form.errors == {'field': [str(value)]}, (
            "%r: %r" % (value, dict(form.errors)))


def check_decimal_field_cases():
    """test_value_placeholder_with_decimal_field -- includes the NaN case that
    the DecimalField.validate removal routes to the param-carrying validator,
    and the bound-limit (max_*) cases that keep the '%(max)s' binding."""
    from django import forms

    cases = [
        ('NaN', 'invalid'),
        ('123', 'max_digits'),
        ('0.12', 'max_decimal_places'),
        ('12', 'max_whole_digits'),
    ]
    for value, code in cases:
        class MyForm(forms.Form):
            field = forms.DecimalField(
                max_digits=2,
                decimal_places=1,
                error_messages={code: '%(value)s'},
            )

        form = MyForm({'field': value})
        assert form.is_valid() is False
        assert form.errors == {'field': [value]}, (
            "%r/%s: %r" % (value, code, dict(form.errors)))


def check_decimal_notfinite_routing():
    """decimal_reject_params reference: the DecimalField.validate control-flow
    deletion. On the GOLD-patched stack a NOT-finite Decimal (NaN / signalling
    NaN / Infinity) is no longer short-circuited by a paramless screen but flows
    through to DecimalValidator.__call__'s `exponent in {'F','n','N'}` bare
    rejection, whose error binds 'value' -- so a custom '%(value)s' template
    renders str(value). We assert this for EVERY not-finite shape, both at the
    raw validator layer (the params key set) and end-to-end through the form.

    Converse: with the PRE-PATCH DecimalField.validate present, a not-finite
    candidate is intercepted FIRST by a paramless ValidationError(..., 'invalid')
    -- which cannot render '%(value)s' to str(value). We reconstruct that
    pre-patch screen exactly and assert it is detectably wrong, confirming the
    deletion (the modeled control-flow change) is load-bearing.
    """
    from decimal import Decimal
    from django import forms
    from django.core import validators
    from django.core.exceptions import ValidationError

    notfinite = ['NaN', 'sNaN', 'Infinity', '-Infinity']

    # (1) GOLD: the not-finite Decimal reaches DecimalValidator's bare rejection,
    # which binds 'value'. Exercise the raw validator (the routing target) and
    # read its produced params key set directly.
    dv = validators.DecimalValidator(max_digits=2, decimal_places=1)
    for s in notfinite:
        d = Decimal(s)
        assert not d.is_finite(), s
        raised = None
        try:
            dv(d)
        except ValidationError as e:
            raised = e
        assert raised is not None, (
            "DecimalValidator should reject not-finite %r" % s)
        # The gold patch makes this bare rejection carry params={'value': value}.
        assert getattr(raised, 'params', None) is not None and \
            'value' in raised.params, (
            "not-finite rejection must bind 'value' (gold routing), got %r"
            % (getattr(raised, 'params', None),))
        # The bound value IS the offending decimal object itself (identity --
        # NaN != NaN under ==, so compare by identity / string form, not ==).
        assert raised.params['value'] is d, (
            "the bound value must be the offending decimal itself")

    # (2) GOLD end-to-end through the form: a custom '%(value)s' template renders
    # str(value) for a not-finite decimal (the F2P 'NaN' case, generalised).
    for s in ['NaN', 'Infinity', '-Infinity']:
        class MyForm(forms.Form):
            field = forms.DecimalField(
                max_digits=2,
                decimal_places=1,
                error_messages={'invalid': '%(value)s'},
            )

        form = MyForm({'field': s})
        assert form.is_valid() is False, s
        assert form.errors == {'field': [s]}, (
            "not-finite %r: value placeholder did not render the input: %r"
            % (s, dict(form.errors)))

    # (3) CONVERSE: the PRE-PATCH DecimalField.validate screen, reconstructed
    # exactly, intercepts FIRST with a paramless rejection -- which cannot render
    # '%(value)s' to str(value). This is the behaviour the deletion removes.
    for s in notfinite:
        d = Decimal(s)
        # the deleted screen: raise ValidationError(msg, code='invalid') -- no params
        prepatch_err = ValidationError('%(value)s', code='invalid')
        rendered = list(prepatch_err)
        assert rendered == ['%(value)s'], rendered
        assert rendered != [str(d)], (
            "pre-patch paramless not-finite screen unexpectedly rendered the "
            "input for %r" % s)


def check_file_field_case():
    """test_value_placeholder_with_file_field -- the bound-limit-shaped
    extension validator (value added to a params dict already carrying
    other bindings)."""
    from django import forms
    from django.core import validators
    from django.core.files.uploadedfile import SimpleUploadedFile

    class MyForm(forms.Form):
        field = forms.FileField(
            validators=[validators.validate_image_file_extension],
            error_messages={'invalid_extension': '%(value)s'},
        )

    form = MyForm(files={'field': SimpleUploadedFile('myfile.txt', b'abc')})
    assert form.is_valid() is False
    assert form.errors == {'field': ['myfile.txt']}, dict(form.errors)


def check_bound_limit_keeps_max():
    """A bound-limit rejection still renders the pre-existing '%(max)s'
    placeholder -- the limit binding is preserved alongside the added value."""
    from django import forms

    class MyForm(forms.Form):
        field = forms.DecimalField(
            max_digits=2,
            decimal_places=1,
            error_messages={'max_digits': '%(max)s|%(value)s'},
        )

    form = MyForm({'field': '123'})
    assert form.is_valid() is False
    # max_digits == 2, value == '123': both placeholders must render.
    assert form.errors == {'field': ['2|123']}, dict(form.errors)


# --- converse: the pre-patch param maps cannot render '%(value)s' -----------

def check_value_binding_is_load_bearing():
    """With the PRE-PATCH parameter maps (no 'value' key), a '%(value)s'
    template does NOT render to str(value) -- so the binding the model requires
    is exactly what makes the input renderable.

    Two distinct pre-patch failure modes, matching __iter__'s `if error.params`
    guard (django/core/exceptions.py):
      * bare rejection (params is None): the guard is false, so no
        interpolation happens at all -- the literal template is yielded, never
        str(value);
      * bound-limit rejection (params is {'max': ...}, no 'value'): the guard
        is true, so `message %= params` runs and raises KeyError on 'value'.
    """
    from django.core.exceptions import ValidationError

    value = 'blah'

    # bare rejection, pre-patch: params is None -> no interpolation, literal
    # template yielded; in particular it does NOT render to str(value).
    err = ValidationError('%(value)s', code='invalid')
    rendered = list(err)
    assert rendered == ['%(value)s'], rendered
    assert rendered != [value], (
        "pre-patch bare rejection unexpectedly rendered the input")

    # bound-limit rejection, pre-patch: params has 'max' but no 'value' -> the
    # interpolation runs and raises KeyError on the missing 'value' key.
    err2 = ValidationError('%(value)s', code='max_digits', params={'max': 2})
    raised2 = False
    try:
        list(err2)
    except KeyError:
        raised2 = True
    assert raised2, "pre-patch bound-limit rejection unexpectedly rendered %(value)s"

    # post-patch shapes DO render to str(value) (positive control of mechanism)
    ok = ValidationError('%(value)s', code='invalid', params={'value': value})
    assert list(ok) == [value], list(ok)
    ok2 = ValidationError('%(max)s|%(value)s', code='max_digits',
                          params={'max': 2, 'value': '123'})
    assert list(ok2) == ['2|123'], list(ok2)


def main():
    configure_django()
    check_char_field_cases()
    check_null_character_case()
    check_integer_field_cases()
    check_decimal_field_cases()
    check_decimal_notfinite_routing()
    check_file_field_case()
    check_bound_limit_keeps_max()
    check_value_binding_is_load_bearing()
    print("G-AX OK: rendering A-reference sound on all 5 FAIL_TO_PASS groups "
          "(char/null/integer/decimal/file) + bound-limit '%(max)s' "
          "preservation + DecimalField not-finite routing (the validate-deletion "
          "control-flow change, every not-finite shape, gold + pre-patch "
          "converse); pre-patch maps confirmed unable to render %(value)s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
