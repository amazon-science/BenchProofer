# P2 adversarial audit — django__django-14434

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
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint

class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'
        db_table = 'probe_table'

with connection.schema_editor() as editor:
    constraint = UniqueConstraint(fields=['name'], name='name_uq')
    sql = constraint.create_sql(ProbeModel, editor)

table = ProbeModel._meta.db_table
rc = sql.references_column(table, 'name')
print("references_column(table,'name') =", repr(rc))
assert rc is True, "references_column must be True for covered column"
print("PASS")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint

class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = "contenttypes"
        db_table = "probe_table"
table = ProbeModel._meta.db_table

with connection.schema_editor() as editor:
    sql = UniqueConstraint(fields=["name"], name="name_uq").create_sql(ProbeModel, editor)

# R1.2 uncovered column -> False
r_uncov = sql.references_column(table, "age")
print("references_column(table,'age') =", repr(r_uncov))
assert r_uncov is False, "uncovered column must be False (identity)"

# R1.3 other table -> False for every column
r_other = sql.references_column("other_table", "name")
print("references_column('other_table','name') =", repr(r_other))
assert r_other is False

# R2.1 references_table True for own table (identity)
rt = sql.references_table(table)
print("references_table(table) =", repr(rt))
assert rt is True

# R2.2 other table -> False
rt_other = sql.references_table("other_table")
print("references_table('other_table') =", repr(rt_other))
assert rt_other is False
print("PASS")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint

class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = "contenttypes"
        db_table = "probe_table"
table = ProbeModel._meta.db_table

with connection.schema_editor() as editor:
    sql = UniqueConstraint(fields=["name"], name="name_uq").create_sql(ProbeModel, editor)
rendered = str(sql)
print("rendered =", rendered)
# Expected SQL for sqlite: CREATE UNIQUE INDEX "name_uq" ON "probe_table" ("name")
expected = 'CREATE UNIQUE INDEX "name_uq" ON "probe_table" ("name")'
assert rendered == expected, "rendered SQL / quoting must be exactly %r" % expected
print("PASS")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint

class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = "contenttypes"
        db_table = "probe_table"
table = ProbeModel._meta.db_table

with connection.schema_editor() as editor:
    # no name supplied -> auto-generate from table + columns
    sql = UniqueConstraint(fields=["name", "age"], name="x").create_sql(ProbeModel, editor)
rendered = str(sql)
print("named rendered =", rendered)
expected = 'CREATE UNIQUE INDEX "x" ON "probe_table" ("name", "age")'
assert rendered == expected, "multi-col named SQL must be %r" % expected
# both columns referenced
assert sql.references_column(table, "name") is True
assert sql.references_column(table, "age") is True
print("PASS")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint

class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = "contenttypes"
        db_table = "probe_table"
table = ProbeModel._meta.db_table

with connection.schema_editor() as editor:
    sql = UniqueConstraint(fields=["name"], name="name_uq").create_sql(ProbeModel, editor)
# rename table
sql.rename_table_references(table, "new_table")
print("after rename_table: references_table(new_table)=", repr(sql.references_table("new_table")),
      " references_table(old)=", repr(sql.references_table(table)))
assert sql.references_table("new_table") is True
assert sql.references_table(table) is False
assert sql.references_column("new_table", "name") is True
# rename column
sql.rename_column_references("new_table", "name", "fullname")
print("after rename_col: references_column(new_table,fullname)=", repr(sql.references_column("new_table", "fullname")),
      " references_column(new_table,name)=", repr(sql.references_column("new_table", "name")))
assert sql.references_column("new_table", "fullname") is True
assert sql.references_column("new_table", "name") is False
print("PASS")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}, INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"], USE_TZ=False)
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint, F
from django.db.models.functions import Lower
class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = "contenttypes"
        db_table = "probe_table"
table = ProbeModel._meta.db_table

if not connection.features.supports_expression_indexes:
    print("backend lacks supports_expression_indexes; criterion vacuously holds")
    print("PASS"); raise SystemExit(0)
with connection.schema_editor() as editor:
    sql = UniqueConstraint(Lower("name"), name="func_uq").create_sql(ProbeModel, editor)
rt = sql.references_table(table)
rc = sql.references_column(table, "name")
print("expr: references_table =", repr(rt), " references_column(name) =", repr(rc))
assert rt is True, "expr constraint must reference its table"
assert rc is True, "expr constraint must reference the concrete column it resolves to"
# uncovered column still False
assert sql.references_column(table, "age") is False
print("PASS")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint

class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'
        db_table = 'probe_table'

with connection.schema_editor() as editor:
    constraint = UniqueConstraint(fields=['name'], name='name_uq')
    sql = constraint.create_sql(ProbeModel, editor)

table = ProbeModel._meta.db_table
rc = sql.references_column(table, 'name')
print("references_column(table,'name') =", repr(rc))
assert rc is True, "references_column must be True for covered column"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14434: _create_unique_sql passed a Table wrapper (not the plain table-name string) to the columns/name/expressions parts, so references_column always returned False. Gold patch stores the plain string in those parts and wraps only Statement's table=.

Probes (all HOLD on patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): references_column(table,'name') is True. HOLDS patched, VIOLATED at base (AssertionError) => discriminates, prepatch reproduced.
- probe_2 (R1.2/1.3/1.4/R2.1/2.2): uncovered column -> False (identity), other table -> False, references_table(table) is True, other table -> False. All boolean-identity checks.
- probe_3 (R3.1): rendered SQL exactly 'CREATE UNIQUE INDEX "name_uq" ON "probe_table" ("name")' with table+column quoting preserved.
- probe_4 (R3.2): named + multi-column auto SQL exact, both columns referenced.
- probe_5 (R3.5): rename_table_references / rename_column_references update table & column reporting (new True, old False, both directions).
- probe_6 (R3.4): expression-based (Lower('name')) constraint reports references_table True and references_column('name') True, uncovered 'age' False.

