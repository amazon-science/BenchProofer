# P2 adversarial audit — django__django-13121

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
"""Req 1.1/1.3 + positive control: annotate DurationField + timedelta constant
on SQLite (has_native_duration_field=False); iterating must not raise and the
annotated value must equal stored duration + timedelta."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models, connection

class Experiment(models.Model):
    estimated_time = models.DurationField()
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Experiment)

assert connection.features.has_native_duration_field is False, "expected non-native backend"

stored = datetime.timedelta(days=1, hours=2, minutes=3, microseconds=456)
Experiment.objects.create(estimated_time=stored)

delta = datetime.timedelta(hours=5, microseconds=789)
from django.db.models import F
qs = Experiment.objects.annotate(total=F('estimated_time') + delta)
row = list(qs)[0]  # must not raise
observed = row.total
expected = stored + delta
print("observed", observed, "expected", expected)
assert observed == expected, f"{observed!r} != {expected!r}"
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2: over a range of timedelta operands incl. negatives and microsecond
components, the annotated value equals stored + operand for every operand."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import F

class Experiment(models.Model):
    estimated_time = models.DurationField()
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Experiment)

stored = datetime.timedelta(days=2, seconds=10, microseconds=123)
Experiment.objects.create(estimated_time=stored)

operands = [
    datetime.timedelta(0),
    datetime.timedelta(hours=3),
    datetime.timedelta(days=-1, hours=-2),
    datetime.timedelta(microseconds=-999),
    datetime.timedelta(days=1, microseconds=1),
    datetime.timedelta(seconds=-45, microseconds=500000),
]
for d in operands:
    val = Experiment.objects.annotate(total=F('estimated_time') + d).get().total
    exp = stored + d
    print("delta", d, "->", val, "expected", exp)
    assert val == exp, f"for {d!r}: {val!r} != {exp!r}"
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2: Combinable._combine wrapping a bare timedelta yields a Value
whose output_field internal type is DurationField; wrapping a non-timedelta
literal yields an ordinary Value with no imposed duration output type."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models
from django.db.models import F
from django.core.exceptions import FieldError

# timedelta operand -> DurationField output type
expr = F('x') + datetime.timedelta(hours=1)
# expr is CombinedExpression(lhs=F, rhs=Value); rhs is the wrapped literal
rhs = expr.rhs
itype = rhs.output_field.get_internal_type()
print("timedelta wrapped -> output field internal type:", itype)
assert itype == 'DurationField', itype

# non-timedelta operand -> no duration output type imposed
expr2 = F('x') + 5
rhs2 = expr2.rhs
try:
    of = rhs2.output_field
    resolved = of.get_internal_type()
except FieldError:
    resolved = None
print("int wrapped -> output field:", resolved)
assert resolved != 'DurationField', "int literal must not be typed as DurationField"
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 4.1/4.2: subtracting two DateTimeField operands routes through
TemporalSubtraction and yields the correct duration, incl. microsecond diff."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import F, DurationField, ExpressionWrapper

class Experiment(models.Model):
    estimated_time = models.DurationField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Experiment)

start = datetime.datetime(2020, 1, 1, 8, 0, 0, 100000)
end = datetime.datetime(2020, 1, 2, 9, 30, 0, 750000)
Experiment.objects.create(estimated_time=datetime.timedelta(0), start=start, end=end)

expr = ExpressionWrapper(F('end') - F('start'), output_field=DurationField())
diff = Experiment.objects.annotate(d=expr).get().d
print("end - start =", diff, "expected", end - start)
assert diff == end - start, diff

# verify it used TemporalSubtraction routing
from django.db.models.expressions import CombinedExpression, TemporalSubtraction
ce = (F('end') - F('start')).resolve_expression(
    Experiment.objects.all().query)
# resolve output fields via the query
print("connector", ce.connector)
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 5.1: date/datetime combined with a duration operand still returns the
correctly shifted datetime value, including a microsecond component."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import F, DateTimeField, ExpressionWrapper

class Experiment(models.Model):
    estimated_time = models.DurationField()
    start = models.DateTimeField()
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Experiment)

start = datetime.datetime(2020, 1, 1, 12, 0, 0, 123456)
dur = datetime.timedelta(days=3, hours=2, microseconds=654321)
Experiment.objects.create(estimated_time=dur, start=start)

# datetime field + duration constant (mixed types -> explicit output_field)
plus_expr = ExpressionWrapper(F('start') + dur, output_field=DateTimeField())
plus = Experiment.objects.annotate(v=plus_expr).get().v
print("start + dur =", plus, "expected", start + dur)
assert plus == start + dur, plus

# datetime field - duration field
minus_expr = ExpressionWrapper(F('start') - F('estimated_time'), output_field=DateTimeField())
minus = Experiment.objects.annotate(v=minus_expr).get().v
print("start - est =", minus, "expected", start - dur)
assert minus == start - dur, minus
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5.2: durations added to / subtracted from stored duration values in an
annotation reflect the correct combined duration (duration +/- duration)."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import F

class Experiment(models.Model):
    estimated_time = models.DurationField()
    actual = models.DurationField()
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Experiment)

est = datetime.timedelta(days=1, microseconds=250)
act = datetime.timedelta(hours=5, microseconds=125)
Experiment.objects.create(estimated_time=est, actual=act)

# duration field + duration field
s = Experiment.objects.annotate(v=F('estimated_time') + F('actual')).get().v
print("est + act =", s, "expected", est + act)
assert s == est + act, s

# duration field - duration field
d = Experiment.objects.annotate(v=F('estimated_time') - F('actual')).get().v
print("est - act =", d, "expected", est - act)
assert d == est - act, d
print("OK")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 5.5: Value literal semantics preserved — a Value with an explicit output
field remains distinguishable from one without; equality, hashing,
deconstruction and repr consistent. Also confirms DurationValue is gone / not
required for correctness (a bare Value carries the duration typing)."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db.models import Value, DurationField

v_plain = Value(5)
v_typed = Value(5, output_field=DurationField())

# distinguishable
print("plain == typed:", v_plain == v_typed)
assert v_plain != v_typed, "Value with/without output field must differ"

# same-config equality + hash
v_plain2 = Value(5)
assert v_plain == v_plain2, "equal Values must compare equal"
assert hash(v_plain) == hash(v_plain2), "equal Values must hash equal"

# deconstruction round-trips output_field presence
path, args, kwargs = v_typed.deconstruct()
print("deconstruct typed:", path, args, kwargs)
assert 'output_field' in kwargs, "typed Value must deconstruct with output_field"
path2, args2, kwargs2 = v_plain.deconstruct()
assert 'output_field' not in kwargs2, "plain Value must not carry output_field"

# repr sanity
r = repr(v_typed)
print("repr:", r)
assert 'Value' in r
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.1/1.3 + positive control: annotate DurationField + timedelta constant
on SQLite (has_native_duration_field=False); iterating must not raise and the
annotated value must equal stored duration + timedelta."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models, connection

class Experiment(models.Model):
    estimated_time = models.DurationField()
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Experiment)

assert connection.features.has_native_duration_field is False, "expected non-native backend"

stored = datetime.timedelta(days=1, hours=2, minutes=3, microseconds=456)
Experiment.objects.create(estimated_time=stored)

delta = datetime.timedelta(hours=5, microseconds=789)
from django.db.models import F
qs = Experiment.objects.annotate(total=F('estimated_time') + delta)
row = list(qs)[0]  # must not raise
observed = row.total
expected = stored + delta
print("observed", observed, "expected", expected)
assert observed == expected, f"{observed!r} != {expected!r}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Backend: in-memory SQLite (has_native_duration_field=False), asserted in probe_1. All 7 probes HOLD on the gold-patched tree.

Probes -> requirement mapping:
- probe_1 (Req 1.1/1.3, POSITIVE CONTROL): annotate F('estimated_time')+timedelta on SQLite; iterating must not raise and value == stored+delta. HOLDS patched, VIOLATED at base (base raises the interval-literal conversion error) => discriminating.
- probe_2 (Req 1.2): range of operands incl. negatives and microsecond components, each == stored+operand. HOLDS patched, VIOLATED at base.
- probe_3 (Req 2.1/2.2): _combine wraps a bare timedelta into a Value whose output_field internal type is DurationField; a non-timedelta int literal is NOT typed DurationField. HOLDS both trees (base already had DurationValue typing, so not discriminating on its own).
- probe_4 (Req 4.1/4.2): DateTimeField-DateTimeField subtraction via TemporalSubtraction yields correct microsecond duration. HOLDS patched.
- probe_5 (Req 5.1): date/datetime +/- duration returns correctly shifted datetime (ExpressionWrapper for mixed types). HOLDS patched.
- probe_6 (Req 5.2): duration+duration and duration-duration annotations reflect correct combined duration (the duration-only case the fix targets). HOLDS patched, VIOLATED at base.
- probe_7 (Req 5.5): Value literal semantics -- typed vs untyped Value distinguishable, equality/hash/deconstruct/repr consistent. HOLDS patched.

CANDIDATE PATCH candA (partial/lazy fix): the gold diff MINUS the CombinedExpression.as_sql routing hunk -- i.e. it keeps _combine typing timedelta as DurationField and removes DurationValue, but retains the base routing rule (route to DurationExpression whenever EITHER operand is a duration, regardless of type equality), violating Req 3.2. It applies cleanly at base. Probes 1, 2 and 6 REJECT it (the duration+timedelta / duration+duration cases still hit the interval path and raise on iteration), demonstrating the suite discriminates the requirements-critical routing change. probes 3/4/5/7 pass under it as expected. This confirms the suite is not a rubber stamp; no requirements-conforming alternative patch was found, so no TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, the positive control fails at base and holds patched (prepatch reproduced), and >=1 candidate patch is exercised and REJECTED by the probe suite.

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
"""Req 1.1/1.3 + positive control: annotate DurationField + timedelta constant
on SQLite (has_native_duration_field=False); iterating must not raise and the
annotated value must equal stored duration + timedelta."""
import datetime
import django
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    USE_TZ=False)
django.setup()
from django.db import models, connection

class Experiment(models.Model):
    estimated_time = models.DurationField()
    class Meta:
        app_label = 'contenttypes'

with connection.schema_editor() as se:
    se.create_model(Experiment)

assert connection.features.has_native_duration_field is False, "expected non-native backend"

stored = datetime.timedelta(days=1, hours=2, minutes=3, microseconds=456)
Experiment.objects.create(estimated_time=stored)

delta = datetime.timedelta(hours=5, microseconds=789)
from django.db.models import F
qs = Experiment.objects.annotate(total=F('estimated_time') + delta)
row = list(qs)[0]  # must not raise
observed = row.total
expected = stored + delta
print("observed", observed, "expected", expected)
assert observed == expected, f"{observed!r} != {expected!r}"
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

Backend: in-memory SQLite (has_native_duration_field=False), asserted in probe_1. All 7 probes HOLD on the gold-patched tree.

Probes -> requirement mapping:
- probe_1 (Req 1.1/1.3, POSITIVE CONTROL): annotate F('estimated_time')+timedelta on SQLite; iterating must not raise and value == stored+delta. HOLDS patched, VIOLATED at base (base raises the interval-literal conversion error) => discriminating.
- probe_2 (Req 1.2): range of operands incl. negatives and microsecond components, each == stored+operand. HOLDS patched, VIOLATED at base.
- probe_3 (Req 2.1/2.2): _combine wraps a bare timedelta into a Value whose output_field internal type is DurationField; a non-timedelta int literal is NOT typed DurationField. HOLDS both trees (base already had DurationValue typing, so not discriminating on its own).
- probe_4 (Req 4.1/4.2): DateTimeField-DateTimeField subtraction via TemporalSubtraction yields correct microsecond duration. HOLDS patched.
- probe_5 (Req 5.1): date/datetime +/- duration returns correctly shifted datetime (ExpressionWrapper for mixed types). HOLDS patched.
- probe_6 (Req 5.2): duration+duration and duration-duration annotations reflect correct combined duration (the duration-only case the fix targets). HOLDS patched, VIOLATED at base.
- probe_7 (Req 5.5): Value literal semantics -- typed vs untyped Value distinguishable, equality/hash/deconstruct/repr consistent. HOLDS patched.

CANDIDATE PATCH candA (partial/lazy fix): the gold diff MINUS the CombinedExpression.as_sql routing hunk -- i.e. it keeps _combine typing timedelta as DurationField and removes DurationValue, but retains the base routing rule (route to DurationExpression whenever EITHER operand is a duration, regardless of type equality), violating Req 3.2. It applies cleanly at base. Probes 1, 2 and 6 REJECT it (the duration+timedelta / duration+duration cases still hit the interval path and raise on iteration), demonstrating the suite discriminates the requirements-critical routing change. probes 3/4/5/7 pass under it as expected. This confirms the suite is not a rubber stamp; no requirements-conforming alternative patch was found, so no TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, the positive control fails at base and holds patched (prepatch reproduced), and >=1 candidate patch is exercised and REJECTED by the probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch's core change is the new CombinedExpression.as_sql routing predicate: route to DurationExpression iff (not native) AND 'DurationField' in {lhs_type, rhs_type} AND lhs_type != rhs_type. Req 3.1 pins the mixed-type→DurationExpression direction and Req 3.2 pins the same-type→ordinary-path direction (the actual bug fix: duration+duration no longer misrouted into the interval-literal path). This is a biconditional pin of the changed observable behavior, not one branch. Req 2 matches the _combine rewrite (timedelta→Value(output_field=DurationField()), else Value(other)); Req 3.4 matches DurationExpression.compile now formatting any duration-internal-type operand (DurationValue special-case removed); Req 4 matches the preserved TemporalSubtraction branch; Req 5 covers preserved mixed date/duration and general arithmetic/semantics. Req 1 (end-to-end evaluate-without-error returning stored+timedelta) is exactly the issue's failing scenario. No requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change with pre-existing public code symbols (Combinable._combine, CombinedExpression.as_sql, DurationExpression, TemporalSubtraction, backend operations.py) and translates behavior into EARS criteria. All concrete artifacts it shares — the Experiment/DurationField model, F('estimated_time') + timedelta expression, has_native_duration_field, and the microsecond-interval parse failure — are already in the public problem_statement/traceback. No hidden-test names/paths/ids (e.g. test_duration_expressions, FTimeDeltaTests, tests/expressions/tests.py), no quoted test or gold code, and no fix-invented identifiers (the gold only removes DurationValue/date_interval_sql/duration_microseconds, none of which the doc names). Req 1.2's 'negative / microsecond' mention and Req 4/5's subquery + arithmetic-operator + deconstruct/hash/pickle enumerations parallel PASS_TO_PASS test categories but are framed as regression-preservation behavior, not as parametrized case lists or test identifiers, so they describe behavior rather than reconstruct the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
