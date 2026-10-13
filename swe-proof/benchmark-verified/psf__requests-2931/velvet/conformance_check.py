#!/usr/bin/env python3
"""G-CONF differential conformance for psf__requests-2931 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both the SHADOW (Solution.lean's impl region, transliterated) and the ORACLE
(the gold-patched repo behaviour) on the same fuzzed inputs and comparing.

One modeled method:

  * encodePayload         — `_encode_params` on a str/bytes payload. Post-patch
                            it returns its argument UNCHANGED (same kind, same
                            content). The discriminating property the issue
                            demands: a binary (bytes) payload stays binary.

Refinement leg exercised here (I):

  - encodePayload's `return data` is I (identity): a str/bytes payload is
    returned with its kind and content preserved.

BRIDGE (mapping.md §2):
  Payload.text s   ↔ a Python `str`
  Payload.binary b ↔ a Python `bytes`
  octet u          ↔ Char.ofNat u.toNat   (decode each byte to its code point)

In-domain note: `to_native_string(bytes)` decodes with encoding='ascii', so its
bytes domain is the ASCII octets 0..127; the deep model coincides there
(Char.ofNat u == chr(u) == ascii-decode). Bytes fuzz is therefore ASCII-only
(mapping.md §3.1 flag dependency). Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied by
the harness before this runs); stdlib + the repo's own `requests` only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 2931
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean impl region, transliterated --------------------

def shadow_encode(payload):
    """encodePayload: `return data` (identity). `payload` is a Python str or
    bytes; we return it unchanged, preserving both kind and content."""
    return payload


# ---- ORACLE: the gold-patched repo behaviour ------------------------------

def _oracle_callables():
    """Resolve the patched `_encode_params` from the repo installed in the
    container (gold patch already applied)."""
    from requests.models import PreparedRequest
    return PreparedRequest._encode_params


def oracle_encode(enc_params, payload):
    """patch.diff's `_encode_params(payload)` for a str/bytes payload."""
    return enc_params(payload)


# ---- inputs ----------------------------------------------------------------

def fuzz_inputs(n, rng):
    # boundary cases (plan §4.1 step 4)
    yield ""
    yield b""
    yield "test=foo"
    yield b"test=foo"
    yield "ABC123"
    yield b"ABC123"
    yield " \t\n;=&#%"
    yield b" \t\n;=&#%"
    yield "x" * 64
    yield b"x" * 64
    # the F2P-shaped binary payload, restricted to its ASCII transport image:
    yield b"hello world"
    # randomized fuzz: half str, half ASCII bytes
    ascii_chars = [chr(c) for c in range(0, 128)]
    for _ in range(n):
        k = rng.randint(0, 24)
        s = "".join(rng.choice(ascii_chars) for _ in range(k))
        if rng.random() < 0.5:
            yield s
        else:
            yield s.encode("ascii")


def main():
    try:
        enc_params = _oracle_callables()
    except Exception as e:  # pragma: no cover - container wiring
        print("G-CONF ERROR: could not import patched requests: %r" % (e,))
        return 2

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for payload in fuzz_inputs(N_FUZZ, rng):
        count += 1

        # --- encodePayload: identity (kind + content preserved) -------------
        sh_e = shadow_encode(payload)
        or_e = oracle_encode(enc_params, payload)
        # The decisive checks: same TYPE (bytes stays bytes — the F2P property)
        # and same content.
        if type(sh_e) is not type(or_e) or sh_e != or_e:
            disagreements.append(("encode", payload, repr(sh_e), repr(or_e)))

        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tag, inp, sh, orc in disagreements:
            print("  [%s] input=%r shadow=%s oracle=%s" % (tag, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of encodePayload agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements "
          "(bytes payloads preserved as bytes)."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
