# P2 adversarial audit — django__django-13028

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Positive control: Req2.1/2.2 — a value that does NOT participate in the
# expression-resolution protocol (no resolve_expression) but carries a falsey
# `filterable` attribute must NOT be rejected. HOLDS patched, FAILS at base.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
django.setup()
from django.db.models.sql.query import Query
from django.db.utils import NotSupportedError

class PlainValue:
    # like a model instance whose model has a BooleanField named `filterable`
    filterable = False
    # NOTE: intentionally NO resolve_expression attribute

q = Query(None)
try:
    q.check_filterable(PlainValue())
    print("OK: plain value with filterable=False accepted (no NotSupportedError)")
except NotSupportedError as e:
    print("REJECTED plain value:", e)
    raise SystemExit(1)
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1/1.2/3.3 — a genuine query expression (has resolve_expression) marked
# filterable=False MUST be rejected with NotSupportedError, and the message must
# name the class and say "disallowed in the filter clause".
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
django.setup()
from django.db.models.sql.query import Query
from django.db.utils import NotSupportedError

class FakeExpr:
    filterable = False
    def resolve_expression(self, *a, **k):
        return self

q = Query(None)
try:
    q.check_filterable(FakeExpr())
except NotSupportedError as e:
    msg = str(e)
    print("Raised:", msg)
    assert "FakeExpr" in msg, "class name missing"
    assert "disallowed in the filter clause" in msg, "message text missing"
    print("OK: non-filterable expression rejected with correct message")
    raise SystemExit(0)
print("FAIL: no NotSupportedError raised for non-filterable expression")
raise SystemExit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req1.3 / Req2.1 — absence of a `filterable` attribute: a value with
# resolve_expression but NO filterable attribute must be treated as filterable
# (accepted). Also a plain value with no filterable and no resolve_expression.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
django.setup()
from django.db.models.sql.query import Query
from django.db.utils import NotSupportedError

class ExprNoFilterable:
    def resolve_expression(self, *a, **k):
        return self
    # no `filterable` attribute at all

class PlainNoFilterable:
    pass

q = Query(None)
for obj in (ExprNoFilterable(), PlainNoFilterable()):
    try:
        q.check_filterable(obj)
        print("OK accepted:", obj.__class__.__name__)
    except NotSupportedError as e:
        print("FAIL: rejected", obj.__class__.__name__, e)
        raise SystemExit(1)
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1/3.2 — recursion into nested source expressions. An enclosing candidate
# that is itself admissible (filterable=True, has resolve_expression) but whose
# get_source_expressions() yields a non-filterable expression must STILL be
# rejected.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
django.setup()
from django.db.models.sql.query import Query
from django.db.utils import NotSupportedError

class BadInner:
    filterable = False
    def resolve_expression(self, *a, **k):
        return self
    def get_source_expressions(self):
        return []

class GoodOuter:
    filterable = True
    def resolve_expression(self, *a, **k):
        return self
    def get_source_expressions(self):
        return [BadInner()]

q = Query(None)
try:
    q.check_filterable(GoodOuter())
except NotSupportedError as e:
    print("OK: nested non-filterable expression rejected:", e)
    assert "BadInner" in str(e)
    raise SystemExit(0)
print("FAIL: nested non-filterable expression not rejected")
raise SystemExit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3.3 — a real Window expression (filterable=False) must still be rejected
# when used in a filter clause (end-to-end via .filter()). Window rejection
# happens at filter-build time, before touching the DB.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        USE_TZ=True,
    )
django.setup()

from django.db import models

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'

from django.db.models import Window
from django.db.models.functions import RowNumber
from django.db.utils import NotSupportedError

w = Window(expression=RowNumber())
try:
    Thing.objects.filter(val=w).query  # build the query
    print("FAIL: Window expression accepted in filter clause")
    raise SystemExit(1)
except NotSupportedError as e:
    print("OK: Window rejected in filter clause:", e)
    raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req2.1/2.2 — a value that does NOT participate in the
# expression-resolution protocol (no resolve_expression) but carries a falsey
# `filterable` attribute must NOT be rejected. HOLDS patched, FAILS at base.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
django.setup()
from django.db.models.sql.query import Query
from django.db.utils import NotSupportedError

class PlainValue:
    # like a model instance whose model has a BooleanField named `filterable`
    filterable = False
    # NOTE: intentionally NO resolve_expression attribute

q = Query(None)
try:
    q.check_filterable(PlainValue())
    print("OK: plain value with filterable=False accepted (no NotSupportedError)")
except NotSupportedError as e:
    print("REJECTED plain value:", e)
    raise SystemExit(1)
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-13028: check_filterable must gate rejection on hasattr(expression,'resolve_expression') AND falsey filterable, instead of falsey filterable alone.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req2.1/2.2, POSITIVE CONTROL): plain value with filterable=False and NO resolve_expression must be accepted. HOLDS patched, VIOLATED at base (base rejects it -> reproduces the bug). Discriminates.
- probe_2 (Req1.1/1.2/3.3): expression (has resolve_expression) with filterable=False rejected; message names class + 'disallowed in the filter clause'.
- probe_3 (Req1.3/2.1): value with resolve_expression but no filterable attr, and plain value with neither, both accepted (absence => filterable).
- probe_4 (Req3.1/3.2): admissible outer expression whose get_source_expressions yields a non-filterable inner expression is still rejected (recursion preserved).
- probe_5 (Req3.3): real Window(RowNumber()) still rejected via .filter() end-to-end.

