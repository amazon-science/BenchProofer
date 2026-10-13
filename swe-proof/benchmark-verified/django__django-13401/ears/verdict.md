# P2 adversarial audit — django__django-13401

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
"""Positive control: Req1.2 + Req2.4.
Fields inherited from an abstract base by two different concrete models
share creation_counter but are attached to different models -> must be
UNEQUAL and coexist as 2 distinct elements in a set.
HOLDS on patched, FAILS at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class AbstractBase(models.Model):
    myfield = models.IntegerField()
    class Meta:
        app_label = 'myapp'
        abstract = True

class ModelA(AbstractBase):
    class Meta:
        app_label = 'myapp'

class ModelB(AbstractBase):
    class Meta:
        app_label = 'myapp'

fa = ModelA._meta.get_field('myfield')
fb = ModelB._meta.get_field('myfield')
print('creation_counters:', fa.creation_counter, fb.creation_counter)
print('fa==fb:', fa == fb)
s = {fa, fb}
print('len(set):', len(s))
assert fa.creation_counter == fb.creation_counter, "precondition: same counter"
assert fa != fb, "Req1.2: different models -> unequal"
assert len(s) == 2, "Req2.4: both coexist in set"
print("PASS")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3 + Req1.4 + Req4.4: same model -> equal; two unattached with same
counter -> equal; self compares equal & stable hash."""
import django, copy
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models

class ModelA(models.Model):
    myfield = models.IntegerField()
    class Meta:
        app_label = 'myapp'

fa = ModelA._meta.get_field('myfield')
fa2 = ModelA._meta.get_field('myfield')  # same descriptor object
print('same model, fa==fa2:', fa == fa2)
assert fa == fa2, "Req1.3: same model+counter -> equal"

# self equality + stable hash (Req4.4)
assert fa == fa, "self equal"
assert hash(fa) == hash(fa), "stable hash"

# two unattached fields with the SAME counter -> equal (Req1.4)
u1 = models.IntegerField()
u2 = models.IntegerField()
u2.creation_counter = u1.creation_counter
print('unattached u1==u2 (same counter):', u1 == u2)
assert u1 == u2, "Req1.4: two unattached same-counter -> equal"
print("PASS")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.5 + Req3.5 + Req1.6: comparison with non-Field returns NotImplemented
(so == falls to identity -> False, and != -> True); accessing model on an
unattached field must not raise."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models

f = models.IntegerField()  # unattached
# Req1.6 / Req2.2: hashing an unattached field must not raise
h = hash(f)
print('hash unattached ok:', h)

# Req1.5: __eq__ with non-Field returns NotImplemented -> Python identity fallback
print('f == 42:', f == 42)
print('f == "x":', f == "x")
assert (f == 42) is False, "Req1.5: eq non-field -> False via NotImplemented"
assert (f != 42) is True, "Req1.5: ne non-field -> True"
assert f.__eq__(42) is NotImplemented, "Req1.5: __eq__ returns NotImplemented"

# Req3.5: __lt__ with non-Field returns NotImplemented
assert f.__lt__(42) is NotImplemented, "Req3.5: __lt__ returns NotImplemented"
try:
    f < 42
    raised = False
except TypeError:
    raised = True
