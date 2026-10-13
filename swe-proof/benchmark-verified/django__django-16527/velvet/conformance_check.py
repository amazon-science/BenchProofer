#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16527.

Refutes the R/I refinement leg (A2-A5: the modeled boolean conjunction
`!isPopup && hasAddPermission && change && saveAs` over `Bool` inputs).

ORACLE CHOICE — why we transliterate the source line instead of running
`submit_row`:
  The patched flag is computed inside `submit_row(context)`, which requires a
  fully-populated admin template context (a rendered admin change view with a
  real `User`, permissions, a `ModelAdmin`, and the request/response cycle).
  Building that context in-container purely to read back one boolean is
  impractical and would not isolate the modeled behavior. So, per the worker
  prompt, the ORACLE is the patched source line transliterated VERBATIM:
      show_save_as_new = not is_popup and has_add_permission and change and save_as
  (from the gold-patched django/contrib/admin/templatetags/admin_modify.py,
  the `"show_save_as_new"` dict entry). The SHADOW is the modeled formula from
  Solution.lean's `showSaveAsNew` post-image. We differential-test SHADOW vs
  ORACLE over all 2^5 = 32 input combinations plus seeded fuzz. Exit 0 iff zero
  disagreements. stdlib only.

  Note: `has_change_permission` is an input to the model (so the prepatch is
  expressible) but does NOT influence the patched flag — the oracle ignores it,
  and the shadow must too. We fuzz it independently to confirm irrelevance.
"""
import itertools
import random
import sys

SEED = 16527
N_FUZZ = 100_000


def shadow(is_popup, has_add, has_change, change, save_as):
    """showSaveAsNew transliterated: the modeled boolean conjunction.
    Mirrors `!isPopup && hasAddPermission && change && saveAs` exactly.
    `has_change` is accepted but intentionally unused (mapping.md §1)."""
    return (not is_popup) and has_add and change and save_as


def oracle(is_popup, has_add, has_change, change, save_as):
    """The patched source line, transliterated verbatim from
    django/contrib/admin/templatetags/admin_modify.py (gold-patched):
        not is_popup and has_add_permission and change and save_as
    `has_change_permission` is genuinely absent from the patched expression."""
    return not is_popup and has_add and change and save_as


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: all 2^5 = 32 boolean input combinations.
    combos = list(itertools.product([False, True], repeat=5))
    # Plus seeded fuzz over the same boolean cube (redundant coverage, but the
    # prompt asks for fuzz; it also exercises has_change independence).
    combos += [tuple(rng.random() < 0.5 for _ in range(5)) for _ in range(N_FUZZ)]

    for is_popup, has_add, has_change, change, save_as in combos:
        count += 1
        s = bool(shadow(is_popup, has_add, has_change, change, save_as))
        o = bool(oracle(is_popup, has_add, has_change, change, save_as))
        if s != o:
            disagreements.append(
                (is_popup, has_add, has_change, change, save_as, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of showSaveAsNew agrees with the patched "
          "source line on %d inputs (32 exhaustive + fuzz, seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
