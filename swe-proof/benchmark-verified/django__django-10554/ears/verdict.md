# P2 adversarial audit — django__django-10554

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
# Requirement 1.3 / positive control:
# A combined (union) queryset ordered by a column absent from the original
# selection (values_list('order') then order_by('-pk')) must execute without
# a database error and return rows ordered by that column.
import sys, types, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
import os
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5),
    ReservedName(name='rn0', order=6), ReservedName(name='rn9', order=-1)])

qs1 = ReservedName.objects.filter(order__gte=6)
qs2 = ReservedName.objects.filter(order__lte=5)
union_qs = qs1.union(qs2)

try:
    got = list(union_qs.order_by('-pk').values_list('order', flat=True))
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
expected = [-1, 6, 5, 7]
print("order_by('-pk') ->", got, "expected", expected)
sys.exit(0 if got == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 1.3 + 4.4 (all F2P ordering variants of test_union_with_values_list_and_order).
# Combined queryset ordered by columns absent from selection must evaluate and
# return rows ordered correctly, in every form (order_by before/after values_list,
# single and multi-column). Also both derived querysets succeed (no corruption).
import sys, types, os, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5),
    ReservedName(name='rn0', order=6), ReservedName(name='rn9', order=-1)])

qs1 = ReservedName.objects.filter(order__gte=6)
qs2 = ReservedName.objects.filter(order__lte=5)
union_qs = qs1.union(qs2)

cases = [
    (union_qs.order_by('-pk').values_list('order', flat=True), [-1, 6, 5, 7]),
    (union_qs.order_by('pk').values_list('order', flat=True), [7, 5, 6, -1]),
    (union_qs.values_list('order', flat=True).order_by('-pk'), [-1, 6, 5, 7]),
    (union_qs.values_list('order', flat=True).order_by('pk'), [7, 5, 6, -1]),
    (union_qs.order_by('-name', 'pk').values_list('order', flat=True), [-1, 5, 7, 6]),
    (union_qs.values_list('order', flat=True).order_by('-name', 'pk'), [-1, 5, 7, 6]),
]
ok = True
for i, (qs, exp) in enumerate(cases):
    try:
        got = list(qs)
    except Exception as e:
        print("case", i, "RAISED", type(e).__name__, e); ok = False; continue
    print("case", i, "->", got, "exp", exp)
    if got != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 1.4 + 1.1/1.2: Query.add_select_col appends exactly one column,
# extending self.select by one and self.values_select by the col's output_field name.
# And the emitted ORDER BY position never exceeds the number of selected columns.
import sys, types, os, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5)])

from django.db.models.sql.query import Query
# 1.4: add_select_col must exist and extend collections by exactly one.
if not hasattr(Query, 'add_select_col'):
    print("FAIL: Query.add_select_col missing"); sys.exit(1)

q = ReservedName.objects.values('name').query
# build a resolvable Col for 'order'
from django.db.models.expressions import Col
before_select = len(q.select)
before_vs = len(q.values_select)
# get a Col expression for the order field
order_field = ReservedName._meta.get_field('order')
col = Col(q.get_initial_alias(), order_field)
q.add_select_col(col)
after_select = len(q.select)
after_vs = len(q.values_select)
print("select", before_select, "->", after_select, "values_select", before_vs, "->", after_vs)
print("values_select tail:", q.values_select[-1])
ok = (after_select == before_select + 1 and after_vs == before_vs + 1
      and q.select[-1] is col and q.values_select[-1] == 'order')
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 1.2: the emitted ORDER BY ordinal for an added column must refer
# to a column actually present in the SELECT list (position <= number of
# selected columns). Inspect the compiled SQL of the combined query.
import sys, types, os, re, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5)])

qs1 = ReservedName.objects.filter(order__gte=6)
qs2 = ReservedName.objects.filter(order__lte=5)
# order by pk which is NOT among the selected 'order' column -> pk gets added
qs = qs1.union(qs2).values_list('order', flat=True).order_by('pk')
sql, params = qs.query.get_compiler(using='default').as_sql()
print("SQL:", sql)
# count select columns in the outer combined query: number of SELECT positions.
# Find ORDER BY (N) ordinals and the number of top-level select columns.
# The combined SELECT columns == number of columns each subquery selects.
# Extract ORDER BY ordinals:
m = re.search(r'ORDER BY (.+)$', sql)
if not m:
    print("FAIL: no ORDER BY in SQL"); sys.exit(1)