print('f < 42 raised TypeError:', raised)
assert raised, "Req3.5: ordering vs non-field -> TypeError (NotImplemented both ways)"
print("PASS")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1 + Req3.3 + Req3.4 + Req3.6: ordering rules.
- different counter -> smaller counter first regardless of model
- same counter, one unattached -> unattached first
- same counter, both attached -> lexicographic by (app_label, model_name)
- equal fields -> neither < the other"""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models

class AbstractBase(models.Model):
    myfield = models.IntegerField()
    class Meta:
        app_label = 'myapp'
        abstract = True

# app 'aaa' model 'modela'  vs  app 'zzz' model 'modelz'
class ModelA(AbstractBase):
    class Meta:
        app_label = 'aaa'
class ModelZ(AbstractBase):
    class Meta:
        app_label = 'zzz'

fa = ModelA._meta.get_field('myfield')
fz = ModelZ._meta.get_field('myfield')
print('counters equal:', fa.creation_counter == fz.creation_counter)

# Req3.4: same counter, both attached -> lexicographic (aaa < zzz)
assert fa < fz, "Req3.4: (aaa,...) < (zzz,...)"
assert not (fz < fa), "Req3.4 asym"

# Req3.3: same counter, one unattached -> unattached first
u = models.IntegerField()
u.creation_counter = fa.creation_counter
print('u<fa:', u < fa, ' fa<u:', fa < u)
assert u < fa, "Req3.3: unattached ordered first"
assert not (fa < u), "Req3.3 asym"

# Req3.1: different counter -> smaller counter first regardless of model.
# fa has smaller counter than a later-declared field; make a field with a
# LARGER counter but 'aaa' app so model wouldn't help.
later = models.IntegerField()  # larger creation_counter than fa
print('fa.counter', fa.creation_counter, 'later.counter', later.creation_counter)
assert fa.creation_counter < later.creation_counter
assert fa < later, "Req3.1: smaller counter first"
# and reverse: a field with smaller counter always first even if attached model 'zzz'
assert not (later < fa)

# Req3.6: equal -> neither strictly before/after
fa_same = ModelA._meta.get_field('myfield')
assert not (fa < fa_same) and not (fa_same < fa), "Req3.6: equal -> incomparable order"
print("PASS")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.1/2.3 + Req4.1/4.2/4.3: hash consistent with equality; hash derived
from (counter, app_label, model_name); monotonic counters; sorting by distinct
counters == sorting by counter alone; total ordering usable."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models

# Req4.1: monotonically increasing distinct counters
f1 = models.IntegerField()
f2 = models.IntegerField()
f3 = models.CharField(max_length=1)
print('counters:', f1.creation_counter, f2.creation_counter, f3.creation_counter)
assert f1.creation_counter < f2.creation_counter < f3.creation_counter, "Req4.1"

# Req4.2: sort of distinct-counter fields == sort by counter alone
import random
flds = [f1, f2, f3]
shuffled = flds[::-1]
by_sort = sorted(shuffled)
by_counter = sorted(shuffled, key=lambda f: f.creation_counter)
print('sort matches counter-sort:', by_sort == by_counter)
assert by_sort == by_counter, "Req4.2"

# Req2.3: equal fields -> equal hash
class ModelA(models.Model):
    myfield = models.IntegerField()
    class Meta:
        app_label = 'myapp'
fa = ModelA._meta.get_field('myfield')
fa2 = ModelA._meta.get_field('myfield')
assert fa == fa2 and hash(fa) == hash(fa2), "Req2.3: equal -> equal hash"

# Req2.1: hash incorporates model identity -> fields on different models with the
# same counter are permitted to (and here must, per Req2.4) differ. Build two
# inherited descriptors sharing a counter but on different models.
class Base(models.Model):
    g = models.IntegerField()
    class Meta:
        app_label = 'myapp'
        abstract = True
class MA(Base):
    class Meta:
        app_label = 'aaa'
class MB(Base):
    class Meta:
        app_label = 'bbb'
ga = MA._meta.get_field('g')
gb = MB._meta.get_field('g')
print('same counter:', ga.creation_counter == gb.creation_counter,
      'hashes differ:', hash(ga) != hash(gb))
assert ga.creation_counter == gb.creation_counter
assert hash(ga) != hash(gb), "Req2.1/2.4: hash incorporates model identity"

# Req4.3: usable in set/dict
d = {fa: 1, f1: 2}
assert d[fa] == 1
print("PASS")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.2 + Req2.4.
Fields inherited from an abstract base by two different concrete models
share creation_counter but are attached to different models -> must be
UNEQUAL and coexist as 2 distinct elements in a set.
HOLDS on patched, FAILS at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class AbstractBase(models.Model):
    myfield = models.IntegerField()
    class Meta:
        app_label = 'myapp'
        abstract = True

class ModelA(AbstractBase):
    class Meta:
        app_label = 'myapp'

class ModelB(AbstractBase):
    class Meta:
        app_label = 'myapp'

fa = ModelA._meta.get_field('myfield')
fb = ModelB._meta.get_field('myfield')
print('creation_counters:', fa.creation_counter, fb.creation_counter)
print('fa==fb:', fa == fb)
s = {fa, fb}
print('len(set):', len(s))
assert fa.creation_counter == fb.creation_counter, "precondition: same counter"
assert fa != fb, "Req1.2: different models -> unequal"
assert len(s) == 2, "Req2.4: both coexist in set"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on gold-patched tree; all executed via nl_attack in the official image.

Probe->requirement mapping and results (PATCHED / BASE / WEAK-candidate):
- probe_1 (POSITIVE CONTROL): Req1.2 + Req2.4 — two inherited descriptors from an abstract base share creation_counter but attach to different models -> must be UNEQUAL and both coexist in a set (len==2). PATCHED: HOLDS (fa!=fb, set len 2). BASE: FAILS (assert fa!=fb) => prepatch_reproduced=True. WEAK: HOLDS (eq/hash fixed).
- probe_2: Req1.3/1.4/4.4 — same model+counter equal; two unattached same-counter equal; self equal & stable hash. PATCHED HOLDS.
- probe_3: Req1.5/3.5/1.6/2.2 — __eq__(non-Field) is NotImplemented (== -> False, != -> True); __lt__(non-Field) NotImplemented (TypeError); hashing an unattached field does not raise. PATCHED HOLDS.
- probe_4: Req3.1/3.3/3.4/3.6 — ordering: smaller counter first regardless of model; same-counter one-unattached -> unattached first; same-counter both attached -> lexicographic by (app_label, model_name) (aaa<zzz); equal -> neither < other. PATCHED HOLDS. BASE FAILS (assert fa<fz). WEAK candidate (eq+hash fixed, __lt__ left counter-only) FAILS here => suite discriminates the wrong fix.
- probe_5: Req2.1/2.3/4.1/4.2/4.3 — monotonic distinct counters; sort of distinct-counter fields == sort by counter alone; equal->equal hash; hash incorporates model identity so two same-counter fields on different models get different hashes; usable as dict keys. PATCHED HOLDS.

CANDIDATE PATCH exercised: weak.diff applies gold's __eq__ and __hash__ changes but leaves __lt__ counter-only. Runner-executed results under --patch: probe_1,2,3,5 exit 0; probe_4 exit 1 (REJECTED). This proves the suite discriminates a plausible partial fix (the naive 'only equality/hash matter' reading), so the requirements are not too weak on the ordering criteria. No requirement-conforming patch was found that fails the hidden tests.

Positive control discriminates: probe_1 HOLDS on patched, FAILS at base. Verdict SOUND: >=5 probes hold on the patched tree, positive control discriminates base vs patched, and a wrong-fix candidate is rejected by the suite.

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
"""Positive control: Req1.2 + Req2.4.
Fields inherited from an abstract base by two different concrete models
share creation_counter but are attached to different models -> must be
UNEQUAL and coexist as 2 distinct elements in a set.
HOLDS on patched, FAILS at base."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    )
django.setup()
from django.db import models


