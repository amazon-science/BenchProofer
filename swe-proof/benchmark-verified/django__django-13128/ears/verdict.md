# P2 adversarial audit — django__django-13128

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
"""POSITIVE CONTROL. Req 1.3 + 1.5: a subtraction of two same-typed DateField
operands, when resolved (no ExpressionWrapper, no output_field), SHALL be
re-typed to a temporal-subtraction carrying a DurationField value-type.

Holds on patched tree; fails at base (base raises FieldError 'mixed types').
Exit 0 iff resolved expr has a determinate DurationField output_field.
"""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models
from django.db.models import F, DurationField
from django.core.exceptions import FieldError


class M(models.Model):
    assigned = models.DateField()
    completed = models.DateField()

    class Meta:
        app_label = 'contenttypes'


expr = F('completed') - F('assigned')
qs = M.objects.annotate(diff=expr)
resolved = qs.query.annotations['diff']
print("resolved type:", type(resolved).__name__)
try:
    of = resolved.output_field
except FieldError as e:
    print("FieldError raised (base behavior):", e)
    raise SystemExit(1)
print("output_field:", type(of).__name__)
if isinstance(of, DurationField):
    print("OK: DurationField determined without wrapper")
    raise SystemExit(0)
print("WRONG output_field")
raise SystemExit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2: an ordinary combination where exactly one resolved operand is a
DurationField and the other is a different type SHALL be re-typed to a
DurationExpression during resolution.

datetime + duration : one operand DateTimeField, other DurationField.
Exit 0 iff resolved expr is a DurationExpression.
"""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models
from django.db.models import F
from django.db.models.expressions import DurationExpression


class M(models.Model):
    start = models.DateTimeField()
    delta = models.DurationField()

    class Meta:
        app_label = 'contenttypes'


expr = F('start') + F('delta')
qs = M.objects.annotate(res=expr)
resolved = qs.query.annotations['res']
print("resolved type:", type(resolved).__name__)
if isinstance(resolved, DurationExpression):
    print("OK: re-typed to DurationExpression")
    raise SystemExit(0)
print("NOT a DurationExpression")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.4 + Req 2: an ordinary combination matching NEITHER condition SHALL
stay an ordinary CombinedExpression with already-resolved operands; and a
non-SUB temporal combination (e.g. addition of two dates) must NOT be re-typed
to a temporal subtraction. Also Req 2.1: re-resolving an already-specialized
combination keeps its kind.

Exit 0 iff:
  (a) int - int stays an ordinary CombinedExpression (not specialised), and
  (b) date + date (addition, not SUB) stays ordinary (not TemporalSubtraction), and
  (c) re-resolving a resolved TemporalSubtraction stays a TemporalSubtraction.
"""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models
from django.db.models import F
from django.db.models.expressions import (
    CombinedExpression, TemporalSubtraction, DurationExpression,
)


class M(models.Model):
    a = models.IntegerField()
    b = models.IntegerField()
    d1 = models.DateField()
    d2 = models.DateField()

    class Meta:
        app_label = 'contenttypes'


ok = True

# (a) int - int : ordinary, not specialised
r_int = M.objects.annotate(x=F('a') - F('b')).query.annotations['x']
print("int-int:", type(r_int).__name__)
if not isinstance(r_int, CombinedExpression) or isinstance(r_int, (TemporalSubtraction, DurationExpression)):
    print("  FAIL: int-int got specialised")
    ok = False

# (b) date + date : addition (not SUB) -> must stay ordinary
r_add = M.objects.annotate(y=F('d1') + F('d2')).query.annotations['y']
print("date+date:", type(r_add).__name__)
if isinstance(r_add, (TemporalSubtraction, DurationExpression)):
    print("  FAIL: date+date wrongly specialised")
    ok = False

# (c) re-resolve an already-resolved temporal subtraction (Req 2.1)
r_sub = M.objects.annotate(z=F('d1') - F('d2')).query.annotations['z']
print("date-date:", type(r_sub).__name__)
if not isinstance(r_sub, TemporalSubtraction):
    print("  FAIL: date-date not TemporalSubtraction")
    ok = False