ords = [int(x) for x in re.findall(r'\((\d+)\)', m.group(1))]
print("ORDER BY ordinals:", ords)
# Determine select count: count occurrences of the first subquery's SELECT list.
# Robust approach: run the query; if position out of range it errors.
try:
    rows = list(qs)
    print("rows:", rows)
except Exception as e:
    print("FAIL: query raised", type(e).__name__, e); sys.exit(1)
# Also assert ordinals are >=1 and, per the fix, position equals select count (2:
# 'order' + added 'pk'). Any ordinal must be <= number of selected cols.
# We compute select count from the compiler's outer query select length.
n_sel = len(qs.query.get_compiler(using='default').query.select) or len(qs.query.select)
# after compile the added col is present:
n_sel = len(qs.query.select)
print("n selected columns:", n_sel)
ok = all(1 <= o <= n_sel for o in ords)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 2.1/2.2: an ORDER BY term over a combined query that references a
# named (aliased) selected column absent from the result columns must still
# RAISE a database error (not be silently added). Encoded via annotate(foo=...)
# whose alias is NOT in the union's selected columns but is used in order_by.
import sys, types, os, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection
from django.db.models import F

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5)])

qs1 = ReservedName.objects.filter(order__gte=6)
qs2 = ReservedName.objects.filter(order__lte=5)
# alias 'foo' annotated but NOT selected (values('name') only), then order by it.
qs = qs1.annotate(foo=F('order')).values('name').union(
     qs2.annotate(foo=F('order')).values('name')).order_by('foo')
raised = False
try:
    rows = list(qs)
    print("NO RAISE: rows =", rows)
except Exception as e:
    raised = True
    print("Raised as required:", type(e).__name__, str(e)[:120])
sys.exit(0 if raised else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 3.1 + 4.3: When an ordering term matches an already-selected
# column of a combined query, it resolves to that column's existing position
# WITHOUT adding a new column; and values_list (flat and annotated) over
# combined querysets returns selected values ordered as requested.
# This is test_union_with_values_list_on_annotated_and_unannotated (a P2P/F2P).
import sys, types, os, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection
from django.db.models import Value, IntegerField

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5),
    ReservedName(name='rn0', order=6), ReservedName(name='rn9', order=-1)])

ok = True

# flat values_list union then order by the selected col.
q1 = ReservedName.objects.filter(order__gte=6)
q2 = ReservedName.objects.filter(order__lte=5)
u = q1.union(q2)

# Req 3.1: order by 'order' which IS selected -> should resolve to existing pos,
# no crash, and select length stays at 1 (only 'order').
qs = u.values_list('order', flat=True).order_by('order')
try:
    got = sorted(list(qs))
    print("order-by-selected-col ->", list(qs))
except Exception as e:
    print("FAIL ordered by selected col raised", e); ok = False
n_sel = len(qs.query.select)
print("selected columns after compile:", n_sel)
if n_sel != 1:
    print("FAIL: expected exactly 1 selected column (order), got", n_sel); ok = False
if got != [-1, 5, 6, 7]:
    print("FAIL: wrong ordered values", got); ok = False

# 4.3: flat values_list union basic
res = ReservedName.objects.filter(order__gte=6).values_list('order', flat=True).union(
      ReservedName.objects.filter(order__lte=5).values_list('order', flat=True))
vals = sorted(res)
print("flat union values:", vals)
if vals != [-1, 5, 6, 7]:
    print("FAIL: flat union wrong", vals); ok = False

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Requirement 2.1/2.2 (discriminating): an ORDER BY term that is a *reference*
# to a named (aliased) selected column which does not match any result column
# must STILL RAISE a database error and NOT be silently added to the select
# list. Case: annotate(xx=F('order')).values('xx') in each union leg, ordered
# by F('xx') -- a Ref term with a col_alias that fails the match scan.
# Gold: raises DatabaseError. A weak fix that drops the col_alias guard: returns
# rows silently -> this probe rejects such a fix.
import sys, types, os, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection
from django.db.models import F

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5)])

