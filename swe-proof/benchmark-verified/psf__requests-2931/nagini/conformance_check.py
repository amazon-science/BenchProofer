#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-2931 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls stripped (the impl regions contain no Requires/Ensures/Assert lines to
strip). The `Value` carrier class is a plain-Python shim (same two-field
constructor body); `PSeq[int]` content becomes a plain tuple of ints. The
single @ContractOnly callee, `to_native`, is realized by calling the REAL
repo function `requests.utils.to_native_string` (imported from /testbed) on
the bridged str/bytes value, per the contract for @ContractOnly callees.

ORACLE: the two REAL patched repo sites the model models per mapping.md:
  - site A: `requests.models.PreparedRequest._encode_params` on a
    textual-or-binary value (the branch the model's `serialize_request_body`
    abstracts). Called directly — it is a static method.
  - site B: the textual-or-binary coercion of the `params` argument inside
    `requests.models.PreparedRequest.prepare_url` (the site the model's
    `normalize_query_string` abstracts). Checked two ways: (1) the patched
    site's guard+call fragment executed with the REAL repo callee over the
    full Requires domain, and (2) end-to-end through `prepare_url` itself on
    inputs whose content is query-safe (so downstream percent-requoting is
    the identity and the coerced value is observable verbatim in `.url`).

The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the patched code is what gets imported.

Type bridge (mapping.md section 2): a model Value(is_bytes=False, data)
maps to the str whose k-th code point is data[k]; Value(is_bytes=True, data)
maps to the bytes whose k-th octet is data[k]. The bridge is the bijection
value_to_py / py_to_value below; shadow and oracle outputs are compared as
(type tag, content tuple) pairs.

Input domain (Requires-satisfying only):
  - serialize_request_body: Requires is permission-only, so ANY value is
    admissible — str content over the full code-point range (ASCII, latin-1,
    BMP, astral, lone surrogates) and bytes content over all octets 0..255,
    including non-ASCII octets (the discriminating payload class).
  - normalize_query_string: Requires(binary => all octets < 128), so bytes
    inputs draw octets 0..127 only; str inputs are unconstrained.

>= 1e5 Requires-satisfying inputs: boundary cases + 60000 site-A fuzz +
60000 site-B fragment fuzz + 2000 site-B end-to-end fuzz.
Pinned fuzz seed: 2931.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 2931
N_FUZZ_A = 60_000
N_FUZZ_B = 60_000
N_FUZZ_B_URL = 2_000


# --- Value carrier shim (constructor impl region verbatim) ----------------

class Value:
    def __init__(self, is_bytes, data):
        self.is_bytes = is_bytes
        self.data = data


# --- type bridge: model carrier <-> repo str/bytes -------------------------

def value_to_py(v):
    """Value(is_bytes, tuple-of-int) -> the str/bytes it abstracts."""
    if v.is_bytes:
        return bytes(v.data)
    return "".join(chr(c) for c in v.data)


def py_to_value(x):
    """str/bytes -> (type tag, content tuple) observation."""
    if isinstance(x, bytes):
        return (True, tuple(x))
    if isinstance(x, str):
        return (False, tuple(ord(ch) for ch in x))
    return ("<non-string %r>" % type(x), x)


def observe(v):
    """(type tag, content tuple) observation of a shadow Value."""
    return (bool(v.is_bytes), tuple(v.data))


# --- @ContractOnly callee: delegates to the REAL repo function -------------

_REAL_TO_NATIVE = None  # bound in main() after the repo import


def to_native(v_is_bytes, v_data):
    py = bytes(v_data) if v_is_bytes else "".join(chr(c) for c in v_data)
    out = _REAL_TO_NATIVE(py)
    return tuple(ord(ch) for ch in out)


# --- impl regions of model.py, verbatim (contracts stripped) ---------------

def serialize_request_body(v):
    r = Value(v.is_bytes, v.data)
    return r


def normalize_query_string(v):
    nd = to_native(v.is_bytes, v.data)
    r = Value(False, nd)
    return r


