# P2 adversarial audit — django__django-13406

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
"""Positive control + Req1.3: pickle a .values('name').annotate(Sum) query,
install via the query setter, evaluate. Must yield dict rows and not crash.
HOLDS on patched, FAILS at base (base raises / returns wrong type)."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection
from django.db.models import Sum


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)
Toy.objects.create(name="a", qty=2)
Toy.objects.create(name="b", qty=5)

orig = Toy.objects.values("name").annotate(total=Sum("qty")).order_by("name")
expected = list(orig)
print("expected:", expected)

pq = pickle.dumps(orig.query)
qs = Toy.objects.all()
try:
    qs.query = pickle.loads(pq)
    got = list(qs)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("got:", got)

if any(not isinstance(r, dict) for r in got):
    print("FAIL: non-dict rows")
    sys.exit(1)
if got != expected:
    print("FAIL: rows differ from original")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1 + Req1.4: installing a query originating from a .values_list(...) variant
(here flat=True) must set _iterable_class to ValuesIterable and produce dict rows."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection
from django.db.models.query import ValuesIterable


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)
Toy.objects.create(name="b", qty=5)

for desc, src in [
    ("positional", Toy.objects.values_list("name", "qty").order_by("name")),
    ("flat", Toy.objects.values_list("name", flat=True).order_by("name")),
    ("named", Toy.objects.values_list("name", named=True).order_by("name")),
]:
    pq = pickle.dumps(src.query)
    qs = Toy.objects.all()
    qs.query = pickle.loads(pq)
    print(desc, "iterable_class:", qs._iterable_class.__name__)
    if qs._iterable_class is not ValuesIterable:
        print("FAIL: not ValuesIterable for", desc)
        sys.exit(1)
    rows = list(qs)
    print(desc, "rows:", rows)
    if any(not isinstance(r, dict) for r in rows):
        print("FAIL: non-dict rows for", desc)
        sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.1 + Req2.2: installing a NON-projecting (ordinary) query must leave the
default ModelIterable strategy unchanged, and evaluation yields model instances."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection
from django.db.models.query import ModelIterable


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)
Toy.objects.create(name="b", qty=5)

orig = Toy.objects.filter(qty__gt=0).order_by("name")
pq = pickle.dumps(orig.query)
qs = Toy.objects.all()
before = qs._iterable_class
qs.query = pickle.loads(pq)
print("before:", before.__name__, "after:", qs._iterable_class.__name__)
if qs._iterable_class is not ModelIterable or before is not ModelIterable:
    print("FAIL: strategy changed for non-projecting query")
    sys.exit(1)
rows = list(qs)
print("rows types:", [type(r).__name__ for r in rows])
if any(not isinstance(r, Toy) for r in rows):
    print("FAIL: not model instances")
    sys.exit(1)
# pk accessible (Req3.5)
_ = [r.pk for r in rows]
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.3: if the queryset already carries a NON-model strategy and the installed
query projects no fields, the setter must NOT reset it to ModelIterable.
Here we install a plain (non-projecting) query into a .values() queryset."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection
from django.db.models.query import ValuesIterable, ModelIterable


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)

# queryset that already has a non-model strategy
vqs = Toy.objects.values("name")
vqs._iterable_class = ValuesIterable  # ensure
before = vqs._iterable_class
print("before:", before.__name__)

# ordinary, non-projecting query
plain_q = pickle.loads(pickle.dumps(Toy.objects.all().query))
print("installed query values_select:", plain_q.values_select)
vqs.query = plain_q
print("after:", vqs._iterable_class.__name__)
if vqs._iterable_class is ModelIterable:
    print("FAIL: strategy reset to ModelIterable for non-projecting query")
    sys.exit(1)
if vqs._iterable_class is not before:
    print("FAIL: strategy changed unexpectedly")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.1: the setter ALWAYS stores the assigned query as _query, in every case
(projecting and non-projecting)."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection
from django.db.models import Sum


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)

# non-projecting
q1 = pickle.loads(pickle.dumps(Toy.objects.all().query))
qs1 = Toy.objects.all()
qs1.query = q1
assert qs1._query is q1, "non-projecting query not stored identically"
assert qs1.query is q1

# projecting
q2 = pickle.loads(pickle.dumps(Toy.objects.values("name").annotate(t=Sum("qty")).query))
qs2 = Toy.objects.all()
qs2.query = q2
assert qs2._query is q2, "projecting query not stored identically"
assert qs2.query is q2

print("stored identity OK for both cases")
print("OK")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req3.2: the setter must NOT mutate result cache / prefetch state as a side effect.
Also Req3.3/3.5: whole-queryset pickle round-trips and evaluates to model instances."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)
Toy.objects.create(name="b", qty=5)

# Req3.2: setter does not touch _result_cache / _prefetch_related_lookups
qs = Toy.objects.all()
qs._result_cache = "SENTINEL"
qs._prefetch_related_lookups = ("SENTINEL_PREFETCH",)
qs.query = pickle.loads(pickle.dumps(Toy.objects.filter(qty__gt=0).query))
if qs._result_cache != "SENTINEL":
    print("FAIL: setter mutated _result_cache")
    sys.exit(1)
if qs._prefetch_related_lookups != ("SENTINEL_PREFETCH",):
    print("FAIL: setter mutated _prefetch_related_lookups")
    sys.exit(1)
print("result_cache/prefetch preserved")

# Req3.3 / 3.5: whole-queryset pickle round-trip -> model instances w/ pk
whole = pickle.loads(pickle.dumps(Toy.objects.order_by("name")))
rows = list(whole)
if any(not isinstance(r, Toy) for r in rows):
    print("FAIL: whole-qs round-trip not model instances")
    sys.exit(1)
pks = [r.pk for r in rows]
names = [r.name for r in rows]
print("round-trip rows pks:", pks, "names:", names)
if names != ["a", "b"]:
    print("FAIL: wrong round-trip results")
    sys.exit(1)
print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1.3: pickle a .values('name').annotate(Sum) query,
install via the query setter, evaluate. Must yield dict rows and not crash.
HOLDS on patched, FAILS at base (base raises / returns wrong type)."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection
from django.db.models import Sum


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)
Toy.objects.create(name="a", qty=2)
Toy.objects.create(name="b", qty=5)

orig = Toy.objects.values("name").annotate(total=Sum("qty")).order_by("name")
expected = list(orig)
print("expected:", expected)

pq = pickle.dumps(orig.query)
qs = Toy.objects.all()
try:
    qs.query = pickle.loads(pq)
    got = list(qs)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("got:", got)

if any(not isinstance(r, dict) for r in got):
    print("FAIL: non-dict rows")
    sys.exit(1)
if got != expected:
    print("FAIL: rows differ from original")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probes -> requirement criteria:
- probe_1 (POSITIVE CONTROL): Req1.3 — pickle .values('name').annotate(Sum) query, install via setter, evaluate; must yield dict rows == original and not raise. HOLDS patched; at base VIOLATED (AttributeError: 'NoneType' object has no attribute 'attname'). Discriminates.
- probe_2: Req1.1+Req1.4 — installing a query from any .values_list variant (positional/flat/named) sets _iterable_class=ValuesIterable and produces dict rows. HOLDS patched.
- probe_3: Req2.1+Req2.2 (+3.5) — installing an ordinary non-projecting query leaves ModelIterable and yields model instances with accessible pk. HOLDS patched.
- probe_4: Req2.3 — a queryset already carrying a non-model strategy (ValuesIterable) is NOT reset to ModelIterable when a non-projecting query is installed. HOLDS patched.
- probe_5: Req3.1 — setter always stores assigned query as _query (identity) in both projecting and non-projecting cases. HOLDS patched.
- probe_6: Req3.2+Req3.3+Req3.5 — setter does not mutate _result_cache/_prefetch_related_lookups; whole-queryset pickle round-trips to correct model instances. HOLDS patched.

Candidate wrong patches (both REJECTED by the suite -> suite discriminates wrong impls):
- weak_valueslist.diff: sets ValuesListIterable instead of ValuesIterable. REJECTED by probe_1 (non-dict rows) and probe_2 (not ValuesIterable). This is the lazy misreading and would produce tuples/flat/named rows, failing the hidden tests that expect dicts.
- weak_unconditional.diff: always sets ValuesIterable ignoring the values_select guard. REJECTED by probe_3 (strategy changed for non-projecting query -> breaks normal model-instance querysets).

No requirement-conforming alternative patch found that would fail the hidden tests: the gold guard `if value.values_select: self._iterable_class = ValuesIterable` is the minimal behavior all probes pin. Requirements faithfully mirror gold behavior.

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
"""Positive control + Req1.3: pickle a .values('name').annotate(Sum) query,
install via the query setter, evaluate. Must yield dict rows and not crash.
HOLDS on patched, FAILS at base (base raises / returns wrong type)."""
import pickle, sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
django.setup()
from django.db import models, connection
from django.db.models import Sum


class Toy(models.Model):
    name = models.CharField(max_length=50)
    qty = models.IntegerField(default=0)
    class Meta:
        app_label = "contenttypes"


with connection.schema_editor() as se:
    se.create_model(Toy)
Toy.objects.create(name="a", qty=1)
Toy.objects.create(name="a", qty=2)
Toy.objects.create(name="b", qty=5)

orig = Toy.objects.values("name").annotate(total=Sum("qty")).order_by("name")
expected = list(orig)
print("expected:", expected)

pq = pickle.dumps(orig.query)
qs = Toy.objects.all()
try:
    qs.query = pickle.loads(pq)
    got = list(qs)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("got:", got)

if any(not isinstance(r, dict) for r in got):
    print("FAIL: non-dict rows")
    sys.exit(1)
if got != expected:
    print("FAIL: rows differ from original")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probes -> requirement criteria:
- probe_1 (POSITIVE CONTROL): Req1.3 — pickle .values('name').annotate(Sum) query, install via setter, evaluate; must yield dict rows == original and not raise. HOLDS patched; at base VIOLATED (AttributeError: 'NoneType' object has no attribute 'attname'). Discriminates.
- probe_2: Req1.1+Req1.4 — installing a query from any .values_list variant (positional/flat/named) sets _iterable_class=ValuesIterable and produces dict rows. HOLDS patched.
- probe_3: Req2.1+Req2.2 (+3.5) — installing an ordinary non-projecting query leaves ModelIterable and yields model instances with accessible pk. HOLDS patched.
- probe_4: Req2.3 — a queryset already carrying a non-model strategy (ValuesIterable) is NOT reset to ModelIterable when a non-projecting query is installed. HOLDS patched.
- probe_5: Req3.1 — setter always stores assigned query as _query (identity) in both projecting and non-projecting cases. HOLDS patched.
- probe_6: Req3.2+Req3.3+Req3.5 — setter does not mutate _result_cache/_prefetch_related_lookups; whole-queryset pickle round-trips to correct model instances. HOLDS patched.

Candidate wrong patches (both REJECTED by the suite -> suite discriminates wrong impls):
- weak_valueslist.diff: sets ValuesListIterable instead of ValuesIterable. REJECTED by probe_1 (non-dict rows) and probe_2 (not ValuesIterable). This is the lazy misreading and would produce tuples/flat/named rows, failing the hidden tests that expect dicts.
- weak_unconditional.diff: always sets ValuesIterable ignoring the values_select guard. REJECTED by probe_3 (strategy changed for non-projecting query -> breaks normal model-instance querysets).

No requirement-conforming alternative patch found that would fail the hidden tests: the gold guard `if value.values_select: self._iterable_class = ValuesIterable` is the minimal behavior all probes pin. Requirements faithfully mirror gold behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior at the correct boundary: values_select non-empty <-> set ValuesIterable, else leave _iterable_class untouched. Requirement 1.4's claim that ANY values_list variant becomes dict-producing (not tuple/flat/named) is a deliberately correct reflection of the patch always assigning ValuesIterable (a documented quirk of the fix, not an invention). R3 regression clauses are standard preservation statements consistent with a one-line additive change. No requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes to real Django internals (Query.values_select, QuerySet._iterable_class, ValuesIterable/ModelIterable, ValuesListIterable variants) — all pre-existing framework identifiers, not fix-invented ones, so naming them is legitimate localization. The core behavior (field-projecting pickled query must yield dict rows; non-projecting queries preserve strategy; query is always stored) is a faithful behavioral translation of the gold edit (`if value.values_select: self._iterable_class = ValuesIterable`), which is exactly what a spec should do.

Borderline items I checked and cleared:
(1) Req 1.4 enumerates the three values_list forms '(positional, flat=True, or named=True)', which mirrors the test's three subTest cases in test_annotation_values_list. However these are the complete, canonical set of values_list variants in Django (ValuesListIterable/FlatValuesListIterable/NamedValuesListIterable) — describing 'values_list collapses to dict rows' necessarily lists them; it is the behavioral domain, not an arbitrary test-specific parametrization. This behavior is also the natural side-effect of the gold patch, so it's describing fix behavior rather than transmitting the test.
(2) Req 1.3 uses '.values('name')' where the PUBLIC problem_statement example uses '.values('material')' and the hidden test uses '.values('name')'. This is a mild echo of the test's field choice, but 'name' is a generic field that also exists in the problem_statement's model, and no test-specific literals leak: the document never exposes the test's asserted values ({'name': 'test'}, latest_time=Max('when')), the test/class/method names, the file path (tests/queryset_pickle/tests.py), or any quoted test/gold code.

No test names/paths/ids, no quoted test or gold source, no fix-invented identifiers, and no case enumeration that reconstructs the hidden tests beyond describing behavior. Not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
