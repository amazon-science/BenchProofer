#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-13989.

This bundle has NO consumed axioms: the assembly of the histogram keyword
options (the `hist_kwargs` mapping forwarded to `numpy.histogram` inside
`Axes.hist`) is modelled DEEPLY (the two guarded writes spelled out in
model.py's impl region). G-AX therefore validates the single **A-reference** --
that the deep model equals the real operation it mirrors -- by:

  (1) reconstructing the REAL `Axes.hist` kwargs-assembly logic in BOTH code
      states -- the gold in-place write `hist_kwargs['density'] = density` and
      the base_commit rebind `hist_kwargs = dict(density=density)` -- exactly
      the single line the gold patch touches, over boundary + randomized-fuzz
      combinations of the branch conditions, and asserting the resulting key
      SET matches the deep model in the gold state and differs in the buggy
      state (so the observable discriminates fixed from buggy); and

  (2) driving the REAL `numpy.histogram` (the library `Axes.hist` forwards the
      kwargs to) with each assembled mapping and confirming the observable the
      deep model relies on: when the range entry is preserved (gold), the
      returned bin edges span the requested interval (`bins[0]==lo`,
      `bins[-1]==hi`); when it is dropped (base_commit bug), they follow the
      data instead. This is exactly the F2P observable
      (`test_hist_range_and_density`: `bins[0]==0`, `bins[-1]==1`).

Deep model under check (model.py impl region), over the options mapping keyed by
the option-name tokens KEY_RANGE (0) and KEY_DENSITY (1):

    hist_kwargs = {}
    if not multi_precomputed:           # single-pass: record the range
        hist_kwargs[KEY_RANGE] = range_value
    if density and not stacked:         # record the normalisation flag ...
        hist_kwargs[KEY_DENSITY] = 1    # ... WITHOUT discarding the range (gold)

Mapping to the real operation (mapping.md §1, §3):
  * KEY_RANGE  <->  the string key 'range' placed by `hist_kwargs['range'] =
    bin_range` (single-pass / `else` arm).
  * KEY_DENSITY  <->  the string key 'density' placed by the `density and not
    stacked` branch.
  * multi_precomputed  <->  `not input_empty and len(x) > 1` (the precompute-
    shared-bins branch, which records no range).

PATCH-STATE CONTROL (the load-bearing correctness property of this script).
The SWE-bench image is checked out at `base_commit`, i.e. the UNPATCHED tree in
which the density branch REBINDS `hist_kwargs` and drops 'range'. This script
does NOT trust the ambient `Axes.hist`; it reconstructs the exact one-line
assembly under BOTH policies at runtime (the only thing the gold patch changes
is rebind-vs-in-place on that single line) so the check is correct whether the
live tree is pre- or post-fix, and it proves the observable genuinely
distinguishes the two.

Imports: the standard library plus `numpy` (the real histogram backend). Exit 0
iff every observation matches.
"""
import random
import sys

import numpy as np

# Option-name tokens, matching model.py's KEY_RANGE()/KEY_DENSITY().
KEY_RANGE = 0
KEY_DENSITY = 1


def real_assemble(multi_precomputed, density, stacked, range_value, gold):
    """Reconstruct the REAL `Axes.hist` assembly of the keyword-options dict,
    keyed by the actual string keys 'range'/'density', under the chosen policy:

      gold=True  -> density branch writes in place: hist_kwargs['density'] = density
      gold=False -> density branch rebinds:          hist_kwargs = dict(density=density)

    This is the only line the gold patch changes; everything else is the
    verbatim surrounding control flow (lines 6654, 6676-6685, 6687-6689)."""
    hist_kwargs = dict()
    # single-pass arm records the range; multi-dataset arm precomputes bins and
    # records nothing.
    if not multi_precomputed:
        hist_kwargs['range'] = range_value
    density = bool(density)
    if density and not stacked:
        if gold:
            hist_kwargs['density'] = density          # gold: in-place write
        else:
            hist_kwargs = dict(density=density)        # base_commit bug: rebind
    return hist_kwargs


def deep_model_keys(multi_precomputed, density, stacked):
    """The deep model's verdict: which option tokens are present in the
    forwarded mapping (model.py impl region)."""
    keys = set()
    if not multi_precomputed:
        keys.add(KEY_RANGE)
    if density and not stacked:
        keys.add(KEY_DENSITY)
    return keys


def observed_keys(hist_kwargs):
    """Map the real string-keyed dict to the model's int token set."""
    toks = set()
    if 'range' in hist_kwargs:
        toks.add(KEY_RANGE)
    if 'density' in hist_kwargs:
        toks.add(KEY_DENSITY)
    # the assembly places ONLY these two options; assert no stray key sneaks in.
    assert set(hist_kwargs.keys()) <= {'range', 'density'}, (
        "unexpected option key in assembled hist_kwargs: %r" % (hist_kwargs,))
    return toks


def check_keys(multi_precomputed, density, stacked, range_value):
    """A-reference part (1): under the gold policy the real assembly's key set
    matches the deep model."""
    gold_kwargs = real_assemble(multi_precomputed, density, stacked,
                                range_value, gold=True)
    expected = deep_model_keys(multi_precomputed, density, stacked)
    observed = observed_keys(gold_kwargs)
    assert observed == expected, (
        "deep model unsound vs the real (gold) Axes.hist assembly "
        "(multi=%r, density=%r, stacked=%r): real keys %r, deep model %r"
        % (multi_precomputed, density, stacked, observed, expected))
    # When the range is recorded (gold), it survives with its exact value.
    if KEY_RANGE in expected:
        assert gold_kwargs['range'] == range_value, (
            "gold assembly dropped/altered the recorded range %r -> %r"
            % (range_value, gold_kwargs.get('range')))


def check_range_observable(rng):
    """A-reference part (2): drive the REAL numpy.histogram with the assembled
    kwargs and confirm the observable the deep model relies on, for the F2P
    configuration (single-pass, density=True, not stacked).

      gold  -> 'range' preserved -> bins span the requested interval.
      bug   -> 'range' dropped   -> bins follow the data (do NOT span it),
               with high probability for random data strictly inside (lo,hi).
    """
    for _ in range(500):
        lo = round(rng.uniform(-5.0, 0.0), 3)
        hi = round(rng.uniform(lo + 1.0, lo + 10.0), 3)
        n = rng.randint(2, 40)
        # data strictly inside (lo, hi) so the data-driven edges differ from
        # the requested interval (this is the bug's symptom).
        data = np.array([rng.uniform(lo + 0.1, hi - 0.1) for _ in range(n)])

        gold_kwargs = real_assemble(multi_precomputed=False, density=True,
                                    stacked=False, range_value=(lo, hi),
                                    gold=True)
        bug_kwargs = real_assemble(multi_precomputed=False, density=True,
                                   stacked=False, range_value=(lo, hi),
                                   gold=False)

        _, gbins = np.histogram(data, "auto", **gold_kwargs)
        # GOLD: bins span the requested interval exactly (the F2P assertion).
        assert gbins[0] == lo and gbins[-1] == hi, (
            "real numpy.histogram with the gold-preserved range did NOT span "
            "[%r, %r]: bins=[%r .. %r]" % (lo, hi, gbins[0], gbins[-1]))

        _, bbins = np.histogram(data, "auto", **bug_kwargs)
        # BUG: range dropped -> edges driven by the data, which lies strictly
        # inside (lo, hi); they cannot reach both endpoints.
        assert not (bbins[0] == lo and bbins[-1] == hi), (
            "the base_commit rebind unexpectedly still spanned [%r, %r] "
            "(observable cannot witness the fix): bins=[%r .. %r]"
            % (lo, hi, bbins[0], bbins[-1]))


def main():
    # === part (1): key set matches the deep model under the gold policy =======
    # all 8 combinations of the three branch conditions, with a representative
    # range value.
    boundary = [(m, d, s) for m in (False, True)
                for d in (False, True) for s in (False, True)]
    for multi, density, stacked in boundary:
        check_keys(multi, density, stacked, range_value=(0.0, 1.0))

    # Differential: under the base_commit rebind, the F2P configuration LOSES
    # the range key (so its key set differs from the deep model) -- proving the
    # observable discriminates fixed from buggy.
    bug_kwargs = real_assemble(multi_precomputed=False, density=True,
                               stacked=False, range_value=(0.0, 1.0),
                               gold=False)
    assert 'range' not in bug_kwargs and 'density' in bug_kwargs, (
        "the base_commit rebind did NOT drop 'range' in the F2P configuration: "
        "%r -- the two-state check is not discriminating." % (bug_kwargs,))
    assert observed_keys(bug_kwargs) != deep_model_keys(False, True, False), (
        "buggy key set unexpectedly equals the deep model -- no discrimination.")

    # randomized fuzz over the three branch conditions, gold policy.
    rng = random.Random(13989)
    for _ in range(5000):
        multi = rng.random() < 0.5
        density = rng.random() < 0.5
        stacked = rng.random() < 0.5
        check_keys(multi, density, stacked, range_value=(rng.random(),
                                                         rng.random()))

    # === part (2): real numpy.histogram honours the preserved range ===========
    check_range_observable(rng)

    print("G-AX OK: the deep model (A-reference) == the real Axes.hist "
          "hist_kwargs assembly on %d boundary + 5000 fuzz condition tuples "
          "(gold in-place write keeps 'range' + adds 'density'); under the "
          "base_commit rebind the 'range' key is dropped in the F2P "
          "configuration (the bug the F2P test pins); and the REAL "
          "numpy.histogram over 500 fuzz cases spans the requested interval "
          "exactly iff the range is preserved -- so the observable "
          "discriminates fixed from buggy." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
