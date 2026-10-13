#!/usr/bin/env python3
"""G-AX soundness check for matplotlib__matplotlib-20826.

The model has ONE axiomatized callee, the mapping-copy primitive
``dict_carry_over`` (an A-reference: a deep model of an unchanged dict
operation, validated == the real primitive here, not relied on as opaque
behaviour). Its contract:

    Requires Acc(dict_pred(d), 1/2)
    Ensures  Result is a FRESH mapping with EXACTLY the key/value content of d:
        for every k:  k in d        => k in Result and Result[k] == d[k]
        for every k:  k in Result   => k in d      and Result[k] == d[k]

The real primitive is Python's mapping carry-over: building a new dict that
preserves every existing key/value and introduces none (``dict(d)`` /
``d.copy()`` / ``{**d}``). This is exactly the "carry over the existing tick
keyword settings" step the fixed re-initialisation performs (it updates only
the grid-visibility key in place, leaving every other key intact); the model
realises that preservation as a fresh equal mapping.

This script ALSO validates the END-TO-END re-initialisation behaviour the model
specifies (grid-visibility key set to ``grids_on and which_match`` while every
other key is preserved) against a faithful Python reference of the fixed
operation, on boundary + fuzz inputs, so the modelled postconditions are
checked against real dict semantics. stdlib-only; exit 0 iff sound.
"""
import random
import sys

KEY_GRID = 0  # model's refreshed_key(): the one designated (grid-visibility) setting-name token.


# --- the real unchanged callee the axiom stands for -------------------------
def real_carry_over(d):
    """Real mapping-copy primitive: a fresh dict with the same content."""
    return dict(d)


# --- faithful Python reference of the FIXED re-initialisation ---------------
def real_reinit(tick_kw, grids_on, which_match):
    """Mirror of the gold behaviour: update only the grid-visibility entry,
    preserving every other entry. (The real code mutates the same object in
    place: ``self._major_tick_kw['gridOn'] = grids_on and which_match``; we
    return the resulting mapping so it can be compared to the model.)"""
    result = dict(tick_kw)  # carry over existing keys/values
    result[KEY_GRID] = grids_on and which_match
    return result


def check_carry_over(d):
    r = real_carry_over(d)
    # Fresh object (not the same identity) -- matches "FRESH mapping".
    assert r is not d, "carry-over must be a fresh mapping"
    # k in d => k in r and r[k] == d[k]
    for k, v in d.items():
        assert k in r and r[k] == v, ("carry-over dropped/changed key", k, d)
    # k in r => k in d and r[k] == d[k]
    for k, v in r.items():
        assert k in d and d[k] == v, ("carry-over introduced key", k, d)


def check_reinit(tick_kw, grids_on, which_match):
    r = real_reinit(tick_kw, grids_on, which_match)
    expected_grid = bool(grids_on and which_match)
    # (1) grid key present and equal to the prescribed conjunction.
    assert KEY_GRID in r, ("grid key missing", tick_kw)
    assert r[KEY_GRID] == expected_grid, ("grid value wrong", r[KEY_GRID],
                                          expected_grid, tick_kw)
    # (2) every OTHER entry present on entry is preserved exactly.
    for k, v in tick_kw.items():
        if k != KEY_GRID:
            assert k in r and r[k] == v, ("preservation failed", k, tick_kw)
    # (3) the result introduces no entry other than the grid key.
    for k, v in r.items():
        if k != KEY_GRID:
            assert k in tick_kw and tick_kw[k] == v, ("spurious key", k, r,
                                                      tick_kw)
    # Cross-check: pre-patch behaviour (empty then set grid) would DROP the
    # non-grid entries -- confirming the spec's clause (2) discriminates.
    buggy = {KEY_GRID: expected_grid}
    if any(k != KEY_GRID for k in tick_kw):
        assert buggy != r, "buggy emptying must differ from the fixed result"


def main():
    rng = random.Random(20826)

    # Boundary inputs: empty, grid-only, the side-hiding visibility flags that
    # shared axes store, mixtures, and grid already set both ways.
    boundary = [
        {},
        {KEY_GRID: True},
        {KEY_GRID: False},
        {1: False},                       # a hidden tick/label flag alone
        {1: False, 2: False},             # tick1On=False, label1On=False
        {KEY_GRID: True, 1: False, 2: False},
        {KEY_GRID: False, 1: True, 2: False, 3: True},
        {1: True, 2: True, 3: True, 4: True},
    ]
    flag_combos = [(g, w) for g in (False, True) for w in (False, True)]

    for d in boundary:
        check_carry_over(d)
        for g, w in flag_combos:
            check_reinit(d, g, w)

    # Fuzz: random mappings over a small key space with boolean values.
    for _ in range(20000):
        n = rng.randint(0, 8)
        keys = rng.sample(range(0, 12), n)
        d = {k: bool(rng.getrandbits(1)) for k in keys}
        check_carry_over(d)
        g = bool(rng.getrandbits(1))
        w = bool(rng.getrandbits(1))
        check_reinit(d, g, w)

    print("axiom_check OK: dict_carry_over == real mapping copy; "
          "fixed re-init preserves all non-grid keys (boundary + 20000 fuzz)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
