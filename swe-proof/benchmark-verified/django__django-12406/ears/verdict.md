# P2 adversarial audit — django__django-12406

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
"""Req1.2 + Req1.5: RadioSelect (class) + blank NOT permitted -> no empty choice; empty_label is None."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
    )
sys.path.insert(0, '/tmp')

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author
with connection.schema_editor() as se:
    se.create_model(Author)
Author.objects.create(name="Alice")
Author.objects.create(name="Bob")

from django.forms.models import ModelChoiceField
from django.forms import RadioSelect

f = ModelChoiceField(Author.objects.all().order_by('pk'), widget=RadioSelect, blank=False)
print("empty_label:", repr(f.empty_label))
choices = list(f.choices)
print("choices:", choices)
has_empty = len(choices) > 0 and choices[0][0] == ''
labels = [c[1] for c in choices]
print("has_empty_choice:", has_empty, "labels:", labels)
ok = (f.empty_label is None) and (not has_empty) and labels == ["Alice", "Bob"]
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3: RadioSelect + blank PERMITTED -> empty choice is first, then queryset entries."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
        "class BookReq(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE)\n"
        "    class Meta: app_label='probeapp'\n"
        "class BookBlank(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)\n"
        "    class Meta: app_label='probeapp'\n"
    )
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author, BookReq, BookBlank
with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(BookReq); se.create_model(BookBlank)
Author.objects.create(name="Alice"); Author.objects.create(name="Bob")
from django.forms.models import ModelChoiceField
from django.forms import RadioSelect
f = ModelChoiceField(Author.objects.all().order_by('pk'), widget=RadioSelect, blank=True)
choices = list(f.choices)
print("empty_label:", repr(f.empty_label))
labels = [c[1] for c in choices]
print("labels:", labels)
ok = choices[0][0] == '' and choices[0][1] == '---------' and labels[1:] == ["Alice","Bob"]
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.4: radio widget recognized as class OR instance -> identical output (blank=False -> no empty)."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
        "class BookReq(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE)\n"
        "    class Meta: app_label='probeapp'\n"
        "class BookBlank(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)\n"
        "    class Meta: app_label='probeapp'\n"
    )
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author, BookReq, BookBlank
with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(BookReq); se.create_model(BookBlank)
Author.objects.create(name="Alice"); Author.objects.create(name="Bob")
from django.forms.models import ModelChoiceField
from django.forms import RadioSelect
f_cls = ModelChoiceField(Author.objects.all().order_by('pk'), widget=RadioSelect, blank=False)
f_inst = ModelChoiceField(Author.objects.all().order_by('pk'), widget=RadioSelect(), blank=False)
c_cls = [(str(v),l) for v,l in f_cls.choices]
c_inst = [(str(v),l) for v,l in f_inst.choices]
print("class:", c_cls)
print("inst :", c_inst)
print("empty_labels:", f_cls.empty_label, f_inst.empty_label)
ok = (c_cls == c_inst) and (f_cls.empty_label is None) and (f_inst.empty_label is None) and (c_cls[0][1] != '---------')
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.2/2.3/2.4: ForeignKey.formfield propagates model blank -> radio field choices.
BookReq FK (blank=False) -> no empty choice; BookBlank FK (blank=True) -> empty choice first.
Labels use str(obj), values use pk."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
        "class BookReq(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE)\n"
        "    class Meta: app_label='probeapp'\n"
        "class BookBlank(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)\n"
        "    class Meta: app_label='probeapp'\n"
    )
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author, BookReq, BookBlank
with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(BookReq); se.create_model(BookBlank)
Author.objects.create(name="Alice"); Author.objects.create(name="Bob")
from django.forms import RadioSelect
fk_req = BookReq._meta.get_field('author')
fk_blank = BookBlank._meta.get_field('author')
ff_req = fk_req.formfield(widget=RadioSelect)
ff_blank = fk_blank.formfield(widget=RadioSelect)
cr = list(ff_req.choices)
cb = list(ff_blank.choices)
print("req choices:", [(str(v),l) for v,l in cr])
print("blank choices:", [(str(v),l) for v,l in cb])
alice = Author.objects.get(name="Alice")
req_no_empty = cr[0][0] != ''
blank_has_empty = cb[0][0] == '' and cb[0][1] == '---------'
# value uses pk, label uses str
val_label_ok = int(str(cr[0][0])) == alice.pk and cr[0][1] == "Alice"
print("req_no_empty:", req_no_empty, "blank_has_empty:", blank_has_empty, "val_label_ok:", val_label_ok)
ok = req_no_empty and blank_has_empty and val_label_ok
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1: default (non-radio Select) widget ALWAYS includes empty choice first, regardless of blank."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
        "class BookReq(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE)\n"
        "    class Meta: app_label='probeapp'\n"
        "class BookBlank(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)\n"
        "    class Meta: app_label='probeapp'\n"
    )
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author, BookReq, BookBlank
with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(BookReq); se.create_model(BookBlank)
Author.objects.create(name="Alice"); Author.objects.create(name="Bob")
from django.forms.models import ModelChoiceField
f_bf = ModelChoiceField(Author.objects.all().order_by('pk'), blank=False)   # default widget
f_bt = ModelChoiceField(Author.objects.all().order_by('pk'), blank=True)
c_bf = list(f_bf.choices); c_bt = list(f_bt.choices)
print("blank=False choices[0]:", (str(c_bf[0][0]), c_bf[0][1]))
print("blank=True  choices[0]:", (str(c_bt[0][0]), c_bt[0][1]))
ok = c_bf[0][0]=='' and c_bf[0][1]=='---------' and c_bt[0][0]=='' and c_bt[0][1]=='---------'
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.2: required + non-None initial -> empty_label None and no empty choice, regardless of widget/blank."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
        "class BookReq(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE)\n"
        "    class Meta: app_label='probeapp'\n"
        "class BookBlank(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)\n"
        "    class Meta: app_label='probeapp'\n"
    )
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author, BookReq, BookBlank
with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(BookReq); se.create_model(BookBlank)
Author.objects.create(name="Alice"); Author.objects.create(name="Bob")
from django.forms.models import ModelChoiceField
from django.forms import RadioSelect
alice = Author.objects.get(name="Alice")
# even with a Select widget and blank=True, required+initial suppresses empty
f = ModelChoiceField(Author.objects.all().order_by('pk'), required=True, initial=alice.pk, blank=True)
choices = list(f.choices)
print("empty_label:", repr(f.empty_label), "choices0:", (str(choices[0][0]), choices[0][1]))
ok = f.empty_label is None and choices[0][0] != ''
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req4.1/4.2/4.3: clean behavior preserved.
- instance in queryset -> returned
- wrong-model instance -> ValidationError with expected message
- empty value -> None"""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
        "class BookReq(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE)\n"
        "    class Meta: app_label='probeapp'\n"
        "class BookBlank(models.Model):\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE, blank=True, null=True)\n"
        "    class Meta: app_label='probeapp'\n"
    )
