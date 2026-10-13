#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13142
(nagini).

SHADOW: the impl region of model.py's `fit_and_label`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The
model IS Python: the backward best-trial scan and the persist-then-query
sequence run directly. The one @ContractOnly callee, `labels_of` (the
unchanged label-assignment query primitive, mapping.md section 3.1), calls
the REAL repo primitive per the contract for @ContractOnly callees: set the
held parameters on a real estimator via `_set_parameters`, then take the
row-wise argmax of the e-step responsibilities (`_e_step`), exactly the
query `fit_predict` itself uses. The pure helpers `best_score`/`best_config`
are spec-only (referenced by contracts, never executed by the impl), so
nothing PSeq-valued needs a runtime shim.

ORACLE: the REAL patched repo function the model models per mapping.md —
`BaseMixture.fit_predict` (`sklearn/mixture/base.py`), exercised through
`GaussianMixture` / `BayesianGaussianMixture`. The gate applies the gold
patch to /testbed before this script runs and sets PYTHONPATH so the patched
package is what imports here; this script does NOT apply any patch itself.

Type bridge (mapping.md section 2):
  * a parameter configuration <-> an `int` identifier: each case carries a
    pool of distinct real parameter snapshots (produced by real fits) and
    `config == i` means "the parameters of pool entry i";
  * a trial score <-> an `int`: the selection depends only on the ORDER of
    the per-trial lower bounds, so integer scores (lane A) drive the real
    loop directly through `_compute_lower_bound`, and real float lower
    bounds (lane B) are rank-encoded to ints preserving `>` and `==`;
  * the returned label array <-> the opaque label value: compared as the
    full label tuple (elementwise integer equality, no tolerance);
  * `inst.config` on return <-> the parameters the estimator retains:
    compared via elementwise array equality of `_get_parameters()` against
    the pool entry the shadow selected.

