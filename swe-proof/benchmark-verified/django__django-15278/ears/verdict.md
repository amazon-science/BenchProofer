# P2 adversarial audit — django__django-15278

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)

f = models.IntegerField(null=True, unique=True)
f.set_attributes_from_name('code')
sql, _ = collected_for(f)
print("SQL:", sql)
ok = is_remake(sql) and not is_plain_alter(sql)
print("remake=%s plain_alter=%s" % (is_remake(sql), is_plain_alter(sql)))
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)
Author = make_author()
with connection.schema_editor() as ed:
    ed.create_model(Author)
# populate a row
Author.objects.create(name="alice")
o2o = models.OneToOneField(Author, null=True, on_delete=models.CASCADE)
o2o.set_attributes_from_name('boss')
try:
    with connection.schema_editor() as ed:
        ed.add_field(Author, o2o)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
# inspect column
with connection.cursor() as c:
    cols = connection.introspection.get_table_description(c, Author._meta.db_table)
info = {col.name: col for col in cols}
print("columns:", list(info))
if 'boss_id' not in info:
    print("boss_id column missing"); sys.exit(1)
if not info['boss_id'].null_ok:
    print("boss_id not nullable"); sys.exit(1)
# existing row preserved
with connection.cursor() as c:
    c.execute("SELECT name FROM %s" % Author._meta.db_table)
    rows=[r[0] for r in c.fetchall()]
print("rows:", rows)
if rows != ["alice"]:
    print("row not preserved"); sys.exit(1)
print("OK: o2o added, column nullable, row preserved")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)
f = models.IntegerField(primary_key=True)
f.set_attributes_from_name('pk2')
sql, _ = collected_for(f)
print("SQL:", sql)
ok = is_remake(sql) and not is_plain_alter(sql)
print("remake=%s plain_alter=%s" % (is_remake(sql), is_plain_alter(sql)))
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)
f = models.IntegerField(null=True)
f.set_attributes_from_name('plainint')
sql, _ = collected_for(f)
print("SQL:", sql)
ok = is_plain_alter(sql) and not is_remake(sql)
print("remake=%s plain_alter=%s" % (is_remake(sql), is_plain_alter(sql)))
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)
f = models.IntegerField(null=False, default=0)
f.set_attributes_from_name('nn')
sql, _ = collected_for(f)
print("SQL:", sql)
# non-nullable -> remake regardless
ok = is_remake(sql) and not is_plain_alter(sql)
print("remake=%s plain_alter=%s" % (is_remake(sql), is_plain_alter(sql)))
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)
f = models.IntegerField(null=True, default=7)
f.set_attributes_from_name('defint')
sql, _ = collected_for(f)
print("SQL:", sql)
ok = is_remake(sql) and not is_plain_alter(sql)
print("remake=%s plain_alter=%s" % (is_remake(sql), is_plain_alter(sql)))
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)
Author = make_author()
with connection.schema_editor() as ed:
    ed.create_model(Author)
# populate a row
Author.objects.create(name="alice")
o2o = models.OneToOneField(Author, null=True, on_delete=models.CASCADE)
o2o.set_attributes_from_name('boss')
try:
    with connection.schema_editor() as ed:
        ed.add_field(Author, o2o)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
# inspect column
with connection.cursor() as c:
    cols = connection.introspection.get_table_description(c, Author._meta.db_table)
info = {col.name: col for col in cols}
print("columns:", list(info))
if 'boss_id' not in info:
    print("boss_id column missing"); sys.exit(1)
if not info['boss_id'].null_ok:
    print("boss_id not nullable"); sys.exit(1)
# existing row preserved
with connection.cursor() as c:
    c.execute("SELECT name FROM %s" % Author._meta.db_table)
    rows=[r[0] for r in c.fetchall()]
print("rows:", rows)
if rows != ["alice"]:
    print("row not preserved"); sys.exit(1)
print("OK: o2o added, column nullable, row preserved")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Probe suite (collect_sql-based path detection + live add_field on populated table) covering all 9 EARS criteria across the instance Docker image.

### PROBE RESULTS (patched / base / weak_pkonly candidate):
- probe_1 (Req1.1: unique field -> remake, not plain ALTER): HOLDS patched / VIOLATED base (emits `ALTER TABLE ADD COLUMN ... UNIQUE`) / VIOLATED under weak_pkonly.
- probe_2 (POSITIVE CONTROL; Req1.2+1.3+2.5: nullable O2O added to populated table w/o error, column present & NULL-ok, existing row preserved): HOLDS patched / VIOLATED base (`OperationalError: Cannot add a UNIQUE column`) / VIOLATED under weak_pkonly. Discriminates.
- probe_3 (Req1.4: primary-key field -> remake): HOLDS patched / HOLDS base (base already remakes for pk via not-null branch) / HOLDS weak.
- probe_4 (Req2.3: nullable, no default, non-pk, non-unique -> inherited plain ADD COLUMN): HOLDS on all trees.
- probe_5 (Req2.1: non-nullable field -> remake): HOLDS on all trees.
- probe_6 (Req2.2: nullable field with effective default -> remake): HOLDS on all trees.

CANDIDATE PATCH: weak_pkonly.diff adds only `field.primary_key` to the guard, omitting `field.unique` — a partial/lazy reading of Req1. It is REJECTED by probes 1 and 2 (unique/O2O still take the plain ALTER path and crash), demonstrating the suite discriminates wrong implementations. No requirement-conforming-yet-wrong patch was found; the unique-column criterion is the crux and any conforming patch must handle it.

