# P2 adversarial audit — django__django-13449

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
"""Req 1.3 & 1.4 (POSITIVE CONTROL): a decimal-typed Window query executes on
SQLite without an OperationalError about OVER, and returns correct decimal
Lag values (empty/None for the first row of a partition)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

import sys
from decimal import Decimal
from django.db import connection, models


class Emp(models.Model):
    name = models.CharField(max_length=40)
    dept = models.CharField(max_length=40)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

rows = [
    ("a", "x", Decimal("10.50")),
    ("b", "x", Decimal("20.25")),
    ("c", "y", Decimal("30.00")),
]
for n, d, s in rows:
    Emp.objects.create(name=n, dept=d, salary=s)

from django.db.models import F, Window
from django.db.models.functions import Lag

qs = Emp.objects.annotate(
    prev=Window(
        expression=Lag("salary"),
        partition_by=[F("dept")],
        order_by=[F("name").asc()],
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
    )
).order_by("dept", "name")

try:
    got = [(e.name, e.dept, e.prev) for e in qs]
except Exception as e:
    print("EXECUTION FAILED:", type(e).__name__, e)
    sys.exit(1)

print("rows:", got)

# Expected Lag within partition ordered by name:
expected = {
    "a": None,
    "b": Decimal("10.50"),
    "c": None,
}
ok = True
for name, dept, prev in got:
    exp = expected[name]
    if exp is None:
        if prev is not None:
            print("row", name, "expected None got", prev); ok = False
    else:
        if prev is None or Decimal(prev) != exp:
            print("row", name, "expected", exp, "got", prev); ok = False
        # confirm it is a decimal-typed value, not float garbage
        if prev is not None and not isinstance(prev, Decimal):
            print("row", name, "value not Decimal:", type(prev)); ok = False

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 & 1.2: on SQLite the decimal window renders CAST wrapping the WHOLE
windowed expression: CAST(<operand> OVER (<window>) AS NUMERIC). The CAST must
enclose the OVER clause; there must be NO 'CAST(...) OVER' shape (a closed CAST
term immediately followed by OVER), and no cast between operand and OVER."""
import re, sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import connection, models
from django.db.models import F, Window
from django.db.models.functions import Lag


class Emp(models.Model):
    name = models.CharField(max_length=40)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

win = Window(
    expression=Lag("salary"),
    order_by=[F("name").asc()],
    output_field=models.DecimalField(max_digits=10, decimal_places=2),
)
qs = Emp.objects.annotate(prev=win)
sql, params = qs.query.get_compiler("default").as_sql()
print("SQL:", sql)

# Find the windowed fragment. It must contain OVER, and be wrapped by CAST(... AS NUMERIC).
ok = True

# 1) An OVER clause exists.
if "OVER" not in sql:
    print("no OVER in SQL"); ok = False

# 2) NO closed CAST term immediately followed by OVER: 'CAST(...) OVER'
if re.search(r"CAST\s*\([^()]*\([^()]*\)[^()]*AS\s+NUMERIC\s*\)\s+OVER", sql, re.I) or \
   re.search(r"AS\s+NUMERIC\s*\)\s+OVER", sql, re.I):
    print("BAD: found 'CAST(... AS NUMERIC) OVER' — cast inside/around operand only"); ok = False

# 3) The CAST(... AS NUMERIC) must enclose an OVER (whole windowed expr as unit).
#    i.e. there is a CAST(...) span whose interior contains 'OVER'.
found_wrap = False
for m in re.finditer(r"CAST\s*\(", sql, re.I):
    start = m.end()
    depth = 1
    i = start
    while i < len(sql) and depth > 0:
        if sql[i] == "(":
            depth += 1
        elif sql[i] == ")":
            depth -= 1
        i += 1
    interior = sql[start:i-1]
    # 'CAST( <expr> AS NUMERIC )' -> AS NUMERIC lives at the END of the interior.
    if "OVER" in interior.upper() and re.search(r"AS\s+NUMERIC\s*$", interior.strip(), re.I):
        found_wrap = True
