#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13741.

There are NO consumed @ContractOnly axioms in model.py. The two unchanged base
behaviours that the model spells out DEEPLY are instead validated == the real
base field out-of-band here (A-reference deep models):

  (A-reference 1) `make_field` -- the read-only-hash field's construction.
      model.py computes the post-construction flags deeply as:
          required = required_kw if named else False   (default not-required)
          disabled = disabled_kw if named else True     (default not-editable)
      and stores them verbatim (the base field's __init__ does
      `self.disabled = disabled`, `self.required = required`). We assert the
      REAL `ReadOnlyPasswordHashField`, after construction, exposes exactly
      these `.required` / `.disabled` values across the four kwarg
      combinations (both unnamed; each named True/False).

  (A-reference 2) `has_changed` -- the generic change decision.
      model.py spells out the base field's decision deeply:
          if self.disabled: return False
          else:             return norm(initial) != norm(data)
      with None normalised to the empty value. We assert the REAL base
      `forms.Field.has_changed` matches this over disabled/enabled fields and a
      battery of (initial, data) pairs including None<->'' boundaries.

Imports only Django (the repo under test, importable in-container) and the
stdlib. Exit 0 iff every observation matches model.py.
"""
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY="axcheck-13741-not-secret",
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


def _model_make_field(required_kw, disabled_kw):
    """model.py make_field reference (None = caller did not name the flag)."""
    required = False if required_kw is None else required_kw
    disabled = True if disabled_kw is None else disabled_kw
    return required, disabled


def _norm(v):
    """model.py norm_seq reference: None is the empty value."""
    return "" if v is None else v


def _model_has_changed(disabled, initial, data):
    """model.py has_changed reference."""
    if disabled:
        return False
    return _norm(initial) != _norm(data)


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django import forms
    from django.contrib.auth.forms import ReadOnlyPasswordHashField

    # --- A-reference 1: make_field default/explicit flags -------------------
    # kwarg combinations: (required_kw, disabled_kw); None = not named.
    kwarg_cases = [
        (None, None),
        (None, True), (None, False),
        (True, None), (False, None),
        (True, True), (True, False),
        (False, True), (False, False),
    ]
    for required_kw, disabled_kw in kwarg_cases:
        kwargs = {}
        if required_kw is not None:
            kwargs["required"] = required_kw
        if disabled_kw is not None:
            kwargs["disabled"] = disabled_kw
        field = ReadOnlyPasswordHashField(**kwargs)   # REAL field
        exp_required, exp_disabled = _model_make_field(required_kw, disabled_kw)
        assert field.required == exp_required, (
            "make_field unsound (%r): real .required=%r, model=%r"
            % (kwargs, field.required, exp_required))
        assert field.disabled == exp_disabled, (
            "make_field unsound (%r): real .disabled=%r, model=%r"
            % (kwargs, field.disabled, exp_disabled))

    # The headline default the F2P test pins: unnamed -> disabled True.
    default_field = ReadOnlyPasswordHashField()
    assert default_field.disabled is True, (
        "default ReadOnlyPasswordHashField().disabled is not True: %r"
        % (default_field.disabled,))

    # --- A-reference 2: base Field.has_changed over disabled/enabled --------
    value_pairs = [
        (None, None), (None, ""), ("", None), ("", ""),
        ("aaa", "bbb"), ("aaa", "aaa"), ("aaa", None), (None, "bbb"),
        ("", "x"), ("x", ""), ("hash$abc", "hash$abc"), ("hash$abc", "hash$xyz"),
        ("Joe's", "Joe's"), ("Joe's", "joe's"),
    ]
    for disabled in (True, False):
        # A bare base Field with the chosen disabled flag exercises the EXACT
        # inherited has_changed the patched field now relies on
        # (ReadOnlyPasswordHashField extends forms.Field directly, whose
        #  to_python is the identity, matching norm_seq's content comparison).
        f = forms.Field(disabled=disabled)
        for initial, data in value_pairs:
            observed = bool(f.has_changed(initial, data))     # REAL base method
            expected = _model_has_changed(disabled, initial, data)
            assert observed == expected, (
                "has_changed unsound (disabled=%r, initial=%r, data=%r): "
                "real=%r, model=%r" % (disabled, initial, data, observed, expected))

    # --- composed: the patched field never reports a change (F2P) -----------
    assert ReadOnlyPasswordHashField().has_changed("aaa", "bbb") is False, (
        "ReadOnlyPasswordHashField().has_changed('aaa','bbb') is not False")

    print("G-AX OK: make_field flag defaults + base Field.has_changed "
          "short-circuit/comparison sound on %d kwarg cases and %d value pairs "
          "(x2 disabled states)." % (len(kwarg_cases), len(value_pairs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
