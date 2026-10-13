# P2 adversarial audit — django__django-15629

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
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
tp = A._meta.get_field("code").db_parameters(connection)
fp = B._meta.get_field("fk").db_parameters(connection)
print("MARKER target=%r fk=%r" % (tp, fp), file=sys.stderr)
ok = ("collation" in fp) and (fp["collation"] == tp.get("collation") == "nocase")
# Req1.4: type and check unchanged/present
ok = ok and fp.get("type") == B._meta.get_field("fk").db_type(connection) and ("check" in fp)
print("MARKER ok=%s" % ok, file=sys.stderr)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
import django.db.backends.sqlite3.schema as sq
with connection.schema_editor() as se:
    se.create_model(A); se.create_model(B)
old = A._meta.get_field("code")
new = copy.deepcopy(old); new.db_collation="rtrim"; new.set_attributes_from_name("code"); new.model=A
orig = sq.DatabaseSchemaEditor._remake_table
calls=[]
def spy(self, model, *a, **k):
    calls.append(model.__name__); return orig(self, model, *a, **k)
sq.DatabaseSchemaEditor._remake_table = spy
with connection.schema_editor() as se:
    se.alter_field(A, old, new)
print("MARKER remake_calls=%r" % (calls,), file=sys.stderr)
ok = "B" in calls  # referencing table rebuilt even though type unchanged
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
with connection.schema_editor() as se:
    se.create_model(A); se.create_model(B)
old = A._meta.get_field("code")
new = copy.deepcopy(old); new.db_collation="rtrim"; new.set_attributes_from_name("code"); new.model=A
with connection.schema_editor(collect_sql=True) as se:
    se.alter_field(A, old, new)
    sql = se.collected_sql
bcreate = [s for s in sql if 'CREATE TABLE "new__testapp_b"' in s]
print("MARKER bcreate=%r" % bcreate, file=sys.stderr)
# Req3.5: the collation applied to the referencing column equals the collation
# reported by that FK's db_parameters (propagated from the referenced key, Req1).
fk_coll = B._meta.get_field("fk").db_parameters(connection).get("collation")
print("MARKER fk_reported_collation=%r" % fk_coll, file=sys.stderr)
ok = (fk_coll is not None) and len(bcreate)==1 \
     and ("COLLATE %s" % fk_coll) in bcreate[0] and "fk_id" in bcreate[0]
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
with connection.schema_editor(collect_sql=True) as se:
    se.create_model(A); se.create_model(B)
    sql = se.collected_sql
bcreate = [s for s in sql if "testapp_b" in s.lower() and "create table" in s.lower()]
print("MARKER bcreate=%r" % bcreate, file=sys.stderr)
ok = len(bcreate)==1 and "COLLATE nocase" in bcreate[0] and "fk_id" in bcreate[0]
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
import django.db.backends.sqlite3.schema as sq
with connection.schema_editor() as se:
    se.create_model(A); se.create_model(B)
old = A._meta.get_field("code")
# change only a non-db attribute (help_text): no type change, no collation change
new = copy.deepcopy(old); new.help_text="changed"; new.set_attributes_from_name("code"); new.model=A
orig = sq.DatabaseSchemaEditor._remake_table
calls=[]
def spy(self, model, *a, **k):
    calls.append(model.__name__); return orig(self, model, *a, **k)
sq.DatabaseSchemaEditor._remake_table = spy
with connection.schema_editor() as se:
    se.alter_field(A, old, new)
print("MARKER remake_calls=%r" % (calls,), file=sys.stderr)
ok = "B" not in calls  # referencing table must NOT be rebuilt
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
import django.db.backends.sqlite3.schema as sq
with connection.schema_editor() as se:
    se.create_model(A); se.create_model(B)
old = A._meta.get_field("code")
new = copy.deepcopy(old); new.max_length=20; new.set_attributes_from_name("code"); new.model=A
print("MARKER oldtype=%s newtype=%s" % (old.db_type(connection), new.db_type(connection)), file=sys.stderr)
orig = sq.DatabaseSchemaEditor._remake_table
calls=[]
def spy(self, model, *a, **k):
    calls.append(model.__name__); return orig(self, model, *a, **k)
sq.DatabaseSchemaEditor._remake_table = spy
with connection.schema_editor() as se:
    se.alter_field(A, old, new)
