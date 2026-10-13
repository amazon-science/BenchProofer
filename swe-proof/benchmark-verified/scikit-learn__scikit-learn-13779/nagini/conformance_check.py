#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13779
(nagini).

SHADOW: the impl region of model.py's `check_weighting_support`, copied
verbatim below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped. The carrier is a plain List[int] of per-entry status tags, so no
PSeq shim is needed (the impl region indexes the list directly). The single
@ContractOnly callee, `accepts_weighting`, calls the REAL repo probe
`sklearn.utils.validation.has_fit_parameter(estimator, 'sample_weight')` on a
representative present estimator of the given status — exactly the bijection
in mapping.md §2 (status 1 = a present estimator whose `fit` declares
`sample_weight`; status 2 = one whose `fit` does not). The @Pure helper
`config_supports` is spec-only (never called by the impl region) and is not
needed here.

ORACLE: the REAL patched repo function the model models per mapping.md —
the weighted-fit pre-check loop inside `_BaseVoting.fit` in
sklearn/ensemble/voting.py. The gate applies the patch to /testbed before
this script runs. Per roster of status tags, the oracle builds the
corresponding `estimators` list of (name, step) tuples (status 0 -> step is
None; status 1 -> a weight-accepting step; status 2 -> a weight-rejecting
step) and calls the real `_BaseVoting.fit` with a non-None sample_weight.
The observation is isolated to the modeled pre-check loop by stubbing, on
the instance, the first callee that executes AFTER the loop
(`self._validate_names`) to raise a sentinel:

  * sentinel raised            -> the pre-check returned normally
  * ValueError raised          -> the pre-check rejected the configuration
                                  (the only other ValueError source before
                                  the sentinel is the weights-length guard,
                                  which is unreachable here: weights is None)
  * any other exception        -> the pre-check crashed (e.g. the probe was
                                  consulted on an absent entry) — always a
                                  disagreement against the shadow

Outcomes compare as strings: "supports" / "rejects" / "crash:<TypeName>".
The shadow's WeightingUnsupported maps to "rejects" (mapping.md §2: the
rejection's identity is the observable; its message text is not).

Input domain (the model's Requires): a list of tags each in {0, 1, 2}. One
documented restriction: non-empty rosters only. The surrounding function
rejects an empty `estimators` configuration with its own guard BEFORE the
modeled pre-check loop is ever reached, so the empty roster has no
real-execution counterpart for this loop (mapping.md §1 scopes the model to
the pre-check loop alone; the empty-configuration guard is outside it and
unchanged). On the empty roster the loop body trivially never runs.

Coverage: full enumeration of every roster of length 1..4 (120 rosters),
each run twice — once with lightweight synthesized estimators and once with
real sklearn estimators (LogisticRegression / KNeighborsClassifier / None)
anchoring the status->estimator bijection against genuine `fit` signatures —
plus long-roster edges, plus 100000 fuzz rosters biased toward the
discriminating shapes (all-absent, no-rejecting, exactly-one-rejecting at a
random slot). >= 1e5 Requires-satisfying inputs total.
Pinned fuzz seed: 13779.

Exit 0 iff zero disagreements; on disagreement prints the roster and both
outcomes and exits 1. stdlib + the repo under test only.
"""
import itertools
import json
import random
import sys

SEED = 13779
N_FUZZ = 100_000

from sklearn.utils.validation import has_fit_parameter  # the REAL probe
from sklearn.ensemble.voting import _BaseVoting, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier


class WeightingUnsupported(Exception):
    """The shadow's rejection outcome (model.py's user-defined stand-in for
    the real check's rejection; the identity of the rejection is the
    observable, per mapping.md §2)."""


class _WeightStep:
    """A minimal present sub-estimator whose `fit` DOES accept per-sample
    weighting (status 1)."""
    def fit(self, X, y, sample_weight=None):
        return self

    def get_params(self, deep=True):
        return {}


class _NoWeightStep:
    """A minimal present sub-estimator whose `fit` does NOT accept per-sample
    weighting (status 2)."""
    def fit(self, X, y):
        return self

    def get_params(self, deep=True):
        return {}


# Representative present estimators for the @ContractOnly probe bridge:
# the shadow's accepts_weighting(status) consults the REAL probe on a
# present estimator of that status (mapping.md §2 bijection).
_PROBE_REP = {1: _WeightStep(), 2: _NoWeightStep()}


def accepts_weighting(status):
    """@ContractOnly callee -> the REAL repo probe. Meaningful only for a
    present entry (status in {1, 2}), exactly the axiom's precondition."""
    assert status == 1 or status == 2, (
        "shadow consulted the probe outside its precondition: status=%r"
        % (status,))
    return has_fit_parameter(_PROBE_REP[status], 'sample_weight')


