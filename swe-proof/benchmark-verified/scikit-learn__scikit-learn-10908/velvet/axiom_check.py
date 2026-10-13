#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-10908.

Executes the REAL unchanged callees that `get_feature_names` orchestrates —
`VectorizerMixin._validate_vocabulary`, `_check_vocabulary`, and the return
projection — on real `CountVectorizer` objects over boundary + fuzzed
vocabularies and fit/unfit states, and asserts every observation matches the
DEEP MODELS of `Solution.lean` (mapping.md §3).

DIRECTIVE 7: this check NEVER calls the function under spec
(`get_feature_names`, the op the patch changes). G-AX runs in the UNPATCHED base
image, so the patched orchestration does not exist here anyway; the end-to-end
R/I fidelity of that orchestration is G-CONF's job (it runs with the gold patch
applied). G-AX validates only the unchanged callees + the I projection, and
re-assembles the establish→guard→project sequence FROM those callees by hand
(exactly `featureNamesRun`), so soundness is judged at the callee level the
deep models actually claim it.

Obligations (mapping.md §3):

  (A-reference) `materializeIndex` == `_validate_vocabulary` on the modeled
      domain (`vocabulary` is None, or a well-formed unique non-empty list):
        None       -> fixed_vocabulary_ = False, vocabulary_ unset
        [t0,t1,..] -> fixed_vocabulary_ = True,  vocabulary_ = {ti: i}

  (A-reference) `readinessGuard` == `_check_vocabulary`:
        vocabulary_ unset  -> raises (NotFittedError <: ValueError)  [notReady]
        vocabulary_ empty  -> raises ValueError("Vocabulary is empty") [emptyIndex]
        vocabulary_ present-> returns                                  [ok]

  (I, content) `featureList` == `get_feature_names`'s return: the terms of the
      index in ascending index order.

