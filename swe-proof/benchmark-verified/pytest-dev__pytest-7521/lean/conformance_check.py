#!/usr/bin/env python3
r"""G-CONF — differential test of the R shadow of implementation_readCaptured
against the patch.diff behaviour (the post-patch capture readback).

The impl region is all R (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the post-patch impl op-for-op: a verbatim copy of the written
character stream (identity). We diff that against an INDEPENDENT oracle that
exercises the REAL patched code path: an `io.TextIOWrapper` constructed exactly
as the patch builds the capture `EncodedFile` — `encoding="utf-8",
errors="replace", newline=""` — over the bytes that were written, then `.read()`.
That is precisely what `FDCapture.snap()` does to turn the buffer back into text.

We additionally assert (the discriminating fact) that the PRE-patch path
(`newline=None`) disagrees with the shadow on at least one carriage-return input
— i.e. the spec genuinely sees the bug.

Bijection (mapping.md): Python `str` code points <-> Lean `List Char`. The fuzz
alphabet oversamples `\r`, `\n` and ASCII letters so `\r`, `\r\n`, `\r\r\n`,
trailing `\r`, and plain text are all covered.

stdlib-only. exit 0 iff zero disagreements on the post-patch leg AND the
prepatch leg is observably different.
"""
import io
import json
import random
import sys

SEED = 7521          # pinned in mapping.md
N = 120_000          # >= 10^5

# Oversample CR/LF relative to letters so newline combinations are dense.
ALPHABET = list("\r\r\r\n\n\nabcXYZ 0%.")


def real_readback(written: str, newline) -> str:
    """The real capture readback: write bytes into a TextIOWrapper built like the
    capture EncodedFile, then read() them back. `newline=""` is the patched
    behaviour; `newline=None` is the pre-patch behaviour."""
    raw = io.BytesIO(written.encode("utf-8"))
    wrapper = io.TextIOWrapper(
        raw, encoding="utf-8", errors="replace", newline=newline, write_through=True
    )
    wrapper.seek(0)
    return wrapper.read()


def shadow(written: str) -> str:
    """R shadow of implementation_readCaptured (post-patch): verbatim copy."""
    out = []
    for c in written:
        out.append(c)
    return "".join(out)


def rand_str(rng: random.Random) -> str:
    n = rng.randint(0, 64)
    return "".join(rng.choice(ALPHABET) for _ in range(n))


def main() -> int:
    rng = random.Random(SEED)

    # Deterministic boundary / regression cases first.
    fixed = [
        "", "\r", "\n", "\r\n", "\r\r\n", "x\r", "  0%\r",
        "a\nb", "a\rb", "a\r\nb", "Greetings from DOS\r",
        "\n\r", "\r\r", "\n\n", "line1\r\nline2\r",
    ]

    disagreements = 0
    examples = []
    prepatch_differs = False

    def check(s: str) -> None:
        nonlocal disagreements, prepatch_differs
        sh = shadow(s)
        post = real_readback(s, "")           # patched: verbatim
        if sh != post:
            disagreements += 1
            if len(examples) < 10:
                examples.append({"input": s, "shadow": sh, "real_post": post})
        pre = real_readback(s, None)          # pre-patch: universal-newline xlate
        if pre != post:
            prepatch_differs = True

    for s in fixed:
        check(s)
    for _ in range(N):
        check(rand_str(rng))

    ok = disagreements == 0 and prepatch_differs
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "seed": SEED,
        "cases": N + len(fixed),
        "disagreements": disagreements,
        "examples": examples,
        "prepatch_differs_from_postpatch": prepatch_differs,
        "note": "shadow (verbatim copy) == real newline='' readback; "
                "prepatch newline=None readback differs on CR inputs (the bug)",
    }))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
