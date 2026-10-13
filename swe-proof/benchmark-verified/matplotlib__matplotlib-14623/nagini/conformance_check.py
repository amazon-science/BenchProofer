#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-14623 (nagini).

Refutes the refinement leg: does the MODEL (`model.py::set_axis_interval`)
actually agree with the REAL gold-patched repository functions it claims to
model? Runs in-container with the gold patch already applied by the gate
(apply_gold=True, PYTHONPATH=/testbed), so `import matplotlib` resolves the
PATCHED source.

SHADOW -- the impl region of model.py, copied VERBATIM
------------------------------------------------------
`shadow_set_axis_interval` below is the text between `# impl-start` and
`# impl-end` in model.py with only the contract calls removed (here: the
`Requires`/`Ensures` block above `# impl-start` is simply not copied; the impl
region itself contains no Requires/Ensures/Invariant/Assert/Fold/Unfold/Acc/
MustTerminate call, so nothing inside it needed stripping). The
three-statement temp swap, the pre-conditioning `swapped` capture and the
statement order are preserved exactly -- no renaming, no `a, b = b, a`
"simplification". model.py's `# pure-start` region is empty ("no pure helpers
needed"), so there is no @Pure helper to copy. No PSeq/ToSeq carrier appears in
this model, so no sequence shim is needed.

The two @ContractOnly callees `conditioned_lo` / `conditioned_hi` have no body
to copy, so per the contract they CALL THE REAL REPO CALLEE they axiomatise
(mapping.md §1/§3.1): the conditioning composition

    lo, hi = <axis>.get_major_locator().nonsingular(lo, hi)
    lo, hi = <axis>.limit_range_for_scale(lo, hi)

on a real matplotlib axis of the site's scale. The axiom is therefore
EXERCISED here, not assumed (its own soundness against the model `Ensures` is
G-AX / axiom_check.py). Because the model axiomatises the pair-valued callee as
two pure component functions, `conditioned_lo` returns component 0 and
`conditioned_hi` component 1 of one real invocation.

ORACLE -- the REAL patched repo function, CALLED (not transliterated)
--------------------------------------------------------------------
mapping.md §1 binds `set_axis_interval` to five byte-identical patch hunks:

    Axes.set_xlim          lib/matplotlib/axes/_base.py:3161  (patched body 3264-3273)
    Axes.set_ylim          lib/matplotlib/axes/_base.py:3540  (patched body 3647-3653)
    Axes3D.set_xlim3d      lib/mpl_toolkits/mplot3d/axes3d.py:589
    Axes3D.set_ylim3d      lib/mpl_toolkits/mplot3d/axes3d.py:646
    Axes3D.set_zlim3d      lib/mpl_toolkits/mplot3d/axes3d.py:704

All five are directly drivable in this container -- a bare `plt.subplots()` /
`add_subplot(projection="3d")` axis is all the context they need -- so this
check DRIVES THE REAL FUNCTIONS and compares their stored interval against the
shadow. (This is deliberately stronger than the velvet sibling, whose docstring
records a transliteration of the patched limit-commit block; nothing here is
transliterated, so the check cannot be fooled by a misreading of the patched
source.) Each site's *stored* interval is read back two ways -- the value the
patched function returns AND the live view interval (`get_ylim()` /
`get_xlim()` / `get_*lim3d()`, i.e. `viewLim.interval*`, which is what the F2P
test `test_inverted_limits` asserts on) -- and both must equal the shadow.

Every modeled site is covered, on every scale the model's axiom referent covers
(mapping.md §3.1/§3.2: log = the bug's locus, linear = the coupled
`Locator.nonsingular` hunk). mplot3d limits are linear-only.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
The model's carrier is `int` endpoints in the order-faithful window
`(0, 1e15)`; the repo's endpoints are `float`. `to_repo(n) = float(n)` is the
bridge, applied exactly at the two places the model touches the repo (the
@ContractOnly conditioning callee) and at the oracle call; it is injective and
order-faithful on the `Requires` domain (`n < 1e15 < 2**53`, so every generated
int is exactly representable). The model's `Tuple[int, int]` result maps
componentwise to the stored `(left, right)` / `(bottom, top)` pair, and
comparison is EXACT float equality -- no tolerance -- because shadow and oracle
run the same real conditioning callee, so agreeing outputs must agree bit for
bit. Generation happens on the MODEL side (positive ints < 1e15), which keeps
every input inside `Requires(lo > 0 and hi > 0 and lo < 1e15 and hi < 1e15)`;
nothing is generated that the model's precondition excludes.