print("MARKER remake_calls=%r" % (calls,), file=sys.stderr)
ok = "B" in calls
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
tp = A._meta.get_field("code").db_parameters(connection)
fp = B._meta.get_field("fk").db_parameters(connection)
print("MARKER target=%r fk=%r" % (tp, fp), file=sys.stderr)
ok = ("collation" in fp) and (fp["collation"] == tp.get("collation") == "nocase")
# Req1.4: type and check unchanged/present
ok = ok and fp.get("type") == B._meta.get_field("fk").db_type(connection) and ("check" in fp)
print("MARKER ok=%s" % ok, file=sys.stderr)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15629: propagate a PK's db_collation to referencing FK columns. Suite of 6 standalone probes, all run in the official image on patched/base/candidate trees.

Probe->requirement mapping and observed results (PATCHED / BASE):
- probe_1 (Req1.1-1.4, POSITIVE CONTROL): ForeignKey.db_parameters returns a 'collation' key equal to target field's collation ('nocase'), with 'type'/'check' still present. HOLDS patched / VIOLATED base (base fk params = {'type','check'} only, no collation). Discriminates.
- probe_2 (Req4.1/4.2): SQLite _alter_field rebuilds the referencing table B on a collation-only change (type unchanged). Verified via _remake_table spy -> 'B' rebuilt. HOLDS patched / VIOLATED base (only 'A' rebuilt).
- probe_3 (Req3.5): the rebuilt referencing column's emitted collation equals the collation FK.db_parameters reports (COLLATE nocase on new__testapp_b.fk_id). HOLDS patched / VIOLATED base (B not rebuilt, no COLLATE).
- probe_4 (Req1 propagation via create_model / F2P 'Creation of models with a FK to a PK with db_collation'): CREATE TABLE for B carries COLLATE nocase on fk_id. HOLDS patched / VIOLATED base (no COLLATE).
- probe_5 (Req5.3/2.3 regression): altering only a non-db attribute (help_text) -> no type/collation change -> referencing table B is NOT rebuilt. HOLDS on both trees (correct-preserving).
- probe_6 (Req4.3 regression): a real type change (max_length 10->20) still rebuilds B. HOLDS on both trees (existing behavior kept).

CANDIDATE PATCH exercised: 'related_only_lazy_fix' (weak.diff) applies ONLY the ForeignKey.db_parameters change from the gold patch, omitting the base/schema.py drop-FK + re-collate logic and the sqlite3/schema.py rebuild-on-collation logic. This is the lazy reading of Req1 alone. Result under candidate: probe_1 HOLDS, probe_4 HOLDS (create_model column_sql reads db_parameters collation), but probe_2 REJECTED and probe_3 REJECTED (alter path never rebuilds/re-collates referencing table). So the suite discriminates this requirements-partial wrong fix -- it would not resolve the AlterField F2P test. Floor met: >=1 candidate exercised, >=1 rejected.

