# P2 adversarial audit — django__django-11433

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
weak.diff replaces the `cleaned_data.get(f.name) in field.empty_values` guard with `not cleaned_data.get(f.name)` (general falsiness). It passes probes 1-5 but is REJECTED by probe_6: a cleaned_data value of 0 (falsy, but NOT a member of EMPTY_VALUES={None,'',[],(),{}}) is wrongly treated as empty and the field is left at its model default (7) instead of being overridden to 0. On the gold-patched tree probe_6 correctly yields 0.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1 (positive control): a non-empty cleaned_data value for a field that
has a model default and was omitted from submitted data overrides the default.
Holds on patched, FAILS on base."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    USE_TZ=True,
)
import sys, types
mod = types.ModuleType('probeapp')
mod.__path__ = ['/tmp']
sys.modules['probeapp'] = mod
django.setup()

from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=50, default='DEFAULT', blank=True)
    class Meta:
        app_label = 'probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name', 'kind']
    def clean(self):
        cd = super().clean()
        cd['kind'] = 'DERIVED'   # non-empty value produced in clean(), kind omitted from data
        return cd

# 'kind' omitted from submitted data
form = F(data={'name': 'x'})
assert form.is_valid(), form.errors
inst = M()
construct_instance(form, inst)
print("kind =", repr(inst.kind))
if inst.kind == 'DERIVED':
    print("PASS: cleaned_data overrode model default")
    sys.exit(0)
print("FAIL: field left at default", repr(inst.kind))
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2 AC1/AC2: an EMPTY cleaned_data value ('') for a field with a model
default that was omitted from data leaves the field at its model default.
Holds on patched (and base)."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, USE_TZ=True,
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'])
mod = types.ModuleType('probeapp'); mod.__path__=['/tmp']; sys.modules['probeapp']=mod
django.setup()
from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=50, default='DEFAULT', blank=True)
    class Meta: app_label='probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name','kind']
    def clean(self):
        cd = super().clean()
        cd['kind'] = ''   # empty sentinel
        return cd

form = F(data={'name':'x'})
assert form.is_valid(), form.errors
inst = M()
construct_instance(form, inst)
print("kind =", repr(inst.kind))
if inst.kind == 'DEFAULT':
    print("PASS: empty cleaned_data left field at model default")
    sys.exit(0)
print("FAIL: field was overwritten with empty value")
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2 AC3: an optional checkbox-style (BooleanField, not required) field
omitted from submitted data with empty resolved value (False in empty_values?)
Actually test: unchecked checkbox -> value_omitted_from_data False for checkbox,
so use a genuinely omitted non-checkbox empty. Here test the empty_values
membership for None: cleaned_data None leaves default.
Holds on patched."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, USE_TZ=True,
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'])
mod = types.ModuleType('probeapp'); mod.__path__=['/tmp']; sys.modules['probeapp']=mod
django.setup()
from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    count = models.IntegerField(default=7, null=True, blank=True)
    class Meta: app_label='probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name','count']
    def clean(self):
        cd = super().clean()
        cd['count'] = None   # None is in empty_values
        return cd

form = F(data={'name':'x'})
assert form.is_valid(), form.errors
inst = M()
construct_instance(form, inst)
print("count =", repr(inst.count))
if inst.count == 7:
    print("PASS: None (empty sentinel) left field at model default")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3 AC3: a field with NO model default gets its cleaned_data value
assigned even when that value is EMPTY (default-fallback rule applies only to
fields that HAVE a default). Holds on patched AND base (regression)."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, USE_TZ=True,
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'])
mod = types.ModuleType('probeapp'); mod.__path__=['/tmp']; sys.modules['probeapp']=mod
django.setup()
from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    note = models.CharField(max_length=50, blank=True)  # NO default
    class Meta: app_label='probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name','note']
    def clean(self):
        cd = super().clean()
        cd['note'] = ''   # empty, but field has no default
        return cd

# preset note to a sentinel so we can tell if it got assigned
inst = M(note='PRESET')
form = F(data={'name':'x'})
assert form.is_valid(), form.errors
construct_instance(form, inst)
print("note =", repr(inst.note))
if inst.note == '':
    print("PASS: no-default field assigned empty cleaned_data value")
    sys.exit(0)
