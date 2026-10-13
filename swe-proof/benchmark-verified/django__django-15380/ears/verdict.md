# P2 adversarial audit — django__django-15380

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
"""Positive control — Req 1.4 / 2.1 / 2.2:
Renaming a model AND one of its fields in one step must not crash and must
produce RenameModel followed by RenameField in a single migration.
Holds on patched tree; crashes (KeyError) at base.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
)
django.setup()

from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner


def make_state(model_name, field_name):
    st = ProjectState()
    st.add_model(ModelState("testapp", model_name, [
        ("id", models.AutoField(primary_key=True)),
        (field_name, models.CharField(max_length=20)),
    ]))
    return st


before = make_state("Foo", "name")
after = make_state("Bar", "title")

qa = MigrationQuestioner({"ask_rename_model": True, "ask_rename": True})
ad = MigrationAutodetector(before, after, qa)

try:
    changes = ad._detect_changes()
except Exception as e:
    print("FAIL: _detect_changes raised %r" % e)
    sys.exit(1)

migs = changes.get("testapp", [])
print("num migrations for testapp:", len(migs))
if len(migs) != 1:
    print("FAIL: expected exactly 1 migration, got", len(migs))
    sys.exit(1)

ops = migs[0].operations
names = [op.__class__.__name__ for op in ops]
print("operations:", names)
if names != ["RenameModel", "RenameField"]:
    print("FAIL: expected [RenameModel, RenameField], got", names)
    sys.exit(1)

print("PASS: model+field rename detected without crash, correct op order")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.3 / 2.4: the RenameModel op must carry old=Foo new=Bar, and the
RenameField op must carry old=name new=title (correct old/new names)."""
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner

def mk(mn, fn):
    st = ProjectState()
    st.add_model(ModelState("testapp", mn, [
        ("id", models.AutoField(primary_key=True)),
        (fn, models.CharField(max_length=20))]))
    return st

qa = MigrationQuestioner({"ask_rename_model": True, "ask_rename": True})
ad = MigrationAutodetector(mk("Foo", "name"), mk("Bar", "title"), qa)
ops = ad._detect_changes()["testapp"][0].operations
rm = ops[0]; rf = ops[1]
print("RenameModel old=%s new=%s" % (rm.old_name, rm.new_name))
print("RenameField model=%s old=%s new=%s" % (rf.model_name, rf.old_name, rf.new_name))
ok = (rm.old_name == "Foo" and rm.new_name == "Bar"
      and rf.old_name == "name" and rf.new_name == "title")
if not ok:
    print("FAIL: names incorrect"); sys.exit(1)
print("PASS: rename op names correct"); sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1: field rename WITHOUT a model rename must still be detected as a
RenameField with correct old/new names (regression)."""
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner

def mk(fn):
    st = ProjectState()
    st.add_model(ModelState("testapp", "Foo", [
        ("id", models.AutoField(primary_key=True)),
        (fn, models.CharField(max_length=20))]))
    return st

qa = MigrationQuestioner({"ask_rename": True})
ad = MigrationAutodetector(mk("name"), mk("title"), qa)
migs = ad._detect_changes().get("testapp", [])
ops = migs[0].operations if migs else []
names = [o.__class__.__name__ for o in ops]
print("operations:", names)
if names != ["RenameField"]:
    print("FAIL: expected [RenameField]"); sys.exit(1)
rf = ops[0]
print("RenameField old=%s new=%s" % (rf.old_name, rf.new_name))
if rf.old_name != "name" or rf.new_name != "title":
    print("FAIL: names incorrect"); sys.exit(1)
print("PASS: plain field rename preserved"); sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.2: model rename WITHOUT any field rename must still produce a single
RenameModel with correct old/new names (regression)."""
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner

def mk(mn):
    st = ProjectState()
    st.add_model(ModelState("testapp", mn, [
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=20))]))
    return st

qa = MigrationQuestioner({"ask_rename_model": True})
ad = MigrationAutodetector(mk("Foo"), mk("Bar"), qa)
migs = ad._detect_changes().get("testapp", [])
ops = migs[0].operations if migs else []
names = [o.__class__.__name__ for o in ops]
print("operations:", names)
if names != ["RenameModel"]:
    print("FAIL: expected [RenameModel]"); sys.exit(1)
rm = ops[0]
print("RenameModel old=%s new=%s" % (rm.old_name, rm.new_name))
if rm.old_name != "Foo" or rm.new_name != "Bar":
    print("FAIL: names incorrect"); sys.exit(1)
