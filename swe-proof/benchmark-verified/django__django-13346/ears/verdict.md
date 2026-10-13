# P2 adversarial audit — django__django-13346

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)

in_ids = sorted(JM.objects.filter(value__c__in=[14]).values_list('id', flat=True))
eq_ids = sorted(JM.objects.filter(value__c=14).values_list('id', flat=True))
expect = sorted([o_c14a.id, o_c14b.id])
print("in=%s eq=%s expect=%s" % (in_ids, eq_ids, expect))
ok = (in_ids == expect) and (in_ids == eq_ids)
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)
in_ids = sorted(JM.objects.filter(value__foo__in=['bar']).values_list('id', flat=True))
eq_ids = sorted(JM.objects.filter(value__foo='bar').values_list('id', flat=True))
print("in=%s eq=%s" % (in_ids, eq_ids))
ok = in_ids == eq_ids == [o_foobar.id]
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)
one = set(JM.objects.filter(value__c__in=[14]).values_list('id', flat=True))
two = set(JM.objects.filter(value__c__in=[14, 99]).values_list('id', flat=True))
expect_two = {o_c14a.id, o_c14b.id, o_c99.id}
print("one=%s two=%s expect_two=%s" % (sorted(one), sorted(two), sorted(expect_two)))
ok = one.issubset(two) and two == expect_two and one == {o_c14a.id, o_c14b.id}
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)
in_ids = sorted(JM.objects.filter(value__bar__in=[['foo', 'bar']]).values_list('id', flat=True))
eq_ids = sorted(JM.objects.filter(value__bar=['foo', 'bar']).values_list('id', flat=True))
print("in=%s eq=%s" % (in_ids, eq_ids))
ok = in_ids == eq_ids == [o_foobar.id]
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)
in_ids = sorted(JM.objects.filter(value__bax__in=[{'foo': 'bar'}, {'a': 'b'}]).values_list('id', flat=True))
eq_ids = sorted(JM.objects.filter(value__bax={'foo': 'bar'}).values_list('id', flat=True))
print("in=%s eq=%s" % (in_ids, eq_ids))
ok = in_ids == eq_ids == [o_foobar.id]
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)
in_ids = sorted(JM.objects.filter(value__0__in=[1]).values_list('id', flat=True))
eq_ids = sorted(JM.objects.filter(value__0=1).values_list('id', flat=True))
in2 = sorted(JM.objects.filter(value__0__in=[1, 3]).values_list('id', flat=True))
print("in=%s eq=%s in2=%s" % (in_ids, eq_ids, in2))
ok = in_ids == eq_ids == [o_arr1.id] and in2 == [o_arr1.id]
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)
from django.core.exceptions import FieldError
try:
    list(JM.objects.filter(value__c__in=[14]))
    registered = True
except FieldError as e:
    print("FieldError:", e); registered = False
eq_ids = sorted(JM.objects.filter(value__c=14).values_list('id', flat=True))
print("registered=%s eq=%s" % (registered, eq_ids))
ok = registered and eq_ids == sorted([o_c14a.id, o_c14b.id])
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)
ic = sorted(JM.objects.filter(value__foo__iregex=r'^BAR$').values_list('id', flat=True))
cs_wrong = sorted(JM.objects.filter(value__foo__regex=r'^BAR$').values_list('id', flat=True))
cs_right = sorted(JM.objects.filter(value__foo__regex=r'^bar$').values_list('id', flat=True))
print("iregex_BAR=%s regex_BAR=%s regex_bar=%s foobar_id=%s" % (ic, cs_wrong, cs_right, o_foobar.id))
ok = ic == [o_foobar.id] and cs_wrong == [] and cs_right == [o_foobar.id]
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)

in_ids = sorted(JM.objects.filter(value__c__in=[14]).values_list('id', flat=True))
eq_ids = sorted(JM.objects.filter(value__c=14).values_list('id', flat=True))
expect = sorted([o_c14a.id, o_c14b.id])
print("in=%s eq=%s expect=%s" % (in_ids, eq_ids, expect))
ok = (in_ids == expect) and (in_ids == eq_ids)
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13346: `__in` lookup on JSONField key/index transforms returned no rows on non-native-JSON backends because RHS values were compared against raw stored text instead of the extracted JSON value. Gold patch adds KeyTransformIn(lookups.In) overriding process_rhs to wrap RHS in JSON_EXTRACT/JSON_VALUE for sqlite/mysql/mariadb/oracle, and registers it on KeyTransform.

