#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14404 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with no contract
calls to strip (all Requires/Ensures/Exsures live in the pre/post regions;
the impl region itself is plain Python). The user-defined `NotFound`
exception class is copied over, and the @Pure helper `with_trailing_slash`
is copied as a plain function over tuples (PSeq -> tuple shim); the impl
does not call it, it is exercised only as a cross-check of the shadow's own
output shape. There are no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md --
`AdminSite.catch_all_view(self, request, url)` in
django/contrib/admin/sites.py. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched code
importable. The callee reads exactly: settings.APPEND_SLASH, the `url`
argument's trailing-slash state, `request.urlconf` / `request.path_info`
(fed to URL resolution), `request.path` (the redirect-target base), and the
resolved view's `should_append_slash` attribute. A minimal request object
carrying `path`, `path_info`, and `urlconf` attributes is therefore a
faithful driver: the callee's contract with the request is exactly those
three attribute reads.

BRIDGE (mapping.md section 2):
  * List[int] code points <-> str via chr/ord; code point 47 <-> '/'.
  * append_slash_enabled <-> settings.APPEND_SLASH (set per case).
  * url_has_trailing_slash <-> whether the passed `url` ends with '/'
    (per case we build a `url` realizing exactly the intended boolean).
  * slash_form_resolves <-> the resolution outcome of the slash-terminated
    application-relative path against `request.urlconf`. Realized exactly
    by the choice of urlconf module: a catch-all pattern (matches every
    path, DOTALL so any code point is fine) vs. an empty pattern list
    (never matches). `path_info` is generated starting with '/' (as the
    WSGI layer guarantees), so the catch-all really does always match and
    the boolean is realized exactly as intended.
  * target_view_opts_in <-> the matched view's `should_append_slash`
    attribute (default True; a second catch-all urlconf routes to a view
    with the attribute set False, which is what the opt-out decorator
    does).
  * Redirect return <-> a permanent-redirect response; the model's
    Result() is the constructor's Location argument. The response encodes
    its Location header through an IRI-to-URI step, which is the IDENTITY
    on the unreserved-ASCII + '/' alphabet used here (and ':' is excluded
    so no input can parse as carrying a URL scheme, which the redirect
    class would reject). On this domain response.url IS the raw target
    string, so the shadow's code-point list is compared against
    [ord(c) for c in response.url], plus a 301 status check.
  * NotFound raise <-> Http404 raise.

Input domain: the model Requires only read access to the two code-point
lists; the realizable oracle domain used here is paths over the
URL-safe alphabet above, with `app_relative_path` starting with '/' (the
invariant the WSGI request layer establishes) and all four booleans free.
Path pairs are drawn both WSGI-correlated (full path = prefix + stripped
tail, exactly as the request object builds it -- including the deployment-
prefix regime where the two paths differ) and fully independent (any pair
is realizable at the callee boundary since the attributes are independent
reads).

>= 1e5 Requires-satisfying inputs: 16 boolean combos x boundary path pairs
x url variants, plus 100000 fuzz cases. Pinned fuzz seed: 14404.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import sys
import types

SEED = 14404
N_FUZZ = 100_000

ALPHABET = ("abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789-._~")


# --- model.py shadow -----------------------------------------------------


class NotFound(Exception):
    """The fall-through "no routable target" signal (a not-found result)."""


def with_trailing_slash(p):
    """@Pure helper from model.py, decorator stripped; PSeq -> tuple shim
    (PSeq concatenation becomes tuple concatenation)."""
    return tuple(p) + (47,)


def slash_redirect_target(
        full_path,
        app_relative_path,
        append_slash_enabled,
        url_has_trailing_slash,
        slash_form_resolves,
        target_view_opts_in):
    # impl region of model.py, verbatim (contract calls all live outside it)
    if append_slash_enabled and not url_has_trailing_slash:
        if slash_form_resolves:
            if target_view_opts_in:
                result = list(full_path)  # type: List[int]
                result.append(47)
                return result
    raise NotFound()


