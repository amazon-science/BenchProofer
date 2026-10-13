# P2 adversarial audit — django__django-13807

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
"""POSITIVE CONTROL + Req2.4/3.3: genuine FK violation on reserved-word
table/columns raises IntegrityError, NOT an OperationalError syntax error.

Mirrors tests/backends/models.py::SQLKeywordsModel (db_table='order',
pk db_column='select', FK db_column='where') and the F2P test.

HOLDS iff check_constraints(['order']) raises IntegrityError (the intended
violation report). At base it raises OperationalError ('near "order"').
"""
import os, django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection, IntegrityError, OperationalError

class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    class Meta:
        app_label = "contenttypes"

class SQLKeywordsModel(models.Model):
    id = models.AutoField(primary_key=True, db_column="select")
    reporter = models.ForeignKey(Reporter, models.CASCADE, db_column="where")
    class Meta:
        app_label = "contenttypes"
        db_table = "order"

with connection.schema_editor() as se:
    se.create_model(Reporter)
    se.create_model(SQLKeywordsModel)

r = Reporter.objects.create(first_name="John")
obj = SQLKeywordsModel.objects.create(reporter=r)
obj.refresh_from_db()
# Break the FK while constraint checks are disabled.
obj.reporter_id = 30
with connection.constraint_checks_disabled():
    obj.save()
    try:
        connection.check_constraints(table_names=["order"])
    except IntegrityError as e:
        print("OK IntegrityError raised:", str(e)[:120])
        os._exit(0)
    except OperationalError as e:
        print("FAIL OperationalError (syntax error):", str(e)[:120])
        os._exit(1)
    except Exception as e:
        print("FAIL unexpected", type(e).__name__, str(e)[:120])
        os._exit(1)
    else:
        print("FAIL no exception raised (violation not detected)")
        os._exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1/1.2: reserved-word table with NO violations -> check_constraints
runs the foreign_key_check pragma without a syntax error.

HOLDS iff check_constraints(['order']) completes without raising when the data
is consistent. At base, quoting is absent so 'PRAGMA foreign_key_check(order)'
raises OperationalError near "order".
"""
import os, django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection, OperationalError

class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    class Meta:
        app_label = "contenttypes"

class SQLKeywordsModel(models.Model):
    id = models.AutoField(primary_key=True, db_column="select")
    reporter = models.ForeignKey(Reporter, models.CASCADE, db_column="where")
    class Meta:
        app_label = "contenttypes"
        db_table = "order"

with connection.schema_editor() as se:
    se.create_model(Reporter)
    se.create_model(SQLKeywordsModel)

r = Reporter.objects.create(first_name="John")
SQLKeywordsModel.objects.create(reporter=r)  # consistent -> no violation

try:
    connection.check_constraints(table_names=["order"])
except OperationalError as e:
    print("FAIL OperationalError:", str(e)[:120])
    os._exit(1)
except Exception as e:
    print("FAIL unexpected", type(e).__name__, str(e)[:120])
    os._exit(1)
print("OK check_constraints(['order']) completed without raising")
os._exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.1/1.3 & Req2.1/2.2: the interpolated identifiers are rendered through
quote_name (double-quoted) in the actual SQL executed.

Captures every SQL string the sqlite cursor executes during check_constraints
on the reserved-word schema with a genuine violation, then asserts:
 - a `PRAGMA foreign_key_check("order")` query was issued (Req1.1/1.3)
 - a `PRAGMA foreign_key_list("order")` query was issued (Req2.1)
 - a SELECT ... FROM "order" WHERE rowid query with the pk/fk columns quoted
   ("select", "where") was issued (Req2.2)

HOLDS iff all three quoted forms appear. A base/unquoted impl would emit the
bare identifiers (and in fact crash), so this discriminates the fix.
"""
import os, django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection, IntegrityError
from django.db.backends.sqlite3 import base as sqlite_base

class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    class Meta:
        app_label = "contenttypes"

