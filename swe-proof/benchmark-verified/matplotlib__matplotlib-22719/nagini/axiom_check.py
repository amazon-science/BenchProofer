#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-22719.

This bundle consumes NO `@ContractOnly` axiom: the only changed operation (the
non-emptiness guard `X.size and ...`) is modelled deeply, and the unchanged
universal "all elements classify" verdict is spelled out by the front-recursive
fold `all_classify` (model.py pure region). G-AX therefore validates the
*behavioural* facts the deep model rests on against the REAL runtime semantics
that the patched code uses:

  (1) the vacuous-truth fact `all([]) == True` (the convert site's
      `all(<predicate> for v in values)`) and the equivalent unentered-loop fact
      that the `convertible` accumulator stays `True` for empty data (the update
      site). This is precisely why the PRE-patch decision (`is_numlike` /
      `convertible` alone) emitted the advisory on empty input;

  (2) the model's `all_classify` fold == the real `all`/`convertible` universal
      verdict on boundary + fuzz flag sequences;

  (3) the size ↔ length bijection: for the patched arrays
      `np.atleast_1d(np.array(value, dtype=object))`, `array.size == 0` iff the
      input is empty, so `array.size` (the changed conjunct) ↔ `len(flags) > 0`;

  (4) the full patched decision `array.size and all_classify` == the model's
      `Ensures` (`len(flags) > 0 and all_classify(flags)`) on every input,
      and == `False` on the empty input.

Imports only the standard library plus `numpy` — the very array layer the gold
patch calls (`np.atleast_1d(np.array(..., dtype=object))`); nothing
repo-specific. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def all_classify(flags):
    """Reference of model.py's deep model `all_classify`: every element's flag
    is non-zero (vacuously True on the empty sequence)."""
    for f in flags:
        if f == 0:
            return False
    return True


def model_decision(flags):
    """model.py's Ensures: len(flags) > 0 and all_classify(flags)."""
    return len(flags) > 0 and all_classify(flags)


# --- the real runtime decisions, as in lib/matplotlib/category.py ------------

def real_convert_decision(predicate_results):
    """Reconstruct the patched convert decision `values.size and is_numlike`
    over a list of per-element predicate booleans, using the SAME array layer
    the patch uses."""
    # values = np.atleast_1d(np.array(value, dtype=object))  (one cell per elem)
    values = np.atleast_1d(np.array(list(range(len(predicate_results))),
                                    dtype=object))
    is_numlike = all(bool(p) for p in predicate_results)   # the real `all(...)`
    return bool(values.size and is_numlike)                # patched guard


def real_update_decision(predicate_results):
    """Reconstruct the patched update decision `data.size and convertible`
    over a list of per-element predicate booleans, faithfully reproducing the
    `convertible` left-fold (seeded True, short-circuited)."""
    data = np.atleast_1d(np.array(list(range(len(predicate_results))),
                                  dtype=object))
    convertible = True
    for p in predicate_results:                            # the real left-fold
        if convertible:
            convertible = bool(p)
    return bool(data.size and convertible)                 # patched guard


def check_case(predicate_results):
    flags = [1 if p else 0 for p in predicate_results]

    # (1)+(2) vacuous truth + universal-verdict equivalence
    py_all = all(bool(p) for p in predicate_results)
    assert all_classify(flags) == py_all, (
        "all_classify deep model disagrees with real all(...) on %r: model=%r "
        "python=%r" % (predicate_results, all_classify(flags), py_all))
    if len(predicate_results) == 0:
        assert all_classify(flags) is True and py_all is True, (
            "vacuous-truth fact broken: all([]) must be True")

    # (3) size <-> length bijection on the patched array layer
    arr = np.atleast_1d(np.array(list(range(len(predicate_results))),
                                 dtype=object))
    assert (arr.size > 0) == (len(flags) > 0), (
        "size<->len bijection broken on %r: arr.size=%r len=%r"
        % (predicate_results, arr.size, len(flags)))

    # (4) full patched decision == model Ensures, both sites
    want = model_decision(flags)
    got_convert = real_convert_decision(predicate_results)
    got_update = real_update_decision(predicate_results)
    assert got_convert == want, (
        "convert decision != model on %r: real=%r model=%r"
        % (predicate_results, got_convert, want))
    assert got_update == want, (
        "update decision != model on %r: real=%r model=%r"
        % (predicate_results, got_update, want))
    if len(predicate_results) == 0:
        assert got_convert is False and got_update is False, (
            "empty input must NOT emit the advisory (the bug being fixed)")


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        [],                 # the empty case — the F2P scenario, advisory off
        [True],             # one classifying element -> advisory on
        [False],            # one non-classifying element -> advisory off
        [True, True],
        [True, False],
        [False, True],
        [False, False],
        [True, True, True, True],
        [True, False, True],
    ]
    for case in boundary:
        check_case(case)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(22719)
    for _ in range(20000):
        n = rng.randint(0, 16)
        case = [rng.random() < 0.7 for _ in range(n)]
        check_case(case)

    # explicit empty-input regression witness for BOTH sites
    assert real_convert_decision([]) is False, "convert: empty must be advisory-off"
    assert real_update_decision([]) is False, "update: empty must be advisory-off"
    # and the PRE-patch decision (no size guard) WOULD have fired on empty:
    assert all(bool(p) for p in []) is True, "pre-patch convert fired on empty"
    pre_convertible = True
    for _ in []:
        pass
    assert pre_convertible is True, "pre-patch update fired on empty"

    print("G-AX OK: all_classify deep model == real all/convertible verdict; "
          "size<->len bijection holds; patched decision == model Ensures and "
          "is advisory-off on empty input, over %d boundary + 20000 fuzz cases"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