if not found_wrap:
    print("BAD: no CAST(... AS NUMERIC) enclosing an OVER clause"); ok = False
else:
    print("GOOD: CAST wraps the full 'OVER' windowed expression")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1 & 2.2: a NON-decimal window expression renders the bare
'<operand> OVER (<window>)' with NO surrounding numeric cast on SQLite, and the
part order is operand, ' OVER (', window clause, ')'."""
import re, sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import connection, models
from django.db.models import F, Window
from django.db.models.functions import Lag


class Emp(models.Model):
    name = models.CharField(max_length=40)
    n = models.IntegerField()

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

# IntegerField output -> not decimal.
win = Window(
    expression=Lag("n"),
    partition_by=[F("name")],
    order_by=[F("name").asc()],
    output_field=models.IntegerField(),
)
qs = Emp.objects.annotate(prev=win)
sql, params = qs.query.get_compiler("default").as_sql()
print("SQL:", sql)

ok = True
# No CAST(... AS NUMERIC) around the window for non-decimal output.
if re.search(r"CAST\s*\([^;]*OVER[^;]*AS\s+NUMERIC", sql, re.I):
    print("BAD: numeric cast applied to non-decimal window"); ok = False

# Structural order: operand then ' OVER (' then window then ')'.
m = re.search(r"\bLAG\b.*?\bOVER\s*\(.*?\)", sql, re.I | re.S)
if not m:
    print("BAD: could not find 'LAG ... OVER ( ... )' shape"); ok = False
else:
    print("GOOD: bare 'operand OVER (window)' with no numeric cast")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3: the 'not supported' error is still raised when a Window expression
is compiled for a backend that does not support OVER clauses. We simulate this
by monkeypatching the connection ops to declare no window support (the same
check_expression_support path Window.as_sql invokes)."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import connection, models, NotSupportedError
from django.db.models import F, Window
from django.db.models.functions import Lag


class Emp(models.Model):
    name = models.CharField(max_length=40)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

# Force "window not supported" via the exact flag as_sql checks.
type(connection.features).supports_over_clause = False

win = Window(
    expression=Lag("salary"),
    order_by=[F("name").asc()],
    output_field=models.DecimalField(max_digits=10, decimal_places=2),
)
qs = Emp.objects.annotate(prev=win)

ok = False
try:
    sql, params = qs.query.get_compiler("default").as_sql()
    print("NO ERROR RAISED — got SQL:", sql)
except NotSupportedError as e:
    print("GOOD: NotSupportedError raised:", e)
    ok = True
except Exception as e:
    print("other error:", type(e).__name__, e)

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2: the str/repr and structural behavior of the Window expression are
unchanged — source expression, partition_by, order_by, frame preserved, and
filterable is False, contains_over_clause True."""
import sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models
from django.db.models import F, Window
from django.db.models.functions import Lag
from django.db.models.expressions import RowRange

win = Window(
    expression=Lag("salary", offset=1),
    partition_by=[F("dept")],
    order_by=[F("name").asc()],
    frame=RowRange(start=-2, end=None),
    output_field=models.DecimalField(max_digits=10, decimal_places=2),
)

ok = True
s = str(win)
r = repr(win)
print("str:", s)
print("repr:", r)

if "OVER" not in s:
    print("BAD: str missing OVER"); ok = False
if "PARTITION BY" not in s:
    print("BAD: str missing PARTITION BY"); ok = False
if "ORDER BY" not in s:
    print("BAD: str missing ORDER BY"); ok = False
if not r.startswith("<Window:"):
    print("BAD: repr shape"); ok = False

# structural
if win.contains_over_clause is not True:
    print("BAD: contains_over_clause", win.contains_over_clause); ok = False
if win.filterable is not False:
    print("BAD: filterable", win.filterable); ok = False

srcs = win.get_source_expressions()
# [source_expression, partition_by, order_by, frame]
if len(srcs) != 4:
    print("BAD: source expr count", len(srcs)); ok = False
