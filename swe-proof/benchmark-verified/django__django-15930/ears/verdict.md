# P2 adversarial audit — django__django-15930

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
"""POSITIVE CONTROL / Req1 crit 2&3: annotate with a match-everything When
(~Q(pk__in=[])) and a differing default must (a) NOT raise, (b) assign the
branch's `then` (not the default) to EVERY row, (c) return all rows.
Holds on patched, must FAIL at base (base emits `WHEN  THEN` -> DB syntax err)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Case, When, Value, Q, BooleanField

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
for i in range(3):
    Thing.objects.create(val=i)

try:
    qs = list(Thing.objects.annotate(
        c=Case(When(~Q(pk__in=[]), then=Value(True)),
               default=Value(False), output_field=BooleanField())
    ).values_list("c", flat=True))
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)

print("rows:", qs)
if len(qs) != 3:
    print("wrong row count, expected 3")
    sys.exit(1)
if not all(v is True or v == 1 for v in qs):
    print("not all rows got the then=True branch")
    sys.exit(1)
print("OK: all rows got then value, no error")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1 crit 1&4: the emitted CASE SQL for a match-everything When must contain
a non-empty predicate between WHEN and THEN (no `WHEN  THEN`), and using it in
order_by must execute successfully."""
import sys, re
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Case, When, Value, Q, BooleanField

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
for i in range(3):
    Thing.objects.create(val=i)

qs = Thing.objects.annotate(
    c=Case(When(~Q(pk__in=[]), then=Value(1)), default=Value(0),
           output_field=models.IntegerField()))
sql, params = qs.query.sql_with_params()
print("SQL:", sql)
# find CASE ... END, check there's no empty WHEN THEN
m = re.search(r"WHEN\s+THEN", sql, re.IGNORECASE)
if m:
    print("FOUND empty predicate 'WHEN THEN'")
    sys.exit(1)
if not re.search(r"CASE\s+WHEN\s+\S", sql, re.IGNORECASE):
    print("no non-empty predicate after WHEN")
    sys.exit(1)

# order_by must execute
try:
    rows = list(qs.order_by("c").values_list("val", flat=True))
except Exception as e:
    print("order_by RAISED:", type(e).__name__, e)
    sys.exit(1)
print("order_by rows:", rows)
print("OK: non-empty predicate, order_by executed")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3 crit 1: a match-NOTHING When (Q(pk__in=[])) must NOT get the always-true
substitution. The default must be applied to every row, branch `then` to none."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Case, When, Value, Q, BooleanField

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
for i in range(3):
    Thing.objects.create(val=i)

qs = list(Thing.objects.annotate(
    c=Case(When(Q(pk__in=[]), then=Value(True)), default=Value(False),
           output_field=BooleanField())
).values_list("c", flat=True))
print("rows:", qs)
if len(qs) != 3:
    print("wrong row count")
    sys.exit(1)
# match-nothing => all rows get DEFAULT (False), NOT the then value
if any(v is True or v == 1 for v in qs):
    print("a row got the then value -> always-true wrongly applied to match-nothing")
    sys.exit(1)
