#!/usr/bin/env python
"""G-CONF: differential conformance for astropy__astropy-8707.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_cardFromString` skeleton and diffs it against the REAL patched
`Card.fromstring(image)._image` over the str/bytes input matrix plus >=1e5
randomized draws.

  shadow of `implementation_cardFromString`   vs   Card.fromstring(image)._image
  observable: the produced card-image text (the value `fromstring` sets and the
              keyword/value parser reads back)

Both the latin-1 reinterpretation (`bytes.decode('latin1')`) and the padding
(`_pad`) are the A-reference deep models being validated here.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240626
N_RANDOM = 120_000  # >= 1e5
CARD_WIDTH = 80


# ---- shadow of bytesAsText / padCard / implementation_cardFromString -------

def shadow_pad(text):
    n = len(text)
    if n == CARD_WIDTH:
        return text
    if n > CARD_WIDTH:
        r = n % CARD_WIDTH
        return text if r == 0 else text + " " * (CARD_WIDTH - r)
    r = n % CARD_WIDTH
    return text + " " * (CARD_WIDTH - r)


def shadow_card_from_string(image):
    # image is either str or bytes (R shadow of CardImage.text / .bytes)
    if isinstance(image, bytes):
        # bytesAsText: byte n -> code point n (latin-1 identity)
        text = "".join(chr(b) for b in image)
    else:
        text = image
    return shadow_pad(text)


# ---- the real patched Card.fromstring --------------------------------------

def real_observe(image):
    from astropy.io.fits.card import Card
    card = Card.fromstring(image)
    # `._image` is the only state fromstring sets; it is the value the
    # keyword/value parser reads back. Compare it as the observable.
    return card._image


def main():
    rng = random.Random(SEED)

    cases = []
    # Boundary lengths around the 80-column width (str and bytes forms).
    for n in [0, 1, 79, 80, 81, 159, 160, 161]:
        cases.append("A" * n)
        cases.append((b"A" * n))
    # The exact F2P card.
    cases.append(b"ABC     = 'abc'")
    cases.append("ABC     = 'abc'")
    # Non-ASCII bytes that exercise latin-1 (0x80..0xFF) — the whole point.
    cases.append(bytes(range(256)))
    cases.append(bytes([0x80, 0xA0, 0xFF, 0x41]))

    def rand_text(n):
        # printable-ish characters; FITS images are normally ASCII text
        return "".join(chr(rng.randint(32, 126)) for _ in range(n))

    def rand_bytes(n):
        return bytes(rng.randint(0, 255) for _ in range(n))

    for _ in range(N_RANDOM):
        n = rng.randint(0, 200)
        if rng.random() < 0.5:
            cases.append(rand_text(n))
        else:
            cases.append(rand_bytes(n))

    disagreements = 0
    checked = 0
    for image in cases:
        try:
            got = real_observe(image)
        except Exception as e:  # noqa: BLE001
            got = ("EXC", type(e).__name__)
        exp = shadow_card_from_string(image)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH image={image!r:.40}: real={got!r:.60} shadow={exp!r:.60}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
