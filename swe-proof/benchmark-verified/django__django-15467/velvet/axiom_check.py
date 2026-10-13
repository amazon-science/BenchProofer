#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15467.

The modeled slice consumes NO axiom: its only external value is the standard
fallback placeholder `_("None")`, modeled DEEPLY in Solution.lean's `pure`
region as the literal `defaultLabel = some "None"`. This is an **A-reference**
(SPEC_GUIDE §0.7, §3): a deep model validated == the real callee, not a consumed
axiom. G-AX validates that model against the real callee here.

The one A-reference check:

  (A-reference) the deep model `defaultLabel` (Solution.lean: `some "None"`)
      equals the real `django.utils.translation.gettext("None")` under the
      default locale active in the admin-widgets test environment (no
      translation catalog installed for the test models — the locale the F2P
      test `test_radio_fields_foreignkey_formfield_overrides_empty_label`
      runs in). We assert it for both the active default and an explicitly
      forced default ('en'), and confirm `gettext_lazy("None")` resolves to the
      same `str`.

Additionally we exercise `resolved_label` — the Python transliteration of
Solution.lean's `resolvedLabel` — over the placeholder semantics to confirm the
model is internally faithful to the "keep caller value else fallback; no
placeholder when blank not admitted" rule (a self-consistency check; the
behavioural equivalence to the real patched function is G-CONF's job).

Imports only `django` (present in the instance image) + stdlib. Exit 0 iff every
obligation holds.
"""
import sys

# A sentinel for "caller supplied nothing" (carrier `none`) vs "supplied None".
_ABSENT = object()

# --- Solution.lean model reference encodings (in lock-step with the spec) ----

DEFAULT_LABEL = "None"  # Solution.lean: defaultLabel = some "None"


def resolved_label(allows_blank, override):
    """resolvedLabel allowsBlank override (Solution.lean), transliterated.

    override is _ABSENT (carrier `none`) or a value (carrier `some v`)."""
    if allows_blank:
        return DEFAULT_LABEL if override is _ABSENT else override
    return None


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                            "django.contrib.admin"],
            USE_I18N=True,
            USE_TZ=True,
        )
    django.setup()


def check_default_label_reference():
    """A-reference: defaultLabel (model 'None') == real gettext('None')."""
    from django.utils import translation

    # Active default locale (the F2P test environment installs no catalog for
    # the test models, so the source string passes through unchanged).
    observed = translation.gettext("None")
    assert observed == DEFAULT_LABEL, (
        "defaultLabel A-reference unsound (active default locale): "
        "gettext('None') gave %r, deep model gives %r"
        % (observed, DEFAULT_LABEL))

    # Explicitly forced default language 'en' — same result, no en catalog
    # translates the bare source string 'None'.
    with translation.override("en"):
        observed_en = translation.gettext("None")
    assert observed_en == DEFAULT_LABEL, (
        "defaultLabel A-reference unsound (forced 'en'): gettext('None') gave "
        "%r, deep model gives %r" % (observed_en, DEFAULT_LABEL))

    # With i18n disabled (no active translation) the source string is returned
    # verbatim — the most conservative reading of the default.
    with translation.override(None):
        observed_none = translation.gettext("None")
    assert observed_none == DEFAULT_LABEL, (
        "defaultLabel A-reference unsound (no active translation): "
        "gettext('None') gave %r, deep model gives %r"
        % (observed_none, DEFAULT_LABEL))

    # gettext_lazy resolves to the same str when coerced.
    lazy = translation.gettext_lazy("None")
    assert str(lazy) == DEFAULT_LABEL, (
        "defaultLabel A-reference unsound: str(gettext_lazy('None')) = %r"
        % (str(lazy),))


def check_resolved_label_self_consistency():
    """Confirm resolved_label encodes 'keep caller value else fallback; no
    placeholder when blank not admitted' — the rule Solution.lean's spec pins."""
    # blank admitted, nothing supplied -> the fallback placeholder
    assert resolved_label(True, _ABSENT) == DEFAULT_LABEL
    # blank admitted, a caller value supplied -> kept verbatim
    for v in ["Custom empty label", "", "None", "x", "—", None]:
        assert resolved_label(True, v) == v, (
            "resolved_label dropped caller value %r" % (v,))
    # blank NOT admitted -> no placeholder, regardless of what was supplied
    assert resolved_label(False, _ABSENT) is None
    for v in ["Custom empty label", "", None, "None"]:
        assert resolved_label(False, v) is None, (
            "resolved_label produced a placeholder for a non-blank field "
            "with override %r" % (v,))


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover
        print("G-AX ERROR: could not configure Django: %r" % (exc,))
        return 2

    check_default_label_reference()
    check_resolved_label_self_consistency()

    print("G-AX OK: defaultLabel deep model (== real gettext('None')) sound "
          "under active-default / forced-'en' / no-translation locales and "
          "gettext_lazy; resolved_label self-consistent on blank/non-blank × "
          "{absent, value, None} placeholder cases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
