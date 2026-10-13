#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-12406 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. This
bundle has NO axiomatized callees, so the entire impl region of both modeled
methods is R/I and is covered here; there is nothing for G-AX (no axiom_check.py)
and no A-tagged callee left as a real-repo call.

Two coupled sites, each a pure boolean decision:

  * SITE B — `relationBlankFlag`: the blank flag a model relation forwards
    to its choice field.
  * SITE A — `blankChoiceOffered`: whether the synthetic leading blank choice is
    offered (observable as `empty_label is not None`).

ORACLE CHOICE — why we transliterate the patched source expressions instead of
constructing live Django objects:
  The patched booleans live inside `ForeignKey.formfield` (needs a loaded model,
  a related model, a default manager, a DB connection) and inside
  `ModelChoiceField.__init__` (needs a queryset, a widget instance, and the
  `ModelChoiceIterator` to read back `empty_label is not None`). Building that
  machinery in-container purely to read back two booleans is impractical and
  would not isolate the modeled behavior. So, per the worker prompt, the ORACLE
  for each site is the patched source expression transliterated VERBATIM from
  the gold patch:

    site B (django/db/models/fields/related.py, formfield kwargs):
        blank = self.blank                      # forwarded value == self.blank
    site A (django/forms/models.py, ModelChoiceField.__init__):
        empty_label_is_None = (
            (required and initial is not None) or
            (isinstance(self.widget, RadioSelect) and not blank)
        )
        # blank option offered  <=>  empty_label is not None  <=>  not the above

  The SHADOW for each site is the modeled formula from Solution.lean's
  post-image. We differential-test SHADOW vs ORACLE exhaustively over the
  boolean cube (2 inputs for site B, 4 for site A) plus seeded fuzz. Exit 0 iff
  zero disagreements. stdlib only.
"""
import itertools
import random
import sys

SEED = 12406
N_FUZZ = 100_000


# --- SITE B: relationBlankFlag ------------------------------------------

def shadow_relation_blank(model_allows_blank):
    """relationBlankFlag transliterated: `return modelAllowsBlank`."""
    return model_allows_blank


def oracle_relation_blank(model_allows_blank):
    """Patched source: `'blank': self.blank` — the forwarded value IS self.blank.
    `model_allows_blank` bridges `self.blank` (mapping.md §2)."""
    self_blank = model_allows_blank
    return self_blank


# --- SITE A: blankChoiceOffered ----------------------------------------------

def shadow_blank_choice(required, initial_present, widget_is_radio, blank):
    """blankChoiceOffered transliterated:
    `!((required && initialPresent) || (widgetIsRadio && !blank))`."""
    return not ((required and initial_present) or (widget_is_radio and not blank))


def oracle_blank_choice(required, initial_present, widget_is_radio, blank):
    """Patched source (ModelChoiceField.__init__), transliterated verbatim:
        if ((required and initial is not None) or
            (isinstance(self.widget, RadioSelect) and not blank)):
            self.empty_label = None
        else:
            self.empty_label = empty_label
    observed via ModelChoiceIterator as `empty_label is not None`.
    Here `initial_present` bridges `initial is not None`; `widget_is_radio`
    bridges `isinstance(self.widget, RadioSelect)` (mapping.md §2)."""
    empty_label_is_none = (
        (required and initial_present) or
        (widget_is_radio and not blank)
    )
    empty_label_is_not_none = not empty_label_is_none
    return empty_label_is_not_none  # == blank option offered


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- SITE B: exhaustive over the 2 boolean inputs + fuzz -----------------
    site_b = list(itertools.product([False, True], repeat=1))
    site_b += [(rng.random() < 0.5,) for _ in range(N_FUZZ)]
    for (mab,) in site_b:
        count += 1
        s = bool(shadow_relation_blank(mab))
        o = bool(oracle_relation_blank(mab))
        if s != o:
            disagreements.append(("relationBlankFlag", mab, s, o))
            if len(disagreements) >= 5:
                break

    # --- SITE A: exhaustive over the 2^4 = 16 boolean inputs + fuzz ----------
    if len(disagreements) < 5:
        site_a = list(itertools.product([False, True], repeat=4))
        site_a += [tuple(rng.random() < 0.5 for _ in range(4))
                   for _ in range(N_FUZZ)]
        for required, initial_present, widget_is_radio, blank in site_a:
            count += 1
            s = bool(shadow_blank_choice(
                required, initial_present, widget_is_radio, blank))
            o = bool(oracle_blank_choice(
                required, initial_present, widget_is_radio, blank))
            if s != o:
                disagreements.append((
                    "blankChoiceOffered",
                    (required, initial_present, widget_is_radio, blank), s, o))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadows of relationBlankFlag and "
          "blankChoiceOffered agree with the patched source expressions on %d "
          "inputs (2 + 16 exhaustive + fuzz, seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