class SQLKeywordsModel(models.Model):
    id = models.AutoField(primary_key=True, db_column="select")
    reporter = models.ForeignKey(Reporter, models.CASCADE, db_column="where")
    class Meta:
        app_label = "contenttypes"
        db_table = "order"

with connection.schema_editor() as se:
    se.create_model(Reporter)
    se.create_model(SQLKeywordsModel)

r = Reporter.objects.create(first_name="John")
obj = SQLKeywordsModel.objects.create(reporter=r)
obj.refresh_from_db()
obj.reporter_id = 30

captured = []
orig = sqlite_base.SQLiteCursorWrapper.execute
def spy(self, query, params=None):
    captured.append(query)
    return orig(self, query, params) if params is not None else orig(self, query)
sqlite_base.SQLiteCursorWrapper.execute = spy

with connection.constraint_checks_disabled():
    obj.save()
    try:
        connection.check_constraints(table_names=["order"])
    except IntegrityError:
        pass

sqlite_base.SQLiteCursorWrapper.execute = orig

joined = "\n".join(captured)
print("Captured queries during check_constraints:")
for q in captured:
    if "PRAGMA" in q or "rowid" in q:
        print("  ", q)

checks = {
    'foreign_key_check("order")': 'PRAGMA foreign_key_check("order")' in joined,
    'foreign_key_list("order")': 'PRAGMA foreign_key_list("order")' in joined,
    'SELECT "select"': '"select"' in joined,
    'quoted fk col "where"': '"where"' in joined,
    'FROM "order"': 'FROM "order"' in joined,
}
for k, v in checks.items():
    print(f"  check {k}: {v}")
if all(checks.values()):
    print("OK all identifiers quoted via quote_name")
    os._exit(0)
print("FAIL some identifier not quoted")
os._exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1 & Req3.4: with table_names=None all tables are checked via the plain
`PRAGMA foreign_key_check` (no per-table interpolation, no parentheses).

Spies on executed SQL while calling check_constraints() with no args on a clean
reserved-word schema. HOLDS iff a bare 'PRAGMA foreign_key_check' (exact, no
'(') query was issued and NO 'PRAGMA foreign_key_check(' interpolated form was.
"""
import os, django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection
from django.db.backends.sqlite3 import base as sqlite_base

class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    class Meta:
        app_label = "contenttypes"

class SQLKeywordsModel(models.Model):
    id = models.AutoField(primary_key=True, db_column="select")
    reporter = models.ForeignKey(Reporter, models.CASCADE, db_column="where")
    class Meta:
        app_label = "contenttypes"
        db_table = "order"

with connection.schema_editor() as se:
    se.create_model(Reporter)
    se.create_model(SQLKeywordsModel)

r = Reporter.objects.create(first_name="John")
SQLKeywordsModel.objects.create(reporter=r)

captured = []
orig = sqlite_base.SQLiteCursorWrapper.execute
def spy(self, query, params=None):
    captured.append(query)
    return orig(self, query, params) if params is not None else orig(self, query)
sqlite_base.SQLiteCursorWrapper.execute = spy

connection.check_constraints()  # no table names

sqlite_base.SQLiteCursorWrapper.execute = orig

plain = [q for q in captured if q.strip() == "PRAGMA foreign_key_check"]
interp = [q for q in captured if "PRAGMA foreign_key_check(" in q]
print("plain 'PRAGMA foreign_key_check' issued:", bool(plain))
print("interpolated per-table form issued:", bool(interp), interp[:2])
if plain and not interp:
    print("OK no-args path uses plain pragma without interpolation")
    os._exit(0)
print("FAIL no-args path does not match Req3.1/3.4")
os._exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2 & Req3.3 & Req3.5 (regression, ORDINARY identifiers):
 - clean ordinary schema: check_constraints completes without raising (3.2)
 - genuine violation under ordinary identifiers: raises IntegrityError with the
   expected descriptive message (3.3)
 - disable/enable + manual check_constraints workflow works (3.5)

Uses ordinary table/column names (no reserved words). HOLDS iff both the clean
call is silent AND the violating call raises IntegrityError mentioning table,
column, and referenced table.
"""
import os, django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection, IntegrityError