All probes run in the official Docker image on SQLite (has_native_json_field=False — the exact broken backend, so the non-native code path is genuinely exercised).

Probes (criterion -> observed patched / base / weak-candidate):
- probe_1 POSITIVE CONTROL, Req1.1/1.2/4/5: value__c__in=[14] returns exactly {c==14} and equals value__c=14. HOLDS patched / VIOLATED base / VIOLATED weak.
- probe_2 Req1.2: single-element string list value__foo__in=['bar'] == value__foo='bar'. HOLDS / VIOLATED / VIOLATED.
- probe_3 Req1.3: monotonic union — [14] subset of [14,99], multi returns union, never drops. HOLDS / VIOLATED / VIOLATED.
- probe_4 Req2.2: array candidate value__bar__in=[['foo','bar']]. HOLDS / VIOLATED / VIOLATED.
- probe_5 Req2.3: dict candidate value__bax__in=[{'foo':'bar'},{'a':'b'}]. HOLDS / VIOLATED / VIOLATED.
- probe_6 Req2.5: array-index transform value__0__in=[1] / [1,3]. HOLDS / VIOLATED / VIOLATED.
- probe_7 Req3.5/3.3: __in resolves as registered lookup (no FieldError) AND equality lookup unchanged. HOLDS patched / HOLDS base / HOLDS weak (regression criterion, holds everywhere by design).
- probe_8 Req3.1/3.2: iregex case-insensitive matches ^BAR$, regex case-sensitive rejects ^BAR$ but matches ^bar$. HOLDS / HOLDS / HOLDS (regression criterion).

Positive control (probe_1) FAILED at base and HOLDS patched -> discriminating power confirmed (prepatch reproduced).

Candidate patch 'naive_register_no_extract': the lazy fix a weak reading of Req3.5 permits — register a bare `class KeyTransformIn(lookups.In): pass` on KeyTransform without overriding process_rhs. It satisfies the 'registered lookup, no unsupported error' criterion (probe_7 HOLDS) and leaves regex regression intact (probe_8 HOLDS) but is REJECTED by all 6 behavioral membership probes (1-6) because RHS is still compared against raw stored text. This proves the probe suite discriminates the requirements-partial wrong fix; no TOO-WEAK finding.

>=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and a plausible wrong-fix candidate is rejected. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Reusable Django bootstrap + dataset. Probes exec this text at top.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection

class JM(models.Model):
    value = models.JSONField(null=True)
    class Meta:
        app_label = 'contenttypes'

HAS_NATIVE = connection.features.has_native_json_field
print("vendor=%s has_native_json_field=%s" % (connection.vendor, HAS_NATIVE))

with connection.schema_editor() as se:
    se.create_model(JM)

def mk(v):
    return JM.objects.create(value=v)

o_c14a = mk({'c': 14, 'd': 'x'})
o_c14b = mk({'c': 14, 'e': 'y'})
o_c99  = mk({'c': 99})
o_arr1 = mk([1, 2, 3])
o_arr9 = mk([9, 2, 3])
o_foobar = mk({'foo': 'bar', 'bar': ['foo', 'bar'], 'bax': {'foo': 'bar'}})
o_foobaz = mk({'foo': 'baz'})
o_none = mk(None)

in_ids = sorted(JM.objects.filter(value__c__in=[14]).values_list('id', flat=True))
eq_ids = sorted(JM.objects.filter(value__c=14).values_list('id', flat=True))
expect = sorted([o_c14a.id, o_c14b.id])
print("in=%s eq=%s expect=%s" % (in_ids, eq_ids, expect))
ok = (in_ids == expect) and (in_ids == eq_ids)
print("HOLDS" if ok else "VIOLATED")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13346: `__in` lookup on JSONField key/index transforms returned no rows on non-native-JSON backends because RHS values were compared against raw stored text instead of the extracted JSON value. Gold patch adds KeyTransformIn(lookups.In) overriding process_rhs to wrap RHS in JSON_EXTRACT/JSON_VALUE for sqlite/mysql/mariadb/oracle, and registers it on KeyTransform.

