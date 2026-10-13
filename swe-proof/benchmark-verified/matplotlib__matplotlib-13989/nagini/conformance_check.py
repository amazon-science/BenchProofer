#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-13989
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model's carrier is a plain
``Dict[int, int]`` and the impl region is ordinary Python, so no PSeq shim is
needed; the @Pure helpers ``KEY_RANGE`` / ``KEY_DENSITY`` copy over as plain
functions. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md --
``matplotlib.axes.Axes.hist``, observed at the exact point the model
abstracts: the keyword-options mapping the method forwards to
``numpy.histogram`` for each dataset. The observation is made by swapping
``numpy.histogram`` for a capture-and-abort wrapper for the duration of one
``ax.hist`` call: the wrapper records the keyword arguments of the first
forwarded call and raises, so the real method runs its genuine
options-assembly logic up to the forwarding point and no drawing happens.
The explicit ``weights=`` keyword at the call site is passed separately from
the assembled options mapping and is removed from the observation. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched package importable.

Type bridge (mapping.md section 2):
  * option-name tokens: the real string key 'range' <-> KEY_RANGE() == 0 and
    the real string key 'density' <-> KEY_DENSITY() == 1;
  * ``range_value`` is an opaque token whose only observed property is
    preservation: the shadow entry under KEY_RANGE() must equal the supplied
    token exactly when the real forwarded mapping carries 'range' with the
    value the surrounding method recorded for it (the caller-supplied
    interval, or the data-derived interval when no interval was supplied);
  * the normalisation flag records as the constant 1 in the shadow and as a
    truthy value in the real mapping;
  * the model's boolean parameters are the resolved runtime conditions of
    the real method: ``multi_precomputed`` <-> (input non-empty AND more than
    one dataset), ``density`` <-> the resolved normalisation request (either
    spelling of the keyword), ``stacked`` <-> the resolved stacking flag
    (the explicit argument, or the stacking histogram type).

Every generated call drives the REAL method with concrete datasets / keyword
arguments chosen so the resolved conditions cover all combinations, then
compares the token-mapped observation against the shadow's returned mapping
(key set AND per-key values).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz calls.
Pinned fuzz seed: 13989.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys
import warnings

import numpy as np

SEED = 13989
N_FUZZ = 100_000

# Sentinel for "entry present but with an unexpected value" so a value
# mismatch surfaces as a dict disagreement rather than a silent pass.
BAD_VALUE = -999


# --- pure helpers from model.py, contracts stripped ---------------------------

def KEY_RANGE():
    # Option-name token under which an explicit value range is recorded.
    return 0


def KEY_DENSITY():
    # Option-name token under which the normalisation flag is recorded.
    return 1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def assemble_binning_options(multi_precomputed, density, stacked, range_value):
    hist_kwargs = {}  # type: dict
    if not multi_precomputed:
        hist_kwargs[KEY_RANGE()] = range_value
    if density and not stacked:
        hist_kwargs[KEY_DENSITY()] = 1
    return hist_kwargs


# --- oracle: observe the real method's forwarded options mapping --------------

class _Captured(Exception):
    """Raised by the capture wrapper to abort the real method at the
    forwarding point (after the options mapping is fully assembled)."""


def make_axes():
    # Backend-free figure: no GUI, no pyplot state.
    from matplotlib.figure import Figure
    fig = Figure()
    return fig.add_subplot(1, 1, 1)


def real_forwarded_options(ax, x, bins, rng_arg, density_arg, weights,
                           stacked_arg, histtype, normed_arg):
    """Invoke the REAL ``Axes.hist`` and return the keyword-options mapping it
    forwards to ``numpy.histogram`` (the call site's explicit ``weights``
    keyword removed -- it is not part of the assembled options mapping)."""
    captured = {}
    real_histogram = np.histogram

    def capture(*args, **kwargs):
        captured.update(kwargs)
        raise _Captured()

    np.histogram = capture
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ax.hist(x, bins=bins, range=rng_arg, density=density_arg,
                    weights=weights, histtype=histtype, stacked=stacked_arg,
                    normed=normed_arg)
    except _Captured:
        pass
    finally:
        np.histogram = real_histogram
    opts = dict(captured)
    opts.pop('weights', None)
    return opts


