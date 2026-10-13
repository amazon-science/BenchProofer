# P2 adversarial audit — django__django-13590

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
"""Req 2.1/2.2 (POSITIVE CONTROL): resolve_lookup_value on a namedtuple value
rebuilds a namedtuple of the same type WITHOUT raising TypeError."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models
from collections import namedtuple

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

from django.db.models.sql.query import Query
q = Query(Thing)
NT = namedtuple("NT", ["lo", "hi"])
val = NT(1, 5)
try:
    out = q.resolve_lookup_value(val, can_reuse=set(), allow_joins=True)
except TypeError as e:
    print("VIOLATION: TypeError raised:", e)
    sys.exit(1)
print("observed:", repr(out), "type:", type(out).__name__)
assert type(out) is NT, f"type not preserved: {type(out)}"
assert tuple(out) == (1, 5), f"values wrong: {tuple(out)}"
assert out.lo == 1 and out.hi == 5, "fields wrong"
print("OK namedtuple preserved")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2/1.3 (plain tuple regression): plain tuple value rebuilt as plain
tuple, same length/order/elements."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

from django.db.models.sql.query import Query
q = Query(Thing)
val = (3, 7, 11)
out = q.resolve_lookup_value(val, can_reuse=set(), allow_joins=True)
print("observed:", repr(out), "type:", type(out).__name__)
assert type(out) is tuple, f"type not plain tuple: {type(out)}"
assert out == (3, 7, 11), f"values wrong: {out}"
print("OK plain tuple preserved")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2/1.3 (plain list regression): plain list value rebuilt as list."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

from django.db.models.sql.query import Query
q = Query(Thing)
val = [10, 20, 30]
out = q.resolve_lookup_value(val, can_reuse=set(), allow_joins=True)
print("observed:", repr(out), "type:", type(out).__name__)
assert type(out) is list, f"type not list: {type(out)}"
assert out == [10, 20, 30], f"values wrong: {out}"
print("OK plain list preserved")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.4/3.1: an element that is a resolvable expression (F()) inside a
tuple is replaced by its resolved form (per-element recursion)."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models
from django.db.models import F
from django.db.models.expressions import Col

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

from django.db.models.sql.query import Query
q = Query(Thing)
val = (F("num"), 100)
out = q.resolve_lookup_value(val, can_reuse=set(), allow_joins=True)
print("observed:", repr(out), "type:", type(out).__name__)
assert type(out) is tuple, f"type wrong: {type(out)}"
assert len(out) == 2
# F('num') should be resolved into an expression (not the raw F instance).
assert not isinstance(out[0], F), "F element was not resolved"
assert hasattr(out[0], "resolve_expression") or isinstance(out[0], Col), \
    f"element0 not an expression: {out[0]!r}"
assert out[1] == 100, f"element1 changed: {out[1]}"
print("OK expression element resolved in place")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2: a value that is neither expression nor list/tuple is returned
unchanged (e.g. an int, a str, a set)."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

from django.db.models.sql.query import Query
q = Query(Thing)
for v in [42, "hello", {1, 2, 3}]:
    out = q.resolve_lookup_value(v, can_reuse=set(), allow_joins=True)
    print("in:", repr(v), "-> out:", repr(out))
    assert out is v or out == v, f"value changed: {v!r} -> {out!r}"
    assert type(out) is type(v), f"type changed: {type(v)} -> {type(out)}"
print("OK scalar/other values unchanged")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 2.3 (end-to-end): filtering with a __range lookup whose value is a
2-element namedtuple executes AND returns exactly the inclusive-range rows."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models, connection
from collections import namedtuple

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

with connection.schema_editor() as se:
    se.create_model(Thing)

for n in [1, 3, 5, 7, 9]:
    Thing.objects.create(num=n)

NT = namedtuple("NT", ["lo", "hi"])
qs = Thing.objects.filter(num__range=NT(3, 7)).order_by("num")
got = list(qs.values_list("num", flat=True))
print("observed rows:", got)
assert got == [3, 5, 7], f"wrong rows: {got}"
print("OK range with namedtuple returns inclusive range")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 2.1/2.2 (POSITIVE CONTROL): resolve_lookup_value on a namedtuple value
rebuilds a namedtuple of the same type WITHOUT raising TypeError."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models
from collections import namedtuple

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

from django.db.models.sql.query import Query
q = Query(Thing)
NT = namedtuple("NT", ["lo", "hi"])
val = NT(1, 5)
try:
    out = q.resolve_lookup_value(val, can_reuse=set(), allow_joins=True)
except TypeError as e:
    print("VIOLATION: TypeError raised:", e)
    sys.exit(1)
print("observed:", repr(out), "type:", type(out).__name__)
assert type(out) is NT, f"type not preserved: {type(out)}"
assert tuple(out) == (1, 5), f"values wrong: {tuple(out)}"
assert out.lo == 1 and out.hi == 5, "fields wrong"
print("OK namedtuple preserved")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13590: fix rebuilds list/tuple lookup values via type(value)(...) unless the type is a namedtuple (hasattr _make), in which case it uses type_(*values).

Probes (all HOLD on gold-patched tree; runner re-executes):
- probe_1 (Req 2.1/2.2, POSITIVE CONTROL): resolve_lookup_value(namedtuple NT(1,5)) returns NT of same type without TypeError. HOLDS patched (NT(lo=1,hi=5)); VIOLATED at base (TypeError: __new__() missing 1 required positional argument: 'hi'). Discriminates base vs patched.
- probe_2 (Req 1.2/1.3/3.3, plain-tuple regression): (3,7,11) -> plain tuple (3,7,11). HOLDS.
- probe_3 (Req 1.2/1.3/3.3, plain-list regression): [10,20,30] -> list. HOLDS.
- probe_4 (Req 1.1/1.4/3.1, per-element expression resolution): (F('num'),100) -> element0 resolved to Col expression, element1 unchanged, type tuple. HOLDS.
- probe_5 (Req 3.2, non-container passthrough): int/str/set returned unchanged, same type. HOLDS.
- probe_6 (Req 2.3, end-to-end): filter(num__range=NT(3,7)) over rows [1,3,5,7,9] returns exactly [3,5,7]. HOLDS patched; VIOLATED at base.

Candidate wrong-fix (weak.diff): replaces `type(value)(...)` with `tuple(...)`. This is the lazy fix that avoids the namedtuple TypeError by always producing a plain tuple. REJECTED by the suite: probe_1 VIOLATED (namedtuple type lost) and probe_3 VIOLATED (list input becomes tuple). probe_2/4/5/6 still hold, confirming the suite pinpoints exactly the type-preservation + namedtuple criteria that this weak reading violates. Demonstrates the probe suite discriminates a requirements-underconforming implementation.

Probe env note: each probe builds a throwaway on-disk 'probeapp' package under a tempdir and adds it to sys.path so Django app loading (needs filesystem __path__ and real __spec__) works inside the py3.6 testbed image.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary (namedtuple), and 'SHALL keep' regressions all hold on patched; positive control discriminates base vs patched; >=1 wrong-fix candidate exercised and REJECTED.

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
"""Req 2.1/2.2 (POSITIVE CONTROL): resolve_lookup_value on a namedtuple value
rebuilds a namedtuple of the same type WITHOUT raising TypeError."""
import sys, types
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["probeapp"], USE_TZ=False)
import os, tempfile
_d = tempfile.mkdtemp()
os.makedirs(os.path.join(_d, "probeapp"))
open(os.path.join(_d, "probeapp", "__init__.py"), "w").close()
open(os.path.join(_d, "probeapp", "models.py"), "w").close()
sys.path.insert(0, _d)
django.setup()
from django.db import models
from collections import namedtuple

class Thing(models.Model):
    num = models.IntegerField()
    class Meta: app_label = "probeapp"

from django.db.models.sql.query import Query
q = Query(Thing)
NT = namedtuple("NT", ["lo", "hi"])
val = NT(1, 5)
try:
    out = q.resolve_lookup_value(val, can_reuse=set(), allow_joins=True)
except TypeError as e:
    print("VIOLATION: TypeError raised:", e)
    sys.exit(1)
print("observed:", repr(out), "type:", type(out).__name__)
assert type(out) is NT, f"type not preserved: {type(out)}"
assert tuple(out) == (1, 5), f"values wrong: {tuple(out)}"
assert out.lo == 1 and out.hi == 5, "fields wrong"
print("OK namedtuple preserved")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13590: fix rebuilds list/tuple lookup values via type(value)(...) unless the type is a namedtuple (hasattr _make), in which case it uses type_(*values).

Probes (all HOLD on gold-patched tree; runner re-executes):
- probe_1 (Req 2.1/2.2, POSITIVE CONTROL): resolve_lookup_value(namedtuple NT(1,5)) returns NT of same type without TypeError. HOLDS patched (NT(lo=1,hi=5)); VIOLATED at base (TypeError: __new__() missing 1 required positional argument: 'hi'). Discriminates base vs patched.
- probe_2 (Req 1.2/1.3/3.3, plain-tuple regression): (3,7,11) -> plain tuple (3,7,11). HOLDS.
- probe_3 (Req 1.2/1.3/3.3, plain-list regression): [10,20,30] -> list. HOLDS.
- probe_4 (Req 1.1/1.4/3.1, per-element expression resolution): (F('num'),100) -> element0 resolved to Col expression, element1 unchanged, type tuple. HOLDS.
- probe_5 (Req 3.2, non-container passthrough): int/str/set returned unchanged, same type. HOLDS.
- probe_6 (Req 2.3, end-to-end): filter(num__range=NT(3,7)) over rows [1,3,5,7,9] returns exactly [3,5,7]. HOLDS patched; VIOLATED at base.

Candidate wrong-fix (weak.diff): replaces `type(value)(...)` with `tuple(...)`. This is the lazy fix that avoids the namedtuple TypeError by always producing a plain tuple. REJECTED by the suite: probe_1 VIOLATED (namedtuple type lost) and probe_3 VIOLATED (list input becomes tuple). probe_2/4/5/6 still hold, confirming the suite pinpoints exactly the type-preservation + namedtuple criteria that this weak reading violates. Demonstrates the probe suite discriminates a requirements-underconforming implementation.

Probe env note: each probe builds a throwaway on-disk 'probeapp' package under a tempdir and adds it to sys.path so Django app loading (needs filesystem __path__ and real __spec__) works inside the py3.6 testbed image.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary (namedtuple), and 'SHALL keep' regressions all hold on patched; positive control discriminates base vs patched; >=1 wrong-fix candidate exercised and REJECTED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces `return type(value)(gen)` with a namedtuple-aware split: `if hasattr(type_, '_make'): return type_(*values); return type_(values)`. The requirements pin exactly this changed observable behavior — the whole list/tuple branch plus namedtuple special-case and the expression-precedence guard — not a narrow slice. Probes run in the instance image: patched HOLDS (exit 0), base namedtuple path raises the described TypeError.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements are a faithful behavioral translation whose entire scope is already public in problem_statement: the module/class/method (django.db.models.sql.query.Query.resolve_lookup_value), the named-2-tuple-as-__range-argument scenario, the TypeError on missing positional args, and the '* expand the contents of the iterator into the constructor' fix approach are all stated there. No hidden test artifacts leak: the F2P test name (test_range_lookup_namedtuple), class (IterableLookupInnerExpressionsTests), path (tests/expressions/tests.py), and all test literals (EmployeeRange, minimum=51/maximum=100, Company/num_employees, self.c5, the assertSequenceEqual expectation) are absent. Req 2.3's 'range bounds / inclusive range' is generic behavior, not the test's specific values. Borderline item: Req 2.4 describes namedtuple detection 'by the presence of the named-tuple factory method used to build an instance from an iterable', which corresponds to the gold's hasattr(type_, '_make'); however _make is a public stdlib namedtuple API (not a fix-invented identifier), it is paraphrased rather than quoted, and the 'don't hard-code classes' framing is a legitimate behavioral requirement consistent with the publicly-stated *-expansion fix. No verbatim gold lines, no parametrization-mirroring enumeration. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
