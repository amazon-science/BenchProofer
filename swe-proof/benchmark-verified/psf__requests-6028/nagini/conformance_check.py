#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-6028 (nagini).

SHADOW: the impl region of model.py's ``normalize_location``, copied verbatim
below with the contract calls (Assert) stripped. The @Pure helpers of the pure
region (``effective_authority`` / ``assembled``) copy over on a small
immutable-tuple PSeq shim; they serve here as an internal cross-check of the
shadow output.

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``requests.utils.prepend_scheme_if_needed``. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH=/testbed,
so the import resolves to the patched module.

Type bridge (mapping.md section 2): each str component lowers to ``List[int]``
of Unicode code points via ``ord`` and the shadow's output list lifts back the
same way; component presence flags bridge as truthiness (``has_creds`` <->
``if auth:``, ``has_query``/``has_frag`` <-> the truthiness tests inside the
combining callee). The model operates over the already-parsed components
(mapping.md section 2.1), so the end-to-end bridge derives the shadow's inputs
by running the REAL unchanged decomposition callee (``parse_url``, the same
object the oracle calls) and the repo body's component-normalisation lines
that sit above the modelled logic (the netloc/path swap and the scheme/path
None-defaults), then compares the lifted shadow output against the oracle's
output on the raw location string.

Two differential layers:
  1. END-TO-END (primary, vs the real ``prepend_scheme_if_needed``):
     boundary location strings + 100000 fuzz locations, restricted to the
     modelled regime (non-empty effective netloc after the swap — mapping.md
     section 3.3); locations the real parser rejects are skipped (the oracle
     itself raises on them, so no component inputs exist).
  2. COMPONENT-LEVEL (supplement, vs the real callee composition
     ``'@'.join`` + ``urllib.parse.urlunparse`` exactly as the repo lines
     compose them): 20000 fuzz component tuples over a wide code-point
     alphabet, exercising the Requires-satisfying input space directly
     (the preconditions demand only readable lists of code points; the
     regime restrictions — non-empty authority, non-empty scheme, path
     empty-or-'/'-led — are the documented modelled regime).

