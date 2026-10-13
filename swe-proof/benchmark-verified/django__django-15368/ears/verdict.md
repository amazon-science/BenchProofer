# P2 adversarial audit — django__django-15368

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
Weak candidate (replace `isinstance(attr, Expression)` with `isinstance(attr, F)`) resolves bare F('note') but wraps computed expressions like F('num')+1 (a CombinedExpression, not an F) in Value(...), which raises during SQL prep. probe_2 REJECTS it (VIOLATED under --patch weak.diff), confirming the suite discriminates a requirements-under-satisfying fix.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req 1.2: assigning F('note') to `misc` and bulk_update-ing
must persist the referenced column's value ('test_note'), NOT the repr 'F(note)'.
HOLDS iff reloaded misc == note value for all rows. Fails at base (stringified)."""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False)
    django.setup()

from django.db import models, connection
from django.db.models import F


class MyNote(models.Model):
    note = models.CharField(max_length=100)
    misc = models.CharField(max_length=100, null=True)

    class Meta:
        app_label = 'contenttypes'


with connection.schema_editor() as se:
    se.create_model(MyNote)

notes = [MyNote.objects.create(note='test_note', misc='test_misc') for _ in range(10)]
for n in notes:
    n.misc = F('note')
MyNote.objects.bulk_update(notes, ['misc'])

reloaded = list(MyNote.objects.values_list('misc', flat=True))
print("reloaded misc values:", reloaded)
ok = all(v == 'test_note' for v in reloaded)
print("all resolved to referenced column:", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 3.2: a COMPUTED expression (F('num') + 1) is embedded & resolved,
persisting the computed result, not a literal repr. HOLDS iff reloaded num == old+1."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
    django.setup()
from django.db import models, connection
from django.db.models import F

class MyNote(models.Model):
    num = models.IntegerField(null=True)
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(MyNote)

objs = [MyNote.objects.create(num=i) for i in range(5)]
for o in objs:
    o.num = F('num') + 1
MyNote.objects.bulk_update(objs, ['num'])
reloaded = sorted(MyNote.objects.values_list('num', flat=True))
print("reloaded num:", reloaded)
ok = reloaded == [1, 2, 3, 4, 5]
print("computed expression resolved:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.2 / 3.1 / 3.6: ordinary plain values (incl None) are persisted verbatim,
NOT resolved as expressions. Mix of string, int, None across objects.
HOLDS iff each reloaded value equals the exact assigned literal."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
    django.setup()
from django.db import models, connection

class MyNote(models.Model):
    misc = models.CharField(max_length=100, null=True)
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(MyNote)

vals = ['hello', 'world', None, 'F(note)', None]
objs = [MyNote.objects.create(misc='init') for _ in vals]
for o, v in zip(objs, vals):
    o.misc = v
MyNote.objects.bulk_update(objs, ['misc'])
reloaded = list(MyNote.objects.order_by('pk').values_list('misc', flat=True))
print("assigned:", vals)
print("reloaded:", reloaded)
ok = reloaded == vals
print("plain values (incl None and the literal string 'F(note)') stored verbatim:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.3: validation/control behavior preserved. negative batch_size raises;
empty fields raises; no objects returns 0 without querying; pk field rejected."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
    django.setup()
from django.db import models, connection

class MyNote(models.Model):
    misc = models.CharField(max_length=100, null=True)
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(MyNote)

objs = [MyNote.objects.create(misc='x') for _ in range(3)]
checks = {}

try:
    MyNote.objects.bulk_update(objs, ['misc'], batch_size=-1)
    checks['neg_batch_raises'] = False
except ValueError:
    checks['neg_batch_raises'] = True

try:
    MyNote.objects.bulk_update(objs, [])
    checks['empty_fields_raises'] = False
except ValueError:
    checks['empty_fields_raises'] = True

checks['empty_objs_returns_0'] = (MyNote.objects.bulk_update([], ['misc']) == 0)

try:
    MyNote.objects.bulk_update(objs, ['id'])
    checks['pk_field_rejected'] = False
except ValueError:
    checks['pk_field_rejected'] = True

print(checks)
ok = all(checks.values())
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.4 / 3.5: batching + custom db_column + multiple fields.
More objects than batch_size -> returns total rows across batches; a field with a
custom db_column persists correctly; multiple fields updated together per object."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
    django.setup()
from django.db import models, connection

class MyNote(models.Model):
    misc = models.CharField(max_length=100, null=True)
    col = models.CharField(max_length=100, null=True, db_column='custom_col')
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(MyNote)

objs = [MyNote.objects.create(misc='a', col='c') for _ in range(10)]
for i, o in enumerate(objs):
    o.misc = 'm%d' % i
    o.col = 'k%d' % i
# batch_size 3 across 10 objs => multiple batches
rows = MyNote.objects.bulk_update(objs, ['misc', 'col'], batch_size=3)
print("rows updated:", rows)
reloaded = list(MyNote.objects.order_by('pk').values_list('misc', 'col'))
print("reloaded:", reloaded)
expect = [('m%d' % i, 'k%d' % i) for i in range(10)]
ok = rows == 10 and reloaded == expect
print("batching+multi-field+custom-column correct:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 2.1 (structural): a bare F(...) value must be placed into the CASE
branch UNWRAPPED (not inside a Value literal). We introspect the SQL that
bulk_update would compile by capturing the query. HOLDS iff the generated UPDATE
SQL references the target column as a column expression (resolves note), i.e. it
does NOT contain the literal string 'F(note)'. Uses connection query capture."""
import django, sys
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'], USE_TZ=False)
    django.setup()
