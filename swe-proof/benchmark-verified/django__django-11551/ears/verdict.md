# P2 adversarial audit — django__django-11551

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: R2/R3 -- field accessible only via instance (hasattr(model,item) False,
# but get_field succeeds) must NOT produce admin.E108.
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
    SITE_ID=1)
django.setup()
from django.db.models import Field, Model
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class PositionField(Field):
    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, self)
    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError()

class TestModel(Model):
    field = PositionField()
    class Meta:
        app_label = 'admin'

class TestModelAdmin(ModelAdmin):
    list_display = ('field',)

# sanity: hasattr on the model class must be False (the regression trigger)
print("hasattr(model,'field') =", hasattr(TestModel, 'field'))
admin_obj = TestModelAdmin(TestModel, AdminSite())
errs = admin_obj.checks_class()._check_list_display_item(admin_obj, 'field', 'list_display[0]')
ids = [e.id for e in errs]
print("errors:", ids)
if any(e.id == 'admin.E108' for e in errs):
    print("FAIL: E108 raised for instance-only field")
    sys.exit(1)
if errs:
    print("FAIL: unexpected errors", ids)
    sys.exit(1)
print("PASS: no error for instance-only field")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'], SITE_ID=1)
django.setup()
from django.db.models import Model, IntegerField
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class M(Model):
    n = IntegerField(default=0)
    class Meta: app_label='admin'

# model class whose _meta.get_field must NOT be called for a callable
called = {'get_field': False}
orig = M._meta.get_field
def spy(item):
    called['get_field'] = True
    return orig(item)
M._meta.get_field = spy

class A(ModelAdmin):
    list_display = (lambda o: 'x',)

a = A(M, AdminSite())
def mycall(o): return 'y'
errs = a.checks_class()._check_list_display_item(a, mycall, 'list_display[0]')
print("errors:", [e.id for e in errs], "get_field called:", called['get_field'])
if errs:
    print("FAIL: callable produced error"); sys.exit(1)
if called['get_field']:
    print("FAIL: field resolution attempted for callable"); sys.exit(1)
print("PASS: callable accepted, no field lookup"); sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'], SITE_ID=1)
django.setup()
from django.db.models import Model, IntegerField
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class M(Model):
    n = IntegerField(default=0)
    class Meta: app_label='admin'
called={'g':False}
orig=M._meta.get_field
def spy(i):
    called['g']=True; return orig(i)
M._meta.get_field=spy

class A(ModelAdmin):
    list_display=('my_attr',)
    def my_attr(self, obj): return 'z'

a=A(M, AdminSite())
errs=a.checks_class()._check_list_display_item(a,'my_attr','list_display[0]')
print("errors:", [e.id for e in errs], "get_field called:", called['g'])
if errs: print("FAIL: admin attr produced error"); sys.exit(1)
if called['g']: print("FAIL: field lookup attempted for admin attr"); sys.exit(1)
print("PASS: admin attr accepted, no field lookup"); sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'], SITE_ID=1)
django.setup()
from django.db.models import Model, IntegerField
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class M(Model):
    n = IntegerField(default=0)
    class Meta: app_label='admin'
class A(ModelAdmin):
    list_display=('no_such',)
a=A(M, AdminSite())
errs=a.checks_class()._check_list_display_item(a,'no_such','list_display[0]')
print("errors:", [(e.id,e.msg) for e in errs])
if len(errs)!=1 or errs[0].id!='admin.E108':
    print("FAIL: expected exactly one E108"); sys.exit(1)
msg=errs[0].msg
# message must mention item, admin class, model app_label.object_name
need=["no_such","not a callable","attribute of 'A'","attribute or method on","admin.M"]
for tok in need:
    if tok not in msg:
        print("FAIL: message missing token:", tok); sys.exit(1)
print("PASS: single E108 with correct message"); sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'], SITE_ID=1)
django.setup()
from django.db.models import Model, IntegerField, ManyToManyField
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class Other(Model):
    class Meta: app_label='admin'
class M(Model):
    rel = ManyToManyField(Other)
    class Meta: app_label='admin'
class A(ModelAdmin):
    list_display=('rel',)
a=A(M, AdminSite())
errs=a.checks_class()._check_list_display_item(a,'rel','list_display[0]')
print("errors:", [e.id for e in errs])
if len(errs)!=1 or errs[0].id!='admin.E109':
    print("FAIL: expected exactly one E109"); sys.exit(1)
print("PASS: M2M -> single E109"); sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'], SITE_ID=1)
django.setup()
from django.db.models import Model, IntegerField
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class M(Model):
    n = IntegerField(default=0)
    class Meta: app_label='admin'
    def a_method(self): return 5
class A(ModelAdmin):
    list_display=('n','a_method')
