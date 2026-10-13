# P2 adversarial audit — django__django-16667

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req1.1+1.2+1.3: oversized component -> no exception, returns "0-0-0"."""
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
import django; django.setup()
from django.forms.widgets import SelectDateWidget

w = SelectDateWidget()
name = "mydate"
big = "999999999999999999999"  # syntactically valid int, overflows C date
data = {"%s_year" % name: big, "%s_month" % name: "1", "%s_day" % name: "1"}
try:
    v = w.value_from_datadict(data, {}, name)
except Exception as e:
    print("FAIL: exception propagated:", type(e).__name__, e)
    sys.exit(1)
print("returned:", repr(v))
# Req1.2/1.3: all three collapse to 0 placeholder, no raw text carried through
if v != "0-0-0":
    print("FAIL: expected '0-0-0'")
    sys.exit(1)
if big in str(v):
    print("FAIL: raw oversized text present")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1: DateField cleaning the "0-0-0" sentinel raises 'Enter a valid date.'"""
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
import django; django.setup()
from django.forms import DateField
from django.core.exceptions import ValidationError

f = DateField()
try:
    f.clean("0-0-0")
    print("FAIL: no ValidationError")
    sys.exit(1)
except ValidationError as e:
    msgs = e.messages
    print("messages:", msgs)
    if msgs == ["Enter a valid date."]:
        print("PASS")
        sys.exit(0)
    print("FAIL: unexpected messages")
    sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.2+2.3: Form with DateField+SelectDateWidget, oversized input -> is_valid False, single 'Enter a valid date.'"""
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
import django; django.setup()
from django import forms
from django.forms.widgets import SelectDateWidget

class F(forms.Form):
    d = forms.DateField(widget=SelectDateWidget())

data = {"d_year": "1234567821345678", "d_month": "1", "d_day": "1"}
form = F(data)
valid = form.is_valid()
print("is_valid:", valid)
if valid:
    print("FAIL: form should be invalid")
    sys.exit(1)
errs = list(form.errors.get("d", []))
print("errors[d]:", errs)
if errs != ["Enter a valid date."]:
    print("FAIL: expected exactly single 'Enter a valid date.'")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1+3.2+3.3: regression - empty->None; missing component->fallback data.get(name); valid date->formatted."""
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
import django; django.setup()
from django.forms.widgets import SelectDateWidget

w = SelectDateWidget()
name = "d"
ok = True

# 3.1 all empty -> None
v = w.value_from_datadict({"d_year":"", "d_month":"", "d_day":""}, {}, name)
print("all-empty:", repr(v))
if v is not None:
    print("FAIL 3.1"); ok = False

# 3.2 a component absent -> fallback to data.get(name)
v = w.value_from_datadict({"d_year":"2017", "d_month":"3", "d": "FALLBACK"}, {}, name)  # day absent
print("missing-day fallback:", repr(v))
if v != "FALLBACK":
    print("FAIL 3.2"); ok = False

# 3.3 valid date -> rendered in first DATE_INPUT_FORMAT
v = w.value_from_datadict({"d_year":"2017","d_month":"3","d_day":"23"}, {}, name)
print("valid date:", repr(v))
# default first DATE_INPUT_FORMAT is %Y-%m-%d
if v != "2017-03-23":
    print("FAIL 3.3"); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.4: well-formed but non-representable (no overflow) -> pseudo-ISO '<y>-<m>-<d>' with 0 for empties.
Must NOT be collapsed to '0-0-0'. Distinguishes overflow-handling from ordinary ValueError path."""
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
import django; django.setup()
from django.forms.widgets import SelectDateWidget

w = SelectDateWidget()
name = "d"
ok = True

# impossible month=0 -> ValueError branch -> "2017-0-23"
v = w.value_from_datadict({"d_year":"2017","d_month":"0","d_day":"23"}, {}, name)
print("month0:", repr(v))
if v != "2017-0-23":
    print("FAIL: expected 2017-0-23"); ok = False

# impossible day 31 in Feb -> ValueError -> keep raw components
v = w.value_from_datadict({"d_year":"2017","d_month":"2","d_day":"31"}, {}, name)
print("feb31:", repr(v))
if v != "2017-2-31":
    print("FAIL: expected 2017-2-31"); ok = False

# non-numeric text -> ValueError -> raw carried
v = w.value_from_datadict({"d_year":"abc","d_month":"2","d_day":"3"}, {}, name)
print("nonnum:", repr(v))
if v != "abc-2-3":
    print("FAIL: expected abc-2-3"); ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1+1.2+1.3: oversized component -> no exception, returns "0-0-0"."""
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
import django; django.setup()
from django.forms.widgets import SelectDateWidget

w = SelectDateWidget()
name = "mydate"
big = "999999999999999999999"  # syntactically valid int, overflows C date
data = {"%s_year" % name: big, "%s_month" % name: "1", "%s_day" % name: "1"}
try:
    v = w.value_from_datadict(data, {}, name)
