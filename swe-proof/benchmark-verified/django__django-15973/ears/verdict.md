# P2 adversarial audit — django__django-15973

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_pc.py`, `probe_2_through_ref.py`, `probe_3_two_entry.py`, `probe_4_no_through.py`, `probe_5_same_app.py`, `probe_6_ops.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_pc.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

import sys
changes = get_changes([], sep_states())
migs = changes["authors"]
addmig = None
for m in migs:
    for op in m.operations:
        if op.__class__.__name__ == "AddField":
            addmig = m
addmig = addmig or migs[-1]
deps = set((d[0], d[1]) for d in addmig.dependencies)
print("authors add-field-migration deps:", deps)
# The migration adding the cross-app m2m must depend on BOTH the through app
# (contract) and the target app (testapp) - Req 1.3.
apps = set(d[0] for d in deps)
ok = "contract" in apps and "testapp" in apps
print("apps:", apps)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_through_ref.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

def dep_apps(mig):
    return set((d[0], d[1]) for d in mig.dependencies)

import sys
ps = make_state(sep_states())
ad = MigrationAutodetector(ProjectState(), ps)
field = ps.models["authors","author"].fields["publishers"]
deps = ad._get_dependencies_for_foreign_key("authors","author",field,ps)
print("deps:", deps)
# second entry must be resolved from through ('contract.Contract') -> ('contract','contract')
ok = len(deps)==2 and (deps[1][0],deps[1][1])==("contract","contract")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_two_entry.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

def dep_apps(mig):
    return set((d[0], d[1]) for d in mig.dependencies)

import sys
ps = make_state(sep_states())
ad = MigrationAutodetector(ProjectState(), ps)
field = ps.models["authors","author"].fields["publishers"]
deps = ad._get_dependencies_for_foreign_key("authors","author",field,ps)
print("deps:", deps)
ok = len(deps)==2 and (deps[0][0],deps[0][1])==("testapp","publisher")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_no_through.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

def dep_apps(mig):
    return set((d[0], d[1]) for d in mig.dependencies)

import sys
author = ModelState("authors","Author",[
    ("id", models.AutoField(primary_key=True)),
    ("publishers", models.ManyToManyField("testapp.Publisher")),
])
publisher = ModelState("testapp","Publisher",[("id", models.AutoField(primary_key=True))])
ps = make_state([author, publisher])
ad = MigrationAutodetector(ProjectState(), ps)
field = ps.models["authors","author"].fields["publishers"]
deps = ad._get_dependencies_for_foreign_key("authors","author",field,ps)
print("deps:", deps)
ok = len(deps)==1 and (deps[0][0],deps[0][1])==("testapp","publisher")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_same_app.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

def dep_apps(mig):
    return set((d[0], d[1]) for d in mig.dependencies)

import sys
# through model 'otherapp.Contract' same app as target 'otherapp.Publisher'
author = ModelState("testapp","Author",[
    ("id", models.AutoField(primary_key=True)),
    ("publishers", models.ManyToManyField("otherapp.Publisher", through="otherapp.Contract")),
])
publisher = ModelState("otherapp","Publisher",[("id", models.AutoField(primary_key=True))])
contract = ModelState("otherapp","Contract",[
    ("id", models.AutoField(primary_key=True)),
    ("author", models.ForeignKey("testapp.Author", models.CASCADE)),
    ("publisher", models.ForeignKey("otherapp.Publisher", models.CASCADE)),
])
ps = make_state([author, publisher, contract])
ad = MigrationAutodetector(ProjectState(), ps)
field = ps.models["testapp","author"].fields["publishers"]
deps = ad._get_dependencies_for_foreign_key("testapp","author",field,ps)
print("deps:", deps)
# both entries should be otherapp (target and through same app) -> unchanged from historical behavior
ok = len(deps)==2 and (deps[0][0],deps[0][1])==("otherapp","publisher") and (deps[1][0],deps[1][1])==("otherapp","contract")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_ops.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

def dep_apps(mig):
    return set((d[0], d[1]) for d in mig.dependencies)

import sys
changes = get_changes([], sep_states())
def optypes(app, idx):
    return [op.__class__.__name__ for op in changes[app][idx].operations]
# authors: CreateModel then AddField across 2 migrations
authors_ops = []
for m in changes["authors"]:
    authors_ops += [op.__class__.__name__ for op in m.operations]
print("authors ops:", authors_ops)
# find AddField op attrs
addf = None
for m in changes["authors"]:
    for op in m.operations:
        if op.__class__.__name__=="AddField":
            addf = op
