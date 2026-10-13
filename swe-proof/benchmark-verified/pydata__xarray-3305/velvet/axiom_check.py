#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-3305.

Executes the REAL repo callee `xarray.core.options._get_keep_attrs` under every
ambient `keep_attrs` option setting and both fallbacks, and asserts that every
observation matches the deep model `resolveGlobal` from Solution.lean's `pure`
region.

The single kind-A check:

  (A-reference) the deep model `resolveGlobal(g, fallback)` (Solution.lean pure
      region) == the real `_get_keep_attrs(default=fallback)` under
      `set_options(keep_attrs=g)`:
        gDefault ("default") -> fallback
        gKeep    (True)      -> True
        gDrop    (False)     -> False
      (the ValueError branch is unreachable — the option setter restricts the
      global to True/False/"default").

There is NO consumed axiom in this bundle; `resolveGlobal` models an UNCHANGED
callee. Runs in-container against the real xarray. Exit 0 iff every obligation
holds.
"""
import random
import sys

# --- Solution.lean `resolveGlobal` reference encoding (lock-step with model) -
# GlobalPref: "default" <-> gDefault, True <-> gKeep, False <-> gDrop.
def resolve_global(global_choice, fallback):
    if global_choice == "default":
        return fallback
    elif global_choice is True:
        return True
    elif global_choice is False:
        return False
    raise AssertionError("unexpected global option %r" % (global_choice,))


def main():
    from xarray import set_options
    from xarray.core.options import _get_keep_attrs

    global_choices = ["default", True, False]
    fallbacks = [True, False]

    checks = 0
    # boundary: every (global option, fallback) combination
    for g in global_choices:
        for fb in fallbacks:
            with set_options(keep_attrs=g):
                observed = _get_keep_attrs(default=fb)   # real callee
            expected = resolve_global(g, fb)             # deep model
            assert bool(observed) == bool(expected), (
                "resolveGlobal deep model unsound: _get_keep_attrs(default=%r) "
                "under keep_attrs=%r gave %r, model gives %r"
                % (fb, g, observed, expected))
            checks += 1

    # randomized fuzz over the same finite domain (defends against accidental
    # statefulness / option leakage across calls)
    rng = random.Random(3305)
    for _ in range(20000):
        g = rng.choice(global_choices)
        fb = rng.choice(fallbacks)
        with set_options(keep_attrs=g):
            observed = _get_keep_attrs(default=fb)
        expected = resolve_global(g, fb)
        assert bool(observed) == bool(expected), (
            "resolveGlobal deep model unsound (fuzz): keep_attrs=%r default=%r "
            "gave %r, model gives %r" % (g, fb, observed, expected))
        checks += 1

    # the operation's own fallback is drop (default=False), as the variable.py
    # hunk uses: confirm that under the ambient "default" the element reduction
    # would drop unless the caller opts in.
    with set_options(keep_attrs="default"):
        assert _get_keep_attrs(default=False) is False
    with set_options(keep_attrs=True):
        assert _get_keep_attrs(default=False) is True
    with set_options(keep_attrs=False):
        assert _get_keep_attrs(default=False) is False

    print("G-AX OK: resolveGlobal deep model (== xarray _get_keep_attrs) sound "
          "on %d (option x fallback) observations" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
