# P2 adversarial audit — django__django-16801

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
"""Positive control / Req 1.1 & 1.2 & 1.3:
An ImageField with NO width_field/height_field on a concrete model must NOT
register a post_init receiver whose sender is that model.
HOLDS on patched, FAILS at base.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models
from django.db.models import signals


class NoDim(models.Model):
    mugshot = models.ImageField(upload_to="x")

    class Meta:
        app_label = "auth"


sender_ids = [sid for (_, sid), *_ in signals.post_init.receivers]
connected = id(NoDim) in sender_ids
print("NoDim in post_init senders:", connected)
print("total post_init receivers:", len(signals.post_init.receivers))
# criterion: NOT connected
raise SystemExit(0 if not connected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 2.2: ImageField that configures width_field AND/OR height_field on
a concrete model MUST register a post_init receiver whose sender is that model.
Tests both (a) both fields, and (b) only one field configured.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True, DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models
from django.db.models import signals


class Both(models.Model):
    w = models.IntegerField(null=True)
    h = models.IntegerField(null=True)
    mugshot = models.ImageField(upload_to="x", width_field="w", height_field="h")
    class Meta:
        app_label = "auth"


class WidthOnly(models.Model):
    w = models.IntegerField(null=True)
    mugshot = models.ImageField(upload_to="x", width_field="w")
    class Meta:
        app_label = "auth"


class HeightOnly(models.Model):
    h = models.IntegerField(null=True)
    mugshot = models.ImageField(upload_to="x", height_field="h")
    class Meta:
        app_label = "auth"


sender_ids = [sid for (_, sid), *_ in signals.post_init.receivers]
ok = True
for m in (Both, WidthOnly, HeightOnly):
    conn = id(m) in sender_ids
    print(m.__name__, "registered:", conn)
    ok = ok and conn
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1: Abstract model with a configured ImageField must NOT get a post_init
receiver bound to the abstract model. Also its concrete subclass MUST get one.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True, DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models
from django.db.models import signals


class AbstractPerson(models.Model):
    h = models.IntegerField(null=True)
    mugshot = models.ImageField(upload_to="x", height_field="h")
    class Meta:
        app_label = "auth"
        abstract = True


class Concrete(AbstractPerson):
    class Meta:
        app_label = "auth"


sender_ids = [sid for (_, sid), *_ in signals.post_init.receivers]
abstract_conn = id(AbstractPerson) in sender_ids
concrete_conn = id(Concrete) in sender_ids
print("abstract registered:", abstract_conn, "(must be False)")
print("concrete registered:", concrete_conn, "(must be True)")
raise SystemExit(0 if (not abstract_conn and concrete_conn) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 4.1,4.3,4.4,4.8: dimension syncing for a configured field.
- constructor with image value sets width/height (4.1)
- assignment via descriptor updates dims with force (4.3, 4.8)
- assigning None clears dims (4.4)
- update_dimension_fields with force on a NO-dimension field makes no change,
  raises no error (4.8 tail).
Uses an in-memory sqlite + real PNG bytes via Pillow.
"""
import io, tempfile, os
import django
from django.conf import settings

tmpd = tempfile.mkdtemp()
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    MEDIA_ROOT=tmpd,
)
django.setup()

from django.db import models, connection
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image

storage = FileSystemStorage(location=tmpd)


class Pic(models.Model):
    w = models.IntegerField(null=True)
    h = models.IntegerField(null=True)
    mugshot = models.ImageField(storage=storage, upload_to="t",
                                width_field="w", height_field="h", blank=True)
    class Meta:
        app_label = "auth"


class NoDim(models.Model):
    mugshot = models.ImageField(storage=storage, upload_to="t", blank=True)
    class Meta:
        app_label = "auth"


with connection.schema_editor() as se:
    se.create_model(Pic)
    se.create_model(NoDim)


def png_bytes(w, h):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (1, 2, 3)).save(buf, "PNG")
    return buf.getvalue()


ok = True

# 4.3 assignment via descriptor with a real image -> dims updated
p = Pic()
p.mugshot = ContentFile(png_bytes(24, 42), name="a.png")
print("after assign:", p.w, p.h)
if (p.w, p.h) != (24, 42):
    ok = False; print("FAIL assign dims")

# 4.4 assign None clears
p.mugshot = None
print("after None:", p.w, p.h)
if (p.w, p.h) != (None, None):
    ok = False; print("FAIL None clear")

