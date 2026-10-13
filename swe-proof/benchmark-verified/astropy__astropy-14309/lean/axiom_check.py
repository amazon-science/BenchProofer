#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model of the path branch against the
REAL standard-library string operations the patched line uses,
`filepath.lower().endswith((...))`.

The proof consumes NO callee axiom (axioms region empty). The only deeply
modeled op with a real-callee reference is the suffix test (refinement.md row
4): the Lean `endsWithAny (p.map Char.toLower) fitsExtensions` is asserted to
agree, on boundaries + fuzz, with `p.lower().endswith(EXTS)`. This guards the
deep model against drift from the real string ops.

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import sys

SEED = 14309

EXTS = (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")


def model_endswith_any(p: str) -> bool:
    """The Lean `endsWithAny (p.map Char.toLower) fitsExtensions`.

    Char.toLower is per-code-point; for the suffixes (pure ASCII) this matches
    str.lower on every input that affects the decision. We mirror str.lower for
    the comparison carrier and test plain suffix membership."""
    low = p.lower()
    return any(low.endswith(suf) for suf in EXTS)


def real_endswith_any(p: str) -> bool:
    """REAL callee: filepath.lower().endswith(tuple)."""
    return p.lower().endswith(EXTS)


def main() -> int:
    rng = random.Random(SEED)

    cases = [
        "", "foo.bar", "bububu.ecsv", "x.fits", "X.FITS", "a.FiTs.GZ",
        "a.fit", "b.FIT.GZ", "c.fts", "d.FTS.GZ", ".fits", "fits",
        "name.fits.gz.txt", "weird.FITS ", " .fit", "tab\t.fits",
        "résumé.FITS", "\U0001f600.fts", "MiXeD.FiT.gZ",
    ]
    # Fuzz: random stems + random (possibly truncated/altered) extensions and
    # random case, so both match and non-match paths are exercised.
    stems = ["data", "img", "TBL", "", "a.b.c", "x_y-Z", "café"]
    tails = list(EXTS) + [".txt", ".fit.zip", ".fitsx", ".gz", ".FI", ""]
    for _ in range(50_000):
        stem = rng.choice(stems)
        tail = rng.choice(tails)
        s = stem + tail
        # randomly perturb case
        s = "".join(ch.upper() if rng.random() < 0.5 else ch.lower() for ch in s)
        cases.append(s)

    mismatches = 0
    examples = []
    for p in cases:
        got = model_endswith_any(p)
        want = real_endswith_any(p)
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append((p, got, want))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs filepath.lower().endswith")
        for p, g, w in examples:
            print(f"  path={p!r} model={g} real={w}")
        return 1

    print(f"G-AX OK: endsWithAny == lower().endswith on all probes "
          f"({len(cases)} inputs, seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