print("FAIL: field not assigned (still", repr(inst.note), ")")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3 AC2: exclude collection honored — a field in `exclude` is NOT
assigned even though it has a non-empty override. Also Req3 AC1 (name absent
from cleaned_data skipped) implicitly. Regression: holds patched AND base."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, USE_TZ=True,
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'])
mod = types.ModuleType('probeapp'); mod.__path__=['/tmp']; sys.modules['probeapp']=mod
django.setup()
from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=50, default='DEFAULT', blank=True)
    class Meta: app_label='probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name','kind']
    def clean(self):
        cd = super().clean()
        cd['kind'] = 'DERIVED'
        return cd

form = F(data={'name':'x'})
assert form.is_valid(), form.errors
inst = M()
ret = construct_instance(form, inst, exclude=['kind'])
print("kind =", repr(inst.kind), "ret is inst:", ret is inst)
ok = (inst.kind == 'DEFAULT') and (ret is inst)
if ok:
    print("PASS: excluded field left at default; returns same instance in place")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1 AC3 / Req3: emptiness is determined by empty_values membership, NOT by
general falsiness. 0 and False are falsy but NOT in EMPTY_VALUES
(None,'',[],(),{}), so a cleaned_data value of 0 on a field that has a default
and was omitted MUST override the default. This discriminates a weak fix using
`not cleaned_data.get(f.name)`. Holds patched, FAILS base."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, USE_TZ=True,
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'])
mod = types.ModuleType('probeapp'); mod.__path__=['/tmp']; sys.modules['probeapp']=mod
django.setup()
from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    count = models.IntegerField(default=7, null=True, blank=True)
    class Meta: app_label='probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name','count']
    def clean(self):
        cd = super().clean()
        cd['count'] = 0   # falsy, but NOT an empty_value
        return cd

form = F(data={'name':'x'})
assert form.is_valid(), form.errors
inst = M()
construct_instance(form, inst)
print("count =", repr(inst.count))
if inst.count == 0:
    print("PASS: 0 (non-empty per empty_values) overrode default")
    sys.exit(0)
print("FAIL: 0 treated as empty; field left at default", repr(inst.count))
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1 (positive control): a non-empty cleaned_data value for a field that
has a model default and was omitted from submitted data overrides the default.
Holds on patched, FAILS on base."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    USE_TZ=True,
)
import sys, types
mod = types.ModuleType('probeapp')
mod.__path__ = ['/tmp']
sys.modules['probeapp'] = mod
django.setup()

from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=50, default='DEFAULT', blank=True)
    class Meta:
        app_label = 'probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name', 'kind']
    def clean(self):
        cd = super().clean()
        cd['kind'] = 'DERIVED'   # non-empty value produced in clean(), kind omitted from data
        return cd

# 'kind' omitted from submitted data
form = F(data={'name': 'x'})
assert form.is_valid(), form.errors
inst = M()
construct_instance(form, inst)
print("kind =", repr(inst.kind))
if inst.kind == 'DERIVED':
    print("PASS: cleaned_data overrode model default")
    sys.exit(0)
print("FAIL: field left at default", repr(inst.kind))
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree. Positive control (probe_1) HOLDS patched / FAILS base (kind='DEFAULT' vs 'DERIVED') — discriminating power confirmed. probe_6 also FAILS at base, doubling as a second discriminator. Requirements coverage: Req1 AC1/AC2 (probe_1), Req1 AC3 empty_values-not-falsiness (probe_6), Req2 AC1/AC2 empty '' (probe_2), Req2 None sentinel (probe_3), Req3 AC3 no-default field assigns empty (probe_4), Req3 AC2/AC5 exclude + return-same-instance-in-place (probe_5). Candidate weak patch REJECTED by suite (probe_6), demonstrating discrimination against the lazy falsiness reading the requirements' emphasis on empty_values (Req1 AC3, Req2 AC2) explicitly forbids. Test models used blank=True to keep forms valid while fields omitted from data. All runs completed in the official image.

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
weak.diff replaces the `cleaned_data.get(f.name) in field.empty_values` guard with `not cleaned_data.get(f.name)` (general falsiness). It passes probes 1-5 but is REJECTED by probe_6: a cleaned_data value of 0 (falsy, but NOT a member of EMPTY_VALUES={None,'',[],(),{}}) is wrongly treated as empty and the field is left at its model default (7) instead of being overridden to 0. On the gold-patched tree probe_6 correctly yields 0.
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
"""Req1 (positive control): a non-empty cleaned_data value for a field that
has a model default and was omitted from submitted data overrides the default.
Holds on patched, FAILS on base."""
import django
from django.conf import settings
settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
    USE_TZ=True,
)
import sys, types
mod = types.ModuleType('probeapp')
mod.__path__ = ['/tmp']
sys.modules['probeapp'] = mod
django.setup()

