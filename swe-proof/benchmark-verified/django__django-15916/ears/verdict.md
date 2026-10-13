# P2 adversarial audit — django__django-15916

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_meta_direct.py`, `probe_2_factory_base_meta.py`, `probe_3_meta_inheritance.py`, `probe_4_toplevel_ignored.py`, `probe_5_factory_widgets.py`, `probe_6_improperly.py`, `probe_7_noncallable.py`, `probe_8_explicit_callback.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_meta_direct.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_meta_direct.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

def callback(db_field, **kwargs):
    return forms.CharField(widget=forms.Textarea)

class NewForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["id","name"]
        formfield_callback = callback

widgets = {n: type(f.widget) for n,f in NewForm.base_fields.items()}
print("Req2.1 direct-Meta callback -> widgets:", {n:w.__name__ for n,w in widgets.items()})
ok = all(w is forms.Textarea for w in widgets.values()) and len(widgets)>=2
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_factory_base_meta.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms
from django.forms.models import modelform_factory

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

def callback(db_field, **kwargs):
    return forms.CharField(widget=forms.Textarea)

class BaseForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = "__all__"
        formfield_callback = callback

NewForm = modelform_factory(model=Person, form=BaseForm)
class InheritedForm(NewForm): pass

nw = {n: type(f.widget) for n,f in NewForm.base_fields.items()}
iw = {n: type(f.widget) for n,f in InheritedForm.base_fields.items()}
print("factory-form widgets:", {n:w.__name__ for n,w in nw.items()})
print("inherited widgets:", {n:w.__name__ for n,w in iw.items()})
ok = (len(nw)>=1 and all(w is forms.Textarea for w in nw.values())
      and all(iw[n] is nw[n] for n in nw))
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_meta_inheritance.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

def callback(db_field, **kwargs):
    return forms.CharField(widget=forms.Textarea)

class BaseForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["id","name"]
        formfield_callback = callback

# Derived form whose own Meta inherits from BaseForm.Meta and does NOT redeclare callback
class Derived(BaseForm):
    class Meta(BaseForm.Meta):
        pass

w = {n: type(f.widget) for n,f in Derived.base_fields.items()}
print("Req2.4 inherited-Meta callback widgets:", {n:x.__name__ for n,x in w.items()})
ok = len(w)>=2 and all(x is forms.Textarea for x in w.values())
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_toplevel_ignored.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

def cb(db_field, **kwargs):
    return forms.CharField(widget=forms.Textarea)

# Top-level class attribute callback, but NO Meta.formfield_callback
class F(forms.ModelForm):
    formfield_callback = cb
    class Meta:
        model = Person
        fields = ["id","name"]

w = {n: type(f.widget) for n,f in F.base_fields.items()}
print("Req2.3 top-level-only callback widgets:", {n:x.__name__ for n,x in w.items()})
# Gold: default construction -> NOT Textarea for the CharField 'name'
ok = (type(F.base_fields["name"].widget) is not forms.Textarea)
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_factory_widgets.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms
from django.forms.models import modelform_factory

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

F = modelform_factory(model=Person, fields=["id","name"],
                      widgets={"name": forms.Textarea})
w = {n: type(f.widget) for n,f in F.base_fields.items()}
print("Req4.5 factory widgets:", {n:x.__name__ for n,x in w.items()})
ok = type(F.base_fields["name"].widget) is forms.Textarea
# and default when absent
F2 = modelform_factory(model=Person, fields=["name"])
ok = ok and type(F2.base_fields["name"].widget) is not forms.Textarea
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_improperly.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms
from django.forms.models import modelform_factory
from django.core.exceptions import ImproperlyConfigured

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

try:
    modelform_factory(model=Person)
    print("no exception raised"); raised=False
except ImproperlyConfigured as e:
    print("Req4.6 raised ImproperlyConfigured:", e); raised=True
except Exception as e:
    print("wrong exception:", type(e).__name__, e); raised=False
import sys; sys.exit(0 if raised else 1)
```

Attack 7 — `probe_7_noncallable.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

try:
    class F(forms.ModelForm):
        class Meta:
            model = Person
            fields = ["id","name"]
            formfield_callback = "not-callable"
    _ = F.base_fields
    print("no TypeError raised"); raised=False