class Person(models.Model):
    name = models.CharField(max_length=30)
    class Meta:
        app_label = "contenttypes"

class Book(models.Model):
    title = models.CharField(max_length=30)
    author = models.ForeignKey(Person, models.CASCADE)
    class Meta:
        app_label = "contenttypes"

with connection.schema_editor() as se:
    se.create_model(Person)
    se.create_model(Book)

p = Person.objects.create(name="A")
b = Book.objects.create(title="T", author=p)

# 3.2 clean
try:
    connection.check_constraints(table_names=[Book._meta.db_table])
    connection.check_constraints()
except Exception as e:
    print("FAIL clean check raised", type(e).__name__, str(e)[:120])
    os._exit(1)
print("OK clean ordinary check_constraints completed")

# 3.3 + 3.5 disable/enable workflow with a genuine violation
b.refresh_from_db()
b.author_id = 9999
with connection.constraint_checks_disabled():
    b.save()
    try:
        connection.check_constraints(table_names=[Book._meta.db_table])
    except IntegrityError as e:
        msg = str(e)
        print("OK IntegrityError:", msg[:160])
        ok = (Book._meta.db_table in msg and Person._meta.db_table in msg)
        if ok:
            os._exit(0)
        print("FAIL message missing expected table/column info")
        os._exit(1)
    except Exception as e:
        print("FAIL unexpected", type(e).__name__, str(e)[:120])
        os._exit(1)
    else:
        print("FAIL no exception on ordinary violation")
        os._exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""POSITIVE CONTROL + Req2.4/3.3: genuine FK violation on reserved-word
table/columns raises IntegrityError, NOT an OperationalError syntax error.

Mirrors tests/backends/models.py::SQLKeywordsModel (db_table='order',
pk db_column='select', FK db_column='where') and the F2P test.