from django.db import models
from django import forms
from django.forms.models import construct_instance

class M(models.Model):
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=50, default='DEFAULT', blank=True)
    class Meta:
        app_label = 'probeapp'

class F(forms.ModelForm):
    class Meta:
        model = M
        fields = ['name', 'kind']
    def clean(self):
        cd = super().clean()
        cd['kind'] = 'DERIVED'   # non-empty value produced in clean(), kind omitted from data
        return cd

# 'kind' omitted from submitted data
form = F(data={'name': 'x'})
assert form.is_valid(), form.errors
inst = M()
construct_instance(form, inst)
print("kind =", repr(inst.kind))
if inst.kind == 'DERIVED':
    print("PASS: cleaned_data overrode model default")
    sys.exit(0)
print("FAIL: field left at default", repr(inst.kind))
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree. Positive control (probe_1) HOLDS patched / FAILS base (kind='DEFAULT' vs 'DERIVED') — discriminating power confirmed. probe_6 also FAILS at base, doubling as a second discriminator. Requirements coverage: Req1 AC1/AC2 (probe_1), Req1 AC3 empty_values-not-falsiness (probe_6), Req2 AC1/AC2 empty '' (probe_2), Req2 None sentinel (probe_3), Req3 AC3 no-default field assigns empty (probe_4), Req3 AC2/AC5 exclude + return-same-instance-in-place (probe_5). Candidate weak patch REJECTED by suite (probe_6), demonstrating discrimination against the lazy falsiness reading the requirements' emphasis on empty_values (Req1 AC3, Req2 AC2) explicitly forbids. Test models used blank=True to keep forms valid while fields omitted from data. All runs completed in the official image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds the empty_values check to the skip condition in construct_instance. R1/R2 pin the changed observable behavior (default-vs-value decision) biconditionally on empty_values membership — the correct modeling boundary, not a narrow slice. R3 correctly restates unchanged surrounding behavior (editable/pk/absent-name skips, fields/exclude filtering, no-default fields always assigned, file-field second pass, in-place return). R1.3/R2.2 correctly enumerate EMPTY_VALUES members (None, '', [], (), {}). Behavior verified via nl_attack probe on patched (exit 0) and base (exit 1) trees.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally: a non-empty cleaned_data value overrides a field's model default, while empty values (per the form field's empty_values) fall back to the default. All named identifiers (construct_instance, django/forms/models.py, value_omitted_from_data, has_default, empty_values, EMPTY_VALUES) are pre-existing PUBLIC Django APIs used for legitimate localization, not fix-invented names. The enumeration of empty_values members (None, '', [], (), {}) is a factual statement about the public django.core.validators.EMPTY_VALUES constant, not a mirror of the test's parametrization. None of the hidden test's distinctive artifacts leak: test name (test_default_not_populated_on_non_empty_value_in_cleaned_data), file path (tests/model_forms/tests.py), model/form names (PublicationDefaults, PubForm), the mocked_mode attribute, subTest usage, or the concrete values 'de'/'di' all appear nowhere in requirements.md. The gold patch's core mechanism (cleaned_data.get(f.name) in field.empty_values) is transmitted only as a behavioral requirement, which is the intended translation, not test/gold-code transmission. The problem_statement already publicizes the entire scenario (cleaned_data overwriting a field's model default when not in the payload).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
