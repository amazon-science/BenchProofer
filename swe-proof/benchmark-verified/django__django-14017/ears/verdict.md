# P2 adversarial audit — django__django-14017

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Req 1.1/1.2/1.3/1.4/1.5.
Q(...) & Exists(...) and Q(...) | Exists(...) must NOT raise (commutativity),
and must filter to exactly the correct rows (same as expression-first order).
Exits 0 iff all hold. FAILS at base (TypeError from Q._combine)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType('testapp')
app.__path__ = ['/work']
sys.modules['testapp'] = app

django.setup()
from django.db import models, connection

class Employee(models.Model):
    name = models.CharField(max_length=50)
    salary = models.IntegerField()
    class Meta:
        app_label = 'testapp'

class Company(models.Model):
    name = models.CharField(max_length=50)
    point_of_contact = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL, related_name='+')
    class Meta:
        app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(Employee)
    se.create_model(Company)

from django.db.models import Q, Exists, OuterRef

alice = Employee.objects.create(name='alice', salary=10)   # not poc, salary<15
bob   = Employee.objects.create(name='bob',   salary=40)   # poc, salary>=30
carol = Employee.objects.create(name='carol', salary=20)   # not poc, mid
Company.objects.create(name='c1', point_of_contact=bob)

is_poc = Company.objects.filter(point_of_contact=OuterRef('pk'))

ok = True
def check(label, qs, expected_names):
    global ok
    got = sorted(e.name for e in qs)
    exp = sorted(expected_names)
    print(f"{label}: got={got} expected={exp}")
    if got != exp:
        ok = False

# Req 1.1/1.3 : Q & Exists  (salary>=30 AND is_poc) -> bob
check("Q&Exists", Employee.objects.filter(Q(salary__gte=30) & Exists(is_poc)), ['bob'])
# commutativity vs Exists & Q
check("Exists&Q", Employee.objects.filter(Exists(is_poc) & Q(salary__gte=30)), ['bob'])

# Req 1.2/1.4 : Q | Exists (salary<15 OR is_poc) -> alice, bob
check("Q|Exists", Employee.objects.filter(Q(salary__lt=15) | Exists(is_poc)), ['alice', 'bob'])
check("Exists|Q", Employee.objects.filter(Exists(is_poc) | Q(salary__lt=15)), ['alice', 'bob'])

# Req 1.5 commutativity explicit: both AND orders equal, both OR orders equal
and1 = sorted(e.name for e in Employee.objects.filter(Q(salary__gte=30) & Exists(is_poc)))
and2 = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) & Q(salary__gte=30)))
or1 = sorted(e.name for e in Employee.objects.filter(Q(salary__lt=15) | Exists(is_poc)))
or2 = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) | Q(salary__lt=15)))
print(f"commut AND {and1}=={and2}? OR {or1}=={or2}?")
if and1 != and2 or or1 != or2:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 2.3: empty Q() combined with a conditional expression reduces to
the expression alone, in both & and | and both orders. Rows selected must be
exactly those satisfying the expression (the poc employee)."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'], USE_TZ=False)
app = types.ModuleType('testapp'); app.__path__ = ['/work']; sys.modules['testapp'] = app
django.setup()
from django.db import models, connection
class Employee(models.Model):
    name = models.CharField(max_length=50); salary = models.IntegerField()
    class Meta: app_label = 'testapp'
class Company(models.Model):
    name = models.CharField(max_length=50)
    point_of_contact = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL, related_name='+')
    class Meta: app_label = 'testapp'
with connection.schema_editor() as se:
    se.create_model(Employee); se.create_model(Company)
from django.db.models import Q, Exists, OuterRef
alice = Employee.objects.create(name='alice', salary=10)
bob = Employee.objects.create(name='bob', salary=40)
Company.objects.create(name='c1', point_of_contact=bob)
is_poc = Company.objects.filter(point_of_contact=OuterRef('pk'))
expr_only = sorted(e.name for e in Employee.objects.filter(Exists(is_poc)))
print("expr alone:", expr_only)  # ['bob']
ok = expr_only == ['bob']
for label, cond in [
    ("Q()&Exists", Q() & Exists(is_poc)),
    ("Exists&Q()", Exists(is_poc) & Q()),
    ("Q()|Exists", Q() | Exists(is_poc)),
    ("Exists|Q()", Exists(is_poc) | Q()),
]:
    got = sorted(e.name for e in Employee.objects.filter(cond))
    print(f"{label}: {got}")
    if got != expr_only:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 3.2: reject operands that are neither Q nor conditional-truthy.
