#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14309 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (R_TRUE / R_FALSE /
R_FAULT / decided is not needed by the impl; only the result-code helpers are)
copy over as plain functions. The model is a pure control-flow decision over
boolean classification bits + an argument count, so no PSeq shim is needed.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL repo function the model models per mapping.md —
`astropy.io.fits.connect.is_fits(origin, filepath, fileobj, *args)`. The gate
applies the diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the module importable. This script never applies any diff itself.

Type bridge (mapping.md section 2): each runtime probe of the real predicate
maps to one model input —
  fileobj is not None                      -> stream_present: bool
  leading bytes == the FITS signature      -> sig_matches: bool
  filepath is not None                     -> path_present: bool
  filepath.lower().endswith(known suffixes)-> path_recognised: bool
  len(args)                                -> n_trailing: int >= 0
  isinstance(args[0], accepted HDU kinds)  -> first_trailing_accepted: bool
and the observable outcome maps to the model's result code: a returned bool
-> R_TRUE / R_FALSE; an IndexError from indexing an absent trailing argument
-> R_FAULT. The Requires (n_trailing >= 0; first_trailing_accepted only when
n_trailing >= 1) hold by construction for bits derived from real inputs.

>= 1e5 Requires-satisfying inputs: structured boundary cases (the F2P shape,
every branch of the priority cascade, path/stream/trailing-arg interactions)
plus 100000 fuzz configurations. Pinned fuzz seed: 143090.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (random; no hypothesis needed).
"""
import io
import json
import random
import sys

SEED = 143090
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped ---------------------------

def R_TRUE():
    # definite TRUE verdict
    return 1


def R_FALSE():
    # definite FALSE verdict
    return 0


def R_FAULT():
    # the predicate indexed an absent trailing argument (out-of-range fault)
    return -1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def is_recognised_input(stream_present, sig_matches,
                        path_present, path_recognised,
                        n_trailing, first_trailing_accepted):
    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
    # index the trailing-argument tuple.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    # Only reached when neither a stream nor a path name is present: the first
    # trailing argument decides; indexing it when there is none is the fault.
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()


# --- bridge: real call configuration <-> model classification bits ------------

FITS_SUFFIXES = (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")


def classification_bits(filepath, fileobj, args, signature, hdu_kinds):
    """Compute the model's input facts for one real call, mirroring the
    predicate's own probes (restores the stream position afterwards)."""
    stream_present = fileobj is not None
    sig_matches = False
    if stream_present:
        pos = fileobj.tell()
        sig = fileobj.read(30)
        fileobj.seek(pos)
        sig_matches = (sig == signature)
    path_present = filepath is not None
    path_recognised = path_present and filepath.lower().endswith(FITS_SUFFIXES)
    n_trailing = len(args)
    first_trailing_accepted = (
        n_trailing >= 1 and isinstance(args[0], hdu_kinds))
    return (stream_present, sig_matches, path_present, path_recognised,
            n_trailing, first_trailing_accepted)


def real_outcome(is_fits, origin, filepath, fileobj, args):
    """Run the REAL predicate and map its observable outcome to a model code:
    a returned bool -> TRUE/FALSE code; an IndexError (out-of-range access on
    the trailing-argument tuple) -> the FAULT code."""
    try:
        res = is_fits(origin, filepath, fileobj, *args)
    except IndexError:
        return R_FAULT()
    if res is not True and res is not False:
        return None  # non-bool: reported as a disagreement by the caller
    return R_TRUE() if res else R_FALSE()


def check_one(is_fits, signature, hdu_kinds, origin, filepath, fileobj, args):
    bits = classification_bits(filepath, fileobj, args, signature, hdu_kinds)
    # Requires hold by construction for bits derived from real inputs:
    assert bits[4] >= 0 and (not bits[5] or bits[4] >= 1)
    shadow = is_recognised_input(*bits)
    real = real_outcome(is_fits, origin, filepath, fileobj, args)
    if real != shadow:
        return ("DISAGREEMENT\n  origin=%r filepath=%r fileobj=%r args=%r\n"
                "  bits(stream_present,sig_matches,path_present,"
                "path_recognised,n_trailing,first_trailing_accepted)=%r\n"
                "  shadow=%r  real=%r" % (origin, filepath, fileobj, args,
                                          bits, shadow, real))
    return None


