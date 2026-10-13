# P2 adversarial audit — django__django-12273

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_propagate.py`, `probe_2_none_clears.py`, `probe_3_link_eq_pk.py`, `probe_4_unrelated_untouched.py`, `probe_5_read_and_plain.py`, `probe_db.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_db.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_propagate.py` → holds on the patched tree (good)

```python
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'
class Senator(Congressman):
    class Meta: app_label='probeapp'
class Plain(models.Model):
    x = models.IntegerField(default=0)
    class Meta: app_label='probeapp'
class Place(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Restaurant(Place):
    place_ptr = models.OneToOneField(Place, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    class Meta: app_label='probeapp'


c = Congressman()
c.pk = 5
own = getattr(c, Congressman._meta.pk.attname)   # person_ptr_id
pol = getattr(c, "politician_id", "MISSING")
print("own(%s)=%r politician_id=%r pk=%r" % (Congressman._meta.pk.attname, own, pol, c.pk))
ok = (own == 5) and (pol == 5) and (c.pk == 5)
print("REQ1_PROP_OK" if ok else "REQ1_PROP_FAIL"); sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_none_clears.py` → holds on the patched tree (good)

```python
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'
class Senator(Congressman):
    class Meta: app_label='probeapp'
class Plain(models.Model):
    x = models.IntegerField(default=0)
    class Meta: app_label='probeapp'
class Place(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Restaurant(Place):
    place_ptr = models.OneToOneField(Place, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    class Meta: app_label='probeapp'


c = Congressman()
c.pk = 5
c.pk = None
own = getattr(c, Congressman._meta.pk.attname)
pol = getattr(c, "politician_id", "MISSING")
print("own=%r politician_id=%r pk=%r" % (own, pol, c.pk))
ok = (own is None) and (pol is None) and (c.pk is None)
print("REQ1_4_OK" if ok else "REQ1_4_FAIL"); sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_link_eq_pk.py` → holds on the patched tree (good)

```python
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'
class Senator(Congressman):
    class Meta: app_label='probeapp'
class Plain(models.Model):
    x = models.IntegerField(default=0)
    class Meta: app_label='probeapp'
class Place(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Restaurant(Place):
    place_ptr = models.OneToOneField(Place, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    class Meta: app_label='probeapp'


r = Restaurant()
# sanity: this model has a parent link equal to its own pk, target_field.attname="id"
link = list(Restaurant._meta.parents.values())[0]
assert link == Restaurant._meta.pk, "test model precondition"
assert link.target_field.attname == "id", link.target_field.attname
r.pk = 9
print("place_ptr_id=%r id=%r pk=%r" % (getattr(r,"place_ptr_id",None), getattr(r,"id",None), r.pk))
# Req2.2: the link==pk must NOT be double-written; own pk attname is place_ptr_id.
# A misfiring impl that writes target_field.attname would set id=9. Correct: id stays None.
ok = (getattr(r,"place_ptr_id",None) == 9) and (getattr(r,"id",None) is None) and (r.pk == 9)
print("REQ2_2_OK" if ok else "REQ2_2_FAIL"); sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_unrelated_untouched.py` → holds on the patched tree (good)

```python
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'
class Senator(Congressman):
    class Meta: app_label='probeapp'
class Plain(models.Model):
    x = models.IntegerField(default=0)
    class Meta: app_label='probeapp'
class Place(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Restaurant(Place):
    place_ptr = models.OneToOneField(Place, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    class Meta: app_label='probeapp'


c = Congressman()
c.name = "Alice"; c.title = "Speaker"; c.state = "CA"
c.pk = 42
print("name=%r title=%r state=%r" % (c.name, c.title, c.state))
ok = (c.name == "Alice") and (c.title == "Speaker") and (c.state == "CA")
print("REQ2_3_OK" if ok else "REQ2_3_FAIL"); sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_read_and_plain.py` → holds on the patched tree (good)

```python
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'
class Senator(Congressman):
    class Meta: app_label='probeapp'
class Plain(models.Model):
    x = models.IntegerField(default=0)
    class Meta: app_label='probeapp'
class Place(models.Model):
    name = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Restaurant(Place):
    place_ptr = models.OneToOneField(Place, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    class Meta: app_label='probeapp'


# Req4.1 read: pk reflects own pk attname
p = Plain()
setattr(p, Plain._meta.pk.attname, 11)
r_read = (p.pk == 11)
# Req4.2: assigning pk on a non-MTI model sets own pk and makes NO additional key writes.
p2 = Plain()
before = {k:v for k,v in vars(p2).items() if not k.startswith("_")}
p2.pk = 77
after = {k:v for k,v in vars(p2).items() if not k.startswith("_")}
changed = {k for k in set(before)|set(after) if before.get(k)!=after.get(k)}
own = Plain._meta.pk.attname
print("read_ok=%s changed=%s own=%s parents=%s" % (r_read, sorted(changed), own, dict(Plain._meta.parents)))
# only the own pk attribute may have changed; no parents => no extra writes
ok = r_read and (changed <= {own}) and (getattr(p2, own) == 77) and (len(Plain._meta.parents)==0)
print("REQ4_OK" if ok else "REQ4_FAIL"); sys.exit(0 if ok else 1)
```

Attack 6 — `probe_db.py` → holds on the patched tree (good)

```python
# Requirement 3 (+1.4, positive-control-grade): clearing pk on a multi-inheritance
# instance and saving inserts NEW rows at every level; existing parent rows retain
# their original values. Mirrors F2P test_..._multi_inheritance with own models.
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models, connection
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'

with connection.schema_editor() as se:
    for M in (Person, Politician, Congressman):
        se.create_model(M)

c1 = Congressman.objects.create(state="PA", name="John", title="senator 1")
c2 = Person.objects.get(pk=c1.pk).congressman
c2.pk = None
c2.id = None
c2.politician_ptr_id = None
c2.name = "Bill"; c2.title = "senator 2"
c2.save()

n = Congressman.objects.count()
person_john = Person.objects.get(pk=c1.pk).name
pol_title = Politician.objects.get(pk=c1.politician_ptr_id).title
print("Congressman.count=%d Person(orig).name=%r Politician(orig).title=%r" % (n, person_john, pol_title))
ok = (n == 2) and (person_john == "John") and (pol_title == "senator 1")
print("REQ3_OK" if ok else "REQ3_FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_db.py`

```python
# Requirement 3 (+1.4, positive-control-grade): clearing pk on a multi-inheritance
# instance and saving inserts NEW rows at every level; existing parent rows retain
# their original values. Mirrors F2P test_..._multi_inheritance with own models.
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models, connection
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'

with connection.schema_editor() as se:
    for M in (Person, Politician, Congressman):
        se.create_model(M)

c1 = Congressman.objects.create(state="PA", name="John", title="senator 1")
c2 = Person.objects.get(pk=c1.pk).congressman
c2.pk = None
c2.id = None
c2.politician_ptr_id = None
c2.name = "Bill"; c2.title = "senator 2"
c2.save()

n = Congressman.objects.count()
person_john = Person.objects.get(pk=c1.pk).name
pol_title = Politician.objects.get(pk=c1.politician_ptr_id).title
print("Congressman.count=%d Person(orig).name=%r Politician(orig).title=%r" % (n, person_john, pol_title))
ok = (n == 2) and (person_john == "John") and (pol_title == "senator 1")
print("REQ3_OK" if ok else "REQ3_FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12273: Model._set_pk_val must re-key the whole MTI inheritance chain. Gold patch loops self._meta.parents.values(); for each parent_link that is truthy and != self._meta.pk, setattr(target_field.attname, value), then sets own pk attname.

### PROBE SUITE (all HOLD on gold-patched tree; all runs completed):
- probe_1_propagate.py (Req1.1/1.2/1.3): Congressman().pk=5 => own person_ptr_id=5 AND ancestor politician_id=5. GOLD HOLDS, BASE VIOLATED (politician_id=None) — discriminator.
- probe_2_none_clears.py (Req1.4): pk=None clears own + politician_id. Holds gold & base (base already zeroes own; used for spec-fidelity of the clear path).
- probe_3_link_eq_pk.py (Req2.2/4.3): Restaurant with place_ptr parent_link==pk (target_field.attname='id'); pk=9 => place_ptr_id=9, id stays None (no double/misfire write). Holds.
- probe_4_unrelated_untouched.py (Req2.3): assigning pk leaves name/title/state unchanged. Holds.
- probe_5_read_and_plain.py (Req4.1/4.2): pk read returns own attr; non-MTI Plain model assign changes ONLY own pk attr, parents={}. Holds.
- probe_db.py (Req3.1/3.2/3.3, POSITIVE CONTROL): DB-backed replica of F2P multi_inheritance — create Congressman, fetch via Person, clear pk/id/politician_ptr_id, resave => count==2 and original Person.name='John', Politician.title='senator 1' preserved. GOLD HOLDS (exit0), BASE VIOLATED (integrity/overwrite error). prepatch_reproduced=true.

### CANDIDATE WRONG PATCHES (both REJECTED => suite discriminates wrong impls):
- weak_attname.diff: uses parent_link.attname instead of target_field.attname. REJECTED by probe_1 (politician_id stays None) and probe_db (F2P scenario errors). Confirms Req1.2's target_field.attname requirement is load-bearing.
- weak_noneonly.diff: propagates only when value is None. REJECTED by probe_1 (non-None assignment doesn't reach ancestor) — enforces Req1.2/1.3 apply for any assigned value, not just clearing.

Environment: py3.6 image (subprocess capture_output unavailable); probes use in-process settings.configure with a temp app package (container FS is read-only under /work except tempdir). No probe timed out; SOUND after 6 probes hold and positive control discriminates base vs gold, with >=1 candidate exercised and rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_propagate.py`, `probe_2_none_clears.py`, `probe_3_link_eq_pk.py`, `probe_4_unrelated_untouched.py`, `probe_5_read_and_plain.py`, `probe_db.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_db.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_propagate.py` → holds on the patched tree (good)

Attack 2 — `probe_2_none_clears.py` → holds on the patched tree (good)

Attack 3 — `probe_3_link_eq_pk.py` → holds on the patched tree (good)

Attack 4 — `probe_4_unrelated_untouched.py` → holds on the patched tree (good)

Attack 5 — `probe_5_read_and_plain.py` → holds on the patched tree (good)

Attack 6 — `probe_db.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_db.py`

```python
# Requirement 3 (+1.4, positive-control-grade): clearing pk on a multi-inheritance
# instance and saving inserts NEW rows at every level; existing parent rows retain
# their original values. Mirrors F2P test_..._multi_inheritance with own models.
import os, sys, tempfile
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d,'probeapp'))
open(os.path.join(d,'probeapp','__init__.py'),'w').close(); open(os.path.join(d,'probeapp','models.py'),'w').close()
sys.path.insert(0,d)
import django
from django.conf import settings
settings.configure(INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','probeapp'],
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}})
django.setup()
from django.db import models, connection
class Person(models.Model):
    name = models.CharField(max_length=100)
    class Meta: app_label='probeapp'
class Politician(models.Model):
    politician_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    class Meta: app_label='probeapp'
class Congressman(Person, Politician):
    state = models.CharField(max_length=2)
    class Meta: app_label='probeapp'

with connection.schema_editor() as se:
    for M in (Person, Politician, Congressman):
        se.create_model(M)

c1 = Congressman.objects.create(state="PA", name="John", title="senator 1")
c2 = Person.objects.get(pk=c1.pk).congressman
c2.pk = None
c2.id = None
c2.politician_ptr_id = None
c2.name = "Bill"; c2.title = "senator 2"
c2.save()

n = Congressman.objects.count()
person_john = Person.objects.get(pk=c1.pk).name
pol_title = Politician.objects.get(pk=c1.politician_ptr_id).title
print("Congressman.count=%d Person(orig).name=%r Politician(orig).title=%r" % (n, person_john, pol_title))
ok = (n == 2) and (person_john == "John") and (pol_title == "senator 1")
print("REQ3_OK" if ok else "REQ3_FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-12273: Model._set_pk_val must re-key the whole MTI inheritance chain. Gold patch loops self._meta.parents.values(); for each parent_link that is truthy and != self._meta.pk, setattr(target_field.attname, value), then sets own pk attname.

### PROBE SUITE (all HOLD on gold-patched tree; all runs completed):
- probe_1_propagate.py (Req1.1/1.2/1.3): Congressman().pk=5 => own person_ptr_id=5 AND ancestor politician_id=5. GOLD HOLDS, BASE VIOLATED (politician_id=None) — discriminator.
- probe_2_none_clears.py (Req1.4): pk=None clears own + politician_id. Holds gold & base (base already zeroes own; used for spec-fidelity of the clear path).
- probe_3_link_eq_pk.py (Req2.2/4.3): Restaurant with place_ptr parent_link==pk (target_field.attname='id'); pk=9 => place_ptr_id=9, id stays None (no double/misfire write). Holds.
- probe_4_unrelated_untouched.py (Req2.3): assigning pk leaves name/title/state unchanged. Holds.
- probe_5_read_and_plain.py (Req4.1/4.2): pk read returns own attr; non-MTI Plain model assign changes ONLY own pk attr, parents={}. Holds.
- probe_db.py (Req3.1/3.2/3.3, POSITIVE CONTROL): DB-backed replica of F2P multi_inheritance — create Congressman, fetch via Person, clear pk/id/politician_ptr_id, resave => count==2 and original Person.name='John', Politician.title='senator 1' preserved. GOLD HOLDS (exit0), BASE VIOLATED (integrity/overwrite error). prepatch_reproduced=true.

### CANDIDATE WRONG PATCHES (both REJECTED => suite discriminates wrong impls):
- weak_attname.diff: uses parent_link.attname instead of target_field.attname. REJECTED by probe_1 (politician_id stays None) and probe_db (F2P scenario errors). Confirms Req1.2's target_field.attname requirement is load-bearing.
- weak_noneonly.diff: propagates only when value is None. REJECTED by probe_1 (non-None assignment doesn't reach ancestor) — enforces Req1.2/1.3 apply for any assigned value, not just clearing.

Environment: py3.6 image (subprocess capture_output unavailable); probes use in-process settings.configure with a temp app package (container FS is read-only under /work except tempdir). No probe timed out; SOUND after 6 probes hold and positive control discriminates base vs gold, with >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified in the instance image (django 3.1, base 927c903f). Requirement 3's multi-level chain claim (Req3.3) is consistent with _meta.parents holding only the immediate parent link at each level: each MTI level's own setter propagates its immediate parent's target, so a re-key at each save() level covers the chain — matches the gold test test_create_new_instance_with_pk_equals_none_multi_inheritance. No requirement mandates behavior the patch lacks, forbids behavior it has, invents behavior, or mispins the boundary.

Counterexample / evidence:

```
Discriminating probe on multiple-inheritance model Child(Mother, Father): pk.attname='mother_ptr_id'; the qualifying non-pk parent link (Father) has target_field.attname='id'. Assigning c.pk=99 on the PATCHED tree sets c.mother_ptr_id==99 AND c.id==99 (qualifying target propagated), while c.father_ptr_id stays 5 (link.attname is NOT the boundary — target_field.attname is). On BASE the same assignment leaves c.id==5, so the probe fails at base (positive control discriminates). All 4 requirements' behaviors reproduce on the patched tree.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the gold fix (Model._set_pk_val propagating the assigned value to each self._meta.parents entry via target_field.attname, guarding against falsy links and links equal to self._meta.pk) into behavioral requirements. This is legitimate localization + behavioral translation, not a test/gold leak. None of the hidden-test specifics appear: no test file path (tests/model_inheritance_regress/tests.py), no test function names (test_create_new_instance_with_pk_equals_none / _multi_inheritance), no test class (ModelInheritanceTest), and none of the concrete test model/attribute identifiers (Profile, User, Congressman, Politician, Person, user_ptr_id, politician_ptr_id, username, state/title). Req 2's guard conditions (falsy link; link equal to pk) mirror the gold patch's logic but are the loci-of-change behavior, which is the explicitly-permitted kind of translation, and are prose not verbatim code. Req 3.3's 'more than two levels of inheritance' is a genuine behavioral property (the multi-inheritance scenario) rather than a test id. Req 4.4's mention of joins/select-related/parent-field filtering/parent updates reads as generic MTI regression preservation using standard Django ORM vocabulary, not a reconstruction of specific PASS_TO_PASS test ids. The problem_statement already covers pk=None copying via MTI; the document does not go beyond it in a test-reconstructing way.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
