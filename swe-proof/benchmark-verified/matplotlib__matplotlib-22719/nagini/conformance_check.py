#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-22719 (nagini).

SHADOW: the impl regions of model.py's two decision functions, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helper `all_classify` copies over as a plain function with the PSeq
shim (`drop(1)` -> `s[1:]` on a plain sequence); the impl bodies themselves do
not call it (only stripped Assert lines did), so it is kept for an internal
consistency cross-check only. There are no @ContractOnly callees in this
bundle.

ORACLE: the REAL repo functions the model models per mapping.md --
`matplotlib.category.StrCategoryConverter.convert` (whether the numeric
pass-through deprecation advisory is emitted) and
`matplotlib.category.UnitData.update` (whether the informational advisory
about all-parsable category labels is logged). The gate applies the diff to
/testbed before this script runs (PYTHONPATH=/testbed); this script never
applies any diff itself. Advisory emission is observed directly: a recorded
MatplotlibDeprecationWarning during convert, and an INFO record on the
module logger during update (each call site has exactly one such advisory,
so presence of the category/level is the decision bit).

TYPE BRIDGE (mapping.md section 2): a real input sequence maps to the model's
List[int] of per-element classification flags, computed by the UNCHANGED real
per-element classifiers themselves:
  convert: flags[k] = 1 iff element k is numeric-like and not text
           (the same probe the real code performs per element);
  update:  flags[k] = 1 iff element k is a string parsable as a float or a
           date (UnitData._str_is_convertible, the real classifier).
The real update fold walks unique values only, but a universal verdict over
the unique set equals the one over the full sequence (per-element
classification is position- and duplicate-independent), so flags are taken
over the full sequence, matching the model. The Requires (list_pred) holds by
construction for any Python list of ints.

