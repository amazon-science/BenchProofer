#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14309 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `classifyFitsOrigin` impl
              region, transliterated to Python over the *real* repo types. The
              branch CONTROL FLOW (stream → path → args, the operation the change
              fixes) is the I content; it reads the REAL sub-observations (a real
              fileobj `read`/signature compare, the real
              `str.lower().endswith((...))` extension test — the A-reference
              callee, real code not a model — and the real `isinstance` against
              the HDU classes). What G-CONF exercises is that a present path
              yields the extension verdict OUTRIGHT and never falls through to
              `args[0]`.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched real
              `astropy.io.fits.connect.is_fits` itself, called on the same
              arguments (the real correctness oracle, G-RESOLVE — the harness
              applies patch.diff before this runs).

Both are classified into the `Except Crash Bool` outcome domain: an `IndexError`
escaping ↔ ("raise","index"); a returned bool ↔ ("value", b). They must agree
for every argument configuration. Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the astropy
under test only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import io
import random
import string
import sys

from astropy.io.fits import connect
from astropy.io.fits import HDUList, TableHDU, BinTableHDU, GroupsHDU
from astropy.io.fits.hdu.hdulist import FITS_SIGNATURE

SEED = 14309
N_FUZZ = 100_000
KNOWN_EXTS = (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")
HDU_CLASSES = (HDUList, TableHDU, BinTableHDU, GroupsHDU)


# --- the A-reference callee: the REAL unchanged extension test ----------------
def real_ext_test(path):
    return path.lower().endswith(KNOWN_EXTS)


def outcome_shadow(filepath, fileobj, args):
    """The R/I transliteration of `classifyFitsOrigin`: branch stream → path →
    args, using the REAL sub-observations. A present path returns the extension
    verdict outright (the fixed control flow); only a path-absent call reads
    args, and args[0] on empty args raises IndexError."""
    try:
        if fileobj is not None:                         # stream branch (A1)
            pos = fileobj.tell()
            sig = fileobj.read(30)
            fileobj.seek(pos)
            return ("value", bool(sig == FITS_SIGNATURE))
        if filepath is not None:                        # path branch (A2): outright
            return ("value", bool(real_ext_test(filepath)))
        # args branch (A3): reached only when neither stream nor path present
        return ("value", bool(isinstance(args[0], HDU_CLASSES)))
    except IndexError:
        return ("raise", "index")                       # Crash.indexOOB


def outcome_oracle(filepath, fileobj, args):
    """patch.diff's behaviour: the gold-patched real is_fits, classified into the
    same observable-outcome domain."""
    try:
        v = connect.is_fits("write", filepath, fileobj, *args)
    except IndexError:
        return ("raise", "index")
    return ("value", bool(v))


def make_fileobj(content):
    return io.BytesIO(content)


def fuzz_inputs(n, rng):
    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    # the F2P scenario: present non-matching path, EMPTY args -> must NOT raise
    yield (None, "foo.bar", None, ())
    yield (None, "bububu.ecsv", None, ())
    yield (None, "", None, ())
    # present MATCHING path, empty args -> True, no read of args
    yield (None, "a.fits", None, ())
    yield (None, "X.FITS.GZ", None, ())
    yield (None, "y.fit", None, ())
    # present path WITH args present too -> still the path verdict (args ignored)
    yield (None, "foo.bar", None, (object(),))
    yield (None, "a.fits", None, (HDUList(),))
    # path-absent, EMPTY args -> IndexError on both sides
    yield (None, None, None, ())
    # path-absent, args present -> head's isinstance verdict
    yield (None, None, None, (HDUList(),))
    yield (None, None, None, (object(),))
    yield (None, None, None, (123, "ignored"))
    # stream present (matching + non-matching signature)
    yield (None, None, make_fileobj(FITS_SIGNATURE + b" rest"), ())
    yield (None, None, make_fileobj(b"not a fits header at all...."), ())
    # stream present even with a path -> stream wins
    yield (None, "a.fits", make_fileobj(b"nope"), ())

    # --- randomized fuzz -----------------------------------------------------
    alphabet = string.ascii_letters + string.digits + "._-/ "
    arg_pool = [HDUList(), object(), 123, "str", None, b"bytes", [1, 2]]
    for _ in range(n):
        roll = rng.random()
        # build a possibly-matching path
        base = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        if rng.random() < 0.4:
            ext = rng.choice(KNOWN_EXTS)
            ext = "".join(c.upper() if rng.random() < 0.3 else c for c in ext)
            pathval = base + ext
        else:
            pathval = base
        # random trailing args (often empty, to exercise the crash boundary)
        k = rng.choice([0, 0, 0, 1, 2])
        args = tuple(rng.choice(arg_pool) for _ in range(k))

        if roll < 0.45:
            # present path (matching or not), variable args -> path verdict
            yield (None, pathval, None, args)
        elif roll < 0.70:
            # path-absent -> args branch (empty args -> IndexError)
            yield (None, None, None, args)
        elif roll < 0.90:
            # stream present
            if rng.random() < 0.5:
                fo = make_fileobj(FITS_SIGNATURE + bytes(rng.randint(0, 255)
                                  for _ in range(rng.randint(0, 8))))
            else:
                fo = make_fileobj(bytes(rng.randint(0, 255)
                                  for _ in range(rng.randint(0, 40))))
            yield (None, pathval if rng.random() < 0.5 else None, fo, args)
        else:
            # path present together with present args -> args must be ignored
            yield (None, pathval, None, args if args else (object(),))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for _lead, filepath, fileobj, args in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # fileobj is consumed by tell/read/seek on BOTH sides; give each a fresh
        # copy so the shadow and oracle see identical stream state.
        if fileobj is not None:
            data = fileobj.getvalue()
            fo_shadow = io.BytesIO(data)
            fo_oracle = io.BytesIO(data)
        else:
            fo_shadow = fo_oracle = None
        shadow = outcome_shadow(filepath, fo_shadow, args)
        oracle = outcome_oracle(filepath, fo_oracle, args)
        if shadow != oracle:
            disagreements.append(
                (repr(filepath), fileobj is not None, len(args), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for fp, has_fo, nargs, sh, orc in disagreements:
            print("  path=%s fileobj=%s nargs=%d shadow=%r oracle=%r"
                  % (fp, has_fo, nargs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of classifyFitsOrigin agrees with patch.diff "
          "behaviour on %d is_fits calls (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
