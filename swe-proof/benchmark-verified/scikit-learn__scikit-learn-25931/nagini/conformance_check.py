#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25931
(nagini backend).

Refutes -- does not prove -- the refinement leg: does the MODEL in model.py
actually agree with the REAL patched repository code it claims to model?

=============================================================================
SHADOW  (clause 1: the impl region, VERBATIM, contracts deleted)
=============================================================================
The model IS Python, so nothing is transliterated. Copied below with only the
contract calls removed (`Requires`/`Ensures`/`Acc`/`Implies`/`Old`, and the
`# pre-conditions-*` / `# post-conditions-*` markers):

  * `mismatch_advisory(...)`   -- the `@Pure` helper the impl regions call
                                 (model.py `# pure-start` .. `# pure-end`).
  * `Estimator.__init__`       -- field writes only.
  * `Matrix.__init__`          -- field write only.
  * `validating_scorer(...)`   -- SITE 1 impl region, verbatim.
  * `fit_offset(...)`          -- SITE 2 impl region (the patched site), verbatim.

Also shadowed, for the harness self-test only, is model_prepatch.py's SITE 2
impl region (`fit_offset_prepatch`) -- the buggy variant that routes the offset
through the validating public scorer. It is NOT part of the verdict; it is used
to prove the harness is CAPABLE OF FAILING (see HARNESS SELF-TEST below).

No `PSeq`/`ToSeq` shim is needed: this model uses no Nagini sequence carrier.

`@ContractOnly` callees have no body to copy, so they are shimmed to call the
REAL repo function they axiomatize (mapping.md §1/§3), which exercises each
axiom instead of assuming it:

  * `prepare(X_raw)`            -> REAL `BaseEstimator._validate_data(X,
      accept_sparse=["csc"], dtype=tree_dtype)` (reset=True), i.e. exactly the
      call `IsolationForest.fit` makes at `_iforest.py:291` (mapping.md §3.2).
  * `prepared_scorer(self, X)`  -> REAL `IsolationForest._score_samples(X)`,
      the private non-validating scorer the gold patch introduces
      (mapping.md §3.3), followed by the REAL `numpy.percentile(scores,
      100.0 * contamination)` that turns those per-row scores into the offset.

Each shim additionally ASSERTS the part of its own `Ensures` that the real
callee is claimed to satisfy -- that it emits ZERO label-mismatch advisories,
and (for `prepared_scorer`) that it returns one score per row. An axiom whose
real callee violates its contract is reported as a disagreement rather than
silently trusted.