def range_values_equal(observed, expected):
    """Exact equality of the recorded interval (None, or a pair of floats;
    float64 round-trips the generated values exactly)."""
    if observed is None or expected is None:
        return observed is None and expected is None
    return (len(observed) == 2 and len(expected) == 2
            and float(observed[0]) == float(expected[0])
            and float(observed[1]) == float(expected[1]))


def observed_token_map(opts, expected_range, token):
    """Map the real string-keyed options mapping to the model's int-token
    carrier: 'range' -> KEY_RANGE() (value = the opaque token iff the
    recorded interval is exactly the one the method recorded for this call),
    'density' -> KEY_DENSITY() (value = 1 iff the recorded flag is truthy)."""
    assert set(opts.keys()) <= {'range', 'density'}, (
        "unexpected option key forwarded to numpy.histogram: %r" % (opts,))
    out = {}
    if 'range' in opts:
        out[KEY_RANGE()] = (token if range_values_equal(opts['range'],
                                                        expected_range)
                            else BAD_VALUE)
    if 'density' in opts:
        out[KEY_DENSITY()] = 1 if opts['density'] else BAD_VALUE
    return out


# --- one differential trial ---------------------------------------------------

def run_case(ax, datasets, bins, rng_arg, density_arg, weights, stacked_arg,
             histtype, normed_arg, token):
    """Drive the real method with concrete inputs, resolve the model's
    boolean parameters from those same inputs (the mapping.md bridge), run
    the shadow, and return an error string on disagreement, else None."""
    # resolved runtime conditions (mapping.md section 2)
    input_empty = sum(len(d) for d in datasets) == 0
    nx = len(datasets)
    multi_precomputed = (not input_empty) and nx > 1
    density_resolved = bool(density_arg) or bool(normed_arg)
    stacked_resolved = bool(stacked_arg) or (histtype == 'barstacked')

    # the interval the method records for the single-pass case: the supplied
    # one, or the data-derived one when none is supplied (None if no finite
    # data exists to derive it from)
    if rng_arg is not None:
        expected_range = rng_arg
    else:
        flat = [v for d in datasets for v in d]
        expected_range = (min(flat), max(flat)) if flat else None

    shadow = assemble_binning_options(multi_precomputed, density_resolved,
                                      stacked_resolved, token)

    opts = real_forwarded_options(ax, datasets, bins, rng_arg, density_arg,
                                  weights, stacked_arg, histtype, normed_arg)
    observed = observed_token_map(opts, expected_range, token)

    if observed != shadow:
        return ("DISAGREEMENT\n"
                "  datasets=%r\n  bins=%r range=%r density=%r weights=%r\n"
                "  stacked=%r histtype=%r normed=%r token=%r\n"
                "  resolved: multi_precomputed=%r density=%r stacked=%r\n"
                "  real forwarded options=%r -> token map %r\n"
                "  shadow=%r"
                % (datasets, bins, rng_arg, density_arg, weights,
                   stacked_arg, histtype, normed_arg, token,
                   multi_precomputed, density_resolved, stacked_resolved,
                   opts, observed, shadow))
    return None


# --- input generation ----------------------------------------------------------

