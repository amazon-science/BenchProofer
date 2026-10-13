#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-2931.

This bundle has NO consumed axioms. The single modeled external callee is the
native-string coercion `toNativeString` (Solution.lean pure region), modeled
DEEPLY (an A-reference), and validated here `== ` the REAL repo callee
`requests.utils.to_native_string` over its whole input domain.

  (A-reference) deep model `to_native_string_model` == real `to_native_string`:
      - text payload (str)   : identity                          -> str
      - binary payload (bytes): decode each octet to its code point
        (Char.ofNat u.toNat ↔ chr(u))                            -> str

  FLAG / DOMAIN dependency (mapping.md §3.1): `to_native_string(string,
  encoding='ascii')` decodes bytes with the DEFAULT encoding 'ascii'. Its bytes
  domain is therefore the ASCII octets 0..127; outside that range the real
  callee raises UnicodeDecodeError and the gold path never reaches it (the
  payload is passed straight through by the patched `_encode_params`). We fuzz
  exactly that in-domain region — where `chr(u) == ascii-decode(u)` so the deep
  model coincides exactly — and additionally CONFIRM the real callee raises on
  out-of-ASCII bytes (documenting why the model's domain is the right one).

Imports only the repo's own `requests` (the same module the gold patch calls)
plus stdlib. Exit 0 iff every obligation holds.
"""
import random
import sys


def to_native_string_model(payload):
    """Reference encoding of Solution.lean's deep model `toNativeString`.
    `payload` is a Python str (text) or bytes (binary)."""
    if isinstance(payload, str):
        return payload
    return "".join(chr(b) for b in payload)   # per-octet decode


def check_reference(to_native_string, payload):
    """Assert the deep model == the REAL to_native_string on an in-domain input."""
    observed = to_native_string(payload)          # real callee
    expected = to_native_string_model(payload)    # deep model
    assert observed == expected, (
        "toNativeString deep model unsound on %r: real gave %r, model gives %r"
        % (payload, observed, expected))
    # The native form is always a `str` (text payload) — the property the spec's
    # `toNativeString` postcondition (.text ...) relies on.
    assert isinstance(observed, str), (
        "to_native_string did not yield a native str on %r: %r"
        % (payload, observed))


def main():
    from requests.utils import to_native_string

    # --- boundary: text payloads (identity) --------------------------------
    text_boundary = ["", "test=foo", "ABC123", " \t\n;=&#%",
                     "x" * 64, "Joe's Crab Shack", "a=1&b=2"]
    for s in text_boundary:
        check_reference(to_native_string, s)

    # --- boundary: binary payloads, ASCII domain (per-octet decode) --------
    bytes_boundary = [b"", b"test=foo", b"ABC123", b" \t\n;=&#%",
                      b"x" * 64, bytes(range(0, 128))]
    for b in bytes_boundary:
        check_reference(to_native_string, b)

    # --- randomized fuzz over the in-domain region -------------------------
    rng = random.Random(2931)
    ascii_chars = [chr(c) for c in range(0, 128)]
    n_checks = len(text_boundary) + len(bytes_boundary)
    for _ in range(20000):
        k = rng.randint(0, 24)
        s = "".join(rng.choice(ascii_chars) for _ in range(k))
        if rng.random() < 0.5:
            check_reference(to_native_string, s)            # str
        else:
            check_reference(to_native_string, s.encode("ascii"))  # ASCII bytes
        n_checks += 1

    # --- domain documentation: real callee raises on out-of-ASCII bytes ----
    # (Justifies restricting the model's bytes domain to ASCII octets, mapping
    #  §3.1; the gold-patched _encode_params never coerces such payloads.)
    raised = 0
    for hi in (0x80, 0xC3, 0xFF, 0xE2):
        try:
            to_native_string(bytes([hi]))
        except (UnicodeDecodeError, UnicodeError):
            raised += 1
    assert raised == 4, (
        "expected to_native_string to raise on all 4 out-of-ASCII octets, "
        "raised on %d" % raised)

    print("G-AX OK: toNativeString deep model (== real requests.to_native_string) "
          "sound on %d boundary + fuzz in-domain inputs; real callee confirmed to "
          "raise on out-of-ASCII bytes (model domain = ASCII octets)." % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
