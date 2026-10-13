#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13124
(nagini).

SHADOW: the impl region of model.py `per_class_draw_states`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The impl region uses no PSeq operations (PSeq appears only inside contracts),
but the @Pure helper `state_stream` copies over as a plain function on a tuple
shim and is used as a redundant spec-consistency probe on the boundary cases.
The two @ContractOnly callees the impl invokes are realized by their REAL repo
counterparts per mapping.md section 3.1:

  - `seed_state(seed)`  -> the internal state of
        sklearn.utils.check_random_state(seed) (the integer branch: a numpy
        RandomState seeded by `seed`), taken as a canonical hashable encoding
        of RandomState.get_state().
  - `advance(state)`    -> the state after the real per-class draw: restore a
        RandomState to `state`, perform the shuffle of the per-class index
        vector exactly as KFold._iter_test_indices does
        (check_random_state(rng).shuffle(np.arange(m))), and read the state
        back out.

Type bridge (mapping.md section 2): the model carries a source's internal
state as an opaque value compared only for equality (typed `int` there); any
injective encoding works, so the shadow uses the canonical tuple encoding of
RandomState.get_state(). The per-draw transition depends on the length of the
shuffled index vector, which in the modeled balanced configuration is the
same `m = max(count, n_splits)` for every class; the shadow fixes that length
per test case (module-level `_DRAW_LEN`), matching the single abstract
transition the model uses.

ORACLE: the REAL patched repo function the model models per mapping.md --
`StratifiedKFold._make_test_folds` (sklearn/model_selection/_split.py). The
gate applies patch.diff to /testbed before this script runs; PYTHONPATH=
/testbed makes the patched module importable. The diff direction: the shadow's
per-class draw states are pushed through the UNCHANGED downstream fold
bookkeeping (KFold fold sizing, the over-large-split trim, per-class
assignment -- all orthogonal to the patch per mapping.md section 2) to
reconstruct the full test-fold vector, which must equal the oracle's output
exactly. Any divergence in which state class k draws from changes class k's
permutation and hence the reconstructed vector, so state-level disagreement
is observable.

