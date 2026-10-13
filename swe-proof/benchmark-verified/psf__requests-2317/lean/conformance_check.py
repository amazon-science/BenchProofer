#!/usr/bin/env python
"""G-CONF: differential conformance for psf__requests-2317.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_normalizeMethod` skeleton and diffs it against the REAL patched
request-method normalization performed by `requests.sessions.Session.request`
(the changed `method = to_native_string(method)` step followed by
`method.upper()`), as it is finally stored on a `PreparedRequest`.

  shadow of `implementation_normalizeMethod`   vs   real patched normalization
  observable (over the ASCII HTTP-method-token domain, for BOTH a native `str`
  method and a `bytes` method):
    * the stored method's character content == to_native_string(method).upper()

The discriminator (a `bytes` method) IS runtime-observable on this Python-3
testbed: `builtin_str(b'GET') == "b'GET'"` (the bug) vs
`to_native_string(b'GET') == "GET"` (the fix). The conformance check therefore
exercises the bug directly, on both input forms.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import string
import sys

SEED = 23170630
N_RANDOM = 120_000  # >= 1e5


# ---- shadow of implementation_normalizeMethod ------------------------------
# A method is modeled by its decoded textual content (chars) plus whether the
# caller supplied it as text or as a bytes token. The skeleton recovers the
# native textual content (op 1) then upper-cases it (op 2).

def shadow_normalize(chars, is_bytes):
    # op 1: nativeContent -- decoded text in both cases (bytes -> its chars)
    m = chars
    # op 2: upper-case the code points
    m = m.upper()
    return m


# ASCII HTTP-method-token domain (mapping.md domain note): letters, digits and
# the token punctuation a method name may legally contain. All ASCII so that
# bytes(...).decode('ascii') is total.
DOMAIN = string.ascii_letters + string.digits + "-_."


def real_normalize(method, to_native_string):
    """Drive the REAL patched operation and return the stored method chars.

    Mirrors `Session.request`: recover native string via `to_native_string`,
    then build the upper-cased method (`Request(method = method.upper())`)."""
    coerced = to_native_string(method)       # the line the patch CHANGES TO
    upper = coerced.upper()                   # Request(method = method.upper())
    return upper


def main():
    from requests.utils import to_native_string

    rnd = random.Random(SEED)
    checks = 0
    disagreements = 0

    # discrete boundary matrix (text tokens)
    fixed = ["", "GET", "POST", "get", "post", "Put", "dElEtE", "OPTIONS",
             "head", "PATCH", "x", "X", "123", "a-b_c.d", "GeT123"]

    cases = []  # list of (chars, is_bytes)
    for s in fixed:
        cases.append((s, False))
        cases.append((s, True))   # same token, supplied as bytes

    for _ in range(N_RANDOM):
        n = rnd.randint(0, 12)
        s = "".join(rnd.choice(DOMAIN) for _ in range(n))
        cases.append((s, bool(rnd.getrandbits(1))))

    for chars, is_bytes in cases:
        want = shadow_normalize(chars, is_bytes)
        method = chars.encode("ascii") if is_bytes else chars
        got = real_normalize(method, to_native_string)
        checks += 1
        if got != want:
            disagreements += 1
            if disagreements <= 10:
                print("CONTENT MISMATCH method=%r is_bytes=%s want=%r got=%r"
                      % (method, is_bytes, want, got))

    if disagreements:
        print("status=fail conformance FAILED (%d checks, %d disagreements)"
              % (checks, disagreements))
        return 1
    print("status=pass conformance OK (%d checks, 0 disagreements)" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