class AbstractBase(models.Model):
    myfield = models.IntegerField()
    class Meta:
        app_label = 'myapp'
        abstract = True

class ModelA(AbstractBase):
    class Meta:
        app_label = 'myapp'

class ModelB(AbstractBase):
    class Meta:
        app_label = 'myapp'

fa = ModelA._meta.get_field('myfield')
fb = ModelB._meta.get_field('myfield')
print('creation_counters:', fa.creation_counter, fb.creation_counter)
print('fa==fb:', fa == fb)
s = {fa, fb}
print('len(set):', len(s))
assert fa.creation_counter == fb.creation_counter, "precondition: same counter"
assert fa != fb, "Req1.2: different models -> unequal"
assert len(s) == 2, "Req2.4: both coexist in set"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on gold-patched tree; all executed via nl_attack in the official image.

Probe->requirement mapping and results (PATCHED / BASE / WEAK-candidate):
- probe_1 (POSITIVE CONTROL): Req1.2 + Req2.4 — two inherited descriptors from an abstract base share creation_counter but attach to different models -> must be UNEQUAL and both coexist in a set (len==2). PATCHED: HOLDS (fa!=fb, set len 2). BASE: FAILS (assert fa!=fb) => prepatch_reproduced=True. WEAK: HOLDS (eq/hash fixed).
- probe_2: Req1.3/1.4/4.4 — same model+counter equal; two unattached same-counter equal; self equal & stable hash. PATCHED HOLDS.
- probe_3: Req1.5/3.5/1.6/2.2 — __eq__(non-Field) is NotImplemented (== -> False, != -> True); __lt__(non-Field) NotImplemented (TypeError); hashing an unattached field does not raise. PATCHED HOLDS.
- probe_4: Req3.1/3.3/3.4/3.6 — ordering: smaller counter first regardless of model; same-counter one-unattached -> unattached first; same-counter both attached -> lexicographic by (app_label, model_name) (aaa<zzz); equal -> neither < other. PATCHED HOLDS. BASE FAILS (assert fa<fz). WEAK candidate (eq+hash fixed, __lt__ left counter-only) FAILS here => suite discriminates the wrong fix.
- probe_5: Req2.1/2.3/4.1/4.2/4.3 — monotonic distinct counters; sort of distinct-counter fields == sort by counter alone; equal->equal hash; hash incorporates model identity so two same-counter fields on different models get different hashes; usable as dict keys. PATCHED HOLDS.

