# P2 adversarial audit — django__django-14725

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
"""
POSITIVE CONTROL — Req 2.2 / 2.3: saving an edit_only modelformset does NOT
create new objects even when extra forms are fully filled in and valid.
Must HOLD on patched tree, FAIL at base (base has no edit_only kwarg / no effect).
Exit 0 iff no new object is created and returned list == existing only.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

from django.forms.models import modelformset_factory

a1 = Author.objects.create(name='alice')

FormSet = modelformset_factory(Author, fields=('name',), edit_only=True, extra=1)

data = {
    'form-TOTAL_FORMS': '2',
    'form-INITIAL_FORMS': '1',
    'form-MAX_NUM_FORMS': '',
    'form-0-id': str(a1.pk),
    'form-0-name': 'alice-edited',
    'form-1-id': '',
    'form-1-name': 'bob-new',
}
fs = FormSet(data, queryset=Author.objects.all())
assert fs.is_valid(), fs.errors
saved = fs.save()

count = Author.objects.count()
names = sorted(Author.objects.values_list('name', flat=True))
print("saved objects:", [o.name for o in saved])
print("db count:", count, "names:", names)

ok = (count == 1) and ('bob-new' not in names) and (len(saved) == 1) and (saved[0].name == 'alice-edited')
print("edit persisted:", Author.objects.get(pk=a1.pk).name)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""
Req 1.2 + Req 2.4 (regression): default edit_only is False, and a NON-edit-only
formset still creates new objects from filled-in extra forms, returning existing
then new. Exit 0 iff default formset creates the new object.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True, DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)
from django.forms.models import modelformset_factory

a1 = Author.objects.create(name='alice')
FormSet = modelformset_factory(Author, fields=('name',), extra=1)  # no edit_only -> default
print("class edit_only default:", getattr(FormSet, 'edit_only', 'MISSING'))
data = {
    'form-TOTAL_FORMS': '2', 'form-INITIAL_FORMS': '1', 'form-MAX_NUM_FORMS': '',
    'form-0-id': str(a1.pk), 'form-0-name': 'alice-edited',
    'form-1-id': '', 'form-1-name': 'bob-new',
}
fs = FormSet(data, queryset=Author.objects.all())
assert fs.is_valid(), fs.errors
saved = fs.save()
names = sorted(Author.objects.values_list('name', flat=True))
print("saved:", [o.name for o in saved], "db:", names)
ok = (getattr(FormSet, 'edit_only', True) is False) and ('bob-new' in names) and (Author.objects.count() == 2) and (len(saved) == 2)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""
Req 1.3: the requested edit_only setting is recorded on the generated formset
CLASS, so every instance observes the same setting.
Exit 0 iff FormSet.edit_only is True and instances see it True.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True, DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)
from django.forms.models import modelformset_factory

FormSet = modelformset_factory(Author, fields=('name',), edit_only=True)
inst = FormSet(queryset=Author.objects.none())
print("class edit_only:", FormSet.edit_only, "instance edit_only:", inst.edit_only)
ok = (FormSet.edit_only is True) and (inst.edit_only is True)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""
Req 2.5: an edit_only formset with filled-in extra forms is still VALID
(edit-only changes what is saved, not whether valid data is accepted).
Exit 0 iff fs.is_valid() is True with a fully-filled extra form.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True, DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)
from django.forms.models import modelformset_factory

a1 = Author.objects.create(name='alice')
FormSet = modelformset_factory(Author, fields=('name',), edit_only=True, extra=1)
data = {
    'form-TOTAL_FORMS': '2', 'form-INITIAL_FORMS': '1', 'form-MAX_NUM_FORMS': '',
    'form-0-id': str(a1.pk), 'form-0-name': 'alice-edited',
    'form-1-id': '', 'form-1-name': 'bob-new',
}
fs = FormSet(data, queryset=Author.objects.all())
valid = fs.is_valid()
print("is_valid:", valid, "errors:", fs.errors)
sys.exit(0 if valid else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""
Req 3.1/3.2/3.3: an edit_only formset saved with a form carrying the pk of an
object NOT in the formset's queryset SHALL NOT create a new object, SHALL leave
that out-of-scope object unchanged, and SHALL leave all stored objects unchanged
except the in-scope edited ones.
Exit 0 iff out-of-scope object unchanged, no new rows, only in-scope edited.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True, DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)
from django.forms.models import modelformset_factory

alice = Author.objects.create(name='alice')       # in scope
carol = Author.objects.create(name='carol')       # OUT of scope
before_total = Author.objects.count()

# queryset excludes carol
qs = Author.objects.filter(pk=alice.pk)
FormSet = modelformset_factory(Author, fields=('name',), edit_only=True, extra=1)
data = {
    'form-TOTAL_FORMS': '2', 'form-INITIAL_FORMS': '1', 'form-MAX_NUM_FORMS': '',
    'form-0-id': str(alice.pk), 'form-0-name': 'alice-edited',
    # extra form references the OUT-OF-SCOPE pk with a changed name
    'form-1-id': str(carol.pk), 'form-1-name': 'carol-HACKED',
}
fs = FormSet(data, queryset=qs)
assert fs.is_valid(), fs.errors
fs.save()

carol_after = Author.objects.get(pk=carol.pk).name
alice_after = Author.objects.get(pk=alice.pk).name
after_total = Author.objects.count()
print("carol name after:", carol_after, "alice after:", alice_after, "total:", after_total)
ok = (carol_after == 'carol') and (alice_after == 'alice-edited') and (after_total == before_total)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""
Req 4.1/4.2/4.3: inlineformset_factory accepts edit_only (default False),
forwards it to the underlying model formset, and an edit_only inline formset
persists updates to existing children but does NOT create new children from
filled-in extra forms.
Exit 0 iff edit_only recorded on inline FormSet class AND no new child created.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True, DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()
from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)
    se.create_model(Book)
from django.forms.models import inlineformset_factory

# default False check
Default = inlineformset_factory(Author, Book, fields=('title',))
print("inline default edit_only:", getattr(Default, 'edit_only', 'MISSING'))

author = Author.objects.create(name='alice')
b1 = Book.objects.create(author=author, title='book1')

FormSet = inlineformset_factory(Author, Book, fields=('title',), edit_only=True, extra=1)
print("inline edit_only class:", getattr(FormSet, 'edit_only', 'MISSING'))
data = {
    'book_set-TOTAL_FORMS': '2', 'book_set-INITIAL_FORMS': '1', 'book_set-MAX_NUM_FORMS': '',
    'book_set-0-id': str(b1.pk), 'book_set-0-author': str(author.pk), 'book_set-0-title': 'book1-edited',
    'book_set-1-id': '', 'book_set-1-author': str(author.pk), 'book_set-1-title': 'newbook',
}
fs = FormSet(data, instance=author)
assert fs.is_valid(), fs.errors
saved = fs.save()
titles = sorted(Book.objects.values_list('title', flat=True))
print("saved:", [b.title for b in saved], "db titles:", titles)
ok = (getattr(Default, 'edit_only', True) is False) and (FormSet.edit_only is True) \
    and ('newbook' not in titles) and (Book.objects.count() == 1) \
    and (Book.objects.get(pk=b1.pk).title == 'book1-edited')
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""
POSITIVE CONTROL — Req 2.2 / 2.3: saving an edit_only modelformset does NOT
create new objects even when extra forms are fully filled in and valid.
Must HOLD on patched tree, FAIL at base (base has no edit_only kwarg / no effect).
Exit 0 iff no new object is created and returned list == existing only.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

from django.forms.models import modelformset_factory

a1 = Author.objects.create(name='alice')

FormSet = modelformset_factory(Author, fields=('name',), edit_only=True, extra=1)

data = {
    'form-TOTAL_FORMS': '2',
    'form-INITIAL_FORMS': '1',
    'form-MAX_NUM_FORMS': '',
    'form-0-id': str(a1.pk),
    'form-0-name': 'alice-edited',
    'form-1-id': '',
    'form-1-name': 'bob-new',
}
fs = FormSet(data, queryset=Author.objects.all())
assert fs.is_valid(), fs.errors
saved = fs.save()

count = Author.objects.count()
names = sorted(Author.objects.values_list('name', flat=True))
print("saved objects:", [o.name for o in saved])
print("db count:", count, "names:", names)

ok = (count == 1) and ('bob-new' not in names) and (len(saved) == 1) and (saved[0].name == 'alice-edited')
print("edit persisted:", Author.objects.get(pk=a1.pk).name)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-14725: edit_only formsets. 6 probes cover all requirements.

Probe results on GOLD-PATCHED tree (all HOLD):
- probe_1 (Req 2.2/2.3, POSITIVE CONTROL): edit_only modelformset save() creates NO new object from a filled-in extra form; returns only existing edited objects. HOLDS patched, FAILS at base (TypeError: unexpected kwarg 'edit_only') => discriminates.
- probe_2 (Req 1.2 + 2.4 regression): default edit_only is False; non-edit-only formset still creates new objects and returns existing+new. HOLDS.
- probe_3 (Req 1.3): edit_only recorded on the generated formset CLASS; instances observe it. HOLDS.
- probe_4 (Req 2.5): edit_only formset with filled extra form still reports is_valid()==True. HOLDS.
- probe_5 (Req 3.1/3.2/3.3): extra form carrying pk of out-of-scope object creates nothing, leaves that object unchanged, total row count unchanged. HOLDS.
- probe_6 (Req 4.1/4.2/4.3): inlineformset_factory accepts edit_only (default False), forwards it, and edit_only inline formset edits existing child but creates no new child. HOLDS.

CANDIDATE (wrong-fix) weak_return_only.diff: applies edit_only only to the RETURN list (still calls save_new_objects, so rows are actually created in DB but omitted from the return value). Probe suite REJECTS it: probe_1 (db count 1 expected but new row created => VIOLATED), probe_5 (out-of-scope carol row created, total=3 => VIOLATED), probe_6 (newbook child created => VIOLATED). probes 2/3/4 still HOLD. This demonstrates the suite discriminates a plausibly-wrong partial fix that would fail the hidden tests.

Conclusion: >=5 distinct probes all hold on the patched tree; positive control holds patched and fails at base (prepatch reproduced); >=1 wrong-fix candidate exercised and REJECTED. Requirements are faithful to the gold patch and strong enough to exclude the naive return-only fix. SOUND.

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
"""
POSITIVE CONTROL — Req 2.2 / 2.3: saving an edit_only modelformset does NOT
create new objects even when extra forms are fully filled in and valid.
Must HOLD on patched tree, FAIL at base (base has no edit_only kwarg / no effect).
Exit 0 iff no new object is created and returned list == existing only.
"""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=True,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
)
django.setup()

from django.db import models, connection

class Author(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(Author)

from django.forms.models import modelformset_factory

a1 = Author.objects.create(name='alice')

FormSet = modelformset_factory(Author, fields=('name',), edit_only=True, extra=1)

data = {
    'form-TOTAL_FORMS': '2',
    'form-INITIAL_FORMS': '1',
    'form-MAX_NUM_FORMS': '',
    'form-0-id': str(a1.pk),
    'form-0-name': 'alice-edited',
    'form-1-id': '',
    'form-1-name': 'bob-new',
}
fs = FormSet(data, queryset=Author.objects.all())
assert fs.is_valid(), fs.errors
saved = fs.save()

count = Author.objects.count()
names = sorted(Author.objects.values_list('name', flat=True))
print("saved objects:", [o.name for o in saved])
print("db count:", count, "names:", names)

ok = (count == 1) and ('bob-new' not in names) and (len(saved) == 1) and (saved[0].name == 'alice-edited')
print("edit persisted:", Author.objects.get(pk=a1.pk).name)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django-14725: edit_only formsets. 6 probes cover all requirements.

Probe results on GOLD-PATCHED tree (all HOLD):
- probe_1 (Req 2.2/2.3, POSITIVE CONTROL): edit_only modelformset save() creates NO new object from a filled-in extra form; returns only existing edited objects. HOLDS patched, FAILS at base (TypeError: unexpected kwarg 'edit_only') => discriminates.
- probe_2 (Req 1.2 + 2.4 regression): default edit_only is False; non-edit-only formset still creates new objects and returns existing+new. HOLDS.
- probe_3 (Req 1.3): edit_only recorded on the generated formset CLASS; instances observe it. HOLDS.
- probe_4 (Req 2.5): edit_only formset with filled extra form still reports is_valid()==True. HOLDS.
- probe_5 (Req 3.1/3.2/3.3): extra form carrying pk of out-of-scope object creates nothing, leaves that object unchanged, total row count unchanged. HOLDS.
- probe_6 (Req 4.1/4.2/4.3): inlineformset_factory accepts edit_only (default False), forwards it, and edit_only inline formset edits existing child but creates no new child. HOLDS.

CANDIDATE (wrong-fix) weak_return_only.diff: applies edit_only only to the RETURN list (still calls save_new_objects, so rows are actually created in DB but omitted from the return value). Probe suite REJECTS it: probe_1 (db count 1 expected but new row created => VIOLATED), probe_5 (out-of-scope carol row created, total=3 => VIOLATED), probe_6 (newbook child created => VIOLATED). probes 2/3/4 still HOLD. This demonstrates the suite discriminates a plausibly-wrong partial fix that would fail the hidden tests.

Conclusion: >=5 distinct probes all hold on the patched tree; positive control holds patched and fails at base (prepatch reproduced); >=1 wrong-fix candidate exercised and REJECTED. Requirements are faithful to the gold patch and strong enough to exclude the naive return-only fix. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a minimal, faithful implementation: save() branches on self.edit_only to skip save_new_objects, both factories gain edit_only=False param, modelformset_factory sets FormSet.edit_only, inlineformset_factory forwards it via kwargs. Requirements' modeling boundary matches the changed observable behavior (save no longer creating new objects) rather than a narrow slice. Probed live in the instance image (gold-patched HOLDS exit=0). Requirement prose correctly notes extra forms are still accepted/valid (R2.5) and only creation is suppressed — matches code (validation path untouched).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the edit_only formset feature behaviorally without transmitting hidden-test/gold content. The `edit_only` keyword is the NEW PUBLIC API parameter being added (added to modelformset_factory/inlineformset_factory signatures) — specifying a public parameter's name is the legitimate deliverable spec a consumer needs, not a fix-internal invented identifier. Named modules/functions (BaseModelFormSet.save, save_existing_objects, the two factories, django/forms/models.py) are legitimate localization. No test names (test_edit_only*), no test file path, no parametrization ids, no fixture data ('Charles Baudelaire', 'Arthur Rimbaud', 'Les Fleurs du Mal', 'Parth Patil'), no form-TOTAL_FORMS/INITIAL_FORMS POST mechanics, and no verbatim gold-patch lines (the `if self.edit_only:` branch). The three requirement scenarios (save skips creation, out-of-queryset untouched, inline parity) loosely correspond to the three F2P tests but are phrased as behavioral guarantees rather than mirroring test structure/data; the out-of-scope-pk case is genuine behavior described in prose. Translation of test-checked behavior into requirements is the intended purpose, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