a=A(M, AdminSite())
c=a.checks_class()
e1=c._check_list_display_item(a,'n','list_display[0]')       # concrete field
e2=c._check_list_display_item(a,'a_method','list_display[1]') # model method via getattr
print("field errors:", [e.id for e in e1], "method errors:", [e.id for e in e2])
if e1 or e2:
    print("FAIL: concrete field or model method rejected"); sys.exit(1)
print("PASS: concrete field and model method accepted"); sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'], SITE_ID=1)
django.setup()
from django.db.models import Model, IntegerField, ManyToManyField
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class Other(Model):
    class Meta: app_label='admin'
class M(Model):
    n = IntegerField(default=0)
    class Meta: app_label='admin'
# attach a raw ManyToManyField as a plain class attribute (NOT contributed to _meta)
M.m2m_attr = ManyToManyField(Other)
# confirm it's not in _meta
try:
    M._meta.get_field('m2m_attr'); in_meta=True
except Exception:
    in_meta=False
class A(ModelAdmin):
    list_display=('m2m_attr',)
a=A(M, AdminSite())
errs=a.checks_class()._check_list_display_item(a,'m2m_attr','list_display[0]')
print("in_meta:", in_meta, "errors:", [e.id for e in errs])
if in_meta:
    print("SKIP-INVALID: field unexpectedly in meta"); sys.exit(1)
if len(errs)!=1 or errs[0].id!='admin.E109':
    print("FAIL: expected exactly one E109 for getattr-resolved M2M"); sys.exit(1)
print("PASS: getattr-resolved M2M -> E109"); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: R2/R3 -- field accessible only via instance (hasattr(model,item) False,
# but get_field succeeds) must NOT produce admin.E108.
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
    SITE_ID=1)
django.setup()
from django.db.models import Field, Model
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class PositionField(Field):
    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, self)
    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError()

class TestModel(Model):
    field = PositionField()
    class Meta:
        app_label = 'admin'

class TestModelAdmin(ModelAdmin):
    list_display = ('field',)

# sanity: hasattr on the model class must be False (the regression trigger)
print("hasattr(model,'field') =", hasattr(TestModel, 'field'))
admin_obj = TestModelAdmin(TestModel, AdminSite())
errs = admin_obj.checks_class()._check_list_display_item(admin_obj, 'field', 'list_display[0]')
ids = [e.id for e in errs]
print("errors:", ids)
if any(e.id == 'admin.E108' for e in errs):
    print("FAIL: E108 raised for instance-only field")
    sys.exit(1)
if errs:
    print("FAIL: unexpected errors", ids)
    sys.exit(1)
print("PASS: no error for instance-only field")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11551: fix `_check_list_display_item` so a field reachable only via a model instance (descriptor raising AttributeError on the class) still validates. Gold patch removes the `hasattr(obj.model, item)` gate and resolves via `_meta.get_field` first, falling back to `getattr(obj.model, item)`, emitting E108 only when both fail and E109 for M2M.

Probes (all HOLD on gold-patched tree):
- probe_1 (R2.1-2.3/R3, POSITIVE CONTROL): PositionField-style descriptor, hasattr(model,'field')=False; must NOT raise E108. HOLDS patched (errors=[]), VIOLATED at base (E108) => discriminates.
- probe_2 (R1.1/R1.3): callable entry -> no error AND get_field never called (spied). HOLDS.
- probe_3 (R1.2/R1.4): admin-object attribute -> no error AND get_field never called. HOLDS.
- probe_4 (R3.1/R3.2): nonexistent entry 'no_such' -> exactly one E108 with message containing item, admin class 'A', model 'admin.M'. HOLDS.
- probe_5 (R4.1/R4.2): M2M in _meta -> exactly one E109. HOLDS.
- probe_6 (R5.4): concrete IntegerField and model method a_method accepted (no error). HOLDS.
- probe_7 (R4.4): ManyToManyField reachable only via model-class attribute (not in _meta, resolved by getattr) -> exactly one E109, not E108. HOLDS.

Candidate wrong-fix patches (>=1 rejected required; both REJECTED by the suite):
- reject_noE108.diff: removes the E108 branch entirely (never rejects unresolvable entries; only handles _meta fields). REJECTED by probe_4 (nonexistent entry now yields [] instead of E108) and probe_7 (getattr M2M yields []).
- reject_partial_getattr.diff: resolves via _meta then getattr and emits E108 correctly, but omits the ManyToManyField check on the getattr-resolved path. Passes probes 1/4/5 but REJECTED by probe_7 (getattr-resolved M2M -> [] instead of E109), matching the exact secondary bug the requirements (R4.4) forbid.

All needed runs completed. 7 distinct probes hold on patched; positive control discriminates (patched HOLDS, base VIOLATED); >=1 candidate exercised and REJECTED. Suite discriminates wrong implementations. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Positive control: R2/R3 -- field accessible only via instance (hasattr(model,item) False,
# but get_field succeeds) must NOT produce admin.E108.
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.admin'],
    SITE_ID=1)