INPUTS
------
The modeled input space (int pairs in [1, 1e15)) is finite but astronomically
larger than 1e5, so: boundary cases first, then seeded fuzz. Boundary set
includes the exact F2P shape `(10, 1)` (the descending log request the gold
patch fixes) and its mirror `(1, 10)`, the domain floor `(1, 1)`, equal pairs,
adjacent-integer pairs just below the 1e15 bound, and wide-magnitude pairs.
Both impl branches are covered and the coverage is ASSERTED, not assumed: the
run fails if the `swapped` branch (descending request), the fall-through branch
(ascending request) or the equal-endpoint conditioning-expansion case was not
each exercised at every site -- an input generator that avoided the branch the
gold patch changed would fail here rather than pass silently.
Total >= 1e5 Requires-satisfying inputs across the sites (see the summary
line). Pinned seed: SEED = 14623 (recorded in mapping.md §G-CONF).

AUXILIARY REFUTATION
--------------------
Besides the shadow/oracle diff, each real stored interval is checked against the
discriminating orientation property the F2P test pins (descending request ->
descending stored interval, ascending -> ascending, equal -> strictly
ascending). Sensitivity was confirmed by hand: run against the UNPATCHED repo
(apply_gold=False) this script reports disagreements on every descending log
input, i.e. it is capable of failing.

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + matplotlib (the repo under test)
only.
"""
import json
import random
import sys
import warnings

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers "3d")

SEED = 14623
N_FUZZ_PRIMARY = 100_000   # the log set_ylim site: the bug's locus / F2P site
N_FUZZ_OTHER = 20_000      # every other modeled site

# The model's Requires domain, byte-for-byte: lo > 0 and hi > 0 and
# lo < 1000000000000000 and hi < 1000000000000000.
MAG_BOUND = 1000000000000000


def in_requires(lo, hi):
    return lo > 0 and hi > 0 and lo < MAG_BOUND and hi < MAG_BOUND


# --- type bridge (mapping.md §2) ---------------------------------------------

def to_repo(n):
    """model `int` endpoint -> repo `float` endpoint (injective and
    order-faithful on the Requires domain: n < 1e15 < 2**53)."""
    return float(n)


# --- the @ContractOnly conditioning callee: THE REAL REPO CALLEE -------------
# `_AXIS` is the real repo axis object (xaxis/yaxis/zaxis of a real Axes /
# Axes3D of the site's scale) the conditioning composition runs on; it is
# rebound per site by `run_site`.
_AXIS = None


def _real_conditioning(lo, hi):
    """The UNCHANGED repo callee axiomatised by conditioned_lo/conditioned_hi
    (mapping.md §3.1), invoked for real:

        lo, hi = <axis>.get_major_locator().nonsingular(lo, hi)
        lo, hi = <axis>.limit_range_for_scale(lo, hi)
    """
    a, b = _AXIS.get_major_locator().nonsingular(to_repo(lo), to_repo(hi))
    a, b = _AXIS.limit_range_for_scale(a, b)
    return float(a), float(b)


def conditioned_lo(lo, hi):
    """model.py @ContractOnly axiom -> first component of the REAL callee."""
    return _real_conditioning(lo, hi)[0]


def conditioned_hi(lo, hi):
    """model.py @ContractOnly axiom -> second component of the REAL callee."""
    return _real_conditioning(lo, hi)[1]


# --- SHADOW: model.py impl region, verbatim (contracts stripped) -------------

def shadow_set_axis_interval(lo, hi):
    # impl-start  (copied verbatim from model.py; nothing restructured)
    swapped = lo > hi
    a = conditioned_lo(lo, hi)
    b = conditioned_hi(lo, hi)
    # The conditioning normalises to strictly ascending order; the requested
    # orientation, captured before conditioning, is restored afterwards.
    if swapped:
        # caller requested descending: restore the requested orientation.
        tmp = a
        a = b
        b = tmp
    return (a, b)
    # impl-end


# --- ORACLE: the five real patched repo functions, driven --------------------

class Site:
    """One modeled repo site: the real patched setter + the live view-interval
    reader, on a real axis of the given scale."""

    def __init__(self, key, symbol, scale, make):
        self.key = key
        self.symbol = symbol
        self.scale = scale
        self._make = make
        self.fig = None
        self.axis = None
        self._set = None
        self._get = None

    def open(self):
        self.fig, self.axis, self._set, self._get = self._make()

    def close(self):
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None

    def call(self, lo, hi):
        """Drive the REAL patched function on the bridged float endpoints.
        Returns (returned_pair, stored_view_pair)."""
        returned = self._set(to_repo(lo), to_repo(hi))
        stored = self._get()
        return ((float(returned[0]), float(returned[1])),
                (float(stored[0]), float(stored[1])))


def _make_2d(which, scale):
    def make():
        fig, ax = plt.subplots()
        if which == "y":
            ax.set_yscale(scale)
            return fig, ax.yaxis, ax.set_ylim, ax.get_ylim
        ax.set_xscale(scale)
        return fig, ax.xaxis, ax.set_xlim, ax.get_xlim
    return make


def _make_3d(which):
    def make():
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        if which == "x":
            return fig, ax.xaxis, ax.set_xlim3d, ax.get_xlim3d
        if which == "y":
            return fig, ax.yaxis, ax.set_ylim3d, ax.get_ylim3d
        return fig, ax.zaxis, ax.set_zlim3d, ax.get_zlim3d
    return make


def sites():
    return [
        # the bug's locus and the F2P site: descending limits on a log y axis
        Site("set_ylim/log", "matplotlib.axes._base._AxesBase.set_ylim",
             "log", _make_2d("y", "log")),
        Site("set_ylim/linear", "matplotlib.axes._base._AxesBase.set_ylim",
             "linear", _make_2d("y", "linear")),
        Site("set_xlim/log", "matplotlib.axes._base._AxesBase.set_xlim",
             "log", _make_2d("x", "log")),
        Site("set_xlim/linear", "matplotlib.axes._base._AxesBase.set_xlim",
             "linear", _make_2d("x", "linear")),
        # mplot3d limits are linear-only
        Site("set_xlim3d", "mpl_toolkits.mplot3d.axes3d.Axes3D.set_xlim3d",
             "linear", _make_3d("x")),
        Site("set_ylim3d", "mpl_toolkits.mplot3d.axes3d.Axes3D.set_ylim3d",
             "linear", _make_3d("y")),
        Site("set_zlim3d", "mpl_toolkits.mplot3d.axes3d.Axes3D.set_zlim3d",
             "linear", _make_3d("z")),
    ]


# --- inputs ------------------------------------------------------------------

BOUNDARY = [
    (10, 1),                # the exact F2P shape: descending log request
    (1, 10),                # its ascending mirror
    (1, 1),                 # domain floor, equal (conditioning expansion)
    (1, 2), (2, 1),         # minimal distinct pairs, both orientations
    (5, 5), (10, 10),       # more equal pairs
    (3, 7), (7, 3),
    (1000, 1), (1, 1000),
    (100000, 1), (1, 100000),
    (1000000, 1), (1, 1000000),
    (10000000000, 1), (1, 10000000000),
    (1, MAG_BOUND - 1), (MAG_BOUND - 1, 1),          # widest in-domain pairs
    (MAG_BOUND - 2, MAG_BOUND - 1),                  # adjacent, just in domain
    (MAG_BOUND - 1, MAG_BOUND - 2),
    (MAG_BOUND - 1, MAG_BOUND - 1),                  # equal at the bound
    (42, 42), (999, 999),
]


def fuzz_pair(rng):
    """A Requires-satisfying int pair, log-uniform over the in-domain
    magnitude window so all 15 decades are exercised; ~2% equal pairs so the
    conditioning-expansion case keeps recurring; orientation drawn both ways
    because each endpoint is drawn independently."""
    lo = int(10.0 ** rng.uniform(0.0, 14.999)) + 1
    hi = int(10.0 ** rng.uniform(0.0, 14.999)) + 1
    lo = min(lo, MAG_BOUND - 1)
    hi = min(hi, MAG_BOUND - 1)
    if rng.random() < 0.02:
        hi = lo
    return lo, hi


# --- the differential check --------------------------------------------------

def run_site(site, n_fuzz, rng):
    """Diff the shadow against the real patched function at one site. Returns
    (checked, branch_counts, failures)."""
    global _AXIS
    site.open()
    _AXIS = site.axis
    checked = 0
    branches = {"swapped": 0, "straight": 0, "equal": 0}
    failures = []

    def check(lo, hi):
        nonlocal checked
        assert in_requires(lo, hi), ("generated input violates Requires",
                                     lo, hi)
        shadow = shadow_set_axis_interval(lo, hi)
        returned, stored = site.call(lo, hi)
        checked += 1
        if lo > hi:
            branches["swapped"] += 1
        elif lo < hi:
            branches["straight"] += 1
        else:
            branches["equal"] += 1
        if shadow != returned or shadow != stored:
            failures.append(
                "DISAGREEMENT at %s (%s, exact float equality):\n"
                "  input (model int carrier): lo=%d hi=%d  "
                "-> bridged floats (%r, %r)\n"
                "  shadow (model.py impl region, verbatim): %r\n"
                "  oracle (%s returned):                    %r\n"
                "  oracle (stored view interval):           %r"
                % (site.key, site.symbol, lo, hi, to_repo(lo), to_repo(hi),
                   shadow, site.symbol, returned, stored))
            return
        # Auxiliary refutation: the discriminating orientation property the
        # F2P test pins, asserted on the REAL stored interval.
        if lo > hi and not stored[0] > stored[1]:
            failures.append(
                "ORIENTATION LOST at %s: descending request (%d, %d) stored "
                "as %r (not descending)" % (site.key, lo, hi, stored))
        elif lo < hi and not stored[0] < stored[1]:
            failures.append(
                "ORIENTATION LOST at %s: ascending request (%d, %d) stored "
                "as %r (not ascending)" % (site.key, lo, hi, stored))
        elif lo == hi and not stored[0] < stored[1]:
            failures.append(
                "EXPANSION LOST at %s: equal request (%d, %d) stored as %r "
                "(not strictly ascending)" % (site.key, lo, hi, stored))

    for lo, hi in BOUNDARY:
        check(lo, hi)
        if failures:
            break
    if not failures:
        for _ in range(n_fuzz):
            lo, hi = fuzz_pair(rng)
            check(lo, hi)
            if failures:
                break

    site.close()
    _AXIS = None
    return checked, branches, failures


def main():
    # The patched setters warn (cbook._warn_external) on identical endpoints
    # and matplotlib chatters about the Agg backend; neither is behaviour.
    warnings.simplefilter("ignore")

    rng = random.Random(SEED)
    total = 0
    per_site = {}
    all_failures = []

    for site in sites():
        n_fuzz = (N_FUZZ_PRIMARY if site.key == "set_ylim/log"
                  else N_FUZZ_OTHER)
        checked, branches, failures = run_site(site, n_fuzz, rng)
        total += checked
        per_site[site.key] = checked
        all_failures.extend(failures)
        if failures:
            break
        # Branch coverage is ASSERTED, not assumed: a generator that skipped
        # the branch the gold patch changed must fail here, not pass quietly.
        for branch, count in branches.items():
            if count == 0:
                all_failures.append(
                    "INPUT COVERAGE GAP at %s: impl branch %r never exercised"
                    % (site.key, branch))
        if all_failures:
            break

    if all_failures:
        print("G-CONF FAIL: %d problem(s) over %d inputs (seed=%d)."
              % (len(all_failures), total, SEED))
        for line in all_failures[:10]:
            print(line)
        print(json.dumps({"status": "fail", "checked": total, "seed": SEED,
                          "disagreements": len(all_failures)}))
        return 1

    print("G-CONF OK: the verbatim model.py impl region (shadow, with the "
          "@ContractOnly conditioning axiom realized as the REAL "
          "locator.nonsingular + limit_range_for_scale callee) agrees "
          "EXACTLY with the real gold-patched repo functions %s on %d "
          "Requires-satisfying inputs (%d boundary incl. the F2P (10,1) "
          "descending-log request + seeded fuzz, seed=%d), per site %s; "
          "0 disagreements, and every real stored interval keeps the "
          "requested orientation."
          % (", ".join(sorted({s.symbol.rsplit('.', 1)[-1] for s in sites()})),
             total, len(BOUNDARY), SEED, json.dumps(per_site)))
    print(json.dumps({"status": "pass", "checked": total, "seed": SEED,
                      "disagreements": 0, "per_site": per_site,
                      "shadow": "direct (verbatim impl region, contracts "
                                "stripped; @ContractOnly callee = real repo "
                                "conditioning composition)",
                      "oracle": "real patched set_xlim/set_ylim/"
                                "set_xlim3d/set_ylim3d/set_zlim3d (called, "
                                "not transliterated)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
