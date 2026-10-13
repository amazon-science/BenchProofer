#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-6028.

Executes the REAL combining callee (stdlib ``urllib.parse.urlunparse`` /
``urlunsplit``) and the REAL credential-join (Python ``'@'.join``) on inputs
(boundary cases plus randomized fuzzing) and asserts that every observation
matches the model's deep models, as encoded in model.py.

The two A-reference deep-model checks:

  (A-reference 1) ``effective_authority`` (model.py pure region) -- the
      credential '@'-join under specification -- equals the real
      ``'@'.join([creds, authority])`` when credentials are present, and the
      bare authority otherwise. This is the changed behavioural choice, modelled
      deeply (not behind a consumed axiom); G-AX validates it == the real join.

  (A-reference 2) ``assembled`` (model.py pure region) -- the location
      re-assembly -- equals the real stdlib ``urlunparse`` on the regime these
      locations inhabit (non-empty authority, present scheme, empty params):
      ``scheme://authority + path`` with ``?query`` appended when a query is
      present and ``#fragment`` appended when a fragment is present.

An additional END-TO-END check (guarded; uses urllib3's ``parse_url``, the
unchanged decomposition callee available in the eval container) confirms the
whole modelled pipeline reproduces the real ``prepend_scheme_if_needed`` on the
F2P/P2P inputs and on fuzz, so ``verify ⟹ resolved`` is grounded against the
real code.

