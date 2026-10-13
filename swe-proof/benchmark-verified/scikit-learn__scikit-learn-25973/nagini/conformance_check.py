#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25973 (nagini).

Refutes (never proves) the one leg no other gate covers: does the MODEL in
`model.py` agree with the REAL gold-patched repository code it claims to model?
G-VERIFY says the impl meets the spec, G-PBT says no wrong impl meets the spec,
G-AX says the consumed axioms' contracts are sound — none of them run the greedy
selection loop of the patched repo. This script does, and exits non-zero if the
shadow and the repo disagree on even one input.

The gate applies `patch.diff` to /testbed and sets PYTHONPATH before this runs,
so every `sklearn` import below is an import of the PATCHED repository.


SHADOW (provenance "direct" — on nagini the model IS Python)
============================================================
`shadow_select_features` is the `# impl-start` / `# impl-end` region of
`model.py`'s `select_features`, copied VERBATIM with only the contract calls
deleted (`Assert`, `Invariant`, and the `# invariants-start`/`-end` markers).
Nothing is renamed, reordered, or "simplified" — the
`cv = secure_reusable_source(src)` / `used = []` / `i = 0` /
`while i < n_scorings:` / `c = draw_splits(cv)` / `keep_score(cv, c)` /
`used.append(c)` / `i = i + 1` / `return SelectionResult(used, cv)` sequence is
character-for-character the model's, because a shadow that paraphrases the impl
tests the paraphrase.

Its dependencies come across the same way:

  * the whole `# pure-start` / `# pure-end` region — `draw_count` and
    `step_completes`, contracts stripped, bodies verbatim. (`step_completes`
    is not called by the impl region; it is carried anyway and checked as a
    second leg, see "Leg 2" below, so the pure region is covered too.)
  * `SplitSource` and `SelectionResult` as plain records — the model's
    constructors are pure field stores wrapped in permission contracts, so the
    contract-stripped bodies are exactly `self.size = size` etc.
  * `secure_reusable_source`, `draw_splits` and `keep_score` are `@ContractOnly`
    in the model: they have NO body to copy. Per the contracts this shadow
    therefore CALLS / PERFORMS the real repo operations the axioms stand for and
    MEASURES the results, rather than assuming any `Ensures`:
      - `secure_reusable_source` calls `sklearn.model_selection.check_cv`
        (`_split.py:2406`, invoked by the gold patch at `_sequential.py:262`) and
        derives BOTH facets of the returned carrier by drawing the real returned
        object. So `Result().size == src.size` and `Result().reusable == True`
        are MEASURED off real `check_cv` output; if real `check_cv` ever failed
        to preserve the family size or to re-present it, the shadow would report
        the true facets and diverge from the model's spec-level claim rather than
        silently agreeing with it. It also counts what the call consumed from the
        CONFIGURED object, which is leg 3's first datum.
      - `draw_splits` performs ONE real `.split()` draw of the real secured
        object and returns the count COUNTED off that draw.
      - `keep_score` commits that draw into the shadow's journal, enforcing the
        model's alternation precondition (exactly one draw outstanding) as an
        assertion rather than assuming it.
    The bridge context these need is read from a module-level `_CTX`, NOT
    threaded through the signatures, so the impl region's own call sites stay
    character-for-character the model's.

There is no `PSeq` in this model (its only sequence is a plain `List[int]`
built by `append`), so no immutable-sequence shim is needed.


ORACLE — CALLED, not transliterated
===================================
mapping.md §1 binds `select_features(src, n_scorings)` to
`SequentialFeatureSelector.fit` (`sklearn/feature_selection/_sequential.py:189`;
the selection loop at :276-284 post-patch) together with its per-candidate draw
site `_get_best_new_feature_score` -> `cross_val_score(..., cv=cv, ...)`
(:308-315). That real patched `fit` is DRIVEN:

    sfs = SequentialFeatureSelector(_NullClassifier(), n_features_to_select=k,
                                    direction=..., tol=None, scoring=<probe>,
                                    cv=<real cv source>, n_jobs=None)
    sfs.fit(X, y)

Nothing about the mechanism under specification is re-authored here. The
`cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))` line the
patch adds, the threading of that `cv` into `_get_best_new_feature_score`, the
`cross_val_score(..., cv=cv, ...)` per-candidate draw, and the
`_aggregate_score_dicts` aggregation that raises `IndexError` on an empty draw
are all the patched repo's own code. Revert any one of them and this oracle
changes — which is the point.

