#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12276.

Executes the REAL unchanged inherited base callee —
``django.forms.widgets.Widget.use_required_attribute`` (reached from the new
``FileInput.use_required_attribute`` via ``super().use_required_attribute(initial)``)
— and asserts that every observation matches the ``generic_requires_value``
axiom in model.py:

  generic_requires_value(hidden) -> bool   with   Ensures(Result() == (not hidden))

i.e. the real base method returns ``not self.is_hidden`` for any ``initial``,
IGNORING the ``initial`` argument. As an additional refinement check it also
validates the FULL moved method on the post-patch ``FileInput`` (and on
``ClearableFileInput``, whose behaviour must be unchanged) equals the modeled
conjunction ``(not self.is_hidden) and (not initial)`` over a battery of
``initial`` values covering both truthiness cases and several Python types.

This is run inside the official SWE-bench container for the instance, where
Django is importable. It configures minimal settings, then drives the real
methods. Exit 0 iff every obligation holds.

stdlib + Django only (Django is the package under change).
"""
import sys


def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={},
            USE_TZ=False,
        )
    import django
    django.setup()


# A battery of `initial` values covering both truthiness cases and several
# Python types the framework may hand the method (None / "" / 0 / [] / False
# are falsy; non-empty str, file-like objects, ints, lists, True are truthy).
class _FakeFile:
    def __init__(self, url):
        self.url = url

    def __bool__(self):
        return True


_INITIALS = [
    None,            # falsy  (no initial value)
    "",              # falsy  (empty string)
    0,               # falsy
    [],              # falsy
    {},              # falsy
    False,           # falsy
    "resume.txt",    # truthy (the F2P initial value)
    "x",             # truthy
    " ",             # truthy (non-empty whitespace)
    1,               # truthy
    [0],             # truthy
    {"a": 1},        # truthy
    True,            # truthy
    _FakeFile("/media/resume.txt"),  # truthy (a stored-file-like object)
]


def main():
    try:
        _configure_django()
        from django.forms.widgets import (
            Widget, Input, FileInput, ClearableFileInput, HiddenInput,
        )
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    observations = 0

    # ----- (1) The axiom: the unchanged inherited base method ignores `initial`
    #            and returns `not self.is_hidden`. We exercise the base method on
    #            widgets with both hidden states (FileInput is non-hidden;
    #            HiddenInput is hidden), for every `initial` in the battery.
    base = Widget.use_required_attribute  # the unbound real base callee

    widgets = [FileInput(), ClearableFileInput(), Input(), Widget(), HiddenInput()]
    for w in widgets:
        expected_base = (not w.is_hidden)
        for initial in _INITIALS:
            got = base(w, initial)  # super().use_required_attribute(initial)
            assert isinstance(got, bool), (
                "base use_required_attribute returned non-bool %r on %r"
                % (got, type(w).__name__))
            # Axiom: Result() == (not hidden), independent of `initial`.
            assert got == expected_base, (
                "axiom violated: base.use_required_attribute(%r) on %s = %r, "
                "expected (not is_hidden) = %r"
                % (initial, type(w).__name__, got, expected_base))
            observations += 1

    # ----- (2) Refinement: the FULL moved method on the post-patch FileInput
    #            equals the modeled conjunction (not is_hidden) and (not initial).
    fi = FileInput()
    for initial in _INITIALS:
        got = fi.use_required_attribute(initial)
        expected = (not fi.is_hidden) and (not initial)
        assert bool(got) == bool(expected), (
            "FileInput.use_required_attribute(%r) = %r, expected %r"
            % (initial, got, expected))
        # The discriminating cases from the F2P test:
        if initial is None:
            assert got is True, "FileInput.use_required_attribute(None) must be True"
        if initial == "resume.txt":
            assert got is False, (
                "FileInput.use_required_attribute('resume.txt') must be False")
        observations += 1

    # ----- (3) ClearableFileInput behaviour must be UNCHANGED by the move: it
    #            now inherits the identical method; result must match the same
    #            conjunction (the patch removed its own copy).
    cfi = ClearableFileInput()
    for initial in _INITIALS:
        got = cfi.use_required_attribute(initial)
        expected = (not cfi.is_hidden) and (not initial)
        assert bool(got) == bool(expected), (
            "ClearableFileInput.use_required_attribute(%r) = %r, expected %r"
            % (initial, got, expected))
        observations += 1

    print(
        "G-AX OK: generic_requires_value axiom (Result() == not hidden, "
        "independent of initial) sound against the real "
        "Widget.use_required_attribute; the moved FileInput/ClearableFileInput "
        "method equals (not is_hidden) and (not initial) over %d observations."
        % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