Harness note: probe prints go to stderr; the runner's 400-char tail sometimes shows git-apply lines instead, but exit codes are authoritative and were confirmed by re-running with MARKER greps. All runs completed (no INCONCLUSIVE). >=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base). Verdict SOUND.

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
import sys, os, tempfile, django, copy
from django.conf import settings
def _setup(models_src):
    d = tempfile.mkdtemp(); pkg=os.path.join(d,"testapp"); os.makedirs(pkg)
    open(os.path.join(pkg,"__init__.py"),"w").close()
    open(os.path.join(pkg,"models.py"),"w").write(models_src)
    sys.path.insert(0,d)
    settings.configure(DEBUG=True, DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth","testapp"], USE_TZ=True)
    django.setup()
MODELS = (
"from django.db import models\n"
"class A(models.Model):\n"
"    code = models.CharField(max_length=10, primary_key=True, db_collation=\"nocase\")\n"
"class B(models.Model):\n"
"    fk = models.ForeignKey(A, on_delete=models.CASCADE)\n")

_setup(MODELS)
from testapp.models import A, B
from django.db import connection
tp = A._meta.get_field("code").db_parameters(connection)
fp = B._meta.get_field("fk").db_parameters(connection)
print("MARKER target=%r fk=%r" % (tp, fp), file=sys.stderr)
ok = ("collation" in fp) and (fp["collation"] == tp.get("collation") == "nocase")
# Req1.4: type and check unchanged/present
ok = ok and fp.get("type") == B._meta.get_field("fk").db_type(connection) and ("check" in fp)
print("MARKER ok=%s" % ok, file=sys.stderr)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15629: propagate a PK's db_collation to referencing FK columns. Suite of 6 standalone probes, all run in the official image on patched/base/candidate trees.

Probe->requirement mapping and observed results (PATCHED / BASE):
- probe_1 (Req1.1-1.4, POSITIVE CONTROL): ForeignKey.db_parameters returns a 'collation' key equal to target field's collation ('nocase'), with 'type'/'check' still present. HOLDS patched / VIOLATED base (base fk params = {'type','check'} only, no collation). Discriminates.
- probe_2 (Req4.1/4.2): SQLite _alter_field rebuilds the referencing table B on a collation-only change (type unchanged). Verified via _remake_table spy -> 'B' rebuilt. HOLDS patched / VIOLATED base (only 'A' rebuilt).
- probe_3 (Req3.5): the rebuilt referencing column's emitted collation equals the collation FK.db_parameters reports (COLLATE nocase on new__testapp_b.fk_id). HOLDS patched / VIOLATED base (B not rebuilt, no COLLATE).
- probe_4 (Req1 propagation via create_model / F2P 'Creation of models with a FK to a PK with db_collation'): CREATE TABLE for B carries COLLATE nocase on fk_id. HOLDS patched / VIOLATED base (no COLLATE).
- probe_5 (Req5.3/2.3 regression): altering only a non-db attribute (help_text) -> no type/collation change -> referencing table B is NOT rebuilt. HOLDS on both trees (correct-preserving).
- probe_6 (Req4.3 regression): a real type change (max_length 10->20) still rebuilds B. HOLDS on both trees (existing behavior kept).

CANDIDATE PATCH exercised: 'related_only_lazy_fix' (weak.diff) applies ONLY the ForeignKey.db_parameters change from the gold patch, omitting the base/schema.py drop-FK + re-collate logic and the sqlite3/schema.py rebuild-on-collation logic. This is the lazy reading of Req1 alone. Result under candidate: probe_1 HOLDS, probe_4 HOLDS (create_model column_sql reads db_parameters collation), but probe_2 REJECTED and probe_3 REJECTED (alter path never rebuilds/re-collates referencing table). So the suite discriminates this requirements-partial wrong fix -- it would not resolve the AlterField F2P test. Floor met: >=1 candidate exercised, >=1 rejected.

Harness note: probe prints go to stderr; the runner's 400-char tail sometimes shows git-apply lines instead, but exit codes are authoritative and were confirmed by re-running with MARKER greps. All runs completed (no INCONCLUSIVE). >=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements track the gold patch faithfully across all changed files. Req 1 <-> related.py db_parameters adds collation from target_field.db_parameters (patch lines 92-99), confirmed by probe both patched and --base. Req 2 <-> base/schema.py drop_foreign_keys gains 'or (old_collation != new_collation)' (lines 8-17). Req 3 <-> the rels_to_update loop's new if old_rel_collation != rel_collation branch using _alter_column_collation_sql with other_actions=[] and the referencing field's own db_parameters collation (lines 37-52). Req 4 <-> sqlite3/schema.py rebuild condition gains 'or old_collation != new_collation' under new_field.unique (lines 78-82). Req 5 preservation clauses are consistent with an additive change. Modeling boundary is the changed observable behavior (collation propagation), not a narrow slice; no invented, mandated-missing, or forbidden-present behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes the fix behaviorally and localizes it to the changed modules/functions (ForeignKey.db_parameters, BaseDatabaseSchemaEditor._alter_field, SQLite DatabaseSchemaEditor._alter_field) — legitimate, since the document must localize the change. No hidden-test content is transmitted: no test function/class names (test_alter_field_pk_fk_db_collation, test_create_fk_models_to_pk_field_db_collation), no test file paths (tests/migrations/test_operations.py, test_base.py), no test fixtures (Pony/Rider/Stable/ShetlandPony models, CharField(max_length=10), assertColumnCollation, pony_id), and no parametrization ids. The db_collation term and the utf8_bin/MySQL ALTER TABLE examples are all in the PUBLIC problem_statement. The 'collation' key in db_parameters and the collation-vs-type branching mirror the gold edit, but that is behavioral translation of the fix (the whole point), not the transmission of tests. Req 3.3's 'no additional follow-up actions' tracks the gold's other_actions=[] but describes fix mechanism, not any test assertion (tests never inspect other_actions). Req 5.2's enumeration (FK, M2M, through, to-field references) reflects general Django reference concepts / the FieldOperationTests PASS_TO_PASS regression surface, not test-parametrization case ids. No leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
