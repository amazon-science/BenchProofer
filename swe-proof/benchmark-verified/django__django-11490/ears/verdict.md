# P2 adversarial audit — django__django-11490

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

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""POSITIVE CONTROL. Req2.2: a composed queryset evaluated first projecting
one column list and then a DIFFERENT list must return exactly the columns
requested by the second evaluation. Encodes the exact issue example.
HOLDS iff the second evaluation returns a single-column ('order',) row.
Fails at base (returns stale two-column row)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(ReservedName)

ReservedName.objects.create(name='a', order=2)
qs1 = ReservedName.objects.all()

first = qs1.union(qs1).values_list('name', 'order').get()
print("first (name,order):", first)
second = qs1.union(qs1).values_list('order').get()
print("second (order):", second)

ok = (first == ('a', 2)) and (second == (2,))
print("OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1 & 1.2: a restricted column list is applied to combined parts so the
compound SQL projects exactly the requested columns, in the composed query's
selection order. HOLDS iff union().values_list('name','order') yields a row
with exactly those two columns in that order, and values_list('order','name')
yields them in the reversed order."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(ReservedName)

ReservedName.objects.create(name='a', order=2)
qs1 = ReservedName.objects.all()

r1 = qs1.union(qs1).values_list('name', 'order').get()
r2 = qs1.union(qs1).values_list('order', 'name').get()
print("name,order ->", r1)
print("order,name ->", r2)
ok = (r1 == ('a', 2)) and (r2 == (2, 'a'))
print("OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1: applying the column list must be done on a per-evaluation copy and
leave the shared combined-query definition unchanged. Probe: inspect the
composed queryset's underlying combined query objects BEFORE and AFTER
building SQL for an evaluation restricted to a column list. Their values_select
must be unchanged (empty) after compilation — i.e. compilation did not mutate
the shared part. HOLDS iff the combined parts' values_select stays empty."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(ReservedName)

ReservedName.objects.create(name='a', order=2)
qs1 = ReservedName.objects.all()

composed = qs1.union(qs1).values_list('name', 'order')
combined = composed.query.combined_queries
before = [tuple(q.values_select) for q in combined]
print("combined values_select before:", before)

# Force SQL construction (the compiler path that used to mutate shared parts).
_ = str(composed.query)
list(composed)  # execute

after = [tuple(q.values_select) for q in combined]
print("combined values_select after:", after)

ok = all(v == () for v in before) and all(v == () for v in after)
print("OK" if ok else "MUTATED")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.2 (compositions over annotated querysets) + Req1.2 (per-part column
list built from extra/value/annotation selections in order). Mirrors
test_union_with_two_annotated_values_list: two annotated querysets unioned and
projected via values_list on the annotations. HOLDS iff the compound projects
exactly the annotated columns with correct values.

Also exercises Req1.3 indirectly: a part that already restricts its own
columns (via values_list) must keep them. Here we union two querysets that each
already carry values_list('num','count')."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection
from django.db.models import Count

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(Number)

for n in range(1, 5):
    Number.objects.create(num=n)

qs1 = Number.objects.filter(num=1).annotate(count=Count('pk')).values_list('num', 'count')
qs2 = Number.objects.filter(num=2).annotate(count=Count('pk')).values_list('num', 'count')
rows = sorted(qs1.union(qs2))
print("rows:", rows)
ok = rows == [(1, 1), (2, 1)]
print("OK" if ok else "BAD")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1.4 & Req3.1/3.3: when the composed query does NOT restrict its
projection, combined parts' projection is left unchanged; and union/difference
with an empty part still omits the empty part and produces correct counts.
HOLDS iff:
  - a plain union (no values) returns full model rows with all fields,
  - union with an empty qs yields the non-empty side's rows,
  - difference with an empty qs yields the full left side."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection

class Number(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(Number)

for n in range(1, 6):
    Number.objects.create(num=n)

qs = Number.objects.all()
empty = Number.objects.none()

# plain union, no values() restriction -> full objects
u = qs.union(qs)
objs = list(u)
print("plain union count:", len(objs), "first has num attr:", hasattr(objs[0], "num"))

# union with empty part
ue = qs.union(empty)
nums_ue = sorted(o.num for o in ue)
print("union with empty:", nums_ue)

# difference with empty part -> full left
de = qs.difference(empty)
nums_de = sorted(o.num for o in de)
print("difference with empty:", nums_de)

ok = (len(objs) == 5 and hasattr(objs[0], "num")
      and nums_ue == [1, 2, 3, 4, 5]
      and nums_de == [1, 2, 3, 4, 5])
print("OK" if ok else "BAD")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.3 + Req3.4/3.5: repeated evaluation with the SAME column list gives the
same correct result; ordering by a non-selected column raises a DB error;
limits/counting keep working. HOLDS iff all hold."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection, DatabaseError

class ReservedName(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(ReservedName)

ReservedName.objects.create(name='a', order=2)
ReservedName.objects.create(name='b', order=1)
qs1 = ReservedName.objects.all()

# repeated same-list evaluation
composed = qs1.union(qs1)
r_a = composed.values_list('order').order_by('order')
first = list(r_a)
second = list(qs1.union(qs1).values_list('order').order_by('order'))
print("repeat1:", first, "repeat2:", second)

# limits / counting
cnt = qs1.union(qs1).count()
print("count:", cnt)
limited = list(qs1.union(qs1).values_list('order').order_by('order')[:1])
print("limited:", limited)

# ordering by a column not among selected -> DB error
raised = False
try:
    list(qs1.union(qs1).values_list('order').order_by('name'))
except DatabaseError as e:
    raised = True
    print("order-by-nonselected raised:", type(e).__name__)
print("raised:", raised)

ok = (first == second == [(1,), (2,)]
      and cnt == 2
      and limited == [(1,)]
      and raised)
print("OK" if ok else "BAD")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL. Req2.2: a composed queryset evaluated first projecting
one column list and then a DIFFERENT list must return exactly the columns
requested by the second evaluation. Encodes the exact issue example.
HOLDS iff the second evaluation returns a single-column ('order',) row.
Fails at base (returns stale two-column row)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(ReservedName)

ReservedName.objects.create(name='a', order=2)
qs1 = ReservedName.objects.all()

first = qs1.union(qs1).values_list('name', 'order').get()
print("first (name,order):", first)
second = qs1.union(qs1).values_list('order').get()
print("second (order):", second)

ok = (first == ('a', 2)) and (second == (2,))
print("OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11490: gold fix adds `compiler.query = compiler.query.clone()` in get_combinator_sql so column-list propagation operates on a per-evaluation copy instead of mutating the shared combined-query part.

Probes (all standalone python, run in the official image; each configures an in-memory sqlite Django project with a probeapp path='/tmp' to satisfy AppConfig):
- probe_1 (POSITIVE CONTROL) — Req2.2: composed union evaluated first with values_list('name','order') then with values_list('order') must return the second list exactly. HOLDS patched ('a',2) then (2,); VIOLATED at base (second returns stale ('a',2)) => prepatch reproduced.
- probe_2 — Req1.1/1.2: restricted column list applied to parts in selection order; values_list('name','order') and reversed ('order','name') both project exactly the requested columns/order. HOLDS patched.
- probe_3 — Req2.1: inspects composed.query.combined_queries[*].values_select before and after building/executing SQL for a restricted evaluation; must stay () (shared definition unmutated). HOLDS patched.
- probe_4 — Req3.2/1.3: union of two annotated values_list querysets projects exactly the annotated columns [(1,1),(2,1)]. HOLDS patched.
- probe_5 — Req1.4/3.1/3.3: plain union (no values restriction) returns full model objects; union/difference with an empty part omit it and give correct rows. HOLDS patched.
- probe_6 — Req2.3/3.4/3.5: repeated same-list evaluation identical; count and limit work; order_by a non-selected column raises DatabaseError. HOLDS patched.

Candidate wrong-fix (weak.diff, 'clone_but_discard'): clones compiler.query but does NOT reassign it back (`_unused_clone = compiler.query.clone()`), so it still mutates the shared part — the lazy misreading of the requirement. Applies at base_commit. Under it, probes 1, 2, and 3 are REJECTED (stale second-evaluation result + mutated shared values_select), while 4/5/6 still hold. This demonstrates the suite discriminates a requirements-non-conforming fix; it would also fail the hidden F2P test (test_union_with_values changed-column-list assertion).

All 6 probes HOLD on the gold-patched tree; positive control discriminates (HOLDS patched, VIOLATED base). No violation or too-weak finding => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""POSITIVE CONTROL. Req2.2: a composed queryset evaluated first projecting
one column list and then a DIFFERENT list must return exactly the columns
requested by the second evaluation. Encodes the exact issue example.
HOLDS iff the second evaluation returns a single-column ('order',) row.
Fails at base (returns stale two-column row)."""
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import sys, types
pa = types.ModuleType("probeapp"); pa.__path__ = ['/tmp']; sys.modules["probeapp"] = pa
django.setup()
from django.db import models, connection

class ReservedName(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    class Meta:
        app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(ReservedName)

ReservedName.objects.create(name='a', order=2)
qs1 = ReservedName.objects.all()

first = qs1.union(qs1).values_list('name', 'order').get()
print("first (name,order):", first)
second = qs1.union(qs1).values_list('order').get()
print("second (order):", second)

ok = (first == ('a', 2)) and (second == (2,))
print("OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-11490: gold fix adds `compiler.query = compiler.query.clone()` in get_combinator_sql so column-list propagation operates on a per-evaluation copy instead of mutating the shared combined-query part.

Probes (all standalone python, run in the official image; each configures an in-memory sqlite Django project with a probeapp path='/tmp' to satisfy AppConfig):
- probe_1 (POSITIVE CONTROL) — Req2.2: composed union evaluated first with values_list('name','order') then with values_list('order') must return the second list exactly. HOLDS patched ('a',2) then (2,); VIOLATED at base (second returns stale ('a',2)) => prepatch reproduced.
- probe_2 — Req1.1/1.2: restricted column list applied to parts in selection order; values_list('name','order') and reversed ('order','name') both project exactly the requested columns/order. HOLDS patched.
- probe_3 — Req2.1: inspects composed.query.combined_queries[*].values_select before and after building/executing SQL for a restricted evaluation; must stay () (shared definition unmutated). HOLDS patched.
- probe_4 — Req3.2/1.3: union of two annotated values_list querysets projects exactly the annotated columns [(1,1),(2,1)]. HOLDS patched.
- probe_5 — Req1.4/3.1/3.3: plain union (no values restriction) returns full model objects; union/difference with an empty part omit it and give correct rows. HOLDS patched.
- probe_6 — Req2.3/3.4/3.5: repeated same-list evaluation identical; count and limit work; order_by a non-selected column raises DatabaseError. HOLDS patched.

Candidate wrong-fix (weak.diff, 'clone_but_discard'): clones compiler.query but does NOT reassign it back (`_unused_clone = compiler.query.clone()`), so it still mutates the shared part — the lazy misreading of the requirement. Applies at base_commit. Under it, probes 1, 2, and 3 are REJECTED (stale second-evaluation result + mutated shared values_select), while 4/5/6 still hold. This demonstrates the suite discriminates a requirements-non-conforming fix; it would also fail the hidden F2P test (test_union_with_values changed-column-list assertion).

All 6 probes HOLD on the gold-patched tree; positive control discriminates (HOLDS patched, VIOLATED base). No violation or too-weak finding => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe probe.py: HOLDS on gold-patched (r1=, r2=); VIOLATED on --base (r2==, AssertionError). Patch is a single added line cloning the combined-part query before set_values, so mutation no longer touches the shared part object across re-evaluations. Requirements' modeling boundary is the changed observable behavior (re-evaluation projects the newly requested columns), correctly stated biconditionally in Req 1.3/1.4 and Req 2.1.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes behavior and localizes the change to SQLCompiler.get_combinator_sql / values()/values_list(), which is legitimate. All potentially test-derived content is already public: the multi-evaluation column-change behavior (Requirement 2) is verbatim the problem_statement's ('name','order')->('order',) example; the gold edit is a single added line (compiler.query = compiler.query.clone()) and the doc translates it as 'do so on a per-evaluation copy... leave the underlying shared definition unchanged' — behavioral, no invented identifier or quoted code. Requirement 1.2's 'extra selections + value selections + annotation selections, preserving order' describes the pre-existing visible set_values((*extra_select,*values_select,...)) call, not the gold line. Requirement 3's regression list (union/intersection/difference, all=True/distinct, empty part omission for union/difference, ordering incl. by expression, error on ordering by non-selected column, unsupported slicing/ordering, limits, counting, multiple models, nesting) parallels the PASS_TO_PASS suite but is stated as public Django combinator API behavior — no test names, paths, ids, parametrization ids, quoted test code, or fix-invented identifiers. No semantic reconstruction of the hidden tests beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