except TypeError as e:
    print("Req4.1 raised TypeError:", e); raised=True
except Exception as e:
    print("wrong exception:", type(e).__name__, e); raised=False
import sys; sys.exit(0 if raised else 1)
```

Attack 8 — `probe_8_explicit_callback.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms
from django.forms.models import modelform_factory

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

calls = []
def cb(db_field, **kwargs):
    calls.append(db_field.name)
    return forms.CharField(widget=forms.Textarea)

F = modelform_factory(model=Person, fields=["id","name"], formfield_callback=cb)
w = {n: type(f.widget) for n,f in F.base_fields.items()}
print("Req3.3 explicit callback widgets:", {n:x.__name__ for n,x in w.items()}, "calls:", calls)
ok = (len(F.base_fields)>=2 and all(x is forms.Textarea for x in w.values())
      and set(calls) >= {"id","name"})
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_meta_direct.py`

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

def callback(db_field, **kwargs):
    return forms.CharField(widget=forms.Textarea)

class NewForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["id","name"]
        formfield_callback = callback

widgets = {n: type(f.widget) for n,f in NewForm.base_fields.items()}
print("Req2.1 direct-Meta callback -> widgets:", {n:w.__name__ for n,w in widgets.items()})
ok = all(w is forms.Textarea for w in widgets.values()) and len(widgets)>=2
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes, all HOLD on gold-patched tree. Coverage: probe_1 (Req2.1/2.2 Meta.formfield_callback used when class built directly), probe_2 (Req3.1/3.2 + F2P test_custom_callback_from_base_form_meta: factory keeps base form's Meta callback, inherited subclass matches), probe_3 (Req1.3/2.4 Meta-inheritance of callback), probe_4 (Req2.3 top-level class-attr callback IGNORED when Meta has none), probe_5 (Req4.5 factory widgets mapping + default), probe_6 (Req4.6 ImproperlyConfigured without fields/exclude), probe_7 (Req4.1 non-callable -> TypeError), probe_8 (Req3.3 explicit factory callback used, once per field).

Discriminating power: probes 1,2,4,7 are HOLD on gold / VIOLATED at base. Positive control probe_1 encodes the core fixed behavior (Meta.formfield_callback honored when the ModelForm is built directly) — VIOLATED at base, HOLDS on gold. probes 3,5,6,8 are regression/'SHALL keep' criteria that hold on both trees.

Candidate patches:
- candidate_A_factory_only (gold's 3rd hunk only: stop factory injecting top-level formfield_callback, but DON'T teach the metaclass to read Meta.formfield_callback): REJECTED by probe_1 (Req2.1 fails: direct Meta callback still ignored) and probe_4. A weak reading of Req3 alone permits this; the suite rejects it — demonstrates discrimination.
- candidate_B_metaclass_only (gold's first two hunks: ModelFormOptions.formfield_callback + metaclass reads opts.formfield_callback, but leaves the factory's {'formfield_callback': None} top-level injection): PASSES all 8 probes. This is NOT a too-weak finding — it is a genuinely correct equivalent fix. Once the metaclass no longer pops the top-level attr and instead reads opts.formfield_callback, the factory's inert top-level None is simply ignored (metaclass consults the Meta options chain, into which the factory writes the real callback). It would resolve the hidden tests, so it is reported only as a benign equivalent, not a weakness. The runner may confirm against the harness.

No VIOLATION found (every mandated behavior holds on the patched tree) and no probe-conforming alternative that fails to resolve. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1_meta_direct.py`, `probe_2_factory_base_meta.py`, `probe_3_meta_inheritance.py`, `probe_4_toplevel_ignored.py`, `probe_5_factory_widgets.py`, `probe_6_improperly.py`, `probe_7_noncallable.py`, `probe_8_explicit_callback.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_meta_direct.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_meta_direct.py` → holds on the patched tree (good)

Attack 2 — `probe_2_factory_base_meta.py` → holds on the patched tree (good)

Attack 3 — `probe_3_meta_inheritance.py` → holds on the patched tree (good)

Attack 4 — `probe_4_toplevel_ignored.py` → holds on the patched tree (good)

Attack 5 — `probe_5_factory_widgets.py` → holds on the patched tree (good)

