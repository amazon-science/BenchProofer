#!/usr/bin/env python3
"""G-CONF differential conformance for scikit-learn__scikit-learn-25973 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`runScoringRounds`) is the greedy selection loop of
`SequentialFeatureSelector.fit` (`sklearn/feature_selection/_sequential.py:283-289`),
which runs `n_iterations` consecutive scoring rounds, each reading the
cross-validation split source via `cross_val_score(..., cv=<source>, ...)`. The
CHANGED behaviour the spec pins is that EVERY round observes the FULL split
sequence — even when the `cv` source is a single-pass generator.

This is not reproducible as a pure, input-dependent R/I shadow this gate can
fuzz over >=1e5 inputs:

  * The only observable that distinguishes pre- from post-patch is a STATEFUL
    SIDE EFFECT: a one-shot generator (e.g. `LeaveOneGroupOut().split(...)`) is
    EXHAUSTED by the first round's read and yields the empty split set on every
    later read. Pre-patch, `fit` passed the raw `self.cv` into every round, so
    round 2..n saw `[]` and `_aggregate_score_dicts([])` raised
    `IndexError: list index out of range`. Reproducing this requires a live
    generator object, the real `cross_val_score` iterating it, and the
    `_aggregate_score_dicts` aggregation — i.e. the F2P integration test itself
    (`test_cv_generator_support`), not a DB-free transliteration this gate can
    fuzz.
  * The R/I content of the loop, once a re-readable source is supplied, reduces
    to "observe `source.splits` each round"; there is no input-dependent
    computation on the split CONTENTS to differentially refute. The
    discriminating fact is whether the source was BUFFERED before the loop (the
    `check_cv(...)` call the patch adds, modeled by `materialize`) — a branch
    exercised only by the live read/exhaust machinery, covered instead by
    axiom_check.py (G-AX).

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the impl region's observable is a
stateful generator-exhaustion side effect with no input-dependent, DB/CV-free
R/I shadow, set meta.json conf_skip=true and ship this status=skip stub.
Soundness of the modeled change is carried instead by G-VERIFY (the spec
provably forces every round to observe the full splits, requiring the
`materialize` step), G-DIFF (the prepatch, which omits `materialize`, fails
exactly the `obs = List.replicate k source.splits` clause for a single-pass
source), and G-AX (the real `check_cv` makes a one-shot generator re-readable
with the same split sequence, while the un-buffered baseline loses the splits on
the second read). See mapping.md section 3/4 and refinement.md section C.
"""
import sys


def main():
    print("G-CONF status=skip: scikit-learn__scikit-learn-25973 — the modeled "
          "do-block runs n_iterations scoring rounds, each reading a "
          "cross-validation split source; post-patch a check_cv(...) call "
          "buffers a possibly single-pass generator so every round observes the "
          "full splits. The only discriminating observable is a stateful "
          "generator-exhaustion side effect (round 2.. sees [] for a one-shot "
          "cv) with no input-dependent, CV-free R/I shadow. conf_skip=true. "
          "Soundness covered by G-VERIFY + G-DIFF + G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
