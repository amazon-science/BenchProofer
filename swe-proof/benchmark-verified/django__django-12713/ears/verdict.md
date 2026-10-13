# P2 adversarial audit — django__django-12713

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

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()

# Requirement 1.1 & 1.4 (POSITIVE CONTROL): supplied widget must survive the
# cascade even though field is in filter_horizontal. Django binds the widget
# onto the form field (may copy it), so we assert the widget's CLASS and our
# sentinel attr survive, and that it is NOT an admin cascade widget.
from django.contrib.admin.widgets import (FilteredSelectMultiple,
    ManyToManyRawIdWidget, AutocompleteSelectMultiple)
class MyAdmin(admin.ModelAdmin):
    filter_horizontal = ['friends']
ma = MyAdmin(Holder, site)
sentinel = forms.SelectMultiple(attrs={'data-sentinel': 'MINE'})
ff = ma.formfield_for_manytomany(m2m(), Req(), widget=sentinel)
used = ff.widget
print("widget type:", type(used).__name__, "attrs:", getattr(used, 'attrs', None))
cascade = (FilteredSelectMultiple, ManyToManyRawIdWidget, AutocompleteSelectMultiple)
ok = (type(used) is forms.SelectMultiple
      and getattr(used, 'attrs', {}).get('data-sentinel') == 'MINE'
      and not isinstance(used, cascade))
