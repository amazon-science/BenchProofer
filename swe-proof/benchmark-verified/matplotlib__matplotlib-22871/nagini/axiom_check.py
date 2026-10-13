#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-22871.

The model has NO consumed @ContractOnly axioms. The two column reductions the
behaviour composes are modelled DEEPLY by structural predicates in model.py's
pure region:

  (A-reference)  col_varies(col)  ==  len(np.unique(col)) > 1
  (A-reference)  col_has_one(col) ==  np.any(np.unique(col) == 1)

`np.unique` / `np.any` are unchanged numpy reductions the changed code calls;
the gold patch is

    -            if len(np.unique(tickdate[:, level])) > 1:
    -                if level < 2:
    +            unique = np.unique(tickdate[:, level])
    +            if len(unique) > 1:
    +                if level < 2 and np.any(unique == 1):

so the predicates `col_varies` / `col_has_one` are exactly the two real numpy
reductions the patch keeps and adds. This check runs those REAL numpy reductions
on boundary + randomized fuzz integer columns and asserts that every observation
matches the structural model in model.py.

Additionally, the WHOLE labelling-level computation (`determine_level`, the
straight-line transcription of the `for level in range(5, -1, -1)` scan) is
checked end-to-end against a faithful re-implementation of the real loop body
from `lib/matplotlib/dates.py` (post-patch), on random 6-column tick tables, so
that the deep model's scan + offset logic == the real algorithm.

Imports only numpy (the library the changed code uses). Exit 0 iff sound.
"""
import random
import sys

import numpy as np


# --- model.py reference encodings (kept in lock-step with the pure region) ----

def model_col_varies(col):
    """Reference of model.py `col_varies`: two ticks disagree on this column."""
    return any(col[i] != col[j]
               for i in range(len(col)) for j in range(i + 1, len(col)))


def model_col_has_one(col):
    """Reference of model.py `col_has_one`: the value 1 occurs in the column."""
    return any(v == 1 for v in col)


def model_determine_level(cols):
    """Reference of model.py `determine_level`: the straight-line cascade over
    levels 5..0, returning (level, show_offset)."""
    for level in (5, 4, 3, 2):
        if model_col_varies(cols[level]):
            return level, 1
    if model_col_varies(cols[1]):
        return (1, 0) if model_col_has_one(cols[1]) else (1, 1)
    if model_col_varies(cols[0]):
        return (0, 0) if model_col_has_one(cols[0]) else (0, 1)
    return 5, 1


# --- the REAL numpy reductions, exactly as in lib/matplotlib/dates.py ---------

def real_col_varies(col):
    """The real `len(np.unique(tickdate[:, level])) > 1`."""
    return len(np.unique(np.asarray(col))) > 1


def real_col_has_one(col):
    """The real `np.any(unique == 1)` (unique = np.unique(col))."""
    unique = np.unique(np.asarray(col))
    return bool(np.any(unique == 1))


def real_determine_level(cols):
    """Faithful transcription of the post-patch real loop body in
    `ConciseDateFormatter.format_ticks` (lib/matplotlib/dates.py):

        show_offset = True   # self.show_offset default
        for level in range(5, -1, -1):
            unique = np.unique(tickdate[:, level])
            if len(unique) > 1:
                if level < 2 and np.any(unique == 1):
                    show_offset = False
                break
            elif level == 0:
                level = 5
        return level, show_offset
    """
    tickdate = np.array(cols).T  # shape (N, 6); cols[c] is column c
    show_offset = True
    level = 5
    for level in range(5, -1, -1):
        unique = np.unique(tickdate[:, level])
        if len(unique) > 1:
            if level < 2 and np.any(unique == 1):
                show_offset = False
            break
        elif level == 0:
            level = 5
    return level, 1 if show_offset else 0


# --- the checks ---------------------------------------------------------------

def check_reductions(col):
    obs_varies = real_col_varies(col)
    exp_varies = model_col_varies(col)
    assert obs_varies == exp_varies, (
        "col_varies deep model unsound on %r: numpy gave %r, model %r"
        % (col, obs_varies, exp_varies))
    obs_one = real_col_has_one(col)
    exp_one = model_col_has_one(col)
    assert obs_one == exp_one, (
        "col_has_one deep model unsound on %r: numpy gave %r, model %r"
        % (col, obs_one, exp_one))


def check_full(cols):
    obs = real_determine_level(cols)
    exp = model_determine_level(cols)
    assert obs == exp, (
        "determine_level deep model unsound on %r: real loop gave %r, "
        "model gives %r" % (cols, obs, exp))


def main():
    # --- column reductions: boundary cases ---------------------------------
    boundary_cols = [
        [1], [2], [0],
        [1, 1], [1, 2], [2, 2], [2, 3],
        [1, 1, 1], [1, 2, 3], [2, 3, 4],
        [12, 1], [2, 7], [1, 12], [0, 1],
        [1997, 1997], [1997, 1998],
        [-1, 1], [1, -1, 1], [0, 0, 0],
    ]
    for col in boundary_cols:
        check_reductions(col)

    # --- column reductions: randomized fuzz --------------------------------
    rng = random.Random(22871)
    for _ in range(20000):
        n = rng.randint(1, 8)
        # small calendar-component-like integers, biased to include 1 / not
        col = [rng.randint(0, 13) for _ in range(n)]
        check_reductions(col)

    # --- full determine_level: boundary 6-column tick tables ---------------
    # Each entry is a 6-list of equal-length columns (year..second).
    boundary_tables = [
        # all identical down to second -> level 5, offset shown
        [[1997], [2], [14], [0], [0], [0]],
        # months vary, January present -> level 1, offset suppressed
        [[1997, 1997, 1997], [1, 2, 3], [1, 1, 1], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
        # months vary, January ABSENT -> level 1, offset shown (the bug fix)
        [[1997, 1997, 1997], [2, 4, 7], [19, 1, 30], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
        # years vary, value 1 present in years column (degenerate) -> level 0
        [[1, 2], [3, 3], [4, 4], [0, 0], [0, 0], [0, 0]],
        # years vary, value 1 absent -> level 0, offset shown
        [[1997, 1998], [3, 3], [4, 4], [0, 0], [0, 0], [0, 0]],
        # days vary (fine level >= 2) -> offset always shown
        [[1997, 1997], [1, 1], [1, 2], [0, 0], [0, 0], [0, 0]],
        # seconds vary -> level 5, offset shown
        [[1997, 1997], [1, 1], [1, 1], [0, 0], [0, 0], [10, 20]],
    ]
    for cols in boundary_tables:
        check_full(cols)

    # --- full determine_level: randomized fuzz -----------------------------
    for _ in range(20000):
        n = rng.randint(1, 6)
        # random calendar tables: years near 1997, months 1..12, etc.
        cols = [
            [rng.choice([1996, 1997, 1998]) for _ in range(n)],   # year
            [rng.randint(1, 12) for _ in range(n)],               # month
            [rng.randint(1, 28) for _ in range(n)],               # day
            [rng.randint(0, 23) for _ in range(n)],               # hour
            [rng.randint(0, 59) for _ in range(n)],               # minute
            [rng.randint(0, 59) for _ in range(n)],               # second
        ]
        check_full(cols)

    print("G-AX OK: col_varies / col_has_one deep models == real numpy "
          "reductions on %d boundary + 20000 fuzz columns; determine_level "
          "deep model == real format_ticks scan on %d boundary + 20000 fuzz "
          "tick tables" % (len(boundary_cols), len(boundary_tables)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