# --- the impl region of model.py, verbatim (contracts stripped) ---------------

def check_weighting_support(roster):
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        status = roster[i - 1]
        if status == 0:
            # absent entry: skip, never consult the probe on it
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return


# --- shadow outcome ------------------------------------------------------------

def shadow_outcome(roster):
    try:
        check_weighting_support(list(roster))
    except WeightingUnsupported:
        return "rejects"
    except Exception as e:  # noqa: BLE001 - any crash is an outcome to compare
        return "crash:%s" % type(e).__name__
    return "supports"


# --- oracle: the real patched pre-check loop -----------------------------------

class _PreCheckCompleted(Exception):
    """Sentinel: raised by the stubbed post-loop callee, meaning the real
    pre-check loop finished without rejecting."""


# Tiny fixed fit arguments; the code under observation never touches X or y
# before the sentinel fires, and sample_weight is only tested for being
# non-None inside the modeled loop.
_X = [[0.0], [1.0]]
_Y = [0, 1]
_W = [1.0, 1.0]


def _make_estimators(roster, factories):
    return [("e%d" % k, factories[status]()) for k, status in enumerate(roster)]


def real_outcome(roster, factories):
    voter = VotingClassifier(estimators=_make_estimators(roster, factories))

    def _sentinel(names):
        raise _PreCheckCompleted()

    voter._validate_names = _sentinel  # first callee after the modeled loop
    try:
        # The REAL patched function containing the modeled pre-check loop.
        _BaseVoting.fit(voter, _X, _Y, sample_weight=_W)
    except _PreCheckCompleted:
        return "supports"
    except ValueError:
        # weights is None here, so the only ValueError reachable before the
        # sentinel is the pre-check's rejection.
        return "rejects"
    except Exception as e:  # noqa: BLE001 - e.g. probing an absent entry
        return "crash:%s" % type(e).__name__
    return "crash:NoObservation"  # fit returned without reaching the sentinel


# --- estimator factories per status tag ----------------------------------------

FACTORIES_SYNTH = {0: lambda: None, 1: _WeightStep, 2: _NoWeightStep}
FACTORIES_REAL = {0: lambda: None,
                  1: LogisticRegression,          # fit(..., sample_weight=None)
                  2: KNeighborsClassifier}        # fit(X, y) — no sample_weight


# --- driving --------------------------------------------------------------------

def check_case(roster, factories, checked):
    s = shadow_outcome(roster)
    r = real_outcome(roster, factories)
    if s != r:
        print("DISAGREEMENT\n  roster=%r\n  shadow=%r\n  real=%r"
              % (list(roster), s, r))
        return False
    checked[0] += 1
    return True


def boundary_rosters():
    """Every roster of length 1..4 over {0,1,2}, plus long-roster edges."""
    out = []
    for n in (1, 2, 3, 4):
        out.extend(itertools.product((0, 1, 2), repeat=n))
    out += [
        (0,) * 8,                    # long all-absent
        (1,) * 8,                    # long all-accepting
        (2,) + (1,) * 7,             # rejecting entry first
        (1,) * 7 + (2,),             # rejecting entry last
        (0, 1) * 4,                  # alternating absent/accepting
        (0, 2) * 4,                  # alternating absent/rejecting
        (1, 0, 1, 0, 2, 0, 1, 1),    # mixed with a buried rejecting entry
    ]
    return out


def rand_roster(rng):
    n = rng.randint(1, 8)
    mode = rng.randint(0, 3)
    if mode == 0:                                    # uniform tags
        return [rng.randint(0, 2) for _ in range(n)]
    if mode == 1:                                    # no rejecting entries
        return [rng.choice((0, 1)) for _ in range(n)]
    if mode == 2:                                    # exactly one rejecting slot
        r = [rng.choice((0, 1)) for _ in range(n)]
        r[rng.randrange(n)] = 2
        return r
    return [0] * n                                   # all absent


def main():
    checked = [0]

    # boundary: synthesized estimators AND real sklearn estimators (the
    # latter anchors the status->estimator bijection on genuine signatures)
    for roster in boundary_rosters():
        if not check_case(roster, FACTORIES_SYNTH, checked):
            return 1
        if not check_case(roster, FACTORIES_REAL, checked):
            return 1

    n_boundary = checked[0]

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        if not check_case(rand_roster(rng), FACTORIES_SYNTH, checked):
            return 1

    print("G-CONF OK: shadow impl == real pre-check outcome on %d inputs "
          "(%d boundary [synth + real estimators] + %d fuzz, seed %d)."
          % (checked[0], n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "ContractOnly probe -> real has_fit_parameter)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