CANDIDATE PATCH exercised: weak.diff applies gold's __eq__ and __hash__ changes but leaves __lt__ counter-only. Runner-executed results under --patch: probe_1,2,3,5 exit 0; probe_4 exit 1 (REJECTED). This proves the suite discriminates a plausible partial fix (the naive 'only equality/hash matter' reading), so the requirements are not too weak on the ordering criteria. No requirement-conforming patch was found that fails the hidden tests.

Positive control discriminates: probe_1 HOLDS on patched, FAILS at base. Verdict SOUND: >=5 probes hold on the patched tree, positive control discriminates base vs patched, and a wrong-fix candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe used module-scoped abstract base + two concrete models sharing app_label 'contenttypes' so all three inherited 'field' descriptors share creation_counter; patched: af!=f1!=f2, distinct hashes, set len 3, ordering af<f1<f2 by model_name lexicographic, unattached-fields-with-forced-equal-counter compare equal and hash equal, unattached ordered before attached. Requirements 1-4 model the full base Field boundary in fields/__init__.py exactly as the gold diff changes it — no over/under-specification found. Requirement text's use of getattr/hasattr semantics matches the patch's getattr(...,None) in __eq__ and hasattr guards in __lt__/__hash__.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally and localize it to Field.__eq__/__lt__/__hash__ in django/db/models/fields/__init__.py — legitimate localization even though the file/attribute names aren't in the problem_statement. Every specific detail (equality gated on creation_counter AND attached model; hash derived from (creation_counter, app_label, model_name); ordering by creation_counter first then unattached-first then lexicographic (app_label, model_name); NotImplemented for non-Field operands; getattr/hasattr tolerance for unattached descriptors) is a faithful behavioral translation of the gold patch, which is exactly the intended work — not a transmission of the tests. No test function/class names (e.g. test_abstract_inherited_fields), no test file path (tests/model_fields/tests.py), no FAIL_TO_PASS string, no quoted test/gold code, and no fix-invented identifiers appear. The Requirement-3 case list enumerates the four ordering branches of the gold __lt__ (describing behavior), not the test's concrete AbstractModel/InheritAbstractModel1/2 fixtures or its assertLess chain, so it does not reconstruct the hidden test. The hidden test's specific scenario (abstract base + two concrete inheritors collapsing in a set) is already fully disclosed in the public problem_statement (classes A/B/C, len({...})==1). No leakage beyond the public spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
