# P2 adversarial audit — django__django-15382

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
"""Req 1.3 (POSITIVE CONTROL): filter(~Exists(empty) & Q(pk=...)) returns the matching row."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
with connection.schema_editor() as se:
    se.create_model(Thing)
from django.db.models import Exists, Q

obj = Thing.objects.create(name='test')
qs = Thing.objects.filter(~Exists(Thing.objects.none()) & Q(pk=obj.pk))
rows = list(qs)
print("rows:", rows)
ok = rows == [obj]
print("expected exactly the matching row:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1: Exists.as_sql on empty subquery, negated -> returns ('', ()) instead of raising EmptyResultSet."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
from django.db.models import Exists
from django.core.exceptions import EmptyResultSet

expr = ~Exists(Thing.objects.none())
print("negated:", expr.negated)
compiler = Thing.objects.all().query.get_compiler(using='default')
try:
    sql, params = expr.as_sql(compiler, connection)
except EmptyResultSet:
    print("as_sql raised EmptyResultSet -- criterion FAILS")
    sys.exit(1)
print("as_sql returned:", repr(sql), repr(params))
ok = sql == '' and tuple(params) == ()
print("empty sql and empty params:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2: the compiled WHERE clause retains the additional condition (not dropped)."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
from django.db.models import Exists, Q

qs = Thing.objects.filter(~Exists(Thing.objects.none()) & Q(name='test'))
sql, params = qs.query.get_compiler(using='default').as_sql()
print("SQL:", sql)
print("params:", params)
has_where = 'WHERE' in sql.upper()
has_name = 'name' in sql.lower() and 'test' in [str(p) for p in params]
ok = has_where and has_name
print("WHERE retained with name condition:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1: NON-negated Exists over empty subquery still signals EmptyResultSet from as_sql."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
from django.db.models import Exists
from django.core.exceptions import EmptyResultSet

expr = Exists(Thing.objects.none())  # NOT negated
print("negated:", expr.negated)
compiler = Thing.objects.all().query.get_compiler(using='default')
try:
    sql, params = expr.as_sql(compiler, connection)
except EmptyResultSet:
    print("as_sql propagated EmptyResultSet -- criterion HOLDS")
    sys.exit(0)
print("as_sql returned instead of raising:", repr(sql), repr(params), "-- criterion FAILS")
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2 & 3.3 & 3.4: non-empty subquery -> EXISTS SQL; negated prefixes 'NOT '; params unchanged;
   inversion toggles negated flag."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
from django.db.models import Exists

compiler = Thing.objects.all().query.get_compiler(using='default')

pos = Exists(Thing.objects.filter(name='x'))
sql_pos, params_pos = pos.as_sql(compiler, connection)
print("non-negated:", repr(sql_pos), params_pos)

neg = ~Exists(Thing.objects.filter(name='x'))
sql_neg, params_neg = neg.as_sql(compiler, connection)
print("negated:", repr(sql_neg), params_neg)

e = Exists(Thing.objects.filter(name='x'))
print("base negated:", e.negated, " inverted:", (~e).negated)

c1 = 'EXISTS' in sql_pos.upper() and not sql_pos.upper().startswith('NOT')
c2 = sql_neg.upper().startswith('NOT ') and 'EXISTS' in sql_neg.upper()
c3 = list(params_pos) == list(params_neg)
c4 = (e.negated is False) and ((~e).negated is True)
print("checks:", c1, c2, c3, c4)
sys.exit(0 if (c1 and c2 and c3 and c4) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.1: a signal OTHER than EmptyResultSet raised while rendering the subquery
   must propagate unchanged, even when negated."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
from django.db.models import Exists
from django.db.models.expressions import Subquery

class Boom(Exception):
    pass

orig = Subquery.as_sql
def boom(self, *a, **k):
    raise Boom("other signal")
Subquery.as_sql = boom
try:
    expr = ~Exists(Thing.objects.filter(name='x'))
    compiler = Thing.objects.all().query.get_compiler(using='default')
    try:
        expr.as_sql(compiler, connection)
    except Boom:
        print("other signal propagated (negated) -- criterion HOLDS")
        sys.exit(0)
    except Exception as e:
        print("unexpected exception:", type(e).__name__, e)
        sys.exit(1)
    print("swallowed the other signal -- criterion FAILS")
    sys.exit(1)
finally:
    Subquery.as_sql = orig
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.3 (POSITIVE CONTROL): filter(~Exists(empty) & Q(pk=...)) returns the matching row."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
with connection.schema_editor() as se:
    se.create_model(Thing)
from django.db.models import Exists, Q

obj = Thing.objects.create(name='test')
qs = Thing.objects.filter(~Exists(Thing.objects.none()) & Q(pk=obj.pk))
rows = list(qs)
print("rows:", rows)
ok = rows == [obj]
print("expected exactly the matching row:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15382: Exists.as_sql must swallow EmptyResultSet ONLY when negated (return '', ()), returning a trivially-true empty fragment so surrounding WHERE conditions survive.

### PROBES (all standalone, build a real on-disk 'probeapp' package + sqlite :memory: model, stdlib+django only):
- probe_1 (Req 1.3, POSITIVE CONTROL): Manager-style filter(~Exists(none()) & Q(pk=obj.pk)) returns exactly [obj]. HOLDS patched; FAILS at base (rows==[]). Discriminates.
- probe_2 (Req 1.1): ~Exists(none()).as_sql returns ('', ()) rather than raising EmptyResultSet. HOLDS patched; at base raises EmptyResultSet -> fail.
- probe_3 (Req 1.2): compiled SQL for filter(~Exists(none()) & Q(name='test')) still has WHERE with name=%s param. HOLDS patched; base raises EmptyResultSet during compile -> fail.
- probe_4 (Req 2.1): NON-negated Exists(none()).as_sql still raises EmptyResultSet (must NOT swallow). HOLDS on both base and patched (guard is negated-only).
- probe_5 (Req 3.2/3.3/3.4): non-empty subquery -> non-negated yields EXISTS(...), negated yields 'NOT EXISTS(...)', params identical, and ~ toggles .negated. HOLDS both.
- probe_6 (Req 3.1): a non-EmptyResultSet signal raised during subquery render (monkeypatched Subquery.as_sql -> Boom) propagates even when negated. HOLDS patched (except clause catches only EmptyResultSet); base has no try so also propagates.

Positive control (probe_1): HOLDS patched, FAILS base (prepatch_reproduced=true).

### CANDIDATE WRONG PATCHES (both apply at base_commit 770d3e6a; both REJECTED by suite => suite discriminates, no TOO-WEAK finding):
- weak_always_swallow.diff: `except EmptyResultSet: return '', ()` unconditionally (drops the `if self.negated: raise`). Satisfies Req1 but VIOLATES Req 2.1 -> probe_4 REJECTS (non-negated empty now returns '' instead of propagating; would break query optimization / hidden non-negated behavior).
- weak_broad_except.diff: `except Exception: if negated: return '', ()` catches ALL exceptions, not just EmptyResultSet. Satisfies Req1/Req2 but VIOLATES Req 3.1 -> probe_6 REJECTS (swallows arbitrary signals when negated).

All 6 probes hold on the gold-patched tree; positive control discriminates base vs patched; two plausible weak fixes each rejected by >=1 probe. No probe-conforming alternative found that would leave hidden tests unresolved.

Env: swebench-lean conda; nl_attack probe runner in django__django-15382 official image (py3.9 testbed). Worktree used to generate diffs was cleaned up.

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
"""Req 1.3 (POSITIVE CONTROL): filter(~Exists(empty) & Q(pk=...)) returns the matching row."""
import sys, os, tempfile
import django
from django.conf import settings
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, 'probeapp'))
open(os.path.join(_d, 'probeapp', '__init__.py'), 'w').close()
with open(os.path.join(_d, 'probeapp', 'models.py'), 'w') as _f:
    _f.write("from django.db import models\n"
             "class Thing(models.Model):\n"
             "    name = models.CharField(max_length=50)\n")
sys.path.insert(0, _d)
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        DEFAULT_AUTO_FIELD='django.db.models.AutoField')
django.setup()
from django.db import connection
from probeapp.models import Thing
with connection.schema_editor() as se:
    se.create_model(Thing)
from django.db.models import Exists, Q

obj = Thing.objects.create(name='test')
qs = Thing.objects.filter(~Exists(Thing.objects.none()) & Q(pk=obj.pk))
rows = list(qs)
print("rows:", rows)
ok = rows == [obj]
print("expected exactly the matching row:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-15382: Exists.as_sql must swallow EmptyResultSet ONLY when negated (return '', ()), returning a trivially-true empty fragment so surrounding WHERE conditions survive.

### PROBES (all standalone, build a real on-disk 'probeapp' package + sqlite :memory: model, stdlib+django only):
- probe_1 (Req 1.3, POSITIVE CONTROL): Manager-style filter(~Exists(none()) & Q(pk=obj.pk)) returns exactly [obj]. HOLDS patched; FAILS at base (rows==[]). Discriminates.
- probe_2 (Req 1.1): ~Exists(none()).as_sql returns ('', ()) rather than raising EmptyResultSet. HOLDS patched; at base raises EmptyResultSet -> fail.
- probe_3 (Req 1.2): compiled SQL for filter(~Exists(none()) & Q(name='test')) still has WHERE with name=%s param. HOLDS patched; base raises EmptyResultSet during compile -> fail.
- probe_4 (Req 2.1): NON-negated Exists(none()).as_sql still raises EmptyResultSet (must NOT swallow). HOLDS on both base and patched (guard is negated-only).
- probe_5 (Req 3.2/3.3/3.4): non-empty subquery -> non-negated yields EXISTS(...), negated yields 'NOT EXISTS(...)', params identical, and ~ toggles .negated. HOLDS both.
- probe_6 (Req 3.1): a non-EmptyResultSet signal raised during subquery render (monkeypatched Subquery.as_sql -> Boom) propagates even when negated. HOLDS patched (except clause catches only EmptyResultSet); base has no try so also propagates.

Positive control (probe_1): HOLDS patched, FAILS base (prepatch_reproduced=true).

### CANDIDATE WRONG PATCHES (both apply at base_commit 770d3e6a; both REJECTED by suite => suite discriminates, no TOO-WEAK finding):
- weak_always_swallow.diff: `except EmptyResultSet: return '', ()` unconditionally (drops the `if self.negated: raise`). Satisfies Req1 but VIOLATES Req 2.1 -> probe_4 REJECTS (non-negated empty now returns '' instead of propagating; would break query optimization / hidden non-negated behavior).
- weak_broad_except.diff: `except Exception: if negated: return '', ()` catches ALL exceptions, not just EmptyResultSet. Satisfies Req1/Req2 but VIOLATES Req 3.1 -> probe_6 REJECTS (swallows arbitrary signals when negated).

All 6 probes hold on the gold-patched tree; positive control discriminates base vs patched; two plausible weak fixes each rejected by >=1 probe. No probe-conforming alternative found that would leave hidden tests unresolved.

Env: swebench-lean conda; nl_attack probe runner in django__django-15382 official image (py3.9 testbed). Worktree used to generate diffs was cleaned up.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch wraps only the super().as_sql call in try/except EmptyResultSet, returning ('', ()) iff self.negated, else re-raising. Requirements model exactly this observable behavior at the correct boundary (Exists.as_sql negated vs non-negated over empty subquery), plus the preserved end-to-end WHERE-clause behavior. Probed on gold-patched tree: WHERE preserved for negated, EmptyResultSet propagates for non-negated, negated as_sql returns ('', ()).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior and localize the change to Exists.as_sql / EmptyResultSet in expressions.py, all of which is inferable from the public problem_statement (which already gives the exact failing filter `~Exists(MyModel.objects.none()), name='test'`, the dropped-WHERE symptom, and the EmptyResultSet signal). No hidden-test artifacts are transmitted: no test function/class names (test_negated_empty_exists, ExistsTests), no file path (tests/expressions/tests.py), no fixture identifiers (Manager, pk=manager.pk), no assertion API, and no parametrization ids. Req 1.3's 'single matching row' is a generic behavioral translation of the test outcome, not a reproduction of the test's concrete setup. The closest-to-gold detail is Req 1.1's 'empty SQL string together with an empty sequence of parameters' (gold's `return '', ()`), but an empty/no-op WHERE contribution is a legitimate behavioral characterization directly implied by the public requirement to preserve the remaining WHERE conditions, and it is not observable by any test nor derived from one. Legitimate localization + behavioral translation; no test or gold reconstruction beyond the public statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
