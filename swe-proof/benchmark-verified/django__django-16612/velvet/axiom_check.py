#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16612.

Validates the single kind-A construct of this bundle:

  (A-reference) the deep model `redirectTarget` (Solution.lean pure region) ==
      the REAL unchanged callee `HttpRequest.get_full_path(force_append_slash=
      True)`. The changed redirect destination is modeled DEEPLY (no consumed
      axiom); G-AX validates that deep model against the real callee.

`redirectTarget(encodedPath, encodedQuery)` assembles, per mapping.md §3.1:

    encodedPath
      ++ ("" if encodedPath ends in "/" else "/")
      ++ ("" if encodedQuery == "" else "?" + encodedQuery)

where `encodedPath = escape_uri_path(path)` and
`encodedQuery = iri_to_uri(QUERY_STRING)` are the outputs of the two unchanged
percent-encoders (refined into the input carrier, mapping.md §2). We therefore
assert, over boundary + fuzzed (path, query) pairs:

    redirectTarget(escape_uri_path(path), iri_to_uri(qs))
        == request.get_full_path(force_append_slash=True)

with a real `HttpRequest` whose `.path == path` and
`.META["QUERY_STRING"] == qs`. Imports only `django` (the repo under test) and
stdlib. Exit 0 iff every obligation holds.
"""
import os
import random
import sys


def _configure_django():
    """Minimal settings so `django.http`/`django.utils.encoding` import."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_X_FORWARDED_HOST=False,
            ALLOWED_HOSTS=["*"],
            DEFAULT_CHARSET="utf-8",
        )
    django.setup()


# --- Solution.lean redirectTarget deep model, transliterated -----------------
def redirect_target(encoded_path, encoded_query):
    """Reference implementation of Solution.lean `redirectTarget`, over the
    str carrier (encoded_path / encoded_query are already-encoded strings)."""
    slash = "" if encoded_path.endswith("/") else "/"
    query = "" if encoded_query == "" else "?" + encoded_query
    return encoded_path + slash + query


# --- the check ---------------------------------------------------------------
def make_request(path, qs):
    from django.http import HttpRequest
    r = HttpRequest()
    r.path = path
    r.META["QUERY_STRING"] = qs
    return r


def check_reference(path, qs):
    """Assert the deep model == the REAL get_full_path(force_append_slash=True)."""
    from django.utils.encoding import escape_uri_path, iri_to_uri
    req = make_request(path, qs)
    observed = req.get_full_path(force_append_slash=True)          # real callee
    encoded_path = escape_uri_path(path)                            # real encoder
    encoded_query = iri_to_uri(qs) if qs else ""                    # real encoder
    expected = redirect_target(encoded_path, encoded_query)         # deep model
    assert observed == expected, (
        "redirectTarget deep model unsound on path=%r qs=%r: "
        "get_full_path gave %r, deep model gives %r"
        % (path, qs, observed, expected))


def main():
    _configure_django()

    # --- boundary cases ------------------------------------------------------
    paths = [
        "",
        "/admin/auth/foo",
        "/admin/auth/foo/",            # already ends in slash
        "/admin/auth/article",
        "/prefix/admin/auth/article",
        "/a b/c",                      # space -> %20 in path
        "/I ♥ Django/",                # non-ASCII path, trailing slash
        "/x/",
        "/x",
        "/",                           # bare root, already slash
    ]
    queries = [
        "",                            # no query string -> no suffix
        "id=1",
        "id=123",
        "id=1&x=2",
        "q=a b",                       # space in query
        "q=I ♥ Django",                # non-ASCII query
        "a=1&a=2&b=3",
        "next=/test_admin/admin/admin_views/article",
        "f=%3D&g=~",
        "empty=",
    ]
    boundary = [(p, q) for p in paths for q in queries]
    for p, q in boundary:
        check_reference(p, q)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(16612)
    path_alphabet = list("abcXYZ0/9 -_.~!*'()&+$,:@é♥") + ["/"]
    qs_alphabet = list("abcXYZ0/9 -_.~=&?#%é♥+;")
    for _ in range(20000):
        np = rng.randint(0, 20)
        nq = rng.randint(0, 20)
        path = "/" + "".join(rng.choice(path_alphabet) for _ in range(np))
        # query string is sometimes empty (exercises the no-suffix branch)
        qs = "" if rng.random() < 0.2 else "".join(
            rng.choice(qs_alphabet) for _ in range(nq))
        check_reference(path, qs)

    print("G-AX OK: redirectTarget deep model (== real "
          "get_full_path(force_append_slash=True)) sound on %d boundary + "
          "20000 fuzz (path, query) pairs." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
