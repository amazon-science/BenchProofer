#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14034 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`subRequired`
              and the `requiredPlan` fold) transliterated to Python. The model's
              boolean inputs are read from the REAL repo objects via the
              mapping.md bijection:
                 outerRequired = widget.use_required_attribute(bf.initial)
                                 and field.required and form.use_required_attribute
                 requireAll    = field.require_all_fields
                 per sub-field: marksRequired = subwidget.use_required_attribute(bf.initial)
                                required      = subfield.required
              There is NO axiom model to leave as a real callee here (the bundle
              ships no consumed axioms); the entire impl region is R/I.
  * ORACLE  — `patch.diff`'s behaviour: the per-sub-widget `required` attribute
              actually rendered by a real patched MultiValueField/MultiWidget
              form (the real correctness oracle, G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patched), Django +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import re
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
        INSTALLED_APPS=[],
    )
    django.setup()

from django.forms import CharField, Form, MultiValueField, MultiWidget
from django.forms.widgets import HiddenInput, TextInput

SEED = 14034
N_FUZZ = 100_000
MAX_SUBS = 4


class _MF(MultiValueField):
    def compress(self, data_list):
        return None


# --- the R/I shadow: Solution.lean subRequired / requiredPlan ----------------

def sub_required(outer_required, require_all, marks_required, required):
    """subRequired (Solution.lean): outer gate ∧ (require-all ∨ (opt-in ∧ req))."""
    return bool(outer_required and (require_all or (marks_required and required)))


def shadow_plan(outer_required, require_all, subs):
    """requiredPlan (Solution.lean) over a list of (marks_required, required)
    tuples — the R/I shadow of the requiredFlags fold."""
    return [sub_required(outer_required, require_all, m, r) for (m, r) in subs]


# --- the oracle: patch.diff's rendered per-sub-widget `required` -------------

_INPUT_RE = re.compile(r"<input[^>]*>")


def _rendered_required(input_tag):
    """Whether an <input ...> tag carries the boolean `required` attribute."""
    return bool(re.search(r"(?:\s)required(?:\s|>|=)", input_tag))


def build_form(sub_specs, outer_required, require_all):
    """sub_specs: list of (required_bool, kind) with kind in {'text','hidden'}."""
    fields = [CharField(required=r) for (r, _) in sub_specs]
    subwidgets = [TextInput() if k == "text" else HiddenInput()
                  for (_, k) in sub_specs]

    class F(Form):
        f = _MF(
            fields=tuple(fields),
            widget=MultiWidget(widgets=subwidgets),
            require_all_fields=require_all,
            required=outer_required,
        )

    return F({})


def oracle_plan(sub_specs, outer_required, require_all):
    """Render the real patched MultiValueField and read the per-sub-widget
    `required` attribute actually emitted."""
    form = build_form(sub_specs, outer_required, require_all)
    bf = form["f"]
    inputs = _INPUT_RE.findall(str(bf))
    return [_rendered_required(t) for t in inputs]


def model_inputs(sub_specs, outer_required, require_all):
    """Read the model's boolean inputs from the REAL field/widget objects
    (mapping.md §2 R-refinements)."""
    form = build_form(sub_specs, outer_required, require_all)
    bf = form["f"]
    field = bf.field
    widget = field.widget
    outer = bool(widget.use_required_attribute(bf.initial)
                 and field.required and form.use_required_attribute)
    require_all_real = bool(field.require_all_fields)
    subs = [(bool(sw.use_required_attribute(bf.initial)), bool(sf.required))
            for (sf, sw) in zip(field.fields, widget.widgets)]
    return outer, require_all_real, subs


def gen_cases(n_fuzz, rng):
    # boundary cases first (plan §4.1 step 4): the F2P scenario + neighbours
    yield ([(True, "text"), (False, "text")], True, False)   # F2P PartiallyRequired
    yield ([(False, "text"), (True, "text")], True, False)   # mirror
    yield ([(True, "text"), (False, "text")], True, True)    # require_all=True
    yield ([(True, "text"), (False, "text")], False, False)  # outer not required
    yield ([(True, "hidden"), (True, "text")], True, False)  # hidden sub-widget
    yield ([(True, "text")], True, False)                    # single sub-field
    yield ([], True, False)                                  # no sub-fields (n=0)
    for _ in range(n_fuzz):
        n = rng.randint(1, MAX_SUBS)
        specs = [(rng.random() < 0.5, "text" if rng.random() < 0.7 else "hidden")
                 for _ in range(n)]
        outer = rng.random() < 0.6
        require_all = rng.random() < 0.5
        yield (specs, outer, require_all)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (specs, outer, require_all) in gen_cases(N_FUZZ, rng):
        count += 1
        o, ra, subs = model_inputs(specs, outer, require_all)
        shadow = shadow_plan(o, ra, subs)
        oracle = oracle_plan(specs, outer, require_all)
        if shadow != oracle:
            disagreements.append((specs, outer, require_all, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for specs, outer, ra, sh, orc in disagreements:
            print("  specs=%r outer=%r require_all=%r shadow=%r oracle=%r"
                  % (specs, outer, ra, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of requiredFlags agrees with patch.diff "
          "rendered per-sub-widget `required` on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