from django.db import models, connection
from django.db.models import F

class MyNote(models.Model):
    note = models.CharField(max_length=100)
    misc = models.CharField(max_length=100, null=True)
    class Meta: app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(MyNote)

objs = [MyNote.objects.create(note='n%d' % i, misc='m') for i in range(3)]
for o in objs:
    o.misc = F('note')

# capture SQL executed during bulk_update
captured = []
orig = connection.cursor
class Wrap:
    def __init__(self, c): self._c = c
    def execute(self, sql, params=None):
        captured.append((sql, params))
        return self._c.execute(sql, params)
    def __getattr__(self, n): return getattr(self._c, n)
    def __enter__(self):
        self._cm = self._c.__enter__(); return self
    def __exit__(self, *a): return self._c.__exit__(*a)
def cursor_wrap(*a, **k):
    return Wrap(orig(*a, **k))
connection.cursor = cursor_wrap
try:
    MyNote.objects.bulk_update(objs, ['misc'])
finally:
    connection.cursor = orig

update_sqls = [s for s, p in captured if s.strip().upper().startswith('UPDATE')]
print("UPDATE statements:", update_sqls)
allparams = [p for s, p in captured if s.strip().upper().startswith('UPDATE')]
print("params:", allparams)
# The stringified F would appear as a bound param 'F(note)'. Reject if so.
stringified = any(
    any(isinstance(v, str) and 'F(note)' in v for v in (p or []))
    for p in allparams)
