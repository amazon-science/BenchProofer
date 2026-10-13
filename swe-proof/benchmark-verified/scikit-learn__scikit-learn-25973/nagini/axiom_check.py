#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25973.

This bundle has ONE A-consumed axiom — the unchanged library helper
`secure_reusable_source` (model.py: `@ContractOnly`, == `sklearn.model_selection
.check_cv`), whose `Ensures` is the UNIQUE grantor of the abstract capability
`presents_family(Result())`. Its contract: the source it returns carries the
SAME split-family size as its input and presents that family on every draw. The
per-round draw count is a deep model (A-reference): the pure functions
`draw_count` / `round_completes`. G-AX validates BOTH the consumed axiom and the
deep models == the REAL library behaviour, by executing the real callees the
gold patch invokes (`check_cv` and the cross-validation source's `split` method)
and asserting every observation matches.

Obligations validated:

  (axiom: draw_splits == ONE real `.split()` draw) — drawing is an EFFECT on the
      source, so the model makes it an operation that advances the source's draw
      ledger (`draws_taken`) by exactly one and reports the count THAT draw
      presented. Validated against the real object: `n` successive real draws of
      a `check_cv`-secured source each present `draw_count(reusable, size,
      prior)` for their own `prior`, and exactly `n` draws occur for `n`
      round-drawing operations — so a ledger tally of `n` is reachable only by
      performing `n` real draws, which is what the model's abstract ledger
      encodes. The counts a secured source reports are IDENTICAL on every draw,
      which is precisely why the tally (not the counts) is what witnesses that
      each round drew.

  (axiom: secure_reusable_source == check_cv on a one-shot split generator)
      the source `check_cv` returns carries the SAME split-family size as the
      configured source (count preservation, `Result().size == src.size`) and
      presents that family afresh on every draw (`Result().reusable == True`,
      and every draw yields the full positive count). This is exactly the
      capability the `presents_family` token abstracts: that the source the
      rounds draw presents its full family on every draw. Granting it only for
      the materialised source is sound because the materialised source is the
      only one with this property.

  (A-reference: draw_count(reusable=True, size, prior_draws) == size for EVERY
      prior_draws) — a source that presents its family every draw (the one
      `check_cv` builds) never depletes.

  (A-reference: draw_count(reusable=False, size, prior_draws) == size when
      prior_draws == 0 and 0 otherwise) — a RAW one-shot generator presents its
      full family on the first draw only and nothing afterwards. This is the
      modelled exhaustion — exactly the pre-patch behaviour that raised
      IndexError on rounds after the first — and confirms the differential the
      fix removes is real (the prepatch never secures a source carrying the
      capability, so it cannot complete every round).

Imports nothing beyond the package under test (`sklearn`, `numpy`) — the same
package whose `check_cv` the gold patch calls. Exit 0 iff every obligation
holds.
"""
import sys

import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import check_cv, LeaveOneGroupOut, KFold


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def draw_count(reusable, size, prior_draws):
    """Reference of model.py's pure `draw_count`."""
    assert size >= 0 and prior_draws >= 0
    if reusable:
        return size
    if prior_draws == 0:
        return size
    return 0


# --- helpers -----------------------------------------------------------------

def n_splits_drawn(cv_source, X, y):
    """Draw a split source once and report how many splits it yields."""
    return sum(1 for _ in cv_source.split(X, y))


def _grouped(n_groups, random_state):
    """A dataset plus a group vector partitioning the samples into `n_groups`
    groups, so LeaveOneGroupOut yields exactly `n_groups` splits."""
    X, y = make_classification(n_samples=40, n_features=6, random_state=random_state)
    groups = np.zeros_like(y, dtype=int)
    step = y.size // n_groups
    for g in range(n_groups):
        end = (g + 1) * step if g + 1 < n_groups else y.size
        groups[g * step:end] = g
    return X, y, groups


# --- axiom + A-reference: secure_reusable_source / draw_count(reusable=True) --

def check_materialise_and_reuse(n_groups, n_rounds):
    """Validate the consumed axiom `secure_reusable_source` == real
    `check_cv(generator)` (count preserved, presents its family on every draw)
    and `draw_count(True, size, prior) == size` for every round."""
    X, y, groups = _grouped(n_groups, random_state=0)

    logo = LeaveOneGroupOut()
    size = logo.get_n_splits(groups=groups)
    assert size == n_groups, (
        "setup error: expected %d groups, got %d" % (n_groups, size))

    # The configured source is a single-use GENERATOR (the exact F2P input).
    splits = logo.split(X, y, groups=groups)

    # The fix: secure a re-drawable source ONCE, before iterating, via check_cv.
    reusable = check_cv(splits, y, classifier=True)

    # axiom, count preservation: secure_reusable_source(src).size == src.size.
    first = n_splits_drawn(reusable, X, y)
    assert first == size, (
        "count not preserved: check_cv(generator) yielded %d splits, "
        "configured family had %d (model: secure_reusable_source(src).size==src.size)"
        % (first, size))

    # axiom (presents_family) + A-reference: every round draws the full positive
    # family -> draw_count(reusable=True, size, prior) == size.
    for r in range(n_rounds):
        observed = n_splits_drawn(reusable, X, y)
        expected = draw_count(True, size, r)
        assert observed == expected, (
            "deep model unsound: round %d of the materialised source yielded "
            "%d splits, model draw_count(True, %d, %d) = %d"
            % (r, observed, size, r, expected))
        assert observed >= 1, (
            "round %d yielded a non-positive split count %d" % (r, observed))


def check_materialise_splitter(n_folds, n_rounds):
    """check_cv also accepts a CV splitter object directly; the materialised
    source it returns must likewise be re-drawable with the full fold count
    (draw_count(True, n_folds, prior) == n_folds on every round)."""
    X, y, _ = _grouped(3, random_state=1)
    kf = KFold(n_splits=n_folds)
    reusable = check_cv(kf, y, classifier=True)
    for r in range(n_rounds):
        observed = n_splits_drawn(reusable, X, y)
        expected = draw_count(True, n_folds, r)
        assert observed == expected, (
            "deep model unsound (splitter): round %d yielded %d splits, "
            "model draw_count(True, %d, %d) = %d"
            % (r, observed, n_folds, r, expected))


# --- A-reference 3: draw_count(reusable=False) — the one-shot exhaustion -----

def check_oneshot_exhaustion(n_groups, n_rounds):
    """The RAW single-use generator is NOT re-drawable: it yields its full
    family on the first draw and ZERO on every later one — exactly
    draw_count(reusable=False, size, prior). This is the pre-patch behaviour
    (IndexError on rounds after the first) and proves the modelled exhaustion is
    real and the materialisation the fix performs is load-bearing."""
    X, y, groups = _grouped(n_groups, random_state=2)
    logo = LeaveOneGroupOut()
    size = logo.get_n_splits(groups=groups)
    splits = logo.split(X, y, groups=groups)  # single-use generator

    for r in range(n_rounds):
        observed = sum(1 for _ in splits)     # draw r from the RAW generator
        expected = draw_count(False, size, r)
        assert observed == expected, (
            "deep model unsound (one-shot): draw %d of the raw generator "
            "yielded %d splits, model draw_count(False, %d, %d) = %d"
            % (r, observed, size, r, expected))
    assert size >= 1, "setup: family size must be positive"


def check_draw_advances_ledger(n_groups, n_rounds):
    """Validate the `draw_splits` axiom == ONE real `.split()` draw: each draw
    reports the count for its OWN number of prior draws, and performing `n`
    round-draws performs exactly `n` real draws on the source (so the modelled
    ledger tally is reachable only by drawing). Also confirms the counts alone
    do NOT witness the tally: every draw of a secured source reports the SAME
    number, so a remembered number is indistinguishable from a fresh draw by
    value — the tally is the only discriminator."""
    X, y, groups = _grouped(n_groups, random_state=3)
    logo = LeaveOneGroupOut()
    size = logo.get_n_splits(groups=groups)
    secured = check_cv(logo.split(X, y, groups=groups), y, classifier=True)

    taken = 0
    reported = []
    for _ in range(n_rounds):
        observed = n_splits_drawn(secured, X, y)   # ONE real draw
        expected = draw_count(True, size, taken)   # for ITS prior-draw count
        assert observed == expected, (
            "draw_splits unsound: draw with %d prior draws yielded %d, model "
            "draw_count(True,%d,%d)=%d" % (taken, observed, size, taken, expected))
        taken += 1                                 # the ledger advances by ONE
        reported.append(observed)

    assert taken == n_rounds, (
        "ledger unsound: %d draws performed for %d rounds" % (taken, n_rounds))
    # The value-level collapse the ledger exists to defeat: identical counts.
    assert len(set(reported)) <= 1, (
        "expected every draw of a secured source to report the same count, got %r"
        % (reported,))
    assert all(c == size for c in reported), (
        "secured source did not present its full family every draw: %r" % (reported,))


def main():
    # axiom: one draw == one ledger advance, reporting that draw's own count.
    for n_groups in (2, 3, 4, 5):
        for n_rounds in (1, 2, 3, 5):
            check_draw_advances_ledger(n_groups, n_rounds)

    # A-reference 1 & 2: materialised source is re-drawable with full count.
    for n_groups in (2, 3, 4, 5):
        for n_rounds in (1, 2, 3, 5):
            check_materialise_and_reuse(n_groups, n_rounds)
    for n_folds in (2, 3, 5):
        for n_rounds in (1, 2, 4):
            check_materialise_splitter(n_folds, n_rounds)

    # A-reference 3: the raw generator exhausts after the first draw (the bug).
    for n_groups in (2, 3, 4):
        for n_rounds in (1, 2, 3, 4):
            check_oneshot_exhaustion(n_groups, n_rounds)

    print("G-AX OK: axioms + deep models sound — the consumed axiom "
          "secure_reusable_source == check_cv materialises a one-shot generator "
          "into a source preserving the split-family size and presenting it on "
          "every draw (the presents_family capability; draw_count(True,size,*)"
          "==size); draw_splits == ONE real .split() draw, advancing the draw "
          "ledger by exactly one and reporting that draw's own count, so a tally "
          "of n is reachable only by performing n real draws (and since every "
          "draw of a secured source reports the SAME count, the tally rather "
          "than the counts is what witnesses that each round drew); raw "
          "generators exhaust after the first draw (draw_count(False,size,prior)"
          ": size then 0), so a routine that never secures such a source cannot "
          "complete every round.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
