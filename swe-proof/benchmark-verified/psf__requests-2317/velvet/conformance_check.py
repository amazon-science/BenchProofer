#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-2317.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type, via the mapping.md bijection
              (`List Char` ↔ token characters; for a byte token the carried
              characters are the ASCII decodings of the bytes). The impl region
              computes `nativeSeq token`, the identity on the carried character
              sequence; the deep model `nativeSeq` is the A-reference (validated
              == to_native_string by G-AX) and IS the computed value, so the
              shadow is the R/I leg.
  * ORACLE  — patch.diff's behaviour: the patched coercion
              `to_native_string(method)` (requests' own callee, the real
              correctness oracle, G-RESOLVE), materialized as its character
              sequence.

They must agree on every spec-domain (ASCII) input, for both the native-text
and the byte-string token form. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + requests
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 2317
N_FUZZ = 100_000

# The spec domain is ASCII method tokens (every code point < 128); for an ASCII
# token a byte value equals the code point of its ASCII decoding, so a single
# carrier serves the text and byte forms.
ASCII = [chr(c) for c in range(128)]


def shadow_native(token_chars):
    """nativeSeq (token) transliterated to Python: the identity copy of the
    carried character sequence (the R/I shadow of the impl)."""
    out = []
    for c in token_chars:
        out.extend([c])      # nativeChar c = [c]
    return out


def oracle_native(method):
    """patch.diff's behaviour: requests' own to_native_string(method),
    materialized as its list of characters."""
    from requests.utils import to_native_string
    return list(to_native_string(method))


def fuzz_tokens(n, rng):
    # boundary cases first
    yield ""
    yield "GET"
    yield "POST"
    yield "PUT"
    yield "DELETE"
    yield "HEAD"
    yield "OPTIONS"
    yield "PATCH"
    yield "a"
    yield "Z"
    for _ in range(n):
        k = rng.randint(0, 16)
        yield "".join(rng.choice(ASCII) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_tokens(N_FUZZ, rng):
        # carried character sequence (mapping.md §2): the token's characters
        token_chars = list(s)
        shadow = shadow_native(token_chars)

        # text form: method is the native str token
        oracle_text = oracle_native(s)
        if shadow != oracle_text:
            disagreements.append(("text", s, shadow, oracle_text))

        # byte form: method is the ASCII byte string carrying the same chars
        b = s.encode("ascii")
        oracle_bytes = oracle_native(b)
        if shadow != oracle_bytes:
            disagreements.append(("bytes", s, shadow, oracle_bytes))

        count += 1
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d tokens:"
              % (len(disagreements), count))
        for kind, s, sh, orc in disagreements:
            print("  form=%s input=%r shadow=%r oracle=%r" % (kind, s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of nativeToken agrees with patch.diff "
          "behaviour (to_native_string) on %d tokens x {text,bytes} "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