HOLDS iff check_constraints(['order']) raises IntegrityError (the intended
violation report). At base it raises OperationalError ('near "order"').
"""
import os, django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection, IntegrityError, OperationalError

class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    class Meta:
        app_label = "contenttypes"

class SQLKeywordsModel(models.Model):
    id = models.AutoField(primary_key=True, db_column="select")
    reporter = models.ForeignKey(Reporter, models.CASCADE, db_column="where")
    class Meta:
        app_label = "contenttypes"
        db_table = "order"

with connection.schema_editor() as se:
    se.create_model(Reporter)
    se.create_model(SQLKeywordsModel)

r = Reporter.objects.create(first_name="John")
obj = SQLKeywordsModel.objects.create(reporter=r)
obj.refresh_from_db()
# Break the FK while constraint checks are disabled.
obj.reporter_id = 30
with connection.constraint_checks_disabled():
    obj.save()
    try:
        connection.check_constraints(table_names=["order"])
    except IntegrityError as e:
        print("OK IntegrityError raised:", str(e)[:120])
        os._exit(0)
    except OperationalError as e:
        print("FAIL OperationalError (syntax error):", str(e)[:120])
        os._exit(1)
    except Exception as e:
        print("FAIL unexpected", type(e).__name__, str(e)[:120])
        os._exit(1)
    else:
        print("FAIL no exception raised (violation not detected)")
        os._exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13807: SQLite check_constraints must quote interpolated identifiers via connection.ops.quote_name so reserved-word table/column names (db_table='order', pk db_column='select', FK db_column='where' per hidden SQLKeywordsModel) no longer crash with OperationalError.

Probes (all standalone python, in-memory sqlite, models under app_label 'contenttypes'):
- probe_1.py (POSITIVE CONTROL, Req2.4/3.3): genuine FK violation on reserved-word table 'order' with pk col 'select' / fk col 'where' -> check_constraints(['order']) must raise IntegrityError (not OperationalError). PATCHED: HOLDS. BASE: VIOLATED (raises OperationalError near "order") => discriminates.
- probe_2.py (Req1.1/1.2): clean reserved-word schema -> check_constraints(['order']) completes without raising. PATCHED: HOLDS.
- probe_3.py (Req1.1/1.3, Req2.1/2.2): spies on executed SQL and asserts PRAGMA foreign_key_check("order"), PRAGMA foreign_key_list("order"), and SELECT with "select"/"where"/FROM "order" all quoted. PATCHED: HOLDS.
- probe_4.py (Req3.1/3.4): check_constraints() with no args issues plain 'PRAGMA foreign_key_check' and NO interpolated per-table form. PATCHED: HOLDS.
- probe_5.py (Req3.2/3.3/3.5 regression, ordinary identifiers): clean call silent; genuine violation raises IntegrityError with table/referenced-table in message; disable/enable workflow works. PATCHED: HOLDS.

Weak candidate (weak_partial.diff): quotes only the Req1 foreign_key_check table name and the foreign_key_list table name + SELECT table name, but leaves primary_key_column_name and column_name UNQUOTED in the reporting SELECT (a partial reading of the requirements that skips Req2.2's column quoting). Applies cleanly at base. Probe results under this candidate: probe_1 VIOLATED (SELECT "select"... unquoted -> the bad column 'where'/'select' reintroduces a syntax error on the reporting path), probe_3 VIOLATED (columns not quoted). probe_2/4/5 HOLD (ordinary/clean paths unaffected). => the suite REJECTS the partial fix, demonstrating discriminating power on the Req2 column-quoting criterion; 1/1 weak candidate rejected.

All 5 probes hold on the patched (gold) tree; positive control fails at base and holds patched; the requirements-conforming-minus-Req2 weak patch is rejected. No violation found; no probe-conforming alternative that would leave the fix incomplete survived. Verdict SOUND.

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
"""POSITIVE CONTROL + Req2.4/3.3: genuine FK violation on reserved-word
table/columns raises IntegrityError, NOT an OperationalError syntax error.

Mirrors tests/backends/models.py::SQLKeywordsModel (db_table='order',
pk db_column='select', FK db_column='where') and the F2P test.