Input domain: the modeled function requires n_classes >= 0 and an integer
seed; the concrete source accepts seeds in [0, 2**32). End-to-end cases need
n_classes >= 1 (a data set must exist) and count >= n_splits per class (the
splitter's own validity guard); the n_classes == 0 boundary is checked
shadow-side against the spec stream (empty result).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases, each a
(seed, n_classes, count, n_splits) configuration diffed end-to-end.
Pinned fuzz seed: 13124.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 13124
N_FUZZ = 100_000


# --- PSeq shim (only the operations state_stream uses) ------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    """Materialize a list as a pure sequence (the Nagini ToSeq bridge)."""
    return PSeq._wrap(lst)


# --- the @ContractOnly callees, realized by their REAL repo counterparts ------

# Length of the per-class index vector the real draw shuffles; constant across
# classes in the modeled balanced configuration, set per test case.
_DRAW_LEN = 5


def _canon(state):
    """Canonical hashable encoding of a RandomState state tuple (the opaque
    state value the model compares for equality)."""
    return (state[0], state[1].tobytes(), int(state[2]), int(state[3]),
            float(state[4]))


def _restore(canon_state):
    """A RandomState positioned at the given canonical state."""
    rng = np.random.RandomState()
    rng.set_state((canon_state[0],
                   np.frombuffer(canon_state[1], dtype=np.uint32),
                   canon_state[2], canon_state[3], canon_state[4]))
    return rng


def seed_state(seed):
    """REAL callee: the initial internal state of the source that
    check_random_state builds from an integer seed."""
    from sklearn.utils import check_random_state
    return _canon(check_random_state(seed).get_state())


def advance(state):
    """REAL callee: the state after one per-class draw -- the shuffle of the
    per-class index vector performed exactly as the splitter's per-class
    KFold does it, on the source restored to `state`."""
    from sklearn.utils import check_random_state
    rng = _restore(state)
    indices = np.arange(_DRAW_LEN)
    check_random_state(rng).shuffle(indices)
    return _canon(rng.get_state())


# --- pure helper from model.py, contracts stripped ----------------------------

def state_stream(s, n):
    """The sequence of draw states for n successive classes sharing one
    advancing source that starts at state s."""
    if n == 0:
        return PSeq(0).take(0)
    return PSeq(s) + state_stream(advance(s), n - 1)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def per_class_draw_states(seed, n_classes):
    start = seed_state(seed)
    cur = start
    result = []  # type: list
    i = 0
    while i < n_classes:
        result = result + [cur]
        cur = advance(cur)
        i = i + 1
    return result
    # (impl region ends)


# --- bridge: per-class draw states -> full test-fold vector -------------------

def _perm_from_state(state, m):
    """The per-class permutation the real draw produces from a given source
    state: shuffle of the m-length index vector, as the per-class KFold does."""
    from sklearn.utils import check_random_state
    rng = _restore(state)
    indices = np.arange(m)
    check_random_state(rng).shuffle(indices)
    return indices


def shadow_test_folds(seed, n_classes, count, n_splits):
    """Reconstruct the full test-fold vector from the shadow's per-class draw
    states via the UNCHANGED downstream bookkeeping: per-class KFold fold
    sizing over the shuffled index vector, trim of indices beyond the class
    size, and per-class fold assignment (mapping.md section 2: all orthogonal
    to the modeled change)."""
    global _DRAW_LEN
    m = max(count, n_splits)
    _DRAW_LEN = m
    states = per_class_draw_states(seed, n_classes)
    fold_sizes = np.full(n_splits, m // n_splits, dtype=int)
    fold_sizes[:m % n_splits] += 1
    test_folds = np.zeros(n_classes * count, dtype=int)
    for k in range(n_classes):
        perm = _perm_from_state(states[k], m)
        cls_folds = np.zeros(count, dtype=int)
        cur = 0
        for fold_idx, fold_size in enumerate(fold_sizes):
            test_split = perm[cur:cur + fold_size]
            test_split = test_split[test_split < count]
            cls_folds[test_split] = fold_idx
            cur += fold_size
        test_folds[k * count:(k + 1) * count] = cls_folds
    return test_folds


# --- differential driver -------------------------------------------------------

def check_case(seed, n_classes, count, n_splits):
    """Run shadow (bridged) and oracle on one configuration; return an error
    string on disagreement, else None."""
    from sklearn.model_selection import StratifiedKFold
    y = np.repeat(np.arange(n_classes), count)
    X = np.zeros(len(y))
    skf = StratifiedKFold(n_splits, shuffle=True, random_state=seed)
    real = skf._make_test_folds(X, y)
    shadow = shadow_test_folds(seed, n_classes, count, n_splits)
    if not np.array_equal(shadow, real):
        return ("DISAGREEMENT\n  seed=%r n_classes=%r count=%r n_splits=%r\n"
                "  shadow=%r\n  real=%r"
                % (seed, n_classes, count, n_splits,
                   shadow.tolist(), real.tolist()))
    return None


def boundary_cases():
    """(seed, n_classes, count, n_splits) boundary configurations: extreme
    seeds, minimal and larger class counts, count == n_splits (empty trim) and
    count > n_splits (uneven folds), several split counts."""
    cases = []
    seeds = [0, 1, 2, 42, 12345, 2**31 - 1, 2**32 - 1]
    for seed in seeds:
        cases.append((seed, 1, 3, 3))     # single class, count == n_splits
        cases.append((seed, 2, 5, 5))     # two classes, count == n_splits
        cases.append((seed, 2, 7, 3))     # uneven fold sizes
        cases.append((seed, 3, 4, 2))     # minimal split count
        cases.append((seed, 5, 6, 5))
        cases.append((seed, 8, 10, 4))    # more classes: longer state stream
    return cases


def main():
    import warnings
    warnings.simplefilter("ignore")

    # n_classes == 0 boundary: no data set exists, so no oracle call -- the
    # shadow must produce the empty stream the spec pins.
    global _DRAW_LEN
    _DRAW_LEN = 5
    empty = per_class_draw_states(0, 0)
    assert empty == [] and ToSeq(empty) == state_stream(seed_state(0), 0), (
        "shadow n_classes=0 must yield the empty stream, got %r" % (empty,))

    checked = 0
    for (seed, n_classes, count, n_splits) in boundary_cases():
        err = check_case(seed, n_classes, count, n_splits)
        if err:
            print(err)
            return 1
        # redundant spec-consistency probe: the shadow output IS the advancing
        # stream from the seed's initial state (checked on boundaries only)
        _DRAW_LEN = max(count, n_splits)
        assert (ToSeq(per_class_draw_states(seed, n_classes)) ==
                state_stream(seed_state(seed), n_classes)), (
            "shadow diverged from the pure stream for seed=%r n_classes=%r"
            % (seed, n_classes))
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        seed = rng.randrange(0, 2**32)
        n_classes = rng.randint(1, 6)
        n_splits = rng.randint(2, 5)
        count = n_splits + rng.randint(0, 4)
        err = check_case(seed, n_classes, count, n_splits)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (real seed_state/advance callees, unchanged "
          "downstream bookkeeping bridge) == real patched per-class fold "
          "assignment on %d configurations (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees call the real repo "
                                "functions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
