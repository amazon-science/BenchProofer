# P2 adversarial audit — django__django-11740

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
# Positive control (Req1.1/1.2/5, F2P): AlterField into cross-app FK -> dependency on referenced app.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def mk(mss):
    ps=ProjectState()
    for m in mss: ps.add_model(m.clone())
    return ps
def changes(b,a):
    return MigrationAutodetector(mk(b),mk(a),None)._detect_changes()

author=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True))])
book=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.ForeignKey("testapp.Author",models.CASCADE)),("title",models.CharField(max_length=200))])
book_int=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.IntegerField()),("title",models.CharField(max_length=200))])

ch=changes([author,book_int],[author,book])
migs=ch.get("otherapp",[])
print("num otherapp migrations:", len(migs))
assert len(migs)==1, "expected 1 migration"
ops=migs[0].operations
print("op types:", [type(o).__name__ for o in ops])
assert [type(o).__name__ for o in ops]==["AlterField"], "expected single AlterField"
deps=migs[0].dependencies
print("dependencies:", deps)
assert ('testapp','__first__') in deps, "missing cross-app creation dependency"
assert len(deps)>=1, "empty dependencies"
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req2.1/2.3: AlterField for a non-relational change -> NO relation dependencies.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def mk(mss):
    ps=ProjectState()
    for m in mss: ps.add_model(m.clone())
    return ps
def changes(b,a):
    return MigrationAutodetector(mk(b),mk(a),None)._detect_changes()

# same app, plain field attribute change (max_length)
a1=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True)),
    ("name",models.CharField(max_length=100))])
a2=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True)),
    ("name",models.CharField(max_length=200))])
ch=changes([a1],[a2])
migs=ch.get("testapp",[])
print("num migrations:", len(migs))
assert len(migs)==1
ops=migs[0].operations
print("op types:", [type(o).__name__ for o in ops])
assert [type(o).__name__ for o in ops]==["AlterField"]
deps=migs[0].dependencies
print("dependencies:", deps)
# a non-relational alteration in a single app should have no dependencies at all
assert deps==[], "non-relational AlterField must have no dependencies, got %r"%(deps,)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req3.4 (+Req1 consistency): a FK that already existed cross-app, only unrelated attrs of
# the relation change (e.g. db_index) -> AlterField SHALL still carry the relation dependency.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def mk(mss):
    ps=ProjectState()
    for m in mss: ps.add_model(m.clone())
    return ps
def changes(b,a):
    return MigrationAutodetector(mk(b),mk(a),None)._detect_changes()

author=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True))])
book_a=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.ForeignKey("testapp.Author",models.CASCADE))])
# only change: add null=True to the same cross-app FK
book_b=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.ForeignKey("testapp.Author",models.CASCADE,null=True))])

ch=changes([author,book_a],[author,book_b])
migs=ch.get("otherapp",[])
print("num migrations:", len(migs))
assert len(migs)==1
ops=[type(o).__name__ for o in migs[0].operations]
print("op types:", ops)
assert ops==["AlterField"], ops
deps=migs[0].dependencies
print("dependencies:", deps)
assert ('testapp','__first__') in deps, "existing-FK alter must still carry relation dep, got %r"%(deps,)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1 (SHALL keep): m2m<->concrete change -> RemoveField + AddField, NOT AlterField.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def mk(mss):
    ps=ProjectState()
    for m in mss: ps.add_model(m.clone())
    return ps
def changes(b,a):
    return MigrationAutodetector(mk(b),mk(a),None)._detect_changes()

author=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True))])
# before: concrete FK; after: m2m -> must be Remove+Add, not Alter
book_fk=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("authors",models.ForeignKey("testapp.Author",models.CASCADE))])
book_m2m=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("authors",models.ManyToManyField("testapp.Author"))])

ch=changes([author,book_fk],[author,book_m2m])
migs=ch.get("otherapp",[])
allops=[type(o).__name__ for m in migs for o in m.operations]
print("all otherapp op types:", allops)
assert "AlterField" not in allops, "must not emit AlterField for m2m<->concrete"
assert "RemoveField" in allops and "AddField" in allops, "expected RemoveField+AddField, got %r"%(allops,)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req2.2 (independence): a relational alter of one field must NOT add deps to another
# field's non-relational AlterField (deps computed per-field).
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def mk(mss):
    ps=ProjectState()
    for m in mss: ps.add_model(m.clone())
    return ps
def changes(b,a):
    return MigrationAutodetector(mk(b),mk(a),None)._detect_changes()

author=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True))])
# otherapp.Book: field 'author' int->FK (relational alter); field 'ztitle' charfield len change (plain)
before=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.IntegerField()),("ztitle",models.CharField(max_length=100))])
after=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.ForeignKey("testapp.Author",models.CASCADE)),("ztitle",models.CharField(max_length=200))])