def boundary_cases():
    """Hand-picked calls covering all resolved-condition combinations plus
    the input shapes that decide them: single vs multiple datasets, empty
    input (including multiple empty datasets), both spellings of the
    normalisation request, explicit stacking vs the stacking histogram type,
    supplied vs data-derived interval, and per-dataset weights."""
    one = [[0.25, 0.5, 0.75]]
    two = [[0.2, 0.4], [0.6, 0.8]]
    cases = []
    # all 8 combos of (multi, density, stacked) via concrete inputs
    for datasets in (one, two):
        for density_arg in (False, True):
            for stacked_arg in (False, True):
                cases.append(dict(datasets=datasets, bins=10,
                                  rng_arg=(0.0, 1.0), density_arg=density_arg,
                                  weights=None, stacked_arg=stacked_arg,
                                  histtype='bar', normed_arg=None))
    # empty input: single empty dataset, and several empty datasets (still
    # the single-pass side of the resolved condition)
    for datasets in ([[]], [[], []]):
        for density_arg in (False, True):
            cases.append(dict(datasets=datasets, bins=5, rng_arg=(0.0, 1.0),
                              density_arg=density_arg, weights=None,
                              stacked_arg=False, histtype='bar',
                              normed_arg=None))
    # stacking via the histogram type (resolves stacked even when the
    # explicit argument is off)
    cases.append(dict(datasets=two, bins=8, rng_arg=(0.0, 1.0),
                      density_arg=True, weights=None, stacked_arg=False,
                      histtype='barstacked', normed_arg=None))
    cases.append(dict(datasets=one, bins=8, rng_arg=(0.0, 1.0),
                      density_arg=True, weights=None, stacked_arg=False,
                      histtype='barstacked', normed_arg=None))
    # normalisation requested through the alternate keyword
    cases.append(dict(datasets=one, bins=10, rng_arg=(0.0, 1.0),
                      density_arg=None, weights=None, stacked_arg=False,
                      histtype='bar', normed_arg=True))
    cases.append(dict(datasets=two, bins=10, rng_arg=(0.0, 1.0),
                      density_arg=None, weights=None, stacked_arg=False,
                      histtype='bar', normed_arg=True))
    # no supplied interval: recorded interval is data-derived (single-pass)
    # or irrelevant (precomputed-bins side)
    cases.append(dict(datasets=one, bins=10, rng_arg=None, density_arg=True,
                      weights=None, stacked_arg=False, histtype='bar',
                      normed_arg=None))
    cases.append(dict(datasets=two, bins=10, rng_arg=None, density_arg=True,
                      weights=None, stacked_arg=False, histtype='bar',
                      normed_arg=None))
    cases.append(dict(datasets=[[]], bins=10, rng_arg=None, density_arg=True,
                      weights=None, stacked_arg=False, histtype='bar',
                      normed_arg=None))
    # per-dataset weights (forwarded separately from the options mapping)
    cases.append(dict(datasets=one, bins=10, rng_arg=(0.0, 1.0),
                      density_arg=True, weights=[[1.0, 2.0, 1.0]],
                      stacked_arg=False, histtype='bar', normed_arg=None))
    cases.append(dict(datasets=two, bins=10, rng_arg=(0.0, 1.0),
                      density_arg=True, weights=[[1.0, 2.0], [0.5, 3.0]],
                      stacked_arg=False, histtype='bar', normed_arg=None))
    # negative / wide intervals, three datasets
    cases.append(dict(datasets=[[-3.5, 2.25]], bins=4, rng_arg=(-10.0, 10.0),
                      density_arg=True, weights=None, stacked_arg=False,
                      histtype='bar', normed_arg=None))
    cases.append(dict(datasets=[[0.1], [0.2], [0.3]], bins=3,
                      rng_arg=(0.0, 1.0), density_arg=True, weights=None,
                      stacked_arg=False, histtype='bar', normed_arg=None))
    return cases


def rand_case(rng):
    nx = rng.choice([1, 1, 1, 2, 2, 3])
    if rng.random() < 0.03:
        datasets = [[] for _ in range(nx)]
    else:
        datasets = [[round(rng.uniform(-100.0, 100.0), 4)
                     for _ in range(rng.randint(1, 6))] for _ in range(nx)]
    if rng.random() < 0.1:
        rng_arg = None
    else:
        lo = round(rng.uniform(-200.0, 100.0), 4)
        hi = round(lo + rng.uniform(0.5, 300.0), 4)
        rng_arg = (lo, hi)
    # normalisation request: off / on via either keyword spelling
    roll = rng.random()
    if roll < 0.45:
        density_arg, normed_arg = False, None
    elif roll < 0.9:
        density_arg, normed_arg = True, None
    else:
        density_arg, normed_arg = None, True
    stacked_arg = rng.random() < 0.4
    histtype = 'barstacked' if rng.random() < 0.1 else 'bar'
    weights = None
    if rng.random() < 0.15 and all(len(d) > 0 for d in datasets):
        weights = [[round(rng.uniform(0.1, 5.0), 3) for _ in d]
                   for d in datasets]
    token = rng.randint(1, 10 ** 9)
    return dict(datasets=datasets, bins=rng.randint(1, 20), rng_arg=rng_arg,
                density_arg=density_arg, weights=weights,
                stacked_arg=stacked_arg, histtype=histtype,
                normed_arg=normed_arg), token


def main():
    ax = make_axes()

    checked = 0
    bcases = boundary_cases()
    for i, case in enumerate(bcases):
        err = run_case(ax, token=1000 + i, **case)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        case, token = rand_case(rng)
        err = run_case(ax, token=token, **case)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == the real method's forwarded options "
          "mapping on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(bcases), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
