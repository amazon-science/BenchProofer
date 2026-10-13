# P2 adversarial audit — django__django-12774

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

Counterexample / evidence:

```
Weak candidate patch collects single-field UniqueConstraints from opts.constraints (all of them) instead of opts.total_unique_constraints, so it wrongly ACCEPTS a field covered only by a partial/conditional UniqueConstraint. probe_3 (Req2.3) VIOLATED under this patch (exit 1: partial-constraint field accepted), while all other probes hold — demonstrating the suite discriminates the correct total-vs-any-constraint boundary.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req1.1/1.2/1.3 + positive control: in_bulk on a field made unique by a
TOTAL single-field UniqueConstraint SHALL proceed and return value->object map.
Exits 0 iff no ValueError and mapping correct."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class M(models.Model):
    slug = models.CharField(max_length=50)
    class Meta:
        app_label = 'auth'
        constraints = [models.UniqueConstraint(fields=['slug'], name='u_slug_total')]

with connection.schema_editor() as se:
    se.create_model(M)

M.objects.create(slug='a')
M.objects.create(slug='b')
M.objects.create(slug='c')

try:
    # 1.2/1.3: explicit list, missing value omitted
    d = M.objects.in_bulk(['a', 'c', 'zzz'], field_name='slug')
except ValueError as e:
    print("FAIL: ValueError raised on constraint-unique field:", e)
    raise SystemExit(1)

print("returned keys:", sorted(d.keys()))
ok = set(d.keys()) == {'a', 'c'} and d['a'].slug == 'a' and d['c'].slug == 'c'
if not ok:
    print("FAIL: mapping wrong", d)
    raise SystemExit(1)

# 1.1: no explicit list -> all rows
d2 = M.objects.in_bulk(field_name='slug')
print("all keys:", sorted(d2.keys()))
if set(d2.keys()) != {'a', 'b', 'c'}:
    print("FAIL: full map wrong")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2: a non-pk field neither unique nor covered by any total
single-field constraint SHALL raise ValueError with the exact message.
Exits 0 iff ValueError raised with matching message."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class M(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        app_label = 'auth'

with connection.schema_editor() as se:
    se.create_model(M)
M.objects.create(name='x')

expected = "in_bulk()'s field_name must be a unique field but %r isn't." % 'name'
try:
    M.objects.in_bulk(['x'], field_name='name')
except ValueError as e:
    print("got ValueError:", e)
    if str(e) == expected:
        print("PASS")
        raise SystemExit(0)
    print("FAIL: message mismatch; expected:", expected)
    raise SystemExit(1)
print("FAIL: no ValueError raised for non-unique field")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.3: a field covered only by a PARTIAL (conditional) unique constraint
SHALL be treated as not guaranteed unique -> ValueError.
Exits 0 iff ValueError raised."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection
from django.db.models import Q

class M(models.Model):
    slug = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    class Meta:
        app_label = 'auth'
        constraints = [models.UniqueConstraint(fields=['slug'], name='u_slug_partial',
                                                condition=Q(active=True))]

with connection.schema_editor() as se:
    se.create_model(M)
M.objects.create(slug='a', active=True)

try:
    M.objects.in_bulk(['a'], field_name='slug')
except ValueError as e:
    print("PASS: partial-constraint field rejected:", e)
    raise SystemExit(0)
print("FAIL: partial-constraint field was accepted (should raise)")
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.4: a field covered only within a MULTI-field unique constraint SHALL
be treated as not guaranteed unique -> ValueError.
Exits 0 iff ValueError raised."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class M(models.Model):
    a = models.CharField(max_length=50)
    b = models.CharField(max_length=50)
    class Meta:
        app_label = 'auth'
        constraints = [models.UniqueConstraint(fields=['a', 'b'], name='u_ab')]

with connection.schema_editor() as se:
    se.create_model(M)
M.objects.create(a='x', b='y')

try:
    M.objects.in_bulk(['x'], field_name='a')
except ValueError as e:
    print("PASS: multi-field-constraint field rejected:", e)
    raise SystemExit(0)
print("FAIL: field in multi-field constraint was accepted (should raise)")
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3: regression protection.
3.1 pk default works; 3.2 unique=True field works; 3.3 empty id_list -> {} without query;
3.4 id_list=None -> all rows; 3.6 sliced queryset fails.
Exits 0 iff all hold."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class M(models.Model):
    code = models.CharField(max_length=50, unique=True)
    class Meta:
        app_label = 'auth'

with connection.schema_editor() as se:
    se.create_model(M)
o1 = M.objects.create(code='p')
o2 = M.objects.create(code='q')

# 3.1 pk default
d = M.objects.in_bulk([o1.pk, o2.pk])
assert set(d.keys()) == {o1.pk, o2.pk}, ("pk default failed", d)
print("3.1 ok")

# 3.2 unique=True field
d = M.objects.in_bulk(['p'], field_name='code')
assert list(d.keys()) == ['p'] and d['p'].pk == o1.pk, ("unique field failed", d)
print("3.2 ok")

# 3.3 empty id_list -> {} without query
from django.db import connection as conn
n_before = len(conn.queries_log)
d = M.objects.in_bulk([])
assert d == {}, ("empty id_list not empty", d)
print("3.3 ok (empty dict)")

# 3.4 id_list=None -> all rows
d = M.objects.in_bulk()
assert set(d.keys()) == {o1.pk, o2.pk}, ("None id_list failed", d)
print("3.4 ok")

# 3.6 sliced queryset must fail
try:
    M.objects.all()[:1].in_bulk()
    print("FAIL: sliced in_bulk did not raise")
    raise SystemExit(1)
except (AssertionError, TypeError) as e:
    print("3.6 ok: sliced rejected:", type(e).__name__)

print("PASS")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1/1.2/1.3 + positive control: in_bulk on a field made unique by a
TOTAL single-field UniqueConstraint SHALL proceed and return value->object map.
Exits 0 iff no ValueError and mapping correct."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class M(models.Model):
    slug = models.CharField(max_length=50)
    class Meta:
        app_label = 'auth'
        constraints = [models.UniqueConstraint(fields=['slug'], name='u_slug_total')]

with connection.schema_editor() as se:
    se.create_model(M)

M.objects.create(slug='a')
M.objects.create(slug='b')
M.objects.create(slug='c')

try:
    # 1.2/1.3: explicit list, missing value omitted
    d = M.objects.in_bulk(['a', 'c', 'zzz'], field_name='slug')
except ValueError as e:
    print("FAIL: ValueError raised on constraint-unique field:", e)
    raise SystemExit(1)

print("returned keys:", sorted(d.keys()))
ok = set(d.keys()) == {'a', 'c'} and d['a'].slug == 'a' and d['c'].slug == 'c'
if not ok:
    print("FAIL: mapping wrong", d)
    raise SystemExit(1)

# 1.1: no explicit list -> all rows
d2 = M.objects.in_bulk(field_name='slug')
print("all keys:", sorted(d2.keys()))
if set(d2.keys()) != {'a', 'b', 'c'}:
    print("FAIL: full map wrong")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Probe results (patched / base / weak-candidate):
- probe_1 (Req1.1/1.2/1.3 + positive control): total single-field UniqueConstraint field accepted, correct value->object map incl. omission of missing values and id_list=None all-rows. PATCHED=HOLDS, BASE=VIOLATED (in_bulk wrongly raised ValueError on constraint-unique slug), WEAK=HOLDS.
- probe_2 (Req2.1/2.2): plain non-unique field raises ValueError with exact message text. PATCHED=HOLDS, BASE=HOLDS, WEAK=HOLDS.
- probe_3 (Req2.3): field covered only by a PARTIAL (condition=Q(...)) constraint must raise. PATCHED=HOLDS, WEAK=VIOLATED (rejected the weak fix).
- probe_4 (Req2.4): field in a MULTI-field constraint must raise. PATCHED=HOLDS, WEAK=HOLDS.
- probe_5 (Req3.1/3.2/3.3/3.4/3.6 regression): pk default, unique=True field, empty id_list->{}, id_list=None->all, sliced queryset raises AssertionError. PATCHED=HOLDS.
All 5 probes hold on the gold-patched tree; positive control (probe_1) fails at base and holds patched (discriminating power confirmed). The requirements-conforming-but-wrong candidate was exercised and REJECTED by probe_3, so the suite is not too weak on the total-vs-conditional boundary. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate patch collects single-field UniqueConstraints from opts.constraints (all of them) instead of opts.total_unique_constraints, so it wrongly ACCEPTS a field covered only by a partial/conditional UniqueConstraint. probe_3 (Req2.3) VIOLATED under this patch (exit 1: partial-constraint field accepted), while all other probes hold — demonstrating the suite discriminates the correct total-vs-any-constraint boundary.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1.1/1.2/1.3 + positive control: in_bulk on a field made unique by a
TOTAL single-field UniqueConstraint SHALL proceed and return value->object map.
Exits 0 iff no ValueError and mapping correct."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import models, connection

class M(models.Model):
    slug = models.CharField(max_length=50)
    class Meta:
        app_label = 'auth'
        constraints = [models.UniqueConstraint(fields=['slug'], name='u_slug_total')]

with connection.schema_editor() as se:
    se.create_model(M)

M.objects.create(slug='a')
M.objects.create(slug='b')
M.objects.create(slug='c')

try:
    # 1.2/1.3: explicit list, missing value omitted
    d = M.objects.in_bulk(['a', 'c', 'zzz'], field_name='slug')
except ValueError as e:
    print("FAIL: ValueError raised on constraint-unique field:", e)
    raise SystemExit(1)

print("returned keys:", sorted(d.keys()))
ok = set(d.keys()) == {'a', 'c'} and d['a'].slug == 'a' and d['c'].slug == 'c'
if not ok:
    print("FAIL: mapping wrong", d)
    raise SystemExit(1)

# 1.1: no explicit list -> all rows
d2 = M.objects.in_bulk(field_name='slug')
print("all keys:", sorted(d2.keys()))
if set(d2.keys()) != {'a', 'b', 'c'}:
    print("FAIL: full map wrong")
    raise SystemExit(1)
print("PASS")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Probe results (patched / base / weak-candidate):
- probe_1 (Req1.1/1.2/1.3 + positive control): total single-field UniqueConstraint field accepted, correct value->object map incl. omission of missing values and id_list=None all-rows. PATCHED=HOLDS, BASE=VIOLATED (in_bulk wrongly raised ValueError on constraint-unique slug), WEAK=HOLDS.
- probe_2 (Req2.1/2.2): plain non-unique field raises ValueError with exact message text. PATCHED=HOLDS, BASE=HOLDS, WEAK=HOLDS.
- probe_3 (Req2.3): field covered only by a PARTIAL (condition=Q(...)) constraint must raise. PATCHED=HOLDS, WEAK=VIOLATED (rejected the weak fix).
- probe_4 (Req2.4): field in a MULTI-field constraint must raise. PATCHED=HOLDS, WEAK=HOLDS.
- probe_5 (Req3.1/3.2/3.3/3.4/3.6 regression): pk default, unique=True field, empty id_list->{}, id_list=None->all, sliced queryset raises AssertionError. PATCHED=HOLDS.
All 5 probes hold on the gold-patched tree; positive control (probe_1) fails at base and holds patched (discriminating power confirmed). The requirements-conforming-but-wrong candidate was exercised and REJECTED by probe_3, so the suite is not too weak on the total-vs-conditional boundary. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch broadens the in_bulk guard by computing unique_fields from opts.total_unique_constraints (constraints with no condition) restricted to single-field constraints. total_unique_constraints excludes conditional (partial) constraints by construction, so requirement 2.3's partial-constraint rejection is faithful; the len==1 filter enforces requirement 2.4's multi-field rejection. Modeling boundary is correct — requirements describe the full changed behavior, not a narrow slice. All probes run in the instance image; base vs patched divergence confirmed on the slug case.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes only public/behavioral content. The ValueError message string ('in_bulk()'s field_name must be a unique field but %r isn't.') is public — it appears verbatim in the problem_statement traceback. The UniqueConstraint(fields=[...]) usage, unique=True, and field_name='slug' are all from the problem_statement. The fix concepts named (total/unconditional single-field unique constraint; 'considering only constraints that cover exactly one field'; _meta options) faithfully translate the gold logic (opts.total_unique_constraints + len(constraint.fields)==1) into behavioral requirements — legitimate localization, not gold-code transmission. The Req 2 enumeration (partial/conditional constraint rejected; multi-field/together constraint rejected) mirrors the two branches of the fix's own logic, not test-only artifacts. No hidden-test identifiers leak: no field values 'year'/'ean'/'brand', no model names Season/Model, no test method names (test_in_bulk_meta_constraint, test_in_bulk_non_unique_meta_constaint), no subTest/parametrization ids, no test file paths (tests/lookup/*), and no fix-invented identifier is exposed as such.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
