# P2 adversarial audit — django__django-13964

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Requirement 1.3 / positive control:
Child with CharField primary_key='' (empty string) assigned to parent BEFORE
the child's pk is set. After child pk set and saved, saving the owner must adopt
the string pk into the FK attname (not leave it '').
HOLDS on patched, FAILS at base (base only adopts on None)."""
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class ParentModel(models.Model):
    name = models.CharField(primary_key=True, max_length=15)
    class Meta: app_label = 'probeapp'
class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ParentModel); se.create_model(ChildModel)

parent = ParentModel()               # name == '' (empty string pk)
child = ChildModel(parent=parent)    # assign FK before pk known
parent.name = 'abc'                  # now set the pk
parent.save()
child.save()

observed = child.parent_id
print("child.parent_id after save =", repr(observed))
if observed == 'abc':
    print("PASS: adopted the string pk")
    sys.exit(0)
print("FAIL: FK value not adopted (empty-string not treated as empty)")
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection
# Requirement 1.4: when the stored FK value is NON-EMPTY (and differs from obj.pk),
# it SHALL be left unchanged (not overwritten by obj.pk). Keeps the relation cached.
class ParentModel(models.Model):
    name = models.CharField(primary_key=True, max_length=15)
    class Meta: app_label = 'probeapp'
class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'
with connection.schema_editor() as se:
    se.create_model(ParentModel); se.create_model(ChildModel)

p = ParentModel(name='abc'); p.save()
child = ChildModel(parent=p)          # caches obj(pk='abc'), parent_id='abc'
child.parent_id = 'xyz'               # stored value now non-empty, != obj.pk
fld = ChildModel._meta.get_field('parent')
print("cached after setting attname =", fld.is_cached(child))
if not fld.is_cached(child):
    # re-cache without touching attname
    fld.set_cached_value(child, p)
print("cached (final) =", fld.is_cached(child), "| parent_id before =", repr(child.parent_id))
child._prepare_related_fields_for_save('save')
observed = child.parent_id
print("parent_id after prepare =", repr(observed))
if observed == 'xyz':
    print("PASS: non-empty stored value preserved (not overwritten)")
    sys.exit(0)
print("FAIL: non-empty value was overwritten with obj.pk")
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection
# Requirement 2.1: unsaved related object (pk None) on save -> ValueError naming the field.
# Requirement 2.2: on a single-valued (OneToOne) relation the unsaved object is removed
# from the relation's cached value (reverse cache) before raising.
class AParent(models.Model):
    x = models.IntegerField(default=0)
    class Meta: app_label = 'probeapp'
class O2OChild(models.Model):
    parent = models.OneToOneField(AParent, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'
with connection.schema_editor() as se:
    se.create_model(AParent); se.create_model(O2OChild)

ap = AParent()                       # unsaved -> pk None
ac = O2OChild(parent=ap)             # caches forward (on ac) and reverse (on ap)
rev = O2OChild._meta.get_field('parent').remote_field
print("reverse cached before =", rev.is_cached(ap))
raised = False; msg = ''
try:
    ac._prepare_related_fields_for_save('save')
except ValueError as e:
    raised = True; msg = str(e)
print("ValueError raised =", raised, "| msg =", msg)
rev_after = rev.is_cached(ap)
print("reverse cached after =", rev_after)
if raised and 'parent' in msg and 'prohibited' in msg and (not rev_after):
    print("PASS: raised naming field, single-valued reverse cache removed")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection
# Requirement 2.3: related object has pk and stored value already non-empty & equal ->
# preserved, save completes normally.
class ParentModel(models.Model):
    name = models.CharField(primary_key=True, max_length=15)
    class Meta: app_label = 'probeapp'
class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'
with connection.schema_editor() as se:
    se.create_model(ParentModel); se.create_model(ChildModel)

p = ParentModel(name='abc'); p.save()
child = ChildModel(parent=p)   # parent_id already 'abc' == pk
child.save()
print("parent_id after save =", repr(child.parent_id))
ok = child.parent_id == 'abc' and ChildModel.objects.filter(parent=p).count() == 1
print("row matches by parent =", ChildModel.objects.filter(parent=p).count())
if ok:
    print("PASS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection
# Requirement 1.5: after adoption, filter by fk matches the row; filter fk == '' does NOT match.
class ParentModel(models.Model):
    name = models.CharField(primary_key=True, max_length=15)
    class Meta: app_label = 'probeapp'
class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'
with connection.schema_editor() as se:
    se.create_model(ParentModel); se.create_model(ChildModel)

parent = ParentModel()
child = ChildModel(parent=parent)
parent.name = 'abc'; parent.save(); child.save()

by_parent = ChildModel.objects.filter(parent=parent).count()
by_empty = ChildModel.objects.filter(parent_id='').count()
print("match by parent =", by_parent, "; match by parent_id='' =", by_empty)
if by_parent == 1 and by_empty == 0:
    print("PASS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection
# Requirement 3.3 (regression): auto numeric pk that becomes available only after saving
# is still adopted (the pre-existing None case must keep working).
class NParent(models.Model):
    class Meta: app_label = 'probeapp'
class NChild(models.Model):
    parent = models.ForeignKey(NParent, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'
with connection.schema_editor() as se:
    se.create_model(NParent); se.create_model(NChild)

parent = NParent()
child = NChild(parent=parent)   # parent_id is None
parent.save()                   # auto pk assigned
child.save()
print("child.parent_id =", repr(child.parent_id), "parent.pk =", repr(parent.pk))
if child.parent_id == parent.pk and child.parent_id is not None:
    print("PASS")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 1.3 / positive control:
Child with CharField primary_key='' (empty string) assigned to parent BEFORE
the child's pk is set. After child pk set and saved, saving the owner must adopt
the string pk into the FK attname (not leave it '').
HOLDS on patched, FAILS at base (base only adopts on None)."""
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class ParentModel(models.Model):
    name = models.CharField(primary_key=True, max_length=15)
    class Meta: app_label = 'probeapp'
