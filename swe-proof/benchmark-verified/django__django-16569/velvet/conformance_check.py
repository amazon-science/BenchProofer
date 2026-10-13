#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16569 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`shouldOfferDeletion` / `positionWithinInitial`, the removal-control
              decision) transliterated to Python over the abstract carrier
              (enabled, offer_on_extra, position, initial_count) via the
              mapping.md bijection (bool↔Bool, int|None↔Option Nat, int↔Nat).
              There are NO A-tagged callees in the impl region (no axioms in this
              bundle), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.forms.formsets.BaseFormSet.add_fields` applied at
              base_commit, observed as whether the per-row removal control
              (`DELETION_FIELD_NAME`) is added to the form's fields — the
              F2P-observable decision. The real function is bound onto a minimal
              stub formset/form so the decision can be probed in isolation (no
              live form rendering). The harness applies patch.diff before this
              runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 16569
N_FUZZ = 100_000

# abstract carrier domains (Solution.lean inputs)
ENABLED = [False, True]                 # self.can_delete            (Bool)
OFFER_ON_EXTRA = [False, True]          # self.can_delete_extra      (Bool)
# index : int | None  ->  Option Nat   (None ↔ none; non-negative int ↔ some i)
POSITIONS = [None, 0, 1, 2, 3, 5, 9, 50]
INITIAL_COUNTS = [0, 1, 2, 3, 5, 50]    # initial_form_count : Nat


# ---- the R/I shadow: shouldOfferDeletion transliterated to Python -----------
def shadow_decision(enabled, offer_on_extra, position, initial_count):
    """`shouldOfferDeletion enabled offerOnExtra position initialCount`
    (Solution.lean pure region). positionWithinInitial: present position counts
    iff it is strictly below initial_count; absent position contributes False."""
    position_within = (position is not None) and (position < initial_count)
    return enabled and (offer_on_extra or position_within)


# ---- the oracle: the patched real add_fields decision -----------------------
def _build_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={},
            USE_I18N=False,
        )
        django.setup()
    from django.forms.formsets import BaseFormSet, DELETION_FIELD_NAME
    from django.forms.widgets import CheckboxInput
    return BaseFormSet, DELETION_FIELD_NAME, CheckboxInput


class _StubForm:
    def __init__(self):
        self.fields = {}


def make_oracle(BaseFormSet, DELETION_FIELD_NAME, CheckboxInput):
    add_fields = BaseFormSet.add_fields                  # the patched function
    widget = CheckboxInput()

    class _StubFormSet:
        # add_fields uses: self.initial_form_count(), self.can_order,
        # self.can_delete, self.can_delete_extra, self.get_deletion_widget().
        can_order = False

        def __init__(self, enabled, offer_on_extra, initial_count):
            self.can_delete = enabled
            self.can_delete_extra = offer_on_extra
            self._initial_count = initial_count

        def initial_form_count(self):
            return self._initial_count

        def get_deletion_widget(self):
            return widget

    def oracle(enabled, offer_on_extra, position, initial_count):
        fs = _StubFormSet(enabled, offer_on_extra, initial_count)
        form = _StubForm()
        add_fields(fs, form, position)                   # patched: never raises
        return DELETION_FIELD_NAME in form.fields

    return oracle


def all_configs():
    """The full abstract product (2*2*8*6 = 192) — boundary enumeration."""
    return list(itertools.product(ENABLED, OFFER_ON_EXTRA, POSITIONS, INITIAL_COUNTS))


def fuzz_configs(n, rng):
    for _ in range(n):
        yield (rng.choice(ENABLED), rng.choice(OFFER_ON_EXTRA),
               rng.choice([None] + list(range(0, 60))), rng.randint(0, 60))


def main():
    rng = random.Random(SEED)
    bundle = _build_django()
    oracle = make_oracle(*bundle)
    disagreements = []
    count = 0
    for cfg in itertools.chain(all_configs(), fuzz_configs(N_FUZZ, rng)):
        count += 1
        shadow = shadow_decision(*cfg)
        truth = oracle(*cfg)
        if shadow != truth:
            disagreements.append((cfg, shadow, truth))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, sh, tr in disagreements:
            print("  cfg=%r shadow=%r oracle=%r" % (cfg, sh, tr))
        return 1
    print("G-CONF OK: R/I shadow of deletionFieldDecision (shouldOfferDeletion) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
