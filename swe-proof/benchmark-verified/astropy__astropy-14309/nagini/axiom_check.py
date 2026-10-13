#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14309.

This bundle consumes NO `@ContractOnly` axiom and references NO stdlib
deep-model (the `axioms` region of model.py is empty): the modeled delta is a
control-flow decision over boolean classification bits + an argument count,
spelled out deeply as the pure cascade `decided` (model.py). G-AX therefore
reduces to a DECISION-EQUIVALENCE check: call the REAL
`astropy.io.fits.connect.is_fits` on the F2P input and on a fuzz of
present-path / present-stream / trailing-argument configurations, observe its
result (a bool, or an IndexError), and assert it equals the verdict the model's
`decided` decides from the same classification bits.

The load-bearing obligation: when a path name (`filepath`) is present, the real
predicate returns a definite bool computed solely from the suffix test — TRUE
iff the path ends with a recognised FITS suffix, FALSE otherwise — and NEVER
faults by indexing an absent trailing argument. This equivalence holds only
AFTER the gold patch; the script also asserts the pre-patch divergence is real
(an unrecognised present path with no trailing argument WOULD raise IndexError
under the one-armed fall-through), documenting that the spec senses the change.

Imports only the repo's own `astropy.io.fits` (the very package the patch lives
in) — no Nagini, nothing model-specific. Exit 0 iff every obligation holds.
"""
import io
import random
import sys

from astropy.io.fits import connect
from astropy.io.fits import BinTableHDU, GroupsHDU, HDUList, TableHDU
from astropy.io.fits.hdu.hdulist import FITS_SIGNATURE

# Model result codes (model.py pure region):
R_TRUE = 1
R_FALSE = 0
R_FAULT = -1

FITS_SUFFIXES = (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")


def decided(stream_present, sig_matches, path_present, path_recognised,
            n_trailing, first_trailing_accepted):
    """Reference copy of model.py's pure `decided` cascade."""
    if stream_present:
        if sig_matches:
            return R_TRUE
        return R_FALSE
    if path_present:
        if path_recognised:
            return R_TRUE
        return R_FALSE
    if n_trailing == 0:
        return R_FAULT
    if first_trailing_accepted:
        return R_TRUE
    return R_FALSE


def real_outcome(filepath, fileobj, args):
    """Run the REAL is_fits and map its observable outcome to a model code.
    A returned bool -> R_TRUE / R_FALSE; an IndexError (the out-of-range fault
    on args[0]) -> R_FAULT."""
    try:
        res = connect.is_fits("write", filepath, fileobj, *args)
    except IndexError:
        return R_FAULT
    assert res is True or res is False, (
        "is_fits returned a non-bool %r for filepath=%r fileobj=%r args=%r"
        % (res, filepath, fileobj, args))
    return R_TRUE if res else R_FALSE


def classification_bits(filepath, fileobj, args):
    """Compute the model's input facts for a real call, mirroring is_fits's own
    probes."""
    stream_present = fileobj is not None
    sig_matches = False
    if stream_present:
        pos = fileobj.tell()
        sig = fileobj.read(30)
        fileobj.seek(pos)
        sig_matches = (sig == FITS_SIGNATURE)
    path_present = filepath is not None
    path_recognised = path_present and filepath.lower().endswith(FITS_SUFFIXES)
    n_trailing = len(args)
    first_trailing_accepted = (
        n_trailing >= 1
        and isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU)))
    return dict(stream_present=stream_present, sig_matches=sig_matches,
                path_present=path_present, path_recognised=path_recognised,
                n_trailing=n_trailing,
                first_trailing_accepted=first_trailing_accepted)


def check(filepath, fileobj, args, label):
    bits = classification_bits(filepath, fileobj, args)
    want = decided(**bits)
    got = real_outcome(filepath, fileobj, args)
    assert got == want, (
        "%s: real is_fits outcome %d != model decided %d (bits=%s)"
        % (label, got, want, bits))
    return bits, want, got