=============================================================================
ORACLE  (clause 2: the real patched repo function -- CALLED, not reimplemented)
=============================================================================
`IsolationForest.fit` -- `sklearn/ensemble/_iforest.py:268` at base_commit
e3d1f9ac39e4bf0f31430e779acc50fb05fe1b64, WITH the gold patch applied (the
gate git-applies patch.diff to /testbed and sets PYTHONPATH before this script
runs; this script applies nothing itself). Nothing is transliterated: site 2's
oracle is a live `IsolationForest(...).fit(X)` on a real ndarray / real pandas
DataFrame, and site 1's oracle is the live public `IsolationForest
.score_samples(X)` (`_iforest.py:407` post-patch). The observables are read off
the real estimator and the real `warnings` stream.

=============================================================================
TYPE BRIDGE  (clause 3: mapping.md §2, inverted)
=============================================================================
The model works over minimal records; the real code wants real containers, so
each modelled field is generated on the ABSTRACT side and realized concretely:

  model                              <-> repo reality
  ---------------------------------- --- ----------------------------------------
  `Matrix.has_labels: bool`          <-> True  => `pd.DataFrame(data, columns=[...])`
                                         False => bare `np.ndarray`
                                         (read back as `_get_feature_names(X)
                                          is not None`)
  `Estimator.fitted_with_labels`     <-> `hasattr(est, "feature_names_in_")`
  `Estimator.fit_advisories: int`    <-> number of `UserWarning`s during the call
                                         whose text contains "does not have valid
                                         feature names" (that ONE advisory only;
                                         the "X has feature names, but ... fitted
                                         without" message is a different advisory
                                         and is counted as 0, per mapping.md §3.1)
  `Estimator.offset_set: bool`       <-> `hasattr(est, "offset_") and
                                          contamination != "auto"`
  `calibration_requested: bool`      <-> `contamination != "auto"`

A bridge payload (`.real`) is attached to the shadow's `Matrix`/`Estimator`
AFTER construction, so the copied constructors stay verbatim; it carries the
concrete object the `@ContractOnly` shims drive.

STRENGTHENING BEYOND THE MODEL. mapping.md §2 abstracts the offset VALUE away
(only existence + provenance are modelled). The shadow nevertheless computes
the concrete offset through its `prepared_scorer` shim and this check compares
it bit-for-bit against the real fitted `est.offset_`. That is strictly harder
than the model claims, and it is what makes the `prepared_input` /
`raw_fit_input` provenance tokens load-bearing rather than decorative: it
refutes the model if the real patched `fit` derives its offset from anything
other than per-row scores of the prepared form of fit's own input.

=============================================================================
INPUT DOMAIN  (clause 4: >= 1e5 Requires-satisfying inputs)
=============================================================================
Every generated input satisfies the `Requires` by construction: each site-2
case starts from a FRESH estimator (`fit_advisories == 0`, `offset_set ==
False`) and passes that fit's OWN raw input as `X_raw` (the `raw_fit_input`
token: the same object is handed to both legs, never a fabricated matrix), and
`prepare`'s result -- the only thing fed to `prepared_scorer` -- is what
carries `prepared_input`.

The MODELLED input space is FINITE and tiny: site 2 is
(`has_labels`, `calibration_requested`) = 4 points, site 1 is
(`arg_has_labels`, `fitted_with_labels`) = 4 points -- 8 abstract points in
all. Per the contract's finite-space clause, all 8 are ENUMERATED EXHAUSTIVELY
(so every branch of both impl regions is taken, including the advisory-firing
branch of `mismatch_advisory`, which the patched `fit` must never reach but
site 1 must), and the count is then filled by fuzzing the CONCRETE PRE-IMAGES
of those same 8 points -- row count, column count, data values, the actual
contamination value, `n_estimators`, `random_state`, ndarray vs DataFrame,
dense vs CSC-sparse. That is a stronger check than 1e5 samples of an infinite
space, not a weaker one: the abstraction is covered completely and each
abstract point is stress-tested against thousands of distinct realizations.

Boundary cases run first: the F2P repro exactly (`pd.DataFrame(rng.randn(4),
columns=["a"])`, `contamination=0.05`, `random_state=0`), the singleton row,
one column and many columns, both contamination interval endpoints (the
`Interval(Real, 0, 0.5, closed="right")` upper bound 0.5 and a near-zero
value), `"auto"`, and CSC-sparse unlabelled input.

Pinned seed: `SEED = 25931` (recorded in mapping.md §G-CONF).

ORACLE COST / why the counts are split the way they are: the site-2 oracle is a
full real `IsolationForest.fit` (parameter validation + ensemble construction +
chunked scoring), ~4 ms, not a pure function. The shadow's per-input cost is
held down by caching the fitted TREES per (dataset, n_estimators,
random_state) from a `contamination="auto"` fit -- the branch that early-returns
`offset_ = -0.5` and never touches the offset path, so it cannot import the
behaviour under test -- then deleting `feature_names_in_`/`offset_` so the
shadow's own `prepare` and `prepared_scorer` do the modelled work. Trees are
independent of `contamination` (it is read only in the tail), so this is sound;
were it not, it would show up as an offset disagreement, not a false pass. The
oracle leg is never cached: every counted site-2 input is a distinct real fit.
Both counts are reported separately in the final JSON -- no silent truncation.

=============================================================================
CSC-SPARSE: A REAL DEFECT IN THE GOLD PATCH, FOUND BY THIS CHECK
=============================================================================
Driving the boundary battery surfaced a genuine regression in the GOLD PATCH
itself (not in model.py, and not in this bridge). With CSC-sparse input and
`contamination != "auto"`, the patched `fit` raises

    ValueError: X should be in csr_matrix format, got <class
    'scipy.sparse._csc.csc_matrix'>

whereas the PRE-patch code returns an offset normally. Mechanism: `fit`'s
preparation pass is `_validate_data(..., accept_sparse=["csc"])`, so the
prepared matrix is CSC. Pre-patch, the offset path went through the PUBLIC
`score_samples`, whose own `_validate_data(accept_sparse="csr")` re-validated
CSC -> CSR before scoring. The patch removes exactly that re-validation (which
is the point -- it is what emitted the spurious advisory), so the CSC matrix now
reaches `_compute_score_samples` -> `tree.apply`, which requires CSR. Upstream
scikit-learn later fixed this by inserting `if issparse(X): X = X.tocsr()`
before the `_score_samples` call in `fit`; that line is absent from this
bundle's patch.diff. The benchmark's own `test_iforest_sparse` P2P test does not
catch it because it never sets `contamination` (it stays at the default
`"auto"`, the branch that early-returns before the offset path).

This is reported as a FINDING about the instance's gold patch. It is NOT
routed around: CSC-sparse inputs REMAIN in the input domain, and the check
requires the two legs to agree on the exception as an observation (identical
error identity + identical advisory tally). They do agree -- the shadow
reproduces the raise because its `prepared_scorer` shim drives the SAME real
`_score_samples` rather than reimplementing it, which is precisely the property
that makes this leg evidence. The model is silent about exceptions (mapping.md
§2 abstracts the offset VALUE away and models no error channel), so this
divergence is outside what model.py claims and is not a model-unfaithfulness
finding; it does not make the refinement false.

=============================================================================
HARNESS SELF-TEST (capable of failing)
=============================================================================
Before the verdict, `harness_self_test()` runs the PRE-PATCH shadow
(model_prepatch.py's impl region) against the same oracle on the F2P input and
requires that it DISAGREE. If the buggy shadow passes, the harness is not
discriminating and the script exits 1 rather than reporting a green that
certifies nothing.

Exit 0 iff zero disagreements. On disagreement the input and both sides'
observations are printed and the exit status is 1.

Imports: stdlib + numpy + pandas + scipy.sparse + the patched repo itself.
"""
import json
import random
import sys
import warnings

import numpy as np

SEED = 25931

# Counted differential inputs. Site 2 is the patched site (real `fit` per
# input, ~4 ms); site 1 is the public scoring routine (real `score_samples`
# per input). Sum >= 1e5.
N_SITE2_FUZZ = 60_000
N_SITE1_FUZZ = 45_000

# The one advisory the model counts (mapping.md §3.1).
ADVISORY = "does not have valid feature names"


# =============================================================================
# SHADOW -- model.py, verbatim, contract calls deleted
# =============================================================================

# --- model.py `# pure-start` .. `# pure-end`, verbatim ------------------------
def mismatch_advisory(arg_has_labels, fitted_with_labels):
    """Number of label-mismatch advisories a single label-consistency check
    emits for one matrix. (Docstring and body verbatim from model.py.)
    """
    if (not arg_has_labels) and fitted_with_labels:
        return 1
    return 0