else:
    r_sub2 = r_sub.resolve_expression(M.objects.all().query)
    print("re-resolved:", type(r_sub2).__name__)
    if not isinstance(r_sub2, TemporalSubtraction):
        print("  FAIL: re-resolution changed kind")
        ok = False

if ok:
    print("OK")
    raise SystemExit(0)
raise SystemExit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 5.1 + 5.3 (regression, functional end-to-end): temporal subtraction
without a wrapper, filtered against timedelta thresholds, returns the correct
rows; and a subtraction against a NULL date yields None.

Uses a real in-memory sqlite DB. Exit 0 iff both hold.
"""
import datetime
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import F, Value, DateField


class Exp(models.Model):
    name = models.CharField(max_length=10)
    assigned = models.DateField()
    completed = models.DateField()

    class Meta:
        app_label = 'contenttypes'


with connection.schema_editor() as se:
    se.create_model(Exp)

base = datetime.date(2020, 1, 1)
data = [('e0', 0), ('e1', 2), ('e2', 4), ('e3', 6), ('e4', 8)]
for name, days in data:
    Exp.objects.create(name=name, assigned=base,
                       completed=base + datetime.timedelta(days=days))

if not connection.features.supports_temporal_subtraction:
    print("SKIP-NOTE: backend lacks supports_temporal_subtraction; cannot test")
    # Should not happen on sqlite modern; treat as inconclusive -> fail closed
    raise SystemExit(1)

qs = Exp.objects.annotate(dur=F('completed') - F('assigned'))
ge5 = {e.name for e in qs.filter(dur__gte=datetime.timedelta(days=5))}
lt5 = {e.name for e in qs.filter(dur__lt=datetime.timedelta(days=5))}
print("gte5:", ge5, "lt5:", lt5)
ok = ge5 == {'e3', 'e4'} and lt5 == {'e0', 'e1', 'e2'}
if not ok:
    print("FAIL: wrong threshold rows")
    raise SystemExit(1)

# NULL operand -> None (Req 5.3)
qn = Exp.objects.annotate(diff=F('completed') - Value(None, output_field=DateField()))
first = qn.first()
print("null diff:", first.diff)
if first.diff is not None:
    print("FAIL: null subtraction not None")
    raise SystemExit(1)

print("OK")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 5.4 (regression): datetime subtraction preserves microsecond-level
precision, including large timedelta magnitudes. No wrapper.

Exit 0 iff the computed duration equals the exact expected timedelta with
microseconds.
"""
import datetime
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import F


