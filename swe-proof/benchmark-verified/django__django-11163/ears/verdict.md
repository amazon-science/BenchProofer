# P2 adversarial audit — django__django-11163

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

Counterexample / evidence:

```
weak.diff (`if fields is not None and len(fields) > 0 and f.name not in fields`) is a requirements-plausible partial fix that re-introduces the exact defect: it still tests the selection for non-emptiness, so an empty fields=[] imposes no constraint and returns all fields instead of {}. probe_1 REJECTS it (observed {'id':None,'name':'Joe','age':30} instead of {}), demonstrating the suite discriminates against the wrong fix. It would fail the hidden F2P test (assertEqual(model_to_dict(bw, fields=[]), {})).
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Requirement 2.1 / 2.3 + core fix (positive control):
model_to_dict(instance, fields=[]) SHALL return an empty mapping.
On base it returns all fields (defect); on patched it returns {}.
Exit 0 iff result == {}."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
import sys, types
django.setup()

from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    class Meta:
        app_label = "auth"

from django.forms.models import model_to_dict
p = Person(name="Joe", age=30)
result = model_to_dict(p, fields=[])
print("model_to_dict(p, fields=[]) =", result)
if result == {}:
    print("HOLDS: empty fields -> empty dict")
    sys.exit(0)
print("FAIL: expected {} got", result)
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.1/1.2 (SHALL keep): absent/None fields imposes no constraint;
every editable, non-excluded field returned. Non-editable 'slug' must NOT appear.
Exit 0 iff both model_to_dict(p) and model_to_dict(p, fields=None) == {'id','name','age'}."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
import sys, types
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    slug = models.CharField(max_length=20, editable=False, default="x")
    class Meta: app_label = "auth"
from django.forms.models import model_to_dict
p = Person(name="Joe", age=30)
r_none = set(model_to_dict(p))
r_omit = set(model_to_dict(p, fields=None))
expected = {"id", "name", "age"}
print("fields omitted ->", r_omit)
print("fields=None    ->", r_none)
if r_none == expected and r_omit == expected:
    print("HOLDS: absent selection -> all editable fields, slug excluded")
    sys.exit(0)
print("FAIL: expected", expected)
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 3.1/3.3: non-empty fields restricts to named editable fields;
a name not corresponding to an editable field is omitted (slug -> not editable,
'bogus' -> nonexistent). Exit 0 iff model_to_dict(p, fields=['name','bogus','slug'])
== {'name': 'Joe'}."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
import sys, types
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    slug = models.CharField(max_length=20, editable=False, default="x")
    class Meta: app_label = "auth"
from django.forms.models import model_to_dict
p = Person(name="Joe", age=30)
r = model_to_dict(p, fields=["name", "bogus", "slug"])
print("result =", r)
if r == {"name": "Joe"}:
    print("HOLDS: only named editable field returned; bogus/non-editable omitted")
    sys.exit(0)
print("FAIL: expected {'name':'Joe'}")
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 3.2 (SHALL keep): model-declared order preserved; NOT reordered
to match the inclusion selection order. Fields declared name,age; requesting
['age','name'] must yield keys in declared order name,age.
Exit 0 iff list(model_to_dict(p, fields=['age','name']).keys()) == ['name','age']."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
import sys, types
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    class Meta: app_label = "auth"
from django.forms.models import model_to_dict
p = Person(name="Joe", age=30)
keys = list(model_to_dict(p, fields=["age", "name"]).keys())
print("keys =", keys)
if keys == ["name", "age"]:
    print("HOLDS: declared order preserved, not reordered to selection")
    sys.exit(0)
print("FAIL: expected ['name','age']")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 4.1/4.2/4.3 (SHALL keep): exclude drops named field even if in
fields; exclude=[] identical to exclude absent; exclude wins over fields.
Checks:
 (a) exclude=['name'] with fields=['name','age'] -> {'age'}
 (b) exclude=[] -> same as absent -> {'id','name','age'}
Exit 0 iff both hold."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
import sys, types
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    class Meta: app_label = "auth"
from django.forms.models import model_to_dict
p = Person(name="Joe", age=30)
a = set(model_to_dict(p, fields=["name", "age"], exclude=["name"]))
b = set(model_to_dict(p, exclude=[]))
absent = set(model_to_dict(p))
print("fields=[name,age] exclude=[name] ->", a)
print("exclude=[] ->", b, " absent ->", absent)
ok = (a == {"age"}) and (b == absent == {"id", "name", "age"})
if ok:
    print("HOLDS: exclude semantics unchanged")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 5.2 (SHALL keep): retained field paired with the value extracted
from the instance. Set values and verify value_from_object semantics.
Exit 0 iff model_to_dict(p, fields=['name','age']) == {'name':'Alice','age':42}."""
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
import sys, types
django.setup()
from django.db import models
class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    class Meta: app_label = "auth"
from django.forms.models import model_to_dict
p = Person(name="Alice", age=42)
r = model_to_dict(p, fields=["name", "age"])
print("result =", r)
if r == {"name": "Alice", "age": 42}:
    print("HOLDS: correct name/value pairing")
    sys.exit(0)
print("FAIL")
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Requirement 2.1 / 2.3 + core fix (positive control):
model_to_dict(instance, fields=[]) SHALL return an empty mapping.
On base it returns all fields (defect); on patched it returns {}.
Exit 0 iff result == {}."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
import sys, types
django.setup()

from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    class Meta:
        app_label = "auth"

from django.forms.models import model_to_dict
p = Person(name="Joe", age=30)
result = model_to_dict(p, fields=[])
print("model_to_dict(p, fields=[]) =", result)
if result == {}:
    print("HOLDS: empty fields -> empty dict")
    sys.exit(0)
print("FAIL: expected {} got", result)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix = single line `if fields and f.name not in fields` -> `if fields is not None and f.name not in fields`. 6 probes cover all 5 requirements: probe_1 (R2.1/2.3, positive control: fields=[] -> {}); probe_2 (R1.1/1.2 SHALL-keep: absent/None -> all editable, non-editable slug excluded); probe_3 (R3.1/3.3: non-empty selection restricts to named editable fields, bogus & non-editable omitted); probe_4 (R3.2 SHALL-keep: declared order preserved, not reordered to selection); probe_5 (R4.1/4.2/4.3 SHALL-keep: exclude drops even if in fields, exclude=[] == absent); probe_6 (R5.2 SHALL-keep: correct name/value pairing). RESULTS: positive control probe_1 HOLDS patched, FAILS at base (returns all fields — defect reproduced), and is REJECTED under weak.diff. probes 2-6 HOLD on patched tree. Under weak.diff, probes 2-6 all HOLD but probe_1 fails => the candidate is NOT too-weak (probe suite catches it). No requirements-conforming alternative found that resolves differently; the single boundary (empty vs absent) is fully pinned by R2.2/2.3 and exercised by probe_1. Probes run in official docker image via nl_attack; app_label 'auth' reused for a real filesystem-backed app config.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak.diff (`if fields is not None and len(fields) > 0 and f.name not in fields`) is a requirements-plausible partial fix that re-introduces the exact defect: it still tests the selection for non-emptiness, so an empty fields=[] imposes no constraint and returns all fields instead of {}. probe_1 REJECTS it (observed {'id':None,'name':'Joe','age':30} instead of {}), demonstrating the suite discriminates against the wrong fix. It would fail the hidden F2P test (assertEqual(model_to_dict(bw, fields=[]), {})).
```

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
"""Requirement 2.1 / 2.3 + core fix (positive control):
model_to_dict(instance, fields=[]) SHALL return an empty mapping.
On base it returns all fields (defect); on patched it returns {}.
Exit 0 iff result == {}."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
import sys, types
django.setup()

from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=50)
    age = models.IntegerField(default=0)
    class Meta:
        app_label = "auth"

from django.forms.models import model_to_dict
p = Person(name="Joe", age=30)
result = model_to_dict(p, fields=[])
print("model_to_dict(p, fields=[]) =", result)
if result == {}:
    print("HOLDS: empty fields -> empty dict")
    sys.exit(0)
print("FAIL: expected {} got", result)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix = single line `if fields and f.name not in fields` -> `if fields is not None and f.name not in fields`. 6 probes cover all 5 requirements: probe_1 (R2.1/2.3, positive control: fields=[] -> {}); probe_2 (R1.1/1.2 SHALL-keep: absent/None -> all editable, non-editable slug excluded); probe_3 (R3.1/3.3: non-empty selection restricts to named editable fields, bogus & non-editable omitted); probe_4 (R3.2 SHALL-keep: declared order preserved, not reordered to selection); probe_5 (R4.1/4.2/4.3 SHALL-keep: exclude drops even if in fields, exclude=[] == absent); probe_6 (R5.2 SHALL-keep: correct name/value pairing). RESULTS: positive control probe_1 HOLDS patched, FAILS at base (returns all fields — defect reproduced), and is REJECTED under weak.diff. probes 2-6 HOLD on patched tree. Under weak.diff, probes 2-6 all HOLD but probe_1 fails => the candidate is NOT too-weak (probe suite catches it). No requirements-conforming alternative found that resolves differently; the single boundary (empty vs absent) is fully pinned by R2.2/2.3 and exercised by probe_1. Probes run in official docker image via nl_attack; app_label 'auth' reused for a real filesystem-backed app config.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-line change 'if fields' -> 'if fields is not None'. Probe on gold-patched tree: HOLDS (exit 0). Probe on base: VIOLATED on the empty-fields assertion (returned all fields). Requirements 1,3,4,5 describe unchanged surrounding behavior accurately and are consistent with observed patched behavior. No mandated behavior the code lacks, no forbidden behavior it has, correct modeling boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes model_to_dict field-selection semantics purely behaviorally. No hidden-test artifacts appear: no test function names (test_modelform_subclassed_model), no test path (tests/model_forms/tests.py), no model class (BetterWriter), no field-name literals ('id','name','score','writer_ptr'), no assertEqual(sorted(...)) shapes. The core fix ('fields is not None' vs 'fields and') is quoted verbatim in the PUBLIC problem_statement, so mentioning the absent-vs-empty distinction is public. Req 4's exclude=[]==absent equivalence maps a test assertion but is stated as behavior derivable from the function's public contract/docstring, not from test literals. Enumerations (absent / empty / non-empty fields; empty/non-empty exclude) mirror the argument space, not the specific parametrized values. Localizing to model_to_dict and its args is legitimate spec description. No leakage beyond problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
