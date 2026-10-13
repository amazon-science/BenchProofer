# P2 adversarial audit — django__django-15695

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.1, 1.2, 2.1: named index whose resolved source name already == new_name
# => forward must issue NO rename statement, index left unchanged.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx]})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn:
    alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))
    def _constraint_names(self,*a,**k): raise AssertionError("introspection not expected for named path")

# both states carry the index already under the target name "new_idx"
from_state=state("new_idx"); to_state=state("new_idx")
op=RenameIndex("Pony", new_name="new_idx", old_name="new_idx")
se=FakeSE()
op.database_forwards(app, se, from_state, to_state)
print("rename calls:", se.renames)
assert se.renames==[], "expected NO rename when source already has target name"
print("OK: no rename issued")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2.2, 2.3, 1.1: unnamed (old_fields) index that already carries the target name
# => forward must issue NO rename; read-only introspection permitted.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx], "index_together":{("pink","weight")}})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn: alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]; self.introspected=False
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))
    def _constraint_names(self, model, column_names=None, index=None):
        # resolve unnamed index by columns -> it already has the target name
        self.introspected=True
        return ["new_idx"]

from_state=state("new_idx"); to_state=state("new_idx")
op=RenameIndex("Pony", new_name="new_idx", old_fields=("pink","weight"))
se=FakeSE()
op.database_forwards(app, se, from_state, to_state)
print("introspected:", se.introspected, "rename calls:", se.renames)
assert se.introspected, "expected column introspection on unnamed path"
assert se.renames==[], "expected NO rename when resolved index already has target name"
print("OK: unnamed idempotent no-op")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.4, 3.3: names differ => exactly ONE rename from resolved source to target.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx]})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn: alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))

from_state=state("old_idx"); to_state=state("new_idx")
op=RenameIndex("Pony", new_name="new_idx", old_name="old_idx")
se=FakeSE()
op.database_forwards(app, se, from_state, to_state)
print("rename calls:", se.renames)
assert se.renames==[("old_idx","new_idx")], "expected exactly one rename old->new"
print("OK: single correct rename")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.2: unnamed path, wrong number of matching indexes => ValueError raised.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx],"index_together":{("pink","weight")}})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn: alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))
    def _constraint_names(self, model, column_names=None, index=None):
        return ["i1","i2"]   # wrong count (2)

from_state=state("x"); to_state=state("new_idx")
op=RenameIndex("Pony", new_name="new_idx", old_fields=("pink","weight"))
se=FakeSE()
raised=False
try:
    op.database_forwards(app, se, from_state, to_state)
except ValueError as e:
    raised=True; print("ValueError:", e)
assert raised, "expected ValueError for wrong number of matching indexes"
assert se.renames==[], "no rename when erroring"
print("OK: wrong-count ValueError preserved")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.1: allow_migrate_model False => no-op, no rename, no introspection.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx]})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn: alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]; self.introspected=False
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))
    def _constraint_names(self,*a,**k): self.introspected=True; return ["z"]

# monkeypatch allow_migrate_model to return False
from django.db.migrations.operations.models import RenameIndex as RI
orig = RI.allow_migrate_model
RI.allow_migrate_model = lambda self, conn_alias, model: False
try:
    from_state=state("old_idx"); to_state=state("new_idx")
    op=RenameIndex("Pony", new_name="new_idx", old_name="old_idx")
    se=FakeSE()
    op.database_forwards(app, se, from_state, to_state)
    print("rename:", se.renames, "introspected:", se.introspected)
    assert se.renames==[] and not se.introspected, "expected full no-op when migration not allowed"
    print("OK: allow_migrate_model False => no-op")
finally:
    RI.allow_migrate_model = orig
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.4: backward with unnamed index (old_fields) => no-op.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx],"index_together":{("pink","weight")}})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn: alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]; self.introspected=False
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))
    def _constraint_names(self,*a,**k): self.introspected=True; return ["z"]

from_state=state("new_idx"); to_state=state("new_idx")
op=RenameIndex("Pony", new_name="new_idx", old_fields=("pink","weight"))
se=FakeSE()
op.database_backwards(app, se, from_state, to_state)
print("rename:", se.renames, "introspected:", se.introspected)
assert se.renames==[] and not se.introspected, "backward unnamed must be no-op"
print("OK: backward unnamed no-op")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 3.5: backward (named) swaps names, does forward-with-swapped, then restores;
# a backward then forward returns index to its post-forward name, and names are
# restored on the operation object after backward.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx]})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn: alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))