else:
    if not isinstance(srcs[0], Lag):
        print("BAD: source[0] not Lag", type(srcs[0])); ok = False
    if not isinstance(srcs[3], RowRange):
        print("BAD: frame not RowRange", type(srcs[3])); ok = False

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.1 & 3.3: on a non-SQLite backend the decimal Window renders exactly as
before — NO CAST(... AS NUMERIC) at all. compiler.compile dispatches to
'as_<vendor>' or falls back to as_sql. We set the connection vendor to
'postgresql' (drivers unavailable, but SQL *text* generation needs none): then
neither the Window nor its DecimalField source expression get the SQLite
numeric wrap, so the emitted SQL is the bare '<operand> OVER (<window>)'."""
import re, sys
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import connection, models
from django.db.models import F, Window
from django.db.models.functions import Lag


class Emp(models.Model):
    name = models.CharField(max_length=40)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

win = Window(
    expression=Lag("salary"),
    order_by=[F("name").asc()],
    output_field=models.DecimalField(max_digits=10, decimal_places=2),
)
qs = Emp.objects.annotate(prev=win)
compiler = qs.query.get_compiler("default")

# Pretend we're on a backend other than sqlite: compiler.compile uses
# getattr(node, 'as_'+vendor, node.as_sql) -> falls back to as_sql everywhere.
compiler.connection.vendor = "postgresql"
sql, params = compiler.as_sql()

print("non-sqlite SQL:", sql)

ok = True
if re.search(r"CAST\s*\(.*AS\s+NUMERIC", sql, re.I):
    print("BAD: numeric cast present on non-sqlite backend"); ok = False
if "OVER" not in sql.upper():
    print("BAD: no OVER clause"); ok = False
if ok:
    print("GOOD: non-sqlite rendering is bare 'operand OVER (window)', no cast")

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.3 & 1.4 (POSITIVE CONTROL): a decimal-typed Window query executes on
SQLite without an OperationalError about OVER, and returns correct decimal
Lag values (empty/None for the first row of a partition)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

import sys
from decimal import Decimal
from django.db import connection, models


class Emp(models.Model):
    name = models.CharField(max_length=40)
    dept = models.CharField(max_length=40)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

rows = [
    ("a", "x", Decimal("10.50")),
    ("b", "x", Decimal("20.25")),
    ("c", "y", Decimal("30.00")),
]
for n, d, s in rows:
    Emp.objects.create(name=n, dept=d, salary=s)

from django.db.models import F, Window
from django.db.models.functions import Lag

qs = Emp.objects.annotate(
    prev=Window(
        expression=Lag("salary"),
        partition_by=[F("dept")],
        order_by=[F("name").asc()],
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
    )
).order_by("dept", "name")

try:
    got = [(e.name, e.dept, e.prev) for e in qs]
except Exception as e:
    print("EXECUTION FAILED:", type(e).__name__, e)
    sys.exit(1)

print("rows:", got)

# Expected Lag within partition ordered by name:
expected = {
    "a": None,
    "b": Decimal("10.50"),
    "c": None,
}
ok = True
for name, dept, prev in got:
    exp = expected[name]
    if exp is None:
        if prev is not None:
            print("row", name, "expected None got", prev); ok = False
    else:
        if prev is None or Decimal(prev) != exp:
            print("row", name, "expected", exp, "got", prev); ok = False
        # confirm it is a decimal-typed value, not float garbage
        if prev is not None and not isinstance(prev, Decimal):
            print("row", name, "value not Decimal:", type(prev)); ok = False

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements for django__django-13449: on SQLite, a DecimalField-typed Window expression must render CAST(<operand> OVER (<window>) AS NUMERIC) — cast around the whole windowed unit — so the query executes and returns correct decimals, with non-decimal windows and non-SQLite backends unchanged.

6 probes, all HOLD on the gold-patched tree:
- probe_1 (Req 1.3/1.4, POSITIVE CONTROL): end-to-end Lag over DecimalField on real SQLite in-memory DB executes without OperationalError and returns correct Decimal Lag values (None for first row of each partition). HOLDS patched; at --base it FAILS with `OperationalError near "OVER": syntax error` => prepatch reproduced, discriminating power confirmed.
- probe_2 (Req 1.1/1.2): inspects generated SQL; requires a CAST(...) span whose interior contains OVER and ends in `AS NUMERIC`, and rejects any `... AS NUMERIC) OVER` (closed CAST followed by OVER). HOLDS patched.
- probe_3 (Req 2.1/2.2): non-decimal (IntegerField) window renders bare `LAG(...) OVER (...)` with no numeric cast; part order preserved. HOLDS.
- probe_4 (Req 2.3): forcing connection.features.supports_over_clause=False still raises NotSupportedError('...does not support window expressions.'). HOLDS.
- probe_5 (Req 3.2): str/repr, get_source_expressions (source/partition/order/frame), contains_over_clause=True, filterable=False all intact. HOLDS.
- probe_6 (Req 3.1/3.3): setting compiler.connection.vendor='postgresql' (non-SQLite dispatch) yields bare `LAG(...) OVER (...)` with NO CAST anywhere. HOLDS.

Discrimination — two wrong-fix candidates, both REJECTED by the suite:
- weak_mixin_only.diff (naive: add SQLiteNumericMixin to Window, no as_sqlite override): the DecimalField source gets inner-cast giving `CAST(LAG(...) AS NUMERIC) OVER (...)` wrapped again -> probe_1 REJECTS (OperationalError near OVER at runtime) and probe_2 REJECTS (closed-CAST-then-OVER shape). Probes 3-6 hold.
- weak_floatdrop.diff (lazy: cast source to Float and drop the outer numeric cast entirely): executes fine (probe_1 holds) but emits bare `LAG(...) OVER (...)` for the decimal window with no `CAST(... AS NUMERIC)` -> probe_2 REJECTS (Req 1.1 mandates the wrapping cast; without it decimal read-back is unfaithful, which the hidden test asserts). 

Both candidates rejected => suite discriminates wrong implementations. All 6 probes hold patched and positive control fails at base and holds patched. No requirements violation and no probe-conforming wrong patch found.

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
"""Req 1.3 & 1.4 (POSITIVE CONTROL): a decimal-typed Window query executes on
SQLite without an OperationalError about OVER, and returns correct decimal
Lag values (empty/None for the first row of a partition)."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