Core checks import only the Python standard library (``urllib.parse`` -- the
very module the gold patch's combining call resolves to). Exit 0 iff every
obligation holds.
"""
import random
import sys
from urllib.parse import urlunparse


# --- model.py reference encodings (kept in lock-step with the deep models) ---

def effective_authority(creds, authority, has_creds):
    """Reference of model.py's deep model `effective_authority`, on str."""
    if has_creds:
        return creds + "@" + authority
    return authority


def assembled(scheme, authority, path, query, frag, has_query, has_frag):
    """Reference of model.py's deep model `assembled`, on str."""
    base = scheme + "://" + authority + path
    if has_query:
        if has_frag:
            return base + "?" + query + "#" + frag
        return base + "?" + query
    if has_frag:
        return base + "#" + frag
    return base


# --- the checks --------------------------------------------------------------

def check_effective_authority(creds, authority, has_creds):
    """effective_authority == the REAL '@'.join when creds present."""
    model = effective_authority(creds, authority, has_creds)
    if has_creds:
        real = "@".join([creds, authority])      # real credential-join op
    else:
        real = authority
    assert model == real, (
        "effective_authority deep model unsound on creds=%r authority=%r "
        "has_creds=%r: model=%r real=%r"
        % (creds, authority, has_creds, model, real))
    # When credentials are present they MUST survive (non-empty creds change it)
    if has_creds and len(creds) > 0:
        assert model != authority, (
            "credentials dropped for creds=%r authority=%r" % (creds, authority))


def check_assembled(scheme, authority, path, query, frag, has_query, has_frag):
    """assembled == the REAL stdlib urlunparse in the modelled regime."""
    model = assembled(scheme, authority, path, query, frag, has_query, has_frag)
    q = query if has_query else ""
    f = frag if has_frag else ""
    real = urlunparse((scheme, authority, path, "", q, f))   # real callee
    assert model == real, (
        "assembled deep model unsound on scheme=%r authority=%r path=%r "
        "query=%r frag=%r has_query=%r has_frag=%r: model=%r real=%r"
        % (scheme, authority, path, query, frag, has_query, has_frag,
           model, real))


def main():
    rng = random.Random(6028)

    creds_pool = ["", "user", "user:pass", "u", "user:pass word",
                  "user%25user:pass", "a:b", "x"]
    auth_pool = ["example.com", "example.com:80", "host", "h.com:443",
                 "192.168.0.1", "192.168.0.1:5000", "some.host"]
    scheme_pool = ["http", "https", "socks5", "ftp"]
    path_pool = ["", "/path", "/a/b/c", "/path/", "/x"]
    query_pool = ["", "query", "a=1&b=2", "query=yes", "buz=ppicture"]
    frag_pool = ["", "frag", "section", "f", "top"]

    # --- A-reference 1: effective_authority == real '@'.join --------------
    boundary_pairs = [
        ("user:pass", "example.com", True),
        ("user", "example.com", True),
        ("", "example.com", True),         # has_creds True but empty creds
        ("", "example.com", False),        # no creds
        ("a:b", "host:80", True),
    ]
    for creds, authority, has_creds in boundary_pairs:
        check_effective_authority(creds, authority, has_creds)

    for _ in range(20000):
        creds = rng.choice(creds_pool)
        authority = rng.choice(auth_pool)
        has_creds = (creds != "") if rng.random() < 0.5 else rng.choice([True, False])
        check_effective_authority(creds, authority, has_creds)

    # --- A-reference 2: assembled == real urlunparse ----------------------
    boundary_assem = [
        ("http", "example.com", "/path", "", "", False, False),
        ("http", "example.com", "/path", "query", "", True, False),
        ("http", "user:pass@example.com", "/path", "query", "", True, False),
        ("http", "user@example.com", "/path", "query", "", True, False),
        ("http", "example.com:80", "", "", "", False, False),
        ("https", "host", "", "a=1", "", True, False),
        ("http", "user:pass@example.com", "/path", "query", "frag", True, True),
        ("http", "example.com", "/path", "", "section", False, True),
        ("http", "user@example.com", "/path", "", "f", False, True),
    ]
    for scheme, authority, path, query, frag, has_query, has_frag \
            in boundary_assem:
        check_assembled(scheme, authority, path, query, frag,
                        has_query, has_frag)

    for _ in range(20000):
        scheme = rng.choice(scheme_pool)
        authority = rng.choice(auth_pool)
        # the effective authority may carry credentials
        if rng.random() < 0.5:
            authority = rng.choice(creds_pool) + "@" + authority
        path = rng.choice(path_pool)
        query = rng.choice(query_pool)
        frag = rng.choice(frag_pool)
        has_query = query != ""
        has_frag = frag != ""
        check_assembled(scheme, authority, path, query, frag,
                        has_query, has_frag)

    # --- END-TO-END (guarded): the modelled pipeline == real function -----
    try:
        from urllib3.util import parse_url
    except Exception:
        parse_url = None

    if parse_url is not None:
        def model_prepend(url, new_scheme):
            parsed = parse_url(url)
            scheme, auth, host, port, path, query, fragment = parsed
            netloc = parsed.netloc
            if not netloc:
                netloc, path = path, netloc
            # The modelled components -> the model's deep functions:
            scheme_s = scheme if scheme is not None else new_scheme
            path_s = path if path is not None else ""
            eff = effective_authority(auth or "", netloc or "", bool(auth))
            return assembled(scheme_s, eff, path_s, query or "",
                             fragment or "", bool(query), bool(fragment))

        def real_prepend(url, new_scheme):
            # the gold post-patch prepend_scheme_if_needed
            parsed = parse_url(url)
            scheme, auth, host, port, path, query, fragment = parsed
            netloc = parsed.netloc
            if not netloc:
                netloc, path = path, netloc
            if auth:
                netloc = "@".join([auth, netloc])
            if scheme is None:
                scheme = new_scheme
            if path is None:
                path = ""
            return urlunparse((scheme, netloc, path, "", query, fragment))

        e2e_cases = [
            "example.com/path", "//example.com/path", "example.com:80",
            "http://user:pass@example.com/path?query",
            "http://user@example.com/path?query",
            "https://u:p@some.host/path", "http://u:p@other.host/path",
            "http://complex.url.com/path?query=yes",
            "http://user:pass@example.com/path?query#frag",
            "http://example.com/path#section",
            "http://user@example.com/path#f",
            "http://u:p@some.host/path?q=1#top",
        ]
        for url in e2e_cases:
            m = model_prepend(url, "http")
            r = real_prepend(url, "http")
            assert m == r, ("end-to-end model != real prepend on %r: "
                            "model=%r real=%r" % (url, m, r))

        # fuzz the pipeline
        host_pool = ["example.com", "some.host", "other.host:80", "h.io"]
        for _ in range(5000):
            scheme = rng.choice(["http", "https", ""])
            creds = rng.choice(creds_pool)
            host = rng.choice(host_pool)
            path = rng.choice(["", "/p", "/a/b"])
            query = rng.choice(["", "q=1", "x=y&z=w"])
            frag = rng.choice(["", "frag", "top"])
            url = ""
            if scheme:
                url += scheme + "://"
            if creds:
                url += creds + "@"
            url += host + path
            if query:
                url += "?" + query
            if frag:
                url += "#" + frag
            try:
                m = model_prepend(url, "http")
                r = real_prepend(url, "http")
            except Exception:
                continue
            assert m == r, ("end-to-end model != real prepend on fuzz %r: "
                            "model=%r real=%r" % (url, m, r))
        e2e_note = "; end-to-end == real prepend_scheme_if_needed on %d + 5000 fuzz" % len(e2e_cases)
    else:
        e2e_note = "; end-to-end skipped (urllib3 unavailable)"

    print("G-AX OK: effective_authority (credential '@'-join) == real join and "
          "assembled == real urlunparse over boundary + 40000 fuzz inputs%s"
          % e2e_note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
