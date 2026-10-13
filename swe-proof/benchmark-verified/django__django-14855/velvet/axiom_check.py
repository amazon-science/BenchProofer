#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14855.

Validates the ONE consumed axiom of this bundle: `resolveAddress`
(Solution.lean axioms region) models the UNCHANGED address-resolution callee
`django.urls.base.reverse(viewname, args, current_app=...)`. The fix the gold
patch makes is purely to thread `reverse`'s `current_app` argument
(`current_app=self.model_admin.admin_site.name`); `reverse` itself is unchanged.

The axiom claims `resolveAddress` is a function of THREE inputs jointly —
(route name, positional argument, application context) — pinning no concrete
URL. The single load-bearing property the spec relies on, and the one the bug
violated, is that the **application context is a genuine determinant** of the
result: the same route+argument resolved under two different contexts yields two
different addresses. This is exactly Django's instance-namespace mechanism that
`reverse(..., current_app=...)` drives — the same mechanism a custom `AdminSite`
relies on (two sites registering the same app under distinct namespaces).

So G-AX asserts, against the REAL `reverse`, over a real namespaced URL
configuration with two application-instance namespaces (a "default" site and a
"custom" site sharing one application namespace, as admin sites do):

  (A1) determinism — `reverse` is a function of its inputs: the same
       (viewname, args, current_app) always yields the same address.
  (A2) context-sensitivity — for the same (viewname, args), resolving under the
       custom context yields a URL under the custom prefix, and under the
       default context yields one under the default prefix; the two DIFFER. This
       is the property `resolveAddress`'s third argument encodes and the bug
       (resolving with no/ambient context) violated.
  (A3) failure leg — an unregistered route raises `NoReverseMatch`, which the
       `get_admin_url` try/except turns into the modeled `none` outcome.

Imports only `django` (configured in-process) + stdlib. Exit 0 iff sound.
"""
import random
import sys
import types

SEED = 14855


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            ALLOWED_HOSTS=["*"],
            DATABASES={},
            INSTALLED_APPS=[],
            ROOT_URLCONF=None,
        )
    django.setup()


def _dummy_view(request, *args, **kwargs):  # pragma: no cover - never called
    return None


def _build_urlconf():
    """A real namespaced URL configuration with two instance namespaces that
    share one application namespace 'app' — the structure two admin sites form
    (app_name 'admin', distinct site names). Returns a module object suitable as
    `reverse`'s `urlconf` argument (get_resolver caches by it, so it must be
    hashable — a ModuleType is)."""
    from django.urls import include, path

    inner = (
        [path("obj/<path:pk>/", _dummy_view, name="change")],
        "app",  # application namespace shared by both instances
    )
    patterns = [
        # default instance namespace (the ambient "/admin/..." site)
        path("admin/", include(inner, namespace="default_site")),
        # custom instance namespace (the "/custom-admin/..." site)
        path("custom-admin/", include(inner, namespace="custom_site")),
    ]
    mod = types.ModuleType("_axiom_check_urlconf_14855")
    mod.urlpatterns = patterns
    return mod


def main():
    _configure_django()
    from django.urls import NoReverseMatch, reverse

    urlconf = _build_urlconf()
    view = "app:change"

    rng = random.Random(SEED)
    # boundary + fuzz positional arguments (the quoted pk)
    # the `<path:pk>` converter requires a non-empty value (a pk always is one)
    pks = ["1", "0", "42", "abc", "name-with-dash", "%20", "a/b"]
    pks += ["".join(rng.choice("0123456789abcdefABCDEF-_") for _ in range(rng.randint(1, 12)))
            for _ in range(2000)]

    seen = {}
    for pk in pks:
        # (A1) determinism: same (view, pk, current_app) => same address
        a_custom = reverse(view, urlconf=urlconf, args=[pk], current_app="custom_site")
        a_custom2 = reverse(view, urlconf=urlconf, args=[pk], current_app="custom_site")
        assert a_custom == a_custom2, (
            "reverse non-deterministic for pk=%r current_app='custom_site': "
            "%r vs %r" % (pk, a_custom, a_custom2))
        a_default = reverse(view, urlconf=urlconf, args=[pk], current_app="default_site")

        # cross-pk caching sanity: results are pure functions of inputs
        key = ("custom_site", pk)
        if key in seen:
            assert seen[key] == a_custom, (
                "reverse not a function of inputs: pk=%r gave %r then %r"
                % (pk, seen[key], a_custom))
        seen[key] = a_custom

        # (A2) context-sensitivity: the two contexts yield DIFFERENT, correctly
        # prefixed addresses. This is the property resolveAddress's 3rd argument
        # encodes; passing the wrong/ambient context (the bug) gives the wrong
        # URL.
        assert a_custom != a_default, (
            "current_app is NOT a determinant of reverse for pk=%r: both "
            "contexts gave %r — the axiom's context-sensitivity is unsound"
            % (pk, a_custom))
        assert a_custom.startswith("/custom-admin/"), (
            "custom context did not resolve under its own prefix: %r" % a_custom)
        assert a_default.startswith("/admin/"), (
            "default context did not resolve under its own prefix: %r" % a_default)

    # (A3) failure leg: an unregistered route raises NoReverseMatch, which the
    # get_admin_url try/except maps to the modeled `none` outcome.
    raised = False
    try:
        reverse("app:does_not_exist", urlconf=urlconf, args=["1"], current_app="custom_site")
    except NoReverseMatch:
        raised = True
    assert raised, "expected NoReverseMatch for an unregistered route"

    print("G-AX OK: resolveAddress contract sound for the real django reverse — "
          "deterministic, context-sensitive (custom vs default namespace differ "
          "and are correctly prefixed), and NoReverseMatch on an unregistered "
          "route, over %d argument inputs (seed=%d)." % (len(pks), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