# Post-forward world: index is "new_idx". Backward should rename new_idx -> old_idx.
# from_state/to_state naming as used in database_backwards: it swaps then calls forwards.
op=RenameIndex("Pony", new_name="new_idx", old_name="old_idx")
# For backward: forward(with swapped names) renames from current(new_idx) to old_idx.
# database_forwards resolves old_index from from_state by (swapped) old_name=new_idx.
from_state=state("new_idx"); to_state=state("old_idx")
se=FakeSE()
op.database_backwards(app, se, from_state, to_state)
print("backward rename:", se.renames)
print("names after backward:", op.old_name, op.new_name)
assert se.renames==[("new_idx","old_idx")], "backward should rename new->old"
# names restored
assert op.old_name=="old_idx" and op.new_name=="new_idx", "names must be restored after backward"

# Now forward again (post-backward world: index is old_idx) => rename old->new
from_state2=state("old_idx"); to_state2=state("new_idx")
se2=FakeSE()
op.database_forwards(app, se2, from_state2, to_state2)
print("forward rename:", se2.renames)
assert se2.renames==[("old_idx","new_idx")], "forward after backward should restore post-forward name"
print("OK: backward+forward round trip")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1, 1.2, 2.1: named index whose resolved source name already == new_name
# => forward must issue NO rename statement, index left unchanged.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx]})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn:
    alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))
    def _constraint_names(self,*a,**k): raise AssertionError("introspection not expected for named path")

# both states carry the index already under the target name "new_idx"
from_state=state("new_idx"); to_state=state("new_idx")
op=RenameIndex("Pony", new_name="new_idx", old_name="new_idx")
se=FakeSE()
op.database_forwards(app, se, from_state, to_state)
print("rename calls:", se.renames)
assert se.renames==[], "expected NO rename when source already has target name"
print("OK: no rename issued")
```

Prepatch bug re-encoded as an attack: `True`.

RenameIndex.database_forwards idempotency audit for django__django-15695. Gold adds `if old_index.name == self.new_name: return` AFTER both the old_fields (unnamed) resolution and the old_name (named) resolution branches, so the guard covers BOTH paths.

Probes (all run in-image via nl_attack; each uses real ProjectState/ModelState + a FakeSchemaEditor recording rename_index calls and introspection):
- probe_1 (Req 1.1/1.2/2.1, POSITIVE CONTROL): named index already carries target name => 0 rename calls. HOLDS patched, FAILS at base (base issues rename new_idx->new_idx). Discriminates.
- probe_2 (Req 2.2/2.3/1.1): unnamed old_fields index resolved by column introspection already carries target name => introspection permitted but 0 rename calls. HOLDS patched, FAILS at base.
- probe_3 (Req 1.4/3.3): names differ => exactly one rename old_idx->new_idx. HOLDS on both trees (regression).
- probe_4 (Req 3.2): unnamed path, _constraint_names returns 2 => ValueError preserved, no rename. HOLDS patched.
- probe_5 (Req 3.1): allow_migrate_model False => full no-op (no rename, no introspection). HOLDS patched.
- probe_6 (Req 3.4): backward with old_fields => no-op. HOLDS patched.
- probe_7 (Req 3.5): backward (named) renames new->old, restores op.old_name/new_name; subsequent forward renames old->new (round-trip). HOLDS patched.

Candidate patch (weak.diff, 'named_path_only_guard'): places the idempotency guard inside the `else` (old_name) branch only, leaving the unnamed/old_fields path unguarded — the lazy reading permitted by a suite that only checks the named case. Applies cleanly at base. Under this candidate probe_2 is REJECTED (still issues a rename on the unnamed idempotent case), while probes 1 and 3 pass. Since the hidden F2P test (test_rename_index_unnamed_index) exercises exactly the unnamed re-apply path, this candidate would NOT resolve — the suite correctly discriminates it.

>=5 distinct probes all hold on patched tree; positive control (probe_1) discriminates base vs patched (prepatch reproduced); >=1 wrong-fix candidate exercised and rejected. Verdict SOUND. Note: FakeSchemaEditor is a faithful stand-in for the DB layer since the requirements are stated in terms of whether an index-rename statement is issued; probes assert on rename_index invocation, matching the criteria wording.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Req 1.1, 1.2, 2.1: named index whose resolved source name already == new_name
# => forward must issue NO rename statement, index left unchanged.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[
        "django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db.migrations.state import ProjectState, ModelState
from django.db import models
from django.db.migrations.operations.models import RenameIndex

app="testapp"
def state(index_name):
    idx = models.Index(fields=["pink","weight"], name=index_name)
    ms = ModelState(app,"Pony",[("id",models.AutoField(primary_key=True)),
        ("pink",models.IntegerField(default=1)),("weight",models.FloatField())],
        options={"indexes":[idx]})
    ps=ProjectState(); ps.add_model(ms); return ps

class FakeConn:
    alias="default"
class FakeSE:
    def __init__(self): self.connection=FakeConn(); self.renames=[]
    def rename_index(self, model, old, new): self.renames.append((old.name,new.name))
    def _constraint_names(self,*a,**k): raise AssertionError("introspection not expected for named path")

# both states carry the index already under the target name "new_idx"
from_state=state("new_idx"); to_state=state("new_idx")
op=RenameIndex("Pony", new_name="new_idx", old_name="new_idx")
se=FakeSE()
op.database_forwards(app, se, from_state, to_state)
print("rename calls:", se.renames)
assert se.renames==[], "expected NO rename when source already has target name"
print("OK: no rename issued")
```