print("OK: match-nothing -> default applied to all rows")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3 crit 2&3: constructor validation preserved.
- When(Q()) empty -> ValueError
- When() no condition, and When(non-Q/non-lookup arg) -> TypeError
Req2 crit 1: an ordinary non-empty condition renders WHEN <pred> THEN normally."""
import sys, re
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Case, When, Value, Q

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

ok = True

# empty Q() -> ValueError
try:
    When(Q(), then=Value(1))
    print("empty Q(): no error"); ok = False
except ValueError:
    print("empty Q() -> ValueError OK")
except Exception as e:
    print("empty Q() -> wrong exc", type(e).__name__); ok = False

# no condition -> TypeError
try:
    When(then=Value(1))
    print("no condition: no error"); ok = False
except TypeError:
    print("no condition -> TypeError OK")
except Exception as e:
    print("no condition -> wrong exc", type(e).__name__); ok = False

# non-Q non-lookup arg -> TypeError
try:
    When(object(), then=Value(1))
    print("bad arg: no error"); ok = False
except TypeError:
    print("bad arg -> TypeError OK")
except Exception as e:
    print("bad arg -> wrong exc", type(e).__name__); ok = False

# ordinary condition renders normal WHEN <pred> THEN
with connection.schema_editor() as se:
    se.create_model(Thing)
Thing.objects.create(val=5)
qs = Thing.objects.annotate(
    c=Case(When(val=5, then=Value(1)), default=Value(0),
           output_field=models.IntegerField()))
sql, params = qs.query.sql_with_params()
print("SQL:", sql)
if re.search(r"WHEN\s+THEN", sql, re.IGNORECASE):
    print("ordinary cond produced empty WHEN THEN"); ok = False
if '"val"' not in sql.lower() and 'val' not in sql.lower():
    print("ordinary predicate missing"); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1 crit 5 + Req2 crit 3 / Req4: the always-true substitution keeps params
consistent with SQL, and match-everything works in aggregate and update.
- aggregate: Sum over a Case(When(~Q(pk__in=[]), then=val)) equals sum(val)
- update: update via Case(When(~Q(pk__in=[]),...)) sets all rows, no error
- params count consistent (query compiles & executes)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Case, When, Value, Q, Sum, IntegerField

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
for i in range(4):
    Thing.objects.create(val=i)   # vals 0,1,2,3 sum=6

# aggregate
try:
    agg = Thing.objects.aggregate(
        s=Sum(Case(When(~Q(pk__in=[]), then="val"), default=Value(0),
                   output_field=IntegerField())))
except Exception as e:
    print("aggregate RAISED:", type(e).__name__, e); sys.exit(1)
print("aggregate:", agg)
if agg["s"] != 6:
    print("aggregate wrong, expected 6"); sys.exit(1)

# update
try:
    n = Thing.objects.update(
        val=Case(When(~Q(pk__in=[]), then=Value(99)), default=Value(-1),
                 output_field=IntegerField()))
except Exception as e:
    print("update RAISED:", type(e).__name__, e); sys.exit(1)
vals = sorted(Thing.objects.values_list("val", flat=True))
print("after update:", vals, "updated", n)
if vals != [99, 99, 99, 99]:
    print("update did not set all rows to then value"); sys.exit(1)
print("OK: aggregate + update with match-everything condition")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL / Req1 crit 2&3: annotate with a match-everything When
(~Q(pk__in=[])) and a differing default must (a) NOT raise, (b) assign the
branch's `then` (not the default) to EVERY row, (c) return all rows.
Holds on patched, must FAIL at base (base emits `WHEN  THEN` -> DB syntax err)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Case, When, Value, Q, BooleanField

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
for i in range(3):
    Thing.objects.create(val=i)

try:
    qs = list(Thing.objects.annotate(
        c=Case(When(~Q(pk__in=[]), then=Value(True)),
               default=Value(False), output_field=BooleanField())
    ).values_list("c", flat=True))
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)

print("rows:", qs)
if len(qs) != 3:
    print("wrong row count, expected 3")
    sys.exit(1)
if not all(v is True or v == 1 for v in qs):
    print("not all rows got the then=True branch")
    sys.exit(1)
print("OK: all rows got then value, no error")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements pin When.as_sql: when a condition renders to an empty predicate fragment (match-everything, e.g. ~Q(pk__in=[])), substitute an always-TRUE predicate (with its params) so the CASE is syntactically valid AND the branch's `then` applies to every row.

5 probes, all HOLD on gold-patched tree:
- probe_1 (Req1 crit 2&3, POSITIVE CONTROL): annotate with ~Q(pk__in=[]) When(then=True), default=False -> every row gets True, 3 rows, no error. Patched: HOLDS [True,True,True]. Base: VIOLATED (OperationalError syntax error near THEN). Discriminates.
- probe_2 (Req1 crit 1&4): emitted CASE SQL has non-empty predicate between WHEN and THEN (no `WHEN  THEN`) and order_by executes. Patched HOLDS (`CASE WHEN %s THEN...`); base VIOLATED (`CASE WHEN  THEN`).
- probe_3 (Req3 crit 1): match-NOTHING Q(pk__in=[]) must NOT get always-true substitution -> default applied to all rows, no `then`. HOLDS [False,False,False].
- probe_4 (Req3 crit 2&3, Req2 crit 1): empty Q() -> ValueError; no condition -> TypeError; bad arg -> TypeError; ordinary condition renders normal `WHEN val=%s THEN`. HOLDS.
- probe_5 (Req1 crit 5, Req2 crit 3): params consistent; aggregate Sum(Case(When(~Q(pk__in=[]),then=val))) == sum(val)==6; update sets all rows to then value 99. HOLDS.

CANDIDATE (wrong fix) exercised: weak.diff substitutes Value(False) instead of Value(True) — the lazy 'just make the SQL valid' fix a weak reading permits. It FIXES the syntax (probe_2/3/4 HOLD) but is REJECTED by probe_1 (rows get default False, not then) and probe_5 (aggregate=0 not 6). So the suite discriminates a probe-conforming-on-syntax-only wrong impl; the always-False fix would NOT resolve the F2P test (test_annotate_with_full_when expects the then value on every row). No requirements-conforming wrong patch found. Verdict SOUND.

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
"""POSITIVE CONTROL / Req1 crit 2&3: annotate with a match-everything When
(~Q(pk__in=[])) and a differing default must (a) NOT raise, (b) assign the
branch's `then` (not the default) to EVERY row, (c) return all rows.
Holds on patched, must FAIL at base (base emits `WHEN  THEN` -> DB syntax err)."""
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False)
django.setup()
from django.db import models, connection
from django.db.models import Case, When, Value, Q, BooleanField

class Thing(models.Model):
    val = models.IntegerField()
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Thing)
for i in range(3):
    Thing.objects.create(val=i)

try:
    qs = list(Thing.objects.annotate(
        c=Case(When(~Q(pk__in=[]), then=Value(True)),
               default=Value(False), output_field=BooleanField())
    ).values_list("c", flat=True))
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)

print("rows:", qs)
if len(qs) != 3:
    print("wrong row count, expected 3")
    sys.exit(1)
if not all(v is True or v == 1 for v in qs):
    print("not all rows got the then=True branch")
    sys.exit(1)
print("OK: all rows got then value, no error")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements pin When.as_sql: when a condition renders to an empty predicate fragment (match-everything, e.g. ~Q(pk__in=[])), substitute an always-TRUE predicate (with its params) so the CASE is syntactically valid AND the branch's `then` applies to every row.

5 probes, all HOLD on gold-patched tree:
- probe_1 (Req1 crit 2&3, POSITIVE CONTROL): annotate with ~Q(pk__in=[]) When(then=True), default=False -> every row gets True, 3 rows, no error. Patched: HOLDS [True,True,True]. Base: VIOLATED (OperationalError syntax error near THEN). Discriminates.
- probe_2 (Req1 crit 1&4): emitted CASE SQL has non-empty predicate between WHEN and THEN (no `WHEN  THEN`) and order_by executes. Patched HOLDS (`CASE WHEN %s THEN...`); base VIOLATED (`CASE WHEN  THEN`).
- probe_3 (Req3 crit 1): match-NOTHING Q(pk__in=[]) must NOT get always-true substitution -> default applied to all rows, no `then`. HOLDS [False,False,False].
- probe_4 (Req3 crit 2&3, Req2 crit 1): empty Q() -> ValueError; no condition -> TypeError; bad arg -> TypeError; ordinary condition renders normal `WHEN val=%s THEN`. HOLDS.
- probe_5 (Req1 crit 5, Req2 crit 3): params consistent; aggregate Sum(Case(When(~Q(pk__in=[]),then=val))) == sum(val)==6; update sets all rows to then value 99. HOLDS.

CANDIDATE (wrong fix) exercised: weak.diff substitutes Value(False) instead of Value(True) — the lazy 'just make the SQL valid' fix a weak reading permits. It FIXES the syntax (probe_2/3/4 HOLD) but is REJECTED by probe_1 (rows get default False, not then) and probe_5 (aggregate=0 not 6). So the suite discriminates a probe-conforming-on-syntax-only wrong impl; the always-False fix would NOT resolve the F2P test (test_annotate_with_full_when expects the then value on every row). No requirements-conforming wrong patch found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: in When.as_sql, `if condition_sql == "": condition_sql, condition_params = compiler.compile(Value(True))`. Requirements pin the changed observable behavior (empty-predicate branch renders as always-true) rather than an over-narrow slice — they correctly cover both the match-everything (substitute) and match-nothing (do NOT substitute) cases, which is the correct biconditional boundary. Probe run in instance image: base VIOLATED with `near "THEN" syntax error`, patched HOLDS with valid SQL and all assertions passing.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes the empty-predicate→always-true substitution behaviorally (Req 1) without quoting the gold's `condition_sql == ""` check or `Value(True)` substitution — naming When.as_sql / expressions.py is legitimate localization. The hidden FAIL_TO_PASS test's invented literals ('selected'/'not selected') are NOT leaked; Req 1.2 uses generic 'then value'/'default value', and the ~Q(pk__in=[]), all-rows-match, and syntax-error facts it echoes are all already in the public problem_statement. Req 3/4 enumerate regression behaviors (empty Q()→ValueError, invalid args→TypeError, hashability, documentation examples for aggregation/update/filter/lookup) that mirror the PASS_TO_PASS suite, but these are publicly-documented Django contract stated as 'preserve existing behavior', containing no test names, ids, paths, or code. No verbatim test/gold code, no test file paths, no fix-invented identifiers. The doc-example enumeration is the most test-shaped prose but is derivable from public Django docs, not only the hidden tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
