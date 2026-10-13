#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_getFeatureNames
against the patch.diff behaviour (the POST-patch `get_feature_names`).

The impl region has R/I content (the `let mut voc` selection between an
already-available vocabulary and a constructor-supplied one, the empty check, and
the final extraction), so this runs a real fuzz. The shadow reproduces the Lean
impl's control flow op-for-op. The two deeply-modeled callees (`validateList`,
`featureNames`) are A-references, so — per the G-CONF protocol — they are realised
here by the REAL repo callees (`_validate_vocabulary`, the index-ordered
extraction).

The patched side is an independent driver of the POST-patch `get_feature_names`
body over the same state space:
  * learned vocabulary available  -> set cv.vocabulary_ directly, then call;
  * no learned vocab, constructor vocabulary supplied -> CountVectorizer(vocabulary=p);
  * neither                      -> CountVectorizer() unfitted.
The observable outcome is the returned name list, or the error class
(NotFittedError -> 'notFitted'; ValueError "empty" -> 'empty';
ValueError "duplicate/repeated" -> 'dup').

We assert zero disagreements over >=10^5 fuzzed states.

Runs inside the instance image (sklearn importable via PYTHONPATH=/testbed).
exit 0 iff zero disagreements.
"""
import random
import sys
from operator import itemgetter

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.exceptions import NotFittedError


# ---- A-reference callees realised by the REAL repo ground truth ------------

def validate_list_real(p):
    """Real `_validate_vocabulary` on a list vocabulary -> ('empty',)/('dup',)
    or ('ok', {term: index})."""
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
    return ('ok', dict(cv.vocabulary_))


def feature_names_real(voc_dict):
    """Index-ordered name extraction, exactly as the post-patch body."""
    return [t for t, i in sorted(voc_dict.items(), key=itemgetter(1))]


# ---- R/I shadow of implementation_getFeatureNames -------------------------

def shadow(state):
    """state = (learned, param):
        learned : dict | None      (already-available vocabulary)
        param   : list[str] | None (constructor-supplied ordered terms)
    Returns ('ok', names) or ('err', tag)."""
    learned, param = state
    if learned is not None:                       # match st.learned with some v
        voc = dict(learned)
    else:                                         # | none =>
        if param is None:                         #   match st.param with none =>
            return ('err', 'notFitted')           #     return notFitted
        r = validate_list_real(param)             #   | some p => validateList p
        if r[0] != 'ok':                          #     | error e =>
            return ('err', r[0])                  #       return e
        voc = r[1]                                #     | ok v => voc := v
    if len(voc) == 0:                             # if voc.isEmpty
        return ('err', 'empty')                   #   return empty
    return ('ok', feature_names_real(voc))        # return ok (featureNames voc)


# ---- patched-side oracle: POST-patch get_feature_names --------------------

def patched(state):
    learned, param = state
    if learned is not None:
        cv = CountVectorizer()
        cv.vocabulary_ = dict(learned)
    elif param is not None:
        cv = CountVectorizer(vocabulary=list(param))
    else:
        cv = CountVectorizer()
    try:
        names = cv.get_feature_names()
    except NotFittedError:
        return ('err', 'notFitted')
    except ValueError as e:
        msg = str(e).lower()
        if 'duplicate' in msg:
            return ('err', 'dup')
        if 'empty' in msg:
            return ('err', 'empty')
        raise
    return ('ok', list(names))


# ---- Fuzzing ----------------------------------------------------------------

def rand_term(rng):
    return rng.choice(['beer', 'burger', 'celeri', 'coke', 'pizza', 'salad',
                       'sparkling', 'tomato', 'water', 'a', 'b', 'c', 'and',
                       'the', 'is', 'one', 'x', 'y', 'z'])


def rand_list(rng):
    return [rand_term(rng) for _ in range(rng.randint(0, 8))]


def rand_learned(rng):
    """A random already-available vocabulary dict {term: distinct index}."""
    terms = list(dict.fromkeys(rand_list(rng)))   # de-dup preserve order
    idxs = list(range(len(terms)))
    rng.shuffle(idxs)
    return {t: i for t, i in zip(terms, idxs)}


def rand_state(rng):
    k = rng.randint(0, 3)
    if k == 0:
        return (rand_learned(rng), None)
    if k == 1:
        return (None, rand_list(rng))
    if k == 2:
        return (None, None)
    # both present: learned takes precedence (matches Lean + Python)
    return (rand_learned(rng), rand_list(rng))


def main() -> int:
    rng = random.Random(10908)
    N = 120_000

    fixed = [
        (None, None),                                   # notFitted
        (None, []),                                     # empty (validation)
        (None, ['pizza', 'pizza']),                     # dup
        (None, ['beer', 'burger', 'celeri', 'coke', 'pizza', 'salad',
                'sparkling', 'tomato', 'water']),       # the F2P custom vocab
        (None, ['z', 'y', 'x']),                        # order preserved
        ({}, None),                                     # empty learned
        ({'a': 0, 'b': 1, 'c': 2}, None),               # learned, ordered
        ({'a': 2, 'b': 0, 'c': 1}, None),               # learned, reordered
    ]
    states = fixed + [rand_state(rng) for _ in range(N)]

    disagreements = 0
    examples = []
    for st in states:
        got = shadow(st)
        want = patched(st)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((st, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for st, g, w in examples:
            print(f"  state={st!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(states)} inputs, 0 disagreements (seed=10908)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
