#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11133 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (this bundle's impl carries none inside the impl markers) and
the @Pure helper `is_buffer_kind` copied over as a plain function. PSeq[int]
is carried as a plain tuple of ints. The one @ContractOnly callee,
`charset_encode`, is bridged to the REAL callee it models per mapping.md
section 3.1 -- the builtin text encoder applied in the output charset -- by
building the str from the code points and encoding it (the charset is the
enclosing response's output charset, threaded through a module-level slot
since the model treats it as ambient).

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.http.response.HttpResponseBase.make_bytes` -- imported from /testbed
(the gate applies patch.diff before this script runs; PYTHONPATH=/testbed).
One response object per charset supplies the ambient output charset.

Type bridge (mapping.md section 2): a runtime value is abstracted to the
model's Value carrier by its representation --
  bytes b        -> Value(KIND_OCTETS, buf=tuple(b), cps=(), ...)
  memoryview m   -> Value(KIND_VIEW,   buf=tuple(bytes(m)), cps=(), ...)
  str s          -> Value(KIND_TEXT,   buf=(), cps=tuple(ord(c) for c in s), ...)
  anything else  -> Value(KIND_OTHER,  buf=(), cps=code points of str(value), ...)
and the output bytestring maps to the result's `data` as tuple(output).
Outcomes compare as ("ok", octet tuple) or ("raise", exception type name):
a code-point sequence unencodable in the chosen charset must make shadow and
oracle raise the same way, so the raising region of the domain is checked
too rather than excluded.

Input domain: the model's Requires places only access permissions on the
carrier, so every well-formed runtime value is Requires-satisfying. Boundary
cases cover empty/full-range/high-bit octet buffers (as bytes and as
memoryviews, including sliced and bytearray-backed views), ascii and
non-ascii text, and non-string values (ints, floats, bools, None,
containers, bytearray -- which is NOT buffer-kind here, matching the
runtime discrimination). Fuzz draws all four representations across four
charsets.

>= 1e5 Requires-satisfying inputs: boundary cases x charsets + 100000 fuzz.
Pinned fuzz seed: 11133.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 11133
N_FUZZ = 100_000

# Representation tags (model.py module constants).
KIND_OCTETS = 0
KIND_VIEW = 1
KIND_TEXT = 2
KIND_OTHER = 3

CHARSETS = ["utf-8", "latin-1", "ascii", "utf-16"]

# Ambient output charset for the bridged @ContractOnly callee.
_CHARSET = "utf-8"


def charset_encode(cps):
    """Bridge for the @ContractOnly callee: the REAL builtin text encoder
    applied in the ambient output charset, over code points carried as a
    tuple of ints (mapping.md section 3.1)."""
    return tuple("".join(chr(c) for c in cps).encode(_CHARSET))


# --- pure helper from model.py, decorator stripped ---------------------------

def is_buffer_kind(kind):
    return kind == KIND_OCTETS or kind == KIND_VIEW


# --- the impl regions of model.py, verbatim (contracts stripped) -------------

class Value:
    def __init__(self, kind, buf, cps, data):
        self.kind = kind  # type: int
        self.buf = buf    # type: PSeq[int]
        self.cps = cps    # type: PSeq[int]
        self.data = data  # type: PSeq[int]


def coerce_to_octets(v):
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))


# --- bridge: runtime value -> model carrier ----------------------------------

def abstract(value):
    """mapping.md section 2: representation tag + octet buffer / code points."""
    if isinstance(value, bytes):
        return Value(KIND_OCTETS, tuple(value), (), ())
    if isinstance(value, memoryview):
        return Value(KIND_VIEW, tuple(bytes(value)), (), ())
    if isinstance(value, str):
        return Value(KIND_TEXT, (), tuple(ord(c) for c in value), ())
    return Value(KIND_OTHER, (), tuple(ord(c) for c in str(value)), ())


def shadow_outcome(value, charset):
    global _CHARSET
    _CHARSET = charset
    try:
        return ("ok", coerce_to_octets(abstract(value)).data)
    except Exception as e:  # noqa: BLE001 - encode errors are part of the domain
        return ("raise", type(e).__name__)


def real_outcome(resp, value):
    try:
        return ("ok", tuple(resp.make_bytes(value)))
    except Exception as e:  # noqa: BLE001
        return ("raise", type(e).__name__)


def check_case(responses, value, charset):
    s = shadow_outcome(value, charset)
    r = real_outcome(responses[charset], value)
    if s != r:
        return ("DISAGREEMENT\n  value=%r (type %s)\n  charset=%s\n"
                "  shadow=%r\n  real=%r"
                % (value, type(value).__name__, charset, s, r))
    return None


# --- input generation ---------------------------------------------------------

def boundary_values():
    bufs = [
        b"",
        b"My Content",
        b"\x00\x01\x02\xfe\xff",
        bytes(range(256)),
        b"\x80\x81\x82",            # high bytes, not valid utf-8 text
        b"a" * 300,
    ]
    vals = []
    for b in bufs:
        vals.append(b)
        vals.append(memoryview(b))
        vals.append(memoryview(b)[::2])          # non-trivial sliced view
        vals.append(memoryview(bytearray(b)))    # mutable-backed view
    vals += ["", "My Content", "12345", "x" * 300,
             "caf\xe9", "na\xefve", "日本語", "\U0001F600"]
    vals += [0, 1, -1, 12345, -(2 ** 63), 2 ** 70, 3.5, -0.0, True, False,
             None, [1, 2, 3], (1,), {"k": "v"}, bytearray(b"raw"),
             float("inf"), float("nan")]
    return vals


def rand_value(rng):
    k = rng.random()
    n = rng.randint(0, 48)
    if k < 0.25:
        return bytes(rng.randint(0, 255) for _ in range(n))
    if k < 0.50:
        b = bytes(rng.randint(0, 255) for _ in range(n))
        v = memoryview(b)
        if rng.random() < 0.25 and n >= 2:
            v = v[:: rng.randint(1, 3)]
        return v
    if k < 0.75:
        # Mixed code-point ranges: ascii-safe, latin-1-safe, and full BMP+
        # (unencodable points in narrow charsets exercise the raise path).
        pick = rng.random()
        if pick < 0.5:
            return "".join(chr(rng.randint(32, 126)) for _ in range(n))
        if pick < 0.8:
            return "".join(chr(rng.randint(0, 255)) for _ in range(n))
        return "".join(chr(rng.choice((rng.randint(0, 0xD7FF),
                                       rng.randint(0xE000, 0x10FFFF))))
                       for _ in range(n))
    r = rng.random()
    if r < 0.4:
        return rng.randint(-10 ** 12, 10 ** 12)
    if r < 0.6:
        return rng.random() * 10 ** rng.randint(-3, 6)
    if r < 0.7:
        return rng.choice([True, False, None])
    if r < 0.85:
        return [rng.randint(0, 9) for _ in range(rng.randint(0, 5))]
    return bytearray(rng.randint(0, 255) for _ in range(rng.randint(0, 8)))


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=False, DEFAULT_CHARSET="utf-8")
        try:
            django.setup()
        except Exception:
            pass
    # REAL patched function: the response-body coercion the model models.
    from django.http import HttpResponse

    responses = {cs: HttpResponse(charset=cs) for cs in CHARSETS}

    checked = 0
    n_boundary = 0
    for value in boundary_values():
        for cs in CHARSETS:
            err = check_case(responses, value, cs)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(responses, rand_value(rng), rng.choice(CHARSETS))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real body coercion on %d inputs "
          "(%d boundary + %d fuzz, seed %d) across %d charsets."
          % (checked, n_boundary, N_FUZZ, SEED, len(CHARSETS)))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