# 4.1 constructor with image value
p2 = Pic(mugshot=ContentFile(png_bytes(11, 7), name="b.png"))
print("constructor:", p2.w, p2.h)
if (p2.w, p2.h) != (11, 7):
    ok = False; print("FAIL constructor dims")

# 4.8 tail: update_dimension_fields force on no-dim field: no error, no attr
nd = NoDim()
try:
    nd._meta.get_field("mugshot").update_dimension_fields(nd, force=True)
    print("no-dim force ok")
except Exception as e:
    ok = False; print("FAIL no-dim force raised:", e)

raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.6 & 4.7: DB-load preserves populated dims (no recompute); deferred
field forces no load & no change.
- 4.6: instance loaded from DB with dims already populated -> not recomputed
  (even if we store wrong dims, they are kept, not overwritten from the file).
- 4.7: deferred image attr (attname not in __dict__) -> handler no-ops and does
  NOT force-load the field.
"""
import io, tempfile
import django
from django.conf import settings

tmpd = tempfile.mkdtemp()
settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    MEDIA_ROOT=tmpd,
)
django.setup()

from django.db import models, connection
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image

storage = FileSystemStorage(location=tmpd)


class Pic(models.Model):
    w = models.IntegerField(null=True)
    h = models.IntegerField(null=True)
    mugshot = models.ImageField(storage=storage, upload_to="t",
                                width_field="w", height_field="h", blank=True)
    class Meta:
        app_label = "auth"


with connection.schema_editor() as se:
    se.create_model(Pic)


def png_bytes(w, h):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (9, 9, 9)).save(buf, "PNG")
    return buf.getvalue()


ok = True

p = Pic()
p.mugshot = ContentFile(png_bytes(30, 40), name="c.png")
p.mugshot.save("c.png", ContentFile(png_bytes(30, 40)), save=False)
# deliberately store WRONG dims to detect recompute-on-load
p.w = 999
p.h = 888
p.save()
pk = p.pk

# 4.6: full load; dims must remain the DB-stored (wrong) values, not recomputed
loaded = Pic.objects.get(pk=pk)
print("loaded dims:", loaded.w, loaded.h)
if (loaded.w, loaded.h) != (999, 888):
    ok = False; print("FAIL 4.6 recomputed on load")

# 4.7: deferred mugshot -> handler no-op, no forced load
deferred = Pic.objects.defer("mugshot").get(pk=pk)
has_attr = "mugshot" in deferred.__dict__
print("deferred: mugshot in __dict__ =", has_attr, " dims:", deferred.w, deferred.h)
if has_attr:
    ok = False; print("FAIL 4.7 forced load of deferred field")
if (deferred.w, deferred.h) != (999, 888):
    ok = False; print("FAIL 4.7 dims changed on deferred load")

raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.1 & 1.2 & 1.3:
An ImageField with NO width_field/height_field on a concrete model must NOT
register a post_init receiver whose sender is that model.
HOLDS on patched, FAILS at base.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models
from django.db.models import signals


class NoDim(models.Model):
    mugshot = models.ImageField(upload_to="x")

    class Meta:
        app_label = "auth"


sender_ids = [sid for (_, sid), *_ in signals.post_init.receivers]
connected = id(NoDim) in sender_ids
print("NoDim in post_init senders:", connected)
print("total post_init receivers:", len(signals.post_init.receivers))
# criterion: NOT connected
raise SystemExit(0 if not connected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16801: ImageField should only connect its post_init update_dimension_fields handler when width_field OR height_field is configured (and model non-abstract).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2/1.3, POSITIVE CONTROL): concrete model, ImageField with no width/height field => model id NOT among post_init receiver senders. HOLDS patched (0 receivers), FAILS at base (VIOLATED: 1 receiver, model connected). Discriminates.
- probe_2 (Req 2.1/2.2): concrete models with both fields / width-only / height-only each MUST register a post_init receiver. HOLDS patched.
- probe_3 (Req 3.1): abstract model with configured height_field NOT registered; its concrete subclass IS registered. HOLDS patched.
- probe_4 (Req 4.1/4.3/4.4/4.8): descriptor assignment sets dims (24,42); assign None clears (None,None); constructor sets dims (11,7); update_dimension_fields(force=True) on a no-dimension field is a no-op raising no error. HOLDS patched.
- probe_5 (Req 4.6/4.7): full DB load keeps stored (deliberately wrong 999/888) dims => no recompute; deferred('mugshot') load leaves mugshot absent from __dict__ and dims unchanged => no forced load. HOLDS patched.

Candidate wrong-fix (weak.diff): uses `self.width_field AND self.height_field` instead of `OR`. REJECTED by the suite: probe_2 VIOLATED (WidthOnly/HeightOnly not registered => Req 2.2 broken) and probe_3 VIOLATED (concrete single-field subclass not registered). This is the naive misreading and the suite discriminates it. No requirements-conforming candidate found that would fail the hidden tests.

>=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and rejected. Verdict SOUND.

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
"""Positive control / Req 1.1 & 1.2 & 1.3:
An ImageField with NO width_field/height_field on a concrete model must NOT
register a post_init receiver whose sender is that model.
HOLDS on patched, FAILS at base.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DEFAULT_AUTO_FIELD="django.db.models.AutoField",
)
django.setup()

