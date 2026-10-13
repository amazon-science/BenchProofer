#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14631 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`slotValue`,
              `initialFor`, the `cleanedSeq` fold) transliterated to Python over
              the real repo types via the mapping.md bijection (FieldSlot ↔ a
              disabled-or-enabled DateTimeField slot; Stamp ↔ datetime
              second/microsecond). There is NO axiom model to leave as a real
              callee here (the bundle ships no consumed axioms); the one
              A-reference (`initialFor == BoundField.initial`) is validated by
              G-AX, while G-CONF tests that the *whole* R/I value-resolution
              agrees with the patched form.
  * ORACLE  — `patch.diff`'s behaviour: the patched `BaseForm._clean_fields`,
              i.e. `form.cleaned_data` of a real disabled/enabled DateTimeField
              form (the real correctness oracle, G-RESOLVE).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.

Coverage note (plan §4.1, logged not silent): the changed behaviour lives in the
read-only (disabled) path. The enabled path supplies a value through form data;
the default DateTimeField input format carries no sub-second precision, so the
enabled path is fuzzed with sub=0 (a microsecond-bearing string would not
round-trip through the widget and is out of the field's input domain). The
read-only path is fuzzed over the full second/microsecond range.
"""
import datetime
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django import forms
from django.forms.widgets import TextInput

SEED = 14631
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean slotValue/initialFor/cleanedSeq -----------

def initial_for(stored, coarse):
    """initialFor (Solution.lean): coarse slot drops the sub-second part."""
    if coarse:
        return stored.replace(microsecond=0)
    return stored


def slot_value(read_only, coarse, stored, given):
    """slotValue (Solution.lean): read-only ⇒ exposed stored; else given."""
    if read_only:
        return initial_for(stored, coarse)
    return given


def shadow_clean(slots):
    """cleanedSeq (Solution.lean) over a list of (read_only, coarse, stored,
    given) tuples — the R/I shadow of the cleanFields fold."""
    return [slot_value(ro, co, st, gv) for (ro, co, st, gv) in slots]


# --- the oracle: patch.diff's _clean_fields behaviour ------------------------

def oracle_clean(slots):
    """For each slot build a real Django form with a single DateTimeField and
    return its cleaned datetime — exercising the patched _clean_fields path.

    A read-only slot ⇒ disabled field with callable initial = stored.
    An enabled slot  ⇒ field fed `given` via bound data (sub-second dropped by
    the input format, matching the shadow's enabled-path sub=0 constraint)."""
    out = []
    for (read_only, coarse, stored, given) in slots:
        widget = None if coarse else TextInput
        if read_only:
            class F(forms.Form):
                dt = forms.DateTimeField(
                    initial=lambda s=stored: s, disabled=True,
                    **({"widget": widget} if widget else {}),
                )
            form = F({})
        else:
            class F(forms.Form):
                dt = forms.DateTimeField(
                    disabled=False,
                    **({"widget": widget} if widget else {}),
                )
            form = F({"dt": given.strftime("%Y-%m-%d %H:%M:%S")})
        assert form.errors == {}, "oracle form errored: %r" % (form.errors,)
        out.append(form.cleaned_data["dt"])
    return out


def fuzz_slots(n, rng):
    base_date = (2006, 10, 25, 14, 30)
    # boundary cases first (plan §4.1 step 4)
    yield [(True, True, datetime.datetime(2006, 10, 25, 14, 30, 45, 123456),
            datetime.datetime(2006, 10, 25, 14, 30, 45, 0))]          # the F2P case
    yield [(True, False, datetime.datetime(2006, 10, 25, 14, 30, 45, 123456),
            datetime.datetime(2006, 10, 25, 14, 30, 45, 0))]          # micro widget
    yield [(False, True, datetime.datetime(2006, 10, 25, 14, 30, 45, 0),
            datetime.datetime(2006, 10, 25, 14, 30, 45, 0))]          # enabled
    yield []                                                          # empty
    for _ in range(n):
        sec = rng.randint(0, 59)
        sub = rng.randint(0, 999999)
        read_only = rng.random() < 0.5
        coarse = rng.random() < 0.5
        # enabled path: sub-second not representable through the input format
        stored_sub = sub if read_only else 0
        given_sub = 0
        stored = datetime.datetime(*base_date, sec, stored_sub)
        given = datetime.datetime(*base_date, sec, given_sub)
        yield [(read_only, coarse, stored, given)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for slots in fuzz_slots(N_FUZZ, rng):
        count += 1
        shadow = shadow_clean(slots)
        oracle = oracle_clean(slots)
        if shadow != oracle:
            disagreements.append((slots, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for slots, sh, orc in disagreements:
            print("  slots=%r shadow=%r oracle=%r" % (slots, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of cleanFields agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
