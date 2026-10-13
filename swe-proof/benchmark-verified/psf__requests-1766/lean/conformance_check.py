#!/usr/bin/env python3
"""G-CONF for psf__requests-1766.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_digestAuthHeader` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`HTTPDigestAuth.build_digest_header`, over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

Model (refinement.md): `build_digest_header` assembles the Digest `Authorization`
header value by appending directives to a `base` string and prefixing `Digest `.
The component values it appends — username, realm, nonce, request uri, response
digest, optional opaque/algorithm/digest, nonce-count (nc), client-nonce (cnonce)
— are computed UPSTREAM and unchanged by the patch; the patched op is solely the
QUOTING of the quality-of-protection directive value (`qop="auth"`).

  * Oracle = the REAL patched `build_digest_header(method, url)`.
  * Shadow = assembledDigestHeader(...) (Python port of the Lean pure helper),
             fed the component values. The values we CONTROL as inputs (username,
             realm, nonce, uri, opaque, algorithm) are known directly; the three
             values the real function derives internally with entropy/hashing
             (the response digest, nc and cnonce) are read back out of the
             oracle's output and handed to the shadow. The qop directive's quoted
             value `"auth"` is supplied by the MODEL (not parsed), so a bare-token
             assembly would disagree with the patched oracle.

Type bijection (mapping.md): every component `str` <-> Lean `String`
(byte-for-byte); an absent optional directive (`None`/falsy) <-> the empty string.
stdlib-only; no hypothesis required.
"""
import os
import random
import re
import sys

# requests is import-installed in /testbed (gold patch applied).
from requests.auth import HTTPDigestAuth
try:
    from requests.compat import urlparse
except Exception:  # pragma: no cover - fallback
    from urllib.parse import urlparse


# ---- shadow: Python port of assembledDigestHeader (Solution.lean pure helper) --
def assembled_digest_header(username, realm, nonce, uri, respdig,
                            opaque, algorithm, entdig, qop, ncvalue, cnonce):
    base = ('username="' + username + '", realm="' + realm + '", nonce="' + nonce
            + '", uri="' + uri + '", response="' + respdig + '"')
    if opaque != "":
        base = base + ', opaque="' + opaque + '"'
    if algorithm != "":
        base = base + ', algorithm="' + algorithm + '"'
    if entdig != "":
        base = base + ', digest="' + entdig + '"'
    if qop != "":
        # MODEL-sourced: qop directive value is the double-quoted literal "auth".
        base = base + ', qop="auth", nc=' + ncvalue + ', cnonce="' + cnonce + '"'
    return "Digest " + base


def compute_path(url):
    """Replicate build_digest_header's unchanged path computation (auth.py:101-104)."""
    p = urlparse(url)
    path = p.path
    if p.query:
        path += '?' + p.query
    return path


def oracle(username, password, realm, nonce, url, method,
           opaque, algorithm, qop):
    """Real patched build_digest_header for these inputs."""
    auth = HTTPDigestAuth(username, password)
    chal = {'realm': realm, 'nonce': nonce}
    if qop is not None:
        chal['qop'] = qop
    if algorithm is not None:
        chal['algorithm'] = algorithm
    if opaque is not None:
        chal['opaque'] = opaque
    auth.chal = chal
    return auth.build_digest_header(method, url)


# Extract only the three internally-derived (entropy/hash) component values.
_RESP_RE = re.compile(r'response="([0-9a-fA-F]+)"')
_NC_RE = re.compile(r'nc=([0-9a-fA-F]+)')
_CNONCE_RE = re.compile(r'cnonce="([0-9a-fA-F]+)"')


# Safe alphabet: no '"', no ',', no '=' so parsing the dynamic values is
# unambiguous and the assembled directive structure is well-defined.
SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~"


def rand_token(rng, lo=1, hi=12):
    n = rng.randint(lo, hi)
    return "".join(rng.choice(SAFE) for _ in range(n))


def main():
    rng = random.Random(1766)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    methods = ["GET", "POST", "PUT", "HEAD", "DELETE"]
    algo_pool = [None, "MD5", "md5", "MD5-SESS", "SHA", "sha"]
    qop_pool = [None, "auth", "auth,auth-int"]
    for i in range(N):
        username = rand_token(rng)
        password = rand_token(rng)
        realm = rand_token(rng)
        nonce = rand_token(rng, 4, 16)
        host = rand_token(rng)
        path = "/" + rand_token(rng)
        query = rand_token(rng) if rng.random() < 0.4 else ""
        url = "http://" + host + ".example.com" + path
        if query:
            url += "?" + "k=" + query
        method = rng.choice(methods)
        algorithm = rng.choice(algo_pool)
        opaque = rand_token(rng) if rng.random() < 0.5 else None
        qop = rng.choice(qop_pool)

        o = oracle(username, password, realm, nonce, url, method,
                   opaque, algorithm, qop)

        # Known inputs -> shadow component values.
        uri = compute_path(url)
        m_resp = _RESP_RE.search(o)
        respdig = m_resp.group(1) if m_resp else ""
        if qop is not None:
            m_nc = _NC_RE.search(o)
            m_cn = _CNONCE_RE.search(o)
            ncvalue = m_nc.group(1) if m_nc else ""
            cnonce = m_cn.group(1) if m_cn else ""
        else:
            ncvalue = ""
            cnonce = ""

        s = assembled_digest_header(
            username, realm, nonce, uri, respdig,
            opaque if opaque is not None else "",
            algorithm if algorithm is not None else "",
            "",  # entdig: always None in build_digest_header ("XXX not implemented")
            "auth" if qop is not None else "",
            ncvalue, cnonce,
        )

        if o != s:
            disagreements += 1
            if first is None:
                first = (username, realm, nonce, url, method, algorithm, opaque,
                         qop, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