# --- oracle plumbing ------------------------------------------------------


def make_urlconfs():
    """Three urlconf modules realizing the (resolves, opts-in) regimes:
      * catch-all -> view with the default (True) opt-in attribute
      * catch-all -> view whose opt-in attribute is False
      * empty pattern list -> never resolves
    DOTALL on the catch-all so every code point (incl. newline, were it ever
    generated) matches; the leading '/' of the resolved path is consumed by
    the root resolver."""
    from django.urls import re_path

    def opted_in_view(request):
        return None

    def opted_out_view(request):
        return None
    opted_out_view.should_append_slash = False

    def mod(mod_name, patterns):
        m = types.ModuleType(mod_name)
        m.urlpatterns = patterns
        return m

    return (
        mod("conf_urlconf_optin", [re_path(r"(?s)^.*$", opted_in_view)]),
        mod("conf_urlconf_optout", [re_path(r"(?s)^.*$", opted_out_view)]),
        mod("conf_urlconf_empty", []),
    )


def make_url(rng_base, trailing):
    """A `url` argument realizing exactly the intended trailing-slash
    boolean (the callee only reads url.endswith('/'))."""
    base = rng_base.rstrip("/")
    if trailing:
        return base + "/"
    return base  # '' or a non-'/'-terminated string: endswith('/') is False


def check_case(site, settings, urlconfs, Http404,
               full_path, app_relative_path,
               append_slash_enabled, url_has_trailing_slash,
               slash_form_resolves, target_view_opts_in, url):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    optin, optout, empty = urlconfs

    # shadow over code points
    fp_codes = [ord(c) for c in full_path]
    ap_codes = [ord(c) for c in app_relative_path]
    try:
        shadow_out = slash_redirect_target(
            fp_codes, ap_codes, append_slash_enabled,
            url_has_trailing_slash, slash_form_resolves,
            target_view_opts_in)
        shadow_raised = False
    except NotFound:
        shadow_out = None
        shadow_raised = True

    # oracle: the real patched callee
    settings.APPEND_SLASH = append_slash_enabled
    if slash_form_resolves:
        urlconf = optin if target_view_opts_in else optout
    else:
        urlconf = empty
    request = types.SimpleNamespace(
        path=full_path, path_info=app_relative_path, urlconf=urlconf)
    try:
        response = site.catch_all_view(request, url)
        real_raised = False
    except Http404:
        response = None
        real_raised = True

    ctx = ("full_path=%r app_relative_path=%r append_slash=%r "
           "url_trailing=%r resolves=%r opts_in=%r url=%r"
           % (full_path, app_relative_path, append_slash_enabled,
              url_has_trailing_slash, slash_form_resolves,
              target_view_opts_in, url))

    if shadow_raised != real_raised:
        return ("DISAGREEMENT (raise vs return)\n  %s\n  shadow=%s\n  real=%s"
                % (ctx,
                   "NotFound raised" if shadow_raised else repr(shadow_out),
                   "Http404 raised" if real_raised
                   else repr(getattr(response, "url", response))))
    if shadow_raised:
        return None

    # sanity: the pure helper agrees with the impl's output shape
    if tuple(shadow_out) != with_trailing_slash(fp_codes):
        return ("SHADOW-INTERNAL disagreement (impl vs pure helper)\n  %s\n"
                "  impl=%r helper=%r"
                % (ctx, shadow_out, with_trailing_slash(fp_codes)))

    real_target = response.url  # identity encoding on this alphabet
    real_codes = [ord(c) for c in real_target]
    if shadow_out != real_codes or response.status_code != 301:
        return ("DISAGREEMENT (redirect target)\n  %s\n"
                "  shadow=%r (%r)\n  real=%r (%r) status=%r"
                % (ctx, shadow_out, "".join(chr(c) for c in shadow_out),
                   real_codes, real_target, response.status_code))
    return None


# --- input generation -----------------------------------------------------


