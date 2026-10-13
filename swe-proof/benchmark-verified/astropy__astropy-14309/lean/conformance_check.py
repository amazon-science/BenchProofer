#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_isFits
against the patch.diff behaviour (post-patch `is_fits`).

The impl region is NOT all-A-tagged (it is mostly I/R structure). The single
A-reference op (the path suffix test) is left as the REAL string ops
`p.lower().endswith(EXTS)` — exactly what the post-patch path branch evaluates.
The shadow therefore reproduces the post-patch control flow op-for-op; we assert
zero disagreements vs an independent reconstruction of the patched function over
>=10^5 fuzzed inputs spanning all three branches.

Outcomes are encoded as ("ok", bool) for a normal return, or ("error",) for the
out-of-range positional access (the IndexError the bug produced / the post-patch
code still produces only when no path/fileobj is given and args is empty).

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14309
N = 120_000

FITS_SIGNATURE = "SIMPLE  =                    T"   # 30 chars (ASCII bytes)
EXTS = (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")


def shadow(filepath, fileobj, args):
    """R/I shadow of implementation_isFits.

    if fileobj is not None: return ok(take30 == signature)
    if filepath is not None: return ok(lower().endswith(EXTS))   # A-reference
    match args: [] -> error ; a::_ -> ok(a)
    """
    if fileobj is not None:
        return ("ok", fileobj[:30] == FITS_SIGNATURE)
    if filepath is not None:
        return ("ok", filepath.lower().endswith(EXTS))   # REAL callee
    if len(args) == 0:
        return ("error",)
    return ("ok", bool(args[0]))


def patched_is_fits(filepath, fileobj, args):
    """Independent reconstruction of post-patch is_fits behaviour.

    fileobj branch returns sig==FITS_SIGNATURE; filepath branch returns the
    endswith boolean directly; otherwise probes args[0] (IndexError if empty)."""
    if fileobj is not None:
        sig = fileobj[:30]
        return ("ok", sig == FITS_SIGNATURE)
    elif filepath is not None:
        return ("ok", filepath.lower().endswith(EXTS))
    try:
        return ("ok", bool(args[0]))
    except IndexError:
        return ("error",)


def rand_path(rng):
    stems = ["data", "img", "TBL", "", "a.b.c", "x_y-Z", "café", "bububu"]
    tails = list(EXTS) + [".ecsv", ".txt", ".fit.zip", ".fitsx", ".gz", ".FI", ""]
    s = rng.choice(stems) + rng.choice(tails)
    return "".join(ch.upper() if rng.random() < 0.5 else ch.lower() for ch in s)


def rand_content(rng):
    # half the time produce the real signature (possibly with trailing junk),
    # half random ASCII, to exercise the equality both ways.
    if rng.random() < 0.5:
        extra = "".join(chr(rng.randint(32, 126)) for _ in range(rng.randint(0, 5)))
        return FITS_SIGNATURE + extra
    n = rng.randint(0, 40)
    return "".join(chr(rng.randint(32, 126)) for _ in range(n))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (incl. the issue repro: non-FITS path,
    # empty args -> the bug site, now ok(False) post-patch).
    fixed = [
        (None, None, []),                       # no path/obj, empty args -> error
        (None, None, [True]),                   # args probe true
        (None, None, [False]),                  # args probe false
        ("bububu.ecsv", None, []),              # the issue repro -> ok(False)
        ("foo.bar", None, []),                  # F2P: connect.is_fits("","foo.bar",None)
        ("x.fits", None, []),                   # ok(True)
        ("X.FITS", None, []),                   # case-insensitive -> ok(True)
        ("a.fit.gz", None, [False]),            # path wins over args
        (None, FITS_SIGNATURE, []),             # signature match -> ok(True)
        (None, "nope", []),                     # signature mismatch -> ok(False)
        (None, FITS_SIGNATURE + "xx", [True]),  # take30 match, fileobj wins
        ("ignored.fits", FITS_SIGNATURE, []),   # fileobj wins over path
    ]

    cases = list(fixed)
    for _ in range(N):
        r = rng.random()
        if r < 0.34:
            fileobj = rand_content(rng)
            filepath = rand_path(rng) if rng.random() < 0.5 else None
            args = [rng.random() < 0.5 for _ in range(rng.randint(0, 3))]
            cases.append((filepath, fileobj, args))
        elif r < 0.67:
            filepath = rand_path(rng)
            args = [rng.random() < 0.5 for _ in range(rng.randint(0, 3))]
            cases.append((filepath, None, args))
        else:
            args = [rng.random() < 0.5 for _ in range(rng.randint(0, 3))]
            cases.append((None, None, args))

    for filepath, fileobj, args in cases:
        got = shadow(filepath, fileobj, args)
        want = patched_is_fits(filepath, fileobj, args)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((filepath, fileobj, args, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for fp, fo, a, g, w in examples:
            print(f"  filepath={fp!r} fileobj={fo!r} args={a!r} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
