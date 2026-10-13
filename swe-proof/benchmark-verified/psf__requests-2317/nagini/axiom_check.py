#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-2317.

Executes the REAL post-patch coercion callee on method tokens (boundary
HTTP-method tokens as both native text and byte strings, plus randomized ASCII
fuzz over the WHOLE Requires domain) and asserts that every observation matches
the model, as encoded in model.py.

The single kind-A check:

  (A-reference) the deep model `native_method` (the verified copy loop in
      model.py) == the real post-patch callee `requests.utils.to_native_string`.
      The changed coercion is modeled DEEPLY, not behind a consumed axiom; G-AX
      validates that deep model against the real callee:
        to_native_string(text-token)  -> the token's own characters
        to_native_string(byte-token)  -> the ASCII decoding (same characters)
      i.e. the identity on the carried code-point sequence for an ASCII token.

The fuzz alphabet is generated DIRECTLY from the model's `Requires` predicate
(every value 0..127 except quote 39 and backslash 92), so the checked domain
equals the spec domain (no strict-subset hole): the A-reference is exercised on
every value the model admits, including the control characters 0..31 and DEL
127 that a narrower printable-ASCII alphabet would have skipped.

The real post-patch callee is `requests.utils.to_native_string` (the very
function the gold patch introduces). It is imported when `requests` is
available (the eval container); otherwise a provenance-faithful inline copy of
`requests/utils.py:655` (Python-3 branch) is used so the check still runs. Both
agree on the ASCII token domain. Exit 0 iff every obligation holds.
"""
import random
import sys

try:
    from requests.utils import to_native_string  # the REAL post-patch callee
    _SOURCE = "requests.utils.to_native_string (installed)"
except Exception:
    # Provenance-faithful inline copy of requests/utils.py:655, Python-3 branch
    # (builtin_str == str, is_py2 == False).
    def to_native_string(string, encoding="ascii"):  # noqa: ANN001
        if isinstance(string, str):
            return string
        return string.decode(encoding)
    _SOURCE = "inline requests/utils.py:655 (Py3 branch)"


# --- model.py reference encoding (kept in lock-step with the model) ----------

def native_method(content, is_bytes):
    """Reference implementation of model.py's deep model `native_method`: the
    token's own carried characters, independent of `is_bytes`."""
    return list(content)


# --- the model Requires domain ------------------------------------------------
# model.py pre-conditions: every value 0 <= v < 128 and v != 39 and v != 92.
def in_requires_domain(values):
    return all(0 <= v < 128 and v != 39 and v != 92 for v in values)


# --- the check ----------------------------------------------------------------

def check_native_reference(content):
    """Assert the deep model native_method(...) == the REAL to_native_string
    on BOTH the text and the (ASCII) byte form of the token. `content` is a
    list of code points satisfying the model Requires domain."""
    assert in_requires_domain(content), (
        "fuzz token %r is outside the model Requires domain" % (content,))
    method_str = "".join(chr(v) for v in content)

    # text token
    obs_text = [ord(ch) for ch in to_native_string(method_str)]   # real callee
    exp_text = native_method(content, False)                      # deep model
    assert obs_text == exp_text, (
        "native_method deep model unsound on text %r: to_native_string gave %r,"
        " deep model gives %r" % (method_str, obs_text, exp_text))

    # byte token
    bs = bytes(content)
    obs_bytes = [ord(ch) for ch in to_native_string(bs)]          # real callee
    exp_bytes = native_method(content, True)                      # deep model
    assert obs_bytes == exp_bytes, (
        "native_method deep model unsound on bytes %r: to_native_string gave %r,"
        " deep model gives %r" % (bs, obs_bytes, exp_bytes))


def main():
    # Boundary HTTP method tokens (and a few mixed-case / longer ones).
    boundary = ["", "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS",
                "PATCH", "TRACE", "CONNECT", "get", "Post", "X", "GETGET"]
    for m in boundary:
        check_native_reference([ord(ch) for ch in m])

    # Exhaustive single-value sweep of the WHOLE Requires domain (0..127 except
    # 39/92), so every in-domain code point -- including the control chars 0..31
    # and DEL 127 -- is exercised as both a text and a byte token.
    domain = [v for v in range(0, 128) if v not in (39, 92)]
    for v in domain:
        check_native_reference([v])

    # Randomized fuzz over the SAME (full) Requires domain alphabet.
    rng = random.Random(2317)
    alphabet = domain
    for _ in range(20000):
        n = rng.randint(0, 16)
        content = [rng.choice(alphabet) for _ in range(n)]
        check_native_reference(content)

    print("G-AX OK [%s]: native_method deep model (== to_native_string) sound "
          "on %d boundary + %d full-domain-sweep + 20000 fuzz tokens "
          "(text+bytes) over the entire Requires domain (0..127 \\ {39,92})."
          % (_SOURCE, len(boundary), len(domain)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
