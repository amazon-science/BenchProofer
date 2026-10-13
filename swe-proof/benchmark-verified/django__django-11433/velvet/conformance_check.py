#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11433 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `applies`/`applyPlan` over the flattened field list
              (`handed = eligible AND NOT (hasDefault AND noIncoming AND
              cleanedEmpty)`), via the mapping.md bijection (opts.fields ↔ List
              Field; the four real builtins ↔ the Bool fields; hand-off-or-skip
              ↔ the Bool entry). There are NO A-tagged callees in this bundle,
              so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.forms.models.construct_instance` applied at base_commit
              (the real correctness oracle, G-RESOLVE), driven on a real bound
              ModelForm + model instance. Its observable per field is whether
              the loop HANDS the field's cleaned value to that field's
              `save_form_data` write step (vs `continue`-ing past it so the
              model fallback stands) — the mapping.md §1 boundary. The write
              step itself is unchanged, downstream behaviour: some field
              classes interpret particular handed tokens as "no change", so
              observing the raw attribute would conflate the changed decision
              with unchanged token handling. The oracle therefore instruments
              the hand-off itself (per-field `save_form_data` reached or not).

They must agree on every input, field by field. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample. As a secondary
sanity check, for plain text-valued fields (whose write step is an
unconditional attribute write) the hand-off must coincide with the attribute
moving off its sentinel pre-state — pinning the two views together where they
provably agree.

Runs in-container (the prebuilt SWE-Bench instance image, patched), Django +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
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
        MEDIA_ROOT="/tmp/gconf_media_11433",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django import forms
from django.db import models
from django.forms.models import construct_instance

SEED = 11433
N_CASES = 20000          # × 8 fields ⇒ ≥ 1.6e5 per-field comparisons
SENTINEL = "\x00__UNASSIGNED__\x00"

# Fields f0..f2 declare a model default; f3..f5 do not (mapping.md §2:
# modelHasDefault is fixed per field slot at model-definition time).
# f6/f7 are file-type fields (f7 with a default) so the fuzz also drives the
# per-field decision through a field class whose write step interprets some
# handed tokens as "no change" (mapping.md §1 boundary note).
_NAMES = ["f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7"]
_HAS_DEFAULT = {"f0": True, "f1": True, "f2": True,
                "f3": False, "f4": False, "f5": False,
                "f6": False, "f7": True}
_FILE_FIELDS = {"f6", "f7"}
_TEXT_FIELDS = [n for n in _NAMES if n not in _FILE_FIELDS]

# empty / non-empty cleaned-value tokens (mapping.md §2: cleanedValueEmpty ⇔
# value ∈ EMPTY_VALUES == (None, '', [], (), {})). All tokens differ from
# SENTINEL, so for the plain text fields "handed" is also detectable as
# "attribute changed from SENTINEL" (secondary sanity check).
_EMPTY_TOKENS = [None, "", [], (), {}]
_NONEMPTY_TOKENS = ["de", "x", "0", " ", "value", 0]
# file-type form fields clean to None / '' / a file-ish value; keep their
# cleaned tokens in-domain for the write step while covering both knob values.
_EMPTY_TOKENS_FILE = [None, ""]
_NONEMPTY_TOKENS_FILE = ["de", "x", "up/y.bin"]


class _GModel(models.Model):
    f0 = models.CharField(max_length=50, default="DFLT0")
    f1 = models.CharField(max_length=50, default="DFLT1")
    f2 = models.CharField(max_length=50, default="DFLT2")
    f3 = models.CharField(max_length=50)
    f4 = models.CharField(max_length=50)
    f5 = models.CharField(max_length=50)
    f6 = models.FileField(upload_to="u", blank=True)
    f7 = models.FileField(upload_to="u", blank=True, default="d.bin")

    class Meta:
        app_label = "contenttypes"  # borrow an installed app's registry


class _GForm(forms.ModelForm):
    class Meta:
        model = _GModel
        fields = "__all__"


# --- the R/I shadow: Solution.lean applies / applyPlan -----------------------

def shadow_applies(eligible, has_default, no_incoming, cleaned_empty):
    """applies (Solution.lean): eligible ∧ ¬(hasDefault ∧ noIncoming ∧ empty)."""
    return bool(eligible and not (has_default and no_incoming and cleaned_empty))


# --- one fuzzed input -> (per-field knobs) -----------------------------------

class _Knob:
    __slots__ = ("name", "in_cleaned", "in_exclude", "in_fields_allow",
                 "no_incoming", "cleaned_empty", "cleaned_value")

    def __init__(self, name, rng, use_fields_arg):
        self.name = name
        self.in_cleaned = rng.random() < 0.75
        self.in_exclude = rng.random() < 0.20
        self.in_fields_allow = rng.random() < 0.80
        self.no_incoming = rng.random() < 0.55
        self.cleaned_empty = rng.random() < 0.50
        if name in _FILE_FIELDS:
            empties, nonempties = _EMPTY_TOKENS_FILE, _NONEMPTY_TOKENS_FILE
        else:
            empties, nonempties = _EMPTY_TOKENS, _NONEMPTY_TOKENS
        if self.cleaned_empty:
            self.cleaned_value = rng.choice(empties)
        else:
            self.cleaned_value = rng.choice(nonempties)

    def eligible(self, use_fields_arg):
        """The real eligibility gate (models.py:42-47), mirrored:
        in cleaned_data ∧ (no fields filter ∨ allowed) ∧ not excluded."""
        return bool(self.in_cleaned
                    and (not use_fields_arg or self.in_fields_allow)
                    and not self.in_exclude)


def _build_case(knobs, use_fields_arg):
    """Materialize a real bound ModelForm + instance for one case, and the
    fields/exclude args, exactly as the bijection (mapping.md §2) dictates."""
    # value_omitted_from_data looks at form.data for text widgets and at
    # form.files for file widgets: present iff NOT no_incoming. The payload
    # *value* is irrelevant to the guard (only membership is checked).
    data = {k.name: "submitted" for k in knobs
            if not k.no_incoming and k.name not in _FILE_FIELDS}
    files = {k.name: "submitted" for k in knobs
             if not k.no_incoming and k.name in _FILE_FIELDS}
    form = _GForm(data=data, files=files)
    # cleaned_data: name present iff in_cleaned; value per cleaned_empty knob.
    form.cleaned_data = {k.name: k.cleaned_value for k in knobs if k.in_cleaned}

    instance = _GModel()
    for k in knobs:
        setattr(instance, k.name, SENTINEL)  # uniform pre-state

    exclude = [k.name for k in knobs if k.in_exclude] or None
    if use_fields_arg:
        fields = [k.name for k in knobs if k.in_fields_allow]
    else:
        fields = None
    return form, instance, fields, exclude


def _oracle_handed(knobs, use_fields_arg):
    """Run the REAL patched construct_instance; observe per field whether the
    loop handed the cleaned value to that field's save_form_data write step
    (the mapping.md §1 observable). Instrumented by wrapping each model
    field's save_form_data for the duration of the call; the wrapper still
    performs the real (unchanged) write so the secondary attribute sanity
    check sees genuine behaviour."""
    form, instance, fields, exclude = _build_case(knobs, use_fields_arg)
    names = {k.name for k in knobs}
    handed = set()
    wrapped_fields = []
    for f in instance._meta.fields:
        if f.name not in names:
            continue
        orig = f.save_form_data

        def _wrap(inst, data, _name=f.name, _orig=orig):
            handed.add(_name)
            return _orig(inst, data)

        f.save_form_data = _wrap
        wrapped_fields.append(f)
    try:
        construct_instance(form, instance, fields=fields, exclude=exclude)
    finally:
        for f in wrapped_fields:
            del f.__dict__["save_form_data"]  # restore the class method

    # Secondary sanity check: for the plain text fields the write step is an
    # unconditional attribute write, so hand-off ⇔ attribute moved off the
    # sentinel. Pins the hand-off observable to the attribute view where the
    # two provably coincide.
    for name in _TEXT_FIELDS:
        if name in names:
            moved = getattr(instance, name) != SENTINEL
            assert (name in handed) == moved, (
                "text-field hand-off/attribute mismatch on %s: handed=%r "
                "moved=%r" % (name, name in handed, moved))
    return handed


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def run_case(knobs, use_fields_arg, tag):
        nonlocal count
        handed = _oracle_handed(knobs, use_fields_arg)
        for k in knobs:
            count += 1
            elig = k.eligible(use_fields_arg)
            sh = shadow_applies(elig, _HAS_DEFAULT[k.name],
                                k.no_incoming, k.cleaned_empty)
            orc = k.name in handed
            if sh != orc:
                disagreements.append((tag, k.name, dict(
                    in_cleaned=k.in_cleaned, in_exclude=k.in_exclude,
                    in_fields_allow=k.in_fields_allow,
                    use_fields_arg=use_fields_arg,
                    no_incoming=k.no_incoming, cleaned_empty=k.cleaned_empty,
                    has_default=_HAS_DEFAULT[k.name]), sh, orc))

    # --- boundary cases first (plan §4.1 step 4): the F2P scenario ------------
    # F2P: a field with a model default, omitted from the payload, with a
    # NON-empty cleaned value -> MUST be handed off (the new behaviour).
    def knob(name, in_cleaned, in_exclude, in_fields_allow, no_incoming,
             cleaned_empty, value):
        k = _Knob.__new__(_Knob)
        k.name = name
        k.in_cleaned = in_cleaned
        k.in_exclude = in_exclude
        k.in_fields_allow = in_fields_allow
        k.no_incoming = no_incoming
        k.cleaned_empty = cleaned_empty
        k.cleaned_value = value
        return k

    boundary = [
        # f0 has default, payload omitted, cleaned NON-empty -> handed (F2P).
        ([knob("f0", True, False, True, True, False, "de")], False),
        # f0 has default, payload omitted, cleaned EMPTY -> NOT handed.
        ([knob("f0", True, False, True, True, True, "")], False),
        # f0 has default, payload PRESENT, cleaned empty -> handed.
        ([knob("f0", True, False, True, False, True, "")], False),
        # f3 no default, payload omitted, cleaned empty -> handed (no default).
        ([knob("f3", True, False, True, True, True, "")], False),
        # excluded field -> not handed even if otherwise eligible.
        ([knob("f0", True, True, True, True, False, "de")], False),
        # not in cleaned_data -> not handed.
        ([knob("f0", False, False, True, True, False, "de")], False),
        # fields filter excludes f0 -> not handed.
        ([knob("f0", True, False, False, True, False, "de")], True),
        # file-type, no default, cleaned None -> handed (its unchanged write
        # step treats the handed token as "no change"; the DECISION is what
        # the guard governs and it says hand off).
        ([knob("f6", True, False, True, True, True, None)], False),
        # file-type WITH default, payload omitted, cleaned None -> NOT handed
        # (the guard fires: default + omitted + empty).
        ([knob("f7", True, False, True, True, True, None)], False),
        # file-type WITH default, payload omitted, cleaned NON-empty -> handed
        # (the F2P shape through the file-typed slot).
        ([knob("f7", True, False, True, True, False, "de")], False),
        # file-type WITH default, payload PRESENT (in files), cleaned empty ->
        # handed.
        ([knob("f7", True, False, True, False, True, None)], False),
    ]
    for knobs, ufa in boundary:
        run_case(knobs, ufa, "boundary")
        if len(disagreements) >= 5:
            break

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(N_CASES):
        if len(disagreements) >= 5:
            break
        use_fields_arg = rng.random() < 0.5
        knobs = [_Knob(name, rng, use_fields_arg) for name in _NAMES]
        run_case(knobs, use_fields_arg, "fuzz")

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d per-field "
              "comparisons:" % (len(disagreements), count))
        for tag, name, knobs, sh, orc in disagreements:
            print("  [%s] field=%s knobs=%r shadow=%r oracle=%r"
                  % (tag, name, knobs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of applyPlan agrees with patch.diff "
          "construct_instance hand-off decisions on %d per-field comparisons "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