print("PASS: plain model rename preserved"); sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.4: model names treated case-insensitively — changing only the case of
a model name produces NO migration (regression)."""
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner

def mk(mn):
    st = ProjectState()
    st.add_model(ModelState("testapp", mn, [
        ("id", models.AutoField(primary_key=True)),
        ("name", models.CharField(max_length=20))]))
    return st

# Foo -> foo (case-only change)
qa = MigrationQuestioner({"ask_rename_model": True, "ask_rename": True})
ad = MigrationAutodetector(mk("Foo"), mk("foo"), qa)
changes = ad._detect_changes()
migs = changes.get("testapp", [])
print("num migrations:", len(migs))
if migs:
    print("ops:", [o.__class__.__name__ for o in migs[0].operations])
    print("FAIL: expected no migration for case-only change"); sys.exit(1)
print("PASS: case-only model change produces no migration"); sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.3 / 2.5: field rename with db_column preserving the old column name.
When the renamed field sets db_column to the old field's name, the autodetector
must still recognize the rename (RenameField) rather than drop+add, and no
AlterField for the column should be needed. Combined with a simultaneous model
rename to exercise the fixed path."""
import sys, django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"])
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner

# before: Foo.name ; after: Foo.title with db_column="name" (plain field rename,
# preserving column) -- Req 3.3 without a model rename.
def mk(fn, dbcol=None):
    st = ProjectState()
    st.add_model(ModelState("testapp", "Foo", [
        ("id", models.AutoField(primary_key=True)),
        (fn, models.CharField(max_length=20, db_column=dbcol))]))
    return st

qa = MigrationQuestioner({"ask_rename": True})
ad = MigrationAutodetector(mk("name"), mk("title", dbcol="name"), qa)
migs = ad._detect_changes().get("testapp", [])
ops = migs[0].operations if migs else []
names = [o.__class__.__name__ for o in ops]
print("operations:", names)
# must contain a RenameField (recognized as rename, not RemoveField+AddField)
if "RenameField" not in names:
    print("FAIL: field not recognized as rename"); sys.exit(1)
if "RemoveField" in names or "AddField" in names:
    print("FAIL: treated as drop+add"); sys.exit(1)
rf = [o for o in ops if o.__class__.__name__ == "RenameField"][0]
print("RenameField old=%s new=%s" % (rf.old_name, rf.new_name))
if rf.old_name != "name" or rf.new_name != "title":
    print("FAIL: rename names incorrect"); sys.exit(1)
print("PASS: db_column-preserving field rename detected as RenameField"); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Req 1.4 / 2.1 / 2.2:
Renaming a model AND one of its fields in one step must not crash and must
produce RenameModel followed by RenameField in a single migration.
Holds on patched tree; crashes (KeyError) at base.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
)
django.setup()

from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner


def make_state(model_name, field_name):
    st = ProjectState()
    st.add_model(ModelState("testapp", model_name, [
        ("id", models.AutoField(primary_key=True)),
        (field_name, models.CharField(max_length=20)),
    ]))
    return st


before = make_state("Foo", "name")
after = make_state("Bar", "title")

qa = MigrationQuestioner({"ask_rename_model": True, "ask_rename": True})
ad = MigrationAutodetector(before, after, qa)

try:
    changes = ad._detect_changes()
except Exception as e:
    print("FAIL: _detect_changes raised %r" % e)
    sys.exit(1)

migs = changes.get("testapp", [])
print("num migrations for testapp:", len(migs))
if len(migs) != 1:
    print("FAIL: expected exactly 1 migration, got", len(migs))
    sys.exit(1)

ops = migs[0].operations
names = [op.__class__.__name__ for op in ops]
print("operations:", names)
if names != ["RenameModel", "RenameField"]:
    print("FAIL: expected [RenameModel, RenameField], got", names)
    sys.exit(1)

print("PASS: model+field rename detected without crash, correct op order")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15380: generate_renamed_fields() looked up the owning model in to_state.models under the OLD name; gold fixes it to use the current name (model_name). 

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req 1.4/2.1/2.2): simultaneous Foo->Bar model rename + name->title field rename yields exactly ONE migration with ops [RenameModel, RenameField]. HOLDS patched; at base raises KeyError(('testapp','foo')) => prepatch reproduced.
- probe_2 (Req 2.3/2.4): RenameModel old=Foo new=Bar, RenameField old=name new=title. HOLDS.
- probe_3 (Req 3.1): plain field rename (no model rename) still -> [RenameField] name->title. HOLDS.
- probe_4 (Req 3.2): plain model rename (no field rename) still -> [RenameModel] Foo->Bar. HOLDS.
- probe_5 (Req 3.4): case-only model change Foo->foo produces NO migration. HOLDS.
- probe_6 (Req 3.3/2.5): field rename with db_column preserving old column recognized as RenameField (not RemoveField+AddField). HOLDS (ops [AlterField, RenameField]).