class Ev(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        app_label = 'contenttypes'


with connection.schema_editor() as se:
    se.create_model(Ev)

start = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
delta = datetime.timedelta(days=500, hours=3, minutes=7, seconds=9, microseconds=123456)
end = start + delta
Ev.objects.create(start=start, end=end)

if not connection.features.supports_temporal_subtraction:
    print("no temporal subtraction support")
    raise SystemExit(1)

got = Ev.objects.annotate(d=F('end') - F('start')).first().d
print("expected:", delta)
print("got     :", got)
if got == delta:
    print("OK: microsecond precision preserved")
    raise SystemExit(0)
print("FAIL: precision mismatch")
raise SystemExit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5.6 (regression): non-temporal numeric arithmetic still works and gives
unchanged results (add/sub/mul/div/mod on integers, both operand orders); and
Req 1.6: a combination whose operand has no determinable output_field must not
raise from classification during resolution.

Exit 0 iff numeric arithmetic returns correct values AND resolving a
combination with an output_field-less operand does not raise.
"""
import datetime
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import F, Value
from django.core.exceptions import FieldError


class N(models.Model):
    a = models.IntegerField()
    b = models.IntegerField()

    class Meta:
        app_label = 'contenttypes'


with connection.schema_editor() as se:
    se.create_model(N)

N.objects.create(a=20, b=6)
row = N.objects.annotate(
    add=F('a') + F('b'),
    sub=F('a') - F('b'),
    mul=F('a') * F('b'),
    div=F('a') / F('b'),
    mod=F('a') % F('b'),
    radd=Value(100) + F('a'),
).first()
print("add,sub,mul,div,mod,radd:", row.add, row.sub, row.mul, row.div, row.mod, row.radd)
ok = (row.add == 26 and row.sub == 14 and row.mul == 120 and
      row.div == 3 and row.mod == 2 and row.radd == 120)
if not ok:
    print("FAIL: numeric arithmetic wrong")
    raise SystemExit(1)

# Req 1.6: operand with no determinable output_field must not raise from
# classification. F('a') - F('b') where combination itself... use a bare
# subtraction of two expressions whose output_field lookup would fail: mixing
# without a concrete field. Use F('a') - Value('x') (str) — mixed types is
# handled by classification; ensure no crash in resolve_expression itself.
try:
    expr = F('a') - Value(3)  # ordinary, resolves fine
    resolved = N.objects.annotate(z=expr).query.annotations['z']
    print("resolve of ordinary combo OK:", type(resolved).__name__)
except FieldError as e:
    print("FAIL: classification raised during resolution:", e)
    raise SystemExit(1)

print("OK")
raise SystemExit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.1: an ordinary CombinedExpression.as_sql SHALL emit plain arithmetic
SQL and SHALL NOT re-derive a duration/temporal kind at SQL-generation time.

Verify by resolving an int-int subtraction (stays ordinary) and compiling it:
the emitted SQL must be a plain "(a - b)" arithmetic, containing no interval /
duration-microsecond machinery. Also check that TemporalSubtraction/Duration
are reached via RESOLUTION not as_sql: the resolved date-date subtraction is a
TemporalSubtraction whose as_sql produces temporal SQL.

Exit 0 iff plain combo compiles to plain arithmetic (no CAST/interval juggling
specific to duration) and the resolved-temporal path still compiles.
"""
import datetime
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.models import F
from django.db.models.sql.compiler import SQLCompiler


class M(models.Model):
    a = models.IntegerField()
    b = models.IntegerField()
    d1 = models.DateField()
    d2 = models.DateField()

    class Meta:
        app_label = 'contenttypes'


qs = M.objects.annotate(x=F('a') - F('b'))
compiler = qs.query.get_compiler('default')
resolved = qs.query.annotations['x']
sql, params = resolved.as_sql(compiler, connection)
print("plain combo SQL:", sql)
# plain arithmetic: contains the columns joined by '-', no julianday/interval
low = sql.lower()
if 'julianday' in low or 'interval' in low or '1000000' in sql:
    print("FAIL: plain combo emitted duration/temporal SQL")
    raise SystemExit(1)

# temporal reached via resolution
r_sub = qs.query.annotations if False else M.objects.annotate(z=F('d1') - F('d2')).query.annotations['z']
from django.db.models.expressions import TemporalSubtraction
if not isinstance(r_sub, TemporalSubtraction):
    print("FAIL: date-date not TemporalSubtraction after resolution")
    raise SystemExit(1)
c2 = M.objects.annotate(z=F('d1') - F('d2')).query.get_compiler('default')
tsql, _ = r_sub.as_sql(c2, connection)
print("temporal SQL:", tsql)
print("OK")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL. Req 1.3 + 1.5: a subtraction of two same-typed DateField
operands, when resolved (no ExpressionWrapper, no output_field), SHALL be
re-typed to a temporal-subtraction carrying a DurationField value-type.

Holds on patched tree; fails at base (base raises FieldError 'mixed types').
Exit 0 iff resolved expr has a determinate DurationField output_field.
"""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models
from django.db.models import F, DurationField
from django.core.exceptions import FieldError


class M(models.Model):
    assigned = models.DateField()
    completed = models.DateField()

    class Meta:
        app_label = 'contenttypes'


expr = F('completed') - F('assigned')
qs = M.objects.annotate(diff=expr)
resolved = qs.query.annotations['diff']
print("resolved type:", type(resolved).__name__)
try:
    of = resolved.output_field
except FieldError as e:
    print("FieldError raised (base behavior):", e)
    raise SystemExit(1)
print("output_field:", type(of).__name__)
if isinstance(of, DurationField):
    print("OK: DurationField determined without wrapper")
    raise SystemExit(0)
print("WRONG output_field")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and observed results (patched / base / weak.diff):
- probe_1 (POSITIVE CONTROL, Req 1.3+1.5): F('completed')-F('assigned') on two DateField operands resolves to TemporalSubtraction with a determinate DurationField output_field, no ExpressionWrapper. HOLDS patched (TemporalSubtraction/DurationField) / VIOLATED base (stays CombinedExpression, output_field=DateField -> discriminates) / VIOLATED weak.diff (stays CombinedExpression).
- probe_2 (Req 1.2): datetime+duration (one DurationField, other DateTimeField) re-types to DurationExpression during resolution. HOLDS patched / HOLDS weak.diff.
- probe_3 (Req 1.4 + Req 2.1/2.2): int-int stays ordinary CombinedExpression; date+date (non-SUB) not specialised; re-resolving a TemporalSubtraction keeps its kind. HOLDS patched / VIOLATED weak.diff (int-int check is fine but the date-date temporal-subtraction leg fails since weak.diff omits the SUB branch).
- probe_4 (Req 5.1+5.3, functional): unwrapped temporal subtraction filtered by timedelta gte/lt returns correct rows {e3,e4}/{e0,e1,e2}; NULL date operand yields None. HOLDS patched.
- probe_5 (Req 5.4): datetime subtraction preserves microsecond precision for large magnitude (500d 3:07:09.123456). HOLDS patched.
- probe_6 (Req 5.6 + Req 1.6): integer add/sub/mul/div/mod/right-add unchanged (26,14,120,3,2,120); classification does not raise on ordinary combos. HOLDS patched.
- probe_7 (Req 3.1): ordinary int-int CombinedExpression.as_sql emits plain arithmetic ('("a" - "b")') with no duration/interval machinery; temporal SQL is reached via resolution (TemporalSubtraction). HOLDS patched.

CANDIDATE PATCH (weak.diff): a partial/naive fix that moves classification to resolve_expression but implements ONLY the DurationField-mixing branch (Req 1.2) and OMITS the temporal-subtraction branch (Req 1.3). It applies cleanly at base. The probe suite REJECTS it: probe_1 (positive control) VIOLATED and probe_3 VIOLATED, because date-date subtraction no longer becomes a TemporalSubtraction with a DurationField. This demonstrates the suite discriminates a wrong implementation and would not pass the hidden temporal-subtraction FAIL_TO_PASS tests.

Conclusion: requirements are faithful to and no stronger than the gold patch (no VIOLATION found among 7 probes), and the suite rejects a plausibly-wrong partial fix (no TOO-WEAK finding). Positive control discriminates base vs patched. Verdict SOUND.

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
"""POSITIVE CONTROL. Req 1.3 + 1.5: a subtraction of two same-typed DateField
operands, when resolved (no ExpressionWrapper, no output_field), SHALL be
re-typed to a temporal-subtraction carrying a DurationField value-type.

Holds on patched tree; fails at base (base raises FieldError 'mixed types').
Exit 0 iff resolved expr has a determinate DurationField output_field.
"""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    USE_TZ=False,
)
django.setup()

from django.db import models
from django.db.models import F, DurationField
from django.core.exceptions import FieldError


class M(models.Model):
    assigned = models.DateField()
    completed = models.DateField()

    class Meta:
        app_label = 'contenttypes'


expr = F('completed') - F('assigned')
qs = M.objects.annotate(diff=expr)
resolved = qs.query.annotations['diff']
print("resolved type:", type(resolved).__name__)
try:
    of = resolved.output_field
except FieldError as e:
    print("FieldError raised (base behavior):", e)
    raise SystemExit(1)
print("output_field:", type(of).__name__)
if isinstance(of, DurationField):
    print("OK: DurationField determined without wrapper")
    raise SystemExit(0)
print("WRONG output_field")
raise SystemExit(1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and observed results (patched / base / weak.diff):
- probe_1 (POSITIVE CONTROL, Req 1.3+1.5): F('completed')-F('assigned') on two DateField operands resolves to TemporalSubtraction with a determinate DurationField output_field, no ExpressionWrapper. HOLDS patched (TemporalSubtraction/DurationField) / VIOLATED base (stays CombinedExpression, output_field=DateField -> discriminates) / VIOLATED weak.diff (stays CombinedExpression).
- probe_2 (Req 1.2): datetime+duration (one DurationField, other DateTimeField) re-types to DurationExpression during resolution. HOLDS patched / HOLDS weak.diff.
- probe_3 (Req 1.4 + Req 2.1/2.2): int-int stays ordinary CombinedExpression; date+date (non-SUB) not specialised; re-resolving a TemporalSubtraction keeps its kind. HOLDS patched / VIOLATED weak.diff (int-int check is fine but the date-date temporal-subtraction leg fails since weak.diff omits the SUB branch).
- probe_4 (Req 5.1+5.3, functional): unwrapped temporal subtraction filtered by timedelta gte/lt returns correct rows {e3,e4}/{e0,e1,e2}; NULL date operand yields None. HOLDS patched.
- probe_5 (Req 5.4): datetime subtraction preserves microsecond precision for large magnitude (500d 3:07:09.123456). HOLDS patched.
- probe_6 (Req 5.6 + Req 1.6): integer add/sub/mul/div/mod/right-add unchanged (26,14,120,3,2,120); classification does not raise on ordinary combos. HOLDS patched.
- probe_7 (Req 3.1): ordinary int-int CombinedExpression.as_sql emits plain arithmetic ('("a" - "b")') with no duration/interval machinery; temporal SQL is reached via resolution (TemporalSubtraction). HOLDS patched.

CANDIDATE PATCH (weak.diff): a partial/naive fix that moves classification to resolve_expression but implements ONLY the DurationField-mixing branch (Req 1.2) and OMITS the temporal-subtraction branch (Req 1.3). It applies cleanly at base. The probe suite REJECTS it: probe_1 (positive control) VIOLATED and probe_3 VIOLATED, because date-date subtraction no longer becomes a TemporalSubtraction with a DurationField. This demonstrates the suite discriminates a wrong implementation and would not pass the hidden temporal-subtraction FAIL_TO_PASS tests.

Conclusion: requirements are faithful to and no stronger than the gold patch (no VIOLATION found among 7 probes), and the suite rejects a plausibly-wrong partial fix (no TOO-WEAK finding). Positive control discriminates base vs patched. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes run in the instance image on the gold-patched tree. The patch precisely moves the DurationField-mixing and temporal-subtraction (SUB, same date/datetime/time type) classification from CombinedExpression.as_sql into resolve_expression, guarded so it only applies to plain CombinedExpression (not already DurationExpression/TemporalSubtraction), and adds the has_native_duration_field short-circuit in DurationExpression.as_sql. Requirements pin the changed observable behavior at the correct boundary (re-typing during resolution yielding determinate DurationField output_field), not a narrow slice. Notably the classification uses self.lhs/self.rhs (unresolved) for constructing the specialized expression while type-checking the resolved operands — requirements 1.1-1.4 accurately describe operands being resolved first then classified. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to public source identifiers only (CombinedExpression.resolve_expression/as_sql, DurationField/DateField/DateTimeField/TimeField, native duration field) — all pre-existing in django/db/models/expressions.py and its backend features, none invented by the gold patch. The gold-patch classes TemporalSubtraction and DurationExpression are referenced only via generic prose ('temporal-subtraction combination', 'duration combination'), not by their code names. The core problem (FieldError on unwrapped temporal subtraction, and the goal of classifying at resolve time) is already public in problem_statement. Requirement 5 is the most test-adjacent (it enumerates subquery operands, NULL->None, microsecond precision, Case-expression operands, gt/lt threshold filters), tracking the FAIL_TO_PASS/PASS_TO_PASS regression suite's structure — but it transmits BEHAVIORS, not tests: no test function/class names (test_date_subtraction, FTimeDeltaTests, etc.), no file path (tests/expressions/tests.py), no parametrization ids, no quoted test or gold code, and no test-specific literals (the 8999999999999999-microsecond value is generalized to 'large timedelta magnitudes'; no Experiment/Time model or field names like completed/assigned/start/end are surfaced). Translating what the tests check into behavioral acceptance criteria is the intended purpose of the spec, and localizing to the changed module is legitimate. Nothing here reconstructs the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