The model's step index is the CANDIDATE SCORING, not the selection round: the
real `fit` performs one `cross_val_score` — hence one `cv.split(...)` draw and
one kept aggregate score — per candidate per round, so
`n_scorings = sum_{r<n_iterations}(n_features - r)` (mapping.md §1/§4.1).

How the modeled observable is read back out of the real run: the `scoring`
callable is a probe. `cross_val_score` invokes it once per split the source
yielded for that candidate, so the number of consecutive probe calls carrying
the same candidate-column signature IS the number of splits that candidate's
draw presented. X is built so `X[i, c] == c*_COL + i`, making the candidate
column set recoverable from any test row (`int(v) // _COL`); consecutive equal
signatures are grouped, one group per candidate scoring, in the repo's own
order. `tol=None` with an INTEGER `n_features_to_select` makes `is_auto_select`
False (:275), so the repo loop cannot `break` early and runs exactly
`n_iterations` rounds, hence exactly `n_scorings` candidate scorings — matching
the model's unconditional `while i < n_scorings`.

Two further OBSERVATION-ONLY probes supply leg 3, and neither re-authors
anything: (a) the object handed to the estimator as `cv=` is a counting
realization that records every fresh consumption of ITSELF, which is
`draws_taken(src)` for the configured source; (b)
`_sequential.cross_val_score` is temporarily replaced by a recorder that logs
the identity of the `cv=` argument and then CALLS THE REAL FUNCTION, which
attributes each kept score to the object it was aggregated from — the model's
`scores_kept(src)` vs `scores_kept(Result().cv)`. Both are restored in a
`finally`.

The oracle is allowed to RAISE, and a raise is recorded as a DISAGREEMENT (the
shadow always returns counts). That is not defensive noise: it is the reported
failure mode itself. Run with the gold patch REVERTED, the one-shot-generator
inputs below make the second candidate scoring draw an exhausted source,
`cross_val_score` returns an empty score array, `_aggregate_score_dicts` indexes
`scores[0]` and raises `IndexError: list index out of range` — and this script
reports disagreements and exits 1. Leg 3 refutes the pre-patch code a second,
independent way: unpatched, the configured object is consumed once per candidate
scoring and every kept score is attributed to it, so `draws_taken(src) > 1` and
`scores_kept(src) > 0`.