# --- model.py carriers, constructors reduced to their field writes ------------
class Estimator:
    def __init__(self):
        self.fitted_with_labels = False
        self.fit_advisories = 0
        self.offset_set = False


class Matrix:
    def __init__(self, has_labels):
        self.has_labels = has_labels


# --- @ContractOnly axioms -> the REAL repo callees they axiomatize ------------
class AxiomViolation(Exception):
    """A real callee violated the `Ensures` its @ContractOnly axiom claims."""


class RealCalleeRaised(Exception):
    """A real callee driven by a @ContractOnly shim raised a ValueError on the
    real prepared input. Carries the error identity so the shadow's observation
    can be compared against the oracle's."""


def _count_advisories(records):
    return sum(1 for r in records if ADVISORY in str(r.message))


def _err_key(exc):
    """A comparable identity for an exception raised by the real code: type
    plus the message with the concrete class repr normalized away."""
    msg = str(exc)
    if "format, got" in msg:
        msg = msg.split("format, got")[0] + "format, got <...>"
    return "%s: %s" % (type(exc).__name__, msg)


def prepare(X_raw):
    """@ContractOnly `prepare` -> REAL `BaseEstimator._validate_data(X,
    accept_sparse=["csc"], dtype=tree_dtype)` (reset=True), the fitting
    preparation pass of `IsolationForest.fit` (`_iforest.py:291`,
    mapping.md §3.2). Returns the prepared `Matrix` carrying `prepared_input`.
    """
    from sklearn.tree._tree import DTYPE as tree_dtype
    from sklearn.utils.validation import _get_feature_names

    est = X_raw.owner
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        real_prepared = est.real._validate_data(
            X_raw.real, accept_sparse=["csc"], dtype=tree_dtype)
    # `prepare` has no permission to `fit_advisories`: it cannot emit one.
    emitted = _count_advisories(rec)
    if emitted != 0:
        raise AxiomViolation(
            "prepare/_validate_data(reset=True) emitted %d advisory(ies); the "
            "axiom claims it emits none" % emitted)
    # Ensures(Result().has_labels == False) -- the A-reference deep fact.
    real_has_labels = _get_feature_names(real_prepared) is not None
    if real_has_labels:
        raise AxiomViolation(
            "prepare/_validate_data(reset=True) returned a LABELLED matrix; "
            "the axiom claims the prepared form is always unlabelled")
    out = Matrix(real_has_labels)
    out.real = real_prepared          # bridge payload
    out.owner = est
    out.prepared_input = True         # the token `prepared_scorer` requires
    return out