Wrong-fix candidate 'swallow_keyerror' (weak.diff): wraps the buggy to_state[old_name] lookup in try/except KeyError: continue. This avoids the crash (a lazy reading of Req 1.4 permits it) but SKIPS field-rename detection in the simultaneous case, degenerating it into RemoveField+AddField. REJECTED by probe_1 (got [RenameModel, RemoveField, AddField]) and probe_2 (no old_name attr). Demonstrates the suite discriminates the discriminating behavior beyond mere no-crash. Positive control discriminates (holds patched, fails at base). Verdict SOUND.

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
"""Positive control — Req 1.4 / 2.1 / 2.2:
Renaming a model AND one of its fields in one step must not crash and must
produce RenameModel followed by RenameField in a single migration.
Holds on patched tree; crashes (KeyError) at base.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
)
django.setup()

from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import MigrationQuestioner


def make_state(model_name, field_name):
    st = ProjectState()
    st.add_model(ModelState("testapp", model_name, [
        ("id", models.AutoField(primary_key=True)),
        (field_name, models.CharField(max_length=20)),
    ]))
    return st


before = make_state("Foo", "name")
after = make_state("Bar", "title")

qa = MigrationQuestioner({"ask_rename_model": True, "ask_rename": True})
ad = MigrationAutodetector(before, after, qa)

try:
    changes = ad._detect_changes()
except Exception as e:
    print("FAIL: _detect_changes raised %r" % e)
    sys.exit(1)

migs = changes.get("testapp", [])
print("num migrations for testapp:", len(migs))
if len(migs) != 1:
    print("FAIL: expected exactly 1 migration, got", len(migs))
    sys.exit(1)

ops = migs[0].operations
names = [op.__class__.__name__ for op in ops]
print("operations:", names)
if names != ["RenameModel", "RenameField"]:
    print("FAIL: expected [RenameModel, RenameField], got", names)
    sys.exit(1)

print("PASS: model+field rename detected without crash, correct op order")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15380: generate_renamed_fields() looked up the owning model in to_state.models under the OLD name; gold fixes it to use the current name (model_name). 

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL; Req 1.4/2.1/2.2): simultaneous Foo->Bar model rename + name->title field rename yields exactly ONE migration with ops [RenameModel, RenameField]. HOLDS patched; at base raises KeyError(('testapp','foo')) => prepatch reproduced.
- probe_2 (Req 2.3/2.4): RenameModel old=Foo new=Bar, RenameField old=name new=title. HOLDS.
- probe_3 (Req 3.1): plain field rename (no model rename) still -> [RenameField] name->title. HOLDS.
- probe_4 (Req 3.2): plain model rename (no field rename) still -> [RenameModel] Foo->Bar. HOLDS.
- probe_5 (Req 3.4): case-only model change Foo->foo produces NO migration. HOLDS.
- probe_6 (Req 3.3/2.5): field rename with db_column preserving old column recognized as RenameField (not RemoveField+AddField). HOLDS (ops [AlterField, RenameField]).

Wrong-fix candidate 'swallow_keyerror' (weak.diff): wraps the buggy to_state[old_name] lookup in try/except KeyError: continue. This avoids the crash (a lazy reading of Req 1.4 permits it) but SKIPS field-rename detection in the simultaneous case, degenerating it into RemoveField+AddField. REJECTED by probe_1 (got [RenameModel, RemoveField, AddField]) and probe_2 (no old_name attr). Demonstrates the suite discriminates the discriminating behavior beyond mere no-crash. Positive control discriminates (holds patched, fails at base). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe (patched, exit 0): OPS ['RenameModel','RenameField'], RenameModel MyModel->MyModel2, RenameField field_a->field_b. Probe (base, exit 1): KeyError: ('testapp','mymodel') at autodetector.py generate_renamed_fields — identical to problem_statement traceback. Requirement boundary is the changed observable behavior (simultaneous model+field rename), not a narrower slice; Req 1 additionally describes the exact helper mechanics of the changed line, consistent with the fix. Req 3 correctly frames the surgical no-regression constraint.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to generate_renamed_fields(), renamed_models, and the from_state/to_state lookups — all of which are already public: the problem_statement includes the full traceback with the exact buggy line 'new_model_state = self.to_state.models[app_label, old_model_name]', the KeyError, and the 'rename a model and field in a single step' scenario. Requirements translate the fix into behavioral EARS criteria (index prior snapshot by prior name, current snapshot by current name; emit RenameModel then RenameField) at the correct altitude. No test-invented identifiers leak: the hidden test's concrete values (Author/RenamedAuthor, name/renamed_name, ask_rename_model/ask_rename, test function name test_rename_field_with_renamed_model, file path tests/migrations/test_autodetector.py, assert helpers) do NOT appear anywhere in requirements.md. Req 2's 'single migration' / 'RenameModel followed by RenameField' describes the natural correct output, not the parametrization. Req 3's preserve-behavior list enumerates broad, publicly-known autodetector behaviors (case-insensitivity, FK/M2M, db_column) as regression guarantees, not specific test reconstructions. No quoted test/gold code, no paths, no ids.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
