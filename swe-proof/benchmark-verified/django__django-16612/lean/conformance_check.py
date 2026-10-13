#!/usr/bin/env python3
"""G-CONF for django__django-16612.

The gold patch is already applied to /testbed when this runs. We compare the
R/I + A-reference Python shadow of `implementation_redirectTargetWithTrailingSlash`
(the Lean impl, transliterated op-for-op per refinement.md) against the REAL
patched redirect-target construction, over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

The patch swaps the admin catch-all redirect target from `"%s/" % request.path`
to `request.get_full_path(force_append_slash=True)`. The modeled unit is that
target-construction expression, unfolded through `HttpRequest._get_full_path`:

    escape_uri_path(path)
      + ("/" if not path.endswith("/") else "")        # force_append_slash=True
      + ("?" + iri_to_uri(query_string)) if query_string else ""

  * ORACLE = the REAL patched `HttpRequest.get_full_path(force_append_slash=True)`
             on an HttpRequest with the fuzzed path + QUERY_STRING. This is
             exactly the callee the post-patch `catch_all_view` invokes.
  * SHADOW = escapePathComponent(path) + slash + querySuffix, the op-for-op
             transliteration of the Lean impl, with the A-reference leaves
             escapePathComponent / encodeQueryString left as the REAL repo
             callees `escape_uri_path` / `iri_to_uri`.

Type bijection (mapping.md): path<->request.path (str), queryString<->
request.META["QUERY_STRING"] (str), result<->the redirect-target str.
stdlib-only; no hypothesis required. Pinned seed: 16612 (also in mapping.md).
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={},
        INSTALLED_APPS=[],
        ALLOWED_HOSTS=["*"],
    )
    django.setup()

from django.http import HttpRequest
from django.utils.encoding import escape_uri_path, iri_to_uri


def oracle(path: str, query_string: str) -> str:
    """The REAL patched target: request.get_full_path(force_append_slash=True)."""
    req = HttpRequest()
    req.path = path
    req.META["QUERY_STRING"] = query_string
    return req.get_full_path(force_append_slash=True)


def shadow(path: str, query_string: str) -> str:
    """Op-for-op transliteration of implementation_redirectTargetWithTrailingSlash.
    A-reference leaves use the REAL repo callees."""
    escaped_path = escape_uri_path(path)                       # op #1 (A-reference)
    trailing_slash = "" if path.endswith("/") else "/"         # op #2 (R/I)
    query_suffix = "" if query_string == "" else "?" + iri_to_uri(query_string)  # op #3
    return escaped_path + trailing_slash + query_suffix        # op #4 (I)


def make_path(rng: random.Random) -> str:
    pieces = []
    n = rng.randint(0, 4)
    pool = [
        "admin", "auth", "foo", "bar", "article", "user",
        "a b", "café", "x%y", "p#q", "with space", "ü",
        "a/b", "", "123", "MixedCase", "tilde~", "plus+plus",
    ]
    for _ in range(n):
        pieces.append(rng.choice(pool))
    path = "/" + "/".join(p for p in pieces if p != "")
    # randomly make it already-slash-terminated
    if rng.random() < 0.35:
        path = path + "/"
    return path


def make_query(rng: random.Random) -> str:
    r = rng.random()
    if r < 0.30:
        return ""                       # the "no query string" branch
    pool = [
        "id=1", "id=123", "a=1&b=2", "q=hello+world", "next=/admin/",
        "x=a b", "u=café", "k=%41", "empty=", "f=a&f=b&f=c",
        "weird=#frag", "key=val/ue", "uni=üñ",
    ]
    k = rng.randint(1, 3)
    return "&".join(rng.choice(pool) for _ in range(k))


def main() -> int:
    rng = random.Random(16612)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        path = make_path(rng)
        qs = make_query(rng)
        o = oracle(path, qs)
        s = shadow(path, qs)
        if o != s:
            disagreements += 1
            if first is None:
                first = (path, qs, o, s)
    if disagreements:
        print(f"G-CONF FAIL: {disagreements}/{N} disagreements; first={first!r}")
        return 1
    print(f"G-CONF OK: {N} inputs, 0 disagreements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
