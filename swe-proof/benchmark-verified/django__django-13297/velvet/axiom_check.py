#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13297.

This bundle has NO consumed axiom and NO deep-model reference: the change is a
callee-swap of the deferred-value constructor, and the distinguishing behaviour
is modeled DIRECTLY in Solution.lean by `Wrapper.reported` + `coerce`
(refinement.md §C). G-AX therefore validates the *type-dispatch facts that
direct model depends on* by executing the REAL Django objects in-container:

  (1) PRE-patch wrapper  — `SimpleLazyObject(access_value)` — masquerades as the
      wrapped value's runtime type: `isinstance(pre, type(value))` is True. This
      is the model's `reported = some v.tag` (a `coerce` PASSTHROUGH).
  (2) POST-patch wrapper — `lazy(access_value, type(value))()` — does NOT:
      `isinstance(post, type(value))` is False (it is a distinct `__proxy__`
      type). This is the model's `reported = none` (a `coerce` GENUINE).
  (3) A type-dispatching consumer (`CharField.to_python`, whose guard is
      `if isinstance(value, str) or value is None: return value`) returns the
      PRE wrapper UNCHANGED (a non-genuine value, `type(...) is not str`) but
      coerces the POST wrapper to a GENUINE `str` equal to the original value.
      This is exactly `coerce (deferOne v) v.tag = genuine v` (post) vs
      `passthrough` (pre).

Imports only `django` (the module under change) + the standard library. The
boundary + fuzz inputs cover empty, ascii, unicode, slug-shaped, and
warning-emitting closures. Exit 0 iff every obligation holds.
"""
import random
import sys
import warnings


def _configure_django():
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
        )
    django.setup()


def _make_access_value(value):
    """The closure the changed function binds per entry (base.py:172-181):
    emits the deprecation warning and returns the captured value."""
    from django.utils.deprecation import RemovedInDjango40Warning

    def access_value(value=value):
        warnings.warn("deprecated", RemovedInDjango40Warning, stacklevel=2)
        return value

    return access_value


def check_value(value):
    """Run all three obligations for one wrapped string `value`."""
    from django.utils.functional import lazy, SimpleLazyObject
    from django.db.models.fields import CharField

    av = _make_access_value(value)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        pre = SimpleLazyObject(av)                  # pre-patch wrapper
        post = lazy(av, type(value))()              # post-patch wrapper
        vtype = type(value)                         # the value's runtime type

        # (1) PRE masquerades as the value's runtime type -> reported = some tag
        assert isinstance(pre, vtype), (
            "pre-patch SimpleLazyObject(%r) did NOT masquerade as %s "
            "(model assumes reported = some tag)" % (value, vtype.__name__))

        # (2) POST does NOT masquerade -> reported = none
        assert not isinstance(post, vtype), (
            "post-patch lazy(...,type)() DID masquerade as %s "
            "(model assumes reported = none)" % vtype.__name__)

        # (3) the type-dispatching consumer: PRE passthrough, POST genuine
        f = CharField()
        coerced_pre = f.to_python(pre)
        coerced_post = f.to_python(post)

        assert type(coerced_pre) is not str, (
            "pre-patch wrapper coerced to a GENUINE str on %r (expected the "
            "non-genuine passthrough that crashes the DB bind)" % (value,))
        assert type(coerced_post) is str, (
            "post-patch wrapper did NOT coerce to a genuine str on %r "
            "(model requires coerce = genuine)" % (value,))
        assert coerced_post == value, (
            "post-patch genuine value %r != original %r"
            % (coerced_post, value))


def main():
    _configure_django()

    boundary = [
        "",
        "Rene Magritte",
        "Rene-Magritte",
        "abc",
        "a b/c",
        "0",
        "slug-with-dashes-123",
        "Ünïcödé",
        "•bullet•",
        "Joe's Crab Shack",
        "<script>",
        " leading-and-trailing ",
        "MixedCASE123",
    ]
    for v in boundary:
        check_value(v)

    # randomized fuzz over slug/text-shaped strings
    rng = random.Random(13297)
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789-_ /é•'<>")
    for _ in range(2000):
        n = rng.randint(0, 32)
        v = "".join(rng.choice(alphabet) for _ in range(n))
        check_value(v)

    print("G-AX OK: type-dispatch facts sound on %d boundary + 2000 fuzz "
          "values: pre-patch SimpleLazyObject masquerades (passthrough), "
          "post-patch lazy(...,type)() does not (genuine via CharField."
          "to_python)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