class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ParentModel); se.create_model(ChildModel)

parent = ParentModel()               # name == '' (empty string pk)
child = ChildModel(parent=parent)    # assign FK before pk known
parent.name = 'abc'                  # now set the pk
parent.save()
child.save()

observed = child.parent_id
print("child.parent_id after save =", repr(observed))
if observed == 'abc':
    print("PASS: adopted the string pk")
    sys.exit(0)
print("FAIL: FK value not adopted (empty-string not treated as empty)")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13964 (v4.0). Gold patch changes the empty-check in Model._prepare_related_fields_for_save from `getattr(self, field.attname) is None` to `... in field.empty_values`, so an empty-string FK value (from a CharField primary_key='') is also adopted from the related object's pk.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.3, POSITIVE CONTROL): child with CharField pk assigned to owner before pk set; after parent.name='abc';parent.save();child.save() the FK attname becomes 'abc'. HOLDS patched, FAILS at base (base only adopts on None; at base child.save() hits FOREIGN KEY constraint failed because parent_id stayed ''). Discriminates.
- probe_2 (Req 1.4 / 3.4): non-empty stored FK value ('xyz') differing from obj.pk is preserved, not overwritten. Rejects weak_overwrite candidate.
- probe_3 (Req 2.1/2.2): unsaved related object (pk None) -> ValueError naming 'parent'; on a OneToOne relation the reverse cache on the related obj is removed before raising.
- probe_4 (Req 2.3): related obj with pk, stored value already non-empty & equal -> preserved, save completes, row queryable by parent.
- probe_5 (Req 1.5): after adoption, filter(parent=...) matches the row (count 1) and filter(parent_id='') does NOT match (count 0).
- probe_6 (Req 3.3 regression): auto numeric pk available only after saving is still adopted (pre-existing None case). Rejects weak_partial candidate (which drops None handling -> NOT NULL/IntegrityError).