Prepatch bug re-encoded as an attack: `True`.

RenameIndex.database_forwards idempotency audit for django__django-15695. Gold adds `if old_index.name == self.new_name: return` AFTER both the old_fields (unnamed) resolution and the old_name (named) resolution branches, so the guard covers BOTH paths.

Probes (all run in-image via nl_attack; each uses real ProjectState/ModelState + a FakeSchemaEditor recording rename_index calls and introspection):
- probe_1 (Req 1.1/1.2/2.1, POSITIVE CONTROL): named index already carries target name => 0 rename calls. HOLDS patched, FAILS at base (base issues rename new_idx->new_idx). Discriminates.
- probe_2 (Req 2.2/2.3/1.1): unnamed old_fields index resolved by column introspection already carries target name => introspection permitted but 0 rename calls. HOLDS patched, FAILS at base.
- probe_3 (Req 1.4/3.3): names differ => exactly one rename old_idx->new_idx. HOLDS on both trees (regression).
- probe_4 (Req 3.2): unnamed path, _constraint_names returns 2 => ValueError preserved, no rename. HOLDS patched.
- probe_5 (Req 3.1): allow_migrate_model False => full no-op (no rename, no introspection). HOLDS patched.
- probe_6 (Req 3.4): backward with old_fields => no-op. HOLDS patched.
- probe_7 (Req 3.5): backward (named) renames new->old, restores op.old_name/new_name; subsequent forward renames old->new (round-trip). HOLDS patched.

Candidate patch (weak.diff, 'named_path_only_guard'): places the idempotency guard inside the `else` (old_name) branch only, leaving the unnamed/old_fields path unguarded — the lazy reading permitted by a suite that only checks the named case. Applies cleanly at base. Under this candidate probe_2 is REJECTED (still issues a rename on the unnamed idempotent case), while probes 1 and 3 pass. Since the hidden F2P test (test_rename_index_unnamed_index) exercises exactly the unnamed re-apply path, this candidate would NOT resolve — the suite correctly discriminates it.

>=5 distinct probes all hold on patched tree; positive control (probe_1) discriminates base vs patched (prepatch reproduced); >=1 wrong-fix candidate exercised and rejected. Verdict SOUND. Note: FakeSchemaEditor is a faithful stand-in for the DB layer since the requirements are stated in terms of whether an index-rename statement is issued; probes assert on rename_index invocation, matching the criteria wording.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patched source (via inspect in instance image): forwards resolves old_index in old_fields branch (Index(fields=old_fields, name=matching_index_name[0])) or old_name branch (from_model_state.get_index_by_name(old_name)), then `# Don't alter when the index name is not changed.` / `if old_index.name == self.new_name: return` before building to-state new_index and calling schema_editor.rename_index. Base commit lacks the guard (base probe proceeds past to to_state.models subscript). Requirements' Introduction correctly frames the unnamed-index re-apply crash ('relation already exists') from the issue. No requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior using only public API vocabulary (RenameIndex, old_name/old_fields, unique_together/index_together, forward/backward direction, target new name) — all present in the public problem_statement or legitimate localization of the changed module django/db/migrations/operations/models.py. No hidden-test artifacts appear: the FAIL_TO_PASS test name (test_rename_index_unnamed_index), the test file path (tests/migrations/test_operations.py), the assertNumQueries(0)/assertIndexNameExists mechanics, and the 'new_pony_test_idx' identifier are NOT reproduced. The gold edit invents no identifier (it adds `if old_index.name == self.new_name: return`); the no-op idempotency requirement is a behavioral translation of that check, not a transcription of the test. Requirement 2's named-vs-unnamed split reflects the code's two source-index resolution branches (get_index_by_name vs old_fields lookup), a behavioral generalization rather than test parametrization mirroring. The apply->unapply->apply-again narrative and the PostgreSQL 'relation already exists' crash are drawn directly from the public problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