print("supplied widget preserved:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
class MyWidget(forms.SelectMultiple):
    pass
class MyAdmin(admin.ModelAdmin):
    filter_vertical = ['friends']
    formfield_overrides = {models.ManyToManyField: {'widget': MyWidget}}
ma = MyAdmin(Holder, site)
ff = ma.formfield_for_dbfield(m2m(), request=Req())
w = ff.widget
inner = w.widget if isinstance(w, RelatedFieldWidgetWrapper) else w
print("outer:", type(w).__name__, "inner:", type(inner).__name__)
ok = isinstance(inner, MyWidget)
print("overrides widget used:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()
from django.contrib.admin.widgets import FilteredSelectMultiple
class HAdmin(admin.ModelAdmin):
    filter_horizontal = ['friends']
class VAdmin(admin.ModelAdmin):
    filter_vertical = ['friends']
hff = HAdmin(Holder, site).formfield_for_manytomany(m2m(), Req())
vff = VAdmin(Holder, site).formfield_for_manytomany(m2m(), Req())
print("h widget:", type(hff.widget).__name__, "is_stacked:", getattr(hff.widget,'is_stacked',None))
print("v widget:", type(vff.widget).__name__, "is_stacked:", getattr(vff.widget,'is_stacked',None))
ok = (isinstance(hff.widget, FilteredSelectMultiple) and hff.widget.is_stacked is False
      and isinstance(vff.widget, FilteredSelectMultiple) and vff.widget.is_stacked is True)
print("cascade correct:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()
from django.contrib.admin.widgets import FilteredSelectMultiple, ManyToManyRawIdWidget, AutocompleteSelectMultiple
class PlainAdmin(admin.ModelAdmin):
    pass
ff = PlainAdmin(Holder, site).formfield_for_manytomany(m2m(), Req())
w = ff.widget
print("widget:", type(w).__name__)
special = (FilteredSelectMultiple, ManyToManyRawIdWidget, AutocompleteSelectMultiple)
ok = not isinstance(w, special)
print("default widget left in place:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()
class PlainAdmin(admin.ModelAdmin):
    pass
ff = PlainAdmin(Holder, site).formfield_for_manytomany(m2m(), Req())
help_text = ff.help_text or ""
print("help_text:", repr(help_text))
ok = "hold down" in help_text.lower()
print("help augmented for plain select:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()
# Requirement 3.2: a caller-supplied queryset SHALL be left in place (not
# replaced by the ordering-aware related queryset). The form field clones the
# queryset via .all(), so we assert the DISTINCTIVE filter survives rather than
# object identity.
class PlainAdmin(admin.ModelAdmin):
    pass
qs = Related.objects.filter(name='SENTINEL_ZZZ')
ff = PlainAdmin(Holder, site).formfield_for_manytomany(m2m(), Req(), queryset=qs)
sql = str(ff.queryset.query)
print("field query:", sql)
ok = 'SENTINEL_ZZZ' in sql
print("supplied queryset left in place:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()

# Requirement 1.1 & 1.4 (POSITIVE CONTROL): supplied widget must survive the
# cascade even though field is in filter_horizontal. Django binds the widget
# onto the form field (may copy it), so we assert the widget's CLASS and our
# sentinel attr survive, and that it is NOT an admin cascade widget.
from django.contrib.admin.widgets import (FilteredSelectMultiple,
    ManyToManyRawIdWidget, AutocompleteSelectMultiple)
class MyAdmin(admin.ModelAdmin):
    filter_horizontal = ['friends']
ma = MyAdmin(Holder, site)
sentinel = forms.SelectMultiple(attrs={'data-sentinel': 'MINE'})
ff = ma.formfield_for_manytomany(m2m(), Req(), widget=sentinel)
used = ff.widget
print("widget type:", type(used).__name__, "attrs:", getattr(used, 'attrs', None))
cascade = (FilteredSelectMultiple, ManyToManyRawIdWidget, AutocompleteSelectMultiple)
ok = (type(used) is forms.SelectMultiple
      and getattr(used, 'attrs', {}).get('data-sentinel') == 'MINE'
      and not isinstance(used, cascade))
print("supplied widget preserved:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: formfield_for_manytomany must honor a caller-supplied widget (skip cascade) and otherwise preserve the existing autocomplete>raw-id>filter cascade, help-text augmentation, queryset, and through-model behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.4, POSITIVE CONTROL): supplied widget survives even though field is in filter_horizontal; asserts widget class + sentinel attr survive and is not a cascade widget. HOLDS patched, VIOLATED at base (base returns FilteredSelectMultiple) => prepatch reproduced, discriminating.
- probe_2 (Req 1.2/1.3): formfield_overrides widget for ManyToManyField wins over filter_vertical cascade; observed as RelatedFieldWidgetWrapper inner widget = MyWidget. HOLDS patched.
- probe_3 (Req 2.1/2.4): no widget -> FilteredSelectMultiple, is_stacked False for filter_horizontal and True for filter_vertical. HOLDS.
- probe_4 (Req 2.5): no widget, field in no list -> plain SelectMultiple (no cascade widget). HOLDS.
- probe_5 (Req 3.3): plain multiple-select gets 'Hold down Control...' help text. HOLDS.
- probe_6 (Req 3.2): caller-supplied queryset left in place (distinctive filter survives). HOLDS.

Candidate wrong-fix (weak_partial.diff): guards ONLY the autocomplete branch with 'widget' not in kwargs, leaving raw_id/filter branches unconditional (a plausible partial reading). Probe suite REJECTS it: probe_1 VIOLATED (filter_horizontal still clobbers supplied widget) and probe_2 VIOLATED (overrides widget replaced by FilteredSelectMultiple); probe_3 still HOLDS. This demonstrates the suite discriminates a partial/wrong implementation.

All 6 probes hold on patched; positive control fails at base and holds patched; a plausible wrong fix is rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes', 'django.contrib.auth',
            'django.contrib.admin', 'django.contrib.messages',
            'django.contrib.sessions',
        ],
        SITE_ID=1, USE_TZ=True,
        MIDDLEWARE=[], TEMPLATES=[],
    )
django.setup()
from django.db import models
from django import forms
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Related(models.Model):
    name = models.CharField(max_length=20)
    class Meta: app_label = 'auth'

class Holder(models.Model):
    friends = models.ManyToManyField(Related, related_name='+')
    class Meta: app_label = 'auth'

def m2m():
    return Holder._meta.get_field('friends')

class Req: pass
site = AdminSite()

# Requirement 1.1 & 1.4 (POSITIVE CONTROL): supplied widget must survive the
# cascade even though field is in filter_horizontal. Django binds the widget
# onto the form field (may copy it), so we assert the widget's CLASS and our
# sentinel attr survive, and that it is NOT an admin cascade widget.
from django.contrib.admin.widgets import (FilteredSelectMultiple,
    ManyToManyRawIdWidget, AutocompleteSelectMultiple)
class MyAdmin(admin.ModelAdmin):
    filter_horizontal = ['friends']
ma = MyAdmin(Holder, site)
sentinel = forms.SelectMultiple(attrs={'data-sentinel': 'MINE'})
ff = ma.formfield_for_manytomany(m2m(), Req(), widget=sentinel)
used = ff.widget
print("widget type:", type(used).__name__, "attrs:", getattr(used, 'attrs', None))
cascade = (FilteredSelectMultiple, ManyToManyRawIdWidget, AutocompleteSelectMultiple)
ok = (type(used) is forms.SelectMultiple
      and getattr(used, 'attrs', {}).get('data-sentinel') == 'MINE'
      and not isinstance(used, cascade))
print("supplied widget preserved:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: formfield_for_manytomany must honor a caller-supplied widget (skip cascade) and otherwise preserve the existing autocomplete>raw-id>filter cascade, help-text augmentation, queryset, and through-model behavior.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.4, POSITIVE CONTROL): supplied widget survives even though field is in filter_horizontal; asserts widget class + sentinel attr survive and is not a cascade widget. HOLDS patched, VIOLATED at base (base returns FilteredSelectMultiple) => prepatch reproduced, discriminating.
- probe_2 (Req 1.2/1.3): formfield_overrides widget for ManyToManyField wins over filter_vertical cascade; observed as RelatedFieldWidgetWrapper inner widget = MyWidget. HOLDS patched.
- probe_3 (Req 2.1/2.4): no widget -> FilteredSelectMultiple, is_stacked False for filter_horizontal and True for filter_vertical. HOLDS.
- probe_4 (Req 2.5): no widget, field in no list -> plain SelectMultiple (no cascade widget). HOLDS.
- probe_5 (Req 3.3): plain multiple-select gets 'Hold down Control...' help text. HOLDS.
- probe_6 (Req 3.2): caller-supplied queryset left in place (distinctive filter survives). HOLDS.

Candidate wrong-fix (weak_partial.diff): guards ONLY the autocomplete branch with 'widget' not in kwargs, leaving raw_id/filter branches unconditional (a plausible partial reading). Probe suite REJECTS it: probe_1 VIOLATED (filter_horizontal still clobbers supplied widget) and probe_2 VIOLATED (overrides widget replaced by FilteredSelectMultiple); probe_3 still HOLDS. This demonstrates the suite discriminates a partial/wrong implementation.

All 6 probes hold on patched; positive control fails at base and holds patched; a plausible wrong fix is rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch is a single change: the autocomplete/raw-id/filter widget cascade is wrapped in `if 'widget' not in kwargs:`. Req 1 (honor supplied widget, skip whole cascade) and Req 2 (preserve cascade order autocomplete->raw-id->filter when no widget) match this exactly and are confirmed by probe (gold HOLDS exit 0; base VIOLATED exit 1 on 'supplied widget not honored'). Req 3 correctly asserts the untouched neighbors (through-model early return, queryset computation, help-text augmentation, formfield_for_foreignkey, related-widget wrapper, formfield_overrides merge) remain unchanged — none are modified by the diff. Modeling boundary is the changed behavior, not a sub-branch or helper. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally: it names the changed methods (formfield_for_manytomany/foreignkey/dbfield) and the admin classification lists (autocomplete_fields/raw_id_fields/filter_vertical/filter_horizontal) and formfield_overrides — all public via the problem statement and legitimate source localization. None of the hidden-test specifics leak: the test function name (test_formfield_overrides_m2m_filter_widget), test class (AdminFormfieldForDBFieldTests), file path (tests/admin_widgets/tests.py), the concrete widget class CheckboxSelectMultiple, the model Band, the field name 'members', and the assertion path field.widget.widget are absent. Req 1.3's mention of the 'relation-field widget wrapper around it' describes real public Django RelatedFieldWidgetWrapper behavior, not the assertion. The four-list enumeration tracks the gold patch cascade structure (public source), not a test parametrization (the F2P test is a single non-parametrized case). No quoted test/gold code and no fix-invented identifiers.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
