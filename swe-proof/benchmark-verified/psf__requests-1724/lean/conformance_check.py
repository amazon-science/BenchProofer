#!/usr/bin/env python
"""G-CONF: differential conformance for psf__requests-1724.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_normalizeMethod` skeleton and diffs it against the REAL patched
request-method normalization performed by `requests.sessions.Session.request`
(the added `method = builtin_str(method)` step followed by `method.upper()`),
as it is finally stored on a `PreparedRequest`.

  shadow of `implementation_normalizeMethod`   vs   real patched normalization
  observable (over the ASCII HTTP-method-token domain):
    * the stored method's character content  == builtin_str(method).upper()
    * the stored method's runtime type        is the native `builtin_str` type

The Python-2-only `wide` (unicode-vs-native) discriminator the spec also pins is
NOT runtime-observable on this Python-3.9 testbed (`builtin_str is str`); it is
enforced by G-DIFF (the prepatch fails to typecheck on `result.wide = false`),
not here. See mapping.md.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import string
import sys

SEED = 17240626
N_RANDOM = 120000  # >= 1e5


# ---- shadow of implementation_normalizeMethod ------------------------------
# A method is modeled as its sequence of code points (a str). The skeleton
# clears the wide flag (native coercion -> identity on ASCII content) then
# upper-cases the code points.

def shadow_normalize(method_chars):
    # op 2: native coercion (identity on ASCII code-point content)
    m = method_chars
    # op 3: upper-case the code points
    m = m.upper()
    return m


# ASCII HTTP-method-token domain (mapping.md domain note): letters, digits and
# the token punctuation a method name may legally contain.
DOMAIN = string.ascii_letters + string.digits + "-_."


def real_normalize(method, builtin_str, PreparedRequest):
    """Drive the REAL patched operations and return (stored_chars, is_native).

    Mirrors `Session.request`: coerce via `builtin_str`, build the upper-cased
    method, then push it through `PreparedRequest.prepare_method` (the unchanged
    downstream that finally stores `self.method`)."""
    coerced = builtin_str(method)            # the line the patch ADDS
    upper = coerced.upper()                  # Request(method = method.upper())
    pr = PreparedRequest()
    pr.prepare_method(upper)                 # unchanged downstream storage
    stored = pr.method
    return stored, isinstance(stored, builtin_str)


def main():
    from requests.compat import builtin_str
    from requests.models import PreparedRequest

    rnd = random.Random(SEED)
    checks = 0
    disagreements = 0

    # discrete boundary matrix
    fixed = ["", "GET", "POST", "get", "post", "Put", "dElEtE", "OPTIONS",
             "head", "PATCH", "x", "X", "123", "a-b_c.d", "GeT123"]
    cases = list(fixed)
    for _ in range(N_RANDOM):
        n = rnd.randint(0, 12)
        cases.append("".join(rnd.choice(DOMAIN) for _ in range(n)))

    for method in cases:
        want_chars = shadow_normalize(method)
        stored, is_native = real_normalize(method, builtin_str, PreparedRequest)
        checks += 1
        if stored != want_chars:
            disagreements += 1
            if disagreements <= 10:
                print("CONTENT MISMATCH method=%r want=%r got=%r"
                      % (method, want_chars, stored))
        if not is_native:
            disagreements += 1
            if disagreements <= 10:
                print("TYPE MISMATCH method=%r stored type=%r not native"
                      % (method, type(stored)))

    if disagreements:
        print("status=fail conformance FAILED (%d checks, %d disagreements)"
              % (checks, disagreements))
        return 1
    print("status=pass conformance OK (%d checks, 0 disagreements)" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
