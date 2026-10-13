# P2 adversarial audit — django__django-10880

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
"""Positive control / Req1.2: distinct Count over a Case/When must NOT glue
DISTINCT to CASE (never DISTINCTCASE); must contain a whitespace boundary.
Also Req1.1: DISTINCT followed by a single space.
HOLDS on patched, FAILS at base."""
import re
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection
from django.db.models import Count, Case, When, Value, IntegerField


class Book(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(null=True)

    class Meta:
        app_label = 'probeapp'


agg = Count(Case(When(rating__gt=3, then='rating')), distinct=True)
qs = Book.objects.annotate(v=agg)
sql, params = qs.query.get_compiler(using='default').as_sql()
print("SQL:", sql)

# Extract the COUNT(...) call
m = re.search(r'COUNT\((.*?)\)', sql, re.IGNORECASE | re.DOTALL)
inner = m.group(1) if m else sql
print("inner:", repr(inner))

if 'DISTINCTCASE' in sql.upper().replace(' ', '') and 'DISTINCT CASE' not in sql.upper():
    print("FAIL: DISTINCT glued to CASE")
    raise SystemExit(1)

# Require an explicit 'DISTINCT ' with trailing whitespace before CASE
if not re.search(r'DISTINCT\s+CASE', sql, re.IGNORECASE):
    print("FAIL: no whitespace boundary between DISTINCT and CASE")
    raise SystemExit(1)

print("PASS: DISTINCT is separated from CASE")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3: distinct aggregate over a conditional argument executes without a SQL
syntax error and returns the correct distinct count of conditionally-selected
values. Runs against sqlite backend end-to-end."""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection
from django.db.models import Count, Case, When


class Book(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(null=True)

    class Meta:
        app_label = 'probeapp'


with connection.schema_editor() as se:
    se.create_model(Book)

# ratings: 5,5,4,2,None -> distinct ratings >3 are {5,4} -> count 2
for r in [5, 5, 4, 2, None]:
    Book.objects.create(name='b', rating=r)

agg = Count(Case(When(rating__gt=3, then='rating')), distinct=True)
try:
    result = Book.objects.aggregate(v=agg)
except Exception as e:
    print("FAIL: query raised:", type(e).__name__, e)
    raise SystemExit(1)

print("result:", result)
if result['v'] != 2:
    print("FAIL: expected 2 distinct values, got", result['v'])
    raise SystemExit(1)
print("PASS: executed and returned correct distinct count")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1 & Req2.2: non-distinct aggregate emits no DISTINCT and no leading
space; argument follows '(' immediately. Also Req1.1 for a plain-column distinct:
DISTINCT + single space + column."""
import re
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models
from django.db.models import Count


class Book(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(null=True)

    class Meta:
        app_label = 'probeapp'


def frag(agg):
    qs = Book.objects.annotate(v=agg)
    return qs.query.get_compiler(using='default').as_sql()[0]


# non-distinct count over rating
nd = frag(Count('rating'))
print("non-distinct SQL:", nd)
mnd = re.search(r'COUNT\((.*?)\)', nd)
inner = mnd.group(1)
print("non-distinct inner:", repr(inner))
if 'DISTINCT' in inner.upper():
    print("FAIL: DISTINCT present in non-distinct aggregate")
    raise SystemExit(1)
if inner != inner.lstrip():
    print("FAIL: stray leading whitespace in non-distinct argument")
    raise SystemExit(1)

# distinct count over plain column: exactly 'DISTINCT ' + column
d = frag(Count('rating', distinct=True))
print("distinct SQL:", d)
md = re.search(r'COUNT\((.*?)\)', d)
dinner = md.group(1)
print("distinct inner:", repr(dinner))
if not dinner.upper().startswith('DISTINCT '):
    print("FAIL: distinct inner does not start with 'DISTINCT '")
    raise SystemExit(1)
# ensure single space (not double)
if re.match(r'DISTINCT\s{2,}', dinner, re.IGNORECASE):
    print("FAIL: more than one space after DISTINCT")
    raise SystemExit(1)

print("PASS: non-distinct clean; distinct has single separating space")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.2: an aggregate that does not permit distinct raises TypeError when
constructed with distinct=True (e.g. Sum). Req3.4 regression: the existing
error is preserved."""
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db.models import Sum, Avg, Max

for cls in (Sum, Avg, Max):
    try:
        cls('x', distinct=True)
    except TypeError as e:
        print("OK %s raised TypeError: %s" % (cls.__name__, e))
        if 'distinct' not in str(e).lower():
            print("FAIL: message does not mention distinct")
            raise SystemExit(1)
    else:
        print("FAIL: %s did not raise TypeError for distinct=True" % cls.__name__)
        raise SystemExit(1)

print("PASS: non-distinct-capable aggregates reject distinct=True")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1 & Req3.4 regression: overall call structure preserved and plain/star
counts and distinct sum-like renderings unchanged.
- COUNT(*) renders as COUNT(*) (no DISTINCT, no stray space)
- distinct Sum-style over a column renders 'DISTINCT ' + column
- non-distinct Avg renders AVG(<col>) with arg right after '('."""
import re
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models
from django.db.models import Count, Avg


class Book(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(null=True)

    class Meta:
        app_label = 'probeapp'


def frag(agg):
    qs = Book.objects.annotate(v=agg)
    return qs.query.get_compiler(using='default').as_sql()[0]


# COUNT(*)
star = frag(Count('*'))
print("star SQL:", star)
ms = re.search(r'COUNT\((.*?)\)', star)
sinner = ms.group(1)
print("star inner:", repr(sinner))
if sinner != '*':
    print("FAIL: COUNT(*) inner is not exactly '*':", repr(sinner))
    raise SystemExit(1)

# AVG non-distinct: arg immediately after '('
avg = frag(Avg('rating'))
print("avg SQL:", avg)
ma = re.search(r'AVG\((.*?)\)', avg)
ainner = ma.group(1)
print("avg inner:", repr(ainner))
if ainner != ainner.lstrip() or 'DISTINCT' in ainner.upper():
    print("FAIL: AVG rendering altered")
    raise SystemExit(1)

# distinct Count over column: structure FUNC( DISTINCT col )
dc = frag(Count('rating', distinct=True))
print("distinct count SQL:", dc)
if not re.search(r'COUNT\(DISTINCT "probeapp_book"\."rating"\)', dc):
    print("FAIL: distinct count structure unexpected")
    raise SystemExit(1)

print("PASS: structure and existing renderings preserved")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.2: distinct Count over a Case/When must NOT glue
DISTINCT to CASE (never DISTINCTCASE); must contain a whitespace boundary.
Also Req1.1: DISTINCT followed by a single space.
HOLDS on patched, FAILS at base."""
import re
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection
from django.db.models import Count, Case, When, Value, IntegerField


class Book(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(null=True)

    class Meta:
        app_label = 'probeapp'


agg = Count(Case(When(rating__gt=3, then='rating')), distinct=True)
qs = Book.objects.annotate(v=agg)
sql, params = qs.query.get_compiler(using='default').as_sql()
print("SQL:", sql)

# Extract the COUNT(...) call
m = re.search(r'COUNT\((.*?)\)', sql, re.IGNORECASE | re.DOTALL)
inner = m.group(1) if m else sql
print("inner:", repr(inner))

if 'DISTINCTCASE' in sql.upper().replace(' ', '') and 'DISTINCT CASE' not in sql.upper():
    print("FAIL: DISTINCT glued to CASE")
    raise SystemExit(1)

# Require an explicit 'DISTINCT ' with trailing whitespace before CASE
if not re.search(r'DISTINCT\s+CASE', sql, re.IGNORECASE):
    print("FAIL: no whitespace boundary between DISTINCT and CASE")
    raise SystemExit(1)

print("PASS: DISTINCT is separated from CASE")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-10880: gold fix changes extra_context['distinct'] from 'DISTINCT' to 'DISTINCT ' in Aggregate.as_sql, so COUNT(DISTINCT CASE WHEN ...) no longer emits COUNT(DISTINCTCASE ...).

Probes (all on the gold-patched tree via nl_attack probe runner):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): distinct Count over a Case/When must contain 'DISTINCT CASE' with a whitespace boundary, never DISTINCTCASE. HOLDS patched (inner='DISTINCT CASE WHEN ...'); FAILS at base (VIOLATED: 'DISTINCTCASE WHEN ...') — discriminates.
- probe_2 (Req1.3): distinct Count over Case/When executes on sqlite and returns the correct distinct count (2 for ratings {5,5,4,2,None} filtered >3). HOLDS patched.
- probe_3 (Req2.1/2.2 + Req1.1): non-distinct Count('rating') inner has no DISTINCT and no leading whitespace; distinct Count('rating') inner is exactly 'DISTINCT '+col with a single space. HOLDS patched.
- probe_4 (Req3.2/3.4): Sum/Avg/Max with distinct=True raise TypeError mentioning distinct. HOLDS patched.
- probe_5 (Req3.1/3.4): COUNT(*) inner is exactly '*', AVG('rating') unchanged, distinct Count structure COUNT(DISTINCT col). HOLDS patched.

Candidate wrong-fix (weak.diff): move the separator into the template ('%(function)s(%(distinct)s %(expressions)s)') while leaving the modifier as bare 'DISTINCT'. This fixes the DISTINCT-glue case (probe_1, probe_2 still pass) but introduces a stray leading space for every NON-distinct aggregate. REJECTED by probe_3 (non-distinct inner ' "..."."rating"') and probe_5 (COUNT( *) instead of COUNT(*)). This byte-level regression would also fail the hidden regression tests that assert non-distinct SQL is unchanged. Demonstrates the suite discriminates a plausibly-wrong reading of the requirements.

All 5 probes hold on the patched tree; positive control fails at base and holds patched; the candidate patch is rejected by the suite => SOUND.

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
"""Positive control / Req1.2: distinct Count over a Case/When must NOT glue
DISTINCT to CASE (never DISTINCTCASE); must contain a whitespace boundary.
Also Req1.1: DISTINCT followed by a single space.
HOLDS on patched, FAILS at base."""
import re
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    )
django.setup()

from django.db import models, connection
from django.db.models import Count, Case, When, Value, IntegerField


class Book(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(null=True)

    class Meta:
        app_label = 'probeapp'


agg = Count(Case(When(rating__gt=3, then='rating')), distinct=True)
qs = Book.objects.annotate(v=agg)
sql, params = qs.query.get_compiler(using='default').as_sql()
print("SQL:", sql)

# Extract the COUNT(...) call
m = re.search(r'COUNT\((.*?)\)', sql, re.IGNORECASE | re.DOTALL)
inner = m.group(1) if m else sql
print("inner:", repr(inner))

if 'DISTINCTCASE' in sql.upper().replace(' ', '') and 'DISTINCT CASE' not in sql.upper():
    print("FAIL: DISTINCT glued to CASE")
    raise SystemExit(1)

# Require an explicit 'DISTINCT ' with trailing whitespace before CASE
if not re.search(r'DISTINCT\s+CASE', sql, re.IGNORECASE):
    print("FAIL: no whitespace boundary between DISTINCT and CASE")
    raise SystemExit(1)

print("PASS: DISTINCT is separated from CASE")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-10880: gold fix changes extra_context['distinct'] from 'DISTINCT' to 'DISTINCT ' in Aggregate.as_sql, so COUNT(DISTINCT CASE WHEN ...) no longer emits COUNT(DISTINCTCASE ...).

Probes (all on the gold-patched tree via nl_attack probe runner):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): distinct Count over a Case/When must contain 'DISTINCT CASE' with a whitespace boundary, never DISTINCTCASE. HOLDS patched (inner='DISTINCT CASE WHEN ...'); FAILS at base (VIOLATED: 'DISTINCTCASE WHEN ...') — discriminates.
- probe_2 (Req1.3): distinct Count over Case/When executes on sqlite and returns the correct distinct count (2 for ratings {5,5,4,2,None} filtered >3). HOLDS patched.
- probe_3 (Req2.1/2.2 + Req1.1): non-distinct Count('rating') inner has no DISTINCT and no leading whitespace; distinct Count('rating') inner is exactly 'DISTINCT '+col with a single space. HOLDS patched.
- probe_4 (Req3.2/3.4): Sum/Avg/Max with distinct=True raise TypeError mentioning distinct. HOLDS patched.
- probe_5 (Req3.1/3.4): COUNT(*) inner is exactly '*', AVG('rating') unchanged, distinct Count structure COUNT(DISTINCT col). HOLDS patched.

Candidate wrong-fix (weak.diff): move the separator into the template ('%(function)s(%(distinct)s %(expressions)s)') while leaving the modifier as bare 'DISTINCT'. This fixes the DISTINCT-glue case (probe_1, probe_2 still pass) but introduces a stray leading space for every NON-distinct aggregate. REJECTED by probe_3 (non-distinct inner ' "..."."rating"') and probe_5 (COUNT( *) instead of COUNT(*)). This byte-level regression would also fail the hidden regression tests that assert non-distinct SQL is unchanged. Demonstrates the suite discriminates a plausibly-wrong reading of the requirements.

All 5 probes hold on the patched tree; positive control fails at base and holds patched; the candidate patch is rejected by the suite => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-character fix (add trailing space to DISTINCT modifier). R3.2 (TypeError for non-distinct-capable aggregates), R3.3 (filter clause rendering), and R3.4 (unchanged behavior of all other aggregates) are all preserved-behavior requirements consistent with the patch touching only the distinct-modifier string — the surrounding filter/template logic is untouched. No requirement mandates behavior the code lacks, forbids behavior it has, invents behavior, or mispins the boundary. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to django.db.models.aggregates / Aggregate.as_sql / Count and describes the distinct-modifier spacing fix — all legitimate localization and behavioral description. The malformed-SQL example `COUNT(DISTINCTCASE WHEN ...)` and the `CASE WHEN` token appear verbatim in the PUBLIC problem_statement, so they are not leaks. Checked against hidden material: the sole FAIL_TO_PASS test name `test_count_distinct_expression`, its path `tests/aggregation/tests.py`, the invented annotation identifier `distinct_ratings`, the specific test inputs (`Count(Case(When(pages__gt=300, then='rating')), distinct=True)`), and the expected value `4` are NONE of them present in requirements.md. The gold edit ('DISTINCT' -> 'DISTINCT ') is described behaviorally (single trailing separator) rather than quoted. Requirement 3.4's enumeration (plain counts, star counts, distinct sums, filtered/conditional aggregations, value/annotation aggregations, ordering by aggregates) reads as a generic aggregate-feature regression list, not a mirror of PASS_TO_PASS parametrization — no test ids, field names, or case-specific values. This is translating test-checked behavior into requirements, which is the intended purpose, not transmitting the tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
