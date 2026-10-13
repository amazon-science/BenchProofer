#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14608 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (buildNonFormErrors)
              transliterated to Python over the *real* repo types, via the
              mapping.md bijection. The impl preserves the message list and
              attaches the CSS class computed by `cssClassFor (some "nonform")`.
              `cssClassFor` is concrete/computable so it is transliterated here;
              its equality to the real ErrorList class string is *separately*
              validated as an A-reference by axiom_check.py (G-AX).
  * ORACLE  — `patch.diff`'s behaviour. The patch changes the construction
              `self._non_form_errors = self.error_class(...)` to pass
              `error_class='nonform'`. Two oracle legs:
                (1) HIGH-VOLUME: the patched construction expression transliterated
                    VERBATIM — `ErrorList(msgs, error_class='nonform')` (the real
                    repo callee `self.error_class` IS `django.forms.utils.ErrorList`,
                    mapping.md §1) — fuzzed over message lists. Reading back its
                    stored messages and `.error_class` is the real behaviour of the
                    construction op the patch performs.
                (2) LIVE ANCHORS: real bound `FormSet`s driven over their
                    validate_max / validate_min / custom-clean non-form-error paths
                    so the actual patched `full_clean` runs end-to-end at both
                    construction sites (formsets.py:336 empty, :383 validation
                    error). Confirms the collection `non_form_errors()` really
                    builds matches the shadow.

They must agree on every input: stored messages == the messages, rendered class
== `errorlist nonform`. Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys

SEED = 14608
N_FUZZ = 100_000


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True, USE_TZ=False, DATABASES={},
            INSTALLED_APPS=['django.forms'], USE_I18N=False,
        )
        django.setup()


# --- the R/I shadow: Solution.lean buildNonFormErrors, transliterated --------

def css_class_for(modifier):
    """cssClassFor (modifier : Option (List Char)) transliterated to str.
    modifier=None -> 'errorlist'; modifier=label -> 'errorlist ' + label."""
    if modifier is None:
        return "errorlist"
    return "errorlist " + modifier


def shadow_build(messages):
    """buildNonFormErrors transliterated: preserve the message list, attach the
    class computed by cssClassFor (some 'nonform'). Returns (data, cssClass)."""
    return (list(messages), css_class_for("nonform"))


# --- oracle leg (1): the patched construction expression, verbatim ----------

def oracle_construct(ErrorList, messages):
    """patch.diff op: `self._non_form_errors = self.error_class(e.error_list,
    error_class='nonform')`. `self.error_class` IS ErrorList (mapping.md §1).
    Build it on the given messages and read back stored messages + class."""
    el = ErrorList(list(messages), error_class='nonform')
    return ([str(m) for m in el], el.error_class)


# --- oracle leg (2): live bound FormSets, real full_clean at both sites ------

def _choice_formset(extra, **kw):
    from django import forms
    from django.forms.formsets import formset_factory, BaseFormSet
    from django.core.exceptions import ValidationError

    class Choice(forms.Form):
        choice = forms.CharField()
        votes = forms.IntegerField()

    return forms, formset_factory(Choice, extra=extra, **kw)