CANDIDATE PATCH (weak.diff): gold column-path fix applied BUT Statement(table=...) left as the bare plain string instead of Table(table, self.quote_name). This is the lazy/partial fix a weak reading permits (it makes references_column pass, so it would satisfy the column-membership criteria). My suite REJECTS it: probe_3 fails because the rendered SQL emits the table identifier UNQUOTED (R3.1 violated). Demonstrated: probe_1/2/5 HOLD under the candidate, probe_3 VIOLATED. This proves the probe suite discriminates wrong implementations.

Note on probe_6: at base the expression branch already received the plain string, so probe_6 does not discriminate base-vs-patched by itself; it is a regression-coverage probe (R3.4). probe_1 is the discriminating positive control. An earlier candidate (fixing only _index_columns arg) was found to actually resolve the F2P test, so it was replaced with the partial-unwrapped-table candidate which the suite rejects.

Verdict SOUND: 6 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 wrong candidate exercised and REJECTED by the suite.

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
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=False,
    )
django.setup()
from django.db import connection, models
from django.db.models import UniqueConstraint

class ProbeModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    class Meta:
        app_label = 'contenttypes'
        db_table = 'probe_table'

with connection.schema_editor() as editor:
    constraint = UniqueConstraint(fields=['name'], name='name_uq')
    sql = constraint.create_sql(ProbeModel, editor)

table = ProbeModel._meta.db_table
rc = sql.references_column(table, 'name')
print("references_column(table,'name') =", repr(rc))
assert rc is True, "references_column must be True for covered column"
print("PASS")
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14434: _create_unique_sql passed a Table wrapper (not the plain table-name string) to the columns/name/expressions parts, so references_column always returned False. Gold patch stores the plain string in those parts and wraps only Statement's table=.

Probes (all HOLD on patched tree):
- probe_1 (R1.1, POSITIVE CONTROL): references_column(table,'name') is True. HOLDS patched, VIOLATED at base (AssertionError) => discriminates, prepatch reproduced.
- probe_2 (R1.2/1.3/1.4/R2.1/2.2): uncovered column -> False (identity), other table -> False, references_table(table) is True, other table -> False. All boolean-identity checks.
- probe_3 (R3.1): rendered SQL exactly 'CREATE UNIQUE INDEX "name_uq" ON "probe_table" ("name")' with table+column quoting preserved.
- probe_4 (R3.2): named + multi-column auto SQL exact, both columns referenced.
- probe_5 (R3.5): rename_table_references / rename_column_references update table & column reporting (new True, old False, both directions).
- probe_6 (R3.4): expression-based (Lower('name')) constraint reports references_table True and references_column('name') True, uncovered 'age' False.

CANDIDATE PATCH (weak.diff): gold column-path fix applied BUT Statement(table=...) left as the bare plain string instead of Table(table, self.quote_name). This is the lazy/partial fix a weak reading permits (it makes references_column pass, so it would satisfy the column-membership criteria). My suite REJECTS it: probe_3 fails because the rendered SQL emits the table identifier UNQUOTED (R3.1 violated). Demonstrated: probe_1/2/5 HOLD under the candidate, probe_3 VIOLATED. This proves the probe suite discriminates wrong implementations.

Note on probe_6: at base the expression branch already received the plain string, so probe_6 does not discriminate base-vs-patched by itself; it is a regression-coverage probe (R3.4). probe_1 is the discriminating positive control. An earlier candidate (fixing only _index_columns arg) was found to actually resolve the F2P test, so it was replaced with the partial-unwrapped-table candidate which the suite rejects.

Verdict SOUND: 6 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 wrong candidate exercised and REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: _create_unique_sql now passes the plain table-name string (table = model._meta.db_table) to IndexName, _index_columns, and Expressions, while wrapping ONLY Statement.table in Table(table, quote_name). This makes the columns/name parts hold a plain string so references_column/references_table compare correctly. The requirements pin exactly this observable boundary — the Statement's membership queries (Req 1-2) and SQL/rename/lifecycle preservation (Req 3) — not a narrow helper. Requirement 1.4's identity-to-bool clause matches the test_patch assertions (assertIs(..., True)). Modeling boundary is correct (biconditional coverage of covered vs uncovered columns and own vs other table). Confirmed via nl_attack probe HOLDS on patched, VIOLATED on --base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change by naming public modules/functions (ddl_references.py, _create_unique_sql, Table/Columns/Expressions/Statement) — legitimate, and the core of it is already in the public problem_statement (Table passed to Columns where a string is expected). No hidden-test content transmitted: no test file path, no test function/class names (test_unique_constraint, SchemaTests never appear), no parametrization ids, no quoted test/gold code, no fix-invented identifiers (gold only rebinds table=model._meta.db_table; the test literals 'name'/'name_uq' are not cited — requirements use generic 'model's table name'/'each column'). Req 1.4 (boolean True/False comparable by identity) parallels the test's assertIs checks but is a legitimate behavioral property, not test code. Req 3.6's list of constraint kinds (partial, deferrable, covering, opclass, expression) enumerates standard public UniqueConstraint feature categories describing behavior, not the parametrized PASS_TO_PASS test ids. Verdict: faithful behavioral translation.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