Base runs: probe_1 VIOLATED (bug reproduced); probes 2/3/4/5 HOLD at base (regression criteria, unchanged by patch).

Candidate wrong-fixes, both REJECTED by the suite (=> discriminating, no too-weak finding):
- weak1 (naive lazy fix: gate on hasattr(expression,'filterable') instead of resolve_expression): probe_1 VIOLATED (plain PlainValue with a filterable attr still rejected). This is the exact lazy reading a weak spec might admit; suite catches it.
- weak2 (delete the check, `if False`): probes 2, 4, 5 VIOLATED.

All needed runs completed in the official image. >=5 probes hold patched, positive control discriminates, both wrong candidates rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# Positive control: Req2.1/2.2 — a value that does NOT participate in the
# expression-resolution protocol (no resolve_expression) but carries a falsey
# `filterable` attribute must NOT be rejected. HOLDS patched, FAILS at base.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
django.setup()
from django.db.models.sql.query import Query
from django.db.utils import NotSupportedError

class PlainValue:
    # like a model instance whose model has a BooleanField named `filterable`
    filterable = False
    # NOTE: intentionally NO resolve_expression attribute

q = Query(None)
try:
    q.check_filterable(PlainValue())
    print("OK: plain value with filterable=False accepted (no NotSupportedError)")
except NotSupportedError as e:
    print("REJECTED plain value:", e)
    raise SystemExit(1)
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-13028: check_filterable must gate rejection on hasattr(expression,'resolve_expression') AND falsey filterable, instead of falsey filterable alone.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req2.1/2.2, POSITIVE CONTROL): plain value with filterable=False and NO resolve_expression must be accepted. HOLDS patched, VIOLATED at base (base rejects it -> reproduces the bug). Discriminates.
- probe_2 (Req1.1/1.2/3.3): expression (has resolve_expression) with filterable=False rejected; message names class + 'disallowed in the filter clause'.
- probe_3 (Req1.3/2.1): value with resolve_expression but no filterable attr, and plain value with neither, both accepted (absence => filterable).
- probe_4 (Req3.1/3.2): admissible outer expression whose get_source_expressions yields a non-filterable inner expression is still rejected (recursion preserved).
- probe_5 (Req3.3): real Window(RowNumber()) still rejected via .filter() end-to-end.

Base runs: probe_1 VIOLATED (bug reproduced); probes 2/3/4/5 HOLD at base (regression criteria, unchanged by patch).

Candidate wrong-fixes, both REJECTED by the suite (=> discriminating, no too-weak finding):
- weak1 (naive lazy fix: gate on hasattr(expression,'filterable') instead of resolve_expression): probe_1 VIOLATED (plain PlainValue with a filterable attr still rejected). This is the exact lazy reading a weak spec might admit; suite catches it.
- weak2 (delete the check, `if False`): probes 2, 4, 5 VIOLATED.

All needed runs completed in the official image. >=5 probes hold patched, positive control discriminates, both wrong candidates rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on the gold-patched instance image. Verified: (R1) Expr with resolve_expression+filterable=False -> NotSupportedError naming class 'Expr is disallowed in the filter clause.' [matches Req1.1/1.2]; (R2) Plain value filterable=False, no resolve_expression -> no raise [matches Req2.1/2.2/2.3]; (R3) Container.get_source_expressions()=[Expr()] -> raises on nested expr [matches Req3.1/3.2/3.3]; (Req1.3/2 absent-attr) object with resolve_expression but no filterable attr -> no raise [matches, getattr default True]. Requirement 2 correctly identifies the ISSUE-driven fix (model instance with a field named 'filterable'=False was wrongly rejected). Modeling boundary is the full changed behavior (resolve_expression gate + recursion), not a narrow slice. Requirement source citation (django/db/models/sql/query.py, check_filterable) is accurate.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes the fix purely behaviorally. Everything localizing the change (check_filterable, query.py, build_filter/add_q, NotSupportedError message, the 'filterable' field name, window-expression filterable=False) is already public via the problem_statement traceback and Django domain knowledge. The fix mechanism is described as 'participates in the expression-resolution protocol' without naming resolve_expression literally, and resolve_expression is a pre-existing Django attribute, not a fix-invented identifier. No hidden-test content is transmitted: no test names (test_field_with_filterable, test_ticket8439), no test file paths, no fixture/model identifiers (ExtraInfo, Author, e2/a3/a4), no parametrization ids, and no verbatim gold-patch lines beyond what the problem_statement exposes. Requirement 3's recursion-into-nested-source-expressions clause describes preserved existing code, not a test enumeration.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