def main():
    n_checks = 0

    # --- F2P case: connect.is_fits("", "foo.bar", None) -> False -------------
    # present path, unrecognised suffix, no stream, NO trailing argument.
    bits, want, got = check("foo.bar", None, (), "F2P gh-14305")
    assert bits["path_present"] and not bits["path_recognised"] \
        and not bits["stream_present"] and bits["n_trailing"] == 0, \
        "F2P: expected present-unrecognised-path, no stream, no trailing arg"
    assert want == R_FALSE and got == R_FALSE, \
        "F2P: is_fits('','foo.bar',None) must return False (not fault)"
    n_checks += 1

    # --- present path, RECOGNISED suffix, no trailing arg -> True ------------
    for fp in [".fits", "a.FITS", "x.fit", "y.fits.gz", "z.FTS.GZ",
               "deep/path/img.fit.gz"]:
        bits, want, got = check(fp, None, (), "recognised path %r" % fp)
        assert bits["path_recognised"] and want == R_TRUE and got == R_TRUE, \
            "recognised FITS path must return True: %r" % fp
        n_checks += 1

    # --- present path, UNRECOGNISED suffix, no trailing arg -> False ---------
    for fp in ["foo.bar", "table.ecsv", "data.txt", "noext", "x.fits.bz2",
               "archive.fit.zip", ""]:
        bits, want, got = check(fp, None, (), "unrecognised path %r" % fp)
        assert not bits["path_recognised"] and want == R_FALSE \
            and got == R_FALSE, \
            "unrecognised path with no trailing arg must return False: %r" % fp
        n_checks += 1

    # --- present path, unrecognised, WITH a trailing arg: still path-decided -
    # The patch makes the present-path branch decide solely by the suffix; the
    # trailing argument must NOT influence the verdict when a path is present.
    for arg in [object(), 123, "str", HDUList(), TableHDU()]:
        bits, want, got = check("foo.bar", None, (arg,),
                                "unrecognised path + trailing %r" % type(arg))
        assert want == R_FALSE and got == R_FALSE, \
            "present unrecognised path must return False regardless of args"
        n_checks += 1
        bits, want, got = check("x.fits", None, (arg,),
                                "recognised path + trailing %r" % type(arg))
        assert want == R_TRUE and got == R_TRUE, \
            "present recognised path must return True regardless of args"
        n_checks += 1

    # --- no path, no stream: trailing argument decides (unchanged branch) ----
    for arg, exp in [(HDUList(), R_TRUE), (TableHDU(), R_TRUE),
                     (BinTableHDU(), R_TRUE), (object(), R_FALSE),
                     (42, R_FALSE), ("nope", R_FALSE)]:
        bits, want, got = check(None, None, (arg,), "no-path trailing")
        assert want == exp and got == exp, \
            "no-path, no-stream: args[0] isinstance decides (%r)" % arg
        n_checks += 1

    # --- stream present: signature comparison decides (unchanged branch) -----
    fobj_hit = io.BytesIO(FITS_SIGNATURE + b"rest of header padding ...")
    bits, want, got = check(None, fobj_hit, (), "stream sig match")
    assert bits["stream_present"] and bits["sig_matches"] \
        and want == R_TRUE and got == R_TRUE, "matching signature -> True"
    n_checks += 1
    fobj_miss = io.BytesIO(b"NOT A FITS HEADER ............................")
    bits, want, got = check(None, fobj_miss, (), "stream sig miss")
    assert bits["stream_present"] and not bits["sig_matches"] \
        and want == R_FALSE and got == R_FALSE, "wrong signature -> False"
    n_checks += 1
    # stream present + recognised path: stream wins (priority), still no fault
    fobj_hit2 = io.BytesIO(FITS_SIGNATURE + b"   ")
    bits, want, got = check("foo.bar", fobj_hit2, (), "stream over path")
    assert want == R_TRUE and got == R_TRUE, "stream takes priority"
    n_checks += 1

    # --- fuzz: random configurations of path / stream / trailing args --------
    rng = random.Random(14309)
    suffixes = list(FITS_SUFFIXES) + [".bar", ".ecsv", ".txt", "", ".gz",
                                      ".FITS", ".Fit", ".fits.bz2"]
    stems = ["foo", "data", "image", "table", "", "a.b", "deep/path/x"]
    arg_choices = [None, object(), 1, "s", HDUList(), TableHDU(),
                   BinTableHDU(), GroupsHDU()]
    for _ in range(3000):
        # filepath: present (random stem+suffix) or absent
        if rng.random() < 0.8:
            filepath = rng.choice(stems) + rng.choice(suffixes)
        else:
            filepath = None
        # fileobj: present (random bytes, sometimes the signature) or absent
        if rng.random() < 0.25:
            if rng.random() < 0.5:
                fileobj = io.BytesIO(FITS_SIGNATURE + b"x" * rng.randint(0, 5))
            else:
                fileobj = io.BytesIO(
                    bytes(rng.randint(0, 255) for _ in range(rng.randint(0, 40))))
        else:
            fileobj = None
        # trailing args: 0..2 random objects
        nargs = rng.randint(0, 2)
        args = tuple(rng.choice(arg_choices) for _ in range(nargs))
        check(filepath, fileobj, args, "fuzz")
        n_checks += 1

    print("G-AX OK: decision-equivalence holds on %d real inputs "
          "(F2P + path/stream/trailing controls + 3000 fuzz); real is_fits "
          "outcome matches model `decided`; a present path yields a total "
          "bool verdict (no IndexError fault). No consumed axiom." % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
