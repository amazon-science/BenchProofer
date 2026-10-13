#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16612 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped.  The @Pure helpers
(``ends_with_slash`` / ``slash_part`` / ``query_part`` / ``redirect_target``)
copy over as plain functions on top of a small immutable-tuple PSeq shim; they
are contract-side but serve here as an internal cross-check of the shadow.
There are no @ContractOnly callees in this bundle (the axioms region is
empty).

ORACLE: the REAL patched repo construction the model models per mapping.md —
the redirect target built by ``AdminSite.catch_all_view`` (the ``Location``
header of the permanent redirect it returns), which the patched code obtains
from ``HttpRequest.get_full_path(force_append_slash=True)`` /
``HttpRequest._get_full_path``.  The gate applies patch.diff to /testbed
before this script runs, so both call sites are the patched code.  Two oracle
levels are diffed against the shadow on every input:

  (1) ``request.get_full_path(force_append_slash=True)`` — the full-path
      construction the deep model ``redirect_target`` models directly;
  (2) the ``Location`` header of the response returned by the real
      ``AdminSite.catch_all_view`` (reached via a minimal configured settings
      + catch-all URLconf), i.e. the modeled changed behaviour end-to-end.

Type bridge (mapping.md section 2): locations and query components are
``str`` in the repo and ``List[int]`` of Unicode code points in the model;
the bridge is ``ord``/``chr`` per character.  The R-refinement (mapping.md
section 3, audited by axiom_check.py / G-AX) scopes the model to the input
class on which the location/query normalisations are the identity on
character content; the scope guard below reproduces that domain with the REAL
repo normalisation functions, so out-of-class inputs are skipped (they are
outside the declared refinement domain) and do not count toward the total.