>= 1e5 Requires-satisfying inputs total. Pinned fuzz seed: 6028.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plus the in-container repo import).
"""
import json
import random
import sys
from urllib.parse import urlunparse

SEED = 6028
N_E2E_FUZZ = 100000
N_COMP_FUZZ = 20000


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

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, contracts stripped ------------------------------

def effective_authority(creds, authority, has_creds):
    """The authority segment that must flow into the assembly. With credentials
    present, they are prepended to the authority joined by a single '@' (64);
    otherwise the authority is used as-is."""
    if has_creds:
        return creds + PSeq(64) + authority
    return authority


def assembled(scheme, authority, path, query, frag, has_query, has_frag):
    """The combining callee's assembly of a location from its components, for
    the regime these locations inhabit (non-empty authority, present scheme,
    empty params)."""
    base = scheme + PSeq(58, 47, 47) + authority + path
    if has_query:
        if has_frag:
            return base + PSeq(63) + query + PSeq(35) + frag
        return base + PSeq(63) + query
    if has_frag:
        return base + PSeq(35) + frag
    return base


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def normalize_location(scheme, creds, authority, path, query, frag,
                       has_creds, has_query, has_frag):
    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    return result


# --- type bridge: str <-> List[int] code points --------------------------------

def lower(s):
    return [ord(ch) for ch in s]


def lift(lst):
    return "".join(chr(c) for c in lst)


# --- oracle: the real patched repo function ------------------------------------

def real_oracle():
    from requests.utils import prepend_scheme_if_needed
    return prepend_scheme_if_needed


def real_parse_url():
    # the unchanged decomposition callee, the same object the oracle calls
    try:
        from requests.utils import parse_url
    except ImportError:
        from urllib3.util import parse_url
    return parse_url


# --- differential drivers -------------------------------------------------------

def shadow_run(scheme, creds, authority, path, query, frag,
               has_creds, has_query, has_frag):
    """Run the shadow on str components via the documented bridge; return the
    lifted str, cross-checking the impl output against the pure-region fold."""
    out = normalize_location(lower(scheme), lower(creds), lower(authority),
                             lower(path), lower(query), lower(frag),
                             has_creds, has_query, has_frag)
    expect = assembled(ToSeq(lower(scheme)),
                       effective_authority(ToSeq(lower(creds)),
                                           ToSeq(lower(authority)), has_creds),
                       ToSeq(lower(path)), ToSeq(lower(query)),
                       ToSeq(lower(frag)), has_query, has_frag)
    if ToSeq(out) != expect:
        raise AssertionError(
            "INTERNAL: impl region and pure fold disagree on components "
            "scheme=%r creds=%r authority=%r path=%r query=%r frag=%r "
            "flags=(%r,%r,%r)" % (scheme, creds, authority, path, query,
                                  frag, has_creds, has_query, has_frag))
    return lift(out)


def check_e2e(oracle, parse_url, url, new_scheme):
    """One end-to-end differential: derive the shadow's component inputs from
    the real parse (plus the repo's component-normalisation lines that sit
    above the modelled logic), run the shadow, compare against the oracle on
    the raw location. Returns (error-or-None, checked_bool)."""
    try:
        parsed = parse_url(url)
    except Exception:
        return None, False        # the oracle raises here too: no components
    scheme, auth, _host, _port, path, query, fragment = parsed
    netloc = parsed.netloc
    if not netloc:
        netloc, path = path, netloc
    if scheme is None:
        scheme = new_scheme
    if path is None:
        path = ""
    if not netloc:
        return None, False        # outside the modelled regime (mapping.md 3.3)
    try:
        real = oracle(url, new_scheme)
    except Exception as exc:
        return ("ORACLE ERROR on input %r: %r" % (url, exc)), False
    shadow = shadow_run(scheme, auth or "", netloc, path, query or "",
                        fragment or "", bool(auth), bool(query),
                        bool(fragment))
    if shadow != real:
        return ("DISAGREEMENT on location %r (new_scheme=%r):\n"
                "  components: scheme=%r creds=%r authority=%r path=%r "
                "query=%r frag=%r flags=(%r,%r,%r)\n"
                "  shadow (impl region)  = %r\n"
                "  real (patched repo fn) = %r"
                % (url, new_scheme, scheme, auth or "", netloc, path,
                   query or "", fragment or "", bool(auth), bool(query),
                   bool(fragment), shadow, real)), True
    return None, True


def check_components(scheme, creds, authority, path, query, frag,
                     has_creds, has_query, has_frag):
    """Component-level differential vs the real callee composition: the real
    '@'.join and the real stdlib urlunparse composed exactly as the mapped
    repo lines compose them (mapping.md sections 3.2/3.3)."""
    netloc = "@".join([creds, authority]) if has_creds else authority
    real = urlunparse((scheme, netloc, path, "",
                       query if has_query else "",
                       frag if has_frag else ""))
    shadow = shadow_run(scheme, creds, authority, path, query, frag,
                        has_creds, has_query, has_frag)
    if shadow != real:
        return ("COMPONENT DISAGREEMENT on scheme=%r creds=%r authority=%r "
                "path=%r query=%r frag=%r flags=(%r,%r,%r):\n"
                "  shadow (impl region)          = %r\n"
                "  real ('@'.join + urlunparse)  = %r"
                % (scheme, creds, authority, path, query, frag, has_creds,
                   has_query, has_frag, shadow, real))
    return None


# --- input generation ------------------------------------------------------------

def boundary_urls():
    return [
        "example.com/path",
        "//example.com/path",
        "example.com",
        "example.com:80",
        "http://example.com/path",
        "http://example.com/path?query",
        "http://example.com/path#frag",
        "http://example.com/path?query#frag",
        "http://user:pass@example.com/path?query",
        "http://user@example.com/path?query",
        "https://u:p@some.host/path",
        "socks5://u:p@other.host:1080/",
        "http://user:pass@example.com/path?query#frag",
        "http://user@example.com#f",
        "http://u@h",
        "http://u:p@h:8080",
        "user:pass@example.com/path",
        "u@example.com",
        "http://example.com/?",
        "http://example.com/#",
        "http://example.com/?#",
        "http://u:p@example.com/?",
        "http://192.168.0.1:5000/x",
        "http://h.io/a/b/c?a=1&b=2#top",
        "HTTP://Example.COM/Path",
        "/just/a/path",
        "http://user%25name:pa%20ss@example.com/p",
    ]


def rand_text(rng, alphabet, lo, hi):
    n = rng.randint(lo, hi)
    return "".join(rng.choice(alphabet) for _ in range(n))


def main():
    oracle = real_oracle()
    parse_url = real_parse_url()
    rng = random.Random(SEED)

    checked = 0
    skipped = 0

    # --- layer 1: end-to-end vs the real patched repo function ------------
    for url in boundary_urls():
        for new_scheme in ("http", "https"):
            err, ok = check_e2e(oracle, parse_url, url, new_scheme)
            if err:
                print(err)
                return 1
            checked += 1 if ok else 0
            skipped += 0 if ok else 1

    scheme_pool = ["http", "https", "socks5", "ftp", ""]
    creds_pool = ["", "user", "user:pass", "u", "a:b", "user%25u:p%20w",
                  "x", "user:", ":pass", "u.se-r:pa_ss"]
    host_pool = ["example.com", "some.host", "other.host", "h.io", "h",
                 "192.168.0.1", "xn--nxasmq6b.example", "sub.d.example.com"]
    port_pool = ["", ":80", ":443", ":8080", ":5000", ":1"]
    path_pool = ["", "/", "/path", "/a/b/c", "/path/", "/x", "/p%20q",
                 "/;params", "/a.b-c_d~e"]
    query_pool = ["", "query", "a=1&b=2", "query=yes", "q", "a=%20",
                  "a=1;b=2", "="]
    frag_pool = ["", "frag", "section", "f", "top", "a/b?c"]

    fuzz_checked = 0
    attempts = 0
    while fuzz_checked < N_E2E_FUZZ and attempts < 4 * N_E2E_FUZZ:
        attempts += 1
        scheme = rng.choice(scheme_pool)
        creds = rng.choice(creds_pool)
        host = rng.choice(host_pool)
        port = rng.choice(port_pool)
        path = rng.choice(path_pool)
        query = rng.choice(query_pool)
        frag = rng.choice(frag_pool)
        url = ""
        if scheme:
            url += scheme + "://"
        elif rng.random() < 0.2:
            url += "//"
        if creds:
            url += creds + "@"
        url += host + port + path
        if query:
            url += "?" + query
        if frag:
            url += "#" + frag
        err, ok = check_e2e(oracle, parse_url, url,
                            rng.choice(["http", "https"]))
        if err:
            print(err)
            return 1
        if ok:
            checked += 1
            fuzz_checked += 1
        else:
            skipped += 1
    n_e2e = checked

    # --- layer 2: component-level vs the real callee composition ----------
    # wide code-point alphabet: ASCII url-ish, separators the assembly emits,
    # controls, latin-1, BMP and astral code points
    comp_alphabet = [chr(c) for c in
                     list(range(33, 127)) + [9, 10, 13, 32, 0x7f, 0x80, 0xe9,
                                             0xff, 0x100, 0x2027, 0x203d,
                                             0x1F600, 0x10FFFF]]
    sep_heavy = ["@", ":", "/", "?", "#", "&", "=", "%"] * 4 + comp_alphabet
    for _ in range(N_COMP_FUZZ):
        scheme = rand_text(rng, comp_alphabet, 1, 8)
        creds = rand_text(rng, sep_heavy, 0, 12)
        authority = rand_text(rng, sep_heavy, 1, 16)
        path = rng.choice(["", "/" + rand_text(rng, sep_heavy, 0, 12)])
        has_creds = rng.random() < 0.6
        has_query = rng.random() < 0.5
        has_frag = rng.random() < 0.5
        query = rand_text(rng, sep_heavy, 1, 12) if has_query else ""
        frag = rand_text(rng, sep_heavy, 1, 10) if has_frag else ""
        err = check_components(scheme, creds, authority, path, query, frag,
                               has_creds, has_query, has_frag)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched prepend_scheme_if_needed "
          "on %d end-to-end inputs (boundary + %d fuzz, %d parse-rejects "
          "skipped) and == the real '@'.join+urlunparse composition on %d "
          "component tuples; seed %d; 0 disagreements."
          % (n_e2e, N_E2E_FUZZ, skipped, N_COMP_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "e2e": n_e2e, "component": N_COMP_FUZZ,
                      "skipped_unparseable": skipped,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
