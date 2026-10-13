#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-1724 (plan section 4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  -- the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` <-> `str`). The R/I content of the impl is
              the per-code-point upper fold (`upperSeq`) plus length preservation.
              The A-consumed callee (the native-flavour constructor `builtin_str`)
              is NOT substituted by its stub model here; G-CONF isolates the R/I
              legs, so the A leg is out of scope (it stays with G-AX). We compare
              the CONTENT (code-point sequence) of the carried method, which is
              the R/I observable; the flavour bit is the A-consumed leg.
  * ORACLE  -- `patch.diff`'s behaviour: the carried method content is
              `builtin_str(method).upper()` applied at base_commit (the real
              correctness oracle, G-RESOLVE). Its code-point sequence is the
              oracle for the content fold.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container, stdlib only. The fuzz seed is pinned (mapping.md section 4) for a
deterministic verdict.
"""
import random
import sys

SEED = 1724
N_FUZZ = 100000

# The real native-flavour constructor the patch calls (content-preserving for
# the ASCII method names). Falls back to stdlib str if requests is absent.
try:
    from requests.compat import builtin_str as REAL_BUILTIN_STR
except Exception:  # pragma: no cover
    REAL_BUILTIN_STR = str


def _upper_cp(c):
    if 97 <= c <= 122:        # 'a'..'z' -> 'A'..'Z'
        return c - 32
    return c


def shadow_content(text):
    """upperSeq (text.toList) transliterated to a code-point sequence. This is
    the R/I content shadow of the impl: the backward `while` fold of
    normalizeMethod computes exactly the per-code-point upper map of `text`."""
    return [_upper_cp(ord(ch)) for ch in text]


def oracle_content(text):
    """patch.diff's carried-method CONTENT: builtin_str(method).upper(), as a
    code-point sequence. (The flavour bit is the A-consumed leg, out of scope
    here; we compare content only.)"""
    return [ord(ch) for ch in REAL_BUILTIN_STR(text).upper()]


def fuzz_inputs(n, rng):
    # boundary cases first (plan section 4.1 step 4)
    yield ""
    for m in ["get", "post", "put", "delete", "head", "options", "patch",
              "trace", "connect", "GET", "POST", "Get", "pOsT"]:
        yield m
    for c in range(0, 128):
        yield chr(c)
    yield "".join(chr(c) for c in range(0, 128))
    yield "abcXYZ123-_ "
    alphabet = list("getposPUTdelHEAD0123-_ ") + [chr(c) for c in range(32, 127)]
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_content(s)
        oracle = oracle_content(s)
        # length preservation + per-code-point content (the R/I postconditions)
        if shadow != oracle or len(shadow) != len(s):
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of normalizeMethod (content fold + length) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
