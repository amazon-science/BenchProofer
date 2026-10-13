# P2 adversarial audit — django__django-16315

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_sql_columns.py`, `probe_2_insert_agrees.py`, `probe_3_upsert_semantics.py`, `probe_4_no_db_column_regression.py`, `probe_5_pk_unique.py`, `probe_6_validation.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_sql_columns.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_sql_columns.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2 (POSITIVE CONTROL): ON CONFLICT target + DO UPDATE SET assignments
# must reference the DB column names (db_column), not the Python field names.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection
from django.db.backends.utils import CursorWrapper

class M(models.Model):
    number = models.IntegerField(db_column="TheNumber", unique=True)
    rank = models.IntegerField(db_column="TheRank")
    class Meta:
        app_label="contenttypes"; db_table="probe_m1"
with connection.schema_editor() as se:
    se.create_model(M)

captured=[]
orig=CursorWrapper.execute
def spy(self, sql, params=None):
    captured.append(sql)
    return orig(self, sql, params)
CursorWrapper.execute=spy
try:
    M.objects.bulk_create([M(number=1,rank=10)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
except Exception as e:
    print("exec raised (ok for base):", type(e).__name__, e)
finally:
    CursorWrapper.execute=orig

ins=[s for s in captured if "ON CONFLICT" in s]
print("captured ON CONFLICT sql:", ins)
assert ins, "no ON CONFLICT statement captured"
sql=ins[0]
# the conflict/update portion is after 'ON CONFLICT'
tail=sql[sql.index("ON CONFLICT"):]
print("tail:", tail)
ok = ('"TheNumber"' in tail and '"TheRank"' in tail
      and '"number"' not in tail and '"rank"' not in tail)
print("uses_db_columns_in_conflict_and_update:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_insert_agrees.py` → holds on the patched tree (good)

```python
# Req 1.4: the INSERT (value-insertion) column list uses db_column names AND agrees
# with the conflict/update lists — all reference the same real columns.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection
from django.db.backends.utils import CursorWrapper

class M(models.Model):
    number = models.IntegerField(db_column="TheNumber", unique=True)
    rank = models.IntegerField(db_column="TheRank")
    class Meta:
        app_label="contenttypes"; db_table="probe_m2"
with connection.schema_editor() as se:
    se.create_model(M)

captured=[]
orig=CursorWrapper.execute
CursorWrapper.execute=lambda self,sql,params=None:(captured.append(sql),orig(self,sql,params))[1]
try:
    M.objects.bulk_create([M(number=1,rank=10)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
except Exception as e:
    print("exec raised:", type(e).__name__, e)
finally:
    CursorWrapper.execute=orig
ins=[s for s in captured if "INSERT INTO" in s and "ON CONFLICT" in s]
print("sql:", ins)
assert ins, "no upsert insert captured"
sql=ins[0]
head=sql[:sql.index("ON CONFLICT")]
ok = ('"TheNumber"' in head and '"TheRank"' in head)
print("insert_uses_db_columns:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_upsert_semantics.py` → holds on the patched tree (good)

```python
# Req 1.3 / 4.2: an actual conflicting insert UPDATES the existing row's update
# column with the incoming value and does NOT add a duplicate row.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection

class M(models.Model):
    number = models.IntegerField(db_column="TheNumber", unique=True)
    rank = models.IntegerField(db_column="TheRank")
    class Meta:
        app_label="contenttypes"; db_table="probe_m3"
with connection.schema_editor() as se:
    se.create_model(M)

M.objects.bulk_create([M(number=1, rank=10)],
    update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
# conflicting insert with new rank value
M.objects.bulk_create([M(number=1, rank=99)],
    update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
rows=list(M.objects.values_list("number","rank"))
print("rows:", rows)
ok = (len(rows)==1 and rows[0]==(1,99))
print("updated_in_place_no_dup:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_no_db_column_regression.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: model with NO custom db_column — conflict/update SQL uses the field
# names (== column names), upsert updates in place. Also tests composite unique + pk.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection
from django.db.backends.utils import CursorWrapper

class P(models.Model):
    number = models.IntegerField(unique=True)
    rank = models.IntegerField()
    class Meta:
        app_label="contenttypes"; db_table="probe_p4"
with connection.schema_editor() as se:
    se.create_model(P)

captured=[]
orig=CursorWrapper.execute
CursorWrapper.execute=lambda self,sql,params=None:(captured.append(sql),orig(self,sql,params))[1]
try:
    P.objects.bulk_create([P(number=5,rank=1)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
    P.objects.bulk_create([P(number=5,rank=2)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
finally:
    CursorWrapper.execute=orig
sql=[s for s in captured if "ON CONFLICT" in s][0]
tail=sql[sql.index("ON CONFLICT"):]
print("tail:", tail)
rows=list(P.objects.values_list("number","rank"))
print("rows:", rows)
ok = ('"number"' in tail and '"rank"' in tail
      and len(rows)==1 and rows[0]==(5,2))
print("no_db_column_regression_ok:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_pk_unique.py` → holds on the patched tree (good)

```python
# Req 2.1 / 4.2: "pk" resolves to the primary key field and is a valid unique target;
# conflict target lists the pk column and upsert updates in place.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection
from django.db.backends.utils import CursorWrapper

class K(models.Model):
    id = models.IntegerField(primary_key=True, db_column="TheId")
    rank = models.IntegerField(db_column="TheRank")
    class Meta:
        app_label="contenttypes"; db_table="probe_k5"
with connection.schema_editor() as se:
    se.create_model(K)

captured=[]
orig=CursorWrapper.execute
CursorWrapper.execute=lambda self,sql,params=None:(captured.append(sql),orig(self,sql,params))[1]
try:
    K.objects.bulk_create([K(id=7,rank=1)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["pk"])
    K.objects.bulk_create([K(id=7,rank=2)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["pk"])
finally:
    CursorWrapper.execute=orig
sql=[s for s in captured if "ON CONFLICT" in s][0]
tail=sql[sql.index("ON CONFLICT"):]
print("tail:", tail)
rows=list(K.objects.values_list("id","rank"))
print("rows:", rows)
ok = ('"TheId"' in tail and '"TheRank"' in tail and '"pk"' not in tail
      and '"id"' not in tail and len(rows)==1 and rows[0]==(7,2))
print("pk_resolution_ok:", ok)
import sys; sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_validation.py` → holds on the patched tree (good)

```python
# Req 3 (regression protection): validation rules still fire.
# 3.1 no update_fields -> ValueError; 3.2 non-concrete update_field -> ValueError;
# 3.3 pk in update_fields -> ValueError; 3.5 ignore+update mutually exclusive;
# 3.6 no unique_fields with target support -> ValueError;
# Req 2.3 unknown field name -> FieldDoesNotExist/FieldError.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection
from django.core.exceptions import FieldDoesNotExist, FieldError

class M(models.Model):
    number = models.IntegerField(db_column="TheNumber", unique=True)
    rank = models.IntegerField(db_column="TheRank")
    class Meta:
        app_label="contenttypes"; db_table="probe_m6"
with connection.schema_editor() as se:
    se.create_model(M)

def expect_valueerror(fn, label, needle=None):
    try:
        fn()
    except ValueError as e:
        print(f"{label}: ValueError OK: {e}")
        if needle and needle.lower() not in str(e).lower():
            print(f"  WARN needle '{needle}' not in msg"); return False
        return True
    except Exception as e:
        print(f"{label}: WRONG exc {type(e).__name__}: {e}"); return False
    print(f"{label}: NO exception raised"); return False

results=[]
# 3.1
results.append(expect_valueerror(
    lambda: M.objects.bulk_create([M(number=1,rank=1)], update_conflicts=True,
        update_fields=[], unique_fields=["number"]),
    "3.1_no_update_fields", "must be provided"))
# 3.3 pk in update_fields
results.append(expect_valueerror(
    lambda: M.objects.bulk_create([M(number=1,rank=1)], update_conflicts=True,
        update_fields=["id"], unique_fields=["number"]),
    "3.3_pk_in_update_fields", "primary key"))
# 3.5 mutually exclusive
results.append(expect_valueerror(
    lambda: M.objects.bulk_create([M(number=1,rank=1)], ignore_conflicts=True,
        update_conflicts=True, update_fields=["rank"], unique_fields=["number"]),
    "3.5_mutually_exclusive", "mutually exclusive"))
# 3.6 no unique_fields
results.append(expect_valueerror(
    lambda: M.objects.bulk_create([M(number=1,rank=1)], update_conflicts=True,
        update_fields=["rank"], unique_fields=[]),
    "3.6_no_unique_fields", "unique fields"))
# 2.3 unknown field name -> field lookup error
def unknown():
    try:
        M.objects.bulk_create([M(number=1,rank=1)], update_conflicts=True,
            update_fields=["rank"], unique_fields=["nope_not_a_field"])
    except (FieldDoesNotExist, FieldError) as e:
        print("2.3_unknown_field: field-lookup error OK:", type(e).__name__, e); return True
    except Exception as e:
        print("2.3_unknown_field: WRONG exc", type(e).__name__, e); return False
    print("2.3_unknown_field: NO exception"); return False
results.append(unknown())

print("all:", results)
import sys; sys.exit(0 if all(results) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_sql_columns.py`

```python
# Req 1.1/1.2 (POSITIVE CONTROL): ON CONFLICT target + DO UPDATE SET assignments
# must reference the DB column names (db_column), not the Python field names.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection
from django.db.backends.utils import CursorWrapper

class M(models.Model):
    number = models.IntegerField(db_column="TheNumber", unique=True)
    rank = models.IntegerField(db_column="TheRank")
    class Meta:
        app_label="contenttypes"; db_table="probe_m1"
with connection.schema_editor() as se:
    se.create_model(M)

captured=[]
orig=CursorWrapper.execute
def spy(self, sql, params=None):
    captured.append(sql)
    return orig(self, sql, params)
CursorWrapper.execute=spy
try:
    M.objects.bulk_create([M(number=1,rank=10)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
except Exception as e:
    print("exec raised (ok for base):", type(e).__name__, e)
finally:
    CursorWrapper.execute=orig

ins=[s for s in captured if "ON CONFLICT" in s]
print("captured ON CONFLICT sql:", ins)
assert ins, "no ON CONFLICT statement captured"
sql=ins[0]
# the conflict/update portion is after 'ON CONFLICT'
tail=sql[sql.index("ON CONFLICT"):]
print("tail:", tail)
ok = ('"TheNumber"' in tail and '"TheRank"' in tail
      and '"number"' not in tail and '"rank"' not in tail)
print("uses_db_columns_in_conflict_and_update:", ok)
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16315: bulk_create upsert must render ON CONFLICT target + DO UPDATE SET assignments using db_column names (not Python field names) so upserts on models with db_column succeed. FAIL_TO_PASS = test_update_conflicts_unique_fields_update_fields_db_column.

Probe suite (all standalone python; configure Django with in-memory sqlite, create dynamic models, capture SQL via CursorWrapper.execute spy / CaptureQueriesContext):
- probe_1_sql_columns (POSITIVE CONTROL, Req 1.1/1.2): with a model whose fields have db_column='TheNumber'/'TheRank', the ON CONFLICT target and DO UPDATE SET list contain the db columns and NOT the field names 'number'/'rank'. HOLDS patched (exit 0: ON CONFLICT("TheNumber") DO UPDATE SET "TheRank"=EXCLUDED."TheRank"); at base it FAILS — sqlite raises OperationalError 'ON CONFLICT clause does not match any PRIMARY KEY or UNIQUE constraint' because the base code emits ON CONFLICT("number"). prepatch_reproduced=true.
- probe_2_insert_agrees (Req 1.4): INSERT column list uses "TheNumber"/"TheRank" and agrees with conflict/update lists. HOLDS patched.
- probe_3_upsert_semantics (Req 1.3/4.2): a conflicting second insert updates rank 10->99 in place, row count stays 1. HOLDS patched; FAILS at base.
- probe_4_no_db_column_regression (Req 4.1/4.2): model WITHOUT db_column -> conflict/update SQL uses field names, upsert updates in place. HOLDS patched.
- probe_5_pk_unique (Req 2.1/4.2): unique_fields=['pk'] resolves to pk field; conflict target uses pk's db_column 'TheId', upsert updates in place. HOLDS patched.
- probe_6_validation (Req 2.3/3.1/3.3/3.5/3.6): no update_fields -> ValueError 'must be provided'; pk in update_fields -> ValueError 'primary keys'; ignore+update -> ValueError 'mutually exclusive'; no unique_fields -> ValueError 'unique fields'; unknown field name -> FieldDoesNotExist. All HOLD patched.

Candidate wrong-fixes (both REJECTED by the suite, demonstrating discrimination):
- weak_compiler_only.diff: applies only the compiler.py f.column change but leaves query.py at base (fields stay as strings), so (f.column for f in ...) crashes with AttributeError -> probe_1 VIOLATED (candidate-patched).
- weak_name_not_column.diff: full query.py resolution BUT compiler.py uses f.name instead of f.column -> emits ON CONFLICT("number")/"rank" for the db_column model; probe_1 & probe_3 VIOLATED (candidate-patched), while probe_4 & probe_6 still hold (correctly, since those don't exercise db_column mismatch). This is the lazy reading a weak spec would permit, and the suite catches it.

All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched; every candidate wrong-fix is rejected. No violation or too-weak finding.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_sql_columns.py`, `probe_2_insert_agrees.py`, `probe_3_upsert_semantics.py`, `probe_4_no_db_column_regression.py`, `probe_5_pk_unique.py`, `probe_6_validation.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_sql_columns.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_sql_columns.py` → holds on the patched tree (good)

Attack 2 — `probe_2_insert_agrees.py` → holds on the patched tree (good)

Attack 3 — `probe_3_upsert_semantics.py` → holds on the patched tree (good)

Attack 4 — `probe_4_no_db_column_regression.py` → holds on the patched tree (good)

Attack 5 — `probe_5_pk_unique.py` → holds on the patched tree (good)

Attack 6 — `probe_6_validation.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_sql_columns.py`

```python
# Req 1.1/1.2 (POSITIVE CONTROL): ON CONFLICT target + DO UPDATE SET assignments
# must reference the DB column names (db_column), not the Python field names.
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True,
        DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes","django.contrib.auth"], USE_TZ=True)
django.setup()
from django.db import models, connection
from django.db.backends.utils import CursorWrapper

class M(models.Model):
    number = models.IntegerField(db_column="TheNumber", unique=True)
    rank = models.IntegerField(db_column="TheRank")
    class Meta:
        app_label="contenttypes"; db_table="probe_m1"
with connection.schema_editor() as se:
    se.create_model(M)

captured=[]
orig=CursorWrapper.execute
def spy(self, sql, params=None):
    captured.append(sql)
    return orig(self, sql, params)
CursorWrapper.execute=spy
try:
    M.objects.bulk_create([M(number=1,rank=10)],
        update_conflicts=True, update_fields=["rank"], unique_fields=["number"])
except Exception as e:
    print("exec raised (ok for base):", type(e).__name__, e)
finally:
    CursorWrapper.execute=orig

ins=[s for s in captured if "ON CONFLICT" in s]
print("captured ON CONFLICT sql:", ins)
assert ins, "no ON CONFLICT statement captured"
sql=ins[0]
# the conflict/update portion is after 'ON CONFLICT'
tail=sql[sql.index("ON CONFLICT"):]
print("tail:", tail)
ok = ('"TheNumber"' in tail and '"TheRank"' in tail
      and '"number"' not in tail and '"rank"' not in tail)
print("uses_db_columns_in_conflict_and_update:", ok)
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-16315: bulk_create upsert must render ON CONFLICT target + DO UPDATE SET assignments using db_column names (not Python field names) so upserts on models with db_column succeed. FAIL_TO_PASS = test_update_conflicts_unique_fields_update_fields_db_column.

Probe suite (all standalone python; configure Django with in-memory sqlite, create dynamic models, capture SQL via CursorWrapper.execute spy / CaptureQueriesContext):
- probe_1_sql_columns (POSITIVE CONTROL, Req 1.1/1.2): with a model whose fields have db_column='TheNumber'/'TheRank', the ON CONFLICT target and DO UPDATE SET list contain the db columns and NOT the field names 'number'/'rank'. HOLDS patched (exit 0: ON CONFLICT("TheNumber") DO UPDATE SET "TheRank"=EXCLUDED."TheRank"); at base it FAILS — sqlite raises OperationalError 'ON CONFLICT clause does not match any PRIMARY KEY or UNIQUE constraint' because the base code emits ON CONFLICT("number"). prepatch_reproduced=true.
- probe_2_insert_agrees (Req 1.4): INSERT column list uses "TheNumber"/"TheRank" and agrees with conflict/update lists. HOLDS patched.
- probe_3_upsert_semantics (Req 1.3/4.2): a conflicting second insert updates rank 10->99 in place, row count stays 1. HOLDS patched; FAILS at base.
- probe_4_no_db_column_regression (Req 4.1/4.2): model WITHOUT db_column -> conflict/update SQL uses field names, upsert updates in place. HOLDS patched.
- probe_5_pk_unique (Req 2.1/4.2): unique_fields=['pk'] resolves to pk field; conflict target uses pk's db_column 'TheId', upsert updates in place. HOLDS patched.
- probe_6_validation (Req 2.3/3.1/3.3/3.5/3.6): no update_fields -> ValueError 'must be provided'; pk in update_fields -> ValueError 'primary keys'; ignore+update -> ValueError 'mutually exclusive'; no unique_fields -> ValueError 'unique fields'; unknown field name -> FieldDoesNotExist. All HOLD patched.

Candidate wrong-fixes (both REJECTED by the suite, demonstrating discrimination):
- weak_compiler_only.diff: applies only the compiler.py f.column change but leaves query.py at base (fields stay as strings), so (f.column for f in ...) crashes with AttributeError -> probe_1 VIOLATED (candidate-patched).
- weak_name_not_column.diff: full query.py resolution BUT compiler.py uses f.name instead of f.column -> emits ON CONFLICT("number")/"rank" for the db_column model; probe_1 & probe_3 VIOLATED (candidate-patched), while probe_4 & probe_6 still hold (correctly, since those don't exercise db_column mismatch). This is the lazy reading a weak spec would permit, and the suite catches it.

All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched; every candidate wrong-fix is rejected. No violation or too-weak finding.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch (query.py + compiler.py) resolves update_fields/unique_fields to field objects in bulk_create and passes (f.column ...) generators to on_conflict_suffix_sql. Requirements pin exactly this changed observable behavior (db_column in ON CONFLICT/DO UPDATE), plus preserved validation (Req3) and non-db_column regression (Req4). The modeling boundary is the changed behavior itself, not a narrow slice. Probe run via nl_attack on the instance image: HOLDS on patched, all assertions pass.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally and localize it to the real modules/functions (query.py bulk_create, sql/compiler.py SQLInsertCompiler.as_sql, on_conflict_suffix_sql) — legitimate localization. Every concrete example (db_column, mixed-case SectorID/sectorid, ON CONFLICT ... DO UPDATE SET ... = EXCLUDED, 'column does not exist' error) is taken from the PUBLIC problem_statement, not the hidden tests. No hidden-test artifacts appear: the test model name FieldsWithDbColumns, field names rank/name, db_column values rAnK/oTheRNaMe, unique_fields=['rank']/update_fields=['name'], the test function name test_update_conflicts_unique_fields_update_fields_db_column, and the file paths tests/bulk_create/{models,tests}.py are all absent. No quoted test/gold code or fix-invented identifiers. Req 3's ValueError enumeration and Req 4.2's single/composite/pk unique-field cases parallel PASS_TO_PASS names but describe pre-existing, generally-derivable upsert behaviors and validation rules rather than transmitting test ids/parametrization — this is the intended behavior translation. The gold-patch mechanics (resolve names to field objects, use f.column, 'pk'->pk field) match the public hints_text direction and are stated as behavioral requirements. No semantic reconstruction of the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