# --- input generation -------------------------------------------------------

def boundary_values_site_a():
    """Full domain: any str, any bytes (incl. non-ASCII octets)."""
    return [
        (False, ()),                             # empty text
        (True, ()),                              # empty binary
        (False, tuple(ord(c) for c in "test=foo")),
        (True, tuple(b"test=foo")),
        (False, (0,)),                           # NUL code point
        (True, (0,)),                            # NUL octet
        (True, (127,)), (True, (128,)), (True, (255,)),
        (True, (0xC3, 0xB6, 0xC3, 0xB6, 0xC3, 0xB6)),  # non-ASCII binary
        (True, tuple(range(256))),               # every octet once
        (False, (0xF6, 0xF6, 0xF6)),             # non-ASCII text
        (False, (0x10FFFF,)),                    # max code point
        (False, (0x1F600,)),                     # astral text
        (False, (0xD800,)),                      # lone surrogate code point
        (False, tuple(ord(c) for c in "a=1&b=2")),
        (True, tuple(b"a=1&b=2")),
    ]


def boundary_values_site_b():
    """Requires-satisfying: binary content must be all-ASCII octets."""
    return [
        (False, ()),
        (True, ()),
        (False, tuple(ord(c) for c in "test=foo")),
        (True, tuple(b"test=foo")),
        (True, (0,)), (True, (127,)),
        (True, tuple(range(128))),               # every ASCII octet once
        (False, (0xF6, 0xF6, 0xF6)),             # non-ASCII TEXT is admissible
        (False, (0x1F600,)),
        (False, tuple(ord(c) for c in "a=1&b=2")),
        (True, tuple(b"a=1&b=2")),
        (False, tuple(ord(c) for c in "!$&'()*+,;=~:@,")),
        (True, tuple(b"!$&'()*+,;=~:@,")),
    ]


def rand_value_site_a(rng):
    is_bytes = rng.random() < 0.5
    n = rng.randint(0, 32)
    if is_bytes:
        data = tuple(rng.randint(0, 255) for _ in range(n))
    else:
        cps = []
        for _ in range(n):
            k = rng.random()
            if k < 0.55:
                cps.append(rng.randint(0, 127))            # ASCII
            elif k < 0.80:
                cps.append(rng.randint(128, 0xFF))         # latin-1 range
            elif k < 0.95:
                cps.append(rng.randint(0x100, 0xFFFF))     # BMP (may hit
                # surrogate code points — Python str carries them fine and
                # nothing here encodes the text)
            else:
                cps.append(rng.randint(0x10000, 0x10FFFF))  # astral
        data = tuple(cps)
    return (is_bytes, data)


def rand_value_site_b(rng):
    is_bytes = rng.random() < 0.5
    n = rng.randint(0, 32)
    if is_bytes:
        data = tuple(rng.randint(0, 127) for _ in range(n))  # ASCII only
    else:
        cps = []
        for _ in range(n):
            k = rng.random()
            if k < 0.7:
                cps.append(rng.randint(0, 127))
            elif k < 0.9:
                cps.append(rng.randint(128, 0xFFFF))
            else:
                cps.append(rng.randint(0x10000, 0x10FFFF))
        data = tuple(cps)
    return (is_bytes, data)


_URL_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789=&-._~"


def rand_value_site_b_urlsafe(rng):
    """Content whose percent-requoting downstream of the modeled site is the
    identity, so the coerced value is observable verbatim in the URL query."""
    is_bytes = rng.random() < 0.5
    n = rng.randint(1, 24)
    chars = [rng.choice(_URL_SAFE) for _ in range(n)]
    data = tuple(ord(c) for c in chars)
    return (is_bytes, data)


# --- differential checks -----------------------------------------------------

def check_site_a(encode_params, is_bytes, data):
    v = Value(is_bytes, data)
    shadow_out = observe(serialize_request_body(v))
    real_out = py_to_value(encode_params(value_to_py(v)))
    if shadow_out != real_out:
        return ("DISAGREEMENT (site A: _encode_params str/bytes branch)\n"
                "  input=(is_bytes=%r, data=%r)\n  shadow=%r\n  real=%r"
                % (is_bytes, data, shadow_out, real_out))
    return None