def boundary_cases(signature, hdu_kinds):
    """Structured cases covering every branch of the priority cascade."""
    HDUList = hdu_kinds[0]
    TableHDU = hdu_kinds[1]
    BinTableHDU = hdu_kinds[2]
    sig_hit = lambda: io.BytesIO(signature + b"trailing header bytes .....")
    sig_miss = lambda: io.BytesIO(b"NOT A MATCHING HEADER .................")
    cases = []
    # the F2P shape: present unrecognised path, no stream, no trailing args
    cases.append(("write", "foo.bar", None, ()))
    # present recognised paths, no trailing args
    for fp in [".fits", "a.FITS", "x.fit", "y.fits.gz", "z.FTS.GZ",
               "deep/path/img.fit.gz", "b.fts"]:
        cases.append(("write", fp, None, ()))
    # present unrecognised paths, no trailing args
    for fp in ["foo.bar", "table.ecsv", "data.txt", "noext", "x.fits.bz2",
               "archive.fit.zip", ""]:
        cases.append(("read", fp, None, ()))
    # present path (both kinds) WITH trailing args of assorted kinds: the
    # verdict must come from the path alone
    for arg in [object(), 123, "str", HDUList(), TableHDU()]:
        cases.append(("write", "foo.bar", None, (arg,)))
        cases.append(("write", "x.fits", None, (arg,)))
    # no path, no stream: trailing argument decides; empty args is the fault
    cases.append(("write", None, None, ()))
    for arg in [HDUList(), TableHDU(), BinTableHDU(), object(), 42, "nope"]:
        cases.append(("write", None, None, (arg,)))
        cases.append(("write", None, None, (arg, object())))
    # stream present: signature comparison decides; stream outranks the path
    cases.append(("read", None, sig_hit(), ()))
    cases.append(("read", None, sig_miss(), ()))
    cases.append(("read", "foo.bar", sig_hit(), ()))
    cases.append(("read", "x.fits", sig_miss(), ()))
    cases.append(("read", "foo.bar", sig_miss(), (HDUList(),)))
    cases.append(("read", None, sig_hit(), (object(),)))
    # short / empty streams (leading bytes cannot equal the signature)
    cases.append(("read", None, io.BytesIO(b""), ()))
    cases.append(("read", None, io.BytesIO(signature[:10]), ()))
    return cases


def main():
    # REAL repo symbols (the module the model models, per mapping.md):
    from astropy.io.fits import connect
    from astropy.io.fits import BinTableHDU, GroupsHDU, HDUList, TableHDU
    from astropy.io.fits.hdu.hdulist import FITS_SIGNATURE

    hdu_kinds = (HDUList, TableHDU, BinTableHDU, GroupsHDU)
    checked = 0

    n_boundary = 0
    for origin, filepath, fileobj, args in boundary_cases(FITS_SIGNATURE,
                                                          hdu_kinds):
        err = check_one(connect.is_fits, FITS_SIGNATURE, hdu_kinds,
                        origin, filepath, fileobj, args)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    suffixes = list(FITS_SUFFIXES) + [".bar", ".ecsv", ".txt", "", ".gz",
                                      ".FITS", ".Fit", ".fits.bz2", ".FIT.GZ"]
    stems = ["foo", "data", "image", "table", "", "a.b", "deep/path/x", "X"]
    arg_makers = [lambda: None, object, lambda: 1, lambda: "s", HDUList,
                  TableHDU, BinTableHDU, GroupsHDU, list, dict]
    for _ in range(N_FUZZ):
        origin = rng.choice(["read", "write"])
        if rng.random() < 0.7:
            filepath = rng.choice(stems) + rng.choice(suffixes)
        else:
            filepath = None
        if rng.random() < 0.25:
            if rng.random() < 0.5:
                fileobj = io.BytesIO(
                    FITS_SIGNATURE + b"x" * rng.randint(0, 6))
            else:
                fileobj = io.BytesIO(bytes(rng.randint(0, 255)
                                           for _ in range(rng.randint(0, 40))))
        else:
            fileobj = None
        nargs = rng.randint(0, 3)
        args = tuple(rng.choice(arg_makers)() for _ in range(nargs))
        err = check_one(connect.is_fits, FITS_SIGNATURE, hdu_kinds,
                        origin, filepath, fileobj, args)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real format-detection predicate on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