ch=changes([author,before],[author,after])
migs=ch.get("otherapp",[])
assert len(migs)==1, "expected 1 migration, got %d"%len(migs)
ops=migs[0].operations
# find AlterField ops by field name
by_name={o.name:o for o in ops if type(o).__name__=="AlterField"}
print("AlterField fields:", list(by_name))
assert "author" in by_name and "ztitle" in by_name, "both fields should be AlterField"
mdeps=migs[0].dependencies
# migration-level deps: must include the cross-app dep (from author) but the ztitle op
# must not have caused any extra spurious dep. Check the ztitle op itself has no per-op deps.
# add_operation stores deps at migration level; verify only the relational dep present.
print("migration dependencies:", mdeps)
rel=[d for d in mdeps if d[0]=="testapp"]
assert ('testapp','__first__') in mdeps, "author relational dep missing"
# No dependency should reference otherapp/ztitle as a relation source (spurious)
assert all(not (d[0]=="testapp" and d not in [('testapp','__first__')]) for d in mdeps), "spurious testapp deps: %r"%mdeps
# exactly one relational dep expected (from the single relational field)
assert mdeps.count(('testapp','__first__'))==1, "duplicate/extra relational deps: %r"%mdeps
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control (Req1.1/1.2/5, F2P): AlterField into cross-app FK -> dependency on referenced app.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def mk(mss):
    ps=ProjectState()
    for m in mss: ps.add_model(m.clone())
    return ps
def changes(b,a):
    return MigrationAutodetector(mk(b),mk(a),None)._detect_changes()

author=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True))])
book=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.ForeignKey("testapp.Author",models.CASCADE)),("title",models.CharField(max_length=200))])
book_int=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.IntegerField()),("title",models.CharField(max_length=200))])

ch=changes([author,book_int],[author,book])
migs=ch.get("otherapp",[])
print("num otherapp migrations:", len(migs))
assert len(migs)==1, "expected 1 migration"
ops=migs[0].operations
print("op types:", [type(o).__name__ for o in ops])
assert [type(o).__name__ for o in ops]==["AlterField"], "expected single AlterField"
deps=migs[0].dependencies
print("dependencies:", deps)
assert ('testapp','__first__') in deps, "missing cross-app creation dependency"
assert len(deps)>=1, "empty dependencies"
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11740: generate_altered_fields must attach relation-induced ordering deps to AlterField ops. Probes exercise the requirements' criteria:

- probe_1 (POSITIVE CONTROL, Req1.1/1.2/5, F2P): IntegerField -> cross-app ForeignKey('testapp.Author') emits a single AlterField whose dependencies include ('testapp','__first__'). PATCHED: HOLDS (deps=[('testapp','__first__')]). BASE: VIOLATED ('missing cross-app creation dependency', deps empty). Discriminates.
- probe_2 (Req2.1/2.3 regression): same-app CharField max_length change emits one AlterField with deps==[] (no relation deps). HOLDS on both base and patched (regression protection).
- probe_3 (Req3.4 + Req1 consistency): pre-existing cross-app FK, only null=True changes -> AlterField STILL carries ('testapp','__first__'). PATCHED HOLDS, BASE VIOLATED (deps empty). Discriminates.
- probe_4 (Req3.1 regression): concrete FK -> ManyToManyField yields RemoveField+AddField, never AlterField. HOLDS both trees.
- probe_5 (Req2.2 independence): a model with one relational alter (int->FK) and one plain alter (CharField len) -> exactly one relational dep, no duplicate/spurious testapp deps. PATCHED HOLDS, BASE VIOLATED. Discriminates.

CANDIDATE PATCH (weak.diff): the naive/partial fix a weak reading permits — introduces `dependencies = []` and wires `dependencies=dependencies` into add_operation, but OMITS the `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` line, so deps are always empty. Probes 1,3,5 REJECT it (VIOLATED); probes 2,4 still hold. This demonstrates the suite discriminates the correct fix from a plausible-but-wrong one. No requirements-conforming-yet-nonresolving (too-weak) alternative was found; the suite pins deps to exactly _get_dependencies_for_foreign_key output for the relational branch, matching the gold behavior and the hidden F2P test test_alter_field_to_fk_dependency_other_app.

Swappable-model criterion (Req1.3) could not be exercised standalone (swappable_setting detection requires full app-registry/isolate_lru_cache wiring that didn't reproduce in the probe sandbox); coverage instead rests on probes 1/3/5 for the concrete/existing-FK relational paths. 5 probes all hold patched; positive control discriminates base vs patched; wrong-fix candidate rejected.

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
# Positive control (Req1.1/1.2/5, F2P): AlterField into cross-app FK -> dependency on referenced app.
import sys, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
django.setup()
from django.db import models
from django.db.migrations.state import ProjectState, ModelState
from django.db.migrations.autodetector import MigrationAutodetector

def mk(mss):
    ps=ProjectState()
    for m in mss: ps.add_model(m.clone())
    return ps
def changes(b,a):
    return MigrationAutodetector(mk(b),mk(a),None)._detect_changes()

author=ModelState("testapp","Author",[("id",models.AutoField(primary_key=True))])
book=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.ForeignKey("testapp.Author",models.CASCADE)),("title",models.CharField(max_length=200))])
book_int=ModelState("otherapp","Book",[("id",models.AutoField(primary_key=True)),
    ("author",models.IntegerField()),("title",models.CharField(max_length=200))])