Candidate wrong patches, both REJECTED by the suite:
- weak_partial (`elif ... == ''`): fixes the empty-string case but regresses the None/auto-pk adoption -> probe_6 VIOLATED.
- weak_overwrite (`else:` always adopt): overwrites a valid non-empty differing FK -> probe_2 VIOLATED.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and every requirement-conforming-but-wrong candidate is caught. No too-weak or violation finding. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Requirement 1.3 / positive control:
Child with CharField primary_key='' (empty string) assigned to parent BEFORE
the child's pk is set. After child pk set and saved, saving the owner must adopt
the string pk into the FK attname (not leave it '').
HOLDS on patched, FAILS at base (base only adopts on None)."""
import sys, types, tempfile
_d = tempfile.mkdtemp()
_m = types.ModuleType('probeapp'); _m.__path__ = [_d]; _m.__file__ = _d + '/__init__.py'
sys.modules['probeapp'] = _m
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class ParentModel(models.Model):
    name = models.CharField(primary_key=True, max_length=15)
    class Meta: app_label = 'probeapp'
class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ParentModel); se.create_model(ChildModel)

parent = ParentModel()               # name == '' (empty string pk)
child = ChildModel(parent=parent)    # assign FK before pk known
parent.name = 'abc'                  # now set the pk
parent.save()
child.save()

observed = child.parent_id
print("child.parent_id after save =", repr(observed))
if observed == 'abc':
    print("PASS: adopted the string pk")
    sys.exit(0)
print("FAIL: FK value not adopted (empty-string not treated as empty)")
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13964 (v4.0). Gold patch changes the empty-check in Model._prepare_related_fields_for_save from `getattr(self, field.attname) is None` to `... in field.empty_values`, so an empty-string FK value (from a CharField primary_key='') is also adopted from the related object's pk.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req 1.1/1.3, POSITIVE CONTROL): child with CharField pk assigned to owner before pk set; after parent.name='abc';parent.save();child.save() the FK attname becomes 'abc'. HOLDS patched, FAILS at base (base only adopts on None; at base child.save() hits FOREIGN KEY constraint failed because parent_id stayed ''). Discriminates.
- probe_2 (Req 1.4 / 3.4): non-empty stored FK value ('xyz') differing from obj.pk is preserved, not overwritten. Rejects weak_overwrite candidate.
- probe_3 (Req 2.1/2.2): unsaved related object (pk None) -> ValueError naming 'parent'; on a OneToOne relation the reverse cache on the related obj is removed before raising.
- probe_4 (Req 2.3): related obj with pk, stored value already non-empty & equal -> preserved, save completes, row queryable by parent.
- probe_5 (Req 1.5): after adoption, filter(parent=...) matches the row (count 1) and filter(parent_id='') does NOT match (count 0).
- probe_6 (Req 3.3 regression): auto numeric pk available only after saving is still adopted (pre-existing None case). Rejects weak_partial candidate (which drops None handling -> NOT NULL/IntegrityError).

Candidate wrong patches, both REJECTED by the suite:
- weak_partial (`elif ... == ''`): fixes the empty-string case but regresses the None/auto-pk adoption -> probe_6 VIOLATED.
- weak_overwrite (`else:` always adopt): overwrites a valid non-empty differing FK -> probe_2 VIOLATED.

Conclusion: >=5 distinct probes all hold on the patched tree, positive control discriminates base vs patched, and every requirement-conforming-but-wrong candidate is caught. No too-weak or violation finding. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on the instance image (patched + --base). Patched function confirmed: `elif getattr(self, field.attname) in field.empty_values: setattr(self, field.attname, obj.pk)`; empty_values=[None,'',[],(),{}] so R1.2's 'includes None and ''' is exact, and 0 is NOT empty (R1.4 respected). F2P test test_save_fk_after_parent_with_non_numeric_pk_set_on_child is exactly R1.3. Minor wording imprecision in R3.2 (says to_field value is 'populated from the target-field value using the same empty-value adoption rule', whereas the adoption branch literally assigns obj.pk; for the gold-tested to_field scenario the value is set at assignment-time by the descriptor and the adoption branch is not reached, so the OBSERVABLE outcome — child.parent_id == parent.name — still holds and matches the patched code). This is a mechanism-description looseness, not an observable behavioral divergence, so it does not break faithfulness. Modeling boundary is the changed observable behavior (empty-value adoption), not a narrow slice — faithful.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to Model._prepare_related_fields_for_save in django/db/models/base.py (legitimate) and translates the behavior into EARS requirements. The core FAIL_TO_PASS scenario (non-numeric/CharField primary key, empty-string '' stored FK value, filter(product_id='') incorrectly matching) is already fully public in problem_statement, including the empty-string-vs-None distinction that IS the gold edit's essence. The gold mechanism (is None -> in field.empty_values) is paraphrased as 'recognized empty values for the field', not quoted. Crucially, none of the test/fix-invented identifiers leak: ParentStringPrimaryKey, ChildStringPrimaryKeyParent, and the test function name test_save_fk_after_parent_with_non_numeric_pk_set_on_child do not appear. Requirements 2 and 3 enumerate to_field/nullable-FK/auto-PK/stale-cache dimensions that align with PASS_TO_PASS tests, but these are stated as general behavioral/regression properties (to_field being a public Django feature), not test code, parametrization ids, or case lists that reconstruct the hidden tests. No quoted test or gold code, no file paths, no test names.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
