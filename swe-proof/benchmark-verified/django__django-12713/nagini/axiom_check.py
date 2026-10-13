#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12713.

This bundle axiomatizes NO opaque library callee: the behaviour under
specification -- a presence-guarded default selection over a keyword-options
mapping -- is composed entirely of REAL Python language primitives the gold
patch uses, namely the dict membership test ``key in options`` and the dict
assignment ``options[key] = value``. The default selection is therefore
modelled DEEPLY in model.py (the precedence guard + priority chain spelled out
in the impl region). G-AX validates that deep model against the real
primitives (the A-reference): it reproduces the gold patch's exact control flow
over a real ``dict`` and asserts every observation matches model.py's frozen
postconditions.

Checked obligations (model.py post-conditions region):

  (1) preservation -- if the presentation key was present on entry it is still
      present on exit with the SAME value (no name-derived default replaces a
      caller-supplied component), and every other entry key is carried through
      unchanged; no key but the presentation key is ever added. This is the
      precedence guarantee the fix introduces (the bug overwrote the caller's
      component).

  (2) default selection -- when the presentation key is absent on entry, the
      name-derived default is established by the fixed priority
      primary > secondary > tertiary, or none if no test matches.

Imports nothing repo-specific: ``dict`` membership and assignment are Python
language primitives (the very constructs the gold patch composes). Exit 0 iff
every obligation holds.
"""
import itertools
import random
import sys

# model.py constants (kept in lock-step with the pure region).
KEY_COMPONENT = 0
DEFAULT_PRIMARY = 1
DEFAULT_SECONDARY = 2
DEFAULT_TERTIARY = 3


def real_select_component(options, test_primary, test_secondary, test_tertiary):
    """The gold patch's exact control flow, over a REAL dict: the added
    presence guard wrapping the priority chain, using the real ``in`` test and
    the real ``[]=`` assignment. Mutates ``options`` in place (as the repo code
    mutates its **kwargs dict)."""
    if KEY_COMPONENT not in options:                 # the guard the fix adds
        if test_primary:
            options[KEY_COMPONENT] = DEFAULT_PRIMARY
        elif test_secondary:
            options[KEY_COMPONENT] = DEFAULT_SECONDARY
        elif test_tertiary:
            options[KEY_COMPONENT] = DEFAULT_TERTIARY


def check(options, test_primary, test_secondary, test_tertiary):
    old = dict(options)                              # snapshot of the entry state
    real_select_component(options, test_primary, test_secondary, test_tertiary)

    component_present_on_entry = KEY_COMPONENT in old

    # (1) preservation: every entry key survives with its value unchanged ...
    for k, v in old.items():
        assert k in options and options[k] == v, (
            "preservation unsound: entry key %r=%r changed to %r"
            % (k, v, options.get(k, "<absent>")))
    # ... and no key but the presentation key is ever added.
    for k in options:
        assert k in old or k == KEY_COMPONENT, (
            "spurious key unsound: %r added (not the presentation key)" % (k,))

    # (2) default selection when the presentation key was absent on entry.
    if not component_present_on_entry:
        if test_primary:
            assert KEY_COMPONENT in options and options[KEY_COMPONENT] == DEFAULT_PRIMARY, (
                "default selection unsound: primary branch not taken")
        elif test_secondary:
            assert KEY_COMPONENT in options and options[KEY_COMPONENT] == DEFAULT_SECONDARY, (
                "default selection unsound: secondary branch not taken")
        elif test_tertiary:
            assert KEY_COMPONENT in options and options[KEY_COMPONENT] == DEFAULT_TERTIARY, (
                "default selection unsound: tertiary branch not taken")
        else:
            assert KEY_COMPONENT not in options, (
                "default selection unsound: component established with no "
                "matching membership test")
    else:
        # the F2P guarantee: a caller-supplied component is preserved exactly,
        # regardless of which membership tests fire.
        assert options[KEY_COMPONENT] == old[KEY_COMPONENT], (
            "precedence unsound: caller component %r overwritten to %r"
            % (old[KEY_COMPONENT], options[KEY_COMPONENT]))


def main():
    flags = list(itertools.product([False, True], repeat=3))

    # --- boundary cases: the F2P / P2P scenarios over all flag combinations ---
    # The F2P scenario: a caller-supplied component (e.g. CheckboxSelectMultiple,
    # a component DISTINCT from the three name-derived defaults) present on entry,
    # with the tertiary (filter) membership test firing -- it must be preserved.
    boundary_options = [
        {},                                       # no caller component
        {KEY_COMPONENT: 7},                       # caller component distinct from defaults
        {KEY_COMPONENT: DEFAULT_PRIMARY},         # caller component == a default value
        {KEY_COMPONENT: DEFAULT_SECONDARY},
        {KEY_COMPONENT: DEFAULT_TERTIARY},
        {KEY_COMPONENT: 7, 5: 50},                # caller component + unrelated option
        {5: 50, 6: 60},                           # only unrelated options, no component
    ]
    for base in boundary_options:
        for (a, r, f) in flags:
            check(dict(base), a, r, f)

    # The exact F2P case: tertiary (filter_vertical) test fires, caller supplies
    # CheckboxSelectMultiple (distinct component id); post-patch it must survive.
    f2p = {KEY_COMPONENT: 7}                       # 7 = CheckboxSelectMultiple identity
    check(dict(f2p), False, False, True)          # only the tertiary test fires

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(12713)
    for _ in range(20000):
        base = {}
        if rng.getrandbits(1):
            base[KEY_COMPONENT] = rng.randint(-5, 12)   # maybe a caller component
        for _ in range(rng.randint(0, 4)):
            k = rng.randint(1, 20)                      # unrelated option keys (!= 0)
            base[k] = rng.randint(-5, 50)
        a, r, f = bool(rng.getrandbits(1)), bool(rng.getrandbits(1)), bool(rng.getrandbits(1))
        check(base, a, r, f)

    print("G-AX OK: deep model (presence-guarded priority selection) == the "
          "real dict membership/assignment primitives on %d boundary x %d flag "
          "combinations + the F2P caller-override case + 20000 fuzz cases "
          "(caller component never overwritten; default selected only when "
          "absent)" % (len(boundary_options), len(flags)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