from django.db import models
from django.db.models import signals


class NoDim(models.Model):
    mugshot = models.ImageField(upload_to="x")

    class Meta:
        app_label = "auth"


sender_ids = [sid for (_, sid), *_ in signals.post_init.receivers]
connected = id(NoDim) in sender_ids
print("NoDim in post_init senders:", connected)
print("total post_init receivers:", len(signals.post_init.receivers))
# criterion: NOT connected
raise SystemExit(0 if not connected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16801: ImageField should only connect its post_init update_dimension_fields handler when width_field OR height_field is configured (and model non-abstract).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.2/1.3, POSITIVE CONTROL): concrete model, ImageField with no width/height field => model id NOT among post_init receiver senders. HOLDS patched (0 receivers), FAILS at base (VIOLATED: 1 receiver, model connected). Discriminates.
- probe_2 (Req 2.1/2.2): concrete models with both fields / width-only / height-only each MUST register a post_init receiver. HOLDS patched.
- probe_3 (Req 3.1): abstract model with configured height_field NOT registered; its concrete subclass IS registered. HOLDS patched.
- probe_4 (Req 4.1/4.3/4.4/4.8): descriptor assignment sets dims (24,42); assign None clears (None,None); constructor sets dims (11,7); update_dimension_fields(force=True) on a no-dimension field is a no-op raising no error. HOLDS patched.
- probe_5 (Req 4.6/4.7): full DB load keeps stored (deliberately wrong 999/888) dims => no recompute; deferred('mugshot') load leaves mugshot absent from __dict__ and dims unchanged => no forced load. HOLDS patched.

Candidate wrong-fix (weak.diff): uses `self.width_field AND self.height_field` instead of `OR`. REJECTED by the suite: probe_2 VIOLATED (WidthOnly/HeightOnly not registered => Req 2.2 broken) and probe_3 VIOLATED (concrete single-field subclass not registered). This is the naive misreading and the suite discriminates it. No requirements-conforming candidate found that would fail the hidden tests.

>=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch changes two spots in django/db/models/fields/files.py: (1) contribute_to_class now guards signals.post_init.connect on `not cls._meta.abstract and (self.width_field or self.height_field)`; (2) update_dimension_fields drops the `has_dimension_fields` early-return, keeping only the deferred guard `if self.attname not in instance.__dict__`. Requirements 1-3 correctly model the new connection boundary (concrete AND at least one non-empty dim field; abstract never). Requirement 4 preserves the dimension-syncing semantics; 4.8 correctly captures that the handler now handles the no-dim-field case gracefully via the per-field setattr guards. F2P test is test_post_init_not_connected, matching Req1. All probes returned exit 0 (HOLDS) on the patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document names only public API surfaces (ImageField, contribute_to_class, update_dimension_fields, post_init signal, width_field/height_field) — all present in the public problem_statement, which explicitly states the post_init handler is a no-op when width_field/height_field are unset and should be removed. Requirement 1 (esp. criteria 1-2, 'model SHALL NOT appear as the sender of any post_init receiver') translates the hidden test's assertion into a behavioral requirement — this is the legitimate spec-writing task, not transmission of the test. No verbatim/near-verbatim test code, no test file path (tests/model_fields/test_imagefield.py), no test function/class names (test_post_init_not_connected, ImageFieldNoDimensionsTests), no parametrization ids, no quoted gold-patch lines, and no fix-invented identifiers appear. The gold patch introduces no new identifiers (it only adds a boolean condition on existing attributes), so there is nothing invented to leak. Req 4/5 enumerations describe behavioral preservation scenarios (dimension syncing, pickling, equality, deferred loading) as behavior; they align with PASS_TO_PASS coverage but are phrased as requirements, not test ids, and follow naturally from 'preserve existing behavior' — not a reconstruction of the parametrization. The single FAIL_TO_PASS (post_init not connected) is expressed behaviorally, not as test-shaped code.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