sys.path.insert(0, '/tmp')
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author, BookReq, BookBlank
with connection.schema_editor() as se:
    se.create_model(Author); se.create_model(BookReq); se.create_model(BookBlank)
Author.objects.create(name="Alice"); Author.objects.create(name="Bob")
from django.forms.models import ModelChoiceField
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
alice = Author.objects.get(name="Alice")
f = ModelChoiceField(Author.objects.all(), required=False)
# 1. instance in queryset
r = f.clean(alice.pk)
print("clean(pk) ->", r)
same = (r == alice)
# 3. empty -> None
none_ok = f.clean('') is None
# 2. wrong model / not in queryset -> ValidationError
msg_ok = False
try:
    f.clean(999999)  # nonexistent pk
except ValidationError as e:
    msg = e.messages[0]
    print("err:", msg)
    msg_ok = msg == "Select a valid choice. That choice is not one of the available choices."
print("same:", same, "none_ok:", none_ok, "msg_ok:", msg_ok)
ok = same and none_ok and msg_ok
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.2 + Req1.5: RadioSelect (class) + blank NOT permitted -> no empty choice; empty_label is None."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
    )
sys.path.insert(0, '/tmp')

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author
with connection.schema_editor() as se:
    se.create_model(Author)
Author.objects.create(name="Alice")
Author.objects.create(name="Bob")

