#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24870 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`chooseLevelArg`)
              transliterated to Python over the real repo values, via the
              mapping.md bijection (Bool ↔ bool; int ↔ ('count', n); list ↔
              ('explicit', [floats])). The impl is all-R/I (no axiom), so the
              shadow is the full branch logic.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `ContourSet._process_contour_level_args(args, z_dtype)` selection
              branch, run in-container after patch.diff is applied. We isolate
              the *changed selection* (which `levels_arg` it picks) from the
              UNCHANGED downstream (`isinstance(..., Integral)` →
              `_autolev`/`np.asarray`, level filtering) by giving the real method
              a fake `self`: `_autolev(n)` raises a sentinel capturing the int
              count, and a wide (zmin,zmax) lets the explicit-list path finish
              untrimmed. Thus the only thing observed is the selection — the R/I
              content of the impl, exactly per §4.1.

The same `_process_contour_level_args` is the selection routine for BOTH
`contour`/`contourf` and `tricontour`/`tricontourf` (it lives only in
contour.py; TriContourSet inherits it). So this single check covers the
selection legs of all four F2P call paths; the tri `_contour_args` /
`_check_xyz` hunks are dtype-plumbing (refinement.md §B), which feed the
`z_dtype` argument we vary directly here.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + numpy
(repo dep) only. The fuzz seed is pinned (mapping.md §5) for a deterministic
verdict.
"""
import os
import random
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

SEED = 24870
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean chooseLevelArg, transliterated ------------
def shadow_choose(levels_kw_set, levels_kw, pos_given, pos_arg,
                  bool_field, filled):
    """chooseLevelArg's do block, transliterated. Returns a normalized tag
    ('count', n) | ('explicit', [floats])."""
    if levels_kw_set:
        out = levels_kw
    else:
        if pos_given:
            out = pos_arg
        else:
            if bool_field:
                if filled:
                    out = ('explicit', [0.0, 0.5, 1.0])
                else:
                    out = ('explicit', [0.5])
            else:
                out = ('count', 7)
    return out


# --- the oracle: real patched _process_contour_level_args selection ----------
class _AutolevSentinel(Exception):
    def __init__(self, n):
        self.n = n


def _make_fake_self(filled):
    import numpy as np

    class _FakeCS:
        pass

    fake = _FakeCS()
    fake.filled = filled
    # Wide data range so the unchanged not-filled trimming keeps every level.
    fake.zmin = float("-inf")
    fake.zmax = float("inf")

    def _autolev(n):
        # The int → count path; capture n and stop before unchanged filtering.
        raise _AutolevSentinel(int(n))

    fake._autolev = _autolev
    # `self.levels` is set below per the levels-keyword flag by the caller.
    return fake


def oracle_choose(levels_kw_set, levels_kw, pos_given, pos_arg,
                  bool_field, filled):
    """Run the real patched selection and observe which levels_arg it picked."""
    import numpy as np
    from matplotlib.contour import ContourSet

    func = ContourSet._process_contour_level_args  # patched: takes z_dtype

    fake = _make_fake_self(filled)

    # Reconstruct the repo-side inputs from the abstract flags (mapping.md §3):
    #   self.levels is None  <-> not levels_kw_set
    if levels_kw_set:
        fake.levels = _to_repo_value(levels_kw)
    else:
        fake.levels = None
    #   args truthiness <-> pos_given; args[0] <-> pos_arg
    args = [_to_repo_value(pos_arg)] if pos_given else []
    #   np.issubdtype(z_dtype, bool) <-> bool_field
    z_dtype = np.dtype(bool) if bool_field else np.dtype(np.float64)

    try:
        func(fake, args, z_dtype)
    except _AutolevSentinel as s:
        return ('count', s.n)
    # Explicit-list path: self.levels is the np.asarray of the selected list.
    return ('explicit', [float(v) for v in np.asarray(fake.levels).tolist()])


def _to_repo_value(tag):
    """('count', n) -> python int n; ('explicit', xs) -> python list xs."""
    kind, payload = tag
    if kind == 'count':
        return int(payload)
    return list(payload)


# --- fuzzing -----------------------------------------------------------------
def _rand_levelarg(rng):
    """A representative levels_kw / pos_arg value: an int count, or a strictly
    increasing list of length >= 2 (so it survives the unchanged 'must be
    increasing' / 'filled needs >= 2 levels' downstream checks regardless of
    the filled flag)."""
    if rng.random() < 0.5:
        return ('count', rng.randint(0, 30))
    k = rng.randint(2, 6)
    start = rng.randint(-5, 5)
    step = rng.randint(1, 4)
    vals = [float(start + step * i) for i in range(k)]
    return ('explicit', vals)


def fuzz_cases(n, rng):
    bools = [False, True]
    # boundary: the full Boolean cube of the four flags, with simple values
    base_kw = ('count', 3)
    base_pos = ('explicit', [1.0, 2.0, 3.0])
    for lk in bools:
        for pg in bools:
            for bf in bools:
                for fl in bools:
                    yield (lk, base_kw, pg, base_pos, bf, fl)
    # the four F2P-tested boolean-field defaults explicitly
    yield (False, base_kw, False, base_pos, True, False)   # contour(bool)  -> [.5]
    yield (False, base_kw, False, base_pos, True, True)    # contourf(bool) -> [0,.5,1]
    yield (False, base_kw, False, base_pos, False, False)  # contour(float) -> 7
    yield (False, base_kw, False, base_pos, False, True)   # contourf(float)-> 7
    # randomized fuzz
    for _ in range(n):
        yield (
            rng.random() < 0.5, _rand_levelarg(rng),
            rng.random() < 0.5, _rand_levelarg(rng),
            rng.random() < 0.5, rng.random() < 0.5,
        )


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for case in fuzz_cases(N_FUZZ, rng):
        count += 1
        shadow = shadow_choose(*case)
        oracle = oracle_choose(*case)
        if shadow != oracle:
            disagreements.append((case, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for case, sh, orc in disagreements:
            print("  case=%r shadow=%r oracle=%r" % (case, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of chooseLevelArg agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
