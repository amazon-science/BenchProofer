# P2 adversarial audit — django__django-14034

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak patch (suppresses parent 'required' for partial-multi but never sets per-subwidget required) is REJECTED by probe_1: rendered mv_0 subwidget lacks the required attribute though its subfield is required=True.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req1 AC2+AC3: partially-required MVF renders per-subwidget
required markers. subfield0 required -> its subwidget carries required;
subfield1 optional -> its subwidget does NOT. Parent widget must NOT get required.
Holds on patched, fails at base (base puts required on parent only)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVF(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=False))
        super().__init__(fields=fields, require_all_fields=False, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


class F(forms.Form):
    mv = MVF(required=True)


html = str(F()['mv'])
print("RENDER:", html)
# count required= occurrences in the two subwidgets
# subwidget0 (name mv_0) should be required, subwidget1 (mv_1) should not.
import re
# split by name attr
ok = True
# find the input for mv_0
m0 = re.search(r'<input[^>]*name="mv_0"[^>]*>', html)
m1 = re.search(r'<input[^>]*name="mv_1"[^>]*>', html)
if not m0 or not m1:
    print("FAIL: could not find both subwidgets")
    sys.exit(1)
sub0, sub1 = m0.group(0), m1.group(0)
print("sub0:", sub0)
print("sub1:", sub1)
if 'required' not in sub0:
    print("FAIL: required subfield subwidget missing required attr")
    ok = False
if 'required' in sub1:
    print("FAIL: optional subfield subwidget wrongly has required attr")
    ok = False
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1 AC1: when guard holds and partial-multi condition holds,
build_widget_attrs SHALL NOT add 'required' to the parent attrs mapping."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVF(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=False))
        super().__init__(fields=fields, require_all_fields=False, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


class F(forms.Form):
    mv = MVF(required=True)


bf = F()['mv']
attrs = bf.build_widget_attrs({})
print("parent attrs:", attrs)
if 'required' in attrs:
    print("FAIL: parent attrs must not contain 'required' for partial-multi")
    sys.exit(1)
print("OK: parent has no required marker")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2 AC1+AC3: ordinary field (non-MultiWidget) with guard holding SHALL get
'required' True on parent attrs. Also Req2 AC4: MVF with require_all_fields=True
takes ordinary single-marker placement (parent gets required)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVFall(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=True))
        super().__init__(fields=fields, require_all_fields=True, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


class F(forms.Form):
    plain = forms.CharField(required=True)
    mvall = MVFall(required=True)


ok = True
attrs_plain = F()['plain'].build_widget_attrs({})
print("plain attrs:", attrs_plain)
if attrs_plain.get('required') is not True:
    print("FAIL: ordinary field must get required=True on parent")
    ok = False

attrs_all = F()['mvall'].build_widget_attrs({})
print("mvall (require_all_fields=True) attrs:", attrs_all)
if attrs_all.get('required') is not True:
    print("FAIL: MVF with require_all_fields=True must get required=True on parent")
    ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2 AC2: if guard does NOT hold (form.use_required_attribute False), no
'required' added to parent AND no subwidget required set. Also Req3 AC1: attrs
copied not mutated. Req3 AC2/AC3: disabled marker handling."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVF(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=False))
        super().__init__(fields=fields, require_all_fields=False, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


# form that disables required attribute entirely
class F(forms.Form):
    use_required_attribute = False
    mv = MVF(required=True)


ok = True
bf = F()['mv']
# reset subwidget attrs to known state
for w in bf.field.widget.widgets:
    w.attrs.pop('required', None)
incoming = {'class': 'x'}
attrs = bf.build_widget_attrs(incoming)
print("attrs when guard fails:", attrs)
if 'required' in attrs:
    print("FAIL: no required on parent when guard fails")
    ok = False
for i, w in enumerate(bf.field.widget.widgets):
    if 'required' in w.attrs:
        print("FAIL: subwidget", i, "required set though guard fails:", w.attrs)
        ok = False
# Req3 AC1: incoming not mutated
if incoming != {'class': 'x'}:
    print("FAIL: incoming attrs mutated:", incoming)
    ok = False
# Req3 AC4: incoming entry preserved
if attrs.get('class') != 'x':
    print("FAIL: incoming 'class' entry not preserved")
    ok = False
print("incoming after:", incoming, "returned class:", attrs.get('class'))
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3 AC2/AC3/AC5: disabled marker independent of required decision.
A disabled partial-multi field: parent gets disabled=True, and parent must NOT
get required (partial-multi). A non-disabled field: no disabled marker."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVF(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=False))
        super().__init__(fields=fields, require_all_fields=False, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


class F(forms.Form):
    mv_dis = MVF(required=True, disabled=True)
    mv_nodis = MVF(required=True)


ok = True
a_dis = F()['mv_dis'].build_widget_attrs({})
print("disabled partial-multi attrs:", a_dis)
if a_dis.get('disabled') is not True:
    print("FAIL: disabled field must add disabled=True")
    ok = False
if 'required' in a_dis:
    print("FAIL: partial-multi must not add required to parent even when disabled")
    ok = False

a_nodis = F()['mv_nodis'].build_widget_attrs({})
print("non-disabled attrs:", a_nodis)
if 'disabled' in a_nodis:
    print("FAIL: non-disabled field must not add disabled marker")
    ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4 AC1/AC2: validation depends on individual subfields for a required MVF
with require_all_fields=False. Required subfield filled + optional blank -> valid.
Required subfield blank -> invalid. This is the 'SHALL keep' regression."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVF(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=False))
        super().__init__(fields=fields, require_all_fields=False, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


class F(forms.Form):
    mv = MVF(required=True)


ok = True
# required subfield (mv_0) filled, optional (mv_1) blank -> valid
f1 = F(data={'mv_0': 'hello', 'mv_1': ''})
print("required filled, optional blank -> is_valid:", f1.is_valid(), f1.errors)
if not f1.is_valid():
    print("FAIL: should be valid when required subfield filled, optional blank")
    ok = False

# required subfield blank -> invalid
f2 = F(data={'mv_0': '', 'mv_1': 'world'})
print("required blank -> is_valid:", f2.is_valid(), f2.errors)
if f2.is_valid():
    print("FAIL: should be invalid when required subfield blank")
    ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1 AC2+AC3: partially-required MVF renders per-subwidget
required markers. subfield0 required -> its subwidget carries required;
subfield1 optional -> its subwidget does NOT. Parent widget must NOT get required.
Holds on patched, fails at base (base puts required on parent only)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVF(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=False))
        super().__init__(fields=fields, require_all_fields=False, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


class F(forms.Form):
    mv = MVF(required=True)


html = str(F()['mv'])
print("RENDER:", html)
# count required= occurrences in the two subwidgets
# subwidget0 (name mv_0) should be required, subwidget1 (mv_1) should not.
import re
# split by name attr
ok = True
# find the input for mv_0
m0 = re.search(r'<input[^>]*name="mv_0"[^>]*>', html)
m1 = re.search(r'<input[^>]*name="mv_1"[^>]*>', html)
if not m0 or not m1:
    print("FAIL: could not find both subwidgets")
    sys.exit(1)
sub0, sub1 = m0.group(0), m1.group(0)
print("sub0:", sub0)
print("sub1:", sub1)
if 'required' not in sub0:
    print("FAIL: required subfield subwidget missing required attr")
    ok = False
if 'required' in sub1:
    print("FAIL: optional subfield subwidget wrongly has required attr")
    ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-14034: build_widget_attrs must place per-subwidget required markers for a require_all_fields=False MultiValueField over a MultiWidget, while keeping single-marker placement for ordinary/require_all_fields=True fields and preserving disabled/copy/validation behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1 AC2/AC3, positive control): required subfield's subwidget carries HTML required, optional subfield's does not. HOLDS patched, FAILS at base (base marks BOTH subwidgets required). prepatch reproduced.
- probe_2 (Req1 AC1): parent attrs mapping gets no 'required' for partial-multi. HOLDS patched, FAILS at base (parent got required=True).
- probe_3 (Req2 AC1/AC3/AC4): ordinary CharField and require_all_fields=True MVF both get required=True on parent.
- probe_4 (Req2 AC2 + Req3 AC1/AC4): guard-fails (form.use_required_attribute=False) => no parent required, no subwidget required set, incoming attrs not mutated, incoming 'class' preserved.
- probe_5 (Req3 AC2/AC3/AC5): disabled partial-multi field gets disabled=True and still no parent required; non-disabled gets no disabled marker.
- probe_6 (Req4 AC1/AC2, regression): validation depends on subfields — required filled + optional blank => valid; required blank => invalid.

Candidate patches exercised: weak.diff (partial fix, suppresses parent marker but omits per-subwidget assignment) applies cleanly at base and is REJECTED by probe_1 (required subwidget missing required attr) while passing probes 2/3/6 — demonstrating the suite discriminates a wrong implementation. No requirements-conforming-yet-wrong patch found.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates (patched pass / base fail), and >=1 candidate patch is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak patch (suppresses parent 'required' for partial-multi but never sets per-subwidget required) is REJECTED by probe_1: rendered mv_0 subwidget lacks the required attribute though its subfield is required=True.
```

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
"""Positive control / Req1 AC2+AC3: partially-required MVF renders per-subwidget
required markers. subfield0 required -> its subwidget carries required;
subfield1 optional -> its subwidget does NOT. Parent widget must NOT get required.
Holds on patched, fails at base (base puts required on parent only)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, USE_TZ=False, DATABASES={},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()
from django import forms
from django.forms.widgets import MultiWidget, TextInput


class MW(MultiWidget):
    def __init__(self, attrs=None):
        super().__init__([TextInput(), TextInput()], attrs)
    def decompress(self, value):
        return value.split(',') if value else [None, None]


class MVF(forms.MultiValueField):
    def __init__(self, **kw):
        fields = (forms.CharField(required=True), forms.CharField(required=False))
        super().__init__(fields=fields, require_all_fields=False, widget=MW(), **kw)
    def compress(self, dl):
        return ','.join(str(x) for x in dl) if dl else ''


class F(forms.Form):
    mv = MVF(required=True)


html = str(F()['mv'])
print("RENDER:", html)
# count required= occurrences in the two subwidgets
# subwidget0 (name mv_0) should be required, subwidget1 (mv_1) should not.
import re
# split by name attr
ok = True
# find the input for mv_0
m0 = re.search(r'<input[^>]*name="mv_0"[^>]*>', html)
m1 = re.search(r'<input[^>]*name="mv_1"[^>]*>', html)
if not m0 or not m1:
    print("FAIL: could not find both subwidgets")
    sys.exit(1)
sub0, sub1 = m0.group(0), m1.group(0)
print("sub0:", sub0)
print("sub1:", sub1)
if 'required' not in sub0:
    print("FAIL: required subfield subwidget missing required attr")
    ok = False
if 'required' in sub1:
    print("FAIL: optional subfield subwidget wrongly has required attr")
    ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-14034: build_widget_attrs must place per-subwidget required markers for a require_all_fields=False MultiValueField over a MultiWidget, while keeping single-marker placement for ordinary/require_all_fields=True fields and preserving disabled/copy/validation behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1 AC2/AC3, positive control): required subfield's subwidget carries HTML required, optional subfield's does not. HOLDS patched, FAILS at base (base marks BOTH subwidgets required). prepatch reproduced.
- probe_2 (Req1 AC1): parent attrs mapping gets no 'required' for partial-multi. HOLDS patched, FAILS at base (parent got required=True).
- probe_3 (Req2 AC1/AC3/AC4): ordinary CharField and require_all_fields=True MVF both get required=True on parent.
- probe_4 (Req2 AC2 + Req3 AC1/AC4): guard-fails (form.use_required_attribute=False) => no parent required, no subwidget required set, incoming attrs not mutated, incoming 'class' preserved.
- probe_5 (Req3 AC2/AC3/AC5): disabled partial-multi field gets disabled=True and still no parent required; non-disabled gets no disabled marker.
- probe_6 (Req4 AC1/AC2, regression): validation depends on subfields — required filled + optional blank => valid; required blank => invalid.

Candidate patches exercised: weak.diff (partial fix, suppresses parent marker but omits per-subwidget assignment) applies cleanly at base and is REJECTED by probe_1 (required subwidget missing required attr) while passing probes 2/3/6 — demonstrating the suite discriminates a wrong implementation. No requirements-conforming-yet-wrong patch found.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates (patched pass / base fail), and >=1 candidate patch is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds, inside the existing guard (use_required_attribute(initial) and field.required and form.use_required_attribute), a branch: if hasattr(field,'require_all_fields') and not field.require_all_fields and isinstance(field.widget, MultiWidget), it iterates zip(self.field.fields, widget.widgets) setting subwidget.attrs['required']=subwidget.use_required_attribute(self.initial) and subfield.required (and skips setting parent attrs['required']); else attrs['required']=True. Requirements map exactly: Req1.1 (no parent marker), Req1.2 (aligned zip, per-subwidget biconditional on subwidget.use_required_attribute AND subfield.required), Req1.3/1.4 (rendered per-subwidget, one-to-one order) — all confirmed by probe. Req2 preserves single-marker for non-partial/non-MultiWidget/require_all_fields=True and no-op when guard fails (subwidget mutation is only inside the guard). Req3 (attrs=dict(attrs) copy, disabled handling unchanged, independent of required) and Req4 (validation unchanged — patch is render-only) hold. Boundary is correct: requirements pin the changed observable behavior (per-subwidget required placement), not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally and localizes it to public Django API only. No hidden-test artifacts appear: the test name (test_render_required_attributes), file path (tests/forms_tests/field_tests/test_multivaluefield.py), test-invented classes (PartiallyRequiredField/PartiallyRequiredForm), field ids (f_0/f_1/id_f_0), and the assertInHTML markup strings are all absent. All named identifiers — build_widget_attrs, require_all_fields, use_required_attribute, MultiWidget, MultiValueField, CharField — are pre-existing public API (require_all_fields, MultiValueField, MultiWidget, CharField and the is_valid true/false behavior all appear in the public problem_statement). The patch invents no new identifiers, so nothing fix-specific can be leaked. The closest call is Req 1 criterion 2, which states the required decision equals 'subwidget.use_required_attribute(self.initial) AND subfield.required' — this mirrors the gold's substantive line, but it is behavioral prose over public method names describing intended behavior (the whole point of the spec), not quoted test/gold code and not the hidden tests. Req 4.1/4.2 restate the problem_statement's own is_valid examples. No case enumeration mirrors the test parametrization; the doc gives general per-subwidget behavior, not the Hello/blank case.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