print("addfield name:", getattr(addf,"name",None), "model_name:", getattr(addf,"model_name",None))
ok = "CreateModel" in authors_ops and "AddField" in authors_ops
ok = ok and addf is not None and addf.name=="publishers" and addf.model_name=="author"
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_pc.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

import sys
changes = get_changes([], sep_states())
migs = changes["authors"]
addmig = None
for m in migs:
    for op in m.operations:
        if op.__class__.__name__ == "AddField":
            addmig = m
addmig = addmig or migs[-1]
deps = set((d[0], d[1]) for d in addmig.dependencies)
print("authors add-field-migration deps:", deps)
# The migration adding the cross-app m2m must depend on BOTH the through app
# (contract) and the target app (testapp) - Req 1.3.
apps = set(d[0] for d in deps)
ok = "contract" in apps and "testapp" in apps
print("apps:", apps)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15973: fix makes the m2m 'through' migration dependency resolve from field.remote_field.through instead of the target reference (remote_field_model), in MigrationAutodetector._get_dependencies_for_foreign_key. All 6 probes HOLD on the gold-patched tree.

Probe map (requirement -> observed):
- probe_1_pc (POSITIVE CONTROL, Req 1.3): full autodetector run over 3 separate apps (authors m2m -> testapp.Publisher through contract.Contract); the AddField migration must depend on both 'contract' and 'testapp' apps. PATCHED: deps apps={authors,testapp,contract} -> HOLD. BASE: apps={testapp} only (through mis-resolved to target app) -> FAIL. Discriminates.
- probe_2_through_ref (Req 1.1/1.2): direct _get_dependencies_for_foreign_key -> second dep == ('contract','contract'). PATCHED HOLD; BASE gives ('testapp','publisher') duplicated -> FAIL.
- probe_3_two_entry (Req 2.1/2.3): exactly two entries, target ('testapp','publisher') first. HOLD.
- probe_4_no_through (Req 2.2/3.3): plain m2m without through -> single target dependency only. HOLD.
- probe_5_same_app (Req 3.1 regression): through and target both in otherapp -> deps unchanged (('otherapp','publisher'),('otherapp','contract')). HOLD.
- probe_6_ops (Req 3.2/3.4): CreateModel+AddField emitted; AddField attrs name='publishers', model_name='author' unchanged. HOLD.

CANDIDATE PATCH (weak_naive_split.diff, applies at base): the lazy fix a weak reading permits -- resolve through via field.remote_field.through.split('.',1) instead of resolve_relation. It satisfies Req 1.3 at the app-label level (probe_1_pc HOLDS -> so a suite that only checked app labels would pass it) but is REJECTED by probe_2 and probe_5 because it fails to lower-case the object name (returns ('contract','Contract') / ('otherapp','Contract') vs the canonical lower-cased 'contract'). This demonstrates the suite discriminates wrong implementations at the object-name granularity, and also that it does not resolve recursive/unscoped references or non-string through classes. REJECTED candidate => not a too-weak finding.

All required runs completed cleanly in the official image; no INCONCLUSIVE runs at submit time. Verdict SOUND: >=5 probes hold on patched, positive control discriminates (patched HOLD / base FAIL), and >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_pc.py`, `probe_2_through_ref.py`, `probe_3_two_entry.py`, `probe_4_no_through.py`, `probe_5_same_app.py`, `probe_6_ops.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_pc.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_pc.py` → holds on the patched tree (good)

Attack 2 — `probe_2_through_ref.py` → holds on the patched tree (good)

Attack 3 — `probe_3_two_entry.py` → holds on the patched tree (good)

Attack 4 — `probe_4_no_through.py` → holds on the patched tree (good)

Attack 5 — `probe_5_same_app.py` → holds on the patched tree (good)

Attack 6 — `probe_6_ops.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_pc.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def make_state(mss):
    ps = ProjectState()
    for ms in mss:
        ps.add_model(ms.clone())
    return ps

def get_changes(before, after):
    return MigrationAutodetector(make_state(before), make_state(after))._detect_changes()

def sep_states():
    author = ModelState("authors","Author",[
        ("id", models.AutoField(primary_key=True)),
        ("publishers", models.ManyToManyField("testapp.Publisher", through="contract.Contract")),
    ])
    publisher = ModelState("testapp","Publisher",[
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=100)),
    ])
    contract = ModelState("contract","Contract",[
        ("id", models.AutoField(primary_key=True)),
        ("author", models.ForeignKey("authors.Author", models.CASCADE)),
        ("publisher", models.ForeignKey("testapp.Publisher", models.CASCADE)),
    ])
    return [author, publisher, contract]

