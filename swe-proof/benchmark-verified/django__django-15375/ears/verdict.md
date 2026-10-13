# P2 adversarial audit — django__django-15375

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
"""POSITIVE CONTROL. Req 1.4/1.5/1: a terminal aggregate carrying a `default`
applied AFTER annotate() must succeed and return the plain integer sum (not
raise a DB error). Crashes at base (empty select list), holds when patched."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Sum, F

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
Thing.objects.bulk_create([Thing(num=n) for n in (10, 30)])  # sum = 40

try:
    res = Thing.objects.annotate(dbl=F("num") * 2).aggregate(value=Sum("num", default=0))
except Exception as e:
    print(f"OBSERVED: aggregate() after annotate() raised {type(e).__name__}: {e}")
    sys.exit(1)
print(f"OBSERVED: result={res}")
sys.exit(0 if res.get("value") == 40 else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2: an aggregate carrying a `default` resolved as TERMINAL (summarize=True)
must yield a Coalesce wrapper whose is_summary is True."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

agg = Sum("num", default=0)
q = Thing.objects.all().query
resolved = agg.resolve_expression(q, allow_joins=True, reuse=None, summarize=True)
print(f"OBSERVED type={type(resolved).__name__} is_summary={getattr(resolved,'is_summary',None)}")
ok = isinstance(resolved, Coalesce) and getattr(resolved, "is_summary", None) is True
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 1.1: an aggregate carrying a `default` resolved as NON-TERMINAL
(summarize=False, as annotate() does) must yield a Coalesce wrapper whose
is_summary is False (equal to the wrapped aggregate's). This is the leg that a
hardcoded is_summary=True 'fix' gets wrong."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

agg = Sum("num", default=0)
q = Thing.objects.all().query
resolved = agg.resolve_expression(q, allow_joins=True, reuse=None, summarize=False)
inner = resolved.get_source_expressions()[0]
print(f"OBSERVED type={type(resolved).__name__} wrapper.is_summary="
      f"{getattr(resolved,'is_summary',None)} inner.is_summary={getattr(inner,'is_summary',None)}")
ok = (isinstance(resolved, Coalesce)
      and getattr(resolved, "is_summary", None) == getattr(inner, "is_summary", None)
      and getattr(resolved, "is_summary", None) is False)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 3.2 (regression): when NO default is supplied, resolve_expression
returns the BARE aggregate (not wrapped in Coalesce), and a terminal aggregate
WITHOUT default after annotate() still works, returning the plain sum."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Sum, F
from django.db.models.functions import Coalesce

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

# tree shape: no default -> bare aggregate
agg = Sum("num")
q = Thing.objects.all().query
resolved = agg.resolve_expression(q, allow_joins=True, reuse=None, summarize=True)
is_bare = isinstance(resolved, Sum) and not isinstance(resolved, Coalesce)
print(f"OBSERVED no-default resolved type={type(resolved).__name__} bare={is_bare}")

with connection.schema_editor() as se:
    se.create_model(Thing)
Thing.objects.bulk_create([Thing(num=n) for n in (10, 30)])
res = Thing.objects.annotate(dbl=F("num") * 2).aggregate(value=Sum("num"))
print(f"OBSERVED no-default aggregate-after-annotate result={res}")
sys.exit(0 if (is_bare and res.get("value") == 40) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 3.4 (regression): a terminal aggregate with a `default`, applied
DIRECTLY (no preceding annotation), returns the sum on the non-empty case and
the default on the empty case."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Sum

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)

# empty set -> default returned
empty = Thing.objects.aggregate(value=Sum("num", default=99))
# non-empty -> real sum
Thing.objects.bulk_create([Thing(num=n) for n in (10, 30)])
nonempty = Thing.objects.aggregate(value=Sum("num", default=99))
print(f"OBSERVED empty={empty} nonempty={nonempty}")
sys.exit(0 if (empty.get("value") == 99 and nonempty.get("value") == 40) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.3 (regression): an annotation with a non-aggregate expression added,
then a SEPARATE aggregate without a default applied after it, computes over the
underlying rows and matches the annotation-free result."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Sum, F

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
Thing.objects.bulk_create([Thing(num=n) for n in (10, 30)])

with_ann = Thing.objects.annotate(dbl=F("num") * 2).aggregate(value=Sum("num", default=0))
without_ann = Thing.objects.aggregate(value=Sum("num", default=0))
print(f"OBSERVED with_ann={with_ann} without_ann={without_ann}")
sys.exit(0 if (with_ann.get("value") == 40 and without_ann.get("value") == 40) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL. Req 1.4/1.5/1: a terminal aggregate carrying a `default`
applied AFTER annotate() must succeed and return the plain integer sum (not
raise a DB error). Crashes at base (empty select list), holds when patched."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Sum, F

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
Thing.objects.bulk_create([Thing(num=n) for n in (10, 30)])  # sum = 40

try:
    res = Thing.objects.annotate(dbl=F("num") * 2).aggregate(value=Sum("num", default=0))
except Exception as e:
    print(f"OBSERVED: aggregate() after annotate() raised {type(e).__name__}: {e}")
    sys.exit(1)
print(f"OBSERVED: result={res}")
sys.exit(0 if res.get("value") == 40 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: Aggregate.resolve_expression wraps a default-carrying aggregate in Coalesce and sets coalesce.is_summary = c.is_summary (propagate the wrapped aggregate's terminal marker). Bug: wrapper defaulted to is_summary=False, so aggregate()-after-annotate() was not lifted into the outer SELECT and emitted invalid 'SELECT FROM (...)'.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.4/1.5): aggregate(Sum(default=0)) after annotate() succeeds and returns integer sum 40. BASE: VIOLATED (OperationalError: near "FROM": syntax error) -> discriminates. PATCHED: HOLDS.
- probe_2 (Req 1.2): terminal resolve (summarize=True) yields Coalesce with is_summary=True. PATCHED HOLDS; BASE VIOLATED (is_summary=False).
- probe_3 (Req 1.3/1.1): non-terminal resolve (summarize=False, annotate case) yields Coalesce with is_summary=False equal to wrapped aggregate. PATCHED HOLDS. This is the discriminating leg vs the wrong fix.
- probe_4 (Req 2.1/3.2): no default -> bare aggregate (not Coalesce); no-default aggregate-after-annotate still returns 40.
- probe_5 (Req 3.1/3.4): direct terminal aggregate with default returns default (99) on empty set, real sum (40) on non-empty.
- probe_6 (Req 3.3): unrelated non-aggregate annotation does not change the aggregate result (40 with and without annotation).

CANDIDATE PATCH exercised & REJECTED: weak.diff sets coalesce.is_summary = True unconditionally (the fix proposed verbatim in the issue's hints_text). It passes probe_1,2,4,5,6 but is REJECTED by probe_3 (wrapper.is_summary=True != inner.is_summary=False, violates Req 1.3/1.1). This demonstrates the suite discriminates a wrong reading of the requirements. The requirements correctly demand PROPAGATION of the marker, not hardcoding, matching the gold patch.

All needed runs completed. 6 distinct probes hold patched; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and rejected. Verdict SOUND.

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
"""POSITIVE CONTROL. Req 1.4/1.5/1: a terminal aggregate carrying a `default`
applied AFTER annotate() must succeed and return the plain integer sum (not
raise a DB error). Crashes at base (empty select list), holds when patched."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes"], USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Sum, F

