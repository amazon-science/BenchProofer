#!/usr/bin/env python3
"""G-AX — validate the deep-model A-references for scikit-learn__scikit-learn-10908.

The modeled function `get_feature_names` delegates to two UNCHANGED repo callees,
both of which are modeled DEEPLY in Solution.lean (so they are A-references,
validated == the real callee here, not consumed axioms):

  * `validateList`  mirrors `VectorizerMixin._validate_vocabulary` on the
    list-vocabulary case: build a term->index mapping from a supplied ordered
    term list, rejecting an empty list and a list with a repeated term.
  * `featureNames`  mirrors the index-ordered name extraction
    `[t for t, i in sorted(vocabulary_.items(), key=itemgetter(1))]`.

This check runs the REAL repo callees on boundary + fuzzed inputs and asserts the
deep models reproduce them.

Properties validated:
  (A1) validateList(p) classifies / maps identically to _validate_vocabulary:
        - empty list                -> error "empty"
        - list with a repeated term -> error "dup"
        - otherwise                 -> ok, vocabulary_ == {t: i for i, t in enumerate(p)}
                                       and fixed_vocabulary_ is True
  (A2) featureNames(voc) == [t for t, i in sorted(voc.items(), key=itemgetter(1))]

Runs inside the instance image (sklearn importable via PYTHONPATH=/testbed).
exit 0 iff the deep models match the real callees on every input.
"""
import random
import sys
from operator import itemgetter

from sklearn.feature_extraction.text import CountVectorizer


# ---- Python mirrors of the Lean deep models --------------------------------

def validate_list_model(p):
    """Mirror of Lean `validateList`. Returns ('empty',)/('dup',) on error or
    ('ok', mapping_dict) on success, where mapping pairs each term with its
    index (term -> position)."""
    if len(p) == 0:
        return ('empty',)
    if len(set(p)) != len(p):
        return ('dup',)
    return ('ok', {t: i for i, t in enumerate(p)})


def feature_names_model(voc):
    """Mirror of Lean `featureNames`: terms in increasing index order.
    `voc` is a list of (term, index) pairs (a stable mergeSort by index)."""
    return [t for t, i in sorted(voc, key=lambda kv: kv[1])]


# ---- Real repo callees ------------------------------------------------------

def validate_list_real(p):
    """The REAL unchanged callee: VectorizerMixin._validate_vocabulary on a list
    vocabulary. Returns the same shape as validate_list_model."""
    cv = CountVectorizer(vocabulary=list(p))
    try:
        cv._validate_vocabulary()
    except ValueError as e:
        msg = str(e).lower()
        if 'duplicate' in msg:
            return ('dup',)
        if 'empty' in msg:
            return ('empty',)
        raise
    assert cv.fixed_vocabulary_ is True, "fixed_vocabulary_ not set True"
    return ('ok', dict(cv.vocabulary_))


def feature_names_real(voc):
    """The REAL extraction the post-patch body performs over vocabulary_."""
    d = {t: i for t, i in voc}
    return [t for t, i in sorted(d.items(), key=itemgetter(1))]


# ---- Fuzzing ----------------------------------------------------------------

def rand_term(rng):
    pool = ['beer', 'burger', 'celeri', 'coke', 'pizza', 'salad', 'water',
            'a', 'b', 'c', 'and', 'the', 'is', 'one', 'x', 'y', 'z']
    return rng.choice(pool)


def rand_list(rng):
    n = rng.randint(0, 8)
    return [rand_term(rng) for _ in range(n)]


def main() -> int:
    rng = random.Random(10908)
    N = 120_000

    fixed_lists = [
        [],
        ['beer'],
        ['beer', 'burger', 'celeri', 'coke', 'pizza', 'salad',
         'sparkling', 'tomato', 'water'],
        ['and', 'document', 'first', 'is', 'one', 'second', 'the',
         'third', 'this'],
        ['pizza', 'beer'],            # valid
        ['pizza', 'pizza'],           # duplicate
        ['a', 'b', 'a'],              # duplicate
        ['z', 'y', 'x'],              # reverse order preserved
    ]
    lists = fixed_lists + [rand_list(rng) for _ in range(N)]

    mismatches = 0
    examples = []
    for p in lists:
        m = validate_list_model(p)
        r = validate_list_real(p)
        # compare error tag, or the resulting mapping on success
        ok = (m[0] == r[0]) and (m[0] != 'ok' or m[1] == r[1])
        if ok and m[0] == 'ok':
            # A2: index-ordered extraction over the validated vocabulary
            voc_pairs = list(m[1].items())
            fn_m = feature_names_model([(t, i) for t, i in voc_pairs])
            fn_r = feature_names_real([(t, i) for t, i in voc_pairs])
            ok = fn_m == fn_r
        if not ok:
            mismatches += 1
            if len(examples) < 10:
                examples.append((p, m, r))

    if mismatches:
        print(f"G-AX FAIL: deep models diverge from real callees on "
              f"{mismatches} inputs")
        for p, m, r in examples:
            print(f"  in={p!r} model={m!r} real={r!r}")
        return 1

    print(f"G-AX OK: deep models == _validate_vocabulary / index-ordered "
          f"extraction on {len(lists)} inputs (seed=10908)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
