# P2 adversarial audit — django__django-14631

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.2 + 1.4 (POSITIVE CONTROL): disabled DateTimeField w/ callable microsecond
# initial -> cleaned_data equals form[name].initial and microseconds stripped
import sys, datetime
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

val = datetime.datetime(2021, 1, 1, 10, 30, 15, 123456)
class F(forms.Form):
    dt = forms.DateTimeField(initial=lambda: val, disabled=True)

form = F({})  # bound, no submitted data for dt
if not form.is_valid():
    print("form invalid", form.errors); sys.exit(1)
cd = form.cleaned_data['dt']
bfi = form['dt'].initial
print("cleaned=", cd, "microsecond=", cd.microsecond, "bf.initial=", bfi)
ok = (cd == bfi) and (cd.microsecond == 0)
print("ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.3: callable initial evaluated only ONCE; cleaned value reflects the same
# single evaluation form[name].initial reflects. Vary the SECONDS component per
# call so a re-evaluation is detectable even when microseconds get normalized.
import sys, datetime
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

counter = {'n': 0}
def cb():
    counter['n'] += 1
    return datetime.datetime(2021, 1, 1, 10, 30, counter['n'], 123456)

class F(forms.Form):
    dt = forms.DateTimeField(initial=cb, disabled=True)

form = F({})
if not form.is_valid():
    print("form invalid", form.errors); sys.exit(1)
cd = form.cleaned_data['dt']
bfi1 = form['dt'].initial
bfi2 = form['dt'].initial  # cached -> same value
print("cleaned=", cd, "bf.initial(1)=", bfi1, "bf.initial(2)=", bfi2, "callcount=", counter['n'])
ok = (cd == bfi1) and (bfi1 == bfi2)
print("ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1: editable field cleaned from its submitted data (form[name].data)
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

class F(forms.Form):
    name = forms.CharField()

form = F({'name': 'hello'})
if not form.is_valid():
    print("invalid", form.errors); sys.exit(1)
ok = form.cleaned_data['name'] == 'hello' and form['name'].data == 'hello'
print("cleaned=", form.cleaned_data['name'], "bf.data=", form['name'].data, "ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.3: cleaning error -> error recorded, NO cleaned_data entry for that field;
# other fields still cleaned. Req 2.4: one entry per successfully cleaned field.
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

class F(forms.Form):
    a = forms.CharField()            # required, will be missing
    b = forms.CharField(required=False)

form = F({'b': 'x'})
valid = form.is_valid()
ok = (not valid) and ('a' in form.errors) and ('a' not in form.cleaned_data) \
     and form.cleaned_data.get('b') == 'x'
print("errors=", dict(form.errors), "cleaned=", form.cleaned_data, "ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2/4.6: changed_data uses BoundField initial; has_changed iff non-empty
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

class F(forms.Form):
    x = forms.CharField(initial='orig')
    y = forms.CharField(initial='keep')

same = F({'x': 'orig', 'y': 'keep'})
chg  = F({'x': 'new',  'y': 'keep'})
ok = (same.changed_data == [] and same.has_changed() is False
      and chg.changed_data == ['x'] and chg.has_changed() is True)
print("same.changed=", same.changed_data, "chg.changed=", chg.changed_data, "ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 4.3/4.4: hidden-initial input; conversion failure -> treated as changed
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

class F(forms.Form):
    n = forms.IntegerField(show_hidden_initial=True)

# hidden initial 'notanint' cannot convert -> field must be reported changed
form = F({'n': '5', 'initial-n': 'notanint'})
ok = 'n' in form.changed_data
print("changed_data=", form.changed_data, "ok=", ok)

# valid hidden initial equal to submitted -> not changed
form2 = F({'n': '5', 'initial-n': '5'})
ok2 = 'n' not in form2.changed_data
print("changed_data2=", form2.changed_data, "ok2=", ok2)
sys.exit(0 if (ok and ok2) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 1.5: disabled temporal field whose widget SUPPORTS sub-second precision
# retains microseconds in cleaned_data, equal to form[name].initial
import sys, datetime
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

class MicroInput(forms.DateTimeInput):
    supports_microseconds = True

val = datetime.datetime(2021, 1, 1, 1, 1, 1, 500000)
class F(forms.Form):
    dt = forms.DateTimeField(initial=lambda: val, disabled=True, widget=MicroInput)

form = F({})
if not form.is_valid():
    print("invalid", form.errors); sys.exit(1)
cd = form.cleaned_data['dt']
bfi = form['dt'].initial
ok = cd.microsecond == 500000 and cd == bfi
print("cleaned=", cd, "microsecond=", cd.microsecond, "bf.initial=", bfi, "ok=", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.2 + 1.4 (POSITIVE CONTROL): disabled DateTimeField w/ callable microsecond
# initial -> cleaned_data equals form[name].initial and microseconds stripped
import sys, datetime
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

val = datetime.datetime(2021, 1, 1, 10, 30, 15, 123456)
class F(forms.Form):
    dt = forms.DateTimeField(initial=lambda: val, disabled=True)

form = F({})  # bound, no submitted data for dt
if not form.is_valid():
    print("form invalid", form.errors); sys.exit(1)
cd = form.cleaned_data['dt']
bfi = form['dt'].initial
print("cleaned=", cd, "microsecond=", cd.microsecond, "bf.initial=", bfi)
ok = (cd == bfi) and (cd.microsecond == 0)
print("ok=", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering Req1.2/1.4 (disabled DateTimeField w/ callable microsecond initial -> cleaned_data == form[name].initial, microseconds stripped), Req1.3 (callable evaluated exactly once, cleaned value == cached BoundField.initial), Req2.1 (editable field cleaned from form[name].data), Req2.3/2.4 (validation error -> no cleaned_data entry, other fields still cleaned in order), Req4.1/4.2/4.6 (changed_data via BoundField initial; has_changed iff non-empty), Req4.3/4.4 (hidden-initial conversion failure -> treated as changed; equal -> not changed), Req1.5 (microsecond-supporting widget retains sub-second). ALL 7 HOLD on gold-patched tree.

Positive control probe_1 FAILS at base (cleaned=...123456 microsecond=123456 vs bf.initial stripped) and HOLDS patched -> discriminates. probe_2 also fails at base (double callable eval, callcount=2).

WEAK candidate (weak.diff): applies naive microsecond-stripping to get_initial_for_field result but still RE-EVALUATES the callable rather than routing through cached BoundField.initial. It passes probes 1,3,4,5,6,7 but is REJECTED by probe_2 (callcount=2, cleaned != cached initial) -> Req1.3 discriminates the wrong fix. This demonstrates the suite catches the lazy partial fix, so no requirements-conforming wrong patch was found.

Env: python via miniconda swebench-lean; runs on official django__django-14631 image.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.2 + 1.4 (POSITIVE CONTROL): disabled DateTimeField w/ callable microsecond
# initial -> cleaned_data equals form[name].initial and microseconds stripped
import sys, datetime
import django
from django.conf import settings
settings.configure(DEBUG=True, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django import forms

val = datetime.datetime(2021, 1, 1, 10, 30, 15, 123456)
class F(forms.Form):
    dt = forms.DateTimeField(initial=lambda: val, disabled=True)

form = F({})  # bound, no submitted data for dt
if not form.is_valid():
    print("form invalid", form.errors); sys.exit(1)
cd = form.cleaned_data['dt']
bfi = form['dt'].initial
print("cleaned=", cd, "microsecond=", cd.microsecond, "bf.initial=", bfi)
ok = (cd == bfi) and (cd.microsecond == 0)
print("ok=", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering Req1.2/1.4 (disabled DateTimeField w/ callable microsecond initial -> cleaned_data == form[name].initial, microseconds stripped), Req1.3 (callable evaluated exactly once, cleaned value == cached BoundField.initial), Req2.1 (editable field cleaned from form[name].data), Req2.3/2.4 (validation error -> no cleaned_data entry, other fields still cleaned in order), Req4.1/4.2/4.6 (changed_data via BoundField initial; has_changed iff non-empty), Req4.3/4.4 (hidden-initial conversion failure -> treated as changed; equal -> not changed), Req1.5 (microsecond-supporting widget retains sub-second). ALL 7 HOLD on gold-patched tree.

Positive control probe_1 FAILS at base (cleaned=...123456 microsecond=123456 vs bf.initial stripped) and HOLDS patched -> discriminates. probe_2 also fails at base (double callable eval, callcount=2).

WEAK candidate (weak.diff): applies naive microsecond-stripping to get_initial_for_field result but still RE-EVALUATES the callable rather than routing through cached BoundField.initial. It passes probes 1,3,4,5,6,7 but is REJECTED by probe_2 (callcount=2, cleaned != cached initial) -> Req1.3 discriminates the wrong fix. This demonstrates the suite catches the lazy partial fix, so no requirements-conforming wrong patch was found.

Env: python via miniconda swebench-lean; runs on official django__django-14631 image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch moves per-field access in _clean_fields and changed_data through BoundField (bf.data / bf.initial) and introduces BoundField._has_changed. Requirements accurately pin the CHANGED OBSERVABLE behavior (disabled-field cleaned value == bf.initial incl. single callable eval + microsecond normalization; changed_data via bf) rather than a narrow slice. Boundary is correct and biconditional (Req4.6). All claims machine-verified via nl_attack probe on the patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior and localizes the change to pre-existing/public symbols (BaseForm._clean_fields, changed_data, _html_output, BoundField.initial/.data) — all named or implied by the public problem_statement (which itself already cites _bound_items(), bf._did_change(), the _clean_fields vs form[name].initial disagreement, callable-initial+disabled scenario, and test_datetime_clean_initial_callable_disabled). No hidden-test artifacts appear: no FakeTime helper, no elapsed_seconds counter, no concrete datetime literals (2006-10-25 14:30:46 / microseconds=123456), no test names/paths, no parametrization ids, no quoted test or gold code, and no fix-invented identifiers (the gold's _widget_data_value/_has_changed are not surfaced; _bound_items/_did_change are already public via the problem statement). The single-evaluation (Req 1.3) and microsecond-normalization (Req 1.4/1.5) requirements are behavioral consequences of BoundField.initial's cached_property + sub-second normalization, stated generally (Req 1.5 even covers the widget-can-represent case the tests never exercise) rather than as a case-list mirroring the two FAIL_TO_PASS tests. This is legitimate behavioral translation, not test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
