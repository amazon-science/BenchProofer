#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-12276.

Refutes the R/I refinement leg of `useRequiredAttribute`'s impl:
the modeled formula `inheritedRequiredDecision(hasInitial) && !hasInitial`.

REFINEMENT STRUCTURE:
  - The inherited base decision (`super().use_required_attribute(initial)`) is an
    UNCHANGED inherited callee, modeled as an OPAQUE free function. It is
    A-consumed (structural): the spec/impl reference it but assert nothing about
    its value. So it is a FREE INPUT here — we fuzz it over {True, False}.
  - The discriminating behavior introduced by the fix is the `and not initial`
    conjunct (Lean `&& !hasInitial`). This is the I (identical concrete op) /
    deeply-modeled leg and IS testable: it is a pure boolean conjunction over the
    free inherited decision and the `hasInitial` flag.

ORACLE: the patched method body transliterated verbatim from
  django/forms/widgets.py (FileInput.use_required_attribute, gold-patched):
      return super().use_required_attribute(initial) and not initial
  with `super().use_required_attribute(initial)` represented by the free input
  `base` (the inherited decision) and `not initial` by `not has_initial`.

SHADOW: Solution.lean's `useRequiredAttribute` post-image transliterated:
      base and (not has_initial)

We differential-test SHADOW vs ORACLE over all 2^2 = 4 (base, has_initial)
combinations plus seeded fuzz. Exit 0 iff zero disagreements. stdlib only.

  Note on `has_initial`: in the real widget `initial` is an arbitrary value and
  the conjunct is `not initial`, i.e. Python truthiness of the initial value.
  The model abstracts that to the boolean `hasInitial` = "an existing value is
  present (truthy)" per mapping.md §2. `not initial` ↔ `!hasInitial`.
"""
import itertools
import random
import sys

SEED = 12276
N_FUZZ = 100_000


def shadow(base, has_initial):
    """useRequiredAttribute transliterated: `base && !hasInitial`."""
    return base and (not has_initial)


def oracle(base, has_initial):
    """The patched method body, transliterated verbatim:
        super().use_required_attribute(initial) and not initial
    `base` stands for the (free) inherited decision; `has_initial` stands for
    the truthiness of `initial` (so `not initial` ↔ `not has_initial`)."""
    return base and not has_initial


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: all 2^2 = 4 (base, has_initial) boolean combinations.
    combos = list(itertools.product([False, True], repeat=2))
    # Plus seeded fuzz over the same boolean cube.
    combos += [tuple(rng.random() < 0.5 for _ in range(2)) for _ in range(N_FUZZ)]

    for base, has_initial in combos:
        count += 1
        s = bool(shadow(base, has_initial))
        o = bool(oracle(base, has_initial))
        if s != o:
            disagreements.append((base, has_initial, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of useRequiredAttribute agrees with the "
          "patched method body on %d inputs (4 exhaustive + fuzz, seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