def prepared_scorer(self, X):
    """@ContractOnly `prepared_scorer` -> REAL `IsolationForest._score_samples`
    (introduced by the gold patch; mapping.md §3.3), then the REAL
    `numpy.percentile(scores, 100.0 * contamination)` that derives the offset
    from those per-row scores. Grants `offset_set` + the
    `offset_from_unvalidated_scoring` token, per the axiom's `Ensures`.
    """
    if not getattr(X, "prepared_input", False):
        raise AxiomViolation(
            "prepared_scorer called on a matrix without the prepared_input "
            "token (Requires violated by the harness)")
    if X.has_labels:
        raise AxiomViolation(
            "prepared_scorer called on a LABELLED matrix (Requires "
            "X.has_labels == False violated by the harness)")
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        try:
            scores = self.real._score_samples(X.real)
        except ValueError as exc:
            # The REAL callee rejected the REAL prepared matrix. Not an axiom
            # violation of the modelled behaviour -- it is an observation the
            # oracle must reproduce too (CSC-sparse note in the docstring).
            self.raised = _err_key(exc)
            self.fit_advisories += _count_advisories(rec)
            raise RealCalleeRaised(self.raised)
        offset = float(np.percentile(scores, 100.0 * self.contamination))
    # Ensures(self.fit_advisories == Old(self.fit_advisories)): it runs no
    # validation pass, so it emits nothing.
    emitted = _count_advisories(rec)
    if emitted != 0:
        raise AxiomViolation(
            "prepared_scorer/_score_samples emitted %d advisory(ies); the "
            "axiom claims it runs no label-consistency check" % emitted)
    # It must furnish per-row scores (one per row of the prepared matrix).
    n_rows = X.real.shape[0]
    if np.asarray(scores).shape != (n_rows,):
        raise AxiomViolation(
            "prepared_scorer/_score_samples returned shape %r for %d rows; the "
            "axiom claims per-row scores"
            % (np.asarray(scores).shape, n_rows))
    # Ensures(self.offset_set) and Ensures(offset_from_unvalidated_scoring(self))
    self.offset_set = True
    self.offset_from_unvalidated_scoring = True
    self.offset_value = offset


# --- SITE 1 impl region of model.py, VERBATIM (contracts deleted) -------------
def validating_scorer(self, X):
    # impl-start
    # one label-consistency check on the caller-supplied argument, whose advisory
    # is recorded on the estimator as it is emitted
    self.fit_advisories = self.fit_advisories \
        + mismatch_advisory(X.has_labels, self.fitted_with_labels)
    # ... per-row scoring of the validated argument follows (scores unmodelled).
    # impl-end


# --- SITE 2 impl region of model.py, VERBATIM (contracts deleted) -------------
def fit_offset(self, X_raw, calibration_requested):
    # impl-start
    # the fitting preparation pass: record whether the table carried labels, then
    # prepare the raw input to the unlabelled numeric matrix. This pass records
    # the labels for later consistency checks and never emits a mismatch advisory.
    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # derive the calibration offset from per-row scores of the ALREADY-
        # prepared matrix (emits no advisory and furnishes the token-bearing
        # offset).
        prepared_scorer(self, Xp)
    # impl-end


# --- SITE 2 impl region of model_prepatch.py, VERBATIM -- SELF-TEST ONLY ------
def fit_offset_prepatch(self, X_raw, calibration_requested):
    # impl-start
    self.fitted_with_labels = X_raw.has_labels
    Xp = prepare(X_raw)  # prepared form of THIS fit's input
    if calibration_requested:
        # PRE-PATCH (buggy): route the already-prepared matrix through the
        # PUBLIC scoring path, which runs a second label-consistency check.
        validating_scorer(self, Xp)
        self.offset_set = True
    # impl-end


# =============================================================================
# TYPE BRIDGE
# =============================================================================