class Thing(models.Model):
    num = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
Thing.objects.bulk_create([Thing(num=n) for n in (10, 30)])  # sum = 40

try:
    res = Thing.objects.annotate(dbl=F("num") * 2).aggregate(value=Sum("num", default=0))
except Exception as e:
    print(f"OBSERVED: aggregate() after annotate() raised {type(e).__name__}: {e}")
    sys.exit(1)
print(f"OBSERVED: result={res}")
sys.exit(0 if res.get("value") == 40 else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: Aggregate.resolve_expression wraps a default-carrying aggregate in Coalesce and sets coalesce.is_summary = c.is_summary (propagate the wrapped aggregate's terminal marker). Bug: wrapper defaulted to is_summary=False, so aggregate()-after-annotate() was not lifted into the outer SELECT and emitted invalid 'SELECT FROM (...)'.

Probes (all HOLD on gold-patched tree):
- probe_1 (POSITIVE CONTROL, Req 1.4/1.5): aggregate(Sum(default=0)) after annotate() succeeds and returns integer sum 40. BASE: VIOLATED (OperationalError: near "FROM": syntax error) -> discriminates. PATCHED: HOLDS.
- probe_2 (Req 1.2): terminal resolve (summarize=True) yields Coalesce with is_summary=True. PATCHED HOLDS; BASE VIOLATED (is_summary=False).
- probe_3 (Req 1.3/1.1): non-terminal resolve (summarize=False, annotate case) yields Coalesce with is_summary=False equal to wrapped aggregate. PATCHED HOLDS. This is the discriminating leg vs the wrong fix.
- probe_4 (Req 2.1/3.2): no default -> bare aggregate (not Coalesce); no-default aggregate-after-annotate still returns 40.
- probe_5 (Req 3.1/3.4): direct terminal aggregate with default returns default (99) on empty set, real sum (40) on non-empty.
- probe_6 (Req 3.3): unrelated non-aggregate annotation does not change the aggregate result (40 with and without annotation).

CANDIDATE PATCH exercised & REJECTED: weak.diff sets coalesce.is_summary = True unconditionally (the fix proposed verbatim in the issue's hints_text). It passes probe_1,2,4,5,6 but is REJECTED by probe_3 (wrapper.is_summary=True != inner.is_summary=False, violates Req 1.3/1.1). This demonstrates the suite discriminates a wrong reading of the requirements. The requirements correctly demand PROPAGATION of the marker, not hardcoding, matching the gold patch.

All needed runs completed. 6 distinct probes hold patched; positive control fails at base and holds patched (prepatch reproduced); >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The change is a single one-line flag propagation; requirements model the actual observable boundary (is_summary flag on the resolved wrapper AND the end-to-end aggregate-after-annotate result/SQL). Req 2.2 (reset wrapped default) and 2.3 (output_field from wrapped agg) reflect pre-existing patch context lines and remain true. No requirement mandates behavior the code lacks, forbids behavior it has, or invents unseen behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally using only public Django symbols (is_summary, Coalesce, resolve_expression, aggregates.py, Query.get_aggregation) — all pre-existing, legitimate localization, not fix-invented identifiers. The crash-after-annotate scenario, invalid 'SELECT FROM (...)' SQL, and Coalesce-wrapping are all present in the public problem_statement. No hidden-test content is transmitted: no test names (test_aggregation_default_after_annotation, test_aggregation_default_not_in_aggregate), no test file path (tests/aggregation/tests.py), no parametrization ids, and no concrete gold fixtures/values (40, 20, Publisher, num_awards, book__rating, 2.5, F('num_awards')*2). Req 1.4 and Req 3.3 do parallel the two hidden tests, but only as generic behavioral requirements (integer sum over rows; unrelated non-aggregate annotation + separate aggregate) — behavioral translation without the tests' concrete data, which is the intended purpose, not test reconstruction. The gold's is_summary propagation is stated as a required semantic on a documented existing attribute, not quoted gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