def live_anchors():
    """Yield (label, observed_messages, observed_css) from real bound formsets
    whose patched full_clean built self._non_form_errors at each site."""
    from django import forms
    from django.forms.formsets import formset_factory, BaseFormSet
    from django.core.exceptions import ValidationError

    class Choice(forms.Form):
        choice = forms.CharField()
        votes = forms.IntegerField()

    # site :383 — validate_max raises -> error_class(e.error_list, 'nonform')
    FS = formset_factory(Choice, extra=1, max_num=1, validate_max=True)
    fs = FS({
        'choices-TOTAL_FORMS': '2', 'choices-INITIAL_FORMS': '0',
        'choices-MIN_NUM_FORMS': '0', 'choices-MAX_NUM_FORMS': '2',
        'choices-0-choice': 'Zero', 'choices-0-votes': '0',
        'choices-1-choice': 'One', 'choices-1-votes': '1',
    }, auto_id=False, prefix='choices')
    assert not fs.is_valid()
    nfe = fs.non_form_errors()
    yield ("validate_max", [str(m) for m in nfe], nfe.error_class)

    # site :383 — validate_min raises
    FS = formset_factory(Choice, extra=1, min_num=3, validate_min=True)
    fs = FS({
        'choices-TOTAL_FORMS': '1', 'choices-INITIAL_FORMS': '0',
        'choices-MIN_NUM_FORMS': '0', 'choices-MAX_NUM_FORMS': '1',
        'choices-0-choice': 'Zero', 'choices-0-votes': '0',
    }, auto_id=False, prefix='choices')
    assert not fs.is_valid()
    nfe = fs.non_form_errors()
    yield ("validate_min", [str(m) for m in nfe], nfe.error_class)

    # site :383 — custom clean() raising a cross-form ValidationError
    class DrinkFormSet(BaseFormSet):
        def clean(self):
            if any(self.errors):
                return
            names = []
            for form in self.forms:
                name = form.cleaned_data.get('name')
                if name in names:
                    raise ValidationError('You may only specify a drink once.')
                names.append(name)

    class Drink(forms.Form):
        name = forms.CharField()

    FS = formset_factory(Drink, formset=DrinkFormSet, extra=3)
    fs = FS({
        'drinks-TOTAL_FORMS': '2', 'drinks-INITIAL_FORMS': '0',
        'drinks-MIN_NUM_FORMS': '0', 'drinks-MAX_NUM_FORMS': '1000',
        'drinks-0-name': 'Gin and Tonic', 'drinks-1-name': 'Gin and Tonic',
    }, prefix='drinks')
    assert not fs.is_valid()
    nfe = fs.non_form_errors()
    yield ("custom_clean", [str(m) for m in nfe], nfe.error_class)

    # site :336 — empty construction: a valid formset has empty non_form_errors
    # that still carries the nonform class.
    FS = formset_factory(Choice, extra=1)
    fs = FS({
        'choices-TOTAL_FORMS': '1', 'choices-INITIAL_FORMS': '0',
        'choices-MIN_NUM_FORMS': '0', 'choices-MAX_NUM_FORMS': '1000',
        'choices-0-choice': 'Zero', 'choices-0-votes': '0',
    }, auto_id=False, prefix='choices')
    fs.full_clean()
    nfe = fs.non_form_errors()
    yield ("empty_site", [str(m) for m in nfe], nfe.error_class)


def fuzz_messages(n, rng):
    alphabet = string.ascii_letters + string.digits + " .,'\"<>&-_é•"
    # boundary cases first
    yield []
    yield [""]
    yield ["Please submit at most 1 form."]
    yield ["Please submit at least 3 forms."]
    yield ["You may only specify a drink once."]
    yield ["a", "b", "c"]
    yield ["with <html> & 'special' chars"]
    for _ in range(n):
        k = rng.randint(0, 4)
        yield ["".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
               for _ in range(k)]


def main():
    _configure_django()
    from django.forms.utils import ErrorList

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # leg (1): high-volume construction fuzz over message lists
    for msgs in fuzz_messages(N_FUZZ, rng):
        count += 1
        o_data, o_css = oracle_construct(ErrorList, msgs)
        s_data, s_css = shadow_build(msgs)
        if s_data != o_data or s_css != o_css:
            disagreements.append((count, msgs, (o_data, o_css), (s_data, s_css)))
            if len(disagreements) >= 5:
                break

    # leg (2): live bound-formset anchors at both construction sites
    if not disagreements:
        for label, o_data, o_css in live_anchors():
            count += 1
            s_data, s_css = shadow_build(o_data)
            if s_data != o_data or s_css != o_css:
                disagreements.append((label, o_data, (o_data, o_css), (s_data, s_css)))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tag, msgs, oracle, shadow in disagreements:
            print("  case=%r msgs=%r oracle=%r shadow=%r"
                  % (tag, msgs, oracle, shadow))
        return 1
    print("G-CONF OK: R/I shadow of buildNonFormErrors agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