>= 1e5 Requires-satisfying inputs: structured boundary cases for both sites
(the empty sequence, singletons, mixed sequences, scalars, duplicates) plus
50000 fuzz sequences per site. PINNED SEED: 227190.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + numpy only (no hypothesis needed).
"""
import json
import logging
import random
import sys
import warnings

SEED = 227190
N_FUZZ_PER_SITE = 50_000


# --- pure helper from model.py, contracts stripped, PSeq -> plain sequence ---

def all_classify(s):
    """Whether EVERY element of *s* satisfies the per-element classification
    (its flag is non-zero). The empty sequence satisfies this vacuously
    (`True`). Front-recursive so one unfold is available to callers."""
    if len(s) == 0:
        return True
    return (s[0] != 0) and all_classify(s[1:])


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def should_warn_numeric_passthrough(flags):
    every = True
    i = len(flags)
    while i > 0:
        c = flags[i - 1]
        if c == 0:
            every = False
        i = i - 1
    return len(flags) > 0 and every


def should_log_numeric_strings(flags):
    classify = True
    i = len(flags)
    while i > 0:
        c = flags[i - 1]
        if c == 0:
            classify = False
        i = i - 1
    return len(flags) > 0 and classify


# --- bridges: real input sequence -> model flag list -------------------------

def convert_flags(value, np, units, _api):
    """Per-element classification flags for the convert site, computed with
    the same array layer and the same unchanged per-element probe the real
    code uses (the probe is itself deprecated upstream, so it is queried
    under the same suppression context the real code uses)."""
    values = np.atleast_1d(np.array(value, dtype=object))
    flags = []
    with _api.suppress_matplotlib_deprecation_warning():
        for v in values:
            ok = (units.ConversionInterface.is_numlike(v)
                  and not isinstance(v, (str, bytes)))
            flags.append(1 if ok else 0)
    return flags


def update_flags(data, np, UnitData):
    """Per-element classification flags for the update site, computed with
    the same array layer and the real unchanged parsability classifier,
    over the FULL sequence (universal verdicts over the full sequence and
    over its unique values coincide)."""
    arr = np.atleast_1d(np.array(data, dtype=object))
    return [1 if UnitData._str_is_convertible(v) else 0 for v in arr]


# --- real observable outcomes -------------------------------------------------

def real_convert_emits(value, category, MplDeprecation):
    """Run the REAL convert on a fresh unit mapping and report whether the
    deprecation advisory was emitted. Later element-type checks may reject
    some mixed inputs with an exception; the emission decision is made
    before those, so the observation stays valid."""
    unit = category.UnitData()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        try:
            category.StrCategoryConverter.convert(value, unit, None)
        except (TypeError, ValueError):
            pass
    return any(issubclass(w.category, MplDeprecation) for w in rec)


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.records = []

    def emit(self, record):
        self.records.append(record)


def real_update_emits(data, category):
    """Run the REAL update on a fresh unit mapping and report whether the
    informational advisory was logged on the module logger."""
    logger = logging.getLogger("matplotlib.category")
    handler = _CaptureHandler()
    old_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        ud = category.UnitData()
        ud.update(data)
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
    return any(r.levelno == logging.INFO for r in handler.records)


# --- differential drivers ------------------------------------------------------

def check_convert(value, mods):
    np, category, units, _api, MplDeprecation = mods
    flags = convert_flags(value, np, units, _api)
    shadow = should_warn_numeric_passthrough(flags)
    # internal consistency: impl == the pure characterization it verifies to
    assert shadow == (len(flags) > 0 and all_classify(tuple(flags)))
    real = real_convert_emits(value, category, MplDeprecation)
    if bool(real) != bool(shadow):
        return ("DISAGREEMENT (convert site)\n  value=%r\n  flags=%r\n"
                "  shadow=%r  real=%r" % (value, flags, shadow, real))
    return None


def check_update(data, mods):
    np, category, units, _api, MplDeprecation = mods
    flags = update_flags(data, np, category.UnitData)
    shadow = should_log_numeric_strings(flags)
    assert shadow == (len(flags) > 0 and all_classify(tuple(flags)))
    real = real_update_emits(data, category)
    if bool(real) != bool(shadow):
        return ("DISAGREEMENT (update site)\n  data=%r\n  flags=%r\n"
                "  shadow=%r  real=%r" % (data, flags, shadow, real))
    return None


def convert_boundary_cases(np):
    return [
        [],                       # the empty sequence: advisory must be off
        np.array([], dtype=object),
        [1],
        [1.5],
        [0],                      # zero is still a number
        [-3],
        [True],                   # bool is numeric-like
        ["a"],                    # single non-numeric element
        [b"b"],                   # bytes are excluded from the numeric class
        ["1.5"],                  # numeric-LOOKING string is still a string
        3,                        # scalar number -> one-element sequence
        2.25,
        "abc",                    # scalar string -> one-element sequence
        [1, 2, 3],
        [1, "a"],                 # mixed: not every element classifies
        ["a", 1],
        ["a", "b"],
        [None],                   # not a number
        [1, None, 2],
        [1.0, 2, -7, 1e9],
        [float("nan")],           # nan is still numeric-like
        [complex(1, 2)],          # complex is numeric-like
    ]


def update_boundary_cases(np):
    return [
        [],                       # the empty sequence: advisory must be off
        np.array([], dtype=object),
        ["1"],
        ["1.5"],
        ["-2e3"],
        ["2020-01-01"],           # parsable as a date
        ["hello_zzz"],            # parsable as neither float nor date
        [""],
        "3.5",                    # scalar string -> one-element sequence
        "not_a_number_zzz",
        [b"2.5"],                 # bytes parse via float()
        [b"zzz_bytes"],
        ["1", "2", "3"],
        ["1", "hello_zzz"],
        ["hello_zzz", "1"],
        ["1", "1", "1"],          # duplicates: unique-set fold, same verdict
        ["hello_zzz", "hello_zzz"],
        ["3.5", "2020-01-01", "-7"],
        ["nan"],                  # float('nan') parses
        ["inf"],
    ]


def main():
    # REAL repo symbols (the module the model models, per mapping.md):
    import numpy as np
    from matplotlib import _api, category, units
    from matplotlib._api.deprecation import MatplotlibDeprecationWarning

    mods = (np, category, units, _api, MatplotlibDeprecationWarning)
    checked = 0
    n_boundary = 0

    for value in convert_boundary_cases(np):
        err = check_convert(value, mods)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1
    for data in update_boundary_cases(np):
        err = check_update(data, mods)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)

    # convert-site fuzz: sequences over numeric-like and non-numeric elements
    numeric_pool = [0, 1, -1, 3.5, -2.25, 1e12, float("nan"), True,
                    complex(0, 1), 7, 0.0]
    non_numeric_pool = ["a", "1.5", "xyz", "", b"raw", None, b"1"]
    for _ in range(N_FUZZ_PER_SITE):
        n = rng.randint(0, 8)
        if n == 0:
            value = []
        elif rng.random() < 0.10:
            # scalar input (one-element sequence after normalization)
            value = rng.choice(numeric_pool if rng.random() < 0.5
                               else ["s", "1.5", "abc"])
        else:
            p_num = rng.choice([0.0, 0.3, 0.7, 1.0])
            value = [rng.choice(numeric_pool) if rng.random() < p_num
                     else rng.choice(non_numeric_pool) for _ in range(n)]
        err = check_convert(value, mods)
        if err:
            print(err)
            return 1
        checked += 1

    # update-site fuzz: sequences of str/bytes labels, parsable or not
    parsable_pool = ["1", "3.14", "-2e5", "0", "2020-01-01", "Jan 3 2021",
                     "12:30", b"2.5", "nan", "1962-03-30"]
    unparsable_pool = ["hello_zzz", "qq_rr_ss", "%%##", b"zzz_bytes",
                       "", "12,34,56,78zz"]
    for _ in range(N_FUZZ_PER_SITE):
        n = rng.randint(0, 8)
        if n == 0:
            data = []
        elif rng.random() < 0.10:
            data = rng.choice(parsable_pool[:6] + unparsable_pool[:3])
        else:
            p_ok = rng.choice([0.0, 0.3, 0.7, 1.0])
            data = [rng.choice(parsable_pool) if rng.random() < p_ok
                    else rng.choice(unparsable_pool) for _ in range(n)]
            if rng.random() < 0.3 and len(data) > 1:
                # inject duplicates: the unique-set fold must not change the verdict
                data[rng.randrange(len(data))] = data[0]
        err = check_update(data, mods)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow decision impls == real advisory emission on %d "
          "inputs (%d boundary + 2x%d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ_PER_SITE, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