All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced). Requirements are faithful to the gold patch and strong enough to reject the naive pk-only fix.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
import django, sys
from django.conf import settings
settings.configure(DEBUG=True,
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'], USE_TZ=True)
django.setup()
from django.db import connection, models

def make_author():
    class Author(models.Model):
        name = models.CharField(max_length=50)
        class Meta:
            app_label='exp'
    return Author

def collected_for(field, model=None):
    if model is None:
        model = make_author()
    with connection.schema_editor() as ed:
        ed.create_model(model)
    with connection.schema_editor(collect_sql=True) as ed:
        ed.add_field(model, field)
        return list(ed.collected_sql), model

def is_remake(sql_list):
    joined = "\n".join(sql_list)
    return "new__" in joined and "CREATE TABLE" in joined

def is_plain_alter(sql_list):
    joined = "\n".join(sql_list)
    return ("ADD COLUMN" in joined) and ("new__" not in joined)
Author = make_author()
with connection.schema_editor() as ed:
    ed.create_model(Author)
# populate a row
Author.objects.create(name="alice")
o2o = models.OneToOneField(Author, null=True, on_delete=models.CASCADE)
o2o.set_attributes_from_name('boss')
try:
    with connection.schema_editor() as ed:
        ed.add_field(Author, o2o)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
# inspect column
with connection.cursor() as c:
    cols = connection.introspection.get_table_description(c, Author._meta.db_table)
info = {col.name: col for col in cols}
print("columns:", list(info))
if 'boss_id' not in info:
    print("boss_id column missing"); sys.exit(1)
if not info['boss_id'].null_ok:
    print("boss_id not nullable"); sys.exit(1)
# existing row preserved
with connection.cursor() as c:
    c.execute("SELECT name FROM %s" % Author._meta.db_table)
    rows=[r[0] for r in c.fetchall()]
print("rows:", rows)
if rows != ["alice"]:
    print("row not preserved"); sys.exit(1)
print("OK: o2o added, column nullable, row preserved")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Probe suite (collect_sql-based path detection + live add_field on populated table) covering all 9 EARS criteria across the instance Docker image.

### PROBE RESULTS (patched / base / weak_pkonly candidate):
- probe_1 (Req1.1: unique field -> remake, not plain ALTER): HOLDS patched / VIOLATED base (emits `ALTER TABLE ADD COLUMN ... UNIQUE`) / VIOLATED under weak_pkonly.
- probe_2 (POSITIVE CONTROL; Req1.2+1.3+2.5: nullable O2O added to populated table w/o error, column present & NULL-ok, existing row preserved): HOLDS patched / VIOLATED base (`OperationalError: Cannot add a UNIQUE column`) / VIOLATED under weak_pkonly. Discriminates.
- probe_3 (Req1.4: primary-key field -> remake): HOLDS patched / HOLDS base (base already remakes for pk via not-null branch) / HOLDS weak.
- probe_4 (Req2.3: nullable, no default, non-pk, non-unique -> inherited plain ADD COLUMN): HOLDS on all trees.
- probe_5 (Req2.1: non-nullable field -> remake): HOLDS on all trees.
- probe_6 (Req2.2: nullable field with effective default -> remake): HOLDS on all trees.

CANDIDATE PATCH: weak_pkonly.diff adds only `field.primary_key` to the guard, omitting `field.unique` — a partial/lazy reading of Req1. It is REJECTED by probes 1 and 2 (unique/O2O still take the plain ALTER path and crash), demonstrating the suite discriminates wrong implementations. No requirement-conforming-yet-wrong patch was found; the unique-column criterion is the crux and any conforming patch must handle it.

All 6 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced). Requirements are faithful to the gold patch and strong enough to reject the naive pk-only fix.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes add_field's decision to: field.primary_key OR field.unique OR not field.null OR effective_default(field) is not None -> _remake_table, else super().add_field (plain ALTER TABLE ADD COLUMN). Req 1.1=field.unique(incl o2o), Req 1.4=field.primary_key, Req 2.1=not field.null, Req 2.2=effective_default not None, Req 2.3=else branch (nullable, no default, not pk, not unique -> plain ALTER). Modeling boundary is precisely the changed observable branch decision, not a sub-helper. Probe: patched HOLDS exit=0 'OK nullable o2o added'; base VIOLATED 'Cannot add a UNIQUE column'.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior of the SQLite add_field decision (remake-table vs ALTER TABLE ADD COLUMN) and legitimately localizes to django.db.backends.sqlite3.schema.DatabaseSchemaEditor.add_field. No hidden-test content transmitted: no test names (test_add_field_o2o_nullable), no path (tests/schema/tests.py), no parametrization ids, no quoted test/gold code, no fix-invented identifiers (e.g., 'note_id', the column-index assertion columns['note_id'][1][6]). Req 1.4's primary-key clause reflects the gold edit's added condition (field.primary_key or field.unique) but is stated as a general behavioral rule, not as a test — and there is no PK case in FAIL_TO_PASS to reconstruct. Req 2.4's field-kind enumeration (binary/defaulted/text-transformed) names general behavioral categories, not test parametrization ids. Req 1.3's NULL-permitting/column-present assertion is a behavioral translation, not the test's mechanism. This is exactly the intended translate-tests-into-behavior; the tests themselves are not transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
