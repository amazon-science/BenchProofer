# P2 adversarial audit — django__django-16950

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import uuid, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","probeapp"],
        USE_TZ=True,
    )
import sys, types
m = types.ModuleType("probeapp")
m.__file__ = "/testbed/probeapp.py"
m.__path__ = ["/testbed"]
sys.modules["probeapp"] = m
django.setup()
from django.db import models

class ParentWithUUIDAlternateKey(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"

class ChildRelatedViaAK(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentWithUUIDAlternateKey, models.CASCADE, to_field="uuid")
    class Meta: app_label = "probeapp"

class UUIDPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChild(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(UUIDPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

class AutoPKParent(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChildOfAutoPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(AutoPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

from django.forms.models import inlineformset_factory
from django.forms.models import inlineformset_factory
fs = inlineformset_factory(ParentWithUUIDAlternateKey, ChildRelatedViaAK, fields="__all__")
formset = fs({
    "childrelatedviaak_set-TOTAL_FORMS": 3,
    "childrelatedviaak_set-INITIAL_FORMS": 0,
    "childrelatedviaak_set-MAX_NUM_FORMS": "",
    "childrelatedviaak_set-0-name": "Test",
    "childrelatedviaak_set-1-name": "",
    "childrelatedviaak_set-2-name": "",
})
valid = formset.is_valid()
uuid_val = formset.instance.uuid
child_pid = formset.forms[0].instance.parent_id
print("valid=", valid, "instance.uuid=", uuid_val, "child.parent_id=", child_pid)
ok = valid and (uuid_val is not None) and (child_pid == uuid_val)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import uuid, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","probeapp"],
        USE_TZ=True,
    )
import sys, types
m = types.ModuleType("probeapp")
m.__file__ = "/testbed/probeapp.py"
m.__path__ = ["/testbed"]
sys.modules["probeapp"] = m
django.setup()
from django.db import models

class ParentWithUUIDAlternateKey(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"

class ChildRelatedViaAK(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentWithUUIDAlternateKey, models.CASCADE, to_field="uuid")
    class Meta: app_label = "probeapp"

class UUIDPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChild(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(UUIDPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

class AutoPKParent(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChildOfAutoPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(AutoPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

from django.forms.models import inlineformset_factory
from django.forms.models import inlineformset_factory
fs = inlineformset_factory(UUIDPKParent, UUIDPKChild, fields="__all__")
formset = fs({
    "uuidpkchild_set-TOTAL_FORMS": 3,
    "uuidpkchild_set-INITIAL_FORMS": 0,
    "uuidpkchild_set-MAX_NUM_FORMS": "",
    "uuidpkchild_set-0-name": "Foo",
    "uuidpkchild_set-1-name": "",
    "uuidpkchild_set-2-name": "",
})
valid = formset.is_valid()
uuid_val = formset.instance.uuid
child_pid = formset.forms[0].instance.parent_id
print("valid=", valid, "instance.uuid=", uuid_val, "child.parent_id=", child_pid)
ok = valid and (uuid_val is None) and (child_pid is None)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import uuid, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","probeapp"],
        USE_TZ=True,
    )
import sys, types
m = types.ModuleType("probeapp")
m.__file__ = "/testbed/probeapp.py"
m.__path__ = ["/testbed"]
sys.modules["probeapp"] = m
django.setup()
from django.db import models

class ParentWithUUIDAlternateKey(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"

class ChildRelatedViaAK(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentWithUUIDAlternateKey, models.CASCADE, to_field="uuid")
    class Meta: app_label = "probeapp"

class UUIDPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChild(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(UUIDPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

class AutoPKParent(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChildOfAutoPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(AutoPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

from django.forms.models import inlineformset_factory
from django.forms.models import inlineformset_factory
fs = inlineformset_factory(ParentWithUUIDAlternateKey, ChildRelatedViaAK, fields="__all__")
formset = fs()  # unbound: no submitted data
initial = formset.forms[0].fields["parent"].initial
uuid_val = formset.instance.uuid
print("parent.initial=", initial, "instance.uuid=", uuid_val)
ok = (initial is None) and (uuid_val is None)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import uuid, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","probeapp"],
        USE_TZ=True,
    )
import sys, types
m = types.ModuleType("probeapp")
m.__file__ = "/testbed/probeapp.py"
m.__path__ = ["/testbed"]
sys.modules["probeapp"] = m
django.setup()
from django.db import models

class ParentWithUUIDAlternateKey(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"

class ChildRelatedViaAK(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentWithUUIDAlternateKey, models.CASCADE, to_field="uuid")
    class Meta: app_label = "probeapp"

class UUIDPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChild(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(UUIDPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

class AutoPKParent(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChildOfAutoPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(AutoPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

from django.forms.models import inlineformset_factory
from django.forms.models import inlineformset_factory
sentinel = uuid.uuid4()
parent = ParentWithUUIDAlternateKey(uuid=sentinel, name="x")
parent._state.adding = False
fs = inlineformset_factory(ParentWithUUIDAlternateKey, ChildRelatedViaAK, fields="__all__")
formset = fs({
    "childrelatedviaak_set-TOTAL_FORMS": 1,
    "childrelatedviaak_set-INITIAL_FORMS": 0,
    "childrelatedviaak_set-MAX_NUM_FORMS": "",
    "childrelatedviaak_set-0-name": "Test",
}, instance=parent)
_ = formset.forms  # trigger add_fields
print("instance.uuid=", formset.instance.uuid, "sentinel=", sentinel)
sys.exit(0 if formset.instance.uuid == sentinel else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import uuid, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","probeapp"],
        USE_TZ=True,
    )
import sys, types
m = types.ModuleType("probeapp")
m.__file__ = "/testbed/probeapp.py"
m.__path__ = ["/testbed"]
sys.modules["probeapp"] = m
django.setup()
from django.db import models

class ParentWithUUIDAlternateKey(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"

class ChildRelatedViaAK(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentWithUUIDAlternateKey, models.CASCADE, to_field="uuid")
    class Meta: app_label = "probeapp"

class UUIDPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChild(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(UUIDPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

class AutoPKParent(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChildOfAutoPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(AutoPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

from django.forms.models import inlineformset_factory
from django.forms.models import inlineformset_factory
parent = AutoPKParent(name="x")
parent.pk = 4242  # adding state true (default), pk field AutoField has no default
fs = inlineformset_factory(AutoPKParent, UUIDPKChildOfAutoPKParent, fields="__all__")
formset = fs({
    "uuidpkchildofautopkparent_set-TOTAL_FORMS": 1,
    "uuidpkchildofautopkparent_set-INITIAL_FORMS": 0,
    "uuidpkchildofautopkparent_set-MAX_NUM_FORMS": "",
    "uuidpkchildofautopkparent_set-0-name": "Test",
}, instance=parent)
_ = formset.forms
print("adding=", parent._state.adding, "instance.pk=", formset.instance.pk)
sys.exit(0 if formset.instance.pk == 4242 else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import uuid, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","probeapp"],
        USE_TZ=True,
    )
import sys, types
m = types.ModuleType("probeapp")
m.__file__ = "/testbed/probeapp.py"
m.__path__ = ["/testbed"]
sys.modules["probeapp"] = m
django.setup()
from django.db import models

class ParentWithUUIDAlternateKey(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"

class ChildRelatedViaAK(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentWithUUIDAlternateKey, models.CASCADE, to_field="uuid")
    class Meta: app_label = "probeapp"

class UUIDPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChild(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(UUIDPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

class AutoPKParent(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChildOfAutoPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(AutoPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

from django.forms.models import inlineformset_factory
from django.forms.models import inlineformset_factory
fs = inlineformset_factory(ParentWithUUIDAlternateKey, ChildRelatedViaAK, fields="__all__")
formset = fs({
    "childrelatedviaak_set-TOTAL_FORMS": 3,
    "childrelatedviaak_set-INITIAL_FORMS": 0,
    "childrelatedviaak_set-MAX_NUM_FORMS": "",
    "childrelatedviaak_set-0-name": "Test",
    "childrelatedviaak_set-1-name": "",
    "childrelatedviaak_set-2-name": "",
})
valid = formset.is_valid()
uuid_val = formset.instance.uuid
child_pid = formset.forms[0].instance.parent_id
print("valid=", valid, "instance.uuid=", uuid_val, "child.parent_id=", child_pid)
ok = valid and (uuid_val is not None) and (child_pid == uuid_val)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16950: BaseInlineFormSet.add_fields must clear parent's linked key attr only when (adding AND field.has_default() AND (field is pk OR no form.data)). Probes built via inline model defs (ParentWithUUIDAlternateKey/ChildRelatedViaAK, UUIDPKParent/UUIDPKChild, AutoPKParent/UUIDPKChildOfAutoPKParent) mirroring the hidden test models.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): alternate to_field key w/ default + submitted data => instance.uuid preserved (non-None) AND child.parent_id == instance.uuid. HOLDS patched, VIOLATED at base (base sets uuid=None, child.parent_id=None) => discriminating.
- probe_2 (Req2.1): pk-with-default (UUIDPKParent) + data => instance.uuid set to None, child.parent_id None. HOLDS patched.
- probe_3 (Req2.2): alternate key, NO submitted data (unbound formset) => forms[0].fields['parent'].initial is None AND instance.uuid None. HOLDS patched.
- probe_4 (Req3.1): parent NOT adding (_state.adding=False) w/ alternate key+default+data => uuid unchanged (== sentinel). HOLDS patched.
- probe_5 (Req3.2): linked field has no default (AutoField pk) while adding => pk unchanged (4242). HOLDS patched.

Candidate wrong-fixes (both REJECTED by suite => discriminates):
- weak_A (`has_default() and not form.data`): drops pk-with-data clearing => probe_2 VIOLATED (Req2.1). Other probes hold.
- weak_B (`has_default() and attname==pk.name`): never clears alternate key even without data => probe_3 VIOLATED (Req2.2). Other probes hold.

No requirements-conforming alternative found: any patch satisfying probe_1 (preserve alt key w/ data), probe_2 (clear pk w/ data), probe_3 (clear alt key w/o data) must implement exactly the gold biconditional, matching the F2P/P2P behavior. Verdict SOUND: 5 distinct probes hold patched, positive control fails at base, >=1 candidate exercised and REJECTED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import uuid, django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","probeapp"],
        USE_TZ=True,
    )
import sys, types
m = types.ModuleType("probeapp")
m.__file__ = "/testbed/probeapp.py"
m.__path__ = ["/testbed"]
sys.modules["probeapp"] = m
django.setup()
from django.db import models

class ParentWithUUIDAlternateKey(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    class Meta: app_label = "probeapp"

class ChildRelatedViaAK(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentWithUUIDAlternateKey, models.CASCADE, to_field="uuid")
    class Meta: app_label = "probeapp"

class UUIDPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChild(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(UUIDPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

class AutoPKParent(models.Model):
    name = models.CharField(max_length=255)
    class Meta: app_label = "probeapp"

class UUIDPKChildOfAutoPKParent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(AutoPKParent, models.CASCADE)
    class Meta: app_label = "probeapp"

from django.forms.models import inlineformset_factory
from django.forms.models import inlineformset_factory
fs = inlineformset_factory(ParentWithUUIDAlternateKey, ChildRelatedViaAK, fields="__all__")
formset = fs({
    "childrelatedviaak_set-TOTAL_FORMS": 3,
    "childrelatedviaak_set-INITIAL_FORMS": 0,
    "childrelatedviaak_set-MAX_NUM_FORMS": "",
    "childrelatedviaak_set-0-name": "Test",
    "childrelatedviaak_set-1-name": "",
    "childrelatedviaak_set-2-name": "",
})
valid = formset.is_valid()
uuid_val = formset.instance.uuid
child_pid = formset.forms[0].instance.parent_id
print("valid=", valid, "instance.uuid=", uuid_val, "child.parent_id=", child_pid)
ok = valid and (uuid_val is not None) and (child_pid == uuid_val)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16950: BaseInlineFormSet.add_fields must clear parent's linked key attr only when (adding AND field.has_default() AND (field is pk OR no form.data)). Probes built via inline model defs (ParentWithUUIDAlternateKey/ChildRelatedViaAK, UUIDPKParent/UUIDPKChild, AutoPKParent/UUIDPKChildOfAutoPKParent) mirroring the hidden test models.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): alternate to_field key w/ default + submitted data => instance.uuid preserved (non-None) AND child.parent_id == instance.uuid. HOLDS patched, VIOLATED at base (base sets uuid=None, child.parent_id=None) => discriminating.
- probe_2 (Req2.1): pk-with-default (UUIDPKParent) + data => instance.uuid set to None, child.parent_id None. HOLDS patched.
- probe_3 (Req2.2): alternate key, NO submitted data (unbound formset) => forms[0].fields['parent'].initial is None AND instance.uuid None. HOLDS patched.
- probe_4 (Req3.1): parent NOT adding (_state.adding=False) w/ alternate key+default+data => uuid unchanged (== sentinel). HOLDS patched.
- probe_5 (Req3.2): linked field has no default (AutoField pk) while adding => pk unchanged (4242). HOLDS patched.

Candidate wrong-fixes (both REJECTED by suite => discriminates):
- weak_A (`has_default() and not form.data`): drops pk-with-data clearing => probe_2 VIOLATED (Req2.1). Other probes hold.
- weak_B (`has_default() and attname==pk.name`): never clears alternate key even without data => probe_3 VIOLATED (Req2.2). Other probes hold.

No requirements-conforming alternative found: any patch satisfying probe_1 (preserve alt key w/ data), probe_2 (clear pk w/ data), probe_3 (clear alt key w/o data) must implement exactly the gold biconditional, matching the F2P/P2P behavior. Verdict SOUND: 5 distinct probes hold patched, positive control fails at base, >=1 candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds a guard: clear parent linked-key iff to_field.has_default() and (to_field.attname == fk.remote_field.model._meta.pk.name OR not form.data), inside the pre-existing self.instance._state.adding block. Probe on the instance image (patched tree, exit 0): (A) alternate-key UUIDField default + form data present -> uuid PRESERVED, forms[0].instance.parent_id == instance.uuid (matches Req 1.1/1.2); (B) alternate key + no form data -> parent field initial is None i.e. cleared (matches Req 2.2). Base tree (unpatched) VIOLATED: uuid was cleared even with form data -> confirms this is the changed behavior. Requirement mapping: Req1<->form-data-present preserve; Req2.1<->pk-disjunct clear; Req2.2<->not-form.data-disjunct clear for both pk and alt; Req2.3 is a verbatim biconditional of the patch condition (adding & has_default & (is_pk | no_data)); Req3.1<->outer _state.adding guard; Req3.2<->has_default() guard; Req3.3<->to_field resolution via get_field(to_field) else _meta.pk and 'is pk' judged by attname==pk.name (exact code). No divergence between requirements and patched behavior; boundary is the changed decision, not a slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally: it names the module/function/attributes involved (add_fields, django/forms/models.py, to_field, primary key) — legitimate localization — and translates the gold boolean condition (to_field.has_default() AND (attname==pk.name OR not form.data)) into EARS acceptance criteria, which is the intended purpose. No hidden-test content leaks: the test file path (tests/model_formsets/test_uuid.py), method names, fixture classes (ParentWithUUIDAlternateKey, ChildRelatedViaAK), the concrete attributes (uuid, parent_id), and the 3-form TOTAL_FORMS parametrization are all ABSENT. The UUIDField/default=uuid.uuid4/editable=False/unique=True details are public via the problem_statement's UUIDModel example, not test-derived. No case enumeration mirrors the parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