django.setup()
from django.db.models import Field, Model
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite

class PositionField(Field):
    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, self)
    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError()

class TestModel(Model):
    field = PositionField()
    class Meta:
        app_label = 'admin'

class TestModelAdmin(ModelAdmin):
    list_display = ('field',)

# sanity: hasattr on the model class must be False (the regression trigger)
print("hasattr(model,'field') =", hasattr(TestModel, 'field'))
admin_obj = TestModelAdmin(TestModel, AdminSite())
errs = admin_obj.checks_class()._check_list_display_item(admin_obj, 'field', 'list_display[0]')
ids = [e.id for e in errs]
print("errors:", ids)
if any(e.id == 'admin.E108' for e in errs):
    print("FAIL: E108 raised for instance-only field")
    sys.exit(1)
if errs:
    print("FAIL: unexpected errors", ids)
    sys.exit(1)
print("PASS: no error for instance-only field")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11551: fix `_check_list_display_item` so a field reachable only via a model instance (descriptor raising AttributeError on the class) still validates. Gold patch removes the `hasattr(obj.model, item)` gate and resolves via `_meta.get_field` first, falling back to `getattr(obj.model, item)`, emitting E108 only when both fail and E109 for M2M.

Probes (all HOLD on gold-patched tree):
- probe_1 (R2.1-2.3/R3, POSITIVE CONTROL): PositionField-style descriptor, hasattr(model,'field')=False; must NOT raise E108. HOLDS patched (errors=[]), VIOLATED at base (E108) => discriminates.
- probe_2 (R1.1/R1.3): callable entry -> no error AND get_field never called (spied). HOLDS.
- probe_3 (R1.2/R1.4): admin-object attribute -> no error AND get_field never called. HOLDS.
- probe_4 (R3.1/R3.2): nonexistent entry 'no_such' -> exactly one E108 with message containing item, admin class 'A', model 'admin.M'. HOLDS.
- probe_5 (R4.1/R4.2): M2M in _meta -> exactly one E109. HOLDS.
- probe_6 (R5.4): concrete IntegerField and model method a_method accepted (no error). HOLDS.
- probe_7 (R4.4): ManyToManyField reachable only via model-class attribute (not in _meta, resolved by getattr) -> exactly one E109, not E108. HOLDS.

Candidate wrong-fix patches (>=1 rejected required; both REJECTED by the suite):
- reject_noE108.diff: removes the E108 branch entirely (never rejects unresolvable entries; only handles _meta fields). REJECTED by probe_4 (nonexistent entry now yields [] instead of E108) and probe_7 (getattr M2M yields []).
- reject_partial_getattr.diff: resolves via _meta then getattr and emits E108 correctly, but omits the ManyToManyField check on the getattr-resolved path. Passes probes 1/4/5 but REJECTED by probe_7 (getattr-resolved M2M -> [] instead of E109), matching the exact secondary bug the requirements (R4.4) forbid.

All needed runs completed. 7 distinct probes hold on patched; positive control discriminates (patched HOLDS, base VIOLATED); >=1 candidate exercised and REJECTED. Suite discriminates wrong implementations. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces the `hasattr(obj.model, item)` gate with a try get_field -> except FieldDoesNotExist: try getattr -> except AttributeError: E108, followed by an unconditional isinstance(field, ManyToManyField) check. Requirements 1-5 accurately capture: (1) callable/admin-attr short-circuits with no field lookup; (2) metadata-first then getattr fallback, NOT gated on class attribute access; (3) E108 only when both routes fail; (4) E109 when resolved field is M2M via EITHER route (matches unconditional isinstance check, incl. R4.4 getattr route); (5) preserved aggregation/E107. The modeling boundary is the full changed control flow, not a narrow slice. Probe HOLDS on patched (exit 0), VIOLATED on base (E108 for the instance-only field).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md names the module/function under change (django.contrib.admin.checks, _check_list_display, _check_list_display_item), the get_field/getattr resolution order, FieldDoesNotExist/AttributeError handling, admin.E107/E108/E109 ids and messages, ManyToManyField, and the PositionField-descriptor-raising-AttributeError-on-class scenario. Every one of these is disclosed in the PUBLIC problem_statement, which literally contains the full proposed fix code, the exact error message strings, the E108/E109 ids, and an exhaustive 12-row logic table over hasattr/get_field/ManyToMany. The hidden test (test_valid_field_accessible_via_instance, its custom PositionField with __get__ raising AttributeError) is described only at the same conceptual level already present in the public statement. No hidden-only artifacts appear: no test function/class/file names or ids, no quoted test code, no fix-invented identifiers (the doc invents none beyond public ones), and the requirement enumerations describe behavior (resolve via metadata OR class attr; reject only when both fail) rather than mirroring the test parametrization. Localization + behavioral translation only.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