from django.forms.models import ModelChoiceField
from django.forms import RadioSelect

f = ModelChoiceField(Author.objects.all().order_by('pk'), widget=RadioSelect, blank=False)
print("empty_label:", repr(f.empty_label))
choices = list(f.choices)
print("choices:", choices)
has_empty = len(choices) > 0 and choices[0][0] == ''
labels = [c[1] for c in choices]
print("has_empty_choice:", has_empty, "labels:", labels)
ok = (f.empty_label is None) and (not has_empty) and labels == ["Alice", "Bob"]
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 standalone probes, all HOLD on gold-patched tree; all built with an on-disk 'probeapp' package (in-memory sqlite) so they run self-contained in the instance image.

Probe->criterion mapping:
- probe_1 (Req1.2/1.5, POSITIVE CONTROL): RadioSelect class + blank=False -> empty_label is None AND choices == ['Alice','Bob'] (no empty choice). HOLDS patched; FAILS at base (TypeError: __init__() got unexpected kwarg 'blank') -> prepatch reproduced, discriminating power confirmed.
- probe_2 (Req1.3): RadioSelect + blank=True -> empty choice ('', '---------') first, then queryset entries. HOLDS.
- probe_3 (Req1.4): RadioSelect passed as class vs instance produce identical output with blank=False (both suppress empty). HOLDS.
- probe_4 (Req2.2/2.3/2.4): ForeignKey.formfield propagates model blank: BookReq FK(blank=False)->no empty; BookBlank FK(blank=True,null)->empty first; value uses pk, label uses str(obj). HOLDS.
- probe_5 (Req3.1): default (non-radio Select) widget always includes empty choice first regardless of blank. HOLDS.
- probe_6 (Req3.2): required + non-None initial -> empty_label None and no empty choice even with Select+blank=True. HOLDS.
- probe_7 (Req4.1/4.2/4.3): clean() preserved: instance in qs returned; nonexistent pk raises ValidationError 'Select a valid choice. That choice is not one of the available choices.'; empty value -> None. HOLDS.

CANDIDATE PATCH (weak.diff): adds 'blank' kwarg to ModelChoiceField.__init__ and passes self.blank from FK.formfield (satisfies Req1.1 and Req2.1 arg-plumbing) but keeps the ORIGINAL empty_label logic (no RadioSelect+not-blank suppression). This is the naive/partial fix a weak reading permits. Suite REJECTS it: probe_1 FAIL (empty_label not None, empty choice present), probe_3 FAIL (choices include ('', '---------')), probe_4 FAIL (BookReq radio field still has empty choice). Probes 2,5,6,7 correctly still HOLD. => suite discriminates the wrong implementation.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates (holds patched / fails base), and >=1 requirements-plausible alternative patch is exercised and REJECTED.

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
"""Req1.2 + Req1.5: RadioSelect (class) + blank NOT permitted -> no empty choice; empty_label is None."""
import sys, os
os.makedirs('$SCRATCH', exist_ok=True)
open('$SCRATCH/__init__.py', 'w').close()
with open('$SCRATCH/models.py', 'w') as fh:
    fh.write(
        "from django.db import models\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=50)\n"
        "    class Meta: app_label='probeapp'\n"
        "    def __str__(self): return self.name\n"
    )
sys.path.insert(0, '/tmp')

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=True,
    )
django.setup()
from django.db import connection
from probeapp.models import Author
with connection.schema_editor() as se:
    se.create_model(Author)
Author.objects.create(name="Alice")
Author.objects.create(name="Bob")

from django.forms.models import ModelChoiceField
from django.forms import RadioSelect

f = ModelChoiceField(Author.objects.all().order_by('pk'), widget=RadioSelect, blank=False)
print("empty_label:", repr(f.empty_label))
choices = list(f.choices)
print("choices:", choices)
has_empty = len(choices) > 0 and choices[0][0] == ''
labels = [c[1] for c in choices]
print("has_empty_choice:", has_empty, "labels:", labels)
ok = (f.empty_label is None) and (not has_empty) and labels == ["Alice", "Bob"]
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 standalone probes, all HOLD on gold-patched tree; all built with an on-disk 'probeapp' package (in-memory sqlite) so they run self-contained in the instance image.