HOLDS iff check_constraints(['order']) raises IntegrityError (the intended
violation report). At base it raises OperationalError ('near "order"').
"""
import os, django
from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    USE_TZ=False,
)
django.setup()

from django.db import models, connection, IntegrityError, OperationalError

class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    class Meta:
        app_label = "contenttypes"

class SQLKeywordsModel(models.Model):
    id = models.AutoField(primary_key=True, db_column="select")
    reporter = models.ForeignKey(Reporter, models.CASCADE, db_column="where")
    class Meta:
        app_label = "contenttypes"
        db_table = "order"

with connection.schema_editor() as se:
    se.create_model(Reporter)
    se.create_model(SQLKeywordsModel)

r = Reporter.objects.create(first_name="John")
obj = SQLKeywordsModel.objects.create(reporter=r)
obj.refresh_from_db()
# Break the FK while constraint checks are disabled.
obj.reporter_id = 30
with connection.constraint_checks_disabled():
    obj.save()
    try:
        connection.check_constraints(table_names=["order"])
    except IntegrityError as e:
        print("OK IntegrityError raised:", str(e)[:120])
        os._exit(0)
    except OperationalError as e:
        print("FAIL OperationalError (syntax error):", str(e)[:120])
        os._exit(1)
    except Exception as e:
        print("FAIL unexpected", type(e).__name__, str(e)[:120])
        os._exit(1)
    else:
        print("FAIL no exception raised (violation not detected)")
        os._exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-13807: SQLite check_constraints must quote interpolated identifiers via connection.ops.quote_name so reserved-word table/column names (db_table='order', pk db_column='select', FK db_column='where' per hidden SQLKeywordsModel) no longer crash with OperationalError.

Probes (all standalone python, in-memory sqlite, models under app_label 'contenttypes'):
- probe_1.py (POSITIVE CONTROL, Req2.4/3.3): genuine FK violation on reserved-word table 'order' with pk col 'select' / fk col 'where' -> check_constraints(['order']) must raise IntegrityError (not OperationalError). PATCHED: HOLDS. BASE: VIOLATED (raises OperationalError near "order") => discriminates.
- probe_2.py (Req1.1/1.2): clean reserved-word schema -> check_constraints(['order']) completes without raising. PATCHED: HOLDS.
- probe_3.py (Req1.1/1.3, Req2.1/2.2): spies on executed SQL and asserts PRAGMA foreign_key_check("order"), PRAGMA foreign_key_list("order"), and SELECT with "select"/"where"/FROM "order" all quoted. PATCHED: HOLDS.
- probe_4.py (Req3.1/3.4): check_constraints() with no args issues plain 'PRAGMA foreign_key_check' and NO interpolated per-table form. PATCHED: HOLDS.
- probe_5.py (Req3.2/3.3/3.5 regression, ordinary identifiers): clean call silent; genuine violation raises IntegrityError with table/referenced-table in message; disable/enable workflow works. PATCHED: HOLDS.

Weak candidate (weak_partial.diff): quotes only the Req1 foreign_key_check table name and the foreign_key_list table name + SELECT table name, but leaves primary_key_column_name and column_name UNQUOTED in the reporting SELECT (a partial reading of the requirements that skips Req2.2's column quoting). Applies cleanly at base. Probe results under this candidate: probe_1 VIOLATED (SELECT "select"... unquoted -> the bad column 'where'/'select' reintroduces a syntax error on the reporting path), probe_3 VIOLATED (columns not quoted). probe_2/4/5 HOLD (ordinary/clean paths unaffected). => the suite REJECTS the partial fix, demonstrating discriminating power on the Req2 column-quoting criterion; 1/1 weak candidate rejected.

All 5 probes hold on the patched (gold) tree; positive control fails at base and holds patched; the requirements-conforming-minus-Req2 weak patch is rejected. No violation found; no probe-conforming alternative that would leave the fix incomplete survived. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements correctly model the full changed behavioral boundary, not a narrow slice: they cover all three quoted sites (both pragmas AND the SELECT's three identifiers), require the reserved-word case to yield IntegrityError, and preserve the unchanged no-table-names path and SQL text. Ran probe on both patched and base trees via nl_attack; results match the requirements. R2.2 explicitly names pk-column and fk-column quoting, matching the patch's quote_name(primary_key_column_name)/quote_name(column_name) additions — no under-modeling of the SELECT identifiers.

Counterexample / evidence:

```
Probe reproducing the issue's exact scenario (db_table='order', db_column='select', FK db_column='where', check_constraints(table_names=['order']) after constraint_checks_disabled with a dangling FK): gold-patched tree -> IntegrityError raised as expected (exit 0, HOLDS); base_commit -> OperationalError: near "order": syntax error (VIOLATED). This is precisely the boundary R2.4 pins.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix as behavior: render every identifier interpolated into check_constraints' PRAGMA/SELECT queries through connection.ops.quote_name. All named identifiers are either public (table name 'order' appears verbatim in problem_statement; the check_constraints function and file paths django/db/backends/sqlite3/base.py are legitimate localization) or generic behavioral descriptions. The hidden test's distinguishing content is NOT leaked: the test/model names (test_check_constraints_sql_keywords, SQLKeywordsModel), the specific reserved-word column values db_column='select' and db_column='where', and the test's disable-then-recheck-with-table_names=['order'] structure. The doc mentions 'primary-key or foreign-key column whose database name is a reserved word' only generically (never naming select/where), which is a faithful translation of the gold edit that quotes primary_key_column_name and column_name — describing behavior, not transmitting the test. No quoted test/gold code, no parametrization ids, no fix-invented identifiers, no case enumeration mirroring tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