def make_real_X(data, has_labels, sparse=False):
    """`Matrix.has_labels` -> the concrete container (mapping.md §2)."""
    import pandas as pd
    if has_labels:
        return pd.DataFrame(
            data, columns=["f%d" % i for i in range(data.shape[1])])
    if sparse:
        from scipy.sparse import csc_matrix
        return csc_matrix(data)
    return data


def real_has_labels(X):
    from sklearn.utils.validation import _get_feature_names
    return _get_feature_names(X) is not None


def new_forest(contamination, n_estimators, random_state):
    from sklearn.ensemble import IsolationForest
    return IsolationForest(contamination=contamination,
                           n_estimators=n_estimators,
                           random_state=random_state)


# =============================================================================
# ORACLE -- the REAL patched repo functions, called
# =============================================================================

def oracle_fit(real_X, contamination, n_estimators, random_state):
    """SITE 2 oracle: a live patched `IsolationForest.fit`. Returns the
    modelled observation, bridged off the real estimator + warning stream.

    A `ValueError` from the real code is itself an observation (see the
    CSC-SPARSE note in the module docstring): it is recorded rather than
    swallowed, so the shadow is required to reproduce it."""
    est = new_forest(contamination, n_estimators, random_state)
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        try:
            est.fit(real_X)
        except ValueError as exc:
            return {"raised": _err_key(exc),
                    "fit_advisories": _count_advisories(rec)}
    calibration_requested = (contamination != "auto")
    return {
        "raised": None,
        "fitted_with_labels": hasattr(est, "feature_names_in_"),
        "fit_advisories": _count_advisories(rec),
        "offset_set": hasattr(est, "offset_") and calibration_requested,
        "offset_value": (float(est.offset_) if calibration_requested else None),
    }


def oracle_score_samples(fitted_est, real_X):
    """SITE 1 oracle: a live patched public `IsolationForest.score_samples`.
    Returns the advisory count the call emits as a side effect."""
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        fitted_est.score_samples(real_X)
    return _count_advisories(rec)


# =============================================================================
# SHADOW DRIVER
# =============================================================================

class TreeCache(object):
    """Fitted trees for the shadow leg, from a `contamination="auto"` fit (the
    branch that early-returns `offset_ = -0.5` without ever entering the offset
    path). Keyed by (dataset id, n_estimators, random_state); `contamination`
    is read only in fit's tail, so trees are independent of it."""

    def __init__(self):
        self._cache = {}

    def base(self, key, data, n_estimators, random_state):
        est = self._cache.get(key)
        if est is None:
            est = new_forest("auto", n_estimators, random_state)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                est.fit(data)
            self._cache[key] = est
        # Restore the modelled pre-state: nothing recorded, no offset set.
        for attr in ("feature_names_in_", "offset_"):
            if hasattr(est, attr):
                delattr(est, attr)
        return est


def shadow_fit(real_X, contamination, base_est, impl=fit_offset):
    """Run the shadow's SITE 2 impl region on one input and read off the
    modelled observation. `base_est` supplies the real fitted trees the
    `prepared_scorer` shim needs; the modelled state is fresh."""
    self = Estimator()                      # Requires: advisories 0, offset unset
    self.real = base_est                    # bridge payload
    self.contamination = contamination
    self.offset_value = None
    self.offset_from_unvalidated_scoring = False
    self.raised = None

    X_raw = Matrix(real_has_labels(real_X))
    X_raw.real = real_X                     # bridge payload
    X_raw.owner = self
    X_raw.raw_fit_input = True              # this fit's OWN input

    calibration_requested = (contamination != "auto")
    try:
        impl(self, X_raw, calibration_requested)
    except RealCalleeRaised:
        return {"raised": self.raised,
                "fit_advisories": self.fit_advisories}, self

    return {
        "raised": None,
        "fitted_with_labels": self.fitted_with_labels,
        "fit_advisories": self.fit_advisories,
        "offset_set": self.offset_set,
        "offset_value": (self.offset_value if calibration_requested else None),
    }, self


def shadow_score(fitted_with_labels, arg_has_labels):
    """Run the shadow's SITE 1 impl region and read off the advisory delta."""
    self = Estimator()
    self.fitted_with_labels = fitted_with_labels
    X = Matrix(arg_has_labels)
    before = self.fit_advisories
    validating_scorer(self, X)
    return self.fit_advisories - before


# =============================================================================
# DIFFERENTIAL CASES
# =============================================================================