import sys
from decimal import Decimal
from django.db import connection, models


class Emp(models.Model):
    name = models.CharField(max_length=40)
    dept = models.CharField(max_length=40)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = "probeapp"


with connection.schema_editor() as se:
    se.create_model(Emp)

rows = [
    ("a", "x", Decimal("10.50")),
    ("b", "x", Decimal("20.25")),
    ("c", "y", Decimal("30.00")),
]
for n, d, s in rows:
    Emp.objects.create(name=n, dept=d, salary=s)

from django.db.models import F, Window
from django.db.models.functions import Lag

qs = Emp.objects.annotate(
    prev=Window(
        expression=Lag("salary"),
        partition_by=[F("dept")],
        order_by=[F("name").asc()],
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
    )
).order_by("dept", "name")

try:
    got = [(e.name, e.dept, e.prev) for e in qs]
except Exception as e:
    print("EXECUTION FAILED:", type(e).__name__, e)
    sys.exit(1)

print("rows:", got)

# Expected Lag within partition ordered by name:
expected = {
    "a": None,
    "b": Decimal("10.50"),
    "c": None,
}
ok = True
for name, dept, prev in got:
    exp = expected[name]
    if exp is None:
        if prev is not None:
            print("row", name, "expected None got", prev); ok = False
    else:
        if prev is None or Decimal(prev) != exp:
            print("row", name, "expected", exp, "got", prev); ok = False
        # confirm it is a decimal-typed value, not float garbage
        if prev is not None and not isinstance(prev, Decimal):
            print("row", name, "value not Decimal:", type(prev)); ok = False

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements for django__django-13449: on SQLite, a DecimalField-typed Window expression must render CAST(<operand> OVER (<window>) AS NUMERIC) — cast around the whole windowed unit — so the query executes and returns correct decimals, with non-decimal windows and non-SQLite backends unchanged.

