#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14855.

The bundle models ONE function: `AdminReadonlyField.get_admin_url`
(`django/contrib/admin/helpers.py:205-215`), at the fix point. The patch adds the
`current_app=self.model_admin.admin_site.name` keyword to the `reverse(...)` call:

    -    url = reverse(url_name, args=[quote(remote_obj.pk)])
    +    url = reverse(url_name, args=[quote(remote_obj.pk)],
    +                  current_app=self.model_admin.admin_site.name)

so a non-default (custom-named) admin site resolves the change-view URL under its
OWN namespace prefix instead of the default one.

The Lean impl `implementation_getAdminUrl` is the R/I skeleton of that behavior:

    urlName = "admin:" + appLabel + "_" + modelName + "_change"
    match resolveUrl(urlName, arg, some siteName):
      some url -> formatLink(url, remoteObjStr)
      none     -> remoteObjStr

The downstream callees `resolveUrl`/`formatLink` are A-references — here they are
bound to the REAL `reverse` / `format_html`:
  * `resolveUrl name arg (some site)` == `reverse(name, args=[arg],
    current_app=site)`, with `NoReverseMatch` folded into `Option` (`none`).
  * `formatLink url txt` == `format_html('<a href="{}">{}</a>', url, txt)`.

  * ORACLE  — a faithful in-process replica of the POST-PATCH `get_admin_url` at
    the fix point: literal `reverse(url_name, args=[arg],
    current_app=site_name)` inside `try/except NoReverseMatch`, then
    `format_html(...)` / `str(remote_obj)`.
  * SHADOW  — the Lean impl's logic via the type bijection (mapping.md): build the
    route name by concatenation, call the SAME real `reverse` with
    `current_app=site_name`, frame with the SAME real `format_html` or fall back.

Both legs run against a REAL namespaced URLconf carrying a default `admin`
namespace and several custom-named admin-site namespaces, so `reverse` with
`current_app` genuinely yields different prefixes. They must agree on the returned
markup for EVERY input — in particular when `siteName` is a custom site, the
oracle/shadow resolve under that site's prefix (a wrong `current_app=None` would
diverge there: that is the bug the prepatch encodes).

Type bijection (mapping.md): appLabel/modelName/arg/siteName/remoteObjStr <-> the
corresponding str values; resolveUrl <-> reverse (Option <-> NoReverseMatch);
formatLink <-> format_html; result <-> returned markup str.
stdlib-only fuzzing; pinned seed 14855 (also in mapping.md). Exit 0 iff zero
disagreements.
"""
import random
import sys

import django
from django.conf import settings

# A small set of admin-site namespaces: the default "admin" plus custom names.
SITE_NAMES = ["admin", "custom_admin", "namespaced_admin", "admin7", "second_site"]
# (appLabel, modelName) pairs that ARE registered (route exists for each site).
REGISTERED = [
    ("admin_views", "readonlyrelatedfield"),
    ("admin_views", "language"),
    ("auth", "user"),
    ("admin_views", "chapter"),
]


def build_urlconf_module():
    """Construct a real URLconf: each site name is a namespace instance carrying
    `<app>_<model>_change` routes for every REGISTERED (app, model)."""
    import types
    from django.urls import path, include

    def make_view(label):
        def _v(request, *a, **k):
            from django.http import HttpResponse
            return HttpResponse(label)
        return _v

    # Build per-namespace url patterns: one named route per registered model.
    inner = []
    for app, model in REGISTERED:
        name = "%s_%s_change" % (app, model)
        inner.append(path("%s/%s/<path:object_id>/change/" % (app, model),
                           make_view(name), name=name))

    urlpatterns = []
    for site in SITE_NAMES:
        # app_name = "admin", instance namespace = the site name.
        urlpatterns.append(
            path("%s/" % site, include((inner, "admin"), namespace=site))
        )

    mod = types.ModuleType("gconf_urls_14855")
    mod.urlpatterns = urlpatterns
    sys.modules["gconf_urls_14855"] = mod
    return "gconf_urls_14855"


def configure():
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            USE_TZ=False,
            DATABASES={},
            INSTALLED_APPS=[],
            TEMPLATES=[],
            ROOT_URLCONF="gconf_urls_14855",
        )
    build_urlconf_module()
    django.setup()


def oracle(app_label, model_name, arg, site_name, remote_obj_str):
    """Faithful in-process replica of the POST-PATCH get_admin_url."""
    from django.urls import reverse, NoReverseMatch
    from django.utils.html import format_html
    url_name = "admin:%s_%s_change" % (app_label, model_name)
    try:
        url = reverse(url_name, args=[arg], current_app=site_name)
        return format_html('<a href="{}">{}</a>', url, remote_obj_str)
    except NoReverseMatch:
        return str(remote_obj_str)


def shadow(app_label, model_name, arg, site_name, remote_obj_str):
    """R/I transliteration of implementation_getAdminUrl (Lean), with resolveUrl
    bound to the REAL reverse (Option<->NoReverseMatch) and formatLink to the REAL
    format_html."""
    from django.urls import reverse, NoReverseMatch
    from django.utils.html import format_html
    # Op 1: urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
    url_name = "admin:" + app_label + "_" + model_name + "_change"
    # Op 2: resolveUrl urlName arg (some siteName)  -> Option
    try:
        resolved = reverse(url_name, args=[arg], current_app=site_name)
    except NoReverseMatch:
        resolved = None
    # Op 3/4: match on the Option
    if resolved is not None:
        return format_html('<a href="{}">{}</a>', resolved, remote_obj_str)
    else:
        return remote_obj_str


def rand_str(rng):
    n = rng.randint(0, 6)
    alpha = "abcDE0<>&\"' "
    return "".join(rng.choice(alpha) for _ in range(n))


ARG_POOL = ["1", "42", "abc", "no.opinion", "a%2Fb", "Ελληνικά", "x y", "0",
            "100", "café", "a&b", "<id>"]


def main():
    configure()
    rng = random.Random(14855)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        site_name = rng.choice(SITE_NAMES)
        # Mostly registered pairs (route resolves); sometimes a bogus pair that
        # raises NoReverseMatch -> the fallback branch.
        if rng.random() < 0.8:
            app_label, model_name = rng.choice(REGISTERED)
        else:
            app_label = rng.choice(["admin_views", "bogus", "nope"])
            model_name = rng.choice(["missing", "language", "ghost"])
        arg = rng.choice(ARG_POOL) if rng.random() < 0.7 else rand_str(rng)
        remote_obj_str = rng.choice(["super", "Chapter 1", "Fictional", "x"]) \
            if rng.random() < 0.7 else rand_str(rng)
        o = oracle(app_label, model_name, arg, site_name, remote_obj_str)
        s = shadow(app_label, model_name, arg, site_name, remote_obj_str)
        if o != s:
            disagreements += 1
            if first is None:
                first = (app_label, model_name, arg, site_name, remote_obj_str, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