- plain object -> TypeError
- object with conditional=False -> TypeError
- object with conditional missing -> TypeError
- object with conditional truthy-but-not-True (e.g. 1) -> TypeError
  (criterion 3.2: mere presence not sufficient; gold uses `is True`)."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
django.setup()
from django.db.models import Q

class Plain: pass
class CondFalse: conditional = False
class CondOne: conditional = 1  # truthy but not the boolean True

ok = True
def expect_typeerror(label, other, op):
    global ok
    try:
        if op == '&':
            Q(x=1) & other
        else:
            Q(x=1) | other
        print(f"{label} ({op}): NO ERROR -> FAIL")
        ok = False
    except TypeError:
        print(f"{label} ({op}): TypeError (ok)")
    except Exception as e:
        print(f"{label} ({op}): {type(e).__name__} {e} -> FAIL")
        ok = False

for op in ('&', '|'):
    expect_typeerror("plain object", Plain(), op)
    expect_typeerror("conditional=False", CondFalse(), op)
    expect_typeerror("no conditional attr", object(), op)
    # 3.2: conditional present but not truthy-True. Gold guard is `is True`,
    # so conditional=1 must still be rejected.
    expect_typeerror("conditional=1 (not True)", CondOne(), op)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 4.1 (SHALL keep Q&Q / Q|Q) and Req 2.2 (non-empty Q combined with empty
Q reduces to the non-empty Q). Regression coverage."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'], USE_TZ=False)
app = types.ModuleType('testapp'); app.__path__ = ['/work']; sys.modules['testapp'] = app
django.setup()
from django.db import models, connection
class Employee(models.Model):
    name = models.CharField(max_length=50); salary = models.IntegerField()
    class Meta: app_label = 'testapp'
with connection.schema_editor() as se:
    se.create_model(Employee)
from django.db.models import Q
Employee.objects.create(name='alice', salary=10)
Employee.objects.create(name='bob', salary=40)
Employee.objects.create(name='carol', salary=20)
ok = True
def check(label, qs, exp):
    global ok
    got = sorted(e.name for e in qs); exp = sorted(exp)
    print(f"{label}: {got} exp {exp}")
    if got != exp: ok = False
