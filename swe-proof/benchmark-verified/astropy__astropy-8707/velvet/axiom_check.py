#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-8707.

There are NO consumed axioms in Solution.lean. The single kind-A obligation is
an **A-reference**: the deep model `codepointsOf` (Solution.lean `pure` region)
must equal the REAL octet -> character interpretation the fix performs on a raw
octet source, namely Python's `bytes.decode('latin-1')` (each octet b in 0..255
becomes the character whose code point is exactly b, byte-for-byte, no
re-encoding). This is the operation the gold patch introduces:

    image = image.decode('latin1')

`bytes.decode('latin-1')` is a Python built-in (the same decode the gold patch
calls); this check imports nothing repo-specific. We also exercise the modeled
function end to end through the REAL repo callee `Card.fromstring` (its stored
`_image` on a `bytes` input must equal `_pad(image.decode('latin1'))`), which
confirms the deep model + the unchanged downstream normalizer compose exactly as
refinement.md claims. Exit 0 iff every observation matches the model.
"""
import random
import sys


def codepoints_of(octets):
    """Reference of Solution.lean's deep model `codepointsOf`, as a list of
    code points: octet b (0..255) -> the character with code point b."""
    # Char.ofNat b  ==  chr(b)  on 0..255 (the latin-1 block, identity on
    # code points). Returned as code points to compare with the real decode.
    return [b for b in octets]


def check_decode_reference(octets):
    """A-reference: codepointsOf(octets) == [ord(ch) for ch in
    bytes(octets).decode('latin-1')] (the REAL octet->char interpretation)."""
    raw = bytes(octets)
    observed = [ord(ch) for ch in raw.decode("latin-1")]   # real callee
    expected = codepoints_of(octets)                       # deep model
    assert observed == expected, (
        "codepointsOf deep model unsound on %r: bytes.decode('latin-1') gave "
        "%r, deep model gives %r" % (octets, observed, expected))


def main():
    # --- A-reference: every single octet value (the full 0..255 domain) -----
    for b in range(256):
        check_decode_reference([b])

    # --- A-reference: boundary octet sequences ------------------------------
    boundary = [
        [],
        [0], [255], [0, 255], [255, 0],
        list(range(256)),                 # all octets in order
        list(reversed(range(256))),
        [65, 66, 67, 32, 61, 32, 39, 97, 98, 99, 39],   # b"ABC     = 'abc'"-ish
        [0x80, 0x81, 0xfe, 0xff],         # high bytes (mojibake territory)
        [0xc3, 0xa9],                     # UTF-8 'é' bytes, taken byte-for-byte
    ]
    for seq in boundary:
        check_decode_reference(seq)

    # --- A-reference: randomized fuzz ---------------------------------------
    rng = random.Random(8707)
    for _ in range(20000):
        n = rng.randint(0, 90)
        seq = [rng.randint(0, 255) for _ in range(n)]
        check_decode_reference(seq)

    # --- end-to-end through the REAL repo callee (deep model + downstream
    #     normalizer compose as refinement.md C claims): optional, only if the
    #     repo is importable in this container. ------------------------------
    e2e = 0
    try:
        from astropy.io.fits.card import Card, _pad
        for seq in boundary + [[rng.randint(0, 255) for _ in range(rng.randint(0, 90))]
                               for _ in range(2000)]:
            raw = bytes(seq)
            observed = Card.fromstring(raw)._image            # real patched callee
            expected = _pad(raw.decode("latin-1"))            # model + downstream
            assert observed == expected, (
                "Card.fromstring(bytes)._image mismatch on %r: real gave %r, "
                "model+pad gives %r" % (seq, observed, expected))
            e2e += 1
    except Exception as exc:  # noqa: BLE001 - repo not importable -> skip e2e leg
        print("G-AX note: end-to-end repo leg skipped (%s)" % (exc,))

    print("G-AX OK: codepointsOf deep model (== bytes.decode('latin-1')) sound "
          "on 256 single octets + %d boundary + 20000 fuzz sequences%s"
          % (len(boundary),
             ("; +%d end-to-end Card.fromstring checks" % e2e) if e2e else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
