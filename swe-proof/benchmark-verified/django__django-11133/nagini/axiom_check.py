#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11133.

Executes the REAL coercion logic of the changed function (Django's
``HttpResponseBase.make_bytes``, reproduced verbatim below from the patched
source) and the REAL stdlib callee it relies on (``str.encode``) on inputs
covering all four representations (bytes, memoryview, str, and non-string
values) plus randomized fuzzing, and asserts that every observation matches the
model encoded in model.py.

The model's two soundness obligations:

  (A-consumed) the ``charset_encode`` axiom (model.py axioms region) stands in
      for ``str.encode(charset)``. The proof consumes only its PURITY /
      DETERMINISM (``@Pure``, ``Ensures(True)``): a pure function of its
      code-point argument. G-AX checks that determinism on the real callee
      (same code points + same charset -> same octets).

  (model content, the discriminating behaviour) a buffer-bearing value -- an
      immutable octet string (bytes, KIND_OCTETS) OR a buffer view exposing the
      same octets (memoryview, KIND_VIEW) -- is carried through as exactly its
      underlying octets:  make_bytes(memoryview(b)) == make_bytes(b) == b.
      This is what the F2P test demands and is modeled by
      ``Result().data == v.buf``.

Imports nothing repo-specific: ``codecs``/``random`` are standard library and
``str.encode`` is a builtin -- the very encoder the function calls. Exit 0 iff
every obligation holds.
"""
import random
import sys


# --- the REAL changed function, reproduced verbatim from patched source ------
# django/http/response.py  HttpResponseBase.make_bytes (post-gold-patch body).
# The only repo-specific input is self.charset; we parameterize it directly.
def real_make_bytes(value, charset):
    # Handle string types -- can't rely on force_bytes here.
    if isinstance(value, (bytes, memoryview)):   # <- the gold-patched guard
        return bytes(value)
    if isinstance(value, str):
        return bytes(value.encode(charset))
    # Handle non-string types.
    return str(value).encode(charset)


# --- model.py reference: charset_encode is exactly str.encode(charset) -------
def charset_encode(cps, charset):
    """Reference for model.py's axiomatized `charset_encode`, applied to a list
    of code points: build the str from the code points and encode it."""
    return list("".join(chr(c) for c in cps).encode(charset))


# --- the checks --------------------------------------------------------------

def check_buffer_passthrough(raw, charset):
    """A-content: bytes and the memoryview over the same octets both coerce to
    exactly those octets, and the two agree (KIND_OCTETS == KIND_VIEW)."""
    b = bytes(raw)
    from_bytes = real_make_bytes(b, charset)
    from_view = real_make_bytes(memoryview(b), charset)
    assert from_bytes == b, (
        "bytes branch unsound on %r: make_bytes gave %r" % (b, from_bytes))
    assert from_view == b, (
        "memoryview branch unsound on %r: make_bytes gave %r (expected the "
        "underlying octets verbatim, not a textual rendering)" % (b, from_view))
    assert from_view == from_bytes, (
        "buffer kinds disagree on %r: bytes->%r memoryview->%r"
        % (b, from_bytes, from_view))


def check_text_branch(s, charset):
    """A-consumed + R: a str coerces to charset_encode of its code points."""
    observed = list(real_make_bytes(s, charset))
    expected = charset_encode([ord(ch) for ch in s], charset)
    assert observed == expected, (
        "str branch unsound on %r/%s: make_bytes gave %r, model gives %r"
        % (s, charset, observed, expected))


def check_other_branch(value, charset):
    """A-consumed + R: a non-string value coerces to charset_encode of the
    code points of its native-text rendering str(value)."""
    observed = list(real_make_bytes(value, charset))
    expected = charset_encode([ord(ch) for ch in str(value)], charset)
    assert observed == expected, (
        "other branch unsound on %r/%s: make_bytes gave %r, model gives %r"
        % (value, charset, observed, expected))


def _encode_outcome(cps, charset):
    """The deterministic outcome of charset_encode: either the octet list or
    the exception type (a deterministic raise is still a pure function)."""
    try:
        return ("ok", charset_encode(list(cps), charset))
    except Exception as e:                       # noqa: BLE001 - any encode error
        return ("raise", type(e).__name__)


def check_encode_determinism(cps, charset):
    """A-consumed: charset_encode is a pure deterministic function of its
    code-point argument (the only property the proof consumes) -- same input
    yields the same outcome (value or raised exception type)."""
    a = _encode_outcome(cps, charset)
    b = _encode_outcome(cps, charset)
    assert a == b, (
        "charset_encode non-deterministic on %r/%s: %r vs %r"
        % (cps, charset, a, b))


def main():
    charsets = ["utf-8", "latin-1", "ascii", "utf-16"]

    # --- buffer passthrough (A-content): boundary octet buffers -------------
    boundary_buffers = [
        b"",
        b"memoryview",                 # the literal F2P payload
        b"My Content",                 # the problem-statement payload
        b"\x00\x01\x02\xfe\xff",       # full octet range edges
        bytes(range(256)),             # every octet value
        b"\x80\x81\x82",               # high bytes (not valid utf-8 text)
        b"a" * 257,                    # spans a chunk boundary
    ]
    for raw in boundary_buffers:
        for cs in charsets:
            check_buffer_passthrough(raw, cs)

    # --- text branch (A-consumed): ascii-safe strings (encodable everywhere) -
    ascii_texts = ["", "My Content", "12345", "abcdef", "x" * 200]
    for s in ascii_texts:
        for cs in charsets:
            check_text_branch(s, cs)
    # utf-8-only text (the default charset) for non-ascii code points
    for s in ["café", "naïve", "•—é", "日本語", "\U0001F600"]:
        check_text_branch(s, "utf-8")

    # --- other branch (A-consumed): non-string values ----------------------
    other_values = [12345, 0, -7, 3.5, True, None, [1, 2, 3], {"k": "v"}, (1,)]
    for v in other_values:
        for cs in ["utf-8", "latin-1"]:
            check_other_branch(v, cs)

    # --- charset_encode determinism (A-consumed) ----------------------------
    for cps in [[], [104, 105], [0, 255], list(range(0, 128))]:
        for cs in charsets:
            check_encode_determinism(cps, cs)

    # --- randomized fuzz: buffers + text + others ---------------------------
    rng = random.Random(11133)
    for _ in range(20000):
        n = rng.randint(0, 32)
        raw = bytes(rng.randint(0, 255) for _ in range(n))
        cs = rng.choice(charsets)
        check_buffer_passthrough(raw, cs)
    for _ in range(20000):
        n = rng.randint(0, 32)
        s = "".join(chr(rng.randint(32, 126)) for _ in range(n))  # ascii-safe
        cs = rng.choice(charsets)
        check_text_branch(s, cs)
    for _ in range(5000):
        v = rng.choice([rng.randint(-10**9, 10**9), rng.random(),
                        rng.choice([True, False, None])])
        check_other_branch(v, rng.choice(["utf-8", "latin-1"]))

    print("G-AX OK: buffer passthrough (bytes==memoryview==underlying octets) "
          "verbatim on %d boundary + 20000 fuzz buffers across %d charsets; "
          "charset_encode == str.encode deterministic on text + other branches "
          "(+20000 text + 5000 other fuzz)."
          % (len(boundary_buffers), len(charsets)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
