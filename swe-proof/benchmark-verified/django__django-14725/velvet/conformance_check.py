#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14725 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`reported` / `storedAfter`, the `if noCreate then … else …`
              branch) transliterated to Python over the abstract carrier
              (edit_only ↔ noCreate, saved/created instances ↔ List Nat of
              identities, list `+` ↔ `++`) via the mapping.md §2 bijection.
              The A-tagged callees (`save_existing_objects`, `save_new_objects`)
              are left as stubs returning the supplied free-input identity lists
              — G-CONF isolates the R/I legs, so the A legs stay with G-AX. The
              impl's computed output is pure R/I, so conf_skip=false.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `BaseModelFormSet.save` (the harness applies the gold patch before
              this runs, G-RESOLVE). We bind it onto a minimal stub formset whose
              `edit_only` flag and two component persistence steps are controlled,
              recording (a) the list it returns and (b) WHETHER the new-row
              producer was invoked — the F2P-observable side effect (new rows
              created or not).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied).
stdlib + django only; no database needed (the component callees are stubbed,
isolating the R/I branch the patch added). The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 14725
N_FUZZ = 100_000


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[],
            USE_TZ=True,
        )
    django.setup()


# --- the R/I shadow: Solution.lean reported / storedAfter, transliterated -----

def shadow_reported(no_create, existing, fresh):
    """reported noCreate existing fresh: existing when new rows forbidden, else
    existing followed by fresh."""
    if no_create:
        return list(existing)
    return list(existing) + list(fresh)


def shadow_new_called(no_create):
    """storedAfter side-effect frame: the new-row producer runs (growing the
    persisted set) exactly when new rows are permitted."""
    return not no_create


# --- the oracle: the patched real BaseModelFormSet.save -----------------------

class _StubFormSet:
    """A minimal carrier on which the REAL patched BaseModelFormSet.save runs.
    The two component persistence steps are stubbed to return the supplied
    free-input identity lists and to record whether the new-row producer ran;
    the commit=False bookkeeping block is exercised but inert."""

    def __init__(self, edit_only, existing, fresh):
        self.edit_only = edit_only
        self._existing = list(existing)
        self._fresh = list(fresh)
        self.new_called = False
        self.saved_forms = []

    def save_existing_objects(self, commit=True):
        return list(self._existing)

    def save_new_objects(self, commit=True):
        self.new_called = True
        return list(self._fresh)


def oracle_save(save_fn, no_create, existing, fresh):
    """Drive the real patched save() and observe (returned list, new producer
    invoked)."""
    stub = _StubFormSet(no_create, existing, fresh)
    out = save_fn(stub, commit=True)
    return list(out), stub.new_called


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield (True, [], [])
    yield (False, [], [])
    yield (True, [1], [2])
    yield (False, [1], [2])
    yield (True, [], [9])
    yield (False, [], [9])
    yield (True, [7], [])
    yield (False, [7], [])
    yield (True, [1, 2, 3], [4, 5])
    yield (False, [1, 2, 3], [4, 5])
    for _ in range(n):
        no_create = rng.random() < 0.5
        n_e = rng.randint(0, 8)
        n_f = rng.randint(0, 8)
        existing = [rng.randint(0, 10 ** 6) for _ in range(n_e)]
        fresh = [rng.randint(0, 10 ** 6) for _ in range(n_f)]
        yield (no_create, existing, fresh)


def main():
    _bootstrap_django()
    from django.forms.models import BaseModelFormSet
    save_fn = BaseModelFormSet.save  # the patched function under test

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for no_create, existing, fresh in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh_list = shadow_reported(no_create, existing, fresh)
        sh_new = shadow_new_called(no_create)
        orc_list, orc_new = oracle_save(save_fn, no_create, existing, fresh)
        if sh_list != orc_list or sh_new != orc_new:
            disagreements.append(
                (no_create, existing, fresh,
                 (sh_list, sh_new), (orc_list, orc_new)))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for nc, e, f, sh, orc in disagreements:
            print("  edit_only=%r existing=%r fresh=%r shadow=%r oracle=%r"
                  % (nc, e, f, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of saveFormset (reported list + new-row "
          "producer invoked) agrees with patch.diff behaviour on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
