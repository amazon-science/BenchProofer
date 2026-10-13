#!/usr/bin/env python
"""G-CONF: differential conformance for psf__requests-6028.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_prependScheme` / `reassemble` skeleton and diffs it against the
REAL patched callee `requests.utils.prepend_scheme_if_needed` over a discrete
catalogue of URLs plus >=1e5 randomized URLs.

Modeled domain (mapping.md): URLs whose parse yields a NON-EMPTY authority
(`parse_url(url).netloc` truthy) — i.e. a host is present. That is the
precondition `authority0 ≠ ""` carried in `correct_prependScheme`, and the
configuration the issue reports (a proxy URL with userinfo + host). The
empty-authority swap branch and the auth-without-host degenerate case are out of
the modeled precondition domain and excluded (they are not what the F2P tests
exercise; the real callee even raises on the latter).

Bridge (mapping.md): the upstream `parse_url(url)` is the I-tagged parse step.
Its components map to the Lean inputs as
  scheme0   <- parsed.scheme            (None -> none)
  auth      <- parsed.auth              (None -> none)
  authority0<- parsed.netloc            (host[:port], the urllib3 `netloc`)
  path0     <- parsed.path or ''        (None -> "")
  query     <- parsed.query or ''       (None -> "")
  fragment  <- parsed.fragment or ''    (None -> "")
The Lean result `String` is compared verbatim against the real function's str.

Exit 0 iff zero disagreements. stdlib + urllib3 (already in the image); pinned
seed.
"""
import random
import string
import sys

SEED = 20240630
N_RANDOM = 150_000  # >= 1e5


# ---- Python shadow of assembleUrl / reassemble / implementation_prependScheme
# (post-patch R/I leg, transliteration of the Lean `pure` + `impl` regions) -----

def assemble_url(scheme, authority, path, query, fragment):
    url = path
    if url != "" and url[:1] != "/":
        url = "/" + url
    url = "//" + authority + url
    url = scheme + ":" + url
    if query != "":
        url = url + "?" + query
    if fragment != "":
        url = url + "#" + fragment
    return url


def shadow_reassemble(scheme0, auth, authority0, path, query, fragment, new_scheme):
    """Transliteration of `reassemble` / `implementation_prependScheme`.
    `scheme0`, `auth` are str or None; the rest are str."""
    authority = path if authority0 == "" else authority0
    path = authority0 if authority0 == "" else path
    if auth is not None and auth != "":
        authority = auth + "@" + authority
    scheme = new_scheme if scheme0 is None else scheme0
    return assemble_url(scheme, authority, path, query, fragment)


# ---- real callee observation ------------------------------------------------

def real_prepend(url, new_scheme):
    from requests.utils import prepend_scheme_if_needed
    return prepend_scheme_if_needed(url, new_scheme)


def main():
    from urllib3.util import parse_url
    from urllib3.exceptions import LocationParseError

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0
    skipped = 0

    def rand_token(n):
        alpha = string.ascii_letters + string.digits
        return "".join(rng.choice(alpha) for _ in range(rng.randint(0, n)))

    def gen_url():
        scheme = rng.choice(["http", "https", "ftp", "HTTP", None])
        if rng.random() < 0.6:
            u = rand_token(6)
            auth = u if rng.random() < 0.5 else u + ":" + rand_token(6)
        else:
            auth = None
        host = rng.choice(["example.com", "h", "some.host", "a.b.c", "x.io"])
        port = str(rng.randint(1, 65535)) if rng.random() < 0.4 else None
        path = ("/" + rand_token(6)) if rng.random() < 0.7 else ""
        query = rand_token(5) if rng.random() < 0.5 else None
        frag = rand_token(4) if rng.random() < 0.4 else None
        s = ""
        if scheme:
            s += scheme + "://"
        elif rng.random() < 0.5:
            s += "//"
        if auth:
            s += auth + "@"
        s += host
        if port:
            s += ":" + port
        s += path
        if query:
            s += "?" + query
        if frag:
            s += "#" + frag
        return s

    discrete = [
        "http://user:pass@example.com/path?query",
        "http://user@example.com/path?query",
        "example.com/path",
        "//example.com/path",
        "example.com:80",
        "http://user@host/p",
        "http://h:80/p?q#frag",
        "https://u:p@some.host:443/a/b?c=d#e",
        "ftp://x.io",
        "//u:p@h",
    ]

    cases = list(discrete) + [gen_url() for _ in range(N_RANDOM)]

    for url in cases:
        try:
            p = parse_url(url)
        except (LocationParseError, ValueError):
            skipped += 1
            continue
        netloc = p.netloc
        if not netloc:  # empty-authority swap branch: out of modeled precondition
            skipped += 1
            continue
        scheme0 = p.scheme
        auth = p.auth
        authority0 = netloc
        path0 = p.path or ""
        query = p.query or ""
        fragment = p.fragment or ""

        try:
            got = real_prepend(url, "http")
        except Exception as e:  # noqa: BLE001
            got = ("ERR", type(e).__name__)
        exp = shadow_reassemble(scheme0, auth, authority0, path0, query, fragment, "http")
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH url={url!r}: real={got!r} shadow={exp!r} "
                      f"parsed=(scheme={scheme0!r},auth={auth!r},netloc={authority0!r},"
                      f"path={path0!r},query={query!r},frag={fragment!r})")

    print(f"checked={checked} skipped={skipped} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