ch=changes([author,book_int],[author,book])
migs=ch.get("otherapp",[])
print("num otherapp migrations:", len(migs))
assert len(migs)==1, "expected 1 migration"
ops=migs[0].operations
print("op types:", [type(o).__name__ for o in ops])
assert [type(o).__name__ for o in ops]==["AlterField"], "expected single AlterField"
deps=migs[0].dependencies
print("dependencies:", deps)
assert ('testapp','__first__') in deps, "missing cross-app creation dependency"
assert len(deps)>=1, "empty dependencies"
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11740: generate_altered_fields must attach relation-induced ordering deps to AlterField ops. Probes exercise the requirements' criteria:

- probe_1 (POSITIVE CONTROL, Req1.1/1.2/5, F2P): IntegerField -> cross-app ForeignKey('testapp.Author') emits a single AlterField whose dependencies include ('testapp','__first__'). PATCHED: HOLDS (deps=[('testapp','__first__')]). BASE: VIOLATED ('missing cross-app creation dependency', deps empty). Discriminates.
- probe_2 (Req2.1/2.3 regression): same-app CharField max_length change emits one AlterField with deps==[] (no relation deps). HOLDS on both base and patched (regression protection).
- probe_3 (Req3.4 + Req1 consistency): pre-existing cross-app FK, only null=True changes -> AlterField STILL carries ('testapp','__first__'). PATCHED HOLDS, BASE VIOLATED (deps empty). Discriminates.
- probe_4 (Req3.1 regression): concrete FK -> ManyToManyField yields RemoveField+AddField, never AlterField. HOLDS both trees.
- probe_5 (Req2.2 independence): a model with one relational alter (int->FK) and one plain alter (CharField len) -> exactly one relational dep, no duplicate/spurious testapp deps. PATCHED HOLDS, BASE VIOLATED. Discriminates.

CANDIDATE PATCH (weak.diff): the naive/partial fix a weak reading permits — introduces `dependencies = []` and wires `dependencies=dependencies` into add_operation, but OMITS the `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` line, so deps are always empty. Probes 1,3,5 REJECT it (VIOLATED); probes 2,4 still hold. This demonstrates the suite discriminates the correct fix from a plausible-but-wrong one. No requirements-conforming-yet-nonresolving (too-weak) alternative was found; the suite pins deps to exactly _get_dependencies_for_foreign_key output for the relational branch, matching the gold behavior and the hidden F2P test test_alter_field_to_fk_dependency_other_app.

Swappable-model criterion (Req1.3) could not be exercised standalone (swappable_setting detection requires full app-registry/isolate_lru_cache wiring that didn't reproduce in the probe sandbox); coverage instead rests on probes 1/3/5 for the concrete/existing-FK relational paths. 5 probes all hold patched; positive control discriminates base vs patched; wrong-fix candidate rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `dependencies=[]` at top of generate_altered_fields loop, `dependencies.extend(self._get_dependencies_for_foreign_key(new_field))` inside the `new_field.remote_field.model` branch (after rename adjustments), and passes `dependencies=dependencies` to add_operation for the AlterField. Requirements model exactly this changed observable behavior at the correct boundary (deps on the emitted AlterField operation), tied biconditionally to whether new_field is a relation, and defer the exact dep contents to _get_dependencies_for_foreign_key. Only cosmetic imprecision: Req1.5 says deps resolve to the referenced app's 'latest migration' while the observed raw dep tuple is ('testapp2','__first__') — that's resolver-side illustration, not a mandated code behavior, and the load-bearing clause ('exactly those returned by _get_dependencies_for_foreign_key') holds. Verified live via nl_attack probe on patched and --base images.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document translates the public problem_statement (UUID/Integer field altered into a cross-app ForeignKey missing migration dependencies) into behavioral EARS requirements. It localizes to generate_altered_fields, _get_dependencies_for_foreign_key, and add_operation(dependencies=...) — all legitimate module/function naming matching the gold edit's touch points, not leaked test content. No test function names (test_alter_field_to_fk_dependency_other_app), file paths (tests/migrations/test_autodetector.py), ModelState fixture names (book_with_no_author_fk), assertion helpers, or dependency tuples like ('testapp','__first__') are quoted or reconstructed. The swappable/through-model acceptance criteria describe the general behavior of the existing _get_dependencies_for_foreign_key helper (referenced by the gold), not the single hidden test's parametrization (there is exactly one FAIL_TO_PASS case, so there is no test enumeration to mirror). Minor watch: line 13 names 'IntegerField' as an example plain field, matching the hidden test's IntegerField fixture, but it is presented as a generic example alongside the public UUIDField and does not reconstruct the test. Verdict: NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