6 probes, all HOLD on the gold-patched tree:
- probe_1 (Req 1.3/1.4, POSITIVE CONTROL): end-to-end Lag over DecimalField on real SQLite in-memory DB executes without OperationalError and returns correct Decimal Lag values (None for first row of each partition). HOLDS patched; at --base it FAILS with `OperationalError near "OVER": syntax error` => prepatch reproduced, discriminating power confirmed.
- probe_2 (Req 1.1/1.2): inspects generated SQL; requires a CAST(...) span whose interior contains OVER and ends in `AS NUMERIC`, and rejects any `... AS NUMERIC) OVER` (closed CAST followed by OVER). HOLDS patched.
- probe_3 (Req 2.1/2.2): non-decimal (IntegerField) window renders bare `LAG(...) OVER (...)` with no numeric cast; part order preserved. HOLDS.
- probe_4 (Req 2.3): forcing connection.features.supports_over_clause=False still raises NotSupportedError('...does not support window expressions.'). HOLDS.
- probe_5 (Req 3.2): str/repr, get_source_expressions (source/partition/order/frame), contains_over_clause=True, filterable=False all intact. HOLDS.
- probe_6 (Req 3.1/3.3): setting compiler.connection.vendor='postgresql' (non-SQLite dispatch) yields bare `LAG(...) OVER (...)` with NO CAST anywhere. HOLDS.

Discrimination — two wrong-fix candidates, both REJECTED by the suite:
- weak_mixin_only.diff (naive: add SQLiteNumericMixin to Window, no as_sqlite override): the DecimalField source gets inner-cast giving `CAST(LAG(...) AS NUMERIC) OVER (...)` wrapped again -> probe_1 REJECTS (OperationalError near OVER at runtime) and probe_2 REJECTS (closed-CAST-then-OVER shape). Probes 3-6 hold.
- weak_floatdrop.diff (lazy: cast source to Float and drop the outer numeric cast entirely): executes fine (probe_1 holds) but emits bare `LAG(...) OVER (...)` for the decimal window with no `CAST(... AS NUMERIC)` -> probe_2 REJECTS (Req 1.1 mandates the wrapping cast; without it decimal read-back is unfaithful, which the hidden test asserts). 

Both candidates rejected => suite discriminates wrong implementations. All 6 probes hold patched and positive control fails at base and holds patched. No requirements violation and no probe-conforming wrong patch found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `Window(SQLiteNumericMixin, Expression)` + `as_sqlite` that, only for DecimalField output, copies the expr, retypes source[0] to FloatField, and delegates to SQLiteNumericMixin.as_sqlite (which wraps the full `%(expression)s OVER (%(window)s)` in CAST(... AS NUMERIC)). Requirements pin exactly this observable behavioral boundary — the whole-windowed-expression cast on SQLite for decimal output vs. no change otherwise — not a narrow branch/helper slice. Behavior probed live in the instance image on the gold-patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the (very detailed) public problem_statement plus legitimate localization. Public already: the crashing SQL CAST(LAG(...) AS NUMERIC) OVER (...), the 'near "OVER": syntax error' OperationalError, DecimalField-only scope, the FloatField workaround, and the target 'wrap the whole statement' shape. The doc names django/db/models/expressions.py, the Window expression, and SQLiteNumericMixin — SQLiteNumericMixin is a real pre-existing Django helper (appears in hints_text, not problem_statement, but naming the affected component is legitimate localization, not a fix-invented identifier). No leak of the gold mechanism (the FloatField output_field swap on source_expressions[0]), no test names/paths (test_lag_decimalfield, expressions_window.tests), no 'bonus' field, and no enumeration of the test's specific per-row decimal/None result values. Req 1.4's mention of an empty/absent result when the offset falls outside the partition is behavioral lag semantics, not a mirror of the test's parametrized rows.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
