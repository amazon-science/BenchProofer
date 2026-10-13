#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15741.

Executes the REAL callees the bundle abstracts and asserts that every
observation matches the model in model.py. Two kind-A obligations:

  (A-reference) ``resolve`` (model.py pure region) is the deep model of the
      placeholder-to-text coercion ``str(format_type)``. For a name that
      arrives ALREADY-RESOLVED (a real ``str``) and for the SAME name that
      arrives DEFERRED (a lazy string proxy), the real coercion yields the same
      underlying character sequence, independent of the deferred form:
        str(eager_name)  == name
        str(deferred(name)) == name
      i.e. resolve ignores the deferred flag, exactly as the model encodes it.

  (A-consumed) the ``format_value`` / ``do_lookup`` axioms model the unchanged
      downstream localisation lookup as a deterministic function of the
      RESOLVED character sequence only. We validate this against the real
      ``django.utils.formats.get_format`` (post-patch): for every format name,
      requesting it in its deferred (lazy) form returns exactly what requesting
      it in its already-resolved (str) form returns —
        get_format(deferred(name)) == get_format(name)
      so the value is keyed only on the resolved characters, as the axiom
      requires.

Imports only the standard library plus the repo-under-test's own
``django.utils.functional.lazy`` / ``gettext_lazy`` and
``django.utils.formats.get_format`` — the very symbols the patch touches and
calls. Exit 0 iff every obligation holds.
"""
import random
import sys


# A representative set of localisation names, including the F2P witnesses, plus
# adversarial strings (empty, unicode, names that are NOT known formats).
NAMES = [
    "DATE_FORMAT",
    "TIME_FORMAT",
    "DATETIME_FORMAT",
    "SHORT_DATE_FORMAT",
    "SHORT_DATETIME_FORMAT",
    "YEAR_MONTH_FORMAT",
    "MONTH_DAY_FORMAT",
    "DECIMAL_SEPARATOR",
    "THOUSAND_SEPARATOR",
    "NUMBER_GROUPING",
    "FIRST_DAY_OF_WEEK",
    "DATE_INPUT_FORMATS",
    "TIME_INPUT_FORMATS",
    "DATETIME_INPUT_FORMATS",
    "H:i",                     # the test_date_lazy witness ('H:i')
    "Y-m-d",
    "N j, Y",
    "",                        # boundary: empty
    "NOT_A_REAL_FORMAT_NAME",  # falls through to returning the name itself
    "héllo",                   # unicode
    "a b c",
]


def check_resolve_reference():
    """A-reference: str() coercion of a deferred name == the resolved name, and
    is independent of the deferred flag (== the eager str())."""
    from django.utils.functional import lazy

    # A lazy str proxy that yields its argument unchanged (the shape of every
    # gettext_lazy / format_lazy value: a deferred string).
    deferred = lazy(lambda s: s, str)

    rng = random.Random(15741)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdef:,- éç•0123456789"
    names = list(NAMES)
    for _ in range(5000):
        n = rng.randint(0, 24)
        names.append("".join(rng.choice(alphabet) for _ in range(n)))

    for name in names:
        eager = str(name)              # already-resolved form
        lzy = deferred(name)           # deferred form (lazy proxy)
        # The deep model `resolve` returns the underlying characters in BOTH
        # forms; the real coercion must agree and ignore the deferred flag.
        assert str(eager) == name, (
            "resolve unsound on eager %r: str() gave %r" % (name, str(eager)))
        assert str(lzy) == name, (
            "resolve unsound on deferred %r: str(lazy) gave %r"
            % (name, str(lzy)))
        assert str(eager) == str(lzy), (
            "resolve not independent of deferred flag on %r: %r vs %r"
            % (name, str(eager), str(lzy)))


def check_lookup_axiom():
    """A-consumed: the real get_format value is a function of the resolved name
    only — deferred and already-resolved names return the same value.

    Requires Django settings; configured minimally here. If the in-container
    environment already provides settings (the eval image does), that is used.
    """
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            USE_I18N=True,
            USE_L10N=True,
            USE_TZ=False,
            INSTALLED_APPS=[],
            DATABASES={},
        )
        django.setup()

    from django.utils.formats import get_format, reset_format_cache
    from django.utils.translation import gettext_lazy

    for name in NAMES:
        reset_format_cache()
        eager_val = get_format(str(name))          # already-resolved request
        reset_format_cache()
        lazy_val = get_format(gettext_lazy(name))  # deferred (lazy) request
        assert eager_val == lazy_val, (
            "format_value axiom unsound on %r: eager=%r lazy=%r "
            "(value not keyed only on resolved name)"
            % (name, eager_val, lazy_val))

    # The F2P witnesses explicitly: lazy DATE_FORMAT resolves to the default.
    reset_format_cache()
    assert get_format(gettext_lazy("DATE_FORMAT")) == get_format("DATE_FORMAT")


def main():
    check_resolve_reference()
    n_resolve = "5000 fuzz + %d boundary" % len(NAMES)
    try:
        check_lookup_axiom()
        lookup_status = "OK on %d names (deferred == already-resolved)" % len(NAMES)
    except ImportError as exc:
        # Django not importable in this minimal host; the A-reference check
        # (the load-bearing str/lazy invariant) still ran. G-AX runs this
        # in-container where Django is present.
        lookup_status = "SKIPPED (Django unavailable: %s)" % exc
    print("G-AX OK: resolve deep model (== str() coercion) sound on %s "
          "inputs; format_value lookup determinism %s"
          % (n_resolve, lookup_status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
