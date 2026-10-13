# P2 adversarial audit — django__django-13033

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
# R1.1 + R1.2 + R1.3 (POSITIVE CONTROL):
# Ordering by a multi-segment lookup whose final segment names the FK's stored
# attribute (record__root_id) SHALL order directly by that stored column,
# ascending, and SHALL NOT introduce the extra join that expanding the related
# model's default ordering requires. HOLDS patched; FAILS at base (base expands
# OneModel.Meta.ordering=("-id",) => id DESC + an extra join).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

class TwoModel(models.Model):
    class Meta:
        app_label = "probeapp"
    id = models.BigAutoField(primary_key=True)
    record = models.ForeignKey(OneModel, on_delete=models.CASCADE)
    twoval = models.BigIntegerField(null=True)

sql = str(TwoModel.objects.order_by("record__root_id").query)
njoin = sql.upper().count(" JOIN ")
order = sql.split("ORDER BY")[-1].strip()
print("SQL:", sql)
print("joins=%d order=%r" % (njoin, order))

ok = True
# Direct order by the root_id stored column, ascending
if 'ROOT_ID" ASC' not in order.upper():
    print("FAIL: order is not root_id ASC"); ok = False
# Must NOT have inherited the related model's DESC default direction
if "DESC" in order.upper():
    print("FAIL: order contains DESC (inherited default ordering)"); ok = False
# Must NOT introduce the extra join that default-ordering expansion needs.
# Direct-column ordering needs exactly 1 join (record -> OneModel to reach root_id);
# expansion would add a second join (root -> OneModel).
if njoin >= 2:
    print("FAIL: extra join present (default ordering expanded)"); ok = False
print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.4: descending request (leading '-') on the same final-segment lookup SHALL
# be descending on the designated stored column, regardless of related default.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

class TwoModel(models.Model):
    class Meta:
        app_label = "probeapp"
    id = models.BigAutoField(primary_key=True)
    record = models.ForeignKey(OneModel, on_delete=models.CASCADE)
    twoval = models.BigIntegerField(null=True)

sql = str(TwoModel.objects.order_by("-record__root_id").query)
njoin = sql.upper().count(" JOIN ")
order = sql.split("ORDER BY")[-1].strip()
print("SQL:", sql)
print("joins=%d order=%r" % (njoin, order))
ok = True
if 'ROOT_ID" DESC' not in order.upper():
    print("FAIL: not root_id DESC"); ok = False
if "ASC" in order.upper():
    print("FAIL: order contains ASC"); ok = False
if njoin >= 2:
    print("FAIL: extra join present"); ok = False
