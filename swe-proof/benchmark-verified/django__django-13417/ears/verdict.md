# P2 adversarial audit — django__django-13417

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
"""Req1 crit2: aggregate annotate() on model with Meta.ordering -> ordered False.
Also positive control (core fixed behavior)."""
import sys
import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.db.models import Count


class OrderedModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"
        ordering = ["name"]


qs = OrderedModel.objects.annotate(num=Count("pk"))
observed = qs.ordered
print("aggregate-annotated ordered =", observed)
print("group_by =", qs.query.group_by)
sys.exit(0 if observed is False else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1 crit3: values(...).annotate(...) grouped query on ordered model -> ordered False."""
import sys
import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.db.models import Count


class OrderedModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"
        ordering = ["name"]


qs = OrderedModel.objects.values("name").annotate(num=Count("pk"))
observed = qs.ordered
print("values().annotate() ordered =", observed)
print("group_by =", qs.query.group_by)
sys.exit(0 if observed is False else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2 crit1&2: explicit order_by on aggregated qs -> ordered True (overrides grouped default)."""
import sys
import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.db.models import Count


class OrderedModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"
        ordering = ["name"]


qs = OrderedModel.objects.annotate(num=Count("pk"))
base = qs.ordered
ordered_qs = qs.order_by("name")
observed = ordered_qs.ordered
print("aggregated ordered =", base, "; after order_by ordered =", observed)
sys.exit(0 if (base is False and observed is True) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2 crit3 + Req3 crit2/crit1: extra(order_by), non-grouped default ordering, empty qs.
Regression 'SHALL keep' criteria."""
import sys
import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
django.setup()

from django.db import models


class OrderedModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"
        ordering = ["name"]


ok = True

# Req3 crit2: non-grouped, default ordering in force, Meta.ordering -> True
r2 = OrderedModel.objects.all().ordered
print("non-grouped default-ordering ordered =", r2, "(expect True)")
ok &= (r2 is True)

# Req2 crit3: extra order_by -> True
r_extra = OrderedModel.objects.all().extra(order_by=["id"]).ordered
print("extra(order_by) ordered =", r_extra, "(expect True)")
ok &= (r_extra is True)

# Req3 crit1: EmptyQuerySet -> True
r_empty = OrderedModel.objects.none().ordered
print("EmptyQuerySet ordered =", r_empty, "(expect True)")
ok &= (r_empty is True)

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3 crit3 & crit4: non-grouped model without Meta.ordering -> False;
grouped without default ordering -> False; order_by() cleared -> False."""
import sys
import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.db.models import Count


class OrderedModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"
        ordering = ["name"]


class Unordered(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"


ok = True

# Req3 crit3: non-grouped, no Meta.ordering -> False
r = Unordered.objects.all().ordered
print("non-grouped, no Meta.ordering ordered =", r, "(expect False)")
ok &= (r is False)

# Req3 crit3: cleared default ordering via order_by() -> False
r2 = OrderedModel.objects.all().order_by().ordered
print("order_by() cleared ordered =", r2, "(expect False)")
ok &= (r2 is False)

# Req3 crit4: grouped (annotate) on model WITHOUT default ordering -> False
r3 = Unordered.objects.annotate(num=Count("pk")).ordered
print("grouped, no default ordering ordered =", r3, "(expect False)")
ok &= (r3 is False)

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req1 crit2: aggregate annotate() on model with Meta.ordering -> ordered False.
Also positive control (core fixed behavior)."""
import sys
import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.db.models import Count


class OrderedModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"
        ordering = ["name"]


qs = OrderedModel.objects.annotate(num=Count("pk"))
observed = qs.ordered
print("aggregate-annotated ordered =", observed)
print("group_by =", qs.query.group_by)
sys.exit(0 if observed is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements target QuerySet.ordered for GROUP BY queries. 5 probes cover: probe_1 (Req1.2 aggregate annotate on Meta.ordering model -> False; POSITIVE CONTROL: holds patched, FAILS at base where ordered=True), probe_2 (Req1.3 values().annotate() grouped -> False; also fails at base), probe_3 (Req2.1/2.2 explicit order_by on aggregated qs -> True AND aggregated alone -> False), probe_4 (Req2.3 extra(order_by) -> True; Req3.2 non-grouped default ordering -> True; Req3.1 EmptyQuerySet -> True), probe_5 (Req3.3 no Meta.ordering -> False, order_by() cleared -> False; Req3.4 grouped w/o default ordering -> False). All 5 HOLD on gold-patched tree. Positive control discriminates (patched=holds, base=violated). Candidate weak_A (a plausible lazy fix: `if self.query.group_by: return False` placed BEFORE the explicit-order_by check) is REJECTED by probe_3 because it makes an explicitly order_by()'d grouped queryset report ordered=False, violating Req2.1/2.2. This demonstrates the suite discriminates a wrong implementation that a weak reading of the requirements might permit. No TOO-WEAK finding: the one candidate that a naive reading permits is caught. Verdict SOUND.

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
"""Req1 crit2: aggregate annotate() on model with Meta.ordering -> ordered False.
Also positive control (core fixed behavior)."""
import sys
import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=True,
)
django.setup()

from django.db import models
from django.db.models import Count


class OrderedModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "probeapp"
        ordering = ["name"]


qs = OrderedModel.objects.annotate(num=Count("pk"))
observed = qs.ordered
print("aggregate-annotated ordered =", observed)
print("group_by =", qs.query.group_by)
sys.exit(0 if observed is False else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements target QuerySet.ordered for GROUP BY queries. 5 probes cover: probe_1 (Req1.2 aggregate annotate on Meta.ordering model -> False; POSITIVE CONTROL: holds patched, FAILS at base where ordered=True), probe_2 (Req1.3 values().annotate() grouped -> False; also fails at base), probe_3 (Req2.1/2.2 explicit order_by on aggregated qs -> True AND aggregated alone -> False), probe_4 (Req2.3 extra(order_by) -> True; Req3.2 non-grouped default ordering -> True; Req3.1 EmptyQuerySet -> True), probe_5 (Req3.3 no Meta.ordering -> False, order_by() cleared -> False; Req3.4 grouped w/o default ordering -> False). All 5 HOLD on gold-patched tree. Positive control discriminates (patched=holds, base=violated). Candidate weak_A (a plausible lazy fix: `if self.query.group_by: return False` placed BEFORE the explicit-order_by check) is REJECTED by probe_3 because it makes an explicitly order_by()'d grouped queryset report ordered=False, violating Req2.1/2.2. This demonstrates the suite discriminates a wrong implementation that a weak reading of the requirements might permit. No TOO-WEAK finding: the one candidate that a naive reading permits is caught. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch: in django/db/models/query.py the `ordered` property's third branch becomes `default_ordering and get_meta().ordering and not group_by`. Probed patched behavior (custom app model with Meta.ordering=['name']): plain qs -> True (Req 3.2); annotate(Count('pk')) -> False (Req 1.2); values('name').annotate(Count) -> False (Req 1.3); annotate(Count).order_by('name') -> True (Req 2.1/2.2); model w/o Meta.ordering plain -> False (Req 3.3); model w/o ordering + annotate -> False (Req 3.4); none() EmptyQuerySet -> True (Req 3.1). All 7 predictions held (exit 0). Req 1.1/1.4 correctly identify group_by as the grouping signal; Req 2.3 (extra_order_by) preserved by untouched second branch; Req 3.5 forbids extra conditions, matching that the patch adds only the group_by check. No modeling-boundary error, no invented behavior, no over/under-mandate found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to the ordered property in django/db/models/query.py and names self.query.group_by as the grouping signal — but group_by is a pre-existing Query attribute, not a fix-invented identifier, and localization is legitimate. The two FAIL_TO_PASS tests use annotate(Count('pk')) and values('name').annotate(Count('pk')); Req 1.2 ('count over the primary key') is already public in the problem_statement's worked example (Foo.objects.annotate(Count("pk"))), and Req 1.3 abstracts the values().annotate() form without the verbatim field name — it describes a standard GROUP-BY idiom behaviorally rather than transcribing the test. No test names/paths/ids, no quoted test or gold code, no verbatim gold lines. The case enumeration tracks the behavioral decomposition (grouped vs non-grouped, explicit/extra ordering, empty queryset) which is also derivable from the public source of the ordered property, not from the hidden tests. Translating test assertions into behavioral requirements is the intended purpose; nothing here reconstructs the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