import sys
changes = get_changes([], sep_states())
migs = changes["authors"]
addmig = None
for m in migs:
    for op in m.operations:
        if op.__class__.__name__ == "AddField":
            addmig = m
addmig = addmig or migs[-1]
deps = set((d[0], d[1]) for d in addmig.dependencies)
print("authors add-field-migration deps:", deps)
# The migration adding the cross-app m2m must depend on BOTH the through app
# (contract) and the target app (testapp) - Req 1.3.
apps = set(d[0] for d in deps)
ok = "contract" in apps and "testapp" in apps
print("apps:", apps)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15973: fix makes the m2m 'through' migration dependency resolve from field.remote_field.through instead of the target reference (remote_field_model), in MigrationAutodetector._get_dependencies_for_foreign_key. All 6 probes HOLD on the gold-patched tree.

Probe map (requirement -> observed):
- probe_1_pc (POSITIVE CONTROL, Req 1.3): full autodetector run over 3 separate apps (authors m2m -> testapp.Publisher through contract.Contract); the AddField migration must depend on both 'contract' and 'testapp' apps. PATCHED: deps apps={authors,testapp,contract} -> HOLD. BASE: apps={testapp} only (through mis-resolved to target app) -> FAIL. Discriminates.
- probe_2_through_ref (Req 1.1/1.2): direct _get_dependencies_for_foreign_key -> second dep == ('contract','contract'). PATCHED HOLD; BASE gives ('testapp','publisher') duplicated -> FAIL.
- probe_3_two_entry (Req 2.1/2.3): exactly two entries, target ('testapp','publisher') first. HOLD.
- probe_4_no_through (Req 2.2/3.3): plain m2m without through -> single target dependency only. HOLD.
- probe_5_same_app (Req 3.1 regression): through and target both in otherapp -> deps unchanged (('otherapp','publisher'),('otherapp','contract')). HOLD.
- probe_6_ops (Req 3.2/3.4): CreateModel+AddField emitted; AddField attrs name='publishers', model_name='author' unchanged. HOLD.

CANDIDATE PATCH (weak_naive_split.diff, applies at base): the lazy fix a weak reading permits -- resolve through via field.remote_field.through.split('.',1) instead of resolve_relation. It satisfies Req 1.3 at the app-label level (probe_1_pc HOLDS -> so a suite that only checked app labels would pass it) but is REJECTED by probe_2 and probe_5 because it fails to lower-case the object name (returns ('contract','Contract') / ('otherapp','Contract') vs the canonical lower-cased 'contract'). This demonstrates the suite discriminates wrong implementations at the object-name granularity, and also that it does not resolve recursive/unscoped references or non-string through classes. REJECTED candidate => not a too-weak finding.

All required runs completed cleanly in the official image; no INCONCLUSIVE runs at submit time. Verdict SOUND: >=5 probes hold on patched, positive control discriminates (patched HOLD / base FAIL), and >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified the patched _get_dependencies_for_foreign_key source in the instance image via nl_attack probe (dependencies=[(dep_app_label,dep_object_name,None,True)]; if through, append resolve_relation(field.remote_field.through, app_label, model_name)). Confirmed resolve_relation semantics for 'app.Model' strings and 'self' recursion. Requirements track the changed behavioral boundary (through-dependency resolution across three apps), consistent with the issue's cross-app through AttributeError and the one-line diff.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the gold fix and hidden test into behavioral requirements without transmitting the tests themselves. Everything load-bearing is either public in problem_statement (the three-separate-apps m2m/through scenario, the AttributeError 'str' object has no attribute '_meta', the generated-migration/dependencies shape) or legitimate localization (naming autodetector.py, utils.py, _get_dependencies_for_foreign_key, resolve_relation). The core behavioral claim (resolve the intermediary dependency from the field's own through reference rather than the target reference) mirrors the gold edit remote_field_model -> field.remote_field.through, but 'field.remote_field.through' is public Django API vocabulary, not a fix-invented identifier. No hidden-test artifacts leak: no test function/class name (test_create_with_through_model_separate_apps / AutodetectorTests), no test file path, no parametrization ids, no test literals (app labels authors/contract/testapp, ('...','auto_1') dependency tuples, assertNumberMigrations counts of 1/1/2), and no quoted test or gold code. Requirement 2/3 prose about the two-entry dependency list and create-model+add-field ordering describes general autodetector behavior (also visible in the problem_statement's example migration), not the test's specific assertions. The 'three different apps' framing matches the public bug report, not a test-only construction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