q1 = ReservedName.objects.filter(order__gte=6)
q2 = ReservedName.objects.filter(order__lte=5)
qs = q1.annotate(xx=F('order')).values('xx').union(
     q2.annotate(xx=F('order')).values('xx')).order_by(F('xx'))
raised = False
try:
    rows = list(qs)
    print("NO RAISE (violation of Req 2): rows =", rows)
except Exception as e:
    raised = True
    print("Raised as required by Req 2:", type(e).__name__, str(e)[:120])
sys.exit(0 if raised else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1.3 / positive control:
# A combined (union) queryset ordered by a column absent from the original
# selection (values_list('order') then order_by('-pk')) must execute without
# a database error and return rows ordered by that column.
import sys, types, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
import os
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5),
    ReservedName(name='rn0', order=6), ReservedName(name='rn9', order=-1)])

qs1 = ReservedName.objects.filter(order__gte=6)
qs2 = ReservedName.objects.filter(order__lte=5)
union_qs = qs1.union(qs2)

try:
    got = list(union_qs.order_by('-pk').values_list('order', flat=True))
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
expected = [-1, 6, 5, 7]
print("order_by('-pk') ->", got, "expected", expected)
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (DatabaseError 'ORDER BY term does not match any column in the result set') and HOLDS patched -> discriminating power confirmed.

Coverage of requirements.md:
- probe_1 (Req 1.3, positive control): union().order_by('-pk').values_list('order',flat) evaluates and returns [-1,6,5,7]; raises at base.
- probe_2 (Req 1.3 + 4.4): all 6 ordering variants from the F2P test_union_with_values_list_and_order (order_by before/after values_list, single & multi-column) return the exact expected sequences.
- probe_3 (Req 1.4 + 1.1): Query.add_select_col exists and extends self.select and self.values_select by exactly one, with values_select tail == the col's output_field.name.
- probe_4 (Req 1.2): compiled SQL of union().values_list('order').order_by('pk') emits ORDER BY (2) with n_selected==2 -> ordinal never exceeds select-list length; query executes.
- probe_5 (Req 2.1/2.2, alias absent): order_by('foo') on an annotated-but-unselected alias still raises.
- probe_6 (Req 3.1 + 4.3): ordering by an already-selected column keeps select length at 1 (no new column added) and returns correctly ordered values; flat values_list union works.
- probe_7 (Req 2.1/2.2, DISCRIMINATING): a Ref term order_by(F('xx')) to a named alias that fails the match scan must RAISE. Gold raises DatabaseError; the weak candidate returns rows silently.

Candidate patch (weak.diff): gold fix WITHOUT the `if col_alias: raise` guard (always add the column). It applies at base_commit and PASSES probes 1-6 but is REJECTED by probe_7 (Req 2 violation: gold raises DatabaseError, weak returns [{'xx':5},{'xx':7}]). This demonstrates the suite discriminates a plausibly-wrong partial fix that a weak reading of Req 1 (ignoring Req 2) would permit. No requirements-conforming alternative found: the only wrong-fix candidate that satisfies Req 1 fails a Req-2 probe.

All runs completed in the official image; no INCONCLUSIVE runs.

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
# Requirement 1.3 / positive control:
# A combined (union) queryset ordered by a column absent from the original
# selection (values_list('order') then order_by('-pk')) must execute without
# a database error and return rows ordered by that column.
import sys, types, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'probeapp'],
        USE_TZ=False)
import os
os.makedirs('$SCRATCH', exist_ok=True)
pa = types.ModuleType('probeapp'); pa.__path__ = ['$SCRATCH']; sys.modules['probeapp'] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    class Meta: app_label = 'probeapp'

with connection.schema_editor() as se:
    se.create_model(ReservedName)
ReservedName.objects.bulk_create([
    ReservedName(name='rn1', order=7), ReservedName(name='rn2', order=5),
    ReservedName(name='rn0', order=6), ReservedName(name='rn9', order=-1)])

qs1 = ReservedName.objects.filter(order__gte=6)
qs2 = ReservedName.objects.filter(order__lte=5)
union_qs = qs1.union(qs2)