>= 1e5 domain-satisfying inputs: boundary cases (slash-terminated and
slash-less locations, empty location, empty and non-empty queries, separator
characters inside the query) + randomized fuzz over the identity-class
alphabets, generated until the compared count reaches the target.  Pinned
fuzz seed: 166120.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib only.
"""
import json
import random
import string
import sys
import types

SEED = 166120
TARGET = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def ends_with_slash(s):
    return len(s) > 0 and s[len(s) - 1] == 47


def slash_part(path):
    if ends_with_slash(path):
        return PSeq(47).take(0)
    return PSeq(47)


def query_part(query):
    if len(query) == 0:
        return PSeq(63).take(0)
    return PSeq(63) + query


def redirect_target(path, query):
    return path + slash_part(path) + query_part(query)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def build_append_slash_redirect(path, query):
    result = []
    m = len(path)
    n = len(query)
    i = 0
    while i < m:
        result = result + [path[i]]
        i = i + 1
    if not (m > 0 and path[m - 1] == 47):
        result = result + [47]
    if n > 0:
        result = result + [63]
        j = 0
        while j < n:
            result = result + [query[j]]
            j = j + 1
    return result


# --- oracle: the real patched repo construction --------------------------------

def setup_oracle():
    """Configure a minimal Django settings module plus a catch-all URLconf so
    the real ``AdminSite.catch_all_view`` can be driven directly, and return
    the pieces the differential driver needs."""
    from django.conf import settings

    urls_mod = types.ModuleType("gconf_urls")

    def _view(request, *args, **kwargs):
        return None

    # the branch under test only fires for endpoints that opt in (the default)
    _view.should_append_slash = True
    settings.configure(
        DEBUG=False,
        APPEND_SLASH=True,
        ROOT_URLCONF=urls_mod,
        ALLOWED_HOSTS=["*"],
        USE_TZ=False,
    )
    from django.urls import re_path
    urls_mod.urlpatterns = [re_path(r"^.*$", _view)]

    from django.contrib.admin.sites import AdminSite
    from django.http import HttpRequest
    from django.utils.encoding import escape_uri_path, iri_to_uri

    return AdminSite(), HttpRequest, escape_uri_path, iri_to_uri


def check(site, HttpRequest, escape_uri_path, iri_to_uri, path_s, query_s):
    """Run shadow and both real-oracle levels on one (location, query) pair.
    Returns None if skipped (outside the declared refinement domain), True if
    compared and agreeing, or an error string on disagreement."""
    # scope guard: the R-refinement domain — the REAL repo normalisations are
    # the identity on character content (mapping.md sections 2-3, G-AX).
    if escape_uri_path(path_s) != path_s or iri_to_uri(query_s) != query_s:
        return None

    # bridge: str -> List[int] of code points
    path_l = [ord(ch) for ch in path_s]
    query_l = [ord(ch) for ch in query_s]
    shadow_l = build_append_slash_redirect(path_l, query_l)
    shadow = "".join(chr(c) for c in shadow_l)

    # internal cross-check: the executable impl agrees with the pure deep model
    if ToSeq(shadow_l) != redirect_target(ToSeq(path_l), ToSeq(query_l)):
        return ("INTERNAL: impl region and pure deep model disagree on "
                "path=%r query=%r" % (path_s, query_s))

    # oracle level 1: the real full-path construction the deep model models
    req = HttpRequest()
    req.path = path_s
    req.path_info = path_s
    req.META["QUERY_STRING"] = query_s
    real_full = req.get_full_path(force_append_slash=True)
    if shadow != real_full:
        return ("DISAGREEMENT on path=%r query=%r:\n"
                "  shadow (impl region)                       = %r\n"
                "  real get_full_path(force_append_slash=True) = %r"
                % (path_s, query_s, shadow, real_full))

    # oracle level 2: the modeled changed behaviour end-to-end — the Location
    # header of the permanent redirect the real catch_all_view returns.  The
    # root resolver only accepts locations starting with "/" (or empty, which
    # resolves as "/"); other shapes stay on oracle level 1 alone.
    if path_s == "" or path_s.startswith("/"):
        resp = site.catch_all_view(req, "x")
        if resp.status_code != 301:
            return ("DISAGREEMENT on path=%r query=%r: expected a permanent "
                    "redirect, got status %r" % (path_s, query_s,
                                                 resp.status_code))
        real_loc = resp["Location"]
        if shadow != real_loc:
            return ("DISAGREEMENT on path=%r query=%r:\n"
                    "  shadow (impl region)              = %r\n"
                    "  real catch_all_view Location      = %r"
                    % (path_s, query_s, shadow, real_loc))
    return True


def boundary_cases():
    paths = [
        "",                                   # empty location
        "/",                                  # bare slash-terminated location
        "/a",
        "/admin",
        "/admin/",                            # already slash-terminated
        "/admin/auth/foo",
        "/admin/auth/foo/",                   # already slash-terminated
        "/test_admin/admin/admin_views/article",
        "/prefix/admin/admin_views/article",
        "//double",                           # doubled separator
        "/ends//",
        "/mix:ed@chars+(!)~",                 # location-safe punctuation
        "no-leading-slash",                   # level-1 oracle only
    ]
    queries = [
        "",                                   # no query -> slash only
        "id=1",
        "id=123",
        "a=b",
        "a=b&c=d",
        "page=2&sort=name",
        "x=1&y=2&z=3",
        "=",
        "&",
        "&&==",
        "?",                                  # query-safe "?" inside the query
        "??double",
        "a=/slash/in/query",
        "a=:@;$&()+,!*'~",                    # query-safe punctuation
        "%41",                                # "%" is query-safe verbatim
        "#frag=like",
        "[]=brackets",
    ]
    return [(p, q) for p in paths for q in queries]


def main():
    site, HttpRequest, escape_uri_path, iri_to_uri = setup_oracle()

    checked = 0
    skipped = 0
    n_boundary = 0
    for path_s, query_s in boundary_cases():
        r = check(site, HttpRequest, escape_uri_path, iri_to_uri,
                  path_s, query_s)
        if r is None:
            skipped += 1
            continue
        if r is not True:
            print(r)
            return 1
        checked += 1
        n_boundary += 1

    # randomized fuzz over the identity-class alphabets (plus a sprinkle of
    # out-of-class characters that the scope guard filters), pinned seed;
    # generate until the compared count reaches the target.
    rng = random.Random(SEED)
    alnum = string.ascii_letters + string.digits
    path_alphabet = alnum + "/:@&+$,-_.!~*'()" + "/" * 6
    query_alphabet = alnum + "/#%[]=:;$&()+,!?*@'~-_." + "=&" * 4
    out_of_class = " \t\u00e9\u2022^{}<>\"\\"
    while checked < TARGET + n_boundary:
        plen = rng.randint(0, 14)
        qlen = rng.randint(0, 14)
        path_s = "/" + "".join(rng.choice(path_alphabet) for _ in range(plen))
        query_s = "".join(rng.choice(query_alphabet) for _ in range(qlen))
        if rng.random() < 0.01:
            # occasionally inject an out-of-class character: the scope guard
            # must classify it as outside the refinement domain and skip it
            k = rng.randrange(0, len(path_s) + 1)
            path_s = path_s[:k] + rng.choice(out_of_class) + path_s[k:]
        if rng.random() < 0.01:
            k = rng.randrange(0, len(query_s) + 1)
            query_s = query_s[:k] + rng.choice(out_of_class) + query_s[k:]
        r = check(site, HttpRequest, escape_uri_path, iri_to_uri,
                  path_s, query_s)
        if r is None:
            skipped += 1
            continue
        if r is not True:
            print(r)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched redirect-target "
          "construction (get_full_path(force_append_slash=True) AND the "
          "catch_all_view Location header) on %d inputs (%d boundary + fuzz, "
          "seed %d, %d out-of-domain skipped); 0 disagreements."
          % (checked, n_boundary, SEED, skipped))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "skipped_out_of_domain": skipped,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