def diff_site2(case, trees, label):
    """One SITE 2 differential input. Returns an error string or None."""
    (data, has_labels, sparse, contamination, n_estimators, random_state,
     key) = case
    real_X = make_real_X(data, has_labels, sparse)

    oracle = oracle_fit(real_X, contamination, n_estimators, random_state)

    base = trees.base(key, make_real_X(data, False, sparse),
                      n_estimators, random_state)
    try:
        shadow, state = shadow_fit(real_X, contamination, base)
    except AxiomViolation as exc:
        return ("AXIOM VIOLATION (site 2, %s): %s\n  shape=%r has_labels=%r "
                "sparse=%r contamination=%r n_estimators=%r random_state=%r"
                % (label, exc, data.shape, has_labels, sparse, contamination,
                   n_estimators, random_state))

    # An exception is an observation: both legs must agree on it. The real
    # patched code rejects CSC-sparse input on the offset path (docstring:
    # CSC-SPARSE), and the shadow reproduces that because its prepared_scorer
    # shim drives the SAME real callee -- a genuine agreement, not a skip.
    if shadow.get("raised") is not None or oracle.get("raised") is not None:
        if shadow.get("raised") != oracle.get("raised"):
            return _site2_error(label, "raised", data, has_labels, sparse,
                                contamination, n_estimators, random_state,
                                shadow, oracle)
        if shadow["fit_advisories"] != oracle["fit_advisories"]:
            return _site2_error(label, "fit_advisories", data, has_labels,
                                sparse, contamination, n_estimators,
                                random_state, shadow, oracle)
        return None

    # The model's own consistency: `offset_set == calibration_requested`, and
    # when set the offset carries the unforgeable-provenance token.
    calibration_requested = (contamination != "auto")
    if shadow["offset_set"] != calibration_requested:
        return ("SHADOW SELF-INCONSISTENCY (site 2, %s): offset_set=%r but "
                "calibration_requested=%r"
                % (label, shadow["offset_set"], calibration_requested))
    if calibration_requested and not state.offset_from_unvalidated_scoring:
        return ("SHADOW SELF-INCONSISTENCY (site 2, %s): offset set without "
                "the offset_from_unvalidated_scoring token" % (label,))

    for field in ("fitted_with_labels", "fit_advisories", "offset_set"):
        if shadow[field] != oracle[field]:
            return _site2_error(label, field, data, has_labels, sparse,
                                contamination, n_estimators, random_state,
                                shadow, oracle)
    # Strengthening beyond mapping.md §2: the concrete offset must match too.
    if calibration_requested and shadow["offset_value"] != oracle["offset_value"]:
        return _site2_error(label, "offset_value", data, has_labels, sparse,
                            contamination, n_estimators, random_state,
                            shadow, oracle)
    return None


def _site2_error(label, field, data, has_labels, sparse, contamination,
                 n_estimators, random_state, shadow, oracle):
    return ("DISAGREEMENT (site 2 / IsolationForest.fit, %s) on %r\n"
            "  input: shape=%r has_labels=%r sparse=%r contamination=%r "
            "n_estimators=%r random_state=%r\n"
            "  shadow (model.py fit_offset impl region) = %r\n"
            "  oracle (real patched IsolationForest.fit) = %r"
            % (label, field, data.shape, has_labels, sparse, contamination,
               n_estimators, random_state, shadow, oracle))


def diff_site1(fitted_est, fitted_with_labels, real_arg, arg_has_labels, label):
    """One SITE 1 differential input. Returns an error string or None."""
    shadow = shadow_score(fitted_with_labels, arg_has_labels)
    oracle = oracle_score_samples(fitted_est, real_arg)
    if shadow != oracle:
        return ("DISAGREEMENT (site 1 / IsolationForest.score_samples, %s)\n"
                "  input: fitted_with_labels=%r arg_has_labels=%r shape=%r\n"
                "  shadow (model.py validating_scorer impl region) = %d "
                "advisory(ies)\n"
                "  oracle (real patched score_samples)            = %d "
                "advisory(ies)"
                % (label, fitted_with_labels, arg_has_labels,
                   getattr(real_arg, "shape", None), shadow, oracle))
    return None


# =============================================================================
# HARNESS SELF-TEST -- the check must be capable of failing
# =============================================================================