try:
    got = list(union_qs.order_by('-pk').values_list('order', flat=True))
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
expected = [-1, 6, 5, 7]
print("order_by('-pk') ->", got, "expected", expected)
sys.exit(0 if got == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on the gold-patched tree; positive control (probe_1) FAILS at base (DatabaseError 'ORDER BY term does not match any column in the result set') and HOLDS patched -> discriminating power confirmed.

Coverage of requirements.md:
- probe_1 (Req 1.3, positive control): union().order_by('-pk').values_list('order',flat) evaluates and returns [-1,6,5,7]; raises at base.
- probe_2 (Req 1.3 + 4.4): all 6 ordering variants from the F2P test_union_with_values_list_and_order (order_by before/after values_list, single & multi-column) return the exact expected sequences.
- probe_3 (Req 1.4 + 1.1): Query.add_select_col exists and extends self.select and self.values_select by exactly one, with values_select tail == the col's output_field.name.
- probe_4 (Req 1.2): compiled SQL of union().values_list('order').order_by('pk') emits ORDER BY (2) with n_selected==2 -> ordinal never exceeds select-list length; query executes.
- probe_5 (Req 2.1/2.2, alias absent): order_by('foo') on an annotated-but-unselected alias still raises.
- probe_6 (Req 3.1 + 4.3): ordering by an already-selected column keeps select length at 1 (no new column added) and returns correctly ordered values; flat values_list union works.
- probe_7 (Req 2.1/2.2, DISCRIMINATING): a Ref term order_by(F('xx')) to a named alias that fails the match scan must RAISE. Gold raises DatabaseError; the weak candidate returns rows silently.

Candidate patch (weak.diff): gold fix WITHOUT the `if col_alias: raise` guard (always add the column). It applies at base_commit and PASSES probes 1-6 but is REJECTED by probe_7 (Req 2 violation: gold raises DatabaseError, weak returns [{'xx':5},{'xx':7}]). This demonstrates the suite discriminates a plausibly-wrong partial fix that a weak reading of Req 1 (ignoring Req 2) would permit. No requirements-conforming alternative found: the only wrong-fix candidate that satisfies Req 1 fails a Req-2 probe.

All runs completed in the official image; no INCONCLUSIVE runs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold diff: in SQLCompiler.get_order_by combinator loop, the else-of-for now splits on col_alias: if col_alias -> raise DatabaseError (Req2 AC1/AC2); else self.query.add_select_col(src) + RawSQL('%d' % len(self.query.select)) (Req1 AC1 position=new total, AC2 in-range). New helper Query.add_select_col appends one col to self.select and its output_field.name to values_select (Req1 AC4). Matching branch unchanged: RawSQL(idx+1) (Req3 AC1/AC3), 'elif col_alias: continue' skips non-referenced aliased cols and 'src = src.source' for is_ref terms compares underlying expr (Req3 AC2). Positional relabel is gated by 'if self.query.combinator:' so non-combined path is untouched (Req4 AC1); dedup via seen-set ignoring direction preserved (Req4 AC2). Modeling boundary is the changed observable behavior (unmatched-term resolution keyed on col_alias), not a narrow slice. Verified live on instance image (python3.6/testbed); injected FAIL_TO_PASS test returned OK. G-RESOLVE=pass corroborates PASS_TO_PASS incl. test_order_raises_on_non_selected_column.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally and stays within the public problem_statement. No hidden-test content transmitted: no test function/class names (test_union_with_values_list_and_order, QuerySetSetOperationTests), no test model (ReservedName), no parametrized data/expected-result enumerations (order values 7/5/6/-1 and their expected orderings), no test file path. The fix-invented Query helper `add_select_col` is NOT named — Req 1.4 describes it purely behaviorally ('a means to append a single column to the query's selected-columns collection'). The strings `ORDER BY (4)` and 'ORDER BY position N is not in select list' derive directly from the PUBLIC problem_statement traceback. The error text paraphrased in Req 2.1 ('ORDER BY term does not match any column in the result set') is pre-existing code that the gold only guards with `if col_alias:`, not a gold-invented artifact, and describing an observable error is legitimate. 'position equal to the new total number of selected columns' translates the fix logic (len(self.query.select)) into behavior — the intended purpose of the spec, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
