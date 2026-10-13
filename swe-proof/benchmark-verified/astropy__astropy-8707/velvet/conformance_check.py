#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-8707 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`buildImage`),
              transliterated to Python over the *real* repo types via the
              mapping.md bijection:
                Source.text s  ↔  a Python `str`         (the image used as-is)
                Source.raw  b  ↔  a Python `bytes`        (octets 0..255)
                codepointsOf b ↔  bytes.decode('latin-1') (the deep R model)
              then the unchanged downstream fixed-width normalizer `_pad` (an
              I-tagged op, mapping.md §3.1) is applied to the resulting image —
              left as the REAL repo callee, not re-modeled.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Card.fromstring(.)` applied
              at base_commit (the real correctness oracle, G-RESOLVE). Its stored
              `_image` is exactly `_pad(image)` where `image` is the str input or
              the latin-1 decode of the bytes input.

They must agree on every Requires-satisfying input (raw octets are constrained
to 0..255, which Python `bytes` guarantees). Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib-only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 8707
N_FUZZ = 100_000


def shadow_image(src):
    """buildImage(src) transliterated to str/bytes, then the unchanged
    downstream normalizer `_pad` (I-tagged) applied to the resulting image.

    `src` is ('text', str) or ('raw', bytes). Returns the stored image string.
    """
    from astropy.io.fits.card import _pad     # unchanged I-tagged callee (real)
    kind, payload = src
    if kind == "text":
        image = payload                        # Source.text s -> s
    else:
        # codepointsOf b : Char.ofNat applied per octet == bytes.decode('latin-1')
        image = payload.decode("latin-1")     # deep R model, transliterated
    return _pad(image)


def oracle_image(src):
    """patch.diff's behaviour: the patched Card.fromstring's stored `_image`."""
    from astropy.io.fits.card import Card     # patched: decodes bytes via latin1
    kind, payload = src
    return Card.fromstring(payload)._image


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ("raw", b"")
    yield ("raw", b"ABC     = 'abc'")          # the F2P card image
    yield ("raw", bytes([0]))
    yield ("raw", bytes([255]))
    yield ("raw", bytes(range(256)))
    yield ("raw", bytes([0x80, 0x81, 0xfe, 0xff]))
    yield ("raw", bytes([0xc3, 0xa9]))         # UTF-8 'é' bytes, byte-for-byte
    yield ("raw", b"X" * 80)                   # exactly one card length
    yield ("raw", b"X" * 81)                   # just over a card length
    yield ("text", "")
    yield ("text", "ABC     = 'abc'")
    yield ("text", "Y" * 80)
    yield ("text", "Y" * 160)
    ascii_chars = [chr(c) for c in range(32, 127)]
    for _ in range(n):
        if rng.random() < 0.5:
            k = rng.randint(0, 200)
            yield ("raw", bytes(rng.randint(0, 255) for _ in range(k)))
        else:
            k = rng.randint(0, 200)
            yield ("text", "".join(rng.choice(ascii_chars) for _ in range(k)))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for src in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_image(src)
        oracle = oracle_image(src)
        if shadow != oracle:
            disagreements.append((src, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for src, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (src, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildImage agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