except Exception as e:
    print("FAIL: exception propagated:", type(e).__name__, e)
    sys.exit(1)
print("returned:", repr(v))
# Req1.2/1.3: all three collapse to 0 placeholder, no raw text carried through
if v != "0-0-0":
    print("FAIL: expected '0-0-0'")
    sys.exit(1)
if big in str(v):
    print("FAIL: raw oversized text present")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

SelectDateWidget.value_from_datadict oversized-numeric-component overflow fix (django-16667). 5 probes cover: p1 Req1.1/1.2/1.3 (no exception + collapse to '0-0-0', no raw text); p2 Req2.1 (DateField.clean('0-0-0') -> 'Enter a valid date.'); p3 Req2.2/2.3 (Form is_valid False, exactly single error); p4 Req3.1/3.2/3.3 (empty->None, missing component->data.get(name) fallback, valid date->'%Y-%m-%d'); p5 Req3.4 (well-formed non-representable/non-overflow -> raw pseudo-ISO '2017-0-23','2017-2-31','abc-2-3', NOT collapsed). All 5 HOLD on gold-patched tree. Positive control p1 discriminates: FAILS at base with unhandled OverflowError, HOLDS patched. Candidate weak patch (catches OverflowError but returns raw pseudo-ISO '%s-%s-%s' instead of '0-0-0') is REJECTED by p1 (returned '999999999999999999999-1-1', carries raw oversized text, violates Req1.2/1.3) while passing p2-p5 -> suite discriminates the lazy fix. Verdict SOUND: requirements are faithful (gold satisfies all probes) and the suite rejects the requirements-plausible weak alternative.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.1+1.2+1.3: oversized component -> no exception, returns "0-0-0"."""
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(USE_I18N=True, INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
import django; django.setup()
from django.forms.widgets import SelectDateWidget

w = SelectDateWidget()
name = "mydate"
big = "999999999999999999999"  # syntactically valid int, overflows C date
data = {"%s_year" % name: big, "%s_month" % name: "1", "%s_day" % name: "1"}
try:
    v = w.value_from_datadict(data, {}, name)
except Exception as e:
    print("FAIL: exception propagated:", type(e).__name__, e)
    sys.exit(1)
print("returned:", repr(v))
# Req1.2/1.3: all three collapse to 0 placeholder, no raw text carried through
if v != "0-0-0":
    print("FAIL: expected '0-0-0'")
    sys.exit(1)
if big in str(v):
    print("FAIL: raw oversized text present")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

SelectDateWidget.value_from_datadict oversized-numeric-component overflow fix (django-16667). 5 probes cover: p1 Req1.1/1.2/1.3 (no exception + collapse to '0-0-0', no raw text); p2 Req2.1 (DateField.clean('0-0-0') -> 'Enter a valid date.'); p3 Req2.2/2.3 (Form is_valid False, exactly single error); p4 Req3.1/3.2/3.3 (empty->None, missing component->data.get(name) fallback, valid date->'%Y-%m-%d'); p5 Req3.4 (well-formed non-representable/non-overflow -> raw pseudo-ISO '2017-0-23','2017-2-31','abc-2-3', NOT collapsed). All 5 HOLD on gold-patched tree. Positive control p1 discriminates: FAILS at base with unhandled OverflowError, HOLDS patched. Candidate weak patch (catches OverflowError but returns raw pseudo-ISO '%s-%s-%s' instead of '0-0-0') is REJECTED by p1 (returned '999999999999999999999-1-1', carries raw oversized text, violates Req1.2/1.3) while passing p2-p5 -> suite discriminates the lazy fix. Verdict SOUND: requirements are faithful (gold satisfies all probes) and the suite rejects the requirements-plausible weak alternative.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is `except OverflowError: return "0-0-0"`. Requirements pin the full observable behavior of value_from_datadict across all branches (overflow, ValueError/pseudo-ISO, empty, missing, valid) plus downstream DateField/Form — the correct changed-behavior boundary, not a narrow slice. All assertions in probe.py passed on patched tree; base violated (OverflowError propagates).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes only public/behavioral content. Module and method (SelectDateWidget.value_from_datadict, django/forms/widgets.py), the OverflowError crash, and sys.maxsize are all in the public problem_statement. The '0' placeholder / pseudo-ISO representation and the '2017-0-23' example (Req 3.4) come from the pre-existing public source comment in value_from_datadict, not the hidden test. The all-zeros sentinel behavior (gold returns '0-0-0') is described as a behavioral translation derived from that public zeros representation, which is the legitimate purpose of the spec. 'Enter a valid date.' is Django's generic public DateField message. No test file paths, test function/class names, parametrization ids/tuples ((str(sys.maxsize+1),'12','1'),'0-0-0'), quoted test/gold code, or fix-invented identifiers appear. Req 3.6's feature enumeration reflects the widget's existing rendering surface (regression protection), not the hidden parametrization. Nothing reconstructs the hidden tests beyond describing behavior.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
