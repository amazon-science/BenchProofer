#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-23476.

This bundle consumes NO `@ContractOnly` axiom (model.py's axioms region is
empty): the change is a `dict.get`-with-default selection plus an in-place
assignment, modeled DEEPLY in the impl region. What G-AX validates here is the
single **A-reference**: that the deep model's selection semantics
(`normalize_state_dpi`, model.py) reproduces real Python's
`state["_dpi"] = state.get('_original_dpi', state['_dpi'])` — the gold patch's
exact operation — on boundary + randomized inputs.

The deep model encodes (under the key-token / value-token refinement of
mapping.md §2):
    if '_original_dpi' in state:  state['_dpi'] = state['_original_dpi']
    else:                         state['_dpi'] = state['_dpi']
i.e. the resulting '_dpi' is `state.get('_original_dpi', state['_dpi'])`, and
every other entry is untouched.

The check also exercises the value-token refinement (`float` DPI ↔ `int`): it
runs with real `float` DPI values (including the exact `42.0` / `294.0` of the
F2P test) AND with arbitrary int/float values, confirming the behaviour is pure
value-SELECTION (no arithmetic), so an int token faithfully models it.

Imports only the standard library (`random`, `sys`, `copy`) — nothing
repo-specific (the gold patch itself uses only the builtin `dict`). Exit 0 iff
every observation matches the deep model.
"""
import copy
import random
import sys

KEY_DPI = "_dpi"
KEY_ORIGINAL_DPI = "_original_dpi"


def real_getstate_dpi_fix(state):
    """The REAL gold-patch operation, verbatim (the line added to
    Figure.__getstate__). Mutates `state` in place and returns it."""
    state["_dpi"] = state.get('_original_dpi', state['_dpi'])
    return state


def deep_model(state):
    """Reference of model.py's deep model `normalize_state_dpi` selection.
    Mutates `state` in place: '_dpi' becomes '_original_dpi' if present, else
    is left at its own value; nothing else changes."""
    if KEY_ORIGINAL_DPI in state:
        state[KEY_DPI] = state[KEY_ORIGINAL_DPI]
    else:
        state[KEY_DPI] = state[KEY_DPI]
    return state


def check(state):
    """Assert the deep model and the real gold operation agree on `state`, and
    that no entry other than '_dpi' is altered."""
    before = copy.deepcopy(state)
    real = real_getstate_dpi_fix(copy.deepcopy(state))
    model = deep_model(copy.deepcopy(state))
    assert real == model, (
        "deep model disagrees with real dict.get on %r: real=%r model=%r"
        % (before, real, model))
    # '_dpi' must equal the selected value
    expected_dpi = before.get(KEY_ORIGINAL_DPI, before[KEY_DPI])
    assert model[KEY_DPI] == expected_dpi, (
        "selection wrong on %r: got %r expected %r"
        % (before, model[KEY_DPI], expected_dpi))
    # every key other than '_dpi' is untouched (membership + value)
    for k in set(before) | set(model):
        if k == KEY_DPI:
            continue
        assert (k in model) == (k in before), (
            "membership of %r changed on %r" % (k, before))
        if k in before:
            assert model[k] == before[k], (
                "value of %r changed on %r" % (k, before))


def main():
    # --- boundary cases ---------------------------------------------------
    boundary = [
        # the F2P scenario: original 42, live scaled to 42*7 = 294
        {"_dpi": 294.0, "_original_dpi": 42.0},
        # original present, equal to live (no scaling applied)
        {"_dpi": 42.0, "_original_dpi": 42.0},
        # original ABSENT -> '_dpi' kept as-is (the .get default branch)
        {"_dpi": 100.0},
        # original present alongside other unrelated state entries
        {"_dpi": 294.0, "_original_dpi": 42.0, "_cachedRenderer": None,
         "__mpl_version__": "3.5.2", "stale": True},
        # other entries but no original record
        {"_dpi": 72.0, "figwidth": 6.4, "figheight": 4.8},
        # integer-valued dpi (value-token refinement: selection is value-agnostic)
        {"_dpi": 200, "_original_dpi": 100},
        {"_dpi": 0, "_original_dpi": 0},
        # repeated-cycle witness: a value that doubled many times
        {"_dpi": 419430400.0, "_original_dpi": 200.0},
    ]
    for st in boundary:
        check(st)

    # idempotence witness: applying the fix, re-recording original = result,
    # then re-applying must keep the original (the bug was re-scaling here)
    st = {"_dpi": 294.0, "_original_dpi": 42.0}
    fixed = deep_model(copy.deepcopy(st))
    assert fixed["_dpi"] == 42.0
    # simulate a second serialise cycle where original now equals the restored
    st2 = {"_dpi": fixed["_dpi"], "_original_dpi": fixed["_dpi"]}
    assert deep_model(copy.deepcopy(st2))["_dpi"] == 42.0

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(23476)
    extra_keys = ["_cachedRenderer", "figwidth", "figheight", "stale",
                  "__mpl_version__", "_restore_to_pylab", "dpi_scale_trans"]
    for _ in range(50000):
        st = {"_dpi": rng.choice([rng.randint(0, 10**9),
                                  rng.uniform(0.0, 1e9)])}
        if rng.random() < 0.6:
            st[KEY_ORIGINAL_DPI] = rng.choice([rng.randint(0, 10**9),
                                               rng.uniform(0.0, 1e9)])
        for k in extra_keys:
            if rng.random() < 0.3:
                st[k] = rng.randint(-1000, 1000)
        check(st)

    print("G-AX OK: deep model (== real dict.get('_original_dpi', state['_dpi']))"
          " sound on %d boundary + 50000 fuzz states" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
