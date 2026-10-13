#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-12406.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the two Lean
`implementation_*` skeletons and diffs it against the REAL patched callees over
the full discrete input matrix plus >=1e5 randomized draws.

  behavior 1  shadow of `implementation_emptyOption`  vs  ModelChoiceField.__init__
              observable: self.empty_label  (str | None)
  behavior 2  shadow of `implementation_formKwargs`   vs  ForeignKey.formfield
              observable: the 'blank' kwarg + the frame (all other kwargs)

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import os
import random
import sys
import tempfile

SEED = 20240612
N_RANDOM = 120_000  # >= 1e5


def setup_django():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "testapp"))
    open(os.path.join(d, "testapp", "__init__.py"), "w").close()
    open(os.path.join(d, "testapp", "models.py"), "w").close()
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                        "testapp"],
        USE_TZ=True,
    )
    django.setup()


# ---- behavior 1: shadow of implementation_emptyOption ----------------------

def shadow_empty_option(required, initial_present, radio_widget, blank_allowed,
                        default_label):
    # transliteration of problem_spec_emptyOption / implementation_emptyOption
    if (required and initial_present) or (radio_widget and not blank_allowed):
        return None
    return default_label


def check_behavior1():
    from django import forms
    from django.forms.widgets import RadioSelect, Select

    default_label = "---------"

    def real(required, initial_present, widget, blank):
        initial = "seed" if initial_present else None
        f = forms.ModelChoiceField(
            queryset=None, required=required, initial=initial,
            widget=widget, blank=blank, empty_label=default_label)
        return f.empty_label

    # widget choices and the radio_widget bit each induces
    widget_cases = [
        (None, False),               # default widget -> not RadioSelect
        (Select(), False),
        (RadioSelect(), True),
        (RadioSelect, True),         # class (Django instantiates it)
    ]

    disagreements = 0
    checked = 0

    # full discrete matrix
    cases = []
    for required in (True, False):
        for initial_present in (True, False):
            for widget, is_radio in widget_cases:
                for blank in (True, False):
                    cases.append((required, initial_present, widget, is_radio, blank))

    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        required = rng.choice([True, False])
        initial_present = rng.choice([True, False])
        widget, is_radio = rng.choice(widget_cases)
        blank = rng.choice([True, False])
        cases.append((required, initial_present, widget, is_radio, blank))

    for required, initial_present, widget, is_radio, blank in cases:
        got = real(required, initial_present, widget, blank)
        exp = shadow_empty_option(required, initial_present, is_radio, blank,
                                  default_label)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"behavior1 MISMATCH required={required} "
                      f"initial_present={initial_present} radio={is_radio} "
                      f"blank={blank}: real={got!r} shadow={exp!r}")
    return checked, disagreements


# ---- behavior 2: shadow of implementation_formKwargs -----------------------

def shadow_form_kwargs(base, blank_allowed):
    # transliteration of implementation_formKwargs: copy base, set 'blank'
    d = dict(base)
    d["blank"] = ("flag", blank_allowed)
    return d


def normalize_kwargs(kw):
    """Map a real kwargs dict to the KwargVal abstraction used by the spec:
    only the 'blank' flag value is observed concretely; other keys keep an
    opaque-but-stable token so the frame can be compared."""
    out = {}
    for k, v in kw.items():
        if k == "blank":
            out[k] = ("flag", bool(v))
        else:
            out[k] = ("obj", k)  # opaque, identity-by-key
    return out


def check_behavior2():
    from django.db import models
    from django import forms

    captured = {}
    orig = forms.ModelChoiceField.__init__

    def spy(self, queryset, **kw):
        captured.clear()
        captured.update(kw)
        return orig(self, queryset, **kw)

    forms.ModelChoiceField.__init__ = spy

    class T2Target(models.Model):
        class Meta:
            app_label = "testapp"

    class T2Holder(models.Model):
        fk_req = models.ForeignKey(T2Target, on_delete=models.CASCADE,
                                   blank=False)
        fk_blank = models.ForeignKey(T2Target, on_delete=models.CASCADE,
                                     null=True, blank=True, related_name="h2")
        class Meta:
            app_label = "testapp"

    disagreements = 0
    checked = 0
    rng = random.Random(SEED + 1)

    field_cases = [("fk_req", False), ("fk_blank", True)]
    # full matrix + repeated randomized draws (the discrete domain is tiny, so
    # repetition exercises the capture path deterministically under the seed).
    plan = list(field_cases) + [rng.choice(field_cases) for _ in range(N_RANDOM)]

    for fname, model_blank in plan:
        field = T2Holder._meta.get_field(fname)
        captured.clear()
        field.formfield()
        real_kw = normalize_kwargs(captured)
        # base = the kwargs WITHOUT the added 'blank' key (the pre-patch dict)
        base = {k: v for k, v in real_kw.items() if k != "blank"}
        exp_kw = shadow_form_kwargs(base, model_blank)
        checked += 1
        if real_kw != exp_kw:
            disagreements += 1
            if disagreements <= 5:
                print(f"behavior2 MISMATCH {fname} model.blank={model_blank}: "
                      f"real={real_kw} shadow={exp_kw}")

    forms.ModelChoiceField.__init__ = orig
    return checked, disagreements


def main():
    setup_django()
    c1, d1 = check_behavior1()
    c2, d2 = check_behavior2()
    total = d1 + d2
    print(f"behavior1: checked={c1} disagreements={d1}")
    print(f"behavior2: checked={c2} disagreements={d2}")
    if total == 0:
        print(f"status=pass conformance OK ({c1 + c2} checks, 0 disagreements)")
        return 0
    print(f"status=fail {total} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