def check_site_b_fragment(is_bytes, data):
    """The patched site's guard+call fragment, executed with the REAL repo
    callee, vs the shadow."""
    v = Value(is_bytes, data)
    shadow_out = observe(normalize_query_string(v))
    params = value_to_py(v)
    if isinstance(params, (str, bytes)):
        params = _REAL_TO_NATIVE(params)
    real_out = py_to_value(params)
    if shadow_out != real_out:
        return ("DISAGREEMENT (site B fragment: params coercion)\n"
                "  input=(is_bytes=%r, data=%r)\n  shadow=%r\n  real=%r"
                % (is_bytes, data, shadow_out, real_out))
    return None


def check_site_b_url(prepared_request_cls, is_bytes, data):
    """End-to-end through the REAL patched prepare_url: on query-safe content
    the coerced value appears verbatim as the URL query, and the shadow
    predicts it (native text, same characters)."""
    v = Value(is_bytes, data)
    shadow_out = normalize_query_string(v)
    expected_query = "".join(chr(c) for c in shadow_out.data)
    p = prepared_request_cls()
    p.prepare_url("http://example.com/path", value_to_py(v))
    base = "http://example.com/path"
    real_url = p.url
    expected_url = base + ("?" + expected_query if expected_query else "")
    if real_url != expected_url:
        return ("DISAGREEMENT (site B end-to-end: prepare_url query)\n"
                "  input=(is_bytes=%r, data=%r)\n  shadow predicts url=%r\n"
                "  real url=%r" % (is_bytes, data, expected_url, real_url))
    return None


def main():
    global _REAL_TO_NATIVE
    # REAL patched repo symbols (PYTHONPATH=/testbed, gold patch applied).
    from requests.models import PreparedRequest
    from requests.utils import to_native_string
    _REAL_TO_NATIVE = to_native_string
    encode_params = PreparedRequest._encode_params

    checked = 0

    # --- site A: boundary + fuzz over the full str/bytes domain ------------
    for is_bytes, data in boundary_values_site_a():
        err = check_site_a(encode_params, is_bytes, data)
        if err:
            print(err)
            return 1
        checked += 1
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_A):
        is_bytes, data = rand_value_site_a(rng)
        err = check_site_a(encode_params, is_bytes, data)
        if err:
            print(err)
            return 1
        checked += 1

    # --- site B fragment: boundary + fuzz over the Requires domain ---------
    for is_bytes, data in boundary_values_site_b():
        err = check_site_b_fragment(is_bytes, data)
        if err:
            print(err)
            return 1
        checked += 1
    for _ in range(N_FUZZ_B):
        is_bytes, data = rand_value_site_b(rng)
        err = check_site_b_fragment(is_bytes, data)
        if err:
            print(err)
            return 1
        checked += 1

    # --- site B end-to-end: query-safe content through prepare_url ---------
    for is_bytes, data in [(True, tuple(b"test=foo")),
                           (False, tuple(ord(c) for c in "test=foo")),
                           (True, tuple(b"a=1&b=2")),
                           (False, tuple(ord(c) for c in "a=1&b=2"))]:
        err = check_site_b_url(PreparedRequest, is_bytes, data)
        if err:
            print(err)
            return 1
        checked += 1
    for _ in range(N_FUZZ_B_URL):
        is_bytes, data = rand_value_site_b_urlsafe(rng)
        err = check_site_b_url(PreparedRequest, is_bytes, data)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched repo on %d inputs "
          "(site A boundary+%d fuzz incl. non-ASCII binary; site B fragment "
          "boundary+%d fuzz; site B end-to-end %d; seed %d)."
          % (checked, N_FUZZ_A, N_FUZZ_B, N_FUZZ_B_URL, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions; "
                                "@ContractOnly callee bound to the real "
                                "repo function)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
