# P2 adversarial audit — django__django-16899

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
# Positive control. Req1 crit 1,2,3,4: exactly one admin.E035, message names the
# offending value verbatim via "refers to '<value>', which is not a callable,..."
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Song(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        app_label = "probeapp"

class SongAdmin(admin.ModelAdmin):
    readonly_fields = ("title", "nonexistent")

errors = SongAdmin(Song, AdminSite()).check()
print("errors:", [(e.id, e.msg) for e in errors])
assert len(errors) == 1, "expected exactly one error"
e = errors[0]
assert e.id == "admin.E035", e.id
msg = e.msg
# offending value present verbatim
assert "'nonexistent'" in msg, "offending value not in message"
# 'refers to' construction, value after label
assert "refers to 'nonexistent'" in msg, "missing refers-to construction"
assert "which is not a callable" in msg, "missing 'which is not a callable'"
# positional label present and before the value
assert "readonly_fields[1]" in msg, "missing positional label"
assert msg.index("readonly_fields[1]") < msg.index("refers to 'nonexistent'")
# admin class name and model label
assert "'SongAdmin'" in msg and "'probeapp.Song'" in msg, msg
print("OK probe_1")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class State(models.Model):
    class Meta: app_label = "probeapp"
class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    class Meta: app_label = "probeapp"

class CityInline(admin.TabularInline):
    model = City
    readonly_fields = ["i_dont_exist"]

errors = CityInline(State, AdminSite()).check()
print("errors:", [(e.id, e.msg) for e in errors])
assert len(errors) == 1 and errors[0].id == "admin.E035"
msg = errors[0].msg
assert "readonly_fields[0]" in msg
assert "refers to 'i_dont_exist'" in msg, msg
assert "'CityInline'" in msg, "inline class name missing"
assert "'probeapp.City'" in msg, "bound model label missing"
print("OK probe_2")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Song(models.Model):
    title = models.CharField(max_length=100)
    class Meta: app_label = "probeapp"

class SongAdmin(admin.ModelAdmin):
    readonly_fields = ("bad_one", "title", "bad_two")

errors = SongAdmin(Song, AdminSite()).check()
msgs = [e.msg for e in errors]
print("errors:", [(e.id, e.msg) for e in errors])
assert all(e.id == "admin.E035" for e in errors)
assert len(errors) == 2, "expected two errors (title is valid)"
# each cites own label and own value
assert any("readonly_fields[0]" in m and "refers to 'bad_one'" in m for m in msgs), msgs
assert any("readonly_fields[2]" in m and "refers to 'bad_two'" in m for m in msgs), msgs
print("OK probe_3")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Song(models.Model):
    title = models.CharField(max_length=100)
    def model_method(self): return "x"
    class Meta: app_label = "probeapp"

def a_callable(obj): return "y"

class SongAdmin(admin.ModelAdmin):
    readonly_fields = (a_callable, "admin_method", "model_method", "title")
    def admin_method(self, obj): return "z"

errors = SongAdmin(Song, AdminSite()).check()
print("errors:", [(e.id, e.msg) for e in errors])
# no E035 for any of these valid entries
assert [e for e in errors if e.id == "admin.E035"] == [], "spurious E035"
print("OK probe_4")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Song(models.Model):
    title = models.CharField(max_length=100)
    class Meta: app_label = "probeapp"

class SongAdmin(admin.ModelAdmin):
    readonly_fields = "test"  # not a list/tuple

errors = SongAdmin(Song, AdminSite()).check()
print("errors:", [(e.id, e.msg) for e in errors])
assert len(errors) == 1, errors
e = errors[0]
assert e.id == "admin.E034", e.id
assert "must be a list or tuple" in e.msg, e.msg
# the per-item resolution wording must NOT appear here
assert "refers to" not in e.msg, e.msg
print("OK probe_5")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Song(models.Model):
    title = models.CharField(max_length=100)
    class Meta: app_label = "probeapp"

class SongAdmin(admin.ModelAdmin):
    readonly_fields = ("title", "nonexistent")

errors = SongAdmin(Song, AdminSite()).check()
msg = errors[0].msg
print("msg:", msg)
# ordering: label, then value, then 'not a callable', then admin class, then model
i_label = msg.index("readonly_fields[1]")
i_val = msg.index("'nonexistent'")
i_call = msg.index("not a callable")
i_admin = msg.index("'SongAdmin'")
i_model = msg.index("'probeapp.Song'")
assert i_label < i_val < i_call < i_admin < i_model, (i_label,i_val,i_call,i_admin,i_model)
# single sentence: exactly one period at the end
assert msg.rstrip().endswith("."), msg
assert msg.count(".") >= 1
print("OK probe_6")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control. Req1 crit 1,2,3,4: exactly one admin.E035, message names the
# offending value verbatim via "refers to '<value>', which is not a callable,..."
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Song(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        app_label = "probeapp"

class SongAdmin(admin.ModelAdmin):
    readonly_fields = ("title", "nonexistent")

errors = SongAdmin(Song, AdminSite()).check()
print("errors:", [(e.id, e.msg) for e in errors])
assert len(errors) == 1, "expected exactly one error"
e = errors[0]
assert e.id == "admin.E035", e.id
msg = e.msg
# offending value present verbatim
assert "'nonexistent'" in msg, "offending value not in message"
# 'refers to' construction, value after label
assert "refers to 'nonexistent'" in msg, "missing refers-to construction"
assert "which is not a callable" in msg, "missing 'which is not a callable'"
# positional label present and before the value
assert "readonly_fields[1]" in msg, "missing positional label"
assert msg.index("readonly_fields[1]") < msg.index("refers to 'nonexistent'")
# admin class name and model label
assert "'SongAdmin'" in msg and "'probeapp.Song'" in msg, msg
print("OK probe_1")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16899: gold patch changes the admin.E035 readonly_fields item error text to name the offending value via the "refers to '<value>', which is not a callable, an attribute of '<Admin>', or an attribute of '<model.label>'." construction.

Probes (all run in the official image; runner re-runs):
- probe_1 (Req1 c1-4, POSITIVE CONTROL): exactly one admin.E035; message contains offending value verbatim, uses 'refers to <value>' before 'which is not a callable', label precedes value, names admin class + model label. HOLDS patched; FAILS at base (old text lacks the value). Discriminates.
- probe_2 (Req1 c5): inline admin (CityInline/State bound model City) — message names inline class name 'CityInline' and bound model 'probeapp.City' with the refers-to construction. HOLDS patched.
- probe_3 (Req1 c6): three-entry readonly_fields (bad_one, title, bad_two) -> exactly two E035, each citing its own label ([0]/[2]) and its own value. HOLDS patched.
- probe_4 (Req2 c1-4): callable, admin method, model method, declared field all accepted -> no E035. HOLDS patched.
- probe_5 (Req3 c3): non-list/tuple readonly_fields keeps its distinct admin.E034 'must be a list or tuple' diagnostic, without the refers-to wording. HOLDS patched.
- probe_6 (Req1 c3): strict single-sentence ordering label<value<'not a callable'<admin class<model label; ends with a period. HOLDS patched.

All 6 HOLD on the gold-patched tree; positive control (probe_1) FAILS at base -> discriminating power confirmed.

Candidate wrong-fix (weak.diff, applies at base_commit): appends the value as a trailing parenthetical '(offending value: '<v>')' instead of using the mandated 'refers to <value>, which is not...' construction / ordering. This is a requirements-VIOLATING lazy fix. Probes REJECT it: probe_1 (no 'refers to <value>'), probe_2 (same), probe_3 (VIOLATED, wrong text), probe_6 (ordering value after model label). It would also fail the hidden tests, which assert the exact expected message string. probes 4/5 correctly still hold (acceptance + container diagnostic unchanged). Thus the suite discriminates wrong implementations; no requirements-conforming alternative that fails the hidden tests was found -> not TOO WEAK. Verdict SOUND.

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
# Positive control. Req1 crit 1,2,3,4: exactly one admin.E035, message names the
# offending value verbatim via "refers to '<value>', which is not a callable,..."
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth","django.contrib.admin",
        "django.contrib.sessions","django.contrib.messages"], MIDDLEWARE=[],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField")
django.setup()
from django.db import models
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

class Song(models.Model):
    title = models.CharField(max_length=100)
    class Meta:
        app_label = "probeapp"

class SongAdmin(admin.ModelAdmin):
    readonly_fields = ("title", "nonexistent")

errors = SongAdmin(Song, AdminSite()).check()
print("errors:", [(e.id, e.msg) for e in errors])
assert len(errors) == 1, "expected exactly one error"
e = errors[0]
assert e.id == "admin.E035", e.id
msg = e.msg
# offending value present verbatim
assert "'nonexistent'" in msg, "offending value not in message"
# 'refers to' construction, value after label
assert "refers to 'nonexistent'" in msg, "missing refers-to construction"
assert "which is not a callable" in msg, "missing 'which is not a callable'"
# positional label present and before the value
assert "readonly_fields[1]" in msg, "missing positional label"
assert msg.index("readonly_fields[1]") < msg.index("refers to 'nonexistent'")
# admin class name and model label
assert "'SongAdmin'" in msg and "'probeapp.Song'" in msg, msg
print("OK probe_1")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16899: gold patch changes the admin.E035 readonly_fields item error text to name the offending value via the "refers to '<value>', which is not a callable, an attribute of '<Admin>', or an attribute of '<model.label>'." construction.

Probes (all run in the official image; runner re-runs):
- probe_1 (Req1 c1-4, POSITIVE CONTROL): exactly one admin.E035; message contains offending value verbatim, uses 'refers to <value>' before 'which is not a callable', label precedes value, names admin class + model label. HOLDS patched; FAILS at base (old text lacks the value). Discriminates.
- probe_2 (Req1 c5): inline admin (CityInline/State bound model City) — message names inline class name 'CityInline' and bound model 'probeapp.City' with the refers-to construction. HOLDS patched.
- probe_3 (Req1 c6): three-entry readonly_fields (bad_one, title, bad_two) -> exactly two E035, each citing its own label ([0]/[2]) and its own value. HOLDS patched.
- probe_4 (Req2 c1-4): callable, admin method, model method, declared field all accepted -> no E035. HOLDS patched.
- probe_5 (Req3 c3): non-list/tuple readonly_fields keeps its distinct admin.E034 'must be a list or tuple' diagnostic, without the refers-to wording. HOLDS patched.
- probe_6 (Req1 c3): strict single-sentence ordering label<value<'not a callable'<admin class<model label; ends with a period. HOLDS patched.

All 6 HOLD on the gold-patched tree; positive control (probe_1) FAILS at base -> discriminating power confirmed.

Candidate wrong-fix (weak.diff, applies at base_commit): appends the value as a trailing parenthetical '(offending value: '<v>')' instead of using the mandated 'refers to <value>, which is not...' construction / ordering. This is a requirements-VIOLATING lazy fix. Probes REJECT it: probe_1 (no 'refers to <value>'), probe_2 (same), probe_3 (VIOLATED, wrong text), probe_6 (ordering value after model label). It would also fail the hidden tests, which assert the exact expected message string. probes 4/5 correctly still hold (acceptance + container diagnostic unchanged). Thus the suite discriminates wrong implementations; no requirements-conforming alternative that fails the hidden tests was found -> not TOO WEAK. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correctly pinned to the changed observable behavior (error message content/ordering), not a narrow slice. No requirement forbids behavior the code has, mandates behavior it lacks, or invents behavior. Requirements referencing 'attribute of the bound model' vs a distinct 'declared field' are consistent: the code catches FieldDoesNotExist so the emitted message groups them under 'attribute of <model label>', which the requirements describe accurately (message names admin class and model label; resolution logic that distinguishes field vs attribute is unchanged and not misdescribed). Verdict: FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the readonly_fields E035 message change purely at the behavioral level. Every seemingly specific detail is already public in the problem_statement: the old message text ("...is not a callable, an attribute of 'CityInline', or an attribute of 'admin_checks.City'."), the target "refers to '<value>', which is not ..." construction (shown for list_editable), the error id admin.E035, and the readonly_fields/list_editable/list_display/raw_id_fields comparison. Naming _check_readonly_fields_item and django/contrib/admin/checks.py is legitimate localization. No hidden-test artifacts leak: the test names (test_nonexistent_field, test_nonexistent_field_on_inline), test class (SystemChecksTestCase), fixture admin/model names (SongAdmin, CityInline, Song, City), and the specific offending values ('nonexistent', 'i_dont_exist') do NOT appear. Req 1.3's message-part enumeration decomposes the already-public message string, not the test parametrization. No gold-patch-invented identifiers exist (the fix only edits message text). No leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