# Q & Q  (salary>=20 AND salary<30) -> carol
check("Q&Q", Employee.objects.filter(Q(salary__gte=20) & Q(salary__lt=30)), ['carol'])
# Q | Q  (salary<15 OR salary>=40) -> alice, bob
check("Q|Q", Employee.objects.filter(Q(salary__lt=15) | Q(salary__gte=40)), ['alice', 'bob'])
# Req 2.2: non-empty Q & empty Q  -> non-empty alone
check("Q(salary<15)&Q()", Employee.objects.filter(Q(salary__lt=15) & Q()), ['alice'])
check("Q(salary<15)|Q()", Employee.objects.filter(Q(salary__lt=15) | Q()), ['alice'])
check("Q()&Q(salary<15)", Employee.objects.filter(Q() & Q(salary__lt=15)), ['alice'])
# combining two empty Q must not raise and yields all rows
allrows = ['alice', 'bob', 'carol']
check("Q()&Q()", Employee.objects.filter(Q() & Q()), allrows)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.4: two conditional expressions combined with & / | still yield a
combined filter condition that works on a queryset.
Req 4.3: combining two non-conditional expressions with bitwise ops SHALL
continue to be rejected as before."""
import django, sys, types
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'], USE_TZ=False)
app = types.ModuleType('testapp'); app.__path__ = ['/work']; sys.modules['testapp'] = app
django.setup()
from django.db import models, connection
class Employee(models.Model):
    name = models.CharField(max_length=50); salary = models.IntegerField()
    class Meta: app_label = 'testapp'
class Company(models.Model):
    name = models.CharField(max_length=50)
    point_of_contact = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL, related_name='+')
    ceo = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL, related_name='+')
    class Meta: app_label = 'testapp'
with connection.schema_editor() as se:
    se.create_model(Employee); se.create_model(Company)
from django.db.models import Q, Exists, OuterRef, F
alice = Employee.objects.create(name='alice', salary=10)
bob = Employee.objects.create(name='bob', salary=40)
Company.objects.create(name='c1', point_of_contact=bob, ceo=bob)
is_poc = Company.objects.filter(point_of_contact=OuterRef('pk'))
is_ceo = Company.objects.filter(ceo=OuterRef('pk'))
ok = True
# Req 4.4: two conditional expressions combined -> combined filter
got_and = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) & Exists(is_ceo)))
got_or = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) | Exists(is_ceo)))
print("Exists&Exists:", got_and, "Exists|Exists:", got_or)
if got_and != ['bob'] or got_or != ['bob']:
    ok = False

# Req 4.3: two non-conditional expressions with bitwise ops must continue to be
# rejected as before. The documented error for combining non-conditional
# expressions is NotImplementedError (Combinable._combine bitwise guard); the
# criterion is that it stays rejected, not silently accepted.
try:
    F('salary') & F('salary')
    print("F & F: NO ERROR -> FAIL")
    ok = False
except (NotImplementedError, TypeError) as e:
    print("F & F: rejected as before:", type(e).__name__, str(e)[:60])
except Exception as e:
    print("F & F: unexpected", type(e).__name__, "-> FAIL")
    ok = False
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req 1.1/1.2/1.3/1.4/1.5.
Q(...) & Exists(...) and Q(...) | Exists(...) must NOT raise (commutativity),
and must filter to exactly the correct rows (same as expression-first order).
Exits 0 iff all hold. FAILS at base (TypeError from Q._combine)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType('testapp')
app.__path__ = ['/work']
sys.modules['testapp'] = app

django.setup()
from django.db import models, connection

class Employee(models.Model):
    name = models.CharField(max_length=50)
    salary = models.IntegerField()
    class Meta:
        app_label = 'testapp'

class Company(models.Model):
    name = models.CharField(max_length=50)
    point_of_contact = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL, related_name='+')
    class Meta:
        app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(Employee)
    se.create_model(Company)

from django.db.models import Q, Exists, OuterRef

alice = Employee.objects.create(name='alice', salary=10)   # not poc, salary<15
bob   = Employee.objects.create(name='bob',   salary=40)   # poc, salary>=30
carol = Employee.objects.create(name='carol', salary=20)   # not poc, mid
Company.objects.create(name='c1', point_of_contact=bob)

is_poc = Company.objects.filter(point_of_contact=OuterRef('pk'))

ok = True
def check(label, qs, expected_names):
    global ok
    got = sorted(e.name for e in qs)
    exp = sorted(expected_names)
    print(f"{label}: got={got} expected={exp}")
    if got != exp:
        ok = False

# Req 1.1/1.3 : Q & Exists  (salary>=30 AND is_poc) -> bob
check("Q&Exists", Employee.objects.filter(Q(salary__gte=30) & Exists(is_poc)), ['bob'])
# commutativity vs Exists & Q
check("Exists&Q", Employee.objects.filter(Exists(is_poc) & Q(salary__gte=30)), ['bob'])

# Req 1.2/1.4 : Q | Exists (salary<15 OR is_poc) -> alice, bob
check("Q|Exists", Employee.objects.filter(Q(salary__lt=15) | Exists(is_poc)), ['alice', 'bob'])
check("Exists|Q", Employee.objects.filter(Exists(is_poc) | Q(salary__lt=15)), ['alice', 'bob'])

# Req 1.5 commutativity explicit: both AND orders equal, both OR orders equal
and1 = sorted(e.name for e in Employee.objects.filter(Q(salary__gte=30) & Exists(is_poc)))
and2 = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) & Q(salary__gte=30)))
or1 = sorted(e.name for e in Employee.objects.filter(Q(salary__lt=15) | Exists(is_poc)))
or2 = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) | Q(salary__lt=15)))
print(f"commut AND {and1}=={and2}? OR {or1}=={or2}?")
if and1 != and2 or or1 != or2:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-14017: Q._combine gold fix relaxes the RHS type guard to `isinstance(other, Q) or getattr(other,'conditional',False) is True`, making &/| commutative for Q/conditional-expression pairs.

Probes (all DB-backed via in-memory sqlite; standalone, no pytest). Results on gold-PATCHED tree unless noted:
- probe_1 (POSITIVE CONTROL; Req 1.1-1.5): Q & Exists and Q | Exists do not raise, filter to exactly the correct rows, and are commutative with the expression-first order. HOLDS patched; FAILS at base (TypeError from Q._combine raise) -> prepatch reproduced.
- probe_2 (Req 2.1/2.3): empty Q() combined with Exists in both &/| and both orders reduces to the expression alone. HOLDS.
- probe_3 (Req 3.1/3.2): plain object / conditional=False / missing conditional / conditional=1 (truthy but not boolean True) all raise TypeError in both & and |. HOLDS. Encodes the `is True` strictness.
- probe_4 (Req 4.1/2.2): Q&Q, Q|Q, non-empty Q with empty Q (both orders), Q()&Q() regression. HOLDS.
- probe_5 (Req 4.3/4.4): Exists&Exists and Exists|Exists still yield combined filters; F&F still rejected with the documented NotImplementedError. HOLDS.

Candidate wrong patches (REQUIRED floor: >=1 exercised, >=1 rejected):
- weak_truthy.diff: drops `is True`, using plain truthiness `getattr(other,'conditional',False)`. REJECTED by probe_3 (conditional=1 wrongly accepted in both & and |), violating Req 3.2.
- weak_and_only.diff: accepts conditional only when conn==AND. REJECTED by probe_1 (Q | Exists raises TypeError), violating Req 1.2/1.4/1.5.

Both candidates rejected => suite discriminates wrong implementations. All 5 probes hold on patched; positive control discriminates base vs patched. No requirements-conforming alternative patch found that would fail hidden tests. Verdict SOUND.

Note: probe_5 initially expected TypeError for F&F but the documented error is NotImplementedError ('Use .bitand()/.bitor()'); Req 4.3 says keep raising the documented error, so probe accepts either rejection type.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control + Req 1.1/1.2/1.3/1.4/1.5.
Q(...) & Exists(...) and Q(...) | Exists(...) must NOT raise (commutativity),
and must filter to exactly the correct rows (same as expression-first order).
Exits 0 iff all hold. FAILS at base (TypeError from Q._combine)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'testapp'],
    USE_TZ=False,
)
import sys, types
app = types.ModuleType('testapp')
app.__path__ = ['/work']
sys.modules['testapp'] = app

django.setup()
from django.db import models, connection

class Employee(models.Model):
    name = models.CharField(max_length=50)
    salary = models.IntegerField()
    class Meta:
        app_label = 'testapp'

class Company(models.Model):
    name = models.CharField(max_length=50)
    point_of_contact = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL, related_name='+')
    class Meta:
        app_label = 'testapp'

with connection.schema_editor() as se:
    se.create_model(Employee)
    se.create_model(Company)

from django.db.models import Q, Exists, OuterRef

alice = Employee.objects.create(name='alice', salary=10)   # not poc, salary<15
bob   = Employee.objects.create(name='bob',   salary=40)   # poc, salary>=30
carol = Employee.objects.create(name='carol', salary=20)   # not poc, mid
Company.objects.create(name='c1', point_of_contact=bob)

is_poc = Company.objects.filter(point_of_contact=OuterRef('pk'))

ok = True
def check(label, qs, expected_names):
    global ok
    got = sorted(e.name for e in qs)
    exp = sorted(expected_names)
    print(f"{label}: got={got} expected={exp}")
    if got != exp:
        ok = False

# Req 1.1/1.3 : Q & Exists  (salary>=30 AND is_poc) -> bob
check("Q&Exists", Employee.objects.filter(Q(salary__gte=30) & Exists(is_poc)), ['bob'])
# commutativity vs Exists & Q
check("Exists&Q", Employee.objects.filter(Exists(is_poc) & Q(salary__gte=30)), ['bob'])

# Req 1.2/1.4 : Q | Exists (salary<15 OR is_poc) -> alice, bob
check("Q|Exists", Employee.objects.filter(Q(salary__lt=15) | Exists(is_poc)), ['alice', 'bob'])
check("Exists|Q", Employee.objects.filter(Exists(is_poc) | Q(salary__lt=15)), ['alice', 'bob'])

# Req 1.5 commutativity explicit: both AND orders equal, both OR orders equal
and1 = sorted(e.name for e in Employee.objects.filter(Q(salary__gte=30) & Exists(is_poc)))
and2 = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) & Q(salary__gte=30)))
or1 = sorted(e.name for e in Employee.objects.filter(Q(salary__lt=15) | Exists(is_poc)))
or2 = sorted(e.name for e in Employee.objects.filter(Exists(is_poc) | Q(salary__lt=15)))
print(f"commut AND {and1}=={and2}? OR {or1}=={or2}?")
if and1 != and2 or or1 != or2:
    ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-14017: Q._combine gold fix relaxes the RHS type guard to `isinstance(other, Q) or getattr(other,'conditional',False) is True`, making &/| commutative for Q/conditional-expression pairs.

Probes (all DB-backed via in-memory sqlite; standalone, no pytest). Results on gold-PATCHED tree unless noted:
- probe_1 (POSITIVE CONTROL; Req 1.1-1.5): Q & Exists and Q | Exists do not raise, filter to exactly the correct rows, and are commutative with the expression-first order. HOLDS patched; FAILS at base (TypeError from Q._combine raise) -> prepatch reproduced.
- probe_2 (Req 2.1/2.3): empty Q() combined with Exists in both &/| and both orders reduces to the expression alone. HOLDS.
- probe_3 (Req 3.1/3.2): plain object / conditional=False / missing conditional / conditional=1 (truthy but not boolean True) all raise TypeError in both & and |. HOLDS. Encodes the `is True` strictness.
- probe_4 (Req 4.1/2.2): Q&Q, Q|Q, non-empty Q with empty Q (both orders), Q()&Q() regression. HOLDS.
- probe_5 (Req 4.3/4.4): Exists&Exists and Exists|Exists still yield combined filters; F&F still rejected with the documented NotImplementedError. HOLDS.

Candidate wrong patches (REQUIRED floor: >=1 exercised, >=1 rejected):
- weak_truthy.diff: drops `is True`, using plain truthiness `getattr(other,'conditional',False)`. REJECTED by probe_3 (conditional=1 wrongly accepted in both & and |), violating Req 3.2.
- weak_and_only.diff: accepts conditional only when conn==AND. REJECTED by probe_1 (Q | Exists raises TypeError), violating Req 1.2/1.4/1.5.

Both candidates rejected => suite discriminates wrong implementations. All 5 probes hold on patched; positive control discriminates base vs patched. No requirements-conforming alternative patch found that would fail hidden tests. Verdict SOUND.

Note: probe_5 initially expected TypeError for F&F but the documented error is NotImplementedError ('Use .bitand()/.bitor()'); Req 4.3 says keep raising the documented error, so probe accepts either rejection type.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched tree: full _combine source confirmed via inspect; acceptance of conditional-True, rejection of conditional=False/1/absent (strict `is True`), and empty-operand neutral-element branch all behave as the requirements state. Modeling boundary is correct — biconditional accept/reject on `conditional is True` plus the Q/Q and expr-first preservation clauses.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the change behaviorally: commutative &/| for Q + conditional expression, empty-operand shortcuts, and TypeError rejection of unsupported operands. It legitimately localizes the change (Q._combine, Q.__and__/__or__, query_utils.py) and uses the pre-existing public `conditional` attribute — not a fix-invented identifier. No hidden-test content leaks: none of the test names (test_boolean_expression_combined, test_boolean_expression_combined_with_empty_Q), the path tests/expressions/tests.py, the fixtures/models (Employee, Company, is_poc, is_ceo, self.max, salary__gte=30/salary__lt=15), or expected result rows appear. The empty-Q commutativity enumeration (Req 2) derives from the PUBLIC problem_statement, which already shows both Exists(...) & Q() and Q() & Exists(...). No quoted test/gold code and no case enumeration mirroring the parametrized rows/expected outputs; the gold's `is True` semantics are rendered as behavioral prose, not transmitted verbatim.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