Two oracle lanes:

  Lane A (trial injection, the >=1e5 lane): drive the REAL patched
  `fit_predict` with a subclass that (i) sets the held parameters to a
  chosen pool snapshot at each initialization, (ii) makes the M-step a
  no-op so trial i's parameters stay pool[i]'s, and (iii) returns the
  chosen integer score as the trial's lower bound. Every selection /
  persistence / query line that executes is the genuine patched repo
  code; only the per-trial parameter+score PRODUCTION (outside the modeled
  boundary, mapping.md section 1) is steered.

  Lane B (end-to-end, nothing steered): fit real estimators with real EM
  over n_init trials; the per-trial (parameter snapshot, lower bound)
  pairs are observed through the behavior-neutral per-init progress hook
  (`_print_verbose_msg_init_end`, a pure observation point called once per
  trial with the trial's converged state current), rank-encoded, and fed
  to the shadow; the shadow's labels and selected configuration are then
  compared against the real `fit_predict` return and the really retained
  parameters.

>= 1e5 Requires-satisfying inputs: 100000 injected-trial fuzz cases +
boundary cases (single trial, all-tied scores, earliest-max ties, max at
first/last/middle, duplicated configurations, extreme score magnitudes) +
160 end-to-end fits (both estimator classes, incl. the F2P-shaped setup).
Pinned seed: 13142.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' outputs and exits 1. stdlib + numpy only.
"""
import json
import sys
import warnings

import numpy as np

SEED = 13142
N_INJECT_FUZZ = 100_000
N_E2E_SMALL = 150
POOL_SIZE = 12


# --- the impl region of model.py, verbatim, contract calls stripped ----------

class Estimator(object):
    def __init__(self, config):
        self.config = config


# labels_of shim context: set per case by the harness below. `_POOL` maps a
# configuration identifier to a real parameter snapshot; `_SCRATCH` is a real
# estimator object the query primitive runs on; `_X` is the fixed data.
_POOL = None
_SCRATCH = None
_X = None


def labels_of(config):
    """@ContractOnly callee shim: the REAL unchanged query primitive — set the
    held parameters to the identified configuration, then take the row-wise
    argmax of the e-step responsibilities (the same primitive the repo's
    fit_predict uses to produce its labels)."""
    _SCRATCH._set_parameters(_POOL[config])
    _, log_resp = _SCRATCH._e_step(_X)
    return tuple(int(v) for v in log_resp.argmax(axis=1))


def fit_and_label(inst, run_config, run_score):
    # impl-start (contracts stripped)
    n = len(run_config)
    # The transient configuration the object holds after the final trial is the
    # final trial's configuration (may differ from the selected one).
    inst.config = run_config[n - 1]
    # Select the highest-scoring (earliest-on-tie) configuration over all trials
    # by scanning the trials from last to first; the running selection equals
    # best_config / best_score over the already-scanned suffix.
    selected = run_config[n - 1]  # type: int
    selected_score = run_score[n - 1]  # type: int
    i = n
    while i > 1:
        s = run_score[i - 2]
        if s >= selected_score:
            selected = run_config[i - 2]
            selected_score = s
        i = i - 1
    # Persist the selected configuration, THEN derive the labels from the
    # persisted (retained) configuration.
    inst.config = selected
    labels = labels_of(inst.config)
    return labels
    # impl-end


# --- oracle plumbing ----------------------------------------------------------

def make_trial_driver(base_cls, n_components):
    """A subclass of the REAL estimator that steers only the per-trial
    parameter+score production: each initialization installs a preset pool
    snapshot, the M-step is a no-op (so the trial's parameters stay that
    snapshot), and the trial's lower bound is the preset score. The selection
    loop, the parameter persistence, and the final label query inside
    fit_predict are the genuine patched repo code, untouched."""

    class TrialDriver(base_cls):
        def __init__(self, params_seq, scores_seq):
            super(TrialDriver, self).__init__(
                n_components=n_components, n_init=len(scores_seq), max_iter=1)
            self._params_seq = params_seq
            self._scores_seq = scores_seq
            self._trial_idx = -1

        def _initialize_parameters(self, X, random_state):
            self._trial_idx += 1
            self._set_parameters(self._params_seq[self._trial_idx])

        def _m_step(self, X, log_resp):
            pass

        def _compute_lower_bound(self, log_resp, log_prob_norm):
            return self._scores_seq[self._trial_idx]

    return TrialDriver


def make_recorder(base_cls):
    """A subclass of the REAL estimator that records, via the behavior-neutral
    per-init progress hook, each trial's converged parameter snapshot and
    lower bound. Nothing else is overridden: the EM iterations, the selection,
    the persistence and the label query are all the real repo code."""

    class Recorder(base_cls):
        def _print_verbose_msg_init_end(self, ll):
            self._recorded_trials.append((self._get_parameters(), float(ll)))
            base_cls._print_verbose_msg_init_end(self, ll)

        def fit_predict(self, X, y=None):
            self._recorded_trials = []
            return base_cls.fit_predict(self, X, y)

    return Recorder


def params_equal(pa, pb):
    """Elementwise array equality of two parameter snapshots (entries may be
    arrays or tuples of arrays, depending on the estimator class)."""
    if isinstance(pa, tuple) or isinstance(pb, tuple):
        if not (isinstance(pa, tuple) and isinstance(pb, tuple)
                and len(pa) == len(pb)):
            return False
        return all(params_equal(a, b) for a, b in zip(pa, pb))
    return np.array_equal(np.asarray(pa), np.asarray(pb))


def rank_encode(values):
    """Order- and tie-preserving int encoding of a float sequence (the model's
    integer score carrier; mapping.md section 2)."""
    distinct = sorted(set(values))
    rank = {v: i for i, v in enumerate(distinct)}
    return [rank[v] for v in values]


def run_shadow(pool, scratch, X, run_config, run_score):
    """Run the contract-stripped impl with the labels_of context bound."""
    global _POOL, _SCRATCH, _X
    _POOL, _SCRATCH, _X = pool, scratch, X
    inst = Estimator(-1)
    labels = fit_and_label(inst, list(run_config), list(run_score))
    return labels, inst.config


def disagree(label, inputs, what, shadow_val, real_val):
    print("DISAGREEMENT (%s) on %s\n  inputs=%r\n  shadow=%r\n  real=%r"
          % (label, what, inputs, shadow_val, real_val))
    return 1


# --- input generation -----------------------------------------------------------

def boundary_cases(pool_size):
    """Hand-picked Requires-satisfying trial runs (config ids, int scores)."""
    return [
        # (run_config, run_score)
        ([0], [0]),                                # single trial
        ([3], [-1000000]),                         # single trial, big negative
        ([0, 1], [5, 5]),                          # two-way tie -> earliest
        ([1, 0], [5, 5]),
        ([0, 1, 2], [7, 7, 7]),                    # all tied -> earliest
        ([2, 1, 0], [1, 2, 3]),                    # max at last
        ([2, 1, 0], [3, 2, 1]),                    # max at first
        ([2, 1, 0], [1, 3, 2]),                    # max in the middle
        ([4, 4, 4], [1, 2, 3]),                    # duplicated configs
        ([0, 1, 2, 3], [-5, -5, -7, -6]),          # negative scores, tie
        ([5, 6, 7, 8, 9], [2, 9, 9, 1, 9]),        # three-way tie -> earliest
        ([0, 1], [-(10 ** 18), 10 ** 18]),         # extreme magnitudes
        ([1, 0], [10 ** 18, -(10 ** 18)]),
        (list(range(pool_size)), list(range(pool_size))),      # increasing
        (list(range(pool_size)), list(range(pool_size, 0, -1))),  # decreasing
        (list(range(pool_size)), [0] * pool_size),             # all zero
    ]


def fuzz_case(rng, pool_size):
    T = int(rng.randint(1, 9))
    run_config = [int(rng.randint(0, pool_size)) for _ in range(T)]
    if rng.random() < 0.5:
        # narrow score range -> frequent ties (exercises earliest-max)
        run_score = [int(rng.randint(-3, 4)) for _ in range(T)]
    else:
        run_score = [int(rng.randint(-10 ** 6, 10 ** 6)) for _ in range(T)]
    return run_config, run_score


def build_pool(base_cls, n_components, X, size):
    """Distinct real parameter snapshots: real short fits under varied seeds.
    Each pool index is one configuration identifier (mapping.md section 2)."""
    pool = []
    for s in range(size):
        est = base_cls(n_components=n_components, random_state=s,
                       max_iter=5, n_init=1)
        est.fit(X)
        pool.append(est._get_parameters())
    return pool


def main():
    from sklearn.mixture import GaussianMixture, BayesianGaussianMixture

    warnings.simplefilter("ignore")
    rng = np.random.RandomState(SEED)
    checked = 0

    # ---- lane A: injected trials through the REAL patched fit_predict -------
    K = 3
    XA = rng.randn(24, 2)
    pool = build_pool(GaussianMixture, K, XA, POOL_SIZE)
    scratch = GaussianMixture(n_components=K, random_state=0,
                              max_iter=5, n_init=1)
    scratch.fit(XA)
    Driver = make_trial_driver(GaussianMixture, K)

    lane_a_cases = boundary_cases(POOL_SIZE)
    for _ in range(N_INJECT_FUZZ):
        lane_a_cases.append(fuzz_case(rng, POOL_SIZE))

    for run_config, run_score in lane_a_cases:
        shadow_labels, shadow_sel = run_shadow(pool, scratch, XA,
                                               run_config, run_score)
        drv = Driver([pool[c] for c in run_config], list(run_score))
        real_labels = tuple(int(v) for v in drv.fit_predict(XA))
        inputs = {"run_config": run_config, "run_score": run_score}
        if shadow_labels != real_labels:
            return disagree("lane A", inputs, "returned labels",
                            shadow_labels, real_labels)
        # the retained configuration: the really-persisted parameters must be
        # the pool snapshot the shadow selected
        if not params_equal(drv._get_parameters(), pool[shadow_sel]):
            return disagree("lane A", inputs, "retained configuration",
                            "pool[%d]" % shadow_sel, "other parameters")
        checked += 1

    # ---- lane B: end-to-end real fits, per-trial observations bridged -------
    e2e_setups = []
    for j in range(N_E2E_SMALL):
        n = int(rng.randint(30, 80))
        Xb = rng.randn(n, 2) + rng.randint(-3, 4, size=(1, 2))
        cls = GaussianMixture if j % 3 else BayesianGaussianMixture
        n_init = int(rng.randint(1, 7))
        e2e_setups.append((cls, dict(n_components=3, n_init=n_init,
                                     max_iter=15, random_state=j), Xb))
    # the F2P-shaped setups: larger data, several inits
    XF = np.random.RandomState(0).randn(1000, 5)
    for s in range(5):
        e2e_setups.append((GaussianMixture,
                           dict(n_components=5, n_init=5, random_state=s), XF))
    for s in range(5):
        e2e_setups.append((BayesianGaussianMixture,
                           dict(n_components=5, n_init=10, random_state=s), XF))

    n_e2e = 0
    for cls, kw, Xb in e2e_setups:
        Rec = make_recorder(cls)
        est = Rec(**kw)
        real_labels = tuple(int(v) for v in est.fit_predict(Xb))
        # capture the really-retained parameters BEFORE the shadow runs (the
        # shadow's labels_of shim re-installs pool parameters on `est`); the
        # snapshot holds references that later _set_parameters calls do not
        # mutate (attributes are reassigned, arrays are never written in place)
        retained = est._get_parameters()
        trials = est._recorded_trials
        run_config = list(range(len(trials)))            # snapshot i <-> id i
        run_score = rank_encode([lb for _, lb in trials])
        pool_b = [p for p, _ in trials]
        shadow_labels, shadow_sel = run_shadow(pool_b, est, Xb,
                                               run_config, run_score)
        inputs = {"class": cls.__name__, "kw": kw, "n_trials": len(trials),
                  "scores": run_score}
        if shadow_labels != real_labels:
            return disagree("lane B", inputs, "returned labels",
                            shadow_labels, real_labels)
        if not params_equal(retained, pool_b[shadow_sel]):
            return disagree("lane B", inputs, "retained configuration",
                            "trial %d parameters" % shadow_sel,
                            "other parameters")
        checked += 1
        n_e2e += 1

    print("G-CONF OK: shadow impl == real patched best-trial selection + "
          "post-persist label query on %d inputs (%d injected-trial + %d "
          "end-to-end cases, seed %d)."
          % (checked, checked - n_e2e, n_e2e, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "e2e_cases": n_e2e,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly labels_of -> real "
                                "_set_parameters + _e_step argmax)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