def wsgi_pair(script_name, raw_path_info):
    """The request object's own construction of the two paths from the WSGI
    environ values (unchanged by this instance): the full path re-attaches
    the deployment prefix in front of the stripped path's tail."""
    path_info = raw_path_info or "/"
    path = "%s/%s" % (script_name.rstrip("/"), path_info.replace("/", "", 1))
    return path, path_info


def boundary_path_pairs():
    pairs = []
    wsgi_cases = [
        ("", "/admin/articles"),
        ("", "/admin/articles/x"),
        ("", ""),                          # empty PATH_INFO -> '/'
        ("/prefix/", "/admin/articles"),   # deployment-prefix regime
        ("/prefix", "/admin/articles"),
        ("/deep/nested/prefix/", "/x"),
        ("/p", "/"),
        ("/prefix/", ""),
        ("/Prefix-With.Dots_123/", "/a/b/c"),
    ]
    for sn, raw in wsgi_cases:
        pairs.append(wsgi_pair(sn, raw))
    # independent pairs (any attribute pair is realizable at the callee)
    pairs += [
        ("", "/"),
        ("/", "/"),
        ("/a", "/totally/unrelated"),
        ("/x/y/z", "/"),
        ("/already/slashed/", "/also/slashed/"),
        ("/~tilde-._segment", "/q"),
    ]
    return pairs


def rand_segment(rng, lo=0, hi=8):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(lo, hi)))


def rand_path(rng, force_leading_slash):
    n = rng.randint(0, 4)
    p = "/".join(rand_segment(rng) for _ in range(n))
    if force_leading_slash or (p and rng.random() < 0.8):
        p = "/" + p
    if rng.random() < 0.3:
        p += "/"
    if force_leading_slash and not p.startswith("/"):
        p = "/" + p
    return p


def fuzz_case(rng):
    if rng.random() < 0.6:
        # WSGI-correlated pair, prefix present ~2/3 of the time
        if rng.random() < 0.35:
            script_name = ""
        else:
            script_name = "/" + "/".join(
                rand_segment(rng, 1, 6)
                for _ in range(rng.randint(1, 3)))
            if rng.random() < 0.5:
                script_name += "/"
        raw = rand_path(rng, force_leading_slash=True) \
            if rng.random() < 0.9 else rng.choice(["", "/"])
        full_path, app_relative_path = wsgi_pair(script_name, raw)
    else:
        # independent pair
        full_path = rand_path(rng, force_leading_slash=False)
        app_relative_path = rand_path(rng, force_leading_slash=True)
    bools = [rng.random() < 0.5 for _ in range(4)]
    url = make_url(rand_segment(rng, 0, 10), bools[1])
    return (full_path, app_relative_path,
            bools[0], bools[1], bools[2], bools[3], url)


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            ALLOWED_HOSTS=["*"],
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            ROOT_URLCONF=None,
        )
        django.setup()
    from django.contrib.admin.sites import AdminSite
    from django.http import Http404

    site = AdminSite()
    urlconfs = make_urlconfs()

    cases = 0

    def run_one(args):
        nonlocal cases
        cases += 1
        err = check_case(site, settings, urlconfs, Http404, *args)
        if err is not None:
            print(err)
            sys.exit(1)

    # --- boundary grid: every boolean combo x path pairs x url variants ---
    bool_combos = [(a, t, r, o)
                   for a in (False, True) for t in (False, True)
                   for r in (False, True) for o in (False, True)]
    for full_path, app_relative_path in boundary_path_pairs():
        for a, t, r, o in bool_combos:
            for base in ("", "seg", "a/b"):
                url = make_url(base, t)
                run_one((full_path, app_relative_path, a, t, r, o, url))

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        run_one(fuzz_case(rng))

    print("G-CONF OK: shadow == real callee on %d cases (0 disagreements), "
          "seed=%d" % (cases, SEED))
    print('{"cases": %d, "disagreements": 0, "seed": %d}' % (cases, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