All probes run in the official Docker image on SQLite (has_native_json_field=False — the exact broken backend, so the non-native code path is genuinely exercised).

Probes (criterion -> observed patched / base / weak-candidate):
- probe_1 POSITIVE CONTROL, Req1.1/1.2/4/5: value__c__in=[14] returns exactly {c==14} and equals value__c=14. HOLDS patched / VIOLATED base / VIOLATED weak.
- probe_2 Req1.2: single-element string list value__foo__in=['bar'] == value__foo='bar'. HOLDS / VIOLATED / VIOLATED.
- probe_3 Req1.3: monotonic union — [14] subset of [14,99], multi returns union, never drops. HOLDS / VIOLATED / VIOLATED.
- probe_4 Req2.2: array candidate value__bar__in=[['foo','bar']]. HOLDS / VIOLATED / VIOLATED.
- probe_5 Req2.3: dict candidate value__bax__in=[{'foo':'bar'},{'a':'b'}]. HOLDS / VIOLATED / VIOLATED.
- probe_6 Req2.5: array-index transform value__0__in=[1] / [1,3]. HOLDS / VIOLATED / VIOLATED.
- probe_7 Req3.5/3.3: __in resolves as registered lookup (no FieldError) AND equality lookup unchanged. HOLDS patched / HOLDS base / HOLDS weak (regression criterion, holds everywhere by design).
- probe_8 Req3.1/3.2: iregex case-insensitive matches ^BAR$, regex case-sensitive rejects ^BAR$ but matches ^bar$. HOLDS / HOLDS / HOLDS (regression criterion).

Positive control (probe_1) FAILED at base and HOLDS patched -> discriminating power confirmed (prepatch reproduced).

Candidate patch 'naive_register_no_extract': the lazy fix a weak reading of Req3.5 permits — register a bare `class KeyTransformIn(lookups.In): pass` on KeyTransform without overriding process_rhs. It satisfies the 'registered lookup, no unsupported error' criterion (probe_7 HOLDS) and leaves regex regression intact (probe_8 HOLDS) but is REJECTED by all 6 behavioral membership probes (1-6) because RHS is still compared against raw stored text. This proves the probe suite discriminates the requirements-partial wrong fix; no TOO-WEAK finding.

>=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and a plausible wrong-fix candidate is rejected. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds KeyTransformIn(lookups.In) registered on KeyTransform, rewriting the __in RHS through JSON_EXTRACT/JSON_VALUE on non-native-JSON backends so comparison happens against the extracted value. Requirements pin exactly this changed observable boundary (membership equivalence to equality on key/index transforms, backend-independent) rather than the SQL-implementation slice. Note: instance FAIL_TO_PASS also lists test_key_iregex, but that test's fixtures merely happened to be added alongside; iregex behavior is unchanged base-vs-patched and Req3.1 correctly frames it as regression protection, not new behavior — so this is not an unfaithful over-claim. Probed on SQLite (a non-native-JSON backend, the bug's target). Oracle/MySQL/MariaDB branches not directly runnable but requirements make only backend-independence claims that the SQLite branch confirms and the equality-parity semantics are backend-agnostic.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes __in-on-JSON-key-transform behavior at the behavioral level and localizes the change to the public module django/db/models/fields/json.py (legitimate). None of the hidden-test artifacts appear: no test names (test_key_in, test_key_iregex), no test path, no parametrized values (14, 15, 'bar', 'baz', ['foo','bar'], {'foo':'bar'}, self.objs slices), and no fix-invented identifier (KeyTransformIn / process_rhs / JSON_EXTRACT / JSON_QUERY / JSON_VALUE / JSON_UNQUOTE). Requirement 2's scalar/array/object/array-index breakdown reflects natural JSON value types and the equality lookup's accepted types, not the specific parametrized cases. Requirement 3.4 enumerates lookups already registered in the public module (iexact/startswith/isnull/lt-gte etc.), which is regression scoping, not test transmission. Requirement 3.1 describes iregex behavior generically (iregex IS a FAIL_TO_PASS) but states behavior without the test's data/pattern. Single-element-list emphasis (Req 1.2) is already public in the problem_statement's [0]->0 rows example. Backend list (SQLite/MySQL/MariaDB/Oracle) is from problem_statement + gold vendor branches described as behavior, not code. Conclusion: behavioral translation, no reconstruction of hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
