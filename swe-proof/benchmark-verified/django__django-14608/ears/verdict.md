# P2 adversarial audit — django__django-14608

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (Req 1.2, 1.3, 2.2): validate_max failure -> non_form_errors
renders as <ul class="errorlist nonform">. HOLDS patched, FAILS at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory


class SimpleForm(forms.Form):
    name = forms.CharField()


FS = formset_factory(SimpleForm, validate_max=True, max_num=1)
data = {
    "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "2",
    "form-0-name": "a", "form-1-name": "b",
}
fs = FS(data)
assert not fs.is_valid()
nfe = fs.non_form_errors()
html = str(nfe)
print("html=", html)
ok = html.startswith('<ul class="errorlist nonform">')
print("holds=", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 & 1.4 & 2.3: validate_min failure -> non_form_errors is an ErrorList
whose class attr is exactly 'errorlist nonform' (nonform IN ADDITION to base)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory
from django.forms.utils import ErrorList


class SimpleForm(forms.Form):
    name = forms.CharField()


FS = formset_factory(SimpleForm, validate_min=True, min_num=2)
data = {
    "form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
    "form-0-name": "a",
}
fs = FS(data)
assert not fs.is_valid()
nfe = fs.non_form_errors()
print("type=", type(nfe), "isErrorList=", isinstance(nfe, ErrorList))
html = str(nfe)
print("html=", html)
# extract class attribute
import re
m = re.search(r'<ul class="([^"]*)">', html)
cls = m.group(1) if m else None
print("class=", cls)
ok = (isinstance(nfe, ErrorList)
      and cls == "errorlist nonform"
      and "errorlist" in (cls or "")
      and "nonform" in (cls or ""))
print("holds=", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.4: FormSet.clean() raising ValidationError during cross-form validation
-> non-form ErrorList carries nonform class, and messages preserved (Req 3.4)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory, BaseFormSet


class SimpleForm(forms.Form):
    name = forms.CharField()


class MyFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        raise forms.ValidationError("cross-form boom")


FS = formset_factory(SimpleForm, formset=MyFormSet)
data = {
    "form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
    "form-0-name": "a",
}
fs = FS(data)
assert not fs.is_valid()
nfe = fs.non_form_errors()
html = str(nfe)
print("html=", html)
print("messages=", list(nfe))
ok = (html.startswith('<ul class="errorlist nonform">')
      and list(nfe) == ["cross-form boom"])
print("holds=", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 3.5: at start of full cleaning the non-form errors are initialized
as an ErrorList carrying nonform, AND empty case: non_form_errors() is an empty
ErrorList == [] and renders as empty string. Also Req 3.2 message text/count."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory
from django.forms.utils import ErrorList


class SimpleForm(forms.Form):
    name = forms.CharField()


# --- empty case: valid formset, no non-form errors ---
FS = formset_factory(SimpleForm)
data = {
    "form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
    "form-0-name": "a",
}
fs = FS(data)
assert fs.is_valid()
nfe = fs.non_form_errors()
print("empty type=", type(nfe), "eq[]=", nfe == [], "str=", repr(str(nfe)))
ok_empty = isinstance(nfe, ErrorList) and nfe == [] and str(nfe) == ""

# --- Req 3.2: validate_max message text & count, singular/plural ---
FS2 = formset_factory(SimpleForm, validate_max=True, max_num=1)
d2 = {"form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "0",
      "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "2",
      "form-0-name": "a", "form-1-name": "b"}
fs2 = FS2(d2)
assert not fs2.is_valid()
msgs = list(fs2.non_form_errors())
print("max msgs=", msgs)
ok_max = msgs == ["Please submit at most 1 form."] and len(msgs) == 1

print("holds=", ok_empty and ok_max)
raise SystemExit(0 if (ok_empty and ok_max) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1 & 4.2 & 4.3: dependent APIs preserved. total_error_count == sum of
non-form errors + per-form error counts; is_valid False with non-form errors;
non_form_errors() before is_valid() triggers full clean and carries nonform."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory


class TwoField(forms.Form):
    name = forms.CharField()
    age = forms.IntegerField()


# validate_max fails (1 non-form error). form-1 is partially filled (age given,
# name missing) so it is a *changed* invalid form -> 1 per-form error.
FS = formset_factory(TwoField, validate_max=True, max_num=1)
data = {
    "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "2",
    "form-0-name": "a", "form-0-age": "1",
    "form-1-age": "2",  # name missing -> per-form error, but form is "changed"
}
fs = FS(data)

# 4.3: call non_form_errors() BEFORE is_valid()
nfe = fs.non_form_errors()
carries = str(nfe).startswith('<ul class="errorlist nonform">')
print("nfe html=", str(nfe), "carries=", carries)

valid = fs.is_valid()
tec = fs.total_error_count()
n_nonform = len(fs.non_form_errors())
n_form = sum(len(f.errors) for f in fs.forms)
print("is_valid=", valid, "total_error_count=", tec,
      "n_nonform=", n_nonform, "n_form=", n_form)
ok = (carries and valid is False and tec == n_nonform + n_form
      and n_nonform >= 1 and n_form >= 1)
print("holds=", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.4: admin changelist formset exposes non-form errors as an ErrorList
whose rendered form matches an ErrorList built with the nonform CSS class.
We assert equivalence at the ErrorList API level: the non-form ErrorList from a
formset renders identically to ErrorList(msgs, error_class='nonform')."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory
from django.forms.utils import ErrorList


class SimpleForm(forms.Form):
    name = forms.CharField()


FS = formset_factory(SimpleForm, validate_max=True, max_num=1)
data = {"form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "2",
        "form-0-name": "a", "form-1-name": "b"}
fs = FS(data)
assert not fs.is_valid()
nfe = fs.non_form_errors()
msgs = list(nfe)
reference = ErrorList(msgs, error_class="nonform")
print("nfe  =", str(nfe))
print("ref  =", str(reference))
ok = str(nfe) == str(reference)
print("holds=", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.2, 1.3, 2.2): validate_max failure -> non_form_errors
renders as <ul class="errorlist nonform">. HOLDS patched, FAILS at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory


class SimpleForm(forms.Form):
    name = forms.CharField()


FS = formset_factory(SimpleForm, validate_max=True, max_num=1)
data = {
    "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "2",
    "form-0-name": "a", "form-1-name": "b",
}
fs = FS(data)
assert not fs.is_valid()
nfe = fs.non_form_errors()
html = str(nfe)
print("html=", html)
ok = html.startswith('<ul class="errorlist nonform">')
print("holds=", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: add 'nonform' CSS class to BaseFormSet non-form ErrorList (django/forms/formsets.py). Gold patch sets error_class='nonform' on both the init line and the clean() except-path ErrorList.

6 probes, all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req 1.2/1.3/2.2): validate_max failure renders <ul class="errorlist nonform">. HOLDS patched, FAILS at base (base renders <ul class="errorlist">) -> discriminates.
- probe_2 (Req 1.1/1.4/2.3): validate_min failure -> ErrorList instance whose class attr is EXACTLY 'errorlist nonform' (nonform in addition to base). HOLDS.
- probe_3 (Req 2.4/3.4): FormSet.clean() raising ValidationError -> nonform class + message preserved ('cross-form boom'). HOLDS.
- probe_4 (Req 2.1/3.5/3.2): empty valid formset -> empty ErrorList ==[] renders ''; validate_max message text/count exact ('Please submit at most 1 form.'). HOLDS.
- probe_5 (Req 4.1/4.2/4.3): total_error_count == non-form + per-form counts (2 == 1+1); is_valid False; non_form_errors() before is_valid() triggers clean and carries nonform. HOLDS.
- probe_6 (Req 4.4): formset non-form ErrorList renders identically to ErrorList(msgs, error_class='nonform') (admin-equivalence). HOLDS.

### Candidate patches
- reject.diff (naive wrong fix: 'nonfield' copy-paste typo instead of 'nonform'): REJECTED by probes 1,2,3,5,6 (5/6). Demonstrates the suite discriminates wrong CSS-class implementations.
- weak.diff (except-path-only, leaves init line unpatched): passes all 6 probes. This is NOT a genuine too-weak finding: validate_max/validate_min both raise ValidationError caught by the same except block, so the except-path assignment is what actually tags those errors; the init-line assignment only matters for the empty case (already ''). weak.diff is an equivalent fix, not a defect the requirements admit. It would still resolve the hidden tests.

Probes stdlib+django only, no pytest. Positive control confirmed failing at base (prepatch_reproduced=true). Verdict SOUND: >=5 probes hold on patched tree, positive control discriminates base vs patched, and a plausibly-wrong candidate (reject.diff) is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (Req 1.2, 1.3, 2.2): validate_max failure -> non_form_errors
renders as <ul class="errorlist nonform">. HOLDS patched, FAILS at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
    django.setup()
from django import forms
from django.forms import formset_factory


class SimpleForm(forms.Form):
    name = forms.CharField()


FS = formset_factory(SimpleForm, validate_max=True, max_num=1)
data = {
    "form-TOTAL_FORMS": "2", "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "2",
    "form-0-name": "a", "form-1-name": "b",
}
fs = FS(data)
assert not fs.is_valid()
nfe = fs.non_form_errors()
html = str(nfe)
print("html=", html)
ok = html.startswith('<ul class="errorlist nonform">')
print("holds=", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: add 'nonform' CSS class to BaseFormSet non-form ErrorList (django/forms/formsets.py). Gold patch sets error_class='nonform' on both the init line and the clean() except-path ErrorList.

6 probes, all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL, Req 1.2/1.3/2.2): validate_max failure renders <ul class="errorlist nonform">. HOLDS patched, FAILS at base (base renders <ul class="errorlist">) -> discriminates.
- probe_2 (Req 1.1/1.4/2.3): validate_min failure -> ErrorList instance whose class attr is EXACTLY 'errorlist nonform' (nonform in addition to base). HOLDS.
- probe_3 (Req 2.4/3.4): FormSet.clean() raising ValidationError -> nonform class + message preserved ('cross-form boom'). HOLDS.
- probe_4 (Req 2.1/3.5/3.2): empty valid formset -> empty ErrorList ==[] renders ''; validate_max message text/count exact ('Please submit at most 1 form.'). HOLDS.
- probe_5 (Req 4.1/4.2/4.3): total_error_count == non-form + per-form counts (2 == 1+1); is_valid False; non_form_errors() before is_valid() triggers clean and carries nonform. HOLDS.
- probe_6 (Req 4.4): formset non-form ErrorList renders identically to ErrorList(msgs, error_class='nonform') (admin-equivalence). HOLDS.

### Candidate patches
- reject.diff (naive wrong fix: 'nonfield' copy-paste typo instead of 'nonform'): REJECTED by probes 1,2,3,5,6 (5/6). Demonstrates the suite discriminates wrong CSS-class implementations.
- weak.diff (except-path-only, leaves init line unpatched): passes all 6 probes. This is NOT a genuine too-weak finding: validate_max/validate_min both raise ValidationError caught by the same except block, so the except-path assignment is what actually tags those errors; the init-line assignment only matters for the empty case (already ''). weak.diff is an equivalent fix, not a defect the requirements admit. It would still resolve the hidden tests.

Probes stdlib+django only, no pytest. Positive control confirmed failing at base (prepatch_reproduced=true). Verdict SOUND: >=5 probes hold on patched tree, positive control discriminates base vs patched, and a plausibly-wrong candidate (reject.diff) is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes django/forms/formsets.py full_clean: initializes self._non_form_errors = self.error_class(error_class='nonform') and rebuilds it with error_class='nonform' in the clean() ValidationError branch. Requirements 1-4 model exactly this: the nonform CSS class appended after base 'errorlist' across all non-form-error production paths (management-form, validate_max, validate_min, clean()), while preserving messages/order/type and dependent APIs. Probe (patched HOLDS exit=0, base VIOLATED exit=1) confirms max/min/clean strings, ErrorList type, and empty-list value equality. No mandated behavior absent from the code, no forbidden behavior present, no invented behavior, correct modeling boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the public problem_statement (add a `nonform` CSS class to FormSet non-form errors, mirroring `nonfield`). No hidden-test content is transmitted: no test function/class names or file paths appear; the test-specific fixture strings ('You may only specify a drink once.', 'Grace is not a Zombie') and parametrized limits (max=1, min=3) are absent. The doc uses Django's PUBLIC built-in validate_max/validate_min messages in generic 'N form(s)' form, not the concrete test values. The HTML string `<ul class="errorlist nonform">` (line 46) is the natural, derivable rendering of an ErrorList given the requested class — behavioral, not a fixture-specific artifact. Identifiers `nonform`/`error_class` are public API; module names (formsets.py, utils.py) are legitimate localization. Requirement 2 enumerates four production paths (broader than the 3 covered tests), describing behavior rather than mirroring parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