Probe->criterion mapping:
- probe_1 (Req1.2/1.5, POSITIVE CONTROL): RadioSelect class + blank=False -> empty_label is None AND choices == ['Alice','Bob'] (no empty choice). HOLDS patched; FAILS at base (TypeError: __init__() got unexpected kwarg 'blank') -> prepatch reproduced, discriminating power confirmed.
- probe_2 (Req1.3): RadioSelect + blank=True -> empty choice ('', '---------') first, then queryset entries. HOLDS.
- probe_3 (Req1.4): RadioSelect passed as class vs instance produce identical output with blank=False (both suppress empty). HOLDS.
- probe_4 (Req2.2/2.3/2.4): ForeignKey.formfield propagates model blank: BookReq FK(blank=False)->no empty; BookBlank FK(blank=True,null)->empty first; value uses pk, label uses str(obj). HOLDS.
- probe_5 (Req3.1): default (non-radio Select) widget always includes empty choice first regardless of blank. HOLDS.
- probe_6 (Req3.2): required + non-None initial -> empty_label None and no empty choice even with Select+blank=True. HOLDS.
- probe_7 (Req4.1/4.2/4.3): clean() preserved: instance in qs returned; nonexistent pk raises ValidationError 'Select a valid choice. That choice is not one of the available choices.'; empty value -> None. HOLDS.

CANDIDATE PATCH (weak.diff): adds 'blank' kwarg to ModelChoiceField.__init__ and passes self.blank from FK.formfield (satisfies Req1.1 and Req2.1 arg-plumbing) but keeps the ORIGINAL empty_label logic (no RadioSelect+not-blank suppression). This is the naive/partial fix a weak reading permits. Suite REJECTS it: probe_1 FAIL (empty_label not None, empty choice present), probe_3 FAIL (choices include ('', '---------')), probe_4 FAIL (BookReq radio field still has empty choice). Probes 2,5,6,7 correctly still HOLD. => suite discriminates the wrong implementation.

Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates (holds patched / fails base), and >=1 requirements-plausible alternative patch is exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** R4.1 is phrased 'return that same instance'; the patched code path (unchanged by this patch) re-fetches by pk so it returns a distinct-identity but pk-equal instance. This is pre-existing behavior unaffected by the patch and the requirement's intent (round-trips the in-queryset instance without error) holds. R3.5 (empty-queryset truthiness) not separately probed but is unchanged legacy ModelChoiceIterator behavior outside the patch's scope. No divergence between requirements and patched behavior found.

Counterexample / evidence:

```
None — probe.py exercising all 4 requirements exits 0 (HOLDS) on the patched tree; base tree lacks the `blank` kwarg entirely (TypeError), confirming the change is real and the requirements track it.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change by naming the involved public API (ModelChoiceField, ModelChoiceIterator, ForeignKey.formfield, RadioSelect, empty_label, blank) — all legitimate and, moreover, already present in the public problem_statement (which shows `blank=False on the model`, `widgets = {'data_file': RadioSelect()}`, and the rendered `---------` empty option). No hidden-test artifacts are transmitted: no test file paths, test/class names (test_choices_radio_blank, test_blank/non_blank_foreign_key_with_radio, test_clean_model_instance), parametrization ids, or verbatim gold-patch lines appear. Req 1 crit 4 ('widget as class or instance, identical output') parallels the test's `for widget in [forms.RadioSelect, forms.RadioSelect()]`, but it states a genuine behavioral robustness property rather than transmitting test code, and follows from Field.__init__ instantiating the widget. Req 4 crit 2 quotes the standard 'Select a valid choice...' validation message, which is public Django API behavior, not a test-invented identifier. The blank-kwarg default ('blank not permitted') and the empty_label=None outcome describe observable behavior the gold produces, not the gold source itself. Document translates test-checked behavior into behavioral requirements — the intended function — rather than reconstructing the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