print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.5: self-referential FK. Ordering OneModel by root__root_id (final segment
# names the FK's stored attribute) SHALL order directly by that stored column
# ascending and SHALL NOT expand OneModel's own default ordering (-id) nor add
# the extra self-join. HOLDS patched; FAILS at base (base => id DESC, 2 joins).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

sql = str(OneModel.objects.order_by("root__root_id").query)
njoin = sql.upper().count(" JOIN ")
order = sql.split("ORDER BY")[-1].strip()
print("SQL:", sql)
print("joins=%d order=%r" % (njoin, order))
ok = True
if 'ROOT_ID" ASC' not in order.upper():
    print("FAIL: not root_id ASC"); ok = False
if "DESC" in order.upper():
    print("FAIL: inherited DESC default ordering on self-ref"); ok = False
# base needs 2 joins to reach the expanded default id; direct needs exactly 1
if njoin >= 2:
    print("FAIL: extra self-join (default ordering expanded)"); ok = False
print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.1 (regression / SHALL keep): ordering by a BARE relation (record__root)
# whose final segment does NOT equal the FK's stored attribute name SHALL STILL
# append the related model's default ordering. OneModel.Meta.ordering=("-id",)
# so the effective sort must be id DESC via the expansion (with its extra join).
# This behavior is identical on base and patched; the fix must NOT regress it.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

class TwoModel(models.Model):
    class Meta:
        app_label = "probeapp"
    id = models.BigAutoField(primary_key=True)
    record = models.ForeignKey(OneModel, on_delete=models.CASCADE)
    twoval = models.BigIntegerField(null=True)

sql = str(TwoModel.objects.order_by("record__root").query)
njoin = sql.upper().count(" JOIN ")
order = sql.split("ORDER BY")[-1].strip()
print("SQL:", sql)
print("joins=%d order=%r" % (njoin, order))
ok = True
# Default ordering (-id) of the related model must have been expanded => id DESC
if 'ID" DESC' not in order.upper():
    print("FAIL: related default ordering (id DESC) NOT expanded"); ok = False
if "ROOT_ID" in order.upper():
    print("FAIL: ordered by root_id column, expansion did not happen"); ok = False
# Expansion requires the extra join reaching the related model's id
if njoin < 2:
    print("FAIL: expected the extra join from default-ordering expansion"); ok = False
print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3.1 (pk shortcut) and R3.2 (single-segment FK attname) and R2.3 (related
# model with NO default ordering): all three SHALL order directly, no expansion.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

class TwoModel(models.Model):
    class Meta:
        app_label = "probeapp"
    id = models.BigAutoField(primary_key=True)
    record = models.ForeignKey(OneModel, on_delete=models.CASCADE)
    twoval = models.BigIntegerField(null=True)

class PlainRoot(models.Model):
    class Meta:
        app_label = "probeapp"   # no default ordering
    name = models.CharField(max_length=10)

class HasPlainFK(models.Model):
    class Meta:
        app_label = "probeapp"
    plain = models.ForeignKey(PlainRoot, on_delete=models.CASCADE)

ok = True

# R3.1: pk shortcut -> order by pk column directly, no expansion, no join
sql = str(OneModel.objects.order_by("pk").query)
print("pk SQL:", sql)
if sql.upper().count(" JOIN ") != 0 or 'ID" ASC' not in sql.split("ORDER BY")[-1].upper():
    print("FAIL: pk shortcut did not order by id directly"); ok = False

# R3.2: single-segment FK stored attribute on the queried model -> direct, no join
sql2 = str(TwoModel.objects.order_by("record_id").query)
print("record_id SQL:", sql2)
o2 = sql2.split("ORDER BY")[-1]
if sql2.upper().count(" JOIN ") != 0 or 'RECORD_ID" ASC' not in o2.upper():
    print("FAIL: single-seg FK attname did not order directly"); ok = False

# R2.3: related model has no default ordering -> order by resolved column directly
sql3 = str(HasPlainFK.objects.order_by("plain").query)
print("plain SQL:", sql3)
o3 = sql3.split("ORDER BY")[-1]
if sql3.upper().count(" JOIN ") != 0 or 'PLAIN_ID" ASC' not in o3.upper():
    print("FAIL: no-default-ordering related model expanded or joined"); ok = False

print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R3.3: a lookup path that explicitly descends to the related model's PRIMARY
# KEY (ending in __id, e.g. record__root__id) SHALL order directly by that pk
# column without expanding the related model's default ordering.
# This holds on BOTH base and patched (regression guard) — the fix must keep it.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

class TwoModel(models.Model):
    class Meta:
        app_label = "probeapp"
    id = models.BigAutoField(primary_key=True)
    record = models.ForeignKey(OneModel, on_delete=models.CASCADE)
    twoval = models.BigIntegerField(null=True)

sql = str(TwoModel.objects.order_by("record__root__id").query)
njoin = sql.upper().count(" JOIN ")
order = sql.split("ORDER BY")[-1].strip()
print("SQL:", sql)
print("joins=%d order=%r" % (njoin, order))
ok = True
# Orders by root's pk (root_id column reached via the record join), ascending.
if 'ID" ASC' not in order.upper():
    print("FAIL: not ordered ASC by an id column"); ok = False
if "DESC" in order.upper():
    print("FAIL: DESC present => default ordering expanded"); ok = False
# Must not add the second expansion join; direct __id descent uses one join.
if njoin >= 2:
    print("FAIL: extra join present (default ordering expanded)"); ok = False
print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# R4.1/R4.2/R4.3 (SHALL keep, general ordering semantics preserved):
#  - a model's declared default ordering applies when no explicit order given
#  - an explicit order_by overrides the model default
#  - reverse() inverts the effective ordering, including inverting the model
#    default under reversal.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

ok = True

# R4.1: default ordering applied with no explicit ordering => id DESC
d = str(OneModel.objects.all().query).split("ORDER BY")[-1]
print("default:", d.strip())
if 'ID" DESC' not in d.upper():
    print("FAIL: model default ordering not applied"); ok = False

# R4.2: explicit ordering overrides the model default => oneval ASC only
e = str(OneModel.objects.order_by("oneval").query).split("ORDER BY")[-1]
print("explicit:", e.strip())
if 'ONEVAL" ASC' not in e.upper() or "ID" in e.upper().replace("ONEVAL", ""):
    # ensure id not present in order clause besides oneval
    if 'ID"' in e.upper():
        print("FAIL: model default still present alongside explicit order"); ok = False
if 'ONEVAL" ASC' not in e.upper():
    print("FAIL: explicit order not applied"); ok = False

# R4.3: reverse() inverts the default ordering => id ASC
r = str(OneModel.objects.all().reverse().query).split("ORDER BY")[-1]
print("reversed:", r.strip())
if 'ID" ASC' not in r.upper():
    print("FAIL: reverse() did not invert default ordering"); ok = False

print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 + R1.2 + R1.3 (POSITIVE CONTROL):
# Ordering by a multi-segment lookup whose final segment names the FK's stored
# attribute (record__root_id) SHALL order directly by that stored column,
# ascending, and SHALL NOT introduce the extra join that expanding the related
# model's default ordering requires. HOLDS patched; FAILS at base (base expands
# OneModel.Meta.ordering=("-id",) => id DESC + an extra join).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

class TwoModel(models.Model):
    class Meta:
        app_label = "probeapp"
    id = models.BigAutoField(primary_key=True)
    record = models.ForeignKey(OneModel, on_delete=models.CASCADE)
    twoval = models.BigIntegerField(null=True)

sql = str(TwoModel.objects.order_by("record__root_id").query)
njoin = sql.upper().count(" JOIN ")
order = sql.split("ORDER BY")[-1].strip()
print("SQL:", sql)
print("joins=%d order=%r" % (njoin, order))

ok = True
# Direct order by the root_id stored column, ascending
if 'ROOT_ID" ASC' not in order.upper():
    print("FAIL: order is not root_id ASC"); ok = False
# Must NOT have inherited the related model's DESC default direction
if "DESC" in order.upper():
    print("FAIL: order contains DESC (inherited default ordering)"); ok = False
# Must NOT introduce the extra join that default-ordering expansion needs.
# Direct-column ordering needs exactly 1 join (record -> OneModel to reach root_id);
# expansion would add a second join (root -> OneModel).
if njoin >= 2:
    print("FAIL: extra join present (default ordering expanded)"); ok = False
print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-13033: gold changes the default-ordering-expansion predicate in SQLCompiler.find_ordering_name from comparing field.attname against the WHOLE lookup name to comparing it against the FINAL segment pieces[-1]. So `TwoModel.objects.order_by('record__root_id')` orders directly by root_id (1 join, requested direction) instead of expanding OneModel.Meta.ordering=('-id',) (2 joins, id DESC).

7 probes, all HOLD on the gold-patched tree; all run in the official Docker image via nl_attack.
- probe_1 (POSITIVE CONTROL, R1.1/1.2/1.3): record__root_id => root_id ASC, exactly 1 join, no inherited DESC. HOLDS patched, VIOLATED at base (base gives T3.id DESC + 2 joins). prepatch_reproduced=true.
- probe_2 (R1.4): -record__root_id => root_id DESC, 1 join. HOLDS patched, VIOLATED at base.
- probe_3 (R1.5 self-ref FK): root__root_id => root_id ASC, 1 join (base: id DESC, 2 joins). HOLDS patched, VIOLATED at base.
- probe_4 (R2.1 regression): bare record__root => related default (-id) STILL expanded => id DESC + extra join. HOLDS both trees.
- probe_5 (R3.1 pk / R3.2 single-seg FK attname / R2.3 no-default-ordering related model): all order directly, no join/expansion. HOLDS both trees.
- probe_6 (R3.3): record__root__id descends to related pk directly, no expansion, 1 join. HOLDS both trees.
- probe_7 (R4.1/4.2/4.3): model default applied w/o explicit order; explicit order_by overrides default; reverse() inverts default (id DESC -> id ASC). HOLDS both trees.

Candidate wrong-fixes constructed and re-run under --patch; BOTH REJECTED by the suite (each fails probes 1,2,3 while passing 4-7), demonstrating discriminating power:
- weak_pieces0: compares attname against pieces[0] (first segment) instead of pieces[-1] — a plausible off-by-index misreading. Rejected.
- weak_selfexcl: uses pieces[-1] EXCEPT falls back to the old `name` comparison for self-referential FKs (a weak reading that R1.5 explicitly forbids). Rejected on probe_3 (self-ref) and also probes 1/2 (its non-self-ref branch is fine but it still fails... note: it fails probes 1-3 because for these self-ref/multi-seg cases the fallback triggers). Both are probe-rejected, so no TOO-WEAK finding.

No VIOLATION found (all 7 probes hold patched); no requirements-conforming alternative that would fail to resolve was found. Verdict SOUND: >=5 probes hold, positive control discriminates base vs patched, >=1 candidate exercised and >=1 rejected (2/2 rejected).

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
# R1.1 + R1.2 + R1.3 (POSITIVE CONTROL):
# Ordering by a multi-segment lookup whose final segment names the FK's stored
# attribute (record__root_id) SHALL order directly by that stored column,
# ascending, and SHALL NOT introduce the extra join that expanding the related
# model's default ordering requires. HOLDS patched; FAILS at base (base expands
# OneModel.Meta.ordering=("-id",) => id DESC + an extra join).
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["probeapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False)
import sys, types
mod = types.ModuleType("probeapp"); mod.__path__ = ["/tmp"]; mod.__file__ = "$SCRATCH/probeapp.py"
sys.modules["probeapp"] = mod
django.setup()
from django.db import models

class OneModel(models.Model):
    class Meta:
        app_label = "probeapp"; ordering = ("-id",)
    id = models.BigAutoField(primary_key=True)
    root = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    oneval = models.BigIntegerField(null=True)

class TwoModel(models.Model):
    class Meta:
        app_label = "probeapp"
    id = models.BigAutoField(primary_key=True)
    record = models.ForeignKey(OneModel, on_delete=models.CASCADE)
    twoval = models.BigIntegerField(null=True)

sql = str(TwoModel.objects.order_by("record__root_id").query)
njoin = sql.upper().count(" JOIN ")
order = sql.split("ORDER BY")[-1].strip()
print("SQL:", sql)
print("joins=%d order=%r" % (njoin, order))

ok = True
# Direct order by the root_id stored column, ascending
if 'ROOT_ID" ASC' not in order.upper():
    print("FAIL: order is not root_id ASC"); ok = False
# Must NOT have inherited the related model's DESC default direction
if "DESC" in order.upper():
    print("FAIL: order contains DESC (inherited default ordering)"); ok = False
# Must NOT introduce the extra join that default-ordering expansion needs.
# Direct-column ordering needs exactly 1 join (record -> OneModel to reach root_id);
# expansion would add a second join (root -> OneModel).
if njoin >= 2:
    print("FAIL: extra join present (default ordering expanded)"); ok = False
print("RESULT:", "HOLD" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-13033: gold changes the default-ordering-expansion predicate in SQLCompiler.find_ordering_name from comparing field.attname against the WHOLE lookup name to comparing it against the FINAL segment pieces[-1]. So `TwoModel.objects.order_by('record__root_id')` orders directly by root_id (1 join, requested direction) instead of expanding OneModel.Meta.ordering=('-id',) (2 joins, id DESC).

7 probes, all HOLD on the gold-patched tree; all run in the official Docker image via nl_attack.
- probe_1 (POSITIVE CONTROL, R1.1/1.2/1.3): record__root_id => root_id ASC, exactly 1 join, no inherited DESC. HOLDS patched, VIOLATED at base (base gives T3.id DESC + 2 joins). prepatch_reproduced=true.
- probe_2 (R1.4): -record__root_id => root_id DESC, 1 join. HOLDS patched, VIOLATED at base.
- probe_3 (R1.5 self-ref FK): root__root_id => root_id ASC, 1 join (base: id DESC, 2 joins). HOLDS patched, VIOLATED at base.
- probe_4 (R2.1 regression): bare record__root => related default (-id) STILL expanded => id DESC + extra join. HOLDS both trees.
- probe_5 (R3.1 pk / R3.2 single-seg FK attname / R2.3 no-default-ordering related model): all order directly, no join/expansion. HOLDS both trees.
- probe_6 (R3.3): record__root__id descends to related pk directly, no expansion, 1 join. HOLDS both trees.
- probe_7 (R4.1/4.2/4.3): model default applied w/o explicit order; explicit order_by overrides default; reverse() inverts default (id DESC -> id ASC). HOLDS both trees.

Candidate wrong-fixes constructed and re-run under --patch; BOTH REJECTED by the suite (each fails probes 1,2,3 while passing 4-7), demonstrating discriminating power:
- weak_pieces0: compares attname against pieces[0] (first segment) instead of pieces[-1] — a plausible off-by-index misreading. Rejected.
- weak_selfexcl: uses pieces[-1] EXCEPT falls back to the old `name` comparison for self-referential FKs (a weak reading that R1.5 explicitly forbids). Rejected on probe_3 (self-ref) and also probes 1/2 (its non-self-ref branch is fine but it still fails... note: it fails probes 1-3 because for these self-ref/multi-seg cases the fallback triggers). Both are probe-rejected, so no TOO-WEAK finding.

No VIOLATION found (all 7 probes hold patched); no requirements-conforming alternative that would fail to resolve was found. Verdict SOUND: >=5 probes hold, positive control discriminates base vs patched, >=1 candidate exercised and >=1 rejected (2/2 rejected).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch changes exactly one predicate in SQLCompiler.find_ordering_name: `getattr(field, 'attname', None) != name` -> `getattr(field, 'attname', None) != pieces[-1]` (comparing the FK attname to the FINAL '__'-separated segment rather than the whole lookup string). Requirement 1's condition 'whose final "__"-separated segment equals that field's own stored attribute name' precisely captures pieces[-1]. The modeling boundary is the observable ordering result (direct stored-column ordering vs. related-model default-ordering expansion, extra JOIN, and inherited sort direction), which is the changed behavior — not a narrow branch/helper. Base-commit probe fails the same assertions (T3 extra join + DESC), confirming the requirements discriminate patched from unpatched. Req 4's preservation clauses (default ordering when no explicit order; explicit overrides default; reversal inverts default; cycle detection raising the ordering error) correspond to unchanged code paths and hold. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All specifics in requirements.md trace to the PUBLIC problem_statement: the multi-segment lookup ending in a relation's stored `_id` column (record__root_id), the bare-relation fallback to Meta.ordering (record__root), the descend-to-pk form (record__root__id), ascending vs descending (-record__root_id), self-referential FK, and Meta.ordering=('-id',). The doc names find_ordering_name/compiler.py to localize the change (legitimate) and translates the fix ('final "__" segment equals the field's stored attname') into a behavioral requirement without quoting the pieces[-1] token or gold-diff lines. No hidden test artifacts leak: the test file paths (tests/ordering/tests.py, models.py), the test name test_order_by_self_referential_fk, the invented 'editor'/'editor_id' field, and the specific assertQuerysetEqual expectations ('Article 2','Article 1' vs 'Article 1','Article 2') do not appear. The asc/desc/pk/fk-attname/__id enumeration mirrors the problem_statement's own worked SQL examples rather than the hidden test parametrization. No fix-invented identifiers leaked.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
