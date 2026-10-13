#!/usr/bin/env python3
"""G-AX / refinement soundness check for django__django-16612.

This bundle has NO consumed @ContractOnly axioms: the redirect-target
construction is modelled DEEPLY (the pure `redirect_target` fold over code
points). What must be audited is the single R-refinement claim the bundle
makes (mapping.md / refinement.md):

  For the location and query character classes exercised by the targeted
  behaviour, the real slash-completing full-path construction
  `_get_full_path(path, force_append_slash=True)` produces, on character
  content, EXACTLY the deep concatenation modelled here:

        target = path + ("/" if not path.endswith("/") else "")
                      + ("?" + query if query else "")

  i.e. (a) the location's percent/IRI normalisation is the identity, (b) the
  query characters are reproduced verbatim, introduced by "?", and (c) the
  query is dropped iff it is empty.

We reproduce the REAL stdlib transforms the construction relies on
(`urllib.parse.quote` with Django's exact `safe=` sets, which is what
`django.utils.encoding.escape_uri_path` / `iri_to_uri` call) and assert the
constructed target equals the deep model. Boundary cases over the tested
classes (admin paths, ASCII query strings) plus randomized ASCII fuzz.

stdlib-only imports. Exit 0 iff every observation matches the deep model.
"""
import random
import sys
from urllib.parse import quote


# --- real transforms (verbatim from django/utils/encoding.py @ base_commit) --
def escape_uri_path(path):
    # django.utils.encoding.escape_uri_path
    return quote(path, safe="/:@&+$,-_.!~*'()")


def iri_to_uri(iri):
    # django.utils.encoding.iri_to_uri (non-Promise string branch)
    return quote(iri, safe="/#%[]=:;$&()+,!?*@'~")


def real_get_full_path(path, query_string):
    # django.http.request.HttpRequest._get_full_path(path, force_append_slash=True)
    return "%s%s%s" % (
        escape_uri_path(path),
        "/" if not path.endswith("/") else "",
        ("?" + iri_to_uri(query_string)) if query_string else "",
    )


# --- the deep model (model.py redirect_target, on str) -----------------------
def deep_model(path, query_string):
    target = path
    if not path.endswith("/"):
        target += "/"
    if query_string:
        target += "?" + query_string
    return target


def check(path, query_string):
    """Assert real construction == deep model, AND the discriminating
    query-preservation property. Only over inputs whose location/query are in
    the identity-transform class (the tested classes); the R-refinement is
    scoped to exactly those (mapping.md)."""
    # scope guard: only audit inputs where normalisation is the identity
    if escape_uri_path(path) != path or iri_to_uri(query_string) != query_string:
        return  # outside the declared R-refinement domain
    real = real_get_full_path(path, query_string)
    model = deep_model(path, query_string)
    assert real == model, (
        "deep model != real construction: path=%r q=%r real=%r model=%r"
        % (path, query_string, real, model)
    )
    # discriminating property: a non-empty query is preserved verbatim at the
    # tail (the pre-patch bug dropped it).
    if query_string:
        assert real.endswith("?" + query_string), (
            "query dropped/mangled: %r -> %r" % (query_string, real)
        )
    else:
        assert "?" not in real or "?" in path


def main():
    # Boundary cases over the tested classes (admin endpoints + ASCII queries).
    paths = [
        "/test_admin/admin/admin_views/article",
        "/prefix/admin/admin_views/article",
        "/admin/auth/foo",
        "/a",
        "/admin/",            # already ends with slash
        "/admin/x/",          # already ends with slash
        "",                   # empty location
    ]
    queries = [
        "",                   # no query  -> slash only
        "id=1",
        "id=123",
        "a=b",
        "a=b&c=d",
        "page=2&sort=name",
        "q=hello",
        "x=1&y=2&z=3",
    ]
    for p in paths:
        for q in queries:
            check(p, q)

    # Randomized ASCII fuzz over the identity-transform class.
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~/=&"
    rng = random.Random(20230302)
    for _ in range(20000):
        plen = rng.randint(0, 12)
        qlen = rng.randint(0, 12)
        path = "/" + "".join(rng.choice(safe_chars) for _ in range(plen))
        query = "".join(rng.choice(safe_chars) for _ in range(qlen))
        check(path, query)

    print("OK: deep redirect-target model == real construction on all "
          "boundary + fuzz inputs in the declared R-refinement domain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