def harness_self_test(trees):
    """Run the PRE-PATCH shadow (model_prepatch.py's impl region) against the
    same oracle on the F2P input. It MUST disagree: the pre-patch impl routes
    the offset through the validating public scorer, so its modelled tally is
    1 where the patched `fit` emits 0. If it agrees, this harness cannot
    refute anything and must not report a green."""
    rng = np.random.RandomState(0)
    data = rng.randn(4).reshape(-1, 1)
    real_X = make_real_X(data, True)
    oracle = oracle_fit(real_X, 0.05, 100, 0)
    base = trees.base(("selftest",), data, 100, 0)
    shadow, _ = shadow_fit(real_X, 0.05, base, impl=fit_offset_prepatch)
    if shadow["fit_advisories"] == oracle["fit_advisories"]:
        return ("HARNESS SELF-TEST FAILED: the pre-patch (buggy) shadow agrees "
                "with the real patched fit on the F2P input (both %r "
                "advisories), so this differential cannot refute a wrong "
                "model." % (oracle["fit_advisories"],))
    return None


# =============================================================================
# INPUT GENERATION -- exhaustive over the abstract space, fuzz over pre-images
# =============================================================================

# contamination is Interval(Real, 0, 0.5, closed="right") or "auto".
CONTAM_BOUNDARY = ["auto", 0.5, 0.05, 0.25, 0.4, 1e-6, 0.01, 0.1]
SHAPE_BOUNDARY = [(1, 1), (4, 1), (2, 2), (5, 3), (16, 1), (9, 7), (32, 4)]


def boundary_site2(rng):
    """Exhaustive over the abstract space (`has_labels` x
    `calibration_requested`), crossed with the boundary realizations."""
    cases = []
    # The F2P repro, exactly: pd.DataFrame(rng.randn(4), columns=["a"]),
    # IsolationForest(random_state=0, contamination=0.05).
    f2p = np.random.RandomState(0).randn(4).reshape(-1, 1)
    cases.append((f2p, True, False, 0.05, 100, 0, ("f2p",)))
    cases.append((f2p, False, False, 0.05, 100, 0, ("f2p",)))
    cases.append((f2p, True, False, "auto", 100, 0, ("f2p",)))
    cases.append((f2p, False, False, "auto", 100, 0, ("f2p",)))

    for si, (n, d) in enumerate(SHAPE_BOUNDARY):
        data = rng.randn(n, d)
        for contamination in CONTAM_BOUNDARY:
            for has_labels in (True, False):
                cases.append((data, has_labels, False, contamination,
                              3, 0, ("bshape", si)))
        # CSC-sparse unlabelled input (a legitimate has_labels=False pre-image).
        for contamination in ("auto", 0.05, 0.5):
            cases.append((np.abs(data), False, True, contamination,
                          3, 0, ("bsparse", si)))
    return cases


def fuzz_pool(rng, n_datasets=48):
    """Concrete pre-image pool. Each entry is a (dataset, n_estimators,
    random_state) whose trees the shadow can cache."""
    pool = []
    for i in range(n_datasets):
        n = rng.randint(1, 24)
        d = rng.randint(1, 6)
        scale = rng.choice([1e-3, 1.0, 25.0])
        data = rng.randn(n, d) * scale
        n_estimators = int(rng.choice([1, 2, 5]))
        random_state = int(rng.randint(0, 4))
        pool.append((data, n_estimators, random_state, ("fuzz", i)))
    return pool


