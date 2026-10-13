#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-2931.

Executes the REAL native-string decoder callee (`requests.utils.to_native_string`)
on Requires-satisfying inputs (boundary cases + randomized fuzz) and asserts
that every observation matches the model's single axiom, as encoded in model.py:

  (axiom `to_native`)
      Requires(Implies(v_is_bytes, is_ascii(v_data)))   # binary input -> ASCII octets
      Ensures(Result() == v_data)                       # content preserved (native text)

i.e. for a native-text input the decoder is the identity, and for a binary
input whose octets are all ASCII (< 128) the decoded native text has exactly
the same content (code points == octet values). The result is always native
text (Python 3); the caller drops the binary tag. Non-ASCII binary inputs are
EXCLUDED by the Requires (the real callee raises there) and are not asserted on
— but we additionally confirm the decoder DOES reject them, which is precisely
why the body path (which never calls it) must carry binary payloads verbatim.

In the SWE-bench eval container `requests` is installed, so the REAL callee is
imported and exercised directly. For host runs where requests is absent we fall
back to a byte-identical replica of the Python-3 branch of `to_native_string`
(requests/utils.py @ base_commit) — the same function the gold patch calls.
Exit 0 iff every obligation holds.
"""
import random
import sys


def _load_callee():
    """Return the REAL requests.utils.to_native_string if importable, else a
    byte-identical replica of its Python-3 branch (requests/utils.py)."""
    try:
        from requests.utils import to_native_string as real
        return real, "requests.utils.to_native_string (real callee)"
    except Exception:
        def replica(string, encoding="ascii"):
            # requests/utils.py @ base_commit, Python-3 branch:
            #   if isinstance(string, builtin_str): out = string
            #   else: out = string.decode(encoding)
            if isinstance(string, str):
                return string
            return string.decode(encoding)
        return replica, "to_native_string replica (Python-3 branch)"


def check_native(callee, value, content):
    """Assert to_native(value) preserves content and yields native text (str).

    `value` is a str or bytes whose per-element content is `content`
    (code points for str, octet values for bytes). Requires precondition:
    if value is bytes, every octet < 128.
    """
    if isinstance(value, bytes):
        assert all(b < 128 for b in value), "test input violates the axiom Requires"
    out = callee(value)
    assert isinstance(out, str), (
        "to_native unsound on %r: result %r is not native text" % (value, out))
    observed = [ord(ch) for ch in out]
    assert observed == content, (
        "to_native unsound on %r: callee gave content %r, axiom Ensures %r"
        % (value, observed, content))


def check_rejects_non_ascii(callee, value):
    """Outside the Requires, the binary decoder rejects non-ASCII octets — the
    very reason the body path must NOT route a binary payload through it."""
    raised = False
    try:
        callee(value)
    except Exception:
        raised = True
    assert raised, (
        "expected the native-string decoder to reject non-ASCII binary %r, "
        "but it did not" % (value,))


def main():
    callee, label = _load_callee()

    # --- boundary: native-text (str) inputs are the identity ---------------
    text_boundary = ["", "test=foo", "a", "ABC xyz", "0123456789",
                     "!$&'()*+,;=~:@,", "x=1&y=2", "key=value&k2=v2"]
    for s in text_boundary:
        check_native(callee, s, [ord(c) for c in s])

    # --- boundary: ASCII binary inputs decode to the same content ----------
    bytes_boundary = [b"", b"test=foo", b"A", b"0123456789",
                      b"x=1&y=2", b"!$&'()*+,;=~:@,"]
    for b in bytes_boundary:
        check_native(callee, b, list(b))

    # --- randomized fuzz over the Requires-satisfying domain ---------------
    rng = random.Random(2931)
    ascii_codes = list(range(0, 128))
    for _ in range(20000):
        n = rng.randint(0, 24)
        codes = [rng.choice(ascii_codes) for _ in range(n)]
        s = "".join(chr(c) for c in codes)
        check_native(callee, s, codes)              # native text
        check_native(callee, bytes(codes), codes)   # ASCII binary

    # --- outside Requires: non-ASCII binary is rejected --------------------
    # incl. the F2P payload u"ööö".encode("utf-8") == b"\xc3\xb6\xc3\xb6\xc3\xb6"
    non_ascii = [b"\xc3\xb6\xc3\xb6\xc3\xb6", b"\x80", b"\xff",
                 b"caf\xc3\xa9", b"\xe2\x80\xa2"]
    for b in non_ascii:
        check_rejects_non_ascii(callee, b)

    print("G-AX OK [%s]: to_native axiom sound on %d text + %d bytes boundary "
          "+ 40000 fuzz (ASCII text & bytes), and rejects %d non-ASCII binary "
          "inputs" % (label, len(text_boundary), len(bytes_boundary),
                      len(non_ascii)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