There is NO consumed axiom in this bundle; every kind-A row is an A-reference, so
G-AX validates the deep models against the real callees. Imports only `sklearn`
(present in the instance image) + stdlib. Exit 0 iff every obligation holds.
"""
import random
import sys

from sklearn.feature_extraction.text import CountVectorizer


# --- deep-model reference encodings (lock-step with Solution.lean) -----------

def materialize_index(supplied, has_index):
    """Reference of Solution.lean `materializeIndex`, returning the modeled
    post-state as (index_or_None, explicit_bool). `has_index` is irrelevant when
    supplied is a list (the model overwrites index); for supplied=None the model
    leaves index as-is (here always None at the call site)."""
    if supplied is None:
        return (None, False)               # { st with explicit := false }
    return ([(t, i) for i, t in enumerate(supplied)], True)


def feature_list(index_pairs):
    """Reference of Solution.lean `featureList`: terms in ascending index order."""
    return [t for t, i in sorted(index_pairs, key=lambda p: p[1])]


# --- the checks --------------------------------------------------------------

def check_validate_reference(supplied):
    """A-reference: materializeIndex == _validate_vocabulary on the modeled
    domain. Build a fresh CountVectorizer, drive the real callee, compare the two
    attribute writes the model pins."""
    cv = CountVectorizer(vocabulary=supplied)
    assert not hasattr(cv, "vocabulary_"), "fresh estimator must be unfitted"
    cv._validate_vocabulary()                                   # real callee

    exp_index, exp_explicit = materialize_index(supplied, has_index=False)
    assert cv.fixed_vocabulary_ == exp_explicit, (
        "explicit/fixed_vocabulary_ mismatch on %r: real=%r model=%r"
        % (supplied, cv.fixed_vocabulary_, exp_explicit))
    if exp_index is None:
        assert not hasattr(cv, "vocabulary_"), (
            "model leaves vocabulary_ unset for %r but real set it" % (supplied,))
    else:
        real_pairs = sorted(cv.vocabulary_.items(), key=lambda p: p[1])
        assert real_pairs == sorted(exp_index, key=lambda p: p[1]), (
            "vocabulary_ index mismatch on %r: real=%r model=%r"
            % (supplied, real_pairs, exp_index))


def check_guard_unfitted():
    """A-reference: readinessGuard none == _check_vocabulary raising NotReady."""
    cv = CountVectorizer()                       # vocabulary=None, never fitted
    cv._validate_vocabulary()                    # records fixed_vocabulary_=False
    assert not hasattr(cv, "vocabulary_")
    raised = False
    try:
        cv._check_vocabulary()
    except ValueError:                           # NotFittedError <: ValueError
        raised = True
    assert raised, "guard must reject the unfitted estimator (notReady)"


def check_guard_empty():
    """A-reference: readinessGuard (some []) == _check_vocabulary raising empty."""
    cv = CountVectorizer()
    cv.vocabulary_ = {}                          # established but empty index
    raised = False
    try:
        cv._check_vocabulary()
    except ValueError:
        raised = True
    assert raised, "guard must reject the empty index (emptyIndex)"


def _assemble_run(cv):
    """Re-assemble `featureNamesRun` from the unchanged callees ONLY — directive
    7: never call the function under spec (`get_feature_names`). This is the
    establish→guard→project sequence the patch introduces, but built here from
    the validated A-reference callees + the I projection, so what we exercise is
    the callees, not the patched function. Returns (outcome, fixed_vocabulary_).
    outcome is ("ok", terms-in-index-order) or ("raise",)."""
    if not hasattr(cv, "vocabulary_"):           # st.index = none
        cv._validate_vocabulary()                # materializeIndex (A-reference)
    try:
        cv._check_vocabulary()                   # readinessGuard   (A-reference)
    except ValueError:                           # NotFittedError <: ValueError
        return (("raise",), getattr(cv, "fixed_vocabulary_", "<unset>"))
    names = feature_list(list(cv.vocabulary_.items()))   # featureList (I)
    return (("ok", names), getattr(cv, "fixed_vocabulary_", "<unset>"))


def check_full_explicit_untrained(supplied):
    """End-to-end A-reference + I, assembled from callees (NOT get_feature_names):
    an explicit, never-fitted estimator establishes the index, admits the
    request, and yields the terms in index order; fixed_vocabulary_ is True."""
    cv = CountVectorizer(vocabulary=supplied)
    assert not hasattr(cv, "vocabulary_"), "fresh estimator must be unfitted"
    (outcome, flag) = _assemble_run(cv)
    index_pairs = materialize_index(supplied, has_index=False)[0]
    assert outcome == ("ok", feature_list(index_pairs)), (
        "assembled run order mismatch on %r: real=%r model=%r"
        % (supplied, outcome, ("ok", feature_list(index_pairs))))
    assert flag is True, "explicit-untrained run must set fixed_vocabulary_=True"
    for idx, name in enumerate(outcome[1]):
        assert cv.vocabulary_.get(name) == idx


def check_unfitted_no_vocab_raises_but_sets_flag():
    """The clause B2 side effect, assembled from callees (NOT get_feature_names):
    a never-fitted estimator WITHOUT a vocabulary still rejects, yet
    fixed_vocabulary_ has been recorded False by the establishment step first."""
    cv = CountVectorizer()
    (outcome, flag) = _assemble_run(cv)
    assert outcome == ("raise",), "unfitted no-vocab estimator must reject"
    assert flag is False, (
        "fixed_vocabulary_ must be recorded False even though the guard raised")


def random_vocab(rng):
    pool = ["beer", "burger", "celeri", "coke", "pizza", "salad", "sparkling",
            "tomato", "water", "and", "document", "first", "is", "one",
            "second", "the", "third", "this", "alpha", "zeta", "x", "q9"]
    n = rng.randint(1, len(pool))
    return rng.sample(pool, n)                   # unique, non-empty


def main():
    # A-reference: _validate_vocabulary boundary cases ------------------------
    boundary = [
        None,
        ["beer"],
        ["beer", "burger"],
        ["beer", "burger", "celeri", "coke", "pizza", "salad", "sparkling",
         "tomato", "water"],
        ["and", "document", "first", "is", "one", "second", "the", "third",
         "this"],
        ["z", "y", "x", "w"],                    # descending terms, index order kept
    ]
    for supplied in boundary:
        check_validate_reference(supplied)
        if supplied is not None:
            check_full_explicit_untrained(supplied)

    # A-reference: the readiness guard on both rejection shapes ----------------
    check_guard_unfitted()
    check_guard_empty()
    check_unfitted_no_vocab_raises_but_sets_flag()

    # A-reference: randomized fuzz over well-formed list vocabularies ----------
    rng = random.Random(10908)
    n_fuzz = 5000
    for _ in range(n_fuzz):
        supplied = random_vocab(rng)
        check_validate_reference(supplied)
        check_full_explicit_untrained(supplied)

    print("G-AX OK: materializeIndex/readinessGuard deep models match the real "
          "_validate_vocabulary/_check_vocabulary, and featureList matches the "
          "callee-assembled index-order projection, over %d boundary + %d fuzz "
          "vocabularies; the unfitted no-vocab reject still records "
          "fixed_vocabulary_=False. (No call to the function under spec.)"
          % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