def main():
    try:
        import pandas  # noqa: F401
    except ImportError as exc:
        print("status=skip pandas unavailable (%r)" % (exc,))
        print(json.dumps({"status": "skip",
                          "reason": "pandas unavailable: %r" % (exc,)}))
        return 0

    from sklearn.ensemble import IsolationForest
    if not hasattr(IsolationForest, "_score_samples"):
        # The gate applies the gold patch before running us; without the
        # patched private scorer there is no post-patch oracle to diff against.
        print("status=error IsolationForest._score_samples missing: the gold "
              "patch does not appear to be applied")
        return 1

    rng = np.random.RandomState(SEED)
    pyrng = random.Random(SEED)
    trees = TreeCache()

    # ---- harness self-test: prove the differential can refute --------------
    err = harness_self_test(trees)
    if err:
        print(err)
        return 1

    checked_site2 = 0
    checked_site1 = 0

    # ---- SITE 2 boundary battery (abstract space exhaustive) ---------------
    for case in boundary_site2(rng):
        err = diff_site2(case, trees, "boundary")
        if err:
            print(err)
            return 1
        checked_site2 += 1
    n_site2_boundary = checked_site2

    # ---- SITE 2 fuzz over the concrete pre-images of the same 4 points -----
    pool = fuzz_pool(rng)
    contam_choices = [0.5, 0.05, 0.25, 0.4, 0.001, 0.1, 0.33, 1e-6]
    for _ in range(N_SITE2_FUZZ):
        data, n_estimators, random_state, key = pool[pyrng.randrange(len(pool))]
        has_labels = pyrng.random() < 0.5
        # Keep both abstract branches of `calibration_requested` well covered.
        if pyrng.random() < 0.4:
            contamination = "auto"
        else:
            contamination = pyrng.choice(contam_choices)
        case = (data, has_labels, False, contamination, n_estimators,
                random_state, key)
        err = diff_site2(case, trees, "fuzz")
        if err:
            print(err)
            return 1
        checked_site2 += 1

    # ---- SITE 1: exhaustive over (arg_has_labels, fitted_with_labels) ------
    # Fitted estimators are cached per (dataset, fitted_with_labels); the
    # oracle call itself (real public score_samples) runs per input.
    fitted = {}

    def fitted_for(di, data, fitted_with_labels):
        est = fitted.get((di, fitted_with_labels))
        if est is None:
            est = new_forest("auto", 3, 0)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                est.fit(make_real_X(data, fitted_with_labels))
            fitted[(di, fitted_with_labels)] = est
        return est

    site1_data = [rng.randn(max(2, n), d) for (n, d) in SHAPE_BOUNDARY]
    for di, data in enumerate(site1_data):
        for fitted_with_labels in (True, False):
            est = fitted_for(di, data, fitted_with_labels)
            for arg_has_labels in (True, False):
                real_arg = make_real_X(data, arg_has_labels)
                err = diff_site1(est, fitted_with_labels, real_arg,
                                 arg_has_labels, "boundary")
                if err:
                    print(err)
                    return 1
                checked_site1 += 1
    n_site1_boundary = checked_site1

    for _ in range(N_SITE1_FUZZ):
        di = pyrng.randrange(len(site1_data))
        data = site1_data[di]
        fitted_with_labels = pyrng.random() < 0.5
        arg_has_labels = pyrng.random() < 0.5
        est = fitted_for(di, data, fitted_with_labels)
        real_arg = make_real_X(data, arg_has_labels)
        err = diff_site1(est, fitted_with_labels, real_arg, arg_has_labels,
                         "fuzz")
        if err:
            print(err)
            return 1
        checked_site1 += 1

    total = checked_site2 + checked_site1
    print("G-CONF OK: contract-stripped impl regions of model.py agree with the "
          "real patched repo functions on %d inputs, 0 disagreements. "
          "Site 2 (fit_offset vs real IsolationForest.fit): %d inputs "
          "(%d boundary incl. the F2P repro + %d fuzz), observation = "
          "(fitted_with_labels, fit_advisories, offset_set, offset_value -- the "
          "value compared bit-for-bit, stronger than the model's abstraction). "
          "Site 1 (validating_scorer vs real score_samples): %d inputs "
          "(%d boundary + %d fuzz), observation = advisory delta. The 8-point "
          "abstract input space (2 sites x has_labels x branch) is enumerated "
          "exhaustively; fuzz varies the concrete pre-images. @ContractOnly "
          "prepare/prepared_scorer call the REAL _validate_data(reset=True) / "
          "_score_samples, whose Ensures are asserted, not assumed. Pre-patch "
          "shadow self-test refuted as required. seed=%d."
          % (total, checked_site2, n_site2_boundary,
             checked_site2 - n_site2_boundary, checked_site1,
             n_site1_boundary, checked_site1 - n_site1_boundary, SEED))
    print(json.dumps({
        "checked": total,
        "checked_site2_real_fits": checked_site2,
        "checked_site1_real_score_samples": checked_site1,
        "disagreements": 0,
        "seed": SEED,
        "oracle": "called: IsolationForest.fit + IsolationForest.score_samples "
                  "(sklearn/ensemble/_iforest.py, gold patch applied)",
        "shadow": "direct (contract-stripped impl regions of model.py; "
                  "@ContractOnly prepare/prepared_scorer -> real "
                  "_validate_data(reset=True) / _score_samples)",
        "abstract_space": "finite (8 points) -- enumerated exhaustively, "
                          "fuzzed over concrete pre-images",
        "harness_self_test": "pre-patch shadow refuted",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