print("F got stringified into a literal param:", stringified)
sys.exit(1 if stringified else 0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.2: assigning F('note') to `misc` and bulk_update-ing
must persist the referenced column's value ('test_note'), NOT the repr 'F(note)'.
HOLDS iff reloaded misc == note value for all rows. Fails at base (stringified)."""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False)
    django.setup()

from django.db import models, connection
from django.db.models import F


class MyNote(models.Model):
    note = models.CharField(max_length=100)
    misc = models.CharField(max_length=100, null=True)

    class Meta:
        app_label = 'contenttypes'


with connection.schema_editor() as se:
    se.create_model(MyNote)

notes = [MyNote.objects.create(note='test_note', misc='test_misc') for _ in range(10)]
for n in notes:
    n.misc = F('note')
MyNote.objects.bulk_update(notes, ['misc'])

reloaded = list(MyNote.objects.values_list('misc', flat=True))
print("reloaded misc values:", reloaded)
ok = all(v == 'test_note' for v in reloaded)
print("all resolved to referenced column:", ok)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix broadens the expression test from isinstance(attr, Expression) to hasattr(attr, 'resolve_expression'), so bare F(...) references pass through unwrapped instead of being stringified.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2): assign F('note') to misc, bulk_update, reloaded misc must equal referenced column 'test_note'. HOLDS patched; VIOLATED at base (stored 'F(note)'). Discriminates.
- probe_2 (Req 2.1/3.2): computed expression F('num')+1 embedded & resolved -> num becomes old+1. HOLDS patched; REJECTS weak.diff.
- probe_3 (Req 2.2/3.1/3.6): plain values incl None and the literal string 'F(note)' stored verbatim.
- probe_4 (Req 3.3): validation preserved — negative batch_size raises, empty fields raises, empty objs returns 0, pk field rejected.
- probe_5 (Req 3.4/3.5): batching (batch_size=3 over 10 objs returns 10), multiple fields, custom db_column persist correctly.
- probe_6 (Req 1.3/2.1 structural): captured UPDATE SQL/params show F is NOT bound as a stringified literal param; column is referenced as a column expression.

All 6 probes completed and hold on the patched tree; positive control fails at base; the plausible weak fix is rejected by probe_2. No violation or too-weak finding.

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
Weak candidate (replace `isinstance(attr, Expression)` with `isinstance(attr, F)`) resolves bare F('note') but wraps computed expressions like F('num')+1 (a CombinedExpression, not an F) in Value(...), which raises during SQL prep. probe_2 REJECTS it (VIOLATED under --patch weak.diff), confirming the suite discriminates a requirements-under-satisfying fix.
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
"""Positive control / Req 1.2: assigning F('note') to `misc` and bulk_update-ing
must persist the referenced column's value ('test_note'), NOT the repr 'F(note)'.
HOLDS iff reloaded misc == note value for all rows. Fails at base (stringified)."""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False)
    django.setup()

from django.db import models, connection
from django.db.models import F


class MyNote(models.Model):
    note = models.CharField(max_length=100)
    misc = models.CharField(max_length=100, null=True)

    class Meta:
        app_label = 'contenttypes'


with connection.schema_editor() as se:
    se.create_model(MyNote)

notes = [MyNote.objects.create(note='test_note', misc='test_misc') for _ in range(10)]
for n in notes:
    n.misc = F('note')
MyNote.objects.bulk_update(notes, ['misc'])

reloaded = list(MyNote.objects.values_list('misc', flat=True))
print("reloaded misc values:", reloaded)
ok = all(v == 'test_note' for v in reloaded)
print("all resolved to referenced column:", ok)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix broadens the expression test from isinstance(attr, Expression) to hasattr(attr, 'resolve_expression'), so bare F(...) references pass through unwrapped instead of being stringified.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.1/1.2): assign F('note') to misc, bulk_update, reloaded misc must equal referenced column 'test_note'. HOLDS patched; VIOLATED at base (stored 'F(note)'). Discriminates.
- probe_2 (Req 2.1/3.2): computed expression F('num')+1 embedded & resolved -> num becomes old+1. HOLDS patched; REJECTS weak.diff.
- probe_3 (Req 2.2/3.1/3.6): plain values incl None and the literal string 'F(note)' stored verbatim.
- probe_4 (Req 3.3): validation preserved — negative batch_size raises, empty fields raises, empty objs returns 0, pk field rejected.
- probe_5 (Req 3.4/3.5): batching (batch_size=3 over 10 objs returns 10), multiple fields, custom db_column persist correctly.
- probe_6 (Req 1.3/2.1 structural): captured UPDATE SQL/params show F is NOT bound as a stringified literal param; column is referenced as a column expression.

All 6 probes completed and hold on the patched tree; positive control fails at base; the plausible weak fix is rejected by probe_2. No violation or too-weak finding.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Req 1 (F resolves to referenced column, not stringified repr) and Req 2 (duck-typed resolve_expression recognition, wrap non-expressions in Value) match the diff precisely, including the correct modeling boundary — the changed detection predicate, not one branch/helper. Req 3 (preserve validation/batching/None/custom-pk behavior) is consistent with a one-line detection-only change that touches nothing else. Requirements are faithful.

Counterexample / evidence:

```
None found. Base probe: c8=='F(name)'; patched probe: c8=='hello' (rows=1).
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to bulk_update() in django/db/models/query.py and translates the fix into behavioral requirements. Everything load-bearing is already public in problem_statement: the plain F('...') bug, the 'F(name)' stringification, the CASE/WHEN construction, Value wrapping, and even the exact fix — duck-typing on hasattr(attr,'resolve_expression'). The requirements paraphrase 'exposes the expression-resolution behavior common to expression values' straight from that public hint. The hidden FAIL_TO_PASS (test_f_expression) uses the Note model, misc=F('note'), filter misc='test_note'; NONE of these identifiers (Note, misc, note, test_note, the test function name/path) appear in the document — the F-expression behavior is stated abstractly. Requirement 3's enumeration (boolean/datetime/IP/JSON values, negative batch size, empty field list, pk-set requirement, concrete-non-m2m fields, custom db columns, inherited/custom pk, None values, batching) does map fairly closely onto the PASS_TO_PASS regression suite, which is the only test-shaped area. However these are generic, well-documented bulk_update behaviors described as 'preserve existing behavior' — no test names, parametrization ids, quoted test/gold code, or fix-invented identifiers are transmitted, and the enumeration does not reveal the actual FAIL_TO_PASS scenario. Borderline on the regression enumeration but stays on the legitimate behavior-translation side of the line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