Attack 6 — `probe_6_improperly.py` → holds on the patched tree (good)

Attack 7 — `probe_7_noncallable.py` → holds on the patched tree (good)

Attack 8 — `probe_8_explicit_callback.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_meta_direct.py`

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
    'django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import models
from django import forms

class Person(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    class Meta: app_label='auth'

def callback(db_field, **kwargs):
    return forms.CharField(widget=forms.Textarea)

class NewForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["id","name"]
        formfield_callback = callback

widgets = {n: type(f.widget) for n,f in NewForm.base_fields.items()}
print("Req2.1 direct-Meta callback -> widgets:", {n:w.__name__ for n,w in widgets.items()})
ok = all(w is forms.Textarea for w in widgets.values()) and len(widgets)>=2
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

8 probes, all HOLD on gold-patched tree. Coverage: probe_1 (Req2.1/2.2 Meta.formfield_callback used when class built directly), probe_2 (Req3.1/3.2 + F2P test_custom_callback_from_base_form_meta: factory keeps base form's Meta callback, inherited subclass matches), probe_3 (Req1.3/2.4 Meta-inheritance of callback), probe_4 (Req2.3 top-level class-attr callback IGNORED when Meta has none), probe_5 (Req4.5 factory widgets mapping + default), probe_6 (Req4.6 ImproperlyConfigured without fields/exclude), probe_7 (Req4.1 non-callable -> TypeError), probe_8 (Req3.3 explicit factory callback used, once per field).

Discriminating power: probes 1,2,4,7 are HOLD on gold / VIOLATED at base. Positive control probe_1 encodes the core fixed behavior (Meta.formfield_callback honored when the ModelForm is built directly) — VIOLATED at base, HOLDS on gold. probes 3,5,6,8 are regression/'SHALL keep' criteria that hold on both trees.

Candidate patches:
- candidate_A_factory_only (gold's 3rd hunk only: stop factory injecting top-level formfield_callback, but DON'T teach the metaclass to read Meta.formfield_callback): REJECTED by probe_1 (Req2.1 fails: direct Meta callback still ignored) and probe_4. A weak reading of Req3 alone permits this; the suite rejects it — demonstrates discrimination.
- candidate_B_metaclass_only (gold's first two hunks: ModelFormOptions.formfield_callback + metaclass reads opts.formfield_callback, but leaves the factory's {'formfield_callback': None} top-level injection): PASSES all 8 probes. This is NOT a too-weak finding — it is a genuinely correct equivalent fix. Once the metaclass no longer pops the top-level attr and instead reads opts.formfield_callback, the factory's inert top-level None is simply ignored (metaclass consults the Meta options chain, into which the factory writes the real callback). It would resolve the hidden tests, so it is reported only as a benign equivalent, not a weakness. The runner may confirm against the harness.

No VIOLATION found (every mandated behavior holds on the patched tree) and no probe-conforming alternative that fails to resolve. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Ran nl_attack probe on both gold-patched (exit 0, ALL OK) and base (exit 1, ModelFormOptions has no attribute formfield_callback) trees. Requirements 4.x are regression-protection over unchanged behavior (TypeError on non-callable, ImproperlyConfigured without fields/exclude, widgets mapping, metaclass identity) and are consistent with the code. Modeling boundary is correct: requirements pin the observable field-builder-callback resolution behavior across all three changed symbols (ModelFormOptions, ModelFormMetaclass.__new__, modelform_factory) rather than one branch/helper.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior in EARS terms at an appropriate abstraction. All named symbols (ModelFormOptions, ModelFormMetaclass.__new__, modelform_factory, fields_for_model) are legitimate change-localization; formfield_callback/Meta/modelform_factory/base-form inheritance all appear in the public problem_statement. The hidden test fixtures (callback returning forms.CharField(widget=forms.Textarea), model Person, fields ["id","name"]/"__all__", test names test_custom_callback_in_meta / test_custom_callback_from_base_form_meta, type(field.widget) assertions) are NOT present — no widget/model/field-name specifics, no test names/paths/ids, no quoted test or gold code. The gold patch introduces no new identifier the spec exposes. 'same widget type per field' (Req 2.5/4.2) is a behavioral translation of the assertions, not a transcription, and there is no test-shaped enumeration mirroring the parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