TYPE BRIDGE (mapping.md §2, inverted)
=====================================
The model works over the abstract carrier; the real `fit` wants a real cv
object, a real X/y, and a real estimator. Both directions are explicit.

  model -> repo (`concretize_source`), mapping.md §2 row 1:
    `SplitSource(size, reusable=False)` -> a single-traversal GENERATOR over
        `size` explicit `(train, test)` index pairs. This is the reported input
        shape (`LeaveOneGroupOut().split(...)` is exactly such a generator) and
        the only carrier value for which the patch's behaviour differs.
    `SplitSource(size, reusable=True)` -> one of the three re-presenting
        realizations, cycled over so each is exercised: a LIST of the same
        `size` pairs (check_cv's `_CVIterableWrapper` path), a `KFold(size)`
        splitter (check_cv's pass-through path), or the INTEGER `size`
        (check_cv's `StratifiedKFold(size)` construction path).
    `n_scorings` -> `n_features_to_select=k` with `direction`, chosen so the
        repo's own arithmetic (:268-272 for the round count, :300 for the
        per-round candidate list) yields exactly the modeled value: forward gives
        `sum_{r<k}(n_features - r)`, backward `sum_{r<n_features-k}(n_features -
        r)`. Both directions are generated.

  repo -> model (`abstract_source`): a real cv object -> `SplitSource`, with
    `size` = the number of `(train, test)` pairs one `.split(X, y)` draw yields
    and `reusable` = whether a SECOND draw presents that same positive family
    again. Both facets are counted off real draws; neither is assumed.

X/y are synthetic and minimal: `n_samples = 2 * max(size, 3)` with alternating
labels, so every class holds at least `size` members and `StratifiedKFold(size)`
is legal; `n_features` in 2..7 (the repo's `ensure_min_features=2` at :222).
The estimator is a trivial constant classifier and the scorer returns a
constant, so no numeric behaviour of any real model can perturb the observable
— the split counts alone are compared.

Every generated input satisfies `select_features`'s Requires by construction:
`src.size >= 1 > 0`, `n_scorings >= 1`, and both of the configured object's
ledgers stand at 0 because it is built fresh for the trial. The domain is never
narrowed to dodge a branch; in particular `reusable=False` (the one-shot
generator, the branch the gold patch changed) is generated in the enumeration
AND in the fuzz.


INPUT SPACE — exhaustive, then fuzzed to 1e5
============================================
The modeled input space reachable through the real `fit` is FINITE and smaller
than 1e5: the carrier is `(size, reusable-realization, n_scorings)` and the repo
bounds the round count by `n_features - 1`, so with `size` in 1..6,
`n_features` in 2..7 and both directions the whole space is _ENUM_SIZE configs
(printed in the summary). This script therefore ENUMERATES that space
EXHAUSTIVELY first — every `(size, realization, n_features, direction, k)`
combination, so every branch of the shadow and every check_cv path is taken —
and then FUZZES over the same space with a pinned seed to reach the required
count. Exhaustive coverage of a finite space is a strictly stronger check than
1e5 samples of it, not a weaker one; the fuzz phase adds ordering diversity and
the required volume.

The fuzz phase samples with weight 1/`trial_cost` (a trial's cost is the number
of real splits it drives, on both sides) so 1e5 real `fit` runs fit inside the
gate's 1800s container budget. That reweighting shifts only the MIX, never the
SUPPORT: every config keeps positive probability, and each was already executed
exactly once in the exhaustive phase, so no configuration and no branch is
dropped. The weighting buys headroom on a loaded host; it does not buy the
green, since the exhaustive phase alone already covers every modeled config.

Boundary cases are enumerated first and explicitly, before anything else:
`size == 1` (singleton split family, the smallest satisfying `src.size > 0`),
`n_scorings == 1` (a single candidate scoring — the pre-patch code is CORRECT
here, so this is the case that must NOT be flagged), a one-shot generator with
more than one candidate scoring (the exact F2P shape: exhaustion would bite from
the second scoring on), `n_features == 2` (the repo's minimum), and each of the
four check_cv input paths (generator / list / splitter / integer).

Leg 1 (the impl region): shadow `counts` and `(cv.size, cv.reusable)` vs the
real patched `fit`'s per-scoring split counts and the family the scorings drew.
Leg 2 (the pure region): `step_completes(cv.reusable, cv.size, i)` vs whether
scoring i of the real run actually produced a usable score, for every scoring.
Leg 3 (the ledgers): the model's four ledger postconditions against tallies
MEASURED on both sides — the shadow's own draw/keep tallies and journal, and the
real run's measured `draws_taken` / `scores_kept` for the secured source AND for
the configured source. This is the leg that would catch a spec whose ledger
clauses are true of the model but false of the repo; it is also the leg that
refutes the pre-patch code independently of the `IndexError`.

Exit 0 iff zero disagreements over all three legs. stdlib + the package under
test.
"""
import random
import sys
from typing import List

import numpy as np
from sklearn.base import BaseEstimator, is_classifier
from sklearn.feature_selection import SequentialFeatureSelector
import sklearn.feature_selection._sequential as _SEQ
from sklearn.model_selection import KFold, check_cv

# Pinned fuzz seed (recorded in mapping.md, ## G-CONF section).
SEED = 25973
TARGET_INPUTS = 100_000

# Column-tagging stride for the type bridge: X[i, c] == c * _COL + i, so a
# candidate's column set is recoverable from any test row as int(v) // _COL.
_COL = 1000


# ===========================================================================
# SHADOW — model.py's regions, contracts stripped, otherwise verbatim.
# ===========================================================================

class SplitSource:
    """model.py `SplitSource`, contract-stripped (the body is a field store)."""

    def __init__(self, size, reusable):
        self.size = size
        self.reusable = reusable
        # Shadow-only bookkeeping for the @ContractOnly operations: the real
        # object to draw, and the two ledgers + journal the model tracks
        # abstractly (`draws_taken`, `scores_kept`, `score_from_draw`).
        self.real = None
        self.taken = 0
        self.kept = 0
        self.journal = []


class SelectionResult:
    """model.py `SelectionResult`, contract-stripped (the body is a field store)."""

    def __init__(self, counts, cv):
        self.counts = counts
        self.cv = cv


# --- model.py `# pure-start` .. `# pure-end`, contracts stripped ------------

def draw_count(reusable, size, prior_draws):
    if reusable:
        return size
    if prior_draws == 0:
        return size
    return 0


def step_completes(reusable, size, prior_draws):
    return draw_count(reusable, size, prior_draws) > 0


# --- model.py `secure_reusable_source` is @ContractOnly: no body to copy, so
# --- CALL the real repo function it axiomatizes and MEASURE the result's
# --- facets off real draws (mapping.md §1/§3.1: sklearn.model_selection
# --- .check_cv, `_split.py:2406`, invoked by the patch at `_sequential.py:262`).

def secure_reusable_source(src):
    """The @ContractOnly callee, realized by the REAL repo callee.

    `check_cv` is called exactly as the gold patch calls it, then BOTH facets of
    the returned carrier are counted off real draws of the real object, and what
    the call consumed from the CONFIGURED object is counted too. Nothing from
    the axiom's `Ensures` is assumed here.

    The bridge context this needs (which real cv realization, and the real X/y/
    estimator to draw against) is read from the module-level `_CTX` that
    `compare()` sets, NOT threaded through the signature — so the impl region
    below stays character-for-character the model's.
    """
    real_src = concretize_source(src, _CTX["X"], _CTX["y"], kind=_CTX["kind"])
    checked = check_cv(real_src, _CTX["y"],
                       classifier=is_classifier(_CTX["estimator"]))
    carrier = abstract_source(checked, _CTX["X"], _CTX["y"])
    # What the securing call itself consumed from the CONFIGURED object: the
    # axiom's `Implies(src.reusable == False, draws_taken(src) == Old(..) + 1)`
    # and `scores_kept(src) == Old(scores_kept(src))`, MEASURED (leg 3).
    src.taken = _draws_of(real_src)
    # Retain the REAL secured object so `draw_splits` below can draw IT, and
    # start the ledgers at 0 (the axiom's `draws_taken/scores_kept == 0`).
    carrier.real = checked
    carrier.taken = 0
    carrier.kept = 0
    carrier.journal = []
    return carrier


# --- model.py `draw_splits` is @ContractOnly: no body to copy, so PERFORM the
# --- real per-scoring draw it axiomatizes — one real `.split()` of the real
# --- secured object (mapping.md §1: the `cv.split(...)` draw inside
# --- `cross_val_score`, `_sequential.py:308-315` -> `_validation.py:274`) — and
# --- advance the ledger. Nothing from the axiom's `Ensures` is assumed: the
# --- count is COUNTED off the real draw, so if a real secured source ever
# --- depleted, the shadow would report the true count and diverge from the model
# --- rather than agree with it.

def draw_splits(cv):
    """One real draw of the real secured source; the ledger advances by one."""
    assert cv.taken == cv.kept, "draw with a draw already outstanding"
    count = sum(1 for _ in cv.real.split(_CTX["X"], _CTX["y"]))
    cv.taken += 1
    return count


# --- model.py `keep_score` is @ContractOnly: no body to copy. It models the one
# --- aggregate score a candidate scoring keeps from its OWN draw — the
# --- `cross_val_score(..., cv=cv, ...).mean()` value stored at
# --- `_sequential.py:308-315`, aggregated over exactly that draw's splits
# --- (`_validation.py:309`). Here it commits the count into the journal and
# --- advances the second ledger, ENFORCING (not assuming) the model's
# --- alternation precondition: exactly one draw outstanding, and the committed
# --- count is that draw's own.

def keep_score(cv, c):
    """Commit the score built from the single outstanding draw."""
    assert cv.taken == cv.kept + 1, "keep_score without exactly one draw outstanding"
    cv.journal.append(c)
    cv.kept += 1


# --- model.py `select_features` `# impl-start` .. `# impl-end`, VERBATIM
# --- minus `Assert(...)` and the `# invariants-start`/`-end` block. -------

def shadow_select_features(src, n_scorings):
    # impl-start
    cv = secure_reusable_source(src)  # type: SplitSource
    used = []  # type: List[int]
    i = 0
    while i < n_scorings:
        # step i draws the secured source (`i` draws preceded it) and keeps the
        # score built from that draw before the next step draws.
        c = draw_splits(cv)  # type: int
        keep_score(cv, c)
        used.append(c)
        i = i + 1
    return SelectionResult(used, cv)
    # impl-end


# ===========================================================================
# TYPE BRIDGE (mapping.md §2, inverted)
# ===========================================================================

def _pairs(n_samples, size):
    """`size` explicit (train, test) index pairs over `n_samples` samples."""
    out = []
    for j in range(size):
        t = j % n_samples
        train = np.array([i for i in range(n_samples) if i != t], dtype=int)
        out.append((train, np.array([t], dtype=int)))
    return out


# The re-presenting realizations of `reusable == True`, one per check_cv path.
REUSABLE_KINDS = ("list", "splitter", "integer")
ONESHOT_KIND = "generator"
ALL_KINDS = (ONESHOT_KIND,) + REUSABLE_KINDS


# Bridge context for the @ContractOnly callees (see `secure_reusable_source`).
_CTX = {"kind": ONESHOT_KIND, "X": None, "y": None, "estimator": None}


class _CountingGen:
    """A single-traversal split generator that records every fresh consumption
    of ITSELF — the observable behind `draws_taken(src)` for a one-shot
    configured source. Exhausts after the first traversal, exactly as
    `LeaveOneGroupOut().split(...)` does."""

    def __init__(self, items):
        self._it = iter(list(items))
        self.draws = 0

    def __iter__(self):
        self.draws += 1
        return self

    def __next__(self):
        return next(self._it)


class _CountingList(list):
    """A re-presenting iterable that records every fresh consumption of itself."""

    def __init__(self, items):
        super().__init__(items)
        self.draws = 0

    def __iter__(self):
        self.draws += 1
        return super().__iter__()


class _CountingKFold(KFold):
    """A new-style splitter (check_cv's pass-through path) that records every
    `.split()` call on itself."""

    def __init__(self, n_splits):
        super().__init__(n_splits=n_splits)
        self.draws = 0

    def split(self, X=None, y=None, groups=None):
        self.draws += 1
        return super().split(X, y, groups)


def _draws_of(real_src):
    """How many draws have been taken off a configured cv realization. An
    INTEGER realization is not a drawable object at all (check_cv builds a fresh
    splitter from it and the integer itself is never consumed), so it is 0 by
    construction."""
    return getattr(real_src, "draws", 0)


def concretize_source(src, X, y, kind=None):
    """model -> repo: a `SplitSource` carrier becomes a real cv object.

    `reusable == False` is the single-traversal generator (the reported input
    shape); `reusable == True` is whichever re-presenting realization the
    carrier was tagged with. Every drawable realization counts its own
    consumptions, which is what leg 3 reads.
    """
    if kind is None:
        kind = "list" if src.reusable else ONESHOT_KIND
    n_samples = X.shape[0]
    if kind == ONESHOT_KIND:
        return _CountingGen(_pairs(n_samples, src.size))
    if kind == "list":
        return _CountingList(_pairs(n_samples, src.size))
    if kind == "splitter":
        return _CountingKFold(n_splits=src.size)
    if kind == "integer":
        return int(src.size)
    raise AssertionError("unknown cv realization %r" % (kind,))


def abstract_source(cv_obj, X, y):
    """repo -> model: a real cv object becomes a `SplitSource`.

    `size` is the family one draw presents; `reusable` is whether a SECOND draw
    presents that same positive family again. Both are counted off real draws.
    """
    first = sum(1 for _ in cv_obj.split(X, y))
    second = sum(1 for _ in cv_obj.split(X, y))
    return SplitSource(first, second == first and first > 0)


def make_X_y(n_samples, n_features):
    """Minimal real data. X[i, c] == c*_COL + i tags each column so the
    candidate column set is recoverable from any test row; labels alternate so
    each class holds n_samples // 2 members (StratifiedKFold legality)."""
    X = np.empty((n_samples, n_features), dtype=float)
    for c in range(n_features):
        for i in range(n_samples):
            X[i, c] = c * _COL + i
    y = np.array([i % 2 for i in range(n_samples)], dtype=int)
    return X, y


class _NullClassifier(BaseEstimator):
    """A trivial constant classifier: `is_classifier` is True (so the real
    `check_cv(..., classifier=True)` path the patch takes is exercised) and no
    numeric model behaviour can perturb the observed split counts."""

    _estimator_type = "classifier"

    def fit(self, X, y=None):
        self.classes_ = np.array([0, 1])
        return self

    def predict(self, X):
        return np.zeros(X.shape[0], dtype=int)


def n_scorings_of(n_features, direction, k):
    """The model's `n_scorings` from the repo's own arithmetic: one candidate
    scoring per candidate per round (`:268-272` rounds, `:300` candidates).
    Machine-measured against the real patched fit in mapping.md §4.1."""
    n_iterations = k if direction == "forward" else n_features - k
    return sum(n_features - r for r in range(n_iterations))


# ===========================================================================
# ORACLE — drive the REAL patched SequentialFeatureSelector.fit
# ===========================================================================

def oracle_fit(size, kind, n_features, direction, k):
    """Run the REAL patched `fit` and read back, per candidate scoring, how many
    splits that scoring's draw presented, plus the measured ledgers of both the
    secured and the configured source.

    Returns (counts, ledgers, error). `counts[i]` is the split count scoring i's
    draw presented. `ledgers` is a dict with the measured
    `src_draws` / `src_kept` / `secured_kept` tallies. `error` is a string if the
    real `fit` raised or the draw stream did not segment into the expected number
    of scorings; both are recorded as disagreements.
    """
    n_samples = 2 * max(size, 3)
    X, y = make_X_y(n_samples, n_features)
    estimator = _NullClassifier()
    cv_obj = concretize_source(SplitSource(size, kind != ONESHOT_KIND), X, y,
                               kind=kind)

    calls = []

    def probe(est, X_test, y_test):
        row = np.asarray(X_test)
        sig = () if row.size == 0 else tuple(sorted({int(v) // _COL for v in row[0]}))
        calls.append(sig)
        return 0.5

    # OBSERVATION-ONLY recorders: note WHICH OBJECT the patched fit secured, and
    # which object each candidate scoring was handed as `cv=`, then CALL THE REAL
    # check_cv / cross_val_score. This attributes each kept score to the object
    # it was aggregated from (the model's `scores_kept`), and re-authors nothing.
    #
    # The secured object is identified by capturing what the repo's OWN
    # `check_cv` call returned rather than by "anything that is not the
    # configured object". On check_cv's pass-through path (a new-style splitter,
    # `_split.py:2462` `return cv`) the two are the SAME object, so a
    # not-the-configured-one test would attribute every kept score away from the
    # source the scorings actually drew and read `scores_kept(Result().cv) == 0`
    # on a run that kept one score per scoring. Both tallies are therefore
    # counted independently, and on the pass-through path both advance — which is
    # precisely the case the model states its configured-source clauses
    # conditionally for (refinement.md A3c / §B pin 4).
    kept = {"src": 0, "secured": 0}
    real_cvs = _SEQ.cross_val_score
    real_check_cv = _SEQ.check_cv
    secured = {"obj": None}

    def recording_check_cv(cv, y=None, classifier=False):
        out = real_check_cv(cv, y, classifier=classifier)
        secured["obj"] = out
        return out

    def recording_cvs(estimator_, X_, y_=None, **kw):
        given = kw.get("cv")
        out = real_cvs(estimator_, X_, y_, **kw)
        # the aggregate score exists and is about to be kept
        if given is secured["obj"]:
            kept["secured"] += 1
        if given is cv_obj:
            kept["src"] += 1
        return out

    sfs = SequentialFeatureSelector(
        estimator, n_features_to_select=k, direction=direction, tol=None,
        scoring=probe, cv=cv_obj, n_jobs=None)
    _SEQ.cross_val_score = recording_cvs
    _SEQ.check_cv = recording_check_cv
    try:
        sfs.fit(X, y)
    except Exception as exc:                     # a raise IS a disagreement
        return [], {}, "%s: %s" % (type(exc).__name__, str(exc)[:120])
    finally:
        _SEQ.cross_val_score = real_cvs
        _SEQ.check_cv = real_check_cv

    ledgers = {"src_draws": _draws_of(cv_obj), "src_kept": kept["src"],
               "secured_kept": kept["secured"]}

    # Consecutive probe calls with the same candidate signature = one draw, i.e.
    # one candidate scoring, in the repo's own order.
    draws = []
    for sig in calls:
        if draws and draws[-1][0] == sig:
            draws[-1][1] += 1
        else:
            draws.append([sig, 1])

    expected = n_scorings_of(n_features, direction, k)
    if len(draws) != expected:
        return [], ledgers, ("recovered %d candidate scorings, repo performs %d"
                             % (len(draws), expected))
    return [c for (_sig, c) in draws], ledgers, None


# ===========================================================================
# DIFF
# ===========================================================================

def compare(size, kind, n_features, direction, k):
    """One differential trial. Returns None on agreement, else a report dict."""
    n_scorings = n_scorings_of(n_features, direction, k)
    n_samples = 2 * max(size, 3)
    X, y = make_X_y(n_samples, n_features)
    estimator = _NullClassifier()

    _CTX.update(kind=kind, X=X, y=y, estimator=estimator)
    src = SplitSource(size, kind != ONESHOT_KIND)
    shadow = shadow_select_features(src, n_scorings)

    counts, ledgers, error = oracle_fit(size, kind, n_features, direction, k)
    if error is not None:
        return {"leg": 1, "reason": "real fit did not produce %d clean candidate "
                                    "scorings" % n_scorings,
                "oracle_error": error, "shadow_counts": list(shadow.counts)}

    # Leg 1: the impl region's observable.
    if list(shadow.counts) != list(counts):
        return {"leg": 1, "reason": "per-scoring split counts differ",
                "shadow_counts": list(shadow.counts), "oracle_counts": list(counts)}
    if len(shadow.counts) != n_scorings:
        return {"leg": 1, "reason": "shadow recorded %d scorings, expected %d"
                                    % (len(shadow.counts), n_scorings)}
    # The family the scorings drew: size preserved and re-presented (measured).
    if shadow.cv.size != size:
        return {"leg": 1, "reason": "secured family size %d != configured %d"
                                    % (shadow.cv.size, size)}
    if shadow.cv.reusable is not True:
        return {"leg": 1, "reason": "real check_cv result did not re-present its "
                                    "family (shadow cv.reusable is False)"}

    # Leg 2: the pure region — step_completes vs "scoring i produced a score".
    for i in range(n_scorings):
        modeled = step_completes(shadow.cv.reusable, shadow.cv.size, i)
        real = counts[i] > 0
        if modeled != real:
            return {"leg": 2, "reason": "step_completes(%r) != real scoring %d "
                                        "completing (%r)" % (modeled, i, real)}

    # Leg 3: the LEDGERS, measured on BOTH sides against the model's four
    # ledger postconditions. The shadow tallies come from real draws it
    # performed; the oracle tallies come from the real run (the counting cv
    # realization and the pass-through cross_val_score recorder), so this leg is
    # a measurement of the repository, not a restatement of the model.
    #   Ensures(draws_taken(Result().cv) == n_scorings)
    if shadow.cv.taken != n_scorings:
        return {"leg": 3, "reason": "shadow took %d real draws of the secured "
                                    "source, expected one per scoring (%d)"
                                    % (shadow.cv.taken, n_scorings)}
    #   Ensures(scores_kept(Result().cv) == n_scorings)  -- both sides
    if shadow.cv.kept != n_scorings:
        return {"leg": 3, "reason": "shadow kept %d scores off the secured "
                                    "source, expected %d"
                                    % (shadow.cv.kept, n_scorings)}
    if ledgers["secured_kept"] != n_scorings:
        return {"leg": 3, "reason": "real fit kept %d scores off the source it "
                                    "secured, model says %d"
                                    % (ledgers["secured_kept"], n_scorings)}
    #   Ensures(counts[k] == score_from_draw(Result().cv, k))
    if list(shadow.cv.journal) != list(shadow.counts):
        return {"leg": 3, "reason": "reported record is not the journal the kept "
                                    "scores wrote",
                "journal": list(shadow.cv.journal),
                "counts": list(shadow.counts)}
    #   Ensures(Implies(src.reusable == False, scores_kept(src) == 0)) -- no kept
    #   score came off a draw of the CONFIGURED source. This is the clause the
    #   pre-patch code violates.
    #
    #   The "splitter" realization is check_cv's PASS-THROUGH path, where the
    #   real call returns its own argument: there the secured source IS the
    #   configured source, so every kept score is legitimately attributed to it
    #   and `scores_kept(src) == n_scorings`. That is exactly why the model
    #   states this clause for the one-shot case only (mapping.md §2, refinement
    #   .md A3c). The check is applied to the three realizations on which
    #   check_cv returns a DISTINCT object — a strictly wider domain than the
    #   spec claims, so it can still refute — and skipped on the pass-through
    #   one, where a zero would be the wrong expectation rather than a stronger
    #   one.
    if kind != "splitter" and ledgers["src_kept"] != 0:
        return {"leg": 3, "reason": "real fit kept %d scores off a draw of the "
                                    "CONFIGURED source (%s realization, on which "
                                    "check_cv returns a distinct object); model "
                                    "says 0" % (ledgers["src_kept"], kind)}
    if kind == "splitter" and ledgers["src_kept"] != n_scorings:
        return {"leg": 3, "reason": "check_cv pass-through path: the secured "
                                    "source IS the configured one, so every kept "
                                    "score should be attributed to it (%d), got %d"
                                    % (n_scorings, ledgers["src_kept"])}
    #   Ensures(Implies(src.reusable == False, draws_taken(src) == 1)) -- both
    #   sides: the securing call's own consumption (shadow) and the whole real
    #   run's (oracle).
    if kind == ONESHOT_KIND:
        if src.taken != 1:
            return {"leg": 3, "reason": "securing call consumed the one-shot "
                                        "configured source %d times, model says 1"
                                        % src.taken}
        if ledgers["src_draws"] != 1:
            return {"leg": 3, "reason": "real fit consumed the one-shot configured "
                                        "source %d times over the whole run, "
                                        "model says exactly 1"
                                        % ledgers["src_draws"]}
    return None


def enumerate_space():
    """The whole finite modeled space reachable through the real `fit`.

    Boundary configs first and explicitly, then every remaining combination of
    (size, check_cv realization, n_features, direction, k).
    """
    space = []
    seen = set()

    def add(size, kind, n_features, direction, k):
        key = (size, kind, n_features, direction, k)
        if key in seen:
            return
        seen.add(key)
        space.append(key)

    # --- boundaries, first ---
    add(1, ONESHOT_KIND, 2, "forward", 1)        # size==1, fewest scorings
    add(1, ONESHOT_KIND, 3, "forward", 2)        # size==1, many one-shot scorings
    add(2, ONESHOT_KIND, 2, "forward", 1)        # 2 scorings, one-shot
    add(2, ONESHOT_KIND, 3, "forward", 2)        # F2P shape: exhaustion bites
    add(2, ONESHOT_KIND, 7, "forward", 6)        # deepest one-shot scoring count
    add(2, ONESHOT_KIND, 3, "backward", 1)       # one-shot, backward direction
    for kind in REUSABLE_KINDS:                  # each check_cv path, min config
        add(2, kind, 2, "forward", 1)
        add(2, kind, 3, "forward", 2)

    # --- the rest of the finite space ---
    for size in range(1, 7):
        for kind in ALL_KINDS:
            if kind == "integer" and size < 2:
                continue                          # StratifiedKFold needs >= 2
            if kind == "splitter" and size < 2:
                continue                          # KFold needs n_splits >= 2
            for n_features in range(2, 8):
                for k in range(1, n_features):
                    add(size, kind, n_features, "forward", k)
                    add(size, kind, n_features, "backward", k)
    return space


def trial_cost(cfg):
    """Number of real splits one trial drives, on both sides — the trial's
    runtime, to within a constant. Used ONLY to weight the fuzz phase (below);
    it never removes a config, since phase 1 already ran every one of them."""
    size, _kind, n_features, direction, k = cfg
    return 2 * n_scorings_of(n_features, direction, k) * size + 1


def main():
    space = enumerate_space()
    rng = random.Random(SEED)

    checked = 0
    disagreements = 0
    first = None

    # Phase 1: EXHAUSTIVE over the finite modeled space.
    for cfg in space:
        report = compare(*cfg)
        checked += 1
        if report is not None:
            disagreements += 1
            if first is None:
                first = (cfg, report)

    exhaustive = checked

    # Phase 2: seeded fuzz over the SAME space to reach the required count.
    # Sampled with weight 1/cost so the run fits the gate's container budget;
    # this shifts only the MIX, never the support — every config in `space`
    # keeps positive probability here and was already run exactly once in phase
    # 1, so no branch is dropped and nothing is silently truncated.
    weights = [1.0 / trial_cost(cfg) for cfg in space]
    while checked < TARGET_INPUTS and disagreements == 0:
        cfg = rng.choices(space, weights=weights, k=1)[0]
        report = compare(*cfg)
        checked += 1
        if report is not None:
            disagreements += 1
            if first is None:
                first = (cfg, report)

    if disagreements:
        cfg, report = first
        size, kind, n_features, direction, k = cfg
        print("G-CONF FAIL: shadow of model.py's impl region disagrees with the "
              "real patched SequentialFeatureSelector.fit")
        print("  input (model carrier): SplitSource(size=%d, reusable=%r), "
              "n_scorings=%d" % (size, kind != ONESHOT_KIND,
                                 n_scorings_of(n_features, direction, k)))
        print("  input (repo bridge):   cv=%s, n_features=%d, direction=%s, "
              "n_features_to_select=%d" % (kind, n_features, direction, k))
        print("  disagreement: %r" % (report,))
        print("  %d disagreement(s) over %d inputs" % (disagreements, checked))
        return 1

    print("G-CONF OK: %d inputs (%d = the ENTIRE finite modeled space, "
          "exhaustively; %d seeded 1/cost-weighted fuzz over that same space, "
          "full support, seed=%d), 0 disagreements. Shadow = "
          "model.py impl region verbatim (contracts stripped), @ContractOnly "
          "secure_reusable_source / draw_splits / keep_score realized by the "
          "REAL sklearn.model_selection.check_cv and real draws/aggregations, "
          "with both carrier facets and all four ledgers measured off real "
          "events; oracle = the REAL patched SequentialFeatureSelector.fit "
          "driven end-to-end, per-candidate-scoring split counts read back "
          "through the scoring probe. Legs: per-scoring counts + secured family "
          "(impl region), step_completes (pure region), and the four ledger "
          "postconditions measured on BOTH sides incl. the CONFIGURED source's "
          "own draw/kept tallies (1 draw, 0 kept scores; on check_cv's "
          "pass-through path, where the secured source IS the configured one, "
          "the kept scores are checked to be attributed to it instead). "
          "One-shot-generator "
          "inputs (the branch the gold patch changed) covered; unpatched, this "
          "script exits 1." % (checked, exhaustive, checked - exhaustive, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
